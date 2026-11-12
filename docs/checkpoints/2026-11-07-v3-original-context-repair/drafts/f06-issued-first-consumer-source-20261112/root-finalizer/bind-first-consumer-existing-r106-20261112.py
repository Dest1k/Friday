"""Root binds only the never-started consumer stage; never calls issuer/old driver."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import types

os.umask(0o077)
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
X=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-CONSUMER-EXISTING-R106-20261112')
W=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ISSUED-AUTHORITY-FIRST-CONSUMER-SOURCE-20261112')
D=Path('/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-ISSUED-FIRST-CONSUMER-20261112')
J=Path('/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-FIRST-CONSUMER-ROOT-FINALIZER-20261112/RESULT.json')
PYTHON='/home/jericho/jericho/.venv/bin/python'
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def helper():
 p=B/'bind-first-ordinary-f06-20261112.py'
 assert hashlib.sha256(p.read_bytes()).hexdigest()=='dcae3bd55d52d435a66d432a01b0f17da76e88cb21c83054cb2861d88be739d7'
 return module(p,'unchanged_root_pure_helpers')
def get(p):return json.loads(Path(p).read_bytes())
def packages():
 h=helper()
 assert h.ref(W/'SOURCE-FREEZE.json')['sha256']=='4e84373385be18bcde23643e455437e62b734a7fbfa327e9de68d872ebeab3b1'
 for leaf,want in get(W/'SOURCE-FREEZE.json')['files'].items():
  assert Path(leaf).name==leaf and h.ref(W/leaf)==dict(path=str(W/leaf),bytes=want['bytes'],sha256=want['sha256'])
 assert h.ref(D/'RESULT.json')['sha256']=='5598964d3d50737989845f022df96be0157052de4101aea5fc2c1bdedf430e87'
 review=get(D/'RESULT.json');assert review['decision']=='SOURCE_ONLY_READY_UNBOUND' and review['source_freeze_sha256']==h.ref(W/'SOURCE-FREEZE.json')['sha256'] and not review['open_critical_defects']
 a=h.load(W/'f06_source.py','first_consumer_adapter');checker=h.load(W/'current207.py','first_consumer_current');caller=h.load(W/'root_bind_existing_consumer_once.py','first_consumer_caller')
 return h,a,checker,caller
def prepare():
 h,a,check,caller=packages()
 if X.exists():
  # The sole known failed bulk preparation stopped at a missing pure-helper API,
  # before any observation/clock/once/grant/consumer. Preserve its inert marker.
  assert {p.name for p in X.iterdir()}=={'work','CURRENT.NOT_GRANTED.json'} and not any((X/'work').iterdir())
  assert get(X/'CURRENT.NOT_GRANTED.json')==dict(status='UNBOUND_PREPARATION_ONLY_NO_CURRENT_ADMISSION')
 else:X.mkdir(mode=0o700);(X/'work').mkdir(mode=0o700)
 c=get(O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json')
 authority=caller.EXISTING_AUTHORITY;assert h.ref(Path(authority['path']))==authority
 released=get(authority['path']);parent=Path(authority['path']).with_name('INDEPENDENT-AUTHORITY-R105.json');pred=get(parent)
 assert pred['authority_id']==released['supersedes']['authority_id']
 c.update(authority=authority,authority_id=caller.EXISTING_AUTHORITY_ID,authority_chain=dict(predecessor=h.ref(parent),predecessor_authority_id=pred['authority_id'],created_at=released['created_at'],expires_at=released['expires_at']),status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',adapter=h.ref(W/'f06_source.py'),footer=h.ref(W/'f06_footer.py.txt'),actual_root_B_checker=h.ref(W/'current207.py'))
 c['root_current_proof']=h.ref(X/'CURRENT.NOT_GRANTED.json') if (X/'CURRENT.NOT_GRANTED.json').exists() else h.put(X/'CURRENT.NOT_GRANTED.json',dict(status='UNBOUND_PREPARATION_ONLY_NO_CURRENT_ADMISSION'))
 assert c['run_id']==caller.ORIGINAL_RUN and c['scenario_sha256']==caller.ORIGINAL_SCENARIO_SHA and h.ref(Path(c['scenario_ref']['path']))==c['scenario_ref']
 a.admission(c,released,read=caller.read)
 c['root_proofs']['source_review']=h.ref(D/'RESULT.json')
 c['resources']['clock']=h.put(X/'CLOCK.NOT_STARTED.json',dict(status='UNBOUND_CONSUMER_CLOCK_NOT_STARTED'))
 placeholder=h.put(X/'BUDGET.NOT_GRANTED.json',dict(status='UNBOUND_CONSUMER_RESOURCES_NO_ACTOR'))
 c['resources']['owned_parent_wait_cleanup']=placeholder
 c['root_proofs']['owned_actor_stop_resources']=placeholder;c['root_proofs']['authoritative_budget_policy']=placeholder
 privacy=get(c['root_proofs']['private_password_handling']['path'])
 privacy['private_roots']=sorted(set(privacy['private_roots'])|{str(W),str(X),str(D),str(parent.parent)})
 privacy['scope']+=' Existing R106 first-consumer source/review/authority-parent private directories covered; prior observed product consumer remains historical206 unchanged207 evidence.'
 c['root_proofs']['private_password_handling']=h.put(X/'ROOT-PRIVACY.json',privacy)
 proof,actual=h.baseline(c,check)
 assert actual==get(O/'OBSERVED-BULK-FACTS.json'),'Unchanged history/current basis drifted: reconcile before any clock'
 c['boundary']=actual['f06_mutable_boundary'];proof.update(runtime_privacy_review=c['root_proofs']['private_password_handling'],history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'])
 check.semantic(proof,c,actual);check.private_material(proof,c,actual,X/'PREPARED-CURRENT-PROOF.json')
 h.put(X/'OBSERVED-BULK-FACTS.json',actual);h.put(X/'CONTRACT.PREPARED-NO-CLOCK.json',c)
 h.put(X/'ROOT-BULK-DECISION.json',dict(schema='friday.root.F06.unstarted-consumer-bulk.v1',decision='ROOT_PREPARED_SEPARATE_UNSTARTED_CONSUMER_NO_CLOCK_NO_NEW_AUTHORITY_NO_SEND',source_review=h.ref(D/'RESULT.json'),source_freeze=h.ref(W/'SOURCE-FREEZE.json'),contract=h.ref(X/'CONTRACT.PREPARED-NO-CLOCK.json'),observation=h.ref(X/'OBSERVED-BULK-FACTS.json'),prebirth_closure=caller.PREBIRTH_CLOSURE,existing_authority=authority,old_driver_retry=False,issuer_repeated=False,typed_semantic_and_private_material_checks_pass=True))
 print(json.dumps(dict(state='BULK_READY_NO_CLOCK_NO_NEW_AUTHORITY_NO_SEND',decision=h.ref(X/'ROOT-BULK-DECISION.json'))))
def execute_once():
 h,a,check,caller=packages();review=get(J)
 assert review['decision']=='ACCEPT_ROOT_FINALIZER_NO_LIVE_GRANT' and review['root_finalizer_sha256']==h.ref(Path(__file__))['sha256'] and review['root_bulk_decision_sha256']==h.ref(X/'ROOT-BULK-DECISION.json')['sha256'] and review['open_critical_defects']==[]
 assert not (X/'CONSUMER-CLOCK.json').exists() and not (X/'work/ROOT-FIRST-CONSUMER-ONCE.json').exists()
 bulk=get(X/'ROOT-BULK-DECISION.json')
 assert h.ref(X/'CONTRACT.PREPARED-NO-CLOCK.json')==bulk['contract'] and h.ref(X/'OBSERVED-BULK-FACTS.json')==bulk['observation']
 assert h.ref(D/'RESULT.json')==bulk['source_review'] and h.ref(W/'SOURCE-FREEZE.json')==bulk['source_freeze']
 c=get(X/'CONTRACT.PREPARED-NO-CLOCK.json')
 accepted=get(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json');basis=get(accepted['basis']['path']);assert h.ref(Path(accepted['basis']['path']))==accepted['basis']
 for row in basis['source_files'].values():check.reference(row['ref'],private=False)
 for row in accepted['proxy_scope_metadata']:check.reference(row['file'],private=True)
 preclock,actual=h.baseline(c,check);assert actual==get(X/'OBSERVED-BULK-FACTS.json')
 preclock.update(runtime_privacy_review=c['root_proofs']['private_password_handling'],history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'])
 check.semantic(preclock,c,actual);check.private_material(preclock,c,actual,X/'PREPARED-CURRENT-PROOF.json')
 a.admission(c,get(c['authority']['path']),read=caller.read)
 # Bounded metadata only; supports evaluation of this effect's newly produced carriers.
 profile=check.H/'profiles/telegram-bot-8812646969';dirs=[check.H/n for n in ('logs','sessions','memories','user-artifacts')]+[profile/n for n in ('logs','sessions','memories','workspace','cache','.curator_backups')]
 files=[]
 for root in dirs:
  if root.exists():
   for path in sorted(root.rglob('*')):
    assert not path.is_symlink() and len(files)<12000
    if path.is_file():
     s=path.stat();files.append(dict(path=str(path),device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
 h.put(X/'PRE-EFFECT-TECHNICAL-CARRIER-METADATA.json',dict(roots=list(map(str,dirs)),files=files,db_metadata=actual['databases'],at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),content_read=False))
 cursor=subprocess.run(['journalctl','--user','-u','hermes-gateway-1b7e7667.service','-n','0','--show-cursor','--no-pager'],check=True,capture_output=True,timeout=10).stdout.decode()
 h.put(X/'PRE-EFFECT-JOURNAL-CURSOR.json',dict(cursor=cursor,content_read=False))
 # New clock for the untouched consumer segment only. Old closed clock stays immutable.
 wall,mono=time.time(),time.monotonic();clock=dict(schema='frw.Root.F06.unstarted-consumer-finite-clock.v1',started_at=wall,deadline_at=wall+600,started_monotonic=mono,deadline_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 cref=h.put(X/'CONSUMER-CLOCK.json',clock);c['resources']['clock']=cref
 wait=h.put(X/'OWNED-CONSUMER-WAIT.json',dict(operator='Root',clock=cref,caller=h.ref(W/'root_bind_existing_consumer_once.py'),old_issuer_driver_closed=True,one_untouched_consumer_only=True,R3_same_child_stop_reap_original_deadline=True,no_appended_cleanup_time=True,permanent_services_untouched=True))
 c['resources']['owned_parent_wait_cleanup']=wait;c['root_proofs']['owned_actor_stop_resources']=wait
 c['root_proofs']['authoritative_budget_policy']=h.put(X/'CONSUMER-BUDGET-POLICY.json',dict(operator='Root',status='ROOT_ADMITTED_UNSTARTED_CONSUMER_SEGMENT',clock=cref,timing=a.TIMING,existing_authority=c['authority'],prebirth_closure=caller.PREBIRTH_CLOSURE,old_clock=get(caller.PREBIRTH_CLOSURE['path'])['original_clock'],old_clock_not_reset=True,old_once_not_reused=True,issuer_repeated=False,original_run_and_scenario_unchanged=True,scope=c['scope']))
 prepared,now=h.baseline(c,check);assert now==actual,'Mutable facts changed during final binding'
 prepared.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION',observed=now,runtime_privacy_review=c['root_proofs']['private_password_handling'],history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'])
 check.semantic(prepared,c,now);check.private_material(prepared,c,now,X/'PREPARED-CURRENT-PROOF.json')
 c['root_current_proof']=h.put(X/'PREPARED-CURRENT-PROOF.json',prepared)
 old=get(caller.PREBIRTH_CLOSURE['path']);t=time.time()
 reconciled=dict(schema='frw.Root.F06.issuer-only-prebirth-reconciliation.v1',operator='Root',status='ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER',created_at=t,expires_at=t+120,prebirth_closure=caller.PREBIRTH_CLOSURE,original_run_id=c['run_id'],scenario_sha256=c['scenario_sha256'],existing_authority=c['authority'],old_once=old['once_claim_preserved'],old_clock=old['original_clock'])
 for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry'):reconciled[key]=True
 rref=h.put(X/'ROOT-PREBIRTH-RECONCILIATION.json',reconciled)
 s=check.SLOT.stat();slot=dict(device=s.st_dev,inode=s.st_ino,uid=s.st_uid,mode=stat.S_IMODE(s.st_mode),nlink=s.st_nlink)
 inputs=dict(schema='frw.Root.F06.existing-R106-first-consumer.v1',status='ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER',contract=c,source_freeze=h.ref(W/'SOURCE-FREEZE.json'),independent_review=h.ref(D/'RESULT.json'),workdir=str(X/'work'),slot_identity=slot,expected_binding_sha256=None,prebirth_closure=caller.PREBIRTH_CLOSURE,prebirth_reconciliation=rref)
 caller.validate_inputs(inputs);caller.prebirth_reconciled(inputs)
 bref=h.put(X/'ROOT-CONSUMER-INPUTS.json',inputs)
 assert caller.clock_remaining(clock)>=305
 os.execv(PYTHON,[PYTHON,'-I','-B','-S',str(W/'root_bind_existing_consumer_once.py'),'--execute-once',bref['path'],bref['sha256']])
if __name__=='__main__':
 assert sys.argv[1:] in (['--prepare'],['--execute-once'])
 prepare() if sys.argv[1]=='--prepare' else execute_once()
