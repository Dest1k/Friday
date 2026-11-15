from pathlib import Path
import os, sys, json, hashlib, subprocess, resource, time, stat, fcntl, importlib.util, select, signal
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path('/home/jericho/.cache/FRW-ASTRA-PAPER-HELPER-NONOFFICE-TOPOLOGY-20261115')
CODE=ROOT/'code'; WORK=ROOT/'work'
HELPER=Path('/home/jericho/.cache/FRW-ASTRA-CALC-COMBINED-OBSERVER-DIAGNOSTIC-R3-20261115/outer/deps/metric_namespace.py')
BINDING=Path('/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/python-uno-binding/root')
LOCK=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
EXPECTED_HELPER='2223ffcee689611fa1ee8f19cb62e80a2a417f93affa7a28b4d3dc15acddea4b'
def now():return datetime.now(ZoneInfo('Europe/Moscow')).isoformat()
def sha(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(path):
    st=os.stat(path)
    return {'path':str(path),'sha256':sha(path),'dev':st.st_dev,'ino':st.st_ino,'size':st.st_size,'mode':oct(st.st_mode),'uid':st.st_uid}
def proc(pid):
    raw=Path('/proc',str(pid),'stat').read_text()
    fields=raw.rsplit(')',1)[1].split()
    return {'pid':pid,'ppid':int(fields[1]),'start_ticks':int(fields[19]),'state':fields[0]}
def own_identity(record):
    try:v=proc(record['pid'])
    except FileNotFoundError:return None
    if v['start_ticks']!=record['start_ticks']:raise RuntimeError('host_pid_reuse_no_signal')
    return v
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(10,10))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
    os.setsid()

RESULT={'schema':'frw.Root.own-popen-topology-result.v1','assignment':'ASTRA-PAPER-HELPER-NONOFFICE-TOPOLOGY-20261115#1',
        'started_moscow':now(),'effect_count':0,'actual_M':None,
        'budget':{'wall_seconds':20,'cpu_seconds_per_inherited_process':10,'output_bytes':1024*1024,'core_bytes':0,'RLIMIT_AS':None,'gdb_stop_limit':32},
        'scope':'one nonOffice C fixture fixed stock popen in reviewed ordinary namespace; no Office/UNO/document/model/send/service/Git effects',
        'acceptance':None,'error':None}
begin=time.monotonic(); known={}; maxrss={}; p=None; reaped=False; lockfd=None; capture=bytearray(); rusage=None
try:
    if sha(HELPER)!=EXPECTED_HELPER:raise RuntimeError('namespace_helper_pin')
    RESULT['tool_pins_before']={k:pin(v) for k,v in {'namespace_helper':HELPER,'gdb':Path('/usr/bin/gdb'),'bwrap':Path('/usr/bin/bwrap'),'gcc':Path('/usr/bin/cc'),'dash':Path('/usr/bin/dash'),'paperconf':Path('/usr/bin/paperconf')}.items()}
    if RESULT['tool_pins_before']['dash']['sha256']!='c626229526bb58ec2d0f585f3c3ae1412e6f973b4353385042d11c38d8426917':raise RuntimeError('dash_pin')
    if RESULT['tool_pins_before']['paperconf']['sha256']!='cce22660a60a113e52288cb55ea04cd0ee96ec1f1a19ba08aa120dd118608103':raise RuntimeError('paperconf_pin')
    compile_result=subprocess.run(['/usr/bin/cc','-std=gnu11','-O0','-g','-Wall','-Wextra','-Werror','-o',str(CODE/'fixture'),str(CODE/'fixture.c')],capture_output=True,timeout=15)
    RESULT['compile']={'exit':compile_result.returncode,'output_bytes':len(compile_result.stdout)+len(compile_result.stderr)}
    if compile_result.returncode or compile_result.stdout or compile_result.stderr:raise RuntimeError('compile_nonclean')
    RESULT['fixture_binary_before_removal']=pin(CODE/'fixture')
    RESULT['source_pins']={k:pin(v) for k,v in {'C':CODE/'fixture.c','gdb_script':CODE/'gdb_trace.py','runner':ROOT/'runner.py'}.items()}
    for name in ('tmp','cache','config','runtime'):(WORK/name).mkdir(mode=0o700,exist_ok=True)
    available={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name,_,value=line.partition(':')
        if name in ('MemAvailable','MemTotal'):available[name]=value.strip()
    RESULT['resources_before']={'memory':available,'own_affinity_cpu_count':len(os.sched_getaffinity(0)),
                                'glibc_host':os.confstr('CS_GNU_LIBC_VERSION')}
    lockfd=os.open(LOCK,os.O_RDWR|os.O_CLOEXEC|os.O_NOFOLLOW)
    a=os.fstat(lockfd);b=os.stat(LOCK,follow_symlinks=False)
    if not stat.S_ISREG(a.st_mode) or a.st_uid!=os.getuid() or a.st_mode&0o077 or (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino):raise RuntimeError('lock_identity')
    RESULT['lock_identity']={'dev':a.st_dev,'ino':a.st_ino,'uid':a.st_uid,'mode':oct(a.st_mode)}
    fcntl.flock(lockfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    RESULT['lock_acquired_moscow']=now()
    spec=importlib.util.spec_from_file_location('metric_namespace',HELPER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    command=['/usr/bin/gdb','--quiet','--nx','--nh','--batch','--init-eval-command','set auto-load off',
             '--init-eval-command','set startup-with-shell off',
             '--init-eval-command','set debuginfod enabled off',
             '--eval-command','set environment DEBUGINFOD_URLS',
             '--eval-command','source '+str(CODE/'gdb_trace.py'),'--args',str(CODE/'fixture')]
    argv=module.build_namespace(writable=WORK,readonly=[CODE],binding_root=BINDING,command=command)
    RESULT['namespace_argv_sha256']=hashlib.sha256(json.dumps(argv,separators=(',',':')).encode()).hexdigest()
    (ROOT/'namespace-argv.json').write_text(json.dumps(argv)+'\n');(ROOT/'namespace-argv.json').chmod(0o600)
    RESULT['live_started_moscow']=now();live_begin=time.monotonic()
    p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,preexec_fn=limits)
    RESULT['effect_count']=1
    known[p.pid]=proc(p.pid);os.set_blocking(p.stdout.fileno(),False)
    while True:
        for record in list(known.values()):
            current=own_identity(record)
            if current is None:continue
            path=Path('/proc',str(record['pid']))
            try:
                status=(path/'status').read_text()
                for line in status.splitlines():
                    if line.startswith(('VmRSS:','VmHWM:')):
                        key=line.split(':',1)[0];v=int(line.split()[1])
                        maxrss.setdefault(str(record['pid']),{})[key]=max(v,maxrss.get(str(record['pid']),{}).get(key,0))
                nspid=next((line.split()[1:] for line in status.splitlines() if line.startswith('NSpid:')),[])
                record['namespace_pids']=[int(v) for v in nspid]
                if 'exe' not in record:
                    record['exe']=os.readlink(path/'exe')
                    record['exe_sha256']=sha(path/'exe')
                children=(path/'task'/str(record['pid'])/'children').read_text()
                if len(children)>1024:raise RuntimeError('own_children_bound')
                for word in children.split():
                    child=int(word)
                    if child not in known:
                        item=proc(child)
                        if item['ppid']!=record['pid']:raise RuntimeError('host_child_lineage')
                        known[child]=item
            except FileNotFoundError:pass
            except ProcessLookupError:pass
        readable,_,_=select.select([p.stdout],[],[],0.01)
        if readable:
            try:data=os.read(p.stdout.fileno(),65536)
            except BlockingIOError:data=b''
            capture.extend(data)
            if len(capture)>1024*1024:raise RuntimeError('output_bound')
        waited,status,usage=os.wait4(p.pid,os.WNOHANG)
        if waited:
            reaped=True;p.returncode=os.waitstatus_to_exitcode(status);rusage=usage
            while True:
                try:data=os.read(p.stdout.fileno(),65536)
                except BlockingIOError:break
                if not data:break
                capture.extend(data)
                if len(capture)>1024*1024:raise RuntimeError('output_bound')
            break
        if time.monotonic()-live_begin>20:raise RuntimeError('wall_budget')
    RESULT['live_finished_moscow']=now();RESULT['live_seconds']=time.monotonic()-live_begin
    RESULT['exit']=p.returncode
    if (WORK/'trace.json').exists():RESULT['trace_ref']=pin(WORK/'trace.json')
    trace=json.loads((WORK/'trace.json').read_text())
    exits=[e for e in trace['events'] if e['kind']=='exited']
    RESULT['terminal_exits']=[{'inferior':e['inferior'],'exit_code':e['exit_code'],'event_id':e['event_id']} for e in exits]
    RESULT['topology']=trace['known']
    RESULT['trace_status']=trace['status'];RESULT['trace_error']=trace['error']
    RESULT['acceptance']='TOPOLOGY_OBSERVED' if p.returncode==0 and trace['status']=='TERMINAL' and trace['error'] is None and trace['all_gdb_inferiors_pid0_after_cleanup'] else 'FAILED'
except BaseException as e:
    RESULT['error']=type(e).__name__+':'+str(e)[:300]
    RESULT['acceptance']='FAILED'
finally:
    RESULT['cleanup_signaled_host_pids']=[]
    for record in reversed(list(known.values())):
        try:
            if own_identity(record) is not None:
                os.kill(record['pid'],signal.SIGKILL)
                RESULT['cleanup_signaled_host_pids'].append(record['pid'])
        except (FileNotFoundError,ProcessLookupError):pass
        except BaseException as e:RESULT.setdefault('cleanup_errors',[]).append(type(e).__name__+':'+str(e)[:100])
    if p is not None and not reaped:
        try:
            _,status,rusage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status);reaped=True
        except ChildProcessError:pass
    RESULT['host_own_processes']=list(known.values());RESULT['host_RSS_peak_KiB']=maxrss
    RESULT['bwrap_reaped']=reaped
    RESULT['host_known_absent']={str(pid):not Path('/proc',str(pid)).exists() for pid in known}
    if rusage is not None:RESULT['wait4_resources']={'user_cpu_seconds':rusage.ru_utime,'system_cpu_seconds':rusage.ru_stime,'maxrss_KiB':rusage.ru_maxrss}
    if any(not absent for absent in RESULT['host_known_absent'].values()):RESULT['acceptance']='FAILED';RESULT['cleanup_incomplete']=True
    (ROOT/'gdb-stdout.log').write_bytes(capture);(ROOT/'gdb-stdout.log').chmod(0o600)
    RESULT['stdout_ref']=pin(ROOT/'gdb-stdout.log')
    RESULT['tool_pins_after']={}
    for key,entry in RESULT.get('tool_pins_before',{}).items():RESULT['tool_pins_after'][key]=pin(entry['path'])
    RESULT['unchanged_tool_pins']=RESULT.get('tool_pins_before')==RESULT['tool_pins_after']
    binary=CODE/'fixture'
    if binary.exists():
        RESULT['binary_unchanged_before_removal']=pin(binary)==RESULT.get('fixture_binary_before_removal')
        binary.unlink()
    RESULT['binary_removed']=not binary.exists()
    if lockfd is not None:os.close(lockfd)
    RESULT['finished_moscow']=now();RESULT['elapsed_seconds']=time.monotonic()-begin
    (ROOT/'RESULT.json').write_text(json.dumps(RESULT,indent=2,sort_keys=True)+'\n');(ROOT/'RESULT.json').chmod(0o600)
    (ROOT/'RESULT.sha256').write_text(sha(ROOT/'RESULT.json')+'  RESULT.json\n');(ROOT/'RESULT.sha256').chmod(0o600)
    print(json.dumps({'acceptance':RESULT['acceptance'],'error':RESULT['error'],'trace_status':RESULT.get('trace_status'),'trace_error':RESULT.get('trace_error'),'result_sha256':sha(ROOT/'RESULT.json'),'elapsed_seconds':RESULT['elapsed_seconds']}))
