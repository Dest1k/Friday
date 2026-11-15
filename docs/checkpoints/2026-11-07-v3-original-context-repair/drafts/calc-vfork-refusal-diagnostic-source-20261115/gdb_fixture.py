import gdb,os,json,ast
from pathlib import Path
ROOT=Path('/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/vfork-diagnostic-real-fixture-r2')
STATE={'process':None,'error':None,'status':'UNRELEASED','records':[],'actual_M':None}
def save():
 (ROOT/'trace.json').write_text(json.dumps(STATE,sort_keys=True)+'\n');os.chmod(ROOT/'trace.json',0o600)
def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def fail(reason):
    if STATE['error'] is None:
        STATE['error'] = reason
    STATE['status'] = 'REFUSED'
    save()
    return True

def boundary_symbol(value, limit):
    if value is None:
        return None
    return ''.join((c if 32 <= ord(c) < 127 else '?' for c in value[:limit]))

def boundary_proc_identity(pid):
    with Path('/proc/' + str(pid) + '/stat').open('r', encoding='ascii') as f:
        raw = f.read(4097)
    require(len(raw) <= 4096, 'boundary_stat_bound')
    fields = raw.rsplit(')', 1)[1].split()
    return {'pid': pid, 'ppid': int(fields[1]), 'start_ticks': int(fields[19])}

def process_boundary_snapshot():
    result = {'schema': 'frw.process-boundary-symbols.v1', 'purpose': 'REFUSAL_DIAGNOSTIC_ONLY', 'gdb_pid': os.getpid(), 'known_process': STATE['process'], 'frames': []}
    try:
        inferiors = gdb.inferiors()
        result['inferiors'] = [{'number': i.num, 'pid': i.pid} for i in inferiors[:4]]
        result['inferiors_truncated'] = len(inferiors) > 4
        inf = gdb.selected_inferior()
        result['selected_inferior'] = {'number': inf.num, 'pid': inf.pid}
        t = gdb.selected_thread()
        ptid = list(t.ptid) if t is not None and t.is_valid() else None
        result['selected_thread_ptid'] = ptid
        known = STATE['process']
        if known is not None and inf.pid == known['pid'] and (ptid is not None) and (len(ptid) == 3) and all((type(v) is int and v >= 0 for v in ptid)) and (ptid[0] == inf.pid) and (ptid[1] > 0):
            parent = boundary_proc_identity(inf.pid)
            result['selected_process_identity'] = parent
            if parent['ppid'] == os.getpid() and parent['start_ticks'] == known['start_ticks']:
                p = Path('/proc/' + str(inf.pid) + '/task/' + str(ptid[1]) + '/children')
                with p.open('r', encoding='ascii') as f:
                    children = f.read(257)
                require(len(children) <= 256, 'boundary_children_bound')
                pids = children.split()
                require(all((v.isdecimal() and 0 < int(v) <= 2147483647 for v in pids)), 'boundary_children_numeric')
                result['selected_lwp_children'] = [int(v) for v in pids[:8]]
                result['children_truncated'] = len(pids) > 8
    except Exception as exc:
        result['identity_exception_class'] = type(exc).__name__
    try:
        f = gdb.newest_frame()
        for _ in range(24):
            if f is None or not f.is_valid():
                break
            pc = int(f.pc())
            module = gdb.solib_name(pc)
            result['frames'].append({'pc': pc, 'kind': int(f.type()), 'symbol': boundary_symbol(f.name(), 256), 'module_basename': boundary_symbol(Path(module).name, 128) if module else None})
            f = f.older()
        result['frames_truncated'] = f is not None
    except Exception as exc:
        result['stack_exception_class'] = type(exc).__name__
    return result

def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        fail('unexpected_signal')
    elif isinstance(event, gdb.BreakpointEvent) and any((b.type == gdb.BP_CATCHPOINT for b in event.breakpoints)):
        try:
            STATE['process_boundary_diagnostic'] = process_boundary_snapshot()
        except Exception as exc:
            STATE['process_boundary_diagnostic'] = {'exception_class': type(exc).__name__}
        fail('unexpected_fork_vfork_exec')
gdb.execute('set pagination off')
gdb.execute('set confirm off')
gdb.execute('set startup-with-shell off')
gdb.execute('set debuginfod enabled off')
gdb.execute('set auto-load off')
gdb.execute('set follow-fork-mode parent')
gdb.execute('set detach-on-fork off')
gdb.execute('start',to_string=True)
pid=gdb.selected_inferior().pid
st=boundary_proc_identity(pid)
assert st['ppid']==os.getpid()
STATE['process']={'pid':pid,'gdb_pid':os.getpid(),'inferior':gdb.selected_inferior().num,'start_ticks':st['start_ticks']}
gdb.events.stop.connect(stopped)
gdb.execute('catch vfork',to_string=True)
try:
 gdb.execute('continue',to_string=True)
 assert STATE['status']=='REFUSED' and STATE['error']=='unexpected_fork_vfork_exec'
 d=STATE['process_boundary_diagnostic']
 assert d['selected_process_identity']==st
 assert 1<=len(d['frames'])<=24
 assert any(f['symbol']=='frw_fixture_boundary' for f in d['frames'])
 assert 'identity_exception_class' not in d and 'stack_exception_class' not in d
 for f in d['frames']:
  assert set(f)=={'pc','kind','symbol','module_basename'}
  assert f['symbol'] is None or len(f['symbol'])<=256
 assert len(json.dumps(d).encode())<16384
 STATE['fixture_diagnostic_passed']=True
finally:
 gdb.events.stop.disconnect(stopped)
 before=[{'pid':i.pid,'number':i.num} for i in gdb.inferiors() if i.pid]
 for i in gdb.inferiors():
  if i.pid:
   gdb.execute('inferior '+str(i.num),to_string=True)
   gdb.execute('kill',to_string=True)
 STATE['cleanup']={'owned_inferiors_before_kill':before,'all_gdb_inferiors_pid0':all(i.pid==0 for i in gdb.inferiors())}
 save()
