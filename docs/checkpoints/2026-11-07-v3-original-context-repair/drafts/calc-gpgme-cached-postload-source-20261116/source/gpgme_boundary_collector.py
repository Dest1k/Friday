"""Read-only, finite collector for an already owned, stopped GDB inferior.

SOURCE ONLY. Importing this module performs no observation or target execution.
The collector never calls inferior functions, writes memory, steps, continues,
attaches, opens inferior output pipes, or creates breakpoints. The adapter owns
event routing and terminal custody. Every returned proof is for this all-stop
boundary only; it is not an admission or a claim of continuous stability.

API: BoundaryCollector(gdb, native_namespace, pins, runtime=bundle_runtime).
proc(pid) returns {pid,ppid,start_ticks}. At the adapter's already source-bound
original bootstrap, bind_current_environment(pid) freezes and returns a copy
of the actual effective environment for this one initialization. Subsequent
current_environment(pid) checks that complete frozen snapshot; it never binds
implicitly. image_binding(pid,image,pc), dependencies(pid,
role), fds(pid), config(pid), resources(pid), exec_observation(pid,image,pc,
role), snapshot(original_pid,role='original',expected_thread=None) collect
their named evidence. snapshot['context'] is the policy's exact boundary
context. Methods require a selected stopped owned inferior, except proc().

Pins contain genuine Root host-fstat evidence and a protected host-view UID
map witness for the exact collector user namespace. They are future runtime
inputs, never fabricated by this source package. Root must read the UID map
from its HOST user namespace and bind that witness to collector_userns. The
inside read is a SELF_TO_PARENT_USERNS view, not the Root reader's view.
The protected Root TARGET_TO_ROOT_READER_USERNS bytes alone translate host
owners; both maps are parsed and must have identical inside domains. Nonempty
kernel uid_map is write-once: the exact live collector userns ties both views
to that one immutable map. The self-view digest is frozen at first successful
join and checked with namespace/map/overflow CAS on every later join. Unknown
provenance, unmapped second-field sentinels, domain changes and overflow aliases
are refused; raw cross-view equality is diagnostic only, never authority. Both the actual namespace stamp and Root stamp are retained.
operation/original/reaper/private_roots/cgroup/uid_projection may be None in a
source template. They are bound exactly once to actual native birth, original
runtime clock, and the existing Root office-release/unit-release witness.
Masked cgroupfs is explicit: current membership, inherited /proc limits and
process usage are observed here; existing Root monitor owns current whole-unit
CPU/memory/stop enforcement. Its protected witness is never called an inner
read of kernel limits.
"""
import copy
import errno
import fcntl
import hashlib
import math
import os
import re
import stat
import struct
import time

if 'policy' not in globals():
    import gpgme_engine_policy as policy
if 'mapper' not in globals():
    import gpgme_mapped_image as mapper


STAMP_KEYS = {'dev_major', 'dev_minor', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'uid', 'nlink'}
NS_NAMES = ('user', 'mnt', 'pid', 'net', 'uts', 'ipc', 'cgroup')
MAX_FILE = 32 * 1024 * 1024
ENV_SOURCE = dict(libc_sha256='9941dc28e68bc5fd788d9cd024c69e68c791d63799e7538a97b6040dd9f50fb6',
    load_offset=0x8e21b, load_bytes='488b058e3d1800', got_offset=0x211fb0,
    storage_offset=0x219de8, dereference_offset=0x8e238, dereference_bytes='4c8b08',
    call_offset=0x8e242, call_bytes='e879cc0800', zero_fill_start=0x214000,
    data_memory_end=0x220d90)
# Exact same fifteen selected font inputs as immutable paper_helper_gdb.py.
# Other effective environment keys are frozen from actual libc memory at bind,
# not guessed from the launch environment or accepted by a name/value list.
FONT_ENV_KEYS = ('HOME', 'TMPDIR', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
    'FONTCONFIG_FILE', 'FONTCONFIG_PATH', 'FONTCONFIG_SYSROOT', 'FC_LANG', 'LANG', 'LC_ALL',
    'SAL_FONTPATH', 'SAL_USE_VCLPLUGIN', 'LD_LIBRARY_PATH', 'URE_BOOTSTRAP')


def need(value, reason):
    if not value:
        raise RuntimeError(reason)


def exact(value, keys, reason):
    need(type(value) is dict and set(value) == set(keys), reason)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def canonical(path):
    return (type(path) is str and path.startswith('/') and '\0' not in path and '\\' not in path
            and all(part not in ('', '.', '..') for part in path.split('/')[1:]))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(value):
    return dict(dev_major=os.major(value.st_dev), dev_minor=os.minor(value.st_dev),
        ino=value.st_ino, size=value.st_size, mtime_ns=value.st_mtime_ns,
        ctime_ns=value.st_ctime_ns, mode=value.st_mode, uid=value.st_uid, nlink=value.st_nlink)


def validate_stamp(value, *, root_file=False, directory=False):
    exact(value, STAMP_KEYS, 'gpgme_collector_stamp_schema')
    need(all(integer(v) for v in value.values()) and value['ino'] > 0 and value['nlink'] > 0,
         'gpgme_collector_stamp_values')
    if root_file:
        need(value['uid'] == 0 and stat.S_ISREG(value['mode']) and not value['mode'] & 0o022
             and value['nlink'] == 1 and 64 <= value['size'] <= MAX_FILE,
             'gpgme_collector_host_root_file_pin')
    if directory:
        need(stat.S_ISDIR(value['mode']) and not value['mode'] & 0o022,
             'gpgme_collector_directory_pin')
    return value


def validate_image(image):
    exact(image, ('path', 'sha256', 'build_id', 'host_stamp'), 'gpgme_collector_image_schema')
    need(canonical(image['path']) and policy.sha(image['sha256'])
         and type(image['build_id']) is str and re.fullmatch('[0-9a-f]{2,128}', image['build_id'])
         and len(image['build_id']) % 2 == 0, 'gpgme_collector_image_pin')
    validate_stamp(image['host_stamp'], root_file=True)
    return image


def validate_ns(value):
    exact(value, ('dev', 'ino'), 'gpgme_collector_namespace_schema')
    need(all(integer(v, 1) for v in value.values()), 'gpgme_collector_namespace_values')


# Finite exact post-main C.UTF-8 profile. These are data mappings, not
# ELF dependency images. No path prefix, optional file or arbitrary superset
# is accepted. Source/package proof is bound by this immutable collector.
EXIT_LOCALE_PROFILE = 'GNUPG_C_UTF8_GLIBC_2_43_EXIT_INTENT_V1'
EXIT_HELPERS = {
    'gpgconf': ('/usr/bin/gpgconf', 'fba79b5d1b14100b0696bc93bd47bb4d1816a32619c8de8f3094cf430c1db5f9',
                ('list_dirs', 'list_components', 'gpgconf_version')),
    'gpg': ('/usr/bin/gpg', 'c8f3dc07a34ab0a0a081368b482724b79a2a6d6b7aa856741c09edf7af854754',
            ('gpg_version',)),
    'gpgsm': ('/usr/bin/gpgsm', '1181239ec3a7a41a586f7c66aebb6b24cc5855dc3c020a3c8fd290dcac79e270',
              ('gpgsm_version',)),
}
EXIT_LOCALE_FILES = tuple(('/usr/lib/locale/C.utf8/' + name, 'r--p') for name in (
    'LC_ADDRESS', 'LC_COLLATE', 'LC_CTYPE', 'LC_IDENTIFICATION', 'LC_MEASUREMENT',
    'LC_MESSAGES/SYS_LC_MESSAGES', 'LC_MONETARY', 'LC_NAME', 'LC_NUMERIC',
    'LC_PAPER', 'LC_TELEPHONE', 'LC_TIME')) + (
    ('/usr/lib/locale/locale-archive', 'r--p'),
    ('/usr/lib/x86_64-linux-gnu/gconv/gconv-modules.cache', 'r--s'))
EXIT_LOCALE_SOURCE_SHA256 = {
    'source_package': '8da6cfd185aebbc3631cb5278763250c965d5e3d626e3d92adb926ad270eb4b4',
    'setlocale.c': '8b2370a4245679bfdaf02fa2bd2978e5611ddbb6b0234c9f59a19490273ca0fa',
    'findlocale.c': '813a8d07433d82a26d56b709a4c137d717b58053b94eca734bbc0c70fdc31e30',
    'loadlocale.c': 'd870b2d7064be7813f88faac4996ede36ebc6ebf12c564d4f8d9818d74a110af',
    'loadarchive.c': '1c475382c5f8cc7faaee13bbbd2aa8a3298db888de2c79e31c9833293acea841',
    'gconv_cache.c': '69f6b7a710e286a6a85aa34722e3cc1684b31da9710a1aff60e8abf4312c9ddf',
}


def validate_passive_file(image):
    exact(image, ('path', 'sha256', 'host_stamp', 'perms'), 'gpgme_collector_passive_schema')
    need((image['path'], image['perms']) in EXIT_LOCALE_FILES and policy.sha(image['sha256']),
         'gpgme_collector_passive_exact_path_or_permissions')
    host = validate_stamp(image['host_stamp'])
    need(host['uid'] == 0 and stat.S_ISREG(host['mode']) and not host['mode'] & 0o022
         and host['nlink'] == 1 and 1 <= host['size'] <= MAX_FILE,
         'gpgme_collector_passive_host_root_file_pin')
    return image


def validate_exit_profile(value, pins):
    exact(value, ('profile', 'phase', 'locale', 'source_sha256', 'files'),
          'gpgme_collector_exit_profile_schema')
    need(value['profile'] == EXIT_LOCALE_PROFILE and value['phase'] == 'exit_intent'
         and value['locale'] == 'C.UTF-8' and value['source_sha256'] == EXIT_LOCALE_SOURCE_SHA256,
         'gpgme_collector_exit_profile_source_phase_locale')
    need(pins['environment'].get('LC_ALL') == pins['environment'].get('LANG') == 'C.UTF-8'
         and not any(key in pins['environment'] for key in ('LOCPATH', 'GCONV_PATH', 'LANGUAGE')),
         'gpgme_collector_exit_profile_environment')
    files = value['files']
    need(type(files) is list and len(files) == len(EXIT_LOCALE_FILES),
         'gpgme_collector_exit_profile_file_bound')
    for image in files:
        validate_passive_file(image)
    need([(image['path'], image['perms']) for image in files] == list(EXIT_LOCALE_FILES),
         'gpgme_collector_exit_profile_exact_files')
    for role, (path, sha256, branches) in EXIT_HELPERS.items():
        if role not in pins['dependencies']:
            continue
        matches = [image for image in pins['dependencies'][role] if image['path'] == path]
        need(len(matches) == 1 and matches[0]['sha256'] == sha256,
             'gpgme_collector_exit_profile_exact_helper')
    return value


def validate_pins(pins):
    """Pure strict validation; it does not demand any future process exists."""
    exact(pins, ('operation', 'original', 'reaper', 'library', 'libc', 'environment', 'cwd',
                 'absent_paths', 'private_roots', 'cgroup', 'uid_projection', 'dependencies',
                 'exit_intent_mappings'),
          'gpgme_collector_pins_schema')
    if pins['operation'] is not None:
        exact(pins['operation'], ('operation_id', 'nonce', 'deadline_monotonic'),
              'gpgme_collector_operation_schema')
        op = pins['operation']
        need(type(op['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', op['operation_id'])
             and type(op['nonce']) is str and re.fullmatch('[0-9a-f]{32}', op['nonce'])
             and policy.positive(op['deadline_monotonic']), 'gpgme_collector_original_operation')
    for key in ('original', 'reaper'):
        if pins[key] is not None:
            policy.identity(pins[key])
    if pins['original'] is not None and pins['reaper'] is not None:
        need(pins['original']['pid'] != pins['reaper']['pid'], 'gpgme_collector_reaper_distinct')
    validate_image(pins['library'])
    validate_image(pins['libc'])
    need(pins['library']['path'] == policy.LIBRARY_PATH
         and pins['library']['sha256'] == policy.LIBRARY_SHA256
         and pins['library']['build_id'] == policy.BUILD_ID
         and pins['libc']['sha256'] == ENV_SOURCE['libc_sha256'], 'gpgme_collector_exact_source_images')
    policy.validate_environment(pins['environment'], pins['environment'])
    need(pins['cwd'] == '/tmp/friday-metric-work', 'gpgme_collector_cwd_pin')
    absent = pins['absent_paths']
    need(type(absent) is list and 1 <= len(absent) <= 128 and all(canonical(p) for p in absent)
         and len(set(absent)) == len(absent), 'gpgme_collector_absence_pins')
    # These are the default user configuration roots of the supported exact
    # engine source. Extra system configuration exclusions remain explicit pins.
    need('/tmp/friday-metric-work/tmp/.gnupg' in absent and '/etc/gnupg' in absent,
         'gpgme_collector_default_gnupg_config_exclusions')
    roots = pins['private_roots']
    if roots is None:
        roots = []  # Structural source template, not a runtime witness.
    need(type(roots) is list and len(roots) <= 16 and (roots or pins['private_roots'] is None),
         'gpgme_collector_private_roots_bound')
    names = []
    for root in roots:
        exact(root, ('path', 'stamp'), 'gpgme_collector_private_root_schema')
        need(canonical(root['path']) and (root['path'] == pins['cwd']
             or root['path'].startswith(pins['cwd'] + '/')), 'gpgme_collector_private_root_path')
        validate_stamp(root['stamp'], directory=True)
        need(stat.S_IMODE(root['stamp']['mode']) == 0o700, 'gpgme_collector_private_root_mode')
        names.append(root['path'])
    need(pins['private_roots'] is None or (len(set(names)) == len(names) and pins['cwd'] in names
         and all(v in names for k, v in pins['environment'].items()
                 if k in ('HOME', 'TMPDIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR', 'XDG_DATA_HOME'))),
         'gpgme_collector_private_environment_roots')
    c = pins['cgroup']
    if c is not None:
        _validate_cgroup_pin(c)
    u = pins['uid_projection']
    if u is not None:
        _validate_projection_pin(u)
    deps = pins['dependencies']
    need(type(deps) is dict and set(deps) <= {'original', 'gpgconf', 'gpg', 'gpgsm', 'g13'}
         and 'original' in deps, 'gpgme_collector_dependency_roles')
    for role, images in deps.items():
        need(type(images) is list and 1 <= len(images) <= 128, 'gpgme_collector_dependency_bound')
        for image in images:
            validate_image(image)
        paths = [image['path'] for image in images]
        need(len(set(paths)) == len(paths) and pins['libc'] in images
             and (role != 'original' or pins['library'] in images), 'gpgme_collector_dependency_pins')
    validate_exit_profile(pins['exit_intent_mappings'], pins)
    return pins


def _validate_cgroup_pin(c):
    exact(c, ('membership_sha256', 'mount_path', 'directory_stamp', 'cpu_max', 'memory_max',
              'pids_max', 'cpu_usage_origin_usec'), 'gpgme_collector_cgroup_schema')
    need(policy.sha(c['membership_sha256']) and canonical(c['mount_path'])
         and (c['mount_path'] == '/sys/fs/cgroup' or c['mount_path'].startswith('/sys/fs/cgroup/'))
         and type(c['cpu_max']) is str and re.fullmatch('(max|[0-9]+) [1-9][0-9]*\n', c['cpu_max'])
         and type(c['memory_max']) is str and re.fullmatch('[1-9][0-9]*\n', c['memory_max'])
         and int(c['memory_max']) <= 2147483648
         and type(c['pids_max']) is str and re.fullmatch('[1-9][0-9]*\n', c['pids_max'])
         and int(c['pids_max']) <= 512 and integer(c['cpu_usage_origin_usec']),
         'gpgme_collector_original_cgroup_limits')
    validate_stamp(c['directory_stamp'], directory=True)
    return c


UID_WITNESS_SCHEMA = 'frw.calc.host-uid-map-witness.v2'
HOST_MAP_VIEW = 'TARGET_TO_ROOT_READER_USERNS'
SELF_MAP_VIEW = 'SELF_TO_PARENT_USERNS'
UID_MAP_BASIS = 'KERNEL_WRITE_ONCE_UID_MAP_EXACT_USERNS'
UID_WITNESS_KEYS = ('schema', 'host_map_view', 'self_map_view', 'mapping_basis',
    'host_uid_map_ascii', 'root_host_uid_map_sha256', 'overflowuid', 'collector_userns', 'host_userns')


def _validate_projection_pin(u):
    exact(u, UID_WITNESS_KEYS, 'gpgme_collector_uid_projection_schema')
    need(u['schema'] == UID_WITNESS_SCHEMA and u['host_map_view'] == HOST_MAP_VIEW
         and u['self_map_view'] == SELF_MAP_VIEW and u['mapping_basis'] == UID_MAP_BASIS
         and type(u['host_uid_map_ascii']) is str and u['host_uid_map_ascii'].isascii()
         and 0 < len(u['host_uid_map_ascii']) <= 32768
         and policy.sha(u['root_host_uid_map_sha256'])
         and digest(u['host_uid_map_ascii'].encode('ascii')) == u['root_host_uid_map_sha256']
         and integer(u['overflowuid']) and u['overflowuid'] < 2 ** 32 - 1,
         'gpgme_collector_host_view_mapping_witness')
    parse_uid_map(u['host_uid_map_ascii'].encode('ascii'))
    validate_ns(u['collector_userns'])
    validate_ns(u['host_userns'])
    return u


def parse_proc_stat(raw, pid):
    need(type(raw) is bytes and 0 < len(raw) <= 4096 and integer(pid, 1), 'gpgme_collector_stat_bound')
    try:
        head, tail = raw.rsplit(b')', 1)
        need(head.split(b' (', 1)[0] == str(pid).encode(), 'gpgme_collector_stat_pid')
        fields = tail.split()
        need(len(fields) >= 22 and fields[0] in (b'R', b'S', b'D', b'T', b't', b'Z', b'X', b'I'),
             'gpgme_collector_stat_schema')
        result = dict(pid=pid, ppid=int(fields[1]), start_ticks=int(fields[19]))
        policy.identity(result)
        return result, dict(state=fields[0].decode(), utime_ticks=int(fields[11]),
                            stime_ticks=int(fields[12]), vsize=int(fields[20]), rss_pages=int(fields[21]))
    except (ValueError, IndexError):
        raise RuntimeError('gpgme_collector_stat_encoding') from None


def parse_uid_map(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 32768, 'gpgme_collector_uid_map_bound')
    rows = []
    try:
        need(raw.endswith(b'\n'), 'gpgme_collector_uid_map_encoding')
        for line in raw.splitlines(keepends=True):
            need(re.fullmatch(rb'[ \t]*[0-9]+[ \t]+[0-9]+[ \t]+[0-9]+[ \t]*\n', line),
                 'gpgme_collector_uid_map_encoding')
            parts = line.split()
            need(len(parts) == 3 and all(p.isdigit() for p in parts), 'gpgme_collector_uid_map_encoding')
            inside, outside, count = map(int, parts)
            need(count > 0 and 0 <= inside < 2 ** 32 - 1 and 0 <= outside < 2 ** 32 - 1
                 and inside + count <= 2 ** 32 - 1 and outside + count <= 2 ** 32 - 1,
                 'gpgme_collector_uid_map_range')
            need(all(inside + count <= a or a + n <= inside for a, b, n in rows)
                 and all(outside + count <= b or b + n <= outside for a, b, n in rows),
                 'gpgme_collector_uid_map_overlap')
            rows.append((inside, outside, count))
    except ValueError:
        raise RuntimeError('gpgme_collector_uid_map_encoding') from None
    need(1 <= len(rows) <= 340, 'gpgme_collector_uid_map_count')
    return rows


def project_host_owner(host_rows, host_uid, overflow):
    """Translate only protected ROOT-reader rows, never self-parent rows."""
    need(integer(host_uid) and host_uid < 2 ** 32 - 1 and integer(overflow)
         and overflow < 2 ** 32 - 1, 'gpgme_collector_host_owner_type')
    found = [inside + host_uid - outside for inside, outside, count in host_rows
             if outside <= host_uid < outside + count]
    need(len(found) <= 1, 'gpgme_collector_host_owner_map_ambiguous')
    if found:
        return found[0]
    need(not any(inside <= overflow < inside + count for inside, outside, count in host_rows),
         'gpgme_collector_overflow_aliases_mapped_uid')
    return overflow


def project_host_root(raw, overflow, witness, current_userns, *, self_map_sha256=None):
    """Join two labeled views of the same write-once, exact kernel userns.

    The protected Root release authorizes HOST rows; the actual /proc/self read
    supplies parent-relative rows, independently parsed and frozen by caller.
    A pure caller cannot turn an untrusted mapping/hash/boolean into authority:
    the real collector accepts this witness only from its birth/cgroup/nonce/
    clock-bound protected release and obtains raw/ns directly from the kernel.
    """
    _validate_projection_pin(witness)
    validate_ns(current_userns)
    need(self_map_sha256 is None or policy.sha(self_map_sha256),
         'gpgme_collector_self_map_baseline_type')
    need(integer(overflow) and overflow < 2 ** 32 - 1 and overflow == witness['overflowuid']
         and current_userns == witness['collector_userns']
         and (self_map_sha256 is None or digest(raw) == self_map_sha256),
         'gpgme_collector_uid_map_or_namespace_changed')
    self_rows = parse_uid_map(raw)
    host_raw = witness['host_uid_map_ascii'].encode('ascii')
    host_rows = parse_uid_map(host_raw)
    need(sorted((a, n) for a, b, n in self_rows) == sorted((a, n) for a, b, n in host_rows),
         'gpgme_collector_uid_map_or_namespace_changed')
    if current_userns == witness['host_userns']:
        need(self_rows == host_rows == [(0, 0, 2 ** 32 - 1)],
             'gpgme_collector_host_userns_identity_map')
    projected = project_host_owner(host_rows, 0, overflow)
    mapped = any(outside == 0 for inside, outside, count in host_rows)
    return dict(schema='frw.calc.host-root-uid-projection.v2', actual_uid=projected,
        source='EXACT_HOST_ROOT_MAP' if mapped else 'ACTUAL_UNMAPPED_HOST_ROOT_OVERFLOW',
        self_map_sha256=digest(raw), root_host_uid_map_sha256=digest(host_raw), overflowuid=overflow,
        self_map_view=SELF_MAP_VIEW, host_map_view=HOST_MAP_VIEW, mapping_basis=UID_MAP_BASIS,
        collector_userns=copy.deepcopy(current_userns), host_userns=copy.deepcopy(witness['host_userns']))


def projection_failure_metadata(raw, overflow, witness, current_userns, baseline, exc, *, after=None):
    """Bounded types/numbers/digests/flags only. No raw maps, paths or values."""
    u = witness if type(witness) is dict else {}
    def ns(value):
        return {k: value.get(k) if type(value) is dict and integer(value.get(k), 1) else None
                for k in ('dev', 'ino')}
    def rows(value):
        try:
            return parse_uid_map(value)
        except Exception:
            return None
    actual = rows(raw)
    host_text = u.get('host_uid_map_ascii')
    host_raw = host_text.encode('ascii') if type(host_text) is str and host_text.isascii() and len(host_text) <= 32768 else None
    host = rows(host_raw)
    actual_sha = digest(raw) if type(raw) is bytes and len(raw) <= 32768 else None
    host_sha = digest(host_raw) if host_raw is not None else None
    pinned_sha = u.get('root_host_uid_map_sha256')
    pinned_sha = pinned_sha if policy.sha(pinned_sha) else None
    safe_int = lambda v: v if integer(v) and v < 2 ** 32 else None
    return dict(schema='frw.calc.uid-projection-refusal-metadata.v1',
        phase='UID_PROJECTION', exception_class=type(exc).__name__[:64],
        raw_is_bytes=type(raw) is bytes, overflow_is_int=type(overflow) is int,
        witness_is_dict=type(witness) is dict, namespace_is_dict=type(current_userns) is dict,
        self_map_bytes=len(raw) if type(raw) is bytes and len(raw) <= 32768 else None,
        self_map_rows=None if actual is None else len(actual),
        host_map_rows=None if host is None else len(host),
        self_map_sha256=actual_sha, actual_host_map_sha256=host_sha, root_host_map_sha256=pinned_sha,
        self_baseline_sha256=baseline if policy.sha(baseline) else None,
        cross_view_raw_digest_equal=actual_sha is not None and actual_sha == host_sha,
        host_digest_matches_pin=host_sha is not None and host_sha == pinned_sha,
        self_map_matches_baseline=baseline is None or actual_sha == baseline,
        inside_domains_equal=actual is not None and host is not None and
            sorted((a, n) for a, b, n in actual) == sorted((a, n) for a, b, n in host),
        current_userns=ns(current_userns), collector_userns=ns(u.get('collector_userns')),
        host_userns=ns(u.get('host_userns')), namespace_matches=current_userns == u.get('collector_userns'),
        actual_overflowuid=safe_int(overflow), expected_overflowuid=safe_int(u.get('overflowuid')),
        overflow_matches=type(overflow) is int and type(u.get('overflowuid')) is int and overflow == u['overflowuid'],
        post_read_cas=after)


def parse_environment(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 131072 and raw.endswith(b'\0'),
         'gpgme_collector_environment_bound')
    items = raw[:-1].split(b'\0') if raw != b'\0' else []
    need(len(items) <= 512 and all(b'=' in item for item in items), 'gpgme_collector_environment_items')
    pairs = [item.split(b'=', 1) for item in items]
    try:
        result = {key.decode('ascii'): value.decode('utf-8', 'strict') for key, value in pairs}
    except UnicodeError:
        raise RuntimeError('gpgme_collector_environment_encoding') from None
    need(len(result) == len(pairs) and all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', k) for k in result),
         'gpgme_collector_environment_duplicates_or_keys')
    return result


def generic_elf_metadata(raw):
    """Bounded ELF64 x86-64 metadata for helpers/libc exceeding mapper's 2MiB.

    GpgME itself always uses the unchanged repaired mapper. No ELF is loaded.
    """
    need(type(raw) is bytes and 64 <= len(raw) <= MAX_FILE and raw[:7] == b'\x7fELF\x02\x01\x01',
         'gpgme_collector_ELF64_LE_bound')
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    need(h[1] in (2, 3) and h[2:4] == (62, 1) and h[8:10] == (64, 56)
         and 0 < h[10] <= 128 and 64 <= h[5] and h[5] + 56 * h[10] <= len(raw),
         'gpgme_collector_ELF_header')
    loads, builds = [], []
    for i in range(h[10]):
        kind, flags, off, va, pa, size, memory, align = struct.unpack_from('<IIQQQQQQ', raw, h[5] + 56 * i)
        need(off <= len(raw) and off + size <= len(raw) and va + memory <= 1 << 64,
             'gpgme_collector_ELF_segment_bound')
        if kind == 1:
            need(0 < size <= memory and align == 4096 and off % align == va % align and flags <= 7,
                 'gpgme_collector_ELF_PT_LOAD')
            loads.append(dict(flags=flags, offset=off, vaddr=va, filesz=size, memsz=memory))
        if kind == 4:
            cursor, end, count = off, off + size, 0
            while cursor < end:
                need(cursor + 12 <= end and count < 128, 'gpgme_collector_ELF_note_header')
                namesz, descsz, typ = struct.unpack_from('<III', raw, cursor)
                cursor += 12
                name_end = cursor + namesz
                desc = (name_end + 3) & ~3
                desc_end = desc + descsz
                need(name_end <= end and desc_end <= end, 'gpgme_collector_ELF_note_range')
                if raw[cursor:name_end] == b'GNU\0' and typ == 3:
                    need(0 < descsz <= 64, 'gpgme_collector_ELF_build_id')
                    builds.append(raw[desc:desc_end].hex())
                cursor, count = (desc_end + 3) & ~3, count + 1
            need(cursor == end, 'gpgme_collector_ELF_note_alignment')
    need(1 <= len(loads) <= 32 and len(builds) == 1, 'gpgme_collector_ELF_metadata_ambiguity')
    return dict(loads=loads, build_id=builds[0], sha256=digest(raw), elf_type=h[1], entry=h[4])


def generic_image_join(maps_before, maps_after, actual, host, raw, image, pc):
    need(type(maps_before) is bytes and maps_before == maps_after,
         'gpgme_collector_generic_maps_changed')
    validate_stamp(actual)
    validate_stamp(host, root_file=True)
    need(all(actual[k] == host[k] for k in STAMP_KEYS - {'uid'})
         and actual['size'] == len(raw) and integer(pc, 1),
         'gpgme_collector_generic_host_file_join')
    meta = generic_elf_metadata(raw)
    need(meta['sha256'] == image['sha256'] and meta['build_id'] == image['build_id'],
         'gpgme_collector_generic_hash_build_id')
    rows = mapper.parse_maps(maps_before)
    own = [r for r in rows if r['path'] == image['path']]
    same = [r for r in rows if (r['dev_major'], r['dev_minor'], r['ino']) ==
            (host['dev_major'], host['dev_minor'], host['ino'])]
    need(1 <= len(own) <= 32 and same == own and all(r['perms'].endswith('p') for r in own),
         'gpgme_collector_generic_mapping_alias_or_sharing')
    down = lambda v: v & ~4095
    up = lambda v: (v + 4095) & ~4095
    biases = None
    for row in own:
        values = set()
        for segment in meta['loads']:
            if (down(segment['offset']) <= row['offset'] < up(segment['offset'] + segment['filesz'])
                    and row['offset'] + row['end'] - row['start'] <= up(segment['offset'] + segment['filesz'])
                    and all(p == '-' or segment['flags'] & flag
                            for p, flag in zip(row['perms'][:3], (4, 2, 1)))):
                bias = row['start'] - (down(segment['vaddr']) + row['offset'] - down(segment['offset']))
                if bias >= 0 and bias % 4096 == 0:
                    values.add(bias)
        need(values, 'gpgme_collector_generic_mapping_not_PT_LOAD')
        biases = values if biases is None else biases & values
    need(len(biases) == 1, 'gpgme_collector_generic_load_bias_ambiguous')
    bias = biases.pop()
    selected = [r for r in own if r['start'] <= pc < r['end'] and 'x' in r['perms']]
    need(len(selected) == 1 and any(s['flags'] & 1 and s['vaddr'] <= pc - bias < s['vaddr'] + s['memsz']
                                    for s in meta['loads']), 'gpgme_collector_generic_PC_not_PT_LOAD')
    need(meta['elf_type'] == 3 or bias == 0, 'gpgme_collector_ET_EXEC_nonzero_bias')
    return dict(schema='frw.calc.generic-current-map-join.v1', backing_sha256=meta['sha256'],
        build_id=meta['build_id'], device_major=host['dev_major'], device_minor=host['dev_minor'],
        inode=host['ino'], load_bias=bias, relative_pc=pc - bias,
        executable_map_start=selected[0]['start'], executable_map_end=selected[0]['end'],
        executable_file_offset=selected[0]['offset'], elf_entry=meta['entry'],
        runtime_attested=False, collector_complete=False)


# Exact source/ELF callsites from four existing Root-owned OwnC variants.
# No new caller image, process, helper or arbitrary mapped DSO is admitted.
OWNC_CACHED_CALLERS = {'4306445fda08251959d3f145644437e8d62ceca38414bbc2991730178e42320f': {'source_sha256': 'cd703be33373758c4cf735ed0c16dd9a6881bf3f6ba6243aeccfb634ab381938', 'target_elf_origin': 4194304, 'marker_offsets': {'fixture_after_close': 4926, 'fixture_after_load': 4876, 'fixture_close_marker': 4915, 'fixture_paper_done': 4865, 'fixture_query_marker': 4887, 'fixture_ready': 4854, 'fixture_restore_marker': 4904}, 'marker_entry_bytes': {'fixture_after_close': 'f30f1efa554889e5905dc3', 'fixture_after_load': 'f30f1efa554889e5905dc3', 'fixture_close_marker': 'f30f1efa554889e5905dc3', 'fixture_paper_done': 'f30f1efa554889e5905dc3', 'fixture_query_marker': 'f30f1efa554889e5897dfc8b45fc905d', 'fixture_ready': 'f30f1efa554889e5905dc3', 'fixture_restore_marker': 'f30f1efa554889e5905dc3'}, 'fixture_after_close_return': 4200239, 'fixture_close_marker_return': 4200234, 'fixture_query_marker_return': 4200214, 'fixture_restore_marker_return': 4200229}, '25f8b869bcdc7b4b3fef816bbf4a7c9a2564d4b57ec598bd8f86f1f096bafdd4': {'source_sha256': 'cd703be33373758c4cf735ed0c16dd9a6881bf3f6ba6243aeccfb634ab381938', 'target_elf_origin': 4194304, 'marker_offsets': {'fixture_after_close': 4862, 'fixture_after_load': 4812, 'fixture_close_marker': 4851, 'fixture_paper_done': 4801, 'fixture_query_marker': 4823, 'fixture_ready': 4790, 'fixture_restore_marker': 4840}, 'marker_entry_bytes': {'fixture_after_close': 'f30f1efa554889e5905dc3', 'fixture_after_load': 'f30f1efa554889e5905dc3', 'fixture_close_marker': 'f30f1efa554889e5905dc3', 'fixture_paper_done': 'f30f1efa554889e5905dc3', 'fixture_query_marker': 'f30f1efa554889e5897dfc8b45fc905d', 'fixture_ready': 'f30f1efa554889e5905dc3', 'fixture_restore_marker': 'f30f1efa554889e5905dc3'}, 'fixture_after_close_return': 4200065, 'fixture_close_marker_return': 4200060, 'fixture_query_marker_return': 4200040, 'fixture_restore_marker_return': 4200055}, '99e789e084989913a8df169f1b510ae8dfd7d239f6c961663413b9842e073866': {'source_sha256': '791cef29a79b5138e36964d7c3f2bdb607542f523a5fd9fd115bac547525a7c4', 'target_elf_origin': 4194304, 'marker_offsets': {'fixture_after_close': 5246, 'fixture_after_load': 5196, 'fixture_close_marker': 5235, 'fixture_paper_done': 5185, 'fixture_query_marker': 5207, 'fixture_ready': 5174, 'fixture_restore_marker': 5224}, 'marker_entry_bytes': {'fixture_after_close': 'f30f1efa554889e5905dc3', 'fixture_after_load': 'f30f1efa554889e5905dc3', 'fixture_close_marker': 'f30f1efa554889e5905dc3', 'fixture_paper_done': 'f30f1efa554889e5905dc3', 'fixture_query_marker': 'f30f1efa554889e5897dfc8b45fc905d', 'fixture_ready': 'f30f1efa554889e5905dc3', 'fixture_restore_marker': 'f30f1efa554889e5905dc3'}, 'cached_return': 4200424, 'fixture_after_close_return': 4200479, 'fixture_close_marker_return': 4200474, 'fixture_query_marker_return': 4200454, 'fixture_restore_marker_return': 4200469}, 'd4d078769f1730540f8f6ff48788946cab78b975cee9bb9cd5fb72920276e429': {'source_sha256': 'cd703be33373758c4cf735ed0c16dd9a6881bf3f6ba6243aeccfb634ab381938', 'target_elf_origin': 4194304, 'marker_offsets': {'fixture_after_close': 4862, 'fixture_after_load': 4812, 'fixture_close_marker': 4851, 'fixture_paper_done': 4801, 'fixture_query_marker': 4823, 'fixture_ready': 4790, 'fixture_restore_marker': 4840}, 'marker_entry_bytes': {'fixture_after_close': 'f30f1efa554889e5905dc3', 'fixture_after_load': 'f30f1efa554889e5905dc3', 'fixture_close_marker': 'f30f1efa554889e5905dc3', 'fixture_paper_done': 'f30f1efa554889e5905dc3', 'fixture_query_marker': 'f30f1efa554889e5897dfc8b45fc905d', 'fixture_ready': 'f30f1efa554889e5905dc3', 'fixture_restore_marker': 'f30f1efa554889e5905dc3'}, 'fixture_after_close_return': 4200057, 'fixture_close_marker_return': 4200052, 'fixture_query_marker_return': 4200032, 'fixture_restore_marker_return': 4200047}}

class BoundaryCollector:
    def __init__(self, gdb, native, pins, *, runtime=None):
        validate_pins(pins)
        need(type(native) is dict and callable(native.get('phase')) and callable(native.get('get_active')),
             'gpgme_collector_native_namespace')
        self.g, self.n, self.p, self.runtime = gdb, native, copy.deepcopy(pins), copy.deepcopy(runtime)
        self.known = {} if pins['original'] is None else {pins['original']['pid']: copy.deepcopy(pins['original'])}
        self.reaper = copy.deepcopy(pins['reaper'])
        self.refusal = None
        self._memory_total = 0
        self.host_witness = None
        self._release_digest = None
        self._unit_digest = None
        self._entry_verified = set()
        self._current_environment = None
        self._self_uid_map_sha256 = None
        self._uid_projection_failure = None
        self._uid_projection_failure_attempted = False
        self._birth_refusal_attempted = False

    def _read(self, path, limit):
        need(canonical(path) and integer(limit, 1) and limit <= MAX_FILE, 'gpgme_collector_read_bound')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            before = stamp(os.fstat(fd))
            chunks, size = [], 0
            while True:
                part = os.read(fd, min(65536, limit + 1 - size))
                if not part:
                    break
                chunks.append(part)
                size += len(part)
                need(size <= limit, 'gpgme_collector_read_over_bound')
            need(before == stamp(os.fstat(fd)), 'gpgme_collector_read_changed')
            return b''.join(chunks)
        finally:
            os.close(fd)

    def _stat_process(self, pid):
        need(integer(pid, 1), 'gpgme_collector_pid_type')
        return parse_proc_stat(self._read('/proc/%d/stat' % pid, 4096), pid)

    def pending_fork_child(self, parent_pid, tid, *, expected=None, materialized=False):
        """Observe one ptrace-held fork birth without adopting it in proc().

        This token permits only the separately proved GDB table operation. It
        grants no target execution or generic exemption from the proc guard.
        Compare it again BEFORE any post-materialization snapshot can adopt.
        """
        need(self.refusal is None and self.n['STATE']['error'] is None
             and self.g.parameter('non-stop') is False,
             'gpgme_pending_fork_terminal_or_nonstop')
        need(integer(tid, 1) and parent_pid in self.known,
             'gpgme_pending_fork_parent_unknown')
        parent = self.proc(parent_pid)
        path = '/proc/%d/task/%d/children' % (parent_pid, tid)
        raw = self._read(path, 4096)
        parts = raw.split()
        need(len(parts) == 1 and parts[0].isdigit(), 'gpgme_pending_fork_direct_child')
        pid = int(parts[0])
        need(pid > 1 and pid not in self.known and pid != os.getpid(),
             'gpgme_pending_fork_child_already_known')
        child, detail = self._stat_process(pid)
        need(child['ppid'] == parent_pid and detail['state'] == 't',
             'gpgme_pending_fork_birth_or_ptrace_stop')
        status = self._read('/proc/%d/status' % pid, 32768)
        def field(name, text=status):
            values = re.findall(rb'^' + name + rb':\s*([^\n]+)$', text, re.M)
            need(len(values) == 1, 'gpgme_pending_fork_status_field')
            return values[0].split()
        need(field(b'Pid') == field(b'Tgid') == [str(pid).encode()]
             and field(b'TracerPid') == [str(os.getpid()).encode()]
             and field(b'Threads') == [b'1'], 'gpgme_pending_fork_tracer_or_thread')
        parent_status = self._read('/proc/%d/status' % parent_pid, 32768)
        need(all(field(name) == field(name, parent_status) for name in (b'Uid', b'Gid')),
             'gpgme_pending_fork_credentials')
        tasks = os.listdir('/proc/%d/task' % pid)
        need(tasks == [str(pid)], 'gpgme_pending_fork_child_tasks')
        matches, rosters, pending_seen = [], {}, 0
        represented = represented_threads = 0
        for inf in self.g.inferiors():
            need(inf.is_valid(), 'gpgme_pending_fork_invalid_inferior')
            if not inf.pid:
                continue
            represented += 1
            if inf.pid == pid:
                matches.append(inf)
            else:
                need(inf.pid in self.known, 'gpgme_pending_fork_foreign_inferior')
                self.proc(inf.pid)
            threads = list(inf.threads())
            represented_threads += len(threads)
            need(represented <= 16 and represented_threads <= 1024,
                 'gpgme_pending_fork_roster_bound')
            need(0 < len(threads) <= 512 and all(t.is_valid() and t.is_stopped()
                 and list(t.ptid)[0] == inf.pid for t in threads),
                 'gpgme_pending_fork_not_all_stopped')
            for thread in threads:
                ptid = list(thread.ptid)
                policy.thread_identity(ptid)
                roster_path = '/proc/%d/task/%d/children' % (inf.pid, ptid[1])
                roster = self._read(roster_path, 4096)
                members = roster.split()
                need(len(members) <= 16 and all(v.isdigit() and int(v) > 0 for v in members)
                     and len({int(v) for v in members}) == len(members)
                     and roster_path not in rosters, 'gpgme_pending_fork_roster_bound')
                rosters[roster_path] = roster
                for value in members:
                    member = int(value)
                    if member == pid:
                        need(ptid == [parent_pid, tid, 0], 'gpgme_pending_fork_child_wrong_lwp')
                        pending_seen += 1
                    else:
                        # An unrepresented OS child is refused before any
                        # generic proc() call could turn it into a known PID.
                        need(member in self.known, 'gpgme_pending_fork_unknown_roster_child')
                        observed, _ = self._stat_process(member)
                        need(observed['start_ticks'] == self.known[member]['start_ticks']
                             and observed['ppid'] == inf.pid, 'gpgme_pending_fork_roster_birth_changed')
        need(pending_seen == 1, 'gpgme_pending_fork_pending_roster_ambiguous')
        child_roster_path = '/proc/%d/task/%d/children' % (pid, pid)
        child_roster = self._read(child_roster_path, 4096)
        need(child_roster_path not in rosters or rosters[child_roster_path] == child_roster,
             'gpgme_pending_fork_newborn_roster_cas')
        need(not child_roster.split(), 'gpgme_pending_fork_newborn_has_child')
        rosters.setdefault(child_roster_path, child_roster)
        need((not materialized and matches == []) or (materialized and len(matches) == 1
             and matches[0].num > 3 and [list(t.ptid) for t in matches[0].threads()] == [[pid, pid, 0]]),
             'gpgme_pending_fork_inferior_stage')
        namespaces = self._ns(os.getpid())
        need(self._ns(pid) == self._ns(parent_pid) == namespaces,
             'gpgme_pending_fork_namespaces')
        membership = self._read('/proc/%d/cgroup' % pid, 32768)
        need(membership == self._read('/proc/%d/cgroup' % parent_pid, 32768)
             == self._read('/proc/%d/cgroup' % os.getpid(), 32768),
             'gpgme_pending_fork_cgroup')
        limits = self._read('/proc/%d/limits' % pid, 32768)
        need(limits == self._read('/proc/%d/limits' % parent_pid, 32768),
             'gpgme_pending_fork_inherited_limits')
        exe, cwd = (stamp(os.stat('/proc/%d/%s' % (pid, name))) for name in ('exe', 'cwd'))
        need(exe == stamp(os.stat('/proc/%d/exe' % parent_pid))
             and cwd == stamp(os.stat('/proc/%d/cwd' % parent_pid)),
             'gpgme_pending_fork_exe_or_cwd')
        value = dict(identity=child, parent=parent, thread=[parent_pid, tid, 0],
            namespaces=namespaces, membership_sha256=digest(membership),
            limits_sha256=digest(limits), exe=exe, cwd=cwd)
        need(expected is None or value == expected, 'gpgme_pending_fork_custody_changed')
        child_after, detail_after = self._stat_process(pid)
        need(child_after == child and detail_after['state'] == 't'
             and self.proc(parent_pid) == parent and self._read(path, 4096) == raw
             and self._read('/proc/%d/status' % pid, 32768) == status
             and self._ns(pid) == namespaces
             and self._read('/proc/%d/cgroup' % pid, 32768) == membership
             and self._read('/proc/%d/limits' % pid, 32768) == limits
             and stamp(os.stat('/proc/%d/exe' % pid)) == exe
             and stamp(os.stat('/proc/%d/cwd' % pid)) == cwd
             and all(self._read(path, 4096) == raw for path, raw in rosters.items()),
             'gpgme_pending_fork_raw_cas')
        return value

    def proc(self, pid):
        if self.p['original'] is None or self.p['reaper'] is None or self.p['operation'] is None:
            native = self.n['STATE']['process']
            need(type(native) is dict and integer(native.get('pid'), 1), 'gpgme_collector_native_birth_unavailable')
            self._bind_runtime(native['pid'], require_witness=False)
        value, _ = self._stat_process(pid)
        need(self.p['original'] is not None and self.p['reaper'] is not None,
             'gpgme_collector_runtime_identities_not_bound')
        if pid == self.p['reaper']['pid']:
            need(value == self.p['reaper'], 'gpgme_collector_reaper_birth_changed')
            return value
        known = self.known.get(pid)
        if known is not None:
            need(value['start_ticks'] == known['start_ticks'], 'gpgme_collector_owned_birth_changed')
            if pid == self.p['original']['pid']:
                need(value == self.p['original'] and value['ppid'] == os.getpid(),
                     'gpgme_collector_original_birth_or_gdb_parent')
            else:
                need(value['ppid'] in self.known or value['ppid'] == self.p['reaper']['pid'],
                     'gpgme_collector_owned_parent_unknown')
            return value
        live = [i for i in self.g.inferiors() if i.pid == pid and i.is_valid()]
        try:
            need(len(live) == 1 and value['ppid'] in self.known,
                 'gpgme_collector_unowned_or_unobserved_birth')
        except RuntimeError as exc:
            # Attribution only, using facts already read above.  No diagnostic
            # failure may replace this guard or cause a retry/continuation.
            if not self._birth_refusal_attempted:
                self._birth_refusal_attempted = True
                try:
                    self._record_birth_refusal(pid, value, len(live), exc.__traceback__)
                except Exception:
                    pass
            raise
        parent = self.proc(value['ppid'])
        need(parent['start_ticks'] == self.known[parent['pid']]['start_ticks'],
             'gpgme_collector_parent_birth_changed')
        self.known[pid] = copy.deepcopy(value)
        return value

    def _record_birth_refusal(self, pid, value, matching_inferiors, failure_traceback):
        # Fixed numeric metadata joins the existing native trace via fail/save.
        # Never read another process, publish a file, or confer child custody.
        policy.identity(value)
        need(integer(pid, 1) and integer(matching_inferiors)
             and matching_inferiors <= 512, 'gpgme_collector_birth_diagnostic_bound')
        parent = self.known.get(value['ppid'])
        if parent is not None:
            policy.identity(parent)
        need(pid <= 2147483647 and all(v['pid'] <= 2147483647 and v['ppid'] <= 2147483647
             and v['start_ticks'] <= 18446744073709551615
             for v in ([value] if parent is None else [value, parent])),
             'gpgme_collector_birth_diagnostic_numeric_bound')
        frames, frame = [], failure_traceback.tb_frame
        roles = {'gpgme_boundary_collector.py': 'collector',
                 'gpgme_engine_gdb.py': 'adapter',
                 'native_return_observer.py': 'native', 'ownc_gdb.py': 'ownc_driver'}
        try:
            for _ in range(8):
                if frame is None:
                    break
                line = failure_traceback.tb_lineno if not frames else frame.f_lineno
                need(integer(line, 1) and line <= 1000000, 'gpgme_collector_birth_diagnostic_line')
                frames.append(dict(source_role=roles.get(os.path.basename(frame.f_code.co_filename), 'other'),
                                   line=line))
                frame = frame.f_back
        finally:
            del frame
        metadata = dict(schema='frw.calc.gpgme-first-unobserved-birth.v1',
            requested_pid=pid, observed_identity={k: value[k] for k in ('pid', 'ppid', 'start_ticks')},
            matching_valid_inferior_count=matching_inferiors,
            known_parent_count=0 if parent is None else 1,
            known_parent_identity=None if parent is None else {k: parent[k] for k in ('pid', 'ppid', 'start_ticks')},
            source_frames=frames, observation_scope='FIRST_FAILED_PROC_GUARD_ONLY_NO_CUSTODY_OR_RELEASE')
        state = self.n['STATE']
        need(type(state) is dict and 'gpgme_collector_birth_refusal' not in state,
             'gpgme_collector_birth_diagnostic_already_present')
        state['gpgme_collector_birth_refusal'] = metadata

    def _ns(self, pid):
        result = {}
        for name in NS_NAMES:
            value = os.stat('/proc/%d/ns/%s' % (pid, name))
            result[name] = dict(dev=value.st_dev, ino=value.st_ino)
        return result

    def _projection(self):
        raw = overflow = current_userns = after = None
        try:
            if self.host_witness is None:
                need(self.p['operation'] is not None and self.p['original'] is not None
                     and self.p['reaper'] is not None, 'gpgme_collector_native_identities_unbound')
                self._bind_host_witness()
            need(self.p['uid_projection'] is not None, 'gpgme_collector_host_uid_witness_unbound')
            current_userns = self._ns(os.getpid())['user']
            raw = self._read('/proc/%d/uid_map' % os.getpid(), 32768)
            overflow_raw = self._read('/proc/sys/kernel/overflowuid', 64)
            need(re.fullmatch(b'[0-9]+\n', overflow_raw), 'gpgme_collector_overflowuid_encoding')
            overflow = int(overflow_raw)
            result = project_host_root(raw, overflow, self.p['uid_projection'], current_userns,
                                       self_map_sha256=self._self_uid_map_sha256)
            raw_after = self._read('/proc/%d/uid_map' % os.getpid(), 32768)
            overflow_after = self._read('/proc/sys/kernel/overflowuid', 64)
            namespace_after = self._ns(os.getpid())['user']
            validate_ns(namespace_after)
            after = dict(self_map_sha256=digest(raw_after), current_userns=namespace_after,
                overflow_sha256=digest(overflow_after), self_map_equal=raw == raw_after,
                overflow_equal=overflow_raw == overflow_after, namespace_equal=current_userns == namespace_after)
            need(all(after[k] for k in ('self_map_equal', 'overflow_equal', 'namespace_equal')),
                 'gpgme_collector_uid_map_or_namespace_changed')
            self._self_uid_map_sha256 = result['self_map_sha256']
            return result
        except Exception as exc:
            # Preserve the first real guard even if metadata construction or
            # protected publication fails. No retry/rearm/clock change.
            if not self._uid_projection_failure_attempted:
                self._uid_projection_failure_attempted = True
                try:
                    self._uid_projection_failure = projection_failure_metadata(raw, overflow,
                        self.p['uid_projection'], current_userns, self._self_uid_map_sha256, exc, after=after)
                    self._publish_projection_failure(self._uid_projection_failure)
                except Exception:
                    pass
            raise

    def _publish_projection_failure(self, metadata):
        import json
        raw = (json.dumps(metadata, sort_keys=True, separators=(',', ':')) + '\n').encode()
        need(len(raw) <= 8192, 'gpgme_collector_uid_diagnostic_bound')
        directory = self._secure_open(self.p['cwd'])
        try:
            before = stamp(os.fstat(directory))
            need(stat.S_ISDIR(before['mode']) and before['uid'] == os.geteuid()
                 and stat.S_IMODE(before['mode']) == 0o700
                 and before == stamp(os.stat(self.p['cwd'], follow_symlinks=False)),
                 'gpgme_collector_uid_diagnostic_private_directory')
            fd = os.open('gpgme-uid-projection-refusal.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
            try:
                st = os.fstat(fd)
                need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == os.geteuid()
                     and stat.S_IMODE(st.st_mode) == 0o600, 'gpgme_collector_uid_diagnostic_rights')
                view = memoryview(raw)
                while view:
                    written = os.write(fd, view)
                    need(written > 0, 'gpgme_collector_uid_diagnostic_write')
                    view = view[written:]
                os.fsync(fd)
                need(stamp(os.fstat(fd)) == stamp(os.stat('gpgme-uid-projection-refusal.json',
                    dir_fd=directory, follow_symlinks=False)), 'gpgme_collector_uid_diagnostic_cas')
            finally:
                os.close(fd)
            need(all(stamp(os.fstat(directory))[k] == before[k] for k in
                     ('dev_major', 'dev_minor', 'ino', 'mode', 'uid'))
                 and all(stamp(os.stat(self.p['cwd'], follow_symlinks=False))[k] == before[k]
                         for k in ('dev_major', 'dev_minor', 'ino', 'mode', 'uid')),
                 'gpgme_collector_uid_diagnostic_directory_changed')
        finally:
            os.close(directory)

    def _all_stop(self, pid, expected_thread=None):
        need(self.refusal is None, self.refusal or 'gpgme_collector_terminal_refusal')
        need(self.g.parameter('non-stop') is False, 'gpgme_collector_gdb_non_stop_unsupported')
        inf = self.g.selected_inferior()
        need(inf.is_valid() and inf.pid in self.known and pid in self.known,
             'gpgme_collector_selected_inferior')
        selected = self.g.selected_thread()
        need(selected is not None and selected.is_valid() and selected.is_stopped(),
             'gpgme_collector_selected_thread')
        ptid = list(selected.ptid)
        policy.thread_identity(ptid)
        need(ptid[0] == inf.pid and (expected_thread is None or ptid == expected_thread),
             'gpgme_collector_selected_tid_changed')
        live, tids = [], []
        for candidate in self.g.inferiors():
            need(candidate.is_valid(), 'gpgme_collector_invalid_inferior')
            if candidate.pid == 0:
                continue
            self.proc(candidate.pid)
            need(integer(candidate.num, 1), 'gpgme_collector_inferior_number')
            threads = list(candidate.threads())
            need(0 < len(threads) <= 512, 'gpgme_collector_thread_bound')
            actual_tids = sorted(int(name) for name in os.listdir('/proc/%d/task' % candidate.pid)
                                 if name.isdecimal())
            observed_tids = []
            for thread in threads:
                need(thread.is_valid() and thread.is_stopped(), 'gpgme_collector_not_all_stopped')
                identity = list(thread.ptid)
                policy.thread_identity(identity)
                need(identity[0] == candidate.pid, 'gpgme_collector_thread_pid')
                actual, detail = parse_proc_stat(self._read('/proc/%d/task/%d/stat' %
                    (candidate.pid, identity[1]), 4096), identity[1])
                need(detail['state'] in ('t', 'T') and actual['ppid'] == self.proc(candidate.pid)['ppid'],
                     'gpgme_collector_kernel_thread_not_stopped')
                observed_tids.append(identity[1])
                tids.append(dict(ptid=identity, start_ticks=actual['start_ticks']))
            need(sorted(observed_tids) == actual_tids and len(set(observed_tids)) == len(observed_tids),
                 'gpgme_collector_missing_or_duplicate_thread')
            live.append((candidate.num, candidate.pid))
        need(0 < len(live) <= 16 and len(tids) <= 1024 and len({n for n, p in live}) == len(live)
             and len({p for n, p in live}) == len(live), 'gpgme_collector_inferior_bound')
        return dict(inferiors=sorted(live), threads=sorted(tids, key=lambda t: t['ptid']), selected=ptid)

    def _inferior(self, pid):
        matches = [inf for inf in self.g.inferiors() if inf.is_valid() and inf.pid == pid]
        need(len(matches) == 1, 'gpgme_collector_requested_inferior_ambiguous')
        return matches[0]

    def _secure_open(self, path):
        need(canonical(path), 'gpgme_collector_noncanonical_file')
        directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            parts = path.split('/')[1:]
            for component in parts[:-1]:
                new = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                              dir_fd=directory)
                os.close(directory)
                directory = new
            return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
        finally:
            os.close(directory)

    def _file(self, image, *, passive=False):
        need(type(passive) is bool, 'gpgme_collector_file_kind')
        (validate_passive_file if passive else validate_image)(image)
        projection = self._projection()
        descriptor = self._secure_open(image['path'])
        try:
            before = stamp(os.fstat(descriptor))
            expected = image['host_stamp']
            need(all(before[k] == expected[k] for k in STAMP_KEYS - {'uid'})
                 and before['uid'] == projection['actual_uid'], 'gpgme_collector_host_backing_pin_or_projection')
            raw = bytearray()
            while len(raw) <= MAX_FILE:
                part = os.read(descriptor, min(65536, MAX_FILE + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
            after = stamp(os.fstat(descriptor))
            # Reopen current canonical path while the same hashed FD is live.
            current = self._secure_open(image['path'])
            try:
                current_stamp = stamp(os.fstat(current))
            finally:
                os.close(current)
            need(before == after == current_stamp and len(raw) == before['size'] <= MAX_FILE,
                 'gpgme_collector_same_fd_or_current_path_changed')
            need(digest(raw) == image['sha256'], 'gpgme_collector_backing_hash')
            return bytes(raw), before, after, projection
        finally:
            os.close(descriptor)

    def image_binding(self, pid, image, pc):
        image = self._resolve_image(image)
        self.proc(pid)
        stop = self._all_stop(pid)
        namespaces = self._ns(os.getpid())
        need(self._ns(pid) == namespaces, 'gpgme_collector_cross_namespace_image')
        before = self._read('/proc/%d/maps' % pid, 524288)
        raw, first, last, projection = self._file(image)
        after = self._read('/proc/%d/maps' % pid, 524288)
        # Host stamp is used as a HOST stamp only after the explicit projection
        # comparison above. We do not replace the actual fstat uid in evidence.
        if image['path'] == self.p['library']['path']:
            result = mapper.bind_current_image(before, after, image['host_stamp'], image['host_stamp'], raw,
                {key: image[key] for key in ('path', 'sha256', 'build_id')}, pc)
        else:
            result = generic_image_join(before, after, first, image['host_stamp'], raw, image, pc)
        need(self._all_stop(pid) == stop and self._ns(os.getpid()) == namespaces
             and self._ns(pid) == namespaces and self.proc(pid)['start_ticks'] == self.known[pid]['start_ticks'],
             'gpgme_collector_image_boundary_changed')
        return dict(result, join=result, actual_namespace_stamp=first, actual_namespace_stamp_after=last,
                    root_host_stamp=copy.deepcopy(image['host_stamp']), uid_projection=projection,
                    current_path=image['path'], maps_sha256=digest(before), namespaces=namespaces)

    def _regions(self, pid):
        return mapper.parse_maps(self._read('/proc/%d/maps' % pid, 524288))

    def _memory(self, address, count, regions, *, owner=None, pid=None):
        need(integer(address, 1) and address < 1 << 47 and integer(count, 1) and count <= 64
             and address + count <= 1 << 47, 'gpgme_collector_memory_range')
        matches = [r for r in regions if r['start'] <= address and address + count <= r['end']
                   and r['perms'][0] == 'r' and (owner is None or r['path'] == owner)]
        need(len(matches) == 1, 'gpgme_collector_memory_not_current_readable_mapping')
        self._memory_total += count
        need(self._memory_total <= 524288, 'gpgme_collector_total_memory_bound')
        need(integer(pid, 1) and pid in self.known, 'gpgme_collector_memory_owned_pid')
        result = bytes(self._inferior(pid).read_memory(address, count))
        need(len(result) == count, 'gpgme_collector_short_memory_read')
        return result

    def _bound_environment(self):
        need(self.refusal is None, self.refusal or 'gpgme_collector_terminal_refusal')
        need(self._current_environment is not None, 'gpgme_collector_current_environment_unbound')
        return dict(self._current_environment)

    def bind_current_environment(self, pid):
        """Freeze once at the adapter's proved current original source site.

        The caller owns that source-site proof, before calling this method.
        This method independently requires the selected original all-stop
        boundary, reads actual pinned-libc GOT __environ twice, and joins its
        fifteen font inputs to both the static launch pins and actual kernel
        exec metadata. Kernel exec metadata is a separate startup baseline;
        it never stands in for the actual effective environment. The returned
        full dict is a copy; the internal complete snapshot is immutable.
        """
        if self.refusal is not None:
            raise RuntimeError(self.refusal)
        try:
            need(self._current_environment is None, 'gpgme_collector_current_environment_already_bound')
            identity = self.proc(pid)
            need(type(pid) is int and pid == self.p['original']['pid']
                 and identity == self.p['original'] and self.g.selected_inferior().pid == pid,
                 'gpgme_collector_current_environment_original_binding')
            stop = self._all_stop(pid)
            raw = self._read('/proc/%d/environ' % pid, 131072)
            initial = parse_environment(raw)
            policy.validate_environment(initial, initial)
            current = self._effective_environment(pid)
            policy.validate_environment(current, current)
            need(all(current.get(k) == initial.get(k) == self.p['environment'].get(k)
                     for k in FONT_ENV_KEYS), 'gpgme_collector_font_runtime_environment_changed')
            need(self._read('/proc/%d/environ' % pid, 131072) == raw
                 and self.proc(pid) == identity and self._all_stop(pid) == stop
                 and self.g.selected_inferior().pid == pid,
                 'gpgme_collector_current_environment_binding_changed')
            self._current_environment = tuple(sorted(current.items()))
            return dict(self._current_environment)
        except Exception as exc:
            self.refusal = str(exc) if type(exc) is RuntimeError else type(exc).__name__
            raise RuntimeError(self.refusal) from None

    def current_environment(self, pid):
        """Actual effective __environ, exact against the explicit frozen bind."""
        expected = self._bound_environment()
        result = self._effective_environment(pid)
        policy.validate_environment(result, expected)
        return result

    def _effective_environment(self, pid):
        """Bounded double actual read; no implicit initialization or admission."""
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        self._memory_total = 0
        libc = self.p['libc']
        regions = self._regions(pid)
        executable = [r for r in regions if r['path'] == libc['path'] and 'x' in r['perms']]
        need(len(executable) == 1, 'gpgme_collector_libc_mapping')
        bound = self.image_binding(pid, libc, executable[0]['start'])
        base = bound['join']['load_bias']
        read = lambda a, n, owner=None: self._memory(a, n, regions, owner=owner, pid=pid)
        for prefix in ('load', 'dereference', 'call'):
            code = bytes.fromhex(ENV_SOURCE[prefix + '_bytes'])
            need(read(base + ENV_SOURCE[prefix + '_offset'], len(code), libc['path']) == code,
                 'gpgme_collector_libc_environ_instruction')
        storage = int.from_bytes(read(base + ENV_SOURCE['got_offset'], 8, libc['path']), 'little')
        need(storage == base + ENV_SOURCE['storage_offset'], 'gpgme_collector_environ_interposition')
        need(any(r['start'] == base + ENV_SOURCE['zero_fill_start'] and r['start'] <= storage
                 and storage + 8 <= r['end'] and r['perms'] == 'rw-p' and r['path'] == '' for r in regions)
             and any(r['end'] == base + ENV_SOURCE['zero_fill_start'] and r['path'] == libc['path'] for r in regions)
             and storage + 8 <= base + ENV_SOURCE['data_memory_end'], 'gpgme_collector_environ_zero_fill')

        def collect():
            vector = int.from_bytes(read(storage, 8, ''), 'little')
            need(vector > 0 and vector % 8 == 0, 'gpgme_collector_environ_vector')
            entries, total = [], 0
            for index in range(513):
                address = int.from_bytes(read(vector + index * 8, 8), 'little')
                if address == 0:
                    return vector, parse_environment(b'\0'.join(entries) + b'\0')
                need(index < 512, 'gpgme_collector_environment_vector_bound')
                item = bytearray()
                for block in range(513):
                    cursor = address + len(item)
                    matching = [r for r in regions if r['start'] <= cursor < r['end'] and 'r' in r['perms']]
                    need(len(matching) == 1, 'gpgme_collector_environment_string_mapping')
                    count = min(64, matching[0]['end'] - cursor, 32769 - len(item))
                    need(count > 0, 'gpgme_collector_environment_item_bound')
                    chunk = read(cursor, count)
                    total += len(chunk)
                    need(total <= 131072, 'gpgme_collector_environment_total_bound')
                    end = chunk.find(b'\0')
                    if end >= 0:
                        item.extend(chunk[:end])
                        break
                    item.extend(chunk)
                    need(len(item) <= 32768, 'gpgme_collector_environment_item_bound')
                else:
                    raise RuntimeError('gpgme_collector_environment_item_bound')
                entries.append(bytes(item))
            raise RuntimeError('gpgme_collector_environment_vector_bound')

        pointer, result = collect()
        need((pointer, result) == collect() and self._regions(pid) == regions and self.proc(pid) == identity
             and self._all_stop(pid) == stop, 'gpgme_collector_effective_environment_changed')
        return result

    def fds(self, pid):
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        root = '/proc/%d/fd' % pid
        names = sorted(os.listdir(root))
        need(len(names) <= 256 and all(name.isdecimal() and str(int(name)) == name for name in names),
             'gpgme_collector_fd_inventory_bound')
        values = {}
        for name in names:
            number = int(name)
            before = stamp(os.stat(root + '/' + name))
            raw = self._read('/proc/%d/fdinfo/%s' % (pid, name), 4096)
            matches = re.findall(rb'^flags:\s+([0-7]+)$', raw, re.M)
            need(len(matches) == 1, 'gpgme_collector_fdinfo_flags')
            flags = int(matches[0], 8)
            actual = os.stat(root + '/' + name)
            need(stamp(actual) == before, 'gpgme_collector_fd_replaced')
            values[number] = dict(dev=actual.st_dev, ino=actual.st_ino, type=stat.S_IFMT(actual.st_mode),
                rdev=actual.st_rdev, access=flags & os.O_ACCMODE, cloexec=bool(flags & os.O_CLOEXEC))
            policy.fd(values[number])
        need(sorted(os.listdir(root)) == names
             and self.proc(pid) == identity and self._all_stop(pid) == stop,
             'gpgme_collector_fd_set_or_boundary_changed')
        return values

    def fd(self, pid, number):
        need(integer(number) and number <= 1048575, 'gpgme_collector_fd_number')
        actual = self.fds(pid)
        need(number in actual, 'gpgme_collector_fd_missing')
        return actual[number]

    def maps(self, pid):
        self.proc(pid)
        before = self._read('/proc/%d/maps' % pid, 524288)
        parsed = mapper.parse_maps(before)
        need(self._read('/proc/%d/maps' % pid, 524288) == before,
             'gpgme_collector_current_maps_changed')
        return parsed

    def _resolve_image(self, image):
        if type(image) is dict and set(image) == {'path', 'sha256', 'dev', 'ino'}:
            policy.helper_image(image)
            found = [candidate for images in self.p['dependencies'].values() for candidate in images
                     if candidate['path'] == image['path']]
            unique = []
            for candidate in found:
                if candidate not in unique:
                    unique.append(candidate)
            need(len(unique) == 1, 'gpgme_collector_short_image_missing_or_ambiguous')
            selected = unique[0]
            host = selected['host_stamp']
            need(selected['sha256'] == image['sha256'] and host['ino'] == image['ino']
                 and os.makedev(host['dev_major'], host['dev_minor']) == image['dev'],
                 'gpgme_collector_short_image_pin_changed')
            return selected
        validate_image(image)
        return image

    def pinned_file(self, image):
        image = self._resolve_image(image)
        raw, first, last, projection = self._file(image)
        meta = generic_elf_metadata(raw)
        need(meta['sha256'] == image['sha256'] and meta['build_id'] == image['build_id'],
             'gpgme_collector_pinned_file_ELF_changed')
        return dict(path=image['path'], sha256=meta['sha256'], build_id=meta['build_id'],
                    actual_namespace_stamp=first, actual_namespace_stamp_after=last,
                    root_host_stamp=image['host_stamp'], uid_projection=projection, metadata=meta)

    def children(self, pid, tid):
        parent = self.proc(pid)
        stop = self._all_stop(pid)
        need(integer(tid, 1) and any(t['ptid'][:2] == [pid, tid] for t in stop['threads']),
             'gpgme_collector_children_tid')
        raw = self._read('/proc/%d/task/%d/children' % (pid, tid), 4096)
        parts = raw.split()
        need(len(parts) <= 16 and all(part.isdigit() and int(part) > 0 for part in parts),
             'gpgme_collector_children_bound')
        values = [int(part) for part in parts]
        need(len(set(values)) == len(values), 'gpgme_collector_children_duplicate')
        need(self._read('/proc/%d/task/%d/children' % (pid, tid), 4096) == raw
             and self.proc(pid) == parent and self._all_stop(pid) == stop,
             'gpgme_collector_children_boundary_changed')
        return sorted(values)

    def exec_environment(self, pid):
        """Kernel startup view before entry; effective frozen view after entry.

        Only the original's kernel startup view uses static launch pins.
        Every child must inherit the explicitly bound full effective parent.
        """
        if pid in self._entry_verified:
            return self.current_environment(pid)
        return self._kernel_exec_environment(pid)

    def _kernel_exec_environment(self, pid):
        """Actual kernel exec metadata, separate from post-entry __environ."""
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        raw = self._read('/proc/%d/environ' % pid, 131072)
        value = parse_environment(raw)
        expected = (self.p['environment'] if pid == self.p['original']['pid']
                    else self._bound_environment())
        policy.validate_environment(value, expected)
        need(self._read('/proc/%d/environ' % pid, 131072) == raw and self.proc(pid) == identity
             and self._all_stop(pid) == stop, 'gpgme_collector_kernel_exec_environment_changed')
        return value

    def exec_image(self, pid, image, argv):
        image = self._resolve_image(image)
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        need(type(argv) is list and 1 <= len(argv) <= 16
             and all(type(v) is str and '\0' not in v for v in argv), 'gpgme_collector_exec_argv_schema')
        expected = b'\0'.join(v.encode('utf-8') for v in argv) + b'\0'
        need(len(expected) <= 32768 and self._read('/proc/%d/cmdline' % pid, 32768) == expected
             and os.readlink('/proc/%d/exe' % pid) == image['path'], 'gpgme_collector_exec_image_or_command')
        bound = self.pinned_file(image)
        observed = stamp(os.stat('/proc/%d/exe' % pid))
        need(observed == bound['actual_namespace_stamp'] and self.proc(pid) == identity
             and self._all_stop(pid) == stop, 'gpgme_collector_exec_inode_or_boundary_changed')
        return bound

    def _role_image(self, pid, role):
        need(type(role) is str and role in self.p['dependencies'], 'gpgme_collector_entry_role')
        path = os.readlink('/proc/%d/exe' % pid)
        found = [image for image in self.p['dependencies'][role] if image['path'] == path]
        need(len(found) == 1, 'gpgme_collector_entry_executable_not_pinned')
        return found[0]

    def entry_address(self, pid, role):
        self.proc(pid)
        self._all_stop(pid)
        image = self._role_image(pid, role)
        meta = self.pinned_file(image)['metadata']
        rows = self.maps(pid)
        executable = [r for r in rows if r['path'] == image['path'] and 'x' in r['perms']]
        need(len(executable) == 1, 'gpgme_collector_entry_executable_mapping')
        bound = self.image_binding(pid, image, executable[0]['start'])
        entry = bound['load_bias'] + meta['entry']
        raw = self._read('/proc/%d/auxv' % pid, 4096)
        need(len(raw) % 16 == 0 and 16 <= len(raw) <= 4096, 'gpgme_collector_auxv_bound')
        entries = [struct.unpack_from('<QQ', raw, offset) for offset in range(0, len(raw), 16)]
        need(entries[-1] == (0, 0) and all(k > 0 for k, v in entries[:-1])
             and len({k for k, v in entries}) == len(entries)
             and [v for k, v in entries if k == 9] == [entry]
             and any(r['start'] <= entry < r['end'] and 'x' in r['perms']
                     and r['path'] == image['path'] for r in rows), 'gpgme_collector_AT_ENTRY_or_load_join')
        return entry

    def verify_entry(self, pid, role, pc):
        need(integer(pc, 1) and self.g.selected_inferior().pid == pid
             and int(self.g.newest_frame().pc()) == pc == self.entry_address(pid, role),
             'gpgme_collector_not_actual_helper_entry')
        self._entry_verified.add(pid)
        return True

    def config(self, pid):
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        namespaces = self._ns(os.getpid())
        need(self._ns(pid) == namespaces, 'gpgme_collector_configuration_namespace')
        cwd = os.readlink('/proc/%d/cwd' % pid)
        need(cwd == self.p['cwd'], 'gpgme_collector_current_cwd')
        roots = []
        for item in self.p['private_roots']:
            descriptor = self._secure_open(item['path'])
            try:
                current = stamp(os.fstat(descriptor))
                need(all(current[k] == item['stamp'][k] for k in
                         ('dev_major', 'dev_minor', 'ino', 'mode', 'uid')) and current['uid'] == os.geteuid()
                     and stat.S_ISDIR(current['mode']) and stat.S_IMODE(current['mode']) == 0o700,
                     'gpgme_collector_private_root_changed')
            finally:
                os.close(descriptor)
            # Directory contents can legitimately grow during LOAD. Pin their
            # identity/rights; do not pretend original mtime is immutable data.
            roots.append(dict(path=item['path'], identity={k: current[k] for k in
                         ('dev_major', 'dev_minor', 'ino', 'mode', 'uid')}))
        for path in self.p['absent_paths']:
            need(not os.path.lexists(path), 'gpgme_collector_configuration_path_present')
        need(os.stat('/proc/%d/cwd' % pid).st_ino == os.stat(cwd).st_ino
             and os.stat('/proc/%d/cwd' % pid).st_dev == os.stat(cwd).st_dev,
             'gpgme_collector_cwd_identity')
        need(self.proc(pid) == identity and self._all_stop(pid) == stop
             and self._ns(pid) == self._ns(os.getpid()) == namespaces,
             'gpgme_collector_configuration_boundary_changed')
        return dict(cwd=cwd, private_roots=roots, absent_paths=list(self.p['absent_paths']),
                    namespaces=namespaces, scope='THIS_ALL_STOP_BOUNDARY_ONLY')

    def resources(self, pid):
        if self.host_witness is not None:
            return self._witness_resources(pid)
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        cgroup = self.p['cgroup']
        now = time.monotonic()
        need(now < self.p['operation']['deadline_monotonic'], 'gpgme_collector_original_deadline')
        member = self._read('/proc/%d/cgroup' % pid, 32768)
        own_member = self._read('/proc/%d/cgroup' % os.getpid(), 32768)
        need(member == own_member and digest(member) == cgroup['membership_sha256']
             and re.fullmatch(rb'0::/[^\n]*\n', member), 'gpgme_collector_cgroup_membership')
        # Pin actual cgroup2 mount identity rather than using a pathname prefix
        # as proof. Unsupported escaped/stacked mountpoints are refused.
        mounts = self._read('/proc/%d/mountinfo' % os.getpid(), 524288).splitlines()
        matches = []
        for line in mounts:
            parts = line.split()
            if b'-' not in parts:
                continue
            at = parts.index(b'-')
            if at + 1 < len(parts) and parts[at + 1] == b'cgroup2':
                need(len(parts) >= 7 and b'\\' not in parts[4], 'gpgme_collector_cgroup_mount_encoding')
                mount = parts[4].decode('ascii')
                if cgroup['mount_path'] == mount or cgroup['mount_path'].startswith(mount + '/'):
                    matches.append((mount, parts[3].decode('ascii')))
        need(len(matches) == 1, 'gpgme_collector_cgroup_mount_ambiguity')
        relative_member = member.decode('ascii').split('::', 1)[1].rstrip('\n')
        mount, mount_root = matches[0]
        joined = mount.rstrip('/') if relative_member == '/' else mount.rstrip('/') + relative_member
        need(mount_root == '/' and cgroup['mount_path'] == joined,
             'gpgme_collector_cgroup_mount_membership_join')
        path = cgroup['mount_path']
        before = stamp(os.stat(path, follow_symlinks=False))
        need(before == cgroup['directory_stamp'], 'gpgme_collector_cgroup_directory_changed')
        actual = {name: self._read(path + '/' + name.replace('_', '.'), 32768)
                  for name in ('cpu_max', 'memory_max', 'pids_max')}
        need(all(actual[name].decode('ascii') == cgroup[name] for name in actual),
             'gpgme_collector_cgroup_limit_changed')
        cpu = self._read(path + '/cpu.stat', 32768)
        usage = re.findall(rb'^usage_usec ([0-9]+)$', cpu, re.M)
        need(len(usage) == 1, 'gpgme_collector_cgroup_cpu_stat')
        used = int(usage[0])
        need(cgroup['cpu_usage_origin_usec'] <= used
             and used - cgroup['cpu_usage_origin_usec'] < 120000000,
             'gpgme_collector_original_whole_cgroup_cpu_budget')
        memory = self._read(path + '/memory.current', 64)
        need(re.fullmatch(rb'[0-9]+\n', memory) and int(memory) <= int(cgroup['memory_max']),
             'gpgme_collector_memory_budget')
        pids = self._read(path + '/cgroup.procs', 32768)
        need(all(part.isdigit() for part in pids.split()) and len(pids.split()) <= 512
             and pid in [int(part) for part in pids.split()]
             and os.getpid() in [int(part) for part in pids.split()], 'gpgme_collector_cgroup_pid_custody')
        need(stamp(os.stat(path, follow_symlinks=False)) == before
             and self._read('/proc/%d/cgroup' % pid, 32768) == member
             and self.proc(pid) == identity and self._all_stop(pid) == stop
             and time.monotonic() < self.p['operation']['deadline_monotonic'],
             'gpgme_collector_resource_boundary_changed')
        _, process_usage = self._stat_process(pid)
        return dict(membership_sha256=digest(member), cgroup_stamp=before,
            limits={name: actual[name].decode('ascii') for name in actual},
            cpu_usage_origin_usec=cgroup['cpu_usage_origin_usec'], cpu_usage_usec=used,
            original_cpu_consumed_usec=used - cgroup['cpu_usage_origin_usec'],
            memory_current=int(memory), cgroup_process_count=len(pids.split()),
            process_usage=process_usage, observed_monotonic=now,
            deadline_monotonic=self.p['operation']['deadline_monotonic'])

    def _json_file(self, path):
        """Read the existing protected release channel with same-FD/path CAS."""
        import json
        descriptor = self._secure_open(path)
        try:
            before = stamp(os.fstat(descriptor))
            need(stat.S_ISREG(before['mode']) and before['uid'] == os.geteuid()
                 and stat.S_IMODE(before['mode']) == 0o600 and before['nlink'] == 1
                 and before['size'] <= 131072, 'gpgme_collector_release_rights')
            chunks, size = [], 0
            while True:
                part = os.read(descriptor, min(16384, 131073 - size))
                if not part:
                    break
                chunks.append(part)
                size += len(part)
                need(size <= 131072, 'gpgme_collector_release_bound')
            need(before == stamp(os.fstat(descriptor))
                 and before == stamp(os.stat(path, follow_symlinks=False)),
                 'gpgme_collector_release_cas')
        finally:
            os.close(descriptor)
        raw = b''.join(chunks)
        def pairs(items):
            value = dict(items)
            need(len(value) == len(items), 'gpgme_collector_duplicate_json_key')
            return value
        return json.loads(raw, object_pairs_hook=pairs), digest(raw)

    def _release(self):
        release, release_sha = self._json_file('/tmp/friday-metric-work/office-release.json')
        unit, unit_sha = self._json_file('/tmp/friday-metric-work/unit-release.json')
        op = self.p['operation']
        need(type(release) is dict and type(unit) is dict
             and all(release.get(k) == unit.get(k) == op[k] for k in ('operation_id', 'nonce'))
             and release.get('stage') == 'ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND'
             and unit.get('stage') == 'ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED',
             'gpgme_collector_release_operation_or_stage')
        host = release.get('host_binding')
        need(type(host) is dict and host.get('unit') == unit.get('unit')
             and type(unit.get('unit')) is str and re.fullmatch('[A-Za-z0-9_.@-]+', unit['unit'])
             and host.get('invocation_id') == unit.get('invocation_id')
             and type(unit.get('invocation_id')) is str
             and re.fullmatch('[0-9a-f]{32}', unit['invocation_id']),
             'gpgme_collector_release_unit_or_invocation')
        expected_ns = {name: os.readlink('/proc/%d/ns/%s' % (os.getpid(), name))
                       for name in ('pid', 'mnt', 'net', 'user')}
        boot = self._read('/proc/sys/kernel/random/boot_id', 128).decode('ascii').strip()
        original = self.p['original']
        native = self.n['STATE']['process']
        need(release.get('native_process') == host.get('native_process') == native
             and release.get('native_symbols') == host.get('native_symbols') == self.n['STATE']['symbols'],
             'gpgme_collector_release_native_binding')
        for role, pid, birth in (('office', original['pid'], original['start_ticks']),
                                 ('gdb', os.getpid(), self._stat_process(os.getpid())[0]['start_ticks'])):
            item = host.get(role)
            need(type(item) is dict and integer(item.get('pid'), 1) and integer(item.get('ppid'))
                 and type(item.get('nspid')) is list and item['nspid']
                 and all(integer(v, 1) for v in item['nspid']) and item['nspid'][-1] == pid
                 and item.get('start_ticks') == birth and item.get('namespaces') == expected_ns
                 and item.get('boot_id') == boot, 'gpgme_collector_release_host_process_join')
        cg = host.get('cgroup')
        need(host['office']['ppid'] == host['gdb']['pid'] and type(cg) is dict
             and cg.get('path') == unit.get('cgroup_path') and canonical(cg['path'])
             and integer(cg.get('inode'), 1)
             and host['office'].get('cgroup') == host['gdb'].get('cgroup') == '0::' + cg['path'],
             'gpgme_collector_release_host_cgroup_join')
        reaper = host.get('namespace_reaper')
        need(type(reaper) is dict and reaper.get('nspid') and reaper['nspid'][-1] == 1
             and reaper.get('start_ticks') == self.p['reaper']['start_ticks']
             and reaper.get('namespaces') == expected_ns and reaper.get('boot_id') == boot
             and reaper.get('cgroup') == '0::' + cg['path'], 'gpgme_collector_release_reaper_join')
        supervisor = unit.get('namespace_supervisor_host_identity')
        need(type(supervisor) is dict and type(supervisor.get('nspid')) is list and supervisor['nspid']
             and all(integer(pid, 1) for pid in supervisor['nspid'])
             and supervisor.get('namespaces') == expected_ns and supervisor.get('boot_id') == boot
             and supervisor.get('cgroup') == '0::' + cg['path'],
             'gpgme_collector_release_supervisor_join')
        supervisor_now, _ = self._stat_process(supervisor['nspid'][-1])
        need(supervisor_now['start_ticks'] == supervisor.get('start_ticks'),
             'gpgme_collector_release_supervisor_birth_changed')
        if self._release_digest is not None:
            need(release_sha == self._release_digest and unit_sha == self._unit_digest,
                 'gpgme_collector_accepted_release_changed')
        return release, unit, release_sha, unit_sha

    def _bind_host_witness(self):
        release, unit, release_sha, unit_sha = self._release()
        witness = release.get('gpgme_collector_witness')
        exact(witness, ('schema', 'operation_id', 'nonce', 'deadline_monotonic', 'uid_projection',
                        'private_roots', 'cgroup'), 'gpgme_collector_host_witness_schema')
        need(witness['schema'] == 'frw.calc.gpgme-collector-host-witness.v1'
             and all(witness[k] == self.p['operation'][k] for k in ('operation_id', 'nonce', 'deadline_monotonic')),
             'gpgme_collector_host_witness_operation')
        _validate_projection_pin(witness['uid_projection'])
        if self.p['uid_projection'] is not None:
            need(self.p['uid_projection'] == witness['uid_projection'], 'gpgme_collector_uid_witness_pin_changed')
        self.p['uid_projection'] = copy.deepcopy(witness['uid_projection'])
        self.host_witness = copy.deepcopy(witness)
        self._projection()
        # The protected Root map is in host-owner coordinates. The self map
        # checked above is parent-relative and must never translate these UIDs.
        mapping = parse_uid_map(witness['uid_projection']['host_uid_map_ascii'].encode('ascii'))

        def actual_owner(host_uid):
            return project_host_owner(mapping, host_uid, witness['uid_projection']['overflowuid'])

        roots = witness['private_roots']
        wanted = {self.p['cwd']} | {value for key, value in self.p['environment'].items()
                   if key in ('HOME', 'TMPDIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR', 'XDG_DATA_HOME')}
        need(type(roots) is list and 1 <= len(roots) <= 16, 'gpgme_collector_witness_private_bound')
        actual_roots = []
        for item in roots:
            exact(item, ('path', 'host_stamp'), 'gpgme_collector_witness_private_schema')
            need(item['path'] in wanted, 'gpgme_collector_witness_private_path')
            validate_stamp(item['host_stamp'], directory=True)
            descriptor = self._secure_open(item['path'])
            try:
                current = stamp(os.fstat(descriptor))
                need(all(current[k] == item['host_stamp'][k] for k in ('dev_major', 'dev_minor', 'ino', 'mode'))
                     and current['uid'] == actual_owner(item['host_stamp']['uid']) == os.geteuid()
                     and stat.S_IMODE(current['mode']) == 0o700 and stat.S_ISDIR(current['mode'])
                     and current == stamp(os.fstat(descriptor)), 'gpgme_collector_witness_private_identity')
                actual_roots.append(dict(path=item['path'], stamp=current))
            finally:
                os.close(descriptor)
        need({r['path'] for r in roots} == wanted and len(roots) == len(wanted),
             'gpgme_collector_witness_private_set')
        if self.p['private_roots'] is not None:
            need({r['path'] for r in self.p['private_roots']} == wanted,
                 'gpgme_collector_private_template_set_changed')
            bypath = {r['path']: r['stamp'] for r in self.p['private_roots']}
            need(all(all(r['stamp'][k] == bypath[r['path']][k] for k in
                         ('dev_major', 'dev_minor', 'ino', 'mode', 'uid')) for r in actual_roots),
                 'gpgme_collector_private_identity_pin_changed')
        self.p['private_roots'] = actual_roots
        cg = witness['cgroup']
        exact(cg, ('mount_path', 'directory_host_stamp', 'cpu_max', 'memory_max', 'pids_max', 'cpu_usage_origin_usec'),
              'gpgme_collector_host_cgroup_witness_schema')
        validate_stamp(cg['directory_host_stamp'], directory=True)
        bound = release['host_binding']['cgroup']
        need(cg['mount_path'] == '/sys/fs/cgroup' + bound['path']
             and cg['directory_host_stamp']['ino'] == bound['inode']
             and type(cg['cpu_max']) is str and re.fullmatch('[1-9][0-9]* [1-9][0-9]*\n', cg['cpu_max'])
             and len(set(cg['cpu_max'].split())) == 1
             and type(cg['memory_max']) is str and re.fullmatch('[1-9][0-9]*\n', cg['memory_max'])
             and int(cg['memory_max']) <= 2147483648
             and type(cg['pids_max']) is str and re.fullmatch('[1-9][0-9]*\n', cg['pids_max'])
             and int(cg['pids_max']) <= 512 and type(cg['cpu_usage_origin_usec']) is int
             and cg['cpu_usage_origin_usec'] == 0, 'gpgme_collector_root_whole_unit_budget_witness')
        member = self._read('/proc/%d/cgroup' % os.getpid(), 32768)
        need(member == self._read('/proc/%d/cgroup' % self.p['original']['pid'], 32768)
             and re.fullmatch(rb'0::/[^\n]*\n', member), 'gpgme_collector_initial_current_cgroup_membership')
        self.host_witness = copy.deepcopy(witness)
        self._membership = member
        self._inherited_limits = {
            'gdb': self._read('/proc/%d/limits' % os.getpid(), 32768),
            'original': self._read('/proc/%d/limits' % self.p['original']['pid'], 32768)}
        self._namespace_baseline = self._namespace_processes()
        self._release_digest, self._unit_digest = release_sha, unit_sha

    def _witness_resources(self, pid):
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        release, unit, _, _ = self._release()
        need(self._read('/proc/%d/cgroup' % pid, 32768)
             == self._read('/proc/%d/cgroup' % os.getpid(), 32768) == self._membership,
             'gpgme_collector_current_cgroup_membership_changed')
        # In this supported namespace /sys is intentionally masked. The Root
        # monitor enforces current whole-unit limits. Record current inherited
        # /proc limits and process counters without calling them a cgroup cap.
        own_limits = self._read('/proc/%d/limits' % os.getpid(), 32768)
        child_limits = self._read('/proc/%d/limits' % pid, 32768)
        need(b'Max cpu time' in own_limits and b'Max address space' in own_limits
             and b'Max cpu time' in child_limits and b'Max address space' in child_limits,
             'gpgme_collector_current_limits_missing')
        need(own_limits == self._inherited_limits['gdb']
             and child_limits == self._inherited_limits['original'],
             'gpgme_collector_current_inherited_guard_changed')
        _, usage = self._stat_process(pid)
        need(self.proc(pid) == identity and self._all_stop(pid) == stop
             and self._read('/proc/%d/cgroup' % pid, 32768) == self._membership
             and time.monotonic() < self.p['operation']['deadline_monotonic'],
             'gpgme_collector_root_monitored_resource_boundary_changed')
        cg = self.host_witness['cgroup']
        return dict(source='ROOT_MONITOR_CUSTODY_HOST_WITNESS', kernel_limits_current_inside=False,
            operation_id=self.p['operation']['operation_id'], nonce=self.p['operation']['nonce'],
            unit=unit['unit'], invocation_id=unit['invocation_id'],
            accepted_release_sha256=self._release_digest, accepted_unit_release_sha256=self._unit_digest,
            current_membership_sha256=digest(self._membership),
            host_cgroup_stamp=cg['directory_host_stamp'], host_limit_snapshot={k: cg[k] for k in
                ('cpu_max', 'memory_max', 'pids_max', 'cpu_usage_origin_usec')},
            current_inherited_limits_sha256=dict(gdb=digest(own_limits), process=digest(child_limits)),
            process_usage=usage, deadline_monotonic=self.p['operation']['deadline_monotonic'])

    def _namespace_processes(self):
        names = [name for name in os.listdir('/proc') if name.isdecimal()]
        need(0 < len(names) <= 512, 'gpgme_collector_namespace_process_bound')
        result = {}
        namespaces = self._ns(os.getpid())
        for name in names:
            pid = int(name)
            try:
                identity, _ = self._stat_process(pid)
                need(self._ns(pid) == namespaces, 'gpgme_collector_foreign_namespace_process')
                need(self._read('/proc/%d/cgroup' % pid, 32768) == self._membership,
                     'gpgme_collector_foreign_cgroup_process')
                result[pid] = identity
            except FileNotFoundError:
                # A disappearance is not accepted as a stable scan: callers
                # refuse and the first underlying boundary is retained.
                raise RuntimeError('gpgme_collector_namespace_process_changed') from None
        need(set(result) == {int(name) for name in os.listdir('/proc') if name.isdecimal()},
             'gpgme_collector_namespace_process_set_changed')
        return result

    def no_pipe_writer_or_descendant(self, pipe, child_identities):
        """Metadata-only exhaustive scan of this owned exclusive PID namespace.

        It never reads the pipe or a foreign environment/memory. Any inaccessible
        PID/FD, untracked new process, birth change, or unstable scan is refusal.
        """
        policy.pipe_key(pipe)
        need(type(child_identities) is list and 1 <= len(child_identities) <= 12,
             'gpgme_collector_terminal_children_bound')
        for child in child_identities:
            policy.identity(child)
            need(child['pid'] in self.known
                 and self.known[child['pid']]['start_ticks'] == child['start_ticks'],
                 'gpgme_collector_terminal_child_unobserved')
            need(not os.path.lexists('/proc/%d' % child['pid']), 'gpgme_collector_terminal_child_still_present')
        self._all_stop(self.p['original']['pid'])
        before = self._namespace_processes()
        allowed = set(self._namespace_baseline) | set(self.known)
        need(set(before) <= allowed, 'gpgme_collector_unobserved_namespace_descendant')
        for pid, identity in before.items():
            original = self._namespace_baseline.get(pid, self.known.get(pid))
            need(identity['start_ticks'] == original['start_ticks'], 'gpgme_collector_terminal_pid_reused')
            if pid == os.getpid():
                descriptors = self._self_fds()
                for item in descriptors.values():
                    if {key: item[key] for key in ('dev', 'ino', 'type', 'rdev')} == pipe:
                        need(item['access'] == os.O_RDONLY, 'gpgme_collector_gdb_retains_pipe_writer')
                need(self._self_fds() == descriptors, 'gpgme_collector_gdb_fd_custody_changed')
                continue
            names = os.listdir('/proc/%d/fd' % pid)
            need(len(names) <= 256 and all(n.isdecimal() for n in names),
                 'gpgme_collector_terminal_fd_scan_bound')
            for name in names:
                path = '/proc/%d/fd/%s' % (pid, name)
                current = os.stat(path)
                identity_key = dict(dev=current.st_dev, ino=current.st_ino,
                                    type=stat.S_IFMT(current.st_mode), rdev=current.st_rdev)
                if identity_key != pipe:
                    continue
                info = self._read('/proc/%d/fdinfo/%s' % (pid, name), 4096)
                flags = re.findall(rb'^flags:\s+([0-7]+)$', info, re.M)
                need(len(flags) == 1 and int(flags[0], 8) & os.O_ACCMODE == os.O_RDONLY,
                     'gpgme_collector_unreaped_pipe_writer')
                need(stamp(os.stat(path)) == stamp(current), 'gpgme_collector_terminal_pipe_fd_changed')
            need(sorted(os.listdir('/proc/%d/fd' % pid)) == sorted(names),
                 'gpgme_collector_terminal_fd_set_changed')
        need(self._namespace_processes() == before, 'gpgme_collector_terminal_namespace_scan_changed')
        return dict(schema='frw.calc.gpgme-no-writer-or-descendant.v1',
                    scanned_processes=len(before), all_observed_children_absent=True,
                    matching_write_descriptors=0, pipe=copy.deepcopy(pipe),
                    scope='THIS_METADATA_SCAN_ONLY_NO_PIPE_READ')

    def _self_fds(self):
        raw = self._read('/proc/%d/status' % os.getpid(), 32768)
        size = re.findall(rb'^FDSize:\s+([0-9]+)$', raw, re.M)
        need(len(size) == 1 and 0 < int(size[0]) <= 4096, 'gpgme_collector_gdb_fd_table_bound')
        result = {}
        # No directory iterator FD can appear/disappear in its own inventory.
        for number in range(int(size[0])):
            try:
                value = os.fstat(number)
                flags = fcntl.fcntl(number, fcntl.F_GETFL)
                fdflags = fcntl.fcntl(number, fcntl.F_GETFD)
            except OSError as exc:
                if exc.errno == errno.EBADF:
                    continue
                raise
            result[number] = dict(dev=value.st_dev, ino=value.st_ino, type=stat.S_IFMT(value.st_mode),
                rdev=value.st_rdev, access=flags & os.O_ACCMODE, cloexec=bool(fdflags & fcntl.FD_CLOEXEC))
        after = self._read('/proc/%d/status' % os.getpid(), 32768)
        need(re.findall(rb'^FDSize:\s+([0-9]+)$', after, re.M) == size,
             'gpgme_collector_gdb_fd_table_changed')
        return result

    def _passive_binding(self, pid, image, rows):
        validate_passive_file(image)
        need(self._ns(pid) == self._ns(os.getpid()), 'gpgme_collector_passive_cross_namespace')
        raw, first, last, projection = self._file(image, passive=True)
        host = image['host_stamp']
        own = [row for row in rows if row['path'] == image['path']]
        same = [row for row in rows if (row['dev_major'], row['dev_minor'], row['ino']) ==
                (host['dev_major'], host['dev_minor'], host['ino'])]
        need(len(own) == 1 and same == own and own[0]['perms'] == image['perms']
             and own[0]['offset'] == 0
             and own[0]['end'] - own[0]['start'] == (len(raw) + 4095) & ~4095,
             'gpgme_collector_passive_exact_mapping')
        return dict(path=image['path'], kind='PASSIVE_LOCALE_DATA', sha256=digest(raw),
                    actual_namespace_stamp=first, actual_namespace_stamp_after=last,
                    root_host_stamp=host, uid_projection=projection,
                    mapping=copy.deepcopy(own[0]), runtime_attested=False)

    def dependencies(self, pid, role, *, entry=True, phase='load_boundary', branch=None):
        need(type(role) is str and role in self.p['dependencies'], 'gpgme_collector_dependency_role')
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        before = self._read('/proc/%d/maps' % pid, 524288)
        rows = mapper.parse_maps(before)
        actual = {r['path'] for r in rows if r['path'].startswith('/')}
        images = self.p['dependencies'][role]
        need(type(entry) is bool, 'gpgme_collector_dependency_stage_type')
        need(phase in ('load_boundary', 'exit_intent') and
             ((phase == 'load_boundary' and branch is None) or (phase == 'exit_intent' and entry)),
             'gpgme_collector_dependency_phase')
        passive = []
        if phase == 'exit_intent':
            need(role in EXIT_HELPERS and branch in EXIT_HELPERS[role][2]
                 and pid in self._entry_verified, 'gpgme_collector_exit_profile_role_branch_or_entry')
            image = self._role_image(pid, role)
            need((image['path'], image['sha256']) == EXIT_HELPERS[role][:2],
                 'gpgme_collector_exit_profile_current_image')
            environment = self.current_environment(pid)
            need(environment.get('LANG') == environment.get('LC_ALL') == 'C.UTF-8'
                 and not any(key in environment for key in ('LOCPATH', 'GCONV_PATH', 'LANGUAGE')),
                 'gpgme_collector_exit_profile_current_environment')
            passive = self.p['exit_intent_mappings']['files']
        expected = {i['path'] for i in images} | {i['path'] for i in passive}
        need(actual <= expected and (not entry or actual == expected),
             'gpgme_collector_exact_mapped_dependency_set')
        need(os.readlink('/proc/%d/exe' % pid) in actual,
             'gpgme_collector_dependency_main_executable_missing')
        result = []
        for image in images:
            if image['path'] not in actual:
                continue
            executable = [r for r in rows if r['path'] == image['path'] and 'x' in r['perms']]
            need(len(executable) == 1, 'gpgme_collector_dependency_executable_mapping')
            result.append(dict(path=image['path'], binding=self.image_binding(pid, image, executable[0]['start'])))
        result.extend(self._passive_binding(pid, image, rows) for image in passive)
        need(self._read('/proc/%d/maps' % pid, 524288) == before and self.proc(pid) == identity
             and self._all_stop(pid) == stop, 'gpgme_collector_dependency_boundary_changed')
        return result

    def exec_observation(self, pid, image, pc, role):
        identity = self.proc(pid)
        stop = self._all_stop(pid)
        need(os.readlink('/proc/%d/exe' % pid) == image['path'], 'gpgme_collector_exec_current_image')
        executable = os.stat('/proc/%d/exe' % pid)
        host = image['host_stamp']
        need(os.major(executable.st_dev) == host['dev_major'] and os.minor(executable.st_dev) == host['dev_minor']
             and executable.st_ino == host['ino'], 'gpgme_collector_exec_current_inode')
        raw = self._read('/proc/%d/cmdline' % pid, 32768)
        need(raw.endswith(b'\0') and len(raw.split(b'\0')) <= 17, 'gpgme_collector_exec_argv_bound')
        try:
            command = [part.decode('utf-8', 'strict') for part in raw[:-1].split(b'\0')]
        except UnicodeError:
            raise RuntimeError('gpgme_collector_exec_argv_encoding') from None
        # At exec-before-first-instruction the initial environment is actual
        # kernel exec metadata. At entry, effective __environ is additionally
        # read from the pinned libc; an unloaded libc cannot be guessed.
        initial_env = self._kernel_exec_environment(pid)
        if pid in self._entry_verified:
            self.current_environment(pid)
        fds = self.fds(pid)
        binding = self.image_binding(pid, image, pc)
        need(self.proc(pid) == identity and self._all_stop(pid) == stop
             and self._read('/proc/%d/cmdline' % pid, 32768) == raw,
             'gpgme_collector_exec_boundary_changed')
        return dict(identity=identity, command=command, initial_exec_environment=initial_env,
                    fds=fds, image=binding, role=role,
                    environment_source='KERNEL_EXEC_RANGE_ONLY_NOT_EFFECTIVE_AFTER_EXEC')

    def _window(self, *, readonly=False):
        need(type(self.runtime) is dict, 'gpgme_collector_runtime_unbound')
        r = self.runtime
        op = self.p['operation']
        need(all(r.get(key) == op[key] for key in ('operation_id', 'nonce'))
             and r.get('operation_deadline_monotonic') == op['deadline_monotonic']
             and canonical(r.get('marker_path')), 'gpgme_collector_runtime_operation_binding')
        descriptor = self._secure_open(r['marker_path'])
        try:
            before = stamp(os.fstat(descriptor))
            need(stat.S_ISREG(before['mode']) and before['uid'] == os.geteuid()
                 and stat.S_IMODE(before['mode']) == 0o600 and before['nlink'] == 1
                 and before['size'] <= 4096, 'gpgme_collector_load_marker_rights')
            raw = os.read(descriptor, 4097)
            need(len(raw) <= 4096 and before == stamp(os.fstat(descriptor))
                 and before == stamp(os.stat(r['marker_path'], follow_symlinks=False)),
                 'gpgme_collector_load_marker_cas')
        finally:
            os.close(descriptor)
        import json
        def pairs(items):
            value = dict(items)
            need(len(value) == len(items), 'gpgme_collector_duplicate_marker_key')
            return value
        marker = json.loads(raw, object_pairs_hook=pairs)
        exact(marker, ('schema', 'operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'state',
                       'operation_deadline_monotonic'), 'gpgme_collector_load_marker_schema')
        need(marker['schema'] == 'frw.calc.load-dependency-window.v1' and marker['state'] == ('LOAD_CLOSED' if readonly else 'LOAD_OPEN')
             and all(marker[key] == r[key] for key in
                     ('operation_id', 'nonce', 'source_sha256', 'operation_deadline_monotonic'))
             and marker['manifest_ref'] == r['paper_manifest_ref'], 'gpgme_collector_load_marker_binding')
        if readonly:
            return dict(marker_sha256=digest(raw), marker_stamp=before,
                        native=self._readonly_phase())
        need(self.n['phase']() == {'nonce': op['nonce'], 'phase': 'IDLE', 'index': None, 'digit': None}
             and type(self.n['STATE']['records']) is list and self.n['STATE']['records'] == []
             and self.n['get_active']() is None and self.n['STATE'].get('error') is None,
             'gpgme_collector_outside_idle_records0_load')
        return dict(marker_sha256=digest(raw), marker_stamp=before)

    def _readonly_phase(self):
        """Finite post-load observation, never a spawn-policy context.

        Ordinary callers have IDLE/0 or CLOSED/10. OwnC keeps IDLE while its
        exact inert marker prefix grows, and closes only after restore/close.
        No METRIC-active or hypothetical Office lifecycle is admitted here.
        """
        phase, state = self.n['phase'](), self.n['STATE']
        records = state['records']
        need(type(records) is list and len(records) <= 10
             and self.n['get_active']() is None and state.get('error') is None,
             'gpgme_collector_readonly_active_or_refused')
        count = len(records)
        closed = phase == dict(nonce=self.p['operation']['nonce'], phase='CLOSED', index=None, digit=None)
        idle = phase == dict(nonce=self.p['operation']['nonce'], phase='IDLE', index=None, digit=None)
        need((idle and count == 0) or (closed and count == 10)
             or (idle and state.get('kind') == 'OWN_POPEN_FIXTURE_ONLY'),
             'gpgme_collector_readonly_phase')
        fixture = None
        if state.get('kind') == 'OWN_POPEN_FIXTURE_ONLY':
            expected = [dict(schema='frw.ownC.inert-marker.v1', index=i,
                semantics='FIXTURE_MARKER_ONLY_NO_NATIVE_RANGE') for i in range(count)]
            restore, close = state.get('fixture_restore_marker_seen'), state.get('fixture_close_marker_seen')
            need(records == expected and type(restore) is bool and type(close) is bool
                 and (not close or restore) and (not restore or count == 10)
                 and state.get('record_semantics') == 'FIXTURE_MARKER_ONLY'
                 and state.get('native_main_executed') is False
                 and type(state.get('accepted_held_points')) is int
                 and state['accepted_held_points'] in ((1, 2) if closed else (0, 1))
                 and (state['accepted_held_points'] != 0 or (count == 0 and not restore and not close))
                 and state.get('fixture_boundary') == ('AFTER_READONLY_CLOSE' if closed else 'AFTER_LOAD_BEFORE_QUERY')
                 and (not closed or (restore and close)),
                 'gpgme_collector_readonly_fixture_progress')
            fixture = dict(boundary=state['fixture_boundary'], restore=restore, close=close,
                           held=state['accepted_held_points'])
        import json
        return dict(phase=copy.deepcopy(phase), records_count=count,
            records_sha256=digest(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()),
            fixture=fixture)

    def readonly_caller(self, original_pid, pc, *, site='cached_return'):
        """Bind a current caller to existing CFG or library pins, not a grant.

        CFG target/symbol pins already belong to the launch owner. Their
        namespace fstat is retained as such, never relabelled a Root host stamp.
        No arbitrary mapped module becomes a permitted caller.
        """
        identity = self.proc(original_pid)
        stop = self._all_stop(original_pid)
        cfg = self.n['CFG']
        owner = self.g.solib_name(pc) or cfg['target_path']
        need(canonical(owner), 'gpgme_collector_readonly_caller_owner')
        if owner == self.p['library']['path']:
            need(cfg.get('kind') != 'OWN_POPEN_FIXTURE_ONLY',
                 'gpgme_collector_readonly_fixture_source_caller')
            return dict(kind='PINNED_LIBRARY', binding=self.image_binding(original_pid, self.p['library'], pc))
        pins = [(cfg.get('target_path'), cfg.get('target_sha256')),
                (cfg.get('symbol_file_path'), cfg.get('symbol_file_sha256'))]
        hashes = {sha for path, sha in pins if path == owner and type(sha) is str}
        need(len(hashes) == 1, 'gpgme_collector_readonly_caller_unpinned')
        expected = None
        if cfg.get('kind') == 'OWN_POPEN_FIXTURE_ONLY':
            expected = OWNC_CACHED_CALLERS.get(cfg['target_sha256'])
            need(expected is not None and owner == cfg['target_path']
                 and expected['source_sha256'] == self.runtime['source_sha256']
                 and cfg['marker_offsets'] == expected['marker_offsets'],
                 'gpgme_collector_readonly_fixture_source_caller')
            if site in expected:
                need(pc == expected[site], 'gpgme_collector_readonly_exact_caller_site')
            else:
                need(site in ('fixture_query_marker', 'fixture_restore_marker',
                              'fixture_close_marker', 'fixture_after_close')
                     and pc == expected['target_elf_origin'] + expected['marker_offsets'][site],
                     'gpgme_collector_readonly_exact_marker_site')
        regions = self.maps(original_pid)
        selected = [r for r in regions if r['path'] == owner and r['start'] <= pc
                    and pc + 16 <= r['end'] and r['perms'] == 'r-xp']
        need(len(selected) == 1, 'gpgme_collector_readonly_caller_mapping')
        row = selected[0]
        fd = self._secure_open(owner)
        try:
            before = stamp(os.fstat(fd))
            need(stat.S_ISREG(before['mode']) and before['nlink'] == 1
                 and not before['mode'] & 0o022 and before['size'] <= MAX_FILE,
                 'gpgme_collector_readonly_caller_file')
            raw = bytearray()
            while len(raw) <= MAX_FILE:
                part = os.read(fd, min(65536, MAX_FILE + 1 - len(raw)))
                if not part: break
                raw.extend(part)
            need(before == stamp(os.fstat(fd)) == stamp(os.stat(owner, follow_symlinks=False))
                 and len(raw) == before['size'] and digest(raw) in hashes,
                 'gpgme_collector_readonly_caller_cas_hash')
        finally:
            os.close(fd)
        need(all(row[k] == before[k] for k in ('dev_major', 'dev_minor', 'ino')),
             'gpgme_collector_readonly_caller_file_mapping')
        meta = generic_elf_metadata(bytes(raw))
        own = [r for r in regions if r['path'] == owner]
        same = [r for r in regions if all(r[k] == before[k] for k in ('dev_major', 'dev_minor', 'ino'))]
        need(1 <= len(own) <= 32 and same == own and all(r['perms'].endswith('p') for r in own),
             'gpgme_collector_readonly_caller_alias_or_sharing')
        down, up = lambda v: v & ~4095, lambda v: (v + 4095) & ~4095
        biases = None
        for region in own:
            values = set()
            for segment in meta['loads']:
                if (down(segment['offset']) <= region['offset'] < up(segment['offset'] + segment['filesz'])
                        and region['offset'] + region['end'] - region['start'] <= up(segment['offset'] + segment['filesz'])
                        and all(p == '-' or segment['flags'] & flag
                                for p, flag in zip(region['perms'][:3], (4, 2, 1)))):
                    bias = region['start'] - (down(segment['vaddr']) + region['offset'] - down(segment['offset']))
                    if bias >= 0 and bias % 4096 == 0: values.add(bias)
            need(values, 'gpgme_collector_readonly_caller_not_PT_LOAD')
            biases = values if biases is None else biases & values
        need(len(biases) == 1, 'gpgme_collector_readonly_caller_bias_ambiguous')
        bias = biases.pop()
        need((meta['elf_type'] == 3 or bias == 0)
             and any(v['flags'] & 1 and v['vaddr'] <= pc-bias < v['vaddr']+v['filesz'] for v in meta['loads']),
             'gpgme_collector_readonly_caller_ELF_bias_or_PC')
        offset = row['offset'] + pc - row['start']
        loads = [v for v in meta['loads'] if v['flags'] & 1 and v['offset'] <= offset
                 and offset + 16 <= v['offset'] + v['filesz']]
        need(len(loads) == 1 and bytes(self._inferior(original_pid).read_memory(pc, 16)) == raw[offset:offset+16]
             and self.maps(original_pid) == regions and self.proc(original_pid) == identity
             and self._all_stop(original_pid) == stop,
             'gpgme_collector_readonly_caller_boundary_changed')
        if expected is not None:
            if site.endswith('_return'):
                need(offset >= 5 and raw[offset-5] == 0xe8
                     and bytes(self._inferior(original_pid).read_memory(pc-5, 5)) == raw[offset-5:offset],
                     'gpgme_collector_readonly_caller_call_opcode')
            else:
                code = bytes.fromhex(expected['marker_entry_bytes'][site])
                need(raw[offset:offset+len(code)] == code
                     and bytes(self._inferior(original_pid).read_memory(pc, len(code))) == code,
                     'gpgme_collector_readonly_marker_entry_bytes')
        return dict(kind='PINNED_LAUNCH_CALLER', path=owner, sha256=meta['sha256'],
            build_id=meta['build_id'], namespace_stamp=before, mapping=row, load_bias=bias, relative_pc=pc-bias, site=site, pc=pc,
            code_sha256=digest(raw[offset:offset+16]))

    def snapshot(self, original_pid, role='original', expected_thread=None):
        return self._snapshot(original_pid, role, expected_thread, readonly=False)

    def readonly_snapshot(self, original_pid, expected_thread=None):
        return self._snapshot(original_pid, 'original', expected_thread, readonly=True)

    def _snapshot(self, original_pid, role, expected_thread, *, readonly):
        """Collect real current facts, terminally refusing the first ambiguity."""
        if self.refusal is not None:
            raise RuntimeError(self.refusal)
        try:
            self._bind_runtime(original_pid)
            self._bound_environment()
            need(type(role) is str and role in ('original', 'intermediate', 'final', 'fork_syscall',
                 'exiting_child', 'gpgconf', 'gpg', 'gpgsm', 'g13'), 'gpgme_collector_snapshot_role')
            need(original_pid == self.p['original']['pid'] and type(original_pid) is int,
                 'gpgme_collector_snapshot_original')
            original = self.proc(original_pid)
            state = self.n['STATE']['process']
            need(type(state) is dict and all(type(state.get(k)) is int for k in
                    ('pid', 'start_ticks', 'gdb_pid', 'inferior'))
                 and all(state.get(k) == original[k] for k in ('pid', 'start_ticks'))
                 and state.get('gdb_pid') == os.getpid() and state.get('inferior') == 1,
                 'gpgme_collector_native_original_binding')
            stop = self._all_stop(original_pid, expected_thread)
            marker = self._window(readonly=readonly)
            namespaces = self._ns(os.getpid())
            need(self._ns(original_pid) == namespaces, 'gpgme_collector_original_namespaces')
            environment = self.current_environment(original_pid)
            configuration = self.config(original_pid)
            resources = self.resources(original_pid)
            regions = self._regions(original_pid)
            selected_map = [row for row in regions if row['path'] == self.p['library']['path']
                            and 'x' in row['perms']]
            need(len(selected_map) == 1, 'gpgme_collector_original_library_mapping')
            image = self.image_binding(original_pid, self.p['library'], selected_map[0]['start'])
            fds = self.fds(original_pid)
            need(self.proc(original_pid) == original and self._all_stop(original_pid, expected_thread) == stop
                 and self._window(readonly=readonly) == marker and self._ns(original_pid) == self._ns(os.getpid()) == namespaces
                 and self.current_environment(original_pid) == environment
                 and self.config(original_pid) == configuration and self.fds(original_pid) == fds,
                 'gpgme_collector_whole_boundary_changed')
            now = time.monotonic()
            need(now < self.p['operation']['deadline_monotonic'], 'gpgme_collector_original_deadline')
            context = dict(self.p['operation'], now=now, original=original, all_stop=True,
                phase='LOAD_CLOSED' if readonly else 'LOAD_OPEN',
                records_count=marker['native']['records_count'] if readonly else 0,
                metric_active=False, library_current_bound=True,
                environment_current_bound=True, configuration_isolated=True, resource_custody_bound=True)
            return dict(context=context, original=original, selected=stop, environment=environment,
                        configuration=configuration, resources=resources, image=image, fds=fds,
                        namespaces=namespaces, marker=marker, role=role,
                        runtime_attested=False, collector_scope='CURRENT_ALL_STOP_BOUNDARY_ONLY')
        except Exception as exc:
            self.refusal = str(exc) if type(exc) is RuntimeError else type(exc).__name__
            raise RuntimeError(self.refusal) from None

    def _bind_runtime(self, original_pid, *, require_witness=True):
        """Bind templates once from actual native birth and the same runtime."""
        need(type(self.runtime) is dict and integer(original_pid, 1), 'gpgme_collector_runtime_unbound')
        runtime_op = dict(operation_id=self.runtime.get('operation_id'), nonce=self.runtime.get('nonce'),
                          deadline_monotonic=self.runtime.get('operation_deadline_monotonic'))
        need(type(runtime_op['operation_id']) is str
             and re.fullmatch('[A-Za-z0-9_.-]{1,128}', runtime_op['operation_id'])
             and type(runtime_op['nonce']) is str and re.fullmatch('[0-9a-f]{32}', runtime_op['nonce'])
             and policy.positive(runtime_op['deadline_monotonic']), 'gpgme_collector_runtime_original_operation')
        if self.p['operation'] is None:
            self.p['operation'] = runtime_op
        need(self.p['operation'] == runtime_op and time.monotonic() < runtime_op['deadline_monotonic'],
             'gpgme_collector_runtime_clock_changed_or_expired')
        actual, _ = self._stat_process(original_pid)
        state = self.n['STATE']['process']
        need(type(state) is dict and all(type(state.get(k)) is int for k in
                ('pid', 'start_ticks', 'gdb_pid', 'inferior'))
             and all(state.get(k) == actual[k] for k in ('pid', 'start_ticks'))
             and actual['ppid'] == os.getpid() and state.get('gdb_pid') == os.getpid()
             and state.get('inferior') == 1 and self.n['CFG']['nonce'] == runtime_op['nonce'],
             'gpgme_collector_actual_native_launch_identity')
        if self.p['original'] is None:
            self.p['original'] = actual
            self.known[original_pid] = copy.deepcopy(actual)
        need(self.p['original'] == actual, 'gpgme_collector_original_template_rebound')
        observed_reaper, _ = self._stat_process(1)
        need(self._ns(1) == self._ns(original_pid) == self._ns(os.getpid())
             and self._stat_process(1)[0] == observed_reaper and observed_reaper['pid'] != original_pid,
             'gpgme_collector_namespace_reaper_identity')
        if self.p['reaper'] is None:
            self.p['reaper'] = observed_reaper
        need(self.p['reaper'] == observed_reaper, 'gpgme_collector_reaper_template_rebound')
        self.reaper = copy.deepcopy(observed_reaper)
        if require_witness and self.host_witness is None:
            self._bind_host_witness()


def _terminal(method):
    """Every public observation keeps the first refusal; no later rearming."""
    def guarded(self, *args, **kwargs):
        if self.refusal is not None:
            raise RuntimeError(self.refusal)
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            self.refusal = str(exc) if type(exc) is RuntimeError else type(exc).__name__
            raise RuntimeError(self.refusal) from None
    guarded.__name__, guarded.__doc__ = method.__name__, method.__doc__
    return guarded


for _method_name in ('proc', 'pending_fork_child', 'maps', 'pinned_file', 'image_binding', 'bind_current_environment', 'current_environment',
        'fds', 'fd', 'children', 'config', 'resources', 'dependencies', 'exec_observation',
        'exec_environment', 'exec_image', 'entry_address', 'verify_entry',
        'no_pipe_writer_or_descendant', 'snapshot', 'readonly_snapshot', 'readonly_caller'):
    setattr(BoundaryCollector, _method_name, _terminal(getattr(BoundaryCollector, _method_name)))
