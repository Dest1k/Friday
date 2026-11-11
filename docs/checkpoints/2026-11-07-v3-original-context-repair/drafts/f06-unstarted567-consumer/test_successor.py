from pathlib import Path
import sys,os,json,copy,types,importlib.util,unittest,tempfile,hashlib,contextlib
from unittest.mock import patch
sys.dont_write_bytecode=True
os.umask(0o077)
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('successor',B/'candidate/harness.py'); h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class Controls(unittest.TestCase):
 def setUp(self):
  self.scratch=tempfile.TemporaryDirectory(dir=B,prefix='pure-'); self.root=Path(self.scratch.name)
  self.original_ref=h.ref_read; self.reads=[]
  self.old={k:json.loads(self.original_ref(ref)) for k,ref in h.OLD_EVIDENCE.items()}
  original=self.old['binding']
  self.m={k:copy.deepcopy(original[k]) for k in ('fixtures','root_generation_result','independent_input_oracle','credential','credential_keys','root_generation_operation_id')}
  self.m.update(schema='friday.f06.unstarted567-binding.v1',assignment=h.NEW_ASSIGNMENT,operation_id=h.OPERATION,
    execution_ids=list(h.SUBSET),original_evidence=h.OLD_EVIDENCE,
    harness_sha256=h.sha(Path(h.__file__).read_bytes()),native_source_pins_sha256=h.sha((h.BASE/'SOURCE-PINS.json').read_bytes()),
    limits={'wall_seconds':h.WALL,'cpu_seconds':h.CPU,'address_space_bytes':h.MEMORY,'parent_disk_bytes':h.PARENT_CAP,'harness_disk_bytes':h.OWN_CAP,'cpu_count':2},
    effect_scope={'state':'own_synthetic_only','network':False,'Office':False,'model':False,'input_writes':False,'output':'retained_encrypted_derivatives_only','fixtures':list(h.SUBSET)},
    input_custody=[dict(r['input'],identity=h.stat_identity(r['input']['path'])) for r in original['fixtures']],
    root_admission={'old_effect_closed':True,'old_actor_pids':[],'old_clocks_retained':True,'slot_exclusively_held':True,'target567_unstarted_current':True,'source_only_import_readiness_pass':True,
       'cpu_affinity':sorted(os.sched_getaffinity(0))[:2],'markers':copy.deepcopy(h.EXPECTED_MARKERS),
       'old_workspace_closure':[{'path':p,'identity':h.stat_identity(p)} for p in h.EXPECTED_OLD_WORKSPACES]},
    work_path=str(h.BASE/'qualification-unstarted567'),once_path=str(h.BASE/'UNSTARTED567-ONCE.json'))
  self.grant={'schema':'friday.f06.unstarted567-root-grant.v1','assignment':h.NEW_ASSIGNMENT,'native567_authorized':True,'automatic_retry':False,'old_grant_reused_as_authority':False,'issued_unix':h.time.time()-1,'expires_unix':h.time.time()+200}
 def tearDown(self):self.scratch.cleanup()
 def checked(self,modify=None,grant_modify=None):
  m=copy.deepcopy(self.m);g=copy.deepcopy(self.grant)
  if modify:modify(m)
  raw=(json.dumps(m)+'\n').encode();mp=self.root/'request.json';mp.write_bytes(raw);mp.chmod(0o600)
  digest=h.sha(raw);g.update(manifest_sha256=digest,intent=m)
  if grant_modify:grant_modify(g)
  rawg=(json.dumps(g)+'\n').encode();gp=self.root/'grant.json';gp.write_bytes(rawg);gp.chmod(0o600)
  denied={r['input']['path'] for r in m['fixtures']}|{m['credential']['path']}
  def read(ref,*args,**kwargs):
   self.reads.append(ref['path'])
   if ref['path'] in denied:raise AssertionError('CIPHERTEXT_OR_CREDENTIAL_READ')
   return self.original_ref(ref,*args,**kwargs)
  with patch.object(h,'ref_read',read):return h.binding_check(mp,digest,gp,h.sha(rawg))
 def reject(self,modify=None,grant_modify=None):
  with self.assertRaises(h.Refused):self.checked(modify,grant_modify)
 def test_positive_exact567_metadata_only(self):
  result=self.checked();self.assertEqual([r['id'] for r in result['fixtures']],list(h.SUBSET));self.assertEqual(len(self.m['fixtures']),7)
  self.assertFalse(any(p in self.reads for p in [r['input']['path'] for r in self.m['fixtures']]+[self.m['credential']['path']]))
 def test_original_grant_not_authority(self):self.reject(grant_modify=lambda g:g.update(self.old['grant']))
 def test_original_operation_not_reused(self):self.reject(lambda m:m.update(operation_id=self.old['binding']['operation_id']))
 def test_exact_subset_rejects_any_old_row(self):
  for ids in (['f06-1','f06-5','f06-6','f06-7'],['f06-4','f06-5','f06-6'],['f06-5'],['f06-6','f06-5','f06-7'],list(h.SUBSET)*2):
   with self.subTest(ids=ids):self.reject(lambda m:m.update(execution_ids=ids))
 def test_full7_provenance_cannot_truncate(self):self.reject(lambda m:m.update(fixtures=m['fixtures'][4:]))
 def test_full7_semantics_cannot_change(self):self.reject(lambda m:m['fixtures'][0]['edit'].update(new_text='other'))
 def test_missing_grant_refuses(self):self.reject(grant_modify=lambda g:g.pop('native567_authorized'))
 def test_grant_reuse_assertion_refuses(self):self.reject(grant_modify=lambda g:g.update(old_grant_reused_as_authority=True))
 def test_grant_manifest_drift(self):self.reject(grant_modify=lambda g:g.update(manifest_sha256='0'*64))
 def test_grant_intent_drift(self):self.reject(grant_modify=lambda g:g.update(intent={}))
 def test_expired_grant(self):self.reject(grant_modify=lambda g:g.update(issued_unix=0,expires_unix=1))
 def test_unbounded_grant(self):self.reject(grant_modify=lambda g:g.update(expires_unix=g['issued_unix']+301))
 def test_future_grant(self):self.reject(grant_modify=lambda g:g.update(issued_unix=h.time.time()+1))
 def test_consumer_source_drift(self):self.reject(lambda m:m.update(harness_sha256='0'*64))
 def test_pins_drift(self):self.reject(lambda m:m.update(native_source_pins_sha256='0'*64))
 def test_old_evidence_drift(self):self.reject(lambda m:m['original_evidence']['once'].update(sha256='0'*64))
 def test_current_input_identity_drift(self):self.reject(lambda m:m['input_custody'][3]['identity'].__setitem__(1,0))
 def test_source_marker_substitute_refuses(self):self.reject(lambda m:m['root_admission']['markers'][0].update(path=str(self.root/'wrong')))
 def test_source_marker_digest_substitute_refuses(self):self.reject(lambda m:m['root_admission']['markers'][0].update(sha256='0'*64))
 def test_old_workspace_substitute_refuses(self):self.reject(lambda m:m['root_admission']['old_workspace_closure'][0].update(path=str(self.root)))
 def test_old_workspace_current_drift(self):self.reject(lambda m:m['root_admission']['old_workspace_closure'][0]['identity'].__setitem__(1,0))
 def test_root_fresh_admission_all_required(self):
  for key in ('old_effect_closed','old_clocks_retained','slot_exclusively_held','target567_unstarted_current','source_only_import_readiness_pass'):
   with self.subTest(key=key):self.reject(lambda m:m['root_admission'].update({key:False}))
 def test_old_actors_still_running(self):self.reject(lambda m:m['root_admission'].update(old_actor_pids=[123]))
 def test_two_cpus_required(self):self.reject(lambda m:m['root_admission'].update(cpu_affinity=m['root_admission']['cpu_affinity'][:1]))
 def test_resource_clock_cannot_reset_by_limits(self):self.reject(lambda m:m['limits'].update(wall_seconds=600))
 def test_work_relocation_refuses(self):self.reject(lambda m:m.update(work_path=str(self.root/'new')))
 def test_once_relocation_refuses(self):self.reject(lambda m:m.update(once_path=str(self.root/'new')))
 def test_existing_once_refuses(self):
  real=h.os.path.lexists
  with patch.object(h.os.path,'lexists',lambda p:True if str(p)==self.m['once_path'] else real(p)):self.reject()
 def test_existing_work_refuses(self):
  real=h.os.path.lexists
  with patch.object(h.os.path,'lexists',lambda p:True if str(p)==self.m['work_path'] else real(p)):self.reject()
 def test_existing_launch_refuses_default_admission(self):
  real=h.os.path.lexists
  with patch.object(h.os.path,'lexists',lambda p:True if str(p)==str(h.BASE/'unstarted567-launch.log') else real(p)):self.reject()
 def test_direct_worker_without_supervisor_refuses(self):
  with self.assertRaises(h.Refused):h.verify_supervisor(types.SimpleNamespace(launch_fd=None,supervisor_pid=None))
 def test_wrong_supervisor_pid_refuses(self):
  with self.assertRaises(h.Refused):h.verify_supervisor(types.SimpleNamespace(launch_fd=3,supervisor_pid=-1))
 def test_inherited_descriptor_identity_checked(self):
  path=self.root/'unstarted567-launch.log';path.touch(mode=0o600)
  foreign=self.root/'other.log';foreign.touch(mode=0o600)
  with path.open('ab') as good,foreign.open('ab') as bad,patch.object(h,'BASE',self.root):
   h.verify_supervisor(types.SimpleNamespace(launch_fd=good.fileno(),supervisor_pid=os.getppid()))
   with self.assertRaises(h.Refused):h.verify_supervisor(types.SimpleNamespace(launch_fd=bad.fileno(),supervisor_pid=os.getppid()))
 def test_once_exclusive_keeps_first_bytes(self):
  target=self.root/'once.json';h.dump(target,{'started':101},exclusive=True)
  before=target.read_bytes()
  with self.assertRaises(FileExistsError):h.dump(target,{'started':202},exclusive=True)
  self.assertEqual(before,target.read_bytes())
 def test_exact_pin_delta_and_all_hashes(self):
  pins=h.pins_check();delta=json.loads((B/'pins-delta.json').read_bytes())
  self.assertEqual(len(pins['files']),287);self.assertEqual(len(delta['added_exact_modules']),4)
  self.assertFalse(any(r['relative']=='tools/scoped_presentation_layout.py' for r in pins['files']))
  self.assertTrue(h.source_read_allowed(h.SOURCE/'tools/scoped_odf_review.py',pins))
  self.assertFalse(h.source_read_allowed(h.SOURCE/'tools/scoped_presentation_layout.py',pins))
  self.assertFalse(h.source_read_allowed(h.SOURCE/'.env',pins))
 def test_qualify_rejects_old_rows_before_any_read_or_native(self):
  with patch.object(h,'ref_read',side_effect=AssertionError('effect')):
   with self.assertRaises(h.Refused):h.qualify(object(),self.m,self.root)
 def supervisor_case(self,timeout,leftover=False):
  import io
  calls=[]
  class FakeProcess:
   pid=99999999
   returncode=0
   def __init__(self,*a,**k):
    calls.append(('popen',k));self.first=True
   def wait(self,timeout=None):
    calls.append(('wait',timeout))
    if self.first and timeout is not None and timeout_case:
     self.first=False;self.returncode=-9;raise h.subprocess.TimeoutExpired('fake',timeout)
    return self.returncode
  timeout_case=timeout
  def killpg(pid,sig):
   calls.append(('killpg',pid,sig))
   if sig==0:
    probes=[c for c in calls if c[0]=='killpg' and c[2]==0]
    if leftover and len(probes)==1:return
    raise ProcessLookupError()
  argv=['harness.py','run-unstarted567','--manifest',str(self.root/'metadata'),
    '--manifest-sha256','0'*64,'--root-grant',str(self.root/'grant'),'--root-grant-sha256','1'*64]
  with patch.object(h,'BASE',self.root),patch.object(h,'pins_check',lambda:None),patch.object(h,'budget',lambda:None),patch.object(h,'binding_check',lambda *a,**k:{}),patch.object(h.subprocess,'Popen',FakeProcess),patch.object(h.os,'killpg',killpg),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
   code=h.main()
  report=json.loads((self.root/'SUPERVISOR.json').read_bytes())
  self.assertEqual(code,124 if timeout else 2 if leftover else 0);self.assertEqual(report['timed_out'],timeout)
  self.assertEqual(report['wall_budget_seconds'],300);self.assertTrue(report['worker_reaped']);self.assertTrue(report['own_group_absent_observed'])
  self.assertFalse(report['automatic_retry']);self.assertTrue(report['partial_outputs_retained'])
  first=[c for c in calls if c[0]=='popen'][0];self.assertEqual(len(first[1]['pass_fds']),1)
  self.assertEqual([c for c in calls if c[0]=='wait'][0][1],300)
 def test_mock_supervisor_unexpected_actors_reconcile(self):self.supervisor_case(False,True)
 def test_mock_supervisor_normal_reaped(self):self.supervisor_case(False)
 def test_mock_supervisor_timeout_own_group_only(self):self.supervisor_case(True)
 def test_mock_loop_touches567_only(self):
  homes=[self.root/'a',self.root/'b']
  for p in homes:(p/'workspace').mkdir(parents=True,mode=0o700)
  calls=[]
  class ScopeDenied(Exception):pass
  class Retained:
   revoked=True
   def check(self):raise ScopeDenied()
  retained=Retained()
  scope=types.SimpleNamespace(ScopeDenied=ScopeDenied,scoped_file=lambda *a,**k:{'success':False,'error':'scope'},authority=lambda p:contextlib.nullcontext())
  class Fake:
   def __init__(self):self.homes=homes;self.scope=scope;self.sources=[types.SimpleNamespace(_friday_user_scope=retained)]
   def enter(self,i=0):return contextlib.nullcontext()
   def read(self,p,**kw):calls.append(('read',str(p)));return {'success':False,'error':'fake'}
   def write(self,p,*a,**kw):calls.append(('write',str(p)));return {'success':False,'error':'fake'}
   def enabled(self,v):calls.append(('enabled',v))
   def admit(self,i):return types.SimpleNamespace(_friday_user_scope=retained)
  mods={'tools.read_extract':types.SimpleNamespace(extract_scoped_document_bytes=lambda *a:(_ for _ in ()).throw(AssertionError('crypto'))),
   'hermes_cli':types.SimpleNamespace(friday_workspace_docx=types.SimpleNamespace(_create_bytes=lambda *a,**k:None),friday_workspace_odf_password=types.SimpleNamespace(_create_bytes=lambda *a,**k:None))}
  m=copy.deepcopy(self.m);m['fixtures']=m['fixtures'][4:]
  def fake_ref(ref,*a):
   if ref==m['credential']:return b'{"password":"TESTONLY-CORRECT-SECRET","wrong_password":"TESTONLY-WRONG-SECRET"}'
   self.assertIn(ref,[r['input'] for r in m['fixtures']]);return b'PURE-FAKE-FIXTURE'
  with patch.dict(sys.modules,mods),patch.object(h,'ref_read',fake_ref):result=h.qualify(Fake(),m,self.root)
  self.assertEqual([r['id'] for r in result['fixtures']],list(h.SUBSET))
  for kind,p in calls:
   if kind in ('read','write'):
    self.assertFalse(any('f06-'+str(n)+'.' in p or 'f06-'+str(n)+'-' in p for n in range(1,5)))
  self.assertTrue(any(kind=='enabled' for kind,p in calls))
  self.assertTrue((homes[0]/'workspace/f06-5.ods').exists());self.assertTrue((homes[0]/'workspace/f06-6.odp').exists());self.assertTrue((homes[0]/'workspace/f06-7.odt').exists())
  self.assertFalse(result['all_f06_accepted'] if 'all_f06_accepted' in result else False)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 report={'scope':'PURE_MOCK_ONLY_NO_REAL_NATIVE_NO_CREDENTIAL_OR_CIPHERTEXT_BODY_READ','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'actual_live_effects':0}
 (B/'test-results.json').write_text(json.dumps(report,indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
