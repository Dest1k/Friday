"""Unchanged AST-selected pure preservation helpers; provenance in PROVENANCE.json.
No product runtime imports or workbook-specific defaults.
"""
import re
from xml.etree import ElementTree as ET
from xml.parsers import expat

O = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'

T = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'

TB = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'

D = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'

q = lambda ns, local: '{' + ns + '}' + local

CELL_TAGS = {q(TB, 'table-cell'), q(TB, 'covered-table-cell')}

ROW_GROUPS = {q(TB, n) for n in ('table-header-rows', 'table-row-group', 'table-rows')}

def need(value, code):
    if not value:
        raise AssertionError(code)

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

def node_span(raw, root, node):
    span = element_spans(raw)[list(root.iter()).index(node)]
    need(span['tag'] == node.tag, 'independent_span_node_alignment')
    return span
