"""Typed worker declaration proposals; no admission or deployment authority.

The caller must authenticate the source references and own the native operator
transaction.  These functions deliberately do not edit config, reseal a home,
archive a worker, run a probe, or treat a declaration as an observation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat


ROOT_A0 = ('a0_deployment',)
SETTINGS = ('plugins', 'entries', 'friday_rework', 'settings')
TEMPLATE = SETTINGS + ('onboarding', 'templates', 'friday-local')
TEMPLATE_A0 = TEMPLATE + ('config', 'a0_deployment')
TEMPLATE_INPUTS = TEMPLATE + ('worker_inputs',)
IDENTITY_FIELDS = ('platform', 'transport_profile', 'account_id', 'user_id')
CHANGE_PATHS = frozenset({('root_config', ROOT_A0),
    ('profile_config', ROOT_A0), ('root_config', TEMPLATE_A0),
    ('root_config', TEMPLATE_INPUTS)})
WORKER_INPUT_CHANGE_PATHS = (
    ('workers', 'a0', 'a0', 'deployment'),
    ('workers', 'a0', 'a0', 'launcher', 'sha256'),
    ('workers', 'a0', 'a0', 'policy'),
    ('a0_network', 'policy'),
    ('a0_network', 'endpoints'),
)
NATIVE_GAPS = (
    'reviewed_current_root_input_and_source_build_pm_inventory_required',
    'native_stopped_consumer_and_operator_admission_handoff_required',
    'exact_config_marker_lineage_and_profile_reseal_cas_required',
    'reviewed_launcher_promotion_and_all_input_pin_propagation_required',
)
MAX_SOURCE_BYTES = 32 * 1024 * 1024
DSH_CURRENT_DECLARATION_SCHEMA = 'friday.dsh-current-declaration-stage.v1'
DSH_CURRENT_PROOF_SCHEMA = 'friday.dsh-current-proof-stage.v1'
DSH_CURRENT_SCHEMAS = frozenset({DSH_CURRENT_DECLARATION_SCHEMA, DSH_CURRENT_PROOF_SCHEMA})
DSH_CURRENT_APPLY_SCHEMA = 'friday.dsh-current-availability.apply.v1'
PROFILE_DSH = SETTINGS + ('runtime', 'workers', 'dsh')
DSH_DECLARATION_PATHS = (('dsh', 'web', 'egress_evidence'), ('dsh', 'web', 'resolver'))

# These are public source bytes, not an installed worker/service receipt.  The
# guarded-six operational predecessor has additional private history and is not
# interchangeable with this five-file public predecessor.
SERVICE_SCHEMA = 'friday.worker-web-service-source-declaration.v1'
SERVICE_FILES = frozenset({
    'scripts/a0_runtime.py', 'scripts/rootless_docker_launch.py',
    'plugins/friday_rework/adapters/a0_profile.py',
    'plugins/friday_rework/adapters/a0_web.py',
    'scripts/friday-rework-docker.service',
})
SERVICE_ANCHOR = {
    'scripts/a0_runtime.py': 'd46880a70ac70dadefb56281d21137e1aa12e1042f71e47ba455956e2477cc32',
    'scripts/rootless_docker_launch.py': 'b6825c510a7b50be20419fc0f57fee042dc9beef6d10a58b10fef1592da2fd77',
    'plugins/friday_rework/adapters/a0_profile.py': 'a0ebc0925111dfb06c99e381c20a8cea079761e9ddea8ef2ef2af7a68cc57bc9',
    'plugins/friday_rework/adapters/a0_web.py': '1daf09d50e2443d0984b26d40356478c7a3d210ccd373d92e0781ec5e78d7bf0',
    'scripts/friday-rework-docker.service': '53e6d86ff912f4ad0761362bc5e7937d2131e48892469236be09db6b49bcd0ba',
}
WEB_PROBE_RUNTIME_SHA256 = 'f02f471dc6546999e8d33d004768650ab51f3eefe5d1ab36b1ab0eee928f59b8'
WEB_PROBE_SOURCE_SHA256 = 'ba8c7a73ef8452184d1b832fc207f1d954a8efe15ac0b8ab799b5b1986a34d76'
WEB_PROBE_TARGET = dict(SERVICE_ANCHOR, **{
    'scripts/a0_runtime.py': WEB_PROBE_RUNTIME_SHA256,
    'plugins/friday_rework/adapters/a0_web.py': WEB_PROBE_SOURCE_SHA256,
})
WEB_PROBE_SERVICE_DISCRIMINATOR = 'PUBLIC_A0_WEB_OVERLAY_XMLRPC_EXACT'
WEB_HTTP_RUNTIME_SHA256 = '943b399247db9636dbf6aaf96f79ae988852f4366f3f7ef3893e77433425d11a'
WEB_HTTP_SOURCE_SHA256 = 'b16fb6681372223c4c6c04e6e7021eb53993cea56136bfe28419ac566976d5b6'
WEB_HTTP_TARGET = dict(WEB_PROBE_TARGET, **{
    'scripts/a0_runtime.py': WEB_HTTP_RUNTIME_SHA256,
    'plugins/friday_rework/adapters/a0_web.py': WEB_HTTP_SOURCE_SHA256,
})
WEB_HTTP_SERVICE_DISCRIMINATOR = 'PUBLIC_A0_WEB_HTTP_CONFIG_GIT_EXACT'
SERVICE_INPUT_PATHS = (
    ('workers', 'a0', 'a0', 'runtime', 'sha256'),
    ('workers', 'a0', 'a0', 'launcher', 'sha256'),
)


def web_probe_service_transition(old, new):
    """Recognize only the reviewed public two-file web/runtime source edge."""
    return (type(old) is dict and type(new) is dict
        and old == SERVICE_ANCHOR and new == WEB_PROBE_TARGET)


def web_http_service_transition(old, new):
    """The exact public first web tuple to its HTTP/Git repair."""
    return (type(old) is dict and type(new) is dict
        and old == WEB_PROBE_TARGET and new == WEB_HTTP_TARGET)


def service_transition_pair(discriminator):
    """Resolve only published public source edges, never installed history."""
    if discriminator == WEB_PROBE_SERVICE_DISCRIMINATOR:
        return copy.deepcopy(SERVICE_ANCHOR), copy.deepcopy(WEB_PROBE_TARGET)
    require(discriminator == WEB_HTTP_SERVICE_DISCRIMINATOR,
        'worker_declaration_exact_public_web_service_transition_required')
    return copy.deepcopy(WEB_PROBE_TARGET), copy.deepcopy(WEB_HTTP_TARGET)


def service_installed_discriminator(project):
    target = service_project_sources(project)
    if target == WEB_PROBE_TARGET:
        return WEB_PROBE_SERVICE_DISCRIMINATOR
    require(target == WEB_HTTP_TARGET,
        'worker_declaration_installed_service_target_required')
    return WEB_HTTP_SERVICE_DISCRIMINATOR


def service_source_transition(old, new):
    require(web_probe_service_transition(old, new) or web_http_service_transition(old, new),
        'worker_declaration_exact_public_web_service_transition_required')
    return ('plugins/friday_rework/adapters/a0_web.py', 'scripts/a0_runtime.py')


def service_transition_discriminator(old, new):
    service_source_transition(old, new)
    return (WEB_HTTP_SERVICE_DISCRIMINATOR if web_http_service_transition(old, new)
        else WEB_PROBE_SERVICE_DISCRIMINATOR)


def service_project_sources(project):
    require(type(project) is dict,
        'worker_declaration_service_project_inventory_required')
    return {name: project.get(name) for name in SERVICE_FILES}


def service_source_edge(previous, current, anchor, *, target=None):
    """Distinguish pending publication from unchanged source observations."""
    if target is None:
        target = WEB_HTTP_TARGET if anchor == WEB_PROBE_TARGET else WEB_PROBE_TARGET
    service_source_transition(anchor, target)
    left = service_project_sources(previous)
    right = service_project_sources(current)
    require(any(left == a and right == b for a, b in (
        (anchor, anchor), (anchor, target), (target, target))),
        'worker_declaration_exact_public_web_service_edge_changed')
    return left == anchor and right == target


def pending_service_project(previous, current):
    require(type(previous) is dict and type(current) is dict
        and type(previous.get('project_files')) is dict
        and type(current.get('project_files')) is dict,
        'worker_declaration_service_project_inventory_required')
    old = service_project_sources(previous['project_files'])
    new = service_project_sources(current['project_files'])
    if old == new:
        return None
    service_source_transition(old, new)
    require(_same({k: v for k, v in previous.items() if k != 'project_files'},
        {k: v for k, v in current.items() if k != 'project_files'}),
        'worker_declaration_service_project_operational_delta_refused')
    return copy.deepcopy(current['project_files'])


def service_pending_target(anchor, current, future):
    service_source_transition(anchor, future)
    require(type(current) is dict and current in (anchor, future),
        'worker_declaration_exact_public_web_pending_required')


def service_publication_sources(before, after, old, new, home):
    """Join both existing source mirrors; never publish or grant authority."""
    changed = service_source_transition(old, new)
    require(type(before) is dict and type(after) is dict and set(before) == set(after),
        'worker_declaration_service_publication_inventory_required')
    root = _absolute(str(home))
    for staged, ref in before.items():
        require(type(staged) is str and staged.startswith('worker-runtime-source/')
            and _reference(ref) == root / staged,
            'worker_declaration_service_publication_plan_join_changed')
        if staged not in {'worker-runtime-source/' + name for name in changed}:
            require(after[staged] == ref['sha256'],
                'worker_declaration_service_unrelated_publication_delta')
    for name in changed:
        staged = 'worker-runtime-source/' + name
        require(staged in before and _reference(before[staged]) == root / staged
            and before[staged]['sha256'] == old[name]
            and after.get(staged) == new[name],
            'worker_declaration_service_publication_plan_join_changed')


def service_worker_discriminator(after):
    runtime_after = _at(after, SERVICE_INPUT_PATHS[0])
    require(runtime_after in (WEB_PROBE_RUNTIME_SHA256, WEB_HTTP_RUNTIME_SHA256),
        'worker_declaration_exact_service_input_pin_required')
    return (WEB_HTTP_SERVICE_DISCRIMINATOR
        if runtime_after == WEB_HTTP_RUNTIME_SHA256 else WEB_PROBE_SERVICE_DISCRIMINATOR)


def service_worker_inputs(before, after, home):
    """Update the public runtime donor hash, retaining every other input."""
    require(type(before) is dict and type(after) is dict,
        'worker_declaration_service_worker_inputs_required')
    anchor, target = service_transition_pair(service_worker_discriminator(after))
    restored = copy.deepcopy(after)
    root = _absolute(str(home))
    for path, name in zip(SERVICE_INPUT_PATHS,
            ('scripts/a0_runtime.py', 'scripts/rootless_docker_launch.py')):
        require(_at(before, path) == anchor[name]
            and _at(after, path) == target[name],
            'worker_declaration_exact_service_input_pin_required')
        old_ref, new_ref = _at(before, path[:-1]), _at(after, path[:-1])
        require(_reference(old_ref) == _reference(new_ref)
            and (name != 'scripts/a0_runtime.py'
                or old_ref['path'] == str(root / 'worker-runtime-source' / name)),
            'worker_declaration_service_input_path_changed')
        _replace(restored, path, anchor[name])
    require(_same(before, restored),
        'worker_declaration_service_unrelated_worker_input_delta')


def service_installation_delta(previous, current, plan):
    """Maintain two worker mirrors only after canonical source installation.

    This writer never installs project/native code. Both installation tuples
    describe the same already-installed public target; only the separate
    declaration and the two existing worker mirrors may change.
    """
    require(type(plan) is dict, 'worker_declaration_exact_service_plan_required')
    _, target = service_transition_pair(plan.get('service_source_transition'))
    require(type(previous) is dict and type(current) is dict
        and _same(previous, current)
        and type(current.get('project_files')) is dict
        and service_project_sources(current['project_files']) == target,
        'worker_declaration_installed_service_target_required')
    require(_same(_at(current, ('product', 'runtime')), {'enabled': False}),
        'worker_declaration_runtime_must_remain_disabled')


def service_declaration_plan(root_config, profile_config, worker_inputs, identity, bundle):
    """Plan the exact public mirror edge; native custody is still required."""
    require(type(root_config) is dict and type(profile_config) is dict
        and type(worker_inputs) is dict and type(bundle) is dict,
        'worker_declaration_documents_required')
    require(bundle.get('schema') == SERVICE_SCHEMA and bundle.get('state') ==
        'PROPOSED_NOT_APPLIED_NOT_AN_EXECUTABLE_MIGRATION_REQUEST',
        'worker_declaration_service_schema_required')
    _reference(bundle.get('identity_reference'))
    home, profile_home = _identity_join(root_config, profile_config, identity, bundle)
    require(worker_inputs.get('required') == ['dsh', 'a0']
        and type(worker_inputs.get('workers')) is dict
        and set(worker_inputs['workers']) == {'dsh', 'a0'}
        and all(type(worker_inputs['workers'][name]) is dict for name in ('dsh', 'a0'))
        and _same(worker_inputs.get('source_scope'),
            {'home': str(home), 'profile': identity['binding']['transport_profile']}),
        'worker_declaration_service_scope_changed')
    before = _at(root_config, TEMPLATE_INPUTS)
    service_worker_inputs(before, worker_inputs, home)
    discriminator = service_worker_discriminator(worker_inputs)
    deployment = _at(worker_inputs, ('workers', 'a0', 'a0', 'deployment'))
    require(type(deployment) is dict and type(deployment.get('chat')) is dict
        and type(deployment.get('utility')) is dict
        and type(deployment.get('embedding')) is dict
        and all(_same(deployment, _at(cfg, path)) for cfg, path in (
            (root_config, ROOT_A0), (profile_config, ROOT_A0),
            (root_config, TEMPLATE_A0))),
        'worker_declaration_service_deployment_must_remain_unchanged')
    rows = bundle.get('changes')
    require(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict
        and set(rows[0]) == {'document', 'path', 'before_sha256', 'after_reference'}
        and rows[0]['document'] == 'root_config'
        and rows[0]['path'] == list(TEMPLATE_INPUTS)
        and rows[0]['before_sha256'] == fingerprint(before),
        'worker_declaration_service_exact_input_change_required')
    _reference(rows[0]['after_reference'])
    result = copy.deepcopy(root_config)
    _replace(result, TEMPLATE_INPUTS, worker_inputs)
    return {'schema': 'friday.worker-declaration-delta.v1',
        'state': 'SOURCE_DECLARATION_DELTA_ONLY_NOT_NATIVE_AUTHORITY',
        'ready': False, 'native_authority': False,
        'native_apply_implemented': True, 'workers_enabled': False,
        'service_source_transition': discriminator,
        'root_config': result, 'profile_config': copy.deepcopy(profile_config),
        'semantic_changes': [{'document': 'root_config', 'path': list(TEMPLATE_INPUTS),
            'before_sha256': fingerprint(before), 'after_sha256': fingerprint(worker_inputs)}],
        'principal': identity['principal'], 'generation': identity['generation'],
        'profile': str(profile_home),
        'launcher': {'reference': copy.deepcopy(_at(worker_inputs,
            ('workers', 'a0', 'a0', 'launcher'))),
            'state': 'UNCHANGED_PUBLIC_LAUNCHER_SOURCE_ONLY', 'installed': False},
        'missing_native_prerequisites': list(NATIVE_GAPS)}


class DeclarationError(ValueError):
    """Bounded public code; never interpolate a path or private document."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise DeclarationError(code)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _typed(value):
    """Canonical JSON equality distinguishes bool/int and absent/null."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False)


def _same(left, right):
    return _typed(left) == _typed(right)


def _at(value, path):
    for part in path:
        require(type(value) is dict and part in value,
            'worker_declaration_path_missing')
        value = value[part]
    return value


def _replace(value, path, replacement):
    parent = _at(value, path[:-1])
    require(type(parent) is dict and path[-1] in parent,
        'worker_declaration_path_missing')
    parent[path[-1]] = copy.deepcopy(replacement)


def _absolute(value):
    require(type(value) is str and value.startswith('/')
        and not any(ord(char) < 32 for char in value),
        'worker_declaration_absolute_path_required')
    path = Path(value)
    require(str(path) == value and '..' not in path.parts,
        'worker_declaration_canonical_path_required')
    return path


def _reference(value):
    require(type(value) is dict and set(value) == {'path', 'sha256'},
        'worker_declaration_exact_reference_required')
    path = _absolute(value['path'])
    sha = value['sha256']
    require(type(sha) is str and len(sha) == 64
        and all(c in '0123456789abcdef' for c in sha) and sha != '0' * 64,
        'worker_declaration_exact_digest_required')
    return path


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'worker_declaration_duplicate_json_key')
        result[key] = value
    return result


def _read_reference(ref, *, json_document=True):
    """Read a pinned owned private regular file, retaining exact fd identity.

    Open each directory without following links. Native mutation locks remain
    the caller's responsibility; an unchanged hash alone grants no authority.
    """
    path = _reference(ref)
    # Reject a FIFO/device at fstat instead of blocking in open beforehand.
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    parent_fd = os.open('/', flags | os.O_DIRECTORY)
    fd = None
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, flags | os.O_DIRECTORY, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child
        fd = os.open(path.name, flags, dir_fd=parent_fd)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
            and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600
            and before.st_size <= MAX_SOURCE_BYTES,
            'worker_declaration_private_source_required')
        chunks = []
        size = 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, MAX_SOURCE_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            require(size <= MAX_SOURCE_BYTES, 'worker_declaration_source_too_large')
        after = os.fstat(fd)
        current = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
            s.st_ctime_ns, s.st_mode, s.st_uid, s.st_nlink)
        require(identity(before) == identity(after) == identity(current),
            'worker_declaration_source_changed')
        raw = b''.join(chunks)
        require(hashlib.sha256(raw).hexdigest() == ref['sha256'],
            'worker_declaration_source_digest_changed')
        if not json_document:
            return raw
        return json.loads(raw, object_pairs_hook=_no_duplicates,
            parse_constant=lambda _: (_ for _ in ()).throw(
                DeclarationError('worker_declaration_nonfinite_json')))
    finally:
        if fd is not None:
            os.close(fd)
        os.close(parent_fd)


def _identity_join(root_config, profile_config, identity, bundle, *, dsh_current=False):
    require(type(identity) is dict and identity.get('schema') ==
        'frw.current-dest-worker-identity.v1', 'worker_declaration_identity_schema')
    binding = identity.get('binding')
    require(type(binding) is dict and all(type(binding.get(k)) is str
        and binding[k] and len(binding[k].encode()) <= 512
        and binding[k].strip() == binding[k]
        and not any(ord(char) < 32 for char in binding[k]) for k in IDENTITY_FIELDS)
        and all(type(binding.get(k)) is str and re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', binding[k])
            for k in ('runtime_profile', 'transport_profile')),
        'worker_declaration_identity_invalid')
    principal = hashlib.sha256(json.dumps([binding[k] for k in IDENTITY_FIELDS],
        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    require(identity.get('principal') == principal
        and identity.get('binding_sha256') == fingerprint(binding),
        'worker_declaration_identity_fingerprint_changed')
    require(type(identity.get('generation')) is int and identity['generation'] > 0
        and identity.get('enabled') is True,
        'worker_declaration_current_generation_required')
    require((identity.get('profile_template') == 'friday-ordinary-local' or (
            dsh_current and type(identity.get('profile_template')) is str
            and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', identity['profile_template'])))
        and identity.get('worker_attach_template') == 'friday-local',
        'worker_declaration_template_identity_changed')
    profile_home = _absolute(identity.get('profile'))
    require(profile_home.name == binding['runtime_profile']
        and profile_home.parent.name == 'profiles',
        'worker_declaration_profile_identity_changed')
    home = profile_home.parent.parent
    rows = _at(root_config, SETTINGS + ('user_isolation', 'bindings'))
    require(type(rows) is list, 'worker_declaration_bindings_required')
    matches = [row for row in rows if type(row) is dict
        and row.get('runtime_profile') == binding['runtime_profile']]
    require(len(matches) == 1 and _same(matches[0], binding),
        'worker_declaration_current_binding_changed')
    for document in (root_config, profile_config):
        settings = _at(document, SETTINGS)
        require(type(settings) is dict and (dsh_current or (
            _same(settings.get('runtime'), {'enabled': False})
            and 'worker_requirements' not in settings)),
            'worker_declaration_ordinary_profile_required')
    refs = identity.get('source_refs')
    require(type(refs) is dict and set(refs) == {'access_state', 'configuration',
        'onboarding', 'root_configuration', 'stale_attachment', 'user_marker'},
        'worker_declaration_identity_sources_required')
    paths = {name: _reference(ref) for name, ref in refs.items()}
    expected = {'configuration': profile_home / 'config.yaml',
        'root_configuration': home / 'config.yaml',
        'onboarding': profile_home / '.friday-onboarding.json',
        'user_marker': profile_home / '.friday-user-scope.json',
        'stale_attachment': profile_home / 'workers' / 'attachment.json'}
    require(all(paths[name] == path for name, path in expected.items())
        and paths['access_state'].name == 'state.json'
        and paths['access_state'].parent.parent == home / 'plugin-data',
        'worker_declaration_identity_source_path_changed')
    require(_same(refs['root_configuration'], bundle.get('root_before'))
        and _same(refs['configuration'], bundle.get('profile_before')),
        'worker_declaration_current_raw_cas_changed')
    return home, profile_home


def _deployment_join(root_config, profile_config, deployment):
    """Join A0 chat to both current native main declarations, keeping auxiliaries.

    An authenticated proposal still cannot choose a different model/capacity
    merely because its four container subtrees were explicitly named.
    """
    chat_fields = {'endpoint', 'model', 'context_length', 'max_output_tokens'}
    require(type(deployment) is dict and type(deployment.get('chat')) is dict,
        'worker_declaration_deployment_required')
    after_chat = deployment['chat']
    for document in (root_config, profile_config):
        model = _at(document, ('model',))
        require(type(model) is dict and type(model.get('default')) is str
            and type(model.get('base_url')) is str,
            'worker_declaration_current_main_metadata_required')
        capacity = _at(document, ('providers', 'friday-local', 'models', model['default']))
        require(type(capacity) is dict and type(capacity.get('context_length')) is int
            and capacity['context_length'] > 0
            and type(capacity.get('bounded_context')) is dict
            and type(capacity['bounded_context'].get('main_max_output_tokens')) is int
            and 0 < capacity['bounded_context']['main_max_output_tokens'] <=
                capacity['context_length'],
            'worker_declaration_current_main_capacity_required')
        expected = {'endpoint': model['base_url'], 'model': model['default'],
            'context_length': capacity['context_length'],
            'max_output_tokens': capacity['bounded_context']['main_max_output_tokens']}
        require(all(field in after_chat and _same(after_chat[field], value)
            for field, value in expected.items()),
            'worker_declaration_current_main_join_changed')
    for before in (_at(root_config, ROOT_A0), _at(profile_config, ROOT_A0),
            _at(root_config, TEMPLATE_A0)):
        require(type(before) is dict and type(before.get('chat')) is dict
            and all(field in before and field in deployment
                and _same(before[field], deployment[field]) for field in ('utility', 'embedding')),
            'worker_declaration_auxiliary_deployment_changed')
        # Preserve timeout and all unrequested chat/deployment metadata. The
        # declared descriptive name and the four current-main leaves may move.
        require('timeout' in before['chat'] and 'timeout' in after_chat
            and _same(before['chat']['timeout'], after_chat['timeout'])
            and _same({k: v for k, v in before['chat'].items() if k not in chat_fields},
                {k: v for k, v in after_chat.items() if k not in chat_fields})
            and _same({k: v for k, v in before.items() if k not in ('name', 'chat')},
                {k: v for k, v in deployment.items() if k not in ('name', 'chat')}),
            'worker_declaration_deployment_metadata_changed')


def _worker_inputs_join(root_config, worker_inputs, deployment):
    """Retain every resource budget/native pin outside five reviewed leaves."""
    before = _at(root_config, TEMPLATE_INPUTS)
    require(type(before) is dict, 'worker_declaration_current_worker_inputs_required')
    _reference(_at(before, ('workers', 'a0', 'a0', 'launcher')))
    policy = _at(worker_inputs, ('workers', 'a0', 'a0', 'policy'))
    network_policy = _at(worker_inputs, ('a0_network', 'policy'))
    _reference(policy)
    _reference(network_policy)
    require(_same(policy, network_policy), 'worker_declaration_network_policy_join_changed')
    endpoints = []
    for role in ('chat', 'utility', 'embedding'):
        value = deployment[role].get('endpoint')
        require(type(value) is str and value,
            'worker_declaration_deployment_endpoint_required')
        if value not in endpoints:
            endpoints.append(value)
    require(_same(_at(worker_inputs, ('a0_network', 'endpoints')), endpoints),
        'worker_declaration_network_endpoints_join_changed')
    restored = copy.deepcopy(worker_inputs)
    for path in WORKER_INPUT_CHANGE_PATHS:
        # Both sides must actually contain each admitted leaf. No implicit
        # defaults or guessed native declarations may enter the proposal.
        _at(restored, path)
        _replace(restored, path, _at(before, path))
    require(_same(before, restored), 'worker_declaration_unrelated_worker_input_delta')


def plan_declaration_delta(root_config, profile_config, worker_inputs, identity, bundle):
    """Return exactly four typed CAS replacements on current document copies.

    This pure function checks a static identity join, not native pairing,
    current_access, a signed operator session, or current source installation.
    Authenticate all input pins in the owning native transaction before use.
    """
    require(type(root_config) is dict and type(profile_config) is dict
        and type(worker_inputs) is dict and type(bundle) is dict,
        'worker_declaration_documents_required')
    if bundle.get('schema') in DSH_CURRENT_SCHEMAS:
        return dsh_current_plan(root_config, profile_config, worker_inputs, identity, bundle)
    if bundle.get('schema') == SERVICE_SCHEMA:
        return service_declaration_plan(root_config, profile_config, worker_inputs, identity, bundle)
    require(bundle.get('schema') == 'frw.current-both-spark-declaration-change-data.v1'
        and bundle.get('state') ==
            'PROPOSED_NOT_APPLIED_NOT_AN_EXECUTABLE_MIGRATION_REQUEST',
        'worker_declaration_bundle_schema')
    _reference(bundle.get('identity_reference'))
    home, profile_home = _identity_join(root_config, profile_config, identity, bundle)
    require(worker_inputs.get('required') == ['dsh', 'a0']
        and type(worker_inputs.get('workers')) is dict
        and set(worker_inputs['workers']) == {'dsh', 'a0'}
        and _same(worker_inputs.get('source_scope'), {'home': str(home),
            'profile': identity['binding']['transport_profile']}),
        'worker_declaration_worker_input_scope_changed')
    try:
        deployment = worker_inputs['workers']['a0']['a0']['deployment']
        launcher = worker_inputs['workers']['a0']['a0']['launcher']
    except (KeyError, TypeError):
        raise DeclarationError('worker_declaration_a0_inputs_required') from None
    _reference(launcher)
    require(type(deployment) is dict and type(deployment.get('chat')) is dict
        and type(deployment.get('utility')) is dict
        and type(deployment.get('embedding')) is dict,
        'worker_declaration_deployment_required')
    _deployment_join(root_config, profile_config, deployment)
    _worker_inputs_join(root_config, worker_inputs, deployment)
    changes = bundle.get('changes')
    require(type(changes) is list and len(changes) == 4,
        'worker_declaration_exact_four_changes_required')
    indexed = {}
    for row in changes:
        require(type(row) is dict and type(row.get('document')) is str
            and type(row.get('path')) is list
            and all(type(part) is str for part in row['path']),
            'worker_declaration_change_shape_invalid')
        key = (row['document'], tuple(row['path']))
        require(key in CHANGE_PATHS and key not in indexed,
            'worker_declaration_change_path_forbidden')
        indexed[key] = row
    require(set(indexed) == CHANGE_PATHS, 'worker_declaration_exact_four_changes_required')
    documents = {'root_config': copy.deepcopy(root_config),
        'profile_config': copy.deepcopy(profile_config)}
    semantic = []
    for document, path in sorted(CHANGE_PATHS):
        row = indexed[(document, path)]
        before = _at(documents[document], path)
        if path == TEMPLATE_INPUTS:
            require(set(row) == {'document', 'path', 'before_sha256', 'after_reference'}
                and row['before_sha256'] == fingerprint(before),
                'worker_declaration_worker_inputs_cas_changed')
            _reference(row['after_reference'])
            after = worker_inputs
        else:
            require(set(row) == {'document', 'path', 'before', 'after'}
                and _same(before, row['before']), 'worker_declaration_beforeimage_changed')
            require(_same(row['after'], deployment),
                'worker_declaration_deployment_join_changed')
            after = row['after']
        require(not _same(before, after), 'worker_declaration_noop_not_four_changes')
        _replace(documents[document], path, after)
        semantic.append({'document': document, 'path': list(path),
            'before_sha256': fingerprint(before), 'after_sha256': fingerprint(after)})
    # Prove the complement, including dynamic identity collections and all
    # browser/web/compressor/model settings, with type-sensitive equality.
    for name, original in (('root_config', root_config), ('profile_config', profile_config)):
        restored = copy.deepcopy(documents[name])
        for document, path in CHANGE_PATHS:
            if document == name:
                _replace(restored, path, _at(original, path))
        require(_same(original, restored), 'worker_declaration_unrelated_delta')
    return {'schema': 'friday.worker-declaration-delta.v1',
        'state': 'SOURCE_DECLARATION_DELTA_ONLY_NOT_NATIVE_AUTHORITY',
        'ready': False, 'native_authority': False, 'native_apply_implemented': True,
        'workers_enabled': False,
        'root_config': documents['root_config'], 'profile_config': documents['profile_config'],
        'semantic_changes': semantic, 'principal': identity['principal'],
        'generation': identity['generation'], 'profile': str(profile_home),
        'launcher': {'reference': copy.deepcopy(launcher),
            'state': 'ALREADY_PROMOTED_LAUNCHER_REQUIRED_AT_NATIVE_APPLY', 'installed': False},
        'missing_native_prerequisites': list(NATIVE_GAPS)}


def profile_dsh_path(profile_config):
    """Retain the native single-worker or worker-map configuration shape."""
    runtime = _at(profile_config, SETTINGS + ('runtime',))
    require(type(runtime) is dict and runtime.get('enabled') is True,
        'dsh_current_enabled_profile_required')
    if 'dsh' in runtime:
        require('a0' not in runtime and 'workers' not in runtime, 'dsh_current_runtime_shape')
        return SETTINGS + ('runtime',)
    require(type(runtime.get('workers')) is dict and 'dsh' in runtime['workers'],
        'dsh_current_runtime_shape')
    return PROFILE_DSH


def historical_dsh_current(runtime, native, *, source_names=None):
    """Check the signed retired D/P headers without granting current health.

    Old source paths may now contain a reviewed successor and an old resolver
    may be absent. Only the exact old D/P/cycle documents are retained here;
    current-source, boot and environment observations belong to the new D/P.
    """
    from .dsh_current_availability import (
        DECLARATION, PROOF, HISTORY_NAMES, checked_cycle, source_pins,
        runtime_semantic_digest, runtime_input_pins)
    previous = runtime.get('current_availability')
    require(type(previous) is dict and set(previous) == {'declaration', 'proof', 'cycle'}
        and previous['proof'] is not None, 'dsh_current_refresh_active_beforeimage_required')
    for ref in previous.values():
        _reference(ref)
    old = _read_reference(previous['declaration'])
    proof = _read_reference(previous['proof'])
    checked_cycle(previous['cycle'])
    require(type(old) is dict and set(old) == {'schema', 'runtime_home', 'runtime_profile',
        'runtime_sha256', 'policy', 'policy_authority', 'native', 'sources', 'inputs', 'history'}
        and old['schema'] == DECLARATION
        and old['runtime_home'] == runtime['runtime_home']
        and old['runtime_profile'] == runtime['runtime_profile']
        and old['runtime_sha256'] == runtime_semantic_digest(runtime)
        and _same(old['native'], native)
        and _same(old['policy'], _at(runtime, ('dsh', 'web', 'egress_evidence')))
        and _same(old['inputs'], runtime_input_pins(runtime)),
        'dsh_current_historical_declaration_join_changed')
    if source_names is None:
        source_names = set(source_pins())
    require(type(old['sources']) is dict and set(old['sources']) == source_names
        and type(old['history']) is dict and HISTORY_NAMES <= set(old['history'])
        and set(old['history']) <= HISTORY_NAMES | {'preparation_provenance', 'current_requalification'}
        and type(old['history']['retained']) is dict
        and type(old['policy_authority']) is dict and set(old['policy_authority']) == {'id', 'generation'}
        and type(old['policy_authority']['id']) is str and old['policy_authority']['id']
        and type(old['policy_authority']['generation']) is int and old['policy_authority']['generation'] > 0,
        'dsh_current_historical_declaration_shape_changed')
    for ref in (*old['sources'].values(), *old['inputs'].values(),
            *(old['history'][name] for name in HISTORY_NAMES - {'retained'}),
            *old['history']['retained'].values()):
        _reference(ref)
    if 'preparation_provenance' in old['history']:
        provenance = old['history']['preparation_provenance']
        require(type(provenance) is dict and set(provenance) == {'intent', 'committed'},
            'dsh_current_historical_provenance_shape_changed')
        for ref in provenance.values():
            _reference(ref)
    if 'current_requalification' in old['history']:
        # Retired headers retain their complete typed metadata. Do not reopen
        # missing historical originals or rerun old readiness after reboot.
        mode = old['history']['current_requalification']
        require(type(mode) is dict and set(mode) == {'schema', 'purpose',
            'historical_graph_integrity', 'missing_as_of', 'recovery_provenance',
            'edges', 'static_smoke'}
            and mode['schema'] == 'friday.dsh-current-history-requalification.v1'
            and mode['purpose'] == 'DSH_CURRENT_ONLY_NO_HISTORICAL_REACCEPTANCE'
            and mode['historical_graph_integrity'] == 'INCOMPLETE'
            and type(mode['missing_as_of']) is str and re.fullmatch(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+]03:00', mode['missing_as_of'])
            and type(mode['edges']) is dict
            and set(mode['edges']) == set(old['history']['retained']),
            'dsh_current_historical_requalification_shape')
        _reference(mode['recovery_provenance'])
        for name, item in mode['edges'].items():
            require(type(item) is dict and set(item) == {'reference', 'state', 'copy'}
                and _same(item['reference'], old['history']['retained'][name])
                and item['state'] in ('VERIFIED_ORIGINAL', 'VERIFIED_EXACT_COPY', 'MISSING_AS_OF'),
                'dsh_current_historical_requalification_edge_shape')
            if item['state'] == 'VERIFIED_EXACT_COPY':
                _reference(item['copy'])
                require(item['copy']['sha256'] == item['reference']['sha256']
                    and item['copy']['path'] != item['reference']['path'],
                    'dsh_current_historical_requalification_alias_shape')
            else:
                require(item['copy'] is None, 'dsh_current_historical_requalification_alias_shape')
        smoke = mode['static_smoke']
        require(type(smoke) is dict and set(smoke) == {'observation', 'canonical_observation', 'reuse'}
            and _same(smoke['canonical_observation'], old['history']['observation'])
            and smoke['reuse'] == 'EXACT_SAME_STATIC_INPUTS_ONLY',
            'dsh_current_historical_static_provenance_shape')
        _reference(smoke['observation']); _reference(smoke['canonical_observation'])
    require(type(proof) is dict and set(proof) == {'schema', 'effects', 'per_job_authority',
        'declaration', 'runtime_sha256', 'policy', 'native', 'sources', 'inputs', 'current',
        'clock', 'observed_mono', 'pending_transaction', 'folder', 'safety', 'network', 'cycle'}
        and proof['schema'] == PROOF and proof['effects'] == 'OBSERVATION_ONLY'
        and proof['per_job_authority'] == 'NOT_GRANTED'
        and _same(proof['declaration'], previous['declaration'])
        and _same(proof['cycle'], previous['cycle'])
        and proof['runtime_sha256'] == old['runtime_sha256']
        and all(_same(proof[name], old[name]) for name in ('policy', 'native', 'sources', 'inputs')),
        'dsh_current_historical_proof_join_changed')
    _reference(proof['clock']); _reference(proof['pending_transaction'])
    _absolute(proof['folder'])
    context = proof['current']
    require(type(context) is dict and set(context) == {'boot_id', 'net_namespace'}
        and type(context['boot_id']) is str and context['boot_id']
        and type(context['net_namespace']) is list and len(context['net_namespace']) == 2
        and all(type(value) is int and value >= 0 for value in context['net_namespace']),
        'dsh_current_historical_proof_context_changed')
    require(type(proof.get('observed_mono')) in (int, float)
        and math.isfinite(proof['observed_mono']) and proof['observed_mono'] >= 0,
        'dsh_current_historical_proof_time_changed')
    return copy.deepcopy(previous)


def dsh_current_transaction_name(bundle, previous=None, *, before_configurations=None):
    """Consume a signed before-edge, never declaration encoding or a new clock."""
    from .dsh_current_availability import identity
    current = bundle['runtime_after']['current_availability']
    declaration_stage = bundle['schema'] == DSH_CURRENT_DECLARATION_SCHEMA
    if not declaration_stage:
        # One signed pending edge permits one activation attempt. Neither a
        # different observation nor formatting/path/clock changes can replay a
        # consumed or UNKNOWN T2. A new cycle requires its own typed T1.
        _reference(current['declaration']); _reference(current['cycle'])
        key = fingerprint({'schema':'friday.dsh-current-activation-key.v1',
            'declaration':current['declaration'],'cycle':current['cycle']})
        return 'ordinary-dsh-current-activation-' + key
    if declaration_stage and previous is not None:
        observed = identity()
        require(_same(bundle.get('refresh_context'), observed),
            'dsh_current_refresh_context_changed')
        key = fingerprint({'schema': 'friday.dsh-current-refresh-key.v1',
            'stage': DSH_CURRENT_DECLARATION_SCHEMA, 'previous': previous,
            'declaration_semantic_sha256': fingerprint(_read_reference(current['declaration'])),
            'current': observed})
        return 'ordinary-dsh-current-refresh-' + key
    # The authenticated initial root/profile beforeimage and native capability
    # identify this first edge. Neither a changed D, its path/JSON encoding nor
    # a different request/cycle clock grants a second attempt on that baseline.
    _reference(bundle['root_before']); _reference(bundle['profile_before'])
    if before_configurations is None:
        from hermes_cli.config import fast_safe_load
        before_configurations = tuple(fast_safe_load(_read_reference(bundle[name],
            json_document=False).decode('utf-8-sig'))
            for name in ('root_before', 'profile_before'))
    require(type(before_configurations) is tuple and len(before_configurations) == 2
        and all(type(value) is dict for value in before_configurations),
        'dsh_current_initial_semantic_beforeimage_required')
    native = _read_reference(current['declaration'])['native']
    key = fingerprint({'schema': 'friday.dsh-current-initial-key.v1',
        'root_before_sha256': fingerprint(before_configurations[0]),
        'profile_before_sha256': fingerprint(before_configurations[1]),
        'native': native})
    return 'ordinary-dsh-current-initial-' + key


def dsh_current_consumption_check(preparation, bundle, previous=None):
    """Read-only once check, retaining every legacy raw consumed intent.

    Unresolved legacy partial directories fail closed: no old intent is
    migrated, repaired, removed or silently assigned a fresh clock. The same
    check is required immediately before the atomic primary mkdir.
    """
    preparation = Path(preparation)
    name = dsh_current_transaction_name(bundle, previous)
    target = preparation / name
    require(not os.path.lexists(target), 'worker_declaration_consumed_no_retry')
    if bundle['schema'] != DSH_CURRENT_DECLARATION_SCHEMA or previous is not None:
        return target
    if not os.path.lexists(preparation):
        return target
    info = preparation.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == 0o700 and preparation.resolve() == preparation,
        'dsh_current_consumption_parent_identity')
    count = 0
    for entry in preparation.iterdir():
        if not entry.name.startswith('ordinary-dsh-current-declaration-'):
            continue
        count += 1
        require(count <= 256, 'dsh_current_legacy_consumption_limit')
        state = entry.lstat()
        require(stat.S_ISDIR(state.st_mode) and state.st_uid == os.getuid()
            and stat.S_IMODE(state.st_mode) == 0o700 and entry.resolve() == entry,
            'dsh_current_legacy_consumption_unresolved')
        try:
            def legacy_json(path):
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
                try:
                    first = os.fstat(fd)
                    require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
                        and first.st_nlink == 1 and stat.S_IMODE(first.st_mode) == 0o600
                        and first.st_size <= MAX_SOURCE_BYTES,
                        'dsh_current_legacy_consumption_unresolved')
                    data = os.read(fd, MAX_SOURCE_BYTES + 1)
                    fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_nlink',
                        'st_size', 'st_mtime_ns', 'st_ctime_ns')
                    require(len(data) == first.st_size and all(getattr(first, k)
                        == getattr(os.fstat(fd), k) == getattr(path.lstat(), k) for k in fields),
                        'dsh_current_legacy_consumption_unresolved')
                finally:
                    os.close(fd)
                return _read_reference({'path': str(path),
                    'sha256': hashlib.sha256(data).hexdigest()})
            intent = legacy_json(entry / 'intent.json')
            require(intent.get('state') == 'CONSUMED_NO_RETRY'
                and intent.get('retry_authorized') is False,
                'dsh_current_legacy_consumption_unresolved')
            request = _read_reference(intent['request_reference'])
            require(intent['request_sha256'] == intent['request_reference']['sha256']
                and request['schema'] == DSH_CURRENT_APPLY_SCHEMA
                and _same(intent, {'schema': 'friday.worker-declarations.apply.v1',
                    'state': 'CONSUMED_NO_RETRY', 'request_sha256': intent['request_reference']['sha256'],
                    'request_reference': intent['request_reference'],
                    'request_semantic_sha256': hashlib.sha256((json.dumps(request,
                        sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest(),
                    'clock': _read_reference(request['clock']), 'clock_reference': request['clock'],
                    'previous_input': request['previous_input'], 'current_input': request['current_input'],
                    'before': request['before'], 'ready': False, 'retry_authorized': False,
                    'consumers_started': False, 'workers_enabled': False, 'runtime_acceptance': 'NOT_GRANTED'}),
                'dsh_current_legacy_consumption_unresolved')
            old, _, _ = load_declaration_source(request['declaration_source'])
            require(old['schema'] == DSH_CURRENT_DECLARATION_SCHEMA
                and entry.name == 'ordinary-dsh-current-declaration-'
                    + old['runtime_after']['current_availability']['declaration']['sha256'],
                'dsh_current_legacy_consumption_unresolved')
            # Refresh had a separate semantic namespace even in the legacy
            # implementation; a raw legacy initial key must not assert refresh.
            require('refresh_context' not in old,
                'dsh_current_legacy_consumption_unresolved')
            from hermes_cli.config import fast_safe_load
            old_runtime = old['runtime_after']
            root_home = _absolute(_read_reference(
                old_runtime['current_availability']['declaration'])['native']['authorization_home'])
            own_path = _absolute(old_runtime['runtime_home'])
            own_name = str(own_path.relative_to(root_home)) + '/config.yaml'
            require(_same(old['root_before'], request['before'].get('config.yaml'))
                and _same(old['profile_before'], request['before'].get(own_name)),
                'dsh_current_legacy_consumption_unresolved')
            originals = []
            for document, relative in (('root_before', 'config.yaml'),
                    ('profile_before', own_name)):
                original = old[document]
                archive = entry / 'before' / relative
                ref = ({'path': str(archive), 'sha256': original['sha256']}
                    if os.path.lexists(archive) else original)
                originals.append(fast_safe_load(_read_reference(ref,
                    json_document=False).decode('utf-8-sig')))
            require(dsh_current_transaction_name(old,
                before_configurations=tuple(originals)) != name,
                'worker_declaration_consumed_no_retry')
        except DeclarationError:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            raise DeclarationError('dsh_current_legacy_consumption_unresolved') from None
    current_info = preparation.lstat()
    require((info.st_dev, info.st_ino, info.st_uid, info.st_mode)
        == (current_info.st_dev, current_info.st_ino, current_info.st_uid, current_info.st_mode),
        'dsh_current_consumption_parent_changed')
    return target


def dsh_current_plan(root_config, profile_config, worker_inputs, identity, bundle):
    """Plan the DSH policy declaration edge or its later proof activation.

    This is source data. Current native admission and stopped publication
    custody belong to the existing writer. Historical receipts are preserved.
    """
    from .dsh_current_availability import validate_declaration, validate_proof, checked_cycle
    from .host_runtime import HostUnavailable
    require(type(bundle) is dict and set(bundle) in ({'schema', 'state',
        'root_before', 'profile_before', 'identity_reference', 'changes', 'runtime_after'},
        {'schema', 'state', 'root_before', 'profile_before', 'identity_reference',
            'changes', 'runtime_after', 'refresh_context'})
        and bundle['schema'] in DSH_CURRENT_SCHEMAS
        and bundle['state'] == 'PROPOSED_NOT_APPLIED_NOT_AN_EXECUTABLE_MIGRATION_REQUEST',
        'dsh_current_exact_stage_bundle_required')
    _reference(bundle['identity_reference'])
    home, profile_home = _identity_join(root_config, profile_config, identity, bundle,
        dsh_current=True)
    before_inputs = _at(root_config, TEMPLATE_INPUTS)
    require(_same(before_inputs, worker_inputs),
        'dsh_current_global_worker_inputs_must_remain_unchanged')
    runtime_path = profile_dsh_path(profile_config)
    before_runtime = _at(profile_config, runtime_path)
    after_runtime = bundle['runtime_after']
    require(type(before_runtime) is dict and type(after_runtime) is dict
        and before_runtime.get('enabled') is True and after_runtime.get('enabled') is True
        and before_runtime.get('runtime_home') == after_runtime.get('runtime_home') == str(profile_home)
        and before_runtime.get('runtime_profile') == after_runtime.get('runtime_profile') == profile_home.name,
        'dsh_current_exact_profile_runtime_required')
    rows = bundle['changes']
    require(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict
        and set(rows[0]) == {'document', 'path', 'before_sha256', 'after_reference'}
        and rows[0]['document'] == 'root_config' and rows[0]['path'] == list(TEMPLATE_INPUTS)
        and rows[0]['before_sha256'] == fingerprint(before_inputs),
        'dsh_current_exact_template_row_required')
    _reference(rows[0]['after_reference'])
    current = after_runtime.get('current_availability')
    require(type(current) is dict and set(current) == {'declaration', 'proof', 'cycle'},
        'dsh_current_exact_availability_required')
    _reference(current['declaration'])
    _reference(current['cycle'])
    declaration = _read_reference(current['declaration'])
    native = declaration.get('native') if type(declaration) is dict else None
    require(type(native) is dict and native.get('authorization_home') == str(home)
        and _same(native.get('binding'), identity['binding'])
        and type(native.get('generation')) is int and native['generation'] == identity['generation'],
        'dsh_current_native_declaration_join_changed')
    try:
        new_cycle = checked_cycle(current['cycle'])
        validate_declaration(after_runtime, declaration, check_config=False)
        if bundle['schema'] == DSH_CURRENT_DECLARATION_SCHEMA:
            require(current['proof'] is None, 'dsh_current_t1_pending_proof_required')
            previous = before_runtime.get('current_availability')
            if previous is not None:
                previous = historical_dsh_current(before_runtime, native,
                    source_names=set(declaration['sources']))
                require(previous['cycle']['sha256'] != current['cycle']['sha256'],
                    'dsh_current_refresh_new_cycle_required')
                old_proof = _read_reference(previous['proof'])
                if new_cycle['boot_id'] == old_proof['current']['boot_id']:
                    require(new_cycle['started_mono'] >= old_proof['observed_mono'],
                        'dsh_current_refresh_clock_precedes_old_observation')
                dsh_current_transaction_name(bundle, previous)
            else:
                require('refresh_context' not in bundle,
                    'dsh_current_unexpected_refresh_context')
            restored_runtime = copy.deepcopy(after_runtime)
            if previous is None:
                restored_runtime.pop('current_availability')
            else:
                restored_runtime['current_availability'] = copy.deepcopy(previous)
            for path in DSH_DECLARATION_PATHS:
                old_runtime, new_runtime = _at(before_runtime, path), _at(after_runtime, path)
                for pin in (old_runtime, new_runtime):
                    _reference(pin)
                _replace(restored_runtime, path, old_runtime)
            require(_same(restored_runtime, before_runtime), 'dsh_current_unrelated_runtime_delta')
        else:
            require('refresh_context' not in bundle, 'dsh_current_unexpected_refresh_context')
            require(_same(before_inputs, worker_inputs), 'dsh_current_t2_worker_inputs_changed')
            previous = before_runtime.get('current_availability')
            require(type(previous) is dict and set(previous) == {'declaration', 'proof', 'cycle'}
                and previous['proof'] is None
                and _same(previous['declaration'], current['declaration']),
                'dsh_current_t2_pending_declaration_required')
            _reference(current['proof'])
            restored = copy.deepcopy(after_runtime)
            restored['current_availability']['proof'] = None
            require(_same(restored, before_runtime), 'dsh_current_t2_unrelated_runtime_delta')
            validate_proof(after_runtime, declaration, _read_reference(current['proof']))
    except HostUnavailable:
        raise DeclarationError('dsh_current_evidence_invalid') from None
    root_after, profile_after = copy.deepcopy(root_config), copy.deepcopy(profile_config)
    _replace(root_after, TEMPLATE_INPUTS, worker_inputs)
    _replace(profile_after, runtime_path, after_runtime)
    changes = []
    if not _same(before_inputs, worker_inputs):
        changes.append({'document': 'root_config', 'path': list(TEMPLATE_INPUTS),
            'before_sha256': fingerprint(before_inputs), 'after_sha256': fingerprint(worker_inputs)})
    changes.append({'document': 'profile_config', 'path': list(runtime_path),
        'before_sha256': fingerprint(before_runtime), 'after_sha256': fingerprint(after_runtime)})
    return {'schema': 'friday.worker-declaration-delta.v1',
        'state': 'SOURCE_DECLARATION_DELTA_ONLY_NOT_NATIVE_AUTHORITY',
        'ready': False, 'native_authority': False, 'native_apply_implemented': True,
        'workers_enabled': False, 'dsh_current_stage': bundle['schema'],
        'root_config': root_after, 'profile_config': profile_after,
        'semantic_changes': changes, 'principal': identity['principal'],
        'generation': identity['generation'], 'profile': str(profile_home),
        'launcher': {'reference': copy.deepcopy(_at(worker_inputs,
            ('workers', 'a0', 'a0', 'launcher'))),
            'state': 'UNCHANGED_A0_STOP_CUSTODY_SOURCE_ONLY', 'installed': False},
        'missing_native_prerequisites': list(NATIVE_GAPS)}


def load_declaration_source(companion):
    """Read exact private JSON pins; no public request supplies callbacks."""
    require(type(companion) is dict and set(companion) == {'bundle', 'worker_inputs', 'identity'},
        'worker_declaration_exact_source_companion_required')
    bundle = _read_reference(companion['bundle'])
    identity = _read_reference(companion['identity'])
    inputs = _read_reference(companion['worker_inputs'])
    require(_same(bundle.get('identity_reference'), companion['identity']),
        'worker_declaration_identity_reference_changed')
    rows = bundle.get('changes')
    require(type(rows) is list, 'worker_declaration_change_shape_invalid')
    refs = [row.get('after_reference') for row in rows if type(row) is dict
        and row.get('document') == 'root_config' and row.get('path') == list(TEMPLATE_INPUTS)]
    require(len(refs) == 1 and _same(refs[0], companion['worker_inputs']),
        'worker_declaration_inputs_reference_changed')
    return bundle, inputs, identity


def validate_declaration_source(companion, root_config, profile_config, *, root_home, profile_home):
    """Authenticated Onboarding companion preflight; return redacted proof only.

    The caller owns the signed session, native current_access/generation/proof
    checks and config/admission locks. This function grants none of them. The
    stale attachment is a historical member: its returned digest must match
    the archive engine's exact before-tree inventory. The engine retains that
    custody across rename; this function never guesses a replacement path.
    """
    bundle, inputs, identity = load_declaration_source(companion)
    plan = plan_declaration_delta(root_config, profile_config, inputs, identity, bundle)
    require(Path(root_home) == Path(identity['profile']).parent.parent
        and Path(profile_home) == Path(identity['profile']),
        'worker_declaration_native_home_changed')
    for name, ref in identity['source_refs'].items():
        if name != 'stale_attachment':
            _read_reference(ref, json_document=False)
    return {'schema': 'friday.worker-declaration-source-join.v1',
        'state': plan['state'], 'status': 'SOURCE_JOIN_ONLY_NOT_NATIVE_AUTHORITY',
        'ready': False, 'native_authority': False,
        'native_apply_implemented': plan['native_apply_implemented'],
        'binding_sha256': identity['binding_sha256'],
        'generation': identity['generation'], 'principal': identity['principal'],
        'stale_attachment_sha256': identity['source_refs']['stale_attachment']['sha256'],
        'bundle_sha256': companion['bundle']['sha256'],
        # Semantic JSON fingerprints, never native YAML/raw configuration pins.
        'candidate_root_sha256': fingerprint(plan['root_config']),
        'candidate_profile_sha256': fingerprint(plan['profile_config']),
        'candidate_digest_kind': 'semantic-canonical-json-not-native-yaml-raw',
        'source': copy.deepcopy(companion),
        'semantic_changes': copy.deepcopy(plan['semantic_changes']),
        'delta_sha256': fingerprint(plan['semantic_changes']),
        'launcher_state': plan['launcher']['state'],
        'native_migration': 'NOT_INVOKED',
        'missing_native_prerequisites': list(NATIVE_GAPS)}
