"""SOURCE-only real method tests with synthetic GDB/kernel boundaries.

Named function linespecs in this GDB model advance to a synthetic post-prologue
PC (+5 solely a test datum); numeric address locations retain entry ABI. No GDB,
process actor, /proc read, helper, namespace or executable image is invoked.
"""
from pathlib import Path
import ast,copy,hashlib,json,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parents[1]
OLD=Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115/candidate/outer/deps/gpgme_engine_gdb.py')
NEW=B/'candidate/outer/deps/gpgme_engine_gdb.py'
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
m=module(NEW,'entry_successor')
LIB='/synthetic/pinned/libgpgme.so.11';BASE=0x500000;ENTRY=BASE+m.SITE_OFFSETS['engine_entry'];STACK=0x700000
class SyntheticPath:
 def __init__(self,v):self.v=str(v)
 def __str__(self):return self.v
 def __truediv__(self,v):return SyntheticPath(self.v+'/'+str(v))
 def resolve(self):return self
 def exists(self):
  assert self.v.startswith('/proc/'),self.v
  return False
class Error(Exception):pass
class Value:
 is_unavailable=False;is_optimized_out=False
 def __init__(self,v):self.v=v
 def __int__(self):return self.v
class FakeGDB:
 error=Error
 def __init__(self):
  self.inf=types.SimpleNamespace(num=1,pid=501);self.pc=ENTRY;self.rsp=STACK;self.symbol=ENTRY;self.owner=LIB
  self.symbol_ready=True;self.bp_error=False;self.expressions=[];self.bps=[];self.commands=[]
  self.arch='i386:x86-64';self.location_shift=0;g=self
  class Breakpoint:
   def __init__(self,spec,internal=False):
    if g.bp_error:raise Error('synthetic construction error')
    self.spec=spec;self.internal=internal;self.number=len(g.bps)+1;self.inferior=None;self.enabled=True;self.valid=True
    self.address=(int(spec[1:],16)+g.location_shift) if spec.startswith('*0x') else g.symbol+5
    g.bps.append(self)
   def is_valid(self):return self.valid
   def delete(self):self.valid=False
  self.Breakpoint=Breakpoint
 def parse_and_eval(self,expression):
  self.expressions.append(expression)
  if not self.symbol_ready:raise Error('synthetic missing symbol')
  if expression!='&gpgme_get_engine_info':raise AssertionError('unexpected evaluator request')
  return Value(self.symbol)
 def selected_inferior(self):return self.inf
 def selected_thread(self):return types.SimpleNamespace(ptid=(501,501,0),is_valid=lambda:True)
 def newest_frame(self):
  return types.SimpleNamespace(pc=lambda:self.pc,is_valid=lambda:True,
   architecture=lambda:types.SimpleNamespace(name=lambda:self.arch),
   read_register=lambda name:Value(self.rsp if name=='rsp' else 0))
 def solib_name(self,pc):return self.owner
 def breakpoints(self):return [b for b in self.bps if b.is_valid()]
 def execute(self,command,to_string=True):
  self.commands.append(command)
  if command.startswith('catch '):self.Breakpoint(command)
 def land(self,bp):
  self.pc=bp.address;self.rsp=STACK if bp.address==ENTRY else STACK-8
class Collector:
 def __init__(self,g,events):self.g=g;self.events=events;self.mapped=True;self.bad_bytes=False;self.current_environment_binds=0
 def maps(self,pid):
  self.events.append('maps');return [{'path':LIB}] if self.mapped else []
 def image_binding(self,pid,pin,pc):
  self.events.append('image');return {'load_bias':BASE,'relative_pc':pc-BASE}
 def bind_current_environment(self,pid):self.events.append('bindENV');self.current_environment_binds+=1
 def snapshot(self,pid,role,expected_thread):self.events.append('snapshot');return {'synthetic':True}
def fixture(source=m):
 g=FakeGDB();events=[];c=Collector(g,events)
 paper=types.SimpleNamespace(c=types.SimpleNamespace(e={'state':'CLOSED','children':[{'inferior':2,'pid':601},{'inferior':3,'pid':602}]}))
 o=source.Adapter.__new__(source.Adapter)
 o.g=g;o.n={'STATE':{'process':{'pid':501},'error':None}};o.m={'collector_pins':{'library':{'path':LIB}}};o.paper=paper;o.collector=c
 o.breakpoints=[];o.handlers={};o.retired=set();o.bootstrap=None;o.installed=False;o.pending_stop=None;o.pending=None;o.to_create=[];o.to_retire=[]
 o.init_active=False;o.finished_initialization=False;o.init_thread=None;o.init_stack=None;o.binding=None;o.process_guards=[];o.catchpoints={};o.exits={};o.c=None
 o.original=lambda:{'pid':501};o.publish=lambda:events.append('publish')
 o.ensure=lambda:events.append('ensure')
 o.context=lambda **k:(events.append('context') or {},{})
 def memory(address,count):
  if address==BASE+0x55558:return (1).to_bytes(8,'little')[:count]
  sites={BASE+m.SITE_OFFSETS[name]:bytes.fromhex(raw) for name,raw in m.SITE_BYTES.items()}
  raw=sites.get(address,b'\0'*count)
  if c.bad_bytes and address==ENTRY:raw=b'\0'*len(raw)
  return raw[:count]
 o.memory=memory
 return o,g,c,events
class EntryControls(unittest.TestCase):
 def run_entry(self,o,g):
  with patch.object(m,'Path',SyntheticPath):
   g.land(o.bootstrap);self.assertTrue(o.queue_stop(types.SimpleNamespace(breakpoints=[o.bootstrap])));return o.dispatch()
 def test_actual_changed_method_numeric_address_keeps_first_instruction_and_abi(self):
  o,g,c,e=fixture();o.install();self.assertEqual(o.bootstrap.address,ENTRY);self.assertTrue(o.bootstrap.internal)
  self.assertEqual(o.bootstrap.inferior,1);self.assertTrue(o.bootstrap.spec.startswith('*0x'))
  self.assertEqual(self.run_entry(o,g),'CONTINUE');self.assertEqual(o.init_stack,STACK);self.assertTrue(o.init_active)
  self.assertTrue(o.installed);self.assertEqual(c.current_environment_binds,1);self.assertEqual(len(o.process_guards),3)
 def test_predecessor_symbolic_prologue_adjustment_is_meaningful_counterexample(self):
  old=module(OLD,'entry_predecessor');o,g,c,e=fixture(old);o.install();g.land(o.bootstrap)
  self.assertEqual(g.pc,ENTRY+5)
  with patch.object(old,'Path',SyntheticPath),self.assertRaisesRegex(RuntimeError,'^gpgme_bootstrap_exact_symbol_offset$'):o.bootstrap_entry()
  self.assertFalse(o.init_active);self.assertFalse(o.installed)
 def test_missing_symbol_no_pending_breakpoint_then_late_load_retries_once(self):
  o,g,c,e=fixture();g.symbol_ready=False;o.install();self.assertIsNone(o.bootstrap);self.assertEqual(g.bps,[])
  g.symbol_ready=True;o.install();o.install();self.assertEqual(len(g.bps),1);self.run_entry(o,g)
 def test_mapping_not_yet_present_defers_without_symbol_or_numeric_fallback(self):
  o,g,c,e=fixture();c.mapped=False;o.install();self.assertEqual(g.expressions,[]);self.assertEqual(g.bps,[])
  c.mapped=True;o.install();self.assertEqual(o.bootstrap.address,ENTRY)
 def test_unbound_process_and_foreign_selected_inferior_do_not_arm(self):
  for branch in ('process','inferior'):
   o,g,c,e=fixture()
   if branch=='process':o.n['STATE']['process']=None
   else:g.inf.num=4
   o.install();self.assertEqual(g.bps,[]);self.assertEqual(e,[])
 def test_breakpoint_construction_error_does_not_publish_or_install(self):
  o,g,c,e=fixture();g.bp_error=True;o.install();self.assertIsNone(o.bootstrap);self.assertEqual(o.handlers,{})
  self.assertFalse(o.installed);self.assertNotIn('bindENV',e)
 def test_callback_has_no_observer_mutation(self):
  o,g,c,e=fixture();o.install();before=copy.copy(e)
  self.assertTrue(o.bootstrap.stop());self.assertTrue(o.bootstrap.stop());self.assertEqual(e,before);self.assertFalse(o.init_active)
 def test_owner_interposition_and_executable_PLT_refuse_before_paper_or_image(self):
  for owner in (None,'/synthetic/interposer.so','/synthetic/fixture-executable'):
   o,g,c,e=fixture();o.install();g.owner=owner
   with patch.object(m,'Path',SyntheticPath),self.assertRaisesRegex(RuntimeError,'^gpgme_bootstrap_symbol_owner$'):self.run_entry(o,g)
   self.assertNotIn('image',e);self.assertFalse(o.init_active)
 def test_paper_must_be_closed_before_any_image_binding_or_helper_admission(self):
  o,g,c,e=fixture();o.install();o.paper.c.e['state']='RUNNING'
  with self.assertRaisesRegex(RuntimeError,'^gpgme_requires_observed_paper_closed_inferiors_2_3$'):self.run_entry(o,g)
  self.assertNotIn('image',e);self.assertFalse(o.init_active)
 def test_paper_descendant_absence_guard_preserved(self):
  o,g,c,e=fixture();o.install()
  with patch.object(SyntheticPath,'exists',return_value=True),self.assertRaisesRegex(RuntimeError,'^gpgme_paper_descendant_present$'):self.run_entry(o,g)
  self.assertNotIn('image',e)
 def test_numerically_adjusted_location_still_refuses_exact_offset(self):
  o,g,c,e=fixture();g.location_shift=1;o.install()
  with self.assertRaisesRegex(RuntimeError,'^gpgme_bootstrap_exact_symbol_offset$'):self.run_entry(o,g)
  self.assertFalse(o.init_active);self.assertNotIn('bindENV',e)
 def test_wrong_symbol_offset_with_same_library_refuses(self):
  o,g,c,e=fixture();g.symbol=ENTRY+16;o.install()
  with self.assertRaisesRegex(RuntimeError,'^gpgme_bootstrap_exact_symbol_offset$'):self.run_entry(o,g)
  self.assertNotIn('bindENV',e)
 def test_wrong_entry_bytes_refuses_before_ENV_and_site_installation(self):
  o,g,c,e=fixture();c.bad_bytes=True;o.install()
  with self.assertRaisesRegex(RuntimeError,'^gpgme_exact_site_engine_entry$'):self.run_entry(o,g)
  self.assertNotIn('bindENV',e);self.assertFalse(o.installed)
 def test_wrong_architecture_refuses_before_ABI_capture(self):
  o,g,c,e=fixture();g.arch='aarch64';o.install()
  with self.assertRaisesRegex(RuntimeError,'^gpgme_frame_architecture$'):self.run_entry(o,g)
  self.assertIsNone(o.init_stack)
 def test_wrong_inferior_at_queue_refuses(self):
  o,g,c,e=fixture();o.install();g.inf.num=4
  with self.assertRaisesRegex(RuntimeError,'^gpgme_breakpoint_event_inferior$'):o.queue_stop(types.SimpleNamespace(breakpoints=[o.bootstrap]))
 def test_stop_context_change_before_dispatch_refuses(self):
  o,g,c,e=fixture();o.install();g.land(o.bootstrap);o.queue_stop(types.SimpleNamespace(breakpoints=[o.bootstrap]));g.pc+=1
  with self.assertRaisesRegex(RuntimeError,'^gpgme_queued_stop_context_changed$'):o.dispatch()
  self.assertFalse(o.init_active)
 def test_first_binding_order_paper_image_bytes_ENV_snapshot_then_initialization(self):
  o,g,c,e=fixture();o.install();self.run_entry(o,g)
  self.assertLess(e.index('image'),e.index('bindENV'));self.assertLess(e.index('bindENV'),e.index('snapshot'));self.assertLess(e.index('snapshot'),e.index('ensure'))
 def test_cached_getter_reuses_exact_entry_without_ENV_rebind_or_site_duplicates(self):
  o,g,c,e=fixture();o.install();self.run_entry(o,g);count=len(g.bps);c.current_environment_binds=0
  o.init_active=False;o.finished_initialization=True;o.process_guards=[];e.clear();self.run_entry(o,g)
  self.assertEqual(len(g.bps),count);self.assertEqual(c.current_environment_binds,0);self.assertNotIn('ensure',e);self.assertNotIn('context',e)
 def test_cached_engine_list_guard_preserved(self):
  o,g,c,e=fixture();o.install();self.run_entry(o,g);o.init_active=False;o.finished_initialization=True;read=o.memory;o.memory=lambda a,n:b'\0'*n if a==BASE+0x55558 else read(a,n)
  with self.assertRaisesRegex(RuntimeError,'^gpgme_cached_engine_list_changed$'):self.run_entry(o,g)
 def test_repeated_initialization_guard_preserved(self):
  o,g,c,e=fixture();o.install();self.run_entry(o,g)
  with self.assertRaisesRegex(RuntimeError,'^gpgme_repeated_or_foreign_engine_initialization$'):self.run_entry(o,g)
 def test_error_dispatch_keeps_first_error_and_clears_pending_without_construction(self):
  o,g,c,e=fixture();o.install();o.n['STATE']['error']='first-refusal';o.to_create=[(123,None,1,False)]
  self.assertIsNone(o.dispatch());self.assertEqual(o.n['STATE']['error'],'first-refusal');self.assertEqual(o.to_create,[]);self.assertFalse(o.init_active)
 def test_only_install_AST_changes_all_guards_and_cleanup_unchanged(self):
  def methods(p):
   tree=ast.parse(p.read_text());return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Adapter' for n in n.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  old,new=methods(OLD),methods(NEW);self.assertEqual(set(old),set(new));self.assertEqual([k for k in old if old[k]!=new[k]],['install'])
if __name__=='__main__':unittest.main(verbosity=2)
