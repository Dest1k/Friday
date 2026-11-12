"""Dormant one-load caller; imports no UNO, opens nothing on import.

The embedded entry passes its already connected, empty Desktop. This module
never reconnects, retries, launches Office, stores or interprets diagnostic
success as acceptance. Root alone supplies a future admission and private inputs.
"""
import json
import re
from pathlib import Path

import f06_contract as c
from conversion_probe import exception_metadata
from readonly_diagnostic import observe_one_readonly
from request_args_compat_v2 import install_request_args_compat, restore_request_args_compat

MODE = 'one-template-diagnostic'
IDS = ['template-ott-source']
SELECTED_SHA = '61c72a4b14ce2a83677acce3b267fb00aeb773e7dc74ffd448a449bd5dfb4650'
SELECTED_URL = 'file:///inputs/native-outputs/retained-source.ott'
MAX_BYTES = 32768
QUALIFIED = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}\Z')
PHASES = frozenset(('entered', 'request_type_before', 'get_request_before',
    'get_request_after', 'classify_before', 'error_code_before', 'error_code_after',
    'classify_after', 'get_continuations_before', 'get_continuations_after',
    'query_abort_type_before', 'query_interface_before', 'query_interface_after',
    'select_before', 'select_after', 'no_abort_continuation', 'callback_exception_reraised'))
KNOWN_PAYLOADS = frozenset(('com.sun.star.task.DocumentPasswordRequest',
    'com.sun.star.task.DocumentMSPasswordRequest', 'com.sun.star.task.DocumentPasswordRequest2',
    'com.sun.star.task.DocumentMSPasswordRequest2', 'com.sun.star.task.ErrorCodeRequest2'))
REASONS = frozenset(('MISSING_CONVERSION_OBSERVATION', 'EXTRA_CALLBACK',
    'UNKNOWN_CLASS_IDENTITY', 'CALLBACK_FAULT', 'HOOK_CAS_OR_RESTORATION_DRIFT',
    'METADATA_FAILURE', 'INPUT_CAS_DRIFT', 'COMPAT_RESTORATION_DRIFT',
    'LOAD_OR_SEMANTIC_FAULT', 'DOCUMENT_CLOSE_FAULT', 'CLIENT_SCOPE_INCOMPLETE'))


def need(value, code):
    if not value:
        raise ValueError(code)


def class_identity(value):
    need(type(value) is str and len(value) <= 240 and QUALIFIED.fullmatch(value), 'CLASS_ONLY')


def exception_projection(value, *, chain=False):
    """Validate known metadata shapes BEFORE any JSON traversal or output."""
    need(type(value) is dict, 'EXCEPTION_OBJECT')
    if chain:
        need(set(value) == {'chain', 'chain_truncated_or_cycle'}
             and type(value['chain']) is list and 1 <= len(value['chain']) <= 4
             and type(value['chain_truncated_or_cycle']) is bool, 'EXCEPTION_CHAIN')
        for row in value['chain']:
            need(type(row) is dict and set(row) == {'edge', 'exception_class', 'source_frames', 'frames_truncated'}
                 and row['edge'] in ('top', 'cause', 'context')
                 and type(row['frames_truncated']) is bool, 'EXCEPTION_CHAIN_ROW')
            exception_projection({'exception_class': row['exception_class'], 'source_frames': row['source_frames']})
        return
    need(set(value) == {'exception_class', 'source_frames'}, 'EXCEPTION_FIELDS')
    class_identity(value['exception_class'])
    frames = value['source_frames']
    need(type(frames) is list and len(frames) <= 12, 'EXCEPTION_FRAMES')
    for frame in frames:
        need(type(frame) is dict and set(frame) in ({'source', 'line'}, {'source', 'function', 'line'}), 'FRAME_FIELDS')
        need(frame['source'] in ('conversion_probe.py', 'callback_observer_v2.py', 'readonly_diagnostic.py',
             'callback_observer.py', 'office_fixture_driver.py', 'uno.py', 'unohelper.py', 'OTHER_SOURCE')
             and type(frame['line']) is int and frame['line'] > 0, 'FRAME_TYPES')
        if 'function' in frame:
            need(type(frame['function']) is str and len(frame['function']) <= 100 and QUALIFIED.fullmatch(frame['function']), 'FRAME_FUNCTION')


def probe_projection(probe):
    # An early probe refusal may leave the initially empty metadata dictionary.
    need(type(probe) is dict, 'PROBE_OBJECT')
    if not probe:
        return
    required = {'schema', 'get_request_calls', 'purpose', 'setter_events', 'setter_events_overflow',
                'metadata_incomplete', 'restored', 'origin'}
    optional = {'cached_exception_setters_planned', 'get_request_error', 'setters_restored', 'cleanup_failures'}
    need(required <= set(probe) <= required | optional, 'PROBE_FIELDS')
    need(probe['schema'] == 'friday.pyuno.conversion-metadata.v1'
         and probe['purpose'] == 'DIAGNOSTIC_NOT_ACCEPTANCE'
         and probe['origin'] == 'RETURN_OR_ERROR_CONVERSION_UNKNOWN'
         and type(probe['get_request_calls']) is int and 0 <= probe['get_request_calls'] <= 1, 'PROBE_FIXED')
    for key in ('setter_events_overflow', 'metadata_incomplete', 'restored'):
        need(type(probe[key]) is bool, 'PROBE_BOOLEAN')
    for key in ('cached_exception_setters_planned', 'setters_restored'):
        if key in probe:
            need(type(probe[key]) is int and 0 <= probe[key] <= 8192, 'PROBE_COUNT')
    if 'get_request_error' in probe:
        exception_projection(probe['get_request_error'], chain=True)
    if 'cleanup_failures' in probe:
        known = {'POSTSCAN_FAILED', 'GENERATED_CLASS_IDENTITY_DRIFT', 'SETTER_RESTORE_FAILED',
                 'SETTER_RESTORE_CAS_DRIFT', 'HELPER_RESTORE_CAS_DRIFT', 'HELPER_RESTORE_FAILED', 'COMPAT_SETTER_DRIFT'}
        need(type(probe['cleanup_failures']) is list and len(probe['cleanup_failures']) <= 16390
             and all(type(item) is str and item in known for item in probe['cleanup_failures']), 'PROBE_CLEANUP')
    need(type(probe['setter_events']) is list and len(probe['setter_events']) <= 16, 'SETTER_EVENTS')
    for row in probe['setter_events']:
        need(type(row) is dict and {'generated_exception_class_during_conversion', 'attribute', 'phase'} <= set(row)
             <= {'generated_exception_class_during_conversion', 'attribute', 'phase', 'error'}, 'SETTER_FIELDS')
        class_identity(row['generated_exception_class_during_conversion'])
        need(row['generated_exception_class_during_conversion'].startswith('com.sun.star.')
             and row['attribute'] == 'args'
             and row['phase'] in ('delegate_before', 'delegate_exception_reraised', 'delegate_returned'), 'SETTER_FIXED')
        if 'error' in row:
            exception_projection(row['error'], chain=True)


def adapter_projection(value):
    required = {'schema', 'state', 'load_calls', 'opened', 'semantic_match', 'close_attempted',
                'closed_or_disposed', 'planned_stores', 'store_count_instrumented',
                'original_strict_all_pass', 'acceptance_granted', 'actual_payload_type',
                'interaction_events', 'get_request_window_consumed'}
    optional = {'load_or_semantic_error', 'close_error', 'dispose_error'}
    need(type(value) is dict and required <= set(value) <= required | optional, 'ADAPTER_FIELDS')
    need(value['schema'] == 'friday.f06.one-bridge-observation.v1'
         and value['state'] == 'DIAGNOSTIC_NOT_QUALIFICATION'
         and type(value['load_calls']) is int and value['load_calls'] == 1
         and type(value['planned_stores']) is int and value['planned_stores'] == 0
         and value['store_count_instrumented'] is False
         and value['original_strict_all_pass'] is False and value['acceptance_granted'] is False
         and value['actual_payload_type'] == 'UNKNOWN', 'ADAPTER_FIXED')
    for key in ('opened', 'semantic_match', 'close_attempted', 'closed_or_disposed', 'get_request_window_consumed'):
        need(type(value[key]) is bool, 'ADAPTER_BOOLEAN')
    need(not value['semantic_match'] or value['opened'], 'SEMANTICS_REQUIRES_OPEN')
    need(value['opened'] == value['close_attempted'], 'CLOSE_REQUIRED_IF_OPENED')
    for key in optional:
        if key in value:
            exception_projection(value[key], chain=True)
    events = value['interaction_events']
    # The adapter itself can append an extra rejected callback. Keep bounded
    # evidence; its OneShotConversionProbe prevents a second native getRequest.
    need(type(events) is list and len(events) <= 16, 'EVENT_BOUND')
    for event in events:
        required_event = {'phase', 'phases', 'request_kind', 'abort_selected'}
        optional_event = {'request_class', 'payload_class', 'is_document_password', 'is_document_ms_password',
            'is_error_code_request2', 'error_code', 'continuation_attempts', 'callback_error_phase',
            'callback_error', 'conversion_probe'}
        need(type(event) is dict and required_event <= set(event) <= required_event | optional_event, 'EVENT_FIELDS')
        seq = event['phases']
        need(event['phase'] in PHASES and type(seq) is list and 1 <= len(seq) <= 128
             and all(type(item) is str and item in PHASES for item in seq)
             and seq[0] == 'entered' and seq[-1] == event['phase'], 'EVENT_PHASES')
        need(event['request_kind'] in ('UNCLASSIFIED', 'DocumentPasswordRequest', 'DocumentMSPasswordRequest', 'ErrorCodeRequest2', 'OTHER')
             and type(event['abort_selected']) is bool, 'EVENT_FIXED')
        for key in ('request_class', 'payload_class'):
            if key in event:
                class_identity(event[key])
        for key in ('is_document_password', 'is_document_ms_password', 'is_error_code_request2'):
            if key in event:
                need(type(event[key]) is bool, 'EVENT_BOOLEAN')
        if 'error_code' in event:
            need(type(event['error_code']) is int and -(2**31) <= event['error_code'] < 2**31, 'EVENT_CODE')
        if 'continuation_attempts' in event:
            attempts = event['continuation_attempts']
            need(type(attempts) is list and len(attempts) <= 16, 'CONTINUATION_BOUND')
            for attempt in attempts:
                need(type(attempt) is dict and {'phase'} <= set(attempt) <= {'phase', 'abort_available'}
                     and attempt['phase'] in ('query_abort_type_before', 'query_interface_before', 'query_interface_after', 'select_before', 'select_after')
                     and ('abort_available' not in attempt or type(attempt['abort_available']) is bool), 'CONTINUATION_FIELDS')
        need(('callback_error' in event) == ('callback_error_phase' in event), 'CALLBACK_FAULT_JOIN')
        if 'callback_error' in event:
            need(event['callback_error_phase'] in PHASES and event['phase'] == 'callback_exception_reraised', 'CALLBACK_FAULT_PHASE')
            exception_projection(event['callback_error'])
        if 'conversion_probe' in event:
            probe_projection(event['conversion_probe'])
    return value


def terminal_reasons(diagnostic):
    """Pure stop policy; named conversion classes are observations, never shims."""
    adapter_projection(diagnostic)
    reasons = []
    events = diagnostic['interaction_events']
    if not events:
        reasons.append('MISSING_CONVERSION_OBSERVATION')
    if len(events) > 1:
        reasons.append('EXTRA_CALLBACK')
    for event in events:
        probe = event.get('conversion_probe', {})
        if event.get('request_kind') == 'OTHER' or event.get('payload_class') not in KNOWN_PAYLOADS:
            reasons.append('UNKNOWN_CLASS_IDENTITY')
        if 'callback_error' in event:
            reasons.append('CALLBACK_FAULT')
        if not probe or probe.get('get_request_calls') != 1 or probe.get('metadata_incomplete') or probe.get('setter_events_overflow'):
            reasons.append('METADATA_FAILURE')
        if not probe.get('restored') or probe.get('cleanup_failures'):
            reasons.append('HOOK_CAS_OR_RESTORATION_DRIFT')
    if not diagnostic['get_request_window_consumed']:
        reasons.append('MISSING_CONVERSION_OBSERVATION')
    if 'load_or_semantic_error' in diagnostic:
        reasons.append('LOAD_OR_SEMANTIC_FAULT')
    if diagnostic['opened'] and not diagnostic['closed_or_disposed'] or 'close_error' in diagnostic or 'dispose_error' in diagnostic:
        reasons.append('DOCUMENT_CLOSE_FAULT')
    return sorted(set(reasons))


def ott_source_semantic(doc):
    # Exact narrow branch from the existing driver; values never enter output.
    return (doc.supportsService('com.sun.star.text.TextDocument')
            and doc.getText().getString().splitlines() == ['OTT-UNIQUE-BEFORE', 'RETAINED-TEXT-PARAGRAPH'])


def input_snapshot(expected_digest):
    c.need(type(expected_digest) is str and re.fullmatch('[0-9a-f]{64}', expected_digest), 'INPUT_DIGEST')
    raw, manifestpin = c.private('/inputs/NATIVE-OUTPUTS.json', '/inputs')
    c.need(manifestpin['sha256'] == expected_digest, 'MANIFEST_CAS')
    manifest = c.decode(raw)
    c.manifest_contract(manifest)
    raw, stagedpin = c.private('/inputs/STAGED.json', '/inputs')
    staged = c.decode(raw)
    c.need(staged.get('selected_count') == 1 and type(staged.get('selected_count')) is int
           and staged.get('selected_fixture_ids') == IDS and staged.get('input_sha256') == expected_digest
           and type(staged.get('expected_probes')) is int and staged['expected_probes'] == 1
           and type(staged.get('expected_stores')) is int and staged['expected_stores'] == 0, 'STAGED_SELECTION')
    row = manifest['fixtures'][0]
    c.need(row['sha256'] == SELECTED_SHA, 'EXACT_SELECTED_CIPHERTEXT')
    _, cipherpin = c.private('/inputs/native-outputs/retained-source.ott', '/inputs')
    c.need(all(cipherpin[key] == row[key] for key in ('bytes', 'sha256')), 'STAGED_CIPHER_CAS')
    c.need({path.name for path in c.safe_dir('/inputs/native-outputs').iterdir()} == {'retained-source.ott'}, 'SELECTED_DIRECTORY')
    credential_raw, credentialpin = c.private('/inputs/credential.private.json', '/inputs')
    credential = manifest['credential']
    c.need(all(credentialpin[key] == credential[key] for key in ('bytes', 'sha256')), 'STAGED_CREDENTIAL_CAS')
    pins = staged.get('source_pins')
    expected = {key: row[key] for key in ('path', 'bytes', 'sha256', 'identity')}
    c.need(staged.get('credential_source') == credential
           and type(pins) is list and len(pins) == 1 and type(pins[0]) is dict
           and pins[0].get('fixture_id') == row['fixture_id']
           and all(pins[0].get(key) == value for key, value in expected.items())
           and pins[0].get('native_source_ciphertext') == expected, 'STAGED_ORIGINAL_PINS')
    return dict(manifest=manifestpin, staged=stagedpin, cipher=cipherpin, credential=credentialpin), credential_raw


def result_contract(value, expected_digest, client_exit=None):
    required = {'schema', 'state', 'mode', 'selected_count', 'selected_fixture_ids', 'input_manifest_sha256',
                'input_cas_before', 'input_cas_after', 'original_strict_all_pass', 'acceptance_granted',
                'diagnostic', 'terminal_reasons', 'client_errors'}
    need(type(value) is dict and set(value) == required, 'RESULT_FIELDS')
    need(value['schema'] == 'friday.f06.one-template-diagnostic-client.v1'
         and value['mode'] == MODE and type(value['selected_count']) is int and value['selected_count'] == 1
         and value['selected_fixture_ids'] == IDS and value['input_manifest_sha256'] == expected_digest
         and value['original_strict_all_pass'] is False and value['acceptance_granted'] is False, 'RESULT_FIXED')
    need(type(value['input_cas_before']) is bool and type(value['input_cas_after']) is bool, 'RESULT_CAS_TYPES')
    need(type(value['client_errors']) is list and len(value['client_errors']) <= 3, 'CLIENT_ERROR_BOUND')
    for row in value['client_errors']:
        need(type(row) is dict and set(row) == {'phase', 'exception'}
             and row['phase'] in ('before_inputs', 'correct_credential', 'compat_install',
                 'one_observation', 'metadata_projection', 'compat_restore', 'after_inputs'), 'CLIENT_ERROR_FIELDS')
        exception_projection(row['exception'], chain=True)
    reasons = value['terminal_reasons']
    need(type(reasons) is list and reasons == sorted(set(reasons)) and all(type(item) is str and item in REASONS for item in reasons), 'RESULT_REASONS')
    if value['diagnostic'] is None:
        need('METADATA_FAILURE' in reasons or 'CLIENT_SCOPE_INCOMPLETE' in reasons, 'RESULT_MISSING_METADATA')
    else:
        need(set(terminal_reasons(value['diagnostic'])) <= set(reasons), 'RESULT_STOP_JOIN')
    need(value['input_cas_before'] or 'CLIENT_SCOPE_INCOMPLETE' in reasons, 'RESULT_BEFORE_JOIN')
    need(value['input_cas_after'] or 'INPUT_CAS_DRIFT' in reasons, 'RESULT_AFTER_JOIN')
    state = 'TERMINAL_STOP' if reasons else 'COMPLETE_METADATA_DIAGNOSTIC_ONLY'
    need(value['state'] == state, 'RESULT_STATE_JOIN')
    if client_exit is not None:
        need(type(client_exit) is int and client_exit == (1 if reasons else 0), 'RESULT_EXIT_JOIN')
    raw = (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode()
    need(len(raw) <= MAX_BYTES, 'RESULT_32K_BOUND')
    return value


def run_once(*, uno, unohelper, desktop, property_value, interaction_handler_type,
             password_request_type, ms_password_request_type, error_code_request_type,
             input_manifest_sha256):
    # No file/document effects before the explicit fixed mode and digest checks.
    c.need(c.MODE == MODE and c.limits(MODE)['max_metadata_bytes'] == MAX_BYTES, 'MODE_AND_METADATA_BOUND')
    c.need(type(input_manifest_sha256) is str and re.fullmatch('[0-9a-f]{64}', input_manifest_sha256), 'INPUT_DIGEST')
    c.within()
    result = dict(schema='friday.f06.one-template-diagnostic-client.v1', state='TERMINAL_STOP',
        mode=MODE, selected_count=1, selected_fixture_ids=list(IDS), input_manifest_sha256=input_manifest_sha256,
        input_cas_before=False, input_cas_after=False, original_strict_all_pass=False,
        acceptance_granted=False, diagnostic=None, terminal_reasons=[], client_errors=[])
    out = c.safe_dir('/work') / 'one-template-diagnostic'
    out.mkdir(mode=0o700, exist_ok=False)  # durable document-phase boundary; never reused
    before = None
    token = None
    phase = 'before_inputs'
    def record_error(error, where):
        try:
            metadata = exception_metadata(error)
            exception_projection(metadata, chain=True)
            result['client_errors'].append(dict(phase=where, exception=metadata))
        except BaseException:
            result['terminal_reasons'].append('METADATA_FAILURE')
    try:
        before, raw = input_snapshot(input_manifest_sha256)
        result['input_cas_before'] = True
        phase = 'correct_credential'
        secret = c.decode(raw)
        password = secret['password']
        c.need(type(password) is str and bool(password), 'IN_MEMORY_CORRECT_PASSWORD')
        phase = 'compat_install'
        token = install_request_args_compat(uno)
        c.within()
        phase = 'one_observation'
        diagnostic = observe_one_readonly(uno=uno, unohelper=unohelper, desktop=desktop,
            property_value=property_value, interaction_handler_type=interaction_handler_type,
            password_request_type=password_request_type, ms_password_request_type=ms_password_request_type,
            error_code_request_type=error_code_request_type, compat_token=token,
            selected_file_url=SELECTED_URL, correct_password=password, semantic_check=ott_source_semantic)
        # No serialization can reach arbitrary adapter/object values.
        phase = 'metadata_projection'
        adapter_projection(diagnostic)
        result['diagnostic'] = diagnostic
        result['terminal_reasons'].extend(terminal_reasons(diagnostic))
    except BaseException as error:
        # Exception bodies, args, repr, str, locals and arbitrary objects are absent.
        result['terminal_reasons'].append('CLIENT_SCOPE_INCOMPLETE' if before is None else 'METADATA_FAILURE')
        record_error(error, phase)
    finally:
        if token is not None:
            try:
                restore_request_args_compat(token)
            except BaseException as error:
                result['terminal_reasons'].append('COMPAT_RESTORATION_DRIFT')
                record_error(error, 'compat_restore')
        # Always try full staged-input/credential CAS, including adapter failures.
        try:
            after, _ = input_snapshot(input_manifest_sha256)
            result['input_cas_after'] = before is not None and after == before
        except BaseException as error:
            record_error(error, 'after_inputs')
        if not result['input_cas_after']:
            result['terminal_reasons'].append('INPUT_CAS_DRIFT')
    result['terminal_reasons'] = sorted(set(result['terminal_reasons']))
    result['state'] = 'TERMINAL_STOP' if result['terminal_reasons'] else 'COMPLETE_METADATA_DIAGNOSTIC_ONLY'
    try:
        result_contract(result, input_manifest_sha256)
    except BaseException:
        # Preserve only fixed stop facts if metadata is malformed or over budget.
        result['diagnostic'] = None
        result['terminal_reasons'] = sorted(set(result['terminal_reasons']) | {'METADATA_FAILURE'})
        result['state'] = 'TERMINAL_STOP'
        result_contract(result, input_manifest_sha256)
    c.save(out / 'RESULT.json', result)
    return 1 if result['terminal_reasons'] else 0
