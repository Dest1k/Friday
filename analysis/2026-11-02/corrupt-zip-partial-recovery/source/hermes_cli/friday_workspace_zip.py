"""Bounded ordinary archives: descriptor custody, no payload execution.

No globbing, shell, external codec, in-place archive editing or overwrite. Extraction
builds a private new tree before one atomic NOREPLACE publication. The optional
reviewed 7z codec consumes pure bytes under the original native call's clock.
"""
from io import BytesIO
from pathlib import PurePosixPath
import hashlib
import json
import math
import os
import stat
import time
import unicodedata
import uuid
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED, BadZipFile
from tools.scoped_zip import read_zip_member, ZipMemberDataError

from hermes_cli.friday_user_scope import ScopeDenied, workspace_document
from hermes_cli.friday_workspace_revision import check, _move
from hermes_cli.friday_workspace_docx import _check_parent, _create_bytes

MAX_BYTES = 1000000
MAX_ENTRIES = 128
MAX_DEPTH = 16
MAX_SECRET_SCAN = 10000000
TAR_FORMATS = frozenset(('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'tar.zst'))
STREAM_SUFFIXES = {'.gz': 'gzip', '.bz2': 'bzip2', '.xz': 'xz', '.zst': 'zstd'}
STREAM_FORMATS = frozenset(STREAM_SUFFIXES.values())
TAR_SUFFIXES = (('.tar.bz2', 'tar.bz2'), ('.tar.zst', 'tar.zst'), ('.tar.gz', 'tar.gz'), ('.tar.xz', 'tar.xz'), ('.tbz2', 'tar.bz2'), ('.tzst', 'tar.zst'), ('.tgz', 'tar.gz'), ('.txz', 'tar.xz'), ('.tar', 'tar'))


def _secret_name(part):
    lower = part.casefold()
    return (lower in {'credentials', 'credentials.json', 'secrets', 'secrets.json',
                     'secrets.txt', 'token', 'token.txt', 'id_rsa', 'id_ed25519'}
            or lower.endswith(('.pem', '.key', '.p12', '.pfx')))


def _path(value, *, directory=False):
    if not isinstance(value, str) or not value or len(value.encode('utf-8')) > 512:
        raise ScopeDenied()
    name = value[:-1] if directory and value.endswith('/') else value
    pieces = name.split('/')
    if (not name or len(pieces) > MAX_DEPTH or name != unicodedata.normalize('NFC', name)
            or any(c in name for c in ('\\', ':', '\x00'))
            or any(unicodedata.category(c).startswith('C') for c in name)
            or any(not p or p in ('.', '..') or p.startswith('.') for p in pieces)):
        raise ScopeDenied()
    # Own-workspace confinement already excludes service secrets. Also refuse
    # explicit credential-shaped members; never silently omit them from a ZIP.
    for part in pieces:
        if _secret_name(part):
            raise ScopeDenied()
    return name


def _object(content, field):
    if not isinstance(content, str) or len(content.encode('utf-8')) > 100000:
        raise ScopeDenied()
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ScopeDenied()
            result[key] = value
        return result
    try:
        value = json.loads(content, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        raise ScopeDenied() from None
    if not isinstance(value, dict) or set(value) != {field}:
        raise ScopeDenied()
    return value[field]



def _archive_spec(content, required, optional=()):
    # Same bounded duplicate-key discipline as the original single-key schema.
    if type(content) is not str or len(content.encode('utf-8')) > 100000:
        raise ScopeDenied()
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ScopeDenied()
            result[key] = item
        return result
    try:
        value = json.loads(content, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        raise ScopeDenied() from None
    if (type(value) is not dict or not set(required) <= set(value) or
            not set(value) <= set(required) | set(optional)):
        raise ScopeDenied()
    return value


def _archive_password(password):
    from hermes_cli.friday_workspace_7z_codec import _password, CodecRefused
    try:
        _password(password)
    except CodecRefused:
        raise ScopeDenied() from None
    return password


def _password_path(password, *names):
    # A caller must not reuse its credential as any exposed output/member path.
    if password is not None and any(password in name for name in names):
        raise ScopeDenied()

def _source(cap, relative):
    relative = _path(relative)
    data, actual, identity = workspace_document(
        str(cap.home / 'workspace' / relative), max_bytes=MAX_BYTES, with_identity=True)
    if actual != relative:
        raise ScopeDenied()
    check(cap)
    return data, identity


def _archive_source(cap, relative, parts=None):
    from hermes_cli.friday_workspace_7z_parts import (
        is_split_path, ordered_parts, assemble, Split7zRefused)
    if not is_split_path(relative):
        if parts is not None:
            raise Split7zRefused('archive_parts_invalid')
        data, identity = _source(cap, relative)
        return data, [(relative, data, identity)], None
    paths = ordered_parts(relative, parts)
    sources = []; payloads = []; manifest = []; total = 0
    for path in paths:
        check(cap)
        try:
            data, identity = _source(cap, path)
        except ScopeDenied:
            # Missing, linked, or unauthorized parts share one content-free
            # refusal; do not expose which custody check failed.
            raise Split7zRefused('archive_parts_unavailable') from None
        total += len(data)
        if total > MAX_BYTES:
            raise Split7zRefused('archive_parts_invalid')
        sources.append((path, data, identity)); payloads.append(data)
        manifest.append(dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    data = assemble(payloads, max_bytes=MAX_BYTES)
    _verify(cap, sources)
    return data, sources, manifest


def _check_secrets(data, *, depth=0, budget=None, _compression_depth=0):
    """Reuse native secret detection without altering a user's archived bytes.

    Inspect bounded nested ZIP document parts too (DOCX/XLSX are ZIP packages).
    Unsupported depth, encrypted inner data and over-budget scans refuse the
    whole operation; they never become silent secret-scan exceptions.
    """
    from agent.redact import redact_sensitive_text, _is_secret_file_arg
    if budget is None:
        budget = [MAX_SECRET_SCAN]
    budget[0] -= len(data)
    if budget[0] < 0:
        raise ScopeDenied()
    text = data.decode('utf-8', errors='ignore')
    if redact_sensitive_text(text, force=True, redact_url_credentials=True) != text:
        raise ScopeDenied()
    compression = ('gzip' if data.startswith(b'\x1f\x8b') else
                   'bz2' if data.startswith(b'BZh') else
                   'xz' if data.startswith(b'\xfd7zXZ\x00') else
                   'zstd' if data.startswith(b'\x28\xb5\x2f\xfd') else None)
    if compression is not None:
        if _compression_depth >= 4:
            raise ScopeDenied()
        from tools.scoped_tar import decompress_stream, TarError
        try:
            unpacked = decompress_stream(data, compression)
        except TarError:
            raise ScopeDenied() from None
        _check_secrets(unpacked, depth=depth, budget=budget,
                       _compression_depth=_compression_depth + 1)
        return
    if len(data) >= 512 and data[257:262] == b'ustar':
        if depth >= 2:
            raise ScopeDenied()
        for name, directory, payload in _tar_rows(data, 'tar'):
            _path(name, directory=directory)
            if not directory:
                _check_secrets(payload, depth=depth + 1, budget=budget)
        return
    if data.startswith((b'PK\x03\x04', b'PK\x05\x06')):
        if depth >= 2:
            raise ScopeDenied()
        try:
            with ZipFile(BytesIO(data)) as nested:
                infos = nested.infolist()
                if len(infos) > 256:
                    raise ScopeDenied()
                for info in infos:
                    if (_is_secret_file_arg(info.filename)
                            or any(_secret_name(p) for p in info.filename.replace('\\', '/').split('/'))
                            or info.flag_bits & 1
                            or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                            or info.file_size > budget[0]):
                        raise ScopeDenied()
                    if info.is_dir():
                        continue
                    part = read_zip_member(nested, data, info, budget[0])
                    if len(part) != info.file_size:
                        raise ScopeDenied()
                    _check_secrets(part, depth=depth+1, budget=budget)
        except (BadZipFile, EOFError, OSError, RuntimeError, NotImplementedError, ValueError):
            raise ScopeDenied() from None


def _verify(cap, sources):
    for relative, data, identity in sources:
        current, current_identity = _source(cap, relative)
        if current_identity != identity or current != data:
            raise ScopeDenied()


def _rows(data, *, allow_partial=False):
    """Inspect everything before any write; inflate at most one MiB in total."""
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ScopeDenied()
    if _zip_encrypted(data):
        raise ScopeDenied()
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= MAX_ENTRIES:
                raise ScopeDenied()
            names = set(); files = set(); rows = []; total = 0; damaged = []
            for info in infos:
                directory = info.is_dir()
                name = _path(info.filename, directory=directory)
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if (name in names or info.orig_filename != info.filename
                        or info.flag_bits & 1 or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                        or kind not in (0, stat.S_IFDIR if directory else stat.S_IFREG)
                        or info.file_size > MAX_BYTES
                        or info.file_size > max(4096, info.compress_size * 200)
                        or directory and info.file_size):
                    raise ScopeDenied()
                names.add(name)
                if not directory:
                    files.add(name)
                total += info.file_size
                if total > MAX_BYTES:
                    raise ScopeDenied()
                try:
                    payload = read_zip_member(archive, data, info, MAX_BYTES)
                except ZipMemberDataError:
                    if not allow_partial or directory:
                        raise
                    damaged.append(dict(path=name, reason='member_data_invalid',
                                        declared_bytes=info.file_size))
                    continue
                if len(payload) != info.file_size:
                    raise ScopeDenied()
                rows.append((name, directory, payload))
            for name in names:
                if any(str(parent) in files for parent in PurePosixPath(name).parents
                       if str(parent) != '.'):
                    raise ScopeDenied()
            return (rows, damaged) if allow_partial else rows
    except (BadZipFile, EOFError, OSError, RuntimeError, NotImplementedError, ValueError):
        raise ScopeDenied() from None


def archive_format(relative):
    from hermes_cli.friday_workspace_7z_parts import is_split_path
    lower = relative.lower()
    if is_split_path(relative):
        return '7z'
    for suffix, value in TAR_SUFFIXES:
        if lower.endswith(suffix):
            return value
    suffix = PurePosixPath(lower).suffix
    if suffix in ('.lha', '.lzh'):
        return 'lha'
    return STREAM_SUFFIXES.get(suffix, suffix.lstrip('.'))


def _stream_rows(data, relative):
    from tools.scoped_single_stream import decode_stream, StreamError
    format = archive_format(relative)
    if format not in STREAM_FORMATS:
        raise ScopeDenied()
    # Gzip optional names are untrusted metadata. Single streams have no member
    # registry: derive the sole extracted name from the workspace source name.
    member = _path(PurePosixPath(relative).name.rsplit('.', 1)[0])
    try:
        payload = decode_stream(data, format)
    except StreamError:
        raise ScopeDenied() from None
    return [(member, False, payload)]


def _tar_rows(data, format):
    from tools.scoped_tar import decode_tar, TarError
    try:
        rows = decode_tar(data, format)
    except TarError:
        raise ScopeDenied() from None
    for name, directory, payload in rows:
        if _path(name, directory=directory) != name:
            raise ScopeDenied()
    return rows


def _new_tar(cap, rows, format):
    from tools.scoped_tar import encode_tar, TarError
    check(cap)
    try:
        data = encode_tar(rows, format)
    except TarError:
        raise ScopeDenied() from None
    check(cap)
    if type(data) is not bytes or len(data) > MAX_BYTES:
        raise ScopeDenied()
    return data


def _manifest(rows, prefix=''):
    return [dict(path=prefix + name, directory=directory, bytes=len(data),
                 **({} if directory else {'sha256': hashlib.sha256(data).hexdigest()}))
            for name, directory, data in rows]


class _CodecFailure(Exception):
    def __init__(self, error, *, unknown=False):
        self.error, self.unknown = error, unknown


def _codec_failure(failure):
    if failure.unknown:
        from agent.web_call_context import _current
        call = _current.get()
        if call is not None and hasattr(call, 'agent'):
            call.agent._friday_reply_effect_unknown = True
    result = dict(success=False, error=failure.error,
                  effect_disposition='unknown' if failure.unknown else 'none')
    budget = _inline_budget()
    if not _fits(result, budget):
        # Keep custody UNKNOWN even if its precise finite error cannot fit.
        result['error'] = 'capacity'
    if not _fits(result, budget):
        result.pop('error')
    return _encode(result)


def _codec_guard(cap, call, deadline):
    from agent.web_call_context import _current
    check(cap)
    if _current.get() is not call:
        raise ScopeDenied()
    # A later gate/exclusion change cannot extend this already-admitted codec
    # interval. Native check() still enforces any newly shorter deadline/stop.
    if time.monotonic() >= deadline:
        raise TimeoutError('archive_original_deadline')


def _codec(cap, operation, value, *, password=None, header_encryption=False):
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_7z_codec as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if (type(deadline) not in (int, float) or not math.isfinite(deadline)
            or deadline - time.monotonic() <= codec.WALL_SECONDS + 2):
        raise _CodecFailure('archive_codec_budget_insufficient')
    _codec_guard(cap, call, deadline)
    try:
        result = (codec.encode_7z(value, max_bytes=MAX_BYTES, max_entries=MAX_ENTRIES,
                                  password=password, header_encryption=header_encryption)
                  if operation == 'encode' else
                  codec.decode_7z(value, max_bytes=MAX_BYTES, max_entries=MAX_ENTRIES, password=password))
    except codec.CodecUnavailable:
        raise _CodecFailure('archive_codec_unavailable') from None
    except codec.CodecRefused as exc:
        # Cleanup failure concerns owned process custody even though the codec
        # itself never publishes files. Preserve UNKNOWN and suppress blind retry.
        if str(exc) == 'encrypted_archive':
            raise _CodecFailure('archive_password_required') from None
        raise _CodecFailure('archive_codec_cleanup_unconfirmed' if
            str(exc) == 'cleanup_unconfirmed' else 'archive_codec_refused',
            unknown=str(exc) == 'cleanup_unconfirmed') from None
    _codec_guard(cap, call, deadline)
    return result, lambda: _codec_guard(cap, call, deadline)


def _seven_rows(cap, data, *, password=None):
    decoded, guard = _codec(cap, 'decode', data, password=password)
    rows = []; names = set(); files = set(); scan_budget = [MAX_SECRET_SCAN]
    for name, directory, payload in decoded:
        # Codec preserves spelling, including a trailing slash for directories.
        # Apply the existing ordinary ZIP policy too: no NFC rewriting or secret
        # paths, and never silently drop a directory or member.
        name = _path(name, directory=directory)
        if name in names:
            raise ScopeDenied()
        names.add(name)
        if not directory:
            files.add(name)
            _check_secrets(payload, budget=scan_budget)
        rows.append((name, directory, payload))
    for name in names:
        if any(str(parent) in files for parent in PurePosixPath(name).parents
               if str(parent) != '.'):
            raise ScopeDenied()
    guard()
    return rows, guard


def _zip_encrypted(data):
    # Any AES indicator selects strict admission, including contradictory local
    # headers or an AES extra field without the required method/encryption bit.
    # Otherwise malformed AES can fall through the ordinary plaintext reader.
    import struct
    def aes_extra(extra):
        pos = 0
        while pos < len(extra):
            if pos + 4 > len(extra):
                raise ScopeDenied()
            kind, size = struct.unpack_from('<HH', extra, pos)
            pos += 4
            if pos + size > len(extra):
                raise ScopeDenied()
            if kind == 0x9901:
                return True
            pos += size
        return False
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= MAX_ENTRIES:
                raise ScopeDenied()
            for info in infos:
                if info.flag_bits & 1 or info.compress_type == 99 or aes_extra(info.extra):
                    return True
                local = info.header_offset
                if local < 0 or local + 30 > len(data) or data[local:local+4] != b'PK\x03\x04':
                    raise ScopeDenied()
                flags, method = struct.unpack_from('<HH', data, local + 6)
                nlen, xlen = struct.unpack_from('<HH', data, local + 26)
                start = local + 30 + nlen
                if start + xlen > len(data):
                    raise ScopeDenied()
                if flags & 1 or method == 99 or aes_extra(data[start:start+xlen]):
                    return True
            return False
    except (BadZipFile, ValueError, EOFError, OSError, struct.error):
        raise ScopeDenied() from None


def _zip_crypto(cap, operation, value, password):
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_zip_aes as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if (type(deadline) not in (int, float) or not math.isfinite(deadline)
            or deadline-time.monotonic() <= codec.WALL_SECONDS+2):
        raise _CodecFailure('archive_codec_budget_insufficient')
    guard = lambda: _codec_guard(cap, call, deadline)
    guard()
    try:
        result = (codec.encode_zip(value, password=password, checkpoint=guard)
                  if operation == 'encode' else
                  codec.decode_zip(value, password=password, checkpoint=guard))
    except codec.CodecUnavailable:
        raise _CodecFailure('archive_codec_unavailable') from None
    except codec.CodecRefused as exc:
        code = str(exc)
        error = {'password_required': 'archive_password_required',
                 'password_or_archive_invalid': 'archive_password_or_data_invalid',
                 'authentication_failed': 'archive_authentication_failed',
                 'unsupported_zip_profile': 'archive_encryption_profile_unsupported',
                 'cleanup_unconfirmed': 'archive_codec_cleanup_unconfirmed'}.get(code, 'archive_codec_refused')
        raise _CodecFailure(error, unknown=code == 'cleanup_unconfirmed') from None
    guard()
    return result, guard


def _zip_rows(cap, data, *, password=None):
    if not _zip_encrypted(data):
        return _rows(data), lambda: check(cap)
    decoded, guard = _zip_crypto(cap, 'decode', data, password)
    rows = []; scan_budget = [MAX_SECRET_SCAN]
    for name, directory, payload in decoded:
        name = _path(name, directory=directory)
        _password_path(password, name)
        if not directory:
            _check_secrets(payload, budget=scan_budget)
        rows.append((name, directory, payload))
    guard()
    return rows, guard


def _rar_rows(cap, data):
    """Consume the isolated RAR reader under this original native call's clock."""
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_rar_codec as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if (type(deadline) not in (int, float) or not math.isfinite(deadline)
            or deadline - time.monotonic() <= codec.WALL_SECONDS + 2):
        raise _CodecFailure('archive_codec_budget_insufficient')
    guard = lambda: _codec_guard(cap, call, deadline)
    guard()
    try:
        decoded = codec.read_rar_bytes(data, checkpoint=guard)
    except codec.RARCodecError as exc:
        code = str(exc)
        raise _CodecFailure('archive_codec_cleanup_unconfirmed' if
            code == 'rar_cleanup_unconfirmed' else 'archive_codec_unavailable' if
            code == 'rar_codec_unavailable' else 'archive_codec_refused',
            unknown=code == 'rar_cleanup_unconfirmed') from None
    if type(decoded) is not list or not 1 <= len(decoded) <= MAX_ENTRIES:
        raise ScopeDenied()
    rows = []; names = set(); files = set(); total = 0
    scan_budget = [MAX_SECRET_SCAN]
    for row in decoded:
        guard()
        if (type(row) is not tuple or len(row) != 2
                or not isinstance(row[0], str) or type(row[1]) is not bytes):
            raise ScopeDenied()
        raw_name, payload = row
        directory = raw_name.endswith('/')
        name = _path(raw_name, directory=directory)
        if name in names or directory and payload:
            raise ScopeDenied()
        names.add(name)
        total += len(payload)
        if total > MAX_BYTES:
            raise ScopeDenied()
        if not directory:
            files.add(name)
            _check_secrets(payload, budget=scan_budget)
        rows.append((name, directory, payload))
    for name in names:
        if any(str(parent) in files for parent in PurePosixPath(name).parents
               if str(parent) != '.'):
            raise ScopeDenied()
    guard()
    return rows, guard


def _cab_rows(cap, data):
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_cab_codec as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise _CodecFailure('archive_original_deadline_required')
    guard = lambda: _codec_guard(cap, call, deadline)
    guard()
    try:
        decoded = codec.read_cab_bytes(data, checkpoint=guard)
    except codec.CABCodecError as exc:
        raise _CodecFailure(str(exc)) from None
    rows = []; scan_budget = [MAX_SECRET_SCAN]
    for raw_name, payload in decoded:
        guard()
        name = _path(raw_name)
        _check_secrets(payload, budget=scan_budget)
        rows.append((name, False, payload))
    guard()
    return rows, guard


def _lha_rows(cap, data):
    """Consume the isolated LHA reader under this original native call's clock."""
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_lha_codec as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if (type(deadline) not in (int, float) or not math.isfinite(deadline)
            or deadline - time.monotonic() <= codec.WALL_SECONDS + 2):
        raise _CodecFailure('archive_codec_budget_insufficient')
    guard = lambda: _codec_guard(cap, call, deadline)
    guard()
    try:
        decoded = codec.read_lha_bytes(data, checkpoint=guard)
    except codec.LHACodecError as exc:
        code = str(exc)
        raise _CodecFailure('archive_codec_cleanup_unconfirmed' if
            code == 'lha_cleanup_unconfirmed' else 'archive_codec_unavailable' if
            code == 'lha_codec_unavailable' else 'archive_codec_refused',
            unknown=code == 'lha_cleanup_unconfirmed') from None
    if type(decoded) is not list or not 1 <= len(decoded) <= MAX_ENTRIES:
        raise ScopeDenied()
    rows = []; names = set(); files = set(); total = 0
    scan_budget = [MAX_SECRET_SCAN]
    for row in decoded:
        guard()
        if (type(row) is not tuple or len(row) != 2
                or not isinstance(row[0], str) or type(row[1]) is not bytes):
            raise ScopeDenied()
        raw_name, payload = row
        directory = raw_name.endswith('/')
        name = _path(raw_name, directory=directory)
        if name in names or directory and payload:
            raise ScopeDenied()
        names.add(name)
        total += len(payload)
        if total > MAX_BYTES:
            raise ScopeDenied()
        if not directory:
            files.add(name)
            _check_secrets(payload, budget=scan_budget)
        rows.append((name, directory, payload))
    for name in names:
        if any(str(parent) in files for parent in PurePosixPath(name).parents
               if str(parent) != '.'):
            raise ScopeDenied()
    guard()
    return rows, guard


def _arj_rows(cap, data):
    from agent.web_call_context import _current
    from hermes_cli import friday_workspace_arj_codec as codec
    check(cap)
    call = _current.get()
    if call is None or not callable(getattr(call, 'deadline', None)):
        raise _CodecFailure('archive_original_deadline_required')
    deadline = call.deadline()
    if (type(deadline) not in (int, float) or not math.isfinite(deadline) or
            deadline - time.monotonic() <= codec.WALL_SECONDS + 2):
        raise _CodecFailure('archive_codec_budget_insufficient')
    guard = lambda: _codec_guard(cap, call, deadline)
    try:
        decoded = codec.read_arj_bytes(data, checkpoint=guard)
    except codec.ARJCodecError as exc:
        raise _CodecFailure(str(exc)) from None
    rows = []; scan_budget = [MAX_SECRET_SCAN]
    for raw_name, directory, payload in decoded:
        guard()
        name = _path(raw_name, directory=directory)
        if not directory:
            _check_secrets(payload, budget=scan_budget)
        rows.append((name, directory, payload))
    guard()
    return rows, guard


def _encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _inline_budget():
    from agent.bounded_context import bounded_tool_result_budget
    budget = bounded_tool_result_budget()
    return 100000 if budget is None else budget


def _fits(value, budget):
    # The tool result is itself a JSON string inside the provider payload.
    from agent.bounded_context import serialized_bytes
    return serialized_bytes(_encode(value)) <= budget


def _capacity(budget, *, total=None, offset=None):
    result = dict(success=False, error='capacity: archive result exceeds inline budget',
                  effect_disposition='none')
    if total is not None:
        result.update(total_entries=total, partial=offset <= total, next_offset=offset)
    if not _fits(result, budget):
        result = dict(success=False, error='capacity')
        if total is not None:
            result.update(total_entries=total, partial=offset <= total, next_offset=offset)
        else:
            result['effect_disposition'] = 'none'
    # No archive effect has started. A budget too small even for this native
    # failure envelope cannot be repaired by discarding a successful effect.
    return _encode(result)


def _omitted_receipt(result, rows, archive_path):
    return dict(result, member_count=len(rows), registry_omitted=True,
                registry_read_file=archive_path, next_offset=1)


def _effect_receipt(result, rows, archive_path, budget, *, prefix=''):
    if not result.get('success') and not result.get('published_partial'):
        return _encode(result)
    full = dict(result, member_count=len(rows), registry_omitted=False,
                archive_members=_manifest(rows, prefix))
    if _fits(full, budget):
        return _encode(full)
    # This exact compact success envelope was capacity-checked BEFORE the
    # publication. Never report failure or repeat creation to recover a list.
    return _encode(_omitted_receipt(result, rows, archive_path))


def read_archive(cap, relative, *, offset=1, limit=2000, char_offset=0, password=None, parts=None):
    if (type(offset) is not int or type(limit) is not int or type(char_offset) is not int
            or not 1 <= offset <= 1000000 or not 1 <= limit <= 2000 or char_offset != 0):
        raise ScopeDenied()
    budget = _inline_budget()
    from hermes_cli.friday_workspace_7z_parts import Split7zRefused
    try:
        data, sources, part_manifest = _archive_source(cap, relative, parts)
    except Split7zRefused as exc:
        return _codec_failure(_CodecFailure(str(exc)))
    source_format = archive_format(relative)
    password = _archive_password(password)
    if password is not None and source_format not in ('7z', 'zip'):
        raise ScopeDenied()
    _password_path(password, relative, *(row['path'] for row in (part_manifest or [])))
    guard = lambda: check(cap)
    damaged = []
    if source_format == '7z':
        try:
            rows, guard = _seven_rows(cap, data, password=password)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'rar':
        try:
            rows, guard = _rar_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'arj':
        try:
            rows, guard = _arj_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'cab':
        try:
            rows, guard = _cab_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'lha':
        try:
            rows, guard = _lha_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'zip':
        try:
            if _zip_encrypted(data):
                rows, guard = _zip_rows(cap, data, password=password)
            else:
                rows, damaged = _rows(data, allow_partial=True)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format in TAR_FORMATS:
        rows = _tar_rows(data, source_format)
    elif source_format in STREAM_FORMATS:
        rows = _stream_rows(data, relative)
    else:
        raise ScopeDenied()
    _verify(cap, sources)
    guard()
    start = min(offset, len(rows) + 1)
    result = dict(success=True, format=source_format, path=relative,
        scope='own_user_workspace', archive_members=[], extracted=False,
        sha256=hashlib.sha256(data).hexdigest(), total_entries=len(rows),
        partial=start <= len(rows), next_offset=start)
    if damaged:
        result.update(success=False, error='archive_member_data_invalid',
                      archive_complete=False, damaged_members=damaged,
                      recovery='Only verified healthy members may be extracted with explicit zip_extract allow_partial=true; output remains incomplete.')
    if part_manifest is not None:
        result.update(split_7z=True, source_parts=part_manifest)
    if source_format in STREAM_FORMATS:
        result.update(compressed_stream=True, member_name_origin='compressed_filename')
    if not _fits(result, budget):
        return _capacity(budget, total=len(rows), offset=start)
    for index in range(start - 1, min(len(rows), start - 1 + limit)):
        entry = _manifest([rows[index]])[0]
        candidate = dict(result, archive_members=result['archive_members'] + [entry],
                         partial=index + 1 < len(rows), next_offset=index + 2)
        if not _fits(candidate, budget):
            if not result['archive_members']:
                return _capacity(budget, total=len(rows), offset=start)
            break
        result = candidate
    guard()
    return _encode(result)


def create_zip(cap, fd, leaf, relative, content):
    _check_parent(cap, fd, relative)
    budget = _inline_budget()
    spec = _archive_spec(content, ('entries',), ('password',))
    password = _archive_password(spec.get('password'))
    _password_path(password, relative)
    entries = spec['entries']
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ENTRIES:
        raise ScopeDenied()
    sources = []; names = set(); rows = []; total = 0
    scan_budget = [MAX_SECRET_SCAN]
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'source', 'member'}:
            raise ScopeDenied()
        source = _path(entry['source']); member = _path(entry['member'])
        _password_path(password, source, member)
        if member in names:
            raise ScopeDenied()
        names.add(member)
        data, identity = _source(cap, source)
        _check_secrets(data, budget=scan_budget)
        total += len(data)
        if total > MAX_BYTES:
            raise ScopeDenied()
        sources.append((source, data, identity)); rows.append((member, False, data))
    for name in names:
        if any(str(parent) in names for parent in PurePosixPath(name).parents if str(parent) != '.'):
            raise ScopeDenied()
    if password is not None:
        return _publish_archive(cap, fd, leaf, relative, rows, sources, 'zip', budget,
                                password=password)
    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED, allowZip64=False) as archive:
        for member, _, data in rows:
            check(cap)
            info = ZipInfo(member)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3; info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, data)
    data = output.getvalue()
    receipt = dict(success=True, format='zip', path=relative,
        scope='own_user_workspace', create_only=True, verified=True,
        bytes_written=len(data), sha256=hashlib.sha256(data).hexdigest())
    if not _fits(_omitted_receipt(receipt, rows, relative), budget):
        return _capacity(budget)
    result = json.loads(_create_bytes(cap, fd, leaf, relative, data,
        output_format='zip', verify_source=lambda: _verify(cap, sources)))
    return _effect_receipt(result, rows, relative, budget)


def _new_zip(cap, rows):
    # Existing ZIP admission requires at least one member and a compression ratio
    # <=200. Use stored members for this new conversion route so even highly
    # compressible genuine 7z payloads remain readable by that same ZIP consumer.
    if not rows:
        raise _CodecFailure('archive_empty_conversion_unsupported')
    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_STORED, allowZip64=False) as archive:
        for member, directory, payload in rows:
            check(cap)
            info = ZipInfo(member + '/' if directory else member)
            info.compress_type = ZIP_STORED
            info.create_system = 3
            info.external_attr = ((stat.S_IFDIR | 0o700) if directory else
                                  (stat.S_IFREG | 0o600)) << 16
            if directory:
                info.external_attr |= 0x10
            archive.writestr(info, payload)
    data = output.getvalue()
    if len(data) > MAX_BYTES:
        raise ScopeDenied()
    return data


def _publish_archive(cap, fd, leaf, relative, rows, sources, output_format, budget,
                     *, guard=lambda: None, password=None, header_encryption=False):
    if output_format == '7z':
        _password_path(password, relative, *(name for name, _, _ in rows))
        # File-only S494 API cannot represent any explicit directory record.
        # Refuse before encoding instead of silently losing an empty directory.
        if any(directory for _, directory, _ in rows):
            return _codec_failure(_CodecFailure('archive_directory_encode_unsupported'))
        try:
            data, guard = _codec(cap, 'encode', [(name, payload) for name, _, payload in rows],
                                 password=password, header_encryption=header_encryption)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif output_format in TAR_FORMATS:
        data = _new_tar(cap, rows, output_format)
    else:
        if output_format != 'zip':
            raise ScopeDenied()
        try:
            if password is None:
                data = _new_zip(cap, rows)
            else:
                _password_path(password, relative, *(name for name, _, _ in rows))
                if any(directory for _, directory, _ in rows):
                    return _codec_failure(_CodecFailure('archive_directory_encode_unsupported'))
                data, guard = _zip_crypto(cap, 'encode',
                    [(name, payload) for name, _, payload in rows], password)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    receipt = dict(success=True, format=output_format, path=relative,
        scope='own_user_workspace', create_only=True, verified=True,
        bytes_written=len(data), sha256=hashlib.sha256(data).hexdigest())
    if output_format == 'zip' and password is not None:
        receipt.update(encryption='WinZip AES-256 AE-2', member_names_encrypted=False)
    if not _fits(_omitted_receipt(receipt, rows, relative), budget):
        return _capacity(budget)
    def verify():
        guard()
        _verify(cap, sources)
        guard()
    verify()
    result = json.loads(_create_bytes(cap, fd, leaf, relative, data,
        output_format=output_format, verify_source=verify))
    if result.get('success') and output_format == 'zip' and password is not None:
        result.update(encryption='WinZip AES-256 AE-2', member_names_encrypted=False)
    return _effect_receipt(result, rows, relative, budget)


def create_7z(cap, fd, leaf, relative, content):
    _check_parent(cap, fd, relative)
    budget = _inline_budget()
    spec = _archive_spec(content, ('entries',), ('password', 'header_encryption'))
    password = _archive_password(spec.get('password'))
    header_encryption = spec.get('header_encryption', False)
    if type(header_encryption) is not bool or (header_encryption and password is None):
        raise ScopeDenied()
    entries = spec['entries']
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ENTRIES:
        raise ScopeDenied()
    sources = []; rows = []; names = set(); total = 0
    scan_budget = [MAX_SECRET_SCAN]
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'source', 'member'}:
            raise ScopeDenied()
        source = _path(entry['source']); member = _path(entry['member'])
        if member in names:
            raise ScopeDenied()
        names.add(member)
        data, identity = _source(cap, source)
        _check_secrets(data, budget=scan_budget)
        total += len(data)
        if total > MAX_BYTES:
            raise ScopeDenied()
        sources.append((source, data, identity)); rows.append((member, False, data))
    for name in names:
        if any(str(parent) in names for parent in PurePosixPath(name).parents if str(parent) != '.'):
            raise ScopeDenied()
    return _publish_archive(cap, fd, leaf, relative, rows, sources, '7z', budget,
                            password=password, header_encryption=header_encryption)


def create_tar(cap, fd, leaf, relative, content, *, format):
    _check_parent(cap, fd, relative)
    if format not in TAR_FORMATS or archive_format(relative) != format:
        raise ScopeDenied()
    entries = _object(content, 'entries')
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ENTRIES:
        raise ScopeDenied()
    rows = []; sources = []; names = set(); total = 0
    scan_budget = [MAX_SECRET_SCAN]
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'source', 'member'}:
            raise ScopeDenied()
        source = _path(entry['source']); member = _path(entry['member'])
        if member in names:
            raise ScopeDenied()
        names.add(member)
        data, identity = _source(cap, source)
        _check_secrets(data, budget=scan_budget)
        total += len(data)
        if total > MAX_BYTES:
            raise ScopeDenied()
        sources.append((source, data, identity)); rows.append((member, False, data))
    for name in names:
        if any(str(parent) in names for parent in PurePosixPath(name).parents if str(parent) != '.'):
            raise ScopeDenied()
    return _publish_archive(cap, fd, leaf, relative, rows, sources, format, _inline_budget())


def create_stream(cap, fd, leaf, relative, content, *, format):
    from tools.scoped_single_stream import encode_stream, StreamError
    _check_parent(cap, fd, relative)
    if format not in STREAM_FORMATS or archive_format(relative) != format:
        raise ScopeDenied()
    source = _path(_object(content, 'source'))
    payload, identity = _source(cap, source)
    _check_secrets(payload)
    check(cap)
    try:
        data = encode_stream(payload, format)
    except StreamError:
        raise ScopeDenied() from None
    check(cap)
    member = _path(PurePosixPath(relative).name.rsplit('.', 1)[0])
    rows = [(member, False, payload)]
    budget = _inline_budget()
    receipt = dict(success=True, format=format, path=relative,
        scope='own_user_workspace', create_only=True, verified=True,
        bytes_written=len(data), sha256=hashlib.sha256(data).hexdigest(),
        compressed_stream=True, member_name_origin='compressed_filename')
    if not _fits(_omitted_receipt(receipt, rows, relative), budget):
        return _capacity(budget)
    sources = [(source, payload, identity)]
    _verify(cap, sources)
    result = json.loads(_create_bytes(cap, fd, leaf, relative, data,
        output_format=format, verify_source=lambda: _verify(cap, sources)))
    result.update(compressed_stream=True, member_name_origin='compressed_filename')
    return _effect_receipt(result, rows, relative, budget)


def convert_archive(cap, fd, leaf, relative, content):
    _check_parent(cap, fd, relative)
    budget = _inline_budget()
    source = _path(_object(content, 'source'))
    from hermes_cli.friday_workspace_7z_parts import is_split_path
    if is_split_path(source) or is_split_path(relative):
        raise ScopeDenied()
    source_format = archive_format(source)
    output_format = archive_format(relative)
    allowed = TAR_FORMATS | {'zip', '7z'}
    if (source_format not in allowed | {'rar'} or output_format not in allowed
            or source_format == output_format
            or source_format == 'rar' and output_format == '7z'):
        raise ScopeDenied()
    data, identity = _source(cap, source)
    guard = lambda: check(cap)
    if source_format == '7z':
        try:
            rows, guard = _seven_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif source_format == 'rar':
        try:
            rows, guard = _rar_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    else:
        rows = _rows(data) if source_format == 'zip' else _tar_rows(data, source_format)
        scan_budget = [MAX_SECRET_SCAN]
        for _, directory, payload in rows:
            check(cap)
            if not directory:
                _check_secrets(payload, budget=scan_budget)
    return _publish_archive(cap, fd, leaf, relative, rows, [(source, data, identity)],
                            output_format, budget, guard=guard)


def edit_archive(cap, fd, leaf, relative, content):
    """Replace/add/delete explicit ZIP/TAR members in a new same-profile copy."""
    _check_parent(cap, fd, relative)
    if type(content) is not str or len(content.encode('utf-8')) > 100000:
        raise ScopeDenied()
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ScopeDenied()
            value[key] = item
        return value
    try:
        spec = json.loads(content, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        raise ScopeDenied() from None
    if type(spec) is not dict or set(spec) != {'source', 'remove', 'entries'}:
        raise ScopeDenied()
    source = _path(spec['source'])
    format = archive_format(source)
    if format not in TAR_FORMATS | {'zip'} or archive_format(relative) != format or source == relative:
        raise ScopeDenied()
    removals, entries = spec['remove'], spec['entries']
    if (type(removals) is not list or type(entries) is not list
            or not 1 <= len(removals) + len(entries) <= MAX_ENTRIES):
        raise ScopeDenied()
    remove = [_path(name) for name in removals]
    if len(set(remove)) != len(remove):
        raise ScopeDenied()
    data, identity = _source(cap, source)
    old = _rows(data) if format == 'zip' else _tar_rows(data, format)
    original = {name: (directory, payload) for name, directory, payload in old}
    if any(name not in original for name in remove):
        raise ScopeDenied()
    changes = {}
    sources = [(source, data, identity)]
    for entry in entries:
        if type(entry) is not dict or set(entry) != {'source', 'member'}:
            raise ScopeDenied()
        item = _path(entry['source'])
        member = _path(entry['member'])
        if member in changes or member in remove or original.get(member, (False,))[0]:
            raise ScopeDenied()
        payload, item_identity = _source(cap, item)
        changes[member] = (False, payload)
        sources.append((item, payload, item_identity))
    # Replacements retain their original order; new members follow request order.
    rows = [(name, *changes.get(name, (directory, payload)))
            for name, directory, payload in old if name not in remove]
    rows.extend((name, *row) for name, row in changes.items() if name not in original)
    if not 1 <= len(rows) <= MAX_ENTRIES or sum(len(payload) for _, _, payload in rows) > MAX_BYTES:
        raise ScopeDenied()
    names = {name for name, _, _ in rows}
    files = {name for name, directory, _ in rows if not directory}
    if len(names) != len(rows) or any(str(parent) in files for name in names
            for parent in PurePosixPath(name).parents if str(parent) != '.'):
        raise ScopeDenied()
    scan_budget = [MAX_SECRET_SCAN]
    for _, directory, payload in rows:
        check(cap)
        if not directory:
            _check_secrets(payload, budget=scan_budget)
    return _publish_archive(cap, fd, leaf, relative, rows, sources, format, _inline_budget())


def _tree_snapshot(fd, rows):
    """Reject changed bytes, links, permissions and unexpected private-stage files."""
    expected = {}
    for name, directory, data in rows:
        parts = name.split('/')
        for index in range(1, len(parts)):
            expected['/'.join(parts[:index])] = None
        expected[name] = None if directory else data
    seen = {}
    def walk(parent, prefix=''):
        for leaf in os.listdir(parent):
            name = prefix + leaf
            info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            if name not in expected or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ScopeDenied()
            if stat.S_ISDIR(info.st_mode) and expected[name] is None:
                child = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                try:
                    if os.fstat(child).st_ino != info.st_ino or os.fstat(child).st_dev != info.st_dev:
                        raise ScopeDenied()
                    seen[name] = None; walk(child, name + '/')
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode) and expected[name] is not None and info.st_nlink == 1:
                item = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                try:
                    before = os.fstat(item)
                    if (before.st_dev, before.st_ino) != (info.st_dev, info.st_ino):
                        raise ScopeDenied()
                    with os.fdopen(os.dup(item), 'rb') as stream:
                        data = stream.read(MAX_BYTES + 1)
                    after = os.fstat(item)
                    named = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
                    fields = ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_uid','st_nlink')
                    if (data != expected[name] or any(getattr(before, key) != getattr(after, key)
                            or getattr(after, key) != getattr(named, key) for key in fields)):
                        raise ScopeDenied()
                    seen[name] = data
                finally:
                    os.close(item)
            else:
                raise ScopeDenied()
        os.fsync(parent)
    walk(fd)
    if seen != expected:
        raise ScopeDenied()


def _remove_private_tree(fd):
    # fd belongs only to our random staging tree; never follows an entry link.
    for leaf in os.listdir(fd):
        info = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                _remove_private_tree(child)
            finally:
                os.close(child)
            os.rmdir(leaf, dir_fd=fd)
        else:
            os.unlink(leaf, dir_fd=fd)


def extract_zip(cap, fd, leaf, relative, content, *, _format='zip'):
    _check_parent(cap, fd, relative)
    budget = _inline_budget()
    if _format in ('7z', 'zip'):
        spec = _archive_spec(content, ('source',), ('password', 'parts') if _format == '7z' else ('password', 'allow_partial'))
        source = _path(spec['source'])
        password = _archive_password(spec.get('password'))
        _password_path(password, source, relative)
    else:
        source = _path(_object(content, 'source'))
        password = None
    from hermes_cli.friday_workspace_7z_parts import Split7zRefused
    try:
        data, sources, part_manifest = _archive_source(
            cap, source, spec.get('parts') if _format == '7z' else None)
    except Split7zRefused as exc:
        return _codec_failure(_CodecFailure(str(exc)))
    _password_path(password, *(row['path'] for row in (part_manifest or [])))
    guard = lambda: check(cap)
    damaged = []
    allow_partial = spec.get('allow_partial', False) if _format == 'zip' else False
    if type(allow_partial) is not bool:
        raise ScopeDenied()
    if _format == '7z':
        if archive_format(source) != '7z':
            raise ScopeDenied()
        try:
            rows, guard = _seven_rows(cap, data, password=password)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'rar':
        if archive_format(source) != 'rar':
            raise ScopeDenied()
        try:
            rows, guard = _rar_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'arj':
        if archive_format(source) != 'arj':
            raise ScopeDenied()
        try:
            rows, guard = _arj_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'cab':
        if archive_format(source) != 'cab':
            raise ScopeDenied()
        try:
            rows, guard = _cab_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'lha':
        if archive_format(source) != 'lha':
            raise ScopeDenied()
        try:
            rows, guard = _lha_rows(cap, data)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'zip':
        try:
            if allow_partial:
                # Encryption/authentication and malformed structure are never
                # downgraded to partial success, even for explicit recovery.
                if _zip_encrypted(data) or password is not None:
                    raise ScopeDenied()
                rows, damaged = _rows(data, allow_partial=True)
            else:
                rows, guard = _zip_rows(cap, data, password=password)
        except _CodecFailure as failure:
            return _codec_failure(failure)
    elif _format == 'tar':
        source_format = archive_format(source)
        if source_format not in TAR_FORMATS:
            raise ScopeDenied()
        rows = _tar_rows(data, source_format)
    elif _format == 'stream':
        rows = _stream_rows(data, source)
    else:
        raise ScopeDenied()
    def verify():
        guard()
        _verify(cap, sources)
        guard()
    receipt = dict(success=True, format=_format + '_extract', path=relative,
        scope='own_user_workspace', create_only=True, verified=True,
        source_sha256=hashlib.sha256(data).hexdigest())
    if damaged:
        if not any(not directory for _, directory, _ in rows):
            verify()
            return _encode(dict(success=False, error='archive_no_recoverable_members',
                                effect_disposition='none', archive_complete=False,
                                damaged_members=damaged))
        receipt.update(success=False, error='archive_partially_extracted',
                       archive_complete=False, published_partial=True,
                       effect_disposition='known_partial', damaged_members=damaged)
    if part_manifest is not None:
        receipt.update(split_7z=True, source_parts=part_manifest)
    if not _fits(_omitted_receipt(receipt, rows, source), budget):
        return _capacity(budget)
    try:
        os.stat(leaf, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        return json.dumps(dict(success=False, error='archive_destination_exists', path=relative))
    stage = '.friday-zip-' + uuid.uuid4().hex
    tree = None; published = False; uncertain = False; cleanup_failed = False
    try:
        os.mkdir(stage, 0o700, dir_fd=fd)
        tree = os.open(stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        for name, directory, payload in rows:
            check(cap); current = os.dup(tree)
            try:
                parts = name.split('/')
                for part in (parts if directory else parts[:-1]):
                    try:
                        os.mkdir(part, 0o700, dir_fd=current)
                    except FileExistsError:
                        pass
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                    os.close(current); current = child
                if not directory:
                    item = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                   0o600, dir_fd=current)
                    with os.fdopen(item, 'wb') as stream:
                        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
                os.fsync(current)
            finally:
                os.close(current)
        _tree_snapshot(tree, rows); os.fsync(tree); verify(); _check_parent(cap, fd, relative)
        uncertain = True
        _move(fd, stage, fd, leaf)
        published = True; uncertain = False
        os.fsync(fd); _check_parent(cap, fd, relative)
        named = os.stat(leaf, dir_fd=fd, follow_symlinks=False); held = os.fstat(tree)
        if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino):
            raise ScopeDenied()
        _tree_snapshot(tree, rows); verify(); check(cap)
        result = receipt
    except (OSError, ScopeDenied, RuntimeError, TimeoutError):
        if uncertain and tree is not None:
            try:
                named = os.stat(stage, dir_fd=fd, follow_symlinks=False); held = os.fstat(tree)
                if (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino):
                    uncertain = False
            except OSError:
                pass
        unknown = published or uncertain
        result = dict(success=False, error='archive_publication_uncertain' if unknown else 'archive_not_extracted',
                      effect_disposition='unknown' if unknown else 'none')
    finally:
        if tree is not None:
            try:
                named = os.stat(stage, dir_fd=fd, follow_symlinks=False); held = os.fstat(tree)
                if (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino):
                    _remove_private_tree(tree); os.rmdir(stage, dir_fd=fd); os.fsync(fd)
            except FileNotFoundError:
                pass
            except (OSError, ScopeDenied):
                cleanup_failed = True
            finally:
                os.close(tree)
    if cleanup_failed:
        result = dict(success=False, error='archive_cleanup_incomplete', effect_disposition='unknown')
    if result.get('effect_disposition') == 'unknown':
        from agent.web_call_context import _current
        call = _current.get()
        if call is not None and hasattr(call, 'agent'):
            call.agent._friday_reply_effect_unknown = True
    return _effect_receipt(result, rows, source, budget, prefix=relative + '/')
