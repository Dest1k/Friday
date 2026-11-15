"""Actual unchanged metadata consumers only; no actor/runtime entry points."""
import ast
import copy
import hashlib
import json
import os
import stat
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parent
PACKAGE = ROOT.parent
CONTROLLER = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115/host/ownc_root_controller.py')
EXPECTED_CONTROLLER = '98c0105bfeae6eeb852ccfae958acf1a95e39de24b1147f6edb118ad6fc0d0ae'
ADAPTER = {'path': str(PACKAGE / 'candidate/outer/deps/gpgme_engine_gdb.py'), 'sha256': '173e03a9ca2165985f8b03a557fee6a36a2c3e7bb21fb92e22f37b35dc63e353'}

def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty', 'os.exec', 'os.posix_spawn', 'os.kill', 'os.killpg', 'socket.__new__', 'socket.connect'}:
        raise RuntimeError('review_forbidden_effect:' + event)
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = os.fsdecode(args[0])
        if path == '/proc' or path.startswith('/proc/') or path == '/sys' or path.startswith('/sys/'):
            raise RuntimeError('review_forbidden_live_read')
        mode, flags = args[1], args[2]
        writes = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writes and not Path(path).absolute().is_relative_to(ROOT):
            raise RuntimeError('review_forbidden_write')
sys.addaudithook(audit)

raw = CONTROLLER.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED_CONTROLLER
# Extract unchanged real functions and their globals, excluding all actor leaves.
tree = ast.parse(raw, str(CONTROLLER))
names = {'need', 'stamp', 'read_ref', 'load_module', 'verify_image_ref', 'json_load', 'validate_budget', 'inspect_plan', 'build_bundles'}
nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign)) or isinstance(n, ast.FunctionDef) and n.name in names]
controller = types.ModuleType('frw_independent_exact_metadata_consumers')
controller.__file__ = str(CONTROLLER)
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(CONTROLLER), 'exec'), controller.__dict__)

def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def read_ref(refvalue):
    path = Path(refvalue['path'])
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == refvalue['sha256'], str(path)
    return data

def refuses(fn, code):
    try:
        fn()
    except Exception as e:
        assert str(e) == code, (str(e), code)
    else:
        raise AssertionError('Expected refusal ' + code)

selected_path = PACKAGE / 'inputs/SELECTED-INPUTS.json'
composition_path = PACKAGE / 'SOURCE-COMPOSITION.json'
current_path = PACKAGE / 'CURRENT-REFERENCE-CHECK.json'
selected = json.loads(selected_path.read_bytes())
composition = json.loads(read_ref(selected['reviewed_composition']))
current = json.loads(current_path.read_bytes())
assert selected['reviewed_composition'] == ref(composition_path)
assert set(selected['variants']) == {'worker_cached', 'extra_fork', 'forbidden_gpg_home', 'wrong_gpgconf_name'}
assert selected['future_execution'] is False and selected['actual_M'] is None
assert composition['runtime_admitted'] is False and composition['installed224_changed'] is False
changed = [v for v in composition['files'] if v.get('changed_by_bootstrap_entry_successor')]
assert len(changed) == 1 and changed[0]['relative_path'] == 'outer/deps/gpgme_engine_gdb.py'
assert {k: changed[0]['selected'][k] for k in ADAPTER} == ADAPTER
verified = []
for value in current['refs']:
    path = Path(value['path'])
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert len(data) == value['bytes'] and hashlib.sha256(data).hexdigest() == value['sha256']
    verified.append({k: value[k] for k in ('path', 'sha256')})
assert len(verified) == current['current_unique_count'] == 47

results = []
negatives = []
for name, bindings in selected['variants'].items():
    plan = json.loads(read_ref(bindings['plan_ref']))
    prepared = controller.inspect_plan(plan)
    assert plan['prepared_ref'] == bindings['prepared_ref']
    assert prepared == json.loads(read_ref(bindings['prepared_ref']))
    assert prepared['reviewed_composition'] == selected['reviewed_composition']
    assert prepared['gpgme_binding']['adapter'] == plan['observer']['gpgme_engine_init']['adapter'] == ADAPTER
    assert prepared['target_environment'] == plan['target_environment'] == selected['full_target_startup_environment']
    assert plan['budgets'] == {'cleanup_seconds': 10, 'cpu_seconds': 120, 'memory_bytes': 2147483648, 'startup_seconds': 60, 'tasks_max': 64, 'wall_seconds': 240}
    assert prepared['gpgme_runtime_template']['operation_deadline_monotonic'] is None
    assert prepared['runtime_template']['operation_deadline_monotonic'] is None
    namespace = controller.load_module(plan['source_refs']['namespace'], 'frw_independent_exact_namespace_' + name)
    paper, gpgme = controller.build_bundles(plan, prepared, namespace, operation_id='independent-source-only', nonce='1' * 32, deadline=1.0, validation_only=True)
    assert gpgme['adapter_ref'] == ADAPTER
    assert gpgme['runtime']['operation_deadline_monotonic'] == paper['runtime']['operation_deadline_monotonic'] == 1.0
    bad = copy.deepcopy(plan)
    bad['observer']['gpgme_engine_init']['adapter']['sha256'] = '0' * 64
    refuses(lambda: controller.inspect_plan(bad), 'ownc_helper_binding_join')
    negatives.append(name + ':actual_plan_prepared_adapter_join_refuses_changed_hash')
    bad = copy.deepcopy(prepared['gpgme_binding'])
    bad['adapter']['sha256'] = '0' * 64
    refuses(lambda: namespace.gpgme_sources(bad), 'pinned_source_changed')
    negatives.append(name + ':actual_namespace_consumer_refuses_adapter_hash_mismatch')
    results.append({'variant': name, 'plan_ref': bindings['plan_ref'], 'prepared_ref': bindings['prepared_ref'], 'adapter_ref': ADAPTER, 'inspect_plan': 'PASS', 'build_bundles': 'PASS', 'namespace_validator_collector_mapper_policy': 'PASS', 'unbound_original_templates_preserved': True})

output = {'schema': 'frw.gpgme-bootstrap-independent-metadata.v1', 'scope': 'SOURCE_ONLY_NO_ACTOR_NO_RUNTIME_CREDIT',
    'controller_ref': ref(CONTROLLER), 'selected_ref': ref(selected_path), 'composition_ref': ref(composition_path),
    'current_reference_ref': ref(current_path), 'all47_current_references_independently_verified': True,
    'actual4_consumer_joins': results, 'meaningful_negative_controls': negatives,
    'script_effect_audit': 'FORBIDS_PROCESS_NETWORK_LIVE_PROC_SYS_READS_AND_EXTERNAL_WRITES', 'findings': []}
path = ROOT / 'INDEPENDENT-METADATA.json'
path.write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
path.chmod(0o600)
print(json.dumps({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'variants': len(results), 'negative_controls': len(negatives)}, sort_keys=True))
