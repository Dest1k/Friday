#!/usr/bin/env python3
"""Read existing capsule bytes only; never run Office or create document files.

Run: python3 -B verify.py
Requires Python >=3.10 and openpyxl (verified with 3.1.5). Nothing is installed.
JSON goes to stdout. MATCH below means this exact typed projection only.
"""
import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import stat
import types
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
q = lambda ns, tag: '{' + ns + '}' + tag


class VerificationError(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise VerificationError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode), 'not_regular_file')
    return tuple(getattr(info, key) for key in (
        'st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink',
        'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def differences(left, right, pointer=''):
    if type(left) != type(right):
        return [(pointer, left, right)]
    if isinstance(left, dict):
        rows = []
        for key in sorted(left.keys() | right.keys()):
            if key not in left or key not in right:
                rows.append((pointer + '/' + key, left.get(key), right.get(key)))
            else:
                rows.extend(differences(left[key], right[key], pointer + '/' + key))
        return rows
    if isinstance(left, list):
        if len(left) != len(right):
            return [(pointer, left, right)]
        return [row for index, pair in enumerate(zip(left, right))
                for row in differences(*pair, pointer + '/' + str(index))]
    return [] if left == right else [(pointer, left, right)]


def chart_facts(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        root = ET.fromstring(archive.read('ppt/charts/chart1.xml'))
        rels = ET.fromstring(archive.read('ppt/charts/_rels/chart1.xml.rels'))
        return {
            'workbooks': [n for n in archive.namelist() if n.startswith('ppt/embeddings/')],
            'externalData': len(root.findall(q(C, 'externalData'))),
            'package_relationships': sum(n.get('Type') == R + '/package' for n in rels),
            'native_bar_charts': len(list(root.iter(q(C, 'barChart')))),
            'series': len(list(root.iter(q(C, 'ser')))),
            'formulas': [n.text for n in root.iter(q(C, 'f'))],
            'cached_values': [n.text for n in root.iter(q(C, 'v'))],
            'explicit_titles': [[n.text or '' for n in title.iter(q(A, 't'))]
                                for title in root.findall('./' + q(C, 'chart') + '/' + q(C, 'title'))],
            'category_axis_numFmt': [dict(n.attrib) for n in root.findall('.//' + q(C, 'catAx') + '/' + q(C, 'numFmt'))],
        }


def expanded_package_checks(raw, depth=0):
    """Check all XML/metadata, nested XLSX, ZIP comments and known binary parts.

    This is a reproducible check for the declared synthetic capsule, not a
    general secret detector. Human template/thumbnail inspection is in STATUS.
    """
    need(depth <= 1, 'unexpected_nested_archive_depth')
    counts = {'archives': 1, 'members': 0, 'xml_parts': 0, 'binary_parts': 0}
    markers = re.compile(r'/(?:home|Users|tmp|run|private)/|file:/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:api[_-]?key|password|secret|bearer)\s*[:=]', re.I)
    binaries = {
        'ppt/printerSettings/printerSettings1.bin': 'd7768f87e07d29634782e448ece1cddd05a52b9499254222b1190bc8f6dc579e',
        'docProps/thumbnail.jpeg': '116f9aa8ea038e39ef47ee99a23592ab569cf77feafecd0a30e222369e931d25',
    }
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(not archive.comment, 'unexpected_archive_comment')
        for info in archive.infolist():
            counts['members'] += 1
            need(not info.comment and not info.extra, 'unexpected_member_metadata')
            data = archive.read(info)
            if data.startswith(b'PK\x03\x04'):
                for key, value in expanded_package_checks(data, depth + 1).items():
                    counts[key] += value
            elif info.filename.endswith(('.xml', '.rels')):
                counts['xml_parts'] += 1
                text = data.decode('utf-8')
                need(not markers.search(text), 'private_path_contact_or_credential_marker')
                root = ET.fromstring(data)
                for node in root.iter():
                    need(node.get('TargetMode', 'Internal') == 'Internal', 'external_relationship')
                    if node.tag.rsplit('}', 1)[-1] in ('creator', 'lastModifiedBy'):
                        need((node.text or '') in ('', 'Steve Canny'), 'unexpected_creator_metadata')
            else:
                counts['binary_parts'] += 1
                need(binaries.get(info.filename) == sha(data), 'unexpected_binary_part')
    return counts


def main():
    manifest = json.loads((HERE / 'MANIFEST.json').read_bytes())
    names = set(manifest['files']) | {'MANIFEST.json'}
    need({p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()} == names,
         'capsule_file_set_changed')
    before = {name: identity(HERE / name) for name in names}
    before_hashes = {name: sha((HERE / name).read_bytes()) for name in names}
    for name, record in manifest['files'].items():
        need(not (HERE / name).is_symlink(), 'symlink_in_capsule')
        need(before_hashes[name] == record['sha256'] and (HERE / name).stat().st_size == record['bytes'],
             'manifest_mismatch')
    contract = runpy.run_path(str(HERE / 'code/presentation_contract.py'))
    parser = contract['PARSER']
    observe, compare = contract['observe'], contract['compare']
    raw = {key: (HERE / 'artifacts' / name).read_bytes() for key, name in (
        ('original', 'known-synthetic.pptx'), ('resaved', 'actual-resaved.pptx'),
        ('reopened', 'actual-reopened.pptx'))}
    expectation = json.loads((HERE / 'original-expectation.json').read_bytes())
    observed = {key: observe(data, 'pptx') for key, data in raw.items()}
    comparison = {key: compare(value, expectation) for key, value in observed.items()}
    need([comparison[k]['status'] for k in ('original', 'resaved', 'reopened')] ==
         ['MATCH', 'DIFFERENT', 'DIFFERENT'], 'original_expectation_comparison_changed')
    need(all(value['coverage_preserved'] for value in comparison.values()), 'typed_coverage_changed')
    pair_expectation = contract['expectation'](raw['resaved'], 'pptx', 'IN_MEMORY_TYPED_PAIR_ONLY', True)
    pair = compare(observed['reopened'], pair_expectation)
    need(pair['status'] == 'MATCH', 'saved_pair_no_longer_matches_typed_projection')

    # Reconstruct only the previous parser in memory; do not install it or write it.
    fixed_source = (HERE / 'code/scoped_presentation.py').read_text()
    added = ("        # Paragraph tab stops configure layout; only text/run tabs are content.\n"
             "        tab_stops = {tab for tabs in paragraph.findall('./'+q(A, 'pPr')+'/'+q(A, 'tabLst'))\n"
             "                     for tab in tabs.findall(q(A, 'tab'))}\n")
    need(fixed_source.count(added) == 1, 'minimal_delta_context_changed')
    old_source = fixed_source.replace(added, '').replace(
        "part.tag == q(A, 'tab') and part not in tab_stops", "part.tag == q(A, 'tab')")
    need(sha(old_source.encode()) == '285591a979085cc294aec2e366a0d8714d01ab928068693c199aa2ef71990a3c',
         'previous_parser_reconstruction_changed')
    old_parser = {'__name__': 'previous_parser_in_memory'}
    exec(compile(old_source, '<previous_parser_in_memory>', 'exec'), old_parser)
    old_observe = types.FunctionType(observe.__code__, dict(contract, extract_presentation=old_parser['extract_presentation']))
    old = {key: old_observe(data, 'pptx') for key, data in raw.items()}
    need(old['original'] == observed['original'] and old['resaved'] == observed['resaved'],
         'unaffected_observations_changed')
    delta = differences(old['reopened']['semantic_projection'], observed['reopened']['semantic_projection'])
    need(delta == [('/slides/0/content/0/text', '\tQuarterly report', 'Quarterly report'),
                   ('/slides/0/notes/content/0/text', '\tSpeaker note α', 'Speaker note α'),
                   ('/slides/1/content/0/text', '\tSecond slide', 'Second slide')],
         'fix_is_not_exactly_three_layout_tabs')

    facts = {key: chart_facts(data) for key, data in raw.items()}
    need(len(facts['original']['workbooks']) == facts['original']['externalData'] ==
         facts['original']['package_relationships'] == 1, 'original_workbook_binding_changed')
    need(facts['original']['formulas'] == ['Sheet1!$B$1', 'Sheet1!$A$2:$A$3', 'Sheet1!$B$2:$B$3'],
         'original_cell_references_changed')
    need(facts['original']['explicit_titles'] == [] and facts['original']['category_axis_numFmt'] == [],
         'original_chart_style_changed')
    for key, linked in (('resaved', '1'), ('reopened', '0')):
        fact = facts[key]
        need(not fact['workbooks'] and fact['externalData'] == fact['package_relationships'] == 0,
             'recorded_workbook_loss_changed')
        need(fact['formulas'] == ['label 0', 'categories', '0'] and fact['explicit_titles'] == [['RUB']],
             'recorded_formula_title_change_changed')
        need(fact['category_axis_numFmt'] == [{'formatCode': '[$-409]mm/dd/yyyy', 'sourceLinked': linked}],
             'recorded_axis_style_drift_changed')
    need(all(fact['native_bar_charts'] == fact['series'] == 1 and fact['cached_values'] ==
             ['RUB', 'A01', 'B02', '3601.5', '1499.7'] for fact in facts.values()),
         'native_chart_or_cached_data_changed')
    nonchart = []
    for value in observed.values():
        slides = copy.deepcopy(value['semantic_projection']['slides'])
        need(slides[0]['content'].pop(2)['kind'] == 'chart', 'chart_role_changed')
        nonchart.append(slides)
    need(nonchart[0] == nonchart[1] == nonchart[2] and len(nonchart[0]) == 2,
         'nonchart_text_notes_table_slide_order_changed')

    literal_whitespace_controls = 0
    with zipfile.ZipFile(io.BytesIO(raw['reopened'])) as archive:
        for name, text in (('ppt/slides/slide1.xml', 'Quarterly report'),
                           ('ppt/slides/slide2.xml', 'Second slide'),
                           ('ppt/notesSlides/notesSlide1.xml', 'Speaker note α')):
            root = ET.fromstring(archive.read(name))
            shape = next(n for n in root.iter(q(P, 'sp')) if any(t.text == text for t in n.iter(q(A, 't'))))
            need(old_parser['drawing_text'](shape) == '\t' + text and parser['drawing_text'](shape) == text,
                 'layout_tab_not_distinguished')
            for actual in ('\t' + text, ' ' + text, text + '\t', text + '\ncontinued'):
                changed = copy.deepcopy(shape)
                next(changed.iter(q(A, 't'))).text = actual
                need(parser['drawing_text'](changed) == actual, 'real_literal_whitespace_lost')
                literal_whitespace_controls += 1
            changed = copy.deepcopy(shape)
            next(changed.iter(q(A, 'p'))).append(ET.Element(q(A, 'br')))
            need(parser['drawing_text'](changed) == text + '\n', 'explicit_break_lost')
    node = ET.fromstring('<a:p xmlns:a="' + A + '"><a:r><a:t>one</a:t></a:r><a:tab/><a:fld><a:t>two</a:t></a:fld><a:br/></a:p>')
    need(parser['drawing_text'](node) == old_parser['drawing_text'](node) == 'one\ttwo\n',
         'explicit_tab_field_or_break_lost')

    mutations = {
        'title_text': lambda o: o['semantic_projection']['slides'][0]['content'][0].update(text='Quarterly report\t'),
        'table_value': lambda o: o['semantic_projection']['slides'][0]['content'][1]['rows'][0].__setitem__(1, '3601.51'),
        'chart_cached_value': lambda o: o['semantic_projection']['slides'][0]['content'][2]['series'][0]['val']['values'].__setitem__(0, '3601.6'),
        'chart_formula_reference': lambda o: o['semantic_projection']['slides'][0]['content'][2]['series'][0]['val']['formulas'].__setitem__(0, 'Sheet1!$C$2:$C$3'),
        'chart_workbook_association': lambda o: o['semantic_projection']['slides'][0]['content'][2].update(embedded_data=[]),
        'workbook_cell': lambda o: o['semantic_projection']['embedded_workbooks'][0]['sheets_formulas']['Sheet1'][2].update(value=3601.6),
        'note_text': lambda o: o['semantic_projection']['slides'][0]['notes']['content'][0].update(text='Speaker note β'),
        'note_role': lambda o: o['semantic_projection']['slides'][0].update(notes={'status': 'absent', 'content': []}),
        'slide_order': lambda o: o['semantic_projection']['slides'].reverse(),
        'slide_removed': lambda o: o['semantic_projection']['slides'].pop(),
        'external_link_guard': lambda o: o['structural_projection']['metadata'].update(external_relationships_not_resolved=1),
    }
    negatives = {}
    for name, mutate in mutations.items():
        changed = copy.deepcopy(observed['original'])
        mutate(changed)
        changed['semantic_sha256'] = sha(contract['json_bytes'](changed['semantic_projection']))
        result = compare(changed, expectation)
        need(result['status'] == 'DIFFERENT', 'typed_negative_accepted_' + name)
        if name == 'external_link_guard':
            need(not result['coverage_preserved'], 'external_link_guard_bypassed')
        negatives[name] = 'DIFFERENT'
    package_checks = {key: expanded_package_checks(data) for key, data in raw.items()}
    need(all(identity(HERE / name) == before[name] and sha((HERE / name).read_bytes()) == before_hashes[name]
             for name in names), 'verification_changed_capsule')
    need({p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()} == names,
         'verification_created_files')
    return {
        'status': 'PASS', 'manifest_files_verified': len(manifest['files']),
        'original_expectation_comparisons': {key: value['status'] for key, value in comparison.items()},
        'resaved_to_reopened': 'MATCH_TYPED_PROJECTION_ONLY',
        'semantic_sha256': {key: value['semantic_sha256'] for key, value in observed.items()},
        'parser_delta': 'EXACTLY_THREE_LAYOUT_TABS_REMOVED',
        'real_literal_whitespace_controls': literal_whitespace_controls,
        'explicit_break_controls': 3, 'explicit_tab_field_break_control': 'PASS',
        'typed_negative_controls': negatives, 'raw_chart_facts': facts,
        'expanded_package_checks': package_checks, 'all_capsule_bytes_and_identity_unchanged': True,
        'document_generation_office_network_or_install': False,
        'original_actual_qualification': 'DIFFERENT_EXIT_2_PRESERVED_NO_NEW_QUALIFICATION',
        'render_visual_full_format_or_user_acceptance': False,
    }


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False, sort_keys=True, indent=2))
    except Exception as error:
        result = {'status': 'FAIL', 'error_class': type(error).__name__}
        if isinstance(error, VerificationError):
            result['check'] = str(error)
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(1)
