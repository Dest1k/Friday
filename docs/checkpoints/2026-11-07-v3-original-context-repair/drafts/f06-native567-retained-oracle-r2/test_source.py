"""Finite source-only checks; actual ciphertext/credential content opens denied."""
import copy,hashlib,json,os,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
req=json.loads((P/'METADATA-REQUEST.json').read_bytes())
binding=json.loads(Path(req['evidence']['native_binding']['path']).read_bytes())
records=json.loads(Path(req['evidence']['records']['path']).read_bytes())
forbidden={f['input']['path']for f in binding['fixtures']}|{o['path']for o in records['outputs']}|{req['credential']['path']}
opens=[]
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  name=os.fsdecode(args[0]);opens.append(name)
  if name in forbidden:raise RuntimeError('FORBIDDEN_BODY_OPEN')
sys.addaudithook(audit)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
m=module(P/'native567_handoff.py','handoff')
results=[]
def passed(name):results.append({'name':name,'status':'PASS'})
def refusal(name,run):
 try:run()
 except Exception as error:
  if isinstance(error,RuntimeError)and str(error)=='FORBIDDEN_BODY_OPEN':raise
  passed(name);return
 raise AssertionError(name)
h,credential,evidence,proofs=m.inspect_metadata(req);passed('actual_exact_metadata_lineage_no_body_opens')
for name,mut in [
 ('selected_old4',lambda q:q.update(selected_fixture_ids=['f06-4'])),
 ('selected_latest7',lambda q:q.update(selected_fixture_ids=['f06-5','f06-6','f06-7'])),
 ('selected_reversed',lambda q:q.update(selected_fixture_ids=['f06-6','f06-5'])),
 ('old_assignment',lambda q:q.update(native_assignment=h.ASSIGNMENT)),
 ('old_operation',lambda q:q.update(native_operation_id=evidence['original_binding']['operation_id'])),
 ('fake_grant_path',lambda q:q['evidence']['native_root_grant'].update(path=q['evidence']['original_grant']['path'])),
 ('missing_original_once',lambda q:q['evidence'].pop('original_once')),
 ('extra_authority_field',lambda q:q.update(execution_authorized=True)),
 ('wrong_credential_digest',lambda q:q['credential'].update(sha256='0'*64)),
 ('bool_selected',lambda q:q.update(selected_fixture_ids=[True,'f06-6']))]:
 q=copy.deepcopy(req);mut(q);refusal(name,lambda:m.inspect_metadata(q))
# Mock only ciphertext custody reader, retaining all actual nonsecret evidence checks.
count=0
source_pins={}
for f,pin in zip(binding['fixtures'],binding['input_custody']):
 d=pin['identity'];source_pins[f['input']['path']]={**f['input'],'uid':d[3],'gid':d[4],'mode':'0600','dev':d[0],'ino':d[1],'nlink':d[5],'mtime_ns':d[7],'ctime_ns':d[8]}
output_pins={}
for i,row in enumerate(records['outputs']):output_pins[row['path']]={**{k:row[k]for k in ('path','bytes','sha256')},'uid':os.getuid(),'gid':os.getgid(),'mode':'0600','dev':2050,'ino':90000000+i,'nlink':1,'mtime_ns':100+i,'ctime_ns':100+i}
def fake_cipher(h,ref,cred):
 global count
 count+=1;need=source_pins.get(ref['path'])or output_pins[ref['path']];assert all(need[k]==ref[k]for k in ('path','bytes','sha256'));return dict(need)
m.cipher_ref=fake_cipher
manifest=m.build(req);assert count==8 and manifest['selected_fixture_ids']==['f06-5','f06-6']and manifest['native_operation_id']==binding['operation_id']and manifest['expected_Office_password_probes']==6 and manifest['expected_Office_stores']==0;passed('mocked_cipher_full_manifest_and_second_CAS')
# Mutations of genuine receipt/lineage data through mocked metadata reader are rejected.
real_helper=m.helper
for name,change in [
 ('correct_edit_source_join',lambda e:e['observations'][0]['receipts']['correct_edit'].update(source_sha256='0'*64)),
 ('create_only_receipt',lambda e:e['observations'][0]['receipts']['correct_edit'].update(create_only=False)),
 ('new_grant_is_old_authority',lambda e:e['native_root_grant'].update(old_grant_reused_as_authority=True)),
 ('new_grant_entire_intent',lambda e:e['native_root_grant']['intent'].pop('root_admission')),
 ('new_once_consumed_join',lambda e:e['native_once'].update(effect='BOUND_NATIVE_QUALIFICATION')),
 ('latest_fail_cannot_promote',lambda e:e['observations'][2].update(status='NATIVE_PASS_OUTPUT_ORACLE_PENDING')),
 ('supervisor_reap_required',lambda e:e['supervisor'].update(worker_reaped=False)),
 ('closure_source_join',lambda e:e['Root_native_closure']['source'].update(sha256='0'*64))]:
 e=copy.deepcopy(evidence);change(e)
 # Preserve summary==observations in cases where we specifically test nested receipt invariants.
 if name in ('correct_edit_source_join','create_only_receipt','latest_fail_cannot_promote'):e['summary']['fixtures']=copy.deepcopy(e['observations'])
 class Fake:
  def __getattr__(self,n):return getattr(h,n)
  def read_ref(self,ref,*args,**kwargs):
   key=next((k for k,v in req['evidence'].items()if v['path']==ref['path']),None)
   if key is None:return h.read_ref(ref,*args,**kwargs)
   raw=e[key]if isinstance(e[key],bytes)else json.dumps(e[key]).encode();return raw,proofs[key]
 m.helper=lambda:Fake();refusal(name,lambda:m.inspect_metadata(req));m.helper=real_helper
# Source+output pin drift is rejected on second custody pass.
for name,mutate_path in [('source_after_CAS',records['outputs'][0]['fixture_id']),('output_after_CAS',records['outputs'][1]['path'])]:
 counts={}
 def drift(h,ref,cred):
  row=fake_cipher(h,ref,cred);p=ref['path'];counts[p]=counts.get(p,0)+1
  target=binding['fixtures'][4]['input']['path']if name=='source_after_CAS'else mutate_path
  if p==target and counts[p]>1:row['ino']+=1
  return row
 m.cipher_ref=drift;refusal(name,lambda:m.build(req))
m.cipher_ref=fake_cipher
c=module(P/'candidate/f06_contract.py','f06_contract')
assert c.CANONICAL_ACCEPTANCE_SHA is None
inside=module(P/'candidate/inside_once.py','inside_once')
mdigest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
staged={'selected_count':2,'selected_fixture_ids':['f06-5','f06-6'],'input_sha256':mdigest,'expected_stores':0,'expected_probes':6,'source_pins':[{**output_pins[row['path']],'fixture_id':row['fixture_id']}for row in manifest['fixtures']],'credential_source':req['credential']}
selected=inside.selection_contract(staged,manifest,mdigest,c.LIMITS);assert selected['expected_probes']==6 and c.LIMITS['max_password_probes']==6;passed('nearest_inside_selection_contract_accepts_new_manifest_fixed6probes')
for name,mut in [('nearest_stores_refused',lambda q:q.update(expected_stores=1)),('nearest_probe_expansion_refused',lambda q:q.update(expected_probes=7)),('nearest_selection_dup_refused',lambda q:q.update(selected_fixture_ids=['f06-5','f06-5']))]:
 q=copy.deepcopy(staged);mut(q);refusal(name,lambda:inside.selection_contract(q,manifest,mdigest,c.LIMITS))
cred_id=c.credential_metadata(req['credential'])[1]
minimal={'mode':c.MODE,'credential_source':req['credential'],'credential_source_identity':cred_id,'metadata_adapter_source':{'path':str(P/'native567_handoff.py'),'bytes':(P/'native567_handoff.py').stat().st_size,'sha256':hashlib.sha256((P/'native567_handoff.py').read_bytes()).hexdigest()}}
try:c.output_inputs(minimal)
except ValueError as error:assert str(error)=='NATIVE567_ROOT_ACCEPTANCE_UNBOUND';passed('consumer_unbound_acceptance_refused_before_cipher_manifest')
else:raise AssertionError('unbound')
# Exact preserved M3R4 source-check validates codec and all metadata refs only.
r=module(P/'candidate/root_frame.py','root_frame')
checked=r.offline_check();assert checked['state']=='SOURCE_ONLY_NO_RUNTIME_AUTHORITY';passed('M3R4_exact_offline_source_schema_codec_and_refs')
assert not(set(opens)&forbidden)
report={'schema':'friday.f06.native567-source-tests.v1','state':'PASS_SOURCE_ONLY_MOCKS_NO_EXECUTION_AUTHORITY','tests':results,'passed':len(results),'forbidden_ciphertext_or_credential_body_opens':0,'actual_Office_starts':0,'actual_native_runs':0,'actual_slot_effects':0,'actual_admissions':0,'mock_manifest_not_written':True,'source_check':checked}
(P/'TEST-RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');(P/'TEST-RESULTS.json').chmod(0o600)
print(json.dumps({'state':report['state'],'passed':len(results),'forbidden_body_opens':0}))
