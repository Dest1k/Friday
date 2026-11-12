import ast,copy,hashlib,json,os,shutil,subprocess,tempfile,types
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'candidate';rows=[]
def check(n,v):
 if not v:raise AssertionError(n)
 rows.append(n)
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
freeze=json.loads((C/'SOURCE-FREEZE.json').read_bytes());leaves=set(freeze['files']);check('exact5freeze',leaves=={'f06_source.py','f06_footer.py.txt','first_ingress.py','current_root.py','root_bind_dispatch_once.py'})
for name,pin in freeze['files'].items():check('frozen_'+name,ref(C/name)==dict(path=str(C/name),**pin))
patch=(B/'SOURCE.patch').read_bytes();stand=B/'own-patch-stand';stand.mkdir(mode=0o700)
try:
 for name in leaves:(stand/name).write_bytes((B/'before'/name).read_bytes())
 def git(*args):return subprocess.run(['git','--no-optional-locks','apply',*args,'-'],input=patch,cwd=stand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
 check('patch_forward_check',git('--check').returncode==0);check('patch_forward_real',git().returncode==0)
 check('forward_all5_byteexact',all((stand/n).read_bytes()==(C/n).read_bytes() for n in leaves))
 check('patch_reverse_check',git('--reverse','--check').returncode==0);check('patch_reverse_real',git('--reverse').returncode==0)
 check('reverse_all5_byteexact',all((stand/n).read_bytes()==(B/'before'/n).read_bytes() for n in leaves))
 p=stand/'f06_source.py';p.write_bytes(p.read_bytes().replace(b"PHASE='DOCX-CORRECT-READ-SAME-UPLOAD'",b"PHASE='SYNTHETIC_DRIFT'",1));check('touched_hunk_drift_rejected',git('--check').returncode!=0)
finally:shutil.rmtree(stand)
check('own_stand_removed',not stand.exists())
# Static source of real unchanged issuer: no issue/main/derive call. This tests its
# actual pure scope predicate rather than borrowing fake issuer acceptance.
p=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py');raw=p.read_bytes();check('issuer_source_exact_pinned',hashlib.sha256(raw).hexdigest()=='ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518')
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='validate_scope');env={};exec(compile(ast.Module(body=[node],type_ignores=[]),'SYNTHETIC_PURE_ISSUER_PREDICATE','exec'),env)
m=types.ModuleType('inert_adapter');m.__file__=str(C/'f06_source.py');exec(compile((C/'f06_source.py').read_bytes(),m.__file__,'exec'),m.__dict__)
env['validate_scope'](m.scope(),{'SYNTHETIC_WRONGEDIT':'1'*64});check('actual_unchanged_issuer_scope_support',True)
for bad in ('product acceptance','B00 acceptance'):
 try:env['validate_scope'](bad,{'SYNTHETIC':'1'*64})
 except SystemExit:check('actual_scope_rejects_'+bad,True)
 else:raise AssertionError(bad)
# Wholecaller's original IO/sourceclock/wait/stop helpers unchanged from Task29.
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)}
x=funcs(B/'before/root_bind_dispatch_once.py');y=funcs(C/'root_bind_dispatch_once.py')
for n in ('read','readref','ref','load','new','clock_remaining','owned_remaining','wait_owned','canonical_path','identity','unique'):
 check('unchanged_caller_'+n,x[n]==y[n])
# No copiedTrue/actualruntime objects in UNBOUND handoff metadata.
templates={p.name:json.loads(p.read_bytes()) for p in (B/'templates').glob('*.json')}
check('contract_operational_unbound',all(templates['CONTRACT.UNBOUND.json'][k] is None for k in ('scenario_ref','authority','root_current_proof','correct_read','change_spec','source_reference','first_ingress')))
check('driver_unbound_no_work_slot_clock',templates['ROOT-BINDING-INPUTS.UNBOUND.json']['status']=='UNBOUND_NOT_GRANTED' and templates['ROOT-BINDING-INPUTS.UNBOUND.json']['workdir'] is None and templates['ROOT-BINDING-INPUTS.UNBOUND.json']['slot_identity'] is None)
check('change_no_invented_old_new',templates['PRIVATE-CHANGE.UNBOUND.json']['old'] is None and templates['PRIVATE-CHANGE.UNBOUND.json']['new'] is None)
check('correct_dependency_no_invented_ACK',templates['CORRECT-READ.UNBOUND.json']['ack'] is None and templates['CORRECT-READ.UNBOUND.json']['assessment'] is None)
check('clock_no_fabricated_timestamp',all(v is None for k,v in templates['ROOT-CLOCK.UNBOUND.json'].items() if k!='schema'))
check('postcondition_ungraded',templates['POST-OP-ASSESSMENT.UNBOUND.json']['acceptance']=='NOT_ESTABLISHED')
print(json.dumps({'schema':'frw.Sol.Task30.patch-handoff-controls.v1','count':len(rows),'checks':rows,'source_freeze':ref(C/'SOURCE-FREEZE.json'),'patch':ref(B/'SOURCE.patch'),'actual_issuer_executed':False,'generated_consumer_executed':False,'runtime_NOT_RUN':True,'no_secret_document_or_H_STATE_reads':True,'own_patch_stand_removed':True},sort_keys=True))
