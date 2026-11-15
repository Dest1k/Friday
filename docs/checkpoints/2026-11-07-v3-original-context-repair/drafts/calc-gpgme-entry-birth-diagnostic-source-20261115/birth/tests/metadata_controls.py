"""Real four plan/prepared/source/bundle/validator joins, no actor effects."""
from pathlib import Path
import ast,copy,hashlib,json,types,unittest
B=Path(__file__).resolve().parents[1]
P=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-BOOTSTRAP-ENTRY-SOURCE-20261115')
UID=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115')
p=UID/'host/ownc_root_controller.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='98c0105bfeae6eeb852ccfae958acf1a95e39de24b1147f6edb118ad6fc0d0ae'
host=types.ModuleType('actual_host');host.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),host.__dict__)
class Metadata(unittest.TestCase):
 def test_actual_four_current_joins_and_unchanged_budgets(self):
  rows=[]
  for variant in ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name'):
   plan=json.loads((B/'inputs'/variant/'STATIC-PLAN.json').read_bytes());prepared=host.inspect_plan(plan)
   ns=host.load_module(plan['source_refs']['namespace'],'actual_namespace_'+variant)
   paper,gpgme=host.build_bundles(plan,prepared,ns,operation_id='source-only-unbound',nonce='0'*32,deadline=1.,validation_only=True)
   self.assertEqual(gpgme['collector_ref'],prepared['gpgme_binding']['collector'])
   self.assertEqual(gpgme['collector_ref']['path'],str(B/'candidate/outer/deps/gpgme_boundary_collector.py'))
   self.assertEqual(gpgme['adapter_ref'],json.loads((P/'inputs'/variant/'PREPARED.json').read_bytes())['gpgme_binding']['adapter'])
   self.assertEqual(plan['budgets'],json.loads((P/'inputs'/variant/'STATIC-PLAN.json').read_bytes())['budgets'])
   rows.append({'variant':variant,'current_collector_ref':gpgme['collector_ref'],'validator_ref':gpgme['validator_ref'],'adapter_ref':gpgme['adapter_ref'],'original_budgets':plan['budgets'],'actual_module_consumers_passed':True})
  (B/'tests/ACTUAL4-CONSUMERS.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
 def test_stale_collector_graph_rejected(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes());prior=json.loads((P/'inputs/worker_cached/PREPARED.json').read_bytes())
  plan['observer']['gpgme_engine_init']['collector']=prior['gpgme_binding']['collector']
  with self.assertRaisesRegex(RuntimeError,'^ownc_helper_binding_join$'):host.inspect_plan(plan)
 def test_corrupt_collector_pin_rejected(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes());ns=host.load_module(plan['source_refs']['namespace'],'badpin_namespace')
  binding=copy.deepcopy(plan['observer']['gpgme_engine_init']);binding['collector']['sha256']='0'*64
  with self.assertRaisesRegex(ns.Refused,'^pinned_source_changed$'):ns.gpgme_sources(binding)
 def test_successor_root_required(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes());plan['readonly_roots'].remove(str(B))
  with self.assertRaisesRegex(RuntimeError,'^ownc_readonly_source_not_mounted$'):host.inspect_plan(plan)
 def test_no_future_identity_clocks_or_released_children_added(self):
  selected=json.loads((B/'inputs/SELECTED-INPUTS.json').read_bytes())
  for refs in selected['variants'].values():
   prepared=json.loads(Path(refs['prepared_ref']['path']).read_bytes())
   for runtime in (prepared['runtime_template'],prepared['gpgme_runtime_template']):
    self.assertIsNone(runtime['operation_id']);self.assertIsNone(runtime['nonce']);self.assertIsNone(runtime['operation_deadline_monotonic'])
   manifest=json.loads(Path(prepared['gpgme_binding']['manifest']['path']).read_bytes())
   for key in ('original','reaper','operation'):self.assertIsNone(manifest['collector_pins'][key])
 def test_runtime_delta_has_only_attribution_and_original_guard(self):
  old=ast.parse((UID/'candidate/outer/deps/gpgme_boundary_collector.py').read_bytes())
  new=ast.parse((B/'candidate/outer/deps/gpgme_boundary_collector.py').read_bytes())
  def defs(tree):
   cls=next(v for v in tree.body if isinstance(v,ast.ClassDef) and v.name=='BoundaryCollector')
   return {v.name:ast.dump(v,include_attributes=False) for v in cls.body if isinstance(v,ast.FunctionDef)}
  before,after=defs(old),defs(new);self.assertEqual(set(after)-set(before),{'_record_birth_refusal'})
  self.assertEqual({k for k in before if before[k]!=after[k]},{'__init__','proc'})
  proc=next(v for v in new.body if isinstance(v,ast.ClassDef) and v.name=='BoundaryCollector')
  proc=next(v for v in proc.body if isinstance(v,ast.FunctionDef) and v.name=='proc')
  guard=next(v for v in ast.walk(proc) if isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='need' and len(v.args)==2 and isinstance(v.args[1],ast.Constant) and v.args[1].value=='gpgme_collector_unowned_or_unobserved_birth')
  oldproc=next(v for v in old.body if isinstance(v,ast.ClassDef) and v.name=='BoundaryCollector')
  oldproc=next(v for v in oldproc.body if isinstance(v,ast.FunctionDef) and v.name=='proc')
  oldguard=next(v for v in ast.walk(oldproc) if isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='need' and len(v.args)==2 and isinstance(v.args[1],ast.Constant) and v.args[1].value=='gpgme_collector_unowned_or_unobserved_birth')
  self.assertEqual(ast.dump(guard),ast.dump(oldguard))
if __name__=='__main__':unittest.main(verbosity=2)
