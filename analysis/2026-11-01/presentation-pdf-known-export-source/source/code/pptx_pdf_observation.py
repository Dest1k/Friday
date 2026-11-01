"""Authenticate retained PPTX/PDF runtime observations; never grants user acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import stat
import time

HERE = Path(__file__).resolve().parent
BOUNDARY = runpy.run_path(str(HERE / 'pptx_pdf_boundary.py'))
CONTRACT = runpy.run_path(str(HERE / 'pptx_pdf_contract.py'))
PAGES = runpy.run_path(str(HERE / 'pdf_pages.py'))
TRACE = runpy.run_path(str(HERE.parent / 'base' / 's16_observation_v2.py'))
read_ref, need, correlate, trace_facts = BOUNDARY['read_ref'], BOUNDARY['need'], BOUNDARY['correlate'], TRACE['trace_facts']
FILTER = TRACE['FILTER']
FIXED_EXPORT_EXECUTABLES = {
    '/opt/friday-archive/python', '/usr/bin/dirname', '/usr/bin/grep', '/usr/bin/uname',
    *['/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/' + name
      for name in ('soffice', 'oosplash', 'soffice.bin', 'javaldx')]}
COMPLETE = 'PPTX_PDF_EXPORT_RAW_RUNTIME_OBSERVATIONS_REVIEW_REQUIRED'


def _json_ref(ref, cap=2 * 1024 * 1024):
    need(type(ref) is dict and set(ref) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}), 'EXACT_OBSERVATION_REF_REQUIRED')
    raw = read_ref({k: ref[k] for k in ('path', 'sha256')}, cap, private=True)
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'OBSERVATION_BYTE_JOIN')
    return json.loads(raw)


def _check_pdf(ref, data, expected, binding, end, page_reader):
    observed = _json_ref(ref)
    CONTRACT['artifact'](observed.get('artifact'))
    need(observed['artifact']['sha256'] == hashlib.sha256(data).hexdigest()
         and observed['artifact']['bytes'] == len(data), 'PDF_ARTIFACT_OBSERVATION_JOIN')
    CONTRACT['validate_pdf_observation'](observed, data, expected)
    if page_reader is None:
        tool = PAGES['authenticate_tool'](None, CONTRACT['PDFTOTEXT'],
                                           binding['pdf_reader']['executable']['sha256'], binding['pdf_reader']['version'])
        read = PAGES['read_pages'](data, Path(observed['artifact']['path']), deadline_monotonic=end, tool=tool)
    else:
        read = page_reader(data, Path(observed['artifact']['path']), end, binding)
    need(observed['pages'] == read['pages'], 'PDF_PAGE_TEXT_RECOMPUTE_MISMATCH')
    need(observed['comparison'] == CONTRACT['compare_pdf_pages'](read['pages'], expected), 'PDF_COMPARISON_RECOMPUTE_MISMATCH')
    need(observed['reader']['source']['sha256'] == binding['pdf_reader']['source']['sha256']
         and observed['reader']['helper']['sha256'] == binding['pdf_reader']['executable']['sha256']
         and observed['reader']['helper']['version'] == binding['pdf_reader']['version']
         and observed['reader'].get('ocr_or_hosted_fallback') is False, 'PDF_READER_PIN_JOIN_REQUIRED')
    return observed


def authenticate(binding_ref, host_ref, root_review_ref, page_reader=None):
    read_end = time.monotonic() + 45
    binding = json.loads(read_ref(binding_ref, 65536, private=True))
    joined = correlate(binding)
    clock = joined['operation_clock']
    host = json.loads(read_ref(host_ref, 65536, private=True))
    review = json.loads(read_ref(root_review_ref, 65536, private=True))
    expected = json.loads(read_ref(binding['expectation'], 1_000_000, private=True))
    need(host.get('schema') == 'frw.Root.pptx-pdf-export-existing-boundary-host-report.v1'
         and host.get('state') == COMPLETE and host.get('own_processes_zero') is True
         and host.get('original_received_preserved') is True and host.get('delivered_pdf_preserved') is True,
         'ACTUAL_PDF_HOST_ISOLATION_REAP_CUSTODY_NOT_ESTABLISHED')
    need(host.get('worker_exit_code') == 0, 'ACTUAL_PDF_WORKER_EXIT_REQUIRED')
    artifact_root = Path(host_ref['path']).parent
    need(Path(host_ref['path']).name == 'HOST-OBSERVER-RESULT.json', 'EXACT_PDF_HOST_REPORT_REQUIRED')
    original = read_ref(binding['received_artifact'], 1_000_000, private=True)
    delivered = read_ref(binding['delivered_pdf'], 8_000_000, private=True)
    need(len(original) == binding['received_bytes'] and len(delivered) == binding['delivered_pdf_bytes'], 'EXACT_ORIGINAL_PAIR_BYTES_REQUIRED')
    worker = host.get('worker_report', {})
    phases = worker.get('phases', [])
    need(worker.get('state') == COMPLETE and worker.get('schema') == 'frw.Root.pptx-pdf-finite-native-consumer-draft.v1'
         and worker.get('binding_sha256') == binding_ref['sha256'] and worker.get('invocation_id') == binding['invocation_id']
         and worker.get('received_sha256') == binding['received_artifact']['sha256']
         and worker.get('delivered_pdf_sha256') == binding['delivered_pdf']['sha256']
         and worker.get('received_snapshot_unchanged') is True and worker.get('delivered_snapshot_unchanged') is True
         and worker.get('process_reaped') is True and worker.get('format') == 'pptx'
         and len(phases) == 1 and phases[0].get('stage') == 'export', 'ACTUAL_ONE_PHASE_PDF_CORRELATION_REQUIRED')
    need(type(review) is dict and set(review) == {'schema', 'operator', 'binding', 'host_report', 'invocation_id', 'trace_filter', 'phase_reviews'}
         and review['schema'] == 'frw.Root.pptx-pdf-actual-invocation-review.v1' and review['operator'] == 'Root'
         and review['binding'] == binding_ref and review['host_report'] == host_ref
         and review['invocation_id'] == binding['invocation_id'] and review['trace_filter'] == FILTER
         and type(review['phase_reviews']) is list and len(review['phase_reviews']) == 1,
         'EXACT_ROOT_PDF_INVOCATION_REVIEW_REQUIRED')
    phase = phases[0]
    phase_review = review['phase_reviews'][0]
    need(phase.get('trace_filter') == FILTER and phase.get('trace_complete') is True and phase.get('exit_code') == 0
         and phase.get('process_reaped') is True and phase.get('input_unchanged') is True
         and phase.get('timed_out') is False and phase.get('overflow') is False, 'COMPLETE_ACTUAL_PDF_PHASE_REQUIRED')
    need(all(type(phase.get(n)) in (int, float) and math.isfinite(phase[n])
             for n in ('started_monotonic', 'ended_monotonic', 'deadline_monotonic'))
         and phase['started_monotonic'] <= phase['ended_monotonic'] <= phase['deadline_monotonic']
         and phase['ended_monotonic'] - phase['started_monotonic'] <= 35, 'ACTUAL_MEASURED_PDF_WINDOW_REQUIRED')
    need(clock['origin_monotonic'] <= phase['started_monotonic'] and phase['deadline_monotonic'] <= clock['deadline_monotonic'],
         'SEPARATE_FINITE_PDF_CLOCK_LINEAGE_REQUIRED')
    output = phase['output_artifact']
    CONTRACT['artifact'](output)
    need(output['path'] == str(artifact_root / 'received-exported.pdf'), 'EXACT_EXPORTED_PDF_ARTIFACT_REQUIRED')
    data = read_ref({k: output[k] for k in ('path', 'sha256')}, 8_000_000, private=True)
    need(len(data) == output['bytes'] and phase['input_sha256'] == binding['received_artifact']['sha256']
         and phase['input_path'] == '/mnt/input/received.pptx', 'ORIGINAL_PPTX_EXPORT_LINEAGE_JOIN')
    need(phase['trace_reference']['path'] == str(artifact_root / 'EXPORT-SYSCALLS-PRIVATE.log')
         and phase['log_reference']['path'] == str(artifact_root / 'EXPORT-CONSUMER-PRIVATE.log'), 'EXACT_PDF_TRACE_AND_LOG_REQUIRED')
    trace = read_ref(phase['trace_reference'], 4 * 1024 * 1024, private=True)
    need(len(trace) == phase['trace_bytes'], 'COMPLETE_PDF_TRACE_LENGTH_REQUIRED')
    log = read_ref(phase['log_reference'], 65536, private=True)
    need(b'strace:' not in log, 'TRACER_DIAGNOSTIC_REQUIRES_REVIEW')
    facts = trace_facts(trace, phase['input_path'], phase['output_path'])
    if any(record['path'] not in FIXED_EXPORT_EXECUTABLES for record in facts['exec_records']):
        return {'status': 'FAIL', 'reason': 'UNEXPECTED_EXEC_GRAPH', 'consumer_safety': 'FAIL',
                'full_format_acceptance': False, 'editable_preservation': 'FAIL_RETAINED'}
    if facts['unexpected_network_family']:
        return {'status': 'FAIL', 'reason': 'NETWORK_FAMILY_INITIATION_OBSERVED', 'consumer_safety': 'FAIL',
                'full_format_acceptance': False, 'editable_preservation': 'FAIL_RETAINED'}
    need(type(phase_review) is dict and set(phase_review) == {'stage', 'trace_reference', 'exec_records', 'network_records', 'decision'}
         and phase_review['stage'] == phase['stage'] and phase_review['trace_reference'] == phase['trace_reference']
         and phase_review['exec_records'] == facts['exec_records'] and phase_review['network_records'] == facts['network_records']
         and phase_review['decision'] == 'FIXED_PPTX_PDF_EXPORT_GRAPH_NO_NETWORK_OR_COMMAND_INITIATION',
         'ROOT_REVIEW_MUST_AUTHENTICATE_EXACT_PDF_GRAPH')
    original_observed = _json_ref(phase['input_observation'])
    need(original_observed == CONTRACT['observe_pptx'](original), 'PPTX_STRUCTURAL_OBSERVATION_MUST_MATCH_ORIGINAL')
    exported = _check_pdf(phase['output_observation'], data, expected, binding, read_end, page_reader)
    delivered_observed = _check_pdf(worker['delivered_observation'], delivered, expected, binding, read_end, page_reader)
    need(exported['artifact'] == output
         and delivered_observed['artifact'] == {**binding['delivered_pdf'], 'bytes': binding['delivered_pdf_bytes']},
         'EXACT_PDF_OBSERVATION_ARTIFACT_PATH_JOIN')
    need(phase['output_comparison'] == exported['comparison'] and worker['delivered_comparison'] == delivered_observed['comparison'],
         'PDF_COMPARISON_RECORD_JOIN_REQUIRED')
    comparisons = [{'role': 'exported', **exported['comparison']}, {'role': 'delivered', **delivered_observed['comparison']}]
    return {'schema': 'frw.Root.pptx-pdf-native-consumer-diagnostic.v1',
            'status': 'REAL_CONSUMER_OBSERVATIONS_AUTHENTICATED_ROOT_REVIEW_REQUIRED', 'operator': 'Root',
            'invocation_id': binding['invocation_id'], 'binding': binding_ref, 'host_report': host_ref,
            'actual_invocation_review': root_review_ref,
            'runtime_observations': [{'stage': 'export', 'trace_reference': phase['trace_reference'],
                                      'lineage_anchors': {'input_read_open': True, 'output_write': True},
                                      'internal_phase_timestamps': 'NOT_OBSERVED'}],
            'structural_comparisons': comparisons,
            'bounded_projection_status': 'MATCH' if all(c['status'] == 'MATCH' for c in comparisons) else 'DIFFERENT',
            'consumer_safety': 'ROOT_SEPARATE_ACCEPTANCE_REQUIRED', 'product_acceptance': 'NOT_AUTOMATICALLY_GRANTED',
            'render_visual_user_semantics': 'NOT_OBSERVED', 'editable_preservation': 'FAIL_RETAINED',
            'full_format_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('binding', 'host-report', 'root-review'):
        parser.add_argument('--' + name, required=True)
        parser.add_argument('--' + name + '-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    output = Path(args.output)
    need(output.is_absolute() and output.parent.resolve() == output.parent and not output.exists(), 'NEW_CANONICAL_PDF_DIAGNOSTIC_OUTPUT_REQUIRED')
    parent = output.parent.stat()
    need(parent.st_uid == os.getuid() and stat.S_IMODE(parent.st_mode) == 0o700, 'OWNED0700_PDF_DIAGNOSTIC_PARENT_REQUIRED')
    def ref(name):
        return {'path': getattr(args, name), 'sha256': getattr(args, name + '_sha256')}
    try:
        result = authenticate(ref('binding'), ref('host_report'), ref('root_review'))
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, AssertionError) as exc:
        result = {'schema': 'frw.Root.pptx-pdf-runtime-observation-authentication.v1', 'status': 'UNKNOWN',
                  'reason_class': type(exc).__name__, 'actual_proof': 'NOT_ESTABLISHED', 'consumer_safety': 'UNKNOWN',
                  'full_format_acceptance': False, 'editable_preservation': 'FAIL_RETAINED'}
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(result, stream, ensure_ascii=True, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'consumer_safety': result['consumer_safety']}))
    return 0 if result['status'] == 'REAL_CONSUMER_OBSERVATIONS_AUTHENTICATED_ROOT_REVIEW_REQUIRED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
