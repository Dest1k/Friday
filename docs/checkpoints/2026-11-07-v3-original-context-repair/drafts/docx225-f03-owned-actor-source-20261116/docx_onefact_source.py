"""Pure saved-byte DOCX onefact check; no reads, writes, edit or runtime effects.

The caller pins/loads office_semantics.py and passes its inspect callable.
This helper permits exactly one Unicode character substitution in an exact,
unique paragraph literal within the main BODY (including table paragraphs).
No metadata part is exempted. p10 remains an external selection label.
"""
from __future__ import annotations
import hashlib
import io
import zipfile
from xml.etree import ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
Q = '{' + W + '}'


def _need(ok, why):
    if not ok:
        raise ValueError(why)


def _xml(raw):
    # Package safety/size/DTD checks have already run through office.inspect.
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    return ET.fromstring(raw, parser=parser)


def _fingerprint(e):
    # ET uses function objects for comment/PI tags; stable within this process.
    return (e.tag, tuple(sorted(e.attrib.items())), e.text, e.tail,
            tuple(_fingerprint(c) for c in e))


def _namespaces(raw):
    # Pin each declaration to its element path as well as prefix/URI.
    pending, paths, child_counts, result = [], [], [], []
    for event, value in ET.iterparse(io.BytesIO(raw), events=('start-ns', 'start', 'end')):
        if event == 'start-ns':
            pending.append(value)
        elif event == 'start':
            if paths:
                path = paths[-1] + (child_counts[-1],)
                child_counts[-1] += 1
            else:
                path = ()
            result.extend((path, prefix, uri) for prefix, uri in pending)
            pending.clear()
            paths.append(path)
            child_counts.append(0)
        else:
            paths.pop()
            child_counts.pop()
    return tuple(result)


def _outside_misc(raw):
    depth, result, root_seen = 0, [], False
    for event, value in ET.iterparse(io.BytesIO(raw), events=('start', 'end', 'comment', 'pi')):
        if event == 'start':
            root_seen = True
            depth += 1
        elif event == 'end':
            depth -= 1
        elif depth == 0:
            # Prolog and epilog placement is part of document-level custody.
            result.append((root_seen, event, value.text))
    return tuple(result)


def _paragraph_text(e):
    pieces = []
    for n in e.iter():
        if n.tag == Q + 't':
            pieces.append(n.text or '')
        elif n.tag == Q + 'tab':
            pieces.append('\t')
        elif n.tag in (Q + 'br', Q + 'cr'):
            pieces.append('\n')
        elif n.tag in (Q + 'txbxContent', Q + 'sym'):
            raise ValueError('unsupported target content')
    return ''.join(pieces)


def assess_onefact(before: bytes, saved: bytes, *, source: dict,
                   selection: dict, inspect_office) -> dict:
    """Validate exact before pin, one literal edit, and complete part preservation.

    source exactly {sha256: str, bytes: int}; selection exactly
    {part: 'word/document.xml', literal_before: str, literal_after: str}.
    inspect_office is the pinned Office module's inspect(data, 'docx').
    Any failed/unsupported claim raises ValueError (including Unsupported).
    """
    _need(type(before) is bytes and type(saved) is bytes, 'byte inputs required')
    _need(type(source) is dict and set(source) == {'sha256', 'bytes'}, 'source schema')
    _need(type(source['bytes']) is int and source['bytes'] == len(before), 'before size mismatch')
    _need(type(source['sha256']) is str and source['sha256'] == hashlib.sha256(before).hexdigest(), 'before hash mismatch')
    _need(type(selection) is dict and set(selection) == {'part', 'literal_before', 'literal_after'}, 'selection schema')
    part = selection['part']
    old, new = selection['literal_before'], selection['literal_after']
    _need(part == 'word/document.xml', 'only exact main BODY selection supported')
    _need(type(old) is str and type(new) is str and old and len(old) == len(new), 'equal-length literals required')
    changes = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
    _need(len(changes) == 1, 'exactly one character substitution required')
    previous, current = inspect_office(before, 'docx'), inspect_office(saved, 'docx')
    _need(previous['main_part'] == current['main_part'] == part, 'main part changed')
    _need(set(previous['parts']) == set(current['parts']), 'OPC part set changed')
    changed = sorted(p for p in previous['parts'] if previous['parts'][p] != current['parts'][p])
    _need(changed == [part], 'only main part may change')
    # inspect validated duplicate names, sizes, CRC, OPC roots and safety first.
    with zipfile.ZipFile(io.BytesIO(before)) as z:
        before_xml = z.read(part)
    with zipfile.ZipFile(io.BytesIO(saved)) as z:
        saved_xml = z.read(part)
    _need(_namespaces(before_xml) == _namespaces(saved_xml), 'namespace declarations changed')
    _need(_outside_misc(before_xml) == _outside_misc(saved_xml), 'document-level comments/PIs changed')
    expected, actual = _xml(before_xml), _xml(saved_xml)
    bodies = expected.findall(Q + 'body')
    _need(len(bodies) == 1, 'one BODY required')
    body = bodies[0]
    _need(not list(body.iter(Q + 'txbxContent')), 'textbox target unsupported')
    paragraphs = list(body.iter(Q + 'p'))
    texts = [_paragraph_text(p) for p in paragraphs]
    _need(sum(t.count(old) for t in texts) == 1, 'before literal must occur once in BODY paragraphs')
    candidates = [p for p, t in zip(paragraphs, texts) if t == old]
    _need(len(candidates) == 1, 'exact unique full paragraph literal required')
    paragraph = candidates[0]
    _need(not any(e.tag in (Q + t for t in ('tab', 'br', 'cr', 'fldChar', 'fldSimple', 'instrText')) for e in paragraph.iter()), 'target must consist of plain text runs')
    offset = changes[0]
    for n in paragraph.iter(Q + 't'):
        s = n.text or ''
        if offset < len(s):
            _need(s[offset] == old[changes[0]], 'selected character mismatch')
            n.text = s[:offset] + new[changes[0]] + s[offset + 1:]
            break
        offset -= len(s)
    else:
        raise ValueError('target character not in text node')
    _need(_fingerprint(expected) == _fingerprint(actual), 'main XML differs beyond selected character')
    return {'schema': 'frw.Source.docx-onefact-assessment.v1',
            'before': dict(source),
            'saved': {'sha256': hashlib.sha256(saved).hexdigest(), 'bytes': len(saved)},
            'selection': dict(selection), 'changed_parts': changed,
            'all_other_part_hashes_equal': True, 'part_set_equal': True,
            'main_xml_tree_exact_except_selected_character': True,
            'target_body_paragraph_ordinal_zero_based_including_tables': paragraphs.index(paragraph),
            'semantic_scope': 'EXACT_SINGLE_CHARACTER_BODY_FACT_AND_OTHER_OPC_PART_BYTES',
            'receiver_custody': 'EXTERNAL_JOIN_REQUIRED',
            'office_rendering': 'NOT_ASSESSED'}
