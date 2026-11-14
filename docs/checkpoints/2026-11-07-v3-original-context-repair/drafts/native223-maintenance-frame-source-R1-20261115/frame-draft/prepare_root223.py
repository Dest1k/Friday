SOURCE_BOUND = False
def require_source_bound():
    if not SOURCE_BOUND: raise ValueError('native223_source_inputs_UNBOUND_before_current_or_effect')
"Root-only finite current record producer. Import inert; never starts installation.\n\nReuses reviewed static/source and running-scope primitives; stopped qualification\nand actual runtime postconditions remain the existing actor's responsibility.\n"
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import fcntl, hashlib, json, os, stat, subprocess, sys, time, types

R=Path('/home/jericho/jericho/Friday_rework')
H=R/'.runtime/friday-normal-both-workers-frw032'
F=Path(__file__).parent
O=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-AFTER220-WHOLE-CALLER-PREP-20261114/frame')
T=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SHA=None
RECOVERY_SHA='6065badeb31001aaf432c295c509b3857d04898fd1b539afbf540c96a988d864'
RECOVERY_DEPENDENCIES={
    'SOURCE-PINS.json':'1ad6e0df4555e5f88cc01ea8b2ca52260b1fb5256fff142b4c71558c2728a6d8',
    'recovery_scope.py':'dc054df08cec229a2f1be1fca3e2e04f1a822dadeb667ea7b85575c4383460e6',
}
PRODUCT_PY=H/'installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'

def require(v,why):
    if not v:raise ValueError(why)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
def now():return datetime.now(ZoneInfo('Europe/Moscow')).isoformat()
def module(p,name,expected):
    raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'source_changed:'+name)
    m=types.ModuleType(name);m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m
def command(args):
    return subprocess.run(args,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20,check=True).stdout
def prospective_ref(p,value):
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()}

def main():
    require_source_bound()
    global SHA
    require(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and
            len(sys.argv)==4 and sys.argv[1:3]==['--root-observe-and-bind-no-install','--source-pins-sha256'],'explicit_Root_current_only_required')
    require(sys.executable==str(PRODUCT_PY),'selected_product_python_required')
    SHA=sys.argv[3]
    os.umask(0o077)
    pins=load(F/'SOURCE-PINS.json');require(sha(F/'SOURCE-PINS.json')==SHA,'external_source_pin_required')
    def fm(name):return module(F/name,'RootCurrent_'+name,pins['source_refs'][str(F/name)])
    fm('frame_source.py').verify_manifest(SHA,frame=F)
    core=fm('core223-first-actual-root.py');contract=fm('boundary_contract.py')
    meta=fm('root223_metadata.py');meta.require_bound_data(SHA);data=meta.bound_data()
    acceptance=load(F/'ROOT-223-SOURCE-ACCEPTANCE.json')
    meta._validate_acceptance_fields(acceptance);meta.validate_independent_acceptances(acceptance)
    final_names=['CURRENT-SERVICE-ANCHOR','FRESH-READBACK','MINIMUM-BANK-PROFILE-QUALIFICATION',
                 'NEW-OPERATION-PLAN','RUNTIME-AUTHORITY','BOUND-INPUTS','FRESH-ADMISSION']
    require(all(not os.path.lexists(F/('ROOT-223-'+n+'.json')) for n in final_names),'current_records_exist_preserve_and_reconcile')
    require(not os.path.lexists(F/'FUTURE-EXECUTION') and
            not os.path.lexists(F/'ROOT-NATIVE223-LIVE-OPERATION.json'),'223_already_started_no_retry')
    request=load(F/'ROOT-FRESH-REQUEST.json')
    source=meta.validate_source_request(request,acceptance)
    actual=meta.actual_predecessor()
    head=command(['/usr/bin/git','--no-optional-locks','-C',str(R),'rev-parse','HEAD']).strip()
    origin=meta.source_origin(head,None,provenance_mode='local-committed-main',acceptance=acceptance)
    require(head==acceptance['source_provenance']['commit'],'accepted_current_main_changed')
    transaction=H/'preparation'/('ordinary-source-update-v45-'+sha(F/'ROOT-FRESH-REQUEST.json')[:16])
    require(not os.path.lexists(transaction),'new223_request_transaction_exists_reconcile')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    services={};envs={};units={}
    for label,unit in [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]:
        keys='LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,UnitFileState,RuntimeMaxUSec,NRestarts'
        row=dict(x.split('=',1) for x in command(['/usr/bin/systemctl','--user','show',unit,'--property='+keys]).splitlines() if '=' in x)
        require(all(row[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items()),'permanent_service_unhealthy')
        pid=int(row['MainPID']);ticks=core.birth(pid);proc=Path('/proc')/str(pid)
        require('0::'+row['ControlGroup'] in (proc/'cgroup').read_text().splitlines(),'service_cgroup_changed')
        selected={b'HERMES_HOME',b'HERMES_GATEWAY_LOCK_DIR',b'HERMES_RUNTIME_DIR',b'HERMES_INSTALL_ROOT',b'HERMES_PROFILE'}
        env={k.decode():v.decode() for raw in (proc/'environ').read_bytes().split(b'\0') for k,sep,v in [raw.partition(b'=')] if sep and k in selected}
        require(env.get('HERMES_HOME')==str(H),'wrong_product_home')
        services[label]=dict(pid=pid,birth_ticks=ticks,boot_id=boot,invocation_id=row['InvocationID'],cgroup=row['ControlGroup'],enabled_active=True,runtime_max='infinity')
        envs[label]=env;units[label]=row
    argv=[x.decode() for x in (Path('/proc')/str(services['gateway']['pid'])/'cmdline').read_bytes().split(b'\0') if x]
    argv_digest=contract.validate_normal_gateway_argv(argv)
    kernel_exe=(Path('/proc')/str(services['gateway']['pid'])/'exe').stat()
    selected_exe=PRODUCT_PY.stat()
    require((kernel_exe.st_dev,kernel_exe.st_ino)==(selected_exe.st_dev,selected_exe.st_ino)
            and sys.version.split()[0]=='3.14.7','actual_gateway_selected_python_identity_required')
    core.metadata(request['launcher']['path']);core.metadata(request['native_unit']['path'])
    raw=(H/'gateway_state.json').read_bytes();state=json.loads(raw);tg=state['platforms']['telegram']
    require(state['pid']==services['gateway']['pid'] and state['start_time']==services['gateway']['birth_ticks'] and state['hermes_home']==str(H),'gateway_state_identity_changed')
    require(state['served_profiles']==['default','dest_telegram','telegram-bot-8812646969'] and
            state['gateway_state']=='running' and state['active_agents']==0 and state['active_work'] is None and
            state['restart_requested'] is False and state['session_store']['status']=='ok' and
            tg['state']=='connected' and tg['needs_attention'] is False,'current_product_not_quiescent_healthy')
    for name,digest in RECOVERY_DEPENDENCIES.items():
        core.metadata(OLD/name);require(sha(OLD/name)==digest,'exact_reused_recovery_dependency_changed:'+name)
    recovery_module=module(OLD/'root221_recovery_scope.py','RootExistingRunningRecovery',RECOVERY_SHA)
    recovery=recovery_module.collect(services,envs)
    require(recovery['current_resume_turn_and_delivery_conflict_free'] is True,'running_recovery_conflict')
    require(not os.path.lexists(T/'observer-stop.json'),'tester_stop_present')
    cooldown=load(T/'cooldown.json') if (T/'cooldown.json').exists() else {}
    require(cooldown.get('until',0)<=time.time(),'tester_cooldown_active')
    publisher='frw-astra-native223-install-after222-20261115.service'
    u=dict(x.split('=',1) for x in command(['/usr/bin/systemctl','--user','show',publisher,'--property=LoadState,MainPID,ControlPID,ControlGroup']).splitlines() if '=' in x)
    require(u==dict(LoadState='not-found',MainPID='0',ControlPID='0',ControlGroup=''),'future_publisher_exists_reconcile')
    locks=[]
    for p in [Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock'),T/'consumer.lock',T/'tester-token']:
        require(not any(q.is_symlink() for q in (p,*p.parents)),'lock_link_rejected')
        fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW)
        try:
            s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1,'unsafe_existing_lock')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks.append(dict(path=str(p),available=True,identity=[s.st_dev,s.st_ino,s.st_uid,s.st_nlink,stat.S_IMODE(s.st_mode)]))
        finally:os.close(fd)
    require(locks[0]['identity'][4]==0o600,'shared_slot_mode_changed')
    memory=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
    fs=os.statvfs(F);cpus=sorted(os.sched_getaffinity(0))
    require(memory>8*1024**2 and fs.f_bavail*fs.f_frsize>16*1024**3 and len(cpus)>=2,'current_resources_insufficient')
    closed147=Path('/home/jericho/.cache/FRW-ASTRA-R02-ORIGINAL147-ROOT-LIVE-20261113/ROOT-ACTUAL-ORIGINAL147-CLOSED.json')
    require(sha(closed147)=='02adbddab6a3f37760d8075d4e0f4fb4273ab404c2e651365195eafaf997cf0d','original147_closure_changed')
    old147=load(closed147)
    require(all(old147[k] is True for k in ['root_current_original147_primary_admission_closed_no_actor_pending','producer_once_consumed','one_original600_expired_not_reset']),'original147_not_closed')
    qualification=load(F/'ROOT-223-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json')
    bank=Path(qualification['bank_path']);s=bank.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o500 and not any(p.is_symlink() for p in (bank,*bank.parents)),'bank_root_changed')
    qualification['bank_directory_metadata']=[s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode]
    for n,row in qualification['current_critical_bank_files'].items():
        row['metadata']=core.metadata(bank/n);require(sha(bank/n)==row['sha256'],'bank_critical_source_changed')
    before=meta.supplied_predecessor()['values']['receipt']
    for n,digest in qualification['before_profile_source_digests'].items():require(sha(H/'hermes-agent'/n)==digest,'installed_bank_profile_source_changed')
    meta.validate_profile_join({**qualification,'template_only_no_execution_grant':False},before,data['native_spec_value'])
    # The <=15s native/SQL cut is taken last, after slower source/bank/writer work.
    native=fm('native_scope_preflight222.py').fresh_native(state)
    dbs=core.readonly_databases()
    contract.validate_global_quiescence(native['global_work'],dbs,services['gateway'],current_monotonic=time.monotonic())
    require((H/'gateway_state.json').read_bytes()==raw,'gateway_state_changed_during_boundary')
    core.collect_services(boot,{'services':services,'process_environment':envs},contract)
    at=now()
    evidence=dict(schema='frw.Root.native223.current-observation.v1',at_moscow=at,boot_id=boot,
        services=services,selected_environment=envs,raw_units=units,gateway_argv_sha256=argv_digest,
        native=native,all3_databases=dbs,recovery_scope=recovery,original147_closed=ref(closed147),
        original147_not_pending=True,old_original147_acceptance='OPEN_UNKNOWN_TIMING_NO_REPLAY',
        gateway_state_sha256=hashlib.sha256(raw).hexdigest(),served_profiles=state['served_profiles'],telegram_connected=tg['state'],
        observer_stop_absent=True,cooldown_clear=True,future_publisher=u,unconsumed_transaction_path=str(transaction),
        unconsumed_transaction_absent=True,locks=locks,
        resources=dict(memory_available_kib=memory,disk_available_bytes=fs.f_bavail*fs.f_frsize,affinity=cpus),
        selected_product_python=str(PRODUCT_PY),python_version=sys.version.split()[0],source_request_check=source,
        reused_running_recovery_source=ref(OLD/'root221_recovery_scope.py'),
        reused_running_recovery_dependencies={n:ref(OLD/n) for n in RECOVERY_DEPENDENCIES},
        finite_current_check_scope={
            'cancellation_clear':'No current blocker in the observed finite operation scope: tester observer-stop absent/cooldown elapsed; gateway restart false; all effective served routes active/resume/suspended clear; global runner/terminal/web work and all3 SQL leases/delegations quiescent. This actor does not invoke native cancel and has no operation cancel receipt. Unexposed in-memory queues/approvals remain unproved.',
            'no_current_maintenance':'Existing common synthetic-live-acceptance flock and tester consumer/token flocks available at exact current identities; new223 journal/once/transaction absent; future publisher not-found; same-UID nonservice H writer/cwd scan clear. Together with owner-authorized sole-integrator custody, this excludes competing authorized maintenance of THIS admitted resource domain, not every hypothetical host process.',
            'future_exclusion':'The reviewed actor reacquires the exact common slot then native/build/PM/home/all-profile admission locks and proves retained22 consumers stopped before stopped DB/recovery qualification. These future observations are NOT pre-PASS in this record.',
            'not_claimed':['HOST_WIDE_GLOBAL_MAINTENANCE_OR_CANCEL_API','ALL_PROFILE_IN_MEMORY_PENDING_QUEUE_APPROVAL_PROOF','HOSTILE_SAME_UID_WRITER_ISOLATION','POWERLOSS_ATOMICITY'],
        },
        current_actual222_predecessor=actual,source_origin=origin,source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),
        current_bank_directory_metadata=qualification['bank_directory_metadata'],current_critical_bank_files=qualification['current_critical_bank_files'],
        limitations=['ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED','SCOPED_TESTER_QUEUE_FIELDS_DO_NOT_PROVE_ALL_PROFILE_PENDING_OR_APPROVALS','POINT_OBSERVATION_PLUS_SINGLE_INTEGRATOR_CUSTODY_NOT_HOSTILE_WRITER_OR_POWERLOSS_ATOMICITY'],
        no_model_user_send_Office_maintenance_once_or_operation_clock=True,execution_grant=False)
    ep=O/('ROOT223-FRESH-CURRENT-OBSERVATION-'+str(time.time_ns())+'.json')
    # Actual evidence must exist before metadata.validate_join follows refs.
    # If a later pure check refuses, preserve this dated observation; no grant,
    # once or maintenance has been created. A later capture uses a new leaf.
    core.save(ep,evidence);er=core.ref(ep)
    anchor=load(F/'ROOT-223-CURRENT-SERVICE-ANCHOR-TEMPLATE.json');anchor.pop('required_state_after_actual_Root_readback')
    anchor.update(state='ROOT_ACTUAL_CURRENT222_BOUNDARY',template_only_no_execution_grant=False,observed_at_moscow=at,boot_id=boot,services=services,process_environment=envs,historical_refs=pins['historical_refs'],evidence=[er],checks={k:True for k in anchor['checks']})
    anchor['quiescence_basis']['root_current_all_profile_pending_approval_cancel_maintenance_evidence']=[er]
    anchor['startup_data_cutoff_scope']=recovery['startup_data_cutoff_scope'];anchor['startup_data_cutoff_scope']['evidence']=[er]
    fm('recovery_scope.py').checked(anchor['startup_data_cutoff_scope'],home=H,frame=F)
    contract.validate_anchor(anchor,current_time=time.time(),boot=boot,historical=pins['historical_refs'],frame=str(F),publisher=publisher,home=str(H))
    qualification.pop('required_state_after_actual_Root_acceptance')
    qualification.update(state='ROOT_ACCEPTED_MINIMUM_INSTALLED_BANK_PROFILE_FOR_NATIVE223_SELECTION_NO_FORMAL_CREDIT',template_only_no_execution_grant=False,minimum_installed_profile_accepted=True,current_bank_profile_refreshed_at_moscow=at,
        declared_minimum_scope='Exact207 PDF/presentation source retained through222 into223; no new Office/App/layout/formal credit.',
        actual_scope_and_limits='Fresh actual bank directory metadata/four critical hashes and222 profile source; exact immutable207 profile evidence reused. Existing RTF/ODP limits retained; no format/layout/formal acceptance.',
        evidence=[er,qualification['profile_equivalence_join']])
    meta.validate_profile_join(qualification,before,data['native_spec_value'])
    rows={r['relative']:r for r in load('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')['files']}
    core.checked_prelaunch_qualification_record(qualification,bank_rows=rows,source_spec_ref=data['native_spec'],operational_input=data['static_binding']['current_input'])
    snapshot=load(F/'ROOT-223-FRESH-READBACK-TEMPLATE.json');snapshot.pop('required_state_after_actual_Root_current_readback')
    snapshot.update(state='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT',template_only_no_execution_grant=False,observed_at_moscow=at,boot_id=boot,head=head,origin_main=None,provenance_mode='local-committed-main',source_origin=origin,services=services,evidence=[er],checks={k:True for k in snapshot['checks']})
    # Every true check above is backed by the actual source/CAS, native/SQL,
    # services, recovery, queue-limit, locks and bank observations in evidence.
    binding=meta.validate_join(request,acceptance,snapshot,now=time.time(),boot_id=boot)
    plan=load(F/'ROOT-223-NEW-OPERATION-PLAN-TEMPLATE.json')
    plan.update(state='ROOT_REVIEWED_DISTINCT_FUTURE223_OPERATION',template_only_no_execution_grant=False,consumed_history=ref(F/'ROOT-223-CONSUMED-HISTORY-TEMPLATE.json'),source_pin_manifest=ref(F/'SOURCE-PINS.json'),source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),selected_frame_review=acceptance['frame_review_evidence'][0],reviewed_at_moscow=at)
    contract.validate_new_operation_plan(plan,history=ref(F/'ROOT-223-CONSUMED-HISTORY-TEMPLATE.json'),manifest=ref(F/'SOURCE-PINS.json'),source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),frame=str(F),publisher=publisher,current_time=time.time())
    authority=load(F/'ROOT-223-RUNTIME-AUTHORITY-TEMPLATE.json')
    authority.update(state='ROOT_REVIEWED_EXACT223_FUTURE_EXECUTION',template_only_no_execution_grant=False,
        current_service_anchor=prospective_ref(F/'ROOT-223-CURRENT-SERVICE-ANCHOR.json',anchor),source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),source_pin_manifest=ref(F/'SOURCE-PINS.json'),new_operation_plan=prospective_ref(F/'ROOT-223-NEW-OPERATION-PLAN.json',plan),
        execution_commit=head,provenance_mode='local-committed-main',origin_url=command(['/usr/bin/git','--no-optional-locks','-C',str(R),'remote','get-url','origin']).strip(),public_main_sha=None,
        shared_slot_identity=locks[0]['identity'],future_finite_operation_reviewed=True,old_effects_clocks_preserved=True,
        document_owner_217_accepted_source_only_not_runtime_qualified=True,m09_summary_218_accepted_source_only_not_runtime_qualified=True)
    contract.validate_authority(authority,manifest=ref(F/'SOURCE-PINS.json'),boundary=ref(F/'core223-first-actual-root.py'),caller=ref(F/'core223-first-actual-root.py'),anchor=authority['current_service_anchor'],source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),predecessor=ref(F/'ACTUAL222-EIGHT-ROW-BINDING.json'),frame=str(F))
    # Commit actual records only after all source/current validation in RAM.
    for name,value in [('CURRENT-SERVICE-ANCHOR',anchor),('MINIMUM-BANK-PROFILE-QUALIFICATION',qualification),('FRESH-READBACK',snapshot),('NEW-OPERATION-PLAN',plan),('RUNTIME-AUTHORITY',authority)]:core.save(F/('ROOT-223-'+name+'.json'),value)
    bound=dict(schema='frw.root.native223-bound-inputs.v1',state='ROOT_CURRENT_BOUND_INPUTS_NOT_EXECUTION_GRANT',template_only_no_execution_grant=False,binding=binding,request=ref(F/'ROOT-FRESH-REQUEST.json'),source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),fresh_readback=ref(F/'ROOT-223-FRESH-READBACK.json'))
    core.save(F/'ROOT-223-BOUND-INPUTS.json',bound)
    meta.load_actor_binding(F)
    admission=load(F/'ROOT-223-FRESH-ADMISSION-TEMPLATE.json');admission.pop('required_state_after_actual_Root_review_and_qualification')
    admission.update(state='ROOT_ACCEPTED_EXACT223_SOURCE_AND_MINIMUM_INSTALLED_BANK_PROFILE_FINITE_WINDOW',template_only_no_execution_grant=False,accepted_at_moscow=now(),boot_id=boot,
        bound_inputs=ref(F/'ROOT-223-BOUND-INPUTS.json'),source_acceptance=ref(F/'ROOT-223-SOURCE-ACCEPTANCE.json'),minimum_installed_bank_profile_qualification=ref(F/'ROOT-223-MINIMUM-BANK-PROFILE-QUALIFICATION.json'),new_operation_plan=ref(F/'ROOT-223-NEW-OPERATION-PLAN.json'))
    core.save(F/'ROOT-223-FRESH-ADMISSION.json',admission)
    print(json.dumps(dict(state='ROOT_CURRENT222_BOUND_AND_FINITE223_ADMISSION_READY_NO_INSTALL_STARTED',at_moscow=at,services={k:v['pid'] for k,v in services.items()},messages={k:v['messages'] for k,v in dbs.items()},evidence=ref(ep),operation_clock_started=False)))

if __name__=='__main__':main()
