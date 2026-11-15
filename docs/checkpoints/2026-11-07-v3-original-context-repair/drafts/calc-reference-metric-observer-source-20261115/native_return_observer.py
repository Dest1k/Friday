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
        require(type(value['index']) is int and 0 <= value['index'] <= 9
                and value['digit'] == str(value['index']), 'phase_digit')
    else:
        require(value['index'] is None and value['digit'] is None, 'inactive_phase_payload')
    return value


def identity():
    inf = gdb.selected_inferior()
    require(len(gdb.inferiors()) == 1 and inf.num == 1 and inf.pid > 0, 'inferior_identity')
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
    if installed or STATE['error']:
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
        entry_bp.enabled = return_bp.enabled = False
        installed = True
        identity()
        STATE['status'] = 'READY_UNRELEASED'
        save()
    except Exception as exc:
        fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)


def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        fail('unexpected_signal')
    elif isinstance(event, gdb.BreakpointEvent) and any(
            b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
        fail('unexpected_fork_vfork_exec')


def exited(event):
    STATE['exit_code'] = getattr(event, 'exit_code', None)


def main():
    global pending_action
    require(CFG['kind'] in ('ABI_FIXTURE_ONLY', 'OFFICE_UNADMITTED'), 'kind')
    require(type(CFG['nonce']) is str and len(CFG['nonce']) == 32
            and all(c in '0123456789abcdef' for c in CFG['nonce']), 'nonce')
    require(len(gdb.inferiors()) == 1 and gdb.selected_inferior().pid == 0,
            'preexisting_inferior_forbidden')
    require(gdb.current_progspace().filename == CFG['target_path'], 'launch_target')
    pin(CFG['target_path'], CFG['target_sha256'])
    pin(CFG['symbol_file_path'], CFG['symbol_file_sha256'])
    require(Path(CFG['target_path']).read_bytes()[:6] == b'\x7fELF\x02\x01', 'ELF64_LE_required')
    for setting in ['set pagination off', 'set confirm off', 'set startup-with-shell off', 'set non-stop off',
                    'set debuginfod enabled off', 'set disable-randomization off',
                    'set follow-fork-mode parent', 'set detach-on-fork off',
                    'set follow-exec-mode same', 'set print thread-events off', 'set stop-on-solib-events 1']:
        gdb.execute(setting, to_string=True)
    # Fork/vfork/exec after startup is an unreviewed process boundary; stop, then kill own inferior.
    gdb.execute('catch fork', to_string=True)
    gdb.execute('catch vfork', to_string=True)
    gdb.execute('catch exec', to_string=True)
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
    while gdb.selected_inferior().pid:
        gdb.execute('continue', to_string=True)
        require(STATE['error'] is None, 'trace_refused')
        if not gdb.selected_inferior().pid:
            break
        action, pending_action = pending_action, None
        require(action in ('START_CALL', 'END_CALL', 'CONTINUE'), 'unrecognized_stop')
        # GDB documents that Breakpoint.stop must not mutate breakpoints. All
        # finish creation and enabling/disabling occur here, outside callbacks.
        if action == 'START_CALL':
            OuterFinish(frame_ok(gdb.newest_frame()), active)
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
    # Only this launch's exact direct child. Unknown/forked process state is never released.
    if STATE['process'] is not None and gdb.selected_inferior().pid:
        try:
            identity()
            gdb.execute('kill', to_string=True)
        except Exception:
            STATE['error'] = 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
            STATE['status'] = 'REFUSED'
    STATE['own_inferior_absent'] = (gdb.selected_inferior().pid == 0 and
        (STATE['process'] is None or not Path('/proc/' + str(STATE['process']['pid'])).exists()))
    save()
    gdb.execute('quit ' + ('0' if STATE['status'].startswith('COMPLETE_') else '2'))
