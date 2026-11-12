import os,sys,pathlib,subprocess,resource,json,datetime,time,hashlib
os.umask(0o077);B=pathlib.Path(__file__).resolve().parent;out=B/'checks/r1';out.mkdir(mode=0o700)
cpus=sorted(os.sched_getaffinity(0))[:2]
def limits():
 os.sched_setaffinity(0,cpus);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
started=datetime.datetime.now().astimezone().isoformat();mono=time.monotonic();r0=resource.getrusage(resource.RUSAGE_CHILDREN)
p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(B/'pure_controls.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limits)
state='CLOSED';timedout=False
try:stdout,stderr=p.communicate(timeout=90)
except subprocess.TimeoutExpired:
 timedout=True;p.kill();stdout,stderr=p.communicate();state='TIMEOUT_CLOSED'
r1=resource.getrusage(resource.RUSAGE_CHILDREN);(out/'stdout.json').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
result={'started_moscow':started,'finished_moscow':datetime.datetime.now().astimezone().isoformat(),'wall_seconds':time.monotonic()-mono,'cpu_seconds':r1.ru_utime+r1.ru_stime-r0.ru_utime-r0.ru_stime,'maxrss_KiB':r1.ru_maxrss,'pid':p.pid,'returncode':p.returncode,'state':state,'timeout':timedout,'caps':{'enforced_wall':90,'enforced_RLIMIT_CPU':60,'enforced_RLIMIT_AS':536870912,'affinity':cpus},'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()};(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(p.returncode)
