#!/usr/bin/env python3
"""Portable offline tests for the bounded native ODS same-format editor.

Public eligible source: no actual filenames, values, formulas or data pins.
Use the real isolated tools/hermes_cli source stand, with empty __init__.py
package initializers disclosed in the JSON report. No replacement primitives.
Input/output workbooks stay in memory; the report contains hashes/counts/codes.
Example: python3 -I -B test_sameformat_ods.py --native-root STAND \
  --s01-ods /private/basic.ods --s11-ods /private/rich.ods --report PRIVATE.json
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import sys
from xml.etree import ElementTree as ET
from xml.parsers import expat
import zipfile

O = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
T = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
TB = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
XL = 'http://www.w3.org/1999/xlink'
D = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
M = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
q = lambda ns, local: '{' + ns + '}' + local
CELL_TAGS = {q(TB, 'table-cell'), q(TB, 'covered-table-cell')}
CELL_EXPAT = {TB + '}table-cell', TB + '}covered-table-cell'}
ROW_GROUPS = {q(TB, n) for n in ('table-header-rows', 'table-row-group', 'table-rows')}
# Pin the finite pure-parser closure, never walk an installed source image.
PURE_SOURCES = (
    'tools/__init__.py', 'hermes_cli/__init__.py',
    'tools/scoped_zip.py', 'tools/scoped_presentation.py',
    'tools/scoped_odt.py', 'tools/scoped_ods.py',
    'tools/scoped_ods_chart.py', 'tools/scoped_spreadsheet_profiles.py',
    'tools/scoped_spreadsheet_rich.py', 'tools/scoped_spreadsheet_conversion.py',
)


class CliGuardError(ValueError):
    pass


def cli_need(value, code):
    if not value:
        raise CliGuardError(code)


def source_pins(root):
    return {name: sha((root / name).read_bytes()) for name in PURE_SOURCES}


def check_stand(root):
    # These checks MUST precede imports from either product package: the normal
    # installed tools initializer can initialize runtime services.
    cli_need(not any(name == package or name.startswith(package + '.')
                     for name in sys.modules for package in ('tools', 'hermes_cli')),
             'product_package_already_loaded')
    for name in ('tools/__init__.py', 'hermes_cli/__init__.py'):
        path = root / name
        try:
            info = path.lstat()
            cli_need(stat.S_ISREG(info.st_mode) and not path.is_symlink(),
                     'package_initializer_not_regular')
            cli_need(path.read_bytes() == b'', 'package_initializer_not_empty')
        except OSError:
            raise CliGuardError('package_initializer_unreadable') from None
    for name in PURE_SOURCES:
        try:
            info = (root / name).lstat()
            cli_need(stat.S_ISREG(info.st_mode) and not (root / name).is_symlink(),
                     'required_source_not_regular')
        except OSError:
            raise CliGuardError('required_source_unreadable') from None


def loaded_origins(root):
    result = {}
    for name, module in tuple(sys.modules.items()):
        if not any(name == package or name.startswith(package + '.')
                   for package in ('tools', 'hermes_cli')):
            continue
        origin = getattr(module, '__file__', None)
        cli_need(origin is not None, 'loaded_source_origin_missing')
        try:
            relative = str(Path(origin).resolve(strict=True).relative_to(root))
        except (OSError, ValueError):
            raise CliGuardError('loaded_source_outside_stand') from None
        cli_need(relative in PURE_SOURCES, 'loaded_source_outside_pure_closure')
        result[name] = relative
    return result


def reserve_report(path, root, inputs):
    """Reserve one new 0600 file through a verified owned parent dir fd."""
    absolute = Path(os.path.abspath(path))
    parent = absolute.parent
    try:
        cli_need(not any(p.is_symlink() for p in (parent, *parent.parents)),
                 'report_parent_symlink')
        actual_parent = parent.resolve(strict=True)
        actual = actual_parent / absolute.name
        cli_need(not actual.is_relative_to(root), 'report_destination_inside_source')
        cli_need(all(actual != p.resolve(strict=True) for p in inputs),
                 'report_destination_aliases_input')
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except CliGuardError:
        raise
    except OSError:
        raise CliGuardError('report_parent_or_input_unavailable') from None
    try:
        info = os.fstat(directory)
        cli_need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                 and not info.st_mode & 0o022, 'report_parent_not_private_owned')
        try:
            descriptor = os.open(absolute.name,
                                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=directory)
        except FileExistsError:
            raise CliGuardError('report_destination_exists') from None
        except OSError:
            raise CliGuardError('report_destination_unavailable') from None
        os.fchmod(descriptor, 0o600)
        return descriptor
    finally:
        os.close(directory)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(value, code):
    if not value:
        raise AssertionError(code)


def parts(data):
    with zipfile.ZipFile(BytesIO(data)) as archive:
        return {i.filename: archive.read(i) for i in archive.infolist()}


def rewrite(data, member, changed):
    out = BytesIO()
    with zipfile.ZipFile(BytesIO(data)) as src, zipfile.ZipFile(out, 'w') as dst:
        dst.comment = src.comment
        for info in src.infolist():
            dst.writestr(info, changed if info.filename == member else src.read(info))
    return out.getvalue()


def endtag(raw, start):
    quote = None
    for i in range(start, len(raw)):
        if quote:
            if raw[i] == quote:
                quote = None
        elif raw[i] in (34, 39):
            quote = raw[i]
        elif raw[i] == 62:
            return i + 1
    raise AssertionError('independent_span_tag_unclosed')


def element_spans(raw):
    """Independent expat byte positions for every physical element, pre-order."""
    parser = expat.ParserCreate(namespace_separator='}')
    spans = []
    stack = []
    def begin(name, attrs):
        start = parser.CurrentByteIndex
        entry = {'tag': '{' + name if '}' in name else name,
                 'begin': start, 'opening_end': endtag(raw, start), 'end': None}
        spans.append(entry)
        stack.append(entry)
    def end(name):
        entry = stack.pop()
        entry['end'] = (parser.CurrentByteIndex if
                        raw[entry['begin']:entry['opening_end']].rstrip().endswith(b'/>')
                        else endtag(raw, parser.CurrentByteIndex))
    parser.StartElementHandler = begin
    parser.EndElementHandler = end
    parser.Parse(raw, True)
    return spans


def rows(sheet):
    for child in sheet:
        if child.tag == q(TB, 'table-row'):
            yield child
        elif child.tag in ROW_GROUPS:
            yield from rows(child)


def cells(sheet):
    rn = 1
    for row in rows(sheet):
        height = int(row.get(q(TB, 'number-rows-repeated'), '1'))
        cn = 1
        for cell in row:
            if cell.tag not in CELL_TAGS:
                continue
            width = int(cell.get(q(TB, 'number-columns-repeated'), '1'))
            yield rn, cn, height, width, cell, row
            cn += width
        rn += height


def coordinates(ref):
    match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', ref)
    need(match is not None, 'independent_bad_cellref')
    col = 0
    for char in match[1]:
        col = col * 26 + ord(char) - 64
    return int(match[2]), col


def cellref(row, col):
    name = ''
    while col:
        col, rem = divmod(col - 1, 26)
        name = chr(65 + rem) + name
    return name + str(row)


def workbook(data):
    payloads = parts(data)
    raw = payloads['content.xml']
    root = ET.fromstring(raw)
    body = root.find(q(O, 'body')).find(q(O, 'spreadsheet'))
    return payloads, raw, root, body, body.findall(q(TB, 'table'))


def locate(data, sheet_index=0, ref='C2'):
    payloads, raw, root, body, sheets = workbook(data)
    r, c = coordinates(ref)
    found = [(n, row) for rr, cc, h, w, n, row in cells(sheets[sheet_index])
             if rr <= r < rr + h and cc <= c < cc + w]
    need(len(found) == 1, 'independent_target_ambiguous')
    node, row = found[0]
    index = list(root.iter()).index(node)
    span = element_spans(raw)[index]
    need(span['tag'] == node.tag, 'independent_span_node_alignment')
    return {'payloads': payloads, 'raw': raw, 'root': root, 'body': body,
            'sheets': sheets, 'node': node, 'row': row, 'span': span,
            'sheet_name': sheets[sheet_index].get(q(TB, 'name'))}


def node_span(raw, root, node):
    span = element_spans(raw)[list(root.iter()).index(node)]
    need(span['tag'] == node.tag, 'independent_span_node_alignment')
    return span


def replace_node(data, node, content):
    _, raw, root, _, _ = workbook(data)
    # Select through a pre-order index supplied by the caller, never ET reserialize.
    index = node if type(node) is int else list(root.iter()).index(node)
    span = element_spans(raw)[index]
    return rewrite(data, 'content.xml', raw[:span['begin']] + content + raw[span['end']:])


def attr(data, choose, ns, local, value):
    _, raw, root, body, sheets = workbook(data)
    node = choose(root, body, sheets)
    span = node_span(raw, root, node)
    prefix = None
    for _, pair in ET.iterparse(BytesIO(raw), events=('start-ns',)):
        if pair[1] == ns:
            prefix = pair[0]
            break
    need(prefix is not None, 'independent_attribute_namespace_missing')
    name = ((prefix + ':') if prefix else '') + local
    opening = raw[span['begin']:span['opening_end']]
    pattern = rb'\s+' + re.escape(name.encode()) + rb'\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)'
    escaped = str(value).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
    replacement = (' ' + name + '="' + escaped + '"').encode()
    if re.search(pattern, opening):
        changed = re.sub(pattern, lambda m: replacement, opening, count=1)
    else:
        finish = -2 if opening.rstrip().endswith(b'/>') else -1
        changed = opening[:finish] + replacement + opening[finish:]
    return rewrite(data, 'content.xml', raw[:span['begin']] + changed + raw[span['opening_end']:])


def choose_target(root, body, sheets):
    return next(n for r, c, h, w, n, _ in cells(sheets[0]) if r <= 2 < r+h and c <= 3 < c+w)


def state(path):
    info = path.stat()
    return {'bytes': info.st_size, 'sha256': sha(path.read_bytes()), 'inode': info.st_ino,
            'device': info.st_dev, 'mode': oct(info.st_mode & 0o777),
            'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}


def spec_for(data, sheet=0, ref='C2', replacement=None):
    found = locate(data, sheet, ref)
    old = found['node'].get(q(O, 'value'))
    need(old is not None, 'independent_target_non_numeric')
    return {'sheet': found['sheet_name'], 'cell': ref, 'expected': old,
            'value': str(Decimal(old) + Decimal(1)) if replacement is None else replacement}


def validation_bounds(data):
    found = locate(data)
    identity = found['node'].get(q(TB, 'content-validation-name'))
    definitions = [n for n in found['body'].iter(q(TB, 'content-validation'))
                   if n.get(q(TB, 'name')) == identity]
    need(identity and len(definitions) == 1, 'independent_validation_identity')
    match = re.fullmatch(r'of:cell-content-is-whole-number\(\) and cell-content-is-between\((-?[0-9]+),(-?[0-9]+)\)',
                         definitions[0].get(q(TB, 'condition'), ''))
    need(match is not None, 'independent_validation_syntax')
    return Decimal(match[1]), Decimal(match[2])


def preservation(source, changed, request):
    before, after = locate(source), locate(changed)
    a, b = before['span'], after['span']
    need(before['raw'][:a['begin']] == after['raw'][:b['begin']], 'raw_prefix_changed')
    need(before['raw'][a['end']:] == after['raw'][b['end']:], 'raw_suffix_changed')
    need(before['raw'][a['begin']:a['end']] != after['raw'][b['begin']:b['end']], 'target_raw_unchanged')
    need(before['payloads'].keys() == after['payloads'].keys(), 'member_set_changed')
    need(all(before['payloads'][name] == after['payloads'][name]
             for name in before['payloads'] if name != 'content.xml'), 'noncontent_payload_changed')
    oldattrs, newattrs = dict(before['node'].attrib), dict(after['node'].attrib)
    need(newattrs.pop(q(O, 'value')) == request['value'], 'target_new_numeric_value')
    oldattrs.pop(q(O, 'value'))
    need(oldattrs == newattrs, 'target_identity_type_style_validation_changed')
    oldnodes = list(before['root'].iter())
    newnodes = list(after['root'].iter())
    # Exact raw outside-target identity is stronger than ET semantic comparisons.
    oldcells = [n for n in oldnodes if n.tag in CELL_TAGS and n is not before['node']]
    newcells = [n for n in newnodes if n.tag in CELL_TAGS and n is not after['node']]
    need([ET.tostring(n) for n in oldcells] == [ET.tostring(n) for n in newcells],
         'other_cells_formulas_types_textids_or_caches_changed')
    formulas = [n for n in oldcells if q(TB, 'formula') in n.attrib]
    need(len(formulas) > 0, 'real_formula_input_required')
    structures = {key: len(list(before['root'].iter(tag))) for key, tag in {
        'formula_cells': None, 'validation_definitions': q(TB, 'content-validation'),
        'validation_bindings': None, 'named_ranges': q(TB, 'named-range'),
        'database_ranges': q(TB, 'database-range'), 'filters': q(TB, 'filter'),
        'covered_cells': q(TB, 'covered-table-cell'), 'charts': q(D, 'object')}.items()
        if tag is not None}
    structures['formula_cells'] = len(formulas)
    structures['validation_bindings'] = sum(q(TB, 'content-validation-name') in n.attrib for n in oldcells + [before['node']])
    structures['hidden_rows'] = sum(n.get(q(TB, 'visibility'), 'visible') != 'visible' for n in before['root'].iter(q(TB, 'table-row')))
    structures['merged_anchors'] = sum(any(q(TB, x) in n.attrib for x in ('number-columns-spanned', 'number-rows-spanned')) for n in oldcells)
    return {'target_only_raw_splice': True, 'noncontent_member_payloads_unchanged': True,
            'target_attributes_except_numeric_value_unchanged': True,
            'all_other_cells_and_stored_formula_caches_unchanged': True,
            'structures_preserved_by_exact_raw_identity': structures,
            'cache_recalculation_claimed': False}


def negative_cases(data, label):
    """In-memory derivatives, preserving original data and namespace lexemes."""
    base = spec_for(data)
    stale = dict(base, expected=str(Decimal(base['expected']) + Decimal(2)))
    yield 'expected_mismatch', data, stale, {'cell_expected_mismatch'}, True
    yield 'expected_wrong_type', data, dict(base, expected=Decimal(base['expected'])), {'cell_expected_mismatch'}, True
    for name, replacement in (('numeric_value_wrong_type', 1),
                               ('numeric_value_nonfinite', 'NaN'),
                               ('numeric_value_exponent_limit', '1e301')):
        yield name, data, dict(base,value=replacement), {'invalid_numeric_value','numeric_value_limit'}, True
    _, raw, root, body, sheets = workbook(data)
    for si, sheet in enumerate(sheets):
        formulas = [(r, c, n) for r, c, h, w, n, _ in cells(sheet) if q(TB, 'formula') in n.attrib]
        if formulas:
            r, c, node = formulas[0]
            request = dict(base, sheet=sheet.get(q(TB, 'name')), cell=cellref(r, c),
                           expected=node.get(q(O, 'value'), ''), value='1')
            yield 'formula_target', data, request, {'unsupported_target_cell'}, True
            break
    yield 'repeated_target', attr(data, choose_target, TB, 'number-columns-repeated', '2'), base, {'repeated_target_cell'}, label == 'S01'
    yield 'protected_target', attr(data, choose_target, TB, 'protect', 'true'), base, {'unsupported_target_cell'}, label == 'S01'
    yield 'protected_sheet', attr(data, lambda r,b,s:s[0], TB, 'protected', 'true'), base, {'protected_sheet'}, label == 'S01'
    yield 'unknown_target_attribute', attr(data, choose_target, TB, 'unsupported-test-attribute', 'true'), base, {'unsupported_target_attributes'}, label == 'S01'
    # Inert-looking unknown XML still has to be rejected by the rich admission.
    bodyspan = node_span(raw, root, body)
    close = raw.rfind(b'</', bodyspan['begin'], bodyspan['end'])
    unknown = raw[:close] + ('<table:unknown-test-node xmlns:table="' + TB + '"/>').encode() + raw[close:]
    if label == 'S11':
        yield 'unknown_document_attribute', attr(data, lambda r,b,s:r, TB, 'unsupported-test-attribute', 'true'), base, set(), False
        yield 'unknown_xml_structure', rewrite(data, 'content.xml', unknown), base, set(), False
    # A real active source record, never executed, and external xml:base.
    first = node_span(raw, root, sheets[0])
    active = raw[:first['opening_end']] + ('<table:table-source xmlns:table="' + TB + '"/>').encode() + raw[first['opening_end']:]
    yield 'active_table_source', rewrite(data, 'content.xml', active), base, {'unsupported_preserving_edit'}, False
    opening = raw[:first['opening_end']-1] + b' xml:base="https://invalid.example/"' + raw[first['opening_end']-1:]
    yield 'external_xml_base', rewrite(data, 'content.xml', opening), base, {'unsupported_preserving_edit'}, False
    if label != 'S11':
        return
    low, high = validation_bounds(data)
    yield 'validation_out_of_range', data, dict(base, value=str(high + 1)), set(), True
    yield 'validation_noninteger', data, dict(base, value=str(low + Decimal('0.5'))), set(), True
    yield 'validation_dangling', attr(data, choose_target, TB, 'content-validation-name', 'missing_test_validation'), base, set(), False
    choose_validation = lambda r,b,s:next(b.iter(q(TB, 'content-validation')))
    yield 'validation_unknown_attribute', attr(data, choose_validation, TB, 'unknown-test-attribute', '1'), base, set(), False
    yield 'validation_active_condition', attr(data, choose_validation, TB, 'condition', 'of:WEBSERVICE("https://invalid.example/")'), base, set(), False
    validation = next(root.iter(q(TB, 'content-validation')))
    span = node_span(raw, root, validation)
    duplicate = raw[:span['end']] + raw[span['begin']:span['end']] + raw[span['end']:]
    yield 'validation_ambiguous_duplicate', rewrite(data, 'content.xml', duplicate), base, set(), False
    # Missing/unknown style and master references exercise the public ODSError
    # boundary even when a private graph helper uses indexed graph lookups.
    yield 'graph_missing_sheet_style', attr(data, lambda r,b,s:s[0], TB, 'style-name', 'missing_test_style'), base, set(), False
    style_ns = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
    source_style = sheets[0].get(q(TB, 'style-name'))
    choose_sheet_style = lambda r,b,s:next(n for n in r.iter(q(style_ns,'style')) if n.get(q(style_ns,'name')) == source_style)
    yield 'graph_missing_master', attr(data, choose_sheet_style, style_ns, 'master-page-name', 'missing_test_master'), base, set(), False
    # A duplicated source sheet identity must refuse before target selection.
    yield 'graph_duplicate_sheet_name', attr(data, lambda r,b,s:s[1], TB, 'name', sheets[0].get(q(TB,'name'))), base, {'ambiguous_sheet_name'}, False
    obj = lambda r,b,s:next(r.iter(q(D, 'object')))
    yield 'graph_external_object', attr(data, obj, XL, 'href', 'https://invalid.example/foreign'), base, set(), False
    yield 'graph_dangling_object', attr(data, obj, XL, 'href', './MissingObject'), base, set(), False
    node = next(root.iter(q(D, 'object')))
    span = node_span(raw, root, node)
    duplicated = raw[:span['end']] + raw[span['begin']:span['end']] + raw[span['end']:]
    yield 'graph_ambiguous_object', rewrite(data, 'content.xml', duplicated), base, set(), False
    names = list(root.iter(q(TB, 'named-range')))
    if names:
        span = node_span(raw, root, names[0])
        duplicate = raw[:span['end']] + raw[span['begin']:span['end']] + raw[span['end']:]
        yield 'name_ambiguous_duplicate', rewrite(data, 'content.xml', duplicate), base, set(), False
    for si, sheet in enumerate(sheets):
        for r,c,h,w,node,_ in cells(sheet):
            if any(q(TB,n) in node.attrib for n in ('number-columns-spanned','number-rows-spanned')):
                request = dict(base, sheet=sheet.get(q(TB,'name')), cell=cellref(r,c),
                               expected=node.get(q(O,'string-value'), ''.join(node.itertext())), value='1')
                yield 'merge_anchor_target', data, request, {'unsupported_target_cell'}, True
                break
        else:
            continue
        break
    for si, sheet in enumerate(sheets):
        found = next(((r,c) for r,c,h,w,node,_ in cells(sheet) if node.tag == q(TB,'covered-table-cell')), None)
        if found:
            request = dict(base, sheet=sheet.get(q(TB,'name')), cell=cellref(*found), expected='', value='1')
            # The genuine covered run is repeated. Repetition rejects before
            # the covered-cell target guard and is reported precisely.
            yield 'merge_covered_target', data, request, {'unsupported_target_cell','repeated_target_cell'}, True
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-root', '--source-dir', dest='source_dir', type=Path, required=True)
    parser.add_argument('--s01-ods', type=Path)
    parser.add_argument('--s11-ods', type=Path)
    parser.add_argument('--case', action='append', default=[], help='S01:/absolute/input.ods or S11:/absolute/input.ods')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    start = datetime.now(timezone.utc)
    sys.dont_write_bytecode = True
    try:
        args.source_dir = args.source_dir.resolve(strict=True)
    except OSError:
        raise CliGuardError('native_root_unavailable') from None
    check_stand(args.source_dir)
    paths = {}
    for label,path in (('S01',args.s01_ods),('S11',args.s11_ods)):
        if path is not None:
            paths[label] = path
    for item in args.case:
        cli_need(':' in item, 'case_argument_invalid')
        label, path = item.split(':',1)
        cli_need(label in {'S01','S11'} and label not in paths, 'case_label_invalid_or_duplicate')
        paths[label] = Path(path)
    cli_need(paths, 'case_input_required')
    sourcepins = source_pins(args.source_dir)
    report_fd = reserve_report(args.report,args.source_dir,paths.values())
    sys.path.insert(0, str(args.source_dir))
    from tools import scoped_ods as ods
    from tools import scoped_spreadsheet_profiles as profiles
    report = {'schema':'friday.ods.independent.pure-parser-tests.v1',
              'started_utc':start.isoformat(), 'source_sha256':sourcepins,
              'package_initializers': {name: {'empty': (args.source_dir / name).read_bytes() == b''}
                                       for name in ('tools/__init__.py','hermes_cli/__init__.py')},
              'runner_sha256':sha(Path(__file__).read_bytes()),
              'source_pin_scope':'explicit finite pure-parser source closure; no source-root traversal',
              'empty_package_initializers_verified_before_imports':True,
              'report_destination':'new exclusive no-follow 0600 file outside source and input files; private owned parent',
              'scope':'source-only pure parser; actual modules; no Office/runtime/model/network/send/IPC',
              'private_evidence': True, 'cases':[], 'failures':[]}
    for label, path in paths.items():
        pin_before = state(path)
        data = path.read_bytes()
        case = {'label':label, 'input_pin':pin_before, 'positive':{}, 'negatives':[]}
        request = spec_for(data)
        positive = {}
        for channel, call in (('direct',lambda d,s:ods.edit_spreadsheet(d,s)),
                              ('profile',lambda d,s:profiles.edit(d,'ods',s))):
            try:
                changed = call(data, request)
                facts = preservation(data,changed,request)
                readback = ods.extract_spreadsheet(changed)
                metadata = readback.extraction_metadata
                formula_records = []
                current_sheet = None
                target_records = []
                for line in str(readback).splitlines():
                    sheetline = re.fullmatch(r'\[SHEET (.*)\]',line)
                    if sheetline:
                        current_sheet = json.loads(sheetline[1])
                    match = re.fullmatch(r'\[([A-Z]+[1-9][0-9]*) (\{.*\})\]',line)
                    if match:
                        value = json.loads(match[2])
                        if 'formula' in value:
                            formula_records.append(value)
                        if current_sheet == request['sheet'] and match[1] == request['cell']:
                            target_records.append(value)
                need(len(formula_records) == facts['structures_preserved_by_exact_raw_identity']['formula_cells'], 'readback_formula_count')
                need(all(v.get('cache_status') == 'cached_not_recalculated' for v in formula_records), 'readback_cache_disclosure')
                need(metadata.get('formulas_evaluated') is False, 'readback_evaluation_disclosure')
                need(len(target_records) == 1 and target_records[0]['type'] == 'float'
                     and target_records[0]['value'] == request['value'], 'readback_target_numeric_value')
                facts.update(status='PASS', output_sha256=sha(changed), output_bytes=len(changed),
                             readback_formulas=len(formula_records), readback_formulas_evaluated=False,
                             readback_cache_status='cached_not_recalculated',
                             readback_target_numeric_value_verified=True,
                             readback_unsupported=metadata.get('unsupported'))
                positive[channel] = changed
                case['positive'][channel] = facts
            except ods.ODSError as error:
                case['positive'][channel] = {'status':'REFUSED','code':str(error)}
                report['failures'].append(label + '_' + channel + '_positive_refused')
            except AssertionError as error:
                case['positive'][channel] = {'status':'FAIL','assertion':str(error)}
                report['failures'].append(label + '_' + channel + '_' + str(error))
        if len(positive) == 2:
            case['dispatch_bytes_identical'] = positive['direct'] == positive['profile']
            if not case['dispatch_bytes_identical']:
                report['failures'].append(label + '_dispatch_output_mismatch')
            # A valid second edit consumes the first edited bytes with their
            # honestly stale caches. Restore the original numeric value; this
            # is always inside the original integer validation, when present.
            try:
                second_request = spec_for(positive['direct'],replacement=request['expected'])
                second = ods.edit_spreadsheet(positive['direct'],second_request)
                facts = preservation(positive['direct'],second,second_request)
                facts.update(status='PASS',output_sha256=sha(second),operation='second_numeric_edit_with_stale_caches')
                case['second_edit'] = facts
            except ods.ODSError as error:
                case['second_edit'] = {'status':'REFUSED','code':str(error)}
                report['failures'].append(label + '_second_edit_refused')
            except AssertionError as error:
                case['second_edit'] = {'status':'FAIL','assertion':str(error)}
                report['failures'].append(label + '_second_edit_' + str(error))
        for name, derived, request, expected_codes, localized in negative_cases(data,label):
            entry = {'name':name, 'input_sha256':sha(derived), 'derived_from_original':derived != data,
                     'requires_localized_guard':localized, 'paths':{}}
            for channel, call in (('direct',lambda d,s:ods.edit_spreadsheet(d,s)),
                                  ('profile',lambda d,s:profiles.edit(d,'ods',s))):
                try:
                    output = call(derived, request)
                    entry['paths'][channel] = {'status':'UNEXPECTED_ACCEPT','output_sha256':sha(output)}
                    report['failures'].append(label + '_' + name + '_' + channel + '_accepted')
                except ods.ODSError as error:
                    code = str(error)
                    is_local = code in expected_codes if expected_codes else (
                        name.startswith('validation_') and ('validation' in code or 'constraint' in code))
                    entry['paths'][channel] = {'status':'REFUSED','code':code,
                                              'localized_guard_observed':is_local}
                    if localized and not is_local:
                        report['failures'].append(label + '_' + name + '_' + channel + '_not_localized')
                except Exception as error:
                    entry['paths'][channel] = {'status':'UNEXPECTED_EXCEPTION','exception_type':type(error).__name__}
                    report['failures'].append(label + '_' + name + '_' + channel + '_exception')
            entry['dispatch_refusal_identical'] = entry['paths']['direct'] == entry['paths']['profile']
            if not entry['dispatch_refusal_identical']:
                report['failures'].append(label + '_' + name + '_dispatch_refusal_mismatch')
            case['negatives'].append(entry)
        case['original_input_immutable'] = state(path) == pin_before
        if not case['original_input_immutable']:
            report['failures'].append(label + '_original_input_mutated')
        report['cases'].append(case)
    finalpins = source_pins(args.source_dir)
    report['loaded_source_origins'] = loaded_origins(args.source_dir)
    report['source_unchanged_during_run'] = sourcepins == finalpins
    if not report['source_unchanged_during_run']:
        report['failures'].append('source_changed_during_run')
    report['state'] = 'PASS_SOURCE_ONLY' if not report['failures'] else 'FAIL_SOURCE_ONLY'
    end = datetime.now(timezone.utc)
    report.update(finished_utc=end.isoformat(),elapsed_seconds=(end-start).total_seconds())
    with os.fdopen(report_fd,'w',encoding='utf-8') as output:
        output.write(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'state':report['state'],'case_count':len(report['cases']),
                      'negative_control_count':sum(len(c['negatives']) for c in report['cases']),
                      'failures':report['failures']}))
    return 0 if not report['failures'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except CliGuardError as error:
        print(json.dumps({'state':'REFUSED_CLI_GUARD','code':str(error)}))
        sys.exit(2)
