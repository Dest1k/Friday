"""SOURCE-ONLY own-C caller. Import is inert; run only from Root-owned GDB.

Reuses exact reviewed definitions and native finally; native main is never run.
Fixture markers and two held ENV projections prove no Office/font/native M.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time

WORK=Path('/tmp/friday-metric-work')
NATIVE_NAMES={'font_file','font_read','font_write','capture_font_runtime','require','pin','save','fail',
              'phase','identity','boundary_symbol','boundary_proc_identity','process_boundary_snapshot','stopped','exited'}
CONTROLS=('FRW_NATIVE_OBSERVER_CONFIG','FRW_NATIVE_LOAD_DEPENDENCY_REF',
          'FRW_NATIVE_GPGME_ENGINE_INIT_REF','FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE','FRW_HELD_FIXTURE_CONFIG')


def checked_ref(ref):
    if type(ref) is not dict or set(ref)!={'path','sha256'}:raise RuntimeError('fixture_exact_ref')
    p=Path(ref['path'])
    if not p.is_absolute() or p.resolve()!=p:raise RuntimeError('fixture_source_alias')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        s=os.fstat(fd)
        if not(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid in(0,os.getuid())
               and not s.st_mode&0o022 and s.st_size<=262144):raise RuntimeError('fixture_source_rights_bound')
        raw=os.read(fd,262145);stamp=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
        if stamp(s)!=stamp(os.fstat(fd)) or stamp(s)!=stamp(p.lstat()):raise RuntimeError('fixture_source_changed')
    finally:os.close(fd)
    if len(raw)>262144 or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise RuntimeError('fixture_source_pin')
    return raw


def exact_native(tree):
    definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in NATIVE_NAMES]
    if {n.name for n in definitions}!=NATIVE_NAMES or any(n.decorator_list for n in definitions):
        raise RuntimeError('fixture_native_definitions')
    finals=[n.finalbody for n in tree.body if isinstance(n,ast.Try) and len(n.body)==1
            and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Call)
            and isinstance(n.body[0].value.func,ast.Name) and n.body[0].value.func.id=='main']
    if len(finals)!=1 or not finals[0]:raise RuntimeError('fixture_native_finally')
    return ast.Module(body=definitions,type_ignores=[]),ast.Module(body=finals[0],type_ignores=[])


def atomic_replace(path,value):
    raw=(json.dumps(value,sort_keys=True)+'\n').encode();tmp=path.with_name(path.name+'.pending')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
    os.replace(tmp,path)


def load_window(state):
    atomic_replace(WORK/'load-dependency.json',dict(schema=helper.paper.p['MARKER'],state=state,
        **{key:helper.paper.b['runtime'][key] for key in
        ('operation_id','nonce','source_sha256','manifest_ref','operation_deadline_monotonic')}))


def ready():
    require(helper.paper.c is not None and helper.paper.c.e['state']=='DISARMED','fixture_ready_order')
    STATE.update(fixture_boundary='BEFORE_LOAD_READY',status='READY_UNRELEASED')
    save()
    path=WORK/'own-fixture-ready-go';deadline=helper.b['runtime']['operation_deadline_monotonic']
    while not os.path.lexists(path):
        require(time.monotonic()<deadline,'fixture_ready_original_deadline')
        time.sleep(min(.005,max(0,deadline-time.monotonic())))
    release=json.loads(font_read(path))
    require(release=={'nonce':CFG['nonce'],'boundary':'BEFORE_LOAD_READY'} and time.monotonic()<deadline,
            'fixture_ready_release_binding')
    require((WORK/'office-release.json').is_file() and (WORK/'unit-release.json').is_file(),
            'fixture_missing_actual_host_releases')
    load_window('LOAD_OPEN')
    STATE.update(fixture_boundary='LOAD_OPEN',status='OWN_LOAD_RUNNABLE')


def paper_done():
    # Adapter.metric_ready requires LOAD_CLOSED. Here only paper's custody is
    # closed; GPG still owns the same open window. Its bootstrap also demands
    # actual paper2/3 absence. Never close/reopen the marker around this check.
    helper.paper.ensure().metric()
    helper.gpgme.paper_closed()
    STATE['paper_closed_before_gpgme']=True


def after_load():
    require(not STATE['records'] and STATE['fixture_boundary']=='LOAD_OPEN','fixture_loaded_order')
    helper.paper.ensure().metric()
    helper.gpgme.metric_ready()
    load_window('LOAD_CLOSED')
    helper.metric_ready()
    STATE.update(fixture_boundary='AFTER_LOAD_BEFORE_QUERY',status='OWN_LOADED_GATE_RUNNABLE')


def query_marker():
    identity();index=helper.register('rdi')
    require(len(font_runtime_boundaries)==1 and index==len(STATE['records'])<10
            and STATE['fixture_boundary']=='AFTER_LOAD_BEFORE_QUERY','fixture_marker_order')
    STATE['records'].append(dict(schema='frw.ownC.inert-marker.v1',index=index,
        semantics='FIXTURE_MARKER_ONLY_NO_NATIVE_RANGE'))


def restore_marker():
    require(len(STATE['records'])==10 and not STATE['fixture_restore_marker_seen'],'fixture_restore_order')
    STATE['fixture_restore_marker_seen']=True


def close_marker():
    require(STATE['fixture_restore_marker_seen'] and not STATE['fixture_close_marker_seen'],'fixture_close_order')
    STATE['fixture_close_marker_seen']=True


def after_close():
    require(len(STATE['records'])==10 and len(font_runtime_boundaries)==1
            and STATE['fixture_restore_marker_seen'] and STATE['fixture_close_marker_seen'],'fixture_closed_order')
    atomic_replace(WORK/'phase.json',dict(nonce=CFG['nonce'],phase='CLOSED',index=None,digit=None))
    STATE.update(fixture_boundary='AFTER_READONLY_CLOSE',status='OWN_CLOSED_GATE_RUNNABLE')


def load_custodies():
    native=dict(CFG=CFG,STATE=STATE,phase=phase,get_active=lambda:active,fail=fail,save=save)
    pref=json.loads(os.environ['FRW_NATIVE_LOAD_DEPENDENCY_REF']);pb=json.loads(checked_ref(pref))
    paper_ns={'__name__':'frw_ownc_exact_paper','__file__':pb['adapter_ref']['path']}
    exec(compile(checked_ref(pb['adapter_ref']),pb['adapter_ref']['path'],'exec'),paper_ns)
    paper=paper_ns['create'](gdb,native,pref)
    gref=json.loads(os.environ['FRW_NATIVE_GPGME_ENGINE_INIT_REF']);gb=json.loads(checked_ref(gref))
    gadapter=gb['adapter_ref'];gns={'__name__':'frw_ownc_exact_gpgme','__file__':gadapter['path']}
    exec(compile(checked_ref(gadapter),gadapter['path'],'exec'),gns)
    engine=gns['create'](gdb,native,gref,paper)
    require(os.environ['FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE']==gb['evidence_path'],'fixture_explicit_gpgme_evidence')
    return gns['MultiCustody'](paper,engine)


def declared_environment(expected):
    require(type(expected) is dict and all(type(k) is str and type(v) is str
            and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',k)
            and not any(c in v for c in ('\0','\n','\r')) and v==v.strip()
            for k,v in expected.items()),'fixture_declared_target_environment')
    require(not any(k.startswith('FRW_NATIVE_') or k=='FRW_HELD_FIXTURE_CONFIG' for k in expected),
            'fixture_no_debug_controls_in_target_environment')
    return expected


def construct_inferior_environment(debugger, expected):
    # GDB CLI receives one validated command at a time, with startup shell off
    # before execution. Python's os.environ (including loader/refs) is untouched.
    declared_environment(expected)
    debugger.execute('set confirm off',to_string=True)
    debugger.execute('unset environment',to_string=True)
    for key,value in sorted(expected.items()):
        debugger.execute('set environment '+key+'='+value,to_string=True)


def environment_diagnostic(actual, expected, *, phase, nonce, exception_class):
    """Bounded key names/counts/digests only; never emit an ENV value."""
    keys = lambda names: [name if len(name) <= 128 else 'sha256:' + hashlib.sha256(
        name.encode('utf-8', 'surrogatepass')).hexdigest() for name in sorted(names)[:32]]
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    changed = {key for key in set(actual) & set(expected) if actual[key] != expected[key]}
    digest = lambda env: hashlib.sha256(json.dumps(env, sort_keys=True,
        separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    return dict(schema='frw.ownc.environment-check-metadata.v1', phase=phase, nonce=nonce,
        exception_class=exception_class, actual_count=len(actual), expected_count=len(expected),
        actual_sha256=digest(actual), expected_sha256=digest(expected),
        missing_count=len(missing), extra_count=len(extra), changed_count=len(changed),
        missing_keys=keys(missing), extra_keys=keys(extra), changed_keys=keys(changed))


def validate_inferior_environment(text, expected, *, publish=None, nonce=None):
    declared_environment(expected)
    actual={}
    error=None
    try:
        for line in text.splitlines():
            require('=' in line,'fixture_inferior_environment_encoding')
            key,value=line.split('=',1)
            require(key not in actual,'fixture_inferior_environment_duplicate')
            actual[key]=value
        require(actual==expected,'fixture_complete_startup_environment_mismatch')
    except RuntimeError as exc:
        error=exc
    if publish is not None:
        try:
            diagnostic=environment_diagnostic(actual,expected,phase='GDB_INFERIOR_BEFORE_STARTI',
                nonce=nonce,exception_class='RuntimeError' if error is not None else None)
            diagnostic['observed_text_sha256']=hashlib.sha256(text.encode('utf-8','surrogatepass')).hexdigest()
            publish(diagnostic)
        except Exception:
            if error is not None:raise error from None
            raise
    if error is not None:raise error
    return actual


def observe_stop_stage(event):
    # Numeric/name-only diagnostics. No target calls, writes, resume or new BP.
    # This observer runs before the exact native stop consumer. It grants none.
    STATE['ownc_last_guard_stage']='other-stop'
    try:
        if helper is None:return
        if helper.gpgme.fork_pending is not None:
            STATE['ownc_last_guard_stage']='pending-fork-materialization'
            return
        if not isinstance(event,gdb.BreakpointEvent):return
        numbers=[b.number for b in event.breakpoints]
        if len(numbers)!=1:
            if numbers and helper.gpgme.init_active:
                kinds=[helper.gpgme.catchpoints.get(number) for number in numbers]
                if len(set(kinds))==1 and kinds[0] in ('clone_guard','exit_intent','unsupported_process_or_session'):
                    STATE['ownc_last_guard_stage']='boundary:'+kinds[0]
            return
        number=numbers[0]
        handler=helper.gpgme.handlers.get(number)
        if handler is not None:
            STATE['ownc_last_guard_stage']=handler[1].__name__
        elif event.breakpoints[0].type==gdb.BP_CATCHPOINT:
            kind=helper.gpgme.catchpoints.get(number) or helper.paper.catchpoints.get(number)
            if kind is not None:STATE['ownc_last_guard_stage']='boundary:'+kind
    except Exception as exc:
        STATE['ownc_stage_capture_exception_class']=type(exc).__name__


def capture_refusal_stop():
    # Actual observations only; no preasserted affected-child release flag or
    # negative PASS. Root must evaluate this causal stop and final cleanup.
    value=dict(schema='frw.ownc.first-refusal-stop.v1',
        stage=STATE.get('ownc_last_guard_stage'),first_error=STATE['error'],inferiors=[])
    STATE['ownc_refusal_stop']=value
    try:
        require(helper is not None and hasattr(helper,'gpgme'),'fixture_refusal_owner_missing')
        helper.gpgme.paper_closed()
        value['paper_closed_actual_children_2_3_absent']=True
        value['paper_children']=helper.paper.c.snapshot()['children']
        value['engine_finished_initialization']=helper.gpgme.finished_initialization
        value['engine_active_initialization']=helper.gpgme.init_active
        value['engine_known_inferior_numbers']=sorted(v['inferior'] for v in helper.gpgme.known.values())
        for inf in gdb.inferiors():
            if not inf.pid:continue
            before=helper.proc(inf.pid)
            threads=[dict(ptid=list(t.ptid),valid=t.is_valid(),stopped=t.is_stopped()) for t in inf.threads()]
            require(helper.proc(inf.pid)==before,'fixture_refusal_birth_changed')
            value['inferiors'].append(dict(number=inf.num,identity=before,threads=threads))
        value['observation_scope']='CURRENT_REFUSAL_STOP_ONLY_NO_FUTURE_OR_RELEASE_CLAIM'
    except Exception as exc:
        value['capture_exception_class']=type(exc).__name__
    save()


def run():
    global gdb,CFG,STATE,active,helper,pending_action,font_runtime_boundaries
    import gdb
    os.umask(0o077)
    cfg_path=Path(os.environ['FRW_HELD_FIXTURE_CONFIG'])
    # Config is a protected runtime input; its exact source refs are hash-bound.
    CFG=json.loads(checked_ref({'path':str(cfg_path),'sha256':hashlib.sha256(cfg_path.read_bytes()).hexdigest()}))
    if (Path.cwd()!=WORK or CFG['kind']!='OWN_POPEN_FIXTURE_ONLY'
        or CFG['phase_path']!=str(WORK/'phase.json') or CFG['trace_path']!=str(WORK/'native-trace.json')
        or type(CFG['event_limit']) is not int or not 1<=CFG['event_limit']<=8192):
        raise RuntimeError('fixture_scope_or_work')
    raw=checked_ref(CFG['native_observer_ref']);tree=ast.parse(raw,filename=CFG['native_observer_ref']['path'])
    definitions,final=exact_native(tree)
    STATE=dict(schema='frw.own-held-font-fixture-trace.v1',kind=CFG['kind'],nonce=CFG['nonce'],
        status='UNRELEASED',records=[],error=None,exit_code=None,process=None,symbols=None,actual_M=None,
        runtime_attested=False,record_semantics='FIXTURE_MARKER_ONLY',fixture_boundary=None,
        fixture_restore_marker_seen=False,fixture_close_marker_seen=False,native_main_executed=False,
        native_observer_ref=CFG['native_observer_ref'],paper_closed_before_gpgme=False)
    active=None;helper=None;pending_action=None;font_runtime_boundaries=[]
    exec(compile(definitions,CFG['native_observer_ref']['path'],'exec'),globals())
    try:
        require(len(gdb.inferiors())==1 and gdb.selected_inferior().pid==0,'fixture_fresh_own_inferior')
        require(gdb.current_progspace().filename==CFG['target_path'],'fixture_target')
        pin(CFG['target_path'],CFG['target_sha256']);helper=load_custodies()
        # Clear the entire inherited inferior ENV and construct the complete
        # declaration. All five debugger-only controls remain solely in Python.
        construct_inferior_environment(gdb,CFG['target_environment'])
        validate_inferior_environment(gdb.execute('show environment',to_string=True),CFG['target_environment'],
            nonce=CFG['nonce'],publish=lambda value:atomic_replace(WORK/'ownc-gdb-environment-check.json',value))
        for setting in ('set pagination off','set confirm off','set startup-with-shell off','set non-stop off',
                'set may-call-functions off',
                'set auto-load off','set debuginfod enabled off','set disable-randomization off',
                'set follow-fork-mode parent','set detach-on-fork off','set follow-exec-mode same',
                'set schedule-multiple on','handle SIGCHLD nostop noprint pass','handle SIGSTOP noprint nopass stop',
                'set stop-on-solib-events 1'):
            gdb.execute(setting,to_string=True)
        atomic_replace(WORK/'phase.json',dict(nonce=CFG['nonce'],phase='IDLE',index=None,digit=None))
        gdb.events.stop.connect(observe_stop_stage);gdb.events.stop.connect(stopped);gdb.events.exited.connect(exited)
        catchpoints={}
        for kind in ('fork','vfork','exec'):
            before={bp.number for bp in(gdb.breakpoints() or ())};gdb.execute('catch '+kind,to_string=True)
            for bp in gdb.breakpoints():
                if bp.number not in before:catchpoints[bp.number]=kind
        helper.paper.catchpoints=dict(catchpoints);helper.gpgme.catchpoints=dict(catchpoints)
        gdb.execute('starti',to_string=True);identity();helper.paper.ensure()
        base=helper.base(STATE['process']['pid'],CFG['target_path'])
        handlers=dict(fixture_ready=ready,fixture_paper_done=paper_done,fixture_after_load=after_load,
            fixture_query_marker=query_marker,fixture_restore_marker=restore_marker,
            fixture_close_marker=close_marker,fixture_after_close=after_close)
        for name,callback in handlers.items():
            helper.breakpoint(base+CFG['marker_offsets'][name],callback,one_shot=name!='fixture_query_marker')
        for _ in range(CFG['event_limit']):
            require(time.monotonic()<helper.b['runtime']['operation_deadline_monotonic'],'fixture_original_deadline')
            require(STATE['error'] is None,'fixture_refused');helper.install()
            if helper.installed:gdb.execute('set stop-on-solib-events 0',to_string=True)
            if not any(i.num==1 and i.pid for i in gdb.inferiors()):break
            if not gdb.selected_inferior().pid:helper.original_selected()
            gdb.execute('continue',to_string=True);require(STATE['error'] is None,'fixture_trace_refused')
            helper_action=helper.dispatch()
            if not gdb.selected_inferior().pid:helper.original_selected()
            if not any(i.num==1 and i.pid for i in gdb.inferiors()):break
            require(helper_action is None or pending_action is None,'fixture_stop_collision')
            action,pending_action=helper_action or pending_action,None
            if action=='FONT_RUNTIME':
                capture_font_runtime();STATE['accepted_held_points']=len(font_runtime_boundaries);save()
            elif action=='GPG_DRAIN':helper.gpgme.drain()
            else:require(action in(None,'CONTINUE'),'fixture_unrecognized_stop')
        else:raise RuntimeError('fixture_stop_limit')
        require(STATE['error'] is None and STATE['exit_code']==0 and len(font_runtime_boundaries)==2
                and len(STATE['records'])==10 and helper.paper.c.e['state']=='CLOSED'
                and helper.gpgme.finished_initialization,'fixture_terminal_contract')
        helper.metric_ready();STATE['status']='COMPLETE_HELD_ENV_FIXTURE_ONLY'
    except Exception as exc:
        fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
    finally:
        # Exact final owned-inferior cleanup from reviewed native source; includes
        # unknown descendants, birth CAS, union clear_pending and first error.
        # MultiCustody.cleanup_inferiors is intentionally never called.
        try:
            if STATE['error'] is not None:capture_refusal_stop()
        except Exception as exc:
            STATE['ownc_refusal_diagnostic_exception_class']=type(exc).__name__
        finally:
            exec(compile(final,CFG['native_observer_ref']['path'],'exec'),globals())


if __name__=='__main__':run()
