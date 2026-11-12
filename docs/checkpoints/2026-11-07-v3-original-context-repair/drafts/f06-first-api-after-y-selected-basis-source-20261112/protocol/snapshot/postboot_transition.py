"""Pure postboot Y transition against one explicitly selected Root metadata basis.

Root authenticates each selected raw file and original Y proof, and authenticates
the strict helper source, before calling. No file collection or discovery occurs
here. The selected anchor is retained metadata: Root separately collects the
actual new mapping and makes any current admission decision. A success grants
neither admission, clock, retry nor user/semantic acceptance.
"""
import copy
import hashlib
import json
import re


class PostbootTransitionError(ValueError):
    """Stable content-free refusal reason."""


UNBOUND = 'UNBOUND'
STRICT_MODULE_DESCRIPTOR = {
    'path': '/home/jericho/.cache/FRW-SOL-V3-F06-FIRST-USER-API-AFTER-CLOSED-PREINTENT-CORE-20261112/final/y_custody_delta.py',
    'bytes': 15514,
    'sha256': '8817dca2e5e8116f0b200effb61c46171fb9bd0f3dae21eaf78e485ffbdff4a6'}
STRICT_EVIDENCE_SHA256 = '2f93e07bff7397325416879da50dbd603e0128b36ca5fe6cd3e44858da9626f1'
OLD_PROOF_SHA256 = '0c4da2fe80a594a0814f1c1c10bed2407f0816642083f0de7aca5dd5d462c7df'
OLD_R106_EXPIRES_AT = 1794479034.732844
OLD_CUSTODY_SHA256 = '0d234400607a84652f78af4b138b3b2e2d0dab8fbded7870e6116d24a4d47838'
NEW_CUSTODY_SHA256 = 'b7af3d2d536dcf9a4e5d32ef1712b508de945fc5aeaf283f86632afe21eaea7d'
HISTORICAL_PREVIOUS_RECOVERY = {
    'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261112-EVENING/ROOT-RECOVERY-ACCEPTANCE.json',
    'bytes': 2597, 'sha256': 'a276de54c57dca257dc049bc453b38501f88a908472c668c8a732e969f4ac2ec'}
HISTORICAL_FULL_MANIFEST = {
    'path': '/home/jericho/.cache/FRW-ASTRA-POSTPOWER-INSTALLED207-INTEGRITY-20261112/RESULT.json',
    'bytes': 4604, 'sha256': '239ae4809df8f0225414fe988b18fc713af34a1954d4ce05167b49168eef3cac'}
HISTORICAL_PREVIOUS_BOOT = '4d38196f-04ed-4b84-bcf4-a272d4633787'
SERVICE_CONTROL_GROUPS = {
    'gateway': '/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-gateway-1b7e7667.service',
    'dashboard': '/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-dashboard.service'}
_BASIS = {'recovery_acceptance', 'persistent_runtime_delta', 'postboot_observation'}
_PERSISTENT = {'installed_product', 'databases', 'history', 'cursor', 'cooldown',
               'source', 'profile_configs', 'source_identity'}
_RUNTIME = {'gateway', 'native_readonly', 'services'}
_ALLOWED_TOP = _RUNTIME | {'custody', 'f06_mutable_boundary'}
_ALLOWED_BOUNDARY = {'gateway', 'once_sha256', 'ingress_lineage_sha256'}
_SERVICE_UNIT = {'ActiveState', 'ControlGroup', 'ControlPID', 'InvocationID',
                 'LoadState', 'MainPID', 'NRestarts', 'RuntimeMaxUSec', 'SubState', 'UnitFileState'}
_RECOVERY_KEYS = {'schema', 'at_moscow', 'operator', 'state', 'initial', 'manifest_integrity',
    'native_routing', 'providers', 'persistent_runtime_delta', 'native_PEER_channel',
    'old_Y_no_user_API_assessment', 'installed207_preserved', 'source_native17891_plugins52_byteexact',
    'DB_quickcheck_OK_messages', 'all3_full_DBmetadata_unchanged_from_Y',
    'canonical512_first_F06_run_absent', 'current_gateway', 'dashboard_pid',
    'permanent_services_infinity', 'model_inference_or_user_send_or_install_replayed',
    'original_clocks_and_R106_expiry_preserved', 'R106_current_validity', 'new_admission_or_clock'}
_DELTA_KEYS = {'schema', 'at_moscow', 'scope', 'old_proof_sha256', 'current_observation',
    'changed_top_level_keys', 'persistent_fields_unchanged', 'custody_delta',
    'mutable_boundary_changed_keys', 'before_gateway', 'after_gateway',
    'old_R106_expires_at_preserved', 'old_R106_expired_and_old_boot', 'new_admission'}
_REPEAT_RECOVERY_KEYS = {'schema', 'at_moscow', 'operator', 'state', 'boot_id', 'initial',
    'persistent_runtime_delta', 'current_observation', 'prior_full_manifest_integrity',
    'full17891_rerun', 'why_reuse_valid', 'Qwen', 'all3DBquickcheck_and_fullmetadata',
    'first_F06_user_API', 'previous_recovery', 'new_admission_clock_or_replay'}
_REPEAT_DELTA_KEYS = {'schema', 'at_moscow', 'scope', 'current_observation',
    'persistent_fields_unchanged', 'custody_delta', 'changed_top_level_keys',
    'mutable_boundary_changed_keys', 'current_gateway', 'previous_verified_boot', 'Qwen',
    'new_admission', 'current_runtime_source_plugin_hashes_verified',
    'prior_full17891_integrity_reused', 'full_native17891_rehashed_this_operation'}
STRUCTURAL_READ_SCHEMA = {
    'schema': 'frw.source.F06.Y.selected-postboot-metadata-inputs.v1',
    'input_kind': 'CALLER_AUTHENTICATED_JSON_METADATA_MAPPINGS_ONLY',
    'selected_basis_keys': sorted(_BASIS), 'selected_basis_default': UNBOUND,
    'selected_descriptor_keys': ['bytes', 'path', 'sha256'],
    'raw_recovery_and_delta_authenticated_by_root_before_call': True,
    'canonical_anchor_checked_against_selected_bytes_and_sha256': True,
    'observed_keys': sorted(_PERSISTENT | _RUNTIME | {'custody', 'f06_mutable_boundary',
                                                   'all_profile_projection_limit'}),
    'runtime_identity_keys': ['boot_id', 'pid', 'start_time'],
    'services_keys': ['dashboard', 'gateway'],
    'service_keys': ['identity', 'unit'], 'service_unit_keys': sorted(_SERVICE_UNIT),
    'native_readonly_keys': ['freshness', 'generation', 'identity', 'quiescent', 'read_only',
                             'schema', 'session_id', 'session_key'],
    'closed_variants': {
        'first_postpower': {'recovery_keys': sorted(_RECOVERY_KEYS), 'delta_keys': sorted(_DELTA_KEYS)},
        'repeat_postpower_Qwen_loading': {'recovery_keys': sorted(_REPEAT_RECOVERY_KEYS),
                                        'delta_keys': sorted(_REPEAT_DELTA_KEYS)}},
    'strict_persistent_and_custody_schema': STRICT_MODULE_DESCRIPTOR.copy(),
    'nested_references_followed': False, 'body_or_configuration_content_inputs': False,
    'filesystem_or_runtime_collection': False,
    'actual_transition_run_by_this_source_assignment': False,
}


def _need(ok, code):
    if not ok:
        raise PostbootTransitionError(code)


def _encoded(value):
    try:
        return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                           allow_nan=False) + '\n').encode('ascii')
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise PostbootTransitionError('NON_JSON_METADATA') from None


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _same(a, b):
    return _encoded(a) == _encoded(b)


def _tree(value):
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        _need(count <= 1000000 and depth <= 32, 'METADATA_TREE_BOUND')
        if type(item) is dict:
            _need(all(type(k) is str for k in item), 'NON_STRING_METADATA_KEY')
            stack.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            stack.extend((v, depth + 1) for v in item)
        else:
            _need(item is None or type(item) in (str, int, bool, float), 'NON_JSON_METADATA')
    _need(len(_encoded(value)) <= 24 * 1024**2, 'METADATA_BYTE_BOUND')


def _keys(value, keys, code):
    _need(type(value) is dict and set(value) == keys, code)


def _reference(value):
    _keys(value, {'path', 'bytes', 'sha256'}, 'SELECTED_REFERENCE_SHAPE')
    path = value['path']
    _need(type(path) is str and 1 < len(path) <= 4096 and path.startswith('/')
          and all(p not in ('', '.', '..') for p in path.split('/')[1:])
          and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in path),
          'SELECTED_REFERENCE_CANONICAL_PATH')
    _need(type(value['bytes']) is int and 0 < value['bytes'] <= 24 * 1024**2,
          'SELECTED_REFERENCE_BYTE_BOUND')
    _need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None,
          'SELECTED_REFERENCE_SHA256')


def _basis(selected_basis):
    _need(selected_basis is not None and selected_basis != UNBOUND, 'SELECTED_BASIS_UNBOUND')
    _keys(selected_basis, _BASIS, 'SELECTED_BASIS_SHAPE')
    for reference in selected_basis.values():
        _reference(reference)
    _need(len({r['path'] for r in selected_basis.values()}) == 3,
          'SELECTED_REFERENCE_PATH_ALIAS')


def _identity(value):
    _keys(value, {'pid', 'start_time', 'boot_id'}, 'RUNTIME_IDENTITY_SHAPE')
    _need(all(type(value[k]) is int and value[k] > 0 for k in ('pid', 'start_time'))
          and type(value['boot_id']) is str and re.fullmatch(
              '[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value['boot_id']) is not None,
          'RUNTIME_IDENTITY_TYPE')


def _runtime(observed):
    _need(type(observed) is dict, 'OBSERVED_SHAPE')
    _identity(observed.get('gateway'))
    gateway = observed['gateway']
    services = observed.get('services')
    _keys(services, {'gateway', 'dashboard'}, 'SERVICES_SHAPE')
    for name, service in services.items():
        _keys(service, {'unit', 'identity'}, 'SERVICE_SHAPE')
        identity, unit = service['identity'], service['unit']
        _identity(identity)
        _keys(unit, _SERVICE_UNIT, 'UNIT_SHAPE')
        _need(all(type(v) is str for v in unit.values()), 'UNIT_VALUE_TYPE')
        _need(identity['boot_id'] == gateway['boot_id'], 'SERVICE_BOOT_BINDING')
        _need(unit['MainPID'] == str(identity['pid']), 'SERVICE_PID_BINDING')
        _need(unit['ControlGroup'] == SERVICE_CONTROL_GROUPS[name], 'SERVICE_UNIT_CONTROL_GROUP')
        _need(unit['ActiveState'] == 'active' and unit['SubState'] == 'running'
              and unit['LoadState'] == 'loaded' and unit['UnitFileState'] == 'enabled'
              and unit['RuntimeMaxUSec'] == 'infinity' and unit['ControlPID'] == '0'
              and unit['NRestarts'] == '0', 'SERVICE_RUNNING_PERMANENT_CONTROL')
        _need(re.fullmatch('[0-9a-f]{32}', unit['InvocationID']) is not None
              and unit['InvocationID'] != '0' * 32, 'SERVICE_INVOCATION_NONCE')
    _need(_same(services['gateway']['identity'], gateway), 'GATEWAY_SERVICE_BINDING')
    _need(services['dashboard']['identity']['pid'] != gateway['pid'], 'SERVICE_PID_COLLISION')
    native = observed.get('native_readonly')
    _keys(native, {'schema', 'identity', 'generation', 'quiescent', 'read_only',
                   'freshness', 'session_id', 'session_key'}, 'NATIVE_READONLY_SHAPE')
    _need(_same(native['identity'], gateway), 'NATIVE_IDENTITY_BINDING')
    _need(native['schema'] == 'frw.gateway.ordinary-turn-readonly.v1'
          and native['freshness'] == 'BOUNDED3S_SOCKET_PEERCRED_MONOTONIC_KERNEL_STATE_CAS'
          and native['read_only'] is True and native['quiescent'] is True
          and type(native['generation']) is int and native['generation'] >= 0,
          'NATIVE_READONLY_QUIESCENCE_GENERATION')
    boundary = observed.get('f06_mutable_boundary')
    _need(type(boundary) is dict and type(boundary.get('B')) is dict, 'BOUNDARY_SHAPE')
    _need(_same(boundary.get('gateway'), gateway), 'ACTUAL_BOUNDARY_GATEWAY_BINDING')
    for key in ('session_id', 'session_key'):
        _need(type(native[key]) is str and 0 < len(native[key]) <= 4096
              and native[key] == boundary['B'].get(key), 'NATIVE_SESSION_BINDING')


def _timestamp(value):
    _need(type(value) is str and re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?\+03:00', value) is not None,
        'ROOT_TIMESTAMP_SHAPE')


def _root_records(recovery, delta, selected_basis, old, new, strict_module):
    _need(type(recovery) is dict and type(delta) is dict, 'ROOT_RECORD_MAPPING_TYPE')
    if set(recovery) == _RECOVERY_KEYS:
        variant = 'first_postpower'
        _keys(delta, _DELTA_KEYS, 'DELTA_SHAPE')
    elif set(recovery) == _REPEAT_RECOVERY_KEYS:
        variant = 'repeat_postpower_Qwen_loading'
        _keys(delta, _REPEAT_DELTA_KEYS, 'DELTA_SHAPE')
    else:
        raise PostbootTransitionError('RECOVERY_CLOSED_VARIANT_SHAPE')
    _timestamp(recovery['at_moscow'])
    _timestamp(delta['at_moscow'])
    _need(type(delta['scope']) is str and 0 < len(delta['scope']) <= 4096, 'DELTA_SCOPE_TYPE')
    _reference(recovery['initial'])
    _reference(recovery['persistent_runtime_delta'])
    _reference(delta['current_observation'])
    _need(recovery['schema'] == 'friday.root.postpower.recovery-acceptance.v1'
          and recovery['operator'] == 'Root', 'ROOT_RECOVERY_SCHEMA_OPERATOR')
    _need(delta['schema'] == 'friday.root.postpower.observed-delta.v1'
          and delta['new_admission'] is False, 'DELTA_NOT_ADMISSION')
    _need(_same(delta['current_observation'], selected_basis['postboot_observation'])
          and _same(recovery['persistent_runtime_delta'], selected_basis['persistent_runtime_delta']),
          'ROOT_SELECTED_DESCRIPTOR_BINDING')
    evidence = strict_module.expected_evidence()
    _need(_digest(evidence) == STRICT_EVIDENCE_SHA256, 'STRICT_EVIDENCE_PIN')
    _need(evidence['consumer_born_and_closed'] is True
          and evidence['BotAPI_client_constructed'] is True
          and evidence['canonical_run_created'] is False
          and evidence['raw_status'] == 'REFUSED_OR_UNKNOWN'
          and evidence['original_nested_exception_retained'] is False
          and evidence['ordinary_semantic_or_F06_acceptance'] is False
          and evidence['automatic_retry_or_followup_authorized'] is False,
          'OLD_Y_ORIGINAL_REFUSAL_PRESERVED')
    _need(strict_module.OLD_CUSTODY_SHA256 == OLD_CUSTODY_SHA256
          and strict_module.NEW_CUSTODY_SHA256 == NEW_CUSTODY_SHA256, 'STRICT_CUSTODY_PAIR_PIN')
    if variant == 'first_postpower':
        for key in ('manifest_integrity', 'native_routing', 'providers',
                    'native_PEER_channel', 'old_Y_no_user_API_assessment'):
            _reference(recovery[key])
        _need(recovery['state'] == 'ACCEPT_INSTALLED_SOURCE_DATA_READONLY_RUNTIME_AND_DEPENDENCY_RECOVERY_NOT_USER_TEST_ADMISSION',
              'ROOT_RECOVERY_NOT_ADMISSION')
        _need(all(recovery[k] is True for k in ('installed207_preserved',
            'source_native17891_plugins52_byteexact', 'all3_full_DBmetadata_unchanged_from_Y',
            'canonical512_first_F06_run_absent', 'permanent_services_infinity',
            'original_clocks_and_R106_expiry_preserved'))
            and _same(recovery['DB_quickcheck_OK_messages'], [30, 196, 5510])
            and recovery['model_inference_or_user_send_or_install_replayed'] is False
            and recovery['new_admission_or_clock'] is False
            and recovery['R106_current_validity'] == 'EXPIRED_AND_DIFFERENT_BOOT_CANNOT_ADMIT',
            'ROOT_RECOVERY_PRESERVATION')
        _need(delta['old_R106_expired_and_old_boot'] is True
              and _same(delta['old_R106_expires_at_preserved'], OLD_R106_EXPIRES_AT),
              'DELTA_R106_PRESERVED')
        _need(delta['old_proof_sha256'] == OLD_PROOF_SHA256
              and _same(delta['before_gateway'], old['gateway'])
              and _same(delta['after_gateway'], new['gateway'])
              and _same(recovery['current_gateway'], new['gateway'])
              and type(recovery['dashboard_pid']) is int
              and recovery['dashboard_pid'] == new['services']['dashboard']['identity']['pid'],
              'ROOT_OLD_PROOF_OR_BOOT_BINDING')
        _need(_same(recovery['old_Y_no_user_API_assessment'], evidence['saved_assessment']),
              'OLD_Y_SAVED_ASSESSMENT_BINDING')
    else:
        for key in ('current_observation', 'prior_full_manifest_integrity', 'previous_recovery'):
            _reference(recovery[key])
        _need(recovery['state'] == 'ACCEPT_POSTBOOT_SOURCE_PERSISTENT_DATA_AND_READONLY_RUNTIME_BASIS_QWEN_LOADING_NOT_USER_TEST_ADMISSION'
              and recovery['new_admission_clock_or_replay'] is False
              and recovery['first_F06_user_API'] == 'NOT_RUN'
              and recovery['Qwen'] == 'OWNER_REPORT_LOADING_NO_LIVE_INFERENCE_ADMISSION'
              and delta['Qwen'] == 'OWNER_REPORT_LOADING_NO_INFERENCE_ADMISSION',
              'ROOT_REPEAT_NOT_ADMISSION_QWEN_LOADING')
        _need(_same(recovery['previous_recovery'], HISTORICAL_PREVIOUS_RECOVERY)
              and _same(recovery['prior_full_manifest_integrity'], HISTORICAL_FULL_MANIFEST)
              and delta['previous_verified_boot'] == HISTORICAL_PREVIOUS_BOOT,
              'ROOT_REPEAT_HISTORICAL_PROVENANCE')
        _need(recovery['full17891_rerun'] is False
              and delta['full_native17891_rehashed_this_operation'] is False
              and delta['current_runtime_source_plugin_hashes_verified'] is True
              and recovery['why_reuse_valid'] == 'No installed-source writes since full17891/plugin52 verification; canonical4 and current executing14/runtime+52plugin hashes rechecked through unchanged checker'
              and delta['prior_full17891_integrity_reused'] == HISTORICAL_FULL_MANIFEST['sha256'] + '; no installed source writes since'
              and recovery['all3DBquickcheck_and_fullmetadata'] == 'OK_30_196_5510_leasespending0',
              'ROOT_REPEAT_FULL_NATIVE_REUSE_NOT_FRESH_FULL_REHASH')
        _need(_same(recovery['current_observation'], selected_basis['postboot_observation'])
              and recovery['boot_id'] == new['gateway']['boot_id']
              and recovery['boot_id'] != delta['previous_verified_boot']
              and _same(delta['current_gateway'], new['gateway']),
              'ROOT_REPEAT_CURRENT_BOOT_BINDING')
    _keys(delta['persistent_fields_unchanged'], _PERSISTENT, 'DELTA_PERSISTENT_SHAPE')
    _need(all(v is True for v in delta['persistent_fields_unchanged'].values()),
          'DELTA_PERSISTENT_NOT_UNCHANGED')
    top_changed = sorted(k for k in set(old) | set(new)
                         if k not in old or k not in new or not _same(old[k], new[k]))
    before, after = old['f06_mutable_boundary'], new['f06_mutable_boundary']
    boundary_changed = sorted(k for k in set(before) | set(after)
                              if k not in before or k not in after or not _same(before[k], after[k]))
    _need(top_changed == sorted(_ALLOWED_TOP)
          and _same(delta['changed_top_level_keys'], top_changed)
          and boundary_changed == sorted(_ALLOWED_BOUNDARY)
          and _same(delta['mutable_boundary_changed_keys'], boundary_changed)
          and _same(delta['custody_delta'], {'added': [strict_module.LEAF], 'removed': [], 'changed': []}),
          'DELTA_EXACT_COMPUTED_CHANGE_SET')
    return evidence, variant


def _changed_paths(old, new, path=''):
    if type(old) is dict and type(new) is dict and set(old) == set(new):
        result = {}
        for key in sorted(old):
            result.update(_changed_paths(old[key], new[key], path + ('.' if path else '') + key))
        return result
    return {} if _same(old, new) else {path: {'old': copy.deepcopy(old), 'new': copy.deepcopy(new)}}


def validate_postboot_y_transition(old_observed, new_observed, *,
        original_observed_sha256, selected_basis=UNBOUND, postboot_anchor, recovery, delta, strict_module):
    """Validate actual runtime and Root basis, then strict custody on a COPY.

    selected_basis has no discovery/default fallback. Root authenticates its three
    raw descriptors before this call and binds them to source/component/bulk and
    current admission selection. Only the anchor has canonical raw JSON encoding;
    recovery/delta may retain their original raw pretty encoding. Test fixtures
    may externally alter historical pins on isolated imported instances only.
    """
    for value in (old_observed, new_observed, selected_basis, postboot_anchor, recovery, delta):
        _tree(value)
    _basis(selected_basis)
    _need(type(original_observed_sha256) is str
          and re.fullmatch('[0-9a-f]{64}', original_observed_sha256) is not None
          and _digest(old_observed) == original_observed_sha256, 'ORIGINAL_OBSERVED_DIGEST_MISMATCH')
    _runtime(old_observed)
    _runtime(new_observed)
    _need(old_observed['gateway']['boot_id'] != new_observed['gateway']['boot_id'],
          'POSTBOOT_REQUIRES_DISTINCT_BOOT')
    anchor_bytes = _encoded(postboot_anchor)
    _need(len(anchor_bytes) == selected_basis['postboot_observation']['bytes']
          and hashlib.sha256(anchor_bytes).hexdigest() == selected_basis['postboot_observation']['sha256'],
          'SELECTED_POSTBOOT_ANCHOR_BYTES_OR_SHA256')
    _need(_same(new_observed, postboot_anchor), 'FRESH_OBSERVATION_NOT_EXACT_ROOT_ANCHOR')
    evidence, variant = _root_records(recovery, delta, selected_basis, old_observed, new_observed, strict_module)
    old_native, new_native = old_observed['native_readonly'], new_observed['native_readonly']
    for field in set(old_native) - {'identity', 'generation'}:
        _need(_same(old_native[field], new_native[field]), 'NATIVE_STABLE_FIELD_CHANGED')
    for name in ('gateway', 'dashboard'):
        old_unit, new_unit = old_observed['services'][name]['unit'], new_observed['services'][name]['unit']
        for field in _SERVICE_UNIT - {'MainPID', 'InvocationID'}:
            _need(_same(old_unit[field], new_unit[field]), 'STABLE_UNIT_CONTROL_CHANGED')
        _need(old_unit['InvocationID'] != new_unit['InvocationID'], 'SERVICE_INVOCATION_NOT_NEW_BOOT')
    # Only this declared comparison copy is normalized. Actual mappings stay exact.
    comparison = copy.deepcopy(new_observed)
    for field in _RUNTIME:
        comparison[field] = copy.deepcopy(old_observed[field])
    comparison['f06_mutable_boundary']['gateway'] = copy.deepcopy(old_observed['f06_mutable_boundary']['gateway'])
    strict = strict_module.validate_y_custody_delta(old_observed, comparison,
        original_observed_sha256=original_observed_sha256, evidence=evidence)
    return {
        'schema': 'frw.source.F06.Y.selected-postboot-custody-transition.v1',
        'metadata_validation_only': True, 'admission': False,
        'filesystem_observation_performed': False,
        'actual_original_observed_sha256': _digest(old_observed),
        'actual_new_observed_sha256': _digest(new_observed),
        'actual_postboot_anchor_sha256': _digest(postboot_anchor),
        'selected_basis': copy.deepcopy(selected_basis),
        'root_recovery_variant': variant,
        'provider_readiness': 'NOT_GRANTED',
        'full_native17891_current_operation_rehash_asserted': False,
        'native_integrity_basis': ('ROOT_BYTEEXACT_ASSERTION_AND_REFERENCED_MANIFEST'
            if variant == 'first_postpower' else 'PRIOR_FULL17891_REUSED_CURRENT_RUNTIME_AND_PLUGIN_HASHES_RECHECKED'),
        'repeat_full_native_integrity_reused_not_freshly_rehashed': variant == 'repeat_postpower_Qwen_loading',
        'historical_original_Y_proof_sha256': OLD_PROOF_SHA256,
        'historical_Y_and_R106_basis': ('DIRECT_RECOVERY_AND_DELTA_FIELDS'
            if variant == 'first_postpower' else 'EXACT_PREVIOUS_RECOVERY_PROVENANCE_AND_ROOT_AUTHENTICATED_ORIGINAL_Y'),
        'strict_module_descriptor': copy.deepcopy(STRICT_MODULE_DESCRIPTOR),
        'root_must_authenticate_raw_descriptors_original_Y_and_strict_module': True,
        'root_must_bind_explicit_basis_to_current_selection_source_component_and_bulk': True,
        'root_must_collect_fresh_observation_and_separate_current_admission': True,
        'retained_anchor_is_historical_not_admission': True,
        'old_R106_expiry_preserved_not_reopened': OLD_R106_EXPIRES_AT,
        'old_Y_original_refusal_and_missing_nested_trace_preserved': True,
        'normalized_comparison_copy_only': True,
        'normalized_comparison_copy_sha256': _digest(comparison),
        'normalized_comparison_is_not_actual_proof': True,
        'normalized_paths': ['gateway', 'native_readonly', 'services', 'f06_mutable_boundary.gateway'],
        'actual_runtime_field_map': _changed_paths(
            {k: old_observed[k] for k in _RUNTIME}, {k: new_observed[k] for k in _RUNTIME}),
        'strict_custody_map': copy.deepcopy(strict['derived_field_map']),
        'all3_full_database_metadata_unchanged': strict['all3_full_database_metadata_unchanged'],
        'new_proof_must_always_contain_actual_new_observed': True,
        'CFB_and_unrelated_checks_must_remain_in_root_caller': True,
    }
