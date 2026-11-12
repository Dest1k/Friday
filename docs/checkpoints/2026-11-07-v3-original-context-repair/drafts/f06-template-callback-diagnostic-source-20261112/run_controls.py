"""Finite pure-source subprocess, no application/UNO imports or real inputs."""
import datetime, hashlib, json, os, resource, subprocess, sys, time
from pathlib import Path

B=Path(__file__).resolve().parent
os.umask(0o077)
name=sys.argv[1]
if name not in ("r1", "r2", "r3"):
    raise SystemExit("NAMED_SOURCE_CHECK_ONLY")
out=B/"checks"/name
out.mkdir(mode=0o700,parents=True,exist_ok=False)
cpus=sorted(os.sched_getaffinity(0))[:2]
if len(cpus)!=2:raise SystemExit("TWO_CPUS_REQUIRED")
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
    os.sched_setaffinity(0,cpus)
start=time.monotonic();stamp=datetime.datetime.now().astimezone().isoformat()
command=[sys.executable,"-I","-B",str(B/"tests/pure_controls.py")]
with (out/"stdout.json").open("xb") as stdout,(out/"stderr.log").open("xb") as stderr:
    child=subprocess.Popen(command,stdout=stdout,stderr=stderr,preexec_fn=limits)
    timeout=False
    try:rc=child.wait(timeout=90)
    except subprocess.TimeoutExpired:
        timeout=True;child.kill();rc=child.wait()
usage=resource.getrusage(resource.RUSAGE_CHILDREN)
report={"scope":"PURE_SYNTHETIC_SOURCE_NO_UNO_OFFICE_OR_REAL_INPUT","start_moscow":stamp,
        "end_moscow":datetime.datetime.now().astimezone().isoformat(),"wall_seconds":time.monotonic()-start,
        "command":command,"pid":child.pid,"returncode":rc,"timeout":timeout,
        "limits":{"wall":90,"RLIMIT_CPU":60,"RLIMIT_AS":536870912,"affinity":cpus},
        "actual_child_cpu":usage.ru_utime+usage.ru_stime,"peak_child_RSS_KiB":usage.ru_maxrss,
        "direct_child_reaped":True,"pid_absent_after_wait":not Path('/proc',str(child.pid)).exists(),
        "stdout_sha256":hashlib.sha256((out/"stdout.json").read_bytes()).hexdigest(),
        "stderr_sha256":hashlib.sha256((out/"stderr.log").read_bytes()).hexdigest()}
(out/"RESULT.json").write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
raise SystemExit(rc if rc>=0 else 1)
