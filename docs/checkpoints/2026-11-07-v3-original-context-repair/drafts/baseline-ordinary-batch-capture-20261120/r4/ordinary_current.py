"""Read-only current gate for the selected R4 ordinary caller.

The owner supplies separate immutable decisions and a reviewed live observation
function. This file neither constructs a run nor grants an effect.
"""

from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
from types import ModuleType


STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
METADATA_SHA = '24215d1fca8d59e4109e5934464cf4cfbcf6d2dd48d33b7d44c3fc54377de47f'
TIMING = dict(operation_seconds=300, reply_window_seconds=180, ack_seconds=10,
              reserve_seconds=5, outer_seconds=600)
SEND_STAGES = {'CURSOR_AUTHORITY', 'PRE_INTENT_REVALIDATION'}
PREPARED_FIELDS = {
    'id', 'scenario', 'scenario_sha256', 'created_at', 'deadline', 'step', 'status',
    'send_state', 'sent_ids', 'seen', 'message_ids', 'observations', 'update_count',
    'last_text', 'repeat_count', 'send_attempts', 'capture_start_offset',
}
DECISIONS = (
    'eligible_new_effect', 'old_effects_and_clocks_preserved',
    'profile_chat_and_workspace_checked', 'privacy_and_current_stop_assessed',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_checked(path, limit):
    p = Path(path)
    require(p.is_absolute() and str(p) == str(path) and p.resolve(strict=True) == p,
            'Ordinary exact regular input path required')
    keys = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')

    def identity(info):
        return tuple(getattr(info, key) for key in keys)

    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_NONBLOCK
    with os.fdopen(os.open(p, flags), 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1
                and stat.S_IMODE(info.st_mode) == 0o600 and 0 < info.st_size <= limit,
                'Ordinary protected input custody changed')
        raw = stream.read(info.st_size + 1)
        require(len(raw) == info.st_size
                and identity(info) == identity(os.fstat(stream.fileno())) == identity(p.lstat()),
                'Ordinary protected input changed during read')
    return raw, info


def private_reference(reference):
    require(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}
            and type(reference['bytes']) is int and 0 < reference['bytes'] <= 24 * 1024**2
            and isinstance(reference['sha256'], str) and re.fullmatch('[0-9a-f]{64}', reference['sha256']),
            'Ordinary exact sized private reference required')
    raw, _ = read_checked(reference['path'], reference['bytes'])
    require(len(raw) == reference['bytes'] and digest(raw) == reference['sha256'],
            'Ordinary private reference changed')
    return raw


def document(reference):
    raw = private_reference(reference)
    value = json.loads(raw)
    require(type(value) is dict and encoded(value) == raw, 'Ordinary canonical record required')
    return value


def source_module(reference, name):
    module = ModuleType(name)
    module.__file__ = reference['path']
    exec(compile(private_reference(reference), module.__file__, 'exec'), module.__dict__)
    return module


def check_input(step):
    upload = step.get('input')
    if upload is None:
        return
    old = upload['stat']
    raw, new = read_checked(upload['path'], old['size_bytes'])
    require({'device': new.st_dev, 'inode': new.st_ino, 'size_bytes': new.st_size,
             'uid': new.st_uid, 'mtime_ns': new.st_mtime_ns, 'ctime_ns': new.st_ctime_ns} == old
            and digest(raw) == upload['sha256'], 'Ordinary exact upload changed')


def required_time(stage):
    operation = TIMING['operation_seconds']
    if stage in SEND_STAGES:
        operation = TIMING['ack_seconds'] + TIMING['reply_window_seconds']
    return operation + TIMING['reserve_seconds']


def check_operation(proof, run_id, scenario_sha, stage):
    role = proof['role']
    clock_ref = proof['clock']
    if role == 'preclock':
        require(stage == 'READONLY' and clock_ref is None and proof['once_invocation'] is None,
                'Read-only proof cannot prepare or send a run')
        return None
    require(role == 'owned_consumer' and clock_ref is not None and proof['once_invocation'] is not None,
            'Ordinary owned consumer and original clock required')
    clock = document(clock_ref)
    invocation = document(proof['once_invocation'])
    start, end = clock['started_monotonic'], clock['deadline_monotonic']
    require(clock.get('schema') == 'frw.Root.F07.finite-operation-clock.v1'
            and clock.get('status') == 'ROOT_BOUND_FUTURE_OPERATION'
            and clock.get('run_id') == run_id and clock.get('scenario_sha256') == scenario_sha
            and clock.get('timing') == TIMING and clock.get('old_effects_clocks_preserved') is True
            and all(type(v) in (int, float) and math.isfinite(v) for v in (start, end))
            and 0 <= start <= time.monotonic() and end == start + TIMING['outer_seconds'],
            'Ordinary finite operation clock changed')
    require(invocation.get('schema') == 'frw.Root.F07.one-ordinary-consumer-invocation.v1'
            and invocation.get('run_id') == run_id and invocation.get('clock') == clock_ref
            and invocation.get('consumer') == proof['lock_owners']['consumer']
            and invocation.get('no_retry') is True, 'Ordinary owned once invocation changed')
    return end


def wire_window_fits(proof_ref, run, ack_seconds):
    """Recheck the same immutable clock immediately before the wire call."""
    proof = document(proof_ref)
    require(proof['role'] == 'owned_consumer' and proof['run_id'] == run['id']
            and proof['scenario_sha256'] == run['scenario_sha256']
            and ack_seconds == TIMING['ack_seconds'], 'Ordinary wire clock binding changed')
    stage = 'PRE_INTENT_REVALIDATION'
    end = check_operation(proof, run['id'], run['scenario_sha256'], stage)
    require(not os.path.lexists(STATE / 'observer-stop.json'), 'Ordinary wire observer is stopped')
    wall, mono = time.time(), time.monotonic()
    require(mono < proof['expires_monotonic'] and wall < proof['expires_at']
            and mono + required_time(stage) <= end, 'Ordinary wire proof or full window expired')
    return True


def check_run_rows(authority, run_id, scenario, scenario_sha, stage, offset):
    # The selected R4 gate has already hashed every listed historical row.
    # Enforce set equality as well, including newly inserted terminal rows.
    expected = {name + '.json' for name in authority['history']}
    own_name = run_id + '.json'
    sending = stage in SEND_STAGES
    require(own_name not in expected, 'Ordinary run was already in the retained history')
    if sending:
        expected.add(own_name)
    runs = STATE / 'runs'
    require(runs.resolve(strict=True) == runs and {p.name for p in runs.iterdir()} == expected,
            'Ordinary complete retained history or own PREPARED transition changed')
    if not sending:
        return

    own_raw, _ = read_checked(runs / own_name, 1024**2)
    row = json.loads(own_raw)
    require(type(row) is dict and set(row) == PREPARED_FIELDS and encoded(row) == own_raw
            and row['id'] == run_id and row['scenario'] == scenario and row['scenario_sha256'] == scenario_sha
            and row['status'] == 'PREPARED' and row['send_state'] == 'none' and row['last_text'] is None
            and all(type(row[k]) is int and row[k] == 0 for k in ('step', 'update_count', 'repeat_count', 'send_attempts'))
            and all(row[k] == [] for k in ('sent_ids', 'seen', 'message_ids', 'observations'))
            and type(row['capture_start_offset']) is int and row['capture_start_offset'] == offset,
            'Ordinary own row is no longer exact pristine PREPARED')
    now = time.time()
    created = datetime.fromisoformat(row['created_at'])
    require(created.utcoffset() is not None and 0 <= now - created.timestamp() <= TIMING['operation_seconds']
            and type(row['deadline']) in (int, float) and now + required_time(stage) <= row['deadline']
            and abs(row['deadline'] - created.timestamp() - TIMING['operation_seconds']) <= 1,
            'Ordinary prepared creation clock or full window changed')


def check(proof_ref, *, contract_ref, prepare_ref, authority_ref, run_id, scenario, stage):
    """Check the original three active gates and the separately identified readonly gate."""
    require(stage in SEND_STAGES | {'READONLY', 'NEW'}, 'Unknown ordinary current gate')
    require(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id),
            'Ordinary exact prospective run ID required')
    proof, contract, prepare = (document(ref) for ref in (proof_ref, contract_ref, prepare_ref))
    scenario_sha = digest(encoded(scenario))
    for item, schema in ((proof, 'frw.Root.ordinary-current-proof.v1'),
                         (contract, 'frw.Root.ordinary-current-contract.v1'),
                         (prepare, 'frw.Root.ordinary-current-prepare.v1')):
        require(item.get('schema') == schema and item.get('run_id') == run_id
                and item.get('scenario_sha256') == scenario_sha, 'Ordinary scenario binding changed')
    require(proof['contract'] == contract_ref and proof['prepare'] == prepare_ref
            and contract['authority'] == authority_ref
            and contract['operator'] == 'Root'
            and all(contract['decisions'].get(key) is True for key in DECISIONS),
            'Ordinary explicit current decisions required')
    require(scenario.get('deadline_seconds') == TIMING['operation_seconds']
            and len(scenario.get('steps', ())) == 1
            and scenario['steps'][0]['observe'].get('window_seconds') == TIMING['reply_window_seconds']
            and prepare.get('timing') == TIMING, 'Ordinary operation timing profile changed')
    require(prepare['metadata_helper']['sha256'] == METADATA_SHA, 'Exact reviewed metadata helper required')
    metadata = source_module(prepare['metadata_helper'], '_Root_ordinary_metadata')
    require(metadata.encoded({}) == encoded({}), 'Ordinary canonical encoding changed')
    owner = metadata.kernel(os.getpid())
    require(proof['boot_id'] == owner['boot_id'] and proof['lock_owners']['consumer'] == owner
            and proof['lock_owners']['credential'] == owner, 'Ordinary current lock owner changed')
    slot_owner = proof['lock_owners']['slot']
    if proof['role'] == 'preclock':
        require(slot_owner == owner, 'Ordinary preclock slot belongs to a different process')
    else:
        require(slot_owner == metadata.kernel(os.getppid()), 'Ordinary owned consumer parent changed')

    def locks_and_stop():
        metadata.lock_held(SLOT, slot_owner)
        metadata.lock_held(STATE / 'consumer.lock', owner)
        metadata.lock_held(STATE / 'tester-token', owner)
        require(not os.path.lexists(STATE / 'observer-stop.json'), 'Ordinary observer is stopped')

    locks_and_stop()
    metadata.fresh(proof)
    end = check_operation(proof, run_id, scenario_sha, stage)
    if end is not None:
        require(time.monotonic() + required_time(stage) <= end, 'Ordinary full bounded window no longer fits')
    authority = document(authority_ref)
    require(authority['run_scenarios'] == {run_id: scenario_sha}, 'Ordinary history authority changed')
    bound_cursor = document(contract['cursor'])
    require(Path(contract['cursor']['path']) == STATE / 'cursor.json'
            and type(bound_cursor.get('offset')) is int and bound_cursor['offset'] >= 0,
            'Ordinary capture cursor changed')
    check_run_rows(authority, run_id, scenario, scenario_sha, stage, bound_cursor['offset'])

    check_input(scenario['steps'][0])
    observer = source_module(prepare['current_observer'], '_Root_ordinary_current_observer')
    require(observer.check_current(contract['scope'], scenario=scenario, read_reference=private_reference,
                                   load_module=source_module) is True,
            'Ordinary current route, identity or rights not established')
    locks_and_stop()
    require(document(contract['cursor']) == bound_cursor, 'Ordinary capture cursor changed')
    metadata.fresh(proof)
    if end is not None:
        require(time.monotonic() + required_time(stage) <= end, 'Ordinary full bounded window no longer fits')
    return True
