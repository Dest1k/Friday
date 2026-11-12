"""Finite source-only protocol launch; only owned harness subprocesses, never consumer."""
from pathlib import Path
import ast,subprocess,json,time,resource,os,hashlib,sys
sys.dont_write_bytecode=True
from archive_closed import archive
os.umask(0o077)
P=Path(__file__).resolve().parent
TREE=ast.parse((P/'control.py').read_bytes())
EXPECTED=next(ast.literal_eval(n.value) for n in TREE.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='EXPECTED' for x in n.targets))
CASES=['positive_bootA_first','positive_bootB_repeat',*EXPECTED]
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
def main():
 start=time.monotonic();results=[];args=sys.argv[1:];run_label=args.pop(0);assert run_label.replace('-','').replace('_','').isalnum();selected=args or CASES
 for case in selected:
  assert case in CASES
  label=run_label+'-'+case;begin=time.monotonic()
  assert not (P/'cases'/label).exists(),'fresh never-replayed harness fixture directory required'
  proc=subprocess.Popen([sys.executable,'-I','-B','-S',str(P/'control.py'),label,case,'snapshot'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,preexec_fn=limits)
  timedout=False
  try:out,err=proc.communicate(timeout=90)
  except subprocess.TimeoutExpired:
   timedout=True;proc.kill();out,err=proc.communicate(timeout=5)
  assert proc.poll() is not None
  for ext,data in [('stdout',out),('stderr',err)]:
   q=P/(label+'.'+ext);q.write_text(data);q.chmod(0o600)
  result=dict(control=case,harness_pid=proc.pid,harness_PID_reaped=True,timeout=timedout,exit=proc.returncode,elapsed_seconds=time.monotonic()-begin,stdout=ref(P/(label+'.stdout')),stderr=ref(P/(label+'.stderr')))
  for leaf,key in [('RESULT.json','result'),('RESOURCES.json','resources'),('AUDIT-SUMMARY.json','audit')]:
   rp=P/'cases'/label/leaf
   if rp.exists():
    result[key]=ref(rp)
    if leaf=='RESULT.json':result['observed']=json.loads(rp.read_bytes())
  if not case.startswith('positive_'):result['closed_raw_fixture_archive']=archive(P/'cases'/label)
  results.append(result)
  owned_bytes=sum(x.stat().st_size for x in P.rglob('*') if x.is_file())
  assert owned_bytes<=20*1024**2,'own protocol total storage bound'
  if proc.returncode:break
 output=dict(scope='EXPLICITLY_SYNTHETIC_SOURCE_ONLY_NOT_ACTUAL_ROOT_OR_USER_ACCEPTANCE',elapsed_seconds=time.monotonic()-start,harness=ref(P/'control.py'),launcher=ref(P/'launch_protocol.py'),fixture=ref(P/'observation_fixture.py'),selected_fixture=ref(P/'selected_fixture.py'),input_pins=ref(P/'INPUT-PINS.json'),owned_total_bytes=owned_bytes,limits_per_group=dict(wall_seconds=90,cpu_seconds=60,address_space_bytes=512*1024**2,cpus=2),all_passed=all(r['exit']==0 for r in results),all_harness_PIDs_reaped=all(r['harness_PID_reaped'] for r in results),results=results)
 q=P/('RUN-'+run_label+'.json');assert not q.exists();q.write_text(json.dumps(output,sort_keys=True)+'\n');q.chmod(0o600)
 print(json.dumps({k:v for k,v in output.items() if k!='results'},sort_keys=True));print('GROUPS',len(results));sys.exit(0 if output['all_passed'] else 1)
if __name__=='__main__':main()
