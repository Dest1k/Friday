import hashlib,json,os,resource,time
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent.parent;OUT=B/'review';START=time.monotonic();CPU=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def exact(r):
 p=Path(r['path']);assert p.is_relative_to(B) and not p.is_symlink();raw=p.read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],p;return raw
def load(r):return json.loads(exact(r))
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
protocol_ref=ref(B/'protocol-stand/RESULT.json');assert protocol_ref['sha256']=='76b1137da3b4bed9b4fb30b50b39b3c19ca0ac40f32528b82b12fdc5283dae0c';P=load(protocol_ref)
freeze=load(P['candidate_source_freeze']);assert P['candidate_source_freeze']['sha256']=='1f35c3e7346ca8bfce2bc8e791d393c98d76e3614cd7934a19be1d8d4ee19b4f'
for leaf,pin in freeze['files'].items():assert P['final_five_sources'][leaf]==dict(path=str(B/'candidate'/leaf),**pin);exact(P['final_five_sources'][leaf])
for r in P['harness_sources'].values():exact(r)
load(P['initial_summary']);load(P['historical_harness_reconstruction']['result'])
final=[]
for row in P['final_controls']:
 body=load(row['result']);resource_row=load(row['resource']);assert body['expectation_met'] and body['source_pins']==freeze['files']
 assert resource_row['reaped'] and resource_row['proc_absent'] and resource_row['exit_code']==0 and not resource_row['timeout']
 assert body['audit']['network']==0 and body['audit']['real_subprocess']==0 and not body['audit']['imports']
 assert body['parent_signal_handlers_restored'] and body['all_caller_issuer_opened_fds_closed'] and body['slot_reacquirable_after_return'] and body['old_clock_bodies_not_read'] and body['old_synthetic_custody_preserved']
 assert body['limits']['CPU']==[60,60] and body['limits']['AS']==[512*1024**2]*2 and len(body['limits']['affinity'])==2
 assert body['fake_Popen_count']==(1 if body['boundary'] else 0)
 if row['case']=='final-positive':
  assert row['result']['sha256']=='07fd08e0df5ca60d51ebf3925c9194b27435d9e66285efe0aaff1d30100d32d2'
  assert body['boundary'] and len(body['fake_Popen'])==1 and sum(e[0]=='successor' for e in body['events'])==2
  call=body['fake_Popen'][0];assert call['same_shared_slot_held'] and call['preexec_fn_present'] and call['exact_JSON_contract_reconstruction']
 elif row['case'] in ('final-source-drift-checker','final-source-drift-validator'):assert not any(e[0]=='load' for e in body['events'])
 final.append({'case':row['case'],'boundary':body['boundary'],'failure':body['failure'],'ref':row['result']})
assert len(final)==P['final_control_count']==27 and sum(x['boundary'] for x in final)==1
initial=[]
for row in P['initial_controls']:
 body=load(row['result']);assert body['expectation_met'];initial.append(row['control'])
assert len(initial)==P['initial_control_count']==59
workers=[]
for r in P['worker_resources']:
 w=load(r);assert w['reaped'] and w['proc_absent'] and not w['timeout'];assert w['limits']['wall']==90 and w['limits']['CPU']==60 and w['limits']['AS']==512*1024**2 and len(w['limits']['affinity'])==2
 workers.append({'case':w['case'],'exit_code':w['exit_code'],'wall':w['wall_seconds'],'cpu':w['CPU_seconds']})
assert len(workers)==P['worker_group_count']==88 and P['all_own_workers_reaped'] and P['production_processes_created']==P['network_connections_created']==0
patch_resource=json.loads((B/'checks/patch-handoff-r1/RESULT.json').read_bytes());patchraw=(B/'checks/patch-handoff-r1/stdout').read_bytes();assert sha(patchraw)==patch_resource['stdout_sha256'];patch=json.loads(patchraw);assert patch_resource['exit_code']==0 and patch_resource['reaped'] and patch_resource['proc_absent'] and not patch_resource['timeout'];assert patch['count']==35 and patch['source_freeze']==P['candidate_source_freeze'];exact(patch['patch'])
assert patch['runtime_NOT_RUN'] and not patch['actual_issuer_executed'] and not patch['generated_consumer_executed'] and patch['own_patch_stand_removed']
current=load(ref(B/'current-controls/revision-r2/RESULT.json'));assert current['r2_current_sha256']==freeze['files']['current_root.py']['sha256'] and current['status']=='AFFECTED_SOURCE_DELTA_CONTROLS_PASS' and len(current['checks'])==25
parent=load(ref(B/'PARENT-R2-DELTA-ACCEPTANCE.json'))
r={'schema':'frw.Sol.Task30.independent-final-evidence-check.v1','protocol_ref':protocol_ref,'source_freeze_ref':P['candidate_source_freeze'],'final_controls_verified':final,'initial59_retained_hashes_and_expectations_verified':True,'initial31_explicit_unchanged_rejection_scope_reuse':P['reused_initial_negatives_only'],'initial_other_controls_historical_only':True,'workers_verified':len(workers),'workers_exit_counts':{str(code):sum(w['exit_code']==code for w in workers) for code in {w['exit_code'] for w in workers}},'all_worker_evidence_reaped':True,'finalpositive_one_fake_birth_and_two_exact_reconstructions':True,'sourcefreeze_before_import_gates':True,'current_delta_25controls_and_parent_delta_acceptance_inspected':True,'parent_patch35_source_handoff_checks_verified':True,'execution_seams':P['execution_seams'],'no_actual_current_or_authority_inference':True,'actual_effects':'NOT_RUN','full180':'NOT_RUN','actual_semantic_acceptance':'NOT_ESTABLISHED','source_only':True,'elapsed_wall_seconds':time.monotonic()-START,'elapsed_cpu_seconds':time.process_time()-CPU}
encoded=(json.dumps(r,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode();p=OUT/'final-evidence-check.json';p.write_bytes(encoded);p.chmod(0o600);print(json.dumps({'verified_final_controls':len(final),'verified_initial_controls':len(initial),'verified_workers':len(workers),'sha256':sha(encoded),'wall_seconds':r['elapsed_wall_seconds']}))
