"""Pure F04 post-App assessment seam; explicit bytes only, no filesystem provider.

Unchanged pinned Source83 qualifies the genuine original returned XLSX first.
Its exact destination-check AST is reused against a RAM-only C2=3 projection.
No expected workbook or edited ODS is created. Runtime and custody stay external.
"""
import ast
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import json
import re
import types

SOURCE83_SHA = '87e2a8e37e6a28e63d09f148e997a55783875d528efa7a4e09e4409e626d336c'
SOURCE_SHA = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
AUTHORITY_SHA = 'f805315c82d40bb220b52dbe709063c2dbfc08b5c5a746bf0daae0916c9c9497'
INDEPENDENT_FACT_SHA = '530cb69a8421d6e6ca8fed6bfff94cb07b077f0806812ca883332bb975d373da'
DELTA = {'kind': 'additional_independent_numeric_plus_one', 'sheet_index': 1,
         'cell': 'C2', 'before': '2', 'after': '3', 'addend': '1'}
APP_PIN_KEYS = {'saved_sha256', 'ordinary_request_sha256', 'independent_fact_sha256',
                'delta_sha256', 'conversion_assessment_sha256'}
FALSE_CLAIMS = {'authority_verified': False, 'custody_verified': False,
                'oracle_independence_verified': False, 'runtime_verified': False,
                'installed_version_verified': False, 'ordinary_delivery_verified': False,
                'nonreplay_verified': False, 'new_effect_authorized': False,
                'conversion_runtime_verified': False, 'app_acceptance': False,
                'user_acceptance': False, 'f04_acceptance': False,
                'whole_conversion_pass': False}


class SavedAssessmentError(ValueError):
    pass


def need(value, code):
    if not value:
        raise SavedAssessmentError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _json(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 1000000, 'INDEPENDENT_FACT_SIZE')
    def pairs(items):
        need(len(dict(items)) == len(items), 'INDEPENDENT_FACT_DUPLICATE_KEY')
        return dict(items)
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda unused: need(False, 'INDEPENDENT_FACT_NONFINITE'))


def _source83(code):
    need(type(code) is bytes and sha(code) == SOURCE83_SHA, 'SOURCE83_PIN')
    module = types.ModuleType('_pinned_pure_source83')
    # The exact pinned Source83 contains imports/constants/pure definitions only.
    # Its legacy library loader separately extracts only approved pure defs.
    tree = ast.parse(code)
    need(all(isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign,
                           ast.ClassDef, ast.FunctionDef, ast.Expr)) for n in tree.body),
         'SOURCE83_PURE_MODULE')
    exec(compile(tree, '<pinned-pure-source83>', 'exec'), module.__dict__)
    checks = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_check']
    need(len(checks) == 1, 'SOURCE83_CHECK_DEFINITION')
    starts = [i for i, n in enumerate(checks[0].body)
              if isinstance(n, ast.Assign) and len(n.targets) == 1
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'roots']
    need(len(starts) == 1 and isinstance(checks[0].body[-1], ast.Return),
         'SOURCE83_DESTINATION_BLOCK')
    # Reuse every destination guard and rich comparison, unchanged. Only the
    # already-validated semantic object and independent values are substituted.
    function = ast.parse('def _saved_destination(*, returned_xlsx_bytes, helper, received, '
                         'library, raw, source, authority, values, semantic, pins, projection): pass').body[0]
    function.body = deepcopy(checks[0].body[starts[0]:])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 '<pinned-source83-destination-only>', 'exec'), module.__dict__)
    return module


def _entry_values(m, entries):
    need(type(entries) is list and len(entries) == 5, 'INDEPENDENT_CACHE_COUNT')
    result = {}
    for entry in entries:
        need(type(entry) is dict and {'sheet_index', 'cell', 'value'} <= set(entry)
             and type(entry['sheet_index']) is int and type(entry['cell']) is str,
             'INDEPENDENT_CACHE_SCHEMA')
        key = (entry['sheet_index'] - 1, entry['cell'])
        need(key not in result, 'INDEPENDENT_CACHE_DUPLICATE')
        result[key] = m._number(entry['value'])
    return result


def _expected(m, source, fact):
    need(type(fact) is dict and fact.get('schema') ==
         'friday.Root.F03.independent-numeric-oracle-precommit.v1', 'INDEPENDENT_FACT_SCHEMA')
    need(fact['source']['sha256'] == SOURCE_SHA, 'INDEPENDENT_FACT_SOURCE')
    # This old commitment's original->plus1 expectation is reused for arithmetic
    # only. It is not the F04 ordinary conversion request or an edit observation.
    need(canonical(fact['ordinary_requested_delta']) == canonical(
         {'sheet': 'Orders', 'cell': 'C2', 'expected': '2', 'value': '3'}),
         'INDEPENDENT_FACT_ORIGINAL_PLUS_ONE')
    need(source['sheets'][0]['cells']['C2']['kind'] == 'number'
         and source['sheets'][0]['cells']['C2']['value'] == Decimal('2'), 'ORIGINAL_C2_CAS')
    original_values = m._values(source)
    need(_entry_values(m, fact['source_numeric_formula_semantics']) == original_values,
         'INDEPENDENT_ORIGINAL_ARITHMETIC')
    expected = deepcopy(source)
    expected['sheets'][0]['cells']['C2']['value'] = Decimal('3')
    values = m._values(expected)
    need(_entry_values(m, fact['ordinary_numeric_formula_semantics_if_requested_edit_exact']) == values,
         'INDEPENDENT_SAVED_ARITHMETIC')
    return expected, values


def _cache_state(counts):
    need(type(counts) is dict and counts['sheets'] == 3 and counts['populated_cells'] == 40
         and counts['formula_cells'] == 5 and counts['text_ids'] == 4,
         'SAVED_FIXED_PROFILE_COUNTS')
    need(type(counts['missing_formula_caches']) is int and counts['missing_formula_caches'] == 0,
         'SAVED_FIVE_NUMERIC_CACHES_REQUIRED')
    missing = counts['missing_chart_cache_components']
    need(type(missing) is int and 0 <= missing <= 3, 'SAVED_CHART_CACHE_GAP_COUNT')
    complete = missing == 0
    return ('SAVED_SELECTED_BYTES_AND_ALL_CACHES_MATCH' if complete else
            'SAVED_REQUIRED_FORMULA_CACHES_MATCH_WITH_CHART_GAPS'), complete


def _check(*, source83_code, libraries, source_ods_bytes, received_xlsx_bytes,
           saved_xlsx_bytes, authority_xlsx_bytes, request, projection, oracle,
           conversion_pins, ordinary_request_bytes, independent_fact_bytes, delta, app_pins):
    need(type(app_pins) is dict and set(app_pins) == APP_PIN_KEYS
         and all(type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v)
                 for v in app_pins.values()), 'APP_PIN_SCHEMA')
    for name, data in [('saved', saved_xlsx_bytes), ('ordinary_request', ordinary_request_bytes),
                       ('independent_fact', independent_fact_bytes)]:
        need(type(data) is bytes and 0 < len(data) <= 2 * 1024**2
             and sha(data) == app_pins[name + '_sha256'], 'APP_INPUT_PIN')
    need(canonical(delta) == canonical(DELTA) and sha(canonical(delta)) == app_pins['delta_sha256'],
         'APP_DELTA')
    need(type(source_ods_bytes) is bytes and len(source_ods_bytes) == 16538
         and sha(source_ods_bytes) == SOURCE_SHA
         and type(authority_xlsx_bytes) is bytes and sha(authority_xlsx_bytes) == AUTHORITY_SHA,
         'SELECTED_ORIGINAL_PINS')
    need(sha(independent_fact_bytes) == INDEPENDENT_FACT_SHA, 'ORIGINAL_PRECOMMIT_PIN')
    need(saved_xlsx_bytes != received_xlsx_bytes, 'SAVED_UNCHANGED')
    m = _source83(source83_code)
    qualified = m.assess_conversion(source_ods_bytes=source_ods_bytes,
        returned_xlsx_bytes=received_xlsx_bytes, authority_xlsx_bytes=authority_xlsx_bytes,
        request=request, projection=projection, oracle=oracle, pins=conversion_pins, libraries=libraries)
    need(qualified.get('state') in ('SELECTED_REQUIRED_BYTES_MATCH_SOURCE_PROJECTION',
                                   'SELECTED_STRUCTURE_MATCH_WITH_CACHE_GAPS'),
         'GENUINE_RECEIVED_STRUCTURE_REFUSED')
    need(sha(canonical(qualified)) == app_pins['conversion_assessment_sha256'],
         'CONVERSION_QUALIFICATION_PIN')
    helper, received, library, raw, source, authority, unused, unused_delta, semantic = m._source_profile(
        source_ods_bytes, authority_xlsx_bytes, libraries)
    validation = helper._validations(source, library)
    need(validation[2] <= Decimal('3') <= validation[3], 'SAVED_C2_VALIDATION')
    expected, values = _expected(m, source, _json(independent_fact_bytes))
    # Projection is semantic RAM data only; no ODS/XLSX is serialized or written.
    changed_semantic = deepcopy(semantic)
    changed_semantic['cells'] = m._cell_projection(expected)
    changed_semantic['formula_values'] = m._cache_entries(values)
    semantic_sha = sha(canonical(changed_semantic))
    observed = m._saved_destination(returned_xlsx_bytes=saved_xlsx_bytes,
        helper=helper, received=received, library=library, raw=raw, source=expected,
        authority=authority, values=values, semantic=changed_semantic,
        pins=conversion_pins, projection={'semantic_projection_sha256': semantic_sha})
    counts = observed['counts']
    state, complete = _cache_state(counts)
    return {'schema': 'friday.F04.received-saved-xlsx.selected-byte-assessment.v1',
            'state': state,
            'scope': 'pure_saved_bytes_original_literal_precommit_plus_RAM_delta',
            **FALSE_CLAIMS, 'source83_sha256': SOURCE83_SHA,
            'library_pins': observed['library_pins'], 'conversion_pins': dict(conversion_pins),
            'app_pins': dict(app_pins), 'semantic_projection_sha256': semantic_sha,
            'expected_formula_values_sha256': sha(canonical(m._cache_entries(values))),
            'counts': dict(counts), 'fidelity_history': dict(m.HISTORY),
            'received_qualification_state': qualified['state'],
            'received_cache_gaps': {k: qualified['counts'][k] for k in
                ('missing_formula_caches', 'missing_chart_cache_components')},
            'source_hidden_mode_sha256': observed['source_hidden_mode_sha256'],
            'all_selected_caches_complete': complete, 'external_joins': 'UNBOUND',
            'limitations': ['no_runtime_custody_once_cleanup_or_formal_acceptance',
                'five_formula_caches_required_and_checked_independently',
                'present_chart_points_checked_chart_gaps_explicit_not_full_cache_match',
                'four_losses_four_unassessed_nineteen_dimensions_not_restored',
                'no_expected_or_received_workbook_generated']}


def assess_saved_xlsx(**inputs):
    """Return only fixed codes/counts/digests; never formulas, text or values."""
    try:
        with localcontext() as context:
            context.prec = 512
            return _check(**inputs)
    except SavedAssessmentError as error:
        code = str(error)
    except Exception as error:
        # Only Source83's already fixed codes may cross this boundary.
        code = error.code if type(error).__name__ == 'AssessmentError' and hasattr(error, 'code') else 'BOUNDED_PARSER_OR_SCHEMA'
    return {'schema': 'friday.F04.received-saved-xlsx.selected-byte-assessment.v1',
            'state': 'REFUSED', 'code': code, **FALSE_CLAIMS}
