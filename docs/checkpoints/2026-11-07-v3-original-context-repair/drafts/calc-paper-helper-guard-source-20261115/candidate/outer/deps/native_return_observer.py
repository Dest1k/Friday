"""GDB-only, launch-only, exact x86-64 observer. No Office admission is issued.
The outer return-site breakpoint reads RAX before its first narrowing instruction.
No inferior function calls, writes, forced returns, stepping or foreign attach.
"""
import gdb
import hashlib
import json
import os
from pathlib import Path

CFG = json.loads(Path(os.environ['FRW_NATIVE_OBSERVER_CONFIG']).read_text())
STATE = {'schema': 'frw.native-return-trace.v1', 'kind': CFG['kind'],
         'nonce': CFG['nonce'], 'status': 'UNRELEASED', 'records': [],
         'error': None, 'exit_code': None, 'process': None, 'symbols': None,
         'actual_M': None, 'runtime_attested': False}
active = None
bound_thread = bound_font = bound_device = None
entry_bp = return_bp = outer_bp = None
installed = False
pending_action = None
helper = None
catchpoints = {}


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def pin(path, sha):
    p = Path(path)
    require(p.is_absolute() and str(p.resolve()) == path and p.is_file(), 'noncanonical_file')
    require(hashlib.sha256(p.read_bytes()).hexdigest() == sha, 'file_pin_changed')


def save():
    p = Path(CFG['trace_path'])
    tmp = p.with_suffix('.pending')
    tmp.write_text(json.dumps(STATE, sort_keys=True) + '\n')
    os.replace(tmp, p)


def fail(reason):
    if STATE['error'] is None:
        STATE['error'] = reason
    STATE['status'] = 'REFUSED'
    save()
    return True


def guarded(fn):
    def wrap(*args):
        try:
            return fn(*args)
        except Exception as exc:
            # Only controlled reason identifiers or exception CLASS; never content.
            return fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
    return wrap


def phase():
    p = Path(CFG['phase_path'])
    if not p.exists() and not STATE['records'] and active is None:
        return {'phase': 'IDLE'}
    value = json.loads(p.read_text())
    require(set(value) == {'nonce', 'phase', 'index', 'digit'}, 'phase_schema')
    require(value['nonce'] == CFG['nonce'], 'phase_nonce')
    require(value['phase'] in ('IDLE', 'METRIC', 'CLOSED'), 'unknown_phase')
    if value['phase'] == 'METRIC':
        if helper is not None:
            helper.metric_ready()
        require(type(value['index']) is int and 0 <= value['index'] <= 9
                and value['digit'] == str(value['index']), 'phase_digit')
    else:
        require(value['index'] is None and value['digit'] is None, 'inactive_phase_payload')
    return value


def identity():
    inf = gdb.selected_inferior()
    require(inf.num == 1 and inf.pid > 0 and
            (len(gdb.inferiors()) == 1 if helper is None else helper.identity_scope()), 'inferior_identity')
    pid = inf.pid
    st = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
    require(int(st[1]) == os.getpid(), 'not_direct_own_child')
    require(os.readlink('/proc/' + str(pid) + '/exe') == CFG['target_path'], 'unexpected_exec')
    value = {'pid': pid, 'start_ticks': int(st[19]), 'gdb_pid': os.getpid(), 'inferior': inf.num}
    if STATE['process'] is None:
        STATE['process'] = value
    require(STATE['process'] == value, 'process_changed')
    return inf


def thread():
    identity()
    t = gdb.selected_thread()
    require(t is not None and t.is_valid(), 'thread_unknown')
    return list(t.ptid)


def frame_ok(f):
    require(f is not None and f.is_valid() and f.type() == gdb.NORMAL_FRAME, 'frame_kind')
    require(f.architecture().name() == 'i386:x86-64', 'architecture')
    require(f.unwind_stop_reason() == gdb.FRAME_UNWIND_NO_REASON, 'unwind_error')
    return f


def reg(f, name):
    v = f.read_register(name)
    require(not v.is_optimized_out and not v.is_unavailable, 'register_unavailable')
    return int(v) & ((1 << 64) - 1)


def memint(addr, count):
    require(addr != 0, 'null_pointer')
    return int.from_bytes(gdb.selected_inferior().read_memory(addr, count).tobytes(), 'little')


def digit_at(ustring_address):
    data = memint(ustring_address, 8)  # OUString::pData at 0; exact source/LP64 ABI.
    require(memint(data + 4, 4) == 1, 'not_single_digit')
    char = memint(data + 8, 2)
    require(48 <= char <= 57 and memint(data + 10, 2) == 0, 'digit_content')
    return chr(char)


class OuterFinish(gdb.FinishBreakpoint):
    def __init__(self, f, slot):
        self.slot = slot
        super().__init__(f, internal=True)

    @guarded
    def stop(self):
        global active, pending_action
        slot = self.slot
        require(active is slot and thread() == slot['thread'], 'outer_finish_binding')
        require(phase() == slot['phase'], 'phase_changed_during_call')
        require(slot['native_entered'] and slot['native_returned'], 'missing_native_return')
        raw = slot['raw_native']
        outer = reg(frame_ok(gdb.newest_frame()), 'rax') & 0xffffffff
        outer = outer - (1 << 32) if outer >= (1 << 31) else outer
        slot['outer_int32'] = outer
        STATE['records'].append({k: slot[k] for k in
            ('index', 'digit', 'thread', 'font', 'device', 'string_address', 'raw_native', 'outer_int32',
             'native_return_pc', 'native_entry_sp', 'outer_entry_sp')})
        require(-(1 << 31) <= raw < (1 << 31), 'native_not_representable_int32')
        require(0 < raw < 65536 and outer == raw, 'native_range_or_transport')
        active = None
        pending_action = 'END_CALL'
        STATE['status'] = 'TEN_CALLS_OBSERVED_UNRELEASED' if len(STATE['records']) == 10 else 'UNRELEASED'
        save()
        return True

    def out_of_scope(self):
        fail('outer_unwound_without_return')


class OuterEntry(gdb.Breakpoint):
    @guarded
    def stop(self):
        global active, bound_thread, bound_font, pending_action
        require(STATE['error'] is None, 'already_refused')
        p = phase()
        if p['phase'] != 'METRIC':
            require(active is None and not STATE['records'], 'outer_outside_metric_phase')
            pending_action = 'CONTINUE'
            return True  # Startup only, never an observation.
        require(active is None and p['index'] == len(STATE['records']) < 10, 'extra_nested_or_misaligned_outer')
        f = frame_ok(gdb.newest_frame())
        require(f.pc() == STATE['symbols']['outer'], 'outer_entry_pc')
        tid = thread()
        font, string = reg(f, 'rdi'), reg(f, 'rsi')
        require(font != 0 and digit_at(string) == p['digit'], 'outer_string_or_font')
        if bound_thread is None:
            bound_thread, bound_font = tid, font
        require(tid == bound_thread and font == bound_font, 'outer_thread_or_font_changed')
        active = {'index': p['index'], 'digit': p['digit'], 'thread': tid, 'font': font,
                  'string_address': string, 'phase': p, 'native_entered': False,
                  'native_returned': False, 'outer_entry_sp': reg(f, 'rsp')}
        pending_action = 'START_CALL'
        return True


class NativeEntry(gdb.Breakpoint):
    @guarded
    def stop(self):
        global bound_device, pending_action
        require(active is not None and not active['native_entered'] and thread() == active['thread'],
                'extra_or_foreign_native_entry')
        require(phase() == active['phase'], 'phase_changed_during_call')
        f = frame_ok(gdb.newest_frame())
        require(f.pc() == STATE['symbols']['native'], 'native_entry_pc')
        caller = frame_ok(f.older())
        expected_return = STATE['symbols']['native_return']
        require(caller.pc() == expected_return, 'native_caller_return_pc')
        sp = reg(f, 'rsp')
        require(memint(sp, 8) == expected_return, 'native_stack_return_pc')
        require(reg(f, 'rsi') == active['string_address']
                and digit_at(reg(f, 'rsi')) == active['digit'], 'native_string_binding')
        require(reg(f, 'rdx') == 0 and (reg(f, 'rcx') & 0xffffffff) == 0xffffffff
                and reg(f, 'r8') == reg(f, 'r9') == 0, 'native_span_or_layout_arguments')
        device = reg(f, 'rdi')
        require(device != 0, 'null_device')
        if bound_device is None:
            bound_device = device
        require(device == bound_device, 'device_changed')
        active.update(device=device, native_entered=True, native_entry_sp=sp,
                      native_return_pc=expected_return)
        pending_action = 'CONTINUE'
        return True


class NativeReturn(gdb.Breakpoint):
    @guarded
    def stop(self):
        global pending_action
        require(active is not None and active['native_entered'] and not active['native_returned']
                and thread() == active['thread'], 'extra_or_unmatched_native_return')
        require(phase() == active['phase'], 'phase_changed_during_call')
        f = frame_ok(gdb.newest_frame())
        require(f.pc() == STATE['symbols']['native_return'], 'native_return_pc')
        require(reg(f, 'rsp') == active['native_entry_sp'] + 8, 'native_return_stack')
        value = reg(f, 'rax')
        active.update(raw_native=value - (1 << 64) if value >= (1 << 63) else value,
                      native_returned=True)
        pending_action = 'CONTINUE'
        return True


def address(symbol):
    # Exact pinned mangled symbol, not the nonvirtual thunk; no debugtypes needed.
    require(all(c.isalnum() or c == '_' for c in symbol), 'symbol_spelling')
    return int(gdb.parse_and_eval("(unsigned long)&'" + symbol + "'"))


def install(_event=None):
    global installed, entry_bp, return_bp, outer_bp
    if helper is not None and not STATE['error']:
        try:
            helper.install()
        except Exception as exc:
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
    if installed or STATE['error'] or (helper is not None and gdb.selected_inferior().num != 1):
        return
    try:
        o, n = address(CFG['outer_symbol']), address(CFG['native_symbol'])
    except gdb.error:
        return  # Wait for exact shared object; final result rejects never-resolved symbols.
    try:
        owner = gdb.solib_name(o) or CFG['target_path']
        require(str(Path(owner).resolve()) == CFG['symbol_file_path'], 'symbol_owner')
        require((gdb.solib_name(n) or CFG['target_path']) == owner, 'native_symbol_owner')
        pin(CFG['symbol_file_path'], CFG['symbol_file_sha256'])
        require(n - o == CFG['native_offset'] - CFG['outer_offset'], 'symbol_offsets')
        ret = o + CFG['return_delta']
        memory = gdb.selected_inferior().read_memory(ret, len(bytes.fromhex(CFG['return_bytes']))).tobytes()
        require(memory.hex() == CFG['return_bytes'], 'return_site_bytes')
        STATE['symbols'] = {'outer': o, 'native': n, 'native_return': ret}
        outer_bp = OuterEntry('*' + hex(o), internal=True)
        entry_bp = NativeEntry('*' + hex(n), internal=True)
        return_bp = NativeReturn('*' + hex(ret), internal=True)
        if helper is not None:
            for bp in (outer_bp, entry_bp, return_bp):
                bp.inferior = 1
                require(bp.inferior == 1, 'metric_breakpoint_original_inferior')
        entry_bp.enabled = return_bp.enabled = False
        require(helper is None or helper.installed, 'helper_observer_not_installed')
        installed = True
        identity()
        STATE['status'] = 'READY_UNRELEASED'
        save()
    except Exception as exc:
        fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)


def boundary_symbol(value, limit):
    # Symbol/module metadata only. Never format a frame, argument, value or path.
    if value is None:
        return None
    return ''.join(c if 32 <= ord(c) < 127 else '?' for c in value[:limit])


def boundary_proc_identity(pid):
    # Numeric Linux identity only; never retain comm, argv, environ or exe path.
    with Path('/proc/' + str(pid) + '/stat').open('r', encoding='ascii') as f:
        raw = f.read(4097)
    require(len(raw) <= 4096, 'boundary_stat_bound')
    fields = raw.rsplit(')', 1)[1].split()
    return {'pid': pid, 'ppid': int(fields[1]), 'start_ticks': int(fields[19])}


def process_boundary_snapshot():
    # Refusal-only best effort while stopped. No GDB commands, inferior calls,
    # argument/local/register/payload reads, resume, breakpoint changes or writes.
    result = {'schema': 'frw.process-boundary-symbols.v1',
              'purpose': 'REFUSAL_DIAGNOSTIC_ONLY', 'gdb_pid': os.getpid(),
              'known_process': STATE['process'], 'frames': []}
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
        if (known is not None and inf.pid == known['pid'] and ptid is not None
                and len(ptid) == 3 and all(type(v) is int and v >= 0 for v in ptid)
                and ptid[0] == inf.pid and ptid[1] > 0):
            parent = boundary_proc_identity(inf.pid)
            result['selected_process_identity'] = parent
            # Children belong to the exact selected parent LWP, not a /proc scan.
            if parent['ppid'] == os.getpid() and parent['start_ticks'] == known['start_ticks']:
                p = Path('/proc/' + str(inf.pid) + '/task/' + str(ptid[1]) + '/children')
                with p.open('r', encoding='ascii') as f:
                    children = f.read(257)
                require(len(children) <= 256, 'boundary_children_bound')
                pids = children.split()
                require(all(v.isdecimal() and 0 < int(v) <= 2147483647 for v in pids),
                        'boundary_children_numeric')
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
            result['frames'].append({'pc': pc, 'kind': int(f.type()),
                'symbol': boundary_symbol(f.name(), 256),
                'module_basename': boundary_symbol(Path(module).name, 128) if module else None})
            f = f.older()
        result['frames_truncated'] = f is not None
    except Exception as exc:
        result['stack_exception_class'] = type(exc).__name__
    return result


def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        fail('unexpected_signal')
    elif helper is not None and isinstance(event, gdb.BreakpointEvent):
        try:
            if helper.queue_stop(event):
                return
            if any(b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
                helper.boundary(event)
                return
        except Exception as exc:
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
    elif isinstance(event, gdb.BreakpointEvent) and any(
            b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
        try:
            STATE['process_boundary_diagnostic'] = process_boundary_snapshot()
        except Exception as exc:
            STATE['process_boundary_diagnostic'] = {'exception_class': type(exc).__name__}
        fail('unexpected_fork_vfork_exec')


def exited(event):
    if helper is not None:
        try:
            if helper.exited(event):
                return
        except Exception as exc:
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            return
    STATE['exit_code'] = getattr(event, 'exit_code', None)


def load_helper():
    # Optional explicit pinned bundle; absence preserves the original ABI path.
    raw_ref = os.environ.get('FRW_NATIVE_LOAD_DEPENDENCY_REF')
    if raw_ref is None:
        return None
    require(CFG['kind'] == 'OFFICE_UNADMITTED', 'helper_only_explicit_Office_contract')
    ref = json.loads(raw_ref)
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'helper_bundle_ref')
    def read(r):
        p = Path(r['path'])
        require(p.is_absolute() and str(p.resolve()) == str(p) and p.is_file(), 'helper_bundle_path')
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            st = os.fstat(fd)
            require(st.st_nlink == 1 and not st.st_mode & 0o022 and st.st_size <= 262144,
                    'helper_bundle_rights_bound')
            raw = os.read(fd, 262145)
        finally:
            os.close(fd)
        require(len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == r['sha256'], 'helper_bundle_pin')
        return raw
    bundle = json.loads(read(ref))
    adapter = bundle['adapter_ref']
    namespace = {'__name__': 'frw_pinned_paper_GDB', '__file__': adapter['path']}
    exec(compile(read(adapter), adapter['path'], 'exec'), namespace)
    native = dict(globals(), get_active=lambda: active)
    return namespace['create'](gdb, native, ref)


def main():
    global pending_action, helper
    require(CFG['kind'] in ('ABI_FIXTURE_ONLY', 'OFFICE_UNADMITTED'), 'kind')
    require(type(CFG['nonce']) is str and len(CFG['nonce']) == 32
            and all(c in '0123456789abcdef' for c in CFG['nonce']), 'nonce')
    require(len(gdb.inferiors()) == 1 and gdb.selected_inferior().pid == 0,
            'preexisting_inferior_forbidden')
    require(gdb.current_progspace().filename == CFG['target_path'], 'launch_target')
    pin(CFG['target_path'], CFG['target_sha256'])
    pin(CFG['symbol_file_path'], CFG['symbol_file_sha256'])
    require(Path(CFG['target_path']).read_bytes()[:6] == b'\x7fELF\x02\x01', 'ELF64_LE_required')
    helper = load_helper()
    for setting in ['set pagination off', 'set confirm off', 'set startup-with-shell off', 'set non-stop off',
                    'set debuginfod enabled off', 'set disable-randomization off',
                    'set follow-fork-mode parent', 'set detach-on-fork off',
                    'set follow-exec-mode same', 'set print thread-events off', 'set stop-on-solib-events 1']:
        gdb.execute(setting, to_string=True)
    # Fork/vfork/exec after startup is an unreviewed process boundary; stop, then kill own inferior.
    for kind in ('fork', 'vfork', 'exec'):
        before = {b.number for b in (gdb.breakpoints() or ())}
        gdb.execute('catch ' + kind, to_string=True)
        for bp in gdb.breakpoints():
            if bp.number not in before:
                catchpoints[bp.number] = kind
    if helper is not None:
        helper.catchpoints = dict(catchpoints)
        gdb.execute('set schedule-multiple on', to_string=True)
        gdb.execute('handle SIGCHLD nostop noprint pass', to_string=True)
    gdb.events.new_objfile.connect(install)
    gdb.events.exited.connect(exited)
    gdb.events.stop.connect(stopped)
    gdb.execute('starti', to_string=True)
    identity()
    install()
    for _ in range(256):
        require(STATE['error'] is None, 'installation_refused')
        if installed:
            break
        require(gdb.selected_inferior().pid > 0, 'exit_before_symbols')
        gdb.execute('continue', to_string=True)
        install()
    require(installed, 'symbols_unresolved')
    gdb.execute('set stop-on-solib-events 0', to_string=True)
    while any(i.num == 1 and i.pid for i in gdb.inferiors()):
        gdb.execute('continue', to_string=True)
        require(STATE['error'] is None, 'trace_refused')
        helper_action = helper.dispatch() if helper is not None else None
        if helper is not None and not gdb.selected_inferior().pid:
            helper.original_selected()
        if not any(i.num == 1 and i.pid for i in gdb.inferiors()):
            break
        require(helper_action is None or pending_action is None, 'helper_metric_stop_collision')
        action, pending_action = helper_action or pending_action, None
        require(action in ('START_CALL', 'END_CALL', 'CONTINUE'), 'unrecognized_stop')
        # GDB documents that Breakpoint.stop must not mutate breakpoints. All
        # finish creation and enabling/disabling occur here, outside callbacks.
        if action == 'START_CALL':
            finish = OuterFinish(frame_ok(gdb.newest_frame()), active)
            if helper is not None:
                finish.inferior = 1
            entry_bp.enabled = return_bp.enabled = True
        elif action == 'END_CALL':
            entry_bp.enabled = return_bp.enabled = False
    require(STATE['error'] is None, 'trace_refused')
    require(gdb.selected_inferior().pid == 0 and STATE['exit_code'] == 0, 'unknown_stop_or_exit')
    require(installed and active is None and len(STATE['records']) == 10, 'incomplete_trace')
    require(phase()['phase'] == 'CLOSED', 'phase_not_closed')
    require(not Path('/proc/' + str(STATE['process']['pid'])).exists(), 'process_cleanup_unknown')
    STATE['status'] = 'COMPLETE_FIXTURE_ONLY' if CFG['kind'] == 'ABI_FIXTURE_ONLY' else 'COMPLETE_UNATTESTED'
    save()


try:
    main()
except Exception as exc:
    fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
finally:
    # The only initial inferior was empty, and every later inferior derives from
    # this launch. Refused unexpected descendants remain under outer cgroup
    # containment; never mistake killing the selected helper for Office cleanup.
    if helper is None:
        if STATE['process'] is not None and gdb.selected_inferior().pid:
            try:
                identity()
                gdb.execute('kill', to_string=True)
            except Exception:
                STATE['error'] = 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
                STATE['status'] = 'REFUSED'
        STATE['own_inferior_absent'] = (gdb.selected_inferior().pid == 0 and
            (STATE['process'] is None or not Path('/proc/' + str(STATE['process']['pid'])).exists()))
    else:
        cleanup_pids = set(helper.known)
        for inf in gdb.inferiors():
            if not inf.pid:
                continue
            try:
                before = helper.proc(inf.pid)
                cleanup_pids.add(inf.pid)
                gdb.execute('inferior ' + str(inf.num), to_string=True)
                require(helper.proc(inf.pid) == before, 'cleanup_process_birth_changed')
                gdb.execute('kill', to_string=True)
            except Exception:
                STATE['cleanup_error'] = 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
                STATE['error'] = STATE['error'] or 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
                STATE['status'] = 'REFUSED'
        STATE['own_inferior_absent'] = (all(i.pid == 0 for i in gdb.inferiors()) and
            all(not Path('/proc/' + str(pid)).exists() for pid in cleanup_pids))
        if not STATE['own_inferior_absent']:
            STATE['cleanup_error'] = 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
            STATE['error'] = STATE['error'] or 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
            STATE['status'] = 'REFUSED'
    save()
    gdb.execute('quit ' + ('0' if STATE['status'].startswith('COMPLETE_') else '2'))
