"""Plugin-owned durable state and namespaced settings helpers (split out of hermes_cli.plugins)."""

from __future__ import annotations

import json
import errno
import math
import os
import re
import stat
import threading
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, Mapping

from hermes_constants import get_hermes_home
from hermes_cli.plugins_manifest import _portable_skill_namespace

_PLUGIN_SETTING_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_PLUGIN_SETTING_RESERVED_ROOTS = frozenset({"model", "plugins", "security", "settings"})
_PLUGIN_STATE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_PLUGIN_STATE_QUOTA_BYTES = 10 * 1024 * 1024
# This deployment retains worker associations with their verified runtime pins.
_FRIDAY_REWORK_STATE_QUOTA_BYTES = 64 * 1024 * 1024
_PLUGIN_STATE_LOCKS: Dict[str, threading.RLock] = {}
_PLUGIN_STATE_LOCKS_GUARD = threading.Lock()


def _plugin_relative_segments(key: str) -> tuple[str, ...]:
    """Validate/split a plugin-relative settings key; global paths, traversal, and core roots are rejected
    before any config read.

    The public API accepts only relative keys (``endpoint`` or ``retry.policy``). See #64227.
    """
    if not isinstance(key, str):
        raise ValueError("Expected a plugin-relative config key string")
    segments = tuple(key.split("."))
    invalid = not key or "/" in key or "\\" in key or segments[0].lower() in _PLUGIN_SETTING_RESERVED_ROOTS
    if invalid or not all(_PLUGIN_SETTING_SEGMENT_RE.fullmatch(segment) for segment in segments):
        raise ValueError(
            "Expected a plugin-relative config key such as 'endpoint' or "
            "'retry.policy'; global, cross-plugin, and traversal paths are forbidden"
        )
    return segments


def _nested_plugin_value(root: object, segments: tuple[str, ...], default: Any) -> Any:
    """Walk ``segments`` through nested mappings; ``default`` on the first miss."""
    current = root
    for segment in segments:
        if not isinstance(current, Mapping) or segment not in current:
            return default
        current = current[segment]
    return current


def _nested_plugin_mapping(segments: tuple[str, ...], value: Any) -> dict[str, Any]:
    """Wrap ``value`` in nested single-key dicts, outermost first."""
    nested: Any = value
    for segment in reversed(segments):
        nested = {segment: nested}
    return nested


def _plugin_settings_entry(config: object, plugin_id: str) -> Mapping[str, Any] | None:
    """``plugins.entries.<plugin_id>`` as a mapping, else ``None``."""
    entry = _nested_plugin_value(config, ("plugins", "entries", plugin_id), None)
    return entry if isinstance(entry, Mapping) else None


def save_plugin_setting(plugin_id: str, segments: tuple[str, ...], value: Any) -> None:
    """Atomically write one value under ``plugins.entries.<plugin_id>.settings``.

    THE writer for plugin settings: ``PluginContext.set_config`` (the plugin itself) and the
    Desktop/TUI ``plugins.manage settings`` action both land here so managed-install and
    administrator-managed-key refusals, the cross-process lock and the fail-closed raw read
    are enforced once. ``segments`` must already be validated by :func:`_plugin_relative_segments`.
    """
    from hermes_cli import config as config_mod
    from hermes_cli import managed_scope

    if config_mod.is_managed():
        raise PermissionError("Plugin settings cannot be changed in a managed install")
    full_path = ("plugins", "entries", plugin_id, "settings", *segments)
    dotted_path = ".".join(full_path)
    if managed_scope.is_key_managed(dotted_path):
        raise PermissionError(f"Plugin setting {dotted_path!r} is administrator-managed")
    partial = _nested_plugin_mapping(full_path[:4], _nested_plugin_mapping(segments, value))
    # The lock covers merge-read plus atomic save so sibling plugin writes (threads or
    # processes) cannot race between the two steps.
    with _locked_plugin_state(config_mod.get_config_path()), config_mod._CONFIG_LOCK:
        # Fail closed on malformed YAML: save_config degrades parse failures to {} — safe
        # for reads, destructive for read-modify-write.
        config_mod.read_user_config_raw()
        config_mod.save_config(partial, preserve_keys={full_path}, merge_existing=True)


def _plugin_data_namespace(plugin_id: str, skill_namespace: str) -> str:
    """Return one Windows-safe directory component for plugin-owned data. Portable Agent Plugins already
    receive this exact PLUGIN_DATA path; otherwise the fixed prefix avoids Windows reserved device names and
    the digest prevents fold collisions."""
    candidate = skill_namespace or plugin_id
    portable = skill_namespace and candidate.startswith("agent-plugin-")
    if portable and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,191}", candidate):
        return candidate
    return _portable_skill_namespace(candidate)


class LockAcquisitionBudget:
    """Cumulative acquisition allowance for sequential calls on one thread.

    Time outside ``acquiring`` (including native work and filesystem I/O) is
    excluded. A copied context cannot spend the same allowance concurrently:
    cross-thread use and overlapping acquisition scopes fail closed, without
    introducing another lock. Exhaustion persists for this object's lifetime.
    """

    def __init__(self, seconds: float) -> None:
        if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
                or not math.isfinite(seconds) or seconds < 0):
            raise ValueError("lock budget must be finite nonnegative seconds")
        self._remaining = seconds
        # Thread identifiers can be reused after exit; retain the creator itself.
        self._owner_thread = threading.current_thread()
        self._acquiring = False

    @contextmanager
    def acquiring(self):
        if threading.current_thread() is not self._owner_thread or self._acquiring:
            raise RuntimeError("lock budget requires sequential same-thread acquisition")
        if self._remaining <= 0:
            raise TimeoutError("Plugin state lock budget exceeded")
        began = time.monotonic()
        self._acquiring = True
        try:
            yield began + self._remaining
        finally:
            self._remaining = max(0.0, self._remaining - max(0.0, time.monotonic() - began))
            self._acquiring = False


def _acquisition_scope(deadline, budget):
    return budget.acquiring() if budget is not None else nullcontext(deadline)


def _lock_remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Plugin state lock deadline exceeded")
    return remaining


@contextmanager
def _thread_state_lock(lock, deadline, budget=None):
    with _acquisition_scope(deadline, budget) as acquisition_deadline:
        if acquisition_deadline is None:
            lock.acquire()
        elif not lock.acquire(timeout=_lock_remaining(acquisition_deadline)):
            raise TimeoutError("Plugin state lock deadline exceeded")
    try:
        yield
    finally:
        lock.release()


def _acquire_state_file(handle, deadline):
    if os.name == "nt":  # pragma: no cover - Windows CI
        import msvcrt
        def acquire():
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK if deadline is None else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        def acquire():
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | (fcntl.LOCK_NB if deadline is not None else 0))
    while True:
        if deadline is not None:
            _lock_remaining(deadline)
        try:
            acquire()
            return
        except OSError as exc:
            if deadline is None or exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            time.sleep(min(.01, _lock_remaining(deadline)))


@contextmanager
def _locked_plugin_state(path: Path, *, lock_deadline: float | None = None,
                         lock_budget: LockAcquisitionBudget | None = None):
    """Serialize state read-modify-write across threads/processes (fcntl / msvcrt). The lock lives in a
    sibling file because atomic replacement changes the target's inode."""
    if lock_deadline is not None and (isinstance(lock_deadline, bool)
            or not isinstance(lock_deadline, (float, int)) or not math.isfinite(lock_deadline)):
        raise ValueError("lock_deadline must be a finite monotonic timestamp")
    if lock_budget is not None and (not isinstance(lock_budget, LockAcquisitionBudget)
                                    or lock_deadline is not None):
        raise ValueError("lock_budget must be a LockAcquisitionBudget, without lock_deadline")
    lock_path = path.with_name(f".{path.name}.lock")
    with _thread_state_lock(_PLUGIN_STATE_LOCKS_GUARD, lock_deadline, lock_budget):
        thread_lock = _PLUGIN_STATE_LOCKS.setdefault(str(lock_path.resolve(strict=False)), threading.RLock())
    with _thread_state_lock(thread_lock, lock_deadline, lock_budget):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a+b") as handle:
            if os.name == "nt":  # pragma: no cover - exercised on Windows CI
                import msvcrt
                if handle.seek(0, os.SEEK_END) == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
            with _acquisition_scope(lock_deadline, lock_budget) as acquisition_deadline:
                _acquire_state_file(handle, acquisition_deadline)
            try:
                yield
            finally:
                if os.name == "nt":  # pragma: no cover - exercised on Windows CI
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _private_friday_state_directory(directory: Path, *, repair: bool) -> None:
    """Create/tighten owned Friday metadata without replacing any state bytes.

    Earlier reads created this directory and its native lock at process umask.
    Validate descriptor ownership/type before tightening; never follow a
    substituted directory, lock, or retained state file. An established native
    transaction retains its existing strict drift checks instead of repairing.
    """
    home = directory.parent.parent
    if not home.is_absolute() or home.resolve() != home:
        raise PermissionError("unsafe_plugin_state_home")
    from hermes_constants import assert_named_profile_home_live
    assert_named_profile_home_live(home)
    if repair:
        home.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptors = []
    uid = os.getuid()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        current = os.open(home, flags); descriptors.append(current)
        if os.fstat(current).st_uid != uid:
            raise PermissionError("foreign_plugin_state_owner")
        for name in ("plugin-data", directory.name):
            if repair:
                try:
                    os.mkdir(name, 0o700, dir_fd=current)
                except FileExistsError:
                    pass
            child = os.open(name, flags, dir_fd=current); descriptors.append(child)
            info = os.fstat(child)
            if info.st_uid != uid:
                raise PermissionError("foreign_plugin_state_owner")
            if stat.S_IMODE(info.st_mode) != 0o700:
                if not repair:
                    raise PermissionError("plugin_state_directory_changed")
                os.fchmod(child, 0o700); os.fsync(child)
            linked = os.stat(name, dir_fd=current, follow_symlinks=False)
            if (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino):
                raise PermissionError("plugin_state_directory_changed")
            current = child
        for name in ("state.json", ".state.json.lock"):
            try:
                retained = os.stat(name, dir_fd=current, follow_symlinks=False)
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(retained.st_mode) or retained.st_uid != uid or retained.st_nlink != 1:
                raise PermissionError("unsafe_native_plugin_state")
        lock = os.open(".state.json.lock", (os.O_RDWR | os.O_CREAT if repair else os.O_RDONLY) | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                       0o600, dir_fd=current); descriptors.append(lock)
        info = os.fstat(lock)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != uid or info.st_nlink != 1:
            raise PermissionError("unsafe_native_plugin_state_lock")
        if stat.S_IMODE(info.st_mode) != 0o600:
            if not repair:
                raise PermissionError("plugin_state_lock_changed")
            os.fchmod(lock, 0o600); os.fsync(lock)
        linked = os.stat(".state.json.lock", dir_fd=current, follow_symlinks=False)
        if (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino):
            raise PermissionError("plugin_state_lock_changed")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


class PluginState:
    """Atomic, quota-bounded JSON key/value state owned by one plugin."""

    def __init__(self, plugin_id: str, skill_namespace: str = "") -> None:
        self._plugin_id = plugin_id
        self._data_namespace = _plugin_data_namespace(plugin_id, skill_namespace)
        self._native_namespaces = {}

    @property
    def data_dir(self) -> Path:
        """Profile-scoped PLUGIN_DATA; Friday creates/validates private metadata."""
        directory = get_hermes_home() / "plugin-data" / self._data_namespace
        if self._plugin_id == "friday_rework" and os.name == "posix":
            _private_friday_state_directory(directory, repair=str(directory) not in self._native_namespaces)
        return directory

    @property
    def directory_storage_readonly(self) -> Path:
        """Existing Friday metadata only; never initialize or repair storage."""
        if self._plugin_id != "friday_rework" or os.name != "posix":
            raise RuntimeError("storage_readonly_requires_native_Friday_POSIX_state")
        directory = get_hermes_home() / "plugin-data" / self._data_namespace
        _private_friday_state_directory(directory, repair=False)
        return directory

    def get_storage_readonly(self, key: str, default: Any = None, *,
                             lock_deadline: float | None = None,
                             lock_budget: LockAcquisitionBudget | None = None) -> Any:
        """Read existing state under its native lock without filesystem writes.

        Missing storage, unsafe custody or concurrent namespace changes are
        errors. A missing key in a validated document retains normal get semantics.
        The writer's thread lock and exclusive flock serialize atomic replacement.
        """
        self._validate_key(key)
        if lock_deadline is not None and (isinstance(lock_deadline, bool)
                or not isinstance(lock_deadline, (float, int)) or not math.isfinite(lock_deadline)):
            raise ValueError("lock_deadline must be a finite monotonic timestamp")
        if lock_budget is not None and (not isinstance(lock_budget, LockAcquisitionBudget)
                                        or lock_deadline is not None):
            raise ValueError("lock_budget requires LockAcquisitionBudget without lock_deadline")
        if lock_deadline is None and lock_budget is None:
            lock_deadline = time.monotonic() + 2
        directory = self.directory_storage_readonly
        path = directory / "state.json"
        lock_path = directory / ".state.json.lock"
        with _thread_state_lock(_PLUGIN_STATE_LOCKS_GUARD, lock_deadline, lock_budget):
            thread_lock = _PLUGIN_STATE_LOCKS.setdefault(str(lock_path), threading.RLock())
        with _thread_state_lock(thread_lock, lock_deadline, lock_budget):
            dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                di = os.fstat(dirfd)
                def private(info, *, directory=False):
                    kind = stat.S_ISDIR if directory else stat.S_ISREG
                    if (not kind(info.st_mode) or info.st_uid != os.getuid()
                            or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
                            or not directory and info.st_nlink != 1):
                        raise PermissionError("unsafe_storage_readonly_state")
                def identity(info):
                    return info.st_dev, info.st_ino
                private(di, directory=True)
                lockfd = os.open(".state.json.lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                                 dir_fd=dirfd)
                try:
                    li = os.fstat(lockfd); private(li)
                    with os.fdopen(lockfd, "rb", closefd=False) as handle:
                        with _acquisition_scope(lock_deadline, lock_budget) as acquisition_deadline:
                            _acquire_state_file(handle, acquisition_deadline)
                        try:
                            def check():
                                if self.directory_storage_readonly != directory:
                                    raise PermissionError("storage_readonly_namespace_changed")
                                current = os.stat(directory, follow_symlinks=False); private(current, directory=True)
                                if identity(current) != identity(di):
                                    raise PermissionError("storage_readonly_directory_changed")
                                current = os.stat(".state.json.lock", dir_fd=dirfd, follow_symlinks=False); private(current)
                                if identity(current) != identity(li):
                                    raise PermissionError("storage_readonly_lock_changed")
                            check()
                            statefd = os.open("state.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                                              dir_fd=dirfd)
                            try:
                                before = os.fstat(statefd); private(before)
                                if not 0 <= before.st_size <= self.quota_bytes:
                                    raise ValueError("storage_readonly_state_quota")
                                with os.fdopen(statefd, "rb", closefd=False) as stream:
                                    raw = stream.read(self.quota_bytes + 1)
                                if len(raw) > self.quota_bytes:
                                    raise ValueError("storage_readonly_state_quota")
                                data = json.loads(raw.decode("utf-8-sig"))
                                after = os.fstat(statefd); private(after)
                                linked = os.stat("state.json", dir_fd=dirfd, follow_symlinks=False); private(linked)
                                signature = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                                if signature(before) != signature(after) or signature(after) != signature(linked):
                                    raise PermissionError("storage_readonly_state_changed")
                                if not isinstance(data, dict):
                                    raise ValueError("storage_readonly_state_root_not_object")
                                check()
                                return data.get(key, default)
                            finally:
                                os.close(statefd)
                        finally:
                            import fcntl
                            fcntl.flock(lockfd, fcntl.LOCK_UN)
                finally:
                    os.close(lockfd)
            finally:
                os.close(dirfd)

    @property
    def path(self) -> Path:
        return self.data_dir / "state.json"

    @property
    def quota_bytes(self) -> int:
        if self._plugin_id == "friday_rework":
            return _FRIDAY_REWORK_STATE_QUOTA_BYTES
        return _PLUGIN_STATE_QUOTA_BYTES

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str) or not _PLUGIN_STATE_KEY_RE.fullmatch(key) or ".." in key:
            raise ValueError(
                "Plugin state keys must be 1-128 characters using letters, "
                "numbers, '_', '-', '.', or ':' (without '..')"
            )

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            with open(self.path, encoding="utf-8-sig") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"Cannot parse plugin state {self.path}: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"Cannot parse plugin state {self.path}: root must be an object")
        return data

    def get(self, key: str, default: Any = None, *, lock_deadline: float | None = None,
            lock_budget: LockAcquisitionBudget | None = None) -> Any:
        self._validate_key(key)
        with _locked_plugin_state(self.path, lock_deadline=lock_deadline, lock_budget=lock_budget):
            return self._read_unlocked().get(key, default)

    def set_commit(self, key: str, value: Any, *, cutoff: float | None = None,
                   lock_deadline: float | None = None, lock_budget: LockAcquisitionBudget | None = None,
                   expected_value: Any = None, compare: bool = False, journals=()):
        """Additional native witness API; public set still returns None."""
        self._validate_key(key)
        if os.name != "posix":
            raise RuntimeError("native durable commit requires qualified POSIX custody")
        from hermes_cli.friday_native_state import META, set_native
        if key == META:
            raise ValueError("native state generation is reserved")
        return set_native(self, key, value, cutoff=cutoff, lock_deadline=lock_deadline,
                          lock_budget=lock_budget, expected_value=expected_value,
                          compare=compare, journals=journals)

    def set(self, key: str, value: Any, *, lock_deadline: float | None = None,
            lock_budget: LockAcquisitionBudget | None = None) -> None:
        """Atomically set one JSON value without dropping concurrent updates."""
        self._validate_key(key)
        with _locked_plugin_state(self.path, lock_deadline=lock_deadline, lock_budget=lock_budget):
            data = self._read_unlocked()
            if self._plugin_id == "friday_rework" and key == "product_access.v1":
                from hermes_cli.friday_product_access import KEY, advance_access
                value = advance_access(data.get(KEY, {"schema": KEY, "users": {}}), value)
            data[key] = value
            try:
                encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Plugin state value for {key!r} is not JSON-serializable") from exc
            if len(encoded) > self.quota_bytes:
                raise ValueError(
                    f"Plugin state quota exceeded: {len(encoded)} bytes is greater "
                    f"than the {self.quota_bytes}-byte per-plugin quota"
                )
            from utils import atomic_json_write
            atomic_json_write(self.path, data, mode=0o600)
