"""Root-owned finite same-upload correct-read issuer/binder/full-consumer caller. Import is inert.
SOURCE ONLY: default UNBOUND. Root must separately supply and accept exact facts.
No credential appears in argv/env/reports. The PRIVATE scenario is an input file.
"""
import contextlib, datetime as dt, fcntl, hashlib, io, json, math, os, resource, signal, stat, subprocess, sys, time, types
from pathlib import Path
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
ISSUER=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py')
ISSUER_SHA='ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518'
AUTHORITY_DIR=Path('/home/jericho/.cache/FRW-KIMI-FMT-20261108')
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
    need(type(v) is dict and set(v)=={'schema','status','contract','source_freeze','independent_review','workdir','slot_identity','expected_binding_sha256'} and v['schema']=='frw.Root.F06.same-upload-correctread-driver.v1' and v['status']=='ROOT_BOUND_ONE_FUTURE_OPERATION','F06_DRIVER_UNBOUND_NO_EFFECT')
    need(type(v['contract']) is dict and v['contract'].get('authority') is None and v['contract'].get('authority_id')=='UNBOUND' and v['contract'].get('status')=='UNBOUND_NOT_GRANTED','F06_NO_OLD_AUTHORITY_OR_EFFECT')
    need(type(v['workdir']) is str and canonical_path(v['workdir']).is_absolute() and v['expected_binding_sha256'] is None,'F06_FRESH_BOUND_DRIVER_INPUT_REQUIRED')
    return True

def clock_remaining(clock):
    now=time.time();mono=time.monotonic()
    need(type(clock) is dict and set(clock)=={'schema','started_at','deadline_at','started_monotonic','deadline_monotonic','boot_id'} and clock['schema']=='frw.Root.F06.original-finite-clock.v1','F06_EXACT_ORIGINAL_CLOCK_REQUIRED')
    need(all(type(clock[k]) in (int,float) and math.isfinite(clock[k]) for k in ('started_at','deadline_at','started_monotonic','deadline_monotonic')) and clock['started_at']<=now<clock['deadline_at']<=clock['started_at']+600 and 0<=clock['started_monotonic']<=mono<clock['deadline_monotonic']<=clock['started_monotonic']+600 and clock['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'F06_ORIGINAL_CLOCK_EXPIRED_OR_CHANGED')
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
    own=Path(__file__).resolve().parent
    freeze_raw=readref(v['source_freeze']);freeze=json.loads(freeze_raw,object_pairs_hook=unique)
    need(freeze.get('schema')=='frw.F06.ordinary-singleton.source-freeze.v1'
         and type(freeze.get('files')) is dict
         and {'f06_source.py','f06_footer.py.txt','first_ingress.py','current_root.py','root_bind_dispatch_once.py'}<=set(freeze['files']),
         'F06_COMPLETE_REVIEWED_SOURCE_FREEZE_REQUIRED')
    for leaf,want in freeze['files'].items():need('/' not in leaf and digest(read(own/leaf))==want['sha256'] and len(read(own/leaf))==want['bytes'],'F06_REVIEWED_SOURCE_DRIFT')
    review=json.loads(readref(v['independent_review']),object_pairs_hook=unique)
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('source_freeze_sha256')==digest(freeze_raw) and review.get('open_critical_defects')==[],'F06_EXACT_INDEPENDENT_SOURCE_ACCEPTANCE_REQUIRED')
    need(all(c.get(field)==ref(own/leaf) for field,leaf in
         (('adapter','f06_source.py'),('first_validator','first_ingress.py'),
          ('actual_root_B_checker','current_root.py'),('footer','f06_footer.py.txt'))),
         'F06_EXACT_LOCAL_REVIEWED_SOURCE_REFERENCES_REQUIRED')
    a=load(c['adapter'],'Root_same_upload_correctread_adapter');a.contract_shape(c,bound=False)
    need(v['independent_review']==c['root_proofs']['source_review'],'F06_DRIVER_SOURCE_REVIEW_REFERENCE_MISMATCH')
    first=a.validate_first(c,read)
    need(type(first) is dict and first.get('source_reference')==c['source_reference'],'F06_EXACT_FIRST_UPLOAD_DEPENDENCY_REQUIRED')
    footer=readref(c['footer']);checker=load(c['actual_root_B_checker'],'Root_same_upload_correctread_current')
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
        # One durable claim before issuance: a failure/unknown is reconciliation,
        # never a request to delete this file, rename the run, issue or send again.
        new(work/'ROOT-ONCE-INVOCATION.json',encoded({'schema':'frw.Root.F06.same-upload-correctread-one-driver-invocation.v1','at':time.time(),'binding':binding_ref,'run_id':c['run_id'],'source_freeze':v['source_freeze'],'no_retry':True}))
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
        for path in AUTHORITY_DIR.glob('INDEPENDENT-AUTHORITY-R*.json'):
            need(c['run_id'] not in json.loads(read(path),object_pairs_hook=unique).get('run_scenarios',{}),'F06_AUTHORITY_ALREADY_ISSUED_RECONCILE_ONLY')
        a.validate_first(c,read)
        issuer=load({'path':str(ISSUER),'bytes':len(read(ISSUER,private=False)),'sha256':ISSUER_SHA},'Root_unchanged_atomic_issuer',private=False)
        issuer.RUN_ID=c['run_id'];issuer.SCENARIO=Path(c['scenario_ref']['path']);issuer.EXTRA_SCENARIOS=();issuer.PACKAGE_FILE=None;issuer.ORDERED_PREDECESSORS={};issuer.SCOPE=c['scope']
        issuer.SUPERSEDES_REASON='One genuinely missing F06 ordinary correct-read of the same reconciled closed upload, no second upload; exact Root proof '+c['root_current_proof']['sha256']+'; consumed/UNKNOWN/clocks preserved, no replay or scope reset.'
        issuer.validate_scope(c['scope'],{c['run_id']:c['scenario_sha256']})
        output=io.StringIO()
        with contextlib.redirect_stdout(output):issuer.main()
        issued=json.loads(output.getvalue(),object_pairs_hook=unique)
        authority={k:issued[k] for k in ('path','bytes','sha256')}
        c.update(authority=authority,authority_id=issued['authority_id'],status='ROOT_BOUND_EXACT_F06_CORRECTREAD')
        a.contract_shape(c);a.admission(c,json.loads(readref(authority),object_pairs_hook=unique))
        bound=work/'bot_tester.f06.root-bound.py';source=a.successor(read(a.BASE,private=False),c,footer);new(bound,source)
        new(work/'ROOT-ACTUAL-BINDING.json',encoded({'schema':'frw.Root.F06.exact-same-upload-correctread-binding.v1','contract':c,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'authority':authority,'independent_review':v['independent_review']}))
        need(a.successor(read(a.BASE,private=False),json.loads(read(work/'ROOT-ACTUAL-BINDING.json'))['contract'],footer)==read(bound),'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE')
        argv=[PYTHON,'-I','-B','-S',str(bound),'--state-dir',str(STATE),'run','--run-id',c['run_id'],'--scenario',c['scenario_ref']['path']]
        new(work/'ROOT-DISPATCH-INVOCATION.json',encoded({'state':'ONE_ORIGINAL_FULL_CONSUMER_NO_RETRY','argv':argv,'source':ref(bound),'whole_effect_sha256':a.digest(a.encoded(a.effect(c))),'clock':c['resources']['clock']}))
        need(clock_remaining(clock)>=c['resources']['operation_seconds']+c['resources']['reserve_seconds'],'F06_CLOCK_INSUFFICIENT_BEFORE_BIRTH')
        a.validate_first(c,read)
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
        ended={'schema':'frw.Root.F06.same-upload-correctread-consumer-ended.v1','at_moscow':dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),'exit_code':code,'elapsed_seconds':time.monotonic()-started,'actor_absent':not (Path('/proc')/str(actor.pid)).exists(),'parent_stops':stops,'canonical_run':ref(STATE/'runs'/(c['run_id']+'.json')) if (STATE/'runs'/(c['run_id']+'.json')).exists() else None,'acceptance':'NOT_ESTABLISHED','next':'reconcile/grade saved original only; no retry or followup authorized'}
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
