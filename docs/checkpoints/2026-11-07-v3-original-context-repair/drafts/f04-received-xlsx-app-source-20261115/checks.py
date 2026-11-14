"""Finite source-only controls: no workbook bodies, execute/main, Office or grant."""
import ast
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
SOURCE83 = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/ods-xlsx-required-formulas-assessment-source83-20261114/ods_xlsx_assessor.py')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out
m = module('f04_driver_controls', ROOT / 'run_once.py')
a = module('f04_pure_saved_controls', ROOT / 'saved_xlsx_assessor.py')
checks = []
def require(value):
    assert value

def ok(name, fn):
    fn()
    checks.append({'name': name, 'passed': True})

def refuses(name, fn, code):
    try:
        fn()
    except ValueError as error:
        assert str(error) == code, (name, str(error), code)
        checks.append({'name': name, 'passed': True, 'fixed_code': code})
        return
    raise AssertionError('not refused: ' + name)

ok('syntax_compile_no_execution', lambda: [compile(p.read_bytes(), str(p), 'exec') for p in ROOT.glob('*.py')])
refuses('default_UNBOUND_before_input_toolchain_subprocess_slot_workdir', m.check_only, 'UNBOUND')
ok('no_reserved_operation_or_actual_grant', lambda: require(not os.path.lexists(m.WORK) and not (ROOT / 'ROOT-GRANT.json').exists()))
base = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-RECEIVED-COPY-APP-ENTRY-PREP-20261114')
ok('unchanged_helper_reused_exactly', lambda: require((ROOT / 'profile_helper.py').read_bytes() == (base / 'profile_helper.py').read_bytes()))
for name in ('profile-proof-script.xlc', 'profile-proof-Standard-script.xlb'):
    ok('unchanged_' + name, lambda name=name: require((ROOT / name).read_bytes() == (base / name).read_bytes()))
# Entirely synthetic metadata constructors. No workbook/expected artifact exists.
def pin(path, digest, inode, size=20):
    return {'path': str(path), 'bytes': size, 'sha256': digest,
        'identity': {'dev': 1, 'ino': inode, 'mode': stat.S_IFREG | 0o600,
            'uid': os.getuid(), 'gid': os.getgid(), 'nlink': 1, 'size': size,
            'mtime_ns': 1, 'ctime_ns': 1}}
def ref(name):
    return {'path': '/SYNTHETIC-METADATA-NOT-AN-ARTIFACT/' + name,
            'bytes': 20, 'sha256': 'd' * 64}
b = {'schema': 'friday.Root.F04.received-xlsx-input.v1',
    'state': 'ROOT_BOUND_FUTURE_RECEIVED_COPY_ONCE', 'assignment': m.ASSIGNMENT,
    'source': pin(m.SOURCE, m.SOURCE_SHA, 1, 16538),
    'received': pin('/FUTURE-ROOT-ONLY-NOT-CREATED/genuine.xlsx', 'b' * 64, 2),
    'ordinary_request': ref('ordinary-request'), 'ordinary_request_sha256': 'd' * 64,
    'delta': copy.deepcopy(m.DELTA),
    'conversion_assessment': {'receipt': ref('qualified'),
        'state': 'SELECTED_STRUCTURE_MATCH_WITH_CACHE_GAPS', 'assessor_sha256': m.SOURCE83_SHA,
        'source_sha256': m.SOURCE_SHA, 'received_sha256': 'b' * 64, 'request_sha256': 'c' * 64},
    'custody': ref('custody'), 'phase_authority': ref('authority'), 'installed_current': ref('current')}
ok('binding_schema_roundtrip_metadata_only', lambda: require(m.validate_binding(json.loads(json.dumps(b))) == b))
full = copy.deepcopy(b); full['conversion_assessment']['state'] = 'SELECTED_REQUIRED_BYTES_MATCH_SOURCE_PROJECTION'
ok('full_source83_qualification_accepted_as_schema_only', lambda: m.validate_binding(full))
def bad(name, path, value, code):
    changed = copy.deepcopy(b); here = changed
    for key in path[:-1]:
        here = here[key]
    here[path[-1]] = value
    refuses(name, lambda: m.validate_binding(changed), code)
bad('old_F03_edit_status_never_conversion_status', ['conversion_assessment', 'state'], 'EDIT_BYTES_MATCH', 'CONVERSION_QUALIFICATION')
bad('wrong_Source83_code_pin', ['conversion_assessment', 'assessor_sha256'], '0' * 64, 'CONVERSION_QUALIFICATION')
bad('wrong_received_conversion_join', ['conversion_assessment', 'received_sha256'], 'a' * 64, 'CONVERSION_QUALIFICATION')
bad('ordinary_request_raw_pin_is_separate', ['ordinary_request_sha256'], 'c' * 64, 'ORDINARY_REQUEST_PIN')
bad('original_source_cannot_be_returned', ['received', 'sha256'], m.SOURCE_SHA, 'NOT_FUTURE_RECEIVED')
bad('old_F03_App_output_path_rejected', ['received', 'path'], str(base / 'operation/controlledcopy-saved.ods'), 'NOT_FUTURE_RECEIVED')
bad('old_closed_App_digest_rejected', ['received', 'sha256'], next(iter(m.OLD_OUTPUTS)), 'NOT_FUTURE_RECEIVED')
bad('old_C2_3_to_4_delta_rejected', ['delta', 'before'], '3', 'DELTA')
bad('bool_does_not_equal_integer_delta', ['delta', 'sheet_index'], True, 'DELTA')
bad('private_expected_cache_payload_rejected', ['oracle'], {'anything': 1}, 'BINDING_SCHEMA')
bad('source_path_fixed_existing_Root_selected', ['source', 'path'], '/invented/new-source.ods', 'WRONG_SOURCE')
received = b['received']; staged = copy.deepcopy(received)
staged.update(path=str(m.WORK / 'received-copy.xlsx')); staged['identity']['ino'] = 3
ok('copy_pin_distinct_inode_and_equal_bytes', lambda: m.validate_copy(staged, received))
wrong = copy.deepcopy(staged); wrong['identity']['ino'] = received['identity']['ino']
refuses('same_inode_copy_rejected', lambda: m.validate_copy(wrong, received), 'COPY_BYTES_IDENTITY')
saved = pin(m.WORK / 'controlledcopy-saved.xlsx', 'e' * 64, 4)
ok('same_exact_saved_file_pin_reopen_join', lambda: m.validate_saved(saved, copy.deepcopy(saved)))
wrong = copy.deepcopy(saved); wrong['identity']['ctime_ns'] += 1
refuses('changed_saved_identity_rejected', lambda: m.validate_saved(saved, wrong), 'SAVED_PRE_POST_REOPEN_CAS')
ok('fresh_unit_clock_App300_work270_cleanup30', lambda: require(m.validate_clock(10, 12) == (280, 310)))
refuses('stale_unit_not_new_clock', lambda: m.validate_clock(10, 25), 'FRESH_UNIT_START')
macro = (ROOT / 'calc.bas').read_text()
ok('XLSX_macro_only_fixed_filter_and_paths', lambda: require('.ods' not in macro and '"calc8"' not in macro and macro.count('Calc MS Excel 2007 XML') == 4))
ok('one_controlled_change_recalc_save_Main_source', lambda: require(macro.count('activeDoc.calculateAll()') == 1 and macro.count('activeDoc.storeAsURL(') == 1 and macro.count('\n ProcessReceivedCopy\n') == 1 and 'If cell.getValue() <> 2 Then Guard 8114' in macro and 'cell.getValue() <> 3 Then Guard 8115' in macro))
ok('document_macros_updates_disabled_and_readonly_guard_retained', lambda: require('props(2).Value = 0' in macro and 'props(3).Value = 0' in macro and 'activeDoc.isReadonly() <> readonlyFlag' in macro))
ok('closed_pending_receipt_before_visibility_and_retained_gates', lambda: require(macro.index('WriteReceipt "saved-closed.pending"') < macro.index('sfa.move(ConvertToURL("/work/saved-closed.pending"')))
cmd = m.command('macro:///Standard.Module1.Main')
ok('only_disposable_workdir_mounted_no_source_or_canonical_received', lambda: require(str(m.WORK) in cmd and str(m.SOURCE) not in cmd and b['received']['path'] not in cmd and '--unshare-all' in cmd))
refuses('no_second_arbitrary_phase_command', lambda: m.command('macro:///Other.Main'), 'FIXED_PHASE')
# Synthetic TSV records exercise the changed producer/consumer seam only.
facts = {':BEGIN': 'RECEIVED_DISPOSABLE_COPY_NOT_ORDINARY_OR_USER_DELIVERY'}
for prefix in ('RECEIVED_COPY_BASELINE', 'CONTROLLED_COPY_BEFORE_SAVE', 'CONTROLLED_COPY_READONLY_REOPENED'):
    facts[prefix + ':SHEET_COUNT'] = '3'
    for index in range(3):
        facts[prefix + ':SHEET_NAME:' + str(index)] = 'SYNTHETIC-' + str(index)
    cells = [('0:A' + str(r), 2) for r in range(2, 6)]
    cells += [('0:' + c + str(r), 1) for r in range(2, 6) for c in ('C', 'D')]
    cells += [('0:G' + str(r), 3) for r in range(2, 6)] + [('1:B2', 3)]
    for cell, kind in cells:
        facts[prefix + ':CELL_TYPE:' + cell] = str(kind)
        facts[prefix + ':CELL_ERROR:' + cell] = '0'
        facts[prefix + (':CELL_TEXT:' if kind == 2 else ':CELL_VALUE_CSTR:') + cell] = 'SYNTHETIC' if kind == 2 else '1'
        if kind == 3:
            facts[prefix + ':CELL_FORMULA:' + cell] = '=1'
    if prefix != 'CONTROLLED_COPY_BEFORE_SAVE':
        facts[prefix + ':READ_ONLY'] = 'False' if prefix == 'RECEIVED_COPY_BASELINE' else 'True'
        for sheet in range(3):
            for col in range(1, 8):
                for prop, value in [('WIDTH', '100'), ('OPTIMAL_WIDTH', 'False'), ('COLUMN_VISIBLE', 'True')]:
                    facts[prefix + ':' + prop + ':' + str(sheet) + ':' + str(col)] = value
facts['CONTROLLED_COPY_READONLY_REOPENED:COUNTS'] = m.EXPECTED_COUNTS
facts['CONTROLLED_COPY_READONLY_REOPENED:COMPLETE'] = 'RECEIVED_COPY_SAVED_CLOSED_REOPENED'
def tsv(rows):
    return ''.join(k + '\t' + v + '\n' for k, v in rows).encode()
observations = tsv(facts.items())
sequence = [('OPEN_INTENT', '/work/received-copy.xlsx'), ('OPENED', '/work/received-copy.xlsx'),
    ('CHANGE_INTENT', 'FIRST_SHEET:C2:2:PLUS_ONE:3'), ('CHANGED', 'FIRST_SHEET:C2:2:PLUS_ONE:3'),
    ('CALCULATE_ALL_INTENT', 'RECEIVED_COPY'), ('CALCULATED_ALL', 'RECEIVED_COPY'),
    ('SAVE_INTENT', 'controlledcopy-saved.xlsx'), ('SAVED', 'controlledcopy-saved.xlsx'),
    ('CLOSE_INTENT', 'controlledcopy-saved.xlsx'), ('CLOSED', 'controlledcopy-saved.xlsx'),
    ('OPEN_INTENT', '/work/controlledcopy-saved.xlsx'), ('OPENED', '/work/controlledcopy-saved.xlsx'),
    ('CLOSE_INTENT', 'controlledcopy-saved.xlsx'), ('CLOSED', 'controlledcopy-saved.xlsx'),
    ('COMPLETE', m.EXPECTED_COUNTS)]
journal = tsv(sequence); complete = b'COMPLETE\t1:2:1:2:1:1\n'
ok('XLSX_changed_capture_exact_15_journal_311_observation_records', lambda: require(m.validate_capture(journal, observations, complete)['observation_rows'] == 311))
refuses('old_ODS_journal_open_refused', lambda: m.validate_capture(journal.replace(b'.xlsx', b'.ods'), observations, complete), 'JOURNAL_SEQUENCE_COUNTERS')
refuses('old_C2_3_to_4_journal_refused', lambda: m.validate_capture(journal.replace(b'C2:2:PLUS_ONE:3', b'C2:3:PLUS_ONE:4'), observations, complete), 'JOURNAL_SEQUENCE_COUNTERS')
refuses('extra_open_journal_refused', lambda: m.validate_capture(journal + b'OPENED\t/work/extra.xlsx\n', observations, complete), 'JOURNAL_SEQUENCE_COUNTERS')
refuses('duplicate_capture_record_refused', lambda: m.validate_capture(journal, observations + b':BEGIN\tDUPLICATE\n', complete), 'OBSERVATION_DUPLICATE')
wrongfacts = dict(facts); del wrongfacts['RECEIVED_COPY_BASELINE:WIDTH:2:7']
refuses('missing_third_sheet_width_refused', lambda: m.validate_capture(journal, tsv(wrongfacts.items()), complete), 'OBSERVATION_WIDTH_VALUE')
wrongfacts = dict(facts); wrongfacts['CONTROLLED_COPY_READONLY_REOPENED:CELL_ERROR:1:B2'] = '502'
refuses('formula_error_in_capture_refused', lambda: m.validate_capture(journal, tsv(wrongfacts.items()), complete), 'OBSERVATION_PRIMITIVE')
wrongfacts = dict(facts); wrongfacts['CONTROLLED_COPY_READONLY_REOPENED:READ_ONLY'] = 'False'
refuses('nonreadonly_reopen_capture_refused', lambda: m.validate_capture(journal, tsv(wrongfacts.items()), complete), 'OBSERVATION_READONLY')
wrongfacts = dict(facts); wrongfacts['CONTROLLED_COPY_READONLY_REOPENED:WIDTH:2:7'] = '101'
ok('width_difference_stays_observed_false_no_physical_equivalence_claim', lambda: require(m.validate_capture(journal, tsv(wrongfacts.items()), complete)['same_interpreter_all3_AtoG_widths_equal'] is False))
# Exact-code AST reuse, no workbook or historical context is imported.
code = SOURCE83.read_bytes(); source83 = a._source83(code)
original_tree = ast.parse(code)
check = next(n for n in original_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_check')
start = next(i for i, n in enumerate(check.body) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'roots')
ok('Source83_exact_destination_AST_keeps_all_guard_comparisons', lambda: require(len(check.body[start:]) > 15 and {'_archive', '_xlsx_guard', '_xlsx_names', '_xlsx_filter', '_validation_xlsx', '_source_hidden', '_hidden_xlsx', '_chart_signature', '_chart_cache'} <= set(source83._saved_destination.__code__.co_names) and {'RETURNED_SHEET_NAMES_ORDER', 'RETURNED_POPULATED_LOCATIONS', 'RETURNED_CELL_TYPE', 'RETURNED_FORMULA_GRAPH', 'RETURNED_RAW_MULTIPLICATION', 'RETURNED_RAW_SUMMARY', 'RETURNED_FORMULA_CACHE_INDEPENDENT_SOURCE_SEMANTICS', 'RETURNED_LITERAL_OR_ID', 'RETURNED_MERGES'} <= set(source83._saved_destination.__code__.co_consts)))
refuses('unpinned_Source83_rejected_before_compile', lambda: a._source83(code + b'\n'), 'SOURCE83_PIN')
# Generic RAM-only semantic unit stubs, never archives or received evidence.
source = {'sheets': [{'cells': {}}, {'cells': {'B2': {'kind': 'formula', 'formula': 'SUM(S0!G2:G5)'}}}]}
for row in range(2, 6):
    for col, number in [('C', '2' if row == 2 else '1'), ('D', '2')]:
        source['sheets'][0]['cells'][col + str(row)] = {'kind': 'number', 'value': Decimal(number)}
    source['sheets'][0]['cells']['G' + str(row)] = {'kind': 'formula', 'formula': f'C{row}*D{row}'}
expected = copy.deepcopy(source); expected['sheets'][0]['cells']['C2']['value'] = Decimal('3')
fact = {'schema': 'friday.Root.F03.independent-numeric-oracle-precommit.v1',
        'source': {'sha256': a.SOURCE_SHA}, 'ordinary_requested_delta': {'sheet': 'Orders', 'cell': 'C2', 'expected': '2', 'value': '3'},
        'source_numeric_formula_semantics': source83._cache_entries(source83._values(source)),
        'ordinary_numeric_formula_semantics_if_requested_edit_exact': source83._cache_entries(source83._values(expected))}
ok('RAM_only_expected_C2_delta_independent_graph', lambda: require(a._expected(source83, source, fact)[1] == source83._values(expected) and source['sheets'][0]['cells']['C2']['value'] == Decimal('2')))
wrong = copy.deepcopy(fact); wrong['ordinary_numeric_formula_semantics_if_requested_edit_exact'][0]['value'] = '999'
refuses('wrong_independent_saved_arithmetic_rejected', lambda: a._expected(source83, source, wrong), 'INDEPENDENT_SAVED_ARITHMETIC')
wrong = copy.deepcopy(fact); wrong['source_numeric_formula_semantics'][0]['value'] = '999'
refuses('wrong_independent_original_arithmetic_rejected', lambda: a._expected(source83, source, wrong), 'INDEPENDENT_ORIGINAL_ARITHMETIC')
wrong = copy.deepcopy(source); wrong['sheets'][0]['cells']['C2']['value'] = Decimal('3')
refuses('RAM_original_C2_must_be_2', lambda: a._expected(source83, wrong, fact), 'ORIGINAL_C2_CAS')
entries = copy.deepcopy(fact['source_numeric_formula_semantics']); entries[1] = copy.deepcopy(entries[0])
refuses('independent_cache_duplicate_rejected', lambda: a._entry_values(source83, entries), 'INDEPENDENT_CACHE_DUPLICATE')
counts = {'sheets': 3, 'populated_cells': 40, 'formula_cells': 5, 'text_ids': 4,
          'missing_formula_caches': 0, 'missing_chart_cache_components': 0}
ok('five_formula_plus_three_chart_components_full_state', lambda: require(a._cache_state(counts) == ('SAVED_SELECTED_BYTES_AND_ALL_CACHES_MATCH', True)))
partial = dict(counts, missing_chart_cache_components=1)
ok('chart_gap_state_is_distinct_partial', lambda: require(a._cache_state(partial) == ('SAVED_REQUIRED_FORMULA_CACHES_MATCH_WITH_CHART_GAPS', False)))
refuses('one_missing_formula_cache_is_refused', lambda: a._cache_state(dict(counts, missing_formula_caches=1)), 'SAVED_FIVE_NUMERIC_CACHES_REQUIRED')
refuses('missing_populated_cell_is_refused', lambda: a._cache_state(dict(counts, populated_cells=39)), 'SAVED_FIXED_PROFILE_COUNTS')
refuses('wrong_text_ID_count_is_refused', lambda: a._cache_state(dict(counts, text_ids=3)), 'SAVED_FIXED_PROFILE_COUNTS')
refuses('bool_chart_count_refused', lambda: a._cache_state(dict(counts, missing_chart_cache_components=True)), 'SAVED_CHART_CACHE_GAP_COUNT')
refuses('duplicate_private_fact_key_refused', lambda: a._json(b'{"x":1,"x":2}'), 'INDEPENDENT_FACT_DUPLICATE_KEY')
ok('public_wrapper_fails_closed_no_private_error_text', lambda: require(a.assess_saved_xlsx()['code'] == 'BOUNDED_PARSER_OR_SCHEMA'))
refuses('default_UNBOUND_stays_unbound_after_controls', m.check_only, 'UNBOUND')
result = {'state': 'SOURCE_ONLY_CHANGED_DELTA_CONTROLS_PASSED', 'count': len(checks), 'checks': checks,
    'all_samples': 'SYNTHETIC_METADATA_OR_RAM_UNIT_STUBS_NOT_WORKBOOKS_NOT_RECEIVED_EVIDENCE',
    'workbook_bodies_read_or_generated': 0, 'execute_main_Office_UNO_service_slot_model_TG_calls': 0,
    'Basic_runtime_compiled': False, 'genuine_full_postassessment': 'UNBOUND',
    'independent_source_review': 'REQUIRED_SEPARATELY', 'at_moscow': datetime.now(timezone(timedelta(hours=3))).isoformat()}
(ROOT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
(ROOT / 'checks.json').chmod(0o600)
print(json.dumps({'state': result['state'], 'count': len(checks)}))
