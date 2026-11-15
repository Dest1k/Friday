"""Independent inert controls of exact source; no GDB, procfs or ELF execution."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import types

SOURCE = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-COMPLETE-OBSERVER-SOURCE-20261115')
OWN = Path(__file__).resolve().parent


def load(path):
    scope = {'__file__': str(path), '__name__': 'inert_independent_source'}
    exec(compile(path.read_bytes(), str(path), 'exec'), scope)
    return types.SimpleNamespace(**scope)


P = load(SOURCE / 'candidate/outer/deps/gpgme_engine_policy.py')
PROFILE = dict(schema=P.SCHEMA, stage=P.STAGE,
    library=dict(path=P.LIBRARY_PATH, sha256=P.LIBRARY_SHA256, build_id=P.BUILD_ID),
    source_manifest_ref=P.SOURCE_MANIFEST, conditional_join_ref=P.CONDITIONAL_JOIN,
    branches=[dict(branch=b, role=P.ROLES[b], option=P.OPTIONS[b]) for b in P.BRANCHES],
    pseudo_protocols=list(P.UNSUPPORTED), runtime_available=False,
    budgets=dict(wall_seconds=240, cpu_seconds=120, memory_bytes=2147483648,
        deadline_rule='SAME_ORIGINAL_ABSOLUTE_OPERATION_DEADLINE_NO_RESET'))
ORIGINAL = dict(pid=101, ppid=55, start_ticks=10)
REAPER = dict(pid=1, ppid=0, start_ticks=1)
OP = dict(operation_id='PURE_INDEPENDENT', nonce='c' * 32, deadline_monotonic=500.0)
CTX = dict(OP, now=1.0, original=ORIGINAL, all_stop=True, phase='LOAD_OPEN', records_count=0,
    metric_active=False, library_current_bound=True, environment_current_bound=True,
    configuration_isolated=True, resource_custody_bound=True)
ENV = dict(P.ISOLATED)
HELPERS = {role: dict(path='/inert/' + role, sha256=hashlib.sha256(role.encode()).hexdigest(),
    dev=1, ino=i+10) for i, role in enumerate(('gpgconf', 'gpg', 'gpgsm', 'g13'))}
R = dict(dev=1, ino=555, type=stat.S_IFIFO, rdev=0, access=0, cloexec=True)
W = dict(R, access=1, cloexec=False)
NULL = dict(dev=1, ino=3, type=stat.S_IFCHR, rdev=259, access=2, cloexec=False)
BASE, LIBC_BASE = 0x400000, 0x900000


def need_reject(call, reason):
    try:
        call()
    except RuntimeError as exc:
        assert str(exc) == reason, (str(exc), reason)
        return str(exc)
    raise AssertionError('unexpected acceptance: ' + reason)


def policy(mode='COLD_GPGCONF'):
    return P.EngineInitPreparation(PROFILE, ORIGINAL, OP, ENV, source_mode=mode,
        helpers=HELPERS, reaper=REAPER)


def arm(c, branch):
    image = HELPERS[P.ROLES[branch]]
    c.arm(CTX, branch, [101, 101, 0], [image['path'], P.OPTIONS[branch]], image, R, W,
        source_route=branch)


def births(c, pid, inferior):
    first, final = dict(pid=pid, ppid=101, start_ticks=pid), dict(pid=pid+1, ppid=pid, start_ticks=pid+1)
    c.birth(CTX, ORIGINAL, first, inferior, event='fork', return_offset=P.FIRST_FORK_RETURN,
        thread=[101, 101, 0])
    c.birth(CTX, first, final, inferior+1, event='fork', return_offset=P.SECOND_FORK_RETURN,
        thread=[pid, pid, 0])
    return first, final


def complete_protocol(c, first, final, inferior, *, zombie=False):
    image = HELPERS[c.current['role']]
    c.exec_before_execution(CTX, final, image, [image['path'], P.OPTIONS[c.current['branch']]],
        {0: NULL, 1: W, 2: NULL}, ENV, null_rdev=259, event='exec_before_first_instruction')
    c.entry(CTX, final, image_and_exact_dependency_set_bound=True)
    c.exit(CTX, first, inferior, 0, absent=not zombie)
    reparented = dict(final, ppid=1)
    c.reparent(CTX, reparented, exact_reaper_identity=REAPER, old_parent_absent=not zombie)
    c.spawn_return(CTX, [101, 101, 0], 0)
    c.pipe_terminal(CTX, [101, 101, 0], c.current['pipe'], read_closed=True,
        terminal='OBSERVED_READ_EOF')
    c.exit(CTX, reparented, inferior+1, 0, absent=not zombie)
    return reparented


class NoProcPath:
    def __init__(self, *parts):
        self.parts = parts
    def __truediv__(self, other):
        return self
    def exists(self):
        return False


def adapter(path):
    A = load(path)
    # Replace the namespace used by methods, not any shared stdlib object.
    A.Adapter.try_close.__globals__['Path'] = NoProcPath
    a = A.Adapter.__new__(A.Adapter)
    a.p = vars(P)
    a.c = policy()
    a.binding = dict(load_bias=BASE)
    a.clone_entries = set()
    a.context = lambda **kwargs: (copy.deepcopy(CTX), {'inert': True})
    a.original = lambda: copy.deepcopy(ORIGINAL)
    a.collector = types.SimpleNamespace(image_binding=lambda *args: dict(relative_pc=A.LIBC_FORK_SYSCALL_RETURN),
        no_pipe_writer_or_descendant=lambda *args: True)
    a.m = dict(collector_pins=dict(libc={}))
    a.observations = []
    a.pipe_fd, a.write_fd, a.read_terminal = 5, 6, None
    a.caller_route = a.caller_thread = None
    state = dict(pid=101, offset=P.FIRST_FORK_RETURN, rax=-38, flags=0x1200011)
    def frame(older=False):
        return types.SimpleNamespace(is_valid=lambda: True,
            pc=lambda: BASE + state['offset'] if older else LIBC_BASE + A.LIBC_FORK_SYSCALL_RETURN,
            older=lambda: None if older else frame(True))
    a.g = types.SimpleNamespace(newest_frame=frame,
        selected_inferior=lambda: types.SimpleNamespace(pid=state['pid']))
    a.tid = lambda: [state['pid'], state['pid'], 0]
    a.reg = lambda key: dict(orig_rax=56, rsi=0, rdx=0, r8=0, r10=0x1000,
        rdi=state['flags'])[key]
    a.signed = lambda *args: state['rax']
    a.memory = lambda *args: bytes.fromhex(A.LIBC_FORK_SYSCALL_BYTES)
    return a, state


def sequential_clone_control(path):
    a, state = adapter(path)
    closed = []
    for i, branch in enumerate(P.BRANCHES):
        a.observations = []  # The real spawn_entry likewise resets this list.
        a.pipe_fd = 5
        arm(a.c, branch)
        state.update(pid=101, offset=P.FIRST_FORK_RETURN)
        try:
            a.clone_guard()
        except RuntimeError as exc:
            return dict(first_invocation_closed=bool(closed), second_clone_accepted=False,
                failed_branch=branch, reason=str(exc), retained_keys=sorted(a.clone_entries),
                closed_branches=closed)
        first, final = births(a.c, 201+2*i, 4+2*i)
        state.update(pid=first['pid'], offset=P.SECOND_FORK_RETURN)
        a.clone_guard()
        complete_protocol(a.c, first, final, 4+2*i)
        assert a.try_close(copy.deepcopy(CTX), {'inert': branch}) is True
        closed.append(branch)
    a.c.finish_initialization(CTX, exact_engine_info_return=True, known_no_more_spawn=True)
    return dict(first_invocation_closed=True, second_clone_accepted=True,
        retained_keys=sorted(a.clone_entries), closed_branches=closed, policy_closed=a.c.closed)


def run(path):
    results = {}
    results['consecutive_discovery_clone'] = sequential_clone_control(path)
    a, state = adapter(path)
    arm(a.c, 'list_dirs')
    a.clone_guard()
    results['duplicate_clone_same_invocation'] = need_reject(a.clone_guard,
        'gpgme_clone_fork_flags_or_thread')
    a, state = adapter(path)
    arm(a.c, 'list_dirs')
    state['flags'] |= 0x100  # CLONE_VM is not granted.
    results['unsupported_clone_flags'] = need_reject(a.clone_guard,
        'gpgme_clone_fork_flags_or_thread')

    a, state = adapter(path)
    arm(a.c, 'list_dirs')
    a.clone_guard()
    first, final = births(a.c, 201, 4)
    state.update(pid=201, offset=P.SECOND_FORK_RETURN)
    a.clone_guard()
    complete_protocol(a.c, first, final, 4, zombie=True)
    before = set(a.clone_entries)
    assert a.try_close(CTX, {'inert': 'still-zombies'}) is False
    results['clone_keys_retained_until_actual_absence'] = bool(before) and a.clone_entries == before

    c = policy()
    arm(c, 'list_dirs')
    first, final = births(c, 201, 4)
    reparented = complete_protocol(c, first, final, 4, zombie=True)
    invalid = copy.deepcopy(c)
    results['zombies_not_closed'] = need_reject(lambda: invalid.close_invocation(CTX,
        no_writer_or_other_descendant=True, pipe_read_end_absent=True), 'gpgme_invocation_not_closed')
    c.observe_absence(CTX, first, 4)
    c.observe_absence(CTX, reparented, 5)
    c.close_invocation(CTX, no_writer_or_other_descendant=True, pipe_read_end_absent=True)
    results['observed_exit_then_reparent_before_absence_then_closure'] = c.current is None

    c = policy()
    arm(c, 'list_dirs')
    first = dict(pid=201, ppid=101, start_ticks=201)
    c.birth(CTX, ORIGINAL, first, 4, event='fork', return_offset=P.FIRST_FORK_RETURN, thread=[101,101,0])
    c.current['children'][0]['exit_code'] = 0
    results['second_birth_after_observed_exit'] = need_reject(lambda: c.birth(CTX, first,
        dict(pid=202, ppid=201, start_ticks=202), 5, event='fork',
        return_offset=P.SECOND_FORK_RETURN, thread=[201,201,0]), 'gpgme_second_fork_after_parent_exit')
    results['first_refusal_persists'] = need_reject(lambda: c.finish_initialization(CTX,
        exact_engine_info_return=True, known_no_more_spawn=True), 'gpgme_second_fork_after_parent_exit')

    c = policy()
    arm(c, 'list_dirs')
    later = dict(CTX, now=500.0)
    results['absolute_deadline_not_reset'] = need_reject(lambda: c.birth(later, ORIGINAL,
        first, 4, event='fork', return_offset=P.FIRST_FORK_RETURN, thread=[101,101,0]),
        'gpgme_original_deadline_expired')

    # Complete all six policy invocations in one instance; none is given a clock.
    c = policy()
    for i, branch in enumerate(P.BRANCHES):
        arm(c, branch)
        first, final = births(c, 300+2*i, 4+2*i)
        complete_protocol(c, first, final, 4+2*i)
        c.close_invocation(CTX, no_writer_or_other_descendant=True, pipe_read_end_absent=True)
    c.finish_initialization(CTX, exact_engine_info_return=True, known_no_more_spawn=True)
    results['six_branches_one_policy_one_deadline'] = c.closed and len(c.invocations) == 6
    return results


if __name__ == '__main__':
    original = SOURCE / 'candidate/outer/deps/gpgme_engine_gdb.py'
    repaired = OWN / 'repair-copy/gpgme_engine_gdb.py'
    report = dict(original=run(original), repaired=run(repaired),
        runtime_executed=False, gdb_or_elf_executed=False)
    assert report['original']['consecutive_discovery_clone']['second_clone_accepted'] is False
    assert report['original']['consecutive_discovery_clone']['reason'] == 'gpgme_clone_fork_flags_or_thread'
    assert report['repaired']['consecutive_discovery_clone']['second_clone_accepted'] is True
    print(json.dumps(report, indent=2, sort_keys=True))
