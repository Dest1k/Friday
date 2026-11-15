"""Root-only ownC entry. Prepared source; not executed by its preparer.

The pinned native capture/stopped/getter logic is executed unmodified. Only
own-fixture marker routing and lifetime are added. Ten records below mean ten
observed inert ownC markers, never native metric ranges or an actual M.
"""
import ast
import gdb
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time

os.umask(0o077)
WORK = Path('/tmp/friday-metric-work')


def checked_ref(ref):
    if type(ref) is not dict or set(ref) != {'path', 'sha256'}:
        raise RuntimeError('fixture_exact_ref')
    path = Path(ref['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise RuntimeError('fixture_source_alias')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not (stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022
                and before.st_size <= 262144):
            raise RuntimeError('fixture_source_rights_bound')
        raw = os.read(fd, 262145)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if stamp(before) != stamp(os.fstat(fd)) or stamp(before) != stamp(path.lstat()):
            raise RuntimeError('fixture_source_changed')
    finally:
        os.close(fd)
    if len(raw) > 262144 or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise RuntimeError('fixture_source_pin')
    return raw


CFG = json.loads(Path(os.environ['FRW_HELD_FIXTURE_CONFIG']).read_text())
if (Path.cwd() != WORK or CFG['kind'] != 'OWN_POPEN_FIXTURE_ONLY'
        or CFG['phase_path'] != str(WORK / 'phase.json')
        or CFG['trace_path'] != str(WORK / 'native-trace.json')):
    raise RuntimeError('fixture_scope_or_work')

# Definitions only: native main()/load_helper() and its module-level finally
# are deliberately not executed and receive no new Office admission.
native_names = {'font_file', 'font_read', 'font_write', 'capture_font_runtime',
                'require', 'pin', 'save', 'fail', 'phase', 'identity',
                'boundary_proc_identity', 'stopped', 'exited'}
native_raw = checked_ref(CFG['native_observer_ref'])
tree = ast.parse(native_raw, filename=CFG['native_observer_ref']['path'])
definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in native_names]
if {node.name for node in definitions} != native_names or any(node.decorator_list for node in definitions):
    raise RuntimeError('fixture_native_definitions')
STATE = dict(schema='frw.own-held-font-fixture-trace.v1', kind=CFG['kind'], nonce=CFG['nonce'],
             status='UNRELEASED', records=[], error=None, exit_code=None, process=None, symbols=None,
             actual_M=None, runtime_attested=False, record_semantics='FIXTURE_MARKER_ONLY',
             fixture_boundary=None, fixture_restore_marker_seen=False, fixture_close_marker_seen=False,
             native_observer_ref=CFG['native_observer_ref'], native_main_executed=False)
active = None
helper = None
pending_action = None
font_runtime_boundaries = []
exec(compile(ast.Module(body=definitions, type_ignores=[]), CFG['native_observer_ref']['path'], 'exec'), globals())


def atomic_replace(path, value):
    raw = (json.dumps(value, sort_keys=True) + '\n').encode()
    pending = path.with_name(path.name + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def load_window(state):
    atomic_replace(WORK / 'load-dependency.json', dict(schema=helper.p['MARKER'], state=state,
        **{key: helper.b['runtime'][key] for key in
           ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'operation_deadline_monotonic')}))


def ready():
    require(helper.c is not None and helper.c.e['state'] == 'DISARMED', 'fixture_ready_order')
    load_window('LOAD_OPEN')


def paper_done():
    helper.c.metric()
    load_window('LOAD_CLOSED')
    helper.metric_ready()


def after_load():
    require(not STATE['records'] and STATE['fixture_boundary'] is None, 'fixture_loaded_order')
    helper.metric_ready()
    STATE.update(fixture_boundary='AFTER_LOAD_BEFORE_QUERY', status='OWN_LOADED_GATE_RUNNABLE')


def query_marker():
    identity()
    index = helper.register('rdi')
    require(len(font_runtime_boundaries) == 1 and index == len(STATE['records']) < 10
            and STATE['fixture_boundary'] == 'AFTER_LOAD_BEFORE_QUERY', 'fixture_marker_order')
    STATE['records'].append(dict(schema='frw.ownC.inert-marker.v1', index=index,
                                 semantics='FIXTURE_MARKER_ONLY_NO_NATIVE_RANGE'))


def restore_marker():
    require(len(STATE['records']) == 10 and not STATE['fixture_restore_marker_seen'], 'fixture_restore_order')
    STATE['fixture_restore_marker_seen'] = True


def close_marker():
    require(STATE['fixture_restore_marker_seen'] and not STATE['fixture_close_marker_seen'], 'fixture_close_order')
    STATE['fixture_close_marker_seen'] = True


def after_close():
    require(len(STATE['records']) == 10 and len(font_runtime_boundaries) == 1
            and STATE['fixture_restore_marker_seen'] and STATE['fixture_close_marker_seen'], 'fixture_closed_order')
    atomic_replace(WORK / 'phase.json', dict(nonce=CFG['nonce'], phase='CLOSED', index=None, digit=None))
    STATE.update(fixture_boundary='AFTER_READONLY_CLOSE', status='OWN_CLOSED_GATE_RUNNABLE')


try:
    require(len(gdb.inferiors()) == 1 and gdb.selected_inferior().pid == 0, 'fixture_fresh_own_inferior')
    require(gdb.current_progspace().filename == CFG['target_path'], 'fixture_target')
    pin(CFG['target_path'], CFG['target_sha256'])
    bundle_ref = json.loads(os.environ['FRW_NATIVE_LOAD_DEPENDENCY_REF'])
    bundle = json.loads(checked_ref(bundle_ref))
    adapter = {'__name__': 'frw_held_fixture_exact_paper_adapter', '__file__': bundle['adapter_ref']['path']}
    exec(compile(checked_ref(bundle['adapter_ref']), bundle['adapter_ref']['path'], 'exec'), adapter)
    helper = adapter['create'](gdb, dict(CFG=CFG, STATE=STATE, phase=phase, get_active=lambda: active,
                                      fail=fail, save=save), bundle_ref)
    for setting in ('set pagination off', 'set confirm off', 'set startup-with-shell off', 'set non-stop off',
            'set auto-load off', 'set debuginfod enabled off', 'set disable-randomization off',
            'set follow-fork-mode parent', 'set detach-on-fork off', 'set follow-exec-mode same',
            'set schedule-multiple on', 'handle SIGCHLD nostop noprint pass',
            'handle SIGSTOP noprint nopass stop', 'set stop-on-solib-events 1'):
        gdb.execute(setting, to_string=True)
    atomic_replace(WORK / 'phase.json', dict(nonce=CFG['nonce'], phase='IDLE', index=None, digit=None))
    gdb.events.stop.connect(stopped)
    gdb.events.exited.connect(exited)
    for kind in ('fork', 'vfork', 'exec'):
        before = {bp.number for bp in (gdb.breakpoints() or ())}
        gdb.execute('catch ' + kind, to_string=True)
        for bp in gdb.breakpoints():
            if bp.number not in before:
                helper.catchpoints[bp.number] = kind
    gdb.execute('starti', to_string=True)
    identity()
    helper.ensure()
    base = helper.base(STATE['process']['pid'], CFG['target_path'])
    handlers = dict(fixture_ready=ready, fixture_paper_done=paper_done, fixture_after_load=after_load,
                    fixture_query_marker=query_marker, fixture_restore_marker=restore_marker,
                    fixture_close_marker=close_marker, fixture_after_close=after_close)
    for name, callback in handlers.items():
        helper.breakpoint(base + CFG['marker_offsets'][name], callback, one_shot=name != 'fixture_query_marker')
    for _ in range(512):
        require(time.monotonic() < helper.b['runtime']['operation_deadline_monotonic'], 'fixture_original_deadline')
        require(STATE['error'] is None, 'fixture_refused')
        helper.install()
        if helper.installed:
            gdb.execute('set stop-on-solib-events 0', to_string=True)
        if not any(inf.num == 1 and inf.pid for inf in gdb.inferiors()):
            break
        if not gdb.selected_inferior().pid:
            helper.original_selected()
        gdb.execute('continue', to_string=True)
        require(STATE['error'] is None, 'fixture_trace_refused')
        helper_action = helper.dispatch()
        if not gdb.selected_inferior().pid:
            helper.original_selected()
        if not any(inf.num == 1 and inf.pid for inf in gdb.inferiors()):
            break
        require(helper_action is None or pending_action is None, 'fixture_stop_collision')
        action, pending_action = helper_action or pending_action, None
        if action == 'FONT_RUNTIME':
            capture_font_runtime()
            STATE['accepted_held_points'] = len(font_runtime_boundaries)
            save()
        else:
            require(action in (None, 'CONTINUE'), 'fixture_unrecognized_stop')
    else:
        raise RuntimeError('fixture_stop_limit')
    require(STATE['error'] is None and STATE['exit_code'] == 0 and len(font_runtime_boundaries) == 2
            and len(STATE['records']) == 10 and helper.c.e['state'] == 'CLOSED', 'fixture_terminal_contract')
    STATE['status'] = 'COMPLETE_HELD_ENV_FIXTURE_ONLY'
except Exception as exc:
    fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
finally:
    for inf in gdb.inferiors():
        if not inf.pid:
            continue
        try:
            require(helper is not None and (inf.num == 1 or inf.pid in helper.known), 'fixture_cleanup_ownership')
            before = helper.proc(inf.pid)
            helper.known[inf.pid] = before
            gdb.execute('inferior ' + str(inf.num), to_string=True)
            require(helper.proc(inf.pid) == before, 'fixture_cleanup_birth')
            gdb.execute('kill', to_string=True)
        except Exception:
            fail('fixture_cleanup_unconfirmed')
    STATE['own_inferior_absent'] = all(inf.pid == 0 for inf in gdb.inferiors()) and (
        helper is not None and all(not (Path('/proc') / str(pid)).exists() for pid in helper.known))
    if not STATE['own_inferior_absent']:
        fail('fixture_cleanup_unconfirmed')
    save()
    gdb.execute('quit ' + ('0' if STATE['status'] == 'COMPLETE_HELD_ENV_FIXTURE_ONLY' else '2'))
