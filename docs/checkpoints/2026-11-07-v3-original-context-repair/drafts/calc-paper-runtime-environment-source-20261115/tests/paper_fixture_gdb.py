"""Root-only actual fixture entry, shared exact enforcing adapter, no Office.

This file is prepared but NOT executed by the source implementation assignment.
The caller supplies actual bounded containment; no fixture effect authorizes LO.
"""
import gdb
import hashlib
import json
import os
from pathlib import Path

WORK = Path('/tmp/friday-metric-work')
OUT = WORK / 'native-trace.json'
CFG = json.loads(Path(os.environ['FRW_PAPER_FIXTURE_CONFIG']).read_text())
CFG['kind'] = 'OWN_POPEN_FIXTURE_ONLY'
CFG['target_path'] = CFG.pop('target')
STATE = dict(schema='frw.own-paper-helper-fixture-trace.v1', kind=CFG['kind'], nonce=CFG['nonce'],
    status='UNRELEASED', records=[], error=None, exit_code=None, process=None, symbols=None,
    actual_M=None, runtime_attested=False)


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def atomic(path, value):
    raw = (json.dumps(value, sort_keys=True) + '\n').encode()
    tmp = path.with_name(path.name + '.pending')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def save():
    atomic(OUT, STATE)


def fail(reason):
    STATE.update(status='REFUSED', error=STATE['error'] or reason)
    save()


def phase():
    return json.loads((WORK / 'phase.json').read_text())


def checked_ref(ref):
    p = Path(ref['path'])
    raw = p.read_bytes()
    require(p.is_absolute() and str(p.resolve()) == str(p) and len(raw) <= 262144
            and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'fixture_exact_source_ref')
    return raw


def window(state):
    value = dict(schema=helper.p['MARKER'], state=state, **{k: helper.b['runtime'][k] for k in
        ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'operation_deadline_monotonic')})
    atomic(WORK / 'load-dependency.json', value)


def ready():
    require(helper.c is not None and helper.c.e['state'] == 'DISARMED', 'fixture_ready_order')
    window('LOAD_OPEN')


def done():
    helper.c.metric()
    window('LOAD_CLOSED')
    atomic(WORK / 'phase.json', dict(nonce=CFG['nonce'], phase='CLOSED', index=None, digit=None))
    helper.metric_ready()


def stopped(event):
    try:
        if isinstance(event, gdb.SignalEvent):
            raise RuntimeError('fixture_unexpected_signal')
        if isinstance(event, gdb.BreakpointEvent):
            if helper.queue_stop(event):
                return
            if any(b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
                helper.boundary(event)
    except Exception as e:
        fail(str(e) if type(e) is RuntimeError else type(e).__name__)


def exited(event):
    try:
        if not helper.exited(event):
            STATE['exit_code'] = getattr(event, 'exit_code', None)
    except Exception as e:
        fail(str(e) if type(e) is RuntimeError else type(e).__name__)


bundle_ref = json.loads(os.environ['FRW_NATIVE_LOAD_DEPENDENCY_REF'])
bundle = json.loads(checked_ref(bundle_ref))
adapter = {'__name__': 'frw_fixture_exact_paper_adapter', '__file__': bundle['adapter_ref']['path']}
exec(compile(checked_ref(bundle['adapter_ref']), bundle['adapter_ref']['path'], 'exec'), adapter)
helper = adapter['create'](gdb, dict(CFG=CFG, STATE=STATE, phase=phase, get_active=lambda: None,
                                  fail=fail, save=save), bundle_ref)
try:
    require(Path.cwd() == WORK and not list(gdb.inferiors())[0].pid and len(gdb.inferiors()) == 1,
            'fixture_fresh_own_inferior')
    require(gdb.current_progspace().filename == CFG['target_path'], 'fixture_target')
    require(hashlib.sha256(Path(CFG['target_path']).read_bytes()).hexdigest() == CFG['target_sha256'], 'fixture_target_hash')
    for command in ('set pagination off', 'set confirm off', 'set startup-with-shell off', 'set non-stop off',
        'set auto-load off', 'set debuginfod enabled off', 'set disable-randomization off',
        'set follow-fork-mode parent', 'set detach-on-fork off', 'set follow-exec-mode same',
        'set schedule-multiple on', 'handle SIGCHLD nostop noprint pass', 'set stop-on-solib-events 1'):
        gdb.execute(command, to_string=True)
    atomic(WORK / 'phase.json', dict(nonce=CFG['nonce'], phase='IDLE', index=None, digit=None))
    gdb.events.stop.connect(stopped)
    gdb.events.exited.connect(exited)
    for kind in ('fork', 'vfork', 'exec'):
        before = {b.number for b in (gdb.breakpoints() or ())}
        gdb.execute('catch ' + kind, to_string=True)
        for bp in gdb.breakpoints():
            if bp.number not in before:
                helper.catchpoints[bp.number] = kind
    gdb.execute('starti', to_string=True)
    inf = gdb.selected_inferior()
    proc = helper.proc(inf.pid)
    STATE['process'] = dict(pid=inf.pid, start_ticks=proc['start_ticks'], gdb_pid=os.getpid(), inferior=inf.num)
    helper.ensure()
    base = helper.base(inf.pid, CFG['target_path'])
    helper.breakpoint(base + CFG['ready_offset'], ready)
    helper.breakpoint(base + CFG['done_offset'], done)
    for _ in range(128):
        require(STATE['error'] is None, 'fixture_refused')
        helper.install()
        if helper.installed:
            gdb.execute('set stop-on-solib-events 0', to_string=True)
        if not any(i.num == 1 and i.pid for i in gdb.inferiors()):
            break
        if not gdb.selected_inferior().pid:
            helper.original_selected()
        gdb.execute('continue', to_string=True)
        helper.dispatch()
    else:
        raise RuntimeError('fixture_stop_limit')
    require(STATE['error'] is None and STATE['exit_code'] == 0 and helper.c.e['state'] == 'CLOSED', 'fixture_terminal_contract')
    require(all(i.pid == 0 for i in gdb.inferiors()) and all(not (Path('/proc') / str(pid)).exists()
            for pid in helper.known), 'fixture_owned_tree_not_absent')
    STATE['status'] = 'COMPLETE_HELPER_FIXTURE_ONLY'
except Exception as e:
    fail(str(e) if type(e) is RuntimeError else type(e).__name__)
finally:
    for inf in gdb.inferiors():
        if inf.pid:
            try:
                before = helper.proc(inf.pid)
                helper.known[inf.pid] = before
                gdb.execute('inferior ' + str(inf.num), to_string=True)
                require(helper.proc(inf.pid) == before, 'fixture_cleanup_birth')
                gdb.execute('kill', to_string=True)
            except Exception:
                fail('fixture_cleanup_unconfirmed')
    STATE['own_inferior_absent'] = all(i.pid == 0 for i in gdb.inferiors()) and all(
        not (Path('/proc') / str(pid)).exists() for pid in helper.known)
    if not STATE['own_inferior_absent']:
        fail('fixture_cleanup_unconfirmed')
    save()
    gdb.execute('quit ' + ('0' if STATE['status'] == 'COMPLETE_HELPER_FIXTURE_ONLY' else '2'))
