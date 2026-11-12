"""Bounded source checks; temporary CP journals are synthetic, never actual installed authority.
Historical root reconstruction and final native admission are explicit seams.
"""
from pathlib import Path
import ast,copy,difflib,hashlib,importlib.util,json,os,resource,signal,sys,tempfile,time,types
sys.dont_write_bytecode=True;os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);signal.alarm(90)
B=Path(__file__).resolve().parent;started=time.monotonic();checks=[]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def check(name,result):
 assert result,name;checks.append(name)
def refused(name,call,expected=None):
 try:call()
 except (ValueError,OSError) as e:check(name,expected is None or expected in str(e));return
 raise AssertionError(name+' accepted')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(data if isinstance(data,bytes) else enc(data));p.chmod(0o600)
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def astmap(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
S=json.loads((B/'SOURCES.json').read_bytes())
O=load(Path(S['public']['candidate']),'ninth_public');OP=load(Path(S['private']['candidate']),'ninth_private')
P=B.parent/'FINAL-NATIVE-SPEC.json';pins=json.loads(P.read_bytes())
PAIR=B.parent/'pair/patches/hermes';mn=O.CURRENT_SOURCE_NINTH_LAYER+'-manifest.json';pn=O.CURRENT_SOURCE_NINTH_LAYER+'.patch'
manifest=json.loads((PAIR/mn).read_bytes())
check('exact_frozen_manifest_pin',sha((PAIR/mn).read_bytes())==O.CURRENT_SOURCE_NINTH_MANIFEST==OP.CURRENT_SOURCE_NINTH_MANIFEST)
check('exact_frozen_patch_pin',sha((PAIR/pn).read_bytes())==O.CURRENT_SOURCE_NINTH_PATCH==OP.CURRENT_SOURCE_NINTH_PATCH)
check('exact_11_native_pins',O.CURRENT_SOURCE_NINTH_NATIVE==OP.CURRENT_SOURCE_NINTH_NATIVE=={r['path']:(r['before_sha256'],r['sha256'],r['bytes'],False) for r in pins['native_files']}=={r['path']:(r['before_sha256'],r['sha256'],r['bytes'],r['new_file']) for r in manifest['files']} and len(O.CURRENT_SOURCE_NINTH_NATIVE)==1)
check('all_11_existing_and_no_additions',all(r[3] is False for r in O.CURRENT_SOURCE_NINTH_NATIVE.values()))
for variant,row in S.items():
 check(variant+'_baseline_and_candidate_hashes',sha(Path(row['source']).read_bytes())==row['source_sha256'] and sha(Path(row['candidate']).read_bytes())==row['sha256'])
 old,new=astmap(Path(row['source'])),astmap(Path(row['candidate']))
 changed={n for n in old if old[n]!=new[n]}
 check(variant+'_only_required_three_old_ASTs_changed',changed=={'_current_source_eighth_successor_checked','current_native_source_successor_checked','_current_native_source_edge_checked'})
 check(variant+'_only_two_new_function_class_ASTs',set(new)-set(old)=={'_CurrentSourceNinthHistory','_current_source_ninth_successor_checked'})
 check(variant+'_project_current_consumer_AST_unchanged',old['project_current_source_checked']==new['project_current_source_checked'])
 # Exact unchanged source tail from current metadata selection through native gateway check.
 a=Path(row['source']).read_text();b=Path(row['candidate']).read_text();start="    marker = historical_marker if historical_marker is not None else _current_source_json(home/f.MARKER)\n    leaf = marker.get('input_sha256')"
 # Earlier new v8 checks alter this tail, so compare the precise R1 marker block onwards.
 markerstart='    if leaf:\n        expected_marker = json.loads(json.dumps(before_marker))'
 check(variant+'_exact_R1_marker_config_native_admission_block',a[a.index(markerstart):a.index('\ndef project_current_source_checked')]==b[b.index(markerstart):b.index('\ndef project_current_source_checked')])
def differences(a,b):return [line for line in difflib.ndiff(a.splitlines(True),b.splitlines(True)) if line.startswith(('- ','+ '))]
check('exact_private_public_ndiff_preserved',differences(Path(S['public']['source']).read_text(),Path(S['private']['source']).read_text())==differences(Path(S['public']['candidate']).read_text(),Path(S['private']['candidate']).read_text()))
class UnitAPI:
 MARKER='FRIDAY-INSTALL.json'
 def require(self,value,message):
  if not value:raise ValueError(message)
 def canonical(self,p):return Path(p).resolve()
 def directory(self,p):return Path(p)
 def digest(self,data):return sha(data)
 def owned_file(self,p,**kwargs):return Path(p).read_bytes()
 def read_json(self,p):return json.loads(self.owned_file(p))
 def unique(self,pairs):
  result={}
  for k,v in pairs:self.require(k not in result,'duplicate');result[k]=v
  return result
 def pin(self,r):
  self.require(type(r) is dict and set(r)=={'path','sha256'} and sha(Path(r['path']).read_bytes())==r['sha256'],'bad unit ref');return Path(r['path'])
f=UnitAPI();O.api=lambda:f
original_edge=O._current_native_source_edge_checked;original_eighth=O._current_source_eighth_successor_checked;original_seventh=O._current_source_seventh_successor_checked
with tempfile.TemporaryDirectory(prefix='synthetic-fixed-v8-',dir=B) as td:
 T=Path(td);H=T/'home';H.mkdir(mode=0o700);(H/'preparation').mkdir(mode=0o700)
 inputs={n:T/(str(n)+'.json') for n in (204,205,206,207)}
 for n,p in inputs.items():write(p,{'home':str(H),'source':n})
 root={'path':str(T/'root.json'),'sha256':'a'*64};root203={'path':str(T/'cp203.json'),'sha256':'b'*64}
 def make_request(n,previous_ref,context):
  r={k:None for k in O.CURRENT_SOURCE_CP_FIELDS};r.update(schema='friday.ordinary-telegram-source-update.v46',seconds=120,home=str(H),previous_input=previous_ref,current_input=ref(inputs[n]),current_source_successor=context,predecessor_request={'path':str(T/'152.json'),'sha256':'c'*64},predecessor_receipt_sha256='d'*64,plugin_set=[],plugin_additions=[],project_file_updates=[])
  before={name:enc({'synthetic':name,'input_sha256':previous_ref['sha256']}) for name in ('hermes-agent.source.json',f.MARKER,'hermes-agent/install-stamp.json')}
  for key,name in {'source_receipt':'hermes-agent.source.json','marker':f.MARKER,'stamp':'hermes-agent/install-stamp.json'}.items():r[key]={'path':str(H/name),'sha256':sha(before[name])}
  raw=enc(r);tx=H/'preparation'/('ordinary-source-update-v45-'+sha(raw)[:16]);write(tx/'request.json',raw)
  for name,data in before.items():write(tx/'before'/name,data)
  common=dict(schema='friday.ordinary-telegram-source-update-transaction.v1',request_sha256=sha(raw),request_reference=ref(tx/'request.json'),current_source_successor=context,previous_input=previous_ref,current_input=r['current_input'],gateway_started=False,workers_enabled=False)
  intent={k:None for k in O.CURRENT_SOURCE_CP_INTENT_FIELDS};intent.update(common,state='SOURCE_UPDATE_INTENT',home=str(H),source_receipt=r['source_receipt'],plugin_set=[],plugin_additions=[],project_file_updates=[],metadata=['hermes-agent.source.json',f.MARKER,'hermes-agent/install-stamp.json'])
  commit={k:None for k in O.CURRENT_SOURCE_CP_COMMIT_FIELDS};commit.update(common,state='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED',seconds=1,predecessor_request_sha256=r['predecessor_request']['sha256'],predecessor_receipt_sha256=r['predecessor_receipt_sha256'])
  write(tx/'intent.json',intent);write(tx/'committed.json',commit)
  return r,tx
 r204,tx204=make_request(205,ref(inputs[204]),{'schema':O.CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA,'root_project_update':root,'previous_native_update':root203})
 r205,tx205=make_request(206,ref(inputs[205]),{'schema':O.CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA,'root_project_update':root,'previous_native_update':ref(tx204/'request.json')})
 r206={**copy.deepcopy(r205),'previous_input':ref(inputs[206]),'current_input':ref(inputs[207]),'current_source_successor':{'schema':O.CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,'root_project_update':root,'previous_native_update':ref(tx205/'request.json')}}
 marker205={'input_sha256':ref(inputs[206])['sha256']};write(H/f.MARKER,marker205)
 prior={'request':r205,'value':json.loads(inputs[206].read_bytes())}
 observed=[]
 def eighth_seam(value,request,**kw):
  h=kw['_ninth_history'];observed.append(kw)
  check('ninth_mints_sealed_CP206_proof',type(h) is O._CurrentSourceNinthHistory and h._seal is O._CURRENT_SOURCE_NINTH_HISTORY_SEAL and h.eighth_reference==O.encoded(ref(tx205/'request.json')) and kw['historical_marker']==marker205)
  return prior
 O._current_source_eighth_successor_checked=eighth_seam;O._current_native_source_edge_checked=lambda value,**kwargs:('selected',kwargs)
 got=O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),r206,cli_only=True,source_update=r206)
 check('fixed_ninth_selects_committed_canonical_CP206',got[0]=='selected' and got[1]['prior_edge']==prior)
 for name,mutate in [('wrong_root',lambda r:r['current_source_successor'].update(root_project_update={'path':root['path'],'sha256':'e'*64})),('wrong_before',lambda r:r.update(previous_input=ref(inputs[204]))),('v9',lambda r:r['current_source_successor'].update(schema='friday.current-source-native-successor.v10'))]:
  bad=copy.deepcopy(r206);mutate(bad);refused('fixed_ninth_refuses_'+name,lambda:O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),bad,cli_only=True,source_update=bad))
 duplicate=T/'noncanonical205.json';write(duplicate,enc(r205));bad=copy.deepcopy(r206);bad['current_source_successor']['previous_native_update']=ref(duplicate)
 refused('fixed_ninth_refuses_noncanonical_CP206_copy',lambda:O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),bad,cli_only=True,source_update=bad),'eighth_canonical_request_required')
 commitraw=(tx205/'committed.json').read_bytes();(tx205/'committed.json').unlink()
 refused('expected205_without_committed_CP206_refused',lambda:O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),r206,cli_only=True,source_update=r206));write(tx205/'committed.json',commitraw)
 write(tx205/'rolled-back.json',{});refused('rolledback_CP206_refused',lambda:O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),r206,cli_only=True,source_update=r206),'rolled_back');(tx205/'rolled-back.json').unlink()
 commit=json.loads(commitraw);commit['gateway_started']=True;write(tx205/'committed.json',commit)
 refused('CP206_committed_binding_tamper_refused',lambda:O._current_source_ninth_successor_checked(json.loads(inputs[207].read_bytes()),r206,cli_only=True,source_update=r206),'journal_binding_changed');write(tx205/'committed.json',commitraw)
 tx206=H/'preparation'/('ordinary-source-update-v45-'+sha(enc(r206))[:16]);write(tx206/'request.json',r206);write(tx206/'before'/f.MARKER,marker205)
 write(H/f.MARKER,{'input_sha256':ref(inputs[207])['sha256'],'ordinary_gateway':{'operator_entry':{'input':ref(inputs[207])}}})
 root_tx=H/'preparation'/('ordinary-source-update-'+O.PROJECT_DSH_CURRENT_INPUT);write(root_tx/'intent.json',{'request_reference':root})
 O._project_current_root_checked=lambda *args:({}, {'home':str(H),'source':'root198'})
 got=O.current_native_source_successor_checked(json.loads(inputs[207].read_bytes()),cli_only=True)
 check('default_marker_dispatches_exact_v8',got[0]=='selected' and got[1]['source_update'] is None)
 bad=copy.deepcopy(r206);bad['current_source_successor']['schema']='friday.current-source-native-successor.v10'
 refused('default_dispatch_refuses_unknown_v9',lambda:O.current_native_source_successor_checked(json.loads(inputs[207].read_bytes()),cli_only=True,source_update=bad),'context_required')
 O._current_source_eighth_successor_checked=original_eighth;O._current_native_source_edge_checked=original_edge
 predecessor={'request':{'current_source_successor':{'schema':O.CURRENT_SOURCE_SEVENTH_SUCCESSOR_SCHEMA},'current_input':ref(inputs[205])}}
 def sealed():return O._CurrentSourceNinthHistory(ref(tx205/'request.json'),ref(tx204/'request.json'),root,ref(inputs[206]),r206['current_source_successor'],_seal=O._CURRENT_SOURCE_NINTH_HISTORY_SEAL)
 for name,r,h,p in [('v8_historical',r206,{},prior),('v8_without_v7',r206,None,None),('v8_after_v6',r206,None,predecessor),('v9',bad,None,prior),('unsealed_CP206',r205,{},predecessor)]:
  refused('actual_edge_refuses_'+name,lambda r=r,h=h,p=p:original_edge(json.loads(inputs[207].read_bytes()),cli_only=True,source_update=r,historical_marker=h,prior_edge=p),'context_required')
 refused('history_constructor_rejects_foreign_seal',lambda:O._CurrentSourceNinthHistory({}, {}, {}, {}, {},_seal=object()),'internal_ninth_history_required')
 class ReachedRoot(Exception):pass
 def root_boundary(*args):raise ReachedRoot()
 O._project_current_root_checked=root_boundary
 try:original_edge(json.loads(inputs[206].read_bytes()),cli_only=True,source_update=r205,historical_marker=marker205,prior_edge=predecessor,_ninth_history=sealed())
 except ReachedRoot:check('actual_sealed_historical_CP206_reaches_root198_boundary',True)
 else:raise AssertionError('root boundary not reached')
 for field in ('eighth_reference','seventh_reference','root_reference','selected_previous','selected_context'):
  proof=sealed();setattr(proof,field,b'changed')
  refused('actual_historical_CP206_refuses_changed_'+field,lambda:original_edge(json.loads(inputs[206].read_bytes()),cli_only=True,source_update=r205,historical_marker=marker205,prior_edge=predecessor,_ninth_history=proof),'authenticated_eighth_history_required')
 seen=[];prior6={'request':r204,'value':json.loads(inputs[205].read_bytes())}
 O._current_source_seventh_successor_checked=lambda value,request,**kw:seen.append(kw) or prior6
 O._current_native_source_edge_checked=lambda value,**kw:kw
 got=original_eighth(json.loads(inputs[206].read_bytes()),r205,cli_only=True,source_update=r205,historical_marker=marker205,_ninth_history=sealed())
 check('real_v7_wrapper_propagates_v8_seal',got['historical_marker']==marker205 and type(got['_ninth_history']) is O._CurrentSourceNinthHistory and got['prior_edge']==prior6)
 check('real_v7_restores_own_CP205_before_marker',seen[-1]['historical_marker']['input_sha256']==ref(inputs[205])['sha256'] and type(seen[-1]['_eighth_history']) is O._CurrentSourceEighthHistory)
 refused('real_v7_wrapper_refuses_foreign_history',lambda:original_eighth(json.loads(inputs[206].read_bytes()),r205,cli_only=True,source_update=r205,historical_marker=marker205,_ninth_history=object()),'internal_ninth_history_required')
 O._current_source_seventh_successor_checked=original_seventh;O._current_native_source_edge_checked=original_edge
# Real complete edge reaches the project pin boundary; root/history collaborators remain seams.
with tempfile.TemporaryDirectory(prefix='synthetic-v8-scope-',dir=B) as td:
 T=Path(td);H=T/'home';H.mkdir(mode=0o700);f.ROOT=T/'candidate'
 old={'scripts/friday_ordinary_install.py':'a'*64,'scripts/friday_install.py':'b'*64};old.update({'other/'+str(n):sha(str(n).encode()) for n in range(491)})
 files=dict(old);files['scripts/friday_ordinary_install.py']='c'*64
 manifest_name='patches/hermes/'+mn;patch_name='patches/hermes/'+pn
 files.update({manifest_name:O.CURRENT_SOURCE_NINTH_MANIFEST,patch_name:O.CURRENT_SOURCE_NINTH_PATCH})
 pi=T/'previous.json';ci=T/'current.json';anc=T/'ancestor.json';unit=T/'unit'
 before={'home':str(H),'project_files':old};after={'home':str(H),'project_files':files};write(pi,before);write(ci,after);write(unit,b'unit')
 for n in ('config.yaml','FRIDAY-PROFILE.json','hermes-agent/.hermes/bin/hermes','hermes-agent.source.json','hermes-agent/install-stamp.json'):write(H/n,b'fixture')
 write(H/f.MARKER,{'input_sha256':ref(pi)['sha256']})
 anchor={'predecessor_request':{'path':str(T/'152.json'),'sha256':'1'*64},'predecessor_current_input_sha256':'2'*64,'predecessor_receipt_sha256':'3'*64,'transaction_history':{}};write(anc,anchor)
 root={'current_input':{'path':str(T/'198.json'),'sha256':'4'*64},'publication_ancestor':{'request':ref(anc)},'native_unit':ref(unit)}
 O._project_current_root_checked=lambda *args:(root,{'home':str(H),'project_files':{}})
 request={k:None for k in O.CURRENT_SOURCE_CP_FIELDS};request.update(anchor,schema='friday.ordinary-telegram-source-update.v46',seconds=120,home=str(H),candidate_project=str(f.ROOT),previous_input=ref(pi),current_input=ref(ci),candidate_input=ref(ci),installed_layers=206,installed_files=17891,plugin_set=[],plugin_additions=[],staged_files=[],layer_names=[O.CURRENT_SOURCE_NINTH_LAYER],project_file_updates=['scripts/friday_ordinary_install.py'],layer_manifest_updates=[manifest_name],project_inventory=files,project_inventory_sha256=sha(enc(files)),current_source_successor={'schema':O.CURRENT_SOURCE_NINTH_SUCCESSOR_SCHEMA,'root_project_update':{'path':str(T/'root.json'),'sha256':'5'*64},'previous_native_update':{'path':str(T/'206.json'),'sha256':'6'*64}})
 for key,name in {'source_receipt':'hermes-agent.source.json','target_receipt':'hermes-agent.source.json','marker':f.MARKER,'stamp':'hermes-agent/install-stamp.json','configuration':'config.yaml','profile':'FRIDAY-PROFILE.json','launcher':'hermes-agent/.hermes/bin/hermes'}.items():request[key]=ref(H/name)
 request['native_unit']=ref(unit);prior={'request':{'current_input':ref(pi),'current_source_successor':{'schema':O.CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA}},'value':before,'receipt_sha256':request['source_receipt']['sha256'],'stamp_sha256':request['stamp']['sha256']}
 class ReachedInventory(Exception):pass
 real_owned=f.owned_file
 def boundary(p,**kw):
  if str(p).startswith(str(f.ROOT)+'/'):raise ReachedInventory()
  return real_owned(p,**kw)
 f.owned_file=boundary
 def run():return original_edge(after,cli_only=True,source_update=request,prior_edge=prior)
 try:run()
 except ReachedInventory:check('exact_v8_scope_reaches_project_pin_boundary',True)
 else:raise AssertionError('candidate pin boundary not reached')
 for key,value,message in [('installed_layers',204,'exact_native198_required'),('installed_files',17892,'exact_native198_required'),('layer_names',[O.CURRENT_SOURCE_EIGHTH_LAYER],'exact_ninth_layer_required')]:
  keep=request[key];request[key]=value;refused('real_edge_refuses_'+key,run,message);request[key]=keep
 files['scripts/friday_install.py']='d'*64;write(ci,after);request.update(current_input=ref(ci),candidate_input=ref(ci),project_file_updates=['scripts/friday_install.py','scripts/friday_ordinary_install.py'],project_inventory_sha256=sha(enc(files)))
 refused('real_v8_refuses_extra_friday_install_delta',run,'exact_ninth_helper_scope_required')
 files['scripts/friday_install.py']=old['scripts/friday_install.py'];files['scripts/friday_ordinary_install.py']=old['scripts/friday_ordinary_install.py'];write(ci,after);request.update(current_input=ref(ci),candidate_input=ref(ci),project_file_updates=[],project_inventory_sha256=sha(enc(files)))
 refused('real_v8_refuses_missing_ordinary_helper_delta',run,'exact_ninth_helper_scope_required');f.owned_file=real_owned
# Execute exact new native guard ASTs independently to reach every compiled image pin.
node=next(n for n in ast.parse(Path(S['public']['candidate']).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_current_native_source_edge_checked')
new_guards=[n for n in node.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value in ('ordinary_current_successor_exact_ninth_native_scope_required','ordinary_current_successor_exact_ninth_native_count_required')]
loop=next(n for n in node.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row' and any(isinstance(x,ast.If) and isinstance(x.test,ast.Name) and x.test.id=='ninth' for x in n.body))
image_guard=next(x for x in loop.body if isinstance(x,ast.If) and isinstance(x.test,ast.Name) and x.test.id=='ninth')
def execute_guard(nodes,context):exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<exact-candidate-guards>','exec'),dict(vars(O),f=f,ninth=True,**context))
rows=copy.deepcopy(manifest['files']);execute_guard(new_guards,dict(rows=rows,expected_files={str(n):None for n in range(17891)}));check('exact_native_scope_and_count_guard_accepts',True)
for name,bad in [('missing',rows[:-1]),('extra',rows+[dict(rows[0],path='unexpected.py')])]:refused('native_scope_refuses_'+name,lambda bad=bad:execute_guard(new_guards,dict(rows=bad,expected_files={})), 'exact_ninth_native_scope_required')
refused('native_count_refuses_change',lambda:execute_guard(new_guards,dict(rows=rows,expected_files={})), 'exact_ninth_native_count_required')
for row in rows:
 execute_guard([image_guard],dict(row=row,name=row['path']));check('exact_native_image_'+row['path'],True)
 for key,bad in [('before_sha256','0'*64),('sha256','0'*64),('bytes',row['bytes']+1),('new_file',True)]:
  changed=dict(row,**{key:bad});refused('native_image_refuses_'+row['path']+'_'+key,lambda changed=changed:execute_guard([image_guard],dict(row=changed,name=row['path'])), 'exact_ninth_native_images_required')
result={'state':'PASS_BOUNDED_SOURCE_ONLY','count':len(checks),'checks':checks,'wall_seconds':time.monotonic()-started,'CPU_seconds':time.process_time(),'resources':{'wall_limit':90,'cpu_limit':60,'memory_limit':512*1024**2,'affinity':sorted(os.sched_getaffinity(0))},'authority':'SYNTHETIC_CP_JOURNALS; real parser/canonical selector/committed proof/wrappers/edge guards; earlier root and final native authority remain seams','not_run':['genuine installed CP206/CP207','whole-chain source gates','installation/runtime/native authority/Office/model/Telegram/App']}
(B/'SOURCE-CHECKS.json').write_bytes(enc(result));print(json.dumps({k:result[k] for k in ('state','count','wall_seconds','CPU_seconds')}))
