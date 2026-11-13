"""Single original presentation forward operation, SOURCE ONLY until Root binds.

No effects at import. --readonly-before-clock performs the genuine entire
pre-save qualifier plus current209 collection under three existing locks; it
creates no run/claim/operation clock and reads no credential. --execute-once is
a distinct Root-only future effect. No retry/resume/install/producer path exists.
"""
from __future__ import annotations
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import types

SHARED_DRIVER={'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113/source/root_f07_once.py','bytes':34852,'sha256':'e40343ca212f551d62e842879485f039fbfc6bfb0d9e6777b64776e9eb832ce0'}
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
PYTHON='/home/jericho/jericho/.venv/bin/python'
TIMING=dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600)
PREPARATION_WALL_SECONDS=300
LIMITS=dict(cpu_seconds=120,max_rss_bytes=512*1024**2,disk_bytes=100*1024**2)
PROJECTION_LIMIT='ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED'
ROOT_ASSERTIONS=('original_forward_effect_eligible','old_effects_UNKNOWN_clocks_preserved',
 'all_profile_semantic_unlogged_equivalents_reconciled','root_current_pending_approval_cancel_maintenance_assessed')
INPUT_KEYS={'schema','status','operator','run_id','workdir','driver','source_review','preparation','checker',
 'selected_tester','authority','installation_closure','source_acceptance','Root_acceptance','resources','slot_identity','disk_scope'}


def need(ok,code):
    if not ok:raise ValueError(code)


def encoded(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()


def read_shared():
    p=Path(SHARED_DRIVER['path']);need(not any(q.is_symlink() for q in (p,*p.parents)),'PRESENTATION_SHARED_DRIVER_LINK')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as s:
        before=os.fstat(s.fileno());raw=s.read(SHARED_DRIVER['bytes']+1);after=os.fstat(s.fileno())
    identity=lambda x:tuple(getattr(x,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and stat.S_IMODE(before.st_mode)==0o600
         and before.st_nlink==1 and identity(before)==identity(after)==identity(p.stat())
         and len(raw)==SHARED_DRIVER['bytes'] and digest(raw)==SHARED_DRIVER['sha256'],'PRESENTATION_SHARED_DRIVER_CHANGED')
    m=types.ModuleType('_presentation_reused_finite_helpers');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__);return m


def validate(v,H):
    need(type(v) is dict and set(v)==INPUT_KEYS and v.get('schema')=='frw.Root.PRESENTATION.single-forward-driver.v1'
         and v.get('status')=='ROOT_BOUND_ONE_FUTURE_OPERATION' and v.get('operator')=='Root',
         'PRESENTATION_DRIVER_UNBOUND_NO_EFFECT')
    need(type(v['run_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v['run_id'])
         and v['run_id']!='UNBOUND','PRESENTATION_NEW_RUN_REQUIRED')
    H.canonical_path(v['workdir'])
    for key in INPUT_KEYS & {'driver','source_review','preparation','checker','selected_tester','authority',
                            'installation_closure','source_acceptance','Root_acceptance'}:
        need(H.reference_shape(v[key]),'PRESENTATION_SIZED_ROOT_BINDINGS_REQUIRED')
    need(v['resources']==dict(TIMING,**LIMITS) and all(type(n) is int for n in v['resources'].values()),
         'PRESENTATION_EXACT_FINITE_EXECUTOR_RESOURCES_REQUIRED')
    s=v['disk_scope']
    need(type(s) is dict and set(s)=={'directory_roots','file_paths','max_entries','sample_seconds','scope_evidence'}
         and type(s['directory_roots']) is list and str(STATE) in s['directory_roots'] and v['workdir'] in s['directory_roots']
         and type(s['file_paths']) is list and type(s['max_entries']) is int and 0<s['max_entries']<=100000
         and type(s['sample_seconds']) in (int,float) and 0<s['sample_seconds']<=1
         and type(s['scope_evidence']) is list and bool(s['scope_evidence']),'PRESENTATION_BOUNDED_WRITE_SCOPE_REQUIRED')
    for names in (s['directory_roots'],s['file_paths']):
        need(names==sorted(set(names)),'PRESENTATION_SORTED_WRITE_SCOPE_REQUIRED')
        for p in names:H.canonical_path(p)
    for r in s['scope_evidence']:need(H.reference_shape(r),'PRESENTATION_WRITE_SCOPE_SOURCE_REQUIRED')
    need(type(v['slot_identity']) is dict and set(v['slot_identity'])=={'device','inode','uid','mode','nlink'},
         'PRESENTATION_EXISTING_SLOT_IDENTITY_REQUIRED')
    return True


def current_facts(checker,observed):
    return dict(history_sha256=observed['history']['sha256'],custody_sha256=observed['custody']['sha256'],
        native_SQL_boundary_sha256=checker.digest(checker.encoded(dict(native=observed['native'],databases=observed['databases']))),
        runtime_hashes=observed['installed']['runtime_hashes'],profile_configs=observed['profile_configs'],
        source_stat=observed['source_stat'],presentation_runtime=observed['presentation_runtime'])


def validate_acceptance(v,a,phase,H):
    need(type(a) is dict and a.get('schema')=='frw.Root.PRESENTATION.explicit-preop-decisions.v1'
         and a.get('status')=='ROOT_BOUND_ONE_FUTURE_FORWARD' and a.get('operator')=='Root'
         and a.get('run_id')==v['run_id'] and a.get('scenario_sha256')==phase['scenario_sha256']
         and a.get('Root_authorizes_observed_hash_binding_only') is True,
         'PRESENTATION_EXPLICIT_ROOT_DECISION_UNBOUND')
    need(a.get('bindings')=={k:v[k] for k in ('driver','source_review','preparation','checker','selected_tester',
         'authority','installation_closure','source_acceptance')},'PRESENTATION_EXACT_ACCEPTED_BINDINGS_REQUIRED')
    decision=a.get('original_forward_decision',{});privacy=a.get('privacy_preflight',{})
    need(all(decision.get(k) is True for k in ROOT_ASSERTIONS)
         and decision.get('equivalent_consumed_forward_effects')==[] and decision.get('projection_limit')==PROJECTION_LIMIT
         and type(decision.get('current_scope_evidence')) is list and bool(decision['current_scope_evidence'])
         and type(a.get('accepted_current_facts')) is dict,'PRESENTATION_ROOT_FORWARD_HISTORY_DECISION_REQUIRED')
    need(privacy.get('source_metadata_only_checked') is True and privacy.get('raw_user_retention_separately_scoped') is True
         and privacy.get('genuine_current_event_observed') is False and privacy.get('runtime_logging_verdict')=='NOT_ESTABLISHED',
         'PRESENTATION_SOURCE_PRIVACY_NOT_RUNTIME_VERDICT_REQUIRED')
    for key in ('source_evidence','effective_roots_source_basis','effective_product_roots','private_roots'):
        need(type(privacy.get(key)) is list and bool(privacy[key]),'PRESENTATION_EXPLICIT_PRIVATE_ROOTS_BASIS_REQUIRED')
    need(a.get('aggregate_disk_monitor_limitations_accepted') is True,'PRESENTATION_OBSERVED_GROWTH_NOT_HARD_QUOTA_ACK_REQUIRED')
    return True


def source_inputs(v,H):
    """Explicit exact SOURCE/protected Root inputs. No Store/current/API writes."""
    validate(v,H)
    H.readref(v['driver']);need(v['driver']['path']==str(Path(__file__).absolute()),'PRESENTATION_EXACT_EXECUTED_DRIVER_REQUIRED')
    review=H.doc(v['source_review'])
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('open_critical_defects')==[]
         and v['driver'] in review.get('reviewed_sources',[]) and v['checker'] in review.get('reviewed_sources',[]),
         'PRESENTATION_INDEPENDENT_FINAL_DELTA_REVIEW_REQUIRED')
    checker=H.load_raw(H.readref(v['checker']),v['checker']['path'],'_presentation_current209')
    prep=checker.module(checker.PREP)
    need(checker.PREP in review['reviewed_sources'],'PRESENTATION_REVIEWED_PREPARATION_REQUIRED')
    phase=H.doc(v['preparation']);prep.validate_preparation(phase)
    prep.validate_retained_unit(phase['retained_unit'],reader=H.readref)
    candidate=json.loads(H.readref(prep.CANDIDATE))
    need(phase['scenario']==candidate['scenario'],'PRESENTATION_EXACT_TASK37_REQUEST_REQUIRED')
    base=H.readref(v['selected_tester'],private=False)
    need(v['selected_tester']['path']==prep.SELECTED_TESTER and digest(base)==prep.SELECTED_SHA,
         'PRESENTATION_GENUINE_SELECTED_CC36_REQUIRED')
    authority=H.doc(v['authority'])
    # Exact producer→effect reference must qualify before a once claim/clock.
    phase_scenario_ref(v,phase)
    ordinary=prep.compose_source(base,phase,run_id=v['run_id'],authority_ref=v['authority'],authority=authority,
                                retained_unit=phase['retained_unit'])
    acceptance=H.doc(v['Root_acceptance']);validate_acceptance(v,acceptance,phase,H)
    products=acceptance['privacy_preflight']['effective_product_roots'];private=acceptance['privacy_preflight']['private_roots']
    need(products==sorted(set(products)) and str(checker.H) in products and private==sorted(set(private)),
         'PRESENTATION_SORTED_EFFECTIVE_ROOTS_REQUIRED')
    for p in private:
        H.protected_directory(p)
        need(all(not H.canonical_path(p).is_relative_to(H.canonical_path(r))
             and not H.canonical_path(r).is_relative_to(H.canonical_path(p)) for r in products),
             'PRESENTATION_PRIVATE_ROOT_INTERSECTS_PRODUCT')
    paths=[v[k]['path'] for k in ('driver','source_review','preparation','checker','authority','installation_closure','source_acceptance','Root_acceptance')]
    paths += [v['workdir'],phase['runtime_basis']['path'],phase['retained_unit']['Root_binding']['path']]
    need(all(any(H.canonical_path(p).is_relative_to(H.canonical_path(r)) for r in private) for p in paths),
         'PRESENTATION_PRIVATE_MATERIAL_ROOTS_COVERAGE_REQUIRED')
    # Existing source lives in product UserScope; never require it under secret roots.
    for p in v['disk_scope']['directory_roots']:
        need(not checker.H.is_relative_to(H.canonical_path(p)) and not (checker.H/'hermes-agent').is_relative_to(H.canonical_path(p)),
             'PRESENTATION_BULK_PRODUCT_SOURCE_SCAN_REFUSED')
    for r in (acceptance['original_forward_decision']['current_scope_evidence']
              +acceptance['privacy_preflight']['source_evidence']+acceptance['privacy_preflight']['effective_roots_source_basis']
              +v['disk_scope']['scope_evidence']):H.readref(r)
    H.protected_directory(v['workdir'])
    need(not (STATE/'runs'/(v['run_id']+'.json')).exists(),'PRESENTATION_NO_EXISTING_RUN_REPLAY')
    return checker,prep,base,phase,authority,ordinary,acceptance


def qualify_before_clock(v,H,checker,prep,phase,ordinary,acceptance):
    """FUTURE ROOT ONLY, shared slot held. Genuine pre-save and current209.

    Existing consumer/token locks, no creation. API=None and no token read.
    Only after both complete and unchanged may execute() claim once and clock.
    """
    genuine=H.load_raw(ordinary,v['selected_tester']['path'],'_presentation_preclock_ordinary')
    paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads']
    before={str(p):H.protected_directory(p) for p in paths};store=genuine.Store(STATE)
    need({str(p):H.protected_directory(p) for p in paths}==before,'PRESENTATION_STORE_CONSTRUCTOR_MUTATED_DIRS')
    with store.lock(create=False),store.lock(STATE/'tester-token',create=False):
        me=H.kernel(os.getpid())
        for p in (SLOT,STATE/'consumer.lock',STATE/'tester-token'):checker.lock_held(p,me)
        runner=genuine.Runner(store,None);runner._presentation_reference_bytes=H.readref
        prefix=prep.qualify_selected_ordinary_readonly(runner,run_id=v['run_id'],phase=phase)
        observed=checker.observe_readonly(phase=phase,run_id=v['run_id'],closure_ref=v['installation_closure'],
            acceptance_ref=v['source_acceptance'],resource_limits={k:v['resources'][k] for k in ('max_rss_bytes','disk_bytes')})
        need(current_facts(checker,observed['observed'])==acceptance['accepted_current_facts'],
             'PRESENTATION_ROOT_REVIEWED_CURRENT_BASIS_CHANGED')
        return dict(state='WHOLE_PRE_SAVE_AND_CURRENT209_READONLY_QUALIFIED_NOT_ADMISSION',prefix=prefix,
            current=observed,once_claim_created=False,operation_clock_created=False,API_created=False)


def effect(checker,prep,v,phase,resources):
    return checker.prepare_effect(run_id=v['run_id'],phase=phase,authority_ref=v['authority'],scenario_ref=phase_scenario_ref(v,phase),
        checker_ref=v['checker'],closure_ref=v['installation_closure'],acceptance_ref=v['source_acceptance'],resources=resources)


def phase_scenario_ref(v,phase):
    # Root must pre-save exact canonical scenario; no implicit creation before once.
    # The authority pins this existing scenario leaf explicitly.
    H=read_shared();authority=H.doc(v['authority']);ref=authority.get('presentation_scenario')
    need(H.reference_shape(ref) and H.readref(ref)==encoded(phase['scenario']),
         'PRESENTATION_ROOT_CANONICAL_SCENARIO_REFERENCE_REQUIRED')
    return ref


def apply_store_write_budget(store,H,disk_bytes):
    """Charge each genuine Store atomic write including its temporary full copy.

    Direct immutable one-shot receipts are small existing guarded writes and the
    parent also samples their declared scope. This is not a filesystem quota.
    """
    original=store.write;initial={};current={}
    def bounded(path,data):
        p=H.canonical_path(str(path))
        need(p.is_relative_to(store.root) and not any(q.is_symlink() for q in (p,*p.parents)),
             'PRESENTATION_STORE_WRITE_OUTSIDE_CANONICAL_SCOPE')
        if p not in initial:
            initial[p]=p.stat().st_size if p.exists() else 0;current[p]=initial[p]
        growth=sum(max(0,size-initial[name]) for name,size in current.items())
        need(growth+len(data)<=disk_bytes,'PRESENTATION_AGGREGATE_STORE_WRITE_BOUND')
        original(p,data);current[p]=len(data)
    store.write=bounded
    return dict(scope='genuine_Store.write_and_atomic_copy',disk_bytes=disk_bytes,hard_filesystem_quota=False)


def bind_decisions(H,checker,v,phase,acceptance,e,observed):
    need(current_facts(checker,observed)==acceptance['accepted_current_facts'],'PRESENTATION_ACCEPTED_CURRENT_FACTS_CHANGED')
    decision=dict(acceptance['original_forward_decision'],schema='frw.Root.PRESENTATION.current209-original-case-decision.v1',
        operator='Root',status='ROOT_BOUND',whole_effect_sha256=checker.digest(checker.encoded(e)),
        history_sha256=observed['history']['sha256'],custody_sha256=observed['custody']['sha256'],
        native_SQL_boundary_sha256=current_facts(checker,observed)['native_SQL_boundary_sha256'],explicit_Root_acceptance=v['Root_acceptance'])
    privacy=dict(acceptance['privacy_preflight'],schema='frw.Root.PRESENTATION.current209-privacy-preflight.v1',operator='Root',
        status='ROOT_BOUND_PREFLIGHT_NOT_RUNTIME_VERDICT',whole_effect_sha256=checker.digest(checker.encoded(e)),
        runtime_hashes=observed['installed']['runtime_hashes'],logging_sites=list(checker.LOGGING_SITES),
        technical_log_cursor=observed['technical_log_cursor'],postcondition_plan=checker.postcondition_plan(e,observed),
        effective_roots_profile_config_refs=observed['profile_configs'],explicit_Root_acceptance=v['Root_acceptance'])
    return H.new(Path(v['workdir'])/'ROOT-ORIGINAL-FORWARD-DECISION.json',checker.encoded(decision)),\
           H.new(Path(v['workdir'])/'ROOT-PRIVACY-PREFLIGHT.json',checker.encoded(privacy))


def owned_consumer(v,H,binding_ref,clock_ref,cleanup_ref,slot_fd,parent_identity):
    """Explicit future Root child, exact finite resources before actual caller."""
    H.child_limits(v['resources'])
    checker,prep,base,phase,authority,ordinary,acceptance=source_inputs(v,H)
    need(os.getppid()==parent_identity['pid'] and H.kernel(os.getppid())==parent_identity,'PRESENTATION_OWNED_PARENT_CHANGED')
    need(H.lock_identity(os.fstat(slot_fd))==v['slot_identity'],'PRESENTATION_INHERITED_SLOT_CHANGED')
    checker.lock_held(SLOT,parent_identity);clock=H.doc(clock_ref);work=Path(v['workdir'])
    need(clock['run_id']==v['run_id'] and clock['deadline_monotonic']-clock['started_monotonic']==600
         and time.monotonic()+305<clock['deadline_monotonic'],'PRESENTATION_ORIGINAL_CLOCK_TOO_SHORT_BEFORE_NEW')
    resources=dict(v['resources'],clock=clock_ref,owned_parent_wait_cleanup=cleanup_ref)
    e=effect(checker,prep,v,phase,resources)
    genuine=H.load_raw(ordinary,v['selected_tester']['path'],'_presentation_ordinary')
    paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads']
    before={str(p):H.protected_directory(p) for p in paths};store=genuine.Store(STATE)
    need({str(p):H.protected_directory(p) for p in paths}==before,'PRESENTATION_CHILD_STORE_CONSTRUCTOR_MUTATED_DIRS')
    apply_store_write_budget(store,H,v['resources']['disk_bytes'])
    with store.lock(create=False) as consumer_fd,store.lock(STATE/'tester-token',create=False) as credential_fd:
        me=H.kernel(os.getpid())
        checker.lock_held(STATE/'consumer.lock',me);checker.lock_held(STATE/'tester-token',me)
        invocation=H.new(work/'ROOT-ONCE-CONSUMER-INVOCATION.json',encoded(dict(
            schema='frw.Root.PRESENTATION.one-ordinary-consumer-invocation.v1',run_id=v['run_id'],
            whole_effect_sha256=checker.digest(checker.encoded(e)),clock=clock_ref,no_retry=True,consumer=me,driver_binding=binding_ref)))
        runner=genuine.Runner(store,None);runner._presentation_reference_bytes=H.readref
        prep.qualify_selected_ordinary_readonly(runner,run_id=v['run_id'],phase=phase)
        observed=checker.observe(e,stage='BASELINE')
        decision,privacy=bind_decisions(H,checker,v,phase,acceptance,e,observed)
        wall,mono=time.time(),time.monotonic();proof=checker.unbound_proof()
        proof.update(status='ROOT_BOUND',effect=checker.clone(e),whole_effect_sha256=checker.digest(checker.encoded(e)),
            observed=checker.clone(observed),created_at=wall,expires_at=wall+120,created_monotonic=mono,expires_monotonic=mono+120,
            boot_id=me['boot_id'],lock_owners=dict(shared_slot=parent_identity,consumer=me,credential=me),
            invocation=invocation,Root_decision=decision,privacy_preflight=privacy)
        need(set(proof)==checker.PROOF_FIELDS,'PRESENTATION_EXACT_PROOF_ASSEMBLY_REQUIRED')
        proof_ref=H.new(work/'ROOT-FRESH-CURRENT209-PROOF.json',checker.encoded(proof))
        checker.decisions(proof,observed,proof_ref);checker.fresh(proof)
        candidate=checker.compose_preintent_source(ordinary,phase=phase,run_id=v['run_id'],authority_ref=v['authority'],
            authority=authority,proof_ref=proof_ref,checker_ref=v['checker'])
        candidate_ref=H.new(work/'bot_tester.presentation.current209.py',candidate)
        module=H.load_raw(H.readref(candidate_ref),candidate_ref['path'],'_presentation_actual_consumer')
        H.new(work/'ROOT-ACTUAL-EFFECT-AND-CONSUMER.json',checker.encoded(dict(effect=e,proof=proof_ref,candidate=candidate_ref,
            acceptance='NOT_ESTABLISHED',semantic='NOT_RUN')))
        api=module.BotAPI(module.safe_read(STATE/'tester-token',256).decode('ascii').strip())
        runner=module.Runner(store,api);run=None;stage='NEW'
        try:
            run=runner.new(v['run_id'],phase['scenario'])
            stage='SEND';runner.send(run,consumer_fd=consumer_fd,credential_fd=credential_fd)
            stage='OBSERVE';runner.observe(run)
        except BaseException as exc:
            H.new(work/'CONSUMER-RAW-FAILURE.json',encoded(dict(status='REFUSED_INTERRUPTED_OR_UNKNOWN',phase=stage,
                exception_class=type(exc).__name__,frames=H.enum_failure_frames(exc,stage),no_retry=True,
                product_cancelled=False,semantic='NOT_ESTABLISHED')))
            raise
        finally:
            path=STATE/'runs'/(v['run_id']+'.json')
            H.new(work/'CONSUMER-RAW-CLOSURE.json',encoded(dict(run_id=v['run_id'],canonical_run=H.fileref(path) if path.exists() else None,
                stage=stage,raw_status=run.get('status') if run is not None else None,
                raw_send_state=run.get('send_state') if run is not None else None,
                capture_window_complete=run.get('capture_window_complete') if run is not None else None,
                acceptance='NOT_ESTABLISHED',semantic='NOT_ESTABLISHED',privacy='NOT_ESTABLISHED',custody='NOT_ESTABLISHED',
                native_host_close='NOT_ESTABLISHED',no_retry=True)))
    return 0


def readonly(v,H):
    checker,prep,base,phase,authority,ordinary,acceptance=source_inputs(v,H)
    slot=H.safe_lock(SLOT,v['slot_identity'])
    try:return qualify_before_clock(v,H,checker,prep,phase,ordinary,acceptance)
    finally:os.close(slot)


def execute(v,H,*,binding_ref):
    checker,prep,base,phase,authority,ordinary,acceptance=source_inputs(v,H)
    work=Path(v['workdir']);need(not list(work.iterdir()),'PRESENTATION_FRESH_EMPTY_OPERATION_WORKDIR_REQUIRED')
    slot=H.safe_lock(SLOT,v['slot_identity']);actor=None;clock=None;wait_done=False;stops=[];lifetime=dict(cleanup_attempted=False)
    previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)};forwarded=0
    def forward():
        nonlocal forwarded
        while actor is not None and forwarded<len(stops):
            sig=stops[forwarded];forwarded+=1
            if actor.poll() is None:
                try:actor.send_signal(sig)
                except ProcessLookupError:pass
    def requested(sig,_):stops.append(int(sig));forward()
    try:
        for s in previous:signal.signal(s,requested)
        qualification=qualify_before_clock(v,H,checker,prep,phase,ordinary,acceptance)
        baseline=H.scan_scope(v['disk_scope'],deadline=time.monotonic()+30)
        # End the separate bounded no-effect preparation interval before any
        # once claim or original operation clock. It never extends outer600.
        signal.setitimer(signal.ITIMER_REAL,0)
        H.new(work/'ROOT-ONCE-DRIVER-INVOCATION.json',encoded(dict(schema='frw.Root.PRESENTATION.one-finite-parent-invocation.v1',
            binding=binding_ref,run_id=v['run_id'],no_retry=True,parent=H.kernel(os.getpid()),readonly_preclock_qualification=qualification)))
        need(not stops,'PRESENTATION_OWNER_STOP_BEFORE_CLOCK');start=time.monotonic()
        clock=dict(schema='frw.Root.PRESENTATION.finite-operation-clock.v1',status='ROOT_BOUND_FUTURE_OPERATION',run_id=v['run_id'],
            scenario_sha256=phase['scenario_sha256'],timing=TIMING,started_monotonic=start,deadline_monotonic=start+600,
            old_effects_clocks_preserved=True)
        clock_ref=H.new(work/'ROOT-ORIGINAL-OUTER600-CLOCK.json',encoded(clock))
        cleanup_ref=H.new(work/'ROOT-OWNED-PARENT-WAIT-CLEANUP.json',encoded(dict(schema='frw.Root.PRESENTATION.owned-consumer-wait-cleanup.v1',
            run_id=v['run_id'],clock=clock_ref,outer_seconds=600,reserve_seconds=5,wait_same_owned_child=True,reap_before_release=True,
            no_detached_writer_or_retry=True,implementation=v['driver'],aggregate_disk_scope=v['disk_scope'])))
        parent=H.kernel(os.getpid());argv=[PYTHON,'-I','-B','-S',str(Path(__file__).absolute()),'--owned-consumer',binding_ref['path'],
            binding_ref['sha256'],str(slot),str(parent['pid']),str(parent['start_time']),parent['boot_id'],
            '--clock',clock_ref['path'],clock_ref['sha256'],cleanup_ref['path'],cleanup_ref['sha256']]
        with os.fdopen(os.open(work/'CONSUMER.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as out,\
             os.fdopen(os.open(work/'CONSUMER.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as err:
            need(not stops,'PRESENTATION_OWNER_STOP_BEFORE_BIRTH')
            actor=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(slot,))
            try:
                forward();ident=H.kernel(actor.pid) if actor.poll() is None else dict(pid=actor.pid,already_exited=True)
                H.new(work/'ROOT-OWNED-ACTOR.json',encoded(dict(identity=ident,parent=parent,clock=clock_ref)))
                result=H.wait_owned(actor,clock,v['disk_scope'],baseline,v['resources']['disk_bytes'],stops,lifetime);wait_done=True
            finally:
                if not wait_done and actor.poll() is None and not lifetime['cleanup_attempted']:H.stop_reap(actor,clock,[],lifetime)
        result.update(schema='frw.Root.PRESENTATION.finite-consumer-ended.v1',run_id=v['run_id'],parent_stops=stops,
            at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),elapsed_seconds=time.monotonic()-start,
            owned_child_reaped=actor.poll() is not None,operation_clock=clock_ref,acceptance='NOT_ESTABLISHED',no_retry=True,
            next_action='Root reconcile/assess same saved actual file only; no automatic retry or successor')
        H.new(work/'ROOT-DISPATCH-ENDED.json',encoded(result));return result
    except H.StopUnconfirmed:
        H.new(work/'ROOT-STOP-UNCONFIRMED.json',encoded(dict(state='STOP_UNCONFIRMED',actor_pid=actor.pid,
            original_clock=clock,shared_slot_inherited_by_child=True,no_retry=True)));raise
    finally:
        try:
            if actor is not None and actor.poll() is None and clock is not None and not wait_done and not lifetime['cleanup_attempted']:
                H.stop_reap(actor,clock,[],lifetime)
        finally:
            for s,h in previous.items():signal.signal(s,h)
            os.close(slot)


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv;os.umask(0o077)
    need(len(args) in (3,12) and args[0] in ('--readonly-before-clock','--execute-once','--owned-consumer'),
         'PRESENTATION_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED')
    H=read_shared();v,ref=H.exact_file(args[1],args[2]);validate(v,H)
    # Apply actual finite preparation/parent limits, not a document-only budget.
    # The owned tester consumer applies its own same limits before source reads.
    H.child_limits(v['resources'])
    old_alarm=None
    if args[0]!='--owned-consumer':
        def preparation_expired(_sig,_frame):raise TimeoutError('PRESENTATION_PRECLAIM_PREPARATION_WALL_EXPIRED')
        old_alarm=signal.signal(signal.SIGALRM,preparation_expired)
        signal.setitimer(signal.ITIMER_REAL,PREPARATION_WALL_SECONDS)
    if len(args)==3 and args[0]=='--readonly-before-clock':
        try:print(json.dumps(readonly(v,H),sort_keys=True));return 0
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_alarm)
    if len(args)==3 and args[0]=='--execute-once':
        try:print(json.dumps(execute(v,H,binding_ref=ref),sort_keys=True));return 0
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_alarm)
    if len(args)==12 and args[0]=='--owned-consumer' and args[7]=='--clock':
        clock,clock_ref=H.exact_file(args[8],args[9]);cleanup,cleanup_ref=H.exact_file(args[10],args[11])
        return owned_consumer(v,H,ref,clock_ref,cleanup_ref,int(args[3]),
            dict(pid=int(args[4]),start_time=int(args[5]),boot_id=args[6]))
    raise ValueError('PRESENTATION_EXACT_SINGLE_OPERATION_COMMAND_REQUIRED')


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        # Existing consumer retains its raw facts privately. Driver emits only
        # exception type, never an HTTP URL, credential, raw args or body.
        print(json.dumps(dict(state='REFUSED_INTERRUPTED_OR_UNKNOWN',exception_class=type(exc).__name__,
            no_retry=True,semantic='NOT_ESTABLISHED')),file=sys.stderr)
        sys.exit(1)
