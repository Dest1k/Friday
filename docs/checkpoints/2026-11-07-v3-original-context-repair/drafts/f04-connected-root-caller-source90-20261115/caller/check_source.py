"""Static source controls. Every lifecycle/current/process leaf is in memory.

Reads only addressed source and own templates. Never imports full v42/issuer,
calls product Runner.new/main, observes actual current, or reads workbook/state.
"""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import types
import unicodedata
from unittest.mock import patch

HERE = Path(__file__).absolute().parent


def local(name):
    spec = importlib.util.spec_from_file_location('_F04_check_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a, caller = local('source_adapter'), local('root_f04')
RESULTS = []
current = None


def check(name, function):
    try:
        function()
    except Exception as exc:
        RESULTS.append({'check': name, 'passed': False, 'class': type(exc).__name__})
    else:
        RESULTS.append({'check': name, 'passed': True})


def require(condition):
    if not condition:
        raise AssertionError('SOURCE_CONTROL_FAILED')


def refused(function, code=None):
    try:
        function()
    except (ValueError, SystemExit, FileExistsError, schema['Refused'],
            current.Refused if current is not None else ValueError) as exc:
        if code is not None:
            require(str(exc) == code)
        return
    raise AssertionError('NEGATIVE_CONTROL_DID_NOT_REFUSE')


base_raw = Path(a.BASE['path']).read_bytes()
issuer_raw = Path(a.ISSUER['path']).read_bytes()
require(len(base_raw) == a.BASE['bytes'] and a.digest(base_raw) == a.BASE['sha256'])
require(len(issuer_raw) == a.ISSUER['bytes'] and a.digest(issuer_raw) == a.ISSUER['sha256'])
tree, issuer_tree = ast.parse(base_raw), ast.parse(issuer_raw)
pin = {'device': 1, 'inode': 2, 'size_bytes': a.SOURCE['bytes'], 'uid': os.getuid(),
       'mtime_ns': 3, 'ctime_ns': 4}
scenario = a.construct_scenario(pin)
scenario_raw = a.encoded(scenario)
dummy_authority = {'path': '/synthetic/authority.json', 'bytes': 123, 'sha256': '1' * 64}


def generic_schema_namespace():
    # Actual function AST bodies only: no Runner, Store, BotAPI, main, or module
    # initialization is compiled. Constants are static expressions from pinned AST.
    names = {'validate_document_input', 'validate_scenario', 'validate_reply_capture', 'validate_capture',
             'reply_capture', 'bounded_capture', 'ordinary_s15_reply_capture', 'ordinary_s16_reply_capture',
             'ordinary_s15_roundtrip', 'ordinary_s16_untrusted_table', 'stopped1578_capture_scenario'}
    constants = {'TESTER', 'PEER', 'USERNAME', 'MAX_FILE', 'MAX_UPLOAD', 'UPLOAD_TYPES',
                 'INPUT_STAT_FIELDS', 'REPLY_WINDOW_RESERVE', 'REPLY_ACK_RESERVE',
                 'S15_OUTPUT', 'S15_CAPTURE', 'S16_OUTPUT', 'S16_CAPTURE'}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Refused':
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id in constants
                                                 for n in node.targets):
            require(all(isinstance(n.func, ast.Name) and n.func.id == 'dict'
                        for n in ast.walk(node.value) if isinstance(n, ast.Call)))
            nodes.append(node)
    namespace = {'os': os, 're': re, 'unicodedata': unicodedata, 'Path': Path, 'encoded': a.encoded,
                 'CANONICAL_STATE': Path('/synthetic/operator-private-state')}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<isolated-v42-schema-AST>', 'exec'), namespace)
    return namespace


schema = generic_schema_namespace()
check('actual_v42_schema_accepts_original_singleton', lambda: require(schema['validate_scenario'](scenario) == scenario))


def mutate_scenario(function):
    changed = copy.deepcopy(scenario)
    function(changed)
    return changed


for name, mutation in [
    ('generic_rejects_stat_missing', lambda s: s['steps'][0]['input'].pop('stat')),
    ('generic_rejects_private_extra_input', lambda s: s['steps'][0]['input'].update(oracle='synthetic')),
    ('generic_rejects_expected_output_in_capture', lambda s: s['steps'][0]['observe'].update(sha256='0' * 64)),
    ('generic_rejects_changed_input_mime', lambda s: s['steps'][0]['input'].update(mime_type='application/octet-stream')),
    ('generic_rejects_too_short_window_budget', lambda s: s.update(deadline_seconds=180)),
]:
    check(name, lambda mutation=mutation: refused(lambda: schema['validate_scenario'](mutate_scenario(mutation))))

check('strict_adapter_accepts_exact_original_shape', lambda: require(a.scenario_shape(scenario) == scenario))
for name, mutation in [
    ('adapter_rejects_short_capture', lambda s: s['steps'][0]['observe'].update(window_seconds=179)),
    ('adapter_rejects_extra_step', lambda s: s['steps'].append(copy.deepcopy(s['steps'][0]))),
    ('adapter_rejects_changed_source_path', lambda s: s['steps'][0]['input'].update(path='/synthetic/renamed.ods')),
    ('adapter_rejects_tool_forcing_caption', lambda s: s['steps'][0]['input'].update(caption='Call a tool now')),
    ('adapter_rejects_unknown_future_output', lambda s: s['steps'][0]['observe'].update(filename='future.xlsx')),
]:
    check(name, lambda mutation=mutation: refused(lambda: a.scenario_shape(mutate_scenario(mutation))))

bound = a.bind_full_v42(base_raw, 'synthetic-unstarted-f04', a.digest(scenario_raw),
                        dummy_authority, 'synthetic-new-authority')
check('exact_three_seams_remaining_full_ast_identical', lambda: require(
    a._normalized(tree, a.OLD_AUTHORITY) == a._normalized(ast.parse(bound), 'synthetic-new-authority')))
check('full_tester_not_executed_or_imported', lambda: require('Runner' not in globals() and 'BotAPI' not in globals()))
check('rejects_drifted_full_v42_source', lambda: refused(lambda: a.bind_full_v42(
    base_raw + b'\n', 'synthetic-f04', a.digest(scenario_raw), dummy_authority, 'synthetic-new-authority')))
check('rejects_original_r68_authority_reuse', lambda: refused(lambda: a.bind_full_v42(
    base_raw, 'synthetic-f04', a.digest(scenario_raw), dummy_authority, a.OLD_AUTHORITY)))
check('rejects_unbound_authority_reference', lambda: refused(lambda: a.bind_full_v42(
    base_raw, 'synthetic-f04', a.digest(scenario_raw), None, 'synthetic-new-authority')))

runner_ast = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
ack = next(n for n in runner_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'send_ack_budget')
ack_namespace = {'Refused': ValueError, 'REPLY_ACK_RESERVE': schema['REPLY_ACK_RESERVE']}
exec(compile(ast.Module(body=[ack], type_ignores=[]), '<isolated-v42-ACK-body>', 'exec'), ack_namespace)
fake_ack = types.SimpleNamespace(continuation_receipt=lambda run: None)
check('actual_v42_normal_ack_10_reserve_5_preserved', lambda: require(
    ack_namespace['send_ack_budget'](fake_ack, {}) == 10 and schema['REPLY_WINDOW_RESERVE'] == 5))
check('actual_v42_rejects_f03_ack30_override', lambda: refused(lambda:
    ack_namespace['send_ack_budget'](fake_ack, {'new_ack_timeout_seconds': 30})))


class MemoryPath:
    def __init__(self, *parts):
        self.value = str(PurePosixPath(*map(str, parts)))
    def __str__(self): return self.value
    def __truediv__(self, other): return MemoryPath(self.value, other)
    def __eq__(self, other): return isinstance(other, MemoryPath) and self.value == other.value
    def __hash__(self): return hash(self.value)
    @property
    def parent(self): return MemoryPath(PurePosixPath(self.value).parent)
    @property
    def parents(self): return tuple(MemoryPath(p) for p in PurePosixPath(self.value).parents)
    def absolute(self): return self
    def is_dir(self): return True
    def is_symlink(self): return False
    def exists(self): return False
    def stat(self): return types.SimpleNamespace(st_uid=1000, st_mode=stat.S_IFDIR | 0o700)
    def glob(self, pattern): return []
    def read_text(self):
        require(self.value in MEMORY_SCENARIOS)
        return MEMORY_SCENARIOS[self.value]


MEMORY_SCENARIOS = {'/synthetic/scenario.json': scenario_raw.decode()}
issuer_namespace = {'json': json, 'hashlib': hashlib, 'Path': MemoryPath}
issuer_nodes = [n for n in issuer_tree.body if isinstance(n, ast.FunctionDef)
                and n.name in {'digest', 'encoded', 'collect_scenarios', 'validate_scope'}]
exec(compile(ast.Module(body=issuer_nodes, type_ignores=[]), '<isolated-unchanged-issuer-pure-API>', 'exec'), issuer_namespace)
check('actual_issuer_singleton_API_no_extra_package', lambda: require(
    issuer_namespace['collect_scenarios']('synthetic-unstarted-f04', '/synthetic/scenario.json', (), None)
    == {'synthetic-unstarted-f04': a.digest(scenario_raw)}))
check('actual_issuer_duplicate_singleton_refused', lambda: refused(lambda:
    issuer_namespace['collect_scenarios']('synthetic-unstarted-f04', '/synthetic/scenario.json',
        (('synthetic-unstarted-f04', '/synthetic/scenario.json'),), None)))


def synthetic_root():
    def ref(name): return {'path': '/synthetic/' + name, 'bytes': 1, 'sha256': '2' * 64}
    value = {key: None for key in caller.FIELDS}
    value.update(schema=caller.ROOT_SCHEMA, status='ROOT_BOUND_EXACT_F04', operator='Root',
        root_authority_id='synthetic-root-approval', root_scope=a.ROOT_SCOPE,
        operation_id='synthetic-unstarted-operation', run_id='synthetic-unstarted-f04',
        scenario_ref={'path': '/synthetic/scenario.json', 'bytes': len(scenario_raw), 'sha256': a.digest(scenario_raw)},
        scenario_sha256=a.digest(scenario_raw), source=copy.deepcopy(a.SOURCE),
        current={'proof': ref('current-proof')}, clock=ref('clock'),
        resources={'ordinary_seconds': 300, 'full_capture_seconds': 180, 'ack_seconds': 10,
                   'reserve_seconds': 5, 'outer_seconds': 600, 'cleanup_seconds': 60,
                   'cpu_seconds': 120, 'max_rss_bytes': 1024 ** 3, 'disk_bytes': 32 * 1024 ** 2,
                   'affinity_cpus': [0]},
        slot={'path': caller.SLOT, 'identity': {'device': 1, 'inode': 2, 'uid': 1000, 'mode': 0o600, 'nlink': 1}, 'owner': None},
        once={'path': '/synthetic/work/ROOT-F04-ONCE.json', 'status': 'ABSENT', 'reference': None},
        workdir='/synthetic/work', state_dir=caller.STATE,
        authority_scope='Original F04 ODS to XLSX rich formula singleton. NOT a B00 acceptance; NOT a product acceptance.',
        supersedes_reason='Synthetic source-control only; no old effect replay.', source_freeze=ref('freeze'),
        independent_review=ref('review'), current_stop=ref('current_stop.py'),
        interpreter=caller.PYTHON, boundary_phase='NEW')
    return value


def exercise_lifecycle(*, reject_phase=None, stop_confirmed=True, replay=False,
                       fail_kernel=False, fail_actor_record=False, actual_scope_gap=False):
    events, files = [], {}
    root = synthetic_root()
    caller.validate_root(root)
    clock = {'deadline_wall': 600, 'deadline_monotonic': 600,
             'cleanup_deadline_wall': 600, 'cleanup_deadline_monotonic': 600}
    authority_doc = {'schema': 'frw.Root.ordinary-independent-history-admission.v1',
        'authority_id': 'synthetic-new-authority', 'operator': 'Root', 'accepted': True,
        'run_scenarios': {root['run_id']: root['scenario_sha256']}, 'scope': root['authority_scope'],
        'product_or_B00_acceptance': False, 'new_trial_for_historical_task': False,
        'unknown_effects_resolved': False}
    authority_raw = a.encoded(authority_doc)
    authority_ref = {'path': '/synthetic/issued.json', 'bytes': len(authority_raw), 'sha256': a.digest(authority_raw)}
    class Actor:
        pid = 123
        returncode = None
        def poll(self): return self.returncode
        def wait(self, timeout):
            events.append('wait_reap')
            self.returncode = 0
            return 0
        def send_signal(self, number): events.append('signal_exact_child')
        def terminate(self): events.append('terminate_exact_child')
        def kill(self): events.append('kill_exact_child')
    actor = Actor()
    def create(path, raw):
        key = str(path)
        if fail_actor_record and key.endswith('/ROOT-OWNED-ACTOR.json'):
            raise OSError('SYNTHETIC_ACTOR_RECORD_FAILURE')
        if key in files: raise FileExistsError('synthetic-O_EXCL')
        files[key] = raw
        events.append('new:' + PurePosixPath(key).name)
        return {'path': key, 'bytes': len(raw), 'sha256': a.digest(raw)}
    def fresh_gate(config, leaves):
        phase = config['boundary_phase']
        events.append('gate:' + phase)
        require(config['slot']['owner']['pid'] == 99)
        if phase == 'NEW': require(config['once']['status'] == 'ABSENT')
        else:
            marker = json.loads(files[config['once']['path']])
            require(config['once']['status'] == 'CONSUMED' and marker['no_retry'] is True
                    and marker['scenario_sha256'] == root['scenario_sha256']
                    and marker['source_sha256'] == a.SOURCE['sha256'])
        if actual_scope_gap:
            with inert_static_capture():
                current.require_owned_stop_capability(config, current.RuntimeLeaves())
        occurrence = events.count('gate:' + phase)
        if phase == reject_phase or (phase, occurrence) == reject_phase:
            raise ValueError('SYNTHETIC_CURRENT_CHANGED')
        return {'matched': True, 'current_digest': '3' * 64,
                'root_authority_id': root['root_authority_id'], 'native_ownership': {'seed': 'synthetic'}}
    def stop(config, ownership, leaves):
        events.append('stop_correlated_native')
        require(ownership['actor']['pid'] == 123 and ownership['native_ownership'] == {'seed': 'synthetic'})
        return {'confirmed': stop_confirmed}
    def closure(config, received, leaves):
        events.append('actual_owned_closure')
        require(received['ownership']['actor']['pid'] == 123)
        return {'closed': stop_confirmed}
    checker = types.SimpleNamespace(RuntimeLeaves=lambda: object(), current_gate=fresh_gate,
                                    stop_owned=stop, owned_closure=closure)
    issuer = types.SimpleNamespace(OUT_DIR=MemoryPath('/synthetic/issuer'), validate_scope=lambda *args: None)
    def issue():
        events.append('issuer_main')
        require(issuer.RUN_ID == root['run_id'] and str(issuer.SCENARIO) == root['scenario_ref']['path']
                and issuer.EXTRA_SCENARIOS == () and issuer.PACKAGE_FILE is None
                and issuer.ORDERED_PREDECESSORS == {} and issuer.SCOPE == root['authority_scope'])
        print(json.dumps(dict(authority_ref, authority_id='synthetic-new-authority')))
    issuer.main = issue
    def loader(ref, name, **kwargs):
        events.append('load:' + name)
        if 'source_adapter' in name: return a
        if 'current_stop' in name: return checker
        if 'atomic_issuer' in name: return issuer
        if 'readonly_custody' in name:
            require(actor.returncode == 0)
            return object()
        raise AssertionError('UNEXPECTED_MODULE_LOAD')
    def reader(ref, **kwargs):
        if ref == root['scenario_ref']: return scenario_raw
        if ref == root['clock']: return b'{}'
        if ref == a.BASE: return base_raw
        if ref == authority_ref: return authority_raw
        raise AssertionError('UNEXPECTED_REFERENCE_READ')
    fake_os = types.SimpleNamespace(**{k: getattr(os, k) for k in (
        'O_RDWR', 'O_NOFOLLOW', 'O_WRONLY', 'O_CREAT', 'O_EXCL', 'O_CLOEXEC')})
    fake_os.getuid = lambda: 1000
    fake_os.getpid = lambda: 99
    fake_os.open = lambda *args: 11
    fake_os.fstat = lambda fd: types.SimpleNamespace(st_dev=1, st_ino=2, st_uid=1000,
                                                     st_mode=stat.S_IFREG | 0o600, st_nlink=1)
    fake_os.close = lambda fd: events.append('close_fd')
    fake_os.fdopen = lambda *args: io.BytesIO()
    fake_os.pipe2 = lambda flags: (21, 22)
    fake_os.write = lambda fd, raw: events.append('release_tester_exec') or len(raw)
    fake_os.sched_getaffinity = lambda pid: {0, 1}
    fake_os.sched_setaffinity = lambda pid, cpus: events.append('consumer_affinity')
    def popen(argv, **kwargs):
        events.append('birth_inert_child')
        require(argv[1:5] == ['-I', '-B', '-S', '-c'] and 'os.read(f,1)' in argv[5])
        require(kwargs['pass_fds'] == (11, 21) and kwargs['start_new_session'] is True)
        kwargs['preexec_fn']()
        return actor
    def actor_kernel(pid):
        if pid == 123 and fail_kernel:
            raise ValueError('SYNTHETIC_ACTOR_KERNEL_FAILURE')
        return {'pid': pid, 'starttime': 7, 'pgid': pid}
    fake_subprocess = types.SimpleNamespace(Popen=popen, DEVNULL=-3, TimeoutExpired=TimeoutError)
    fake_signal = types.SimpleNamespace(SIGINT=2, SIGTERM=15, getsignal=lambda number: None,
                                       signal=lambda *args: None)
    fake_resource = types.SimpleNamespace(RLIMIT_CPU=0, RLIMIT_AS=1, RLIMIT_FSIZE=2,
        setrlimit=lambda kind, values: events.append('consumer_resource:' + str(kind)))
    freeze = {'files': {'source_adapter.py': {'path': '/synthetic/source_adapter.py'}}}
    replacements = dict(Path=MemoryPath, os=fake_os, subprocess=fake_subprocess, signal=fake_signal,
        resource=fake_resource, fcntl=types.SimpleNamespace(LOCK_EX=2, LOCK_NB=4,
        flock=lambda *args: events.append('exact_slot_or_probe_lock')),
        reviewed_sources=lambda config: freeze, load=loader, readref=reader, new=create,
        same_source=lambda *args: events.append('fresh_source_custody'),
        validate_clock=lambda value, config: clock, remaining=lambda *args, **kwargs: 500,
        kernel=actor_kernel,
        postconditions=lambda *args: {'full180': True, 'full_saved_custody': True,
            'exactly_one_complete_XLSX': True, 'sent_message_id': 18,
            'tester_message_id_namespace': True, 'semantic_acceptance': 'NOT_ESTABLISHED'})
    with patch.multiple(caller, **replacements):
        if fail_actor_record:
            try:
                caller.execute(root)
            except OSError:
                pass
            else:
                raise AssertionError('ACTOR_RECORD_NEGATIVE_NOT_REFUSED')
        elif reject_phase or not stop_confirmed or fail_kernel or actual_scope_gap:
            refused(lambda: caller.execute(root))
        else:
            ended = caller.execute(root)
            require(ended['child_reaped'] and ended['owned_closure']['closed'])
            require(ended['semantic_acceptance'] == 'NOT_ESTABLISHED' and not ended['retry_authorized'])
            if replay: refused(lambda: caller.execute(root))
    return events, files


def successful_order():
    events, files = exercise_lifecycle()
    def at(name): return events.index(name)
    require(at('gate:NEW') < at('new:ROOT-F04-ONCE.json') < at('gate:CURSOR_AUTHORITY')
            < at('load:Root_unchanged_singleton_atomic_issuer') < at('issuer_main')
            < at('birth_inert_child') < at('release_tester_exec') < at('wait_reap')
            < at('load:Root_completed_F04_readonly_custody') < at('stop_correlated_native')
            < at('actual_owned_closure'))
    require(events.count('gate:PRE_INTENT_REVALIDATION') == 2
            and events.count('issuer_main') == 1 and events.count('release_tester_exec') == 1
            and all('consumer_resource:' + str(n) in events for n in (0, 1, 2)))
    require(set(files) >= {'/synthetic/work/ROOT-F04-ONCE.json', '/synthetic/work/ROOT-DISPATCH-ENDED.json'})


check('connected_lifecycle_all_leaves_inert_order_and_finite_resources', successful_order)


def current_refusal_after_once():
    events, files = exercise_lifecycle(reject_phase='CURSOR_AUTHORITY')
    require('new:ROOT-F04-ONCE.json' in events and 'issuer_main' not in events
            and 'birth_inert_child' not in events)


check('current_change_consumes_once_without_issuer_or_child', current_refusal_after_once)


def no_replay():
    events, _ = exercise_lifecycle(replay=True)
    require(events.count('issuer_main') == events.count('birth_inert_child') == events.count('release_tester_exec') == 1)


check('consumed_once_refuses_replay_without_second_issuer_or_send', no_replay)
check('ambiguous_owned_stop_refuses_closure_without_retry', lambda: exercise_lifecycle(stop_confirmed=False))


def birth_barrier_refusal():
    events, files = exercise_lifecycle(reject_phase=('PRE_INTENT_REVALIDATION', 2))
    require(events.count('birth_inert_child') == 1 and 'release_tester_exec' not in events
            and 'load:Root_completed_F04_readonly_custody' not in events
            and 'stop_correlated_native' in events and 'wait_reap' in events)


check('current_change_after_birth_never_releases_tester_and_reaps_owned_child', birth_barrier_refusal)


def before_release_actor_failure(**failure):
    events, _ = exercise_lifecycle(**failure)
    require('birth_inert_child' in events and 'wait_reap' in events
            and 'release_tester_exec' not in events
            and 'load:Root_completed_F04_readonly_custody' not in events)


check('kernel_identity_failure_reaps_unreleased_child', lambda: before_release_actor_failure(fail_kernel=True))
check('actor_proof_write_failure_reaps_unreleased_child', lambda: before_release_actor_failure(fail_actor_record=True))


def check_actual_postconditions(**changes):
    root = synthetic_root()
    document = {'kind': 'document', 'complete_artifact': True, 'artifact_acceptance': 'RECEIVED_UNGRADED',
        'advertised_document': {'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                'file_name': 'returned.xlsx'},
        'bytes': 9, 'sha256': '5' * 64, 'message_id': 32, 'update_id': 33,
        'path': '/synthetic/received.bin', 'receipt_path': '/synthetic/receipt.json',
        'receipt_sha256': '6' * 64, 'receipt_bytes': 10}
    run = {'id': root['run_id'], 'scenario': scenario, 'scenario_sha256': root['scenario_sha256'],
        'sent_message_id': 18, 'status': 'EVIDENCE_READY', 'send_state': 'sent', 'send_attempts': 1,
        'repeat_count': 0, 'step': 0, 'capture_window_complete': True, 'sent_at': 1,
        'capture_until': 181, 'send_timeout_seconds': 10, 'observations': [document]}
    run.update(changes)
    raw = a.encoded(run)
    called = []
    class SavedPath(MemoryPath):
        def __truediv__(self, other): return SavedPath(self.value, other)
        def exists(self): return True
    class Verifier:
        def __init__(self, store, api, **kwargs):
            require(api is None)
        def verify_reply_custody(self, value):
            require(value == run)
            called.append('same-run-custody-delegate')
    full = types.SimpleNamespace(Runner=Verifier)
    with patch.multiple(caller, Path=SavedPath, read=lambda *args, **kwargs: raw,
                        time=types.SimpleNamespace(time=lambda: 200)):
        result = caller.postconditions(full, root, scenario)
    require(called == ['same-run-custody-delegate'] and result['sent_message_id'] == 18
            and result['tester_message_id_namespace'] is True
            and result['semantic_acceptance'] == 'NOT_ESTABLISHED' and not result['retry_authorized'])
    return result


check('actual_postcondition_body_requires_same_run_custody_full180_one_XLSX', lambda: require(
    check_actual_postconditions()['state'] == 'SAVED_FULL180_CUSTODY_RECEIVED_XLSX_UNGRADED'))
check('postcondition_rejects_old_ACK30', lambda: require(not check_actual_postconditions(send_timeout_seconds=30)['full180']))
check('postcondition_rejects_partial_capture', lambda: require(not check_actual_postconditions(capture_window_complete=False)['full180']))
check('postcondition_rejects_repeated_send', lambda: require(not check_actual_postconditions(send_attempts=2)['full180']))


def actual_clock_check(*, extension=0):
    root = synthetic_root()
    clock = {'schema': 'frw.Root.F04.original-clock.v1', 'operator': 'Root',
        'operation_id': root['operation_id'], 'run_id': root['run_id'], 'boot_id': 'synthetic-boot',
        'origin_wall': 1000, 'deadline_wall': 1600, 'origin_monotonic': 2000,
        'deadline_monotonic': 2600, 'cleanup_deadline_wall': 1600 + extension,
        'cleanup_deadline_monotonic': 2600 + extension}
    class BootPath(MemoryPath):
        def read_text(self):
            require(self.value == '/proc/sys/kernel/random/boot_id')
            return 'synthetic-boot'
    with patch.multiple(caller, Path=BootPath,
                        time=types.SimpleNamespace(time=lambda: 1000, monotonic=lambda: 2000)):
        return caller.validate_clock(clock, root)


check('actual_clock_body_accepts_cleanup_carved_inside_original600', lambda: require(
    actual_clock_check()['cleanup_deadline_wall'] == 1600))
check('actual_clock_body_rejects_extended_cleanup_endpoint', lambda: refused(lambda: actual_clock_check(extension=60)))


def actual_wait_reserve():
    waits, signals = [], []
    class Timeout(Exception): pass
    class Actor:
        returncode = None
        def poll(self): return self.returncode
        def wait(self, timeout):
            waits.append(timeout)
            if len(waits) == 1: raise Timeout()
            self.returncode = 0
            return 0
        def send_signal(self, number): signals.append(number)
        def terminate(self): raise AssertionError('UNNECESSARY_TERM')
        def kill(self): raise AssertionError('UNNECESSARY_KILL')
    with patch.multiple(caller, subprocess=types.SimpleNamespace(TimeoutExpired=Timeout),
                        remaining=lambda clock, cleanup=False: 60 if cleanup else 600):
        require(caller.wait_actor(Actor(), {}, 60) == 0)
    require(waits == [540, 20] and signals == [caller.signal.SIGINT])


check('actual_wait_body_reserves_cleanup_inside_same_endpoint', actual_wait_reserve)


# The concrete current/stop source and exact Root-captured native source are
# static dependencies. No captured gateway module is imported. Their contents
# are supplied only to the actual AST inspector through inert whitelist leaves.
current_ref = json.loads((HERE / 'FINAL-CURRENT-STOP-REF.json').read_text())
current_raw = Path(current_ref['path']).read_bytes()
require(len(current_raw) == current_ref['bytes'] and a.digest(current_raw) == current_ref['sha256'])
current = types.ModuleType('_F04_actual_current_source_controls')
current.__file__ = current_ref['path']
exec(compile(current_raw, current.__file__, 'exec'), current.__dict__)
capture_path = Path('/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source/SOURCE-REFS.json')
capture_raw = capture_path.read_bytes()
require(a.digest(capture_raw) == 'afb7713b2e9150d268bcd2fc524fbc384fb7547b7a97e8a7712ae71cc3643f64')
capture = json.loads(capture_raw)
captured_bodies = {}
for pin in capture['files'].values():
    body = Path(pin['path']).read_bytes()
    require(len(body) == pin['bytes'] and a.digest(body) == pin['sha256'])
    captured_bodies[pin['path']] = body


@contextlib.contextmanager
def inert_static_capture(*, corrupt=False):
    def static_docref(ref, **kwargs):
        require(ref == current.CAPTURE_REFS)
        return copy.deepcopy(capture)
    def static_readref(ref, **kwargs):
        require(ref['path'] in captured_bodies)
        body = captured_bodies[ref['path']]
        if corrupt: body += b'\n'
        current.need(len(body) == ref['bytes'] and a.digest(body) == ref['sha256'],
                     'F04_STATIC_CAPTURE_PIN_CHANGED')
        return body
    with patch.multiple(current, docref=static_docref, readref=static_readref):
        yield


def actual_static_capability():
    with inert_static_capture():
        report = current.RuntimeLeaves().owned_stop_capability({'implemented': True, 'operation_id': 'root-v04-synthetic'})
    require(report['source_verified'] is True and report['implemented'] is False
            and report['assertcode'] == 'F04_STOP_API_SCOPE_UNSUPPORTED'
            and report['F04_relabel_permitted'] is False
            and report['typed_ingress_artifact_terminal_bridge'] is False)
    return report


check('actual_final_current_source_inspector_derives_F04_scope_refusal_from_pinned_AST', actual_static_capability)


def actual_capture_drift_refusal():
    with inert_static_capture(corrupt=True):
        refused(lambda: current.inspect_owned_stop_source(), 'F04_STATIC_CAPTURE_PIN_CHANGED')


check('final_current_inspector_rejects_changed_captured_native_source', actual_capture_drift_refusal)


def concrete_unsupported_stop_refuses_before_once():
    events, files = exercise_lifecycle(actual_scope_gap=True)
    require('gate:NEW' in events and not files
            and 'issuer_main' not in events and 'birth_inert_child' not in events
            and 'release_tester_exec' not in events)


check('concrete_source_bound_unsupported_F04_stop_refuses_caller_before_ONCE_issuer_child',
      concrete_unsupported_stop_refuses_before_once)


def unbound_zero_effects():
    template = json.loads((HERE / 'ROOT-BINDING.template.json').read_text())
    with patch.object(caller, 'reviewed_sources', side_effect=AssertionError('FORBIDDEN_LEAF')):
        refused(lambda: caller.execute(template), 'F04_UNBOUND_NO_DISPATCH')


check('unbound_default_refuses_before_any_dependency_or_current_leaf', unbound_zero_effects)


def full_ack_no_override_in_source():
    rt = ast.parse((HERE / 'root_f04.py').read_bytes())
    require(not any(isinstance(n, ast.Attribute) and n.attr in {'new', 'main'}
                    and isinstance(n.value, ast.Name) and n.value.id in {'full', 'Runner', 'runner'}
                    for n in ast.walk(rt)))
    assignments = [n for n in ast.walk(rt) if isinstance(n, ast.Assign)]
    require(not any(isinstance(t, ast.Attribute) and t.attr == 'send_ack_budget'
                    for n in assignments for t in n.targets))


check('caller_never_calls_product_Runner_new_or_main_and_never_overrides_ACK', full_ack_no_override_in_source)

report = {'schema': 'frw.source.F04.caller-controls.v1', 'source_only': True,
          'actual_v42_sha256': a.digest(base_raw), 'actual_issuer_sha256': a.digest(issuer_raw),
          'actual_final_current_source_ref': current_ref,
          'captured_native_source_manifest_sha256': a.digest(capture_raw),
          'captured_native_modules_imported': False,
          'production_F04_stop_ready': False,
          'production_preop_assertcode': 'F04_STOP_API_SCOPE_UNSUPPORTED',
          'bound_specimen_persisted': False, 'full_tester_or_issuer_imported': False,
          'all_lifecycle_current_process_effect_leaves_inert': True,
          'workbook_state_current_native_model_Telegram_Git_reads_or_effects': False,
          'passed': sum(item['passed'] for item in RESULTS),
          'failed': sum(not item['passed'] for item in RESULTS), 'checks': RESULTS}
target = HERE / 'SOURCE-CHECKS.json'
target.write_bytes(a.encoded(report))
target.chmod(0o600)
print(json.dumps({'passed': report['passed'], 'failed': report['failed'],
                  'checks_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}, sort_keys=True))
raise SystemExit(bool(report['failed']))
