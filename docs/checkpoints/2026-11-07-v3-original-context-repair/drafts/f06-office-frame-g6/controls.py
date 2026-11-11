"""Finite standard-library-only context and redaction controls; no UNO/Office."""
import ast, contextlib, hashlib, io, json, os, runpy, sys, types
from pathlib import Path

sys.dont_write_bytecode=True
os.umask(0o077)
B=Path(__file__).resolve().parent
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-PRODUCER-CONTEXT-DIAGNOSIS-20261111')
E=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-PIPE-OBSERVER-FIX-20261111')
rows=[]
def test(name,fn):
 fn();rows.append(dict(name=name,status='PASS'))
def equal(a,b):assert a==b
def check_pins_and_compile():
 pins=json.loads((F/'SOURCE-PINS.json').read_text());changed=[]
 for row in pins['files']:
  raw=(B/row['name']).read_bytes()
  if row['name'].endswith('.py'):compile(raw,str(B/row['name']),'exec')
  if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:changed.append(row['name'])
 assert sorted(changed)==['embedded_entry.py','f06_contract.py','office_fixture_driver.py','root_frame.py']
 original=ast.parse((F/'office_fixture_driver.py').read_text());candidate=ast.parse((B/'office_fixture_driver.py').read_text())
 old=next(n for n in ast.walk(original) if isinstance(n,ast.FunctionDef) and n.name=='profile');new=next(n for n in ast.walk(candidate) if isinstance(n,ast.FunctionDef) and n.name=='profile')
 assert len(new.body)==3 and ast.dump(ast.Module(body=old.body[1:],type_ignores=[]))==ast.dump(ast.Module(body=new.body[1:],type_ignores=[]))
 old.body[0]=new.body[0]
 assert ast.dump(original)==ast.dump(candidate)
 expected=ast.parse("uno.invoke(config,'setPropertyValue',('DefaultVersion',uno.Any('short',version)))").body[0]
 assert ast.dump(new.body[0])==ast.dump(expected)
test('all11_compile_F4_delta_only_typed_property_call_AST_changed_in_producer',check_pins_and_compile)

original=ast.parse((E/'embedded_entry.py').read_text())
candidate=ast.parse((B/'embedded_entry.py').read_text())
original_args=next(n for n in original.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='argv' for t in n.targets))
candidate_args=next(n for n in candidate.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='argv' for t in n.targets))
test('exact_private_argv_AST_unchanged',lambda:equal(ast.dump(original_args),ast.dump(candidate_args)))
start=next(i for i,n in enumerate(candidate.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='producer_phase' for t in n.targets))
suffix=compile(ast.Module(body=candidate.body[start:],type_ignores=[]),'/recipe/embedded_entry.py','exec')
main=sys.modules['__main__'];token=object();sentinel='f06_context_control_runtime'
assert not hasattr(main,sentinel)
setattr(main,sentinel,token)
case=B/'controls-case';case.mkdir(mode=0o700,exist_ok=True)
program=case/'canary.py'
program.write_text('import sys\nif not hasattr(sys.modules["__main__"],"f06_context_control_runtime"):raise SystemError("synthetic_canary_private_message")\ndef main():\n assert hasattr(sys.modules["__main__"],"f06_context_control_runtime")\n return 0\n')
def original_loses_runtime():
 try:runpy.run_path(str(program),run_name='__main__')
 except SystemError:pass
 else:raise AssertionError('negative control failed')
 assert sys.modules['__main__'] is main and getattr(main,sentinel) is token
test('negative_original_runpy_main_hides_existing_runtime',original_loses_runtime)

def run_suffix(loader,save_override=None):
 output=io.StringIO();saved=[]
 def save(path,obj):saved.append((path,obj))
 ns=dict(runpy=types.SimpleNamespace(run_path=loader),save=save_override or save,attempt=case,json=json)
 with contextlib.redirect_stdout(output):
  try:exec(suffix,ns)
  except SystemExit as exc:exitcode=exc.code
  else:raise AssertionError('no SystemExit')
 return exitcode,output.getvalue(),saved
def actual_run_path_adapter(path,run_name):
 assert path=='/recipe/office_fixture_driver.py' and run_name=='f06_producer_library'
 return runpy.run_path(str(program),run_name=run_name)
def candidate_preserves_runtime():
 status,output,saved=run_suffix(actual_run_path_adapter)
 assert status==0 and not output and not saved
 assert sys.modules['__main__'] is main and getattr(main,sentinel) is token
test('candidate_actual_runpy_named_then_main_preserves_runtime',candidate_preserves_runtime)
for value in (0,1):
 def exit_contract(value=value):
  status,output,saved=run_suffix(lambda *a,**k:dict(main=lambda:value))
  assert status==value and not output and not saved
 test('producer_exit_contract_'+str(value),exit_contract)

def safe_error_capture():
 payload='synthetic_canary_private_message'
 library={}
 exec(compile('def main():\n raise SystemError("'+payload+'")\n','/recipe/office_fixture_driver.py','exec'),library)
 status,output,saved=run_suffix(lambda *a,**k:library)
 error=json.loads(output)
 assert status==2 and len(saved)==1 and saved[0][0]==case/'PRODUCER-ERROR-LOCATION.json'
 assert saved[0][1]==error and error['exception_class']=='SystemError' and error['phase']=='producer_main'
 assert error['source_frames'][-1]==dict(file='/recipe/office_fixture_driver.py',line=2,function='main')
 assert error['exception_messages_or_locals_saved'] is False and payload not in json.dumps(error)
 assert set(error)=={'status','exception_class','phase','source_frames','traceback_truncated','exception_messages_or_locals_saved','location_file_save_failed'}
test('safe_exact_source_frames_without_exceptionmessage_locals_or_args',safe_error_capture)
def library_error_capture():
 def loader(*args,**kwargs):raise ValueError('synthetic_private_loader_payload')
 status,output,saved=run_suffix(loader)
 error=json.loads(output)
 assert status==2 and error['phase']=='producer_library_load' and error['exception_class']=='ValueError'
 assert 'synthetic_private_loader_payload' not in output
test('library_phase_capture_without_loader_payload',library_error_capture)
def reporter_failure_is_safe():
 def loader(*args,**kwargs):raise SystemError('synthetic_original_private_message')
 def failure(*args,**kwargs):raise OSError('synthetic_observer_private_message')
 status,output,saved=run_suffix(loader,save_override=failure)
 error=json.loads(output)
 assert status==2 and error['location_file_save_failed'] is True
 assert 'synthetic_original_private_message' not in output and 'synthetic_observer_private_message' not in output
test('observer_write_failure_preserves_safe_error_exit2',reporter_failure_is_safe)


def class_capture(name,expected):
 error_type=type(name,(Exception,),{})
 def loader(*args,**kwargs):raise error_type('synthetic_private_message_never_save')
 status,output,saved=run_suffix(loader);error=json.loads(output)
 assert status==2 and error['exception_class']==expected and saved[0][1]==error
 assert 'synthetic_private_message_never_save' not in output
for name,expected in [('com.sun.star.uno.RuntimeException','com.sun.star.uno.RuntimeException'),('X'*128,'X'*128),('a.'+'X'*126,'a.'+'X'*126),('X'*129,'REDACTED'),('a.'+'X'*127,'REDACTED'),('a..B','REDACTED'),('.A','REDACTED'),('A.','REDACTED'),('A secret payload','REDACTED'),('A/B','REDACTED'),('', 'REDACTED')]:
 test('qualified_class_bounds_'+str(len(rows)),lambda name=name,expected=expected:class_capture(name,expected))
def stdout_failure_is_safe():
 def loader(*args,**kwargs):raise SystemError('synthetic_context_secret')
 def stdout(*args,**kwargs):raise OSError('synthetic_stdout_secret')
 saved=[];ns=dict(runpy=types.SimpleNamespace(run_path=loader),save=lambda p,v:saved.append(v),attempt=case,json=json,print=stdout)
 try:exec(suffix,ns)
 except SystemExit as e:assert e.code==2
 else:raise AssertionError('missing safe exit')
 assert len(saved)==1 and saved[0]['exception_class']=='SystemError' and 'synthetic_context_secret' not in json.dumps(saved)
test('observer_stdout_failure_still_safe_exit2_without_context_leak',stdout_failure_is_safe)

def typed_setter_call_and_readbacks():
 tree=ast.parse((B/'office_fixture_driver.py').read_text());profile=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='profile')
 log=[]
 class Config:
  value=3
  mismatch=False
  def setPropertyValue(self,*args):raise AssertionError('forbidden direct typed call')
  def commitChanges(self):log.append(('commit',))
  def getPropertyValue(self,name):
   assert name=='DefaultVersion';log.append(('readback',));return 99 if self.mismatch else self.value
 config=Config()
 class Uno:
  def Any(self,kind,value):assert kind=='short';return ('TYPED_SHORT',value)
  def invoke(self,obj,method,args):
   assert obj is config and method=='setPropertyValue' and args[0]=='DefaultVersion' and args[1][0]=='TYPED_SHORT'
   log.append(('invoke',args[1][1]));config.value=args[1][1]
 ns=dict(uno=Uno(),config=config);exec(compile(ast.Module(body=[profile],type_ignores=[]),'/recipe/office_fixture_driver.py','exec'),ns)
 for version in (10,3):
  log.clear();ns['profile'](version);assert log==[('invoke',version),('commit',),('readback',)] and config.value==version
 config.mismatch=True
 try:ns['profile'](10)
 except ValueError as error:assert str(error)=='odf_profile_readback'
 else:raise AssertionError('readback drift accepted')
test('actual_profile_AST_fake_uno_typed10_3_commit_readback_and_wrong_readback_reject',typed_setter_call_and_readbacks)
# Audit guard prevents accidentally crossing source-only assignment boundaries.
import resource
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648))
denied=[]
def audit(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.__new__'):
  denied.append(event);raise RuntimeError('SOURCE_ONLY_EFFECT_DENIED')
 if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]);base=Path(p).name.lower()
  if 'credential' in base or p.startswith(('/home/jericho/.hermes/','/home/jericho/.config/','/home/jericho/.local/share/','/home/jericho/jericho/Friday_rework/.runtime/','/home/jericho/.jericho/state/')):
   denied.append(event);raise RuntimeError('SOURCE_ONLY_STATE_OR_SECRET_DENIED')
sys.addaudithook(audit)
from unittest.mock import patch
sys.path.insert(0,str(B))
import f06_contract as c,root_frame as f
sha=hashlib.sha256((B/'SOURCE-PINS.json').read_bytes()).hexdigest()
def reject(call,code=None):
 try:call()
 except ValueError as error:
  if code is not None:assert str(error)==code,(str(error),code)
 else:raise AssertionError('unexpected acceptance')
def unchanged_guards():
 for name in ('run_once.py','inside_once.py','source_controls.py','source_check.py','office_fixture_driver.original.py','REFERENCES.json','REQUEST.json'):
  assert (B/name).read_bytes()==(F/name).read_bytes()
 old=ast.parse((F/'root_frame.py').read_text());new=ast.parse((B/'root_frame.py').read_text())
 oldf={n.name:ast.dump(n) for n in old.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};newf={n.name:ast.dump(n) for n in new.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 assert all(newf[k]==v for k,v in oldf.items() if k!='missing_document_stage')
 oldc=ast.parse((F/'f06_contract.py').read_text());newc=ast.parse((B/'f06_contract.py').read_text())
 oldf={n.name:ast.dump(n) for n in oldc.body if isinstance(n,ast.FunctionDef)};newf={n.name:ast.dump(n) for n in newc.body if isinstance(n,ast.FunctionDef)}
 assert all(newf[k]==v for k,v in oldf.items() if k not in ('operation','reconciled_inputs'))
 for name in ('LIMITS','PREFLIGHT_LIMITS','FORMATS','PROFILES','NAMES'):
  select=lambda t:next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
  assert ast.dump(select(oldc))==ast.dump(select(newc))
 testproducer=runpy.run_path(str(B/'office_fixture_driver.py'),run_name='f06_control_library')
 assert len(testproducer['JOBS'])==7 and testproducer['PROFILES']==('compatible1.3_or_Agile',)*6+('current_default_latest_odt_negative',)
test('all_runtime_bootstrap_ownership_resource_stop_guards_unchanged_AST_seven_profiles',unchanged_guards)
for key in ('generate-g1','generate-g2','generate-g3','generate-g4','generate-g5','generate-g7','generate-retry'):
 test('refuses_consumed_or_generic_generation_'+key,lambda key=key:reject(lambda:c.operation(key,'generate'),'OPERATION_KEY'))
test('exact_g6_and_unchanged300wall180CPU7stores21probes',lambda:equal((c.operation('generate-g6','generate'),c.LIMITS['max_stores'],c.LIMITS['max_password_probes'],c.LIMITS['whole_wall_seconds'],c.LIMITS['aggregate_CPU_seconds']),(B/'operations/generate-g6',7,21,300,180)))
authority_template=json.loads((B/'MISSING-DOCUMENT-STAGE-AUTHORITY.TEMPLATE.json').read_text())
diag_template=json.loads((B/'TYPED-SETTER-DIAGNOSTIC-ACCEPTANCE.TEMPLATE.json').read_text())
diag_accepted={**diag_template,'state':'ROOT_ACCEPTED_DOCUMENT_FREE_TYPED_SETTER_DIAGNOSTIC'}
def memory_pin(name,obj):
 raw=json.dumps(obj).encode();return raw,dict(path=str(B/name),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),identity=['SOURCE_ONLY_MEMORY'])
diagraw,diagpin=memory_pin('TYPED-SETTER-DIAGNOSTIC-ACCEPTANCE.json',diag_accepted)
accepted={**authority_template,'state':'ROOT_ACCEPTED_EXACT_TYPED_SETTER_FIX_MISSING_DOCUMENT_STAGE_ONLY','typed_setter_diagnostic_acceptance':diagpin}
root=json.loads((F/'operations/generate-g5/ROOT-RESULT.json').read_text());parent=json.loads((F/'operations/generate-g5/PARENT-BINDING.json').read_text())
a=dict(mode='generate',operation_key='generate-g6',source_pins_sha256=sha,boot_id=root['boot_id'],uid=parent['root_uid'])
real_private=c.private
closure_path=F/f.MISSING_STAGE_CLOSURE_RELATIVE
def authority(obj=accepted,ad=a,mutate=None,diag=diag_accepted):
 raw,pin=memory_pin('MISSING-DOCUMENT-STAGE-AUTHORITY.json',obj)
 def private(path,root):
  if str(path)==pin['path']:return raw,pin
  if str(path)==diagpin['path']:return json.dumps(diag).encode(),diagpin
  data,p=real_private(path,root)
  if mutate and str(path)==str(mutate[0]):
   value=json.loads(data);mutate[1](value);data=json.dumps(value).encode()
  return data,p
 with patch.object(c,'private',side_effect=private):return f.missing_document_stage({**ad,'missing_stage_authority':pin},{'missing_stage_authority':pin})
test('actual_pure_consumer_g5closure_emptydirectory_and_fixed10_3_diagnostic_receipts',authority)
test('UNBOUND_authority_rejected',lambda:reject(lambda:authority(authority_template),'MISSING_STAGE_AUTHORITY'))
test('missing_diagnostic_acceptance_rejected',lambda:reject(lambda:authority({**accepted,'typed_setter_diagnostic_acceptance':None}),'TYPED_SETTER_DIAGNOSTIC_REQUIRED'))
test('UNBOUND_diagnostic_acceptance_rejected',lambda:reject(lambda:authority(diag=diag_template),'TYPED_SETTER_DIAGNOSTIC_ACCEPTANCE'))
for key,value in dict(new_operation_key='generate-g7',prior_operation_key='generate-g4',changed_source_files=['office_fixture_driver.py'],prior_source_pins_sha256='0'*64,original_operation_replay=True,original_clocks_reset=True,preflight_reexecuted=True,remaining_document_count=6,remaining_stores=6,remaining_password_probes=18,g5_producer_entered=False,g5_credential_read_status='NOT_READ',g5_observed_exception_class='com.sun.star.uno.RuntimeException').items():
 test('authority_refuses_wrong_'+key,lambda key=key,value=value:reject(lambda:authority({**accepted,key:value})))
for key,value,code in [('actual_root_parent_absent',False,'MISSING_STAGE_KNOWN_CLOSURE'),('encrypted_files',1,'MISSING_STAGE_ZERO_DOCUMENT_CUSTODY'),('document_loads',1,'MISSING_STAGE_ZERO_DOCUMENT_CUSTODY'),('observed_exception_class','com.sun.star.uno.RuntimeException','MISSING_STAGE_ZERO_DOCUMENT_CUSTODY')]:
 test('g5_semantics_refuse_'+key,lambda key=key,value=value,code=code:reject(lambda:authority(mutate=(closure_path,lambda o:o.update({key:value}))),code))
for obj in ({**accepted['prior_empty_directory'],'identity':[0]*9},{**accepted['prior_empty_directory'],'entries':['file.odt']},{**accepted['prior_empty_directory'],'path':str(case)}):
 test('actual_empty_directory_pin_reject_'+str(len(rows)),lambda obj=obj:reject(lambda:authority({**accepted,'prior_empty_directory':obj})))
def own_empty_directory_negative():
 import shutil
 fixture=case/'empty-directory-control';path=fixture/'operations/generate-g5/work/encrypted-inputs';path.mkdir(mode=0o700,parents=True)
 for x in [path,*list(path.parents)[:3]]:x.chmod(0o700)
 row=dict(path=str(path),identity=c.identity(path.lstat()),entries=[])
 try:
  with patch.object(f,'MISSING_STAGE_ROOT',fixture):
   f.empty_prior_directory(row)
   p=path/'unexpected.odt';p.write_bytes(b'x');p.chmod(0o600)
   reject(lambda:f.empty_prior_directory(row),'MISSING_STAGE_EMPTY_DIRECTORY_CHANGED')
   p.unlink();row['identity']=c.identity(path.lstat());f.empty_prior_directory(row)
   link=path/'link';link.symlink_to(program)
   reject(lambda:f.empty_prior_directory(row),'MISSING_STAGE_EMPTY_DIRECTORY_CHANGED')
 finally:shutil.rmtree(fixture)
test('own_emptydirectory_control_rejects_newfile_and_symlink_without_touching_g5',own_empty_directory_negative)
D=f.TYPED_SETTER_DIAGNOSTIC_ROOT
for field,value,code in [('all_pass',False,'TYPED_SETTER_DIAGNOSTIC_ACTUAL_READBACKS'),('document_loads',1,'TYPED_SETTER_DIAGNOSTIC_NO_DOCUMENTS_OR_SECRETS'),('credential_mounts',1,'TYPED_SETTER_DIAGNOSTIC_NO_DOCUMENTS_OR_SECRETS')]:
 test('diagnostic_semantics_refuse_'+field,lambda field=field,value=value,code=code:reject(lambda:authority(mutate=(D/'work/TYPED-SETTER-DIAGNOSTIC.json',lambda o:o.update({field:value}))),code))
test('diagnostic_wrong_invoke_readback_rejected',lambda:reject(lambda:authority(mutate=(D/'work/TYPED-SETTER-DIAGNOSTIC.json',lambda o:o['rows'][0].update(invoke_readback=3))),'TYPED_SETTER_DIAGNOSTIC_ACTUAL_READBACKS'))
for field in ('child_reaped','owned_children_closed','owned_pipes_closed','slot_reacquired_and_released'):
 test('diagnostic_closure_refuse_'+field,lambda field=field:reject(lambda:authority(mutate=(D/'ROOT-RESULT.json',lambda o:o.update({field:False}))),'TYPED_SETTER_DIAGNOSTIC_KNOWN_CLOSED'))
reuse=json.loads((B/'RETAINED-PREFLIGHT-ACCEPTANCE.TEMPLATE.json').read_text())
def retained():
 obj={**reuse,'state':'ROOT_ACCEPTED_RETAINED_TYPED_PREFLIGHT_ONLY'};raw,pin=memory_pin('RETAINED-PREFLIGHT-ACCEPTANCE.json',obj)
 ad={**a,'preflight_reconciliation':pin,'preflight_result':obj['evidence']['root_result'],'preflight_typed_proof':obj['evidence']['typed_proof']}
 with patch.object(c,'private',side_effect=lambda path,root:(raw,pin) if str(path)==pin['path'] else real_private(path,root)):return f.retained_preflight(ad,{'retained_preflight_reconciliation':pin})
test('actual_pure_original9_preflight_consumer_cumulative_G5_mapping',retained)
assert denied==[],denied
delattr(main,sentinel);program.unlink();case.rmdir()
result=dict(state='PASS_AFFECTED_SOURCE_ONLY_NOT_RUNTIME',source_pins_sha256=sha,count=len(rows),controls=rows,actual_Office_starts=0,actual_UNO_imports=0,actual_unit_or_namespace_starts=0,credential_content_reads=0,model_or_network_calls=0,old_closed_effects_or_source_gates_not_replayed=True,actual_Root_diagnostic_reused_not_reexecuted=True)
(B/'CONTROLS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(state=result['state'],count=len(rows))))
