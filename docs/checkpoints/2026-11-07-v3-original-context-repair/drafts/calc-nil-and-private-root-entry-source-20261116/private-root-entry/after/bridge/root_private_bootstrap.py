"""Root-owned SOURCE loader, not admission and not a public actor CLI.

Call only under the existing explicit owner delegation to the trusted Root
runner. This configures a fresh normal native module search path; the entry
itself stamps the one clock before mutable/current checks and any native
imports. Namespace setup grants no scope, principal or operation permission.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import os
import stat
import sys
import time
from types import ModuleType

HERE = Path(__file__).resolve().parent
RUNTIME = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')


def _verified_bytes(path, expected, *, mode, limit):
    if path.resolve() != path or not path.is_absolute():
        raise RuntimeError('root_source_exact_path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or before.st_nlink != 1 or stat.S_IMODE(before.st_mode) not in mode
                or not 0 < before.st_size <= limit):
            raise RuntimeError('root_source_rights')
        raw = bytearray()
        while part := os.read(fd, min(65536, limit + 1 - len(raw))):
            raw.extend(part)
            if len(raw) > limit:
                raise RuntimeError('root_source_limit')
        def stamp(info):
            return tuple(getattr(info, k) for k in ('st_dev','st_ino','st_uid',
                'st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
        if (stamp(before) != stamp(os.fstat(fd)) or stamp(before) != stamp(path.lstat())
                or len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != expected):
            raise RuntimeError('root_source_CAS')
        return bytes(raw)
    finally:
        os.close(fd)


def run_fixed_root_qualification(prepared_path, prepared_sha256):
    entered = time.monotonic()  # same one clock also covers code loading/CAS
    if not sys.dont_write_bytecode:
        raise RuntimeError('root_private_source_requires_python_B')
    config = json.loads(_verified_bytes(Path(prepared_path), prepared_sha256,
        mode=(0o400, 0o600), limit=262144))
    manifest_path = Path(config['manifest_path'])
    if manifest_path != HERE / 'ROOT-BRIDGE-PINS.json' or config['closure_root'] != str(HERE):
        raise RuntimeError('root_fixed_source_config')
    manifest = json.loads(_verified_bytes(manifest_path, config['manifest_sha256'],
        mode=(0o400, 0o600), limit=262144))
    # This only constructs import namespaces from immutable reviewed SOURCE.
    # Refuse hot module replacement in an existing user/model runtime.
    if any(name == root or name.startswith(root + '.')
           for name in sys.modules for root in ('hermes_cli', 'agent', 'tools')):
        raise RuntimeError('root_qualification_fresh_native_runtime_required')
    native = HERE.parent / 'native'
    sys.path.insert(0, str(RUNTIME))
    sys.path.insert(0, str(HERE))
    for name, paths in (
        ('hermes_cli', [HERE / 'hermes_cli', native / 'hermes_cli', RUNTIME / 'hermes_cli']),
        ('agent', [HERE / 'agent', RUNTIME / 'agent']),
        ('tools', [HERE / 'tools', native / 'tools', RUNTIME / 'tools'])):
        package = ModuleType(name)
        package.__path__ = [str(path) for path in paths]
        sys.modules[name] = package
    path = HERE / 'frw_root_qualification_entry.py'
    expected = next(row['sha256'] for row in manifest['files'] if row['path'] == str(path))
    raw = _verified_bytes(path, expected, mode=(0o400,), limit=262144)
    spec = importlib.util.spec_from_file_location('frw_root_qualification_entry', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['frw_root_qualification_entry'] = module
    # The bootstrap/entry are immutable reviewed Root code. Actual byte/CAS and
    # every mutable/code/current action inside run are charged to its one T0.
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module.run_root_first_qualification(prepared_path, prepared_sha256,
                                              _original_entered=entered)

