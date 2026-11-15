"""Pure schema/parser and mocked-OS collector controls. No GDB/ELF execution.

valid_pins() is a synthetic well-typed fixture, never a process observation.
Run python3 -B collector_tests.py; the report labels runtime evidence false.
"""
import copy
import hashlib
import json
import os
import stat
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gpgme_boundary_collector as c


def valid_pins():
    host = dict(dev_major=8, dev_minor=1, ino=100, size=4096, mtime_ns=1,
                ctime_ns=1, mode=stat.S_IFREG | 0o644, uid=0, nlink=1)
    library = dict(path=c.policy.LIBRARY_PATH, sha256=c.policy.LIBRARY_SHA256,
                   build_id=c.policy.BUILD_ID, host_stamp=host)
    libc = dict(path='/usr/lib/x86_64-linux-gnu/libc.so.6',
                sha256=c.ENV_SOURCE['libc_sha256'], build_id='aa' * 20,
                host_stamp=dict(host, ino=101))
    roots = []
    for number, path in enumerate(sorted({'/tmp/friday-metric-work'} | {
            value for key, value in c.policy.ISOLATED.items() if key in
            ('HOME', 'TMPDIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR')})):
        roots.append(dict(path=path, stamp=dict(host, ino=200 + number,
                          mode=stat.S_IFDIR | 0o700, nlink=2, uid=0)))
    uid_map = b'0 1000 1\n'
    return dict(operation=dict(operation_id='PURE_SCHEMA_ONLY', nonce='ab' * 16,
                               deadline_monotonic=1000000.0),
        original=dict(pid=123, ppid=122, start_ticks=100),
        reaper=dict(pid=1, ppid=0, start_ticks=90), library=library, libc=libc,
        environment=dict(c.policy.ISOLATED), cwd='/tmp/friday-metric-work',
        absent_paths=['/tmp/friday-metric-work/tmp/.gnupg', '/etc/gnupg'], private_roots=roots,
        cgroup=dict(membership_sha256=c.digest(b'0::/\n'), mount_path='/sys/fs/cgroup',
            directory_stamp=dict(host, ino=300, mode=stat.S_IFDIR | 0o755, nlink=2),
            cpu_max='100000 100000\n', memory_max='2147483648\n', pids_max='256\n',
            cpu_usage_origin_usec=0),
        uid_projection=dict(uid_map_sha256=c.digest(uid_map), root_host_uid_map_sha256=c.digest(uid_map),
            overflowuid=65534, collector_userns=dict(dev=4, ino=4026533000),
            host_userns=dict(dev=4, ino=4026531837)),
        dependencies={'original': [copy.deepcopy(library), copy.deepcopy(libc)],
                      'gpgconf': [copy.deepcopy(libc)]})


def elf_fixture(*, total=8192, elf_type=3, flags=5, entry=0x120, extra_note=False):
    raw = bytearray(total)
    ident = b'\x7fELF\x02\x01\x01' + b'\0' * 9
    struct.pack_into('<16sHHIQQQIHHHHHH', raw, 0, ident, elf_type, 62, 1,
                     entry, 64, 0, 0, 64, 56, 2 + int(extra_note), 0, 0, 0)
    struct.pack_into('<IIQQQQQQ', raw, 64, 1, flags, 0, 0, 0, total, total, 4096)
    note = struct.pack('<III', 4, 20, 3) + b'GNU\0' + bytes.fromhex('aa' * 20)
    raw[256:256 + len(note)] = note
    struct.pack_into('<IIQQQQQQ', raw, 120, 4, 4, 256, 256, 256, len(note), len(note), 4)
    if extra_note:
        struct.pack_into('<IIQQQQQQ', raw, 176, 4, 4, 256, 256, 256, len(note), len(note), 4)
    return bytes(raw)


def stat_fixture(pid=123, ppid=122, birth=100, state='t'):
    fields = [state, str(ppid)] + ['0'] * 20
    fields[11], fields[12], fields[19], fields[20], fields[21] = '2', '3', str(birth), '4096', '1'
    return ('%d (name with ) and spaces) %s\n' % (pid, ' '.join(fields))).encode()


class PureControls(unittest.TestCase):
    def test_valid_pins(self):
        self.assertIs(c.validate_pins(valid_pins())['operation']['deadline_monotonic'].__class__, float)

    def test_source_templates_without_future_facts(self):
        pins = valid_pins()
        for key in ('operation', 'original', 'reaper', 'private_roots', 'uid_projection', 'cgroup'):
            pins[key] = None
        self.assertEqual(c.validate_pins(pins), pins)

    def test_pin_unknown_field(self):
        pins = valid_pins()
        pins['runtime_available'] = True
        with self.assertRaisesRegex(RuntimeError, 'pins_schema'):
            c.validate_pins(pins)

    def test_bool_pid_refused(self):
        pins = valid_pins()
        pins['original']['pid'] = True
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_bool_stamp_refused(self):
        pins = valid_pins()
        pins['library']['host_stamp']['uid'] = False
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_host_owner_must_be_root(self):
        pins = valid_pins()
        pins['library']['host_stamp']['uid'] = 65534
        with self.assertRaisesRegex(RuntimeError, 'host_root_file'):
            c.validate_pins(pins)

    def test_host_file_hardlink_refused(self):
        pins = valid_pins()
        pins['library']['host_stamp']['nlink'] = 2
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_host_file_world_writable_refused(self):
        pins = valid_pins()
        pins['library']['host_stamp']['mode'] |= 2
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_environment_override_refused(self):
        pins = valid_pins()
        pins['environment']['GNUPGHOME'] = pins['cwd']
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_config_default_exclusion_required(self):
        pins = valid_pins()
        pins['absent_paths'].remove('/etc/gnupg')
        with self.assertRaisesRegex(RuntimeError, 'config_exclusions'):
            c.validate_pins(pins)

    def test_private_root_symlink_schema_refused(self):
        pins = valid_pins()
        pins['private_roots'][0]['stamp']['mode'] = stat.S_IFLNK | 0o700
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_private_environment_root_missing(self):
        pins = valid_pins()
        pins['private_roots'] = pins['private_roots'][:-1]
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_cgroup_cpu_origin_bool_refused(self):
        pins = valid_pins()
        pins['cgroup']['cpu_usage_origin_usec'] = False
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_cgroup_memory_budget_expansion_refused(self):
        pins = valid_pins()
        pins['cgroup']['memory_max'] = '2147483649\n'
        with self.assertRaises(RuntimeError):
            c.validate_pins(pins)

    def test_dependency_alias_schema_refused(self):
        pins = valid_pins()
        pins['dependencies']['original'].append(pins['dependencies']['original'][0])
        with self.assertRaisesRegex(RuntimeError, 'dependency_pins'):
            c.validate_pins(pins)

    def test_uid_host_root_unmapped_actual_overflow(self):
        pins = valid_pins()
        proof = c.project_host_root(b'0 1000 1\n', 65534, pins['uid_projection'],
                                    pins['uid_projection']['collector_userns'])
        self.assertEqual(proof['actual_uid'], 65534)
        self.assertEqual(proof['source'], 'ACTUAL_UNMAPPED_HOST_ROOT_OVERFLOW')

    def test_uid_host_root_mapped_nonzero(self):
        witness = valid_pins()['uid_projection']
        raw = b'5 0 1\n0 1000 1\n'
        witness['uid_map_sha256'] = witness['root_host_uid_map_sha256'] = c.digest(raw)
        self.assertEqual(c.project_host_root(raw, 65534, witness, witness['collector_userns'])['actual_uid'], 5)

    def test_uid_no_blind_overflow_guess(self):
        witness = valid_pins()['uid_projection']
        with self.assertRaisesRegex(RuntimeError, 'uid_map_or_namespace'):
            c.project_host_root(b'0 1000 1\n', 65535, witness, witness['collector_userns'])

    def test_uid_host_witness_mismatch(self):
        witness = valid_pins()['uid_projection']
        witness['root_host_uid_map_sha256'] = '00' * 32
        with self.assertRaises(RuntimeError):
            c.project_host_root(b'0 1000 1\n', 65534, witness, witness['collector_userns'])

    def test_uid_namespace_changed(self):
        witness = valid_pins()['uid_projection']
        with self.assertRaises(RuntimeError):
            c.project_host_root(b'0 1000 1\n', 65534, witness, dict(dev=4, ino=99))

    def test_uid_overflow_alias_refused(self):
        witness = valid_pins()['uid_projection']
        raw = b'65534 1000 1\n'
        witness['uid_map_sha256'] = witness['root_host_uid_map_sha256'] = c.digest(raw)
        with self.assertRaisesRegex(RuntimeError, 'overflow_aliases'):
            c.project_host_root(raw, 65534, witness, witness['collector_userns'])

    def test_uid_overlap_refused(self):
        for raw in (b'0 1000 2\n1 2000 1\n', b'0 1000 2\n4 1001 1\n'):
            with self.assertRaisesRegex(RuntimeError, 'uid_map_overlap'):
                c.parse_uid_map(raw)

    def test_uid_full_host_identity_supported(self):
        witness = valid_pins()['uid_projection']
        raw = b'0 0 4294967295\n'
        witness['collector_userns'] = witness['host_userns']
        witness['uid_map_sha256'] = witness['root_host_uid_map_sha256'] = c.digest(raw)
        self.assertEqual(c.project_host_root(raw, 65534, witness, witness['host_userns'])['actual_uid'], 0)

    def test_uid_claimed_host_ns_nonidentity_refused(self):
        witness = valid_pins()['uid_projection']
        witness['collector_userns'] = witness['host_userns']
        with self.assertRaisesRegex(RuntimeError, 'host_userns_identity'):
            c.project_host_root(b'0 1000 1\n', 65534, witness, witness['host_userns'])

    def test_stat_comm_parentheses_and_birth(self):
        identity, usage = c.parse_proc_stat(stat_fixture(), 123)
        self.assertEqual(identity, dict(pid=123, ppid=122, start_ticks=100))
        self.assertEqual(usage['utime_ticks'] + usage['stime_ticks'], 5)

    def test_stat_wrong_pid_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'stat_pid'):
            c.parse_proc_stat(stat_fixture(), 124)

    def test_stat_bool_pid_refused(self):
        with self.assertRaises(RuntimeError):
            c.parse_proc_stat(stat_fixture(), True)

    def test_environment_parse(self):
        self.assertEqual(c.parse_environment(b'HOME=/tmp\0LANG=C.UTF-8\0'),
                         dict(HOME='/tmp', LANG='C.UTF-8'))

    def test_environment_duplicates_and_bad_keys_refused(self):
        for raw in (b'A=1\0A=2\0', b'=a\0', b'A-1=a\0', b'A=unterminated', b'A=\xff\0'):
            with self.assertRaises(RuntimeError):
                c.parse_environment(raw)

    def test_generic_ELF_over_legacy_2MiB(self):
        raw = elf_fixture(total=2191360)
        result = c.generic_elf_metadata(raw)
        self.assertEqual(result['build_id'], 'aa' * 20)
        self.assertEqual(result['entry'], 0x120)
        with self.assertRaises(RuntimeError):
            c.mapper.elf_metadata(raw)

    def test_generic_ELF_duplicate_build_id_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'metadata_ambiguity'):
            c.generic_elf_metadata(elf_fixture(extra_note=True))

    def test_generic_ELF_load_permission_refused(self):
        with self.assertRaises(RuntimeError):
            c.generic_elf_metadata(elf_fixture(flags=8))

    def test_generic_current_image_join(self):
        raw = elf_fixture()
        host = dict(valid_pins()['library']['host_stamp'], size=len(raw))
        actual = dict(host, uid=65534)
        image = dict(path='/usr/lib/example.so', sha256=c.digest(raw), build_id='aa' * 20, host_stamp=host)
        maps = b'100000-102000 r-xp 00000000 08:01 100 /usr/lib/example.so\n'
        result = c.generic_image_join(maps, maps, actual, host, raw, image, 0x100120)
        self.assertEqual(result['load_bias'], 0x100000)
        self.assertEqual(result['relative_pc'], 0x120)

    def test_generic_wrong_mapping_inode_refused(self):
        raw = elf_fixture()
        host = dict(valid_pins()['library']['host_stamp'], size=len(raw))
        image = dict(path='/usr/lib/example.so', sha256=c.digest(raw), build_id='aa' * 20, host_stamp=host)
        maps = b'100000-102000 r-xp 00000000 08:01 101 /usr/lib/example.so\n'
        with self.assertRaisesRegex(RuntimeError, 'mapping_alias'):
            c.generic_image_join(maps, maps, host, host, raw, image, 0x100120)

    def test_generic_mapped_write_escalation_refused(self):
        raw = elf_fixture()
        host = dict(valid_pins()['library']['host_stamp'], size=len(raw))
        image = dict(path='/usr/lib/example.so', sha256=c.digest(raw), build_id='aa' * 20, host_stamp=host)
        maps = b'100000-102000 rwxp 00000000 08:01 100 /usr/lib/example.so\n'
        with self.assertRaisesRegex(RuntimeError, 'mapping_not_PT_LOAD'):
            c.generic_image_join(maps, maps, host, host, raw, image, 0x100120)

    def test_generic_noncanonical_path_refused(self):
        self.assertFalse(c.canonical('/usr/lib/../example.so'))
        self.assertFalse(c.canonical('/usr//example.so'))
        self.assertFalse(c.canonical('/usr/lib/example.so\0'))

    def test_short_helper_pin_resolves_only_exact_dependency(self):
        pins = valid_pins()
        native = dict(phase=lambda: None, get_active=lambda: None)
        collector = c.BoundaryCollector(None, native, pins)
        image = pins['libc']
        short = dict(path=image['path'], sha256=image['sha256'], dev=os.makedev(8, 1), ino=101)
        self.assertEqual(collector._resolve_image(short), image)
        short['ino'] = 999
        with self.assertRaisesRegex(RuntimeError, 'short_image_pin'):
            collector._resolve_image(short)

    def test_terminal_snapshot_error_retains_first_reason(self):
        collector = c.BoundaryCollector(None, dict(phase=lambda: None, get_active=lambda: None), valid_pins())
        with self.assertRaisesRegex(RuntimeError, 'first_boundary_refusal'):
            with patch.object(collector, '_bind_runtime', side_effect=RuntimeError('first_boundary_refusal')):
                collector.snapshot(123)
        with self.assertRaisesRegex(RuntimeError, 'first_boundary_refusal'):
            collector.snapshot(124)

    def test_actual_read_bound_and_same_fd_cas_control(self):
        pins = valid_pins()
        collector = c.BoundaryCollector(None, dict(phase=lambda: None, get_active=lambda: None), pins)
        value = fake_stat(pins['library']['host_stamp'])
        with patch.object(c.os, 'open', return_value=17), patch.object(c.os, 'fstat', return_value=value), \
                patch.object(c.os, 'close') as close, patch.object(c.os, 'read', side_effect=[b'abc', b'']):
            self.assertEqual(collector._read('/proc/123/maps', 10), b'abc')
            close.assert_called_once_with(17)

    def test_actual_read_over_bound_refused_and_fd_closed(self):
        pins = valid_pins()
        collector = c.BoundaryCollector(None, dict(phase=lambda: None, get_active=lambda: None), pins)
        with patch.object(c.os, 'open', return_value=17), \
                patch.object(c.os, 'fstat', return_value=fake_stat(pins['library']['host_stamp'])), \
                patch.object(c.os, 'close') as close, patch.object(c.os, 'read', return_value=b'abcdef'):
            with self.assertRaisesRegex(RuntimeError, 'read_over_bound'):
                collector._read('/proc/123/maps', 5)
            close.assert_called_once_with(17)

    def test_same_fd_namespace_and_host_stamps_preserved(self):
        collector, image, actual = file_collector_fixture()
        with patch.object(collector, '_secure_open', side_effect=[17, 18]), \
                patch.object(c.os, 'fstat', return_value=fake_stat(actual)), \
                patch.object(c.os, 'read', side_effect=[elf_fixture(), b'']), patch.object(c.os, 'close'):
            raw, before, after, proof = collector._file(image)
        self.assertEqual(before['uid'], 65534)
        self.assertEqual(image['host_stamp']['uid'], 0)
        self.assertEqual(before, after)
        self.assertEqual(c.digest(raw), image['sha256'])
        self.assertEqual(proof['actual_uid'], 65534)

    def test_current_canonical_path_inode_drift_refused(self):
        collector, image, actual = file_collector_fixture()
        stamps = [fake_stat(actual), fake_stat(actual), fake_stat(dict(actual, ino=999))]
        with patch.object(collector, '_secure_open', side_effect=[17, 18]), \
                patch.object(c.os, 'fstat', side_effect=stamps), \
                patch.object(c.os, 'read', side_effect=[elf_fixture(), b'']), patch.object(c.os, 'close'):
            with self.assertRaisesRegex(RuntimeError, 'same_fd_or_current_path'):
                collector._file(image)

    def test_namespace_uid_does_not_blindly_mean_root(self):
        collector, image, actual = file_collector_fixture()
        actual['uid'] = 0
        with patch.object(collector, '_secure_open', return_value=17), \
                patch.object(c.os, 'fstat', return_value=fake_stat(actual)), patch.object(c.os, 'close'):
            with self.assertRaisesRegex(RuntimeError, 'pin_or_projection'):
                collector._file(image)

    def test_all_stop_compares_gdb_threads_with_kernel_tasks(self):
        collector, gdb = stopped_collector_fixture()
        with stopped_kernel(collector):
            proof = collector._all_stop(123, [123, 123, 0])
        self.assertEqual(proof['selected'], [123, 123, 0])
        self.assertEqual(proof['threads'][0]['start_ticks'], 100)

    def test_all_stop_missing_kernel_thread_refused(self):
        collector, gdb = stopped_collector_fixture()
        with stopped_kernel(collector, tasks=['123', '124']):
            with self.assertRaisesRegex(RuntimeError, 'missing_or_duplicate_thread'):
                collector._all_stop(123)

    def test_all_stop_running_gdb_thread_refused(self):
        collector, gdb = stopped_collector_fixture()
        gdb.thread.stopped = False
        with stopped_kernel(collector):
            with self.assertRaisesRegex(RuntimeError, 'selected_thread'):
                collector._all_stop(123)

    def test_all_stop_running_kernel_thread_refused(self):
        collector, gdb = stopped_collector_fixture()
        with stopped_kernel(collector, state='R'):
            with self.assertRaisesRegex(RuntimeError, 'kernel_thread_not_stopped'):
                collector._all_stop(123)

    def test_effective_environment_reads_explicit_original_inferior(self):
        collector, original, child = environment_fixture()
        value = collector.current_environment(123)
        self.assertEqual(value, collector.p['environment'])
        self.assertGreater(original.memory_reads, 0)
        self.assertEqual(child.memory_reads, 0)

    def test_effective_environment_vector_change_refused(self):
        collector, original, child = environment_fixture(change_vector=True)
        with self.assertRaisesRegex(RuntimeError, 'effective_environment_changed'):
            collector.current_environment(123)

    def test_effective_environment_override_refused(self):
        collector, original, child = environment_fixture(extra_env={'GNUPGHOME': '/home/private'})
        with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
            collector.current_environment(123)

    def test_effective_environment_bad_libc_instruction_refused(self):
        collector, original, child = environment_fixture()
        original.memory[0x100000 + c.ENV_SOURCE['load_offset']] = 0
        with self.assertRaisesRegex(RuntimeError, 'libc_environ_instruction'):
            collector.current_environment(123)

    def test_host_release_joins_real_namespace_birth_unit_invocation(self):
        collector, release, unit = release_fixture()
        with release_kernel(collector, release, unit):
            self.assertEqual(collector._release()[0], release)

    def test_host_release_original_birth_mismatch_refused(self):
        collector, release, unit = release_fixture()
        release['host_binding']['office']['start_ticks'] += 1
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'host_process_join'):
                collector._release()

    def test_host_release_unit_invocation_mismatch_refused(self):
        collector, release, unit = release_fixture()
        unit['invocation_id'] = 'ff' * 16
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'unit_or_invocation'):
                collector._release()

    def test_host_release_wrong_namespace_refused(self):
        collector, release, unit = release_fixture()
        release['host_binding']['gdb']['namespaces']['user'] = 'user:[9999]'
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'host_process_join'):
                collector._release()

    def test_host_release_supervisor_is_not_guessed_reaper(self):
        collector, release, unit = release_fixture()
        release['host_binding']['namespace_reaper'] = unit['namespace_supervisor_host_identity']
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'reaper_join'):
                collector._release()

    def test_host_release_cgroup_mismatch_refused(self):
        collector, release, unit = release_fixture()
        unit['cgroup_path'] += '-other'
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'host_cgroup_join'):
                collector._release()

    def test_host_release_accepted_hash_change_refused(self):
        collector, release, unit = release_fixture()
        collector._release_digest, collector._unit_digest = 'changed', 'unit'
        with release_kernel(collector, release, unit):
            with self.assertRaisesRegex(RuntimeError, 'accepted_release_changed'):
                collector._release()


def fake_stat(value):
    return SimpleNamespace(st_dev=os.makedev(value['dev_major'], value['dev_minor']),
        st_ino=value['ino'], st_size=value['size'], st_mtime_ns=value['mtime_ns'],
        st_ctime_ns=value['ctime_ns'], st_mode=value['mode'], st_uid=value['uid'],
        st_nlink=value['nlink'], st_rdev=0)


def release_fixture():
    pins = valid_pins()
    pins['reaper']['start_ticks'] = 80
    native_id = dict(pid=123, start_ticks=100, gdb_pid=122, inferior=1)
    symbols = dict(outer=1, native=2, native_return=3)
    native = dict(phase=lambda: None, get_active=lambda: None,
                  STATE=dict(process=native_id, symbols=symbols))
    collector = c.BoundaryCollector(None, native, pins)
    namespaces = {name: name + ':[800]' for name in ('pid', 'mnt', 'net', 'user')}
    def host(pid, namespace_pid, birth, ppid):
        return dict(pid=pid, ppid=ppid, start_ticks=birth, nspid=[pid, namespace_pid],
                    namespaces=copy.deepcopy(namespaces), boot_id='pure-boot', cgroup='0::/pure/isolated')
    unit = dict(operation_id=pins['operation']['operation_id'], nonce=pins['operation']['nonce'],
        stage='ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED', unit='pure.service', invocation_id='cd' * 16,
        cgroup_path='/pure/isolated', namespace_supervisor_host_identity=host(502, 2, 90, 501))
    binding = dict(unit=unit['unit'], invocation_id=unit['invocation_id'],
        cgroup=dict(path='/pure/isolated', inode=999), office=host(600, 123, 100, 601),
        gdb=host(601, 122, 101, 502), namespace_reaper=host(501, 1, 80, 500),
        native_process=copy.deepcopy(native_id), native_symbols=copy.deepcopy(symbols))
    release = dict(operation_id=unit['operation_id'], nonce=unit['nonce'],
        stage='ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND', native_process=copy.deepcopy(native_id),
        native_symbols=copy.deepcopy(symbols), host_binding=binding)
    return collector, release, unit


class release_kernel:
    def __init__(self, collector, release, unit):
        self.collector, self.release, self.unit = collector, release, unit
        self.patches = []
    def __enter__(self):
        def json_file(path):
            return (self.release, 'release') if path.endswith('/office-release.json') else (self.unit, 'unit')
        def process(pid):
            return (dict(pid=pid, ppid=2, start_ticks=101 if pid == 122 else 90), {})
        self.patches = [patch.object(c.os, 'getpid', return_value=122),
            patch.object(c.os, 'readlink', side_effect=lambda path: path.rsplit('/', 1)[-1] + ':[800]'),
            patch.object(self.collector, '_json_file', side_effect=json_file),
            patch.object(self.collector, '_stat_process', side_effect=process),
            patch.object(self.collector, '_read', return_value=b'pure-boot\n')]
        for item in self.patches:
            item.__enter__()
    def __exit__(self, *args):
        for item in reversed(self.patches):
            item.__exit__(*args)


def file_collector_fixture():
    pins = valid_pins()
    collector = c.BoundaryCollector(None, dict(phase=lambda: None, get_active=lambda: None), pins)
    image = dict(path='/usr/lib/example.so', sha256=c.digest(elf_fixture()),
        build_id='aa' * 20, host_stamp=dict(pins['library']['host_stamp'], size=8192))
    actual = dict(image['host_stamp'], uid=65534)
    collector._projection = lambda: dict(actual_uid=65534, source='PURE_SYNTHETIC_TEST_ONLY')
    return collector, image, actual


class FakeThread:
    def __init__(self, pid):
        self.ptid, self.stopped = (pid, pid, 0), True
    def is_valid(self):
        return True
    def is_stopped(self):
        return self.stopped


class FakeInferior:
    def __init__(self, pid, num=1):
        self.pid, self.num, self.thread = pid, num, FakeThread(pid)
        self.memory, self.memory_reads, self.read_hook = {}, 0, None
    def is_valid(self):
        return True
    def threads(self):
        return [self.thread]
    def read_memory(self, address, count):
        self.memory_reads += 1
        if self.read_hook is not None:
            value = self.read_hook(address, count)
            if value is not None:
                return value
        return bytes(self.memory.get(address + offset, 0) for offset in range(count))


class FakeGdb:
    def __init__(self, original, child=None):
        self.original, self.child = original, child
        self.thread = (child or original).thread
    def inferiors(self):
        return [self.original] + ([] if self.child is None else [self.child])
    def selected_inferior(self):
        return self.child or self.original
    def selected_thread(self):
        return self.thread
    def parameter(self, name):
        return False


def stopped_collector_fixture():
    gdb = FakeGdb(FakeInferior(123))
    collector = c.BoundaryCollector(gdb, dict(phase=lambda: None, get_active=lambda: None), valid_pins())
    collector.proc = lambda pid: dict(pid=pid, ppid=122, start_ticks=100)
    return collector, gdb


class stopped_kernel:
    def __init__(self, collector, tasks=None, state='t'):
        self.collector, self.tasks, self.state = collector, tasks or ['123'], state
    def __enter__(self):
        self.read = patch.object(self.collector, '_read', return_value=stat_fixture(state=self.state))
        self.listdir = patch.object(c.os, 'listdir', return_value=self.tasks)
        self.read.__enter__()
        self.listdir.__enter__()
    def __exit__(self, *args):
        self.listdir.__exit__(*args)
        self.read.__exit__(*args)


def environment_fixture(*, change_vector=False, extra_env=None):
    original, child = FakeInferior(123), FakeInferior(124, 2)
    collector = c.BoundaryCollector(FakeGdb(original, child),
        dict(phase=lambda: None, get_active=lambda: None), valid_pins())
    collector.known[124] = dict(pid=124, ppid=123, start_ticks=110)
    collector.proc = lambda pid: dict(pid=pid, ppid=122 if pid == 123 else 123, start_ticks=100 if pid == 123 else 110)
    collector._all_stop = lambda *args: {'selected': [124, 124, 0], 'pure_test_only': True}
    base, vector = 0x100000, 0x700000
    path = collector.p['libc']['path']
    regions = [dict(start=base, end=base + c.ENV_SOURCE['zero_fill_start'], perms='r-xp', path=path),
        dict(start=base + c.ENV_SOURCE['zero_fill_start'], end=base + 0x221000, perms='rw-p', path=''),
        dict(start=vector, end=vector + 0x10000, perms='rw-p', path='')]
    collector._regions = lambda pid: copy.deepcopy(regions)
    collector.image_binding = lambda *args: dict(join=dict(load_bias=base))

    def put(address, raw):
        original.memory.update({address + offset: value for offset, value in enumerate(raw)})
    for prefix in ('load', 'dereference', 'call'):
        put(base + c.ENV_SOURCE[prefix + '_offset'], bytes.fromhex(c.ENV_SOURCE[prefix + '_bytes']))
    put(base + c.ENV_SOURCE['got_offset'], (base + c.ENV_SOURCE['storage_offset']).to_bytes(8, 'little'))
    storage = base + c.ENV_SOURCE['storage_offset']
    put(storage, vector.to_bytes(8, 'little'))
    env = dict(collector.p['environment'], **(extra_env or {}))
    for index, (key, value) in enumerate(sorted(env.items())):
        address = vector + 0x1000 + index * 512
        put(vector + index * 8, address.to_bytes(8, 'little'))
        put(vector + 0x400 + index * 8, address.to_bytes(8, 'little'))
        put(address, (key + '=' + value).encode() + b'\0')
    if change_vector:
        count = [0]
        def hook(address, amount):
            if address == storage:
                count[0] += 1
                return (vector if count[0] == 1 else vector + 0x400).to_bytes(8, 'little')
        original.read_hook = hook
    return collector, original, child


def run_controls():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PureControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return dict(schema='frw.calc.gpgme-collector-pure-controls.v1', tests=result.testsRun,
                failures=len(result.failures), errors=len(result.errors), passed=result.wasSuccessful(),
                synthetic_only=True, runtime_attested=False, gdb_started=False,
                target_elf_executed=False, target_processes_started=False)


if __name__ == '__main__':
    report = run_controls()
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report['passed'] else 1)
