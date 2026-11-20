#!/usr/bin/env python3
"""Exact S01 in a disposable Store, with a real child and an inert transport."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace


HERE = Path(__file__).resolve().parent
DRAFTS = HERE.parents[1]
RUN_ID = 'baseline-s01-local-once'
SOURCE_SHA = '44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd'
SCENARIO_SHA = '8a028fd974f9290f8cf978e7d2d7ab75f66cb2bb468606365f5e5512468b057d'
PLAN_SHA = '8c47b52d5feb936feeabbdfffd7b6fc364af899160d6e95dd797edcdb58f3dd1'


def module(raw, name):
    result = ModuleType(name)
    exec(compile(raw, name, 'exec'), result.__dict__)
    return result


def ref_data(root):
    actor = module((DRAFTS / 'ordinary-disk-monitor-next-source-20261116/root_f07_once.py').read_bytes(), 'f07')
    actor.STATE = root / 'state'
    actor.SLOT = root / 'acceptance.lock'
    current = module((root / 'current.py').read_bytes(), 'current')
    return actor, current


def once(root, binding):
    actor, current = ref_data(root)
    composer = SimpleNamespace(**runpy.run_path(str(HERE / 'ordinary_admission_source.py')))
    return runpy.run_path(str(HERE / 'ordinary_once.py'))['Once'](actor, current, composer, binding)


def setup(root, source, scenario):
    current = (HERE / 'ordinary_current.py').read_bytes()
    current += f'\nSTATE = Path({str(root / "state")!r})\nSLOT = Path({str(root / "acceptance.lock")!r})\n'.encode()
    (root / 'current.py').write_bytes(current)
    actor, gate = ref_data(root)

    def put(name, value):
        return actor.new(root / name, actor.encoded(value))

    base = module(source, 'r4_base')
    store = base.Store(actor.STATE)
    for path in (actor.SLOT, actor.STATE / 'consumer.lock', actor.STATE / 'tester-token'):
        path.touch(mode=0o600)
    now = datetime.now(timezone.utc)
    parent = actor.kernel(os.getpid())
    history = dict(id='historical-unknown', status='UNKNOWN_SEND', send_state='unknown', scenario={'steps': []},
                   deadline=now.timestamp() - 600)
    old_path = store.run_path(history['id'])
    store.put(old_path, history)
    old = dict(sha256=actor.fileref(old_path)['sha256'], status=history['status'], send_state='unknown',
               deadline=history['deadline'], new_effect_replay_authorized=False, unknown_retained=True)
    gateway = put('gateway.json', dict(pid=parent['pid'], start_time=parent['start_time'], gateway_state='running',
                  active_agents=0, active_work=None, restart_requested=False, session_store={'status': 'ok'},
                  updated_at=now.isoformat(), platforms={'telegram': dict(state='connected', needs_attention=False,
                      writer_pid=parent['pid'], writer_start_time=parent['start_time'])}))
    schema = runpy.run_path(str(HERE / 'ordinary_admission_source.py'))['AUTHORITY_SCHEMA']
    authority = put('authority.json', dict(schema=schema, authority_id='synthetic-control-only', operator='Root',
                    accepted=True, run_scenarios={RUN_ID: SCENARIO_SHA}, created_at=now.timestamp() - 1,
                    expires_at=now.timestamp() + 180, boot_id=parent['boot_id'],
                    gateway=dict(state_path=gateway['path'], pid=parent['pid'], start_time=parent['start_time'],
                                 maximum_staleness_seconds=180), history={history['id']: old},
                    new_independent_inputs_only=True, no_old_task_replay=True, old_rows_modified=False,
                    unknown_effects_resolved=False, product_or_B00_acceptance=False, new_trial_for_historical_task=False))
    context = dict(run_id=RUN_ID, scenario_sha256=SCENARIO_SHA)
    scope = root / 'scope'
    scope.write_bytes(b'fixture-current\n')
    observe = actor.new(root / 'fixture_current.py', b"from pathlib import Path\n"
                        b"def check_current(scope, *, scenario, read_reference, load_module):\n"
                        b"    return Path(scope['file']).read_bytes() == b'fixture-current\\n'\n")
    helper = (DRAFTS / 'f07-ordinary-current209-source-20261113/config-bound-delta/source/current209.py').read_bytes()
    cursor = put('state/cursor.json', {'offset': 0})
    contract = put('contract.json', dict(schema='frw.Root.ordinary-current-contract.v1', **context, operator='Root',
                   authority=authority, decisions=dict.fromkeys(gate.DECISIONS, True), cursor=cursor,
                   scope={'file': str(scope)}))
    prepare = put('prepare.json', dict(schema='frw.Root.ordinary-current-prepare.v1', **context, timing=gate.TIMING,
                  metadata_helper=actor.new(root / 'metadata.py', helper), current_observer=observe))
    work = root / 'operation'
    work.mkdir(mode=0o700)
    binding = put('binding.json', dict(run_id=RUN_ID, workdir=str(work), checker=actor.fileref(root / 'current.py'),
                  authority=authority, contract=contract, prepare=prepare,
                  source=actor.new(root / 'r4.py', source),
                  phase=put('phase.json', dict(scenario=scenario, scenario_sha256=SCENARIO_SHA)),
                  slot_identity=actor.lock_identity(actor.SLOT.stat()),
                  resources=dict(cpu_seconds=45, max_rss_bytes=512 * 1024**2, disk_bytes=12 * 1024**2),
                  disk_scope=dict(directory_roots=[str(work), str(actor.STATE)], file_paths=[],
                                  sample_seconds=0.05, max_entries=100)))
    return binding, store, old_path


def fake_runner(r4, store, root, scenario, mode, parent):
    now = time.time()
    upload = scenario['steps'][0]['input']
    chat = {'id': r4.PEER, 'type': 'private'}

    def sleep(_delay):
        nonlocal now
        now += 180  # Advance only the observer's fixture wall time, after its first poll.

    def stop_during_sample():
        limit = time.monotonic() + 3
        while not (root / 'active-sample-entered').exists() and time.monotonic() < limit:
            time.sleep(0.005)
        assert (root / 'active-sample-entered').is_file()
        (root / 'signal-point').touch(mode=0o600)
        os.kill(parent['pid'], signal.SIGTERM)
        time.sleep(0.25)

    class Transport:
        def call(self, method, params=None, *, timeout):
            assert timeout > 0
            if method == 'getChat' and mode == 'drift':
                (root / 'scope').write_bytes(b'fixture-changed\n')
            if method == 'getChat' and mode == 'stop-before-wire':
                stop_during_sample()
            if method == 'getUpdates' and mode == 'stop-after-ack':
                stop_during_sample()
                raise AssertionError('Stop did not interrupt capture')
            reply = [{'update_id': 72, 'message': dict(message_id=902, chat=chat, date=int(now),
                      **{'from': {'id': r4.PEER, 'is_bot': True}}, reply_to_message={'message_id': 901},
                      text='Synthetic S01 reply; semantic grade intentionally absent.')}]
            result = {'getMe': {'id': r4.TESTER, 'is_bot': True}, 'getWebhookInfo': {'url': ''}, 'getChat': chat,
                      'getUpdates': reply if params and params.get('timeout') else []}[method]
            self._last_response = r4.encoded({'ok': True, 'result': result})
            return result

        def send_document(self, body, content_type, *, timeout):
            assert timeout == 10 and Path(upload['path']).read_bytes() in body
            assert content_type.startswith('multipart/form-data;')
            (root / 'wire').touch(mode=0o600, exist_ok=False)
            return dict(message_id=901, chat=chat, date=int(now), caption=upload['caption'],
                        document=dict(file_id='fixture-in', file_unique_id='fixture-unique',
                                      file_size=upload['stat']['size_bytes']))

    runner = r4.Runner(store, Transport(), clock=lambda: now, sleep=sleep)
    if mode == 'new-durable-refusal':
        save = runner.save

        def save_then_refuse(run):
            save(run)
            assert run['status'] == 'PREPARED'
            raise OSError('fixture error after durable NEW')

        runner.save = save_then_refuse
    return runner


def exercise(source, scenario, mode):
    with tempfile.TemporaryDirectory(prefix='frw-r4-once-') as directory:
        root = Path(directory)
        binding, store, old = setup(root, source, scenario)
        original = old.read_bytes()
        drive = once(root, binding)
        stopping = mode in {'stop-before-wire', 'stop-after-ack'}
        if stopping:
            original_scan = drive.actor.scan_scope
            slowed = False

            def slow_active_sample(scope, *, deadline):
                nonlocal slowed
                if not slowed and (drive.work / 'clock.json').exists():
                    slowed = True
                    (root / 'active-sample-entered').touch(mode=0o600)
                    limit = time.monotonic() + 3
                    while not (root / 'signal-point').exists() and time.monotonic() < limit:
                        time.sleep(0.005)
                    time.sleep(0.45)
                return original_scan(scope, deadline=deadline)

            drive.actor.scan_scope = slow_active_sample

        def launch(slot, parent, claim, clock):
            if mode == 'launch-refusal':
                raise ValueError('fixture launch refusal')
            fd = os.open(drive.actor.SLOT, os.O_RDWR | os.O_NOFOLLOW) if mode == 'bad-inheritance' else slot
            try:
                args = json.dumps([str(root), binding, fd, parent, claim, clock, mode])
                return subprocess.Popen([sys.executable, '-I', '-S', '-B', __file__, '--child', args],
                                        stdin=subprocess.DEVNULL, pass_fds=(fd,))
            finally:
                if fd != slot:
                    os.close(fd)

        run_path = store.run_path(RUN_ID)
        if mode == 'preclock-refusal':
            (root / 'scope').write_bytes(b'fixture-changed\n')
        if mode == 'lock-held':
            with store.lock(create=False):
                refused(drive, launch, 'Another tester consumer is active')
        elif mode == 'preclock-refusal':
            refused(drive, launch, 'current route, identity or rights')
        elif mode == 'launch-refusal':
            refused(drive, launch, 'fixture launch refusal')
            ending = json.loads((drive.work / 'parent-failure.json').read_bytes())
            assert ending['stage'] == 'LAUNCH' and ending['operation_clock'] and not ending['owned_child_reaped']
            assert not run_path.exists()
        else:
            result = drive.execute(launch)
            child = json.loads((drive.work / 'consumer-ended.json').read_bytes())
            assert result['owned_child_reaped'] and (drive.work / 'claim.json').is_file(), result
            clock = json.loads((drive.work / 'clock.json').read_bytes())
            assert clock['deadline_monotonic'] == clock['started_monotonic'] + 600
            run = store.get(run_path)
            if run is not None:
                assert child['run'] == drive.actor.fileref(run_path), child
            if stopping:
                assert result['stop_forwarded'] and result['parent_stops'] == [signal.SIGTERM], result
                assert child['exception_class'] == 'KeyboardInterrupt', child
                assert (root / 'active-sample-entered').is_file() and (root / 'signal-point').is_file()
            if mode in {'capture', 'close-signal'}:
                assert result['exit_code'] == 0 and child['exception_class'] is None, child
                assert run['status'] == 'EVIDENCE_READY' and run['capture_window_complete'], run['status']
                assert run['capture_until'] == run['sent_at'] + 180 and run['send_attempts'] == 1
                assert run['reply_outcome'] == 'RECEIVED_UNGRADED' and len(run['observations']) == 1, run['reply_outcome']
                assert run['acceptance'] == 'NOT_ESTABLISHED'
                existing = run_path.read_bytes()
                refused(drive, launch, 'R4_OPERATION_DIRECTORY_ALREADY_USED')
                assert run_path.read_bytes() == existing
                if mode == 'close-signal':
                    assert (root / 'closing-signal').is_file()
            elif mode == 'stop-after-ack':
                assert child['stage'] == 'OBSERVE', child
                assert run['send_state'] == 'sent' and not run.get('capture_window_complete'), run['status']
            elif mode == 'bad-inheritance':
                assert child['stage'] == 'BOOTSTRAP' and child['exception_class'] == 'BlockingIOError', child
                assert result['exit_code'] != 0 and run is None
            elif mode == 'new-durable-refusal':
                assert child['stage'] == 'NEW' and child['exception_class'] == 'OSError', child
                assert result['exit_code'] != 0 and run['status'] == 'PREPARED' and run['send_attempts'] == 0
            else:
                assert result['exit_code'] != 0 and child['stage'] == 'SEND', child
                assert run['status'] == 'PREPARED' and run['send_attempts'] == 0, run['status']
                if mode == 'drift':
                    diagnostic = store.get(store.root / ('pre-request-' + RUN_ID + '.json'))
                    assert diagnostic['phase'] == 'PRE_INTENT_REVALIDATION', diagnostic
                    assert diagnostic['exception_class'] == 'VALUE_ERROR', diagnostic
        assert (root / 'wire').exists() == (mode in {'capture', 'stop-after-ack', 'close-signal'})
        if mode in {'lock-held', 'preclock-refusal'}:
            assert not run_path.exists() and not list(drive.work.iterdir())
        assert old.read_bytes() == original
        with store.lock(create=False), store.lock(store.root / 'tester-token', create=False):
            fd = drive.actor.safe_lock(drive.actor.SLOT)
            os.close(fd)
        print(mode, 'PASS', flush=True)


def refused(drive, launch, message):
    try:
        drive.execute(launch)
    except Exception as exc:
        assert message in str(exc), type(exc).__name__
    else:
        raise AssertionError('Expected refusal')


def audit(event, _args):
    if event.startswith('socket.'):
        raise AssertionError('Fixture transport attempted a socket')


def main():
    os.umask(0o077)
    sys.addaudithook(audit)
    if sys.argv[1] == '--child':
        root, binding, slot, parent, claim, clock, mode = json.loads(sys.argv[2])
        root = Path(root)
        drive = once(root, binding)
        if mode == 'close-signal':
            write = drive.actor.new

            def stop_during_close(path, raw):
                if path.name == 'consumer-ended.json':
                    (root / 'closing-signal').touch(mode=0o600)
                    signal.raise_signal(signal.SIGINT)
                return write(path, raw)

            drive.actor.new = stop_during_close
        try:
            drive.consume(slot, parent, claim, clock,
                          lambda r4, store: fake_runner(r4, store, root, drive.phase['scenario'], mode, parent))
        except KeyboardInterrupt:
            return 130
        except BlockingIOError:
            if mode == 'bad-inheritance':
                return 2
            raise
        except OSError:
            if mode == 'new-durable-refusal':
                return 2
            raise
        except ValueError:
            if mode == 'drift':
                return 2
            raise
        return 0
    source, raw_plan = (Path(p).read_bytes() for p in sys.argv[1:3])
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA
    assert hashlib.sha256(raw_plan).hexdigest() == PLAN_SHA
    base = module(source, 'base_once')
    scenario = base.validate_scenario(json.loads(raw_plan))
    assert base.digest(base.encoded(scenario)) == SCENARIO_SHA
    for case in ('preclock-refusal', 'lock-held', 'capture', 'drift', 'stop-before-wire', 'stop-after-ack',
                 'launch-refusal', 'bad-inheritance', 'new-durable-refusal', 'close-signal'):
        exercise(source, scenario, case)
    return 0


if __name__ == '__main__':
    sys.exit(main())
