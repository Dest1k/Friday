#!/usr/bin/env python3
"""Portable synthetic mutants; no received artifact, Office or user task.

The source is generated locally from the already-public rich workbook.
All generated workbooks are removed by unittest module cleanup.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = None
WORK = None
spec = importlib.util.spec_from_file_location('assessment', ROOT / 'source/assess_received_s18.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
M, R, P = A.M, A.R, A.P
S1, S2 = 'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml'
WB, WBR = 'xl/workbook.xml', 'xl/_rels/workbook.xml.rels'
CHART, TABLE = 'xl/charts/chart1.xml', 'xl/tables/table1.xml'
OUTCOMES = []


def setUpModule():
    global SOURCE, WORK
    temporary = tempfile.TemporaryDirectory(prefix='.received-test-', dir=ROOT)
    unittest.addModuleCleanup(temporary.cleanup)
    WORK = Path(temporary.name)
    SOURCE = WORK / 'synthetic_source.xlsx'
    spec = importlib.util.spec_from_file_location('public_prepare', ROOT / 'source/prepare_fixture.py')
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    prepare.prepare(ROOT / 'fixtures/source/orders_rich_table.xlsx', SOURCE)
    if A.sha(SOURCE) != A.SOURCE_SHA256:
        raise AssertionError('Generated public source differs from the known source')


def tearDownModule():
    if SOURCE is not None and A.sha(SOURCE) != A.SOURCE_SHA256:
        raise AssertionError('Synthetic source was modified during the controls')


def fixture_parts():
    with zipfile.ZipFile(SOURCE) as z:
        return {name: z.read(name) for name in z.namelist()}


def xml_edit(parts, name, change):
    tree = ET.fromstring(parts[name])
    change(tree)
    parts[name] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)


def cell_change(parts, sheet, address, value, formula=False):
    def change(root):
        node = next(n for n in root.iter() if n.tag == '{'+M+'}c' and n.get('r') == address)
        target = node.find('{'+M+'}f' if formula else '{'+M+'}v')
        assert target is not None
        target.text = value
    xml_edit(parts, sheet, change)


def proper_parts():
    parts = fixture_parts()
    cell_change(parts, S1, 'C3', '4')
    return parts


def write_assess(label, parts):
    path = WORK / (label + '.xlsx')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    report = A.assess(SOURCE, path)
    report['synthetic_own_mutant'] = True
    OUTCOMES.append({'control': label, 'structural_outcome': report['structural_outcome'],
                     'features': {k: [r['status'] for r in rows] for k, rows in report['features'].items()}})
    return report


def feature_status(report, name):
    return [r['status'] for r in report['features'][name]]


class AssessmentControls(unittest.TestCase):
    def test_01_requested_edit(self):
        r = write_assess('positive_requested_edit', proper_parts())
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')
        self.assertTrue(r['source_data_and_formula_sources']['declared_edit_observed'])
        self.assertEqual(r['user_acceptance'], 'UNACCEPTED')

    def test_02_reorder_sheets_and_scope(self):
        parts = proper_parts()
        def change(root):
            sheets = root.find('{'+M+'}sheets')
            sheets[:] = list(reversed(sheets[:]))
            for n in root.findall('./{'+M+'}definedNames/{'+M+'}definedName'):
                if 'localSheetId' in n.attrib:
                    n.set('localSheetId', '1')
        xml_edit(parts, WB, change)
        r = write_assess('positive_reordered_sheets', parts)
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')

    def test_03_rewrite_part_names(self):
        parts = proper_parts()
        replacements = {S1: 'xl/worksheets/renamed_orders.xml', S2: 'xl/worksheets/renamed_summary.xml',
                        CHART: 'xl/charts/renamed_chart.xml', TABLE: 'xl/tables/renamed_table.xml',
                        WB: 'xl/renamed_workbook.xml', WBR: 'xl/_rels/renamed_workbook.xml.rels',
                        'xl/drawings/drawing1.xml': 'xl/drawings/renamed_drawing.xml',
                        'xl/worksheets/_rels/sheet1.xml.rels': 'xl/worksheets/_rels/renamed_orders.xml.rels',
                        'xl/worksheets/_rels/sheet2.xml.rels': 'xl/worksheets/_rels/renamed_summary.xml.rels',
                        'xl/drawings/_rels/drawing1.xml.rels': 'xl/drawings/_rels/renamed_drawing.xml.rels'}
        parts = {replacements.get(name, name): data for name, data in parts.items()}
        text_changes = {'/xl/worksheets/sheet1.xml': '/xl/worksheets/renamed_orders.xml',
                        'xl/workbook.xml': 'xl/renamed_workbook.xml',
                        '/xl/worksheets/sheet2.xml': '/xl/worksheets/renamed_summary.xml',
                        '/xl/charts/chart1.xml': '/xl/charts/renamed_chart.xml',
                        '/xl/drawings/drawing1.xml': '/xl/drawings/renamed_drawing.xml',
                        '../tables/table1.xml': '../tables/renamed_table.xml',
                        '/xl/tables/table1.xml': '/xl/tables/renamed_table.xml'}
        for name in parts:
            for before, after in text_changes.items():
                parts[name] = parts[name].replace(before.encode(), after.encode())
        r = write_assess('positive_renamed_parts', parts)
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')

    def test_04_cache_metadata_numeric_and_added_sheet(self):
        parts = proper_parts()
        cell_change(parts, S1, 'C3', '4.000')
        cell_change(parts, S1, 'G3', '1999.60')
        parts['docProps/core.xml'] = parts['docProps/core.xml'].replace(b'2026-', b'2027-')
        xml_edit(parts, WB, lambda root: ET.SubElement(root.find('{'+M+'}sheets'), '{'+M+'}sheet',
                 {'name': 'Notes', 'sheetId': '91', '{'+R+'}id': 'rNew'}))
        xml_edit(parts, WBR, lambda root: ET.SubElement(root, '{'+P+'}Relationship',
                 {'Id': 'rNew', 'Type': R+'/worksheet', 'Target': 'worksheets/notes.xml'}))
        parts['xl/worksheets/notes.xml'] = ('<worksheet xmlns="'+M+'"><sheetData><row r="1"><c r="A1"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>').encode()
        xml_edit(parts, '[Content_Types].xml', lambda root: ET.SubElement(root, '{http://schemas.openxmlformats.org/package/2006/content-types}Override',
                 {'PartName': '/xl/worksheets/notes.xml', 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'}))
        xml_edit(parts, WB, lambda root: ET.SubElement(root.find('{'+M+'}definedNames'), '{'+M+'}definedName', {'name': 'AdditionalHarmlessName'}).__setattr__('text', "'Orders'!$A$1"))
        r = write_assess('positive_cache_metadata_extra_sheet_formula', parts)
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')
        self.assertEqual(r['source_data_and_formula_sources']['additions_for_review_not_automatic_failure'],
                         [{'sheet': 'Notes', 'scope': 'additional sheet'}])

    def test_05_equivalent_reference_and_split_validation(self):
        parts = proper_parts()
        def validation(root):
            parent = root.find('{'+M+'}dataValidations')
            rule = parent[0]
            rule.set('sqref', 'C2:C3')
            rule.set('allowBlank', 'false')
            second = copy.deepcopy(rule)
            second.set('sqref', '$C$4:$C$5')
            parent.append(second)
            parent.set('count', '2')
        xml_edit(parts, S1, validation)
        parts[WB] = parts[WB].replace(b"'Orders'!$A$2:$G$5", b'Orders!$A$2:$G$5')
        parts[CHART] = parts[CHART].replace(b"'Orders'!$G$2:$G$5", b'Orders!$G$2:$G$5')
        r = write_assess('positive_equivalent_refs_split_validation', parts)
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')

    def test_06_shared_strings_equivalent(self):
        parts = proper_parts()
        def string_cell(root):
            c = next(n for n in root.iter() if n.tag == '{'+M+'}c' and n.get('r') == 'A3')
            c[:] = []
            c.set('t', 's')
            ET.SubElement(c, '{'+M+'}v').text = '0'
        xml_edit(parts, S1, string_cell)
        parts['xl/strings/reencoded.xml'] = ('<sst xmlns="'+M+'"><si><r><t>00</t></r><r><t>02</t></r></si></sst>').encode()
        xml_edit(parts, '[Content_Types].xml', lambda root: ET.SubElement(root, '{http://schemas.openxmlformats.org/package/2006/content-types}Override',
                 {'PartName': '/xl/strings/reencoded.xml', 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml'}))
        xml_edit(parts, WBR, lambda root: ET.SubElement(root, '{'+P+'}Relationship',
                 {'Id': 'rString', 'Type': R+'/sharedStrings', 'Target': 'strings/reencoded.xml'}))
        r = write_assess('positive_equivalent_shared_strings', parts)
        self.assertEqual(r['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')

    def test_07_missing_or_wrong_declared_edit(self):
        for label, parts in [('negative_no_edit', fixture_parts()), ('negative_wrong_edit', proper_parts())]:
            if label.endswith('wrong_edit'):
                cell_change(parts, S1, 'C3', '5')
            r = write_assess(label, parts)
            self.assertEqual(r['source_data_and_formula_sources']['status'], 'lost')
            self.assertFalse(r['source_data_and_formula_sources']['declared_edit_observed'])

    def test_08_unaffected_data_formula_or_formula_replaced_by_cache(self):
        for mode in ('data', 'formula', 'flattened'):
            parts = proper_parts()
            if mode == 'data':
                cell_change(parts, S1, 'F3', '2')
            elif mode == 'formula':
                cell_change(parts, S1, 'G3', 'C3*D3+1', formula=True)
            else:
                def flatten(root):
                    c = next(n for n in root.iter() if n.tag == '{'+M+'}c' and n.get('r') == 'G3')
                    c.remove(c.find('{'+M+'}f'))
                    c.find('{'+M+'}v').text = '1999.6'
                xml_edit(parts, S1, flatten)
            r = write_assess('negative_unaffected_'+mode, parts)
            self.assertEqual(r['source_data_and_formula_sources']['status'], 'lost')

    def test_09_validation_lost_changed_or_conflicting(self):
        for mode in ('lost', 'changed', 'conflicting'):
            parts = proper_parts()
            def validation(root):
                parent = root.find('{'+M+'}dataValidations')
                if mode == 'lost':
                    root.remove(parent)
                elif mode == 'changed':
                    parent[0].find('{'+M+'}formula2').text = '1000'
                else:
                    duplicate = copy.deepcopy(parent[0])
                    duplicate.set('sqref', 'C3')
                    duplicate.find('{'+M+'}formula2').text = '1000'
                    parent.append(duplicate)
            xml_edit(parts, S1, validation)
            r = write_assess('negative_validation_'+mode, parts)
            self.assertEqual(feature_status(r, 'validation'), ['lost'])

    def test_10_name_scope_or_reference(self):
        for mode in ('scope', 'target', 'missing', 'relative'):
            parts = proper_parts()
            def names(root):
                parent = root.find('{'+M+'}definedNames')
                n = next(n for n in parent if n.get('name') == '_xlnm._FilterDatabase')
                if mode == 'scope':
                    n.set('localSheetId', '1')
                elif mode == 'target':
                    n.text = "'Missing'!A1:G5"
                elif mode == 'relative':
                    n.text = "'Orders'!A1:G5"
                else:
                    parent.remove(n)
            xml_edit(parts, WB, names)
            r = write_assess('negative_name_'+mode, parts)
            self.assertIn('lost', feature_status(r, 'named_ranges'))

    def test_11_chart_orphan_dangling_or_wrong_reference(self):
        for mode in ('orphan', 'dangling', 'reference'):
            parts = proper_parts()
            if mode == 'orphan':
                xml_edit(parts, S2, lambda root: root.remove(root.find('{'+M+'}drawing')))
            elif mode == 'dangling':
                parts['xl/drawings/_rels/drawing1.xml.rels'] = parts['xl/drawings/_rels/drawing1.xml.rels'].replace(b'chart1.xml', b'absent.xml')
            else:
                parts[CHART] = parts[CHART].replace(b"'Orders'!$G$2:$G$5", b"'Orders'!$F$2:$F$5")
            r = write_assess('negative_chart_'+mode, parts)
            self.assertEqual(feature_status(r, 'chart_references'), ['lost'])

    def test_12_table_orphan_dangling_or_wrong_range(self):
        for mode in ('orphan', 'dangling', 'range'):
            parts = proper_parts()
            if mode == 'orphan':
                xml_edit(parts, S1, lambda root: root.remove(root.find('{'+M+'}tableParts')))
            elif mode == 'dangling':
                parts['xl/worksheets/_rels/sheet1.xml.rels'] = parts['xl/worksheets/_rels/sheet1.xml.rels'].replace(b'table1.xml', b'absent.xml')
            else:
                xml_edit(parts, TABLE, lambda root: root.set('ref', 'A1:F5'))
            r = write_assess('negative_table_'+mode, parts)
            self.assertEqual(feature_status(r, 'table_linkage'), ['lost'])

    def test_13_external_relationship_and_formula(self):
        for mode in ('relationship', 'formula', 'table_formula'):
            parts = proper_parts()
            if mode == 'relationship':
                xml_edit(parts, WBR, lambda root: ET.SubElement(root, '{'+P+'}Relationship',
                         {'Id': 'rExternal', 'Type': R+'/externalLink', 'TargetMode': 'External', 'Target': 'file:///not-used.xlsx'}))
            elif mode == 'formula':
                def formula(root):
                    data = root.find('{'+M+'}sheetData')
                    row = ET.SubElement(data, '{'+M+'}row', {'r': '9'})
                    c = ET.SubElement(row, '{'+M+'}c', {'r': 'A9'})
                    ET.SubElement(c, '{'+M+'}f').text = "'[other.xlsx]Sheet1'!A1"
                xml_edit(parts, S2, formula)
            else:
                xml_edit(parts, TABLE, lambda root: ET.SubElement(root.find('./{'+M+'}tableColumns/{'+M+'}tableColumn'), '{'+M+'}calculatedColumnFormula').__setattr__('text', "'[other.xlsx]Sheet1'!A1"))
            r = write_assess('negative_external_'+mode, parts)
            self.assertEqual(r['external_links']['status'], 'present')
            self.assertEqual(r['structural_outcome'], 'STRUCTURAL_CHANGE_REQUIRES_REVIEW')

    def test_14_unsupported_formula_encoding_and_name_expression(self):
        for mode in ('formula', 'name'):
            parts = proper_parts()
            if mode == 'formula':
                xml_edit(parts, S1, lambda root: next(n for n in root.iter() if n.tag == '{'+M+'}f').set('t', 'shared'))
            else:
                xml_edit(parts, WB, lambda root: next(n for n in root.iter() if n.get('name') == 'OrderTotal').__setattr__('text', 'OFFSET(Summary!B6,0,0)'))
            r = write_assess('unsupported_'+mode, parts)
            self.assertEqual(r['structural_outcome'], 'INCOMPLETE_UNSUPPORTED')

    def test_15_unsupported_extended_validation_chart_or_table(self):
        for mode in ('validation', 'chart', 'table'):
            parts = proper_parts()
            if mode == 'validation':
                def extended(root):
                    root.remove(root.find('{'+M+'}dataValidations'))
                    ext = ET.SubElement(root, '{'+M+'}extLst')
                    ET.SubElement(ext, '{http://schemas.microsoft.com/office/spreadsheetml/2009/9/main}dataValidation')
                xml_edit(parts, S1, extended)
                kind = 'validation'
            elif mode == 'chart':
                parts[CHART] = parts[CHART].replace(b"'Orders'!$G$2:$G$5", b'OrderSourceRows')
                kind = 'chart_references'
            else:
                xml_edit(parts, TABLE, lambda root: root.set('ref', 'UnsupportedReference'))
                kind = 'table_linkage'
            r = write_assess('unsupported_'+mode+'_feature', parts)
            self.assertEqual(feature_status(r, kind), ['unsupported'])
            self.assertEqual(r['structural_outcome'], 'INCOMPLETE_UNSUPPORTED')

    def test_16_text_identifier_changed_to_number(self):
        parts = proper_parts()
        def numeric(root):
            c = next(n for n in root.iter() if n.tag == '{'+M+'}c' and n.get('r') == 'A3')
            c[:] = []
            c.set('t', 'n')
            ET.SubElement(c, '{'+M+'}v').text = '2'
        xml_edit(parts, S1, numeric)
        r = write_assess('negative_text_identifier_numeric', parts)
        self.assertEqual(r['source_data_and_formula_sources']['status'], 'lost')


    def test_17_cli_static_report_is_not_user_acceptance(self):
        write_assess('cli_synthetic_edit', proper_parts())
        result = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'source/assess_received_s18.py'),
             '--source', str(SOURCE), '--received', str(WORK / 'cli_synthetic_edit.xlsx')],
            capture_output=True, text=True, check=False, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['scope'], 'SOURCE_ONLY_STATIC')
        self.assertEqual(report['structural_outcome'], 'SOURCE_ORIGIN_STRUCTURALLY_RETAINED')
        self.assertEqual(report['source']['sha256'], A.SOURCE_SHA256)
        self.assertTrue(report['gaps'])

    def test_18_cli_malformed_synthetic_file_is_unknown(self):
        malformed = WORK / 'malformed.xlsx'
        malformed.write_bytes(b'This is a synthetic invalid ZIP')
        result = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'source/assess_received_s18.py'),
             '--source', str(SOURCE), '--received', str(malformed)],
            capture_output=True, text=True, check=False, timeout=15)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)['structural_outcome'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main(verbosity=2)
