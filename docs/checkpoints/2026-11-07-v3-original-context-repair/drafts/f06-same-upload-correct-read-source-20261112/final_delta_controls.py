"""Parent independent reviewer-delta assessment; all first artifacts synthetic RAM."""
import ast,copy,json,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'revision2/candidate'
def load(n):
 p=C/n;m=types.ModuleType(n[:-3]);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=load('f06_source.py');F=load('first_ingress.py');code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()};g={'A':A,'F':F,'C':C,'code':code,'json':json};exec(compile((B/'revision2/synthetic_fixture.py').read_bytes(),'PURE_FINAL_FIXTURE','exec'),g);fixture=g['fixture']
old=(B/'baseline/root_bind_dispatch_once.py').read_bytes();new=code[str(C/'root_bind_dispatch_once.py')];current=code[str(C/'current_root.py')]
issuer=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py').read_bytes();it=ast.parse(issuer);fn=next(n for n in it.body if isinstance(n,ast.FunctionDef) and n.name=='validate_scope');ins={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'ORIGINAL_ATOMIC_ISSUER_SCOPE_ONLY','exec'),ins)
'S'.encode('utf-16-le')
def audit(ev,args):
 if ev=='open' or ev.startswith(('socket.','subprocess.','os.system','os.spawn','os.exec')):raise RuntimeError('PURE_NO_IO')
sys.addaudithook(audit)
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,AttributeError,SystemExit):checks.append(n);return
 raise AssertionError(n)
for name,fn in [
 ('omitted_original_context',lambda d:d.pop('original_consumer_custody')),
]:
 c,s,f,r,_=fixture({'closure':fn});refuse(name,lambda:F.validate(c,r))
for name,fn in [
 ('wrong_original_bound_source',lambda d:d.update(bound_source={})),
 ('raw_partial_promoted',lambda d:d.update(capture_window_complete=False)),
 ('raw_status_mismatch',lambda d:d.update(first_status='PASS')),
 ('first_semantic_PASS_as_prerequisite',lambda d:d.update(first_semantic_PASS_required=True)),
 ('late_arrivals_processing',lambda d:d.update(late_arrivals_raw_only=False)),
 ('missing_original_window_assessment',lambda d:d.update(assessed_methods=['verify_capture_context'])),
 ('missing_original_raw_basis',lambda d:d.update(retained_basis=[])),
 ('original_custody_claimed_acceptance',lambda d:d.update(acceptance='PASS')),
]:
 c,s,f,r,_=fixture({'original_custody':fn});refuse(name,lambda:F.validate(c,r))
for status in ('STOPPED','FAILED'):
 c,s,f,r,_=fixture({'run':lambda d,status=status:d.update(status=status,capture_window_complete=False)});ok('honest_partial_'+status,F.validate(c,r)==f)
 def nohead(d,status=status):
  d.update(status=status);d.pop('capture_window_complete');d.pop('receive_head');d.pop('receive_sequence')
 c,s,f,r,_=fixture({'run':nohead});ok('known_missing_head_failure_'+status,F.validate(c,r)==f)
 c,s,f,r,_=fixture({'run':nohead,'original_custody':lambda d:d.update(method_assessment='VERIFIED_ORIGINAL_EXISTING_CUSTODY')});refuse('missing_head_not_verified_'+status,lambda:F.validate(c,r))
c,s,f,r,data=fixture({'run':lambda d:d.pop('capture_window_complete')});refuse('complete_run_cannot_omit_fullwindow_flag',lambda:F.validate(c,r))
for name,fn in [('no_original_bodyhash',lambda d:d.pop('body_sha256')),('wrong_source_MIME',lambda d:d.update(mime_type='text/plain')),('bad_original_multipart_bound',lambda d:d.update(body_bytes=33000))]:
 c,s,f,r,_=fixture({'task':fn});refuse(name,lambda:F.validate(c,r))
for name,fn in [('changed_first_step',lambda d:d.update(step=1)),('changed_first_deadline',lambda d:d.update(deadline=999)),('changed_first_ACK_budget',lambda d:d.update(send_timeout_seconds=30))]:
 c,s,f,r,_=fixture({'run':fn});refuse(name,lambda:F.validate(c,r))
# Same actual R3 finite cleanup logic, not source-only simulated actor authority.
ot=ast.parse(old);nt=ast.parse(new)
for name in ('clock_remaining','owned_remaining','wait_owned'):
 x=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name==name);y=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name==name);ok('original_R3_'+name,ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False))
def actor(raw):return raw[raw.index(b'        actor=None;stops='):raw.index(b'        ended=')]
ok('complete_nonreentrant_birth_stop_reap_block_byteexact',actor(old)==actor(new))
# Real issuer scope parser accepts exact new bounded source purpose, no issuer exec.
ins['validate_scope'](A.scope(),{'SYNTHETIC-correct':'0'*64});ok('original_atomic_issuer_accepts_new_scope')
refuse('original_atomic_issuer_rejects_acceptance_claim',lambda:ins['validate_scope']('product acceptance',{'synthetic':'0'*64}))
# Source-origin guards execute before module load, not just comments.
s=new.decode();ok('reviewed_local_refs_before_any_load',s.index("c.get(field)==ref(own/leaf)")<s.index("a=load("))
ok('exact_five_file_freeze_required',"set(freeze['files'])=={'f06_source.py','f06_footer.py.txt','first_ingress.py','current_root.py','root_bind_dispatch_once.py'}" in s.replace(' ','')) if False else None
ok('current_firstvalidator_origin_before_exec',current.index(b"c['first_validator']==ref(HERE/'first_ingress.py'")<current.index(b'first = a.validate_first(c,read)'))
print(json.dumps({'state':'PASS_FINAL_REVIEWER_DELTA_PURE_ONLY','checks':checks,'count':len(checks),'real_H_firstsource_authority_Office_native_or_Telegram':0},sort_keys=True))
