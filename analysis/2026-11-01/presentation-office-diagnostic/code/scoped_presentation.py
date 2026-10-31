"""Bounded, offline native PPTX/ODP text and cached-data view of immutable bytes.

No rendering, formula evaluation, link refresh, archive extraction or installation.
All content is labelled by slide and role; this view does not grant write authority.
"""
from __future__ import annotations
import io
import json
import posixpath
import re
import stat
import zipfile
import zlib
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
D = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
O = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
DR = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
T = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
TB = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
CH = 'urn:oasis:names:tc:opendocument:xmlns:chart:1.0'
PR = 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0'
XL = 'http://www.w3.org/1999/xlink'
MIME = 'application/vnd.oasis.opendocument.presentation'
MAX_MEMBERS = 512
MAX_MEMBER = 2_000_000
MAX_TOTAL = 8_000_000
MAX_XML = 1_000_000
MAX_XML_TOTAL = 4_000_000
MAX_SLIDES = 200
MAX_POINTS = 5000


def encoded(value):
    # str.splitlines() also treats these Unicode characters as line boundaries.
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            .replace('\u0085', r'\u0085').replace('\u2028', r'\u2028').replace('\u2029', r'\u2029'))


def q(ns, name):
    return '{'+ns+'}'+name


class PresentationError(ValueError):
    pass


class PresentationText(str):
    def __new__(cls, text, metadata):
        obj = super().__new__(cls, text)
        obj.extraction_metadata = metadata
        return obj


def refuse(code):
    raise PresentationError(code)


def integer(value, maximum=MAX_POINTS, minimum=0):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,8}', value):
        refuse('invalid_count')
    result = int(value)
    if not minimum <= result <= maximum:
        refuse('part_count_limit')
    return result


def local_path(base, target):
    # Relationship ../ segments are legitimate; package-root escapes and URIs are not.
    if (not target or any(c in target for c in '\\%?#:')
            or any(ord(c) < 32 for c in target) or target.startswith('//')):
        refuse('unsafe_part_target')
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), target)) if not target.startswith('/') else target[1:]
    if result.startswith('../') or result in ('', '.', '..') or result.startswith('/'):
        refuse('unsafe_part_target')
    return result


class Package:
    def __init__(self, data):
        if not isinstance(data, bytes) or len(data) > 1_000_000:
            refuse('input_limit')
        self.parts = {}; self.xml = {}; self.unsupported = set(); self.external = 0; self.output_bytes = 0
        self.member_info = {}
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_MEMBERS:
                refuse('package_member_limit')
            seen = set(); total = 0; xml_total = 0
            for info in infos:
                name = info.filename
                key = name.rstrip('/')
                if (info.orig_filename != name or not key or '\\' in name or name.startswith('/') or '\x00' in name
                        or any(ord(c) < 32 for c in name) or ':' in name or '%' in name
                        or any(x in ('', '.', '..') for x in key.split('/'))
                        or key.casefold() in seen):
                    refuse('unsafe_or_duplicate_member')
                seen.add(key.casefold())
                mode = info.external_attr >> 16
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR) or info.flag_bits & 1:
                    refuse('encrypted_or_special_member')
                if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    refuse('unsupported_compression')
                total += info.file_size
                if (info.file_size > MAX_MEMBER or total > MAX_TOTAL
                        or info.file_size > max(1, info.compress_size)*200):
                    refuse('package_expansion_limit')
                if info.is_dir():
                    continue
                with archive.open(info) as member:
                    value = member.read(MAX_MEMBER+1)
                if len(value) != info.file_size or len(value) > MAX_MEMBER:
                    refuse('package_member_limit')
                self.parts[name] = value
                self.member_info[name] = (info.compress_type, info.header_offset)
                if name.endswith(('.xml', '.rels')):
                    xml_total += len(value)
                    if len(value) > MAX_XML or xml_total > MAX_XML_TOTAL:
                        refuse('xml_size_limit')
                    try:
                        source = value.decode('utf-8-sig')
                    except UnicodeError:
                        refuse('unsupported_xml_encoding')
                    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)', source, re.I):
                        refuse('xml_dtd_forbidden')
                    root = ET.fromstring(source)
                    stack = [(root, 1)]; count = 0
                    while stack:
                        node, depth = stack.pop(); count += 1
                        if depth > 64 or count > 50_000 or len(node.attrib) > 64:
                            refuse('xml_structure_limit')
                        stack.extend((child, depth+1) for child in node)
                    self.xml[name] = root
        self.relationships = {}
        # Validate every relationship once, even when its target is not rendered.
        for name, root in self.xml.items():
            if not name.endswith('.rels'):
                continue
            if root.tag != q(PKG, 'Relationships'):
                refuse('relationship_namespace')
            if name == '_rels/.rels':
                owner = ''
            else:
                folder, leaf = posixpath.split(name)
                if posixpath.basename(folder) != '_rels':
                    refuse('relationship_location')
                owner = posixpath.join(posixpath.dirname(folder), leaf[:-5])
                if owner not in self.parts:
                    refuse('relationship_owner_missing')
            rows = {}
            for rel in root:
                if rel.tag != q(PKG, 'Relationship') or len(rows) >= 256:
                    refuse('relationship_structure')
                rid, kind, target = (rel.get(k) for k in ('Id', 'Type', 'Target'))
                if not rid or rid in rows or not kind or not target:
                    refuse('duplicate_or_invalid_relationship')
                if kind.rsplit('/', 1)[-1] in ('oleObject', 'control', 'vbaProject', 'audio', 'video'):
                    self.unsupported.add('embedded_media_or_active_content_not_read')
                mode = rel.get('TargetMode', 'Internal')
                if mode == 'External':
                    self.external += 1
                    rows[rid] = (kind, None)
                elif mode == 'Internal':
                    resolved = local_path(owner, target)
                    if resolved not in self.parts:
                        refuse('relationship_target_missing')
                    rows[rid] = (kind, resolved)
                else:
                    refuse('relationship_mode')
            self.relationships[owner] = rows
        if self.external:
            self.unsupported.add('external_relationships_not_resolved')

    def record(self, output, record):
        self.output_bytes += len(encoded(record).encode('utf-8'))
        if self.output_bytes > 900_000:
            refuse('extracted_text_limit')
        output.append(record)

    def root(self, name, expected):
        root = self.xml.get(name)
        if root is None or root.tag != expected:
            refuse('required_part_or_namespace')
        return root

    def target(self, owner, rid, kind):
        row = self.relationships.get(owner, {}).get(rid)
        if row is None or row[0] != R+'/'+kind or row[1] is None:
            refuse('required_relationship')
        return row[1]

    def targets(self, owner, kind):
        return [(rid, target) for rid, (typ, target) in self.relationships.get(owner, {}).items() if typ == R+'/'+kind]


def drawing_text(node):
    paragraphs = []; size = 0
    for paragraph in node.iter(q(A, 'p')):
        chunks = []
        # Paragraph tab stops configure layout; only text/run tabs are content.
        tab_stops = {tab for tabs in paragraph.findall('./'+q(A, 'pPr')+'/'+q(A, 'tabLst'))
                     for tab in tabs.findall(q(A, 'tab'))}
        for part in paragraph.iter():
            value = part.text or '' if part.tag == q(A, 't') else '\n' if part.tag == q(A, 'br') else '\t' if part.tag == q(A, 'tab') and part not in tab_stops else ''
            size += len(value.encode('utf-8'))
            if size > 500_000: refuse('native_text_limit')
            chunks.append(value)
        paragraphs.append(''.join(chunks))
    return '\n'.join(paragraphs)


def chart_field(node, pkg):
    if node is None:
        return None
    field = node.tag[len(C)+2:] if node.tag.startswith('{'+C+'}') else ''
    permitted = ({'strRef', 'v'} if field == 'tx' else {'numRef', 'numLit'}
                 if field in ('val', 'yVal', 'bubbleSize') else
                 {'strRef', 'strLit', 'numRef', 'numLit', 'multiLvlStrRef'})
    for child in node:
        if child.tag != q(C, 'extLst') and child.tag not in {q(C, name) for name in permitted}:
            refuse('chart_field_type')
    cache_tags = {q(C, x) for x in ('strCache', 'numCache', 'strLit', 'numLit', 'multiLvlStrCache')}
    references = {'strRef': 'strCache', 'numRef': 'numCache', 'multiLvlStrRef': 'multiLvlStrCache'}
    formulas = []; caches = []
    for child in node:
        local = child.tag[len(C)+2:] if child.tag.startswith('{'+C+'}') else ''
        if local in references:
            formulas.extend(x.text or '' for x in child.findall(q(C, 'f')))
            caches.extend(child.findall(q(C, references[local])))
        elif local in ('strLit', 'numLit'):
            caches.append(child)
    if set(caches) != {x for x in node.iter() if x.tag in cache_tags}:
        refuse('chart_cache_location')
    literals = node.findall(q(C, 'v'))
    if len(literals) > 1 or (literals and caches): refuse('chart_cache_ambiguous')
    if not caches:
        direct = node.find(q(C, 'v'))
        if direct is not None:
            return {'values': [direct.text or ''], 'formulas': formulas, 'status': 'literal'}
        pkg.unsupported.add('chart_cache_missing')
        return {'values': [], 'formulas': formulas, 'status': 'cache_missing'}
    if len(caches) != 1:
        refuse('chart_cache_ambiguous')
    cache = caches[0]
    count_node = cache.find(q(C, 'ptCount'))
    if count_node is None:
        refuse('chart_cache_count_missing')
    count = integer(count_node.get('val'))
    levels = cache.findall(q(C, 'lvl')) or [cache]
    if len(levels) > 16:
        refuse('chart_level_limit')
    result = []
    for level in levels:
        values = [None]*count; seen = set()
        for point in level.findall(q(C, 'pt')):
            index = integer(point.get('idx'))
            value = point.find(q(C, 'v'))
            if index >= count or index in seen or value is None:
                refuse('chart_cache_mismatch')
            seen.add(index); text = value.text or ''
            if len(text) > 4096:
                refuse('chart_value_limit')
            if cache.tag in (q(C, 'numCache'), q(C, 'numLit')) and text:
                try:
                    if not Decimal(text).is_finite(): refuse('chart_numeric_value')
                except InvalidOperation:
                    refuse('chart_numeric_value')
            values[index] = text
        if len(seen) != count:
            pkg.unsupported.add('chart_sparse_cache_points')
        result.append(values)
    return {'values': result[0] if len(result) == 1 else result, 'formulas': formulas,
            'status': 'cached_not_evaluated'}


def ppt_chart(pkg, name):
    root = pkg.root(name, q(C, 'chartSpace'))
    result = {'source': name, 'text': [x.text or '' for x in root.iter(q(A, 't'))], 'series': []}
    charts = root.findall(q(C, 'chart'))
    if len(charts) != 1 or len(charts[0].findall(q(C, 'plotArea'))) != 1:
        refuse('chart_structure')
    plot = charts[0].find(q(C, 'plotArea'))
    plot_types = {q(C, x) for x in ('barChart', 'bar3DChart', 'lineChart', 'line3DChart',
        'areaChart', 'area3DChart', 'pieChart', 'pie3DChart', 'doughnutChart', 'ofPieChart',
        'scatterChart', 'bubbleChart', 'stockChart', 'surfaceChart', 'surface3DChart', 'radarChart')}
    series_nodes = [series for kind in plot if kind.tag in plot_types for series in kind.findall(q(C, 'ser'))]
    if set(series_nodes) != set(root.iter(q(C, 'ser'))):
        refuse('chart_series_location')
    for series in series_nodes:
        if any(len(series.findall(q(C, key))) > 1 for key in ('tx', 'cat', 'val', 'xVal', 'yVal', 'bubbleSize')):
            refuse('chart_field_ambiguous')
        if series.find(q(C, 'val')) is None and series.find(q(C, 'yVal')) is None:
            pkg.unsupported.add('chart_values_not_available')
        if len(result['series']) >= 128:
            refuse('chart_series_limit')
        result['series'].append({key: chart_field(series.find(q(C, key)), pkg)
                                 for key in ('tx', 'cat', 'val', 'xVal', 'yVal', 'bubbleSize')
                                 if series.find(q(C, key)) is not None})
    if not result['series']:
        pkg.unsupported.add('chart_without_supported_series')
    result['embedded_data'] = []
    for external in root.findall(q(C, 'externalData')):
        rid = external.get(q(R, 'id'))
        row = pkg.relationships.get(name, {}).get(rid)
        if row is None or row[0] != R+'/package':
            refuse('required_relationship')
        result['embedded_data'].append({'source': row[1], 'status': 'not_evaluated_or_refreshed'})
        pkg.unsupported.add('chart_workbook_not_evaluated')
    return result


def ppt_shapes(pkg, name, root, *, notes=False):
    output = []; used_charts = set(); used_diagrams = set()
    def walk(node, hidden=False):
        local = node.tag.rsplit('}', 1)[-1]
        props = node.find('./'+q(P, 'nvSpPr')+'/'+q(P, 'cNvPr'))
        if props is None:
            for prefix in ('nvGrpSpPr', 'nvGraphicFramePr', 'nvPicPr', 'nvCxnSpPr'):
                props = node.find('./'+q(P, prefix)+'/'+q(P, 'cNvPr'))
                if props is not None: break
        hidden = hidden or (props is not None and props.get('hidden') in ('1', 'true'))
        if node.tag in (q(P, 'sp'), q(P, 'cxnSp')):
            ph = node.find('.//'+q(P, 'ph'))
            role = ph.get('type', 'body') if ph is not None else 'body'
            if notes and role in ('sldImg', 'sldNum', 'dt', 'hdr', 'ftr'):
                return
            text = drawing_text(node)
            if text:
                pkg.record(output, {'kind': 'title' if role in ('title', 'ctrTitle') else 'body',
                               'hidden': hidden, 'text': text})
            return
        if node.tag == q(P, 'graphicFrame'):
            if node.find('.//'+q(P, 'oleObj')) is not None: pkg.unsupported.add('ole_not_read')
            if not list(node.iter(q(A, 'graphicData'))): pkg.unsupported.add('unsupported_graphic_payload')
            for graphic in node.iter(q(A, 'graphicData')):
                uri = graphic.get('uri')
                if ((list(graphic.iter(q(A, 'tbl'))) and uri != 'http://schemas.openxmlformats.org/drawingml/2006/table')
                        or (list(graphic.iter(q(C, 'chart'))) and uri != C)
                        or (list(graphic.iter(q(D, 'relIds'))) and uri != D)):
                    refuse('graphic_namespace_mismatch')
                tables = graphic.findall(q(A, 'tbl'))
                for table in tables:
                    rows = [[drawing_text(cell) for cell in row.findall(q(A, 'tc'))] for row in table.findall(q(A, 'tr'))]
                    if len(rows) > 1000 or any(len(row) > 128 for row in rows): refuse('table_limit')
                    pkg.record(output, {'kind': 'table', 'hidden': hidden, 'rows': rows})
                for chart in graphic.iter(q(C, 'chart')):
                    target = pkg.target(name, chart.get(q(R, 'id')), 'chart'); used_charts.add(target)
                    pkg.record(output, {'kind': 'chart', 'hidden': hidden, **ppt_chart(pkg, target)})
                for diagram in graphic.iter(q(D, 'relIds')):
                    target = pkg.target(name, diagram.get(q(R, 'dm')), 'diagramData'); used_diagrams.add(target)
                    data = pkg.root(target, q(D, 'dataModel'))
                    lists = data.findall(q(D, 'ptLst'))
                    if len(lists) != 1: refuse('diagram_point_structure')
                    point_nodes = lists[0].findall(q(D, 'pt'))
                    if len(point_nodes) > MAX_POINTS or set(point_nodes) != set(data.iter(q(D, 'pt'))):
                        refuse('diagram_point_structure')
                    point_ids = set(); points = []
                    for pt in point_nodes:
                        identity = pt.get('modelId')
                        if not identity or identity in point_ids: refuse('diagram_point_identity')
                        point_ids.add(identity)
                        texts = pt.findall(q(D, 't'))
                        if len(texts) > 1: refuse('diagram_point_structure')
                        value = drawing_text(texts[0]) if texts else ''
                        if value: points.append({'id': identity, 'text': value})
                    pkg.record(output, {'kind': 'diagram', 'hidden': hidden, 'source': target, 'points': points})
                    pkg.unsupported.add('diagram_layout_not_rendered')
                if not tables and not list(graphic.iter(q(C, 'chart'))) and not list(graphic.iter(q(D, 'relIds'))):
                    pkg.unsupported.add('unsupported_graphic_payload')
            return
        if node.tag == q(P, 'pic'):
            pkg.unsupported.add('images_not_ocr_read'); return
        if local in ('oleObj', 'video', 'audio', 'timing', 'control', 'AlternateContent'):
            pkg.unsupported.add('active_media_or_alternate_content_not_read')
            return
        if node.tag not in (q(P, 'spTree'), q(P, 'grpSp')):
            if local in ('extLst', 'AlternateContent'): pkg.unsupported.add('extension_or_alternate_content_not_read')
            return
        for child in node:
            walk(child, hidden)
    tree = root.find('./'+q(P, 'cSld')+'/'+q(P, 'spTree'))
    if tree is None: refuse('slide_shape_tree_missing')
    if root.find(q(P, 'timing')) is not None: pkg.unsupported.add('animation_not_read')
    walk(tree)
    if {x[1] for x in pkg.targets(name, 'chart')} != used_charts:
        pkg.unsupported.add('unreferenced_chart_relationship')
    if {x[1] for x in pkg.targets(name, 'diagramData')} != used_diagrams:
        pkg.unsupported.add('unreferenced_diagram_relationship')
    return output


def read_pptx(pkg):
    types = pkg.root('[Content_Types].xml', q(CT, 'Types')); overrides = {}; defaults = {}
    for part in types:
        typ = part.get('ContentType', '')
        if not typ: refuse('invalid_content_type')
        if 'macro' in typ.casefold() or 'vba' in typ.casefold(): refuse('active_package_unsupported')
        if part.tag == q(CT, 'Override'):
            name = local_path('', part.get('PartName', ''))
            if name in overrides: refuse('duplicate_content_type')
            if name not in pkg.parts: refuse('content_type_part_missing')
            overrides[name] = typ
        elif part.tag == q(CT, 'Default'):
            extension = part.get('Extension', '').casefold()
            if not re.fullmatch(r'[a-z0-9]+', extension): refuse('invalid_content_type')
            if extension in defaults: refuse('duplicate_content_type')
            defaults[extension] = typ
        else: refuse('content_type_namespace')
    def content_type(name):
        return overrides.get(name, defaults.get(name.rsplit('.', 1)[-1].casefold()))
    expected_types = {q(P, 'sld'): 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml',
        q(P, 'notes'): 'application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml',
        q(C, 'chartSpace'): 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml',
        q(D, 'dataModel'): 'application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml'}
    for part_name, part_root in pkg.xml.items():
        expected = expected_types.get(part_root.tag)
        if expected and content_type(part_name) != expected: refuse('part_content_type_mismatch')
    roots = pkg.targets('', 'officeDocument')
    if len(roots) != 1 or roots[0][1] is None: refuse('presentation_root_relationship')
    name = roots[0][1]
    if content_type(name) != 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml':
        refuse('not_native_pptx')
    root = pkg.root(name, q(P, 'presentation'))
    slide_ids = root.findall('./'+q(P, 'sldIdLst')+'/'+q(P, 'sldId'))
    if not 1 <= len(slide_ids) <= MAX_SLIDES: refuse('slide_count_limit')
    visited = set(); ids = set(); note_parts = set(); slides = []
    for item in slide_ids:
        target = pkg.target(name, item.get(q(R, 'id')), 'slide')
        if target in visited or not item.get('id') or item.get('id') in ids: refuse('duplicate_slide')
        visited.add(target); ids.add(item.get('id'))
        slide = pkg.root(target, q(P, 'sld'))
        result = {'source': target, 'hidden': slide.get('show') in ('0', 'false'),
                  'content': ppt_shapes(pkg, target, slide)}
        notes = pkg.targets(target, 'notesSlide')
        if len(notes) > 1: refuse('duplicate_notes')
        if notes:
            note = pkg.target(target, notes[0][0], 'notesSlide')
            if note in note_parts: refuse('duplicate_notes')
            note_parts.add(note)
            back = pkg.targets(note, 'slide')
            if len(back) != 1 or back[0][1] != target: refuse('notes_slide_association')
            result['notes'] = {'source': note, 'status': 'present', 'content': ppt_shapes(pkg, note, pkg.root(note, q(P, 'notes')), notes=True)}
        else:
            result['notes'] = {'status': 'absent', 'content': []}
        slides.append(result)
    declared_slides = {n for n in pkg.parts if content_type(n) == expected_types[q(P, 'sld')]}
    declared_notes = {n for n in pkg.parts if content_type(n) == expected_types[q(P, 'notes')]}
    if visited != declared_slides or visited != {x[1] for x in pkg.targets(name, 'slide')}:
        refuse('unreferenced_or_undeclared_slide')
    if note_parts != declared_notes: refuse('unreferenced_or_undeclared_notes')
    pkg.unsupported.add('master_layout_text_and_style_inheritance_not_evaluated')
    return slides


def odf_text(node):
    def inline(part):
        if part.tag == q(T, 's'):
            yield ' '*integer(part.get(q(T, 'c'), '1'), 4096, 1)
        elif part.tag == q(T, 'tab'): yield '\t'
        elif part.tag == q(T, 'line-break'): yield '\n'
        else:
            yield part.text or ''
            for child in part: yield from inline(child)
        yield part.tail or ''
    paragraphs = []; size = 0
    for paragraph in node.iter():
        if paragraph.tag not in (q(T, 'p'), q(T, 'h')): continue
        chunks = []
        for value in inline(paragraph):
            size += len(value.encode('utf-8'))
            if size > 500_000: refuse('native_text_limit')
            chunks.append(value)
        paragraphs.append(''.join(chunks).rstrip('\n'))
    return '\n'.join(paragraphs)


def odf_table(node):
    rows = []; raw_rows = []; cells = 0; text_bytes = 0
    for row in node.iter(q(TB, 'table-row')):
        values = []; raw_values = []
        for cell in row:
            if cell.tag not in (q(TB, 'table-cell'), q(TB, 'covered-table-cell')): continue
            repeat = integer(cell.get(q(TB, 'number-columns-repeated'), '1'), 128, 1)
            native = next((cell.get(q(O, k)) for k in ('value', 'string-value', 'date-value', 'time-value', 'boolean-value') if cell.get(q(O, k)) is not None), None)
            value = odf_text(cell)
            if not value: value = native or ''
            raw = native if native is not None else value
            text_bytes += (len(value.encode('utf-8'))+len(raw.encode('utf-8')))*repeat
            if text_bytes > 500_000: refuse('table_text_limit')
            values.extend([value]*repeat); raw_values.extend([raw]*repeat)
            if len(values) > 128: refuse('table_limit')
        repeat = integer(row.get(q(TB, 'number-rows-repeated'), '1'), 1000, 1)
        text_bytes += sum(len(value.encode('utf-8')) for value in values+raw_values)*(repeat-1)
        if text_bytes > 500_000: refuse('table_text_limit')
        cells += len(values)*repeat
        if len(rows)+repeat > 1000 or cells > 10_000: refuse('table_limit')
        rows.extend([list(values) for _ in range(repeat)])
        raw_rows.extend([list(raw_values) for _ in range(repeat)])
    return {'name': node.get(q(TB, 'name'), ''), 'rows': rows, 'raw_values': raw_rows}


def odf_range(address, tables):
    # Finite local A1 ranges only. Other ODF expressions remain explicit gaps.
    match = re.fullmatch(r"\$?('?[^'.:]+'?|[^'.:]+)\.\$?([A-Z]{1,3})\$?([1-9][0-9]{0,3})(?::(?:\$?('?[^'.:]+'?|[^'.:]+))?\.\$?([A-Z]{1,3})\$?([1-9][0-9]{0,3}))?", address or '')
    if not match: return None
    table, col, row, endtable, endcol, endrow = match.groups(); table = table.strip("'")
    if endtable is not None and endtable.strip("'") != table: return None
    def column(label):
        result = 0
        for char in label: result = result*26+ord(char)-64
        return result-1
    x1=column(col); y1=int(row)-1; x2=column(endcol or col); y2=int(endrow or row)-1
    if x2<x1 or y2<y1 or (x2-x1+1)*(y2-y1+1)>MAX_POINTS: return None
    found = [t for t in tables if t['name']==table]
    if len(found)!=1: return None
    rows=found[0]['raw_values']
    if y2>=len(rows) or any(x2>=len(rows[y]) for y in range(y1,y2+1)): return None
    return [rows[y][x] for y in range(y1,y2+1) for x in range(x1,x2+1)]


def odf_chart(pkg, root, source):
    charts = list(root.iter(q(CH, 'chart')))
    if len(charts) != 1: refuse('odf_chart_structure')
    chart=charts[0]; tables=[odf_table(t) for t in chart.iter(q(TB, 'table'))]
    result={'source':source,'text':odf_text(chart),'tables':tables,'series':[]}
    categories=chart.find('.//'+q(CH, 'categories'))
    cat=categories.get(q(TB, 'cell-range-address')) if categories is not None else None
    for series in chart.iter(q(CH, 'series')):
        record={}
        if series.get(q(CH, 'values-cell-range-address')) is None:
            pkg.unsupported.add('chart_values_not_available')
        for key,address in [('categories',cat),('values',series.get(q(CH,'values-cell-range-address'))),('label',series.get(q(CH,'label-cell-address')))]:
            if address:
                values=odf_range(address,tables)
                record[key]={'range':address,'values':values,'status':'local_table' if values is not None else 'unresolved_range'}
                if values is None: pkg.unsupported.add('odf_chart_range_not_resolved')
        result['series'].append(record)
        if len(result['series'])>128: refuse('chart_series_limit')
    if not result['series']: pkg.unsupported.add('chart_without_supported_series')
    return result


def read_odp(pkg):
    if (pkg.parts.get('mimetype') != MIME.encode()
            or pkg.member_info.get('mimetype') != (zipfile.ZIP_STORED, 0)):
        refuse('not_native_odp')
    manifest=pkg.root('META-INF/manifest.xml', q('urn:oasis:names:tc:opendocument:xmlns:manifest:1.0','manifest'))
    mns='urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
    if any(n.tag==q(mns,'encryption-data') for n in manifest.iter()): refuse('encrypted_package')
    roots = [n for n in manifest if n.tag == q(mns, 'file-entry') and n.get(q(mns, 'full-path')) == '/']
    if len(roots) != 1 or roots[0].get(q(mns, 'media-type')) != MIME:
        refuse('odf_manifest_type')
    root=pkg.root('content.xml',q(O,'document-content'))
    presentation=root.find('./'+q(O,'body')+'/'+q(O,'presentation'))
    if presentation is None: refuse('not_native_odp')
    pages=presentation.findall(q(DR,'page'))
    if not 1<=len(pages)<=MAX_SLIDES: refuse('slide_count_limit')
    slides=[]; names=set()
    for index,page in enumerate(pages,1):
        name=page.get(q(DR,'name'))
        if name and name in names: refuse('duplicate_slide')
        names.add(name)
        result={'source':'content.xml#page='+str(index),'name':name,
                'hidden':page.get(q(PR,'visibility'))=='hidden','content':[]}
        def walk(node, output, role='body', hidden=False):
            if node.tag==q(PR,'notes'): return
            hidden=hidden or node.get(q(PR,'visibility'))=='hidden' or node.get(q(DR,'display'))=='none'
            role='title' if node.get(q(PR,'class')) in ('title','subtitle') else role
            if node.tag==q(TB,'table'):
                pkg.record(output, {'kind':'table','hidden':hidden,**odf_table(node)}); return
            if node.tag in (q(T,'p'),q(T,'h')):
                pkg.record(output, {'kind':role,'hidden':hidden,'text':odf_text(node)}); return
            if node.tag==q(DR,'object'):
                href=node.get(q(XL,'href'))
                if href:
                    try: target=local_path('',href)
                    except PresentationError:
                        pkg.unsupported.add('external_or_unsupported_odf_object'); return
                    target=target.rstrip('/')+'/content.xml'
                    obj=pkg.xml.get(target)
                    if obj is None: refuse('odf_object_missing')
                    if obj.tag != q(O, 'document-content'): refuse('odf_object_namespace')
                else:
                    target=result['source']+'#inline-object'; obj=node
                if list(obj.iter(q(CH,'chart'))):
                    pkg.record(output, {'kind':'chart','hidden':hidden,**odf_chart(pkg,obj,target)})
                else: pkg.unsupported.add('unsupported_odf_object')
                return
            if node.tag in (q(DR,'image'),q(DR,'object-ole'),q(DR,'plugin')):
                pkg.unsupported.add('images_media_and_ole_not_read'); return
            if node.tag in (q(O,'annotation'),q(O,'event-listeners')):
                pkg.unsupported.add('annotations_and_events_not_read'); return
            for child in node: walk(child,output,role,hidden)
        walk(page,result['content'])
        notes=page.findall(q(PR,'notes'))
        if len(notes)>1: refuse('duplicate_notes')
        note_output=[]
        if notes:
            for child in notes[0]: walk(child,note_output)
        result['notes']={'source':result['source']+'#notes' if notes else None,
                         'status':'present' if notes else 'absent','content':note_output}
        slides.append(result)
    pkg.unsupported.add('odf_master_page_style_inheritance_not_evaluated')
    return slides


def extract_presentation(data, format):
    try:
        if format not in ('pptx', 'odp'): refuse('unsupported_format')
        pkg=Package(data)
        slides=read_pptx(pkg) if format=='pptx' else read_odp(pkg) if format=='odp' else refuse('unsupported_format')
        counts={'slides':len(slides),'notes_present':sum(s['notes']['status']=='present' for s in slides),
                'notes_absent':sum(s['notes']['status']=='absent' for s in slides),
                'charts':sum(x['kind']=='chart' for s in slides for x in s['content']),
                'tables':sum(x['kind']=='table' for s in slides for x in s['content']),
                'diagrams':sum(x['kind']=='diagram' for s in slides for x in s['content'])}
        metadata={'kind':'native_presentation_xml_v1','format':format,**counts,
                  'coverage':'native_slide_text_tables_cached_chart_data_diagram_text_and_separate_notes; images_layout_rendering_and_formula_evaluation_not_covered',
                  'unsupported_features':sorted(pkg.unsupported),'external_relationships_not_resolved':pkg.external}
        # One JSON record per labelled line prevents document text forging role boundaries.
        lines=['PRESENTATION '+encoded(metadata)]
        for index,slide in enumerate(slides,1):
            lines.append('SLIDE '+str(index)+' '+encoded({k:v for k,v in slide.items() if k not in ('content','notes')}))
            lines.extend('SLIDE '+str(index)+' CONTENT '+encoded(record) for record in slide['content'])
            lines.append('SLIDE '+str(index)+' SPEAKER_NOTES '+encoded(slide['notes']))
        text='\n'.join(lines)+'\n'
        if len(text.encode('utf-8'))>1_000_000: refuse('extracted_text_limit')
        return PresentationText(text,metadata)
    except PresentationError:
        raise
    except (zipfile.BadZipFile, ET.ParseError, ValueError, OSError, RuntimeError, NotImplementedError, UnicodeError, EOFError, zlib.error) as error:
        raise PresentationError('malformed_presentation_package') from None
