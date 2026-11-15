"""Sole ordinary namespace PID1; no independent outer runner or authority.

All startup, native/helper/UNO work, one-store completion and cleanup share the
original absolute child deadline. Only managed fixed code runs; imports do not
launch Office, GDB, UNO or a namespace.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import time

from . import friday_workspace_calc_native_factory as factory
from . import friday_workspace_calc_native_layout as layout
from . import friday_workspace_calc_native_observer as observer
from . import friday_workspace_calc_measured as measured

WORK=Path(factory.WORK)
CODE=WORK/'code'
PROGRAM=factory.PROGRAM
TARGET_SHA256='d45b782714fd82ee901f577241abe1d023884c97843d8e019d30396cb9979518'
CLEANUP_RESERVE=1.0  # inside original child35, never appended to it


def need(value,code): factory.need(value,code)


def _check(job,*,cleanup=False):
    end=job['deadline'] if cleanup else job['deadline']-CLEANUP_RESERVE
    need(job['started_monotonic']<=time.monotonic()<end,'ordinary_supervisor_original_deadline')
    need(not os.path.lexists(WORK/'ordinary-cancel'),'ordinary_supervisor_cancelled')


def _asset(job,relative):
    rows=[r for r in job['files'] if r[0]==relative]
    need(len(rows)==1,'ordinary_supervisor_missing_indexed_asset')
    path=CODE/layout.safe_relative(relative)
    need(len(layout.read_exact_file(path,rows[0][1]))==rows[0][2],
         'ordinary_supervisor_asset_hash_or_size')
    return dict(path=str(path),sha256=rows[0][1])


def load_job():
    raw=factory._read(WORK/'ordinary-job.json',262144);job=factory.decode(raw)
    need(type(job) is dict and set(job)=={'schema','nonce','source_sha256','source_bytes',
         'started_monotonic','parent_deadline','deadline','generation_index_sha256','entry','files'}
         and job['schema']=='frw.ordinary-calc.native-job.v1','ordinary_supervisor_job_schema')
    need(type(job['nonce']) is str and re.fullmatch('[0-9a-f]{32}',job['nonce'])
         and factory._sha(job['source_sha256']) and factory._sha(job['generation_index_sha256'])
         and type(job['source_bytes']) is int and 0<job['source_bytes']<=1000000,
         'ordinary_supervisor_job_identity')
    need(all(type(job[k]) in (int,float) and math.isfinite(job[k]) for k in
         ('started_monotonic','deadline','parent_deadline'))
         and job['deadline']<=min(job['parent_deadline'],job['started_monotonic']+35),
         'ordinary_supervisor_original35')
    _check(job)
    need(job['entry']=='ordinary_entry.py' and type(job['files']) is list
         and 0<len(job['files'])<=layout.MAX_ASSETS,'ordinary_supervisor_generation')
    for row in job['files']:
        need(type(row) is list and len(row)==3 and factory._sha(row[1])
             and type(row[2]) is int and 0<=row[2]<=layout.MAX_ASSET,'ordinary_supervisor_generation')
        layout.safe_relative(row[0])
    staged=layout.StagedCode(CODE,job['entry'],tuple(tuple(r) for r in job['files']),job['generation_index_sha256'])
    layout.exact_generation_tree(staged)
    for row in job['files']: _asset(job,row[0])
    source=factory._read(WORK/'input.ods',1000000)
    need(len(source)==job['source_bytes'] and factory.digest(source)==job['source_sha256'],
         'ordinary_supervisor_original_source')
    return job


def _font_profile(job):
    profile=factory.decode(observer.read_ref(_asset(job,'deps/font-profile.json')))
    need(type(profile) is dict and set(profile)=={'consumer','baseline','derived_cache','provenance_ref',
         'base_view_sha256','expected_view_sha256'},'ordinary_supervisor_font_profile')
    for role,relative in [('consumer','deps/font_view.py'),('baseline','deps/font-baseline.json'),
                         ('derived_cache','deps/font-derived-cache.json'),('provenance_ref','deps/font-provenance.json')]:
        need(profile[role]==_asset(job,relative),'ordinary_supervisor_fixed_font_asset')
    need(factory._sha(profile['base_view_sha256']) and factory._sha(profile['expected_view_sha256']),
         'ordinary_supervisor_font_digest')
    return profile


def _font_CAS(job,profile,tag):
    _check(job)
    consumer=observer.load_module(profile['consumer'],'frw_ordinary_managed_font_view')
    baseline=factory.decode(observer.read_ref(profile['baseline'],limit=4*1024*1024))
    derived=factory.decode(observer.read_ref(profile['derived_cache'],limit=4*1024*1024))
    observer.read_ref(profile['provenance_ref'],limit=4*1024*1024)
    result=consumer.validate_effective_font_config_view(baseline,
        expected_view_digest=profile['expected_view_sha256'],derived_cache=derived)
    need(result['view_sha256']==profile['expected_view_sha256']
         and result['observation']['status']=='metadata_cas_pass_with_critical_rehash',
         'ordinary_supervisor_font_CAS')
    _check(job)
    observer.atomic(WORK/('ordinary-font-'+tag+'.json'),dict(schema='frw.ordinary-calc.font-phase.v1',
        nonce=job['nonce'],phase=tag,view_sha256=result['view_sha256'],
        base_view_sha256=profile['base_view_sha256'],observation=result['observation'],actual_M=None))


def _own_namespace_processes():
    values=[int(name) for name in os.listdir('/proc') if name.isdecimal()]
    need(0<len(values)<=512,'ordinary_supervisor_process_bound')
    return sorted(values)


def _reap_adopted():
    while True:
        try: pid,_=os.waitpid(-1,os.WNOHANG)
        except ChildProcessError: return
        if pid==0: return


def _spawn(argv,env,children,job):
    # Expensive preparation/hashing may have consumed the remaining budget or
    # cancellation may have arrived since the caller's preceding phase check.
    _check(job)
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,close_fds=True,env=env)
    children.append(child)
    return child


def _wait_child(child,job,expected):
    while child.poll() is None:
        _check(job);time.sleep(min(.005,max(0,job['deadline']-time.monotonic()-CLEANUP_RESERVE)))
    need(child.wait()==expected,'ordinary_supervisor_child_status')
    _check(job)


def _bootstrap(job,children,env):
    """New ordinary invocation of the reviewed stock81 then finalizer0 recipe.

    No document/model/metric is passed, no retry or fabricated profile state.
    Passive managed Fontconfig cache provenance is distinct from this profile.
    """
    profile=WORK/'profile'
    need(profile.is_dir() and not list(profile.iterdir()),'ordinary_supervisor_profile_not_fresh')
    version=factory._proc_bytes(PROGRAM+'/versionrc',32768)
    ids=re.findall(rb'^buildid=([^\r\n]+)',version,re.M)
    need(ids==[factory.COMMIT.encode()],'ordinary_supervisor_stock_buildid')
    argv=[PROGRAM+'/soffice.bin','-env:UserInstallation='+profile.as_uri(),'--headless','--invisible',
          '--nologo','--norestore','--nodefault','--nofirststartwizard','--quickstart=no']
    steps=[]
    for index,expected in enumerate((81,0)):
        _check(job);factory._file_observation(PROGRAM+'/soffice.bin',TARGET_SHA256)
        child=_spawn(argv+(['--terminate_after_init'] if index else []),env,children,job)
        birth=observer.proc(child.pid)
        need(birth['ppid']==1 and os.readlink('/proc/%d/exe'%child.pid)==PROGRAM+'/soffice.bin',
             'ordinary_supervisor_bootstrap_birth')
        _wait_child(child,job,expected);_reap_adopted()
        need(_own_namespace_processes()==[1],'ordinary_supervisor_bootstrap_descendant_remaining')
        buildid=factory._read(profile/'user/extensions/buildid',257)
        need(buildid==ids[0],'ordinary_supervisor_profile_buildid')
        steps.append(dict(index=index,process=birth,exit_code=expected,reaped=True,buildid_sha256=factory.digest(buildid)))
    observer.atomic(WORK/'ordinary-bootstrap.json',dict(schema='frw.ordinary-calc.stock-profile.v1',
        nonce=job['nonce'],source_sha256=job['source_sha256'],profile_origin='CREATED_EMPTY_IN_THIS_OPERATION',
        document_requested=False,steps=steps,actual_M=None))


def _ready(job,gdb):
    path=WORK/'native-trace.json'
    while True:
        _check(job);need(gdb.poll() is None,'ordinary_supervisor_GDB_exit_before_ready')
        if path.exists():
            trace=factory.decode(factory._read(path,1048576))
            need(trace.get('error') is None,'ordinary_supervisor_native_startup_refused')
            if trace.get('status')=='READY_UNRELEASED':
                need(trace['nonce']==job['nonce'] and trace['records']==[]
                     and trace['process']['gdb_pid']==gdb.pid and trace['process']['inferior']==1,
                     'ordinary_supervisor_ready_binding')
                return trace['process'],trace['symbols']
        time.sleep(.005)


def _inner(job,process,symbols,children,env):
    config=dict(schema='frw.ordinary-calc.inner-config.v1',nonce=job['nonce'],
        source_sha256=job['source_sha256'],source_bytes=job['source_bytes'],pipe_name='friday_metric_'+job['nonce'],
        process=process,symbols=symbols,started_monotonic=job['started_monotonic'],
        parent_deadline=job['parent_deadline'],deadline=job['deadline'])
    observer.atomic(WORK/'ordinary-inner.json',config)
    child=_spawn(['/usr/bin/python3','-I','-B','-S',str(CODE/'hermes_cli/friday_workspace_calc_native_uno.py')],env,children,job)
    birth=observer.proc(child.pid)
    need(birth['ppid']==1 and observer.namespaces(child.pid)==observer.namespaces(1),
         'ordinary_supervisor_inner_birth_namespace')
    return child


def _watch(job,built,gdb,inner):
    serviced=[]
    while gdb.poll() is None or inner.poll() is None:
        _check(job)
        for tag in ('loaded','closed'):
            if tag not in serviced and (WORK/('ordinary-boundary-request-'+tag+'.json')).exists():
                need((tag=='loaded' and not serviced) or (tag=='closed' and serviced==['loaded']),
                     'ordinary_supervisor_boundary_order')
                observer.service_boundary(WORK,tag,inputs=built['inputs'],child=gdb)
                serviced.append(tag)
        need(gdb.poll() in (None,0) and inner.poll() in (None,0),'ordinary_supervisor_owned_child_refused')
        time.sleep(.005)
    need(gdb.wait()==inner.wait()==0 and serviced==['loaded','closed'],
         'ordinary_supervisor_incomplete_native_lifecycle')
    _check(job);_reap_adopted()
    need(_own_namespace_processes()==[1],'ordinary_supervisor_unreaped_owned_descendant')


def _components(job,inner):
    values=[]
    for tag,boundary in [('loaded','AFTER_LOAD_BEFORE_QUERY'),('closed','AFTER_READONLY_CLOSE')]:
        raw=factory._read(WORK/('ordinary-components-'+tag+'.json'),32768)
        value=factory.decode(raw)
        need(value['schema']=='frw.ordinary-calc.held-components.v1' and value['nonce']==job['nonce']
             and value['source_sha256']==job['source_sha256'] and value['source_bytes']==job['source_bytes']
             and value['process']==inner['process'] and value['symbols']==inner['symbols']
             and value['barrier']==boundary and value['actual_M'] is None,'ordinary_supervisor_components_binding')
        proof_path=WORK/('font-runtime-'+tag+'-proof.json')
        proof_raw=factory._read(proof_path,32768)
        need(value['font_proof_ref']==observer.ref(proof_path,proof_raw),
             'ordinary_supervisor_components_held_proof_binding')
        rows=value['components']
        need([(r['role'],r['sha256']) for r in rows]==[(role,sha) for role,leaf,sha in factory.COMPONENTS]
             and (tag!='loaded' or all(r['mapped'] is True and r['scope']=='ACTUAL_MAPPED_COMPONENT' for r in rows)),
             'ordinary_supervisor_component_source_roles')
        values.append(value)
    return [[r['role'],r['sha256']] for r in values[0]['components']]


def _terminal(job,built,profile):
    _check(job)
    inner_raw=factory._read(WORK/'ordinary-inner-result.json',1048576);inner=factory.decode(inner_raw)
    factory._verify_inner(inner,nonce=job['nonce'],source_sha256=job['source_sha256'],source_bytes=job['source_bytes'])
    raw=factory._read(WORK/'native-trace.json',1048576)
    projected=factory.verify_terminal_extensions(raw,work=WORK,nonce=job['nonce'],process=inner['process'],
        symbols=inner['symbols'],source_sha256=job['source_sha256'],deadline=job['deadline'])
    measured._unchanged_base_projection(raw,projected,terminal=True)
    terminal=measured.terminal_native_join(projected,nonce=job['nonce'],process=inner['process'],
        symbols=inner['symbols'],responses=inner['responses'],live=inner['live'])
    observer.atomic(WORK/'native-terminal-base.json',factory.decode(projected))
    # The projection may use different whitespace. Preserve hash of exact bytes
    # actually published and compare its canonical meaning before host use.
    base_raw=factory._read(WORK/'native-terminal-base.json',1048576)
    measured._unchanged_base_projection(raw,base_raw,terminal=True)
    terminal=measured.terminal_native_join(base_raw,nonce=job['nonce'],process=inner['process'],
        symbols=inner['symbols'],responses=inner['responses'],live=inner['live'])
    output=factory._read(WORK/'out/input.xlsx',16*1024*1024)
    source=factory._read(WORK/'input.ods',1000000)
    need(len(source)==job['source_bytes'] and factory.digest(source)==job['source_sha256'],
         'ordinary_supervisor_terminal_source')
    components=_components(job,inner)
    _check(job,cleanup=True)
    need(_own_namespace_processes()==[1],'ordinary_supervisor_terminal_tree_not_empty')
    result=dict(schema='frw.ordinary-calc.native-terminal.v1',status='COMPLETE_UNATTESTED',
        nonce=job['nonce'],deadline=job['deadline'],generation_index_sha256=job['generation_index_sha256'],
        source_sha256=job['source_sha256'],source_bytes=len(source),output_sha256=factory.digest(output),output_bytes=len(output),
        inner_sha256=factory.digest(inner_raw),native_raw_sha256=factory.digest(raw),native_base_sha256=factory.digest(base_raw),
        terminal_join=terminal,component_sha256=components,font_view_sha256=profile['expected_view_sha256'],
        recipe_sha256=factory._recipe(job),completed_monotonic=time.monotonic(),
        owned_children_after_reap=[],supervisor_exit_ready=True,actual_M=None,runtime_attested=False)
    observer.atomic(WORK/'ordinary-result.json',result)
    _check(job,cleanup=True)
    # Preserve the existing closest caller's completion transport. This marker
    # grants no native/metric facts; the host separately consumes the real _run
    # receipt and verifies the bound terminal records before D6 validation.
    fd=os.open(WORK/'validated',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(b'SPREADSHEET_NATIVE_VALIDATED\n');stream.flush();os.fsync(stream.fileno())
    _check(job,cleanup=True)


def _cleanup(children,job):
    # Only actual direct children returned by this supervisor's own Popen calls.
    # PID1 death is the final namespace containment fence on any unconfirmed path.
    complete=True
    for child in reversed(children):
        try:
            if child.poll() is None: child.kill()
            # Zero remaining budget permits only a nonblocking reap, never an
            # appended minimum wait. PID1 exit remains the containment fence.
            child.wait(timeout=max(0.,min(.25,job['deadline']-time.monotonic())))
        except (OSError,subprocess.TimeoutExpired): complete=False
    _reap_adopted()
    return complete and _own_namespace_processes()==[1] and time.monotonic()<=job['deadline']


def main():
    need(os.getpid()==1 and Path.cwd()==WORK and sys.flags.isolated==1 and sys.flags.no_site==1
         and sys.dont_write_bytecode and Path(__file__).resolve()==CODE/'hermes_cli/friday_workspace_calc_native_supervisor.py',
         'ordinary_supervisor_managed_PID1_entry')
    layout.apply_child_limits()
    env=factory.target_environment();os.environ.clear();os.environ.update(env)
    job=load_job();children=[];stage='BEFORE_BOOTSTRAP'
    try:
        profile=_font_profile(job);_font_CAS(job,profile,'before-bootstrap')
        _bootstrap(job,children,env);stage='AFTER_BOOTSTRAP';_font_CAS(job,profile,'after-bootstrap')
        assets={role:_asset(job,'deps/'+name) for role,name in observer.ASSET_NAMES.items()}
        built=observer.build_observer_inputs(WORK,operation_id='ordinary_'+job['nonce'],nonce=job['nonce'],
            source_sha256=job['source_sha256'],source_bytes=job['source_bytes'],deadline=job['deadline'],assets=assets,
            launch_environment=env,font_view=profile,custody={k:job[k] for k in
                ('generation_index_sha256','started_monotonic','parent_deadline')})
        stage='GDB_STARTING';gdb=_spawn(built['gdb_argv'],built['gdb_env'],children,job)
        process,symbols=_ready(job,gdb)
        stage='UNO_STARTING';inner=_inner(job,process,symbols,children,env)
        observer.publish_launch_custody(WORK,process=process,symbols=symbols,inputs=built['inputs'])
        stage='LOAD_METRIC_STORE_CLOSE';_watch(job,built,gdb,inner)
        stage='TERMINAL';_terminal(job,built,profile)
        return 0
    except BaseException as exc:
        # Fixed phase/class/source location, no OS/UNO messages or user content.
        tb=exc.__traceback__;locations=[]
        while tb is not None and len(locations)<8:
            locations.append(dict(module=Path(tb.tb_frame.f_code.co_filename).name,line=tb.tb_lineno));tb=tb.tb_next
        clean=_cleanup(children,job)
        try:observer.atomic(WORK/'ordinary-refusal.json',dict(schema='frw.ordinary-calc.refusal.v1',nonce=job['nonce'],
            stage=stage,exception_class=type(exc).__name__,locations=locations,cleanup_confirmed=clean,actual_M=None))
        except Exception:pass
        return 2


if __name__=='__main__':
    raise SystemExit(main())
