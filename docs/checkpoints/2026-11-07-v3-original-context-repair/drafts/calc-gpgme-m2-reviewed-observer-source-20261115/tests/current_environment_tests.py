"""Inert synthetic source controls: no GDB, target ELF or process execution."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-COMPLETE-OBSERVER-SOURCE-20261115/candidate/outer/deps')
sys.path[:0] = [str(HERE), str(ORIGINAL)]
import gpgme_boundary_collector as c
import collector_tests as baseline


def encoded(env):
    return b'\0'.join((k + '=' + v).encode() for k, v in sorted(env.items())) + b'\0'


def put_environment(inferior, env):
    vector = 0x700000
    for address in list(inferior.memory):
        if vector <= address < vector + 0x10000:
            del inferior.memory[address]
    for index, (key, value) in enumerate(sorted(env.items())):
        address = vector + 0x1000 + index * 512
        raw = (key + '=' + value).encode() + b'\0'
        inferior.memory.update({vector + index * 8 + n: v for n, v in
                                enumerate(address.to_bytes(8, 'little'))})
        inferior.memory.update({address + n: v for n, v in enumerate(raw)})


def fixture(*, current=None, startup=None, pins=None, change_vector=False, selected_original=True):
    collector, original, child = baseline.environment_fixture(change_vector=change_vector)
    initial = dict(collector.p['environment']) if startup is None else dict(startup)
    collector.p['environment'] = dict(initial if pins is None else pins)
    actual = dict(initial if current is None else current)
    put_environment(original, actual)
    # Two actual kernel reads during binding. No real procfs or target reads.
    collector._read = lambda path, limit: encoded(initial) if path == '/proc/123/environ' else encoded(actual)
    if selected_original:
        collector.g.child, collector.g.thread = None, original.thread
    return collector, original, child, initial, actual


def snapshot_fixture(collector):
    collector._bind_runtime = lambda *args: None
    collector.n['STATE'] = dict(process=dict(pid=123, start_ticks=100, gdb_pid=os.getpid(), inferior=1))
    collector._window = lambda: dict(mock_marker=True)
    collector._ns = lambda pid: dict(mock_namespaces=True)
    collector.config = lambda pid: dict(mock_configuration=True)
    collector.resources = lambda pid: dict(mock_resources=True)
    collector.fds = lambda pid: {0: dict(mock_descriptor=True)}
    regions = collector._regions(123)
    regions.append(dict(start=0x500000, end=0x501000, perms='r-xp', path=collector.p['library']['path']))
    collector._regions = lambda pid: copy.deepcopy(regions)


class CurrentEnvironmentControls(unittest.TestCase):
    def test_exact_immutable_paper_font15_source(self):
        tree = ast.parse((ORIGINAL / 'paper_helper_gdb.py').read_text())
        declaration = next(n for n in tree.body if isinstance(n, ast.Assign) and
                           any(isinstance(t, ast.Name) and t.id == 'FONT_ENV_KEYS' for t in n.targets))
        self.assertEqual(c.FONT_ENV_KEYS, tuple(k.decode() for k in ast.literal_eval(declaration.value)))
        self.assertEqual(len(c.FONT_ENV_KEYS), 15)

    def test_unbound_current_never_reads_or_implicitly_freezes(self):
        collector, original, child, initial, actual = fixture()
        with self.assertRaisesRegex(RuntimeError, 'current_environment_unbound'):
            collector.current_environment(123)
        self.assertEqual(original.memory_reads, 0)
        self.assertIsNone(collector._current_environment)
        with self.assertRaisesRegex(RuntimeError, 'current_environment_unbound'):
            collector.bind_current_environment(123)

    def test_unbound_whole_snapshot_terminally_refuses(self):
        collector, original, child, initial, actual = fixture()
        snapshot_fixture(collector)
        with self.assertRaisesRegex(RuntimeError, 'current_environment_unbound'):
            collector.snapshot(123)
        self.assertEqual(original.memory_reads, 0)
        self.assertIsNone(collector._current_environment)
        with self.assertRaisesRegex(RuntimeError, 'current_environment_unbound'):
            collector.bind_current_environment(123)

    def test_bind_accepts_arbitrary_nonfont_add_change_and_removal(self):
        startup = dict(c.policy.ISOLATED, ARBITRARY_APPLICATION_INPUT='startup', REMOVED_INPUT='startup')
        actual = dict(c.policy.ISOLATED, ARBITRARY_APPLICATION_INPUT='current', UNLISTED_NEW_INPUT='runtime')
        collector, original, child, initial, current = fixture(current=actual, startup=startup)
        self.assertEqual(collector.bind_current_environment(123), actual)
        self.assertEqual(collector.current_environment(123), actual)
        self.assertEqual(collector.p['environment'], startup)
        self.assertGreater(original.memory_reads, 0)
        self.assertEqual(child.memory_reads, 0)

    def test_bound_result_copy_cannot_rewrite_complete_freeze(self):
        collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, ANY_INPUT='runtime'))
        returned = collector.bind_current_environment(123)
        returned['ANY_INPUT'] = 'caller mutation'
        returned['HOME'] = '/outside'
        self.assertIs(type(collector._current_environment), tuple)
        self.assertEqual(collector.current_environment(123), actual)

    def test_rebind_refused_without_replacing_first_snapshot(self):
        collector, original, child, initial, actual = fixture()
        collector.bind_current_environment(123)
        frozen = collector._current_environment
        with self.assertRaisesRegex(RuntimeError, 'already_bound'):
            collector.bind_current_environment(123)
        self.assertIs(collector._current_environment, frozen)
        with self.assertRaisesRegex(RuntimeError, 'already_bound'):
            collector.current_environment(123)

    def test_nonoriginal_binding_refused_before_memory(self):
        collector, original, child, initial, actual = fixture()
        with self.assertRaisesRegex(RuntimeError, 'original_binding'):
            collector.bind_current_environment(124)
        self.assertEqual(original.memory_reads + child.memory_reads, 0)

    def test_original_not_selected_binding_refused(self):
        collector, original, child, initial, actual = fixture(selected_original=False)
        with self.assertRaisesRegex(RuntimeError, 'original_binding'):
            collector.bind_current_environment(123)
        self.assertEqual(original.memory_reads + child.memory_reads, 0)

    def test_original_identity_drift_refused(self):
        collector, original, child, initial, actual = fixture()
        collector.proc = lambda pid: dict(pid=123, ppid=122, start_ticks=999)
        with self.assertRaisesRegex(RuntimeError, 'original_binding'):
            collector.bind_current_environment(123)

    def test_current_critical_isolation_refused(self):
        for key in c.policy.ISOLATED:
            with self.subTest(key=key):
                collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, **{key: 'changed'}))
                with self.assertRaisesRegex(RuntimeError, 'isolation_or_override'):
                    collector.bind_current_environment(123)
                self.assertIsNone(collector._current_environment)

    def test_optional_data_home_isolation_refused(self):
        collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, XDG_DATA_HOME='/outside'))
        with self.assertRaisesRegex(RuntimeError, 'data_home_isolation'):
            collector.bind_current_environment(123)

    def test_all_existing_forbidden_keys_refused(self):
        for key in c.policy.FORBIDDEN:
            with self.subTest(key=key):
                collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, **{key: 'forbidden'}))
                with self.assertRaisesRegex(RuntimeError, 'isolation_or_override'):
                    collector.bind_current_environment(123)

    def test_font15_presence_and_values_against_pins_and_actual_exec(self):
        for key in set(c.FONT_ENV_KEYS) - set(c.policy.ISOLATED):
            value = c.policy.OPTIONAL_ISOLATED.get(key, '')
            with self.subTest(key=key, mutation='runtime addition'):
                collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, **{key: value}))
                with self.assertRaisesRegex(RuntimeError, 'font_runtime_environment_changed'):
                    collector.bind_current_environment(123)
            with self.subTest(key=key, mutation='startup addition distinct from pins'):
                changed = dict(c.policy.ISOLATED, **{key: value})
                collector, original, child, initial, actual = fixture(current=changed, startup=changed,
                                                                     pins=c.policy.ISOLATED)
                with self.assertRaisesRegex(RuntimeError, 'font_runtime_environment_changed'):
                    collector.bind_current_environment(123)

    def test_font_present_value_change_refused(self):
        startup = dict(c.policy.ISOLATED, FONTCONFIG_PATH='/synthetic/fonts-a')
        actual = dict(startup, FONTCONFIG_PATH='/synthetic/fonts-b')
        collector, original, child, initial, actual = fixture(current=actual, startup=startup)
        with self.assertRaisesRegex(RuntimeError, 'font_runtime_environment_changed'):
            collector.bind_current_environment(123)

    def test_actual_exec_font_change_vs_pins_and_current_refused(self):
        collector, original, child, initial, actual = fixture(startup=dict(c.policy.ISOLATED, FC_LANG=''),
                                                             current=c.policy.ISOLATED, pins=c.policy.ISOLATED)
        with self.assertRaisesRegex(RuntimeError, 'font_runtime_environment_changed'):
            collector.bind_current_environment(123)

    def test_actual_exec_critical_isolation_refused(self):
        collector, original, child, initial, actual = fixture(startup=dict(c.policy.ISOLATED, HOME='/outside'),
                                                             current=c.policy.ISOLATED, pins=c.policy.ISOLATED)
        with self.assertRaisesRegex(RuntimeError, 'isolation_or_override'):
            collector.bind_current_environment(123)

    def test_effective_double_vector_mutation_refused(self):
        collector, original, child, initial, actual = fixture(change_vector=True)
        with self.assertRaisesRegex(RuntimeError, 'effective_environment_changed'):
            collector.bind_current_environment(123)

    def test_effective_double_content_mutation_refused(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='first')
        collector, original, child, initial, actual = fixture(current=actual)
        reads = [0]
        storage = 0x100000 + c.ENV_SOURCE['storage_offset']
        def hook(address, count):
            if address == storage:
                reads[0] += 1
                if reads[0] == 2:
                    put_environment(original, dict(actual, ARBITRARY_INPUT='second'))
        original.read_hook = hook
        with self.assertRaisesRegex(RuntimeError, 'effective_environment_changed'):
            collector.bind_current_environment(123)

    def test_effective_bad_pinned_libc_instruction_refused(self):
        collector, original, child, initial, actual = fixture()
        original.memory[0x100000 + c.ENV_SOURCE['load_offset']] = 0
        with self.assertRaisesRegex(RuntimeError, 'libc_environ_instruction'):
            collector.bind_current_environment(123)

    def test_kernel_startup_double_read_mutation_refused(self):
        collector, original, child, initial, actual = fixture()
        with patch.object(collector, '_read', side_effect=[encoded(initial), encoded(dict(initial, NEW_STARTUP_INPUT='changed'))]):
            with self.assertRaisesRegex(RuntimeError, 'binding_changed'):
                collector.bind_current_environment(123)

    def test_parent_full_nonfont_mutation_after_bind_refused(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='frozen')
        for changed in (dict(actual, ARBITRARY_INPUT='changed'), dict(actual, ADDED_INPUT='later'), c.policy.ISOLATED):
            with self.subTest(changed=sorted(changed)):
                collector, original, child, initial, current = fixture(current=actual)
                collector.bind_current_environment(123)
                put_environment(original, changed)
                with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
                    collector.current_environment(123)

    def test_current_original_reads_original_when_child_selected(self):
        collector, original, child, initial, actual = fixture()
        collector.bind_current_environment(123)
        collector.g.child, collector.g.thread = child, child.thread
        before = original.memory_reads
        self.assertEqual(collector.current_environment(123), actual)
        self.assertGreater(original.memory_reads, before)
        self.assertEqual(child.memory_reads, 0)

    def test_child_kernel_full_bound_parent_passes_and_static_startup_refused(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        collector.bind_current_environment(123)
        self.assertEqual(collector.exec_environment(124), actual)
        with patch.object(collector, '_read', return_value=encoded(initial)):
            with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
                collector.exec_environment(124)

    def test_child_kernel_environment_cannot_use_unbound_startup(self):
        collector, original, child, initial, actual = fixture()
        with self.assertRaisesRegex(RuntimeError, 'current_environment_unbound'):
            collector.exec_environment(124)

    def test_child_kernel_double_read_mutation_refused(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        collector.bind_current_environment(123)
        with patch.object(collector, '_read', side_effect=[encoded(actual), encoded(dict(actual, ARBITRARY_INPUT='later'))]):
            with self.assertRaisesRegex(RuntimeError, 'kernel_exec_environment_changed'):
                collector.exec_environment(124)

    def test_original_kernel_startup_is_separate_from_bound_current(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        self.assertEqual(collector.exec_environment(123), initial)
        self.assertIsNone(collector._current_environment)
        collector.bind_current_environment(123)
        self.assertEqual(collector.exec_environment(123), initial)
        self.assertEqual(collector.current_environment(123), actual)

    def test_entered_child_reads_effective_got_and_exact_complete_parent(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        collector.bind_current_environment(123)
        child.memory = dict(original.memory)
        collector.g.child, collector.g.thread = child, child.thread
        collector._entry_verified.add(124)
        with patch.object(collector, '_read', side_effect=AssertionError('kernel ENV must not substitute effective')):
            self.assertEqual(collector.exec_environment(124), actual)
            put_environment(child, dict(actual, ARBITRARY_INPUT='changed'))
            with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
                collector.exec_environment(124)
        self.assertGreater(child.memory_reads, 0)

    def test_exec_observation_child_kernel_uses_frozen_parent(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        collector.bind_current_environment(123)
        image = collector.p['libc']
        host = image['host_stamp']
        def read(path, limit):
            return b'fixture\0' if path.endswith('/cmdline') else encoded(actual)
        collector.fds = lambda pid: {}
        with patch.object(collector, '_read', side_effect=read), \
                patch.object(c.os, 'readlink', return_value=image['path']), \
                patch.object(c.os, 'stat', return_value=baseline.fake_stat(host)):
            self.assertEqual(collector.exec_observation(124, image, 0x100000, 'gpgconf')['initial_exec_environment'], actual)
        def stale(path, limit):
            return b'fixture\0' if path.endswith('/cmdline') else encoded(initial)
        with patch.object(collector, '_read', side_effect=stale), \
                patch.object(c.os, 'readlink', return_value=image['path']), \
                patch.object(c.os, 'stat', return_value=baseline.fake_stat(host)):
            with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
                collector.exec_observation(124, image, 0x100000, 'gpgconf')

    def test_snapshot_bound_context_and_first_full_mutation_refusal_retained(self):
        actual = dict(c.policy.ISOLATED, ARBITRARY_INPUT='runtime')
        collector, original, child, initial, actual = fixture(current=actual)
        collector.bind_current_environment(123)
        snapshot_fixture(collector)
        with patch.object(c.time, 'monotonic', return_value=1000.0):
            snap = collector.snapshot(123)
        self.assertTrue(snap['context']['environment_current_bound'])
        self.assertEqual(snap['environment'], actual)
        put_environment(original, dict(actual, ARBITRARY_INPUT='changed'))
        with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
            collector.snapshot(123)
        with self.assertRaisesRegex(RuntimeError, 'exact_current_environment_changed'):
            collector.bind_current_environment(124)
        self.assertEqual(collector.refusal, 'gpgme_exact_current_environment_changed')

    def test_bind_failure_terminal_first_reason_retained(self):
        collector, original, child, initial, actual = fixture(current=dict(c.policy.ISOLATED, GNUPGHOME='/outside'))
        with self.assertRaisesRegex(RuntimeError, 'isolation_or_override'):
            collector.bind_current_environment(123)
        put_environment(original, initial)
        for operation in (lambda: collector.bind_current_environment(123),
                          lambda: collector.current_environment(123), lambda: collector.snapshot(124)):
            with self.assertRaisesRegex(RuntimeError, 'isolation_or_override'):
                operation()


def main():
    superseded = {'test_effective_environment_reads_explicit_original_inferior',
        'test_effective_environment_vector_change_refused', 'test_effective_environment_override_refused',
        'test_effective_environment_bad_libc_instruction_refused'}
    old = unittest.defaultTestLoader.loadTestsFromTestCase(baseline.PureControls)
    retained = unittest.TestSuite(test for test in old if test._testMethodName not in superseded)
    targeted = unittest.defaultTestLoader.loadTestsFromTestCase(CurrentEnvironmentControls)
    counts = dict(retained_original=retained.countTestCases(), targeted=targeted.countTestCases(),
                  original_environment_tests_replaced=len(superseded))
    suite = unittest.TestSuite([retained, targeted])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(schema='frw.calc.current-environment-collector-repair-controls.v1', **counts,
                  tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  passed=result.wasSuccessful(), synthetic_only=True, runtime_attested=False,
                  gdb_started=False, target_elf_executed=False, target_processes_started=False)
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == '__main__':
    raise SystemExit(0 if main()['passed'] else 1)
