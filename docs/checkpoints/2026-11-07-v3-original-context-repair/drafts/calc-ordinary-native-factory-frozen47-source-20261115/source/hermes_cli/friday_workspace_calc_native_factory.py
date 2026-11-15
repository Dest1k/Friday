"""Fixed ordinary Calc construction, never a user proof/factory interface.

prepare builds files/argv only. The sole existing _run owns execution and stop;
the fixed parent calls terminal verification after that exact _run returns.
Managed namespace code observes native facts; serialized hashes/types alone do
not grant them. Missing installed assets refuse before any child is launched.
"""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import math
import os
import re
import secrets
import stat
import time

from . import friday_workspace_calc_native_layout as layout
from .friday_workspace_calc_measured import MeasuredRefused

WORK = '/tmp/friday-metric-work'
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
ROLES = ('calc_document','calc_xlsx_filter','sal','toolkit','vcl')
VERSION = '26.2.5.2'
COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
RULE = 'lo-26.2.5.2-explicit-column-forward-v1'
COMPONENTS = (
    ('calc_document','libsclo.so','068dab026bd9df382c5a2441e7f894b3c8c4b9c2b2477c421a15fd86a991fa50'),
    ('calc_xlsx_filter','libscfiltlo.so','5e596afed4ceb859e6756828f823507582015e818b2ca893982ec1e537041114'),
    ('sal','libuno_sal.so.3','2de94acdd2a38f1373ffea27299033de6111294a629fab8d3bed4e061690145b'),
    ('toolkit','libmergedlo.so','569ac2bfab5cccad20badfd3dbc41f9a2464b99e6b98e5d6a6f0711318041f88'),
    ('vcl','libmergedlo.so','569ac2bfab5cccad20badfd3dbc41f9a2464b99e6b98e5d6a6f0711318041f88'))
_PREPARED = object()
INNER_KEYS = {'schema','nonce','source_sha256','source_bytes','responses','live','font','descriptor',
    'source_state','readonly_close_confirmed','store_count','handler_requests','process','symbols',
    'actual_M','runtime_attested','terminal'}
TERMINAL_KEYS = {'schema','status','nonce','deadline','generation_index_sha256','source_sha256','source_bytes',
    'output_sha256','output_bytes','inner_sha256','native_raw_sha256','native_base_sha256','terminal_join',
    'component_sha256','font_view_sha256','recipe_sha256','completed_monotonic','owned_children_after_reap',
    'supervisor_exit_ready','actual_M','runtime_attested'}


class NativeFactoryRefused(MeasuredRefused):
    pass


def need(value, reason):
    if not value:
        raise NativeFactoryRefused(reason)


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def decode(raw):
    def pairs(items):
        value = dict(items)
        need(len(value)==len(items),'ordinary_factory_duplicate_key')
        return value
    def bad(_):
        raise NativeFactoryRefused('ordinary_factory_nonfinite_json')
    try:
        return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
    except (UnicodeError,ValueError,TypeError) as exc:
        if isinstance(exc,NativeFactoryRefused): raise
        raise NativeFactoryRefused('ordinary_factory_json') from None


def _sha(value):
    return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def _read(path,limit):
    path=Path(path)
    need(path.is_absolute() and path.resolve()==path,'ordinary_factory_path_alias')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NOATIME)
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and before.st_mode & 0o022==0 and 0<=before.st_size<=limit,'ordinary_factory_file_custody')
        parts=[];size=0
        while True:
            part=os.read(fd,min(65536,limit+1-size))
            if not part: break
            parts.append(part);size+=len(part)
            need(size<=limit,'ordinary_factory_file_bound')
        need(layout.stamp(before)==layout.stamp(os.fstat(fd))==layout.stamp(path.lstat()),
             'ordinary_factory_file_CAS')
        return b''.join(parts)
    finally:
        os.close(fd)


def _new(path,value):
    raw=canonical(value)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)


def target_environment():
    """Closed stock environment shared by supervisor and managed UNO child."""
    return {'HOME':WORK+'/tmp','TMPDIR':WORK+'/tmp','XDG_CACHE_HOME':WORK+'/cache',
        'XDG_CONFIG_HOME':WORK+'/config','XDG_RUNTIME_DIR':WORK+'/runtime',
        'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PATH':'/usr/bin:/bin','SAL_USE_VCLPLUGIN':'svp',
        'LD_LIBRARY_PATH':WORK+'/code/uno/program:'+PROGRAM+':/opt/friday-document-toolchain/root/usr/lib/x86_64-linux-gnu',
        'URE_BOOTSTRAP':'vnd.sun.star.pathname:'+PROGRAM+'/fundamentalrc','PYTHONDONTWRITEBYTECODE':'1'}


def _recipe(job):
    return digest(canonical(dict(schema='frw.ordinary-calc.fixed-recipe.v1',version=VERSION,commit=COMMIT,rule=RULE,
        generation=job['generation_index_sha256'],source=job['source_sha256'],source_bytes=job['source_bytes'],
        load=dict(Hidden=True,ReadOnly=True,MacroExecutionMode=0,UpdateDocMode=0,FilterName='calc8'),
        store=dict(FilterName='Calc MS Excel 2007 XML',Overwrite=True,ConversionRequestOrigin='CommandLine'),
        namespace_root=WORK,child_seconds=35,parent_seconds=40,one_store=True,full_Font_restore_before_store=True)))


def _proc_bytes(path,limit):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        parts=[];size=0
        while True:
            part=os.read(fd,min(65536,limit+1-size))
            if not part: break
            parts.append(part);size+=len(part)
            need(size<=limit,'ordinary_factory_proc_bound')
        return b''.join(parts)
    finally: os.close(fd)


def _stat_record(raw,pid):
    left,right=raw.find(b' ('),raw.rfind(b') ')
    need(left>0 and right>left and raw[:left]==str(pid).encode(),'ordinary_factory_proc_stat')
    fields=raw[right+2:].split()
    need(len(fields)>=22,'ordinary_factory_proc_stat')
    return dict(pid=pid,ppid=int(fields[1]),start_ticks=int(fields[19])),fields[0]


def _file_observation(path,expected,*,limit=160*1024*1024):
    logical=Path(path);resolved=logical.resolve()
    need(resolved.is_relative_to(PROGRAM),'ordinary_factory_component_path')
    before=resolved.lstat()
    need(stat.S_ISREG(before.st_mode) and 0<before.st_size<=limit and before.st_nlink==1,
         'ordinary_factory_component_file')
    fd=os.open(resolved,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        need(layout.stamp(os.fstat(fd))==layout.stamp(before),'ordinary_factory_component_open_CAS')
        h=hashlib.sha256();size=0;head=b''
        while True:
            chunk=os.read(fd,65536)
            if not chunk: break
            if not head: head=chunk[:16]
            h.update(chunk);size+=len(chunk)
            need(size<=limit,'ordinary_factory_component_file_bound')
        need(head[:6]==b'\x7fELF\x02\x01' and size==before.st_size and h.hexdigest()==expected,
             'ordinary_factory_component_software_hash')
        need(layout.stamp(os.fstat(fd))==layout.stamp(before)==layout.stamp(resolved.lstat())
             and logical.resolve()==resolved,'ordinary_factory_component_file_CAS')
    finally: os.close(fd)
    return resolved,before


def _observe_components(process,*,require_mapped):
    """Actual PID1 all-stop component observation, called by fixed barrier code.

    No callback, path, expected hash or fact provider is supplied by transport.
    Reads current kernel task/maps and exact known software files directly.
    """
    need(os.getpid()==1 and Path.cwd()==Path(WORK) and type(require_mapped) is bool,
         'ordinary_factory_component_namespace_owner')
    need(type(process) is dict and set(process)=={'pid','start_ticks','gdb_pid','inferior'}
         and all(type(v) is int and v>0 for v in process.values()) and process['inferior']==1,
         'ordinary_factory_component_process_shape')
    observer=_observer();pid=process['pid'];debugger=observer.proc(process['gdb_pid'])
    expected=dict(pid=pid,ppid=process['gdb_pid'],start_ticks=process['start_ticks'])
    need(observer.proc(pid)==expected and debugger['ppid']==1
         and observer.namespaces(pid)==observer.namespaces(process['gdb_pid'])==observer.namespaces(1),
         'ordinary_factory_component_actual_birth_namespace')
    status=_proc_bytes('/proc/%d/status'%pid,32768)
    tracer=re.findall(rb'^TracerPid:\s+([0-9]+)$',status,re.M)
    need(tracer==[str(process['gdb_pid']).encode()],'ordinary_factory_component_tracer')
    tids=sorted(os.listdir('/proc/%d/task'%pid))
    need(0<len(tids)<=512 and all(x.isdecimal() for x in tids),'ordinary_factory_component_task_bound')
    def stops():
        result=[]
        for name in tids:
            identity,state=_stat_record(_proc_bytes('/proc/%d/task/%s/stat'%(pid,name),4096),int(name))
            need(state in (b't',b'T') and identity['ppid']==process['gdb_pid'],
                 'ordinary_factory_component_not_kernel_allstop')
            result.append(identity)
        return result
    stopped=stops();maps=_proc_bytes('/proc/%d/maps'%pid,524288)
    parsed=[]
    for line in maps.splitlines():
        fields=line.split(None,5)
        need(len(fields) in (5,6),'ordinary_factory_component_maps')
        if len(fields)!=6: continue
        try:
            major,minor=(int(x,16) for x in fields[3].split(b':'))
            parsed.append((fields[5].decode('utf-8','strict'),fields[1],major,minor,int(fields[4])))
        except (ValueError,UnicodeError):
            raise NativeFactoryRefused('ordinary_factory_component_maps') from None
    actual=[];seen={}
    for role,leaf,expected_sha in COMPONENTS:
        path=PROGRAM+'/'+leaf
        if path not in seen: seen[path]=_file_observation(path,expected_sha)
        resolved,s=seen[path]
        rows=[r for r in parsed if r[0]==str(resolved) and b'x' in r[1]
              and r[2:]==(os.major(s.st_dev),os.minor(s.st_dev),s.st_ino)]
        need(not require_mapped or len(rows)==1,'ordinary_factory_required_component_not_mapped')
        actual.append(dict(role=role,path=str(resolved),sha256=expected_sha,mapped=bool(rows),
            file_stamp=list(layout.stamp(s)),maps_sha256=digest(maps),
            scope='ACTUAL_MAPPED_COMPONENT' if require_mapped else 'POSTCLOSE_BACKING_FILE_CAS'))
    need(observer.proc(pid)==expected and observer.proc(process['gdb_pid'])==debugger
         and _proc_bytes('/proc/%d/maps'%pid,524288)==maps
         and sorted(os.listdir('/proc/%d/task'%pid))==tids and stops()==stopped,
         'ordinary_factory_component_boundary_CAS')
    return actual


@dataclass(frozen=True)
class _Operation:
    argv: tuple
    nonce: str
    deadline: float
    source_sha256: str
    source_bytes: int
    work: Path
    started_monotonic: float
    staged: object
    job_sha256: str
    generation_sha256: str
    authority: object
    execution: list


def prepare_operation(work,data,before,*,deadline):
    """Prepare one exact dynamic source operation; never launch or reset time."""
    from . import friday_workspace_calc_measured as measured
    need(measured.finite_native_family(before,'ods','xlsx'),'ordinary_factory_full_D6_family_required')
    need(type(data) is bytes and 0<len(data)<=1000000,'ordinary_factory_source_bound')
    started=time.monotonic()
    need(type(deadline) in (int,float) and math.isfinite(deadline)
         and started<deadline<=started+35,'ordinary_factory_original_child_deadline')
    work=layout.private_directory(work)
    need({p.name for p in work.iterdir()}=={'out','home','tmp','input.ods','renderer.py'},
         'ordinary_factory_fresh_parent_work')
    for name in ('out','home','tmp'):
        layout.private_directory(work/name)
        need(not list((work/name).iterdir()),'ordinary_factory_initial_private_directory_not_empty')
    source=digest(data)
    need(_read(work/'input.ods',1000000)==data,'ordinary_factory_original_snapshot_mismatch')
    # This pin is installed beside the factory, outside the indexed generation;
    # the generation contains this factory SOURCE without a self-digest cycle.
    try:
        from .friday_workspace_calc_native_pin import GENERATION_SHA256
    except ImportError as exc:
        if exc.name != 'hermes_cli.friday_workspace_calc_native_pin': raise
        raise NativeFactoryRefused('ordinary_native_assets_not_installed') from None
    need(_sha(GENERATION_SHA256),'ordinary_factory_installed_pin_invalid')
    from .friday_workspace_calc_native_assets import stage_installed
    from .friday_workspace_pdf import _toolchain
    staged=stage_installed(work,__file__,GENERATION_SHA256)
    nonce=secrets.token_hex(16)
    for name in ('profile','cache','config','runtime'):
        (work/name).mkdir(mode=0o700)
    (work/'cache/fontconfig').mkdir(mode=0o700)
    job=dict(schema='frw.ordinary-calc.native-job.v1',nonce=nonce,source_sha256=source,source_bytes=len(data),
        started_monotonic=started,parent_deadline=deadline,deadline=deadline,
        generation_index_sha256=GENERATION_SHA256,entry=staged.entry,files=[list(r) for r in staged.files])
    job_sha=_new(work/'ordinary-job.json',job)
    argv=list(layout.namespace_argv(work,_toolchain(),staged,source_sha256=source,source_bytes=len(data)))
    # These passive reviewed cache contents are distinct new managed assets,
    # mounted read-only at the actual stock cache location; both aliases are RO.
    cache=work/'code/deps/font-derived-cache'
    layout.private_directory(cache)
    position=argv.index('--chdir')
    argv[position:position]=['--ro-bind',str(cache),WORK+'/cache/fontconfig']
    need(time.monotonic()<deadline,'ordinary_factory_preparation_deadline')
    return _Operation(tuple(argv),nonce,deadline,source,len(data),work,started,staged,job_sha,
                      GENERATION_SHA256,_PREPARED,[])


def _observer():
    from . import friday_workspace_calc_native_observer
    return friday_workspace_calc_native_observer


def verify_live_extensions(raw,*,work,nonce,process,symbols,source_sha256,deadline):
    return _observer().verify_extensions(raw,work=work,nonce=nonce,process=process,symbols=symbols,
        source_sha256=source_sha256,deadline=deadline,terminal=False)


def verify_terminal_extensions(raw,*,work,nonce,process,symbols,source_sha256,deadline):
    # Called inside original namespace by supervisor before its own final exit.
    # HOST verify_terminal never interprets namespace PIDs as host identities.
    return _observer().verify_extensions(raw,work=work,nonce=nonce,process=process,symbols=symbols,
        source_sha256=source_sha256,deadline=deadline,terminal=True)


def loaded_model_barrier(runtime,doc,*,work,nonce,process,symbols,source_sha256,source_bytes,deadline):
    _observer().request_boundary('loaded',work=work,nonce=nonce,process=process,
        symbols=symbols,source_sha256=source_sha256,deadline=deadline)
    from .friday_workspace_calc_native_uno import bind_loaded_lifecycle
    bind_loaded_lifecycle(runtime,doc,work=work,nonce=nonce,process=process,symbols=symbols,
        source_sha256=source_sha256,source_bytes=source_bytes,deadline=deadline)


def readonly_closed_barrier(*,work,nonce,process,symbols,source_sha256,deadline):
    _observer().request_boundary('closed',work=work,nonce=nonce,process=process,symbols=symbols,
        source_sha256=source_sha256,deadline=deadline)


def _verify_inner(inner,*,nonce,source_sha256,source_bytes):
    need(type(inner) is dict and set(inner)==INNER_KEYS
         and inner['schema']=='frw.ordinary-calc.inner-one-store-candidate.v1'
         and inner['nonce']==nonce and inner['source_sha256']==source_sha256
         and type(inner['source_bytes']) is int and inner['source_bytes']==source_bytes
         and type(inner['store_count']) is int and inner['store_count']==1
         and type(inner['handler_requests']) is int and inner['handler_requests']==0
         and inner['readonly_close_confirmed'] is True and inner['actual_M'] is None
         and inner['runtime_attested'] is False and inner['terminal']=='UNBOUND_PARENT',
         'ordinary_factory_one_store_source_close')


def verify_terminal(work,operation,source,output):
    """Consume exact constructed child AFTER fixed parent _run and output read.

    The trusted parent call order and indexed immutable supervisor SOURCE are
    indispensable provenance. This is not a public receipt/JSON admission API.
    Native current observations and extension verification occurred INSIDE that
    namespace; here validate their bound result, bytes and final numeric join.
    """
    from . import friday_workspace_calc_measured as measured
    need(type(operation) is _Operation and operation.authority is _PREPARED,
         'ordinary_factory_unprepared_operation')
    from .friday_workspace_pdf import _RenderReceipt, _RUN_COMPLETION_AUTHORITY
    need(type(operation.execution) is list and len(operation.execution)==1,
         'ordinary_factory_actual_run_completion_required')
    completion=operation.execution[0]
    need(type(completion) is _RenderReceipt and completion.authority is _RUN_COMPLETION_AUTHORITY
         and completion.argv==operation.argv and completion.work==operation.work
         and type(completion.pid) is int and completion.pid>0
         and type(completion.returncode) is int and completion.returncode==0
         and operation.started_monotonic<=completion.started<=completion.finished
         and operation.deadline<=completion.deadline<=completion.started+40
         and completion.finished<=completion.deadline+2,
         'ordinary_factory_actual_run_completion_binding')
    work=layout.private_directory(work)
    need(work==operation.work and type(source) is bytes and type(output) is bytes
         and len(source)==operation.source_bytes and digest(source)==operation.source_sha256,
         'ordinary_factory_parent_operation_binding')
    need(_read(work/'input.ods',1000000)==source and _read(work/'out/input.xlsx',16*1024*1024)==output,
         'ordinary_factory_parent_source_output_CAS')
    job_raw=_read(work/'ordinary-job.json',262144)
    need(digest(job_raw)==operation.job_sha256,
         'ordinary_factory_job_changed')
    job=decode(job_raw)
    layout.exact_generation_tree(operation.staged)
    for relative,sha,size in operation.staged.files:
        raw=layout.read_exact_file(operation.staged.directory/relative,sha)
        need(len(raw)==size,'ordinary_factory_staged_code_changed')
    report=decode(_read(work/'ordinary-result.json',1048576))
    need(type(report) is dict and set(report)==TERMINAL_KEYS
         and report.get('actual_M') is None and report.get('runtime_attested') is False
         and report.get('schema')=='frw.ordinary-calc.native-terminal.v1'
         and report.get('status')=='COMPLETE_UNATTESTED'
         and report.get('nonce')==operation.nonce and report.get('deadline')==operation.deadline
         and report.get('generation_index_sha256')==operation.generation_sha256
         and report.get('source_sha256')==operation.source_sha256 and report.get('source_bytes')==len(source)
         and report.get('output_sha256')==digest(output) and report.get('output_bytes')==len(output),
         'ordinary_factory_terminal_operation_binding')
    need(type(report.get('completed_monotonic')) in (int,float)
         and operation.started_monotonic<=report['completed_monotonic']<=min(operation.deadline,completion.finished)
         and report.get('owned_children_after_reap')==[] and report.get('supervisor_exit_ready') is True,
         'ordinary_factory_terminal_custody_unconfirmed')
    inner_raw=_read(work/'ordinary-inner-result.json',1048576)
    native_raw=_read(work/'native-trace.json',1048576)
    base_raw=_read(work/'native-terminal-base.json',1048576)
    need(report.get('inner_sha256')==digest(inner_raw) and report.get('native_raw_sha256')==digest(native_raw)
         and report.get('native_base_sha256')==digest(base_raw),'ordinary_factory_terminal_record_CAS')
    inner=decode(inner_raw)
    _verify_inner(inner,nonce=operation.nonce,source_sha256=operation.source_sha256,source_bytes=len(source))
    measured._unchanged_base_projection(native_raw,base_raw,terminal=True)
    terminal=measured.terminal_native_join(base_raw,nonce=operation.nonce,process=inner['process'],
        symbols=inner['symbols'],responses=inner['responses'],live=inner['live'])
    need(terminal==report.get('terminal_join'),'ordinary_factory_terminal_numeric_join_changed')
    rows=report.get('component_sha256')
    need(type(rows) is list and len(rows)==len(ROLES) and tuple(r[0] for r in rows)==ROLES
         and all(type(r) is list and len(r)==2 and _sha(r[1]) for r in rows),
         'ordinary_factory_component_roles')
    need(rows==[[role,sha] for role,leaf,sha in COMPONENTS]
         and report.get('recipe_sha256')==_recipe(job),'ordinary_factory_component_or_recipe_source_binding')
    font_profile=decode(_read(work/'code/deps/font-profile.json',262144))
    need(_sha(report.get('font_view_sha256'))
         and report['font_view_sha256']==font_profile['expected_view_sha256'],
         'ordinary_factory_expected_font_view_binding')
    font=inner['font'];recipe=font['recipe'];nominal=font['source_nominal_font']
    need(nominal['Name']=='Calibri' and nominal['HeightPt']==11.0 and recipe['Height']==220
         and font['observations']['style']['programmatic_name']=='Default'
         and font['default_script']['value']=='LATIN' and font['use_printer_metrics'] is False,
         'ordinary_factory_supported_reference_font')
    facts=dict(producer_version=VERSION,reviewed_source_commit=COMMIT,numeric_rule=RULE,
        recipe_sha256=report['recipe_sha256'],component_sha256=tuple(tuple(r) for r in rows),
        source_style_name='Default',source_font=('Calibri',Decimal(11)),default_script='LATIN',
        export_name=recipe['Name'],export_charset=recipe['CharSet'],raw_font_height=220,
        font_descriptor_sha256=digest(canonical(inner['descriptor'])),font_view_sha256=report['font_view_sha256'],
        reference_state_sha256=digest(canonical({'font':font,'model':inner['source_state']})),
        applicability_sha256=digest(canonical({'source':operation.source_sha256,'output':digest(output),
            'recipe':report['recipe_sha256'],'native':digest(native_raw),'scope':RULE})),raw_m=terminal['raw_m'])
    measured._verified_fact_shape(facts)
    return facts
