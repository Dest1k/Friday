"""EXPLICIT SYNTHETIC memory-only upload/custody fixtures; no real IDs or grants."""
import ast,copy,hashlib,json,os,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent
C=B/'candidate'
def load(n):
 p=C/n;m=types.ModuleType(n[:-3]);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=load('f06_source.py');F=load('first_ingress.py')
code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()}
base=A.BASE.read_bytes();assert A.digest(base)==A.BASE_SHA
fulltree=ast.parse(base);footer=(C/'f06_footer.py.txt').read_bytes()
# Exact frozen source functions, no tester import/global app initialization.
def original_functions(names,ns):
 nodes=[n for n in fulltree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'EXTRACTED_FULL_V42','exec'),ns)
ns={'Refused':ValueError,'MAX_FILE':8*1024**2,'PEER':8751854128,'TESTER':8812646969,'USERNAME':'@jerichodevbot','REPLY_WINDOW_RESERVE':5}
# Exact capture functions depend on optional fixed S15/S16 profiles; take their
# original definitions too, plus original constant assignments referenced by them.
for n in fulltree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('S15_CAPTURE','S16_CAPTURE','S15_OUTPUT','S16_OUTPUT') for t in n.targets):
  exec(compile(ast.Module(body=[n],type_ignores=[]),'V42_CAPTURE_CONSTANT', 'exec'),ns)
original_functions({'reply_capture','ordinary_s16_reply_capture','ordinary_s15_reply_capture','validate_reply_capture','validate_scenario','stopped1578_capture_scenario'},ns)
checks=[]
def ok(name,v=True):assert v,name;checks.append(name)
def refuses(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,AttributeError):checks.append(name);return
 raise AssertionError(name)
# No source, document, credential or network I/O permitted in test body.
def audit(event,args):
 if event=='open' or event.startswith(('socket.','subprocess.','os.system','os.exec','os.spawn')):raise RuntimeError('PURE_CONTROL_EFFECT_REFUSED')
'SYNTHETIC'.encode('utf-16-le')  # load stdlib codec BEFORE pure-I/O barrier
sys.addaudithook(audit)

def fixture(mods=None):
 mods=mods or {};data=dict(code)
 def put(name,v,raw=False):
  p='/SYNTHETIC-T28-ONLY/'+name;raw=v if raw else A.encoded(v);data[p]=raw
  return dict(path=p,bytes=len(raw),sha256=A.digest(raw))
 def tweak(k,v):
  if k in mods:mods[k](v)
  return v
 source=dict(A.SOURCE);identity={'device':1,'inode':2,'size_bytes':23040,'uid':1,'mtime_ns':1,'ctime_ns':1}
 principal={'profile':'telegram-bot-8812646969','session_id':'SYNTHETIC-SESSION','session_key':'SYNTHETIC-KEY'}
 upload=dict(kind='document',path=source['path'],sha256=source['sha256'],stat=identity,filename='f06-new-encrypted.docx',mime_type=A.MIME,caption='SYNTHETIC-WRONG-REQUEST-NOT-A-CREDENTIAL')
 scenario=dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=300,max_updates=65,pace_seconds=1,steps=[{'input':upload,'observe':dict(A.OBSERVE)}])
 ack=tweak('ack',dict(message_id=11,date=1,chat={'id':8751854128,'type':'private'},**{'from':{'id':8812646969,'is_bot':True}},caption=upload['caption'],document=dict(file_id='SYNTHETIC-FILE-ID',file_unique_id='SYNTHETIC-UNIQUE-ID',file_size=23040,file_name='f06-new-encrypted.docx',mime_type=A.MIME)))
 # Canonical path strings are modeled only in this dict; no files are created there.
 def stored(name,v,rep=None):
  p=str(F.STATE/name);raw=A.encoded(v);data[p]=raw;r=dict(path=p,bytes=len(raw),sha256=A.digest(raw));recorded=dict(basename=name,bytes=len(raw),sha256=r['sha256'])
  if rep:recorded['representation']=rep
  return r,recorded
 ar,asr=stored('send-ack-SYNTHETIC-first-0-1.json',ack,'decoded-message-json')
 task=tweak('task',dict(method='sendDocument',chat_id='@jerichodevbot',input_sha256=source['sha256'],input_bytes=23040,input_stat=identity,caption=upload['caption'],scenario_sha256=A.digest(A.encoded(scenario))))
 tr,tsr=stored('send-task-SYNTHETIC-first-0-1.json',task)
 win=tweak('window',dict(run_id='SYNTHETIC-first',scenario_sha256=A.digest(A.encoded(scenario)),sent_message_id=11,sent_at=1,capture_until=181,window_seconds=180,ack=asr,task=tsr))
 wr,wsr=stored('send-window-SYNTHETIC-first-0-1.json',win)
 run=tweak('run',dict(id='SYNTHETIC-first',status='EVIDENCE_READY',send_state='sent',send_attempts=1,scenario=scenario,scenario_sha256=A.digest(A.encoded(scenario)),sent_message_id=11,sent_date=1,capture_until=181,sent_api_ack_reference=asr,sent_task_reference=tsr,sent_window_reference=wsr,request_metadata=task))
 rp=str(F.STATE/'runs'/'SYNTHETIC-first.json');raw=A.encoded(run);data[rp]=raw;rr=dict(path=rp,bytes=len(raw),sha256=A.digest(raw));sr={'run_id':'SYNTHETIC-first','run_sha256':rr['sha256'],'input_sha256':source['sha256']}
 dummy=put('dummy-proof.json',{'synthetic':True})
 old=dict(schema='frw.F06.original-docx-ordinary-first-wrongread.v2',phase='DOCX-WRONG-READ-INGRESS',status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',run_id=run['id'],scenario_sha256=run['scenario_sha256'],source=source,authority=dummy,boundary={'B':dict(principal,native_max_id=1)})
 binding=put('first-binding.json',{'contract':tweak('binding',old)})
 def judgement(k,schema,extra):
  d=dict(schema=schema,operator='Root',status='ROOT_BOUND',source_reference=sr,B=principal,source=source,**extra)
  return put(k+'.json',tweak(k,d))
 closure=judgement('closure','frw.Root.F06.first-operation-closed.v1',dict(actor_tree_closed=True,slot_released=True,no_pending_first_ingress=True,original_clock_preserved=True,raw_outcome_preserved=True))
 rec=judgement('reconciliation','frw.Root.F06.first-effect-reconciliation.v1',dict(canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,closure=closure,effect_disposition='SENT_CONFIRMED_SAME_SOURCE_INGRESSED',unknown_assumed_absent=False,no_reupload=True,raw_failures_and_UNKNOWN_preserved=True,next_operation='ONE_SEPARATE_CORRECT_READ_NO_UPLOAD'))
 cust=judgement('custody','frw.Root.F06.first-upload-private-custody.v1',dict(ack=ar,original_identity=identity,retained_source_sha256=source['sha256'],downloaded_source_sha256=source['sha256'],original_and_retained_CAS_verified=True))
 ingress=judgement('ingress','frw.Root.F06.same-B-source-ingress.v1',dict(platform_message_id=11,file_id=ack['document']['file_id'],file_unique_id=ack['document']['file_unique_id'],native_message_ids=[1,2],source_reference_observed=True))
 first=tweak('first',dict(schema='frw.Root.F06.closed-first-upload.v1',operator='Root',status='ROOT_BOUND_CLOSED_RECONCILED',source_reference=sr,source=source,B=principal,source_identity=identity,canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,closure=closure,root_reconciliation=rec,private_custody=cust,native_ingress=ingress))
 fr=put('closed-first.json',first)
 s=A.construct_scenario(supplied_password='SYNTHETIC-ONLY-NOT-A-REAL-SECRET',first_dependency=first)
 c=A.unbound();c.update(status='ROOT_BOUND_EXACT_F06_CORRECTREAD',run_id='SYNTHETIC-correct',authority=dummy,authority_id='ordinary-independent-SYNTHETIC',source_reference=sr,first_ingress=fr,first_validator=dict(path=str(C/'first_ingress.py'),bytes=len(code[str(C/'first_ingress.py')]),sha256=A.digest(code[str(C/'first_ingress.py')])))
 c.update(scenario_ref=put('correct-scenario.json',s),scenario_sha256=A.digest(A.encoded(s)),adapter=put('adapter-placeholder',b'x',True),footer=put('footer-placeholder',b'x',True),actual_root_B_checker=dummy,root_current_proof=dummy)
 c['product']=dict(source_layers=207,project_files=495,native_files=17891,plugin_files=52,base_source_files=17730,source_receipt_sha256='1'*64,input_sha256='2'*64)
 c['installation']=dict(closure=dummy,source_acceptance=dummy,product=c['product'],runtime_hashes={'SYNTHETIC-only.py':'3'*64})
 c['boundary']={k:'4'*64 for k in A.BOUNDARY};c['boundary'].update(gateway={'pid':1,'start_time':1},B=dict(principal,native_max_id=2),phase_unconsumed=True,uploads_this_operation=0,producer_calls=0,restarts=0)
 c['resources']=dict(A.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=32*1024**2,clock=dummy,owned_parent_wait_cleanup=dummy)
 c['root_proofs']={k:dummy for k in A.PROOFS};c['root_proofs']['first_upload_reconciliation']=rec
 oracle=dict(schema='frw.Root.F06.correct-read-private-oracle.v1',operator='Root',status='ROOT_BOUND',source=source,source_reference=sr,phase=A.PHASE,scenario_sha256=c['scenario_sha256'],correct_secret_verified_for_same_source=True,actual_retained_first_paragraph_oracle=True,toy_placeholder_oracle=False,no_new_document_or_derivative=True,technical_secret_delta_review_required_after_reply=True,original_private_request_exemption_only=True,future_reply_acceptance='NOT_ESTABLISHED',retained_basis=[dummy])
 c['root_proofs']['correct_read_private_oracle']=put('oracle.json',tweak('oracle',oracle))
 return c,s,first,lambda p,**kw:data[str(p)],data
c,s,f,read,data=fixture()
ok('actual_compatible_memory_fixture_first_chain',F.validate(c,read)==f)
ok('separate_correct_private_oracle',F.private_oracle(c,read)['future_reply_acceptance']=='NOT_ESTABLISHED')
ok('full_bound_adapter_shape',A.shape(c,c['run_id'],s,read))
ok('original_full_v42_text_capture_schema',ns['validate_scenario'](s)==s)
ok('pure_constructor_zero_input_no_wire_ref',set(s['steps'][0])=={'request','observe'})
for family,changes in {
 'ack':[('wrong_peer',lambda d:d['chat'].update(id=2)),('wrong_sender',lambda d:d['from'].update(id=3)),('thread',lambda d:d.update(message_thread_id=1)),('wrong_size',lambda d:d['document'].update(file_size=2)),('caption',lambda d:d.update(caption='other'))],
 'run':[('unknown_send',lambda d:d.update(send_state='unknown')),('unfinished',lambda d:d.update(status='OBSERVING')),('second_send',lambda d:d.update(send_attempts=2)),('wrong_source',lambda d:d['scenario']['steps'][0]['input'].update(sha256='f'*64)),('continuation',lambda d:d.update(continuation_reference={'fake':True}))],
 'window':[('shortened',lambda d:d.update(window_seconds=30)),('reclock',lambda d:d.update(capture_until=182))],
 'closure':[('actor_unknown',lambda d:d.update(actor_tree_closed=False)),('slot_held',lambda d:d.update(slot_released=False))],
 'reconciliation':[('unknown_as_absent',lambda d:d.update(unknown_assumed_absent=True)),('no_disposition',lambda d:d.update(effect_disposition='ABSENT')),('reupload',lambda d:d.update(no_reupload=False))],
 'ingress':[('fake_sid',lambda d:d.update(B={'profile':'other'})),('wrong_message',lambda d:d.update(platform_message_id=13))],
 'custody':[('wrong_download',lambda d:d.update(downloaded_source_sha256='f'*64)),('unchecked',lambda d:d.update(original_and_retained_CAS_verified=False))],
 'binding':[('wrong_phase',lambda d:d.update(phase='DOCX-CORRECT-READ-SAME-UPLOAD')),('wrong_B',lambda d:d['boundary']['B'].update(session_id='other'))],
}.items():
 for name,fn in changes:
  x,_,_,r,_=fixture({family:fn});refuses('first_'+family+'_'+name,lambda x=x,r=r:F.validate(x,r))
for name,fn in [('placeholder',lambda d:d.update(toy_placeholder_oracle=True)),('not_correct',lambda d:d.update(correct_secret_verified_for_same_source=False)),('graded_early',lambda d:d.update(future_reply_acceptance='PASS')),('no_basis',lambda d:d.update(retained_basis=[]))]:
 x,_,_,r,_=fixture({'oracle':fn});refuses('oracle_'+name,lambda x=x,r=r:F.private_oracle(x,r))
for name,fn in [('upload',lambda d:d['steps'][0].update(input={'fake':True})),('wire_ref',lambda d:d['steps'][0].update(source_reference={'fake':True})),('reply_to',lambda d:d['steps'][0].update(reply_to_message_id=11)),('short_capture',lambda d:d['steps'][0]['observe'].update(window_seconds=30)),('outbound_doc',lambda d:d['steps'][0]['observe'].update(max_documents=1)),('other_chat',lambda d:d.update(peer_id=2)),('wrongcase_text',lambda d:d['steps'][0].update(request='wrong password request'))]:
 x=copy.deepcopy(s);fn(x);refuses('scenario_'+name,lambda x=x:A.scenario_shape(x))
for name,pw in [('empty',''),('newline','x\ny'),('unbound','UNBOUND'),('over_units','x'*256),('nonbmp_over','\U0001f642'*128),('surrogate','\ud800')]:refuses('password_'+name,lambda pw=pw:A.request_for(pw))
ok('password_exact255_utf16',bool(A.request_for('x'+'\U0001f642'*127)))
ok('unbound_source_product_no_current_claim',all(v is None for v in A.unbound()['product'].values()))
refuses('unbound_rejected_before_effect',lambda:A.contract_shape(A.unbound()))
x=copy.deepcopy(c);x['boundary']['uploads_this_operation']=1;refuses('contract_no_second_upload',lambda:A.contract_shape(x))
x=copy.deepcopy(c);x['root_proofs']['first_upload_reconciliation']=c['authority'];refuses('root_first_ref_mismatch',lambda:F.validate(x,read))
x=copy.deepcopy(c);x['source_reference']['run_sha256']='f'*64;refuses('wrong_canonical_source_hash',lambda:F.validate(x,read))
x=copy.deepcopy(c);x['boundary']['B']['session_id']='other';refuses('actual_new_B_must_match_first',lambda:F.validate(x,read))
ok('whole_effect_carries_dependency_and_private_scenario_hash',all(k in A.effect(c) for k in ('first_ingress','first_validator','source_reference','installation','scenario_sha256')))
x=copy.deepcopy(c);x['authority_id']='ordinary-independent-other';ok('authority_exclusion_no_cycle',A.effect(c)==A.effect(x))
# Exact original full consumer reconstruction: core Runner methods are identical
# except the already-reviewed ordinary current-admission seam. Footer subclasses.
out=A.successor(base,A.unbound(),footer);tree=ast.parse(out)
base_runner=next(n for n in fulltree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
new_runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
changed=[]
for a in base_runner.body:
 if isinstance(a,ast.FunctionDef):
  b=next(n for n in new_runner.body if isinstance(n,ast.FunctionDef) and n.name==a.name)
  if ast.dump(a,include_attributes=False)!=ast.dump(b,include_attributes=False):changed.append(a.name)
ok('original191_runner_core_only_admission_seam',changed==['ordinary_independent_admission'])
ok('original_send_custody_capture_process_unchanged',all(ast.dump(next(n for n in base_runner.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)==ast.dump(next(n for n in new_runner.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False) for name in ('_send','process','new','verify_capture_context','save','guard')))
# Authority cannot come from the old first phase or a memory/continuation grant.
auth=dict(authority_id=c['authority_id'],scope=c['scope'],run_scenarios={c['run_id']:c['scenario_sha256']},ordered_predecessors={},same_canonical_local_run=False)
ok('separate_new_ordinary_authority_shape',A.admission(c,auth))
for name,fn in [('wrong_scope',lambda d:d.update(scope='old-first')),('old_run',lambda d:d.update(run_scenarios={c['source_reference']['run_id']:c['scenario_sha256']})),('continuation',lambda d:d.update(ordered_predecessors={'old':'x'})),('memory',lambda d:d.update(memory_case={}))]:
 x=copy.deepcopy(auth);fn(x);refuses('authority_'+name,lambda x=x:A.admission(c,x))
print(json.dumps({'state':'PASS_PURE_SYNTHETIC_ONLY','count':len(checks),'checks':checks,'real_source_refs_ACKs_passwords_authorities':0,'native_or_Office_or_Telegram_or_H_reads':0,'unbound_full_consumer_bytes':len(out),'unbound_full_consumer_sha256':A.digest(out)},sort_keys=True))
