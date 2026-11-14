"""Pure selected-profile ODS to returned-XLSX byte assessment.

The caller supplies every byte and binding.  This module never opens paths,
creates workbooks, imports a product runtime, or establishes external authority.
Arithmetic expectations are derived from source literals in memory, independently
of destination formula/chart caches.  The parser is deliberately profile-limited.
"""
import ast
import collections
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import io
import json
from pathlib import PurePosixPath
import posixpath
import re
import stat
import types
import xml.etree.ElementTree as ET
import zipfile

ADAPTER_PIN = '5928488a83f9f3df3d5e7ba8313780e9234d32de025fc658faf560089aae0725'
LIBRARY_PINS = {
    'structures': '8cb35d60e20db4a34c37fd9be9a382c3230d10132d79481fae0a2de4ee35c4c6',
    'strict': 'c272c984c90ce2b08a8f4589c361aa299cd461230896deab97e583e117456bf5',
    'received': '5a0f297aad09ef3e5aabad8fb3cccc03f20514863b3680b663e9178570e23bab',
    'preservation': '8b6241e2749f68005faa01b344ec6fe4747da927382269de2d4b796ac66a1e07',
    'recalc': '679cc90c2f14150f011a0330f5f96ef23de48912ed5b738d49a2a43b074e254f',
    'adapter': ADAPTER_PIN,
}
PROFILE = 'selected-original-three-sheet-rich-required-formulas.v1'
REL_BASE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
PACKAGE_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
FALSE_CLAIMS = {
    'authority_verified': False, 'custody_verified': False,
    'oracle_independence_verified': False, 'runtime_verified': False,
    'installed_version_verified': False, 'ordinary_delivery_verified': False,
    'nonreplay_verified': False, 'new_effect_authorized': False,
    'conversion_runtime_verified': False, 'app_acceptance': False,
    'user_acceptance': False, 'f04_acceptance': False,
    'whole_conversion_pass': False,
}
PIN_KEYS = {'source_sha256', 'returned_sha256', 'authority_sha256',
            'request_sha256', 'projection_sha256', 'oracle_sha256'}
REQUEST_KEYS = {'schema', 'profile', 'direction', 'source_sha256',
                'authority_sha256', 'source_numeric_delta', 'fidelity_history'}
PROJECTION_KEYS = {'schema', 'profile', 'source_sha256', 'authority_sha256',
                   'request_sha256', 'oracle_sha256', 'semantic_projection_sha256'}
ORACLE_KEYS = {'schema', 'method', 'source_sha256', 'formula_values',
               'independence_verified'}
HISTORY = {'known_cross_format_losses': 4, 'unassessed_features': 4,
           'dimension_history_observations': 19, 'restoration_claimed': False}


class AssessmentError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(value, code):
    if not value:
        raise AssessmentError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _keys(value, keys, code):
    need(type(value) is dict and set(value) == set(keys), code)


def _attributes(node, allowed, code):
    need(set(node.attrib) <= set(allowed), code)


def _leaf(node, code, attributes=()):
    need(node is not None and len(node) == 0, code)
    _attributes(node, attributes, code)


def _element_only(node, code):
    need(not (node.text or '').strip() and
         all(not (child.tail or '').strip() for child in node), code)


def _number(value):
    need(type(value) is str and len(value) <= 128 and
         re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?', value),
         'NUMERIC_LEXICAL')
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise AssessmentError('NUMERIC_LEXICAL') from None
    need(result.is_finite() and abs(result.adjusted()) <= 100, 'NUMERIC_BOUND')
    return result


def _helpers(libraries):
    _keys(libraries, LIBRARY_PINS, 'LIBRARY_SET')
    for key, expected in LIBRARY_PINS.items():
        need(type(libraries[key]) is bytes and sha(libraries[key]) == expected,
             'LIBRARY_PIN')
    names = {'_select', '_load', '_archive', '_parse', '_reference',
             '_guard_references', '_source_cells', '_baseline_rich',
             '_filter_authority', '_validations', '_hidden', '_chart_profile',
             '_tree', '_filters', '_number'}
    tree = ast.parse(libraries['adapter'])
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in names]
    need({node.name for node in body} == names, 'PURE_HELPER_DEFINITIONS')
    namespace = {name: globals()[name] for name in
                 ('ast', 'collections', 'deepcopy', 'Decimal', 'InvalidOperation',
                  'hashlib', 'io', 'json', 'PurePosixPath', 'posixpath', 're',
                  'stat', 'types', 'ET', 'zipfile')}
    namespace.update({'need': need, '_keys': _keys, 'sha': sha,
                      'RichJoinError': AssessmentError,
                      'LIBRARY_PINS': {k: v for k, v in LIBRARY_PINS.items() if k != 'adapter'},
                      '__name__': __name__})
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                 '<pinned-pure-profile-helpers>', 'exec'), namespace)
    helper = types.SimpleNamespace(**namespace)
    received, unused_recalc, structures, unused_strict, raw = helper._load(
        {k: v for k, v in libraries.items() if k != 'adapter'})
    return helper, received, structures, raw


def _archive(data, kind, helper, received, raw):
    # The reused guard checks bounds, duplicates, XML declarations, PI, UTF16,
    # ODS repetition and meaningful-cell expansion before legacy parsing.
    roots = helper._archive(data, kind, received, raw)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        need(not any(re.search(r'(?i)(vbaProject|activeX|embeddings|externalLinks)', n)
                     for n in names), 'ACTIVE_OR_EXTERNAL_PART_UNSUPPORTED')
        for name in names:
            if name.endswith('.rels'):
                root = ET.fromstring(archive.read(name))
                need(root.tag == '{' + PACKAGE_REL_NS + '}Relationships' and
                     not root.attrib, 'RELATIONSHIPS_ROOT_PROFILE')
                _element_only(root, 'RELATIONSHIPS_MIXED_TEXT')
                if name == '_rels/.rels':
                    owner = ''
                    allowed_types = {REL_BASE + 'officeDocument', REL_BASE + 'extended-properties',
                        REL_BASE + 'custom-properties', PACKAGE_REL_NS + '/metadata/core-properties'}
                else:
                    directory, filename = name.rsplit('/_rels/', 1)
                    owner = directory + '/' + filename.removesuffix('.rels')
                    need(owner in names, 'RELATIONSHIP_OWNER_MISSING')
                    if owner == 'xl/workbook.xml':
                        allowed_types = {REL_BASE + x for x in ('worksheet', 'styles', 'theme', 'sharedStrings')}
                    elif re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml', owner):
                        allowed_types = {REL_BASE + x for x in ('drawing', 'table')}
                    elif re.fullmatch(r'xl/drawings/drawing[0-9]+\.xml', owner):
                        allowed_types = {REL_BASE + 'chart'}
                    else:
                        raise AssessmentError('RELATIONSHIP_OWNER_UNSUPPORTED')
                for node in root:
                    need(node.tag == '{' + PACKAGE_REL_NS + '}Relationship' and
                         {'Id', 'Type', 'Target'} <= set(node.attrib),
                         'RELATIONSHIP_ELEMENT_PROFILE')
                    _leaf(node, 'RELATIONSHIP_ELEMENT_PROFILE', ('Id', 'Type', 'Target', 'TargetMode'))
                    need(not (node.text or '').strip(), 'RELATIONSHIP_MIXED_TEXT')
                    need(node.get('Type') in allowed_types, 'RELATIONSHIP_TYPE_UNSUPPORTED')
                    need(_target(owner, node.get('Target')) in names, 'RELATIONSHIP_TARGET_MISSING')
                ids = [node.get('Id') for node in root]
                need(None not in ids and len(set(ids)) == len(ids), 'RELATIONSHIP_IDENTITY')
                need(all(node.get('TargetMode', 'Internal') == 'Internal'
                         for node in root), 'EXTERNAL_RELATIONSHIP_UNSUPPORTED')
        if kind == 'xlsx':
            need({'xl/workbook.xml', 'xl/_rels/workbook.xml.rels'} <= set(names),
                 'XLSX_REQUIRED_PARTS')
            need('content.xml' not in names, 'XLSX_ODF_AMBIGUITY')
            allowed_parts = (
                r'\[Content_Types\]\.xml', r'_rels/\.rels',
                r'docProps/(?:app|core|custom)\.xml',
                r'xl/(?:workbook|styles|sharedStrings)\.xml',
                r'xl/_rels/workbook\.xml\.rels',
                r'xl/theme/theme[0-9]+\.xml',
                r'xl/worksheets/sheet[0-9]+\.xml',
                r'xl/worksheets/_rels/sheet[0-9]+\.xml\.rels',
                r'xl/drawings/drawing[0-9]+\.xml',
                r'xl/drawings/_rels/drawing[0-9]+\.xml\.rels',
                r'xl/charts/chart[0-9]+\.xml',
                # Original authority carries a vendor table/header-band which
                # the selected ODS no longer establishes.  Its presence is
                # allowed as an explicitly unassessed known history property,
                # never counted as restored or as a required selected fact.
                r'xl/tables/table[0-9]+\.xml',
            )
            need(all(any(re.fullmatch(pattern, name) for pattern in allowed_parts)
                     for name in names), 'XLSX_PACKAGE_PART_UNSUPPORTED')
            for name in names:
                if name.endswith('.rels'):
                    roots[name] = ET.fromstring(archive.read(name))
    return roots


def _target(owner, target):
    need(type(target) is str and target and '\\' not in target and ':' not in target
         and '\0' not in target and '?' not in target and '#' not in target,
         'RELATIONSHIP_TARGET')
    joined = target[1:] if target.startswith('/') else posixpath.normpath(
        posixpath.join(posixpath.dirname(owner), target))
    need(joined and not joined.startswith('../') and not joined.startswith('/'),
         'RELATIONSHIP_TARGET')
    return joined


def _rels(roots, owner):
    name = posixpath.dirname(owner) + '/_rels/' + posixpath.basename(owner) + '.rels'
    root = roots.get(name)
    return {} if root is None else {node.get('Id'): node for node in root}


def _xlsx_guard(roots, parsed, helper, library):
    ns = library.NS
    wb = roots['xl/workbook.xml']
    name_groups = wb.findall('x:definedNames', ns)
    need(len(name_groups) <= 1, 'DEFINED_NAMES_GROUP_COUNT')
    for group in name_groups:
        _attributes(group, (), 'DEFINED_NAMES_GROUP_PROFILE')
        _element_only(group, 'DEFINED_NAMES_MIXED_TEXT')
        for node in group:
            need(node.tag == library.q('x', 'definedName'), 'DEFINED_NAME_ELEMENT_PROFILE')
            _leaf(node, 'DEFINED_NAME_ELEMENT_PROFILE',
                  ('name', 'localSheetId', 'hidden', 'function', 'vbProcedure', 'xlm'))
            need(node.get('name') and all(node.get(flag, '0') in ('0', 'false')
                 for flag in ('function', 'vbProcedure', 'xlm')), 'DEFINED_NAME_ACTIVE_FLAG')
            need(node.get('hidden', '0') in ('0', 'false', '1', 'true'), 'DEFINED_NAME_HIDDEN_BOOLEAN')
            if not node.get('name').startswith('_xlnm.'):
                need(node.get('hidden', '0') in ('0', 'false'), 'CUSTOM_NAME_HIDDEN_UNSUPPORTED')
            if node.get('localSheetId') is not None:
                need(node.get('localSheetId') in ('0', '1', '2'), 'DEFINED_NAME_SCOPE')
    sheets = wb.findall('x:sheets/x:sheet', ns)
    need(len(sheets) == len(parsed['sheets']) == 3 and
         len(set(parsed['names'])) == 3, 'FIXED_THREE_SHEET_IDENTITY')
    need(len({node.get('sheetId') for node in sheets}) == 3, 'SHEET_IDENTITY_DUPLICATE')
    workbook_rels = _rels(roots, 'xl/workbook.xml')
    selected_parts = []
    linked_charts = []
    linked_drawings = []
    for index, sheet in enumerate(sheets):
        rid = library.attr(sheet, 'r', 'id')
        need(rid in workbook_rels and workbook_rels[rid].get('Type') == REL_BASE + 'worksheet',
             'WORKSHEET_RELATIONSHIP')
        part = _target('xl/workbook.xml', workbook_rels[rid].get('Target'))
        need(part in roots and part not in selected_parts, 'WORKSHEET_TARGET')
        selected_parts.append(part)
        root = roots[part]
        _element_only(root, 'XLSX_WORKSHEET_MIXED_TEXT')
        allowed_sheet_children = {library.q('x', name) for name in
            ('sheetPr', 'dimension', 'sheetViews', 'sheetFormatPr', 'cols',
             'sheetData', 'autoFilter', 'mergeCells', 'dataValidations',
             'printOptions', 'pageMargins', 'pageSetup', 'headerFooter', 'drawing',
             'tableParts')}
        need(all(node.tag in allowed_sheet_children for node in root),
             'XLSX_WORKSHEET_ELEMENT_UNSUPPORTED')
        need(len({node.tag for node in root}) == len(root), 'XLSX_WORKSHEET_ELEMENT_DUPLICATE')
        data_nodes = root.findall('x:sheetData', ns)
        need(len(data_nodes) == 1 and
             all(node.tag == library.q('x', 'row') for node in data_nodes[0]),
             'XLSX_SHEET_DATA_ELEMENT_UNSUPPORTED')
        _element_only(data_nodes[0], 'XLSX_SHEET_DATA_MIXED_TEXT')
        rows = root.findall('x:sheetData/x:row', ns)
        seen_rows = set()
        seen_cells = set()
        for row in rows:
            _element_only(row, 'XLSX_ROW_MIXED_TEXT')
            _attributes(row, ('r', 'ht', 'customHeight', 'hidden', 's', 'customFormat',
                             'spans', 'outlineLevel', 'collapsed', 'thickTop', 'thickBot', 'ph'),
                        'XLSX_ROW_ATTRIBUTE_UNSUPPORTED')
            need(all(node.tag == library.q('x', 'c') for node in row),
                 'XLSX_ROW_ELEMENT_UNSUPPORTED')
            number = row.get('r', '')
            need(re.fullmatch(r'[1-9][0-9]{0,3}', number) and
                 int(number) <= 1000 and number not in seen_rows, 'XLSX_ROW_IDENTITY')
            seen_rows.add(number)
            for cell in row.findall('x:c', ns):
                _element_only(cell, 'XLSX_CELL_MIXED_TEXT')
                _attributes(cell, ('r', 's', 't'), 'XLSX_CELL_ATTRIBUTE_UNSUPPORTED')
                location = cell.get('r', '')
                need(re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,3}', location) and
                     re.search(r'[0-9]+$', location).group() == number and
                     location not in seen_cells, 'XLSX_CELL_IDENTITY')
                seen_cells.add(location)
                formula = cell.findall('x:f', ns)
                need(len(formula) <= 1 and len(cell.findall('x:v', ns)) <= 1
                     and len(cell.findall('x:is', ns)) <= 1, 'XLSX_CELL_AMBIGUOUS')
                if formula:
                    _leaf(formula[0], 'XLSX_FORMULA_SCALAR')
                    need(not formula[0].attrib and formula[0].text
                         and cell.get('t', 'n') == 'n' and
                         all(node.tag in (library.q('x', 'f'), library.q('x', 'v'))
                             for node in cell), 'XLSX_FORMULA_PROFILE')
                elif cell.get('t', 'n') == 'n' and cell.find('x:v', ns) is not None:
                    _number(cell.findtext('x:v', namespaces=ns))
                if not formula:
                    expected_child = 'is' if cell.get('t') == 'inlineStr' else 'v'
                    need(all(node.tag == library.q('x', expected_child) for node in cell),
                         'XLSX_LITERAL_PAYLOAD_PROFILE')
                for value in cell.findall('x:v', ns):
                    _leaf(value, 'XLSX_VALUE_SCALAR')
                for inline in cell.findall('x:is', ns):
                    _element_only(inline, 'XLSX_INLINE_STRING_MIXED_TEXT')
                    _attributes(inline, (), 'XLSX_INLINE_STRING_PROFILE')
                    need(len(inline) == 1 and inline[0].tag == library.q('x', 't'),
                         'XLSX_INLINE_STRING_PROFILE')
                    _leaf(inline[0], 'XLSX_TEXT_SCALAR', ('{http://www.w3.org/XML/1998/namespace}space',))
                need(not cell.findall('x:extLst', ns), 'XLSX_CELL_EXTENSION_UNSUPPORTED')
        for group in root.findall('x:mergeCells', ns):
            _element_only(group, 'XLSX_MERGE_MIXED_TEXT')
            _attributes(group, ('count',), 'XLSX_MERGE_GROUP_PROFILE')
            need(group.get('count', str(len(group))) == str(len(group)), 'XLSX_MERGE_DECLARED_COUNT')
            for merge in group:
                need(merge.tag == library.q('x', 'mergeCell') and set(merge.attrib) == {'ref'},
                     'XLSX_MERGE_ELEMENT_PROFILE')
                _leaf(merge, 'XLSX_MERGE_ELEMENT_PROFILE', ('ref',))
                need(not (merge.text or '').strip(), 'XLSX_MERGE_MIXED_TEXT')
        # A chart must be attached to the selected sheet; an orphan chart part
        # cannot satisfy the requirement merely because a glob finds it.
        drawings = root.findall('x:drawing', ns)
        need(len(drawings) == (1 if index == 0 else 0), 'CHART_DRAWING_SCOPE')
        for drawing in drawings:
            relation = _rels(roots, part).get(library.attr(drawing, 'r', 'id'))
            need(relation is not None and relation.get('Type') == REL_BASE + 'drawing',
                 'DRAWING_RELATIONSHIP')
            drawing_part = _target(part, relation.get('Target'))
            need(drawing_part in roots, 'DRAWING_TARGET')
            linked_drawings.append(drawing_part)
            chart_nodes = roots[drawing_part].findall('.//c:chart', ns)
            need(len(chart_nodes) == 1, 'ATTACHED_CHART_COUNT')
            chart_relation = _rels(roots, drawing_part).get(
                library.attr(chart_nodes[0], 'r', 'id'))
            need(chart_relation is not None and chart_relation.get('Type') == REL_BASE + 'chart',
                 'CHART_RELATIONSHIP')
            chart_part = _target(drawing_part, chart_relation.get('Target'))
            need(chart_part in roots, 'CHART_TARGET')
            linked_charts.append(chart_part)
    actual_charts = [name for name in roots if re.fullmatch(r'xl/charts/chart[0-9]+\.xml', name)]
    need(len(linked_charts) == 1 and set(linked_charts) == set(actual_charts),
         'ALL_CHARTS_ATTACHED')
    actual_sheets = {name for name in roots if re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml', name)}
    actual_drawings = {name for name in roots if re.fullmatch(r'xl/drawings/drawing[0-9]+\.xml', name)}
    need(set(selected_parts) == actual_sheets and set(linked_drawings) == actual_drawings,
         'ALL_WORKSHEET_DRAWING_PARTS_ATTACHED')
    if 'xl/sharedStrings.xml' in roots:
        shared = roots['xl/sharedStrings.xml']
        _element_only(shared, 'SHARED_STRING_MIXED_TEXT')
        _attributes(shared, ('count', 'uniqueCount'), 'SHARED_STRING_PROFILE')
        for item in shared:
            _element_only(item, 'SHARED_STRING_MIXED_TEXT')
            need(item.tag == library.q('x', 'si') and not item.attrib and
                 len(item) == 1 and item[0].tag == library.q('x', 't'), 'SHARED_STRING_PROFILE')
            _leaf(item[0], 'SHARED_STRING_TEXT_SCALAR', ('{http://www.w3.org/XML/1998/namespace}space',))
    # Guard before the legacy normalizer can erase a second endpoint sheet.
    for node in wb.findall('x:definedNames/x:definedName', ns):
        helper._reference(node.text, parsed['names'], separator='!')
    for chart in parsed['charts']:
        for node in chart.findall('.//c:f', ns):
            helper._reference(node.text, parsed['names'], separator='!')
    return selected_parts


def _values(source):
    result = {}
    cells = source['sheets'][0]['cells']
    for row in range(2, 6):
        quantity, price, formula = (cells[prefix + str(row)] for prefix in ('C', 'D', 'G'))
        need(quantity['kind'] == price['kind'] == 'number' and
             formula['kind'] == 'formula' and
             formula['formula'] == f'C{row}*D{row}', 'SOURCE_MULTIPLICATION_PROFILE')
        result[(0, 'G' + str(row))] = quantity['value'] * price['value']
    summary = source['sheets'][1]['cells']['B2']
    need(summary['kind'] == 'formula' and summary['formula'] == 'SUM(S0!G2:G5)',
         'SOURCE_SUMMARY_PROFILE')
    result[(1, 'B2')] = sum(result.values())
    need(all(value.is_finite() for value in result.values()), 'SOURCE_ARITHMETIC_BOUND')
    return result


def _cache_entries(values):
    return [{'sheet_index': i + 1, 'cell': location, 'value': str(value)}
            for (i, location), value in sorted(values.items())]


def _cell_projection(parsed):
    return [{'name': name, 'cells': {location: {k: str(v) if isinstance(v, Decimal) else v
              for k, v in cell.items() if k in ('kind', 'value', 'formula')}
              for location, cell in sorted(sheet['cells'].items())}}
            for name, sheet in zip(parsed['names'], parsed['sheets'], strict=True)]


def _hidden_xlsx(roots, parts, library):
    result = []
    sheets = roots['xl/workbook.xml'].findall('x:sheets/x:sheet', library.NS)
    for sheet, part in zip(sheets, parts, strict=True):
        root = roots[part]
        state = sheet.get('state', 'visible')
        need(state in ('visible', 'hidden', 'veryHidden'), 'SHEET_VISIBILITY_PROFILE')
        hidden_rows = []
        for row in root.findall('x:sheetData/x:row', library.NS):
            flag = row.get('hidden', '0')
            need(flag in ('0', '1', 'false', 'true'), 'ROW_HIDDEN_BOOLEAN')
            if flag in ('1', 'true'):
                hidden_rows.append(int(row.get('r')))
        columns = []
        spans = set()
        for column in root.findall('x:cols/x:col', library.NS):
            a, b = column.get('min', ''), column.get('max', '')
            need(a.isdigit() and b.isdigit() and 1 <= int(a) <= int(b) <= 16384,
                 'COLUMN_HIDDEN_EXTENT')
            block = set(range(int(a), int(b) + 1))
            need(not spans & block, 'COLUMN_DECLARATION_OVERLAP')
            spans |= block
            flag = column.get('hidden', '0')
            need(flag in ('0', '1', 'false', 'true'), 'COLUMN_HIDDEN_BOOLEAN')
            if flag in ('1', 'true'):
                columns.extend(sorted(block))
        result.append((state == 'visible', tuple(sorted(hidden_rows)), tuple(sorted(columns))))
    return tuple(result)


def _source_hidden(source, helper, library):
    # XLSX has a current hidden bit, with no ODS collapse/filter provenance.
    # Keep the full source mode digest separately and compare current visibility.
    full = helper._hidden(source, library)
    projected = tuple((display == 'true', tuple(row for row, mode in rows),
                       tuple(column for column, mode in columns))
                      for display, rows, columns in full)
    return projected, sha(canonical(full))


def _xlsx_names(parsed):
    result = []
    for item in parsed['defs']:
        if item['name'].startswith('_xlnm.'):
            need(item['name'] in ('_xlnm.Print_Area', '_xlnm._FilterDatabase'),
                 'BUILTIN_NAME_UNASSESSED')
            continue
        scope = None if item['scope'] is None else int(item['scope'])
        result.append((item['name'], scope, item['ref']))
    need(len(result) == len(set(result)) == 1, 'CUSTOM_NAME_COUNT')
    return sorted(result, key=repr)


def _xlsx_filter(parsed, library):
    result = []
    for index, sheet in enumerate(parsed['sheets']):
        nodes = sheet['xml'].findall('x:autoFilter', library.NS)
        need(len(nodes) <= 1, 'FILTER_COUNT')
        for node in nodes:
            need(set(node.attrib) <= {'ref'} and len(node) == 1, 'FILTER_PROFILE')
            column = node[0]
            need(column.tag == library.q('x', 'filterColumn') and
                 set(column.attrib) <= {'colId', 'hiddenButton', 'showButton'} and
                 column.get('colId', '').isdigit() and len(column) == 1,
                 'FILTER_PROFILE')
            filters = column[0]
            need(filters.tag == library.q('x', 'filters') and
                 set(filters.attrib) <= {'blank'} and filters.get('blank', '0') in ('0', 'false'),
                 'FILTER_PROFILE')
            values = []
            for item in filters:
                need(item.tag == library.q('x', 'filter') and set(item.attrib) == {'val'}
                     and not list(item), 'FILTER_PROFILE')
                values.append(item.get('val'))
            need(values and len(set(values)) == len(values), 'FILTER_VALUES')
            result.append((index, node.get('ref'), int(column.get('colId')), tuple(sorted(values))))
    need(len(result) == 1, 'FILTER_COUNT')
    return result


def _validation_xlsx(parsed, library):
    result = []
    for index, sheet in enumerate(parsed['sheets']):
        groups = sheet['xml'].findall('x:dataValidations', library.NS)
        need(len(groups) <= 1, 'VALIDATION_GROUP_COUNT')
        for group in groups:
            _element_only(group, 'VALIDATION_GROUP_MIXED_TEXT')
            _attributes(group, ('count', 'disablePrompts', 'xWindow', 'yWindow'),
                        'VALIDATION_GROUP_ATTRIBUTE_UNSUPPORTED')
            need(group.get('disablePrompts', '0') in ('0', 'false'),
                 'VALIDATION_GROUP_DISABLE_PROMPTS')
            need(group.get('count', str(len(group))) == str(len(group)), 'VALIDATION_DECLARED_COUNT')
            for node in group:
                _element_only(node, 'VALIDATION_MIXED_TEXT')
                _attributes(node, ('type', 'operator', 'allowBlank', 'showDropDown',
                                  'showInputMessage', 'showErrorMessage', 'errorStyle',
                                  'errorTitle', 'error', 'promptTitle', 'prompt', 'sqref'),
                            'VALIDATION_ATTRIBUTE_UNSUPPORTED')
                need(node.tag == library.q('x', 'dataValidation') and
                     node.get('type') == 'whole' and node.get('operator', 'between') == 'between',
                     'VALIDATION_PROFILE')
                need(len(node.findall('x:formula1', library.NS)) ==
                     len(node.findall('x:formula2', library.NS)) == 1 and len(node) == 2,
                     'VALIDATION_FORMULA_PROFILE')
                for formula in node:
                    _leaf(formula, 'VALIDATION_FORMULA_SCALAR')
                locations = set()
                for part in node.get('sqref', '').split():
                    si, first, last = _reference_local(part, parsed['names'], index, library)
                    need(si == index, 'VALIDATION_CROSS_SHEET')
                    match_a, match_b = re.fullmatch(r'([A-Z]+)([0-9]+)', first), re.fullmatch(r'([A-Z]+)([0-9]+)', last)
                    need(match_a[1] == match_b[1] and
                         0 <= int(match_b[2]) - int(match_a[2]) <= 1000,
                         'VALIDATION_RANGE_PROFILE')
                    block = {match_a[1] + str(row) for row in range(int(match_a[2]), int(match_b[2]) + 1)}
                    need(not locations & block, 'VALIDATION_LOCATION_OVERLAP')
                    locations |= block
                low = _number(node.findtext('x:formula1', namespaces=library.NS))
                high = _number(node.findtext('x:formula2', namespaces=library.NS))
                def boolean(field, default):
                    value = node.get(field, default)
                    need(value in ('0', '1', 'false', 'true'), 'VALIDATION_BOOLEAN')
                    return value in ('1', 'true')
                result.append((index, tuple(sorted(locations)), low, high,
                    boolean('allowBlank', '0'), boolean('showErrorMessage', '0'),
                    node.get('errorStyle', 'stop'), node.get('errorTitle', ''), node.get('error', '')))
    need(len(result) == 1, 'VALIDATION_COUNT')
    return result


def _reference_local(value, names, default, library):
    # Use the same bounded range grammar as the pinned reference helper.
    need(type(value) is str and re.fullmatch(r'\$?[A-Z]{1,3}\$?[1-9][0-9]{0,3}(?::\$?[A-Z]{1,3}\$?[1-9][0-9]{0,3})?', value),
         'LOCAL_RANGE_PROFILE')
    a = value.replace('$', '').split(':')
    return default, a[0], a[-1]


def _chart_signature(parsed, library):
    need(len(parsed['charts']) == 1, 'CHART_COUNT')
    root = parsed['charts'][0]
    for node in root.findall('.//c:f', library.NS) + root.findall('.//c:v', library.NS):
        _leaf(node, 'CHART_REFERENCE_OR_CACHE_SCALAR')
    charts = root.findall('.//c:barChart', library.NS)
    series = root.findall('.//c:ser', library.NS)
    need(len(charts) == len(series) == 1 and
         len(root.findall('.//c:plotArea', library.NS)) == 1, 'CHART_TYPE_SERIES_COUNT')
    plot = root.find('.//c:plotArea', library.NS)
    allowed = {library.q('c', item) for item in ('layout', 'barChart', 'catAx', 'valAx', 'spPr', 'extLst')}
    need(all(node.tag in allowed for node in plot) and
         not plot.findall('c:extLst', library.NS), 'CHART_PLOT_PROFILE')
    refs = [library.norm(node.text, parsed['names'])
            for node in series[0].findall('.//c:f', library.NS)]
    need(len(refs) == 3, 'CHART_REFERENCE_COUNT')
    titles = [''.join(node.text or '' for node in title.findall('.//a:t', library.NS))
              for title in root.findall('.//c:title', library.NS)]
    need(titles and all(titles), 'CHART_TITLE_REQUIRED')
    visible = root.findall('.//c:plotVisOnly', library.NS)
    need(len(visible) == 1 and visible[0].get('val') in ('1', 'true'),
         'CHART_VISIBLE_ONLY_REQUIRED')
    direction = charts[0].findall('c:barDir', library.NS)
    grouping = charts[0].findall('c:grouping', library.NS)
    need(len(direction) == len(grouping) == 1, 'CHART_TYPE_PROFILE')
    need(len(root.findall('.//c:externalData', library.NS)) == 0 and
         len(root.findall('.//c:extLst', library.NS)) == 0, 'CHART_EXTENSION_UNSUPPORTED')
    return (tuple(refs), tuple(titles), direction[0].get('val'), grouping[0].get('val'))


def _chart_cache(parsed, source, values, library):
    series = parsed['charts'][0].find('.//c:ser', library.NS)
    caches = []
    for parent_name, ref_name, cache_name in [('tx', 'strRef', 'strCache'),
                                           ('cat', 'strRef', 'strCache'),
                                           ('val', 'numRef', 'numCache')]:
        parent = series.find('c:' + parent_name, library.NS)
        need(parent is not None, 'CHART_CACHE_REQUIRED')
        _element_only(parent, 'CHART_REFERENCE_MIXED_TEXT')
        # The existing original authority spells its text-ID category reference
        # as numRef with no point cache.  Retain that explicit cache gap; a
        # present numeric category cache is not proof of string-ID labels.
        numeric_text_category = (parent_name == 'cat' and len(parent) == 1 and
                                 parent[0].tag == library.q('c', 'numRef'))
        if numeric_text_category:
            ref_name, cache_name = 'numRef', 'numCache'
        need(len(parent) == 1 and parent[0].tag == library.q('c', ref_name),
             'CHART_REFERENCE_TYPE_PROFILE')
        ref = parent[0]
        _element_only(ref, 'CHART_REFERENCE_MIXED_TEXT')
        need(all(node.tag in (library.q('c', 'f'), library.q('c', cache_name))
                 for node in ref) and len(ref.findall('c:f', library.NS)) == 1,
             'CHART_CACHE_TYPE_PROFILE')
        nodes = ref.findall('c:' + cache_name, library.NS)
        need(len(nodes) <= 1, 'CHART_CACHE_AMBIGUOUS')
        need(not (numeric_text_category and nodes),
             'CHART_CATEGORY_NUMERIC_CACHE_TEXT_IDS_UNSUPPORTED')
        if not nodes:
            caches.append(None)
            continue
        cache = nodes[0]
        _element_only(cache, 'CHART_CACHE_MIXED_TEXT')
        _attributes(cache, (), 'CHART_CACHE_ATTRIBUTE_UNSUPPORTED')
        allowed_cache_children = {library.q('c', x) for x in ('ptCount', 'pt')}
        if cache_name == 'numCache':
            allowed_cache_children.add(library.q('c', 'formatCode'))
        need(all(node.tag in allowed_cache_children for node in cache),
             'CHART_CACHE_ELEMENT_UNSUPPORTED')
        formats = cache.findall('c:formatCode', library.NS)
        need(len(formats) <= 1, 'CHART_CACHE_FORMAT_MULTIPLICITY')
        for node in formats:
            _leaf(node, 'CHART_CACHE_FORMAT_SCALAR')
        count = cache.findall('c:ptCount', library.NS)
        points = cache.findall('c:pt', library.NS)
        need(len(count) == 1 and count[0].get('val') == str(len(points)), 'CHART_CACHE_COUNT')
        _leaf(count[0], 'CHART_CACHE_COUNT_PROFILE', ('val',))
        need(not (count[0].text or '').strip(), 'CHART_CACHE_COUNT_PROFILE')
        need([point.get('idx') for point in points] == [str(i) for i in range(len(points))],
             'CHART_CACHE_INDICES')
        need(all(len(point.findall('c:v', library.NS)) == 1 and len(point) == 1 for point in points),
             'CHART_CACHE_POINTS')
        for point in points:
            _attributes(point, ('idx',), 'CHART_CACHE_POINT_PROFILE')
            _element_only(point, 'CHART_CACHE_POINT_PROFILE')
        caches.append([point.findtext('c:v', namespaces=library.NS) for point in points])
    visible_rows = [row for row in range(2, 6) if row not in source['sheets'][0]['hidden']]
    expected_label = source['sheets'][0]['cells']['G1']['value']
    expected_categories = [source['sheets'][0]['cells']['A' + str(row)]['value'] for row in visible_rows]
    expected_values = [values[(0, 'G' + str(row))] for row in visible_rows]
    actual_values = None if caches[2] is None else [_number(value) for value in caches[2]]
    # Original XLSX may serialize all data points while plotVisOnly excludes a
    # hidden row at rendering.  Both representations retain the same required
    # live references; every serialized point is checked independently.
    all_categories = [source['sheets'][0]['cells']['A' + str(row)]['value'] for row in range(2, 6)]
    all_values = [values[(0, 'G' + str(row))] for row in range(2, 6)]
    need(caches[0] is None or caches[0] == [expected_label],
         'CHART_LABEL_CACHE_SOURCE_SEMANTICS')
    need(caches[1] is None or caches[1] in (expected_categories, all_categories),
         'CHART_CATEGORY_CACHE_SOURCE_SEMANTICS')
    need(actual_values is None or actual_values in (expected_values, all_values),
         'CHART_VALUE_CACHE_INDEPENDENT_SOURCE_SEMANTICS')
    if caches[1] is not None and actual_values is not None:
        need((caches[1] == expected_categories and actual_values == expected_values) or
             (caches[1] == all_categories and actual_values == all_values),
             'CHART_CACHE_REPRESENTATION_COHERENCY')
    return {'complete': all(cache is not None for cache in caches),
            'missing_components': sum(cache is None for cache in caches),
            'points': 0 if caches[1] is None else len(caches[1])}


def _source_chart_cache_shape(source, library):
    # Numeric caches may be stale, but extra/duplicate/misbound cached rows
    # cannot disappear into that limitation.  Their category lineage and exact
    # finite visible-row dimension remain facts independent of numeric truth.
    root = source['charts'][0]
    rows = root.findall('.//table:table/table:table-rows/table:table-row', library.NS)
    visible = [row for row in range(2, 6) if row not in source['sheets'][0]['hidden']]
    expected = [source['sheets'][0]['cells']['A' + str(row)]['value'] for row in visible]
    actual = [library.ods_text(row.findall('table:table-cell', library.NS)[0]) for row in rows]
    need(len(rows) == len(visible) and actual == expected, 'SOURCE_CHART_CACHE_ROW_LINEAGE')


def _source_profile(source_bytes, authority_bytes, libraries):
    helper, received, library, raw = _helpers(libraries)
    source_roots = _archive(source_bytes, 'ods', helper, received, raw)
    authority_roots = _archive(authority_bytes, 'xlsx', helper, received, raw)
    authority = helper._parse(library, 'xlsx', authority_bytes)
    source = helper._parse(library, 'ods', source_bytes, authority['names'])
    authority_parts = _xlsx_guard(authority_roots, authority, helper, library)
    source_raw = raw.raw_cells(source_roots)
    helper._guard_references(source, library, source_raw)
    for row in range(2, 6):
        need(re.fullmatch(r'of:=\[\.\$?C\$?' + str(row) +
                         r'\]\*\[\.\$?D\$?' + str(row) + r'\]',
                         source_raw[0]['cells']['G' + str(row)]['formula']) is not None,
             'SOURCE_RAW_MULTIPLICATION')
    # Only the known selected numeric literal may differ from the original
    # authority, allowing a future Root-selected eligible ordinary edited input.
    adjusted = deepcopy(authority)
    c2 = source['sheets'][0]['cells']['C2']
    need(c2['kind'] == 'number', 'SOURCE_C2_NUMERIC')
    adjusted['sheets'][0]['cells']['C2']['value'] = c2['value']
    helper._source_cells(adjusted, source)
    values = _values(source)
    helper._baseline_rich(library.rich(adjusted, source))
    helper._filter_authority(authority, source, library)
    validation = helper._validations(source, library)
    need(validation[2] <= c2['value'] <= validation[3] and
         c2['value'] == c2['value'].to_integral_value(), 'SOURCE_C2_VALIDATION')
    helper._chart_profile(source, library, authority)
    _source_chart_cache_shape(source, library)
    hidden, mode_digest = _source_hidden(source, helper, library)
    need(hidden == _hidden_xlsx(authority_roots, authority_parts, library),
         'SOURCE_AUTHORITY_CURRENT_HIDDEN')
    names = sorted([(item['name'], item['scope'], item['ref']) for item in source['named']
                    if not item['usable']], key=repr)
    need(names == _xlsx_names(authority), 'SOURCE_CUSTOM_NAME_PROFILE')
    numeric_delta = {'sheet_index': 1, 'cell': 'C2',
                     'authority_value': str(authority['sheets'][0]['cells']['C2']['value']),
                     'source_value': str(c2['value'])}
    semantic = {'cells': _cell_projection(source), 'names': names,
                'current_hidden': hidden, 'source_hidden_mode_sha256': mode_digest,
                'merges': [sorted(sheet['merges']) for sheet in source['sheets']],
                'formula_values': _cache_entries(values),
                'authority_selected_chart': _chart_signature(authority, library),
                'authority_filter_sha256': sha(canonical(_xlsx_filter(authority, library))),
                'source_validation_sha256': sha(canonical(repr(validation)))}
    return helper, received, library, raw, source, authority, values, numeric_delta, semantic


def bind_profile(*, source_ods_bytes, authority_xlsx_bytes, libraries):
    """Prepare private request/oracle/projection in memory, never a workbook.

    Independence, provenance and eligibility remain external unverified joins.
    The oracle values come from source literals and this fixed formula graph.
    """
    with localcontext() as context:
        context.prec = 512
        *unused, values, delta, semantic = _source_profile(
            source_ods_bytes, authority_xlsx_bytes, libraries)
        source_hash, authority_hash = sha(source_ods_bytes), sha(authority_xlsx_bytes)
        request = {'schema': 'friday.ods-xlsx.selected-request.v1', 'profile': PROFILE,
                   'direction': 'ods_to_xlsx', 'source_sha256': source_hash,
                   'authority_sha256': authority_hash, 'source_numeric_delta': delta,
                   'fidelity_history': dict(HISTORY)}
        oracle = {'schema': 'friday.ods-xlsx.source-literal-oracle.v1',
                  'method': 'independent_Decimal_source_literals_fixed_formula_graph',
                  'source_sha256': source_hash, 'formula_values': _cache_entries(values),
                  'independence_verified': False}
        projection = {'schema': 'friday.ods-xlsx.selected-projection-binding.v1',
                      'profile': PROFILE, 'source_sha256': source_hash,
                      'authority_sha256': authority_hash,
                      'request_sha256': sha(canonical(request)),
                      'oracle_sha256': sha(canonical(oracle)),
                      'semantic_projection_sha256': sha(canonical(semantic))}
        return {'request': request, 'oracle': oracle, 'projection': projection}


def _check(*, source_ods_bytes, returned_xlsx_bytes, authority_xlsx_bytes,
           request, projection, oracle, pins, libraries):
    _keys(pins, PIN_KEYS, 'PIN_SCHEMA')
    need(all(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value)
             for value in pins.values()), 'PIN_FORMAT')
    for name, blob in [('source', source_ods_bytes), ('returned', returned_xlsx_bytes),
                       ('authority', authority_xlsx_bytes)]:
        need(type(blob) is bytes and sha(blob) == pins[name + '_sha256'], 'INPUT_PIN')
    for name, data in [('request', request), ('projection', projection), ('oracle', oracle)]:
        need(sha(canonical(data)) == pins[name + '_sha256'], 'JSON_PIN')
    _keys(request, REQUEST_KEYS, 'REQUEST_SCHEMA')
    _keys(projection, PROJECTION_KEYS, 'PROJECTION_SCHEMA')
    _keys(oracle, ORACLE_KEYS, 'ORACLE_SCHEMA')
    bound = bind_profile(source_ods_bytes=source_ods_bytes,
                         authority_xlsx_bytes=authority_xlsx_bytes, libraries=libraries)
    # Canonical JSON equality preserves primitive types (Python bool/int
    # equality must not let a changed binding borrow the original digest).
    need(canonical(request) == canonical(bound['request']), 'REQUEST_SOURCE_PROFILE')
    need(canonical(oracle) == canonical(bound['oracle']), 'ORACLE_SOURCE_ARITHMETIC')
    need(canonical(projection) == canonical(bound['projection']), 'PROJECTION_SOURCE_BINDING')
    need(all(projection[key] == pins[key] for key in
             ('source_sha256', 'authority_sha256', 'request_sha256', 'oracle_sha256')),
         'PROJECTION_PIN_JOIN')
    helper, received, library, raw, source, authority, values, delta, semantic = _source_profile(
        source_ods_bytes, authority_xlsx_bytes, libraries)
    roots = _archive(returned_xlsx_bytes, 'xlsx', helper, received, raw)
    returned = helper._parse(library, 'xlsx', returned_xlsx_bytes)
    parts = _xlsx_guard(roots, returned, helper, library)
    need(returned['names'] == source['names'], 'RETURNED_SHEET_NAMES_ORDER')
    formula_count = 0
    missing_formula_caches = 0
    for index, (before, after) in enumerate(zip(source['sheets'], returned['sheets'], strict=True)):
        need(set(before['cells']) == set(after['cells']), 'RETURNED_POPULATED_LOCATIONS')
        for location, expected in before['cells'].items():
            actual = after['cells'][location]
            need(expected['kind'] == actual['kind'], 'RETURNED_CELL_TYPE')
            if expected['kind'] == 'formula':
                formula_count += 1
                need(expected['formula'] == actual['formula'], 'RETURNED_FORMULA_GRAPH')
                # Fixed raw formula grammar is checked before normalized equality.
                raw_cell = roots[parts[index]].find(".//x:c[@r='" + location + "']", library.NS)
                expression = raw_cell.findtext('x:f', namespaces=library.NS)
                if index == 0:
                    row = re.search(r'[0-9]+$', location).group()
                    need(re.fullmatch(r'\$?C\$?' + row + r'\*\$?D\$?' + row, expression),
                         'RETURNED_RAW_MULTIPLICATION')
                else:
                    match = re.fullmatch(r'SUM\((.+)\)', expression)
                    need(match is not None and helper._reference(match[1], returned['names'],
                         separator='!', default_sheet=index) == (0, 'G2', 'G5'),
                         'RETURNED_RAW_SUMMARY')
                cached = raw_cell.findtext('x:v', namespaces=library.NS)
                if cached is None or cached == '':
                    missing_formula_caches += 1
                else:
                    need(_number(cached) == values[(index, location)],
                         'RETURNED_FORMULA_CACHE_INDEPENDENT_SOURCE_SEMANTICS')
            else:
                need(expected.get('value') == actual.get('value'), 'RETURNED_LITERAL_OR_ID')
        need(before['merges'] == after['merges'], 'RETURNED_MERGES')
    need(formula_count == 5, 'RETURNED_FORMULA_COUNT')
    need(_xlsx_names(returned) == semantic['names'], 'RETURNED_CUSTOM_NAME')
    need(_xlsx_filter(returned, library) == _xlsx_filter(authority, library),
         'RETURNED_FILTER_SEMANTICS')
    need(_validation_xlsx(returned, library) == _validation_xlsx(authority, library),
         'RETURNED_VALIDATION_SEMANTICS')
    source_hidden, source_modes_digest = _source_hidden(source, helper, library)
    need(_hidden_xlsx(roots, parts, library) == source_hidden, 'RETURNED_CURRENT_HIDDEN')
    need(_chart_signature(returned, library) == _chart_signature(authority, library),
         'RETURNED_CHART_REFERENCE_TITLE_TYPE')
    chart_cache = _chart_cache(returned, source, values, library)
    complete = missing_formula_caches == 0 and chart_cache['complete']
    return {'schema': 'friday.ods-xlsx.selected-byte-assessment.v1',
            'state': ('SELECTED_REQUIRED_BYTES_MATCH_SOURCE_PROJECTION' if complete else
                      'SELECTED_STRUCTURE_MATCH_WITH_CACHE_GAPS'),
            'scope': 'source_only_explicit_bytes_selected_profile', **FALSE_CLAIMS,
            'pins': dict(pins), 'library_pins': dict(LIBRARY_PINS),
            'semantic_projection_sha256': projection['semantic_projection_sha256'],
            'source_hidden_mode_sha256': source_modes_digest,
            'counts': {'sheets': 3, 'formula_cells': 5, 'multiplication_cells': 4,
                       'summary_cells': 1, 'text_ids': 4, 'custom_names': 1,
                       'charts': 1, 'checked_chart_cache_points': chart_cache['points'],
                       'missing_formula_caches': missing_formula_caches,
                       'missing_chart_cache_components': chart_cache['missing_components'],
                       'unassessed_vendor_table_parts': sum(bool(re.fullmatch(
                           r'xl/tables/table[0-9]+\.xml', name)) for name in roots),
                       'effective_filters': 1, 'validation_definitions': 1,
                       'validation_cells': 4,
                       'populated_cells': sum(len(s['cells']) for s in source['sheets'])},
            'fidelity_history': dict(HISTORY),
            'cache_assessment': ('PRESENT_CACHES_MATCH_SOURCE_DERIVED_DECIMAL' if complete else
                                 'INCOMPLETE_PRESENT_CACHES_MATCH_MISSING_CACHES_UNASSESSED'),
            'external_joins': 'UNBOUND',
            'limitations': ['no_conversion_custody_runtime_or_ordinary_observation',
                            'hash_bindings_do_not_prove_oracle_independence',
                            'formula_and_chart_caches_are_compared_not_recalculated_by_an_App',
                            'ODS_filter_collapse_hidden_provenance_not_recoverable_from_XLSX_bits',
                            'four_known_losses_four_unassessed_nineteen_dimensions_not_restored',
                            'vendor_features_freeze_header_band_print_geometry_unassessed']}


def assess_conversion(**inputs):
    """Return only fixed codes/counts/digests, never input text or formulas."""
    try:
        with localcontext() as context:
            context.prec = 512
            return _check(**inputs)
    except AssessmentError as error:
        return {'schema': 'friday.ods-xlsx.selected-byte-assessment.v1',
                'state': 'REFUSED', 'code': error.code, **FALSE_CLAIMS}
    except Exception:
        return {'schema': 'friday.ods-xlsx.selected-byte-assessment.v1',
                'state': 'REFUSED', 'code': 'BOUNDED_PARSER_OR_SCHEMA', **FALSE_CLAIMS}
