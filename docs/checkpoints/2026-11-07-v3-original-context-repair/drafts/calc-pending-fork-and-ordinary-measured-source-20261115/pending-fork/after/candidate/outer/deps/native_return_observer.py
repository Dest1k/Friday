"""GDB-only, launch-only, exact x86-64 observer. No Office admission is issued.
The outer return-site breakpoint reads RAX before its first narrowing instruction.
No inferior function calls, writes, forced returns, stepping or foreign attach.
"""
import gdb
import hashlib
import json
import os
import math
import stat
import time
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
font_runtime_boundaries = []


def font_file(boundary, kind):
    require(boundary in ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'), 'font_runtime_boundary')
    require(kind in ('request', 'proof', 'release', 'accepted', 'view'), 'font_runtime_file_kind')
    tag = 'loaded' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'closed'
    name = ('font-view-after-load.json' if tag == 'loaded' else 'font-view-after-close.json') if kind == 'view' else (
        'font-runtime-' + tag + '-' + kind + '.json')
    require(Path(CFG['phase_path']).parent == Path('/tmp/friday-metric-work'), 'font_runtime_work')
    return Path(CFG['phase_path']).with_name(name)


def font_read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == 0o600 and before.st_size <= 32768,
                'font_runtime_file_rights_bound')
        raw = os.read(fd, 32769)
        after = os.fstat(fd)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(len(raw) <= 32768 and stamp(before) == stamp(after) == stamp(path.lstat()),
                'font_runtime_file_changed')
    finally:
        os.close(fd)
    return raw


def font_write(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    require(len(raw) <= 32768 and not os.path.lexists(path), 'font_runtime_future_or_duplicate_proof')
    temporary = path.with_name(path.name + '.pending')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    require(not os.path.lexists(path), 'font_runtime_future_or_duplicate_proof')
    os.replace(temporary, path)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


def capture_font_runtime():
    """One requested all-stop point; never claim stability between points.

    The sole namespace supervisor sends SIGSTOP through a birth-bound pidfd.
    GDB suppresses delivery. No inferior function/write/step/thread change occurs.
    Hold this stop through the namespace font CAS, then accept its exact release.
    Technical signal behavior still requires a real owned fixture before Office.
    """
    require(helper is not None and CFG['kind'] in ('OFFICE_UNADMITTED', 'OWN_POPEN_FIXTURE_ONLY')
            and active is None and len(font_runtime_boundaries) < 2, 'font_runtime_observer_scope')
    identity()
    helper.metric_ready()
    sequence = len(font_runtime_boundaries)
    boundary = ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE')[sequence]
    phase_value = {'nonce': CFG['nonce'], 'phase': 'IDLE' if sequence == 0 else 'CLOSED',
                   'index': None, 'digit': None}
    require(phase() == phase_value and len(STATE['records']) == sequence * 10,
            'font_runtime_phase_or_call_count')
    request_path = font_file(boundary, 'request')
    request_raw = font_read(request_path)
    request = json.loads(request_raw)
    keys = {'schema', 'operation_id', 'nonce', 'boundary', 'sequence', 'process', 'supervisor',
            'deadline_monotonic', 'requested_monotonic'}
    require(type(request) is dict and set(request) == keys
            and request['schema'] == 'frw.calc.font-runtime-request.v1'
            and request['operation_id'] == helper.b['runtime']['operation_id']
            and request['nonce'] == CFG['nonce'] and request['boundary'] == boundary
            and type(request['sequence']) is int and request['sequence'] == sequence
            and request['process'] == STATE['process'], 'font_runtime_request_binding')
    deadline = helper.b['runtime']['operation_deadline_monotonic']
    require(type(request['deadline_monotonic']) in (int, float)
            and math.isfinite(request['deadline_monotonic']) and request['deadline_monotonic'] == deadline
            and type(request['requested_monotonic']) in (int, float) and math.isfinite(request['requested_monotonic'])
            and 0 < request['requested_monotonic'] <= time.monotonic() < deadline,
            'font_runtime_original_deadline')
    supervisor = boundary_proc_identity(os.getppid())
    require(request['supervisor'] == supervisor, 'font_runtime_request_supervisor_birth')
    # These are GDB's kernel signal metadata, not inferior code evaluation.
    sig = lambda expression: int(gdb.parse_and_eval('$_siginfo.' + expression))
    require(sig('si_signo') == 19 and sig('si_code') == 0
            and sig('_sifields._kill.si_pid') == supervisor['pid']
            and sig('_sifields._kill.si_uid') == os.getuid(), 'font_runtime_signal_sender')
    release_path = font_file(boundary, 'release')
    require(not os.path.lexists(release_path), 'font_runtime_future_release')
    inf = identity()
    threads = list(inf.threads())
    require(0 < len(threads) <= 512 and all(t.is_valid() and t.is_stopped() for t in threads),
            'font_runtime_all_threads_stopped')
    env = helper.current_environment(inf.pid)
    request_ref = {'path': str(request_path), 'sha256': hashlib.sha256(request_raw).hexdigest()}
    keys15 = (b'HOME', b'TMPDIR', b'XDG_CACHE_HOME', b'XDG_CONFIG_HOME', b'XDG_DATA_HOME',
        b'FONTCONFIG_FILE', b'FONTCONFIG_PATH', b'FONTCONFIG_SYSROOT', b'FC_LANG', b'LANG', b'LC_ALL',
        b'SAL_FONTPATH', b'SAL_USE_VCLPLUGIN', b'LD_LIBRARY_PATH', b'URE_BOOTSTRAP')
    proof = {'schema': 'frw.calc.current-font-environment.v1', 'operation_id': request['operation_id'],
        'nonce': CFG['nonce'], 'boundary': boundary, 'sequence': sequence, 'process': STATE['process'],
        'supervisor': supervisor, 'request_ref': request_ref, 'phase': phase_value,
        'records_count': len(STATE['records']), 'stopped_thread_count': len(threads),
        'source_class': 'PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON',
        'adapter_ref': helper.b['adapter_ref'], 'libc_sha256': helper.m['images']['libc']['sha256'],
        'font_environment': [{'key': key.decode('ascii'), 'value_sha256':
            hashlib.sha256(env[key]).hexdigest() if key in env else None} for key in keys15],
        'scope': 'THIS_ALL_STOP_POINT_ONLY_NO_CONTINUOUS_ENVIRONMENT_CLAIM',
        'actual_M': None, 'runtime_attested': False}
    # The projection must remain the exact fixed 15 keys, independent of audit metadata limits.
    require([row['key'] for row in proof['font_environment']] == [key.decode('ascii') for key in keys15],
            'font_runtime_exact_projection')
    proof_ref = font_write(font_file(boundary, 'proof'), proof)
    while not os.path.lexists(release_path):
        require(time.monotonic() < deadline, 'font_runtime_release_original_deadline')
        time.sleep(min(0.02, max(0, deadline - time.monotonic())))
    release = json.loads(font_read(release_path))
    expected = {'schema': 'frw.calc.font-runtime-release.v1', 'operation_id': request['operation_id'],
        'nonce': CFG['nonce'], 'boundary': boundary, 'sequence': sequence, 'process': STATE['process'],
        'request_ref': request_ref, 'proof_ref': proof_ref, 'font_view_ref': release.get('font_view_ref')}
    require(release == expected and time.monotonic() < deadline, 'font_runtime_release_binding_or_deadline')
    view = expected['font_view_ref']
    require(type(view) is dict and set(view) == {'path', 'sha256'}
            and view['path'] == str(font_file(boundary, 'view'))
            and hashlib.sha256(font_read(font_file(boundary, 'view'))).hexdigest() == view['sha256'],
            'font_runtime_release_view_pin')
    require(font_read(request_path) == request_raw and phase() == phase_value
            and identity().pid == inf.pid and helper.current_environment(inf.pid) == env,
            'font_runtime_held_stop_changed')
    font_runtime_boundaries.append(proof_ref)
    font_write(font_file(boundary, 'accepted'), dict(schema='frw.calc.font-runtime-accepted.v1',
        **{key: request[key] for key in ('operation_id', 'nonce', 'boundary', 'sequence', 'process')},
        release_ref={'path': str(release_path), 'sha256': hashlib.sha256(font_read(release_path)).hexdigest()},
        status='HELD_STOP_RELEASE_VALIDATED_NO_RESUME_CLAIM'))


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
    global pending_action
    # A refusal can never leave a latent continuation or queued creation.
    pending_action = None
    if helper is not None:
        if hasattr(helper, 'clear_pending'):
            helper.clear_pending()
        else:
            helper.pending = None
            helper.pending_stop = None
            helper.to_create.clear()
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
            require(len(font_runtime_boundaries) == 1, 'font_runtime_loaded_proof_before_metric')
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
    global pending_action
    if STATE['error'] is not None:
        if helper is not None and hasattr(helper, 'clear_pending'):
            helper.clear_pending()
        return
    if helper is not None and hasattr(helper, 'materialization_stop'):
        try:
            if helper.materialization_stop(event):
                return
        except Exception as exc:
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            return
    if isinstance(event, gdb.SignalEvent):
        if (getattr(event, 'stop_signal', None) == 'SIGSTOP' and helper is not None
                and pending_action is None):
            pending_action = 'FONT_RUNTIME'
        else:
            fail('unexpected_signal')
    elif helper is not None and isinstance(event, gdb.BreakpointEvent):
        try:
            if helper.queue_stop(event):
                return
            if any(b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
                helper.boundary(event)
                return
        except Exception as exc:
            # The helper refuses unknown fork/catchpoint before the generic branch.
            # Keep that first refusal; add only the existing bounded symbol snapshot.
            if (STATE['error'] is None and type(exc) is RuntimeError
                    and str(exc) == 'helper_unexpected_fork_or_catchpoint'):
                try:
                    STATE['process_boundary_diagnostic'] = process_boundary_snapshot()
                except Exception as diagnostic_exc:
                    STATE['process_boundary_diagnostic'] = {'exception_class': type(diagnostic_exc).__name__}
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
    elif isinstance(event, gdb.BreakpointEvent) and any(
            b.type == gdb.BP_CATCHPOINT for b in event.breakpoints):
        try:
            STATE['process_boundary_diagnostic'] = process_boundary_snapshot()
        except Exception as exc:
            STATE['process_boundary_diagnostic'] = {'exception_class': type(exc).__name__}
        fail('unexpected_fork_vfork_exec')


def exited(event):
    if STATE['error'] is not None:
        if helper is not None and hasattr(helper, 'clear_pending'):
            helper.clear_pending()
        return
    if (helper is not None and hasattr(helper, 'gpgme')
            and helper.gpgme.fork_pending is not None):
        fail('gpgme_pending_fork_unexpected_exit')
        return
    if helper is not None:
        try:
            if helper.exited(event):
                return
        except Exception as exc:
            fail(str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            return
    STATE['exit_code'] = getattr(event, 'exit_code', None)


def load_helper():
    # Separate explicit GpgME bundle is loaded only alongside the unchanged
    # paper contract. This does not grant an operation or bypass Root admission.
    gpgme_ref = os.environ.get('FRW_NATIVE_GPGME_ENGINE_INIT_REF')
    # Optional explicit pinned bundle; absence preserves the original ABI path.
    raw_ref = os.environ.get('FRW_NATIVE_LOAD_DEPENDENCY_REF')
    if raw_ref is None:
        require(gpgme_ref is None, 'gpgme_requires_explicit_paper_contract')
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
    paper = namespace['create'](gdb, native, ref)
    if gpgme_ref is None:
        return paper
    gref = json.loads(gpgme_ref)
    gbundle = json.loads(read(gref))
    gadapter = gbundle['adapter_ref']
    gnamespace = {'__name__': 'frw_pinned_gpgme_GDB', '__file__': gadapter['path']}
    exec(compile(read(gadapter), gadapter['path'], 'exec'), gnamespace)
    gpgme = gnamespace['create'](gdb, native, gref, paper)
    require(os.environ.get('FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE') == gbundle['evidence_path'],
            'gpgme_explicit_evidence_path')
    return gnamespace['MultiCustody'](paper, gpgme)


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
    if helper is not None and hasattr(helper, 'gpgme'):
        # Debugger control refs must not become inferior ENV or a manifest
        # self-hash dependency. Keep GDB's own os.environ for pinned loaders.
        for name in ('FRW_NATIVE_OBSERVER_CONFIG', 'FRW_NATIVE_LOAD_DEPENDENCY_REF',
                     'FRW_NATIVE_GPGME_ENGINE_INIT_REF', 'FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE'):
            gdb.execute('unset environment ' + name, to_string=True)
    for setting in ['set pagination off', 'set confirm off', 'set startup-with-shell off', 'set non-stop off',
                    'set may-call-functions off',
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
        if hasattr(helper, 'gpgme'):
            helper.paper.catchpoints = dict(catchpoints)
            helper.gpgme.catchpoints = dict(catchpoints)
        else:
            helper.catchpoints = dict(catchpoints)
        gdb.execute('set schedule-multiple on', to_string=True)
        gdb.execute('handle SIGCHLD nostop noprint pass', to_string=True)
        gdb.execute('handle SIGSTOP noprint nopass stop', to_string=True)
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
        require(action in ('START_CALL', 'END_CALL', 'CONTINUE', 'FONT_RUNTIME', 'GPG_DRAIN'), 'unrecognized_stop')
        # GDB documents that Breakpoint.stop must not mutate breakpoints. All
        # finish creation and enabling/disabling occur here, outside callbacks.
        if action == 'START_CALL':
            finish = OuterFinish(frame_ok(gdb.newest_frame()), active)
            if helper is not None:
                finish.inferior = 1
            entry_bp.enabled = return_bp.enabled = True
        elif action == 'END_CALL':
            entry_bp.enabled = return_bp.enabled = False
        elif action == 'FONT_RUNTIME':
            capture_font_runtime()
        elif action == 'GPG_DRAIN':
            require(helper is not None and hasattr(helper, 'gpgme'), 'gpgme_drain_without_owner')
            helper.gpgme.drain()
    require(STATE['error'] is None, 'trace_refused')
    require(gdb.selected_inferior().pid == 0 and STATE['exit_code'] == 0, 'unknown_stop_or_exit')
    require(installed and active is None and len(STATE['records']) == 10, 'incomplete_trace')
    require(phase()['phase'] == 'CLOSED', 'phase_not_closed')
    require(helper is None or len(font_runtime_boundaries) == 2, 'font_runtime_both_boundaries_required')
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
                STATE['error'] = STATE['error'] or 'OWN_PROCESS_CLEANUP_UNCONFIRMED'
                STATE['status'] = 'REFUSED'
        STATE['own_inferior_absent'] = (gdb.selected_inferior().pid == 0 and
            (STATE['process'] is None or not Path('/proc/' + str(STATE['process']['pid'])).exists()))
    else:
        cleanup_pids = set(helper.known)
        if hasattr(helper, 'gpgme'):
            cleanup_pids.update(helper.gpgme.known)
            helper.clear_pending()
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
