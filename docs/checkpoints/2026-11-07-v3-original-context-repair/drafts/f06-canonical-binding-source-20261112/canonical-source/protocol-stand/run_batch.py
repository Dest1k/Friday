"""Finite outer resource owner for synthetic source protocol controls."""
import datetime,hashlib,json,os,resource,signal,subprocess,sys,time
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent
P=B.parent
def encoded(v):return (json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,v):path.write_bytes(encoded(v));path.chmod(0o600)
def snapshot(name,root):
    target=B/name;target.mkdir(mode=0o700)
    pins={}
    for leaf in ('root_bind_existing_consumer_once.py','f06_source.py','current207.py','f06_footer.py.txt'):
        raw=(root/leaf).read_bytes();p=target/leaf;p.write_bytes(raw);p.chmod(0o600)
        pins[leaf]={'bytes':len(raw),'sha256':sha(raw)}
    write(target/'PINS.json',pins)
    return pins
cpus=sorted(os.sched_getaffinity(0))[:2]
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,cpus)
if sys.argv[1]=='snapshot':
    print(json.dumps({'fixed':snapshot('fixed-source',P/'candidate/first'),'old':snapshot('old-source',P/'before/first')}));sys.exit()
controls=sys.argv[1:]
out=B/'runs';out.mkdir(mode=0o700,exist_ok=True)
results=[]
for requested in controls:
    name,_,case=requested.partition('@');case=case or name
    source='old-source' if name=='old_reconstruction' else 'fixed-source'
    started=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)));t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(B/'control.py'),case,name,source],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
    timeout=False
    try:stdout,stderr=p.communicate(timeout=90)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timeout=True
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    (out/(case+'.stdout')).write_bytes(stdout);(out/(case+'.stderr')).write_bytes(stderr)
    row={'control':name,'pid':p.pid,'reaped':True,'proc_absent':not Path('/proc',str(p.pid)).exists(),'exit_code':p.returncode,'timeout':timeout,'started_at_moscow':started.isoformat(),'completed_at_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'wall_seconds':time.monotonic()-t,'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'child_max_rss_kib_cumulative':after.ru_maxrss,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'limits':{'wall':90,'CPU':60,'AS':512*1024**2,'FSIZE':64*1024**2,'affinity':cpus},'claim':'Per-control process RLIMIT and two-CPU affinity, no aggregate cgroup claim'}
    write(out/(case+'.resource.json'),row);results.append(row)
    if p.returncode!=0 or timeout:
        print(json.dumps(row));print(stderr.decode()[-4000:]);print('STOP_BATCH_COMMON_HARNESS_FAILURE');break
    result=json.loads((B/'cases'/case/'RESULT.json').read_bytes())
    print(json.dumps({'control':name,'failure':result['failure'],'boundary':result['boundary'],'loads':result['events'],'wall_seconds':row['wall_seconds']}),flush=True)
    if (name=='positive' and not result['boundary']) or (name=='old_reconstruction' and result['failure']!='ValueError:F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE'):
        print('STOP_BATCH_COMMON_HARNESS_FAILURE');break
write(out/('BATCH-'+str(time.time_ns())+'.json'),results)
