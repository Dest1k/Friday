import datetime,hashlib,json,os,stat,time
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def require(ok,why):
    if not ok:raise AssertionError(why)
def result(case):return json.loads((B/'cases'/case/'RESULT.json').read_bytes())
expected={
'source_drift_adapter':'F06_REVIEWED_SOURCE_DRIFT','source_drift_checker':'F06_REVIEWED_SOURCE_DRIFT','source_drift_footer':'F06_REVIEWED_SOURCE_DRIFT','source_drift_caller':'F06_REVIEWED_SOURCE_DRIFT','guard_disabled_source_drift':'F06_REVIEWED_SOURCE_DRIFT',
'authority_identity':'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT','authority_expired':'F06_EXISTING_AUTHORITY_EXPIRED_OR_TIMES_CHANGED','authority_scope':'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT','authority_run':'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT','authority_predecessor':'F06_EXACT_RELEASED_PREDECESSOR_REQUIRED',
'contract_run':'F06_ONLY_ORIGINAL_RUN_AND_EXISTING_R106','contract_scope':'F06_EXACT_FIRST_WRONG_READ_CONTRACT_REQUIRED',
'scenario_drift':'F06_PIN_CHANGED','scenario_identity':'F06_EXACT_IDENTITIES_AND_BOUNDS_REQUIRED','scenario_observe_window':'F06_FULL180_MAX0_DOCUMENTS_REQUIRED',
'old_O_once_tamper':'F06_PIN_CHANGED','old_O_clock_tamper':'F06_PIN_CHANGED','old_X_once_tamper':'F06_PIN_CHANGED','old_X_clock_tamper':'F06_PIN_CHANGED','old_X_binding_tamper':'F06_PIN_CHANGED','old_X_source_tamper':'F06_PIN_CHANGED','old_O_once_rename':'F06_OLD_ONCE_OR_CLOCK_ERASED_RENAMED_OR_CHANGED','old_X_clock_rename':'F06_BINDING_HISTORY_PATH_RENAMED',
'old_O_dispatch':'F06_PRIOR_CONSUMER_BIND_DISPATCH_BIRTH_OR_UNKNOWN','old_X_dispatch':'F06_BINDING_PRIOR_DISPATCH_BIRTH_OR_UNKNOWN','old_X_unknown':'F06_BINDING_PRIOR_DISPATCH_BIRTH_OR_UNKNOWN','old_X_actor':'F06_BINDING_PRIOR_DISPATCH_BIRTH_OR_UNKNOWN','old_driver_present':'F06_OLD_ROOT_DRIVER_STILL_PRESENT','canonical_run':'F06_PRIOR_CANONICAL_RUN_REFUSE',
'reconciliation_stale':'F06_ROOT_PREBIRTH_RECONCILIATION_STALE','clock_expired':'F06_CONSUMER_CLOCK_EXPIRED_OR_CHANGED','once_exists':'FileExistsError:',
'invalid_cpu':'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND','invalid_memory':'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND','invalid_disk':'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND','invalid_reserve':'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND','invalid_cleanup':'F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND','invalid_stop':'F06_STOP_BEFORE_CONSUMER_BIRTH',
'slot_identity':'F06_EXISTING_SHARED_SLOT_CUSTODY_CHANGED','review_mismatch':'F06_EXACT_INDEPENDENT_SOURCE_ACCEPTANCE_REQUIRED','work_custody':'F06_PRIVATE_WORKDIR_REQUIRED','unknown_closure':'F06_GENUINE_CLOSED_BINDING_ONLY_REFUSAL_REQUIRED','bad_binding_ref':'F06_EXACT_LOCAL_REVIEWED_SOURCE_REFERENCES_REQUIRED','current_changed':'F06_REVIEWED_MUTABLE_BASIS_CHANGED_RECONCILE_ONLY','reconstruction_guard':'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE',
'audit_external_open':'AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED','audit_external_write':'AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED','audit_external_metadata':'AUDIT_EXTERNAL_METADATA_DENIED','audit_network':'AUDIT_NETWORK_DENIED','audit_process':'AUDIT_REAL_ACTOR_DENIED','audit_import':'AUDIT_POST_PREWARM_IMPORT_DENIED'}
fixedpins=json.loads((B/'fixed-source/PINS.json').read_bytes());oldpins=json.loads((B/'old-source/PINS.json').read_bytes())
controls=[];resources=[]
for name,want in expected.items():
    override={'unknown_closure':'unknown_closure-state'}
    case=override.get(name,name+'-final' if (B/'cases'/(name+'-final')/'RESULT.json').exists() else name)
    d=result(case);r=json.loads((B/'runs'/(case+'.resource.json')).read_bytes())
    require(want in d['failure'],name+' unexpected failure '+str(d['failure']))
    require(not d['boundary'] and d['fake_Popen_count']==0,name+' consumer boundary reached')
    require(d['old_custody_preserved'],name+' changed closed history')
    require(d['source_pins']==fixedpins,name+' source mismatch')
    require(r['exit_code']==0 and r['reaped'] and r['proc_absent'] and not r['timeout'],name+' bad process cleanup')
    require(r['wall_seconds']<90 and r['cpu_seconds']<60 and d['max_rss_kib']<512*1024,name+' resource limit')
    require(len(d['resources']['affinity'])<=2,name+' CPU affinity')
    if name.startswith('audit_'):require(len(d['audit']['denied'])==1,name+' expected one audit denial')
    else:require(d['audit']['denied']==[] and d['audit']['network']==0 and d['audit']['real_subprocess']==0 and d['audit']['imports']==[],name+' unexpected audit event')
    if name.startswith('source_drift_') or name=='guard_disabled_source_drift':require(d['events']==[],name+' imported before freeze')
    if name=='invalid_stop':require(d['parent_signal_handlers_restored'] and d['passed_shared_slot_fd_closed'],'stop cleanup')
    controls.append({'control':name,'case':case,'expected_failure':want,'actual_failure':d['failure'],'result':ref(B/'cases'/case/'RESULT.json'),'resource':ref(B/'runs'/(case+'.resource.json'))})
    resources.append(r)
positive=result('positive-stop-delta');old=result('old_reconstruction-confined')
require(positive['boundary'] and positive['fake_Popen_count']==1 and positive['old_custody_preserved'],'positive boundary/custody')
require(positive['parent_signal_handlers_restored'] and positive['passed_shared_slot_fd_closed'],'positive cleanup')
require(positive['audit']['denied']==[] and positive['audit']['real_subprocess']==0 and positive['audit']['network']==0 and positive['audit']['imports']==[],'positive audit')
require(old['failure']=='ValueError:F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE' and old['fake_Popen_count']==0 and old['old_custody_preserved'],'old defect not reproduced')
require(old['audit']['denied']==[] and old['source_pins']==oldpins,'old source/audit')
for d in (positive,old):require([e[1] for e in d['events'] if e[0]=='successor']==[['path','bytes','sha256'],['bytes','path','sha256']],'real fresh mutation seam not observed')
for leaf,pin in fixedpins.items():require(ref(B.parent/'candidate/first'/leaf)['sha256']==pin['sha256'],'candidate drift '+leaf)
base=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
base_ref=ref(base);require(base_ref['sha256']=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3','static base drift')
disk=sum(p.stat().st_size for p in B.parent.rglob('*') if p.is_file())
require(disk<64*1024**2,'whole package disk cap')
for p in B.rglob('*'):
    if p.is_file():p.chmod(0o600)
    elif p.is_dir() and 'work_custody' not in str(p):p.chmod(0o700)
completed=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
v={'schema':'frw.SOL.T29.whole-real-caller-prebirth-source-protocol.v1','status':'QUALIFIED_SYNTHETIC_SOURCE_ONLY_ROOT_REVIEW_PENDING','assignment':'SOL-T29-WHOLE-PREBIRTH-PROTOCOL#1','completed_at_moscow':completed.isoformat(),'scope':'First consumer exact REAL caller main/execute complete controlflow through synthetic no-child Popen sentinel. Correctread producer canonicalization is a sibling package; no claim that future correctread caller was run here.','candidate_source_pins':fixedpins,'old_source_pins':oldpins,'static_fullv42':base_ref,'harness':{'final':ref(B/'control.py'),'pre_stop_delta':ref(B/'control.pre-stop.py'),'outer_limits_owner':ref(B/'run_batch.py'),'aggregator':ref(Path(__file__))},'positive':{'result':ref(B/'cases/positive-stop-delta/RESULT.json'),'resource':ref(B/'runs/positive-stop-delta.resource.json'),'fake_Popen_count':1,'source_mutation_key_order':[['path','bytes','sha256'],['bytes','path','sha256']],'binding_and_bound_source':positive['binding_details'],'handlers_restored':True,'inherited_slot_fd_closed':True},'old_real_failure':{'result':ref(B/'cases/old_reconstruction-confined/RESULT.json'),'resource':ref(B/'runs/old_reconstruction-confined.resource.json'),'failure':old['failure'],'binding_and_bound_source':old['binding_details'],'fake_Popen_count':0},'negative_count':len(controls),'negative_controls':controls,'invariants':{'exact_contract_shape_admission_scenario_checks':'REAL source, no replacements','pinned_module_load_and_source_freeze_review':'REAL source, no replacements','closed_O_X_ref_hash_once_clock_binding_source_reconciliation':'REAL source against declared synthetic files only','local_paths_permissions_custody_once_O_EXCL_binding_JSON_write_read_exact_reconstruction':'REAL source, no replacements','checker_observe_check_transport':'EXPLICIT SYNTHETIC dependency injection after real pinned inert checker source load','adapter_constants':'SOURCE descriptor and INSTALLED_TESTER rebound explicitly to own SYNTHETIC paths; actual fullv42 BASE/BASE_SHA retained','caller_constants':'STATE/SLOT/O/X/authority/run/scenario/issueddata/proc/interpreter explicitly synthetic own stand','host_Path':'Only literal /proc paths remap to own SYNTHETIC-proc; canonical input path validation remains real','network_model_document_token_actual_state_Office_UNO_native_product_effects':False,'consumer_child_spawned':False,'new_issuer_reachable':False,'audit':'Post-stdlib-prewarm: deny external opens/write/directory reads/metadata/network/import/real subprocess; own ancestor metadata and exact static fullv42 read are declared','semantic_acceptance':'NOT_ESTABLISHED; this is source protocol qualification only'},'resources':{'per_control_wall_seconds':90,'per_control_CPU_seconds':60,'per_control_AS_bytes':512*1024**2,'per_control_FSIZE_bytes':64*1024**2,'affinity_max_CPUs':2,'whole_package_bytes_at_finalization':disk,'whole_package_limit_bytes':64*1024**2,'negative_max_wall_seconds':max(r['wall_seconds'] for r in resources),'negative_total_CPU_seconds':sum(r['cpu_seconds'] for r in resources),'aggregate_cgroup_claim':False,'all_selected_control_processes_reaped':True},'preserved_harness_failures':{'cases':['old_reconstruction','positive','old_reconstruction-r2','old_reconstruction-r3'],'reason':'First stand Path subtype was incompatible with Python3.14 pathlib __init__, then proc remapping through __new__ was ineffective. Audit denied /proc open before read. Stopped batch, corrected test-only Path __init__ mapping and exception stack collection; raw failed outputs retained in runs. No candidate production change or actual proc/source/body effect.'},'repeat_reason':'After adding metadata confinement, reran all affected negative controls and old/positive proof on same candidate. After adding synthetic stop test seam, reran new stop negative plus positive nearest consumer; preceding unchanged negative results retained against pre-stop harness snapshot.','independent_review':'PENDING_ROOT; source reviewer and integrator own final acceptance','constraints':'No actual O/X nested refs followed. No real authority/grant, clock, slot, scenario, document, token or STATE read. No models, Office, network, canonical run or consumer. Prior actual effects remain untouched.'}
raw=(json.dumps(v,ensure_ascii=True,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();(B/'RESULT.json').write_bytes(raw);(B/'RESULT.json').chmod(0o600)
(B/'RESULT.sha256').write_text(sha(raw)+'  RESULT.json\n');(B/'RESULT.sha256').chmod(0o600)
print(json.dumps({'path':str(B/'RESULT.json'),'sha256':sha(raw),'negative_count':len(controls),'disk':disk,'completed_at_moscow':v['completed_at_moscow']}))
