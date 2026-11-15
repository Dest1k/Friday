import ast,copy,hashlib,json,os,stat,tempfile,time,types,unittest
from pathlib import Path
B=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115')
R=B/'review'
def load(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
pure=load(R/'independent_controls.final.py','review_pure')
host=load(B/'host/ownc_root_controller.py','review_host')
FINAL='cca495b5d989b22763fb8a9de16ec1afe9316f73e4fef0aeb9d3fc27f69e60be'
snapshot=json.loads((B/'REVIEW-SNAPSHOT.json').read_bytes())
class FinalConsumers(unittest.TestCase):
 def fixture(self):
  d=pure.c['projection_failure_metadata'](b'1000 0 1\n',65535,pure.witness(),pure.COL,None,RuntimeError('synthetic'))
  return d
 def closed(self):
  return dict(status='REFUSED_OWNED_CGROUP_EMPTY',retirement_snapshot=[None,dict(populated=0,pids=[])],invocation_id='a'*32,cgroup_path='/synthetic')
 def test_final_snapshot_and_exact_source_refs(self):
  self.assertEqual(hashlib.sha256((B/'REVIEW-SNAPSHOT.json').read_bytes()).hexdigest(),FINAL)
  for r in snapshot['changed_and_current_refs']:
   with self.subTest(path=r['path']):self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256'])
  refs=json.loads((B/'CURRENT-REFERENCE-CHECK.json').read_bytes())['current_refs']
  self.assertEqual(len(refs),45)
  for r in refs:self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_all_four_actual_consumers_and_future_templates(self):
  for variant,refs in snapshot['current4'].items():
   with self.subTest(variant=variant):
    for r in refs.values():self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256'])
    plan=json.loads(Path(refs['plan_ref']['path']).read_bytes());prepared=host.inspect_plan(plan)
    self.assertEqual(prepared['variant'],variant)
    for key in ['runtime_template','gpgme_runtime_template']:
     for field in ['operation_id','nonce','operation_deadline_monotonic']:self.assertIsNone(prepared[key][field])
    gb=plan['observer']['gpgme_engine_init'];manifest=json.loads(Path(gb['manifest']['path']).read_bytes())
    for field in ['operation','original','reaper','uid_projection','private_roots','cgroup']:self.assertIsNone(manifest['collector_pins'][field])
    self.assertEqual(gb['collector']['sha256'],'0bef26e32fa48aad5f3c819be811732db61bc6fda41395fd9457bc51e3361cba')
 def test_optional_terminal_absence_preserves_prior_behavior(self):
  with tempfile.TemporaryDirectory(dir=R,prefix='purefixture-') as d:
   scope=host.host_work_scope(d);self.assertEqual(host.read_terminal(scope,dict(nonce='a'*32),self.closed(),deadline=time.monotonic()+3),{})
 def test_optional_terminal_validated_and_non_authoritative(self):
  with tempfile.TemporaryDirectory(dir=R,prefix='purefixture-') as d:
   scope=host.host_work_scope(d);p=Path(d)/'gpgme-uid-projection-refusal.json';p.write_text(json.dumps(self.fixture()));p.chmod(0o600)
   records=host.read_terminal(scope,dict(nonce='a'*32),self.closed(),deadline=time.monotonic()+3)
   self.assertEqual(records['uid_projection_failure_diagnostic']['status'],'PRESENT_VALIDATED_METADATA')
   self.assertEqual(set(records),{'uid_projection_failure_diagnostic'})
 def test_optional_bad_partial_and_types_are_isolated(self):
  for kind in ['partial','boolean','rights','size','hardlink','symlink']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory(dir=R,prefix='purefixture-') as d:
    scope=host.host_work_scope(d);p=Path(d)/'gpgme-uid-projection-refusal.json';value=self.fixture()
    if kind=='boolean':value['current_userns']['dev']=True
    p.write_text('{' if kind=='partial' else ' '*8193 if kind=='size' else json.dumps(value));p.chmod(0o600)
    if kind=='rights':p.chmod(0o644)
    if kind=='hardlink':os.link(p,Path(d)/'extra')
    if kind=='symlink':
     p.rename(Path(d)/'target');p.symlink_to('target')
    records=host.read_terminal(scope,dict(nonce='a'*32),self.closed(),deadline=time.monotonic()+3)
    self.assertEqual(records['uid_projection_failure_diagnostic']['status'],'UNAVAILABLE')
    self.assertNotIn('message',records['uid_projection_failure_diagnostic'])
 def test_optional_failure_preserves_original_mandatory_records(self):
  with tempfile.TemporaryDirectory(dir=R,prefix='purefixture-') as d:
   scope=host.host_work_scope(d);nonce='a'*32;op='fixture'
   files={'held-fixture-supervisor-result.json':dict(schema='frw.own-held-font-fixture-supervisor-result.v1',operation_id=op,nonce=nonce,status='REFUSED',refusal_code='original'),
    'native-trace.json':dict(schema='frw.own-held-font-fixture-trace.v1',kind='OWN_POPEN_FIXTURE_ONLY',nonce=nonce,first_refusal='original')}
   for name,value in files.items():p=Path(d)/name;p.write_text(json.dumps(value));p.chmod(0o600)
   p=Path(d)/'gpgme-uid-projection-refusal.json';p.write_text('{');p.chmod(0o600)
   records=host.read_terminal(scope,dict(nonce=nonce,operation_id=op),self.closed(),deadline=time.monotonic()+3)
   self.assertEqual(records['supervisor']['refusal_code'],'original');self.assertEqual(records['trace']['first_refusal'],'original')
   self.assertEqual(records['uid_projection_failure_diagnostic']['status'],'UNAVAILABLE')
 def test_unconfirmed_cleanup_refuses_before_optional_read(self):
  with tempfile.TemporaryDirectory(dir=R,prefix='purefixture-') as d:
   scope=host.host_work_scope(d);closed=self.closed();closed['status']='UNKNOWN'
   with self.assertRaisesRegex(RuntimeError,'cgroup_not_confirmed_empty'):host.read_terminal(scope,dict(nonce='a'*32),closed,deadline=time.monotonic()+3)
 def test_root_diagnostic_rejects_unbounded_or_extra_content(self):
  for update in [dict(extra='raw content'),dict(exception_class='bad/message'),dict(self_map_sha256='x'*64),dict(actual_overflowuid=True),dict(host_map_rows=341)]:
   data=self.fixture();data.update(update)
   with self.assertRaises(RuntimeError):host.uid_projection_diagnostic(data)
if __name__=='__main__':unittest.main(verbosity=2)
