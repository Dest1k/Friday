"""Focused synthetic reviewerfix seams. All fixtures are memory-only; no real IDs."""
import ast,copy,hashlib,json,os,sys,types
from pathlib import Path
R=Path(__file__).resolve().parent
B=R.parent
C=B/'candidate'
FIX=R/'fixed-source'
def load_raw(raw,p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m
A=load_raw((C/'f06_source.py').read_bytes(),C/'f06_source.py')
F=load_raw((FIX/'first_ingress.py').read_bytes(),FIX/'first_ingress.py')
OLD=load_raw((C/'first_ingress.py').read_bytes(),C/'first_ingress.py')
code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()}
fixture_text=ast.get_source_segment((B/'synthetic_controls.py').read_text(),next(n for n in ast.parse((B/'synthetic_controls.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='fixture'))
original_fixture=fixture_text
fixture_text=fixture_text.replace("task=tweak('task',dict(method=", "task=tweak('task',dict(filename='f06-new-encrypted.docx',mime_type=A.MIME,content_type='multipart/form-data; boundary=frw-'+'a'*64,body_sha256='b'*64,body_bytes=24000,method=")
fixture_text=fixture_text.replace("win=tweak('window',dict(run_id=", "win=tweak('window',dict(step=0,send_attempts=1,send_intent_at=0,send_dispatch_at=0,send_timeout_seconds=10,deadline=300,run_id=")
fixture_text=fixture_text.replace(" run=tweak('run',dict(id=", " hr,hsr=stored('receive-SYNTHETIC-first-0-1-0.json',dict(kind='terminal_complete',sequence=0,context=dict(run_id='SYNTHETIC-first',scenario_sha256=A.digest(A.encoded(scenario)),window=wsr,sent_message_id=11,deadline=300)))\n run=tweak('run',dict(step=0,sent_ids=[11],sent_at=1,send_intent_at=0,send_dispatch_at=0,send_timeout_seconds=10,deadline=300,seen=[],message_ids=[],observations=[],receive_head=hsr,receive_sequence=0,capture_window_complete=True,id=")
fixture_text=fixture_text.replace("binding=put('first-binding.json',{'contract':tweak('binding',old)})", "binding=put('first-binding.json',dict(schema='frw.Root.F06.exact-first-wrongread-binding.v1',source=put('original-bound-source.py',b'#SYNTHETIC-NO-ACTUAL-CONSUMER',True),whole_effect_sha256='c'*64,contract=tweak('binding',old)))")
fixture_text=fixture_text.replace(" closure=judgement('closure'", " original=judgement('original_custody','frw.Root.F06.first-original-consumer-custody.v1',dict(canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,bound_source=json.loads(data[binding['path']])['source'],base_consumer_sha256=F.BASE_SHA,assessed_methods=['verify_capture_context','verify_window','verify_reply_custody','receive_inventory'],first_status=run['status'],capture_window_complete_present='capture_window_complete' in run,capture_window_complete=run.get('capture_window_complete'),original_clock_and_window_preserved=True,all_existing_raw_and_receipts_verified=True,known_partial_not_upgraded=True,late_arrivals_raw_only=True,first_semantic_PASS_required=False,acceptance='NOT_ESTABLISHED',receive_head=run.get('receive_head'),receive_sequence=run.get('receive_sequence'),method_assessment='VERIFIED_ORIGINAL_EXISTING_CUSTODY' if run.get('receive_head') else 'ORIGINAL_MISSING_HEAD_FAILURE_PRESERVED',receive_custody='VERIFIED_EXISTING_FULL_OR_PARTIAL' if run.get('receive_head') else 'MISSING_ORIGINAL_RECEIVE_HEAD_FAILURE_PRESERVED',missing_receive_failure_code='SYNTHETIC_ORIGINAL_FAILURE',terminal_receive=hr,retained_basis=[dummy]))\n closure=judgement('closure'")
fixture_text=fixture_text.replace("dict(actor_tree_closed=True", "dict(original_consumer_custody=original,actor_tree_closed=True")
fixture_ns=dict(A=A,F=F,C=C,code=code,json=json)
exec(compile(fixture_text,'SYNTHETIC_REVIEW_FIXTURE','exec'),fixture_ns)
fixture=fixture_ns['fixture']
old_fixture_ns=dict(A=A,F=OLD,C=C,code=code)
exec(compile(original_fixture,'SYNTHETIC_OLD_FIXTURE','exec'),old_fixture_ns)
original_fixture=old_fixture_ns['fixture']
caller_raw=(FIX/'root_bind_dispatch_once.py').read_bytes()
current_raw=(FIX/'current_root.py').read_bytes()
fixed_code={name:((FIX/name).read_bytes() if (FIX/name).exists() else (C/name).read_bytes()) for name in ('f06_source.py','f06_footer.py.txt','first_ingress.py','current_root.py','root_bind_dispatch_once.py')}
base_tree=ast.parse(A.BASE.read_bytes())
runner=next(n for n in base_tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
original_window=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='verify_window')
original_budget=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='valid_send_budget')
original_send_budget=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='send_ack_budget')
window_ns=dict(reply_capture=lambda x:x.get('mode')=='bounded_reply_capture',safe_read=lambda p:b'',json=json,digest=A.digest,MAX_JSON=24*1024**2,Refused=ValueError,unique_object=F.unique,math=__import__('math'),REPLY_WINDOW_RESERVE=5,REPLY_ACK_RESERVE=10)
cl=ast.ClassDef(name='PureOriginalWindow',bases=[],keywords=[],body=[original_window,original_budget,original_send_budget],decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[cl],type_ignores=[])),'EXTRACTED_PURE_ORIGINAL_WINDOW','exec'),window_ns)
PureWindow=window_ns['PureOriginalWindow']
'SYNTHETIC'.encode('utf-16-le')
def audit(event,args):
 if event=='open' or event.startswith(('socket.','subprocess.','os.system','os.exec','os.spawn')):raise RuntimeError('PURE_CONTROL_EFFECT_REFUSED')
sys.addaudithook(audit)
checks=[]
def ok(name,v=True):assert v,name;checks.append(name)
def refuses(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,AttributeError,IndexError):checks.append(name);return
 raise AssertionError(name)
def run_window(c,f,read):
 run=F.doc(f['canonical_run'],read);w=PureWindow();w.continuation_receipt=lambda r:None;w.store=types.SimpleNamespace(root=F.STATE)
 window_ns['safe_read']=read
 w.verify_window(run);return True
c,s,f,read,data=fixture()
ok('synthetic_complete_first_custody_bound',F.validate(c,read)==f)
ok('fixture_matches_exact_original_fullv42_window',run_window(c,f,read))
source_ref=json.loads(data[f['first_binding']['path']])['source']
data[source_ref['path']]=b'DRIFT'
refuses('original_bound_source_drift_refused',lambda:F.validate(c,read))
c,s,f,read,data=fixture()
source_ref=json.loads(data[f['first_binding']['path']])['source'];del data[source_ref['path']]
refuses('original_bound_source_missing_refused',lambda:F.validate(c,read))
c,s,f,read,data=fixture()
c0,s0,f0,r0,data0=original_fixture()
ok('initial_M1_accepts_missing_original_custody',OLD.validate(c0,r0)==f0)
refuses('fixed_rejects_initial_missing_base_fields_and_custody',lambda:F.validate(c0,r0))
for family,variants in {
 'run':[('missing_step',lambda d:d.pop('step')),('wrong_sent_ids',lambda d:d.update(sent_ids=[12])),('late_ACK',lambda d:d.update(sent_at=11)),('ACK_budget',lambda d:d.update(send_timeout_seconds=30)),('over_budget',lambda d:d.update(deadline=180)),('new_ack_override',lambda d:d.update(new_ack_timeout_seconds=10))],
 'task':[('wrong_filename',lambda d:d.update(filename='other.docx')),('wrong_MIME',lambda d:d.update(mime_type='other')),('missing_body',lambda d:d.pop('body_sha256')),('multipart_overflow',lambda d:d.update(body_bytes=33000))],
 'window':[('wrong_step',lambda d:d.update(step=1)),('wrong_attempts',lambda d:d.update(send_attempts=2)),('extended_deadline',lambda d:d.update(deadline=900)),('changed_intent',lambda d:d.update(send_intent_at=-1)),('changed_dispatch',lambda d:d.update(send_dispatch_at=-1)),('changed_timeout',lambda d:d.update(send_timeout_seconds=30))],
 'closure':[('missing_custody',lambda d:d.pop('original_consumer_custody'))],
 'original_custody':[('wrong_run',lambda d:d.update(canonical_run={})),('wrong_source',lambda d:d.update(bound_source={})),('wrong_base',lambda d:d.update(base_consumer_sha256='f'*64)),('missing_original_method',lambda d:d.update(assessed_methods=['verify_window'])),('upgrade_complete',lambda d:d.update(capture_window_complete=False)),('wrong_head',lambda d:d.update(receive_head={})),('semantic_gate',lambda d:d.update(first_semantic_PASS_required=True)),('graded',lambda d:d.update(acceptance='PASS')),('no_basis',lambda d:d.update(retained_basis=[])),('false_method_success',lambda d:d.update(method_assessment='ORIGINAL_MISSING_HEAD_FAILURE_PRESERVED'))]
}.items():
 for name,fn in variants:
  x,_,ff,r,_=fixture({family:fn});refuses(family+'_'+name,lambda x=x,r=r:F.validate(x,r))
for status in ('STOPPED','FAILED'):
 x,_,ff,r,_=fixture({'run':lambda d,status=status:d.update(status=status,capture_window_complete=False)})
 ok('known_partial_'+status+'_preserved',F.validate(x,r)==ff)
 def nohead(d,status=status):
  d.update(status=status);d.pop('capture_window_complete');d.pop('receive_head');d.pop('receive_sequence')
 x,_,ff,r,_=fixture({'run':nohead})
 ok('original_missing_head_'+status+'_failure_preserved',F.validate(x,r)==ff)
 x,_,ff,r,_=fixture({'run':nohead,'original_custody':lambda d:d.update(receive_custody='VERIFIED_EXISTING_FULL_OR_PARTIAL')})
 refuses('missing_head_'+status+'_cannot_claim_existing_verification',lambda x=x,r=r:F.validate(x,r))
# Caller pre-exec provenance checks exercise only prelude; load is a sentinel.
class ReachedLoad(Exception):pass
execute=next(n for n in ast.parse(caller_raw).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
own=FIX
memory={str(own/name):raw for name,raw in fixed_code.items()}
def rr(path):
 raw=memory[str(path)];return dict(path=str(path),bytes=len(raw),sha256=A.digest(raw))
freeze={'schema':'frw.F06.ordinary-singleton.source-freeze.v1','files':{name:{'bytes':len(raw),'sha256':A.digest(raw)} for name,raw in fixed_code.items()}}
fr={'path':'/SYNTHETIC/freeze','bytes':1,'sha256':'a'*64};rv={'path':'/SYNTHETIC/review','bytes':1,'sha256':'b'*64}
review={'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':A.digest(A.encoded(freeze)),'open_critical_defects':[]}
def caller_attempt(change=None):
 contract={field:rr(own/name) for field,name in (('adapter','f06_source.py'),('first_validator','first_ingress.py'),('actual_root_B_checker','current_root.py'),('footer','f06_footer.py.txt'))}
 v={'contract':contract,'source_freeze':fr,'independent_review':rv}
 if change:change(v)
 ns=dict(validate_inputs=lambda v:True,json=json,encoded=A.encoded,unique=F.unique,__file__=str(own/'root_bind_dispatch_once.py'),Path=Path,readref=lambda ref:A.encoded(freeze if ref==fr else review),need=A.need,digest=A.digest,read=lambda p:memory[str(p)],ref=rr,load=lambda *a:(_ for _ in ()).throw(ReachedLoad()))
 exec(compile(ast.Module(body=[execute],type_ignores=[]),'EXTRACTED_CALLER_PRELUDE','exec'),ns)
 return ns['execute'](v,binding_ref={})
try:caller_attempt()
except ReachedLoad:ok('exact_reviewed_local_source_reaches_first_load')
for field in ('adapter','first_validator','actual_root_B_checker','footer'):
 refuses('foreign_'+field+'_rejected_before_exec',lambda field=field:caller_attempt(lambda v:v['contract'][field].update(path='/SYNTHETIC/foreign.py')))
saved=freeze['files'].pop('first_ingress.py')
refuses('freeze_missing_first_validator_rejected_before_exec',caller_attempt)
freeze['files']['first_ingress.py']=saved
ok('current_checker_enforces_exact_local_validator_before_validate',current_raw.index(b"c['first_validator']==ref(HERE/'first_ingress.py'")<current_raw.index(b'first = a.validate_first(c,read)'))
print(json.dumps({'status':'PASS_FOCUSED_REVIEW_FIX_SYNTHETIC_ONLY','checks':checks,'count':len(checks),'real_refs_credentials_ACKs':0,'network_runtime_H_document_DB_native_effects':0},sort_keys=True))
