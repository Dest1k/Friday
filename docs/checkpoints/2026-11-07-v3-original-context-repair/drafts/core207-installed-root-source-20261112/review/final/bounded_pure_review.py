from pathlib import Path
import ast, copy, datetime, difflib, hashlib, json, os, resource, signal, time
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
signal.alarm(90)
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112')
R=B/'review/final'
start=time.monotonic()
def put(name,value):
 p=R/name
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w')as out:
  json.dump(value,out,indent=2,sort_keys=True)
  out.write('\n')
source=(B/'source_controls.py').read_text()
needle="p=B/'SOURCE-CONTROLS.json';fd="
assert source.count(needle)==1
code=source.replace(needle,"p=B/'review/final/REPLAYED-SOURCE-CONTROLS.json';fd=")
namespace={'__file__':str(B/'source_controls.py'),'__name__':'pure_source_controls_review'}
exec(compile(code,str(B/'source_controls.py'),'exec'),namespace)
m=namespace['m'];check=namespace['check'];negative=namespace['negative'];load=namespace['load'];history=namespace['history']
# Full new-frame acceptance/readback join in memory; no current H or request creation.
acceptance=load(B/'ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json')
snapshot=load(B/'ROOT-207-FRESH-READBACK-TEMPLATE.json')
virtual_ref=dict(path='/synthetic/frame-independent-review.json',sha256='a'*64)
acceptance.update(accepted=True,all_four_current_source_gates_accepted=True,gate_retry_history_preserved=True,template_only_no_execution_grant=False,state=acceptance['required_state_after_actual_Root_review'],frame_source_manifest=m.reference(B/'SOURCE-PINS.json'),frame_review_evidence=[virtual_ref],source_provenance=dict(mode='local-committed-main',commit='b'*40),public_main_sha=None)
snapshot.update(state=snapshot['required_state_after_actual_Root_readback'],template_only_no_execution_grant=False,boot_id='c'*36,observed_at_moscow=datetime.datetime.fromtimestamp(1100,datetime.timezone.utc).isoformat(),head='b'*40,provenance_mode='local-committed-main',origin_main=None,source_origin={'virtual':'source_origin_only'},evidence=[virtual_ref])
snapshot['checks']={k:True for k in snapshot['checks']}
snapshot['services']={name:dict(pid=42,birth_ticks=50,boot_id='c'*36,invocation_id='d'*32,cgroup='/user.slice/virtual',enabled_active=True,runtime_max='infinity')for name in ['gateway','dashboard']}
oldread=m.readref;oldrequest=m.validate_source_request;oldorigin=m.source_origin;oldpre=m.actual_predecessor
m.readref=lambda r:{'state':'PASS_SOURCE_ONLY'}if r==virtual_ref else oldread(r)
m.validate_source_request=lambda q:copy.deepcopy(namespace['result'])
m.source_origin=lambda *a,**k:{'virtual':'source_origin_only'}
m.actual_predecessor=lambda:history['references']['request']
def joined(a=acceptance,s=snapshot):return m.validate_join({},a,s,now=1110,boot_id='c'*36)
try:
 value=joined()
 check('review_newframe_full_metadata_join_virtual_positive',value['after_layers']==207 and value['state']=='PURE_METADATA_BOUND_NOT_ADMISSION')
 for name,mut in [
 ('missing_frame_review',lambda a:a.update(frame_review_evidence=[])),
 ('wrong_frame_freeze',lambda a:a['frame_source_manifest'].update(sha256='0'*64)),
 ('prep_review_as_final',lambda a:a.update(modern_final_execution_review=load(B/'REUSED-207-FINAL-SOURCE-EVIDENCE.json')['source_gateprep_review'])),
 ('final_review_absent_independent',lambda a:a.update(independent_review_evidence=[])),
 ('source_acceptance_execution_grant',lambda a:a.update(execution_grant=True)),
 ('unaccepted_source',lambda a:a.update(accepted=False)),
 ('four_gates_unaccepted',lambda a:a.update(all_four_current_source_gates_accepted=False)),
 ('gate_label_wrong',lambda a:a['four_gate_evidence'][0].update(label='wrong')),
 ('source_provenance_mismatch',lambda a:a['source_provenance'].update(commit='e'*40)),
 ('local_remote_claim',lambda a:a.update(public_main_sha='b'*40))]:
  bad=copy.deepcopy(acceptance);mut(bad)
  negative('review_join_reject_'+name,lambda a=bad:joined(a=a))
 for name,mut in [
 ('old_boot',lambda s:s.update(boot_id='f'*36)),
 ('stale_readback',lambda s:s.update(observed_at_moscow=datetime.datetime.fromtimestamp(800,datetime.timezone.utc).isoformat())),
 ('fake206_receipt',lambda s:s.update(installed_receipt_sha256='0'*64)),
 ('finite_permanent_service',lambda s:s['services']['gateway'].update(runtime_max='180')),
 ('lost_known_limits',lambda s:s['remaining_limits'].update(native_canonical_unknown=0)),
 ('false_current_check',lambda s:s['checks'].update(cancellation_clear=False))]:
  bad=copy.deepcopy(snapshot);mut(bad)
  negative('review_join_reject_'+name,lambda s=bad:joined(s=s))
finally:
 m.readref=oldread;m.validate_source_request=oldrequest;m.source_origin=oldorigin;m.actual_predecessor=oldpre
# Order mutation changes only in-memory historical metadata; actual CPs are immutable.
original_legacy=m.readref
record=dict(schema='frw.root.actual206-predecessor.v1',state='ROOT_RECONCILED_GENUINE_INSTALLED206_NOT_EXPECTATION',template_only_no_execution_grant=False,**history['references'])
bad_history=copy.deepcopy(history)
bad_history['ordered206_layers'][0:2]=reversed(bad_history['ordered206_layers'][0:2])
histpath=str(B/'ACTUAL206-HISTORICAL-METADATA.json')
m.readref=lambda ref:copy.deepcopy(bad_history)if ref['path']==histpath else original_legacy(ref)
try:negative('review_actual206_reordered_prefix_refused',lambda:m.validate_predecessor_record(record),'exact_completed206_ordered_prefix_required')
finally:m.readref=original_legacy
# Exact manifest pins and diff truth; no Git reads from current HEAD.
pins=load(B/'SOURCE-PINS.json')
frozen=hashlib.sha256((B/'SOURCE-PINS.json').read_bytes()).hexdigest()
check('review_exact_requested_freeze',frozen=='cdc06817972650d8a35778960b8ad28553b5600999a4ef078637499968e6bdb4')
for group in ['source_refs','historical_refs']:
 for path,digest in pins[group].items():
  p=Path(path);st=p.lstat()
  assert p.is_file()and not p.is_symlink()and st.st_uid==os.getuid()and st.st_nlink==1
  assert all(not q.is_symlink()for q in p.parents)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,path
 check('review_all_'+group+'_exact',True)
manifest=load(B/'DIFF-MANIFEST.json')
for row in manifest['rows']:
 if 'after'in row:
  before=Path(row['before']['path']);after=Path(row['after']['path']);diff=Path(row['diff']['path'])
  expected=''.join(difflib.unified_diff(before.read_text().splitlines(keepends=True),after.read_text().splitlines(keepends=True),fromfile=str(before),tofile=str(after)))
  assert diff.read_text()==expected,diff
 else:assert Path(row['unchanged']).read_bytes()==Path(row['baseline']).read_bytes()
check('review_all_delta_manifests_exact_unified_diffs',True)
check('review_frozen_bytes_unchanged_after_controls',hashlib.sha256((B/'SOURCE-PINS.json').read_bytes()).hexdigest()==frozen)
new_checks=namespace['checks'][86:]
put('INDEPENDENT-CONTROLS.json',dict(state='PASS_PURE_SOURCE_ONLY',checks=len(new_checks),rows=new_checks,manifest_source_refs=len(pins['source_refs']),manifest_historical_refs=len(pins['historical_refs']),source_pin_sha256=frozen,actual_runtime_observations=0,actual_effects=0,full_gates_rerun=False,wall_seconds=time.monotonic()-start,limits=['Join controls use in-memory dictionaries, substituted source reader/origin/request validator; no actual request/admission generated.','Actual206 stage, full495 source origins and rawGit historical206 checked by replayed exact source controls.']))
print(json.dumps(dict(state='PASS',base_controls=86,independent_controls=len(new_checks),wall_seconds=time.monotonic()-start)))
