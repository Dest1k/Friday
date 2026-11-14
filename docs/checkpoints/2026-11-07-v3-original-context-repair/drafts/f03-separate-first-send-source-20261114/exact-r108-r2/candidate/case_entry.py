"""F03-only consumer child entry for one distinct bounded missing first send.
Import is inert. Root supplies a separately accepted protected supplement.
"""
import ast,hashlib,json,os,resource,stat,sys,types
from pathlib import Path
RUN='f03-ods-formulas-original-221-20261114'
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
PINS = {'first_send.py': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/first_send.py', 'bytes': 19459, 'sha256': '52d48a7cfc6162c137569728ec024e6d2633a0d7901ef92071b47cd764af63d7'}, 'bind_source.py': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/bind_source.py', 'bytes': 1805, 'sha256': '1aff00c021fafadf6eb7e6ceb2bc5767d3ee7e34307abe20158c77e1e6149415'}, 'bot_tester.f03.first-send.py': {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/bot_tester.f03.first-send.py', 'bytes': 1144445, 'sha256': '80f2b31bec7b97f4f27951c8240a75b90222b03a26472390138a46e8e1e10561'}}

def readref(r):
    if type(r)is not dict or set(r)!={'path','bytes','sha256'}:raise ValueError('F03_CHILD_EXACT_REF_REQUIRED')
    p=Path(r['path'])
    if not p.is_absolute() or str(p)!=r['path'] or '..'in p.parts or any(q.is_symlink()for q in(p,*p.parents)):raise ValueError('F03_CHILD_CANONICAL_PATH_REQUIRED')
    z=p.stat()
    if not stat.S_ISREG(z.st_mode)or z.st_uid!=os.getuid()or z.st_nlink!=1 or stat.S_IMODE(z.st_mode)!=0o600 or stat.S_IMODE(p.parent.stat().st_mode)!=0o700 or not 0<z.st_size<=24*1024**2:raise ValueError('F03_CHILD_SOURCE_CUSTODY_CHANGED')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb')as f:
        opened=os.fstat(f.fileno())
        if (z.st_dev,z.st_ino,z.st_mode,z.st_size,z.st_mtime_ns,z.st_ctime_ns)!=(opened.st_dev,opened.st_ino,opened.st_mode,opened.st_size,opened.st_mtime_ns,opened.st_ctime_ns):raise ValueError('F03_CHILD_SOURCE_CAS_BEFORE_READ')
        b=f.read(24*1024**2+1);fz=os.fstat(f.fileno())
    ident=lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if ident(z)!=ident(fz)or ident(z)!=ident(p.stat())or len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('F03_CHILD_SOURCE_PIN_CHANGED')
    return b

def load(r,name):
    raw=readref(r);m=types.ModuleType(name);m.__file__=r['path'];exec(compile(raw,m.__file__,'exec'),m.__dict__);return m

def boundary(contract_reference):
    phase=load(PINS['first_send.py'],'_F03_distinct_first_send')
    c,k=phase.contract(contract_reference,preintent=True,active=True)
    d=phase.doc(c['decision'])
    if d.get('case_entry_source')!=phase.pin(Path(__file__),phase.read(Path(__file__))):raise ValueError('F03_CHILD_ENTRY_SOURCE_NOT_SEPARATELY_BOUND')
    raw=phase.rawref(c['consumer']);t=ast.parse(raw)
    bindings=[n for n in t.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=='F03_CONTRACT'for v in n.targets)]
    if len(bindings)!=1:raise ValueError('F03_CHILD_SINGLE_BOUND_CONSUMER_REQUIRED')
    original=ast.literal_eval(bindings[0].value)
    binder=load(PINS['bind_source.py'],'_F03_pure_binder')
    if binder.bind_source(readref(PINS['bot_tester.f03.first-send.py']),original)!=raw:raise ValueError('F03_CHILD_FULL_BOUND_SOURCE_DRIFT')
    full=load(c['consumer'],'_F03_full_bound_consumer')
    if original.get('resources',{}).get('clock')!=phase.OLD_CLOCK:raise ValueError('F03_CHILD_OLD_CLOCK_REFERENCE_CHANGED')
    return phase,c,k,full

def slot_identity(fd,phase):
    if type(fd)is not int:raise ValueError('F03_CHILD_EXISTING_SLOT_FD_REQUIRED')
    z=SLOT.stat();fz=os.fstat(fd)
    if any(p.is_symlink()for p in(SLOT,*SLOT.parents))or (z.st_dev,z.st_ino,z.st_uid,z.st_mode,z.st_nlink)!=(fz.st_dev,fz.st_ino,fz.st_uid,fz.st_mode,fz.st_nlink)or z.st_uid!=os.getuid()or stat.S_IMODE(z.st_mode)!=0o600 or z.st_nlink!=1:raise ValueError('F03_CHILD_SLOT_IDENTITY_CHANGED')
    expected=phase.LOCKS['slot']
    if (z.st_dev,z.st_ino)!=(expected['device'],expected['inode']):raise ValueError('F03_CHILD_ORIGINAL_SLOT_CHANGED')

def run_case(runner,contract_reference,consumer_fd,credential_fd):
    runner._f03_case_stage='FIRST_SEND'
    runner.prepared_first_send(contract_reference,consumer_fd,credential_fd)
    runner._f03_case_stage='LOAD_AFTER_SEND'
    run=runner.load(RUN)
    runner._f03_case_stage='OBSERVE'
    runner.observe(run)
    return dict(run_id=run['id'],status=run['status'],acceptance='NOT_ESTABLISHED',artifact_acceptance=run.get('artifact_acceptance','NOT_ESTABLISHED'))

def runtime_caps():
    for key,value in ((resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,536870912),(resource.RLIMIT_FSIZE,67108864)):
        if resource.getrlimit(key)!=(value,value):raise ValueError('F03_CHILD_EXACT_INHERITED_LIMITS_REQUIRED')
    if not 0<len(os.sched_getaffinity(0))<=2:raise ValueError('F03_CHILD_BOUNDED_INHERITED_AFFINITY_REQUIRED')

def keep_refusal(phase,c,full,contract_reference,runner,exc):
    """One protected operation record: only fixed correlation/class/source PC.
    Never serialize str(exc), args, locals, user values or document/private body.
    Preserve the first record and all historical per-run diagnostics unchanged.
    """
    decision=phase.doc(c['decision'])
    sources={'entry':decision['case_entry_source'],'phase':c['implementation'],
             'consumer':c['consumer'],'adapter':full.F03_CONTRACT['adapter'],
             'current':full.F03_CONTRACT['current_gate'],'binder':PINS['bind_source.py']}
    paths={r['path']:name for name,r in sources.items()}
    classes={'Refused','RateLimited','Uncertain','ReplyWindowClosed','ValueError','TypeError','KeyError','OSError','FileNotFoundError','PermissionError','FileExistsError','TimeoutError','RuntimeError','AssertionError'}
    chain=[];seen=set();cursor=exc
    for _ in range(8):
        if cursor is None or id(cursor)in seen:break
        seen.add(id(cursor));frames=[];tb=cursor.__traceback__
        for _ in range(128):
            if tb is None:break
            code=tb.tb_frame.f_code;role=paths.get(code.co_filename)
            if role is not None and code.co_name.isidentifier()and len(code.co_name)<=80:
                frames.append(dict(source=role,function=code.co_name,line=tb.tb_lineno))
                frames=frames[-8:]
            tb=tb.tb_next
        label=type(cursor).__name__;chain.append(dict(exception_class=label if label in classes else 'EXCEPTION',frames=frames))
        cursor=cursor.__cause__ if cursor.__cause__ is not None else cursor.__context__
    stages={'FIRST_SEND','LOAD_AFTER_SEND','OBSERVE'}
    stage=getattr(runner,'_f03_case_stage',None)if runner is not None else None
    phases={'SEND_ADMISSION','SEND_CLAIM','CURSOR_AUTHORITY','SCENARIO_VALIDATION','PRE_REQUEST_GUARD','INPUT_CUSTODY','GET_PREFLIGHT','METADATA_PREPARATION','PRE_INTENT_REVALIDATION','SEND_INTENT_DURABILITY','SEND_API_CALL'}
    send_phase=getattr(runner,'_send_phase',None)if runner is not None else None
    report=dict(schema='frw.Root.F03.separate-first-send-refusal.v1',role=phase.ROLE,run_id=RUN,contract=contract_reference,new_clock=c['clock'],stage=stage if stage in stages else 'LOCKS_OR_RUNNER_SETUP',send_phase=send_phase if send_phase in phases else 'NOT_IN_SENDER',sources=sources,exception_chain=chain,execution_grant=False,diagnostic_only=True)
    raw=phase.enc(report)
    if len(raw)>65536:raise ValueError('F03_REFUSAL_DIAGNOSTIC_BOUND_EXCEEDED')
    phase.exclusive(Path(c['consumer']['path']).parent/'ROOT-MISSING-FIRST-SEND-CHILD-REFUSAL.json',raw)

def run_bound(contract_reference,slot_fd):
    phase,c,k,full=boundary(contract_reference);slot_identity(slot_fd,phase);runtime_caps()
    store=full.Store(phase.STATE);runner=None
    try:
        with store.lock(store.root/'consumer.lock',create=False)as consumer_fd,store.lock(store.root/'tester-token',create=False)as credential_fd:
            token=full.safe_read(store.root/'tester-token',256).decode('ascii').strip()
            runner=full.Runner(store,full.BotAPI(token),clock=full.time.time)
            return run_case(runner,contract_reference,consumer_fd,credential_fd)
    except Exception as exc:
        try:keep_refusal(phase,c,full,contract_reference,runner,exc)
        except Exception:pass # Diagnostic failure never masks the original failure.
        raise

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--bytes',type=int,required=True);p.add_argument('--sha256',required=True);p.add_argument('--slot-fd',type=int,required=True)
    a=p.parse_args(argv);os.umask(0o077)
    try:
        result=run_bound(dict(path=a.contract,bytes=a.bytes,sha256=a.sha256),a.slot_fd)
        print(json.dumps(result,sort_keys=True));return 0
    except Exception:
        print('{"status":"F03_SEPARATE_FIRST_SEND_REFUSED","acceptance":"NOT_ESTABLISHED"}',file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
