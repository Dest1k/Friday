"""Future Root206 boundary. Preparation/import is inert; explicit main has live effects.

Adapted from accepted core203-first-actual-root.py; no historical script is run.
Root reviews this source before invoking it. No retry, restored clock, user replay,
Office effect or claim of power-loss atomicity. Actor owns original1800 clock.
"""
import datetime, fcntl, hashlib, json, os, signal, sqlite3, stat, subprocess, sys, time, types
from pathlib import Path
from zoneinfo import ZoneInfo

B = Path(__file__).parent
E = B / 'FUTURE-EXECUTION'
R = Path('/home/jericho/jericho/Friday_rework')
H = R / '.runtime/friday-normal-both-workers-frw032'
F = B
PUB = 'frw-astra-native206-install-after205-20261112.service'
S = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
F205 = Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112')
APP = Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-NEW-CREATOR-APP-RECIPE-20261111/app_contract.py')
GATE = B / 'native_scope.py'
RUNTIME = Path('/home/jericho/.cache/FRW-ASTRA-V3-V03-RECEIVED-PPTX-MISSING-APP-20261111/ROOT-FRESH-RUNTIME-PROOF.json')
BANK = Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-APP-ROOT-FRAME-PREP-20261111/BANK-PHYSICAL-INTEGRITY.json')
BEFORE = 'aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb'
INPUT205 = '2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9'
AFTER = '253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21'
LIMITS = dict(native_canonical_unknown=3, structural_unresolved=45,
              R104_semantic_fail=True, default_workers_ready_accepted=False, DSH_A0_deferred=True)

def require(value, reason):
    if not value: raise RuntimeError(reason)

def now(): return datetime.datetime.now(ZoneInfo('Europe/Moscow')).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_bytes())

def metadata(path):
    path = Path(path); v = path.lstat()
    require(stat.S_ISREG(v.st_mode) and v.st_uid == os.getuid() and v.st_nlink == 1 and
            not any(p.is_symlink() for p in (path, *path.parents)), 'owned_regular_no_link:' + str(path))
    return [v.st_dev, v.st_ino, v.st_uid, v.st_gid, v.st_mode, v.st_nlink]

def ref(path):
    metadata(path)
    return dict(path=str(path), sha256=sha(path))

def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out: out.write(raw); out.flush(); os.fsync(out.fileno())
    parent = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(parent)
    finally: os.close(parent)

def run(argv, timeout=20):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=timeout, check=True)

def module(path, name):
    m = types.ModuleType(name); m.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), m.__dict__)
    return m

def birth(pid): return int((Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])

def wait_same_child(child):
    """No deadline/retry/new child: actor's original finite clock or custody hold governs."""
    while True:
        try: return child.wait()
        except (InterruptedError, KeyboardInterrupt): continue

def launch_once(argv, slotfd, boot):
    """Hold same flock open-description in exact child; defer parent INT/TERM until wait.

    Kernel/pin/report exceptions after Popen still await this child. Its explicit
    STOP_UNCONFIRMED custody hold intentionally keeps parent waiting and slot held.
    SIGKILL/power loss cannot be deferred; inherited fd is process-death insurance,
    not transactional storage or power-loss atomicity.
    """
    pending = []; child = None; code = None; started = time.monotonic()
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def defer(signum, _frame): pending.append(signum)
    for s in previous: signal.signal(s, defer)
    try:
        with (E / 'core206-actual-actor.stdout').open('xb') as out, (E / 'core206-actual-actor.stderr').open('xb') as err:
            require(not pending, 'parent_stop_requested_before_actor')
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     close_fds=True, pass_fds=(slotfd,), start_new_session=True)
            try:
                save(E / 'CORE206-ROOT-ONCE-ACTOR-LAUNCHED.json', dict(pid=child.pid,
                     birth_ticks=birth(child.pid), boot_id=boot, actor=ref(F / 'run_native206_once.py'),
                     once_only=True, shared_slot_held_by_Root_parent=os.getpid(), inherited_slot_fd=slotfd))
            finally:
                # Includes failed birth read/ref/save, BaseException and parent signals.
                code = wait_same_child(child)
        return dict(returncode=code, elapsed_Root_seconds=time.monotonic()-started,
                    deferred_parent_signals=pending, no_retry=True)
    finally:
        # An unexpected exception from local report handling must never release a live actor.
        if child is not None and child.returncode is None: wait_same_child(child)
        for s, handler in previous.items(): signal.signal(s, handler)

def readonly_databases():
    rows = {}; deadline = time.monotonic() + 15
    for label, rel in [('default', 'state.db'), ('dest', 'profiles/dest_telegram/state.db'),
                       ('tester', 'profiles/telegram-bot-8812646969/state.db')]:
        database=H/rel;before=metadata(database)
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2) as db:
            db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 10000)
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            row = dict(quick_check=db.execute('PRAGMA quick_check').fetchone()[0],
                       leases=db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0],
                       messages=db.execute('SELECT count(*) FROM messages').fetchone()[0],
                       sessions=db.execute('SELECT count(*) FROM sessions').fetchone()[0],
                       all_origin_pending_delegations=db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0])
            db.rollback(); require(row['quick_check'] == 'ok' and row['leases'] == 0 and row['all_origin_pending_delegations']==0, 'DB_not_quiescent:' + label)
            require(metadata(database)==before,'database_identity_changed_during_read')
            row['observed_monotonic']=time.monotonic(); rows[label] = row
    # Counts are freshly derived, including any completed M14 query; never fixed5504.
    return rows

def collect_services(boot, anchor, contract):
    services = {}; environments = {}
    keys = 'LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,UnitFileState,RuntimeMaxUSec,NRestarts'
    for label, unit in [('gateway', 'hermes-gateway-1b7e7667.service'), ('dashboard', 'hermes-dashboard.service')]:
        t = dict(x.split('=', 1) for x in run(['/usr/bin/systemctl', '--user', 'show', unit, '--property='+keys]).stdout.splitlines() if '=' in x)
        pid = int(t['MainPID']); ticks = birth(pid); proc = Path('/proc') / str(pid)
        require(all(t[k] == v for k, v in dict(LoadState='loaded', ActiveState='active', SubState='running',
                    UnitFileState='enabled', RuntimeMaxUSec='infinity', NRestarts='0', ControlPID='0').items()), 'permanent_service_unhealthy')
        require(len(t['InvocationID']) == 32 and ('0::'+t['ControlGroup']) in (proc/'cgroup').read_text().splitlines(), 'service_kernel_cgroup_changed')
        selected = {'HERMES_HOME', 'HERMES_GATEWAY_LOCK_DIR', 'HERMES_RUNTIME_DIR', 'HERMES_INSTALL_ROOT', 'HERMES_PROFILE'}
        env = {k.decode():v.decode() for row in (proc/'environ').read_bytes().split(b'\0')
               for k, sep, v in [row.partition(b'=')] if sep and k.decode() in selected}
        require(env.get('HERMES_HOME') == str(H), 'process_environment_home_changed')
        environments[label] = env
        services[label] = dict(pid=pid, birth_ticks=ticks, boot_id=boot, invocation_id=t['InvocationID'],
                               cgroup=t['ControlGroup'], enabled_active=True, runtime_max='infinity')
        contract.compare_service(services[label], anchor['services'][label], env, anchor['process_environment'][label])
        require(birth(pid)==ticks, 'service_birth_changed_during_collection')
    return services, environments

def boundary(m, c, transport, pins, op, anchor, contract, slot, slot_info, *, bank_check=True):
    head = run(['git', '-C', str(R), '--no-optional-locks', 'rev-parse', 'HEAD']).stdout.strip()
    require(run(['git','-C',str(R),'--no-optional-locks','remote','get-url','origin']).stdout.strip() in ('https://github.com/Dest1k/Friday','https://github.com/Dest1k/Friday.git'),'effective_origin_url_changed')
    reference='b86eb1693cdb51f9d3a1a8bd0f7b6f8f06b497cb'
    run(['git','-C',str(R),'--no-optional-locks','merge-base','--is-ancestor',reference,head])
    changed=run(['git','-C',str(R),'--no-optional-locks','diff','--no-renames','--name-only','-z',reference,head]).stdout.split('\0')
    require(all(name.startswith('docs/') or name=='README.md' or name in pins['public_changed_files'] for name in changed if name),'only_accepted_product_and_documentation_may_advance_main')
    mode = pins['execution_provenance_mode']
    require(mode in ('published-remote','local-committed-main'), 'explicit_provenance_mode_required')
    origin = None
    if mode == 'published-remote':
        origin = run(['git', '-C', str(R), '--no-optional-locks', 'ls-remote', '--exit-code', 'origin', 'refs/heads/main']).stdout.split()[0]
    require(origin == pins['execution_public_main_sha'], 'exact_remote_observation_required')
    origin_proof = m.source_origin(pins['execution_commit'], origin, provenance_mode=mode)
    require(head == origin_proof['current_head'], 'head_changed_during_origin_check')
    for name, digest in pins['public_changed_files'].items(): require(sha(R/name) == digest, 'public_source_drift:'+name)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    contract.validate_anchor(anchor,current_time=time.time(),boot=boot,historical=pins['historical_refs'],frame=str(F),publisher=PUB,home=str(H))
    for evidence in anchor['evidence']:require(ref(evidence['path'])==evidence,'fresh_anchor_evidence_changed')
    for path, digest in op['restore_verified_inputs']['settled_files'].items(): require(sha(path) == digest, 'accepted205_afterimage_drift')
    for path, identity in op['unchanged_metadata'].items(): require(metadata(path) == identity, 'route_or_service_metadata_drift')
    receipt = load(H/'hermes-agent.source.json'); marker = load(H/'FRIDAY-INSTALL.json'); stamp = load(H/'hermes-agent/install-stamp.json')
    require(sha(H/'hermes-agent.source.json') == BEFORE and marker['input_sha256'] == INPUT205 and
            marker['source_receipt_sha256'] == BEFORE and (len(receipt['layers']), len(receipt['files']), receipt['source_file_count'], len(marker['plugin_files'])) == (205,17891,17730,52), 'current205_tuple_required')
    require(stamp['fridaySource']['layers'] == receipt['layers'] and stamp['fridaySource']['baseTree'] == receipt['base_tree'], 'current_stamp_mismatch')
    for name, digest in marker['plugin_files'].items(): require(sha(H/name) == digest, 'plugin_pin_drift:'+name)
    full_native=full_native_readback(receipt)
    services, environments = collect_services(boot, anchor, contract)
    tester = Path('/home/jericho/.local/share/friday-telegram-bot-test')
    require(not os.path.lexists(tester/'observer-stop.json'), 'observer_stop_present')
    cooldown = load(tester/'cooldown.json') if (tester/'cooldown.json').exists() else {}
    require(cooldown.get('until', 0) <= time.time(), 'cooldown_active')
    uv = dict(x.split('=',1) for x in run(['/usr/bin/systemctl','--user','show','frw-astra-native206-install-after205-20261112.service','--property=LoadState,MainPID,ControlPID,ControlGroup']).stdout.splitlines() if '=' in x)
    require(uv == dict(LoadState='not-found', MainPID='0', ControlPID='0', ControlGroup=''), 'publisher_unit_already_exists')
    pm_path=Path(m.FIXED['pm_environment_basis']['path']);pm = load(pm_path)
    for key in ('facts', 'pyvenv_cfg'): require(sha(pm[key]['path']) == pm[key]['sha256'], 'PM_environment_pin_changed')
    require(pm['python'] == load(F/'ROOT-FUTURE-COMMANDS.json')['commands']['builder'][0] and
            str(Path(pm['python']).parent.parent) == pm['native_PM_committed_environment'] and Path(pm['python']).is_file(), 'native_PM_selected_Python_changed')
    bank_reuse = None
    if bank_check:
        runtime = load(RUNTIME)
        c.DEADLINE=time.monotonic()+90
        # Old native203 rows are historical; current205 is proven separately.
        context = c.runtime_context({'host_context_rows':runtime['host_context_rows'],'native_source_rows':[]}); bankrows = c.bank_snapshot(runtime)
        template = load(F/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json'); bank = Path(template['bank_path']); critical = {}
        require(sha(BANK) == '7135caf77a9c2ae4de2c12b37a8b327cab2065e76ed87e36f675b5d95528a35c', 'retained_bank_proof_drift')
        for name, row in template['current_critical_bank_files'].items():
            path = bank/name; identity = metadata(path); require(sha(path) == row['sha256'], 'critical_bank_drift')
            critical[name] = dict(sha256=row['sha256'], metadata=identity)
        for name, digest in template['before_profile_source_digests'].items(): require(sha(H/'hermes-agent'/name) == receipt['files'][name]['sha256'] == digest, 'minimum_profile_source_changed')
        bank_reuse = dict(retained_full_hash=ref(BANK), runtime=ref(RUNTIME), physical_rows=len(bankrows), context_rows=len(context), critical=critical)
    mem = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
    fs = os.statvfs(B); cpus = sorted(os.sched_getaffinity(0))
    require(mem > 8*1024**2 and fs.f_bavail*fs.f_frsize > 16*1024**3 and len(cpus) >= 2, 'insufficient_resources')
    resources = dict(memory_available_kib=mem, disk_available_bytes=fs.f_bavail*fs.f_frsize, affinity_cpus=cpus,
                     load_average=list(os.getloadavg()), pressure={k:(Path('/proc/pressure')/k).read_text() for k in ('cpu','io','memory')})
    require(collect_services(boot,anchor,contract)==(services,environments),'service_changed_across_boundary')
    # Bank/resource work precedes the final narrow current-work collection.
    raw = (H/'gateway_state.json').read_bytes(); state = json.loads(raw); tg = state['platforms']['telegram']
    require(state['pid'] == services['gateway']['pid'] and state['start_time'] == services['gateway']['birth_ticks'] and
            state['hermes_home'] == str(H) and state['served_profiles'] == ['default','dest_telegram','telegram-bot-8812646969'] and
            state['gateway_state'] == 'running' and state['active_agents'] == 0 and state['active_work'] is None and
            state['restart_requested'] is False and state['session_store']['status'] == 'ok' and tg['state'] == 'connected' and
            tg['needs_attention'] is False and tg['writer_pid'] == state['pid'] and tg['writer_start_time'] == state['start_time'], 'gateway_routing_or_work_not_clear')
    native = transport.fresh_native(state)  # Never transport.check()/whole historic202 gate.
    require(native['quiescent'] and (H/'gateway_state.json').read_bytes() == raw, 'native_boundary_changed')
    dbs = readonly_databases()
    require(collect_services(boot,anchor,contract)==(services,environments),'service_changed_across_global_refresh')
    require((H/'gateway_state.json').read_bytes()==raw,'gateway_state_changed_across_global_refresh')
    contract.validate_global_quiescence(native['global_work'],dbs,services['gateway'],current_monotonic=time.monotonic())
    return dict(at_moscow=now(), full_native_readback=full_native, global_work=native['global_work'], current_anchor=ref(B/'ROOT-206-CURRENT-SERVICE-ANCHOR.json'), boot_id=boot, head=head, origin_main=origin, source_origin=origin_proof, provenance_mode=mode, services=services,
                process_environment=environments, native_readonly=native, databases=dbs, cooldown=cooldown,
                publisher_unit_absent=uv, resources=resources, gateway_routing=dict(served_profiles=state['served_profiles'],
                telegram_connected=tg['state'], active_agents=state['active_agents'], active_work=state['active_work']),
                bank_reuse=bank_reuse, slot=dict(path=str(slot), dev=slot_info.st_dev,
                ino=slot_info.st_ino, Root_pid=os.getpid()), pm_basis=ref(Path(m.FIXED['pm_environment_basis']['path'])))

def full_native_readback(receipt):
    """Physical bytes for all17891 rows; receipt counts alone are insufficient."""
    started=time.monotonic(); rows=[]
    require(len(receipt['files'])==17891, 'full17891_receipt_required')
    for name,row in sorted(receipt['files'].items()):
        require(time.monotonic()-started<=90, 'full_native_readback_budget_exhausted')
        path=H/'hermes-agent'/name
        require(Path(name).is_absolute() is False and '..' not in Path(name).parts, 'native_inventory_path_invalid')
        before=metadata(path); info=path.stat(); identity=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
        digest=sha(path)
        require(before==metadata(path) and identity(info)==identity(path.stat()) and digest==row['sha256'], 'full_native_physical_drift:'+name)
        rows.append([name,digest])
    return dict(files=len(rows), physical_sha256_verified=True, inventory_digest=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(), elapsed_seconds=time.monotonic()-started)

def main():
    require(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and
            len(sys.argv)==4 and sys.argv[1:3] == ['--execute-once-root-reviewed-206-boundary','--source-pins-sha256'], 'explicit_isolated_Root_mode_required')
    os.umask(0o077); os.environ.update(GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1', HERMES_HOME=str(H))
    require(len(sys.argv[3])==64 and sha(B/'SOURCE-PINS.json') == sys.argv[3], 'source_pin_manifest_changed')
    pins = load(B/'SOURCE-PINS.json')
    contract=module(B/'boundary_contract.py','Root206PureBoundary')
    anchor=load(B/'ROOT-206-CURRENT-SERVICE-ANCHOR.json')
    authority=load(B/'ROOT-206-RUNTIME-AUTHORITY.json')
    require(authority['schema']=='frw.root.native206-reviewed-future-boundary.v1' and authority['state']=='ROOT_REVIEWED_EXACT206_FUTURE_EXECUTION' and authority['template_only_no_execution_grant'] is False,'actual_Root_authority_required')
    require(authority['source_pin_manifest']==ref(B/'SOURCE-PINS.json'),'exact_reviewed_frame_required')
    require(authority['actual205_predecessor']==ref(B/'ROOT-ACTUAL205-PREDECESSOR.json'),'actual205_record_ref_required')
    contract.validate_authority(authority,manifest=ref(B/'SOURCE-PINS.json'),boundary=ref(Path(__file__)),caller=ref(B/'start_core206_once.py'),anchor=ref(B/'ROOT-206-CURRENT-SERVICE-ANCHOR.json'),source_acceptance=ref(B/'ROOT-206-SOURCE-ACCEPTANCE.json'),predecessor=ref(B/'ROOT-ACTUAL205-PREDECESSOR.json'),frame=str(F))
    intent=load(E/'INTENT.json')
    require(intent['source_pin_manifest']==ref(B/'SOURCE-PINS.json') and intent['authority']==ref(B/'ROOT-206-RUNTIME-AUTHORITY.json') and intent['parent_pid']==os.getppid() and intent['parent_birth_ticks']==birth(os.getppid()),'single_reviewed_caller_custody_required')
    pins['execution_provenance_mode']=authority['provenance_mode']
    pins['execution_commit']=authority['execution_commit']
    pins['execution_public_main_sha']=authority['public_main_sha']
    for path, digest in {**pins['source_refs'],**pins['historical_refs']}.items(): require(ref(path)['sha256'] == digest, 'reviewed_source_changed:'+path)
    acceptance = load(F/'ROOT-206-SOURCE-ACCEPTANCE.json')
    require(acceptance['accepted'] is True and acceptance['execution_grant'] is False and acceptance['public_main_sha'] == pins['execution_public_main_sha'] and acceptance['source_provenance']=={'mode':pins['execution_provenance_mode'],'commit':pins['execution_commit']} and authority['source_acceptance']==ref(F/'ROOT-206-SOURCE-ACCEPTANCE.json'), 'Root_final_source_acceptance_required')
    m = module(F/'root206_metadata.py', 'Root206binding'); c = module(APP, 'Root206unchanged_bank'); transport = module(GATE, 'Root206fresh_native_transport_only')
    m.actual_predecessor()
    op = load(F205/'ROOT-NATIVE205-LIVE-OPERATION.json')
    require(op['state'] == 'NATIVE205_PROJECT491_FRESH_PERMANENT_SERVICES_RUNNING' and op['full_selected_native_files_readback'] and op['user_db_wal_shm_verified_before_starts'] and op['publisher_closed_before_parent_custody_release'], 'accepted205_proof_required')
    slot = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
    fd = os.open(slot, os.O_RDWR | os.O_NOFOLLOW); info = os.fstat(fd)
    try:
        require((info.st_dev, info.st_ino, info.st_uid, info.st_nlink, stat.S_IMODE(info.st_mode)) == tuple(authority['shared_slot_identity']), 'shared_slot_identity_changed')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Exactly once, through actor return.
        for name in ('ROOT-FRESH-REQUEST.json','ROOT-206-FRESH-READBACK.json','ROOT-206-BOUND-INPUTS.json','ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION.json','ROOT-206-FRESH-ADMISSION.json','ROOT-NATIVE206-LIVE-OPERATION.json','ROOT-NATIVE206-CUSTODY-RELEASE.json','ROOT-native206-retained-observer.stdout','ROOT-native206-retained-observer.stderr','ROOT-native206-publisher.stdout','ROOT-native206-publisher.stderr','ROOT-native206-default-check.stdout','ROOT-native206-default-check.stderr','admission-retained/READONLY-RETAINED-UNITS-INTENT.json','admission-retained/ROOT-ACTUAL-RETAINED-UNIT-OBSERVATIONS.json'):
            require(not os.path.lexists(F/name), 'once_artifact_already_exists:'+name)
        for name in ('CORE206-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json','CORE206-FIRST-ACTUAL-ROOT-RETURN.json','CORE206-ROOT-ONCE-ACTOR-LAUNCHED.json','core206-actual-actor.stdout','core206-actual-actor.stderr'):
            require(not os.path.lexists(E/name), 'Root_once_artifact_already_exists:'+name)
        evidence = boundary(m, c, transport, pins, op, anchor, contract, slot, info, bank_check=False)
        commands = load(F/'ROOT-FUTURE-COMMANDS.json')['commands']
        argv = list(commands['builder']); argv[argv.index('--current-source-native-predecessor')+1]=m.actual_predecessor()['path']; require(argv[argv.index('--layer')+1] == m.LAYER and argv.count('--layer') == 1 and
                argv[argv.index('--current-source-native-predecessor')+1] == m.actual_predecessor()['path'], 'explicit_singlelayer_canonical205_builder_required')
        builder = run(argv, timeout=90)  # Builder writes only the own fresh request; no H transaction.
        save(E/'CORE206-BUILDER-ACTUAL-RETURN.json', dict(returncode=builder.returncode, stdout=builder.stdout, stderr=builder.stderr))
        q = load(F/'ROOT-FRESH-REQUEST.json'); projection = m.validate_source_request(q)
        require(projection['selected_target_count'] == 17 and projection['expected_receipt_sha256'] == AFTER, 'exact206_seventeenCAS_required')
        require(not os.path.lexists(H/'preparation'/('ordinary-source-update-v45-'+sha(F/'ROOT-FRESH-REQUEST.json')[:16])), 'request_already_consumed')
        # Current readback follows builder/pin work, so metadata300s does not start during old source review.
        latest = boundary(m, c, transport, pins, op, anchor, contract, slot, info)
        require(latest['services'] == evidence['services'], 'service_changed_during_request_build')
        latest.update(source_request_projection=projection, request=ref(F/'ROOT-FRESH-REQUEST.json'), remaining_limits=LIMITS)
        save(E/'CORE206-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json', latest)
        snapshot = load(F/'ROOT-206-FRESH-READBACK-TEMPLATE.json'); snapshot.pop('required_state_after_actual_Root_readback')
        # Each field derives from the successful bounded observations above or exact source join below.
        checks = dict(source_authority_verified=latest['head']==pins['execution_commit'] and latest['origin_main']==pins['execution_public_main_sha'],
            public_source_pins_verified=latest['source_origin']==m.source_origin(latest['head'], latest['origin_main'], provenance_mode=latest['provenance_mode']),
            operational_source_pins_verified=projection['project_files_after']==493,
            profile_routing_verified=latest['gateway_routing']['served_profiles']==['default','dest_telegram','telegram-bot-8812646969'],
            process_environment_verified=all(e['HERMES_HOME']==str(H) for e in latest['process_environment'].values()),
            ordinary_readonly_quiescent=latest['native_readonly']['quiescent'],
            all_three_user_db_zero_leases=len(latest['databases'])==3 and all(v['leases']==0 for v in latest['databases'].values()),
            stop_cooldown_clear=latest['cooldown'].get('until',0)<=time.time(), sole_heavy_slot_clear=latest['slot']['Root_pid']==os.getpid(),
            no_current_maintenance=latest['publisher_unit_absent']['LoadState']=='not-found',
            cancellation_clear=anchor['checks']['current_cancel_stop_cooldown_clear'] and latest['native_readonly']['quiescent'], resources_sufficient=latest['resources']['memory_available_kib']>8*1024**2,
            all_profile_owned_work_quiescent=anchor['checks']['current_all_profile_owned_work_quiescent'] and latest['global_work']['global_active_session_keys']==[] and latest['gateway_routing']['active_agents']==0 and all(v['leases']==v['all_origin_pending_delegations']==0 for v in latest['databases'].values()),
            current_request_unconsumed=not os.path.lexists(H/'preparation'/('ordinary-source-update-v45-'+sha(F/'ROOT-FRESH-REQUEST.json')[:16])),
            old_effects_not_replayed=q['installed_layers']==205 and q['layer_names']==[m.LAYER],
            native_pm_selected_python_verified=latest['pm_basis']==ref(Path(m.FIXED['pm_environment_basis']['path'])),
            product_services_healthy_infinite_lifetime=all(v['runtime_max']=='infinity' for v in latest['services'].values()),
            unchanged_bank_profile_evidence_reusable=latest['bank_reuse']['physical_rows']>5116 and len(latest['bank_reuse']['critical'])==4,
            known_limits_retained=latest['remaining_limits']==LIMITS)
        require(set(checks)==set(m.SNAPSHOT_TRUE_FIELDS) and all(checks.values()), 'incomplete_actual_boundary')
        snapshot.update(state='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT', template_only_no_execution_grant=False,
            head=latest['head'], origin_main=latest['origin_main'], source_origin=latest['source_origin'], provenance_mode=latest['provenance_mode'], boot_id=latest['boot_id'], observed_at_moscow=latest['at_moscow'],
            services=latest['services'], evidence=[ref(E/'CORE206-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json')], checks=checks)
        save(F/'ROOT-206-FRESH-READBACK.json', snapshot)
        pure = m.validate_join(q, acceptance, snapshot, now=time.time(), boot_id=latest['boot_id'])
        binder = run(commands['metadata_binder'], timeout=60)
        save(E/'CORE206-BINDER-ACTUAL-RETURN.json', dict(returncode=binder.returncode, stdout=binder.stdout, stderr=binder.stderr))
        qualification = load(F/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json'); qualification.pop('required_state_after_actual_Root_acceptance')
        bank = Path(qualification['bank_path']); bi = bank.lstat()
        qualification.update(state='ROOT_ACCEPTED_MINIMUM_INSTALLED_BANK_PROFILE_FOR_NATIVE206_SELECTION_NO_FORMAL_CREDIT',
            template_only_no_execution_grant=False, minimum_installed_profile_accepted=True, current_bank_profile_refreshed_at_moscow=now(),
            current_critical_bank_files=latest['bank_reuse']['critical'], bank_directory_metadata=[bi.st_dev,bi.st_ino,bi.st_uid,bi.st_gid,bi.st_mode],
            evidence=[ref(F205/'ROOT-205-MINIMUM-BANK-PROFILE-QUALIFICATION.json'), ref(BANK), ref(RUNTIME), ref(E/'CORE206-FRESH-ACTUAL-BOUNDARY-EVIDENCE.json')],
            profile_equivalence_join=ref(B/'PROFILE-SOURCE-JOIN.json'), actual_scope_and_limits='Fresh bank metadata/topology/linktargets/rootCAS+4criticalhash; exact actual205 PDF/presentation source unchanged in206, saved accepted205 minimumprofile reused by pinned source join. Old runtime rows not reused ascurrent205. No Office/newbank/layout/user/formal credit; old failures/unknowns retained.')
        m.validate_profile_join(qualification,load(H/'hermes-agent.source.json'),load(Path(m.FIXED['native_spec']['path'])))
        save(F/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION.json', qualification)
        admission = load(F/'ROOT-206-FRESH-ADMISSION-TEMPLATE.json'); admission.pop('required_state_after_actual_Root_review_and_qualification')
        admission.update(state='ROOT_ACCEPTED_EXACT206_SOURCE_AND_MINIMUM_INSTALLED_BANK_PROFILE_FINITE_WINDOW',
            template_only_no_execution_grant=False, accepted_at_moscow=now(), boot_id=latest['boot_id'], expected_receipt_sha256=pure['expected_receipt_sha256'],
            request=ref(F/'ROOT-FRESH-REQUEST.json'), source_acceptance=ref(F/'ROOT-206-SOURCE-ACCEPTANCE.json'),
            bound_inputs=ref(F/'ROOT-206-BOUND-INPUTS.json'), minimum_installed_bank_profile_qualification=ref(F/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION.json'))
        save(F/'ROOT-206-FRESH-ADMISSION.json', admission)
        final=boundary(m,c,transport,pins,op,anchor,contract,slot,info)
        require(final['services']==latest['services'] and final['process_environment']==latest['process_environment'],'service_changed_before_actor')
        require(ref(B/'ROOT-206-CURRENT-SERVICE-ANCHOR.json')==authority['current_service_anchor'] and ref(B/'ROOT-206-RUNTIME-AUTHORITY.json')==intent['authority'],'Root_authority_changed_before_actor')
        require(not os.path.lexists(H/'preparation'/('ordinary-source-update-v45-'+sha(F/'ROOT-FRESH-REQUEST.json')[:16])),'whole_transaction_consumed_before_actor')
        require(m.load_actor_binding(F)==pure, 'last_exact_binding_changed')
        # Binding/source reads cannot carry a stale global observation into launch.
        contract.validate_global_quiescence(final['global_work'],final['databases'],final['services']['gateway'],current_monotonic=time.monotonic())
        result = launch_once(commands['once_actor'], fd, latest['boot_id'])
        result.update(state='ROOT_ONCE206_ACTOR_RETURN_RECONCILE_ACTUAL_RESULT', at_moscow=now(),
                      journal=ref(F/'ROOT-NATIVE206-LIVE-OPERATION.json') if (F/'ROOT-NATIVE206-LIVE-OPERATION.json').exists() else None)
        save(E/'CORE206-FIRST-ACTUAL-ROOT-RETURN.json', result); print(json.dumps(result))
        require(not result['deferred_parent_signals'], 'parent_stop_deferred_until_same_actor_return')
    finally:
        # Never LOCK_UN: child's inherited description retains custody if parent dies.
        os.close(fd)

if __name__ == '__main__': main()
