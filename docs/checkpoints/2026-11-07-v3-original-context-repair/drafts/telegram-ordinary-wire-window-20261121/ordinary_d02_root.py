"""Bind each D02 phase to one owned R4 operation and its actual receiver client."""

import argparse
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import ModuleType


DRAFTS = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts')
SHARED = DRAFTS / 'baseline-ordinary-batch-capture-20261120/r4/ordinary_s01_root.py'
SHARED_SHA = '126fa16c8b22e814d19b876933310e63657abfeaaa20d45d06075ae959a0ce6e'
DRIVER = Path(__file__).resolve()
PHASES = (
    '088d47d6a8efbf63068bb8fff13c69af05478a20156960811ac1d170db46c4cf',
    'bab05e12b1465b984bf58acfd8b25507162b31c135dbb3623623951a06b10a05',
)
ACTIVE_ROOT = Path('/home/jericho/.cache/FRW-ASTRA-D02-DISTINCT-R4-OPERATIONS-20261121')
ACTIVE_RUNS = {
    PHASES[0]: ('root-d02-alt-odt-01-v3-20261121', 'upload'),
    PHASES[1]: ('root-d02-alt-odt-02-v3-20261121', 'follow-up'),
}
SOURCE_PINS = dict(
    checker='2983e06dc5579adae0f0983d64d07b65c41f849b03dca0985f270d2547a9411b',
    composer='68eaa543d507800232daa3700f570e28eff564280f5c83431420cf57a2d35c90',
    once='e569e03cebf482129c16102ad3559e162d1332a32b1bb3a6271158048b9cc809',
    receiver_client='c12b4268619e546e874ab884acaaed0fe1b3f665fe17c2d06fdf461868d528b4',
)
TOOL_PINS = {
    'gateway/control_socket.py': '0c71b698bbbbfb1829d07e371128bb9e4f803a940c5e5fdf7d5ff3ed9594e1cc',
    'agent/deadline.py': '429ff313e0ae4427cf3bfdfc148a22ed46eaf09b994d6875b1c57693228bd13e',
}
SCHEMA = 'frw.Root.D02.owned-ordinary-driver.v1'
PRIOR_REVIEW = 'frw.Root.D02.distinct-upload-review.v1'


def load_shared():
    from hashlib import sha256

    raw = SHARED.read_bytes()
    if sha256(raw).hexdigest() != SHARED_SHA:
        raise ValueError('D02_EXACT_SHARED_DRIVER_REQUIRED')
    module = ModuleType('_D02_shared_driver')
    module.__file__ = str(SHARED)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def load_operator_sources(actor, binding):
    modules = {}
    for name, sha in SOURCE_PINS.items():
        reference = binding[name]
        actor.need(reference['sha256'] == sha, 'D02_EXACT_OPERATOR_SOURCE_REQUIRED')
        raw = actor.readref(reference, private=False)
        modules[name] = actor.load_raw(raw, reference['path'], '_D02_' + name)
    return modules


def load_runtime_tools(actor, home):
    result = []
    for name, sha in TOOL_PINS.items():
        path = home / 'hermes-agent' / name
        raw = actor.read(path, limit=65536, private=False)
        actor.need(actor.digest(raw) == sha, 'D02_EXACT_RUNTIME_CONTROL_SOURCE_REQUIRED')
        name = '_D02_installed_' + path.stem
        # deadline's dataclasses resolve their defining module.
        module = ModuleType(name)
        module.__file__ = str(path)
        sys.modules[name] = module
        try:
            exec(compile(raw, module.__file__, 'exec'), module.__dict__)
        except BaseException:
            del sys.modules[name]
            raise
        result.append(module)
    return result[0].query_gateway_control, result[1].run_bounded_sync


def check_predecessor(actor, current, authority, contract, run_id, scenario_sha, active):
    rows = authority.get('ordered_predecessors', {})
    if scenario_sha == PHASES[0] or not active:
        actor.need(rows == {}, 'D02_UNEXPECTED_ORDERED_PREDECESSOR')
        return
    actor.need(type(rows) is dict and set(rows) == {run_id}, 'D02_EXACT_UPLOAD_PREDECESSOR_REQUIRED')
    prior = rows[run_id]
    actor.need(set(prior) == {'run_id', 'scenario_sha256', 'run_record_sha256', 'review', 'review_schema',
                              'initially_absent'}
               and prior['scenario_sha256'] == PHASES[0] and prior['review_schema'] == PRIOR_REVIEW
               and prior['initially_absent'] is False and set(prior['review']) == {'path', 'sha256'},
               'D02_EXACT_UPLOAD_PREDECESSOR_REQUIRED')
    prior_id = prior['run_id']
    actor.need(prior_id == ACTIVE_RUNS[PHASES[0]][0] and prior_id != run_id
               and prior_id in authority['history'], 'D02_ORIGINAL_UPLOAD_ID_REQUIRED')
    row_ref = actor.fileref(actor.STATE / 'runs' / (prior_id + '.json'))
    row = current.document(row_ref)
    review_ref = actor.fileref(prior['review']['path'])
    review = current.document(review_ref)
    actor.need(row_ref['sha256'] == prior['run_record_sha256'] == authority['history'][prior_id]['sha256']
               and review_ref['sha256'] == prior['review']['sha256']
               and row['id'] == prior_id and row['scenario_sha256'] == PHASES[0]
               and row['status'] == 'EVIDENCE_READY' and row['send_state'] == 'sent'
               and row['send_attempts'] == 1 and row['capture_window_complete'] is True
               and type(row['deadline']) in (int, float) and math.isfinite(row['deadline'])
               and row['deadline'] <= authority['created_at'] <= time.time()
               and review['schema'] == PRIOR_REVIEW and review['run_id'] == prior_id
               and review['scenario_sha256'] == PHASES[0]
               and review['custody_evidence']['run_record_sha256'] == row_ref['sha256']
               and all(review[field] == 'PASS' for field in ('semantic', 'custody', 'native_source', 'native_context'))
               and review['same_context'] == contract['scope']['predecessor_context'],
               'D02_CLOSED_UPLOAD_AND_INDEPENDENT_CONTEXT_REVIEW_REQUIRED')
    actor.readref(review['same_context'])
    actor.readref(review['independent_evidence'])
    # The original Runner is still responsible for full verify_reply_custody on its ordinary path.


def bind(shared, actor, reference, *, action):
    value = actor.doc(reference)
    active = action != 'check'
    state = 'ROOT_BOUND_ONE_FUTURE_OPERATION' if active else 'ROOT_READONLY_QUALIFICATION'
    actor.need(value['schema'] == SCHEMA and value['status'] == state and value['operator'] == 'Root',
               'D02_EXPLICIT_ROOT_BINDING_REQUIRED')
    work = actor.canonical_path(value['workdir'])
    package = Path(reference['path']).parent
    actor.protected_directory(package)
    actor.need(work.parent == package and not work.is_relative_to(shared.HOME)
               and not work.is_relative_to(actor.STATE), 'D02_DISJOINT_WORKSPACE_REQUIRED')
    slot = value['slot_identity']
    actor.need(type(slot) is dict and set(slot) == {'device', 'inode', 'uid', 'mode', 'nlink'},
               'D02_EXACT_SLOT_REQUIRED')

    def work_current():
        actor.need(shared.protected_work_identity(actor, work) == value['work_identity'],
                   'D02_WORKSPACE_IDENTITY_CHANGED')

    work_current()
    modules = load_operator_sources(actor, value)
    current = modules['checker']
    phase = current.document(value['phase'])
    scenario = phase['scenario']
    phase_sha = current.digest(current.encoded(scenario))
    run_id = value['run_id']
    actor.need(phase_sha in PHASES and phase['scenario_sha256'] == phase_sha
               and type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id)
               and value['source']['sha256'] == shared.R4_SHA, 'D02_EXACT_PHASE_AND_R4_REQUIRED')
    if active:
        exact_run, directory = ACTIVE_RUNS[phase_sha]
        # The original Once claim stays with the fixed phase across later bindings.
        actor.need(run_id == exact_run and work == ACTIVE_ROOT / directory / 'operation',
                   'D02_SINGLE_PHASE_INVOCATION_REQUIRED')
    authority, contract, prepare = (current.document(value[role]) for role in ('authority', 'contract', 'prepare'))
    actor.need(authority['qualification_only'] is (not active)
               and contract['qualification_only'] is (not active)
               and contract['authority'] == value['authority']
               and authority['run_scenarios'] == {run_id: phase_sha},
               'D02_EXACT_PHASE_AUTHORITY_REQUIRED')
    check_predecessor(actor, current, authority, contract, run_id, phase_sha, active)

    profile = 'telegram-bot-' + str(scenario['tester_id'])
    directories, paths = shared.disk_paths(work, actor.STATE, profile)
    routed = shared.HOME / 'profiles' / profile / 'plugin-data' / 'agent-plugin-friday_rework-877e6505'
    resources, disk = value['resources'], value['disk_scope']
    actor.need(set(resources) == set(shared.RESOURCE_LIMITS)
               and all(type(resources[key]) is int and 0 < resources[key] <= cap
                       for key, cap in shared.RESOURCE_LIMITS.items())
               and disk['directory_roots'] == sorted([*directories, str(routed)])
               and disk['file_paths'] == paths
               and type(disk['max_entries']) is int and 0 < disk['max_entries'] <= 100000
               and type(disk['sample_seconds']) in (int, float) and 0 < disk['sample_seconds'] <= 1,
               'D02_BOUNDED_WRITE_SCOPE_REQUIRED')

    class BoundOnce(modules['once'].Once):
        start_fd = None

        def record(self, name, data):
            work_current()
            return super().record(name, data)

        def close_start(self):
            if self.start_fd is not None:
                os.close(self.start_fd)
                self.start_fd = None

        def release_start(self):
            try:
                os.write(self.start_fd, b'S')
            except BrokenPipeError:
                pass  # The existing Once parent records the exact child's exit.
            finally:
                self.close_start()

    once = BoundOnce(actor, current, modules['composer'], reference)
    if active:
        review = current.document(value['source_review'])
        raw = actor.read(DRIVER, limit=65536, private=False)
        self_ref = dict(path=str(DRIVER), bytes=len(raw), sha256=actor.digest(raw))
        actor.need(review['decision'] == 'SOURCE_ONLY_READY_UNBOUND' and review['reviewed_source'] == self_ref
                   and review['current_observer'] == prepare['current_observer']
                   and review['open_critical_defects'] == [], 'D02_EXACT_INDEPENDENT_REVIEW_REQUIRED')

        options = current.document(value['receiver_options'])
        gateway, boot = authority['gateway'], authority['boot_id']
        identity = {key: gateway[key] for key in ('pid', 'start_time')}
        actor.need(actor.kernel(identity['pid']) == dict(identity, boot_id=boot)
                   and set(options) == {'schema', 'principal', 'profile', 'rights', 'observer_expires_monotonic'}
                   and options['schema'] == modules['receiver_client'].OPTIONS_SCHEMA
                   and options['profile'] == profile
                   and options['principal']['transport_profile'] == 'default'
                   and options['principal']['user_id'] == str(scenario['tester_id'])
                   and options['principal']['account_id'] == str(scenario['peer_id']),
                   'D02_EXACT_GATEWAY_RECEIVER_ROUTE_REQUIRED')
        query, bounded = load_runtime_tools(actor, shared.HOME)
        once.receiver_window = modules['receiver_client'].ReceiverWindow(
            actor, workdir=work, home=shared.HOME, gateway=identity, boot_id=boot,
            receiver_options=value['receiver_options'], role='consumer' if action == 'consume' else 'parent',
            query_gateway_control=query, run_bounded_sync=bounded)
    return once


def launch(shared, once, slot, parent, claim, clock):
    read_fd, once.start_fd = os.pipe()
    reference = once.binding_ref
    try:
        argv = [str(shared.PYTHON), '-I', '-S', '-B', str(DRIVER), 'consume', reference['path'], reference['sha256'],
                str(slot), str(parent['pid']), str(parent['start_time']), parent['boot_id'],
                claim['sha256'], clock['sha256'], str(read_fd)]
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, pass_fds=(slot, read_fd))
    finally:
        os.close(read_fd)


def receive(shared, actor, once, args):
    slot, pid, start, boot, claim_sha, clock_sha, start_fd = args
    _, claim = actor.exact_file(str(once.work / 'claim.json'), claim_sha)
    _, clock = actor.exact_file(str(once.work / 'clock.json'), clock_sha)
    parent = dict(pid=int(pid), start_time=int(start), boot_id=boot)
    shared.wait_for_birth(once, int(start_fd), parent, claim, clock)
    once.consume(int(slot), parent, claim, clock, shared.actual_runner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'execute-once', 'consume'))
    parser.add_argument('binding')
    parser.add_argument('sha256')
    parser.add_argument('child_args', nargs='*')
    args = parser.parse_args()
    shared = load_shared()
    if (Path(sys.executable) != shared.PYTHON or not sys.flags.isolated or not sys.flags.no_site
            or not sys.dont_write_bytecode or sys.flags.optimize):
        raise ValueError('D02_EXACT_NATIVE_INTERPRETER_REQUIRED')
    os.umask(0o077)
    actor = shared.load_actor()
    actor.need(len(args.child_args) == (7 if args.action == 'consume' else 0), 'D02_EXACT_ARGUMENTS_REQUIRED')
    _, reference = actor.exact_file(args.binding, args.sha256)
    once = bind(shared, actor, reference, action=args.action)
    if args.action == 'consume':
        receive(shared, actor, once, args.child_args)
        return
    if args.action == 'check':
        result = shared.preclock(once)
        result.update(state='D02_READONLY_QUALIFIED', **once.context)
    else:
        try:
            result = once.execute(lambda *items: launch(shared, once, *items), release=once.release_start)
        finally:
            once.close_start()
    sys.stdout.buffer.write(actor.encoded(result))


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        detail = str(error) if type(error) is ValueError and re.fullmatch(r'D02_[A-Z_]+', str(error)) else type(error).__name__
        print(f'D02_REFUSED_INTERRUPTED_OR_UNKNOWN {detail}', file=sys.stderr)
        sys.exit(2)
