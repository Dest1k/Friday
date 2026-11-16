"""Root's bounded preintent gate for one exact226 ordinary F03 EML copy edit.
No IO at import. Never manufactures future native ingress/read/answer authority.
"""
from pathlib import Path
import hashlib,json,os,stat,time,types
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
RUN = 'ROOT_UNBOUND'
HELPER={'path':'/home/jericho/.cache/FRW-SOL-V3-DOCX-FIRST-SUMMARY-RECALL-SOURCE-CORE-20261116/dependencies/root_f07_once.py','bytes':40278,'sha256':'f172ccd6f9fd4e3eadbd47eb01582d8b83d2cb81415ac148bd1820488d3473dd'}
CHECKER={'bytes':65678,'path':'/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/docx_summary_recall_current.py','sha256':'a1a3f7aa1a9d2c68ed8034188831e3798b29c750eebaf03de494afe214ce069f'}
TRANSPORT={'bytes':5878,'path':'/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/native_scope_post226.py','sha256':'b4543424b0fd34eb0963621ff13083f28d92981a0e811c571b04419a0aad7f54'}
BASE = None
DECISIONS = ('original_EML_operation_genuinely_unexecuted_reconciled', 'old_effects_UNKNOWN_clocks_preserved', 'exact_installed226_current_existing_process_and_native_edit_profile_accepted', 'single_natural_question_no_upload_reset_or_hidden_oracle', 'genuine_received_source_and_receipt_assessed_for_edit', 'native_write_output_custody_reply_are_postconditions', 'current_permission_cancel_recovery_isolation_assessed', 'private_oracle_excluded_from_model', 'metadata_logging_source_unchanged_raw_retention_scoped')
ROOT_BOUND = False
OPERATION = 'edit'
ELIGIBILITY = None
INSTALLED226 = None
RECEIVED_SOURCE = None
EXPECTED226_TUPLE = {'installed': 226, 'project': 533, 'native': 17895, 'plugins': 52, 'base': 17730, 'product_source_commit': '35d5f4fe901dc4c11e43f52c65949e843c70de5c'}
EDIT_NATIVE_REF = {'path': '/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/scoped_communication.py', 'bytes': 35499, 'sha256': 'bf4e515a71979562743607f6432a4370734d0a465d202a195e6ab3b74ee298db'}
CANONICAL226_SHA = {'receipt': '9e65245f445b486fad4445b549360698066726f74006fe236db5afd26d79041e', 'marker': 'f0a62d197decc50a891ab1a47a9fa53b4a56d8f8bda92901dd7afe0454fc457e', 'stamp': '7339e1228c9a5f558e88e6e1e00cc65472ce8982209f968980c71849f5b1fefb'}
def need(ok,why):
 if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(raw,path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def helper():
 p=Path(HELPER['path']);st=p.lstat();raw=p.read_bytes()
 need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and not st.st_mode&0o022 and len(raw)==HELPER['bytes']and digest(raw)==HELPER['sha256'],'EMLCE_exact_private_helper_required')
 return load(raw,p,'RootEMLCEHelper')
def fixed_sources():
 h=helper();c=load(h.readref(CHECKER),CHECKER['path'],'RootEMLCEGenericMetadata');t=load(h.readref(TRANSPORT),TRANSPORT['path'],'RootEMLCENativeProjection');return h,c,t

def validate_proof_shape(proof,run_id,scenario,stage):
 need(ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')
 need(type(proof)is dict and proof.get('schema')=='frw.Root.EML-edit226.preintent-proof.v2' and proof.get('operator')=='Root'and proof.get('accepted')is True,'EMLCE_unbound_Root_preintent')
 need(run_id==RUN==proof.get('run_id')and digest(encoded(scenario))==proof.get('scenario_sha256'),'EMLCE_exact_original_scenario_required')
 need(type(proof.get('decisions'))is dict and all(proof['decisions'].get(k)is True for k in DECISIONS),'EMLCE_explicit_original_decisions_required')
 need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False and proof.get('operation')==OPERATION and proof.get('effect_eligibility')==ELIGIBILITY and proof.get('installed226_assessment')==INSTALLED226 and proof.get('received_source')==RECEIVED_SOURCE,'EMLCE_exact_Root_bindings_no_future_credit')
 need(stage in ('NEW','READONLY','CURSOR_AUTHORITY','SCENARIO_VALIDATION','PRE_REQUEST_GUARD','PRE_INTENT_REVALIDATION'),'EMLCE_preoperation_only')
 wall,mono=time.time(),time.monotonic()
 for k in ('created_at','expires_at','created_monotonic','expires_monotonic'):need(type(proof.get(k))in(int,float),'EMLCE_finite_proof_clock')
 need(proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120 and proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,'EMLCE_stale_preintent')
 return True

def check(proof_ref,*,run_id,scenario,stage):
 need(ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')
 h,c,t=fixed_sources();proof=h.doc(proof_ref);validate_proof_shape(proof,run_id,scenario,stage)
 h.readref(ELIGIBILITY);assessment=h.doc(INSTALLED226)
 need(assessment.get('operator')=='Root'and assessment.get('installed')==226 and assessment.get('current_accepted')is True and assessment.get('existing_native_process_accepted')is True and assessment.get('baseline')==BASE and assessment.get('current_tuple')==EXPECTED226_TUPLE and assessment.get('edit_native_ref')==EDIT_NATIVE_REF,'EDIT226_EXACT_CURRENT_PROFILE_REQUIRED')
 if OPERATION=='edit':
  received=h.doc(RECEIVED_SOURCE)
  need(received.get('source_sha256')=='b308061ec10acc4d9b8f4bf45935da238b5ba851e1da9a5a64d4ec2a0e8b7928'and received.get('source_bytes')==1579 and received.get('genuine_previously_received')is True and received.get('source_unchanged')is True and received.get('original_first_read_preserved')is True,'EMLCE_REAL_RECEIVED_SOURCE_REQUIRED')
  for key in ('received_artifact','receipt','native_ingress','native_original_read'):h.readref(received[key])
  sp=Path(received['source_path']);st=sp.lstat();identity=lambda v:dict(device=v.st_dev,inode=v.st_ino,uid=v.st_uid,size_bytes=v.st_size,mtime_ns=v.st_mtime_ns,ctime_ns=v.st_ctime_ns)
  need(not any(q.is_symlink()for q in(sp,*sp.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and identity(st)==received['source_identity'],'EMLCE_CURRENT_NATIVE_SOURCE_IDENTITY_REQUIRED')
  h.readref(dict(path=str(sp),bytes=received['source_bytes'],sha256=received['source_sha256']))
  need(identity(sp.lstat())==identity(st),'EMLCE_CURRENT_NATIVE_SOURCE_CAS_CHANGED')
 base=h.doc(BASE)
 need(all(base.get('canonical',{}).get(k,{}).get('sha256')==v for k,v in CANONICAL226_SHA.items()),'EDIT226_EXACT_CANONICAL3_REQUIRED')
 need(type(base.get('source'))is dict and list(base['source'].values()).count(EDIT_NATIVE_REF)==1,'EDIT226_EXACT_NATIVE_EDIT_SOURCE_NOT_SIBLING_REQUIRED')
 for label,ref in base['canonical'].items():h.readref(ref,private=False)
 for name,ref in base['source'].items():h.readref(ref,private=False)
 services,env=c.services(base['process_environment']);need(services==base['services'],'EMLCE_service_identity_changed')
 state=c.parse(c.read(H/'gateway_state.json',private=False));tg=state.get('platforms',{}).get('telegram',{})
 need(state.get('gateway_state')=='running' and state.get('active_agents')==0 and state.get('active_work')is None and not state.get('restart_requested') and state.get('served_profiles')==['default','dest_telegram','telegram-bot-8812646969']and tg.get('state')=='connected'and tg.get('needs_attention')is False,'EMLCE_gateway_not_quiescent')
 native=t.fresh_native(state);need(native['quiescent']and native['identity']==base['native']['identity'],'EMLCE_native_not_quiescent')
 dbs=c.databases()
 need(dbs=={k:{a:b for a,b in v.items()if a not in('quick_check','db_wal_shm_present')}for k,v in base['databases'].items()},'EMLCE_preintent_DB_or_principal_changed')
 permission=c.permission_current();need(permission==base['policy_namespace_only'],'EMLCE_current_policy_namespace_changed')
 need(not os.path.lexists(H/'maintenance.json')and not os.path.lexists(STATE/'observer-stop.json'),'EMLCE_cancel_or_maintenance_present')
 cooldown=STATE/'cooldown.json';need(not cooldown.exists()or c.doc(c.ref(cooldown)).get('until',0)<=time.time(),'EMLCE_cooldown_present')
 # A namespace check is no event/source capability. Native admission supplies it with a future ordinary event. No future write is preflight credit.
 for p in (H/'profiles/telegram-bot-8812646969',H/'profiles/telegram-bot-8812646969/workspace',H/'profiles/telegram-bot-8812646969/workspace/received'):
  st=p.lstat();need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISDIR(st.st_mode)and st.st_uid==os.getuid()and stat.S_IMODE(st.st_mode)==0o700,'EMLCE_private_ingress_workspace_required')
 need(set(proof['lock_owners'])=={'slot','consumer','credential'},'EMLCE_all_existing_locks_required')
 for path,key in ((SLOT,'slot'),(STATE/'consumer.lock','consumer'),(STATE/'tester-token','credential')):c.lock_held(path,proof['lock_owners'][key])
 if proof.get('clock')is not None:
  clock=h.doc(proof['clock']);need(clock['run_id']==run_id and clock['deadline_monotonic']-clock['started_monotonic']==900 and time.monotonic()+605<clock['deadline_monotonic'],'EMLCE_original_outer_clock_insufficient')
 # Exact old rows remain enforced by ordinary_independent_admission/current_rows.
 current_refs={p.name for p in (STATE/'runs').glob('*.json')};expected={r['id']+'.json'for r in base['history']}
 need(current_refs in(expected,expected|{run_id+'.json'}),'EMLCE_unreviewed_history_delta')
 need(c.profile_config_refs()==base['policy_namespace_only']['profile_configs'],'EMLCE_configs_or_effective_roots_changed')
 need(t.fresh_native(state)['quiescent'],'EMLCE_final_native_state_changed')
 validate_proof_shape(proof,run_id,scenario,stage)
 return True
