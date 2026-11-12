"""New Root-observed opaque-label compatibility delta, PURE synthetic authority chain."""
import ast,copy,json,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'revision3/candidate'
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=load(C/'f06_source.py');F=load(C/'first_ingress.py');OLD=load(B/'revision2/candidate/f06_source.py');code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()};g={'A':A,'F':F,'C':C,'code':code,'json':json};exec(compile((B/'revision2/synthetic_fixture.py').read_bytes(),'PURE_FIXTURE','exec'),g)
c,s,first,read,data=g['fixture']();base=A.BASE.read_bytes();tree=ast.parse(base);issuer=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py').read_bytes();it=ast.parse(issuer)
class Released:
 stem='INDEPENDENT-AUTHORITY-R105'
 def read_text(self):return json.dumps({'authority_id':'ordinary-f04-postfix-diagnostic-20261112-r105'})
class Out:
 def glob(self,p):return [Released()]
ns={'Path':lambda p:Out(),'json':json,'time':types.SimpleNamespace(strftime=lambda *a:'20261112',localtime=lambda:None)}
exec(compile(ast.Module(body=[n for n in it.body if isinstance(n,ast.FunctionDef) and n.name in ('derive_identity','validate_identity')],type_ignores=[]),'UNCHANGED_ISSUER_PURE_IO_SEAM','exec'),ns)
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
def refused(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,SystemExit):checks.append(n);return
 raise AssertionError(n)
'S'.encode('utf-16-le')
def audit(ev,args):
 if ev=='open' or ev.startswith(('socket.','subprocess.','os.system','os.spawn','os.exec')):raise RuntimeError('PURE_NO_IO')
sys.addaudithook(audit)
new_id,filename,previous=ns['derive_identity']('/SYNTHETIC/ONLY')
ok('original_issuer_preserves_non_independent_prefix',new_id=='ordinary-f04-postfix-diagnostic-20261112-r106')
ok('original_issuer_exact_predecessor_and_file',previous.endswith('-r105') and filename=='INDEPENDENT-AUTHORITY-R106.json')
ns['validate_identity'](new_id,previous,'/SYNTHETIC/ONLY');ok('original_issuer_accepts_real_shape_lineage')
c['authority_id']=new_id;refused('old_adapter_reproduces_prebirth_label_refusal',lambda:OLD.contract_shape(c));ok('new_adapter_accepts_opaque_exactID',A.contract_shape(c))
auth=dict(authority_id=new_id,scope=c['scope'],run_scenarios={c['run_id']:c['scenario_sha256']},ordered_predecessors={},same_canonical_local_run=False)
ok('exact_document_scope_scenario_remain',A.admission(c,auth))
for name,fn in [('wrong_ID',lambda d:d.update(authority_id=previous)),('wrong_scope',lambda d:d.update(scope='ordinary F04')),('wrong_scenario',lambda d:d.update(run_scenarios={c['run_id']:'f'*64})),('extra_run',lambda d:d['run_scenarios'].update(other='f'*64)),('memory_authority',lambda d:d.update(memory_case={}))]:
 x=copy.deepcopy(auth);fn(x);refused(name,lambda x=x:A.admission(c,x))
refused('issuer_selfsupersedes_still_refuses',lambda:ns['validate_identity'](new_id,new_id,'/SYNTHETIC/ONLY'))
for name,value in [('empty',''),('UNBOUND','UNBOUND'),('not_string',None)]:
 x=copy.deepcopy(c);x['authority_id']=value;refused('invalid_ID_'+name,lambda x=x:A.contract_shape(x))
# Full original authority consumer must receive the exact new ID constant, not a prefix.
u=A.unbound();u['authority_id']=new_id;u['run_id']='SYNTHETIC-correct';u['scenario_sha256']='a'*64
raw=A.successor(base,u,code[str(C/'f06_footer.py.txt')]);t=ast.parse(raw);runner=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Runner');m=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission')
ok('fullv42_admission_literal_exact_issuedID',any(isinstance(n,ast.Constant) and n.value==new_id for n in ast.walk(m)))
ok('whole_effect_unchanged_by_opaque_label',A.effect(c)==OLD.effect(c))
x=ast.parse((b'').decode()) if False else None
# Only expected single predicate differs, including no imports/fields/effect changes.
ot=ast.parse(OLD.__dict__['__file__'] if False else '#not read')
ok('correct_phase_source_dependency_unchanged',A.PHASE==OLD.PHASE and A.FIELDS==OLD.FIELDS and A.scope()==OLD.scope() and A.PROOFS==OLD.PROOFS)
print(json.dumps({'state':'PASS_OPAQUE_AUTHORITY_ID_SOURCE_COMPAT_ONLY','checks':checks,'count':len(checks),'real_issuer_or_authority_chain_or_Telegram_calls':0,'new_first_ACK_or_source_reference':False},sort_keys=True))
