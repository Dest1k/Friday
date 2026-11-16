"""Root's bounded preintent gate for one original F01/EML first upload.
No IO at import. Never manufactures future native ingress/read/answer authority.
"""
from pathlib import Path
import hashlib,json,os,stat,time,types
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
RUN='f01-eml-first-received-read-01-20261116'
HELPER={'path':'/home/jericho/.cache/FRW-SOL-V3-DOCX-FIRST-SUMMARY-RECALL-SOURCE-CORE-20261116/dependencies/root_f07_once.py','bytes':40278,'sha256':'f172ccd6f9fd4e3eadbd47eb01582d8b83d2cb81415ac148bd1820488d3473dd'}
CHECKER={'bytes':65678,'path':'/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/docx_summary_recall_current.py','sha256':'a1a3f7aa1a9d2c68ed8034188831e3798b29c750eebaf03de494afe214ce069f'}
TRANSPORT={'bytes':5878,'path':'/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/native_scope_post226.py','sha256':'b4543424b0fd34eb0963621ff13083f28d92981a0e811c571b04419a0aad7f54'}
BASE={'path':'/home/jericho/.cache/FRW-ASTRA-EML-FIRST-READ-PREPARATION-20261116/ROOT-READONLY-PREPARATION-SNAPSHOT.json','sha256':'cf55cb07f4ba677a459e01105745e452f6eb1779aa4a80bb9e7f1c01cbf46491','bytes':151577}
DECISIONS=('original_F01_EML_first_read_eligible','old_effects_UNKNOWN_clocks_preserved','same_principal_new_upload_only','native_ingress_read_and_answer_are_postconditions','current_cancel_recovery_isolation_assessed','private_oracle_excluded_from_model','metadata_logging_source_unchanged_raw_retention_scoped','fresh_file_guard_retained','no_attachment_payload_external_mail_or_write_requested')
def need(ok,why):
 if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(raw,path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def helper():
 p=Path(HELPER['path']);st=p.lstat();raw=p.read_bytes()
 need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and not st.st_mode&0o022 and len(raw)==HELPER['bytes']and digest(raw)==HELPER['sha256'],'EML_exact_private_helper_required')
 return load(raw,p,'RootEMLHelper')
def fixed_sources():
 h=helper();c=load(h.readref(CHECKER),CHECKER['path'],'RootEMLGenericMetadata');t=load(h.readref(TRANSPORT),TRANSPORT['path'],'RootEMLNativeProjection');return h,c,t

def validate_proof_shape(proof,run_id,scenario,stage):
 need(type(proof)is dict and proof.get('schema')=='frw.Root.EML-first-upload.preintent-proof.v1' and proof.get('operator')=='Root'and proof.get('accepted')is True,'EML_unbound_Root_preintent')
 need(run_id==RUN==proof.get('run_id')and digest(encoded(scenario))==proof.get('scenario_sha256'),'EML_exact_original_scenario_required')
 need(type(proof.get('decisions'))is dict and all(proof['decisions'].get(k)is True for k in DECISIONS),'EML_explicit_original_decisions_required')
 need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False,'EML_no_future_credit')
 need(stage in ('NEW','READONLY','CURSOR_AUTHORITY','SCENARIO_VALIDATION','PRE_REQUEST_GUARD','PRE_INTENT_REVALIDATION'),'EML_preoperation_only')
 wall,mono=time.time(),time.monotonic()
 for k in ('created_at','expires_at','created_monotonic','expires_monotonic'):need(type(proof.get(k))in(int,float),'EML_finite_proof_clock')
 need(proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120 and proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,'EML_stale_preintent')
 return True

def check(proof_ref,*,run_id,scenario,stage):
 h,c,t=fixed_sources();proof=h.doc(proof_ref);validate_proof_shape(proof,run_id,scenario,stage)
 base=h.doc(BASE)
 for label,ref in base['canonical'].items():h.readref(ref,private=False)
 for name,ref in base['source'].items():h.readref(ref,private=False)
 services,env=c.services(base['process_environment']);need(services==base['services'],'EML_service_identity_changed')
 state=c.parse(c.read(H/'gateway_state.json',private=False));tg=state.get('platforms',{}).get('telegram',{})
 need(state.get('gateway_state')=='running' and state.get('active_agents')==0 and state.get('active_work')is None and not state.get('restart_requested') and state.get('served_profiles')==['default','dest_telegram','telegram-bot-8812646969']and tg.get('state')=='connected'and tg.get('needs_attention')is False,'EML_gateway_not_quiescent')
 native=t.fresh_native(state);need(native['quiescent']and native['identity']==base['native']['identity'],'EML_native_not_quiescent')
 dbs=c.databases()
 need(dbs=={k:{a:b for a,b in v.items()if a not in('quick_check','db_wal_shm_present')}for k,v in base['databases'].items()},'EML_preintent_DB_or_principal_changed')
 permission=c.permission_current();need(permission==base['policy_namespace_only'],'EML_current_policy_namespace_changed')
 need(not os.path.lexists(H/'maintenance.json')and not os.path.lexists(STATE/'observer-stop.json'),'EML_cancel_or_maintenance_present')
 cooldown=STATE/'cooldown.json';need(not cooldown.exists()or c.doc(c.ref(cooldown)).get('until',0)<=time.time(),'EML_cooldown_present')
 # A namespace check is no event/source capability. Native admission supplies it after upload.
 for p in (H/'profiles/telegram-bot-8812646969',H/'profiles/telegram-bot-8812646969/workspace',H/'profiles/telegram-bot-8812646969/workspace/received'):
  st=p.lstat();need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISDIR(st.st_mode)and st.st_uid==os.getuid()and stat.S_IMODE(st.st_mode)==0o700,'EML_private_ingress_workspace_required')
 need(set(proof['lock_owners'])=={'slot','consumer','credential'},'EML_all_existing_locks_required')
 for path,key in ((SLOT,'slot'),(STATE/'consumer.lock','consumer'),(STATE/'tester-token','credential')):c.lock_held(path,proof['lock_owners'][key])
 if proof.get('clock')is not None:
  clock=h.doc(proof['clock']);need(clock['run_id']==run_id and clock['deadline_monotonic']-clock['started_monotonic']==600 and time.monotonic()+305<clock['deadline_monotonic'],'EML_original_outer_clock_insufficient')
 # Exact old rows remain enforced by ordinary_independent_admission/current_rows.
 current_refs={p.name for p in (STATE/'runs').glob('*.json')};expected={r['id']+'.json'for r in base['history']}
 need(current_refs in(expected,expected|{run_id+'.json'}),'EML_unreviewed_history_delta')
 need(c.profile_config_refs()==base['policy_namespace_only']['profile_configs'],'EML_configs_or_effective_roots_changed')
 need(t.fresh_native(state)['quiescent'],'EML_final_native_state_changed')
 validate_proof_shape(proof,run_id,scenario,stage)
 return True
