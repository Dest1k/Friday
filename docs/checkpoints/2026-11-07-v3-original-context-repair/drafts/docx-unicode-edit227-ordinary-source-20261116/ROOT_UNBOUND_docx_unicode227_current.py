"""Root's qualified227 current guard specialized for one original DOCX Unicode edit.
No IO at import. Never manufactures future native ingress/read/answer authority.
"""
from pathlib import Path
import hashlib,json,os,stat,time,types
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
RUN = 'ROOT_UNBOUND'
HELPER={'path':'/home/jericho/.cache/FRW-SOL-V3-DOCX-FIRST-SUMMARY-RECALL-SOURCE-CORE-20261116/dependencies/root_f07_once.py','bytes':40278,'sha256':'f172ccd6f9fd4e3eadbd47eb01582d8b83d2cb81415ac148bd1820488d3473dd'}
CHECKER = {'path': '/home/jericho/.cache/FRW-ASTRA-FIXED227-METADATA-SIBLING-SOURCE-20261116/fixed227_metadata_source.py', 'bytes': 37670, 'sha256': '787cdfdfa5e8150f4f472767002438a39951c5bac89ff95fbfa2d64d214c7a8e'}
TRANSPORT={'bytes':5878,'path':'/home/jericho/.cache/FRW-ASTRA-DOCX226-SUMMARY-SOURCE-BIND-20261116/bound-source-r1/native_scope_post226.py','sha256':'b4543424b0fd34eb0963621ff13083f28d92981a0e811c571b04419a0aad7f54'}
BASE = None
DECISIONS = ('original_docx_v03_Unicode_edit_preserve_genuinely_unexecuted_reconciled', 'v01_accepted_v02_consumed_CREATE2251_old_effects_UNKNOWN_clocks_preserved', 'exact_installed227_Word_roles_current_fresh_native_process_assessed', 'one_prospective_input_and_natural_question_no_reset_or_hidden_oracle', 'genuine_ingress_native_edit_returned_bytes_custody_are_postconditions', 'current_permission_cancel_recovery_isolation_assessed', 'private_oracle_excluded_from_model', 'metadata_logging_source_unchanged_raw_retention_scoped')
ROOT_BOUND = False
FAMILY = 'docx'
EXPECTED_SOURCE = {'path': '/home/jericho/.cache/FRW-SOL-V3-DOCX-UNICODE-EDIT227-ORDINARY-SOURCE-CORE-20261116/fixture/Сводка_встречи.docx', 'bytes': 3282, 'sha256': '6408c64ba6b05549ef7d7aa24b99d310f536aeb4954690e3efca7a46e05412d6'}
UPLOAD_INPUT = None
READ227_ROLES = {'hermes_cli/friday_workspace_word_profiles.py': ('a31bd9b79b15ec8663d21199955d2d6600a1ccb3b400956ac79f74545c9aabe1', 6558), 'hermes_cli/friday_workspace_docx.py': ('0bc25b322c58c6a1aba5b4db2b6cf108b0b815b886d2e33f3c9cd2d02e881377', 38137), 'tools/scoped_word_profiles.py': ('4718c402bff018cb23544cc7d207755151c9ad93c327646ac1a84db90c34cf68', 25594), 'tools/scoped_word_stories.py': ('cf9760ecf984f5477047ad332832bd33a1b85be07c8e9ceca3a861a0ac43dc8f', 14016), 'tools/file_tools.py': ('cf72649df9e5144edcacc94f92dde6bdf5cbd10054ef795755822944889d1bb1', 191360)}
OPERATION = 'edit'
ELIGIBILITY = None
INSTALLED227 = None
RECEIVED_SOURCE = None
VARIANT = 'v03'
ORIGINAL_CASE = {'case_id': 'F-03', 'case_index': 164, 'original_fixture_ref': 'FX-FMT', 'extension': 'docx', 'variant_id': 'v03', 'variant_source_text': 'Unicode', 'edit_pointer': '/operation_rows/16', 'preserve_pointer': '/operation_rows/20', 'operation': 'initial_genuine_upload_single_BODY_fact_edit_preserve_return_DOCX', 'maximum_trials_per_operation': 1, 'scope': 'DOCX_UNICODE_ONE_FACT_ONLY_NOT_FULL_WORD_APP_OR_OTHER_VARIANTS'}
FUTURE_POSTCONDITIONS = 'GENUINE_INGRESS_NATIVE_EDIT_RETURNED_BYTES_CUSTODY'
def need(ok,why):
 if not ok:raise ValueError(why)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(raw,path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def helper():
 p=Path(HELPER['path']);st=p.lstat();raw=p.read_bytes()
 need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and not st.st_mode&0o022 and len(raw)==HELPER['bytes']and digest(raw)==HELPER['sha256'],'READ227_exact_private_helper_required')
 return load(raw,p,'RootREAD227Helper')
def fixed_sources():
 h=helper();c=load(h.readref(CHECKER),CHECKER['path'],'RootREAD227GenericMetadata');t=load(h.readref(TRANSPORT),TRANSPORT['path'],'RootREAD227NativeProjection');return h,c,t

def expected_role_refs():
 return {name:dict(path=str(H/'hermes-agent'/name),sha256=sha,bytes=size)for name,(sha,size)in READ227_ROLES.items()}
def validate_installed227_assessment(value):
 need(type(value)is dict and set(value)=={'schema','operator','installed','project','native','plugins','base','product_source_commit','source_mode','family','variant','operation','baseline','word_roles','current_grant'},'DOCXUNI227_EXACT_ASSESSMENT_FIELDS_REQUIRED')
 need(value.get('schema')=='frw.Root.DOCX.UNICODE227.role-assessment.v1'and value.get('operator')=='Root'and (value.get('installed'),value.get('project'),value.get('native'),value.get('plugins'),value.get('base'))==(227,535,17895,52,17730)and all(type(value[k])is int for k in ('installed','project','native','plugins','base'))and value.get('product_source_commit')=='0f098a354033317fe4cf20dd7a225ad5b2442361'and value.get('source_mode')=='EXACT_INSTALLED227_WORD_UNICODE_EDIT'and value.get('family')==FAMILY and value.get('variant')==VARIANT and value.get('operation')==OPERATION and value.get('baseline')==BASE and value.get('word_roles')==expected_role_refs()and value.get('current_grant')is False,'DOCXUNI227_EXACT_WORD_ROLE_BASELINE_REQUIRED')
 return True
def validate_eligibility(value):
 need(type(value)is dict and set(value)=={'schema','operator','run_id','family','variant','operation','original_case','source','baseline','installed227_assessment','classification','old_effects_UNKNOWN_clocks_preserved','old_rows_modified','replay_authorized'},'DOCXUNI227_EXACT_ELIGIBILITY_FIELDS_REQUIRED')
 need(value.get('schema')=='frw.Root.DOCX.UNICODE227.effect-eligibility.v1'and value.get('operator')=='Root'and value.get('run_id')==RUN and value.get('family')==FAMILY and value.get('variant')==VARIANT and value.get('operation')==OPERATION and value.get('original_case')==ORIGINAL_CASE and value.get('source')==EXPECTED_SOURCE and value.get('baseline')==BASE and value.get('installed227_assessment')==INSTALLED227 and value.get('classification')=='GENUINELY_UNEXECUTED_ROOT_RECONCILED'and value.get('old_effects_UNKNOWN_clocks_preserved')is True and value.get('old_rows_modified')is False and value.get('replay_authorized')is False,'DOCXUNI227_UNEXECUTED_UNICODE_EDIT_REQUIRED')
 return True

def validate_proof_shape(proof,run_id,scenario,stage):
 need(ROOT_BOUND is True,'READ227_ROOT_UNBOUND_FAILCLOSED')
 need(type(proof)is dict and proof.get('schema')=='frw.Root.DOCX.UNICODE227.preintent-proof.v1' and proof.get('operator')=='Root'and proof.get('accepted')is True,'READ227_unbound_Root_preintent')
 need(run_id==RUN==proof.get('run_id')and digest(encoded(scenario))==proof.get('scenario_sha256'),'READ227_exact_original_scenario_required')
 need(type(proof.get('decisions'))is dict and all(proof['decisions'].get(k)is True for k in DECISIONS),'READ227_explicit_original_decisions_required')
 need(proof.get('baseline')==BASE and proof.get('future_ingress_read_answer_credit') is False and proof.get('operation')==OPERATION and proof.get('family')==FAMILY and proof.get('upload_input')==UPLOAD_INPUT and proof.get('effect_eligibility')==ELIGIBILITY and proof.get('installed227_assessment')==INSTALLED227 and proof.get('received_source')is None and proof.get('variant')==VARIANT and proof.get('original_case')==ORIGINAL_CASE and proof.get('future_postconditions')==FUTURE_POSTCONDITIONS,'READ227_exact_Root_bindings_no_future_credit')
 need(stage in ('NEW','READONLY','CURSOR_AUTHORITY','SCENARIO_VALIDATION','PRE_REQUEST_GUARD','PRE_INTENT_REVALIDATION'),'READ227_preoperation_only')
 wall,mono=time.time(),time.monotonic()
 for k in ('created_at','expires_at','created_monotonic','expires_monotonic'):need(type(proof.get(k))in(int,float),'READ227_finite_proof_clock')
 need(proof['created_at']<=wall<proof['expires_at']<=proof['created_at']+120 and proof['created_monotonic']<=mono<proof['expires_monotonic']<=proof['created_monotonic']+120,'READ227_stale_preintent')
 return True

def check(proof_ref,*,run_id,scenario,stage):
 need(ROOT_BOUND is True,'READ227_ROOT_UNBOUND_FAILCLOSED')
 h,c,t=fixed_sources();proof=h.doc(proof_ref);validate_proof_shape(proof,run_id,scenario,stage)
 eligibility=h.doc(ELIGIBILITY);assessment=h.doc(INSTALLED227)
 validate_eligibility(eligibility)
 validate_installed227_assessment(assessment)
 source=Path(UPLOAD_INPUT['path']);st=source.lstat();identity=lambda v:dict(device=v.st_dev,inode=v.st_ino,uid=v.st_uid,size_bytes=v.st_size,mtime_ns=v.st_mtime_ns,ctime_ns=v.st_ctime_ns)
 need(not any(q.is_symlink()for q in(source,*source.parents))and stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and identity(st)==UPLOAD_INPUT['stat'],'READ227_CURRENT_UPLOAD_SOURCE_IDENTITY_REQUIRED')
 h.readref(EXPECTED_SOURCE)
 need(identity(source.lstat())==identity(st),'READ227_CURRENT_UPLOAD_SOURCE_CAS_CHANGED')
 base=h.doc(BASE)
 # The fixed227 metadata consumer authenticates genuine canonical values now;
 # an assessment boolean or Source-written code-role map is never authority.
 closure=h.doc(c.CLOSURE);metadata=c.installation_metadata(closure)
 values={k:c.doc(r,private=False)for k,r in metadata['canonical4'].items()}
 c.installation_shapes(closure,values['source_receipt'],values['marker'],values['stamp'],values['input'])
 canonical=dict(metadata['canonical4']);canonical['receipt']=canonical.pop('source_receipt')
 need(type(base.get('canonical'))is dict and set(base['canonical'])=={'receipt','marker','stamp'}and all(base['canonical'][k]==canonical[k]for k in base['canonical']),'READ227_EXACT227_BASELINE_CANONICAL_REQUIRED')
 roles=expected_role_refs()
 need(type(base.get('source'))is dict and all(base['source'].get(k)==r for k,r in roles.items()),'READ227_EXACT227_BASELINE_READ_ROLES_REQUIRED')
 for name,r in roles.items():
  row=values['source_receipt'].get('files',{}).get(name,{})
  need(row.get('sha256')==r['sha256']and row.get('bytes')==r['bytes'],'DOCXUNI227_ACTUAL_RECEIPT_WORD_ROLE_CHANGED')
  h.readref(r,private=False)
 for label,ref in base['canonical'].items():h.readref(ref,private=False)
 for name,ref in base['source'].items():h.readref(ref,private=False)
 services,env=c.services(base['process_environment']);need(services==base['services'],'READ227_service_identity_changed')
 state=c.parse(c.read(H/'gateway_state.json',private=False));tg=state.get('platforms',{}).get('telegram',{})
 need(state.get('gateway_state')=='running' and state.get('active_agents')==0 and state.get('active_work')is None and not state.get('restart_requested') and state.get('served_profiles')==['default','dest_telegram','telegram-bot-8812646969']and tg.get('state')=='connected'and tg.get('needs_attention')is False,'READ227_gateway_not_quiescent')
 native=t.fresh_native(state);need(native['quiescent']and native['identity']==base['native']['identity'],'READ227_native_not_quiescent')
 dbs=c.databases()
 need(dbs=={k:{a:b for a,b in v.items()if a not in('quick_check','db_wal_shm_present')}for k,v in base['databases'].items()},'READ227_preintent_DB_or_principal_changed')
 permission=c.permission_current();need(permission==base['policy_namespace_only'],'READ227_current_policy_namespace_changed')
 need(not os.path.lexists(H/'maintenance.json')and not os.path.lexists(STATE/'observer-stop.json'),'READ227_cancel_or_maintenance_present')
 cooldown=STATE/'cooldown.json';need(not cooldown.exists()or c.doc(c.ref(cooldown)).get('until',0)<=time.time(),'READ227_cooldown_present')
 # A namespace check is no event/source capability. Native admission supplies it with a future ordinary event. No future write is preflight credit.
 for p in (H/'profiles/telegram-bot-8812646969',H/'profiles/telegram-bot-8812646969/workspace',H/'profiles/telegram-bot-8812646969/workspace/received'):
  st=p.lstat();need(not any(x.is_symlink()for x in(p,*p.parents))and stat.S_ISDIR(st.st_mode)and st.st_uid==os.getuid()and stat.S_IMODE(st.st_mode)==0o700,'READ227_private_ingress_workspace_required')
 need(set(proof['lock_owners'])=={'slot','consumer','credential'},'READ227_all_existing_locks_required')
 for path,key in ((SLOT,'slot'),(STATE/'consumer.lock','consumer'),(STATE/'tester-token','credential')):c.lock_held(path,proof['lock_owners'][key])
 if proof.get('clock')is not None:
  clock=h.doc(proof['clock']);need(clock['run_id']==run_id and clock['deadline_monotonic']-clock['started_monotonic']==900 and time.monotonic()+605<clock['deadline_monotonic'],'READ227_original_outer_clock_insufficient')
 # Exact old rows remain enforced by ordinary_independent_admission/current_rows.
 current_refs={p.name for p in (STATE/'runs').glob('*.json')};expected={r['id']+'.json'for r in base['history']}
 need(current_refs in(expected,expected|{run_id+'.json'}),'READ227_unreviewed_history_delta')
 need(c.profile_config_refs()==base['policy_namespace_only']['profile_configs'],'READ227_configs_or_effective_roots_changed')
 need(t.fresh_native(state)['quiescent'],'READ227_final_native_state_changed')
 validate_proof_shape(proof,run_id,scenario,stage)
 return True
