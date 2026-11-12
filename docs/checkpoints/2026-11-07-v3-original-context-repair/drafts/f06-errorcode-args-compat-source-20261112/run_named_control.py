"""Bounded owner-only pure source/check subprocess, never a product launcher."""
import os
os.umask(0o077)
import sys,pathlib,subprocess,resource,json,datetime,time,hashlib,signal
B=pathlib.Path(__file__).resolve().parent;name=sys.argv[1];script=sys.argv[2]
assert name in ('composition','reviewer-delta','reviewer-delta-r2','final-protocol','final-protocol-r2') and script in ('compose_controls.py','parent_delta_controls.py','final_protocol_controls.py')
out=B/'checks'/name;out.mkdir(mode=0o700);cpus=sorted(os.sched_getaffinity(0))[:2]
def limits():
 os.sched_setaffinity(0,cpus);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
start=datetime.datetime.now().astimezone().isoformat();mono=time.monotonic();r0=resource.getrusage(resource.RUSAGE_CHILDREN)
p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(B/script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limits,start_new_session=True)
timeout=False
try:stdout,stderr=p.communicate(timeout=90)
except subprocess.TimeoutExpired:
 timeout=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
r1=resource.getrusage(resource.RUSAGE_CHILDREN);(out/'stdout.json').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
r={'command':['/usr/bin/python3','-I','-B','-S',str(B/script)],'started_moscow':start,'finished_moscow':datetime.datetime.now().astimezone().isoformat(),'wall_seconds':time.monotonic()-mono,'cpu_seconds':r1.ru_utime+r1.ru_stime-r0.ru_utime-r0.ru_stime,'maxrss_KiB':r1.ru_maxrss,'pid':p.pid,'returncode':p.returncode,'timeout':timeout,'waited_reaped':True,'caps':{'enforced_wall':90,'enforced_RLIMIT_CPU':60,'enforced_RLIMIT_AS':536870912,'affinity':cpus},'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()};(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(p.returncode)
