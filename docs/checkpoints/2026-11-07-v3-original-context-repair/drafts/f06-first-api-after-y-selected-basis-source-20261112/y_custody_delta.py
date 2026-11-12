"""Pure metadata transition validation. No filesystem collector or live grant.

Root supplies metadata-only mappings obtained at its own permitted boundary.
This module never opens diagnostic, proof, source, configuration or DB bodies.
An exact Y success remains a metadata judgement, never API/semantic acceptance.
"""
import copy
import hashlib
import json
import re


class CustodyDeltaError(ValueError):
    """A stable, content-free reason code; caller material is not interpolated."""


def _need(ok, code):
    if not ok:
        raise CustodyDeltaError(code)


def _encoded(value):
    try:
        return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                           allow_nan=False) + '\n').encode('ascii')
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise CustodyDeltaError('NON_JSON_METADATA') from None


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _same(a, b):
    return _encoded(a) == _encoded(b)


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _json_tree(value):
    stack, nodes = [(value, 0)], 0
    while stack:
        v, depth = stack.pop()
        nodes += 1
        _need(nodes <= 1000000 and depth <= 32, 'METADATA_TREE_BOUND')
        if type(v) is dict:
            _need(all(type(k) is str for k in v), 'NON_STRING_METADATA_KEY')
            stack.extend((x, depth + 1) for x in v.values())
        elif type(v) is list:
            stack.extend((x, depth + 1) for x in v)
        else:
            _need(v is None or type(v) in (str, int, bool, float), 'NON_JSON_METADATA')
    _need(len(_encoded(value)) <= 24 * 1024**2, 'METADATA_BYTE_BOUND')


_BASE = '/home/jericho/.cache/FRW-ASTRA-V3-F06-T29-FIRST-CONSUMER-ROOT-20261112/'
LEAF = 'main-exception-run-f06-first-docx-wrong-read-20261112-r1.json'
OLD_CUSTODY_SHA256 = '0d234400607a84652f78af4b138b3b2e2d0dab8fbded7870e6116d24a4d47838'
NEW_CUSTODY_SHA256 = 'b7af3d2d536dcf9a4e5d32ef1712b508de945fc5aeaf283f86632afe21eaea7d'
_IDENTITY = {'device', 'inode', 'uid', 'gid', 'mode', 'nlink', 'bytes', 'mtime_ns', 'ctime_ns'}
_OBSERVED = {'installed_product', 'services', 'gateway', 'native_readonly', 'databases',
             'history', 'cursor', 'cooldown', 'custody', 'source', 'profile_configs',
             'source_identity', 'f06_mutable_boundary', 'all_profile_projection_limit'}
_BOUNDARY = {'history_manifest_sha256', 'cursor_sha256', 'native_boundary_sha256',
             'once_sha256', 'ingress_lineage_sha256', 'gateway', 'B', 'phase_unconsumed',
             'uploads_this_operation', 'producer_calls', 'restarts'}
_DERIVED = {'once_sha256', 'ingress_lineage_sha256'}
_EXPECTED = dict(source_layers=207, project_files=495, native_files=17891,
                 plugin_files=52, base_source_files=17730,
                 source_receipt_sha256='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b',
                 input_sha256='c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838')


def _reference(path, size, sha):
    return dict(path=path, bytes=size, sha256=sha)


def expected_evidence():
    """Return original metadata descriptors; this does not collect or authenticate files.

    These pins describe retained originals, not new caller/adapter source revisions.
    Root validates any successor source and semantic/lineage review separately.
    """
    return dict(
        closure=_reference(_BASE + 'PREINTENT-GUARD-REFUSAL-CLOSURE.json', 2140,
            '3ba160ed4c5955421fe5dc5cc7e422d6e9fadc2793aa1efe7b1aebaa1756a88d'),
        custody_delta=_reference(_BASE + 'POST-REFUSAL-CUSTODY-DELTA.json', 951,
            '9c15baad29be8c9dc183a3d6560f14e036d646d847e8cd4f0dcf4c1c1081114b'),
        saved_assessment=_reference('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-Y-PREINTENT-REFUSAL-ROOT-SAVED-ASSESSMENT-20261112.json', 2084,
            '8be2ca0e659c8ce4e51aa72c21c94f2de4208ccf8c139da910e2043db12715e2'),
        independent_review=_reference('/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-Y-PREINTENT-CLOSURE-20261112/REVIEW.json', 17730,
            '581a9a080b2acc96cb00a5a4a5a157ceb92332be43bd315507e065f7aa3dd4e7'),
        independent_result=_reference('/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-Y-PREINTENT-CLOSURE-20261112/RESULT.json', 1232,
            '1431470540ef6cd0b090237526ca151639ceeba3185c318c2e566e666969f5d9'),
        observed_shape_source=_reference('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112/candidate/first/current207.py', 37442,
            '63863895d3d205c956eb272b5aa448648783a827eaaedbe8d5cf49b3fcbd08c3'),
        diagnostic=_reference('/home/jericho/.local/share/friday-telegram-bot-test/' + LEAF, 444,
            'd2561293b682a661412852abb8f8f6fed74099a45977c82b239cb984e5895def'),
        old_custody_sha256=OLD_CUSTODY_SHA256, current_custody_sha256=NEW_CUSTODY_SHA256,
        raw_status='REFUSED_OR_UNKNOWN', consumer_born_and_closed=True,
        BotAPI_client_constructed=True, canonical_run_created=False,
        nested_cause_classification='SOURCE_DERIVED_REPRODUCTION_NOT_ORIGINAL_RETAINED_EXCEPTION',
        original_nested_exception_retained=False, ordinary_semantic_or_F06_acceptance=False,
        automatic_retry_or_followup_authorized=False,
        old_root_private_proofs_or_clocks_updated=False, new_clock_or_grant_or_retry=False)


def _identity(value):
    _need(type(value) is dict and set(value) == _IDENTITY, 'CUSTODY_IDENTITY_SHAPE')
    _need(all(type(v) is int and v >= 0 for v in value.values()), 'CUSTODY_IDENTITY_TYPE')
    _need(value['mode'] <= 0o7777 and not value['mode'] & 0o002 and value['nlink'] >= 1,
          'CUSTODY_IDENTITY_UNSAFE')


def _custody(value):
    _need(type(value) is dict and set(value) == {'records', 'sha256', 'contents_read'}
          and value['contents_read'] is False and _sha(value['sha256']), 'CUSTODY_SHAPE')
    records = value['records']
    _need(type(records) is list and 0 < len(records) <= 50000, 'CUSTODY_RECORD_BOUND')
    names, owner = [], None
    for record in records:
        _need(type(record) is list and len(record) == 2, 'CUSTODY_RECORD_SHAPE')
        name, identity = record
        _need(type(name) is str and 0 < len(name) <= 4096
              and all(p not in ('', '.', '..') for p in name.split('/'))
              and not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in name)
              and name.split('/')[0] != 'runs', 'CUSTODY_RELATIVE_NAME')
        _identity(identity)
        owner = identity['uid'] if owner is None else owner
        _need(identity['uid'] == owner, 'CUSTODY_OWNER_MISMATCH')
        names.append(name)
    _need(len(set(names)) == len(names), 'CUSTODY_DUPLICATE_LEAF')
    _need(names == sorted(names, key=lambda name: tuple(name.split('/'))), 'CUSTODY_ORDER')
    _need(_digest(records) == value['sha256'], 'CUSTODY_HASH_MISMATCH')
    return dict(zip(names, records))


def _database_metadata(value):
    _need(type(value) is dict and set(value) == {'default', 'dest', 'tester'}, 'ALL3_DB_SHAPE')
    fields = {'path', 'identity', 'messages', 'max_message_id', 'sessions', 'leases',
              'all_origin_pending_delegations', 'session_metadata_sha256',
              'message_metadata_sha256', 'pending_message_entries'}
    stable = {'device', 'inode', 'uid', 'gid', 'mode', 'nlink'}
    for label, db in value.items():
        _need(type(db) is dict and set(db) == fields | ({'principal'} if label == 'tester' else set()),
              'DB_FULL_METADATA_SHAPE')
        _need(type(db['path']) is str and db['path'].startswith('/'), 'DB_PATH')
        _need(type(db['identity']) is dict and set(db['identity']) == stable
              and all(type(x) is int and x >= 0 for x in db['identity'].values())
              and db['identity']['nlink'] == 1 and not db['identity']['mode'] & 0o002,
              'DB_IDENTITY_SHAPE')
        _need(type(db['messages']) is int and 0 <= db['messages'] <= 100000
              and type(db['sessions']) is int and 0 <= db['sessions'] <= 10000, 'DB_COUNT_BOUND')
        _need(db['max_message_id'] is None if db['messages'] == 0 else
              type(db['max_message_id']) is int and db['max_message_id'] >= 0, 'DB_MAX_ID')
        _need(all(type(db[k]) is int and db[k] == 0 for k in
                  ('leases', 'all_origin_pending_delegations', 'pending_message_entries')), 'DB_PENDING')
        _need(_sha(db['session_metadata_sha256']) and _sha(db['message_metadata_sha256']), 'DB_METADATA_HASH')
        if label == 'tester':
            _need(type(db['principal']) is dict and set(db['principal']) ==
                  {'id', 'source', 'user_id', 'chat_id', 'chat_type', 'session_key', 'profile_name', 'transport_profile'},
                  'DB_PRINCIPAL_SHAPE')


def _ingress(observed):
    return _digest(dict(source=observed['source'], databases=observed['databases'],
                        custody=observed['custody']['sha256']))


def _observation(value):
    _need(type(value) is dict and set(value) == _OBSERVED, 'OBSERVED_SHAPE')
    _need(_same(value['installed_product'], _EXPECTED), 'INSTALLED207_METADATA')
    _database_metadata(value['databases'])
    boundary = value['f06_mutable_boundary']
    _need(type(boundary) is dict and set(boundary) == _BOUNDARY, 'BOUNDARY_SHAPE')
    _need(all(_sha(boundary[k]) for k in ('history_manifest_sha256', 'cursor_sha256',
          'native_boundary_sha256', 'once_sha256', 'ingress_lineage_sha256')), 'BOUNDARY_HASH_TYPE')
    _need(boundary['phase_unconsumed'] is True and all(type(boundary[k]) is int and boundary[k] == n
          for k, n in (('uploads_this_operation', 1), ('producer_calls', 0), ('restarts', 0))), 'BOUNDARY_COUNTERS')
    _need(_same(boundary['gateway'], value['gateway']), 'GATEWAY_BINDING')
    _need(boundary['native_boundary_sha256'] == _digest(value['databases']), 'NATIVE_DB_BINDING')
    _need(boundary['once_sha256'] == value['custody']['sha256'], 'ONCE_CUSTODY_BINDING')
    _need(boundary['ingress_lineage_sha256'] == _ingress(value), 'INGRESS_DERIVATION')
    history = value['history']
    _need(type(history) is dict and set(history) == {'records', 'run_ids', 'manifest_sha256'}
          and type(history['records']) is list and len(history['records']) == 512
          and type(history['run_ids']) is list and len(history['run_ids']) == 512, 'HISTORY_METADATA_SHAPE')
    _need(history['manifest_sha256'] == _digest(history['records']) == boundary['history_manifest_sha256'],
          'HISTORY_MANIFEST_BINDING')
    _need(type(value['cursor']) is dict and value['cursor'].get('sha256') == boundary['cursor_sha256'],
          'CURSOR_BINDING')
    _need(value['all_profile_projection_limit'] == 'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED',
          'ALL_PROFILE_LIMIT')


def _validate(old_observed, new_observed, evidence, original_observed_sha256, expected_old, expected_new, synthetic):
    for value in (old_observed, new_observed, evidence):
        _json_tree(value)
    _need(_same(evidence, expected_evidence()), 'ORIGINAL_EVIDENCE_BINDING_CHANGED')
    _need(_sha(original_observed_sha256) and _digest(old_observed) == original_observed_sha256,
          'ORIGINAL_OBSERVED_DIGEST_MISMATCH')
    old_entries = _custody(old_observed.get('custody') if type(old_observed) is dict else None)
    new_entries = _custody(new_observed.get('custody') if type(new_observed) is dict else None)
    _need(old_observed['custody']['sha256'] == expected_old
          and new_observed['custody']['sha256'] == expected_new, 'RECORDED_CUSTODY_HASH_PAIR')
    _need(LEAF not in old_entries and set(new_entries) - set(old_entries) == {LEAF}, 'EXACT_ADDED_DIAGNOSTIC_ONLY')
    _need(not set(old_entries) - set(new_entries), 'REMOVED_CUSTODY_LEAF')
    _need(_same([r for r in new_observed['custody']['records'] if r[0] != LEAF],
                old_observed['custody']['records']), 'CHANGED_CUSTODY_METADATA')
    added = new_entries[LEAF][1]
    _need(added['bytes'] == evidence['diagnostic']['bytes'] and added['mode'] == 0o600
          and added['nlink'] == 1 and added['uid'] == next(iter(old_entries.values()))[1]['uid'],
          'DIAGNOSTIC_IDENTITY_DESCRIPTOR')
    _observation(old_observed)
    _observation(new_observed)
    for field in _OBSERVED - {'custody', 'f06_mutable_boundary'}:
        _need(_same(old_observed[field], new_observed[field]), 'UNRELATED_OBSERVATION_CHANGED')
    old_b, new_b = old_observed['f06_mutable_boundary'], new_observed['f06_mutable_boundary']
    for field in _BOUNDARY - _DERIVED:
        _need(_same(old_b[field], new_b[field]), 'UNRELATED_BOUNDARY_CHANGED')
    return dict(schema='frw.source.F06.Y.pure-custody-delta-validation.v1',
        metadata_validation_only=True, synthetic_only=synthetic, admission=False,
        original_snapshot_path=_BASE + 'work/ROOT-FRESH-CURRENT-PROOF.json',
        original_observed_sha256=original_observed_sha256,
        new_observed_sha256=_digest(new_observed),
        root_must_authenticate_original_observation_digest=True,
        filesystem_observation_performed=False, diagnostic_content_read=False,
        source_semantic_or_lineage_successor_generated=False,
        added=[LEAF], removed=[], changed=[], all3_full_database_metadata_unchanged=True,
        original_evidence=copy.deepcopy(evidence),
        derived_field_map={
            'custody.records': 'old records plus exactly original protected diagnostic identity',
            'custody.sha256': dict(old=expected_old, new=expected_new, derivation='SHA256(current207.encoded(custody.records))'),
            'f06_mutable_boundary.once_sha256': dict(old=old_b['once_sha256'], new=new_b['once_sha256'], derivation='custody.sha256'),
            'f06_mutable_boundary.ingress_lineage_sha256': dict(old=old_b['ingress_lineage_sha256'], new=new_b['ingress_lineage_sha256'],
                derivation='SHA256(current207.encoded({source,databases,custody:custody.sha256}))')})


def validate_y_custody_delta(old_observed, new_observed, *, original_observed_sha256, evidence):
    """Validate the exact recorded Y transition from caller-supplied metadata.

    evidence must equal expected_evidence(), preserving original source review pins
    and raw UNKNOWN. It authenticates no files; Root must bind the mappings to its
    own current, safely collected observations and descriptor readback. Root must
    authenticate original_observed_sha256 against the unchanged original snapshot;
    it is not inferred from the custody-only saved hash. An actual
    positive was intentionally not run by this source-only implementation task.
    """
    return _validate(old_observed, new_observed, evidence, original_observed_sha256,
                     OLD_CUSTODY_SHA256, NEW_CUSTODY_SHA256, False)


def validate_synthetic_transition_for_tests(old_observed, new_observed, *,
                                             synthetic_old_sha256, synthetic_new_sha256,
                                             original_observed_sha256, evidence):
    """Explicit test-only core entry point; result is always synthetic_only=True."""
    _need(_sha(synthetic_old_sha256) and _sha(synthetic_new_sha256)
          and synthetic_old_sha256 != OLD_CUSTODY_SHA256
          and synthetic_new_sha256 != NEW_CUSTODY_SHA256, 'SYNTHETIC_HASH_PAIR_REQUIRED')
    return _validate(old_observed, new_observed, evidence, original_observed_sha256,
                     synthetic_old_sha256, synthetic_new_sha256, True)
