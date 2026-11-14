SOURCE_BOUND = False
def require_source_bound():
    if not SOURCE_BOUND: raise ValueError('native223_source_inputs_UNBOUND_before_current_or_effect')
'Reviewed candidate SOURCE only. Import is inert; explicit isolated CLI and externally pinned frame are required.\nRoot alone may issue actual source acceptance/current authority and invoke effects.\n'
'Root recovery of ONLY saved native223 permanent-service phases.\nNo publication, rollback, installer, model, Telegram task or new clock is run.\nOriginal actor is never imported. Verified services retain their exact identity.\n'

from pathlib import Path
from contextlib import closing

import sys, os, json, hashlib, subprocess, sqlite3, time, datetime, stat, fcntl

B = Path(__file__).parent
def bind_source_data(external_manifest_sha256):
 require_source_bound()
 import types,hashlib,json
 from pathlib import Path
 raw=(B/'SOURCE-PINS.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=external_manifest_sha256:raise ValueError('external_source_manifest_changed_before_data_import')
 pins=json.loads(raw);path=B/'root223_data.py';code=path.read_bytes()
 if pins['source_refs'].get(str(path))!=hashlib.sha256(code).hexdigest():raise ValueError('pinned_finite_data_loader_required')
 m=types.ModuleType('Root222DataBoundary');m.__file__=str(path)
 exec(compile(code,str(path),'exec'),m.__dict__)
 return m.bind_namespace(globals(),external_manifest_sha256)



H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')

N = H / 'hermes-agent'

GW = 'hermes-gateway-1b7e7667.service'

DASH = 'hermes-dashboard.service'

PUB = 'frw-astra-native223-install-after222-20261115.service'

J = B / 'ROOT-NATIVE223-LIVE-OPERATION.json'

# Sibling bytes are verified by the externally accepted immutable frame manifest.



now = lambda: datetime.datetime.now().astimezone().isoformat()

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def remaining(deadline, seconds=None):
    value = deadline - time.monotonic()
    if value <= 0:
        raise RuntimeError('original_maintenance_budget_exhausted')
    return value if seconds is None else min(seconds, value)

def operation_remaining(*, reserve=75, seconds=None):
    return remaining(origin + 2700 - reserve, seconds)

def command(args, seconds=5, *, deadline=None):
    if deadline is None and 'origin' in globals():
        deadline = origin + 2700 - 75
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
    result = {'DB9': state_file_snapshot(), 'related': recovery.snapshot(
        j['startup_data_cutoff_scope'], home=H, frame=B,
        check=lambda: operation_remaining())}
    if j.get('stopped_recovery_qualification'):
        recovery.frozen_qualification_checked(j['stopped_recovery_qualification'], result,
                                             j['startup_data_cutoff_scope'])
    return result

def all_service_writers_closed():
    recovery.checked(j['startup_data_cutoff_scope'], home=H, frame=B)
    closed(GW); closed(DASH)
    publisher_terminal_proven(deadline=origin + 2700 - 75)
    return True

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
    'not-found alone is insufficient: this attempt must first bind its invocation.'
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
    if j.get('stopped_user_db_wal_shm_before') and not j['service_phases']:
        assert state_file_snapshot() == j['stopped_user_db_wal_shm_before'], 'frozen_DB9_changed_no_SQLite_reopen'
    else:
        assert data() == counts
    marker = json.loads((H / 'FRIDAY-INSTALL.json').read_bytes())
    assert marker['plugin_files'] == before_marker['plugin_files']
    for name, expected in marker['plugin_files'].items():
        assert sha(H / name) == expected
    operation_remaining(reserve=reserve)

def restore_gate():
    publisher_terminal_proven(deadline=origin + 2700 - 75)
    for path, expected in gate['verified_outputs'].items(): assert sha(path) == expected
    for path, expected in gate['settled_files'].items():
        assert not os.path.lexists(path) if expected is None else sha(path) == expected
    for path, expected in gate['settled_metadata'].items(): assert file_metadata(path) == expected
    unchanged_user()
    if not j['service_phases']:
        assert state_file_snapshot() == gate['stopped_user_db_wal_shm'], 'stopped_DB_WAL_SHM_changed_before_first_service_phase'


def module_source(path):
    import types
    m = types.ModuleType('Root222AcceptedPhaseSource'); m.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), m.__dict__)
    return m

class SourceCaptureJournalPersistenceError(RuntimeError):
    'A failed shared-journal save is an install reconciliation issue.'


class SourceCaptureSourceSafetyError(RuntimeError):
    'A bound optional witness source/custody mismatch requires reconciliation.'


def actual_query_adapter():
    raise FileNotFoundError('separate_F04_semantic_witness_authority_not_part_of_ordinary_install')


def normal_gateway_source_capture(stage, *, reserve, state=None):
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
    pins=json.loads((B/'SOURCE-PINS.json').read_bytes())
    for name in ('core223-first-actual-root.py','boundary_contract.py',
                 'native_scope_post223.py' if publisher_code==0 else 'native_scope_preflight222.py'):
        path=B/name
        assert sha(path)==pins['source_refs'][str(path)], 'exact accepted install guard source required'
    return module_source(B/'core223-first-actual-root.py').installed_service_readback(journal,publisher_code=publisher_code,deadline=journal['absolute_deadline_monotonic']-75)

def main():
    require_source_bound()
    import sys
    if len(sys.argv)<4:raise ValueError('external_source_pins_and_real_data_required')
    bind_source_data(sys.argv[3])
    assert __debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv)==4 and sys.argv[1:3]==['--resume-saved-service-phases','--source-pins-sha256'], 'explicit_saved_service_mode_and_external_pin_required'
    manifest=json.loads((B/'SOURCE-PINS.json').read_bytes()); assert sha(B/'SOURCE-PINS.json')==sys.argv[3], 'external_source_manifest_changed'
    verifier=B/'frame_source.py'; assert sha(verifier)==manifest['source_refs'][str(verifier)], 'pinned_frame_verifier_required'
    module_source(verifier).verify_manifest(sys.argv[3],frame=B)
    lock=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
    fd=os.open(lock,os.O_RDWR|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _resume_saved_operation(shared_slot_identity=[info.st_dev,info.st_ino,info.st_uid,info.st_nlink,stat.S_IMODE(info.st_mode)])
    finally: os.close(fd)

def _resume_saved_operation(*, shared_slot_identity):
    global recovery, cutoff, REQ, before_directories, before_marker, before_metadata, began, confirmed, counts, dash_unit, ds, end, expected, g, gate, identity, j, k, key, limit, listener, name, old, origin, phase, phases, pid, proc, process_environment, q, ready, request, reserve, status, ticks, u, was_verified
    if not (__debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv)==4 and sys.argv[1:3] == ['--resume-saved-service-phases','--source-pins-sha256']):
        raise RuntimeError('explicit_isolated_saved_service_phase_mode_required')

    pins=json.loads((B/'SOURCE-PINS.json').read_bytes()); assert sha(B/'SOURCE-PINS.json')==sys.argv[3], 'external_source_manifest_changed'
    os.umask(0o077)
    import importlib.util
    cutoff_path = B / 'cutoff_contract.py'
    assert sha(cutoff_path) == pins['source_refs'][str(cutoff_path)]
    cutoff_spec = importlib.util.spec_from_file_location('Root222CandidateCutoff',cutoff_path)
    cutoff = importlib.util.module_from_spec(cutoff_spec); cutoff_spec.loader.exec_module(cutoff)

    recovery_path = B / 'recovery_scope.py'
    assert sha(recovery_path) == pins['source_refs'][str(recovery_path)]
    recovery_spec = importlib.util.spec_from_file_location('Root222StoppedRecoveryScope', recovery_path)
    recovery = importlib.util.module_from_spec(recovery_spec); recovery_spec.loader.exec_module(recovery)


    sys.dont_write_bytecode = True

    os.environ.update(HERMES_HOME=str(H), HERMES_GATEWAY_LOCK_DIR='/home/jericho/.local/state/hermes/gateway-locks', GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')

    assert len(sys.argv)==4 and sys.argv[1:3] == ['--resume-saved-service-phases','--source-pins-sha256'], 'explicit_service_only_mode_required'

    assert file_metadata(J)[2] == os.getuid()

    j = json.loads(J.read_bytes())

    assert j['schema'] == 'frw.root.native223-maintenance.v1'
    assert j['source_pin_manifest'] == {'path':str(B/'SOURCE-PINS.json'),'sha256':sha(B/'SOURCE-PINS.json')}
    assert j['runtime_authority'] == {'path':str(B/'ROOT-223-RUNTIME-AUTHORITY.json'),'sha256':sha(B/'ROOT-223-RUNTIME-AUTHORITY.json')}
    pins=json.loads((B/'SOURCE-PINS.json').read_bytes())
    for name in ('run_native223_once.py','resume_native223_services.py','boundary_contract.py',
                 'core223-first-actual-root.py','cutoff_contract.py','recovery_scope.py',
                 'native_scope_preflight222.py','native_scope_post223.py','root223_metadata.py'):
        path=B/name
        assert sha(path)==pins['source_refs'][str(path)], 'saved_install_source_changed'
    authority=json.loads((B/'ROOT-223-RUNTIME-AUTHORITY.json').read_bytes())
    lock_info=os.stat('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock',follow_symlinks=False)
    assert shared_slot_identity == [lock_info.st_dev,lock_info.st_ino,lock_info.st_uid,lock_info.st_nlink,stat.S_IMODE(lock_info.st_mode)] == authority['shared_slot_identity']
    assert j['fresh_root_admission']['sha256'] == sha(j['fresh_root_admission']['path'])


    assert j['gateway_before']['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()

    assert j['absolute_deadline_monotonic'] == j['origin_monotonic'] + 2700

    assert j['source_frame_sha256'] == sha(B / 'run_native223_once.py')

    assert j['restore_service_source'] == {'path': str(Path(__file__)), 'sha256': sha(__file__)}

    original = j['actor_identity']; proc = Path('/proc') / str(original['pid'])
    if proc.exists():
        assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19]) != original['birth_ticks'], 'original_actor_still_owns_operation'

    origin = j['origin_monotonic']

    operation_remaining()

    assert j['publisher_closed_before_parent_custody_release'] is True

    assert j['publisher_launch_consumed_no_retry'] is True

    assert j['state'] not in ['STOP_UNCONFIRMED', 'STOP_UNCONFIRMED_CUSTODY_HELD_ROOT_RECONCILIATION_REQUIRED','ROOT_OPERATION_FAILED_CUSTODY_RELEASED_AFTER_ROOT_RECONCILIATION', 'INSTALLED223_AND_HEALTHY_F04_OWNED_INGRESS_STOP_TERMINAL_SEMANTICS_NOT_RUN_SEPARATE',
        'OLD222_PROJECT525_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING']

    assert j['cutoff_contract_source'] == {'path':str(B/'cutoff_contract.py'),'sha256':sha(B/'cutoff_contract.py')}
    gate = j['restore_verified_inputs']
    recovery.frozen_qualification_checked(j['stopped_recovery_qualification'],
        gate['stopped_all_recovery_data'], j['startup_data_cutoff_scope'])
    recovery_mode = cutoff.saved_recovery_checked(j)

    assert j['default_transaction_postconsumer_returncode'] == 0
    assert gate['publisher_code'] == j['publisher_code']
    assert j['fresh_default_spec_inspect'] and j['full_selected_native_files_readback']

    assert j['user_db_wal_shm_verified_before_starts']

    assert j['selected_native_file_count'] == (j['before_native_file_count']+j['native_addition_count'] if gate['publisher_code']==0 else j['before_native_file_count'])

    assert gate['publisher_code'] in [0, 2]

    assert gate['postcheck_original_deadline'] == j['postcheck_phase']['deadline_mono']

    assert j['postcheck_phase']['deadline_mono'] == j['postcheck_phase']['started_mono'] + 90

    REQ = Path(j['request']['path'])

    assert sha(REQ) == j['request']['sha256']

    q = json.loads(REQ.read_bytes())

    assert q['home'] == str(H)

    counts = j['user_data_before']

    before_metadata = j['unchanged_metadata']

    before_directories = j['unchanged_directories']

    before_marker = {'plugin_files':j['plugin_files_before']}

    process_environment = j['process_environment']

    dash_unit = Path('/home/jericho/.config/systemd/user/hermes-dashboard.service')

    try:
        restore_gate()
        if gate['publisher_code'] == 2:
            if not j['service_phases']:
                cutoff.before_old_start(j,observed=related_recovery_snapshot(),settled=gate['stopped_all_recovery_data'],all_writers_sealed=all_service_writers_closed())
                j['old222_restart_data_boundary_verified_before_any_candidate'] = True; save()
            else:
                assert j.get('old222_restart_data_boundary_verified_before_any_candidate') is True, 'old218_saved_phase_requires_original_exact_data_boundary'
        for name, reserve in [(GW,255),(DASH,75)]:
            phases = j['service_phases']; phase = phases.get(name)
            if phase is None:
                closed(name)
                assert operation_remaining(reserve=reserve) >= 180, 'full_original_service_phase_unavailable'
                if name == GW and gate['publisher_code'] == 0:
                    cutoff.before_unconsumed_candidate_service_start(j,request=j['request'],observed=related_recovery_snapshot(),settled=gate['stopped_all_recovery_data'],all_writers_sealed=all_service_writers_closed(),persist=save)
                if name == GW and gate['publisher_code'] == 0:
                    normal_gateway_source_capture('prepare_normal_gateway_source_custody',reserve=180+180+75)
                assert operation_remaining(reserve=reserve) >= 180, 'full_original_service_phase_unavailable_after_source_prepare'
                began = time.monotonic(); end = began + 180
                phase = {'started_mono':began,'deadline_mono':end,'seconds':180,
                    'start_request_consumed_no_retry':True,'verified':False}
                phases[name] = phase; save()
                if name == GW and gate['publisher_code'] == 0:
                    normal_gateway_source_capture('before_normal_gateway_start',reserve=180+75)
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
                    phase['verified'] = True; phase['verified_identity'] = identity; save()
                    if name == GW and gate['publisher_code'] == 0:
                        dashboard_phase=phases.get(DASH)
                        # Finish an already-consumed Dashboard phase before optional work.
                        if dashboard_phase is None or dashboard_phase['verified']:
                            normal_gateway_source_capture('after_verified_normal_gateway_start',
                                reserve=180+75 if dashboard_phase is None else 90,state=g)
                    break
                time.sleep(min(.25,remaining(end)))
            else: raise RuntimeError('original_service_phase_expired_no_retry')
        if gate['publisher_code'] == 0:
            normal_gateway_source_capture('after_verified_normal_gateway_start',reserve=90,state=g)
        restore_gate()
        if gate['publisher_code'] == 2:
            if not j['service_phases']:
                cutoff.before_old_start(j,observed=related_recovery_snapshot(),settled=gate['stopped_all_recovery_data'],all_writers_sealed=all_service_writers_closed())
                j['old222_restart_data_boundary_verified_before_any_candidate'] = True; save()
            else:
                assert j.get('old222_restart_data_boundary_verified_before_any_candidate') is True, 'old218_saved_phase_requires_original_exact_data_boundary'
        for name,key in [(GW,'gateway_after'),(DASH,'dashboard_after')]:
            u = service(name); expected = j[key]['unit']
            assert all(u[k] == expected[k] for k in ['MainPID','ControlPID','InvocationID','ControlGroup','ActiveState','SubState'])
        # Saved install continuation never reads/bootstrap/resends a case slot.
        j['basic_install_service_readback'] = installed_service_readback(j,publisher_code=gate['publisher_code'])
        save()
        j.update(recovery_ready=False,startup_full_sweep_qualification='NOT_RUN_SEPARATE_POST_INSTALL_R02_ASSESSMENT',
            R02_assessment='NOT_RUN_SEPARATE_LIFECYCLE',CASE147='OPEN',full_semantic_formal_acceptance='OPEN',state='INSTALLED223_AND_HEALTHY_F04_OWNED_INGRESS_STOP_TERMINAL_SEMANTICS_NOT_RUN_SEPARATE' if gate['publisher_code'] == 0 else
            'OLD222_PROJECT525_ROLLBACK_VERIFIED_FRESH_PERMANENT_SERVICES_RUNNING',completed_at_moscow=now(),
            elapsed_seconds=time.monotonic()-origin,permanent_service_unit_configuration_unchanged=True,new_artificial_lifetime_timer=False,
            restore_service_phases_resumed_without_publication_or_clock_reset=True)
        save(); print(json.dumps({'state':j['state'],'elapsed_seconds':j['elapsed_seconds']}))
    except BaseException as error:
        j.update(state='ROOT_SERVICE_ONLY_RECONCILIATION_REQUIRED_NO_RETRY',error_class=type(error).__name__,failure_at_moscow=now())
        save(); raise

if __name__ == '__main__':
    main()
