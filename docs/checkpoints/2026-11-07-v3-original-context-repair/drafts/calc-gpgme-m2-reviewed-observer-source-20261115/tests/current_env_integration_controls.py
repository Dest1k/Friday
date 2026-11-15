"""Independent inert bootstrap -> real GOT collector -> real policy controls."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch

OUT = Path(__file__).parent
sys.path.insert(0, str(OUT / 'collector-repair'))
import current_environment_tests as t

ADAPTER = OUT / 'bootstrap-repair/gpgme_engine_gdb.py'
scope = {'__file__': str(ADAPTER), '__name__': 'independent_inert_adapter'}
exec(compile(ADAPTER.read_bytes(), str(ADAPTER), 'exec'), scope)
A, P = scope['Adapter'], t.c.policy
PROFILE = dict(schema=P.SCHEMA, stage=P.STAGE,
    library=dict(path=P.LIBRARY_PATH, sha256=P.LIBRARY_SHA256, build_id=P.BUILD_ID),
    source_manifest_ref=P.SOURCE_MANIFEST, conditional_join_ref=P.CONDITIONAL_JOIN,
    branches=[dict(branch=b, role=P.ROLES[b], option=P.OPTIONS[b]) for b in P.BRANCHES],
    pseudo_protocols=list(P.UNSUPPORTED), runtime_available=False,
    budgets=dict(wall_seconds=240, cpu_seconds=120, memory_bytes=2147483648,
        deadline_rule='SAME_ORIGINAL_ABSOLUTE_OPERATION_DEADLINE_NO_RESET'))
checks = []
for wrong_font in (False, True):
    actual = dict(P.ISOLATED, UNLISTED_NONFONT_CURRENT='current-state')
    if wrong_font:
        actual['FONTCONFIG_FILE'] = '/inert/unpinned-fonts.conf'
    collector, original, child, startup, actual = t.fixture(current=actual)
    t.snapshot_fixture(collector)
    old_binding = collector.image_binding
    libbase = 0x500000
    entry = libbase + scope['SITE_OFFSETS']['engine_entry']
    events = []

    def binding(pid, image, pc):
        if image['path'] == collector.p['libc']['path']:
            return old_binding(pid, image, pc)
        return dict(relative_pc=scope['SITE_OFFSETS']['engine_entry'], load_bias=libbase)

    collector.image_binding = binding
    frame = types.SimpleNamespace(pc=lambda: entry, is_valid=lambda: True,
        architecture=lambda: types.SimpleNamespace(name=lambda: 'i386:x86-64'))
    collector.g.newest_frame = lambda: frame
    collector.g.solib_name = lambda pc: collector.p['library']['path']
    code = bytes.fromhex(scope['SITE_BYTES']['engine_entry'])
    original.memory.update({entry + i: b for i, b in enumerate(code)})
    adapter = A.__new__(A)
    adapter.p = P.__dict__
    adapter.g, adapter.collector = collector.g, collector
    adapter.m = dict(collector_pins=collector.p, profile=PROFILE, source_mode='COLD_GPGCONF',
        helpers={'gpgconf': dict(path='/inert/gpgconf', sha256='ab' * 32, dev=1, ino=11)})
    adapter.n = collector.n
    adapter.b = {'runtime': dict(operation_id=collector.p['operation']['operation_id'],
        nonce=collector.p['operation']['nonce'],
        operation_deadline_monotonic=collector.p['operation']['deadline_monotonic'])}
    adapter.original = lambda: copy.deepcopy(collector.p['original'])
    adapter.paper_closed = lambda: events.append('paper_closed')
    adapter.tid = lambda: [123, 123, 0]
    adapter.reg = lambda name: 0x800000
    adapter.memory = lambda address, count: original.read_memory(address, count)
    adapter.installed = adapter.finished_initialization = adapter.init_active = False
    adapter.c, adapter.pending = None, None
    adapter.boundary_count = 0

    def install(bound):
        events.append('numeric_install')
        adapter.installed = True

    adapter.install_bound_sites = install
    with patch.object(t.c.time, 'monotonic', return_value=1000.0):
        if wrong_font:
            try:
                adapter.bootstrap_entry()
                raise AssertionError('font mutation accepted')
            except RuntimeError as exc:
                assert str(exc) == 'gpgme_collector_font_runtime_environment_changed'
            assert 'numeric_install' not in events and adapter.c is None and not adapter.init_active
        else:
            adapter.bootstrap_entry()
            assert adapter.c.env == actual and adapter.c.env != collector.p['environment']
            assert adapter.init_active and adapter.pending == 'CONTINUE'
            assert collector.current_environment(123) == actual
            assert collector.exec_environment(124) == actual
            old_read = collector._read
            collector._read = lambda path, limit: t.encoded(dict(actual,
                ANOTHER_UNPINNED_CHILD_KEY='different')) if path == '/proc/124/environ' else old_read(path, limit)
            try:
                collector.exec_environment(124)
                raise AssertionError('child mismatch accepted')
            except RuntimeError as exc:
                assert str(exc) == 'gpgme_exact_current_environment_changed'
    checks.append(dict(name='real_bootstrap_real_GOT_real_policy_' +
        ('font_negative' if wrong_font else 'nonfont_current_positive_and_childdiff_negative'),
        result='PASS', events=events))

original_path = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-COMPLETE-OBSERVER-SOURCE-20261115/candidate/outer/deps/gpgme_boundary_collector.py')
old = ast.parse(original_path.read_bytes())
new = ast.parse((OUT / 'collector-repair/gpgme_boundary_collector.py').read_bytes())

def method(tree, name):
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'BoundaryCollector')
    return next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == name)

before = copy.deepcopy(method(old, 'current_environment'))
after = copy.deepcopy(method(new, '_effective_environment'))
before.name = after.name = 'same'
before.body, after.body = before.body[1:], after.body[1:]
before.body = [n for n in before.body if not (isinstance(n, ast.Expr) and
    'policy.validate_environment(result' in ast.unparse(n))]
assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False)
checks.append(dict(name='effective_GOT_bounded_double_capture_exact_AST_preserved', result='PASS'))

old_adapter = ast.parse((OUT / 'adapter/repair-copy/gpgme_engine_gdb.py').read_bytes())
new_adapter = ast.parse(ADAPTER.read_bytes())
for tree in (old_adapter, new_adapter):
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Adapter')
    owner.body = [n for n in owner.body if not (isinstance(n, ast.FunctionDef) and n.name == 'bootstrap_entry')]
assert ast.dump(old_adapter, include_attributes=False) == ast.dump(new_adapter, include_attributes=False)
checks.append(dict(name='adapter_only_bootstrap_delta_beyond_accepted_clone_fix', result='PASS'))

report = dict(schema='frw.calc.gpgme-m2-currentenv-independent-integration.v1',
    at_moscow=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
    collector_sha256=hashlib.sha256((OUT / 'collector-repair/gpgme_boundary_collector.py').read_bytes()).hexdigest(),
    adapter_sha256=hashlib.sha256(ADAPTER.read_bytes()).hexdigest(), checks=checks,
    checker_correction='Initial inert fixture lacked adapter.p; fixed fixture only, no source or actor repeated.',
    status='PASS_INERT_REAL_SOURCE_CONSUMER_CONTROLS',
    real_GDB_Office_helpers_ELF_inferiors_namespaces_executed=False,
    synthetic_GDB_and_proc_inputs=True)
target = OUT / 'CURRENT-ENV-INDEPENDENT-INTEGRATION.json'
target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
target.chmod(0o600)
print(json.dumps(dict(checks=len(checks), report=str(target),
    sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
