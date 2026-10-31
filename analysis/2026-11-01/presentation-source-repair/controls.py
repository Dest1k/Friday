"""Portable offline source controls; all document archives are synthetic and in memory.

Run from a repository analysis block: python3 -B controls.py
For a detached block, --analysis-root may point to the existing public analysis tree.
No installed application, authority mock, Office process or model is used.
"""
import argparse
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED


BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / 'manifest.json').read_text())
options = argparse.ArgumentParser()
options.add_argument('--analysis-root', type=Path, default=BASE.parents[1])
options.add_argument('--result', type=Path)
args = options.parse_args()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(name, source):
    module = types.ModuleType(name)
    exec(compile(source, name, 'exec'), module.__dict__)
    return module


sources = {}
for row in manifest['product_files']:
    if 'published_source' in row:
        source = (BASE / row['published_source']).read_bytes()
    else:
        patch = (args.analysis_root.parent / row['published_container']).read_bytes()
        assert digest(patch) == row['published_container_sha256']
        marker = b'+++ b/tools/scoped_presentation.py\n'
        addition = patch.split(marker, 1)[1].split(b'\n', 1)[1]
        assert all(line.startswith(b'+') for line in addition.splitlines())
        source = b''.join(line[1:] + b'\n' for line in addition.splitlines())
    assert digest(source) == row['sha256'] and len(source) == row['bytes']
    sources[row['path']] = source

w = load('published_native_writer', sources['tools/scoped_presentation_write.py'])
p = load('tools.scoped_presentation', sources['tools/scoped_presentation.py'])
tools_package = types.ModuleType('tools')
tools_package.__path__ = []
sys.modules['tools'] = tools_package
sys.modules['tools.scoped_presentation'] = p
r = load('published_merged_reader', sources['tools/read_extract.py'])
conversion = load('published_conversion_source', sources['hermes_cli/friday_workspace_presentation.py'])


def parts(data):
    with ZipFile(io.BytesIO(data)) as package:
        return {name: package.read(name) for name in package.namelist()}


def pack(items):
    stream = io.BytesIO()
    with ZipFile(stream, 'w', ZIP_DEFLATED) as package:
        for name, value in items.items():
            package.writestr(name, value, compress_type=(0 if name == 'mimetype' else ZIP_DEFLATED))
    return stream.getvalue()


def workbook(sheet):
    return pack({
        '[Content_Types].xml': b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>',
        '_rels/.rels': ('<Relationships xmlns="%s"><Relationship Id="root" Type="%s/officeDocument" Target="xl/workbook.xml"/></Relationships>' % (w.PR, w.R)).encode(),
        'xl/workbook.xml': ('<workbook xmlns="%s" xmlns:r="%s"><sheets><sheet name="Orders" sheetId="1" r:id="sheet"/></sheets></workbook>' % (w.S, w.R)).encode(),
        'xl/_rels/workbook.xml.rels': ('<Relationships xmlns="%s"><Relationship Id="sheet" Type="%s/worksheet" Target="worksheets/sheet1.xml"/></Relationships>' % (w.PR, w.R)).encode(),
        'xl/worksheets/sheet1.xml': ('<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (w.S, sheet)).encode(),
    })


def orders():
    rows = [['order_id', 'sku', 'qty', 'unit_price', 'currency', 'revision'],
            ['row-a', 'Alpha', '1', '12.50', 'USD', '1'],
            ['row-b', 'Beta', '1', '7.25', 'USD', '2']]
    sheet = ''
    for index, row in enumerate(rows, 1):
        cells = ''.join('<c r="%s%d" t="inlineStr"><is><t>%s</t></is></c>' %
                        (chr(65 + col), index, value) for col, value in enumerate(row))
        sheet += '<row r="%d">%s</row>' % (index, cells)
    return workbook(sheet)


def pptx_spec():
    return {'slides': [{'title': 'Overview' if index == 0 else 'Section %d' % index,
                        'body': 'Neutral example body', 'table': index == 1,
                        'chart': index == 0} for index in range(5)], 'series': 'Revenue'}


def pptx():
    return w.create_pptx(w.orders_facts(orders()), pptx_spec())


def edit_spec():
    return {'slide': 1, 'old_title': 'Overview', 'new_title': 'Revised overview',
            'category': 'Alpha', 'old_value': '12.50', 'new_value': '18.75'}


def odp():
    return w.create_odp({'slides': [{'title': 'Neutral ODP', 'body': 'Example body',
             'notes': 'Separate example note',
             'table': [['Item', 'Amount'], ['Alpha', {'type': 'decimal', 'value': '12.50'}]],
             'chart': {'categories': ['Alpha', 'Beta'], 'values': ['12.50', '7.25']}}]})


class Controls(unittest.TestCase):
    def test_exact_sources_ast_and_preserved_table_writer(self):
        self.assertEqual(len(sources), 7)
        for leaf, source in sources.items():
            ast.parse(source, leaf)
        inherited = manifest['inherited_table_writer']
        self.assertEqual(digest((args.analysis_root.parent / inherited['path']).read_bytes()), inherited['sha256'])

    def test_create_pptx_native_structure_and_reused_reader(self):
        data = pptx()
        self.assertTrue(w.validate_native(data, 'pptx'))
        text = r.extract_scoped_document_bytes(data, 'pptx')
        self.assertEqual(text.extraction_metadata['slides'], 5)
        self.assertIn('Alpha', text)
        self.assertIn('12.50', text)
        self.assertIn('ppt/slideMasters/slideMaster1.xml', parts(data))
        self.assertIn('ppt/embeddings/chart.xlsx', parts(data))

    def test_orders_facts_exact_arithmetic(self):
        facts = w.orders_facts(orders())
        self.assertEqual(facts['grand_total'], '19.75')
        self.assertEqual(facts['largest_sku'], 'Alpha')
        self.assertEqual(dict(facts['totals']), {'Alpha': '12.50', 'Beta': '7.25'})

    def test_pptx_edit_only_selected_parts_and_chart_workbook(self):
        before = pptx()
        after = w.edit_pptx(before, edit_spec())
        old, new = parts(before), parts(after)
        self.assertEqual(set(old), set(new))
        changed = {name for name in old if old[name] != new[name]}
        self.assertEqual(changed, {'ppt/slides/slide1.xml', 'ppt/charts/chart1.xml', 'ppt/embeddings/chart.xlsx'})
        self.assertIn('Revised overview', r.extract_scoped_document_bytes(after, 'pptx'))
        self.assertIn(b'18.75', new['ppt/charts/chart1.xml'])
        self.assertIn(b'18.75', parts(new['ppt/embeddings/chart.xlsx'])['xl/worksheets/sheet1.xml'])
        self.assertEqual(before, pptx())

    def test_title_attribute_collision_changes_actual_text_only(self):
        original = parts(pptx())
        original['ppt/slides/slide1.xml'] = original['ppt/slides/slide1.xml'].replace(b'name="Title"', b'name="Overview"')
        after = parts(w.edit_pptx(pack(original), edit_spec()))['ppt/slides/slide1.xml']
        self.assertIn(b'name="Overview"', after)
        self.assertIn(b'>Revised overview</a:t>', after)

    def test_ambiguous_title_refused(self):
        spec = pptx_spec()
        spec['slides'][1]['title'] = 'Overview'
        with self.assertRaises(w.PresentationRefused):
            w.edit_pptx(w.create_pptx(w.orders_facts(orders()), spec), edit_spec())

    def test_wrong_chart_old_value_refused(self):
        spec = edit_spec()
        spec['old_value'] = '12.51'
        with self.assertRaises(w.PresentationRefused):
            w.edit_pptx(pptx(), spec)

    def test_exact_title_body_collision_refuses_instead_of_wrong_edit(self):
        spec = pptx_spec()
        spec['slides'][0]['body'] = 'Overview'
        with self.assertRaises(w.PresentationRefused):
            w.edit_pptx(w.create_pptx(w.orders_facts(orders()), spec), edit_spec())

    def test_invalid_zip_errors_are_typed_refusals(self):
        for bad in (b'PK-invalid', b'not an archive', pptx()[:100]):
            with self.assertRaises(w.PresentationRefused):
                w.validate_native(bad, 'pptx')

    def test_external_relationship_refused(self):
        items = parts(pptx())
        items['_rels/.rels'] = items['_rels/.rels'].replace(b'Id="rId1"', b'Id="rId1" TargetMode="External"')
        with self.assertRaises(w.PresentationRefused):
            w.validate_native(pack(items), 'pptx')

    def test_active_xml_and_unsafe_member_refused(self):
        for name, value in [('unsafe.xml', b'<!DOCTYPE x [<!ENTITY a "x">]><x/>'),
                            ('../escape.bin', b'inert')]:
            items = parts(pptx())
            items[name] = value
            with self.assertRaises(w.PresentationRefused):
                w.validate_native(pack(items), 'pptx')

    def test_create_odp_native_tables_chart_and_separate_notes(self):
        data = odp()
        self.assertTrue(w.validate_native(data, 'odp'))
        text = r.extract_scoped_document_bytes(data, 'odp')
        self.assertEqual(text.extraction_metadata['slides'], 1)
        self.assertIn('Separate example note', text)
        self.assertIn('Alpha', text)
        with ZipFile(io.BytesIO(data)) as package:
            self.assertEqual(package.infolist()[0].filename, 'mimetype')
            self.assertEqual(package.infolist()[0].compress_type, 0)

    def test_odp_numeric_edit_preserves_other_parts(self):
        before = odp()
        spec = {'slide': 1, 'table': 1, 'row': 2, 'column': 2,
                'old_value': '12.50', 'new_value': '18.75'}
        after = w.edit_odp(before, spec)
        old, new = parts(before), parts(after)
        self.assertEqual({name for name in old if old[name] != new[name]}, {'content.xml'})
        self.assertIn(b'office:value="18.75"', new['content.xml'])
        self.assertIn('Separate example note', r.extract_scoped_document_bytes(after, 'odp'))

    def test_odp_wrong_old_value_and_boolean_address_refused(self):
        spec = {'slide': 1, 'table': 1, 'row': 2, 'column': 2,
                'old_value': '12.50', 'new_value': '18.75'}
        for change in ({'old_value': '12.51'}, {'slide': True}):
            with self.assertRaises(w.PresentationRefused):
                w.edit_odp(odp(), dict(spec, **change))

    def test_merged_xlsx_typed_literals_formula_cache_retained(self):
        data = workbook('<row r="1"><c r="A1" t="inlineStr"><is><t>001&#13;A&#9;B&#10;C</t></is></c><c r="B1"><f>1+2</f><v>3</v></c></row>')
        text = r.extract_scoped_document_bytes(data, 'xlsx')
        records = [json.loads(line) for line in text.splitlines() if line.startswith('{"sheet":') and '"literal_value"' in line]
        by_cell = {record['cell']: record for record in records}
        self.assertEqual(by_cell['A1']['literal_value'], '001\rA\tB\nC')
        self.assertEqual(by_cell['B1']['literal_state'], 'not_literal_formula')
        self.assertEqual(by_cell['B1']['saved_cache']['raw_value'], '3')
        self.assertFalse(text.extraction_metadata['recalculated'])

    def test_json_decimal_and_slide_schema_negatives(self):
        for bad in ('{"slides":[],"slides":[]}', '{"slides":[],"extra":0}'):
            with self.assertRaises(w.PresentationRefused):
                w.json_object(bad, ('slides',))
        for bad in (True, 'NaN', '1e3'):
            with self.assertRaises(w.PresentationRefused):
                w.decimal(bad)
        spec = pptx_spec()
        spec['slides'][0]['chart'] = 1
        with self.assertRaises(w.PresentationRefused):
            w.create_pptx(w.orders_facts(orders()), spec)

    def test_conversion_argv_filters_static_only(self):
        expected = {'pptx_pdf': 'pdf:impress_pdf_Export',
                    'odp_pptx': 'pptx:Impress MS PowerPoint 2007 XML',
                    'pptx_odp': 'odp:impress8'}
        for operation, value in expected.items():
            argv = conversion._office_command(operation)
            self.assertEqual(argv[argv.index('--convert-to') + 1], value)
            self.assertIn('--headless', argv)
        with self.assertRaises(ValueError):
            conversion._office_command('arbitrary')

    def test_prompt_revision_v15_and_merged_table_guidance(self):
        tree = ast.parse(sources['hermes_cli/friday_prompt_scope.py'])
        revision = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'DIALOGUE_REVISION' for target in node.targets)]
        self.assertEqual(revision, ['friday.public-identity.v15'])
        source = sources['hermes_cli/friday_prompt_scope.py'].decode()
        self.assertIn('pptx_pdf', source)
        self.assertIn('xlsx_table', source)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    names = [test.id().rsplit('.', 1)[-1] for test in suite]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failed = {test.id().rsplit('.', 1)[-1] for test, error in result.failures + result.errors}
    report = {'schema': 'frw.presentation-source-repair.portable-controls.v1',
              'status': 'PASS_PORTABLE_SOURCE_CONTROLS' if result.wasSuccessful() else 'FAIL',
              'controls_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'controls': [{'name': name, 'status': 'FAIL' if name in failed else 'PASS'} for name in names],
              'exact_native_source_leaves_verified': len(sources), 'reused_public_parser': True,
              'fixtures': 'neutral_synthetic_archives_generated_in_memory',
              'authority_native_runtime_Office_model_Telegram_user_acceptance': 'NOT_EXERCISED',
              'conversion_qualification': 'STATIC_ARGV_ONLY_NO_OFFICE_PROCESS',
              'full_family': 'UNACCEPTED'}
    if args.result:
        args.result.write_text(json.dumps(report, indent=2) + '\n')
    else:
        print(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
