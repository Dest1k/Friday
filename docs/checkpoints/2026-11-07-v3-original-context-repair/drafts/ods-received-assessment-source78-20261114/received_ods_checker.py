"""Finite, pure assessment of an explicitly requested same-format ODS edit.

No file I/O, model/editor/runtime imports, effects, admission or authority checks.
A match means only that supplied bytes match the declared request and pins.
Every provenance, delivery, user acceptance and authorization claim stays false.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO
import json
import re
import stat
from xml.etree import ElementTree as ET
from xml.parsers import expat
import zipfile
import zlib

from preservation_helpers import (O, T, TB, D, q, CELL_TAGS, ROW_GROUPS,
                                  element_spans, rows, cells, coordinates,
                                  cellref, node_span)

MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 512
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 64 * 1024 * 1024
MAX_XML_ELEMENTS = 100000
MAX_XML_DEPTH = 128
MAX_LOGICAL_INDEX = 1000000
MAX_NUMERIC_CHARS = 512
MAX_NUMERIC_ADJUSTED_EXPONENT = 300
MAX_REQUEST_TEXT = 1024
CALCEXT = 'urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0'
MIMETYPE = b'application/vnd.oasis.opendocument.spreadsheet'
REQUEST_FIELDS = frozenset(('sheet', 'cell', 'expected', 'value'))
PIN_FIELDS = frozenset(('source_sha256', 'received_sha256', 'request_sha256'))
OPTIONAL_BINDING_FIELDS = frozenset(('source_custody_ref', 'received_custody_ref', 'operation_ref'))
AUTHORITY_FALSE = {
    'authority_verified': False,
    'source_custody_verified': False,
    'received_custody_verified': False,
    'installed_version_verified': False,
    'nonreplay_verified': False,
    'ordinary_delivery_or_user_acceptance': False,
    'new_effect_authorized': False,
}


class CheckError(ValueError):
    """A fixed public reason code; never contains workbook data."""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _require(condition, code):
    if not condition:
        raise CheckError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _request(request):
    _require(type(request) is dict and set(request) == REQUEST_FIELDS, 'REQUEST_FIELDS_INVALID')
    _require(all(type(v) is str and 0 < len(v) <= MAX_REQUEST_TEXT
                 for v in request.values()), 'REQUEST_TYPES_INVALID')
    _require(re.fullmatch(r'[A-Z]{1,5}[1-9][0-9]{0,6}', request['cell']) is not None,
             'CELL_REFERENCE_INVALID')
    row, col = coordinates(request['cell'])
    _require(row <= MAX_LOGICAL_INDEX and col <= MAX_LOGICAL_INDEX, 'CELL_REFERENCE_LIMIT')
    _number(request['expected'])
    _number(request['value'])
    return request


def request_sha256(request):
    _request(request)
    return sha(json.dumps(request, ensure_ascii=True, separators=(',', ':'),
                          sort_keys=True).encode('ascii'))


def _number(text):
    _require(type(text) is str and 0 < len(text) <= MAX_NUMERIC_CHARS,
             'NUMERIC_VALUE_INVALID')
    _require(re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?',
                         text) is not None, 'NUMERIC_VALUE_INVALID')
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise CheckError('NUMERIC_VALUE_INVALID') from None
    _require(value.is_finite(), 'NUMERIC_VALUE_INVALID')
    _require(abs(value.adjusted()) <= MAX_NUMERIC_ADJUSTED_EXPONENT,
             'NUMERIC_VALUE_LIMIT')
    return value


@dataclass
class ArchiveSnapshot:
    """Assessment-only parsed data; callers must never log roots or payloads."""
    payloads: dict
    roots: dict
    raw: bytes
    root: ET.Element
    body: ET.Element
    sheets: list


def _parse_xml(raw):
    _require(len(raw) <= MAX_MEMBER_BYTES, 'XML_BYTES_LIMIT')
    # Byte-span helpers require ASCII-compatible markup, never UTF-16/32.
    _require(b'\x00' not in raw, 'XML_ENCODING_UNSUPPORTED')
    parser = expat.ParserCreate(namespace_separator='}')
    depth = 0
    count = 0
    def start(name, attrs):
        nonlocal depth, count
        depth += 1
        count += 1
        _require(depth <= MAX_XML_DEPTH and count <= MAX_XML_ELEMENTS, 'XML_STRUCTURE_LIMIT')
    def end(name):
        nonlocal depth
        depth -= 1
    def disallow(*args):
        raise CheckError('XML_ACTIVE_DECLARATION')
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = disallow
    parser.EntityDeclHandler = disallow
    parser.ExternalEntityRefHandler = disallow
    parser.ProcessingInstructionHandler = disallow
    try:
        parser.Parse(raw, True)
        return ET.fromstring(raw)
    except CheckError:
        raise
    except (expat.ExpatError, ET.ParseError, ValueError):
        raise CheckError('XML_MALFORMED') from None


def inspect_ods(data):
    """Parse bounded ZIP/XML bytes only; never access paths or resolve links."""
    _require(type(data) is bytes, 'INPUT_BYTES_REQUIRED')
    _require(0 < len(data) <= MAX_ARCHIVE_BYTES, 'ARCHIVE_BYTES_LIMIT')
    payloads = {}
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            _require(0 < len(infos) <= MAX_MEMBERS, 'ZIP_MEMBER_LIMIT')
            _require(infos[0].filename == 'mimetype'
                     and infos[0].compress_type == zipfile.ZIP_STORED,
                     'ODS_MIMETYPE_STORAGE_INVALID')
            _require(sum(i.file_size for i in infos) <= MAX_EXPANDED_BYTES,
                     'ZIP_EXPANDED_LIMIT')
            for info in infos:
                name = info.filename
                _require(name not in payloads, 'ZIP_DUPLICATE_MEMBER')
                _require(name == info.orig_filename and name and not name.startswith('/') and ':' not in name and '\\' not in name
                         and all(p not in ('', '.', '..') for p in name.rstrip('/').split('/'))
                         and '\x00' not in name, 'ZIP_MEMBER_NAME_INVALID')
                _require(not info.flag_bits & 1, 'ZIP_ENCRYPTED_MEMBER')
                _require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                         'ZIP_COMPRESSION_UNSUPPORTED')
                _require(info.file_size <= MAX_MEMBER_BYTES, 'ZIP_MEMBER_BYTES_LIMIT')
                mode = info.external_attr >> 16
                _require(not stat.S_ISLNK(mode), 'ZIP_SYMLINK_MEMBER')
                with archive.open(info) as stream:
                    value = stream.read(MAX_MEMBER_BYTES + 1)
                    _require(len(value) == info.file_size and len(value) <= MAX_MEMBER_BYTES,
                             'ZIP_MEMBER_SIZE_MISMATCH')
                payloads[name] = value
    except CheckError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, RuntimeError, ValueError,
            NotImplementedError, EOFError, zlib.error):
        raise CheckError('ZIP_MALFORMED') from None
    _require(payloads.get('mimetype') == MIMETYPE, 'ODS_MIMETYPE_INVALID')
    _require('content.xml' in payloads, 'ODS_CONTENT_MISSING')
    roots = {name: _parse_xml(raw) for name, raw in payloads.items() if name.endswith('.xml')}
    root = roots['content.xml']
    _require(root.tag == q(O, 'document-content'), 'ODS_CONTENT_ROOT_INVALID')
    bodies = root.findall(q(O, 'body'))
    _require(len(bodies) == 1, 'ODS_BODY_AMBIGUOUS')
    spreadsheets = bodies[0].findall(q(O, 'spreadsheet'))
    _require(len(spreadsheets) == 1, 'ODS_SPREADSHEET_AMBIGUOUS')
    body = spreadsheets[0]
    sheets = body.findall(q(TB, 'table'))
    _require(0 < len(sheets) <= 256, 'ODS_SHEET_LIMIT')
    sheet_names = [sheet.get(q(TB, 'name')) for sheet in sheets]
    _require(all(type(n) is str and n for n in sheet_names)
             and len(set(sheet_names)) == len(sheet_names), 'ODS_SHEET_IDENTITY_AMBIGUOUS')
    # The reused iterator converts repetition counts to int, so constrain them first.
    for node in root.iter():
        for key in ('number-rows-repeated', 'number-columns-repeated'):
            repeat = node.get(q(TB, key))
            if repeat is not None:
                _require(re.fullmatch(r'[1-9][0-9]{0,6}', repeat) is not None
                         and int(repeat) <= MAX_LOGICAL_INDEX, 'ODS_REPETITION_LIMIT')
    return ArchiveSnapshot(payloads, roots, payloads['content.xml'], root, body, sheets)


def locate(snapshot, sheet, cell):
    """Select one explicit, non-repeated numeric cell from a parsed snapshot."""
    _require(type(sheet) is str and type(cell) is str, 'TARGET_TYPES_INVALID')
    try:
        row_index, col_index = coordinates(cell)
    except AssertionError:
        raise CheckError('CELL_REFERENCE_INVALID') from None
    matches = [s for s in snapshot.sheets if s.get(q(TB, 'name')) == sheet]
    _require(len(matches) == 1, 'TARGET_SHEET_MISSING')
    selected_sheet = matches[0]
    _require(selected_sheet.get(q(TB, 'protected'), 'false') == 'false', 'TARGET_SHEET_PROTECTED')
    found = [(height, width, node, row)
             for rr, cc, height, width, node, row in cells(selected_sheet)
             if rr <= row_index < rr + height and cc <= col_index < cc + width]
    _require(len(found) == 1, 'TARGET_CELL_MISSING_OR_AMBIGUOUS')
    height, width, node, row = found[0]
    _require(height == width == 1, 'TARGET_CELL_REPEATED')
    _require(node.tag == q(TB, 'table-cell') and q(TB, 'formula') not in node.attrib,
             'TARGET_NOT_LITERAL_NUMERIC')
    _require(not any(q(TB, key) in node.attrib for key in
                     ('number-columns-spanned', 'number-rows-spanned', 'protect', 'protected')),
             'TARGET_CELL_UNSUPPORTED')
    allowed = {q(O, 'value'), q(O, 'value-type'), q(CALCEXT, 'value-type'),
               q(TB, 'style-name'), q(TB, 'content-validation-name')}
    _require(set(node.attrib) <= allowed, 'TARGET_ATTRIBUTES_UNSUPPORTED')
    _require(node.get(q(O, 'value-type')) == 'float'
             and node.get(q(CALCEXT, 'value-type'), 'float') == 'float'
             and q(O, 'value') in node.attrib, 'TARGET_NUMERIC_TYPE_INVALID')
    _number(node.get(q(O, 'value')))
    _require(len(node) == 1 and node[0].tag == q(T, 'p') and len(node[0]) == 0,
             'TARGET_DISPLAY_STRUCTURE_UNSUPPORTED')
    _require(_number(node[0].text or '') == _number(node.get(q(O, 'value'))),
             'TARGET_DISPLAY_VALUE_MISMATCH')
    try:
        span = node_span(snapshot.raw, snapshot.root, node)
    except (AssertionError, ValueError, expat.ExpatError):
        raise CheckError('XML_SPAN_ALIGNMENT_INVALID') from None
    selected_raw = snapshot.raw[span['begin']:span['end']]
    _require(b'<!--' not in selected_raw and b'<?' not in selected_raw,
             'TARGET_MARKUP_UNSUPPORTED')
    return {'node': node, 'row': row, 'sheet': selected_sheet, 'span': span}


def _validation(snapshot, target, value):
    identity = target['node'].get(q(TB, 'content-validation-name'))
    if identity is None:
        return
    definitions = [n for n in snapshot.body.iter(q(TB, 'content-validation'))
                   if n.get(q(TB, 'name')) == identity]
    _require(len(definitions) == 1, 'TARGET_VALIDATION_IDENTITY_INVALID')
    expression = definitions[0].get(q(TB, 'condition'), '')
    match = re.fullmatch(r'of:cell-content-is-whole-number\(\) and cell-content-is-between\((-?[0-9]+),(-?[0-9]+)\)', expression)
    _require(match is not None, 'TARGET_VALIDATION_UNSUPPORTED')
    low, high = _number(match[1]), _number(match[2])
    _require(value == value.to_integral_value() and low <= value <= high,
             'TARGET_VALIDATION_VALUE_REJECTED')


def _bound(source, received, request, binding):
    _require(type(binding) is dict, 'BINDING_FIELDS_INVALID')
    _require(set(binding) <= PIN_FIELDS | OPTIONAL_BINDING_FIELDS, 'BINDING_FIELDS_INVALID')
    _require(PIN_FIELDS <= set(binding), 'BINDING_REQUIRED_PINS_MISSING')
    _require(all(type(binding[k]) is str and re.fullmatch(r'[0-9a-f]{64}', binding[k])
                 for k in PIN_FIELDS), 'BINDING_PIN_INVALID')
    _require(all(binding[k] is None or (type(binding[k]) is str and
                                      0 < len(binding[k]) <= MAX_REQUEST_TEXT)
                 for k in OPTIONAL_BINDING_FIELDS & set(binding)), 'BINDING_REFERENCE_INVALID')
    _require(binding['source_sha256'] == sha(source), 'SOURCE_SHA_MISMATCH')
    _require(binding['received_sha256'] == sha(received), 'RECEIVED_SHA_MISMATCH')
    _require(binding['request_sha256'] == request_sha256(request), 'REQUEST_SHA_MISMATCH')


def _facts(before, after, a, b):
    formulas = [n for n in before.root.iter() if n.tag in CELL_TAGS and q(TB, 'formula') in n.attrib]
    _require(formulas, 'SOURCE_FORMULA_INPUT_REQUIRED')
    structures = {key: sum(1 for _ in before.root.iter(tag)) for key, tag in {
        'validation_definitions': q(TB, 'content-validation'),
        'named_ranges': q(TB, 'named-range'), 'database_ranges': q(TB, 'database-range'),
        'filters': q(TB, 'filter'), 'covered_cells': q(TB, 'covered-table-cell'),
        'chart_objects': q(D, 'object')}.items()}
    structures['formula_cells'] = len(formulas)
    structures['validation_bindings'] = sum(q(TB, 'content-validation-name') in n.attrib
                                           for n in before.root.iter() if n.tag in CELL_TAGS)
    structures['hidden_rows'] = sum(n.get(q(TB, 'visibility'), 'visible') != 'visible'
                                    for n in before.root.iter(q(TB, 'table-row')))
    structures['merged_anchors'] = sum(any(q(TB, k) in n.attrib for k in
                                        ('number-columns-spanned', 'number-rows-spanned'))
                                      for n in before.root.iter() if n.tag in CELL_TAGS)
    return {'target_only_raw_change': True, 'noncontent_member_payloads_unchanged': True,
            'nontarget_xml_bytes_unchanged': True,
            'all_raw_formulas_types_text_ids_validation_chart_name_filter_merge_hidden_preserved': True,
            'target_attributes_except_numeric_value_unchanged': True,
            'target_display_metadata_preserved': True,
            'stored_formula_caches_preserved': True, 'caches_recalculated': False,
            'cache_status': 'preserved_not_recalculated', 'preserved_structure_counts': structures,
            'member_count': len(before.payloads)}


def assess_edit(source, received, request, binding):
    """Assess existing bytes, never synthesize an expected workbook or authority.

    binding pins are supplied claims checked against bytes, not verified custody.
    Optional custody/operation refs are opaque and cannot change the result scope.
    The output omits sheet names, cell values, formulas and supplied reference text.
    """
    result = {'schema': 'friday.ods.received-byte-assessment.v1',
              'scope': 'supplied_bytes_only', **AUTHORITY_FALSE,
              'external_root_joins': ['canonical_custody', 'ordinary_ingress', 'delivery',
                                      'installed_version', 'nonreplay', 'user_acceptance'],
              'external_root_joins_status': 'UNBOUND'}
    try:
        _require(type(source) is bytes and type(received) is bytes, 'INPUT_BYTES_REQUIRED')
        _require(0 < len(source) <= MAX_ARCHIVE_BYTES and 0 < len(received) <= MAX_ARCHIVE_BYTES,
                 'ARCHIVE_BYTES_LIMIT')
        _request(request)
        _bound(source, received, request, binding)
        result.update(source_sha256=sha(source), received_sha256=sha(received),
                      request_sha256=request_sha256(request), target_cell=request['cell'])
        before, after = inspect_ods(source), inspect_ods(received)
        a, b = locate(before, request['sheet'], request['cell']), locate(after, request['sheet'], request['cell'])
        _require(before.payloads.keys() == after.payloads.keys(), 'MEMBER_SET_CHANGED')
        _require(all(before.payloads[name] == after.payloads[name]
                     for name in before.payloads if name != 'content.xml'), 'NONCONTENT_PAYLOAD_CHANGED')
        sa, sb = a['span'], b['span']
        _require(before.raw[:sa['begin']] == after.raw[:sb['begin']]
                 and before.raw[sa['end']:] == after.raw[sb['end']:], 'NONTARGET_XML_BYTES_CHANGED')
        _require(before.raw[sa['begin']:sa['end']] != after.raw[sb['begin']:sb['end']],
                 'TARGET_RAW_UNCHANGED')
        old, new = a['node'], b['node']
        _require(old.get(q(O, 'value')) == request['expected'], 'EXPECTED_VALUE_CAS_MISMATCH')
        _require(_number(request['value']) != _number(request['expected']), 'REQUEST_NO_NUMERIC_CHANGE')
        _require(new.get(q(O, 'value')) == request['value'], 'REQUESTED_VALUE_MISMATCH')
        _require(new[0].text == request['value'], 'REQUESTED_DISPLAY_VALUE_MISMATCH')
        oldattrs, newattrs = dict(old.attrib), dict(new.attrib)
        oldattrs.pop(q(O, 'value')); newattrs.pop(q(O, 'value'))
        _require(oldattrs == newattrs, 'TARGET_IDENTITY_METADATA_CHANGED')
        _require(old.text == new.text and old.tail == new.tail
                 and old[0].attrib == new[0].attrib and old[0].tail == new[0].tail,
                 'TARGET_DISPLAY_METADATA_CHANGED')
        _validation(before, a, _number(request['value']))
        result.update(status='EDIT_BYTES_MATCH', code='EDIT_BYTES_MATCH',
                      facts=_facts(before, after, a, b))
    except CheckError as error:
        result.update(status='REFUSED', code=error.code)
    return result
