#!/usr/bin/env python3
"""B162's 34 finite offline controls; all runtime effects remain NOT_RUN."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import stat
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'code'
CONTRACT = runpy.run_path(str(CODE / 'pptx_pdf_contract.py'))
PAGES = runpy.run_path(str(CODE / 'pdf_pages.py'))
BOUNDARY = runpy.run_path(str(CODE / 'pptx_pdf_boundary.py'))
QUALIFY = runpy.run_path(str(CODE / 'qualify_pptx_pdf.py'))
LAUNCH = runpy.run_path(str(CODE / 'launch_pptx_pdf.py'))
FIXTURE = ROOT / 'fixtures/known-visible-label.pptx'
EXPECTATION_PATH = ROOT / 'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json'
EXPECTED = json.loads(EXPECTATION_PATH.read_text())
PAGE_TEXTS = [
    'Quarterly report\nA01 3601.50 B02 1499.70\nVisible chart labels 2718.25 314.75',
    'Second slide\nLiteral =SUM(A1:A2) remains text',
]
SHA = lambda value: hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()
REF = lambda path, sha=None: {'path': str(path), 'sha256': sha or SHA(str(path))}
WORK = ROOT / 'controls' / 'work'
RESULTS = []


def need(value, message='control assertion failed'):
    if not value:
        raise AssertionError(message)


def reject(fn, contains=None):
    try:
        fn()
    except Exception as exc:
        if contains is not None:
            need(contains in str(exc), f'{contains} not in {exc}')
        return type(exc).__name__
    raise AssertionError('negative control unexpectedly accepted')


def ref_with_bytes(path, data):
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def make_manifest():
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.name in ('MANIFEST.json', 'PACKAGE.json') or WORK in path.parents:
            continue
        if any(part in ('__pycache__', '.pytest_cache') for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        files.append({'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
    manifest = {'schema': 'frw.Kimi.b162.source-manifest.v1', 'root': str(ROOT), 'source_only': True,
                'files': files, 'runtime_source_graph': [row['path'] for row in files if row['path'].startswith(('code/', 'base/', 'vendor/b160/'))]}
    raw = CONTRACT['json_bytes'](manifest)
    (ROOT / 'MANIFEST.json').write_bytes(raw)
    (ROOT / 'MANIFEST.json').chmod(0o600)
    return REF(ROOT / 'MANIFEST.json', hashlib.sha256(raw).hexdigest())


def make_plan(manifest_ref, deadline=None, output=None):
    input_ref = REF(FIXTURE, SHA(FIXTURE.read_bytes()))
    source_names = QUALIFY['SOURCES']
    sources = {name: SHA((CODE / name).read_bytes()) for name in source_names}
    clock = {'boot_id': 'boot-offline', 'origin_monotonic': 100.0, 'deadline_monotonic': 160.0}
    tool = lambda path, version: {'executable': REF(path, SHA(path)), 'version': version}
    return {'schema': 'frw.Root.presentation-pdf-native-qualification-plan.v1', 'operator': 'Root', 'format': 'pptx',
            'operation_id': 'offline-known-1', 'input': {**input_ref, 'bytes': FIXTURE.stat().st_size, 'mime': CONTRACT['PPTX_MIME']},
            'expectation': REF(EXPECTATION_PATH, SHA(EXPECTATION_PATH.read_bytes())), 'sources': sources,
            'source_manifest': manifest_ref, 'current': REF('/offline/current'),
            'toolchain': {'consumer': tool(CONTRACT['ENGINE'], 'LibreOffice 26.2.5.2'),
                          'strace': tool(CONTRACT['STRACE'], 'strace -- version 6.0'),
                          'pdf_reader': {'source': REF(CODE / 'read_extract.py', SHA((CODE / 'read_extract.py').read_bytes())),
                                         'executable': REF(CONTRACT['PDFTOTEXT'], SHA(CONTRACT['PDFTOTEXT'])), 'version': 'pdftotext version 24.0'},
                          'wrapper': REF('/opt/friday-archive/bin/libreoffice', SHA('/opt/friday-archive/bin/libreoffice'))},
            'kernel': {'release': 'offline-kernel', 'boot_id': 'boot-offline'}, 'operation_clock': clock,
            'output': str(output or WORK / 'new-known-output'),
            'deadline_utc': (deadline or datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
            'scope': 'frw-pptx-pdf-qualification-1.scope', 'budgets': dict(QUALIFY['BUDGETS']), 'once_intent': REF('/offline/intent')}


def make_binding(manifest_ref):
    tool = lambda path, version: {'executable': REF(path, SHA(path)), 'version': version}
    return {'schema': 'frw.Root.pptx-pdf-native-consumer-admission.v1', 'operator': 'Root',
            'received_artifact': REF(FIXTURE, SHA(FIXTURE.read_bytes())), 'received_bytes': FIXTURE.stat().st_size,
            'delivered_pdf': REF('/offline/delivered.pdf'), 'delivered_pdf_bytes': 4096,
            'mime_type': CONTRACT['PPTX_MIME'], 'ingress_receipt': REF('/offline/receipt'), 'plan': REF('/offline/plan'),
            'run': REF('/offline/run'), 'origin_assessment': REF('/offline/origin'), 'current': REF('/offline/current'),
            'qualification': REF('/offline/closed'), 'consumer_qualification': REF('/offline/qualifier'),
            'operation_clock': REF('/offline/clock'), 'consumer': tool(CONTRACT['ENGINE'], 'LibreOffice 26.2.5.2'),
            'strace': tool(CONTRACT['STRACE'], 'strace -- version 6.0'),
            'kernel': {'release': 'offline-kernel', 'boot_id': 'boot-offline'},
            'import_settings': copy.deepcopy(BOUNDARY['IMPORT_SETTINGS']), 'invocation_id': 'offline-v02-1',
            'expectation': REF(EXPECTATION_PATH, SHA(EXPECTATION_PATH.read_bytes())),
            'pdf_reader': {'source': REF(CODE / 'read_extract.py', SHA((CODE / 'read_extract.py').read_bytes())),
                           'executable': REF(CONTRACT['PDFTOTEXT'], SHA(CONTRACT['PDFTOTEXT'])), 'version': 'pdftotext version 24.0'},
            'source_manifest': manifest_ref, 'export_filter': CONTRACT['EXPORT_FILTER']}


def producer_values(binding):
    request = 'Create five slides from the admitted workbook, with conclusions and one chart; return PPTX and PDF.'
    scenario = {'peer_id': 900000001, 'tester_id': 900000002, 'steps': [{'input': {
        'kind': 'document', 'filename': 'admitted-workbook.xlsx',
        'path': '/private-bindings/admitted-workbook.xlsx',
        'sha256': 'e9e343c8adb24779378e8d4491d329ece731eb865c134a6fa24b56741ced8f21',
        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'caption': request, 'stat': {'size_bytes': 5660}}}]}
    run = {'id': 'run-v02', 'scenario': scenario, 'step': 0, 'send_state': 'sent', 'send_attempts': 1,
           'repeat_count': 0, 'sent_message_id': 1902, 'scenario_sha256': 'b' * 64,
           'request_metadata': {'body_sha256': 'c' * 64}}
    plan = {'schema': 'friday.tester.continue-closed-unknown.v2', 'operator': 'Root', 'new_run_id': 'run-v02',
            'new_scenario': scenario, 'new_task': {'kind': 'ordinary-document-task', 'request': request,
            'source_reference': None, 'nonce': 'a' * 32, 'output': [
                {'filename': None, 'mime_type': CONTRACT['PPTX_MIME']},
                {'filename': None, 'mime_type': CONTRACT['PDF_MIME']}]}}
    advertised = {'file_id': 'pptx-file', 'mime_type': CONTRACT['PPTX_MIME']}
    companion_advertised = {'file_id': 'pdf-file', 'mime_type': CONTRACT['PDF_MIME']}
    receipt = {'downloaded_artifact': {**binding['received_artifact'], 'bytes': binding['received_bytes']},
               'run_id': 'run-v02', 'step': 0, 'sent_message_id': 1902, 'reply_to_message_id': 1902,
               'scenario_sha256': 'b' * 64, 'request_body_sha256': 'c' * 64, 'authenticated_peer_id': 900000001,
               'tester_id': 900000002, 'private_sender': True, 'received_original_bytes': True,
               'artifact_acceptance': 'RECEIVED_UNGRADED', 'advertised_document': advertised,
               'update_id': 77, 'message_id': 88, 'getFile': {'file_id': 'pptx-file'},
               'source_update': {'path': '/offline/update', 'sha256': 'd' * 64, 'bytes': 1},
               'getUpdates_wire': {'path': '/offline/updates', 'sha256': 'e' * 64, 'bytes': 1},
               'getFile_wire': {'path': '/offline/getfile', 'sha256': 'f' * 64, 'bytes': 1},
               'companion_pdf': {'artifact': {**binding['delivered_pdf'], 'bytes': binding['delivered_pdf_bytes']},
                                 'run_id': 'run-v02', 'step': 0, 'reply_to_message_id': 1902,
                                 'received_original_bytes': True, 'artifact_acceptance': 'RECEIVED_UNGRADED',
                                 'advertised_document': companion_advertised, 'getFile': {'file_id': 'pdf-file'},
                                 'getFile_wire': {'path': '/offline/pdf-getfile', 'sha256': '0' * 64, 'bytes': 1}}}
    update = {'update_id': 77, 'message': {'message_id': 88, 'chat': {'type': 'private', 'id': 900000001},
              'from': {'id': 900000001}, 'reply_to_message': {'message_id': 1902}, 'document': advertised}}
    wires = {'/offline/update': update, '/offline/updates': {'ok': True, 'result': [update]},
             '/offline/getfile': {'ok': True, 'result': {'file_id': 'pptx-file'}},
             '/offline/pdf-getfile': {'ok': True, 'result': {'file_id': 'pdf-file'}}}
    return plan, run, receipt, wires


def origin_values(binding, receipt):
    native_ref = REF('/offline/native')
    receiver_ref = REF('/offline/receiver')
    origin = {'schema': 'frw.Root.pptx-pdf-same-created-v02-custody.v1', 'operator': 'Root', 'case': 'V-02',
              'received_artifact': binding['received_artifact'], 'received_bytes': binding['received_bytes'],
              'delivered_pdf': binding['delivered_pdf'], 'delivered_pdf_bytes': binding['delivered_pdf_bytes'],
              'mime_type': binding['mime_type'], 'ingress_receipt': binding['ingress_receipt'], 'run_id': 'run-v02',
              'sent_message_id': 1902, 'root_wire_origin_review': 'EXACT_PEER_REPLY_DOWNLOAD_AND_SAVED_NATIVE_HASH_JOIN',
              'receiver_reconciliation': receiver_ref, 'native_origin': native_ref, 'same_created_presentation': True,
              'editable_preservation': 'FAIL_RETAINED', 'whole_case_acceptance': False}
    receiver = {'status': 'RECEIVED_UNGRADED', 'run_id': 'run-v02', 'sent_message_id': 1902,
                'semantic_acceptance': False, 'canonical_unchanged': True, 'files': [receipt],
                'saved_origin': native_ref}
    native = {'local_artifacts': [
        {'ref': {**binding['received_artifact'], 'bytes': binding['received_bytes']},
         'origin': {'assistant_media_reference': True, 'bytes_match_write_response': True, 'write_tool_verified': True}},
        {'ref': {**binding['delivered_pdf'], 'bytes': binding['delivered_pdf_bytes']},
         'origin': {'assistant_media_reference': True, 'bytes_match_write_response': True, 'write_tool_verified': True}}]}
    return origin, receiver, native


def control(number, name, fn):
    try:
        detail = fn()
        RESULTS.append({'id': number, 'name': name, 'status': 'PASS', 'detail': detail or 'real offline consumer check'})
        print(f'{number:02d} PASS {name}')
    except Exception as exc:
        RESULTS.append({'id': number, 'name': name, 'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}'})
        print(f'{number:02d} FAIL {name}: {type(exc).__name__}: {exc}')


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True, mode=0o700)
    manifest_ref = make_manifest()
    binding = make_binding(manifest_ref)
    plan, run, receipt, wires = producer_values(binding)
    origin, receiver, native = origin_values(binding, receipt)
    original_data = FIXTURE.read_bytes()
    admitted = None

    control(1, 'ordered pages and independent chart/table positive', lambda: need(
        CONTRACT['compare_pdf_pages'](PAGE_TEXTS, EXPECTED)['status'] == 'MATCH'))
    control(2, 'blank PDF text fails despite nonzero bytes', lambda: need(
        CONTRACT['compare_pdf_pages'](['', ''], EXPECTED)['status'] == 'DIFFERENT'))
    control(3, 'wrong page count fails', lambda: reject(lambda: CONTRACT['compare_pdf_pages'](PAGE_TEXTS[:1], EXPECTED), 'PAGE_COUNT'))
    control(4, 'swapped equal-total page content fails', lambda: need(
        CONTRACT['compare_pdf_pages'](list(reversed(PAGE_TEXTS)), EXPECTED)['status'] == 'DIFFERENT'))
    control(5, 'ordinary required token omission fails', lambda: need(
        CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('Quarterly report', ''), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT'))
    control(6, 'chart-only numeric label omission fails with table retained', lambda: need(
        CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('2718.25', ''), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT'))
    control(7, 'table-only numeric cell omission fails with chart retained', lambda: need(
        CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('3601.50', ''), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT'))
    def chart_numeric_boundary():
        need(CONTRACT['contains_token']('1499.70x', '1499.7') is False)
        need(CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('2718.25', '-2718.25'), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT')
        need(CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('314.75', '314.750'), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT')
    control(8, 'chart numeric sign/decimal and substring collision fail', chart_numeric_boundary)
    control(9, 'table numeric sign/decimal fails under declared normalization', lambda: need(
        CONTRACT['compare_pdf_pages']([PAGE_TEXTS[0].replace('3601.50', '+3601.50'), PAGE_TEXTS[1]], EXPECTED)['status'] == 'DIFFERENT'))
    def duplicate_values():
        bad = copy.deepcopy(EXPECTED)
        bad['pages'][0]['chart_numeric_labels'][0] = bad['pages'][0]['table_numeric_cells'][0]
        reject(lambda: CONTRACT['validate_expectation'](bad), 'DUPLICATE_TABLE_CHART')
    control(10, 'duplicate table/chart values cannot prove chart evidence', duplicate_values)

    def sha_before_helper():
        called = []
        with patch.dict(CONTRACT['admit_original'].__globals__, {'observe_pptx': lambda data: called.append(data) or {}}):
            reject(lambda: CONTRACT['admit_original'](FIXTURE, '0' * 64, len(original_data), CONTRACT['PPTX_MIME']), 'SHA_MISMATCH')
        need(called == [])
    control(11, 'original SHA mismatch rejects before helper', sha_before_helper)
    control(12, 'original byte length or MIME mismatch rejects', lambda: (
        reject(lambda: CONTRACT['admit_original'](FIXTURE, SHA(original_data), len(original_data) + 1, CONTRACT['PPTX_MIME']), 'BYTE_LENGTH'),
        reject(lambda: CONTRACT['admit_original'](FIXTURE, SHA(original_data), len(original_data), CONTRACT['PDF_MIME']), 'MIME_MISMATCH')))
    def custody_replacement():
        nonlocal admitted
        admitted = CONTRACT['admit_original'](FIXTURE, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME'])
        copied = WORK / 'custody.pptx'
        shutil.copyfile(FIXTURE, copied)
        copied.chmod(0o600)
        local = CONTRACT['admit_original'](copied, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME'])
        copied.unlink()
        shutil.copyfile(FIXTURE, copied)
        copied.chmod(0o600)
        reject(lambda: CONTRACT['custody_unchanged'](copied, local), 'IDENTITY_REPLACED')
    control(13, 'original identity/path replacement fails custody', custody_replacement)
    def link_substitution():
        link = WORK / 'link.pptx'
        link.symlink_to(FIXTURE)
        reject(lambda: CONTRACT['admit_original'](link, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME']))
        hard = WORK / 'hard.pptx'
        os.link(FIXTURE, hard)
        reject(lambda: CONTRACT['admit_original'](hard, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME']))
        hard.unlink()
    control(14, 'symlink and multi-link substitution reject', link_substitution)
    def unsafe_path():
        relative = Path(str(FIXTURE) + '/../known-visible-label.pptx')
        reject(lambda: CONTRACT['admit_original'](relative, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME']), 'NONCANONICAL')
        writable = WORK / 'writable.pptx'
        shutil.copyfile(FIXTURE, writable)
        writable.chmod(0o666)
        reject(lambda: CONTRACT['admit_original'](writable, SHA(original_data), len(original_data), CONTRACT['PPTX_MIME']), 'WRITABLE')
    control(15, 'noncanonical or writable input path rejects without chmod-to-pass', unsafe_path)
    def mutated_package(kind):
        path = WORK / (kind + '.pptx')
        with zipfile.ZipFile(FIXTURE) as zin, zipfile.ZipFile(path, 'w') as zout:
            for info in zin.infolist():
                raw = zin.read(info.filename)
                if kind == 'external' and info.filename == 'ppt/slides/_rels/slide1.xml.rels':
                    raw = raw.replace(b'TargetMode="Internal"', b'TargetMode="External"')
                    raw = raw.replace(b'<Relationship ', b'<Relationship TargetMode="External" ', 1)
                if kind == 'macro' and info.filename == 'ppt/slides/slide1.xml':
                    raw = raw.replace(b'</p:sld>', b'</p:sld>')
                if kind == 'malformed' and info.filename == 'ppt/slides/slide1.xml':
                    raw = b'<not-xml'
                zout.writestr(info, raw)
            if kind == 'macro':
                zout.writestr('ppt/activeX/activeX1.bin', b'inert')
        return path
    control(16, 'external relationship rejects before helper', lambda: reject(
        lambda: CONTRACT['admit_original'](mutated_package('external'), SHA(mutated_package('external').read_bytes()), mutated_package('external').stat().st_size, CONTRACT['PPTX_MIME'])))
    control(17, 'macro/OLE/executable package content rejects before helper', lambda: reject(
        lambda: CONTRACT['admit_original'](mutated_package('macro'), SHA(mutated_package('macro').read_bytes()), mutated_package('macro').stat().st_size, CONTRACT['PPTX_MIME'])))
    control(18, 'malformed XML or unsafe ZIP package rejects', lambda: reject(
        lambda: CONTRACT['observe_pptx'](mutated_package('malformed').read_bytes())))
    def fixed_filter():
        argv = CONTRACT['fixed_engine_argv']('/opt/friday-archive/bin/libreoffice', '/tmp/profile', '/tmp/out', '/mnt/input/received.pptx')
        need(argv[argv.index('--convert-to') + 1] == 'pdf:impress_pdf_Export')
        need('--infilter' not in argv and ';' not in argv)
        reject(lambda: CONTRACT['fixed_engine_argv']('/bin/sh', '/tmp/profile', '/tmp/out', '/mnt/input/received.pptx'))
    control(19, 'only fixed PDF filter and argv are admitted', fixed_filter)
    control(20, 'reader/source/tool pin mismatch rejects', lambda: (
        reject(lambda: PAGES['load_reader'](expected_sha256='0' * 64), 'PIN_MISMATCH'),
        reject(lambda: PAGES['authenticate_tool'](None, '/bin/false'), 'FIXED_PDFTOTEXT')))
    def version_kernel_schema():
        qualifier = {'schema': 'frw.Root.pptx-pdf-native-consumer-qualification.v1', 'operator': 'Root', 'format': 'pptx',
                     'export_filter': CONTRACT['EXPORT_FILTER'], 'consumer': binding['consumer'], 'strace': binding['strace'],
                     'kernel': binding['kernel'], 'import_settings': binding['import_settings'], 'pdf_reader': binding['pdf_reader'],
                     'source_manifest': binding['source_manifest'], 'actual_observation': REF('/offline/observation'),
                     'full_format_acceptance': False, 'editable_preservation': 'FAIL_RETAINED'}
        BOUNDARY['qualification_identity'](binding, qualifier)
        for path in ('schema', 'consumer', 'kernel'):
            bad = copy.deepcopy(qualifier)
            if path == 'schema':
                bad['schema'] = 'wrong'
            elif path == 'consumer':
                bad['consumer'] = dict(bad['consumer'], version='wrong')
            else:
                bad['kernel'] = dict(bad['kernel'], boot_id='different')
            reject(lambda: BOUNDARY['qualification_identity'](binding, bad), 'QUALIFICATION_JOIN')
    control(21, 'schema/producer/consumer version/kernel/boot mismatch rejects', version_kernel_schema)
    def failed_closed_receipt():
        commands = [{'state': 'RETURNED_ZERO', 'exit_code': 0, 'process_reaped': True, 'own_processes_zero': True, 'log': {'complete': True}}]
        need(CONTRACT['qualification_gate']('ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED', commands, True, True, True, [{'status': 'MATCH'}]) is True)
        need(CONTRACT['qualification_gate']('FAILED_RESERVE_OR_FABRICATED_CLOSED', commands, True, True, True, [{'status': 'MATCH'}]) is False)
    control(22, 'failed resave or fabricated closed receipt cannot qualify', failed_closed_receipt)
    def observation_refs():
        reader = {'source': REF(CODE / 'read_extract.py', SHA((CODE / 'read_extract.py').read_bytes())),
                  'helper': {'path': CONTRACT['PDFTOTEXT'], 'sha256': 'a' * 64, 'version': 'offline'}, 'ocr_or_hosted_fallback': False}
        data = b'%PDF-offline-observation-only'
        observed = CONTRACT['pdf_observation'](data, PAGE_TEXTS, EXPECTED, reader, '/offline/exported.pdf')
        CONTRACT['validate_pdf_observation'](observed, data, EXPECTED)
        bad = copy.deepcopy(observed)
        bad['artifact']['sha256'] = '0' * 64
        reject(lambda: CONTRACT['validate_pdf_observation'](bad, data, EXPECTED), 'ARTIFACT_JOIN')
        reject(lambda: CONTRACT['validate_pdf_observation'](observed, b'%PDF-sibling', EXPECTED), 'ARTIFACT_JOIN')
    control(23, 'closed observation/PDF/known-input refs join and reject siblings', observation_refs)
    def current_join():
        tuple_ref, writer_ref = REF('/offline/tuple'), REF('/offline/writer')
        installed = {'schema': 'frw.Root.ordinary-current116-bindings.v1', 'actual_tuple': tuple_ref,
                     'installed_source': REF('/offline/installed-leaf'), 'sole_writer': writer_ref,
                     'fresh_native_proof': REF('/offline/native-proof'), 'permanent_services': REF('/offline/services')}
        current = {'schema': 'frw.Root.same-received-consumer-current.v1', 'operator': 'Root',
                   'actual_qualification': binding['qualification'], 'whole_case_acceptance': False, 'original_effect_closed': True,
                   'installed_source': REF('/offline/installed'), 'diagnostic_source': REF('/offline/diagnostic'),
                   'local_resource_decision': REF('/offline/resources')}
        diagnostic = {'source_only_accepted': True, 'source_directory': str(CODE), 'source_manifest': manifest_ref}
        resources = {'read_only': True, 'new_baseline_pause': False, 'decision': 'ALLOW offline', 'local_affinity': [0, 1]}
        records = {'/offline/installed': installed, '/offline/diagnostic': diagnostic, '/offline/resources': resources,
                   '/offline/tuple': {'schema': 'frw.Root.actual-installed-tuple.v1', 'tuple': {'service_owner': 'Root', 'source': 116, 'project': 116}},
                   '/offline/writer': {'schema': 'frw.Root.s07-sole-writer-authority.v1', 'operator': 'Root'},
                   str(ROOT / 'MANIFEST.json'): json.loads((ROOT / 'MANIFEST.json').read_text())}
        fake_json = lambda ref, cap=2 * 1024 * 1024: copy.deepcopy(records[ref['path']])
        with patch.dict(BOUNDARY['_check_current'].__globals__, {'_json_ref': fake_json, 'read_ref': lambda *args, **kwargs: b'{}'}):
            BOUNDARY['_check_current'](binding, {'current': current})
            records['/offline/resources']['read_only'] = False
            reject(lambda: BOUNDARY['_check_current'](binding, {'current': current}), 'RESOURCE')
    control(24, 'current source/sole-writer/resource decision mismatch rejects', current_join)
    def pptx_producer_mismatch():
        values = {'plan': plan, 'run': run, 'ingress_receipt': receipt}
        with patch.dict(BOUNDARY['_check_plan_run_receipt'].__globals__, {'_wire': lambda ref: wires[ref['path']]}):
            BOUNDARY['_check_plan_run_receipt'](binding, values)
            bad = copy.deepcopy(receipt)
            bad['downloaded_artifact']['sha256'] = '0' * 64
            reject(lambda: BOUNDARY['_check_plan_run_receipt'](binding, {'plan': plan, 'run': run, 'ingress_receipt': bad}), 'PPTX_JOIN')
    control(25, 'actual V02 original PPTX mismatch rejects; no V01 substitution', pptx_producer_mismatch)
    def pdf_producer_mismatch():
        bad = copy.deepcopy(receipt)
        bad['companion_pdf']['artifact']['sha256'] = '0' * 64
        with patch.dict(BOUNDARY['_check_plan_run_receipt'].__globals__, {'_wire': lambda ref: wires[ref['path']]}):
            reject(lambda: BOUNDARY['_check_plan_run_receipt'](binding, {'plan': plan, 'run': run, 'ingress_receipt': bad}), 'COMPANION_PDF')
    control(26, 'companion PDF mismatch vs same reply/run rejects', pdf_producer_mismatch)
    def unavailable_page_view():
        inert = WORK / 'reader-input.bin'
        inert.write_bytes(b'inert reader input; not an output artifact')
        inert.chmod(0o600)
        fake = {'PDF_PAGE_SCAN_TIMEOUT': 20.0, '_pdf_page_texts': lambda path: None,
                '_pdf_scoped_page_view': lambda data, text: text}
        reject(lambda: PAGES['read_pages'](b'%PDF-inert', inert, reader=fake, tool={'path': 'inert'}), 'PAGE_VIEW_UNAVAILABLE')
        fake['_pdf_page_texts'] = lambda path: ['', '']
        reject(lambda: PAGES['read_pages'](b'%PDF-inert', inert, reader=fake, tool={'path': 'inert'}), 'BLANK_PDF_TEXT')
        commands = [{'state': 'RETURNED_ZERO', 'exit_code': 0, 'process_reaped': True, 'own_processes_zero': True, 'log': {'complete': False}}]
        need(CONTRACT['qualification_gate']('ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED', commands, True, True, True, [{'status': 'MATCH'}]) is False)
    control(27, 'missing page view, blank output, decode loss or truncated log fails', unavailable_page_view)
    control(28, 'PDF delimiter collision cannot qualify page semantics', lambda: reject(
        lambda: CONTRACT['compare_pdf_pages'](['[page 1]\n' + PAGE_TEXTS[0], PAGE_TEXTS[1]], EXPECTED), 'DELIMITER_COLLISION'))
    expired_plan = make_plan(manifest_ref, deadline=datetime.now(timezone.utc) - timedelta(seconds=1))
    control(29, 'expired wall or operation clock rejects before intent/helper', lambda: (
        reject(lambda: QUALIFY['validate_plan'](expired_plan), 'DEADLINE'),
        reject(lambda: CONTRACT['resource_admission'](0, 1), 'CLEANUP_RESERVE')))
    control(30, 'insufficient reserve/CPU and reader timeout remain bounded', lambda: (
        reject(lambda: CONTRACT['resource_admission'](30, 0), 'CPU'),
        need(CONTRACT['resource_admission'](30, 1)['reader_timeout_seconds'] == 18)))
    def helper_failure():
        base = {'state': 'RETURNED_ZERO', 'exit_code': 0, 'process_reaped': True, 'own_processes_zero': True, 'log': {'complete': True}}
        for mutation in ({'state': 'TIMEOUT'}, {'exit_code': 1}, {'process_reaped': False}):
            command = {**base, **mutation}
            need(CONTRACT['qualification_gate']('ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED', [command], True, True, True, [{'status': 'MATCH'}]) is False)
    control(31, 'helper timeout/nonzero exit retains failure and emits no qualification', helper_failure)
    control(32, 'cleanup failure or unreaped own process rejects without global kill', lambda: (
        need(CONTRACT['qualification_gate']('ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED',
             [{'state': 'RETURNED_ZERO', 'exit_code': 0, 'process_reaped': True, 'own_processes_zero': True, 'log': {'complete': True}}],
             False, True, True, [{'status': 'MATCH'}]) is False),
        need(CONTRACT['qualification_gate']('ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED',
             [{'state': 'RETURNED_ZERO', 'exit_code': 0, 'process_reaped': True, 'own_processes_zero': True, 'log': {'complete': True}}],
             True, False, True, [{'status': 'MATCH'}]) is False)))
    def once():
        output = WORK / 'once-output'
        intent = {'schema': 'frw.Root.pptx-pdf-export-once-intent.v1', 'state': 'INTENT_BEFORE_CGROUP_MOVE',
                  'consumed': False, 'output': str(output)}
        need(CONTRACT['once_admission'](output, intent) is True)
        output.mkdir()
        reject(lambda: CONTRACT['once_admission'](output, intent), 'EXISTING_OUTPUT')
        output.rmdir()
        intent['consumed'] = True
        reject(lambda: CONTRACT['once_admission'](output, intent), 'CONSUMED')
        intent['consumed'] = False
        intent['state'] = 'UNKNOWN'
        reject(lambda: CONTRACT['once_admission'](output, intent), 'UNKNOWN')
    control(33, 'existing intent/output/consumed or UNKNOWN operation refuses replay', once)
    def end_to_end():
        # Real emitted plan/admission/observation schemas and their nearest consumers.
        QUALIFY['validate_plan'](make_plan(manifest_ref))
        BOUNDARY['validate'](binding)
        host_plan = {'schema': 'frw.Root.pptx-pdf-fixed-host-launch-plan.v1', 'operator': 'Root',
                     'sources': {name: SHA((CODE / name).read_bytes()) for name in LAUNCH['SOURCES']},
                     'source_manifest': manifest_ref, 'binding': REF('/offline/binding'),
                     'output': str(WORK / 'new-host-output'),
                     'deadline_utc': (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()}
        LAUNCH['validate_plan'](host_plan)
        reader = {'source': REF(CODE / 'read_extract.py', SHA((CODE / 'read_extract.py').read_bytes())),
                  'helper': {'path': CONTRACT['PDFTOTEXT'], 'sha256': 'a' * 64, 'version': 'offline'}, 'ocr_or_hosted_fallback': False}
        data = b'%PDF-offline-only-not-an-export'
        observed = CONTRACT['pdf_observation'](data, PAGE_TEXTS, EXPECTED, reader, '/offline/exported.pdf')
        CONTRACT['validate_pdf_observation'](observed, data, EXPECTED)
        inert = WORK / 'reader-input.bin'
        if not inert.exists():
            inert.write_bytes(b'inert reader input; no document output')
            inert.chmod(0o600)
        reader_module = PAGES['load_reader']()
        reader_globals = reader_module['_pdf_page_texts'].__globals__
        class InertProcess:
            returncode = 0
            stdout = ('\f'.join(PAGE_TEXTS) + '\f').encode('utf-8')
        with patch.object(reader_globals['shutil'], 'which', return_value=CONTRACT['PDFTOTEXT']), \
             patch.object(reader_globals['subprocess'], 'run', return_value=InertProcess()):
            page_read = PAGES['read_pages'](b'%PDF-inert-reader-control', inert,
                                            reader=reader_module, tool={'path': 'inert-offline-double'})
        need(page_read['pages'] == PAGE_TEXTS)
        need(CONTRACT['compare_pdf_pages'](page_read['pages'], EXPECTED)['status'] == 'MATCH')
        with patch.dict(BOUNDARY['_check_plan_run_receipt'].__globals__, {'_wire': lambda ref: wires[ref['path']]}):
            BOUNDARY['_check_plan_run_receipt'](binding, {'plan': plan, 'run': run, 'ingress_receipt': receipt})
        with patch.dict(BOUNDARY['_check_origin'].__globals__, {'_json_ref': lambda ref, cap=2 * 1024 * 1024: {'/offline/origin': origin, '/offline/receiver': receiver, '/offline/native': native}[ref['path']]}):
            BOUNDARY['_check_origin'](binding, {'origin_assessment': origin, 'run': run, 'ingress_receipt': receipt})
        for mutate in (
            lambda p: p['sources'].pop('pdf_pages.py'),
            lambda p: p['budgets'].__setitem__('wall_seconds', 120),
            lambda p: p['input'].__setitem__('bytes', p['input']['bytes'] + 1),
            lambda p: p['operation_clock'].__setitem__('deadline_monotonic', p['operation_clock']['origin_monotonic']),
        ):
            bad = make_plan(manifest_ref)
            mutate(bad)
            reject(lambda: QUALIFY['validate_plan'](bad))
        bad_host = copy.deepcopy(host_plan)
        bad_host['sources']['pptx_pdf_host.py'] = '0' * 64
        # The plan shape admits the pin; the actual launcher manifest/hash check rejects it.
        LAUNCH['validate_plan'](bad_host)
        need(SHA((CODE / 'pptx_pdf_host.py').read_bytes()) != bad_host['sources']['pptx_pdf_host.py'])
        return 'known plan + host plan + producer/custody + emitted PDF observation joins; nested source/path/budget mutations rejected'
    control(34, 'end-to-end offline producer-consumer joins and nested mutations', end_to_end)

    passed = sum(row['status'] == 'PASS' for row in RESULTS)
    result = {'schema': 'frw.Kimi.b162.offline-controls-result.v1', 'assignment': 'KIMI-B162-PPTX-PDF-EXPORT-QUALIFICATION-CONSUMER',
              'total': len(RESULTS), 'passed': passed, 'failed': len(RESULTS) - passed,
              'actual_effects': [], 'actual_Office': 'NOT_RUN', 'actual_export': 'NOT_RUN', 'actual_qualification': 'NOT_RUN',
              'future_actual_refs': 'UNBOUND', 'editable_preservation': 'FAIL_RETAINED', 'full_format_acceptance': False,
              'controls': RESULTS}
    (ROOT / 'controls/OFFLINE-RESULT.json').write_bytes(CONTRACT['json_bytes'](result))
    print(json.dumps({'total': len(RESULTS), 'passed': passed, 'failed': len(RESULTS) - passed}))
    return 0 if len(RESULTS) == 34 and passed == 34 else 1


if __name__ == '__main__':
    raise SystemExit(main())
