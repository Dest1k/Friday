"""Finite owned pure-worker groups: 90wall/60CPU/512MiB/two CPUs each."""
import datetime,hashlib,json,os,resource,signal,subprocess,sys,time
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent
LEAVES=('root_bind_dispatch_once.py','f06_source.py','current_root.py','f06_footer.py.txt','first_ingress.py')
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def write(p,v):p.write_bytes(encoded(v));p.chmod(0o600)
cpus=sorted(os.sched_getaffinity(0))[:2]
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(28*1024**2,28*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,cpus)
if sys.argv[1]=='snapshot':
 root=B.parent/'candidate';target=B/(sys.argv[2] if len(sys.argv)>2 else 'fixed-source');target.mkdir(mode=0o700)
 pins={}
 for leaf in LEAVES:
  raw=(root/leaf).read_bytes();p=target/leaf;p.write_bytes(raw);p.chmod(0o600);pins[leaf]={'bytes':len(raw),'sha256':sha(raw)}
 write(target/'PINS.json',pins);print(json.dumps(pins));sys.exit()
out=B/'runs';out.mkdir(mode=0o700,exist_ok=True);rows=[]
for requested in sys.argv[1:]:
 name,_,tail=requested.partition('@');case,_,source=tail.partition('#');case=case or name;source=source or 'fixed-source'
 start=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)));t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
 p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(B/'control.py'),case,name,source],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
 timedout=False
 try:stdout,stderr=p.communicate(timeout=90)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timedout=True
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 for suffix,raw in (('stdout',stdout),('stderr',stderr)):
  q=out/(case+'.'+suffix);q.write_bytes(raw);q.chmod(0o600)
 row={'control':name,'case':case,'snapshot':source,'pid':p.pid,'reaped':True,'proc_absent':not Path('/proc',str(p.pid)).exists(),'exit_code':p.returncode,'timeout':timedout,'started_at_moscow':start.isoformat(),'completed_at_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'wall_seconds':time.monotonic()-t,'CPU_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'max_rss_kib_cumulative':after.ru_maxrss,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'limits':{'wall':90,'CPU':60,'AS':512*1024**2,'per_file':28*1024**2,'affinity':cpus},'claim':'Per-group limits; no aggregate cgroup claim'}
 write(out/(case+'.resource.json'),row);rows.append(row)
 if p.returncode!=0 or timedout:
  print(json.dumps(row));print(stderr.decode()[-5000:]);print('STOP_BATCH_COMMON_HARNESS_FAILURE');break
 result=json.loads((B/'cases'/case/'RESULT.json').read_bytes());print(json.dumps({'control':name,'case':case,'failure':result['failure'],'boundary':result['boundary'],'wall_seconds':row['wall_seconds']}),flush=True)
 if not result['expectation_met']:
  print('STOP_BATCH_EXPECTATION_FAILURE');break
write(out/('BATCH-'+str(time.time_ns())+'.json'),rows)
