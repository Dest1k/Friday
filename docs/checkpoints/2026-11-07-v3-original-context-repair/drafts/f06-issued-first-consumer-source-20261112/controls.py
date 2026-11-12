"""Bounded source controls; synthetic I/O only, never actual authority/scenario/state."""
import ast,copy,datetime,hashlib,json,math,os,signal,subprocess,time,types
from pathlib import Path
W=Path(__file__).resolve().parent
U=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY207-ROOT-BINDING-SOURCE-20261112')
os.umask(0o077)
def mod(name):
 m=types.ModuleType(name);m.__file__=str(W/name);exec(compile((W/name).read_bytes(),m.__file__,'exec'),m.__dict__);return m
a=mod('f06_source.py');d=mod('root_bind_existing_consumer_once.py');g=mod('current207.py')
results=[]
def record(name,f,refuse=False):
 start=time.monotonic()
 try:
  f()
 except (ValueError,OSError,RuntimeError) as e:
  assert refuse,(name,type(e).__name__,str(e));out='REFUSED';reason=str(e)
 else:
  assert not refuse,(name,'UNEXPECTED_ACCEPT');out='PASS';reason=None
 assert time.monotonic()-start<3,(name,'CONTROL_BUDGET_EXCEEDED')
 results.append({'name':name,'outcome':out,'reason':reason})
def pin(path,raw):return {'path':str(path),'bytes':len(raw),'sha256':a.digest(raw)}
# Actual source derive_identity, extracted without importing/invoking issuer.main.
issuer=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py')
raw=issuer.read_bytes();assert a.digest(raw)=='ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518'
tree=ast.parse(raw);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='derive_identity')
ns={'Path':Path,'json':json,'time':time};exec(compile(ast.Module(body=[node],type_ignores=[]),str(issuer),'exec'),ns)
chain_dir=W/'synthetic-released-chain';chain_dir.mkdir(mode=0o700,exist_ok=True)
parent={'schema':'frw.Root.ordinary-independent-history-admission.v1','accepted':True,'authority_id':'ordinary-f04-postfix-diagnostic-20261111-r105'}
parentraw=a.encoded(parent);parentpath=chain_dir/'INDEPENDENT-AUTHORITY-R105.json';parentpath.write_bytes(parentraw);parentpath.chmod(0o600)
authid,authfile,pred=ns['derive_identity'](chain_dir)
assert authid=='ordinary-f04-postfix-diagnostic-20261112-r106' and authfile=='INDEPENDENT-AUTHORITY-R106.json' and pred==parent['authority_id']
record('actual_issuer_derive_identity_synthetic_highest_released_R105',lambda:None)
# Pure synthetic scenario with the actual input metadata shape, no real credential read.
s=a.construct_scenario(supplied_password='synthetic-control-only',input_pin={'path':a.SOURCE['path'],'sha256':a.SOURCE['sha256'],'stat':{'size_bytes':a.SOURCE['bytes']},'filename':'f06-new-encrypted.docx','mime_type':a.MIME,'kind':'document'})
now=1794457500.0;created=d.EXISTING_CREATED;expires=d.EXISTING_EXPIRES
scenario_raw=a.encoded(s);scenario_ref=pin(W/'synthetic-scenario.json',scenario_raw)
auth={'schema':'frw.Root.ordinary-independent-history-admission.v1','operator':'Root','accepted':True,'authority_id':authid,'scope':a.scope(),'run_scenarios':{d.ORIGINAL_RUN:a.digest(scenario_raw)},'same_canonical_local_run':False,'created_at':created,'expires_at':expires,'supersedes':{'authority_id':pred,'reason':'Synthetic derive_identity chain join'}}
authraw=a.encoded(auth);authref=pin(W/'synthetic-R106.json',authraw)
files={scenario_ref['path']:scenario_raw,authref['path']:authraw,str(parentpath):parentraw}
def read(p,**kw):return files[str(p)]
ref0=pin(W/'synthetic-proof.json',b'{}\n');files[ref0['path']]=b'{}\n'
c=a.unbound();c.update(status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',run_id=d.ORIGINAL_RUN,scenario_ref=scenario_ref,scenario_sha256=a.digest(scenario_raw),authority=authref,authority_id=authid,authority_chain={'predecessor':pin(parentpath,parentraw),'predecessor_authority_id':pred,'created_at':created,'expires_at':expires},adapter=ref0,footer=ref0,actual_root_B_checker=ref0,root_current_proof=ref0,root_proofs={k:ref0 for k in a.PROOFS},product=dict(g.EXPECTED),boundary={**{k:'a'*64 for k in a.BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}},'gateway':{'pid':1,'start_time':1,'boot_id':'synthetic'},'B':{'profile':'telegram-bot-8812646969','session_id':g.SID,'session_key':g.KEY,'native_max_id':5510},'phase_unconsumed':True,'uploads_this_operation':1,'producer_calls':0,'restarts':0},resources={**a.TIMING,'cpu_seconds':360,'max_rss_bytes':1024**3,'disk_bytes':64*1024**2,'clock':ref0,'owned_parent_wait_cleanup':ref0})
record('actual_format_opaque_id_contract_shape',lambda:a.contract_shape(c))
record('actual_format_opaque_id_exact_ref_scope_run_hash_chain_admission',lambda:a.admission(c,auth,read=read,now=now))
record('synthetic_scenario_contract_join',lambda:a.shape(c,d.ORIGINAL_RUN,s,read))
def changed_contract(k,v):
 x=copy.deepcopy(c);x[k]=v;return x
record('wrong_identity',lambda:a.admission(changed_contract('authority_id','ordinary-independent-mislabel'),auth,read=read,now=now),True)
for key,val in [('path',str(W/'wrong-authority.json')),('sha256','f'*64),('bytes',authref['bytes']+1)]:
 bad=dict(authref,**{key:val})
 def test(bad=bad):
  x=changed_contract('authority',bad)
  def bounded_read(p,**kw):return authraw if str(p)==bad['path'] else read(p,**kw)
  # Wrongpath is a different binding, adapter alone accepts an explicitly pinned ref;
  # fixed-existing-R106 caller refuses it independently below.
  if bad['path']!=authref['path']:
   y=copy.deepcopy(driver_inputs);y['contract']['authority']=bad;d.validate_inputs(y)
  else:a.admission(x,auth,read=bounded_read,now=now)
 if key!='path':record('wrong_authority_ref_'+key,test,True)
for name,k,v in [('scope','scope','wrong scope'),('run','run_scenarios',{'wrong-run':c['scenario_sha256']}),('scenario','run_scenarios',{c['run_id']:'a'*64}),('ordered_predecessor','ordered_predecessors',{c['run_id']:{}}),('same_local','same_canonical_local_run',True),('accepted','accepted',False),('supersedes','supersedes',{'authority_id':'unrelated-r105','reason':'x'})]:
 bad=copy.deepcopy(auth);bad[k]=v;badraw=a.encoded(bad);x=changed_contract('authority',pin(authref['path'],badraw))
 record('wrong_'+name,lambda x=x,bad=bad,badraw=badraw:a.admission(x,bad,read=lambda p:badraw if str(p)==authref['path'] else read(p),now=now),True)
record('expired_existing_authority',lambda:a.admission(c,auth,read=read,now=expires),True)
record('preissued_authority_not_yet_created',lambda:a.admission(c,auth,read=read,now=created-1),True)
x=copy.deepcopy(c);x['authority_chain']['expires_at']=expires+1
record('extended_existing_authority',lambda:a.admission(x,auth,read=read,now=now),True)
x=copy.deepcopy(c);x['authority_chain']['predecessor_authority_id']='wrong-parent'
record('wrong_predecessor_chain',lambda:a.admission(x,auth,read=read,now=now),True)
# Full v42 method AST and successor preserve original API/capture/custody; only
# its intended literal ID seam and freshness callsite change in that method.
base=a.BASE.read_bytes();assert a.digest(base)==a.BASE_SHA
footer=(W/'f06_footer.py.txt').read_bytes();unbound=a.unbound();unbound['run_id']=d.ORIGINAL_RUN;unbound['scenario_sha256']=c['scenario_sha256'];unbound['authority']=authref;unbound['authority_id']=authid
built=a.successor(base,unbound,footer);before=ast.parse(base);after=ast.parse(built)
def runner(t):return next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
methods0={n.name:n for n in runner(before).body if isinstance(n,ast.FunctionDef)};methods1={n.name:n for n in runner(after).body if isinstance(n,ast.FunctionDef)}
changed=[k for k in methods0 if ast.dump(methods0[k],include_attributes=False)!=ast.dump(methods1[k],include_attributes=False)]
assert len(methods0)==len(methods1)==191 and changed==['ordinary_independent_admission']
record('fullv42_191_methods_190_unchanged',lambda:None)
# Execute the actual modified fullv42 admission method on a synthetic in-memory
# gateway/history with fake proc metadata, avoiding API/client/store construction.
method=methods1['ordinary_independent_admission']
class Refused(ValueError):pass
class FakePath:
 def __init__(self,p):self.p=str(p)
 def __truediv__(self,x):return FakePath(self.p+'/'+str(x))
 def __str__(self):return self.p
 def stat(self):return types.SimpleNamespace(st_dev=1,st_ino=2,st_mode=0o100600,st_nlink=1,st_uid=os.getuid(),st_gid=os.getgid(),st_size=1,st_mtime_ns=1,st_ctime_ns=1)
 def exists(self):return True
 def read_text(self):return 'synthetic-boot' if self.p.endswith('boot_id') else ' '.join(['1']*21+['123'])
state={'pid':99,'start_time':123,'gateway_state':'running','active_agents':0,'active_work':None,'restart_requested':False,'session_store':{'status':'ok'},'updated_at':datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),'platforms':{'telegram':{'state':'connected','needs_attention':False,'writer_pid':99,'writer_start_time':123}}}
fullauth=copy.deepcopy(auth);fullauth.update(boot_id='synthetic-boot',new_independent_inputs_only=True,no_old_task_replay=True,old_rows_modified=False,unknown_effects_resolved=False,product_or_B00_acceptance=False,new_trial_for_historical_task=False,history={str(i):{} for i in range(40)},gateway={'pid':99,'start_time':123,'state_path':'/synthetic/gateway.json','maximum_staleness_seconds':600})
fullraw=a.encoded(fullauth);fullref=pin(W/'synthetic-full-R106.json',fullraw)
fakens={'Path':FakePath,'safe_read':lambda p,**kw:fullraw if str(p)==fullref['path'] else a.encoded(state),'json':json,'unique_object':d.unique,'encoded':a.encoded,'digest':a.digest,'os':os,'stat':__import__('stat'),'dt':datetime,'Refused':Refused,'no_symlinks':lambda p:p,'_f06_current':lambda *args:True}
exec(compile(ast.Module(body=[method],type_ignores=[]),'<actual-full-v42-admission>','exec'),fakens)
fake=types.SimpleNamespace(ORDINARY_INDEPENDENT_SCENARIOS={c['run_id']:c['scenario_sha256']},ORDINARY_INDEPENDENT_AUTHORITY=fullref,clock=lambda:now,store=types.SimpleNamespace(get=lambda p:{},run_path=lambda n:n),ordinary_independent_history_row=lambda d,p:True)
record('actual_issuer_identity_to_actual_adapted_fullv42_admission',lambda:fakens['ordinary_independent_admission'](fake,c['run_id'],s))
# Actual permitted closure metadata joined to synthetic old once/clock refs.
closure=json.loads((W/'ROOT-PREBIRTH-CLOSURE.METADATA.json').read_bytes())
# We never manufacture hash preimages for actual old files. These readref seams
# stand for already separately pinned immutable inputs and are explicitly recorded.
rec={'schema':'frw.Root.F06.issuer-only-prebirth-reconciliation.v1','operator':'Root','status':'ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER','created_at':now-1,'expires_at':now+119,'prebirth_closure':d.PREBIRTH_CLOSURE,'original_run_id':d.ORIGINAL_RUN,'scenario_sha256':d.ORIGINAL_SCENARIO_SHA,'existing_authority':d.EXISTING_AUTHORITY,'old_once':closure['once_claim_preserved'],'old_clock':closure['original_clock']}
for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry'):rec[key]=True
recref=pin(W/'synthetic-reconciliation.json',a.encoded(rec))
driver_inputs={'schema':'frw.Root.F06.existing-R106-first-consumer.v1','status':'ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER','contract':copy.deepcopy(c),'source_freeze':ref0,'independent_review':ref0,'workdir':str(W/'synthetic-future-work'),'slot_identity':None,'expected_binding_sha256':None,'prebirth_closure':d.PREBIRTH_CLOSURE,'prebirth_reconciliation':recref}
driver_inputs['contract'].update(authority=d.EXISTING_AUTHORITY,authority_id=d.EXISTING_AUTHORITY_ID,scenario_sha256=d.ORIGINAL_SCENARIO_SHA,scenario_ref=dict(scenario_ref,sha256=d.ORIGINAL_SCENARIO_SHA))
record('fixed_original_run_existing_R106_input_binding',lambda:d.validate_inputs(driver_inputs))
for label,key,val in [('wrong_authority_path','authority',dict(d.EXISTING_AUTHORITY,path=str(W/'other-R106.json'))),('wrong_authority_hash','authority',dict(d.EXISTING_AUTHORITY,sha256='a'*64)),('replacement_run','run_id','replacement-r1'),('changed_scenario','scenario_sha256','a'*64),('reissue_id','authority_id','ordinary-independent-new-r107')]:
 v=copy.deepcopy(driver_inputs);v['contract'][key]=val
 record('caller_'+label,lambda v=v:d.validate_inputs(v),True)
# No actual old files are opened. Inject exact allowed source metadata and explicit
# immutable readref seams, plus synthetic lexical absence checks.
old_readref=d.readref;oldexists=d.Path.exists;oldlexists=d.os.path.lexists;oldtime=d.time.time
seam={'once_missing':False,'clock_changed':False,'present':None,'rec':rec}
def rr(r,**kw):
 if r==d.PREBIRTH_CLOSURE:return a.encoded(closure)
 if r==closure['once_claim_preserved']:
  if seam['once_missing']:raise FileNotFoundError('synthetic old once erased/renamed')
  return a.encoded({'schema':'frw.Root.F06.one-driver-invocation.v1','run_id':d.ORIGINAL_RUN,'no_retry':True})
 if r==closure['original_clock']:
  x=copy.deepcopy(closure['original_clock_endpoints_preserved'])
  if seam['clock_changed']:x['deadline_at']+=600
  return a.encoded(x)
 if r==recref:return a.encoded(seam['rec'])
 raise AssertionError(('unexpected synthetic ref',r))
d.readref=rr;d.Path.exists=lambda p:str(p)==seam['present'];d.os.path.lexists=lambda p:str(p)==seam['present'];d.time.time=lambda:now
try:
 record('prebirth_source_predicate_synthetic_explicit_readref_seams',lambda:d.prebirth_reconciled(driver_inputs))
 for name in ('ROOT-ACTUAL-BINDING.json','bot_tester.f06.root-bound.py','ROOT-DISPATCH-INVOCATION.json','ROOT-CONSUMER-ACTOR.json','ROOT-STOP-UNCONFIRMED.json','ROOT-DISPATCH-ENDED.json','CONSUMER.stdout','CONSUMER.stderr'):
  seam['present']=str(d.ORIGINAL_DIR/'work'/name)
  record('prior_stage_'+name,lambda:d.prebirth_reconciled(driver_inputs),True)
 seam['present']=str(d.STATE/'runs'/(d.ORIGINAL_RUN+'.json'));record('prior_canonical_run',lambda:d.prebirth_reconciled(driver_inputs),True)
 seam['present']='/proc/'+str(closure['actual_root_driver_pid']);record('old_driver_alive',lambda:d.prebirth_reconciled(driver_inputs),True)
 seam['present']=None;seam['once_missing']=True;record('old_once_erased_or_renamed',lambda:d.prebirth_reconciled(driver_inputs),True);seam['once_missing']=False
 seam['clock_changed']=True;record('old_clock_extended',lambda:d.prebirth_reconciled(driver_inputs),True);seam['clock_changed']=False
 v=copy.deepcopy(driver_inputs);v['contract']['resources']['clock']=closure['original_clock'];record('old_clock_reuse',lambda:d.prebirth_reconciled(v),True)
 seam['rec']=dict(rec,no_prior_bind_dispatch_canonicalrun_or_unknown=False);record('unknown_prior_effect',lambda:d.prebirth_reconciled(driver_inputs),True)
 seam['rec']=dict(rec,expires_at=now);record('stale_root_prebirth_reconciliation',lambda:d.prebirth_reconciled(driver_inputs),True)
finally:d.readref=old_readref;d.Path.exists=oldexists;d.os.path.lexists=oldlexists;d.time.time=oldtime
# Atomic exact-ref reader negative controls on synthetic bytes, no actual contents.
x=copy.deepcopy(c);x['authority']['sha256']='b'*64
record('actual_readref_hash_mismatch',lambda:a.admission(x,auth,read=read,now=now),True)
# Old R3 signal drain/birth/deadline/slot code reuse is AST-exact.
oldtree=ast.parse((U/'root_bind_dispatch_once.py').read_bytes());newtree=ast.parse((W/'root_bind_existing_consumer_once.py').read_bytes())
def fn(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
for name in ('owned_remaining','wait_owned'):
 assert ast.dump(fn(oldtree,name),include_attributes=False)==ast.dump(fn(newtree,name),include_attributes=False)
 record('R3_'+name+'_AST_exact',lambda:None)
def nested(t,n):return next(x for x in ast.walk(fn(t,'execute')) if isinstance(x,ast.FunctionDef) and x.name==n)
for name in ('child_limits','forward_stops','parent_stop'):
 assert ast.dump(nested(oldtree,name),include_attributes=False)==ast.dump(nested(newtree,name),include_attributes=False)
 record('R3_'+name+'_AST_exact',lambda:None)
# Reachable new caller contains no issuer import/call, authority directory scan,
# old driver reference executable, old once delete/rename or state-mutating helper.
source=(W/'root_bind_existing_consumer_once.py').read_text()
assert all(x not in source for x in ('issuer.main','derive_identity','ISSUER=','AUTHORITY_DIR.glob','unlink(','.rename(','.replace('))
assert all(not isinstance(n,ast.Name) or n.id not in {'issuer','ISSUER','AUTHORITY_DIR'} for n in ast.walk(newtree))
record('issuer_called_or_old_driver_rerun_statically_unreachable',lambda:None)
# Ensure actual new call order validates unstarted stage+existing authority before
# child birth, with at most one Popen syntax call and no auto-dispatch on import.
assert sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='Popen' for x in ast.walk(newtree))==1
record('exactly_one_Popen_source_call_import_inert',lambda:None)
# Actual first-consumer source/binding serialization + reconstruction, in-memory.
# This exercises the real AST statement after removing the issuer branch; no
# undefined legacy local can be hidden by a simplified hand-written JSON fixture.
work=W/'synthetic-memory-work';bound=work/'bot_tester.f06.root-bound.py'
raw_c=copy.deepcopy(c);raw_c['footer']=pin(W/'f06_footer.py.txt',footer)
canonical_c_stmt=next(n for n in fn(newtree,'execute').body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='c' for t in n.targets))
canonical_c_ns={'v':{'contract':raw_c},'json':json,'encoded':d.encoded,'unique':d.unique}
exec(compile(ast.Module(body=[canonical_c_stmt],type_ignores=[]),'<actual-first-consumer-initial-canonical-contract>','exec'),canonical_c_ns)
bind_c=canonical_c_ns['c']
boundraw=a.successor(base,bind_c,footer);memory={str(bound):boundraw}
binding_stmt=next(n for n in ast.walk(fn(newtree,'execute')) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='new' and isinstance(n.value.args[0],ast.BinOp) and isinstance(n.value.args[0].right,ast.Constant) and n.value.args[0].right.value=='ROOT-ACTUAL-BINDING.json')
def memnew(p,raw):
 assert str(p) not in memory;memory[str(p)]=raw
serialize_ns={'work':work,'bound':bound,'c':bind_c,'a':a,'v':driver_inputs,'new':memnew,'encoded':d.encoded,'ref':lambda p:pin(p,memory[str(p)])}
def serialize_actual_binding():
 exec(compile(ast.Module(body=[binding_stmt],type_ignores=[]),'<actual-first-consumer-binding-statement>','exec'),serialize_ns)
 saved=json.loads(memory[str(work/'ROOT-ACTUAL-BINDING.json')])
 assert saved['authority']==bind_c['authority'] and saved['contract']==bind_c
 assert saved['source']==pin(bound,boundraw) and saved['whole_effect_sha256']==a.digest(a.encoded(a.effect(bind_c)))
 assert a.successor(base,saved['contract'],footer)==boundraw
record('actual_binding_record_serialization_and_real_successor_reconstruction',serialize_actual_binding)
# Source-level reproduction of the independent review's original undefined-local
# observation, with the same real statement and no issuer local in its namespace.
legacy=copy.deepcopy(binding_stmt)
class LegacyAuthority(ast.NodeTransformer):
 def visit_Subscript(self,n):
  if isinstance(n.value,ast.Name) and n.value.id=='c' and isinstance(n.slice,ast.Constant) and n.slice.value=='authority':
   return ast.copy_location(ast.Name(id='authority',ctx=ast.Load()),n)
  return self.generic_visit(n)
legacy=ast.fix_missing_locations(LegacyAuthority().visit(legacy))
try:exec(compile(ast.Module(body=[legacy],type_ignores=[]),'<original-removed-issuer-local-regression>','exec'),dict(serialize_ns))
except NameError as exc:assert exc.name=='authority'
else:raise AssertionError('old binding expression unexpectedly had authority local')
record('regression_old_binding_undefined_issuer_authority_local_detected',lambda:None)
# Positive and negative separate-segment clock controls. Host clocks are replaced
# only in this synthetic module process; no execution clock is written.
oldwall=d.time.time;oldmono=d.time.monotonic;oldpath=d.Path
baseclock={'schema':'frw.Root.F06.unstarted-consumer-finite-clock.v1','started_at':now-10,'deadline_at':now+590,'started_monotonic':90.0,'deadline_monotonic':690.0,'boot_id':'synthetic-clock-boot'}
d.time.time=lambda:now;d.time.monotonic=lambda:100.0;d.Path=lambda p:types.SimpleNamespace(read_text=lambda:'synthetic-clock-boot')
try:
 record('separate_future600_clock_valid',lambda:d.clock_remaining(baseclock))
 for label,changes in [('old600_schema',{'schema':'frw.Root.F06.original-finite-clock.v1'}),('extended_outer',{'deadline_at':now+591}),('expired',{'deadline_at':now}),('wrongboot',{'boot_id':'wrong-boot'}),('futurestart',{'started_at':now+1}),('monotonic_extended',{'deadline_monotonic':691.0})]:
  clock=dict(baseclock,**changes)
  record('consumer_clock_'+label,lambda clock=clock:d.clock_remaining(clock),True)
finally:d.time.time=oldwall;d.time.monotonic=oldmono;d.Path=oldpath
v=copy.deepcopy(driver_inputs);v['issuer_called']=True
record('issuer_called_input_forbidden',lambda:d.validate_inputs(v),True)
# Source template must fail before any load, read, slot or process effect.
d.load=lambda *args,**kw:(_ for _ in ()).throw(AssertionError('UNBOUND attempted load'))
record('UNBOUND_execute_refuses_before_io_or_issuer_or_consumer',lambda:d.execute(json.loads((W/'ROOT-CONSUMER-INPUTS.UNBOUND.json').read_bytes()),binding_ref=ref0),True)
# Inert successor must refuse default CLI prior to Store/token/Api construction.
assert "_f06_adapter().contract_shape(F06_CONTRACT)" in footer.decode()
record('UNBOUND_full_consumer_footer_gate_static',lambda:None)
report={'schema':'frw.F06.existing-R106-first-consumer.source-controls.v1','status':'PASS_SOURCE_ONLY_SYNTHETIC_NO_LIVE_ADMISSION','controls':results,'control_count':len(results),'issuer_source_sha256':a.digest(raw),'issuer_execution':'Only actual derive_identity AST on isolated synthetic minimal released R105; issuer.main never imported or invoked','fullv42_total_unique_Runner_methods':191,'fullv42_unchanged_methods':190,'fullv42_changed_methods':changed,'limits':['No actual authority, credential/scenario body, token, DB/state, installed tester or installed product read','Prebirth predicate used explicit synthetic readref/absence seams; not actual Root reconciliation','Fullv42 admission method used synthetic proc/gateway/store/history/current checker seams; not live API/custody/window acceptance','Existing R3 historical exact-scope signal/birth/deadline controls retained by AST equality, no new live gate']}
(W/'CONTROLS.json').write_bytes(a.encoded(report));(W/'CONTROLS.json').chmod(0o600)
# Remove synthetic private data once observations are retained; no live evidence.
parentpath.unlink();chain_dir.rmdir()
print(json.dumps({'status':report['status'],'control_count':len(results)}))
