"""Inert Python GDB-service contract tests. Never import or launch GDB/Office."""
import ast
import io
import json
import os
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import unittest

OUT = Path(__file__).parent
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-CALC-COMBINED-OBSERVER-R2-20261115/outer/deps/native_return_observer.py')
TREE = ast.parse((OUT / 'native_return_observer.py').read_text())
ADDED = {'boundary_symbol', 'boundary_proc_identity', 'process_boundary_snapshot'}

class SignalEvent: pass
class BreakpointEvent:
    def __init__(self, kind=9): self.breakpoints = [SimpleNamespace(type=kind)]

class InertPath:
    files = {}
    opened = []
    def __init__(self, value): self.value = str(value)
    @property
    def name(self): return PurePosixPath(self.value).name
    def open(self, mode, encoding):
        if mode != 'r' or encoding != 'ascii': raise AssertionError('read contract')
        self.opened.append(self.value)
        return io.StringIO(self.files[self.value])

class Frame:
    def __init__(self, symbol='clone3', older=None):
        self.symbol, self.next, self.visits = symbol, older, 0
    def is_valid(self): return True
    def pc(self): return 0x1234
    def type(self): return 0
    def name(self): self.visits += 1; return self.symbol
    def older(self): return self.next
    def read_var(self, *args): raise AssertionError('argument/local read forbidden')
    def read_register(self, *args): raise AssertionError('register read forbidden')
    def __str__(self): raise AssertionError('frame formatting forbidden')

class Tests(unittest.TestCase):
    def setUp(self):
        self.saved = []
        self.frame = Frame()
        self.inferior = SimpleNamespace(num=1, pid=21)
        self.thread = SimpleNamespace(ptid=(21, 27, 0), is_valid=lambda: True)
        self.inferiors = (self.inferior,)
        self.gdb = SimpleNamespace(SignalEvent=SignalEvent, BreakpointEvent=BreakpointEvent,
            BP_CATCHPOINT=9, inferiors=lambda: self.inferiors,
            selected_inferior=lambda: self.inferior, selected_thread=lambda: self.thread,
            newest_frame=lambda: self.frame, solib_name=lambda _pc: '/private/source/libc.so.6')
        self.state = {'error':None, 'status':'READY_UNRELEASED', 'process':
            {'pid':21, 'start_ticks':50, 'gdb_pid':os.getpid(), 'inferior':1}}
        fields = ['S', str(os.getpid())] + ['0'] * 17 + ['50']
        InertPath.files = {'/proc/21/stat':'21 (SENSITIVE_COMM) ' + ' '.join(fields),
                           '/proc/21/task/27/children':'33 34\n'}
        InertPath.opened = []
        self.ns = {'gdb':self.gdb, 'os':os, 'Path':InertPath, 'STATE':self.state,
                   'save':lambda: self.saved.append(json.loads(json.dumps(self.state)))}
        names = ADDED | {'require','fail','stopped'}
        nodes = [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<inert-services>', 'exec'), self.ns)
    def stop(self): self.ns['stopped'](BreakpointEvent())
    def diagnostic(self): return self.state['process_boundary_diagnostic']
    def assert_refused(self):
        self.assertEqual(self.state['status'], 'REFUSED')
        self.assertEqual(self.state['error'], 'unexpected_fork_vfork_exec')
        self.assertEqual(len(self.saved), 1)
        self.assertIn('process_boundary_diagnostic', self.saved[0])
    def test_numeric_relation_and_no_arguments_paths_or_comm(self):
        self.stop(); self.assert_refused(); d=self.diagnostic()
        self.assertEqual(d['selected_lwp_children'], [33,34])
        self.assertEqual(d['selected_process_identity']['ppid'], os.getpid())
        self.assertEqual(d['selected_thread_ptid'], [21,27,0])
        self.assertEqual(d['frames'][0]['module_basename'], 'libc.so.6')
        self.assertEqual(InertPath.opened, ['/proc/21/stat','/proc/21/task/27/children'])
        for secret in ['SENSITIVE_COMM','/private/source','argv','environ']:
            self.assertNotIn(secret, json.dumps(d))
    def test_stack_cycle_bounded_to24_and_ascii_symbol_cap(self):
        self.frame.symbol = 'A' * 400 + '\nSENSITIVE_TRAILER'
        self.frame.next = self.frame
        self.stop(); self.assert_refused(); d=self.diagnostic()
        self.assertEqual(len(d['frames']),24); self.assertTrue(d['frames_truncated'])
        self.assertEqual(self.frame.visits,24)
        self.assertTrue(all(len(f['symbol']) == 256 for f in d['frames']))
        self.assertNotIn('SENSITIVE_TRAILER',json.dumps(d))
        self.assertEqual(self.ns['boundary_symbol']('a\n\tb',256),'a??b')
    def test_children_and_inferiors_caps(self):
        self.inferiors = tuple(SimpleNamespace(num=i,pid=20+i) for i in range(10))
        InertPath.files['/proc/21/task/27/children'] = ' '.join(str(v) for v in range(33,53))
        self.stop(); self.assert_refused(); d=self.diagnostic()
        self.assertEqual(len(d['inferiors']),4); self.assertTrue(d['inferiors_truncated'])
        self.assertEqual(len(d['selected_lwp_children']),8); self.assertTrue(d['children_truncated'])
    def test_invalid_child_text_is_class_only_and_refuses(self):
        InertPath.files['/proc/21/task/27/children']='33 SENSITIVE_PAYLOAD'
        self.stop(); self.assert_refused()
        self.assertEqual(self.diagnostic()['identity_exception_class'],'RuntimeError')
        self.assertNotIn('SENSITIVE_PAYLOAD',json.dumps(self.state))
    def test_proc_bound_refuses_and_keeps_stack(self):
        InertPath.files['/proc/21/stat']='X'*5000
        self.stop(); self.assert_refused()
        self.assertEqual(self.diagnostic()['identity_exception_class'],'RuntimeError')
        self.assertEqual(len(self.diagnostic()['frames']),1)
        self.assertEqual(InertPath.opened,['/proc/21/stat'])
    def test_parent_identity_drift_never_reads_children(self):
        self.state['process']['start_ticks']=51
        self.stop(); self.assert_refused()
        self.assertEqual(InertPath.opened,['/proc/21/stat'])
        self.assertNotIn('selected_lwp_children',self.diagnostic())
    def test_stack_error_only_class_and_original_reason(self):
        def broken(): raise ValueError('SENSITIVE_EXCEPTION')
        self.frame.older=broken
        self.stop(); self.assert_refused()
        self.assertEqual(self.diagnostic()['stack_exception_class'],'ValueError')
        self.assertNotIn('SENSITIVE_EXCEPTION',json.dumps(self.state))
    def test_diagnostic_total_failure_cannot_skip_refusal(self):
        def broken(): raise ValueError('SENSITIVE_EXCEPTION')
        self.ns['process_boundary_snapshot']=broken
        self.stop(); self.assert_refused()
        self.assertEqual(self.diagnostic(),{'exception_class':'ValueError'})
        self.assertNotIn('SENSITIVE_EXCEPTION',json.dumps(self.state))
    def test_prior_guard_error_preserved(self):
        self.state['error']='prior_guard'
        self.stop(); self.assertEqual(self.state['error'],'prior_guard')
        self.assertEqual(self.state['status'],'REFUSED')
    def test_signal_refusal_unchanged_and_other_stops_inert(self):
        self.ns['stopped'](BreakpointEvent(kind=1))
        self.assertEqual(self.state['status'],'READY_UNRELEASED'); self.assertEqual(self.saved,[])
        self.ns['stopped'](SignalEvent())
        self.assertEqual(self.state['error'],'unexpected_signal')
        self.assertNotIn('process_boundary_diagnostic',self.state)
    def test_complete_original_ast_preserved_except_catchpoint_diagnostic(self):
        old=ast.parse(ORIGINAL.read_text())
        oldstop=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='stopped')
        nodes=[]
        for node in TREE.body:
            if isinstance(node,ast.FunctionDef) and node.name in ADDED: continue
            nodes.append(oldstop if isinstance(node,ast.FunctionDef) and node.name=='stopped' else node)
        self.assertEqual(ast.dump(old,include_attributes=False),
            ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False))
        newstop=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='stopped')
        self.assertEqual(ast.dump(oldstop.body[0].body[0]),ast.dump(newstop.body[0].body[0]))
        self.assertEqual(ast.dump(oldstop.body[0].orelse[0].body[-1]),
                         ast.dump(newstop.body[0].orelse[0].body[-1]))
        diagnostic_nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in ADDED]
        forbidden={'execute','parse_and_eval','read_memory','read_var','read_register','select','switch','read_string','string','read_bytes','write_text','write_bytes'}
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in forbidden
            for f in diagnostic_nodes for n in ast.walk(f)))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    stream=io.StringIO(); result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    data={'schema':'frw.inert-gdb-services-tests.v1','tests_run':result.testsRun,
          'failures':len(result.failures),'errors':len(result.errors),
          'success':result.wasSuccessful(),'gdb_office_or_uno_launched':False,
          'runtime_acceptance':False,'log':stream.getvalue()}
    p=OUT/'TEST-RESULT.json'; p.write_text(json.dumps(data,indent=2)+'\n'); p.chmod(0o600)
    print(json.dumps({k:v for k,v in data.items() if k!='log'},sort_keys=True))
    if not result.wasSuccessful(): print(stream.getvalue())
    raise SystemExit(0 if result.wasSuccessful() else 1)
