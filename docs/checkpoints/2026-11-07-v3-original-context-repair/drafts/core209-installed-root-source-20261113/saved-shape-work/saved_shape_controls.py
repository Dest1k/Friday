#!/usr/bin/python3
"""Finite source controls. Saved Root metadata stays historical and output stays UNBOUND.

The connected probe uses genuine R1 metadata with explicit saved-dependency seams:
validate_source_request -> saved actual projection; source_origin -> saved proof;
actual_predecessor -> saved predecessor ref; clock/boot -> saved snapshot values.
Those seams supply no current/native/real-H/admission credit. Binder bytes remain
in memory; no ROOT-209-BOUND-INPUTS.json or Root verdict is written.
"""
from pathlib import Path, PosixPath
import argparse, ast, contextlib, copy, datetime, hashlib, importlib.util, io
import json, os, sys, types

W = Path(__file__).resolve().parent
R1 = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-ROOT-FRAME-PREP-20261113-R1')
S = Path('/home/jericho/.cache/FRW-SOL-V3-F07-NATIVE209-AFTER208-CORE-20261113')
CACHE = Path('/home/jericho/.cache')
EXPECTED_GATES_SHA = '82e66953a98235f690783456bf66bd5a10910b98aa8402f85e53a94ab0edff2c'
EXPECTED_R1_SOURCE_PINS_SHA = 'cc66b9cb42ec75f5a8af6e1133842976cce1949b030905b1b70590f6e873f90b'


def check(value, why):
    if not value:
        raise AssertionError(why)


def permitted(path):
    p = Path(path)
    check(p.is_absolute() and p.is_relative_to(CACHE), 'forbidden_noncache_read:' + str(p))
    check(p.resolve().is_relative_to(CACHE), 'forbidden_resolved_noncache_read:' + str(p))
    return p


def raw(path):
    return permitted(path).read_bytes()


def ref(path):
    p = permitted(path)
    return dict(path=str(p), sha256=hashlib.sha256(raw(p)).hexdigest())


def load(path):
    return json.loads(raw(path))


def dump(name, value):
    p = W / name
    check(p.parent == W, 'own_output_required')
    data = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
    os.chmod(p, 0o600)
    return ref(p)


def expect_reject(module, call, label):
    try:
        call()
    except module.InvalidBinding as exc:
        return dict(control=label, state='PASS_REJECTED', reason=str(exc))
    raise AssertionError('accepted_negative:' + label)


def function_ast(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def shape(value, depth=0):
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'}:
            return dict(kind='strict2', path=value['path'])
        if set(value) == {'path', 'sha256', 'bytes'}:
            return dict(kind='sized3', path=value['path'], bytes_type=type(value['bytes']).__name__)
        return {k: shape(v, depth+1) for k,v in value.items()} if depth < 2 else dict(keys=sorted(value))
    if isinstance(value, list):
        return dict(count=len(value), item_shapes=[shape(v, depth+1) for v in value] if len(value) < 10 else 'inventory_omitted')
    return type(value).__name__


def controls(metadata):
    check(sys.flags.isolated and sys.dont_write_bytecode, 'run_python_I_B_required')
    metadata = permitted(metadata)
    check(metadata.name == 'root209_metadata.py', 'exact_metadata_module_required')
    spec = importlib.util.spec_from_file_location('Core209SavedShapeControl', metadata)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    old_tree = ast.parse(raw(R1/'root209_metadata.py'))
    new_tree = ast.parse(raw(metadata))
    check(ref(R1/'SOURCE-PINS.json')['sha256'] == EXPECTED_R1_SOURCE_PINS_SHA, 'R1_source_manifest_changed')
    check(ref(R1/'root209_metadata.py')['sha256'] == load(R1/'SOURCE-PINS.json')['source_refs'][str(R1/'root209_metadata.py')], 'R1_source_snapshot_changed')
    check(ast.dump(function_ast(old_tree, 'readref')) == ast.dump(function_ast(new_tree, 'readref')), 'readref_must_remain_unchanged_strict2')
    check(hasattr(m, 'read_sized_source_ref'), 'separate_sized_reader_required')
    sized_calls = [n for n in ast.walk(new_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'read_sized_source_ref']
    join_calls = [n for n in ast.walk(function_ast(new_tree, 'validate_join')) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'read_sized_source_ref']
    check(len(sized_calls) == len(join_calls) == 2, 'exact_two_gate_slot_calls_in_join_required')
    check({ast.unparse(n.args[0]) for n in join_calls} == {"row['result']", "row['process_record']"}, 'sized_reader_only_exact_gate_slots')
    check(ast.dump(function_ast(old_tree, 'main')) == ast.dump(function_ast(new_tree, 'main')), 'binder_code_changed')
    check(ast.dump(function_ast(old_tree, 'load_actor_binding')) == ast.dump(function_ast(new_tree, 'load_actor_binding')), 'actor_loader_code_changed')

    gates = load(S/'GATES-SUMMARY.json')
    check(ref(S/'GATES-SUMMARY.json')['sha256'] == EXPECTED_GATES_SHA, 'genuine_gate_summary_changed')
    gate_refs = [(kind, slot, gates['runs'][kind][slot]) for kind in ('operational-success', 'operational-rollback') for slot in ('result', 'process_record')]
    results = []
    for kind, slot, row in gate_refs:
        check(set(row) == {'path','sha256','bytes'} and type(row['bytes']) is int, 'exact_genuine_sized3_required')
        data = raw(row['path'])
        check(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], 'genuine_gate_ref_bytes_or_hash_changed')
        check(m.read_sized_source_ref(row) == json.loads(data), 'sized_reader_json_changed')
        results.append(dict(control='genuine_four_sized_refs/'+kind+'/'+slot, state='PASS', reference=row))
        results.append(expect_reject(m, lambda row=row: m.readref(row), 'strict2_rejects_sized3/'+kind+'/'+slot))
    first = gate_refs[0][2]
    mutations = {
        'missing_bytes': {k:v for k,v in first.items() if k != 'bytes'},
        'bool_bytes': dict(first, bytes=True),
        'float_bytes': dict(first, bytes=float(first['bytes'])),
        'string_bytes': dict(first, bytes=str(first['bytes'])),
        'negative_bytes': dict(first, bytes=-1),
        'wrong_zero_bytes': dict(first, bytes=0),
        'wrong_positive_bytes': dict(first, bytes=first['bytes']+1),
        'huge_wrong_bytes': dict(first, bytes=2**256),
        'unexpected_field': dict(first, grant=True),
        'missing_path': {k:v for k,v in first.items() if k != 'path'},
        'missing_sha256': {k:v for k,v in first.items() if k != 'sha256'},
        'relative_path': dict(first, path='relative.json'),
        'invalid_sha256': dict(first, sha256='not-a-sha'),
        'wrong_valid_sha256': dict(first, sha256='0'*64),
    }
    for name, row in mutations.items():
        results.append(expect_reject(m, lambda row=row: m.read_sized_source_ref(row), 'sized3/'+name))
    for name, row in [('not_dict',None), ('list',list(first.items())), ('dict_subclass',type('RefSubclass',(dict,),{})(first))]:
        results.append(expect_reject(m, lambda row=row: m.read_sized_source_ref(row), 'sized3/'+name))

    # Actual Root-produced historical metadata. None is copied as an R2 verdict.
    names = ['ROOT-209-SOURCE-ACCEPTANCE.json', 'ROOT-209-PROJECT-SOURCE.json',
             'ROOT-209-PUBLIC-ORIGIN-POLICY.json', 'ROOT-209-INDEPENDENT-ACTUAL-BULK-ACCEPTANCE.json',
             'ROOT-209-INDEPENDENT-FRAME-ACCEPTANCE.json', 'ROOT-209-CURRENT-SERVICE-ANCHOR.json',
             'ROOT-209-RUNTIME-AUTHORITY.json', 'ROOT-FRESH-REQUEST.json',
             'ROOT-209-FRESH-READBACK.json', 'ROOT-ACTUAL208-PREDECESSOR.json']
    docs = {name:load(R1/name) for name in names}
    matrix = [dict(file=ref(R1/name), shape=shape(docs[name])) for name in names]
    q = docs['ROOT-FRESH-REQUEST.json']
    acceptance = docs['ROOT-209-SOURCE-ACCEPTANCE.json']
    snapshot = docs['ROOT-209-FRESH-READBACK.json']
    predecessor = docs['ROOT-ACTUAL208-PREDECESSOR.json']
    boundary = load(R1/'FUTURE-EXECUTION/CORE209-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json')
    check(boundary['request'] == ref(R1/'ROOT-FRESH-REQUEST.json'), 'saved_projection_request_join_changed')
    check(snapshot['evidence'] == [ref(R1/'FUTURE-EXECUTION/CORE209-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json')], 'saved_readback_boundary_join_changed')
    check(boundary['source_origin'] == snapshot['source_origin'], 'saved_source_origin_join_changed')
    check(q['current_source_successor']['previous_native_update'] == predecessor['request'], 'saved_predecessor_ref_shape_or_join_changed')
    strict_request_slots = ('marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request target_receipt candidate_input').split()
    check(all(type(q[k]) is dict and set(q[k]) == {'path','sha256'} for k in strict_request_slots), 'saved_builder_request_ref_shape_changed')
    check(hashlib.sha256(m.encoded(acceptance)).hexdigest() == ref(R1/'ROOT-209-SOURCE-ACCEPTANCE.json')['sha256'], 'canonical_acceptance_hash_mismatch')

    original_readref, original_reference = m.readref, m.reference
    original_sized = m.read_sized_source_ref
    trace, dependencies, sized_trace = [], [], []
    captured = {}
    bound_path = R1/'ROOT-209-BOUND-INPUTS.json'
    boot_path = '/proc/sys/kernel/random/boot_id'
    saved_now = datetime.datetime.fromisoformat(snapshot['observed_at_moscow']).timestamp() + 0.5
    saved_boot = snapshot['boot_id']

    def guarded_readref(row):
        if captured and row == captured['reference']:
            trace.append(dict(kind='memory_only_binder_payload', path=str(bound_path)))
            return copy.deepcopy(captured['payload'])
        if type(row) is dict and 'path' in row:
            permitted(row['path'])
        trace.append(dict(kind='strict2', reference=copy.deepcopy(row)))
        return original_readref(row)

    def guarded_reference(path):
        if Path(path) == bound_path:
            check(captured, 'binder_payload_not_captured')
            return copy.deepcopy(captured['reference'])
        return original_reference(permitted(path))

    def guarded_sized(row):
        permitted(row['path'])
        sized_trace.append(copy.deepcopy(row))
        return original_sized(row)

    def saved_source_request(request, accepted=None):
        check(request == q and accepted == acceptance, 'source_request_seam_requires_exact_genuine_saved_inputs')
        dependencies.append('validate_source_request:SAVED_ACTUAL_PROJECTION_NO_CURRENT_OR_NATIVE_REVALIDATION')
        return copy.deepcopy(boundary['source_request_projection'])

    def saved_origin(head, remote, *, repository=None, provenance_mode='published-remote', acceptance=None):
        check(repository is None and head == snapshot['head'] and remote == snapshot['origin_main'] and provenance_mode == snapshot['provenance_mode'] and acceptance == docs['ROOT-209-SOURCE-ACCEPTANCE.json'], 'origin_seam_requires_exact_saved_arguments')
        dependencies.append('source_origin:SAVED_ROOT_ORIGIN_PROOF_NO_GIT_OR_CURRENT_SOURCE_READ')
        return copy.deepcopy(snapshot['source_origin'])

    def saved_predecessor():
        check(predecessor['schema'] == 'frw.root.actual208-predecessor.v1' and predecessor['template_only_no_execution_grant'] is False, 'saved_predecessor_metadata_required')
        dependencies.append('actual_predecessor:SAVED_ROOT_PREDECESSOR_REF_NO_H_HISTORY_REVALIDATION')
        return copy.deepcopy(predecessor['request'])

    class SavedPath(PosixPath):
        def read_text(self, *args, **kwargs):
            check(str(self) == boot_path, 'unexpected_module_text_read:' + str(self))
            dependencies.append('boot_id:SAVED_READBACK_BOOT_NO_PROC_READ')
            return saved_boot

    class CapturedFile(io.BytesIO):
        def fileno(self):
            return 209209
        def close(self):
            data = self.getvalue()
            captured['payload'] = json.loads(data)
            captured['reference'] = dict(path=str(bound_path), sha256=hashlib.sha256(data).hexdigest())
            super().close()

    class BinderOs:
        O_WRONLY, O_CREAT, O_EXCL, O_NOFOLLOW = os.O_WRONLY, os.O_CREAT, os.O_EXCL, os.O_NOFOLLOW
        @staticmethod
        def getuid():
            return os.getuid()
        @staticmethod
        def open(path, flags, mode):
            check(Path(path) == bound_path and flags == (os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW) and mode == 0o600, 'unexpected_binder_write')
            dependencies.append('binder_write:MEMORY_ONLY_NO_ROOT_FILE_CREATED')
            return 209209
        @staticmethod
        def fdopen(fd, mode):
            check(fd == 209209 and mode == 'wb', 'unexpected_binder_fdopen')
            return CapturedFile()
        @staticmethod
        def fsync(fd):
            check(fd == 209209, 'unexpected_binder_fsync')

    def forbidden(*args, **kwargs):
        raise AssertionError('forbidden_git_or_external_IO_dependency')

    m.B = R1  # Only genuine saved-R1 binding paths; never bind the R2 frame.
    m.readref, m.reference, m.read_sized_source_ref = guarded_readref, guarded_reference, guarded_sized
    m.validate_source_request, m.source_origin, m.actual_predecessor = saved_source_request, saved_origin, saved_predecessor
    m.origin_git = forbidden
    m.Path = SavedPath
    m.time = types.SimpleNamespace(time=lambda:saved_now)
    m.os = BinderOs
    pure = m.validate_join(copy.deepcopy(q), copy.deepcopy(acceptance), copy.deepcopy(snapshot), now=saved_now, boot_id=saved_boot)
    # Drive the unchanged binder body against memory-only writes and the unchanged
    # actor loader body against that captured payload. No model/actor is invoked.
    argv = sys.argv
    try:
        sys.argv = [str(metadata), '--validate-and-bind']
        with contextlib.redirect_stdout(io.StringIO()) as capture_stdout:
            m.main()
    finally:
        sys.argv = argv
    printed = json.loads(capture_stdout.getvalue())
    check(printed['execution_grant'] is False and printed['bound_inputs'] == captured['reference'], 'binder_printed_binding_changed')
    check(captured['payload']['binding'] == pure, 'binder_saved_shape_binding_differs_from_direct_join')
    actor = m.load_actor_binding(R1)
    check(actor == pure, 'actor_loader_saved_shape_join_changed')
    check(len(sized_trace) == 12 and all(sized_trace.count(row) == 3 for _,_,row in gate_refs), 'four_genuine_sized_refs_required_per_join_binder_actor')
    check(not bound_path.exists(), 'original_R1_bound_file_must_remain_absent')
    expected_dependency_counts = {
        'validate_source_request:SAVED_ACTUAL_PROJECTION_NO_CURRENT_OR_NATIVE_REVALIDATION':3,
        'source_origin:SAVED_ROOT_ORIGIN_PROOF_NO_GIT_OR_CURRENT_SOURCE_READ':3,
        'actual_predecessor:SAVED_ROOT_PREDECESSOR_REF_NO_H_HISTORY_REVALIDATION':3,
        'boot_id:SAVED_READBACK_BOOT_NO_PROC_READ':2,
        'binder_write:MEMORY_ONLY_NO_ROOT_FILE_CREATED':1,
    }
    check({name:dependencies.count(name) for name in set(dependencies)} == expected_dependency_counts, 'unexpected_dependency_seam_usage')
    trace_result = dict(
        state='PASS_SAVED_METADATA_ONLY_JOIN_BINDER_ACTOR_LOADER_SOURCE_PROBE',
        metadata=ref(metadata), saved_request=ref(R1/'ROOT-FRESH-REQUEST.json'),
        saved_acceptance=ref(R1/'ROOT-209-SOURCE-ACCEPTANCE.json'),
        saved_readback=ref(R1/'ROOT-209-FRESH-READBACK.json'),
        saved_boundary=ref(R1/'FUTURE-EXECUTION/CORE209-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json'),
        saved_time_seconds=saved_now, current_time_or_boot_read=False,
        actual_current_or_runtime_or_admission_credit=False,
        R2_output_binding='UNBOUND', Root_verdict_files_created=0,
        direct_join_equals_memory_binder_equals_actor_loader=True,
        sized_refs_per_entry=4, sized_read_total=len(sized_trace),
        strict_reference_reads=trace, dependency_seams=expected_dependency_counts)
    matrix_ref = dump('SAVED-SHAPE-CALLSITE-MATRIX.json', dict(
        state='SAVED_GENUINE_ROOT_METADATA_SOURCE_SHAPES_AUDITED',
        R2_output_binding='UNBOUND', runtime_or_admission_credit=False,
        documents=matrix, gate_summary=ref(S/'GATES-SUMMARY.json'),
        defect=dict(producer='GATES-SUMMARY.json runs[operational-success|operational-rollback].result|process_record',
                    genuine_shape=['bytes','path','sha256'], R1_consumer='root209_metadata.py:314 readref(row[result]); readref(row[process_record])',
                    R1_reader_contract=['path','sha256'], affected_saved_references=4),
        exact_callsite_matrix=[
            dict(entry='validate_join', boundary='read_sized_source_ref', slots=['runs[kind].result','runs[kind].process_record'], loop_kinds=['operational-success','operational-rollback'], consumed=4),
            dict(entry='main binder', boundary='validate_join then strict2 payload refs', source='same unchanged function body', probe='memory-only output'),
            dict(entry='load_actor_binding', boundary='validate_join then strict2 saved request/source_acceptance/fresh_readback refs', source='same unchanged function body'),
            dict(entry='validate_source_request', boundary='strict2 request pins / clean_reference for historical provenance', source='actual saved successful R1 caller projection reused; no H revalidation'),
            dict(entry='source/current/native IO', boundary='explicit saved dependency seams', source='not executed')],
        additional_discoverable_saved_shape_mismatches=[]))
    control_ref = dump('FOCUSED-CONTROLS.json', dict(state='PASS', controls=results, controls_count=len(results), source_reader_ast_unchanged=True, sized_callsite_count=2, sized_consumer_count_per_join=4))
    probe_ref = dump('SAVED-METADATA-PROBE.json', trace_result)
    return dict(state='PASS_SOURCE_ONLY_GENUINE_SAVED_SHAPE_CONTROLS',
                assignment='ASTRA-NATIVE-CORE209-R2-SAVED-SHAPE-AUDIT-20261113#1',
                result_kind='source-only', metadata=ref(metadata), script=ref(Path(__file__).resolve()),
                matrix=matrix_ref, focused_controls=control_ref, connected_saved_probe=probe_ref,
                additional_saved_shape_mismatches=[], R2_output_binding='UNBOUND',
                actual_current_or_native_or_install_or_admission_or_user_acceptance=False,
                original_R1_untouched=True, source_gates_reexecuted=False,
                checked_boundary='exact four genuine sized gate refs; all surrounding references retain strict2',
                limitations=['Historical source/current/native validations use explicit exact saved metadata seams; no fresh revalidation or current admission credit.',
                             'Binder output is captured in memory solely to check source shape; no bound Root artifact is created.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    result = controls(args.metadata)
    destination = dump('RESULT.json', result)
    print(json.dumps(dict(state=result['state'], result=destination),sort_keys=True))
