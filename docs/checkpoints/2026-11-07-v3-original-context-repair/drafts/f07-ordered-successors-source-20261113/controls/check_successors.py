"""Finite in-memory successor controls, genuine selected custody methods.
No actual Store/state/locks/DB/source fixture/current/native/API/clock is touched.
"""
import ast, copy, datetime as dt, fnmatch, hashlib, json, os, resource, signal, stat, sys, time, types
from pathlib import Path
from unittest.mock import patch
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));signal.alarm(300)
started=time.monotonic();D=Path(__file__).resolve().parents[1];B=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113')
checks=[];mem={}
def check(name,ok):assert ok,name;checks.append(name)
def reject(name,call,exception=(ValueError,)):
 try:call()
 except exception:checks.append(name)
 else:raise AssertionError(name)
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
prep=load(D/'source/f07_phase_prepare.py','prep');caller=load(D/'source/root_caller.py','caller');checker=load(D/'source/current209.py','checker');driver=load(D/'source/root_f07_once.py','driver')
base=Path(prep.SELECTED_TESTER).read_bytes();check('exact selected source',prep.digest(base)==prep.SELECTED_SHA)
def put(path,v):
 raw=prep.encoded(v);mem[str(path)]=raw;return dict(path=str(path),bytes=len(raw),sha256=prep.digest(raw))
def mread(ref,**kw):
 raw=mem[ref['path']];assert len(raw)==ref['bytes'] and prep.digest(raw)==ref['sha256'];return raw
def mdoc(ref,**kw):return prep.unique([]) if False else json.loads(mread(ref))
checker.read_reference=mread;checker.doc=mdoc;checker.module=lambda reference:prep
checker.read_saved_reference=lambda *a,**k:base
def index(raw):
 runner=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Runner')
 return {n.name:n for n in runner.body if isinstance(n,ast.FunctionDef)}
def dump(node):return ast.dump(node,include_attributes=False)
old=load(B/'source/f07_phase_prepare.py','oldprep')
compat_old=old.apply_history_compat(base);compat_new=prep.apply_history_compat(base)
check('entire accepted history compatibility and exact wholeprefix bytes unchanged',compat_old==compat_new)
for name in ('root_f07_once.py','current209.py','root_caller.py','f07_phase_prepare.py'):
 compile((D/'source'/name).read_bytes(),name,'exec')
 check('compiles '+name,True)
for name in ('new','_send','send','observe','cursor_offsets','receive_inventory','ordinary_independent_predecessor_checked'):
 check('genuine selected core unchanged '+name,dump(index(base)[name])==dump(index(compat_new)[name]))
for name in ('qualify_before_clock','execute','wait_owned','stop_reap','child_limits'):
 ot=ast.parse((B/'source/root_f07_once.py').read_bytes());nt=ast.parse((D/'source/root_f07_once.py').read_bytes())
 a=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name==name)
 if name=='execute':
  # Only one local return-tuple variable is added; every live effect statement stays.
  for n in ast.walk(b):
   if isinstance(n,ast.Tuple) and any(getattr(x,'id','')=='previous_phase' for x in n.elts):n.elts=[x for x in n.elts if getattr(x,'id','')!='previous_phase']
 check('finite lifecycle unchanged '+name,dump(a)==dump(b))
phases=[]
for ordinal in range(1,5):
 _,name,mime,size,want=prep.PHASES[ordinal-1]
 upload=dict(kind='document',path=str(Path(prep.SOURCE_BASE)/name),sha256=want,stat=dict(device=1,inode=ordinal,size_bytes=size,uid=os.getuid(),mtime_ns=1,ctime_ns=1),filename=name,mime_type=mime,caption=prep.REQUESTS[ordinal-1])
 phases.append(prep.phase_preparation(ordinal,upload))
saved=dict(result=dict(phases=phases))
for ordinal in (2,3,4):
 p,previous=caller.select_ordered_successor(prep,saved,ordinal=ordinal,scenario_raw=prep.encoded(phases[ordinal-1]['scenario']))
 check('exact successor selected '+str(ordinal),p==phases[ordinal-1] and previous==phases[ordinal-2])
for ordinal in (None,False,True,0,1,5,'2'):
 reject('invalid or phase1 selection refuses '+repr(ordinal),lambda o=ordinal:caller.select_ordered_successor(prep,saved,ordinal=o,scenario_raw=b'{}'))
for label,changed in [('missing',dict(result={})),('reordered',dict(result=dict(phases=[phases[1],phases[0],*phases[2:]]))),('truncated',dict(result=dict(phases=phases[:3])))]:
 reject('saved original array refuses '+label,lambda s=changed:caller.select_ordered_successor(prep,s,ordinal=2,scenario_raw=prep.encoded(phases[1]['scenario'])))
reject('wrong exact selected scenario refuses',lambda:caller.select_ordered_successor(prep,saved,ordinal=2,scenario_raw=prep.encoded(phases[2]['scenario'])))
check('production exact real phase1 anchor retained',caller.ORIGINAL_PHASE1_CANONICAL['sha256']=='1ca07cc37f9be0ead7b5ddcae24d7f0b9f18fad38922bdc4743046b5ba0d961b' and caller.ORIGINAL_PHASE1_REVIEW['sha256']=='b6b21c122204dcea22ff87905cb8e47e9773677b737ea2c33069d0d27edfff2b')

class VPath:
 """In-memory path adapter: no real OS path method is ever called."""
 def __init__(self,path):self.path=str(path)
 def __str__(self):return self.path
 def __fspath__(self):return self.path
 def __truediv__(self,other):return VPath(self.path.rstrip('/')+'/'+str(other))
 def __eq__(self,other):return self.path==str(other)
 def __hash__(self):return hash(self.path)
 def __lt__(self,other):return self.path<str(other)
 @property
 def name(self):return self.path.rsplit('/',1)[-1]
 @property
 def parent(self):return VPath(self.path.rsplit('/',1)[0] or '/')
 @property
 def parents(self):return [VPath(str(p)) for p in Path(self.path).parents]
 def exists(self):return self.path in mem
 def is_symlink(self):return False
 def is_relative_to(self,other):return Path(self.path).is_relative_to(Path(str(other)))
 def read_text(self):return mem[self.path].decode()
 def glob(self,pattern):return sorted([VPath(p) for p in mem if str(Path(p).parent)==self.path and fnmatch.fnmatch(Path(p).name,pattern)])
 def iterdir(self):return self.glob('*')
 def stat(self):return types.SimpleNamespace(st_dev=1,st_ino=1,st_mode=stat.S_IFREG|0o600,st_nlink=1,st_uid=os.getuid(),st_gid=os.getgid(),st_size=len(mem[self.path]),st_mtime_ns=1,st_ctime_ns=1)
class VStore:
 def __init__(self,root):self.root=VPath(root);self.runs=self.root/'runs';self.captures=self.root/'updates';self.downloads=self.root/'downloads'
 def run_path(self,rid):return self.runs/(rid+'.json')
 def get(self,path,default=None):return json.loads(mem[str(path)]) if str(path) in mem else default
 def save(self,*args,**kwargs):raise AssertionError('NO SYNTHETIC SAVE ALLOWED')
def localref(path):
 raw=mem[str(path)];return dict(basename=Path(str(path)).name,bytes=len(raw),sha256=prep.digest(raw))
def vmread(path,*args,**kw):
 try:return mem[str(path)]
 except KeyError:raise FileNotFoundError('synthetic-memory-only') from None
def previous_fixture(phase,rid):
 store=VStore('/SYNTHETIC-CUSTODY');upload=phase['scenario']['steps'][0]['input'];bodysha='c'*64
 run=dict(id=rid,scenario=phase['scenario'],scenario_sha256=phase['scenario_sha256'],step=0,status='EVIDENCE_READY',send_state='sent',send_attempts=1,sent_ids=[20],sent_message_id=20,sent_date=110,sent_at=110,send_intent_at=90,send_dispatch_at=100,send_timeout_seconds=30,capture_until=290,deadline=400,capture_window_complete=True,reply_text_acceptance='RECEIVED_UNGRADED',capture_start_offset=100,reply_capture_prior_tracking={},seen=[100],message_ids=[21],update_count=1)
 ack=dict(chat=dict(id=8751854128,type='private'),message_id=20,date=110,**{'from':dict(id=8812646969,is_bot=True)},caption=upload['caption'],document=dict(file_id='synthetic-file',file_unique_id='synthetic-unique',file_size=upload['stat']['size_bytes']))
 ackpath=store.root/('send-ack-'+rid+'-0-1.json');put(ackpath,ack);run['sent_api_ack_reference']=dict(localref(ackpath),representation='decoded-message-json')
 meta=dict(method='sendDocument',chat_id='@jerichodevbot',input_sha256=upload['sha256'],input_bytes=upload['stat']['size_bytes'],input_stat=upload['stat'],filename=upload['filename'],mime_type=upload['mime_type'],caption=upload['caption'],content_type='multipart/form-data; boundary=frw-'+'d'*64,body_sha256=bodysha,body_bytes=upload['stat']['size_bytes']+100,scenario_sha256=phase['scenario_sha256'])
 run['request_metadata']=meta;taskpath=store.root/('send-task-'+rid+'-0-1.json');put(taskpath,meta);run['sent_task_reference']=localref(taskpath)
 window=dict(run_id=rid,scenario_sha256=phase['scenario_sha256'],step=0,send_attempts=1,sent_message_id=20,sent_at=110,send_intent_at=90,capture_until=290,window_seconds=180,deadline=400,send_dispatch_at=100,send_timeout_seconds=30,ack=run['sent_api_ack_reference'],task=run['sent_task_reference'],continuation=None)
 winpath=store.root/('send-window-'+rid+'-0-1.json');put(winpath,window);run['sent_window_reference']=localref(winpath)
 binding=dict(run_id=rid,scenario_sha256=phase['scenario_sha256'],step=0,sent_message_id=20,sent_ids=[20],request_body_sha256=bodysha)
 context=dict(binding,tester_id=8812646969,peer_id=8751854128,window=run['sent_window_reference'],deadline=400,capture_start_offset=100,prior_tracking={})
 text='Safe malformed rejection' if phase['ordinal']==3 else 'Truthful supported document summary'
 update=dict(update_id=100,message=dict(message_id=21,date=120,chat=dict(id=8751854128,type='private'),**{'from':dict(id=8751854128,is_bot=True)},reply_to_message=dict(message_id=20),text=text))
 rawpath=store.captures/'100.json';put(rawpath,update);rawref=localref(rawpath)
 arrival=dict(context=context,update_id=100,raw_update=rawref,arrived_at=120);arrivalpath=store.captures/'100.arrival.json';put(arrivalpath,arrival)
 obs=dict(binding,kind='reply_text',update_id=100,message_id=21,text=text,text_sha256=prep.digest(text.encode()),date=120,raw_update=rawref)
 receiptpath=store.downloads/(rid+'-21-'+obs['text_sha256']+'.text-receipt.json');put(receiptpath,obs);obs.update(receipt_path=str(receiptpath),receipt_sha256=prep.digest(mem[str(receiptpath)]),receipt_bytes=len(mem[str(receiptpath)]));run['observations']=[obs]
 terminalpath=store.root/('terminal-response-'+rid+'-0-1.json');put(terminalpath,dict(ok=True,result=[]))
 records=[dict(kind='seed',offset=100,legacy_heads={}),dict(kind='capture',offset=101,update_id=100,raw_update=rawref,arrival=localref(arrivalpath)),dict(kind='processing',offset=101,update_id=100),dict(kind='processed',offset=101,update_id=100,observations=[obs],message_ids=[21]),dict(kind='terminal_intent',offset=101,started_at=290,timeout_seconds=10,update_count=1,limit=20),dict(kind='terminal_response',offset=101,received_at=291,wire=localref(terminalpath)),dict(kind='terminal_complete',offset=101,completed_at=292)]
 prior=None
 for i,r in enumerate(records):
  r.update(context=context,sequence=i,previous=prior);path=store.root/('receive-'+rid+'-0-1-'+str(i)+'.json');put(path,r);prior=localref(path)
 run.update(receive_sequence=6,receive_head=prior);cursor=dict(offset=101,capture_receipts={rid+'-0-1':prior});put(store.root/'cursor.json',cursor)
 put(store.run_path(rid),run)
 return store,run,ack,rawpath

phase_results=[]
for ordinal in (2,3,4):
 mem.clear();phase=phases[ordinal-1];previous=phases[ordinal-2];rid='synthetic-successor-'+str(ordinal);prid='synthetic-phase-'+str(ordinal-1)
 store,run,ack,rawpath=previous_fixture(previous,prid)
 canonical=put(str(checker.STATE/'runs'/(prid+'.json')),run)
 # Genuine saved assessment -> existing bridge -> exact saved review, all memory.
 priorbinding=dict(run_id='synthetic-earlier',scenario_sha256=phases[ordinal-3]['scenario_sha256'] if ordinal>2 else 'a'*64,run_record_sha256='a'*64,review=dict(path='/SYNTHETIC/earlier-review.json',sha256='b'*64),review_schema='frw.Root.F07.semantic-custody-review.v1',initially_absent=False)
 if ordinal==3:
  priorbinding.update(run_id=Path(caller.ORIGINAL_PHASE1_CANONICAL['path']).stem,run_record_sha256=caller.ORIGINAL_PHASE1_CANONICAL['sha256'],review={k:caller.ORIGINAL_PHASE1_REVIEW[k] for k in ('path','sha256')})
 oldauthority=dict(ordered_predecessors={prid:priorbinding},f07_original_case=dict(case_id='F-07',case_index=168,phase=previous['phase'],ordinal=previous['ordinal'],controlled_fault_sequence_not_replay=True,prospective_fixture_not_original=True))
 oldaref=put('/SYNTHETIC/old-authority.json',oldauthority)
 effect=dict(run_id=prid,phase=previous,installation_closure=dict(path='/SYNTHETIC/install',bytes=1,sha256='a'*64),authority=oldaref)
 observed=dict(gateway=dict(pid=1),databases=dict(tester=dict(max_message_id=10)),technical_log_cursor={},installed=dict(runtime_hashes={}))
 evidence=dict(canonical_run=canonical,ACK=put('/SYNTHETIC/'+run['sent_api_ack_reference']['basename'],ack),capture=put('/SYNTHETIC/capture.json',{}),technical_carriers=put('/SYNTHETIC/carriers.json',{}),native_host_close=put('/SYNTHETIC/close.json',{}))
 sourceproof=put('/SYNTHETIC/source-ref.json',{});ingress=dict(schema='frw.Root.F07.actual-native-ingress-correlation.v1',operator='Root',run_id=prid,tester_ACK_message_id=20,native_principal=checker.PRINCIPAL,native_platform_message_id=77,native_message_row_id=11,source_sha256=previous['scenario']['steps'][0]['input']['sha256'],filename=previous['scenario']['steps'][0]['input']['filename'],actual_source_ref_custody_checked=True,actual_source_ref_evidence=sourceproof)
 evidence['native_ingress']=put('/SYNTHETIC/ingress.json',ingress)
 # Root assessment bridge ACK envelope custody joins canonical basename/bytes/hash.
 evidence['ACK']=dict(evidence['ACK'],sha256=run['sent_api_ack_reference']['sha256'],bytes=run['sent_api_ack_reference']['bytes'])
 assessment=dict(schema='frw.Root.F07.actual-postcondition-assessment.v1',operator='Root',status='ROOT_ASSESSED_SAVED_ACTUAL_ONLY',plan=checker.postcondition_plan(effect,observed),extra_event_or_replay_performed=False,evidence=evidence,raw_status='EVIDENCE_READY',raw_send_state='sent',raw_consumer_acceptance='NOT_ESTABLISHED',verdicts=dict(semantic='PASS',custody='PASS',privacy='NOT_ESTABLISHED',native_host_close='PASS'),per_logging_site={k:dict(execution='NOT_OBSERVED',verdict='NOT_ESTABLISHED',evidence=[]) for k in checker.LOGGING_SITES})
 assessmentref=put('/SYNTHETIC/assessment.json',assessment)
 review=caller.actual_predecessor_review(checker,effect=effect,observed=observed,assessment=assessment,assessment_ref=assessmentref);reviewref=put('/SYNTHETIC/review.json',review)
 proof=checker.unbound_proof();proof.update(status='ROOT_BOUND',effect=effect,observed=observed,whole_effect_sha256=checker.digest(checker.encoded(effect)));proofref=put('/SYNTHETIC/proof.json',proof)
 descriptorref=put('/SYNTHETIC/effect-consumer.json',dict(effect=effect,proof=proofref))
 bundle=dict(canonical_run=canonical,review=reviewref,effect_and_consumer=descriptorref,proof=proofref,assessment=assessmentref)
 binding=caller.immediate_predecessor_binding(checker,canonical_run_ref=canonical,review_ref=reviewref)
 authority=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,authority_id='synthetic-not-issued',run_scenarios={rid:phase['scenario_sha256']},history={prid:dict(sha256=prep.digest(prep.encoded(run)),status='EVIDENCE_READY',send_state='sent',deadline=400,new_effect_replay_authorized=False,unknown_retained=False)},unknown_effects_resolved=False,old_rows_modified=False,new_trial_for_historical_task=False,product_or_B00_acceptance=False,ordered_predecessors={rid:binding},f07_original_case=dict(case_id='F-07',case_index=168,phase=phase['phase'],ordinal=ordinal,controlled_fault_sequence_not_replay=True,prospective_fixture_not_original=True),created_at=499,expires_at=700,boot_id='synthetic-boot',new_independent_inputs_only=True,no_old_task_replay=True,gateway=dict(state_path='/SYNTHETIC/gateway.json',pid=42,start_time=7,maximum_staleness_seconds=30))
 aref=put('/SYNTHETIC/authority.json',authority)
 # Substitute anchor pins only inside synthetic stand; production pins checked above.
 if ordinal==2:caller.ORIGINAL_PHASE1_CANONICAL=canonical;caller.ORIGINAL_PHASE1_REVIEW=reviewref
 check('actual bridge bundle accepted '+str(ordinal),caller.accepted_successor_predecessor(checker,phase=phase,previous_phase=previous,original_phases=phases,run_id=rid,authority=authority,bundle=bundle)==previous)
 def accept(b=bundle,a=authority,p=previous):return caller.accepted_successor_predecessor(checker,phase=phase,previous_phase=p,original_phases=phases,run_id=rid,authority=a,bundle=b)
 reject('absent predecessor bundle '+str(ordinal),lambda:accept(b={}))
 reject('wrong predecessor original phase '+str(ordinal),lambda:accept(p=phases[(ordinal-1)%4]))
 reject('wrong authority predecessor '+str(ordinal),lambda:accept(a=dict(authority,ordered_predecessors={})))
 bad=dict(review,semantic='FAIL');badref=put('/SYNTHETIC/bad-review.json',bad)
 reject('hand-shaped or failed saved review '+str(ordinal),lambda:accept(b=dict(bundle,review=badref)))
 bad=dict(review,schema='synthetic-untrusted-PASS');badref=put('/SYNTHETIC/bad-schema-review.json',bad)
 reject('wrong schema PASS review '+str(ordinal),lambda:accept(b=dict(bundle,review=badref)))
 for status in ('STOPPED','PARTIAL','RECOVERED_PARTIAL_CAPTURE'):
  changed=dict(run,status=status);changedref=put('/SYNTHETIC/changed-run.json',changed)
  reject('raw '+status+' not converted '+str(ordinal),lambda r=changed:prep.predecessor_binding(r,reviewref,review_schema=review['schema'],run_raw=prep.encoded(r)))
 for label,change in [('nonfull',dict(capture_window_complete=False)),('179seconds',dict(capture_until=289)),('2sends',dict(send_attempts=2))]:
  changed=dict(run,**change)
  reject(label+' cannot be predecessor '+str(ordinal),lambda r=changed:prep.predecessor_binding(r,reviewref,review_schema=review['schema'],run_raw=prep.encoded(r)))
 ordinary=prep.compose_source(base,phase,run_id=rid,authority_ref=aref,authority=authority,previous_phase=previous)
 for label,a,p in [('absent',dict(authority,ordered_predecessors={}),previous),('wrongphase',authority,phase),('falsecase',dict(authority,f07_original_case={}),previous)]:
  ar=put('/SYNTHETIC/bad-authority.json',a)
  reject('ordinary composition refuses '+label+' '+str(ordinal),lambda a=a,p=p,ar=ar:prep.compose_source(base,phase,run_id=rid,authority_ref=ar,authority=a,previous_phase=p))
 # Full genuine ordinary module remains inert. All runtime IO maps to memory.
 m=types.ModuleType('synthetic_genuine');m.__file__='/SYNTHETIC/ordinary.py';exec(compile(ordinary,m.__file__,'exec'),m.__dict__)
 m.safe_read=vmread;m.Path=VPath
 put('/SYNTHETIC/gateway.json',dict(pid=42,start_time=7,gateway_state='running',active_agents=0,active_work=None,restart_requested=False,session_store=dict(status='ok'),platforms=dict(telegram=dict(state='connected',needs_attention=False,writer_pid=42,writer_start_time=7)),updated_at=dt.datetime.fromtimestamp(500,dt.timezone.utc).isoformat()))
 mem['/proc/sys/kernel/random/boot_id']=b'synthetic-boot\n';mem['/proc/42/stat']=(' '.join(['0']*21+['7'])).encode()
 runner=m.Runner(store,None,clock=lambda:500,sleep=lambda _:(_ for _ in ()).throw(AssertionError('NO SLEEP')))
 check('earliest ordinary exact current ACK30 '+str(ordinal),runner.send_ack_budget(dict(id=rid,scenario_sha256=phase['scenario_sha256']))==30)
 check('earliest ordinary actual immediate ACK30 '+str(ordinal),runner.send_ack_budget(run)==30)
 check('earliest older unrelated ACK10 '+str(ordinal),runner.send_ack_budget(dict(id='unrelated',scenario_sha256=previous['scenario_sha256']))==10)
 check('earliest wrong scenario ACK10 '+str(ordinal),runner.send_ack_budget(dict(id=prid,scenario_sha256='e'*64))==10)
 reject('legacy ACK override refuses '+str(ordinal),lambda:runner.send_ack_budget(dict(id='unrelated',new_ack_timeout_seconds=30)),(m.Refused,))
 runner.verify_reply_custody(run)
 check('complete genuine ACK task window cursor raw receipt chain '+str(ordinal),True)
 checked=runner.ordinary_independent_predecessor_checked(binding)
 check('genuine predecessor method complete custody '+str(ordinal),checked==run)
 qualified=caller.qualify_selected_ordinary_readonly(runner,run_id=rid,phase=phase)
 check('genuine whole10 prefix with actual predecessor ACK30 '+str(ordinal),qualified['state']=='WHOLE_ORIGINAL_NEW_PREFIX_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION' and qualified['save_called'] is False)
 originalauthority=m.Runner.ORDINARY_INDEPENDENT_AUTHORITY
 for label,changed in [('expired',dict(authority,expires_at=500)),('not-yet-current',dict(authority,created_at=501)),('unaccepted',dict(authority,accepted=False))]:
  m.Runner.ORDINARY_INDEPENDENT_AUTHORITY=put('/SYNTHETIC/'+label+'-authority.json',changed)
  reject('whole prefix stale or unbound authority '+label+' '+str(ordinal),lambda:caller.qualify_selected_ordinary_readonly(runner,run_id=rid,phase=phase),(m.Refused,))
 m.Runner.ORDINARY_INDEPENDENT_AUTHORITY=originalauthority
 # Independent immutable window corruption and missing raw fail actual methods.
 originalraw=mem[str(rawpath)];mem[str(rawpath)]=b'{}'
 reject('genuine raw substitution refuses '+str(ordinal),lambda:runner.ordinary_independent_predecessor_checked(binding),(m.Refused,))
 mem[str(rawpath)]=originalraw
 oldbudget=m.Runner.send_ack_budget;m.Runner.send_ack_budget=lambda self,row:10
 reject('meaningful control old earliest10 refuses predecessor30 '+str(ordinal),lambda:runner.ordinary_independent_predecessor_checked(binding),(m.Refused,))
 m.Runner.send_ack_budget=oldbudget
 # Continuation own immutable timeout takes precedence over ordinary exact mapping.
 originalreceipt=runner.continuation_receipt;runner.continuation_receipt=lambda row:(dict(ack_timeout_seconds=12),[],{})
 check('continuation admission retains own12 '+str(ordinal),runner.send_ack_budget(dict(run,new_ack_timeout_seconds=12,continuation_reference={}))==12)
 reject('continuation mismatched override refuses '+str(ordinal),lambda:runner.send_ack_budget(dict(run,new_ack_timeout_seconds=30,continuation_reference={})),(m.Refused,))
 runner.continuation_receipt=originalreceipt
 checkerref=checker.ref(D/'source/current209.py');proofnotissued=dict(path='/SYNTHETIC/NOT-ISSUED-FUTURE-PROOF.json',bytes=1,sha256='f'*64)
 final=caller.compose_consumer(checker,base,effect=dict(phase=phase,run_id=rid,authority=aref,checker=checkerref),authority=authority,proof_ref=proofnotissued,previous_phase=previous)
 compile(final,'<UNEXECUTED-final-consumer>','exec')
 check('nearest final caller preserves genuine original new '+str(ordinal),dump(index(final)['new'])==dump(index(base)['new']))
 check('future proof remains exact preintent NEW/SEND gate '+str(ordinal),'_f07.check(' in ast.unparse(index(final)['ordinary_independent_admission']))
 phase_results.append(dict(ordinal=ordinal,phase=phase['phase'],state='SYNTHETIC_COMPLETE_CUSTODY_SOURCE_PASS',actual_run=False))

# Driver pure shape and source path: malformed/unbound inputs never start effects.
reject('default unbound driver refuses',lambda:driver.validate({}))
tree=ast.parse((D/'source/root_f07_once.py').read_bytes());fs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
text=ast.unparse(fs['owned_consumer']);check('actual child forwards exact selected previous phase','previous_phase=previous_phase' in text and 'previous_phase=None' not in text)
text=ast.unparse(fs['source_inputs']);check('source_inputs forwards explicit ordinal and genuine bundle','ordinal=v[\'phase_ordinal\']' in text and 'accepted_successor_predecessor(' in text and 'phases[0]' not in text)
check('one child and one runner new/send/observe call only',sum(isinstance(n,ast.Call) and getattr(n.func,'attr','')=='Popen' for n in ast.walk(fs['execute']))==1 and all(sum(isinstance(n,ast.Call) and getattr(n.func,'attr','')==name and getattr(getattr(n.func,'value',None),'id','')=='runner' for n in ast.walk(fs['owned_consumer']))==1 for name in ('new','send','observe')))
result=dict(schema='frw.F07.ordered-successor-source-controls.v1',state='SOURCE_ONLY_SYNTHETIC_PASS_NOT_ACTUAL_GRANT',checks=checks,count=len(checks),phases=phase_results,elapsed_seconds=time.monotonic()-started,resources=dict(cpu_seconds=120,wall_seconds=300,address_space_bytes=512*1024**2,disk_limit_bytes=100*1024**2),actual_Store_native_DB_current_API_model_send_clock=False,adapters=['VPath/VStore and safe_read are memory-only; genuine whole-prefix, admission, predecessor, ACK, window, cursor, capture, receive and reply custody methods execute unchanged','Actual phase1 anchor pins are asserted, then replaced only in synthetic module stand by synthetic canonical/review pins','checker reads only memory artifacts; current proof collection, effect_shape and installed observations are not invoked'])
with (D/'controls/SUCCESSOR-CONTROLS-133.json').open('xb') as output:output.write(prep.encoded(result))
print(json.dumps(dict(state=result['state'],count=len(checks),elapsed_seconds=result['elapsed_seconds'])))
