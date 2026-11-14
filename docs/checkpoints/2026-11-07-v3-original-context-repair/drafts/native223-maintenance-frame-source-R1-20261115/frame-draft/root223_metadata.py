'Typed actual222 -> prospective223 metadata. Import is inert.\n\nFinite cached source/history never confers current authority. Root must provide\nnew exact acceptance, mutable readback and bound-input records. Only an explicit\nfuture load_actor_binding call reads current leaves, time or boot identity.\n'
from pathlib import Path
import copy
import datetime
import hashlib
import json
import os
import stat
import time
import types

B = Path(__file__).parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
ACTUAL222_COMMIT = '199405849b62edb926a234f119b5a62d2adcf3b5'
PRODUCT223_COMMIT = 'UNBOUND_NATIVE223_PRODUCT223_COMMIT'
LAYER = 'ordinary-f04-owned-ingress-stop-terminal-after-source222'
PRIVATE_HELPER = 'UNBOUND_NATIVE223_PRIVATE_HELPER'
PUBLIC_HELPER = 'UNBOUND_NATIVE223_PUBLIC_HELPER'
BEFORE_HELPER = '06fd2ab2ab96f9bced79a6d76a74fdc3f6886d468dcd8525a28422d89213ad43'
PROFILE_SOURCE_JOIN = {
    'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/PROFILE-SOURCE-JOIN.json',
    'sha256': '9d1c1e6fdaadc68f07eba2425007071cc14bae4c80af203f9b37d54587e53746',
}
PUBLIC_CHECKER_PATH = 'docs/checkpoints/2026-11-07-v3-original-context-repair/m09-genuine-summary-carrier-root-consumer.py'
SNAPSHOT_TRUE_FIELDS = (
    'source_authority_verified', 'public_source_pins_verified',
    'operational_source_pins_verified', 'profile_routing_verified',
    'process_environment_verified', 'ordinary_readonly_quiescent',
    'all_three_user_db_zero_leases', 'stop_cooldown_clear',
    'sole_heavy_slot_clear', 'no_current_maintenance', 'cancellation_clear',
    'resources_sufficient', 'all_profile_owned_work_quiescent',
    'current_request_unconsumed', 'old_effects_not_replayed',
    'native_pm_selected_python_verified',
    'product_services_healthy_infinite_lifetime',
    'unchanged_bank_profile_evidence_reusable', 'known_limits_retained',
    'current_resume_turn_and_delivery_conflict_free',
)
KNOWN_LIMITS = dict(native_canonical_unknown=3, structural_unresolved=45,
                    R104_semantic_fail=True, default_workers_ready_accepted=False,
                    DSH_A0_deferred=True)
_DATA = None
_MANIFEST_REF = None
FIXED = {}
P = C = S = SPEC = None
EXPECTED_RECEIPT = BEFORE_RECEIPT = PREVIOUS_INPUT = None


class InvalidBinding(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise InvalidBinding(reason)


def digest(value, length=64):
    return (type(value) is str and len(value) == length and
            all(c in '0123456789abcdef' for c in value))


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def owned(path):
    p = Path(path)
    require(p.is_absolute() and '..' not in p.parts, 'absolute_exact_path_required')
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and
            s.st_nlink == 1 and not any(q.is_symlink() for q in (p, *p.parents)),
            'owned_regular_singlelink_required')
    return p


def raw_reference(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'} and
            type(ref['path']) is str and digest(ref['sha256']),
            'exact_reference_required')
    p = owned(ref['path'])
    before = p.lstat()
    raw = p.read_bytes()
    after = p.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode,
                          s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(after) and
            hashlib.sha256(raw).hexdigest() == ref['sha256'],
            'reference_identity_or_bytes_changed')
    return raw


def reference(path):
    p = owned(path)
    result = dict(path=str(p), sha256=sha(p))
    raw_reference(result)
    return result


def readref(ref):
    return json.loads(raw_reference(ref))


def clean_reference(ref):
    return {k: ref[k] for k in ('path', 'sha256')}


def read_sized_source_ref(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'} and
            type(ref['bytes']) is int and ref['bytes'] > 0,
            'exact_sized_source_ref_required')
    raw = source_raw(ref)
    require(len(raw) == ref['bytes'], 'source_ref_size_changed')
    return json.loads(raw)


def source_module(name, raw):
    require(name == 'root223_data', 'only_exact223_data_module_allowed')
    path = B / (name + '.py')
    module = types.ModuleType('Root223_' + name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def require_bound_data(external_manifest_sha256):
    global _DATA, _MANIFEST_REF, FIXED, P, C, S, SPEC
    global EXPECTED_RECEIPT, BEFORE_RECEIPT, PREVIOUS_INPUT
    require(digest(external_manifest_sha256), 'external_manifest_sha256_required')
    # Authenticate executable dependency before importing it. Data.load repeats
    # this pin and verifies its own finite dependencies and descriptor.
    manifest_ref = dict(path=str(B/'SOURCE-PINS.json'), sha256=external_manifest_sha256)
    manifest = readref(manifest_ref)
    require(manifest['schema'] == 'frw.root223.coherent-after-actual222-source-pins.v1'
            and manifest['runtime_grant'] is False, 'exact_inert223_manifest_required')
    module_raw = {}
    for name in ('root223_data.py', 'root223_metadata.py'):
        pin = manifest['source_refs'].get(str(B/name))
        require(digest(pin), 'exact_source_pinned_module_required:' + name)
        module_raw[name] = raw_reference(dict(path=str(B/name), sha256=pin))
    data = source_module('root223_data', module_raw['root223_data.py']).load(
        external_manifest_sha256, frame=B)
    _DATA = data
    _MANIFEST_REF = manifest_ref
    FIXED = copy.deepcopy(data['fixed'])
    roots = data['descriptor']['project_roots']
    P, C, S = (Path(roots[k]) for k in ('previous', 'private', 'public'))
    SPEC = Path(data['native_spec']['path'])
    EXPECTED_RECEIPT = data['static_binding']['prospective_receipt_sha256']
    actual = supplied_predecessor()
    BEFORE_RECEIPT = actual['authenticated_row_sha256']['receipt']
    PREVIOUS_INPUT = actual['current_input']['sha256']
    try:
        validate_candidate()
    except Exception:
        _DATA = None
        _MANIFEST_REF = None
        raise
    return copy.deepcopy(data)


def bound_data():
    require(_DATA is not None and _MANIFEST_REF is not None,
            'Root223_external_source_pinned_data_required')
    return _DATA


def source_raw(ref):
    require(type(ref) is dict and set(ref) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'}),
            'exact_static_source_ref_required')
    require(bound_data()['source_refs'].get(ref['path']) == ref['sha256'],
            'static_source_ref_must_be_in_external_manifest')
    raw = raw_reference(clean_reference(ref))
    require('bytes' not in ref or type(ref['bytes']) is int and len(raw) == ref['bytes'],
            'static_source_size_changed')
    return raw


def source_readref(ref):
    return json.loads(source_raw(ref))


def supplied_predecessor():
    actual = copy.deepcopy(bound_data()['predecessor'])
    require(actual['complete_eight'] is True and actual['source_commit'] == ACTUAL222_COMMIT
            and actual['installed'] == dict(base=17730, layers=222, native=17893,
                                            plugins=52, project=525),
            'complete_genuine_actual222_predecessor_required')
    require(actual['values']['input']['project_files']['scripts/friday_ordinary_install.py']
            == BEFORE_HELPER, 'real_old_private525_helper_required')
    return actual


def validate_predecessor_record(record):
    actual = supplied_predecessor()
    require(record == {k: v for k, v in actual.items() if k != 'values'},
            'exact_genuine_closed222_predecessor_record_required')
    return actual['request']


def actual_predecessor():
    return supplied_predecessor()['request']


def native_after_path(name):
    rows = bound_data()['descriptor']['native_after']
    require(name in rows, 'unknown_native_after_source_path')
    return Path(rows[name]['path'])


def validate_candidate():
    data = bound_data()
    binding, spec = data['static_binding'], data['native_spec_value']
    require(binding['schema'] == 'frw.root223.exact-static-frame-binding.v1' and
            binding['source_only'] is True and binding['current_admission'] is False
            and binding['execution_grant'] is False and binding['once'] == 'UNBOUND_ROOT'
            and binding['clock'] == 'UNBOUND_ROOT', 'static_source_is_never_current_authority')
    require(spec['schema'] == 'frw.f04223.pair-spec.v1' and spec['source_only'] is True
            and spec['current_authority'] is False and spec['execution_grant'] is False
            and spec['installed223'] is False and spec['layer'] == LAYER,
            'exact_source_only223_spec_required')
    expected_counts=dict(added=binding['native_additions'],after_layers=223,after_native=binding['after_native'],after_project=527,base=17730,before_layers=222,before_native=17893,before_project=525,modified=binding['native_targets']-binding['native_additions'],plugins=52,retained=17893-(binding['native_targets']-binding['native_additions']))
    require(spec['counts']==expected_counts,'derived223_source527_native_counts_required')
    require(spec['native_files'] == binding['native_files'] and
            spec['selected_targets'] == binding['selected_target_count'] == len(spec['native_files'])+6 and
            data['fixed']['native_spec'] == data['native_spec'] and
            data['source_refs'][data['native_spec']['path']] == data['native_spec']['sha256'],
            'exact_native223_spec_CAS8_and_source_ref_join_required')
    require(source_readref(data['native_spec']) == spec and
            source_readref(data['fixed']['static_binding']) == binding and
            source_readref(data['fixed']['request']) == data['request'],
            'fresh_exact_static223_spec_binding_and_request_bytes_required')
    require(data['private_input']['project_files']['scripts/friday_ordinary_install.py'] == PRIVATE_HELPER
            and data['public_input']['project_files']['scripts/friday_ordinary_install.py'] == PUBLIC_HELPER
            and PRIVATE_HELPER != PUBLIC_HELPER and PRODUCT223_COMMIT != ACTUAL222_COMMIT,
            'private_public_and_historical_source_roles_must_be_distinct')
    return copy.deepcopy(binding), copy.deepcopy(spec)


def validate_project_binding(acceptance=None):
    data = bound_data()
    actual = supplied_predecessor()
    previous = actual['values']['input']
    current, public = data['private_input'], data['public_input']
    require(len(previous['project_files']) == 525 and
            len(current['project_files']) == len(public['project_files']) == 527,
            'genuine525_to527_required')
    require({k:v for k,v in previous.items() if k != 'project_files'} ==
            {k:v for k,v in current.items() if k != 'project_files'} ==
            {k:v for k,v in public.items() if k != 'project_files'},
            'actual222_nonproject_fields_preserved')
    for root, value in ((P, previous), (C, current), (S, public)):
        for name, digest_value in value['project_files'].items():
            path = str(root/name)
            require(data['source_refs'].get(path) == digest_value,
                    'physical_project_source_requires_external_pin')
            require(hashlib.sha256(source_raw(dict(path=path, sha256=digest_value))).hexdigest() == digest_value,
                    'physical_source_inventory_changed')
    differences = sorted(n for n,h in current['project_files'].items()
                         if public['project_files'][n] != h)
    require(len(differences) == 28 and differences ==
            sorted(row['path'] for row in data['public_origin']['public_private_differences']),
            'exact_historical28_private_public_counterparts_required')
    require(PUBLIC_CHECKER_PATH not in current['project_files'] and
            PUBLIC_CHECKER_PATH not in public['project_files'],
            'private_operator_not_product_or_public_origin')
    return dict(private_project=str(C), project_files=527, private_public28=differences,
                source_commit=PRODUCT223_COMMIT, source_only=True)


def project_source_pins(request, acceptance=None):
    data = bound_data()
    actual = supplied_predecessor()
    require(request['previous_input'] == actual['current_input'] == data['static_binding']['previous_input']
            and request['current_input'] == request['candidate_input'] == data['static_binding']['current_input'],
            'exact525_to_private527_input_refs_required')
    return copy.deepcopy(actual['values']['input']), copy.deepcopy(data['private_input'])


def validate_source_request(request, acceptance=None):
    data = bound_data()
    binding, spec = validate_candidate()
    require(request == data['request'], 'exact_authenticated_real223_request_required')
    project_source_pins(request, acceptance)
    validate_project_binding(acceptance)
    for name, pin in request['transaction_history'].items():
        require(reference(H/name)['sha256'] == pin, 'current_history_changed')
    for name in ('marker', 'source_receipt', 'stamp', 'configuration', 'profile',
                 'launcher', 'native_unit', 'previous_input', 'current_input',
                 'predecessor_request', 'target_receipt', 'candidate_input'):
        require(reference(request[name]['path']) == request[name], 'request_pin_changed:' + name)
    for path, pin in binding['selected_targets'].items():
        require(not os.path.lexists(path) if pin['before_sha256'] is None else
                reference(path)['sha256'] == pin['before_sha256'], 'selected_CAS_drift')
    for role in ('manifest', 'patch'):
        require(reference(spec[role]['path']) == clean_reference(spec[role]),
                'native_pair_source_changed')
    for row in spec['native_files']:
        ref = data['descriptor']['native_after'][row['path']]
        raw = source_raw(ref)
        require(ref['sha256'] == row['sha256'] and ref['bytes'] == row['bytes'] == len(raw),
                'native_afterimage_source_changed')
    return dict(expected_receipt_sha256=binding['prospective_receipt_sha256'],
                current_input=copy.deepcopy(binding['current_input']),
                previous_input=copy.deepcopy(binding['previous_input']),
                native_spec=copy.deepcopy(data['native_spec']),
                selected_target_count=binding['selected_target_count'],
                selected_targets=copy.deepcopy(binding['selected_targets']))


def fresh(value, now, reason):
    require(type(value) is str and type(now) in (int, float), reason)
    instant = datetime.datetime.fromisoformat(value)
    require(instant.utcoffset() is not None and 0 <= now-instant.timestamp() <= 300, reason)


def _validate_acceptance_fields(acceptance):
    data = bound_data()
    require(acceptance['schema'] == 'frw.root.native223-source-acceptance.v1' and
            acceptance['state'] == 'ROOT_ACCEPTED_EXACT223_F04_OWNED_INGRESS_STOP_TERMINAL_SOURCE_OFFLINE_NOT_RUNTIME'
            and acceptance['accepted'] is True and acceptance['execution_grant'] is False
            and acceptance['template_only_no_execution_grant'] is False,
            'new_exact_root223_source_only_acceptance_required')
    require(acceptance['frame_source_manifest'] == _MANIFEST_REF and
            acceptance['source_pins'] == data['fixed'] and
            acceptance['native_spec'] == data['native_spec'] and
            acceptance['product_source_commit'] == PRODUCT223_COMMIT,
            'accepted_exact223_manifest_spec_source_and_product_join_required')
    require(acceptance['v25_whole_transaction_and_default_postconsumer_precondition'] ==
            'NOT_RUN_POSTCONDITION_OF_SAME_ADMITTED_TRANSACTION' and
            acceptance['recovery_ready'] is False, 'future_postconsumer_not_precondition')


def validate_independent_acceptances(acceptance):
    require(acceptance['frame_review_evidence'] and acceptance['independent_review_evidence'],
            'independent_exact_source_reviews_required')
    for ref in acceptance['frame_review_evidence'] + acceptance['independent_review_evidence']:
        review = readref(ref)
        require(review.get('accepted') is True and review.get('source_only') is True
                and review.get('execution_grant') is False and not review['blocking_findings']
                and review['reviewed_source_manifest'] == _MANIFEST_REF,
                'independent_exact223_manifest_review_required')
    for ref in acceptance['frame_review_evidence']:
        require(readref(ref).get('whole_frame_acceptance') is True,
                'whole_frame_source_acceptance_required')


def _validate_current_snapshot(snapshot, *, now, boot_id):
    require(snapshot['schema'] == 'frw.root.native223-fresh-readback.v1' and
            snapshot['state'] == 'ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT'
            and snapshot['template_only_no_execution_grant'] is False,
            'new_actual223_fresh_readback_required')
    require(type(boot_id) is str and boot_id and snapshot['boot_id'] == boot_id,
            'same_boot_required')
    fresh(snapshot['observed_at_moscow'], now, 'fresh_readback_required')
    require(set(snapshot['checks']) == set(SNAPSHOT_TRUE_FIELDS) and
            all(v is True for v in snapshot['checks'].values()), 'every_current_check_required')
    require(snapshot['installed_receipt_sha256'] == BEFORE_RECEIPT and
            snapshot['installed_input_sha256'] == PREVIOUS_INPUT, 'actual222_before_pins_required')
    require(set(snapshot['services']) == {'gateway', 'dashboard'}, 'exact_two_current_services_required')
    for service in ('gateway', 'dashboard'):
        row = snapshot['services'][service]
        require(row['boot_id'] == boot_id and type(row['pid']) is int and row['pid'] > 0
                and type(row['birth_ticks']) is int and row['birth_ticks'] > 0
                and digest(row['invocation_id'], 32) and type(row['cgroup']) is str
                and row['cgroup'].startswith('/user.slice/') and '..' not in Path(row['cgroup']).parts
                and row['enabled_active'] is True and row['runtime_max'] == 'infinity',
                'fresh_permanent_service_identity_required')
    require(snapshot['evidence'], 'current_evidence_required')
    require(snapshot['remaining_limits'] == KNOWN_LIMITS and
            snapshot['unexposed_all_profile_pending_queues_proved'] is False,
            'known_limits_preserved')


def validate_join(request, acceptance, snapshot, *, now, boot_id):
    _validate_acceptance_fields(acceptance)
    validate_independent_acceptances(acceptance)
    result = validate_source_request(request, acceptance)
    _validate_current_snapshot(snapshot, now=now, boot_id=boot_id)
    origin = validate_snapshot_origin(acceptance, snapshot)
    for ref in snapshot['evidence']:
        readref(ref)
    b = bound_data()['static_binding']['budgets']
    result.update(source_origin=origin, genuine_actual222_predecessor=actual_predecessor(),
                  fresh_root_services=copy.deepcopy(snapshot['services']),
                  state='PURE_METADATA_BOUND_NOT_ADMISSION',
                  source_acceptance=reference(B/'ROOT-223-SOURCE-ACCEPTANCE.json'),
                  snapshot_boot_id=boot_id, operation_seconds=b['operation'],
                  forward_seconds=b['forward'], external_rollback_seconds=b['external_rollback'],
                  publisher_terminal_cleanup_seconds=b['terminal_cleanup'],
                  publisher_unit_seconds=b['publisher_unit'], publisher_client_seconds=b['publisher_client'])
    return result


def load_actor_binding(bundle):
    require(Path(bundle).resolve() == B.resolve(), 'exact_bundle_required')
    bound_data()
    # Re-read acceptance/readback/bound-input records on every explicit call.
    # Cached222 history and source-only223 data can never satisfy these records.
    names = dict(request='ROOT-FRESH-REQUEST.json',
                 source_acceptance='ROOT-223-SOURCE-ACCEPTANCE.json',
                 fresh_readback='ROOT-223-FRESH-READBACK.json')
    refs = {key: reference(B/name) for key,name in names.items()}
    records = {key: readref(ref) for key,ref in refs.items()}
    value = validate_join(records['request'], records['source_acceptance'],
                          records['fresh_readback'], now=time.time(),
                          boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    saved = readref(reference(B/'ROOT-223-BOUND-INPUTS.json'))
    require(saved['schema'] == 'frw.root.native223-bound-inputs.v1' and
            saved['state'] == 'ROOT_CURRENT_BOUND_INPUTS_NOT_EXECUTION_GRANT'
            and saved['template_only_no_execution_grant'] is False,
            'new223_bound_inputs_required')
    require(saved['binding'] == value, 'bound_input_join_changed')
    for key,ref in refs.items():
        require(saved[key] == ref and reference(B/names[key]) == ref,
                'saved_input_ref_changed')
    return value


def source_binding_refs(acceptance=None):
    if acceptance is None:
        acceptance = readref(reference(B/'ROOT-223-SOURCE-ACCEPTANCE.json'))
    refs = {name: acceptance[name] for name in ('origin_policy', 'project_source_proof')}
    for ref in refs.values():
        require(bound_data()['source_refs'].get(ref['path']) == ref['sha256'],
                'origin_source_proof_must_be_source_pinned')
        readref(ref)
    return refs


def origin_policy(acceptance=None):
    return readref(source_binding_refs(acceptance)['origin_policy'])


def origin_git(repository, *args, input=None):
    import subprocess
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.run(['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                           '-C', str(repository), *args], input=input,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=20, check=True, env=env).stdout


def git_oid(kind, raw):
    return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def origin_tree(repository, commit):
    rows = {}
    for record in origin_git(repository, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not record:
            continue
        header, name = record.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        name = name.decode('utf-8')
        require(name not in rows, 'duplicate_git_path')
        rows[name] = (mode, kind, oid)
    return rows


def origin_blobs(repository, tree, expected, modes=None):
    names = sorted(expected)
    modes = {n:'100644' for n in names} if modes is None else modes
    require(set(modes) == set(expected) and all(m in ('100644', '100755') for m in modes.values()),
            'exact_regular_git_modes_required')
    require(all(n in tree and tree[n][:2] == (modes[n], 'blob') for n in names),
            'exact_regular_published_blobs_required')
    oids = [tree[n][2] for n in names]
    raw = origin_git(repository, 'cat-file', '--batch', input=('\n'.join(oids)+'\n').encode())
    offset = 0
    for name, oid in zip(names, oids):
        end = raw.index(b'\n', offset)
        header = raw[offset:end].decode().split()
        offset = end+1
        require(len(header) == 3 and header[:2] == [oid, 'blob'], 'exact_git_blob_header_required')
        size = int(header[2])
        body = raw[offset:offset+size]
        offset += size
        require(raw[offset:offset+1] == b'\n' and len(body) == size, 'complete_git_blob_required')
        offset += 1
        require(git_oid('blob', body) == oid and hashlib.sha256(body).hexdigest() == expected[name],
                'published_raw_git_counterpart_changed')
    require(offset == len(raw), 'unexpected_git_batch_tail')


def source_origin(expected_head, fresh_origin, *, repository=None,
                  provenance_mode='local-committed-main', acceptance=None,
                  product_source_commit=None):
    data = bound_data()
    if acceptance is None:
        acceptance = readref(reference(B/'ROOT-223-SOURCE-ACCEPTANCE.json'))
    if product_source_commit is None:
        product_source_commit = acceptance['product_source_commit']
    require(product_source_commit == PRODUCT223_COMMIT == data['public_origin']['commit'],
            'fixed_real223_product_origin_join_required')
    require(digest(expected_head, 40), 'genuine_containing_commit_required')
    source_binding_refs(acceptance)
    validate_project_binding(acceptance)
    repository = Path(repository) if repository is not None else Path('/home/jericho/jericho/Friday_rework')
    head = origin_git(repository, 'rev-parse', 'HEAD').decode().strip()
    require(head == expected_head and provenance_mode in ('local-committed-main', 'published-remote'),
            'bound_main_head_required')
    if provenance_mode == 'local-committed-main':
        require(fresh_origin is None and
                origin_git(repository, 'symbolic-ref', '-q', 'HEAD').strip() == b'refs/heads/main' and
                origin_git(repository, 'rev-parse', 'refs/heads/main').decode().strip() == head,
                'local_committed_main_required')
    else:
        require(fresh_origin == head, 'fresh_published_remote_observation_required')
    require(not origin_git(repository, 'for-each-ref', '--format=%(refname)', 'refs/replace/').strip(),
            'replacement_objects_refused')
    require(origin_git(repository, 'rev-parse', '--is-shallow-repository').strip() == b'false',
            'full_ancestry_required')
    graft = Path(origin_git(repository, 'rev-parse', '--path-format=absolute', '--git-path',
                            'info/grafts').decode().strip())
    require(not os.path.lexists(graft), 'grafts_refused')
    for commit in (head, ACTUAL222_COMMIT, product_source_commit):
        require(git_oid('commit', origin_git(repository, 'cat-file', 'commit', commit)) == commit,
                'raw_commit_identity_changed')
        origin_git(repository, 'merge-base', '--is-ancestor', commit, head)
    origin_git(repository, 'merge-base', '--is-ancestor', ACTUAL222_COMMIT, product_source_commit)
    changed = {'scripts/friday_ordinary_install.py',
               'patches/hermes/'+LAYER+'-manifest.json', 'patches/hermes/'+LAYER+'.patch'}
    scoped = origin_git(repository, 'diff', '--no-renames', '--name-only', '-z',
                        ACTUAL222_COMMIT, product_source_commit).decode().split('\x00')
    require(all(n in changed or n.startswith('docs/') or n == 'README.md' for n in scoped if n),
            'product223_scope_outside_exact_new_delta_or_docs')
    beforepublic = data['before_public_input']['project_files']
    public = data['public_input']['project_files']
    modes = data['public_origin']['git_modes']
    origin_blobs(repository, origin_tree(repository, ACTUAL222_COMMIT), beforepublic,
                 {name:modes[name] for name in beforepublic})
    origin_blobs(repository, origin_tree(repository, product_source_commit), public, modes)
    advanced = origin_git(repository, 'diff', '--no-renames', '--name-only', '-z',
                          product_source_commit, head).decode().split('\x00')
    require(all(n.startswith('docs/') or n == 'README.md' or n in changed for n in advanced if n),
            'only_pinned_product_or_documentation_may_advance_origin')
    tree = origin_tree(repository, head)
    require(PUBLIC_CHECKER_PATH not in tree, 'private_operator_must_not_be_published')
    origin_blobs(repository, tree, public, modes)
    for name in changed:
        require(reference(repository/name)['sha256'] == public[name], 'actual_public_delta_working_drift')
    require(origin_git(repository, 'rev-parse', 'HEAD').decode().strip() == head,
            'HEAD_changed_during_source_check')
    return dict(schema='frw.root223.raw-git-full-counterpart-origin-proof.v1',
                current_head=head, product_source_commit=product_source_commit,
                current_head_role='ROOT_EXECUTION_SELECTOR_NOT_PRODUCT_SOURCE_RELABEL',
                fresh_origin_main=fresh_origin, provenance_mode=provenance_mode,
                remote_publication='DEFERRED_NOT_VERIFIED' if provenance_mode == 'local-committed-main'
                else 'FRESH_REMOTE_MAIN_VERIFIED', completed222_source_commit=ACTUAL222_COMMIT,
                predecessor_public_files=525, public_project_files=527, private_difference_count=28,
                reviewed_current_file_count=3, private_operator_public_origin=False,
                target_input_sha256=data['static_binding']['current_input']['sha256'],
                expected_NOT_INSTALLED_receipt_sha256=EXPECTED_RECEIPT)


def validate_snapshot_origin(acceptance, snapshot):
    require(acceptance['source_provenance'] == dict(mode=snapshot['provenance_mode'], commit=snapshot['head'])
            and acceptance['public_main_sha'] == snapshot['origin_main'], 'accepted_source_snapshot_join')
    proof = source_origin(snapshot['head'], snapshot['origin_main'],
                          provenance_mode=snapshot['provenance_mode'], acceptance=acceptance)
    require(snapshot['source_origin'] == proof, 'current_origin_proof_changed')
    return proof


def validate_profile_join(qualification, before, spec):
    require(spec == bound_data()['native_spec_value'], 'profile_selected_exact223_spec_required')
    require(qualification['schema'] == 'frw.root.native223-minimum-installed-bank-profile-qualification.v1',
            'profile223_schema_required')
    require(qualification['template_only_no_execution_grant'] is False and
            qualification['source_before_after'] == [222, 223], 'actual222_profile_revalidation_required')
    require(qualification['profile_equivalence_join'] == PROFILE_SOURCE_JOIN,
            'exact_reviewed_unchanged_profile_join_required')
    require(qualification['native_spec'] == bound_data()['native_spec'] and
            qualification['operational_input'] == bound_data()['static_binding']['current_input'],
            'profile_exact223_spec_and_private527_join_required')
    join = source_readref(PROFILE_SOURCE_JOIN)
    old = {name:before['files'][name]['sha256'] for name in
           ('hermes_cli/friday_workspace_pdf.py', 'hermes_cli/friday_workspace_presentation.py')}
    require(not set(old) & {row['path'] for row in spec['native_files']},
            'new223_tools_must_not_change_bank_profile_files')
    require(join['state'] == 'SOURCE_ONLY_EXACT206_PROFILE_UNCHANGED_IN207_NO_NEW_APP_CREDIT'
            and join['before_profile_source_digests'] == join['after_profile_source_digests'] == old
            and qualification['before_profile_source_digests'] == qualification['minimum_profile_source_digests'] == old,
            'exact_old_bank_profile_source_join_retained_through222_to223')
    require(join['changed_profile_definitions'] == [] and join['new_Office_effects'] == 0
            and join['saved_app_evidence_reused'] is True, 'no_new_Office_credit')
    for ref in join['evidence']:
        source_readref(ref)
    require(qualification['format_layout_ready'] is False and
            qualification['formal_test_credit'] is False, 'no_new_layout_formal_credit')
    return old
