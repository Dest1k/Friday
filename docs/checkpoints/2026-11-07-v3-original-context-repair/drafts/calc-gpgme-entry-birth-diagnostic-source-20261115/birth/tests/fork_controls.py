"""Pure source callback controls; synthetic kernel/GDB data, no actors/proc reads.

The real native.stopped→MultiCustody.boundary→Adapter.birth→collector.snapshot,
_all_stop, children, proc and native.fail bodies execute. Only the named data
sources (kernel file reads, maps, environment and stopped GDB objects) are fake.
A positive here preserves an existing SOURCE route; it is no runtime admission.
"""
from pathlib import Path
import ast,copy,json,os,struct,sys,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parents[1]
PREV=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-BOOTSTRAP-ENTRY-SOURCE-20261115')
composition=json.loads((PREV/'SOURCE-COMPOSITION.json').read_bytes())
refs={v['relative_path']:Path(v['selected']['path']) for v in composition['files']}
def mod(p,name,**injected):
 m=types.ModuleType(name);m.__file__=str(p);m.__dict__.update(injected)
 exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
policy=mod(refs['outer/deps/gpgme_engine_policy.py'],'policy')
mapper=mod(refs['outer/deps/gpgme_mapped_image.py'],'mapper')
c=mod(B/'candidate/outer/deps/gpgme_boundary_collector.py','collector',policy=policy,mapper=mapper)
a=mod(refs['outer/deps/gpgme_engine_gdb.py'],'adapter')
class Inf:
 def __init__(self,pid,num,valid=True,stopped=True):self.pid,self.num,self.valid,self.stopped=pid,num,valid,stopped
 def is_valid(self):return self.valid
 def threads(self):return [types.SimpleNamespace(ptid=(self.pid,self.pid,0),is_valid=lambda:True,is_stopped=lambda:self.stopped)]
class Event:
 def __init__(self):self.breakpoints=[types.SimpleNamespace(number=90,type=1)]
class Signal:pass
class Frame:
 def __init__(self,pc):self.v=pc
 def pc(self):return self.v
 def is_valid(self):return True
 def older(self):return None
class Kernel:
 def __init__(self,n=0,present=False,wrongparent=False,clock=10.):
  self.original=dict(pid=13,ppid=os.getpid(),start_ticks=100)
  self.first=dict(pid=20,ppid=13,start_ticks=110)
  self.child=dict(pid=20 if n==0 else 21,ppid=(13 if n==0 else 20) if not wrongparent else 99,start_ticks=110+n)
  self.parent=self.original if n==0 else self.first
  self.ids={13:self.original,20:self.first};self.ids[self.child['pid']]=self.child
  self.infs=[Inf(13,1)]+([Inf(20,4)] if n else [])+([Inf(self.child['pid'],4+n)] if present else [])
  self.selected=self.infs[0 if n==0 else 1];self.statem='t';self.now=clock;self.badns=False;self.badcg=False
  self.selectedthread=self.selected.threads()[0]
  self.g=types.SimpleNamespace(inferiors=lambda:self.infs,selected_inferior=lambda:self.selected,
   selected_thread=lambda:self.selectedthread,parameter=lambda name:False,BP_CATCHPOINT=1,
   BreakpointEvent=Event,SignalEvent=Signal,newest_frame=lambda:Frame(0x500000+(policy.FIRST_FORK_RETURN if n==0 else policy.SECOND_FORK_RETURN)))
  self.state={'process':dict(self.original,gdb_pid=os.getpid(),inferior=1),'records':[],'error':None}
  self.o=object.__new__(c.BoundaryCollector);o=self.o
  o.p={'original':copy.deepcopy(self.original),'reaper':dict(pid=1,ppid=0,start_ticks=50),
       'operation':dict(operation_id='synthetic',nonce='0'*32,deadline_monotonic=100.),'library':{'path':'synthetic-library'}}
  o.n={'STATE':self.state};o.g=self.g;o.known={13:copy.deepcopy(self.original)}
  if n:o.known[20]=copy.deepcopy(self.first)
  o._birth_refusal_attempted=False;o.refusal=None;o.host_witness={'cgroup':{k:0 for k in ('directory_host_stamp','cpu_max','memory_max','pids_max','cpu_usage_origin_usec')}}
  o._membership=b'0::/synthetic\n';o._release_digest='a'*64;o._unit_digest='b'*64
  o._inherited_limits={'gdb':b'Max cpu time Max address space','original':b'Max cpu time Max address space'}
  o._stat_process=lambda pid:(copy.deepcopy(self.ids[pid]),{})
  o._bind_runtime=lambda pid:None;o._bound_environment=lambda:None;o._window=lambda:{'synthetic':'marker'}
  o._ns=lambda pid:{'pid':{'dev':1,'ino':2 if self.badns and pid==13 else 1}}
  o.current_environment=lambda pid:{'synthetic':'env'};o.config=lambda pid:{'synthetic':'config'}
  o._regions=lambda pid:[{'path':'synthetic-library','perms':'r-xp','start':0x500000}]
  o.image_binding=lambda *x:{'load_bias':0x500000};o.fds=lambda pid:{}
  o._release=lambda:({},dict(unit='synthetic',invocation_id='0'*32),None,None)
  def read(path,limit):
   if path.endswith('/children'):return str(self.child['pid']).encode()
   if '/task/' in path and path.endswith('/stat'):
    pid=int(path.split('/')[2]);d=self.ids[pid];fields=[self.statem,str(d['ppid'])]+['0']*20;fields[19]=str(d['start_ticks'])
    return ('%d (synthetic) %s\n'%(pid,' '.join(fields))).encode()
   if path.endswith('/cgroup'):return b'0::/foreign\n' if self.badcg and path.startswith('/proc/13/') else o._membership
   if path.endswith('/limits'):return b'Max cpu time Max address space'
   raise AssertionError('unmodeled synthetic read:'+path)
  o._read=read
  self.adapter=object.__new__(a.Adapter);ad=self.adapter
  ad.g=self.g;ad.n=o.n;ad.collector=o;ad.b={'runtime':dict(o.p['operation'],operation_deadline_monotonic=100.)};ad.b['runtime'].pop('deadline_monotonic')
  ad.boundary_count=0;ad.init_active=True;ad.finished_initialization=False
  ad.pending=None;ad.pending_stop=None;ad.to_create=[];ad.to_retire=[];ad.catchpoints={90:'fork'};ad.known={};ad.binding={'load_bias':0x500000}
  ad.m={'collector_pins':{'library':{}}};ad.p=policy.__dict__
  ad.spawn_signature={'path_pointer':1,'image':{'path':'/synthetic/helper'},'argv_pointer':2,'fdlist_pointer':3,'fdlist_raw':b'x'*32}
  ad.string=lambda *x:None;ad.memory=lambda ptr,count: (struct.pack('<QQQ',4,5,0) if ptr==2 else b'x'*32 if ptr==3 else bytes.fromhex(a.SITE_BYTES['first_fork_return' if n==0 else 'second_fork_return']))
  o.pinned_file=lambda image:None
  children=[] if n==0 else [dict(identity=copy.deepcopy(self.first),inferior=4,exit_code=None,absent=False)]
  self.births=[]
  def birth(ctx,parent,child,inf,**kw):
   self.births.append((copy.deepcopy(parent),copy.deepcopy(child),inf,kw));children.append({'identity':child,'inferior':inf})
  ad.c=types.SimpleNamespace(current={'children':children,'thread':[13,13,0],'branch':'list_dirs'},birth=birth)
  ad.clone_entries={(self.parent['pid'],policy.FIRST_FORK_RETURN if n==0 else policy.SECOND_FORK_RETURN)}
  ad.observations=[]
  paper=types.SimpleNamespace(clear_pending=lambda:None,to_create=[])
  multi=a.MultiCustody(paper,ad);multi.queue_stop=lambda event:False
  self.saved=[]
  nativepath=refs['outer/deps/native_return_observer.py'];tree=ast.parse(nativepath.read_bytes())
  funcs=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('fail','stopped')]
  self.native={'gdb':self.g,'helper':multi,'STATE':self.state,'pending_action':None,
               'save':lambda:self.saved.append(copy.deepcopy(self.state))}
  exec(compile(ast.Module(body=funcs,type_ignores=[]),str(nativepath),'exec'),self.native)
 def run(self):
  # All accesses to kernel state stay within synthetic methods above.
  with patch.object(c.os,'listdir',lambda path:[str(int(path.split('/')[2]))]),patch.object(c.time,'monotonic',lambda:self.now):
   self.native['stopped'](Event())
  return self.state['error']

class ForkControls(unittest.TestCase):
 def test_pending_inferior_first_and_second_fork_fail_after_full_context(self):
  for n in (0,1):
   with self.subTest(n=n):
    x=Kernel(n);self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth')
    d=x.state['gpgme_collector_birth_refusal'];self.assertEqual(d['requested_pid'],20+n);self.assertEqual(d['observed_identity'],x.child)
    self.assertEqual(d['matching_valid_inferior_count'],0);self.assertEqual(d['known_parent_count'],1)
    self.assertEqual(x.adapter.boundary_count,1);self.assertEqual(x.births,[]);self.assertNotIn(20+n,x.o.known)
    self.assertIsNone(x.adapter.pending);self.assertEqual(x.adapter.to_create,[])
    self.assertEqual(x.saved[-1]['gpgme_collector_birth_refusal'],d)
    self.assertTrue(any(v['source_role']=='adapter' for v in d['source_frames']))
 def test_existing_registered_first_and_second_fork_route_preserved(self):
  for n in (0,1):
   with self.subTest(n=n):
    x=Kernel(n,present=True);self.assertIsNone(x.run());self.assertEqual(len(x.births),1)
    self.assertEqual(x.adapter.pending,'CONTINUE');self.assertNotIn('gpgme_collector_birth_refusal',x.state)
 def test_wrong_parent_and_duplicate_matching_inferiors_remain_refused(self):
  for mode in ('wrongparent','duplicate','invalid'):
   x=Kernel(present=True,wrongparent=mode=='wrongparent')
   if mode=='duplicate':x.infs.append(Inf(20,6))
   if mode=='invalid':x.infs[-1].valid=False
   self.assertIsNotNone(x.run());self.assertEqual(x.births,[]);self.assertIsNone(x.adapter.pending)
   if mode=='wrongparent':self.assertEqual(x.state['gpgme_collector_birth_refusal']['known_parent_count'],0)
 def test_allstop_kernelstop_namespace_cgroup_and_clock_negatives(self):
  for mode,expected in [('allstop','selected_thread'),('kernelstop','kernel_thread_not_stopped'),('namespace','original_namespaces'),('cgroup','current_cgroup_membership_changed'),('clock','resource_boundary_changed')]:
   with self.subTest(mode=mode):
    x=Kernel()
    if mode=='allstop':x.infs[0].stopped=False
    if mode=='kernelstop':x.statem='R'
    if mode=='namespace':x.badns=True
    if mode=='cgroup':x.badcg=True
    if mode=='clock':x.now=101.
    self.assertIn(expected,x.run());self.assertEqual(x.births,[]);self.assertIsNone(x.adapter.pending)
    self.assertNotIn('gpgme_collector_birth_refusal',x.state)
 def test_known_birth_and_parent_birth_changes_keep_existing_guards(self):
  for mode in ('child','parent'):
   x=Kernel(present=mode=='child')
   if mode=='child':x.o.known[20]=dict(x.child,start_ticks=1)
   else:
    x=Kernel(present=True);x.ids[13]=dict(x.original,start_ticks=99)
   self.assertIn('birth_changed',x.run());self.assertEqual(x.births,[])
 def test_diagnostic_construction_failure_is_once_and_never_changes_first_guard(self):
  x=Kernel();calls=[]
  def broken(*args):calls.append(1);raise OSError('private content never rendered')
  x.o._record_birth_refusal=broken
  self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth')
  self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth');self.assertEqual(calls,[1])
  self.assertNotIn('gpgme_collector_birth_refusal',x.state);self.assertEqual(x.births,[])
 def test_diagnostic_is_first_only_bounded_numeric_and_no_source_paths(self):
  x=Kernel();x.run();first=copy.deepcopy(x.state['gpgme_collector_birth_refusal'])
  x.child=dict(x.child,start_ticks=999);x.ids[20]=x.child;x.run()
  self.assertEqual(first,x.state['gpgme_collector_birth_refusal'])
  raw=json.dumps(first);self.assertLess(len(raw),4096);self.assertNotIn('/home/',raw)
  self.assertLessEqual(len(first['source_frames']),8)
  for f in first['source_frames']:self.assertEqual(set(f),{'source_role','line'});self.assertIs(type(f['line']),int)
 def test_preexisting_diagnostic_and_state_publication_failure_preserve_guard(self):
  x=Kernel();x.state['gpgme_collector_birth_refusal']={'sentinel':1};self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth')
  self.assertEqual(x.state['gpgme_collector_birth_refusal'],{'sentinel':1})
  class Broken(dict):
   def __setitem__(self,k,v):
    if k=='gpgme_collector_birth_refusal':raise OSError('synthetic')
    super().__setitem__(k,v)
  x=Kernel();x.state=Broken(x.state);x.o.n['STATE']=x.state;x.native['STATE']=x.state
  self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth');self.assertTrue(x.o._birth_refusal_attempted)
 def test_missing_valid_gdb_ptrace_representation_does_not_gain_custody(self):
  x=Kernel(present=True);x.infs[-1].valid=False
  with self.assertRaisesRegex(RuntimeError,'^gpgme_collector_unowned_or_unobserved_birth$'):x.o.proc(20)
  self.assertNotIn(20,x.o.known);self.assertEqual(x.state['gpgme_collector_birth_refusal']['matching_valid_inferior_count'],0)
  # Invalid representation is a pure input; no claim of real kernel ptrace
  # status, unobserved custody, or safe release follows from this fixture.
 def test_first_source_frame_is_the_original_failed_guard_line(self):
  x=Kernel();x.run();tree=ast.parse((B/'candidate/outer/deps/gpgme_boundary_collector.py').read_bytes())
  guard=next(v for v in ast.walk(tree) if isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='need' and len(v.args)==2 and isinstance(v.args[1],ast.Constant) and v.args[1].value=='gpgme_collector_unowned_or_unobserved_birth')
  self.assertEqual(x.state['gpgme_collector_birth_refusal']['source_frames'][0],{'source_role':'collector','line':guard.lineno})
 def test_out_of_kernel_numeric_diagnostic_bound_cannot_replace_guard(self):
  x=Kernel();x.ids[20]=dict(x.child,start_ticks=1<<65)
  self.assertEqual(x.run(),'gpgme_collector_unowned_or_unobserved_birth')
  self.assertNotIn('gpgme_collector_birth_refusal',x.state);self.assertTrue(x.o._birth_refusal_attempted)
 def test_prior_first_error_stays_first_and_diagnostic_cannot_grant(self):
  x=Kernel();x.state['error']='earlier_guard';x.state['model_declared_child_safe']=True
  self.assertEqual(x.run(),'earlier_guard');self.assertEqual(x.births,[]);self.assertIsNone(x.adapter.pending)

if __name__=='__main__':unittest.main(verbosity=2)
