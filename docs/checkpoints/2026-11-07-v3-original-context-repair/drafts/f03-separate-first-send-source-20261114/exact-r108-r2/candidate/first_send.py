"""F03-only separate missing FIRST send proposal. Import is inert; UNBOUND by default.
This is neither an extension of original300/outer600 nor an R108 reissue.
Only Root can supply a separately accepted decision and current reconciliation.
"""
import datetime as dt
import hashlib,json,math,os,stat,time
from pathlib import Path
RUN='f03-ods-formulas-original-221-20261114'
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
W2=Path('/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-after-json-normalization')
ONCE=W2/'ROOT-MISSING-FIRST-SEND-SEPARATE-PHASE-ONCE.json'
BEFORE=STATE/('first-send-original-before-'+RUN+'.json')
SCENARIO_SHA='98c0c37105804e600a47eed83e6ba7504849333054e409c6af6080ed5496dd4f'
SOURCE_SHA='a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
CREATED=1794676116.984139
DEADLINE=1794676416.9841528
R108_EXPIRY=1794691234.1908894
R108={'path':'/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R108.json','bytes':15001,'sha256':'90baa1afbb9a3d1ec9e46f0970e53e8fd0f2321d2c668cbbd5b1c8baac4ecbe6'}
W4=Path('/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-unsent-user-step-continuation-phase')
PRISTINE={'path':str(W4/'ROOT-PRESERVED-ACTUAL-PRISTINE-RUN.private.json'),'bytes':2839,'sha256':'926d286ef527bf309ec064aa8e6a8e6580b2a39405418b3aec2cae38e310d101'}
CLOSURE={'path':str(W4/'CLOSED-PRISTINE-PREPARED-BEFORE-USER-SEND.json'),'bytes':8128,'sha256':'2d85c967d6730177ac78184a62fb3d5413da9a1fb60b55394a906b18d2ecc837'}
# bytes for these exact source pins are filled by the source builder, never inferred at runtime.
OLD_CLOCK={'bytes': 901, 'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-unsent-user-step-continuation-phase/PHASE-CLOCK.json', 'sha256': '0ed051152f53d7b8193fa8ffd91de7230d4a22cb2a582617c46f59ac6be6ac99'}
LOCKS={'slot': {'device': 2050, 'inode': 9440373}, 'consumer.lock': {'device': 2050, 'inode': 7530843}, 'tester-token': {'device': 2050, 'inode': 7530834}}
MARKERS=[{'bytes': 4130, 'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-after-json-normalization/ROOT-ISSUED-UNSTARTED-CONSUMER-ONCE.json', 'sha256': '92e160b9f88a9bdc52b7b51bb7f7ef46ff0bacd85c83a5e83756ac729c17ee35'}, {'bytes': 4740, 'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-after-json-normalization/ROOT-UNSENT-FIRST-USER-STEP-CONTINUATION-ONCE.json', 'sha256': '3d9f5ee35094d18ef0acf6023be8ecaefaab084bd1949f32cb68f3ba6dda3d1f'}, {'bytes': 615, 'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ordinary-after-json-normalization/ROOT-ONCE-INVOCATION.json', 'sha256': '7873e41d3bb93fe3c2b0bcd75f0be3183d089d9df846fde05bf3a7953d885889'}]
FACTS={'positive_no_send_from_exact_source_pc_and_diagnostic','old_actors_reaped_absent','no_same_effect_unknown','source_ownership_principal_privacy_reviewed','old_clocks_markers_preserved','old_original_expired','Root_holds_shared_slot','consumer_and_credential_locks_held','history_once_cancel_current_reconciled'}
ROLE='SEPARATE_MISSING_FIRST_SEND_AFTER_EXPIRED_POSITIVE_NO_SEND'
META_FIELDS={'contract','once','before'}

def enc(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def require(v,msg):
    if not v:raise ValueError('F03_FIRST_SEND_'+msg)
def unique(pairs):
    d={}
    for k,v in pairs:
        require(k not in d,'DUPLICATE_KEY');d[k]=v
    return d

def read(path,*,limit=24*1024**2):
    p=Path(path);require(p.is_absolute() and str(p)==str(path) and '..' not in p.parts and not any(q.is_symlink() for q in (p,*p.parents)),'CANONICAL_PATH_REQUIRED')
    key=lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    z=p.stat();parent=p.parent.stat()
    require(stat.S_ISREG(z.st_mode) and z.st_uid==os.getuid() and z.st_nlink==1 and stat.S_IMODE(z.st_mode)==0o600 and 0<z.st_size<=limit,'PROTECTED_FILE_CUSTODY')
    legacy=str(p)==R108['path']
    # Sibling entries may change in protected active workdirs. Only the exact
    # historical group-writable R108 parent needs full directory metadata CAS.
    parent_key=key if legacy else lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode)
    if legacy:
        # Historical immutable input under protected .cache; never a grant or
        # a generic parent-mode exception. Exact identity and bytes are required.
        require(key(z)==(2050,8417283,1000,1000,stat.S_IFREG|0o600,1,15001,1794669634207048294,1794669634208048353),'EXACT_LEGACY_R108_FILE_IDENTITY_REQUIRED')
        require((parent.st_dev,parent.st_ino,parent.st_uid,parent.st_gid,parent.st_mode,parent.st_nlink)==(2050,8408484,1000,1000,stat.S_IFDIR|0o775,4),'EXACT_LEGACY_R108_PARENT_REQUIRED')
        ancestors=(('/home/jericho/.cache',2050,7340062,1000,1000,0o700),('/home/jericho',2050,7340034,1000,1000,0o750),('/home',2050,7340033,0,0,0o755),('/',2050,2,0,0,0o755))
        for path_,dev,ino,uid,gid,mode in ancestors:
            a=Path(path_).stat()
            require((a.st_dev,a.st_ino,a.st_uid,a.st_gid,a.st_mode)==(dev,ino,uid,gid,stat.S_IFDIR|mode),'EXACT_LEGACY_R108_ANCESTOR_REQUIRED')
    else:
        require(stat.S_ISDIR(parent.st_mode) and stat.S_IMODE(parent.st_mode)==0o700 and parent.st_uid==os.getuid(),'PROTECTED_PARENT_REQUIRED')
    require(all(stat.S_ISDIR(q.stat().st_mode) and not(q.stat().st_mode&0o002) for q in p.parents if q!=p.parent),'UNSAFE_ANCESTOR')
    # Open the checked parent itself and the leaf relative to it: before/after
    # directory and file CAS authenticate the same objects, including gid.
    dfd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        require(parent_key(parent)==parent_key(os.fstat(dfd)),'PARENT_CAS_CHANGED_BEFORE_READ')
        fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=dfd)
        with os.fdopen(fd,'rb')as f:
            require(key(z)==key(os.fstat(f.fileno())),'FILE_CAS_CHANGED_BEFORE_READ')
            b=f.read(limit+1);after=os.fstat(f.fileno())
        require(len(b)<=limit and key(z)==key(after)==key(p.stat()),'FILE_CAS_CHANGED')
        require(parent_key(parent)==parent_key(os.fstat(dfd))==parent_key(p.parent.stat()),'PARENT_CAS_CHANGED')
        require(not any(q.is_symlink() for q in (p,*p.parents)),'CANONICAL_PATH_CHANGED')
        if legacy:
            require(len(b)==R108['bytes'] and sha(b)==R108['sha256'],'EXACT_LEGACY_R108_BYTES_REQUIRED')
            for path_,dev,ino,uid,gid,mode in ancestors:
                a=Path(path_).stat()
                require((a.st_dev,a.st_ino,a.st_uid,a.st_gid,a.st_mode)==(dev,ino,uid,gid,stat.S_IFDIR|mode),'EXACT_LEGACY_R108_ANCESTOR_CHANGED')
        return b
    finally:os.close(dfd)

def refshape(r):
    return type(r)is dict and set(r)=={'path','bytes','sha256'} and type(r['path'])is str and Path(r['path']).is_absolute() and type(r['bytes'])is int and 0<r['bytes']<=24*1024**2 and type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256'])
def rawref(r):
    require(refshape(r),'EXACT_REF_REQUIRED');b=read(r['path']);require(len(b)==r['bytes'] and sha(b)==r['sha256'],'REF_CHANGED');return b
def doc(r):return json.loads(rawref(r),object_pairs_hook=unique)
def pin(path,b):return dict(path=str(path),bytes=len(b),sha256=sha(b))
def finite(v):return type(v)in(int,float) and math.isfinite(v)

def plan():
    return dict(role=ROLE,run_id=RUN,scenario_sha256=SCENARIO_SHA,source_sha256=SOURCE_SHA,original_created_epoch=CREATED,original_deadline_epoch=DEADLINE,original_pristine=PRISTINE,original_closure=CLOSURE,original_outer_clock=OLD_CLOCK,original_named_locks=LOCKS,consumed_predecessors=MARKERS,R108=R108,R108_expiry_upper_bound=R108_EXPIRY,fixed_once_path=str(ONCE),before_snapshot_path=str(BEFORE),timing=dict(first_send_seconds=300,full_reply_seconds=180,ACK_seconds=30,reserve_seconds=5,outer_seconds_maximum=600),old_clocks_remain_expired_history=True,old_authority_does_not_grant_this_operation=True)
def unbound():
    return dict(schema='frw.Root.F03.separate-missing-first-send.v1',status='UNBOUND_NOT_GRANTED',plan=plan(),implementation=None,consumer=None,decision=None,reconciliation=None,clock=None)

def contract(r,*,preintent=False,active=False):
    c=doc(r);require(type(c)is dict and set(c)==set(unbound()) and c['schema']==unbound()['schema'] and c['plan']==plan(),'EXACT_CASE_PLAN_REQUIRED')
    require(c['status']=='ROOT_BOUND_SEPARATE_MISSING_FIRST_SEND','UNBOUND_NO_GRANT')
    require(c['implementation']==pin(Path(__file__),read(Path(__file__))) and refshape(c['consumer']),'EXACT_REVIEWED_IMPLEMENTATION_REQUIRED');rawref(c['consumer'])
    psha=sha(enc(c['plan']));d=doc(c['decision']);f=doc(c['reconciliation']);k=doc(c['clock'])
    require(d.get('schema')=='frw.Root.F03.separate-first-send-decision.v1' and d.get('operator')=='Root' and d.get('status')=='ROOT_ACCEPTED_SEPARATE_MISSING_FIRST_SEND' and d.get('execution_grant')is True and d.get('authorization_basis')in('ROOT_STANDING_AUTHORIZATION_APPLIES','EXPLICIT_OWNER_APPROVAL') and d.get('plan_sha256')==psha and d.get('binding_sha256')==sha(enc({q:v for q,v in c.items() if q!='decision'})) and d.get('clock')==c['clock'] and d.get('reconciliation')==c['reconciliation'] and d.get('old_clocks_not_extended')is True and d.get('R108_is_only_additional_bound_not_grant')is True,'EXPLICIT_SEPARATE_ROOT_DECISION_REQUIRED')
    require(f.get('schema')=='frw.Root.F03.separate-first-send-reconciliation.v1' and f.get('operator')=='Root' and f.get('plan_sha256')==psha and f.get('original_pristine')==PRISTINE and type(f.get('facts'))is dict and set(f['facts'])==FACTS and all(v is True for v in f['facts'].values()) and type(f.get('evidence'))is list and f['evidence'],'EXPLICIT_POSITIVE_RECONCILIATION_REQUIRED')
    for x in f['evidence']:rawref(x)
    for x in [PRISTINE,CLOSURE,OLD_CLOCK,R108,*MARKERS]:rawref(x)
    old=doc(OLD_CLOCK);authority=doc(R108)
    require(authority.get('expires_at')==R108_EXPIRY and old.get('deadline_wall')<k.get('origin_wall',0),'EXPIRED_ORIGINAL_AND_UNCHANGED_R108_REQUIRED')
    require(k.get('schema')=='frw.Root.F03.distinct-first-send-clock.v1' and k.get('role')==ROLE and k.get('run_id')==RUN and k.get('plan_sha256')==psha,'DISTINCT_CLOCK_REQUIRED')
    for q in ('origin_wall','origin_monotonic','first_send_deadline_wall','first_send_deadline_monotonic','outer_deadline_wall','outer_deadline_monotonic'):require(finite(k.get(q)),'FINITE_CLOCK_REQUIRED')
    require(k['first_send_deadline_wall']==k['origin_wall']+300 and k['first_send_deadline_monotonic']==k['origin_monotonic']+300 and 300<=k['outer_deadline_wall']-k['origin_wall']<=600 and k['outer_deadline_wall']-k['origin_wall']==k['outer_deadline_monotonic']-k['origin_monotonic'] and k['first_send_deadline_wall']<=k['outer_deadline_wall']<=R108_EXPIRY,'FINITE_DISTINCT_CLOCK_BOUNDS')
    wall=time.time() if active or preintent else k['origin_wall'];mono=time.monotonic() if active or preintent else k['origin_monotonic'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip() if active or preintent else k.get('boot_id')
    require(k.get('boot_id')==boot and k['origin_wall']<=wall<k['first_send_deadline_wall'] and k['origin_monotonic']<=mono<k['first_send_deadline_monotonic'] and abs((wall-k['origin_wall'])-(mono-k['origin_monotonic']))<=2 and wall<R108_EXPIRY,'EXPIRED_FUTURE_OR_CHANGED_PHASE_CLOCK')
    require(d.get('expires_at')==k['first_send_deadline_wall'],'DECISION_CLOCK_BOUND_REQUIRED')
    if preintent:
        require(finite(f.get('created_at')) and finite(f.get('created_monotonic')) and f['created_at']<=wall<=f['created_at']+120 and f['created_monotonic']<=mono<=f['created_monotonic']+120 and f.get('boot_id')==boot and abs((wall-f['created_at'])-(mono-f['created_monotonic']))<=2,'FRESH_RECONCILIATION_REQUIRED')
        require(min(k['first_send_deadline_wall']-wall,k['first_send_deadline_monotonic']-mono)>=215,'FULL_ACK_REPLY_RESERVE_DOES_NOT_FIT')
    return c,k

def validate(meta,row,root,*,preintent=False,active=False):
    require(Path(root)==STATE,'FIXED_ORIGINAL_STATE_REQUIRED');require(type(meta)is dict and set(meta)==META_FIELDS,'DURABLE_PHASE_META_REQUIRED')
    c,k=contract(meta['contract'],preintent=preintent,active=active)
    require(meta['once']['path']==str(ONCE) and meta['before']['path']==str(BEFORE),'FIXED_ONCE_AND_BEFORE_REQUIRED')
    b=rawref(meta['before']);require(b==rawref(PRISTINE),'ORIGINAL_BEFORE_CHANGED')
    m=doc(meta['once']);require(m==dict(schema='frw.Root.F03.separate-first-send-consumed.v1',status='CONSUMED_ON_ENTRY_NO_RETRY',run_id=RUN,contract=meta['contract'],before=meta['before'],predecessors=MARKERS,closure=CLOSURE),'CONSUMED_MARKER_BINDING_CHANGED')
    original=json.loads(b,object_pairs_hook=unique)
    require(row.get('id')==RUN and row.get('scenario')==original['scenario'] and row.get('scenario_sha256')==SCENARIO_SHA and row.get('created_at')==original['created_at'] and row.get('deadline')==DEADLINE and dt.datetime.fromisoformat(row['created_at']).timestamp()==CREATED and row.get('first_send_phase')==meta and 'continuation_reference'not in row and 'new_ack_timeout_seconds'not in row,'IMMUTABLE_ORIGINAL_IDENTITY_CLOCK_CHANGED')
    if preintent:
        require(set(row)==set(original)|{'first_send_phase'} and {a:v for a,v in row.items()if a!='first_send_phase'}==original,'EXACT_PRISTINE_ONLY')
        require(not any(STATE.glob('send-task-'+RUN+'-*')) and not any(STATE.glob('send-ack-'+RUN+'-*')) and not any(STATE.glob('send-window-'+RUN+'-*')) and not any(STATE.glob('receive-'+RUN+'-*')),'SEND_OR_CAPTURE_WITNESS_EXISTS')
    return c,k

def preclock_projection(private_workdir):
    """Read-only proof preparation before any operative clock/decision exists."""
    return dict(schema='frw.Root.F03.first-send-preclock-projection.v1',status='UNBOUND_PREPARATION_ONLY',plan_sha256=sha(enc(plan())),original_pristine=PRISTINE,private_workdir=str(private_workdir))
def is_preclock(meta):
    return type(meta)is dict and set(meta)=={'schema','status','plan_sha256','original_pristine','private_workdir'} and meta.get('schema')=='frw.Root.F03.first-send-preclock-projection.v1'
def validate_preclock_projection(meta,row,root):
    require(Path(root)==STATE and is_preclock(meta) and meta==preclock_projection(meta['private_workdir']),'UNBOUND_PRECLOCK_PROJECTION_ONLY')
    work=Path(meta['private_workdir'])
    require(work.is_absolute() and str(work)==meta['private_workdir'] and '..'not in work.parts and not any(q.is_symlink()for q in(work,*work.parents)) and work.is_dir() and work.stat().st_uid==os.getuid() and stat.S_IMODE(work.stat().st_mode)==0o700,'PRECLOCK_PRIVATE_WORKDIR_REQUIRED')
    for ref in (PRISTINE,CLOSURE,OLD_CLOCK,*MARKERS):rawref(ref)
    raw=rawref(PRISTINE)
    require(enc(row)==raw and read(STATE/'runs'/(RUN+'.json'))==raw and time.time()>DEADLINE,'PRECLOCK_EXACT_EXPIRED_PRISTINE_REQUIRED')
    require(not ONCE.exists()and not ONCE.is_symlink()and not BEFORE.exists()and not BEFORE.is_symlink(),'PRECLOCK_ALREADY_CLAIMED')
    for prefix in ('send-task-','send-ack-','send-window-','receive-'):
        require(not any(STATE.glob(prefix+RUN+'-*')),'PRECLOCK_SEND_OR_CAPTURE_WITNESS_EXISTS')
    return True

def validate_preclaim(meta,row,root):
    """Read-only Root proof preparation; never admission, claim or dispatch."""
    require(Path(root)==STATE and type(meta)is dict and set(meta)==META_FIELDS,'FIXED_PRECLAIM_CONTEXT_REQUIRED')
    contract(meta['contract'],preintent=True,active=True)
    raw=rawref(PRISTINE)
    require(enc(row)==raw and read(STATE/'runs'/(RUN+'.json'))==raw,'PRECLAIM_EXACT_PRISTINE_REQUIRED')
    before=pin(BEFORE,raw)
    marker=enc(dict(schema='frw.Root.F03.separate-first-send-consumed.v1',status='CONSUMED_ON_ENTRY_NO_RETRY',run_id=RUN,contract=meta['contract'],before=before,predecessors=MARKERS,closure=CLOSURE))
    require(meta['before']==before and meta['once']==pin(ONCE,marker),'PRECLAIM_EXACT_PROJECTED_REFS_REQUIRED')
    require(not ONCE.exists() and not ONCE.is_symlink() and not BEFORE.exists() and not BEFORE.is_symlink(),'PRECLAIM_KEY_OR_SNAPSHOT_ALREADY_EXISTS')
    for prefix in ('send-task-','send-ack-','send-window-','receive-'):
        require(not any(STATE.glob(prefix+RUN+'-*')),'PRECLAIM_SEND_OR_CAPTURE_WITNESS_EXISTS')
    return True

def remaining(meta,row,root):
    _,k=validate(meta,row,root,active=True);return min(k['first_send_deadline_wall']-time.time(),k['first_send_deadline_monotonic']-time.monotonic())

def effective_deadline(runner,row):
    if 'first_send_phase'not in row:return row['deadline']
    _,k=validate(row['first_send_phase'],row,runner.store.root)
    return k['first_send_deadline_wall']

def exclusive(path,b):
    p=Path(path);require(not any(q.is_symlink()for q in(p,*p.parents)) and p.parent.stat().st_uid==os.getuid() and stat.S_IMODE(p.parent.stat().st_mode)==0o700,'EXCLUSIVE_PARENT_CUSTODY')
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    return pin(p,b)

def entry(runner,r,consumer_fd,credential_fd):
    """Explicit one-shot case API. Caller holds all existing locks/outer lifecycle.
    No Runner.new, generic prepared resume, rewritten original clock or retry.
    """
    c,k=contract(r,preintent=True);require(runner.store.root==STATE,'FIXED_ORIGINAL_STATE_REQUIRED')
    require(c['consumer']==pin(Path(runner.__class__.prepared_first_send.__code__.co_filename),read(Path(runner.__class__.prepared_first_send.__code__.co_filename))),'FULL_CONSUMER_SOURCE_CHANGED')
    import fcntl
    for name,fd in [('consumer.lock',consumer_fd),('tester-token',credential_fd)]:
        require(type(fd)is int,'BOTH_NAMED_LOCKS_REQUIRED');p=STATE/name;z=p.stat();fz=os.fstat(fd)
        require((z.st_dev,z.st_ino,z.st_uid,z.st_mode,z.st_nlink)==(fz.st_dev,fz.st_ino,fz.st_uid,fz.st_mode,fz.st_nlink) and z.st_uid==os.getuid() and z.st_nlink==1 and stat.S_IMODE(z.st_mode)==0o600 and not any(q.is_symlink()for q in(p,*p.parents)),'NAMED_LOCK_IDENTITY_CHANGED')
        require((z.st_dev,z.st_ino)==(LOCKS[name]['device'],LOCKS[name]['inode']),'ORIGINAL_NAMED_LOCK_CHANGED')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    raw=read(runner.store.run_path(RUN));require(raw==rawref(PRISTINE),'EXACT_POSITIVE_PRISTINE_ROW_CHANGED')
    row=json.loads(raw,object_pairs_hook=unique);require(row.get('send_state')=='none' and row.get('status')=='PREPARED' and row.get('send_attempts')==0,'MISSING_FIRST_SEND_ONLY')
    # O_EXCL first: a crash/partial marker consumes this proposed effect forever.
    before=pin(BEFORE,raw)
    once=exclusive(ONCE,enc(dict(schema='frw.Root.F03.separate-first-send-consumed.v1',status='CONSUMED_ON_ENTRY_NO_RETRY',run_id=RUN,contract=r,before=before,predecessors=MARKERS,closure=CLOSURE)))
    exclusive(BEFORE,raw)
    meta=dict(contract=r,once=once,before=before);row['first_send_phase']=meta
    validate(meta,row,runner.store.root,preintent=True)
    runner.save(row)
    runner._f03_first_send_entry=meta
    try:return runner.send(row,resume_prepared=False,consumer_fd=consumer_fd,credential_fd=credential_fd)
    finally:del runner._f03_first_send_entry
