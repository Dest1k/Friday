import datetime,hashlib,json,os,resource,signal,subprocess,sys,time
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent
name=sys.argv[1];script=sys.argv[2];out=B/'checks'/name;out.mkdir(mode=0o700,parents=True,exist_ok=False)
start=datetime.datetime.now().astimezone();before=resource.getrusage(resource.RUSAGE_CHILDREN);mono=time.monotonic();cpus=sorted(os.sched_getaffinity(0))[:2]
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,cpus)
p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(B/script)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
try:stdout,stderr=p.communicate(timeout=90);timeout=False
except subprocess.TimeoutExpired:
 os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timeout=True
end=datetime.datetime.now().astimezone();after=resource.getrusage(resource.RUSAGE_CHILDREN)
(out/'stdout').write_bytes(stdout);(out/'stderr').write_bytes(stderr)
v=dict(started_at_moscow=start.isoformat(),completed_at_moscow=end.isoformat(),elapsed_seconds=time.monotonic()-mono,cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,max_rss_kib=after.ru_maxrss,pid=p.pid,reaped=True,proc_absent=not Path('/proc',str(p.pid)).exists(),exit_code=p.returncode,timeout=timeout,caps=dict(wall_seconds=90,CPU_seconds=60,AS_bytes=512*1024**2,affinity=cpus),source_sha256=hashlib.sha256((B/script).read_bytes()).hexdigest(),stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest())
(out/'RESULT.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));print(stdout.decode()[:12000]);print(stderr.decode()[:2500])
