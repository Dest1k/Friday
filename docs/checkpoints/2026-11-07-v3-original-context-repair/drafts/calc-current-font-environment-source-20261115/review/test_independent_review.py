"""Independent pure/mock nearest-caller controls; no actor, signal or namespace."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parent.parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
B=load('review_transcript_fixture',BASE/'tests/test_font_runtime_boundaries.py')
N=B.N; I=B.I
O=load('review_actual_outer',BASE/'candidate/outer/outer_runner.py')
OLD=load('review_legacy_inner',BASE/'before/inner/inner_client.py')
FROZEN_INNER=load('review_frozen_inner',BASE/'frozen/inner/inner_client.py')
FROZEN_OUTER=load('review_frozen_outer',BASE/'frozen/outer/outer_runner.py')
S=load('review_reused_inert_config',Path('/home/jericho/.cache/FRW-ASTRA-PAPER-RUNTIME-ENVIRONMENT-SOURCE-20261115/tests/test_semantics.py'))
ACTUAL_ENV=json.loads((BASE/'candidate/outer/font_view/baseline.json').read_bytes())['view']['environment']
B.ENV=ACTUAL_ENV
LOGICAL=Path('/tmp/friday-metric-work')

class IndependentReview(unittest.TestCase):
    def ownroot(self):
        tmp=tempfile.TemporaryDirectory(dir=BASE,prefix='control-');self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);root.chmod(0o700);return root
    def pair(self,root,boundary,deadline=None,logical=False):
        f=B.HeldFixture(root,boundary)
        if deadline is not None:
            f.deadline=deadline;f.request['deadline_monotonic']=deadline;f.helper.b['runtime']['operation_deadline_monotonic']=deadline
            f.write(f.files['request'],f.request)
        with patch.object(N,'WORK',root): f.run()
        if logical:
            refs=lambda kind,raw:dict(path=str(LOGICAL/f.files[kind].name),sha256=N.sha(raw))
            req=f.files['request'].read_bytes();proof=json.loads(f.files['proof'].read_bytes())
            proof['request_ref']=refs('request',req);proofraw=B.WIRE(proof);f.files['proof'].write_bytes(proofraw)
            view=json.loads(f.files['view'].read_bytes());view['office_font_environment_proof']=refs('proof',proofraw)
            viewraw=B.WIRE(view);f.files['view'].write_bytes(viewraw)
            release=json.loads(f.files['release'].read_bytes());release.update(request_ref=refs('request',req),proof_ref=refs('proof',proofraw),font_view_ref=refs('view',viewraw))
            relraw=B.WIRE(release);f.files['release'].write_bytes(relraw)
            ack=json.loads(f.files['accepted'].read_bytes());ack['release_ref']=refs('release',relraw);f.files['accepted'].write_bytes(B.WIRE(ack))
        return f
    def execute_inner(self,m,helper=False):
        c=S.inner_config();events=[];memory={};handler=types.SimpleNamespace(requests=0,instance_token='OWN')
        if helper:
            c['load_dependency']=copy.deepcopy(S.RUNTIME);c['load_dependency']['operation_deadline_monotonic']=time.monotonic()+30
        def write(path,value):memory[path]=copy.deepcopy(value);events.append(('write',value.get('phase',value.get('stage',value.get('state')))))
        class Doc:
            def isReadonly(self):return True
            def isModified(self):return False
            def close(self,ownership):events.append(('readonly_close',ownership))
        class Desktop:
            def loadComponentFromURL(self,*args):events.append(('load',));return Doc()
            def terminate(self):events.append(('terminate',));return True
        runtime=dict(handler=handler,desktop=Desktop(),remote_context=None,property_value_factory=lambda k,v:(k,v),descriptor_factory=None,endpoint='OWN_INERT')
        def qualify(*args,**kwargs):
            for index in range(10):
                kwargs['before_digit'](index,str(index));kwargs['after_digit'](index,str(index),index+10)
            events.append(('font_restored',));return dict(actual_M=None,runtime_attested=False,measurement=dict(native_font_restore_completed=True,digit_widths=list(range(10,20))))
        q=dict(validate_preload_inputs=lambda *a:None,qualify_and_observe=qualify)
        pre=dict(source={'sha256':S.MANIFEST['source_sha256']},working_copy={'url':'file:///OWN/INERT/never-opened.xlsx'})
        loaded=dict(load_request=None,process=dict(pid=12,start_ticks=100,executable_sha256='2'*64),startup_locale_environment=None,native_transport=dict(mode='RAW32_POSTQUERY_NATIVE_JOIN'))
        def supplier(*args):
            loaded['load_request']=memory[c['paths']['checkpoint']]['load_request'];return loaded,'f'*64
        old_callbacks=m.PhaseCallbacks
        def callbacks(config,write):return old_callbacks(config,write=write,read=lambda path:memory[path])
        with patch.dict(os.environ,m.START_ENV),patch.object(m,'PhaseCallbacks',callbacks):
            result=m.execute_inner(c,modules=dict(qualifier=q,resolver=dict(resolve_font_recipe=None),leaf=dict(observe_reference_metric=None)),preload=(pre,'f'*64),runtime_factory=lambda c:runtime,identity_observer=lambda c:{'own':True},loaded_supplier=supplier,readiness=lambda:None,write=write,claim=lambda c:None)
        return result,events
    def test_generic_nohelper_actual_execute_inner_remains_legacy(self):
        old,old_events=self.execute_inner(OLD)
        frozen,frozen_events=self.execute_inner(FROZEN_INNER)
        new,new_events=self.execute_inner(I)
        self.assertEqual(old['status'],'CANDIDATE_UNATTESTED_OUTER_POSTCONDITIONS_REQUIRED')
        self.assertEqual(frozen['status'],'REFUSED')
        self.assertEqual(frozen['error']['phase'],'READONLY_CLOSE')
        self.assertEqual(frozen['error']['reason'],'current_font_runtime_close_release_required')
        self.assertIn(('font_restored',),frozen_events)
        self.assertIn(('readonly_close',False),frozen_events)
        self.assertEqual(new['status'],old['status']);self.assertEqual(new_events,old_events)
        self.assertIsNone(new['actual_M']);self.assertFalse(new['runtime_attested'])
        self.assertLess(new_events.index(('font_restored',)),new_events.index(('readonly_close',False)))
        self.assertLess(new_events.index(('readonly_close',False)),new_events.index(('write','CLOSED')))
        self.assertLess(new_events.index(('write','CLOSED')),new_events.index(('terminate',)))
    def test_helper_actual_execute_inner_still_requires_acceptance_after_close(self):
        with patch.object(I,'wait_json',side_effect=I.Refused('OWN_ACCEPTANCE_NOT_PROVIDED')) as waiter:
            result,events=self.execute_inner(I,True)
        waiter.assert_called_once();self.assertEqual(result['status'],'REFUSED')
        self.assertEqual(result['error']['phase'],'READONLY_CLOSE')
        self.assertEqual(result['error']['reason'],'OWN_ACCEPTANCE_NOT_PROVIDED')
        self.assertNotIn(('write','DESKTOP_TERMINATE'),events)
        self.assertEqual(sum(e==('terminate',) for e in events),1)  # Existing refused cleanup, not successful lifecycle.
    def actual_plan(self):
        checkpoint=json.loads(Path('/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/PREPARED-OFFICE-FONT-BOUNDARY-FREEZE1-IDENTITY.json').read_bytes())
        return json.loads(O.read_pinned(checkpoint['plan_ref'],private=True))
    def test_actual_static_plan_helper_present_and_missing_rejected_before_effects(self):
        plan=self.actual_plan()
        with patch.object(O,'acquire_existing_slot',side_effect=AssertionError('NO_SLOT_OR_EFFECT_ALLOWED')):
            result=O.inspect_plan(plan)
            self.assertEqual(result['status'],'SOURCE_INPUTS_INSPECTED_NO_GRANT')
            del plan['observer']['load_dependency'];del plan['inner_input']['load_dependency']
            self.assertEqual(FROZEN_OUTER.inspect_plan(plan)['status'],'SOURCE_INPUTS_INSPECTED_NO_GRANT')
            with self.assertRaisesRegex(O.Refused,'current_font_runtime_getter_requires_pinned_helper_bundle'):O.inspect_plan(plan)
    def test_all_fifteen_actual_baseline_hashes_are_enforced(self):
        root=self.ownroot();f=self.pair(root,'AFTER_LOAD_BEFORE_QUERY')
        proof=json.loads(f.files['proof'].read_bytes());N.validate_font_projection(proof['font_environment'],ACTUAL_ENV)
        self.assertEqual(set(ACTUAL_ENV),set(N.FONT_ENV_KEYS))
        helper_rows=[dict(key=key,initial_value_sha256=N.sha(value.encode()) if value is not None else None,
            runtime_value_sha256=N.sha(value.encode()) if value is not None else None) for key,value in ACTUAL_ENV.items()]
        helper_rows.sort(key=lambda row:N.FONT_ENV_KEYS.index(row['key']))
        N.validate_font_projection(helper_rows,ACTUAL_ENV,helper=True)
        for key in N.FONT_ENV_KEYS:
            rows=copy.deepcopy(proof['font_environment'])
            next(row for row in rows if row['key']==key)['value_sha256']='f'*64
            with self.subTest(key=key),self.assertRaisesRegex(N.Refused,'projection_changed'):N.validate_font_projection(rows,ACTUAL_ENV)
            for field in ('initial_value_sha256','runtime_value_sha256'):
                changed=copy.deepcopy(helper_rows);next(row for row in changed if row['key']==key)[field]='f'*64
                with self.subTest(helper_key=key,field=field),self.assertRaisesRegex(N.Refused,'projection_changed'):
                    N.validate_font_projection(changed,ACTUAL_ENV,helper=True)
    def test_acquire_positive_sends_only_one_mocked_birth_bound_pidfd_signal(self):
        root=self.ownroot();f=self.pair(root,'AFTER_LOAD_BEFORE_QUERY')
        template=json.loads(f.files['proof'].read_bytes())
        for path in f.files.values():path.unlink()
        plan=copy.deepcopy(B.PLAN);plan['observer']['config']={'target_sha256':'2'*64}
        baseline=root/'baseline.json';f.write(baseline,{'view':{'environment':ACTUAL_ENV}});plan['font_view']['baseline']=B.REF(baseline)
        f.write(root/'helper-runtime.json',{'runtime':dict(operation_id=plan['operation_id'],nonce=plan['nonce'],operation_deadline_monotonic=f.deadline)})
        f.write(root/'phase.json',f.phase)
        process=dict(namespace_pid=12,start_ticks=100,ppid=2,executable_sha256='2'*64,namespaces={'pid':'OWN'},boot_id='OWN')
        service=N.LocalServices();service.process=lambda pid:copy.deepcopy(process)
        def sent(*args):
            self.assertTrue(f.files['request'].is_file());self.assertFalse(f.files['proof'].exists())
            request=json.loads(f.files['request'].read_bytes());proof=copy.deepcopy(template)
            proof['supervisor']=request['supervisor'];proof['request_ref']=B.REF(f.files['request']);f.write(f.files['proof'],proof)
        original_close=os.close;closed=[]
        def close(fd):
            if fd==999999:closed.append(fd)
            else:original_close(fd)
        with patch.object(N,'WORK',root),patch.object(N.os,'pidfd_open',return_value=999999) as openfd,patch.object(N.signal,'pidfd_send_signal',side_effect=sent) as sendsig,patch.object(N.os,'close',side_effect=close),patch.object(N.os,'kill',side_effect=AssertionError('GENERIC_SIGNAL_FORBIDDEN')):
            held=service.acquire_font_runtime(plan,B.NATIVE,boundary=f.boundary,deadline=f.deadline,child=types.SimpleNamespace(pid=2,poll=lambda:None))
        openfd.assert_called_once_with(12,0);sendsig.assert_called_once_with(999999,N.signal.SIGSTOP,None,0)
        self.assertEqual(closed,[999999]);self.assertEqual(held['office_process'],process)
        self.assertEqual(held['request']['deadline_monotonic'],f.deadline);self.assertEqual(held['request']['supervisor']['pid'],os.getpid())
        self.assertFalse(f.files['release'].exists());self.assertFalse(f.files['accepted'].exists())
    def final_font_consumer(self,root,loaded,closed):
        tree=ast.parse((BASE/'candidate/outer/outer_runner.py').read_bytes())
        def find_block(node):
            for field,value in ast.iter_fields(node):
                if isinstance(value,list) and value and all(isinstance(n,ast.stmt) for n in value):
                    starts=[i for i,n in enumerate(value) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='font_checker' for t in n.targets)]
                    if starts:
                        start=starts[0];end=next(i for i in range(start+1,len(value)) if isinstance(value[i],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='trace_raw' for t in value[i].targets));return value[start:end]
            for child in ast.iter_child_nodes(node):
                result=find_block(child)
                if result:return result
        block=find_block(tree);self.assertTrue(block)
        baseline=root/'actual-baseline.json';baseline.write_bytes(B.WIRE({'view':{'environment':ACTUAL_ENV}}));baseline.chmod(0o600)
        deadline=loaded.deadline;started=deadline-10
        plan=dict(work_dir=str(root),namespace_entry=B.REF(BASE/'candidate/outer/namespace_entry.py'),font_view=dict(B.PLAN['font_view'],baseline=B.REF(baseline)),nonce=B.PLAN['nonce'],operation_id=B.PLAN['operation_id'],observer=B.PLAN['observer'],budgets=dict(wall_seconds=12,cleanup_seconds=2))
        loaded_view=json.loads(loaded.files['view'].read_bytes());closed_view=json.loads(closed.files['view'].read_bytes())
        ns=dict(O.__dict__,plan=plan,operation_started=started,supervisor_binding=dict(nspid=[111],start_ticks=222),cas_observations=[dict(namespace_process=dict(ppid=0)),{},loaded_view,closed_view],host_binding=dict(native_process=B.NATIVE))
        exec(compile(ast.Module(body=block,type_ignores=[]),str(BASE/'candidate/outer/outer_runner.py'),'exec'),ns)
    def test_exact_actual_outer_final_new_consumer_joins_both_points(self):
        root=self.ownroot();loaded=self.pair(root,'AFTER_LOAD_BEFORE_QUERY',logical=True)
        closed=self.pair(root,'AFTER_READONLY_CLOSE',deadline=loaded.deadline,logical=True)
        self.final_font_consumer(root,loaded,closed)
        ack=json.loads(closed.files['accepted'].read_bytes());ack['nonce']='f'*32;closed.write(closed.files['accepted'],ack)
        with self.assertRaisesRegex(Exception,'font_runtime_pair_CAS_binding'):self.final_font_consumer(root,loaded,closed)
    def test_namespace_actual_CAS_callable_requires_held_proof_and_has_no_release(self):
        root=self.ownroot();f=self.pair(root,'AFTER_READONLY_CLOSE')
        f.files['release'].unlink();f.files['accepted'].unlink();f.files['view'].unlink()
        process=dict(namespace_pid=12,start_ticks=100,ppid=2,namespaces={'pid':'OWN'},boot_id='OWN')
        me=dict(namespace_pid=111,start_ticks=222,ppid=0,namespaces={'pid':'OWN'},boot_id='OWN')
        held=dict(request=f.request,proof=json.loads(f.files['proof'].read_bytes()),proof_ref=B.REF(f.files['proof']),office_process=process)
        baseline=root/'cas-baseline.json';f.write(baseline,{'view':{'environment':ACTUAL_ENV}})
        code=("from pathlib import Path\ndef validate_effective_font_config_view(baseline, **kw):\n    assert not Path("+repr(str(f.files['release']))+").exists()\n    return "+repr(dict(view_sha256=B.PLAN['font_view']['expected_view_sha256'],observation=dict(status='metadata_cas_pass_with_critical_rehash')))+"\n").encode()
        consumer=root/'synthetic_cas.py';consumer.write_bytes(code);consumer.chmod(0o600)
        empty=root/'empty.json';f.write(empty,{})
        plan=copy.deepcopy(B.PLAN);plan['font_view'].update(consumer=B.REF(consumer),baseline=B.REF(baseline),provenance_ref=B.REF(empty),derived_cache=B.REF(empty))
        service=N.LocalServices();service.process=lambda pid:copy.deepcopy(me if pid==os.getpid() else process)
        with patch.object(N,'WORK',root),patch.object(N,'address_space_memory',return_value={'VmRSS':1024,'VmHWM':2048}):
            result=service.font_view_observation(plan,phase=f.boundary,office_pid=12,font_runtime=held)
            self.assertEqual(result['office_font_environment_proof'],held['proof_ref']);self.assertEqual(result['office_font_environment'],ACTUAL_ENV)
            f.write(f.files['release'],{})
            with self.assertRaisesRegex(N.Refused,'font_runtime_CAS_not_held'):service.font_view_observation(plan,phase=f.boundary,office_pid=12,font_runtime=held)
            f.files['release'].unlink()
            with self.assertRaisesRegex(N.Refused,'actual_runtime_font_environment_required'):service.font_view_observation(plan,phase=f.boundary,office_pid=12,font_runtime=None)
    def test_native_main_dispatch_and_cleanup_preserve_first_refusal(self):
        tree=ast.parse((BASE/'candidate/outer/deps/native_return_observer.py').read_bytes())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fail')
        state=dict(error='FIRST_REQUEST_REFUSAL',status='REFUSED');ns=dict(STATE=state,save=lambda:None)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-fail>','exec'),ns);ns['fail']('SECOND_CLEANUP_REFUSAL')
        self.assertEqual(state['error'],'FIRST_REQUEST_REFUSAL')
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        loop=next(n for n in ast.walk(main) if isinstance(n,ast.While))
        text=ast.unparse(loop)
        self.assertLess(text.index('helper.dispatch()'),text.index("'helper_metric_stop_collision'"))
        self.assertLess(text.index("'helper_metric_stop_collision'"),text.index('capture_font_runtime()'))
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='capture_font_runtime' for n in ast.walk(main)),1)

if __name__=='__main__':unittest.main(verbosity=2)
