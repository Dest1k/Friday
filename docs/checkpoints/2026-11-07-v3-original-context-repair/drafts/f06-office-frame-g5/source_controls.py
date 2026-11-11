"""Own-temp controls with an audit fence. No Office/unit/namespace/model calls."""
import ast,fcntl,hashlib,importlib.util,json,os,resource,shutil,stat,sys,tempfile,types
from pathlib import Path
B=Path(__file__).resolve().parent
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648))
# Install before importing any reused helper. Disallow actual runtime/state,
# credentials and subprocess effects even if a default/root is accidentally used.
DENIED=[]
BLOCK=['/home/jericho/jericho/Friday_rework/.runtime','/home/jericho/.jericho/state','/home/jericho/.hermes','/home/jericho/.config','/home/jericho/.local/share']
def audit(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.__new__'):
  DENIED.append(event);raise RuntimeError('AUDIT_EXECUTION_OR_SOCKET_DENIED')
 if event in ('open','os.listdir','os.scandir'):
  raw=args[0]
  if isinstance(raw,(str,bytes,os.PathLike)):
   p=os.fsdecode(raw)
   if any(p==q or p.startswith(q+'/') for q in BLOCK) or 'credential' in Path(p).name.lower() or Path(p).name=='CREDENTIAL-REF.json':
    DENIED.append((event,p));raise RuntimeError('AUDIT_ACTUAL_STATE_OR_SECRET_DENIED')
sys.addaudithook(audit)
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,B/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('f06_contract','f06_contract.py');sys.modules['f06_contract']=c
producer=module('f06_driver','office_fixture_driver.py');inside=module('f06_inside','inside_once.py');frame=module('f06_frame','root_frame.py');runner=module('f06_runner','run_once.py')
ROWS=[]
def assert_original():assert h(B/'office_fixture_driver.original.py')=='b0198c191c0119813d894aa3eb9546a2ccf14c97d1cb8f6ed650dc7a25d51744'
def assert_source(fragment):assert fragment in (B/'office_fixture_driver.py').read_text()
def test(name,fn):
 fn();ROWS.append(dict(name=name,pass_=True))
def reject(fn):
 try:fn()
 except (ValueError,RuntimeError,FileNotFoundError,NotADirectoryError):return
 raise AssertionError('expected rejection')
def write(p,obj):
 p.write_text(json.dumps(obj));p.chmod(0o600)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
root=Path(tempfile.mkdtemp(prefix='source-controls-',dir=B));root.chmod(0o700)
try:
 def setup(prefix):
  r=root/prefix;r.mkdir(mode=0o700);d=r/'encrypted-inputs';d.mkdir(mode=0o700);rows=[]
  for i in range(7):
   p=d/producer.target_name(producer.JOBS[i][0],producer.JOBS[i][2]);p.write_bytes(b'fixture'+str(i).encode());p.chmod(0o600)
   rows.append(dict(format=producer.JOBS[i][0],fixture_profile=producer.PROFILES[i],name=p.name,path=str(d/p.name),bytes=p.stat().st_size,sha256=h(p)))
  return r,d,rows
 r,d,rows=setup('oracle')
 manifest=dict(schema='friday.f06.reconciled-existing-inputs.v1',semantic='ALPHA17',custody_root=str(d),known_prefix_count=7,fixtures=rows)
 mp=r/'RECONCILED-INPUTS.json';write(mp,manifest)
 test('verify_inputs_accepts_exact_seven_including_latest',lambda:producer.reconciled_inputs(r,h(mp)))
 def negative(field,value):
  obj=json.loads(json.dumps(manifest));obj['fixtures'][0][field]=value;write(mp,obj);reject(lambda:producer.reconciled_inputs(r,h(mp)));write(mp,manifest)
 for key,val in [('format','odt'),('fixture_profile','latest'),('name','alien.docx'),('path',str(root/'alien.docx')),('sha256','0'*64),('bytes',99)]:test('reject_existing_'+key,lambda key=key,val=val:negative(key,val))
 def sem_bad():
  obj={**manifest,'semantic':'BRAVO23'};write(mp,obj);reject(lambda:producer.reconciled_inputs(r,h(mp)));write(mp,manifest)
 test('reject_edited_semantics_for_original_inputs',sem_bad)
 test('reject_manifest_hash_drift',lambda:reject(lambda:producer.reconciled_inputs(r,'0'*64)))
 def partial():
  for row in rows[3:]:(d/row['name']).unlink()
  obj={**manifest,'fixtures':rows[:3],'known_prefix_count':3};write(mp,obj);_,o,items=producer.reconciled_inputs(r,h(mp));assert len(items)==3
  assert not len(items)==7
 test('accept_exact_partial_prefix_without_seven_credit',partial)
 def gaps():
  obj={**manifest,'fixtures':rows[1:3],'known_prefix_count':2};write(mp,obj);reject(lambda:producer.reconciled_inputs(r,h(mp)))
 test('reject_gap_in_known_prefix',gaps)
 def extra():
  obj={**manifest,'fixtures':rows[:3],'known_prefix_count':3};write(mp,obj);p=d/'extra.odt';p.write_bytes(b'x');p.chmod(0o600);reject(lambda:producer.reconciled_inputs(r,h(mp)));p.unlink()
 test('reject_unbound_output',extra)
 def link():
  p=d/rows[0]['name'];p.unlink();p.symlink_to(root/'absent');reject(lambda:producer.reconciled_inputs(r,h(mp)));p.unlink()
 test('reject_dangling_existing_symlink',link)
 def hardlink():
  p=d/rows[0]['name'];p.write_bytes(b'fixture0');p.chmod(0o600);os.link(p,root/'hardlink');reject(lambda:producer.private_file(p,r));(root/'hardlink').unlink()
 test('reject_hardlinked_input',hardlink)
 test('deny_replaced_generation_even_dangling_output',lambda:assert_source("if os.path.lexists(target):raise ValueError('output_exists')"))
 def readonly_cfg():
  tree=ast.parse((B/'office_fixture_driver.py').read_text())
  node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="a.mode == 'produce'" and any(isinstance(v,ast.Assign) and 'config' in ast.unparse(v) for v in n.body))
  assert 'ConfigurationUpdateAccess' in ast.unparse(node)
 test('configuration_update_access_only_in_produce_branch',readonly_cfg)
 def no_false_refusal():
  text=(B/'office_fixture_driver.py').read_text();assert "except Exception as e:answer['load_exception_class']" in text
  assert "answer['opened']=True" in text and "abort.select();event['abort_selected']=True" in text
  assert "and all(e['request_kind'] in ('DocumentPasswordRequest','DocumentMSPasswordRequest') and e['abort_selected'] for e in events)" in text
 test('opened_monotonic_and_generic_exceptions_not_refusals',no_false_refusal)
 class FakeChild:
  pid=123456;returncode=None
  def __init__(self):self.killed=False;self.waited=False
  def kill(self):self.killed=True
  def wait(self,timeout=None):self.waited=True;self.returncode=-9
 def nested_probe_controls():
  tree=ast.parse((B/'office_fixture_driver.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  names={'prop','load','close','semantic','probe'};nodes=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in names]
  class Prop:pass
  class Uno:
   @staticmethod
   def systemPathToFileUrl(x):return x
  class Handler:events=[]
  class Text:
   def __init__(self,value):self.value=value
   def getString(self):return self.value
  class Doc:
   def __init__(self,value='F06 SYNTHETIC ALPHA 11 NOV F06 synthetic invariant paragraph',fail=False):self.value=value;self.fail=fail
   def getText(self):
    if self.fail:raise RuntimeError('synthetic semantic exception')
    return Text(self.value)
   def close(self,accepted):pass
  class Desk:
   answer=None;events=[];exception=False;props=None
   def loadComponentFromURL(self,url,frame,flags,props):
    self.props={p.Name:p.Value for p in props};Handler.events.extend(self.events)
    if self.exception:raise RuntimeError('synthetic generic failure')
    return self.answer
  desk=Desk();ns=dict(PropertyValue=Prop,uno=Uno,desktop=desk,handler=Handler)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact nested probe functions>','exec'),ns)
  def case(answer,events,exception=False):
   Handler.events=[];desk.answer=answer;desk.events=events;desk.exception=exception
   return ns['probe'](Path('/synthetic.docx'),'docx',None,False)
  good={'request_kind':'DocumentPasswordRequest','abort_selected':True}
  assert case(None,[good])['expected_password_refusal'] is True
  assert case(None,[{**good,'request_kind':'DocumentMSPasswordRequest'}])['expected_password_refusal'] is True
  for events in [[],[{**good,'abort_selected':False}],[{**good,'request_kind':'OTHER'}],[good,{**good,'request_kind':'OTHER'}]]:assert case(None,events)['expected_password_refusal'] is False
  assert case(None,[good],True)['expected_password_refusal'] is False
  opened=case(Doc(fail=True),[]);assert opened['opened'] is True and opened['expected_password_refusal'] is False and opened['semantic_match'] is False
  assert case(Doc(),[])['semantic_match'] is True
  assert case(Doc(value='F06 SYNTHETIC BRAVO 11 NOV F06 synthetic invariant paragraph'),[])['semantic_match'] is False
  assert desk.props['ReadOnly'] is True and desk.props['MacroExecutionMode']==0 and desk.props['UpdateDocMode']==0
 test('exact_probe_functions_negative_refusal_and_original_semantics',nested_probe_controls)
 def unreaped_cleanup():
  p=FakeChild();inside.stop(p,None);assert p.killed and p.waited and p.returncode is not None
 test('pidfd_binding_failure_still_reaps_same_direct_child',unreaped_cleanup)
 class Closed:
  pid=123456;returncode=0
  def kill(self):raise AssertionError('must not signal reaped PID')
 def reaped_safe():inside.stop(Closed(),None)
 test('already_reaped_child_never_signaled',reaped_safe)
 def runner_birth_failure():
  import time,signal
  op=root/'runner-lifetime';op.mkdir(mode=0o700);ad=dict(state='ROOT_FRESH_ONCE_ADMITTED',assignment=c.ASSIGNMENT,source_pins_sha256='0'*64,limits=c.PREFLIGHT_LIMITS,mode='preflight',operation_key='preflight-g1',boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),nonce='a'*32)
  child=FakeChild();child.returncode=None
  oldargv=sys.argv;oldop=c.operation;oldprivate=c.private;oldrecipe=c.recipe_check;oldrootparent=runner.root_parent;oldbank=c.bank_snapshot;oldbw=c.bwrap;oldcontext=runner.context;oldcpu=runner.cpu;oldpopen=runner.subprocess.Popen;oldpidfd=runner.os.pidfd_open;olddead=c.DEADLINE
  sigs={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
  try:
   sys.argv=['run_once.py','--admission',str(B/'preflight-g1.ADMISSION.json'),'--admission-sha256','0'*64]
   c.operation=lambda key,mode:op;c.private=lambda *args:(json.dumps(ad).encode(),{'sha256':'0'*64});c.recipe_check=lambda:({'sha256':'0'*64},[]);runner.root_parent=lambda *a:None;c.bank_snapshot=lambda:{'fake':'bank'};c.bwrap=lambda *a:['fake']
   runner.context=lambda *args:(root,time.monotonic(),{});runner.cpu=lambda cg:0;runner.subprocess.Popen=lambda *a,**kw:child
   def failed_pidfd(*a):raise OSError('synthetic pidfd failure')
   runner.os.pidfd_open=failed_pidfd
   assert runner.main()==1;assert child.killed and child.waited
   out=json.loads((op/'UNIT-RESULT.json').read_text());assert out['namespace_closed'] is True and out['error_class']=='OSError'
  finally:
   sys.argv=oldargv;c.operation=oldop;c.private=oldprivate;c.recipe_check=oldrecipe;runner.root_parent=oldrootparent;c.bank_snapshot=oldbank;c.bwrap=oldbw;runner.context=oldcontext;runner.cpu=oldcpu;runner.subprocess.Popen=oldpopen;runner.os.pidfd_open=oldpidfd;c.DEADLINE=olddead
   for sig,fn in sigs.items():signal.signal(sig,fn)
 test('unit_post_Popen_pidfd_failure_reaps_actual_returned_child',runner_birth_failure)
 def root_postlaunch_failure(stage):
  import time,signal
  key='preflight-g1';unit=c.unit_name(key);op=root/('parent-lifetime-'+stage);lock=root/('fake-slot-'+stage);lock.write_bytes(b'');lock.chmod(0o600)
  ad=dict(mode='preflight',operation_key=key,nonce='a'*32,boot_id='fake',source_pins_sha256='0'*64,actual_two_cpu_ids=[0,1]);child=FakeChild();child.returncode=None
  count={'launch':0,'show':0,'scope':0,'ref':0,'stop':0,'release':0};fd=None
  class Launcher(FakeChild):
   def wait(self,timeout=None):
    if stage=='wait' and not self.waited:self.waited=True;raise RuntimeError('synthetic post-Popen wait failure')
    self.waited=True;self.returncode=0;return 0
  child=Launcher()
  class Bus:
   held=False
   def __init__(self,unit):self.unit=unit
   def ref(self):
    count['ref']+=1
    if stage=='ref' and count['ref']==1:raise RuntimeError('synthetic reference failure')
    self.held=True
   def stop_owned(self):count['stop']+=1
   def release(self):self.held=False;count['release']+=1
   def close(self):pass
  def props(unit,allow_missing=False):
   count['show']+=1
   if count['show']==1:return dict(LoadState='not-found',MainPID='0',ControlPID='0',ControlGroup='')
   if stage=='show' and count['show']==2:raise RuntimeError('synthetic first post-launch show failure')
   return dict(Id=unit,LoadState='loaded',MainPID='0',ControlPID='0',ControlGroup='/'+unit,ExecMainStartTimestampMonotonic=str(int(time.monotonic()*1e6)),ActiveState='inactive',ExecMainCode='1',ExecMainExitTimestampMonotonic=str(int(time.monotonic()*1e6)+1),ExecMainStatus='0',Job='')
  def scoped(props,*args):
   count['scope']+=1
   if stage=='scope' and count['scope']==1:raise RuntimeError('synthetic first post-launch bind failure')
   return props
  old={name:getattr(frame,name) for name in ('validate_admission','acquire_slot','unit_props','Bus','scope','bind_cgroup','kernel_empty','slice_context')};oldop=c.operation;oldpopen=frame.subprocess.Popen
  try:
   fd=os.open(lock,os.O_RDONLY);frame.validate_admission=lambda *a:(ad,{'sha256':'0'*64});frame.acquire_slot=lambda a:fd;frame.unit_props=props;frame.slice_context=lambda:dict(Id='app.slice',ActiveState='active',ControlGroup='/app.slice');frame.Bus=Bus;frame.scope=scoped;frame.bind_cgroup=lambda *a:'/sys/fs/cgroup/app.slice/'+unit;frame.kernel_empty=lambda *a:True;c.operation=lambda *a:op
   def popen(*a,**kw):count['launch']+=1;return child
   frame.subprocess.Popen=popen
   args=types.SimpleNamespace(admission=B/(key+'.ADMISSION.json'),admission_sha256='0'*64)
   # Isolated flags are checked by actual frame, these source controls run -I.
   assert frame.execute(args)==1
   out=json.loads((op/'ROOT-RESULT.json').read_text());assert out['actual_closure_observed'] is True and count['launch']==1 and count['stop']==1 and count['release']==1
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('slot fd not closed after actual fake closure')
  finally:
   for name,val in old.items():setattr(frame,name,val)
   c.operation=oldop;frame.subprocess.Popen=oldpopen
   try:os.close(fd)
   except OSError:pass
 for stage in ('wait','show','scope','ref'):test('Root_'+stage+'_failure_reconciles_same_unit_before_slot_release',lambda stage=stage:root_postlaunch_failure(stage))
 def actual_own_flock_binding():
  op=root/'real-owned-flock';op.mkdir(mode=0o700);path=op/'owned-fake-slot';path.write_bytes(b'');path.chmod(0o600)
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
  try:
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);sid=c.identity(os.fstat(fd));boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();unit=c.unit_name('preflight-g1')
   v=dict(root_uid=os.getuid(),boot_id=boot,admission_sha256='0'*64,unit=unit,nonce='a'*32,root_pid=os.getpid(),root_starttime=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],slot_fd=fd,slot_identity=sid)
   write(op/'PARENT-BINDING.json',v);ad=dict(boot_id=boot,nonce='a'*32,slot_identity=sid)
   assert runner.root_parent(op,'0'*64,ad,unit)==v
   fcntl.flock(fd,fcntl.LOCK_UN);reject(lambda:runner.root_parent(op,'0'*64,ad,unit))
  finally:os.close(fd)
 test('real_own_flock_fd_identity_and_unlocked_negative',actual_own_flock_binding)
 test('immutable_original_producer_exact_b019',lambda:assert_original())
 def sysd_argv():
  a=dict(mode='generate',operation_key='generate-g1',nonce='a'*32,actual_two_cpu_ids=[0,1]);argv=frame.command(a,'0'*64)
  for value in ['--property=RuntimeMaxSec=300','--property=MemoryMax=2147483648','--property=MemorySwapMax=0','--property=CPUQuota=200%','--property=TasksMax=128','--property=RemainAfterExit=yes','--property=KillMode=control-group']:assert value in argv
  assert '--wait' not in argv and '--collect' not in argv and not any('gateway' in x.lower() or 'dashboard' in x.lower() for x in argv)
 test('finite_only_owned_unit_resource_argv',sysd_argv)
 def bw():
  oldsafe=c.safe_dir;c.safe_dir=lambda p:Path(p)
  try:
   for mode in ('preflight','generate'):
    argv=c.bwrap(root,root,mode,mode+'-g1',0,'a'*32)
    for value in ['--unshare-all','--clearenv','--cap-drop','--ro-bind','--die-with-parent','--as-pid-1']:assert value in argv
    assert ('/inputs' in argv)==(mode!='preflight')
    assert '/work' in argv and c.PREFIX in argv
  finally:c.safe_dir=oldsafe
 test('bwrap_preflight_mounts_no_input_or_secret',bw)
 def early_exit_without_unit_intent():
  op=root/'early-refusal';op.mkdir(mode=0o700);unit=c.unit_name('preflight-g1');expected='/sys/fs/cgroup/user.slice/app.slice/'+unit
  bound=dict(ControlGroup='',ExecMainStartTimestampMonotonic='12345')
  assert frame.bind_cgroup(bound,op,unit,expected)==expected
  assert bound['_cgroup_rel']==expected[len('/sys/fs/cgroup'):]
  assert not (op/'UNIT-INTENT.json').exists()
  reject(lambda:frame.bind_cgroup(dict(ControlGroup='/foreign/'+unit),op,unit,expected))
 test('early_unit_refusal_empty_cgroup_uses_actual_prebound_slice_without_intent',early_exit_without_unit_intent)
 def helper_cpu_accounting():
  import resource
  old=frame.resource.getrusage
  try:
   frame.resource.getrusage=lambda kind:types.SimpleNamespace(ru_utime=2.5,ru_stime=.5)
   assert frame.children_cpu()==3
  finally:frame.resource.getrusage=old
 test('Root_owned_systemctl_and_launcher_CPU_included',helper_cpu_accounting)
 def scope_controls():
  a=dict(mode='generate',operation_key='generate-g1',nonce='a'*32)
  base=dict(Id=c.unit_name('generate-g1'),LoadState='loaded',Description='FRW F06 once '+a['nonce'],InvocationID='b'*32,ExecMainStartTimestampMonotonic='12345',RemainAfterExit='yes',CollectMode='inactive',KillMode='control-group',Restart='no',NRestarts='0',ExecStop='',ExecStopPost='',RuntimeMaxUSec='5min',ExecStart='{ path=/usr/bin/python3 ; argv[]='+' '.join(frame.run_argv(B/'generate-g1.ADMISSION.json','0'*64))+' ; ignore_errors=no ; }')
  frame.scope(base,a,'0'*64)
  for k in ['Id','Description','InvocationID','ExecMainStartTimestampMonotonic','KillMode','RuntimeMaxUSec','ExecStart','Restart','ExecStop']:
   bad={**base,k:'evil'};reject(lambda:frame.scope(bad,a,'0'*64))
 test('stop_scope_requires_actual_unit_nonce_exec_birth_and_limits',scope_controls)
 def auditnegative():
  before=len(DENIED);reject(lambda:Path('/home/jericho/jericho/Friday_rework/.runtime/forbidden-control').read_bytes());assert len(DENIED)==before+1
 test('actual_runtime_read_denied_before_import_tests',auditnegative)
 # Audit-control denials are intentional, and no unrequested runtime reads occur.
 unexpected=DENIED[:-1];assert not unexpected,unexpected
 # This is not a live API test; report only source/control conclusions.
 output=dict(state='SOURCE_CONTROLS_PASS_NO_OFFICE_OR_UNIT',controls=ROWS,count=len(ROWS),actual_Office_starts=0,actual_unit_starts=0,actual_namespace_starts=0,actual_state_or_secret_reads=0,intentional_audit_denials=DENIED,limits='Fake child and argv/source contracts; real boundaries remain UNBOUND')
 (B/'SOURCE-CONTROLS.json').write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'count':len(ROWS),'state':output['state']}))
finally:shutil.rmtree(root)

def assert_original():assert h(B/'office_fixture_driver.original.py')=='b0198c191c0119813d894aa3eb9546a2ccf14c97d1cb8f6ed650dc7a25d51744'
def assert_source(fragment):assert fragment in (B/'office_fixture_driver.py').read_text()
