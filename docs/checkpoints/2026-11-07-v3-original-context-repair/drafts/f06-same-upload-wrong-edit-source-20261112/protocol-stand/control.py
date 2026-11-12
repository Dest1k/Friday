"""Task30 owned isolated synthetic full caller protocol. No runtime acceptance.
Exact reviewed caller main/execute; real pinned adapter and dependency validators.
Only declared fake fixture constants/host-observation seams may be substituted.
"""
import ast, contextlib, datetime, fcntl, hashlib, io, json, locale, math, os
import pathlib, re, resource, signal, socket, sqlite3, stat, subprocess, sys, time, types
import encodings.unicode_escape, encodings.utf_8, encodings.ascii, encodings.utf_16_le
from pathlib import Path
os.umask(0o077)
HERE=Path(__file__).resolve().parent
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
CASE=HERE/'cases'/sys.argv[1];CASE.mkdir(mode=0o700,parents=True)
CONTROL=sys.argv[2];SNAPSHOT=HERE/(sys.argv[3] if len(sys.argv)>3 else 'fixed-source')
AUDIT={'opens':[],'denied':[],'imports':[],'metadata':[],'real_subprocess':0,'network':0};EVENTS=[]
def check(ok,why):
 if not ok:raise AssertionError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def audit(event,args):
 if event=='open':
  path=args[0]
  if isinstance(path,int):return
  absolute=os.path.abspath(os.fsdecode(path));flags=args[2]
  if absolute==str(BASE):
   if isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('AUDIT_STATIC_BASE_WRITE_DENIED')
  elif not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
   AUDIT['denied'].append(['open',absolute]);raise RuntimeError('AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED')
  AUDIT['opens'].append(absolute)
 elif event=='import':AUDIT['imports'].append(args[0]);AUDIT['denied'].append(['import',args[0]]);raise RuntimeError('AUDIT_POST_PREWARM_IMPORT_DENIED')
 elif event.startswith('socket.'):
  AUDIT['network']+=1;AUDIT['denied'].append([event]);raise RuntimeError('AUDIT_NETWORK_DENIED')
 elif event in ('subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.forkpty','pty.spawn') or event.startswith('os.exec'):
  AUDIT['real_subprocess']+=1;AUDIT['denied'].append([event]);raise RuntimeError('AUDIT_REAL_ACTOR_DENIED')
 elif event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.link','os.symlink','os.truncate'):
  for item in args[:2]:
   if isinstance(item,(str,bytes)):
    absolute=os.path.abspath(os.fsdecode(item))
    if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
     AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_MUTATION_DENIED')
 elif event in ('os.listdir','os.scandir') and not isinstance(args[0],int):
  absolute=os.path.abspath(os.fsdecode(args[0]))
  if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
   AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_DIRECTORY_READ_DENIED')
sys.addaudithook(audit)
ancestors={str(p) for p in (*HERE.parents,*BASE.parents)}
def metadata(fn,event):
 def call(path,*args,**kw):
  if not isinstance(path,int):
   absolute=os.path.abspath(os.fsdecode(path))
   if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/') or absolute==str(BASE) or absolute in ancestors):
    AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_METADATA_DENIED')
   AUDIT['metadata'].append([event,absolute])
  return fn(path,*args,**kw)
 return call
os.stat=metadata(os.stat,'stat');os.lstat=metadata(os.lstat,'lstat');os.readlink=metadata(os.readlink,'readlink')
def put(path,v,raw=False):
 path=CASE/path if not isinstance(path,Path) or not path.is_absolute() else path
 path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);data=v if raw else encoded(v)
 path.write_bytes(data);path.chmod(0o600);return {'path':str(path),'bytes':len(data),'sha256':sha(data)}
def jread(ref):return json.loads(Path(ref['path']).read_bytes())
def refresh(ref,v):return put(Path(ref['path']),v)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
own=CASE/'source';own.mkdir(mode=0o700)
pins={}
for leaf in ('root_bind_dispatch_once.py','f06_source.py','current_root.py','f06_footer.py.txt','first_ingress.py'):
 raw=(SNAPSHOT/leaf).read_bytes();put(own/leaf,raw,True);pins[leaf]={'bytes':len(raw),'sha256':sha(raw)}
M=module(own/'root_bind_dispatch_once.py','SYNTHETIC_TASK30_REAL_CALLER')
A=module(own/'f06_source.py','SYNTHETIC_TASK30_REAL_ADAPTER_FIXTURE')
F=module(own/'first_ingress.py','SYNTHETIC_TASK30_REAL_VALIDATOR_FIXTURE')
fakeproc=CASE/'SYNTHETIC-proc';put(fakeproc/'sys/kernel/random/boot_id',b'SYNTHETIC-BOOT-ID\n',True)
class SyntheticPathMeta(type):
 def __instancecheck__(cls,obj):return isinstance(obj,Path)
class SyntheticPath(type(Path()),metaclass=SyntheticPathMeta):
 def __init__(self,*args):
  if args and str(args[0]).startswith('/proc') and (str(args[0])=='/proc' or str(args[0]).startswith('/proc/')):args=(str(fakeproc)+str(args[0])[5:],*args[1:])
  super().__init__(*args)
M.Path=SyntheticPath;M.STATE=SyntheticPath(CASE/'SYNTHETIC-STATE');F.STATE=Path(M.STATE)
(M.STATE/'runs').mkdir(mode=0o700,parents=True)
for leaf in ('consumer.lock','tester-token'):put(M.STATE/leaf,b'',True)
M.SLOT=CASE/'SYNTHETIC-shared-slot.lock';put(M.SLOT,b'',True)
M.AUTHORITY_DIR=CASE/'SYNTHETIC-AUTHORITY';M.AUTHORITY_DIR.mkdir(mode=0o700)
M.PYTHON='/SYNTHETIC/NEVER-EXECUTED-PYTHON'
fake_source=dict(A.SOURCE,path=str(CASE/'SYNTHETIC-retained-descriptor-NEVER-OPENED.docx'));A.SOURCE=fake_source
installed=put('SYNTHETIC-installed-static-placeholder.py',b'# SYNTHETIC never imported\n',True)
A.INSTALLED_TESTER=Path(installed['path']);A.INSTALLED_TESTER_SHA=installed['sha256']
# The canonical path root is a fixture constant. Functions still execute the
# unchanged pinned validator bytes with exact actual read/ref joins.
class FixtureGlobals(dict):
 def __setitem__(self,key,value):
  if key=='STATE':value=Path(M.STATE);EVENTS.append(['SYNTHETIC-validator-STATE-injection'])
  super().__setitem__(key,value)
class FixtureModule:
 def __init__(self,name):object.__setattr__(self,'scope',FixtureGlobals(__name__=name))
 @property
 def __dict__(self):return self.scope
 def __getattr__(self,k):return self.scope[k]
 def __setattr__(self,k,v):self.scope[k]=v
A.types=types.SimpleNamespace(ModuleType=FixtureModule)
# Reuse only compact pure first-upload fixture, no old current/authority state.
closed_first_clock_ref={'path':str(CASE/'SYNTHETIC-old-first-clock-NEVER-READ.json'),'bytes':123,'sha256':'e'*64}
closed_correct_clock_ref={'path':str(CASE/'SYNTHETIC-old-correct-clock-NEVER-READ.json'),'bytes':124,'sha256':'f'*64}
ns={'CLOSED_FIRST_CLOCK_REF':closed_first_clock_ref,'A':A,'F':F,'C':own,'code':{str(own/'first_ingress.py'):(own/'first_ingress.py').read_bytes()},'json':json}
fixture_raw=(HERE/'first_fixture.py').read_text()
fixture_raw=fixture_raw.replace("'/SYNTHETIC-T28-ONLY/'+name","str(CASE/'first-fixture'/name)")
fixture_raw=fixture_raw.replace("s=A.construct_scenario(supplied_password='SYNTHETIC-ONLY-NOT-A-REAL-SECRET',first_dependency=first)","s=dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=300,max_updates=65,pace_seconds=1,steps=[{'request':'SYNTHETIC-CORRECT-READ-OLD-REQUEST','observe':dict(A.OBSERVE)}])")
fixture_raw=fixture_raw.replace('authority=dummy,boundary=',"authority=dummy,resources={'clock':CLOSED_FIRST_CLOCK_REF},boundary=")
ns['CASE']=CASE
exec(compile(fixture_raw,str(HERE/'first_fixture.py'),'exec'),ns)
fixture_mods={}
# These mutate the fake source before hashes/joins are constructed, so actual
# semantic gates, rather than merely stale ref hashes, must reject them.
if CONTROL=='first_ack_missing':fixture_mods['first']=lambda d:d.update(ack=None)
elif CONTROL=='first_user_missing':fixture_mods['ack']=lambda d:d.pop('from')
elif CONTROL=='first_chat_missing':fixture_mods['ack']=lambda d:d.pop('chat')
elif CONTROL=='first_source_missing':fixture_mods['first']=lambda d:d['source_reference'].pop('input_sha256')
elif CONTROL=='first_ack_user':fixture_mods['ack']=lambda d:d['from'].update(id=1)
elif CONTROL=='first_ack_chat':fixture_mods['ack']=lambda d:d['chat'].update(id=1)
elif CONTROL=='first_ingress_missing':fixture_mods['ingress']=lambda d:d.update(native_message_ids=[])
elif CONTROL=='first_source_mismatch':fixture_mods['first']=lambda d:d['source_reference'].update(input_sha256='0'*64)
c,_,first,_,data=ns['fixture'](fixture_mods)
for path,raw in data.items():put(Path(path),raw,True)
# Candidate-specific correct-read assessment fixture is constructed below.
work=CASE/'work';work.mkdir(mode=0o700)
dummy=put('SYNTHETIC-proof-basis.json',{'SYNTHETIC':'not a real authority/private semantic judgment'})
principal=first['B'];rid='SYNTHETIC-correct-read-closed';sr=c['source_reference']
change={'kind':'literal_replace','old':'SYNTHETIC old literal «one»','new':'SYNTHETIC new literal "two"','expected_occurrences':1}
correct={'schema':'frw.Root.F06.closed-correct-read.v1','operator':'Root','status':'ROOT_BOUND_CORRECT_READ_ACCEPTED','source':fake_source,'source_reference':sr,'B':principal}
scenario=A.construct_scenario(supplied_password='SYNTHETIC-DELIBERATELY-WRONG-NOT-A-SECRET',change_spec=change,first_dependency=first,correct_dependency=correct)
if CONTROL=='change_authorization_mismatch':change['new']='SYNTHETIC different authorized replacement'
elif CONTROL=='change_unbounded':change['expected_occurrences']=2
c['change_spec']=put('SYNTHETIC-change-spec.json',change)
c['scenario_ref']=put('SYNTHETIC-wrongedit-scenario.json',scenario);c['scenario_sha256']=c['scenario_ref']['sha256']
c.update(status='UNBOUND_NOT_GRANTED',authority=None,authority_id='UNBOUND',run_id='SYNTHETIC-wrongedit-future')
# Retained old request is fake fixture data, never an actual historical secret.
old_request='В ранее присланном в этой беседе защищённом DOCX f06-new-encrypted.docx используй тестовый пароль «SYNTHETIC-OLD-CORRECT-NOT-A-SECRET» и прочитай только первый абзац. Не изменяй документ, не создавай расшифрованную копию или новые файлы. Не включай пароль в ответ, не запоминай его отдельно и не подбирай другие пароли.'
old_scenario={'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot','deadline_seconds':300,'max_updates':65,'pace_seconds':1,'steps':[{'request':old_request,'observe':dict(A.OBSERVE)}]};oldsha=sha(encoded(old_scenario))
def stored(name,value,rep=None):
 ref=put(Path(M.STATE)/name,value);recorded={'basename':name,'bytes':ref['bytes'],'sha256':ref['sha256']}
 if rep:recorded['representation']=rep
 return ref,recorded
ack={'message_id':31,'date':301,'chat':{'id':8751854128,'type':'private'},'from':{'id':8812646969,'is_bot':True},'text':old_request}
if CONTROL=='correct_user_missing':ack.pop('from')
elif CONTROL=='correct_chat_missing':ack.pop('chat')
elif CONTROL=='correct_ack_user':ack['from']['id']=1
elif CONTROL=='correct_ack_chat':ack['chat']['id']=1
elif CONTROL=='correct_ack_document':ack['document']={'SYNTHETIC':'unwanted'}
ar,asr=stored('send-ack-'+rid+'-0-1.json',ack,'decoded-message-json')
params={'chat_id':'@jerichodevbot','text':old_request};task={'method':'sendMessage','params':params,'body_sha256':sha(encoded(params)),'body_bytes':len(encoded(params)),'scenario_sha256':oldsha}
tr,tsr=stored('send-task-'+rid+'-0-1.json',task)
window={'run_id':rid,'scenario_sha256':oldsha,'step':0,'send_attempts':1,'send_intent_at':300,'send_dispatch_at':300,'send_timeout_seconds':10,'deadline':600,'sent_at':301,'sent_message_id':31,'ack':asr,'task':tsr,'window_seconds':180,'capture_until':481}
wr,wsr=stored('send-window-'+rid+'-0-1.json',window)
terminal={'kind':'terminal_complete','sequence':0,'context':{'run_id':rid,'scenario_sha256':oldsha,'window':wsr,'sent_message_id':31,'deadline':600}}
hr,hsr=stored('receive-'+rid+'-0-1-0.json',terminal)
run={'id':rid,'status':'EVIDENCE_READY','capture_window_complete':True,'send_state':'sent','send_attempts':1,'step':0,'sent_message_id':31,'sent_ids':[31],'sent_date':301,'sent_at':301,'send_intent_at':300,'send_dispatch_at':300,'send_timeout_seconds':10,'deadline':600,'scenario':old_scenario,'scenario_sha256':oldsha,'request_metadata':task,'sent_api_ack_reference':asr,'sent_task_reference':tsr,'sent_window_reference':wsr,'capture_until':481,'receive_head':hsr,'receive_sequence':0}
if CONTROL=='correct_full180':run['capture_window_complete']=False
rr=put(Path(M.STATE)/'runs'/(rid+'.json'),run)
old={'schema':'frw.F06.same-upload-correctread.v1','phase':'DOCX-CORRECT-READ-SAME-UPLOAD','status':'ROOT_BOUND_EXACT_F06_CORRECTREAD','run_id':rid,'scenario_sha256':oldsha,'source':fake_source,'source_reference':dict(sr),'first_ingress':c['first_ingress'],'scenario_ref':put('SYNTHETIC-old-correct-private-scenario.json',old_scenario),'resources':{'clock':closed_correct_clock_ref},'authority':dummy,'boundary':{'B':dict(principal,native_max_id=4)}}
if CONTROL=='correct_linkage':old['source_reference']['run_id']='SYNTHETIC-OTHER-FIRST'
oldsource=put('SYNTHETIC-old-correct-bound-consumer.py',b'# SYNTHETIC closed source metadata; never imported\n',True)
cb=put('SYNTHETIC-correct-binding.json',{'schema':'frw.Root.F06.exact-same-upload-correctread-binding.v1','source':oldsource,'whole_effect_sha256':'c'*64,'contract':old})
def judgement(name,schema,**extra):return put('correct-fixture/SYNTHETIC-'+name+'.json',dict(schema=schema,operator='Root',status='ROOT_BOUND',source=fake_source,source_reference=sr,B=principal,**extra))
cu=judgement('consumer-custody','frw.Root.F06.correct-original-consumer-custody.v1',canonical_run=rr,correct_binding=cb,bound_source=oldsource,base_consumer_sha256=F.BASE_SHA,assessed_methods=['verify_capture_context','verify_window','verify_reply_custody','receive_inventory'],capture_window_complete=True,terminal_complete=True,all_existing_raw_and_receipts_verified=True,late_arrivals_raw_only=True,original_clock_and_window_preserved=True,ack=ar,task=tr,window=wr,terminal_receive=hr,retained_basis=[dummy])
cl=judgement('closure','frw.Root.F06.correct-read-closed.v1',canonical_run=rr,correct_binding=cb,actor_tree_closed=True,slot_released=True,no_pending_effect=True,original_clock_preserved=True,raw_outcome_preserved=True,completed_at=482,clock=closed_first_clock_ref if CONTROL=='closureclock_mismatch' else closed_correct_clock_ref,original_consumer_custody=cu)
assessment={'canonical_run':rr,'correct_binding':cb,'original_consumer_custody':cu,'outcome':'ACTUAL_CORRECT_READ_ACCEPTED','correct_secret_verified_for_same_source':True,'actual_first_paragraph_and_structure_match':True,'toy_placeholder_oracle':False,'new_reply_and_technical_secret_delta_privately_assessed':True,'no_secret_echo_or_unrequested_new_secret_persistence':True,'original_private_request_exemption_only':True,'no_new_artifact_or_source_change':True,'full180_required_and_verified':True,'unknown_assumed_absent':False,'retained_basis':[dummy]}
if CONTROL=='correct_semantics':assessment['actual_first_paragraph_and_structure_match']=False
elif CONTROL=='correct_secret_delta':assessment['new_reply_and_technical_secret_delta_privately_assessed']=False
ass=judgement('assessment','frw.Root.F06.correct-read-semantic-assessment.v1',**assessment)
custody={'canonical_run':rr,'original_source_identity':first['source_identity'],'retained_source_sha256':fake_source['sha256'],'downloaded_source_sha256':fake_source['sha256'],'before_after_full_CAS_verified':True,'no_new_document_or_output':True}
if CONTROL=='correct_source_custody':custody['before_after_full_CAS_verified']=False
pc=judgement('private-custody','frw.Root.F06.correct-read-private-custody.v1',**custody)
ni=judgement('native-ingress','frw.Root.F06.correct-read-native-ingress.v1',canonical_run=rr,platform_message_id=31,native_message_ids=[] if CONTROL=='correct_ingress_missing' else [3,4],actual_same_source_reference_observed=True)
correct.update(canonical_run=rr,correct_binding=cb,ack=ar,task=tr,window=wr,closure=cl,assessment=ass,private_custody=pc,native_ingress=ni)
recfields={k:correct[k] for k in ('canonical_run','correct_binding','ack','task','window','closure','assessment','private_custody','native_ingress')}
cr=judgement('reconciliation','frw.Root.F06.correct-read-effect-reconciliation.v1',**recfields,effect_disposition='ACTUAL_CORRECT_READ_ACCEPTED_SAME_SOURCE_UNCHANGED',unknown_assumed_absent=False,no_reupload=True,raw_failures_and_UNKNOWN_preserved=True,next_operation='ONE_SEPARATE_WRONG_EDIT_SAME_UPLOAD_NO_UPLOAD',next_scenario_sha256=c['scenario_sha256'],change_spec=c['change_spec'])
correct['root_reconciliation']=cr
if CONTROL=='correct_unaccepted':correct['status']='SOURCE_ONLY_READY_UNBOUND'
elif CONTROL=='correct_ack_missing':correct['ack']=None
c['correct_read']=put('SYNTHETIC-closed-correct-read.json',correct)
c['root_proofs']={k:dummy for k in A.PROOFS};c['root_proofs']['first_upload_reconciliation']=first['root_reconciliation'];c['root_proofs']['correct_read_reconciliation']=cr
oracle={'schema':'frw.Root.F06.wrong-edit-private-oracle.v1','operator':'Root','status':'ROOT_BOUND','source':fake_source,'source_reference':sr,'correct_read':c['correct_read'],'phase':A.PHASE,'scenario_sha256':c['scenario_sha256'],'change_spec':c['change_spec'],'future_reply_acceptance':'NOT_ESTABLISHED','correct_edit_authorized':False,'automatic_followup_authorized':False,'max_outbound_documents':0,'retained_basis':[dummy]}
for k in ('legitimate_exact_change_authorized','actual_fixture_old_literal_and_unique_occurrence_privately_verified','deliberately_wrong_secret_verified_for_same_source','wrong_secret_distinct_from_previous_correct_secret','latest_supplied_wrong_password_only','previous_correct_password_or_history_use_prohibited','no_brute_force_or_password_search','expected_no_source_change_plaintext_output_or_delivery','new_reply_tool_arguments_files_and_secret_delta_review_required','original_private_request_exemption_only','actual_before_after_source_and_artifact_CAS_required'):oracle[k]=True
oracle_controls={'wrongonly':'deliberately_wrong_secret_verified_for_same_source','latestcredential':'latest_supplied_wrong_password_only','old_correctpassword':'previous_correct_password_or_history_use_prohibited','change_permission':'legitimate_exact_change_authorized','no_outputs':'expected_no_source_change_plaintext_output_or_delivery','distinct_wrong':'wrong_secret_distinct_from_previous_correct_secret'}
if CONTROL in oracle_controls:oracle[oracle_controls[CONTROL]]=False
elif CONTROL=='correct_edit_permission':oracle['correct_edit_authorized']=True
elif CONTROL=='outbound_document_permission':oracle['max_outbound_documents']=1
c['root_proofs']['wrong_edit_private_oracle']=put('SYNTHETIC-wrongedit-private-oracle.json',oracle)
# Bind only private synthetic source descriptors, not any current product facts.
def localref(leaf):return {'path':str(own/leaf),'bytes':pins[leaf]['bytes'],'sha256':pins[leaf]['sha256']}
c.update(adapter=localref('f06_source.py'),first_validator=localref('first_ingress.py'),actual_root_B_checker=localref('current_root.py'),footer=localref('f06_footer.py.txt'))
clockdata={'schema':'frw.Root.F06.original-finite-clock.v1','started_at':time.time()-1,'deadline_at':time.time()+590,'started_monotonic':time.monotonic()-1,'deadline_monotonic':time.monotonic()+590,'boot_id':'SYNTHETIC-BOOT-ID'}
if CONTROL=='copiedoldstart':clockdata['started_at']=481.0
elif CONTROL=='clock_expired':clockdata['deadline_at']=time.time()-1
elif CONTROL=='clock_insufficient':clockdata['deadline_at']=time.time()+304
elif CONTROL=='clock_wrongboot':clockdata['boot_id']='SYNTHETIC-OTHER-BOOT'
c['resources']=dict(A.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=28*1024**2,clock=put('SYNTHETIC-future-clock.json',clockdata),owned_parent_wait_cleanup=put('SYNTHETIC-cleanup-policy.json',{'SYNTHETIC':'stop same child within clock'}))
if CONTROL=='samefirstclock':c['resources']['clock']=closed_first_clock_ref
elif CONTROL=='samecorrectclock':c['resources']['clock']=closed_correct_clock_ref
freeze_ref=put('SYNTHETIC-source-freeze.json',{'schema':'frw.F06.ordinary-singleton.source-freeze.v1','files':pins})
review=put('SYNTHETIC-independent-review.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':freeze_ref['sha256'],'open_critical_defects':[]});c['root_proofs']['source_review']=review
prepared={'status':'ROOT_PREPARED_ONE_FUTURE_OPERATION','contract_effect':A.effect(c),'whole_effect_sha256':sha(encoded(A.effect(c))),'observed':{'SYNTHETIC':True,'f06_mutable_boundary':c['boundary']}}
c['root_current_proof']=put('SYNTHETIC-prepared-current-proof.json',prepared)
si=M.SLOT.stat();slot_identity={'device':si.st_dev,'inode':si.st_ino,'uid':si.st_uid,'mode':stat.S_IMODE(si.st_mode),'nlink':si.st_nlink}
v={'schema':'frw.Root.F06.same-upload-wrongedit-driver.v1','status':'ROOT_BOUND_ONE_FUTURE_OPERATION','contract':c,'source_freeze':freeze_ref,'independent_review':review,'workdir':str(work),'slot_identity':slot_identity,'expected_binding_sha256':None}
issuer_raw=(HERE/'fake_issuer.py.txt').read_text().replace('__ROOT__',repr(str(CASE))).replace('__CONTROL__',repr(CONTROL)).encode();issuer_ref=put('SYNTHETIC-INERT-FAKE-ISSUER.py',issuer_raw,True);M.ISSUER=Path(issuer_ref['path']);M.ISSUER_SHA=issuer_ref['sha256']
OWNED_OPENED_FDS=[]
class OwnedOS:
 def __getattr__(self,name):return getattr(os,name)
 def open(self,path,*args,**kwargs):
  fd=os.open(path,*args,**kwargs);OWNED_OPENED_FDS.append({'path':str(path),'fd':fd});return fd
M.os=OwnedOS()
real_load=M.load

def load(ref,name,**kw):
 EVENTS.append(['load',Path(ref['path']).name]);m=real_load(ref,name,**kw)
 if Path(ref['path']).name=='f06_source.py':
  m.SOURCE=fake_source;m.INSTALLED_TESTER=Path(installed['path']);m.INSTALLED_TESTER_SHA=installed['sha256'];m.types=types.SimpleNamespace(ModuleType=FixtureModule)
  real_successor=m.successor
  def successor(base,contract,footer):
   EVENTS.append(['successor','freshproof',contract['root_current_proof']['sha256'],'authority',contract['authority']['sha256']]);raw=real_successor(base,contract,footer)
   if CONTROL=='reconstruction_guard' and sum(e[0]=='successor' for e in EVENTS)==2:return raw+b'# SYNTHETIC reconstruction corruption\n'
   return raw
  m.successor=successor
 elif Path(ref['path']).name=='current_root.py':
  def observe(proof):
   EVENTS.append(['SYNTHETIC-checker-observe']);value=json.loads(encoded(proof['observed']))
   if CONTROL=='current_changed':value['SYNTHETIC']='changed'
   return value
  def proofcheck(path,want):
   EVENTS.append(['SYNTHETIC-checker-check'])
   if CONTROL=='freshproof_drift':put(Path(path),{'SYNTHETIC':'drift after freshproof creation'})
   raw=M.read(path);check(sha(raw)==want,'stand pinned fresh proof changed');p=json.loads(raw);check(p['status']=='ROOT_BOUND','stand current status')
   return {'whole_effect_sha256':'0'*64 if CONTROL=='qualified_effect_mismatch' else p['whole_effect_sha256']}
  m.observe=observe;m.check=proofcheck;m.transport=lambda:types.SimpleNamespace(kernel=lambda pid:{'SYNTHETIC':True,'pid':pid,'start_time':1})
 elif Path(ref['path']).name=='SYNTHETIC-INERT-FAKE-ISSUER.py':m.os=M.os;EVENTS.append(['SYNTHETIC-inert-issuer-loaded'])
 else:raise AssertionError('undeclared load')
 return m
M.load=load
class PrebirthBoundary(BaseException):pass
POPEN=[]
def fakepopen(argv,**kw):
 check(argv==[M.PYTHON,'-I','-B','-S',str(work/'bot_tester.f06.root-bound.py'),'--state-dir',str(M.STATE),'run','--run-id',c['run_id'],'--scenario',c['scenario_ref']['path']],'sole original consumer argv')
 check(len(POPEN)==0,'one fakePopen only');check(callable(kw.get('preexec_fn')),'real child resource closure provided')
 check(len(kw.get('pass_fds',()))==1,'shared slot FD passed')
 fd=kw['pass_fds'][0];info=os.fstat(fd);check(info.st_ino==slot_identity['inode'],'same shared slot')
 br=json.loads((work/'ROOT-ACTUAL-BINDING.json').read_bytes());boundraw=(work/'bot_tester.f06.root-bound.py').read_bytes()
 check(br['contract']['authority']!=None and br['contract']['authority_id']=='SYNTHETIC-ONLY-NEW-AUTHORITY','issued synthetic authority mutation reached binding')
 check(br['contract']['root_current_proof']['path']==str(work/'ROOT-FRESH-CURRENT-PROOF.json'),'fresh proof ref mutation reached binding')
 tree=ast.parse(boundraw);contract_node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='F06_CONTRACT' for t in n.targets))
 check(ast.literal_eval(contract_node.value)==br['contract'],'saved source exact JSON contract reconstruction')
 POPEN.append({'argv':argv,'pass_fds':list(kw['pass_fds']),'same_shared_slot_held':True,'preexec_fn_present':True,'source_sha256':sha(boundraw),'authority_mutation_ref':br['contract']['authority'],'freshproof_mutation_ref':br['contract']['root_current_proof'],'exact_JSON_contract_reconstruction':True})
 raise PrebirthBoundary('SYNTHETIC_SOLE_FAKE_POPEN_NO_PROCESS')
M.subprocess=types.SimpleNamespace(Popen=fakepopen,DEVNULL=subprocess.DEVNULL,TimeoutExpired=subprocess.TimeoutExpired)
original_handlers={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
if CONTROL=='stop_before_birth':
 def registration(n,handler):
  prior=signal.signal(n,handler)
  if n==signal.SIGTERM and getattr(handler,'__name__',None)=='parent_stop':EVENTS.append(['SYNTHETIC-stop-before-birth']);handler(n,None)
  return prior
 M.signal=types.SimpleNamespace(SIGINT=signal.SIGINT,SIGTERM=signal.SIGTERM,getsignal=signal.getsignal,signal=registration)
# Late protocol controls preserve all dependencies and alter their intended seam.
if CONTROL.startswith('source_drift_'):
 leaf={'adapter':'f06_source.py','checker':'current_root.py','footer':'f06_footer.py.txt','caller':'root_bind_dispatch_once.py','validator':'first_ingress.py'}[CONTROL[len('source_drift_'):]];put(own/leaf,(own/leaf).read_bytes()+b'\n# SYNTHETIC drift\n',True)
elif CONTROL=='review_mismatch':reviewdata=jread(review);reviewdata['source_freeze_sha256']='0'*64;v['independent_review']=refresh(review,reviewdata)
elif CONTROL=='slot_identity':v['slot_identity']['inode']+=1
elif CONTROL=='once_exists':put(work/'ROOT-ONCE-INVOCATION.json',{'SYNTHETIC':'prior once'})
elif CONTROL=='canonical_run_exists':put(Path(M.STATE)/'runs'/(c['run_id']+'.json'),{'SYNTHETIC':'prior canonical run'})
elif CONTROL=='already_issued':put(M.AUTHORITY_DIR/'INDEPENDENT-AUTHORITY-R-SYNTHETIC-OLD.json',{'run_scenarios':{c['run_id']:c['scenario_sha256']}})
elif CONTROL=='issuer_atomic_collision':put(M.AUTHORITY_DIR/'INDEPENDENT-AUTHORITY-R-SYNTHETIC.json',{'SYNTHETIC':'preexisting untouched collision'})
elif CONTROL=='issuer_wrong_pin':M.ISSUER_SHA='0'*64
elif CONTROL=='invalid_cpu':c['resources']['cpu_seconds']=0
elif CONTROL=='invalid_memory':c['resources']['max_rss_bytes']=3*1024**3
elif CONTROL=='invalid_disk':c['resources']['disk_bytes']=65*1024**2
elif CONTROL=='invalid_reserve':c['resources']['reserve_seconds']=0
elif CONTROL=='scenario_drift':put(Path(c['scenario_ref']['path']),b'{}\n',True)
if CONTROL in ('invalid_cpu','invalid_memory','invalid_disk','invalid_reserve'):
 prepared['contract_effect']=A.effect(c);prepared['whole_effect_sha256']=sha(encoded(A.effect(c)));c['root_current_proof']=refresh(c['root_current_proof'],prepared)
# Preserve old fake fixture bytes and record no replay, modification or lookup of
# real history. Synthetic historical metadata is not actual Root authority.
initial={str(p):sha(p.read_bytes()) for root in (CASE/'first-fixture',CASE/'correct-fixture',M.AUTHORITY_DIR) for p in root.rglob('*') if p.is_file()}
binding=put('SYNTHETIC-root-inputs.json',v);failure=None;boundary=False;trace=[];start=time.monotonic();execution_open_start_index=len(AUDIT['opens'])
try:
 if CONTROL=='audit_external_open':open('/SYNTHETIC-UNDECLARED-EXTERNAL-READ','rb')
 elif CONTROL=='audit_external_write':open('/SYNTHETIC-UNDECLARED-EXTERNAL-WRITE','wb')
 elif CONTROL=='audit_external_metadata':os.stat('/SYNTHETIC-UNDECLARED-EXTERNAL-METADATA')
 elif CONTROL=='audit_network':socket.socket()
 elif CONTROL=='audit_process':subprocess.Popen(['/SYNTHETIC-NEVER-EXECUTED'])
 elif CONTROL=='audit_import':__import__('SYNTHETIC_UNDECLARED_MODULE')
 else:M.main(['--execute-once',binding['path'],binding['sha256']])
except PrebirthBoundary as exc:failure=str(exc);boundary=True
except Exception as exc:
 failure=type(exc).__name__+':'+str(exc);tb=exc.__traceback__
 while tb is not None:trace.append([tb.tb_frame.f_code.co_filename,tb.tb_lineno,tb.tb_frame.f_code.co_name]);tb=tb.tb_next
execution_open_end_index=len(AUDIT['opens']);execution_opens=AUDIT['opens'][execution_open_start_index:execution_open_end_index]
old_clock_bodies_not_read=all(r['path'] not in execution_opens for r in (closed_first_clock_ref,closed_correct_clock_ref))
closed=True
for call in POPEN:
 for fd in call['pass_fds']:
  try:os.fstat(fd);closed=False
  except OSError:pass
all_opened_fds_closed=True
for row in OWNED_OPENED_FDS:
 try:os.fstat(row['fd']);row['closed_after_return']=False;all_opened_fds_closed=False
 except OSError:row['closed_after_return']=True
probe=os.open(M.SLOT,os.O_RDWR|os.O_NOFOLLOW)
try:
 try:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB);slot_reacquirable=True
 except BlockingIOError:slot_reacquirable=False
finally:os.close(probe)
handlers=all(signal.getsignal(n)==h for n,h in original_handlers.items())
preserved=initial=={p:sha(Path(p).read_bytes()) for p in initial}
expected={
'samefirstclock':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','samecorrectclock':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','closureclock_mismatch':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','copiedoldstart':'F06_NEW_CLOCK_MUST_START_AFTER_CORRECT_READ_CLOSURE',
'first_ack_missing':'F06_FIRST_ARTIFACT_CUSTODY_REQUIRED','first_user_missing':'F06_FIRST_REAL_ACK_CONTEXT_REQUIRED','first_chat_missing':'F06_FIRST_REAL_ACK_CONTEXT_REQUIRED','first_source_missing':'F06_FIRST_EXACT_SOURCE_REFERENCE_REQUIRED','correct_ack_missing':'F06_CORRECT_READ_ARTIFACT_CUSTODY_REQUIRED','correct_user_missing':'F06_CORRECT_REAL_TEXT_ACK_REQUIRED','correct_chat_missing':'F06_CORRECT_REAL_TEXT_ACK_REQUIRED','issuer_atomic_collision':'FileExistsError:','issuer_wrong_pin':'F06_PIN_CHANGED',
'first_ack_user':'F06_FIRST_REAL_ACK_CONTEXT_REQUIRED','first_ack_chat':'F06_FIRST_REAL_ACK_CONTEXT_REQUIRED','first_ingress_missing':'F06_FIRST_ACTUAL_NATIVE_SOURCE_INGRESS_REQUIRED','first_source_mismatch':'F06_FIRST_EXACT_SOURCE_REFERENCE_REQUIRED',
'correct_ack_user':'F06_CORRECT_REAL_TEXT_ACK_REQUIRED','correct_ack_chat':'F06_CORRECT_REAL_TEXT_ACK_REQUIRED','correct_ack_document':'F06_CORRECT_REAL_TEXT_ACK_REQUIRED','correct_full180':'F06_CORRECT_READ_FULL_CLOSED_KNOWN_EFFECT_REQUIRED','correct_linkage':'F06_CORRECT_READ_ORIGINAL_BINDING_LINK_REQUIRED','correct_semantics':'F06_CORRECT_READ_REAL_SEMANTIC_ASSESSMENT_REQUIRED','correct_secret_delta':'F06_CORRECT_READ_REAL_SEMANTIC_ASSESSMENT_REQUIRED','correct_source_custody':'F06_CORRECT_READ_UNCHANGED_SOURCE_CUSTODY_REQUIRED','correct_ingress_missing':'F06_CORRECT_READ_NATIVE_LINK_REQUIRED','correct_unaccepted':'F06_ACTUAL_CORRECT_READ_DEPENDENCY_REQUIRED',
'change_authorization_mismatch':'F06_AUTHORIZED_CHANGE_SCENARIO_MISMATCH','change_unbounded':'F06_EXACT_BOUNDED_CHANGE_REQUIRED',
'wrongonly':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','latestcredential':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','old_correctpassword':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','change_permission':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','no_outputs':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','distinct_wrong':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','correct_edit_permission':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED','outbound_document_permission':'F06_WRONGEDIT_PERMISSION_AND_NOCHANGE_ORACLE_REQUIRED',
'clock_expired':'F06_ORIGINAL_CLOCK_EXPIRED_OR_CHANGED','clock_wrongboot':'F06_ORIGINAL_CLOCK_EXPIRED_OR_CHANGED','clock_insufficient':'F06_ORIGINAL_FINITE_CLOCK_INSUFFICIENT','review_mismatch':'F06_EXACT_INDEPENDENT_SOURCE_ACCEPTANCE_REQUIRED','slot_identity':'F06_EXISTING_SHARED_SLOT_CUSTODY_CHANGED','once_exists':'FileExistsError:','canonical_run_exists':'F06_NO_EXISTING_OPERATION_REPLAY','already_issued':'F06_AUTHORITY_ALREADY_ISSUED_RECONCILE_ONLY','scenario_drift':'F06_PIN_CHANGED','current_changed':'F06_REVIEWED_MUTABLE_BASIS_CHANGED_RECONCILE_ONLY','freshproof_drift':'stand pinned fresh proof changed','qualified_effect_mismatch':'F06_WHOLE_EFFECT_PROOF_CHANGED','reconstruction_guard':'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE','stop_before_birth':'F06_STOP_BEFORE_CONSUMER_BIRTH',
'audit_external_open':'AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED','audit_external_write':'AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED','audit_external_metadata':'AUDIT_EXTERNAL_METADATA_DENIED','audit_network':'AUDIT_NETWORK_DENIED','audit_process':'AUDIT_REAL_ACTOR_DENIED','audit_import':'AUDIT_POST_PREWARM_IMPORT_DENIED'}
if CONTROL.startswith('source_drift_'):expected[CONTROL]='F06_REVIEWED_SOURCE_DRIFT'
if CONTROL.startswith('authority_'):expected[CONTROL]='F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT'
if CONTROL.startswith('invalid_'):expected[CONTROL]='F06_FINITE_ACTUAL_CONSUMER_RESOURCES_UNBOUND'
expected_boundary=CONTROL=='positive'
expectation_met=(boundary==expected_boundary and handlers and closed and all_opened_fds_closed and slot_reacquirable and old_clock_bodies_not_read and preserved and failure is not None and (boundary or expected.get(CONTROL,'CONTROL_EXPECTATION_UNDECLARED') in failure))
if CONTROL.startswith('source_drift_') or CONTROL=='review_mismatch':expectation_met=expectation_met and not any(e[0]=='load' for e in EVENTS)
if boundary:expectation_met=expectation_met and len(POPEN)==1 and sum(e[0]=='successor' for e in EVENTS)==2
# Keep actual generated-bound and negative artifacts; no evidence deletion.
removed=[]
result={'control':CONTROL,'snapshot':SNAPSHOT.name,'source_pins':pins,'failure':failure,'trace':trace,'boundary':boundary,'fake_Popen_count':len(POPEN),'fake_Popen':POPEN,'events':EVENTS,'audit':AUDIT,'parent_signal_handlers_restored':handlers,'passed_shared_slot_fd_closed':closed,'all_caller_issuer_opened_fds_closed':all_opened_fds_closed,'slot_reacquirable_after_return':slot_reacquirable,'caller_issuer_opened_fds':OWNED_OPENED_FDS,'old_clock_ref_metadata':{'first':closed_first_clock_ref,'correct':closed_correct_clock_ref},'old_clock_bodies_not_read':old_clock_bodies_not_read,'candidate_execution_opens':execution_opens,'old_synthetic_custody_preserved':preserved,'expectation_met':expectation_met,'expected_failure_fragment':expected.get(CONTROL),'elapsed_seconds':time.monotonic()-start,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':{'CPU':list(resource.getrlimit(resource.RLIMIT_CPU)),'AS':list(resource.getrlimit(resource.RLIMIT_AS)),'FSIZE':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'affinity':sorted(os.sched_getaffinity(0))},'removed_owned_duplicates':removed,'harness_sha256':sha(Path(__file__).read_bytes()),'claim':'SOURCE ONLY synthetic caller prebirth protocol; fake historical evidence not actual current authority; no live/full180/userPASS'}
put(CASE/'RESULT.json',result)
print(json.dumps({k:result[k] for k in ('control','failure','boundary','fake_Popen_count','expectation_met','trace')}))
