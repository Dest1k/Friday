"""Pure, finite cell/cache assessment; no Office, paths, producer, or grant logic.

The caller supplies two explicit ODS byte strings, exact request and oracle,
the independently pinned received checker module, and old raw-cell helper
source bytes. This checks a disposable extra numeric +1 after an already
requested numeric +1. It does not authorize that operation or certify its
runtime, custody, rich structures, or the independence of the supplied oracle.
"""
import ast
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import stat
import xml.etree.ElementTree as ET
import zipfile

OLD_CHECKER_SHA256 = 'c272c984c90ce2b08a8f4589c361aa299cd461230896deab97e583e117456bf5'
_HELPERS = {'q', 'need', 'finite_decimal', 'positive_int', 'xml_bytes',
            'archive_bytes', 'text', 'coordinate', 'raw_cells'}
_HEX = re.compile(r'[0-9a-f]{64}')


class RecalcError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _need(value, code):
    if not value:
        raise RecalcError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _decimal(value):
    _need(type(value) is str and 0 < len(value) <= 128, 'NUMERIC_LEXICAL_BOUND')
    _need(re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?', value),
          'NUMERIC_LEXICAL')
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise RecalcError('NUMERIC_LEXICAL') from None
    _need(result.is_finite() and abs(result.adjusted()) <= 100,
          'NUMERIC_FINITE_BOUND')
    return result


def _keys(value, expected, code):
    _need(type(value) is dict and set(value) == set(expected), code)


def _raw_reader(source):
    """Reuse exact reviewed pure helpers without executing its module/context."""
    _need(type(source) is bytes and sha(source) == OLD_CHECKER_SHA256,
          'RAW_HELPER_PIN')
    tree = ast.parse(source)
    functions = [n for n in tree.body
                 if isinstance(n, ast.FunctionDef) and n.name in _HELPERS]
    _need({n.name for n in functions} == _HELPERS, 'RAW_HELPER_SET')
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and len(n.targets) == 1
                   and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id == 'NS']
    _need(len(assignments) == 1, 'RAW_HELPER_NAMESPACE')
    namespace = {'Decimal': Decimal, 'NS': ast.literal_eval(assignments[0].value),
                 'io': io, 'zipfile': zipfile, 'PurePosixPath': PurePosixPath,
                 're': re, 'stat': stat, 'ET': ET}
    selected = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    exec(compile(selected, '<pinned-reviewed-raw-cell-helpers>', 'exec'), namespace)
    return lambda data: namespace['raw_cells'](namespace['archive_bytes'](data, 'ods'))


def _row_profile(snapshot):
    """The retained raw reader supports direct rows, never nested row groups."""
    table = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
    row_tag = '{' + table + '}table-row'
    unsupported = {'{' + table + '}' + name for name in
                   ('table-row-group', 'table-header-rows', 'table-rows')}
    for sheet in snapshot.sheets:
        _need(not any(node.tag in unsupported for node in sheet.iter()),
              'NESTED_ROW_STRUCTURE_UNSUPPORTED')
        direct = {id(node) for node in sheet if node.tag == row_tag}
        _need(all(id(node) in direct for node in sheet.iter(row_tag)),
              'NESTED_ROW_STRUCTURE_UNSUPPORTED')


def _check(received, saved, request, oracle, binding, received_checker, old_source):
    _need(type(received) is bytes and type(saved) is bytes, 'EXPLICIT_BYTES_REQUIRED')
    _need(0 < len(received) <= 2_000_000 and 0 < len(saved) <= 2_000_000,
          'FINITE_ARCHIVE_BYTES')
    _keys(request, {'sheet', 'cell', 'expected', 'value'}, 'REQUEST_SCHEMA')
    _need(all(type(x) is str for x in request.values()), 'REQUEST_TYPES')
    _need(request['cell'] == 'C2', 'FINITE_TARGET_SCOPE')
    requested_old = _decimal(request['expected'])
    requested_new = _decimal(request['value'])
    _need(requested_new == requested_old + Decimal(1), 'ORDINARY_DELTA_NOT_PLUS_ONE')
    _keys(binding, {'received_sha256', 'saved_sha256', 'request_sha256',
                    'oracle_sha256', 'delta_sha256'}, 'BINDING_SCHEMA')
    _need(all(type(x) is str and _HEX.fullmatch(x) for x in binding.values()),
          'BINDING_HASH_FORMAT')
    request_hash = received_checker.request_sha256(request)
    _need(binding['received_sha256'] == sha(received), 'RECEIVED_HASH')
    _need(binding['saved_sha256'] == sha(saved), 'SAVED_HASH')
    _need(binding['request_sha256'] == request_hash, 'REQUEST_HASH')
    _need(binding['oracle_sha256'] == sha(canonical(oracle)), 'ORACLE_HASH')
    _keys(oracle, {'schema', 'received_sha256', 'request_sha256', 'delta',
                   'formula_caches_after'}, 'ORACLE_SCHEMA')
    _need(oracle['schema'] == 'friday.received-disposable-recalc.oracle.v1',
          'ORACLE_VERSION')
    _need(oracle['received_sha256'] == binding['received_sha256'] and
          oracle['request_sha256'] == request_hash, 'ORACLE_BASIS')
    delta = oracle['delta']
    _keys(delta, {'kind', 'sheet_index', 'cell', 'before', 'after', 'addend'},
          'DELTA_SCHEMA')
    _need(sha(canonical(delta)) == binding['delta_sha256'], 'DELTA_HASH')
    _need(delta['kind'] == 'additional_independent_numeric_plus_one' and
          type(delta['sheet_index']) is int and delta['sheet_index'] == 1 and
          delta['cell'] == request['cell'] and delta['addend'] == '1',
          'CONTROLLED_DELTA_SCOPE')
    before_literal = _decimal(delta['before'])
    after_literal = _decimal(delta['after'])
    _need(before_literal == requested_new and
          after_literal == before_literal + Decimal(1), 'CONTROLLED_DELTA_LINEAGE')
    # The current strict parser rejects active XML declarations/PI/encodings.
    # The retained parser then enforces its tighter expansion limits before
    # raw_cells expands any repeated meaningful cells. Never widen that seam.
    _row_profile(received_checker.inspect_ods(received))
    _row_profile(received_checker.inspect_ods(saved))
    read_cells = _raw_reader(old_source)
    before = read_cells(received)
    after = read_cells(saved)
    _need(before and before[0]['name'] == request['sheet'], 'REQUEST_SHEET')
    _need([s['name'] for s in before] == [s['name'] for s in after],
          'SHEET_NAMES_ORDER')
    target = before[0]['cells'].get('C2')
    _need(target is not None and target['formula'] is None and
          target['attrs'].get('value-type') == 'float' and
          target['attrs'].get('value') == before_literal,
          'RECEIVED_TARGET_CAS')
    entries = oracle['formula_caches_after']
    _need(type(entries) is list and 0 < len(entries) <= 1000, 'ORACLE_CACHE_BOUND')
    caches = {}
    for entry in entries:
        _keys(entry, {'sheet_index', 'cell', 'formula_sha256', 'value'},
              'ORACLE_CACHE_SCHEMA')
        index = entry['sheet_index']
        address = entry['cell']
        _need(type(index) is int and 1 <= index <= len(before) and
              type(address) is str and re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,3}', address),
              'ORACLE_CACHE_LOCATION')
        key = (index - 1, address)
        _need(key not in caches, 'ORACLE_CACHE_DUPLICATE')
        cell = before[index - 1]['cells'].get(address)
        _need(cell is not None and type(cell['formula']) is str and
              entry['formula_sha256'] == sha(cell['formula'].encode('utf-8')),
              'ORACLE_FORMULA_PIN')
        caches[key] = _decimal(entry['value'])
    formula_locations = {(i, address) for i, sheet in enumerate(before)
                         for address, cell in sheet['cells'].items()
                         if cell['formula'] is not None}
    _need(set(caches) == formula_locations, 'ORACLE_ALL_FORMULA_LOCATIONS')
    for index, (left, right) in enumerate(zip(before, after, strict=True)):
        _need(set(left['cells']) == set(right['cells']), 'POPULATED_CELL_LOCATIONS')
        for address, old in left['cells'].items():
            new = right['cells'][address]
            key = (index, address)
            expected = deepcopy(old)
            permitted_display = False
            if key == (0, 'C2'):
                expected['attrs']['value'] = after_literal
                permitted_display = True
            if key in caches:
                expected['attrs']['value'] = caches[key]
                expected['attrs']['value-type'] = 'float'
                permitted_display = True
            _need(old['formula'] == new['formula'], 'RAW_FORMULA_PRESERVATION')
            _need(expected['attrs'] == new['attrs'], 'CELL_TYPE_VALUE_SCOPE')
            _need(old['additional_data_attrs'] == new['additional_data_attrs'],
                  'ADDITIONAL_CELL_ATTRIBUTE_SCOPE')
            if permitted_display:
                _need(_decimal(new['text']) == expected['attrs']['value'],
                      'NUMERIC_DISPLAY_CACHE')
            else:
                _need(old['text'] == new['text'], 'NONTARGET_TEXT_SCOPE')
    return {
        'state': 'RECALC_CELL_BYTES_MATCH_EXPLICIT_ORACLE',
        'authority': False,
        'received_sha256': sha(received),
        'saved_sha256': sha(saved),
        'request_sha256': request_hash,
        'oracle_sha256': binding['oracle_sha256'],
        'delta_sha256': binding['delta_sha256'],
        'formula_cache_count': len(caches),
        'stale_received_caches_permitted': True,
        'ordinary_received_edit_join_required': True,
        'saved_rich_structure_join_required': True,
        'actual_runtime_save_close_reopen_cleanup_join_required': True,
        'independent_root_oracle_provenance_join_required': True,
    }


def assess_recalc(received, saved, request, oracle, binding, *,
                  received_checker, old_checker_source):
    """Return fixed codes and hashes only. Does not read or write any files."""
    try:
        with localcontext() as context:
            context.prec = 512
            return _check(received, saved, request, oracle, binding,
                          received_checker, old_checker_source)
    except RecalcError as error:
        return {'state': 'REFUSED', 'code': error.code, 'authority': False}
    except Exception:
        # Underlying parser errors may include source content; never relay them.
        return {'state': 'REFUSED', 'code': 'BOUNDED_PARSER_OR_SCHEMA',
                'authority': False}
