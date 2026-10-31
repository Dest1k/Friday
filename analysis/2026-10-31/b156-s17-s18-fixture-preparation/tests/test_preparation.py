"""Portable local controls for synthetic fixtures; no Office or product imports."""
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'fixtures/source'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'source' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load('prepare_fixture', 'prepare_fixture.py')
verify = load('verify_fixture', 'verify_fixture.py')


def archive(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        return {name: z.read(name) for name in z.namelist()}


def changed(members, part, before, after):
    result = dict(members)
    if result[part].count(before) != 1:
        raise AssertionError((part, before))
    result[part] = result[part].replace(before, after, 1)
    return result


class FixtureControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.local-test-', dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.fixture = self.work / 'orders_s18_validation.xlsx'
        prepare.prepare(SOURCES / 'orders_rich_table.xlsx', self.fixture)

    def workbook(self, members):
        path = self.work / 'mutant.xlsx'
        with zipfile.ZipFile(path, 'w') as z:
            for part, data in members.items():
                z.writestr(part, data)
        return verify.Workbook(path)

    def test_s18_exact_reproduction(self):
        self.assertEqual(hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
                         '4038289a6e89c86da8fd547705f9eb98ffbf48566e4dc22652768e405f7dec0d')
        rich = archive(SOURCES / 'orders_rich_table.xlsx')
        fixture = archive(self.fixture)
        self.assertEqual(set(rich), set(fixture))
        self.assertEqual([p for p in rich if rich[p] != fixture[p]], ['xl/worksheets/sheet1.xml'])
        self.assertEqual(fixture['xl/worksheets/sheet1.xml'], rich['xl/worksheets/sheet1.xml'].replace(
            b'<pageMargins', prepare.VALIDATION + b'<pageMargins', 1))
        self.assertEqual(verify.validate_s18(verify.Workbook(self.fixture)), [])

    def test_s17_seed_reconciliation_and_correction_only(self):
        books = [verify.Workbook(SOURCES / name) for name in ('orders_base.xlsx', 'orders_correction_only.xlsx')]
        for book, seedname in zip(books, ('orders_base.json', 'orders_correction_only.json')):
            seed = json.loads((ROOT / 'seeds' / seedname).read_text())
            actual = verify.orders(book)
            self.assertEqual(len(seed['rows']), len(actual))
            for expected, found in zip(seed['rows'], actual):
                self.assertEqual(set(expected), set(found))
                for key in expected:
                    if key in ('qty', 'unit_price', 'revision'):
                        self.assertEqual(Decimal(str(expected[key])), Decimal(found[key]))
                    else:
                        self.assertEqual(expected[key], found[key])
        comparison = verify.compare_s17(*books)
        for key, value in verify.EXPECTED_S17.items():
            self.assertEqual(comparison[key], value, key)
        self.assertEqual(comparison['formulas_before'], verify.EXPECTED_FORMULAS)
        self.assertEqual(comparison['formulas_after'], verify.EXPECTED_FORMULAS)
        self.assertTrue(comparison['text_ids_preserved'])

    def test_s17_wrong_correction_refused(self):
        base = verify.Workbook(SOURCES / 'orders_base.xlsx')
        correction = archive(SOURCES / 'orders_correction_only.xlsx')
        correction['xl/worksheets/sheet1.xml'] = prepare.set_numeric_cell(
            correction['xl/worksheets/sheet1.xml'], 'C3', 5)
        result = verify.compare_s17(base, self.workbook(correction))
        self.assertNotEqual(result['changed_inputs'], verify.EXPECTED_S17['changed_inputs'])
        self.assertNotEqual(result['delta_rub'], verify.EXPECTED_S17['delta_rub'])

    def test_s18_negative_controls(self):
        fixture = archive(self.fixture)
        s1, s2 = 'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml'
        names, chart = 'xl/workbook.xml', 'xl/charts/chart1.xml'
        cases = [
            ('validation_removed', changed(fixture, s1, prepare.VALIDATION, b''), {'validation_rule', 'validation_bounds'}),
            ('validation_bounds_changed', changed(fixture, s1, b'<formula2>100</formula2>', b'<formula2>1000</formula2>'), {'validation_bounds'}),
            ('named_range_target_missing', changed(fixture, names, b"'Orders'!$A$2:$G$5", b"'Missing'!$A$2:$G$5"), {'defined_names', 'defined_name_targets', 'defined_name_scope'}),
            ('named_range_renamed', changed(fixture, names, b'name="OrderTotal"', b'name="RenamedTotal"'), {'defined_names', 'defined_name_scope'}),
            ('named_range_global_scope_lost', changed(fixture, names, b'name="OrderTotal"', b'name="OrderTotal" localSheetId="0"'), {'defined_name_scope'}),
            ('named_range_local_scope_changed', changed(fixture, names, b'name="_xlnm._FilterDatabase" localSheetId="0"', b'name="_xlnm._FilterDatabase" localSheetId="1"'), {'defined_name_scope'}),
            ('chart_worksheet_link_removed', changed(fixture, s2, b'<drawing r:id="rId1" />', b''), {'chart_linkage'}),
            ('chart_drawing_target_missing', changed(fixture, 'xl/worksheets/_rels/sheet2.xml.rels', b'Target="/xl/drawings/drawing1.xml"', b'Target="/xl/drawings/missing.xml"'), {'chart_linkage'}),
            ('chart_relationship_target_missing', changed(fixture, 'xl/drawings/_rels/drawing1.xml.rels', b'Target="/xl/charts/chart1.xml"', b'Target="/xl/charts/missing.xml"'), {'chart_linkage'}),
            ('chart_data_reference_broken', changed(fixture, chart, b"'Orders'!$A$2:$A$5", b"'Missing'!$A$2:$A$5"), {'chart_targets', 'chart_linkage'}),
            ('chart_part_deleted', {k: v for k, v in fixture.items() if k != chart}, {'chart_targets', 'chart_linkage'}),
            ('table_worksheet_link_removed', changed(fixture, s1, b'<tableParts count="1"><tablePart r:id="rIdTable1" /></tableParts>', b''), {'table_linkage'}),
            ('table_relationship_target_missing', changed(fixture, 'xl/worksheets/_rels/sheet1.xml.rels', b'Target="../tables/table1.xml"', b'Target="../tables/missing.xml"'), {'table_linkage'}),
        ]
        for name, members, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(set(verify.validate_s18(self.workbook(members))), expected)

    def test_s18_sheet_order_does_not_change_name_scope(self):
        members = archive(self.fixture)
        root = ET.fromstring(members['xl/workbook.xml'])
        sheets = next(node for node in root if verify.local(node.tag) == 'sheets')
        sheets[:] = list(reversed(list(sheets)))
        for node in root.iter():
            if verify.local(node.tag) == 'definedName' and node.attrib.get('name') == '_xlnm._FilterDatabase':
                node.set('localSheetId', '1')
        members['xl/workbook.xml'] = ET.tostring(root)
        self.assertEqual(verify.validate_s18(self.workbook(members)), [])

    def test_s18_invalid_and_duplicate_name_scopes_refused(self):
        fixture = archive(self.fixture)
        for scope in ('-1', '2', '0.5', 'invalid'):
            with self.subTest(scope=scope):
                mutant = changed(fixture, 'xl/workbook.xml', b'localSheetId="0"',
                                 ('localSheetId="' + scope + '"').encode())
                self.assertIn('defined_name_scope', verify.validate_s18(self.workbook(mutant)))
        root = ET.fromstring(fixture['xl/workbook.xml'])
        names = next(node for node in root if verify.local(node.tag) == 'definedNames')
        total = next(node for node in names if node.attrib['name'] == 'OrderTotal')
        names.append(ET.fromstring(ET.tostring(total)))
        duplicate = dict(fixture)
        duplicate['xl/workbook.xml'] = ET.tostring(root)
        self.assertIn('defined_name_scope', verify.validate_s18(self.workbook(duplicate)))

    def test_s18_wrong_relationship_type_and_external_target_refused(self):
        fixture = archive(self.fixture)
        prefix = b'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        wrong_type = changed(fixture, 'xl/worksheets/_rels/sheet1.xml.rels',
                             b'Type="' + prefix + b'table"', b'Type="' + prefix + b'chart"')
        self.assertEqual(verify.validate_s18(self.workbook(wrong_type)), ['table_linkage'])
        external = changed(fixture, 'xl/drawings/_rels/drawing1.xml.rels',
                           b'Type="' + prefix + b'chart"',
                           b'Type="' + prefix + b'chart" TargetMode="External"')
        self.assertEqual(set(verify.validate_s18(self.workbook(external))),
                         {'chart_linkage', 'external_relationships'})

    def test_s18_equivalent_internal_chart_target_accepted(self):
        fixture = archive(self.fixture)
        relative = changed(fixture, 'xl/drawings/_rels/drawing1.xml.rels',
                           b'Target="/xl/charts/chart1.xml"', b'Target="../charts/chart1.xml"')
        self.assertEqual(verify.validate_s18(self.workbook(relative)), [])

    def test_s18_original_missing_validation_refused(self):
        failures = verify.validate_s18(verify.Workbook(SOURCES / 'orders_rich_table.xlsx'))
        self.assertIn('validation_rule', failures)
        self.assertIn('validation_bounds', failures)


if __name__ == '__main__':
    unittest.main(verbosity=2)
