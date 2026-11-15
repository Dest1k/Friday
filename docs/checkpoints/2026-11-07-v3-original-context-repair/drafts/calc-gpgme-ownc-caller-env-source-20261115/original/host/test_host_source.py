"""Pure host/schema controls; no runtime/backend/controller effect is called."""
from pathlib import Path
import copy
import importlib.util
import unittest


def source(name):
    path = Path(__file__).parent / name
    spec = importlib.util.spec_from_file_location('source_' + name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


host = source('ownc_root_controller.py')
supervisor = source('ownc_namespace_supervisor.py')


class PureHostSourceTests(unittest.TestCase):
    def data(self):
        namespaces = {key: key + ':[123]' for key in ('pid', 'mnt', 'net', 'user')}
        native = dict(pid=7, gdb_pid=6, start_ticks=70, inferior=1)
        inside = dict(namespace_pid=7, start_ticks=70, ppid=6, namespaces=namespaces,
                      boot_id='boot', executable_sha256='a' * 64)
        gdb_inside = dict(namespace_pid=6, start_ticks=60, ppid=2, namespaces=namespaces, boot_id='boot')
        common = dict(namespaces=namespaces, boot_id='boot', cgroup='0::/owned')
        target = dict(common, pid=107, ppid=106, nspid=[107, 7], start_ticks=70)
        gdb = dict(common, pid=106, ppid=102, nspid=[106, 6], start_ticks=60)
        sup = dict(common, pid=102, ppid=101, nspid=[102, 2], start_ticks=20)
        reaper = dict(common, pid=101, ppid=1, nspid=[101, 1], start_ticks=10)
        ready = dict(schema='frw.calc.office-ready.v1', operation_id='op', nonce='b' * 32,
                     scope='OWN_C_FIXTURE_ONLY', native_process=native, native_symbols=None,
                     office_identity=inside, gdb_identity=gdb_inside)
        plan = dict(operation_id='op', nonce='b' * 32, observer=dict(config=dict(target_sha256='a' * 64)))
        unit = dict(operation_id='op', nonce='b' * 32, unit='owned.service', invocation_id='c' * 32,
                    cgroup_path='/owned', namespace_supervisor_host_identity=sup)
        binding = dict(office=target, gdb=gdb, unit=unit['unit'], invocation_id=unit['invocation_id'],
                       native_process=native, native_symbols=None, cgroup=dict(path='/owned'), namespace_reaper=reaper)
        witness = dict(schema='frw.calc.gpgme-collector-host-witness.v1', operation_id='op', nonce='b' * 32,
                       deadline_monotonic=100., uid_projection={}, private_roots=[], cgroup={})
        release = dict(operation_id='op', nonce='b' * 32, stage='ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND',
                       native_process=native, native_symbols=None, host_binding=binding,
                       gpgme_collector_witness=witness)
        return plan, ready, [target, gdb, sup, reaper], unit, release

    def test_ready_maps_exact_owned_pid_birth_direct_gdb(self):
        plan, ready, processes, _, _ = self.data()
        self.assertEqual(host.map_ready(plan, ready, processes), tuple(processes[:2]))

    def test_ready_rejects_wrong_birth(self):
        plan, ready, processes, _, _ = self.data()
        processes[0]['start_ticks'] += 1
        with self.assertRaisesRegex(RuntimeError, '^ownc_host_target_pid_birth_mapping$'):
            host.map_ready(plan, ready, processes)

    def test_ready_rejects_wrong_gdb_parent(self):
        plan, ready, processes, _, _ = self.data()
        processes[0]['ppid'] = 999
        with self.assertRaisesRegex(RuntimeError, '^ownc_host_gdb_direct_parent_mapping$'):
            host.map_ready(plan, ready, processes)

    def test_ready_rejects_office_symbols(self):
        plan, ready, processes, _, _ = self.data()
        ready['native_symbols'] = {'outer': 1}
        with self.assertRaisesRegex(RuntimeError, '^ownc_ready_operation_or_fixture_scope$'):
            host.map_ready(plan, ready, processes)

    def test_ready_rejects_ambiguous_pid_mapping(self):
        plan, ready, processes, _, _ = self.data()
        processes.append(copy.deepcopy(processes[0]))
        with self.assertRaisesRegex(RuntimeError, '^ownc_host_target_pid_birth_mapping$'):
            host.map_ready(plan, ready, processes)

    def test_supervisor_rejects_python_pid2_as_reaper(self):
        plan, ready, processes, unit, release = self.data()
        release['host_binding']['namespace_reaper'] = processes[2]
        with self.assertRaisesRegex(RuntimeError, '^fixture_actual_namespace_pid1_reaper$'):
            supervisor.validate_release(release, unit, plan, ready['native_process'],
                ready['office_identity'], ready['gdb_identity'], 100.)

    def test_supervisor_rejects_changed_witness_clock(self):
        plan, ready, processes, unit, release = self.data()
        release['gpgme_collector_witness']['deadline_monotonic'] = 101.
        with self.assertRaisesRegex(RuntimeError, '^fixture_original_host_witness_before_target_continue$'):
            supervisor.validate_release(release, unit, plan, ready['native_process'],
                ready['office_identity'], ready['gdb_identity'], 100.)

    def test_budget_rejects_subtracted_controller_reserve(self):
        budget = dict(wall_seconds=240, cleanup_seconds=10, cpu_seconds=120,
                      memory_bytes=256 * 1024**2, startup_seconds=60, tasks_max=64)
        with self.assertRaisesRegex(RuntimeError, '^ownc_budget_outside_declared_caps$'):
            host.validate_budget(budget)

    def test_complete_environment_mismatch_refused(self):
        class Builder:
            def build_namespace(self, **kwargs):
                return ['bwrap', '--clearenv', '--setenv', 'HOME', '/private', '--', *kwargs['command']]
        plan = dict(source_refs=dict(supervisor=dict(path='/source/supervisor.py')),
                    readonly_roots=['/source'], binding_root='/binding',
                    target_environment={'HOME': '/private', 'DEBUGINFOD_URLS': '', 'UNDECLARED': 'no'})
        with self.assertRaisesRegex(RuntimeError, '^ownc_builder_complete_environment_mismatch$'):
            host.namespace_argv(plan, Builder(), work=Path('/work'), job_ref={})

    def test_confirmed_native_first_error_authorizes_finally_wait(self):
        trace = dict(kind='OWN_POPEN_FIXTURE_ONLY', nonce='b' * 32,
                     status='REFUSED', error='gpgme_expected_guard')
        self.assertTrue(supervisor.native_refusal_trace(trace, 'b' * 32))

    def test_supervisor_only_fault_or_unknown_trace_cannot_delay_cleanup(self):
        trace = dict(kind='OWN_POPEN_FIXTURE_ONLY', nonce='b' * 32,
                     status='READY_UNRELEASED', error=None)
        self.assertFalse(supervisor.native_refusal_trace(trace, 'b' * 32))
        self.assertFalse(supervisor.native_refusal_trace(None, 'b' * 32))
        trace.update(status='REFUSED', error='stale_guard')
        self.assertFalse(supervisor.native_refusal_trace(trace, 'c' * 32))


if __name__ == '__main__':
    unittest.main()
