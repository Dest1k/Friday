"""Root-owned Task29 first consumer finalizer. Import is inert; no default action.

Root must explicitly supply pinned actual plan/source decision. --prepare freezes
bulk facts without a clock/grant/once. --execute-once admits only a separate never
started user-consumer segment after source, bulk and final independent review.
The original O/X callers, once claims, clocks, binding/source, R106/run/scenario
remain immutable. This file supplies neither Root judgments nor live permission.
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
T=Path('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112')
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
X=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-CONSUMER-EXISTING-R106-20261112')
Y=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112')
C=Y/'source'
J=B/'SOL-TASK29-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json'
PYTHON='/home/jericho/jericho/.venv/bin/python'
ROOT_SOURCE_ACCEPTANCE_SHA='f77044b41cac433f3bb00dc1c59330f531f298af5ff33622c7f49ebf20afd41f'
FIRST_FREEZE_SHA='50d169e40335ffe384790642ad39dcecc0fef37a95b5fe99323ab22140b47d39'
REVIEW_PINS={'review/RESULT.json':'f21ae227825c9d72cab9200c55934b93e73771bb5355db924d74638d833df8a4','review/FIRST-SOURCE-REVIEW.json':'101068b7c7abc46726b60ef43c9768657fe1712e8330905c3e07bdb1f22c1daa','PARENT-SOURCE-ACCEPTANCE.json':'949da5f736aa01d84fa431277a1392705fb3db62846c8ad9181aee4394e7f7fe','SOURCE-FREEZE.json':'8e1165b5fa28b98f3b59cc4a38153ffdc33e799305634e148582a4e0f152fbff','RESULT.json':'456795c96d3379ecf05fdcbc4f3a45e8ee77084c0ba1c0bb4253aff73f20346c'}
LEAVES={'f06_source.py','f06_footer.py.txt','current207.py','root_bind_existing_consumer_once.py'}
BOOLS=('user_consumer_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_user_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_user_consumer_authorized','no_old_driver_or_issuer_retry','binding_failure_closed_before_dispatch','binding_once_clock_source_preserved','no_unknown_consumer_effect')

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
    need(type(v) is dict and set(v)=={'schema','operator','status','root_directory','source_directory','root_source_acceptance','original_prepared_contract','original_observation','constructor_acceptance','prebirth_judgment'},'ROOT_EXACT_PREPARATION_PLAN_REQUIRED')
    need(v['schema']=='frw.Root.F06.Task29.finalizer-plan.v1' and v['operator']=='Root' and v['status']=='ROOT_EXPLICIT_PREPARATION_NO_CLOCK_NO_GRANT' and v['root_directory']==str(Y) and v['source_directory']==str(C),'ROOT_PLAN_UNBOUND')
    need(v['root_source_acceptance']['path']==str(J) and v['original_prepared_contract']['path']==str(O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json') and v['original_observation']['path']==str(O/'OBSERVED-BULK-FACTS.json') and v['constructor_acceptance']['path']==str(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json'),'ROOT_ORIGINAL_BASIS_PATH_CHANGED')
    directory(Y);directory(C)
    need(all(not Y.is_relative_to(old) and not old.is_relative_to(Y) for old in (O,X)),'ROOT_NEW_DIRECTORY_MUST_PRESERVE_OLD_BOUNDARIES')
    return v

def packages(p):
    # Every executable byte/ref and independent/Root source decision authenticates
    # BEFORE the first adapter/checker/caller import. Source freeze is direct child.
    fr=ref(C/'SOURCE-FREEZE.json');need(fr['sha256']==FIRST_FREEZE_SHA,'ROOT_TASK29_FIRST_FREEZE_CHANGED')
    freeze=pinned(fr);need(freeze.get('schema')=='frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1' and set(freeze['files'])==LEAVES,'ROOT_EXACT_FOUR_FILE_FIRST_BRANCH_REQUIRED')
    code_refs={}
    for leaf,want in freeze['files'].items():
        r=dict(path=str(C/leaf),bytes=want['bytes'],sha256=want['sha256']);need(path(C/leaf).parent==C and ref(C/leaf)==r,'ROOT_CODE_DRIFT');code_refs[leaf]=r
    evidence={}
    for leaf,digest in REVIEW_PINS.items():
        evidence[leaf]=ref(T/leaf);need(evidence[leaf]['sha256']==digest,'ROOT_SOL_EVIDENCE_CHANGED')
    leaf=evidence['review/FIRST-SOURCE-REVIEW.json'];review=pinned(leaf)
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('source_freeze_sha256')==fr['sha256'] and review.get('open_critical_defects')==[],'ROOT_FIRST_BRANCH_REVIEW_REQUIRED')
    combined=pinned(evidence['review/RESULT.json']);parent=pinned(evidence['PARENT-SOURCE-ACCEPTANCE.json'])
    need(combined['branch_reviews']['first']==leaf and combined['decision']=='SOURCE_ONLY_READY_UNBOUND' and combined['open_critical_defects']==[] and parent['decision']=='ACCEPT_FINITE_SOURCE_ONLY_RUNTIME_UNBOUND' and parent['source_freeze']==evidence['SOURCE-FREEZE.json'] and evidence['review/RESULT.json'] in parent['child_refs'],'ROOT_SOL_REVIEW_PARENT_JOINS_CHANGED')
    need(p['root_source_acceptance']==dict(path=str(J),bytes=3928,sha256=ROOT_SOURCE_ACCEPTANCE_SHA),'ROOT_SOURCE_ACCEPTANCE_EXACT_PIN_REQUIRED')
    root=pinned(p['root_source_acceptance'])
    need(root.get('schema')=='friday.root.SolTask29.source-acceptance.v1' and root.get('state')=='ROOT_ACCEPTED_CANONICAL_FIRST_AND_CORRECT_SOURCE_RUNTIME_UNBOUND' and root.get('operator')=='Root' and root['branch_freezes']['first']==ref(T/'candidate/first/SOURCE-FREEZE.json') and root['branch_freezes']['first']['sha256']==fr['sha256'] and root['branch_reviews']['first']==leaf and root['future_first_source_review_ref']==leaf and root['independent_review']==evidence['review/RESULT.json'] and root['parent_acceptance']==evidence['PARENT-SOURCE-ACCEPTANCE.json'] and root['source_result']==evidence['RESULT.json'] and root['whole_source_freeze']==evidence['SOURCE-FREEZE.json'] and root['execution_authority'] is False and root['ordinary_first_consumer']=='NOT_RUN' and root['new_actual_currentproof_clock_admission']=='UNBOUND' and root['open_critical_defects']==[],'ROOT_ACTUAL_SOURCE_ACCEPTANCE_REQUIRED_BEFORE_IMPORT')
    # No actual metadata or source decision is supplied by this source package.
    return load(code_refs['f06_source.py'],'Root_T29_adapter'),load(code_refs['current207.py'],'Root_T29_current207'),load(code_refs['root_bind_existing_consumer_once.py'],'Root_T29_caller'),leaf,fr,code_refs

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

# The complete pinned Task29 pre-reconciliation O/X predicates follow below;
# extracted source is preserved by SOURCE-FREEZE and checked by controls.
def closed_history(caller,c):
    v=dict(contract=c,prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE)
    need,readref,unique=caller.need,caller.readref,caller.unique
    EXISTING_AUTHORITY,EXISTING_AUTHORITY_ID=caller.EXISTING_AUTHORITY,caller.EXISTING_AUTHORITY_ID
    ORIGINAL_RUN,ORIGINAL_SCENARIO_SHA=caller.ORIGINAL_RUN,caller.ORIGINAL_SCENARIO_SHA
    ORIGINAL_DIR,BINDING_DIR,PREBIRTH_CLOSURE,STATE=caller.ORIGINAL_DIR,caller.BINDING_DIR,caller.PREBIRTH_CLOSURE,caller.STATE
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
    return closure,x

def judgments(p,caller,c):
    j=pinned(p['prebirth_judgment'])
    need(j.get('schema')=='frw.Root.F06.two-closed-prebirth-judgment.v1' and j.get('operator')=='Root' and j.get('status')=='ROOT_ACTUAL_RECONCILED_FUTURE_MISSING_CONSUMER_ONLY' and j.get('prebirth_closure')==caller.PREBIRTH_CLOSURE and j.get('binding_prebirth_closure')==caller.BINDING_PREBIRTH_CLOSURE and j.get('existing_authority')==caller.EXISTING_AUTHORITY and j.get('original_run_id')==caller.ORIGINAL_RUN and j.get('scenario_sha256')==caller.ORIGINAL_SCENARIO_SHA and all(j.get(k) is True for k in BOOLS),'ROOT_ACTUAL_TWO_CLOSED_HISTORY_JUDGMENT_REQUIRED')
    return closed_history(caller,c)

def prepare(p):
    a,check,caller,review,freeze,code_refs=packages(p)
    need(not (Y/'ROOT-BULK-DECISION.json').exists() and not (Y/'CONSUMER-CLOCK.json').exists() and not (Y/'work').exists(),'ROOT_PREPARATION_ALREADY_STARTED_NO_RETRY')
    c=a.canonical_contract(pinned(p['original_prepared_contract']))
    c.update(authority=caller.EXISTING_AUTHORITY,authority_id=caller.EXISTING_AUTHORITY_ID,adapter=code_refs['f06_source.py'],footer=code_refs['f06_footer.py.txt'],actual_root_B_checker=code_refs['current207.py'],status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD')
    released=pinned(c['authority']);predecessor=Path(c['authority']['path']).with_name('INDEPENDENT-AUTHORITY-R105.json');pred=get(predecessor)
    need(pred['authority_id']==released['supersedes']['authority_id'],'ROOT_R105_CHAIN_MISMATCH')
    c['authority_chain']=dict(predecessor=ref(predecessor),predecessor_authority_id=pred['authority_id'],created_at=released['created_at'],expires_at=released['expires_at'])
    need(c['run_id']==caller.ORIGINAL_RUN and c['scenario_sha256']==caller.ORIGINAL_SCENARIO_SHA and ref(c['scenario_ref']['path'])==c['scenario_ref'],'ROOT_ORIGINAL_RUN_SCENARIO_CHANGED')
    old,x=judgments(p,caller,c)
    c['root_proofs']['source_review']=review
    c['root_current_proof']=put(Y/'CURRENT.NOT_GRANTED.json',dict(status='UNBOUND_NO_CURRENT_ADMISSION'))
    c['resources']['clock']=put(Y/'CLOCK.NOT_STARTED.json',dict(status='UNBOUND_CONSUMER_CLOCK_NOT_STARTED'))
    placeholder=put(Y/'BUDGET.NOT_GRANTED.json',dict(status='UNBOUND_CONSUMER_RESOURCES_NO_ACTOR'))
    c['resources']['owned_parent_wait_cleanup']=placeholder
    c['root_proofs']['owned_actor_stop_resources']=placeholder;c['root_proofs']['authoritative_budget_policy']=placeholder
    privacy=pinned(c['root_proofs']['private_password_handling'])
    privacy['private_roots']=sorted(set(privacy['private_roots'])|{str(Y),str(T),str(Path(__file__).parent),str(B),str(predecessor.parent)})
    privacy['scope']+=' Task29 exact first branch and Root helper/source/consumer directories covered. Unchanged qualified207/206 evidence is retained only at its original stated scope; no new runtime or first ordinary acceptance.'
    c['root_proofs']['private_password_handling']=put(Y/'ROOT-PRIVACY.json',privacy)
    check.disjoint(privacy['private_roots'],privacy['effective_product_roots'])
    a.admission(c,released,read=caller.read)
    proof,actual=baseline(c,a,check);need(actual==pinned(p['original_observation']),'ROOT_MUTABLE_BASIS_DRIFT_RECONCILE_BEFORE_CLOCK')
    constructor(p,actual,check)
    c['boundary']=actual['f06_mutable_boundary'];proof,now=baseline(c,a,check);need(now==actual,'ROOT_CURRENT_CHANGED_DURING_BULK')
    check.semantic(proof,c,actual);check.private_material(proof,c,actual,Y/'PREPARED-CURRENT-PROOF.json')
    (Y/'work').mkdir(mode=0o700)
    put(Y/'OBSERVED-BULK-FACTS.json',actual);put(Y/'CONTRACT.PREPARED-NO-CLOCK.json',a.canonical_contract(c))
    decision=dict(schema='frw.Root.F06.Task29.bulk-decision.v1',decision='ROOT_PREPARED_SEPARATE_UNSTARTED_USER_CONSUMER_NO_CLOCK_NO_GRANT',plan=p,root_finalizer=ref(Path(__file__)),source_freeze=freeze,source_review=review,root_source_acceptance=p['root_source_acceptance'],contract=ref(Y/'CONTRACT.PREPARED-NO-CLOCK.json'),observation=ref(Y/'OBSERVED-BULK-FACTS.json'),prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,existing_authority=c['authority'],old_callers_once_clocks_binding_source_preserved=True,issuer_repeated=False)
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
    need(r.get('schema')=='frw.Root.F06.Task29.finalizer-review.v1' and r.get('decision')=='ACCEPT_ROOT_FINALIZER_NO_LIVE_GRANT' and r.get('root_finalizer')==ref(Path(__file__)) and r.get('root_bulk_decision')==bulkref and r.get('root_source_acceptance')==p['root_source_acceptance'] and r.get('open_critical_defects')==[],'ROOT_FINALIZER_AND_BULK_INDEPENDENT_REVIEW_REQUIRED')
    a,check,caller,review,freeze,code_refs=packages(p)
    bulk=pinned(bulkref)
    need(bulk['plan']==p and bulk['root_finalizer']==ref(Path(__file__)) and bulk['contract']==ref(Y/'CONTRACT.PREPARED-NO-CLOCK.json') and bulk['observation']==ref(Y/'OBSERVED-BULK-FACTS.json') and bulk['source_review']==review and bulk['source_freeze']==freeze and bulk['root_source_acceptance']==p['root_source_acceptance'],'ROOT_BULK_CAS_CHANGED')
    need(not (Y/'CONSUMER-CLOCK.json').exists() and not any((Y/'work').iterdir()),'ROOT_STAGE_ALREADY_STARTED_OR_UNKNOWN_NO_RETRY')
    c=a.canonical_contract(pinned(bulk['contract']));old,x=judgments(p,caller,c)
    constructor(p,pinned(bulk['observation']),check)
    prepared,actual=baseline(c,a,check);need(actual==pinned(bulk['observation']),'ROOT_MUTABLE_BASIS_CHANGED_BEFORE_CLOCK')
    check.semantic(prepared,c,actual);check.private_material(prepared,c,actual,Y/'PREPARED-CURRENT-PROOF.json')
    a.admission(c,pinned(c['authority']),read=caller.read)
    technical_carriers(check,actual)
    # Root explicitly invoked the finite future stage; no prep/review wait inside.
    wall,mono=time.time(),time.monotonic()
    need(wall>=max(dt.datetime.fromisoformat(i['at_moscow']).timestamp() for i in (old,x)),'ROOT_NEW_CLOCK_PRECEDES_CLOSED_BOUNDARY')
    clock=dict(schema='frw.Root.F06.unstarted-consumer-finite-clock.v1',started_at=wall,deadline_at=wall+600,started_monotonic=mono,deadline_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    cref=put(Y/'CONSUMER-CLOCK.json',clock);c['resources']['clock']=cref
    wait=put(Y/'OWNED-CONSUMER-WAIT.json',dict(operator='Root',status='ROOT_BOUND_FINITE_SAME_CHILD',clock=cref,caller=code_refs['root_bind_existing_consumer_once.py'],same_child_nonreentrant_signal_drain=True,pending_birth_signal_handoff=True,reap_inside_original_deadline=True,no_appended_cleanup_time=True,stop_unconfirmed_retains_child_slot=True,permanent_gateway_dashboard_untouched=True,old_callers_closed=True,one_untouched_user_consumer_only=True))
    c['resources']['owned_parent_wait_cleanup']=wait;c['root_proofs']['owned_actor_stop_resources']=wait
    c['root_proofs']['authoritative_budget_policy']=put(Y/'CONSUMER-BUDGET-POLICY.json',dict(operator='Root',status='ROOT_ADMITTED_UNSTARTED_USER_CONSUMER_SEGMENT',criterion=c['root_proofs']['original_criterion'],source_review=review,timing=a.TIMING,clock=cref,cpu_seconds=c['resources']['cpu_seconds'],address_space_bytes=c['resources']['max_rss_bytes'],store_growth_and_temporary_copy_cap=c['resources']['disk_bytes'],existing_authority=c['authority'],prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,old_clock=old['original_clock'],binding_old_clock=x['original_consumer_clock_preserved'],old_clocks_reset=False,old_once_reused=False,issuer_repeated=False,one_initial_upload_only=True,followup_or_retry_authorized=False,original_run_and_scenario_unchanged=True,scope=c['scope']))
    c=a.canonical_contract(c);prepared,now=baseline(c,a,check);need(now==actual,'ROOT_MUTABLE_FACTS_CHANGED_DURING_FINAL_BINDING')
    prepared.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION',observed=now)
    check.semantic(prepared,c,now);check.private_material(prepared,c,now,Y/'PREPARED-CURRENT-PROOF.json')
    c['root_current_proof']=put(Y/'PREPARED-CURRENT-PROOF.json',prepared)
    old,x=judgments(p,caller,c);t=time.time()
    reconciliation=dict(schema='frw.Root.F06.two-closed-prebirth-reconciliation.v1',operator='Root',status='ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER',created_at=t,expires_at=t+120,prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,original_run_id=c['run_id'],scenario_sha256=c['scenario_sha256'],existing_authority=c['authority'],old_once=old['once_claim_preserved'],old_clock=old['original_clock'],binding_old_once=x['consumer_stage_once_preserved'],binding_old_clock=x['original_consumer_clock_preserved'],binding_old_source=x['source_file'],binding_old_binding=x['actual_binding'])
    reconciliation.update({k:True for k in BOOLS});rref=put(Y/'ROOT-PREBIRTH-RECONCILIATION.json',reconciliation)
    s=check.SLOT.stat();slot=dict(device=s.st_dev,inode=s.st_ino,uid=s.st_uid,mode=stat.S_IMODE(s.st_mode),nlink=s.st_nlink)
    inputs=dict(schema='frw.Root.F06.canonical-existing-R106-first-consumer.v1',status='ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER',contract=a.canonical_contract(c),source_freeze=freeze,independent_review=review,workdir=str(Y/'work'),slot_identity=slot,expected_binding_sha256=None,prebirth_closure=caller.PREBIRTH_CLOSURE,binding_prebirth_closure=caller.BINDING_PREBIRTH_CLOSURE,prebirth_reconciliation=rref)
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
