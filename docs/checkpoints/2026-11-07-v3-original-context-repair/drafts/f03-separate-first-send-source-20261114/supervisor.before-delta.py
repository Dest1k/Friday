"""Narrow Root-only F03 caller adaptation. No retry and no import effects.
The accepted finite wait/stop/reap and launch block are copied unchanged except
metadata names/argv and the separately validated NEW paired wait_clock.
"""
import ast,json,os,resource,signal,stat,subprocess,time,types
from pathlib import Path
PINS = {'case_entry.py': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-MISSING-FIRST-SEND-CONTRACT-CANDIDATE-20261114/candidate/case_entry.py', 'bytes': 9079, 'sha256': '8bc9a61b2b9da8b62179940d389bb083b7f88f38927776706672537b882064bf'}}
PYTHON='/home/jericho/jericho/.venv/bin/python'
def need(value,reason):
    if not value:raise ValueError(reason)
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
    raise StopUnconfirmed('F03_STOP_UNCONFIRMED_ORIGINAL_OUTER_DEADLINE')

def launch(contract_reference,projected_meta,workdir,slot_fd):
    # Loading the entry is source-pinned before exec. Root accepts this source
    # independently; the separate decision must also bind it exactly.
    entry_ref=PINS['case_entry.py'];p=Path(entry_ref['path']);z=p.stat()
    if not stat.S_ISREG(z.st_mode)or z.st_uid!=os.getuid()or stat.S_IMODE(z.st_mode)!=0o600 or z.st_nlink!=1 or not 0<z.st_size==entry_ref['bytes']<=1024**2 or p.parent.stat().st_uid!=os.getuid()or stat.S_IMODE(p.parent.stat().st_mode)!=0o700 or any(q.is_symlink()for q in(p,*p.parents)):raise ValueError('F03_SUPERVISOR_ENTRY_CUSTODY')
    ident=lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb')as f:
        if ident(z)!=ident(os.fstat(f.fileno())):raise ValueError('F03_SUPERVISOR_ENTRY_CAS')
        b=f.read(entry_ref['bytes']+1);fz=os.fstat(f.fileno())
    import hashlib
    if ident(z)!=ident(fz)or ident(z)!=ident(p.stat())or len(b)!=entry_ref['bytes']or hashlib.sha256(b).hexdigest()!=entry_ref['sha256']:raise ValueError('F03_SUPERVISOR_ENTRY_PIN_OR_CAS')
    entry=types.ModuleType('_F03_reviewed_child_entry');entry.__file__=str(p);exec(compile(b,str(p),'exec'),entry.__dict__)
    phase,c,clock,full=entry.boundary(contract_reference);entry.slot_identity(slot_fd,phase)
    decision=phase.doc(c['decision'])
    if decision.get('supervisor_source')!=phase.pin(Path(__file__),phase.read(Path(__file__))):raise ValueError('F03_SEPARATE_SUPERVISOR_NOT_BOUND')
    if projected_meta.get('contract')!=contract_reference:raise ValueError('F03_SUPERVISOR_CONTRACT_META_CHANGED')
    row=json.loads(phase.read(phase.STATE/'runs'/(phase.RUN+'.json')),object_pairs_hook=phase.unique)
    phase.validate_preclaim(projected_meta,row,phase.STATE)
    cc=full.F03_CONTRACT;proof=phase.doc(cc['root_current_review'])
    current=entry.load(cc['current_gate'],'_F03_current_for_root_slot')
    current.proof_shape(proof);current.lifetime(proof)
    if proof.get('shared_slot_owner',{}).get('pid')!=os.getpid():raise ValueError('F03_ACTUAL_ROOT_SLOT_OWNER_REQUIRED')
    current.shared_slot(proof['shared_slot_owner'],current.helper())
    # The child's actual current.check remains mandatory before GET and intent.
    observed=current.observe(proof,boundary_phase='CURSOR_AUTHORITY',first_send=projected_meta,first_send_preclaim=True)
    if observed!=proof.get('observed'):raise ValueError('F03_SUPERVISOR_PRECLAIM_CURRENT_CAS_CHANGED')
    current.semantics(proof['contract_effect'],current.proof_documents(proof['contract_effect']),observed)
    r=cc['resources']
    if any(type(r.get(k))is not int or r.get(k)!=v for k,v in {'cpu_seconds':120,'max_rss_bytes':536870912,'disk_bytes':67108864,'operation_seconds':300,'reply_window_seconds':180,'ack_seconds':30,'reserve_seconds':5,'outer_seconds':600}.items()):raise ValueError('F03_ORIGINAL_CAPS_CHANGED')
    work=Path(workdir)
    if work!=Path(c['consumer']['path']).parent or any(q.is_symlink()for q in(work,*work.parents))or work.stat().st_uid!=os.getuid()or stat.S_IMODE(work.stat().st_mode)!=0o700:raise ValueError('F03_SUPERVISOR_PRIVATE_BOUND_WORKDIR_REQUIRED')
    privacy=current.proof_documents(proof['contract_effect'])['private_exclusion']
    if str(work)not in privacy.get('private_roots',[]):raise ValueError('F03_SUPERVISOR_WORKDIR_PRIVATE_EXCLUSION_REQUIRED')
    wait_clock={'deadline_at':clock['outer_deadline_wall'],'deadline_monotonic':clock['outer_deadline_monotonic']}
    child_argv=[str(p),'--contract',contract_reference['path'],'--bytes',str(contract_reference['bytes']),'--sha256',contract_reference['sha256'],'--slot-fd',str(slot_fd)]
    bootstrap="import sys;sys.argv="+repr(child_argv)+";exec(compile("+repr(b)+","+repr(str(p))+",'exec'),{'__name__':'__main__','__file__':"+repr(str(p))+"})"
    argv=[PYTHON,'-I','-B','-S','-c',bootstrap]
    phase.contract(contract_reference,preintent=True,active=True);current.lifetime(proof)
    # Exact protected parent invocation record: partial/log presence is preserved.
    phase.exclusive(work/'ROOT-MISSING-FIRST-SEND-DISPATCH.json',phase.enc(dict(schema='frw.Root.F03.separate-first-send-dispatch.v1',contract=contract_reference,entry=entry_ref,consumer=c['consumer'],new_clock=c['clock'],wait_clock=wait_clock,argv=argv,no_retry=True)))
    new=phase.exclusive;encoded=phase.enc
    cpus=sorted(os.sched_getaffinity(0))[:2];need(cpus,'F03_NO_AVAILABLE_CPU')
    def child_limits():
        resource.setrlimit(resource.RLIMIT_CPU,(r['cpu_seconds'],r['cpu_seconds']));resource.setrlimit(resource.RLIMIT_AS,(r['max_rss_bytes'],r['max_rss_bytes']));resource.setrlimit(resource.RLIMIT_FSIZE,(r['disk_bytes'],r['disk_bytes']));os.sched_setaffinity(0,cpus)
    actor=None;stops=[];forwarded_stops=0;wait_attempted=False;forwarding_stops=False
    prior={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
    def forward_stops():
        nonlocal forwarded_stops,forwarding_stops
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
            if actor is not None and forwarded_stops<len(stops):forward_stops()
    def parent_stop(n,_):stops.append({'signal':n,'at':time.time()});forward_stops()
    with os.fdopen(os.open(work/'CONSUMER.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as out,os.fdopen(os.open(work/'CONSUMER.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as err:
        try:
            for n in prior:signal.signal(n,parent_stop)
            need(not stops,'F03_STOP_BEFORE_CONSUMER_BIRTH');started=time.monotonic()
            phase.contract(contract_reference,preintent=True,active=True);current.lifetime(proof)
            need(not stops,'F03_STOP_DURING_FINAL_PREBIRTH_CHECK')
            actor=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(slot_fd,),preexec_fn=child_limits)
            try:
                forward_stops();identity_value=current.kernel(actor.pid)
                new(work/'ROOT-CONSUMER-ACTOR.json',encoded({'identity':identity_value,'clock':c['clock'],'cpu_seconds':r['cpu_seconds'],'max_rss_bytes':r['max_rss_bytes'],'per_file_cap_bytes':r['disk_bytes'],'affinity_cpus':cpus}))
            finally:wait_attempted=True;code=wait_owned(actor,wait_clock,r['reserve_seconds'])
        except StopUnconfirmed:
            new(work/'ROOT-STOP-UNCONFIRMED.json',encoded({'state':'STOP_UNCONFIRMED','actor_pid':actor.pid,'clock':c['clock'],'parent_stops':stops,'retry_authorized':False}));raise
        finally:
            try:
                if actor is not None and actor.poll() is None and not wait_attempted:wait_attempted=True;code=wait_owned(actor,wait_clock,r['reserve_seconds'])
            finally:
                for n,h in prior.items():signal.signal(n,h)
    ended=dict(exit_code=code,parent_stops=stops,new_clock=c['clock'],wait_clock=wait_clock,actor_reaped=actor.poll()is not None,elapsed_seconds=time.monotonic()-started,semantic_acceptance='NOT_ESTABLISHED')
    phase.exclusive(work/'ROOT-MISSING-FIRST-SEND-ENDED.json',phase.enc(ended))
    return ended
