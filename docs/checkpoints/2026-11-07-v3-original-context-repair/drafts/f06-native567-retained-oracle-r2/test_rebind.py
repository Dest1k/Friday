"""Narrow proof-rebind checks; unchanged adapter lineage/helper tests are reused."""
import copy,hashlib,json,os,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent;D=R/'candidate';OLD=P/'candidate'
S=json.loads((R/'SOURCE-SNAPSHOT.json').read_bytes());req=json.loads((P/'METADATA-REQUEST.json').read_bytes())
b=json.loads(Path(req['evidence']['native_binding']['path']).read_bytes());records=json.loads(Path(req['evidence']['records']['path']).read_bytes());forbidden={f['input']['path']for f in b['fixtures']}|{x['path']for x in records['outputs']}|{req['credential']['path']}
body_attempts=0;effect_attempts=0

def audit(event,args):
 global body_attempts,effect_attempts
 if event=='open'and isinstance(args[0],(str,bytes))and os.fsdecode(args[0])in forbidden:body_attempts+=1;raise RuntimeError('FORBIDDEN_BODY_OPEN')
 if event in ('subprocess.Popen','os.system','socket.connect','os.fork','os.posix_spawn'):effect_attempts+=1;raise RuntimeError('FORBIDDEN_EFFECT')
sys.addaudithook(audit)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
c=module(D/'f06_contract.py','f06_contract');tests=[]
def passed(name):tests.append({'name':name,'status':'PASS'})
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def refused(name,run):
 try:run()
 except ValueError as e:
  assert str(e)!='STOP_AFTER_GENUINE_ACCEPTANCE';passed(name);return
 raise AssertionError(name)
assert c.CANONICAL_ACCEPTANCE_SHA==S['Root_adapter_acceptance']['sha256']=='a55c6dde29ad229d9bd085de5a1907741e6091e8a92b706b0faaa940091fa137'
proof=c.decode(c.reference_read(S['Root_adapter_acceptance'])[0]);assert proof['source']==S['adapter'] and proof['independent_review']==S['prior_independent_review'] and proof['execution_authorized']is False;passed('genuine_Root_proof_exact_SHA_custody_schema_source_scope_review')
for key in ('prior_result','prior_snapshot','prior_unbound_source_pins','prior_independent_review','adapter','metadata_request'):assert pin(Path(S[key]['path']))==S[key]
passed('prior719c_DF3_bfbb_adapter_e1e35_request_history_unchanged')
sourcepin,actual=c.recipe_check();assert sourcepin['sha256']==S['source_pins']['sha256'];passed('changed_r2_source_pin_schema_inventory_refs_actual_proof_CAS')
assert [p['name']for p in c.decode((D/'SOURCE-PINS.json').read_bytes())['files']]==sorted(p.name for p in D.iterdir()if p.name in c.decode((D/'SOURCE-PINS.json').read_bytes())['source_set']);passed('source_set_rows_exact_order')
for n in ('callback_observer_v2.py','embedded_entry.py','inside_once.py','office_fixture_driver.py','request_args_compat_v2.py','root_frame.py','run_once.py'):assert pin(D/n)['sha256']==pin(OLD/n)['sha256']
passed('seven_runtime_helpers_exact_reused_no_retesting')
assert c.B==D and c.TASK==P and c.HANDOFF_PATH==Path(S['adapter']['path']) and c.HANDOFF_SHA==S['adapter']['sha256'];key='verify-native-edits-native567retained1';assert c.operation(key,c.MODE)==D/'operations'/key
passed('relocated_B_operation_admission_source_roots_stable_TASK_adapter')
template=json.loads((D/'verify-native-edits.ADMISSION.TEMPLATE.json').read_bytes());proof_template=json.loads((D/'ROOT-PROOFS.TEMPLATE.json').read_bytes());assert template['state']=='UNBOUND_NOT_ADMITTED'and template['task_retention_root']==str(P)and template['original_operation_start_monotonic']is None and template['slot_identity']is None and template['admitted_at_moscow']is None
assert (D/'ROOT-PROOFS.TEMPLATE.json').read_bytes()==(OLD/'ROOT-PROOFS.TEMPLATE.json').read_bytes();passed('templates_exact_inert_no_admission_fabricated')
assert c.LIMITS['max_password_probes']==6 and c.LIMITS['max_stores']==0 and c.LIMITS['whole_wall_seconds']==300 and c.LIMITS['aggregate_CPU_seconds']==180;passed('fixed_limits_and_readonly_effects_unchanged')
base_read=c.reference_read;credid=c.credential_metadata(req['credential'])[1]
a={'mode':c.MODE,'credential_source':req['credential'],'credential_source_identity':credid,'metadata_adapter_source':S['adapter'],'canonical_fix_acceptance':S['Root_adapter_acceptance'],'metadata_request':S['metadata_request']}
def guarded_read(ref,*args,**kwargs):
 if ref['path']==S['metadata_request']['path']:raise ValueError('STOP_AFTER_GENUINE_ACCEPTANCE')
 return base_read(ref,*args,**kwargs)
c.reference_read=guarded_read
try:c.output_inputs(a)
except ValueError as e:assert str(e)=='STOP_AFTER_GENUINE_ACCEPTANCE';passed('actual_Root_proof_passes_changed_consumer_before_metadata_cipher_boundary')
else:raise AssertionError('metadata_boundary')
for name,change in [
 ('acceptance_wrong_schema',lambda x:x.update(schema='old')),
 ('acceptance_wrong_state',lambda x:x.update(state='ROOT_FRESH_ONCE_ADMITTED')),
 ('acceptance_wrong_source_path',lambda x:x['source'].update(path=str(OLD/'f06_contract.py'))),
 ('acceptance_wrong_source_SHA',lambda x:x['source'].update(sha256='0'*64)),
 ('acceptance_wrong_assignment',lambda x:x.update(assignment='oldR3')),
 ('acceptance_wrong_native_operation',lambda x:x.update(native_operation_id='ASTRA-SOL-F06-NATIVE-CORE203-20261112#1')),
 ('acceptance_wrong_selected',lambda x:x.update(selected_fixture_ids=['f06-4'])),
 ('acceptance_outstanding_findings',lambda x:x.update(findings_remaining=['x'])),
 ('acceptance_runtime_authority_refused',lambda x:x.update(execution_authorized=True))]:
 mutated=copy.deepcopy(proof);change(mutated)
 def mocked_read(ref,*args,**kwargs):
  if ref['path']==S['Root_adapter_acceptance']['path']:return json.dumps(mutated).encode(),dict(S['Root_adapter_acceptance'])
  return guarded_read(ref,*args,**kwargs)
 c.reference_read=mocked_read;refused(name,lambda:c.output_inputs(a));c.reference_read=guarded_read
for name,field,val in [('admission_wrong_proof_path','path',str(P/'review/RESULT.json')),('admission_wrong_proof_SHA','sha256','0'*64)]:
 bad=copy.deepcopy(a);bad['canonical_fix_acceptance'][field]=val;refused(name,lambda:c.output_inputs(bad))
c.reference_read=base_read
assert body_attempts==effect_attempts==0
report={'schema':'friday.f06.native567-r2-rebind-source-tests.v1','state':'PASS_NARROW_SOURCE_REBIND_NO_RUNTIME_AUTHORITY','tests':tests,'passed':len(tests),'actual_cipher_credential_body_attempts':body_attempts,'actual_effect_attempts':effect_attempts,'actual_mapping_or_manifest_created':False,'old28_and_independent32_reused_not_repeated':True,'snapshot':S}
(R/'TEST-RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');(R/'TEST-RESULTS.json').chmod(0o600);print(json.dumps({'state':report['state'],'passed':len(tests),'body_attempts':body_attempts,'effects':effect_attempts}))
