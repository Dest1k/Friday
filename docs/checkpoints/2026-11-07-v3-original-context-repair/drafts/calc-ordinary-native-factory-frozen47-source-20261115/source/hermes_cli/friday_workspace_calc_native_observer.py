"""Ordinary-only stock observer construction and phase-specific custody.

Import is inert. Runtime entry is owned by the sole ordinary namespace PID1;
this module never owns an outer process group, service, window or operation.
Pure tests may replace OS leaf reads explicitly; such tests confer no runtime
credit. Historical helper sources remain immutable; these are ordinary deltas.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import os
import re
import signal
import stat
import time
import types

WORK = Path('/tmp/friday-metric-work')
CODE = WORK/'code'
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
BASE = {'schema','kind','nonce','status','records','error','exit_code','process','symbols','actual_M','runtime_attested'}
EXTENSIONS = {'load_dependency','gpgme_engine_init'}
FONT_KEYS = ('HOME','TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','FONTCONFIG_FILE',
    'FONTCONFIG_PATH','FONTCONFIG_SYSROOT','FC_LANG','LANG','LC_ALL','SAL_FONTPATH','SAL_USE_VCLPLUGIN',
    'LD_LIBRARY_PATH','URE_BOOTSTRAP')
LIMITS = dict(cpu_seconds=35,address_space_bytes=1073741824,file_size_bytes=16777216,nofile=128,core_bytes=0)
ASSET_NAMES = {'config_template':'FUTURE-OFFICE-CONFIG-TEMPLATE.json',
    'paper_manifest':'PAPER-HELPER-OFFICE-MANIFEST.json','gpgme_software':'GPG-SOFTWARE-SNAPSHOT.json',
    'native_observer':'native_return_observer.py','paper_policy':'paper_helper_policy.py',
    'paper_adapter':'paper_helper_gdb.py','gpgme_validator':'gpgme_engine_bundle.py',
    'gpgme_collector':'gpgme_boundary_collector.py','gpgme_adapter':'gpgme_engine_gdb.py',
    'gpgme_policy':'gpgme_engine_policy.py','gpgme_mapper':'gpgme_mapped_image.py'}


class ObserverRefused(RuntimeError):
    pass


def need(value, code):
    if not value:
        raise ObserverRefused(code)


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def unique(items):
        result = {}
        for key,value in items:
            need(key not in result,'ordinary_observer_duplicate_key')
            result[key] = value
        return result
    try:
        return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _: need(False,'ordinary_observer_nonfinite'))
    except (ValueError,TypeError,UnicodeError):
        raise ObserverRefused('ordinary_observer_invalid_json') from None


def stamp(value):
    return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def private_read(path, limit=262144, *, source=False):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.resolve()==path,'ordinary_observer_path')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit
             and (not before.st_mode&0o022 if source else (before.st_uid==os.getuid() and stat.S_IMODE(before.st_mode)==0o600)),
             'ordinary_observer_file_rights')
        chunks,size=[],0
        while True:
            part=os.read(fd,min(65536,limit+1-size))
            if not part:break
            chunks.append(part);size+=len(part)
            need(size<=limit,'ordinary_observer_file_bound')
        need(size==before.st_size and stamp(before)==stamp(os.fstat(fd))==stamp(path.lstat()),'ordinary_observer_file_CAS')
        return b''.join(chunks)
    finally:
        os.close(fd)


def ref(path, raw):
    return dict(path=str(path),sha256=sha(raw))


def read_ref(value, *, source=True, limit=1048576):
    need(type(value) is dict and set(value)=={'path','sha256'} and type(value['sha256']) is str
         and re.fullmatch('[0-9a-f]{64}',value['sha256']),'ordinary_observer_ref')
    raw=private_read(value['path'],limit,source=source)
    need(sha(raw)==value['sha256'],'ordinary_observer_ref_changed')
    return raw


def _publish_no_replace(pending,path):
    """One Linux renameat2 commit: no visible nlink2 and no target overwrite.

    libc/kernel/filesystem support is mandatory. Unsupported or refused commit
    leaves no published authority; the sole caller removes its own pending file.
    No link-based fallback, overwrite fallback, retry or permission relaxation.
    """
    import ctypes
    import errno
    need(not os.path.lexists(WORK/'ordinary-cancel'),'ordinary_observer_cancelled')
    libc=ctypes.CDLL(None,use_errno=True)
    rename=getattr(libc,'renameat2',None)
    need(rename is not None,'ordinary_observer_noreplace_unavailable')
    rename.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    rename.restype=ctypes.c_int
    # Linux stable ABI constants: AT_FDCWD=-100, RENAME_NOREPLACE=1.
    result=rename(-100,os.fsencode(pending),-100,os.fsencode(path),1)
    if result:
        code=ctypes.get_errno()
        if code in (errno.EEXIST,errno.ENOTEMPTY):
            raise ObserverRefused('ordinary_observer_prefilled_transport')
        if code in (errno.ENOSYS,errno.EINVAL,errno.EOPNOTSUPP):
            raise ObserverRefused('ordinary_observer_noreplace_unavailable')
        raise OSError(code,'ordinary_observer_noreplace_failed')


def atomic(path,value):
    path=Path(path);raw=canonical(value);pending=path.with_name(path.name+'.pending')
    need(path.parent==WORK or path.parent==WORK/'output','ordinary_observer_transport_path')
    need(len(raw)<=262144 and not os.path.lexists(path),'ordinary_observer_prefilled_transport')
    need(not os.path.lexists(WORK/'ordinary-cancel'),'ordinary_observer_cancelled')
    fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        # Keep the created inode open through commit and cleanup. A conflicting
        # pending pathname never authorizes deleting another writer's file.
        with os.fdopen(fd,'wb',closefd=False) as out:
            out.write(raw);out.flush();os.fsync(out.fileno())
        opened=os.fstat(fd);named=os.stat(pending,follow_symlinks=False)
        need(stamp(opened)==stamp(named) and stat.S_ISREG(opened.st_mode) and opened.st_uid==os.getuid()
             and stat.S_IMODE(opened.st_mode)==0o600 and opened.st_nlink==1 and opened.st_size==len(raw),
             'ordinary_observer_pending_source_changed')
        _publish_no_replace(pending,path)
        published=os.stat(path,follow_symlinks=False)
        need((published.st_dev,published.st_ino)==(opened.st_dev,opened.st_ino)
             and published.st_nlink==1,'ordinary_observer_published_source_changed')
    except BaseException:
        try:
            named=os.stat(pending,follow_symlinks=False);opened=os.fstat(fd)
            if (named.st_dev,named.st_ino)==(opened.st_dev,opened.st_ino):os.unlink(pending)
        except FileNotFoundError:pass
        raise
    finally:
        os.close(fd)
    return ref(path,raw)


def clock(deadline):
    need(type(deadline) in (int,float) and math.isfinite(deadline) and 0<time.monotonic()<deadline,
         'ordinary_observer_original_deadline')
    need(not os.path.lexists(WORK/'ordinary-cancel'),'ordinary_observer_cancelled')


def proc(pid):
    need(type(pid) is int and pid>0,'ordinary_observer_pid')
    root=Path('/proc')/str(pid)
    raw=(root/'stat').read_bytes();parts=raw.rsplit(b')',1)[1].split()
    result=dict(pid=pid,ppid=int(parts[1]),start_ticks=int(parts[19]))
    need((root/'stat').read_bytes()==raw,'ordinary_observer_process_CAS')
    return result


def namespaces(pid):
    return {name:dict(dev=(s:=os.stat('/proc/%d/ns/%s'%(pid,name))).st_dev,ino=s.st_ino)
        for name in ('user','mnt','pid','net','uts','ipc','cgroup')}


def environment(pid):
    raw=Path('/proc/%d/environ'%pid).read_bytes()
    need(0<len(raw)<=131072 and raw.endswith(b'\0'),'ordinary_observer_environment_bound')
    pairs=[part.split(b'=',1) for part in raw[:-1].split(b'\0')]
    need(all(len(v)==2 for v in pairs),'ordinary_observer_environment_encoding')
    result={k.decode('ascii'):v.decode('utf-8') for k,v in pairs}
    need(len(result)==len(pairs),'ordinary_observer_environment_duplicate')
    return result


def namespace_context():
    me=proc(os.getpid());supervisor=proc(1)
    need(supervisor['ppid']==0 and namespaces(1)==namespaces(os.getpid()),'ordinary_observer_namespace_PID1')
    need(me['pid']==1 or me['ppid']==1,'ordinary_observer_direct_PID1_child')
    return supervisor,namespaces(1)


def load_module(value,name):
    module=types.ModuleType(name);module.__file__=value['path']
    exec(compile(read_ref(value),module.__file__,'exec'),module.__dict__)
    return module


def _modules(assets):
    validator=load_module(assets['gpgme_validator'],'frw_ordinary_gpgme_validator')
    binding={'manifest':dict(path=str(WORK/'gpgme-manifest.json'),sha256='0'*64),
        **{role:assets['gpgme_'+role] for role in ('validator','collector','adapter','policy','mapper')}}
    mods=validator.load_sources(binding,read_ref)
    paper=load_module(assets['paper_policy'],'frw_ordinary_paper_policy')
    return paper,validator,mods


def _snapshot_image(image, collector):
    # The expected Source bytes/build-id are fixed software anchors. Only the
    # current SAME-NAMESPACE stat identity is constructed here; no UID inference.
    before=os.stat(image['path'],follow_symlinks=False)
    raw=private_read(image['path'],32*1024*1024,source=True)
    meta=collector.generic_elf_metadata(raw)
    need(meta['sha256']==image['sha256'] and meta['build_id']==image['build_id'],'ordinary_observer_software_drift')
    current=collector.stamp(os.stat(image['path'],follow_symlinks=False))
    need(current['size']==len(raw) and collector.stamp(before)==current,'ordinary_observer_software_stat')
    return dict(path=image['path'],sha256=image['sha256'],build_id=image['build_id'],host_stamp=current)


def _profile(policy):
    return dict(schema=policy.SCHEMA,stage=policy.STAGE,library=dict(path=policy.LIBRARY_PATH,
        sha256=policy.LIBRARY_SHA256,build_id=policy.BUILD_ID),source_manifest_ref=copy.deepcopy(policy.SOURCE_MANIFEST),
        conditional_join_ref=copy.deepcopy(policy.CONDITIONAL_JOIN),branches=[dict(branch=b,role=policy.ROLES[b],option=policy.OPTIONS[b])
        for b in policy.BRANCHES],pseudo_protocols=list(policy.UNSUPPORTED),budgets=dict(wall_seconds=35,cpu_seconds=35,
        memory_bytes=1073741824,deadline_rule='SAME_ORIGINAL_ABSOLUTE_OPERATION_DEADLINE_NO_RESET'),runtime_available=False)


def _fixed_assets(assets):
    need(type(assets) is dict and set(assets)==set(ASSET_NAMES),'ordinary_observer_exact_assets')
    for role,name in ASSET_NAMES.items():
        need(type(assets[role]) is dict and assets[role].get('path')==str(CODE/'deps'/name),
             'ordinary_observer_fixed_asset_path')
        read_ref(assets[role])


def _fixed_font(font):
    names=dict(consumer='font_view.py',baseline='font-baseline.json',derived_cache='font-derived-cache.json',
               provenance_ref='font-provenance.json')
    need(type(font) is dict and set(font)==set(names)|{'expected_view_sha256','base_view_sha256'},
         'ordinary_observer_fixed_font_contract')
    for role,name in names.items():
        need(type(font[role]) is dict and font[role].get('path')==str(CODE/'deps'/name),
             'ordinary_observer_fixed_font_path')
        read_ref(font[role],limit=4*1024*1024)
    need(all(type(font[k]) is str and re.fullmatch('[0-9a-f]{64}',font[k]) for k in
        ('expected_view_sha256','base_view_sha256')),'ordinary_observer_font_view_digest')


def build_observer_inputs(work, *, operation_id,nonce,source_sha256,source_bytes,deadline,assets,
                          launch_environment,font_view,custody):
    """Construct real dynamic manifests/config for one ordinary stock launch.

    Called by sole namespace supervisor before launching GDB. The asset map is
    fixed by its managed source generation, never loaded from caller proof JSON.
    No launch, GDB execution or target import occurs in this constructor.
    """
    need(Path(work)==WORK,'ordinary_observer_single_work')
    supervisor,ns=namespace_context();need(os.getpid()==1,'ordinary_observer_constructor_PID1')
    clock(deadline)
    need(type(custody) is dict and set(custody)=={'generation_index_sha256','started_monotonic','parent_deadline'},
         'ordinary_observer_custody_input')
    need(type(custody['generation_index_sha256']) is str and re.fullmatch('[0-9a-f]{64}',custody['generation_index_sha256'])
         and type(custody['parent_deadline']) in (int,float) and math.isfinite(custody['parent_deadline'])
         and type(custody['started_monotonic']) in (int,float) and math.isfinite(custody['started_monotonic'])
         and custody['started_monotonic']<=time.monotonic()<deadline<=min(custody['parent_deadline'],custody['started_monotonic']+35),
         'ordinary_observer_cumulative35')
    _fixed_assets(assets);_fixed_font(font_view)
    need(type(nonce) is str and re.fullmatch('[0-9a-f]{32}',nonce)
         and type(source_sha256) is str and re.fullmatch('[0-9a-f]{64}',source_sha256)
         and type(source_bytes) is int and 0<source_bytes<=1000000
         and type(operation_id) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}',operation_id), 'ordinary_observer_operation_input')
    raw=private_read(WORK/'input.ods',1000000)
    need(len(raw)==source_bytes and sha(raw)==source_sha256,'ordinary_observer_source_input')
    paper,validator,mods=_modules(assets);p,c=mods['policy'],mods['collector']
    p.validate_environment(launch_environment,launch_environment)
    need(not any(k.startswith('FRW_NATIVE_') for k in launch_environment),'ordinary_observer_control_environment')
    pm=decode(read_ref(assets['paper_manifest']));pm['source_sha256']=source_sha256
    pm['environment']=copy.deepcopy(launch_environment);paper.validate_manifest(pm)
    pmref=atomic(WORK/'paper-manifest.json',pm)
    software=decode(read_ref(assets['gpgme_software']))
    need(software['schema']=='frw.calc.ordinary-static-software-snapshot.v1' and software['source_only'] is True,
         'ordinary_observer_static_software_source')
    cache={}
    for rows in software['dependencies'].values():
        for image in rows:
            previous=cache.get(image['path'])
            current=_snapshot_image(image,c)
            need(previous is None or previous==current,'ordinary_observer_software_alias')
            cache[image['path']]=current
    dependencies={('original' if role=='original_gpgme_library' else role):[cache[i['path']] for i in rows]
        for role,rows in software['dependencies'].items()}
    helpers={role:dict(path=i['path'],sha256=i['sha256'],dev=os.makedev(cache[i['path']]['host_stamp']['dev_major'],
        cache[i['path']]['host_stamp']['dev_minor']),ino=cache[i['path']]['host_stamp']['ino']) for role,i in software['helpers'].items()}
    need(all(not os.path.lexists(path) for path in software['absent_optional_helpers']), 'ordinary_observer_optional_helper_drift')
    absent=list(pm['absent_paths'])+['/etc/gnupg',str(WORK/'tmp/.gnupg')]
    need(all(not os.path.lexists(path) for path in absent),'ordinary_observer_configuration_present')
    gm=dict(schema=validator.MANIFEST,profile=_profile(p),source_mode='COLD_GPGCONF',helpers=helpers,
        collector_pins=dict(operation=None,original=None,reaper=None,library=cache[software['library']['path']],
            libc=cache[software['libc']['path']],environment=copy.deepcopy(launch_environment),cwd=str(WORK),
            absent_paths=absent,private_roots=None,cgroup=None,uid_projection=None,dependencies=dependencies))
    validator.validate_manifest(gm,p,c);gmref=atomic(WORK/'gpgme-manifest.json',gm)
    pr=dict(operation_id=operation_id,nonce=nonce,source_sha256=source_sha256,manifest_ref=pmref,
        marker_path=str(WORK/'load-dependency.json'),operation_deadline_monotonic=deadline)
    pb=dict(schema='frw.calc.paper-helper-runtime-bundle.v1',runtime=pr,manifest_ref=pmref,
        policy_ref=assets['paper_policy'],adapter_ref=assets['paper_adapter'])
    pref=atomic(WORK/'helper-runtime.json',pb)
    gr=dict(operation_id=operation_id,nonce=nonce,source_sha256=source_sha256,manifest_ref=gmref,paper_manifest_ref=pmref,
        marker_path=pr['marker_path'],operation_deadline_monotonic=deadline,bundle_path=validator.BUNDLE_PATH,evidence_path=validator.EVIDENCE_PATH)
    gb=dict(schema=validator.SCHEMA,manifest_ref=gmref,runtime=gr,evidence_path=gr['evidence_path'],
        **{role+'_ref':assets['gpgme_'+role] for role in ('validator','collector','adapter','policy','mapper')})
    validator.validate_bundle(gb,gm,p,c);gref=atomic(Path(validator.BUNDLE_PATH),gb)
    cfg=decode(read_ref(assets['config_template']))
    cfg.update(nonce=nonce,target_path=PROGRAM+'/soffice.bin',symbol_file_path=PROGRAM+'/libmergedlo.so',
        phase_path=str(WORK/'phase.json'),trace_path=str(WORK/'native-trace.json'),ordinary=dict(operation_id=operation_id,
        source_sha256=source_sha256,source_bytes=source_bytes,deadline_monotonic=deadline,
        generation_index_sha256=custody['generation_index_sha256'],launch_environment=copy.deepcopy(launch_environment)))
    need(cfg['kind']=='OFFICE_UNADMITTED','ordinary_observer_stock_only')
    # Actual image pins are read before launch; source symbols/offsets remain fixed.
    need(sha(private_read(cfg['target_path'],32*1024*1024,source=True))==cfg['target_sha256']
         and sha(private_read(cfg['symbol_file_path'],160*1024*1024,source=True))==cfg['symbol_file_sha256'],
         'ordinary_observer_target_software_drift')
    cfgref=atomic(WORK/'native-config.json',cfg)
    atomic(WORK/'phase.json',dict(nonce=nonce,phase='IDLE',index=None,digit=None))
    atomic(WORK/'load-dependency.json',dict(schema=paper.MARKER,state='LOAD_OPEN',**{k:pr[k] for k in
        ('operation_id','nonce','source_sha256','manifest_ref','operation_deadline_monotonic')}))
    inputs=dict(schema='frw.ordinary-calc.observer-inputs.v1',operation_id=operation_id,nonce=nonce,
        source_sha256=source_sha256,source_bytes=source_bytes,deadline=deadline,custody=custody,assets=assets,
        font_view=font_view,config=cfg,config_ref=cfgref,paper_bundle=pb,paper_bundle_ref=pref,gpgme_bundle=gb,
        gpgme_bundle_ref=gref,supervisor=supervisor,namespaces=ns)
    atomic(WORK/'ordinary-observer-inputs.json',inputs)
    args=[cfg['target_path'],'-env:UserInstallation='+(WORK/'profile').as_uri(),
        '--headless','--nologo','--norestore','--nodefault','--nofirststartwizard']
    args+=['--accept=pipe,name=friday_metric_'+nonce+';urp;StarOffice.ComponentContext']
    gdb_env=dict(launch_environment,FRW_NATIVE_OBSERVER_CONFIG=cfgref['path'],
        FRW_NATIVE_LOAD_DEPENDENCY_REF=json.dumps(pref,sort_keys=True),FRW_NATIVE_GPGME_ENGINE_INIT_REF=json.dumps(gref,sort_keys=True),
        FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE=gr['evidence_path'])
    return dict(inputs=inputs,gdb_argv=['/usr/bin/gdb','-nx','-nh','--batch','-q',
        '-iex','maintenance set worker-threads 1','-iex','set auto-load off','-iex','set may-call-functions off',
        '-x',assets['native_observer']['path'],'--args',*args],gdb_env=gdb_env,config=cfg,helper_bundle=pb,gpgme_bundle=gb,
        observer_ref=assets['native_observer'])


def _actual_stock(inputs,pid):
    before=proc(pid);path='/proc/%d/exe'%pid
    target=inputs['config']['target_path']
    need(os.readlink(path)==target,'ordinary_observer_current_stock_exe')
    raw=Path(path).read_bytes()
    need(0<len(raw)<=32*1024*1024 and sha(raw)==inputs['config']['target_sha256']
         and os.readlink(path)==target and proc(pid)==before,'ordinary_observer_current_stock_image')


def publish_launch_custody(work, *, process,symbols,inputs):
    need(Path(work)==WORK and os.getpid()==1,'ordinary_observer_launch_owner')
    clock(inputs['deadline']);supervisor,ns=namespace_context()
    actual=proc(process['pid']);debugger=proc(process['gdb_pid'])
    need(process==dict(pid=actual['pid'],start_ticks=actual['start_ticks'],gdb_pid=actual['ppid'],inferior=1)
         and debugger['ppid']==1 and namespaces(actual['pid'])==namespaces(debugger['pid'])==ns,
         'ordinary_observer_actual_launch_chain')
    need(os.readlink('/proc/%d/exe'%actual['pid'])==inputs['config']['target_path']
         and sha(Path('/proc/%d/exe'%actual['pid']).read_bytes())==inputs['config']['target_sha256'],
         'ordinary_observer_actual_stock_target')
    need(environment(actual['pid'])==inputs['config']['ordinary']['launch_environment'],'ordinary_observer_actual_startup_environment')
    env=inputs['config']['ordinary']['launch_environment']
    roots={str(WORK)}|{v for k,v in env.items() if k in
        ('HOME','TMPDIR','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR','XDG_DATA_HOME')}
    _,_,mods=_modules(inputs['assets']);collector=mods['collector']
    release=dict(schema='frw.ordinary-calc.namespace-launch-custody.v1',operation_id=inputs['operation_id'],nonce=inputs['nonce'],
        source_sha256=inputs['source_sha256'],source_bytes=inputs['source_bytes'],deadline_monotonic=inputs['deadline'],
        supervisor=supervisor,gdb=debugger,process=process,symbols=symbols,namespaces=ns,
        generation_index_sha256=inputs['custody']['generation_index_sha256'],launch_environment_sha256=sha(canonical(env)),
        private_roots=[dict(path=path,stamp=collector.stamp(os.stat(path,follow_symlinks=False))) for path in sorted(roots)],resource_limits=LIMITS)
    need(proc(actual['pid'])==actual and proc(debugger['pid'])==debugger,'ordinary_observer_launch_birth_changed')
    return atomic(WORK/'ordinary-launch-release.json',release)


def _inputs():
    inputs=decode(private_read(WORK/'ordinary-observer-inputs.json'))
    need(inputs['schema']=='frw.ordinary-calc.observer-inputs.v1','ordinary_observer_input_schema')
    cfg=decode(read_ref(inputs['config_ref'],source=False))
    need(cfg==inputs['config'],'ordinary_observer_config_changed')
    _fixed_assets(inputs['assets']);_fixed_font(inputs['font_view'])
    return inputs


def _bind_source(inputs):
    raw=private_read(WORK/'input.ods',1000000)
    need(len(raw)==inputs['source_bytes'] and sha(raw)==inputs['source_sha256'],'ordinary_observer_current_source')
    return raw


def _bind_launch(inputs,process,symbols, *, terminal=False):
    release=decode(private_read(WORK/'ordinary-launch-release.json',32768))
    supervisor,ns=namespace_context()
    need(release['schema']=='frw.ordinary-calc.namespace-launch-custody.v1'
         and release['operation_id']==inputs['operation_id'] and release['nonce']==inputs['nonce']
         and release['source_sha256']==inputs['source_sha256'] and release['source_bytes']==inputs['source_bytes']
         and release['deadline_monotonic']==inputs['deadline'] and release['process']==process and release['symbols']==symbols
         and release['supervisor']==supervisor and release['namespaces']==ns
         and release['generation_index_sha256']==inputs['custody']['generation_index_sha256'],
         'ordinary_observer_current_custody_binding')
    if terminal:
        need(not os.path.lexists('/proc/%d'%process['pid']) and not os.path.lexists('/proc/%d'%process['gdb_pid']),
             'ordinary_observer_terminal_original_or_GDB_present')
    else:
        actual=proc(process['pid']);debugger=proc(process['gdb_pid'])
        need(actual==dict(pid=process['pid'],ppid=process['gdb_pid'],start_ticks=process['start_ticks'])
             and debugger==release['gdb'] and debugger['ppid']==1
             and namespaces(actual['pid'])==namespaces(debugger['pid'])==ns,
             'ordinary_observer_current_process_namespace_birth')
        _actual_stock(inputs,process['pid'])
    _bind_source(inputs)
    return release


def _helpers(trace,inputs,process):
    paper,validator,mods=_modules(inputs['assets'])
    pb,gb=inputs['paper_bundle'],inputs['gpgme_bundle']
    need(decode(read_ref(inputs['paper_bundle_ref'],source=False))==pb
         and decode(read_ref(inputs['gpgme_bundle_ref'],source=False))==gb,'ordinary_observer_helper_bundle_changed')
    pm=decode(read_ref(pb['manifest_ref'],source=False));gm=decode(read_ref(gb['manifest_ref'],source=False))
    paper.validate_manifest(pm);paper.validate_runtime(pb['runtime'],pm)
    validator.validate_bundle(gb,gm,mods['policy'],mods['collector'])
    pe=paper.validate_closed(trace['load_dependency'],pb['runtime'],process)
    ge=validator.validate_evidence(trace['gpgme_engine_init'],gb['runtime'],process,manifest=gm)
    need(decode(private_read(gb['evidence_path']))==ge and ge['reaper']==proc(1),'ordinary_observer_helper_evidence_current')
    children=[c['pid'] for c in pe['children']]
    children += [c['identity']['pid'] for invocation in ge['invocations'] for c in invocation['children']]
    need(all(not os.path.lexists('/proc/%d'%pid) for pid in children),'ordinary_observer_helper_child_present')
    need(pm['source_sha256']==inputs['source_sha256'] and all(pb['runtime'][k]==gb['runtime'][k] for k in
         ('operation_id','nonce','source_sha256','marker_path','operation_deadline_monotonic')),
         'ordinary_observer_dynamic_source_helper_join')
    return pe,ge


def _font_paths(tag):
    need(tag in ('loaded','closed'),'ordinary_observer_font_tag')
    return {kind:WORK/('font-runtime-'+tag+'-'+kind+'.json') for kind in ('request','proof','release','accepted')}


def _font_projection(proof,inputs):
    baseline=decode(read_ref(inputs['font_view']['baseline'],limit=4*1024*1024))
    env=baseline['view']['environment']
    need(type(env) is dict and set(env)==set(FONT_KEYS),'ordinary_observer_font_baseline_environment')
    rows=proof['font_environment']
    need(type(rows) is list and len(rows)==15 and [r.get('key') for r in rows]==list(FONT_KEYS),
         'ordinary_observer_font_exact15')
    for row in rows:
        expected=sha(env[row['key']].encode()) if env[row['key']] is not None else None
        need(set(row)=={'key','value_sha256'} and row['value_sha256']==expected,'ordinary_observer_font_environment_drift')
    return env


def _validate_font_proof(request,proof,inputs,process,tag):
    sequence=0 if tag=='loaded' else 1
    boundary=('AFTER_LOAD_BEFORE_QUERY','AFTER_READONLY_CLOSE')[sequence]
    need(set(request)=={'schema','operation_id','nonce','boundary','sequence','process','supervisor','deadline_monotonic','requested_monotonic'}
         and request['schema']=='frw.calc.font-runtime-request.v1' and request['operation_id']==inputs['operation_id']
         and request['nonce']==inputs['nonce'] and request['boundary']==boundary
         and type(request['sequence']) is int and request['sequence']==sequence and request['process']==process
         and request['supervisor']==proc(1) and request['deadline_monotonic']==inputs['deadline']
         and type(request['requested_monotonic']) in (int,float) and math.isfinite(request['requested_monotonic'])
         and 0<request['requested_monotonic']<inputs['deadline'],'ordinary_observer_font_request_binding')
    need(set(proof)=={'schema','operation_id','nonce','boundary','sequence','process','supervisor','request_ref','phase','records_count',
         'stopped_thread_count','source_class','adapter_ref','libc_sha256','font_environment','scope','actual_M','runtime_attested'},
         'ordinary_observer_font_proof_schema')
    expected_phase=dict(nonce=inputs['nonce'],phase='IDLE' if sequence==0 else 'CLOSED',index=None,digit=None)
    for key in ('operation_id','nonce','boundary','sequence','process','supervisor'):
        need(proof[key]==request[key],'ordinary_observer_font_proof_binding')
    need(proof['schema']=='frw.calc.current-font-environment.v1' and proof['phase']==expected_phase
         and type(proof['records_count']) is int and proof['records_count']==sequence*10
         and type(proof['stopped_thread_count']) is int and 1<=proof['stopped_thread_count']<=512
         and proof['source_class']=='PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON'
         and proof['adapter_ref']==inputs['assets']['paper_adapter']
         and proof['libc_sha256']=='9941dc28e68bc5fd788d9cd024c69e68c791d63799e7538a97b6040dd9f50fb6'
         and proof['scope']=='THIS_ALL_STOP_POINT_ONLY_NO_CONTINUOUS_ENVIRONMENT_CLAIM'
         and proof['actual_M'] is None and proof['runtime_attested'] is False,'ordinary_observer_font_proof_values')
    env=_font_projection(proof,inputs)
    return env


def _font_pair(tag,inputs,process):
    paths=_font_paths(tag);raws={kind:private_read(path,32768) for kind,path in paths.items()}
    values={kind:decode(raw) for kind,raw in raws.items()}
    request,proof,release,accepted=(values[k] for k in ('request','proof','release','accepted'))
    env=_validate_font_proof(request,proof,inputs,process,tag)
    boundary=request['boundary']
    request_ref,proof_ref=ref(paths['request'],raws['request']),ref(paths['proof'],raws['proof'])
    view_path=WORK/('font-view-after-load.json' if tag=='loaded' else 'font-view-after-close.json')
    view_raw=private_read(view_path,32768);view=decode(view_raw)
    expected_release=dict(schema='frw.calc.font-runtime-release.v1',**{k:request[k] for k in
        ('operation_id','nonce','boundary','sequence','process')},request_ref=request_ref,proof_ref=proof_ref,font_view_ref=ref(view_path,view_raw))
    expected_accepted=dict(schema='frw.calc.font-runtime-accepted.v1',**{k:request[k] for k in
        ('operation_id','nonce','boundary','sequence','process')},release_ref=ref(paths['release'],raws['release']),
        status='HELD_STOP_RELEASE_VALIDATED_NO_RESUME_CLAIM')
    need(proof['request_ref']==request_ref and release==expected_release and accepted==expected_accepted
         and view['schema']=='frw.ordinary-calc.font-view-CAS.v1' and view['boundary']==boundary
         and view['process']==process and view['supervisor']==proc(1)
         and view['view_sha256']==inputs['font_view']['expected_view_sha256']
         and view['base_view_sha256']==inputs['font_view']['base_view_sha256']
         and view['proof_ref']==proof_ref and view['font_environment']==env
         and view['observation']['status']=='metadata_cas_pass_with_critical_rehash'
         and view['actual_M'] is None,'ordinary_observer_font_pair_CAS')
    return dict(request_ref=request_ref,proof_ref=proof_ref,view_ref=ref(view_path,view_raw),accepted_ref=ref(paths['accepted'],raws['accepted']))


def request_boundary(tag, *, work,nonce,process,symbols,source_sha256,deadline):
    """Inner fixed synchronous phase handoff; no runtime flags can release it."""
    need(Path(work)==WORK,'ordinary_observer_boundary_work');inputs=_inputs();clock(deadline)
    need(nonce==inputs['nonce'] and source_sha256==inputs['source_sha256'] and deadline==inputs['deadline'],
         'ordinary_observer_boundary_operation')
    _bind_launch(inputs,process,symbols)
    boundary='AFTER_LOAD_BEFORE_QUERY' if tag=='loaded' else 'AFTER_READONLY_CLOSE'
    request=dict(schema='frw.ordinary-calc.boundary-request.v1',tag=tag,boundary=boundary,nonce=nonce,
        process=process,symbols=symbols,source_sha256=source_sha256,deadline=deadline)
    _font_paths(tag)
    accepted_path=WORK/('ordinary-boundary-accepted-'+tag+'.json')
    need(not os.path.lexists(accepted_path),'ordinary_observer_future_boundary_acceptance')
    request_ref=atomic(WORK/('ordinary-boundary-request-'+tag+'.json'),request)
    while not os.path.lexists(accepted_path):
        clock(deadline);_bind_launch(inputs,process,symbols)
        time.sleep(min(.005,max(0,deadline-time.monotonic())))
    accepted=decode(private_read(accepted_path,32768));pair=_font_pair(tag,inputs,process)
    need(accepted=={**request,'schema':'frw.ordinary-calc.boundary-accepted.v1','request_ref':request_ref,
        'font_pair':pair,'status':'CURRENT_HELD_STOP_FONT_CAS_ACCEPTED'},
        'ordinary_observer_boundary_acceptance_binding')
    clock(deadline);return accepted


def service_boundary(work, tag, *, inputs,child):
    """Actual PID1 held all-stop, fixed FontCAS and exact release construction."""
    need(Path(work)==WORK and os.getpid()==1,'ordinary_observer_boundary_owner');clock(inputs['deadline'])
    _font_paths(tag)
    path=WORK/('ordinary-boundary-request-'+tag+'.json');raw=private_read(path,32768);request=decode(raw)
    native,symbols=request['process'],request['symbols'];_bind_launch(inputs,native,symbols)
    boundary='AFTER_LOAD_BEFORE_QUERY' if tag=='loaded' else 'AFTER_READONLY_CLOSE';sequence=0 if tag=='loaded' else 1
    need(request==dict(schema='frw.ordinary-calc.boundary-request.v1',tag=tag,boundary=boundary,nonce=inputs['nonce'],
        process=native,symbols=symbols,source_sha256=inputs['source_sha256'],deadline=inputs['deadline']),
        'ordinary_observer_boundary_request')
    expected_phase=dict(nonce=inputs['nonce'],phase='IDLE' if sequence==0 else 'CLOSED',index=None,digit=None)
    need(decode(private_read(WORK/'phase.json',4096))==expected_phase,'ordinary_observer_boundary_phase')
    trace=decode(private_read(WORK/'native-trace.json'));need(trace['process']==native and trace['symbols']==symbols
        and trace['error'] is None and len(trace['records'])==sequence*10,'ordinary_observer_boundary_trace')
    _helpers(trace,inputs,native)
    if tag=='loaded':
        marker=decode(private_read(WORK/'load-dependency.json',4096))
        need(marker['state']=='LOAD_OPEN' and marker['nonce']==inputs['nonce'],'ordinary_observer_load_window')
        marker['state']='LOAD_CLOSED';replace(WORK/'load-dependency.json',marker)
    paths=_font_paths(tag)
    need(all(not os.path.lexists(p) for p in paths.values()),'ordinary_observer_font_prefilled')
    before=proc(native['pid']);fd=os.pidfd_open(native['pid'],0)
    try:
        need(proc(native['pid'])==before and child.pid==native['gdb_pid'] and child.poll() is None,
             'ordinary_observer_pidfd_birth')
        fr=dict(schema='frw.calc.font-runtime-request.v1',operation_id=inputs['operation_id'],nonce=inputs['nonce'],
            boundary=boundary,sequence=sequence,process=native,supervisor=proc(1),deadline_monotonic=inputs['deadline'],
            requested_monotonic=time.monotonic())
        frref=atomic(paths['request'],fr);signal.pidfd_send_signal(fd,signal.SIGSTOP,None,0)
    finally:os.close(fd)
    while not os.path.lexists(paths['proof']):
        clock(inputs['deadline']);need(child.poll() is None and proc(native['pid'])==before,'ordinary_observer_font_child_lost')
        time.sleep(min(.005,max(0,inputs['deadline']-time.monotonic())))
    proofraw=private_read(paths['proof'],32768);proof=decode(proofraw);proofref=ref(paths['proof'],proofraw)
    need(proof['process']==native and proof['request_ref']==frref and proof['boundary']==boundary,
         'ordinary_observer_font_held_proof')
    env=_validate_font_proof(fr,proof,inputs,native,tag);font=inputs['font_view']
    # Fixed trusted component observer runs while GDB still holds this all-stop.
    # The inner cannot resume until the later font release+accepted handoff.
    clock(inputs['deadline'])
    from hermes_cli.friday_workspace_calc_native_factory import _observe_components
    components=_observe_components(native,require_mapped=(tag=='loaded'))
    clock(inputs['deadline'])
    atomic(WORK/('ordinary-components-'+tag+'.json'),dict(schema='frw.ordinary-calc.held-components.v1',
        source_sha256=inputs['source_sha256'],source_bytes=inputs['source_bytes'],nonce=inputs['nonce'],
        process=native,symbols=symbols,barrier=boundary,font_proof_ref=proofref,
        components=components,actual_M=None))
    consumer=load_module(font['consumer'],'frw_ordinary_fixed_font_CAS')
    baseline=decode(read_ref(font['baseline'],limit=4*1024*1024));derived=decode(read_ref(font['derived_cache'],limit=4*1024*1024))
    read_ref(font['provenance_ref'],limit=4*1024*1024)
    current=consumer.validate_effective_font_config_view(baseline,expected_view_digest=font['expected_view_sha256'],derived_cache=derived)
    clock(inputs['deadline'])
    need(current['view_sha256']==font['expected_view_sha256'] and current['observation']['status']=='metadata_cas_pass_with_critical_rehash'
         and proc(native['pid'])==before and private_read(paths['proof'],32768)==proofraw
         and private_read(path,32768)==raw and decode(private_read(WORK/'phase.json',4096))==expected_phase,
         'ordinary_observer_font_CAS_or_held_boundary_changed')
    view=dict(schema='frw.ordinary-calc.font-view-CAS.v1',boundary=boundary,process=native,supervisor=proc(1),
        view_sha256=current['view_sha256'],base_view_sha256=font['base_view_sha256'],proof_ref=proofref,
        font_environment=env,observation=current['observation'],actual_M=None)
    viewref=atomic(WORK/('font-view-after-load.json' if tag=='loaded' else 'font-view-after-close.json'),view)
    release=atomic(paths['release'],dict(schema='frw.calc.font-runtime-release.v1',**{k:fr[k] for k in
        ('operation_id','nonce','boundary','sequence','process')},request_ref=frref,proof_ref=proofref,font_view_ref=viewref))
    while not os.path.lexists(paths['accepted']):
        clock(inputs['deadline']);need(child.poll() is None,'ordinary_observer_font_GDB_lost')
        time.sleep(min(.005,max(0,inputs['deadline']-time.monotonic())))
    pair=_font_pair(tag,inputs,native)
    return atomic(WORK/('ordinary-boundary-accepted-'+tag+'.json'),{**request,'schema':'frw.ordinary-calc.boundary-accepted.v1','request_ref':ref(path,raw),
        'font_pair':pair,'status':'CURRENT_HELD_STOP_FONT_CAS_ACCEPTED'})


def replace(path,value):
    # Only the already-bound LOAD marker advances; no fresh clock or reopen.
    path=Path(path);need(path==WORK/'load-dependency.json','ordinary_observer_replace_scope')
    pending=path.with_name(path.name+'.pending');raw=canonical(value)
    fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(pending,path)


def verify_extensions(raw, *, work,nonce,process,symbols,source_sha256,deadline,terminal):
    """Validate every required helper extension before canonical base projection.

    LIVE never requires exit or the second postclose Font barrier. TERMINAL
    requires both owned launch processes and every observed helper absent.
    This function must run INSIDE the original ordinary namespace while PID1
    still lives; host verification must additionally consume _run cleanup.
    """
    need(Path(work)==WORK and type(terminal) is bool,'ordinary_observer_verify_context')
    clock(deadline);inputs=_inputs()
    need(inputs['nonce']==nonce and inputs['source_sha256']==source_sha256 and inputs['deadline']==deadline,
         'ordinary_observer_verify_operation')
    need(type(raw) is bytes and private_read(WORK/'native-trace.json')==raw,'ordinary_observer_original_trace_CAS')
    trace=decode(raw);expected=BASE|EXTENSIONS|({'own_inferior_absent'} if terminal else set())
    need(type(trace) is dict and set(trace)==expected,'ordinary_observer_all_extensions_required')
    need(trace['schema']=='frw.native-return-trace.v1' and trace['kind']=='OFFICE_UNADMITTED'
         and trace['process']==process and trace['symbols']==symbols and trace['nonce']==nonce
         and trace['error'] is None and trace['actual_M'] is None and trace['runtime_attested'] is False,
         'ordinary_observer_trace_binding_or_error')
    need(type(trace['records']) is list and len(trace['records'])==10,'ordinary_observer_exact_ten_pair_snapshot')
    _bind_launch(inputs,process,symbols,terminal=terminal);_helpers(trace,inputs,process)
    marker=decode(private_read(WORK/'load-dependency.json',4096));pr=inputs['paper_bundle']['runtime']
    need(marker==dict(schema='frw.calc.load-dependency-window.v1',state='LOAD_CLOSED',**{k:pr[k] for k in
        ('operation_id','nonce','source_sha256','manifest_ref','operation_deadline_monotonic')}),'ordinary_observer_closed_load_marker')
    _font_pair('loaded',inputs,process)
    if terminal:
        need(trace['status']=='COMPLETE_UNATTESTED' and type(trace['exit_code']) is int and trace['exit_code']==0
             and trace['own_inferior_absent'] is True,'ordinary_observer_terminal_state')
        _font_pair('closed',inputs,process)
        need(decode(private_read(WORK/'phase.json',4096))==dict(nonce=nonce,phase='CLOSED',index=None,digit=None),
             'ordinary_observer_terminal_closed_phase')
        # Explicit NEW ordinary output admission; old no-output wrappers remain frozen.
        output=private_read(WORK/'out/input.xlsx',16*1024*1024)
        need(output[:4]==b'PK\x03\x04','ordinary_observer_terminal_stock_output')
    else:
        need(trace['status']=='TEN_CALLS_OBSERVED_UNRELEASED' and trace['exit_code'] is None
             and not os.path.lexists(WORK/'out/input.xlsx')
             and decode(private_read(WORK/'phase.json',4096))==dict(nonce=nonce,phase='METRIC',index=9,digit='9'),
             'ordinary_observer_live_pre_store_phase')
        need(not os.path.lexists(_font_paths('closed')['request']),'ordinary_observer_live_future_close')
    need(private_read(WORK/'native-trace.json')==raw,'ordinary_observer_original_trace_changed')
    clock(deadline)
    return canonical({key:value for key,value in trace.items() if key not in EXTENSIONS})
