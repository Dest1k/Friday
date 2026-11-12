import ast,copy,difflib,hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
b=Path(__file__).resolve().parent;os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);aff=sorted(os.sched_getaffinity(0))[:2];os.sched_setaffinity(0,aff)
start=time.monotonic();rows=[]
def check(name,value):
 assert value,name
 rows.append({'name':name,'pass':True})
pins=json.loads((b/'SOURCE-PINS-DRAFT.json').read_text());paths=[x['path'] for x in pins]
for row in pins:
 for part,key in [('baseline','before_sha256'),('candidate','after_sha256')]:check('sha.'+part+'.'+row['path'],hashlib.sha256((b/part/row['path']).read_bytes()).hexdigest()==row[key])
 for part in ['baseline','candidate']:ast.parse((b/part/row['path']).read_text(),feature_version=(3,12))
# No non-sanitizer runtime functions, guarded startup, or remaining AIAgent definitions change.
def dump(node):return ast.dump(node,include_attributes=False)
def other_runtime(tree):
 result=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in {'sanitize_tool_call_arguments','_prepend_corruption_marker','_find_tool_result','_cursor_skip_prefix'}:continue
  if isinstance(node,ast.ImportFrom) and node.module=='agent.message_sanitization':continue
  result.append(dump(node))
 return result
base=ast.parse((b/'baseline/agent/agent_runtime_helpers.py').read_text());after=ast.parse((b/'candidate/agent/agent_runtime_helpers.py').read_text());check('runtime_unchanged_outside_move',other_runtime(base)==other_runtime(after))
def normalize_facade(tree):
 result=copy.deepcopy(tree)
 for node in result.body:
  if isinstance(node,ast.ImportFrom) and node.module=='agent.message_sanitization':node.names=[n for n in node.names if n.name!='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER']
  if isinstance(node,ast.ClassDef) and node.name=='AIAgent':node.body=[n for n in node.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_TOOL_CALL_ARGUMENTS_CORRUPTION_MARKER' for t in n.targets))]
 return dump(result)
check('all_native_facade_guard_and_methods_ast_unchanged',normalize_facade(ast.parse((b/'baseline/run_agent.py').read_text()))==normalize_facade(ast.parse((b/'candidate/run_agent.py').read_text())))
def normalize_cc(tree):
 tree=copy.deepcopy(tree);tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DB_PERSISTED_MARKER' for t in n.targets)) and not (isinstance(n,ast.ImportFrom) and n.module=='agent.message_metadata' and any(a.name=='_DB_PERSISTED_MARKER' for a in n.names))];return dump(tree)
check('all_compressor_functionality_ast_unchanged',normalize_cc(ast.parse((b/'baseline/agent/context_compressor.py').read_text()))==normalize_cc(ast.parse((b/'candidate/agent/context_compressor.py').read_text())))
# Mandatory complete diff application, no source updater or runtime invocation.
s=b/'composition-stand';s.mkdir(mode=0o700)
try:
 for path in paths:
  p=s/path;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes((b/'baseline'/path).read_bytes())
 for reverse,expected in [(False,'candidate'),(True,'baseline')]:
  args=['/usr/bin/patch','--batch','--fuzz=0','-p1','-i',str(b/'RUNTIME-PURE-COUPLING.patch')]
  if reverse:args.insert(1,'-R')
  p=subprocess.run(args,cwd=s,capture_output=True,timeout=15)
  check('patch_reverse' if reverse else 'patch_forward',p.returncode==0)
  check('exact_result_reverse' if reverse else 'exact_result_forward',all((s/x).read_bytes()==(b/expected/x).read_bytes() for x in paths))
finally:shutil.rmtree(s)
check('stand_removed',not s.exists())
# Native guard sources are read/hash only; baseline five unaffected until Root future integration.
n=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent');guardpaths=['hermes_cli/env_loader.py','hermes_cli/friday_credential_admission.py','hermes_cli/friday_ordinary_gateway.py','hermes_cli/friday_cli_principal.py','agent/reasoning_params.py','agent/turn_iteration_prep.py']
guards=[]
for path in guardpaths:
 p=n/path;raw=p.read_bytes();guards.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'read_only_source_metadata':True})
(b/'GUARD-SOURCE-PINS.json').write_text(json.dumps({'state':'GUARDS_NOT_EDITED_SOURCE_METADATA_ONLY_NO_CURRENT_RUNTIME_PROOF','paths':guards},indent=2)+'\n')
check('five_source_origins_still_match_baseline',all(hashlib.sha256((n/x['path']).read_bytes()).hexdigest()==x['before_sha256'] for x in pins))
result={'state':'COMPOSITION_SOURCE_CHECKS_PASS','checks':rows,'count':len(rows),'pure_controls_reused_unchanged':str(b/'checks/r1/RESULT.json'),'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time(),'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'caps':{'cpu':60,'AS':536870912,'affinity':aff,'outer_wall':90},'live_effects':0,'own_patch_children':'two synchronous subprocess.run; waited/reaped; own stand removed'}
(b/'COMPOSITION-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'state':result['state'],'count':len(rows),'seconds':result['wall_seconds']}))
