"""Portable stdlib controls for the exact source-only reader in the adjacent patch.

All example archives are generated in memory. No installed application, genuine
document, authority/capability, Office process, network or model is used.
Run: python3 -B controls.py
"""
from pathlib import Path
import copy
import hashlib
import io
import json
import types
import unittest
import zipfile
from xml.etree import ElementTree as ET


PATCH_SHA256 = '8649ae57bf5a1c8409956e4643a5e5d44bbf9569acc87752a7f05282eaeba2ca'
PARSER_SHA256 = '285591a979085cc294aec2e366a0d8714d01ab928068693c199aa2ef71990a3c'
patch = Path(__file__).with_name('ordinary-presentation-reader.patch').read_bytes()
if hashlib.sha256(patch).hexdigest() != PATCH_SHA256:
    raise RuntimeError('unexpected patch bytes')
marker = b'+++ b/tools/scoped_presentation.py\n'
addition = patch.split(marker, 1)[1].split(b'\n', 1)[1]
if any(not line.startswith(b'+') for line in addition.splitlines()):
    raise RuntimeError('unexpected new-file patch structure')
source = b''.join(line[1:] + b'\n' for line in addition.splitlines())
if hashlib.sha256(source).hexdigest() != PARSER_SHA256:
    raise RuntimeError('unexpected parser bytes')
p = types.ModuleType('published_presentation_reader')
exec(compile(source, 'tools/scoped_presentation.py', 'exec'), p.__dict__)


def element(namespace, name, attributes=None, text=None):
    node = ET.Element(p.q(namespace, name), attributes or {})
    node.text = text
    return node


def child(parent, namespace, name, attributes=None, text=None):
    node = element(namespace, name, attributes, text)
    parent.append(node)
    return node


def xml(node):
    return ET.tostring(node, encoding='utf-8')


def pack(parts):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data, compress_type=(zipfile.ZIP_STORED
                             if name == 'mimetype' else zipfile.ZIP_DEFLATED))
    return stream.getvalue()


def relationships(rows):
    root = element(p.PKG, 'Relationships')
    for identity, kind, target in rows:
        child(root, p.PKG, 'Relationship',
              {'Id': identity, 'Type': p.R + '/' + kind, 'Target': target})
    return xml(root)


def shape_tree(root, text):
    tree = child(child(root, p.P, 'cSld'), p.P, 'spTree')
    shape = child(tree, p.P, 'sp')
    child(child(child(child(shape, p.P, 'txBody'), p.A, 'p'), p.A, 'r'),
          p.A, 't', text=text)
    return tree


def graphic(tree, namespace, tag, attributes):
    frame = child(tree, p.P, 'graphicFrame')
    data = child(child(frame, p.A, 'graphic'), p.A, 'graphicData', {'uri': namespace})
    return child(data, namespace, tag, attributes)


def pptx_parts():
    """Small neutral structural example; no claim of genuine Office provenance."""
    types_root = element(p.CT, 'Types')
    for extension, kind in [('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
                            ('xml', 'application/xml')]:
        child(types_root, p.CT, 'Default', {'Extension': extension, 'ContentType': kind})
    kinds = {
        'ppt/presentation.xml': 'presentationml.presentation.main',
        'ppt/slides/slide1.xml': 'presentationml.slide',
        'ppt/notesSlides/notesSlide1.xml': 'presentationml.notesSlide',
        'ppt/charts/chart1.xml': 'drawingml.chart',
        'ppt/diagrams/data1.xml': 'drawingml.diagramData',
    }
    for name, kind in kinds.items():
        child(types_root, p.CT, 'Override', {'PartName': '/' + name,
              'ContentType': 'application/vnd.openxmlformats-officedocument.' + kind + '+xml'})
    presentation = element(p.P, 'presentation')
    child(child(presentation, p.P, 'sldIdLst'), p.P, 'sldId',
          {'id': '256', p.q(p.R, 'id'): 'slide'})
    slide = element(p.P, 'sld')
    tree = shape_tree(slide, 'Example slide')
    graphic(tree, p.C, 'chart', {p.q(p.R, 'id'): 'chart'})
    graphic(tree, p.D, 'relIds', {p.q(p.R, 'dm'): 'diagram'})
    notes = element(p.P, 'notes')
    shape_tree(notes, 'Example speaker note')
    chart = element(p.C, 'chartSpace')
    plot = child(child(chart, p.C, 'chart'), p.C, 'plotArea')
    series = child(child(plot, p.C, 'barChart'), p.C, 'ser')
    for field, reference, cache, values in [
            ('cat', 'strRef', 'strCache', ['Alpha', 'Beta']),
            ('val', 'numRef', 'numCache', ['12.50', '7.25'])]:
        ref = child(child(series, p.C, field), p.C, reference)
        child(ref, p.C, 'f', text='Example!$A$2:$A$3')
        cached = child(ref, p.C, cache)
        child(cached, p.C, 'ptCount', {'val': '2'})
        for index, value in enumerate(values):
            child(child(cached, p.C, 'pt', {'idx': str(index)}), p.C, 'v', text=value)
    diagram = element(p.D, 'dataModel')
    point = child(child(diagram, p.D, 'ptLst'), p.D, 'pt', {'modelId': 'example-point'})
    child(child(child(child(point, p.D, 't'), p.A, 'p'), p.A, 'r'), p.A, 't',
          text='Example diagram text')
    return {
        '[Content_Types].xml': xml(types_root),
        '_rels/.rels': relationships([('document', 'officeDocument', 'ppt/presentation.xml')]),
        'ppt/presentation.xml': xml(presentation),
        'ppt/_rels/presentation.xml.rels': relationships([('slide', 'slide', 'slides/slide1.xml')]),
        'ppt/slides/slide1.xml': xml(slide),
        'ppt/slides/_rels/slide1.xml.rels': relationships([
            ('chart', 'chart', '../charts/chart1.xml'),
            ('diagram', 'diagramData', '../diagrams/data1.xml'),
            ('notes', 'notesSlide', '../notesSlides/notesSlide1.xml')]),
        'ppt/notesSlides/notesSlide1.xml': xml(notes),
        'ppt/notesSlides/_rels/notesSlide1.xml.rels': relationships([
            ('slide', 'slide', '../slides/slide1.xml')]),
        'ppt/charts/chart1.xml': xml(chart),
        'ppt/diagrams/data1.xml': xml(diagram),
    }


def odp_parts():
    m = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
    manifest = element(m, 'manifest')
    child(manifest, m, 'file-entry', {p.q(m, 'full-path'): '/', p.q(m, 'media-type'): p.MIME})
    content = element(p.O, 'document-content')
    page = child(child(child(content, p.O, 'body'), p.O, 'presentation'), p.DR, 'page',
                 {p.q(p.DR, 'name'): 'Example'})
    child(child(child(page, p.DR, 'frame'), p.DR, 'text-box'), p.T, 'p', text='Example slide')
    chart = child(child(child(page, p.DR, 'frame'), p.DR, 'object'), p.CH, 'chart')
    plot = child(chart, p.CH, 'plot-area')
    child(child(plot, p.CH, 'axis'), p.CH, 'categories',
          {p.q(p.TB, 'cell-range-address'): 'sample.$A$2:.$A$3'})
    child(plot, p.CH, 'series', {p.q(p.CH, 'values-cell-range-address'): 'sample.$B$2:.$B$3'})
    table = child(chart, p.TB, 'table', {p.q(p.TB, 'name'): 'sample'})
    for values in [['Item', 'Value'], ['Alpha', '12.50'], ['Beta', '7.25']]:
        row = child(table, p.TB, 'table-row')
        for value in values:
            child(child(row, p.TB, 'table-cell'), p.T, 'p', text=value)
    child(child(child(child(page, p.PR, 'notes'), p.DR, 'frame'), p.DR, 'text-box'),
          p.T, 'p', text='Example speaker note')
    return {'mimetype': p.MIME.encode(), 'META-INF/manifest.xml': xml(manifest),
            'content.xml': xml(content)}


def rewrite(parts, name, mutate):
    result = dict(parts)
    root = ET.fromstring(result[name])
    mutate(root)
    result[name] = xml(root)
    return result


def records(text, label):
    return [json.loads(line.split(label, 1)[1]) for line in text.splitlines() if label in line]


class ReaderControls(unittest.TestCase):
    def reject(self, parts, code, fmt='pptx'):
        with self.assertRaises(p.PresentationError) as caught:
            p.extract_presentation(pack(parts), fmt)
        self.assertEqual(str(caught.exception), code)

    def test_positive_pptx_notes_cache_diagram_and_coverage(self):
        text = p.extract_presentation(pack(pptx_parts()), 'pptx')
        metadata = text.extraction_metadata
        self.assertEqual((metadata['slides'], metadata['notes_present'], metadata['charts'],
                          metadata['diagrams']), (1, 1, 1, 1))
        content = records(text, ' CONTENT ')
        self.assertNotIn('Example speaker note', json.dumps(content))
        self.assertIn('Example speaker note', records(text, ' SPEAKER_NOTES ')[0]['content'][0]['text'])
        chart = next(row for row in content if row['kind'] == 'chart')
        self.assertEqual(chart['series'][0]['val']['values'], ['12.50', '7.25'])
        self.assertEqual(chart['series'][0]['val']['status'], 'cached_not_evaluated')
        self.assertIn('diagram_layout_not_rendered', metadata['unsupported_features'])

    def test_positive_odp_notes_and_native_local_values(self):
        text = p.extract_presentation(pack(odp_parts()), 'odp')
        chart = next(row for row in records(text, ' CONTENT ') if row['kind'] == 'chart')
        self.assertEqual(chart['series'][0]['values']['values'], ['12.50', '7.25'])
        self.assertEqual(chart['series'][0]['values']['status'], 'local_table')
        self.assertEqual(text.extraction_metadata['notes_present'], 1)

    def test_odf_cross_table_endpoint_remains_unresolved(self):
        def mutate(root):
            root.find('.//' + p.q(p.CH, 'series')).set(
                p.q(p.CH, 'values-cell-range-address'), 'sample.$B$2:other.$B$3')
        text = p.extract_presentation(pack(rewrite(odp_parts(), 'content.xml', mutate)), 'odp')
        chart = next(row for row in records(text, ' CONTENT ') if row['kind'] == 'chart')
        self.assertIsNone(chart['series'][0]['values']['values'])
        self.assertEqual(chart['series'][0]['values']['status'], 'unresolved_range')
        self.assertIn('odf_chart_range_not_resolved', text.extraction_metadata['unsupported_features'])

    def test_odf_same_table_explicit_and_quoted_endpoints(self):
        tables = [{'name': 'sample', 'raw_values': [['Item', 'Value'], ['Alpha', '12.50'], ['Beta', '7.25']]}]
        for address in ['sample.$B$2:.$B$3', 'sample.$B$2:sample.$B$3', "'sample'.$B$2:$'sample'.$B$3"]:
            self.assertEqual(p.odf_range(address, tables), ['12.50', '7.25'])
        self.assertIsNone(p.odf_range('sample.$B$2:other.$B$3', tables))

    def test_archive_nul_original_name_rejected(self):
        parts = {('ppt/slides/slide1.xmlXsuffix' if name == 'ppt/slides/slide1.xml' else name): data
                 for name, data in pptx_parts().items()}
        data = pack(parts).replace(b'ppt/slides/slide1.xmlXsuffix', b'ppt/slides/slide1.xml\0suffix')
        with self.assertRaisesRegex(p.PresentationError, '^unsafe_or_duplicate_member$'):
            p.extract_presentation(data, 'pptx')

    def test_wrong_part_content_type_rejected(self):
        for name in ['ppt/slides/slide1.xml', 'ppt/notesSlides/notesSlide1.xml',
                     'ppt/charts/chart1.xml', 'ppt/diagrams/data1.xml']:
            with self.subTest(part=name):
                def mutate(root):
                    next(n for n in root if n.get('PartName') == '/' + name).set(
                        'ContentType', 'application/octet-stream')
                self.reject(rewrite(pptx_parts(), '[Content_Types].xml', mutate), 'part_content_type_mismatch')

    def test_wrong_part_root_rejected(self):
        def mutate(root):
            root.tag = p.q(p.C, 'foreignRoot')
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'required_part_or_namespace')

    def test_content_type_default_supported(self):
        def mutate(root):
            for node in list(root):
                if node.get('PartName') == '/ppt/charts/chart1.xml':
                    root.remove(node)
                elif node.get('Extension') == 'xml':
                    node.set('ContentType', 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml')
        text = p.extract_presentation(pack(rewrite(pptx_parts(), '[Content_Types].xml', mutate)), 'pptx')
        self.assertEqual(text.extraction_metadata['charts'], 1)

    def test_duplicate_content_type_rejected(self):
        def mutate(root):
            root.append(copy.deepcopy(root[0]))
        self.reject(rewrite(pptx_parts(), '[Content_Types].xml', mutate), 'duplicate_content_type')

    def test_disconnected_chart_series_rejected(self):
        def mutate(root):
            plot = root.find('.//' + p.q(p.C, 'barChart'))
            series = plot.find(p.q(p.C, 'ser'))
            plot.remove(series)
            child(root, p.C, 'extLst').append(series)
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'chart_series_location')

    def test_disconnected_chart_cache_rejected(self):
        def mutate(root):
            reference = root.find('.//' + p.q(p.C, 'numRef'))
            cache = reference.find(p.q(p.C, 'numCache'))
            reference.remove(cache)
            child(reference, p.C, 'extLst').append(cache)
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'chart_cache_location')

    def test_duplicate_chart_field_rejected(self):
        def mutate(root):
            series = root.find('.//' + p.q(p.C, 'ser'))
            series.append(copy.deepcopy(series.find(p.q(p.C, 'val'))))
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'chart_field_ambiguous')

    def test_string_source_cannot_be_numeric_values(self):
        def mutate(root):
            reference = root.find('.//' + p.q(p.C, 'val') + '/' + p.q(p.C, 'numRef'))
            reference.tag = p.q(p.C, 'strRef')
            reference.find(p.q(p.C, 'numCache')).tag = p.q(p.C, 'strCache')
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'chart_field_type')

    def test_literal_string_cannot_be_numeric_values(self):
        def mutate(root):
            value = root.find('.//' + p.q(p.C, 'val'))
            value[:] = []
            child(value, p.C, 'v', text='example')
        self.reject(rewrite(pptx_parts(), 'ppt/charts/chart1.xml', mutate), 'chart_field_type')

    def test_disconnected_diagram_point_rejected(self):
        def mutate(root):
            points = root.find(p.q(p.D, 'ptLst'))
            point = points[0]
            points.remove(point)
            child(root, p.D, 'extLst').append(point)
        self.reject(rewrite(pptx_parts(), 'ppt/diagrams/data1.xml', mutate), 'diagram_point_structure')

    def test_duplicate_diagram_identity_rejected(self):
        def mutate(root):
            points = root.find(p.q(p.D, 'ptLst'))
            points.append(copy.deepcopy(points[0]))
        self.reject(rewrite(pptx_parts(), 'ppt/diagrams/data1.xml', mutate), 'diagram_point_identity')

    def test_duplicate_diagram_text_rejected(self):
        def mutate(root):
            point = root.find('.//' + p.q(p.D, 'pt'))
            point.append(copy.deepcopy(point.find(p.q(p.D, 't'))))
        self.reject(rewrite(pptx_parts(), 'ppt/diagrams/data1.xml', mutate), 'diagram_point_structure')


if __name__ == '__main__':
    unittest.main(verbosity=2)
