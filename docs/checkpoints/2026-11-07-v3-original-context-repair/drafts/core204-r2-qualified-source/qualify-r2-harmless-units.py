"""Finite real harmless executor qualification; no product publisher/H access."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,time,datetime,signal,secrets,fcntl,stat,resource,sys
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111');D=B/'CORE204-R2-OBSERVER-REAL-HARMLESS-UNITS-20261112';os.umask(0o077);D.mkdir(mode=0o700)
P=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112');source=P/'candidate/run_native204_once.py';source205=P/'candidate/run_native205_once.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(source)=='f890c9b10c43620a214f33fec7a56525eb02cf5a5fbb0a8c7dec3351853d6bb1';assert sha(source205)=='5a1a894c87c910b0e019515602efde200fde5d22d2607995b457fc32ec28b9db'
selected={'remaining','command','service','local_group_absent','reap_exact_owned_local_group','closed','save','event','publisher_cgroup_empty','remember_publisher_identity','publisher_process_closed','publisher_terminal_proven','close_owned_publisher','run_owned_publisher'}
def functions(p):
 raw=p.read_text();a=ast.parse(raw);return {x.name:x for x in a.body if isinstance(x,ast.FunctionDef) and x.name in selected}
a=functions(source);b=functions(source205);assert set(a)==set(b)==selected;assert all(ast.dump(a[n],include_attributes=False)==ast.dump(b[n],include_attributes=False) for n in a)
module=ast.Module(body=list(a.values()),type_ignores=[]);code=compile(module,str(source),'exec')
class StopUnconfirmed(RuntimeError):pass
now=lambda:datetime.datetime.now().astimezone().isoformat()
def save_new(p,j):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(j,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);signal.alarm(60)
slot=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock');fd=os.open(slot,os.O_RDWR|os.O_NOFOLLOW);si=os.fstat(fd);assert (si.st_dev,si.st_ino,si.st_uid,si.st_nlink,stat.S_IMODE(si.st_mode))==(2050,9440373,os.getuid(),1,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
python='/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python'
plan={'at_moscow':now(),'scope':'Two tiny own transient units, fixed harmless sleep/print/exit0-or2 only. Exact source AST functions; not actor/fullpublisher/native/Office/user execution.','source_sha256':sha(source),'source205_sha256':sha(source205),'distinct_needed_reason':'R2 wait branch replaces proven R1 startupemptyID failure; old probe0/publisher once untouched, no product retry','independent_source_review_sha256':'16d0ce6b29068834e57f1a75084a521b125afe19e7e2535bd86a7b8b739c4212','functions_AST_identical':sorted(selected),'budgets':{'total_wall':60,'per_control_wall':25,'unit_runtime':10,'unit_stop':2,'parent_cpu':30,'parent_AS':512*1024**2,'unit_memory':64*1024**2,'unit_CPUQuota':'100%'},'old_publisher_replay':False,'product_source_profile_user_DB_reads':False,'uses_existing_PM_interpreter_only':True,'model_Office_network_Telegram':False};save_new(D/'PLAN.json',plan)
rows=[]
try:
 for expected in [0,2]:
  nonce=secrets.token_hex(8);unit='frw-observer-r2-probe-20261112-'+nonce+'.service';desc='Root-harmless-observer-'+nonce;case=D/('exit'+str(expected));case.mkdir(mode=0o700);J=case/'JOURNAL.json';j={'events':[],'publisher_owned_description':desc,'publisher_launch_consumed_no_retry':True,'probe_only':True};ns=dict(Path=Path,os=os,sys=sys,subprocess=subprocess,time=time,datetime=datetime,json=json,signal=signal,StopUnconfirmed=StopUnconfirmed,GW='UNUSED-NO-PRODUCT-UNIT',PUB=unit,J=J,j=j,now=now);exec(code,ns)
  deadline=time.monotonic()+25;before=ns['service'](unit,deadline=deadline);assert before['LoadState']=='not-found' and before['MainPID']==before['ControlPID']=='0'
  childcode="import time; time.sleep(2.0); print('HARMLESS_OBSERVER_EXIT_"+str(expected)+"',flush=True); raise SystemExit("+str(expected)+")"
  args=['systemd-run','--user','--wait','--pipe','--unit='+unit.removesuffix('.service'),'--property=Description='+desc,'--property=RuntimeMaxSec=10','--property=TimeoutStopSec=2','--property=KillMode=control-group','--property=Restart=no','--property=UMask=0077','--property=MemoryMax=64M','--property=LimitAS=256M','--property=MemorySwapMax=0','--property=CPUQuota=100%','--property=TasksMax=8','/usr/bin/env','-i','PATH=/usr/bin:/bin','PYTHONDONTWRITEBYTECODE=1',python,'-I','-B','-c',childcode]
  save_new(case/'INTENT.json',{'at_moscow':now(),'argv':args,'original_deadline_monotonic':deadline,'unit':unit,'description':desc,'no_retry':True});ns['save']();started=time.monotonic();failure=None
  try:
   with (case/'client.stdout').open('xb') as out,(case/'client.stderr').open('xb') as err:r=ns['run_owned_publisher'](args,stdout=out,stderr=err,client_deadline=deadline)
   assert r.returncode==expected==j['publisher_client_returncode']
   terminal=ns['close_owned_publisher'](deadline)
   assert j['publisher_closed_before_parent_custody_release'] and j['publisher_invocation_id'] and j['publisher_cgroup'] and j['publisher_process_identity']
   assert ns['publisher_cgroup_empty']() and ns['publisher_process_closed']()
   # Negative proof at this real ceased unit: no prior binding cannot gain authority.
   real=j.copy();ns['j']={k:v for k,v in real.items() if k not in ['publisher_invocation_id','publisher_cgroup','publisher_process_identity']}
   refused=False
   try:ns['publisher_terminal_proven'](deadline=deadline)
   except AssertionError:refused=True
   finally:ns['j']=j
   assert refused
   # Failed own units may remain loaded. Reset only after exact terminal proof.
   if terminal['LoadState']!='not-found':
    assert terminal['Description']==desc and terminal['InvocationID'] in ['',j['publisher_invocation_id']]
    reset=ns['command'](['systemctl','--user','reset-failed',unit],deadline=deadline);assert reset.returncode==0
   last=ns['service'](unit,deadline=deadline);assert last['MainPID']==last['ControlPID']=='0' and last['ActiveState']=='inactive' and ns['publisher_cgroup_empty']() and ns['publisher_process_closed']()
   row={'expected_exit':expected,'actual_client_exit':r.returncode,'saved_actual_code':j['publisher_client_returncode'],'invocation':j['publisher_invocation_id'],'process_identity':j['publisher_process_identity'],'cgroup':j['publisher_cgroup'],'terminal':terminal,'final_unit':last,'unbound_terminal_refused':refused,'elapsed_seconds':time.monotonic()-started,'own_scope_closed':True,'old_publisher_or_product_service_effects':False};rows.append(row);save_new(case/'RESULT.json',row)
  except BaseException as e:
   failure={'class':type(e).__name__,'message':str(e)[:300],'j':j,'elapsed_seconds':time.monotonic()-started}
   try:ns['close_owned_publisher'](deadline)
   except BaseException as ce:failure['closure_error']={'class':type(ce).__name__,'message':str(ce)[:300]}
   save_new(case/'FAILURE.json',failure);raise
 result={'schema':'friday.root.publisher-observer.harmless-real-unit.v1','state':'PASS_BOUNDED_REAL0_REAL2_EXACT_SOURCE_AND_CLOSURE','at_moscow':now(),'rows':rows,'source204':sha(source),'source205':sha(source205),'shared_functions_AST_identical':True,'old_publisher_exit':'UNKNOWN_UNCHANGED','new_product_installation':False,'services_stopped_or_restarted':False,'limits':'Only exact extracted shared observerfunctions on two own harmless unit invocations; not whole native updater or futureinstalladmission. Real success/failed terminalGC paths captured asobserved, no syntheticemptyInvocationID claim.'};save_new(D/'RESULT.json',result);print(json.dumps({'state':result['state'],'result_sha256':sha(D/'RESULT.json'),'rows':len(rows),'actual_exits':[r['actual_client_exit'] for r in rows]}))
finally:os.close(fd);signal.alarm(0)
