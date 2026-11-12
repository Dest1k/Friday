"""Root-owned missing first-user-API caller after O/X prebirth and Y born-closed refusal, separate Root-selected current authority; historical R106 remains closed. Import is inert.
SOURCE ONLY: default UNBOUND. Root must separately supply and accept exact facts.
No credential appears in argv/env/reports. The PRIVATE scenario is an input file.
"""
import datetime as dt, fcntl, hashlib, json, math, os, resource, signal, stat, subprocess, sys, time, types, uuid
from pathlib import Path
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
ORIGINAL_DIR=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
PREBIRTH_CLOSURE={'path':str(ORIGINAL_DIR/'PREBIRTH-ISSUER-ONLY-CLOSURE.json'),'bytes':2688,'sha256':'d8f6c472ab34a1349e8dfb49ead0a95383aa479728c8d0fa818a4446b12a83f5'}
EXISTING_AUTHORITY={'path':'/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R106.json','bytes':14157,'sha256':'3dac8de65e8cd1e7ccb612b5eddccbed12bc256b8e67e56fd280b7d8d12d97ec'}
EXISTING_AUTHORITY_ID='ordinary-f04-postfix-diagnostic-20261112-r106'
EXISTING_CREATED=1794457434.732844
EXISTING_EXPIRES=1794479034.732844
ORIGINAL_RUN='f06-first-docx-wrong-read-20261112-r1'
ORIGINAL_SCENARIO_SHA='91e3c83b52337b7b62349533354cab88486f2ba3a7f946f58059b52bcecb75b3'
BINDING_DIR=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-CONSUMER-EXISTING-R106-20261112')
BINDING_PREBIRTH_CLOSURE={'path':str(BINDING_DIR/'PREBIRTH-BINDING-RECONSTRUCTION-REFUSAL-CLOSURE.json'),'bytes':2787,'sha256':'88d9d8ca60a732597935602af1af54d730b7c3887f41c3c11a701aa72afc5cc0'}
Y_DIR=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112')
Y_PREINTENT_CLOSURE={'path':str(Y_DIR/'PREINTENT-GUARD-REFUSAL-CLOSURE.json'),'bytes':2140,'sha256':'3ba160ed4c5955421fe5dc5cc7e422d6e9fadc2793aa1efe7b1aebaa1756a88d'}
Y_SAVED_ASSESSMENT={'path':'/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-Y-PREINTENT-REFUSAL-ROOT-SAVED-ASSESSMENT-20261112.json','bytes':2084,'sha256':'8be2ca0e659c8ce4e51aa72c21c94f2de4208ccf8c139da910e2043db12715e2'}
Y_INDEPENDENT_REVIEW={'path':'/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-Y-PREINTENT-CLOSURE-20261112/REVIEW.json','bytes':17730,'sha256':'581a9a080b2acc96cb00a5a4a5a157ceb92332be43bd315507e065f7aa3dd4e7'}
Y_HISTORY_PINS={'CONSUMER-CLOCK.json': {'bytes': 257,
                         'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/CONSUMER-CLOCK.json',
                         'sha256': 'ce12e89ccb3d583ed3e20f6cb6b828792725538c5e51d43fc7a7057c4fc21bd9'},
 'source/SOURCE-FREEZE.json': {'bytes': 711,
                               'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/source/SOURCE-FREEZE.json',
                               'sha256': '50d169e40335ffe384790642ad39dcecc0fef37a95b5fe99323ab22140b47d39'},
 'source/current207.py': {'bytes': 37442,
                          'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/source/current207.py',
                          'sha256': '63863895d3d205c956eb272b5aa448648783a827eaaedbe8d5cf49b3fcbd08c3'},
 'source/f06_footer.py.txt': {'bytes': 6987,
                              'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/source/f06_footer.py.txt',
                              'sha256': '089d17c3f8b4bb333a62a1f4b6b0538b07bd4764b834f6e786e9e8cdd98460e6'},
 'source/f06_source.py': {'bytes': 18412,
                          'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/source/f06_source.py',
                          'sha256': '519a7acb754b1e40549fa83e35793463e016bf86c5646e130e0cfb87d041a919'},
 'source/root_bind_existing_consumer_once.py': {'bytes': 27738,
                                                'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/source/root_bind_existing_consumer_once.py',
                                                'sha256': '7d759ca77ebec28f7783ac101fb9c88163b56498aaf9e79cae8fd20832390600'},
 'work/ROOT-ACTUAL-BINDING.json': {'bytes': 8351,
                                   'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-ACTUAL-BINDING.json',
                                   'sha256': 'e35f9ff211f7497b3a0719c9f81f68c3e816f2ba6460681b5fdfbd03d95dd19a'},
 'work/ROOT-CONSUMER-ACTOR.json': {'bytes': 415,
                                   'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-CONSUMER-ACTOR.json',
                                   'sha256': '110ac8e6279c527e79e9d83d3afd3b160083a91f074ce1c16d369267a2d056d5'},
 'work/ROOT-DISPATCH-ENDED.json': {'bytes': 336,
                                   'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-DISPATCH-ENDED.json',
                                   'sha256': 'b37f03d5bcc4d52d1c7baf2889bc8830f516f2e98c2f761b937a0e49935dabc3'},
 'work/ROOT-DISPATCH-INVOCATION.json': {'bytes': 1024,
                                        'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-DISPATCH-INVOCATION.json',
                                        'sha256': '32212fc2b86cd1ded20f0ba8f89061521d87b90b74e2228937598e2930c507f0'},
 'work/ROOT-FIRST-CONSUMER-ONCE.json': {'bytes': 1346,
                                        'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-FIRST-CONSUMER-ONCE.json',
                                        'sha256': 'ff175d4a623bd05222c5dca16aaf0ea7b17c5bd48a4935c1c5caed50eb12c387'},
 'work/ROOT-FRESH-CURRENT-PROOF.json': {'bytes': 2496998,
                                        'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/ROOT-FRESH-CURRENT-PROOF.json',
                                        'sha256': '0c4da2fe80a594a0814f1c1c10bed2407f0816642083f0de7aca5dd5d462c7df'},
 'work/bot_tester.f06.root-bound.py': {'bytes': 1149079,
                                       'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/work/bot_tester.f06.root-bound.py',
                                       'sha256': '4fd99efc0b8b32ed7ee3472c2cdc2cb96f4c3329db882ff9074cc394cd4588ee'}}
Y_RECONCILIATION_SCHEMA='frw.Root.F06.closed-Y-missing-first-user-API-reconciliation.v1'
Y_STAGE_STATUS='ROOT_BOUND_SEPARATE_MISSING_FIRST_USER_API_AFTER_CLOSED_Y'
Y_RECONCILIATION_BOOLS=('actual_y_consumer_born_and_closed','first_user_API_never_started','no_user_BotAPI_request_before_synchronous_current_gate_refusal','old_O_X_Y_once_clocks_source_binding_preserved','no_old_caller_issuer_or_consumer_retry','same_original_run_scenario_R106_only','missing_first_user_API_only_authorized','raw_REFUSED_OR_UNKNOWN_preserved','nested_cause_not_originally_retained','no_unknown_API_effect_assumed_absent')

CURRENT_INPUT_SCHEMA='frw.Root.F06.canonical-postboot-current-first-user-API-after-closed-preintent.v1'
CURRENT_Y_SCHEMA='frw.Root.F06.closed-Y-postboot-current-missing-first-user-API-reconciliation.v1'
CURRENT_STAGE_STATUS='ROOT_BOUND_SEPARATE_POSTBOOT_CURRENT_MISSING_FIRST_USER_API_AFTER_CLOSED_Y'
SELECTION_SCHEMA='frw.Root.F06.postY-current-admission-selection.v1'
SELECTION_STATUS='ROOT_EXPLICIT_CURRENT_ADMISSION_SELECTED_MISSING_FIRST_API_ONLY'
# Fixed prior-power descriptors are historical provenance only, never admission criteria.
PROVENANCE_POSTBOOT_ID='4d38196f-04ed-4b84-bcf4-a272d4633787'
RECOVERY_DIR=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261112-EVENING')
PROVENANCE_ROOT_RECOVERY={'path':str(RECOVERY_DIR/'ROOT-RECOVERY-ACCEPTANCE.json'),'bytes':2597,'sha256':'a276de54c57dca257dc049bc453b38501f88a908472c668c8a732e969f4ac2ec'}
PROVENANCE_ROOT_DELTA={'path':str(RECOVERY_DIR/'PERSISTENT-AND-BOOT-DELTA.json'),'bytes':1637,'sha256':'9d92d5e8154346ce05c4246e0f6587ad98edbfac696e0cb9901f3e078b9ed11a'}
PROVENANCE_ROOT_OBSERVATION={'path':str(RECOVERY_DIR/'CURRENT-OBSERVED-METADATA-NOT-ADMISSION.json'),'bytes':2488766,'sha256':'0ce784477296342850ff88817c13ffda8c68d4fed6c9ea0690f64586af4cef03'}
ADMISSION_ADAPTER_BYTES=18622
ADMISSION_ADAPTER_SHA='a82ccbd4366f88f39abdb724ebfe4280b9da39da8311144f1a943eb512ed01b1'
SELECTION_BOOLS=('historical_R106_expired_not_extended','same_original_R1_scenario_source_scope','Y_born_closed_no_user_API_reconciled','separate_missing_first_API_explicitly_selected','postboot_persistent_data_exactly_reconciled','no_old_issuer_caller_once_clock_retry','no_automatic_issuer_authority_or_fallback','unknown_effect_not_assumed_absent','prior_closed_effects_and_clocks_preserved','current_source_bulk_review_required')
CURRENT_Y_RECONCILIATION_BOOLS=tuple('same_original_run_scenario_source_scope_only' if k=='same_original_run_scenario_R106_only' else k for k in Y_RECONCILIATION_BOOLS)

def descriptor(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'} and type(r['bytes']) is int and 0<r['bytes']<=24*1024**2 and type(r['sha256']) is str and len(r['sha256'])==64 and all(k in '0123456789abcdef' for k in r['sha256']),'F06_EXACT_CURRENT_DESCRIPTOR_REQUIRED')
    canonical_path(r['path']);return r

def _selected_shape(c, selected, selection_ref):
    descriptor(selected);descriptor(selection_ref)
    need(selected==c.get('authority') and selected['path']!=EXISTING_AUTHORITY['path'] and selected['sha256']!=EXISTING_AUTHORITY['sha256'] and selection_ref['path'] not in (selected['path'],EXISTING_AUTHORITY['path']) and selection_ref['sha256'] not in (selected['sha256'],EXISTING_AUTHORITY['sha256']),'F06_CURRENT_SELECTION_MUST_DIFFER_FROM_HISTORICAL_R106')
    ident=c.get('authority_id')
    need(type(ident) is str and 1<=len(ident)<=256 and ident not in ('UNBOUND',EXISTING_AUTHORITY_ID) and all(32<ord(k)<127 for k in ident),'F06_CURRENT_SELECTED_AUTHORITY_ID_REQUIRED')
    chain=c.get('authority_chain')
    need(type(chain) is dict and chain.get('predecessor')==EXISTING_AUTHORITY and chain.get('predecessor_authority_id')==EXISTING_AUTHORITY_ID,'F06_CURRENT_IMMEDIATE_PREDECESSOR_MUST_BE_HISTORICAL_R106')

def _postboot_basis(selected_basis):
    need(type(selected_basis) is dict and set(selected_basis)=={'recovery_acceptance','persistent_runtime_delta','postboot_observation'},'F06_EXPLICIT_POSTBOOT_BASIS_REQUIRED')
    for pin in selected_basis.values():descriptor(pin)
    need(len({pin['path'] for pin in selected_basis.values()})==3,'F06_DISTINCT_POSTBOOT_BASIS_DOCUMENTS_REQUIRED')
    return selected_basis

def _recovery_time(recovery):
    try:
        value=dt.datetime.fromisoformat(recovery['at_moscow'])
        need(value.tzinfo is not None,'F06_ROOT_RECOVERY_TIMESTAMP_REQUIRED')
        stamp=value.timestamp()
        need(math.isfinite(stamp),'F06_ROOT_RECOVERY_TIMESTAMP_REQUIRED')
        return stamp
    except (KeyError,TypeError,ValueError,OverflowError):
        raise ValueError('F06_ROOT_RECOVERY_TIMESTAMP_REQUIRED') from None

HISTORICAL_HISTORY_SHA256='7e4229d55cefef760778445f78e87f8516fb0fdf7d27a3d43471061278d44d29'
HISTORICAL_UNKNOWN_IDS=('f03-csv-edit-preserve-01-20261110','root-m12-upload-b14b8b3ee0a2','root-source110-fresh-xlsx-cell-edit-r1')
GATEWAY_STATE_PATH='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/gateway_state.json'
def current_document_metadata(current, anchor):
    """Exact inherited45/3UNKNOWN policy and selected physical consumer inputs.
    The known digest is Root's static R106 map, not a new history acceptance.
    Actual generic schema/canonical/scope/run/parent/time guard remains a.admission.
    """
    history=current.get('history')
    need(type(history) is dict and len(history)==45 and digest(encoded(history))==HISTORICAL_HISTORY_SHA256,'F06_CURRENT_ADMISSION_MUST_PRESERVE_EXACT_45_HISTORY_ROWS')
    need({k for k,row in history.items() if row.get('unknown_retained') is True}==set(HISTORICAL_UNKNOWN_IDS) and all(row.get('new_effect_replay_authorized') is False and row.get('unknown_retained') is (row.get('send_state')=='unknown') for row in history.values()),'F06_CURRENT_ADMISSION_UNKNOWN_AND_NO_REPLAY_REQUIRED')
    flags={'new_independent_inputs_only':True,'no_old_task_replay':True,'old_rows_modified':False,'unknown_effects_resolved':False,'product_or_B00_acceptance':False,'new_trial_for_historical_task':False,'same_canonical_local_run':False}
    need(all(current.get(k) is v for k,v in flags.items()) and 'ordered_predecessors' not in current and 'memory_case' not in current,'F06_CURRENT_ADMISSION_HISTORICAL_POLICY_FLAGS_REQUIRED')
    canonical={'canonical_sha256':"json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(',', ':')) with no trailing newline",'tester_sha256':"bot_tester.encoded(scenario): json.dumps(scenario, ensure_ascii=True, sort_keys=True) + newline"}
    need(current.get('canonical_encoding')==canonical,'F06_CURRENT_ADMISSION_ORIGINAL_ENCODING_REQUIRED')
    gateway=current.get('gateway',{});actual=anchor.get('gateway',{})
    need(current.get('boot_id')==actual.get('boot_id') and type(gateway) is dict and set(gateway)=={'pid','start_time','state_path','maximum_staleness_seconds'} and gateway.get('pid')==actual.get('pid') and gateway.get('start_time')==actual.get('start_time') and gateway.get('state_path')==GATEWAY_STATE_PATH and type(gateway.get('maximum_staleness_seconds')) is int and gateway['maximum_staleness_seconds']==600,'F06_CURRENT_ADMISSION_SELECTED_PHYSICAL_TUPLE_REQUIRED')
    return True

def selection(c, selection_ref, *, selected_basis, effect_binding=True):
    """Verify a separate Root decision and current canonical ordinary admission.
    No authority, clock, issuer, or operation is created. False is preparation
    only, before the frame derives its lineage; actual caller always uses True.
    """
    basis=_postboot_basis(selected_basis)
    need(type(effect_binding) is bool,'F06_SELECTION_EFFECT_BINDING_BOOL_REQUIRED')
    need(type(c) is dict,'F06_CURRENT_CONTRACT_REQUIRED')
    _selected_shape(c,c.get('authority'),selection_ref)
    descriptor(c.get('adapter'))
    need(c['adapter']['bytes']==ADMISSION_ADAPTER_BYTES and c['adapter']['sha256']==ADMISSION_ADAPTER_SHA,'F06_UNCHANGED_REVIEWED_ADMISSION_ADAPTER_REQUIRED')
    a=load(c['adapter'],'Root_postboot_current_admission_adapter')
    a.contract_shape(c)
    need(c['run_id']==ORIGINAL_RUN and c['scenario_sha256']==ORIGINAL_SCENARIO_SHA and c['scenario_ref']['sha256']==ORIGINAL_SCENARIO_SHA,'F06_SAME_ORIGINAL_RUN_SCENARIO_REQUIRED')
    sraw=readref(selection_ref);s=json.loads(sraw,object_pairs_hook=unique)
    need(type(s) is dict and encoded(s)==sraw and s.get('schema')==SELECTION_SCHEMA and s.get('operator')=='Root' and s.get('status')==SELECTION_STATUS,'F06_EXPLICIT_CANONICAL_ROOT_CURRENT_SELECTION_REQUIRED')
    need(s.get('historical_R106')==EXISTING_AUTHORITY and s.get('selected_admission')==c['authority'] and s.get('selected_authority_id')==c['authority_id'] and s.get('predecessor_authority_id')==EXISTING_AUTHORITY_ID,'F06_CURRENT_SELECTION_EXACT_AUTHORITY_CHAIN_REQUIRED')
    need(s.get('original_run_id')==ORIGINAL_RUN and s.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and s.get('source')==c['source'] and s.get('scope')==c['scope'] and s.get('y_preintent_closure')==Y_PREINTENT_CLOSURE and s.get('y_saved_assessment')==Y_SAVED_ASSESSMENT and s.get('y_independent_review')==Y_INDEPENDENT_REVIEW,'F06_CURRENT_SELECTION_ORIGINAL_SCOPE_AND_Y_REQUIRED')
    need(all(s.get(key)==pin for key,pin in basis.items()),'F06_CURRENT_SELECTION_EXACT_POSTBOOT_RECOVERY_REQUIRED')
    for k in SELECTION_BOOLS:need(s.get(k) is True,'F06_CURRENT_SELECTION_EXPLICIT_ROOT_DECISIONS_REQUIRED')
    recovery=json.loads(readref(basis['recovery_acceptance']),object_pairs_hook=unique)
    delta=json.loads(readref(basis['persistent_runtime_delta']),object_pairs_hook=unique)
    readref(basis['postboot_observation'])
    need(type(recovery) is dict and type(delta) is dict,'F06_SELECTED_POSTBOOT_METADATA_OBJECTS_REQUIRED')
    common=recovery.get('schema')=='friday.root.postpower.recovery-acceptance.v1' and recovery.get('operator')=='Root' and recovery.get('persistent_runtime_delta')==basis['persistent_runtime_delta'] and delta.get('schema')=='friday.root.postpower.observed-delta.v1' and delta.get('current_observation')==basis['postboot_observation'] and delta.get('new_admission') is False
    need(common,'F06_EXACT_ROOT_RECOVERY_ACCEPTANCE_REQUIRED')
    if recovery.get('state')=='ACCEPT_INSTALLED_SOURCE_DATA_READONLY_RUNTIME_AND_DEPENDENCY_RECOVERY_NOT_USER_TEST_ADMISSION':
        boot=recovery.get('current_gateway',{}).get('boot_id')
        need(recovery.get('old_Y_no_user_API_assessment')==Y_SAVED_ASSESSMENT and recovery.get('R106_current_validity')=='EXPIRED_AND_DIFFERENT_BOOT_CANNOT_ADMIT' and recovery.get('new_admission_or_clock') is False,'F06_EXACT_ROOT_RECOVERY_ACCEPTANCE_REQUIRED')
        need(delta.get('after_gateway',{}).get('boot_id')==boot and delta.get('old_R106_expires_at_preserved')==EXISTING_EXPIRES and delta.get('old_R106_expired_and_old_boot') is True,'F06_EXACT_ROOT_PERSISTENT_DELTA_REQUIRED')
    elif recovery.get('state')=='ACCEPT_POSTBOOT_SOURCE_PERSISTENT_DATA_AND_READONLY_RUNTIME_BASIS_QWEN_LOADING_NOT_USER_TEST_ADMISSION':
        # This explicitly known Root metadata variant is a readonly recovery
        # basis. Its old-E predecessor is historical provenance, not authority.
        boot=recovery.get('boot_id')
        integrity={'path':'/home/jericho/.cache/FRW-ASTRA-POSTPOWER-INSTALLED207-INTEGRITY-20261112/RESULT.json','bytes':4604,'sha256':'239ae4809df8f0225414fe988b18fc713af34a1954d4ce05167b49168eef3cac'}
        need(recovery.get('current_observation')==basis['postboot_observation'] and recovery.get('previous_recovery')==PROVENANCE_ROOT_RECOVERY and recovery.get('prior_full_manifest_integrity')==integrity and recovery.get('full17891_rerun') is False and recovery.get('first_F06_user_API')=='NOT_RUN' and recovery.get('new_admission_clock_or_replay') is False and recovery.get('Qwen')=='OWNER_REPORT_LOADING_NO_LIVE_INFERENCE_ADMISSION','F06_EXACT_REPEAT_ROOT_RECOVERY_ACCEPTANCE_REQUIRED')
        unchanged=delta.get('persistent_fields_unchanged')
        need(type(unchanged) is dict and set(unchanged)=={'installed_product','databases','history','cursor','cooldown','source','profile_configs','source_identity'} and all(value is True for value in unchanged.values()) and delta.get('current_gateway',{}).get('boot_id')==boot and delta.get('previous_verified_boot')==PROVENANCE_POSTBOOT_ID and delta.get('current_runtime_source_plugin_hashes_verified') is True and delta.get('full_native17891_rehashed_this_operation') is False and delta.get('prior_full17891_integrity_reused')=='239ae4809df8f0225414fe988b18fc713af34a1954d4ce05167b49168eef3cac; no installed source writes since' and delta.get('Qwen')=='OWNER_REPORT_LOADING_NO_INFERENCE_ADMISSION','F06_EXACT_REPEAT_ROOT_PERSISTENT_DELTA_REQUIRED')
    else:raise ValueError('F06_UNKNOWN_ROOT_RECOVERY_METADATA_VARIANT')
    try:need(type(boot) is str and str(uuid.UUID(boot))==boot,'F06_ROOT_SELECTED_BOOT_UUID_REQUIRED')
    except (ValueError,AttributeError):raise ValueError('F06_ROOT_SELECTED_BOOT_UUID_REQUIRED') from None
    need(s.get('boot_id')==boot,'F06_CURRENT_SELECTION_BOOT_MISMATCH')
    need(s.get('current_operation_dependencies_ready') is True,'F06_CURRENT_OPERATION_DEPENDENCIES_NOT_ROOT_ACCEPTED')
    descriptor(s.get('readiness_evidence'));readref(s['readiness_evidence'])
    recovered_at=_recovery_time(recovery)
    # Use the frozen adapter's actual canonical/schema/chain/scope/run/time guard.
    # Its immediate historical predecessor may be expired; it is not current.
    current=json.loads(readref(c['authority']),object_pairs_hook=unique)
    anchor=json.loads(readref(basis['postboot_observation']),object_pairs_hook=unique)
    current_document_metadata(current,anchor)
    a.admission(c,current,read=read)
    chain=c['authority_chain'];now=time.time()
    need(all(type(s.get(k)) in (int,float) and math.isfinite(s[k]) for k in ('created_at','expires_at')) and max(chain['created_at'],recovered_at)<=s['created_at']<=now<s['expires_at']<=chain['expires_at'] and s['created_at']<s['expires_at']<=s['created_at']+6*3600,'F06_ROOT_CURRENT_SELECTION_STALE_OR_OUTSIDE_ADMISSION')
    if effect_binding:
        lineage=json.loads(readref(c['root_proofs']['source_ingress_lineage']),object_pairs_hook=unique)
        need(lineage.get('current_admission_selection')==selection_ref and lineage.get('current_selected_admission')==c['authority'] and lineage.get('postboot_recovery_acceptance')==basis['recovery_acceptance'] and lineage.get('postboot_basis')==basis and lineage.get('readiness_evidence')==s['readiness_evidence'],'F06_CURRENT_SELECTION_NOT_PINNED_IN_WHOLE_EFFECT_LINEAGE')
        need(c.get('boundary',{}).get('gateway',{}).get('boot_id')==boot,'F06_CURRENT_SELECTION_GATEWAY_BOOT_MISMATCH')
    return s

PYTHON='/home/jericho/jericho/.venv/bin/python'
def need(v,msg):
    if not v:raise ValueError(msg)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(v):return hashlib.sha256(v).hexdigest()
def unique(pairs):
    out={}
    for k,v in pairs:need(k not in out,'F06_DUPLICATE_JSON_KEY');out[k]=v
    return out
def identity(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def canonical_path(path):
    text=path if type(path) is str else str(path) if isinstance(path,Path) else None
    need(type(text) is str and text.startswith('/') and not text.startswith('//')
          and not any(ord(ch)<32 or 127<=ord(ch)<=159 for ch in text), 'F06_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    try:text.encode('utf-8')
    except UnicodeError:raise ValueError('F06_CANONICAL_UTF8_PATH_REQUIRED') from None
    need((text=='/' or not any(part in ('','.','..') for part in text.split('/')[1:]))
          and str(Path(text))==text, 'F06_LEXICAL_PATH_ALIAS_REFUSED')
    return Path(text)

def read(path,limit=24*1024**2,*,private=True):
    p=canonical_path(path);need(not any(x.is_symlink() for x in (p,*p.parents)),'F06_ABSOLUTE_NO_SYMLINK_REQUIRED')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        b=os.fstat(f.fileno());raw=f.read(limit+1);a=os.fstat(f.fileno())
    need(stat.S_ISREG(b.st_mode) and b.st_uid==os.getuid() and b.st_nlink==1 and not stat.S_IMODE(b.st_mode)&0o002 and len(raw)<=limit and identity(b)==identity(a)==identity(p.stat()),'F06_UNSAFE_OR_CHANGED_INPUT')
    need(not private or stat.S_IMODE(b.st_mode)==0o600,'F06_PRIVATE_INPUT0600_REQUIRED');return raw

def ref(path,*,private=True):
    raw=read(path,private=private);return {'path':str(path),'bytes':len(raw),'sha256':digest(raw)}
def readref(r,*,private=True):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'},'F06_EXACT_INPUT_REFERENCE_REQUIRED');raw=read(r['path'],private=private);need(len(raw)==r['bytes'] and digest(raw)==r['sha256'],'F06_PIN_CHANGED');return raw
def load(r,name,*,private=True):
    raw=readref(r,private=private);m=types.ModuleType(name);m.__file__=r['path'];exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
def new(path,raw):
    path=canonical_path(path)
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def validate_inputs(v):
    need(type(v) is dict and set(v)=={'schema','status','contract','source_freeze','independent_review','workdir','slot_identity','expected_binding_sha256','prebirth_closure','binding_prebirth_closure','prebirth_reconciliation','y_preintent_closure','y_saved_assessment','y_independent_review','y_reconciliation','selected_admission','admission_selection','postboot_basis'} and v['schema']==CURRENT_INPUT_SCHEMA and v['status']==CURRENT_STAGE_STATUS,'F06_CONSUMER_STAGE_UNBOUND_NO_EFFECT')
    _postboot_basis(v['postboot_basis'])
    c=v['contract']
    need(type(c) is dict and c.get('status')=='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD' and c.get('run_id')==ORIGINAL_RUN and c.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and c.get('scenario_ref',{}).get('sha256')==ORIGINAL_SCENARIO_SHA,'F06_ONLY_ORIGINAL_RUN_AND_SELECTED_CURRENT_ADMISSION')
    _selected_shape(c,v['selected_admission'],v['admission_selection'])
    need(v['prebirth_closure']==PREBIRTH_CLOSURE and v['binding_prebirth_closure']==BINDING_PREBIRTH_CLOSURE and v['y_preintent_closure']==Y_PREINTENT_CLOSURE and v['y_saved_assessment']==Y_SAVED_ASSESSMENT and v['y_independent_review']==Y_INDEPENDENT_REVIEW,'F06_EXISTING_ISSUANCE_OR_CLOSURE_CHANGED')
    need(type(v['workdir']) is str and canonical_path(v['workdir']).is_absolute() and v['expected_binding_sha256'] is None,'F06_FRESH_CONSUMER_BINDING_REQUIRED')
    work=canonical_path(v['workdir'])
    need(all(not work.is_relative_to(old) and not old.is_relative_to(work) for old in (ORIGINAL_DIR,BINDING_DIR,Y_DIR)),'F06_OLD_DRIVER_WORKDIR_MUST_REMAIN_UNTOUCHED')
    return True

def _closed_y_history(v):
    """Authenticate exact saved born-closed Y; no fresh operation is admitted."""
    need(v.get('y_preintent_closure')==Y_PREINTENT_CLOSURE and v.get('y_saved_assessment')==Y_SAVED_ASSESSMENT and v.get('y_independent_review')==Y_INDEPENDENT_REVIEW,'F06_EXACT_CLOSED_Y_REFS_REQUIRED')
    # Authenticate all Y history before inspecting any fresh/current proof. No
    # executable historical module is loaded, and no diagnostic/log body read.
    y=json.loads(readref(v['y_preintent_closure']),object_pairs_hook=unique)
    assessment=json.loads(readref(v['y_saved_assessment']),object_pairs_hook=unique)
    review=json.loads(readref(v['y_independent_review']),object_pairs_hook=unique)
    need(y.get('schema')=='friday.root.F06.first-consumer-preintent-guard-closure.v1' and y.get('state')=='ACTUAL_CONSUMER_BORN_CLOSED_REFUSED_IN_NEW_BEFORE_SAVE_OR_BOTAPI_REQUEST' and y.get('consumer_exit_code')==2 and y.get('consumer_actor_absent') is True and y.get('parent_slot_owner_absent') is True and y.get('slot_free') is True and y.get('canonical_run_absent') is True and y.get('BotAPI_client_constructed') is True and y.get('upload_model_reply_Office') is False and y.get('raw_status_preserved')=='REFUSED_OR_UNKNOWN' and y.get('actual_original_nested_exception_was_retained') is False and y.get('nested_cause_classification')=='SOURCE_DERIVED_REPRODUCTION_NOT_ORIGINAL_RETAINED_EXCEPTION' and y.get('retry_or_followup_authorized_by_this_record') is False,'F06_EXACT_Y_BORN_CLOSED_NO_FIRST_API_REQUIRED')
    need(assessment.get('schema')=='friday.root.F06.Y.saved-preintent-assessment.v1' and assessment.get('operator')=='Root' and assessment.get('state')=='ACCEPT_SOURCE_DERIVED_NO_USER_BOTAPI_BEFORE_CURRENT_GATE_REFUSAL_RAW_UNKNOWN_PRESERVED' and assessment.get('original_closure')==Y_PREINTENT_CLOSURE and assessment.get('independent_review')==Y_INDEPENDENT_REVIEW and assessment.get('consumer_born_and_closed') is True and assessment.get('BotAPI_client_constructed') is True and assessment.get('raw_status')=='REFUSED_OR_UNKNOWN' and assessment.get('canonical_run_created') is False and assessment.get('first_user_upload_or_model_or_reply')=='NOT_RUN' and assessment.get('ordinary_semantic_or_F06_acceptance') is False and assessment.get('automatic_retry_or_followup_authorized') is False,'F06_EXACT_ROOT_SAVED_Y_ASSESSMENT_REQUIRED')
    need(review.get('schema')=='frw.independent-review.F06-Y-preintent-no-send.v1' and review.get('recommendation')=='ACCEPT_ROOT_CLOSURE_CLASSIFICATION_WITH_EXPLICIT_SOURCE_DERIVED_INNER_CAUSE_LIMITATION' and review.get('observed',{}).get('Y_consumer_did_start') is True and review.get('observed',{}).get('raw_status_preserved')=='REFUSED_OR_UNKNOWN' and review.get('reader_cause_assessment',{}).get('original_nested_exception_observed') is False and all(review.get('exact_pins',{}).get(k)==pin for k,pin in Y_HISTORY_PINS.items()),'F06_EXACT_INDEPENDENT_Y_REVIEW_REQUIRED')
    saved={k:readref(pin) for k,pin in Y_HISTORY_PINS.items()}
    oldy={k: Y_HISTORY_PINS[leaf] for k,leaf in (('clock','CONSUMER-CLOCK.json'),('once','work/ROOT-FIRST-CONSUMER-ONCE.json'),('source','work/bot_tester.f06.root-bound.py'),('binding','work/ROOT-ACTUAL-BINDING.json'),('dispatch','work/ROOT-DISPATCH-INVOCATION.json'),('actor','work/ROOT-CONSUMER-ACTOR.json'),('ended','work/ROOT-DISPATCH-ENDED.json'),('freshproof','work/ROOT-FRESH-CURRENT-PROOF.json'))}
    parse=lambda key:json.loads(saved[key],object_pairs_hook=unique)
    yo=parse('work/ROOT-FIRST-CONSUMER-ONCE.json');yc=parse('CONSUMER-CLOCK.json');yb=parse('work/ROOT-ACTUAL-BINDING.json')
    yd=parse('work/ROOT-DISPATCH-INVOCATION.json');ye=parse('work/ROOT-DISPATCH-ENDED.json');yf=parse('source/SOURCE-FREEZE.json')
    need(yo.get('schema')=='frw.Root.F06.canonical-first-consumer-invocation.v1' and yo.get('run_id')==ORIGINAL_RUN and yo.get('existing_authority')==EXISTING_AUTHORITY and yo.get('prebirth_closure')==PREBIRTH_CLOSURE and yo.get('binding_prebirth_closure')==BINDING_PREBIRTH_CLOSURE and yo.get('old_driver_resume') is False and yo.get('issuer_invoked') is False and yo.get('no_retry') is True and yo.get('source_freeze')==Y_HISTORY_PINS['source/SOURCE-FREEZE.json'],'F06_Y_ONCE_PROVENANCE_CHANGED')
    need(yo.get('binding',{}).get('path')==str(Y_DIR/'ROOT-CONSUMER-INPUTS.json'),'F06_Y_INPUT_PROVENANCE_PATH_CHANGED')
    oldinputs=json.loads(readref(yo['binding']),object_pairs_hook=unique)
    need(oldinputs.get('schema')=='frw.Root.F06.canonical-existing-R106-first-consumer.v1' and oldinputs.get('status')=='ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER' and oldinputs.get('prebirth_closure')==PREBIRTH_CLOSURE and oldinputs.get('binding_prebirth_closure')==BINDING_PREBIRTH_CLOSURE and oldinputs.get('prebirth_reconciliation')==v['prebirth_reconciliation'] and oldinputs.get('source_freeze')==Y_HISTORY_PINS['source/SOURCE-FREEZE.json'],'F06_Y_INPUT_AND_HISTORICAL_O_X_RECONCILIATION_CHANGED')
    need(yf.get('schema')=='frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1' and type(yf.get('files')) is dict and set(yf['files'])=={'current207.py','f06_footer.py.txt','f06_source.py','root_bind_existing_consumer_once.py'} and all(yf['files'][leaf]=={key:Y_HISTORY_PINS['source/'+leaf][key] for key in ('bytes','sha256')} for leaf in yf['files']),'F06_Y_SOURCE_FREEZE_CHANGED')
    ycontract=yb.get('contract',{});inputcontract=oldinputs.get('contract',{})
    need(yb.get('schema')=='frw.Root.F06.exact-first-wrongread-binding.v1' and yb.get('source')==oldy['source'] and yb.get('authority')==EXISTING_AUTHORITY and ycontract.get('authority')==EXISTING_AUTHORITY and ycontract.get('authority_id')==EXISTING_AUTHORITY_ID and ycontract.get('authority_chain',{}).get('created_at')==EXISTING_CREATED and ycontract['authority_chain'].get('expires_at')==EXISTING_EXPIRES and ycontract.get('run_id')==ORIGINAL_RUN and ycontract.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and ycontract.get('scenario_ref',{}).get('sha256')==ORIGINAL_SCENARIO_SHA and ycontract.get('scope')==v['contract'].get('scope') and ycontract.get('resources',{}).get('clock')==oldy['clock'] and ycontract.get('root_current_proof')==oldy['freshproof'] and dict(ycontract,root_current_proof=inputcontract.get('root_current_proof'))==inputcontract,'F06_Y_HISTORY_CONTRACT_OR_SOURCE_CHANGED')
    expected_argv=[PYTHON,'-I','-B','-S',oldy['source']['path'],'--state-dir',str(STATE),'run','--run-id',ORIGINAL_RUN,'--scenario',ycontract['scenario_ref']['path']]
    need(yd.get('state')=='ONE_UNSTARTED_USER_CONSUMER_AFTER_TWO_CLOSED_PREBIRTH_FAILURES_NO_RETRY' and yd.get('argv')==expected_argv and yd.get('source')==oldy['source'] and yd.get('clock')==oldy['clock'] and yd.get('whole_effect_sha256')==yb.get('whole_effect_sha256'),'F06_Y_DISPATCH_CHANGED')
    need(ye.get('schema')=='frw.Root.F06.original-consumer-ended.v1' and ye.get('exit_code')==2 and ye.get('actor_absent') is True and ye.get('canonical_run') is None and ye.get('acceptance')=='NOT_ESTABLISHED','F06_Y_END_OR_UNKNOWN_EFFECT_NOT_CLOSED')
    observed=review['observed']
    need(all(type(observed.get(key)) is int and observed[key]>0 and not (Path('/proc')/str(observed[key])).exists() for key in ('actor_pid','parent_pid')) and not os.path.lexists(Y_DIR/'work/ROOT-STOP-UNCONFIRMED.json'),'F06_Y_ACTOR_PARENT_OR_STOP_UNKNOWN_NOT_CLOSED')
    need(yc.get('schema')=='frw.Root.F06.unstarted-consumer-finite-clock.v1' and set(yc)=={'schema','started_at','deadline_at','started_monotonic','deadline_monotonic','boot_id'} and all(type(yc[k]) in (int,float) and math.isfinite(yc[k]) for k in ('started_at','deadline_at','started_monotonic','deadline_monotonic')) and 0<yc['deadline_at']-yc['started_at']<=600 and 0<yc['deadline_monotonic']-yc['started_monotonic']<=600,'F06_Y_OLD_CLOCK_CHANGED')
    return {'y':y,'assessment':assessment,'review':review,'old_inputs':oldinputs,'old_y':oldy,'clock':yc,'once':yo}

def _historical_prebirth_freshness(r,once,clock):
    """Historical O/X admission at saved Y claim; no current time comparison."""
    need(type(r.get('created_at')) in (int,float) and type(r.get('expires_at')) in (int,float) and math.isfinite(r['created_at']) and math.isfinite(r['expires_at']) and type(once.get('at')) in (int,float) and math.isfinite(once['at']) and r['created_at']<=once['at']<r['expires_at']<=r['created_at']+120 and clock['started_at']<=once['at']<clock['deadline_at'],'F06_HISTORICAL_O_X_RECONCILIATION_NOT_VALID_AT_Y_ONCE')
    return True

def closed_history(v):
    """Read-only O/X/Y history; no new clock or future reconciliation required.
    O/X never-started statements remain local to their historical boundaries.
    Y really started and closed; its existing client was not a user API request.
    """
    need(v.get('prebirth_closure')==PREBIRTH_CLOSURE and v.get('binding_prebirth_closure')==BINDING_PREBIRTH_CLOSURE and v.get('y_preintent_closure')==Y_PREINTENT_CLOSURE and v.get('y_saved_assessment')==Y_SAVED_ASSESSMENT and v.get('y_independent_review')==Y_INDEPENDENT_REVIEW,'F06_EXACT_CLOSED_HISTORY_REQUIRED')
    closure=json.loads(readref(v['prebirth_closure']),object_pairs_hook=unique)
    need(closure.get('schema')=='friday.root.F06.first-driver-prebirth-refusal-closure.v1' and closure.get('state')=='DRIVER_CLOSED_AFTER_ISSUANCE_BEFORE_BIND_OR_CONSUMER_BIRTH_NO_SEND' and closure.get('actual_issued_authority')==EXISTING_AUTHORITY and closure.get('actual_authority_id')==EXISTING_AUTHORITY_ID and closure.get('consumer_birth') is False and closure.get('dispatch_invocation_absent') is True and closure.get('canonical_run_absent') is True and closure.get('no_API_client_created') is True and closure.get('reissue_retry_resume_or_rename_authorized') is False,'F06_GENUINE_ISSUER_ONLY_PREBIRTH_CLOSURE_REQUIRED')
    oldonce=closure['once_claim_preserved'];oldclock=closure['original_clock']
    once=json.loads(readref(oldonce),object_pairs_hook=unique)
    clock=json.loads(readref(oldclock),object_pairs_hook=unique)
    need(oldonce['path']==str(ORIGINAL_DIR/'work/ROOT-ONCE-INVOCATION.json') and oldclock['path']==str(ORIGINAL_DIR/'EXECUTION-CLOCK.json') and once.get('schema')=='frw.Root.F06.one-driver-invocation.v1' and once.get('run_id')==ORIGINAL_RUN and once.get('no_retry') is True and clock==closure['original_clock_endpoints_preserved'],'F06_OLD_ONCE_OR_CLOCK_ERASED_RENAMED_OR_CHANGED')
    need(not (Path('/proc')/str(closure['actual_root_driver_pid'])).exists(),'F06_OLD_ROOT_DRIVER_STILL_PRESENT')
    for name in ('ROOT-ACTUAL-BINDING.json','bot_tester.f06.root-bound.py','ROOT-DISPATCH-INVOCATION.json','ROOT-CONSUMER-ACTOR.json','ROOT-STOP-UNCONFIRMED.json','ROOT-DISPATCH-ENDED.json','CONSUMER.stdout','CONSUMER.stderr'):
        need(not os.path.lexists(ORIGINAL_DIR/'work'/name),'F06_PRIOR_CONSUMER_BIND_DISPATCH_BIRTH_OR_UNKNOWN')
    need(not os.path.lexists(STATE/'runs'/(ORIGINAL_RUN+'.json')),'F06_PRIOR_CANONICAL_RUN_REFUSE')
    # The second failed caller wrote source/binding, then exact reconstruction
    # refused before dispatch. Preserve those bytes rather than demanding absence.
    x=json.loads(readref(v['binding_prebirth_closure']),object_pairs_hook=unique)
    need(x.get('schema')=='friday.root.F06.firstconsumer-binding-prebirth-refusal-closure.v1' and x.get('state')=='FIRST_CONSUMER_BINDING_CREATED_RECONSTRUCTION_REFUSED_BEFORE_DISPATCH_NO_SEND' and x.get('driver_exit_code')==1 and x.get('actual_root_driver_absent') is True and x.get('consumer_born') is False and x.get('dispatch_created') is False and x.get('canonical_run_created') is False and x.get('failure')=='F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE' and x.get('source_reconstruction_guard_preserved') is True and x.get('no_API_client_or_upload_or_model_based_on_actual_control_flow') is True and x.get('existing_R106_not_reissued') is True and x.get('old_issuer_only_once_clock_preserved') is True and x.get('no_old_driver_or_issuer_retry') is True,'F06_GENUINE_CLOSED_BINDING_ONLY_REFUSAL_REQUIRED')
    need(type(x.get('actual_root_driver_pid')) is int and x['actual_root_driver_pid']>0 and not (Path('/proc')/str(x['actual_root_driver_pid'])).exists(),'F06_BINDING_DRIVER_STILL_PRESENT_OR_UNKNOWN')
    oldx={'once':x['consumer_stage_once_preserved'],'clock':x['original_consumer_clock_preserved'],'source':x['source_file'],'binding':x['actual_binding']}
    leaves={'once':'ROOT-FIRST-CONSUMER-ONCE.json','source':'bot_tester.f06.root-bound.py','binding':'ROOT-ACTUAL-BINDING.json'}
    need(all(oldx[k]['path']==str(BINDING_DIR/'work'/leaf) for k,leaf in leaves.items()) and oldx['clock']['path']==str(BINDING_DIR/'CONSUMER-CLOCK.json'),'F06_BINDING_HISTORY_PATH_RENAMED')
    xo=json.loads(readref(oldx['once']),object_pairs_hook=unique)
    xc=json.loads(readref(oldx['clock']),object_pairs_hook=unique)
    xb=json.loads(readref(oldx['binding']),object_pairs_hook=unique)
    readref(oldx['source'])
    need(xo.get('schema')=='frw.Root.F06.first-consumer-invocation.v1' and xo.get('run_id')==ORIGINAL_RUN and xo.get('existing_authority')==EXISTING_AUTHORITY and xo.get('prebirth_closure')==PREBIRTH_CLOSURE and xo.get('old_driver_resume') is False and xo.get('issuer_invoked') is False and xo.get('no_retry') is True,'F06_BINDING_OLD_ONCE_CHANGED')
    need(xc.get('schema')=='frw.Root.F06.unstarted-consumer-finite-clock.v1' and set(xc)=={'schema','started_at','deadline_at','started_monotonic','deadline_monotonic','boot_id'} and all(type(xc[k]) in (int,float) and math.isfinite(xc[k]) for k in ('started_at','deadline_at','started_monotonic','deadline_monotonic')) and 0<xc['deadline_at']-xc['started_at']<=600 and 0<xc['deadline_monotonic']-xc['started_monotonic']<=600,'F06_BINDING_OLD_CLOCK_CHANGED')
    bc=xb.get('contract',{})
    need(xb.get('schema')=='frw.Root.F06.exact-first-wrongread-binding.v1' and xb.get('source')==oldx['source'] and xb.get('authority')==EXISTING_AUTHORITY and bc.get('authority')==EXISTING_AUTHORITY and bc.get('authority_id')==EXISTING_AUTHORITY_ID and bc.get('run_id')==ORIGINAL_RUN and bc.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and bc.get('scope')==v['contract'].get('scope') and bc.get('resources',{}).get('clock')==oldx['clock'],'F06_BINDING_HISTORY_CONTRACT_OR_SOURCE_CHANGED')
    for name in ('ROOT-DISPATCH-INVOCATION.json','ROOT-CONSUMER-ACTOR.json','ROOT-STOP-UNCONFIRMED.json','ROOT-DISPATCH-ENDED.json','CONSUMER.stdout','CONSUMER.stderr'):
        need(not os.path.lexists(BINDING_DIR/'work'/name),'F06_BINDING_PRIOR_DISPATCH_BIRTH_OR_UNKNOWN')
    r=json.loads(readref(v['prebirth_reconciliation']),object_pairs_hook=unique)
    need(r.get('schema')=='frw.Root.F06.two-closed-prebirth-reconciliation.v1' and r.get('operator')=='Root' and r.get('status')=='ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER' and r.get('prebirth_closure')==v['prebirth_closure'] and r.get('original_run_id')==ORIGINAL_RUN and r.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and r.get('existing_authority')==EXISTING_AUTHORITY and r.get('old_once')==oldonce and r.get('old_clock')==oldclock and r.get('binding_prebirth_closure')==v['binding_prebirth_closure'] and all(r.get('binding_old_'+k)==oldx[k] for k in ('once','clock','source','binding')),'F06_ROOT_RECONCILIATION_EXACT_REFS_REQUIRED')
    for key in ('user_consumer_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_user_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_user_consumer_authorized','no_old_driver_or_issuer_retry','binding_failure_closed_before_dispatch','binding_once_clock_source_preserved','no_unknown_consumer_effect'):
        need(r.get(key) is True,'F06_ROOT_PREBIRTH_RECONCILIATION_REQUIRED')
    prior_y=_closed_y_history(v)
    y=prior_y['y'];assessment=prior_y['assessment'];review=prior_y['review'];oldinputs=prior_y['old_inputs'];oldy=prior_y['old_y'];yc=prior_y['clock'];yo=prior_y['once'];observed=review['observed']
    # The exact pinned old source rechecked this historical reconciliation
    # synchronously before Popen. Born-closed Y corroborates that admission; no
    # CLOCK_BOOTTIME/monotonic conversion or current freshness is invented here.
    _historical_prebirth_freshness(r,yo,yc)
    return {'old':closure,'x':x,'y':y,'old_inputs':oldinputs,'old_y':oldy,'old_clocks':(oldclock,oldx['clock'],oldy['clock']),'assessment':assessment,'review':review,'historical_prebirth_freshness_basis':'SAVED_ONCE_WITHIN_ORIGINAL_CLOCK_AND_RECONCILIATION; BIRTH_ADMISSION_SOURCE_DERIVED_FROM_EXACT_PINNED_CALLER'}

def prebirth_reconciled(v):
    """Authenticate closed history plus explicit Root-bound missing first API.
    Raw Y refusal and the original unretained nested cause remain unchanged.
    """
    current_selection=selection(v['contract'],v['admission_selection'],selected_basis=v['postboot_basis'],effect_binding=True)
    history=closed_history(v)
    r=json.loads(readref(v['y_reconciliation']),object_pairs_hook=unique)
    c=v['contract']
    need(r.get('schema')==CURRENT_Y_SCHEMA and r.get('operator')=='Root' and r.get('status')==CURRENT_STAGE_STATUS and 'user_consumer_never_started' not in r and r.get('raw_status')=='REFUSED_OR_UNKNOWN' and r.get('original_nested_cause_retained') is False,'F06_ROOT_MISSING_FIRST_API_RECONCILIATION_REQUIRED')
    need(all(r.get(key)==v[key] for key in ('prebirth_closure','binding_prebirth_closure','prebirth_reconciliation','y_preintent_closure','y_saved_assessment','y_independent_review','source_freeze','independent_review','workdir')) and r.get('y_history_pins')==Y_HISTORY_PINS and r.get('original_run_id')==ORIGINAL_RUN and r.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and r.get('existing_authority')==EXISTING_AUTHORITY and r.get('authority_id')==c['authority_id'] and r.get('selected_admission')==v['selected_admission']==c['authority'] and r.get('admission_selection')==v['admission_selection'] and r.get('postboot_basis')==v['postboot_basis'] and r.get('scope')==c.get('scope') and r.get('current_contract_sha256')==digest(encoded(c)) and r.get('future_clock')==c.get('resources',{}).get('clock'),'F06_ROOT_MISSING_FIRST_API_EXACT_CURRENT_CONTRACT_AND_REFS_REQUIRED')
    for key in CURRENT_Y_RECONCILIATION_BOOLS:need(r.get(key) is True,'F06_ROOT_ACTUAL_Y_CLOSED_AND_FIRST_API_NEVER_STARTED_REQUIRED')
    need(type(r.get('created_at')) in (int,float) and type(r.get('expires_at')) in (int,float) and math.isfinite(r['created_at']) and math.isfinite(r['expires_at']) and r['created_at']<=time.time()<r['expires_at']<=r['created_at']+120,'F06_ROOT_MISSING_FIRST_API_RECONCILIATION_STALE')
    fresh=c['resources']['clock']
    need(all(fresh!=old and fresh['path']!=old['path'] for old in history['old_clocks']),'F06_OLD_CLOCK_REUSE_OR_EXTENSION_REFUSED')
    future=json.loads(readref(fresh),object_pairs_hook=unique)
    clock_remaining(future)
    need(future['started_at']>=max(dt.datetime.fromisoformat(item['at_moscow']).timestamp() for item in (history['old'],history['x'],history['y'],history['assessment'])),'F06_FRESH_CLOCK_MUST_FOLLOW_CLOSED_Y_AND_ACCEPTED_ASSESSMENT')
    recovery=json.loads(readref(v['postboot_basis']['recovery_acceptance']),object_pairs_hook=unique)
    need(future['boot_id']==current_selection['boot_id'] and future['started_at']>=max(_recovery_time(recovery),current_selection['created_at']),'F06_FRESH_CLOCK_MUST_FOLLOW_ROOT_RECOVERY_AND_CURRENT_SELECTION')
    return history

def clock_remaining(clock):
    now=time.time();mono=time.monotonic()
    need(type(clock) is dict and set(clock)=={'schema','started_at','deadline_at','started_monotonic','deadline_monotonic','boot_id'} and clock['schema']=='frw.Root.F06.unstarted-consumer-finite-clock.v1','F06_EXACT_SEPARATE_UNSTARTED_CONSUMER_CLOCK_REQUIRED')
    need(all(type(clock[k]) in (int,float) and math.isfinite(clock[k]) for k in ('started_at','deadline_at','started_monotonic','deadline_monotonic')) and clock['started_at']<=now<clock['deadline_at']<=clock['started_at']+600 and 0<=clock['started_monotonic']<=mono<clock['deadline_monotonic']<=clock['started_monotonic']+600 and clock['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'F06_CONSUMER_CLOCK_EXPIRED_OR_CHANGED')
    return min(clock['deadline_at']-now,clock['deadline_monotonic']-mono)

class StopUnconfirmed(RuntimeError):
    """Original outer deadline exhausted without confirmed same-child reap."""

def owned_remaining(clock):
    # The caller already validated this exact original clock/boot. Cleanup uses
    # its original absolute endpoints even when expired; it never creates time.
    return max(0.0,min(clock['deadline_at']-time.time(),clock['deadline_monotonic']-time.monotonic()))

def wait_owned(actor,clock,reserve):
    """Execute and reap inside one original deadline, with cleanup carved within it.
    SIGINT, TERM and KILL each target this exact child. A pathological unreaped
    child is explicit STOP_UNCONFIRMED, never an unbounded wait or cleanup claim.
    """
    if actor.poll() is not None:return actor.wait(timeout=0)
    remaining=owned_remaining(clock)
    run_seconds=max(0.0,remaining-min(reserve,remaining))
    if run_seconds>0:
        try:return actor.wait(timeout=run_seconds)
        except subprocess.TimeoutExpired:pass
    for action,parts in ((lambda:actor.send_signal(signal.SIGINT),3),(actor.terminate,2),(actor.kill,1)):
        if actor.poll() is not None:return actor.wait(timeout=0)
        try:action()
        except ProcessLookupError:
            if actor.poll() is not None:return actor.wait(timeout=0)
        remaining=owned_remaining(clock)
        if remaining>0:
            try:return actor.wait(timeout=remaining/parts)
            except subprocess.TimeoutExpired:pass
    if actor.poll() is not None:return actor.wait(timeout=0)
    raise StopUnconfirmed('F06_STOP_UNCONFIRMED_ORIGINAL_OUTER_DEADLINE')

def execute(v,*,binding_ref):
    validate_inputs(v)
    # Authenticate the complete local source set before any executable module load.
    own=Path(__file__).resolve().parent
    freeze_raw=readref(v['source_freeze']);freeze=json.loads(freeze_raw,object_pairs_hook=unique)
    need(freeze.get('schema')=='frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1' and type(freeze.get('files')) is dict and set(freeze['files'])=={'f06_source.py','f06_footer.py.txt','current207.py','root_bind_existing_consumer_once.py'},'F06_COMPLETE_REVIEWED_SOURCE_FREEZE_REQUIRED')
    for leaf,want in freeze['files'].items():need('/' not in leaf and digest(read(own/leaf))==want['sha256'] and len(read(own/leaf))==want['bytes'],'F06_REVIEWED_SOURCE_DRIFT')
    review=json.loads(readref(v['independent_review']),object_pairs_hook=unique)
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('source_freeze_sha256')==digest(freeze_raw) and review.get('open_critical_defects')==[],'F06_EXACT_INDEPENDENT_SOURCE_ACCEPTANCE_REQUIRED')
    need(all(v['contract'].get(field)==ref(own/leaf) for field,leaf in (('adapter','f06_source.py'),('actual_root_B_checker','current207.py'),('footer','f06_footer.py.txt'))),'F06_EXACT_LOCAL_REVIEWED_SOURCE_REFERENCES_REQUIRED')
    need(v['independent_review']==v['contract'].get('root_proofs',{}).get('source_review'),'F06_DRIVER_SOURCE_REVIEW_REFERENCE_MISMATCH')
    a=load(v['contract']['adapter'],'Root_first_F06_adapter')
    c=a.canonical_contract(v['contract']);a.contract_shape(c)
    prebirth_reconciled(v)
    a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)
    footer=readref(c['footer']);checker=load(c['actual_root_B_checker'],'Root_first_F06_current207')
    need(digest(read(a.BASE,private=False))==a.BASE_SHA and digest(read(a.INSTALLED_TESTER,private=False))==a.INSTALLED_TESTER_SHA,'F06_BASE_OR_INSTALLED_TESTER_CHANGED')
    scenario_raw=readref(c['scenario_ref']);s=json.loads(scenario_raw,object_pairs_hook=unique)
    a.scenario_shape(s);need(scenario_raw==a.encoded(s) and digest(scenario_raw)==c['scenario_sha256'],'F06_PRIVATE_SCENARIO_CANONICAL_DRIFT')
    need(c['source']==a.SOURCE and c['crypto']==a.CRYPTO,'F06_RETAINED_G6_STANDARD32_REQUIRED')
    clock=json.loads(readref(c['resources']['clock']),object_pairs_hook=unique)
    need(clock_remaining(clock)>=c['resources']['operation_seconds']+c['resources']['reserve_seconds'],'F06_ORIGINAL_FINITE_CLOCK_INSUFFICIENT')
    work=canonical_path(v['workdir']);need(work.is_dir() and not any(p.is_symlink() for p in (work,*work.parents)) and stat.S_IMODE(work.stat().st_mode)==0o700 and work.stat().st_uid==os.getuid(),'F06_PRIVATE_WORKDIR_REQUIRED')
    need(work!=own and not (STATE/'runs'/(c['run_id']+'.json')).exists(),'F06_NO_EXISTING_OPERATION_REPLAY')
    # Private package must remain outside all product effective roots, qualified by
    # the pinned current checker and Root private_password_handling proof.
    fd=os.open(SLOT,os.O_RDWR|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);want=v['slot_identity']
        need(type(want) is dict and set(want)=={'device','inode','uid','mode','nlink'} and {'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),'nlink':info.st_nlink}==want and info.st_uid==os.getuid() and stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1,'F06_EXISTING_SHARED_SLOT_CUSTODY_CHANGED')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Short lock probes only. Actual full consumer later acquires and holds its
        # original receiver/token locks; do not pre-open/read the credential.
        for lock in (STATE/'consumer.lock',STATE/'tester-token'):
            q=os.open(lock,os.O_RDWR|os.O_NOFOLLOW)
            try:
                z=os.fstat(q);need(stat.S_ISREG(z.st_mode) and z.st_uid==os.getuid() and z.st_nlink==1 and stat.S_IMODE(z.st_mode)==0o600,'F06_CANONICAL_LOCK_CUSTODY_CHANGED');fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:os.close(q)
        # Separately admitted missing FIRST API segment; Y was already born and closed.
        prebirth_reconciled(v)
        new(work/'ROOT-FIRST-USER-API-ONCE.json',encoded({'schema':'frw.Root.F06.first-user-API-after-closed-preintent-invocation.v1','at':time.time(),'binding':binding_ref,'run_id':c['run_id'],'source_freeze':v['source_freeze'],'existing_authority':EXISTING_AUTHORITY,'selected_admission':v['selected_admission'],'admission_selection':v['admission_selection'],'postboot_basis':v['postboot_basis'],'authority_id':c['authority_id'],'prebirth_closure':v['prebirth_closure'],'binding_prebirth_closure':v['binding_prebirth_closure'],'y_preintent_closure':v['y_preintent_closure'],'y_saved_assessment':v['y_saved_assessment'],'y_independent_review':v['y_independent_review'],'y_reconciliation':v['y_reconciliation'],'actual_y_consumer_born_and_closed':True,'first_user_API_never_started':True,'old_driver_resume':False,'issuer_invoked':False,'no_retry':True}))
        # Fresh Root proof belongs to THIS slot holder. The reviewed template's
        # exact observed/semantic basis is reobserved, never silently updated.
        prepared=json.loads(readref(c['root_current_proof']),object_pairs_hook=unique)
        need(prepared.get('status')=='ROOT_PREPARED_ONE_FUTURE_OPERATION' and prepared.get('contract_effect')==a.effect(c) and prepared.get('whole_effect_sha256')==a.digest(a.encoded(a.effect(c))),'F06_REVIEWED_CURRENT_TEMPLATE_REQUIRED')
        actual=checker.observe(prepared)
        need(actual==prepared.get('observed') and actual.get('f06_mutable_boundary')==c['boundary'],'F06_REVIEWED_MUTABLE_BASIS_CHANGED_RECONCILE_ONLY')
        wall,mono=time.time(),time.monotonic()
        proof=dict(prepared,status='ROOT_BOUND',created_at=wall,expires_at=wall+120,created_monotonic=mono,expires_monotonic=mono+120,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),shared_slot_owner=checker.transport().kernel(os.getpid()))
        fresh_path=work/'ROOT-FRESH-CURRENT-PROOF.json';new(fresh_path,encoded(proof))
        c['root_current_proof']=ref(fresh_path)
        qualified=checker.check(c['root_current_proof']['path'],c['root_current_proof']['sha256'])
        need(qualified['whole_effect_sha256']==a.digest(a.encoded(a.effect(c))),'F06_WHOLE_EFFECT_PROOF_CHANGED')
        # Separately Root-selected existing canonical bytes; no issuer or fallback.
        a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)
        bound=work/'bot_tester.f06.root-bound.py';source=a.successor(read(a.BASE,private=False),c,footer);new(bound,source)
        new(work/'ROOT-ACTUAL-BINDING.json',encoded({'schema':'frw.Root.F06.exact-first-wrongread-binding.v1','contract':c,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'authority':c['authority'],'independent_review':v['independent_review']}))
        need(a.successor(read(a.BASE,private=False),json.loads(read(work/'ROOT-ACTUAL-BINDING.json'))['contract'],footer)==read(bound),'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE')
        argv=[PYTHON,'-I','-B','-S',str(bound),'--state-dir',str(STATE),'run','--run-id',c['run_id'],'--scenario',c['scenario_ref']['path']]
        new(work/'ROOT-DISPATCH-INVOCATION.json',encoded({'state':'ONE_MISSING_FIRST_USER_API_AFTER_CLOSED_Y_NO_OLD_CONSUMER_RETRY','argv':argv,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'clock':c['resources']['clock']}))
        need(clock_remaining(clock)>=c['resources']['operation_seconds']+c['resources']['reserve_seconds'],'F06_CLOCK_INSUFFICIENT_BEFORE_BIRTH')
        r=c['resources'];cpus=sorted(os.sched_getaffinity(0))[:2];need(cpus,'F06_NO_AVAILABLE_CPU')
        def child_limits():
            resource.setrlimit(resource.RLIMIT_CPU,(r['cpu_seconds'],r['cpu_seconds']))
            resource.setrlimit(resource.RLIMIT_AS,(r['max_rss_bytes'],r['max_rss_bytes']))
            resource.setrlimit(resource.RLIMIT_FSIZE,(r['disk_bytes'],r['disk_bytes']))
            os.sched_setaffinity(0,cpus)
        actor=None;stops=[];forwarded_stops=0;wait_attempted=False;forwarding_stops=False
        prior={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
        def forward_stops():
            nonlocal forwarded_stops,forwarding_stops
            # A nested signal records its event; the active drain owns forwarding.
            if forwarding_stops:return
            forwarding_stops=True
            try:
                while actor is not None and forwarded_stops<len(stops):
                    event=stops[forwarded_stops];forwarded_stops+=1
                    if actor.poll() is None:
                        try:actor.send_signal(event['signal'])
                        except ProcessLookupError:actor.poll()
            finally:
                forwarding_stops=False
                # Close a signal arriving after the last empty check but before
                # the drain flag cleared. A handler after clearance drains itself.
                if actor is not None and forwarded_stops<len(stops):forward_stops()
        def parent_stop(n,_frame):
            stops.append({'signal':n,'at':time.time()})
            forward_stops()
        with os.fdopen(os.open(work/'CONSUMER.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as out, os.fdopen(os.open(work/'CONSUMER.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as err:
            try:
                for n in prior:signal.signal(n,parent_stop)
                need(not stops,'F06_STOP_BEFORE_CONSUMER_BIRTH')
                prebirth_reconciled(v)
                a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)
                need(clock_remaining(clock)>=r['operation_seconds']+r['reserve_seconds'],'F06_CONSUMER_CLOCK_INSUFFICIENT_AT_BIRTH')
                started=time.monotonic()
                actor=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(fd,),preexec_fn=child_limits)
                try:
                    # Close the precheck/Popen-return/assignment signal handoff.
                    # A handler after assignment and this replay share one index.
                    forward_stops()
                    actor_identity=checker.transport().kernel(actor.pid)
                    new(work/'ROOT-CONSUMER-ACTOR.json',encoded({'identity':actor_identity,'clock':c['resources']['clock'],'cpu_seconds':r['cpu_seconds'],'max_rss_bytes':r['max_rss_bytes'],'per_file_cap_bytes':r['disk_bytes'],'affinity_cpus':cpus}))
                finally:
                    wait_attempted=True
                    code=wait_owned(actor,clock,r['reserve_seconds'])
            except StopUnconfirmed:
                # Child inherited the SAME slot description. If still alive it
                # retains custody; do not claim closure or open a replacement.
                new(work/'ROOT-STOP-UNCONFIRMED.json',encoded({'state':'STOP_UNCONFIRMED','actor_pid':actor.pid,'clock':c['resources']['clock'],'parent_stops':stops,'retry_or_replacement_authorized':False}))
                raise
            finally:
                try:
                    if actor is not None and actor.poll() is None and not wait_attempted:
                        wait_attempted=True
                        code=wait_owned(actor,clock,r['reserve_seconds'])
                finally:
                    for n,h in prior.items():signal.signal(n,h)
        ended={'schema':'frw.Root.F06.original-consumer-ended.v1','at_moscow':dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),'exit_code':code,'elapsed_seconds':time.monotonic()-started,'actor_absent':not (Path('/proc')/str(actor.pid)).exists(),'parent_stops':stops,'canonical_run':ref(STATE/'runs'/(c['run_id']+'.json')) if (STATE/'runs'/(c['run_id']+'.json')).exists() else None,'acceptance':'NOT_ESTABLISHED','next':'reconcile/grade saved original only; no retry or followup authorized'}
        new(work/'ROOT-DISPATCH-ENDED.json',encoded(ended));return ended
    finally:os.close(fd)

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    need(len(args)==3 and args[0]=='--execute-once','F06_EXACT_ROOT_COMMAND_REQUIRED')
    path=canonical_path(args[1]);raw=read(path);need(digest(raw)==args[2],'F06_ROOT_BINDING_INPUT_CHANGED')
    v=json.loads(raw,object_pairs_hook=unique);validate_inputs(v)
    result=execute(v,binding_ref={'path':str(path),'bytes':len(raw),'sha256':digest(raw)})
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))
if __name__=='__main__':main()
