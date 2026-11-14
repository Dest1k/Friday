from pathlib import Path
import ast,hashlib,json
BASE=Path(__file__).parent
old=Path('/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/caller-root-json-r1/current/current221.py')
full=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
tree=ast.parse(old.read_bytes());defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
checks={}
for name,args in {'database':('slot','private_markers','native_scope'),'services':('closed','h'),'shared_slot':('owner','h'),'inventory':('path',),'selected_access':('row',)}.items():checks['old_'+name+'_exact_signature']=tuple(x.arg for x in defs[name].args.args)==args
v=ast.parse((BASE/'current222.py').read_bytes());f=ast.parse(full.read_bytes());runner=next(n for n in f.body if isinstance(n,ast.ClassDef) and n.name=='Runner');methods={n.name for n in runner.body if isinstance(n,ast.FunctionDef)}
for name in ('ordinary_independent_admission','new','_send','verify_reply_custody','terminal_drain'):checks['v42_'+name+'_exists']=name in methods
checks['v42_pin']=hashlib.sha256(full.read_bytes()).hexdigest()=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
checks['no_old_F03_authorization_calls']=not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='t' and n.func.attr in ('observe','check','effect_shape','semantics','closure','installed','native','resources') for n in ast.walk(v))
checks['import_has_no_effect_calls']=not any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) for n in v.body)
assert all(checks.values()),checks
print(json.dumps({'source_only':True,'passed':len(checks),'failed':0,'assertions':checks},sort_keys=True))
