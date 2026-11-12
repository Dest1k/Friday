import json,os,resource,signal,socket,subprocess,sys,tempfile,time
from pathlib import Path
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);signal.alarm(90)
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));from source_guard import install_guard
runs=W/'runs/guard-probes';runs.mkdir(mode=0o700,exist_ok=True,parents=True);guard=install_guard(W,runs);checks=[]
def denied(n,fn):
 try:fn()
 except PermissionError:checks.append(n)
 else:raise AssertionError(n)
denied('foreign-write-denied',lambda:Path('/tmp/frw-ninth-must-not-exist').write_bytes(b'no'))
denied('socket-denied',lambda:socket.socket())
denied('other-process-denied',lambda:subprocess.run(['/usr/bin/true']))
denied('foreign-mkdir-denied',lambda:os.mkdir('/tmp/frw-ninth-must-not-create'))
p=runs/'allowed.txt';p.write_bytes(b'own');p.unlink();checks.append('own-fixture-write-cleanup-permitted')
(W/'GUARD-CHECKS.json').write_text(json.dumps({'state':'PASS','checks':checks,'guard':guard},indent=2)+'\n');print('PASS',len(checks))
