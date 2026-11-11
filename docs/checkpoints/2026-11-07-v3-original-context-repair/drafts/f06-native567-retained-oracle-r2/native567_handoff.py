"""Exact distinct native567 retained 5/6 metadata adapter; no execution authority.

Import only defines code. build() is a future Root-admitted read-only custody
validation, including ciphertext hashes. inspect_metadata() reads only exact
nonsecret evidence and credential stat metadata. Neither copies nor runs Office.
"""
from __future__ import annotations
import argparse, hashlib, json, os, stat, types
from pathlib import Path
BASE=Path(__file__).resolve().parent
ASSIGNMENT='ASTRA-CHILD-F06-NATIVE567-RETAINED-ORACLE-HANDOFF-20261112#1'
NATIVE_ASSIGNMENT='ASTRA-CHILD-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112#1'
NATIVE_OPERATION='ASTRA-F06-NATIVE203-UNSTARTED567-20261112#1'
SELECTED=['f06-5','f06-6']
OLD_ADAPTER=Path('/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/output-oracle/handoff-r2.py')
OLD_ADAPTER_SHA='160bf85bc4fa14818582562edf433b7ec40c9a4d61c45fc399350f7eadf204cd'
PINNED_REFS={'native_binding': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-UNSTARTED567-ROOT-EXECUTION/ROOT-BOUND-ONLY-UNSTARTED567.json', 'bytes': 15690, 'sha256': '4db9d853c77a786cf45128b924cf0ff1815834ef3b145c00640b6102d0859d52'}, 'native_root_grant': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-UNSTARTED567-ROOT-EXECUTION/ROOT-EXTERNAL-ONLY-UNSTARTED567-GRANT.json', 'bytes': 17128, 'sha256': 'ba4830e3eac5053b18e9cbcb7166c22e6c79ddde1b182b3e1fc55feb7039a62e'}, 'native_once': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/UNSTARTED567-ONCE.json', 'bytes': 612, 'sha256': '5b350416159aeea7e69419d3ab7b1dee689c4ae0f969bc00611967fc9787e3a6'}, 'supervisor': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/SUPERVISOR.json', 'bytes': 397, 'sha256': 'de45a888abda9ab1ed2485a3e192b0ebb2584204840a28168cce650aa1a019f3'}, 'summary': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/qualification-unstarted567/SUMMARY.json', 'bytes': 6715, 'sha256': '277f638d13a3202154b30b53c7463278d97f4ab3e3f1d407107148e9c2f757e2'}, 'observations': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/qualification-unstarted567/OBSERVATIONS.json', 'bytes': 5670, 'sha256': '126a9173839822ed36c04d0205a01ff6fa14027e3cd3a4f2d59fd24db434f488'}, 'records': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/qualification-unstarted567/OUTPUT-ORACLE-REQUESTS.json', 'bytes': 1315, 'sha256': '1d8250ab5aa4a94541c1ad189afbd0be39f42b1e7aabbc020f28de704d1501d4'}, 'Root_native_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-UNSTARTED567-ROOT-EXECUTION/ROOT-FINAL-NATIVE567-CLOSURE.json', 'bytes': 4749, 'sha256': 'c5b0a6eeacce6c6a1bab7ebf9b2ac5848c7b34493c872ab3071ffd43236eca68'}, 'native_harness': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/harness.py', 'bytes': 55529, 'sha256': '24168162be9f57b00bc38a9d8cd32e6850472681537ab7d1f27473c06d13e312'}, 'native_source_pins': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/SOURCE-PINS.json', 'bytes': 93548, 'sha256': 'f6606d43c1597a61ce6831ed20e35fed18f9c3c59ac27d2e46722dd8e4c10bed'}, 'original_binding': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-RETAINED-SEVEN-INPUT-ASSESSMENT/NATIVE-BINDING-ROOT-AUTHORIZED.json', 'sha256': '05afe7d107fcce52d0c6afb605210776ba1c1688894572bb542b7e3d9e89222a', 'bytes': 8075}, 'original_grant': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-RETAINED-SEVEN-INPUT-ASSESSMENT/NATIVE-ROOT-GRANT.json', 'sha256': 'b8f092352e752bc362f46eedb5f7a39519fea9b10edc35f83e32a8cc86b1b7ed', 'bytes': 9313}, 'original_once': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/QUALIFICATION-ONCE.json', 'sha256': 'b39b100918c851f75f44a0a3135a6f3ff1aba313ad5a8102e7ab9573ba77adff', 'bytes': 286}, 'original_summary': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/qualification/SUMMARY.json', 'sha256': '3c97f569ac9fe977daf1d535ef8066672bfa6a2b746632c943a850d04ddda72e', 'bytes': 483}, 'original_observations': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/qualification/OBSERVATIONS.json', 'sha256': '935a3fcf3891339fee00db77b2b39a76044b8b69dd6949b6b3de58a4e3dcddea', 'bytes': 4483}, 'original_reconciliation': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-RETAINED-SEVEN-INPUT-ASSESSMENT/ROOT-NATIVE-PARTIAL-RECONCILIATION.json', 'sha256': '56297abe03e541b7d9454925284507ed8c156d3d8d808f309fdf0b18b55ddae2', 'bytes': 6329}, 'root_generation_result': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-G6-HOST-PROJECTION/custody.json', 'bytes': 2869, 'sha256': 'e5bd9584b8b6e84d6aeb97822590089726ba3dd8448f044cd1d08bb3dcbdba23'}, 'independent_input_oracle': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-RETAINED-SEVEN-INPUT-ASSESSMENT/COMPOSITE-INPUT-ORACLE.json', 'bytes': 70941, 'sha256': 'cae062631ba47d019a794bc4f590bede1e7e7def9344403fca8308c6b221e8fb'}, 'original_metadata_adapter': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/output-oracle/handoff-r2.py', 'bytes': 15142, 'sha256': '160bf85bc4fa14818582562edf433b7ec40c9a4d61c45fc399350f7eadf204cd'}, 'original_adapter_acceptance': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/SOL-TASK19-M2-CANONICAL-ROOT-DELTA-ACCEPTANCE-20261112.json', 'bytes': 2072, 'sha256': '131542358c055c87ccc59aff341e610b7e2d32e05ec31fb58b79f7f6f6be4660'}, 'historical_harness': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/harness.py', 'bytes': 41030, 'sha256': 'ad02621e5d9c2b5760430fe1d5da0f0e324fcf5722ef7227bf337969b4a2bf93'}, 'historical_source_pins': {'path': '/home/jericho/.cache/FRW-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111/native-harness/revision3/SOURCE-PINS.json', 'bytes': 92220, 'sha256': '53edc7bc3d76766fe3a6c22662d902d5aa78cba63c9c62f65901c0aa7974ea69'}}

class HandoffError(ValueError):pass

def need(value,code):
 if not value:raise HandoffError(code)

def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))

def helper():
 # Self-contained bootstrap opens only the exact accepted Python helper source.
 info=OLD_ADAPTER.lstat();need(OLD_ADAPTER.resolve(strict=True)==OLD_ADAPTER and stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600,'OLD_HELPER_CUSTODY')
 fd=os.open(OLD_ADAPTER,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 with os.fdopen(fd,'rb')as f:
  held=os.fstat(f.fileno());raw=f.read(32769);after=os.fstat(f.fileno())
 ident=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 need(ident(info)==ident(held)==ident(after)==ident(OLD_ADAPTER.lstat()) and len(raw)<=32768 and hashlib.sha256(raw).hexdigest()==OLD_ADAPTER_SHA,'OLD_HELPER_SOURCE_CAS')
 m=types.ModuleType('exact_historical_handoff_helpers');m.__file__=str(OLD_ADAPTER);exec(compile(raw,str(OLD_ADAPTER),'exec'),m.__dict__)
 m.private_parents(OLD_ADAPTER);return m

def inspect_metadata(req):
 """No ciphertext or credential content is opened. No mapped manifest emitted."""
 h=helper()
 need(type(req)is dict and set(req)=={'schema','state','assignment','native_assignment','native_operation_id','lineage_mode','credential','selected_fixture_ids','evidence'},'REQUEST_FIELDS')
 need(req['schema']=='friday.f06.native567-output-handoff-request.v1' and req['state']=='BOUND_METADATA_ONLY' and req['assignment']==ASSIGNMENT and req['native_assignment']==NATIVE_ASSIGNMENT and req['native_operation_id']==NATIVE_OPERATION and req['lineage_mode']=='distinct_native567_retained','DISTINCT_NATIVE567_REQUEST')
 need(exact(req['selected_fixture_ids'],SELECTED) and exact(req['evidence'],PINNED_REFS),'EXACT_SELECTED_AND_EVIDENCE')
 credential=h.credential_metadata(req['credential']);credential_identity=tuple(getattr(Path(credential['path']).lstat(),k)for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));forbidden={credential['path']};evidence={};proofs={}
 for name,ref in PINNED_REFS.items():
  raw,actual=h.read_ref(ref,forbidden);proofs[name]=actual
  evidence[name]=raw if name in ('native_harness','historical_harness','original_metadata_adapter') else h.decode(raw)
 b=evidence['native_binding'];g=evidence['native_root_grant'];once=evidence['native_once'];old=evidence['original_binding'];og=evidence['original_grant'];oo=evidence['original_once']
 need(b['schema']=='friday.f06.unstarted567-binding.v1' and b['assignment']==NATIVE_ASSIGNMENT and b['operation_id']==NATIVE_OPERATION and b['execution_ids']==['f06-5','f06-6','f06-7'],'NATIVE567_BINDING')
 need(b['harness_sha256']==PINNED_REFS['native_harness']['sha256'] and b['native_source_pins_sha256']==PINNED_REFS['native_source_pins']['sha256'],'NATIVE567_CODE_PINS')
 need(g['schema']=='friday.f06.unstarted567-root-grant.v1' and g['assignment']==NATIVE_ASSIGNMENT and g['native567_authorized']is True and g['manifest_sha256']==proofs['native_binding']['sha256'] and exact(g['intent'],b) and g['automatic_retry']is False and g['old_grant_reused_as_authority']is False,'NEW_GRANT_NOT_HISTORICAL_AUTHORITY')
 need(once['operation_id']==NATIVE_OPERATION and once['manifest_sha256']==proofs['native_binding']['sha256'] and once['root_grant_sha256']==proofs['native_root_grant']['sha256'] and once['effect']=='NEW_GENUINELY_UNSTARTED567_ONLY' and once['automatic_retry']is False and exact(once['original_once'],PINNED_REFS['original_once']),'NEW_ONCE_JOIN')
 need(old['schema']=='friday.f06.native-binding.v2' and old['assignment']==h.ASSIGNMENT and old['root_authorized_native_run']is True and old['harness_sha256']==h.HARNESS_SHA and old['native_source_pins_sha256']==h.NATIVE_PINS_SHA,'HISTORICAL_BINDING')
 need(old['harness_sha256']==PINNED_REFS['historical_harness']['sha256'] and old['native_source_pins_sha256']==PINNED_REFS['historical_source_pins']['sha256'],'HISTORICAL_SOURCE_BYTES_JOIN')
 need(og['schema']=='friday.f06.root-native-grant.v2' and og['assignment']==h.ASSIGNMENT and og['native_qualification_authorized']is True and og['manifest_sha256']==proofs['original_binding']['sha256'] and exact(og['intent'],{k:old[k]for k in h.INTENT_KEYS}),'HISTORICAL_GRANT_JOIN')
 need(oo['effect']=='BOUND_NATIVE_QUALIFICATION' and oo['automatic_retry']is False and oo['manifest_sha256']==proofs['original_binding']['sha256'] and oo['root_grant_sha256']==proofs['original_grant']['sha256'],'HISTORICAL_ONCE_JOIN')
 need(exact(b['original_evidence'],{k[9:]:ref for k,ref in PINNED_REFS.items()if k.startswith('original_') and k not in ('original_metadata_adapter','original_adapter_acceptance')}),'HISTORICAL_EVIDENCE_SET')
 need(exact(b['fixtures'],old['fixtures']) and len(b['fixtures'])==7,'WHOLE_ORIGINAL_SEVEN_JOIN')
 for key in ('root_generation_result','independent_input_oracle'):
  need(exact(b[key],old[key]) and all(b[key][k]==PINNED_REFS[key][k]for k in ('path','sha256','bytes')),'PRODUCER_INPUT_ORACLE_JOIN')
 need(exact(b['credential'],credential) and exact(old['credential'],credential) and b['credential_keys']==old['credential_keys']=={'correct':'password','wrong':'wrong_password'},'CREDENTIAL_METADATA_LINEAGE')
 need(evidence['original_adapter_acceptance']['state']=='ROOT_INDEPENDENT_EXACT_DELTA_ACCEPTED_SOURCE_ONLY' and evidence['original_adapter_acceptance']['source']['sha256']==OLD_ADAPTER_SHA,'OLD_PURE_HELPER_ACCEPTANCE')
 for i,f in enumerate(b['fixtures']):
  need(f['id']=='f06-'+str(i+1) and f['format']==h.FORMATS[i] and f['profile']==('compatible'if i<6 else 'current_latest') and exact(f['edit'],h.edit_for(f['format'])),'SEVEN_TYPED_FIXTURES_AND_INTENT')
 s=evidence['supervisor'];summary=evidence['summary'];obs=evidence['observations'];records=evidence['records'];closed=evidence['Root_native_closure']
 need(s['operation_id']==NATIVE_OPERATION and s['status']=='COMPLETE_SCOPE567_ONLY' and s['worker_returncode']==0 and s['timed_out']is False and s['worker_reaped']is True and s['own_group_absent_observed']is True and s['automatic_retry']is False,'ACTUAL_SUPERVISOR_CLOSED')
 need(summary['status']=='COMPLETED_BOUNDED_NATIVE_SUBSET' and summary['execution_ids']==['f06-5','f06-6','f06-7'] and summary['audit_denials']==[] and summary['old_effects_replayed']is False and summary['Office_model_network']is False and summary['all_f06_accepted']is False and exact(summary['fixtures'],obs),'ACTUAL_SUMMARY_OBSERVATIONS_JOIN')
 need(closed['schema']=='friday.f06.Root-unstarted567-actual-native-closure.v1' and closed['state']=='NATIVE567_CONSUMED_ODS_ODP_PASS_OUTPUT_ORACLE_PENDING_LATEST_ODT_FAIL' and closed['actual_new_actors']==[] and closed['slot_reacquired_and_released']is True and closed['whole_F06_accepted']is False and closed['no_qualifier_retry']is True,'ROOT_HISTORICAL_CLOSURE')
 for name,key in [('native_binding','binding'),('native_root_grant','grant'),('native_once','once'),('supervisor','supervisor'),('observations','observations'),('summary','summary'),('records','output_requests'),('native_harness','source'),('native_source_pins','source_pins')]:
  need(exact(closed[key],PINNED_REFS[name]),'ROOT_CLOSURE_EVIDENCE_JOIN')
 need(records['stage']=='NOT_RUN' and exact(records['credential'],credential) and exact(records['outputs'],closed['outputs']),'OUTPUT_REQUEST_JOIN')
 need([r['fixture_id']for r in records['outputs']]==SELECTED and [r['id']for r in obs]==['f06-5','f06-6','f06-7'],'ONLY_RETAINED56')
 for item,row in zip(records['outputs'],obs):
  f=b['fixtures'][int(item['fixture_id'][4:])-1];receipt=row['receipts']['correct_edit']
  need(item['fixture_id']==row['id'] and item['format']==row['format']==f['format'] and row['profile']=='compatible' and row['status']=='NATIVE_PASS_OUTPUT_ORACLE_PENDING' and all(v is True for v in row['checks'].values()),'ACTUAL_PASS_RECEIPT_CHECKS')
  need(receipt['success']is True and receipt['sha256']==item['sha256'] and receipt['source_sha256']==f['input']['sha256'] and all(receipt[k]is True for k in ('encrypted','password_preserved','create_only','verified')) and receipt['plaintext_published']is False,'CORRECT_EDIT_OUTPUT_SOURCE_JOIN')
  need(item['path']==b['work_path']+'/authority/profiles/f06-a/workspace/'+item['fixture_id']+'-edited.'+item['format'],'EXACT_CREATE_ONLY_OUTPUT_SLOT')
 latest=obs[2];need(latest['status']=='NATIVE_FAIL' and latest['receipts']['correct_edit']['success']is False and latest['receipts']['correct_edit']['effect_disposition']=='none' and latest['receipts']['correct_edit']['reason']=='odf_encryption_parameters_invalid','LATEST7_FAIL_PRESERVED')
 # Second metadata read catches proof replacement during lineage validation.
 for name,ref in PINNED_REFS.items():need(h.read_ref(ref,forbidden)[1]==proofs[name],'EVIDENCE_AFTER_CAS')
 need(h.credential_metadata(credential)==credential and tuple(getattr(Path(credential['path']).lstat(),k)for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))==credential_identity,'CREDENTIAL_METADATA_AFTER_CAS')
 return h,credential,evidence,proofs

def cipher_ref(h,ref,credential):return h.read_ref(ref,{credential['path']},1_000_000)[1]

def build(req):
 """Future Root-admitted exact byte pins, no staging/native/Office/secret reads."""
 h,credential,evidence,proofs=inspect_metadata(req);b=evidence['native_binding'];rows=[];snapshots=[]
 for item in evidence['records']['outputs']:
  ident=item['fixture_id'];f=b['fixtures'][int(ident[4:])-1];fmt=f['format'];source_ref=f['input'];out_ref={k:item[k]for k in ('path','sha256','bytes')}
  source=cipher_ref(h,source_ref,credential);output=cipher_ref(h,out_ref,credential)
  need(source['path']!=output['path'] and source['sha256']!=output['sha256'],'DERIVATIVE_DISTINCT')
  # Native admitted pre-effect custody must still match full current source identity.
  prior=b['input_custody'][int(ident[4:])-1]
  actual_identity=[source[k]for k in ('dev','ino')]+[stat.S_IFREG|0o600]+[source[k]for k in ('uid','gid','nlink','bytes','mtime_ns','ctime_ns')]
  need(all(prior[k]==source[k]for k in ('path','sha256','bytes')) and prior['identity']==actual_identity,'ORIGINAL_SOURCE_ADMISSION_CAS')
  row={'fixture_id':ident,'format':fmt,'fixture_profile':'compatible1.3_or_Agile','path':output['path'],'sha256':output['sha256'],'bytes':output['bytes'],'staged_name':'f06-native-edited.'+fmt,'semantic':'BRAVO23','native_source_ciphertext':source,'native_output_custody':output,'native_edit_intent':h.edit_for(fmt),'native_case_status':'NATIVE_PASS_OUTPUT_ORACLE_PENDING','lineage':'distinct_native567_retained','native_success_inferred_from_oracle':False,'staging':'COPY_SAME_BYTES_MODE0600_UNDER_ROOT_PRIVATE_NATIVE_OUTPUTS; no store/decrypt/re-encrypt','independent_oracle':'NOT_GRANTED_BY_THIS_MANIFEST'}
  rows.append(row);snapshots.extend([(source_ref,source),(out_ref,output)])
 for ref,expected in snapshots:need(cipher_ref(h,ref,credential)==expected,'SOURCE_OUTPUT_AFTER_CAS')
 return {'schema':'friday.f06.retained-native-edit-oracle.v1','state':'BOUND_RETAINED_BYTES_NOT_EXECUTION_AUTHORITY','assignment':ASSIGNMENT,'native_assignment':NATIVE_ASSIGNMENT,'lineage_mode':'distinct_native567_retained','semantic':'BRAVO23','native_operation_id':NATIVE_OPERATION,'credential':credential,'proofs':proofs,'records_kind':'distinct_native567_retained','native_operation_summary_status':evidence['summary']['status'],'selected_fixture_ids':SELECTED,'selected_count':2,'fixtures':rows,'retained_but_not_selected':[],'not_present_in_retained_records':['f06-1','f06-2','f06-3','f06-4','f06-7'],'expected_Office_stores':0,'expected_Office_password_probes':6,'full_compatible_six_selected':False,'modern_seventh_selected':False,'whole_F06_accepted':False,'authority':'ROOT_FRESH_FINITE_READONLY_ORACLE_ADMISSION_AND_EFFECT_RECONCILIATION_REQUIRED','credential_content_status':'NOT_OPENED_OR_REHASHED; Root must verify exact upstream digest inside admitted private unit','no_credential_values_read_or_written':True,'no_output_regeneration':True,'historical_original_statuses_preserved':True,'old4_missing_native_receipt_not_synthesized':True,'latest7_native_status':'NATIVE_FAIL','latest7_reason':'odf_encryption_parameters_invalid','historical_grant_is_current_authority':False,'native567_effect_consumed_no_replay':True}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--request',required=True);ap.add_argument('--request-sha256',required=True);ap.add_argument('--output');ap.add_argument('--metadata-only',action='store_true');args=ap.parse_args();os.umask(0o077)
 h=helper();path=Path(args.request);raw,_=h.read_ref({'path':str(path),'sha256':args.request_sha256,'bytes':path.lstat().st_size});req=h.decode(raw)
 if args.metadata_only:
  inspect_metadata(req);print(json.dumps(dict(state='EXACT_METADATA_LINEAGE_PASS_NO_CIPHER_SECRET_OFFICE_AUTHORITY',selected_fixture_ids=SELECTED)));return
 need(args.output is not None,'OUTPUT_REQUIRED');result=build(req);out=Path(args.output);need(out.parent==BASE and out.name.endswith('.json'),'OWN_CREATE_ONLY_OUTPUT')
 payload=(json.dumps(result,indent=2)+'\n').encode();fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
 print(json.dumps(dict(state='RETAINED_METADATA_ONLY_NO_OFFICE_AUTHORITY',sha256=hashlib.sha256(payload).hexdigest(),selected_count=2)))

if __name__=='__main__':
 try:main()
 except Exception as error:
  print('F06_NATIVE567_HANDOFF_REFUSED:'+(str(error)if isinstance(error,HandoffError)else type(error).__name__));raise SystemExit(2)
