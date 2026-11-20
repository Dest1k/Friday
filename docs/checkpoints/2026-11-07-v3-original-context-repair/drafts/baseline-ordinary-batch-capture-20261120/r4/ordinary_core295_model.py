"""Bind the selected S01 conversation to the configured Core295 model routes."""

from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit


SCOPE_SHA = '85fbcf3e949b99b1b9ea8c670e321eda20563c3f7b3769a15c5b940e07420eed'
ROUTE_ROLES = (
    'hermes_cli/friday_credential_admission.py', 'hermes_cli/config_effective.py',
    'hermes_cli/friday_dashboard_owner.py',
    'hermes_cli/runtime_provider.py', 'hermes_cli/runtime_provider_custom.py',
    'hermes_constants.py', 'gateway/config.py',
    'agent/bounded_context.py', 'agent/context_compressor_multipass.py',
    'gateway/run.py', 'gateway/run_turn.py', 'gateway/session.py',
)


def describe_routes(config, chat, admission):
    from agent.bounded_context import compression_policy_from_config, policy_from_config
    from hermes_cli.runtime_provider import _detect_api_mode_for_url, _parse_api_mode

    overrides = (config.get('platforms') or {}).get('telegram', {}).get('channel_overrides') or {}
    admission.require(isinstance(overrides, dict) and chat not in {str(key) for key in overrides},
                      's01_channel_override_present')
    primary = admission.local_route(config)
    compression = admission._compression_route(config, primary)
    admission.require(compression is not None, 's01_separate_compressor_required')
    main_policy = policy_from_config(config)
    summary_policy = compression_policy_from_config(config)
    admission.require(main_policy is not None and summary_policy is not None, 's01_bounded_route_policies_required')
    routes = {}
    for name, (provider, model, url, _), block, policy, output in (
        ('main', primary, config['model'], main_policy, main_policy.main_max_output_tokens),
        ('compression', compression, config['auxiliary']['compression'], summary_policy,
         summary_policy.compression_output_tokens),
    ):
        registration = config['providers'][provider.split(':', 1)[1]]
        if name == 'main':
            admission.require(registration.get('default_model') in (None, '', model), 's01_provider_model_mismatch')
        mode = (_parse_api_mode(registration.get('api_mode') or registration.get('transport'))
                or _detect_api_mode_for_url(url) or 'chat_completions')
        admission.require(mode == 'chat_completions' and block.get('api_mode', mode) in (None, mode),
                          's01_chat_completions_required')
        policy.assert_route(provider, model, url, mode)
        routes[name] = dict(provider=provider, model=model, mode=mode, port=urlsplit(url).port,
                            context_length=policy.context_length, max_input_tokens=policy.server_max_input_tokens,
                            max_output_tokens=output,
                            endpoint_sha256=sha256(url.encode()).hexdigest())
    return routes


def observe_model(binding, *, scenario, read_reference, load_module):
    source = binding['scope_observer']
    if source['sha256'] != SCOPE_SHA:
        raise ValueError('Exact reviewed Core295 S01 scope observer required')
    scope = load_module(source, '_Root_core295_conversation')
    basis = binding['conversation']['basis']
    observed_scope = scope.observe_scope(basis, scenario=scenario, read_reference=read_reference,
                                         load_module=load_module)
    scope_sha = scope.digest(scope.encode(observed_scope))
    scope.require(scope_sha == binding['conversation']['scope_sha256'], 'S01 conversation scope changed')
    native = load_module(basis['projection_client'], '_Root_core295_route_projection')
    metadata = load_module(basis['namespace_helper'], '_Root_core295_route_paths')
    home, principal = metadata.H, metadata.PRINCIPAL
    root = home / 'hermes-agent'
    profile = home / 'profiles' / principal['profile_name']
    configs = {name: path / 'config.yaml' for name, path in (('root', home), ('profile', profile))}
    manifest = json.loads(native.read(home / scope.RECEIPT_PATHS['receipt']))
    pins = {name: manifest['files'][name]['sha256'] for name in ROUTE_ROLES}

    def recheck_source():
        for role, pin in pins.items():
            scope.require(scope.digest(native.read(root / role)) == pin, 'Core295 route implementation changed')
        scope.require(scope.digest(native.read(home / scope.RECEIPT_PATHS['receipt']))
                      == observed_scope['metadata_sha256']['receipt'], 'Core295 route receipt changed')

    def config_shas():
        return {name: scope.digest(native.read(path)) for name, path in configs.items()}

    def check_persisted_model():
        raw = scope.scoped_rows(home / 'state.db', 'SELECT entry_json FROM gateway_routing '
                                'WHERE scope = ? AND session_key = ?', (str(home / 'sessions'), native.KEY))
        entry = json.loads(raw['entry_json'], object_pairs_hook=native.unique)
        scope.require(entry['session_id'] == native.SID and not entry.get('active_turn_token')
                      and not entry.get('model_override'), 'S01 persisted route changed or has a model override')

    recheck_source()
    config_refs = config_shas()
    check_persisted_model()

    old_path = sys.path[:]
    binary = Path(sys.executable)
    site = binary.parent.parent / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    try:
        sys.path[:0] = [str(root), str(site)]
        admission = importlib.import_module('hermes_cli.friday_credential_admission')
        scope.require(Path(admission.__file__) == root / ROUTE_ROLES[0], 'Installed route admission required')
        from hermes_cli.config_effective import _effective, fast_safe_load
        from hermes_constants import reset_hermes_home_override, set_hermes_home_override

        routes = {}
        for name, path in configs.items():
            admission.private_home(path.parent)
            raw = admission.read_owned(path, private=True)
            scope.require(sha256(raw).hexdigest() == config_refs[name] and b'${' not in raw,
                          'Managed S01 model config changed or requires interpolation')
            config = fast_safe_load(raw.decode('utf-8-sig'))
            scope.require(isinstance(config, dict), 'Managed S01 configuration mapping required')
            token = set_hermes_home_override(str(path.parent))
            try:
                routes[name] = describe_routes(_effective(config), principal['chat_id'], admission)
            finally:
                reset_hermes_home_override(token)
    finally:
        sys.path[:] = old_path
    scope.require(routes['profile'] == routes['root'], 'S01 route differs across gateway and profile')
    current_route = scope.check_route(home, profile, principal, str(scenario['peer_id']), native)
    gateway = native.fresh_native(native.js(home / 'gateway_state.json'))
    scope.require(current_route == observed_scope['route_sha256'] and gateway['quiescent']
                  and gateway['identity'] == observed_scope['gateway_identity']
                  and gateway['generation'] == observed_scope['native_generation'], 'S01 conversation changed')
    scope.require(config_shas() == config_refs,
                  'S01 route differs across gateway and profile or changed while reading')
    check_persisted_model()
    recheck_source()
    return dict(scope_sha256=scope_sha, installed_route_roles=pins, config_sha256=config_refs,
                routes=routes['profile'], persisted_model_override=False, configured_channel_override=False,
                wire_observed=False)


def check_current(binding, *, scenario, read_reference, load_module):
    expected = binding.get('model_sha256')
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError('Exact reviewed Core295 model route pin required')
    observation = observe_model(binding, scenario=scenario, read_reference=read_reference, load_module=load_module)
    raw = (json.dumps(observation, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode()
    if sha256(raw).hexdigest() != expected:
        raise ValueError('S01 configured model route changed')
    return True
