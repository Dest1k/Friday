"""Root entry for one exact S01. Verification and reconciliation have no transport."""

import argparse
import ctypes
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager


HERE = Path(__file__).resolve().parent
DRIVER = HERE / 'ordinary_s01_root.py'
HOME = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
PYTHON = HOME / 'installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'
SCENARIO_SHA = '8a028fd974f9290f8cf978e7d2d7ab75f66cb2bb468606365f5e5512468b057d'
R4_SHA = '44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd'
ROUTE_SHA = 'e17b79dd1440bfc314ab988ec6f5c9f66cca0a41f49007ced2c24678d678a467'
ACTOR_PATH = HERE.parents[1] / 'ordinary-disk-monitor-next-source-20261116/root_f07_once.py'
ACTOR_SHA = '729efbd54ae5d12b61c0375964fdee817457c57544b08f79ca507215070ea5f5'
CURRENT_SHA = '2983e06dc5579adae0f0983d64d07b65c41f849b03dca0985f270d2547a9411b'
COMPOSER_SHA = '57a21c19d5c2fde2ad06a9800502bdb7a5001ddf1be004c98c6ffe609bc139f6'
ONCE_SHA = '9e2887f4e8d3e4f9ff2a8dbe98b5f35e8686044cb1cd27aa0be405c239454fc6'
RESOURCE_LIMITS = dict(cpu_seconds=600, max_rss_bytes=2 * 1024**3, disk_bytes=100 * 1024**2)
PR_SET_PDEATHSIG = 1


def load_actor():
    from hashlib import sha256
    from types import ModuleType

    raw = ACTOR_PATH.read_bytes()
    if sha256(raw).hexdigest() != ACTOR_SHA:
        raise ValueError('S01_ACTOR_SOURCE_CHANGED')
    actor = ModuleType('_Root_S01_existing_actor')
    actor.__file__ = str(ACTOR_PATH)
    exec(compile(raw, actor.__file__, 'exec'), actor.__dict__)
    return actor


def installed_module(actor, name, checksum):
    path = HERE / (name + '.py')
    raw = actor.read(path, limit=65536, private=False)
    actor.need(actor.digest(raw) == checksum, 'S01_OPERATOR_SOURCE_CHANGED')
    return actor.load_raw(raw, path, '_Root_S01_' + name)


def disk_paths(work, state, profile):
    profile_home = HOME / 'profiles' / profile
    directories = [work, state, HOME / 'logs', HOME / 'sessions',
                   profile_home / 'logs', profile_home / 'sessions', profile_home / 'workspace']
    paths = [HOME / 'gateway_state.json']
    for home in (HOME, profile_home, HOME / 'profiles' / 'dest_telegram'):
        paths.extend(home / name for name in ('state.db', 'state.db-shm', 'state.db-wal'))
    return sorted(map(str, directories)), sorted(map(str, paths))


def protected_work_identity(actor, work):
    dev, inode, uid, _, mode, *_ = actor.protected_directory(work)
    return dict(device=dev, inode=inode, uid=uid, mode=mode)


def bind(actor, ref, *, action):
    value = actor.doc(ref)
    active = action != 'check'
    state = 'ROOT_BOUND_ONE_FUTURE_OPERATION' if active else 'ROOT_READONLY_QUALIFICATION'
    actor.need(value['schema'] == 'frw.Root.S01.owned-ordinary-driver.v1' and value['status'] == state
               and value['operator'] == 'Root', 'S01_ROOT_EXPLICIT_BINDING_REQUIRED')
    work = actor.canonical_path(value['workdir'])
    package = Path(ref['path']).parent
    actor.protected_directory(package)
    actor.need(work.parent == package and not work.is_relative_to(HOME) and not work.is_relative_to(actor.STATE),
               'S01_DISJOINT_OPERATION_DIRECTORY_REQUIRED')
    identity = value['work_identity']
    slot_identity = value['slot_identity']
    actor.need(type(slot_identity) is dict and set(slot_identity) == {'device', 'inode', 'uid', 'mode', 'nlink'},
               'S01_EXACT_SLOT_IDENTITY_REQUIRED')

    def check_work():
        actor.need(protected_work_identity(actor, work) == identity, 'S01_OPERATION_DIRECTORY_IDENTITY_CHANGED')

    check_work()
    current = installed_module(actor, 'ordinary_current', CURRENT_SHA)
    composer = installed_module(actor, 'ordinary_admission_source', COMPOSER_SHA)
    once_module = installed_module(actor, 'ordinary_once', ONCE_SHA)
    actor.need(value['checker']['sha256'] == CURRENT_SHA and value['source']['sha256'] == R4_SHA,
               'S01_EXISTING_GATE_OR_OBSERVER_CHANGED')
    phase = actor.doc(value['phase'])
    run_id = value['run_id']
    actor.need(isinstance(run_id, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id)
               and phase['scenario_sha256'] == SCENARIO_SHA
               and current.digest(current.encoded(phase['scenario'])) == SCENARIO_SHA, 'S01_EXACT_PHASE_REQUIRED')
    contract = current.document(value['contract'])
    prepare = current.document(value['prepare'])
    authority = actor.doc(value['authority'])
    actor.need(authority.get('qualification_only') is (not active)
               and contract.get('qualification_only') is (not active)
               and authority['run_scenarios'] == {run_id: SCENARIO_SHA}
               and prepare['current_observer']['sha256'] == ROUTE_SHA,
               'S01_EXACT_AUTHORITY_OR_CURRENT_ROUTE_REQUIRED')
    expected_profile = f'telegram-bot-{phase["scenario"]["tester_id"]}'
    directories, paths = disk_paths(work, actor.STATE, expected_profile)
    scope, resources = value['disk_scope'], value['resources']
    actor.need(set(resources) == set(RESOURCE_LIMITS)
               and all(type(resources[k]) is int and 0 < resources[k] <= cap for k, cap in RESOURCE_LIMITS.items())
               and scope['directory_roots'] == directories and scope['file_paths'] == paths
               and type(scope['max_entries']) is int and 0 < scope['max_entries'] <= 100000
               and type(scope['sample_seconds']) in (float, int) and 0 < scope['sample_seconds'] <= 1,
               'S01_BOUNDED_WRITE_SCOPE_REQUIRED')
    if active:
        driver = actor.read(DRIVER, limit=65536, private=False)
        review = actor.doc(value['source_review'])
        driver_ref = dict(path=str(DRIVER), bytes=len(driver), sha256=actor.digest(driver))
        actor.need(review.get('decision') == 'SOURCE_ONLY_READY_UNBOUND' and review.get('reviewed_source') == driver_ref
                   and review.get('open_critical_defects') == [], 'S01_EXACT_INDEPENDENT_SOURCE_REVIEW_REQUIRED')
    class BoundOnce(once_module.Once):
        start_fd = None

        def close_start(self):
            if self.start_fd is not None:
                os.close(self.start_fd)
                self.start_fd = None

        def record(self, name, value):
            check_work()
            return super().record(name, value)

        def release_start(self):
            try:
                os.write(self.start_fd, b'S')
            except BrokenPipeError:
                pass  # The wait result records the same child's exit.
            finally:
                self.close_start()

    return BoundOnce(actor, current, composer, ref)


def preclock(once):
    actor = once.actor
    slot = actor.safe_lock(actor.SLOT, once.binding['slot_identity'])
    try:
        actor.need(not list(once.work.iterdir()), 'S01_OPERATION_DIRECTORY_ALREADY_USED')
        parent = actor.kernel(os.getpid())
        with tempfile.TemporaryDirectory(dir=once.work, prefix='preclock-') as scratch:
            observer, ref = once.observer(Path(scratch), 'preclock', parent)
            qualified = actor.qualify_before_clock(dict(run_id=once.context['run_id'], selected_tester=ref),
                         observer, once.metadata, actor.readref(ref), once.phase)
        growth_basis = actor.scan_scope(once.binding['disk_scope'], deadline=time.monotonic() + 30)
        return dict(state='S01_READONLY_QUALIFIED', qualification=qualified, scoped_inode_count=len(growth_basis),
                    operation_clock_created=False, execution_authorized=False)
    finally:
        os.close(slot)


def launch(once, slot, parent, claim, clock):
    ref = once.binding_ref
    read_fd, once.start_fd = os.pipe()
    try:
        argv = [str(PYTHON), '-I', '-S', '-B', str(DRIVER), 'consume', ref['path'], ref['sha256'],
                str(slot), str(parent['pid']), str(parent['start_time']), parent['boot_id'], claim['sha256'],
                clock['sha256'], str(read_fd)]
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, pass_fds=(slot, read_fd))
    finally:
        os.close(read_fd)


def wait_for_birth(once, fd, parent, claim, clock):
    actor = once.actor
    try:
        prctl = ctypes.CDLL(None, use_errno=True).prctl
        prctl.argtypes = [ctypes.c_int, *([ctypes.c_ulong] * 4)]
        actor.need(prctl(PR_SET_PDEATHSIG, signal.SIGINT, 0, 0, 0) == 0,
                   'S01_PARENT_DEATH_BINDING_REFUSED')
        actor.need(actor.kernel(os.getppid()) == parent, 'S01_ORIGINAL_PARENT_CHANGED')
        signal.pthread_sigmask(signal.SIG_UNBLOCK, (signal.SIGINT, signal.SIGTERM))
        actor.need(stat.S_ISFIFO(os.fstat(fd).st_mode) and os.read(fd, 1) == b'S', 'S01_CHILD_START_REFUSED')
    finally:
        os.close(fd)
    birth = actor.doc(actor.fileref(once.work / 'child-birth.json'))
    actor.need(birth['parent'] == parent and birth['claim'] == claim and birth['clock'] == clock
               and birth['pid'] == os.getpid() and birth['identity'] == actor.kernel(os.getpid()),
               'S01_EXACT_DURABLE_CHILD_BIRTH_REQUIRED')


def actual_runner(observer, store):
    class AuthorizedRunner(observer.Runner):
        def new(self, *args, **kwargs):
            run = super().new(*args, **kwargs)
            # The active NEW gate has confirmed the child, locks, clocks and scope.
            token = observer.safe_read(store.root / 'tester-token', 256).decode('ascii').strip()
            self.api = observer.BotAPI(token)
            return run

    return AuthorizedRunner(store, None)


def still_present(actor, identity):
    try:
        return actor.kernel(identity['pid']) == identity
    except (FileNotFoundError, ProcessLookupError):
        return False


def reconcile(once):
    actor, work = once.actor, once.work
    claim_ref = actor.fileref(work / 'claim.json')
    claim = actor.doc(claim_ref)
    actor.need(claim['binding'] == once.binding_ref and claim['no_retry'] is True
               and all(claim[k] == v for k, v in once.context.items()), 'S01_ORIGINAL_INVOCATION_CHANGED')
    clock_path = work / 'clock.json'
    clock_ref = None
    if os.path.lexists(clock_path):
        clock_ref = actor.fileref(clock_path)
        clock = actor.doc(clock_ref)
        actor.need(clock['schema'] == 'frw.Root.F07.finite-operation-clock.v1'
                   and clock['status'] == 'ROOT_BOUND_FUTURE_OPERATION'
                   and clock['timing'] == once.current.TIMING and clock['old_effects_clocks_preserved'] is True
                   and all(clock[k] == v for k, v in once.context.items())
                   and clock['deadline_monotonic'] == clock['started_monotonic'] + once.current.TIMING['outer_seconds'],
                   'S01_ORIGINAL_CLOCK_CHANGED')
    report = dict(state='S01_RECONCILE_ORIGINAL_OPERATION', operation_clock=clock_ref, no_retry=True,
                  product_cancelled=False, acceptance='NOT_ESTABLISHED')
    if still_present(actor, claim['parent']):
        return {**report, 'settlement': 'ORIGINAL_PARENT_STILL_PRESENT'}
    birth_path = work / 'child-birth.json'
    birth_ref, birth = None, None
    if os.path.lexists(birth_path):
        birth_ref = actor.fileref(birth_path)
        birth = actor.doc(birth_ref)
        actor.need(clock_ref is not None and birth['clock'] == clock_ref and birth['claim'] == claim_ref
                   and birth['parent'] == claim['parent'], 'S01_BIRTH_CHANGED')
    stop_path = work / 'stop-unconfirmed.json'
    identity = birth['identity'] if birth is not None else None
    if os.path.lexists(stop_path):
        stopped = actor.fileref(stop_path)
        stop = actor.doc(stopped)
        actor.need(clock_ref is not None and stop.get('state') == 'STOP_UNCONFIRMED'
                   and stop['operation_clock'] == clock_ref and stop['parent'] == claim['parent']
                   and stop['no_retry'] is True and all(stop[k] == v for k, v in once.context.items())
                   and (birth is None or (stop['pid'], stop['identity']) == (birth['pid'], identity)),
                   'S01_STOP_RECEIPT_CHANGED')
        identity = stop['identity']
        report['historical_stop_unconfirmed'] = stopped
    if identity is not None and still_present(actor, identity):
        return {**report, 'settlement': 'ORIGINAL_CONSUMER_STILL_PRESENT'}
    slot = actor.safe_lock(actor.SLOT, once.binding['slot_identity'])
    try:
        with existing_lock(actor, actor.STATE / 'consumer.lock'), existing_lock(actor, actor.STATE / 'tester-token'):
            receipt_path = work / 'consumer-ended.json'
            consumer_ref = actor.fileref(receipt_path) if os.path.lexists(receipt_path) else None
            consumer = actor.doc(consumer_ref) if consumer_ref is not None else None
            if consumer is not None:
                actor.need(consumer['no_retry'] is True and all(consumer[k] == v for k, v in once.context.items()),
                           'S01_CONSUMER_RECEIPT_CHANGED')
                invocation_path = work / 'consumer-invocation.json'
                if os.path.lexists(invocation_path):
                    invocation = actor.doc(actor.fileref(invocation_path))
                    actor.need(invocation['clock'] == clock_ref and invocation['driver_binding'] == once.binding_ref
                               and invocation['run_id'] == once.context['run_id'] and invocation['no_retry'] is True
                               and (identity is None or invocation['consumer'] == identity),
                               'S01_CONSUMER_INVOCATION_CHANGED')
                else:
                    actor.need(consumer['stage'] == 'BOOTSTRAP' and consumer['run'] is None
                               and consumer['exception_class'] is not None, 'S01_CONSUMER_INVOCATION_MISSING')
                report['consumer_ending'] = consumer_ref
            path = actor.STATE / 'runs' / (once.context['run_id'] + '.json')
            if os.path.lexists(path):
                ref = actor.fileref(path)
                row = actor.doc(ref)
                actor.need(row['id'] == once.context['run_id'] and row['scenario_sha256'] == SCENARIO_SHA,
                           'S01_CANONICAL_ROW_CHANGED')
                report.update(run=ref, raw_status=row['status'], send_state=row['send_state'],
                              full_window=row.get('capture_window_complete') is True,
                              run_matches_consumer_ending=consumer is not None and consumer['run'] == ref)
            ending_path = work / 'parent-ended.json'
            ending_ref = None
            if os.path.lexists(ending_path):
                ending_ref = actor.fileref(ending_path)
                ending = actor.doc(ending_ref)
                actor.need(clock_ref is not None and ending['operation_clock'] == clock_ref
                           and ending['owned_child_reaped'] is True and ending['no_retry'] is True
                           and birth_ref is not None and ending['child_birth'] == birth_ref
                           and all(ending[k] == v for k, v in once.context.items()), 'S01_PARENT_ENDING_CHANGED')
            return {**report, 'settlement': 'ORIGINAL_RECORDED_OWNERS_ABSENT_LOCKS_AVAILABLE',
                    'owned_reap_receipt': ending_ref}
    finally:
        os.close(slot)


@contextmanager
def existing_lock(actor, path):
    fd = actor.safe_lock(path)
    try:
        yield
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'execute-once', 'consume', 'reconcile'))
    parser.add_argument('path')
    parser.add_argument('sha256')
    parser.add_argument('child_args', nargs='*')
    args = parser.parse_args()
    if Path(sys.executable) != PYTHON or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise ValueError('S01_EXACT_CORE295_INTERPRETER_REQUIRED')
    os.umask(0o077)
    actor = load_actor()
    _, ref = actor.exact_file(args.path, args.sha256)
    once = bind(actor, ref, action=args.action)
    if args.action == 'consume':
        slot, pid, start, boot, claim_sha, clock_sha, start_fd = args.child_args
        _, claim_ref = actor.exact_file(str(once.work / 'claim.json'), claim_sha)
        _, clock_ref = actor.exact_file(str(once.work / 'clock.json'), clock_sha)
        parent = dict(pid=int(pid), start_time=int(start), boot_id=boot)
        wait_for_birth(once, int(start_fd), parent, claim_ref, clock_ref)
        once.consume(int(slot), parent, claim_ref, clock_ref, actual_runner)
        return
    actor.need(not args.child_args, 'S01_UNEXPECTED_CHILD_ARGUMENTS')
    if args.action == 'check':
        result = preclock(once)
    elif args.action == 'execute-once':
        try:
            result = once.execute(lambda *args: launch(once, *args), release=once.release_start)
        finally:
            once.close_start()
    else:
        result = reconcile(once)
    sys.stdout.buffer.write(actor.encoded(result))


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        # Runtime exceptions may carry credential-bearing URLs. Persist only fixed metadata.
        code = str(exc) if type(exc) is ValueError and re.fullmatch(r'S01_[A-Z_]+', str(exc)) else type(exc).__name__
        print(f'S01_REFUSED_INTERRUPTED_OR_UNKNOWN {code}', file=sys.stderr)
        sys.exit(2)
