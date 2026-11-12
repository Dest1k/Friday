"""Close owned synthetic protocol package with exact source and result pins."""
import datetime,hashlib,json,os,stat
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent

def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(p):raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def load(p):return json.loads(p.read_bytes())
def check(v,msg):
 if not v:raise AssertionError(msg)
initial=load(B/'INITIAL-SUMMARY.json');final=[]
for p in sorted((B/'cases').glob('final-*/RESULT.json')):
 leaf=p.parent.name
 d=load(p);check(d['expectation_met'],'final case failed')
 check(d['all_caller_issuer_opened_fds_closed'] and d['slot_reacquirable_after_return'] and d['parent_signal_handlers_restored'] and d['old_clock_bodies_not_read'],'final FDs/slot/old-clock invariant')
 check(not d['audit']['denied'] and d['audit']['real_subprocess']==0 and d['audit']['network']==0,'final undeclared access')
 final.append({'case':leaf,'result':ref(p),'resource':ref(B/'runs'/(leaf+'.resource.json')),'boundary':d['boundary'],'failure':d['failure']})
finalpins=load(B/'final-source/PINS.json');candidatepins={}
for leaf,pin in finalpins.items():
 r=ref(B.parent/'candidate'/leaf);check({k:r[k] for k in ('bytes','sha256')}==pin,'candidate changed after final stand');candidatepins[leaf]=r
positive=load(B/'cases/final-positive/RESULT.json')
check(positive['boundary'] and positive['fake_Popen_count']==1,'sole fakePopen required')
check(positive['fake_Popen'][0]['exact_JSON_contract_reconstruction'],'exact serialized reconstruction required')
initialcases=[]
for r in initial['controls']:
 p=Path(r['result']['path']);check(ref(p)==r['result'],'initial case evidence drift');d=load(p)
 check(d['expectation_met'] and d['parent_signal_handlers_restored'] and d['passed_shared_slot_fd_closed'] and d['old_synthetic_custody_preserved'],'initial result invariant')
 check(d['audit']['real_subprocess']==(1 if d['control']=='audit_process' else 0),'undeclared process attempt')
 check(d['audit']['network']==(1 if d['control']=='audit_network' else 0),'undeclared network attempt')
 check(not d['audit']['denied'] or d['control'].startswith('audit_'),'undeclared external access')
 initialcases.append(r)
resources=[ref(p) for p in sorted((B/'runs').glob('*.resource.json'))]
for r in resources:
 d=load(Path(r['path']));check(d['reaped'] and d['proc_absent'] and not d['timeout'],'worker closure failed');check(d['wall_seconds']<90 and d['CPU_seconds']<60,'worker budget exceeded')
check(all(positive['source_pins'][k]==v for k,v in finalpins.items()),'final source pins')
initialpins=load(B/'fixed-source/PINS.json');changed=[k for k in finalpins if initialpins.get(k)!=finalpins[k]]
check(changed==['current_root.py','first_ingress.py'],'unexpected final delta requires dependent negatives')
result={
 'assignment':'SOL-T30-WRONGEDIT-PROTOCOL#1','peer_assignment':'ASTRA-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112#1',
 'status':'SYNTHETIC_COMPLETE_CALLER_PROTOCOL_QUALIFIED_SOURCE_ONLY','completed_at_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
 'candidate_source_freeze':ref(B.parent/'candidate/SOURCE-FREEZE.json'),'final_five_sources':candidatepins,
 'initial_source_freeze_sha256':initial['candidate_freeze_sha256'],'initial_summary':ref(B/'INITIAL-SUMMARY.json'),
 'final_changed_files':changed,'reused_initial_negatives_only':['source_drift_adapter','source_drift_footer','source_drift_caller','review_mismatch','authority_scope','authority_run','authority_identity','authority_memory','authority_predecessor','scenario_drift','once_exists','canonical_run_exists','already_issued','clock_expired','clock_insufficient','clock_wrongboot','current_changed','freshproof_drift','qualified_effect_mismatch','slot_identity','invalid_cpu','invalid_memory','invalid_disk','invalid_reserve','reconstruction_guard','audit_external_open','audit_external_write','audit_external_metadata','audit_network','audit_process','audit_import'],'reuse_reason':'current_root private transitive-path enumeration and first_ingress distinct-new-clock gate changed. Exact caller/adapter/footer unchanged. Initial 59 controls remain historical initial-freeze evidence; only initial rejection scopes explicitly unaffected by these deltas are reused. Final enriched fixtures execute complete positive, both changed-source drift gates, all four timing negatives and post-timing semantics/wrong-only negatives. This stand does not qualify actual current host observations.',
 'initial_controls':initialcases,'initial_control_count':len(initialcases),'initial_negative_count':len(initialcases)-1,'final_controls':final,'final_control_count':len(final),
 'final_positive_invariants':{k:positive[k] for k in ('fake_Popen_count','fake_Popen','parent_signal_handlers_restored','passed_shared_slot_fd_closed','all_caller_issuer_opened_fds_closed','slot_reacquirable_after_return','old_synthetic_custody_preserved','old_clock_bodies_not_read','old_clock_ref_metadata','events')},
 'worker_resources':resources,'worker_group_count':len(resources),'worker_wall_seconds_total':sum(load(Path(r['path']))['wall_seconds'] for r in resources),'worker_CPU_seconds_total':sum(load(Path(r['path']))['CPU_seconds'] for r in resources),'maximum_group_wall_seconds':max(load(Path(r['path']))['wall_seconds'] for r in resources),'maximum_group_CPU_seconds':max(load(Path(r['path']))['CPU_seconds'] for r in resources),'maximum_group_rss_kib_observed':max(load(Path(r['path']))['max_rss_kib_cumulative'] for r in resources),'historical_harness_reconstruction':{'result':ref(B/'history/RESULT.json'),'provenance':'Hash-verified reconstruction by reversing exact recorded edits; not a retained original beforeimage. Three reconstructions match preexisting raw result harness_sha256.'},'all_own_workers_reaped':True,'production_processes_created':0,'network_connections_created':0,
 'initial_harness_failures':[{'kind':'Missing utf16-le codec prewarm','resource':ref(B/'runs/prep-positive-1.resource.json'),'stderr':ref(B/'runs/prep-positive-1.stderr'),'resolution':'Added explicit encodings.utf_16_le before audit hook; same untouched source snapshot qualified in new pure fixture case, no product effects.'},{'kind':'Expected scenario-drift rejection code belonged to adapter, actual caller uses F06_PIN_CHANGED','original_result':ref(B/'cases/scenario_drift/RESULT.PRE-EXPECTED-CODE-CORRECTION.json'),'resolution':'Same saved correctly rejected observation regraded; original preserved and no caller or effect replay.'}],
 'execution_seams':['Synthetic source descriptor path with no document body file','Canonical first-validator STATE namespace constant points to owned fake metadata tree; exact validator functions and all read/ref joins execute','Current checker observe/check/transport host observations explicitly synthetic; actual checker internals are independently handled by parent current-controls package','Pinned inert fake issuer source file uses O_EXCL + fsync to owned fake authority path, never original issuer code','Sole Popen replaced with sentinel that validates exact argv, passed slot FD, resource closure and JSON reconstructed contract; no consumer process'],
 'harness_sources':{p.name:ref(p) for p in [B/'control.py',B/'run_batch.py',B/'first_fixture.py',B/'fake_issuer.py.txt',B/'finalize.py']},
 'claims':'SOURCE ONLY synthetic complete prebirth caller protocol. Fake retained fixture judgments are not actual authority or actual semantic qualification. No document/model/API/network/native/credential/body reads or product effects. No live/full180/userPASS. Independent review remains parent owned.'}
files=[p for p in B.rglob('*') if p.is_file()];result['package_bytes_before_result']=sum(p.stat().st_size for p in files);result['package_allocated_bytes_before_result']=sum(p.stat().st_blocks*512 for p in files)
check(sum(p.stat().st_size for p in B.parent.rglob('*') if p.is_file())<64*1024**2,'whole B64MiB budget')
p=B/'RESULT.json';p.write_bytes(encoded(result));p.chmod(0o600);digest=sha(p.read_bytes());q=B/'RESULT.sha256';q.write_text(digest+'  RESULT.json\n');q.chmod(0o600);print(json.dumps(ref(p)))
