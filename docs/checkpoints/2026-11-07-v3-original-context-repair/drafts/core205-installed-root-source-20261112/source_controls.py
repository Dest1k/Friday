"""Finite pure changed-scope controls. No actor/builder/collector import or execution."""
from pathlib import Path
import ast,builtins,copy,datetime,hashlib,json,os,resource,sys,time,types
B=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
START=time.monotonic();rows=[]
def record(name,fn):
 if time.monotonic()-START>90:raise RuntimeError('pure_controls_wall_exhausted')
 fn();rows.append(dict(name=name,state='PASS'))
def eq(a,b):assert a==b,(a,b)
def rejects(fn):
 try:fn()
 except (ValueError,RuntimeError,AssertionError,KeyError):return
 raise AssertionError('negative_accepted')
def pure(name):
 m=types.ModuleType(name);m.__file__=str(B/(name+'.py'));exec(compile((B/(name+'.py')).read_bytes(),m.__file__,'exec'),m.__dict__);return m
c=pure('boundary_contract');meta=pure('root205_metadata')
ref=lambda label:dict(path='/source/'+label,sha256='a'*64)
refs={k:ref(k)for k in ('manifest','boundary','caller','anchor','source_acceptance','predecessor')}
A=dict(schema='frw.root.native205-reviewed-future-boundary.v1',state='ROOT_REVIEWED_EXACT205_FUTURE_EXECUTION',template_only_no_execution_grant=False,source_pin_manifest=refs['manifest'],boundary=refs['boundary'],caller=refs['caller'],current_service_anchor=refs['anchor'],source_acceptance=refs['source_acceptance'],actual204_predecessor=refs['predecessor'],frame='/source/frame',execution_commit='1'*40,origin_url='https://github.com/Dest1k/Friday',provenance_mode='local-committed-main',public_main_sha=None,future_finite_operation_reviewed=True,original_future205_budgets=dict(actor=1800,source=600,publisher_unit=810,publisher_client=840,cold_each=180,postcheck=90,reserve=75),old_effects_clocks_preserved=True,Task23_future206_not_integrated=True,shared_slot_identity=[1,2,os.getuid(),1,384])
def auth(v):return c.validate_authority(v,**refs,frame='/source/frame')
record('authority_exact_future205',lambda:auth(A))
for url in ('https://github.com/Dest1k/Friday','https://github.com/Dest1k/Friday.git'):
 v=copy.deepcopy(A);v['origin_url']=url;record('origin_accepted_'+url.rsplit('/',1)[-1],lambda v=v:auth(v))
for key,val in [('origin_url','https://github.com/Dest1k/restricted'),('frame','/old/frame'),('execution_commit','UNBOUND'),('public_main_sha','1'*40),('future_finite_operation_reviewed',False),('old_effects_clocks_preserved',False),('Task23_future206_not_integrated',False),('template_only_no_execution_grant',True),('shared_slot_identity',[1,2,os.getuid(),2,384])]:
 v=copy.deepcopy(A);v[key]=val;record('authority_reject_'+key,lambda v=v:rejects(lambda:auth(v)))
for key in ('source_pin_manifest','boundary','caller','current_service_anchor','source_acceptance','actual204_predecessor'):
 v=copy.deepcopy(A);v[key]=ref('wrong');record('authority_exact_ref_'+key,lambda v=v:rejects(lambda:auth(v)))
v=copy.deepcopy(A);v.update(provenance_mode='published-remote',public_main_sha='1'*40);record('published_mode_exact',lambda:auth(v))
for value in (datetime.datetime.now(datetime.timezone.utc).isoformat(),):record('fresh_timestamp',lambda value=value:c.fresh(value,time.time()))
for value in ('2000-01-01T00:00:00+00:00','2999-01-01T00:00:00+00:00','2026-11-12T01:00:00'):
 record('fresh_reject_'+value,lambda value=value:rejects(lambda:c.fresh(value,time.time())))
identity=dict(pid=17,birth_ticks=23,boot_id='b'*36)
globalwork=dict(scope='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',read_only=True,identity=dict(pid=17,start_time=23,boot_id='b'*36),observed_monotonic=10,global_active_session_keys=[],web_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False),terminal_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False))
dbs={name:dict(quick_check='ok',leases=0,all_origin_pending_delegations=0)for name in ('default','dest','tester')}
def quiet(g=globalwork,d=dbs,now=11):return c.validate_global_quiescence(g,d,identity,current_monotonic=now)
record('global_native_and_all3DB_allorigin_exact',quiet)
for name in dbs:
 for key in ('leases','all_origin_pending_delegations'):
  d=copy.deepcopy(dbs);d[name][key]=1;record('reject_'+name+'_'+key,lambda d=d:rejects(lambda:quiet(d=d)))
for key,val in [('scope','DEFAULT_SCOPED_ONLY'),('global_active_session_keys',['another-profile']),('observed_monotonic',-20),('identity',dict(pid=18,start_time=23,boot_id='b'*36))]:
 g=copy.deepcopy(globalwork);g[key]=val;record('global_reject_'+key,lambda g=g:rejects(lambda:quiet(g=g)))
for key in ('terminal_custody','web_custody'):
 g=copy.deepcopy(globalwork);g[key]['sessions']=['inflight'];record('global_reject_'+key,lambda g=g:rejects(lambda:quiet(g=g)))
record('whole_transaction_path_reject',lambda:rejects(lambda:c.guard_absent(['/tx/whole'],lambda _:True)))
record('missing_transaction_path_accept',lambda:c.guard_absent(['/tx/whole'],lambda _:False))
record('service_identity_change_refused',lambda:rejects(lambda:c.compare_service({'pid':1},{'pid':2},{},{})))
record('service_environment_change_refused',lambda:rejects(lambda:c.compare_service({'pid':1},{'pid':1},{'HERMES_HOME':'old'},{'HERMES_HOME':'new'})))
# Closest actual boundary sourceprefix: execute its unchanged AST in-memory with
# deterministic Git/source metadata responses; no subprocess/Git/network/runtime read.
tree=ast.parse((B/'core205-first-actual-root.py').read_bytes());boundary=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='boundary')
cut=next(i for i,n in enumerate(boundary.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='boot'for t in n.targets));prefix=copy.deepcopy(boundary);prefix.body=prefix.body[:cut]+[ast.Return(ast.Name(id='origin_proof',ctx=ast.Load()))];ast.fix_missing_locations(prefix)
def sourceprefix(*,url='https://github.com/Dest1k/Friday.git',changes=('docs/status.md','README.md'),mode='local-committed-main',remote=None,head='1'*40):
 calls=[]
 def run(argv,timeout=20):
  calls.append(argv)
  if 'get-url'in argv:return types.SimpleNamespace(stdout=url+'\n')
  if 'rev-parse'in argv:return types.SimpleNamespace(stdout=head+'\n')
  if 'merge-base'in argv:return types.SimpleNamespace(stdout='')
  if 'diff'in argv:return types.SimpleNamespace(stdout='\0'.join(changes)+'\0')
  if 'ls-remote'in argv:return types.SimpleNamespace(stdout=(remote or '')+'\trefs/heads/main\n')
  raise AssertionError(argv)
 def origin(expected,observed,provenance_mode):
  c.require(expected==head,'exact_head');c.require(observed is None if provenance_mode=='local-committed-main'else observed==expected,'mode');return dict(current_head=head)
 ns=dict(run=run,require=c.require,R=Path('/source/repository'),m=types.SimpleNamespace(source_origin=origin),sha=lambda p:'f'*64)
 exec(compile(ast.Module(body=[prefix],type_ignores=[]),'<actual205boundary-prefix>','exec'),ns)
 result=ns['boundary'](ns['m'],None,None,dict(execution_provenance_mode=mode,execution_commit='1'*40,execution_public_main_sha=remote,public_changed_files={'scripts/friday_ordinary_install.py':'f'*64}),None,None,None,None,None)
 return result,calls
record('closest_boundary_local_git_mode',lambda:eq(sourceprefix()[0],dict(current_head='1'*40)))
record('closest_boundary_local_never_network',lambda:eq(any('ls-remote'in x for x in sourceprefix()[1]),False))
record('closest_boundary_bothURL_noGit',lambda:sourceprefix(url='https://github.com/Dest1k/Friday'))
record('closest_boundary_restrictedURL_refused',lambda:rejects(lambda:sourceprefix(url='https://github.com/Dest1k/restricted')))
record('closest_boundary_unreviewed_product_refused',lambda:rejects(lambda:sourceprefix(changes=('scripts/unreviewed.py',))))
record('closest_boundary_reviewed_product_exact',lambda:sourceprefix(changes=('scripts/friday_ordinary_install.py',)))
record('closest_boundary_published_exact',lambda:sourceprefix(mode='published-remote',remote='1'*40))
record('closest_boundary_wrong_HEAD_refused',lambda:rejects(lambda:sourceprefix(head='2'*40)))
record('closest_boundary_no_implicit_fallback',lambda:rejects(lambda:sourceprefix(mode='published-remote',remote=None)))
# Genuine predecessor controls use saved source/transaction metadata only and an
# in-memory proposed Root record, never write an actual predecessor or request.
h=json.loads((B/'ACTUAL204-HISTORICAL-METADATA.json').read_bytes());r=dict(schema='frw.root.actual204-predecessor.v1',state='ROOT_RECONCILED_GENUINE_INSTALLED204_NOT_EXPECTATION',template_only_no_execution_grant=False,**h['references'])
original=meta.readref
registry={str(B/'ROOT-ACTUAL204-PREDECESSOR.json'):r}
def memref(path):
 if str(path)in registry:return dict(path=str(path),sha256='e'*64)
 return dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
meta.reference=memref
meta.readref=lambda v:copy.deepcopy(registry[v['path']])if v['path']in registry else original(v)
record('actual_CP204_real_saved_committed_prefix',lambda:eq(meta.actual_predecessor(),h['references']['request']))
for key in ('request','committed','root_journal','complete_closure'):
 old=registry[str(B/'ROOT-ACTUAL204-PREDECESSOR.json')][key];registry[str(B/'ROOT-ACTUAL204-PREDECESSOR.json')][key]=ref('synthetic-'+key)
 record('actual_CP204_fake_'+key+'_refused',lambda:rejects(meta.actual_predecessor));registry[str(B/'ROOT-ACTUAL204-PREDECESSOR.json')][key]=old
# Source identity/immutable historical defaultfour and actor R2 functions.
old=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-ROOT-FRAME-PREP-20261111')
for name in ('publication/build-layer-publication-request.py','publication/friday_v3_layer_publication.py','PROFILE-SOURCE-JOIN.json','admission-retained/observe-current-retained-units.py'):
 record('unchanged_'+name,lambda name=name:eq((B/name).read_bytes(),(old/name).read_bytes()))
def assignment(path,key):
 n=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==key for t in n.targets));return ast.literal_eval(n.value)
record('builder_default4_immutable',lambda:eq(assignment(B/'publication/build-layer-publication-request.py','LAYER_NAMES'),assignment(B/'publication/friday_v3_layer_publication.py','HISTORICAL_LAYER_NAMES')))
record('builder_default4_not_expanded',lambda:eq(len(assignment(B/'publication/build-layer-publication-request.py','LAYER_NAMES')),4))
def definitions(path):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)}
r2=definitions(Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112/candidate/run_native205_once.py'));current=definitions(B/'run_native205_once.py')
for name in ('observe_owned_publisher','publisher_terminal_proven','bind_owned_publisher','close_owned_publisher'):
 if name in r2:record('unchanged_R2_'+name,lambda name=name:eq(current[name],r2[name]))
record('all_R2_actor_function_ASTs_exact',lambda:eq(current,r2))
# Recovery strict terminal binding is exercised as an extracted pure function.
recovery_ast=ast.parse((B/'resume_native205_services.py').read_bytes());term=next(n for n in recovery_ast.body if isinstance(n,ast.FunctionDef)and n.name=='publisher_terminal_proven')
def terminal(*,bound=True,invocation='',load='loaded',ceased=True,empty=True):
 journal=dict(publisher_invocation_id='a'*32,publisher_cgroup='/user.slice/owned',publisher_process_identity=dict(pid=1,birth_ticks=2),publisher_owned_description='owned')if bound else {}
 ns=dict(j=journal,PUB='owned.service',closed=lambda *a,**k:dict(LoadState=load,Description='owned',InvocationID=invocation),publisher_cgroup_empty=lambda:empty,publisher_process_closed=lambda:ceased)
 exec(compile(ast.Module(body=[term],type_ignores=[]),'<recovery-extracted-terminal>','exec'),ns);return ns['publisher_terminal_proven'](deadline=11)
record('recovery_collected_emptyID_accepts_prior_binding_and_cessation',terminal)
record('recovery_notfound_accepts_prior_binding_and_cessation',lambda:terminal(load='not-found'))
for key in ('bound','ceased','empty'):
 record('recovery_terminal_refuses_'+key,lambda key=key:rejects(lambda:terminal(**{key:False})))
record('recovery_terminal_refuses_foreign_invocation',lambda:rejects(lambda:terminal(invocation='b'*32)))
# Anchor validation cannot promote an expectation/template or historical proof.
anchor=json.loads((B/'ROOT-205-CURRENT-SERVICE-ANCHOR-TEMPLATE.json').read_bytes());anchor.pop('required_state_after_actual_Root_readback');anchor.update(state='ROOT_ACTUAL_CURRENT204_BOUNDARY',template_only_no_execution_grant=False,observed_at_moscow=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id='b'*36,historical_refs={'/historic/proof':'a'*64},evidence=[ref('fresh-current')],checks={k:True for k in anchor['checks']},services={name:dict(pid=17+i,birth_ticks=23+i,boot_id='b'*36,invocation_id='a'*32,cgroup='/user.slice/current',enabled_active=True,runtime_max='infinity')for i,name in enumerate(('gateway','dashboard'))},process_environment={name:dict(HERMES_HOME=anchor['home'])for name in ('gateway','dashboard')})
def anch(v):return c.validate_anchor(v,current_time=time.time(),boot='b'*36,historical={'/historic/proof':'a'*64},frame=str(B),publisher='frw-astra-native205-install-after204-20261112.service',home=anchor['home'])
record('fresh_complete_current204_anchor',lambda:anch(anchor))
for key,val in [('template_only_no_execution_grant',True),('state','EXPECTED204'),('boot_id','c'*36),('observed_at_moscow','2000-01-01T00:00:00+00:00'),('evidence',[dict(path='/historic/proof',sha256='a'*64)])]:
 a=copy.deepcopy(anchor);a[key]=val;record('anchor_reject_'+key,lambda a=a:rejects(lambda:anch(a)))
for name in ('gateway','dashboard'):
 a=copy.deepcopy(anchor);a['services'][name]['runtime_max']='180s';record('anchor_reject_timer_'+name,lambda a=a:rejects(lambda:anch(a)))
# Changed source consumer ordering: expensive bank work must finish before the
# final current global collection; binding cannot age that observation into launch.
caller_ast=ast.parse((B/'core205-first-actual-root.py').read_bytes());bd=next(n for n in caller_ast.body if isinstance(n,ast.FunctionDef)and n.name=='boundary');main_ast=next(n for n in caller_ast.body if isinstance(n,ast.FunctionDef)and n.name=='main')
calllines=lambda root,needle:[n.lineno for n in ast.walk(root)if isinstance(n,ast.Call)and ast.unparse(n.func)==needle]
record('global_refresh_after_bankmetadata',lambda:eq(max(calllines(bd,'c.bank_snapshot'))<min(calllines(bd,'transport.fresh_native')),True))
record('global_refresh_after_resources',lambda:eq(max(calllines(bd,'os.statvfs'))<min(calllines(bd,'transport.fresh_native')),True))
record('all3DB_refresh_after_bankmetadata',lambda:eq(max(calllines(bd,'c.bank_snapshot'))<min(calllines(bd,'readonly_databases')),True))
record('global_age_guard_after_binding_before_launch',lambda:eq(max(calllines(main_ast,'m.load_actor_binding'))<max(calllines(main_ast,'contract.validate_global_quiescence'))<min(calllines(main_ast,'launch_once')),True))
record('simulated_bank_or_binding_delay_refuses_stale_global',lambda:rejects(lambda:quiet(now=101)))
if (B/'SOURCE-PINS.json').exists():
 freeze=pure('prepare_source');frozen=hashlib.sha256((B/'SOURCE-PINS.json').read_bytes()).hexdigest()
 record('closest_frozen_source_codehash_consumer',lambda:freeze.validate(frozen))
 record('closest_frozen_source_wrong_external_digest_refused',lambda:rejects(lambda:freeze.validate('0'*64)))
for p in B.rglob('*.py'):record('syntax_'+str(p.relative_to(B)),lambda p=p:ast.parse(p.read_bytes(),str(p)))
assert not any((B/n).exists()for n in ('ROOT-FRESH-REQUEST.json','ROOT-ACTUAL204-PREDECESSOR.json','ROOT-205-RUNTIME-AUTHORITY.json','ROOT-205-SOURCE-ACCEPTANCE.json','ROOT-NATIVE205-LIVE-OPERATION.json','FUTURE-EXECUTION'))
result=dict(schema='frw.root205.pure-changed-scope-controls.v1',state='PASS_SOURCE_ONLY_NO_RUNTIME_GRANT',checks=len(rows),rows=rows,elapsed_seconds=time.monotonic()-START,budgets=dict(wall=90,cpu=60,memory=512*1024**2,cpus=2),effects=dict(actor_builder_collector_imports=0,requests_created=0,runtime_observations=0,network=0,model_Office_Telegram_DB_effects=0))
(B/'SOURCE-CONTROLS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
