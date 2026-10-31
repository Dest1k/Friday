"""Bounded native presentation admission and typed observations; never runs Office."""
from __future__ import annotations
import hashlib
import copy
import io
import json
import math
from pathlib import Path
import re
import runpy
import stat
import zipfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PARSER = runpy.run_path(str(HERE / 'scoped_presentation.py'))
extract_presentation = PARSER['extract_presentation']
MIMES = {
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/vnd.oasis.opendocument.presentation': 'odp',
}
FILTERS = {'pptx': 'Impress MS PowerPoint 2007 XML', 'odp': 'impress8'}
MAX_BYTES = 1_000_000
MAX_OBSERVATION = 1_000_000
UNSAFE = {
    'embedded_media_or_active_content_not_read',
    'ole_not_read',
    'active_media_or_alternate_content_not_read',
    'images_media_and_ole_not_read',
    'annotations_and_events_not_read',
    'external_or_unsupported_odf_object',
    'unsupported_odf_object',
    'unsupported_graphic_payload',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    need(len(raw) <= MAX_OBSERVATION, 'observation_byte_cap')
    return raw


def without_part_names(value):
    if isinstance(value, dict):
        return {k: without_part_names(v) for k, v in value.items() if k != 'source'}
    if isinstance(value, list):
        return [without_part_names(v) for v in value]
    return value


def workbook_facts(data, source):
    import openpyxl
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        need(0 < len(infos) <= 128, 'embedded_workbook_member_cap')
        need(len({i.filename.casefold() for i in infos}) == len(infos), 'embedded_workbook_duplicate')
        need(sum(i.file_size for i in infos) <= 4_000_000, 'embedded_workbook_expansion_cap')
        for info in infos:
            name = info.filename
            folded = name.casefold()
            mode = info.external_attr >> 16
            need(not info.flag_bits & 1 and stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR), 'embedded_workbook_unsafe_member')
            need(info.file_size <= 1_000_000 and info.file_size <= max(1, info.compress_size) * 200, 'embedded_workbook_expansion_cap')
            need(not folded.startswith(('/', 'xl/vbaproject', 'xl/activex', 'xl/externallinks', 'xl/connections', 'xl/querytables', 'basic/', 'scripts/'))
                 and 'vbaproject' not in folded, 'embedded_workbook_active_content')
            if folded.endswith(('.xml', '.rels')):
                raw = archive.read(info)
                need(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'embedded_workbook_xml_declaration')
                root = ET.fromstring(raw)
            if folded.startswith('xl/worksheets/') and folded.endswith('.xml'):
                # Do not silently truncate workbook cells outside the typed
                # projection. Inspect real XML coordinates, not only a possibly
                # incorrect worksheet dimension declaration.
                for cell in root.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    match = re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,6})', cell.get('r', ''))
                    need(match is not None, 'embedded_workbook_cell_coordinate')
                    column = 0
                    for letter in match[1]:
                        column = column * 26 + ord(letter) - ord('A') + 1
                    need(column <= 64 and int(match[2]) <= 128, 'embedded_workbook_extent_cap')
            if folded.endswith('.rels'):
                for rel in root:
                    need(rel.get('TargetMode', 'Internal') == 'Internal', 'embedded_workbook_external_relationship')
    views = []
    for data_only in (False, True):
        book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=data_only, keep_links=False)
        try:
            need(len(book.sheetnames) <= 16, 'embedded_workbook_sheet_cap')
            view = {}
            for sheet in book.worksheets:
                cells = []
                for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, 128), min_col=1, max_col=min(sheet.max_column or 1, 64)):
                    for cell in row:
                        if cell.value is None:
                            continue
                        need(len(cells) < 2048, 'embedded_workbook_cell_cap')
                        value = cell.value
                        need(not isinstance(value, float) or math.isfinite(value), 'embedded_workbook_nonfinite_value')
                        if not isinstance(value, (str, int, float, bool)) or value is None:
                            value = str(value)
                        if isinstance(value, str):
                            need(len(value) <= 4096, 'embedded_workbook_value_cap')
                        cells.append({'cell': cell.coordinate, 'type': cell.data_type, 'value': value})
                view[sheet.title] = cells
            views.append(view)
        finally:
            book.close()
    return {'source': source, 'sha256': digest(data), 'sheets_formulas': views[0], 'sheets_cached_values': views[1],
            'formula_execution': 'NOT_ESTABLISHED_BY_CACHED_VALUES'}


def observe(data, fmt):
    need(fmt in ('pptx', 'odp'), 'unsupported_presentation_format')
    need(isinstance(data, bytes) and 0 < len(data) <= MAX_BYTES, 'presentation_byte_cap')
    text = extract_presentation(data, fmt)
    metadata = None
    slides = []
    for line in str(text).splitlines():
        if line.startswith('PRESENTATION '):
            need(metadata is None, 'duplicate_presentation_metadata')
            metadata = json.loads(line[len('PRESENTATION '):])
            continue
        match = re.fullmatch(r'SLIDE ([1-9][0-9]*) (.*)', line)
        need(match is not None, 'invalid_presentation_projection_line')
        number, payload = int(match.group(1)), match.group(2)
        if payload.startswith('CONTENT '):
            need(slides and number == len(slides), 'presentation_content_order')
            slides[-1]['content'].append(json.loads(payload[len('CONTENT '):]))
        elif payload.startswith('SPEAKER_NOTES '):
            need(slides and number == len(slides), 'presentation_notes_order')
            slides[-1]['notes'] = json.loads(payload[len('SPEAKER_NOTES '):])
        else:
            need(number == len(slides) + 1, 'presentation_slide_order')
            slides.append({**json.loads(payload), 'content': [], 'notes': None})
    need(metadata is not None and metadata['format'] == fmt and metadata['slides'] == len(slides), 'presentation_metadata_join')
    need(all(s['notes'] is not None for s in slides), 'presentation_notes_missing')
    unsupported = set(metadata['unsupported_features'])
    external = metadata['external_relationships_not_resolved']
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        need(not any(n.casefold().startswith(('basic/', 'scripts/')) or 'vbaproject' in n.casefold()
                     or '/activex/' in n.casefold() for n in names), 'active_package_unsupported')
        embedded = sorted({row['source'] for slide in slides for item in slide['content'] if item['kind'] == 'chart'
                           for row in item.get('embedded_data', [])})
        workbooks = [workbook_facts(archive.read(name), name) for name in embedded]
    structural = {'format': fmt, 'metadata': metadata, 'slides': slides, 'embedded_workbooks': workbooks}
    # ZIP metadata and packaging hash are custody facts, not workbook cell semantics.
    by_source = {book['source']: {k: v for k, v in book.items() if k not in ('source', 'sha256')} for book in workbooks}
    semantic_slides = copy.deepcopy(slides)
    for slide in semantic_slides:
        for item in slide['content']:
            if item['kind'] == 'chart':
                for linked in item.get('embedded_data', []):
                    # Preserve which typed workbook belongs to each chart even
                    # when Office changes package part names or ZIP metadata.
                    linked['workbook_semantics'] = by_source[linked['source']]
    workbook_semantics = sorted(by_source.values(), key=json_bytes)
    semantic = without_part_names({'format': fmt, 'slides': semantic_slides, 'embedded_workbooks': workbook_semantics})
    safe = external == 0 and not (unsupported & UNSAFE)
    return {
        'schema': 'frw.presentation.native-structural-observation.v1',
        'format': fmt,
        'input': {'sha256': digest(data), 'bytes': len(data)},
        'structural_projection': structural,
        'semantic_projection': semantic,
        'semantic_sha256': digest(json_bytes(semantic)),
        'bounded_native_admission': safe,
        'admission_refusal': None if safe else 'ACTIVE_EXTERNAL_OR_UNSUPPORTED_CONTENT',
        'coverage': 'TYPED_NATIVE_STRUCTURE_ONLY_NOT_RENDER_NOT_OFFICE_NOT_USER_SEMANTICS',
        'unsupported_features': sorted(unsupported),
        'full_format_acceptance': False,
    }


def expectation(data, fmt, description, synthetic):
    observed = observe(data, fmt)
    need(observed['bounded_native_admission'], 'unsafe_known_input')
    return {
        'schema': 'frw.presentation.known-input-expectation.v1',
        'format': fmt,
        'input_sha256': observed['input']['sha256'],
        'input_bytes': len(data),
        'description': description,
        'synthetic_offline_fixture': bool(synthetic),
        'semantic_projection': observed['semantic_projection'],
        'semantic_sha256': observed['semantic_sha256'],
        'unsupported_features': observed['unsupported_features'],
        'external_relationships_not_resolved': observed['structural_projection']['metadata']['external_relationships_not_resolved'],
        'qualification_scope': 'EXACT_KNOWN_TYPED_PROJECTION_ONLY',
        'original_user_odp': False,
        'full_format_acceptance': False,
    }


def compare(observed, expected):
    need(type(observed) is dict and observed.get('schema') == 'frw.presentation.native-structural-observation.v1', 'observation_schema')
    need(type(expected) is dict and expected.get('schema') == 'frw.presentation.known-input-expectation.v1', 'expectation_schema')
    need(observed.get('format') == expected.get('format'), 'format_mismatch')
    actual = digest(json_bytes(observed['semantic_projection']))
    need(actual == observed.get('semantic_sha256'), 'observation_digest_mismatch')
    need(expected.get('semantic_sha256') == digest(json_bytes(expected['semantic_projection'])), 'expectation_digest_mismatch')
    new_unsupported = sorted(set(observed['unsupported_features']) - set(expected['unsupported_features']))
    external = observed['structural_projection']['metadata']['external_relationships_not_resolved']
    coverage_preserved = (observed['bounded_native_admission'] is True and not new_unsupported
                          and external == expected['external_relationships_not_resolved'] == 0)
    match = actual == expected['semantic_sha256'] and coverage_preserved
    return {'status': 'MATCH' if match else 'DIFFERENT', 'expected_semantic_sha256': expected['semantic_sha256'],
            'observed_semantic_sha256': actual, 'coverage_preserved': coverage_preserved,
            'new_unsupported_features': new_unsupported, 'external_relationships_not_resolved': external,
            'observed_not_claimed': True, 'render_or_visual_comparison': 'NOT_OBSERVED', 'full_format_acceptance': False}


def fixed_engine_argv(engine, fmt, profile, output, source):
    need(fmt in FILTERS, 'wrong_format')
    for value in (engine, profile, output, source):
        need(isinstance(value, str) and value.startswith('/') and '\x00' not in value, 'canonical_fixed_path_required')
    return [engine, '-env:UserInstallation=file://' + profile, '--headless', '--nologo', '--nodefault',
            '--nofirststartwizard', '--norestore', '--convert-to', fmt + ':' + FILTERS[fmt],
            '--outdir', output, source]
