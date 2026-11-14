SOURCE_BOUND = False
def require_source_bound():
    if not SOURCE_BOUND: raise ValueError('native223_source_inputs_UNBOUND_before_current_or_effect')
'Existing ordinary install readback/launch machinery plus exact223 once boundary; import inert.'
from pathlib import Path
from contextlib import closing
import datetime,fcntl,hashlib,json,os,signal,sqlite3,stat,subprocess,sys,time,types
B=Path(__file__).parent
F=B
E=B/'FUTURE-EXECUTION'
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')

def require(value, reason):
    if not value: raise ValueError(reason)

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
    "No deadline/retry/new child: actor's original finite clock or custody hold governs."
    while True:
        try: return child.wait()
        except (InterruptedError, KeyboardInterrupt): continue

def launch_once(argv, slotfd, boot):
    'Hold same flock open-description in exact child; defer parent INT/TERM until wait.\n\n    Kernel/pin/report exceptions after Popen still await this child. Its explicit\n    STOP_UNCONFIRMED custody hold intentionally keeps parent waiting and slot held.\n    SIGKILL/power loss cannot be deferred; inherited fd is process-death insurance,\n    not transactional storage or power-loss atomicity.\n    '
    require(argv == [load(F / 'ROOT-FUTURE-COMMANDS.json')['commands']['builder'][0],
                     '-I', '-B', str(F / 'run_native223_once.py'),
                     '--execute-once-root-accepted-223','--source-pins-sha256',sha(F/'SOURCE-PINS.json')], 'exact_current220_actor_argv_required')
    pending = []; child = None; code = None; started = time.monotonic()
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def defer(signum, _frame): pending.append(signum)
    for s in previous: signal.signal(s, defer)
    try:
        with (E / 'core222-actual-actor.stdout').open('xb') as out, (E / 'core222-actual-actor.stderr').open('xb') as err:
            require(not pending, 'parent_stop_requested_before_actor')
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     close_fds=True, pass_fds=(slotfd,), start_new_session=True)
            try:
                save(E / 'CORE222-ROOT-ONCE-ACTOR-LAUNCHED.json', dict(pid=child.pid,
                     birth_ticks=birth(child.pid), boot_id=boot, actor=ref(F / 'run_native223_once.py'),
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

def readonly_databases(*, deadline=None):
    rows = {}; deadline = time.monotonic()+15 if deadline is None else min(deadline,time.monotonic()+15)
    for label, rel in [('default', 'state.db'), ('dest', 'profiles/dest_telegram/state.db'),
                       ('tester', 'profiles/telegram-bot-8812646969/state.db')]:
        require(time.monotonic()<deadline,'original_readonly_database_deadline_exhausted')
        database=H/rel;before=metadata(database)
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
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

def collect_services(boot, anchor, contract, *, deadline=None):
    services = {}; environments = {}
    keys = 'LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,UnitFileState,RuntimeMaxUSec,NRestarts'
    for label, unit in [('gateway', 'hermes-gateway-1b7e7667.service'), ('dashboard', 'hermes-dashboard.service')]:
        timeout=20 if deadline is None else min(20,deadline-time.monotonic())
        require(timeout>0,'original_install_service_readback_deadline_exhausted')
        t = dict(x.split('=', 1) for x in run(['/usr/bin/systemctl', '--user', 'show', unit, '--property='+keys],timeout=timeout).stdout.splitlines() if '=' in x)
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

def installed_service_readback(journal, *, publisher_code, deadline=None):
    'Basic ordinary install postcondition only; no R02 assessment or UUID API.\n\n    Called after actual default transaction consumer + full17893 readback and\n    fresh normal permanent starts. Reuses exact saved phases; never starts one.\n    '
    require(publisher_code == journal['publisher_code'] and publisher_code in (0,2), 'settled_publisher_branch_required')
    for key in ('fresh_default_spec_inspect','full_selected_native_files_readback','user_db_wal_shm_verified_before_starts'):
        require(journal[key] is True, 'actual_install_postcondition_required:'+key)
    require(journal['default_transaction_postconsumer_returncode']==0 and journal['selected_native_file_count']==(journal['before_native_file_count']+journal['native_addition_count'] if publisher_code==0 else journal['before_native_file_count']),
            'successful_default_consumer_and_full17893_required')
    require(journal['absolute_deadline_monotonic']==journal['origin_monotonic']+2700,'same_original_install_clock_required')
    if deadline is not None:
        require(deadline==journal['absolute_deadline_monotonic']-75 and time.monotonic()<deadline,'original_install_deadline_required')
    contract=module(B/'boundary_contract.py','Root222InstallBoundary')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(boot==journal['actor_identity']['boot_id'], 'same_install_boot_required')
    services={}; environments={}
    for label,unit in (('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')):
        row=journal[label+'_after']; saved=row['unit']; phase=journal['service_phases'][unit]
        require(phase['verified'] is True and phase['start_request_consumed_no_retry'] is True and
                phase['seconds']==180 and phase['deadline_mono']==phase['started_mono']+180,
                'same_verified_consumed_install_phase_required')
        identity=dict(pid=int(saved['MainPID']),start_time=row['start_time'],invocation=saved['InvocationID'],cgroup=saved['ControlGroup'])
        require(identity==phase['verified_identity'] and row['start_time']/os.sysconf('SC_CLK_TCK')>=phase['started_mono']-.05,
                'fresh_saved_install_process_required')
        if label=='gateway': require(row['pid']==identity['pid'] and row['boot_id']==boot,'saved_gateway_identity_changed')
        old=journal['gateway_before']['unit'] if label=='gateway' else journal['dashboard_before']
        require(identity['pid']!=int(old['MainPID']) and identity['invocation']!=old['InvocationID'], 'old_install_process_forbidden')
        services[label]=dict(pid=identity['pid'],birth_ticks=identity['start_time'],boot_id=boot,
                             invocation_id=identity['invocation'],cgroup=identity['cgroup'],enabled_active=True,runtime_max='infinity')
        environments[label]=journal['process_environment'][unit]
    anchor=dict(services=services,process_environment=environments)
    services,environments=collect_services(boot,anchor,contract,deadline=deadline)
    argv=(Path('/proc')/str(services['gateway']['pid'])/'cmdline').read_bytes().rstrip(b'\0').decode().split('\x00')
    normal=contract.validate_normal_gateway_argv(argv)
    raw=(H/'gateway_state.json').read_bytes(); state=json.loads(raw); tg=state['platforms']['telegram']
    require(state['pid']==services['gateway']['pid'] and state['start_time']==services['gateway']['birth_ticks'] and
            state['served_profiles']==['default','dest_telegram','telegram-bot-8812646969'] and state['gateway_state']=='running' and
            state['active_agents']==0 and state['active_work'] is None and state['restart_requested'] is False and
            state['session_store']['status']=='ok' and tg['state']=='connected' and tg['needs_attention'] is False and
            tg['writer_pid']==state['pid'] and tg['writer_start_time']==state['start_time'], 'installed_gateway_routing_or_work_not_clear')
    guard=B/('native_scope_post223.py' if publisher_code==0 else 'native_scope_preflight222.py')
    if deadline is not None: require(time.monotonic()+3<=deadline,'original_native_readback_budget_unavailable')
    native=module(guard,'Root222BasicInstalledNative').fresh_native(state)
    dbs=readonly_databases(deadline=deadline)
    contract.validate_global_quiescence(native['global_work'],dbs,services['gateway'],current_monotonic=time.monotonic())
    require(native['quiescent'] is True and collect_services(boot,anchor,contract,deadline=deadline)==(services,environments) and
            (H/'gateway_state.json').read_bytes()==raw and boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'installed_service_or_state_changed_across_readback')
    if deadline is not None: require(time.monotonic()<deadline,'original_install_readback_deadline_exhausted')
    return dict(services=services,selected_environment=environments,native_readonly=native,DB_current=dbs,
                normal_Source_gateway_argv_sha256=normal,case_assessment='NOT_RUN_SEPARATE_LIFECYCLE')


'Small Root once boundary over the existing reviewed actor/launch/readback.\n\nNo collector or effect runs on import. Root must bind new current records and\nobtain exact independent frame review before invoking the explicit CLI.\n'
def checked_new_operation_plan(pins):
    history_path = B/'ROOT-223-CONSUMED-HISTORY-TEMPLATE.json'
    history = load(history_path)
    require(ref(history_path)['sha256'] == pins['source_refs'][str(history_path)], 'source_pinned_closed222_history_required')
    require(history['schema'] == 'frw.root223.closed-predecessor-history.v1' and
            history['history_only'] is True and history['execution_grant'] is False and
            history['old_admission_and_once_reusable'] is False and history['original_clocks_closed'] is True,
            'closed222_history_not_new_authority')
    basis_path = Path(history['actual222_binding']['path'])
    require(ref(basis_path) == history['actual222_binding'] and
            ref(basis_path)['sha256'] == pins['source_refs'][str(basis_path)], 'exact_typed_actual222_basis_required')
    plan_path = B/'ROOT-223-NEW-OPERATION-PLAN.json'
    value = load(plan_path)
    identity = metadata(plan_path)
    require(stat.S_IMODE(identity[4]) == 0o600 and stat.S_IMODE(plan_path.parent.stat().st_mode) == 0o700,
            'protected_new_Root223_plan_required')
    contract = module(B/'boundary_contract.py','Root223NewPlan')
    contract.validate_new_operation_plan(value,history=ref(history_path),manifest=ref(B/'SOURCE-PINS.json'),
        source_acceptance=ref(B/'ROOT-223-SOURCE-ACCEPTANCE.json'),frame=str(B),
        publisher='frw-astra-native223-install-after222-20261115.service',current_time=time.time())
    require(value['product_source_commit'] == load(B/'ROOT-223-SOURCE-ACCEPTANCE.json')['product_source_commit'],
            'accepted_new223_source_plan_origin_join_required')
    return ref(plan_path)


def checked_prelaunch_qualification_record(value, *, bank_rows, source_spec_ref, operational_input):
    'Validate existing record shape/static bank facts, not live bank state.'
    require(value['bank_path'] == '/home/jericho/.jericho/toolchains/libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111' and
            value['bank_manifest_sha256'] == 'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776',
            'exact_unchanged_minimum_bank_record_required')
    require(value['native_spec'] == source_spec_ref and value['operational_input'] == operational_input,
            'prelaunch_qualification_private527_selected_spec_required')
    directory = value['bank_directory_metadata']
    require(type(directory) is list and len(directory) == 5 and all(type(x) is int for x in directory) and
            directory[0] > 0 and directory[1] > 0 and directory[2] == os.getuid() and
            stat.S_ISDIR(directory[4]) and stat.S_IMODE(directory[4]) == 0o500,
            'typed_owned_protected_bank_directory_record_required')
    names = ('bundle-provenance.json','root/usr/lib/libreoffice/program/soffice',
             'root/usr/lib/libreoffice/program/soffice.bin','root/usr/lib/libreoffice/program/libcomphelper.so')
    require(type(value['current_critical_bank_files']) is dict and
            set(value['current_critical_bank_files']) == set(names), 'exact_four_critical_bank_records_required')
    for name in names:
        recorded = value['current_critical_bank_files'][name];row = bank_rows[name]
        require(type(recorded) is dict and set(recorded) == {'metadata','sha256'} and
                recorded['sha256'] == row['sha256'], 'static_critical_bank_sha_record_required:'+name)
        item = recorded['metadata']
        require(type(item) is list and len(item) == 6 and all(type(x) is int for x in item) and
                item[0] > 0 and item[1] > 0 and item[2] == os.getuid() and item[5] == 1 and
                stat.S_ISREG(item[4]) and stat.S_IMODE(item[4]) == int(row['mode'],8),
                'typed_owned_singlelink_critical_bank_metadata_required:'+name)
    evidence = value['evidence']
    require(type(evidence) is list and evidence, 'actual_Root_qualification_evidence_required_before_once')
    for item in evidence:
        require(type(item) is dict and set(item) == {'path','sha256'} and type(item['path']) is str and
                Path(item['path']).is_absolute() and str(Path(item['path'])) == item['path'] and
                '..' not in Path(item['path']).parts and 'UNBOUND' not in item['path'] and
                type(item['sha256']) is str and len(item['sha256']) == 64 and
                all(c in '0123456789abcdef'for c in item['sha256']), 'exact_qualification_evidence_ref_required')
    return True


def main():
    require_source_bound()
    require(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 4 and
            sys.argv[1:3] == ['--execute-once-root-reviewed-223-boundary','--source-pins-sha256'],
            'explicit_isolated_Root223_once_boundary_required')
    os.umask(0o077)
    expected = sys.argv[3]
    manifest_raw = (B/'SOURCE-PINS.json').read_bytes()
    require(hashlib.sha256(manifest_raw).hexdigest() == expected, 'external_source_manifest_changed')
    pins = json.loads(manifest_raw)
    verifier = B/'frame_source.py'
    require(sha(verifier) == pins['source_refs'][str(verifier)], 'pinned_frame_verifier_required')
    module(verifier,'Root223SourceVerifier').verify_manifest(expected,frame=B)
    module(B/'root223_data.py','Root223Data').bind_namespace(globals(),expected)
    require(not os.path.lexists(E), 'new223_once_boundary_already_consumed_no_retry')
    # All Root records must exist and the exact authority/admission must bind
    # this frozen source before touching the shared slot or consuming once.
    required_records = ('ROOT-223-SOURCE-ACCEPTANCE.json','ROOT-223-CURRENT-SERVICE-ANCHOR.json',
        'ROOT-223-RUNTIME-AUTHORITY.json','ROOT-223-NEW-OPERATION-PLAN.json','ROOT-223-FRESH-READBACK.json',
        'ROOT-223-BOUND-INPUTS.json','ROOT-223-MINIMUM-BANK-PROFILE-QUALIFICATION.json','ROOT-223-FRESH-ADMISSION.json')
    record_refs = {name:ref(B/name)for name in required_records}
    authority = load(B/'ROOT-223-RUNTIME-AUTHORITY.json')
    contract = module(B/'boundary_contract.py','Root223BoundaryContract')
    contract.validate_authority(authority,manifest=ref(B/'SOURCE-PINS.json'),boundary=ref(Path(__file__)),
        caller=ref(Path(__file__)),anchor=ref(B/'ROOT-223-CURRENT-SERVICE-ANCHOR.json'),
        source_acceptance=ref(B/'ROOT-223-SOURCE-ACCEPTANCE.json'),
        predecessor=ref(B/'ACTUAL222-EIGHT-ROW-BINDING.json'),frame=str(B))
    plan = checked_new_operation_plan(pins)
    require(authority['new_operation_plan'] == plan and authority['consumed_history'] ==
            ref(B/'ROOT-223-CONSUMED-HISTORY-TEMPLATE.json'), 'new223_missing_phase_authority_join')
    admission = load(B/'ROOT-223-FRESH-ADMISSION.json')
    qualification_path = B/'ROOT-223-MINIMUM-BANK-PROFILE-QUALIFICATION.json'
    require(stat.S_IMODE(metadata(B/'ROOT-223-FRESH-ADMISSION.json')[4]) == 0o600 and
            admission['template_only_no_execution_grant'] is False and
            admission['schema'] == 'frw.root.native223-fresh-window-admission.v1' and
            admission['state'] == 'ROOT_ACCEPTED_EXACT223_SOURCE_AND_MINIMUM_INSTALLED_BANK_PROFILE_FINITE_WINDOW',
            'actual_new223_admission_required_before_slot_and_once')
    for key,path in dict(actor=B/'run_native223_once.py',recovery=B/'resume_native223_services.py',
                         source_acceptance=B/'ROOT-223-SOURCE-ACCEPTANCE.json',
                         bound_inputs=B/'ROOT-223-BOUND-INPUTS.json',request=B/'ROOT-FRESH-REQUEST.json',
                         minimum_installed_bank_profile_qualification=qualification_path).items():
        require(admission[key] == ref(path), 'prelaunch_exact_admission_ref_required:'+key)
    require(admission['native_spec'] == pins['source_spec_ref'] and
            admission['expected_receipt_sha256'] == EXPECTED and admission['operation_seconds'] == 2700 and
            admission['budgets'] == dict(forward=1200,external_rollback=300,terminal_cleanup=30,
                publisher_unit=1530,publisher_client=1560,operation=2700), 'prelaunch_exact_new223_source_and_budgets')
    require(0 <= time.time()-datetime.datetime.fromisoformat(admission['accepted_at_moscow']).timestamp() <= 300,
            'fresh_Root_admission_required_before_slot_and_once')
    metadata_module = module(B/'root223_metadata.py','Root223Metadata')
    metadata_module.require_bound_data(expected)
    bound = metadata_module.load_actor_binding(B)
    require(bound['selected_target_count'] == len(bound['selected_targets']) == len(metadata_module.bound_data()['native_spec_value']['native_files'])+6 and bound['expected_receipt_sha256'] == EXPECTED,
            'exact_new223_source_projection_required')
    require(admission['home'] == str(H) and admission['consumed_history'] == authority['consumed_history'] and
            admission['new_operation_plan'] == authority['new_operation_plan'] == plan,
            'prelaunch_admission_exact_home_history_new_plan_required')
    qualification = load(qualification_path)
    bank_manifest = Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')
    bank_manifest_sha = 'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'
    require(pins['source_refs'].get(str(bank_manifest)) == bank_manifest_sha and
            sha(bank_manifest) == bank_manifest_sha,'exact_source_pinned_critical_bank_manifest_required')
    bank_rows = {row['relative']:row for row in load(bank_manifest)['files']}
    checked_prelaunch_qualification_record(qualification,bank_rows=bank_rows,
        source_spec_ref=pins['source_spec_ref'],operational_input=bound['current_input'])
    for item in qualification['evidence']:
        require(ref(Path(item['path'])) == item,'current_qualification_evidence_changed_before_slot_and_once')
    require(qualification['state'] == 'ROOT_ACCEPTED_MINIMUM_INSTALLED_BANK_PROFILE_FOR_NATIVE223_SELECTION_NO_FORMAL_CREDIT' and
            qualification['minimum_installed_profile_accepted'] is True and
            qualification['template_only_no_execution_grant'] is False,
            'actual_new223_minimum_profile_record_required_before_slot_and_once')
    metadata_module.validate_profile_join(qualification,metadata_module.supplied_predecessor()['values']['receipt'],
                                         metadata_module.bound_data()['native_spec_value'])
    contract.fresh(qualification['current_bank_profile_refreshed_at_moscow'],time.time())
    anchor = load(B/'ROOT-223-CURRENT-SERVICE-ANCHOR.json')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(admission['boot_id'] == boot,'current_Root_admission_boot_required')
    contract.validate_anchor(anchor,current_time=time.time(),boot=boot,historical=pins['historical_refs'],
        frame=str(B),publisher='frw-astra-native223-install-after222-20261115.service',home=str(H))
    require(anchor['services'] == bound['fresh_root_services'], 'new_actor_bound_current_service_anchor_join')
    lock = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
    slotfd = os.open(lock,os.O_RDWR|os.O_NOFOLLOW)
    try:
        info = os.fstat(slotfd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1 and
                stat.S_IMODE(info.st_mode) == 0o600, 'existing_owned_singlelink_shared_slot_required')
        fcntl.flock(slotfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(all(ref(B/name)==r for name,r in record_refs.items()),'Root_current_records_changed_after_prelaunch_qualification')
        require(authority['shared_slot_identity'] ==
                [info.st_dev,info.st_ino,info.st_uid,info.st_nlink,stat.S_IMODE(info.st_mode)],
                'exact_Root_current_shared_slot_identity_required')
        # Claim before the potentially ambiguous launch. No removal/reset/retry.
        E.mkdir(mode=0o700)
        save(E/'INTENT.json',dict(schema='frw.root223.once-boundary-intent.v1',source_pin_manifest=ref(B/'SOURCE-PINS.json'),
             authority=ref(B/'ROOT-223-RUNTIME-AUTHORITY.json'),new_operation_plan=plan,
             parent_pid=os.getpid(),parent_birth_ticks=birth(os.getpid()),boot_id=boot,
             no_old222_clock_reset=True,no_old_effect_replay=True))
        python = load(B/'ROOT-FUTURE-COMMANDS.json')['commands']['builder'][0]
        result = launch_once([python,'-I','-B',str(B/'run_native223_once.py'),
                              '--execute-once-root-accepted-223','--source-pins-sha256',expected],slotfd,boot)
        result.update(state='ROOT223_ONCE_ACTOR_RETURN_RECONCILE_ACTUAL_RESULT',journal=ref(B/'ROOT-NATIVE223-LIVE-OPERATION.json')
                      if (B/'ROOT-NATIVE223-LIVE-OPERATION.json').exists() else None)
        save(E/'RETURN.json',result)
        print(json.dumps(result))
        return result['returncode']
    finally:
        # launch_once waits for the SAME child, including STOP_UNCONFIRMED hold,
        # before this exact shared open-description can be released.
        os.close(slotfd)


if __name__ == '__main__':
    raise SystemExit(main())
