"""Root-only actual221 prerequisite for the first original F03 ordinary upload.

Inert import. No issuer, grant, once claim, model, Office, send, or restart.
Only Root may invoke observe/check. The unchanged scoped native/kernel helpers
are reused, never M09 case acceptance or gate202.check/fresh_native. Full221's
closed readback is pinned; current canonical4 and selected active routes are
freshly checked without rescanning all 17,893 installed files at every seam.
"""
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import time
import types

HERE = Path(__file__).parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
HELPER = Path('/home/jericho/.cache/FRW-SOL-V3-M09-FXDOC-PRIVACY-SOURCE-CORE-20261114/candidate-r2/private/root_m09.py')
HELPER_SHA = '1d03d4e2d310a5c8109a85daea8ab32d34b47b1eb897f0a9080990b61beec7fc'
CLOSURE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-AFTER220-WHOLE-CALLER-PREP-20261114/frame/ACTUAL221-INSTALLED-CLOSED.json')
CLOSURE_SHA = 'f155ec3337f46b9405afcc73725af71f0bce09d71c1bee4525a44fc10066bfa2'
NATIVE_SHA = '466c67eb3f70713c88573ff6b19ba623762b0e127dc031873f2ed70015ec2743'
RUN_ID = 'f03-ods-formulas-original-221-20261114'
CASE = 'F-03'
OPERATION = 'CASE164/format27/edit/formulas-v02/row667'
PHASE = 'FIRST-ORDINARY-UPLOAD-EDIT-RETURN'
SID = '20261030_093055_43bba39f'
KEY = 'agent:telegram-bot-8812646969:telegram:dm:8812646969'
SOURCE = dict(path='/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods', bytes=16538, sha256='a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58')
EXPECTED = dict(source_layers=221, project_files=523, native_files=17893, plugin_files=52, base_source_files=17730, source_receipt_sha256='a4d278c67b044b684c3182107947bdb9d82a592b54924d9a5bb283fc11ac1d40', input_sha256='60d879571771e861df8441a02489cb74bf8d8707e2f14e0ae3448b81ed87504d')
ORIGINAL_SELECTION_PATH = '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/ROOT-ORIGINAL-VARIANT-PHASE-DECISION.json'
ORIGINAL_SELECTION_SHA = 'a62471b1ea1766fb4f22696f58867848981e6043d3f0edf3b13e3c4a57091203'
PREPARED_FIELDS = {'id', 'scenario', 'scenario_sha256', 'created_at', 'deadline', 'step', 'status', 'send_state', 'sent_ids', 'seen', 'message_ids', 'observations', 'update_count', 'last_text', 'repeat_count', 'send_attempts', 'capture_start_offset'}
PROOFS = {'original_selection', 'source_custody', 'all_profile_history_semantic_once', 'private_exclusion', 'source_review', 'owned_actor_stop_resources'}
CODE_MINIMUM = ('gateway/ordinary_turn_projection.py', 'gateway/run.py', 'plugins/platforms/telegram/adapter.py', 'plugins/platforms/telegram/telegram_file_boundary.py', 'plugins/platforms/telegram/telegram_ingress.py', 'plugins/platforms/telegram/telegram_document_bytes.py', 'plugins/platforms/telegram/telegram_message_event.py', 'hermes_cli/friday_ordinary_gateway.py', 'hermes_cli/friday_workspace_ods.py', 'hermes_cli/friday_workspace_revision.py', 'hermes_cli/friday_user_scope.py', 'hermes_cli/friday_product_access.py', 'hermes_cli/plugins_state.py', 'tools/scoped_ods.py', 'tools/scoped_ods_table.py', 'tools/scoped_ods_recalculate.py')
PROFILE_HOMES = {'default': H, 'A': H/'profiles/dest_telegram', 'B': H/'profiles/telegram-bot-8812646969'}
PRE_INTENT_BOUNDARY_PHASES = ('NEW', 'CURSOR_AUTHORITY', 'PRE_INTENT_REVALIDATION')


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'F03_DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def identity(info):
    return {k: getattr(info, 'st_'+k) for k in ('dev', 'ino', 'uid', 'gid', 'mode', 'nlink', 'size', 'mtime_ns', 'ctime_ns')}


def read(path, *, private=False, limit=24*1024**2):
    path = Path(path)
    require(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)), 'F03_ABSOLUTE_NO_LINK_PATH_REQUIRED')
    with os.fdopen(os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno()); raw = stream.read(limit+1); after = os.fstat(stream.fileno())
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
            and not stat.S_IMODE(before.st_mode)&0o002 and len(raw) <= limit
            and identity(before) == identity(after) == identity(path.stat()), 'F03_FILE_CUSTODY_OR_CAS_CHANGED')
    if private:
        parent = path.parent.stat()
        require(stat.S_IMODE(before.st_mode) == 0o600 and parent.st_uid == os.getuid()
                and stat.S_IMODE(parent.st_mode) == 0o700, 'F03_ROOT0600_0700_REQUIRED')
    return raw


def reference(value):
    return (type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
            and type(value['path']) is str and Path(value['path']).is_absolute()
            and str(Path(value['path'])) == value['path'] and '..' not in Path(value['path']).parts
            and type(value['bytes']) is int and 0 < value['bytes'] <= 24*1024**2
            and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['sha256']) is not None)


def readref(value, *, private=True):
    require(reference(value), 'F03_EXACT_PROTECTED_REFERENCE_REQUIRED')
    raw = read(value['path'], private=private)
    require(len(raw) == value['bytes'] and digest(raw) == value['sha256'], 'F03_ROOT_REFERENCE_DRIFT')
    return raw


def docref(value, *, private=True):
    return json.loads(readref(value, private=private), object_pairs_hook=unique)


def pin(path, *, private=False):
    raw = read(path, private=private)
    return dict(path=str(path), bytes=len(raw), sha256=digest(raw))


def load(value, name):
    raw = readref(value, private=False)
    module = types.ModuleType(name); module.__file__ = value['path']
    exec(compile(raw, value['path'], 'exec'), module.__dict__)
    return module


def helper():
    raw = read(HELPER, private=True)
    require(len(raw) == 55948 and digest(raw) == HELPER_SHA, 'F03_UNCHANGED_SCOPED_NATIVE_HELPER_REQUIRED')
    module = types.ModuleType('_F03_genuine_readonly_helpers'); module.__file__ = str(HELPER)
    exec(compile(raw, str(HELPER), 'exec'), module.__dict__)
    return module


def kernel(pid):
    return helper().kernel(pid)


def effect_shape(effect):
    require(type(effect) is dict and effect.get('case') == CASE and effect.get('operation_id') == OPERATION
            and effect.get('phase') == PHASE and effect.get('run_id') == RUN_ID
            and effect.get('source') == SOURCE and effect.get('expected_product') == EXPECTED,
            'F03_EXACT_ORIGINAL_EFFECT_REQUIRED')
    require(set(effect.get('root_proofs', {})) == PROOFS and all(reference(r) for r in effect['root_proofs'].values()), 'F03_ROOT_SCOPED_PROOFS_UNBOUND')
    require(all(reference(effect.get(k)) for k in ('adapter', 'current_gate', 'scenario_ref', 'proposal_ref'))
            and effect['scenario_ref']['sha256'] == effect.get('scenario_sha256'), 'F03_REVIEWED_SOURCE_SCENARIO_UNBOUND')
    require(effect['current_gate']['path'] == str(HERE/'current221.py'), 'F03_EXACT_CURRENT_GATE_PATH')
    return True


def proof_shape(proof):
    require(type(proof) is dict and proof.get('schema') == 'frw.Root.f03-current221-preupload.v1'
            and proof.get('operator') == 'Root'
            and proof.get('status') in ('ROOT_PREPARED_ONE_FUTURE_OPERATION', 'ROOT_BOUND'), 'F03_EXACT_ROOT_CURRENT221_PROOF_REQUIRED')
    effect_shape(proof.get('contract_effect'))
    require(proof.get('boundary_phase') in PRE_INTENT_BOUNDARY_PHASES, 'F03_PREINTENT_ONLY')
    require(reference(proof.get('native_request')) and type(proof.get('native_socket_path')) is str
            and type(proof.get('current_files')) is list and proof['current_files']
            and all(reference(r) for r in proof['current_files']), 'F03_CURRENT_NATIVE_ROUTE_CONFIG_UNBOUND')
    require(type(proof.get('mutable_paths')) is list and proof['mutable_paths'], 'F03_CANCEL_ONCE_ACTION_OWNERSHIP_SELECTORS_UNBOUND')
    categories = set()
    for row in proof['mutable_paths']:
        require(type(row) is dict and set(row) == {'category', 'path'} and row['category'] in ('cancel', 'once', 'recovery', 'action_ownership')
                and type(row['path']) is str and Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts, 'F03_MUTABLE_PATH_SELECTOR_SHAPE')
        categories.add(row['category'])
    require(categories == {'cancel', 'once', 'recovery', 'action_ownership'}, 'F03_MUTABLE_ACTION_SCOPE_INCOMPLETE')
    require(len({r['path'] for r in proof['current_files']}) == len(proof['current_files'])
            and len({(r['category'], r['path']) for r in proof['mutable_paths']}) == len(proof['mutable_paths']), 'F03_DUPLICATE_CURRENT_SELECTOR')
    return True


def lifetime(proof, *, wall=None, mono=None):
    wall = time.time() if wall is None else wall; mono = time.monotonic() if mono is None else mono
    for key in ('created_at', 'expires_at', 'created_monotonic', 'expires_monotonic'):
        require(type(proof.get(key)) in (int, float) and math.isfinite(proof[key]), 'F03_PAIRED_FINITE_ROOT_CLOCK_REQUIRED')
    require(proof['created_at'] <= wall < proof['expires_at'] <= proof['created_at']+120
            and 0 <= proof['created_monotonic'] <= mono < proof['expires_monotonic'] <= proof['created_monotonic']+120
            and abs((wall-proof['created_at'])-(mono-proof['created_monotonic'])) <= 2, 'F03_STALE_FUTURE_OR_CLOCK_JUMP_ROOT_PROOF')
    return True


def closure():
    raw = read(CLOSURE, private=True)
    require(digest(raw) == CLOSURE_SHA, 'F03_CLOSED221_READBACK_REFERENCE_CHANGED')
    value = json.loads(raw, object_pairs_hook=unique)
    require(value.get('schema') == 'friday.Root.actual221-installed-closed.v1'
            and value.get('installed') == dict(layers=221, project=523, native=17893, plugins=52, base=17730)
            and value.get('source_commit') == 'c11d33599afa4e25fbee62e28d6f7d515fb33782'
            and value.get('actors_boundary_publisher_closed') is True and value.get('healthy_services_infinity') is True
            and value.get('full17893_readback_reused_from_exact_justclosed_actor') is True, 'F03_ACCEPTED_FULL221_CLOSURE_REQUIRED')
    return value


def installed(closed, current_files):
    canonical = {}
    for name in ('input', 'source_receipt', 'marker', 'stamp'):
        row = closed['canonical4'][name]; raw = read(row['path'])
        require(digest(raw) == row['sha256'], 'F03_CURRENT_CANONICAL4_CHANGED_'+name)
        canonical[name] = dict(path=row['path'], bytes=len(raw), sha256=digest(raw))
    receipt = json.loads(read(H/'hermes-agent.source.json'), object_pairs_hook=unique)
    marker = json.loads(read(H/'FRIDAY-INSTALL.json'), object_pairs_hook=unique)
    stamp = json.loads(read(H/'hermes-agent/install-stamp.json'), object_pairs_hook=unique)
    current_input = json.loads(read(closed['canonical4']['input']['path']), object_pairs_hook=unique)
    product = dict(source_layers=len(receipt['layers']), project_files=len(current_input['project_files']), native_files=len(receipt['files']), plugin_files=len(marker['plugin_files']), base_source_files=receipt['source_file_count'], source_receipt_sha256=canonical['source_receipt']['sha256'], input_sha256=canonical['input']['sha256'])
    require(product == EXPECTED and marker['source_receipt_sha256'] == EXPECTED['source_receipt_sha256']
            and marker['input_sha256'] == EXPECTED['input_sha256'] and stamp['fridaySource']['layers'] == receipt['layers']
            and stamp['fridaySource']['baseTree'] == receipt['base_tree'], 'F03_ACTUAL221_CANONICAL_TUPLE_CHANGED')
    required = {str(H/'config.yaml'), str(H/'profiles/dest_telegram/config.yaml'), str(H/'profiles/telegram-bot-8812646969/config.yaml'), str(H/'plugin-data/agent-plugin-friday_rework-877e6505/state.json'), str(H/'profiles/dest_telegram/.friday-user-scope.json'), str(H/'profiles/telegram-bot-8812646969/.friday-user-scope.json')}
    required.update(str(H/'hermes-agent'/name) for name in CODE_MINIMUM)
    if 'tools/scoped_ods_rich.py' in receipt['files']:
        required.add(str(H/'hermes-agent/tools/scoped_ods_rich.py'))
    require(required <= {r['path'] for r in current_files}, 'F03_SELECTED_ACTIVE_CODE_CONFIG_ROUTE_PINS_INCOMPLETE')
    for row in current_files:
        readref(row, private=False)
        path = Path(row['path'])
        if path.is_relative_to(H/'hermes-agent'):
            name = str(path.relative_to(H/'hermes-agent')); item = receipt['files'].get(name)
            require(item is not None and row['sha256'] == (item['sha256'] if type(item) is dict else item), 'F03_ACTIVE_CODE_NOT_SELECTED_INSTALLED_SOURCE')
        elif path.is_relative_to(H) and str(path.relative_to(H)) in marker['plugin_files']:
            require(row['sha256'] == marker['plugin_files'][str(path.relative_to(H))], 'F03_SELECTED_PLUGIN_ROUTE_CHANGED')
    for name, expected in marker['plugin_files'].items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts
                and digest(read(H/name)) == expected, 'F03_CURRENT_SELECTED_PLUGIN_DRIFT')
    native_pin = next(r for r in current_files if r['path'] == str(H/'hermes-agent/gateway/ordinary_turn_projection.py'))
    require(native_pin['sha256'] == NATIVE_SHA, 'F03_CURRENT_NATIVE466C_REQUIRED')
    return product, canonical


def services(closed, h):
    result = {}
    for name, unit in (('gateway', 'hermes-gateway-1b7e7667.service'), ('dashboard', 'hermes-dashboard.service')):
        fields = {'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlPID', 'ControlGroup', 'InvocationID', 'UnitFileState', 'RuntimeMaxUSec'}
        run = subprocess.run(['/usr/bin/systemctl', '--user', 'show', unit, '--property='+','.join(sorted(fields))], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=True)
        require(len(run.stdout) <= 65536 and len(run.stderr) <= 65536, 'F03_BOUNDED_SERVICE_METADATA')
        value = {}
        for line in run.stdout.decode().splitlines():
            require('=' in line, 'F03_MALFORMED_SERVICE_METADATA'); key, item = line.split('=', 1)
            require(key in fields and key not in value, 'F03_DUPLICATE_SERVICE_METADATA'); value[key] = item
        old = closed['services'][name]
        require(set(value) == fields and value['LoadState'] == 'loaded' and value['ActiveState'] == 'active' and value['SubState'] == 'running'
                and value['MainPID'] == str(old['pid']) and value['ControlPID'] == '0' and value['ControlGroup'] == old['cgroup']
                and value['InvocationID'] == old['invocation_id'] and value['UnitFileState'] == 'enabled'
                and value['RuntimeMaxUSec'] == old['runtime_max'] == 'infinity', 'F03_CURRENT_PERMANENT_SERVICE_CUSTODY_CHANGED')
        require(h.kernel(old['pid']) == dict(pid=old['pid'], start_time=old['birth_ticks'], boot_id=old['boot_id']), 'F03_CURRENT_SERVICE_KERNEL_CHANGED')
        result[name] = value
    return result


def selected_access(row):
    access = row.get('access')
    expected = dict(platform='telegram', transport_profile='default', account_id='8751854128', user_id='8812646969', enabled=True, role='user')
    require(type(access) is dict and set(access) == set(expected)|{'generation'}
            and {k: access[k] for k in expected} == expected and type(access['generation']) is int and access['generation'] >= 1
            and row.get('principal_id') == 'b21d67fc1b4ccce97241421bf86e3bc7416064133f7afd0822e6734ac6d5eef5', 'F03_CURRENT_SELECTED_NATIVE_ACCESS_UNBOUND')
    return True


def native(proof, h):
    raw = read(H/'gateway_state.json'); state = json.loads(raw, object_pairs_hook=unique); tg = state.get('platforms', {}).get('telegram', {})
    require(state.get('gateway_state') == 'running' and state.get('active_agents') == 0 and state.get('active_work') is None
            and state.get('restart_requested') is False and state.get('session_store', {}).get('status') == 'ok'
            and tg.get('state') == 'connected' and tg.get('needs_attention') is False
            and tg.get('writer_pid') == state.get('pid') and tg.get('writer_start_time') == state.get('start_time'), 'F03_CURRENT_WRITER_NOT_HEALTHY_QUIESCENT')
    value, gateway = h.native(dict(native_request=proof['native_request'], native_socket_path=proof['native_socket_path'], native_implementation_sha256=NATIVE_SHA), state, raw, require_sessions=False)
    selected = value['scopes']['B']; selected_access(selected)
    require(selected.get('session_id') == SID and selected.get('session_key') == KEY, 'F03_ORIGINAL_SELECTED_NATIVE_SESSION_CHANGED')
    return value, gateway, raw


def native_stable(value):
    return {k: v for k, v in value.items() if k not in ('observed_monotonic', 'query_id')}


def database(slot, private_markers, native_scope=None):
    path = PROFILE_HOMES[slot]/'state.db'; before = identity(path.stat())
    require(not any(p.is_symlink() for p in (path, *path.parents)) and stat.S_ISREG(before['mode'])
            and before['uid'] == os.getuid() and before['nlink'] == 1 and not stat.S_IMODE(before['mode'])&0o002, 'F03_DB_CUSTODY_CHANGED')
    with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=2)) as db:
        db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
        rows = db.execute('SELECT * FROM messages ORDER BY id').fetchall(); columns = [x[1] for x in db.execute('PRAGMA table_info(messages)')]
        require(len(rows) <= 20000 and sum(len(encoded([repr(x) for x in row])) for row in rows) <= 32*1024**2, 'F03_ALL_PROFILE_HISTORY_BOUND')
        manifest = []
        for row in rows:
            record = dict(zip(columns, row)); text = record.get('content') or ''
            require(not any(marker in encoded([repr(x) for x in row]) for marker in private_markers), 'F03_PRIVATE_PREPARATION_IN_PRODUCT_HISTORY')
            manifest.append([record.get('id'), record.get('session_id'), record.get('role'), record.get('platform_message_id'), digest(encoded([repr(x) for x in row]))])
        sessions = db.execute('SELECT * FROM sessions ORDER BY id').fetchall()
        session_columns = [x[1] for x in db.execute('PRAGMA table_info(sessions)')]
        selected_session = None
        if native_scope is not None and native_scope.get('session_id'):
            profile, user = (('dest_telegram', '467035772') if slot == 'A' else ('telegram-bot-8812646969', '8812646969'))
            selected_rows = [dict(zip(session_columns, row)) for row in sessions if dict(zip(session_columns, row))['id'] == native_scope['session_id']]
            require(len(selected_rows) == 1, 'F03_CURRENT_NATIVE_DB_SESSION_MISSING')
            selected_session = selected_rows[0]
            expected = dict(id=native_scope['session_id'], source='telegram', user_id=user, chat_id=user, chat_type='dm', session_key=native_scope['session_key'], profile_name=profile, transport_profile='default')
            require({k: selected_session.get(k) for k in expected} == expected, 'F03_NATIVE_DB_PROFILE_PRINCIPAL_MISMATCH')
        require(len(sessions) <= 2048, 'F03_PROFILE_SESSION_BOUND')
        leases = db.execute('SELECT * FROM session_turn_leases').fetchall()
        pending = db.execute("SELECT delegation_id,state,delivery_state FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred') ORDER BY delegation_id").fetchall()
        require(leases == [] and pending == [], 'F03_ALL_PROFILE_DURABLE_LEASE_OR_PENDING_WORK')
        routes = db.execute('SELECT scope,session_key,entry_json FROM gateway_routing ORDER BY scope,session_key').fetchall() if slot == 'default' else []
        db.rollback()
    after = identity(path.stat()); custody = ('dev', 'ino', 'uid', 'gid', 'mode', 'nlink')
    require({k: before[k] for k in custody} == {k: after[k] for k in custody}, 'F03_DB_IDENTITY_CAS_CHANGED')
    return dict(identity={k: before[k] for k in custody}, counts=dict(messages=len(rows), max_message_id=max((row[0] for row in manifest), default=0)), selected_session=selected_session, manifest=manifest, manifest_sha256=digest(encoded(manifest)), sessions_sha256=digest(encoded([[repr(x) for x in row] for row in sessions])), routes=[list(row) for row in routes], leases=leases, pending=pending)



def separate_first_send(meta, row=None, *, preintent=True, preclaim=False):
    # Fixed source path; the separately pinned supplement authenticates itself.
    source=HERE.parent/'first_send.py'
    module=types.ModuleType('_F03_separate_first_send');module.__file__=str(source)
    raw=read(source)
    require(len(raw)==17341 and digest(raw)=='dc4cac00c396c33ad3dd7f4b971ac7088bc79898e07e15cda7fe6682f63da1cf', 'F03_SEPARATE_PHASE_SOURCE_PIN_CHANGED')
    exec(compile(raw,str(source),'exec'),module.__dict__)
    if row is None:
        row=json.loads(read(STATE/'runs'/(RUN_ID+'.json'),private=True),object_pairs_hook=unique)
    if preclaim and module.is_preclock(meta):module.validate_preclock_projection(meta,row,STATE)
    elif preclaim:module.validate_preclaim(meta,row,STATE)
    else:module.validate(meta,row,STATE,preintent=preintent,active=True)
    return module

def history(effect, scenario, boundary_phase, *, first_send=None, first_send_preclaim=False):
    require(boundary_phase in PRE_INTENT_BOUNDARY_PHASES, 'F03_PREINTENT_ONLY')
    raw = read(STATE/'cursor.json', private=True); cursor = json.loads(raw, object_pairs_hook=unique)
    require(type(cursor.get('offset')) is int and cursor['offset'] >= 0, 'F03_CANONICAL_CURSOR_UNBOUND')
    paths = sorted((STATE/'runs').glob('*.json')); require(len(paths) <= 2048, 'F03_TESTER_HISTORY_BOUND')
    records = []; own = False
    for path in paths:
        data = read(path, private=True, limit=1024**2); row = json.loads(data, object_pairs_hook=unique)
        require(row.get('id') == path.stem and encoded(row) == data, 'F03_HISTORY_CANONICAL_ID_OR_ENCODING')
        if row['id'] == RUN_ID:
            require(boundary_phase != 'NEW', 'F03_NEW_RUN_ALREADY_EXISTS')
            require(set(row) == PREPARED_FIELDS | ({'first_send_phase'} if first_send is not None and not first_send_preclaim else set()) and row.get('scenario') == scenario and row.get('scenario_sha256') == effect['scenario_sha256'] and row.get('status') == 'PREPARED' and row.get('send_state') == 'none'
                    and all(type(row.get(k)) is int and row[k] == 0 for k in ('step', 'send_attempts', 'update_count', 'repeat_count'))
                    and all(row.get(k) == [] for k in ('sent_ids', 'seen', 'message_ids', 'observations')) and row.get('last_text') is None
                    and row.get('capture_start_offset') == cursor['offset'] and 'continuation_reference' not in row, 'F03_OWN_PRISTINE_PREPARED_ONLY_NO_REPLAY')
            created = dt.datetime.fromisoformat(row['created_at']).timestamp()
            if first_send is None:
                require(type(row.get('deadline')) in (int, float) and math.isfinite(row['deadline']) and created <= time.time() < row['deadline'] <= created+301, 'F03_ORIGINAL300_CLOCK_CHANGED')
            else:
                require(first_send_preclaim or row.get('first_send_phase') == first_send, 'F03_EXPLICIT_PHASE_METADATA_CHANGED')
                separate_first_send(first_send, row, preclaim=first_send_preclaim)
            own = True; continue
        records.append([path.name, len(data), digest(data), row.get('status'), row.get('send_state')])
    require(boundary_phase not in ('CURSOR_AUTHORITY', 'PRE_INTENT_REVALIDATION') or own, 'F03_PREPARED_OWN_RUN_REQUIRED')
    require(not list(STATE.glob('send-task-'+RUN_ID+'-*')), 'F03_OWN_SEND_INTENT_ALREADY_EXISTS')
    return dict(records=records, manifest_sha256=digest(encoded(records)), cursor=dict(path=str(STATE/'cursor.json'), bytes=len(raw), sha256=digest(raw)))


def inventory(path):
    path = Path(path)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'F03_MUTABLE_PATH_LINK')
    if not path.exists():
        return dict(state='ABSENT', path=str(path))
    info = path.stat()
    if stat.S_ISREG(info.st_mode):
        return dict(state='FILE', ref=pin(path), identity=identity(info))
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode)&0o002, 'F03_MUTABLE_ROOT_CUSTODY')
    paths = sorted(path.rglob('*')); require(len(paths) <= 4096, 'F03_ONCE_INVENTORY_BOUND')
    records = []; total = 0
    for leaf in paths:
        require(not leaf.is_symlink(), 'F03_ONCE_INVENTORY_LINK')
        if leaf.is_file():
            row = pin(leaf); total += row['bytes']; require(total <= 24*1024**2, 'F03_ONCE_INVENTORY_BYTES_BOUND')
            records.append([str(leaf.relative_to(path)), row['bytes'], row['sha256']])
    return dict(state='DIRECTORY', path=str(path), records=records, manifest_sha256=digest(encoded(records)))


def proof_documents(effect):
    result = {}
    for name, row in effect['root_proofs'].items():
        value = docref(row)
        if name == 'original_selection':
            require(row['path'] == ORIGINAL_SELECTION_PATH and row['sha256'] == ORIGINAL_SELECTION_SHA
                    and value.get('schema') == 'friday.Root.F03.original-required-formula-variant-phase-decision.v1'
                    and value.get('state') == 'ORIGINAL_REQUIRED_ODS_FORMULA_VARIANT_FIRST_ORDINARY_PHASE_SELECTED_PENDING_CURRENT_ADMISSION'
                    and value.get('execution_grant') is False and value.get('current_admission') is False
                    and value.get('original_case') == 164 and value.get('case_id') == CASE and value.get('format') == 27
                    and value.get('variant') == 'formulas/v02' and value.get('existing_ledger_pointer') == '/operation_rows/667', 'F03_ROOT_ORIGINAL_VARIANT_DECISION_REQUIRED')
            for key in ('selected_proposal', 'Root_receives_exact68_result', 'canonical_comparison', 'retained_scope_comparison', 'source110_original_request'):
                readref(value[key], private=False)
        elif name == 'source_review':
            require(value.get('decision') == 'SOURCE_ONLY_READY_UNBOUND' and value.get('open_critical_defects') == [], 'F03_INDEPENDENT_SOURCE_REVIEW_NOT_READY')
        else:
            require(value.get('schema') == 'frw.Root.f03.'+name+'.v1' and value.get('operator') == 'Root'
                    and value.get('case') == CASE and value.get('operation_id') == OPERATION and value.get('phase') == PHASE
                    and value.get('run_id') == RUN_ID and value.get('source_sha256') == SOURCE['sha256'], 'F03_EXACT_SCOPED_ROOT_REVIEW_REQUIRED_'+name)
            require(type(value.get('evidence')) is list and value['evidence'], 'F03_ROOT_EVIDENCE_UNBOUND_'+name)
            for dependency in value['evidence']:
                readref(dependency, private=False)
        result[name] = value
    return result


def private_roots(effect, proof, reviews):
    evidence = reviews['private_exclusion']; roots = evidence.get('private_roots'); product = evidence.get('effective_product_roots')
    require(type(roots) is list and roots and type(product) is list and product, 'F03_EFFECTIVE_PRIVATE_PRODUCT_ROOTS_UNBOUND')
    required = {str(Path(effect[k]['path']).parent) for k in ('adapter', 'current_gate', 'scenario_ref', 'proposal_ref', 'source')}
    required.update(str(Path(r['path']).parent) for r in effect['root_proofs'].values())
    required.add(str(Path(proof['native_request']['path']).parent))
    required.add(str(Path(effect['resources']['clock']['path']).parent))
    require(required <= set(roots), 'F03_PRIVATE_INPUT_ROOT_SET_INCOMPLETE')
    for root in roots+product:
        path = Path(root)
        require(type(root) is str and not root.startswith('//') and all(ord(ch) >= 32 and ord(ch) != 127 for ch in root)
                and path.is_absolute() and str(path) == root and '..' not in path.parts
                and not any(p.is_symlink() for p in (path, *path.parents))
                and path.is_dir(), 'F03_CANONICAL_NO_ALIAS_PRIVATE_PRODUCT_ROOT_REQUIRED')
    for own in map(Path, roots):
        for visible in map(Path, product):
            require(not own.is_relative_to(visible) and not visible.is_relative_to(own), 'F03_PRIVATE_PRODUCT_ROOT_OVERLAP')
    return tuple(root.encode() for root in roots)


def semantics(effect, reviews, observed):
    boundary = observed['f03_mutable_boundary']; selected = reviews['original_selection']; custody = reviews['source_custody']; hist = reviews['all_profile_history_semantic_once']; owned = reviews['owned_actor_stop_resources']; privacy = reviews['private_exclusion']
    require(selected.get('phase_boundaries', {}).get('ordinary_ingress') == 'NOT_RUN_SELECTED_PHASE; real receiver/native receipt is future postcondition of admitted first upload, never a fabricated precondition PASS'
            and custody.get('same_authorized_principal') is True and custody.get('selected_native_scope') == observed['selected_scope'], 'F03_ORIGINAL_FRONTIER_PRINCIPAL_OR_ROUTE_UNBOUND')
    require(custody.get('source_ref') == SOURCE and custody.get('source_stat') == observed['source_stat']
            and custody.get('root_fixture_owned') is True and custody.get('principal_acl_reviewed') is True
            and custody.get('ordinary_ingress_existing_required') is False and custody.get('unchanged_source_required') is True, 'F03_ROOT_FIXTURE_CUSTODY_ACL_UNBOUND')
    require(hist.get('history_manifest_sha256') == boundary['history_manifest_sha256']
            and hist.get('native_manifests') == {k: v['manifest_sha256'] for k, v in observed['databases'].items()}
            and hist.get('once_sha256') == boundary['once_sha256'] and hist.get('mutable_paths_sha256') == boundary['mutable_paths_sha256']
            and hist.get('equivalent_original_phase_effects') == [] and hist.get('unresolved_original_phase_equivalents') == []
            and hist.get('all_profiles_and_compacted_unlogged_equivalents_reconciled') is True
            and hist.get('old_effects_UNKNOWN_and_clocks_preserved') is True
            and hist.get('retained_effects') == {'R86': 'CONSUMED', 'oldS11': 'CONSUMED', 'source110': 'UNKNOWN'}, 'F03_ALL_PROFILE_SEMANTIC_ONCE_UNBOUND_OR_CONSUMED')
    require(privacy.get('current_context_files_complete_for_selected_action') is True
            and privacy.get('private_inputs_not_ingested_or_product_visible') is True
            and privacy.get('history_manifest_sha256') == boundary['history_manifest_sha256']
            and privacy.get('native_manifests') == {k: v['manifest_sha256'] for k, v in observed['databases'].items()}
            and privacy.get('current_files') == observed['current_files'], 'F03_FRESH_PRIVATE_CONTEXT_EXCLUSION_UNBOUND')
    require(owned.get('resources') == effect['resources'] and owned.get('mutable_paths_complete_for_action') is True
            and owned.get('current_files') == observed['current_files'] and owned.get('native_implementation_sha256') == NATIVE_SHA
            and owned.get('cancel_root_only') is True and owned.get('no_old_effect_replay') is True
            and owned.get('new_effect_unconsumed') is True and owned.get('source_fixture_no_product_write') is True,
            'F03_OWNED_CANCEL_ROUTE_OR_RESOURCE_REVIEW_UNBOUND')
    return True


def resources(effect, gateway, *, first_send=None):
    if first_send is None:
        value = docref(effect['resources']['clock']); now = time.monotonic(); wall = time.time()
        require(value.get('schema') == 'frw.Root.f03.original-clock.v1' and value.get('operator') == 'Root' and value.get('run_id') == RUN_ID and value.get('boot_id') == gateway['boot_id'], 'F03_ORIGINAL_ROOT_CLOCK_UNBOUND')
        for key in ('origin_monotonic', 'deadline_monotonic', 'origin_wall', 'deadline_wall'):
            require(type(value.get(key)) in (int, float) and math.isfinite(value[key]), 'F03_ORIGINAL_CLOCK_FINITE_REQUIRED')
        require(0 <= value['origin_monotonic'] <= now < value['deadline_monotonic'] <= value['origin_monotonic']+600
                and value['origin_wall'] <= wall < value['deadline_wall'] <= value['origin_wall']+600
                and abs((wall-value['origin_wall'])-(now-value['origin_monotonic'])) <= 2
                and now+300 <= value['deadline_monotonic'], 'F03_ORIGINAL_OUTER600_OR_FULL300_WINDOW_EXHAUSTED')
    else:
        module=separate_first_send(first_send)
        _,value=module.contract(first_send['contract'],preintent=True,active=True)
        require(value.get('boot_id')==gateway['boot_id'], 'F03_SEPARATE_PHASE_GATEWAY_BOOT_CHANGED')
        require(effect['resources']['clock']==module.OLD_CLOCK, 'F03_ORIGINAL_CLOCK_REFERENCE_CHANGED')
    memory = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    fs = os.statvfs(STATE); available = fs.f_bavail*fs.f_frsize
    require(memory >= effect['resources']['max_rss_bytes'] and available >= effect['resources']['disk_bytes'] and os.sched_getaffinity(0), 'F03_REQUIRED_FINITE_RESOURCES_UNAVAILABLE')
    return value


def observe(proof, *, boundary_phase='NEW', first_send=None, first_send_preclaim=False):
    """Observe a caller's pre-intent phase without rewriting Root's proof."""
    require(boundary_phase in PRE_INTENT_BOUNDARY_PHASES, 'F03_PREINTENT_ONLY')
    proof_shape(proof); effect = proof['contract_effect']; a = load(effect['adapter'], '_F03_reviewed_adapter')
    c = dict(effect, status='UNBOUND_NOT_GRANTED', root_current_review=None)
    a.contract_shape(c, bound=False); require(a.effect(c) == effect, 'F03_ADAPTER_WHOLE_EFFECT_SHAPE_CHANGED')
    require(readref(effect['current_gate'], private=False) == read(HERE/'current221.py'), 'F03_SELF_SOURCE_CHANGED')
    scenario = docref(effect['scenario_ref']); a.scenario_shape(scenario); require(digest(encoded(scenario)) == effect['scenario_sha256'], 'F03_SCENARIO_CANONICAL_SHA_CHANGED')
    readref(effect['proposal_ref']); source_raw = readref(SOURCE)
    info = Path(SOURCE['path']).stat(); source_stat = {k: getattr(info, 'st_'+{'device': 'dev', 'inode': 'ino', 'size_bytes': 'size'}.get(k, k)) for k in a.INPUT_STAT_FIELDS}
    require(source_stat == scenario['steps'][0]['input']['stat'] and len(source_raw) == SOURCE['bytes'], 'F03_CURRENT_ROOT_SOURCE_STAT_CHANGED')
    reviews = proof_documents(effect); markers = private_roots(effect, proof, reviews);
    if first_send is not None:
        ph=separate_first_send(first_send,preclaim=first_send_preclaim)
        if ph.is_preclock(first_send):
            refs=[ph.PRISTINE,ph.CLOSURE,ph.OLD_CLOCK,*ph.MARKERS]
            roots={str(ph.STATE),str(ph.ONCE.parent),str(HERE.parent),first_send['private_workdir']}
        else:
            pc,_=ph.contract(first_send['contract'],preintent=True,active=True)
            refs=[first_send['contract'],first_send['once'],first_send['before'],pc['implementation'],pc['consumer'],pc['decision'],pc['reconciliation'],pc['clock']]
            roots=set()
        require(roots | {str(Path(x['path']).parent) for x in refs} <= set(reviews['private_exclusion']['private_roots']), 'F03_SEPARATE_PHASE_PRIVATE_ROOTS_OMITTED')
        owned=[ph.ONCE,ph.BEFORE,STATE/'runs'/(RUN_ID+'.json')]
        for selector in proof['mutable_paths']:
            selected=Path(selector['path'])
            require(not any(path==selected or path.is_relative_to(selected) or selected.is_relative_to(path) for path in owned), 'F03_SELF_MUTATION_IN_GENERIC_CAS_SELECTOR')
    h = helper(); closed = closure()
    product, canonical = installed(closed, proof['current_files']); units = services(closed, h)
    value, gateway, state_raw = native(proof, h)
    require(gateway == dict(pid=closed['services']['gateway']['pid'], start_time=closed['services']['gateway']['birth_ticks'], boot_id=closed['services']['gateway']['boot_id']), 'F03_CLOSED221_CURRENT_WRITER_CHANGED')
    for leaf in ('cmdline', 'environ'):
        raw = (Path('/proc')/str(gateway['pid'])/leaf).read_bytes()
        require(len(raw) <= 1024**2 and not any(marker in raw for marker in markers), 'F03_PRIVATE_ORACLE_IN_PRODUCT_PROCESS')
    for row in proof['current_files']+reviews['private_exclusion'].get('current_context_files', []):
        raw = readref(row, private=False); require(not any(marker in raw for marker in markers), 'F03_PRIVATE_ORACLE_IN_PRODUCT_CONFIG_CONTEXT')
    databases = {slot: database(slot, markers, value['scopes'].get(slot)) for slot in PROFILE_HOMES}
    selected = value['scopes']['B']; sessions = databases['B']
    routes = [row for row in databases['default']['routes'] if row[0] == str(H/'sessions') and row[1] == KEY]
    require(len(routes) == 1, 'F03_ACTUAL_ORIGINAL_SESSION_ROUTE_MISSING')
    route = json.loads(routes[0][2], object_pairs_hook=unique)
    require(route.get('session_id') == SID and route.get('session_key') == KEY and route.get('platform') == 'telegram'
            and route.get('chat_type') == 'dm' and route.get('transport_profile', 'default') == 'default'
            and not route.get('active_turn_token') and not route.get('pending_command_text') and not route.get('resume_pending'), 'F03_SELECTED_ROUTE_CHANGED_OR_OWNS_OLD_PENDING_ACTION')
    hist = history(effect, scenario, boundary_phase, first_send=first_send, first_send_preclaim=first_send_preclaim)
    require(not (STATE/'observer-stop.json').exists(), 'F03_OBSERVER_STOP_RETAINED')
    if (STATE/'cooldown.json').exists():
        cool = json.loads(read(STATE/'cooldown.json', private=True), object_pairs_hook=unique)
        require(time.time() >= cool.get('until', 0), 'F03_COOLDOWN_RETAINED')
    paths = [{'category': row['category'], 'value': inventory(row['path'])} for row in proof['mutable_paths']]
    required_recovery = set(closed['related_recovery_data_cutoff_scope']['related_recovery_state_paths'])
    require(required_recovery <= {row['path'] for row in proof['mutable_paths'] if row['category'] == 'recovery'}, 'F03_CLOSED_RECOVERY_CANCEL_SCOPE_OMITTED')
    once = {leaf: inventory(STATE/leaf) for leaf in ('continuations', 'reconciliations')}
    boundary = dict(gateway=gateway, installed_closure_sha256=CLOSURE_SHA, canonical4_sha256=digest(encoded(canonical)), source_stat_sha256=digest(encoded(source_stat)), history_manifest_sha256=hist['manifest_sha256'], canonical_cursor_sha256=hist['cursor']['sha256'], current_files_sha256=digest(encoded(proof['current_files'])), once_sha256=digest(encoded(once)), mutable_paths_sha256=digest(encoded(paths)), native_boundary_sha256=digest(encoded(dict(native=native_stable(value), databases=databases))))
    require(read(H/'gateway_state.json') == state_raw, 'F03_CURRENT_STATE_CAS_AFTER_COLLECTORS')
    selected_scope = {k: selected[k] for k in ('principal_id', 'profile', 'session_id', 'session_key', 'native_session_generation', 'access')}
    return dict(admission=False, installed_product=product, gateway=gateway, native_readonly=value, selected_scope=selected_scope, canonical4=canonical, services=units, source_stat=source_stat, history=hist, databases=databases, current_files=proof['current_files'], mutable_paths=paths, once=once, f03_mutable_boundary=boundary)


def shared_slot(owner, h):
    require(type(owner) is dict and set(owner) == {'pid', 'start_time', 'boot_id'}, 'F03_ACTUAL_ROOT_SHARED_SLOT_OWNER_REQUIRED')
    info = SLOT.stat()
    require(info.st_uid == os.getuid() and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600
            and not any(p.is_symlink() for p in (SLOT, *SLOT.parents)) and h.kernel(owner['pid']) == owner, 'F03_ROOT_SLOT_CUSTODY_OR_KERNEL_CHANGED')
    key = f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}'
    require(any(len(parts := line.split()) >= 6 and parts[1] == 'FLOCK' and parts[3] == 'WRITE'
                and parts[4] == str(owner['pid']) and parts[5] == key for line in Path('/proc/locks').read_text().splitlines()), 'F03_ROOT_EXISTING_EXCLUSIVE_SLOT_NOT_HELD')


def check(path, sha, *, boundary_phase='NEW', first_send=None):
    """Verify the caller's phase against Root's immutable <=120s proof."""
    require(boundary_phase in PRE_INTENT_BOUNDARY_PHASES, 'F03_PREINTENT_ONLY')
    raw = read(path, private=True); require(digest(raw) == sha, 'F03_ROOT_CURRENT_PROOF_PIN_CHANGED')
    proof = json.loads(raw, object_pairs_hook=unique)
    require(proof.get('status') == 'ROOT_BOUND', 'F03_UNBOUND_OR_PREPARED_PROOF_NOT_CURRENT_ADMISSION')
    proof_shape(proof); lifetime(proof)
    effect = proof['contract_effect']; a = load(effect['adapter'], '_F03_check_reviewed_adapter')
    a.contract_shape(dict(effect, status='ROOT_BOUND_EXACT_F03', root_current_review=dict(path=str(path), bytes=len(raw), sha256=sha)))
    actual = observe(proof, boundary_phase=boundary_phase, first_send=first_send); saved = proof.get('observed')
    require(type(saved) is dict, 'F03_ROOT_OBSERVED_BOUNDARY_UNBOUND')
    for key in ('installed_product', 'gateway', 'selected_scope', 'canonical4', 'services', 'source_stat', 'history', 'databases', 'current_files', 'mutable_paths', 'once', 'f03_mutable_boundary'):
        require(actual[key] == saved.get(key), 'F03_CURRENT_CAS_CHANGED_'+key)
    require(native_stable(actual['native_readonly']) == native_stable(saved.get('native_readonly', {})), 'F03_CURRENT_NATIVE_GENERATION_CUSTODY_CHANGED')
    require(effect.get('mutable_boundary') == actual['f03_mutable_boundary'], 'F03_ROOT_EFFECT_MUTABLE_BOUNDARY_UNBOUND')
    reviews = proof_documents(effect); semantics(effect, reviews, actual); resources(effect, actual['gateway'], first_send=first_send); h = helper(); shared_slot(proof.get('shared_slot_owner'), h)
    final_observed = observe(proof, boundary_phase=boundary_phase, first_send=first_send)
    for key in ('installed_product', 'gateway', 'selected_scope', 'canonical4', 'services', 'source_stat', 'history', 'databases', 'current_files', 'mutable_paths', 'once', 'f03_mutable_boundary'):
        require(final_observed[key] == actual[key], 'F03_FINAL_MUTABLE_CAS_CHANGED_'+key)
    final = final_observed['native_readonly']; gateway = final_observed['gateway']
    require(native_stable(final) == native_stable(actual['native_readonly']), 'F03_FINAL_NATIVE_KERNEL_SCOPE_CAS_CHANGED')
    resources(effect, gateway, first_send=first_send); lifetime(proof)
    return dict(admission=False, installed_product=dict(EXPECTED), Root_proof_sha256=sha, f03_mutable_boundary=actual['f03_mutable_boundary'], whole_effect_sha256=digest(encoded(effect)), gateway=gateway, native_readonly=dict(schema='frw.F03.selected-native-readonly.v1', read_only=True, quiescent=True, session_id=SID, session_key=KEY, identity=gateway, generation=final['scopes']['B']['native_session_generation'], genuine_snapshot=final))
