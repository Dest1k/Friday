"""Inert finite Root caller for the FIRST original F07 ordinary phase.

SOURCE ONLY. Import, inspect and pure validation issue no authority or effects.
Only an explicit --execute-once command on a separately Root-bound input starts
one owned consumer. No issuer, context fabrication, retry, resume or grader.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time
import types

STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
PYTHON = '/home/jericho/jericho/.venv/bin/python'
SELECTED_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
TIMING = dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=30,reserve_seconds=5,outer_seconds=600)
MAX_REF = 24*1024**2
PROJECTION_LIMIT = 'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED'
ROOT_ASSERTIONS = ('original_phase_effect_eligible','old_effects_UNKNOWN_clocks_preserved',
    'all_profile_semantic_unlogged_equivalents_reconciled','root_current_pending_approval_cancel_maintenance_assessed')
PRIVACY_ASSERTIONS = ('source_metadata_only_checked','raw_user_retention_separately_scoped')
INPUT_KEYS = {'schema','status','operator','run_id','workdir','driver','source_review','checker','root_caller',
    'selected_tester','saved_phase_preflight','scenario','authority','installation_closure','source_acceptance',
    'Root_acceptance','resources','slot_identity','disk_scope'}


def need(ok,code):
    if not ok: raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    out={}
    for key,value in pairs:
        need(key not in out,'F07_DUPLICATE_JSON_KEY');out[key]=value
    return out


def parse(raw): return json.loads(raw,object_pairs_hook=unique)


def canonical_path(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and str(Path(value))==value and all(p not in ('','.','..') for p in value.split('/')[1:])
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value),'F07_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    value.encode('utf-8'); return Path(value)


def identity(s):
    return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def reference_shape(ref):
    return (type(ref) is dict and set(ref)=={'path','bytes','sha256'}
        and canonical_path(ref['path']).is_absolute() and type(ref['bytes']) is int and 0<ref['bytes']<=MAX_REF
        and type(ref['sha256']) is str and re.fullmatch('[a-f0-9]{64}',ref['sha256']) is not None)


def read(path,*,limit,private=True):
    path=canonical_path(str(path));need(not any(p.is_symlink() for p in (path,*path.parents)),'F07_INPUT_LINK')
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        before=os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and not stat.S_IMODE(before.st_mode)&0o002 and (not private or stat.S_IMODE(before.st_mode)==0o600),'F07_UNSAFE_INPUT')
        raw=stream.read(limit+1);after=os.fstat(stream.fileno())
    need(len(raw)<=limit and len(raw)==before.st_size and identity(before)==identity(after)==identity(path.stat()),'F07_CHANGED_OR_OVERSIZE_INPUT')
    return raw


def readref(ref,*,private=True):
    need(reference_shape(ref),'F07_EXACT_SIZED_REFERENCE_REQUIRED')
    raw=read(ref['path'],limit=ref['bytes'],private=private)
    need(len(raw)==ref['bytes'] and digest(raw)==ref['sha256'],'F07_EXACT_PIN_CHANGED');return raw


def doc(ref): return parse(readref(ref))


def fileref(path):
    raw=read(path,limit=MAX_REF);return dict(path=str(path),bytes=len(raw),sha256=digest(raw))


def new(path,raw):
    """No overwrite, one durable file and containing-directory commit."""
    path=canonical_path(str(path));need(not any(p.is_symlink() for p in path.parents),'F07_OUTPUT_PARENT_LINK')
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    return dict(path=str(path),bytes=len(raw),sha256=digest(raw))


def load_raw(raw,path,name):
    value=types.ModuleType(name);value.__file__=str(path)
    exec(compile(raw,str(path),'exec'),value.__dict__);return value


def protected_directory(path):
    path=canonical_path(str(path));info=path.stat()
    need(not any(p.is_symlink() for p in (path,*path.parents)) and stat.S_ISDIR(info.st_mode)
        and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700,'F07_EXISTING_PRIVATE_DIRECTORY_REQUIRED')
    return identity(info)


def kernel(pid):
    raw=Path('/proc')/str(pid)/'stat';fields=raw.read_text().rsplit(')',1)[1].split()
    return dict(pid=int(pid),start_time=int(fields[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def lock_identity(info):
    return dict(device=info.st_dev,inode=info.st_ino,uid=info.st_uid,mode=stat.S_IMODE(info.st_mode),nlink=info.st_nlink)


def safe_lock(path,expected=None):
    need(not any(p.is_symlink() for p in (path,*path.parents)),'F07_LOCK_LINK')
    fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600
             and info.st_nlink==1 and identity(info)==identity(path.stat()),'F07_UNSAFE_NAMED_LOCK')
        need(expected is None or lock_identity(info)==expected,'F07_NAMED_SLOT_CHANGED')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);return fd
    except BaseException:
        os.close(fd);raise


def validate(v):
    """Pure shape checks; defaults, absent Root judgment and other phases fail."""
    need(type(v) is dict and set(v)==INPUT_KEYS and v.get('schema')=='frw.Root.F07.first-phase-finite-driver.v1'
        and v.get('status')=='ROOT_BOUND_ONE_FUTURE_OPERATION' and v.get('operator')=='Root','F07_DRIVER_UNBOUND_NO_EFFECT')
    need(type(v['run_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v['run_id'])
         and v['run_id']!='UNBOUND','F07_EXPLICIT_NEW_RUN_REQUIRED')
    canonical_path(v['workdir'])
    for key in INPUT_KEYS & {'driver','source_review','checker','root_caller','selected_tester','saved_phase_preflight',
                            'scenario','authority','installation_closure','source_acceptance','Root_acceptance'}:
        need(reference_shape(v[key]),'F07_SIZED_ROOT_BINDINGS_REQUIRED')
    r=v['resources']
    need(type(r) is dict and set(r)==set(TIMING)|{'cpu_seconds','max_rss_bytes','disk_bytes'}
         and all(type(r.get(k)) is int and r[k]==n for k,n in TIMING.items())
         and type(r['cpu_seconds']) is int and 0<r['cpu_seconds']<=600
         and type(r['max_rss_bytes']) is int and 0<r['max_rss_bytes']<=2*1024**3
         and type(r['disk_bytes']) is int and 0<r['disk_bytes']<=100*1024**2,'F07_FINITE_IMMUTABLE_RESOURCES_REQUIRED')
    scope=v['disk_scope']
    need(type(scope) is dict and set(scope)=={'directory_roots','file_paths','max_entries','sample_seconds','scope_evidence'}
         and type(scope['directory_roots']) is list and str(STATE) in scope['directory_roots'] and v['workdir'] in scope['directory_roots']
         and type(scope['file_paths']) is list and type(scope['max_entries']) is int and 0<scope['max_entries']<=100000
         and type(scope['sample_seconds']) in (int,float) and math.isfinite(scope['sample_seconds'])
         and 0<scope['sample_seconds']<=1 and type(scope['scope_evidence']) is list and bool(scope['scope_evidence']),
         'F07_EXPLICIT_BOUNDED_OPERATION_WRITE_SCOPE_REQUIRED')
    for paths in (scope['directory_roots'],scope['file_paths']):
        need(paths==sorted(set(paths)),'F07_SORTED_UNIQUE_DISK_SCOPE_REQUIRED')
        for path in paths: canonical_path(path)
    for ref in scope['scope_evidence']: need(reference_shape(ref),'F07_DISK_SCOPE_SOURCE_REQUIRED')
    need(type(v['slot_identity']) is dict and set(v['slot_identity'])=={'device','inode','uid','mode','nlink'},'F07_SLOT_IDENTITY_REQUIRED')
    return True


def accepted_current_facts(checker,observed):
    """Observed facts only. No semantic, eligibility or privacy judgment."""
    return dict(history_sha256=observed['history']['sha256'],custody_sha256=observed['custody']['sha256'],
        native_SQL_boundary_sha256=checker.digest(checker.encoded(dict(native=observed['native'],databases=observed['databases']))),
        runtime_hashes=observed['installed']['runtime_hashes'],profile_configs=observed['profile_configs'],source_stat=observed['source_stat'])


def validate_acceptance(v,a,phase):
    """Root must explicitly supply every assertion; none are filled as PASS."""
    need(type(a) is dict and a.get('schema')=='frw.Root.F07.explicit-preop-decisions.v1'
         and a.get('status')=='ROOT_BOUND_ONE_FUTURE_PHASE' and a.get('operator')=='Root'
         and a.get('run_id')==v['run_id'] and a.get('scenario_sha256')==phase['scenario_sha256']
         and a.get('Root_authorizes_observed_hash_binding_only') is True,'F07_ROOT_DECISIONS_UNBOUND')
    need(a.get('bindings')=={k:v[k] for k in ('driver','source_review','checker','root_caller','selected_tester',
        'saved_phase_preflight','scenario','authority','installation_closure','source_acceptance')},'F07_EXACT_ROOT_ACCEPTED_BINDINGS_REQUIRED')
    decision=a.get('original_phase_decision',{});privacy=a.get('privacy_preflight',{})
    need(all(decision.get(k) is True for k in ROOT_ASSERTIONS)
         and decision.get('equivalent_consumed_phase_effects')==[] and decision.get('projection_limit')==PROJECTION_LIMIT
         and type(decision.get('current_scope_evidence')) is list and bool(decision['current_scope_evidence'])
         and type(a.get('accepted_current_facts')) is dict,'F07_ROOT_ORIGINAL_BROADSCOPE_JUDGMENT_REQUIRED')
    need(all(privacy.get(k) is True for k in PRIVACY_ASSERTIONS)
         and privacy.get('genuine_current_event_observed') is False and privacy.get('runtime_logging_verdict')=='NOT_ESTABLISHED',
         'F07_ROOT_SOURCE_PRIVACY_PREFLIGHT_REQUIRED')
    for key in ('source_evidence','effective_roots_source_basis','effective_product_roots','private_roots'):
        need(type(privacy.get(key)) is list and bool(privacy[key]),'F07_ROOT_SOURCE_EFFECTIVE_PRIVATE_ROOTS_REQUIRED')
    need(a.get('aggregate_disk_monitor_limitations_accepted') is True,'F07_OBSERVED_GROWTH_NOT_QUOTA_ACKNOWLEDGMENT_REQUIRED')
    return True


def source_inputs(v):
    """Pinned SOURCE and explicit Root decisions, before creating a user clock."""
    validate(v)
    own=readref(v['driver']);need(v['driver']['path']==str(Path(__file__).absolute()),'F07_EXACT_EXECUTED_DRIVER_REQUIRED')
    review=doc(v['source_review'])
    need(review.get('decision')=='SOURCE_ONLY_READY_UNBOUND' and review.get('reviewed_source')==v['driver']
         and review.get('open_critical_defects')==[],'F07_INDEPENDENT_EXACT_DRIVER_REVIEW_REQUIRED')
    caller=load_raw(readref(v['root_caller']),v['root_caller']['path'],'_Root_F07_caller')
    checker=caller.load_checker(v['checker'],readref)
    base=readref(v['selected_tester'],private=False)
    need(digest(base)==SELECTED_SHA and v['selected_tester']['path']==checker.module(checker.PREP).SELECTED_TESTER,
         'F07_GENUINE_SELECTED_CC36_REQUIRED')
    saved=doc(v['saved_phase_preflight']);phase=saved['result']['phases'][0]
    need(phase['ordinal']==1 and phase['phase']=='NO_EXTENSION'
         and phase==checker.module(checker.PREP).phase_preparation(1,phase['scenario']['steps'][0]['input'])
         and readref(v['scenario'])==checker.encoded(phase['scenario']),'F07_EXACT_SAVED_FIRST_PHASE_REQUIRED')
    authority=doc(v['authority']);ordinary=checker.module(checker.PREP).compose_source(base,phase,run_id=v['run_id'],
        authority_ref=v['authority'],authority=authority,previous_phase=None)
    acceptance=doc(v['Root_acceptance']);validate_acceptance(v,acceptance,phase)
    privacy=acceptance['privacy_preflight'];roots=privacy['effective_product_roots'];private=privacy['private_roots']
    need(roots==sorted(set(roots)) and str(checker.H) in roots and private==sorted(set(private)),
         'F07_EXPLICIT_SORTED_EFFECTIVE_AND_PRIVATE_ROOTS_REQUIRED')
    products=[canonical_path(p) for p in roots];protected=[canonical_path(p) for p in private]
    for path in protected:
        protected_directory(path)
        need(all(not path.is_relative_to(root) and not root.is_relative_to(path) for root in products),'F07_PRIVATE_ROOT_INTERSECTS_PRODUCT')
    materials=[v[k]['path'] for k in ('driver','source_review','checker','root_caller','saved_phase_preflight','scenario',
        'authority','installation_closure','source_acceptance','Root_acceptance')]
    materials += [v['workdir'],phase['scenario']['steps'][0]['input']['path']]
    need(all(any(canonical_path(p).is_relative_to(root) for root in protected) for p in materials),'F07_PRIVATE_DRIVER_MATERIAL_COVERAGE_REQUIRED')
    # Scope comes from existing write-consumer evidence. Full product/source
    # traversal would be an unrelated inventory and is explicitly refused.
    for path in v['disk_scope']['directory_roots']:
        p=canonical_path(path)
        need(not checker.H.is_relative_to(p) and not (checker.H/'hermes-agent').is_relative_to(p),
             'F07_BULK_PRODUCT_SOURCE_DISK_SCAN_REFUSED')
    for ref in (acceptance['original_phase_decision']['current_scope_evidence']
                + acceptance['privacy_preflight']['source_evidence']+acceptance['privacy_preflight']['effective_roots_source_basis']
                + v['disk_scope']['scope_evidence']): readref(ref)
    protected_directory(v['workdir'])
    need(not (STATE/'runs'/(v['run_id']+'.json')).exists(),'F07_NO_EXISTING_RUN_REPLAY')
    return caller,checker,base,phase,authority,ordinary,acceptance


def bind_decisions(v,acceptance,checker,effect,observed):
    """Copy Root's judgments; derive only exact current data joins and hashes."""
    need(accepted_current_facts(checker,observed)==acceptance['accepted_current_facts'],
         'F07_ROOT_REVIEWED_CURRENT_BASIS_CHANGED_RECONCILE_ONLY')
    decision=dict(acceptance['original_phase_decision'],schema='frw.Root.F07.current209-original-case-decision.v1',
        operator='Root',status='ROOT_BOUND',whole_effect_sha256=checker.digest(checker.encoded(effect)),
        history_sha256=observed['history']['sha256'],custody_sha256=observed['custody']['sha256'],
        native_SQL_boundary_sha256=accepted_current_facts(checker,observed)['native_SQL_boundary_sha256'],
        explicit_Root_acceptance=v['Root_acceptance'])
    privacy=dict(acceptance['privacy_preflight'],schema='frw.Root.F07.current209-privacy-preflight.v1',operator='Root',
        status='ROOT_BOUND_PREFLIGHT_NOT_RUNTIME_VERDICT',whole_effect_sha256=checker.digest(checker.encoded(effect)),
        runtime_hashes=observed['installed']['runtime_hashes'],logging_sites=list(checker.LOGGING_SITES),
        technical_log_cursor=observed['technical_log_cursor'],postcondition_plan=checker.postcondition_plan(effect,observed),
        effective_roots_profile_config_refs=observed['profile_configs'],explicit_Root_acceptance=v['Root_acceptance'])
    return decision,privacy


DISK_MONITOR_ENUMS = ('F07_DISK_SCAN_OUTER_DEADLINE','F07_DISK_SCOPE_ENTRY_BOUND',
    'F07_OPERATION_WRITE_SCOPE_LINK_RECONCILE_ONLY','F07_WRITE_SCOPE_SPECIAL_FILE',
    'F07_CANONICAL_ABSOLUTE_PATH_REQUIRED')
DISK_MONITOR_STAGES = ('SCAN_START','SCAN_ENTRY_DEADLINE','SCAN_ENTRY_BOUND','SCAN_ENTRY_LSTAT',
    'SCAN_ENTRY_LINK_GUARD','SCAN_ENTRY_REGULAR_SIZE','SCAN_DIRECTORY_OPEN','SCAN_DIRECTORY_NEXT',
    'SCAN_ENTRY_TYPE_GUARD','SCAN_ROOT_CANONICAL_PATH','CHARGE_GROWTH','SAMPLE_UPDATE','MONITOR_BLOCK')


def disk_monitor_failure(exc,*,stage,path=None,entries=None):
    """Bounded protected metadata only; no exception message/args or file body."""
    classes=(ValueError,PermissionError,FileNotFoundError,NotADirectoryError,IsADirectoryError,
        OSError,RecursionError,RuntimeError,OverflowError,MemoryError,TypeError)
    kind=type(exc);name=kind.__name__ if kind in classes else 'OTHER_EXCEPTION'
    code='F07_DISK_MONITOR_UNCLASSIFIED_EXCEPTION'
    if kind is ValueError and len(exc.args)==1 and type(exc.args[0]) is str and exc.args[0] in DISK_MONITOR_ENUMS:
        code=exc.args[0]
    number=None
    if kind in (PermissionError,FileNotFoundError,NotADirectoryError,IsADirectoryError,OSError):
        code='F07_DISK_MONITOR_OS_ERROR'
        value=exc.errno
        if type(value) is int and -4095<=value<=4095:number=value
    text=str(path) if isinstance(path,Path) else path if type(path) is str else None
    size=len(text) if text is not None else None
    return dict(exception_class=name,enum=code,errno=number,
        stage=stage if stage in DISK_MONITOR_STAGES else 'MONITOR_BLOCK',
        path=text if text is not None and len(text)<=4096 else None,
        path_status='RECORDED' if text is not None and len(text)<=4096 else 'OMITTED_OVER_BOUND' if text is not None else 'NOT_APPLICABLE',
        path_chars=size,entries=entries if type(entries) is int and 0<=entries<=100001 else None)


def scan_scope(scope,*,deadline,failure=None):
    """Finite scoped metadata scan, no bulk H/source traversal or content read."""
    rows={};visited=set();count=0
    stage='SCAN_START';active_path=None
    def entry(path,recurse):
        nonlocal count,stage,active_path
        stage='SCAN_ENTRY_DEADLINE';active_path=path
        need(time.monotonic()<deadline,'F07_DISK_SCAN_OUTER_DEADLINE')
        text=str(path)
        if text in visited:return
        visited.add(text);count+=1;stage='SCAN_ENTRY_BOUND'
        need(count<=scope['max_entries'],'F07_DISK_SCOPE_ENTRY_BOUND')
        stage='SCAN_ENTRY_LSTAT'
        try:info=path.lstat()
        except FileNotFoundError:return
        stage='SCAN_ENTRY_LINK_GUARD'
        need(not stat.S_ISLNK(info.st_mode),'F07_OPERATION_WRITE_SCOPE_LINK_RECONCILE_ONLY')
        if stat.S_ISREG(info.st_mode):
            stage='SCAN_ENTRY_REGULAR_SIZE'
            rows[(info.st_dev,info.st_ino)]=max(rows.get((info.st_dev,info.st_ino),0),info.st_size)
        elif stat.S_ISDIR(info.st_mode) and recurse:
            stage='SCAN_DIRECTORY_OPEN'
            with os.scandir(path) as children:
                stage='SCAN_DIRECTORY_NEXT'
                for child in children:
                    entry(Path(child.path),True)
                    stage='SCAN_DIRECTORY_NEXT';active_path=path
        else:
            stage='SCAN_ENTRY_TYPE_GUARD'
            need(stat.S_ISDIR(info.st_mode),'F07_WRITE_SCOPE_SPECIAL_FILE')
    try:
        for path in scope['directory_roots']:
            stage='SCAN_ROOT_CANONICAL_PATH';active_path=path
            entry(canonical_path(path),True)
        for path in scope['file_paths']:
            stage='SCAN_ROOT_CANONICAL_PATH';active_path=path
            entry(canonical_path(path),False)
    except Exception as exc:
        if failure is not None:failure.update(disk_monitor_failure(exc,stage=stage,path=active_path,entries=count))
        raise
    return rows


def charge_growth(baseline,current,highwater):
    for key,size in current.items():highwater[key]=max(highwater.get(key,0),max(0,size-baseline.get(key,0)))
    return sum(highwater.values())


class StopUnconfirmed(RuntimeError): pass


def remaining(clock): return max(0.0,clock['deadline_monotonic']-time.monotonic())


def stop_reap(actor,clock,signals,lifetime=None):
    """Only this Popen child; no group/global kill and no fresh cleanup clock."""
    if lifetime is not None:lifetime['cleanup_attempted']=True
    for sig,parts in ((signal.SIGINT,3),(signal.SIGTERM,2),(signal.SIGKILL,1)):
        if actor.poll() is not None:return actor.wait(timeout=0)
        try:actor.send_signal(sig);signals.append(int(sig))
        except ProcessLookupError:pass
        left=remaining(clock)
        if left:
            try:return actor.wait(timeout=left/parts)
            except subprocess.TimeoutExpired:pass
    if actor.poll() is not None:return actor.wait(timeout=0)
    raise StopUnconfirmed('F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED')


def wait_owned(actor,clock,scope,baseline,disk_bytes,stops,lifetime=None):
    highwater={};samples=0;largest=0;reason=None;signals=[]
    monitor_failure=None;final_monitor_failure=None
    while actor.poll() is None:
        if stops:reason='PARENT_STOP_REQUEST';break
        if remaining(clock)<=5:reason='ORIGINAL_OUTER_CLEANUP_RESERVE';break
        failure={};stage='MONITOR_BLOCK'
        try:
            current=scan_scope(scope,deadline=clock['deadline_monotonic']-5,failure=failure)
            stage='CHARGE_GROWTH';charged=charge_growth(baseline,current,highwater)
            stage='SAMPLE_UPDATE'
            samples+=1;largest=max(largest,charged)
            if charged>=disk_bytes:reason='OBSERVED_AGGREGATE_NEW_DISK_BOUND';break
        except Exception as exc:
            monitor_failure=failure or disk_monitor_failure(exc,stage=stage)
            reason='AGGREGATE_DISK_MONITOR_REFUSED';break
        try:actor.wait(timeout=min(scope['sample_seconds'],max(0.001,remaining(clock)-5)))
        except subprocess.TimeoutExpired:pass
    code=stop_reap(actor,clock,signals,lifetime) if actor.poll() is None else actor.wait(timeout=0)
    # Preserve a final sample when possible, including the just-exited process's
    # carriers. This never consumes a replacement or extended operation clock.
    failure={};stage='MONITOR_BLOCK'
    try:
        current=scan_scope(scope,deadline=clock['deadline_monotonic'],failure=failure)
        stage='CHARGE_GROWTH';charged=charge_growth(baseline,current,highwater)
        stage='SAMPLE_UPDATE';largest=max(largest,charged);samples+=1
        if largest>=disk_bytes and reason is None:reason='OBSERVED_DISK_BOUND_AT_EXIT'
    except Exception as exc:
        final_monitor_failure=failure or disk_monitor_failure(exc,stage=stage)
        if reason is None:reason='FINAL_DISK_SAMPLE_NOT_ESTABLISHED'
    return dict(exit_code=code,stop_reason=reason,cleanup_signals=signals,samples=samples,
        observed_new_bytes_highwater=largest,aggregate_cap_bytes=disk_bytes,
        accounting='SUM_PER_INODE_OBSERVED_POSITIVE_GROWTH_HIGHWATER',hard_filesystem_quota=False,
        monitor_failure=monitor_failure,final_monitor_failure=final_monitor_failure,
        limitations=['between-sample transient files/growth can be missed','gateway external growth outside declared roots is unbounded',
                    'stop targets owned tester consumer; product host lifetime is separately owned'])


def child_limits(resources):
    for label,key in ((resource.RLIMIT_CPU,'cpu_seconds'),(resource.RLIMIT_AS,'max_rss_bytes'),(resource.RLIMIT_FSIZE,'disk_bytes')):
        resource.setrlimit(label,(resources[key],resources[key]))


def owned_consumer(v,binding_ref,clock_ref,cleanup_ref,slot_fd,parent_identity):
    """One real locked consumer. Called only by its finite owning parent."""
    child_limits(v['resources'])
    caller,checker,base,phase,authority,ordinary,acceptance=source_inputs(v)
    need(os.getppid()==parent_identity['pid'] and kernel(os.getppid())==parent_identity,'F07_OWNED_PARENT_CHANGED')
    need(lock_identity(os.fstat(slot_fd))==v['slot_identity'],'F07_INHERITED_SLOT_CHANGED')
    checker.lock_held(SLOT,parent_identity)
    work=Path(v['workdir']);clock=doc(clock_ref)
    need(clock['run_id']==v['run_id'] and clock['deadline_monotonic']-clock['started_monotonic']==600
         and time.monotonic()+305<clock['deadline_monotonic'],'F07_ORIGINAL_CLOCK_TOO_SHORT_BEFORE_NEW')
    r=dict(v['resources'],clock=clock_ref,owned_parent_wait_cleanup=cleanup_ref)
    effect=caller.assemble_effect(checker,phase=phase,run_id=v['run_id'],authority_ref=v['authority'],scenario_ref=v['scenario'],
        checker_ref=v['checker'],closure_ref=v['installation_closure'],acceptance_ref=v['source_acceptance'],resources=r)
    # Load the unmodified genuine selected ordinary composition. Its existing
    # Store validates pre-existing protected dirs; no alternate state is allowed.
    ordinary_path=work/'selected-ordinary-source.py';new(ordinary_path,ordinary)
    genuine=load_raw(ordinary,ordinary_path,'_Root_F07_genuine_ordinary')
    paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads']
    before={str(p):protected_directory(p) for p in paths};store=genuine.Store(STATE)
    need({str(p):protected_directory(p) for p in paths}==before,'F07_STORE_CONSTRUCTOR_MUTATED_DIRS')
    with store.lock(create=False) as consumer_fd,store.lock(STATE/'tester-token',create=False) as credential_fd:
        me=kernel(os.getpid());checker.lock_held(STATE/'consumer.lock',me);checker.lock_held(STATE/'tester-token',me)
        invocation_ref=new(work/'ROOT-ONCE-CONSUMER-INVOCATION.json',encoded(dict(
            schema='frw.Root.F07.one-ordinary-consumer-invocation.v1',run_id=v['run_id'],
            whole_effect_sha256=checker.digest(checker.encoded(effect)),clock=clock_ref,no_retry=True,consumer=me,
            driver_binding=binding_ref)))
        qualified=caller.qualify_selected_ordinary_readonly(genuine.Runner(store,None),run_id=v['run_id'],phase=phase)
        new(work/'SELECTED-ORDINARY-READONLY.json',encoded(qualified))
        observed=checker.observe(effect,stage='BASELINE')
        decision,privacy=bind_decisions(v,acceptance,checker,effect,observed)
        decision_ref=new(work/'ROOT-ORIGINAL-CASE-DECISION.json',checker.encoded(decision))
        privacy_ref=new(work/'ROOT-PRIVACY-PREFLIGHT.json',checker.encoded(privacy))
        wall,mono=time.time(),time.monotonic()
        proof=caller.assemble_root_proof(checker,effect=effect,observed=observed,created_at=wall,expires_at=wall+120,
            created_monotonic=mono,expires_monotonic=mono+120,boot_id=me['boot_id'],
            lock_owners=dict(shared_slot=parent_identity,consumer=me,credential=me),invocation_ref=invocation_ref,
            Root_decision_ref=decision_ref,privacy_preflight_ref=privacy_ref)
        proof_ref=new(work/'ROOT-FRESH-CURRENT209-PROOF.json',checker.encoded(proof))
        # Execute privacy decisions BEFORE creating any run or reading the token.
        checker.decisions(proof,observed,proof_ref);checker.fresh(proof)
        candidate=caller.compose_consumer(checker,base,effect=effect,authority=authority,proof_ref=proof_ref,previous_phase=None)
        candidate_ref=new(work/'bot_tester.f07.current209.py',candidate)
        module=load_raw(readref(candidate_ref),candidate_ref['path'],'_Root_F07_actual_consumer')
        new(work/'ROOT-ACTUAL-EFFECT-AND-CONSUMER.json',checker.encoded(dict(effect=effect,proof=proof_ref,
            candidate=candidate_ref,acceptance='NOT_ESTABLISHED',semantic='NOT_RUN')))
        # The genuine route and original send durability/ACK/capture/error paths
        # are preserved. No main()/resume path is used and no retry is possible.
        api=module.BotAPI(module.safe_read(STATE/'tester-token',256).decode('ascii').strip())
        runner=module.Runner(store,api);run=None;stage='NEW'
        try:
            run=runner.new(v['run_id'],phase['scenario'])
            stage='SEND';runner.send(run,consumer_fd=consumer_fd,credential_fd=credential_fd)
            stage='OBSERVE';runner.observe(run)
        except BaseException as exc:
            # The existing sender saves protected technical prewire diagnostics.
            # Never serialize exception messages, HTTP URLs or user contents.
            new(work/'CONSUMER-RAW-FAILURE.json',encoded(dict(status='REFUSED_INTERRUPTED_OR_UNKNOWN',phase=stage,
                exception_class=type(exc).__name__,frames=enum_failure_frames(exc,stage),no_retry=True,
                product_cancelled=False,semantic='NOT_ESTABLISHED')))
            raise
        finally:
            path=STATE/'runs'/(v['run_id']+'.json')
            run_ref=fileref(path) if path.exists() else None
            new(work/'CONSUMER-RAW-CLOSURE.json',encoded(dict(run_id=v['run_id'],canonical_run=run_ref,
                stage=stage,raw_status=run.get('status') if run is not None else None,
                raw_send_state=run.get('send_state') if run is not None else None,
                capture_window_complete=run.get('capture_window_complete') if run is not None else None,
                acceptance='NOT_ESTABLISHED',semantic='NOT_ESTABLISHED',privacy='NOT_ESTABLISHED',
                custody='NOT_ESTABLISHED',native_host_close='NOT_ESTABLISHED',no_retry=True)))
    return 0


def qualify_before_clock(v,caller,checker,ordinary,phase):
    """ROOT ONLY read-only actual history call. No file/claim/clock/API creation.

    Caller holds the shared slot; take existing consumer+credential locks without
    creating them. Store construction is allowed only for pre-existing checked
    directories and must preserve their exact metadata. No child invokes this on
    actual inputs. Refusal propagates before spending a new operation lifecycle.
    """
    genuine=load_raw(ordinary,v['selected_tester']['path'],'_Root_F07_preclock_ordinary')
    paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads']
    before={str(p):protected_directory(p) for p in paths};store=genuine.Store(STATE)
    need({str(p):protected_directory(p) for p in paths}==before,'F07_STORE_CONSTRUCTOR_MUTATED_DIRS')
    with store.lock(create=False),store.lock(STATE/'tester-token',create=False):
        me=kernel(os.getpid())
        checker.lock_held(SLOT,me);checker.lock_held(STATE/'consumer.lock',me);checker.lock_held(STATE/'tester-token',me)
        return caller.qualify_selected_ordinary_readonly(genuine.Runner(store,None),run_id=v['run_id'],phase=phase)


DIAGNOSTIC_PHASES=('NEW','SEND','OBSERVE')
DIAGNOSTIC_CALLS=('new','validate_scenario','cursor_offsets','receive_inventory','legacy_receive_inventory',
    'b00_closed_partial_history','_f07_exact_history_row','ordinary_independent_admission',
    'ordinary_independent_history_row','ordinary_independent_current_rows','ordinary_independent_predecessor_checked',
    'verify_reply_custody','check_reply_text_receipt','verify_capture_context','verify_window',
    'a02_terminal_partial','s05_settled_partial','m03_stopped1754_history','settings_stopped1667_history',
    'm12_r02_local_history','w03_stopped_local_history','check','decisions','send','_send','observe')


def enum_failure_frames(exc,stage):
    """No paths, dynamic names, exception text, locals or user payloads."""
    need(stage in DIAGNOSTIC_PHASES,'F07_ENUM_DIAGNOSTIC_PHASE_REQUIRED')
    frames=[];tb=exc.__traceback__
    while tb is not None:
        name=tb.tb_frame.f_code.co_name
        if name in DIAGNOSTIC_CALLS and len(frames)<24:
            frames.append(dict(call=name,line=tb.tb_lineno))
        tb=tb.tb_next
    return frames


def execute(v,*,binding_ref):
    caller,checker,base,phase,authority,ordinary,acceptance=source_inputs(v)
    need(any(canonical_path(binding_ref['path']).is_relative_to(canonical_path(p))
             for p in acceptance['privacy_preflight']['private_roots']),'F07_PRIVATE_ROOT_BINDING_COVERAGE_REQUIRED')
    work=Path(v['workdir']);need(not list(work.iterdir()),'F07_FRESH_EMPTY_OPERATION_WORKDIR_REQUIRED')
    slot_fd=safe_lock(SLOT,v['slot_identity']);actor=None;clock=None;stops=[];wait_done=False;result=None;forwarded=0;draining=False
    lifetime=dict(cleanup_attempted=False)
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def forward_stops():
        nonlocal forwarded,draining
        if draining:return
        draining=True
        try:
            while actor is not None and forwarded<len(stops):
                sig=stops[forwarded];forwarded+=1
                if actor.poll() is None:
                    try:actor.send_signal(sig)
                    except ProcessLookupError:pass
        finally:
            draining=False
            if actor is not None and forwarded<len(stops):forward_stops()
    def requested(sig,_frame):
        stops.append(int(sig))
        forward_stops()
    try:
        for sig in previous:signal.signal(sig,requested)
        readonly_qualification=qualify_before_clock(v,caller,checker,ordinary,phase)
        baseline=scan_scope(v['disk_scope'],deadline=time.monotonic()+30)
        # One claim before the sole clock: any later refusal/UNKNOWN consumes it.
        new(work/'ROOT-ONCE-DRIVER-INVOCATION.json',encoded(dict(schema='frw.Root.F07.one-finite-parent-invocation.v1',
            binding=binding_ref,run_id=v['run_id'],no_retry=True,parent=kernel(os.getpid()),
            readonly_preclock_qualification=readonly_qualification)))
        need(not stops,'F07_OWNER_STOP_BEFORE_CLOCK')
        start=time.monotonic()
        clock=dict(schema='frw.Root.F07.finite-operation-clock.v1',status='ROOT_BOUND_FUTURE_OPERATION',
            run_id=v['run_id'],scenario_sha256=phase['scenario_sha256'],timing=TIMING,
            started_monotonic=start,deadline_monotonic=start+600,old_effects_clocks_preserved=True)
        clock_ref=new(work/'ROOT-ORIGINAL-OUTER600-CLOCK.json',encoded(clock))
        cleanup_ref=new(work/'ROOT-OWNED-PARENT-WAIT-CLEANUP.json',encoded(dict(
            schema='frw.Root.F07.owned-consumer-wait-cleanup.v1',run_id=v['run_id'],clock=clock_ref,
            outer_seconds=600,reserve_seconds=5,wait_same_owned_child=True,reap_before_release=True,
            no_detached_writer_or_retry=True,implementation=v['driver'],aggregate_disk_scope=v['disk_scope'])))
        parent_identity=kernel(os.getpid())
        argv=[PYTHON,'-I','-B','-S',str(Path(__file__).absolute()),'--owned-consumer',binding_ref['path'],binding_ref['sha256'],
            str(slot_fd),str(parent_identity['pid']),str(parent_identity['start_time']),parent_identity['boot_id'],
            '--clock',clock_ref['path'],clock_ref['sha256'],cleanup_ref['path'],cleanup_ref['sha256']]
        with os.fdopen(os.open(work/'CONSUMER.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as out,\
             os.fdopen(os.open(work/'CONSUMER.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as err:
            need(not stops,'F07_OWNER_STOP_BEFORE_BIRTH')
            actor=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(slot_fd,))
            try:
                # A signal between Popen and assignment is recorded and forwarded.
                forward_stops()
                actor_identity=kernel(actor.pid) if actor.poll() is None else dict(pid=actor.pid,already_exited=True)
                new(work/'ROOT-OWNED-ACTOR.json',encoded(dict(identity=actor_identity,parent=parent_identity,clock=clock_ref)))
                result=wait_owned(actor,clock,v['disk_scope'],baseline,v['resources']['disk_bytes'],stops,lifetime)
                wait_done=True
            finally:
                if not wait_done and actor.poll() is None and not lifetime['cleanup_attempted']:stop_reap(actor,clock,[],lifetime)
        result.update(schema='frw.Root.F07.finite-consumer-ended.v1',run_id=v['run_id'],
            parent_stops=stops,at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),
            elapsed_seconds=time.monotonic()-start,owned_child_reaped=actor.poll() is not None,
            operation_clock=clock_ref,acceptance='NOT_ESTABLISHED',no_retry=True,
            next_action='Root reconcile/assess saved actual evidence only; no successor or replay admitted')
        new(work/'ROOT-DISPATCH-ENDED.json',encoded(result));return result
    except StopUnconfirmed:
        new(work/'ROOT-STOP-UNCONFIRMED.json',encoded(dict(state='STOP_UNCONFIRMED',actor_pid=actor.pid,
            original_clock=clock,shared_slot_inherited_by_child=True,no_retry=True)))
        raise
    finally:
        try:
            # Catch exceptions even during Popen-return/actor bookkeeping.
            if actor is not None and actor.poll() is None and clock is not None and not wait_done and not lifetime['cleanup_attempted']:
                stop_reap(actor,clock,[],lifetime)
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
            os.close(slot_fd)


def exact_file(path,sha):
    raw=read(canonical_path(path),limit=MAX_REF);need(digest(raw)==sha,'F07_COMMAND_PIN_CHANGED')
    return parse(raw),dict(path=path,bytes=len(raw),sha256=sha)


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv;os.umask(0o077)
    if len(args)==3 and args[0]=='--execute-once':
        value,reference=exact_file(args[1],args[2]);validate(value)
        result=execute(value,binding_ref=reference);print(json.dumps(result,sort_keys=True));return 0
    if len(args)==12 and args[0]=='--owned-consumer':
        value,reference=exact_file(args[1],args[2]);validate(value)
        clock,clock_ref=exact_file(args[8],args[9]);cleanup,cleanup_ref=exact_file(args[10],args[11])
        parent=dict(pid=int(args[4]),start_time=int(args[5]),boot_id=args[6])
        # argv positions are deliberately explicit and checked by pure controls.
        need(args[7]=='--clock','F07_OWNED_CHILD_EXACT_ARGUMENTS_REQUIRED')
        return owned_consumer(value,reference,clock_ref,cleanup_ref,int(args[3]),parent)
    raise ValueError('F07_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED')


if __name__=='__main__':
    try:raise SystemExit(main())
    except (Exception,KeyboardInterrupt) as exc:
        # Private raw tester carriers contain details. Never leak exception text.
        print(json.dumps(dict(status='REFUSED_INTERRUPTED_OR_UNKNOWN',exception_class=type(exc).__name__,no_retry=True,
            product_cancelled=False,acceptance='NOT_ESTABLISHED')),file=sys.stderr);raise SystemExit(2)
