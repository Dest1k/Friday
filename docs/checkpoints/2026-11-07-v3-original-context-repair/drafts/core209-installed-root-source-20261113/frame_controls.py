"""Finite R2 metadata/caller-pin/relocation controls; no current H or product effects."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys,types,time
B=Path(__file__).parent;O=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-ROOT-FRAME-PREP-20261113-R1');start=time.monotonic();rows=[]
def check(n,v):
 assert v,n;rows.append(dict(name=n,passed=True))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
interfaces=['boundary_contract.py','native_scope.py','root209_metadata.py','start_core209_once.py','run_native209_once.py','resume_native209_services.py','core209-first-actual-root.py','root209_real_preflight.py','prepare_source.py','admission-retained/observe-current-retained-units.py']
for n in interfaces:compile((B/n).read_bytes(),str(B/n),'exec')
check('R2_operational_interfaces_compile',True)
script='''import sys,types,pathlib,os,json,subprocess,socket,sqlite3,importlib.util,datetime,zoneinfo,fcntl,stat,hashlib,signal,time,struct,math,resource,errno
B=pathlib.Path(sys.argv[1])
def audit(event,args):
 if event in {'subprocess.Popen','socket.connect','socket.bind','os.mkdir','os.rename','os.remove','os.putenv','os.unsetenv','os.chdir','os.chmod','os.kill','os.killpg'}:raise RuntimeError('import_effect')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes))and str(p).startswith('/home/jericho/jericho/Friday_rework/.runtime/'):raise RuntimeError('import_H_read')
  if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('import_write')
sys.addaudithook(audit)
for n in sys.argv[2:]:
 p=B/n;m=types.ModuleType('R2_'+n.replace('/','_').replace('.','_'));m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
'''
r=subprocess.run([sys.executable,'-I','-B','-c',script,str(B),*interfaces],capture_output=True,timeout=10);check('R2_import_inert_no_H_IO_or_effects',r.returncode==0)
for n in ['root209_real_preflight.py','start_core209_once.py','run_native209_once.py','core209-first-actual-root.py','resume_native209_services.py','root209_metadata.py','prepare_source.py']:
 r=subprocess.run([sys.executable,'-I','-B',str(B/n)],capture_output=True,timeout=5);check('R2_noarg_refused_'+n,r.returncode!=0 and any(k in r.stderr.lower()for k in [b'explicit',b'required']))
for n in ['resume_native209_services.py','boundary_contract.py','native_scope.py','start_core209_once.py','core209-first-actual-root.py','root209_real_preflight.py','prepare_source.py','publication/build-layer-publication-request.py','publication/friday_v3_layer_publication.py','admission-retained/observe-current-retained-units.py']:
 check('R1_runtime_source_reused_'+n,(B/n).read_text()==(O/n).read_text().replace(str(O),str(B)))
actor=(B/'run_native209_once.py').read_text();oldactor=(O/'run_native209_once.py').read_text().replace(str(O),str(B));check('actor_delta_only_metadata_source_pin',actor==oldactor.replace(sha(O/'root209_metadata.py'),sha(B/'root209_metadata.py')))
def defs(p):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before=defs(O/'root209_metadata.py');after=defs(B/'root209_metadata.py')
check('readref_strict_AST_unchanged',after['readref']==before['readref'])
for n in before:
 if n!='validate_join':check('metadata_existing_definition_unchanged_'+n,after[n]==before[n])
s=(B/'root209_metadata.py').read_text();a=ast.parse(s);v=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name=='validate_join');count=0
for n in ast.walk(v):
 if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='read_sized_source_ref':n.func.id='readref';count+=1
check('validate_join_exact_two_gate_ref_adapter_calls_only',count==2 and ast.dump(v,include_attributes=False)==before['validate_join'])
for p in B.glob('*TEMPLATE.json'):
 expected=json.loads(json.dumps(json.loads((O/p.name).read_bytes())).replace(str(O),str(B)));actual=json.loads(p.read_bytes())
 if p.name in {'ROOT-209-FRESH-ADMISSION-TEMPLATE.json','ROOT-209-RUNTIME-AUTHORITY-TEMPLATE.json'}:
  for k in ('actor','recovery','boundary','caller'):
   if k in expected:expected[k]=actual[k]
 check('template_relocation_no_new_policy_'+p.name,expected==actual)
check('consumed_R1_manifest_preserved',sha(O/'SOURCE-PINS.json')=='cc66b9cb42ec75f5a8af6e1133842976cce1949b030905b1b70590f6e873f90b')
check('R1_no_retry_and_root_decisions_not_copied',all(not(B/n).exists()for n in ['FUTURE-EXECUTION','ROOT-FRESH-REQUEST.json','ROOT-209-SOURCE-ACCEPTANCE.json','ROOT-209-RUNTIME-AUTHORITY.json','ROOT-209-FRESH-ADMISSION.json','ROOT-209-BOUND-INPUTS.json','ROOT-NATIVE209-LIVE-OPERATION.json']))
v=dict(state='PASS_R2_METADATA_CALLER_SOURCE_ONLY',count=len(rows),rows=rows,elapsed_seconds=time.monotonic()-start,current_H_reads_or_effects=0,consumed_R1_untouched=True,existing_R1_guard_and_runtime_reviews_reused=True);p=B/'FRAME-CONTROLS.json';p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o600);print(json.dumps(dict(state=v['state'],count=v['count'])))
