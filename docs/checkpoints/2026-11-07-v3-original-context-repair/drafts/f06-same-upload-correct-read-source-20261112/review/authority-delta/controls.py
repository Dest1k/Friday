"""Focused opaque authority-ID compatibility controls; entirely synthetic."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
R=Path(__file__).resolve().parent
B=R.parent.parent
C=B/'revision3/candidate'
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
A=load(C/'f06_source.py');OLD=load(B/'revision2/candidate/f06_source.py');F=load(C/'first_ingress.py')
code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()}
ns=dict(A=A,F=F,C=C,code=code,json=json)
exec(compile((B/'revision2/synthetic_fixture.py').read_bytes(),'SYNTHETIC_FIRST_FIXTURE','exec'),ns)
fixture=ns['fixture']
base=A.BASE.read_bytes();footer=(C/'f06_footer.py.txt').read_bytes()
issuer=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py')
it=ast.parse(issuer.read_bytes());nodes=[n for n in it.body if isinstance(n,ast.FunctionDef) and n.name in ('derive_identity','validate_identity')]
assert len(nodes)==2
class FakeFile:
 def __init__(self,n,d):self.stem=n[:-5];self.d=d
 def read_text(self):return json.dumps(self.d)
 def __str__(self):return '/SYNTHETIC/'+self.stem+'.json'
class FakeOut:
 def __init__(self,docs):self.docs=docs
 def glob(self,p):return self.docs
 def __str__(self):return '/SYNTHETIC'
out=FakeOut([FakeFile('INDEPENDENT-AUTHORITY-R105.json',{'authority_id':'ordinary-f04-postfix-diagnostic-20261111-r105'})])
iscope=dict(Path=lambda v:v,json=json,time=types.SimpleNamespace(strftime=lambda *a:'20261112',localtime=lambda:None))
exec(compile(ast.Module(body=nodes,type_ignores=[]),'EXTRACTED_INERT_ISSUER_IDENTITY','exec'),iscope)
'SYNTHETIC'.encode('utf-16-le')
def audit(event,args):
 if event=='open' or event.startswith(('socket.','subprocess.','os.system','os.exec','os.spawn')):raise RuntimeError('PURE_CONTROL_EFFECT_REFUSED')
sys.addaudithook(audit)
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
def refuses(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,AttributeError,SystemExit):checks.append(n);return
 raise AssertionError(n)
c,s,first,read,data=fixture()
opaque='ordinary-f04-postfix-diagnostic-20261112-r106'
c['authority_id']=opaque
refuses('old_prefix_predicate_reproduces_opaque_label_refusal',lambda:OLD.contract_shape(c))
ok('new_nonempty_opaque_label_shape_supported',A.contract_shape(c))
for val in ('','UNBOUND',None,1,True,[],{}):
 x=copy.deepcopy(c);x['authority_id']=val
 refuses('invalid_id_'+repr(val),lambda x=x:A.contract_shape(x))
auth=dict(authority_id=opaque,scope=c['scope'],run_scenarios={c['run_id']:c['scenario_sha256']},ordered_predecessors={},same_canonical_local_run=False)
ok('opaque_id_still_requires_exact_admission_shape',A.admission(c,auth))
for n,change in (
 ('wrong_identity',lambda d:d.update(authority_id='ordinary-independent-OTHER')),
 ('wrong_scope',lambda d:d.update(scope='other')),
 ('wrong_scenario',lambda d:d.update(run_scenarios={c['run_id']:'f'*64})),
 ('wrong_run',lambda d:d.update(run_scenarios={'SYNTHETIC-other':c['scenario_sha256']})),
 ('borrowed_predecessor',lambda d:d.update(ordered_predecessors={'SYNTHETIC-old':{}})),
 ('memory_grant',lambda d:d.update(memory_case={})),
 ('old_canonical',lambda d:d.update(same_canonical_local_run=True))):
 d=copy.deepcopy(auth);change(d);refuses('admission_'+n,lambda d=d:A.admission(c,d))
newid,fileid,previd=iscope['derive_identity'](out)
ok('original_issuer_derives_actual_shaped_inherited_prefix',newid==opaque and fileid=='INDEPENDENT-AUTHORITY-R106.json' and previd=='ordinary-f04-postfix-diagnostic-20261111-r105')
ok('issuer_accepts_legitimate_opaque_chain',iscope['validate_identity'](newid,previd,out) is None)
for n,args in (
 ('self_supersedes',(previd,previd,out)),
 ('missing_predecessor',(newid,'missing',out)),
 ('empty_identity',('',previd,out)),
 ('empty_predecessor',(newid,'',out))):
 refuses('issuer_'+n,lambda args=args:iscope['validate_identity'](*args))
# Reconstruct/inspect, never execute, the original full consumer successor.
c['footer']=dict(path=str(C/'f06_footer.py.txt'),bytes=len(footer),sha256=A.digest(footer))
generated=A.successor(base,c,footer)
tree=ast.parse(generated)
runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission')
id_compares=[n for n in ast.walk(method) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Call) and isinstance(n.left.func,ast.Attribute) and n.left.func.attr=='get' and n.left.args and isinstance(n.left.args[0],ast.Constant) and n.left.args[0].value=='authority_id']
ok('fullv42_admission_still_compares_exact_opaque_ID',len(id_compares)==1 and isinstance(id_compares[0].ops[0],ast.NotEq) and ast.literal_eval(id_compares[0].comparators[0])==opaque)
ok('authority_private_ref_remains_exact_bound',ast.literal_eval(next(n.value for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ORDINARY_INDEPENDENT_AUTHORITY' for t in n.targets)))==c['authority'])
original=ast.parse(base);old_runner=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='Runner');old_method=next(n for n in old_runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission')
method_source=ast.get_source_segment(generated.decode(),method)
ok('full_original_method_authentication_guard_checks_remain',all(t in method_source for t in ("len(raw) != reference['bytes']","digest(raw) != reference['sha256']","document.get('operator') != 'Root'","document.get('accepted') is not True","document.get('run_scenarios') != self.ORDINARY_INDEPENDENT_SCENARIOS","digest(encoded(scenario)) != expected_sha")))
print(json.dumps({'status':'PASS_FOCUSED_OPAQUE_AUTHORITY_ID_SOURCE_ONLY','count':len(checks),'checks':checks,'actual_authority_reads':0,'network_H_runtime_native_model_Telegram_effects':0,'fullconsumer_executed':False},sort_keys=True))
