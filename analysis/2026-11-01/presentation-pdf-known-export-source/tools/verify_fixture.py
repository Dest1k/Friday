#!/usr/bin/env python3
"""Inspect the retained synthetic PPTX and its declared expectation, without helpers."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
EXPECTED_SHA = 'dd4ee86bcadb09eeaa98763ec1d536b437471a240b065fd7fd941ae3a0140a3a'
PUBLISHED_SHA = '73f78e17395fd6170a9be7826ef89a4d3cc2769e1bc88fc0f39d858c94a7d762'
PUBLISHED_BYTES = 40190


def need(value, message):
    if not value:
        raise ValueError(message)


def inspect(data, expected):
    need(len(data) == PUBLISHED_BYTES, 'public derivative length')
    need(hashlib.sha256(data).hexdigest() == PUBLISHED_SHA, 'public derivative hash')
    need(expected['input_bytes'] == 40228 and expected['input_sha256'] == EXPECTED_SHA,
         'preserved expectation must bind the original accepted source')
    need(expected['source_only_fixture'] is True and expected['full_format_acceptance'] is False,
         'source-only qualification boundary')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) and len(names) <= 256, 'unique bounded ZIP entries')
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename,
                 'safe ZIP names')
            need(item.file_size <= 1024 * 1024, 'bounded ZIP member')
            if item.filename.endswith('.rels'):
                rels = ET.fromstring(archive.read(item.filename))
                need(all(r.get('TargetMode') != 'External' for r in rels), 'external relationship')
        slide1 = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
        slide2 = ET.fromstring(archive.read('ppt/slides/slide2.xml'))
        chart = ET.fromstring(archive.read('ppt/charts/chart1.xml'))
        table_rows = [[ ''.join(cell.itertext()) for cell in row.findall('a:tc', NS)]
                      for row in slide1.findall('.//a:tbl/a:tr', NS)]
        table_values = [row[1] for row in table_rows]
        chart_values = [node.text for node in chart.findall('.//c:numCache/c:pt/c:v', NS)]
        show = chart.findall('.//c:showVal', NS)
        need(bool(show) and all(node.get('val') == '1' for node in show), 'visible chart labels declared')
        need(table_values == ['3601.50', '1499.70'], 'actual table source values')
        need(chart_values == ['2718.25', '314.75'], 'actual chart source values')
        need(set(table_values).isdisjoint(chart_values), 'table cannot substitute chart evidence')
        need(expected['table_source'] == {'part': 'ppt/slides/slide1.xml', 'values': table_values},
             'declared table fact source')
        need(expected['chart_label_source'] == {'part': 'ppt/charts/chart1.xml', 'showVal': True,
                                               'values': chart_values}, 'declared chart fact source')
        pages = expected['pages']
        need(len(pages) == 2 and [p['page'] for p in pages] == [1, 2], 'ordered page expectations')
        need(pages[0]['table_numeric_cells'] == table_values and
             pages[0]['chart_numeric_labels'] == chart_values, 'independent page roles')
        slide_text = [' '.join(node.text or '' for node in slide.findall('.//a:t', NS))
                      for slide in (slide1, slide2)]
        need(all(token in slide_text[0] for token in pages[0]['text_tokens']
                 if token not in chart_values), 'page-one source text')
        need(all(token in slide_text[1] for token in pages[1]['text_tokens']) and
             pages[1]['table_numeric_cells'] == [] and pages[1]['chart_numeric_labels'] == [],
             'page-two source text')
    return {'status': 'PASS_RETAINED_SYNTHETIC_SOURCE_FACTS_ONLY', 'input_bytes': len(data),
            'input_sha256': PUBLISHED_SHA, 'accepted_original_sha256': EXPECTED_SHA, 'metadata_sanitized': True, 'chart_labels': chart_values,
            'table_cells': table_values, 'actual_Office': 'NOT_RUN', 'actual_PDF': 'NOT_RUN'}


def main():
    data = (ROOT / 'fixtures/known-visible-label.sanitized.pptx').read_bytes()
    expected = json.loads((ROOT / 'fixtures/EXPECTED-PAGES.json').read_bytes())
    print(json.dumps(inspect(data, expected), sort_keys=True))


if __name__ == '__main__':
    main()
