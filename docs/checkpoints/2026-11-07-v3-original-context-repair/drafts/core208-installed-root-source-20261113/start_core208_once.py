"""Inert on import. Root-only one-shot R2 launcher; never retry/rename consumed work."""
import datetime,hashlib,json,os,pathlib,signal,stat,subprocess,sys,time
B=pathlib.Path(__file__).parent
F=B
R=pathlib.Path('/home/jericho/jericho/Friday_rework')
E=B/'FUTURE-EXECUTION'
def require(value,reason):
    if not value:raise RuntimeError(reason)
def ref(path):
    path=pathlib.Path(path);s=path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and not any(p.is_symlink() for p in (path,*path.parents)), 'owned_regular_source_required')
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def load(path):return json.loads(pathlib.Path(path).read_bytes())
def birth(pid):return int((pathlib.Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19])
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
def create(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
def wait_same(child):
    while True:
        try:return child.wait()
        except (InterruptedError,KeyboardInterrupt):continue

def main():
    require(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv)==4 and
            sys.argv[1:3]==['--execute-once-root-reviewed-208','--source-pins-sha256'], 'explicit_isolated_Root_R2_launcher_required')
    os.umask(0o077);os.environ.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',
        HERMES_HOME=str(R/'.runtime/friday-normal-both-workers-frw032'),HERMES_GATEWAY_LOCK_DIR='/home/jericho/.local/state/hermes/gateway-locks')
    require(ref(B/'SOURCE-PINS.json')['sha256']==sys.argv[3], 'externally_reviewed_manifest_sha_required')
    pins=load(B/'SOURCE-PINS.json')
    require(pins['frame']==str(F) and pins['schema']=='frw.root208.coherent-after-actual207-source-pins.v1','exact_R2_source_manifest_required')
    for path,digest in {**pins['source_refs'],**pins['historical_refs']}.items():require(ref(path)['sha256']==digest,'source_pin_changed:'+path)
    accepted=load(B/'ROOT-208-SOURCE-ACCEPTANCE.json')
    require(accepted['accepted']is True and accepted['execution_grant']is False and accepted['template_only_no_execution_grant']is False and accepted['frame_source_manifest']==ref(B/'SOURCE-PINS.json') and accepted['frame_review_evidence'],'authentic_new_Root208_source_acceptance_required')
    for review in accepted['frame_review_evidence']:require(ref(review['path'])==review,'exact_frame_review_changed')
    authority=load(B/'ROOT-208-RUNTIME-AUTHORITY.json')
    require(authority['template_only_no_execution_grant']is False and authority['source_acceptance']==ref(B/'ROOT-208-SOURCE-ACCEPTANCE.json') and authority['current_service_anchor']==ref(B/'ROOT-208-CURRENT-SERVICE-ANCHOR.json') and authority['caller']==ref(pathlib.Path(__file__)),'authentic_Root208_authority_required')
    # mkdir is the launch claim; no cleanup/reset or resume of this launcher exists.
    E.mkdir(mode=0o700)
    python=load(F/'ROOT-FUTURE-COMMANDS.json')['commands']['once_actor'][0]
    argv=[python,'-I','-B',str(B/'core208-first-actual-root.py'),'--execute-once-root-reviewed-208-boundary','--source-pins-sha256',sys.argv[3]]
    create(E/'INTENT.json',dict(at_moscow=now(),source_pin_manifest=ref(B/'SOURCE-PINS.json'),
        authority=ref(B/'ROOT-208-RUNTIME-AUTHORITY.json'),current_anchor=ref(B/'ROOT-208-CURRENT-SERVICE-ANCHOR.json'),
        argv=argv,parent_pid=os.getpid(),parent_birth_ticks=birth(os.getpid()),
        scope='Genuine committed207to208 future source-install boundary; no user/model/Office replay',
        old_consumed_launch_not_replayed=True,no_original_clock_reset=True))
    child=None;pending=[];started=time.monotonic()
    previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def defer(signum,_frame):pending.append(signum)
    for sig in previous:signal.signal(sig,defer)
    try:
        with os.fdopen(os.open(E/'boundary.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as out,os.fdopen(os.open(E/'boundary.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as err:
            require(not pending,'parent_stop_before_boundary_launch')
            child=subprocess.Popen(argv,cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
            try:create(E/'LAUNCH.json',dict(at_moscow=now(),pid=child.pid,parent_pid=os.getpid(),birth_ticks=birth(child.pid)))
            finally:code=wait_same(child)
        create(E/'RETURN.json',dict(at_moscow=now(),returncode=code,boundary_pid=child.pid,
            boundary_pid_absent=not pathlib.Path('/proc',str(child.pid)).exists(),
            elapsed_seconds=time.monotonic()-started,deferred_parent_signals=pending,no_retry=True,
            state='RETURN_RECONCILE_ACTUAL_RESULT_NOT_INSTALL_ACCEPTANCE'))
        print(json.dumps(dict(returncode=code,private_evidence=str(E),state='RETURN_RECONCILE_ACTUAL')))
        require(not pending,'parent_stop_deferred_until_same_boundary_return')
    finally:
        if child is not None and child.returncode is None:wait_same(child)
        for sig,handler in previous.items():signal.signal(sig,handler)

if __name__=='__main__':main()
