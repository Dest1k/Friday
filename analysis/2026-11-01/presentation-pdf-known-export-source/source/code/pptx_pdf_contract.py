"""Finite PPTX -> PDF content-projection contract; no Office or network execution."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy
import stat
import zipfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PPTX_MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
PDF_MIME = 'application/pdf'
EXPORT_FILTER = 'pdf:impress_pdf_Export'
ENGINE = '/opt/friday-archive/toolchains/libreoffice-26.2.5.2-ubuntu26.04-amd64/root/usr/lib/libreoffice/program/soffice.bin'
STRACE = '/usr/bin/strace'
PDFTOTEXT = '/usr/bin/pdftotext'
READER_SHA256 = '19f28c155fc7e55636df628d94e254c51291d24275a78b9023786ec13b68246f'
MAX_PPTX_BYTES = 1_000_000
MAX_PDF_BYTES = 8_000_000
MAX_PAGES = 64
MAX_PAGE_TEXT = 1_000_000
NUMERIC = re.compile(r'[-+]?(?:[0-9]+(?:\.[0-9]+)?|[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?)\Z')
NUMBER_IN_TEXT = re.compile(r'(?<![A-Za-z0-9_])[-+]?(?:[0-9]+(?:\.[0-9]+)?|[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?)(?![A-Za-z0-9_])')
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    need(len(raw) <= 2_000_000, 'JSON observation cap')
    return raw


def reference(value):
    return (type(value) is dict and set(value) == {'path', 'sha256'}
            and type(value['path']) is str and value['path'].startswith('/')
            and not value['path'].startswith('//')
            and all(part not in ('', '.', '..') for part in value['path'].split('/')[1:])
            and type(value['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', value['sha256']) is not None)


def artifact_reference(value):
    return reference({k: value.get(k) for k in ('path', 'sha256')}) if type(value) is dict else False


def artifact(value, cap=MAX_PDF_BYTES):
    need(type(value) is dict and set(value) == {'path', 'sha256', 'bytes'}, 'EXACT_ARTIFACT_REFERENCE_REQUIRED')
    need(reference({k: value[k] for k in ('path', 'sha256')}), 'EXACT_ARTIFACT_PIN_REQUIRED')
    need(type(value['bytes']) is int and not isinstance(value['bytes'], bool) and 0 < value['bytes'] <= cap, 'ARTIFACT_BYTE_BOUND')
    return value


def reject_interfaces(value):
    if type(value) is dict:
        need(not {'argv', 'shell', 'payload', 'command', 'command_text', 'mock_consumer', 'runtime_authenticator'} & value.keys(),
             'ARBITRARY_OR_MOCK_NESTED_INTERFACE')
        for item in value.values():
            reject_interfaces(item)
    elif type(value) is list:
        for item in value:
            reject_interfaces(item)
    elif type(value) is str:
        need('UNBOUND' not in value, 'ACTUAL_BINDING_UNBOUND')


def fixed_engine_argv(engine, profile, output, source):
    """The only Office conversion argv admitted by this package."""
    for value in (engine, profile, output, source):
        need(type(value) is str and value.startswith('/') and '\x00' not in value, 'CANONICAL_FIXED_PATH_REQUIRED')
    need(engine in (ENGINE, '/opt/friday-archive/bin/libreoffice',
                    '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/soffice'),
         'FIXED_OFFICE_ENGINE_REQUIRED')
    return [engine, '-env:UserInstallation=file://' + profile, '--headless', '--nologo', '--nodefault',
            '--nofirststartwizard', '--norestore', '--convert-to', EXPORT_FILTER,
            '--outdir', output, source]


def normalized_text(value):
    need(type(value) is str and len(value.encode('utf-8')) <= MAX_PAGE_TEXT, 'PAGE_TEXT_CAP')
    return ' '.join(value.split())


def contains_token(text, token):
    """Whitespace-normalized literal tokens; numeric tokens cannot be substrings."""
    need(type(token) is str and bool(token.strip()), 'EMPTY_EXPECTATION_TOKEN')
    haystack = normalized_text(text)
    needle = normalized_text(token)
    if NUMERIC.fullmatch(needle):
        return re.search(r'(?<![A-Za-z0-9_+-])' + re.escape(needle) + r'(?![A-Za-z0-9_+-])', haystack) is not None
    return needle in haystack


def _numeric_values(values, role):
    need(type(values) is list and len(values) <= 128, role + '_CAP')
    need(all(type(v) is str and NUMERIC.fullmatch(v.strip()) for v in values), role + '_NUMERIC_TOKEN_REQUIRED')
    result = [v.strip() for v in values]
    need(len(set(result)) == len(result), role + '_DUPLICATE_VALUES')
    return result


def validate_expectation(expected, input_sha256=None, input_bytes=None):
    fields = {'schema', 'format', 'input_sha256', 'input_bytes', 'pptx_semantic_sha256', 'pages',
              'chart_label_source', 'table_source', 'normalization', 'source_only_fixture',
              'full_format_acceptance', 'visual_acceptance', 'editable_preservation'}
    need(type(expected) is dict and set(expected) == fields, 'EXACT_PPTX_PDF_EXPECTATION_FIELDS')
    need(expected['schema'] == 'frw.Root.pptx-pdf-known-input-expectation.v1' and expected['format'] == 'pptx',
         'PPTX_PDF_EXPECTATION_SCHEMA_REQUIRED')
    need(re.fullmatch(r'[0-9a-f]{64}', expected['input_sha256']) is not None
         and re.fullmatch(r'[0-9a-f]{64}', expected['pptx_semantic_sha256']) is not None, 'EXPECTATION_HASH_REQUIRED')
    need(type(expected['input_bytes']) is int and 0 < expected['input_bytes'] <= MAX_PPTX_BYTES, 'EXPECTATION_INPUT_BYTES')
    if input_sha256 is not None:
        need(expected['input_sha256'] == input_sha256, 'EXPECTATION_INPUT_SHA_MISMATCH')
    if input_bytes is not None:
        need(expected['input_bytes'] == input_bytes, 'EXPECTATION_INPUT_BYTES_MISMATCH')
    need(type(expected['source_only_fixture']) is bool, 'FIXTURE_PROVENANCE_REQUIRED')
    need(expected['normalization'] == {'whitespace': 'collapse', 'numeric': 'exact-token-no-coercion'},
         'DECLARED_NUMERIC_NORMALIZATION_REQUIRED')
    need(expected['full_format_acceptance'] is False and expected['visual_acceptance'] == 'NOT_OBSERVED'
         and expected['editable_preservation'] == 'FAIL_RETAINED', 'PRESERVED_PPTX_FAILURE_AND_VISUAL_GAP_REQUIRED')
    pages = expected['pages']
    need(type(pages) is list and 2 <= len(pages) <= MAX_PAGES, 'AT_LEAST_TWO_ORDERED_PAGES_REQUIRED')
    chart_all, table_all = [], []
    for index, page in enumerate(pages, 1):
        need(type(page) is dict and set(page) == {'page', 'text_tokens', 'chart_numeric_labels', 'table_numeric_cells'},
             'EXACT_PAGE_EXPECTATION_FIELDS')
        need(page['page'] == index and type(page['text_tokens']) is list and page['text_tokens'], 'ORDERED_PAGE_TEXT_REQUIRED')
        need(all(type(token) is str and token.strip() and len(token) <= 256 for token in page['text_tokens']), 'PAGE_TOKEN_CAP')
        chart = _numeric_values(page['chart_numeric_labels'], 'CHART')
        table = _numeric_values(page['table_numeric_cells'], 'TABLE')
        need(set(chart).isdisjoint(table), 'DUPLICATE_TABLE_CHART_VALUES_CANNOT_PROVE_CHART')
        need(all(contains_token(' '.join(page['text_tokens']), token) for token in chart + table),
             'ROLE_TOKEN_MUST_BE_INDEPENDENTLY_DECLARED_IN_PAGE_TEXT')
        chart_all.extend(chart)
        table_all.extend(table)
    need(chart_all and table_all and set(chart_all).isdisjoint(table_all), 'DISTINCT_CHART_AND_TABLE_EVIDENCE_REQUIRED')
    need(type(expected['chart_label_source']) is dict
         and expected['chart_label_source'].get('part', '').startswith('ppt/charts/')
         and expected['chart_label_source'].get('showVal') is True
         and expected['chart_label_source'].get('values') == chart_all,
         'VISIBLE_CHART_LABEL_PROVENANCE_REQUIRED')
    need(type(expected['table_source']) is dict
         and expected['table_source'].get('part', '').startswith('ppt/slides/')
         and expected['table_source'].get('values') == table_all,
         'TABLE_CELL_PROVENANCE_REQUIRED')
    return expected


def _presentation_contract():
    return runpy.run_path(str(HERE / 'presentation_contract.py'))


def observe_pptx(data):
    need(type(data) is bytes and 0 < len(data) <= MAX_PPTX_BYTES, 'PPTX_BYTE_BOUND')
    return _presentation_contract()['observe'](data, 'pptx')


def _chart_labels(data):
    ns = {'c': C}
    found = []
    with zipfile.ZipFile(__import__('io').BytesIO(data)) as archive:
        names = [n for n in archive.namelist() if n.startswith('ppt/charts/') and n.endswith('.xml')]
        need(names, 'CHART_SOURCE_PART_REQUIRED')
        for name in sorted(names):
            raw = archive.read(name)
            need(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'CHART_XML_DECLaration_FORBIDDEN')
            root = ET.fromstring(raw)
            for chart in root.findall('.//c:barChart', ns) + root.findall('.//c:lineChart', ns):
                labels = chart.find('c:dLbls', ns)
                if labels is None:
                    labels = chart.find('c:ser/c:dLbls', ns)
                show = labels is not None and labels.find('c:showVal', ns) is not None and labels.find('c:showVal', ns).get('val') == '1'
                if not show:
                    continue
                values = [v.text or '' for v in chart.findall('c:ser/c:val/c:numRef/c:numCache/c:pt/c:v', ns)]
                found.append({'part': name, 'showVal': True, 'values': values})
    need(found, 'VISIBLE_CHART_DATA_LABELS_REQUIRED')
    return found


def _table_values(observed):
    values = []
    for slide in observed['semantic_projection']['slides']:
        for item in slide['content']:
            if item.get('kind') == 'table':
                for row in item.get('rows', []):
                    for cell in row:
                        if NUMERIC.fullmatch(str(cell).strip()):
                            values.append(str(cell).strip())
    return values


def expectation_from_pptx(data, pages, source_only_fixture=True):
    """Bind predeclared page expectations to independently inspected PPTX source facts."""
    observed = observe_pptx(data)
    need(observed['bounded_native_admission'] is True, 'UNSAFE_PPTX_SOURCE')
    charts = _chart_labels(data)
    chart_values = [value for chart in charts for value in chart['values']]
    table_values = _table_values(observed)
    expected = {
        'schema': 'frw.Root.pptx-pdf-known-input-expectation.v1', 'format': 'pptx',
        'input_sha256': digest(data), 'input_bytes': len(data),
        'pptx_semantic_sha256': observed['semantic_sha256'], 'pages': pages,
        'chart_label_source': {'part': charts[0]['part'], 'showVal': True, 'values': chart_values},
        'table_source': {'part': 'ppt/slides/slide1.xml', 'values': table_values},
        'normalization': {'whitespace': 'collapse', 'numeric': 'exact-token-no-coercion'},
        'source_only_fixture': bool(source_only_fixture), 'full_format_acceptance': False,
        'visual_acceptance': 'NOT_OBSERVED', 'editable_preservation': 'FAIL_RETAINED',
    }
    return validate_expectation(expected)


def validate_source_expectation(data, expected):
    validate_expectation(expected, digest(data), len(data))
    regenerated = expectation_from_pptx(data, expected['pages'], expected['source_only_fixture'])
    need(regenerated == expected, 'EXACT_SOURCE_CHART_TABLE_EXPECTATION_REQUIRED')
    return expected


def compare_pdf_pages(page_texts, expected):
    """Compare authoritative per-page text, including independent numeric roles."""
    validate_expectation(expected)
    need(type(page_texts) is list and len(page_texts) == len(expected['pages']), 'PDF_PAGE_COUNT_MISMATCH')
    need(all(type(page) is str for page in page_texts), 'PDF_PAGE_TEXT_TYPE')
    missing = []
    for index, (actual, wanted) in enumerate(zip(page_texts, expected['pages']), 1):
        need(not re.search(r'\[page [0-9]+\]|\[end of page view', actual), 'PDF_PAGE_DELIMITER_COLLISION')
        for role, tokens in (('text', wanted['text_tokens']),
                             ('chart', wanted['chart_numeric_labels']),
                             ('table', wanted['table_numeric_cells'])):
            for token in tokens:
                if not contains_token(actual, token):
                    missing.append({'page': index, 'role': role, 'token': token})
    result = {'status': 'MATCH' if not missing else 'DIFFERENT', 'page_count': len(page_texts),
              'missing': missing, 'normalization': expected['normalization'],
              'chart_table_evidence': 'INDEPENDENT_VISIBLE_LABELS_AND_TABLE_CELLS',
              'render_visual_comparison': 'NOT_OBSERVED', 'editable_preservation': 'FAIL_RETAINED',
              'full_format_acceptance': False}
    return result


def pdf_observation(data, page_texts, expected, reader, path):
    artifact({'path': str(path), 'sha256': digest(data), 'bytes': len(data)})
    need(type(data) is bytes and 0 < len(data) <= MAX_PDF_BYTES and data.startswith(b'%PDF-'), 'ACTUAL_PDF_BYTES_REQUIRED')
    comparison = compare_pdf_pages(page_texts, expected)
    return {'schema': 'frw.Root.pptx-pdf-content-observation.v1', 'artifact': {
                'path': str(path), 'sha256': digest(data), 'bytes': len(data)},
            'pages': list(page_texts), 'comparison': comparison, 'reader': reader,
            'page_semantics': 'AUTHORITATIVE_LOCAL_PDFTOTEXT_PAGE_VIEW_ONLY',
            'ocr_or_hosted_fallback': False, 'visual_acceptance': 'NOT_OBSERVED',
            'editable_preservation': 'FAIL_RETAINED', 'full_format_acceptance': False}


def validate_pdf_observation(observed, data, expected):
    need(type(observed) is dict and observed.get('schema') == 'frw.Root.pptx-pdf-content-observation.v1',
         'PDF_OBSERVATION_SCHEMA_REQUIRED')
    artifact(observed.get('artifact'))
    need(observed['artifact']['sha256'] == digest(data) and observed['artifact']['bytes'] == len(data),
         'PDF_OBSERVATION_ARTIFACT_JOIN')
    need(observed.get('comparison') == compare_pdf_pages(observed.get('pages'), expected), 'PDF_OBSERVATION_RECOMPUTE_MISMATCH')
    need(observed.get('ocr_or_hosted_fallback') is False and observed.get('visual_acceptance') == 'NOT_OBSERVED'
         and observed.get('full_format_acceptance') is False, 'PDF_OBSERVATION_COVERAGE_REQUIRED')
    return observed


def admit_original(path, expected_sha256, expected_bytes, mime):
    """Read and statically admit an original before any helper or output mutation."""
    need(mime == PPTX_MIME, 'ORIGINAL_MIME_MISMATCH')
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path, 'NONCANONICAL_ORIGINAL_PATH')
    protected = False
    for parent in path.parents:
        info = parent.lstat()
        need(stat.S_ISDIR(info.st_mode) and not parent.is_symlink(), 'NONCANONICAL_ORIGINAL_ANCESTOR')
        protected = protected or (info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077)
    before = path.lstat()
    need(protected and stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
         and before.st_nlink == 1 and not stat.S_IMODE(before.st_mode) & 0o002, 'UNOWNED_OR_WRITABLE_ORIGINAL')
    identity = path_identity(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        need(info.st_size == expected_bytes and 0 < info.st_size <= MAX_PPTX_BYTES, 'ORIGINAL_BYTE_LENGTH_MISMATCH')
        raw = stream.read(MAX_PPTX_BYTES + 1)
        need(len(raw) == info.st_size and os.fstat(stream.fileno()).st_ino == info.st_ino, 'ORIGINAL_READ_DRIFT')
    need(digest(raw) == expected_sha256, 'ORIGINAL_SHA_MISMATCH')
    observed = observe_pptx(raw)
    need(observed['bounded_native_admission'] is True, 'UNSAFE_ORIGINAL_CONTENT')
    need(path_identity(path) == identity and digest(raw) == expected_sha256, 'ORIGINAL_CUSTODY_DRIFT')
    return {'data': raw, 'observation': observed, 'identity': identity, 'path': str(path)}


def custody_unchanged(path, admitted):
    need(path_identity(path) == admitted['identity'], 'ORIGINAL_IDENTITY_REPLACED')
    need(digest(Path(path).read_bytes()) == digest(admitted['data']), 'ORIGINAL_BYTES_REPLACED')
    return True


def resource_admission(remaining_seconds, cpu_seconds_remaining, cleanup_reserve=12, cpu_count=2):
    need(all(type(v) in (int, float) and not isinstance(v, bool) and math.isfinite(v)
             for v in (remaining_seconds, cpu_seconds_remaining, cleanup_reserve)), 'FINITE_RESOURCE_VALUES_REQUIRED')
    need(cpu_count >= 2 and cpu_seconds_remaining > 0, 'INSUFFICIENT_CPU_REMAINING')
    need(remaining_seconds > cleanup_reserve + 5, 'INSUFFICIENT_CLEANUP_RESERVE')
    return {'reader_timeout_seconds': min(20.0, remaining_seconds - cleanup_reserve),
            'cleanup_reserve_seconds': cleanup_reserve, 'cpu_count': cpu_count}


def once_admission(output, intent):
    output = Path(output)
    need(output.is_absolute() and output.parent.resolve() == output.parent and not output.exists(), 'EXISTING_OUTPUT_REFUSES_REPEAT')
    parent = output.parent.stat()
    need(parent.st_uid == os.getuid() and stat.S_IMODE(parent.st_mode) == 0o700, 'OWNED0700_ONCE_PARENT_REQUIRED')
    need(type(intent) is dict and intent.get('schema') == 'frw.Root.pptx-pdf-export-once-intent.v1'
         and intent.get('state') == 'INTENT_BEFORE_CGROUP_MOVE' and intent.get('consumed') is False
         and intent.get('output') == str(output), 'CONSUMED_OR_UNKNOWN_OPERATION_REFUSES_REPLAY')
    return True


def qualification_gate(state, commands, own_processes_zero, temporary_homes_removed, input_unchanged, comparisons):
    need(type(commands) is list and commands, 'QUALIFICATION_COMMANDS_REQUIRED')
    commands_ok = all(c.get('state') == 'RETURNED_ZERO' and c.get('exit_code') == 0
                      and c.get('process_reaped') is True and c.get('own_processes_zero') is True
                      and c.get('log', {}).get('complete') is True for c in commands)
    comparisons_ok = type(comparisons) is list and bool(comparisons) and all(c.get('status') == 'MATCH' for c in comparisons)
    return bool(state == 'ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED' and commands_ok
                and own_processes_zero is True and temporary_homes_removed is True and input_unchanged is True and comparisons_ok)


def finite_clock(clock, maximum):
    need(type(clock) is dict and set(clock) == {'boot_id', 'origin_monotonic', 'deadline_monotonic'}, 'FINITE_CLOCK_FIELDS')
    need(type(clock['boot_id']) is str and clock['boot_id'], 'CLOCK_BOOT_REQUIRED')
    need(all(type(clock[n]) in (int, float) and not isinstance(clock[n], bool) and math.isfinite(clock[n])
             for n in ('origin_monotonic', 'deadline_monotonic')), 'FINITE_CLOCK_VALUES')
    need(0 < clock['deadline_monotonic'] - clock['origin_monotonic'] <= maximum, 'FINITE_CLOCK_WINDOW')


def path_identity(path):
    """Stable custody tuple used before and after a Root-owned operation."""
    info = Path(path).lstat()
    need(stat.S_ISREG(info.st_mode) and not Path(path).is_symlink() and info.st_nlink == 1, 'SINGLE_LINK_REGULAR_FILE_REQUIRED')
    return {'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid, 'gid': info.st_gid,
            'mode': info.st_mode, 'nlink': info.st_nlink, 'bytes': info.st_size,
            'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}
