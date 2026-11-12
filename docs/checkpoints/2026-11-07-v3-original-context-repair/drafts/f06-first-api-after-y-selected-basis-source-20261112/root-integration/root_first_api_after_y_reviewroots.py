"""Root-only dormant POSTBOOT CURRENT FIRST USER API frame after exact O/X/Y closed local effects.
No default action, grants, clocks, scenario or actual authority supplied here.
Y consumer WAS born and closed, its raw REFUSED_OR_UNKNOWN is immutable.
Separate future Root decision admits only missing first upload/API, never old caller.
"""
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import types

B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
T=Path('/home/jericho/.cache/FRW-SOL-V3-F06-FIRST-USER-API-AFTER-CLOSED-PREINTENT-CORE-20261112/final/revision-selected-basis')
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
X=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-CONSUMER-EXISTING-R106-20261112')
OLD_Y=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112')
Y=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-API-AFTER-Y-ROOT-20261112')
C=Y/'source'
J=B/'SOL-TASK31-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json'
PYTHON='/home/jericho/jericho/.venv/bin/python'
FIRST_FREEZE_SHA='cac08142c2406e36a451c0bfed4f23b934fe4492dfb765ba67012d7917cf8204'
FRAME_SUPPORT_SHA='8817dca2e5e8116f0b200effb61c46171fb9bd0f3dae21eaf78e485ffbdff4a6'
BOUNDED_READER_ACCEPTANCE={'path':'/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-BOUNDED-READER-R2-ROOT-SOURCE-ACCEPTANCE-20261112.json','bytes':4440,'sha256':'eef9303fd0bd1a4b981b94f0a08a02704ea8fc6e14630b509a118fd8be7cfc10'}
POSTBOOT_HELPER_SHA='c8294eba94f0791053d23260a2b199193184d2b49ce5d9ee0dcf9c3bdc3e6ed1'
BASIS_FIELDS={'recovery_acceptance','persistent_runtime_delta','postboot_observation'}
LEAVES={'f06_source.py','f06_footer.py.txt','current207.py','root_bind_existing_consumer_once.py'}
Y_PROOF={'path':str(OLD_Y/'work/ROOT-FRESH-CURRENT-PROOF.json'),'bytes':2496998,'sha256':'0c4da2fe80a594a0814f1c1c10bed2407f0816642083f0de7aca5dd5d462c7df'}
Y_DELTA={'path':str(OLD_Y/'POST-REFUSAL-CUSTODY-DELTA.json'),'bytes':951,'sha256':'9c15baad29be8c9dc183a3d6560f14e036d646d847e8cd4f0dcf4c1c1081114b'}
BOOLS=('actual_y_consumer_born_and_closed','no_user_BotAPI_request_before_synchronous_current_gate_refusal','old_O_X_Y_once_clocks_source_binding_preserved','no_old_caller_issuer_or_consumer_retry','same_original_run_scenario_source_scope_only','missing_first_user_API_only_authorized','raw_REFUSED_OR_UNKNOWN_preserved','nested_cause_not_originally_retained','no_unknown_API_effect_assumed_absent')

def need(ok,why):
    if not ok:raise ValueError(why)
def raw(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def unique(pairs):
    out={}
    for k,v in pairs:need(k not in out,'ROOT_DUPLICATE_JSON_KEY');out[k]=v
    return out
def path(v):
    s=str(v) if isinstance(v,Path) else v
    need(type(s) is str and s.startswith('/') and not s.startswith('//') and str(Path(s))==s and all(x not in ('','.','..') for x in s.split('/')[1:]) and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in s),'ROOT_CANONICAL_PATH_REQUIRED')
    s.encode('utf-8');return Path(s)
def identity(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def read(p):
    p=path(p);need(not any(q.is_symlink() for q in (p,*p.parents)),'ROOT_NO_LINKS')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        b=os.fstat(f.fileno());data=f.read(24*1024**2+1);a=os.fstat(f.fileno())
    need(stat.S_ISREG(b.st_mode) and b.st_uid==os.getuid() and b.st_nlink==1 and stat.S_IMODE(b.st_mode)==0o600 and len(data)<=24*1024**2 and identity(b)==identity(a)==identity(p.stat()),'ROOT_UNSAFE_OR_CHANGED_PRIVATE_INPUT')
    return data
def ref(p):
    p=path(p);b=read(p);return dict(path=str(p),bytes=len(b),sha256=sha(b))
def readref(r):
    need(type(r) is dict and set(r)=={'path','bytes','sha256'} and type(r['bytes']) is int and r['bytes']>0 and type(r['sha256']) is str and len(r['sha256'])==64,'ROOT_EXACT_REFERENCE_REQUIRED')
    b=read(r['path']);need(len(b)==r['bytes'] and sha(b)==r['sha256'],'ROOT_REFERENCE_CAS_CHANGED');return b
def get(p):return json.loads(read(p),object_pairs_hook=unique)
def pinned(r):return json.loads(readref(r),object_pairs_hook=unique)
def put(p,v):
    p=path(p)
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw(v));f.flush();os.fsync(f.fileno())
    return ref(p)
def directory(p):
    p=path(p);s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700 and not any(q.is_symlink() for q in (p,*p.parents)),'ROOT_PRIVATE_DIRECTORY_REQUIRED')
def load(r,name):
    b=readref(r);m=types.ModuleType(name);m.__file__=r['path'];exec(compile(b,r['path'],'exec'),m.__dict__);return m

def plan_input(p,digest):
    v=pinned(dict(path=str(path(p)),bytes=len(read(p)),sha256=digest))
    fields={'schema','operator','status','root_directory','source_directory','root_source_acceptance','frame_acceptance','original_prepared_contract','y_fresh_proof','constructor_acceptance','y_judgment','selected_admission','admission_selection','postboot_basis'}
    need(type(v) is dict and set(v)==fields,'ROOT_EXACT_PREPARATION_PLAN_REQUIRED')
    need(v['schema']=='frw.Root.F06.Task31.first-API-plan.v1' and v['operator']=='Root' and v['status']=='ROOT_EXPLICIT_PREPARATION_NO_CLOCK_NO_GRANT' and v['root_directory']==str(Y) and v['source_directory']==str(C) and type(v['postboot_basis']) is dict and set(v['postboot_basis'])==BASIS_FIELDS,'ROOT_PLAN_UNBOUND')
    need(v['root_source_acceptance']['path']==str(J) and v['original_prepared_contract']['path']==str(OLD_Y/'CONTRACT.PREPARED-NO-CLOCK.json') and v['y_fresh_proof']==Y_PROOF and v['constructor_acceptance']['path']==str(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json'),'ROOT_ORIGINAL_Y_BASIS_PATH_CHANGED')
    directory(Y);directory(C)
    need(all(not Y.is_relative_to(old) and not old.is_relative_to(Y) for old in (O,X,OLD_Y)),'ROOT_NEW_DIRECTORY_MUST_PRESERVE_O_X_Y_BOUNDARIES')
    return v

def packages(p):
    # Exact source+Root component and frame acceptance authenticate BEFORE import.
    fr=ref(C/'SOURCE-FREEZE.json');need(fr['sha256']==FIRST_FREEZE_SHA,'ROOT_FINAL_FIRST_BRANCH_FREEZE_CHANGED')
    freeze=pinned(fr);need(freeze.get('schema')=='frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1' and set(freeze['files'])==LEAVES,'ROOT_EXACT_FOUR_FILE_FIRST_BRANCH_REQUIRED')
    code_refs={}
    for leaf,want in freeze['files'].items():
        r=dict(path=str(C/leaf),bytes=want['bytes'],sha256=want['sha256']);need(path(C/leaf).parent==C and ref(C/leaf)==r,'ROOT_CODE_DRIFT');code_refs[leaf]=r
    support=ref(Y/'y_custody_delta.py');need(support['sha256']==FRAME_SUPPORT_SHA,'ROOT_CUSTODY_DELTA_SOURCE_CHANGED')
    postboot=ref(Y/'postboot_transition.py');need(postboot['sha256']==POSTBOOT_HELPER_SHA,'ROOT_POSTBOOT_DELTA_SOURCE_CHANGED')
    root=pinned(p['root_source_acceptance']);review_ref=root.get('first_source_review');review=pinned(review_ref)
    need(root.get('schema')=='frw.Root.F06.Task31.component-source-acceptance.v1' and root.get('operator')=='Root' and root.get('decision')=='ROOT_ACCEPTED_SOURCE_ONLY_MISSING_FIRST_API_UNBOUND' and root.get('source_freeze')==fr and root.get('source_files')==code_refs and root.get('custody_delta_source')==support and root.get('postboot_transition_source')==postboot and root.get('postboot_basis')==p['postboot_basis'] and root.get('open_critical_defects')==[] and root.get('runtime_authority') is False,'ROOT_ACTUAL_COMPONENT_SOURCE_ACCEPTANCE_REQUIRED')
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('source_freeze_sha256')==fr['sha256'] and review.get('open_critical_defects')==[],'ROOT_EXACT_FINAL_FOUR_FILE_BRANCH_REVIEW_REQUIRED')
    # The separately accepted bounded-reader component must be the exact parent
    # recorded by Root, not an old T29 approval transposed to changed source.
    need(root.get('bounded_reader_root_acceptance')==BOUNDED_READER_ACCEPTANCE,'ROOT_EXACT_BOUNDED_READER_ACCEPTANCE_PIN_REQUIRED')
    reader=pinned(BOUNDED_READER_ACCEPTANCE)
    need(reader.get('schema')=='friday.root.F06.bounded-reader-R2-source-acceptance.v1' and reader.get('operator')=='Root' and reader.get('state')=='ROOT_ACCEPTED_F06_BOUNDED_READER_COMPONENTS_SOURCE_RUNTIME_INTEGRATION_UNBOUND' and reader.get('branch_freezes',{}).get('first',{}).get('sha256')=='4925dcfb564c7cad0c29223bd5e58b29cd7a47dbec1b7d8aef5a38ae4a7941f6' and reader.get('open_material_source_defects')==[] and reader.get('new_admission_or_clock_or_goal') is False and reader.get('ordinary_semantic_or_F06_acceptance') is False,'ROOT_BOUNDED_READER_ROOT_ACCEPTANCE_REQUIRED')
    frame=pinned(p['frame_acceptance'])
    need(frame.get('schema')=='frw.Root.F06.Task31.frame-source-acceptance.v1' and frame.get('operator')=='Root' and frame.get('decision')=='ROOT_ACCEPTED_FRAME_SOURCE_ONLY_UNBOUND' and frame.get('root_finalizer')==ref(Path(__file__)) and frame.get('custody_delta_source')==support and frame.get('postboot_transition_source')==postboot and frame.get('source_freeze')==fr and frame.get('postboot_basis')==p['postboot_basis'] and frame.get('component_acceptance')==p['root_source_acceptance'] and frame.get('runtime_authority') is False and frame.get('open_critical_defects')==[],'ROOT_FRAME_SOURCE_ACCEPTANCE_REQUIRED_BEFORE_IMPORT')
    # Full branch and helper CAS is complete before any executable import.
    modules=[load(code_refs[n],name) for n,name in [('f06_source.py','Root31_adapter'),('current207.py','Root31_current207'),('root_bind_existing_consumer_once.py','Root31_caller')]]
    return (*modules,review_ref,fr,code_refs)

def delta_module():
    r=ref(Y/'y_custody_delta.py');need(r['sha256']==FRAME_SUPPORT_SHA,'ROOT_CUSTODY_DELTA_SOURCE_CHANGED');return load(r,'Root31_Y_custody_delta')

def postboot_module():
    r=ref(Y/'postboot_transition.py');need(r['sha256']==POSTBOOT_HELPER_SHA,'ROOT_POSTBOOT_DELTA_SOURCE_CHANGED');return load(r,'Root31_postboot_transition')

def baseline(c,a,check):
    proof=check.unbound_proof();closure=pinned(ref(check.CLOSURE))
    proof.update(contract_effect=a.effect(c),whole_effect_sha256=sha(raw(a.effect(c))),installation_closure=ref(check.CLOSURE),installation_acceptance=closure['source_acceptance'],runtime_privacy_review=c['root_proofs']['private_password_handling'],history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'])
    return proof,check.observe(proof)

def constructor(p,actual,check):
    accepted=pinned(p['constructor_acceptance']);need(accepted['decision']=='ROOT_ACCEPT_SCOPED_SOURCE_CONFIG_INFERENCE' and accepted['effective_product_roots']==[str(check.H)] and accepted['profile_configs']==actual['profile_configs'] and accepted['external_manager_source_inference']=='CORE_NO_EXPLICIT_HANDOFF_NO_MANAGER_CONSTRUCTED','ROOT_CORE_MANAGER_SOURCE_CONFIG_BASIS_CHANGED')
    check.reference(accepted['result']);basis=pinned(accepted['basis'])
    for row in basis['source_files'].values():check.reference(row['ref'],private=False)
    for row in accepted['proxy_scope_metadata']:check.reference(row['file'],private=True)
    return accepted

def historical_inputs(caller,c):
    # Y source binding is historical data: its contract/scenario is never run.
    old_once=pinned(caller.Y_HISTORY_PINS['work/ROOT-FIRST-CONSUMER-ONCE.json'])
    old_inputs=pinned(old_once['binding'])
    v=dict(old_inputs,contract=c,y_preintent_closure=caller.Y_PREINTENT_CLOSURE,y_saved_assessment=caller.Y_SAVED_ASSESSMENT,y_independent_review=caller.Y_INDEPENDENT_REVIEW)
    return v

def judgments(p,caller,c):
    v=historical_inputs(caller,c);j=pinned(p['y_judgment'])
    need(j.get('schema')=='frw.Root.F06.Y-postboot-current-first-API-judgment.v1' and j.get('operator')=='Root' and j.get('status')=='ROOT_ACTUAL_RECONCILED_POSTBOOT_CURRENT_MISSING_FIRST_API_ONLY' and j.get('prebirth_closure')==caller.PREBIRTH_CLOSURE and j.get('binding_prebirth_closure')==caller.BINDING_PREBIRTH_CLOSURE and j.get('y_preintent_closure')==caller.Y_PREINTENT_CLOSURE and j.get('y_saved_assessment')==caller.Y_SAVED_ASSESSMENT and j.get('y_independent_review')==caller.Y_INDEPENDENT_REVIEW and j.get('existing_authority')==caller.EXISTING_AUTHORITY and j.get('original_run_id')==caller.ORIGINAL_RUN and j.get('scenario_sha256')==caller.ORIGINAL_SCENARIO_SHA and j.get('y_fresh_proof')==Y_PROOF and j.get('custody_delta')==Y_DELTA and j.get('selected_admission')==c['authority'] and j.get('admission_selection')==p['admission_selection'] and j.get('postboot_basis')==p['postboot_basis'] and all(j.get(k) is True for k in BOOLS),'ROOT_ACTUAL_CLOSED_Y_API_JUDGMENT_REQUIRED')
    h=caller.closed_history(v);return h['old'],h['x'],h['y']

def derive_reviews(c,check,old_actual,actual,decision,caller,selection_ref,selected_basis):
    """Narrow explicit current-proof successors; all old originals stay immutable.

    Only custody-bound history/ingress fields and private preparation directories
    change. No old PASS criterion, installed/native/config/producer fact is changed.
    """
    refs=[caller.Y_PREINTENT_CLOSURE,caller.Y_SAVED_ASSESSMENT,caller.Y_INDEPENDENT_REVIEW,Y_DELTA,Y_PROOF,*[selected_basis[k] for k in sorted(BASIS_FIELDS)],selection_ref,decision]
    old_history=pinned(c['root_proofs']['all_profile_history_semantic_once']);history=json.loads(raw(old_history))
    before=old_actual['f06_mutable_boundary'];after=actual['f06_mutable_boundary']
    need(history['once_sha256']==before['once_sha256'] and history['ingress_lineage_sha256']==before['ingress_lineage_sha256'] and history['history_manifest_sha256']==old_actual['history']['manifest_sha256'] and history['native_boundary_sha256']==before['native_boundary_sha256'],'ROOT_OLD_HISTORY_BASIS_NOT_EXACT_Y')
    history.update(once_sha256=after['once_sha256'],ingress_lineage_sha256=after['ingress_lineage_sha256'])
    history['retained_basis']=history['retained_basis']+refs
    c['root_proofs']['all_profile_history_semantic_once']=put(Y/'ROOT-Y-DERIVED-HISTORY.json',history)
    old_lineage=pinned(c['root_proofs']['source_ingress_lineage']);lineage=json.loads(raw(old_lineage))
    need(lineage['current_ingress_lineage_sha256']==before['ingress_lineage_sha256'],'ROOT_OLD_INGRESS_BASIS_NOT_EXACT_Y')
    lineage['current_ingress_lineage_sha256']=after['ingress_lineage_sha256'];lineage['retained_producer_oracle_basis']=lineage['retained_producer_oracle_basis']+refs
    selection_doc=pinned(selection_ref)
    lineage.update(current_admission_selection=selection_ref,current_selected_admission=c['authority'],postboot_recovery_acceptance=selected_basis['recovery_acceptance'],postboot_basis=selected_basis,readiness_evidence=selection_doc['readiness_evidence'])
    c['root_proofs']['source_ingress_lineage']=put(Y/'ROOT-Y-DERIVED-INGRESS.json',lineage)
    privacy=pinned(c['root_proofs']['private_password_handling'])
    roots={str(Y),str(T),str(Path(__file__).parent),str(B),str(OLD_Y),str(Path(c['authority']['path']).parent),str(Path(selection_ref['path']).parent),*[str(Path(r['path']).parent) for r in selected_basis.values()],str(Path(selection_doc['readiness_evidence']['path']).parent),str(Path(c['root_proofs']['source_review']['path']).parent)}
    privacy['private_roots']=sorted(set(privacy['private_roots'])|roots)
    privacy['scope']+=' Separate Root-admitted missing FIRST USER API after actual Y born/closed current-gate refusal; exact diagnostic-only STATE delta retained. No original nested trace or old PASS reclassification.'
    c['root_proofs']['private_password_handling']=put(Y/'ROOT-Y-DERIVED-PRIVACY.json',privacy)
    check.disjoint(privacy['private_roots'],privacy['effective_product_roots'])
    return dict(old_history=old_history,new_history=history,old_lineage=old_lineage,new_lineage=lineage,only_changed_history_fields=['once_sha256','ingress_lineage_sha256','retained_basis'],only_changed_lineage_fields=['current_ingress_lineage_sha256','retained_producer_oracle_basis','current_admission_selection','current_selected_admission','postboot_recovery_acceptance','postboot_basis','readiness_evidence'],private_directory_additions=sorted(roots))

def prepare(p):
    a,check,caller,review,freeze,code_refs=packages(p)
    need(not (Y/'ROOT-BULK-DECISION.json').exists() and not (Y/'CONSUMER-CLOCK.json').exists() and not (Y/'work').exists(),'ROOT_PREPARATION_ALREADY_STARTED_NO_RETRY')
    c=a.canonical_contract(pinned(p['original_prepared_contract']))
    c.update(authority=p['selected_admission'],adapter=code_refs['f06_source.py'],footer=code_refs['f06_footer.py.txt'],actual_root_B_checker=code_refs['current207.py'],status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD')
    released=pinned(c['authority']);c['authority_id']=released.get('authority_id')
    c['authority_chain']=dict(predecessor=caller.EXISTING_AUTHORITY,predecessor_authority_id=caller.EXISTING_AUTHORITY_ID,created_at=released.get('created_at'),expires_at=released.get('expires_at'))
    caller.selection(c,p['admission_selection'],selected_basis=p['postboot_basis'],effect_binding=False)
    need(c['run_id']==caller.ORIGINAL_RUN and c['scenario_sha256']==caller.ORIGINAL_SCENARIO_SHA and ref(c['scenario_ref']['path'])==c['scenario_ref'],'ROOT_ORIGINAL_RUN_SCENARIO_CHANGED')
    old,x,y=judgments(p,caller,c)
    c['root_proofs']['source_review']=review
    c['root_current_proof']=put(Y/'CURRENT.NOT_GRANTED.json',dict(status='UNBOUND_NO_CURRENT_ADMISSION'))
    c['resources']['clock']=put(Y/'CLOCK.NOT_STARTED.json',dict(status='UNBOUND_CONSUMER_CLOCK_NOT_STARTED'))
    placeholder=put(Y/'BUDGET.NOT_GRANTED.json',dict(status='UNBOUND_CONSUMER_RESOURCES_NO_ACTOR'))
    c['resources']['owned_parent_wait_cleanup']=placeholder
    c['root_proofs']['owned_actor_stop_resources']=placeholder;c['root_proofs']['authoritative_budget_policy']=placeholder
    a.admission(c,released,read=caller.read)
    old_proof=pinned(p['y_fresh_proof']);old_actual=old_proof['observed']
    proof,actual=baseline(c,a,check)
    dm=delta_module()
    pb=postboot_module()
    delta=pb.validate_postboot_y_transition(old_actual,actual,original_observed_sha256=sha(raw(old_actual)),selected_basis=p['postboot_basis'],postboot_anchor=pinned(p['postboot_basis']['postboot_observation']),recovery=pinned(p['postboot_basis']['recovery_acceptance']),delta=pinned(p['postboot_basis']['persistent_runtime_delta']),strict_module=dm)
    dref=put(Y/'ROOT-Y-EXACT-DELTA-DECISION.json',dict(schema='frw.Root.F06.Y-derived-custody-decision.v1',operator='Root',y_judgment=p['y_judgment'],y_fresh_proof=p['y_fresh_proof'],saved_delta=Y_DELTA,selected_postboot_basis=p['postboot_basis'],derivation=delta,old_observation_sha256=sha(raw(old_actual)),new_observation_sha256=sha(raw(actual))))
    changes=derive_reviews(c,check,old_actual,actual,dref,caller,p['admission_selection'],p['postboot_basis'])
    c['boundary']=actual['f06_mutable_boundary']
    caller.selection(c,p['admission_selection'],selected_basis=p['postboot_basis'],effect_binding=True)
    put(Y/'ROOT-Y-PROOF-DERIVATION.json',changes)
    constructor(p,actual,check)
    c['boundary']=actual['f06_mutable_boundary'];proof,now=baseline(c,a,check);need(now==actual,'ROOT_CURRENT_CHANGED_DURING_BULK')
    check.semantic(proof,c,actual);check.private_material(proof,c,actual,Y/'PREPARED-CURRENT-PROOF.json')
    (Y/'work').mkdir(mode=0o700)
    put(Y/'OBSERVED-BULK-FACTS.json',actual);put(Y/'CONTRACT.PREPARED-NO-CLOCK.json',a.canonical_contract(c))
    decision=dict(schema='frw.Root.F06.Task31.first-API-bulk-decision.v1',decision='ROOT_PREPARED_MISSING_FIRST_API_AFTER_CLOSED_Y_NO_CLOCK_NO_GRANT',plan=p,root_finalizer=ref(Path(__file__)),source_freeze=freeze,source_review=review,root_source_acceptance=p['root_source_acceptance'],contract=ref(Y/'CONTRACT.PREPARED-NO-CLOCK.json'),observation=ref(Y/'OBSERVED-BULK-FACTS.json'),prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,y_preintent_closure=caller.Y_PREINTENT_CLOSURE,y_saved_assessment=caller.Y_SAVED_ASSESSMENT,y_independent_review=caller.Y_INDEPENDENT_REVIEW,y_delta_decision=dref,existing_authority=c['authority'],old_callers_once_clocks_binding_source_preserved=True,issuer_repeated=False)
    return put(Y/'ROOT-BULK-DECISION.json',decision)

def technical_carriers(check,actual):
    profile=check.H/'profiles/telegram-bot-8812646969'
    dirs=[check.H/n for n in ('logs','sessions','memories','user-artifacts')]+[profile/n for n in ('logs','sessions','memories','workspace','cache','.curator_backups')]
    files=[];visited=0
    for root in dirs:
        if root.exists():
            todo=[root]
            while todo:
                directory=todo.pop();s=directory.lstat()
                need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and not directory.is_symlink(),'ROOT_UNSAFE_CARRIER_DIRECTORY')
                with os.scandir(directory) as entries:
                    for entry in entries:
                        visited+=1;need(visited<=12000,'ROOT_CARRIER_INVENTORY_TOO_LARGE')
                        f=Path(entry.path);s=entry.stat(follow_symlinks=False)
                        need(s.st_uid==os.getuid() and not stat.S_ISLNK(s.st_mode),'ROOT_UNSAFE_CARRIER_ENTRY')
                        if stat.S_ISDIR(s.st_mode):todo.append(f)
                        else:
                            need(stat.S_ISREG(s.st_mode),'ROOT_NONREGULAR_CARRIER_ENTRY')
                            files.append(dict(path=str(f),device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
    files.sort(key=lambda row:row['path'])
    put(Y/'PRE-EFFECT-TECHNICAL-CARRIER-METADATA.json',dict(roots=list(map(str,dirs)),files=files,db_metadata=actual['databases'],at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),content_read=False))
    cursor=subprocess.run(['journalctl','--user','-u','hermes-gateway-1b7e7667.service','-n','0','--show-cursor','--no-pager'],check=True,capture_output=True,timeout=10).stdout.decode()
    put(Y/'PRE-EFFECT-JOURNAL-CURSOR.json',dict(cursor=cursor,content_read=False))

def execute_once(p,final_review):
    # Exact Root helper/bulk review precedes the first executable module import.
    r=pinned(final_review);bulkref=ref(Y/'ROOT-BULK-DECISION.json')
    need(r.get('schema')=='frw.Root.F06.Task31.finalizer-and-actual-bulk-review.v1' and r.get('decision')=='ACCEPT_ROOT_FINALIZER_NO_LIVE_GRANT' and r.get('root_finalizer')==ref(Path(__file__)) and r.get('root_bulk_decision')==bulkref and r.get('root_source_acceptance')==p['root_source_acceptance'] and r.get('open_critical_defects')==[],'ROOT_FINALIZER_AND_BULK_INDEPENDENT_REVIEW_REQUIRED')
    a,check,caller,review,freeze,code_refs=packages(p)
    bulk=pinned(bulkref)
    need(bulk['plan']==p and bulk['root_finalizer']==ref(Path(__file__)) and bulk['contract']==ref(Y/'CONTRACT.PREPARED-NO-CLOCK.json') and bulk['observation']==ref(Y/'OBSERVED-BULK-FACTS.json') and bulk['source_review']==review and bulk['source_freeze']==freeze and bulk['root_source_acceptance']==p['root_source_acceptance'],'ROOT_BULK_CAS_CHANGED')
    need(not (Y/'CONSUMER-CLOCK.json').exists() and not any((Y/'work').iterdir()),'ROOT_STAGE_ALREADY_STARTED_OR_UNKNOWN_NO_RETRY')
    c=a.canonical_contract(pinned(bulk['contract']));old,x,y=judgments(p,caller,c)
    constructor(p,pinned(bulk['observation']),check)
    prepared,actual=baseline(c,a,check);need(actual==pinned(bulk['observation']),'ROOT_MUTABLE_BASIS_CHANGED_BEFORE_CLOCK')
    check.semantic(prepared,c,actual);check.private_material(prepared,c,actual,Y/'PREPARED-CURRENT-PROOF.json')
    caller.selection(c,p['admission_selection'],selected_basis=p['postboot_basis'],effect_binding=True)
    a.admission(c,pinned(c['authority']),read=caller.read)
    technical_carriers(check,actual)
    # Root explicitly invoked the finite future stage; no prep/review wait inside.
    wall,mono=time.time(),time.monotonic()
    assessment=pinned(caller.Y_SAVED_ASSESSMENT)
    need(wall>=max(dt.datetime.fromisoformat(i['at_moscow']).timestamp() for i in (old,x,y,assessment,pinned(p['postboot_basis']['recovery_acceptance']))),'ROOT_NEW_CLOCK_PRECEDES_CLOSED_Y_AND_ASSESSMENT')
    clock=dict(schema='frw.Root.F06.unstarted-consumer-finite-clock.v1',started_at=wall,deadline_at=wall+600,started_monotonic=mono,deadline_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    cref=put(Y/'CONSUMER-CLOCK.json',clock);c['resources']['clock']=cref
    wait=put(Y/'OWNED-CONSUMER-WAIT.json',dict(operator='Root',status='ROOT_BOUND_FINITE_SAME_CHILD',clock=cref,caller=code_refs['root_bind_existing_consumer_once.py'],same_child_nonreentrant_signal_drain=True,pending_birth_signal_handoff=True,reap_inside_original_deadline=True,no_appended_cleanup_time=True,stop_unconfirmed_retains_child_slot=True,permanent_gateway_dashboard_untouched=True,old_callers_closed=True,one_missing_first_user_API_only=True,actual_Y_consumer_born_and_closed=True))
    c['resources']['owned_parent_wait_cleanup']=wait;c['root_proofs']['owned_actor_stop_resources']=wait
    c['root_proofs']['authoritative_budget_policy']=put(Y/'CONSUMER-BUDGET-POLICY.json',dict(operator='Root',status='ROOT_ADMITTED_MISSING_FIRST_API_AFTER_CLOSED_Y',criterion=c['root_proofs']['original_criterion'],source_review=review,timing=a.TIMING,clock=cref,cpu_seconds=c['resources']['cpu_seconds'],address_space_bytes=c['resources']['max_rss_bytes'],store_growth_and_temporary_copy_cap=c['resources']['disk_bytes'],existing_authority=c['authority'],prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,old_clock=old['original_clock'],binding_old_clock=x['original_consumer_clock_preserved'],y_old_clock=caller.Y_HISTORY_PINS['CONSUMER-CLOCK.json'],y_preintent_closure=caller.Y_PREINTENT_CLOSURE,old_clocks_reset=False,old_once_reused=False,issuer_repeated=False,one_initial_upload_only=True,followup_or_retry_authorized=False,original_run_and_scenario_unchanged=True,scope=c['scope']))
    c=a.canonical_contract(c);prepared,now=baseline(c,a,check);need(now==actual,'ROOT_MUTABLE_FACTS_CHANGED_DURING_FINAL_BINDING')
    prepared.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION',observed=now)
    check.semantic(prepared,c,now);check.private_material(prepared,c,now,Y/'PREPARED-CURRENT-PROOF.json')
    c['root_current_proof']=put(Y/'PREPARED-CURRENT-PROOF.json',prepared)
    old,x,y=judgments(p,caller,c);t=time.time()
    hv=historical_inputs(caller,c)
    reconciliation=dict(schema='frw.Root.F06.closed-Y-postboot-current-missing-first-user-API-reconciliation.v1',operator='Root',status='ROOT_BOUND_SEPARATE_POSTBOOT_CURRENT_MISSING_FIRST_USER_API_AFTER_CLOSED_Y',created_at=t,expires_at=t+120,prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,y_preintent_closure=caller.Y_PREINTENT_CLOSURE,y_saved_assessment=caller.Y_SAVED_ASSESSMENT,y_independent_review=caller.Y_INDEPENDENT_REVIEW,original_run_id=c['run_id'],scenario_sha256=c['scenario_sha256'],existing_authority=caller.EXISTING_AUTHORITY,selected_admission=c['authority'],admission_selection=p['admission_selection'],postboot_basis=p['postboot_basis'],old_once=old['once_claim_preserved'],old_clock=old['original_clock'],binding_old_once=x['consumer_stage_once_preserved'],binding_old_clock=x['original_consumer_clock_preserved'],binding_old_source=x['source_file'],binding_old_binding=x['actual_binding'],y_history_pins=caller.Y_HISTORY_PINS,y_custody_delta=Y_DELTA,y_delta_decision=bulk['y_delta_decision'])
    reconciliation.update({k:True for k in BOOLS});reconciliation.update(first_user_API_never_started=True,raw_status='REFUSED_OR_UNKNOWN',original_nested_cause_retained=False,prebirth_reconciliation=hv['prebirth_reconciliation'],authority_id=c['authority_id'],scope=c['scope'],current_contract_sha256=sha(raw(a.canonical_contract(c))),future_clock=c['resources']['clock'],source_freeze=freeze,independent_review=review,workdir=str(Y/'work'));rref=put(Y/'ROOT-Y-FIRST-API-RECONCILIATION.json',reconciliation)
    s=check.SLOT.stat();slot=dict(device=s.st_dev,inode=s.st_ino,uid=s.st_uid,mode=stat.S_IMODE(s.st_mode),nlink=s.st_nlink)
    inputs=dict(schema='frw.Root.F06.canonical-postboot-current-first-user-API-after-closed-preintent.v1',status='ROOT_BOUND_SEPARATE_POSTBOOT_CURRENT_MISSING_FIRST_USER_API_AFTER_CLOSED_Y',contract=a.canonical_contract(c),source_freeze=freeze,independent_review=review,workdir=str(Y/'work'),slot_identity=slot,expected_binding_sha256=None,prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,prebirth_reconciliation=hv['prebirth_reconciliation'],y_preintent_closure=caller.Y_PREINTENT_CLOSURE,y_saved_assessment=caller.Y_SAVED_ASSESSMENT,y_independent_review=caller.Y_INDEPENDENT_REVIEW,y_reconciliation=rref,selected_admission=c['authority'],admission_selection=p['admission_selection'],postboot_basis=p['postboot_basis'])
    caller.validate_inputs(inputs);caller.prebirth_reconciled(inputs)
    bref=put(Y/'ROOT-CONSUMER-INPUTS.json',inputs)
    need(caller.clock_remaining(clock)>=305,'ROOT_CLOCK_INSUFFICIENT_BEFORE_CALLER')
    os.execv(PYTHON,[PYTHON,'-I','-B','-S',str(C/'root_bind_existing_consumer_once.py'),'--execute-once',bref['path'],bref['sha256']])

def main(argv):
    need((len(argv)==3 and argv[0]=='--prepare') or (len(argv)==5 and argv[0]=='--execute-once'),'ROOT_EXPLICIT_MODE_PLAN_SHA_AND_REVIEW_REQUIRED')
    os.umask(0o077);p=plan_input(argv[1],argv[2])
    if argv[0]=='--prepare':print(json.dumps(dict(state='ROOT_BULK_READY_NO_CLOCK_NO_GRANT_NO_SEND',decision=prepare(p))))
    else:
        review_path=path(argv[3]);review=ref(review_path);need(review['sha256']==argv[4],'ROOT_FINAL_REVIEW_CAS_CHANGED');execute_once(p,review)
if __name__=='__main__':main(sys.argv[1:])
