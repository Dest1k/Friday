import os,sys,resource,time,json,ast,copy,logging,io,importlib.abc,hashlib,types
from pathlib import Path
B=Path(__file__).resolve().parent
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
cpus=sorted(os.sched_getaffinity(0))[:2];os.sched_setaffinity(0,cpus)
started=time.monotonic();rows=[]
def check(name,value):
 if not value:raise AssertionError(name)
 rows.append({'name':name,'pass':True})
# No full application source/dependencies exist in this stand. No sys.modules fake.
S=B/'pure-stand';sys.path.insert(0,str(S));sys.dont_write_bytecode=True
class Forbidden(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'run_agent','hermes_cli','utils','model_tools','dotenv','openai','anthropic'} or fullname in {'agent.context_compressor','agent.vision_message_prep','agent.credential_pool'}:
   raise AssertionError('FORBIDDEN_APP_IMPORT')
sys.meta_path.insert(0,Forbidden())
# Fail if implementation tries any app file, socket, child, or arbitrary filesystem write.
allowed_root=Path(sys.base_prefix).resolve();stdlib=Path(os.__file__).resolve().parent
file_events=[]
def audit(event,args):
 if event in {'subprocess.Popen','os.system','socket.__new__','socket.connect','os.fork','os.posix_spawn'}:raise AssertionError('FORBIDDEN_EFFECT')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(p)).resolve()
   if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise AssertionError('FORBIDDEN_WRITE')
   if not (p.is_relative_to(B) or p.is_relative_to(stdlib)) :raise AssertionError('FORBIDDEN_READ')
   file_events.append(str(p))
sys.addaudithook(audit)
from agent import message_sanitization as m
from agent import message_metadata as meta
from agent import tool_dispatch_helpers as td
from agent import lazy_forward
check('application_module_absent',all(k not in sys.modules for k in ['run_agent','agent.context_compressor','agent.vision_message_prep','agent.credential_pool','hermes_cli.config']))
check('physical_stand_has_no_application',not (S/'run_agent.py').exists() and not (S/'agent/context_compressor.py').exists() and not (S/'hermes_cli').exists())
# Fixed clock covers actual constructor timestamps in differential comparisons only.
meta.wall_time=lambda:1234567890.0
marker=m._TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER;stamp=meta._DB_PERSISTED_MARKER
old=ast.parse((B/'baseline/agent/agent_runtime_helpers.py').read_text());new=ast.parse((B/'candidate/agent/message_sanitization.py').read_text())
names={'_prepend_corruption_marker','_find_tool_result','_cursor_skip_prefix','sanitize_tool_call_arguments'}
oldfunc={x.name:x for x in old.body if isinstance(x,ast.FunctionDef) and x.name in names};newfunc={x.name:x for x in new.body if isinstance(x,ast.FunctionDef) and x.name in names}
class OwnerRename(ast.NodeTransformer):
 def visit_ImportFrom(self,node):
  if node.module=='agent.context_compressor' and [x.name for x in node.names]==['_DB_PERSISTED_MARKER']:return None
  return node
 def visit_Attribute(self,node):
  if isinstance(node.value,ast.Attribute) and isinstance(node.value.value,ast.Call) and isinstance(node.value.value.func,ast.Name) and node.value.value.func.id=='_ra' and node.value.attr=='AIAgent':
   if node.attr=='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER':return ast.copy_location(ast.Name(id='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER',ctx=ast.Load()),node)
   if node.attr=='_get_tool_call_id_static':return ast.copy_location(ast.Name(id='coalesce_tool_call_id',ctx=ast.Load()),node)
  return self.generic_visit(node)
 def visit_Call(self,node):
  node=self.generic_visit(node)
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='logging' and node.func.attr=='getLogger' and len(node.args)==1 and isinstance(node.args[0],ast.Name) and node.args[0].id=='__name__':node.args=[ast.Constant('agent.agent_runtime_helpers')]
  return node
normalized=[ast.fix_missing_locations(OwnerRename().visit(copy.deepcopy(oldfunc[name]))) for name in ['_prepend_corruption_marker','_find_tool_result','_cursor_skip_prefix','sanitize_tool_call_arguments']]
for f in normalized:check('body_parity.'+f.name,ast.dump(f,include_attributes=False)==ast.dump(newfunc[f.name],include_attributes=False))
# Reference uses only normalized original four function ASTs + actual leaf policies, NOT mocked run_agent/bootstrap.
ref=dict(vars(m));ref['__name__']='normalized_baseline_reference'
exec(compile(ast.Module(body=normalized,type_ignores=[]),'<normalized-original-functions>','exec'),ref)
def call(cid,args='{"x":',name='other',**kw):return {'id':cid,'type':'function','function':{'name':name,'arguments':args},**kw}
def record(items):return {'role':'assistant',stamp:True,'content':'unchanged prose','tool_calls':items}
cases={
 'empty':[], 'nondict':[None,5,'text'], 'valid':[record([call('v','{"x":1}')])],
 'empty_none':[record([call('e',None)])], 'empty_ws':[record([call('e','  ')])],
 'dict_args':[record([call('d',{'password':'synthetic-only'})])],
 'invalid':[record([call('b')])], 'no_function':[record([{},None,{'function':'x'}])],
 'codex_precedence':[record([call('item-id',call_id='call-id')])],
 'existing_alias':[record([call('item-id',call_id='call-id',response_item_id='response')]),{'role':'tool','tool_call_id':'item-id','content':'kept',stamp:True}],
 'composite':[record([call('call-z|item-z')]),{'role':'tool','tool_call_id':'item-z','content':'kept',stamp:True}],
 'unrelated_result':[record([call('b')]),{'role':'tool','tool_call_id':'unrelated','content':'keep',stamp:True}],
 'boundary':[record([call('b')]),{'role':'user','content':'private chat unchanged'},{'role':'tool','tool_call_id':'b','content':'too late'}],
 'duplicate_id':[record([call('dup'),call('dup')])],
 'existing_marker':[record([call('b')]),{'role':'tool','tool_call_id':'b','content':marker+'\nkept',stamp:True}],
 'nonstring_result':[record([call('b')]),{'role':'tool','tool_call_id':'b','content':{'x':1},stamp:True}],
 'null_result':[record([call('b')]),{'role':'tool','tool_call_id':'b','content':None,stamp:True}],
 'unknown_name':[record([{'id':'b','function':{'arguments':'bad'}}])],
 'web_result':[record([call('w',name='web_search')])],
 'unicode':[record([call('u','{"text":"кириллица 😀"}')])],
 'malformed_read':[record([call('r','{"password":"SYNTHETIC_PRIVATE",',name='read_file')])],
 'malformed_write':[record([call('w','{"password":"SYNTHETIC_PRIVATE",',name='write_file')])],
}
def invoke(fn,messages,cursor=None):
 stream=io.StringIO();log=logging.Logger('synthetic');handler=logging.StreamHandler(stream);log.addHandler(handler)
 n=fn(messages,logger=log,session_id='synthetic-session',cursor=cursor)
 return n,stream.getvalue()
for name,items in cases.items():
 a=copy.deepcopy(items);b=copy.deepcopy(items);ca={};cb={}
 ra=invoke(ref['sanitize_tool_call_arguments'],a,ca);rb=invoke(m.sanitize_tool_call_arguments,b,cb)
 check('differential.'+name,ra==rb and a==b and ca==cb)
 if name in {'malformed_read','malformed_write'}:check('warning_privacy.'+name,'SYNTHETIC_PRIVATE' not in rb[1] and '[redacted file-tool arguments]' in rb[1])
check('non_list_returns_zero',m.sanitize_tool_call_arguments(None)==0 and m.sanitize_tool_call_arguments({})==0)
a=[record([call('b')])];n,logs=invoke(m.sanitize_tool_call_arguments,a)
check('actual_repair',n==1 and a[0]['tool_calls'][0]['function']['arguments']=='{}' and len(a)==2 and a[1]['tool_call_id']=='b' and a[1]['content']==marker)
check('persisted_marker_removed',stamp not in a[0])
check('content_unchanged',a[0]['content']=='unchanged prose')
check('already_repaired_idempotent',invoke(m.sanitize_tool_call_arguments,a)[0]==0)
a=[record([call('v','{}')])];cursor={};m.sanitize_tool_call_arguments(a,cursor=cursor);a.append(record([call('new')]))
check('cursor_append',m.sanitize_tool_call_arguments(a,cursor=cursor)==1 and all(x is y for x,y in zip(cursor['prefix'],a)))
a[0]=record([call('replaced')]);check('cursor_replacement',m.sanitize_tool_call_arguments(a,cursor=cursor)==1)
check('dict_argument_not_redacted_in_execution',cases['dict_args'][0]['tool_calls'][0]['function']['arguments']['password']=='synthetic-only')
# Legacy aliases are executed ONLY as exact import/assignment AST statements; full native app never imported.
runtime_tree=ast.parse((B/'candidate/agent/agent_runtime_helpers.py').read_text());alias_ns={}
for node in runtime_tree.body:
 if isinstance(node,ast.ImportFrom) and node.module=='agent.message_sanitization':exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<runtime-leaf-reexports>','exec'),alias_ns)
check('legacy_helper_same_function',alias_ns['sanitize_tool_call_arguments'] is m.sanitize_tool_call_arguments)
for name in names-{'sanitize_tool_call_arguments'}:check('legacy_private_alias.'+name,alias_ns[name] is getattr(m,name))
ra_tree=ast.parse((B/'candidate/run_agent.py').read_text());class_node=next(x for x in ra_tree.body if isinstance(x,ast.ClassDef) and x.name=='AIAgent');class_ns={}
imports=[x for x in ra_tree.body if isinstance(x,ast.ImportFrom) and x.module=='agent.message_sanitization']
for node in imports:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<facade-pure-imports>','exec'),class_ns)
for node in class_node.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER','_get_tool_call_id_static'} for t in node.targets):exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<facade-alias-assignments>','exec'),class_ns)
check('facade_marker_identity',class_ns['_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER'] is marker)
check('facade_static_id_identity',class_ns['_get_tool_call_id_static'].__func__ is m.coalesce_tool_call_id)
cc_tree=ast.parse((B/'candidate/agent/context_compressor.py').read_text());cc_ns={}
for node in cc_tree.body:
 if isinstance(node,ast.ImportFrom) and node.module=='agent.message_metadata' and any(x.name=='_DB_PERSISTED_MARKER' for x in node.names):exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<compressor-marker-alias>','exec'),cc_ns)
check('compressor_marker_identity',cc_ns['_DB_PERSISTED_MARKER'] is meta._DB_PERSISTED_MARKER)
stream=io.StringIO();log=logging.getLogger('agent.agent_runtime_helpers');h=logging.StreamHandler(stream);log.addHandler(h)
try:m.sanitize_tool_call_arguments([record([call('log')])])
finally:log.removeHandler(h)
check('default_logger_preserved','Corrupted tool_call arguments repaired before request' in stream.getvalue())
check('end_app_absence','run_agent' not in sys.modules and 'agent.context_compressor' not in sys.modules and 'hermes_cli.config' not in sys.modules)
print(json.dumps({'state':'SOURCE_PURE_CONTROLS_PASS','checks':rows,'count':len(rows),'not_runtime_or_user_acceptance':True,'normalization_scope':'four original functions; only explicit dependency-owner/logger AST replacements, no app import or guard mock','imported_own_modules':[k for k,v in sys.modules.items() if getattr(v,'__file__',None) and str(getattr(v,'__file__')).startswith(str(S))],'source_reads':len(file_events),'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time(),'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':{'wall_seconds_outer':90,'cpu_seconds':60,'as_bytes':536870912,'affinity':cpus}},indent=2))
