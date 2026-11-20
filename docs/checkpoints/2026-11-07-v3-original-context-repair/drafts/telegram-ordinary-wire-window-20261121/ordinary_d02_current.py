"""Observe the selected D02 ordinary route without taking a product action."""

from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import re
import sys
import time

PHASES = (
    '088d47d6a8efbf63068bb8fff13c69af05478a20156960811ac1d170db46c4cf',
    'bab05e12b1465b984bf58acfd8b25507162b31c135dbb3623623951a06b10a05',
)
SOURCE_NAME = 'D02-Mednaya-otmel-v1.odt'
SOURCE_SHA = 'bae9af5c7d9d9a1ed4c4d6ebde175ea37d852209b1ab9f689569f78503e4d953'
RETAINED_UPLOAD_SHA = '7fb0da6af7b963f9e64ac1aa2a5320f6392429f52e1a36539d7b1e6649baf1e5'
RECEIVER_ROOT = Path('/home/jericho/.local/share/friday-telegram-bot-test')
HELPER_PINS = {
    'io': 'e7360483db530bfb47da5e871dc4774341dd06831c2071755818a29bd462174d',
    'route': 'ac30ed03842e37eb6844321187ad6f0d7e8c03096bc0c38e031a6f4ba014e0f8',
    'projection': 'bd465b9664851e061b7a1ea69ed01a53d0fd40b075c7664d394c855e548b45b1',
}
INSTALL_PATHS = {'receipt': 'hermes-agent.source.json', 'marker': 'FRIDAY-INSTALL.json',
                 'stamp': 'hermes-agent/install-stamp.json'}
ROLES = (
    'gateway/ordinary_turn_projection.py', 'gateway/control_socket.py', 'gateway/host_rendezvous.py',
    'gateway/run.py', 'gateway/platforms/base.py',
    'gateway/pairing.py', 'gateway/session_identity.py', 'gateway/profile_routing.py',
    'gateway/run_inbound_consumer.py', 'gateway/run_attachment_presentation.py',
    'gateway/upload_anchor.py', 'gateway/admitted_ingress.py', 'hermes_state.py', 'hermes_state_messages.py',
    'hermes_cli/config.py', 'hermes_cli/friday_user_scope.py',
    'hermes_cli/friday_product_access.py', 'hermes_cli/plugins_state.py', 'hermes_cli/friday_native_state.py',
    'plugins/platforms/telegram/adapter.py', 'plugins/platforms/telegram/telegram_held_inbound.py',
    'tools/file_tools.py', 'tools/session_search_tool.py',
)
OVERLAY_ROLES = ('plugins/friday_rework/__init__.py', 'plugins/friday_rework/admission.py')
RECEIVER_ROLES = ('gateway/d02_receiver_control.py', 'gateway/d02_receiver_state.py',
                  'gateway/ordinary_dm_ingress.py', 'gateway/ordinary_dm_dispatch_closure.py',
                  'plugins/platforms/telegram/telegram_receive_window.py')


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def install_inputs(io, home, expected):
    need(set(expected['metadata_sha256']) == set(INSTALL_PATHS), 'D02 exact installed metadata pins required')
    result = {}
    for key, relative in INSTALL_PATHS.items():
        raw = io.checked_read(home / relative, limit=24 * 1024**2, private=False)
        need(digest(raw) == expected['metadata_sha256'][key], 'D02 installed metadata changed')
        result[key] = io.decode(raw)
    return result['receipt'], result['marker'], result['stamp']


def installed_roles(io, root, expected, projection):
    manifest, marker, stamp = install_inputs(io, root, expected)
    source = root / 'hermes-agent'
    receipt_pin = expected['metadata_sha256']['receipt']
    need(manifest['schema'] == 'friday.hermes-source.v1'
         and len(manifest['layers']) == expected['layer_count']
         and stamp['commit'] == manifest['commit']
         and stamp['fridaySource'] == {'baseTree': manifest['base_tree'], 'layers': manifest['layers']}
         and marker['schema'] == 'friday.native-install.v1' and marker['completion_stage'] == 'TELEGRAM_ORDINARY'
         and marker['home'] == str(root) and marker['source'] == str(source)
         and marker['source_receipt_sha256'] == marker['ordinary_gateway']['source_receipt_sha256'] == receipt_pin,
         'D02 installed source, route marker and stamp disagree')
    receiver = set(RECEIVER_ROLES).issubset(manifest['files'])
    need(receiver or not set(RECEIVER_ROLES).intersection(manifest['files']),
         'D02 receiver sources are only partially present')
    paths = ROLES + (RECEIVER_ROLES if receiver else ())
    pins = {}
    for name in paths:
        raw = io.checked_read(source / name, limit=4 * 1024**2, private=False)
        leaf = manifest['files'][name]
        need(len(raw) == leaf['bytes'] and digest(raw) == leaf['sha256'], 'D02 installed ordinary source role changed')
        pins[name] = leaf['sha256']
    overlay = OVERLAY_ROLES + (('plugins/friday_rework/d02_wire_receipts.py',) if receiver else ())
    for name in overlay:
        raw = io.checked_read(root / name, limit=4 * 1024**2)
        need(digest(raw) == marker['plugin_files'][name], 'D02 actual Friday plugin overlay changed')
        pins[name] = marker['plugin_files'][name]
    need(pins['gateway/ordinary_turn_projection.py'] == projection.NATIVE_SHA,
         'D02 native projection implementation changed')
    overlay_pin = digest(json.dumps(marker['plugin_files'], sort_keys=True).encode())
    return manifest['commit'], pins, receiver, overlay_pin


def permission(io, route, root, lane, principal, account):
    from hermes_cli import friday_product_access as access, friday_user_scope as scope
    from hermes_cli.config import load_config_storage_readonly
    from hermes_cli.plugins_state import PluginState

    uid = principal['user_id']
    key = access.principal_id('telegram', 'default', account, uid)
    with scope.authority(root):
        policy = scope.policy(root)
        accounts = [item for item in access.access_policy()['accounts']
                    if (item['platform'], item['transport_profile'], item['account_id'])
                    == ('telegram', 'default', account)]
        state = access.current_access(PluginState('friday_rework'))
        config = load_config_storage_readonly()['gateway']
    bindings = [item for item in policy['bindings'] if access.principal_id(
        *(item[k] for k in ('platform', 'transport_profile', 'account_id', 'user_id'))) == key]
    row = state['users'].get(key)
    need(len(accounts) == len(bindings) == 1 and lane.name in accounts[0]['runtime_profiles']
         and bindings[0]['runtime_profile'] == lane.name and 'read_file' in bindings[0]['tools']
         and row is not None and row['enabled'] is True and row['role'] == 'user'
         and type(row['generation']) is int and row['generation'] > 0,
         'D02 enabled ordinary account, profile and reader required')
    grant = bindings[0]
    onboarding_raw = io.checked_read(lane / scope.ONBOARDING, limit=32768)
    marker = io.decode(io.checked_read(lane / scope.MARKER, limit=32768))
    onboarding = io.decode(onboarding_raw)
    expected = dict(schema='friday.user-home.v1', principal=key, profile=lane.name,
                    binding_sha256=scope._fingerprint(grant), onboarding_sha256=digest(onboarding_raw))
    need(marker == expected and onboarding['schema'] == 'friday.onboarding.v1'
         and onboarding['binding_sha256'] == expected['binding_sha256']
         and onboarding['directory_identity'] == list(io.identity(lane, directory=True)[:2])
         and onboarding['authorization_home'] == str(root)
         and digest(io.checked_read(lane / 'config.yaml', limit=4 * 1024**2)) == onboarding['config_sha256']
         and digest(io.checked_read(lane / 'SOUL.md', limit=2 * 1024**2)) == onboarding['soul_sha256'],
         'D02 selected onboarding lineage changed')
    routes = [item for item in config['profile_routes'] if item.get('platform') == 'telegram'
              and (item.get('bot_profile') or 'default') == 'default' and item.get('user_id') == uid]
    need(config['multiplex_profiles'] is True and routes == [
        dict(name='friday-' + key, platform='telegram', bot_profile='default',
             user_id=uid, profile=lane.name, enabled=True)
    ], 'D02 selected configured profile route changed')
    binding_sha = digest(encoded(grant))
    active = route.active_pairing_and_reader(root, principal, dict(principal_key=key, binding_sha256=binding_sha))
    return {'binding_sha256': binding_sha, 'onboarding_sha256': digest(onboarding_raw),
            'pairing_sha256': active, 'access_row_sha256': digest(encoded(row)), 'generation': row['generation']}, grant


def upload_name_free(io, workspace):
    received = workspace / 'received'
    before = (io.identity(workspace, directory=True), io.identity(received, directory=True))
    need(not os.path.lexists(workspace / SOURCE_NAME), 'D02 upload basename is present')
    registered = re.compile(r'telegram_[0-9a-f]{64}_' + re.escape(SOURCE_NAME))
    with os.scandir(received) as entries:
        for count, entry in enumerate(entries, 1):
            need(count <= 10000, 'D02 received names exceed observer bound')
            need(entry.name != SOURCE_NAME and registered.fullmatch(entry.name) is None,
                 'D02 upload basename is present')
    need(before == (io.identity(workspace, directory=True), io.identity(received, directory=True)),
         'D02 workspace identity changed')
    return before


def database_identity(io, path):
    # The normal read-only SQLite view must see committed WAL records.
    main = io.identity(path)
    wal = io.identity(path.with_name(path.name + '-wal'))
    shared = io.identity(path.with_name(path.name + '-shm'))
    return main[:-1], wal[:-1], shared[:5]


def observe_current(binding, *, scenario, read_reference, load_module):
    phase = digest(encoded(scenario))
    need(phase in PHASES, 'D02 exact normalized phase required')
    basis = binding['basis']
    need(all(basis[key]['sha256'] == pin for key, pin in HELPER_PINS.items()), 'D02 exact scope helper pins required')
    io, route, native = (load_module(basis[key], '_D02_scope_' + key) for key in ('io','route','projection'))
    root = native.HOME
    fence = binding['installation']
    require_receiver = binding['require_receiver']
    need(type(require_receiver) is bool, 'D02 installation observation mode required')
    expected_gateway = fence['gateway']
    need(root == Path(fence['home']) and sys.executable == io.NATIVE_PYTHON
         and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         'D02 exact installed interpreter and home required')
    uid, account = str(scenario['tester_id']), str(scenario['peer_id'])
    profile = 'telegram-bot-' + uid
    need(native.KEY == f'agent:{profile}:telegram:dm:{uid}', 'D02 exact retained conversation key required')
    native.SID = binding['selected_session_id']
    need(isinstance(native.SID, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,96}', native.SID),
         'D02 selected session identifier required')
    principal = dict(id=native.SID, source='telegram', user_id=uid, chat_id=uid, chat_type='dm',
                     session_key=native.KEY, profile_name=profile, transport_profile='default')
    lane = root / 'profiles' / profile
    workspace = lane / 'workspace'
    files = (root / 'state.db', lane / 'state.db')
    database = tuple(database_identity(io, path) for path in files)
    # Reuse the checked selected-row join with the existing WAL-aware reader.
    io.scoped_rows = route.scoped_rows
    commit, roles, receiver, overlay_pin = installed_roles(io, root, fence, native)
    need(not require_receiver or receiver, 'D02 actual receiver installation required before admission')
    config = tuple(digest(io.checked_read(path / 'config.yaml',limit=4 * 1024**2)) for path in (root, lane))

    def route_and_state():
        need(not os.path.lexists(root / 'maintenance.json'), 'D02 maintenance blocks ordinary observation')
        state = io.decode(io.checked_read(root / 'gateway_state.json', private=False))
        need(state['code_sha'] == commit and state['hermes_home'] == str(root)
             and state['session_store']['status'] == 'ok', 'D02 gateway source or route store changed')
        service = route.gateway_route(state, dict(pid=expected_gateway['pid'],
                             birth_ticks=expected_gateway['start_time']), principal)
        observed_route = io.checked_route_row(route, root, lane, principal, account, native)
        return state, service, observed_route

    gateway_state, service, stored_route = route_and_state()
    source = root / 'hermes-agent'
    binary = Path(sys.executable).parent.parent
    site = binary / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    need(site.resolve(strict=True) == site and site.is_dir(), 'D02 exact runtime package tree required')
    old_path = sys.path[:]
    try:
        sys.path[:0] = [str(source), str(site)]
        for name in ('hermes_cli.friday_user_scope', 'hermes_cli.friday_product_access',
                     'hermes_cli.plugins_state'):
            module = importlib.import_module(name)
            need(Path(module.__file__) == source / (name.replace('.', '/') + '.py'), 'D02 installed module path changed')
        rights, grant = permission(io, route, root, lane, principal, account)
        projected = native.fresh_native(gateway_state)
        need(projected['identity'] == expected_gateway and projected['quiescent'],
             'D02 exact running gateway and current idle conversation required')
        if require_receiver:
            # Reuse the native owner observation retained when this installed process started.
            # The live projection above still proves the same boot, PID, start and selected route.
            started = io.decode(read_reference(fence['native_owner_observation']))
            identify = started['identify']
            owner = identify['friday_owner']
            need(started['schema'] == 'frw.Root.D02.native-gateway-start-observation.v1'
                 and started['identity'] == expected_gateway and started['transport'] == 'unix-peer-credentials'
                 and identify['protocol'] == 1 and identify['kind'] == 'hermes-gateway'
                 and identify['pid'] == expected_gateway['pid']
                 and identify['start_time'] == expected_gateway['start_time']
                 and identify['hermes_home'] == owner['home'] == str(root)
                 and identify['code_sha'] == commit
                 and owner['source']['receipt'] == fence['metadata_sha256']['receipt']
                 and owner['source']['plugin'] == overlay_pin,
                 'D02 running receiver needs the actual successor startup binding')
        if phase == PHASES[0]:
            need('predecessor_context' not in binding, 'D02 upload unexpectedly has a predecessor')
            namespace = upload_name_free(io, workspace)
            predecessor = None
        else:
            need(basis['retained_upload_observer']['sha256'] == RETAINED_UPLOAD_SHA,
                 'D02 precise retained-upload observer required')
            helper = load_module(basis['retained_upload_observer'], '_D02_retained_upload')
            from gateway import upload_anchor
            from hermes_state import SessionDB

            need(Path(upload_anchor.__file__) == source / 'gateway/upload_anchor.py'
                 and Path(sys.modules[SessionDB._is_explicit_fork_child_row.__module__].__file__)
                     == source / 'hermes_state_messages.py', 'D02 exact native anchor and lineage sources required')
            predecessor = helper.check_retained_upload(
                binding['predecessor_context'], session_key=native.KEY, session_id=native.SID,
                profile_home=lane, principal=('telegram', 'default', account, uid), binding=grant,
                expected_upload_ack=binding['predecessor_upload_ack'],
                expected_ingress_settlement_sha256=binding['predecessor_ingress_settlement_sha256'],
                receiver_root=RECEIVER_ROOT, checked_read=io.checked_read, native_anchor=upload_anchor,
                native_fork_check=SessionDB._is_explicit_fork_child_row, deadline=time.monotonic()+0.5)
            namespace = (io.identity(workspace, directory=True), io.identity(workspace/'received', directory=True))
        need(permission(io, route, root, lane, principal, account) == (rights, grant),
             'D02 active pairing or scoped authority changed')
    finally:
        sys.path[:] = old_path
    if phase == PHASES[0]:
        need(upload_name_free(io, workspace) == namespace, 'D02 upload namespace changed')
    final_state, final_service, final_route = route_and_state()
    final_projection = native.fresh_native(final_state)
    need(tuple(database_identity(io, path) for path in files) == database
         and (final_service, final_route) == (service, stored_route)
         and final_projection['quiescent']
         and (final_projection['identity'], final_projection['generation'])
             == (projected['identity'], projected['generation'])
         and tuple(digest(io.checked_read(path / 'config.yaml', limit=4 * 1024**2)) for path in (root,lane)) == config,
         'D02 current installed route or selected storage changed')
    need(installed_roles(io, root, fence, native) == (commit, roles, receiver, overlay_pin),
         'D02 selected installed source roles changed')
    return {'phase_sha256':phase, 'source_sha256':SOURCE_SHA, 'metadata_sha256':fence['metadata_sha256'],
            'installed_roles':roles, 'receiver_sources_present':receiver,
            'native_identity':projected['identity'], 'native_generation':projected['generation'],
            'session_id':native.SID, 'route_sha256':digest(encoded(stored_route)),
            'workspace_sha256':digest(encoded(namespace)), 'config_sha256':config,
            'protected_db_identity_sha256':digest(encoded(database)),
            'rights':rights, 'predecessor':predecessor, 'event_authority':False}


def check_current(binding, *, scenario, read_reference, load_module):
    expected = binding['scope_sha256']
    need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected),
         'D02 exact current observation pin required')
    current = observe_current(binding, scenario=scenario, read_reference=read_reference, load_module=load_module)
    need(digest(encoded(current)) == expected, 'D02 installation, route or retained input changed')
    return True
