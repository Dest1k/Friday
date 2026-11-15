"""Independent inert review checks; no GDB, helper or Office execution."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import types
import unittest

BASE = Path(__file__).resolve().parent / 'source'
HOOK = BASE / 'candidate/outer/deps/native_return_observer.py'


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


class MainHarness:
    """Execute the exact main AST with every process boundary replaced by data."""
    def __init__(self, *, unknown_stop=False, collision=False):
        self.commands = []
        self.steps = 0
        self.reselected = 0
        self.original = types.SimpleNamespace(num=1, pid=0)
        self.dead_helper = types.SimpleNamespace(num=3, pid=0)
        self.selected = self.original
        self.breakpoints = []
        self.unknown_stop = unknown_stop
        self.collision = collision
        self.state = dict(error=None, exit_code=None, records=[{}] * 10,
                          process=dict(pid=99999999), status='READY_UNRELEASED')
        self.cfg = dict(kind='OFFICE_UNADMITTED', nonce='0' * 32,
                        target_path='/INERT/target', target_sha256='1' * 64,
                        symbol_file_path='/INERT/symbols', symbol_file_sha256='2' * 64)
        self.helper = types.SimpleNamespace(catchpoints={}, dispatch=self.dispatch,
                                            original_selected=self.original_selected)
        self.events = types.SimpleNamespace(connect=lambda callback: None)
        self.gdb = types.SimpleNamespace(
            inferiors=lambda: [self.original, self.dead_helper] if self.steps else [self.original],
            selected_inferior=lambda: self.selected,
            current_progspace=lambda: types.SimpleNamespace(filename='/INERT/target'),
            breakpoints=lambda: self.breakpoints, execute=self.execute,
            events=types.SimpleNamespace(new_objfile=self.events, exited=self.events, stop=self.events))
        class InertPath:
            def __init__(self, value): self.value = value
            def read_bytes(self): return b'\x7fELF\x02\x01'
            def exists(self): return False
        self.env = dict(CFG=self.cfg, STATE=self.state, gdb=self.gdb, Path=InertPath,
                        require=require, pin=lambda *args: None, load_helper=lambda: self.helper,
                        installed=False, catchpoints={}, pending_action=None, active=None,
                        identity=lambda: None, phase=lambda: {'phase': 'CLOSED'},
                        save=lambda: None, exited=lambda event: None, stopped=lambda event: None)
        def install(*args): self.env['installed'] = True
        self.env['install'] = install
        tree = ast.parse(HOOK.read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        exec(compile(ast.Module(body=[main], type_ignores=[]), '<exact-main-inert>', 'exec'), self.env)

    def execute(self, cmd, **kwargs):
        self.commands.append(cmd)
        if cmd.startswith('catch '):
            self.breakpoints.append(types.SimpleNamespace(number=len(self.breakpoints) + 1))
        elif cmd == 'starti':
            self.original.pid = 12
        elif cmd == 'continue':
            self.steps += 1
            if self.steps == 1:
                self.selected = self.dead_helper
                if self.collision:
                    self.env['pending_action'] = 'START_CALL'
            elif self.steps == 2:
                require(self.selected is self.original, 'original_not_reselected')
                self.original.pid = 0
                self.state['exit_code'] = 0
            else:
                raise AssertionError('Unexpected extra inert continuation')

    def dispatch(self):
        return None if self.unknown_stop else 'CONTINUE'

    def original_selected(self):
        if self.original.pid:
            self.selected = self.original
            self.reselected += 1
            return True
        return False


class IndependentReviewChecks(unittest.TestCase):
    def source_policy_case(self):
        spec = importlib.util.spec_from_file_location('review_policy_case', BASE / 'tests/test_semantics.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, module.through(module.custody(), 'paper_entry')

    def test_exact_before_copy_matches_all_frozen_C3_files(self):
        c3 = Path('/home/jericho/.cache/FRW-ASTRA-CALC-COMBINED-OBSERVER-DIAGNOSTIC-R3-20261115/SOURCE-FREEZE-R3.json')
        j = json.loads(c3.read_bytes())
        for item in j['files']:
            raw = (BASE / 'before' / item['relative_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'], item['relative_path'])
            self.assertEqual(len(raw), item['bytes'])

    def test_dead_selected_helper_does_not_end_original_main(self):
        h = MainHarness()
        h.env['main']()
        self.assertEqual(h.steps, 2)
        self.assertEqual(h.reselected, 1)
        self.assertEqual(h.state['exit_code'], 0)
        self.assertEqual(h.state['status'], 'COMPLETE_UNATTESTED')
        self.assertEqual(set(h.helper.catchpoints.values()), {'fork', 'vfork', 'exec'})

    def test_unrecognized_stop_still_refuses_after_selected_helper_exit(self):
        h = MainHarness(unknown_stop=True)
        with self.assertRaisesRegex(RuntimeError, '^unrecognized_stop$'):
            h.env['main']()
        self.assertEqual(h.steps, 1)

    def test_helper_and_metric_stop_collision_refuses(self):
        h = MainHarness(collision=True)
        with self.assertRaisesRegex(RuntimeError, '^helper_metric_stop_collision$'):
            h.env['main']()
        self.assertEqual(h.steps, 1)

    def adapter(self, path=None):
        spec = importlib.util.spec_from_file_location('reviewed_adapter', path or BASE / 'candidate/outer/deps/paper_helper_gdb.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        a = module.Adapter.__new__(module.Adapter)
        state = dict(error=None)
        a.n = {'STATE': state, 'fail': lambda reason: state.update(error=state['error'] or reason)}
        a.breakpoints = []
        a.stop_handlers = {}
        a.retired_breakpoints = set()
        a.pending_stop = None
        a.to_create = []
        a.pending = None
        a.publish = lambda: None
        a.tid = lambda: [12, 12, 0]
        inf = types.SimpleNamespace(num=1, pid=12)
        class Breakpoint:
            def __init__(self, *args, **kwargs):
                self.number = len(a.breakpoints) + 1
                self.enabled = True
            def is_valid(self): return True
        a.g = types.SimpleNamespace(Breakpoint=Breakpoint, selected_inferior=lambda: inf,
                                    newest_frame=lambda: types.SimpleNamespace(pc=lambda: 0x1234))
        return a, inf, state

    def test_repeated_stop_predicate_advances_only_one_actual_event(self):
        a, inf, state = self.adapter()
        module, c = self.source_policy_case()
        bp = a.breakpoint(0x1234, lambda: c.eof(module.THREAD, empty_eof=True))
        for _ in range(5):
            self.assertTrue(bp.stop())
        self.assertFalse(c.e['empty_stdout_eof'])
        event = types.SimpleNamespace(breakpoints=[bp])
        self.assertTrue(a.queue_stop(event))
        self.assertTrue(bp.stop())
        self.assertFalse(c.e['empty_stdout_eof'])
        self.assertEqual(a.dispatch(), 'CONTINUE')
        self.assertEqual(a.dispatch(), None)
        self.assertTrue(c.e['empty_stdout_eof'])
        self.assertIsNone(state['error'])

    def test_original_callback_duplicate_reproduces_retained_EOF_error(self):
        path = Path('/home/jericho/.cache/FRW-ASTRA-CALC-PAPER-HELPER-GUARD-SOURCE-20261115/candidate/outer/deps/paper_helper_gdb.py')
        spec = importlib.util.spec_from_file_location('original_callback_adapter', path)
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        a = original.Adapter.__new__(original.Adapter)
        module, c = self.source_policy_case()
        state = dict(error=None)
        a.n = {'STATE': state, 'fail': lambda reason: state.update(error=state['error'] or reason)}
        a.publish = lambda: None
        callback = a.callback(lambda: c.eof(module.THREAD, empty_eof=True))
        self.assertTrue(callback())
        self.assertIsNone(state['error'])
        self.assertTrue(callback())
        self.assertEqual(state['error'], 'helper_stdout_not_empty_EOF')
        self.assertTrue(c.e['empty_stdout_eof'])

    def test_duplicate_actual_stop_event_and_foreign_inferior_refuse(self):
        a, inf, state = self.adapter()
        bp = a.breakpoint(0x1234, lambda: self.fail('unexpected callback'))
        event = types.SimpleNamespace(breakpoints=[bp])
        a.queue_stop(event)
        with self.assertRaisesRegex(RuntimeError, '^helper_ambiguous_or_duplicate_stop_event$'):
            a.queue_stop(event)
        a.pending_stop = None
        inf.num = 3
        with self.assertRaisesRegex(RuntimeError, '^helper_stop_event_inferior$'):
            a.queue_stop(event)

    def test_context_drift_refuses_before_observation(self):
        a, inf, state = self.adapter()
        bp = a.breakpoint(0x1234, lambda: self.fail('unexpected callback'))
        a.queue_stop(types.SimpleNamespace(breakpoints=[bp]))
        inf.pid = 99
        self.assertIsNone(a.dispatch())
        self.assertEqual(state['error'], 'helper_stop_event_context_changed')

    def test_first_refusal_freezes_all_later_helper_transitions(self):
        a, inf, state = self.adapter()
        def fail_once(): raise RuntimeError('first-refusal')
        first = a.breakpoint(0x1234, fail_once)
        second = a.breakpoint(0x1234, lambda: self.fail('post-refusal mutation'))
        a.queue_stop(types.SimpleNamespace(breakpoints=[first]))
        a.dispatch()
        self.assertEqual(state['error'], 'first-refusal')
        self.assertTrue(a.queue_stop(types.SimpleNamespace(breakpoints=[second])))
        self.assertIsNone(a.dispatch())
        a.boundary(types.SimpleNamespace())
        self.assertTrue(a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=3))))
        self.assertEqual(state['error'], 'first-refusal')

    def test_previous_revision_two_real_EOF_events_around_shell_exit_reproduce_R2(self):
        previous = Path('/home/jericho/.cache/FRW-ASTRA-CALC-PAPER-GUARD-CORRECTED-ROOT-20261115/candidate/outer/deps/paper_helper_gdb.py')
        a, inf, state = self.adapter(previous)
        module, c = self.source_policy_case()
        a.c = c
        a.ensure = lambda: c
        bp = a.breakpoint(0x1234, lambda: c.eof(module.THREAD, empty_eof=True))
        event = types.SimpleNamespace(breakpoints=[bp])
        a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=3), exit_code=3))
        a.dispatch()
        a.queue_stop(event)
        a.dispatch()
        self.assertTrue(c.e['empty_stdout_eof'])
        self.assertIsNone(state['error'])
        a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=2), exit_code=3))
        a.dispatch()
        a.queue_stop(event)  # Same original thread/PC after helper exit/reselect.
        a.dispatch()
        self.assertEqual(state['error'], 'helper_stdout_not_empty_EOF')
        self.assertEqual(c.e['state'], 'PAPERCONF_ENTRY')
        self.assertIsNone(c.e['pclose_status'])

    def test_one_shot_EOF_retires_before_shell_exit_and_delivered_duplicate_refuses(self):
        a, inf, state = self.adapter()
        module, c = self.source_policy_case()
        a.c = c
        a.ensure = lambda: c
        seen = []
        def observe():
            c.eof(module.THREAD, empty_eof=True)
            seen.append('EOF')
        bp = a.breakpoint(0x1234, observe)
        a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=3), exit_code=3))
        a.dispatch()
        a.queue_stop(types.SimpleNamespace(breakpoints=[bp]))
        a.dispatch()
        self.assertFalse(bp.enabled)
        self.assertIn(bp.number, a.retired_breakpoints)
        a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=2), exit_code=3))
        a.dispatch()
        # A disabled actual trap is no longer armed. If an event is nevertheless
        # delivered, the exact native stopped consumer must refuse it, not replay EOF.
        class SignalEvent: pass
        class BreakpointEvent:
            def __init__(self): self.breakpoints = [bp]
        tree = ast.parse(HOOK.read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'stopped')
        env = dict(helper=a, fail=a.n['fail'], gdb=types.SimpleNamespace(
            SignalEvent=SignalEvent, BreakpointEvent=BreakpointEvent, BP_CATCHPOINT=9))
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<exact-stopped-retired-event>', 'exec'), env)
        env['stopped'](BreakpointEvent())
        self.assertEqual(state['error'], 'helper_retired_breakpoint_event')
        self.assertEqual(seen, ['EOF'])
        self.assertIsNone(c.e['pclose_status'])

    def test_failed_observation_does_not_retire_breakpoint(self):
        a, inf, state = self.adapter()
        def fail_value(): raise RuntimeError('wrong-observed-value')
        bp = a.breakpoint(0x1234, fail_value)
        a.queue_stop(types.SimpleNamespace(breakpoints=[bp]))
        a.dispatch()
        self.assertTrue(bp.enabled)
        self.assertNotIn(bp.number, a.retired_breakpoints)
        self.assertEqual(state['error'], 'wrong-observed-value')

    def test_persistent_popen_rejects_second_invocation_without_retirement(self):
        a, inf, state = self.adapter()
        module, _ = self.source_policy_case()
        c = module.custody()
        bp = a.breakpoint(0x1234, lambda: module.arm(c), one_shot=False)
        event = types.SimpleNamespace(breakpoints=[bp])
        a.queue_stop(event)
        a.dispatch()
        self.assertTrue(bp.enabled)
        self.assertNotIn(bp.number, a.retired_breakpoints)
        a.queue_stop(event)
        a.dispatch()
        self.assertEqual(state['error'], 'helper_extra_invocation')
        self.assertEqual(c.e['invocations'], 1)

    def test_install_keeps_popen_persistent_and_return_sites_one_shot(self):
        a, inf, state = self.adapter()
        module, _ = self.source_policy_case()
        a.installed = False
        a.n['STATE']['process'] = {'pid': 12}
        a.m = module.MANIFEST
        a.base = lambda pid, path: 0x100000
        a.ensure = lambda: None
        a.install()
        self.assertEqual(len(a.breakpoints), 4)
        flags = [a.stop_handlers[b.number][2] for b in a.breakpoints]
        self.assertEqual(flags, [False, True, True, True])


if __name__ == '__main__':
    unittest.main(verbosity=2)
