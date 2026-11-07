#!/usr/bin/env python3
"""File Tools Module - LLM agent file manipulation tools.

Companions: ``file_tools_paths`` (task-aware resolution), ``file_tools_write_guards``
(write-side guards), ``file_tools_read_tracking`` (per-task dedup / loop-detection /
staleness state).
"""

import base64
import errno
import json
import logging
import os
import re
import stat
import threading
import time
from contextlib import ExitStack
from pathlib import Path

from agent.file_safety import get_nt_namespace_error, get_read_block_error
from agent.tool_result_classification import GUARDRAIL_REFUSAL_KEY
from tools.binary_extensions import has_binary_extension
from tools.skill_provenance import is_background_review
from tools.file_operations import (
    ShellFileOperations, normalize_read_pagination, normalize_search_pagination)
from tools.file_operations_common import DEFAULT_READ_LIMIT
from tools import file_state
from agent.redact import _is_secret_file_arg, redact_sensitive_text
from tools.file_tools_paths import (
    _expand_tilde, _path_resolution_warning, _resolve_base_dir, _resolve_entry_for_task,
    _resolve_path_for_task)
from tools.file_tools_write_guards import (
    _READ_DEDUP_STATUS_MESSAGE, _check_approval_required_write, _check_binary_document_write,
    _check_cross_profile_path, _check_protected_instruction_write, _check_sensitive_path,
    _is_internal_file_tool_content, _stale_overwrite_blocker, _stale_write_refusal)
from tools.file_tools_read_tracking import (
    _add_conflict_hint, _bump_consecutive, _cap_read_tracker_data, _check_file_staleness, _check_not_found_cache,
    _file_metadata, _file_version,
    _mark_full_write_baseline, _mark_verification_stale, _note_read_coverage, _patch_failure_lock,
    _patch_failure_tracker, _read_tracker, _read_tracker_lock, _record_not_found,
    _record_patch_failure, _reset_patch_failures, _task_data, _update_read_timestamp)

logger = logging.getLogger(__name__)


_EXPECTED_WRITE_ERRNOS = {errno.EACCES, errno.EPERM, errno.EROFS}

# Read-size guard. Model-agnostic, so characters proxy tokens: 100K chars is
# ~25-35K tokens across typical tokenisers. Configurable: file_read_max_chars.
_DEFAULT_MAX_READ_CHARS = 100_000
def _get_max_read_chars() -> int:
    """Return ``file_read_max_chars`` from config.yaml (default on missing/invalid). No module
    cache: ``load_config_readonly`` is already mtime+path cached, and a process-lifetime slot
    would pin the launch profile's value under the multiplexed gateway."""
    try:
        from hermes_cli.config import load_config_readonly
        val = load_config_readonly().get("file_read_max_chars")
    except Exception:
        val = None
    valid = isinstance(val, (int, float)) and val > 0
    return int(val) if valid else _DEFAULT_MAX_READ_CHARS


def _truncate_to_char_budget(content: str, max_chars: int) -> tuple[str, int, bool]:
    """Trim line-numbered ``read_file`` content to the last COMPLETE line within *max_chars*.

    Returns ``(kept_text, lines_kept, truncated)`` so the caller can offer a
    ``next_offset`` instead of rejecting the read. If not even the first line
    fits it is clamped mid-line so the read is never empty and the cursor advances.

    Ported in spirit from nearai/ironclaw#5029 (dual line/byte cap on ``read_file``). Where hermes
    previously hard-rejected an oversized read (forcing the model to guess a smaller ``limit`` and burn a
    round-trip returning nothing), this trims the content to the last *complete line* that fits within
    ``max_chars`` and reports how many lines were kept so the caller can offer a ``next_offset``
    continuation.
    """
    if len(content) <= max_chars:
        return content, (content.count("\n") + 1 if content else 0), False

    lines = content.split("\n")
    kept: list[str] = []
    running = 0
    for line in lines:
        addition = len(line) + (1 if kept else 0)  # +1 for the rejoining "\n"
        if running + addition > max_chars:
            break
        kept.append(line)
        running += addition
    if not kept:
        kept.append(lines[0][:max_chars])
    return "\n".join(kept), len(kept), True


def _apply_char_budget(result_dict: dict, content: str, offset: int, total_lines, max_chars: int) -> str:
    """Trim *content* to the char budget, annotate *result_dict* with the
    continuation hint, and return the trimmed text."""
    trimmed, lines_kept, _ = _truncate_to_char_budget(content, max_chars)
    next_offset = offset + lines_kept
    result_dict["content"] = trimmed
    result_dict["truncated"] = True
    result_dict["truncated_by"] = "bytes"
    result_dict["next_offset"] = next_offset
    result_dict["hint"] = (
        f"Output truncated at the {max_chars:,}-char read budget after "
        f"{lines_kept} line(s) (showing lines {offset}-{next_offset - 1} of "
        f"{total_lines}). Use offset={next_offset} to continue.")
    if len(trimmed.split("\n", 1)[0]) >= max_chars:
        result_dict["truncated_lines"] = True
        result_dict["hint"] += (
            " Note: the first line alone exceeded the budget and was "
            "clamped mid-line; its remainder is not retrievable via offset.")
    return trimmed


# Above this size, a wide read (limit > 200) gets a hint toward targeted reads.
_LARGE_FILE_HINT_BYTES = 512_000

# Device/fd paths whose reads hang the process. Checked by path only — no I/O.
_BLOCKED_DEVICE_PATHS = frozenset({
    "/dev/zero", "/dev/random", "/dev/urandom", "/dev/full",     # never reach EOF
    "/dev/stdin", "/dev/tty", "/dev/console",                    # block on input
    "/dev/stdout", "/dev/stderr",                                # nonsensical to read
    "/dev/fd/0", "/dev/fd/1", "/dev/fd/2",                       # fd aliases
})
# /proc/<pid>/... (and /proc/<pid>/task/<tid>/...) files that leak secrets,
# argv, memory layout (ASLR oracle: maps family, auxv, pagemap) or raw memory.
_BLOCKED_PROC_SUFFIXES = (
    "/fd/0", "/fd/1", "/fd/2",  # stdio aliases
    "/environ", "/cmdline", "/maps", "/smaps", "/smaps_rollup", "/numa_maps",
    "/mem", "/auxv", "/pagemap")


def _file_ops_uses_host_paths(file_ops) -> bool:
    """True when *file_ops* targets the host filesystem (only then may we stat paths
    or rewrite V4A headers to host-absolute paths; sandboxes have their own namespace)."""
    env = getattr(file_ops, "env", None)
    if env is None:
        return True
    try:
        from tools.environments.local import LocalEnvironment
    except ImportError:
        return True
    return isinstance(env, LocalEnvironment)


# V4A file headers: group 1 = header prefix, 2 = op, 3 = path. ``\s*`` after
# ``***`` mirrors patch_parser's leniency (``***Update File:`` applies, so it
# must be checked).
_V4A_SINGLE_HEADER_RE = re.compile(r'^(\*\*\*\s*(Update|Add|Delete)\s+File:\s*)(.+)$', re.MULTILINE)
_V4A_MOVE_HEADER_RE = re.compile(r'^(\*\*\*\s*Move\s+File:\s*)(.+?)\s*->\s*(.+)$', re.MULTILINE)


def _rewrite_v4a_patch_paths_for_host(patch: str, path_to_resolved: dict, path_to_entry: dict,
                                      file_ops) -> str:
    """Rewrite V4A file headers to the resolved host paths (host backends only).

    The shell layer must patch the SAME files ``patch_tool`` resolved for
    locking/staleness, not re-resolve a relative header against its own cwd
    (which can differ — the git-worktree cwd bug). Delete and Move headers take
    ``path_to_entry``: they act on a symlink itself, never on its target.
    """
    if not _file_ops_uses_host_paths(file_ops):
        return patch

    def _res(raw: str, entry: bool = False) -> str:
        raw = raw.strip()
        return (path_to_entry if entry else path_to_resolved).get(raw) or raw

    patch = _V4A_SINGLE_HEADER_RE.sub(
        lambda m: f"{m.group(1)}{_res(m.group(3), entry=m.group(2) == 'Delete')}", patch)
    return _V4A_MOVE_HEADER_RE.sub(
        lambda m: f"{m.group(1)}{_res(m.group(2), entry=True)} -> {_res(m.group(3), entry=True)}", patch)


def _is_blocked_device_path(path: str) -> bool:
    """Return True for concrete device/fd/proc paths that can hang reads or leak process state."""
    normalized = os.path.normpath(_expand_tilde(path))
    if normalized in _BLOCKED_DEVICE_PATHS:
        return True
    return normalized.startswith("/proc/") and normalized.endswith(_BLOCKED_PROC_SUFFIXES)


def _is_blocked_device(filepath: str, base_dir: str | Path | None = None) -> bool:
    """True if the path (literal, any symlink hop, or final realpath) is a blocked device.

    Literal first so /dev/stdin is caught before resolving to a terminal path;
    every symlink hop is checked so an alias cannot bypass the guard.
    """
    expanded = _expand_tilde(filepath)
    if base_dir is not None and not os.path.isabs(expanded):
        expanded = os.path.join(os.fspath(base_dir), expanded)
    normalized = os.path.normpath(expanded)
    if _is_blocked_device_path(normalized):
        return True

    seen: set[str] = set()
    current = normalized
    for _ in range(20):
        try:
            target = os.readlink(current)
        except OSError:
            break
        if not os.path.isabs(target):
            target = os.path.join(os.path.dirname(current), target)
        target = os.path.normpath(target)
        if _is_blocked_device_path(target):
            return True
        if target in seen:
            break
        seen.add(target)
        current = target

    try:
        resolved = os.path.normpath(os.path.realpath(normalized))
    except (OSError, ValueError):
        return False
    return _is_blocked_device_path(resolved)


def _resolved_match_path(path: str, task_id: str) -> str:
    """Best-effort task-cwd resolution of a search hit's path.

    Search backends may return cwd-relative paths while the process cwd differs, so both the
    read-block filter and the redaction classifier must resolve against the task cwd. An
    unresolvable path is used as-is (the raw path is still worth classifying).
    """
    try:
        return str(_resolve_path_for_task(path, task_id))
    except (OSError, ValueError, RuntimeError):
        return path


def _filter_read_blocked_search_results(result, task_id: str = "default") -> int:
    """Remove credential/cache/env paths from a SearchResult in-place; return the omitted count.

    Each path is resolved against the task cwd first (search backends may
    return cwd-relative paths; the process cwd can differ).
    """
    omitted = 0

    def _allowed(path: str) -> bool:
        nonlocal omitted
        if get_read_block_error(_resolved_match_path(path, task_id)):
            omitted += 1
            return False
        return True

    if getattr(result, "matches", None):
        result.matches = [m for m in result.matches if _allowed(m.path)]
    if getattr(result, "files", None):
        result.files = [f for f in result.files if _allowed(f)]
    if getattr(result, "counts", None):
        result.counts = {f: c for f, c in result.counts.items() if _allowed(f)}
    return omitted


def _is_expected_write_exception(exc: Exception) -> bool:
    """Return True for expected write denials that should not hit error logs."""
    return isinstance(exc, PermissionError) or (
        isinstance(exc, OSError) and exc.errno in _EXPECTED_WRITE_ERRNOS)


# ── ShellFileOperations per terminal environment ─────────────────────────
_file_ops_lock = threading.Lock()
_file_ops_cache: dict = {}


def _create_terminal_env_for_file_ops(raw_task_id: str, task_id: str):
    """Build the terminal environment for *task_id* via the shared ``_create_configured_env``,
    so a file tool that runs before any terminal command still gets the configured backend."""
    from tools.terminal_tool_config import _is_container_backend, coerce_ssh_remote_cwd
    from tools.terminal_tool import (
        _create_configured_env, _get_env_config, _is_mounted_host_cwd, _is_unusable_container_cwd,
        _resolve_task_host_cwd, _select_image, get_session_cwd, resolve_task_overrides)

    config = _get_env_config()
    env_type = config["env_type"]
    overrides = resolve_task_overrides(raw_task_id)
    try:
        recorded_cwd = get_session_cwd(raw_task_id)
    except Exception:
        recorded_cwd = None
    cwd = coerce_ssh_remote_cwd(overrides.get("cwd") or recorded_cwd or config["cwd"], env_type)
    # Re-apply the container cwd guard: a gateway/TUI/ACP override is a raw HOST
    # path and ``docker run -w <host-path>`` makes search_files & co silently
    # return nothing. Valid in-container overrides (/workspace, /root) pass.
    # Re-apply the container cwd guard that _get_env_config() already ran on config["cwd"] (see #50636). A
    # per-task cwd override registered by the gateway/TUI/ACP for workspace tracking is a raw host path
    # (e.g. a Desktop session's /Users/<me>/workspace or C:\\Users\\<me>). On a container backend that
    # reaches ``docker run -w <host-path>`` and the container starts in a directory that doesn't exist
    # inside the sandbox, so search_files and friends silently return empty results (#54447). Sanitize it
    # back to the already-validated config["cwd"] so the override can't bypass the guard.
    host_cwd = _resolve_task_host_cwd(config, raw_task_id)
    if _is_container_backend(env_type) and _is_unusable_container_cwd(cwd, mounted_host=host_cwd):
        fallback = "/workspace" if _is_mounted_host_cwd(cwd, host_cwd) else config["cwd"]
        if cwd != fallback:
            logger.info(
                "Ignoring host/relative cwd override %r for %s backend "
                "(won't exist in sandbox). Using %r instead.",
                cwd, env_type, fallback)
        cwd = fallback
    logger.info("Creating new %s environment for task %s...", env_type, task_id[:8])
    terminal_env = _create_configured_env(
        config, env_type, image=_select_image(env_type, overrides, config), cwd=cwd,
        timeout=config["timeout"], task_id=task_id,
        host_cwd=host_cwd,
        local_config={"persistent": config.get("local_persistent", False)} if env_type == "local" else None,
    )
    return env_type, terminal_env


def _get_file_ops(task_id: str = "default") -> ShellFileOperations:
    """Get or create ShellFileOperations for the task's terminal environment.

    Uses terminal_tool's per-task creation locks (no duplicate sandboxes).
    Subagent task_ids collapse to "default" (``_resolve_container_task_id``) so
    delegate_task children share the parent's container; RL/benchmark task_ids
    with a registered env override keep their isolation.
    """
    from tools.terminal_tool import (
        _active_environments, _env_lock, _last_activity, _start_cleanup_thread,
        _creation_locks, _creation_locks_lock, _resolve_container_task_id,
        get_session_cwd, record_session_cwd)

    raw_task_id = task_id or "default"
    task_id = _resolve_container_task_id(raw_task_id)

    # Fast path: cached AND the environment is still alive (cleanup thread may have killed it).
    with _file_ops_lock:
        cached = _file_ops_cache.get(task_id)
    if cached is not None:
        with _env_lock:
            if task_id in _active_environments:
                _last_activity[task_id] = time.time()
                return cached
            # Env was cleaned up: rescue its cwd into the session record FILL-ONLY
            # (``cached.cwd`` is the SHARED env's cwd, not this session's own).
            # Environment was cleaned up -- preserve the old cwd in the session record before invalidating
            # the stale cache entry (fixes #26211: silent file-creation failures in long-running
            # conversations). Usually a no-op: every completed command already recorded its cwd. Fill-only:
            # ``cached.cwd`` is a snapshot of the SHARED env's cwd at cache-build time, so it is not
            # attributable to this session (same class as the interrupted-command bug, #85658). Rescue a
            # session that has no record, but never overwrite a record the session wrote for itself.
            old_cwd = getattr(cached, "cwd", None)
            if old_cwd:
                try:
                    if get_session_cwd(raw_task_id) is None:
                        record_session_cwd(raw_task_id, old_cwd)
                except Exception:
                    pass
            with _file_ops_lock:
                _file_ops_cache.pop(task_id, None)

    with _creation_locks_lock:
        task_lock = _creation_locks.setdefault(task_id, threading.Lock())

    with task_lock:
        # Double-check: another thread may have created it while we waited.
        with _env_lock:
            terminal_env = _active_environments.get(task_id)
            if terminal_env is not None:
                _last_activity[task_id] = time.time()
        if terminal_env is None:
            env_type, terminal_env = _create_terminal_env_for_file_ops(raw_task_id, task_id)
            with _env_lock:
                _active_environments[task_id] = terminal_env
                _last_activity[task_id] = time.time()
            _start_cleanup_thread()
            logger.info("%s environment ready for task %s", env_type, task_id[:8])

    file_ops = ShellFileOperations(terminal_env)
    with _file_ops_lock:
        _file_ops_cache[task_id] = file_ops
    return file_ops


def clear_file_ops_cache(task_id: str = None):
    """Clear file-operation state for a finished task, or all tasks."""
    with _file_ops_lock:
        if task_id:
            _file_ops_cache.pop(task_id, None)
        else:
            _file_ops_cache.clear()

    with _read_tracker_lock:
        if task_id:
            _read_tracker.pop(task_id, None)
        else:
            _read_tracker.clear()

    with _patch_failure_lock:
        if task_id:
            _patch_failure_tracker.pop(task_id, None)
        else:
            _patch_failure_tracker.clear()

    if task_id:
        file_state.get_registry().forget_task(task_id)
    else:
        file_state.get_registry().clear()


_SPECIAL_FILE_KINDS = (
    (stat.S_ISFIFO, "a FIFO (named pipe)"),
    (stat.S_ISSOCK, "a socket"),
    (stat.S_ISCHR, "a character device"),
    (stat.S_ISBLK, "a block device"))


def _special_file_kind(path) -> str | None:
    """Human name for a non-regular file type that would hang a read, else None.

    Stat-based sibling of ``_is_blocked_device``: a FIFO/socket in a workspace
    hangs like ``/dev/zero`` but has no recognizable name. Host filesystems
    only; unstattable paths return None and flow to the normal read path.
    """
    try:
        mode = os.stat(os.fspath(path)).st_mode  # follows symlinks, matching a real read
    except OSError:
        return None
    if stat.S_ISREG(mode) or stat.S_ISDIR(mode):
        return None
    return next((label for predicate, label in _SPECIAL_FILE_KINDS if predicate(mode)),
                "a special (non-regular) file")


def _read_msg_page(text, file_size, offset, limit, char_offset, document_format="msg"):
    """Bounded generic stored-text pagination; never grants raw write coverage."""
    label = {"msg": "MSG", "one": "OneNote", "pub": "Publisher"}.get(document_format, "DjVu")
    if type(char_offset) is not int or not 0 <= char_offset <= 1000000:
        return tool_error(f"Invalid {label} char_offset")
    lines = text.splitlines()
    if offset <= len(lines) and char_offset > len(lines[offset - 1]):
        return tool_error(f"Invalid {label} char_offset")
    metadata = text.extraction_metadata
    result = dict(success=True, content='', total_lines=len(lines), file_size=file_size,
                  extracted_document=True, format=document_format if document_format in ('djvu', 'djv') else metadata.get('format', document_format), extraction=metadata,
                  source_sha256=metadata['source_sha256'], coverage=metadata['coverage'],
                  partial=offset <= len(lines), truncated=offset <= len(lines),
                  next_offset=offset, next_char_offset=char_offset)
    # Bound metadata, escaping and content together, in UTF-8 bytes.
    budget = min(_get_max_read_chars(), 100000)
    encode = lambda: json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    fits = lambda: len(encode().encode('utf-8')) <= budget
    if not fits():
        return tool_error(f"capacity: {label} metadata exceeds inline budget")
    for n in range(offset - 1, min(len(lines), offset - 1 + limit)):
        start = char_offset if n == offset - 1 else 0
        payload = lines[n][start:]
        prior = result['content']
        prefix = ('\n' if prior else '') + f'{n+1}: '
        low, high = 0, len(payload)
        while low < high:
            mid = (low + high + 1) // 2
            result.update(content=prior + prefix + payload[:mid], partial=True,
                          truncated=True, next_offset=n+1, next_char_offset=start+mid)
            if fits(): low = mid
            else: high = mid - 1
        complete = low == len(payload)
        partial = not (complete and n + 1 == len(lines))
        result.update(content=prior+prefix+payload[:low], partial=partial, truncated=partial,
                      next_offset=n+2 if complete else n+1,
                      next_char_offset=0 if complete else start+low)
        if not fits() or (not complete and low == 0):
            result.update(content=prior, partial=True, truncated=True,
                          next_offset=n+1, next_char_offset=start)
            if not prior:
                return tool_error(f"capacity: no {label} text character fits")
            break
        if not complete: break
    result['content'] = redact_sensitive_text(result['content'], file_read=True, secret_file=False)
    if not fits():
        return tool_error(f"capacity: redacted {label} result exceeds inline budget")
    return encode()


def _read_extracted_document(path: str, _resolved, offset: int, limit: int, task_id: str, char_offset: int = 0) -> str | None:
    """Render an extractable document (.docx/.xlsx/.pdf/...) as paginated text.

    Returns the JSON result, a tool_error for an actionable extraction failure
    (size cap, encrypted, malformed), or ``None`` to fall through to the normal
    read path. Runs BEFORE the binary-extension guard.
    """
    from tools.read_extract import (
        ANYDOC_EXTENSIONS, EXTRACTABLE_EXTENSIONS, MAX_DOCUMENT_BYTES, ExtractionError,
        extract_document_bytes, is_extractable_document)

    if not is_extractable_document(str(_resolved)):
        return None
    file_ops = _get_file_ops(task_id)
    msg = _resolved.suffix.lower() == ".msg"
    onenote = _resolved.suffix.lower() == ".one"
    publisher = _resolved.suffix.lower() == ".pub"
    djvu = _resolved.suffix.lower() in (".djvu", ".djv")
    djvu_snapshot = None
    literal_table = _resolved.suffix.lower() in (".dif", ".slk")
    iwork = _resolved.suffix.lower() in (".pages", ".numbers", ".key")
    communication = _resolved.suffix.lower() in (".eml", ".ics", ".vcf")
    legacy_word = _resolved.suffix.lower() in (".wpd", ".wps")
    bounded_native = publisher or onenote or msg or literal_table or iwork or communication or djvu or legacy_word
    def msg_checkpoint():
        from agent.web_call_context import _current
        call = _current.get()
        if call is not None:
            call.check()
        if djvu or onenote:
            from tools.interrupt import is_interrupted
            if is_interrupted():
                raise RuntimeError(('onenote' if onenote else 'djvu') + '_call_stopped')
            if get_read_block_error(str(_resolved)):
                raise ExtractionError(('onenote' if onenote else 'djvu') + '_source_authority_changed')
    def snapshot_djvu():
        # The generic lane is local-only: preserve descriptor identity and bytes.
        # Scoped reads instead use the admitted workspace_document capability.
        if not _file_ops_uses_host_paths(file_ops):
            raise ExtractionError(('onenote' if onenote else 'djvu') + '_local_identity_required')
        def identity(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                    info.st_ctime_ns, info.st_mode, info.st_uid, info.st_gid, info.st_nlink)
        try:
            fd = os.open(str(_resolved), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except OSError:
            raise ExtractionError(("onenote" if onenote else "djvu") + "_source_unavailable") from None
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > 1000000:
                raise ExtractionError(('onenote' if onenote else 'djvu') + '_input_limit')
            parts, total = [], 0
            while True:
                msg_checkpoint()
                part = os.read(fd, min(65536, 1000001-total))
                if not part: break
                parts.append(part); total += len(part)
                if total > 1000000: raise ExtractionError(('onenote' if onenote else 'djvu') + '_input_limit')
            if (identity(before) != identity(os.fstat(fd))
                    or identity(before) != identity(os.stat(str(_resolved), follow_symlinks=False))):
                raise ExtractionError(('onenote' if onenote else 'djvu') + '_source_changed')
            return b''.join(parts), identity(before)
        except OSError:
            raise ExtractionError(('onenote' if onenote else 'djvu') + '_source_unavailable') from None
        finally:
            os.close(fd)
    version_before = _file_metadata(str(_resolved)) if bounded_native and _file_ops_uses_host_paths(file_ops) else None
    try:
        if bounded_native: msg_checkpoint()
        if djvu or onenote:
            from types import SimpleNamespace
            djvu_snapshot = snapshot_djvu()
            binary = SimpleNamespace(error=None, base64_content=base64.b64encode(djvu_snapshot[0]),
                                     file_size=len(djvu_snapshot[0]))
        else:
            binary = file_ops.read_file_bytes(str(_resolved), max_bytes=1000000 if bounded_native else MAX_DOCUMENT_BYTES)
        if binary.error or binary.base64_content is None:
            raise ExtractionError(binary.error or "Document bytes unavailable")
        document_bytes = base64.b64decode(binary.base64_content, validate=True)
        extracted_text = extract_document_bytes(document_bytes, str(_resolved),
                                                checkpoint=msg_checkpoint if bounded_native else None)
        if (djvu or onenote) and snapshot_djvu() != djvu_snapshot:
            raise ExtractionError(("onenote" if onenote else "djvu") + "_source_changed")
        if bounded_native:
            msg_checkpoint()
            if version_before is not None and _file_metadata(str(_resolved)) != version_before:
                raise ExtractionError(("Publisher" if publisher else "MSG" if msg else "iWork" if iwork else "Communication" if communication else "Legacy word" if legacy_word else "DIF/SYLK") + " source changed during read")
    except (ExtractionError, ValueError, base64.binascii.Error) as exc:
        logger.debug("document extraction failed for %s", path, exc_info=True)
        # Binary formats surface the specific failure (fallthrough would only
        # give a generic binary error); .ipynb and byte-transport errors fall through.
        _doc_ext = _resolved.suffix.lower()
        _binary_doc = _doc_ext in ANYDOC_EXTENSIONS or (
            _doc_ext in EXTRACTABLE_EXTENSIONS and _doc_ext != ".ipynb")
        if onenote:
            return tool_error(f"OneNote reading refused: {exc}. No external conversion fallback.")
        if djvu:
            return tool_error(f"DjVu reading refused: {exc}. No external conversion fallback.")
        if legacy_word:
            return tool_error(f"Legacy word reading refused: {exc}. No external conversion fallback.")
        if publisher:
            return tool_error(f"Publisher reading refused: {exc}. No external conversion fallback.")
        if msg:
            return tool_error(f"MSG reading refused: {exc}. No external conversion fallback.")
        if communication:
            return tool_error(f"Communication reading refused: {exc}. No external conversion fallback.")
        if iwork:
            return tool_error(f"iWork reading refused: {exc}. No external conversion fallback.")
        if literal_table:
            return tool_error(f"DIF/SYLK reading refused: {exc}. No external conversion fallback.")
        if (_binary_doc and isinstance(exc, ExtractionError)
                and not str(exc).startswith("Unsupported document type")):
            return tool_error(
                f"Cannot read '{path}' ({_doc_ext}): document "
                f"extraction failed — {exc}. Use terminal utilities "
                "to inspect or convert the file.")
        return None

    if djvu or onenote:
        rendered = _read_msg_page(extracted_text, binary.file_size, offset, limit, char_offset,
                                  document_format=_resolved.suffix.lower().lstrip('.'))
        msg_checkpoint()
        if snapshot_djvu() != djvu_snapshot:
            return tool_error("OneNote reading refused: onenote_source_changed" if onenote else "DjVu reading refused: djvu_source_changed")
        return rendered
    if publisher or msg or iwork or communication or legacy_word:
        if communication:
            import hashlib
            extracted_text.extraction_metadata = dict(
                extracted_text.extraction_metadata,
                source_sha256=hashlib.sha256(document_bytes).hexdigest())
        rendered = _read_msg_page(extracted_text, binary.file_size, offset, limit, char_offset,
                                  document_format="pub" if publisher else "msg")
        msg_checkpoint()
        if version_before is not None and _file_metadata(str(_resolved)) != version_before:
            return tool_error(("Publisher" if publisher else "MSG" if msg else "iWork" if iwork else "Legacy word" if legacy_word else "Communication") + " source changed during read")
        return rendered
    lines = extracted_text.splitlines()
    total_lines = len(lines)
    end_line = offset + limit - 1
    page_text = "\n".join(lines[offset - 1:end_line])
    from tools.tool_output_limits import get_max_line_length
    max_line_length = get_max_line_length()
    truncated_lines = any(len(line) > max_line_length for line in page_text.split('\n'))
    result_dict = {
        "content": file_ops._add_line_numbers(page_text, offset) if page_text else "",
        "total_lines": total_lines,
        "file_size": binary.file_size,
        "truncated": total_lines > end_line,
        "extracted_document": True}
    if literal_table:
        import hashlib
        result_dict['source_sha256'] = hashlib.sha256(document_bytes).hexdigest()
        result_dict['extraction'] = getattr(extracted_text, 'extraction_metadata', {})
    if _resolved.suffix.lower() == ".abw":
        # Keep the native reader's partial-coverage contract on the generic lane
        # too; pagination completeness does not mean rendered-document coverage.
        result_dict["format"] = "abw"
        result_dict["extraction"] = extracted_text.extraction_metadata
    elif not literal_table:
        # Preserve the reader's coverage on every page, without duplicating
        # document titles, authors or other stored payload outside redacted text.
        metadata = getattr(extracted_text, "extraction_metadata", None)
        if isinstance(metadata, dict):
            coverage = {key: metadata[key] for key in (
                "semantic_status", "status", "coverage", "limitations",
                "validation", "metadata_not_covered", "rendered", "vision",
                "visible_text_proven", "resources_loaded", "external_resources_loaded",
                "scripts_executed", "geometry_interpretation", "font_availability")
                if key in metadata}
            if coverage:
                result_dict["format"] = _resolved.suffix.lower().lstrip(".")
                result_dict["extraction"] = coverage
    if result_dict["truncated"]:
        result_dict["hint"] = (
            f"Use offset={end_line + 1} to continue reading "
            f"(showing {offset}-{min(end_line, total_lines)} of {total_lines} lines)")
    max_chars = _get_max_read_chars()
    if len(result_dict["content"]) > max_chars:
        _apply_char_budget(result_dict, result_dict["content"], offset, total_lines, max_chars)
    if result_dict["content"]:
        rendered = result_dict["content"]
        result_dict["content"] = redact_sensitive_text(
            rendered, file_read=True,
            secret_file=_is_secret_file_arg(str(_resolved)))
        redacted = result_dict["content"] != rendered
    else:
        redacted = False
    if (not literal_table and offset == 1 and not result_dict["truncated"] and not redacted
            and not truncated_lines and not result_dict.get("truncated_lines")):
        # The whole document was shown, so a text-authorable format (.ipynb)
        # may later be overwritten by write_file; the binary-container guard
        # keeps refusing .docx/.xlsx/.pdf regardless of this baseline.
        _mark_full_write_baseline(str(_resolved), task_id)
        _update_read_timestamp(str(_resolved), task_id)
        file_state.record_read(task_id, str(_resolved))
    return json.dumps(result_dict, ensure_ascii=False)


def _dedup_stub_or_block(task_data: dict, dedup_key: tuple, path: str) -> str:
    """Return the "unchanged" stub for a repeated identical read, escalating to a
    hard BLOCK after 2 stubs so weak tool-followers don't loop forever."""
    with _read_tracker_lock:
        hits = task_data["dedup_hits"].get(dedup_key, 0) + 1
        task_data["dedup_hits"][dedup_key] = hits
        _cap_read_tracker_data(task_data)

    if hits >= 2:
        return tool_error(
            f"BLOCKED: You have called read_file on this "
            f"exact region {hits + 1} times and the file "
            "has NOT changed. STOP calling read_file for "
            "this path — the content from your earlier "
            "read_file result in this conversation is "
            "still current. Proceed with your task using "
            "the information you already have.",
            path=path,
            already_read=hits + 1,
            # A REFUSAL the harness chose, not a failure the tool hit: without the
            # marker the failure classifiers count the block and a repeated read
            # escalates to `repeated_exact_failure_block` over calls that never failed.
            **{GUARDRAIL_REFUSAL_KEY: True})

    return json.dumps({
        "status": "unchanged",
        "message": _READ_DEDUP_STATUS_MESSAGE,
        "path": path,
        "dedup": True,
        "content_returned": False,
    }, ensure_ascii=False)


def _record_successful_read(task_data: dict, task_id: str, path: str, resolved_str: str,
                            offset: int, limit: int, dedup_key: tuple, *, partial: bool,
                            redacted: bool = False, end_line: int | None = None,
                            total_lines=None, version_before=None, snapshot=None) -> int:
    """Bookkeeping after a real (non-stub) read; returns the consecutive-read count.

    Per-task tracker under the lock (stub counter, history, consecutive count,
    mtime for dedup + staleness, page coverage, and the write_file baseline once
    the task has seen every line UNREDACTED — in one page or by paging
    contiguously through a file too big for one; a redacted page returned a
    non-round-trippable ``«redacted:…»`` sentinel, so it must not bless an
    overwrite that would persist the sentinel into a credential file). Then
    OUTSIDE our lock (no nested locking): the cross-agent registry, and the
    background-review read-mark (a FULL read of a skill file counts like
    skill_view so a follow-up skill_manage(patch) is accepted).
    """
    version = (snapshot or _file_version(resolved_str)) if version_before is not None else None
    stable = version is not None and version[:-1] == version_before == _file_metadata(resolved_str)
    complete = False
    with _read_tracker_lock:
        task_data["dedup_hits"].pop(dedup_key, None)
        task_data["dedup_generation_reads"].add(dedup_key)
        task_data["read_history"].add((path, offset, limit))
        count = _bump_consecutive(task_data, ("read", path, offset, limit))
        try:
            _mtime_now = os.path.getmtime(resolved_str)
            task_data.setdefault("read_timestamps", {})[resolved_str] = _mtime_now
        except OSError:
            pass
        baselines = task_data["full_write_baselines"]
        if stable and version is not None and count < 4:
            task_data["dedup"][dedup_key] = version_before
            # A narrower view does not undo knowledge of these same bytes. Do
            # not revive a baseline after a partial read of a different version.
            complete = baselines.get(resolved_str) == version
            if not complete:
                complete = not partial
                if partial and end_line is not None:
                    complete, redacted = _note_read_coverage(
                        task_data, resolved_str, version, offset, end_line, total_lines, redacted)
                complete = complete and not redacted
            if complete:
                baselines[resolved_str] = version
        if not complete:
            baselines.pop(resolved_str, None)
        if not stable or count >= 4:
            task_data["dedup"].pop(dedup_key, None)
            task_data["dedup_generation_reads"].discard(dedup_key)
        _cap_read_tracker_data(task_data)

    try:
        file_state.record_read(task_id, resolved_str, partial=not complete)
    except Exception:
        logger.debug("file_state.record_read failed", exc_info=True)

    if complete:
        try:
            # Background-review read-before-write guard integration (#61521): when the self-improvement
            # review fork reads a skill file with read_file (now whitelisted dispatch-side), register the
            # read the same way skill_view does, so a follow-up skill_manage(action='patch') on the loaded
            # file is accepted. A partial read doesn't count — the guard requires the CURRENT full content
            # to have been seen. No-op outside review forks (mark_background_review_skill_read gates on
            # is_background_review).
            from tools.skill_manager_guards import mark_background_review_skill_read
            mark_background_review_skill_read(Path(resolved_str))
        except Exception:
            logger.debug("background-review read-mark failed", exc_info=True)
    return count


def read_file_tool(path: str, offset: int = 1, limit: int = DEFAULT_READ_LIMIT, task_id: str = "default", char_offset: int = 0, pdf_form_fields: bool = False, password: str | None = None, pdf_signatures: bool = False, archive_parts: list[str] | None = None) -> str:
    """Read a file with pagination and line numbers.

    Guard order: NT/device-namespace prefix (raw string, no resolution) →
    device-path blocklist (no I/O) → stat-based special-file guard (host only)
    → Hermes internal denylist → document extraction → binary-extension guard
    → negative-result cache → dedup stub → real read.
    """
    from hermes_cli.friday_user_scope import scoped_file, ScopeDenied, ordinary_tool_error_json
    try:
        scoped = scoped_file("read_file", dict(path=path, offset=offset, limit=limit, char_offset=char_offset, pdf_form_fields=pdf_form_fields, password=password, pdf_signatures=pdf_signatures, archive_parts=archive_parts), task_id=task_id)
        if scoped is not None:
            return scoped
    except ScopeDenied:
        return ordinary_tool_error_json("product_user_scope_refused") or json.dumps({"success": False, "error": "product_user_scope_refused"})
    if archive_parts is not None:
        return tool_error("archive_parts requires an own-workspace split 7z archive")
    if pdf_signatures:
        return tool_error("pdf_signatures requires an own-workspace scoped PDF")
    if pdf_form_fields:
        return tool_error("pdf_form_fields requires an own-workspace scoped PDF")
    if password is not None:
        return tool_error("password requires an own-workspace supported encrypted archive, PDF, ODF or OOXML document")
    if char_offset and Path(path).suffix.lower() not in (".one", ".djvu", ".djv", ".msg", ".pub", ".pages", ".numbers", ".key", ".eml", ".ics", ".vcf", ".wpd", ".wps"):
        return tool_error("char_offset requires a scoped text continuation or a bounded native document")
    try:
        offset, limit = normalize_read_pagination(offset, limit)

        # On the RAW model-supplied string, before any expanduser()/resolve():
        # on Windows resolving \??\UNC\host\share already sends SMB auth (NTLM
        # leak); on POSIX the task-base join would anchor the prefix as a
        # relative segment and hide it from every resolved-path check below.
        nt_err = get_nt_namespace_error(path, verb="Read")
        if nt_err:
            return tool_error(nt_err)

        device_base = None if Path(path).expanduser().is_absolute() else _resolve_base_dir(task_id)
        if _is_blocked_device(path, base_dir=device_base):
            return tool_error(
                f"Cannot read '{path}': this is a device file that would "
                "block or produce infinite output.")

        _resolved = _resolve_path_for_task(path, task_id)

        # A read on a FIFO/socket blocks until the exec timeout: a self-shipped DoS.
        if _file_ops_uses_host_paths(_get_file_ops(task_id)):
            kind = _special_file_kind(_resolved)
            if kind is not None:
                return json.dumps({
                    "success": False,
                    "note": (
                        f"'{path}' is {kind}, not a regular file — reading "
                        "it would block indefinitely, so no read was "
                        "attempted. Use terminal utilities if you need to "
                        "interact with it.")})

        # Hermes internal denylist (prompt injection via catalog metadata,
        # credential stores). Runs BEFORE document extraction so a
        # protected SQLite store (state.db) cannot be read through the extractor. Pass the RESOLVED path: the denylist's own
        # resolve() uses the process cwd and would miss a relative "auth.json".
        block_error = get_read_block_error(str(_resolved))
        if block_error:
            return tool_error(block_error)

        extracted = _read_extracted_document(path, _resolved, offset, limit, task_id, char_offset)
        if extracted is not None:
            return extracted

        # The extension is a claim, so this message names only the extension;
        # the content-sniffing path names the actual magic-byte type.
        if has_binary_extension(str(_resolved)):
            return tool_error(
                f"Cannot read binary file '{path}' ({_resolved.suffix.lower()}). "
                "Use vision_analyze for images, or terminal to inspect binary files.")

        resolved_str = str(_resolved)
        cached_not_found = _check_not_found_cache("read", resolved_str, task_id)
        if cached_not_found is not None:
            return cached_not_found

        # Dedup: identical (path, offset, limit) on an unchanged file returns a
        # lightweight stub instead of re-sending the content.
        dedup_key = (resolved_str, offset, limit)
        with _read_tracker_lock:
            task_data = _task_data(task_id)
            cached_version = task_data["dedup"].get(dedup_key)
            # First unchanged read after a compaction boundary serves full content
            # (the summary may have dropped exact bytes); later ones get the stub.
            content_served_in_generation = dedup_key in task_data["dedup_generation_reads"]
        # Same rule as skill_view: the review fork shares the parent's task_id and its
        # read-before-write guard needs a real read, which the stub path never records (#95976).
        file_ops = _get_file_ops(task_id)
        version_before = _file_metadata(resolved_str) if _file_ops_uses_host_paths(file_ops) else None
        if (cached_version is not None and not is_background_review()
                and version_before == cached_version and content_served_in_generation):
            return _dedup_stub_or_block(task_data, dedup_key, path)

        result = file_ops.read_file(resolved_str if _file_ops_uses_host_paths(file_ops) else path, offset, limit)
        result_dict = result.to_dict()

        # Failed reads cannot establish whole-file knowledge.
        _err = result_dict.get("error") or ""
        if isinstance(_err, str) and _err.startswith("File not found:"):
            _record_not_found("read", resolved_str, task_id, json.dumps(result_dict, ensure_ascii=False))
        if _err or result_dict.get("is_binary"):
            return json.dumps(result_dict, ensure_ascii=False)

        # Char budget on the FORMATTED content (what enters context), BEFORE
        # redaction (skip the regex pass on huge content); truncate gracefully
        # with a next_offset instead of rejecting.
        file_size = result_dict.get("file_size", 0)
        max_chars = _get_max_read_chars()
        if len(result.content or "") > max_chars:
            result.content = _apply_char_budget(
                result_dict, result.content or "", offset,
                result_dict.get("total_lines", "unknown"), max_chars)
        redacted = False
        if result.content:
            unredacted = result.content
            result.content = redact_sensitive_text(
                unredacted, file_read=True, secret_file=_is_secret_file_arg(resolved_str))
            redacted = result.content != unredacted
            result_dict["content"] = result.content

        _add_conflict_hint(result_dict, result.content)

        if (file_size and file_size > _LARGE_FILE_HINT_BYTES
                and limit > 200 and result_dict.get("truncated")):
            result_dict.setdefault("_hint", (
                f"This file is large ({file_size:,} bytes). "
                "Consider reading only the section you need with offset and limit "
                "to keep context usage efficient."))

        total_lines = result_dict.get("total_lines")
        if result_dict.get("truncated_by") == "bytes":
            end_line = int(result_dict.get("next_offset", offset)) - 1
        else:
            end_line = offset + limit - 1
            if isinstance(total_lines, int) and total_lines > 0:
                end_line = min(end_line, total_lines)
        count = _record_successful_read(task_data, task_id, path, resolved_str, offset, limit,
                                        dedup_key, partial=(offset > 1) or bool(result_dict.get("truncated")),
                                        redacted=redacted or bool(result_dict.get("truncated_lines")),
                                        end_line=end_line, total_lines=total_lines,
                                        version_before=version_before,
                                        snapshot=getattr(result, "_snapshot", None))
        if count >= 4:
            return tool_error(
                f"BLOCKED: You have read this exact file region {count} times in a row. "
                "The content has NOT changed. You already have this information. "
                "STOP re-reading and proceed with your task.",
                path=path,
                already_read=count,
                **{GUARDRAIL_REFUSAL_KEY: True})
        if count >= 3:
            result_dict["_warning"] = (
                f"You have read this exact file region {count} times consecutively. "
                "The content has not changed since your last read. Use the information you already have. "
                "If you are stuck in a loop, stop reading and proceed with writing or responding.")
        return json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        return tool_error(str(e))


# ── Shared write/patch plumbing ──────────────────────────────────────────

def _resolve_or_none(filepath: str, task_id: str, *, entry: bool = False) -> str | None:
    """Task-resolved path string, or None when resolution fails for any reason.
    ``entry``: keep a symlink in the last component (``_resolve_entry_for_task``)."""
    try:
        return str((_resolve_entry_for_task if entry else _resolve_path_for_task)(filepath, task_id))
    except Exception:
        return None


def _write_precheck_error(paths: list[str], content_paths: list[str], task_id: str,
                          cross_profile: bool) -> str | None:
    """Run the shared write/patch guards in order; return the first error string.

    Order matters: hard denies (sensitive path, mirror) and the corruption
    guard run before anything that could prompt the user, and ONE approval
    prompt covers every path of a multi-file patch.
    """
    for p in paths:
        err = _check_sensitive_path(p, task_id) or (
            None if cross_profile else _check_cross_profile_path(p, task_id))
        if err:
            return err
    for p in content_paths:
        err = _check_binary_document_write(p, task_id)
        if err:
            return err
    return (_check_protected_instruction_write(paths, task_id)
            or _check_approval_required_write(paths, task_id))


def _edit_warnings(paths: list[str], path_to_resolved: dict, task_id: str) -> list[str]:
    """One pre-edit warning per path, in priority order: cross-agent registry
    (names the sibling subagent) > per-task staleness > workspace divergence
    (relative path resolving outside the terminal's cwd — the worktree-cwd bug)."""
    warnings: list[str] = []
    for p in paths:
        r = path_to_resolved.get(p)
        w = (file_state.check_stale(task_id, r) if r else None) or _check_file_staleness(p, task_id)
        if not w and r:
            w = _path_resolution_warning(p, Path(r), task_id)
        if w:
            warnings.append(w)
    return warnings


def _note_edited(task_id: str, paths: list[str], path_to_resolved: dict, session_id: str | None) -> None:
    """Post-success bookkeeping: verification-stale marker, then per path refresh
    the read stamp (no false staleness on the next edit) and record the write."""
    _mark_verification_stale(task_id, [path_to_resolved.get(p) or p for p in paths], session_id=session_id)
    for p in paths:
        _update_read_timestamp(p, task_id)
        if path_to_resolved.get(p):
            file_state.note_write(task_id, path_to_resolved[p])


# Whole-file rewrite hint: an overwrite of an existing file this large whose new content keeps at least
# this fraction of the old lines is a patch written the expensive way. In one 1,393-agent run 661 such
# rewrites of >20k-char files cost ~25M output chars (~$155) where `patch` averaged 1.3k chars/call.
_REWRITE_HINT_MIN_CHARS = 20_000
_REWRITE_HINT_MIN_UNCHANGED = 0.80


# Above this the line diff is skipped: SequenceMatcher on pathological repeated-line files is
# quadratic (a 460 KB same-line file took ~22 s under the write lock).
_REWRITE_HINT_MAX_CHARS = 400_000


def _whole_file_rewrite_hint(task_id: str, resolved: str | None, new_content: str) -> str | None:
    """Return a hint when ``new_content`` mostly re-sends what is already at ``resolved``.

    Reads the OLD content through the task's own file ops (``read_file_raw``, the sandbox/remote
    backend the write targets), never the host path: on a remote backend the host file is a
    different file, and a host FIFO at that path would block the write lock forever. Bounded size
    and a line multiset comparison (linear) instead of a sequence diff (quadratic on repeated lines)."""
    if not resolved or not (_REWRITE_HINT_MIN_CHARS <= len(new_content) <= _REWRITE_HINT_MAX_CHARS):
        return None
    try:
        result = _get_file_ops(task_id).read_file_raw(resolved)
        old = getattr(result, "content", None)
        if getattr(result, "error", None) or not isinstance(old, str):
            return None
    except Exception:
        return None
    if not (_REWRITE_HINT_MIN_CHARS <= len(old) <= _REWRITE_HINT_MAX_CHARS):
        return None
    old_lines, new_lines = old.splitlines(), new_content.splitlines()
    if not old_lines:
        return None
    from collections import Counter
    unchanged = sum((Counter(old_lines) & Counter(new_lines)).values())
    ratio = unchanged / max(len(old_lines), len(new_lines))
    if ratio < _REWRITE_HINT_MIN_UNCHANGED:
        return None
    changed = max(len(old_lines), len(new_lines)) - unchanged
    return (
        f"{unchanged:,} of {len(new_lines):,} lines were already on disk ({ratio:.0%} unchanged); ~{changed:,} "
        f"line(s) actually changed. Re-sending a {len(new_content):,}-char file costs output tokens for every "
        "unchanged line; for edits like this use patch (old_string/new_string), which sends only the changed region."
    )


def write_file_tool(path: str, content: str, task_id: str = "default",
                    cross_profile: bool = False,
                    session_id: str | None = None, format: str = "text") -> str:
    """Write content to a file.

    ``cross_profile`` bypasses the sandbox-mirror lost-write guards only
    (unadvertised in the schema; the mirror rejection error teaches it — the
    cross-PROFILE guard it was named for no longer exists).
    """
    from hermes_cli.friday_user_scope import scoped_file, ScopeDenied, ordinary_tool_error_json
    allowed_formats = list(
        (WRITE_FILE_SCHEMA.get('parameters', {}).get('properties', {})
         .get('format', {}).get('enum') or ['text']))
    if format not in allowed_formats:
        return json.dumps({'success': False, 'error': 'unsupported_format',
                           'format': format, 'allowed': allowed_formats}, ensure_ascii=False)
    try:
        scoped = scoped_file("write_file", dict(path=path, content=content, format=format), task_id=task_id)
        if scoped is not None:
            return scoped
    except ScopeDenied as cause:
        return ordinary_tool_error_json("product_user_scope_refused", cause=cause) or json.dumps({"success": False, "error": "product_user_scope_refused"})
    if format != "text":
        return json.dumps({"success": False, "error": "document_creation_requires_user_scope"})
    # write_file checks the binary-document guard before the mirror guard.
    err = (_check_sensitive_path(path, task_id)
           or _check_binary_document_write(path, task_id)
           or _check_protected_instruction_write([path], task_id)
           or _check_approval_required_write([path], task_id)
           or (None if cross_profile else _check_cross_profile_path(path, task_id)))
    if not err and _is_internal_file_tool_content(content):
        err = ("Refusing to write internal read_file display text as file content. "
               "Strip read_file line-number prefixes or reconstruct the intended "
               "file contents before writing.")
    if err:
        return tool_error(err)
    try:
        # Resolution failure falls back to the legacy unlocked path (the write
        # still proceeds; the per-task staleness check still runs).
        _resolved = _resolve_or_none(path, task_id)
        path_to_resolved = {path: _resolved}
        with ExitStack() as _lock:
            if _resolved:
                # Per-path lock serializes read→modify→write across concurrent
                # subagents; different paths stay fully parallel.
                _lock.enter_context(file_state.lock_path(_resolved))
            # A whole-file overwrite of content this task never saw, or that
            # changed since, is refused HERE — before the write — instead of
            # warning after the clobber (#65604). Nothing below runs.
            blocker = _stale_overwrite_blocker(path, _resolved, task_id)
            if blocker:
                return json.dumps(_stale_write_refusal(path, blocker, _resolved), ensure_ascii=False)
            warnings = _edit_warnings([path], path_to_resolved, task_id)
            rewrite_hint = _whole_file_rewrite_hint(task_id, _resolved, content)
            result = _get_file_ops(task_id).write_file(_resolved or path, content)
            result_dict = result.to_dict()
            if warnings:
                result_dict["_warning"] = warnings[0]
            if rewrite_hint and not result_dict.get("error"):
                result_dict["hint"] = rewrite_hint
            if _resolved:
                # Always report the ABSOLUTE path written so a wrong-cwd mismatch
                # is visible in the response instead of silently landing elsewhere.
                result_dict["resolved_path"] = _resolved
            if result_dict.get("error"):
                _update_read_timestamp(path, task_id)
            else:
                if _resolved:
                    result_dict["files_modified"] = [_resolved]
                    # Own write = current whole-file content: consecutive
                    # same-task writes stay unblocked. patch never does this.
                    _mark_full_write_baseline(_resolved, task_id, getattr(result, "_content_sha256", None))
                _note_edited(task_id, [path], path_to_resolved, session_id)
        return json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        if _is_expected_write_exception(e):
            logger.debug("write_file expected denial: %s: %s", type(e).__name__, e)
        else:
            logger.error("write_file error: %s: %s", type(e).__name__, e, exc_info=True)
        return tool_error(str(e))


def _collect_v4a_header_paths(patch: str) -> tuple[list[str], list[str], list[str]] | str:
    """Extract every path named in V4A headers, rejecting ``..`` traversal.

    Returns ``(all_paths, content_write_paths, entry_paths)`` or a tool_error
    string. Header paths come from patch CONTENT (more attacker-influenceable
    than ``path=``, which keeps its legitimate ``..`` use). Move headers check
    BOTH endpoints; only Update/Add write text and feed the binary-document
    guard; Delete and Move act on the directory entry (``entry_paths``).
    """
    from tools.path_security import has_traversal_component

    headers = [(m.group(3), m.group(2) in ("Update", "Add")) for m in _V4A_SINGLE_HEADER_RE.finditer(patch)]
    headers += [(g, False) for m in _V4A_MOVE_HEADER_RE.finditer(patch) for g in (m.group(2), m.group(3))]
    paths: list[str] = []
    content_paths: list[str] = []
    entry_paths: list[str] = []
    for raw, writes_text in headers:
        v4a_path = raw.strip()
        if has_traversal_component(v4a_path):
            return tool_error(
                f"V4A patch header contains '..' traversal: {v4a_path!r}. "
                "Use the agent's cwd-relative path (no '..') or an absolute "
                "path in '*** Update File:' / '*** Add File:' / "
                "'*** Delete File:' / '*** Move File:' headers.")
        paths.append(v4a_path)
        (content_paths if writes_text else entry_paths).append(v4a_path)
    return paths, content_paths, entry_paths


def patch_tool(mode: str = "replace", path: str = None, old_string: str = None,
               new_string: str = None, replace_all: bool = False, patch: str = None,
               task_id: str = "default", cross_profile: bool = False,
               session_id: str | None = None) -> str:
    """Patch a file using replace mode or V4A patch format.

    ``cross_profile``: same semantics as ``write_file``'s flag (mirror-guard
    bypass only; unadvertised).
    """
    _paths_to_check = [path] if path else []
    _content_write_paths = list(_paths_to_check)
    _entry_paths: list[str] = []
    if mode == "patch" and patch:
        collected = _collect_v4a_header_paths(patch)
        if isinstance(collected, str):
            return collected
        _paths_to_check += collected[0]
        _content_write_paths += collected[1]
        _entry_paths = collected[2]
    precheck_err = _write_precheck_error(_paths_to_check, _content_write_paths, task_id, cross_profile)
    if precheck_err:
        return tool_error(precheck_err)
    try:
        # Lock paths in sorted, deduplicated order so concurrent callers with
        # overlapping multi-file patches can't deadlock (every caller locks in
        # the same order). An unresolvable path is simply not locked.
        _path_to_resolved: dict[str, str] = {_p: _resolve_or_none(_p, task_id) for _p in _paths_to_check}
        _path_to_entry: dict[str, str] = {_p: _resolve_or_none(_p, task_id, entry=True) for _p in _entry_paths}
        with ExitStack() as _locks:
            for _r in sorted({_r for _r in (*_path_to_resolved.values(), *_path_to_entry.values()) if _r}):
                _locks.enter_context(file_state.lock_path(_r))
            stale_warnings = _edit_warnings(_paths_to_check, _path_to_resolved, task_id)
            file_ops = _get_file_ops(task_id)

            # Hand the shell layer the RESOLVED targets so both layers agree on
            # which file is edited even when the shell's cwd differs.
            if mode == "replace":
                if not path:
                    return tool_error("path required")
                if old_string is None or new_string is None:
                    return tool_error("old_string and new_string required")
                _replace_target = _path_to_resolved.get(path) or path
                result = file_ops.patch_replace(_replace_target, old_string, new_string, replace_all)
            elif mode == "patch":
                if not patch:
                    return tool_error("patch content required")
                result = file_ops.patch_v4a(
                    _rewrite_v4a_patch_paths_for_host(patch, _path_to_resolved, _path_to_entry, file_ops))
            else:
                return tool_error(f"Unknown mode: {mode}")

            result_dict = result.to_dict()
            if stale_warnings:
                result_dict["_warning"] = " | ".join(stale_warnings)
            if not result_dict.get("error"):
                # Report the ABSOLUTE path(s) actually patched so a wrong-cwd
                # mismatch is visible instead of silently landing elsewhere.
                _resolved_modified = [_path_to_entry.get(_p) or _path_to_resolved.get(_p) or _p
                                      for _p in _paths_to_check]
                result_dict["files_modified"] = _resolved_modified
                if len(_resolved_modified) == 1:
                    result_dict["resolved_path"] = _resolved_modified[0]
                _note_edited(task_id, _paths_to_check, _path_to_resolved, session_id)
                # Clear failure counters so a future miss starts a fresh count.
                _reset_patch_failures(task_id, [_r for _r in _path_to_resolved.values() if _r])
        # old_string-not-found hint. Failure escalation is tracked for replace
        # mode only (V4A misses are rare); the generic hint is suppressed when
        # patch_replace already attached a richer "Did you mean?" snippet.
        if result_dict.get("error") and "Could not find" in str(result_dict["error"]):
            failure_count = 0
            if mode == "replace" and path:
                failure_count = _record_patch_failure(task_id, _path_to_resolved.get(path) or path)
            if failure_count >= 3:
                result_dict["_hint"] = (
                    f"This is failure #{failure_count} patching {path!r}. "
                    "Stop retrying with variations of the same old_string. "
                    "Either: (1) re-read the file fresh to verify current "
                    "content, (2) use a longer / more unique old_string with "
                    "surrounding context lines, or (3) use write_file to "
                    "replace the entire file if the targeted region is hard "
                    "to anchor.")
            elif "Did you mean one of these sections?" not in str(result_dict["error"]):
                result_dict["_hint"] = (
                    "old_string not found. Use read_file to verify the current "
                    "content, or search_files to locate the text.")
        return json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        return tool_error(str(e))


def search_tool(pattern: str, target: str = "content", path: str = ".",
                file_glob: str = None, limit: int = 50, offset: int = 0,
                output_mode: str = "content", context: int = 0,
                order: str = "discovery",
                task_id: str = "default") -> str:
    """Search for content or files."""
    try:
        offset, limit = normalize_search_pagination(offset, limit)

        # Pagination args (and order) are part of the key so paging through truncated
        # results doesn't trip the repeated-search guard.
        search_key = ("search", pattern, target, str(path), file_glob or "", limit, offset, order)
        with _read_tracker_lock:
            task_data = _read_tracker.setdefault(task_id, {
                "last_key": None, "consecutive": 0, "read_history": set()})
            count = _bump_consecutive(task_data, search_key)

        if count >= 4:
            return tool_error(
                f"BLOCKED: You have run this exact search {count} times in a row. "
                "The results have NOT changed. You already have this information. "
                "STOP re-searching and proceed with your task.",
                pattern=pattern,
                already_searched=count,
                **{GUARDRAIL_REFUSAL_KEY: True})

        # Raw string before _resolve_path_for_task: resolving is the NTLM-leak
        # trigger and the task-base join would hide the prefix (see read_file_tool).
        nt_err = get_nt_namespace_error(path, verb="Search")
        if nt_err:
            return tool_error(nt_err)
        try:
            resolved_search_path = str(_resolve_path_for_task(path, task_id))
        except (OSError, ValueError, RuntimeError) as exc:
            resolved_search_path = path
            # A RuntimeError still surfaces as the tool error unless the raw
            # path is itself denylisted (that error wins).
            if isinstance(exc, RuntimeError) and not get_read_block_error(path):
                raise
        block_error = get_read_block_error(resolved_search_path)
        if block_error:
            return tool_error(block_error)

        # A missing search root costs two shells (search + parent listing for
        # "Similar paths"); cache the miss so a retry skips both.
        cached_search_nf = _check_not_found_cache("search", resolved_search_path, task_id)
        if cached_search_nf is not None:
            return cached_search_nf

        result = _get_file_ops(task_id).search(
            pattern=pattern, path=path, target=target, file_glob=file_glob,
            limit=limit, offset=offset, output_mode=output_mode, context=context, order=order)
        omitted = _filter_read_blocked_search_results(result, task_id)
        for m in getattr(result, "matches", None) or ():
            if getattr(m, "content", None):
                m.content = redact_sensitive_text(
                    m.content, file_read=True,
                    secret_file=_is_secret_file_arg(_resolved_match_path(m.path, task_id)))
        result_dict = result.to_dict(densify=True)

        if omitted:
            result_dict["_omitted"] = (
                f"{omitted} result(s) omitted because they target credential, "
                "token, cache, or secret-bearing environment files.")

        # No early return on a cached miss — same rationale as the read path.
        _search_err = result_dict.get("error") or ""
        if isinstance(_search_err, str) and _search_err.startswith("Path not found:"):
            _record_not_found("search", resolved_search_path, task_id, json.dumps(result_dict, ensure_ascii=False))

        if count >= 3:
            result_dict["_warning"] = (
                f"You have run this exact search {count} times consecutively. "
                "The results have not changed. Use the information you already have.")

        # Structured like ``_warning`` above: text appended after the JSON
        # breaks every json.loads consumer (execute_code RPC, strict tool-message
        # providers) — #90322.
        if result_dict.get("truncated"):
            result_dict["_hint"] = (
                f"Results truncated. Use offset={offset + limit} to see more, "
                "or narrow with a more specific pattern or file_glob."
            )
        return json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        return tool_error(str(e))


# ---------------------------------------------------------------------------
# Schemas + Registry
# ---------------------------------------------------------------------------
from tools.registry import registry, tool_error


def _check_file_reqs():
    """Lazy wrapper to avoid circular import with tools/__init__.py."""
    from tools import check_file_requirements
    return check_file_requirements()

READ_FILE_SCHEMA = {
    "name": "read_file",
    # Document formats are stated unconditionally: firecrawl-anydoc is a
    # core dependency (bundled), so its absence is a broken install, not a
    # configuration — the teaching error in read_extract handles that rare
    # case with the PM repair hint. The ONE dynamic word: "PDF (text
    # layer)" upgrades to "PDF (scanned or text)" when hosted OCR has a
    # route we trust (_read_file_schema_overrides). Scanned-page coverage
    # teaching lives in the response-time NEEDS-OCR warning
    # (read_extract.py); the schema doesn't pre-teach it.
    "description": "Read a text file with line numbers and pagination. Use this instead of cat/head/tail in terminal. Output format: 'LINE_NUM|CONTENT'. Suggests similar filenames if not found. Use offset and limit for large files. Reads exceeding ~100K characters are truncated on a line boundary and return a next_offset; continue with offset to read the rest. Documents auto-extract to readable text: .ipynb, Office (.docx/.xlsx/.pptx and legacy .doc/.ppt/.xls), PDF (text layer), OpenDocument, RTF, EPUB, SQLite (.db/.sqlite: schema, row counts, first rows). Cannot read images/binary — use vision_analyze for images.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read (absolute, relative, or ~/path)"},
            "offset": {"type": "integer", "description": "Line number to start reading from (1-indexed, default: 1)", "default": 1, "minimum": 1},
            "password": {"type": "string", "description": "Optional password for an encrypted ZIP or 7z archive in the own-user workspace only. Never copy it into output filenames or replies."},
            "archive_parts": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 128, "description": "Explicit ordered fixed-size raw split 7z paths, NAME.7z.001 onward, same directory/base. path must be the first part. All parts together at most 1000000 bytes; no discovery. Only own-user workspace."},
            "char_offset": {"type": "integer", "description": "Scoped text or MSG continuation: characters already read on the first selected line. Use returned next_char_offset with next_offset.", "default": 0, "minimum": 0},
            "limit": {"type": "integer", "description": "Maximum number of lines to read (default: 2000, max: 2000). Reads are additionally capped at a ~100K-character budget with a next_offset continuation.", "default": DEFAULT_READ_LIMIT, "maximum": 2000}
        },
        "required": ["path"]
    }
}

READ_FILE_SCHEMA['description'] += ' Raw split 7z: read_file path=NAME.7z.001 requires archive_parts=["NAME.7z.001","NAME.7z.002",...] in exact order. For 7z_extract use {"source":"NAME.7z.001","parts":["NAME.7z.001","NAME.7z.002",...]}, with optional password, into a NEW folder. Supply the complete fixed-size set (last may be shorter), 2..128 parts, total at most 1000000 bytes. No volume discovery; missing/mixed/reordered/corrupt sets refuse before publication. Split ZIP, RAR multivolume, SFX and split-set conversion remain unsupported. '

READ_FILE_SCHEMA['description'] += (
    ' In the own-user workspace, native POTX/OTP templates and PPSX slideshows also expose slide text, '
    'tables, cached chart data and separate speaker notes. This reading does not render layout '
    'or authorize template/slideshow creation/editing. Genuine PPTM/POTM/PPSM expose the same bounded '
    'native reading plus opaque project-present/hash metadata; no macro source or p-code is inspected, '
    'no macro runs, and safety is unproven. Macro variant creation, merging and conversion remain unsupported; bounded plain edits use presentation_macro_edit and protected edits use ooxml_password_edit. '
    'Flat FODP presentations expose their native slide text, tables, cached chart data and separate notes. '
    'External references and embedded scripts are not followed or executed. FODP reading does not '
    'authorize creating, overwriting, editing or converting that format; rendering is not performed. '
    'Classic binary .ppt/.pot/.pps expose current native slide text and associated notes without a renderer. '
    'Their tables, charts, images and individual shape visibility are not interpreted. '
    'Creation/editing/conversion of these legacy formats are unsupported; renaming does not convert them. '
    'Native EML exposes bounded stored headers, decoded plain-text bodies and attachment metadata without '
    'rendering HTML, opening attachments or sending. Native ICS exposes stored event, timezone and recurrence '
    'fields without occurrence expansion, UTC conversion or import. Native VCF exposes repeated and typed '
    'stored contact fields without fetching URIs or importing contacts. All three preserve unknown values as '
    'stored claims, enforce byte/part/depth/decoded-text limits and never follow remote resources.')

READ_FILE_SCHEMA['description'] += ' Binary VSD v11 returns partial stored page/master/shape/text evidence only. Geometry, visibility, display order, flow, inheritance and active ShapeSheet safety remain UNKNOWN; not safe-to-open or complete diagram acceptance. No execution or writing; VST/VSS/v1-v6 and known OLE/link/action records refuse.'
READ_FILE_SCHEMA['description'] += ' MSG files return partial, untrusted stored-email properties as paginated JSON and attachment metadata/hashes only. Continue next_offset/next_char_offset and check source_sha256. No sending/import, header authentication, rendering, attachment extraction or whole-format acceptance. MSG creation and plain-body copy editing require explicit msg_create/msg_edit in the own-workspace scope; raw overwrite is refused.'

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": 'MSG files require explicit msg_create or msg_edit into a NEW .msg path; no raw overwrite, sending or import. Native slide text: presentation_text_edit uses exactly source/slide/role/old_text/new_text into a NEW path of the same native profile. slide is one-based; role is slide or notes. Replaces one unique literal occurrence within a supported paragraph. Equally formatted OOXML split runs and plain ODF paragraphs supported; typed/cached or repeated ODF table cells, mixed formatting, fields, links, whitespace that changes native semantics, ambiguous or missing text refuse. Only selected text-element contents are rewritten; other XML bytes and archive payloads preserved. Native presentation variants: presentation_create uses slides with title/body/notes/table/chart (the ODP schema) into a NEW .pptx/.potx/.ppsx/.odp/.otp/.fodp path. presentation_convert uses exactly {"source":"deck.odp"}; the NEW output suffix selects a supported native profile or PDF. Macro and legacy binary formats excluded. presentation_edit uses {"source":"deck.otp","edit":{"slide":1,"table":1,"row":2,"column":2,"old_value":"24","new_value":"25"}} into the same native profile at a NEW path. PPTX/POTX/PPSX edit keys: slide/old_title/new_title/category/old_value/new_value; changes one title and chart datum. ODF edit changes one numeric table cell. Cross-family conversion uses isolated Office; visual fidelity not claimed. External resources, active content and conflicting flat styles refuse. PPTX merge: format=pptx_merge, NEW .pptx path, content JSON {"sources":["a.pptx","b.pptx"],"title":{"source":1,"slide":1},"order":[{"source":2,"slide":3},{"source":1,"slide":2}]}. Sources are two distinct own-workspace decks; source and slide are one-based. Slide1 is the declared title of each deck: choose exactly one; order lists distinct slides >=2 in exact output order after that title, and both decks must contribute. Native slide/chart/table/notes/image/theme/layout payloads are retained; source files are unchanged. Same slide size/global text defaults/table styles/global theme and compatible notes masters are required; macros, external links, cross-links to omitted slides, unsupported global structures and oversized packages refuse. No render/Office validation is implied. ' 'XLSX creation: format=xlsx_create, NEW .xlsx path, content JSON {"sheets":[{"name":"Data","rows":[["id","amount","date","note"],["0001",{"type":"decimal","value":"1200.50"},{"type":"date","value":"2026-04-05"},"=1+1"]]}]}. Strings (including =,+,-,@ prefixes and long IDs) are literal text; no prefix inference. Explicit native formulas use {"type":"formula","value":"C2*D2"} or {"type":"formula","value":"SUM(Orders!G2:G5)"}; references must be numeric, in bounds and acyclic. A sheet may add "freeze":"A2" to freeze row 1 (only an in-bounds A-column single-cell row split), "print_area":"A1:G5" for one bounded local rectangle, and/or "table":{"name":"OrdersTable","ref":"A1:G5"}. Decimal/formula objects may add "number_format":"0.00" for two-decimal numeric display; arbitrary formats are refused. Top-level "names":{"OrderSourceRows":"Orders!$A$2:$G$5"} declares native names. Formulas are not evaluated here; recalculate the returned copy separately. null or {"type":"blank"} is blank, distinct from numeric 0. Optional explicit {"type":"string","value":"0001"}; plain numbers/booleans accepted. Decimal value is a dot-decimal string, at most 15 significant digits/12 places; dates are ISO YYYY-MM-DD (1900-03-01 onward), real Excel dates displayed dd.mm.yyyy. At most 8 uniquely named sheets, 512 rows/sheet, 64 columns, 4096 cells total, 100000 UTF-8 content bytes; rows must be rectangular. XLSX join: format=xlsx_join, NEW .xlsx path, content JSON {"source":"input.xlsx","left_sheet":"Orders","right_sheet":"Codes","key":"order_id","sheet":"Joined"}. Exact-text LEFT join of two different sheets in one own-workspace workbook: preserve left order and every left row, append right non-key columns, unmatched right cells blank. Both sides require unique nonempty text keys and unique text headers; overlapping non-key names refuse. No case/Unicode/space folding or numeric-key coercion. Produces a new plain table, not a formatting-preserving copy; literal scalar source cells only, selected formulas/merged cells/tables and unsupported numeric formats refuse. Source remains unchanged. ' 'Archives: zip/7z/tar/tar.gz/tar.bz2/tar.xz/tar.zst use entries source/member and a NEW matching archive path; zip_extract/7z_extract/rar_extract/tar_extract use {source} and a NEW folder. Genuine bounded single-volume stored or version29 LZ/Huffman RAR4 and supported RAR5 regular files/directories can be read, extracted or converted into ZIP/TAR; RAR4 PPMd/VM/other compression versions, RAR creation/editing, encrypted/multivolume/linked/special/unsupported members refuse. archive_convert uses {source} between supported ZIP/7z/TAR families preserving names and bytes; explicit directories cannot be encoded to 7z. Single-stream compression: gzip/bzip2/xz/zstd use {source} into a NEW .gz/.bz2/.xz/.zst path; stream_extract uses {source} into a NEW folder. The single extracted name is the input compressed basename minus its compression suffix, never an embedded header name. read_file lists this derived entry, not decoded text. For 7z, creation accepts optional password and header_encryption=true (requires password); 7z_extract accepts source/password. read_file accepts password for own-workspace 7z. AES-256 plus LZMA2 data and AES-only private headers are supported with bounded KDF, exact padding and complete streams; other encrypted profiles refuse. Missing/wrong passwords refuse without publication. Never echo passwords in replies, filenames or member names. Encrypted conversion/editing is unsupported. Sources are unchanged. Compressed input/output and decoded single payload are bounded to 1000000 bytes. Unsupported, encrypted, unsafe, concatenated or over-limit streams refuse; never just rename extensions. ' 'Merge two supported own-workspace XLSX sources with format=xlsx_merge, a NEW .xlsx path, and JSON {"base":"orders_base.xlsx","update":"orders_update.xlsx","sheet":"Orders","key":"order_id","revision":"revision"}. Text keys stay text. Equal rows deduplicate; strictly newer integer revision wins; equal-revision conflicts refuse. In result row_sources, source/source_row/revision identify only the selected row. Each observed item is [source, source_row, revision], with source base or update; complete lists retain every occurrence, including duplicates. provenance gives the observation field order, reason legend, complete flag, returned/total observation counts, omitted_rows for observation lists, and selected_rows_omitted for whole metadata records. Result metadata is bounded; missing records or observed lists mean unknown/omitted provenance, never absent input membership. For omitted details inspect both unchanged source rows. Never infer both-input membership from the selected source: say both only when that row has observed entries from base and update. selection_reason derives from numeric revision equality, not spelling. Only dense inline-text/numeric rows, row-local scalar formulas, identical styles and explicit SUM summaries are supported; tables/charts/names and other cross-row structures refuse. Base package parts are preserved; caches are cleared, not recomputed. Recalculate the merged copy separately if requested. ' 'To recalculate an existing own-workspace XLSX, use format=xlsx_recalculate, a NEW .xlsx path, and content JSON with exactly source, e.g. {"source":"orders-edited.xlsx"}. A bounded local LibreOffice engine recomputes supported numeric formulas and ordinary chart reference caches; source, formulas, tables, names and other package content are preserved. Unsupported formulas, packages and chart caches refuse without publishing. After an XLSX edit, recalculate that returned copy when requested; do not repeat the edit. ' 'Export an existing own-workspace DOCX to a NEW PDF with format=docx_pdf and content JSON {"source":"report.docx"}. Uses a bounded local renderer, leaves the source untouched, refuses existing output names, unsafe packages and unavailable rendering. DOCX uses docx_pdf; presentations use only pptx_pdf, odp_pptx or pptx_odp; no arbitrary conversion commands. ' 'For preserving edits to an existing DOCX, use format=docx_edit, path a NEW .docx name, and content JSON with source, old_text, new_text. Example: {"source":"draft.docx","old_text":"Old deadline","new_text":"New deadline"}. Replaces exactly one literal occurrence within one main-body/table paragraph, including equally formatted split runs; other package parts and XML structure remain unchanged. Missing/ambiguous matches, mixed formatting across runs, fields/anchor boundaries and unsupported packages refuse without creating a file. Use a longer unique old_text for context. No regex, paragraph-spanning edits, header/footer/note edits or overwrite. Never reconstruct an existing DOCX from extracted text to claim layout preservation. docx and docx_structured only CREATE new documents; they do not preserve an existing source. ' 'Word titles/headings/tables require format=docx_structured. Content is JSON {"blocks":[...]}; blocks: title(text), heading(text,level=1..9), paragraph(text), table(rows of string cells). Plain format=docx keeps Markdown/tabs literal. XLSX: format=xlsx; content JSON keys source,sheet,cell,expected,value creates a NEW one-cell numeric copy; preserves other parts/formulas, no recalculation. ' "For own user workspace, format=xlsx creates a NEW workbook copy changing one numeric cell; content JSON requires source, sheet, cell, expected, value. Preserves other parts/formulas, no formula recalculation. Never write spreadsheet text under .xlsx/.xls. Explicit format=docx creates a NEW .docx from short plain paragraphs (100000 UTF-8 bytes, 2000 paragraphs); existing names are refused. For preserving revisions use docx_edit with the original source; these creation modes rebuild documents. Omit format for normal text. Write content to a file, completely replacing existing content. Use this instead of echo/cat heredoc in terminal. Creates parent directories automatically. OVERWRITES the entire file — use 'patch' for targeted edits. For an EXISTING file, call read_file first: write_file refuses (file untouched) when this task has no current full read/write of the file or the file changed on disk since; on refusal, read_file, merge, then retry. Auto-runs syntax checks on .py/.json/.yaml/.toml and other linted languages; only NEW errors introduced by this write are surfaced (pre-existing errors are filtered out). The result's verified:true means the on-disk content hash was confirmed — do NOT re-read the file to check the write landed.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to write (will be created if it doesn't exist, overwritten if it does)"},
            "content": {"type": "string", "description": 'For docx_pdf, JSON with exactly source (existing own-workspace DOCX). For docx_edit, JSON with exactly source, old_text, new_text; unique exact text replacement into a NEW .docx copy. ' "Complete content. With docx_structured, a JSON string {\"blocks\":[...]} using title/paragraph blocks {\"type\":\"title\",\"text\":\"Report\"}, headings {\"type\":\"heading\",\"level\":1,\"text\":\"Data\"}, and tables {\"type\":\"table\",\"rows\":[[\"Item\",\"Amount\"],[\"Work\",\"800\"]]}. Exact keys only; table cells are strings, rows rectangular (1-32 columns). 100000 UTF-8 bytes total, at most 2000 paragraphs including table cells."},
            "format": {"type": "string", "enum": ["text", "eml_create", "eml_edit", "eml_extract_attachment", "ics_create", "ics_edit", "vcf_create", "vcf_edit", "docx", "docx_structured", "docx_edit", "docx_fill", "docx_pdf", "pdf_pages", "xlsx", "xlsx_recalculate", "xlsx_merge", "xlsx_create", "xlsx_join", "zip", "zip_extract", "7z", "7z_extract", "rar_extract", "lha_extract", "tar", "tar.gz", "tar.bz2", "tar.xz", "tar.zst", "tar_extract", "gzip", "bzip2", "xz", "zstd", "stream_extract", "image_transform", "mhtml", "mht", "mhtml_structured", "mht_structured", "mhtml_edit", "mht_edit", "archive_edit", "archive_convert", "pptx_create", "pptx_merge", "odf_merge", "pptx_edit", "pptx_pdf", "odp_create", "odp_edit", "odp_pptx", "pptx_odp", "presentation_create", "presentation_edit", "presentation_convert", "presentation_text_edit"], "description": 'ODF presentation merge: format=odf_merge, NEW .odp/.otp/.fodp path, content JSON {"sources":["a.odp","b.fodp"],"title":{"source":1,"slide":1},"order":[{"source":2,"slide":3},{"source":1,"slide":2}]}. Two distinct own-workspace ODP/OTP/FODP sources; one-based indexes. Keep exactly one chosen slide1 title, then distinct selected slides >=2 in the given order; both sources must contribute. Native selected content/notes/tables/charts/PNG/JPEG is preserved through inline ODF resources; sources are unchanged. Identical global font/style/master/settings structures required. Title-source metadata is retained except derived document statistics. Ambiguous IDs/table names, fragment/external links, animations/forms, page-view settings, unsupported extensions/resources and oversized packages refuse; no Office or visual validation is implied. ' 'PPTX merge: format=pptx_merge, NEW .pptx path, content JSON {"sources":["a.pptx","b.pptx"],"title":{"source":1,"slide":1},"order":[{"source":2,"slide":3},{"source":1,"slide":2}]}. Sources are two distinct own-workspace decks; source and slide are one-based. Slide1 is the declared title of each deck: choose exactly one; order lists distinct slides >=2 in exact output order after that title, and both decks must contribute. Native slide/chart/table/notes/image/theme/layout payloads are retained; source files are unchanged. Same slide size/global text defaults/table styles/global theme and compatible notes masters are required; macros, external links, cross-links to omitted slides, unsupported global structures and oversized packages refuse. No render/Office validation is implied. ' 'XLSX creation: format=xlsx_create, NEW .xlsx path, content JSON {"sheets":[{"name":"Data","rows":[["id","amount","date","note"],["0001",{"type":"decimal","value":"1200.50"},{"type":"date","value":"2026-04-05"},"=1+1"]]}]}. Strings (including =,+,-,@ prefixes and long IDs) are literal text; no prefix inference. Explicit native formulas use {"type":"formula","value":"C2*D2"} or {"type":"formula","value":"SUM(Orders!G2:G5)"}; references must be numeric, in bounds and acyclic. A sheet may add "freeze":"A2" to freeze row 1 (only an in-bounds A-column single-cell row split), "print_area":"A1:G5" for one bounded local rectangle, and/or "table":{"name":"OrdersTable","ref":"A1:G5"}. Decimal/formula objects may add "number_format":"0.00" for two-decimal numeric display; arbitrary formats are refused. Top-level "names":{"OrderSourceRows":"Orders!$A$2:$G$5"} declares native names. Formulas are not evaluated here; recalculate the returned copy separately. null or {"type":"blank"} is blank, distinct from numeric 0. Optional explicit {"type":"string","value":"0001"}; plain numbers/booleans accepted. Decimal value is a dot-decimal string, at most 15 significant digits/12 places; dates are ISO YYYY-MM-DD (1900-03-01 onward), real Excel dates displayed dd.mm.yyyy. At most 8 uniquely named sheets, 512 rows/sheet, 64 columns, 4096 cells total, 100000 UTF-8 content bytes; rows must be rectangular. XLSX join: format=xlsx_join, NEW .xlsx path, content JSON {"source":"input.xlsx","left_sheet":"Orders","right_sheet":"Codes","key":"order_id","sheet":"Joined"}. Exact-text LEFT join of two different sheets in one own-workspace workbook: preserve left order and every left row, append right non-key columns, unmatched right cells blank. Both sides require unique nonempty text keys and unique text headers; overlapping non-key names refuse. No case/Unicode/space folding or numeric-key coercion. Produces a new plain table, not a formatting-preserving copy; literal scalar source cells only, selected formulas/merged cells/tables and unsupported numeric formats refuse. Source remains unchanged. ' 'Archives: zip/7z/tar/tar.gz/tar.bz2/tar.xz/tar.zst use entries source/member and a NEW matching archive path; zip_extract/7z_extract/rar_extract/tar_extract use {source} and a NEW folder. Genuine bounded single-volume stored or version29 LZ/Huffman RAR4 and supported RAR5 regular files/directories can be read, extracted or converted into ZIP/TAR; RAR4 PPMd/VM/other compression versions, RAR creation/editing, encrypted/multivolume/linked/special/unsupported members refuse. archive_convert uses {source} between supported ZIP/7z/TAR families preserving names and bytes; explicit directories cannot be encoded to 7z. Single-stream compression: gzip/bzip2/xz/zstd use {source} into a NEW .gz/.bz2/.xz/.zst path; stream_extract uses {source} into a NEW folder. The single extracted name is the input compressed basename minus its compression suffix, never an embedded header name. read_file lists this derived entry, not decoded text. Sources are unchanged. Compressed input/output and decoded single payload are bounded to 1000000 bytes. Unsupported, encrypted, unsafe, concatenated or over-limit streams refuse; never just rename extensions. ' 'Merge two supported own-workspace XLSX sources with format=xlsx_merge, a NEW .xlsx path, and JSON {"base":"orders_base.xlsx","update":"orders_update.xlsx","sheet":"Orders","key":"order_id","revision":"revision"}. Text keys stay text. Equal rows deduplicate; strictly newer integer revision wins; equal-revision conflicts refuse. In result row_sources, source/source_row/revision identify only the selected row. Each observed item is [source, source_row, revision], with source base or update; complete lists retain every occurrence, including duplicates. provenance gives the observation field order, reason legend, complete flag, returned/total observation counts, omitted_rows for observation lists, and selected_rows_omitted for whole metadata records. Result metadata is bounded; missing records or observed lists mean unknown/omitted provenance, never absent input membership. For omitted details inspect both unchanged source rows. Never infer both-input membership from the selected source: say both only when that row has observed entries from base and update. selection_reason derives from numeric revision equality, not spelling. Only dense inline-text/numeric rows, row-local scalar formulas, identical styles and explicit SUM summaries are supported; tables/charts/names and other cross-row structures refuse. Base package parts are preserved; caches are cleared, not recomputed. Recalculate the merged copy separately if requested. ' 'To recalculate an existing own-workspace XLSX, use format=xlsx_recalculate, a NEW .xlsx path, and content JSON with exactly source, e.g. {"source":"orders-edited.xlsx"}. A bounded local LibreOffice engine recomputes supported numeric formulas and ordinary chart reference caches; source, formulas, tables, names and other package content are preserved. Unsupported formulas, packages and chart caches refuse without publishing. After an XLSX edit, recalculate that returned copy when requested; do not repeat the edit. ' 'docx_pdf exports source DOCX to NEW PDF; content is JSON with exactly source. docx_edit preserves an existing DOCX in a NEW copy using content JSON source/old_text/new_text. ' "Default text. docx creates new plain paragraphs, preserving literal Markdown. For real Word titles, outline headings or tables, use docx_structured and the JSON blocks content contract. Both DOCX modes create a NEW .docx only. xlsx edits one existing numeric cell into a NEW own-workspace copy; content is JSON with source, sheet, cell, expected, value. Example: {\"source\":\"orders.xlsx\",\"sheet\":\"Orders\",\"cell\":\"C3\",\"expected\":4,\"value\":5}. Other archive parts and formulas preserved; formula caches are not recalculated."},
            # NOTE: the handler still accepts `cross_profile` (bool) — it now
            # bypasses only the #32049 sandbox-mirror lost-write guards, whose
            # rejection error teaches it. Unadvertised: the cross-PROFILE
            # guard it was named for was removed (profiles are not isolated,
            # maintainer decision), and mirror hits are rare + self-teaching.
        },
        "required": ["path", "content"]
    }
}

WRITE_FILE_SCHEMA['description'] += ' Native local communication files: eml_create accepts JSON exactly from,to,subject,text for a NEW plain-text EML; eml_edit accepts JSON exactly source,source_sha256,old_value,new_value and changes only the unique top-level Subject. eml_extract_attachment accepts exactly source,source_sha256,part_path,expected_decoded_sha256 from a current ordinary EML read and writes only that decoded attachment leaf to one explicitly named NEW own-workspace file; MIME filenames never choose the destination. This is extraction only, not document interoperability, execution, rendering, sending or import. ics_create accepts uid,summary,start_date,dtstamp plus optional end_date,description,location for one NEW all-day nonrecurring event; ics_edit uses source,source_sha256,uid,old_value,new_value for one selected VEVENT SUMMARY. vcf_create accepts fn plus optional uid,emails,phones,organization,title,note for a NEW simple vCard; typed email/phone rows use value/types. vcf_edit uses source,source_sha256,old_value,new_value for one single-card FN. Every edit creates a NEW same-format file, preserves unselected source bytes, refuses conflicts and never sends/imports. '
WRITE_FILE_SCHEMA['description'] += ' Raw split 7z: read_file path=NAME.7z.001 requires archive_parts=["NAME.7z.001","NAME.7z.002",...] in exact order. For 7z_extract use {"source":"NAME.7z.001","parts":["NAME.7z.001","NAME.7z.002",...]}, with optional password, into a NEW folder. Supply the complete fixed-size set (last may be shorter), 2..128 parts, total at most 1000000 bytes. No volume discovery; missing/mixed/reordered/corrupt sets refuse before publication. Split ZIP, RAR multivolume, SFX and split-set conversion remain unsupported. '


# ODT extends the existing own-workspace native document lane.
_DOCUMENT_PROFILE_GUIDANCE = (
    'Native Word DOCX/DOTX and ODF ODT/OTT/FODT support bounded reading, creation and '
    'preserving exact-text copies. Use the matching profile name as format for plain '
    'creation, or append _structured for JSON blocks, or _edit for a preserving copy. '
    'Word template fill: format=docx_fill, NEW .docx path, content JSON exactly '
    '{"source":"template.docx-or-.dotx","source_sha256":"64-lowercase-hex-from-read_file",'
    '"fields":{"NAME":"literal string"}}. Placeholders are {{NAME}} in supported body/table '
    'paragraphs; the exact discovered field set is required. Same-style split runs and repeated '
    'placeholders are supported. Mixed formatting, fields, revisions, anchors, headers, malformed '
    'syntax, active/signed/macro/external content and unsupported whitespace refuse. Values are '
    'literal and never recursively filled. DOTX becomes genuine DOCX by content-type conversion. '
    'ODF template fill uses format=odt_fill for ODT/OTT into a NEW .odt, or fodt_fill '
    'for FODT into a NEW .fodt, with exactly {"source":"template.odt",'
    '"source_sha256":"hash from the current read_file","fields":{"NAME":"literal value"}}. '
    'Every exact {{NAME}} occurrence in supported body/heading/table paragraphs must have '
    'one mapping entry; missing/extra fields, zero/malformed placeholders, mixed formatting, '
    'comments/revisions and placeholders in headers/footers/fields/notes/drawings or other '
    'unsupported positions refuse. Values are literal and never recursively interpreted. '
    'Each output requires a NEW matching suffix and the genuine native content type, '
    'MIME/manifest or flat XML profile. OTT instantiation changes both MIME and manifest. '
    'For example dotx_structured creates a NEW .dotx; '
    'ott_edit requires JSON {"source":"template.ott","old_text":"old","new_text":"new"} '
    'and a NEW .ott. Edit source and output share a profile; OTT fill outputs ODT. Never '
    'merely rename a document or rebuild it from extracted text to claim preservation. '
    'Word structured blocks: title/paragraph {type,text}, heading {type,text,level 1..9}, '
    'table {type,rows of rectangular string cells}. ODF structured blocks: paragraph '
    '{type,text}, heading {type,text,level 1..9}, list {type,items of strings,ordered boolean}, '
    'table {type,rows of rectangular strings}. Exact keys; at most100000 UTF-8 input bytes. '
    'Preserving edit content has exactly source/old_text/new_text: one unique supported '
    'paragraph match; mixed formatting, active fields, anchors, unsafe resources and '
    'unsupported preserving operations refuse. Unselected ZIP part payloads are preserved; '
    'FODT edits preserve unselected XML bytes and namespace declarations. Reading exposes '
    'text only and grants no raw binary overwrite authority or layout/render acceptance. '
    'DOCM/DOTM expose inert native text. Plain DOCM/DOTM use word_macro_edit, while protected DOCM/DOTM use ooxml_password_edit, for one unique source-hash-bound literal into a new same-profile copy; VBA remains opaque and never executes. Other macro-profile writes refuse; never silently drop VBA. ')
READ_FILE_SCHEMA['description'] += (
    ' Own-workspace DOCX/DOTX/DOCM/DOTM/ODT/OTT/FODT use bounded native profile readers. '
    'Macro projects remain opaque and never execute; extraction metadata discloses coverage '
    'limits. Native document reads return source_sha256 for source-bound operations such as '
    'docx_fill. No raw overwrite or layout acceptance follows from text extraction.')
WRITE_FILE_SCHEMA['description'] = _DOCUMENT_PROFILE_GUIDANCE + WRITE_FILE_SCHEMA['description']
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] = (
    _DOCUMENT_PROFILE_GUIDANCE + WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'])
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'][1:1] = [
    'odt', 'odt_structured', 'odt_edit', 'odt_fill', 'ott', 'ott_structured', 'ott_edit',
    'fodt', 'fodt_structured', 'fodt_edit', 'fodt_fill', 'dotx', 'dotx_structured', 'dotx_edit']
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] = (
    _DOCUMENT_PROFILE_GUIDANCE + WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'])

# Bounded native DOCX package merge stays in the ordinary own-workspace lane.
_DOCX_MERGE_GUIDANCE = (
    'DOCX merge: format=docx_merge, a NEW .docx path, and content string with exactly '
    '{"sources":["first.docx","second.docx"]}. Exactly two distinct own-workspace DOCX '
    'sources are included once each in the exact given order. Supported full body paragraphs, '
    'run formatting, tables and inline PNG/JPEG media bytes are preserved; source files stay '
    'unchanged. Continuous body only, without implicit page breaks. Shared globals, including '
    'styles/settings/metadata, must be byte-identical and final section properties compatible. '
    'Numbered content (including inherited style numbering), headers/footers, section breaks, '
    'compatibility markup, bookmarks, notes, macros, fields, OLE, external relations and other '
    'unsupported structures refuse before publication. '
    'This is native package merging; never substitute extracted-text concatenation. '
    'No Office, layout or rendering acceptance is implied. ')
WRITE_FILE_SCHEMA['description'] = _DOCX_MERGE_GUIDANCE + WRITE_FILE_SCHEMA['description']
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] = (
    _DOCX_MERGE_GUIDANCE + WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'])
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] = (
    _DOCX_MERGE_GUIDANCE + WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'])
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'][1:1] = ['docx_merge']

# Native RTF extends the same admitted document lane, without Office execution.
_RTF_GUIDANCE = (
    'RTF: use rtf_create with plain text or rtf_structured with JSON {"blocks":[...]}, '
    'into a NEW .rtf. Structured blocks match paragraph(type,text), heading(type,text,level1..9), '
    'list(type,items,ordered) with literal labels rather than automatic numbering, and '
    'table(type,rows) of rectangular strings. At most100000 UTF-8 input bytes. '
    'rtf_edit requires JSON source/old_text/new_text and a NEW .rtf path; replaces one '
    'unique literal occurrence within a body paragraph or table cell with uniform supported '
    'formatting. Other source bytes are preserved. Fields, objects, tracked revisions and '
    'protected or mixed-format targets refuse. Reading handles RTF code pages, escaped '
    'bytes and Unicode; ignored destinations are disclosed, never executed. No render '
    'or layout validation is implied. Never save plain text under an RTF suffix. ')
READ_FILE_SCHEMA['description'] += (
    ' RTF exposes bounded body paragraphs, outline levels and table cells; header/footer, '
    'field, object, image and other ignored destinations are reported separately. No embedded '
    'object or external link is executed or resolved.')
WRITE_FILE_SCHEMA['description'] = _RTF_GUIDANCE + WRITE_FILE_SCHEMA['description']
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] = (
    _RTF_GUIDANCE + WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'])
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'][1:1] = [
    'rtf_create', 'rtf_structured', 'rtf_edit']

_PRESENTATION_WRITE_GUIDANCE = (
    'Native presentations use exact-key JSON and NEW output paths; sources stay unchanged and existing outputs refuse. '
    'For a presentation whose factual statements must come from an XLSX/CSV table, use pptx_create with {"source":"input.xlsx","data":{"sheet":"Orders","group":"sku","order":"order_id","amount":{"product":["qty","unit_price"]},"currency":"currency"}}; the only optional top-level key is slides as described below. '
    'When slides is omitted, this source-bound mode generates five editable slides (overview, grouped counts/table, one sum chart, computed conclusion, calculation basis) without authored prose. It reads real selected source cells and calculates exact row counts, distinct text order counts, per-group sums and total; it never uses formula caches. '
    'Generic selectors are exact header text, not fixed column names: amount is exactly {"column":"net"} or {"product":["quantity","price"]}; currency is a source text column or null; sheet is required for XLSX and null for strict UTF-8 comma CSV. XLSX amounts must be literal numeric cells; selected formulas, unsupported structures/visibility, mixed currencies, missing/duplicate headers or nondecimal CSV amounts refuse without output. '
    'Bounded to 100 data rows and eight groups; output must also fit explicit 24pt title/18pt body/14pt table and chart-label budgets. Oversized content refuses; it is not silently cropped or reduced below those floors. Real Office rendering and font availability still require visual checks. The receipt includes source SHA-256 and the factual/calculation basis. '
    'When the user supplies a slide plan, preserve its exact titles, order and required sections: add slides using the five-slide title/body/table/chart contract below. In source/data/slides mode the table and chart still contain computed source aggregates; titles and body are caller-authored and explicitly unverified in the receipt. Keep factual assertions supported by the read inputs and returned source_facts; a group total is not an individual order amount. Do not replace requested sections with the default overview/groups/chart/conclusion/basis plan. '
    'pptx_edit is only the bounded title/chart/embedded-workbook edit described below; it does not recompute source-bound tables, generated conclusions or calculation basis. Generic edits to source-bound facts are unsupported; create a new source-bound deck from the current table for updated facts. '
    'For existing authored-content creation, the source/slides/series mode below remains available; body/title prose is caller-authored and unverified, and must not be represented as mechanically validated table-derived numbers or calculation provenance. '
    'PPTX authored create complete example: {"source":"orders.xlsx","series":"Sales","slides":['
    '{"title":"Opening","body":"Summary","table":false,"chart":false},'
    '{"title":"Inputs","body":"Source overview","table":false,"chart":false},'
    '{"title":"Sales","body":"Native data","table":true,"chart":true},'
    '{"title":"Conclusions","body":"Total from Orders","table":false,"chart":false},'
    '{"title":"Sources","body":"Orders only","table":false,"chart":false}]}. '
    'Exactly five slides are required; every slide has exactly title (nonempty string <=256), body (string, may be empty), table (boolean), chart (boolean); exactly one table=true and one chart=true across the deck. '
    'For a supplied PPTX template, use exactly source/slides/series/template, with template naming the existing own-workspace .pptx and source an XLSX Orders table with order_id/sku/qty/unit_price/currency/revision columns. This existing-template mode preserves five slide slots, positions, fonts, palette, master/layout structure and native editable table/chart; titles and bodies use the same slides contract. Each template slide must have one title and one body slot; table/chart flags must match its existing slots. The one table keeps its column selection and row count, and one bar/line chart receives computed per-sku totals. Read the template and brief first and copy their required title/order/sections into slides. Capacity or unsupported-template refusals are limitations to report, never permission to substitute a default deck and claim template compliance. Internal template notes, comments and author metadata are omitted from the output; do not quote that excluded content in the user reply. Other source contents stay unchanged. '
    'PPTX edit example: {"source":"deck.pptx","slide":3,"old_title":"Sales","new_title":"Sales corrected","category":"A01","old_value":"3601.50","new_value":"3602.50"}; slide is one-based, title/category/old value must identify exactly one native chart datum, and cache plus embedded workbook change together. '
    'ODP create complete example: {"slides":[{"title":"Report","body":"Summary","notes":"Speaker only","table":[["SKU","Value"],["A01",{"type":"decimal","value":"3601.50"}]],"chart":{"categories":["A01"],"values":["3601.50"]}}]}. '
    'Use 1-20 ODP slides; each has exactly title/body/notes/table/chart. notes is a string; table is null or 1-128 rectangular rows of 1-32 string or exact {"type":"decimal","value":"dot-decimal"} cells; chart is null or equal-length categories/values arrays (1-128) of strings and dot-decimal strings. '
    'ODP edit example: {"source":"deck.odp","slide":1,"table":1,"row":2,"column":2,"old_value":"3601.50","new_value":"3602.50"}; slide/table/row/column are one-based logical addresses including preceding repetitions. Only a plain nonformula numeric cell with consistent display text is edited; repeated targets, merged/covered cells, formulas, spans/mixed content and ambiguity refuse before publication. '
    'Conversions use exactly {"source":"deck.pptx"} or the matching ODP path with pptx_pdf, odp_pptx or pptx_odp only; DOCX uses docx_pdf. Unsafe/active/external/malformed packages, stale sources and plain text/XML under .pptx/.odp refuse. ')
WRITE_FILE_SCHEMA['description'] = _PRESENTATION_WRITE_GUIDANCE + WRITE_FILE_SCHEMA['description']
for _property in WRITE_FILE_SCHEMA['parameters']['properties'].values():
    if 'description' in _property:
        _property['description'] = _PRESENTATION_WRITE_GUIDANCE + _property['description']

PATCH_SCHEMA = {
    "name": "patch",
    # BASE = replace-only (what nearly every model family was trained on).
    # The V4A patch mode (mode + patch params, dual-mode description) is
    # LAYERED ON dynamically for OpenAI-family mains only — V4A is the
    # OpenAI apply_patch dialect their models emit natively; advertising
    # it to everyone cost every other session ~148 tok/call
    # (_patch_schema_overrides below). The handler accepts BOTH shapes
    # from any model regardless (replay compat + strong models that know
    # V4A anyway): mode defaults to 'replace' when omitted.
    "description": (
        "Targeted find-and-replace edits in files. Use this instead of sed/awk in terminal. "
        "Uses fuzzy matching (9 strategies) so minor whitespace/indentation differences won't break it. "
        "Returns a unified diff. Auto-runs syntax checks after editing. "
        "Finds a unique string and replaces it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to edit.",
            },
            "old_string": {
                "type": "string",
                "description": "Exact text to find and replace. Must be unique in the file unless replace_all=true. Include surrounding context lines to ensure uniqueness.",
            },
            "new_string": {
                "type": "string",
                "description": "Changed replacement text; it must differ from old_string. Pass empty string '' to delete the matched text.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences instead of requiring a unique match (default: false)",
                "default": False,
            },
            # NOTE: handler still accepts `cross_profile` — see write_file's
            # NOTE (mirror-guard bypass only; unadvertised by design).
            # NOTE: handler still accepts `mode` + `patch` (V4A) from ANY
            # model — the schema just doesn't advertise them off-family.
        },
        "required": ["path", "old_string", "new_string"],
    },
}


# V4A layer, rendered only for OpenAI-family main models (see PATCH_SCHEMA
# comment). Kept as data so the override composes it deterministically.
_PATCH_V4A_DESCRIPTION = (
    "Targeted find-and-replace edits in files. Use this instead of sed/awk in terminal. "
    "Uses fuzzy matching (9 strategies) so minor whitespace/indentation differences won't break it. "
    "Returns a unified diff. Auto-runs syntax checks after editing.\n\n"
    "REPLACE MODE (mode='replace', default): find a unique string and replace it. "
    "REQUIRED PARAMETERS: mode, path, old_string, new_string.\n"
    "PATCH MODE (mode='patch'): apply V4A multi-file patches for bulk changes. "
    "REQUIRED PARAMETERS: mode, patch."
)

_PATCH_V4A_PARAMS = {
    "mode": {
        "type": "string",
        "enum": ["replace", "patch"],
        "description": "Edit mode. 'replace' (default): requires path + old_string + new_string. 'patch': requires patch content only.",
        "default": "replace",
    },
    "patch": {
        "type": "string",
        "description": "REQUIRED when mode='patch'. V4A format patch content. Format:\n*** Begin Patch\n*** Update File: path/to/file\n@@ context hint @@\n context line\n-removed line\n+added line\n*** End Patch",
    },
}


def _is_openai_family_main() -> bool:
    """Whether the active main provider/model is the OpenAI/codex family —
    the population trained on the V4A apply_patch dialect.

    Provider-family-coarse on purpose (no per-model training-diet table to
    go stale): direct OpenAI providers always qualify; on aggregators
    (openrouter/nous/azure...) the MODEL slug decides (gpt-*/o-series/
    codex). Fail-closed to the universal replace-only schema.
    """
    try:
        from agent.auxiliary_client import _read_main_model, _read_main_provider

        provider = (_read_main_provider() or "").strip().lower()
        model = (_read_main_model() or "").strip().lower()
    except Exception:  # noqa: BLE001
        return False
    if provider in {"openai", "openai-chat", "openai-codex", "azure-openai", "codex"}:
        return True
    # Aggregators: the model slug carries the family.
    slug = model.split("/", 1)[-1]
    if slug.startswith(("gpt-", "gpt.", "chatgpt", "codex", "o1", "o3", "o4", "o5")):
        return True
    return "openai/" in model


SEARCH_FILES_SCHEMA = {
    "name": "search_files",
    "description": "Search file contents or find files by name. Use this instead of grep/rg/find/ls in terminal. Ripgrep-backed, faster than shell equivalents. On macOS, broad searches above the user home automatically skip TCC-protected folders (Desktop, Documents, Downloads, Library, Movies, Music, Pictures); target one directly when access is intentional.\n\nContent search (target='content'): Regex search inside files. Output modes: full matches with line numbers, file paths only, or match counts.\n\nFile search (target='files'): Find files by glob pattern (e.g., '*.py', '*config*'). Also use this instead of ls. Discovery order is the fast bounded default; exact global newest-first order is an explicit opt-in and may scan the full tree.",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern for content search, or glob pattern (e.g., '*.py') for file search"},
            "target": {"type": "string", "enum": ["content", "files"], "description": "'content' searches inside file contents, 'files' searches for files by name", "default": "content"},
            "path": {"type": "string", "description": "Directory or file to search in (default: current working directory)", "default": "."},
            "file_glob": {"type": "string", "description": "Filter files by pattern in grep mode (e.g., '*.py' to only search Python files)"},
            "limit": {"type": "integer", "description": "Maximum number of results to return (default: 50)", "default": 50},
            "offset": {"type": "integer", "description": "Skip first N results for pagination (default: 0)", "default": 0},
            "order": {"type": "string", "enum": ["discovery", "modified"], "description": "File-search order: 'discovery' is fast bounded traversal order; 'modified' is exact global newest-first and may scan the full tree; ignored for content", "default": "discovery"},
            "output_mode": {"type": "string", "enum": ["content", "files_only", "count"], "description": "Output format for grep mode: 'content' shows matching lines with line numbers, 'files_only' lists file paths, 'count' shows match counts per file", "default": "content"},
            "context": {"type": "integer", "description": "Number of context lines before and after each match (grep mode only)", "default": 0}
        },
        "required": ["pattern"]
    }
}


def _handle_read_file(args, **kw):
    tid = kw.get("task_id") or "default"
    return read_file_tool(path=args.get("path", ""), offset=args.get("offset", 1), limit=args.get("limit", DEFAULT_READ_LIMIT), task_id=tid, char_offset=args.get("char_offset", 0), pdf_form_fields=args.get("pdf_form_fields", False), password=args.get("password"), pdf_signatures=args.get("pdf_signatures", False), archive_parts=args.get("archive_parts"))


def _handle_write_file(args, **kw):
    tid = kw.get("task_id") or "default"
    if not args.get("path") or not isinstance(args.get("path"), str):
        return tool_error(
            "write_file: missing required field 'path'. Re-emit the tool call with "
            "both 'path' and 'content' set."
        )
    if "content" not in args:
        return tool_error(
            "write_file: missing required field 'content'. The tool call included a "
            "path but no content argument — this is almost always a dropped-arg bug "
            "under context pressure. Re-emit the tool call with the full content "
            "payload, or use execute_code with hermes_tools.write_file() for very "
            "large files."
        )
    if not isinstance(args["content"], str):
        return tool_error(
            f"write_file: 'content' must be a string, got "
            f"{type(args['content']).__name__}."
        )
    from hermes_cli.observability.shared_metrics_harness import record_file_edit

    return record_file_edit("write_file", "whole_file", lambda: write_file_tool(
        path=args["path"], content=args["content"], task_id=tid,
        cross_profile=bool(args.get("cross_profile", False)),
        session_id=kw.get("session_id"), format=args.get("format", "text"),
    ))


def _handle_patch(args, **kw):
    from hermes_cli.observability.shared_metrics_harness import record_file_edit

    tid = kw.get("task_id") or "default"
    mode = args.get("mode", "replace")
    return record_file_edit("patch", mode, lambda: patch_tool(
        mode=mode, path=args.get("path"),
        old_string=args.get("old_string"), new_string=args.get("new_string"),
        replace_all=args.get("replace_all", False), patch=args.get("patch"), task_id=tid,
        cross_profile=bool(args.get("cross_profile", False)),
        session_id=kw.get("session_id"),
    ))


def _handle_search_files(args, **kw):
    tid = kw.get("task_id") or "default"
    target_map = {"grep": "content", "find": "files"}
    raw_target = args.get("target", "content")
    target = target_map.get(raw_target, raw_target)
    # The schema documents path='.'; a present-but-blank (or JSON null) value
    # is not a missing key for dict.get, so apply the default here (#112424).
    path = args.get("path", ".")
    if path is None or (isinstance(path, str) and not path.strip()):
        path = "."
    return search_tool(
        pattern=args.get("pattern", ""), target=target, path=path,
        file_glob=args.get("file_glob"), limit=args.get("limit", 50), offset=args.get("offset", 0),
        output_mode=args.get("output_mode", "content"), context=args.get("context", 0),
        order=args.get("order", "discovery"), task_id=tid)


def _read_file_schema_overrides():
    """One-word capability upgrade: "PDF (text layer)" → "PDF (scanned or
    text)" when hosted OCR has a trusted route (see
    read_extract.hosted_ocr_available). Config/env probe only — no
    network at schema-build time. Compaction's tool refresh (#97073)
    picks up a key added mid-session.
    """
    try:
        from tools.read_extract import hosted_ocr_available

        if hosted_ocr_available():
            return {
                "description": READ_FILE_SCHEMA["description"].replace(
                    "PDF (text layer)", "PDF (scanned or text)"
                )
            }
    except Exception:  # noqa: BLE001
        pass
    return {}


registry.register(name="read_file", toolset="file", schema=READ_FILE_SCHEMA, handler=_handle_read_file, check_fn=_check_file_reqs, emoji="📖", max_result_size_chars=100_000, dynamic_schema_overrides=_read_file_schema_overrides)
registry.register(name="write_file", toolset="file", schema=WRITE_FILE_SCHEMA, handler=_handle_write_file, check_fn=_check_file_reqs, emoji="✍️", max_result_size_chars=100_000)
def _patch_schema_overrides():
    """Layer the V4A patch mode onto the base replace-only schema for
    OpenAI-family mains (see PATCH_SCHEMA comment). Config/context probe
    only — no I/O at schema-build time; compaction's tool refresh
    (#97073) re-evaluates on model switches."""
    try:
        if not _is_openai_family_main():
            return {}
        params = {
            "type": "object",
            "properties": {
                "mode": _PATCH_V4A_PARAMS["mode"],
                **PATCH_SCHEMA["parameters"]["properties"],
                "patch": _PATCH_V4A_PARAMS["patch"],
            },
            "required": ["mode"],
        }
        return {"description": _PATCH_V4A_DESCRIPTION, "parameters": params}
    except Exception:  # noqa: BLE001
        return {}


registry.register(name="patch", toolset="file", schema=PATCH_SCHEMA, handler=_handle_patch, check_fn=_check_file_reqs, emoji="🔧", max_result_size_chars=100_000, dynamic_schema_overrides=_patch_schema_overrides)
registry.register(name="search_files", toolset="file", schema=SEARCH_FILES_SCHEMA, handler=_handle_search_files, check_fn=_check_file_reqs, emoji="🔎", max_result_size_chars=100_000)

# Native ODS extends the existing bounded own-workspace document lane.
_ODS_GUIDANCE = 'Native ODS: ods_create creates a NEW .ods from exactly {sheets:[{name,rows}]}, using explicit scalar cells as xlsx_create. String IDs and prefixes remain literal; bounded acyclic SUM ranges and two-cell multiplication are calculated locally. ods_edit creates a NEW .ods from {source,sheet,cell,expected,value}: exact float/string/boolean target only, same type, no repeated/merged/formula/protected target. Other member payloads preserved; existing formula caches are not recalculated after edits. ODS/OTS reading separates values, formula cache and display. Use spreadsheet modes for OTS/FODS. '
WRITE_FILE_SCHEMA["description"] = _ODS_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["ods_create", "ods_edit"]
READ_FILE_SCHEMA["description"] += " Native ODS/OTS returns cell types, values and separate formula/cache observations."

_ODS_TABLE_GUIDANCE = 'ODS table operations create new plain native tables; source formatting is not preserved. ods_join uses {source,left_sheet,right_sheet,key,sheet} for a same-workbook exact text LEFT JOIN. ods_merge uses {base,update,sheet,key,revision}; identical ordered headers required, newer nonnegative integer numeric revision wins, equal-revision conflicts refuse. Text keys are unique and nonempty; no string/number or Unicode coercion. Formula/merged/unsupported selected cells refuse. '
WRITE_FILE_SCHEMA["description"] = _ODS_TABLE_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["ods_join", "ods_merge"]

_ODS_CHART_GUIDANCE = 'Native ODS chart/recalculation: ods_chart uses exactly {source,sheet,range,title} into a NEW .ods. range is A1:Bn or A1:Cn with a header row, literal text categories in the first column and one or two literal numeric series. It creates a real editable column chart with source references and matching local cache; no image substitute or formula execution. ods_recalculate uses exactly {source} into a NEW .ods and recalculates only existing acyclic numeric SUM ranges and two-cell products, preserving formulas and other package members. Missing/non-numeric values, cycles, unsupported formulas/content and charted recalculation inputs refuse. Ordinary ODS readback reports supported chart source ranges and verified local caches; no Office/render acceptance is implied. '
WRITE_FILE_SCHEMA["description"] = _ODS_CHART_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["ods_chart", "ods_recalculate"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] = _ODS_CHART_GUIDANCE + WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] = _ODS_CHART_GUIDANCE + WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"]
READ_FILE_SCHEMA["description"] += " Supported native ODS charts return source ranges, series values and verified local cache records; rendering is not covered."

# Native spreadsheet profiles extend the existing scoped document contracts.
_SPREADSHEET_GUIDANCE = 'Native spreadsheet profiles: spreadsheet_create with exactly {sheets:[{name,rows}]} creates a NEW .xlsx/.xltx/.ods/.ots/.fods, with true native type declarations. XLSX/XLTX also accept xlsx_create sheet options. spreadsheet_edit uses exactly {source,sheet,cell,expected,value} for nonmacro profiles, or exact {source,source_sha256,sheet,cell,expected,value} for existing XLSM/XLTM, into a NEW output of the SAME profile; OOXML edits one numeric cell (JSON numbers), ODF edits exact scalar float (decimal-string expected/value), string or boolean cells. Other XML bytes and package payloads are preserved; existing formula caches are not recalculated. For XLSM/XLTM, read_file first supplies source_sha256; only exact-value numeric edits retaining one opaque VBA payload are supported, never macro creation/execution or a safety claim. Signed, protected, hidden, external/active, formula-target and other unsupported packages refuse; old macro create/convert refusals remain. spreadsheet_convert uses exactly {source}, NEW output; only XLSX<->XLTX or ODS/OTS/FODS family conversions are native. The XLSX/ODS pair uses a separately validated isolated Office conversion; other cross-family pairs are unsupported. ODS creation calculates only bounded SUM/product formulas. Native XLSM/XLTM reading is inert: macros are opaque and never executed. Read separates available values and formula caches and discloses coverage/external resources; no visual/layout fidelity claim. Repeated, merged, rich, protected, formula or constrained ODF edit targets refuse; unsupported resources/styles refuse flat conversion. '
WRITE_FILE_SCHEMA["description"] = _SPREADSHEET_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["spreadsheet_create", "spreadsheet_edit", "spreadsheet_convert"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] = _SPREADSHEET_GUIDANCE + WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"]
READ_FILE_SCHEMA["description"] += " Native XLSX/XLTX/XLSM/XLTM/ODS/OTS/FODS reading reports its coverage; macros are opaque and never executed."

_PDF_PAGES_GUIDANCE = 'PDF page assembly: format=pdf_pages, NEW .pdf path, exact JSON {"sources":["a.pdf","b.pdf"],"pages":[{"source":2,"page":1,"rotation":90},{"source":1,"page":2,"rotation":0}]}. One or two distinct own-workspace PDF sources; source/page are one-based. Each selected page appears once in the exact requested order, and every listed source contributes. Each page rotation is additional clockwise 0/90/180/270 degrees. At most 64 input/output pages and 1 MB per input/output. Native page content/resources are preserved; document-level metadata is omitted. No rasterization. Forms, annotations, links/actions, attachments, encryption, signatures, outlines, layers and unsupported document structures refuse. Original PDFs are unchanged. '
_RASTER_GUIDANCE = 'Raster images: read_file on JPG/JPEG/PNG/TIF/TIFF/WebP/BMP/GIF returns a complete paginated frame/pixel registry, not vision or OCR. image_transform creates a NEW JPG/JPEG/PNG/TIF/TIFF/WebP/BMP file from JSON {"source":"scan.tiff","frame":2,"rotation":90,"crop":[0,0,300,200]}. Frame is required and one-based; crop is optional in EXIF-normalized pixels, then rotation is optional clockwise 0/90/180/270 degrees. Every input frame must decode within 32 frames and 16 million total pixels; 1 MB input/output. Only pixels losslessly representable as RGBA8 are supported; high-bit-depth, floating-point and non-RGB color modes refuse. Only the chosen frame is output. Other source frames are unchanged. Derivatives contain pixels only: EXIF orientation is applied, other metadata including ICC/EXIF is omitted. JPEG is lossy; alpha to JPEG/BMP refuses. No OCR, visual interpretation or fidelity claim follows from a pixel hash. HEIC/HEIF: read_file supports a bounded direct 8-bit HEVC YUV420 profile, registering every top-level frame with native plane hashes and explicit color metadata; thumbnails are not decoded. Transforming a HEIC/HEIF source additionally REQUIRES JSON "color_matrix":"bt601" or "bt709", matching a declared known matrix. With an unspecified matrix this is an explicit user choice, not inferred color fidelity. Primaries and transfer are not converted; output is pixels only, without ICC. Coded pixel aspect is reported but not resampled: dimensions and transforms use the stored sample grid, without a display-aspect preservation claim. Example: {"source":"photo.heic","frame":1,"color_matrix":"bt709"}. Container rotation/mirroring/crop properties, high depth, auxiliary/derived items, ICC and external references refuse. color_matrix is refused on other source formats. HEIC/HEIF output creation is unsupported. '
WRITE_FILE_SCHEMA["description"] = _RASTER_GUIDANCE + WRITE_FILE_SCHEMA["description"]

_MHTML_GUIDANCE = 'MHTML/MHT: mhtml/mht creates a NEW genuine multipart HTML archive from literal text; mhtml_structured/mht_structured uses JSON {"title":"Report","blocks":[{"type":"heading","level":1,"text":"Title"},{"type":"paragraph","text":"Text"},{"type":"table","rows":[["A","B"]]}]}. mhtml_edit/mht_edit uses exactly source/old_text/new_text for one unique visible literal match within one root HTML text run. It creates a NEW archive preserving all other MIME parts and headers. Unsupported active/ambiguous MIME/HTML refuses, no external resources are fetched. Read preserves text/table order and reports missing resources; images, CSS and layout are not rendered. '
WRITE_FILE_SCHEMA["description"] = _MHTML_GUIDANCE + WRITE_FILE_SCHEMA["description"]

_ARCHIVE_EDIT_GUIDANCE = 'ZIP/TAR preserving member edits: archive_edit into a NEW same-profile archive with exact JSON {"source":"original.zip","remove":["obsolete.txt"],"entries":[{"source":"new.txt","member":"docs/new.txt"}]}. Explicit listed members only: matching entries replace existing files; others append. Removal names must exist and remove only that exact member, not descendants. Unchanged member names/order/payload bytes are retained; original archive and input files remain unchanged. Container metadata is normalized, not byte-preserved. Duplicate/conflicting paths, directory replacement, secret-bearing payloads and empty output refuse. Supports ZIP and TAR family; 7z edit is unsupported. '
WRITE_FILE_SCHEMA["description"] = _ARCHIVE_EDIT_GUIDANCE + WRITE_FILE_SCHEMA["description"]

WRITE_FILE_SCHEMA['description'] += _PDF_PAGES_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _PDF_PAGES_GUIDANCE


_REPORT_GUIDANCE = (
    'Word report: format=docx_report, NEW .docx, content JSON {"blocks":[...],"toc_levels":3,"header":"Report","page_numbers":true}. '
    'Blocks use docx_structured title/heading/paragraph/table rules. toc_levels is 1-9, header optional, page_numbers defaults true. '
    'Real TOC and PAGE/NUMPAGES fields are created; their displayed values require refresh in a compatible office engine. '
    'Creation does not verify page counts, table-of-contents page references or visual layout. No automatic rendering or PDF export is claimed. '
)
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("docx_report")
WRITE_FILE_SCHEMA["description"] = _REPORT_GUIDANCE + WRITE_FILE_SCHEMA["description"]


_WORD_LOCATED_GUIDANCE = (
    'Word located edit: format=word_located_edit, NEW .docx/.dotx matching the source profile, exact JSON {"source":"draft.docx","source_sha256":"<64 lowercase hex from read_file>","paragraph":3,"old_text":"Old","new_text":"New"}. '
    'Read the current Word paragraph records first; use exact source_sha256 from that page and its one-based paragraph number including table-cell paragraphs. If the source changed, reread and reselect; do not merely refresh the hash. '
    'Exactly one literal occurrence within that paragraph changes; repeated text in other paragraphs is preserved. '
    'Fields, mixed-format or anchor-spanning selections, stale source and existing output refuse. This does not accept tracked changes. '
)
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("word_located_edit")
WRITE_FILE_SCHEMA["description"] = _WORD_LOCATED_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] = _WORD_LOCATED_GUIDANCE + WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"]

# Bounded text AcroForm support is explicit so ordinary PDF text reads keep their contract.
READ_FILE_SCHEMA["parameters"]["properties"]["pdf_form_fields"] = {
    "type": "boolean", "default": False,
    "description": "For an own-workspace PDF, return supported AcroForm text field names/types/values and source_sha256. Use default pagination. Metadata only, not page text or a render."}
READ_FILE_SCHEMA["description"] += " Use pdf_form_fields=true to inspect supported flat AcroForm text fields before pdf_form_fill."
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_form_fill")
WRITE_FILE_SCHEMA["description"] += (' PDF text form filling: format=pdf_form_fill into a NEW .pdf with JSON '
    '{"source":"form.pdf","source_sha256":"<exact read_file hash>","fields":{"name":"value"}}. '
    'Read source first with pdf_form_fields=true. Only flat AcroForm text widgets with standard Helvetica/Courier defaults, '
    'plain left-aligned single lines are supported; text must fit. Printable ASCII retains its standard appearance; '
    'bounded supported Latin/Cyrillic text uses the pinned embedded DejaVu Sans font and Unicode values. '
    'Native field values and appearance streams are generated and reparsed; no flattening. '
    'A changed existing appearance must exactly match the supported plain appearance for its current value; untouched custom appearances remain preserved. '
    'XFA, signatures, actions, encrypted files, complex field trees, unsupported fonts/glyphs, combining marks, controls, bidi text and overflow refuse; the pinned font must be available. '
    'Source and unrelated pages/resources/fields are preserved. Do not claim general PDF forms or arbitrary typography.')

_PDF_OPTIMIZE_GUIDANCE = 'PDF optimization: format=pdf_optimize, NEW .pdf path, exact JSON {"source":"input.pdf","source_sha256":"<64 lowercase hex from read_file>"}. Native lossless qpdf stream/object compression; page content, resources, geometry/order, document Info and XMP are verified unchanged with bounded decoded graph digests. Original unchanged. Reports before_bytes, after_bytes and smaller/not_smaller; reduction is not guaranteed. Inert PDFs only: unfiltered/plain Flate streams, 1 MB input/output, 64 pages, 4 MB total decoded streams. Other filters/predictors, forms, annotations, links/actions, attachments, encryption, signatures, outlines, layers and unsupported structures refuse. Trailer ID may regenerate; no rasterization. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_optimize")
WRITE_FILE_SCHEMA["description"] += _PDF_OPTIMIZE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _PDF_OPTIMIZE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _PDF_OPTIMIZE_GUIDANCE

WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("docx_public_copy")
WRITE_FILE_SCHEMA["description"] += (' docx_public_copy creates a NEW plain reconstructed .docx from supported DOCX/DOTX main-body paragraphs and tables, using exact JSON {"source":"private.docx","source_sha256":"<read hash>","remove_strings":["sensitive literal"]}. Exact case-sensitive literals are replaced; original retained. Source comments, properties, headers, footers and embedded parts are not copied. Formatting is not preserved; active, hidden/revision text, fields and unsupported body structures refuse. Any hidden marker in source styles/defaults refuses, even if unused or disabled; style visibility is not evaluated. Tracked cell revisions also refuse.')

READ_FILE_SCHEMA['description'] += (
    ' In the own-user workspace, genuine bounded single-volume stored or version29 LZ/Huffman RAR4 and supported RAR5 '
    'regular files/directories return a checked member registry, without extraction. '
    'RAR4 PPMd/VM/other compression versions, encryption, multivolume, links/special members and unsupported inputs '
    'refuse the whole archive; no member is silently skipped.'
)


_PDF_COMMENT_GUIDANCE = (
    'PDF comments: format=pdf_annotate, NEW .pdf, exact content JSON '
    '{"source":"input.pdf","source_sha256":"<current read_file SHA256>","annotations":[{"page":1,"x":20,"y":40,"text":"Comment"}]}. '
    'Pages are one-based. x/y are PDF user-space points from the lower-left; the full 18-point square icon must fit '
    'inside MediaBox intersect CropBox. At most 32 comments, 32 pages, 1 MB PDF, 2048 Unicode characters per comment; LF line breaks allowed. '
    'Native Text comments with Unicode contents and a vector icon are added, preserving original pages, form values/appearances and unrelated inert annotations. '
    'Rotated pages, non-default UserUnit, encryption, signatures, actions, attachments and unsafe/unsupported structures refuse. '
    'No author or signature is invented. This does not create free-text overlays or flatten comments. '
)
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_annotate")
WRITE_FILE_SCHEMA["description"] = _PDF_COMMENT_GUIDANCE + WRITE_FILE_SCHEMA["description"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] = _PDF_COMMENT_GUIDANCE + WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"]


_ZIP_ENCRYPTION_GUIDANCE = (
    'Encrypted ZIP: format=zip uses entries source/member and optional password in content JSON, into a NEW .zip. '
    'Creates authenticated WinZip AES-256 AE-2; member names remain visible. '
    'read_file accepts password for own-workspace ZIP; zip_extract accepts {"source":"private.zip","password":"..."} into a NEW folder. '
    'Supports single-volume non-ZIP64 AES-256 AE-1/AE-2 stored/deflate entries, with optional plain empty entries; nonempty mixed plaintext, weak ZipCrypto, other AES strengths/profiles, encrypted conversion/editing and header encryption refuse. '
    'Missing password differs from wrong password or damaged data; a refused password can be corrected on the same source without publishing partial files. '
    'Never put a password in a filename/member name, reply or log. Sources remain unchanged; limits and cancellation still apply. '
)
READ_FILE_SCHEMA['description'] += _ZIP_ENCRYPTION_GUIDANCE
WRITE_FILE_SCHEMA['description'] += _ZIP_ENCRYPTION_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _ZIP_ENCRYPTION_GUIDANCE
READ_FILE_SCHEMA["parameters"]["properties"]["password"]["description"] += " Also supports protected inert PDFs for read-only extraction when the document permits it; no decrypted output is published."
READ_FILE_SCHEMA["description"] += " For a protected PDF, pass the supplied password to read_file. Missing or wrong passwords and restricted extraction refuse explicitly. Original encrypted source hash is retained. pdf_form_fields and writes do not accept a PDF password."
READ_FILE_SCHEMA["parameters"]["properties"]["password"]["description"] += " Also supports read-only Agile AES/CBC encrypted OOXML in the own-user workspace; the supplied password and package HMAC are verified before extraction. No decrypted file is published."
READ_FILE_SCHEMA["description"] += " Protected DOCX/DOTX/DOCM/DOTM, XLSX/XLTX/XLSM/XLTM/XLSB and PPTX/POTX/PPSX/PPTM/POTM/PPSM support bounded Agile AES/CBC password reads. Pass only the user's supplied password. Wrong or missing password, unsupported encryption or damaged data refuse without partial content. Existing native format limits still apply; legacy binary Office encryption is unsupported. Use the separate ooxml_password_edit profile for bounded same-format encrypted edits."
_PDF_REDACT_GUIDANCE = (
    'Genuine bounded PDF redaction: format=pdf_redact, NEW .pdf, exact JSON '
    '{"source":"input.pdf","source_sha256":"<current read_file SHA256>","removals":[{"page":1,"text":"Secret code"}]}. '
    'Supply the exact sensitive literals explicitly; do not infer them. Each target must equal one complete Tj text-show string, '
    'occur exactly once in the document, and be on the declared one-based page. Partial, repeated, split, absent or ambiguously encoded targets refuse. ' 
    'Also refuses if remaining glyphs anywhere could spell a target in any reading order, ignoring whitespace. '
    'Only inert simple text/graphics PDFs: standard Type1 Helvetica/Courier/Times, plain Standard or WinAnsi encoding, printable ASCII, '
    'one show per BT/ET with ET immediately after Tj; unfiltered/plain Flate single content streams. '
    'No images/XObjects, TJ arrays, embedded/custom fonts, Unicode, annotations/forms/actions/attachments, encryption, signatures, Info/XMP or unsupported structures. '
    'Creates a fresh PDF with target strings removed, retaining native unaffected page operators, resources and geometry; no black overlay or rasterization. '
    'Original unchanged; source metadata and unreachable/history objects are not copied. 1 MB input/output, 64 pages, 16 targets, 4 MB decoded streams. '
)
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_redact")
WRITE_FILE_SCHEMA["description"] += _PDF_REDACT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _PDF_REDACT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _PDF_REDACT_GUIDANCE

_PDF_TEXT_EDIT_GUIDANCE = 'Native PDF text replacement: format=pdf_text_edit into a NEW .pdf, exact JSON {"source":"input.pdf","source_sha256":"<current read_file hash>","page":1,"old_text":"Date 2026-10-31","new_text":"Date 2026-11-01"}. User must explicitly supply both literals; never infer values. One complete Tj string, unique in the document and on the declared one-based page, is replaced. The target uses standard Type1 Courier family for printable ASCII, or Helvetica/Times families when every changed character is a decimal digit; equal codepoint count and identical space positions; StandardEncoding apostrophe/backtick, other target fonts, partial/repeated/split targets and no-ops refuse. Remaining glyphs that could reconstruct old_text also refuse. Only inert standard Type1 ASCII text/graphics with one show then ET, single unfiltered/plain Flate content streams, 1 MB input/output, 64 pages, 4 MB decoded. Retains native unaffected operators, resources, geometry and all other pages without overlay or rasterization. Original unchanged; fresh output omits metadata, unreachable/history objects and comments. Unicode/custom fonts/images, Info/XMP, forms/annotations/actions/attachments/encryption/signatures and unsupported structures refuse. This is a bounded literal edit, not general PDF editing or redaction. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_text_edit")
WRITE_FILE_SCHEMA["description"] += _PDF_TEXT_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _PDF_TEXT_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _PDF_TEXT_EDIT_GUIDANCE


_PDF_SIGNATURE_GUIDANCE = ('PDF signature inventory: read_file pdf_signatures=true with default pagination, '
    'no password or pdf_form_fields. Structural ByteRange/Contents checks only; always NOT_CRYPTOGRAPHICALLY_VERIFIED. '
    'No certificate, trust, revocation, digest or legal validity claim. Create an explicitly UNSIGNED separate derivative '
    'with write_file format=pdf_unsigned_copy, NEW .pdf path, exact JSON {"source":"signed.pdf","source_sha256":"<inventory hash>"}. '
    'Original signed bytes remain unchanged. Entire signature widgets/appearances, AcroForm and document metadata are deliberately discarded; '
    'page content/resources/geometry/order are verified unchanged without rasterization. Flat signature-only forms, 16 signatures, '
    '64 pages, 1 MB input/output only. Mixed forms, actions, attachments, encryption, DocMDP/Perms and unsupported profiles refuse. '
    'The derivative has no digital signatures and can be used for supported later PDF edits. Static signature-looking page artwork '
    'is ordinary content and may remain; never describe it as a valid signature. Default signed-PDF write guards remain in force. ')
READ_FILE_SCHEMA["parameters"]["properties"]["pdf_signatures"] = {"type":"boolean","default":False,
    "description":"Bounded structural signature inventory only; NOT_CRYPTOGRAPHICALLY_VERIFIED. Default pagination; own-workspace PDF only."}
READ_FILE_SCHEMA["description"] += _PDF_SIGNATURE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("pdf_unsigned_copy")
WRITE_FILE_SCHEMA["description"] += _PDF_SIGNATURE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _PDF_SIGNATURE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _PDF_SIGNATURE_GUIDANCE


# Native PDF report creation is a distinct bounded profile, not raw PDF writes.
from hermes_cli.friday_workspace_pdf_report import GUIDANCE as _PDF_REPORT_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'].append('pdf_report')
WRITE_FILE_SCHEMA['description'] += ' ' + _PDF_REPORT_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += ' ' + _PDF_REPORT_GUIDANCE

_ODF_PASSWORD_GUIDANCE = 'Protected ODF: read_file accepts the supplied password for bounded ODT/OTT/ODS/OTS/ODP/OTP package decryption in memory. Missing/wrong passwords, unsupported encryption and active/signed packages refuse; never guess, echo or store passwords in files. AES-CBC and legacy Blowfish-CFB8 PBKDF2 profiles only. For an explicitly requested preserving edit use write_file format=odf_password_edit to a NEW name with the SAME extension, content JSON {"source":"private.odt","source_sha256":"<read_file hash>","password":"<supplied password>","edit":{"old_text":"Old","new_text":"New"}}. ODT/OTT edit is exact unique text; ODS/OTS edit is {"sheet":"Sheet1","cell":"A1","expected":"1","value":"2"}; ODP/OTP edit is {"slide":1,"role":"slide","old_text":"Old","new_text":"New"}. The output keeps encryption with the same password and fresh member salts/IVs; no plaintext file is published, original remains unchanged. Do not put the password in the output name, prose or receipt. Worksheet protection is not removed; existing native edit restrictions still apply. A password checksum does not verify authenticity. Encrypted OOXML uses a separate authenticated profile; same-profile edits use ooxml_password_edit, while conversion remains unsupported. '
READ_FILE_SCHEMA["description"] += _ODF_PASSWORD_GUIDANCE
READ_FILE_SCHEMA["parameters"]["properties"]["password"]["description"] += _ODF_PASSWORD_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("odf_password_edit")
from hermes_cli.friday_workspace_ooxml_password import GUIDANCE as _OOXML_PASSWORD_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("ooxml_password_edit")
WRITE_FILE_SCHEMA["description"] += _OOXML_PASSWORD_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _ODF_PASSWORD_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _ODF_PASSWORD_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _ODF_PASSWORD_GUIDANCE

# Native read-only diagram inventory.
READ_FILE_SCHEMA["description"] += ' ODG/OTG/FODG drawings: read_file returns paginated native OBJECT and CONNECTOR records with page, IDs, labels, raw geometry and declared start/end shape IDs. Read all pages before building the object table. Connection endpoints come only from explicit IDREFs, never filenames or proximity. Direction is reported only for supported geometric triangle arrowheads; arbitrary markers, unresolved attachments and ambiguous direction are UNKNOWN. Marker names do not establish arrow meaning. No visual/layout rendering or automatic flow inference is implied; explicit bounded ODG/FODG creation uses diagram_create. Binary Visio support is not implied. Active, external, embedded binary and unsupported foreign content refuse. '
# Native diagram reading is restricted to immutable own-user snapshots.
READ_FILE_SCHEMA['description'] += (
    ' VSDX/VSTX/VSDM/VSTM expose stored page shapes, labels, groups and Connects glue. '
    'VSSX/VSSM expose MASTER definitions with separately scoped shape IDs, not page '
    'instances. Glue is not process direction; inheritance, formulas, indexed/custom '
    'line ends, visual geometry and missing labels remain UNKNOWN. Read every page '
    'and join char_offset segments. Macro profiles may contain a bounded opaque VBA '
    'project; code is never read or executed and safety remains unproven. External '
    'relationships, other active/embedded content and malformed packages refuse. '
    'No diagram writing, rendering or template instantiation. Binary VST/VSS '
    'remain unsupported; never relabel another format to claim native acceptance.')


# Explicit native editable diagrams have a separate create-only contract.
from tools.scoped_odg_write import GUIDANCE as _DIAGRAM_CREATE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'].append('diagram_create')
WRITE_FILE_SCHEMA['description'] += _DIAGRAM_CREATE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _DIAGRAM_CREATE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _DIAGRAM_CREATE_GUIDANCE

# Separate same-profile macro edit; ordinary presentation formats remain macro-free.
from hermes_cli.friday_workspace_presentation_macro import GUIDANCE as _MACRO_PRESENTATION_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("presentation_macro_edit")
WRITE_FILE_SCHEMA["description"] += _MACRO_PRESENTATION_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _MACRO_PRESENTATION_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _MACRO_PRESENTATION_GUIDANCE

_WORD_CONVERSION_GUIDANCE = 'Word conversion: docx_odt creates a NEW .odt from .docx; odt_docx creates a NEW .docx from .odt. Content is exactly JSON {source,source_sha256}; read the source first and use its current lowercase SHA-256. An isolated local Office process converts genuine native input; parsed destination paragraphs, heading levels and plain rectangular tables must match the original semantic inventory. Only plain text, explicit spaces/tabs/line breaks and unmerged tables are supported; fonts, run styling and pagination may change. Lists, fields, images, notes, links, hidden/protected/signed/active content and ambiguous styles refuse. Source remains unchanged; unavailable toolchain or unsupported conversion refuses without publishing. Never rename a suffix or rebuild extracted text to claim conversion. '
_SPREADSHEET_CONVERSION_GUIDANCE = 'XLSX/ODS cross-family conversion: spreadsheet_convert with exactly {source} into a NEW opposite .ods or .xlsx output uses isolated Office. Only this XLSX<->ODS pair is added; other existing native family conversions keep their limits. The output must retain sheet order, exact text/IDs, booleans, bounded decimals, dates and supported formula references, with independent formula/cache verification. Plain scalar cells and bounded SUM/product formulas only; custom styles, names, tables, charts, merged/hidden cells or sheets, protected/macro/external content refuse. Source is unchanged. No general filter or visual/layout fidelity is promised; unsupported output or unavailable toolchain produces no file. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["docx_odt", "odt_docx"]
for _conversion_guidance in (_WORD_CONVERSION_GUIDANCE, _SPREADSHEET_CONVERSION_GUIDANCE):
    WRITE_FILE_SCHEMA["description"] += _conversion_guidance
    WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _conversion_guidance
    WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _conversion_guidance

_DELIMITED_TABLE_GUIDANCE = 'Delimited native tables: delimited_convert creates a NEW CSV/TSV/XLSX/ODS, exactly one side delimited and the other native. Import JSON requires source,encoding,delimiter,type_policy,sheet; type_policy="text" keeps every field literal, or {columns:["text","decimal","boolean","date"],header_rows:0} gives explicit column types and header_rows 0 or 1. Export JSON requires source,encoding,delimiter,type_policy,line_ending; sheet is mandatory for multi-sheet files, range is optional A1:D5. Export type_policy="text" permits only text/blanks; "canonical" exports exact supported numeric/boolean/ISO-date values, without display formatting or formula caches. Encoding is explicit utf-8/utf-8-sig/utf-16/utf-16-le/utf-16-be/cp1251; generic utf-16 input requires a BOM. Delimiter is comma/semicolon/tab/vertical bar; TSV requires tab; line_ending is LF or CRLF. No detection or locale inference. Quoted field delimiters, quotes and embedded line breaks are preserved. All formulas, unsafe/active/macro structures and ambiguous native extents refuse. OOXML escape-looking text is unsupported for XLSX. Without range native data must be an explicit A1 rectangle matching declarations. Sources remain unchanged; no overwrite. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["delimited_convert"]
for _new_document_guidance in (_DELIMITED_TABLE_GUIDANCE,):
    WRITE_FILE_SCHEMA["description"] += _new_document_guidance
    WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _new_document_guidance
    WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _new_document_guidance

_WORD_MACRO_EDIT_GUIDANCE = 'Word macro text: word_macro_edit accepts exactly {source,source_sha256,old_text,new_text} into a NEW same-format .docm/.dotm. Obtain source_sha256 from current read_file. One unique literal in a supported main-body/table paragraph changes; equal-format split runs work. All other XML/member bytes, macro-enabled main declaration and any opaque VBA project remain intact. Signatures, protection, fields, revisions, hidden text, mixed-format matches, external/active/OLE/unknown parts refuse. VBA is never evaluated or executed and its safety remains unproven. This operation does not create, instantiate, convert or strip macro templates/documents. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("word_macro_edit")
WRITE_FILE_SCHEMA["description"] += _WORD_MACRO_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _WORD_MACRO_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _WORD_MACRO_EDIT_GUIDANCE

_DOCUMENT_PDF_GUIDANCE = 'Native PDF export: odt_pdf, xlsx_pdf and ods_pdf export the matching original to a NEW .pdf with exactly {source,source_sha256}. Read the source first and supply its current lowercase SHA-256. The original remains unchanged; no overwrite. The isolated Office export must pass an independent source/text/value and visible-glyph check before publication. ODT supports bounded plain text and rectangular tables in single-column reading order. XLSX/ODS supports bounded scalar cells and independently recomputed supported formulas, one visible nonempty sheet per page in source order. Unsupported, hidden, protected, signed, macro, external or active source content, stale formula caches, unsupported fonts/paint, missing/extra/cropped text and ambiguous layout refuse without publishing. Only the bounded visible text profile is supported; general Office producer compatibility and visual fidelity are not established. The PDF is a derivative: editable structure and formulas stay in the original. Existing docx_pdf and presentation routes keep their own contracts. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["odt_pdf", "xlsx_pdf", "ods_pdf"]
WRITE_FILE_SCHEMA["description"] += _DOCUMENT_PDF_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _DOCUMENT_PDF_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _DOCUMENT_PDF_GUIDANCE

_SVG_NATIVE_GUIDANCE = 'SVG: bounded static element attributes and stored text only; no rendering or proven visible content. Scripts, CSS, external resources, image/use/foreignObject and animation refuse. svg_create creates a NEW .svg from {width,height,shapes}; shapes: rect/circle/line/text with explicit numeric coordinates, optional id/fill/stroke/stroke_width/font_size, and text for text. svg_text_edit creates a NEW .svg from exactly {source,source_sha256,id,old_text,new_text}; one ID-selected plain text leaf must match, and every other source byte is preserved. No raw SVG overwrite, conversion or template inference. '
READ_FILE_SCHEMA["description"] += _SVG_NATIVE_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _SVG_NATIVE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["svg_create", "svg_text_edit"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _SVG_NATIVE_GUIDANCE

_FB2_GUIDANCE = 'FB2: read_file returns bounded stored Unicode book metadata and body text from native FictionBook 2 XML. UTF-8 and UTF-16 only; no styles/images/layout rendering or resource fetching; full XSD validation is not implied. fb2_create creates a NEW .fb2 using exact JSON {"title":"Book","author":"Author","language":"en","sections":[{"title":"Chapter","paragraphs":["Text"]}]}. fb2_edit creates a NEW .fb2 using JSON {"source":"book.fb2","source_sha256":"<current read_file hash>","old_text":"Whole paragraph","new_text":"Replacement paragraph"}. Both literals must be explicit. Without a selector, exactly one matching complete plain paragraph directly within any section is required. Optionally supply the complete selector triplet {"body":2,"section":1,"paragraph":1}; ordinals are one-based direct body/section/paragraph children and permit selection among duplicate text. Partial, invalid or missing targets refuse without falling back to unaddressed search; selected old_text must match exactly. Addressed paragraphs must have no attributes. Both modes require UTF-8 and no inline/mixed content in the target; every unselected byte is preserved. DTD/entities/processing instructions and unsupported structures refuse. Source is unchanged; overwrites, raw writes, compressed FB2, conversion and general editing are unsupported. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["fb2_create", "fb2_edit"]
READ_FILE_SCHEMA["description"] += _FB2_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _FB2_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _FB2_GUIDANCE
READ_FILE_SCHEMA["description"] += ' Legacy OpenOffice.org 1.0 SXW/STW, SXC/STC and SXI/STI: read_file returns bounded stored text, tables/cells and slide text with explicit PARTIAL coverage. The legacy namespaces, version 1.0, document class and exact document/template MIME must agree; renaming modern ODF or a document as a template does not convert it. Formula strings and stored values are observations only; styles, layout, field evaluation and visual fidelity are unverified. Known legacy external DTD declarations are inert; entities, encryption, recognized scripts/forms and embedded objects refuse. Unknown structures are omitted, and links are never fetched. Creation: write_file format=legacy_openoffice_create into a NEW .sxw/.stw/.sxc/.stc/.sxi/.sti path. Text uses {"blocks":[{"type":"paragraph","text":"Hello"},{"type":"heading","level":1,"text":"Title"},{"type":"table","rows":[["A","B"]]}]}; sheets use {"sheets":[{"name":"Data","rows":[["literal",12,true,null]]}]}; slides use {"slides":[{"title":"Title","paragraphs":["Body"]}]}. Exact schemas, at most100000 UTF-8 JSON bytes; single-line strings, no tabs, leading/trailing/repeated ASCII spaces. Strings including = are literals, no formulas; each document/template has its own genuine MIME. For a preserving copy use format=legacy_openoffice_edit, NEW same extension, JSON {"source":"source.sxw","source_sha256":"<read_file hash>","old_text":"Complete old paragraph","new_text":"Complete replacement"}. Changes exactly one complete plain paragraph or heading leaf in content.xml; unselected XML bytes, other member payloads and descriptive ZIP metadata are preserved. No substring/split-run, typed/formula/repeated/spanned cell, unresolved revision, unknown-member or whitespace-sensitive edit. Original unchanged; raw overwrite, conversion, template instantiation and render/Office compatibility remain unsupported. '

# Real bounded DBF tables; creation/editing is delegated to the own-user scope.
from tools.scoped_dbf import READ_GUIDANCE as _DBF_READ, WRITE_GUIDANCE as _DBF_WRITE
READ_FILE_SCHEMA["description"] += _DBF_READ
WRITE_FILE_SCHEMA["description"] += _DBF_WRITE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["dbf_create", "dbf_edit"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _DBF_WRITE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _DBF_WRITE
from tools.scoped_xps import GUIDANCE as _XPS_READ_GUIDANCE
READ_FILE_SCHEMA['description'] += ' ' + _XPS_READ_GUIDANCE

# Inert DIF/SYLK literal tables with native create-only copies.
from tools.scoped_dif_sylk import READ_GUIDANCE as _DIF_SLK_READ, WRITE_GUIDANCE as _DIF_SLK_WRITE
READ_FILE_SCHEMA["description"] += _DIF_SLK_READ
WRITE_FILE_SCHEMA["description"] += _DIF_SLK_WRITE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["dif_create", "dif_edit", "slk_create", "slk_edit"]
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _DIF_SLK_WRITE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _DIF_SLK_WRITE
_ABW_GUIDANCE = 'AbiWord ABW: read_file returns bounded stored paragraph and table-cell text from native .abw XML (UTF-8/UTF-16), not rendered/visible text. No DTD/entities/PI, resource fetching, fields, links, images, embedded data, lists, revisions, notes, frames, templates, compressed ABW or whole-format/application validation. abw_create creates a NEW .abw using exactly {"paragraphs":["First paragraph","Second paragraph"]}; plain single-line Unicode strings (tabs allowed), no inferred Markdown formatting. abw_edit creates a NEW .abw using exactly {"source":"document.abw","source_sha256":"<current read_file hash>","old_text":"Whole paragraph","new_text":"Replacement paragraph"}. Both literals must be explicit and single-line. Only a unique complete plain paragraph directly within a section in UTF-8 can change; mixed/ambiguous targets refuse. Source and all other bytes remain unchanged. No overwrite, raw write, conversion or visual-fidelity claim. '
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["abw_create", "abw_edit"]
READ_FILE_SCHEMA["description"] += _ABW_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _ABW_GUIDANCE
_ODF_SPECIAL_GUIDANCE = 'ODM/ODF: read_file returns bounded stored views with PARTIAL coverage and source SHA-256. ODM stays read-only; linked sections and cached text are not resolved or presented as current subdocument content. ODF returns inert MathML nodes with one-based IDs and source annotations, never a computed or rendered equation. Use explicit odf_formula_create or odf_formula_edit for the bounded native formula profile and a NEW .odf path; unsupported variants refuse. No conversion, password support, link fetching or raw text/XML writes. '
READ_FILE_SCHEMA["description"] += " " + _ODF_SPECIAL_GUIDANCE
WRITE_FILE_SCHEMA["description"] += " " + _ODF_SPECIAL_GUIDANCE

_CAB_GUIDANCE = (
    ' CAB: read_file lists checked regular-file members of genuine bounded CAB 1.3; '
    'write_file format=cab_extract with exact content JSON {"source":"input.cab"} '
    'extracts all files into a NEW own-workspace folder using create-only publication. '
    'Supports single-cabinet NONE/MSZIP including shared 32 KiB history; never executes members. '
    'Input and decoded total are at most 1000000 bytes, 128 files/folders and 1024 blocks; '
    'decoded bytes cannot exceed max(65536, compressed bytes*200). '
    'Present checksums are verified; checksum zero means absent per CAB specification. '
    'LZX, Quantum, spanning cabinets, reserve extensions, executable attributes, special/unsafe '
    'names, ambiguous encodings, overlapping/gapped data, creation/editing/conversion refuse. '
)
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'].append('cab_extract')
WRITE_FILE_SCHEMA['description'] += _CAB_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _CAB_GUIDANCE
READ_FILE_SCHEMA['description'] += _CAB_GUIDANCE

READ_FILE_SCHEMA['description'] += ' LHA/LZH: bounded level 0/1/2 ASCII-name regular files/directories using -lh0-, -lh5-, -lh6-, -lh7- and -lhd- can be listed. Links, special members, SFX, unsupported headers/methods/encodings and corrupt input refuse as a whole.'
WRITE_FILE_SCHEMA['description'] += ' LHA/LZH extraction: format=lha_extract with exactly {"source":"input.lzh"} (or .lha) writes into a NEW folder. Same bounded read profiles; no LHA creation/edit/conversion. The isolated decoder needs 14 seconds remaining on the original call.'

from tools.scoped_iwork import GUIDANCE as _IWORK_READ_GUIDANCE
READ_FILE_SCHEMA["description"] += _IWORK_READ_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _IWORK_READ_GUIDANCE

# Explicit bounded native formula writes; ODM remains read-only.
from tools.scoped_odf_formula import GUIDANCE as _FORMULA_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["odf_formula_create", "odf_formula_edit"]
WRITE_FILE_SCHEMA["description"] += _FORMULA_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _FORMULA_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _FORMULA_GUIDANCE

# Bounded native BIFF12 scalar writes; no converter fallback.
from tools.scoped_xlsb_write import GUIDANCE as _XLSB_WRITE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["xlsb_create", "xlsb_edit"]
for _target in (WRITE_FILE_SCHEMA, WRITE_FILE_SCHEMA["parameters"]["properties"]["format"], WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]):
    _target["description"] += _XLSB_WRITE_GUIDANCE

_MSG_WRITE_GUIDANCE = 'Native MSG: msg_create takes exact JSON {"sender":{"email":"a@example.test","name":"Alice"},"recipients":[{"type":"to","email":"b@example.test","name":"Bob"}],"subject":"Subject","body_text":"Plain body"}; names are optional, type is to/cc/bcc. Nonempty Unicode text, simple ASCII SMTP addresses, 1..128 recipients; no attachments or custom properties. msg_edit takes exactly {"source":"mail.msg","source_sha256":"<current read_file hash>","old_text":"unique literal","new_text":"replacement"}. It changes one unique plain-body literal into a NEW .msg, retaining every other stream and storage metadata; container allocation is rebuilt. Only supported passive properties and plain-only email qualify; rich/alternate bodies, attachments, custom/named/active properties and body caches refuse. No conversion, sending, importing, overwrite, identity authentication or Outlook application acceptance is claimed. '
WRITE_FILE_SCHEMA['description'] += _MSG_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'] += ['msg_create', 'msg_edit']
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _MSG_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _MSG_WRITE_GUIDANCE

_ARJ_GUIDANCE = 'ARJ: read_file validates genuine single-volume .arj archives and lists member names, sizes and SHA-256 hashes; read a returned extracted path separately for its content. write_file format=arj_extract with exactly {"source":"input.arj"} extracts all validated members atomically into a NEW folder. Supports stored method0, block Huffman/LZ methods1–3 and fast LZ method4; 1000000-byte input and total output, 128 members, ratio200, ASCII safe names only. Encryption, multivolume, SFX, extended metadata, text-mode conversion, links/special members, unsafe/duplicate names and unrecognized profiles refuse the entire operation. The source is unchanged; no ARJ creation, raw text write, patch, editing or conversion. '
READ_FILE_SCHEMA["description"] += _ARJ_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _ARJ_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("arj_extract")
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _ARJ_GUIDANCE

# Genuine bounded OpenOffice.org 1.0 create/copy-edit operations.
_LEGACY_OPENOFFICE_WRITE_GUIDANCE = 'Creation: write_file format=legacy_openoffice_create into a NEW .sxw/.stw/.sxc/.stc/.sxi/.sti path. Text uses {"blocks":[{"type":"paragraph","text":"Hello"},{"type":"heading","level":1,"text":"Title"},{"type":"table","rows":[["A","B"]]}]}; sheets use {"sheets":[{"name":"Data","rows":[["literal",12,true,null]]}]}; slides use {"slides":[{"title":"Title","paragraphs":["Body"]}]}. Exact schemas, at most100000 UTF-8 JSON bytes; single-line strings, no tabs, leading/trailing/repeated ASCII spaces. Strings including = are literals, no formulas; each document/template has its own genuine MIME. For a preserving copy use format=legacy_openoffice_edit, NEW same extension, JSON {"source":"source.sxw","source_sha256":"<read_file hash>","old_text":"Complete old paragraph","new_text":"Complete replacement"}. Changes exactly one complete plain paragraph or heading leaf in content.xml; unselected XML bytes, other member payloads and descriptive ZIP metadata are preserved. No substring/split-run, typed/formula/repeated/spanned cell, unresolved revision, unknown-member or whitespace-sensitive edit. Original unchanged; raw overwrite, conversion, template instantiation and render/Office compatibility remain unsupported.'
WRITE_FILE_SCHEMA['description'] += _LEGACY_OPENOFFICE_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _LEGACY_OPENOFFICE_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'] += ['legacy_openoffice_create', 'legacy_openoffice_edit']

from tools.scoped_epub_write import GUIDANCE as _EPUB_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'] += ['epub_create', 'epub_edit']
WRITE_FILE_SCHEMA['description'] += _EPUB_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _EPUB_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _EPUB_GUIDANCE

# Explicit Visio 2003 XML operations; binary/OPC Visio profiles remain read-only.
from tools.scoped_vdx_write import GUIDANCE as _VDX_WRITE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"] += ["vdx_create", "vdx_text_edit"]
WRITE_FILE_SCHEMA["description"] += _VDX_WRITE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _VDX_WRITE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _VDX_WRITE_GUIDANCE

from tools.scoped_xps_write import GUIDANCE as _XPS_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'] += ['xps_create', 'xps_edit']
WRITE_FILE_SCHEMA['description'] += _XPS_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _XPS_WRITE_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _XPS_WRITE_GUIDANCE

from tools.scoped_odg_edit import GUIDANCE as _ODG_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("diagram_text_edit")
WRITE_FILE_SCHEMA["description"] += _ODG_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["description"] += _ODG_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]["description"] += _ODG_EDIT_GUIDANCE

# Access is passive native read only in every advertised file direction.
READ_FILE_SCHEMA["description"] += ' Access MDB/ACCDB: read_file decodes bounded local scalar user tables in unencrypted Jet4 MDB (Access2000/2002/2003) or ACE2007 ACCDB. System flags/MSys namespace excluded; stored values are untrusted. At most1000000 bytes,16 user tables,64 columns/table,1024 rows/table,8192 cells total,4096 characters/text value. Supported scalar booleans, byte/int16/int32, finite floats, exact decimal currency, raw Access date/time serials (epoch1899-12-30), binary hex, text and GUID. No SQL, query evaluation, external connections, DB execution or macros. Passwords/encryption, Jet3/newer ACE, memo/OLE/decimal/complex/calculated fields, schema evolution, linked/hidden user tables, overflow rows and multi-page table definitions refuse the whole input. Read all returned pages; partial pagination does not cover the whole table. All MDB/ACCDB creation, editing, raw writes and conversion remain unsupported. '
WRITE_FILE_SCHEMA["description"] += ' Access MDB/ACCDB: read_file decodes bounded local scalar user tables in unencrypted Jet4 MDB (Access2000/2002/2003) or ACE2007 ACCDB. System flags/MSys namespace excluded; stored values are untrusted. At most1000000 bytes,16 user tables,64 columns/table,1024 rows/table,8192 cells total,4096 characters/text value. Supported scalar booleans, byte/int16/int32, finite floats, exact decimal currency, raw Access date/time serials (epoch1899-12-30), binary hex, text and GUID. No SQL, query evaluation, external connections, DB execution or macros. Passwords/encryption, Jet3/newer ACE, memo/OLE/decimal/complex/calculated fields, schema evolution, linked/hidden user tables, overflow rows and multi-page table definitions refuse the whole input. Read all returned pages; partial pagination does not cover the whole table. All MDB/ACCDB creation, editing, raw writes and conversion remain unsupported. '

from tools.scoped_pub import GUIDANCE as _PUB_GUIDANCE
from tools.scoped_pub_write import GUIDANCE as _PUB_EDIT_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['format']['enum'] += ['pub_text_edit']
WRITE_FILE_SCHEMA['parameters']['properties']['format']['description'] += _PUB_EDIT_GUIDANCE
WRITE_FILE_SCHEMA['parameters']['properties']['content']['description'] += _PUB_EDIT_GUIDANCE
WRITE_FILE_SCHEMA['description'] += _PUB_EDIT_GUIDANCE
READ_FILE_SCHEMA['description'] += ' ' + _PUB_GUIDANCE
WRITE_FILE_SCHEMA['description'] += ' ' + _PUB_GUIDANCE

_ONENOTE_GUIDANCE = 'OneNote .one: read_file returns bounded current titles and stored text in persisted page/outline order from desktop OneStore v42 sections (1000000-byte tool input). Continue every partial page using next_offset/next_char_offset and verify source_sha256. Coverage is PARTIAL: images, ink and attachments are explicit non-text markers, never rendered, recognized or extracted. Committed default-context role-1 revisions only; stale/uncommitted data is not scanned. Encrypted, conflict/deleted, unsupported graph/text or hidden paragraph-style profiles refuse. Hidden text runs are omitted. No .onepkg/.onetoc2/sync-store reads, password support, external-resource loading, general creation, conversion or raw overwrite; only the separate bounded onenote_text_edit profile can edit. '
READ_FILE_SCHEMA["description"] += _ONENOTE_GUIDANCE
WRITE_FILE_SCHEMA["description"] += _ONENOTE_GUIDANCE

from tools.scoped_onenote_edit import GUIDANCE as _ONENOTE_EDIT_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("onenote_text_edit")
for _target in (READ_FILE_SCHEMA, WRITE_FILE_SCHEMA, WRITE_FILE_SCHEMA["parameters"]["properties"]["format"], WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]):
    _target["description"] += _ONENOTE_EDIT_GUIDANCE
# Native Project is intentionally exposed only inside the admitted workspace lane.
from tools.scoped_mpp import GUIDANCE as _MPP_GUIDANCE
READ_FILE_SCHEMA['description'] += _MPP_GUIDANCE
WRITE_FILE_SCHEMA['description'] += _MPP_GUIDANCE

from tools.scoped_mpp_write import GUIDANCE as _MPP_WRITE_GUIDANCE
WRITE_FILE_SCHEMA["parameters"]["properties"]["format"]["enum"].append("mpp_task_name_edit")
for _mpp_target in (WRITE_FILE_SCHEMA, WRITE_FILE_SCHEMA["parameters"]["properties"]["format"], WRITE_FILE_SCHEMA["parameters"]["properties"]["content"]):
    _mpp_target["description"] += _MPP_WRITE_GUIDANCE
