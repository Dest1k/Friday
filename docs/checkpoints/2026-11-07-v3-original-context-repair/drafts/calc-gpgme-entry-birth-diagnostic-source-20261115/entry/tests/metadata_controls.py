"""Nearest actual metadata consumers, SOURCE only, no actor effects."""
from pathlib import Path
import copy,hashlib,json,types,unittest
B=Path(__file__).resolve().parents[1]
UID=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115')
p=UID/'host/ownc_root_controller.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='98c0105bfeae6eeb852ccfae958acf1a95e39de24b1147f6edb118ad6fc0d0ae'
host=types.ModuleType('unchanged_actual_host');host.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),host.__dict__)
class ActualMetadata(unittest.TestCase):
 def test_actual_four_source_plans_and_nearest_module_consumers(self):
  for variant in ('worker_cached','extra_fork','forbidden_gpg_home','wrong_gpgconf_name'):
   with self.subTest(variant=variant):
    plan=json.loads((B/'inputs'/variant/'STATIC-PLAN.json').read_bytes());prepared=host.inspect_plan(plan)
    ns=host.load_module(plan['source_refs']['namespace'],'actual_namespace_'+variant)
    paper,gpgme=host.build_bundles(plan,prepared,ns,operation_id='source-only-unbound',nonce='0'*32,deadline=1.,validation_only=True)
    self.assertEqual(gpgme['adapter_ref'],prepared['gpgme_binding']['adapter']);self.assertEqual(gpgme['adapter_ref']['path'],str(B/'candidate/outer/deps/gpgme_engine_gdb.py'))
    self.assertEqual(plan['budgets'],json.loads((UID/'inputs'/variant/'STATIC-PLAN.json').read_bytes())['budgets'])
 def test_stale_adapter_graph_mismatch_rejected_by_actual_host(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes())
  prior=json.loads((UID/'inputs/worker_cached/PREPARED.json').read_bytes())
  plan['observer']['gpgme_engine_init']['adapter']=prior['gpgme_binding']['adapter']
  with self.assertRaisesRegex(RuntimeError,'^ownc_helper_binding_join$'):host.inspect_plan(plan)
 def test_corrupt_adapter_pin_rejected_by_actual_pinned_source_loader(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes())
  ns=host.load_module(plan['source_refs']['namespace'],'actual_namespace_bad_pin')
  binding=copy.deepcopy(plan['observer']['gpgme_engine_init']);binding['adapter']['sha256']='0'*64
  with self.assertRaisesRegex(ns.Refused,'^pinned_source_changed$'):ns.gpgme_sources(binding)
 def test_new_source_root_is_required_by_actual_mount_graph_guard(self):
  plan=json.loads((B/'inputs/worker_cached/STATIC-PLAN.json').read_bytes());plan['readonly_roots'].remove(str(B))
  with self.assertRaisesRegex(RuntimeError,'^ownc_readonly_source_not_mounted$'):host.inspect_plan(plan)
 def test_templates_still_have_no_operation_nonce_or_clocks(self):
  selected=json.loads((B/'inputs/SELECTED-INPUTS.json').read_bytes())
  for refs in selected['variants'].values():
   p=json.loads(Path(refs['prepared_ref']['path']).read_bytes())
   for runtime in (p['runtime_template'],p['gpgme_runtime_template']):
    self.assertIsNone(runtime['operation_id']);self.assertIsNone(runtime['nonce']);self.assertIsNone(runtime['operation_deadline_monotonic'])
if __name__=='__main__':unittest.main(verbosity=2)
