"""SOURCE: ordinary measured renderer's protected files and launch boundary.

No Office process is launched here. A complete native constructor/supervisor is
still required; this module supplies no synthetic runtime facts or admission.
The parent must execute the resulting argv exactly once through existing _run.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import stat

WORK = '/tmp/friday-metric-work'
PREFIX = '/opt/friday-document-toolchain'
MAX_ASSET = 4 * 1024 * 1024
MAX_ASSETS = 64
MAX_ASSET_BYTES = 16 * 1024 * 1024


class LayoutRefused(RuntimeError):
    pass


def need(value, reason):
    if not value:
        raise LayoutRefused(reason)


def exact_path(value):
    p = Path(value)
    need(p.is_absolute() and '..' not in p.parts and str(p) == str(value),
         'native_layout_canonical_absolute_path')
    need(p.resolve() == p, 'native_layout_path_alias')
    return p


def private_directory(value):
    p = exact_path(value)
    s = p.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid()
         and stat.S_IMODE(s.st_mode) == 0o700, 'native_layout_private_directory')
    return p


def managed_toolchain_directory(value):
    """Same ownership/readonly mode domain as existing _toolchain()."""
    p = exact_path(value)
    s = p.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid()
         and s.st_mode & 0o277 == 0, 'native_layout_managed_toolchain')
    return p


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode,
            s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def read_exact_file(value, expected_sha256, *, limit=MAX_ASSET):
    """Read a named immutable asset; hash correlation is not runtime authority."""
    p = exact_path(value)
    need(type(expected_sha256) is str and len(expected_sha256) == 64
         and all(c in '0123456789abcdef' for c in expected_sha256),
         'native_layout_digest_shape')
    before = p.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
         and before.st_nlink == 1 and before.st_mode & 0o022 == 0
         and 0 <= before.st_size <= limit, 'native_layout_source_file')
    fd = os.open(p, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NOATIME)
    try:
        need(stamp(os.fstat(fd)) == stamp(before), 'native_layout_open_race')
        parts = []
        size = 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            parts.append(chunk)
            size += len(chunk)
            need(size <= limit, 'native_layout_source_size')
        raw = b''.join(parts)
        need(stamp(os.fstat(fd)) == stamp(before) == stamp(p.lstat()),
             'native_layout_read_race')
    finally:
        os.close(fd)
    need(hashlib.sha256(raw).hexdigest() == expected_sha256,
         'native_layout_source_hash')
    return raw


def safe_relative(value):
    need(type(value) is str and value and len(value) <= 256 and '\\' not in value,
         'native_layout_relative_name')
    p = Path(value)
    need(not p.is_absolute() and '..' not in p.parts and str(p) == value
         and len(p.parts) <= 8 and all(part not in ('', '.') for part in p.parts),
         'native_layout_relative_name')
    return p


@dataclass(frozen=True)
class StagedCode:
    directory: Path
    entry: str
    files: tuple
    source_index_sha256: str


def exact_generation_tree(staged):
    """The whole mounted directory must contain exactly the indexed code."""
    root = private_directory(staged.directory)
    expected_files = {str(safe_relative(row[0])) for row in staged.files}
    expected_dirs = set()
    for relative in expected_files:
        parts = Path(relative).parts
        expected_dirs.update(str(Path(*parts[:i])) for i in range(1, len(parts)))
    actual_files, actual_dirs = set(), set()
    directory_stamps = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        before = directory.lstat()
        directory_stamps[directory] = stamp(before)
        with os.scandir(directory) as entries:
            for item in entries:
                info = item.stat(follow_symlinks=False)
                path = directory / item.name
                relative = str(path.relative_to(root))
                if stat.S_ISDIR(info.st_mode):
                    need(relative in expected_dirs, 'native_layout_unindexed_directory')
                    private_directory(path)
                    actual_dirs.add(relative)
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    need(relative in expected_files, 'native_layout_unindexed_file')
                    actual_files.add(relative)
                else:
                    raise LayoutRefused('native_layout_generation_type')
        need(stamp(directory.lstat()) == stamp(before), 'native_layout_generation_race')
    need(actual_files == expected_files and actual_dirs == expected_dirs,
         'native_layout_generation_members')
    for path, before in directory_stamps.items():
        need(stamp(path.lstat()) == before, 'native_layout_generation_race')


def stage_code(work, trusted_index, expected_index_sha256):
    """Copy a code generation pinned by the installed factory, never user JSON.

    The caller's code must bind expected_index_sha256 to its reviewed installed
    source generation. A supplied index and matching digest alone grant nothing.
    This routine cannot manufacture that provenance or mark a backend ready.
    """
    work = private_directory(work)
    index_path = exact_path(trusted_index)
    raw = read_exact_file(index_path, expected_index_sha256, limit=262144)
    index = json.loads(raw)
    need(type(index) is dict and set(index) == {'schema', 'entry', 'files'}
         and index['schema'] == 'frw.calc.native-code-generation.v1',
         'native_layout_index_schema')
    entry = safe_relative(index['entry'])
    files = index['files']
    need(type(files) is list and 0 < len(files) <= MAX_ASSETS,
         'native_layout_index_count')
    seen = set()
    prepared = []
    total = 0
    for item in files:
        need(type(item) is dict and set(item) == {'relative', 'sha256'},
             'native_layout_member_schema')
        rel = safe_relative(item['relative'])
        need(str(rel) not in seen, 'native_layout_duplicate_member')
        seen.add(str(rel))
        data = read_exact_file(index_path.parent / rel, item['sha256'])
        total += len(data)
        need(total <= MAX_ASSET_BYTES, 'native_layout_total_bytes')
        prepared.append((rel, data, item['sha256']))
    need(str(entry) in seen, 'native_layout_missing_entry')
    target = work / 'code'
    target.mkdir(mode=0o700)  # Exclusive: never merge two generations.
    created = []
    try:
        for rel, data, expected in prepared:
            dst = target / rel
            parent = target
            for part in rel.parts[:-1]:
                parent = parent / part
                if not parent.exists():
                    parent.mkdir(mode=0o700)
                private_directory(parent)
            fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            with os.fdopen(fd, 'wb') as out:
                out.write(data)
            created.append((str(rel), expected, len(data)))
            need(read_exact_file(dst, expected) == data, 'native_layout_stage_mismatch')
    except BaseException:
        # No child exists at preparation time. Remove this routine's new files
        # and directories only; the parent's original input/output remain owned.
        for path in sorted(target.rglob('*'), key=lambda x: len(x.parts), reverse=True):
            if path.is_file() and not path.is_symlink():
                path.unlink()
            elif path.is_dir() and not path.is_symlink():
                path.rmdir()
        target.rmdir()
        raise
    return StagedCode(target, str(entry), tuple(created), expected_index_sha256)


def namespace_argv(work, toolchain, staged, *, source_sha256, source_bytes):
    """Build a single ordinary namespace, no separate systemd/Root operation."""
    work = private_directory(work)
    toolchain = managed_toolchain_directory(toolchain)
    need(not toolchain.is_relative_to(work) and not work.is_relative_to(toolchain),
         'native_layout_toolchain_work_overlap')
    need(type(staged) is StagedCode and staged.directory == work / 'code',
         'native_layout_staged_generation')
    entry = safe_relative(staged.entry)
    need(type(staged.files) is tuple and 0 < len(staged.files) <= MAX_ASSETS
         and len({x[0] for x in staged.files}) == len(staged.files)
         and str(entry) in {x[0] for x in staged.files},
         'native_layout_staged_entry')
    source = work / 'input.ods'
    raw = read_exact_file(source, source_sha256, limit=1000000)
    need(type(source_bytes) is int and len(raw) == source_bytes,
         'native_layout_original_source')
    need((toolchain / 'share-merged').is_dir()
         and (toolchain / 'root/usr/lib/libreoffice/program/soffice.bin').is_file(),
         'native_layout_toolchain')
    private_directory(work / 'out')
    private_directory(work / 'home')
    private_directory(work / 'tmp')
    private_directory(staged.directory)
    exact_generation_tree(staged)
    for relative, expected, length in staged.files:
        relative = safe_relative(relative)
        need(type(length) is int and 0 <= length <= MAX_ASSET
             and len(read_exact_file(staged.directory / relative, expected)) == length,
             'native_layout_staged_generation_drift')
    argv = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--as-pid-1', '--cap-drop', 'ALL', '--clearenv', '--ro-bind', '/usr', '/usr']
    for name in ('bin', 'sbin', 'lib', 'lib64'):
        item = Path('/') / name
        if item.exists():
            resolved = item.resolve()
            need(resolved.is_relative_to('/usr'), 'native_layout_system_alias')
            argv += ['--symlink', str(resolved), str(item)]
    argv += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/opt',
             '--ro-bind', str(toolchain), PREFIX,
             '--ro-bind', '/usr/share', PREFIX + '/.host-share',
             '--ro-bind', str(toolchain / 'share-merged'), '/usr/share', '--dir', '/etc']
    for value in ('/etc/fonts', '/etc/ld.so.cache', '/var/cache/fontconfig'):
        if Path(value).exists():
            argv += ['--ro-bind', value, value]
    # One canonical writable work mount. Both code and source are separate RO
    # overlays; there is no /work alias that re-exposes the writable input inode.
    argv += ['--bind', str(work), WORK,
             '--ro-bind', str(source), WORK + '/input.ods',
             '--ro-bind', str(staged.directory), WORK + '/code',
             '--chdir', WORK, '--remount-ro', '/', '--',
             '/usr/bin/python3', '-I', '-B', '-S', WORK + '/code/' + staged.entry]
    return tuple(argv)


def apply_child_limits():
    """Only the real namespace PID1 entry may call this, before any descendant."""
    import resource
    need(os.getpid() == 1, 'native_layout_namespace_init_required')
    os.umask(0o077)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    need(bool(cpus), 'native_layout_cpu_affinity')
    os.sched_setaffinity(0, cpus)
    for key, value in ((resource.RLIMIT_AS, 1024**3), (resource.RLIMIT_CPU, 35),
                       (resource.RLIMIT_FSIZE, 16 * 1024**2),
                       (resource.RLIMIT_CORE, 0), (resource.RLIMIT_NOFILE, 128)):
        resource.setrlimit(key, (value, value))
    return tuple(cpus)
