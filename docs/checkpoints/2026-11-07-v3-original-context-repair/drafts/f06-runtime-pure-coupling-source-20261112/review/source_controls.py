from pathlib import Path
import ast, copy, json, hashlib, os, resource, signal
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024*1024,4*1024*1024));signal.alarm(90)
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
r=Path(__file__).resolve().parent;b=r.parent
paths=[p['path'] for p in json.loads((b/'SOURCE-PINS-DRAFT.json').read_text())]
texts={(scope,rel):(b/scope/rel).read_text() for scope in ['baseline','candidate'] for rel in paths}
trees={k:ast.parse(v) for k,v in texts.items()}
def dump(node):return ast.dump(node,include_attributes=False)
def node(scope,rel,name):return next(n for n in trees[(scope,rel)].body if getattr(n,'name',None)==name)
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def exact(left,right):return dump(left)==dump(right)
br='agent/agent_runtime_helpers.py';cs='agent/message_sanitization.py'
for name in ['_find_tool_result','_cursor_skip_prefix']:
 check(name+'_AST_exact',exact(node('baseline',br,name),node('candidate',cs,name)))
f=copy.deepcopy(node('baseline',br,'_prepend_corruption_marker'))
f.body=[n for n in f.body if not isinstance(n,ast.ImportFrom)]
check('prepend_AST_exact_except_removed_compressor_import',exact(f,node('candidate',cs,f.name)))
f=copy.deepcopy(node('baseline',br,'sanitize_tool_call_arguments'))
f.body=[n for n in f.body if not isinstance(n,ast.ImportFrom)]
class Direct(ast.NodeTransformer):
 def visit_Call(self,n):
  if dump(n)==dump(ast.parse('logging.getLogger(__name__)',mode='eval').body):return ast.parse('logging.getLogger("agent.agent_runtime_helpers")',mode='eval').body
  return self.generic_visit(n)
 def visit_Attribute(self,n):
  if dump(n)==dump(ast.parse('_ra().AIAgent._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER',mode='eval').body):return ast.Name(id='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER',ctx=ast.Load())
  if dump(n)==dump(ast.parse('_ra().AIAgent._get_tool_call_id_static',mode='eval').body):return ast.Name(id='coalesce_tool_call_id',ctx=ast.Load())
  return self.generic_visit(n)
f=Direct().visit(f)
check('sanitizer_AST_exact_except_three_declared_dependencies',exact(f,node('candidate',cs,'sanitize_tool_call_arguments')))
# All existing leaf functions except the explicitly lazy vision import remain exact.
bnames={n.name:n for n in trees[('baseline',cs)].body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
cnames={n.name:n for n in trees[('candidate',cs)].body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
check('all_existing_leaf_functions_AST_exact',all(exact(n,cnames[name]) for name,n in bnames.items()))
# Entire facade AST equals only declared remove/alias rewiring.
a=copy.deepcopy(trees[('baseline',br)])
a.body=[n for n in a.body if getattr(n,'name',None) not in ['_prepend_corruption_marker','_find_tool_result','_cursor_skip_prefix','sanitize_tool_call_arguments']]
imp=next(n for n in a.body if isinstance(n,ast.ImportFrom) and n.module=='agent.message_sanitization')
imp.names += [ast.alias(name=x) for x in ['sanitize_tool_call_arguments','_prepend_corruption_marker','_find_tool_result','_cursor_skip_prefix']]
check('runtimehelper_entire_AST_exact_except_declared_alias_move',exact(a,trees[('candidate',br)]))
# Native run_agent source guard and every other byte survive the narrow alias delta.
ra='run_agent.py';old=texts[('baseline',ra)];new=texts[('candidate',ra)]
baseclass=node('baseline',ra,'AIAgent');baseassign=next(n for n in baseclass.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER' for x in n.targets))
baseblock='\n'.join(old.splitlines()[baseassign.lineno-1:baseassign.end_lineno])
restored=new.replace('    _TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER as _sanitize_tool_call_arguments_corruption_marker,\n','',1).replace('    _TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER = _sanitize_tool_call_arguments_corruption_marker',baseblock,1)
check('run_agent_all_other_bytes_exact_native_guard_untouched',restored==old)
marker=ast.literal_eval(baseassign.value)
newassign=next(n for n in trees[('candidate',cs)].body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER' for x in n.targets))
check('corruption_marker_literal_exact',marker==ast.literal_eval(newassign.value))
for scope in ['baseline','candidate']:
 cls=node(scope,ra,'AIAgent');static=next(n for n in cls.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_get_tool_call_id_static' for x in n.targets))
 check(scope+'_callID_legacy_static_alias',dump(static.value)==dump(ast.parse('staticmethod(_sanitize_coalesce_tool_call_id)',mode='eval').body))
# Marker relocation is the only metadata/compressor semantic edit.
rel='agent/message_metadata.py';a=copy.deepcopy(trees[('candidate',rel)]);a.body=[n for n in a.body if not (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_DB_PERSISTED_MARKER' for x in n.targets))]
check('metadata_AST_exact_except_marker_ownership',exact(a,trees[('baseline',rel)]))
rel='agent/context_compressor.py';a=copy.deepcopy(trees[('baseline',rel)])
for i,n in enumerate(a.body):
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_DB_PERSISTED_MARKER' for x in n.targets):a.body[i]=ast.ImportFrom(module='agent.message_metadata',names=[ast.alias(name='_DB_PERSISTED_MARKER')],level=0)
check('compressor_AST_exact_except_legacy_marker_import',exact(a,trees[('candidate',rel)]))
# Leaf wrapper delegates without adapting its input/result; no eager vision import remains.
wrapper=node('candidate',cs,'_provider_model_key')
check('vision_lazy_wrapper_exact',dump(wrapper)==dump(ast.parse('def _provider_model_key(agent):\n from agent.vision_message_prep import _provider_model_key as provider_model_key\n return provider_model_key(agent)\n').body[0]))
check('vision_not_eagerly_imported',not any(isinstance(n,ast.ImportFrom) and n.module=='agent.vision_message_prep' for n in trees[('candidate',cs)].body))
# Nearest consumer forward source remains in unchanged native file: source read only.
origin=Path(json.loads((b/'SOURCE-PINS-DRAFT.json').read_text())[0]['source_origin']).parent/'reasoning_params.py'
txt=origin.read_text();tr=ast.parse(txt)
forward=[n for n in ast.walk(tr) if isinstance(n,ast.Assign) and dump(n)==dump(ast.parse('_sanitize_tool_call_arguments = _forward_static(\"agent.agent_runtime_helpers\", \"sanitize_tool_call_arguments\")').body[0])]
check('reasoning_params_has_exact_runtimehelper_forward',len(forward)==1)
print(json.dumps({'status':'PASS','checks':checks,'check_count':len(checks),'reasoning_params_source_sha256':hashlib.sha256(origin.read_bytes()).hexdigest(),'limits':'Source AST/byte parity; reasoning consumer source only, no import/runtime claim','mutation_support_limit':'Out-of-tree replacement of AIAgent marker/static helper no longer governs leaf; supported source constants and static alias match.'},sort_keys=True))
