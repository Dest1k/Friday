import ast,hashlib,json,os,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
base=BASE.read_bytes();assert hashlib.sha256(base).hexdigest()=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
def ref(p):
 r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
checks=[];artifacts={}
def good(n,v):assert v,n;checks.append(n)
for branch in ('first','correct'):
 d=B/'candidate'/branch;p=d/'f06_source.py';m=types.ModuleType('actual_pure_'+branch);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
 raw=json.loads((B/'producer-controls'/(branch+'-binding.json')).read_bytes());c=raw.get('contract',raw)
 c['footer']=ref(d/'f06_footer.py.txt');c['adapter']=ref(p)
 c['actual_root_B_checker']=ref(d/('current207.py' if branch=='first' else 'current_root.py'))
 c=json.loads(m.encoded(c))
 c['root_current_proof']={'path':str(B/'NEVER-OPENED-SYNTHETIC-FRESH-PROOF'),'bytes':123,'sha256':'3'*64}
 footer=(d/'f06_footer.py.txt').read_bytes();out=m.successor(base,c,footer);roundtrip=json.loads(m.encoded(c));again=m.successor(base,roundtrip,footer)
 good(branch+':exact_actual_footer_source_readback',out==again)
 tree=ast.parse(out);compile(tree,'SYNTHETIC_NEVER_EXECUTED_SOURCE','exec')
 good(branch+':actual_footer_whole_source_compiles',True)
 value=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='F06_CONTRACT' for t in n.targets));good(branch+':embedded_contract_values_equal',ast.literal_eval(value.value)==c)
 before=ast.parse(base);old=next(n for n in before.body if isinstance(n,ast.ClassDef) and n.name=='Runner');new=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
 funcs=lambda cls:{n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 bf,af=funcs(old),funcs(new);good(branch+':191_methods',len(bf)==len(af)==191);good(branch+':190_base_methods_exact',all(af[k]==v for k,v in bf.items() if k!='ordinary_independent_admission'))
 try:m.successor(base,c,footer+b'# changed')
 except ValueError as e:good(branch+':actual_footer_pin_drift_refused',e.args==('F06_PINNED_FOOTER_REQUIRED',))
 else:raise AssertionError('footer drift')
 path=B/(branch+'-ACTUAL-FOOTER-SYNTHETIC-NOT-RUNTIME.py');path.write_bytes(out);artifacts[branch]=ref(path)
print(json.dumps({'status':'PURE_ACTUAL_FOOTER_SOURCE_CONSTRUCTION_PASS','synthetic_contract_only':True,'generated_consumer_executed':False,'checks':checks,'count':len(checks),'artifacts':artifacts},sort_keys=True))
