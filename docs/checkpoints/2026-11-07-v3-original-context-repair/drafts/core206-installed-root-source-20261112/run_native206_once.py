"""Root finite native206 one-time maintenance; source preparation is not execution.
New original1800; CP original600/unit810/client840 and cold180each retained.
Source200 scripts/archived pairing/R92/g1/g2 consumed effects are never replayed.
On any error retain journal/clocks, reconcile exact state; never rerun this actor.
Partial permanent start keeps original phase deadline; no repeated start request.
"""
from pathlib import Path
import sys, os, json, hashlib, subprocess, sqlite3, socket, time, datetime, fcntl, stat, signal

if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode):
    raise RuntimeError('isolated_nonoptimized_no_bytecode_python_required')
assert sys.argv[1:] == ['--execute-once-root-accepted-206'], 'explicit_Root_execute_once_mode_required'
os.umask(0o077)
sys.dont_write_bytecode = True
B = Path(__file__).parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N = H / 'hermes-agent'
P = Path('/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/project491')
C = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112/project493')
CP = B / 'publication/friday_v3_layer_publication.py'
RESTORE = B / 'resume_native206_services.py'
REQ = B / 'ROOT-FRESH-REQUEST.json'
PY = str(H / 'installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python')
GW = 'hermes-gateway-1b7e7667.service'
DASH = 'hermes-dashboard.service'
PUB = 'frw-astra-native206-install-after205-20261112.service'
now = lambda: datetime.datetime.now().astimezone().isoformat()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Safe metadata module has no product/API imports or collection effects.
import importlib.util
assert sha(B / 'root206_metadata.py') == '4c27068c38ebd28d8621c0b3af181ce0891ba27977de76a5d12e2fa0b562a929'
binding_spec = importlib.util.spec_from_file_location('root206_metadata', B / 'root206_metadata.py')
binding = importlib.util.module_from_spec(binding_spec); binding_spec.loader.exec_module(binding)
assert sha(CP) == '7e8e886adaf738296ded1fda09740df5b242d6ad3b98d4bcdb29d8ada672da9c'
assert sha(RESTORE) == '4f53ff97d238d71cca4463dec88a9a30500627825ec54ccfa0dfdc426fcbc680'
SOURCE_ACCEPTANCE = B / 'ROOT-206-SOURCE-ACCEPTANCE.json'
bound = binding.load_actor_binding(B)
EXPECTED = bound['expected_receipt_sha256']
q = json.loads(REQ.read_bytes())
cur = json.loads(Path(q['current_input']['path']).read_bytes())
previous = json.loads(Path(q['previous_input']['path']).read_bytes())
assert len(cur['project_files']) == 493
assert len(previous['project_files']) == 491
assert q['home'] == str(H) and q['candidate_project'] == str(C) and q['seconds'] == 600
assert q['layer_names'] == ['f06-protected-office-profiles-after-source205']
tx = H / 'preparation' / ('ordinary-source-update-v45-' + sha(REQ)[:16])
assert not os.path.lexists(tx)
for name, expected in cur['project_files'].items():
    assert sha(C / name) == expected, name
for name, expected in previous['project_files'].items():
    assert sha(P / name) == expected, name
for name in ['marker', 'source_receipt', 'stamp', 'configuration', 'profile', 'launcher', 'native_unit',
        'previous_input', 'current_input', 'predecessor_request', 'target_receipt', 'candidate_input']:
    assert sha(q[name]['path']) == q[name]['sha256'], name
before_receipt = json.loads((H / 'hermes-agent.source.json').read_bytes())
before_marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())
assert len(before_receipt['layers']) == 205 and len(before_marker['plugin_files']) == 52
assert sha(H / 'hermes-agent.source.json') == 'aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb'
layer = json.loads((C / 'patches/hermes/f06-protected-office-profiles-after-source205-manifest.json').read_bytes())
targets = {x['path']: x['sha256'] for x in layer['files']}
SPEC = Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112/FINAL-NATIVE-SPEC.json')
assert sha(SPEC) == '90b12d3a915e9c841f15360588094119ffe9fe40e1e3813a2cb630ec6a1e9e56'
spec = json.loads(SPEC.read_bytes())
assert layer['files'] == spec['native_files']
assert len(targets) == 11
assert bound['selected_target_count'] == 17
native_additions = {row['path'] for row in layer['files'] if row['new_file']}
assert native_additions == set()
assert set(before_receipt['files']) & native_additions == set()
assert len(before_receipt['files']) == 17891
assert before_marker['input_sha256'] == q['previous_input']['sha256']
assert q['schema'] == 'friday.ordinary-telegram-source-update.v46'
assert q['current_source_successor']['schema'] == 'friday.current-source-native-successor.v8'
assert q['current_source_successor']['previous_native_update'] == bound['genuine_actual205_predecessor']
assert sha(q['current_source_successor']['previous_native_update']['path']) == q['current_source_successor']['previous_native_update']['sha256']
assert q['project_file_updates'] == ['scripts/friday_ordinary_install.py']
for row in layer['files']:
    path = N / row['path']
    assert not os.path.lexists(path) if row['new_file'] else sha(path) == row['before_sha256'], row['path']
project_targets = set(q['project_file_updates'] + q['layer_manifest_updates'] + [f'patches/hermes/{name}.patch' for name in q['layer_names']])
os.environ.update(HERMES_HOME=str(H), HERMES_GATEWAY_LOCK_DIR='/home/jericho/.local/state/hermes/gateway-locks',
    GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
assert sha(P / 'scripts/friday_install.py') == '47273b21753788012bd23f43fcc34e7c97adcd4841848eea2a3023dc60536f27'
assert sha(P / 'scripts/friday_ordinary_install.py') == 'f570120371c28eeeb9f708ffbd32d451056c39fc57f7a49ed60eb9db0eb26cb5'
sys.path.insert(0, str(P))
from scripts import friday_install as f
f.native_packages(N)
from scripts import friday_ordinary_install as ordinary
from scripts.install_containment import Budget
assert Path(f.__file__).resolve() == P / 'scripts/friday_install.py'
assert sha(f.__file__) == '47273b21753788012bd23f43fcc34e7c97adcd4841848eea2a3023dc60536f27'
assert sha(ordinary.__file__) == 'f570120371c28eeeb9f708ffbd32d451056c39fc57f7a49ed60eb9db0eb26cb5'

def remaining(deadline, seconds=None):
    value = deadline - time.monotonic()
    if value <= 0:
        raise RuntimeError('original_maintenance_budget_exhausted')
    return value if seconds is None else min(seconds, value)

def operation_remaining(*, reserve=75, seconds=None):
    return remaining(origin + 1800 - reserve, seconds)

def command(args, seconds=5, *, deadline=None):
    if deadline is None and 'origin' in globals():
        deadline = origin + 1800 - 75
    timeout = seconds if deadline is None else remaining(deadline, seconds)
    return subprocess.run(args, capture_output=True, timeout=timeout, check=False)

def service(name=GW, *, deadline=None):
    r = command(['systemctl', '--user', 'show', name,
        '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,NRestarts,InvocationID,Result,ExecMainStatus,ControlGroup,UnitFileState,Description,RuntimeMaxUSec'], deadline=deadline)
    assert r.returncode == 0
    return dict(x.split('=', 1) for x in r.stdout.decode().splitlines())

def data():
    out = {}
    data_end = time.monotonic() + 15
    for name, relative in [('default', 'state.db'), ('dest_telegram', 'profiles/dest_telegram/state.db'),
            ('telegram-bot-8812646969', 'profiles/telegram-bot-8812646969/state.db')]:
        with sqlite3.connect((H / relative).as_uri() + '?mode=ro', uri=True, timeout=1) as db:
            db.set_progress_handler(lambda: int(time.monotonic() >= data_end), 10000)
            remaining(data_end)
            qc = db.execute('PRAGMA quick_check').fetchone()[0]
            leases = db.execute('select count(*) from session_turn_leases').fetchone()[0]
            assert qc == 'ok' and leases == 0
            out[name] = {'quick_check': qc, 'leases': leases,
                'messages': db.execute('select count(*) from messages').fetchone()[0],
                'sessions': db.execute('select count(*) from sessions').fetchone()[0]}
    return out

def local_group_absent(child):
    try: os.killpg(child.pid, 0)
    except ProcessLookupError: return True
    return False

def reap_exact_owned_local_group(child, identity_key, flag_key):
    """Never signal a reused PID/PGID after its leader has been reaped."""
    try:
        if not local_group_absent(child):
            identity = j.get(identity_key)
            assert identity and identity['pid'] == child.pid
            assert child.returncode is None, 'reaped_leader_group_requires_Root_reconciliation'
            proc = Path('/proc') / str(child.pid)
            current_birth = int((proc / 'stat').read_text().rsplit(')',1)[1].split()[19])
            assert current_birth == identity['birth_ticks'], 'owned_local_PID_birth_changed'
            assert os.getpgid(child.pid) == os.getsid(child.pid) == child.pid, 'owned_local_session_group_changed'
            os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=5)
        assert local_group_absent(child), 'owned_local_descendant_group_remains_after_reap'
    except BaseException as error:
        j[flag_key] = True
        raise StopUnconfirmed('owned_local_group_cleanup_unconfirmed') from error

def run_reaped(args, *, timeout, **kwargs):
    """Own only this local observer/check process group, including failure paths."""
    child = subprocess.Popen(args, start_new_session=True, **kwargs)
    try:
        j['owned_local_process_identity'] = {'pid':child.pid, 'birth_ticks':int((Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(')',1)[1].split()[19])}
        save()
        child.wait(timeout=timeout)
        return subprocess.CompletedProcess(args, child.returncode)
    except BaseException:
        reap_exact_owned_local_group(child, 'owned_local_process_identity', 'owned_local_cleanup_unconfirmed')
        raise
    finally:
        if child.returncode is not None and not local_group_absent(child):
            j['owned_local_cleanup_unconfirmed'] = True
            raise StopUnconfirmed('reaped_local_leader_group_requires_Root_reconciliation')

def file_metadata(path):
    path = Path(path); info = path.lstat()
    assert stat.S_ISREG(info.st_mode) and not path.is_symlink()
    assert info.st_uid == os.getuid() and info.st_nlink == 1
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode, info.st_nlink]

def directory_metadata(path):
    path = Path(path); info = path.lstat()
    assert stat.S_ISDIR(info.st_mode) and not path.is_symlink() and info.st_uid == os.getuid()
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode]

def state_file_snapshot():
    """Pin stopped user DB plus WAL/SHM; never checkpoint, chmod, repair or delete."""
    result = {}
    for relative in ['state.db', 'profiles/dest_telegram/state.db', 'profiles/telegram-bot-8812646969/state.db']:
        for suffix in ['', '-wal', '-shm']:
            path = H / (relative + suffix)
            result[str(path)] = None if not os.path.lexists(path) else {'sha256':sha(path), 'metadata':file_metadata(path)}
    return result

def selected_process_environment(pid):
    selected = {b'HERMES_HOME', b'HERMES_GATEWAY_LOCK_DIR', b'HERMES_RUNTIME_DIR', b'HERMES_INSTALL_ROOT', b'HERMES_PROFILE'}
    values = {}
    for row in (Path('/proc') / str(pid) / 'environ').read_bytes().split(b'\0'):
        key, separator, value = row.partition(b'=')
        if separator and key in selected: values[key.decode()] = value.decode()
    assert values.get('HERMES_HOME') == str(H)
    assert not values.get('HERMES_GATEWAY_LOCK_DIR') or values['HERMES_GATEWAY_LOCK_DIR'] == '/home/jericho/.local/state/hermes/gateway-locks'
    assert not values.get('HERMES_RUNTIME_DIR') and not values.get('HERMES_INSTALL_ROOT')
    return values

def closed(name, *, deadline=None):
    u = service(name, deadline=deadline)
    assert u['MainPID'] == u['ControlPID'] == '0' and u['ControlGroup'] == ''
    assert u['ActiveState'] in ['inactive', 'failed']
    return u

ADMISSION = B / 'ROOT-206-FRESH-ADMISSION.json'
assert file_metadata(ADMISSION)[2] == os.getuid() and stat.S_IMODE(ADMISSION.lstat().st_mode) == 0o600
admission = json.loads(ADMISSION.read_bytes())
assert admission['schema'] == 'frw.root.native206-fresh-window-admission.v1'
assert admission['state'] == 'ROOT_ACCEPTED_EXACT206_SOURCE_AND_MINIMUM_INSTALLED_BANK_PROFILE_FINITE_WINDOW'
assert admission['home'] == str(H) and admission['request'] == {'path':str(REQ), 'sha256':sha(REQ)}
assert admission['actor'] == {'path':str(Path(__file__)), 'sha256':sha(__file__)}
assert admission['recovery'] == {'path':str(RESTORE), 'sha256':sha(RESTORE)}
assert admission['native_spec'] == {'path':str(SPEC), 'sha256':sha(SPEC)}
assert admission['source_acceptance'] == {'path':str(SOURCE_ACCEPTANCE), 'sha256':sha(SOURCE_ACCEPTANCE)}
assert admission['expected_receipt_sha256'] == EXPECTED and admission['operation_seconds'] == 1800
assert admission['bound_inputs'] == {'path':str(B / 'ROOT-206-BOUND-INPUTS.json'), 'sha256':sha(B / 'ROOT-206-BOUND-INPUTS.json')}
assert admission['budgets'] == {'forward':600,'external_rollback':180,'terminal_cleanup':30,'publisher_unit':810,'publisher_client':840,'operation':1800}
assert admission['template_only_no_execution_grant'] is False
assert admission['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert 0 <= time.time() - datetime.datetime.fromisoformat(admission['accepted_at_moscow']).timestamp() <= 300
qualification_ref = admission['minimum_installed_bank_profile_qualification']
assert file_metadata(qualification_ref['path'])[2] == os.getuid() and sha(qualification_ref['path']) == qualification_ref['sha256']
qualification = json.loads(Path(qualification_ref['path']).read_bytes())
assert qualification['state'] == 'ROOT_ACCEPTED_MINIMUM_INSTALLED_BANK_PROFILE_FOR_NATIVE206_SELECTION_NO_FORMAL_CREDIT'
assert qualification['bank_path'] == '/home/jericho/.jericho/toolchains/libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111'
assert qualification['bank_manifest_sha256'] == 'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'
assert qualification['native_spec'] == {'path':str(SPEC), 'sha256':sha(SPEC)}
assert qualification['operational_input'] == q['current_input']
assert qualification['minimum_installed_profile_accepted'] is True and qualification['formal_test_credit'] is False
assert qualification['template_only_no_execution_grant'] is False
assert 0 <= time.time() - datetime.datetime.fromisoformat(qualification['current_bank_profile_refreshed_at_moscow']).timestamp() <= 300
bank = Path(qualification['bank_path'])
assert directory_metadata(bank) == qualification['bank_directory_metadata']
assert stat.S_IMODE(bank.lstat().st_mode) == 0o500
bank_manifest = Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')
assert sha(bank_manifest) == qualification['bank_manifest_sha256']
bank_rows = {row['relative']:row for row in json.loads(bank_manifest.read_bytes())['files']}
critical_bank_paths = ['bundle-provenance.json', 'root/usr/lib/libreoffice/program/soffice',
    'root/usr/lib/libreoffice/program/soffice.bin', 'root/usr/lib/libreoffice/program/libcomphelper.so']
assert set(qualification['current_critical_bank_files']) == set(critical_bank_paths)
for name in critical_bank_paths:
    row = bank_rows[name]; path = bank / name; recorded = qualification['current_critical_bank_files'][name]
    assert sha(path) == row['sha256'] == recorded['sha256']
    assert file_metadata(path) == recorded['metadata'] and stat.S_IMODE(path.lstat().st_mode) == int(row['mode'],8)
binding.validate_profile_join(qualification, before_receipt, spec)
assert qualification['evidence'], 'exact_actual_qualification_evidence_required'
for reference in qualification['evidence']:
    file_metadata(reference['path'])
    assert sha(reference['path']) == reference['sha256']

svc = service()
dash_before = service(DASH)
g = json.loads((H / 'gateway_state.json').read_bytes())
pid = int(svc['MainPID'])
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
ticks = int((Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])
assert pid > 0 and ticks > 0 and g['pid'] == pid and g['start_time'] == ticks
assert svc['ControlPID'] == '0' and svc['ControlGroup'] and ('0::' + svc['ControlGroup']) in (Path('/proc') / str(pid) / 'cgroup').read_text().splitlines()
assert svc['ActiveState'] == 'active' and g['platforms']['telegram']['state'] == 'connected'
assert int(dash_before['MainPID']) > 0 and len(dash_before['InvocationID']) == 32
dash_proc_before = Path('/proc') / dash_before['MainPID']
dash_ticks_before = int((dash_proc_before / 'stat').read_text().rsplit(')',1)[1].split()[19])
assert dash_before['ControlPID'] == '0' and dash_before['ControlGroup'] and ('0::'+dash_before['ControlGroup']) in (dash_proc_before / 'cgroup').read_text().splitlines()
assert dash_before['ActiveState'] == 'active' and dash_before['UnitFileState'] == 'enabled'
for label, current_unit, current_pid, current_ticks in [('gateway',svc,pid,ticks),('dashboard',dash_before,int(dash_before['MainPID']),dash_ticks_before)]:
    root_identity = bound['fresh_root_services'][label]
    assert (root_identity['pid'],root_identity['birth_ticks'],root_identity['boot_id']) == (current_pid,current_ticks,boot)
    assert root_identity['invocation_id'] == current_unit['InvocationID'] and root_identity['cgroup'] == current_unit['ControlGroup']
    assert current_unit['RuntimeMaxUSec'] == 'infinity' and current_unit['UnitFileState'] == 'enabled'

dash_unit = Path('/home/jericho/.config/systemd/user/hermes-dashboard.service')
assert sha(dash_unit) == '0b91c52ec3db406f18daa545463a1692c62a5d77108a80d7645439801e155761'
before_metadata = {str(Path(q[name]['path'])): file_metadata(q[name]['path']) for name in
    ['configuration', 'profile', 'launcher', 'native_unit']}
before_metadata[str(dash_unit)] = file_metadata(dash_unit)
before_directories = {str(path): directory_metadata(path) for path in [H, N, H / 'profiles']}
before_project_targets = {name:None if not os.path.lexists(H / name) else {'sha256':sha(H / name),'metadata':file_metadata(H / name)} for name in project_targets}
process_environment = {GW: selected_process_environment(pid), DASH: selected_process_environment(int(dash_before['MainPID']))}
dash_status = command([str(N / '.hermes/bin/hermes'), '-p', 'default', 'dashboard', '--status'], 30)
assert dash_status.returncode == 0
dash_native_before = json.loads(dash_status.stdout)
assert dash_native_before['state'] == 'VERIFIED' and all(dash_native_before[n] is True for n in
    ['verified', 'nonce_verified', 'auth_required', 'servesSpa'])
assert dash_native_before['pid'] == int(dash_before['MainPID']) and dash_native_before['startTime'] == dash_ticks_before
assert dash_native_before['source_receipt_sha256'] == sha(H / 'hermes-agent.source.json')
for name, before in [(GW, svc), (DASH, dash_before)]:
    confirm = service(name)
    assert all(confirm[key] == before[key] for key in ['MainPID','ControlPID','InvocationID','ControlGroup','ActiveState','SubState'])
rpc = {'protocol': 1, 'id': 'Root-native206-maintenance-boundary-readonly', 'verb': 'ordinary-turn-readonly',
    'params': {'session_key': 'agent:telegram-bot-8812646969:telegram:dm:8812646969', 'session_id': '20261030_093055_43bba39f'}}
with socket.socket(socket.AF_UNIX) as sock:
    rpc_end = time.monotonic() + 5
    sock.settimeout(2)
    sock.connect(str(H / 'gateway.sock'))
    sock.sendall((json.dumps(rpc) + '\n').encode())
    raw = b''
    while b'\n' not in raw:
        sock.settimeout(remaining(rpc_end, 2))
        chunk = sock.recv(65536)
        assert chunk and len(raw) + len(chunk) < 524288
        raw += chunk
v = json.loads(raw)
snap = v['result']['snapshot']
assert v['ok'] and v['result']['accepted'] and snap['answering_pid'] == pid and snap['birth_ticks'] == ticks and snap['boot_id'] == boot
for name in ['active', 'active_session_keys', 'turn_tokens', 'active_adapters', 'adapter_generations', 'pending_messages',
        'queued_events', 'pending_command', 'approvals', 'detached_owned_work', 'live_owned_delegations', 'durable_pending_delegations']:
    assert not snap[name], name
assert snap['web_custody']['status'] == snap['terminal_custody']['status'] == 'QUIESCENT'
counts = data()
actor_pid = os.getpid()
actor_birth_ticks = int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19])
assert 0 <= time.time() - datetime.datetime.fromisoformat(admission['accepted_at_moscow']).timestamp() <= 300
origin = time.monotonic()
J = B / 'ROOT-NATIVE206-LIVE-OPERATION.json'
j = {'schema': 'frw.root.native206-maintenance.v1', 'state': 'ORIGINAL_MAINTENANCE_STARTED',
    'actor_identity':{'pid':actor_pid,'birth_ticks':actor_birth_ticks,'boot_id':boot}, 'custody_hold_nonce':os.urandom(16).hex(),
    'started_at_moscow': now(), 'origin_monotonic': origin, 'absolute_deadline_monotonic': origin + 1800,
    'budgets': {'maintenance': 1800, 'stop_each': 45, 'native_publisher_original': 600, 'external_rollback_reserve': 180, 'publisher_terminal_cleanup': 30, 'publisher_unit_runtime': 810,
        'postcheck': 90, 'cold_gateway': 180, 'cold_dashboard': 180, 'cleanup_reserve': 75, 'publisher_client_wait': 840},
    'gateway_before': {'pid': pid, 'start_time': ticks, 'boot_id': boot, 'unit': svc}, 'dashboard_before': dash_before,
    'dashboard_native_before': dash_native_before, 'dashboard_birth_ticks_before': dash_ticks_before,
    'unchanged_metadata': before_metadata, 'unchanged_directories': before_directories, 'process_environment': process_environment,
    'user_data_before': counts, 'plugin_files_before':before_marker['plugin_files'], 'before_project_targets':before_project_targets, 'request': {'path': str(REQ), 'sha256': sha(REQ)}, 'publisher_sha256': sha(CP),
    'current_input': q['current_input'], 'fresh_root_admission':{'path':str(ADMISSION),'sha256':sha(ADMISSION)},
    'minimum_installed_bank_profile_qualification':qualification_ref, 'before_readonly_snapshot': snap, 'native_before_after': [205, 206],
    'restore_service_source': {'path':str(RESTORE), 'sha256':sha(RESTORE)},
    'publisher_owned_description':'Root-native206-' + sha(REQ)[:16] + '-' + os.urandom(16).hex(),
    'expected_receipt_sha256': EXPECTED, 'new_model_Telegram_worker_operations': 0, 'events': [], 'service_phases': {}, 'source_frame_sha256': sha(__file__)}
fd = os.open(J, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    json.dump(j, stream, indent=2)
    stream.write('\n')
    stream.flush()
    os.fsync(stream.fileno())
directory_fd = os.open(J.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try: os.fsync(directory_fd)
finally: os.close(directory_fd)

def save():
    temporary = J.with_name('.' + J.name + '.pending')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(j, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, J)
    directory_fd = os.open(J.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(directory_fd)
    finally: os.close(directory_fd)

def event(name, **values):
    j['events'].append({'name': name, 'at_moscow': now(), **values})
    save()

def unchanged_user(*, reserve=75):
    operation_remaining(reserve=reserve)
    for name in ['configuration', 'profile', 'launcher', 'native_unit']:
        assert sha(q[name]['path']) == q[name]['sha256'], name
    assert sha(dash_unit) == '0b91c52ec3db406f18daa545463a1692c62a5d77108a80d7645439801e155761'
    assert all(file_metadata(path) == expected for path, expected in before_metadata.items())
    assert all(directory_metadata(path) == expected for path, expected in before_directories.items())
    assert data() == counts
    marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())
    assert marker['plugin_files'] == before_marker['plugin_files']
    for name, expected in marker['plugin_files'].items():
        assert sha(H / name) == expected
    operation_remaining(reserve=reserve)

class StopUnconfirmed(RuntimeError):
    pass

def publisher_cgroup_empty():
    group = j.get('publisher_cgroup')
    if not group: return True
    assert group.startswith('/user.slice/') and group.endswith('/' + PUB) and '..' not in Path(group).parts
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not base.exists(): return True
    events = dict(row.split() for row in (base / 'cgroup.events').read_text().splitlines())
    return events.get('populated') == '0' and not (base / 'cgroup.procs').read_text().strip()

def remember_publisher_identity(u):
    assert u['Description'] == j['publisher_owned_description'], 'publisher_name_conflict_no_authority_to_stop'
    invocation = u['InvocationID']; assert len(invocation) == 32
    assert j.get('publisher_invocation_id') in [None, invocation], 'publisher_invocation_changed'
    j['publisher_invocation_id'] = invocation
    if u['ControlGroup']:
        group = u['ControlGroup']
        assert group.startswith('/user.slice/') and group.endswith('/' + PUB) and '..' not in Path(group).parts
        assert j.get('publisher_cgroup') in [None, group]
        j['publisher_cgroup'] = group
    if int(u['MainPID']) > 0:
        proc = Path('/proc') / u['MainPID']
        ticks = int((proc / 'stat').read_text().rsplit(')', 1)[1].split()[19])
        assert '0::' + u['ControlGroup'] in (proc / 'cgroup').read_text().splitlines()
        current_identity = {'pid':int(u['MainPID']), 'birth_ticks':ticks}
        assert j.get('publisher_process_identity') in [None,current_identity], 'publisher_main_process_identity_changed'
        j['publisher_process_identity'] = current_identity
    save()

def publisher_process_closed():
    identity = j.get('publisher_process_identity')
    assert identity and j.get('publisher_invocation_id') and j.get('publisher_cgroup'), 'owned_publisher_exact_binding_missing'
    proc = Path('/proc') / str(identity['pid'])
    if not proc.exists(): return True
    try: current_birth = int((proc / 'stat').read_text().rsplit(')', 1)[1].split()[19])
    except FileNotFoundError: return True
    return current_birth != identity['birth_ticks']

def publisher_terminal_proven(*, deadline):
    """not-found alone is insufficient: this attempt must first bind its invocation."""
    assert j.get('publisher_invocation_id') and j.get('publisher_cgroup') and j.get('publisher_process_identity'), 'owned_publisher_exact_binding_missing'
    result = closed(PUB, deadline=deadline)
    if result['LoadState'] != 'not-found':
        assert result['Description'] == j['publisher_owned_description']
        # A collected inactive unit may already have cleared its invocation.
        # Prior exact binding plus both cessation proofs below remain mandatory.
        assert result['InvocationID'] in [j['publisher_invocation_id'], ''], 'publisher_invocation_changed'
    assert publisher_cgroup_empty() and publisher_process_closed(), 'owned_publisher_scope_not_closed'
    return result

def close_owned_publisher(custody_deadline):
    """Close only the nonce/invocation-pinned publisher admitted by this attempt."""
    try:
        if j.get('publisher_client_spawn_failed_before_child_created'):
            result = closed(PUB, deadline=custody_deadline)
            assert result['LoadState'] == 'not-found' and not j.get('publisher_invocation_id'), 'failed_spawn_publisher_name_no_longer_unused'
        else:
            result = publisher_terminal_proven(deadline=custody_deadline)
    except BaseException:
        current = service(PUB, deadline=custody_deadline)
        remember_publisher_identity(current)
        # A terminal not-found with no prior exact binding remains ambiguous.
        assert j.get('publisher_process_identity') and j.get('publisher_cgroup'), 'owned_publisher_exact_binding_missing'
        j['publisher_close_requested'] = True
        save()
        close_end = min(time.monotonic() + 30, custody_deadline)
        stop = command(['systemctl', '--user', 'stop', '--no-block', PUB], deadline=close_end)
        event('publisher_exact_unit_stop_requested', returncode=stop.returncode)
        if stop.returncode != 0:
            current = service(PUB, deadline=close_end)
            remember_publisher_identity(current)
            j['publisher_exact_kill_consumed_no_retry'] = True; save()
            kill = command(['systemctl','--user','kill','--kill-whom=all','--signal=SIGKILL',PUB],deadline=close_end)
            event('publisher_exact_owned_unit_kill_requested',returncode=kill.returncode)
        while time.monotonic() < close_end:
            try:
                result = publisher_terminal_proven(deadline=close_end)
                break
            except (AssertionError, subprocess.TimeoutExpired):
                time.sleep(min(.1, remaining(close_end)))
        else:
            raise StopUnconfirmed('publisher_unit_or_cgroup_not_confirmed_closed')
    j['publisher_terminal_unit'] = result
    j['publisher_closed_before_parent_custody_release'] = True
    save()
    return result

def run_owned_publisher(args, *, stdout, stderr, client_deadline):
    """Observe the exact transient invocation while the one consumed launch runs."""
    try:
        child = subprocess.Popen(args, stdout=stdout, stderr=stderr, start_new_session=True)
    except OSError:
        j['publisher_client_spawn_failed_before_child_created'] = True
        save()
        raise
    try:
        # None means UNKNOWN; closure/ExecMainStatus never supplies this code.
        j['publisher_client_returncode'] = None
        j['publisher_client_identity'] = {'pid':child.pid,
            'birth_ticks':int((Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(')',1)[1].split()[19])}
        save()
        binding_keys = ('publisher_invocation_id', 'publisher_cgroup', 'publisher_process_identity')
        while child.poll() is None:
            remaining(client_deadline)
            current = service(PUB, deadline=client_deadline)
            binding_complete = all(j.get(key) for key in binding_keys)
            if not binding_complete:
                # These fixed states/flags describe observation only, never ownership.
                state_values = {
                    'LoadState': ('loaded', 'not-found', 'stub', 'error', 'bad-setting', 'merged', 'masked'),
                    'ActiveState': ('active', 'reloading', 'inactive', 'failed', 'activating', 'deactivating', 'maintenance', 'refreshing'),
                    'SubState': ('dead', 'condition', 'start-pre', 'start', 'start-post', 'running', 'exited',
                        'reload', 'reload-signal', 'reload-notify', 'stop', 'stop-watchdog', 'stop-sigterm',
                        'stop-sigkill', 'stop-post', 'final-watchdog', 'final-sigterm', 'final-sigkill',
                        'failed', 'auto-restart', 'auto-restart-queued', 'cleaning'),
                }
                observation = {key: current[key] if current[key] in values else 'unsupported'
                    for key, values in state_values.items()}
                observation.update(description_relation=('owned_nonce' if current['Description'] == j['publisher_owned_description']
                    else 'unit_name_placeholder' if current['Description'] == PUB else 'foreign'),
                    invocation_present=bool(current['InvocationID']), main_pid_present=current['MainPID'] != '0',
                    control_pid_present=current['ControlPID'] != '0', cgroup_present=bool(current['ControlGroup']),
                    prior_binding_components=sum(bool(j.get(key)) for key in binding_keys), client_observed_alive=True)
                j.setdefault('publisher_admission_first_observation', observation)
                if j.get('publisher_admission_last_observation') != observation:
                    j['publisher_admission_last_observation'] = observation
                    save()
                # A name-only placeholder may be pending startup or collected: its
                # phase is unknown. Waiting for this same client grants no authority.
                assert current['Description'] == j['publisher_owned_description'] or (
                    current['Description'] == PUB and not current['InvocationID'] and
                    current['MainPID'] == current['ControlPID'] == '0' and not current['ControlGroup']
                ), 'publisher_name_conflict_no_authority_to_stop'
            if current['LoadState'] != 'not-found':
                if current['InvocationID']:
                    remember_publisher_identity(current)
                elif binding_complete:
                    # Only a prior full binding can support terminal proof.
                    publisher_terminal_proven(deadline=client_deadline)
                # Before full binding an empty invocation is only an observation;
                # keep polling the same client under its unchanged original deadline.
            if all(j.get(key) for key in binding_keys):
                break
            time.sleep(min(.05, remaining(client_deadline)))
        child.wait(timeout=remaining(client_deadline))
        j['publisher_client_returncode'] = child.returncode
        save()
        assert j.get('publisher_process_identity') and j.get('publisher_cgroup') and j.get('publisher_invocation_id'), 'publisher_finished_without_exact_binding'
        return subprocess.CompletedProcess(args, child.returncode)
    except BaseException:
        try:
            # Capture an exit already observed before our own cleanup; a client
            # killed during cleanup cannot turn the publisher's UNKNOWN into -9.
            client_returncode = child.poll()
            if client_returncode is not None:
                j['publisher_client_returncode'] = client_returncode
                save()
        finally:
            reap_exact_owned_local_group(child, 'publisher_client_identity', 'publisher_client_cleanup_unconfirmed')
        raise
    finally:
        if child.returncode is not None and not local_group_absent(child):
            j['publisher_client_cleanup_unconfirmed'] = True
            raise StopUnconfirmed('reaped_publisher_client_leader_group_requires_Root_reconciliation')

class RootReleasedAfterFailure(RuntimeError):
    pass

def retain_custody_until_root_release(error):
    """Suspend THIS existing holder; no new operation, retry, watcher or clock.

    Root must first reconcile the nonce/invocation-bound publisher, then write the
    exact release record and SIGCONT this same PID/birth. An invalid resume keeps
    the same custody. The failed publication/start path can never continue.
    """
    self_pid = j['actor_identity']['pid']
    self_ticks = j['actor_identity']['birth_ticks']
    hold = {'schema':'frw.root.native206-custody-hold.v1','actor_pid':self_pid,'actor_birth_ticks':self_ticks,
        'boot_id':boot,'publisher_owned_description':j['publisher_owned_description'],
        'publisher_invocation_id':j.get('publisher_invocation_id'),'publisher_cgroup':j.get('publisher_cgroup'),
        'publisher_process_identity':j.get('publisher_process_identity'),
        'publisher_client_identity':j.get('publisher_client_identity'),
        'owned_local_process_identity':j.get('owned_local_process_identity'),
        'owned_local_cleanup_unconfirmed':j.get('owned_local_cleanup_unconfirmed',False),
        'publisher_client_cleanup_unconfirmed':j.get('publisher_client_cleanup_unconfirmed',False),
        'hold_nonce':j['custody_hold_nonce'],'original_operation_deadline':origin + 1800,
        'operation_failed_no_new_execution_or_clock':True}
    j.update(state='STOP_UNCONFIRMED_CUSTODY_HELD_ROOT_RECONCILIATION_REQUIRED',
        custody_hold=hold,error_class=type(error).__name__)
    release = B / 'ROOT-NATIVE206-CUSTODY-RELEASE.json'
    while True:
        # Evidence/storage/pipe failure cannot unwind a live publisher's holder.
        try: save()
        except BaseException as evidence_error: j['hold_evidence_error_class'] = type(evidence_error).__name__
        try: print(json.dumps({'state':j['state'],'hold':hold}),flush=True)
        except BaseException: pass
        os.kill(self_pid, signal.SIGSTOP)
        release_snapshot = dict(j)
        try:
            assert file_metadata(release)[2] == os.getuid()
            assert stat.S_IMODE(Path(release).lstat().st_mode) == 0o600
            receipt = json.loads(release.read_bytes())
            assert set(receipt) == {'schema','state','hold','publisher_identity_reconciliation'}
            assert receipt['schema'] == 'frw.root.native206-custody-release.v1'
            assert receipt['state'] == 'ROOT_RECONCILED_EXACT_PUBLISHER_AND_OWNED_LOCAL_SCOPES_CLOSED_RELEASE_FAILED_OPERATION_ONLY'
            assert receipt['hold'] == hold
            recovered = receipt['publisher_identity_reconciliation']
            if j.get('publisher_launch_consumed_no_retry') and not j.get('publisher_client_spawn_failed_before_child_created'):
                assert set(recovered) == {'owned_description','invocation_id','cgroup','process_identity','evidence'}
                assert recovered['owned_description'] == j['publisher_owned_description']
                assert len(recovered['invocation_id']) == 32
                assert recovered['cgroup'].startswith('/user.slice/') and recovered['cgroup'].endswith('/' + PUB) and '..' not in Path(recovered['cgroup']).parts
                assert set(recovered['process_identity']) == {'pid','birth_ticks'} and all(isinstance(x,int) and x>0 for x in recovered['process_identity'].values())
                for saved_key, recovered_key in [('publisher_invocation_id','invocation_id'),('publisher_cgroup','cgroup'),('publisher_process_identity','process_identity')]:
                    assert j.get(saved_key) in [None, recovered[recovered_key]], 'Root_reconciliation_cannot_override_recorded_identity'
                    j[saved_key] = recovered[recovered_key]
                file_metadata(recovered['evidence']['path'])
                assert sha(recovered['evidence']['path']) == recovered['evidence']['sha256']
                j['publisher_identity_reconciliation'] = recovered
            else:
                assert recovered is None
            # A bounded control-only release proof; it grants no expired operation.
            if j.get('publisher_launch_consumed_no_retry') and not j.get('publisher_client_spawn_failed_before_child_created'):
                unit = publisher_terminal_proven(deadline=time.monotonic() + 5)
            else:
                unit = closed(PUB, deadline=time.monotonic() + 5)
                assert unit['LoadState'] == 'not-found', 'unused_publisher_name_no_longer_absent'
            # Exact hold binds any local closure obligation; Root reconciles each
            # pinned PID/birth/process group and attests closure in this release.
            for key in ['owned_local_process_identity', 'publisher_client_identity']:
                identity = j.get(key)
                if identity:
                    proc = Path('/proc') / str(identity['pid'])
                    if proc.exists():
                        try: current_birth = int((proc / 'stat').read_text().rsplit(')',1)[1].split()[19])
                        except FileNotFoundError: current_birth = None
                        if current_birth == identity['birth_ticks']:
                            # This actor may reap its own now-dead direct child;
                            # this is cleanup only after Root's explicit proof.
                            try: os.waitpid(identity['pid'], os.WNOHANG)
                            except ChildProcessError: pass
                            if proc.exists():
                                try: current_birth = int((proc / 'stat').read_text().rsplit(')',1)[1].split()[19])
                                except FileNotFoundError: current_birth = None
                                assert current_birth != identity['birth_ticks'], 'owned_local_exact_process_still_live'
                    try: os.killpg(identity['pid'], 0)
                    except ProcessLookupError: pass
                    else: raise StopUnconfirmed('owned_local_process_group_still_live')
            j.update(custody_release_verified=True,custody_release_reference={'path':str(release),'sha256':sha(release)},
                publisher_terminal_unit=unit,publisher_closed_before_parent_custody_release=True)
            save()
            break
        except BaseException as release_error:
            j.clear(); j.update(release_snapshot)
            j['last_release_rejection_class'] = type(release_error).__name__
    raise RootReleasedAfterFailure('failed_operation_released_after_exact_root_reconciliation_no_replay')

try:
    j['state'] = 'OWNED_DASHBOARD_AND_GATEWAY_STOP_STARTED'
    save()
    for name, old_pid in [(DASH, int(dash_before['MainPID'])), (GW, pid)]:
        r = command(['systemctl', '--user', 'stop', name], 45)
        event('stop_returned', unit=name, returncode=r.returncode, service=service(name))
        assert r.returncode == 0 and not (Path('/proc') / str(old_pid)).exists()
        closed(name)
    custody_deadline = origin + 1800 - 90 - 180 - 180 - 75
    budget = Budget(1800, started=origin, deadline=custody_deadline)
    homefd = os.open(H, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fcntl.flock(homefd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode)
        home_identity = identity(os.fstat(homefd))
        with ordinary.stopped_consumers(H, q['native_unit'], budget) as native_prove, ordinary.retained_build_lock(N) as build_prove, ordinary.retained_pm_lock(H, N) as pm_prove, ordinary.project_current_admission_locks(H, budget) as admission_prove:
            def prove():
                assert identity(os.fstat(homefd)) == home_identity == identity(H.lstat())
                native_prove(); build_prove(); pm_prove(); admission_prove(); budget.check(reserve=15)
            try:
                prove()
                # One fresh actual22-unit observation after native/allprofile custody;
                # this observer is read-only and its own control children must be reaped.
                assert budget.check(reserve=15) >= 135, 'readonly_observer_family_budget_unavailable'
                assert sha(B / 'admission-retained/observe-current-retained-units.py') == 'c719860c492f9ae2eb88c6267905d06aac338fec97f05f12bbd2c787e043d6d5'
                with (B / 'ROOT-native206-retained-observer.stdout').open('xb') as out, (B / 'ROOT-native206-retained-observer.stderr').open('xb') as err:
                    observation = run_reaped([PY, '-I', '-B', str(B / 'admission-retained/observe-current-retained-units.py')],
                        stdout=out, stderr=err, timeout=remaining(custody_deadline - 15, 135))
                assert observation.returncode == 0
                rr = json.loads((B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json').read_bytes())
                assert rr['count'] == rr['quiescent'] == 22 and rr['all_control_children_reaped_closed'] and rr['actual_store_hashes_unchanged']
                assert 0 <= time.time() - datetime.datetime.fromisoformat(rr['at_moscow']).timestamp() <= 30
                assert data() == counts
                j['stopped_user_db_wal_shm_before'] = state_file_snapshot()
                save()
                for name in ['marker','source_receipt','stamp','configuration','profile','launcher','native_unit']:
                    assert sha(q[name]['path']) == q[name]['sha256'], name
                j['fresh_retained_unit_observations'] = {'path':str(B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json'),
                    'sha256':sha(B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json')}
                prove()
                # The original CP600/unit810/stop15 family must fit before launch;
                # never release custody while a shortened client wait leaves it live.
                assert budget.check(reserve=45) >= 840, 'publisher_family_and_close_budget_unavailable'
                unused = service(PUB)
                assert unused['LoadState'] == 'not-found' and unused['MainPID'] == unused['ControlPID'] == '0' and unused['ControlGroup'] == ''
                j['native_source_build_PM_home_allprofile_admission_custody_held'] = True
                j['state'] = 'GENUINE_NATIVE_CP_PUBLISHER_STARTED'
                save()
                args = ['systemd-run', '--user', '--wait', '--pipe', '--unit=' + PUB.removesuffix('.service'),
                    '--property=Description=' + j['publisher_owned_description'], '--property=RuntimeMaxSec=810', '--property=TimeoutStopSec=15', '--property=KillMode=control-group', '--property=Restart=no', '--property=UMask=0077', '--property=MemoryMax=2G',
                    '--property=LimitCPU=1560', '--property=LimitAS=3G', '--property=MemorySwapMax=0', '--property=CPUQuota=200%', '--property=TasksMax=96',
                    '--setenv=HERMES_HOME=' + str(H), '--setenv=HERMES_GATEWAY_LOCK_DIR=/home/jericho/.local/state/hermes/gateway-locks',
                    '--setenv=PYTHONDONTWRITEBYTECODE=1', '--setenv=GIT_OPTIONAL_LOCKS=0', PY, '-I', '-B', str(CP),
                    '--request', str(REQ), '--request-sha256', sha(REQ)]
                # The intent precedes the potentially ambiguous launch. Never relaunch it.
                j['publisher_launch_consumed_no_retry'] = True
                j['parent_custody_deadline'] = custody_deadline
                save()
                try:
                    with (B / 'ROOT-native206-publisher.stdout').open('xb') as out, (B / 'ROOT-native206-publisher.stderr').open('xb') as err:
                        publisher_timeout = remaining(custody_deadline - 45, 840)
                        assert publisher_timeout == 840, 'publisher_family_budget_unavailable'
                        r = run_owned_publisher(args, stdout=out, stderr=err, client_deadline=time.monotonic() + publisher_timeout)
                    event('publisher_client_returned', returncode=r.returncode)
                finally:
                    try: close_owned_publisher(custody_deadline)
                    except BaseException as close_error: retain_custody_until_root_release(close_error)
                    prove()
                operation_remaining(reserve=180 + 180 + 75)
            except BaseException as custody_error:
                # Closure/hold is INSIDE native/build/PM/home/allprofile contexts.
                if j.get('publisher_launch_consumed_no_retry') and not j.get('publisher_closed_before_parent_custody_release'):
                    try: close_owned_publisher(custody_deadline)
                    except BaseException as close_error: retain_custody_until_root_release(close_error)
                if isinstance(custody_error, StopUnconfirmed):
                    retain_custody_until_root_release(custody_error)
                raise
    finally:
        os.close(homefd)
    assert operation_remaining(reserve=180 + 180 + 75) >= 90, 'full_postcheck_budget_unavailable'
    postcheck_start = time.monotonic()
    postcheck_end = postcheck_start + 90
    j['postcheck_phase'] = {'started_mono':postcheck_start, 'deadline_mono':postcheck_end, 'seconds':90}
    save()
    unchanged_user(reserve=180 + 180 + 75)
    remaining(postcheck_end)
    receipt = json.loads((H / 'hermes-agent.source.json').read_bytes())
    marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())
    stamp = json.loads((N / 'install-stamp.json').read_bytes())
    if r.returncode == 0:
        assert sha(H / 'hermes-agent.source.json') == EXPECTED
        assert len(receipt['layers']) == 206 and receipt['layers'][:-1] == before_receipt['layers']
        assert len(receipt['files']) == 17891
        assert {n: v for n, v in receipt['files'].items() if n not in targets} == {n: v for n, v in before_receipt['files'].items() if n not in targets}
        assert marker['input_sha256'] == q['current_input']['sha256'] and marker['source_receipt_sha256'] == EXPECTED
        assert stamp['fridaySource']['layers'] == receipt['layers']
        for name, expected in targets.items():
            assert sha(N / name) == expected == receipt['files'][name]['sha256']
        for name, row in receipt['files'].items():
            remaining(postcheck_end)
            assert sha(N / name) == row['sha256'], name
        assert (tx / 'committed.json').exists() and not (tx / 'rolled-back.json').exists()
        assert sha(tx / 'request.json') == sha(REQ)
        for name in project_targets: assert sha(H / name) == cur['project_files'][name], name
        j['state'] = 'NATIVE206_COMMITTED_REQUIRES_FRESH_DEFAULT_CHECK'
        save()
        selected_project, selected_input = C, q['current_input']
    else:
        assert r.returncode == 2, 'publisher_unknown_or_stop_unconfirmed_do_not_start'
        diagnosis = json.loads((B / 'ROOT-native206-publisher.stderr').read_bytes().splitlines()[-1])
        assert diagnosis['state'] == 'REFUSED_NOT_RUNTIME_ACCEPTED'
        for name in ['marker', 'source_receipt', 'stamp', 'configuration', 'profile', 'launcher', 'native_unit']:
            assert sha(q[name]['path']) == q[name]['sha256'], name
        for name, row in before_receipt['files'].items():
            remaining(postcheck_end)
            assert sha(N / name) == row['sha256'], name
        for name in native_additions:
            assert not os.path.lexists(N / name), 'rollback_new_native_residual:' + name
        for name, state in before_project_targets.items():
            assert not os.path.lexists(H / name) if state is None else (sha(H / name) == state['sha256'] and file_metadata(H / name)[2:] == state['metadata'][2:]), name
        assert not (tx / 'intent.json').exists() or (tx / 'rolled-back.json').is_file(), 'publisher_unsettled_intent_do_not_start'
        j['state'] = 'PUBLICATION_REFUSED_BEFORE_EFFECT_OR_ROLLBACK_VERIFIED'
        j['publisher_code'] = r.returncode
        selected_project, selected_input = P, q['previous_input']
        save()
    assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'publication_changed_stopped_user_DB_WAL_SHM'
    with (B / 'ROOT-native206-default-check.stdout').open('xb') as out, (B / 'ROOT-native206-default-check.stderr').open('xb') as err:
        fresh = run_reaped([PY, '-I', '-B', str(selected_project / 'scripts/friday_install.py'), 'check', '--input', selected_input['path']],
            env=dict(os.environ), stdout=out, stderr=err, timeout=remaining(postcheck_end))
    remaining(postcheck_end)
    operation_remaining(reserve=180 + 180 + 75)
    event('fresh_default_check_returned', returncode=fresh.returncode)
    assert fresh.returncode == 0, 'settled_default_consumer_refused_do_not_start'
    assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'default_check_changed_stopped_user_DB_WAL_SHM'
    j['user_db_wal_shm_verified_before_starts'] = True
    j['fresh_default_spec_inspect'] = j['full_selected_native_files_readback'] = True
    j['selected_native_file_count'] = len(receipt['files'])
    j['selected_input'] = selected_input
    j['selected_project'] = str(selected_project)
    settled_paths = [H / 'FRIDAY-INSTALL.json', H / 'hermes-agent.source.json', N / 'install-stamp.json']
    settled_paths += [N / name for name in targets]
    settled_paths += [H / name for name in set(q['project_file_updates'] + q['layer_manifest_updates'] +
        [f'patches/hermes/{name}.patch' for name in q['layer_names']])]
    j['restore_verified_inputs'] = {'settled_files': {str(path): sha(path) if path.exists() else None for path in settled_paths},
        'settled_metadata': {str(path): file_metadata(path) for path in settled_paths if path.exists()},
        'verified_outputs': {str(B / name): sha(B / name) for name in ['ROOT-native206-default-check.stdout','ROOT-native206-default-check.stderr']},
        'publisher_code':r.returncode, 'postcheck_original_deadline':postcheck_end,
        'stopped_user_db_wal_shm':j['stopped_user_db_wal_shm_before']}
    save()
    remaining(postcheck_end)
    verified = time.monotonic()
    assert operation_remaining(reserve=180 + 75) >= 180, 'full_gateway_phase_budget_unavailable'
    end = verified + 180
    j['service_phases'][GW] = {'started_mono':verified,'deadline_mono':end,'seconds':180,'start_request_consumed_no_retry':True,'verified':False}
    save()
    start = command(['systemctl', '--user', 'start', '--no-block', GW], deadline=end)
    event('fresh_gateway_start_requested', returncode=start.returncode)
    assert start.returncode == 0
    while time.monotonic() < end:
        u = service(deadline=end)
        new_pid = int(u['MainPID'])
        try: g = json.loads((H / 'gateway_state.json').read_bytes())
        except FileNotFoundError: g = {}
        if u['ActiveState'] == 'active' and u['SubState'] == 'running' and new_pid > 0 and new_pid != pid and g.get('pid') == new_pid and g.get('gateway_state') == 'running' and g.get('platforms', {}).get('telegram', {}).get('state') == 'connected':
            new_ticks = int((Path('/proc') / str(new_pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])
            assert g['start_time'] == new_ticks and new_ticks / os.sysconf('SC_CLK_TCK') >= verified - .05
            assert u['ControlPID'] == '0' and u['InvocationID'] != svc['InvocationID'] and u['ControlGroup'] and ('0::'+u['ControlGroup']) in (Path('/proc') / str(new_pid) / 'cgroup').read_text().splitlines()
            assert g['served_profiles'] == ['default', 'dest_telegram', 'telegram-bot-8812646969']
            assert selected_process_environment(new_pid) == process_environment[GW]
            remaining(end)
            unchanged_user(reserve=180 + 75)
            remaining(end)
            j['service_phases'][GW]['verified'] = True
            j['service_phases'][GW]['verified_identity'] = {'pid':new_pid,'start_time':new_ticks,'invocation':u['InvocationID'],'cgroup':u['ControlGroup']}
            j['gateway_after'] = {'pid': new_pid, 'start_time': new_ticks, 'boot_id': boot, 'unit': u}
            save()
            break
        time.sleep(min(.25, remaining(end)))
    else:
        raise RuntimeError('fresh_gateway_start_not_confirmed')
    dash_verified = time.monotonic()
    assert operation_remaining(reserve=75) >= 180, 'full_dashboard_phase_budget_unavailable'
    end = dash_verified + 180
    j['service_phases'][DASH] = {'started_mono':dash_verified,'deadline_mono':end,'seconds':180,'start_request_consumed_no_retry':True,'verified':False}
    save()
    dash_start = command(['systemctl', '--user', 'start', '--no-block', DASH], deadline=end)
    event('fresh_dashboard_start_requested', returncode=dash_start.returncode)
    assert dash_start.returncode == 0
    while time.monotonic() < end:
        du = service(DASH, deadline=end)
        if du['ActiveState'] == 'failed':
            raise RuntimeError('fresh_dashboard_failed')
        listener = command(['ss', '-H', '-ltn', 'sport = :9119'], deadline=end)
        if du['ActiveState'] == 'active' and int(du['MainPID']) > 0 and listener.returncode == 0 and listener.stdout.strip():
            status = command([str(N / '.hermes/bin/hermes'), '-p', 'default', 'dashboard', '--status'], 30, deadline=end)
            if status.returncode == 0:
                ds = json.loads(status.stdout)
                assert ds['state'] == 'VERIFIED' and all(ds[n] is True for n in ['verified', 'nonce_verified', 'auth_required', 'servesSpa'])
                assert ds['source_receipt_sha256'] == sha(H / 'hermes-agent.source.json')
                dash_pid = int(du['MainPID'])
                assert ds['pid'] == dash_pid and dash_pid != int(dash_before['MainPID'])
                assert du['SubState'] == 'running' and du['ControlPID'] == '0'
                assert len(du['InvocationID']) == 32 and du['InvocationID'] != dash_before['InvocationID']
                dash_proc = Path('/proc') / str(dash_pid)
                dash_ticks = int((dash_proc / 'stat').read_text().rsplit(')', 1)[1].split()[19])
                assert ds['startTime'] == dash_ticks and dash_ticks / os.sysconf('SC_CLK_TCK') >= dash_verified - .05
                assert du['ControlGroup'] and '0::' + du['ControlGroup'] in (dash_proc / 'cgroup').read_text().splitlines()
                assert selected_process_environment(dash_pid) == process_environment[DASH]
                confirmed = service(DASH, deadline=end)
                assert all(confirmed[key] == du[key] for key in
                    ['MainPID', 'ControlPID', 'InvocationID', 'ControlGroup', 'ActiveState', 'SubState'])
                remaining(end)
                j['service_phases'][DASH]['verified'] = True
                j['service_phases'][DASH]['verified_identity'] = {'pid':dash_pid,'start_time':dash_ticks,'invocation':du['InvocationID'],'cgroup':du['ControlGroup']}
                j['dashboard_after'] = {'unit': confirmed, 'native_status': ds, 'start_time': dash_ticks}
                break
            # ABSENT3 is the initial no-record startup state, UNKNOWN is terminal.
            if status.returncode != 3:
                raise RuntimeError('fresh_dashboard_status_unknown')
        time.sleep(min(.5, remaining(end)))
    else:
        raise RuntimeError('fresh_dashboard_start_not_confirmed')
    unchanged_user()
    final_gateway = service(GW)
    assert final_gateway['ActiveState'] == 'active' and final_gateway['SubState'] == 'running'
    assert all(final_gateway[key] == j['gateway_after']['unit'][key] for key in ['MainPID','ControlPID','InvocationID','ControlGroup'])
    after_data = data()
    operation_remaining(reserve=75)
    j.update(state='NATIVE206_PROJECT493_FRESH_PERMANENT_SERVICES_RUNNING' if r.returncode == 0 else 'OLD205_PROJECT491_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING',
        user_data_after=after_data, completed_at_moscow=now(), elapsed_seconds=time.monotonic() - origin,
        permanent_service_unit_configuration_unchanged=True, new_artificial_lifetime_timer=False)
    save()
    operation_remaining(reserve=75)
    print(json.dumps({'state': j['state'], 'gateway_after': j['gateway_after'], 'dashboard_after': j['dashboard_after'],
        'elapsed_seconds': j['elapsed_seconds'], 'receipt_sha256': sha(H / 'hermes-agent.source.json')}))
    raise SystemExit(r.returncode)
except BaseException as error:
    if isinstance(error, SystemExit):
        raise
    j.update(state='ROOT_OPERATION_FAILED_CUSTODY_RELEASED_AFTER_ROOT_RECONCILIATION' if isinstance(error, RootReleasedAfterFailure) else ('STOP_UNCONFIRMED' if isinstance(error, StopUnconfirmed) else 'ROOT_RECONCILIATION_REQUIRED_DO_NOT_RETRY_OR_START_BLINDLY'), error_class=type(error).__name__,
        failure_at_moscow=now(), elapsed_seconds=time.monotonic() - origin)
    save()
    raise
