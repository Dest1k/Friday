"""Complete ONLY missing old203 postcheck/service phases under original204maintenance clock.
No publication/retry/rollback/installation/new clock/Office/model/user task.
Original failed journal immutable; new recovery references exact frozen failure.
"""
from pathlib import Path
import sys,os,json,hashlib,subprocess,sqlite3,time,datetime,stat,signal,fcntl
assert __debug__ and sys.flags.isolated and sys.dont_write_bytecode
assert sys.argv[1:]==['--recover-only-exact-old203-services']
os.umask(0o077)
D=Path(__file__).resolve().parent
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-ROOT-MAINTENANCE-FRAME-20261111')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032');N=H/'hermes-agent'
P=Path('/home/jericho/.cache/FRW-SOL-V3-CORE203-FINAL-COMPOSITION-20261111/project487')
GW='hermes-gateway-1b7e7667.service';DASH='hermes-dashboard.service';PUB='frw-astra-native204-publication-20261111.service'
OLD=B/'ROOT-NATIVE204-LIVE-OPERATION.json';J=D/'OLD203-SERVICE-RECOVERY.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.datetime.now().astimezone().isoformat()
OLD_SHA='1eaffcf49ba6e23889c2cdea76b40ed08810d1491cf2c50ddf7d244404cb08a9'
assert sha(OLD)==OLD_SHA
j=json.loads(OLD.read_bytes());assert j['state']=='ROOT_RECONCILIATION_REQUIRED_DO_NOT_RETRY_OR_START_BLINDLY'
origin=j['origin_monotonic'];assert j['absolute_deadline_monotonic']==origin+1800
assert j['gateway_before']['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert j['publisher_launch_consumed_no_retry'] and j['publisher_closed_before_parent_custody_release']
assert not j['service_phases'] and not J.exists()
j['original_failure_ref']={'path':str(OLD),'sha256':OLD_SHA};j['original_failed_state']=j['state']
j['recovery_source']={'path':str(Path(__file__)),'sha256':sha(__file__)}
j['publisher_exit_outcome']='UNKNOWN_AFTER_ROOT_OBSERVER_ASSERT';j['recovery_is_not_publisher_retry']=True
j['state']='EXACT_OLD203_POSTCHECK_STARTED';j['service_phases']={}
REQ=Path(j['request']['path']);assert sha(REQ)==j['request']['sha256'];q=json.loads(REQ.read_bytes());assert q['home']==str(H)
counts=j['user_data_before'];before_metadata=j['unchanged_metadata'];before_directories=j['unchanged_directories'];before_marker={'plugin_files':j['plugin_files_before']}
process_environment=j['process_environment'];dash_unit=Path('/home/jericho/.config/systemd/user/hermes-dashboard.service')


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
        assert result['InvocationID'] == j['publisher_invocation_id']
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


slot=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
slotfd=os.open(slot,os.O_RDWR|os.O_NOFOLLOW);si=os.fstat(slotfd)
assert (si.st_dev,si.st_ino,si.st_uid,si.st_nlink,stat.S_IMODE(si.st_mode))==(2050,9440373,os.getuid(),1,0o600)
fcntl.flock(slotfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
operation_remaining(reserve=180+180+75,seconds=90)
poststart=time.monotonic();postend=poststart+90
assert postend<=origin+1800-180-180-75
j['recovery_postcheck']={'started_mono':poststart,'deadline_mono':postend,'seconds':90};save()
publisher_terminal_proven(deadline=postend)
for field in ['actor_identity','owned_local_process_identity','publisher_client_identity']:
 identity=j[field];p=Path('/proc')/str(identity['pid'])
 assert not p.exists() or int((p/'stat').read_text().rsplit(')',1)[1].split()[19])!=identity['birth_ticks'],field
closed(GW,deadline=postend);closed(DASH,deadline=postend)
unchanged_user(reserve=180+180+75)
for key in ['marker','source_receipt','stamp','configuration','profile','launcher','native_unit']:assert sha(q[key]['path'])==q[key]['sha256'],key
receipt=json.loads((H/'hermes-agent.source.json').read_bytes());assert len(receipt['layers'])==203 and len(receipt['files'])==17891
for name,row in receipt['files'].items():
 remaining(postend);assert sha(N/name)==row['sha256'],name
for name,before in j['before_project_targets'].items():
 p=H/name
 assert not os.path.lexists(p) if before is None else sha(p)==before['sha256'] and file_metadata(p)[2:]==before['metadata'][2:],name
# Known request identity, original source-update journal cannot be assumed settled.
tx=H/'preparation'/('ordinary-source-update-v45-'+sha(REQ)[:16])
assert not (tx/'intent.json').exists(), 'unexpected_transaction_intent_requires_separate_reconciliation'
assert state_file_snapshot()==j['stopped_user_db_wal_shm_before']
oldinput=Path(q['previous_input']['path']);assert sha(oldinput)==q['previous_input']['sha256']
value=json.loads(oldinput.read_bytes());assert value['home']==str(H) and len(value['project_files'])==487
for name,h in value['project_files'].items():remaining(postend);assert sha(P/name)==h,name
PY=q['python']['path'] if isinstance(q.get('python'),dict) else str(H/'installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python')
argv=[PY,'-I','-B',str(P/'scripts/friday_install.py'),'check','--input',str(oldinput)]
out=D/'OLD203-default-check.stdout';err=D/'OLD203-default-check.stderr'
with out.open('xb') as so,err.open('xb') as se:
 child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,env=dict(os.environ,HERMES_HOME=str(H),PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
 try:
  child_birth=int((Path('/proc')/str(child.pid)/'stat').read_text().rsplit(')',1)[1].split()[19])
  j['default_consumer_identity']={'pid':child.pid,'birth_ticks':child_birth,'session':child.pid,'process_group':child.pid};save()
  code=child.wait(timeout=remaining(postend))
 except BaseException:
  if child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
  try:os.killpg(child.pid,0)
  except ProcessLookupError:pass
  else:raise RuntimeError('STOP_UNCONFIRMED_own_consumer_group_after_timeout')
  raise
try:os.killpg(child.pid,0)
except ProcessLookupError:j['default_consumer_group_closed']=True;save()
else:raise RuntimeError('STOP_UNCONFIRMED_own_consumer_group_after_reap')
assert code==0,'genuine_unchanged203_default_consumer_refused'
remaining(postend);assert state_file_snapshot()==j['stopped_user_db_wal_shm_before']
j['recovery_verified_old203']={'full17891_native_sha':True,'canonical_request_CAS':True,'project_beforeimages_exact':True,'source_project487_sha':True,'default_spec_check_code':code,'actual_consumer':[str(out),str(err)],'stopped_DB_WAL_SHM_exact':True,'publisher_exit_outcome':'UNKNOWN_AFTER_ROOT_OBSERVER_ASSERT','no_transaction_intent':True};save()
settled={str(H/'FRIDAY-INSTALL.json'):sha(H/'FRIDAY-INSTALL.json'),str(H/'hermes-agent.source.json'):sha(H/'hermes-agent.source.json'),str(N/'install-stamp.json'):sha(N/'install-stamp.json')}
def restore_gate():
 publisher_terminal_proven(deadline=origin+1800-75)
 assert sha(OLD)==OLD_SHA,'original_failure_changed'
 for p,h in settled.items():assert sha(p)==h,'verified_old_source_drift'
 unchanged_user()
 if not j['service_phases']:assert state_file_snapshot()==j['stopped_user_db_wal_shm_before']


try:
    restore_gate()
    for name, reserve in [(GW,255),(DASH,75)]:
        phases = j['service_phases']; phase = phases.get(name)
        if phase is None:
            old_unit=closed(name)
            assert old_unit['UnitFileState']=='enabled' and old_unit['RuntimeMaxUSec']=='infinity','prestart_permanent_unit_lifetime_changed'
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
            assert u['UnitFileState']=='enabled' and u['RuntimeMaxUSec']=='infinity','permanent_unit_lifetime_changed'
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
        u = service(name); assert u['UnitFileState']=='enabled' and u['RuntimeMaxUSec']=='infinity'; expected = j[key]['unit']
        assert all(u[k] == expected[k] for k in ['MainPID','ControlPID','InvocationID','ControlGroup','ActiveState','SubState'])
    j.update(state='EXACT_UNCHANGED_OLD203_SERVICES_RECOVERED_PUBLISHER_EXIT_UNKNOWN',completed_at_moscow=now(),
        elapsed_seconds=time.monotonic()-origin,permanent_service_unit_configuration_unchanged=True,new_artificial_lifetime_timer=False,
        restore_service_phases_resumed_without_publication_or_clock_reset=True)
    save(); print(json.dumps({'state':j['state'],'elapsed_seconds':j['elapsed_seconds'],'original_failure_immutable':sha(OLD)==OLD_SHA}))
except BaseException as error:
    j.update(state='ROOT_SERVICE_ONLY_RECONCILIATION_REQUIRED_NO_RETRY',error_class=type(error).__name__,failure_at_moscow=now())
    save(); raise
