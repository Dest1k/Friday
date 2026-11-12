import copy,datetime,hashlib,importlib.util,json,os,resource,sys,time
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
B=Path(__file__).resolve().parent;R=Path('/home/jericho/jericho/Friday_rework');H=R/'.runtime/friday-normal-both-workers-frw032'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
checks=[]
def check(name,ok,**facts):
 checks.append(dict(name=name,pass_=bool(ok),**facts));assert ok,name
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
start=time.monotonic();started=datetime.datetime.now().astimezone().isoformat()
builder=load(B/'publication/build-layer-publication-request.py','source208_builder');publisher=builder.publication()
spec=json.loads((B/'FINAL-NATIVE-SPEC.json').read_bytes())
previous=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112/INPUT-SOURCE207.json')
predecessor=H/'preparation/ordinary-source-update-v45-6320a882b34740a5/request.json'
rawprior=json.loads(predecessor.read_bytes());root=rawprior['current_source_successor']['root_project_update']
check('actual_predecessor207_raw_pin',sha(predecessor)=='6320a882b34740a5e76b876ce3531a1966e58a9d2ebaf00162e684226042c89c')
check('actual_previous207_input_pin',sha(previous)=='c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838')
argv=['--layer',spec['layer'],'--home',str(H),'--candidate-project',str(B/'project497'),'--previous-input',str(previous),'--current-input',str(B/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json'),'--current-source-project-update',root['path'],'--current-source-native-predecessor',str(predecessor),'--output',str(B/'NEVER-EMITTED-ACTUAL-REQUEST.json'),'--seconds','600']
check('builder_historical_default_four_unchanged',tuple(builder.parse_args([]).layer_names)==tuple(publisher.HISTORICAL_LAYER_NAMES) and len(builder.LAYER_NAMES)==4)
before={str(p):sha(p) for p in (H/'hermes-agent.source.json',H/'FRIDAY-INSTALL.json',H/'hermes-agent/install-stamp.json',predecessor,previous,H/'hermes-agent/gateway/run_turn.py',H/'hermes-agent/agent/turn_context.py')}
failure=None;request=None
try:
 args=builder.parse_args(argv);request=builder.build_request(args)
 check('normal_builder_actual207_to208_preflight_passed',request['current_source_successor']['schema']=='friday.current-source-native-successor.v10' and request['current_source_successor']['previous_native_update']==dict(path=str(predecessor),sha256=sha(predecessor)))
 check('exact_actual_counts_and_scope',request['installed_layers']==207 and request['installed_files']==17891 and len(request['project_inventory'])==497 and request['project_file_updates']==['scripts/friday_ordinary_install.py'] and not request['plugin_set'] and not request['plugin_additions'] and not request['staged_files'])
 check('normal_consumer_actual_origin',str(sys.modules['scripts.friday_install'].ROOT)==str(B/'project497') and Path(sys.modules['scripts.friday_ordinary_install'].__file__).resolve()==B/'project497/scripts/friday_ordinary_install.py')
 check('input_nonproject_equal_actual207',{k:v for k,v in json.loads(previous.read_bytes()).items() if k!='project_files'}=={k:v for k,v in json.loads((B/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json').read_bytes()).items() if k!='project_files'})
 # Necessary new-boundary refusals run the real whole builder/consumer; no live writes.
 for label,mutate in [
  ('wrong_predecessor206',lambda a:setattr(a,'current_source_native_predecessor',Path(rawprior['current_source_successor']['previous_native_update']['path']))),
  ('installed_layer207_selected',lambda a:(setattr(a,'layer_names',('f06-modern-odt-authenticated-profile-after-source206',)),setattr(a,'layer',['f06-modern-odt-authenticated-profile-after-source206']))),
 ]:
  a=copy.copy(args);mutate(a)
  try:builder.build_request(a)
  except Exception as exc:check(label+'_refused',True,reason=getattr(exc,'reason',str(exc)[:160]))
  else:check(label+'_refused',False)
 for label,mutate in [
  ('unsupported_v11',lambda q:q['current_source_successor'].update(schema='friday.current-source-native-successor.v11')),
  ('wrong_before_count206',lambda q:q.update(installed_layers=206)),
  ('wrong_previous_input206',lambda q:q.update(previous_input=rawprior['previous_input'])),
  ('wrong_predecessor_digest',lambda q:q['current_source_successor']['previous_native_update'].update(sha256='f'*64)),
  ('wrong_predecessor_root',lambda q:q['current_source_successor']['root_project_update'].update(sha256='f'*64)),
 ]:
  q=copy.deepcopy(request);mutate(q)
  try:publisher.current_source_consumer_checked(json.loads((B/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json').read_bytes()),q,B/'project497')
  except Exception as exc:check(label+'_refused',True,reason=getattr(exc,'reason',str(exc)[:160]))
  else:check(label+'_refused',False)
except Exception as exc:
 failure=dict(class_=type(exc).__name__,reason=getattr(exc,'reason',str(exc)[:160]))
check('exact_live_files_unchanged',all(sha(Path(p))==h for p,h in before.items()))
check('no_actual_request_output_created',not (B/'NEVER-EMITTED-ACTUAL-REQUEST.json').exists())
result=dict(state='PASS_ACTUAL_READONLY_BUILDER_PREFLIGHT' if failure is None else 'FAILED_ACTUAL_READONLY_BUILDER_PREFLIGHT',started=started,elapsed_seconds=time.monotonic()-start,checks=checks,failure=failure,actual_predecessor=ref(predecessor),actual_previous_input=ref(previous),consumer_origin=str(B/'project497'),fresh_request_emitted=False,source_only=True,no_runtime_or_install_or_user_acceptance=True)
(B/'ACTUAL-BUILDER-CONSUMER-CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(state=result['state'],elapsed_seconds=result['elapsed_seconds'],checks=len(checks),failure=failure)))
if failure:raise SystemExit(1)
