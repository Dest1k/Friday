"""One future Root-owned original F04 ordinary operation. SOURCE ONLY by default.

UNBOUND input refuses before code/state/current/issuer/slot/clock effects. There
is no retry or resume command. A consumed once or any partial result is reconciled
as the same operation. Actual native ownership is established by current_stop;
an observer exit or a generic idle state never establishes product closure.
"""
import argparse
import contextlib
import copy
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time
import types

ROOT_SCHEMA = 'frw.Root.F04.original-ordinary222.binding.v1'
STATE = '/home/jericho/.local/share/friday-telegram-bot-test'
SLOT = '/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock'
PYTHON = '/home/jericho/jericho/.venv/bin/python'
FIELDS = {'schema', 'status', 'operator', 'root_authority_id', 'root_scope', 'operation_id',
          'run_id', 'scenario_ref', 'scenario_sha256', 'source', 'current', 'clock', 'resources',
          'slot', 'once', 'workdir', 'state_dir', 'authority_scope', 'supersedes_reason',
          'source_freeze', 'independent_review', 'current_stop', 'interpreter', 'boundary_phase'}


def need(condition, code):
    if not condition:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'F04_DUPLICATE_JSON_KEY')
        value[key] = item
    return value


def absolute(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and not any(p in ('', '.', '..') for p in value.split('/')[1:])
         and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value),
         'F04_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    value.encode('utf-8')
    return Path(value)


def reference(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
         and type(value['bytes']) is int and value['bytes'] > 0
         and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['sha256']),
         'F04_PROTECTED_EXACT_REFERENCE_REQUIRED')
    absolute(value['path'])
    return value


def identity(info):
    return tuple(getattr(info, k) for k in ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode',
                                           'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def read(path, *, private=True, cap=24 * 1024 ** 2):
    path = absolute(str(path))
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'F04_PATH_SYMLINK_REFUSED')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        raw = stream.read(cap + 1)
        after = os.fstat(stream.fileno())
    need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
         and not stat.S_IMODE(before.st_mode) & 0o002 and len(raw) <= cap
         and identity(before) == identity(after) == identity(path.stat()),
         'F04_READ_CUSTODY_OR_IDENTITY_CHANGED')
    need(not private or stat.S_IMODE(before.st_mode) == 0o600, 'F04_PRIVATE0600_REQUIRED')
    return raw


def readref(value, *, private=True):
    reference(value)
    raw = read(value['path'], private=private)
    need(len(raw) == value['bytes'] and digest(raw) == value['sha256'], 'F04_REFERENCE_DRIFT')
    return raw


def load(value, name, *, private=True):
    raw = readref(value, private=private)
    module = types.ModuleType(name)
    module.__file__ = value['path']
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def new(path, raw):
    path = absolute(str(path))
    need(not any(p.is_symlink() for p in path.parents), 'F04_NEW_PARENT_SYMLINK_REFUSED')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        offset = 0
        while offset < len(raw):
            amount = os.write(fd, raw[offset:])
            need(amount > 0, 'F04_SHORT_WRITE')
            offset += amount
        os.fsync(fd)
    finally:
        os.close(fd)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def validate_root(root):
    """Pure shape check. Crucially precedes ANY live/dependency observation."""
    need(type(root) is dict and root.get('schema') == ROOT_SCHEMA
         and root.get('status') == 'ROOT_BOUND_EXACT_F04' and root.get('operator') == 'Root',
         'F04_UNBOUND_NO_DISPATCH')
    need(set(root) == FIELDS and root['root_scope'] ==
         'case165/F04/format27_to26/original_required_rich_formula', 'F04_EXACT_ROOT_SCOPE_REQUIRED')
    for key in ('root_authority_id', 'operation_id', 'run_id', 'authority_scope', 'supersedes_reason'):
        need(type(root[key]) is str and root[key].strip() and 'UNBOUND' not in root[key],
             'F04_FRESH_ROOT_FIELD_REQUIRED')
    need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', root['run_id']) is not None,
         'F04_SAFE_RUN_ID_REQUIRED')
    need(root['boundary_phase'] == 'NEW' and root['state_dir'] == STATE
         and root['interpreter'] == PYTHON, 'F04_EXACT_INITIAL_BOUNDARY_REQUIRED')
    for key in ('scenario_ref', 'source', 'clock', 'source_freeze', 'independent_review', 'current_stop'):
        reference(root[key])
    need(root['scenario_sha256'] == root['scenario_ref']['sha256'], 'F04_SCENARIO_DIGEST_REQUIRED')
    need(type(root['current']) is dict and set(root['current']) == {'proof'},
         'F04_ROOT_CURRENT_PROOF_UNBOUND')
    reference(root['current']['proof'])
    slot = root['slot']
    need(type(slot) is dict and set(slot) == {'path', 'identity', 'owner'} and slot['path'] == SLOT
         and slot['owner'] is None, 'F04_FRESH_EXISTING_SLOT_REQUIRED')
    shape = {'device', 'inode', 'uid', 'mode', 'nlink'}
    need(type(slot['identity']) is dict and set(slot['identity']) == shape
         and all(type(v) is int and v >= 0 for v in slot['identity'].values())
         and slot['identity']['mode'] == 0o600 and slot['identity']['nlink'] == 1,
         'F04_EXACT_SLOT_IDENTITY_REQUIRED')
    once = root['once']
    need(type(once) is dict and set(once) == {'path', 'status', 'reference'}
         and once['status'] == 'ABSENT' and once['reference'] is None,
         'F04_UNCONSUMED_ONCE_REQUIRED')
    work = absolute(root['workdir'])
    need(absolute(once['path']) == work / 'ROOT-F04-ONCE.json', 'F04_EXACT_ONCE_PATH_REQUIRED')
    resources = root['resources']
    fixed = {'ordinary_seconds': 300, 'full_capture_seconds': 180, 'ack_seconds': 10,
             'reserve_seconds': 5, 'outer_seconds': 600}
    need(type(resources) is dict and set(resources) == set(fixed) | {
             'cleanup_seconds', 'cpu_seconds', 'max_rss_bytes', 'disk_bytes', 'affinity_cpus'}
         and all(type(resources[k]) is int and resources[k] == v for k, v in fixed.items()),
         'F04_ORIGINAL_300_180_10_5_600_REQUIRED')
    need(type(resources['cleanup_seconds']) is int and 1 <= resources['cleanup_seconds'] <= 60
         and type(resources['cpu_seconds']) is int and 0 < resources['cpu_seconds'] <= 300
         and type(resources['max_rss_bytes']) is int and 0 < resources['max_rss_bytes'] <= 2 * 1024 ** 3
         and type(resources['disk_bytes']) is int and 0 < resources['disk_bytes'] <= 64 * 1024 ** 2
         and type(resources['affinity_cpus']) is list and 1 <= len(resources['affinity_cpus']) <= 2
         and len(set(resources['affinity_cpus'])) == len(resources['affinity_cpus'])
         and all(type(v) is int and v >= 0 for v in resources['affinity_cpus']),
         'F04_FINITE_RESOURCE_CONTRACT_REQUIRED')
    text = ' '.join(root['authority_scope'].lower().split())
    need(all(part in text for part in ('f04', 'ods', 'xlsx', 'original', 'rich', 'formula',
                                      'not a b00 acceptance', 'not a product acceptance')),
         'F04_TRUTHFUL_SINGLETON_SCOPE_REQUIRED')
    return root


def kernel(pid):
    raw = Path('/proc', str(pid), 'stat').read_text()
    tail = raw[raw.rfind(')') + 2:].split()
    return {'pid': pid, 'starttime': int(tail[19]), 'pgid': int(tail[2])}


def remaining(clock, *, cleanup=False):
    prefix = 'cleanup_deadline' if cleanup else 'deadline'
    return max(0.0, min(clock[prefix + '_wall'] - time.time(),
                        clock[prefix + '_monotonic'] - time.monotonic()))


def validate_clock(clock, root):
    fields = {'schema', 'operator', 'operation_id', 'run_id', 'boot_id', 'origin_wall',
              'deadline_wall', 'origin_monotonic', 'deadline_monotonic',
              'cleanup_deadline_wall', 'cleanup_deadline_monotonic'}
    need(type(clock) is dict and set(clock) == fields
         and clock['schema'] == 'frw.Root.F04.original-clock.v1' and clock['operator'] == 'Root'
         and clock['operation_id'] == root['operation_id'] and clock['run_id'] == root['run_id'],
         'F04_EXACT_ORIGINAL_CLOCK_REQUIRED')
    names = fields - {'schema', 'operator', 'operation_id', 'run_id', 'boot_id'}
    need(all(type(clock[k]) in (int, float) and math.isfinite(clock[k]) for k in names),
         'F04_FINITE_CLOCK_REQUIRED')
    now, mono = time.time(), time.monotonic()
    need(clock['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
         and 0 <= clock['origin_wall'] <= now < clock['deadline_wall'] <= clock['origin_wall'] + 600
         and 0 <= clock['origin_monotonic'] <= mono < clock['deadline_monotonic'] <= clock['origin_monotonic'] + 600
         and abs((clock['deadline_wall'] - now) - (clock['deadline_monotonic'] - mono)) <= 2
         and clock['cleanup_deadline_wall'] == clock['deadline_wall']
         and clock['cleanup_deadline_monotonic'] == clock['deadline_monotonic']
         and abs((clock['cleanup_deadline_wall'] - now) -
                 (clock['cleanup_deadline_monotonic'] - mono)) <= 2
         and remaining(clock) >= 305 + root['resources']['cleanup_seconds'],
         'F04_EXPIRED_CHANGED_OR_INSUFFICIENT_CLOCK')
    return clock


def reviewed_sources(root):
    freeze_raw = readref(root['source_freeze'])
    freeze = json.loads(freeze_raw, object_pairs_hook=unique)
    need(type(freeze) is dict and set(freeze) == {'schema', 'files'}
         and freeze['schema'] == 'frw.Root.F04.caller-source-freeze.v1'
         and type(freeze['files']) is dict and set(freeze['files']) == {
             'root_f04.py', 'source_adapter.py', 'current_stop.py'}, 'F04_WHOLE_SOURCE_FREEZE_REQUIRED')
    own = Path(__file__).absolute().parent
    for name, ref in freeze['files'].items():
        if name != 'current_stop.py':
            need(ref['path'] == str(own / name), 'F04_SOURCE_LOCATION_DRIFT')
        readref(ref)
    need(freeze['files']['current_stop.py'] == root['current_stop'], 'F04_EXACT_CURRENT_STOP_REQUIRED')
    review = json.loads(readref(root['independent_review']), object_pairs_hook=unique)
    need(review.get('decision') == 'SOURCE_ONLY_READY_UNBOUND'
         and review.get('source_freeze_sha256') == digest(freeze_raw)
         and review.get('open_critical_defects') == [], 'F04_EXACT_INDEPENDENT_REVIEW_REQUIRED')
    return freeze


def same_source(adapter, root, scenario):
    need(root['source'] == adapter.SOURCE, 'F04_SELECTED_ORIGINAL_METADATA_CHANGED')
    adapter.scenario_shape(scenario)
    raw = readref(root['source'])
    info = absolute(root['source']['path']).stat()
    current = {key: getattr(info, 'st_' + {'device': 'dev', 'inode': 'ino', 'size_bytes': 'size'}.get(key, key))
               for key in adapter.STAT_FIELDS}
    need(current == scenario['steps'][0]['input']['stat'] and len(raw) == adapter.SOURCE['bytes'],
         'F04_FRESH_SELECTED_SOURCE_IDENTITY_CHANGED')


def gate(checker, root, leaves, phase):
    root['boundary_phase'] = phase
    proof = checker.current_gate(root, leaves)
    need(type(proof) is dict and proof.get('matched') is True
         and type(proof.get('current_digest')) is str
         and re.fullmatch('[a-f0-9]{64}', proof['current_digest'])
         and proof.get('root_authority_id') == root['root_authority_id']
         and type(proof.get('native_ownership')) is dict, 'F04_CURRENT_GATE_DID_NOT_BIND_ROOT_EFFECT')
    return proof


def wait_actor(actor, clock, reserve):
    """No time extension. Cleanup targets exact unreaped child, never a process group."""
    if actor.poll() is not None:
        return actor.wait(timeout=0)
    try:
        return actor.wait(timeout=max(0.0, remaining(clock) - reserve))
    except subprocess.TimeoutExpired:
        pass
    for send, parts in ((lambda: actor.send_signal(signal.SIGINT), 3), (actor.terminate, 2), (actor.kill, 1)):
        if actor.poll() is not None:
            return actor.wait(timeout=0)
        # Popen's still-unreaped child identity is ours; no pid-only external kill.
        try:
            send()
        except ProcessLookupError:
            pass
        try:
            return actor.wait(timeout=remaining(clock, cleanup=True) / parts)
        except subprocess.TimeoutExpired:
            pass
    need(actor.poll() is not None, 'F04_STOP_UNCONFIRMED_OWN_CHILD_NOT_REAPED')
    return actor.wait(timeout=0)


def postconditions(full, root, scenario):
    """Read-only verifier on exactly the saved run; no network, wait, save or new."""
    state = Path(STATE)
    class EvidenceView:
        root = state
        runs, captures, downloads = state / 'runs', state / 'updates', state / 'downloads'
        def run_path(self, name):
            return self.runs / (name + '.json')
        def get(self, path, default=None):
            return json.loads(read(path), object_pairs_hook=unique) if Path(path).exists() else default
    result = {'state': 'ACTUAL_POSTCONDITIONS_NOT_ESTABLISHED', 'run_id': root['run_id'],
              'full_saved_custody': False, 'full180': False, 'exactly_one_complete_XLSX': False,
              'semantic_acceptance': 'NOT_ESTABLISHED', 'retry_authorized': False}
    path = state / 'runs' / (root['run_id'] + '.json')
    if not path.exists():
        return result
    raw = read(path)
    run = json.loads(raw, object_pairs_hook=unique)
    result['canonical_run'] = {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}
    need(raw == encoded(run) and run.get('id') == root['run_id'] and run.get('scenario') == scenario
         and run.get('scenario_sha256') == root['scenario_sha256'], 'F04_SAVED_RUN_BINDING_CHANGED')
    if type(run.get('sent_message_id')) is int:
        result['sent_message_id'] = run['sent_message_id']
        result['tester_message_id_namespace'] = True
    def no_sleep(_):
        raise ValueError('F04_POSTCONDITION_NO_WAIT')
    try:
        inspector = full.Runner(EvidenceView(), None, clock=time.time, sleep=no_sleep)
        inspector.verify_reply_custody(run)
        need(read(path) == raw, 'F04_SAVED_RUN_CHANGED_DURING_CUSTODY')
        result['full_saved_custody'] = True
    except Exception as exc:
        result['checker_refusal_class'] = type(exc).__name__
        return result
    result['full180'] = (run.get('status') == 'EVIDENCE_READY' and run.get('send_state') == 'sent'
        and run.get('send_attempts') == 1 and run.get('repeat_count') == 0 and run.get('step') == 0
        and run.get('capture_window_complete') is True
        and run.get('capture_until') == run.get('sent_at', 0) + 180
        and run.get('send_timeout_seconds') == 10 and time.time() >= run.get('capture_until', math.inf))
    docs = [item for item in run.get('observations', []) if item.get('kind') == 'document']
    result['exactly_one_complete_XLSX'] = (len(docs) == 1 and docs[0].get('complete_artifact') is True
        and docs[0].get('artifact_acceptance') == 'RECEIVED_UNGRADED'
        and docs[0].get('advertised_document', {}).get('mime_type') ==
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        and str(docs[0].get('advertised_document', {}).get('file_name', '')).lower().endswith('.xlsx')
        and type(docs[0].get('bytes')) is int and 0 < docs[0]['bytes'] <= 1048576)
    if result['exactly_one_complete_XLSX']:
        result['received_artifact'] = {key: docs[0][key] for key in (
            'path', 'bytes', 'sha256', 'message_id', 'update_id', 'receipt_path', 'receipt_sha256', 'receipt_bytes')}
    if result['full180'] and result['exactly_one_complete_XLSX']:
        result['state'] = 'SAVED_FULL180_CUSTODY_RECEIVED_XLSX_UNGRADED'
    return result


def execute(value):
    validate_root(value)
    root = copy.deepcopy(value)
    freeze = reviewed_sources(root)
    adapter = load(freeze['files']['source_adapter.py'], 'Root_F04_source_adapter')
    checker = load(root['current_stop'], 'Root_F04_current_stop')
    leaves = checker.RuntimeLeaves()
    scenario_raw = readref(root['scenario_ref'])
    scenario = json.loads(scenario_raw, object_pairs_hook=unique)
    need(scenario_raw == encoded(scenario), 'F04_CANONICAL_SCENARIO_REQUIRED')
    adapter.scenario_shape(scenario)
    same_source(adapter, root, scenario)
    clock = validate_clock(json.loads(readref(root['clock']), object_pairs_hook=unique), root)
    work = absolute(root['workdir'])
    need(work.is_dir() and not any(p.is_symlink() for p in (work, *work.parents))
         and work.stat().st_uid == os.getuid() and stat.S_IMODE(work.stat().st_mode) == 0o700
         and work != Path(__file__).absolute().parent, 'F04_PRIVATE_EXISTING_WORKDIR_REQUIRED')
    need(not (Path(STATE) / 'runs' / (root['run_id'] + '.json')).exists(),
         'F04_EXISTING_RUN_RECONCILE_ONLY')
    fd = os.open(SLOT, os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        actual = {'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid,
                  'mode': stat.S_IMODE(info.st_mode), 'nlink': info.st_nlink}
        need(actual == root['slot']['identity'] and stat.S_ISREG(info.st_mode)
             and info.st_uid == os.getuid(), 'F04_SHARED_SLOT_CUSTODY_CHANGED')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root['slot']['owner'] = kernel(os.getpid())
        # Probe existing consumer/credential locks WITHOUT reading credentials.
        for name in ('consumer.lock', 'tester-token'):
            lock = os.open(Path(STATE) / name, os.O_RDWR | os.O_NOFOLLOW)
            try:
                pin = os.fstat(lock)
                need(stat.S_ISREG(pin.st_mode) and pin.st_uid == os.getuid()
                     and pin.st_nlink == 1 and stat.S_IMODE(pin.st_mode) == 0o600,
                     'F04_CANONICAL_LOCK_CUSTODY_CHANGED')
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(lock)
        gate(checker, root, leaves, 'NEW')
        once = {'schema': 'frw.Root.F04.once.v1', 'operator': 'Root', 'operation_id': root['operation_id'],
                'root_authority_id': root['root_authority_id'], 'root_scope': root['root_scope'],
                'run_id': root['run_id'], 'scenario_sha256': root['scenario_sha256'],
                'source_sha256': root['source']['sha256'],
                'scenario_ref': root['scenario_ref'], 'source': root['source'],
                'clock': root['clock'], 'source_freeze': root['source_freeze'], 'no_retry': True}
        root['once']['reference'] = new(root['once']['path'], encoded(once))
        root['once']['status'] = 'CONSUMED'
        gate(checker, root, leaves, 'CURSOR_AUTHORITY')
        # First issuer import occurs only AFTER real Root current + slot + once.
        issuer = load(adapter.ISSUER, 'Root_unchanged_singleton_atomic_issuer', private=False)
        issuer.RUN_ID, issuer.SCENARIO = root['run_id'], Path(root['scenario_ref']['path'])
        issuer.EXTRA_SCENARIOS, issuer.PACKAGE_FILE, issuer.ORDERED_PREDECESSORS = (), None, {}
        issuer.SCOPE, issuer.SUPERSEDES_REASON = root['authority_scope'], root['supersedes_reason']
        # Refuse an already released admission for this operation before publishing.
        for path in issuer.OUT_DIR.glob('INDEPENDENT-AUTHORITY-R*.json'):
            old = json.loads(read(path), object_pairs_hook=unique)
            need(root['run_id'] not in old.get('run_scenarios', {}),
                 'F04_AUTHORITY_ALREADY_ISSUED_RECONCILE_ONLY')
        issuer.validate_scope(root['authority_scope'], {root['run_id']: root['scenario_sha256']})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            issuer.main()
        issued = json.loads(output.getvalue(), object_pairs_hook=unique)
        authority = {key: issued[key] for key in ('path', 'bytes', 'sha256')}
        document = json.loads(readref(authority), object_pairs_hook=unique)
        adapter.verify_issued(document, root, issued['authority_id'])
        base_raw = readref(adapter.BASE, private=False)
        bound_raw = adapter.bind_full_v42(base_raw, root['run_id'], root['scenario_sha256'],
                                          authority, issued['authority_id'])
        bound = new(work / 'bot_tester.f04.root-bound.py', bound_raw)
        binding = {'schema': 'frw.Root.F04.actual-singleton-binding.v1', 'root': root,
                   'authority': authority, 'authority_id': issued['authority_id'], 'source': bound,
                   'retry_authorized': False}
        new(work / 'ROOT-ACTUAL-BINDING.json', encoded(binding))
        same_source(adapter, root, scenario)
        proof = gate(checker, root, leaves, 'PRE_INTENT_REVALIDATION')
        need(remaining(clock) >= 305 + root['resources']['cleanup_seconds'],
             'F04_ORIGINAL_CLOCK_INSUFFICIENT_BEFORE_CHILD')
        cpus = root['resources']['affinity_cpus']
        need(set(cpus) <= os.sched_getaffinity(0), 'F04_DECLARED_CPUS_UNAVAILABLE')
        r = root['resources']
        def child_limits():
            resource.setrlimit(resource.RLIMIT_CPU, (r['cpu_seconds'], r['cpu_seconds']))
            resource.setrlimit(resource.RLIMIT_AS, (r['max_rss_bytes'], r['max_rss_bytes']))
            resource.setrlimit(resource.RLIMIT_FSIZE, (r['disk_bytes'], r['disk_bytes']))
            os.sched_setaffinity(0, cpus)
        argv = [PYTHON, '-I', '-B', '-S', bound['path'], '--state-dir', STATE,
                'run', '--run-id', root['run_id'], '--scenario', root['scenario_ref']['path']]
        new(work / 'ROOT-DISPATCH-INVOCATION.json', encoded({'argv': argv, 'source': bound,
                                                          'clock': root['clock'], 'no_retry': True}))
        actor, ownership, received, failure = None, None, {}, None
        previous = {n: signal.getsignal(n) for n in (signal.SIGINT, signal.SIGTERM)}
        pending = []
        def parent_stop(number, _):
            pending.append(number)
            if actor is not None and actor.poll() is None:
                try:
                    actor.send_signal(number)
                except ProcessLookupError:
                    pass
        read_fd, release_fd = os.pipe2(os.O_CLOEXEC)
        # This child imports only stdlib and blocks before exec. The full tester
        # cannot observe credentials/current or call Runner.new before release.
        birth_gate = ('import os,sys; f=int(sys.argv[1]); b=os.read(f,1); os.close(f); '
                      'sys.exit(125) if b!=b"1" else os.execv(sys.argv[2],sys.argv[2:])')
        with contextlib.ExitStack() as streams:
            out = streams.enter_context(os.fdopen(os.open(work / 'CONSUMER.stdout',
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb'))
            err = streams.enter_context(os.fdopen(os.open(work / 'CONSUMER.stderr',
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb'))
            try:
                for number in previous:
                    signal.signal(number, parent_stop)
                need(not pending, 'F04_PARENT_STOP_BEFORE_CHILD')
                launch = [PYTHON, '-I', '-B', '-S', '-c', birth_gate, str(read_fd)] + argv
                actor = subprocess.Popen(launch, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                         pass_fds=(fd, read_fd), preexec_fn=child_limits, start_new_session=True)
                os.close(read_fd)
                read_fd = None
                ownership = {'actor': kernel(actor.pid), 'native_ownership': proof['native_ownership'],
                             'clock': clock, 'shared_slot_owner': root['slot']['owner'],
                             'run_id': root['run_id'], 'operation_id': root['operation_id']}
                new(work / 'ROOT-OWNED-ACTOR.json', encoded(ownership))
                gate(checker, root, leaves, 'PRE_INTENT_REVALIDATION')
                need(not pending and remaining(clock) >= 305 + root['resources']['cleanup_seconds'],
                     'F04_STOP_OR_CLOCK_BEFORE_TESTER_RELEASE')
                need(os.write(release_fd, b'1') == 1, 'F04_CHILD_RELEASE_FAILED')
                os.close(release_fd)
                release_fd = None
                for number in pending:
                    if actor.poll() is None:
                        actor.send_signal(number)
                code = wait_actor(actor, clock, r['cleanup_seconds'])
                full = load(bound, 'Root_completed_F04_readonly_custody')
                received = postconditions(full, root, scenario)
            except BaseException as exc:
                failure = exc
            finally:
                try:
                    for pipe_fd in (read_fd, release_fd):
                        if pipe_fd is not None:
                            os.close(pipe_fd)
                    if actor is not None and actor.poll() is None:
                        wait_actor(actor, clock, r['cleanup_seconds'])
                    if actor is not None:
                        need(ownership is not None, 'F04_STOP_UNCONFIRMED_NO_ACTOR_IDENTITY')
                        # Keep a copy, not a reference cycle. Closure receives the
                        # same exact actor and native scope as the stop call.
                        received['ownership'] = copy.deepcopy(ownership)
                        ownership['received'] = copy.deepcopy(received)
                        # Concrete module must resolve native own-turn identity before stop.
                        stopped = checker.stop_owned(root, ownership, leaves)
                        closure = checker.owned_closure(root, received, leaves)
                        ended = {'schema': 'frw.Root.F04.ended.v1', 'child_exit_code': actor.returncode,
                                 'child_reaped': actor.poll() is not None, 'received': received,
                                 'owned_stop': stopped, 'owned_closure': closure,
                                 'parent_stop_signals': pending, 'retry_authorized': False,
                                 'semantic_acceptance': 'NOT_ESTABLISHED'}
                        new(work / 'ROOT-DISPATCH-ENDED.json', encoded(ended))
                        need(stopped.get('confirmed') is True and closure.get('closed') is True,
                             'F04_STOP_UNCONFIRMED_NATIVE_OR_RESOURCE_CLOSURE')
                finally:
                    for number, handler in previous.items():
                        signal.signal(number, handler)
            if failure is not None:
                raise failure
        return ended
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-binding', required=True)
    args = parser.parse_args(argv)
    root = json.loads(read(args.root_binding), object_pairs_hook=unique)
    result = execute(root)
    # Logs, bindings and receipts remain protected. No private caption/source data on stdout.
    print(json.dumps({'state': 'ROOT_OPERATION_ENDED', 'child_reaped': result['child_reaped'],
                      'retry_authorized': False, 'semantic_acceptance': 'NOT_ESTABLISHED'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
