"""Exact future V02 admission and producer/consumer joins; no execution entrypoint."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import runpy

HERE = Path(__file__).resolve().parent
BASE = runpy.run_path(str(HERE / 's16_boundary.py'))
read_ref, pinned_read, reference, reject_interfaces = (BASE[n] for n in ('read_ref', 'pinned_read', 'reference', 'reject_interfaces'))
need = BASE['need']
CONTRACT = runpy.run_path(str(HERE / 'pptx_pdf_contract.py'))
PPTX_MIME, PDF_MIME, EXPORT_FILTER = CONTRACT['PPTX_MIME'], CONTRACT['PDF_MIME'], CONTRACT['EXPORT_FILTER']
ENGINE, STRACE, PDFTOTEXT = CONTRACT['ENGINE'], CONTRACT['STRACE'], CONTRACT['PDFTOTEXT']
FIELDS = {'schema', 'operator', 'received_artifact', 'received_bytes', 'delivered_pdf', 'delivered_pdf_bytes',
          'mime_type', 'ingress_receipt', 'plan', 'run', 'origin_assessment', 'current', 'qualification',
          'consumer_qualification', 'operation_clock', 'consumer', 'strace', 'kernel', 'import_settings',
          'invocation_id', 'expectation', 'pdf_reader', 'source_manifest', 'export_filter'}
REF_FIELDS = ('received_artifact', 'delivered_pdf', 'ingress_receipt', 'plan', 'run', 'origin_assessment',
              'current', 'qualification', 'consumer_qualification', 'operation_clock', 'expectation', 'source_manifest')
IMPORT_SETTINGS = {'encoding': 'OOXML-per-part-declaration', 'delimiter': 'not-applicable', 'locale': 'C.UTF-8',
                   'other_declared_options': {'profile': 'fresh-default', 'filter': EXPORT_FILTER,
                       'column_types': 'not-applicable', 'formula_evaluation': 'not-evaluated', 'input_extension': 'pptx'}}


def _tool(value, path):
    need(type(value) is dict and set(value) == {'executable', 'version'} and reference(value['executable'])
         and value['executable']['path'] == path and type(value['version']) is str
         and 0 < len(value['version']) <= 128, 'ACTUAL_TOOL_VERSION_PIN_REQUIRED')
    return value


def _reader(value):
    need(type(value) is dict and set(value) == {'source', 'executable', 'version'}
         and reference(value['source']) and reference(value['executable'])
         and value['executable']['path'] == PDFTOTEXT and type(value['version']) is str
         and 0 < len(value['version']) <= 128, 'EXACT_PDF_READER_AND_TOOL_PINS_REQUIRED')
    return value


def validate(binding):
    need(type(binding) is dict and set(binding) == FIELDS, 'EXACT_PPTX_PDF_ADMISSION_FIELDS')
    reject_interfaces(binding)
    need(binding['schema'] == 'frw.Root.pptx-pdf-native-consumer-admission.v1' and binding['operator'] == 'Root',
         'ROOT_PPTX_PDF_ADMISSION_REQUIRED')
    for name in REF_FIELDS:
        need(reference(binding[name]), 'EXACT_PIN_' + name)
    need(type(binding['received_bytes']) is int and 0 < binding['received_bytes'] <= CONTRACT['MAX_PPTX_BYTES'], 'PPTX_BYTE_BOUND')
    need(type(binding['delivered_pdf_bytes']) is int and 0 < binding['delivered_pdf_bytes'] <= CONTRACT['MAX_PDF_BYTES'], 'PDF_BYTE_BOUND')
    need(binding['mime_type'] == PPTX_MIME and binding['export_filter'] == EXPORT_FILTER, 'FIXED_PPTX_PDF_FILTER_REQUIRED')
    need(type(binding['invocation_id']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', binding['invocation_id']) is not None,
         'FINITE_INVOCATION_ID')
    _tool(binding['consumer'], ENGINE)
    _tool(binding['strace'], STRACE)
    _reader(binding['pdf_reader'])
    kernel = binding['kernel']
    need(type(kernel) is dict and set(kernel) == {'release', 'boot_id'}
         and all(type(v) is str and 0 < len(v) <= 128 for v in kernel.values()), 'ACTUAL_KERNEL_BOOT_REQUIRED')
    need(binding['import_settings'] == IMPORT_SETTINGS, 'FIXED_PDF_EXPORT_IMPORT_SETTINGS_REQUIRED')
    return 'pptx'


def _json_ref(ref, cap=2 * 1024 * 1024):
    need(type(ref) is dict and set(ref) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}), 'EXACT_JSON_REF_REQUIRED')
    raw = read_ref({k: ref[k] for k in ('path', 'sha256')}, cap, private=True)
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'JSON_REF_BYTE_JOIN')
    return json.loads(raw)


def _wire(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}, 'WIRE_REF_REQUIRED')
    raw = read_ref({k: ref[k] for k in ('path', 'sha256')}, 2 * 1024 * 1024, private=True)
    need(len(raw) == ref['bytes'], 'WIRE_BYTE_JOIN')
    return json.loads(raw)


def _check_plan_run_receipt(binding, values):
    plan, run, receipt = values['plan'], values['run'], values['ingress_receipt']
    need(type(plan) is dict and plan.get('operator') == 'Root'
         and plan.get('schema') == 'friday.tester.continue-closed-unknown.v2'
         and type(run) is dict and run.get('id') == plan.get('new_run_id')
         and run.get('scenario') == plan.get('new_scenario') and run.get('step') == 0
         and run.get('send_state') == 'sent' and run.get('send_attempts') == 1 and run.get('repeat_count') == 0
         and type(run.get('sent_message_id')) is int and run['sent_message_id'] > 0,
         'EXACT_EXISTING_ONCE_SENT_PLAN_RUN_JOIN_REQUIRED')
    scenario = run['scenario']
    need(type(scenario) is dict and type(scenario.get('steps')) is list and len(scenario['steps']) == 1
         and type(plan.get('new_task', {}).get('request')) is str, 'ONE_EXACT_V02_TASK_REQUIRED')
    task, source = plan['new_task'], scenario['steps'][0].get('input', {})
    request = 'Create five slides from the admitted workbook, with conclusions and one chart; return PPTX and PDF.'
    output = [{'filename': None, 'mime_type': PPTX_MIME}, {'filename': None, 'mime_type': PDF_MIME}]
    need(task.get('kind') == 'ordinary-document-task' and task.get('request') == request
         and task.get('source_reference') is None and task.get('output') == output
         and type(task.get('nonce')) is str and re.fullmatch('[a-f0-9]{32}', task['nonce']) is not None
         and source.get('kind') == 'document' and source.get('filename') == 'admitted-workbook.xlsx'
         and source.get('path') == '/private-bindings/admitted-workbook.xlsx'
         and source.get('sha256') == 'e9e343c8adb24779378e8d4491d329ece731eb865c134a6fa24b56741ced8f21'
         and source.get('mime_type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
         and source.get('caption') == request and source.get('stat', {}).get('size_bytes') == 5660
         and scenario.get('peer_id') == 900000001 and scenario.get('tester_id') == 900000002,
         'EXACT_GENUINE_V02_TABLE_REQUEST_NEUTRAL_PAIR_REQUIRED')
    downloaded = receipt.get('downloaded_artifact', {})
    need(downloaded == {**binding['received_artifact'], 'bytes': binding['received_bytes']}
         and receipt.get('run_id') == run['id'] and receipt.get('step') == 0
         and receipt.get('sent_message_id') == run['sent_message_id']
         and receipt.get('reply_to_message_id') == run['sent_message_id']
         and receipt.get('scenario_sha256') == run.get('scenario_sha256')
         and type(receipt.get('scenario_sha256')) is str and len(receipt['scenario_sha256']) == 64
         and receipt.get('request_body_sha256') == run.get('request_metadata', {}).get('body_sha256')
         and receipt.get('authenticated_peer_id') == scenario.get('peer_id')
         and receipt.get('tester_id') == scenario.get('tester_id')
         and type(receipt.get('authenticated_peer_id')) is int and type(receipt.get('tester_id')) is int
         and receipt.get('private_sender') is True and receipt.get('received_original_bytes') is True
         and receipt.get('artifact_acceptance') == 'RECEIVED_UNGRADED'
         and receipt.get('advertised_document', {}).get('mime_type') == binding['mime_type'],
         'ACTUAL_PRIVATE_ORIGINAL_V02_PPTX_JOIN_REQUIRED')
    companion = receipt.get('companion_pdf', {})
    need(type(companion) is dict and companion.get('artifact') == {**binding['delivered_pdf'], 'bytes': binding['delivered_pdf_bytes']}
         and companion.get('run_id') == run['id'] and companion.get('step') == 0
         and companion.get('reply_to_message_id') == run['sent_message_id']
         and companion.get('received_original_bytes') is True
         and companion.get('artifact_acceptance') == 'RECEIVED_UNGRADED'
         and companion.get('advertised_document', {}).get('mime_type') == PDF_MIME
         and type(companion.get('getFile_wire')) is dict
         and set(companion['getFile_wire']) == {'path', 'sha256', 'bytes'}, 'SAME_REPLY_COMPANION_PDF_JOIN_REQUIRED')
    update = _wire(receipt.get('source_update'))
    updates = _wire(receipt.get('getUpdates_wire'))
    getfile = _wire(receipt.get('getFile_wire'))
    companion_getfile = _wire(companion['getFile_wire'])
    message = update.get('message', {})
    need(updates.get('ok') is True and type(updates.get('result')) is list
         and sum(x == update for x in updates['result']) == 1
         and update.get('update_id') == receipt.get('update_id')
         and message.get('message_id') == receipt.get('message_id')
         and message.get('chat', {}).get('type') == 'private'
         and message.get('from', {}).get('id') == receipt['authenticated_peer_id']
         and message.get('chat', {}).get('id') == receipt['authenticated_peer_id']
         and message.get('reply_to_message', {}).get('message_id') == run['sent_message_id']
         and message.get('document') == receipt.get('advertised_document')
         and getfile.get('ok') is True and getfile.get('result') == receipt.get('getFile')
         and getfile['result'].get('file_id') == message['document'].get('file_id')
         and companion_getfile.get('ok') is True
         and companion_getfile.get('result') == companion.get('getFile')
         and companion_getfile['result'].get('file_id') == companion['advertised_document'].get('file_id'),
         'ACTUAL_V02_WIRE_ORIGIN_JOIN_REQUIRED')
    return [receipt['source_update'], receipt['getUpdates_wire'], receipt['getFile_wire'], companion['getFile_wire']]


def _check_origin(binding, values):
    origin, run, receipt = values['origin_assessment'], values['run'], values['ingress_receipt']
    fields = {'schema', 'operator', 'case', 'received_artifact', 'received_bytes', 'delivered_pdf', 'delivered_pdf_bytes',
              'mime_type', 'ingress_receipt', 'run_id', 'sent_message_id', 'root_wire_origin_review',
              'receiver_reconciliation', 'native_origin', 'same_created_presentation', 'editable_preservation',
              'whole_case_acceptance'}
    need(type(origin) is dict and set(origin) == fields and origin['schema'] == 'frw.Root.pptx-pdf-same-created-v02-custody.v1'
         and origin['operator'] == 'Root' and origin['case'] == 'V-02'
         and origin['whole_case_acceptance'] is False and origin['same_created_presentation'] is True
         and origin['editable_preservation'] == 'FAIL_RETAINED'
         and all(origin[n] == binding[n] for n in ('received_artifact', 'received_bytes', 'delivered_pdf',
                                                    'delivered_pdf_bytes', 'mime_type', 'ingress_receipt'))
         and origin['run_id'] == run['id'] and origin['sent_message_id'] == run['sent_message_id']
         and origin['root_wire_origin_review'] == 'EXACT_PEER_REPLY_DOWNLOAD_AND_SAVED_NATIVE_HASH_JOIN'
         and reference(origin['receiver_reconciliation']) and reference(origin['native_origin']),
         'EXPLICIT_ROOT_V02_CUSTODY_REQUIRED')
    reconciled = _json_ref(origin['receiver_reconciliation'])
    native = _json_ref(origin['native_origin'])
    need(reconciled.get('status') == 'RECEIVED_UNGRADED' and reconciled.get('run_id') == run['id']
         and reconciled.get('sent_message_id') == run['sent_message_id'] and reconciled.get('semantic_acceptance') is False
         and reconciled.get('canonical_unchanged') is True
         and sum(f == receipt for f in reconciled.get('files', [])) == 1
         and {k: reconciled.get('saved_origin', {}).get(k) for k in ('path', 'sha256')} == origin['native_origin'],
         'EXACT_V02_RECEIVER_RECONCILIATION_REQUIRED')
    artifacts = native.get('local_artifacts', [])
    for artifact, size in ((binding['received_artifact'], binding['received_bytes']),
                           (binding['delivered_pdf'], binding['delivered_pdf_bytes'])):
        saved = [a for a in artifacts if a.get('ref', {}).get('sha256') == artifact['sha256']
                 and a.get('ref', {}).get('bytes') == size]
        need(len(saved) == 1 and saved[0].get('origin', {}).get('assistant_media_reference') is True
             and saved[0].get('origin', {}).get('bytes_match_write_response') is True
             and saved[0].get('origin', {}).get('write_tool_verified') is True,
             'EXACT_V02_NATIVE_TOOL_WRITE_JOIN_REQUIRED')
    return [origin['receiver_reconciliation'], origin['native_origin']]


def qualification_identity(binding, qualifier):
    fields = {'schema', 'operator', 'format', 'export_filter', 'consumer', 'strace', 'kernel', 'import_settings',
              'pdf_reader', 'source_manifest', 'actual_observation', 'full_format_acceptance', 'editable_preservation'}
    need(type(qualifier) is dict and set(qualifier) == fields
         and qualifier.get('full_format_acceptance') is False and qualifier.get('editable_preservation') == 'FAIL_RETAINED'
         and qualifier.get('schema') == 'frw.Root.pptx-pdf-native-consumer-qualification.v1'
         and qualifier.get('operator') == 'Root' and qualifier.get('format') == 'pptx'
         and qualifier.get('export_filter') == EXPORT_FILTER
         and all(qualifier.get(n) == binding[n] for n in ('consumer', 'strace', 'kernel', 'import_settings', 'pdf_reader', 'source_manifest'))
         and reference(qualifier.get('actual_observation')), 'ACTUAL_KNOWN_PDF_QUALIFICATION_JOIN_REQUIRED')
    return qualifier


def _check_known_qualification(binding, values):
    qualifier = qualification_identity(binding, values['consumer_qualification'])
    actual = _json_ref(qualifier['actual_observation'])
    need(actual.get('schema') == 'frw.Root.pptx-pdf-native-qualification-observation.v1'
         and actual.get('operator') == 'Root' and actual.get('format') == 'pptx'
         and actual.get('state') == 'ACTUAL_KNOWN_PPTX_PDF_EXPORT_COMPLETE_ROOT_REVIEW_REQUIRED'
         and actual.get('own_processes_zero') is True and actual.get('temporary_homes_removed') is True
         and actual.get('whole_case_acceptance') is False and actual.get('full_format_acceptance') is False
         and actual.get('editable_preservation') == 'FAIL_RETAINED'
         and all(actual.get(n) == binding[n] for n in ('consumer', 'strace', 'kernel', 'pdf_reader', 'source_manifest')),
         'COMPLETE_ACTUAL_KNOWN_PDF_QUALIFICATION_OBSERVATION_REQUIRED')
    manifest = _json_ref(binding['source_manifest'])
    leaves = {row.get('path'): row.get('sha256') for row in manifest.get('files', []) if type(row) is dict}
    source_names = {'qualify_pptx_pdf.py', 'pptx_pdf_contract.py', 'pdf_pages.py',
                    'presentation_contract.py', 'scoped_presentation.py', 'read_extract.py'}
    sources = actual.get('sources')
    need(type(sources) is dict and set(sources) == source_names
         and all(leaves.get('code/' + name) == sources[name] for name in source_names)
         and actual.get('qualifier_source_sha256') == sources['qualify_pptx_pdf.py'],
         'KNOWN_PDF_QUALIFICATION_SOURCE_GRAPH_JOIN_REQUIRED')
    fixture = HERE.parent / 'fixtures/known-visible-label.pptx'
    expectation_path = HERE.parent / 'fixtures/KNOWN-PPTX-PDF-EXPECTATION.json'
    known_input = {'path': str(fixture), 'sha256': leaves.get('fixtures/known-visible-label.pptx')}
    known_expectation = {'path': str(expectation_path), 'sha256': leaves.get('fixtures/KNOWN-PPTX-PDF-EXPECTATION.json')}
    need(reference(known_input) and reference(known_expectation), 'KNOWN_FIXTURE_PINS_REQUIRED')
    original = read_ref(known_input, CONTRACT['MAX_PPTX_BYTES'], private=True)
    expected = _json_ref(known_expectation)
    CONTRACT['validate_source_expectation'](original, expected)
    need(expected['source_only_fixture'] is True, 'KNOWN_FIXTURE_PROVENANCE_REQUIRED')
    phases = actual.get('phases', [])
    need(type(phases) is list and len(phases) == 1 and phases[0].get('stage') == 'export'
         and phases[0].get('qualified') is True and phases[0].get('input_unchanged') is True
         and phases[0].get('output_comparison', {}).get('status') == 'MATCH', 'ACTUAL_ONE_PHASE_PDF_QUALIFICATION_REQUIRED')
    need(actual.get('input_comparison', {}).get('status') == 'MATCH'
         and actual.get('qualification_input') == known_input
         and actual.get('expectation') == known_expectation, 'KNOWN_PDF_INPUT_EXPECTATION_LINEAGE_REQUIRED')
    commands = actual.get('commands', [])
    need(type(commands) is list and len(commands) == 4
         and all(c.get('state') == 'RETURNED_ZERO' and c.get('exit_code') == 0
                 and c.get('process_reaped') is True and c.get('own_processes_zero') is True
                 and c.get('log', {}).get('complete') is True for c in commands),
         'COMPLETE_BOUNDED_PDF_QUALIFICATION_COMMANDS_REQUIRED')
    need(all(type(actual.get(n)) in (int, float) and math.isfinite(actual[n])
             for n in ('started_monotonic', 'deadline_monotonic', 'ended_monotonic'))
         and actual['started_monotonic'] <= actual['ended_monotonic'] <= actual['deadline_monotonic']
         and actual['deadline_monotonic'] - actual['started_monotonic'] <= 90, 'FINITE_KNOWN_PDF_WINDOW_REQUIRED')
    CONTRACT['finite_clock'](actual.get('operation_clock'), 90)
    known_clock = actual['operation_clock']
    need(known_clock['boot_id'] == binding['kernel']['boot_id']
         and known_clock['origin_monotonic'] <= actual['started_monotonic']
         and actual['deadline_monotonic'] <= known_clock['deadline_monotonic'], 'KNOWN_CLOCK_CUSTODY_JOIN')
    known_current = _json_ref(actual.get('current'))
    need(known_current.get('schema') == 'frw.Root.pptx-pdf-known-export-current.v1'
         and known_current.get('operator') == 'Root' and known_current.get('source_only_accepted') is True
         and known_current.get('source_directory') == str(HERE)
         and known_current.get('source_manifest') == binding['source_manifest']
         and known_current.get('kernel') == binding['kernel']
         and known_current.get('whole_case_acceptance') is False and known_current.get('original_effect_closed') is True,
         'KNOWN_CURRENT_SOURCE_CUSTODY_JOIN')
    for n in ('consumer', 'strace', 'pdf_reader'):
        need(known_current.get('toolchain', {}).get(n) == binding[n], 'KNOWN_CURRENT_TOOLCHAIN_CUSTODY_JOIN')
    intent = _json_ref(actual.get('once_intent'))
    need(intent.get('schema') == 'frw.Root.pptx-pdf-export-once-intent.v1' and intent.get('operator') == 'Root'
         and intent.get('state') == 'INTENT_BEFORE_CGROUP_MOVE' and intent.get('consumed') is False
         and intent.get('operation_id') == actual.get('operation_id')
         and intent.get('current') == actual['current'] and intent.get('operation_clock') == known_clock
         and intent.get('expectation') == known_expectation
         and intent.get('source_manifest') == binding['source_manifest']
         and intent.get('input') == {**known_input, 'bytes': len(original), 'mime': PPTX_MIME}, 'KNOWN_ONCE_CUSTODY_JOIN')
    refs = [qualifier['actual_observation'], actual['current'], actual['once_intent']]
    for command in commands:
        log = command['log']
        need(type(log) is dict and set(log) == {'path', 'sha256', 'bytes', 'complete'}, 'EXACT_PDF_LOG_REF')
        ref = {k: log[k] for k in ('path', 'sha256')}
        need(len(read_ref(ref, 65536, private=True)) == log['bytes'], 'COMPLETE_PDF_LOG_BYTE_JOIN')
        refs.append(ref)
    output = phases[0].get('output_artifact')
    CONTRACT['artifact'](output)
    output_raw = read_ref({k: output[k] for k in ('path', 'sha256')}, CONTRACT['MAX_PDF_BYTES'], private=True)
    need(len(output_raw) == output['bytes'], 'KNOWN_PDF_ARTIFACT_BYTE_JOIN')
    output_obs = _json_ref(phases[0]['output_observation'], 2 * 1024 * 1024)
    need(output_obs.get('artifact') == output, 'KNOWN_PDF_OBSERVATION_ARTIFACT_PATH_JOIN')
    CONTRACT['validate_pdf_observation'](output_obs, output_raw, expected)
    need(phases[0]['output_comparison'] == output_obs['comparison'], 'KNOWN_PDF_OBSERVATION_COMPARISON_JOIN')
    refs.extend([{k: output[k] for k in ('path', 'sha256')}, phases[0]['output_observation']])
    input_obs = _json_ref(actual['input_observation'], 2 * 1024 * 1024)
    need(input_obs == CONTRACT['observe_pptx'](original), 'KNOWN_PPTX_STRUCTURAL_OBSERVATION_JOIN')
    need(input_obs['bounded_native_admission'] is True and input_obs['semantic_sha256'] == expected['pptx_semantic_sha256'],
         'KNOWN_INPUT_EXPECTATION_SOURCE_SEMANTICS_JOIN')
    reader = output_obs.get('reader', {})
    need(reader.get('source') == binding['pdf_reader']['source']
         and reader.get('helper') == {'path': PDFTOTEXT, 'sha256': binding['pdf_reader']['executable']['sha256'],
                                      'version': binding['pdf_reader']['version']}
         and reader.get('ocr_or_hosted_fallback') is False, 'KNOWN_PDF_READER_JOIN')
    refs.extend([actual['input_observation'], known_input, known_expectation])
    return refs


def _check_current(binding, values):
    current = values['current']
    need(type(current) is dict and current.get('schema') == 'frw.Root.same-received-consumer-current.v1'
         and current.get('operator') == 'Root' and current.get('actual_qualification') == binding['qualification']
         and current.get('whole_case_acceptance') is False and current.get('original_effect_closed') is True,
         'ROOT_CURRENT_PDF_QUALIFICATION_JOIN_REQUIRED')
    refs, records = [], {}
    for name in ('installed_source', 'diagnostic_source', 'local_resource_decision'):
        need(reference(current.get(name)), 'ROOT_CURRENT_PIN_REQUIRED_' + name)
        records[name] = _json_ref(current[name])
        refs.append(current[name])
    installed = records['installed_source']
    match = re.fullmatch(r'frw\.Root\.ordinary-current([1-9][0-9]*)-bindings\.v1', installed.get('schema', ''))
    need(match is not None, 'ACTUAL_ORDINARY_INSTALLED_CURRENT_SCHEMA_REQUIRED')
    for name in ('actual_tuple', 'installed_source', 'sole_writer', 'fresh_native_proof', 'permanent_services'):
        need(reference(installed.get(name)), 'ACTUAL_INSTALLED_CURRENT_PIN_REQUIRED_' + name)
        read_ref(installed[name], 2 * 1024 * 1024, private=True)
        refs.append(installed[name])
    tuple_record = _json_ref(installed['actual_tuple'])
    actual_tuple = tuple_record.get('tuple', {})
    need(tuple_record.get('schema') == 'frw.Root.actual-installed-tuple.v1'
         and actual_tuple.get('service_owner') == 'Root'
         and actual_tuple.get('source') == actual_tuple.get('project') == int(match[1]), 'ACTUAL_INSTALLED_SOURCE_TUPLE_JOIN_REQUIRED')
    writer = _json_ref(installed['sole_writer'])
    need(writer.get('schema') == 'frw.Root.s07-sole-writer-authority.v1' and writer.get('operator') == 'Root',
         'EXISTING_ROOT_SOLE_WRITER_REQUIRED')
    source = records['diagnostic_source']
    need(source.get('source_only_accepted') is True and source.get('source_directory') == str(HERE)
         and source.get('source_manifest') == binding['source_manifest'], 'ROOT_ACCEPTED_EXACT_PDF_SOURCE_GRAPH_REQUIRED')
    manifest = _json_ref(binding['source_manifest'])
    leaves = {row.get('path'): row.get('sha256') for row in manifest.get('files', []) if type(row) is dict}
    need(all(leaves.get('code/' + leaf.name) == hashlib.sha256(leaf.read_bytes()).hexdigest()
             for leaf in HERE.glob('*.py')), 'ROOT_ACCEPTED_PDF_MANIFEST_HASH_JOIN')
    resources = records['local_resource_decision']
    need(resources.get('read_only') is True and resources.get('new_baseline_pause') is False
         and type(resources.get('decision')) is str and bool(resources['decision'])
         and type(resources.get('local_affinity')) is list and len(set(resources['local_affinity'])) >= 2
         and all(type(cpu) is int and cpu >= 0 for cpu in resources['local_affinity']),
         'ACTUAL_READONLY_LOCAL_RESOURCE_DECISION_REQUIRED')
    return refs


def correlate(binding):
    validate(binding)
    values = {name: _json_ref(binding[name]) for name in
              ('ingress_receipt', 'plan', 'run', 'origin_assessment', 'current', 'qualification',
               'consumer_qualification', 'operation_clock', 'expectation')}
    expected = values['expectation']
    CONTRACT['validate_expectation'](expected, binding['received_artifact']['sha256'], binding['received_bytes'])
    need(expected['source_only_fixture'] is False, 'GENUINE_RECEIVED_EXPECTATION_REQUIRED')
    original = read_ref(binding['received_artifact'], CONTRACT['MAX_PPTX_BYTES'], private=True)
    CONTRACT['validate_source_expectation'](original, expected)
    observed = CONTRACT['observe_pptx'](original)
    need(len(original) == binding['received_bytes'] and observed['bounded_native_admission'] is True
         and observed['semantic_sha256'] == expected['pptx_semantic_sha256'], 'GENUINE_RECEIVED_SOURCE_EXPECTATION_JOIN')
    known_manifest = _json_ref(binding['source_manifest'])
    known_sha = next((r['sha256'] for r in known_manifest.get('files', [])
                      if r.get('path') == 'fixtures/known-visible-label.pptx'), None)
    need(binding['received_artifact']['sha256'] != known_sha, 'KNOWN_FIXTURE_CANNOT_BE_USER_ARTIFACT')
    refs = _check_known_qualification(binding, values)
    refs += _check_plan_run_receipt(binding, values)
    refs += _check_origin(binding, values)
    refs += _check_current(binding, values)
    clock = values['operation_clock']
    CONTRACT['finite_clock'](clock, 120)
    need(clock['boot_id'] == binding['kernel']['boot_id'], 'OPERATION_CLOCK_BOOT_MISMATCH')
    values['additional_custody_refs'] = refs
    return values
