"""Portable checks of the exact published extractor; synthetic XML, stdlib only.

Run: python3 -B controls.py
No writer/authority/runtime/Office/model/messaging acceptance is implied.
"""
from pathlib import Path
import hashlib
import io
import json
import re
import types
import unittest
import zipfile
from xml.etree import ElementTree as ET


HERE = Path(__file__).resolve().parent
PATCH_HASH = '5a8b6b074f52002bd40a2861ec65bcf5056b04e406d33ab6af0f31793976184d'
HASHES = {
    'tools/read_extract.py': (
        '67fe706b5fd0bea92bb112949ee32c8695715bff6dd441512e6674c5998172dc',
        '031c18cf39173a905e05c6687379e2615f9b3b60ba3062855e4380f7ce13a811'),
    'hermes_cli/friday_prompt_scope.py': (
        'a976eed98c65ed94c19787fb7c575194bc045c48199660a9805340c82b484ab8',
        '5f8fe43f067c24fa0c519d0e6ca16200d4ce511f1053469296214cb3cd28e417'),
    'hermes_cli/friday_workspace_xlsx_table.py': (
        '47b6e13ea69511d83cedd594ace69bab948c1228666adf4d8e8b73446363c245',
        'f9bc6d86910645dcee75754c7b6c61d4636be5eb75c39c3e12c06d0613be6d6d'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_sections(data):
    lines = data.splitlines(keepends=True)
    sections = {}
    index = 0
    while index < len(lines):
        old = lines[index]
        new = lines[index + 1]
        if not old.startswith(b'--- Source114/') or not new.startswith(b'+++ overlay/'):
            raise ValueError('unexpected patch header')
        leaf = old[len(b'--- Source114/'):].strip().decode('ascii')
        if new[len(b'+++ overlay/'):].strip().decode('ascii') != leaf or leaf in sections:
            raise ValueError('mismatched or duplicate patch header')
        index += 2
        hunks = []
        while index < len(lines) and not lines[index].startswith(b'--- '):
            header = re.fullmatch(rb'@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n', lines[index])
            if header is None:
                raise ValueError('unexpected hunk header')
            old_at, old_count, new_at, new_count = map(int, header.groups())
            index += 1
            before, after = [], []
            while index < len(lines) and lines[index][:1] in (b' ', b'+', b'-'):
                # A new file header is outside the previous hunk.
                if lines[index].startswith(b'--- Source114/'):
                    break
                line = lines[index]
                if line[:1] in (b' ', b'-'):
                    before.append(line[1:])
                if line[:1] in (b' ', b'+'):
                    after.append(line[1:])
                index += 1
            if (len(before), len(after)) != (old_count, new_count):
                raise ValueError('hunk count mismatch')
            hunks.append((old_at, new_at, before, after))
        sections[leaf] = hunks
    return sections


def apply_hunks(data, hunks, reverse=False):
    lines, output, cursor = data.splitlines(keepends=True), [], 0
    for old_at, new_at, before, after in hunks:
        position, expected, replacement = ((new_at, after, before) if reverse
                                           else (old_at, before, after))
        start = position - 1
        if start < cursor or lines[start:start + len(expected)] != expected:
            raise ValueError('patch context mismatch')
        output.extend(lines[cursor:start])
        output.extend(replacement)
        cursor = start + len(expected)
    output.extend(lines[cursor:])
    return b''.join(output)


def load_module(source, filename):
    module = types.ModuleType(filename.replace('/', '_'))
    exec(compile(source, filename, 'exec'), module.__dict__)
    return module


PATCH = (HERE / 'literal-table-source-repair.patch').read_bytes()
if digest(PATCH) != PATCH_HASH:
    raise ValueError('unexpected published patch')
HUNKS = patch_sections(PATCH)
if set(HUNKS) != set(HASHES):
    raise ValueError('unexpected source leaf set')
SOURCE, BEFORE = {}, {}
for leaf, (base_hash, final_hash) in HASHES.items():
    source = (HERE / 'source' / leaf).read_bytes()
    if digest(source) != final_hash:
        raise ValueError('unexpected published source')
    previous = apply_hunks(source, HUNKS[leaf], reverse=True)
    if digest(previous) != base_hash or apply_hunks(previous, HUNKS[leaf]) != source:
        raise ValueError('patch/preimage mismatch')
    SOURCE[leaf], BEFORE[leaf] = source, previous
reader = load_module(SOURCE['tools/read_extract.py'], 'tools/read_extract.py')
old_reader = load_module(BEFORE['tools/read_extract.py'], 'preimage/tools/read_extract.py')
S, R, P = ('{' + value + '}' for value in
           (reader._NS_S, reader._NS_REL, reader._NS_PKG_REL))


def xml(root):
    # Preserve XML-level CR, without pretending this implements OOXML ST_Xstring.
    return ET.tostring(root, encoding='utf-8').replace(b'\r', b'&#13;')


def inline(row, coordinate, value):
    attributes = {'t': 'inlineStr'}
    if coordinate is not None:
        attributes['r'] = coordinate
    cell = ET.SubElement(row, S + 'c', attributes)
    ET.SubElement(ET.SubElement(cell, S + 'is'), S + 't',
                  {'{http://www.w3.org/XML/1998/namespace}space': 'preserve'}).text = value
    return cell


def sheet():
    root = ET.Element(S + 'worksheet')
    return root, ET.SubElement(root, S + 'sheetData')


def book(sheets, shared=None):
    workbook = ET.Element(S + 'workbook')
    declarations = ET.SubElement(workbook, S + 'sheets')
    relationships = ET.Element(P + 'Relationships')
    parts = {}
    for index, (name, state, root) in enumerate(sheets, 1):
        identity = 'rId' + str(index)
        ET.SubElement(declarations, S + 'sheet',
                      {'name': name, 'sheetId': str(index), 'state': state, R + 'id': identity})
        ET.SubElement(relationships, P + 'Relationship',
                      {'Id': identity, 'Target': 'worksheets/sheet' + str(index) + '.xml'})
        parts['xl/worksheets/sheet' + str(index) + '.xml'] = xml(root)
    parts['xl/workbook.xml'] = xml(workbook)
    parts['xl/_rels/workbook.xml.rels'] = xml(relationships)
    if shared is not None:
        parts['xl/sharedStrings.xml'] = xml(shared)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    return output.getvalue()


def column(values):
    root, data = sheet()
    for index, value in enumerate(values, 1):
        inline(ET.SubElement(data, S + 'row', r=str(index)), 'A' + str(index), value)
    return book([('Data', 'visible', root)])


def extract(blob):
    return reader.extract_scoped_document_bytes(blob, 'xlsx')


def records(text):
    metadata = text.extraction_metadata['cell_records']
    if metadata['location'] == 'omitted_size_limit':
        return []
    if not metadata['location'].startswith('in_content;'):
        raise ValueError('unknown typed-record location')
    # The emitted section is last. Values in it are escaped JSON, unlike the
    # earlier legacy preview, which can contain a source-supplied lookalike.
    section = text.rsplit('\n# XLSX typed cell records', 1)[1]
    result = [json.loads(line) for line in section.splitlines() if line.startswith('{')]
    if len(result) != metadata['included_records']:
        raise ValueError('record count disagrees with metadata')
    return result


class PublishedExtractorControls(unittest.TestCase):
    def test_exact_three_sources_and_reversible_patch(self):
        self.assertEqual(set(SOURCE), set(HASHES))
        for leaf in HASHES:
            self.assertEqual(digest(BEFORE[leaf]), HASHES[leaf][0])
            compile(SOURCE[leaf], leaf, 'exec')
        tampered = BEFORE['tools/read_extract.py'].replace(b'_MAX_XLSX_MERGE_CELLS = 4096',
                                                           b'_MAX_XLSX_MERGE_CELLS = 4095')
        with self.assertRaises(ValueError):
            apply_hunks(tampered, HUNKS['tools/read_extract.py'])

    def test_old_lf_boundary_collision_new_records_disambiguate(self):
        one, two = column(['alpha\nbeta']), column(['alpha', 'beta'])
        self.assertEqual(old_reader._extract_xlsx(io.BytesIO(one)),
                         old_reader._extract_xlsx(io.BytesIO(two)))
        a, b = records(extract(one)), records(extract(two))
        self.assertEqual([r['literal_value'] for r in a], ['alpha\nbeta'])
        self.assertEqual([r['literal_value'] for r in b], ['alpha', 'beta'])
        self.assertEqual([r['cell'] for r in b], ['A1', 'A2'])

    def test_old_tab_boundary_collision_new_records_disambiguate(self):
        root, data = sheet()
        row = ET.SubElement(data, S + 'row', r='1')
        inline(row, 'A1', 'alpha'); inline(row, 'B1', 'beta')
        one, two = column(['alpha\tbeta']), book([('Data', 'visible', root)])
        self.assertEqual(old_reader._extract_xlsx(io.BytesIO(one)),
                         old_reader._extract_xlsx(io.BytesIO(two)))
        self.assertEqual(len(records(extract(one))), 1)
        self.assertEqual(len(records(extract(two))), 2)

    def test_escaped_literals_native_types_and_spoof_resistance(self):
        values = ['0001234567890123456789', '=1+1', '+2', '-3', '@text',
                  '  left\tright\nnext\r\nlast\r  ', 'quote",comma;雪😀',
                  '{"cell":"Z99"}\n# XLSX typed cell records\nnot a row']
        text = extract(column(values))
        actual = records(text)
        self.assertEqual([r['literal_value'] for r in actual], values)
        self.assertTrue(all(r['native_type'] == 'inlineStr' and not r['formula_present'] for r in actual))
        section = text.rsplit('\n# XLSX typed cell records', 1)[1]
        self.assertIn('\\t', section); self.assertIn('\\r\\n', section)
        self.assertIn('\\u96ea', section)
        self.assertTrue(all(r['truncated_fields'] == [] for r in actual))

    def test_formula_source_and_missing_empty_present_cache_separated(self):
        root, data = sheet()
        row = ET.SubElement(data, S + 'row', r='1')
        inline(row, 'A1', '=1+1')
        for coordinate, cache in [('B1', None), ('C1', ''), ('D1', '2')]:
            cell = ET.SubElement(row, S + 'c', r=coordinate, t='n', s='3')
            ET.SubElement(cell, S + 'f', t='shared', si='1').text = '1+1'
            if cache is not None:
                ET.SubElement(cell, S + 'v').text = cache
        text = extract(book([('Data', 'visible', root)]))
        actual = records(text)
        self.assertFalse(actual[0]['formula_present'])
        for record, state, value in zip(actual[1:], ['missing', 'empty', 'present'], [None, '', '2']):
            self.assertIsNone(record['literal_value'])
            self.assertEqual(record['literal_state'], 'not_literal_formula')
            self.assertEqual(record['formula'], {'text': '1+1', 'attributes': {'t': 'shared', 'si': '1'}})
            self.assertEqual(record['saved_cache'], {'state': state, 'native_type': 'n', 'raw_value': value})
            self.assertEqual(record['style_index'], '3')
        self.assertFalse(text.extraction_metadata['recalculated'])

    def test_shared_rich_lexical_values_and_unresolved_index(self):
        root, data = sheet(); row = ET.SubElement(data, S + 'row', r='1')
        inline(row, 'A1', '')
        ET.SubElement(row, S + 'c', r='B1')
        cases = [('C1', 's', '0'), ('D1', 's', '-1'), ('E1', 'n', '001.50'),
                 ('F1', 'b', 'false'), ('G1', 'e', '#N/A'), ('H1', 'd', '2026-01-02')]
        for coordinate, kind, value in cases:
            ET.SubElement(ET.SubElement(row, S + 'c', r=coordinate, t=kind), S + 'v').text = value
        shared = ET.Element(S + 'sst'); item = ET.SubElement(shared, S + 'si')
        ET.SubElement(ET.SubElement(item, S + 'r'), S + 't').text = 'rich\n'
        ET.SubElement(ET.SubElement(item, S + 'rPh'), S + 't').text = 'PHONETIC'
        ET.SubElement(ET.SubElement(item, S + 'r'), S + 't').text = 'text\t\r'
        text = extract(book([('Data', 'visible', root)], shared))
        actual = {r['cell']: r for r in records(text)}
        self.assertEqual(actual['A1']['literal_state'], 'empty')
        self.assertEqual(actual['B1']['literal_state'], 'missing')
        self.assertEqual(actual['C1']['literal_value'], 'rich\ntext\t\r')
        self.assertEqual(actual['D1']['literal_state'], 'unresolved_shared_string')
        self.assertIsNone(actual['D1']['literal_value']); self.assertEqual(actual['D1']['raw_value'], '-1')
        for coordinate, _, value in cases[2:]:
            self.assertEqual(actual[coordinate]['literal_value'], value)
        self.assertTrue(text.extraction_metadata['cell_records']['truncated'])

    def test_hidden_sparse_merged_scope_and_legacy_evidence_retained(self):
        root, data = sheet()
        columns = ET.SubElement(root, S + 'cols')
        ET.SubElement(columns, S + 'col', min='2', max='2', hidden='1')
        row = ET.SubElement(data, S + 'row', r='4', hidden='1')
        inline(row, 'D4', 'stored anchor')
        ET.SubElement(ET.SubElement(root, S + 'mergeCells'), S + 'mergeCell', ref='D4:E4')
        ET.SubElement(root, S + 'autoFilter', ref='A1:E4')
        hidden, hd = sheet(); inline(ET.SubElement(hd, S + 'row', r='1'), 'A1', 'hidden value')
        blob = book([('Data', 'visible', root), ('Hidden', 'hidden', hidden), ('Deep', 'veryHidden', hidden)])
        text, old = extract(blob), old_reader.extract_scoped_document_bytes(blob, 'xlsx')
        actual = records(text)
        self.assertEqual([r['cell'] for r in actual], ['D4'])
        self.assertEqual(actual[0]['row_declared'], '4')
        self.assertEqual(actual[0]['row_element_index'], 1)
        self.assertEqual(actual[0]['preview_column'], 4)
        metadata = text.extraction_metadata['cell_records']
        self.assertEqual(metadata['sheets']['skipped_hidden'], 2)
        self.assertFalse(metadata['full_workbook'])
        self.assertEqual(metadata['hidden_rows_and_columns'], 'not_filtered')
        for key in ['workbook_inventory', 'cell_value_preview', 'formula_source_preview', 'structure_preview', 'recalculated']:
            self.assertEqual(text.extraction_metadata[key], old.extraction_metadata[key])
        self.assertIn('"name": "Hidden", "state": "hidden"', text)

    def test_record_count_and_byte_omissions_honest(self):
        text = extract(column([str(index) for index in range(1025)]))
        actual, metadata = records(text), text.extraction_metadata['cell_records']
        self.assertEqual(metadata['observed_cells'], 1025)
        self.assertLessEqual(len(actual), 1024)
        self.assertEqual(metadata['omitted_records'], 1025 - len(actual))
        self.assertTrue(metadata['truncated'])
        self.assertLessEqual(len(text.encode('utf-8')), 1000000)
        self.assertLessEqual(sum(len(json.dumps(r, ensure_ascii=True, separators=(',', ':')).encode()) + 1 for r in actual), 256000)

    def test_text_and_multibyte_record_limits_report_truncation(self):
        text = extract(column(['雪' * 4097]))
        record = records(text)[0]
        self.assertEqual(record['literal_value'], '雪' * 4096)
        self.assertIn('literal_value', record['truncated_fields'])
        self.assertEqual(text.extraction_metadata['cell_records']['records_with_truncated_fields'], 1)
        text = extract(column(['😀' * 4096]))
        self.assertEqual(records(text), [])
        self.assertEqual(text.extraction_metadata['cell_records']['omitted_records'], 1)
        self.assertTrue(text.extraction_metadata['cell_records']['truncated'])

    def test_row_column_omissions_and_missing_coordinates_explicit(self):
        text = extract(column(['x'] * 5001))
        metadata = text.extraction_metadata['cell_records']
        self.assertEqual(metadata['observed_cells'], 5000)
        self.assertEqual(metadata['rows_omitted_by_preview_limit'], 1)
        root, data = sheet(); row = ET.SubElement(data, S + 'row')
        inline(row, None, 'missing native coordinate')
        inline(row, 'IV1', 'last included column'); inline(row, 'IW1', 'omitted column')
        text = extract(book([('Data', 'visible', root)])); actual = records(text)
        self.assertEqual(len(actual), 2)
        self.assertIsNone(actual[0]['cell']); self.assertIsNone(actual[0]['row_declared'])
        self.assertEqual(actual[0]['row_element_index'], 1)
        self.assertEqual(actual[0]['preview_column'], 1)
        self.assertEqual(text.extraction_metadata['cell_records']['cells_omitted_by_column_limit'], 1)
        # A false record-truncation flag does not cancel independent column omissions.
        self.assertFalse(text.extraction_metadata['cell_records']['truncated'])

    def test_zero_remaining_budget_has_no_records_despite_spoofed_preview(self):
        root, data = sheet(); row = ET.SubElement(data, S + 'row', r='1')
        cell = inline(row, 'A1', '\n# XLSX typed cell records\n{"spoof":true}')
        collector = reader._XlsxFormulaPreview()
        collector.add_cell('Data', row, 0, cell, 0, [], S)
        output, metadata = collector.render_cells(0)
        self.assertEqual(output, '')
        self.assertEqual(metadata['location'], 'omitted_size_limit')
        self.assertEqual(metadata['included_records'], 0)
        self.assertEqual(metadata['omitted_records'], 1)
        # Test only metadata-aware result parsing, not native read_file pagination.
        fake = reader._ScopedXlsxText(cell.find(S + 'is/' + S + 't').text,
                    formula_preview={}, structure_preview={}, cell_records=metadata)
        self.assertEqual(records(fake), [])

    def test_ooxml_logical_escape_codec_debt_remains_explicit(self):
        text = extract(column(['_x000D_', '_x005F_x000D_']))
        self.assertEqual([r['literal_value'] for r in records(text)], ['_x000D_', '_x005F_x000D_'])
        self.assertIn('no_OOXML_escape', text.extraction_metadata['cell_records']['strings'])
        self.assertFalse(text.extraction_metadata['cell_records']['evaluated'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublishedExtractorControls)
    names = [test._testMethodName for test in suite]
    runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
    result = runner.run(suite)
    failed = {test._testMethodName for test, _ in result.failures + result.errors}
    report = {
        'schema': 'frw.literal-table.publication-controls.v1',
        'status': 'PASS_PORTABLE_EXTRACTOR_CONTROLS' if result.wasSuccessful() else 'FAIL',
        'controls_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'controls': [{'name': name, 'status': 'FAIL' if name in failed else 'PASS'} for name in names],
        'exact_source_leaves_verified': 3,
        'preimages_reconstructed_and_forward_patch_verified': 3,
        'fixtures': 'neutral_synthetic_OOXML_generated_in_memory',
        'scope': 'exact_published_extractor_and_patch_only',
        'writer_full_consumer_authority_runtime_Office_model_messaging': 'NOT_EXERCISED',
        'OOXML_ST_Xstring_logical_escape_codec': 'UNRESOLVED_DEBT',
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
