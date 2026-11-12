"""Relevant refusal seams only; all clients, inputs, bank and hooks synthetic."""
import ast,copy,datetime,json,os,pathlib,stat,sys,types
B=pathlib.Path(__file__).resolve().parent;C=B/'candidate';checks=[]
def ok(n,v):assert v,n;checks.append(dict(name=n,pass_=True))
def refused(fn,code):
 try:fn()
 except ValueError as e:assert e.args==(code,);return
 raise AssertionError('EXPECTED_REFUSAL')
# Load only source control definitions; their __main__ test runner never runs.
ns={'__name__':'delta_controls_library','__file__':str(B/'inside_controls.py')}
exec(compile((B/'inside_controls.py').read_text(),'inside_controls.py','exec'),ns)
cli=ns['client'];testcls=ns['NewSeamControls']
for label in ('probe_restored_false','compat_restore_refusal'):
 case=testcls('test_same_connected_desktop_one_load_cleanup_restore');case.setUp();restore=cli.restore_request_args_compat
 try:
  if label=='probe_restored_false':
   original_adapter=cli.observe_one_readonly
   def broken_probe(**kw):
    value=original_adapter(**kw)
    for event in value['interaction_events']:event['conversion_probe']['restored']=False
    return value
   cli.observe_one_readonly=broken_probe
   reason='HOOK_CAS_OR_RESTORATION_DRIFT'
  else:
   def refuse_restore(token):raise ValueError('SYNTHETIC_CAS_FAILURE')
   cli.restore_request_args_compat=refuse_restore;reason='COMPAT_RESTORATION_DRIFT'
  code,value=case.run_client();ok(label+'_terminal_stop',code==1 and value['state']=='TERMINAL_STOP' and reason in value['terminal_reasons'])
  ok(label+'_one_business_load_one_getrequest',case.loads==1 and len(case.requests)==1 and case.requests[0].calls==1)
 finally:cli.restore_request_args_compat=restore;case.tearDown()
# Existing actual bank consumer rejects manifest drift before another source read.
ns2={'__file__':str(C/'f06_contract.py'),'__name__':'contract_delta'};exec(compile(ast.parse((C/'f06_contract.py').read_text()),'f06_contract.py','exec'),ns2)
g=ns2['bank_snapshot'].__globals__;saved=g['stable'];seen=[]
def altered_manifest(path,**kw):seen.append(path);return b'{}',{'sha256':'0'*64}
g['stable']=altered_manifest
try:refused(ns2['bank_snapshot'],'BANK_MANIFEST');ok('altered_bank_manifest_refused_before_second_read',seen==[ns2['MANIFEST']])
finally:g['stable']=saved
# The Root consumer compares fresh bank proof with current bank. No filesystem,
# credential, real clock, actor or actual authority is observed here.
node=next(n for n in ast.parse((C/'root_frame.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='validate_fields')
a=dict(mode=ns2['MODE'],operation_key=ns2['OPERATION_KEY'],credential_source={},schema='friday.f06.one-template-post-args-admission.v1',state='ROOT_FRESH_ONCE_ADMITTED',assignment=ns2['ASSIGNMENT'],uid=123,boot_id='syntheticboot',nonce='1'*32,admitted_at_moscow='synthetic',original_operation_start_monotonic=10,source_pins_sha256='a'*64,limits=ns2['LIMITS'],actual_two_cpu_ids=[0,1],fresh_boundary={},slot_identity=[1])
fresh=dict(state='ROOT_FRESH_POST_ARGS_COMPAT_ONE_TEMPLATE_KERNEL_CUSTODY',boot_id=a['boot_id'],uid=123,nonce=a['nonce'],slot_identity=[1],original_operation_start_monotonic=10,observed_at_moscow='synthetic',bank={'altered':True})
c=types.SimpleNamespace(need=ns2['need'],operation=lambda *x:None,limits=lambda m:ns2['LIMITS'],credential_metadata=lambda r:({},[]),PRE_STAGE_CREDENTIAL_PATHS=set(),ASSIGNMENT=ns2['ASSIGNMENT'],within=lambda *x:None,recipe_check=lambda:({'sha256':'a'*64},None),exact_json=ns2['exact_json'],diagnostic_acceptance=lambda a:None,bank_snapshot=lambda:{'altered':False})
c.credential_metadata=lambda r:({'path':'/synthetic/credential-not-read'},[])
class FakePath:
 def __init__(self,*parts):self.parts=parts
 def read_text(self):assert self.parts==('/proc/sys/kernel/random/boot_id',);return 'syntheticboot'
n=dict(c=c,need=c.need,os=types.SimpleNamespace(getuid=lambda:123,sched_getaffinity=lambda n:{0,1}),Path=FakePath,re=__import__('re'),time=types.SimpleNamespace(monotonic=lambda:11),fresh_time=lambda *x:None,proof=lambda r:(fresh,{}))
exec(compile(ast.Module(body=[node],type_ignores=[]),'root_frame.py','exec'),n)
refused(lambda:n['validate_fields'](a),'FRESH_BANK_METADATA_CAS_CRITICAL4');ok('Root_current_bank_mismatch_refused',True)
# Immutable old frame safety bodies are reused, compared at this snapshot.
T=pathlib.Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112/candidate')
def function_ast(p,name):return ast.dump(next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)and n.name==name),include_attributes=False)
for name in ('bank_snapshot','stable','save','private','credential_metadata','output_inputs','retention_snapshot'):
 ok('unchanged_actual_safety_function_'+name,function_ast(C/'f06_contract.py',name)==function_ast(T/'f06_contract.py',name))
for name in ('final_dependency_audit','acquire_slot','cpu_total','unit_closed'):
 # Source names may differ by old architecture; only names present are compared.
 nodes={n.name for n in ast.parse((T/'root_frame.py').read_text()).body if isinstance(n,ast.FunctionDef)}
 if name in nodes:ok('unchanged_Root_safety_function_'+name,function_ast(C/'root_frame.py',name)==function_ast(T/'root_frame.py',name))
print(json.dumps(dict(schema='post-args.safety-delta-controls.v1',checks=checks,count=len(checks),all_pass=True,scope='SYNTHETIC_SOURCE_ONLY_NO_OFFICE',no_actual_inputs_or_proofs=True),sort_keys=True))
