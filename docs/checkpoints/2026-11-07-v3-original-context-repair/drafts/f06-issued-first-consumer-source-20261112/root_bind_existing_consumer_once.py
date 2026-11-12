"""Root-owned first-consumer-only caller for an already issued R106. Import is inert.
SOURCE ONLY: default UNBOUND. Root must separately supply and accept exact facts.
No credential appears in argv/env/reports. The PRIVATE scenario is an input file.
"""
import datetime as dt, fcntl, hashlib, json, math, os, resource, signal, stat, subprocess, sys, time, types
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
    need(type(v) is dict and set(v)=={'schema','status','contract','source_freeze','independent_review','workdir','slot_identity','expected_binding_sha256','prebirth_closure','prebirth_reconciliation'} and v['schema']=='frw.Root.F06.existing-R106-first-consumer.v1' and v['status']=='ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER','F06_CONSUMER_STAGE_UNBOUND_NO_EFFECT')
    c=v['contract']
    need(type(c) is dict and c.get('authority')==EXISTING_AUTHORITY and c.get('authority_id')==EXISTING_AUTHORITY_ID and c.get('status')=='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD' and c.get('run_id')==ORIGINAL_RUN and c.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and c.get('scenario_ref',{}).get('sha256')==ORIGINAL_SCENARIO_SHA,'F06_ONLY_ORIGINAL_RUN_AND_EXISTING_R106')
    need(c.get('authority_chain',{}).get('created_at')==EXISTING_CREATED and c['authority_chain'].get('expires_at')==EXISTING_EXPIRES and v['prebirth_closure']==PREBIRTH_CLOSURE,'F06_EXISTING_ISSUANCE_OR_CLOSURE_CHANGED')
    need(type(v['workdir']) is str and canonical_path(v['workdir']).is_absolute() and v['expected_binding_sha256'] is None,'F06_FRESH_CONSUMER_BINDING_REQUIRED')
    work=canonical_path(v['workdir'])
    need(not work.is_relative_to(ORIGINAL_DIR) and not ORIGINAL_DIR.is_relative_to(work),'F06_OLD_DRIVER_WORKDIR_MUST_REMAIN_UNTOUCHED')
    return True

def prebirth_reconciled(v):
    """Read-only pins and Root judgement for the separately admitted missing stage.
    Old driver/issuance/once/600 are closed historical effects, never resumed.
    """
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
    r=json.loads(readref(v['prebirth_reconciliation']),object_pairs_hook=unique)
    need(r.get('schema')=='frw.Root.F06.issuer-only-prebirth-reconciliation.v1' and r.get('operator')=='Root' and r.get('status')=='ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER' and r.get('prebirth_closure')==v['prebirth_closure'] and r.get('original_run_id')==ORIGINAL_RUN and r.get('scenario_sha256')==ORIGINAL_SCENARIO_SHA and r.get('existing_authority')==EXISTING_AUTHORITY and r.get('old_once')==oldonce and r.get('old_clock')==oldclock,'F06_ROOT_RECONCILIATION_EXACT_REFS_REQUIRED')
    for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry'):
        need(r.get(key) is True,'F06_ROOT_PREBIRTH_RECONCILIATION_REQUIRED')
    need(type(r.get('created_at')) in (int,float) and type(r.get('expires_at')) in (int,float) and math.isfinite(r['created_at']) and math.isfinite(r['expires_at']) and r['created_at']<=time.time()<r['expires_at']<=r['created_at']+120,'F06_ROOT_PREBIRTH_RECONCILIATION_STALE')
    need(v['contract']['resources']['clock']!=oldclock and v['contract']['resources']['clock']['path']!=oldclock['path'],'F06_OLD_CLOCK_REUSE_OR_EXTENSION_REFUSED')
    return closure

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
    c=json.loads(encoded(v['contract']),object_pairs_hook=unique)
    prebirth_reconciled(v)
    a=load(c['adapter'],'Root_first_F06_adapter');a.contract_shape(c)
    a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)
    footer=readref(c['footer']);checker=load(c['actual_root_B_checker'],'Root_first_F06_current207')
    freeze_raw=readref(v['source_freeze']);freeze=json.loads(freeze_raw,object_pairs_hook=unique)
    need(freeze.get('schema')=='frw.F06.existing-R106-first-consumer.source-freeze.v1','F06_SOURCE_FREEZE_REQUIRED')
    own=Path(__file__).resolve().parent
    for leaf,want in freeze['files'].items():need('/' not in leaf and digest(read(own/leaf))==want['sha256'] and len(read(own/leaf))==want['bytes'],'F06_REVIEWED_SOURCE_DRIFT')
    review=json.loads(readref(v['independent_review']),object_pairs_hook=unique)
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('source_freeze_sha256')==digest(freeze_raw) and review.get('open_critical_defects')==[],'F06_EXACT_INDEPENDENT_SOURCE_ACCEPTANCE_REQUIRED')
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
        # Separate never-started consumer claim. Old once/issuance remain untouched.
        prebirth_reconciled(v)
        new(work/'ROOT-FIRST-CONSUMER-ONCE.json',encoded({'schema':'frw.Root.F06.first-consumer-invocation.v1','at':time.time(),'binding':binding_ref,'run_id':c['run_id'],'source_freeze':v['source_freeze'],'existing_authority':c['authority'],'prebirth_closure':v['prebirth_closure'],'old_driver_resume':False,'issuer_invoked':False,'no_retry':True}))
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
        # Existing issuance only: no issuer module, scan, entry point or reissue.
        a.admission(c,json.loads(readref(c['authority']),object_pairs_hook=unique),read=read)
        bound=work/'bot_tester.f06.root-bound.py';source=a.successor(read(a.BASE,private=False),c,footer);new(bound,source)
        new(work/'ROOT-ACTUAL-BINDING.json',encoded({'schema':'frw.Root.F06.exact-first-wrongread-binding.v1','contract':c,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'authority':c['authority'],'independent_review':v['independent_review']}))
        need(a.successor(read(a.BASE,private=False),json.loads(read(work/'ROOT-ACTUAL-BINDING.json'))['contract'],footer)==read(bound),'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE')
        argv=[PYTHON,'-I','-B','-S',str(bound),'--state-dir',str(STATE),'run','--run-id',c['run_id'],'--scenario',c['scenario_ref']['path']]
        new(work/'ROOT-DISPATCH-INVOCATION.json',encoded({'state':'ONE_PREVIOUSLY_UNSTARTED_FULL_CONSUMER_EXISTING_R106_NO_RETRY','argv':argv,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'clock':c['resources']['clock']}))
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
