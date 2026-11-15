"""Root preparation for one future private metric observation, not admission.

The stock document-toolchain bytes/font view are reused. This separate caller
adds explicit private read-only source/code/binding mounts and starts the exact
selected command rather than the normal document conversion entrypoint.
Import starts no process, loads no UNO, and touches no application profile.
"""
from pathlib import Path
import os
import stat

TOOLCHAIN = Path('/home/jericho/.jericho/toolchains/libreoffice-26.2.5.2-ubuntu26.04-amd64')
PREFIX = '/opt/friday-document-toolchain'
PROGRAM = PREFIX + '/root/usr/lib/libreoffice/program'
CACHE = Path('/home/jericho/.cache')
INNER_WORK = '/tmp/friday-metric-work'


def owned_directory(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts or not path.is_relative_to(CACHE):
        raise ValueError('exact_owned_cache_directory_required')
    # No resolved alias: every below-cache component must be a real directory.
    for parent in [path, *path.parents]:
        if parent == CACHE:
            break
        value = parent.lstat()
        if not stat.S_ISDIR(value.st_mode) or value.st_uid != os.getuid() or value.st_mode & 0o022:
            raise ValueError('owned_nonwritable_directory_required')
    return path


def build_namespace(*, writable, readonly, binding_root, command):
    """Build a finite executor argv; caller owns budget, process and evidence.

    There is deliberately no default operation, execution flag, source/case
    acceptance, or process launch here. A pure executor smoke is distinct from
    any later admitted Office load/metric and cannot supply its current facts.
    """
    writable = owned_directory(writable)
    binding_root = owned_directory(binding_root)
    readonly = [owned_directory(path) for path in readonly]
    if len(readonly) != len(set(readonly)) or writable in readonly or binding_root in readonly:
        raise ValueError('distinct_readonly_mounts_required')
    if any(p.is_relative_to(writable) or writable.is_relative_to(p) for p in readonly + [binding_root]):
        raise ValueError('overlapping_readwrite_mounts_refused')
    if not command or not all(type(a) is str and a and '\0' not in a for a in command):
        raise ValueError('explicit_command_required')
    if command[0] not in ('/usr/bin/python3', '/usr/bin/gdb', '/usr/bin/true'):
        raise ValueError('explicit_root_executor_required')
    args = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--hostname', 'friday-metric', '--ro-bind', '/', '/', '--tmpfs', '/opt',
            '--ro-bind', str(TOOLCHAIN), PREFIX,
            '--ro-bind', '/usr/share', PREFIX + '/.host-share',
            '--ro-bind', str(TOOLCHAIN / 'share-merged'), '/usr/share', '--tmpfs', '/etc']
    for path in ('/etc/fonts', '/etc/ld.so.cache', '/etc/localtime', '/etc/machine-id',
                 '/etc/nsswitch.conf', '/etc/passwd', '/etc/group'):
        args += ['--ro-bind-try', path, path]
    args += ['--tmpfs', '/var', '--ro-bind-try', '/var/cache/fontconfig', '/var/cache/fontconfig']
    for path in ('/home', '/root', '/mnt', '/media', '/srv'):
        args += ['--tmpfs', path]
    args += ['--dir', '/home/jericho', '--dir', str(CACHE)]
    for path in readonly + [binding_root]:
        args += ['--ro-bind', str(path), str(path)]
    args += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/run', '--tmpfs', '/sys',
             '--tmpfs', '/tmp', '--bind', str(writable), INNER_WORK, '--chdir', INNER_WORK, '--clearenv']
    environment = {
        'HOME': INNER_WORK + '/tmp', 'TMPDIR': INNER_WORK + '/tmp',
        'XDG_CACHE_HOME': INNER_WORK + '/cache', 'XDG_CONFIG_HOME': INNER_WORK + '/config',
        'XDG_RUNTIME_DIR': INNER_WORK + '/runtime', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
        'PATH': '/usr/bin:/bin', 'SAL_USE_VCLPLUGIN': 'svp',
        'LD_LIBRARY_PATH': str(binding_root / 'usr/lib/libreoffice/program') + ':' + PROGRAM + ':' + PREFIX + '/root/usr/lib/x86_64-linux-gnu',
        'URE_BOOTSTRAP': 'vnd.sun.star.pathname:' + PROGRAM + '/fundamentalrc',
        'PYTHONDONTWRITEBYTECODE': '1',
    }
    for name, value in environment.items():
        args += ['--setenv', name, value]
    return args + ['--', *command]
