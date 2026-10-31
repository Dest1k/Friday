"""Bounded native PPTX/ODP creation and preserving edits; stdlib only."""
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from io import BytesIO
import json
import posixpath
import re
import stat
import zlib
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET
from xml.parsers import expat
from xml.sax.saxutils import escape
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

MAX_PACKAGE = 1000000
MAX_TOTAL = 4000000
MAX_MEMBERS = 256
MAX_XML = 1000000
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
for prefix, uri in (('p', P), ('a', A), ('c', C), ('r', R), ('s', S)):
    ET.register_namespace(prefix, uri)


class PresentationRefused(ValueError):
    pass


def _xml(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_XML or b'\x00' in raw:
        raise PresentationRefused('invalid_xml')
    upper = raw.upper()
    if b'<!DOCTYPE' in upper or b'<!ENTITY' in upper:
        raise PresentationRefused('active_xml')
    depth = count = 0
    parser = expat.ParserCreate(encoding='UTF-8', namespace_separator='}')
    def start(name, attrs):
        nonlocal depth, count
        depth += 1; count += 1
        if depth > 128 or count > 100000:
            raise PresentationRefused('xml_capacity')
    def end(name):
        nonlocal depth
        depth -= 1
    def refuse(*args):
        raise PresentationRefused('active_xml')
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = refuse
    parser.EntityDeclHandler = refuse
    parser.ProcessingInstructionHandler = refuse
    try:
        parser.Parse(raw, True)
        return ET.fromstring(raw)
    except (ET.ParseError, expat.ExpatError, ValueError):
        raise PresentationRefused('invalid_xml') from None


def _tostring(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def _xml_resource_guards(parts, name, root):
    xlink = '{http://www.w3.org/1999/xlink}href'
    for node in root.iter():
        local = node.tag.rsplit('}', 1)[-1]
        if local in ('script', 'scripts', 'event-listener', 'event-listeners',
                     'object-ole', 'plugin', 'applet'):
            raise PresentationRefused('active_xml_content')
        href = node.get(xlink)
        if href is None:
            continue
        if not href or any(ord(char) < 32 for char in href):
            raise PresentationRefused('unsafe_xlink')
        if href.startswith('#'):
            continue
        if (href.startswith(('/', '//')) or '\\' in href or ':' in href
                or '%' in href or '?' in href):
            raise PresentationRefused('external_xlink')
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), href)).rstrip('/')
        if resolved in ('', '.', '..') or resolved.startswith('../'):
            raise PresentationRefused('external_xlink')
        if resolved not in parts and not any(item.startswith(resolved + '/') for item in parts):
            raise PresentationRefused('missing_xlink_target')


def _parts(data, *, _depth=0, _budget=None):
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_PACKAGE or _depth > 2:
        raise PresentationRefused('package_capacity')
    budget = {'packages': 0, 'bytes': 0} if _budget is None else _budget
    budget['packages'] += 1
    if budget['packages'] > 16:
        raise PresentationRefused('nested_package_capacity')
    try:
        with ZipFile(BytesIO(data)) as package:
            infos = package.infolist()
            names = [info.filename for info in infos]
            total = sum(info.file_size for info in infos)
            budget['bytes'] += total
            if (not 1 <= len(infos) <= MAX_MEMBERS or len({name.casefold() for name in names}) != len(names)
                    or total > MAX_TOTAL or budget['bytes'] > MAX_TOTAL):
                raise PresentationRefused('package_capacity')
            parts = {}
            for info in infos:
                name = info.filename
                path = PurePosixPath(name)
                if (path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name
                        or info.flag_bits & 1 or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                        or stat.S_ISLNK(info.external_attr >> 16) or info.file_size > MAX_XML
                        or info.file_size > max(4096, info.compress_size * 200)):
                    raise PresentationRefused('unsafe_package')
                parts[name] = package.read(name)
    except (BadZipFile, RuntimeError, NotImplementedError, OSError, EOFError, UnicodeError, zlib.error):
        raise PresentationRefused('invalid_package') from None
    lowered = {name.lower() for name in parts}
    if any('vbaproject' in name or '/activex/' in '/'+name or '/basic/' in '/'+name
           or '/scripts/' in '/'+name or name.startswith('_xmlsignatures/') for name in lowered):
        raise PresentationRefused('active_content')
    for name, raw in parts.items():
        if name.endswith('.rels'):
            for rel in _xml(raw).findall('{%s}Relationship' % PR):
                mode = rel.get('TargetMode', '').lower()
                if mode == 'external':
                    raise PresentationRefused('external_relationship')
                if mode not in ('', 'internal'):
                    raise PresentationRefused('unsafe_relationship')
                kind = rel.get('Type', '').rsplit('/', 1)[-1].lower()
                if kind in ('oleobject', 'control', 'vbaproject', 'externallink'):
                    raise PresentationRefused('unsupported_active_relationship')
                target = rel.get('Target', '')
                if '\\' in target or target.lower().startswith(('data:', 'file:', 'http:', 'https:')):
                    raise PresentationRefused('unsafe_relationship')
                if name == '_rels/.rels':
                    owner = ''
                elif '/_rels/' in name and name.endswith('.rels'):
                    prefix, leaf = name.rsplit('/_rels/', 1)
                    owner = prefix + '/' + leaf[:-5]
                else:
                    raise PresentationRefused('unsafe_relationship')
                resolved = _resolve(owner, target)
                if resolved not in parts:
                    raise PresentationRefused('missing_relationship_target')
                if kind == 'package' and not resolved.lower().endswith('.xlsx'):
                    raise PresentationRefused('unsupported_embedded_package')
        elif name.endswith(('.xml', '.vml')):
            root = _xml(raw)
            _xml_resource_guards(parts, name, root)
            if name == '[Content_Types].xml' and any(
                    'macro' in (node.get('ContentType', '') + node.get('Extension', '')).lower()
                    or 'vba' in node.get('ContentType', '').lower() for node in root):
                raise PresentationRefused('active_content_type')
    for name, raw in parts.items():
        if name.lower().endswith('.xlsx'):
            _parts(raw, _depth=_depth + 1, _budget=budget)
    return infos, parts


def _zip(parts, *, odp=False):
    output = BytesIO()
    with ZipFile(output, 'w') as target:
        names = list(parts)
        if odp:
            names.remove('mimetype')
            names.insert(0, 'mimetype')
        for name in names:
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_STORED if odp and name == 'mimetype' else ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            target.writestr(info, parts[name])
    data = output.getvalue()
    if len(data) > MAX_PACKAGE:
        raise PresentationRefused('package_capacity')
    return data


def _rewrite(infos, parts, changes):
    output = BytesIO()
    with ZipFile(output, 'w') as target:
        for info in infos:
            target.writestr(info, changes.get(info.filename, parts[info.filename]))
    data = output.getvalue()
    if len(data) > MAX_PACKAGE:
        raise PresentationRefused('package_capacity')
    return data


def json_object(content, fields, *, limit=100000):
    if not isinstance(content, str) or len(content.encode('utf-8')) > limit:
        raise PresentationRefused('json_capacity')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PresentationRefused('duplicate_json_key')
            result[key] = value
        return result
    try:
        value = json.loads(content, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        raise PresentationRefused('invalid_json') from None
    if not isinstance(value, dict) or set(value) != set(fields):
        raise PresentationRefused('exact_json_schema')
    return value


def text(value, *, empty=False, limit=4000):
    if not isinstance(value, str) or (not empty and not value) or len(value) > limit:
        raise PresentationRefused('text_capacity')
    if len(value.encode('utf-8')) > limit or any(not (
            ord(c) in (9, 10, 13) or 0x20 <= ord(c) <= 0xD7FF
            or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF) for c in value):
        raise PresentationRefused('invalid_text')
    return value


def decimal(value, *, positive=False):
    if not isinstance(value, str) or re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,12})?', value) is None:
        raise PresentationRefused('decimal_required')
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise PresentationRefused('decimal_required') from None
    if not number.is_finite() or len(value.replace('-', '').replace('.', '').lstrip('0')) > 15:
        raise PresentationRefused('decimal_capacity')
    if positive and number <= 0:
        raise PresentationRefused('positive_decimal_required')
    return number


def _resolve(base, target):
    if not isinstance(target, str) or not target or '\\' in target:
        raise PresentationRefused('unsafe_relationship')
    if target.startswith('/'):
        name = posixpath.normpath(target.lstrip('/'))
    else:
        name = posixpath.normpath(posixpath.join(posixpath.dirname(base), target))
    if name.startswith('../') or name == '..' or name == '.':
        raise PresentationRefused('unsafe_relationship')
    return name


def _rels(parts, name):
    if name not in parts:
        return {}
    root = _xml(parts[name])
    result = {}
    for rel in root.findall('{%s}Relationship' % PR):
        rid = rel.get('Id')
        if not rid or rid in result:
            raise PresentationRefused('ambiguous_relationship')
        result[rid] = rel
    return result


def _shared(parts):
    values = []
    if 'xl/sharedStrings.xml' in parts:
        root = _xml(parts['xl/sharedStrings.xml'])
        for item in root.findall('{%s}si' % S):
            values.append(''.join(node.text or '' for node in item.iter('{%s}t' % S)))
    return values


def _sheet(parts, sheet_name=None):
    workbook = _xml(parts['xl/workbook.xml'])
    rels = _rels(parts, 'xl/_rels/workbook.xml.rels')
    sheets = workbook.findall('.//{%s}sheets/{%s}sheet' % (S, S))
    if not sheets:
        raise PresentationRefused('missing_sheet')
    matches = [item for item in sheets if sheet_name is None or item.get('name') == sheet_name]
    if len(matches) != 1 or (sheet_name is None and len(sheets) != 1):
        raise PresentationRefused('ambiguous_sheet')
    sheet = matches[0]
    rid = sheet.get('{%s}id' % R)
    if rid not in rels:
        raise PresentationRefused('missing_sheet_relationship')
    path = _resolve('xl/workbook.xml', rels[rid].get('Target', ''))
    if path not in parts:
        raise PresentationRefused('missing_sheet_part')
    return path, _xml(parts[path])


def _cell(cell, shared):
    if cell.find('{%s}f' % S) is not None:
        raise PresentationRefused('unevaluated_formula')
    kind = cell.get('t', 'n')
    if kind == 'inlineStr':
        value = ''.join(node.text or '' for node in cell.findall('.//{%s}t' % S))
    else:
        node = cell.find('{%s}v' % S)
        value = None if node is None else node.text or ''
        if kind == 's':
            try:
                value = shared[int(value)]
            except (ValueError, IndexError):
                raise PresentationRefused('invalid_shared_string') from None
        elif kind == 'b' or value is None:
            raise PresentationRefused('unsupported_cell')
    return value


def _rows(root, shared, *, skip_derived=False):
    rows = []
    for row in root.findall('.//{%s}sheetData/{%s}row' % (S, S)):
        values = {}
        for cell in row.findall('{%s}c' % S):
            ref = cell.get('r', '')
            match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', ref)
            if match is None:
                raise PresentationRefused('invalid_cell_reference')
            if skip_derived and cell.find('{%s}f' % S) is not None:
                continue
            values[match.group(1)] = _cell(cell, shared)
        rows.append(values)
    return rows


def orders_facts(data):
    _, parts = _parts(data)
    path, root = _sheet(parts, 'Orders')
    shared = _shared(parts)
    raw_rows = _rows(root, shared, skip_derived=True)
    if len(raw_rows) < 2 or len(raw_rows) > 101:
        raise PresentationRefused('orders_row_bound')
    columns = sorted({key for row in raw_rows for key in row})
    def number(column):
        value = 0
        for char in column:
            value = value * 26 + ord(char) - 64
        return value
    columns.sort(key=number)
    header = [raw_rows[0].get(column) for column in columns]
    required = ['order_id', 'sku', 'qty', 'unit_price', 'currency', 'revision']
    if header[:6] != required or header[6:] not in ([], ['line_net']):
        raise PresentationRefused('orders_schema')
    header = required
    columns = columns[:6]
    orders = []
    ids = set()
    currencies = set()
    for raw in raw_rows[1:]:
        row = dict(zip(header, (raw.get(column) for column in columns)))
        if any(value is None for value in row.values()):
            raise PresentationRefused('orders_dense_rows')
        text(row['order_id'], limit=64); text(row['sku'], limit=64); text(row['currency'], limit=16)
        if row['order_id'] in ids:
            raise PresentationRefused('duplicate_order')
        ids.add(row['order_id']); currencies.add(row['currency'])
        qty = decimal(row['qty'], positive=True)
        price = decimal(row['unit_price'], positive=True)
        if re.fullmatch(r'[0-9]+', row['revision']) is None:
            raise PresentationRefused('revision_required')
        orders.append(dict(row, amount=qty * price))
    if len(currencies) != 1:
        raise PresentationRefused('single_currency_required')
    totals = OrderedDict()
    for row in orders:
        totals[row['sku']] = totals.get(row['sku'], Decimal(0)) + row['amount']
    grand = sum(totals.values(), Decimal(0))
    largest = min(totals, key=lambda sku: (-totals[sku], sku))
    facts = {
        'rows': orders,
        'totals': OrderedDict((sku, format(value, '.2f')) for sku, value in totals.items()),
        'grand_total': format(grand, '.2f'),
        'currency': next(iter(currencies)),
        'largest_sku': largest,
        'source_sheet_part': path,
    }
    return facts


def _sp(shape_id, name, x, y, cx, cy, value, *, title=False):
    placeholder = '<p:ph type="title"/>' if title else ''
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{escape(name)}"/>'
            f'<p:cNvSpPr/><p:nvPr>{placeholder}</p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            '<p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p><a:r>'
            '<a:rPr lang="ru-RU" dirty="0"/><a:t>' + escape(value) +
            '</a:t></a:r></a:p></p:txBody></p:sp>')


def _table(frame_id, rows, x=457200, y=1828800, cx=5486400, cy=2743200):
    widths = [cx // len(rows[0])] * len(rows[0])
    grid = ''.join(f'<a:gridCol w="{width}"/>' for width in widths)
    native_rows = []
    for row in rows:
        cells = ''.join(
            '<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="ru-RU" dirty="0"/>'
            '<a:t>' + escape(str(value)) + '</a:t></a:r></a:p></a:txBody><a:tcPr/></a:tc>'
            for value in row)
        native_rows.append('<a:tr h="360000">' + cells + '</a:tr>')
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{frame_id}" name="Orders table"/>'
            '<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
            f'</p:nvGraphicFramePr><p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            '<a:tbl><a:tblPr firstRow="1" bandRow="1"/><a:tblGrid>' + grid + '</a:tblGrid>' +
            ''.join(native_rows) + '</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')


def _chart_frame(frame_id, rid):
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{frame_id}" name="Sales chart"/>'
            '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
            '<p:xfrm><a:off x="6400800" y="1828800"/><a:ext cx="2743200" cy="2743200"/></p:xfrm>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
            f'<c:chart xmlns:c="{C}" xmlns:r="{R}" r:id="{rid}"/>'
            '</a:graphicData></a:graphic></p:graphicFrame>')


def _workbook(facts, series):
    rows = [['SKU', series]] + [[sku, value] for sku, value in facts['totals'].items()]
    sheet_rows = []
    for index, row in enumerate(rows, 1):
        cells = []
        for column, value in zip(('A', 'B'), row):
            if index == 1 or column == 'A':
                cells.append(f'<c r="{column}{index}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
            else:
                cells.append(f'<c r="{column}{index}"><v>{value}</v></c>')
        sheet_rows.append(f'<row r="{index}">' + ''.join(cells) + '</row>')
    return _zip({
        '[Content_Types].xml': ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>').encode(),
        '_rels/.rels': ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" Target="xl/workbook.xml"/></Relationships>' % (PR, R)).encode(),
        'xl/workbook.xml': ('<workbook xmlns="%s" xmlns:r="%s"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>' % (S, R)).encode(),
        'xl/_rels/workbook.xml.rels': ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="%s/styles" Target="styles.xml"/></Relationships>' % (PR, R, R)).encode(),
        'xl/worksheets/sheet1.xml': ('<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (S, ''.join(sheet_rows))).encode(),
        'xl/styles.xml': ('<styleSheet xmlns="%s"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="1"><xf xfId="0"/></cellXfs></styleSheet>' % S).encode(),
    })


def _chart(facts, series):
    categories = list(facts['totals'])
    values = list(facts['totals'].values())
    count = len(categories)
    cat_points = ''.join(f'<c:pt idx="{i}"><c:v>{escape(value)}</c:v></c:pt>' for i, value in enumerate(categories))
    val_points = ''.join(f'<c:pt idx="{i}"><c:v>{value}</c:v></c:pt>' for i, value in enumerate(values))
    return (f'<c:chartSpace xmlns:c="{C}" xmlns:a="{A}" xmlns:r="{R}"><c:chart><c:plotArea><c:layout/>'
            '<c:barChart><c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>'
            '<c:ser><c:idx val="0"/><c:order val="0"/><c:tx><c:strRef><c:f>Sheet1!$B$1</c:f>'
            f'<c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>{escape(series)}</c:v></c:pt></c:strCache></c:strRef></c:tx>'
            f'<c:cat><c:strRef><c:f>Sheet1!$A$2:$A${count+1}</c:f><c:strCache><c:ptCount val="{count}"/>{cat_points}</c:strCache></c:strRef></c:cat>'
            f'<c:val><c:numRef><c:f>Sheet1!$B$2:$B${count+1}</c:f><c:numCache><c:formatCode>0.00</c:formatCode><c:ptCount val="{count}"/>{val_points}</c:numCache></c:numRef></c:val>'
            '</c:ser><c:axId val="1"/><c:axId val="2"/></c:barChart>'
            '<c:catAx><c:axId val="1"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:tickLblPos val="nextTo"/><c:crossAx val="2"/></c:catAx>'
            '<c:valAx><c:axId val="2"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:tickLblPos val="nextTo"/><c:crossAx val="1"/></c:valAx>'
            '</c:plotArea><c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>'
            '<c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>').encode()


def create_pptx(facts, spec):
    slides = spec['slides']
    series = text(spec['series'], limit=256)
    if not isinstance(slides, list) or len(slides) != 5:
        raise PresentationRefused('exactly_five_slides')
    table_slides = chart_slides = 0
    for slide in slides:
        if not isinstance(slide, dict) or set(slide) != {'title', 'body', 'table', 'chart'}:
            raise PresentationRefused('slide_schema')
        text(slide['title'], limit=256); text(slide['body'], empty=True)
        if type(slide['table']) is not bool or type(slide['chart']) is not bool:
            raise PresentationRefused('slide_flags')
        table_slides += slide['table']; chart_slides += slide['chart']
    if table_slides != 1 or chart_slides != 1:
        raise PresentationRefused('one_native_table_and_chart')
    parts = {}
    overrides = []
    slide_paths = []
    source_rows = [['order_id', 'sku', 'qty', 'unit_price', 'currency', 'revision']]
    source_rows += [[row[key] for key in source_rows[0]] for row in facts['rows']]
    for index, slide in enumerate(slides, 1):
        name = f'ppt/slides/slide{index}.xml'; slide_paths.append(name)
        shapes = [_sp(2, 'Title', 457200, 365760, 8686800, 640080, slide['title'], title=True),
                  _sp(3, 'Body', 457200, 1097280, 8686800, 548640, slide['body'])]
        rels = ['<Relationship Id="rId1" Type="%s/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>' % R]
        if slide['table']:
            shapes.append(_table(4, source_rows))
        if slide['chart']:
            shapes.append(_chart_frame(5, 'rId2'))
            rels.append('<Relationship Id="rId2" Type="%s/chart" Target="../charts/chart1.xml"/>' % R)
        parts[name] = (f'<p:sld xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld><p:spTree>'
                       '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                       '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                       + ''.join(shapes) + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>').encode()
        parts[f'ppt/slides/_rels/slide{index}.xml.rels'] = ('<Relationships xmlns="%s">%s</Relationships>' % (PR, ''.join(rels))).encode()
        overrides.append(f'<Override PartName="/{name}" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    parts['ppt/charts/chart1.xml'] = _chart(facts, series)
    parts['ppt/charts/_rels/chart1.xml.rels'] = ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/package" Target="../embeddings/chart.xlsx"/></Relationships>' % (PR, R)).encode()
    parts['ppt/embeddings/chart.xlsx'] = _workbook(facts, series)
    master = (f'<p:sldMaster xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>')
    layout = (f'<p:sldLayout xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
    theme = (f'<a:theme xmlns:a="{A}" name="Office"><a:themeElements><a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F1F1F"/></a:dk2><a:lt2><a:srgbClr val="EEEEEE"/></a:lt2><a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')
    parts['ppt/slideMasters/slideMaster1.xml'] = master.encode()
    parts['ppt/slideMasters/_rels/slideMaster1.xml.rels'] = ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="%s/theme" Target="../theme/theme1.xml"/></Relationships>' % (PR, R, R)).encode()
    parts['ppt/slideLayouts/slideLayout1.xml'] = layout.encode()
    parts['ppt/slideLayouts/_rels/slideLayout1.xml.rels'] = ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>' % (PR, R)).encode()
    parts['ppt/theme/theme1.xml'] = theme.encode()
    sld_ids = ''.join(f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>' for i in range(1, 6))
    pres_rels = ['<Relationship Id="rId1" Type="%s/slideMaster" Target="slideMasters/slideMaster1.xml"/>' % R]
    pres_rels += [f'<Relationship Id="rId{i+1}" Type="{R}/slide" Target="slides/slide{i}.xml"/>' for i in range(1, 6)]
    parts['ppt/presentation.xml'] = (f'<p:presentation xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>{sld_ids}</p:sldIdLst><p:sldSz cx="9144000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>').encode()
    parts['ppt/_rels/presentation.xml.rels'] = ('<Relationships xmlns="%s">%s</Relationships>' % (PR, ''.join(pres_rels))).encode()
    parts['_rels/.rels'] = ('<Relationships xmlns="%s"><Relationship Id="rId1" Type="%s/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="%s/extended-properties" Target="docProps/app.xml"/></Relationships>' % (PR, R, R)).encode()
    parts['docProps/core.xml'] = b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Editable presentation</dc:title></cp:coreProperties>'
    parts['docProps/app.xml'] = '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Friday</Application><Slides>5</Slides></Properties>'.encode()
    types = ['<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>', '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>', '<Default Extension="xml" ContentType="application/xml"/>',
             '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
             '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
             '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
             '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
             '<Override PartName="/ppt/charts/chart1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>',
             '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
             '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'] + overrides
    parts['[Content_Types].xml'] = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + ''.join(types) + '</Types>').encode()
    return _zip(parts)


def _slide_paths(parts):
    presentation = 'ppt/presentation.xml'
    if presentation not in parts:
        raise PresentationRefused('not_pptx')
    rels = _rels(parts, 'ppt/_rels/presentation.xml.rels')
    paths = []
    for item in _xml(parts[presentation]).findall('.//{%s}sldIdLst/{%s}sldId' % (P, P)):
        rid = item.get('{%s}id' % R)
        if rid not in rels:
            raise PresentationRefused('missing_slide_relationship')
        path = _resolve(presentation, rels[rid].get('Target', ''))
        if path not in parts:
            raise PresentationRefused('missing_slide')
        paths.append(path)
    if not paths:
        raise PresentationRefused('missing_slides')
    return paths


def _native_number(value):
    if not isinstance(value, str) or not value:
        raise PresentationRefused('invalid_native_number')
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise PresentationRefused('invalid_native_number') from None
    if not number.is_finite():
        raise PresentationRefused('invalid_native_number')
    return number


def _chart_cache(ref, cache_name, *, numeric=False):
    formulas = ref.findall('{%s}f' % C)
    caches = ref.findall('{%s}%s' % (C, cache_name))
    if len(formulas) != 1 or not formulas[0].text or len(caches) != 1:
        raise PresentationRefused('invalid_chart_cache')
    cache = caches[0]
    counts = cache.findall('{%s}ptCount' % C)
    if len(counts) != 1 or re.fullmatch(r'[0-9]{1,4}', counts[0].get('val', '')) is None:
        raise PresentationRefused('invalid_chart_cache_count')
    count = int(counts[0].get('val'))
    points = cache.findall('{%s}pt' % C)
    if count > 5000 or len(points) != count:
        raise PresentationRefused('chart_cache_count_mismatch')
    values = {}
    for point in points:
        raw_index = point.get('idx', '')
        nodes = point.findall('{%s}v' % C)
        if re.fullmatch(r'[0-9]+', raw_index) is None or len(nodes) != 1 or nodes[0].text is None:
            raise PresentationRefused('invalid_chart_cache_point')
        index = int(raw_index)
        if index >= count or index in values:
            raise PresentationRefused('duplicate_chart_cache_index')
        if numeric:
            _native_number(nodes[0].text)
        values[index] = nodes[0]
    if set(values) != set(range(count)):
        raise PresentationRefused('chart_cache_count_mismatch')
    return formulas[0].text, values


def _replace_title_text(raw, old_title, new_title):
    """Replace one actual DrawingML text node, never a matching attribute/body substring."""
    parser = expat.ParserCreate(encoding='UTF-8', namespace_separator='}')
    capture = None
    matches = []
    escaped_old = escape(old_title).encode('utf-8')
    def start(name, attrs):
        nonlocal capture
        if capture is not None:
            raise PresentationRefused('unsupported_title_runs')
        if name == A + '}t':
            capture = [None, []]
    def characters(value):
        if capture is not None:
            if capture[0] is None:
                capture[0] = parser.CurrentByteIndex
            capture[1].append(value)
    def end(name):
        nonlocal capture
        if name == A + '}t' and capture is not None:
            first, values = capture
            if ''.join(values) == old_title:
                last = parser.CurrentByteIndex
                if first is None or raw[first:last] != escaped_old:
                    raise PresentationRefused('unsupported_title_runs')
                matches.append((first, last))
            capture = None
    parser.StartElementHandler = start
    parser.CharacterDataHandler = characters
    parser.EndElementHandler = end
    parser.Parse(raw, True)  # Already bounded and parsed by _parts/_xml.
    if len(matches) != 1:
        raise PresentationRefused('unsupported_title_runs')
    first, last = matches[0]
    return raw[:first] + escape(new_title).encode('utf-8') + raw[last:]


def edit_pptx(data, spec):
    infos, parts = _parts(data)
    paths = _slide_paths(parts)
    index = spec['slide']
    if type(index) is not int or not 1 <= index <= len(paths):
        raise PresentationRefused('slide_index')
    old_title = text(spec['old_title'], limit=256); new_title = text(spec['new_title'], limit=256)
    category = text(spec['category'], limit=256)
    old_value = decimal(spec['old_value']); decimal(spec['new_value'])
    title_matches = []
    for number, path in enumerate(paths, 1):
        root = _xml(parts[path])
        for shape in root.findall('.//{%s}sp' % P):
            placeholders = shape.findall('./{%s}nvSpPr/{%s}nvPr/{%s}ph' % (P, P, P))
            if any(node.get('type', 'body') in ('title', 'ctrTitle') for node in placeholders):
                value = ''.join(node.text or '' for node in shape.findall('.//{%s}t' % A))
                if value == old_title:
                    title_matches.append((number, path, shape))
    if len(title_matches) != 1 or title_matches[0][:2] != (index, paths[index-1]):
        raise PresentationRefused('unique_title_required')
    title_nodes = title_matches[0][2].findall('.//{%s}t' % A)
    if len(title_nodes) != 1 or len(title_nodes[0]) != 0 or title_nodes[0].text != old_title:
        raise PresentationRefused('unsupported_title_runs')
    new_slide = _replace_title_text(parts[paths[index-1]], old_title, new_title)
    slide_rels_name = posixpath.join(posixpath.dirname(paths[index-1]), '_rels', posixpath.basename(paths[index-1]) + '.rels')
    slide_rels = _rels(parts, slide_rels_name)
    charts = [rel for rel in slide_rels.values() if rel.get('Type', '').endswith('/chart')]
    if len(charts) != 1:
        raise PresentationRefused('one_chart_required')
    chart_path = _resolve(paths[index-1], charts[0].get('Target', ''))
    if chart_path not in parts:
        raise PresentationRefused('missing_chart')
    chart = _xml(parts[chart_path])
    matches = []
    for series in chart.findall('.//{%s}ser' % C):
        cat_ref = series.find('./{%s}cat/{%s}strRef' % (C, C))
        val_ref = series.find('./{%s}val/{%s}numRef' % (C, C))
        if cat_ref is None or val_ref is None:
            continue
        cat_formula, cats = _chart_cache(cat_ref, 'strCache')
        val_formula, vals = _chart_cache(val_ref, 'numCache', numeric=True)
        if set(cats) != set(vals) or len({node.text or '' for node in cats.values()}) != len(cats):
            raise PresentationRefused('ambiguous_chart_cache')
        for idx, cat_node in cats.items():
            if (cat_node.text or '') == category and _native_number(vals[idx].text) == old_value:
                matches.append((cat_formula, val_formula, vals[idx], cats, vals))
    if len(matches) != 1:
        raise PresentationRefused('unique_chart_datum_required')
    cat_formula, val_formula, value_node, cats, vals = matches[0]
    expected = {(cats[idx].text or ''): _native_number(vals[idx].text) for idx in cats}
    external = chart.findall('.//{%s}externalData' % C)
    if len(external) != 1:
        raise PresentationRefused('embedded_workbook_required')
    rid = external[0].get('{%s}id' % R)
    chart_rels_name = posixpath.join(posixpath.dirname(chart_path), '_rels', posixpath.basename(chart_path) + '.rels')
    chart_rels = _rels(parts, chart_rels_name)
    if rid not in chart_rels or not chart_rels[rid].get('Type', '').endswith('/package'):
        raise PresentationRefused('embedded_workbook_required')
    workbook_path = _resolve(chart_path, chart_rels[rid].get('Target', ''))
    if workbook_path not in parts or not workbook_path.lower().endswith('.xlsx'):
        raise PresentationRefused('embedded_workbook_required')
    workbook_infos, workbook_parts = _parts(parts[workbook_path])
    worksheet_path, worksheet = _workbook_datum(workbook_parts, cat_formula, val_formula, category, old_value, spec['new_value'], expected)
    value_node.text = spec['new_value']
    workbook_parts[worksheet_path] = _tostring(worksheet)
    changes = {
        paths[index-1]: new_slide,
        chart_path: _tostring(chart),
        workbook_path: _rewrite(workbook_infos, workbook_parts, {worksheet_path: workbook_parts[worksheet_path]}),
    }
    return _rewrite(infos, parts, changes)


def _formula(value):
    match = re.fullmatch(r"(?:'((?:[^']|'')+)'|([A-Za-z_][A-Za-z0-9_.]*))!\$([A-Z]+)\$([1-9][0-9]*):\$([A-Z]+)\$([1-9][0-9]*)", value)
    if match is None:
        raise PresentationRefused('unsupported_chart_formula')
    sheet = match.group(1).replace("''", "'") if match.group(1) is not None else match.group(2)
    return sheet, match.group(3), int(match.group(4)), match.group(5), int(match.group(6))


def _workbook_datum(parts, cat_formula, val_formula, category, old_value, new_text, expected):
    cat_sheet, cat_col, cat_first, cat_last_col, cat_last = _formula(cat_formula)
    val_sheet, val_col, val_first, val_last_col, val_last = _formula(val_formula)
    if (cat_sheet != val_sheet or cat_col != cat_last_col or val_col != val_last_col
            or cat_first != val_first or cat_last != val_last or cat_first >= cat_last):
        raise PresentationRefused('unsupported_chart_ranges')
    path, root = _sheet(parts, cat_sheet)
    shared = _shared(parts)
    cells = {cell.get('r'): cell for cell in root.findall('.//{%s}sheetData/{%s}row/{%s}c' % (S, S, S))}
    matches = []
    observed = {}
    for row in range(cat_first, cat_last + 1):
        cat_cell = cells.get(cat_col + str(row)); val_cell = cells.get(val_col + str(row))
        if cat_cell is None or val_cell is None:
            raise PresentationRefused('chart_workbook_missing_cells')
        node = val_cell.find('{%s}v' % S)
        if node is None:
            raise PresentationRefused('chart_workbook_missing_values')
        observed[_cell(cat_cell, shared)] = _native_number(node.text)
        if _cell(cat_cell, shared) == category:
            if _native_number(node.text) == old_value:
                matches.append((val_cell, node))
    if observed != expected:
        raise PresentationRefused('chart_workbook_cache_mismatch')
    if len(matches) != 1:
        raise PresentationRefused('unique_workbook_datum_required')
    cell, node = matches[0]
    if cell.find('{%s}f' % S) is not None:
        raise PresentationRefused('formula_datum_unsupported')
    node.text = new_text
    return path, root


ODP_NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'presentation': 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0',
    'chart': 'urn:oasis:names:tc:opendocument:xmlns:chart:1.0',
    'xlink': 'http://www.w3.org/1999/xlink',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
}
for prefix, uri in ODP_NS.items():
    ET.register_namespace(prefix, uri)


def _odp_decls():
    return ' '.join(f'xmlns:{prefix}="{uri}"' for prefix, uri in ODP_NS.items())


def _odp_table(name, rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 128 or not isinstance(rows[0], list) or not 1 <= len(rows[0]) <= 32:
        raise PresentationRefused('table_bounds')
    output = [f'<table:table table:name="{escape(name)}"><table:table-column table:number-columns-repeated="{len(rows[0])}"/>']
    for row in rows:
        if not isinstance(row, list) or len(row) != len(rows[0]):
            raise PresentationRefused('rectangular_table')
        output.append('<table:table-row>')
        for value in row:
            if isinstance(value, dict) and set(value) == {'type', 'value'} and value['type'] == 'decimal':
                number = decimal(value['value'])
                output.append(f'<table:table-cell office:value-type="float" office:value="{value["value"]}"><text:p>{value["value"]}</text:p></table:table-cell>')
            else:
                output.append('<table:table-cell office:value-type="string"><text:p>' + escape(text(value, empty=True, limit=1024)) + '</text:p></table:table-cell>')
        output.append('</table:table-row>')
    output.append('</table:table>')
    return ''.join(output)


def create_odp(spec):
    slides = spec['slides']
    if not isinstance(slides, list) or not 1 <= len(slides) <= 20:
        raise PresentationRefused('slide_bounds')
    pages = []
    manifest_objects = []
    objects = {}
    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or set(slide) != {'title', 'body', 'notes', 'table', 'chart'}:
            raise PresentationRefused('odp_slide_schema')
        title = text(slide['title'], limit=256); body = text(slide['body'], empty=True)
        notes = text(slide['notes'], empty=True)
        items = [f'<draw:frame draw:name="Title" svg:width="24cm" svg:height="2cm" svg:x="1cm" svg:y="1cm" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"><draw:text-box><text:p>{escape(title)}</text:p></draw:text-box></draw:frame>',
                 f'<draw:frame draw:name="Body" svg:width="24cm" svg:height="2cm" svg:x="1cm" svg:y="3.5cm" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"><draw:text-box><text:p>{escape(body)}</text:p></draw:text-box></draw:frame>']
        if slide['table'] is not None:
            items.append(_odp_table('Orders' + str(index), slide['table']))
        if slide['chart'] is not None:
            chart = slide['chart']
            if not isinstance(chart, dict) or set(chart) != {'categories', 'values'} or not isinstance(chart['categories'], list) or not isinstance(chart['values'], list) or not 1 <= len(chart['categories']) == len(chart['values']) <= 128:
                raise PresentationRefused('chart_schema')
            for category in chart['categories']:
                text(category, limit=256)
            for value in chart['values']:
                decimal(value)
            object_name = f'Object {len(objects)+1}'
            header = '<table:table-row><table:table-cell office:value-type="string"><text:p>Category</text:p></table:table-cell><table:table-cell office:value-type="string"><text:p>Value</text:p></table:table-cell></table:table-row>'
            local_rows = ''.join('<table:table-row><table:table-cell office:value-type="string"><text:p>' + escape(category) + '</text:p></table:table-cell><table:table-cell office:value-type="float" office:value="' + value + '"><text:p>' + value + '</text:p></table:table-cell></table:table-row>' for category, value in zip(chart['categories'], chart['values']))
            last = len(chart['categories']) + 1
            chart_content = (f'<office:document-content {_odp_decls()} office:version="1.2"><office:body><office:chart><chart:chart chart:class="chart:bar">'
                '<chart:plot-area><chart:axis chart:dimension="x" chart:name="primary-x">'
                f'<chart:categories table:cell-range-address="local-table.$A$2:.$A${last}"/></chart:axis>'
                '<chart:axis chart:dimension="y" chart:name="primary-y"/>'
                f'<chart:series chart:values-cell-range-address="local-table.$B$2:.$B${last}" chart:label-cell-address="local-table.$B$1"/></chart:plot-area>'
                f'<table:table table:name="local-table"><table:table-column table:number-columns-repeated="2"/>{header}{local_rows}</table:table>'
                '</chart:chart></office:chart></office:body></office:document-content>').encode()
            objects[object_name + '/content.xml'] = chart_content
            manifest_objects.append(object_name)
            items.append(f'<draw:frame draw:name="Chart" svg:width="12cm" svg:height="8cm" svg:x="13cm" svg:y="6cm" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"><draw:object xlink:href="./{object_name}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/></draw:frame>')
        pages.append(f'<draw:page draw:name="page{index}" draw:style-name="dp1" draw:master-page-name="Default">' + ''.join(items) + '<presentation:notes><draw:frame draw:name="Notes"><draw:text-box><text:p>' + escape(notes) + '</text:p></draw:text-box></draw:frame></presentation:notes></draw:page>')
    page_layout = '<style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="28cm" fo:page-height="21cm" style:print-orientation="landscape"/></style:page-layout>'
    content = (f'<office:document-content {_odp_decls()} office:version="1.2"><office:automatic-styles><style:style style:name="dp1" style:family="drawing-page"><style:drawing-page-properties/></style:style></office:automatic-styles><office:body><office:presentation>' + ''.join(pages) + '</office:presentation></office:body></office:document-content>').encode()
    parts = {
        'mimetype': b'application/vnd.oasis.opendocument.presentation',
        'content.xml': content,
        'styles.xml': (f'<office:document-styles {_odp_decls()} office:version="1.2"><office:automatic-styles>{page_layout}</office:automatic-styles><office:master-styles><style:master-page style:name="Default" style:page-layout-name="pm1"/></office:master-styles></office:document-styles>').encode(),
        'meta.xml': (f'<office:document-meta {_odp_decls()} office:version="1.2"><office:meta/></office:document-meta>').encode(),
        'settings.xml': (f'<office:document-settings {_odp_decls()} office:version="1.2"><office:settings/></office:document-settings>').encode(),
    }
    parts.update(objects)
    entries = ['<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.presentation"/>']
    for name in parts:
        if name == 'mimetype':
            continue
        entries.append(f'<manifest:file-entry manifest:full-path="{name}" manifest:media-type="text/xml"/>')
    for name in manifest_objects:
        entries.append(f'<manifest:file-entry manifest:full-path="{name}/" manifest:media-type="application/vnd.oasis.opendocument.chart"/>')
    parts['META-INF/manifest.xml'] = ('<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">' + ''.join(entries) + '</manifest:manifest>').encode()
    return _zip(parts, odp=True)


def _odp_structure(infos, parts):
    if (parts.get('mimetype') != b'application/vnd.oasis.opendocument.presentation'
            or not infos or infos[0].filename != 'mimetype' or infos[0].compress_type != ZIP_STORED):
        raise PresentationRefused('not_odp')
    required = ('content.xml', 'META-INF/manifest.xml')
    if any(name not in parts for name in required):
        raise PresentationRefused('not_odp')
    manifest_ns = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
    manifest = _xml(parts['META-INF/manifest.xml'])
    if manifest.tag != '{%s}manifest' % manifest_ns or manifest.findall('.//{%s}encryption-data' % manifest_ns):
        raise PresentationRefused('invalid_odp_manifest')
    entries = manifest.findall('{%s}file-entry' % manifest_ns)
    roots = [node for node in entries if node.get('{%s}full-path' % manifest_ns) == '/']
    if len(roots) != 1 or roots[0].get('{%s}media-type' % manifest_ns) != parts['mimetype'].decode():
        raise PresentationRefused('invalid_odp_manifest')
    if not any(node.get('{%s}full-path' % manifest_ns) == 'content.xml' for node in entries):
        raise PresentationRefused('invalid_odp_manifest')
    root = _xml(parts['content.xml'])
    if root.tag != '{%s}document-content' % ODP_NS['office']:
        raise PresentationRefused('not_odp')
    presentation = root.find('./{%s}body/{%s}presentation' % (ODP_NS['office'], ODP_NS['office']))
    if presentation is None:
        raise PresentationRefused('not_odp')
    pages = presentation.findall('./{%s}page' % ODP_NS['draw'])
    if not 1 <= len(pages) <= 200:
        raise PresentationRefused('slide_bounds')
    for page in pages:
        notes = page.findall('./{%s}notes' % ODP_NS['presentation'])
        if len(notes) > 1 or any(node.findall('.//{%s}page' % ODP_NS['draw']) for node in notes):
            raise PresentationRefused('invalid_odp_notes')
    for obj in root.findall('.//{%s}object' % ODP_NS['draw']):
        href = obj.get('{%s}href' % ODP_NS['xlink'])
        if not href or href.startswith('#'):
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname('content.xml'), href)).rstrip('/') + '/content.xml'
        if target not in parts:
            continue
        chart_root = _xml(parts[target])
        charts = chart_root.findall('.//{%s}chart' % ODP_NS['chart'])
        if not charts:
            continue
        if len(charts) != 1:
            raise PresentationRefused('invalid_odp_chart')
        plots = charts[0].findall('./{%s}plot-area' % ODP_NS['chart'])
        series = charts[0].findall('.//{%s}series' % ODP_NS['chart'])
        categories = charts[0].findall('.//{%s}categories' % ODP_NS['chart'])
        if (len(plots) != 1 or not 1 <= len(series) <= 128 or len(categories) != 1
                or any(not node.get('{%s}values-cell-range-address' % ODP_NS['chart']) for node in series)
                or not categories[0].get('{%s}cell-range-address' % ODP_NS['table'])):
            raise PresentationRefused('invalid_odp_chart')
    return root, pages


def _odp_tables(page):
    result = []
    def walk(node):
        for child in node:
            if child.tag == '{%s}notes' % ODP_NS['presentation']:
                continue
            if child.tag == '{%s}table' % ODP_NS['table']:
                result.append(child)
            elif child.tag != '{%s}object' % ODP_NS['draw']:
                walk(child)
    walk(page)
    return result


def _odp_repeat(node, name, maximum):
    raw = node.get('{%s}%s' % (ODP_NS['table'], name), '1')
    if re.fullmatch(r'[0-9]+', raw) is None or not 1 <= int(raw) <= maximum:
        raise PresentationRefused('table_capacity')
    return int(raw)


def _odp_rows(table):
    result = []
    def walk(node):
        for child in node:
            if child.tag == '{%s}table-row' % ODP_NS['table']:
                repeat = _odp_repeat(child, 'number-rows-repeated', 10000)
                result.extend((child, repeat) for _ in range(repeat))
                if len(result) > 10000:
                    raise PresentationRefused('table_capacity')
            elif child.tag in ('{%s}table-header-rows' % ODP_NS['table'], '{%s}table-row-group' % ODP_NS['table']):
                walk(child)
    walk(table)
    return result


def _odp_cells(row):
    result = []
    for cell in row:
        if cell.tag not in ('{%s}table-cell' % ODP_NS['table'], '{%s}covered-table-cell' % ODP_NS['table']):
            continue
        repeat = _odp_repeat(cell, 'number-columns-repeated', 1024)
        result.extend((cell, repeat) for _ in range(repeat))
        if len(result) > 1024:
            raise PresentationRefused('table_capacity')
    return result


def edit_odp(data, spec):
    infos, parts = _parts(data)
    root, pages = _odp_structure(infos, parts)
    index = spec['slide']; table_index = spec['table']; row_index = spec['row']; column_index = spec['column']
    if any(type(value) is not int for value in (index, table_index, row_index, column_index)) or not 1 <= index <= len(pages) or min(table_index, row_index, column_index) < 1:
        raise PresentationRefused('table_address')
    tables = _odp_tables(pages[index-1])
    if table_index > len(tables):
        raise PresentationRefused('table_address')
    rows = _odp_rows(tables[table_index-1])
    if row_index > len(rows):
        raise PresentationRefused('table_address')
    row, row_repeat = rows[row_index-1]
    cells = _odp_cells(row)
    if column_index > len(cells):
        raise PresentationRefused('table_address')
    cell, column_repeat = cells[column_index-1]
    if row_repeat != 1 or column_repeat != 1 or cell.tag != '{%s}table-cell' % ODP_NS['table']:
        raise PresentationRefused('repeated_or_covered_target_unsupported')
    if any(cell.get('{%s}%s' % (ODP_NS['table'], name), '1') != '1'
           for name in ('number-columns-spanned', 'number-rows-spanned')):
        raise PresentationRefused('merged_target_unsupported')
    if '{%s}formula' % ODP_NS['table'] in cell.attrib:
        raise PresentationRefused('formula_target_unsupported')
    old = decimal(spec['old_value']); decimal(spec['new_value'])
    value_type = '{%s}value-type' % ODP_NS['office']
    value_attribute = '{%s}value' % ODP_NS['office']
    if cell.get(value_type) != 'float' or _native_number(cell.get(value_attribute)) != old:
        raise PresentationRefused('old_value_mismatch')
    paragraphs = cell.findall('./{%s}p' % ODP_NS['text'])
    if len(cell) != 1 or len(paragraphs) != 1 or len(paragraphs[0]) != 0:
        raise PresentationRefused('mixed_cell_text_unsupported')
    if _native_number(paragraphs[0].text) != old:
        raise PresentationRefused('ambiguous_cell_text')
    cell.set(value_attribute, spec['new_value'])
    paragraphs[0].text = spec['new_value']
    return _rewrite(infos, parts, {'content.xml': _tostring(root)})


def validate_native(data, expected):
    infos, parts = _parts(data)
    if expected == 'pptx':
        if 'ppt/presentation.xml' not in parts:
            raise PresentationRefused('not_pptx')
        _slide_paths(parts)
    elif expected == 'odp':
        _odp_structure(infos, parts)
    else:
        raise PresentationRefused('unsupported_native_type')
    return True
