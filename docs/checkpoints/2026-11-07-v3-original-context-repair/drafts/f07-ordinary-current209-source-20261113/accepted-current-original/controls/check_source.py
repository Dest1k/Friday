"""Finite SOURCE/OFFLINE stands. Synthetic authority/proof/reviews stay in RAM.
No tester import, actual Store, Runner.new/_send/send, H/current/socket/API/tool/model
execution. Exact consumer custody methods operate ONLY tiny own synthetic fixtures.
"""
import ast,builtins,copy,difflib,hashlib,importlib.util,json,math,os,pwd,re,resource,signal,sys,time,types,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2));signal.alarm(300)
spec=importlib.util.spec_from_file_location('f07_current209',ROOT/'source/current209.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prep=m.module(m.PREP);base=m._read_bounded(prep.SELECTED_TESTER,2*1024**2,False)
assert m.digest(base)==m.SELECTED_SHA
prior=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT-HARNESS-ORDINARY-PHASE-PREP-20261113/M1-SOURCE-PREFLIGHT.json')
phases=json.loads(prior.read_bytes())['phases']
rows=[]
def test(name,fn):
 try:fn()
 except BaseException as e:rows.append(dict(name=name,state='FAIL',error=type(e).__name__));raise
 else:rows.append(dict(name=name,state='PASS'))
def need(v):assert v
class Refused(Exception):pass
def reject(fn):
 try:fn()
 except (ValueError,Refused,AssertionError,TypeError):return
 raise AssertionError('expected rejection')
def sized(path,data):return dict(path=str(path),bytes=len(data),sha256=m.digest(data))
def put(path,value):
 path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 data=value if type(value) is bytes else m.encoded(value)
 path.write_bytes(data);path.chmod(0o600);return sized(path,data)
# Bounded ABI and actual genuine producer2/3refs. No H reference followed.
tmp=ROOT/'controls'/'synthetic-reader';tmp.mkdir(exist_ok=True,mode=0o700)
small=put(tmp/'tiny.source',b'source only\n');large=put(tmp/'large.source',b'x'*(1024**2+17))
test('reader_default1MiB_rejects_large',lambda:reject(lambda:m.read(large['path'])))
test('reader_no_limit_kwarg_ABI',lambda:reject(lambda:m.read(small['path'],limit=9)))
test('reader_explicit_exactlarge3ref',lambda:need(len(m.read_reference(large))==large['bytes']))
two={k:large[k] for k in ('path','sha256')}
test('reader_two_ref_no_sizefallback',lambda:reject(lambda:m.read_saved_reference(two)))
test('reader_exactknown_large_two_ref',lambda:need(len(m.read_saved_reference(two,known_large={(two['path'],two['sha256']):large['bytes']}))==large['bytes']))
for name,changes in [('bool',dict(bytes=True)),('missing',dict(extra=1)),('wronghash',dict(sha256='0'*64)),('wrongsize',dict(bytes=small['bytes']+1))]:
 r=dict(small,**changes);test('reader_reject_'+name,lambda r=r:reject(lambda:m.read_reference(r)))
test('reader_nested_callback_is_exact',lambda:need(m.read.f06_read_reference is m.read_reference and m.read.f07_read_reference is m.read_reference))
actual_closure=m.doc(m.CLOSURE);accept=m.doc(m.ACCEPTANCE)
test('actual_saved_closure2ref',lambda:need(actual_closure['installed']==m.COUNTS))
test('actual_saved_acceptance2ref',lambda:need(accept['after_counts']==m.COUNTS and accept['source_commit']==m.SOURCE_COMMIT))
input_ref=accept['selected_private_input'];real_input=m.doc(input_ref)
test('actual_saved_input3ref499',lambda:need(len(real_input['project_files'])==499))
source_output=m.doc({'path':'/home/jericho/.cache/FRW-SOL-V3-F07-NATIVE209-AFTER208-CORE-20261113/COMPOSITION-OUTPUT.json','sha256':'45cf138e8e22f322a77ce004a63ed8ffa2b273f6f3be42538f269ad5c338092a'})
test('nested_real_sized_source_input',lambda:need(m.doc(source_output['input'])==real_input))
# Shape predicates use synthetic counts projected from actual saved209 proof;
# these are explicitly not physical receipts/current observations.
receipt={'layers':list(range(209)),'files':{str(i):{} for i in range(17891)},'source_file_count':17730,'base_tree':'SYNTHETIC_SOURCE_SHAPE'}
marker={'plugin_files':{str(i):'x' for i in range(52)},'source_receipt_sha256':m.RECEIPT_SHA,'input_sha256':m.INPUT_SHA}
stamp={'fridaySource':{'layers':receipt['layers'],'baseTree':receipt['base_tree']}}
test('real_contract_projectcount_from_input_not_marker',lambda:need(m.installation_shapes(actual_closure,receipt,marker,stamp,real_input)==actual_closure['selected_environment']))
bad=copy.deepcopy(marker);bad['project_files']={str(i):0 for i in range(499)};badinput=dict(real_input,project_files={})
test('marker_projectcount_cannot_replace_input499',lambda:reject(lambda:m.installation_shapes(actual_closure,receipt,bad,stamp,badinput)))
bad=copy.deepcopy(actual_closure);bad['selected_environment']={'HERMES_HOME':str(m.H)}
test('actor_environment_not_per_service_basis',lambda:reject(lambda:m.installation_shapes(bad,receipt,marker,stamp,real_input)))
# Real saved Root census is metadata-only; classifications come from Root itself.
census=json.loads(Path('/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113/CURRENT-CANONICAL-HISTORY-METADATA-ROOT-PREPARATION.json').read_bytes())
test('real514_saved_census_not_semantic_or_current_admission',lambda:need(census['canonical_rows']==514 and census['exact_F07_and_prospective_matches']==[] and census['no_global_absence_or_semantic_acceptance_claim'] is True))
# Source definition extractor: no selected module import or top-level side effects.
tree=ast.parse(base);runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
methods={n.name:n for n in runner.body if isinstance(n,ast.FunctionDef)}
needed=['ordinary_independent_predecessor_checked','send_ack_budget','valid_send_budget','reply_window','verify_window','verify_capture_context','verify_reply_custody','capture_binding','receive_key','receive_context','read_reference','receive_inventory','cursor_offsets','ready']
top={}
for node in tree.body:
 if isinstance(node,(ast.FunctionDef,ast.ClassDef)):top[node.name]=node
 elif isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name):top[target.id]=node
want=set();todo=[]
for name in needed:
 for n in ast.walk(methods[name]):
  if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id in top and n.id!='Runner':todo.append(n.id)
while todo:
 name=todo.pop()
 if name in want:continue
 want.add(name)
 for n in ast.walk(top[name]):
  if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id in top and n.id!='Runner' and n.id not in want:todo.append(n.id)
selected=[];seen=set()
for node in tree.body:
 if id(node) not in seen and any(top[k] is node for k in want):selected.append(copy.deepcopy(node));seen.add(id(node))
ns=dict(Path=Path,os=os,pwd=pwd,re=re,unicodedata=unicodedata,json=json,hashlib=hashlib,math=math,time=time,dt=__import__('datetime'))
exec(compile(ast.Module(body=selected,type_ignores=[]),'<EXACT_CC36_INERT_HELPERS_ONLY>','exec'),ns)
Refused=ns['Refused']
# Every synthetic review/authority exists in RAM only, never as accepted Rootfiles.
ram={};fixture=ROOT/'controls'/'SYNTHETIC-CUSTODY';fixture.mkdir(exist_ok=True,mode=0o700)
for d in ('runs','downloads','captures'):(fixture/d).mkdir(exist_ok=True,mode=0o700)
def safe_read(path,*args,**kwargs):
 p=Path(path)
 if str(p) in ram:return ram[str(p)]
 need(p.is_relative_to(fixture));return p.read_bytes()
ns['safe_read']=safe_read
class StoreStand:
 root=fixture;runs=fixture/'runs';downloads=fixture/'downloads';captures=fixture/'captures'
 def run_path(self,name):return self.runs/(name+'.json')
 def get(self,path,default=None):
  try:return json.loads(safe_read(path))
  except FileNotFoundError:return default
class Stand:
 def __init__(self):self.store=StoreStand();self.reply_run=None
 def continuation_receipt(self,*args,**kwargs):return None
 def b00_closed_partial_history(self,run):return None
 def continuation_document_match(self,*args):return False
 def clock(self):return 100000
# Exact selected methods, no overridden chain nodes.
for name in needed:
 node=copy.deepcopy(methods[name]);env=dict(ns);exec(compile(ast.Module(body=[node],type_ignores=[]),'<EXACT_CC36_'+name+'>','exec'),env);setattr(Stand,name,env[name])
def authority(ordinal,run,previous=None):
 pred={} if ordinal==1 else {run:previous}
 return dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,authority_id='SOURCE_STAND_NOT_ISSUED',run_scenarios={run:phases[ordinal-1]['scenario_sha256']},history={'SOURCE_STAND':{}},unknown_effects_resolved=False,old_rows_modified=False,new_trial_for_historical_task=False,product_or_B00_acceptance=False,ordered_predecessors=pred,f07_original_case=dict(case_id='F-07',case_index=168,phase=phases[ordinal-1]['phase'],ordinal=ordinal,controlled_fault_sequence_not_replay=True,prospective_fixture_not_original=True))
def authority_ref(value):return sized(ROOT/'controls'/'SOURCE-STAND-NOT-ISSUED-AUTHORITY',m.encoded(value))
checker_ref=m.ref(ROOT/'source/current209.py');proof_ref=sized(ROOT/'controls'/'SOURCE-STAND-NOT-ISSUED-PROOF',b'never issued')
candidates=[];runs=[];bindings=[];st=Stand()
def named_reference(name,value):
 r=put(fixture/name,value);return dict(basename=name,bytes=r['bytes'],sha256=r['sha256'])
def make_run(ordinal,phase):
 name='SOURCE-STAND-phase-'+str(ordinal);start=1000*ordinal;mid=1700+ordinal;uid=4200+ordinal
 upload=phase['scenario']['steps'][0]['input'];metadata=dict(method='sendDocument',chat_id='@jerichodevbot',input_sha256=upload['sha256'],input_bytes=upload['stat']['size_bytes'],input_stat=upload['stat'],filename=upload['filename'],mime_type=upload['mime_type'],caption=upload['caption'],content_type='multipart/form-data; boundary=frw-'+'a'*64,body_sha256='b'*64,body_bytes=upload['stat']['size_bytes']+100,scenario_sha256=phase['scenario_sha256'])
 run=dict(id=name,scenario=copy.deepcopy(phase['scenario']),scenario_sha256=phase['scenario_sha256'],step=0,status='EVIDENCE_READY',send_state='sent',send_attempts=1,sent_ids=[mid],sent_message_id=mid,sent_date=start,sent_at=start+1,send_intent_at=start-1,send_dispatch_at=start,send_timeout_seconds=30,capture_until=start+181,deadline=start+300,capture_window_complete=True,capture_start_offset=uid,seen=[uid],message_ids=[mid+100],update_count=1,observations=[],request_metadata=metadata,reply_capture_prior_tracking=dict(capture_start_offset=uid,seen=[],message_ids=[]),acceptance='NOT_ESTABLISHED',reply_text_acceptance='RECEIVED_UNGRADED')
 ack=dict(message_id=mid,date=start,chat=dict(id=8751854128,type='private'),**{'from':dict(id=8812646969,is_bot=True)},caption=upload['caption'],document=dict(file_id='SYNTHETIC',file_unique_id='SYNTHETIC',file_size=upload['stat']['size_bytes'],file_name=upload['filename'],mime_type=upload['mime_type']))
 run['sent_api_ack_reference']=dict(named_reference('send-ack-'+name+'-0-1.json',ack),representation='decoded-message-json')
 run['sent_task_reference']=named_reference('send-task-'+name+'-0-1.json',metadata)
 commitment=dict(run_id=name,scenario_sha256=phase['scenario_sha256'],step=0,send_attempts=1,sent_message_id=mid,sent_at=run['sent_at'],send_intent_at=run['send_intent_at'],send_dispatch_at=start,send_timeout_seconds=30,capture_until=run['capture_until'],deadline=run['deadline'],window_seconds=180,ack=run['sent_api_ack_reference'],task=run['sent_task_reference'])
 run['sent_window_reference']=named_reference('send-window-'+name+'-0-1.json',commitment)
 text='Синтетический исправный ответ' if ordinal!=3 else 'Не могу прочитать повреждённый контейнер; структура DOCX не подтверждена.'
 update=dict(update_id=uid,message=dict(message_id=mid+100,date=start+2,chat=dict(id=8751854128,type='private'),**{'from':dict(id=8751854128,is_bot=True)},reply_to_message=dict(message_id=mid),text=text))
 raw=m.encoded(update);rawref=dict(basename=str(uid)+'.json',bytes=len(raw),sha256=m.digest(raw));put(fixture/'captures'/rawref['basename'],raw)
 binding=st.capture_binding(run)
 obs=dict(binding,kind='reply_text',message_id=mid+100,update_id=uid,date=start+2,text=text,text_sha256=m.digest(text.encode()),raw_update=rawref)
 receipt=put(fixture/'downloads'/(name+'-'+str(mid+100)+'-'+m.digest(text.encode())+'.text-receipt.json'),obs)
 obs.update(receipt_path=receipt['path'],receipt_sha256=receipt['sha256'],receipt_bytes=receipt['bytes']);run['observations']=[obs]
 context=st.receive_context(run);arrival=dict(update_id=uid,arrived_at=start+2,context=context,raw_update=rawref)
 ar=put(fixture/'captures'/(str(uid)+'.arrival.json'),arrival);arrivalref=dict(basename=str(uid)+'.arrival.json',bytes=ar['bytes'],sha256=ar['sha256'])
 records=[dict(kind='seed',offset=uid),dict(kind='capture',offset=uid+1,update_id=uid,raw_update=rawref,arrival=arrivalref),dict(kind='processing',offset=uid+1,update_id=uid),dict(kind='processed',offset=uid+1,update_id=uid,observations=[obs],message_ids=[mid+100]),dict(kind='terminal_intent',offset=uid+1,started_at=run['capture_until'],timeout_seconds=5,update_count=1,limit=20)]
 wire=named_reference('terminal-response-'+name+'-0-1.json',dict(ok=True,result=[]))
 records.extend([dict(kind='terminal_response',offset=uid+1,received_at=run['capture_until']+1,wire=wire),dict(kind='terminal_complete',offset=uid+1,completed_at=run['capture_until']+2)])
 previous=None
 for i,record in enumerate(records):
  record.update(context=context,sequence=i,previous=previous);previous=named_reference('receive-'+name+'-0-1-'+str(i)+'.json',record)
 run.update(receive_head=previous,receive_sequence=len(records)-1)
 put(fixture/'runs'/(name+'.json'),run)
 return run
# Generate complete four synthetic captures; Root's semantic grades are source-only
# predicates in RAM, never observations of a product response.
for i,p in enumerate(phases,1):runs.append(make_run(i,p))
put(fixture/'cursor.json',dict(offset=4205,capture_receipts={st.receive_key(run):run['receive_head'] for run in runs}))
for run in runs:
 raw=m.encoded(run);review=dict(schema='frw.SOURCE_STAND.F07.review.v1',run_id=run['id'],scenario_sha256=run['scenario_sha256'],semantic='PASS',custody='PASS',custody_evidence=dict(run_record_sha256=m.digest(raw)),synthetic_predicate_not_Root_acceptance=True)
 path=ROOT/'controls'/('SOURCE-STAND-review-'+run['id']);ram[str(path)]=m.encoded(review)
 bindings.append(dict(run_id=run['id'],scenario_sha256=run['scenario_sha256'],run_record_sha256=m.digest(raw),review=dict(path=str(path),sha256=m.digest(ram[str(path)])),review_schema=review['schema'],initially_absent=False))
for i,p in enumerate(phases,1):
 name=runs[i-1]['id'];a=authority(i,name,bindings[i-2] if i>1 else None);ar=authority_ref(a)
 raw=prep.compose_source(base,p,run_id=name,authority_ref=ar,authority=a,previous_phase=phases[i-2] if i>1 else None)
 candidate=m.compose_preintent_source(raw,phase=p,run_id=name,authority_ref=ar,authority=a,proof_ref=proof_ref,checker_ref=checker_ref,previous_phase=phases[i-2] if i>1 else None)
 ct=ast.parse(candidate);cr=next(n for n in ct.body if isinstance(n,ast.ClassDef) and n.name=='Runner');cm={n.name:n for n in cr.body if isinstance(n,ast.FunctionDef)}
 env=dict(ns);exec(compile(ast.Module(body=[copy.deepcopy(cm['send_ack_budget'])],type_ignores=[]),'<EXACT_F07_ACK_MAP>','exec'),env);Stand.send_ack_budget=env['send_ack_budget']
 test('phase'+str(i)+'_current_ACK30_exact_source',lambda i=i:need(st.send_ack_budget(runs[i-1])==30))
 test('phase'+str(i)+'_unrelated_ACK10',lambda:need(st.send_ack_budget(dict(id='unrelated',scenario_sha256='0'*64))==10))
 test('phase'+str(i)+'_current_full_custody_exact_methods',lambda i=i:st.verify_reply_custody(runs[i-1]))
 test('phase'+str(i)+'_sendwindow_and_replywindow180',lambda i=i:need(st.reply_window(runs[i-1])==runs[i-1]['sent_at']+180))
 test('phase'+str(i)+'_terminal_complete_custody',lambda i=i:need(st.receive_inventory(runs[i-1],terminal=True)[2]['complete']['kind']=='terminal_complete'))
 if i>1:
  test('phase'+str(i)+'_exact_immediate_predecessor_ACK30',lambda i=i:need(st.send_ack_budget(runs[i-2])==30))
  test('phase'+str(i)+'_actual_predecessor_to_full_reply_custody_chain',lambda i=i:need(st.ordinary_independent_predecessor_checked(bindings[i-2])==runs[i-2]))
  # The original frozen one-run ACK candidate genuinely fails at nearest consumer.
  oldrunner=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Runner');oldack=next(n for n in oldrunner.body if isinstance(n,ast.FunctionDef) and n.name=='send_ack_budget')
  oldenv=dict(ns);exec(compile(ast.Module(body=[copy.deepcopy(oldack)],type_ignores=[]),'<ORIGINAL_PREP_CURRENT_ONLY_ACK>','exec'),oldenv)
  saved=Stand.send_ack_budget;Stand.send_ack_budget=oldenv['send_ack_budget']
  test('phase'+str(i)+'_negative_original_currentonlyACK_rejects_predecessor',lambda i=i:reject(lambda:st.ordinary_independent_predecessor_checked(bindings[i-2])))
  Stand.send_ack_budget=saved
 if i>2:test('phase'+str(i)+'_older_nonimmediate_ACK10',lambda i=i:need(st.send_ack_budget(runs[i-3])==10))
 # AST guarantees exact full source remainder, including all new/send/capture/stop.
 normalized=copy.deepcopy(ct);nr=next(n for n in normalized.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
 rrunner=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Runner')
 for j,node in enumerate(nr.body):
  if isinstance(node,ast.FunctionDef) and node.name in ('ordinary_independent_admission','send_ack_budget'):
   nr.body[j]=copy.deepcopy(next(n for n in rrunner.body if isinstance(n,ast.FunctionDef) and n.name==node.name))
 test('phase'+str(i)+'_only_admission_prefix_and_exact_ACKmap_delta',lambda:need(ast.dump(normalized,include_attributes=False)==ast.dump(ast.parse(raw),include_attributes=False)))
 # Bound loader prefix executes with synthetic check callback only. Full selected
 # new/send bodies are NEVER executed. Original admission body remains AST-exact.
 prefix=copy.deepcopy(cm['ordinary_independent_admission']);prefix.body=prefix.body[:1]
 def exec_stand(code,globals):
  builtins.exec(code,globals)
  if globals.get('__name__')=='_Root_F07_current209':globals['check']=lambda proof_ref,**kw:trace.append(kw)
 trace=[];prefixenv=dict(ns,types=types,exec=exec_stand)
 prefixenv['safe_read']=lambda path,**kw:m.read_reference(checker_ref) if str(path)==checker_ref['path'] else safe_read(path,**kw)
 exec(compile(ast.Module(body=[prefix],type_ignores=[]),'<EXACT_SOURCE_INSERTED_PREFIX>','exec'),prefixenv)
 fake=types.SimpleNamespace()
 for stage in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'):
  if stage!='NEW':fake._send_phase=stage
  prefixenv['ordinary_independent_admission'](fake,name,p['scenario'])
 test('phase'+str(i)+'_three_rechecks_one_effect_no_new_send_call',lambda:need([x['stage'] for x in trace]==['NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'] and all(x['run_id']==name for x in trace)))
 candidates.append(dict(ordinal=i,bytes=len(candidate),sha256=m.digest(candidate),ACK30_ids=[name]+([runs[i-2]['id']] if i>1 else [])))
 if i==4:(ROOT/'SOURCE-DELTA-TEMPLATE.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),candidate.decode().splitlines(keepends=True),fromfile='frozen-prep-SOURCE-STAND-currentphase4',tofile='current209-SOURCE-STAND-currentphase4')))
# A complete synthetic safe malformed refusal remains raw ungraded and can be
# reviewed for the expected negative semantic; healthy phase4 uses same SID.
test('phase3_truthful_negative_capture_ungraded_preserved',lambda:need(runs[2]['reply_text_acceptance']=='RECEIVED_UNGRADED' and runs[2]['acceptance']=='NOT_ESTABLISHED' and runs[2]['capture_until']-runs[2]['sent_at']==180))
test('phase4_healthy_follows_actual_phase3_review_samechat_source_contract',lambda:need(phases[3]['same_chat_session_no_reset'] and bindings[2]['scenario_sha256']==runs[2]['scenario_sha256'] and phases[3]['expected_semantics']=='healthy_followup_same_chat'))
# Meaningful affected controls from the exact current+previous candidate.
for change in ('window','ack','runhash','reviewgrade','missing_terminal','source_scenario'):
 target=runs[2];path=fixture/'runs'/(target['id']+'.json');before=path.read_bytes();mem_before=copy.deepcopy(ram)
 try:
  if change=='window':target=copy.deepcopy(target);target['capture_until']+=1;put(path,target)
  elif change=='ack':target=copy.deepcopy(target);target['send_timeout_seconds']=10;put(path,target)
  elif change=='runhash':put(path,dict(target,status='STOPPED'))
  elif change=='reviewgrade':rpath=bindings[2]['review']['path'];review=json.loads(ram[rpath]);review['semantic']='FAIL';ram[rpath]=m.encoded(review)
  elif change=='missing_terminal':target=copy.deepcopy(target);target['receive_sequence']-=1;put(path,target)
  elif change=='source_scenario':target=copy.deepcopy(target);target['scenario']['steps'][0]['input']['sha256']='0'*64;put(path,target)
  test('fourphase_chain_reject_'+change,lambda:reject(lambda:st.ordinary_independent_predecessor_checked(bindings[2])))
 finally:path.write_bytes(before);ram.clear();ram.update(mem_before)
# Own current boundary: only absent->exact pristine, no rate-limited second send.
now=10000
pristine=dict(id='SOURCE-STAND-fresh',scenario=phases[0]['scenario'],scenario_sha256=phases[0]['scenario_sha256'],created_at=__import__('datetime').datetime.fromtimestamp(now,__import__('datetime').timezone.utc).isoformat(),deadline=now+300,step=0,status='PREPARED',send_state='none',sent_ids=[],seen=[],message_ids=[],observations=[],update_count=0,last_text=None,repeat_count=0,send_attempts=0,capture_start_offset=0)
effect=dict(run_id=pristine['id'],phase=phases[0])
test('own_exact_pristine_positive',lambda:m.pristine(pristine,effect,now))
for key,value in [('send_attempts',1),('send_state','not_sent_rate_limited'),('deadline',now+214),('status','SEND_INTENT')]:
 bad=dict(pristine,**{key:value});test('own_pristine_reject_'+key,lambda bad=bad:reject(lambda:m.pristine(bad,effect,now)))
# Pure fresh proof checks and source-only unbound state.
unbound=m.unbound_proof();test('unbound_proof_has_no_issued_current_or_authority',lambda:need(unbound['status']=='UNBOUND_NOT_GRANTED' and all(unbound[k] is None for k in ('effect','invocation','Root_decision','privacy_preflight','observed'))))
proof=dict(created_at=10,expires_at=100,created_monotonic=20,expires_monotonic=110)
test('proof_dualclock_positive',lambda:need(m.fresh(proof,wall=50,mono=60)==110))
for key,value in [('expires_at',49),('created_at',51),('expires_monotonic',59),('created_monotonic',61),('expires_at',131)]:
 bad=dict(proof,**{key:value});test('proof_clock_reject_'+key+str(value),lambda bad=bad:reject(lambda:m.fresh(bad,wall=50,mono=60)))

# Execute the REAL checker and REAL Root-decision/privacy validators with explicit
# RAM synthetic factual predicates. The actual collector/locks/kernel are blocked;
# these fixtures are never written as accepted Root files or runtime evidence.
original={k:getattr(m,k) for k in ('doc','effect_shape','observe','kernel','read_kernel_boot','lock_held','process_bytes')}
nowwall=time.time();nowmono=time.monotonic();kid=dict(pid=os.getpid(),start_time=1,boot_id='SYNTHETIC_BOOT_NOT_ACTUAL')
def ramlabeled(name,value):return sized(ROOT/'controls'/('SOURCE-STAND-'+name),m.encoded(value))
synthetic_phase=copy.deepcopy(phases[0]);synthetic_phase['scenario']['steps'][0]['input']['path']=str(ROOT/'controls'/'SYNTHETIC_INPUT_NOT_CURRENT')
synthetic_effect=dict(schema='frw.Root.F07.current209-effect.v1',run_id='SOURCE-STAND-checker',phase=synthetic_phase,
 authority=ramlabeled('authority',{}),scenario=ramlabeled('scenario',{}),checker=checker_ref,source_preparation=ramlabeled('prep',{}),installation_closure=ramlabeled('closure',{}),source_acceptance=ramlabeled('acceptance',{}),resources=dict(m.TIMING,cpu_seconds=120,max_rss_bytes=512*1024**2,disk_bytes=100*1024**2,clock=ramlabeled('clock',{}),owned_parent_wait_cleanup=ramlabeled('cleanup',{})))
ob=dict(history=dict(sha256='1'*64),custody=dict(sha256='2'*64),native=dict(synthetic=True),databases=dict(tester=dict(max_message_id=100)),installed=dict(runtime_hashes={k:'0'*64 for k in m.RELEVANT}),technical_log_cursor=dict(synthetic=True),profile_configs=dict(tester=small),gateway=kid)
proofref=ramlabeled('proof',{});iref=ramlabeled('invocation',{});dref=ramlabeled('decision',{});pref=ramlabeled('privacy',{})
wh=m.digest(m.encoded(synthetic_effect))
proof=dict(schema='frw.Root.F07.current209-preintent.v1',status='ROOT_BOUND',operator='Root',effect=synthetic_effect,whole_effect_sha256=wh,created_at=nowwall-1,expires_at=nowwall+100,created_monotonic=nowmono-1,expires_monotonic=nowmono+100,boot_id=kid['boot_id'],observed=copy.deepcopy(ob),lock_owners={key:kid for key in ('shared_slot','consumer','credential')},invocation=iref,Root_decision=dref,privacy_preflight=pref)
inv=dict(schema='frw.Root.F07.one-ordinary-consumer-invocation.v1',run_id=synthetic_effect['run_id'],whole_effect_sha256=wh,clock=synthetic_effect['resources']['clock'],no_retry=True,consumer=kid)
decision=dict(schema='frw.Root.F07.current209-original-case-decision.v1',operator='Root',status='ROOT_BOUND',whole_effect_sha256=wh,history_sha256=ob['history']['sha256'],custody_sha256=ob['custody']['sha256'],native_SQL_boundary_sha256=m.digest(m.encoded(dict(native=ob['native'],databases=ob['databases']))),original_phase_effect_eligible=True,old_effects_UNKNOWN_clocks_preserved=True,all_profile_semantic_unlogged_equivalents_reconciled=True,equivalent_consumed_phase_effects=[],projection_limit=m.PROJECTION_LIMIT,root_current_pending_approval_cancel_maintenance_assessed=True,current_scope_evidence=[small])
privacy=dict(schema='frw.Root.F07.current209-privacy-preflight.v1',operator='Root',status='ROOT_BOUND_PREFLIGHT_NOT_RUNTIME_VERDICT',whole_effect_sha256=wh,runtime_hashes=ob['installed']['runtime_hashes'],logging_sites=list(m.LOGGING_SITES),technical_log_cursor=ob['technical_log_cursor'],postcondition_plan=m.postcondition_plan(synthetic_effect,ob),source_metadata_only_checked=True,genuine_current_event_observed=False,runtime_logging_verdict='NOT_ESTABLISHED',raw_user_retention_separately_scoped=True,source_evidence=[small],effective_product_roots=[str(m.H)],private_roots=[str(ROOT)],effective_roots_profile_config_refs=ob['profile_configs'],effective_roots_source_basis=[small])
ramdoc={proofref['path']:proof,iref['path']:inv,dref['path']:decision,pref['path']:privacy}
observations=[]
def source_doc(r,**kw):
 if r['path'] in ramdoc:return copy.deepcopy(ramdoc[r['path']])
 return original['doc'](r,**kw)
def source_observe(effect,*,stage):observations.append(stage);return copy.deepcopy(ob)
m.doc=source_doc;m.effect_shape=lambda effect:(None,dict(deadline_monotonic=nowmono+600));m.observe=source_observe
m.kernel=lambda pid:kid;m.read_kernel_boot=lambda:kid['boot_id'];m.lock_held=lambda path,owner:need(owner==kid);m.process_bytes=lambda pid,name:b'SOURCE_STAND_NO_PRODUCT_METADATA'
def gate():return m.check(proofref,run_id=synthetic_effect['run_id'],scenario=synthetic_phase['scenario'],stage='PRE_INTENT_REVALIDATION')
try:
 test('real_checker_with_labelled_synthetic_predicates',lambda:need(gate()['admission'] is False))
 for key,value in [('status','UNBOUND_NOT_GRANTED'),('boot_id','OTHER_BOOT'),('whole_effect_sha256','0'*64),('expires_at',nowwall-1),('lock_owners',{})]:
  saved=copy.deepcopy(proof[key]);proof[key]=value
  test('real_checker_reject_'+key,lambda:reject(gate));proof[key]=saved
 ob['custody']['sha256']='3'*64;test('real_checker_reject_mutable_CAS_drift',lambda:reject(gate));ob['custody']['sha256']='2'*64
 inv['no_retry']=False;test('real_checker_reject_retry_invocation',lambda:reject(gate));inv['no_retry']=True
 for key,value in [('original_phase_effect_eligible',False),('equivalent_consumed_phase_effects',['SYNTHETIC_CONSUMED']),('projection_limit','SCOPED_TESTER_EQUALS_ALL_PROFILE'),('root_current_pending_approval_cancel_maintenance_assessed',False),('history_sha256','0'*64)]:
  saved=copy.deepcopy(decision[key]);decision[key]=value
  test('real_Root_decision_reject_'+key,lambda:reject(gate));decision[key]=saved
 for key,value in [('genuine_current_event_observed',True),('runtime_logging_verdict','PASS'),('technical_log_cursor',{}),('effective_roots_profile_config_refs',{}),('effective_product_roots',[str(ROOT),str(m.H)])]:
  saved=copy.deepcopy(privacy[key]);privacy[key]=value
  test('real_privacy_preflight_reject_'+key,lambda:reject(gate));privacy[key]=saved
 test('real_preintent_requires_no_future_ACK_reply_grade_source_ref',lambda:need(gate()['state']=='CURRENT209_PREINTENT_CHECKED_NOT_PRODUCT_ACCEPTANCE' and 'actual_ACK' not in proof and 'actual_reply' not in proof))
 test('normal_context_capability_or_ContextVar_not_constructed',lambda:need(not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('ContextVar','UserScope','Capability','Source') for node in ast.walk(ast.parse((ROOT/'source/current209.py').read_bytes())))))
finally:
 for k,v in original.items():setattr(m,k,v)
# All nine exact installed209 leafdependency pins from accepted qualification are
# reused without executing its eight tool calls; they join current byte checks.
q=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-F07-QUALIFICATION-PREP-20261113/qualify_current_scope.py')
qt=ast.parse(q.read_bytes());pin=next(n.value for n in qt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED_PINS' for t in n.targets))
test('all_nine_existing_F07_dependency_pins_exact',lambda:need(m.F07_PINS==ast.literal_eval(pin)))
test('F07_paths_plus_nativeprojection_and_logging_current_byteguards',lambda:need(set(m.RELEVANT)==set(m.F07_PINS)|{'gateway/ordinary_turn_projection.py',*m.LOGGING_SITES}))


# New readonly collector seam has no user clock/authority/once precondition. Its
# actual backend is NOT invoked here; only exact public input-join is exercised.
old_collect=m._observe_current;trace=[]
m._observe_current=lambda inputs,*,stage:(trace.append((copy.deepcopy(inputs),stage)) or {'synthetic':True})
try:
 cr=m.ref(m.CLOSURE['path']);ar=m.ref(m.ACCEPTANCE['path'])
 out=m.observe_readonly(phase=phases[0],run_id='SOURCE-STAND-readonly',closure_ref=cr,acceptance_ref=ar,resource_limits=dict(max_rss_bytes=512*1024**2,disk_bytes=100*1024**2))
 test('readonly_current_metadata_seam_no_operationclock_or_authority',lambda:need(out['operation_clock_created'] is False and out['authority_issued'] is False and 'authority' not in trace[0][0] and 'clock' not in trace[0][0]['resources'] and trace[0][1]=='BASELINE'))
 bad=dict(cr,sha256='0'*64)
 test('readonly_wrong_actual209_closure_rejected_before_backend',lambda:reject(lambda:m.observe_readonly(phase=phases[0],run_id='SOURCE-STAND-readonly',closure_ref=bad,acceptance_ref=ar,resource_limits=dict(max_rss_bytes=1,disk_bytes=1))))
finally:m._observe_current=old_collect
# Confirmed actual assessment API + ordinary predecessor-review bridge operate on
# synthetic evidence only. Accepted Root fields remain RAM and carry no admission.
cs=importlib.util.spec_from_file_location('f07_root_caller',ROOT/'source/root_caller.py');caller=importlib.util.module_from_spec(cs);cs.loader.exec_module(caller)
run=runs[2];e=dict(run_id=run['id'],phase=phases[2],installation_closure=m.ref(m.CLOSURE['path']))
observed=dict(gateway=dict(synthetic=True),databases=dict(tester=dict(max_message_id=100)),technical_log_cursor=dict(synthetic=True),installed=dict(runtime_hashes={k:'0'*64 for k in m.RELEVANT}))
actuals={};saved_doc=m.doc;saved_reader=m.read_reference
nr=ramlabeled('native-source-correlation',{})
actuals[nr['path']]=dict(schema='frw.Root.F07.actual-native-ingress-correlation.v1',operator='Root',run_id=run['id'],tester_ACK_message_id=run['sent_message_id'],native_principal=m.PRINCIPAL,native_platform_message_id='9003',native_message_row_id=103,source_sha256=phases[2]['scenario']['steps'][0]['input']['sha256'],filename=phases[2]['scenario']['steps'][0]['input']['filename'],actual_source_ref_custody_checked=True,actual_source_ref_evidence=small)
refs=dict(canonical_run=sized(fixture/'runs'/(run['id']+'.json'),m.encoded(run)),ACK=sized(fixture/run['sent_api_ack_reference']['basename'],(fixture/run['sent_api_ack_reference']['basename']).read_bytes()),capture=sized(fixture/('terminal-response-'+run['id']+'-0-1.json'),(fixture/('terminal-response-'+run['id']+'-0-1.json')).read_bytes()),native_ingress=nr,technical_carriers=ramlabeled('carrier-inventory',{}),native_host_close=ramlabeled('native-host-close',{}))
actuals[refs['technical_carriers']['path']]={'synthetic':True};actuals[refs['native_host_close']['path']]={'synthetic':True}
assessment=dict(schema='frw.Root.F07.actual-postcondition-assessment.v1',operator='Root',status='ROOT_ASSESSED_SAVED_ACTUAL_ONLY',plan=m.postcondition_plan(e,observed),extra_event_or_replay_performed=False,evidence=refs,raw_status='EVIDENCE_READY',raw_send_state='sent',raw_consumer_acceptance='NOT_ESTABLISHED',verdicts=dict(semantic='PASS',privacy='PASS',custody='PASS',native_host_close='PASS'),per_logging_site={site:dict(execution='OBSERVED',verdict='PASS',evidence=[small]) for site in m.LOGGING_SITES})
def actual_doc(r,**kw):
 if r['path'] in actuals:return copy.deepcopy(actuals[r['path']])
 return saved_doc(r,**kw)
def actual_read(r,**kw):
 if r['path'] in actuals:return m.encoded(actuals[r['path']])
 return saved_reader(r,**kw)
m.doc=actual_doc;m.read_reference=actual_read
try:
 test('saved_actual_assessment_separate_semantic_privacy_custody_host',lambda:need(m.assess_saved_actual(assessment,effect=e,observed=observed)['raw_consumer_acceptance']=='NOT_ESTABLISHED'))
 test('native_platform_decimalstring_has_no_tester_ACK_equality_assumption',lambda:need(actuals[nr['path']]['native_platform_message_id']!=str(run['sent_message_id']) and m.assess_saved_actual(assessment,effect=e,observed=observed)['verdicts']['custody']=='PASS'))
 aref=ramlabeled('actual-assessment',assessment);actuals[aref['path']]=assessment
 review=caller.actual_predecessor_review(m,effect=e,observed=observed,assessment=assessment,assessment_ref=aref)
 test('actual_postcondition_to_ordinary_predecessor_review_exact_ABI',lambda:need(review['semantic']==review['custody']=='PASS' and review['custody_evidence']['run_record_sha256']==refs['canonical_run']['sha256']))
 for dimension,value in [('privacy','FAIL'),('native_host_close','NOT_ESTABLISHED')]:
  bad=copy.deepcopy(assessment);bad['verdicts'][dimension]=value;bref=ramlabeled('bad-predecessor-'+dimension,bad);actuals[bref['path']]=bad
  test('postcondition_bridge_reject_'+dimension,lambda bad=bad,bref=bref:reject(lambda:caller.actual_predecessor_review(m,effect=e,observed=observed,assessment=bad,assessment_ref=bref)))
 for name,mutate in [('unobserved_logging_PASS',lambda a:a['per_logging_site'][m.LOGGING_SITES[0]].update(execution='NOT_OBSERVED')),('raw_status_regrade',lambda a:a.update(raw_status='PASS')),('actual_source_ref_missing',lambda a:actuals[nr['path']].update(actual_source_ref_custody_checked=False))]:
  bad=copy.deepcopy(assessment);before=copy.deepcopy(actuals[nr['path']]);mutate(bad)
  test('saved_actual_reject_'+name,lambda bad=bad:reject(lambda:m.assess_saved_actual(bad,effect=e,observed=observed)));actuals[nr['path']]=before
 unknown=dict(run,id=e['run_id'],status='UNKNOWN_SEND',send_state='unknown');uref=ramlabeled('unconfirmed-run',unknown);actuals[uref['path']]=unknown
 closure=dict(schema='frw.Root.F07.unconfirmed-technical-closure.v1',operator='Root',run_id=e['run_id'],whole_effect_sha256=m.digest(m.encoded(e)),phase_successor_admitted=False,raw_outcome_regraded=False,extra_event_or_retry_performed=False,semantic_verdict='NOT_ESTABLISHED',canonical_run=uref,raw_status='UNKNOWN_SEND',raw_send_state='unknown',closure_evidence=[small])
 test('unconfirmed_technical_closure_requires_no_future_ACK_or_ingress',lambda:need(m.assess_unconfirmed_closure(closure,effect=e)['raw_send_state']=='unknown' and 'ACK' not in closure))
 bad=dict(closure,phase_successor_admitted=True);test('unknown_cannot_unlock_phase_successor',lambda:reject(lambda:m.assess_unconfirmed_closure(bad,effect=e)))
finally:m.doc=saved_doc;m.read_reference=saved_reader
# Root caller's separate real readonly method gets api=None and exact calls only.
class ReadonlySourceStand:
 api=None
 def ordinary_independent_admission(self,name,scenario):self.got=(name,scenario);return {'SOURCE_STAND_NOT_AUTHORITY':True}
 def ordinary_independent_current_rows(self,admission,name):need(admission=={'SOURCE_STAND_NOT_AUTHORITY':True});self.current=name
rd=ReadonlySourceStand();r=caller.qualify_selected_ordinary_readonly(rd,run_id='SOURCE-STAND-readonly',phase=phases[0])
test('Root_readonly_wrapper_exact_selected_methods_no_new_send',lambda:need(rd.current=='SOURCE-STAND-readonly' and r['new_called'] is r['send_called'] is False))

# A readonly access-time update is not custody/source drift; inode/owner/mode/
# link/size/mtime/ctime remain mandatory in the exact accepted9-field identity.
stats={key:i+1 for i,key in enumerate(('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))}
left=types.SimpleNamespace(**stats,st_atime=1);right=types.SimpleNamespace(**stats,st_atime=2)
test('final_source_CAS_ignores_read_induced_atime_only',lambda:need(m.identity(left)==m.identity(right)))
right.st_ctime_ns+=1;test('final_source_CAS_still_detects_ctime_drift',lambda:need(m.identity(left)!=m.identity(right)))

report=dict(schema='frw.F07.current209-source-controls.v1',state='SOURCE_OFFLINE_ONLY_NOT_RUNTIME_OR_ROOT_ADMISSION',checks=rows,count=len(rows),candidate_metadata_only=candidates,source_helpers=sorted(want),full_exact_chain_methods=needed,synthetic_boundary='Only tiny source fixture file IO + RAM authority/review + b00 history predicate None; no product execution or source fake capability/context',real_current_H_API_Store_new_send_tool_model_calls=0,previous66_controls_reused_unmodified=True)
put(ROOT/'controls'/'SOURCE-CONTROLS.json',report)
print(json.dumps(dict(state='PASS_SOURCE_ONLY',checks=len(rows),candidates=len(candidates),nearest_chain='exact predecessor/custody/window/receive_inventory/cursor')))
# Own disposable bulk reader stand not needed after verified controls.
(tmp/'large.source').unlink()
