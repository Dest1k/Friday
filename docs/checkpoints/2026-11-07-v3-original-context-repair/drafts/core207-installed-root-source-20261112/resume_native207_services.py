'Root recovery of ONLY saved native207 permanent-service phases.\nNo publication, rollback, installer, model, Telegram task or new clock is run.\nOriginal actor is never imported. Verified services retain their exact identity.\n'
from pathlib import Path
import sys, os, json, hashlib, subprocess, sqlite3, time, datetime, stat
if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode):
    raise RuntimeError('isolated_nonoptimized_no_bytecode_python_required')
os.umask(0o077); sys.dont_write_bytecode = True
B = Path(__file__).parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N = H / 'hermes-agent'
os.environ.update(HERMES_HOME=str(H), HERMES_GATEWAY_LOCK_DIR='/home/jericho/.local/state/hermes/gateway-locks', GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
GW = 'hermes-gateway-1b7e7667.service'
DASH = 'hermes-dashboard.service'
PUB = 'frw-astra-native207-install-after206-20261112.service'
J = B / 'ROOT-NATIVE207-LIVE-OPERATION.json'
now = lambda: datetime.datetime.now().astimezone().isoformat()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


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
        '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,NRestarts,InvocationID,Result,ExecMainStatus,ControlGroup,UnitFileState,Description'], deadline=deadline)
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

def publisher_cgroup_empty():
    group = j.get('publisher_cgroup')
    if not group: return True
    assert group.startswith('/user.slice/') and group.endswith('/' + PUB) and '..' not in Path(group).parts
    base = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not base.exists(): return True
    events = dict(row.split() for row in (base / 'cgroup.events').read_text().splitlines())
    return events.get('populated') == '0' and not (base / 'cgroup.procs').read_text().strip()

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
        assert result['InvocationID'] in [j['publisher_invocation_id'], ''], 'publisher_invocation_changed'
    assert publisher_cgroup_empty() and publisher_process_closed(), 'owned_publisher_scope_not_closed'
    return result

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

assert sys.argv[1:] == ['--resume-saved-service-phases'], 'explicit_service_only_mode_required'
assert file_metadata(J)[2] == os.getuid()
j = json.loads(J.read_bytes())
assert j['schema'] == 'frw.root.native207-maintenance.v1'
assert j['gateway_before']['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert j['absolute_deadline_monotonic'] == j['origin_monotonic'] + 1800
assert j['source_frame_sha256'] == sha(B / 'run_native207_once.py')
assert j['restore_service_source'] == {'path': str(Path(__file__)), 'sha256': sha(__file__)}
origin = j['origin_monotonic']
operation_remaining()
assert j['publisher_closed_before_parent_custody_release'] is True
assert j['publisher_launch_consumed_no_retry'] is True
assert j['state'] not in ['STOP_UNCONFIRMED', 'STOP_UNCONFIRMED_CUSTODY_HELD_ROOT_RECONCILIATION_REQUIRED','ROOT_OPERATION_FAILED_CUSTODY_RELEASED_AFTER_ROOT_RECONCILIATION', 'NATIVE207_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING',
    'OLD206_PROJECT493_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING']
gate = j['restore_verified_inputs']
assert j['fresh_default_spec_inspect'] and j['full_selected_native_files_readback']
assert j['user_db_wal_shm_verified_before_starts']
assert j['selected_native_file_count'] == 17891
assert gate['publisher_code'] in [0, 2]
assert gate['postcheck_original_deadline'] == j['postcheck_phase']['deadline_mono']
assert j['postcheck_phase']['deadline_mono'] == j['postcheck_phase']['started_mono'] + 90
REQ = Path(j['request']['path']); assert sha(REQ) == j['request']['sha256']
q = json.loads(REQ.read_bytes()); assert q['home'] == str(H)
counts = j['user_data_before']; before_metadata = j['unchanged_metadata']
before_directories = j['unchanged_directories']; before_marker = {'plugin_files':j['plugin_files_before']}
process_environment = j['process_environment']
dash_unit = Path('/home/jericho/.config/systemd/user/hermes-dashboard.service')

def restore_gate():
    publisher_terminal_proven(deadline=origin + 1800 - 75)
    for path, expected in gate['verified_outputs'].items(): assert sha(path) == expected
    for path, expected in gate['settled_files'].items():
        assert not os.path.lexists(path) if expected is None else sha(path) == expected
    for path, expected in gate['settled_metadata'].items(): assert file_metadata(path) == expected
    unchanged_user()
    if not j['service_phases']:
        assert state_file_snapshot() == gate['stopped_user_db_wal_shm'], 'stopped_DB_WAL_SHM_changed_before_first_service_phase'
    # After a consumed start, byte evolution has no attribution claim here;
    # count/QC/lease guards continue, no publication or start replay is allowed.

try:
    restore_gate()
    for name, reserve in [(GW,255),(DASH,75)]:
        phases = j['service_phases']; phase = phases.get(name)
        if phase is None:
            closed(name)
            assert operation_remaining(reserve=reserve) >= 180, 'full_original_service_phase_unavailable'
            began = time.monotonic(); end = began + 180
            phase = {'started_mono':began,'deadline_mono':end,'seconds':180,
                'start_request_consumed_no_retry':True,'verified':False}
            phases[name] = phase; save()
            request = command(['systemctl','--user','start','--no-block',name],deadline=end)
            event('saved_phase_permanent_start_requested',unit=name,returncode=request.returncode)
            assert request.returncode == 0
        else:
            began,end = phase['started_mono'],phase['deadline_mono']
            assert phase['seconds'] == 180 and end == began + 180
            assert phase['start_request_consumed_no_retry'] is True
        was_verified = phase['verified']; limit = None if was_verified else end
        while was_verified or time.monotonic() < end:
            u = service(name,deadline=limit)
            if was_verified:
                assert u['ActiveState'] == 'active' and u['SubState'] == 'running', 'verified_permanent_service_changed'
            assert u['ActiveState'] != 'failed', 'saved_service_phase_failed_no_retry'
            if u['ActiveState'] == 'active' and u['SubState'] == 'running' and int(u['MainPID']) > 0:
                pid = int(u['MainPID']); proc = Path('/proc') / str(pid)
                ticks = int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])
                assert ticks / os.sysconf('SC_CLK_TCK') >= began - .05
                old = j['gateway_before']['unit'] if name == GW else j['dashboard_before']
                assert u['InvocationID'] != old['InvocationID'] and len(u['InvocationID']) == 32
                assert u['ControlPID'] == '0' and u['ControlGroup'] and '0::'+u['ControlGroup'] in (proc/'cgroup').read_text().splitlines()
                assert selected_process_environment(pid) == process_environment[name]
                identity = {'pid':pid,'start_time':ticks,'invocation':u['InvocationID'],'cgroup':u['ControlGroup']}
                if was_verified: assert phase['verified_identity'] == identity
                if name == GW:
                    try: g = json.loads((H/'gateway_state.json').read_bytes())
                    except FileNotFoundError: g = {}
                    ready = g.get('pid') == pid and g.get('gateway_state') == 'running' and g.get('platforms',{}).get('telegram',{}).get('state') == 'connected'
                    if not ready:
                        assert not was_verified, 'verified_gateway_state_changed'
                        time.sleep(min(.25,remaining(end))); continue
                    assert g['start_time'] == ticks and g['served_profiles'] == ['default','dest_telegram','telegram-bot-8812646969']
                    j['gateway_after'] = {'pid':pid,'start_time':ticks,'boot_id':j['gateway_before']['boot_id'],'unit':u}
                else:
                    status = command([str(N/'.hermes/bin/hermes'),'-p','default','dashboard','--status'],30,deadline=limit)
                    phase['last_dashboard_status_returncode'] = status.returncode
                    phase['last_dashboard_status_stdout_sha256'] = hashlib.sha256(status.stdout).hexdigest()
                    phase['last_dashboard_status_stderr_sha256'] = hashlib.sha256(status.stderr).hexdigest()
                    save()
                    if status.returncode == 3 and not was_verified:
                        time.sleep(min(.25,remaining(end))); continue
                    assert status.returncode == 0, 'dashboard_saved_phase_status_unknown'
                    ds = json.loads(status.stdout)
                    assert ds['state'] == 'VERIFIED' and all(ds[key] is True for key in ['verified','nonce_verified','auth_required','servesSpa'])
                    assert ds['pid'] == pid and ds['startTime'] == ticks and ds['source_receipt_sha256'] == sha(H/'hermes-agent.source.json')
                    listener = command(['ss','-H','-ltn','sport = :9119'],deadline=limit)
                    assert listener.returncode == 0 and listener.stdout.strip()
                    j['dashboard_after'] = {'unit':u,'native_status':ds,'start_time':ticks}
                confirmed = service(name,deadline=limit)
                assert all(confirmed[key] == u[key] for key in ['MainPID','ControlPID','InvocationID','ControlGroup','ActiveState','SubState'])
                if not was_verified: remaining(end)
                phase['verified'] = True; phase['verified_identity'] = identity; save(); break
            time.sleep(min(.25,remaining(end)))
        else: raise RuntimeError('original_service_phase_expired_no_retry')
    restore_gate()
    for name,key in [(GW,'gateway_after'),(DASH,'dashboard_after')]:
        u = service(name); expected = j[key]['unit']
        assert all(u[k] == expected[k] for k in ['MainPID','ControlPID','InvocationID','ControlGroup','ActiveState','SubState'])
    j.update(state='NATIVE207_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING' if gate['publisher_code'] == 0 else
        'OLD206_PROJECT493_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING',completed_at_moscow=now(),
        elapsed_seconds=time.monotonic()-origin,permanent_service_unit_configuration_unchanged=True,new_artificial_lifetime_timer=False,
        restore_service_phases_resumed_without_publication_or_clock_reset=True)
    save(); print(json.dumps({'state':j['state'],'elapsed_seconds':j['elapsed_seconds']}))
except BaseException as error:
    j.update(state='ROOT_SERVICE_ONLY_RECONCILIATION_REQUIRED_NO_RETRY',error_class=type(error).__name__,failure_at_moscow=now())
    save(); raise
