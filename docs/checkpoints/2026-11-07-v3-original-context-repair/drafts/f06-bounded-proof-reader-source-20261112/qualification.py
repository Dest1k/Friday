"""Confined source qualification. Synthetic transport; stop before save/send."""
import ast,datetime,hashlib,json,os,re,resource,socket,subprocess,sys,time,types
from pathlib import Path
B=Path(__file__).resolve().parent
T=Path('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112')
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
base=BASE.read_bytes();assert hashlib.sha256(base).hexdigest()=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
os.umask(0o077)
CHECKS=[];SEAMS=[];AUDIT={'blocked':[],'own_opens':0};FIXTURES=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def good(n,c=True):
 assert c,n;CHECKS.append(n)
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(b);p.chmod(0o600);return ref(p)
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def load(p):
 m=types.ModuleType('SYNTHETIC_'+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
class StopBeforeSave(BaseException):pass
class TypedFakeAPI:
 def __init__(self):self.calls=[]
 def call(self,*args,**kwargs):self.calls.append((args,kwargs));raise AssertionError('API_FORBIDDEN')
 def send_document(self,*args,**kwargs):raise AssertionError('SEND_DOCUMENT_FORBIDDEN')
 def send_photo(self,*args,**kwargs):raise AssertionError('SEND_PHOTO_FORBIDDEN')
checker_source='''import hashlib,json,os,stat
class SyntheticTypedReadOnlyTransport:
    def current(self,path,expected):
        with open(path,'rb') as stream:
            s=os.fstat(stream.fileno())
            assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600
            raw=stream.read(24*1024**2+1)
        assert len(raw)<=24*1024**2 and hashlib.sha256(raw).hexdigest()==expected
        p=json.loads(raw);r=p['SYNTHETIC_TYPED_TRANSPORT_RESPONSE']
        assert type(r) is dict and type(r['admission']) is bool and type(r['native_readonly']) is dict
        return dict(r,Root_proof_sha256=expected)
def check(path,expected):return SyntheticTypedReadOnlyTransport().current(path,expected)
'''
# Prewarm every original full-consumer import before the confinement boundary.
pre=types.ModuleType('SYNTHETIC_PREWARM');pre.__file__=str(BASE);exec(compile(base,str(BASE),'exec'),pre.__dict__)
BasePath=type(Path())
def build(branch):
 d=B/'checks'/branch;d.mkdir(parents=True,mode=0o700)
 # Explicit synthetic copy of otherwise unchanged adapter; only SOURCE pathname is rebased.
 original=(B/'candidate'/branch/'f06_source.py').read_bytes()
 adapter_path=d/'SYNTHETIC-adapter.py'
 appended="\nSOURCE=dict(SOURCE,path="+repr(str(d/'SYNTHETIC-input.docx'))+")\nclass _SyntheticTime:\n    @staticmethod\n    def time():return 1000000000\ntime=_SyntheticTime()\n"
 put(adapter_path,original+appended.encode());a=load(adapter_path)
 aux=put(d/'SYNTHETIC-direct-proof.json',b'{"SYNTHETIC_ONLY":true}'+b' '*(1048700-23)+b'\n')
 generic=put(d/'SYNTHETIC-small-proof.json',enc({'SYNTHETIC_ONLY':True}))
 state=dict(pid=997777,start_time=88888,updated_at='2000-01-01T00:00:00+00:00',gateway_state='running',active_agents=0,active_work=None,restart_requested=False,session_store={'status':'ok'},platforms={'telegram':{'state':'connected','needs_attention':False,'writer_pid':997777,'writer_start_time':88888}})
 state_path=d/'SYNTHETIC-gateway-state.json';state_ref=put(state_path,enc(state))
 gateway=dict(pid=997777,start_time=88888,state_path=str(state_path),maximum_staleness_seconds=1)
 boundary={k:'a'*64 for k in a.BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}}
 boundary.update(gateway=gateway,B={'profile':'telegram-bot-8812646969','session_id':'SYNTHETIC-SID','session_key':'SYNTHETIC-KEY','native_max_id':0},phase_unconsumed=True,uploads_this_operation=1 if branch=='first' else 0,producer_calls=0,restarts=0)
 c=a.unbound();c.update(status={'first':'ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD','correct':'ROOT_BOUND_EXACT_F06_CORRECTREAD','wrong-edit':'ROOT_BOUND_EXACT_F06_WRONGEDIT'}[branch],run_id='SYNTHETIC-'+branch,authority_id='SYNTHETIC-AUTHORITY',adapter=ref(adapter_path),footer=ref(B/'candidate'/branch/'f06_footer.py.txt'),actual_root_B_checker=put(d/'SYNTHETIC-typed-checker.py',checker_source.encode()),root_current_proof=generic,boundary=boundary,resources=dict(a.TIMING,cpu_seconds=120,max_rss_bytes=1024**3,disk_bytes=64*1024**2,clock=generic,owned_parent_wait_cleanup=generic),product=dict(source_layers=207,project_files=495,native_files=17891,plugin_files=52,base_source_files=17730,source_receipt_sha256='b'*64,input_sha256='c'*64))
 c['root_proofs']={k:aux for k in a.PROOFS}
 if branch=='first':
  pin={'path':a.SOURCE['path'],'sha256':a.SOURCE['sha256'],'stat':{k:0 for k in pre.INPUT_STAT_FIELDS},'filename':'f06-new-encrypted.docx','mime_type':a.MIME,'kind':'document'}
  pin['stat'].update(uid=os.getuid(),inode=1,size_bytes=a.SOURCE['bytes'])
  scenario=a.construct_scenario(supplied_password='SYNTHETIC_ONLY',input_pin=pin)
  pred={'schema':'frw.Root.ordinary-independent-history-admission.v1','accepted':True,'authority_id':'SYNTHETIC-PREDECESSOR'}
  c['authority_chain']=dict(predecessor=put(d/'SYNTHETIC-predecessor.json',enc(pred)),predecessor_authority_id='SYNTHETIC-PREDECESSOR',created_at=999999000,expires_at=1000001000)
 else:
  first_dep={'schema':'frw.Root.F06.closed-first-upload.v1','status':'ROOT_BOUND_CLOSED_RECONCILED','source':a.SOURCE,'source_reference':{}}
  if branch=='correct':scenario=a.construct_scenario(supplied_password='SYNTHETIC_ONLY',first_dependency=first_dep)
  else:
   change_spec=dict(kind='literal_replace',old='SYNTHETIC_OLD',new='SYNTHETIC_NEW',expected_occurrences=1)
   correct_dep={'schema':'frw.Root.F06.closed-correct-read.v1','status':'ROOT_BOUND_CORRECT_READ_ACCEPTED','source_reference':first_dep['source_reference'],'source':a.SOURCE}
   scenario=a.construct_scenario(supplied_password='SYNTHETIC_ONLY',change_spec=change_spec,first_dependency=first_dep,correct_dependency=correct_dep)
   c['correct_read']=aux;c['change_spec']=put(d/'SYNTHETIC-change-spec.json',a.encoded(change_spec))
  # The actual first-ingress implementation remains unchanged in candidate. A typed
  # synthetic dependency qualifies the reader ABI without claiming a real first upload.
  c['first_validator']=put(d/'SYNTHETIC-first-dependency.py',b"def readref(r,read):\n    bounded=getattr(read,'f06_read_reference',None)\n    return bounded(r) if bounded is not None else read(r['path'])\ndef validate(c,read):\n    assert readref(c['first_ingress'],read)\n    return {'SYNTHETIC_ONLY':True}\ndef correct_read(c,read,first):\n    assert readref(c['correct_read'],read)\ndef private_oracle(c,read):\n    assert readref(c['first_ingress'],read)\n")
  c['first_ingress']=aux;c['source_reference']={'run_id':'SYNTHETIC-FIRST','run_sha256':'d'*64,'input_sha256':a.SOURCE['sha256']}
  c['installation']=dict(closure=generic,source_acceptance=generic,product=c['product'],runtime_hashes={'SYNTHETIC':'e'*64})
 c['scenario_ref']=put(d/'SYNTHETIC-scenario.json',a.encoded(scenario));c['scenario_sha256']=sha(a.encoded(scenario))
 state_dir=d/'SYNTHETIC-STATE';state_dir.mkdir(mode=0o700)
 for n in ('runs','updates','downloads'):(state_dir/n).mkdir(mode=0o700)
 history={}
 for i in range(40):
  row=dict(id='SYNTHETIC-HISTORY-'+str(i),status='STOPPED',send_state='none',deadline=1,scenario={'steps':[]})
  rr=put(state_dir/'runs'/(row['id']+'.json'),enc(row));history[row['id']]={'sha256':rr['sha256'],'status':'STOPPED','send_state':'none','deadline':1,'new_effect_replay_authorized':False,'unknown_retained':False}
 issued=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,authority_id=c['authority_id'],scope=c['scope'],run_scenarios={c['run_id']:c['scenario_sha256']},ordered_predecessors={},same_canonical_local_run=False,created_at=999999000,expires_at=1000001000,boot_id='SYNTHETIC-BOOT',new_independent_inputs_only=True,no_old_task_replay=True,old_rows_modified=False,unknown_effects_resolved=False,product_or_B00_acceptance=False,new_trial_for_historical_task=False,history=history,gateway=gateway)
 if branch=='first':issued['supersedes']={'authority_id':'SYNTHETIC-PREDECESSOR','reason':'Synthetic qualification only'}
 c['authority']=put(d/'SYNTHETIC-authority.json',enc(issued))
 proc=d/'SYNTHETIC-proc';put(proc/'sys/kernel/random/boot_id',b'SYNTHETIC-BOOT\n');put(proc/'997777/stat',(' '.join(['0']*21+['88888'])+'\n').encode())
 f=dict(admission=False,installed_product=c['product'],f06_mutable_boundary=c['boundary'],whole_effect_sha256=a.digest(a.encoded(a.effect(c))),gateway=gateway,native_readonly=dict(read_only=True,quiescent=True,session_id=boundary['B']['session_id'],session_key=boundary['B']['session_key'],identity=gateway))
 proof_body=enc({'SYNTHETIC_TYPED_TRANSPORT_RESPONSE':f,'SYNTHETIC_ONLY':True});proof=proof_body[:-1]+b' '*(2496998-len(proof_body))+b'\n';assert len(proof)==2496998
 proof_path=d/'SYNTHETIC-CURRENT-PROOF.json';c['root_current_proof']=put(proof_path,proof)
 c=a.canonical_contract(c);a.contract_shape(c)
 out=a.successor(base,c,(B/'candidate'/branch/'f06_footer.py.txt').read_bytes());outref=put(d/'SYNTHETIC-full-consumer.py',out)
 old_source_dir=(T/'candidate'/branch) if branch!='wrong-edit' else Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112/candidate')
 old_footer=(old_source_dir/'f06_footer.py.txt').read_bytes();old_footer_ref=put(d/'SYNTHETIC-original-footer.py.txt',old_footer)
 old_c=a.canonical_contract(c);old_c['footer']=old_footer_ref
 old_out=a.successor(base,old_c,old_footer);old_m=load(Path(put(d/'SYNTHETIC-original-full-consumer.py',old_out)['path']))
 m=load(Path(outref['path']))
 class StandPathMeta(type):
  def __instancecheck__(cls,obj):return isinstance(obj,Path)
 class StandPath(BasePath,metaclass=StandPathMeta):
  def __init__(self,*args):
   if args and (str(args[0])=='/proc' or str(args[0]).startswith('/proc/')):args=(str(proc)+str(args[0])[5:],*args[1:])
   super().__init__(*args)
 m.Path=StandPath;m.CANONICAL_STATE=state_dir;old_m.Path=StandPath;old_m.CANONICAL_STATE=state_dir
 good(branch+':MAX_JSON_1MiB_unchanged',m.MAX_JSON==1048576 and m.safe_read.__defaults__==(1048576,True))
 oldtree=ast.parse(base);newtree=ast.parse(out)
 funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 good(branch+':original_safe_read_AST_unchanged',funcs(oldtree)['safe_read']==funcs(newtree)['safe_read'])
 good(branch+':byte_reconstruct_after_JSON',out==a.successor(base,json.loads(a.encoded(c)),(B/'candidate'/branch/'f06_footer.py.txt').read_bytes()))
 FIXTURES.append(dict(branch=branch,d=d,a=a,c=c,scenario=scenario,m=m,old_m=old_m,state=state,state_raw=enc(state),state_path=state_path,state_dir=state_dir,proof_path=proof_path,proof=proof,aux=aux))
 SEAMS.append(dict(branch=branch,whole_consumer='real successor/fullv42 Runner.new/ordinary_independent_admission/current_gate',state_history='real own protected synthetic files,40 rows',checker='explicit SYNTHETIC typed read-only transport fixture; actual production checker unchanged, actual current check NOT_RUN',first_dependency='SYNTHETIC typed first validator only for correct branch' if branch!='first' else None,Path='only literal/proc remapped to own fixture; no actual proc read',api='typed fake API with every method refusing',stop='BaseException sentinel BEFORE Runner.save or _send'))
for branch in ('first','correct','wrong-edit'):build(branch)
# After source load/import setup, forbid any unowned content or directory access.
def audit(event,args):
 if event=='open':
  p=args[0]
  if isinstance(p,(str,bytes,os.PathLike)):
   q=Path(os.fsdecode(p))
   if not q.is_absolute():q=Path.cwd()/q
   if not q.is_relative_to(B):AUDIT['blocked'].append({'event':event,'path':str(q)});raise PermissionError('SYNTHETIC_STAND_UNOWNED_OPEN_REFUSED')
   AUDIT['own_opens']+=1
 elif event in ('os.listdir','os.scandir'):
  q=Path(args[0]);
  if not q.is_relative_to(B):raise PermissionError('SYNTHETIC_STAND_UNOWNED_DIRECTORY_REFUSED')
 elif event.startswith(('socket.','subprocess.','os.exec','os.spawn','os.fork')):raise PermissionError('SYNTHETIC_STAND_EXTERNAL_EFFECT_REFUSED')
sys.addaudithook(audit)
def refused(n,fn,expected=None):
 try:fn()
 except Exception as e:
  if expected is not None:assert expected in str(e),(n,type(e).__name__,str(e))
  CHECKS.append(n);return {'type':type(e).__name__,'message':str(e)}
 raise AssertionError(n+':DID_NOT_REFUSE')
for x in FIXTURES:
 branch,d,a,c,m=x['branch'],x['d'],x['a'],x['c'],x['m'];p=x['proof_path'];raw=x['proof']
 refused(branch+':exact_original_default_reader_reproduces_2496998B_size_refusal',lambda:m.safe_read(p),'Unsafe file type, link count, or size')
 good(branch+':bounded_declared_reader_2496998B',a.readref(c['root_current_proof'],m._f06_reference_read)==raw)
 refused(branch+':callback_exact_ref_path_requires_builtin_str',lambda:m._f06_bounded_reference_read(dict(c['root_current_proof'],path=p)),'F06_EXACT_BOUNDED_REFERENCE_REQUIRED')
 # Existing injected Root ABI has NO limit parameter and remains supported.
 calls=[]
 def injected_root_reader(path,*,private=True):calls.append((str(path),private));return m.safe_read(path,limit=24*1024**2,private=private)
 good(branch+':original_injected_Root_reader_ABI',a.readref(c['root_current_proof'],injected_root_reader)==raw and calls==[(str(p),True)])
 def whole_new():
  api=TypedFakeAPI();store=m.Store(x['state_dir']);runner=m.Runner(store,api,clock=lambda:1000000000,sleep=lambda s:(_ for _ in ()).throw(AssertionError('SLEEP_FORBIDDEN')))
  saved=[]
  def stop(run):saved.append({'id':run['id'],'status':run['status'],'send_attempts':run['send_attempts']});raise StopBeforeSave()
  runner.save=stop
  runner._send=lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('SEND_FORBIDDEN'))
  try:runner.new(c['run_id'],x['scenario'])
  except StopBeforeSave:pass
  else:raise AssertionError('MISSING_STOP_SENTINEL')
  good(branch+':whole_full_consumer_NEW_reaches_before_save_with_large_current_and_all_direct_proofs',saved==[{'id':c['run_id'],'status':'PREPARED','send_attempts':0}] and api.calls==[])
  good(branch+':no_canonical_run_saved',not store.run_path(c['run_id']).exists())
 old_runner=x['old_m'].Runner(x['old_m'].Store(x['state_dir']),TypedFakeAPI(),clock=lambda:1000000000)
 old_runner.save=lambda run:(_ for _ in ()).throw(AssertionError('OLD_MUST_REFUSE_BEFORE_SAVE'))
 try:old_runner.new(x['old_m'].F06_CONTRACT['run_id'],x['scenario'])
 except x['old_m'].Refused as exc:
  chain=[];cur=exc
  while cur is not None:chain.append(str(cur));cur=cur.__cause__
  good(branch+':original_whole_consumer_large_proof_failure_reproduced',('F06_FRESH_ROOT_B_BOUNDARY_REFUSED' if branch=='first' else 'F06_NEW_CURRENT_UNBOUND') in chain and 'Unsafe file type, link count, or size' in chain)
 else:raise AssertionError('ORIGINAL_WHOLE_CONSUMER_DID_NOT_REFUSE')
 whole_new()
 # A directly read auxiliary proof also retains declared hash/private/size checks.
 auxpath=Path(x['aux']['path']);auxraw=auxpath.read_bytes()
 for label,write,mode in [('same_size_aux_hash',b'X'+auxraw[1:],0o600),('aux_oversize',auxraw+b'X',0o600),('aux_private_mode',auxraw,0o640)]:
  auxpath.write_bytes(write);auxpath.chmod(mode)
  refused(branch+':'+label,lambda:a.current_gate(c,'NEW',x['state'],x['state_raw'],x['state_path'],m._f06_reference_read))
 auxpath.write_bytes(auxraw);auxpath.chmod(0o600)
 for phase in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'):
  good(branch+':real_adapter_current_gate_'+phase,a.current_gate(c,phase,x['state'],x['state_raw'],x['state_path'],m._f06_reference_read))
 refused(branch+':unsupported_phase_refused',lambda:a.current_gate(c,'POST_INTENT',x['state'],x['state_raw'],x['state_path'],m._f06_reference_read),'F06_PRE_INTENT_GATE_ONLY')
 p.write_bytes(b'X'+raw[1:]);p.chmod(0o600)
 refused(branch+':same_size_proof_hash_tamper',lambda:whole_new(),'F06_FRESH_ROOT_B_BOUNDARY_REFUSED')
 p.write_bytes(raw+b'X');p.chmod(0o600)
 refused(branch+':proof_exceeds_declared_size',lambda:whole_new(),'F06_FRESH_ROOT_B_BOUNDARY_REFUSED')
 p.write_bytes(raw);p.chmod(0o640)
 refused(branch+':private_proof_mode0640_refused',lambda:whole_new(),'F06_FRESH_ROOT_B_BOUNDARY_REFUSED')
 p.chmod(0o600)
 refused(branch+':direct_nonreference_privateFalse_read_still_default1MiB',lambda:m._f06_reference_read(p,private=False),'Unsafe file type, link count, or size')
 # Test immutable reference cap before file open, including int/bool distinctions.
 original_ref=dict(m.F06_CONTRACT['root_current_proof'])
 for label,size in (('zero',0),('negative',-1),('bool',True),('over24MiB',24*1024**2+1)):
  m.F06_CONTRACT['root_current_proof']['bytes']=size
  refused(branch+':declared_'+label+'_refused',lambda:m._f06_bounded_reference_read(m.F06_CONTRACT['root_current_proof']),'F06_EXACT_BOUNDED_REFERENCE_REQUIRED')
 m.F06_CONTRACT['root_current_proof'].update(original_ref)
 # Same size/hash proof contents cannot disable native/current boundary conditions.
 proofdoc=json.loads(raw)
 for label,mut in (('native_not_readonly',lambda f:f['native_readonly'].update(read_only=False)),('native_not_quiescent',lambda f:f['native_readonly'].update(quiescent=False)),('native_identity_drift',lambda f:f['native_readonly'].update(identity={'pid':7})),('product_drift',lambda f:f.update(installed_product={})),('effect_hash_drift',lambda f:f.update(whole_effect_sha256='0'*64)),('admission_grant',lambda f:f.update(admission=True))):
  v=json.loads(raw);mut(v['SYNTHETIC_TYPED_TRANSPORT_RESPONSE']);b=enc(v);b=b[:-1]+b' '*(len(raw)-len(b))+b'\n';put(p,b);m.F06_CONTRACT['root_current_proof']=ref(p);c=m.F06_CONTRACT
  refused(branch+':active_gate_'+label,lambda:a.current_gate(c,'NEW',x['state'],x['state_raw'],x['state_path'],m._f06_reference_read))
 put(p,raw);m.F06_CONTRACT['root_current_proof']=original_ref;c=m.F06_CONTRACT
 # Default nonreference IO remains1MiB; link/symlink protection remains original.
 other=d/'SYNTHETIC-unbound-large.json';put(other,raw)
 refused(branch+':unbound_path_default_stays1MiB',lambda:m._f06_reference_read(other),'Unsafe file type, link count, or size');other.unlink()
 link=d/'SYNTHETIC-hardlink.json';os.link(p,link)
 refused(branch+':hardlinked_proof_refused',lambda:m._f06_bounded_reference_read(c['root_current_proof']),'Unsafe file type, link count, or size');link.unlink()
 alias=d/'SYNTHETIC-symlink.json';alias.symlink_to(p)
 refused(branch+':symlink_refused',lambda:m._f06_reference_read(alias),'Symlink path refused');alias.unlink()
 # State private=False is still permitted only on original nonref default path.
 good(branch+':nonprivate_state_reader_unchanged',m._f06_reference_read(x['state_path'],private=False)==x['state_raw'])
 # Each exact leaf checks its own pin; contradictory metadata cannot read the file.
 refused(branch+':alternate_leaf_hash_same_path_refused',lambda:m._f06_bounded_reference_read(dict(c['root_current_proof'],sha256='f'*64)),'F06_BOUNDED_REFERENCE_CHANGED')
 good(branch+':direct_path_reader_retains_original1MiB_default',m._f06_reference_read.__defaults__ is None)
 invalid_reader=lambda path:raw
 invalid_reader.f06_read_reference=False
 refused(branch+':noncallable_optional_callback_refused',lambda:a.readref(c['root_current_proof'],invalid_reader),'F06_BOUNDED_REFERENCE_CALLBACK_REQUIRED')
 invalid_reader.f06_read_reference=None
 refused(branch+':present_None_callback_refused',lambda:a.readref(c['root_current_proof'],invalid_reader),'F06_BOUNDED_REFERENCE_CALLBACK_REQUIRED')
 # Callback results never bypass the original adapter's own declared-byte/SHA check.
 lying_reader=lambda path:raw
 lying_reader.f06_read_reference=lambda r:b'X'*r['bytes']
 refused(branch+':callback_return_revalidated_by_real_adapter',lambda:a.readref(c['root_current_proof'],lying_reader),'F06_REFERENCE_CHANGED')
for label,fn in [('unowned_open',lambda:open('/etc/hostname','rb')),('network',lambda:socket.socket()),('subprocess',lambda:subprocess.Popen(['/bin/true']))]:refused('confinement_'+label,fn,'SYNTHETIC_STAND_')
result=dict(status='SOURCE_QUALIFICATION_PASS',checks=CHECKS,count=len(CHECKS),seams=SEAMS,audit=AUDIT,revision=2,declared_reference_protocol='optional read.f06_read_reference(exactref); no recursive metadata traversal',actual_ordinary_consumer='NOT_RUN',actual_current_checker='NOT_RUN',actual_api_model_office_telegram=False,semantic_privacy_formal_F06='NOT_RUN_NOT_ACCEPTED',whole_consumer_stop='BEFORE_FIRST_SAVE_AND_SEND',peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
put(B/'QUALIFICATION-RESULT.json',enc(result));print(json.dumps({'status':result['status'],'count':len(CHECKS),'audit':AUDIT,'result':ref(B/'QUALIFICATION-RESULT.json')},sort_keys=True))
