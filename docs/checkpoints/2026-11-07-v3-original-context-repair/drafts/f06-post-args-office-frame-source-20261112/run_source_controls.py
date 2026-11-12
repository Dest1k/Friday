"""Bounded source controls; never starts Office or an admission path."""
import datetime,json,os,pathlib,resource,subprocess,sys,time
os.umask(0o077);B=pathlib.Path(__file__).resolve().parent
name=sys.argv[1];assert name in ('parent','inside','protocol','safety_delta','patch');D=B/'checks'/name;D.mkdir(mode=0o700,parents=True)
def caps():
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(8388608,8388608));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
start=time.monotonic();now=datetime.datetime.now().astimezone().isoformat();before=resource.getrusage(resource.RUSAGE_CHILDREN)
p=subprocess.Popen(['/usr/bin/python3','-I','-B',str(B/(name+'_controls.py'))],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=caps,cwd=B)
timedout=False
try:out,err=p.communicate(timeout=90)
except subprocess.TimeoutExpired:timedout=True;p.kill();out,err=p.communicate()
usage=resource.getrusage(resource.RUSAGE_CHILDREN)
(D/'stdout.json').write_bytes(out);(D/'stderr.txt').write_bytes(err)
report=dict(schema='post-args.bounded-source-control-run.v1',control=name,started_moscow=now,elapsed_wall_seconds=time.monotonic()-start,child_CPU_seconds=usage.ru_utime+usage.ru_stime-before.ru_utime-before.ru_stime,maxrss_kib=usage.ru_maxrss,limits={'wall':90,'CPU':60,'AS':536870912,'FSIZE':8388608,'affinity_two':True},pid=p.pid,exit=p.returncode,timed_out=timedout,reaped=True,proc_absent=not pathlib.Path('/proc',str(p.pid)).exists(),all_pass=p.returncode==0,source_only=True,no_Office_or_actual_input_access=True)
(D/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(0 if report['all_pass']else 1)
