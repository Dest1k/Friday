"""Source unit controls for P; no installed/native authority or readiness claim.

The changed source is loaded from this checkout, with isolated import adapters
for Budget, process IO and installer file primitives. These adapters never
start a process or claim native admission. Sparse review candidates can supply
unchanged dependencies through FRIDAY_DSH_OBSERVER_DEPENDENCY_ROOT; a complete
checkout needs no environment override. Fixtures contain synthetic paths only.
"""
import ast
import contextlib
import argparse
import copy
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = Path(os.environ.get('FRIDAY_DSH_OBSERVER_DEPENDENCY_ROOT', ROOT))
ALIAS = '_dsh_observer_unit_source'
REFUSED = (ValueError, RuntimeError, OSError)
APPLY = 'friday.dsh-current-availability.apply.v1'
OBSERVE = 'friday.dsh-current-observation.apply.v1'
FIELDS = 'Id,LoadState,ActiveState,SubState,ControlGroup'
UNIT = 'friday-qualify-dsh-' + 'a' * 24 + '-1.scope'
SECOND_UNIT = 'friday-qualify-dsh-' + 'b' * 24 + '-1.scope'


def reference(name='input', digit='1'):
    return {'path': '/offline/' + name, 'sha256': digit * 64}


def request():
    return {'schema': OBSERVE, 'seconds': 180, 'home': '/offline/H', 'profile': 'tester',
        **{name: reference(name) for name in ('current_input', 'native_unit', 'clock', 'pending_transaction')},
        'native_pm': {name: reference(name) for name in ('runtime_facts', 'tool_facts', 'pyvenv_cfg', 'node')}}


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n'); path.chmod(0o600)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.fixture(scope='module')
def source():
    """Temporary import namespace; restore every replaced module after tests."""
    prefixes = (ALIAS, 'scripts')
    saved = {key: value for key, value in sys.modules.items()
        if any(key == prefix or key.startswith(prefix + '.') for prefix in prefixes)}
    for key in saved:
        del sys.modules[key]

    class NoNativeImports(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'hermes_cli', 'gateway', 'pm', 'agent', 'tools',
                    'hermes_constants', 'hermes_state_holders'}:
                raise AssertionError('native import outside source unit boundary: ' + fullname)

    guard = NoNativeImports()
    sys.meta_path.insert(0, guard)
    bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        package = ModuleType(ALIAS)
        package.__path__ = list(dict.fromkeys(str(root / 'plugins/friday_rework')
            for root in (ROOT, DEPENDENCIES)))
        package.__spec__ = importlib.machinery.ModuleSpec(ALIAS, loader=None, is_package=True)
        sys.modules[ALIAS] = package
        load = lambda name: importlib.import_module(ALIAS + '.' + name)
        st, cur = load('stopped_operator'), load('dsh_current_availability')
        containment, process, primitives = (load(name) for name in
            ('runtime_containment', 'runtime_process', 'runtime_primitives'))
        scripts = ModuleType('scripts'); scripts.__path__ = []
        sys.modules['scripts'] = scripts
        # Explicit source export adapters: no installer/native bootstrap runs.
        for name, exports in {
                'install_containment': {'Budget': containment.Budget},
                'dsh_prepare': {'run': process.run, 'StopUnconfirmed': process.StopUnconfirmed},
                'friday_install': {'require': primitives.require, 'owned_file': primitives.owned_file},
                }.items():
            module = ModuleType('scripts.' + name); module.__dict__.update(exports)
            sys.modules[module.__name__] = module; setattr(scripts, name, module)
        spec = importlib.util.spec_from_file_location('scripts.friday_ordinary_install',
            ROOT / 'scripts/friday_ordinary_install.py')
        ordinary = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = ordinary; scripts.friday_ordinary_install = ordinary
        spec.loader.exec_module(ordinary)
        yield SimpleNamespace(st=st, cur=cur, Budget=containment.Budget, ordinary=ordinary,
            prepare=sys.modules['scripts.dsh_prepare'], process=process)
    finally:
        sys.dont_write_bytecode = bytecode
        sys.meta_path.remove(guard)
        for key in tuple(sys.modules):
            if any(key == prefix or key.startswith(prefix + '.') for prefix in prefixes):
                del sys.modules[key]
        sys.modules.update(saved)


@pytest.mark.parametrize('seconds', [30, 90, 180])
def test_request_is_pure_and_typed(source, seconds):
    value = request(); value['seconds'] = seconds
    assert source.st.validate_observation_request(value) is value
    assert 'ready' not in value


@pytest.mark.parametrize('key,value', [('seconds', True), ('seconds', 180.0), ('seconds', 29),
    ('seconds', 181), ('schema', APPLY), ('profile', 'default'), ('profile', 'a/b'),
    ('home', '/offline/../H'), ('home', '/'), ('current_input', reference('../x')),
    ('pending_transaction', {'path': 'relative', 'sha256': '1' * 64}), ('native_pm', {})])
def test_request_rejects_invalid_types_bounds_and_paths(source, key, value):
    value_request = request(); value_request[key] = value
    with pytest.raises(REFUSED): source.st.validate_observation_request(value_request)


@pytest.mark.parametrize('extra', ['previous_input', 'verify', 'ready'])
def test_request_does_not_accept_caller_authority_or_declaration_fields(source, extra):
    value = request(); value[extra] = reference()
    with pytest.raises(ValueError, match='exact_observer_request'):
        source.st.CurrentObservationOperator(value, source.Budget(180)).preflight()


def test_operation_key_binds_causal_edge_and_boot_without_new_clock(source, tmp_path):
    args = [tmp_path, reference('T1/committed.json'), reference('D'), reference('cycle'), 'unit-boot']
    original = source.st.observation_transaction(*args)
    assert original.parent == tmp_path / 'preparation'
    for index in range(1, 5):
        changed = copy.deepcopy(args)
        changed[index] = reference('different', '2') if index < 4 else 'other-boot'
        assert source.st.observation_transaction(*changed) != original
    assert source.st.observation_transaction(*copy.deepcopy(args)) == original


def clock(source, root, delta=0, seconds=180):
    now = time.monotonic() + delta
    value = {'schema': 'friday.dsh-current-observation.clock.v1',
        'boot_id': source.cur.identity()['boot_id'], 'started_mono': now,
        'deadline_mono': now + seconds, 'seconds': seconds, 'stage_folder': str(root / 'stage')}
    return value, save(root / 'clock.json', value)


def test_original_clock_deadline_and_cleanup_reserve(source, tmp_path):
    value, ref = clock(source, tmp_path)
    r = request(); r['clock'] = ref
    op = source.st.CurrentObservationOperator(r, source.Budget(180,
        started=value['started_mono'], deadline=value['deadline_mono']))
    assert op._clock() == op._clock(cleanup=True) == value
    assert op.budget.deadline == value['deadline_mono']
    op.budget.deadline -= 1
    with pytest.raises(ValueError, match='original_clock'): op._clock()


def test_cleanup_reserve_does_not_extend_original_clock(source, tmp_path):
    value, ref = clock(source, tmp_path, delta=-151)
    r = request(); r['clock'] = ref
    op = source.st.CurrentObservationOperator(r, source.Budget(180,
        started=value['started_mono'], deadline=value['deadline_mono']))
    with pytest.raises(RuntimeError, match='original_clock_expired'): op._clock()
    assert op._clock(cleanup=True) == value


def test_expired_clock_rejected_before_callback_or_folder(source, tmp_path, monkeypatch):
    _, ref = clock(source, tmp_path, delta=-200)
    monkeypatch.setattr(source.cur, 'validate_current', lambda *a, **k: pytest.fail('validation after expiry'))
    with pytest.raises(RuntimeError, match='original_clock_expired'):
        source.cur.observe_current({}, clock_reference=ref, pending_transaction=reference(),
            folder=tmp_path / 'never', verify=lambda: pytest.fail('callback after expiry'))
    assert not (tmp_path / 'never').exists()


def test_missing_native_verifier_refused_before_clock_io(source, tmp_path):
    with pytest.raises(RuntimeError, match='native_operator_required'):
        source.cur.observe_current({}, clock_reference=reference('absent'),
            pending_transaction=reference(), folder=tmp_path / 'never', verify=None)
    assert not (tmp_path / 'never').exists()


def test_callback_denial_stops_before_observation_files(source, tmp_path):
    value, ref = clock(source, tmp_path)
    now = value['started_mono'] - 1
    cycle = save(tmp_path / 'cycle.json', {'schema': 'friday.worker-declarations.clock.v1',
        'boot_id': source.cur.identity()['boot_id'], 'started_mono': now,
        'deadline_mono': now + 180, 'seconds': 180})
    calls = []
    def deny():
        calls.append('denial'); raise PermissionError('fixture-denial')
    with pytest.raises(PermissionError, match='fixture-denial'):
        source.cur.observe_current({'current_availability': {'cycle': cycle}}, clock_reference=ref,
            pending_transaction=reference(), folder=tmp_path / 'never', verify=deny)
    assert calls == ['denial'] and not (tmp_path / 'never').exists()


class TestCustody(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def isolated_source(self, source, tmp_path):
        self.source = source
        self.root = tmp_path
        self.root.chmod(0o700)

    def test_consume_is_own_p_journal_no_t1_reopen_and_no_retry(self):
        home = self.root / 'H'
        home.mkdir(mode=448)
        (home / 'preparation').mkdir(mode=448)
        r = request()
        r['home'] = str(home)
        op = self.source.st.CurrentObservationOperator(r, self.source.Budget(180), request_reference=reference('request'))
        op.home = home
        op.ordinary = self.source.ordinary
        op.tx = home / 'preparation/dsh-current-observation-fixture'
        op.clock = {'fixture': 'separate-P-clock'}
        op.scope_units = ('friday-qualify-dsh-' + '0' * 24 + '-1.scope',)
        op.t1_committed = {'after': {'config.yaml': 'a' * 64}}
        t1 = home / 'preparation/original-T1'
        t1.mkdir(mode=448)
        original = save(t1 / 'completed.json', {'old_effect': 'COMMITTED_RELEASED'})
        with patch.object(op, 'before_unchanged'), patch.object(op, '_pending'):
            op.consume()
            with self.assertRaisesRegex(ValueError, 'preflight_before_consume'):
                op.consume()
        intent = json.loads((op.tx / 'intent.json').read_bytes())
        self.assertEqual(intent['schema'], self.source.st.OBSERVATION_APPLY_SCHEMA)
        self.assertEqual(intent['clock'], {'fixture': 'separate-P-clock'})
        self.assertEqual(intent['pending_transaction'], r['pending_transaction'])
        self.assertFalse(intent['retry_authorized'])
        self.assertEqual(hashlib.sha256((t1 / 'completed.json').read_bytes()).hexdigest(), original['sha256'])
        op._consumption()
        (op.tx / 'intent.json').unlink()
        save(op.tx / 'intent.json', intent)
        with self.assertRaisesRegex(ValueError, 'consumption_custody_changed'):
            op._consumption()

    def test_replaced_transaction_refused_before_intent_write(self):
        home = self.root / 'H'
        home.mkdir(mode=448)
        (home / 'preparation').mkdir(mode=448)
        op = self.source.st.CurrentObservationOperator(request(), self.source.Budget(180))
        op.home = home
        op.ordinary = self.source.ordinary
        op.tx = home / 'preparation/owned'
        op.tx.mkdir(mode=448)
        info = op.tx.lstat()
        op._tx_identity = (info.st_dev, info.st_ino, info.st_uid, info.st_mode)
        op.tx.rename(home / 'preparation/saved-owned')
        op.tx.mkdir(mode=448)
        with self.assertRaisesRegex(ValueError, 'transaction_identity_changed'):
            op._operation_journal('intent.json', b'fixture')
        self.assertEqual(list(op.tx.iterdir()), [])
        self.assertEqual(list((home / 'preparation/saved-owned').iterdir()), [])

    def test_postopen_rename_writes_only_retained_owned_dir_then_refuses(self):
        home = self.root / 'H'
        home.mkdir(mode=448)
        (home / 'preparation').mkdir(mode=448)
        op = self.source.st.CurrentObservationOperator(request(), self.source.Budget(180))
        op.home = home
        op.ordinary = self.source.ordinary
        op.tx = home / 'preparation/owned'
        op.tx.mkdir(mode=448)
        info = op.tx.lstat()
        op._tx_identity = (info.st_dev, info.st_ino, info.st_uid, info.st_mode)
        original_open = os.open
        injected = []

        def replace_after_open(path, *args, **kwargs):
            fd = original_open(path, *args, **kwargs)
            if path == op.tx and (not injected):
                injected.append(True)
                op.tx.rename(home / 'preparation/saved-owned')
                op.tx.mkdir(mode=448)
            return fd
        with patch.object(self.source.st.os, 'open', replace_after_open), self.assertRaisesRegex(ValueError, 'transaction_identity_changed'):
            op._operation_journal('intent.json', b'fixture')
        self.assertTrue(injected)
        self.assertEqual(list(op.tx.iterdir()), [])
        self.assertEqual((home / 'preparation/saved-owned/intent.json').read_bytes(), b'fixture')

    def test_existing_consumption_refuses_without_altering_it(self):
        home = self.root / 'H'
        home.mkdir(mode=448)
        (home / 'preparation').mkdir(mode=448)
        op = self.source.st.CurrentObservationOperator(request(), self.source.Budget(180))
        op.home = home
        op.tx = home / 'preparation/consumed'
        op.tx.mkdir(mode=448)
        old = save(op.tx / 'original.json', {'never': 'replay'})
        with patch.object(op, 'before_unchanged'), patch.object(op, '_pending'):
            with self.assertRaisesRegex(ValueError, 'consumed_no_retry'):
                op.consume()
        self.assertEqual(hashlib.sha256((op.tx / 'original.json').read_bytes()).hexdigest(), old['sha256'])
        self.assertFalse((op.tx / 'intent.json').exists())

    def test_exact_entry_grammar_only_with_explicit_base_authority_fixture_seam(self):
        op = self.source.st.CurrentObservationOperator(request(), self.source.Budget(180), request_reference=reference('request'))
        canonical = ['genuine-script-path', 'observe-dsh-current', '--request', '/offline/request', '--request-sha256', '1' * 64]
        with patch.object(self.source.st.StoppedOperator, '_context') as base, patch.object(sys, 'argv', canonical):
            self.assertIsNone(op._context())
            base.assert_called_once_with()
            self.assertEqual(sys.argv, canonical)
        variants = [canonical[:1] + ['rebind-worker-declarations'] + canonical[2:], canonical + ['extra'], canonical[:3] + ['/wrong'] + canonical[4:], canonical[:-1] + ['2' * 64]]
        for argv in variants:
            with patch.object(self.source.st.StoppedOperator, '_context'), patch.object(sys, 'argv', argv), self.assertRaisesRegex(ValueError, 'exact_native_entry'):
                op._context()


def raw_scope(**changes):
    fields = {'Id': UNIT, 'LoadState': 'loaded', 'ActiveState': 'inactive',
        'SubState': 'dead', 'ControlGroup': ''}
    fields.update(changes)
    return ''.join(name + '=' + value + '\n' for name, value in fields.items())


SCOPE_CASES = [
    ('absent-five-fields', raw_scope(LoadState='not-found'), False, True),
    ('loaded-dead', raw_scope(), False, True),
    ('retained-empty', raw_scope(ControlGroup='/unit-test/' + UNIT), False, True),
    ('failed-empty', raw_scope(ActiveState='failed', SubState='failed', ControlGroup='/unit-test/' + UNIT), False, True),
    ('active', raw_scope(ActiveState='active', SubState='running'), False, False),
    ('activating', raw_scope(ActiveState='activating', SubState='start'), False, False),
    ('foreign-id', raw_scope(Id='foreign.scope'), False, False),
    ('foreign-group', raw_scope(ControlGroup='/unit-test/foreign.scope'), False, False),
    ('group-child', raw_scope(ControlGroup='/unit-test/' + UNIT + '/child'), False, False),
    ('unknown-load', raw_scope(LoadState='error'), False, False),
    ('inactive-running', raw_scope(SubState='running'), False, False),
    ('failed-dead', raw_scope(ActiveState='failed'), False, False),
    ('absent-nonempty-group', raw_scope(LoadState='not-found', ControlGroup='/unit-test/' + UNIT), False, False),
    ('absent-failed', raw_scope(LoadState='not-found', ActiveState='failed', SubState='failed'), False, False),
    ('populated', raw_scope(ControlGroup='/unit-test/' + UNIT), True, False),
    ('population-unknown', raw_scope(ControlGroup='/unit-test/' + UNIT), None, False),
    ('missing-field', raw_scope().replace('ControlGroup=\n', ''), False, False),
    ('extra-field', raw_scope() + 'Unexpected=0\n', False, False),
    ('invented-pid-fields', raw_scope() + 'MainPID=0\nControlPID=0\n', False, False),
    ('duplicate-field', raw_scope() + 'ControlGroup=\n', False, False),
    ('duplicate-replaces-field', raw_scope().replace('ControlGroup=\n', 'SubState=dead\n'), False, False),
    ('malformed-extra', raw_scope() + 'malformed\n', False, False),
    ('malformed-replaces-field', raw_scope().replace('ControlGroup=\n', 'ControlGroup\n'), False, False),
    ('empty', '', False, False),
]


def scope_adapter(source, monkeypatch, tmp_path, raw, populated=False, units=(UNIT,)):
    calls, groups = [], []
    op = source.st.CurrentObservationOperator({}, source.Budget(180))
    op.home = tmp_path; op.scope_units = units
    op.f = SimpleNamespace(ROOT=tmp_path, clean_environment=lambda home: {'SOURCE_UNIT': '1'})
    def run(argv, root, **kwargs):
        calls.append((argv, root, kwargs))
        if isinstance(raw, BaseException): raise raw
        return (raw[argv[-2]] if isinstance(raw, dict) else raw), {}
    def population(group):
        groups.append(group)
        if populated is None: raise RuntimeError('fixture-unknown-cgroup')
        return populated
    module = ModuleType(ALIAS + '.supervision')
    module.NativeSupervisor = lambda: SimpleNamespace(_populated=population)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(source.prepare, 'run', run)
    monkeypatch.setattr(op, '_profile', lambda **kw: pytest.fail('admission must not gate cleanup'))
    return op, calls, groups


@pytest.mark.parametrize('label,raw,populated,accepted', SCOPE_CASES, ids=[row[0] for row in SCOPE_CASES])
def test_exact_five_field_scope_contract(source, tmp_path, monkeypatch, label, raw, populated, accepted):
    op, calls, groups = scope_adapter(source, monkeypatch, tmp_path, raw, populated)
    if accepted:
        result = op.scopes_released()
        assert len(result) == 1 and set(result[0]) == set(FIELDS.split(','))
        assert 'MainPID' not in result[0] and 'ControlPID' not in result[0]
        assert groups == [result[0]['ControlGroup']]
    else:
        with pytest.raises(REFUSED): op.scopes_released()
    assert calls[0][0][-1] == '--property=' + FIELDS
    assert calls[0][2]['deadline'] == op.budget.deadline
    assert 0 < calls[0][2]['timeout'] <= 5


def test_every_expected_scope_is_checked(source, tmp_path, monkeypatch):
    raw = {UNIT: raw_scope(), SECOND_UNIT: raw_scope(Id=SECOND_UNIT)}
    op, calls, groups = scope_adapter(source, monkeypatch, tmp_path, raw, units=(UNIT, SECOND_UNIT))
    assert [value['Id'] for value in op.scopes_released()] == [UNIT, SECOND_UNIT]
    assert len(calls) == 2 and groups == ['', '']


def test_scope_io_failure_is_not_absence(source, tmp_path, monkeypatch):
    error = RuntimeError('fixture-systemctl-refusal')
    op, _, groups = scope_adapter(source, monkeypatch, tmp_path, error)
    with pytest.raises(RuntimeError) as caught: op.scopes_released()
    assert caught.value is error and groups == []


def test_original_seven_field_assumption_rejects_valid_five_field_scope(source, tmp_path, monkeypatch):
    """Mutation control preserves the original consumer defect without old archives."""
    tree = ast.parse((ROOT / 'plugins/friday_rework/stopped_operator.py').read_text())
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CurrentObservationOperator')
    method = copy.deepcopy(next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'scopes_released'))
    class SevenFields(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == FIELDS:
                return ast.copy_location(ast.Constant('Id,LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup'), node)
            if type(node.value) is int and node.value == 5:
                return ast.copy_location(ast.Constant(7), node)
            return node
    method = SevenFields().visit(method)
    namespace = dict(source.st.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
        str(ROOT / 'plugins/friday_rework/stopped_operator.py'), 'exec'), namespace)
    op, _, _ = scope_adapter(source, monkeypatch, tmp_path, raw_scope(LoadState='not-found'))
    with pytest.raises(ValueError, match='raw_scope_cessation_unconfirmed'):
        namespace['scopes_released'](op)


# Entry routing is AST-extracted from this checkout, before native bootstrap.
SOURCE = Path(os.environ.get("FRIDAY_DSH_OBSERVER_ENTRY_SOURCE", ROOT / "scripts/friday_ordinary_install.py"))
TREE = ast.parse(SOURCE.read_text())

class Refusal(ValueError):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason

class BeforeNative(Exception):
    pass

class StopUnconfirmed(RuntimeError):
    pass

class InstallerExit(SystemExit):

    def __init__(self, code, original):
        super().__init__(code)
        self.friday_custody_primary = original
        self.friday_custody_state = 'UNCONFIRMED' if code == 3 else 'REFUSAL_UNPROVEN'

def require(value, reason):
    if not value:
        raise Refusal(reason)

def same(left, right):
    return left == right

class TestEntry(unittest.TestCase):

    def setUp(self):
        self.saved = {}
        chain = ('_friday_install_validation_plugins', '_friday_install_validation_plugins.friday_rework', '_friday_install_validation_plugins.friday_rework.worker_declarations', 'scripts', 'scripts.dsh_prepare')
        for name in chain:
            self.saved[name] = sys.modules.get(name)
            module = types.ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
        self.pure = sys.modules[chain[2]]
        self.pure.DSH_CURRENT_APPLY_SCHEMA = APPLY
        self.pure.require = require
        self.pure._same = same
        self.pure._read_reference = self.read_reference
        sys.modules['scripts.dsh_prepare'].StopUnconfirmed = StopUnconfirmed
        sys.modules['scripts.dsh_prepare'].CommandFailed = type('CommandFailed', (RuntimeError,), {})
        sys.modules['scripts.dsh_prepare'].safe_observation = lambda observation: observation
        nodes = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in {'_dispatch_dsh_current_native', 'apply_dsh_current_declarations', 'observe_dsh_current', '_dsh_current_observation_failure_diagnostic', 'dsh_current_observation_cli', 'recovery_main'}]
        self.ns = {'Path': Path, 'json': json, 'os': os, 'api': self.before_native, '__name__': 'offline_extracted_entry', '__file__': str(SOURCE)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), self.ns)
        self.references = {}
        self.reads = []
        self.write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True

    def tearDown(self):
        sys.dont_write_bytecode = self.write_bytecode
        for name, original in self.saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    def before_native(self):
        raise BeforeNative('fixture_boundary_before_native_or_filesystem')

    def read_reference(self, ref):
        self.reads.append(ref)
        return self.references[ref['path']]

    def request(self, schema=OBSERVE):
        result = {'schema': schema, 'seconds': 90, 'home': '/offline/home', 'profile': 'offline', 'current_input': {'path': '/offline/current', 'sha256': '1' * 64}, 'native_unit': 'offline.service', 'native_pm': {}, 'clock': {}, 'pending_transaction': {}}
        if schema == APPLY:
            result['previous_input'] = dict(result['current_input'])
        self.references['/offline/request'] = result
        self.references['/offline/current'] = {'home': '/offline/home'}
        return result

    def dispatch(self, request, operation):
        return self.ns['_dispatch_dsh_current_native'](request, request_path='/offline/request', request_sha256='2' * 64, operation=operation)

    def test_observation_reaches_only_pre_native_boundary_without_previous_input(self):
        request = self.request()
        with self.assertRaises(BeforeNative):
            self.dispatch(request, 'observation')
        self.assertEqual([ref['path'] for ref in self.reads], ['/offline/request', '/offline/current'])

    def test_apply_retains_previous_input_equality(self):
        request = self.request(APPLY)
        request['previous_input'] = {'path': '/offline/other', 'sha256': '3' * 64}
        with self.assertRaisesRegex(Refusal, 'installation_input_must_remain_unchanged'):
            self.dispatch(request, 'declaration')
        self.assertEqual(len(self.reads), 1)

    def test_observation_denies_legacy_or_extra_field(self):
        request = self.request()
        request['previous_input'] = request['current_input']
        with self.assertRaisesRegex(Refusal, 'exact_observation_request_required'):
            self.dispatch(request, 'observation')
        self.assertEqual(self.reads, [])

    def test_declaration_schema_cannot_enter_observation(self):
        with self.assertRaisesRegex(Refusal, 'exact_observation_schema_required'):
            self.dispatch(self.request(APPLY), 'observation')
        self.assertEqual(self.reads, [])

    def test_observation_schema_cannot_enter_declaration(self):
        with self.assertRaisesRegex(Refusal, 'exact_apply_schema_required'):
            self.dispatch(self.request(), 'declaration')
        self.assertEqual(self.reads, [])

    def test_bytecode_mode_denied_before_reference_io(self):
        request = self.request()
        sys.dont_write_bytecode = False
        with self.assertRaisesRegex(Refusal, 'native_no_bytecode_required'):
            self.dispatch(request, 'observation')
        self.assertEqual(self.reads, [])

    def terminal_api(self):
        # Actual source helper bodies, extracted before their import/bootstrap.
        path = DEPENDENCIES / 'scripts/friday_install.py'
        names = {'InstallerExit', 'remember_secondary', 'retained_diagnostic', 'safe_diagnostic'}
        nodes = [node for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        assert len(nodes) == len(names)
        namespace = {'Refused': Refusal}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
        return SimpleNamespace(**{name: namespace[name] for name in names}, Refused=Refusal)

    def terminal(self, returned=None, error=None):

        def offline_observer(request, **kwargs):
            if error is not None:
                raise error
            return returned

        def offline_api():
            return self.terminal_api()
        self.ns['observe_dsh_current'] = offline_observer
        self.ns['api'] = offline_api
        output = io.StringIO(); diagnostic = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic), self.assertRaises(SystemExit) as result:
            self.ns['dsh_current_observation_cli']({}, request_path='/private/redacted', request_sha256='4' * 64)
        self.last_diagnostic = json.loads(diagnostic.getvalue()) if diagnostic.getvalue() else None
        return (result.exception, json.loads(output.getvalue()))

    def test_terminal_success_redacts_private_result(self):
        result = {'state': 'DSH_CURRENT_OBSERVATION_COMPLETE', 'ready': False, 'effects': 'OBSERVATION_ONLY', 'per_job_authority': 'NOT_GRANTED', 'proof': {'path': '/private/do-not-print', 'sha256': '5' * 64}}
        exit_status, output = self.terminal(returned=result)
        self.assertEqual(exit_status.code, 0)
        self.assertEqual(set(output), {'state', 'ready', 'effects', 'per_job_authority'})
        self.assertNotIn('private', json.dumps(output))

    def test_terminal_retains_typed_unknown_cause(self):
        original = StopUnconfirmed('/private/do-not-print')
        exit_status, output = self.terminal(error=original)
        self.assertEqual(exit_status.code, 3)
        self.assertIs(exit_status.friday_custody_primary, original)
        self.assertEqual(output['state'], 'STOP_UNCONFIRMED')
        self.assertNotIn('private', json.dumps(output))

    def test_terminal_refusal_retains_original_cause(self):
        original = Refusal('/private/do-not-print')
        exit_status, output = self.terminal(error=original)
        self.assertEqual(exit_status.code, 2)
        self.assertIs(exit_status.friday_custody_primary, original)
        self.assertEqual(output['state'], 'FAILED_CLOSED_RECONCILE_EXACT_JOURNAL')

    def test_terminal_unexpected_result_is_unknown(self):
        exit_status, output = self.terminal(returned={'state': 'wrong'})
        self.assertEqual(exit_status.code, 3)
        self.assertIsInstance(exit_status.friday_custody_primary, StopUnconfirmed)
        self.assertEqual(output['state'], 'STOP_UNCONFIRMED')


@pytest.mark.parametrize('fault', [None, 'observe', 'prove', 'release', 'raw',
    'before', 'proof-clock', 'proof-pending', 'consumption', 'completion'])
def test_native_caller_only_completes_after_release_scope_and_durable_journal(
        source, tmp_path, monkeypatch, fault):
    """Real orchestration body, explicit fake authority and IO; no native proof."""
    st, cur = source.st, source.cur
    writer = importlib.import_module(ALIAS + '.worker_declaration_writer')
    r = request(); events = []; original = RuntimeError('unit-boundary-' + str(fault))
    now = time.monotonic()
    c = {'seconds': 180, 'started_mono': now, 'deadline_mono': now + 180}
    proof = reference('proof', '2')
    def event(name):
        events.append(name)
        if fault == name: raise original
    class Authority:
        def __init__(self, *a, **kw):
            self.runtime = {}; self.folder = tmp_path / 'observation'
        def preflight(self): event('preflight')
        def consume(self): event('consume')
        def __enter__(self): event('enter'); return self
        def __exit__(self, *args): event('exit')
        def prove(self): event('prove')
        def prove_released(self): event('release')
        def scopes_released(self): event('raw'); return [{'Id': UNIT}]
        def before_unchanged(self): event('before')
        def _consumption(self): event('consumption')
        def _operation_journal(self, name, data):
            assert name == 'completed.json'
            event('completion')
            value = json.loads(data)
            assert value['clock'] == r['clock'] and value['pending_transaction'] == r['pending_transaction']
    def observe(config, *, verify, **kwargs):
        event('observe'); verify(); return proof
    value = {'clock': r['clock'], 'pending_transaction': r['pending_transaction']}
    if fault == 'proof-clock': value['clock'] = reference('foreign-clock')
    if fault == 'proof-pending': value['pending_transaction'] = reference('foreign-pending')
    monkeypatch.setattr(st, 'CurrentObservationOperator', Authority)
    monkeypatch.setattr(st, '_read_reference', lambda ref: copy.deepcopy(r))
    monkeypatch.setattr(writer, '_request_snapshot', lambda ref: {'fixture': 'snapshot'})
    monkeypatch.setattr(source.ordinary, 'same_update_file', lambda *a, **k: True)
    monkeypatch.setattr(cur, 'checked_clock', lambda *a, **k: c)
    monkeypatch.setattr(cur, 'observe_current', observe)
    monkeypatch.setattr(cur, 'read_json', lambda ref: value)
    call = lambda: st.observe_current_native(r, request_path='/offline/request', request_sha256='3' * 64)
    if fault is None:
        result = call()
        assert result['state'] == 'DSH_CURRENT_OBSERVATION_COMPLETE'
        assert result['native_released'] is True and result['ready'] is False
        assert result['declaration_written'] is result['config_written'] is False
        assert events == ['preflight', 'consume', 'enter', 'observe', 'prove', 'prove',
            'exit', 'release', 'raw', 'before', 'consumption', 'completion']
    else:
        with pytest.raises(REFUSED) as caught: call()
        assert 'raw' in events
        if fault in ('raw', 'consumption', 'completion'):
            assert isinstance(caught.value, source.prepare.StopUnconfirmed)
            assert caught.value.friday_custody_primary is original
        elif fault.startswith('proof-'):
            assert 'returned_proof_changed' in str(caught.value)
        else:
            assert caught.value is original
        if fault not in ('consumption', 'completion'):
            assert 'completion' not in events
        if fault in ('observe', 'prove', 'release'):
            assert events.index('raw') > events.index(fault)


def test_raw_cleanup_preserves_primary_and_secondary_failures(source, tmp_path, monkeypatch):
    """Use the actual body with authority seams; UNKNOWN never becomes success."""
    st, cur = source.st, source.cur
    writer = importlib.import_module(ALIAS + '.worker_declaration_writer')
    primary, secondary = RuntimeError('fixture-primary'), RuntimeError('fixture-secondary')
    now = time.monotonic(); r = request()
    class Authority:
        def __init__(self, *a, **kw): self.runtime = {}; self.folder = tmp_path / 'not-created'
        def preflight(self): pass
        def consume(self): pass
        def __enter__(self): raise primary
        def __exit__(self, *a): pytest.fail('unentered context exited')
        def scopes_released(self): raise secondary
    monkeypatch.setattr(st, 'CurrentObservationOperator', Authority)
    monkeypatch.setattr(st, '_read_reference', lambda ref: r)
    monkeypatch.setattr(writer, '_request_snapshot', lambda ref: {})
    monkeypatch.setattr(source.ordinary, 'same_update_file', lambda *a: True)
    monkeypatch.setattr(cur, 'checked_clock', lambda *a, **k:
        {'seconds': 180, 'started_mono': now, 'deadline_mono': now + 180})
    with pytest.raises(source.prepare.StopUnconfirmed) as caught:
        st.observe_current_native(r, request_path='/offline/request', request_sha256='3' * 64)
    assert caught.value.friday_custody_primary is primary
    assert caught.value.friday_custody_secondary == (secondary,)
    assert not (tmp_path / 'not-created').exists()


def test_observer_context_inherits_base_and_does_not_rewrite_argv_or_origins():
    tree = ast.parse((ROOT / 'plugins/friday_rework/stopped_operator.py').read_text())
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CurrentObservationOperator')
    context = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == '_context')
    assert 'super()._context()' in ast.unparse(context)
    assignments = [n for n in ast.walk(klass) if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign))]
    assert not any(any(text in ast.unparse(n) for text in ('sys.argv', '__file__', '__spec__'))
        for n in assignments)


@pytest.fixture
def entry():
    fixture = TestEntry('test_observation_reaches_only_pre_native_boundary_without_previous_input')
    fixture.setUp()
    try:
        yield fixture
    finally:
        fixture.tearDown()


@pytest.mark.parametrize('schema', [OBSERVE, APPLY, 'unknown-schema'])
def test_actual_observation_phase_never_falls_through_to_declaration(entry, monkeypatch, schema):
    entry.request(schema)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    calls = []
    args = argparse.Namespace(phase='observe-dsh-current', request=Path('/offline/request'),
        request_sha256='2' * 64)
    parser = SimpleNamespace(add_argument=lambda *a, **k: None, parse_args=lambda: args)
    def exit_cause(parser, code, error, phase): raise error
    entry.ns['api'] = lambda: SimpleNamespace(SafeParser=lambda **kw: parser,
        require=require, exit_retaining_cause=exit_cause)
    entry.ns['dsh_current_observation_cli'] = lambda *a, **kw: calls.append('observation')
    entry.ns['dsh_current_declaration_cli'] = lambda *a, **kw: pytest.fail('declaration fallback')
    entry.ns['rebind_inference'] = lambda *a: pytest.fail('inference fallback')
    entry.ns['recover_first_contact_config'] = lambda *a: pytest.fail('legacy fallback')
    # Parser, umask and data readers are explicit source seams; no CLI launch.
    monkeypatch.setattr(os, 'umask', lambda mode: 0o077)
    if schema == OBSERVE:
        entry.ns['recovery_main']()
        assert calls == ['observation']
    else:
        with pytest.raises(Refusal, match='exact_observation_schema'):
            entry.ns['recovery_main']()
        assert calls == []


def test_fresh_operation_clock_cannot_reconsume_same_causal_edge(source, tmp_path, monkeypatch):
    home = tmp_path / 'H'; home.mkdir(mode=0o700); (home / 'preparation').mkdir(mode=0o700)
    first = request(); second = request(); second['clock'] = reference('new-P-clock', '2')
    edge = (home, first['pending_transaction'], reference('D'), reference('cycle'), 'fixture-boot')
    transaction = source.st.observation_transaction(*edge)
    def operator(r):
        op = source.st.CurrentObservationOperator(r, source.Budget(180))
        op.home = home; op.ordinary = source.ordinary; op.tx = source.st.observation_transaction(*edge)
        op.clock = {'fixture': r['clock']}; op.scope_units = (UNIT,)
        op.t1_committed = {'after': {'config.yaml': 'a' * 64}}
        monkeypatch.setattr(op, 'before_unchanged', lambda: None)
        monkeypatch.setattr(op, '_pending', lambda: None)
        return op
    original = operator(first); original.consume()
    intent = (transaction / 'intent.json').read_bytes()
    with pytest.raises(ValueError, match='consumed_no_retry'): operator(second).consume()
    assert (transaction / 'intent.json').read_bytes() == intent
    assert json.loads(intent)['clock_reference'] == first['clock']
    assert json.loads(intent)['retry_authorized'] is False


def test_request_inode_change_refused_before_native_preflight(source, tmp_path, monkeypatch):
    r = request(); _, r['clock'] = clock(source, tmp_path)
    ref = save(tmp_path / 'request.json', r)
    events = []
    class Boundary:
        def __init__(self, *a, **k): pass
        def preflight(self): events.append('unexpected-preflight')
    monkeypatch.setattr(source.st, 'CurrentObservationOperator', Boundary)
    monkeypatch.setattr(source.ordinary, 'same_update_file', lambda *a, **k: False)
    with pytest.raises(ValueError, match='request_identity_changed'):
        source.st.observe_current_native(r, request_path=ref['path'], request_sha256=ref['sha256'])
    assert events == []


# P terminal custody regressions. All failures/streams are inert source adapters.
def terminal_capture(entry, original, *, stdout=None, stderr=None, api=None,
        request_sha256='4' * 64):
    def observer(*args, **kwargs):
        raise original
    entry.ns['observe_dsh_current'] = observer
    api = api or entry.terminal_api()
    entry.ns['api'] = lambda: api
    stdout = stdout if stdout is not None else io.StringIO()
    stderr = stderr if stderr is not None else io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        with pytest.raises(api.InstallerExit if isinstance(api.InstallerExit, type) else SystemExit) as caught:
            entry.ns['dsh_current_observation_cli']({'private': 'not-projected'},
                request_path='/private/no-output', request_sha256=request_sha256)
    transfer = caught.value
    assert transfer.friday_custody_primary is original
    assert transfer.__cause__ is original
    assert transfer.friday_custody_secondary == getattr(original, 'friday_secondary_failures', ())
    return transfer, stdout, stderr


@pytest.mark.parametrize('kind,code,label', [
    (StopUnconfirmed, 3, 'stop_unconfirmed'), (Refusal, 2, 'source_refused'),
    (PermissionError, 2, 'permission_error'), (TypeError, 2, 'type_error')])
def test_terminal_sanitized_request_phase_class_location(entry, kind, code, label):
    original = kind('/private/token=secret user-body-do-not-export')
    transfer, stdout, stderr = terminal_capture(entry, original)
    assert transfer.code == code
    value = json.loads(stderr.getvalue())
    assert value['phase'] == 'observe-dsh-current'
    assert value['request_sha256'] == '4' * 64
    location = value['failure_location']
    assert location['exception_type'] == label
    assert location['source_frames']
    assert all(frame['module'] == 'scripts/friday_ordinary_install.py'
        and type(frame['line']) is int and frame['line'] > 0
        for frame in location['source_frames'])
    assert location['trace_truncated'] is False
    assert not any(word in stderr.getvalue() + stdout.getvalue()
        for word in ('/private', 'secret', 'user-body', 'not-projected', str(SOURCE)))
    assert set(json.loads(stdout.getvalue())) == {'state', 'ready', 'error', 'effects', 'per_job_authority'}


@pytest.mark.parametrize('sha', ['secret-token', 'A' * 64, 'g' * 64, '/' * 64, 42, None, True])
def test_terminal_invalid_correlation_never_echoes_input(entry, sha):
    _, _, stderr = terminal_capture(entry, Refusal('denied'), request_sha256=sha)
    assert json.loads(stderr.getvalue())['request_sha256'] == 'UNAVAILABLE'
    assert 'secret-token' not in stderr.getvalue()


def test_terminal_unknown_class_name_and_refusal_reason_redacted(entry):
    private_type = type('secret-/private/exception-class', (ValueError,), {})
    _, _, stderr = terminal_capture(entry, private_type('secret-value'))
    assert json.loads(stderr.getvalue())['failure_location']['exception_type'] == 'other'
    assert 'secret' not in stderr.getvalue() and '/private' not in stderr.getvalue()
    _, _, stderr = terminal_capture(entry, Refusal('/private/secret-reason'))
    assert json.loads(stderr.getvalue())['diagnostic']['reason'] == 'native_operation_failed'
    assert 'secret' not in stderr.getvalue()


class TerminalBrokenStream(io.StringIO):
    def __init__(self, secondary, operation):
        super().__init__(); self.secondary = secondary; self.operation = operation
    def write(self, text):
        if self.operation == 'write': raise self.secondary
        return super().write(text)
    def flush(self):
        if self.operation == 'flush': raise self.secondary
        return super().flush()


@pytest.mark.parametrize('channel,operation', [('stdout', 'write'), ('stdout', 'flush'),
    ('stderr', 'write'), ('stderr', 'flush')])
def test_terminal_stream_failures_are_secondary_and_other_stream_survives(entry, channel, operation):
    original = StopUnconfirmed('primary-secret')
    secondary = BrokenPipeError('secondary-secret')
    streams = {channel: TerminalBrokenStream(secondary, operation)}
    transfer, stdout, stderr = terminal_capture(entry, original, **streams)
    assert transfer.code == 3
    assert secondary in transfer.friday_custody_secondary
    surviving = stderr if channel == 'stdout' else stdout
    assert json.loads(surviving.getvalue())
    assert 'secret' not in surviving.getvalue()


def test_terminal_both_broken_streams_keep_original_and_bounded_secondary(entry):
    original = StopUnconfirmed('primary-secret')
    stdout_failure = BrokenPipeError('stdout-secret'); stderr_failure = OSError('stderr-secret')
    transfer, _, _ = terminal_capture(entry, original,
        stdout=TerminalBrokenStream(stdout_failure, 'write'),
        stderr=TerminalBrokenStream(stderr_failure, 'write'))
    assert transfer.code == 3
    assert transfer.friday_custody_secondary == (stderr_failure, stdout_failure)
    assert len(transfer.friday_custody_secondary) <= 16


@pytest.mark.parametrize('failing_call', [1, 2])
def test_terminal_json_format_failures_keep_original_and_other_projection(entry, monkeypatch, failing_call):
    original = StopUnconfirmed('primary-secret'); secondary = TypeError('format-secret')
    dumps = json.dumps; calls = []
    def fail_one(*args, **kwargs):
        calls.append(None)
        if len(calls) == failing_call: raise secondary
        return dumps(*args, **kwargs)
    monkeypatch.setattr(json, 'dumps', fail_one)
    transfer, stdout, stderr = terminal_capture(entry, original)
    assert transfer.code == 3 and transfer.friday_custody_secondary == (secondary,)
    assert json.loads((stdout if failing_call == 1 else stderr).getvalue())


def test_terminal_diagnostic_failure_still_emits_correlation_and_primary(entry):
    original = StopUnconfirmed('primary-secret'); secondary = RuntimeError('diagnostic-secret')
    api = entry.terminal_api()
    def unavailable(*args): raise secondary
    api.retained_diagnostic = unavailable
    transfer, stdout, stderr = terminal_capture(entry, original, api=api)
    assert transfer.friday_custody_secondary == (secondary,)
    assert json.loads(stdout.getvalue())['state'] == 'STOP_UNCONFIRMED'
    assert json.loads(stderr.getvalue()) == {'phase': 'observe-dsh-current',
        'request_sha256': '4' * 64, 'diagnostic': {'reason': 'diagnostic_unavailable'},
        'failure_location': {'exception_type': 'other', 'source_frames': [], 'trace_truncated': False}}
    assert 'secret' not in stderr.getvalue()


def test_terminal_retained_diagnostic_failure_uses_source_bounded_secondary(entry):
    original = Refusal('primary-secret'); secondary = RuntimeError('safe-diagnostic-secret')
    api = entry.terminal_api()
    api.retained_diagnostic.__globals__['safe_diagnostic'] = lambda *a: (_ for _ in ()).throw(secondary)
    transfer, _, stderr = terminal_capture(entry, original, api=api)
    assert transfer.friday_custody_secondary == (secondary,)
    assert json.loads(stderr.getvalue())['diagnostic']['reason'] == 'diagnostic_unavailable'


def test_terminal_diagnostic_projection_filters_existing_private_fields(entry):
    api = entry.terminal_api(); original = Refusal('secret')
    original.friday_diagnostic = {'phase': '/private/secret', 'reason': 'secret-reason',
        'cessation': '/private/secret', 'returncode': 'secret', 'errno': True,
        'timeout': 'secret', 'reaped': False, 'proof': '/private/secret'}
    _, _, stderr = terminal_capture(entry, original, api=api)
    assert json.loads(stderr.getvalue())['diagnostic'] == {'reason': 'native_operation_failed', 'reaped': False}
    assert 'secret' not in stderr.getvalue() and '/private' not in stderr.getvalue()


def test_terminal_transfer_constructed_before_diagnostic_and_streams(entry):
    api = entry.terminal_api(); events = []; installer_exit = api.InstallerExit
    def transfer(code, original):
        events.append('transfer'); return installer_exit(code, original)
    retained = api.retained_diagnostic
    def diagnostic(*args): events.append('diagnostic'); return retained(*args)
    class Stream(io.StringIO):
        def write(self, text): events.append('output'); return super().write(text)
    api.InstallerExit = transfer; api.retained_diagnostic = diagnostic
    terminal_capture(entry, StopUnconfirmed('secret'), api=api, stdout=Stream(), stderr=Stream())
    assert events[0] == 'transfer' and events.index('diagnostic') < events.index('output')


def test_terminal_secondary_retention_stays_bounded(entry):
    original = StopUnconfirmed('secret')
    original.friday_secondary_failures = tuple(RuntimeError('old') for _ in range(15))
    transfer, _, _ = terminal_capture(entry, original,
        stdout=TerminalBrokenStream(BrokenPipeError('stdout'), 'write'),
        stderr=TerminalBrokenStream(OSError('stderr'), 'write'))
    assert len(transfer.friday_custody_secondary) == 16


def test_terminal_traceback_scan_and_emitted_frames_are_bounded(entry):
    namespace = {}
    exec(compile('def nested(n):\n    if n: return nested(n-1)\n    raise RuntimeError("secret")\n', str(SOURCE), 'exec'), namespace)
    try:
        namespace['nested'](100)
    except RuntimeError as original:
        _, _, stderr = terminal_capture(entry, original)
    location = json.loads(stderr.getvalue())['failure_location']
    assert 0 < len(location['source_frames']) <= 8 and location['trace_truncated'] is True
    assert 'secret' not in stderr.getvalue()


@pytest.mark.parametrize('kind,channel,expected', [
    ('refusal', 'stdout', 2), ('refusal', 'stderr', 2),
    ('stop', 'stdout', 3), ('stop', 'stderr', 3), ('stop', 'both', 3)])
def test_terminal_real_interpreter_broken_pipe_preserves_status(kind, channel, expected):
    """Only a Python/AST source adapter, no native import or authority invocation."""
    import subprocess
    api_source = DEPENDENCIES / 'scripts/friday_install.py'
    code = f'''
import ast, json, sys, types
from pathlib import Path
source = Path({str(SOURCE)!r})
api_source = Path({str(api_source)!r})
class StopUnconfirmed(RuntimeError): pass
class Refused(ValueError):
    def __init__(self, reason):
        super().__init__(reason); self.reason = reason
package = types.ModuleType('scripts'); package.__path__ = []
prepare = types.ModuleType('scripts.dsh_prepare')
prepare.StopUnconfirmed = StopUnconfirmed
prepare.CommandFailed = type('CommandFailed', (RuntimeError,), {{}})
prepare.safe_observation = lambda value: value
sys.modules['scripts'] = package; sys.modules['scripts.dsh_prepare'] = prepare
names = {{'InstallerExit', 'remember_secondary', 'retained_diagnostic', 'safe_diagnostic'}}
api_ns = {{'Refused': Refused}}
exec(compile(ast.Module(body=[n for n in ast.parse(api_source.read_text()).body
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names],
    type_ignores=[]), str(api_source), 'exec'), api_ns)
api = types.SimpleNamespace(**{{name: api_ns[name] for name in names}}, Refused=Refused)
entry_ns = {{'json': json, 'api': lambda: api, '__file__': str(source)}}
entry_names = {{'_dsh_current_observation_failure_diagnostic', 'dsh_current_observation_cli'}}
exec(compile(ast.Module(body=[n for n in ast.parse(source.read_text()).body
    if isinstance(n, ast.FunctionDef) and n.name in entry_names],
    type_ignores=[]), str(source), 'exec'), entry_ns)
def observer(*args, **kwargs):
    raise (StopUnconfirmed if {kind!r} == 'stop' else Refused)('/private/secret-sentinel')
entry_ns['observe_dsh_current'] = observer
entry_ns['dsh_current_observation_cli']({{}}, request_path='/private/secret-sentinel', request_sha256='4'*64)
'''
    descriptors = []
    outputs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
    try:
        for name in ('stdout', 'stderr') if channel == 'both' else (channel,):
            read_fd, write_fd = os.pipe(); os.close(read_fd)
            descriptors.append(write_fd); outputs[name] = write_fd
        result = subprocess.run([sys.executable, '-I', '-B', '-c', code],
            stdin=subprocess.DEVNULL, **outputs, check=False, timeout=10)
    finally:
        for descriptor in descriptors: os.close(descriptor)
    assert result.returncode == expected
    if channel != 'both':
        surviving = result.stderr if channel == 'stdout' else result.stdout
        json.loads(surviving)
        assert b'secret' not in surviving and b'/private' not in surviving
        assert b'Exception ignored' not in surviving


def test_terminal_missing_stderr_cannot_redirect_diagnostic_into_stdout(entry):
    original = Refusal('secret'); api = entry.terminal_api(); output = io.StringIO()
    def observer(*args, **kwargs): raise original
    entry.ns['observe_dsh_current'] = observer; entry.ns['api'] = lambda: api
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(None):
        with pytest.raises(api.InstallerExit) as caught:
            entry.ns['dsh_current_observation_cli']({}, request_path='/private', request_sha256='4'*64)
    assert caught.value.friday_custody_primary is original
    assert len(caught.value.friday_custody_secondary) == 1
    assert isinstance(caught.value.friday_custody_secondary[0], AttributeError)
    assert json.loads(output.getvalue())['state'] == 'FAILED_CLOSED_RECONCILE_EXACT_JOURNAL'
    assert 'failure_location' not in output.getvalue()
