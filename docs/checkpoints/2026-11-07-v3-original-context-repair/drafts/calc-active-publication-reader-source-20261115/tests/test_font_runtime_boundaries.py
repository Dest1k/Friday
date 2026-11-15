"""Pure held-boundary controls. Never starts an inferior, signal, namespace or UNO."""
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import tempfile
import time
import types
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
CANDIDATE = BASE / 'candidate'
DEPS = CANDIDATE / 'outer/deps'
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
N = load('font_runtime_namespace', CANDIDATE/'outer/namespace_entry.py')
I = load('font_runtime_inner', CANDIDATE/'inner/inner_client.py')
A = load('font_runtime_adapter', DEPS/'paper_helper_gdb.py')
MANIFEST_PATH = DEPS/'PAPER-HELPER-OFFICE-MANIFEST.json'
MANIFEST = json.loads(MANIFEST_PATH.read_bytes())
REF = lambda p: dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
WIRE = lambda value: (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
NATIVE = dict(pid=12,start_ticks=100,gdb_pid=2,inferior=1)
SUPERVISOR = dict(pid=111,ppid=0,start_ticks=222)
ENV = {key: None for key in N.FONT_ENV_KEYS}
ENV.update(HOME='/OWN/BASE',LANG='C.UTF-8',LC_ALL='C.UTF-8')
PLAN = dict(operation_id='OWN_MOCK',nonce='0'*32, observer=dict(load_dependency=dict(
    adapter=REF(DEPS/'paper_helper_gdb.py'),manifest=REF(MANIFEST_PATH))),
    font_view=dict(expected_view_sha256='c'*64,base_view_sha256='b'*64))

class HeldFixture:
    def __init__(self, root, boundary='AFTER_LOAD_BEFORE_QUERY', changes=None):
        self.root = root; self.boundary = boundary
        self.sequence = 0 if boundary=='AFTER_LOAD_BEFORE_QUERY' else 1
        self.phase = dict(nonce=PLAN['nonce'],phase='IDLE' if self.sequence==0 else 'CLOSED',index=None,digit=None)
        self.env = {k.encode():v.encode() for k,v in ENV.items() if v is not None}
        self.env[b'FRW_HARMLESS_RUNTIME_ONLY'] = b'OWN'
        if changes: self.env.update(changes)
        self.deadline = time.monotonic()+30
        self.request = dict(schema='frw.calc.font-runtime-request.v1',operation_id=PLAN['operation_id'],
            nonce=PLAN['nonce'],boundary=boundary,sequence=self.sequence,process=NATIVE,
            supervisor=SUPERVISOR,deadline_monotonic=self.deadline,requested_monotonic=time.monotonic())
        self.files = {kind:root/('font-runtime-'+('loaded' if self.sequence==0 else 'closed')+'-'+kind+'.json')
            for kind in ('request','proof','release','accepted')}
        self.files['view'] = root/('font-view-after-load.json' if self.sequence==0 else 'font-view-after-close.json')
        self.write(self.files['request'],self.request)
        self.thread_stopped = True; self.sender = 111; self.signal_number = 19; self.signal_code = 0
        self.env_reads = 0
        self.ns = self.native_namespace()
        self.helper = types.SimpleNamespace(metric_ready=lambda:None,
            current_environment=self.current,
            b={'runtime':{'operation_id':PLAN['operation_id'],'operation_deadline_monotonic':self.deadline},
               'adapter_ref':REF(DEPS/'paper_helper_gdb.py')},m=MANIFEST)
        self.ns.update(helper=self.helper)
        self.native_write = self.ns['font_write']
        self.ns['font_write'] = self.write_proof_and_release

    def write(self,path,value):
        path.write_bytes(WIRE(value)); path.chmod(0o600)
    def current(self,pid):
        self.env_reads += 1
        assert pid == NATIVE['pid']
        return dict(self.env)
    def native_namespace(self):
        tree = ast.parse((DEPS/'native_return_observer.py').read_bytes())
        names = {'font_read','font_write','capture_font_runtime'}
        body = [node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        def require(ok,reason):
            if not ok: raise RuntimeError(reason)
        def sig(expression):
            fields = {'$_siginfo.si_signo':self.signal_number,'$_siginfo.si_code':self.signal_code,
                '$_siginfo._sifields._kill.si_pid':self.sender,'$_siginfo._sifields._kill.si_uid':os.getuid()}
            return fields[expression]
        inf = types.SimpleNamespace(pid=12,threads=lambda:[types.SimpleNamespace(is_valid=lambda:True,
            is_stopped=lambda:self.thread_stopped)])
        ns = dict(json=json,os=os,stat=stat,math=math,time=time,Path=Path,hashlib=hashlib,
            require=require,CFG=dict(kind='OFFICE_UNADMITTED',nonce=PLAN['nonce']),
            STATE=dict(process=NATIVE,records=[{} for _ in range(self.sequence*10)]),
            active=None,font_runtime_boundaries=[{} for _ in range(self.sequence)],identity=lambda:inf,
            phase=lambda:self.phase,font_file=lambda boundary,kind:self.files[kind],
            boundary_proc_identity=lambda pid:SUPERVISOR,
            gdb=types.SimpleNamespace(parse_and_eval=sig))
        exec(compile(ast.Module(body=body,type_ignores=[]),str(DEPS/'native_return_observer.py'),'exec'),ns)
        return ns
    def write_proof_and_release(self,path,value):
        ref = self.native_write(path,value)
        if path == self.files['proof']:
            view = dict(phase=self.boundary,view_sha256=PLAN['font_view']['expected_view_sha256'],
                base_static_view_sha256=PLAN['font_view']['base_view_sha256'],office_font_environment=ENV,
                office_font_environment_proof=ref,
                office_process=dict(namespace_pid=12,start_ticks=100,ppid=2))
            self.write(self.files['view'],view)
            release = dict(schema='frw.calc.font-runtime-release.v1',
                **{key:self.request[key] for key in ('operation_id','nonce','boundary','sequence','process')},
                request_ref=REF(self.files['request']),proof_ref=ref,font_view_ref=REF(self.files['view']))
            self.write(self.files['release'],release)
        return ref
    def run(self):
        self.ns['capture_font_runtime']()
        return json.loads(self.files['proof'].read_bytes())
    def validate(self):
        return N.validate_font_runtime_pair(*(self.files[k].read_bytes() for k in
            ('request','proof','release','accepted','view')),plan=PLAN,native=NATIVE,
            environment=ENV,boundary=self.boundary,deadline=self.deadline,supervisor=SUPERVISOR)

class BoundaryTests(unittest.TestCase):
    def make(self,boundary='AFTER_LOAD_BEFORE_QUERY',changes=None):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root=Path(tmp.name); root.chmod(0o700)
        self.addCleanup(patch.stopall); patch.object(N,'WORK',root).start()
        return HeldFixture(root,boundary,changes)
    def test_both_held_points_use_exact_current_projection_and_bound_transcripts(self):
        for boundary in ('AFTER_LOAD_BEFORE_QUERY','AFTER_READONLY_CLOSE'):
            with self.subTest(boundary=boundary):
                f=self.make(boundary); proof=f.run()
                self.assertEqual([row['key'] for row in proof['font_environment']],list(N.FONT_ENV_KEYS))
                self.assertEqual(proof['source_class'],'PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON')
                self.assertEqual(proof['scope'],'THIS_ALL_STOP_POINT_ONLY_NO_CONTINUOUS_ENVIRONMENT_CLAIM')
                self.assertEqual(f.env_reads,2)
                self.assertEqual(f.validate(),REF(f.files['proof']))
    def test_font_change_after_initial_proc_is_rejected_at_each_later_point(self):
        for boundary in ('AFTER_LOAD_BEFORE_QUERY','AFTER_READONLY_CLOSE'):
            with self.subTest(boundary=boundary):
                f=self.make(boundary,{b'FC_LANG':b'OWN_CHANGED'}); f.run()
                with self.assertRaisesRegex(N.Refused,'projection_changed'): f.validate()
    def test_sender_birth_nonce_order_deadline_and_running_thread_refuse(self):
        mutations = (
            lambda f:setattr(f,'sender',999),lambda f:setattr(f,'signal_code',-6),
            lambda f:setattr(f,'thread_stopped',False),
            lambda f:f.request.update(nonce='f'*32),lambda f:f.request.update(supervisor=dict(SUPERVISOR,start_ticks=223)),
            lambda f:f.request.update(deadline_monotonic=f.deadline+1),
            lambda f:f.request.update(requested_monotonic=f.deadline+1),
            lambda f:f.ns['STATE'].update(records=[{}]),lambda f:f.phase.update(phase='CLOSED'))
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                f=self.make(); mutate(f); f.write(f.files['request'],f.request)
                with self.assertRaises(RuntimeError): f.run()
                self.assertFalse(f.files['proof'].exists())
    def test_future_release_and_replayed_boundary_refuse(self):
        f=self.make(); f.write(f.files['release'],{})
        with self.assertRaisesRegex(RuntimeError,'future_release'): f.run()
        f.files['release'].unlink(); f.run()
        with self.assertRaises(RuntimeError): f.run()
    def test_duplicate_missing_extra_keys_hash_drift_and_forged_boolean_refuse(self):
        f=self.make(); proof=f.run()
        for rows in (proof['font_environment'][:-1],proof['font_environment']+[proof['font_environment'][0]],
                     list(reversed(proof['font_environment'])),
                     [dict(row,value_sha256='f'*64) if row['key']=='FC_LANG' else row for row in proof['font_environment']]):
            with self.subTest(rows=len(rows)),self.assertRaises(N.Refused): N.validate_font_projection(rows,ENV)
        helper_rows=[dict(key=k,initial_value_sha256=N.sha(v.encode()) if v is not None else None,
            runtime_value_sha256=N.sha(v.encode()) if v is not None else None) for k,v in ENV.items()]
        # A true summary boolean never substitutes for exact baseline values.
        helper_rows[0]['runtime_value_sha256']='f'*64
        with self.assertRaises(N.Refused): N.validate_font_projection(helper_rows,ENV,helper=True)
        original=f.files['accepted'].read_bytes(); ack=json.loads(original);ack['release_ref']['sha256']='f'*64
        f.write(f.files['accepted'],ack)
        with self.assertRaises(N.Refused):f.validate()
    def test_file_bounds_links_rights_and_nonatomic_partial_data_refuse(self):
        f=self.make(); target=f.files['request']; original=target.read_bytes()
        for mode in (0o644,0o660):
            target.chmod(mode)
            with self.assertRaises(N.Refused): N.font_runtime_read(target)
        target.chmod(0o600); other=f.root/'hardlink';os.link(target,other)
        with self.assertRaises(N.Refused):N.font_runtime_read(target)
        other.unlink();target.write_bytes(b'x'*32769)
        with self.assertRaises(N.Refused):N.font_runtime_read(target)
        target.write_bytes(original);target.chmod(0o600)
        self.assertEqual(N.font_runtime_read(target),original)
    def test_native_guard_functions_and_getter_unchanged(self):
        names=('frame_ok','reg','memint','digit_at','OuterFinish','OuterEntry','NativeEntry','NativeReturn','address',
               'identity','thread','exited','install')
        old=ast.parse((BASE/'before/outer/deps/native_return_observer.py').read_bytes())
        new=ast.parse((DEPS/'native_return_observer.py').read_bytes())
        for name in names:
            nodes=lambda tree:next(n for n in tree.body if getattr(n,'name',None)==name)
            self.assertEqual(ast.dump(nodes(old),include_attributes=False),ast.dump(nodes(new),include_attributes=False))
        for relative in ('outer/deps/paper_helper_gdb.py','outer/deps/paper_helper_policy.py',
            'outer/deps/check_native_trace.py','qualifier/reference_metric_leaf_r2.py','outer/font_view/font_view.py'):
            self.assertEqual((BASE/'before'/relative).read_bytes(),(CANDIDATE/relative).read_bytes())
    def test_signal_routing_only_explicit_stop_and_never_other_signal(self):
        fn=next(n for n in ast.parse((DEPS/'native_return_observer.py').read_bytes()).body
                if isinstance(n,ast.FunctionDef) and n.name=='stopped')
        class SignalEvent:
            def __init__(self,name):self.stop_signal=name
        errors=[]
        ns=dict(gdb=types.SimpleNamespace(SignalEvent=SignalEvent),pending_action=None,
                helper=object(),fail=errors.append)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-stopped>','exec'),ns)
        ns['stopped'](SignalEvent('SIGSTOP'));self.assertEqual(ns['pending_action'],'FONT_RUNTIME')
        ns['stopped'](SignalEvent('SIGSTOP'));self.assertEqual(errors,['unexpected_signal'])
        ns['pending_action']=None;ns['stopped'](SignalEvent('SIGUSR1'))
        self.assertEqual(errors,['unexpected_signal','unexpected_signal'])
        ns['helper']=None
        for name in ('SIGSTOP','SIGUSR1','SIGSEGV'):
            ns['pending_action']=None;ns['stopped'](SignalEvent(name))
            self.assertEqual(errors[-1],'unexpected_signal');self.assertIsNone(ns['pending_action'])
    def test_legacy_nohelper_phase_behavior_matches_exact_prior_snapshot(self):
        f=self.make()
        environments=[]
        for source in (BASE/'before/outer/deps/native_return_observer.py',DEPS/'native_return_observer.py'):
            fn=next(n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='phase')
            def require(ok,reason):
                if not ok:raise RuntimeError(reason)
            namespace=dict(Path=Path,json=json,CFG={'phase_path':str(f.root/'phase.json'),'nonce':PLAN['nonce']},
                STATE={'records':[]},active=None,helper=None,require=require,font_runtime_boundaries=[])
            exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace)
            environments.append(namespace)
        values=[dict(nonce=PLAN['nonce'],phase='IDLE',index=None,digit=None),
                dict(nonce=PLAN['nonce'],phase='METRIC',index=0,digit='0'),
                dict(nonce=PLAN['nonce'],phase='METRIC',index=9,digit='9'),
                dict(nonce=PLAN['nonce'],phase='CLOSED',index=None,digit=None),
                dict(nonce='f'*32,phase='IDLE',index=None,digit=None),
                dict(nonce=PLAN['nonce'],phase='METRIC',index=0,digit='1')]
        for value in values:
            f.write(f.root/'phase.json',value);outputs=[]
            for namespace in environments:
                try:outputs.append(('OK',namespace['phase']()))
                except Exception as exc:outputs.append((type(exc).__name__,str(exc)))
            self.assertEqual(outputs[0],outputs[1])
    def test_no_initial_proc_font_environment_admission_remains(self):
        node=next(n for n in ast.parse((CANDIDATE/'outer/namespace_entry.py').read_bytes()).body if isinstance(n,ast.ClassDef)
            and n.name=='LocalServices')
        fn=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='font_view_observation')
        text=ast.unparse(fn)
        self.assertNotIn("'environ'",text)
        self.assertIn('validate_font_runtime_proof',text)
        inner=ast.parse((CANDIDATE/'inner/inner_client.py').read_bytes())
        execute=next(n for n in inner.body if isinstance(n,ast.FunctionDef) and n.name=='execute_inner')
        text=ast.unparse(execute)
        self.assertLess(text.index('phases.closed()'),text.index("result['stage'] = 'DESKTOP_TERMINATE'"))
    def test_full_inventory_requires_two_points_exact_helper_projection_and_no_extra_outputs(self):
        f=self.make(); f.run()
        closed=HeldFixture(f.root,'AFTER_READONLY_CLOSE');closed.deadline=f.deadline
        closed.request['deadline_monotonic']=f.deadline;closed.helper.b['runtime']['operation_deadline_monotonic']=f.deadline
        closed.write(closed.files['request'],closed.request);closed.run()
        prior=load('prior_E_getter_controls',Path('/home/jericho/.cache/FRW-ASTRA-PAPER-RUNTIME-ENVIRONMENT-SOURCE-20261115/tests/test_runtime_environment.py'))
        memory=prior.MemoryFixture();a=memory.a
        a.audit_actual_env={k.encode():v.encode() for k,v in ENV.items() if v is not None}
        a.audit_expected_env=dict(a.audit_actual_env);a.audit_font_initial=dict(a.audit_actual_env)
        runtime=copy.deepcopy(a.b['runtime']);runtime['operation_deadline_monotonic']=f.deadline
        a.b['runtime']=runtime
        original_path=Path
        def mapped(path):
            if str(path)=='/proc':return f.root/'absent_proc'
            if str(path).startswith('/tmp/friday-metric-work/'):return f.root/original_path(path).name
            return original_path(path)
        with patch.object(prior.A,'Path',mapped):
            a.boundary_metadata(12,'popen','parent');a.boundary_metadata(12,'spawn','parent')
        baseline_tmp=tempfile.TemporaryDirectory();self.addCleanup(baseline_tmp.cleanup)
        baseline_path=Path(baseline_tmp.name)/'baseline.json';baseline_path.write_bytes(WIRE({'view':{'environment':ENV}}));baseline_path.chmod(0o600)
        plan=copy.deepcopy(PLAN);plan['font_view']['baseline']=REF(baseline_path)
        inventory=N.output_inventory(helper_runtime=runtime,original=NATIVE,plan=plan)
        self.assertEqual(len(inventory),11)
        self.assertTrue(all(row.get('sha256') for row in inventory if row['path'].startswith('font-runtime-')))
        sidecar=f.root/'paper-helper-boundary.json';metadata=json.loads(sidecar.read_bytes())
        metadata['stages'][0]['font_environment'][0]['runtime_value_sha256']='f'*64
        f.write(sidecar,metadata)
        with self.assertRaisesRegex(N.Refused,'projection_changed'):
            N.output_inventory(helper_runtime=runtime,original=NATIVE,plan=plan)
        metadata['stages'][0]['font_environment'][0]['runtime_value_sha256']=N.sha(ENV['HOME'].encode());f.write(sidecar,metadata)
        extra=f.root/'arbitrary.json';extra.write_bytes(b'{}');extra.chmod(0o600)
        with self.assertRaisesRegex(N.Refused,'unexpected_writable_output'):
            N.output_inventory(helper_runtime=runtime,original=NATIVE,plan=plan)
    def test_pidfd_guard_refuses_stale_birth_and_deadline_before_any_signal(self):
        f=self.make();f.files['request'].unlink()
        plan=copy.deepcopy(PLAN);plan['observer']['config']={'target_sha256':'2'*64}
        runtime=dict(operation_id=PLAN['operation_id'],nonce=PLAN['nonce'],operation_deadline_monotonic=f.deadline)
        f.write(f.root/'helper-runtime.json',{'runtime':runtime});f.write(f.root/'phase.json',f.phase)
        service=N.LocalServices();service.process=lambda pid:dict(namespace_pid=12,start_ticks=101,ppid=2,executable_sha256='2'*64)
        with patch.object(N.os,'pidfd_open') as openfd,patch.object(N.signal,'pidfd_send_signal') as sendsig:
            with self.assertRaisesRegex(N.Refused,'owned_process'):
                service.acquire_font_runtime(plan,NATIVE,boundary=f.boundary,deadline=f.deadline,
                    child=types.SimpleNamespace(pid=2,poll=lambda:None))
            openfd.assert_not_called();sendsig.assert_not_called()
            with self.assertRaisesRegex(N.Refused,'original_deadline'):
                service.acquire_font_runtime(plan,NATIVE,boundary=f.boundary,deadline=time.monotonic()-1,
                    child=types.SimpleNamespace(pid=2,poll=lambda:None))
            openfd.assert_not_called();sendsig.assert_not_called()

if __name__=='__main__': unittest.main(verbosity=2)
