"""Observe the existing Core295 private Telegram lane for the prepared S01 plan.

The native socket selector, installed policy and active pairing remain binding.
No event or delivery capability is manufactured by this observer.
"""

from contextlib import closing
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
import time


METADATA_SHA = 'b97bbe0cfb22b784a8380dadcb2a728857e70bdcb210c2c1ecae7b3b73762682'
PROJECTION_CLIENT_SHA = 'bd465b9664851e061b7a1ea69ed01a53d0fd40b075c7664d394c855e548b45b1'
INSTALLATION_SHA = '71ec71d2b4b13a28b9123f100af28962e7cf2725fafa7c99ea89474d810cb2e1'
S01_SCENARIO_SHA = '8a028fd974f9290f8cf978e7d2d7ab75f66cb2bb468606365f5e5512468b057d'
PERMISSION_ROLES = ('hermes_cli/friday_user_scope.py', 'hermes_cli/friday_product_access.py',
                    'hermes_cli/plugins_state.py', 'gateway/pairing.py')
RECEIPT_PATHS = {'receipt': 'hermes-agent.source.json', 'stamp': 'hermes-agent/install-stamp.json',
                 'marker': 'FRIDAY-INSTALL.json'}


def require(predicate, why):
    if not predicate:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode()


def identity(path, *, directory=False):
    row = path.lstat()
    test, mode = (stat.S_ISDIR, 0o700) if directory else (stat.S_ISREG, 0o600)
    require(path.resolve(strict=True) == path and test(row.st_mode) and row.st_uid == os.getuid()
            and stat.S_IMODE(row.st_mode) == mode and (directory or row.st_nlink == 1),
            'Exact private S01 store or workspace required')
    return [row.st_dev, row.st_ino, row.st_uid, row.st_mode]


def scoped_rows(path, sql, bindings):
    protected = (path, Path(str(path) + '-wal'), Path(str(path) + '-shm'))
    before = [identity(name) for name in protected]
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0.5)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        rows = [dict(row) for row in db.execute(sql, bindings).fetchmany(2)]
    require([identity(name) for name in protected] == before and len(rows) == 1,
            'Exact retained S01 row or store identity changed')
    return rows[0]


def check_route(home, workspace_home, principal, bot_id, client):
    uid, key, sid = principal['user_id'], client.KEY, client.SID
    route = scoped_rows(home / 'state.db',
                        'SELECT entry_json FROM gateway_routing WHERE scope = ? AND session_key = ?',
                        (str(home / 'sessions'), key))
    entry = json.loads(route['entry_json'], object_pairs_hook=client.unique)
    where = dict(platform='telegram', user_id=uid, chat_id=uid, chat_type='dm', thread_id=None)
    origin = entry['origin']
    require(entry['session_id'] == sid and entry['session_key'] == key
            and entry['transport_profile'] == principal['transport_profile']
            and entry['platform'] == 'telegram' and entry['chat_type'] == 'dm'
            and not entry.get('suspended') and not entry.get('active_turn_token')
            and all(origin.get(name) == value for name, value in where.items()),
            'Exact unthreaded S01 retained routing does not match')

    row = scoped_rows(workspace_home / 'state.db',
                      'SELECT id, source, user_id, chat_id, chat_type, thread_id, session_key, '
                      'profile_name, transport_profile, origin_json FROM sessions WHERE id = ?', (sid,))
    durable_origin = json.loads(row.pop('origin_json'), object_pairs_hook=client.unique)
    account = durable_origin['friday_account_origin']
    expected_account = dict(schema='friday.account_origin.v1', platform='telegram',
                            transport_profile=principal['transport_profile'], account_id=bot_id)
    require(row == {'thread_id': None, **principal}
            and all(durable_origin.get(name) == value for name, value in where.items())
            and account == expected_account,
            'Exact S01 persisted source identity or receiving account changed')
    return digest(encode({'route': {k: entry[k] for k in
                          ('session_id', 'session_key', 'platform', 'chat_type', 'transport_profile')},
                          'profile_row': row, 'origin': where, 'account': account}))


def active_pairing_and_reader(home, principal, policy):
    # The running adapter reads the active pairing file; checking a merged
    # current and legacy layout could incorrectly treat a removed approval as active.
    user_scope = sys.modules['hermes_cli.friday_user_scope']
    access = sys.modules['hermes_cli.friday_product_access']
    pairing = importlib.import_module('gateway.pairing')
    require(Path(pairing.__file__) == home / 'hermes-agent/gateway/pairing.py',
            'Exact installed native pairing implementation required')
    with user_scope.authority(home):
        active_dir = pairing.get_hermes_dir('platforms/pairing', 'pairing', home=home)
        active_file = active_dir / 'telegram-approved.json'
        before = identity(active_file)
        active_doc = pairing._approved_json_storage_readonly(active_file, home)
        require(pairing._matching_ids('telegram', active_doc, principal['user_id']),
                'Active receiving Telegram pairing required for S01')
        require(identity(active_file) == before
                and pairing.get_hermes_dir('platforms/pairing', 'pairing', home=home) == active_dir,
                'Selected active pairing layout changed')
        bindings = [row for row in user_scope.policy(home)['bindings']
                    if access.principal_id(row['platform'], row['transport_profile'],
                                           row['account_id'], row['user_id']) == policy['principal_key']]
    require(len(bindings) == 1 and 'read_file' in bindings[0]['tools']
            and digest(encode(bindings[0])) == policy['binding_sha256'],
            'Current exact S01 binding must allow native file reading')
    return digest(encode({'path': str(active_file), 'identity': before, 'approvals': active_doc}))


def gateway_route(state, installed_gateway, principal):
    writer = state['platforms']['telegram']
    require((state['pid'], state['start_time']) == (installed_gateway['pid'], installed_gateway['birth_ticks'])
            and state['gateway_state'] == 'running' and state['active_agents'] == 0 and state.get('active_work') is None
            and state['restart_requested'] is False and writer['state'] == 'connected'
            and writer['needs_attention'] is False and writer['writer_pid'] == state['pid']
            and writer['writer_start_time'] == state['start_time']
            and principal['profile_name'] in state['served_profiles']
            and 0 <= time.time() - datetime.fromisoformat(state['updated_at']).timestamp() <= 120,
            'Fresh idle Core295 Telegram route required')
    return state['pid'], state['start_time'], tuple(state['served_profiles'])


def observe_scope(basis, *, scenario, read_reference, load_module):
    require(digest(encode(scenario)) == S01_SCENARIO_SHA, 'Exact prepared S01 scenario required')
    for name, checksum in (('installation', INSTALLATION_SHA), ('namespace_helper', METADATA_SHA),
                           ('projection_client', PROJECTION_CLIENT_SHA)):
        require(basis[name]['sha256'] == checksum, 'Exact Core295 scope source required')
    installation = json.loads(read_reference(basis['installation']))
    metadata = load_module(basis['namespace_helper'], '_Root_core295_namespace')
    native = load_module(basis['projection_client'], '_Root_core295_projection')
    home = metadata.H
    require(native.HOME == home and sys.executable == metadata.NATIVE_PYTHON
            and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            'Exact native Core295 environment required')
    principal = metadata.PRINCIPAL
    require(principal['id'] == native.SID and principal['session_key'] == native.KEY
            and principal['user_id'] == principal['chat_id'] == str(scenario['tester_id'])
            and principal['chat_type'] == 'dm', 'Prepared S01 tester does not match the existing lane')
    workspace_home = home / 'profiles' / principal['profile_name']
    scope_dirs = (workspace_home, workspace_home / 'workspace', workspace_home / 'workspace' / 'received')
    workspace = [identity(path, directory=True) for path in scope_dirs]

    def verify_receipts():
        for label, path in RECEIPT_PATHS.items():
            require(digest(native.read(home / path)) == installation['metadata_sha256'][label],
                    'Installed Core295 receipt, marker or stamp changed')

    verify_receipts()
    manifest = json.loads(native.read(home / RECEIPT_PATHS['receipt']))
    require(len(manifest['layers']) == 295, 'Installed layer count changed')
    pins = {name: manifest['files'][name]['sha256'] for name in PERMISSION_ROLES}
    for name, pin in pins.items():
        require(digest(native.read(home / 'hermes-agent' / name)) == pin, 'Current installed scope role changed')
    require(manifest['files']['gateway/ordinary_turn_projection.py']['sha256'] == native.NATIVE_SHA
            and digest(native.read(home / 'hermes-agent/gateway/ordinary_turn_projection.py')) == native.NATIVE_SHA,
            'Exact ordinary native projection implementation changed')
    metadata.LEAF_PINS = metadata.LEAF_PINS | pins

    previous_imports = list(sys.path)
    binary = Path(sys.executable)
    site = binary.parent.parent / 'lib' / ('python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor))
    site /= 'site-packages'
    try:
        require(site.resolve(strict=True) == site and site.is_dir(), 'Exact native package tree required')
        sys.path[:0] = [str(home / 'hermes-agent'), str(site)]
        permission = metadata.permission_current()
        bot_id = str(scenario['peer_id'])
        access = sys.modules['hermes_cli.friday_product_access']
        principal_id = access.principal_id('telegram', principal['transport_profile'], bot_id, principal['user_id'])
        require(permission['principal_key'] == principal_id and permission['runtime_profile'] == principal['profile_name']
                and permission['native_capability_check'] is True
                and permission['new_Telegram_event_capability_issued'] is False,
                'S01 receiving bot, disabled authority or profile changed')
        pairing = active_pairing_and_reader(home, principal, permission)
        route = check_route(home, workspace_home, principal, bot_id, native)
    finally:
        sys.path[:] = previous_imports

    require(not os.path.lexists(home / 'maintenance.json'), 'S01 maintenance is present')
    installed_gateway = installation['services']['gateway']
    state_path = home / 'gateway_state.json'
    state = native.js(state_path)
    gateway = gateway_route(state, installed_gateway, principal)
    observed = native.fresh_native(state)
    require(observed['quiescent'] and observed['identity']['boot_id'] == installation['boot_id']
            and observed['session_key'] == native.KEY and observed['session_id'] == native.SID,
            'Existing S01 conversation is no longer idle')
    require(gateway_route(native.js(state_path), installed_gateway, principal) == gateway
            and workspace == [identity(path, directory=True) for path in scope_dirs]
            and metadata.profile_config_refs() == permission['profile_configs']
            and not os.path.lexists(home / 'maintenance.json'),
            'Core295 S01 workspace, profile configuration or maintenance changed')
    verify_receipts()
    return {
        'namespace_sha256': digest(encode(permission)), 'route_sha256': route,
        'pairing_sha256': pairing, 'workspace_sha256': digest(encode(workspace)),
        'gateway_identity': observed['identity'], 'native_generation': observed['generation'],
        'metadata_sha256': installation['metadata_sha256'], 'selected_scenario_sha256': S01_SCENARIO_SHA,
        'read_file_policy_eligible': True, 'current_private_unthreaded_lane': True,
        'fresh_event_authority_issued': False,
    }


def check_current(binding, *, scenario, read_reference, load_module):
    expected = binding['scope_sha256']
    require(isinstance(expected, str) and len(expected) == 64, 'Exact reviewed S01 scope pin required')
    observed = observe_scope(binding['basis'], scenario=scenario, read_reference=read_reference,
                             load_module=load_module)
    require(digest(encode(observed)) == expected, 'S01 current selected scope changed')
    return True
