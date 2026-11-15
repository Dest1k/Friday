"""Pure extracted-source checks; never imports gdb or executes inferior code."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

BASE = Path(__file__).resolve().parents[1]
ADAPTER = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GDB-OFFICE-CORE-DIAGNOSIS-20261115/candidate/paper_helper_gdb.py')
ADAPTER_SHA = '6c7f293cb7636b34f747143b797f9e6601d96d83ff5e49a752446bbfff334b10'


class SignalEvent:
    def __init__(self, sig):
        self.stop_signal = sig


class BreakpointEvent:
    def __init__(self, kind='fork', number=1, catchpoint=True):
        self.breakpoints = [SimpleNamespace(number=number, type=7 if catchpoint else 1)]
        self.kind = kind


def extract(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pure-extracted-source>', 'exec'), namespace)
    return namespace


def helper_boundary():
    raw = ADAPTER.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ADAPTER_SHA
    cls = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == 'Adapter')
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'boundary')
    ns = {'require': lambda ok, reason: None if ok else (_ for _ in ()).throw(RuntimeError(reason))}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '<pure-exact-helper-boundary>', 'exec'), ns)
    return ns['boundary']


class Helper:
    def __init__(self, env, queued=False, error=None):
        self.env = env
        self.queued = queued
        self.error = error
        self.catchpoints = {1: 'fork', 2: 'vfork', 3: 'exec'}
        self.g = env['gdb']
        self.n = env
        self.actions = []
        self.pending = None

    def queue_stop(self, event):
        return self.queued

    def boundary(self, event):
        if self.error is not None:
            raise self.error
        return helper_boundary()(self, event)

    def birth(self): self.actions.append('birth')
    def exec(self): self.actions.append('exec')
    def publish(self): self.actions.append('publish')


def hook(which='candidate', queued=False, error=None, prior=None, helper=True):
    state = {'error': prior, 'status': 'READY', 'process': None}
    snapshots = []
    saves = []
    def snapshot():
        snapshots.append('snapshot')
        return {'schema': 'frw.process-boundary-symbols.v1', 'frames': [{'symbol': 'caller'}]}
    env = {'gdb': SimpleNamespace(SignalEvent=SignalEvent, BreakpointEvent=BreakpointEvent, BP_CATCHPOINT=7),
           'STATE': state, 'pending_action': None, 'save': lambda: saves.append(dict(state)),
           'process_boundary_snapshot': snapshot}
    extract(BASE/which/'native_return_observer.py', ['stopped', 'fail'], env)
    env['helper'] = Helper(env, queued=queued, error=error) if helper else None
    return env, snapshots, saves


class RoutingTests(unittest.TestCase):
    def test_original_gap_reproduced(self):
        env, calls, saves = hook('before')
        env['stopped'](BreakpointEvent())
        self.assertEqual(calls, [])
        self.assertNotIn('process_boundary_diagnostic', env['STATE'])
        self.assertEqual(saves[-1]['error'], 'helper_unexpected_fork_or_catchpoint')

    def test_exact_helper_fork_refusal_captures_before_original_fail(self):
        env, calls, saves = hook()
        env['stopped'](BreakpointEvent())
        self.assertEqual(calls, ['snapshot'])
        self.assertEqual(env['STATE']['status'], 'REFUSED')
        self.assertEqual(env['STATE']['error'], 'helper_unexpected_fork_or_catchpoint')
        self.assertEqual(saves[-1]['process_boundary_diagnostic']['frames'][0]['symbol'], 'caller')
        self.assertIsNone(env['helper'].pending)
        self.assertEqual(env['helper'].actions, [])

    def test_snapshot_failure_retains_original_refusal(self):
        env, _, saves = hook()
        def broken(): raise ValueError('PRIVATE CONTENT MUST NOT BE STORED')
        env['process_boundary_snapshot'] = broken
        env['stopped'](BreakpointEvent())
        self.assertEqual(env['STATE']['process_boundary_diagnostic'], {'exception_class': 'ValueError'})
        self.assertEqual(saves[-1]['error'], 'helper_unexpected_fork_or_catchpoint')
        self.assertNotIn('PRIVATE', json.dumps(saves))

    def test_prior_error_diagnostic_not_overwritten(self):
        env, calls, saves = hook(prior='first_original_refusal',
                                 error=RuntimeError('helper_unexpected_fork_or_catchpoint'))
        env['STATE']['process_boundary_diagnostic'] = {'original': True}
        env['stopped'](BreakpointEvent())
        self.assertEqual(calls, [])
        self.assertEqual(env['STATE']['error'], 'first_original_refusal')
        self.assertEqual(env['STATE']['process_boundary_diagnostic'], {'original': True})

    def test_accepted_helper_vfork_and_exec_never_snapshot(self):
        for kind, number, action in [('vfork', 2, 'birth'), ('exec', 3, 'exec')]:
            with self.subTest(kind=kind):
                env, calls, saves = hook()
                env['stopped'](BreakpointEvent(kind, number))
                self.assertEqual(calls, [])
                self.assertEqual(saves, [])
                self.assertEqual(env['helper'].actions, [action, 'publish'])
                self.assertEqual(env['helper'].pending, 'CONTINUE')

    def test_queued_helper_breakpoint_does_not_snapshot(self):
        env, calls, saves = hook(queued=True)
        env['stopped'](BreakpointEvent(catchpoint=False))
        self.assertEqual((calls, saves), ([], []))

    def test_other_helper_failure_keeps_original_reason_without_snapshot(self):
        for failure, expected in [(RuntimeError('other_exact_reason'), 'other_exact_reason'),
                                  (ValueError('not retained'), 'ValueError')]:
            with self.subTest(reason=expected):
                env, calls, _ = hook(error=failure)
                env['stopped'](BreakpointEvent())
                self.assertEqual(calls, [])
                self.assertEqual(env['STATE']['error'], expected)

    def test_no_helper_generic_catchpoint_route_unchanged(self):
        env, calls, saves = hook(helper=False)
        env['stopped'](BreakpointEvent())
        self.assertEqual(calls, ['snapshot'])
        self.assertEqual(saves[-1]['error'], 'unexpected_fork_vfork_exec')

    def test_signal_routes_unchanged(self):
        env, calls, _ = hook()
        env['stopped'](SignalEvent('SIGSTOP'))
        self.assertEqual(env['pending_action'], 'FONT_RUNTIME')
        env['stopped'](SignalEvent('SIGSTOP'))
        self.assertEqual(env['STATE']['error'], 'unexpected_signal')
        self.assertEqual(calls, [])


class Frame:
    def __init__(self, number, total): self.number, self.total = number, total
    def is_valid(self): return True
    def pc(self): return 4096 + self.number
    def type(self): return 0
    def name(self): return 'KnownCaller\n\N{SNOWMAN}' + ('x' * 300)
    def older(self): return Frame(self.number+1, self.total) if self.number+1 < self.total else None


class SnapshotTests(unittest.TestCase):
    def test_snapshot_remains_exact_original_source_and_bound(self):
        old, new = [ast.parse((BASE/d/'native_return_observer.py').read_text()) for d in ('before', 'candidate')]
        old_nodes, new_nodes = [{n.name: ast.dump(n) for n in t.body if isinstance(n, ast.FunctionDef)} for t in (old, new)]
        self.assertEqual([k for k in old_nodes if old_nodes[k] != new_nodes[k]], ['stopped'])
        g = SimpleNamespace(inferiors=lambda: [SimpleNamespace(num=i, pid=100+i) for i in range(5)],
            selected_inferior=lambda: SimpleNamespace(num=1, pid=101),
            selected_thread=lambda: SimpleNamespace(ptid=(101, 102, 0), is_valid=lambda: True),
            newest_frame=lambda: Frame(0, 30), solib_name=lambda pc: '/PRIVATE/PATH/libmergedlo.so')
        ns = {'gdb': g, 'Path': Path, 'STATE': {'process': None}, 'os': SimpleNamespace(getpid=lambda: 99),
              'require': lambda ok, msg: None if ok else (_ for _ in ()).throw(RuntimeError(msg))}
        extract(BASE/'candidate/native_return_observer.py', ['boundary_symbol', 'boundary_proc_identity', 'process_boundary_snapshot'], ns)
        result = ns['process_boundary_snapshot']()
        self.assertEqual(len(result['frames']), 24)
        self.assertTrue(result['frames_truncated'])
        self.assertEqual(len(result['inferiors']), 4)
        self.assertTrue(result['inferiors_truncated'])
        for frame in result['frames']:
            self.assertEqual(set(frame), {'pc', 'kind', 'symbol', 'module_basename'})
            self.assertEqual(frame['module_basename'], 'libmergedlo.so')
            self.assertEqual(len(frame['symbol']), 256)
            self.assertTrue(all(32 <= ord(c) < 127 for c in frame['symbol']))
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_full_candidate_compiles_in_memory_only(self):
        compile((BASE/'candidate/native_return_observer.py').read_bytes(), '<candidate-no-import>', 'exec')


if __name__ == '__main__':
    unittest.main(verbosity=2)
