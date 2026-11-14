"""Independent exact captured source controls. Every runtime leaf is inert."""
import ast, asyncio, builtins, copy, hashlib, json, re, types
from pathlib import Path
CAPTURE=Path('/home/jericho/.cache/FRW-ASTRA-SOL-T90-F04-ROOT-ORDINARY-CALLER-20261115/static-native-stop-source')
refs=json.loads((CAPTURE/'SOURCE-REFS.json').read_bytes())
results=[]
def check(name, fn):
    try: fn()
    except Exception as e: results.append({'check':name,'passed':False,'class':type(e).__name__})
    else: results.append({'check':name,'passed':True})
def require(v):
    if not v: raise AssertionError('INDEPENDENT_SOURCE_ASSERTION')
for name,r in refs['files'].items():
    raw=Path(r['path']).read_bytes()
    require(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'])
tree=ast.parse(Path(refs['files']['gateway/ordinary_turn_projection.py']['path']).read_bytes())
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'KEY','SID','PROFILE'}}
# Execute the exact token-list expression, on inert objects, to pin native shape.
snapshot=functions['snapshot']
assign=next(n for n in snapshot.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tokens' for t in n.targets))
token=types.SimpleNamespace(session_id=constants['SID'],owner_key=constants['KEY'],generation=4,released=False)
actual_tokens=eval(compile(ast.Expression(assign.value),'<captured-snapshot-token-expression>','eval'),{'turn':types.SimpleNamespace(lease_tokens={'synthetic':token}),'dict':dict})
check('actual_snapshot_token_is_exact_structured_lease',lambda:require(actual_tokens==[{'session_id':constants['SID'],'owner_key':constants['KEY'],'generation':4,'released':False}]))
# Actual readonly handler rejects unsupported scopes before scheduling a coroutine.
class Never:
    def __getattr__(self,k): raise AssertionError('FORBIDDEN_RUNTIME_LEAF')
ns={'KEY':constants['KEY'],'SID':constants['SID'],'asyncio':Never(),'concurrent':Never(),'snapshot':Never(),'m09_snapshot':Never()}
exec(compile(ast.Module(body=[functions['ordinary_turn_readonly_verb']],type_ignores=[]),'<captured-readonly-handler>','exec'),ns)
handler=ns['ordinary_turn_readonly_verb'](Never(),Never())
check('actual_readonly_foreign_scope_refuses_before_runtime',lambda:require(handler({'session_key':'INERT_FOREIGN','session_id':constants['SID']})=={'accepted':False,'error':'exact_ordinary_scope_required'}))
# Extract exact async dispatch body; imports are restricted to inert dependencies.
outer=functions['ordinary_turn_cancel_verb'];handler_ast=next(n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name=='handler');dispatch=next(n for n in handler_ast.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='dispatch')
regex_calls=[n for n in ast.walk(dispatch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='re' and n.func.attr=='fullmatch']
require(len(regex_calls)==1);pattern=ast.literal_eval(regex_calls[0].args[0])
check('actual_cancel_operation_family_excludes_f04',lambda:require(re.fullmatch(pattern,'root-f04-0123456789ab') is None))
check('actual_cancel_operation_family_distinguishes_v04_from_f04',lambda:require(re.fullmatch(pattern,'root-v04-0123456789ab') is not None and re.fullmatch(pattern,'root-f04-0123456789ab') is None))
imports=[]
def forbidden_home(): raise AssertionError('FORBIDDEN_HOME_OR_INTENT_READ')
def allowed_import(name,globals=None,locals=None,fromlist=(),level=0):
    imports.append(name)
    if name=='json': return json
    if name=='re': return re
    if name=='hermes_constants': return types.SimpleNamespace(get_process_hermes_home=forbidden_home)
    if name=='gateway.run': return types.SimpleNamespace(_INTERRUPT_REASON_STOP='INERT')
    raise AssertionError('UNEXPECTED_IMPORT')
params={k:None for k in ('schema','operation_id','text','root_intent','boot_id','deadline_monotonic','source_receipt_sha256','owned_turn','rights_sha256')}
params.update(schema='frw.Root.s05-owned-native-stop.v1',operation_id='root-f04-0123456789ab',text='/stop')
ns={'params':params,'runner':Never(),'loop':Never(),'__builtins__':dict(vars(builtins),__import__=allowed_import)}
exec(compile(ast.Module(body=[dispatch],type_ignores=[]),'<captured-native-stop-dispatch>','exec'),ns)
result=asyncio.run(ns['dispatch']())
check('actual_cancel_dispatch_refuses_F04_before_home_intent_current_or_effect',lambda:require(result=={'accepted':False,'error':'exact_owned_cancel_schema'}))
# Gateway exact captured registration is inspected, never imported/executed.
run=ast.parse(Path(refs['files']['gateway/run.py']['path']).read_bytes())
verbs=[n for n in ast.walk(run) if isinstance(n,ast.keyword) and n.arg=='verb_handlers' and isinstance(n.value,ast.Dict)]
check('actual_gateway_registers_captured_cancel_verb',lambda:require(any(any(isinstance(k,ast.Constant) and k.value=='ordinary-turn-cancel' and isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='ordinary_turn_cancel_verb' for k,v in zip(n.value.keys,n.value.values))for n in verbs)))
report={'schema':'frw.T90.independent-native-source-controls.v1','source_only':True,'runtime_leaves':'INERT','native_full_module_not_imported':True,'current_queries_or_effects':False,'passed':sum(x['passed']for x in results),'failed':sum(not x['passed']for x in results),'checks':results,'capture_source_refs_sha256':hashlib.sha256((CAPTURE/'SOURCE-REFS.json').read_bytes()).hexdigest()}
p=Path(__file__).with_name('NATIVE-SOURCE-CONTROLS.json');p.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');p.chmod(0o600)
print(json.dumps({'passed':report['passed'],'failed':report['failed'],'path':str(p)}));raise SystemExit(bool(report['failed']))
