"""New caller seams only. Synthetic data; no UNO/Office imports or real inputs."""
import ast
import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import types
import unittest

sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
os.sched_setaffinity(0, set(sorted(os.sched_getaffinity(0))[:2]))
ROOT = Path(__file__).parent / 'candidate'
sys.path.insert(0, str(ROOT))
SENTINEL = 'SYNTHETIC_SECRET_MUST_NOT_APPEAR_IN_METADATA'
EXPECTED_DIGEST = 'a' * 64


class FakeOut:
    def __init__(self, path='/work'):
        self.path = path
    def __truediv__(self, name):
        return FakeOut(self.path + '/' + name)
    def mkdir(self, **kw):
        assert kw == dict(mode=0o700, exist_ok=False)


contract = types.ModuleType('f06_contract')
contract.MODE = 'one-template-diagnostic'
contract.need = lambda value, code: None if value else (_ for _ in ()).throw(ValueError(code))
contract.limits = lambda mode: dict(max_metadata_bytes=32768)
contract.within = lambda: None
contract.safe_dir = lambda path: FakeOut(str(path))
contract.decode = lambda raw: json.loads(raw)
sys.modules['f06_contract'] = contract
import diagnostic_client as client
import request_args_compat_v2 as compat

CALLS = []


def original(self, name, value):
    CALLS.append((type(self), name))
    if name == 'args':
        raise AttributeError(SENTINEL)
    return object.__setattr__(self, name, value)


CLASSES = {name: type(name, (Exception,), {'__pyunostruct__': name,
    '__setattr__': original, '__init__': lambda self: None}) for name in compat.REQUEST_NAMES}


class Request:
    def __init__(self, action):
        self.action = action
        self.calls = 0
    def getRequest(self):
        self.calls += 1
        return self.action()
    def getContinuations(self):
        return []


class Document:
    def __init__(self):
        self.closed = 0
    def supportsService(self, name):
        return name == 'com.sun.star.text.TextDocument'
    def getText(self):
        return self
    def getString(self):
        return 'OTT-UNIQUE-BEFORE\nRETAINED-TEXT-PARAGRAPH'
    def close(self, save):
        assert save is True
        self.closed += 1


class NewSeamControls(unittest.TestCase):
    def setUp(self):
        gc.collect()
        CALLS.clear()
        self.uno = types.ModuleType('synthetic_uno')
        self.uno._uno_struct__setattr__ = original
        self.uno.getClass = CLASSES.__getitem__
        self.unohelper = types.SimpleNamespace(Base=type('SyntheticBase', (), {}))
        self.itype = type('SyntheticInteractionHandler', (), {})
        self.saved = []
        self.snapshots = 0
        self.snapshot_impl = client.input_snapshot
        self.adapter_impl = client.observe_one_readonly
        self.extra_classes = []
        self.requests = []
        self.loads = 0
        self.document = Document()
        self.after_drift = False
        self.after_fault = False
        self.action = lambda: CLASSES[compat.REQUEST_NAMES[0]]()
        self.extra_callback = False
        self.semantic_bad = False
        contract.save = lambda path, value: self.saved.append(copy.deepcopy(value))
        def snapshot(digest):
            self.assertEqual(digest, EXPECTED_DIGEST)
            self.snapshots += 1
            if self.snapshots > 1 and self.after_fault:
                raise ValueError(SENTINEL)
            return dict(identity=2 if self.snapshots > 1 and self.after_drift else 1), json.dumps({'password': SENTINEL}).encode()
        client.input_snapshot = snapshot
        self.desktop = types.SimpleNamespace(loadComponentFromURL=self.load)

    def tearDown(self):
        client.input_snapshot = self.snapshot_impl
        client.observe_one_readonly = self.adapter_impl
        self.uno._uno_struct__setattr__ = original
        for cls in list(CLASSES.values()) + self.extra_classes:
            cls.__setattr__ = original

    def load(self, url, target, flags, properties):
        self.loads += 1
        self.assertEqual((url, target, flags), (client.SELECTED_URL, '_blank', 0))
        props = {row.Name: row.Value for row in properties}
        self.assertEqual(set(props), {'Hidden', 'ReadOnly', 'AsTemplate', 'MacroExecutionMode', 'UpdateDocMode', 'InteractionHandler', 'Password'})
        for key in ('Hidden', 'ReadOnly'):
            self.assertIs(props[key], True)
        self.assertIs(props['AsTemplate'], False)
        self.assertEqual(props['MacroExecutionMode'], 0)
        self.assertEqual(props['UpdateDocMode'], 0)
        self.assertEqual(props['Password'], SENTINEL)
        req = Request(self.action)
        self.requests.append(req)
        props['InteractionHandler'].handle(req)
        if self.extra_callback:
            req = Request(self.action)
            self.requests.append(req)
            props['InteractionHandler'].handle(req)
        return self.document

    def run_client(self):
        exitcode = client.run_once(uno=self.uno, unohelper=self.unohelper, desktop=self.desktop,
            property_value=types.SimpleNamespace, interaction_handler_type=self.itype,
            password_request_type=CLASSES[compat.REQUEST_NAMES[0]],
            ms_password_request_type=CLASSES[compat.REQUEST_NAMES[1]],
            error_code_request_type=CLASSES[compat.REQUEST_NAMES[4]], input_manifest_sha256=EXPECTED_DIGEST)
        self.assertEqual(self.snapshots, 2)
        self.assertEqual(len(self.saved), 1)
        value = self.saved[0]
        client.result_contract(value, EXPECTED_DIGEST, exitcode)
        raw = json.dumps(value, ensure_ascii=True, indent=2) + '\n'
        self.assertNotIn(SENTINEL, raw)
        self.assertLessEqual(len(raw.encode()), 32768)
        self.assertFalse(value['original_strict_all_pass'])
        self.assertFalse(value['acceptance_granted'])
        self.assertLessEqual(self.loads, 1)
        return exitcode, value

    def test_same_connected_desktop_one_load_cleanup_restore(self):
        code, value = self.run_client()
        self.assertEqual(code, 0)
        self.assertEqual(value['state'], 'COMPLETE_METADATA_DIAGNOSTIC_ONLY')
        self.assertEqual(self.loads, 1)
        self.assertEqual(self.requests[0].calls, 1)
        self.assertEqual(self.document.closed, 1)
        self.assertTrue(all(cls.__dict__['__setattr__'] is original for cls in CLASSES.values()))

    def test_actual_second_callback_refused_before_second_get_request(self):
        self.extra_callback = True
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIn('EXTRA_CALLBACK', value['terminal_reasons'])
        self.assertEqual([req.calls for req in self.requests], [1, 0])
        self.assertEqual(self.loads, 1)

    def test_named_unknown_conversion_class_preserved_no_expansion(self):
        cls = type('com.sun.star.synthetic.NewConversionFailure', (Exception,),
            {'__pyunostruct__': 'com.sun.star.synthetic.NewConversionFailure', '__setattr__': original, '__init__': lambda self: None})
        self.extra_classes.append(cls)
        def action():
            cls().args = (SENTINEL,)
        self.action = action
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIn('CALLBACK_FAULT', value['terminal_reasons'])
        row = value['diagnostic']['interaction_events'][0]['conversion_probe']['setter_events'][0]
        self.assertEqual(row['generated_exception_class_during_conversion'], cls.__pyunostruct__)
        self.assertEqual(CALLS, [(cls, 'args')])
        self.assertIs(cls.__dict__['__setattr__'], original)

    def test_unknown_normal_payload_stops(self):
        self.action = lambda: object()
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIn('UNKNOWN_CLASS_IDENTITY', value['terminal_reasons'])

    def test_helper_drift_stops_never_overwritten(self):
        foreign = lambda *args: None
        def action():
            self.uno._uno_struct__setattr__ = foreign
            return CLASSES[compat.REQUEST_NAMES[0]]()
        self.action = action
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIn('HOOK_CAS_OR_RESTORATION_DRIFT', value['terminal_reasons'])
        self.assertIs(self.uno._uno_struct__setattr__, foreign)

    def test_staged_cas_drift_stops_after_one_observation(self):
        self.after_drift = True
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertFalse(value['input_cas_after'])
        self.assertIn('INPUT_CAS_DRIFT', value['terminal_reasons'])

    def test_after_cas_error_does_not_hide_observation(self):
        self.after_fault = True
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIsNotNone(value['diagnostic'])
        self.assertIn('INPUT_CAS_DRIFT', value['terminal_reasons'])

    def test_adapter_failure_cas_still_checked_and_client_stops(self):
        def fail(**kw):
            raise RuntimeError(SENTINEL)
        client.observe_one_readonly = fail
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIsNone(value['diagnostic'])
        self.assertIn('METADATA_FAILURE', value['terminal_reasons'])

    def test_metadata_unknown_field_is_never_serialized(self):
        def injected(**kw):
            value = self.adapter_impl(**kw)
            value['payload'] = SENTINEL
            return value
        client.observe_one_readonly = injected
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIsNone(value['diagnostic'])

    def test_metadata_32k_overflow_fixed_stop_fallback(self):
        def oversized(**kw):
            value = self.adapter_impl(**kw)
            value['interaction_events'][0]['conversion_probe']['cleanup_failures'] = ['POSTSCAN_FAILED'] * 4000
            return value
        client.observe_one_readonly = oversized
        code, value = self.run_client()
        self.assertEqual(code, 1)
        self.assertIsNone(value['diagnostic'])
        self.assertIn('METADATA_FAILURE', value['terminal_reasons'])


class SourceControls(unittest.TestCase):
    def test_exact_task27_five_reviewed_libraries(self):
        expected = {'callback_observer_v2.py': '746846c1ab7c8e19585ed9d51a303b88ebbd41ce31ebee98614e056efc34e967',
            'conversion_probe.py': 'bb556abab6aecde55d61e8f7372fdba980303daabeaae322b40f7e152d3ab1f5',
            'readonly_diagnostic.py': 'de112168cc22f635e08eb43b97a62b6b5d14add24a2e755f9a515010162656cf',
            'request_args_compat_v2.py': '23a2d996d7ee940b4a8a07140867e8e50e57b24859b18884872781ac40e1fc18', 'diagnostic_client.py':'5c8de29ece89b5f57435f3a40746223dea49c5582be50c9f3fcf8b376d218a9d'}
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_python312_grammar_all_new_and_exact_sources(self):
        for path in ROOT.glob('*.py'):
            ast.parse(path.read_bytes(), filename=str(path), feature_version=(3, 12))

    def test_embedded_main_handshake_same_desktop_no_second_resolve(self):
        source = (ROOT / 'embedded_entry.py').read_text()
        self.assertIn("run_name='f06_diagnostic_library'", source)
        self.assertIn("exitcode=oracle['run_once'](uno=uno,unohelper=unohelper,desktop=desktop", source)
        self.assertEqual(source.count('resolver.resolve('), 1)
        self.assertNotIn("run_name='__main__'", source)
        self.assertIn('sys.version_info[:3]!=(3,12,13)', source)
        self.assertIn('sys.flags.no_site and sys.flags.no_user_site', source)

    def test_namespace_no_rawlogs_and_actual81_only(self):
        source = (ROOT / 'inside_once.py').read_text()
        self.assertEqual(source.count('stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL'), 2)
        self.assertNotIn("stdout.private", source)
        module = ast.parse(source)
        fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'continuation')
        ns = {'c': types.SimpleNamespace(need=contract.need, within=lambda: None)}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<pure-continuation-seam>', 'exec'), ns)
        record = dict(Office_exit=81, Office_exit_observed_by_wait=True, Office_terminal_before_cleanup=True,
            client_ready=False, pipe_accepted=False, oracle_entered=False, oracle_result_exists=False,
            document_phase_exists=False, owned_children_closed=True, owned_pipe_closed=True, matching_socket_files=[])
        ns['continuation'](record, 1, 3)
        for key, value in (('Office_exit', 0), ('Office_exit', -9), ('client_ready', True),
                ('document_phase_exists', True), ('owned_children_closed', False)):
            bad = dict(record); bad[key] = value
            with self.assertRaises(ValueError):
                ns['continuation'](bad, 1, 3)
        with self.assertRaises(ValueError):
            ns['continuation'](record, 3, 3)

    def test_owned_pipe_requires_accepted_role_allows_bounded_multiple(self):
        module = ast.parse((ROOT / 'inside_once.py').read_bytes())
        fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'ownership')
        call = next(node for node in ast.walk(fn) if isinstance(node, ast.Call)
            and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == 'OWN_PIPE_EXACT_ONE_LISTENER_AND_ACCEPTED_CONNECTION')
        predicate = compile(ast.Expression(body=call.args[0]), '<pure-ownedpipe-cardinality>', 'eval')
        self.assertFalse(eval(predicate, dict(listeners=[1], connected=[])))
        self.assertFalse(eval(predicate, dict(listeners=[], connected=[1])))
        self.assertTrue(eval(predicate, dict(listeners=[1], connected=[1])))
        self.assertTrue(eval(predicate, dict(listeners=[1], connected=[1, 2])))

    def test_parent_current_manifest_contract_consumes_exact_narrow_row(self):
        import stat
        source = (ROOT.parent / 'candidate' / 'f06_contract.py').read_bytes()
        module = ast.parse(source)
        names = {'need', 'reference_shape', 'full_pin_shape', 'manifest_contract', 'exact_json'}
        definitions = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]
        ns = dict(stat=stat, os=os, re=client.re, json=json, REF_KEYS={'path', 'bytes', 'sha256', 'identity'},
            ASSIGNMENT='ASTRA-NATIVE-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112#1',
            SELECTED_ID='template-ott-source', SELECTED_SHA=client.SELECTED_SHA,
            PROFILES=('own_synthetic_odf13_aes256cbc_pbkdf2sha1_4096',), NAMES=('retained-source.ott',))
        exec(compile(ast.Module(body=definitions, type_ignores=[]), '<pure-parent-contract>', 'exec'), ns)
        pin = dict(path='/synthetic/source.ott', bytes=4624, sha256=client.SELECTED_SHA,
            identity=[1, 2, stat.S_IFREG | 0o600, os.getuid(), os.getgid(), 1, 4624, 3, 4])
        credential = dict(pin, path='/synthetic/credential.json', sha256='b' * 64)
        row = dict(pin, fixture_id='template-ott-source', format='ott', role='source',
            fixture_profile=ns['PROFILES'][0], semantic='BEFORE', mime='application/vnd.oasis.opendocument.text-template',
            service='com.sun.star.text.TextDocument', filter='writer8_template', staged_name='retained-source.ott',
            native_source_ciphertext=dict(pin))
        manifest = dict(schema='friday.f06.one-template-selected.v1', state='ROOT_BOUND_RETAINED_METADATA_NOT_EXECUTION_AUTHORITY',
            assignment=ns['ASSIGNMENT'], selected_count=1, selected_fixture_ids=client.IDS,
            expected_Office_stores=0, expected_Office_password_probes=1, whole_F06_accepted=False,
            as_template=False, credential=credential, fixtures=[row])
        self.assertEqual(ns['manifest_contract'](manifest), row)
        bad = copy.deepcopy(manifest); bad['credential']['sha256'] = None
        with self.assertRaises(ValueError):
            ns['manifest_contract'](bad)


class InputConsumerControls(unittest.TestCase):
    def setUp(self):
        self.oldprivate = getattr(contract, 'private', None)
        self.oldmanifest = getattr(contract, 'manifest_contract', None)
        self.oldsafe = contract.safe_dir
        self.cipher = dict(path='/synthetic/original/own-source.ott', bytes=4624,
            sha256=client.SELECTED_SHA, identity=[1, 2, 33152, 1000, 1000, 1, 4624, 3, 4])
        self.credential = dict(path='/synthetic/original/credential.json', bytes=123,
            sha256='b' * 64, identity=[1, 3, 33152, 1000, 1000, 1, 123, 3, 4])
        self.manifest = dict(fixtures=[dict(self.cipher, fixture_id='template-ott-source')], credential=self.credential)
        self.staged = dict(selected_count=1, selected_fixture_ids=client.IDS, input_sha256=EXPECTED_DIGEST,
            expected_probes=1, expected_stores=0, credential_source=self.credential,
            source_pins=[dict(self.cipher, fixture_id='template-ott-source', native_source_ciphertext=self.cipher)])
        self.rows = {
            '/inputs/NATIVE-OUTPUTS.json': (lambda: json.dumps(self.manifest).encode(), dict(sha256=EXPECTED_DIGEST)),
            '/inputs/STAGED.json': (lambda: json.dumps(self.staged).encode(), dict(sha256='c' * 64)),
            '/inputs/native-outputs/retained-source.ott': (lambda: b'not-a-real-document', dict(bytes=4624, sha256=client.SELECTED_SHA)),
            '/inputs/credential.private.json': (lambda: b'not-a-real-credential', dict(bytes=123, sha256='b' * 64)),
        }
        contract.private = lambda path, root: (self.rows[str(path)][0](), dict(self.rows[str(path)][1]))
        self.validated = []
        contract.manifest_contract = lambda manifest: self.validated.append(manifest)
        contract.safe_dir = lambda path: types.SimpleNamespace(iterdir=lambda: [Path('/synthetic/retained-source.ott')])

    def tearDown(self):
        contract.private = self.oldprivate
        contract.manifest_contract = self.oldmanifest
        contract.safe_dir = self.oldsafe

    def test_real_input_consumer_full_sha_nested_old_stage_shape(self):
        snapshot, raw = client.input_snapshot(EXPECTED_DIGEST)
        self.assertEqual(len(self.validated), 1)
        self.assertEqual(set(snapshot), {'manifest', 'staged', 'cipher', 'credential'})
        self.assertEqual(raw, b'not-a-real-credential')
        self.assertEqual(snapshot['credential']['bytes'], 123)  # not historical115-only

    def test_real_input_consumer_rejects_credential_digest_drift(self):
        self.rows['/inputs/credential.private.json'][1]['sha256'] = 'd' * 64
        with self.assertRaises(ValueError):
            client.input_snapshot(EXPECTED_DIGEST)

    def test_real_input_consumer_rejects_second_fixture_and_original_pin_drift(self):
        self.staged['selected_count'] = 2
        with self.assertRaises(ValueError):
            client.input_snapshot(EXPECTED_DIGEST)
        self.staged['selected_count'] = 1
        self.staged['source_pins'][0]['native_source_ciphertext'] = dict(self.cipher, sha256='e' * 64)
        with self.assertRaises(ValueError):
            client.input_snapshot(EXPECTED_DIGEST)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(schema='friday.f06.one-template.inside-pure-controls.v1',
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        source_only=True, real_Office_starts=0, real_UNO_imports=0, real_document_loads=0,
        real_credential_reads=0, resource_caps=dict(wall_seconds=90, CPU_seconds=60,
        AS_bytes=512*1024**2, affinity_cpus=2))))
    raise SystemExit(not result.wasSuccessful())
