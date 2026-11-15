import gdb, os, json, hashlib, time
from pathlib import Path

OUT = Path('/tmp/friday-metric-work/trace.json')
CODE = Path('/home/jericho/.cache/FRW-ASTRA-PAPER-HELPER-NONOFFICE-TOPOLOGY-20261115/code')
EXPECTED = {
    'fixture': hashlib.sha256((CODE / 'fixture').read_bytes()).hexdigest(),
    'dash': 'c626229526bb58ec2d0f585f3c3ae1412e6f973b4353385042d11c38d8426917',
    'paperconf': 'cce22660a60a113e52288cb55ea04cd0ee96ec1f1a19ba08aa120dd118608103',
}
STATE = {'schema':'frw.own-popen-gdb-topology.v1', 'events':[], 'known':{},
         'inferior_history':{}, 'error':None, 'actual_M':None, 'gdb_pid':os.getpid(),
         'schedule_multiple_off_resume_tested':False}
CP = {}

def save():
    data = json.dumps(STATE, sort_keys=True).encode() + b'\n'
    if len(data) > 512*1024: raise RuntimeError('trace_bound')
    OUT.write_bytes(data)
    OUT.chmod(0o600)

def event(kind, **details):
    STATE['events'].append({'event_id':len(STATE['events'])+1,
                            'kind':kind, 'monotonic':time.monotonic(), **details})
    if len(STATE['events']) > 128: raise RuntimeError('event_bound')

def identity(pid):
    p = Path('/proc') / str(pid)
    raw = (p/'stat').read_text()
    if len(raw) > 4096: raise RuntimeError('stat_bound')
    f = raw.rsplit(')',1)[1].split()
    birth = int(f[19]); ppid = int(f[1])
    previous = STATE['known'].get(str(pid))
    if previous is not None and previous['start_ticks'] != birth:
        raise RuntimeError('pid_reuse')
    if previous is None and ppid != os.getpid() and str(ppid) not in STATE['known']:
        raise RuntimeError('not_own_descendant')
    exe = os.readlink(p/'exe')
    with (p/'exe').open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    roles = [role for role,h in EXPECTED.items() if h == digest]
    if len(roles) != 1: raise RuntimeError('unexpected_own_executable')
    role = roles[0]
    argv = (p/'cmdline').read_bytes()
    if len(argv)>4096: raise RuntimeError('argv_bound')
    args = argv.rstrip(b'\0').split(b'\0')
    if role == 'fixture':
        argvclass = 'exact_own_fixture' if args == [str(CODE/'fixture').encode()] else 'unexpected'
    elif role == 'dash':
        argvclass = 'exact_stock_popen_shell' if args == [b'sh',b'-c',b'--',b'paperconf 2>/dev/null'] else 'unexpected'
    else:
        argvclass = 'exact_stock_paperconf_no_arguments' if args in ([b'paperconf'],[b'/usr/bin/paperconf'],[b'/bin/paperconf']) else 'unexpected'
    if argvclass == 'unexpected': raise RuntimeError('unexpected_argv')
    maps=(p/'maps').read_text()
    if len(maps)>256*1024:raise RuntimeError('own_maps_bound')
    libraries={}
    for line in maps.splitlines():
        entry=line.split(None,5)
        if len(entry)==6 and Path(entry[5]).name in ('libc.so.6','ld-linux-x86-64.so.2'):
            path=entry[5]
            if path not in libraries:
                with open(path,'rb') as file:libraries[path]=hashlib.file_digest(file,'sha256').hexdigest()
    v = {'pid':pid, 'ppid':ppid, 'start_ticks':birth, 'state':f[0], 'exe':exe,
         'exe_sha256':digest, 'role':role, 'argv_class':argvclass,
         'argv_sha256':hashlib.sha256(argv).hexdigest(),'loaded_libc_loader_sha256':libraries}
    if previous is None:
        STATE['known'][str(pid)] = {'pid':pid,'initial_ppid':ppid,'start_ticks':birth,'history':[]}
    hist = STATE['known'][str(pid)]['history']
    if not hist or hist[-1]['role'] != role: hist.append(v)
    return v

def snapshot():
    result = []
    for inf in gdb.inferiors():
        if inf.pid:
            v=identity(inf.pid)
            result.append({'inferior':inf.num, **v})
            STATE['inferior_history'].setdefault(str(inf.num),[])
            item={'pid':inf.pid,'role':v['role'],'start_ticks':v['start_ticks']}
            h=STATE['inferior_history'][str(inf.num)]
            if not h or h[-1]!=item:h.append(item)
    for known in list(STATE['known'].values()):
        childfile = Path('/proc')/str(known['pid'])/'task'/str(known['pid'])/'children'
        try: children=childfile.read_text()
        except FileNotFoundError: continue
        if len(children)>256:raise RuntimeError('children_bound')
        nums=children.split()
        if len(nums)>8 or not all(n.isdecimal() for n in nums):raise RuntimeError('children_invalid')
        for n in nums:identity(int(n))
    return result

def selected():
    inf=gdb.selected_inferior(); thread=gdb.selected_thread()
    return {'inferior':inf.num,'pid':inf.pid,
            'thread_ptid':list(thread.ptid) if thread is not None and thread.is_valid() else None}

def stopped(e):
    if isinstance(e,gdb.SignalEvent):
        event('signal_stop', signal=e.stop_signal, selected=selected(), inferiors=snapshot())
        STATE['error']='unexpected_signal'
    else:
        bps=[{'number':b.number,'catch_kind':CP.get(b.number,'other')} for b in getattr(e,'breakpoints',())]
        frames=[]
        f=gdb.newest_frame()
        for _ in range(16):
            if f is None or not f.is_valid():break
            frames.append({'symbol':f.name(), 'module_basename':Path(gdb.solib_name(f.pc())).name if gdb.solib_name(f.pc()) else None})
            f=f.older()
        event('stop',selected=selected(),breakpoints=bps,inferiors=snapshot(),symbolic_frames=frames)
    save()

def exited(e):
    event('exited',inferior=e.inferior.num if hasattr(e,'inferior') else None,
          exit_code=getattr(e,'exit_code',None),selected=selected())
    save()

def safe_stopped(e):
    try:stopped(e)
    except BaseException as failure:
        STATE['error']='stop_callback:'+type(failure).__name__+':'+str(failure)[:200]
        event('callback_failure',exception=STATE['error'])
        save()

def safe_exited(e):
    try:exited(e)
    except BaseException as failure:
        STATE['error']='exit_callback:'+type(failure).__name__+':'+str(failure)[:200]
        save()

for command in ('set pagination off','set confirm off','set startup-with-shell off',
                'set debuginfod enabled off','set auto-load off','set disable-randomization off',
                'set follow-fork-mode parent','set detach-on-fork off',
                'handle SIGCHLD nostop noprint pass'):
    gdb.execute(command,to_string=True)
STATE['schedule_multiple_initial']=gdb.execute('show schedule-multiple',to_string=True).strip()
gdb.execute('set schedule-multiple on',to_string=True)
STATE['settings']={k:gdb.execute('show '+k,to_string=True).strip() for k in
                   ('follow-fork-mode','detach-on-fork','schedule-multiple','startup-with-shell','auto-load','debuginfod enabled')}
try:
    gdb.execute('start',to_string=True)
    gdb.execute('set scheduler-locking off',to_string=True)
    STATE['settings']['scheduler-locking']=gdb.execute('show scheduler-locking',to_string=True).strip()
    event('main_boundary',selected=selected(),inferiors=snapshot())
    gdb.events.stop.connect(safe_stopped);gdb.events.exited.connect(safe_exited)
    for kind in ('fork','vfork','exec'):
        before=set(b.number for b in gdb.breakpoints())
        gdb.execute('catch '+kind,to_string=True)
        for b in gdb.breakpoints():
            if b.number not in before:CP[b.number]=kind
    for number in range(32):
        active=[i for i in gdb.inferiors() if i.pid]
        if not active:break
        if STATE['error'] is not None:raise RuntimeError(STATE['error'])
        if not gdb.selected_inferior().pid:
            gdb.execute('inferior '+str(active[0].num),to_string=True)
        event('continue_request',iteration=number+1,selected=selected(),inferiors=snapshot())
        output=gdb.execute('continue',to_string=True)
        event('continue_return',iteration=number+1,gdb_text=output[:4096],selected=selected())
    else:raise RuntimeError('stop_limit')
    STATE['all_inferiors_terminal']=all(i.pid==0 for i in gdb.inferiors())
    STATE['status']='TERMINAL' if STATE['all_inferiors_terminal'] else 'FAILED'
except BaseException as e:
    STATE['error']=STATE['error'] or type(e).__name__+':'+str(e)[:200]
    STATE['status']='FAILED'
finally:
    try:gdb.events.stop.disconnect(safe_stopped)
    except Exception:pass
    try:gdb.events.exited.disconnect(safe_exited)
    except Exception:pass
    STATE['cleanup_killed_inferiors']=[]
    for i in gdb.inferiors():
        if i.pid:
            STATE['cleanup_killed_inferiors'].append({'inferior':i.num,'pid':i.pid})
            try:
                gdb.execute('inferior '+str(i.num),to_string=True)
                gdb.execute('kill',to_string=True)
            except Exception as e:event('cleanup_error',exception=type(e).__name__)
    STATE['all_gdb_inferiors_pid0_after_cleanup']=all(i.pid==0 for i in gdb.inferiors())
    save()
