SOURCE_BOUND = True
def require_source_bound():
    if SOURCE_BOUND is not True:
        raise ValueError('native227_source_inputs_UNBOUND_before_current_or_effect')
'Reviewed candidate SOURCE only. Import is inert; explicit isolated CLI and externally pinned frame are required.\nRoot alone may issue actual source acceptance/current authority and invoke effects.\n'
'Root finite native227 one-time maintenance; source preparation is not execution.\nNew original2700; CP forward1200/unit1530/client1560 and cold180each retained.\nSource200 scripts/archived pairing/R92/g1/g2 consumed effects are never replayed.\nOn any error retain journal/clocks, reconcile exact state; never rerun this actor.\nPartial permanent start keeps original phase deadline; no repeated start request.\n'

from pathlib import Path
from contextlib import closing

import sys, os, json, hashlib, subprocess, sqlite3, socket, time, datetime, fcntl, stat, signal

B = Path(__file__).parent
def bind_source_data(external_manifest_sha256):
 require_source_bound()
 import types,hashlib,json
 from pathlib import Path
 raw=(B/'SOURCE-PINS.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=external_manifest_sha256:raise ValueError('external_source_manifest_changed_before_data_import')
 pins=json.loads(raw);path=B/'root227_data.py';code=path.read_bytes()
 if pins['source_refs'].get(str(path))!=hashlib.sha256(code).hexdigest():raise ValueError('pinned_finite_data_loader_required')
 m=types.ModuleType('Root227DataBoundary');m.__file__=str(path)
 exec(compile(code,str(path),'exec'),m.__dict__)
 return m.bind_namespace(globals(),external_manifest_sha256)



H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')

N = H / 'hermes-agent'

P=None

C=None

CP = B / 'publication/friday_v3_layer_publication.py'

RESTORE = B / 'resume_native227_services.py'

REQ = B / 'ROOT-FRESH-REQUEST.json'

PY = str(H / 'installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python')

GW = 'hermes-gateway-1b7e7667.service'

DASH = 'hermes-dashboard.service'

PUB = 'frw-astra-native227-install-after226-20261116.service'

# Sibling bytes are verified by the externally accepted immutable frame manifest.



def now():
    require_source_bound()
    return datetime.datetime.now().astimezone().isoformat()

def sha(p):
    require_source_bound()
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

import importlib.util

SOURCE_ACCEPTANCE = B / 'ROOT-227-SOURCE-ACCEPTANCE.json'

SPEC=None

def remaining(deadline, seconds=None):
    value = deadline - time.monotonic()
    if value <= 0:
        raise RuntimeError('original_maintenance_budget_exhausted')
    return value if seconds is None else min(seconds, value)

def operation_remaining(*, reserve=75, seconds=None):
    return remaining(origin + 2700 - reserve, seconds)

def command(args, seconds=5, *, deadline=None):
    require_source_bound()
    if deadline is None and 'origin' in globals():
        deadline = origin + 2700 - 75
    timeout = seconds if deadline is None else remaining(deadline, seconds)
    return subprocess.run(args, capture_output=True, timeout=timeout, check=False)

def service(name=GW, *, deadline=None):
    require_source_bound()
    r = command(['systemctl', '--user', 'show', name,
        '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,NRestarts,InvocationID,Result,ExecMainStatus,ControlGroup,UnitFileState,Description,RuntimeMaxUSec'], deadline=deadline)
    assert r.returncode == 0
    return dict(x.split('=', 1) for x in r.stdout.decode().splitlines())

def data():
    require_source_bound()
    out = {}
    data_end = time.monotonic() + 15
    for name, relative in [('default', 'state.db'), ('dest_telegram', 'profiles/dest_telegram/state.db'),
            ('telegram-bot-8812646969', 'profiles/telegram-bot-8812646969/state.db')]:
        with closing(sqlite3.connect((H / relative).as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
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
    require_source_bound()
    try: os.killpg(child.pid, 0)
    except ProcessLookupError: return True
    return False

def reap_exact_owned_local_group(child, identity_key, flag_key):
    require_source_bound()
    'Never signal a reused PID/PGID after its leader has been reaped.'
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
    require_source_bound()
    'Own only this local observer/check process group, including failure paths.'
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
    require_source_bound()
    path = Path(path); info = path.lstat()
    assert stat.S_ISREG(info.st_mode) and not path.is_symlink()
    assert info.st_uid == os.getuid() and info.st_nlink == 1
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode, info.st_nlink]

def directory_metadata(path):
    require_source_bound()
    path = Path(path); info = path.lstat()
    assert stat.S_ISDIR(info.st_mode) and not path.is_symlink() and info.st_uid == os.getuid()
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode]

def state_file_snapshot():
    require_source_bound()
    'Pin stopped user DB plus WAL/SHM; never checkpoint, chmod, repair or delete.'
    result = {}
    for relative in ['state.db', 'profiles/dest_telegram/state.db', 'profiles/telegram-bot-8812646969/state.db']:
        for suffix in ['', '-wal', '-shm']:
            path = H / (relative + suffix)
            result[str(path)] = None if not os.path.lexists(path) else {'sha256':sha(path), 'metadata':file_metadata(path)}
    return result

def related_recovery_snapshot():
    # Flat actual *.json expansion occurs here, after stopped writer custody;
    # every later comparison repeats directory membership, including new files.
    require_source_bound()
    result = {'DB9': state_file_snapshot(), 'related': recovery.snapshot(
        j['startup_data_cutoff_scope'], home=H, frame=B,
        check=lambda: operation_remaining())}
    if j.get('stopped_recovery_qualification'):
        recovery.frozen_qualification_checked(j['stopped_recovery_qualification'], result,
                                             j['startup_data_cutoff_scope'])
    return result

def all_service_writers_closed():
    require_source_bound()
    recovery.checked(j['startup_data_cutoff_scope'], home=H, frame=B)
    closed(GW); closed(DASH)
    if j.get('publisher_launch_consumed_no_retry'):
        publisher_terminal_proven(deadline=origin + 2700 - 75)
    else:
        assert closed(PUB)['LoadState'] == 'not-found', 'future_publisher_name_already_owned'
    return True

def selected_process_environment(pid):
    require_source_bound()
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
    require_source_bound()
    u = service(name, deadline=deadline)
    assert u['MainPID'] == u['ControlPID'] == '0' and u['ControlGroup'] == ''
    assert u['ActiveState'] in ['inactive', 'failed']
    return u

ADMISSION = B / 'ROOT-227-FRESH-ADMISSION.json'

J = B / 'ROOT-NATIVE227-LIVE-OPERATION.json'

def save():
    require_source_bound()
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
    require_source_bound()
    j['events'].append({'name': name, 'at_moscow': now(), **values})
    save()

def unchanged_user(*, reserve=75):
    require_source_bound()
    operation_remaining(reserve=reserve)
    for name in ['configuration', 'profile', 'launcher', 'native_unit']:
        assert sha(q[name]['path']) == q[name]['sha256'], name
    assert sha(dash_unit) == '0b91c52ec3db406f18daa545463a1692c62a5d77108a80d7645439801e155761'
    assert all(file_metadata(path) == expected for path, expected in before_metadata.items())
    assert all(directory_metadata(path) == expected for path, expected in before_directories.items())
    if j.get('stopped_user_db_wal_shm_before') and not j['service_phases']:
        assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'frozen_DB9_changed_no_SQLite_reopen'
    else:
        assert data() == counts
    marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())
    assert marker['plugin_files'] == before_marker['plugin_files']
    for name, expected in marker['plugin_files'].items():
        assert sha(H / name) == expected
    operation_remaining(reserve=reserve)

class StopUnconfirmed(RuntimeError):
    pass

def publisher_cgroup_empty():
    require_source_bound()
    group = j.get('publisher_cgroup')
    if not group: return True
    assert group.startswith('/user.slice/') and group.endswith('/' + PUB) and '..' not in Path(group).parts
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not base.exists(): return True
    events = dict(row.split() for row in (base / 'cgroup.events').read_text().splitlines())
    return events.get('populated') == '0' and not (base / 'cgroup.procs').read_text().strip()

def remember_publisher_identity(u):
    require_source_bound()
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
    require_source_bound()
    identity = j.get('publisher_process_identity')
    assert identity and j.get('publisher_invocation_id') and j.get('publisher_cgroup'), 'owned_publisher_exact_binding_missing'
    proc = Path('/proc') / str(identity['pid'])
    if not proc.exists(): return True
    try: current_birth = int((proc / 'stat').read_text().rsplit(')', 1)[1].split()[19])
    except FileNotFoundError: return True
    return current_birth != identity['birth_ticks']

def publisher_terminal_proven(*, deadline):
    require_source_bound()
    'not-found alone is insufficient: this attempt must first bind its invocation.'
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
    require_source_bound()
    'Close only the nonce/invocation-pinned publisher admitted by this attempt.'
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
    require_source_bound()
    'Observe the exact transient invocation while the one consumed launch runs.'
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
    require_source_bound()
    'Suspend THIS existing holder; no new operation, retry, watcher or clock.\n\n    Root must first reconcile the nonce/invocation-bound publisher, then write the\n    exact release record and SIGCONT this same PID/birth. An invalid resume keeps\n    the same custody. The failed publication/start path can never continue.\n    '
    self_pid = j['actor_identity']['pid']
    self_ticks = j['actor_identity']['birth_ticks']
    hold = {'schema':'frw.root.native227-custody-hold.v1','actor_pid':self_pid,'actor_birth_ticks':self_ticks,
        'boot_id':boot,'publisher_owned_description':j['publisher_owned_description'],
        'publisher_invocation_id':j.get('publisher_invocation_id'),'publisher_cgroup':j.get('publisher_cgroup'),
        'publisher_process_identity':j.get('publisher_process_identity'),
        'publisher_client_identity':j.get('publisher_client_identity'),
        'owned_local_process_identity':j.get('owned_local_process_identity'),
        'owned_local_cleanup_unconfirmed':j.get('owned_local_cleanup_unconfirmed',False),
        'publisher_client_cleanup_unconfirmed':j.get('publisher_client_cleanup_unconfirmed',False),
        'hold_nonce':j['custody_hold_nonce'],'original_operation_deadline':origin + 2700,
        'operation_failed_no_new_execution_or_clock':True}
    j.update(state='STOP_UNCONFIRMED_CUSTODY_HELD_ROOT_RECONCILIATION_REQUIRED',
        custody_hold=hold,error_class=type(error).__name__)
    release = B / 'ROOT-NATIVE226-CUSTODY-RELEASE.json'
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
            assert receipt['schema'] == 'frw.root.native227-custody-release.v1'
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


def module_source(path):
    require_source_bound()
    import types
    m = types.ModuleType('Root226AcceptedPhaseSource'); m.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), m.__dict__)
    return m

def check_new_operation_admission(*,manifest,admission):
    require_source_bound()
    'Root-only missing FIRST phase, never a renamed consumed actor admission.'
    path=B/'core227-first-actual-root.py'
    assert sha(path)==manifest['source_refs'][str(path)], 'exact_missing_FIRST_gate_source_required'
    core=module_source(path)
    classification=core.checked_new_operation_plan(manifest)
    history={'path':str(B/'ROOT-227-CONSUMED-HISTORY-TEMPLATE.json'),'sha256':sha(B/'ROOT-227-CONSUMED-HISTORY-TEMPLATE.json')}
    authority=json.loads((B/'ROOT-227-RUNTIME-AUTHORITY.json').read_bytes())
    assert admission['consumed_history']==authority['consumed_history']==history, 'admission_consumed_history_join_required'
    assert admission['new_operation_plan']==authority['new_operation_plan']==classification, 'admission_explicit_missing_FIRST_phase_join_required'
    return classification


def manifest_sha256(manifest):
    require_source_bound()
    value=sha(B/'SOURCE-PINS.json')
    frozen=json.loads((B/'SOURCE-PINS.json').read_bytes())
    assert all(manifest.get(k)==frozen[k]for k in frozen if k not in ('execution_commit','execution_provenance_mode','execution_public_main_sha')), 'immutable_source_manifest_fields_required'
    return value

def checked_native_settlement(before_receipt, receipt, targets, native_additions, *, publisher_code):
    """Pure receipt boundary; a planned result never proves actual file readback."""
    names = {'tools/scoped_communication.py', 'tools/session_search_tool.py'}
    added = set()
    assert set(targets) == names and set(native_additions) == added, 'exact227_two_modifications_no_additions_required'
    assert len(before_receipt['layers']) == 226 and len(before_receipt['files']) == 17895, 'genuine226_receipt_shape_required'
    assert not (added & set(before_receipt['files'])), 'new227_native_preimage_must_be_absent'
    retained = {n: row for n, row in before_receipt['files'].items() if n not in names}
    assert len(retained) == 17893, 'exact17893_retained_native_rows_required'
    if publisher_code == 0:
        assert len(receipt['layers']) == 227 and receipt['layers'][:-1] == before_receipt['layers'], 'exact226_prefix_plus_one227_layer_required'
        assert receipt['layers'][-1]['manifest'] == 'patches/hermes/core-communication-memory-after-source226-manifest.json', 'explicit227_layer_required'
        assert len(receipt['files']) == 17895, 'exact227_native_count_required'
        assert {n: row for n, row in receipt['files'].items() if n not in names} == retained, 'retained226_native_rows_changed'
        assert all(receipt['files'][n]['sha256'] == expected for n, expected in targets.items()), 'selected227_native_postimages_required'
    else:
        assert publisher_code == 2 and receipt == before_receipt, 'old226_only_after_exact_refusal_or_verified_rollback'
    return {'publisher_code': publisher_code, 'selected_native_file_count': len(receipt['files']),
            'retained_native_rows': len(retained), 'owned_addition_count': 0, 'actual_runtime_readback': False}

def read_static_source_inputs(*, manifest, bound, request_path=None):
    require_source_bound()
    "Actual actor SOURCE route reused before once by Root readonly preflight.\n\n    All source/config selections come from this inert actor's declarations. Only\n    the readonly-built request location may differ before its final publication.\n    No product module, authority collector, command or effect is called here.\n    "
    bind_source_data(manifest_sha256(manifest))
    static=module_source(B/'actor_static_inputs227.py')
    inputs=static.read_source_inputs(manifest=manifest,bound=bound,
        request_path=REQ if request_path is None else request_path,home=H,
        previous_project=P,candidate_project=C,native_spec=SPEC)
    static.validate_selection_aliases(source_spec_ref=inputs['source_spec_ref'],
        q=inputs['q'],bound=bound,
        admission=json.loads((B/'ROOT-227-FRESH-ADMISSION-TEMPLATE.json').read_bytes()),
        qualification=json.loads((B/'ROOT-227-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json').read_bytes()))
    return inputs

class SourceCaptureJournalPersistenceError(RuntimeError):
    'A failed shared-journal save is an install reconciliation issue.'


class SourceCaptureSourceSafetyError(RuntimeError):
    'A bound optional witness source/custody mismatch requires reconciliation.'


def actual_query_adapter():
    raise FileNotFoundError('separate_F04_semantic_witness_authority_not_part_of_ordinary_install')


def normal_gateway_source_capture(stage, *, reserve, state=None):
    require_source_bound()
    'Optional case evidence cannot consume the remaining service reserves.'
    allowed=('prepare_normal_gateway_source_custody','before_normal_gateway_start',
             'after_verified_normal_gateway_start')
    assert stage in allowed
    capture=j.setdefault('poststart_source_custody_capture',{
        'state':'PENDING','required_for_ordinary_install':False,
        'qualification':'NOT_RUN_SEPARATE_LIFECYCLE','completed_stages':[]})
    if capture['state']=='UNAVAILABLE_CAPTURE_ONLY_NO_QUALIFICATION':
        return False
    if stage in capture['completed_stages']:
        return True
    full_end=j['absolute_deadline_monotonic']-75
    cap_end=min(time.monotonic()+(10 if stage==allowed[1] else 30),
                j['absolute_deadline_monotonic']-reserve-5)
    if stage==allowed[1]:
        cap_end=min(cap_end,j['service_phases'][GW]['deadline_mono']-1)
    adapter=None
    def persist_capture():
        try: save()
        except BaseException as error:
            raise SourceCaptureJournalPersistenceError('source_capture_shared_journal_save_failed') from error
    try:
        if cap_end<=time.monotonic():
            raise TimeoutError('optional_source_capture_service_reserve_unavailable')
        adapter=actual_query_adapter()
        getattr(adapter,stage)(j,dict(state or {},_root_query_deadline_monotonic=full_end,
            _root_capture_deadline_monotonic=cap_end),persist_capture)
    except (SourceCaptureJournalPersistenceError,SourceCaptureSourceSafetyError):
        raise
    except Exception as error:
        if isinstance(error,getattr(adapter,'NormalGatewayCaptureSafetyError',())):
            raise
        capture.update(state='UNAVAILABLE_CAPTURE_ONLY_NO_QUALIFICATION',failed_stage=stage,
            error_class=type(error).__name__,capture_deadline_monotonic=cap_end,
            original_operation_deadline_monotonic=j['absolute_deadline_monotonic'],
            preserved_service_reserve_seconds=reserve)
        save()
        return False
    capture['completed_stages'].append(stage)
    capture.update(state=('WITNESS_AVAILABLE_NOT_QUALIFICATION' if stage==allowed[2] else 'IN_PROGRESS'),
        last_completed_stage=stage,capture_deadline_monotonic=cap_end,
        original_operation_deadline_monotonic=j['absolute_deadline_monotonic'],
        preserved_service_reserve_seconds=reserve)
    save()
    return True


def installed_service_readback(journal, *, publisher_code):
    # Exact accepted ordinary install guards only. No specialist case adapter.
    require_source_bound()
    pins=json.loads((B/'SOURCE-PINS.json').read_bytes())
    for name in ('core227-first-actual-root.py','boundary_contract.py',
                 'native_scope_post227.py' if publisher_code==0 else 'native_scope_preflight226.py'):
        path=B/name
        assert sha(path)==pins['source_refs'][str(path)], 'exact accepted install guard source required'
    return module_source(B/'core227-first-actual-root.py').installed_service_readback(journal,publisher_code=publisher_code,deadline=journal['absolute_deadline_monotonic']-75)

def main():
    require_source_bound()
    global recovery, cutoff, Budget, EXPECTED, actor_birth_ticks, actor_pid, admission, admission_prove, after_data, args, bank, bank_manifest, bank_rows, before, before_directories, before_marker, before_metadata, before_project_targets, before_receipt, binding, binding_spec, boot, bound, budget, build_prove, chunk, confirm, confirmed, counts, critical_bank_paths, cur, current_pid, current_ticks, current_unit, custody_deadline, dash_before, dash_native_before, dash_pid, dash_proc, dash_proc_before, dash_start, dash_status, dash_ticks, dash_ticks_before, dash_unit, dash_verified, diagnosis, directory_fd, ds, du, end, err, expected, f, fd, final_gateway, fresh, g, home_identity, homefd, identity, j, key, label, layer, listener, marker, n, name, native_additions, native_prove, new_pid, new_ticks, observation, old_pid, ordinary, origin, out, path, pid, pm_prove, postcheck_end, postcheck_start, previous, process_environment, project_targets, publisher_timeout, q, qualification, qualification_ref, r, raw, receipt, recorded, reference, root_identity, row, rpc, rpc_end, rr, selected_input, selected_project, settled_paths, snap, sock, spec, stamp, start, state, status, stream, svc, targets, ticks, tx, u, unused, v, verified, x
    import sys
    if len(sys.argv)<4:raise ValueError('external_source_pins_and_real_data_required')
    bind_source_data(sys.argv[3])
    if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode):
        raise RuntimeError('isolated_nonoptimized_no_bytecode_python_required')

    assert len(sys.argv)==4 and sys.argv[1:3] == ['--execute-once-root-accepted-227','--source-pins-sha256'], 'explicit_Root_execute_once_mode_required'
    manifest=json.loads((B/'SOURCE-PINS.json').read_bytes()); assert sha(B/'SOURCE-PINS.json')==sys.argv[3], 'external_source_manifest_changed'
    verifier=B/'frame_source.py'; assert sha(verifier)==manifest['source_refs'][str(verifier)], 'pinned_frame_verifier_required'
    module_source(verifier).verify_manifest(sys.argv[3],frame=B)

    os.umask(0o077)
    import importlib.util
    cutoff_path = B / 'cutoff_contract.py'
    assert sha(cutoff_path) == manifest['source_refs'][str(cutoff_path)]
    cutoff_spec = importlib.util.spec_from_file_location('Root226CandidateCutoff',cutoff_path)
    cutoff = importlib.util.module_from_spec(cutoff_spec); cutoff_spec.loader.exec_module(cutoff)

    recovery_path = B / 'recovery_scope.py'
    assert sha(recovery_path) == manifest['source_refs'][str(recovery_path)]
    recovery_spec = importlib.util.spec_from_file_location('Root226StoppedRecoveryScope', recovery_path)
    recovery = importlib.util.module_from_spec(recovery_spec); recovery_spec.loader.exec_module(recovery)


    sys.dont_write_bytecode = True

    assert sha(B / 'root227_metadata.py') == manifest['source_refs'][str(B/'root227_metadata.py')]

    binding_spec = importlib.util.spec_from_file_location('root218_metadata', B / 'root227_metadata.py')

    binding = importlib.util.module_from_spec(binding_spec)

    binding_spec.loader.exec_module(binding)
    binding.require_bound_data(sys.argv[3])

    assert sha(CP) == manifest['source_refs'][str(CP)]

    assert sha(RESTORE) == manifest['source_refs'][str(RESTORE)]

    bound = binding.load_actor_binding(B)

    EXPECTED = bound['expected_receipt_sha256']

    actor_inputs = read_static_source_inputs(manifest=manifest,bound=bound)
    q=actor_inputs['q'];cur=actor_inputs['cur'];previous=actor_inputs['previous'];tx=actor_inputs['tx']
    before_receipt=actor_inputs['before_receipt'];before_marker=actor_inputs['before_marker']
    layer=actor_inputs['layer'];targets=actor_inputs['targets'];spec=actor_inputs['spec']
    native_additions=actor_inputs['native_additions'];project_targets=actor_inputs['project_targets']

    os.environ.update(HERMES_HOME=str(H), HERMES_GATEWAY_LOCK_DIR='/home/jericho/.local/state/hermes/gateway-locks',
        GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')

    assert sha(P / 'scripts/friday_install.py') == '47273b21753788012bd23f43fcc34e7c97adcd4841848eea2a3023dc60536f27'

    assert sha(P / 'scripts/friday_ordinary_install.py') == binding.supplied_predecessor()['values']['input']['project_files']['scripts/friday_ordinary_install.py']

    sys.path.insert(0, str(P))

    from scripts import friday_install as f

    f.native_packages(N)

    from scripts import friday_ordinary_install as ordinary

    from scripts.install_containment import Budget

    assert Path(f.__file__).resolve() == P / 'scripts/friday_install.py'

    assert sha(f.__file__) == '47273b21753788012bd23f43fcc34e7c97adcd4841848eea2a3023dc60536f27'

    assert sha(ordinary.__file__) == binding.supplied_predecessor()['values']['input']['project_files']['scripts/friday_ordinary_install.py']

    assert file_metadata(ADMISSION)[2] == os.getuid() and stat.S_IMODE(ADMISSION.lstat().st_mode) == 0o600

    admission = json.loads(ADMISSION.read_bytes())
    check_new_operation_admission(manifest=manifest,admission=admission)

    assert admission['schema'] == 'frw.root.native227-fresh-window-admission.v1'

    assert admission['state'] == 'ROOT_ACCEPTED_EXACT227_SOURCE_AND_MINIMUM_INSTALLED_BANK_PROFILE_FINITE_WINDOW'

    assert admission['home'] == str(H) and admission['request'] == {'path':str(REQ), 'sha256':sha(REQ)}

    assert admission['actor'] == {'path':str(Path(__file__)), 'sha256':sha(__file__)}

    assert admission['recovery'] == {'path':str(RESTORE), 'sha256':sha(RESTORE)}

    assert admission['native_spec'] == actor_inputs['source_spec_ref']

    assert admission['source_acceptance'] == {'path':str(SOURCE_ACCEPTANCE), 'sha256':sha(SOURCE_ACCEPTANCE)}

    assert admission['expected_receipt_sha256'] == EXPECTED and admission['operation_seconds'] == 2700

    assert admission['bound_inputs'] == {'path':str(B / 'ROOT-227-BOUND-INPUTS.json'), 'sha256':sha(B / 'ROOT-227-BOUND-INPUTS.json')}

    assert admission['budgets'] == {'forward':1200,'external_rollback':300,'terminal_cleanup':30,'publisher_unit':1530,'publisher_client':1560,'operation':2700}

    assert admission['template_only_no_execution_grant'] is False

    assert admission['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()

    assert 0 <= time.time() - datetime.datetime.fromisoformat(admission['accepted_at_moscow']).timestamp() <= 300

    qualification_ref = admission['minimum_installed_bank_profile_qualification']

    assert file_metadata(qualification_ref['path'])[2] == os.getuid() and sha(qualification_ref['path']) == qualification_ref['sha256']

    qualification = json.loads(Path(qualification_ref['path']).read_bytes())

    assert qualification['state'] == 'ROOT_ACCEPTED_MINIMUM_INSTALLED_BANK_PROFILE_FOR_NATIVE227_SELECTION_NO_FORMAL_CREDIT'

    assert qualification['bank_path'] == '/home/jericho/.jericho/toolchains/libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111'

    assert qualification['bank_manifest_sha256'] == 'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'

    assert qualification['native_spec'] == actor_inputs['source_spec_ref']

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
    assert g['served_profiles'] == ['default', 'dest_telegram', 'telegram-bot-8812646969']

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

    # Genuine installed226 source preflight BEFORE any stop/install.
    preflight = module_source(B / 'native_scope_preflight226.py')
    snap = preflight.fresh_native(g)

    counts = data()

    actor_pid = os.getpid()

    actor_birth_ticks = int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19])

    assert 0 <= time.time() - datetime.datetime.fromisoformat(admission['accepted_at_moscow']).timestamp() <= 300

    origin = time.monotonic()

    j = {'schema': 'frw.root.native227-maintenance.v1', 'state': 'ORIGINAL_MAINTENANCE_STARTED',
        'actor_identity':{'pid':actor_pid,'birth_ticks':actor_birth_ticks,'boot_id':boot}, 'custody_hold_nonce':os.urandom(16).hex(),
        'started_at_moscow': now(), 'origin_monotonic': origin, 'absolute_deadline_monotonic': origin + 2700,
        'budgets': {'maintenance': 2700, 'stop_each': 45, 'native_publisher_original': 1200, 'external_rollback_reserve': 300, 'publisher_terminal_cleanup': 30, 'publisher_unit_runtime': 1530,
            'postcheck': 90, 'cold_gateway': 180, 'cold_dashboard': 180, 'cleanup_reserve': 75, 'publisher_client_wait': 1560},
        'gateway_before': {'pid': pid, 'start_time': ticks, 'boot_id': boot, 'unit': svc}, 'dashboard_before': dash_before,
        'dashboard_native_before': dash_native_before, 'dashboard_birth_ticks_before': dash_ticks_before,
        'unchanged_metadata': before_metadata, 'unchanged_directories': before_directories, 'process_environment': process_environment,
        'before_native_file_count':len(before_receipt['files']),'native_addition_count':len(native_additions),'user_data_before': counts, 'plugin_files_before':before_marker['plugin_files'], 'before_project_targets':before_project_targets, 'request': {'path': str(REQ), 'sha256': sha(REQ)}, 'publisher_sha256': sha(CP),
        'current_input': q['current_input'], 'fresh_root_admission':{'path':str(ADMISSION),'sha256':sha(ADMISSION)},
        'minimum_installed_bank_profile_qualification':qualification_ref, 'before_readonly_snapshot': snap, 'native_before_after': [226, 227],
        'restore_service_source': {'path':str(RESTORE), 'sha256':sha(RESTORE)},
        'source_pin_manifest':{'path':str(B/'SOURCE-PINS.json'),'sha256':sha(B/'SOURCE-PINS.json')},
        'runtime_authority':{'path':str(B/'ROOT-227-RUNTIME-AUTHORITY.json'),'sha256':sha(B/'ROOT-227-RUNTIME-AUTHORITY.json')},
        'publisher_owned_description':'Root-native227-' + sha(REQ)[:16] + '-' + os.urandom(16).hex(),
        'candidate_project':str(C), 'startup_data_cutoff_scope':json.loads((B/'ROOT-227-CURRENT-SERVICE-ANCHOR.json').read_bytes())['startup_data_cutoff_scope'], 'candidate_startup_cutoff':{'state':'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'}, 'candidate_start_attempt_intent':None, 'managed_phase_may_have_executed':False, 'cutoff_contract_source':{'path':str(B/'cutoff_contract.py'),'sha256':sha(B/'cutoff_contract.py')}, 'expected_receipt_sha256': EXPECTED, 'new_model_Telegram_worker_operations': 0, 'events': [], 'service_phases': {}, 'source_frame_sha256': sha(__file__)}

    fd = os.open(J, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    with os.fdopen(fd, 'w') as stream:
        json.dump(j, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())

    directory_fd = os.open(J.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    try: os.fsync(directory_fd)
    finally: os.close(directory_fd)

    try:
        j['state'] = 'OWNED_DASHBOARD_AND_GATEWAY_STOP_STARTED'
        save()
        for name, old_pid in [(DASH, int(dash_before['MainPID'])), (GW, pid)]:
            r = command(['systemctl', '--user', 'stop', name], 45)
            event('stop_returned', unit=name, returncode=r.returncode, service=service(name))
            assert r.returncode == 0 and not (Path('/proc') / str(old_pid)).exists()
            closed(name)
        custody_deadline = origin + 2700 - 90 - 180 - 180 - 75
        budget = Budget(2700, started=origin, deadline=custody_deadline)
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
                    assert sha(B / 'admission-retained/observe-current-retained-units.py') == manifest['source_refs'][str(B / 'admission-retained/observe-current-retained-units.py')], 'source_pinned_retained_observer_required'
                    with (B / 'ROOT-native226-retained-observer.stdout').open('xb') as out, (B / 'ROOT-native226-retained-observer.stderr').open('xb') as err:
                        observation = run_reaped([PY, '-I', '-B', str(B / 'admission-retained/observe-current-retained-units.py'), '--observe-readonly-retained-once'],
                            stdout=out, stderr=err, timeout=remaining(custody_deadline - 15, 135))
                    assert observation.returncode == 0
                    rr = json.loads((B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json').read_bytes())
                    assert rr['count'] == rr['quiescent'] == 22 and rr['all_control_children_reaped_closed'] and rr['actual_store_hashes_unchanged']
                    assert 0 <= time.time() - datetime.datetime.fromisoformat(rr['at_moscow']).timestamp() <= 30
                    assert data() == counts
                    prove()
                    # Current effective routing/ledger/custody is observed ONLY now.
                    # All handles close before frozen DB9 bytes are taken. No further
                    # SQLite reads are used for pre-start unchanged-input checks.
                    stopped_qualification = recovery.observe_before_freeze(
                        j['startup_data_cutoff_scope'], home=H, frame=B,
                        check=lambda: operation_remaining(),
                        writers_sealed=all_service_writers_closed(), db_snapshot=state_file_snapshot)
                    j['stopped_user_db_wal_shm_before'] = state_file_snapshot()
                    j['stopped_all_recovery_data_before'] = related_recovery_snapshot()
                    j['stopped_recovery_qualification'] = stopped_qualification
                    save()  # Preserve a refusal's hashes/classification, never payloads.
                    recovery.frozen_qualification_checked(stopped_qualification,
                        j['stopped_all_recovery_data_before'], j['startup_data_cutoff_scope'])
                    for name in ['marker','source_receipt','stamp','configuration','profile','launcher','native_unit']:
                        assert sha(q[name]['path']) == q[name]['sha256'], name
                    j['fresh_retained_unit_observations'] = {'path':str(B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json'),
                        'sha256':sha(B / 'admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json')}
                    prove()
                    # The new CP1200/unit1530/stop15 family must fit before launch;
                    # never release custody while a shortened client wait leaves it live.
                    assert budget.check(reserve=45) >= 1560, 'publisher_family_and_close_budget_unavailable'
                    unused = service(PUB)
                    assert unused['LoadState'] == 'not-found' and unused['MainPID'] == unused['ControlPID'] == '0' and unused['ControlGroup'] == ''
                    j['native_source_build_PM_home_allprofile_admission_custody_held'] = True
                    j['state'] = 'GENUINE_NATIVE_CP_PUBLISHER_STARTED'
                    save()
                    args = ['systemd-run', '--user', '--wait', '--pipe', '--unit=' + PUB.removesuffix('.service'),
                        '--property=Description=' + j['publisher_owned_description'], '--property=RuntimeMaxSec=1530', '--property=TimeoutStopSec=15', '--property=KillMode=control-group', '--property=Restart=no', '--property=UMask=0077', '--property=MemoryMax=2G',
                        '--property=LimitCPU=3120', '--property=LimitAS=3G', '--property=MemorySwapMax=0', '--property=CPUQuota=200%', '--property=TasksMax=96',
                        '--setenv=HERMES_HOME=' + str(H), '--setenv=HERMES_GATEWAY_LOCK_DIR=/home/jericho/.local/state/hermes/gateway-locks',
                        '--setenv=PYTHONDONTWRITEBYTECODE=1', '--setenv=GIT_OPTIONAL_LOCKS=0', PY, '-I', '-B', str(CP),
                        '--request', str(REQ), '--request-sha256', sha(REQ)]
                    # The intent precedes the potentially ambiguous launch. Never relaunch it.
                    j['publisher_launch_consumed_no_retry'] = True
                    j['parent_custody_deadline'] = custody_deadline
                    save()
                    try:
                        with (B / 'ROOT-native226-publisher.stdout').open('xb') as out, (B / 'ROOT-native226-publisher.stderr').open('xb') as err:
                            publisher_timeout = remaining(custody_deadline - 45, 1560)
                            assert publisher_timeout == 1560, 'publisher_family_budget_unavailable'
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
        checked_native_settlement(before_receipt, receipt, targets, native_additions, publisher_code=r.returncode)
        if r.returncode == 0:
            assert sha(H / 'hermes-agent.source.json') == EXPECTED
            assert len(receipt['layers']) == 227 and receipt['layers'][:-1] == before_receipt['layers']
            assert len(receipt['files']) == 17895 + len(native_additions)
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
            j['state'] = 'NATIVE227_COMMITTED_REQUIRES_FRESH_DEFAULT_CHECK'
            save()
            selected_project, selected_input = C, q['current_input']
        else:
            assert r.returncode == 2, 'publisher_unknown_or_stop_unconfirmed_do_not_start'
            diagnosis = json.loads((B / 'ROOT-native226-publisher.stderr').read_bytes().splitlines()[-1])
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
        j['publisher_code'] = r.returncode
        save()
        assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'publication_changed_stopped_user_DB_WAL_SHM'
        with (B / 'ROOT-native226-default-check.stdout').open('xb') as out, (B / 'ROOT-native226-default-check.stderr').open('xb') as err:
            fresh = run_reaped([PY, '-I', '-B', str(selected_project / 'scripts/friday_install.py'), 'check', '--input', selected_input['path']],
                env=dict(os.environ), stdout=out, stderr=err, timeout=remaining(postcheck_end))
        remaining(postcheck_end)
        operation_remaining(reserve=180 + 180 + 75)
        event('fresh_default_check_returned', returncode=fresh.returncode)
        assert fresh.returncode == 0, 'settled_default_consumer_refused_do_not_start'
        assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'default_check_changed_stopped_user_DB_WAL_SHM'
        j['default_transaction_postconsumer_returncode'] = fresh.returncode
        # Only the real post-transaction consumer can create this journal fact.
        # Source planning and the preparer never emit an equivalent pre-PASS.
        j['settled_transaction_readback'] = {'request': j['request'], 'transaction_path': str(tx),
            'publisher_code': r.returncode, 'actual_default_consumer_returncode': fresh.returncode}
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
            'verified_outputs': {str(B / name): sha(B / name) for name in ['ROOT-native226-default-check.stdout','ROOT-native226-default-check.stderr']},
            'publisher_code':r.returncode, 'postcheck_original_deadline':postcheck_end,
            'stopped_user_db_wal_shm':j['stopped_user_db_wal_shm_before'], 'stopped_all_recovery_data':j['stopped_all_recovery_data_before']}
        save()
        remaining(postcheck_end)
        if r.returncode == 0:
            cutoff.cross_before_candidate_start(j,request=j['request'],observed=related_recovery_snapshot(),settled=j['stopped_all_recovery_data_before'],all_writers_sealed=all_service_writers_closed(),persist=save)
        else:
            cutoff.before_old_start(j,observed=related_recovery_snapshot(),settled=j['stopped_all_recovery_data_before'],all_writers_sealed=all_service_writers_closed())
            j['old226_restart_data_boundary_verified_before_any_candidate'] = True; save()
        if r.returncode == 0:
            normal_gateway_source_capture('prepare_normal_gateway_source_custody',reserve=180+180+75)
        verified = time.monotonic()
        assert operation_remaining(reserve=180 + 75) >= 180, 'full_gateway_phase_budget_unavailable'
        end = verified + 180
        j['service_phases'][GW] = {'started_mono':verified,'deadline_mono':end,'seconds':180,'start_request_consumed_no_retry':True,'verified':False}
        save()
        if r.returncode == 0:
            normal_gateway_source_capture('before_normal_gateway_start',reserve=180+75)
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
                if r.returncode == 0:
                    normal_gateway_source_capture('after_verified_normal_gateway_start',reserve=180+75,state=g)
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
        # Healthy ordinary services close installation independently of R02.
        j['basic_install_service_readback'] = installed_service_readback(j,publisher_code=r.returncode)
        save()
        unchanged_user()
        final_gateway = service(GW)
        assert final_gateway['ActiveState'] == 'active' and final_gateway['SubState'] == 'running'
        assert all(final_gateway[key] == j['gateway_after']['unit'][key] for key in ['MainPID','ControlPID','InvocationID','ControlGroup'])
        after_data = data()
        operation_remaining(reserve=75)
        j.update(state='INSTALLED227_AND_HEALTHY_CORE_COMMUNICATION_MEMORY_SEMANTICS_NOT_RUN_SEPARATE' if r.returncode == 0 else 'OLD226_PROJECT533_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING',
            user_data_after=after_data, completed_at_moscow=now(), elapsed_seconds=time.monotonic() - origin,
            recovery_ready=False, startup_full_sweep_qualification='NOT_RUN_SEPARATE_POST_INSTALL_R02_ASSESSMENT',
            R02_assessment='NOT_RUN_SEPARATE_LIFECYCLE', CASE147='OPEN', full_semantic_formal_acceptance='OPEN',
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

if __name__ == '__main__':
    main()
