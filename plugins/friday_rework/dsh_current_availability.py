"""DSH current-boot observations, independent of historical qualification.

Q -> R -> D -> pending transaction -> P -> activation is acyclic.  A declaration
or policy is never readiness.  Native user admission and signed configuration
are checked independently, and no proof contains its final config/marker hash.
This module owns no model, service, installer, retry, or per-job authority.
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
import time


DECLARATION = 'friday.dsh-current-declaration.v1'
PROOF = 'friday.dsh-current-observation.v1'
POLICY = 'friday.worker-web.durable-policy.v2'
SOURCE_NAMES = (
    'host_runtime.py', 'user_worker_join.py', 'worker_web.py',
    'runtime_observers.py', 'runtime_containment.py', 'runtime_process.py',
    'runtime_primitives.py', 'dsh_current_availability.py', 'adapters/dsh.py',
    'adapters/dsh_keyless_web.mjs',
    'worker_declarations.py', 'worker_declaration_writer.py', 'stopped_operator.py',
)
HISTORY_NAMES = {'original', 'observation', 'failure', 'completion',
                 'preparation', 'receipt', 'retained'}
HISTORY_REQUALIFICATION = 'friday.dsh-current-history-requalification.v1'
_MISSING_AUXILIARY_EDGES = {
    'retained.cleanup', 'retained.cleanup_control', 'retained.postcheck',
    'retained.returned', 'dsh_refs.clock', 'dsh_refs.returned',
    'safety_refs.acceptance', 'safety_refs.clock', 'safety_refs.observation',
    'safety_refs.returned',
}


def require(value, message):
    if not value:
        from .host_runtime import HostUnavailable
        raise HostUnavailable(message)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def runtime_semantic_digest(config):
    # Only these TWO top-level publication references are non-semantic. Nested
    # fields with either spelling remain bound, including model and limits.
    return fingerprint({k: v for k, v in config.items()
        if k not in ('runtime_receipt', 'current_availability')})


def reference_shape(ref):
    from .host_runtime import _pin
    _pin(ref)
    return ref


def current_shape(value):
    require(type(value) is dict and set(value) == {'declaration', 'proof', 'cycle'},
        'dsh_current_reference_shape')
    reference_shape(value['declaration'])
    reference_shape(value['cycle'])
    if value['proof'] is not None:
        reference_shape(value['proof'])
    return value


def read_reference(ref, *, limit=32 * 1024**2):
    """Pin an owned regular inode; reject duplicate keys, links and read races."""
    from .host_runtime import _pin
    p = _pin(ref).path
    require(p.resolve() == p, 'dsh_current_link_refused')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        first = os.fstat(fd)
        require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
            and first.st_nlink == 1 and not first.st_mode & 0o002
            and (not first.st_mode & 0o020 or any(
                parent.stat().st_uid == os.getuid()
                and stat.S_IMODE(parent.stat().st_mode) == 0o700 for parent in p.parents))
            and first.st_size <= limit, 'dsh_current_reference_identity')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(limit + 1)
        keys = ('st_dev','st_ino','st_uid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
        require(len(data) <= limit and hashlib.sha256(data).hexdigest() == ref['sha256']
            and all(getattr(first,k) == getattr(os.fstat(fd),k) == getattr(p.lstat(),k)
                    for k in keys), 'dsh_current_reference_changed')
        return data
    finally:
        os.close(fd)


def read_json(ref, *, limit=32 * 1024**2):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value, 'dsh_current_duplicate_json')
            value[key] = item
        return value
    return json.loads(read_reference(ref, limit=limit), object_pairs_hook=pairs,
        parse_constant=lambda value: require(False, 'dsh_current_nonfinite_json'))


def verify_reference(ref, *, limit=512 * 1024**2):
    """Large native payloads are hashed in chunks, without retaining a copy."""
    from .host_runtime import _pin
    p = _pin(ref).path
    require(p.resolve() == p, 'dsh_current_link_refused')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        first = os.fstat(fd)
        require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
            and first.st_nlink == 1 and not first.st_mode & 0o002
            and (not first.st_mode & 0o020 or any(parent.stat().st_uid == os.getuid()
                and stat.S_IMODE(parent.stat().st_mode) == 0o700 for parent in p.parents))
            and first.st_size <= limit, 'dsh_current_reference_identity')
        digest = hashlib.sha256(); count = 0
        while True:
            chunk = os.read(fd,1024**2)
            if not chunk: break
            count += len(chunk)
            require(count <= limit, 'dsh_current_reference_too_large')
            digest.update(chunk)
        keys = ('st_dev','st_ino','st_uid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
        require(count == first.st_size and digest.hexdigest() == ref['sha256']
            and all(getattr(first,k) == getattr(os.fstat(fd),k) == getattr(p.lstat(),k)
                for k in keys), 'dsh_current_reference_changed')
    finally:
        os.close(fd)
    return ref


def pin(path):
    path = Path(path)
    ref = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    read_reference(ref)
    return ref


def source_pins():
    root = Path(__file__).parent
    result = {'plugins/friday_rework/' + name: pin(root / name) for name in SOURCE_NAMES}
    import tools.web_profile as profile
    result['tools/web_profile.py'] = pin(Path(profile.__file__))
    # Bind the actual typed native consumers independently of their mutable
    # config/marker afterimages. No current config fingerprint enters D or P.
    import importlib
    for name in ('friday_user_scope','config','config_effective','friday_product_access'):
        module = importlib.import_module('hermes_cli.' + name)
        result['hermes_cli/' + name + '.py'] = pin(Path(module.__file__))
    return result


def runtime_input_pins(config):
    d = config['dsh']; web = d['web']
    return {**{key: copy.deepcopy(d[key]) for key in ('node','cli','patch')},
        **{'native_' + str(i): copy.deepcopy(ref) for i,ref in enumerate(d['native_files'])},
        **{'web_' + key: copy.deepcopy(web[key])
            for key in ('resolver','trust_bundle','egress_evidence','research_policy')}}


def durable_policy(web, home, profile):
    """A reviewed durable declaration, never a current network observation."""
    from urllib.parse import urlsplit
    import ipaddress
    value = read_json({'path': str(web.egress_evidence.path),
        'sha256': web.egress_evidence.sha256}, limit=16000)
    require(stat.S_IMODE(web.egress_evidence.path.stat().st_mode) in (0o400,0o600),
        'dsh_durable_policy_private_required')
    fields = {'schema','runtime_home','runtime_profile','authority_id','generation',
        'web_profile','allow_public_https','document_probes'}
    require(type(value) is dict and set(value) == fields and value['schema'] == POLICY
        and value['runtime_home'] == home and value['runtime_profile'] == profile
        and value['web_profile'] == web.profile and value['allow_public_https'] is True
        and type(value['authority_id']) is str
        and re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',value['authority_id']) is not None
        and type(value['generation']) is int and value['generation'] > 0
        and type(value['document_probes']) is list
        and 1 <= len(value['document_probes']) <= 2, 'dsh_durable_policy_invalid')
    for text in value['document_probes']:
        require(type(text) is str and 0 < len(text) <= 1024
            and not any(ord(c) <= 32 for c in text) and '%' not in text and '\\' not in text,
            'dsh_durable_probe_invalid')
        u = urlsplit(text)
        try:
            ipaddress.ip_address(u.hostname or '')
        except ValueError:
            pass
        else:
            require(False, 'dsh_durable_probe_literal_address')
        require(u.scheme == 'https' and u.username is None and u.password is None
            and u.port is None and not u.query and not u.fragment and u.hostname
            and re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)+',u.hostname) is not None
            and text == 'https://' + u.hostname + u.path, 'dsh_durable_probe_invalid')
    require(len(set(value['document_probes'])) == len(value['document_probes']),
        'dsh_durable_probe_duplicate')
    return value


def identity():
    st = Path('/proc/self/ns/net').stat()
    return {'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'net_namespace': [st.st_dev,st.st_ino]}


def _native(config, native, *, check_config):
    from hermes_cli import friday_user_scope as scope
    from .host_runtime import select_runtime
    require(type(native) is dict and set(native) == {'authorization_home','binding',
        'generation','directory_identity'}, 'dsh_current_native_shape')
    home = Path(config['runtime_home']); binding = native['binding']
    require(type(binding) is dict and binding.get('runtime_profile') == config['runtime_profile']
        and type(native['generation']) is int and native['generation'] > 0
        and type(native['directory_identity']) is list and len(native['directory_identity']) == 2
        and all(type(value) is int and value > 0 for value in native['directory_identity']),
        'dsh_current_native_identity')
    from .host_runtime import _path
    root = Path(_path(native['authorization_home']))
    require(home == root / 'profiles' / config['runtime_profile'], 'dsh_current_foreign_home')
    principal = tuple(binding[k] for k in ('platform','transport_profile','account_id','user_id'))
    with scope.authority(home):
        cap = scope.UserScope(root,home,config['runtime_profile'],principal,copy.deepcopy(binding),
            tuple(native['directory_identity']),native['generation']).check()
        if check_config:
            from hermes_cli.config import require_readable_config_before_write
            own = require_readable_config_before_write(home / 'config.yaml')
            current = own['plugins']['entries']['friday_rework']['settings']['runtime']
            require(select_runtime(current,'dsh') == config, 'dsh_current_signed_runtime_changed')
        cap.check()
    return cap


def _static(config):
    d = config['dsh']
    return {key: d[key] for key in ('payload_root','toolchain_root','node','cli','patch',
        'native_files','profile')}


def _history(config, history, native):
    """Reconcile the accepted failure/completion edge without reopening it."""
    require(type(history) is dict and HISTORY_NAMES <= set(history)
        and set(history) <= HISTORY_NAMES | {'preparation_provenance', 'current_requalification'}
        and type(history['retained']) is dict, 'dsh_current_history_shape')
    values = {name: read_json(history[name]) for name in HISTORY_NAMES - {'retained'}}
    if 'current_requalification' not in history:
        for ref in history['retained'].values(): read_reference(ref)
    old, obs, fail, completed = (values[k] for k in ('original','observation','failure','completion'))
    require(old.get('schema') == 'friday.user-worker-qualification.v1'
        and old.get('home') == config['runtime_home'] and old.get('profile') == config['runtime_profile']
        and old.get('binding') == native['binding'] and old.get('generation') == native['generation']
        and old.get('binding_sha256') == fingerprint(native['binding'])
        and fail.get('state') == 'STOP_UNCONFIRMED'
        and fail.get('original_attempt') == old.get('original_attempt'), 'dsh_current_original_history_changed')
    edge = obs.get('post_a0_completion', {})
    require(obs.get('schema') == 'friday.worker-deployment-observation.v1'
        and obs.get('home') == config['runtime_home'] and obs.get('profile') == config['runtime_profile']
        and obs.get('effects') == 'OBSERVATION_ONLY' and obs.get('per_job_authority') == 'NOT_GRANTED'
        and obs.get('original') == history['original']
        and edge.get('schema') == 'friday.r481.post-a0-completion.v1'
        and edge.get('original') == history['completion']
        and edge.get('retained',{}).get('original') == history['original']
        and edge.get('retained',{}).get('local_failure') == history['failure']
        and completed.get('schema') == edge['schema']
        and completed.get('retained') == edge['retained']
        and completed.get('binding') == native['binding']
        and completed.get('binding_sha256') == old['binding_sha256']
        and completed.get('generation') == native['generation']
        and completed.get('old_attempt_reopened') is False
        and completed.get('A0_start_repeated') is False
        and completed.get('original_attempt') != old['original_attempt'],
        'dsh_current_completion_history_changed')
    # Exact historical preparation may be retained at another path. Its SHA
    # remains the original SHA; current prepared input is never repinned here.
    expected = old['preparations']['dsh']
    require(history['preparation']['sha256'] == expected['sha256']
        and completed['preparations']['dsh'] == expected,
        'dsh_current_historical_preparation_changed')
    if history['preparation'] != expected:
        provenance = history.get('preparation_provenance')
        require(type(provenance) is dict and set(provenance) == {'intent','committed'},
            'dsh_current_preparation_provenance_required')
        intent = read_json(provenance['intent']); committed = read_json(provenance['committed'])
        parent = Path(provenance['intent']['path']).parent
        require(Path(provenance['intent']['path']).name == 'intent.json'
            and Path(provenance['committed']['path']) == parent/'committed.json'
            and Path(history['preparation']['path']) == parent/'before/dsh.json'
            and intent.get('schema') == 'friday.worker-declarations.secondary-policy-successor.postboot-current.v1'
            and committed.get('schema') == intent['schema']
            and intent.get('state') == 'CONSUMED_NO_RETRY'
            and intent.get('resume_allowed') is False
            and intent.get('request',{}).get('before',{}).get('dsh') == expected
            and intent['request'].get('home') == native['authorization_home']
            and intent['request'].get('profile') == config['runtime_profile']
            and committed.get('state') == 'POLICY_ONLY_SUCCESSOR_COMMITTED'
            and committed.get('beforeimages',{}).get('dsh') == history['preparation']
            and committed.get('clock') == intent.get('clock')
            and committed.get('resume_allowed') is False
            and committed.get('runtime_acceptance') == 'NOT_GRANTED'
            and committed.get('workers_enabled') is False
            and committed.get('consumers_started') is False
            and committed.get('qualification_started') is False,
            'dsh_current_preparation_provenance_changed')
    prepared = values['preparation']; before = prepared['runtime']
    require(prepared.get('principal_binding_sha256') == old['binding_sha256']
        and prepared.get('generation') == native['generation']
        and _static(before) == _static(config), 'dsh_current_static_smoke_inputs_changed')
    receipt = values['receipt']
    require(receipt.get('schema') == 'friday-rework.dsh-runtime.v1' and receipt.get('ready') is True
        and history['receipt'] == config['runtime_receipt']
        and history['observation'] in receipt.get('evidence',[]), 'dsh_current_baseline_receipt_changed')
    smoke = obs['workers']['dsh']['smoke']
    require([row['kind'] for row in smoke] == ['version','help','headless-config','headless-help']
        and all(type(row['observation'].get('returncode')) is int
            and row['observation']['returncode'] == 0 and row['observation'].get('reaped') is True
            and row['observation'].get('timeout') is False for row in smoke),
        'dsh_current_historical_smoke_unverified')
    # Every completion edge that is retained is exact and remains present;
    # these are historical reads, never a claim of current environmental safety.
    required_refs = {}
    for name,ref in completed['retained'].items(): required_refs['retained.' + name] = ref
    for group in ('dsh_refs','safety_refs'):
        for name,ref in completed[group].items(): required_refs[group + '.' + name] = ref
    require(history['retained'] == required_refs, 'dsh_current_retained_graph_changed')
    if 'current_requalification' in history:
        _history_requalification(history, values, required_refs, native)
    return values


def _history_requalification(history, values, required_refs, native):
    """New current evidence can coexist with an explicitly incomplete archive.

    This is a separate DSH-only provenance mode, never a fallback from failed
    legacy reads. Every original edge remains bound to the canonical completion.
    Missing auxiliary evidence grants no old PASS, cessation or per-job authority.
    Current cessation/safety/network are independently required by T1/P/T2.
    """
    mode = history['current_requalification']
    require(type(mode) is dict and set(mode) == {'schema', 'purpose',
        'historical_graph_integrity', 'missing_as_of', 'recovery_provenance',
        'edges', 'static_smoke'} and mode['schema'] == HISTORY_REQUALIFICATION
        and mode['purpose'] == 'DSH_CURRENT_ONLY_NO_HISTORICAL_REACCEPTANCE'
        and mode['historical_graph_integrity'] == 'INCOMPLETE'
        and type(mode['missing_as_of']) is str
        and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+]03:00',
            mode['missing_as_of']) is not None
        and type(mode['edges']) is dict and set(mode['edges']) == set(required_refs),
        'dsh_current_requalification_shape')
    # The bounded recovery report is retained provenance, not native authority.
    read_json(mode['recovery_provenance'])
    missing = set(); copies = set(); verified = {}
    for edge, expected in required_refs.items():
        reference_shape(expected)
        item = mode['edges'][edge]
        require(type(item) is dict and set(item) == {'reference', 'state', 'copy'}
            and item['reference'] == expected, 'dsh_current_requalification_edge_changed')
        state = item['state']
        if state == 'VERIFIED_ORIGINAL':
            require(item['copy'] is None, 'dsh_current_original_alias_refused')
            read_reference(expected); verified[edge] = expected
        elif state == 'VERIFIED_EXACT_COPY':
            alias = item['copy']; reference_shape(alias)
            require(alias['sha256'] == expected['sha256'] and alias['path'] != expected['path']
                and alias['path'] not in copies, 'dsh_current_exact_copy_changed')
            copies.add(alias['path']); read_reference(alias); verified[edge] = alias
            # If the original has reappeared, corruption or unsafe custody still
            # refuses. Never silently prefer an alias over a damaged original.
            try:
                Path(expected['path']).lstat()
            except FileNotFoundError:
                pass
            else:
                read_reference(expected)
        elif state == 'MISSING_AS_OF':
            require(edge in _MISSING_AUXILIARY_EDGES and item['copy'] is None,
                'dsh_current_required_history_missing')
            missing.add(edge)
            # ENOENT is a disclosed archive gap. Permission/link/hash failures
            # of a present original are not missing evidence and must refuse.
            try:
                Path(expected['path']).lstat()
            except FileNotFoundError:
                pass
            else:
                read_reference(expected)
        else:
            require(False, 'dsh_current_requalification_state_unknown')
    require(bool(missing), 'dsh_current_incomplete_history_without_gaps')
    smoke = mode['static_smoke']
    require(type(smoke) is dict and set(smoke) == {'observation', 'canonical_observation', 'reuse'}
        and smoke['observation'] == verified.get('dsh_refs.observation')
        and smoke['canonical_observation'] == history['observation']
        and smoke['reuse'] == 'EXACT_SAME_STATIC_INPUTS_ONLY',
        'dsh_current_static_reuse_provenance_changed')
    stage = read_json(smoke['observation'])
    require(stage.get('schema') == 'friday.user-worker-stage-observation.v1'
        and stage.get('kind') == 'dsh' and stage.get('effects') == 'OBSERVATION_ONLY'
        and stage.get('per_job_authority') == 'NOT_GRANTED'
        and stage.get('generation') == native['generation']
        and stage.get('observation', {}).get('smoke') == values['observation']['workers']['dsh']['smoke'],
        'dsh_current_recovered_static_smoke_changed')


def history_custody_references(config, history, native):
    """Physical inputs and disclosed original absences for stopped custody.

    Validate the entire immutable graph first. Original historical pointers
    remain in D, while the native operator retains only verified physical bytes
    and exact-copy donors. An absent auxiliary pointer is tracked as absent,
    never treated as a readable pin or skipped elsewhere in the declaration.
    """
    _history(config, history, native)
    references = [history[name] for name in HISTORY_NAMES - {'retained'}]
    references.extend(history.get('preparation_provenance', {}).values())
    mode = history.get('current_requalification')
    if mode is None:
        references.extend(history['retained'].values())
        return references, []
    references.append(mode['recovery_provenance'])
    absent = []
    for item in mode['edges'].values():
        expected = item['reference']
        if item['state'] == 'VERIFIED_ORIGINAL':
            references.append(expected)
            continue
        if item['state'] == 'VERIFIED_EXACT_COPY':
            references.append(item['copy'])
        # An optional original may already have been recovered. Retain it in
        # that case; only ENOENT represents the explicitly disclosed absence.
        try:
            Path(expected['path']).lstat()
        except FileNotFoundError:
            absent.append(expected)
        else:
            references.append(expected)
    return references, absent


def validate_declaration(config, declaration, *, binding=None, generation=None, check_config=False):
    from .host_runtime import validate_runtime, _dsh_web
    c = validate_runtime(config)
    require('a0' not in c and 'current_availability' in c, 'dsh_current_dsh_only')
    d = declaration
    require(type(d) is dict and set(d) == {'schema','runtime_home','runtime_profile','runtime_sha256',
        'policy','policy_authority','native','sources','inputs','history'}
        and d['schema'] == DECLARATION and d['runtime_home'] == c['runtime_home']
        and d['runtime_profile'] == c['runtime_profile']
        and d['runtime_sha256'] == runtime_semantic_digest(c)
        and d['policy'] == c['dsh']['web']['egress_evidence'], 'dsh_current_declaration_changed')
    if binding is not None: require(d['native']['binding'] == binding, 'dsh_current_binding_changed')
    if generation is not None: require(d['native']['generation'] == generation, 'dsh_current_generation_changed')
    policy = durable_policy(_dsh_web(c['dsh']),c['runtime_home'],c['runtime_profile'])
    require(d['policy_authority'] == {'id':policy['authority_id'],'generation':policy['generation']},
        'dsh_current_policy_authority_changed')
    require(d['sources'] == source_pins() and d['inputs'] == runtime_input_pins(c),
        'dsh_current_source_or_input_changed')
    for ref in d['inputs'].values(): verify_reference(ref)
    _dsh_web(c['dsh']).checked_patch(read_reference(c['dsh']['patch']))
    _native(c,d['native'],check_config=check_config)
    _history(c,d['history'],d['native'])
    return d


def _execution(value, config, folder, current, clock, *, seconds):
    envelope = value.get('resource_envelope',{})
    require(type(value) is dict and type(value.get('returncode')) is int
        and value['returncode'] == 0 and value.get('timeout') is False
        and value.get('reaped') is True and type(envelope) is dict
        and set(envelope) == {'unit','memory_bytes','cpu_percent','tasks','boot_id','deadline'}
        and envelope['unit'] == 'friday-qualify-dsh-' + hashlib.sha256(str(folder).encode()).hexdigest()[:24] + '-1.scope'
        and all(envelope[k] == config['dsh'][k] for k in ('memory_bytes','cpu_percent','tasks'))
        and envelope['boot_id'] == current['boot_id'] and type(envelope['deadline']) in (int,float)
        and math.isfinite(envelope['deadline'])
        and clock['started_mono'] < envelope['deadline'] <= clock['deadline_mono'] - 30,
        'dsh_current_native_execution_unverified')
    # The actual observer enforces the 20/5-second subprocess limit. The signed
    # proof retains that cap explicitly, independently of the operation budget.
    require(type(value.get('current_cap_seconds')) is int and value['current_cap_seconds'] == seconds,
        'dsh_current_native_cap_changed')


def checked_clock(ref, *, active=False):
    clock = read_json(ref)
    require(type(clock) is dict and set(clock) == {'schema','boot_id','started_mono','deadline_mono','seconds','stage_folder'}
        and clock['schema'] == 'friday.dsh-current-observation.clock.v1'
        and type(clock['seconds']) is int and 30 <= clock['seconds'] <= 180
        and all(type(clock[k]) in (int,float) and math.isfinite(clock[k]) for k in ('started_mono','deadline_mono'))
        and clock['started_mono'] >= 0
        and abs(clock['deadline_mono'] - clock['started_mono'] - clock['seconds']) < .001
        and clock['boot_id'] == identity()['boot_id'], 'dsh_current_original_clock_changed')
    from .host_runtime import _path
    _path(clock['stage_folder'])
    if active:
        require(clock['started_mono'] <= time.monotonic() < clock['deadline_mono'] - 30,
            'dsh_current_original_clock_expired')
    return clock


def checked_cycle(ref):
    """Historical T1 clock identity, signed into the pending/active config.

    Its expired deadline cannot terminate a healthy service. The separate
    observer clock owns fresh effects; the cycle prevents old-P reactivation.
    """
    value = read_json(ref)
    require(type(value) is dict and set(value) == {'schema','boot_id','started_mono','deadline_mono','seconds'}
        and value['schema'] == 'friday.worker-declarations.clock.v1'
        and type(value['boot_id']) is str
        and type(value['seconds']) is int and 30 <= value['seconds'] <= 180
        and all(type(value[k]) in (int,float) and math.isfinite(value[k]) for k in ('started_mono','deadline_mono'))
        and value['started_mono'] >= 0
        and abs(value['deadline_mono'] - value['started_mono'] - value['seconds']) < .001,
        'dsh_current_cycle_changed')
    return value


def validate_proof(config, declaration, proof):
    from .host_runtime import _dsh_web
    from .worker_web import checked_network_observation
    from .runtime_observers import checked_dsh_safety, DSH_NATIVE_SAFETY
    p = proof
    require(type(p) is dict and set(p) == {'schema','effects','per_job_authority','declaration',
        'runtime_sha256','policy','native','sources','inputs','current','clock','observed_mono',
        'pending_transaction','folder','safety','network','cycle'} and p['schema'] == PROOF
        and p['effects'] == 'OBSERVATION_ONLY' and p['per_job_authority'] == 'NOT_GRANTED'
        and p['declaration'] == config['current_availability']['declaration']
        and p['cycle'] == config['current_availability']['cycle']
        and p['runtime_sha256'] == declaration['runtime_sha256'] and p['policy'] == declaration['policy']
        and fingerprint(p['native']) == fingerprint(declaration['native']) and p['sources'] == declaration['sources']
        and p['inputs'] == declaration['inputs'] and p['current'] == identity(), 'dsh_current_proof_changed')
    clock = checked_clock(p['clock'])
    cycle = checked_cycle(p['cycle'])
    require(type(p['observed_mono']) in (int,float) and math.isfinite(p['observed_mono'])
        and clock['started_mono'] <= p['observed_mono'] < clock['deadline_mono']
        and cycle['started_mono'] <= clock['started_mono']
        and p['observed_mono'] <= time.monotonic(), 'dsh_current_proof_interval_changed')
    require(cycle['boot_id'] == p['current']['boot_id'],
        'dsh_current_cycle_boot_changed')
    checked_pending(p['pending_transaction'],p['declaration'],p['runtime_sha256'],p['cycle'],
        config=config, observation_started_mono=clock['started_mono'])
    from .host_runtime import _path
    folder = Path(_path(p['folder']))
    require(folder.resolve() == folder and str(folder) == clock['stage_folder'],
        'dsh_current_observation_folder_changed')
    safety = p['safety']; network = p['network']
    require(type(safety['report'].get('shell_result',{}).get('exitCode')) is int,
        'dsh_current_safety_exit_type')
    checked_dsh_safety(safety['report'],config,Path(config['runtime_home']))
    require(safety['specimen_sha256'] == hashlib.sha256(DSH_NATIVE_SAFETY.encode()).hexdigest(),
        'dsh_current_safety_specimen_changed')
    _execution(safety['execution'],config,folder/'dsh-safety',p['current'],clock,seconds=20)
    policy = durable_policy(_dsh_web(config['dsh']),config['runtime_home'],config['runtime_profile'])
    urls = [('https://mcp.exa.ai/' if policy['web_profile'] == 'exa-keyless' else 'https://api.exa.ai/'),
        *policy['document_probes']]
    require(set(network) == {'network','network_execution','policy_sha256'}
        and network['policy_sha256'] == declaration['policy']['sha256'], 'dsh_current_network_changed')
    checked_network_observation(json.dumps(network['network']),urls)
    _execution(network['network_execution'],config,folder/'dsh-network',p['current'],clock,seconds=5)
    return p


def checked_pending(reference, declaration_reference, runtime_sha256, cycle,
        *, config, observation_started_mono=None):
    from .worker_declaration_writer import checked_dsh_current_commit
    from .worker_declarations import DeclarationError
    try:
        return checked_dsh_current_commit(reference, declaration_reference, runtime_sha256,
            cycle, config=config, observation_started_mono=observation_started_mono)
    except (DeclarationError, OSError, ValueError, KeyError, TypeError):
        require(False, 'dsh_current_pending_transaction_unverified')


def validate_current(config, *, binding=None, generation=None, allow_pending=False, check_config=True):
    current = current_shape(config.get('current_availability'))
    checked_cycle(current['cycle'])
    declaration = read_json(current['declaration'])
    validate_declaration(config,declaration,binding=binding,generation=generation,check_config=check_config)
    if current['proof'] is None:
        require(allow_pending, 'dsh_current_observation_pending')
        return {'declaration':declaration,'proof':None}
    proof = read_json(current['proof'])
    validate_proof(config,declaration,proof)
    return {'declaration':declaration,'proof':proof}


def observe_current(config, *, clock_reference, pending_transaction, folder, verify):
    """One explicitly owned no-model operation; publishes no activation grant.

    Caller retains the existing native operator authority. This constructor
    validates the pending signed config without asking it to be already ready.
    Stage is create-only; a partial/UNKNOWN result is never retried in place.
    """
    from .runtime_containment import Budget
    from .runtime_observers import dsh_observe
    require(callable(verify), 'dsh_current_native_operator_required')
    clock = checked_clock(clock_reference,active=True)
    require(checked_cycle(config['current_availability']['cycle'])['started_mono'] <= clock['started_mono'],
        'dsh_current_observation_precedes_cycle')
    budget = Budget(clock['seconds'],started=clock['started_mono'],deadline=clock['deadline_mono'])
    def check():
        verify(); budget.check(reserve=30)
        value = validate_current(config,allow_pending=True)
        require(value['proof'] is None, 'dsh_current_pending_configuration_required')
        require(checked_cycle(config['current_availability']['cycle'])['boot_id'] == identity()['boot_id'],
            'dsh_current_cycle_boot_changed')
        verify(); budget.check(reserve=30)
        return value['declaration']
    declaration = check()
    checked_pending(pending_transaction,config['current_availability']['declaration'],
        declaration['runtime_sha256'],config['current_availability']['cycle'],
        config=config, observation_started_mono=clock['started_mono'])
    folder = Path(folder)
    require(str(folder) == clock['stage_folder'] and folder.is_absolute()
        and folder.resolve() == folder and not os.path.lexists(folder),
        'dsh_current_new_observation_folder_required')
    folder.mkdir(mode=0o700)
    for name in ('dsh-safety','dsh-network'): (folder/name).mkdir(mode=0o700)
    current = identity()
    safety = dsh_observe(config,Path(config['runtime_home']),folder/'dsh-safety',budget,
        safety_only=True,current_policy=True)
    safety['execution']['current_cap_seconds'] = 20
    check()
    network = dsh_observe(config,Path(config['runtime_home']),folder/'dsh-network',budget,
        network_only=True,current_policy=True)
    network['network_execution']['current_cap_seconds'] = 5
    check()
    require(identity() == current, 'dsh_current_changed_during_observation')
    value = {'schema':PROOF,'effects':'OBSERVATION_ONLY','per_job_authority':'NOT_GRANTED',
        'declaration':copy.deepcopy(config['current_availability']['declaration']),
        'cycle':copy.deepcopy(config['current_availability']['cycle']),
        'runtime_sha256':declaration['runtime_sha256'],'policy':declaration['policy'],
        'native':declaration['native'],'sources':declaration['sources'],'inputs':declaration['inputs'],
        'current':current,'clock':clock_reference,'observed_mono':time.monotonic(),
        'pending_transaction':pending_transaction,'folder':str(folder),'safety':safety,'network':network}
    validate_proof(config,declaration,value)
    target = folder/'observation.json'
    raw = (json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    fd = os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out: out.write(raw); out.flush(); os.fsync(out.fileno())
    check()
    return pin(target)
