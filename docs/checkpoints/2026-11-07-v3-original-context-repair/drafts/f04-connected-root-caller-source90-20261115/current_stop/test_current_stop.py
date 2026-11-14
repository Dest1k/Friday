"""Inert-only tests. No current/native/socket/file effect/authority is created."""
import copy
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).with_name('current222.py')
spec=importlib.util.spec_from_file_location('f04_current_source',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def ref(name,sha='a'*64):return {'path':'/INERT_ONLY/'+name,'bytes':1,'sha256':sha}

def fixture():
    root=dict(root_scope=m.ROOT_SCOPE,operation_id='CASE165/F04/format27-to26/P1/FXTAB',run_id='INERT_ONLY_UNSTARTED',root_authority_id='INERT_ONLY_NOT_ROOT_AUTHORITY',scenario_ref=ref('scenario'),source=ref('source',m.SOURCE_SHA),clock=ref('clock'),resources={'ordinary_seconds':300,'full_capture_seconds':180,'ack_seconds':10,'reserve_seconds':5},slot={'path':'/INERT_ONLY/slot','identity':{'inode':1},'owner':{'pid':1,'starttime':2,'pgid':1}},once={'path':'/INERT_ONLY/once','status':'ABSENT','reference':None},boundary_phase='NEW',current={'proof':ref('proof')})
    root['source']['bytes']=16538;root['source']['path']=m.SOURCE_PATH
    actual={k:{'inert':k} for k in m.CURRENT_FIELDS};actual.update(installed_product=copy.deepcopy(m.EXPECTED),databases={'A':{'manifest_sha256':'1'*64},'B':{'manifest_sha256':'2'*64}},history={'manifest_sha256':'3'*64},native_readonly={'query_id':'INERT','observed_monotonic':1,'scopes':{}},source_stat={'inert':'source_stat'},gateway={'pid':1},selected_scope={'inert':'scope'})
    proof={'schema':'frw.Root.F04.current222.v1','operator':'Root','status':'ROOT_BOUND','binding':m.binding(root),'installed_expected':copy.deepcopy(m.EXPECTED),'installed_closure':ref('closed'),'native_request':ref('request'),'native_socket_path':'/INERT_ONLY/socket','current_files':[ref('code')],'mutable_paths':[{'category':k,'path':'/INERT_ONLY/'+k} for k in ('cancel','once','recovery','action_ownership')],'root_reviews':{k:ref(k,m.SELECTION_SHA if k=='original_selection' else 'a'*64) for k in m.REVIEWS+('original_selection',)},'observed':copy.deepcopy(actual),'created_at':90,'expires_at':110,'created_monotonic':40,'expires_monotonic':60,'boot_id':'INERT_ONLY'}
    docs={root['current']['proof']['path']:proof,proof['root_reviews']['original_selection']['path']:{'execution_grant':False,'current_admission':False}}
    for key in m.REVIEWS:
        docs[proof['root_reviews'][key]['path']]={'schema':'frw.Root.F04.'+key+'.v1','operator':'Root','binding_sha256':m.digest(m.encoded(m.binding(root))),'evidence':[ref('INERT_EVIDENCE')]}
    docs['/INERT_ONLY/source_custody'].update(source_ref=root['source'],source_stat=actual['source_stat'],selected_native_scope=actual['selected_scope'],same_authorized_principal=True,root_fixture_owned=True,principal_acl_reviewed=True,unchanged_source_required=True,ordinary_ingress_existing_required=False)
    docs['/INERT_ONLY/all_profile_history_semantic_once'].update(history_manifest_sha256=actual['history']['manifest_sha256'],native_manifests={k:v['manifest_sha256'] for k,v in actual['databases'].items()},once_sha256=m.digest(m.encoded(actual['historical_once'])),mutable_paths_sha256=m.digest(m.encoded(actual['mutable_paths'])),equivalent_original_phase_effects=[],unresolved_original_phase_equivalents=[],all_profiles_and_compacted_unlogged_equivalents_reconciled=True,old_effects_UNKNOWN_and_clocks_preserved=True,retained_effects={'R98':'CONSUMED','R100':'CONSUMED','F03':'CLOSED'})
    docs['/INERT_ONLY/private_exclusion'].update(history_manifest_sha256=actual['history']['manifest_sha256'],native_manifests={k:v['manifest_sha256'] for k,v in actual['databases'].items()},current_files=actual['current_files'],private_context_sha256=m.digest(m.encoded(actual['private_context'])),current_context_files_complete_for_selected_action=True,private_inputs_not_ingested_or_product_visible=True)
    docs['/INERT_ONLY/owned_actor_stop_resources'].update(resources=root['resources'],current_files=actual['current_files'],native_implementation_sha256=m.NATIVE_SHA,cancel_state_sha256=m.digest(m.encoded(actual['cancel_state'])),mutable_paths_complete_for_action=True,cancel_root_only=True,no_old_effect_replay=True,new_effect_unconsumed=True,source_fixture_no_product_write=True)
    class InertLeaves:
        def __init__(self):self.calls=0;self.change_on_second=None
        def docref(self,r,**kwargs):return docs[r['path']]
        def readref(self,r,**kwargs):return b'INERT_ONLY'
        def now(self):return 100,50,'INERT_ONLY'
        def observe(self,r,p):
            self.calls+=1;value=copy.deepcopy(actual)
            if self.calls==2 and self.change_on_second:value[self.change_on_second]={'changed':True}
            return value
        def inventory(self,path):
            if root['once']['status']=='ABSENT':return {'state':'ABSENT','path':path}
            return {'state':'FILE','ref':root['once']['reference']}
        def resources(self,*args):pass
        def owned_stop_capability(self,root):return {'schema':'frw.source.F04.exact-owned-stop-capability.v1','implemented':True,'native_implementation_sha256':m.NATIVE_SHA,'dispatch_source':ref('INERT_DISPATCH'),'projection_source':ref('INERT_PROJECTION',m.NATIVE_SHA)}
    return root,proof,actual,docs,InertLeaves()

class CurrentControls(unittest.TestCase):
    def test_positive_inert_current(self):
        r,p,a,d,l=fixture();v=m.current_gate(r,l);self.assertTrue(v['matched']);self.assertFalse(v['admission']);self.assertFalse(v['runtime_acceptance']);self.assertEqual(l.calls,2)
    def test_unbound_refuses_before_leaves(self):
        r,p,a,d,l=fixture();r['current']=None
        with self.assertRaisesRegex(m.Refused,'CURRENT_UNBOUND'):m.current_gate(r,l)
        self.assertEqual(l.calls,0)
    def test_221_does_not_grant222(self):
        r,p,a,d,l=fixture();a['installed_product']['source_layers']=221;p['observed']=copy.deepcopy(a)
        with self.assertRaisesRegex(m.Refused,'ACTUAL_INSTALLED222'):m.current_gate(r,l)
    def test_source_only_cannot_qualify(self):
        r,p,a,d,l=fixture();p['status']='SOURCE_ONLY'
        with self.assertRaisesRegex(m.Refused,'FRESH_CURRENT'):m.current_gate(r,l)
    def test_current_cas_drift(self):
        r,p,a,d,l=fixture();l.change_on_second='gateway'
        with self.assertRaisesRegex(m.Refused,'FINAL_CURRENT_CAS_CHANGED_gateway'):m.current_gate(r,l)
    def test_cancel_drift(self):
        r,p,a,d,l=fixture();a['cancel_state']={'changed':True}
        with self.assertRaisesRegex(m.Refused,'CURRENT_CAS_CHANGED_cancel'):m.current_gate(r,l)
    def test_permission_denied(self):
        r,p,a,d,l=fixture();d['/INERT_ONLY/source_custody']['principal_acl_reviewed']=False
        with self.assertRaisesRegex(m.Refused,'CUSTODY_PERMISSION'):m.current_gate(r,l)
    def test_private_exposure(self):
        r,p,a,d,l=fixture();d['/INERT_ONLY/private_exclusion']['private_inputs_not_ingested_or_product_visible']=False
        with self.assertRaisesRegex(m.Refused,'PRIVATE_CONTEXT'):m.current_gate(r,l)
    def test_semantic_prior_effect(self):
        r,p,a,d,l=fixture();d['/INERT_ONLY/all_profile_history_semantic_once']['equivalent_original_phase_effects']=['INERT_prior']
        with self.assertRaisesRegex(m.Refused,'SEMANTIC_NONREPLAY'):m.current_gate(r,l)
    def test_selection_not_admission(self):
        r,p,a,d,l=fixture();d['/INERT_ONLY/original_selection']['execution_grant']=True
        with self.assertRaisesRegex(m.Refused,'SELECTION_MUST_NOT'):m.current_gate(r,l)
    def test_expired_proof(self):
        r,p,a,d,l=fixture();p['expires_at']=99
        with self.assertRaisesRegex(m.Refused,'PROOF_EXPIRED'):m.current_gate(r,l)
    def test_dynamic_slot_holder_not_static_binding(self):
        r,p,a,d,l=fixture();r['slot']['owner']={'pid':77,'starttime':88,'pgid':77};self.assertTrue(m.current_gate(r,l)['matched'])
    def test_consumed_once_exact_same_effect(self):
        r,p,a,d,l=fixture();r['boundary_phase']='CURSOR_AUTHORITY';r['once'].update(status='CONSUMED',reference=ref('once'))
        d['/INERT_ONLY/once']={'schema':'frw.Root.F04.once.v1','operator':'Root','root_authority_id':r['root_authority_id'],'run_id':r['run_id'],'operation_id':r['operation_id'],'scenario_sha256':r['scenario_ref']['sha256'],'source_sha256':r['source']['sha256'],'no_retry':True}
        self.assertTrue(m.current_gate(r,l)['matched']);d['/INERT_ONLY/once']['run_id']='OTHER'
        with self.assertRaisesRegex(m.Refused,'ONCE_EFFECT_CHANGED'):m.current_gate(r,l)
    def test_import_inert(self):
        tree=__import__('ast').parse(p.read_bytes());self.assertFalse(any(isinstance(x,(__import__('ast').Expr,)) and isinstance(x.value,__import__('ast').Call) for x in tree.body))

def native_fixture(active=True):
    root,proof,actual,docs,leaves=fixture()
    clock={'schema':'frw.Root.F04.original-clock.v1','operator':'Root','operation_id':root['operation_id'],'run_id':root['run_id'],'boot_id':'INERT_ONLY','origin_wall':50,'origin_monotonic':0,'deadline_wall':300,'deadline_monotonic':250,'cleanup_deadline_wall':300,'cleanup_deadline_monotonic':250}
    docs[root['clock']['path']]=clock
    scope={'session_id':'INERT_SESSION','session_key':'INERT_SCOPE','native_session_generation':3};gateway={'pid':33,'start_time':44,'boot_id':'INERT_ONLY'}
    owner={'native_ownership':{'gateway':gateway,'selected_scope':scope},'clock':clock,'run_id':root['run_id'],'operation_id':root['operation_id'],'actor':{'pid':123,'starttime':456,'pgid':123}}
    received={'ownership':owner,'sent_message_id':2789}
    target={'session_id':'INERT_SESSION','session_key':'INERT_SCOPE','generation':4,'lease':{'session_id':'INERT_SESSION','owner_key':'INERT_SCOPE','generation':4,'released':False},'event_message_id':'4895','ctx_inbound_message_id':4895}
    snapshot=dict(schema='frw.gateway.ordinary-turn-readonly.v1',read_only=True,answering_pid=33,birth_ticks=44,boot_id='INERT_ONLY',implementation_sha256=m.NATIVE_SHA,session_id='INERT_SESSION',session_key='INERT_SCOPE',generation=4,active=True,active_session_keys=['INERT_SCOPE'],turn_tokens=[target['lease']],event_message_id='4895',ctx_inbound_message_id=4895,ctx_generation=4,pending_messages=0,active_adapters=1,adapter_generations=[4],queued_events=0,pending_command=False,approvals=False,detached_owned_work=False,live_owned_delegations=0,durable_pending_delegations=0,web_custody={'status':'QUIESCENT','sessions':[],'recovery_blocked':False},terminal_custody={'status':'QUIESCENT','sessions':[],'recovery_blocked':False},own_web_inflight={'session_id':'INERT_SESSION','session_key':'INERT_SCOPE','generation':4,'recovery_blocked':False,'sessions':[],'unretained_calls':[],'event_message_id':None,'task_id':None,'turn_id':None,'user_authority':None})
    idle=copy.deepcopy(snapshot);idle['generation']=5;idle['own_web_inflight']['generation']=5;idle['active_adapters']=0;idle['adapter_generations']=[]
    for key in ('active','pending_command','approvals','detached_owned_work'):idle[key]=False
    for key in ('active_session_keys','turn_tokens'):idle[key]=[]
    for key in ('event_message_id','ctx_inbound_message_id','ctx_generation'):idle[key]=None
    bridge={'schema':'frw.source.F04.correlated-owned-tuple.v1','root_binding_sha256':m.digest(m.encoded(m.binding(root))),'evidence':[ref('INERT_NATIVE_EVIDENCE')],'target':target,'tester_message_id':2789,'source_sha256':root['source']['sha256'],'scenario_sha256':root['scenario_ref']['sha256'],'NO_RUNTIME_TERMINAL_BRIDGE':True}
    leaves.stop_calls=0;leaves.snap_calls=0
    def owned_snapshot(r,o):
        leaves.snap_calls+=1
        return copy.deepcopy(snapshot if active and leaves.snap_calls==1 else idle)
    def stop_exact(r,t,o):leaves.stop_calls+=1;return {'accepted':True,'sent_once':True,'transport':'existing_gateway_control_socket','session_id':t['session_id'],'generation_before':t['generation'],'generation_after':t['generation']+1,'native_dispatch_id':'a'*64,'settlement':'REQUIRES_FRESH_INDEPENDENT_OBSERVATION','telegram_stop_message_created':False}
    leaves.owned_snapshot=owned_snapshot;leaves.correlation_bridge=lambda *args:bridge;leaves.stop_exact=stop_exact;leaves.received_custody=lambda *args:dict(full180=True,actual_artifact_join=True,actor_absent=True,canonical_locks_free=True)
    return root,received,snapshot,idle,bridge,leaves

class NativeControls(unittest.TestCase):
    def test_production_readiness_fails_before_current_observation(self):
        r,p,a,d,l=fixture();l.owned_stop_capability=m.RuntimeLeaves().owned_stop_capability
        with self.assertRaisesRegex(m.Refused,'F04_STOP_API_SCOPE_UNSUPPORTED'):m.current_gate(r,l)
        self.assertEqual(l.calls,0)
    def test_different_message_namespaces_correlate_by_bridge(self):
        r,v,s,i,b,l=native_fixture();self.assertEqual(m.correlate_owned_tuple(r,v,s,b)['event_message_id'],'4895');self.assertEqual(v['sent_message_id'],2789)
    def test_foreign_active_native_turn_refuses(self):
        r,v,s,i,b,l=native_fixture();s['event_message_id']=9999
        with self.assertRaisesRegex(m.Refused,'NOT_CORRELATED_OWNED'):m.correlate_owned_tuple(r,v,s,b)
    def test_generic_idle_does_not_prove_own_completion(self):
        r,v,s,i,b,l=native_fixture(False);b.pop('NO_RUNTIME_TERMINAL_BRIDGE')
        with self.assertRaisesRegex(m.Refused,'TYPED_TERMINAL_BRIDGE_UNAVAILABLE'):m.correlate_owned_tuple(r,v,i,b)
    def test_no_ingress_summary_no_stop(self):
        r,v,s,i,b,l=native_fixture();out=m.stop_owned(r,v['ownership'],l);self.assertFalse(out['confirmed']);self.assertEqual(l.stop_calls,0)
    def test_stop_once_exact_correlated_target(self):
        r,v,s,i,b,l=native_fixture();out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(out['assertcode'],'F04_TYPED_TERMINAL_BRIDGE_UNAVAILABLE');self.assertEqual(l.stop_calls,1)
    def test_foreign_stop_never_sent(self):
        r,v,s,i,b,l=native_fixture();s['turn_tokens']=['FOREIGN'];out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(l.stop_calls,0)
    def test_uncertain_stop_not_retried(self):
        r,v,s,i,b,l=native_fixture()
        def uncertain(*args):l.stop_calls+=1;return {'accepted':False}
        l.stop_exact=uncertain;out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(l.stop_calls,1);self.assertFalse(out['retry_authorized'])
    def test_artifact_booleans_do_not_replace_terminal_bridge(self):
        r,v,s,i,b,l=native_fixture(False);l.received_custody=lambda *args:dict(full180=True,actual_artifact_join=False,actor_absent=True,canonical_locks_free=True);out=m.owned_closure(r,v,l);self.assertFalse(out['closed'])
    def test_idle_with_no_typed_bridge_remains_unconfirmed(self):
        r,v,s,i,b,l=native_fixture(False);self.assertFalse(m.owned_closure(r,v,l)['closed'])
    def test_post_fixed_cleanup_valid_but_terminal_gap_remains(self):
        r,v,s,i,b,l=native_fixture(False);l.now=lambda:(200,150,'INERT_ONLY');self.assertGreater(m.cleanup_remaining(r,v['ownership'],l),0);out=m.owned_closure(r,v,l);self.assertFalse(out['closed']);self.assertEqual(out['assertcode'],'F04_TYPED_TERMINAL_BRIDGE_UNAVAILABLE')
    def test_expired_cleanup_refuses_without_stop(self):
        r,v,s,i,b,l=native_fixture();l.now=lambda:(400,350,'INERT_ONLY');out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(l.stop_calls,0)

class CapturedSourceControls(unittest.TestCase):
    def test_exact_captured_api_verified_but_f04_scope_unsupported(self):
        value=m.inspect_owned_stop_source();self.assertTrue(value['source_verified']);self.assertFalse(value['implemented']);self.assertFalse(value['F04_relabel_permitted']);self.assertEqual(value['captured_verb'],'ordinary-turn-cancel');self.assertFalse(value['typed_ingress_artifact_terminal_bridge'])
    def test_source_pin_cannot_be_overridden_by_root_json(self):
        r,p,a,d,l=fixture();r['current']['stop_allowed']=True
        with self.assertRaisesRegex(m.Refused,'CURRENT_UNBOUND'):m.current_gate(r,l)
    def test_changed_capture_pin_refuses(self):
        old=m.PROJECTION_SOURCE
        try:
            m.PROJECTION_SOURCE=dict(old,sha256='0'*64)
            with self.assertRaisesRegex(m.Refused,'CAPTURE_PIN_CHANGED'):m.inspect_owned_stop_source()
        finally:m.PROJECTION_SOURCE=old
    def test_actual_tokens_are_lease_dicts(self):
        r,v,s,i,b,l=native_fixture();s['turn_tokens']=['STRING_TOKEN']
        with self.assertRaisesRegex(m.Refused,'NOT_CORRELATED_OWNED'):m.correlate_owned_tuple(r,v,s,b)
    def test_native_event_ctx_cancel_race_refuses(self):
        r,v,s,i,b,l=native_fixture();s['ctx_inbound_message_id']=9999
        with self.assertRaisesRegex(m.Refused,'NOT_CORRELATED_OWNED'):m.correlate_owned_tuple(r,v,s,b)
    def test_attempted_60_second_extension_refuses(self):
        r,v,s,i,b,l=native_fixture();v['ownership']['clock']['cleanup_deadline_wall']+=60;v['ownership']['clock']['cleanup_deadline_monotonic']+=60
        with self.assertRaisesRegex(m.Refused,'FIXED_CLEANUP_ENDPOINTS_CHANGED'):m.cleanup_remaining(r,v['ownership'],l)
    def test_post_cancel_new_generation_is_only_resource_quiescence(self):
        r,v,s,i,b,l=native_fixture(False);self.assertEqual(i['generation'],b['target']['generation']+1);self.assertTrue(m.native_resources_closed(i,b['target']))
        with self.assertRaisesRegex(m.Refused,'TYPED_TERMINAL_BRIDGE_UNAVAILABLE'):m.correlate_owned_tuple(r,v,i,b)

class StopGenerationControls(unittest.TestCase):
    def test_success_receipt_must_invalidate_generation(self):
        r,v,s,i,b,l=native_fixture();original=l.stop_exact
        def no_invalidation(*args):
            result=original(*args);result['generation_after']=result['generation_before'];return result
        l.stop_exact=no_invalidation;out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(out['assertcode'],'F04_EXACT_OWNED_STOP_UNCONFIRMED');self.assertEqual(l.stop_calls,1)
    def test_post_generation_must_match_accepted_receipt(self):
        r,v,s,i,b,l=native_fixture();i['generation']=6;i['own_web_inflight']['generation']=6
        out=m.stop_owned(r,dict(v['ownership'],received=v),l);self.assertFalse(out['confirmed']);self.assertEqual(out['assertcode'],'F04_OWNED_STOP_POST_GENERATION_CAS_CHANGED');self.assertEqual(l.stop_calls,1)

if __name__=='__main__':unittest.main()
