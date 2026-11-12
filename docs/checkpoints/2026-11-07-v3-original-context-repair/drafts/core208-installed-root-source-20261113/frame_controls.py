"""Finite source controls. No actual source-builder, collector, admission or actor run.
Only refused no-arg new interfaces, in-memory pure contracts, and isolated subprocess
fixtures for inherited shared-FD custody and closure. Product/runtime paths denied.
"""
from pathlib import Path
import ast,copy,datetime,fcntl,hashlib,importlib.util,json,os,resource,signal,stat,subprocess,sys,tempfile,time,types
B=Path(__file__).parent
OLD=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/core207-installed-root-source-20261112')
START=time.monotonic();checks=[]
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.umask(0o077)
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append({'name':name,'passed':True})
def negative(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError,RuntimeError):check(name,True);return
 raise AssertionError('negative_did_not_refuse:'+name)
def module(name):
 p=B/name;m=types.ModuleType('control_'+name.replace('.','_').replace('/','_'));m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
for p in B.rglob('*.py'):ast.parse(p.read_bytes(),filename=str(p));compile(p.read_bytes(),str(p),'exec')
check('all_frame_python_compiles',True)
# Preload harmless stdlib for an import-time event audit that rejects writes and all
# product/environment/service/socket execution. No actual runtime is observed here.
violations=[]
def audit(event,args):
 if event in {'subprocess.Popen','socket.connect','socket.bind','os.mkdir','os.rename','os.remove','os.putenv','os.unsetenv','os.chdir','os.chmod','os.kill','os.killpg'}:violations.append(event);raise RuntimeError('import_effect_forbidden:'+event)
 if event=='open':
  p=args[0];flags=args[2]
  if isinstance(p,(str,bytes))and (str(p).startswith('/home/jericho/jericho/Friday_rework/.runtime/')or str(p).startswith('/home/jericho/.jericho/STATE')):violations.append('runtime_open');raise RuntimeError('import_runtime_read_forbidden')
  if isinstance(flags,int)and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):violations.append('write_open');raise RuntimeError('import_write_forbidden')
# Audit installed in isolated import child, so later fixture writes remain independent.
script='''import sys,types,pathlib,os,json,subprocess,socket,sqlite3,importlib.util,datetime,zoneinfo,fcntl,stat,hashlib,signal,time,struct,math
B=pathlib.Path(sys.argv[1]);events=[]
def audit(event,args):
 if event in {'subprocess.Popen','socket.connect','socket.bind','os.mkdir','os.rename','os.remove','os.putenv','os.unsetenv','os.chdir','os.chmod','os.kill','os.killpg'}:raise RuntimeError('import_effect:'+event)
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)) and str(p).startswith('/home/jericho/jericho/Friday_rework/.runtime/'):raise RuntimeError('runtime_import_read')
  if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('import_write')
sys.addaudithook(audit)
for name in sys.argv[2:]:
 p=B/name;m=types.ModuleType('inert_'+name.replace('.','_').replace('/','_'));m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);events.append(name)
print(json.dumps(events))
'''
interfaces=['run_native208_once.py','resume_native208_services.py','start_core208_once.py','core208-first-actual-root.py','admission-retained/observe-current-retained-units.py','root208_metadata.py','native_scope.py','boundary_contract.py','prepare_source.py']
r=subprocess.run([sys.executable,'-I','-B','-c',script,str(B),*interfaces],capture_output=True,timeout=10)
check('default_import_no_product_reads_writes_subprocess_socket_env_or_signals',r.returncode==0)
for name in interfaces[:6]+['prepare_source.py']:
 r=subprocess.run([sys.executable,'-I','-B',str(B/name)],capture_output=True,timeout=5)
 check('no_arg_refused_before_any_binding_'+name,r.returncode!=0 and any(x in r.stderr.lower()for x in [b'explicit',b'required']))
# Load pure source modules (actual functions are called only with pure fixture values).
c=module('boundary_contract.py');a=module('run_native208_once.py');recovery=module('resume_native208_services.py');boundary=module('core208-first-actual-root.py')
# Namespace-normalize original function AST; every process/cleanup/time function unchanged.
namespace=module('assemble_frame.py').__dict__
def defs(s):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for old,new in [('run_native207_once.py','run_native208_once.py'),('resume_native207_services.py','resume_native208_services.py')]:
 original=defs(namespace['transform']((OLD/old).read_text()));fresh=defs((B/new).read_text())
 check('all_original_function_AST_preserved_'+new,all(fresh.get(k)==v for k,v in original.items()))
check('module_global_bindings_preserved',all(isinstance(n,ast.Global)for n in ast.parse((B/'run_native208_once.py').read_bytes()).body[-2].body[:1]))
# New authority and truthfulness controls; synthetic refs never saved as grants.
r=lambda n:{'path':'/synthetic/'+n,'sha256':'a'*64}
refs={k:r(k)for k in ['manifest','boundary','caller','anchor','source_acceptance','predecessor']}
v=dict(schema='frw.root.native208-reviewed-future-boundary.v1',state='ROOT_REVIEWED_EXACT208_FUTURE_EXECUTION',template_only_no_execution_grant=False,frame='/synthetic/frame',execution_commit='b'*40,origin_url='https://github.com/Dest1k/Friday.git',provenance_mode='local-committed-main',public_main_sha=None,future_finite_operation_reviewed=True,new_future208_budgets=dict(actor=1800,source=600,publisher_unit=810,publisher_client=840,cold_each=180,postcheck=90,reserve=75),old_effects_clocks_preserved=True,logging208_accepted_source_only_not_runtime_qualified=True,shared_slot_identity=[1,2,1000,1,384],source_pin_manifest=refs['manifest'],boundary=refs['boundary'],caller=refs['caller'],current_service_anchor=refs['anchor'],source_acceptance=refs['source_acceptance'],actual207_predecessor=refs['predecessor'])
c.validate_authority(v,**refs,frame='/synthetic/frame');check('new208_authority_localmode_pure_positive',True)
for name,mut in [('template_grant',lambda x:x.update(template_only_no_execution_grant=True)),('old207authority',lambda x:x.update(state='ROOT_REVIEWED_EXACT207_FUTURE_EXECUTION')),('wrongpredecessor',lambda x:x.update(actual207_predecessor=r('wrong'))),('oldclockreset',lambda x:x.update(old_effects_clocks_preserved=False)),('budgets_not_reachingconsumer',lambda x:x['new_future208_budgets'].update(source=599)),('false_local_remote',lambda x:x.update(public_main_sha='b'*40))]:
 bad=copy.deepcopy(v);mut(bad);negative('authority_reject_'+name,lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
gw=dict(pid=42,birth_ticks=50,boot_id='b'*36);g=dict(scope='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',read_only=True,identity=dict(pid=42,start_time=50,boot_id='b'*36),observed_monotonic=100,global_active_session_keys=[],terminal_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False),web_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False));dbs={n:dict(quick_check='ok',leases=0,all_origin_pending_delegations=0,observed_monotonic=100)for n in ['default','dest','tester']}
c.validate_global_quiescence(g,dbs,gw,current_monotonic=115);check('globalnative_eachSQL_15s_pure_positive',True)
negative('globalnative_15splus_refused',lambda:c.validate_global_quiescence(g,dbs,gw,current_monotonic=115.001))
for name in dbs:
 bad=copy.deepcopy(dbs);bad[name]['leases']=1;negative('SQL_'+name+'_lease_refused',lambda:c.validate_global_quiescence(g,bad,gw,current_monotonic=110))
 bad=copy.deepcopy(dbs);bad[name]['all_origin_pending_delegations']=1;negative('SQL_'+name+'_pending_refused',lambda:c.validate_global_quiescence(g,bad,gw,current_monotonic=110))
 bad=copy.deepcopy(dbs);bad[name]['observed_monotonic']=99;negative('SQL_'+name+'_stale_refused',lambda:c.validate_global_quiescence(g,bad,gw,current_monotonic=115))
# Finite real isolated process+FD fixture exercises exact unchanged launch_once.
# Uses only a temporary source-test directory and private flock file; never actual slot.
with tempfile.TemporaryDirectory(prefix='frame-controls-',dir=B)as td:
 t=Path(td);slot=t/'synthetic.lock';fd=os.open(slot,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 original_e,original_f,original_ref=boundary.E,boundary.F,boundary.ref;boundary.E=t;boundary.F=B
 childcode='import os,fcntl,sys,time; fd=int(sys.argv[1]);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);os.kill(os.getppid(),2);time.sleep(.03)'
 try:
  result=boundary.launch_once([sys.executable,'-I','-B','-c',childcode,str(fd)],fd,'fixture-boot')
  check('shared_description_child_holds_lock_and_parent_defers_signal',result['returncode']==0 and result['deferred_parent_signals']==[signal.SIGINT])
  check('parent_holder_remains_after_exact_child_reaped',os.fstat(fd).st_nlink==1)
  childjson=json.loads((t/'CORE208-ROOT-ONCE-ACTOR-LAUNCHED.json').read_bytes());check('exact_fixture_child_reaped',not Path('/proc',str(childjson['pid'])).exists())
 finally:boundary.E,boundary.F,boundary.ref=original_e,original_f,original_ref;os.close(fd)
 probe=os.open(slot,os.O_RDWR);fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB);os.close(probe);check('isolated_slot_released_after_holders_close',True)
# Static boundary and actor consumer constraints are exact changed consumers.
s=(B/'core208-first-actual-root.py').read_text();main=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name=='main');part=ast.get_source_segment(s,main)
check('final_freshness_after_binding_before_actor',part.rindex('contract.validate_global_quiescence(')>part.rindex('m.load_actor_binding(')and part.rindex('contract.validate_global_quiescence(')<part.rindex('result = launch_once('))
check('bank_resources_before_globalnative',s.index('native = transport.fresh_native(state)')>s.index('resources = dict(')>s.index('if bank_check:'))
check('same_sharedFD_no_unlock_no_duplicateactor',"pass_fds=(slotfd,)"in s and 'fcntl.LOCK_UN'not in s and part.count('result = launch_once(')==1)
actor=(B/'run_native208_once.py').read_text();check('new208consumer_v10_8CAS_2native',"'friday.current-source-native-successor.v10'"in actor and "bound['selected_target_count'] == 8"in actor and 'len(targets) == 2'in actor and "len(previous['project_files']) == 495"in actor and "len(cur['project_files']) == 497"in actor)
check('publisher_resources_reach_executor',all(x in actor for x in ['--property=RuntimeMaxSec=810','--property=LimitCPU=1560','--property=CPUQuota=200%','--property=MemoryMax=2G','--property=LimitAS=3G','--property=TasksMax=96']))
check('source_acceptance_before_new_clock',actor.index('bound = binding.load_actor_binding(B)')<actor.index('origin = time.monotonic()'))
forbidden=['ROOT-FRESH-REQUEST.json','ROOT-208-SOURCE-ACCEPTANCE.json','ROOT-208-RUNTIME-AUTHORITY.json','ROOT-ACTUAL207-PREDECESSOR.json','ROOT-208-FRESH-READBACK.json','ROOT-208-BOUND-INPUTS.json','ROOT-208-FRESH-ADMISSION.json','ROOT-NATIVE208-LIVE-OPERATION.json','FUTURE-EXECUTION']
check('no_actual_future_artifacts',all(not os.path.lexists(B/n)for n in forbidden))
check('finite_sourcecontrols_wall90',time.monotonic()-START<=90)
value={'schema':'frw.root208.frame-source-controls.v1','state':'PASS_SOURCE_ONLY','checks':len(checks),'rows':checks,'wall_seconds':time.monotonic()-START,'actual_runtime_observations':0,'actual_product_effects':0,'source_fixture_processes_reaped':True,'no_genuine_authority_or_request_created':True,'scope':'pure contracts+refused new noarg interfaces+bounded isolated process/FD fixture only'}
p=B/'FRAME-CONTROLS.json';p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');p.chmod(0o600)
print(json.dumps({k:value[k]for k in ['state','checks','wall_seconds']}))
