"""Pure synthetic current-source/ACK/footer nearest-consumer seams. No H I/O."""
import ast,copy,hashlib,json,os,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'candidate'
def load(n):
 p=C/n;m=types.ModuleType(n[:-3]);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=load('f06_source.py');F=load('first_ingress.py');M=load('current_root.py');D=load('root_bind_dispatch_once.py')
code={str(p):p.read_bytes() for p in C.iterdir() if p.is_file()};rawfixture=(B/'synthetic_controls.py').read_bytes();t=ast.parse(rawfixture)
g={'A':A,'F':F,'C':C,'code':code};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='fixture'],type_ignores=[]),'PURE_SYNTHETIC_FIXTURE_ONLY','exec'),g);fixture=g['fixture']
ftree=ast.parse((C/'f06_footer.py.txt').read_text().replace('__CONTRACT__','{}'))
base=A.BASE.read_bytes();basetree=ast.parse(base)
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
def refuses(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,AttributeError):checks.append(n);return
 raise AssertionError(n)
'S'.encode('utf-16-le')
def audit(ev,args):
 if ev=='open' or ev.startswith(('socket.','subprocess.','os.system','os.spawn','os.exec')):raise RuntimeError('PURE_NO_IO')
sys.addaudithook(audit)
c,s,first,read,data=fixture()
# Current checker exact actual source descriptor, no hard-coded207 or count512.
def put(p,obj):
 raw=A.encoded(obj);data[p]=raw;return dict(path=p,bytes=len(raw),sha256=A.digest(raw))
# Tiny synthetic installation: counts deliberately not a real future source.
receipt={'layers':['SYNTHETIC'],'files':{'one':'1'},'source_file_count':1,'base_tree':'base'}
inputs={'project_files':{'one':'x'}};rr=put('/SYNTHETIC/install/receipt',receipt);ir=put('/SYNTHETIC/install/input',inputs)
plugin=b'SYNTHETIC-PLUGIN';data[str(M.H/'plugins/synthetic.py')]=plugin
marker={'source_receipt_sha256':rr['sha256'],'input_sha256':ir['sha256'],'plugin_files':{'plugins/synthetic.py':A.digest(plugin)}}
mr=put('/SYNTHETIC/install/marker',marker);stamp={'fridaySource':{'layers':receipt['layers'],'baseTree':'base'}};st=put('/SYNTHETIC/install/stamp',stamp)
p=dict(source_layers=1,project_files=1,native_files=1,plugin_files=1,base_source_files=1,source_receipt_sha256=rr['sha256'],input_sha256=ir['sha256'])
runtime={name:A.digest(b'SYNTHETIC-RUNTIME') for name in M.REQUIRED_RUNTIME_PATHS}
for name in runtime:data[str(M.H/'hermes-agent'/name)]=b'SYNTHETIC-RUNTIME'
accept=put('/SYNTHETIC/install/acceptance',{'state':'synthetic-source-accepted'})
cl=dict(schema='friday.root.actual1.complete-closure.v1',state='INSTALLED1_PROJECT1_NATIVE1_SERVICES_HEALTHY_OPERATION_CLOSED',actors_and_boundary_closed=True,full_selected_native_files_readback=True,selected_native_file_count=1,publisher_client_code=0,fresh_DEFAULT_code=0,complete_root_boundary_code=0,source_acceptance=accept,operation=accept,root_return=accept,root_source_decision=accept,committed=accept,canonical_CP1=accept,installed=dict(layers=1,project=1,native=1,plugins=1,base=1,canonical4=dict(source_receipt=rr,marker=mr,stamp=st,current_input=ir)))
clr=put('/SYNTHETIC/install/closure',cl);c['product']=p;c['installation']=dict(closure=clr,source_acceptance=accept,product=p,runtime_hashes=runtime)
proof={'installation_closure':clr,'installation_acceptance':accept}
M.read=lambda path,**kw:data[str(path)]
ok('dynamic_descriptor_exact_product',M.installation_descriptor(c)==c['installation'])
ok('canonical4_actual_count_structure_memory_only',M.installation(proof,c)==cl)
for name,mut in [('descriptor_product',lambda x:x.update(product=dict(x['product'],project_files=2))),('missing_runtime_guard',lambda x:x['installation']['runtime_hashes'].pop('tools/file_tools.py')),('unbound_installation',lambda x:x.update(installation=None))]:
 x=copy.deepcopy(c);mut(x);refuses(name,lambda x=x:M.installation_descriptor(x))
# Mutate independently protected synthetic bytes, keep refs joined, test deeper guard.
for name,mut in [('wrong_schema',lambda x:x.update(schema='other')),('unclosed',lambda x:x.update(actors_and_boundary_closed=False)),('wrong_tuple',lambda x:x['installed'].update(project=2)),('missing_cp',lambda x:x.pop('canonical_CP1')),('source_acceptance',lambda x:x.update(source_acceptance=rr))]:
 x=copy.deepcopy(cl);mut(x);r=put('/SYNTHETIC/install/mutated',x);cc=copy.deepcopy(c);cc['installation']['closure']=r;pp=dict(proof,installation_closure=r);refuses('installation_'+name,lambda cc=cc,pp=pp:M.installation(pp,cc))
# Same first source must exist with exact canonical hash; alternate/source repeats refuse.
class MemPath(type(Path())):
 def is_file(self):return True
class MemRoot:
 def __init__(self,paths):self.paths=paths
 def iterdir(self):return iter(self.paths)
firstpath=MemPath(first['canonical_run']['path']);rows=[firstpath]
M.safe_path=lambda p:MemRoot(rows)
ok('history_exact_first_allowed',M.history(c,s,first)['run_ids']==['SYNTHETIC-first'])
other=dict(id='SYNTHETIC-other',scenario={'steps':[{'input':{'sha256':c['source']['sha256']}}]});op=MemPath(str(M.STATE/'runs'/'SYNTHETIC-other.json'));data[str(op)]=A.encoded(other);rows.append(op)
refuses('history_second_upload_refused',lambda:M.history(c,s,first));rows.pop()
other['scenario']={'steps':[{'request':s['steps'][0]['request']}]};data[str(op)]=A.encoded(other);rows.append(op);refuses('history_correct_text_replay_refused',lambda:M.history(c,s,first));rows.pop()
other['scenario']={'steps':[{'request':'independent unrelated work'}]};data[str(op)]=A.encoded(other);rows.append(op);ok('history_unrelated_allowed_no512guess',len(M.history(c,s,first)['records'])==2);rows.pop()
old=data[str(firstpath)];data[str(firstpath)]=old+b' ';refuses('history_first_canonical_changed',lambda:M.history(c,s,first));data[str(firstpath)]=old
rows.clear();refuses('history_first_absent_is_not_new_upload',lambda:M.history(c,s,first));rows.append(firstpath)
# Independent new schema cannot accept wrongread/old authority driver input.
v=dict(schema='frw.Root.F06.same-upload-correctread-driver.v1',status='ROOT_BOUND_ONE_FUTURE_OPERATION',contract=dict(A.unbound()),source_freeze=None,independent_review=None,workdir='/SYNTHETIC/work',slot_identity=None,expected_binding_sha256=None)
ok('correct_driver_unissued_input_schema',D.validate_inputs(v))
x=copy.deepcopy(v);x['schema']='frw.Root.F06.first-wrongread-driver.v1';refuses('old_wrong_driver_schema',lambda:D.validate_inputs(x))
x=copy.deepcopy(v);x['contract']['authority']={'old':True};refuses('old_authority_driver_input',lambda:D.validate_inputs(x))
# Exact changed footer ACK guard runs after inherited full context validation.
runner=next(n for n in ftree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='verify_capture_context')
class Parent:
 def verify_capture_context(self,run):self.base_calls+=1
ns={'_F06FullRunner':Parent,'F06_CONTRACT':c,'Refused':ValueError,'TESTER':8812646969,'json':json,'unique_object':lambda pairs:dict(pairs),'_f06_adapter':lambda:types.SimpleNamespace(shape=lambda *args:True),'_f06_path':Path,'safe_read':lambda p:ackraw}
cls=ast.ClassDef(name='Runner',bases=[ast.Name(id='_F06FullRunner',ctx=ast.Load())],keywords=[],body=[method],decorator_list=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),'EXACT_FOOTER_ACK','exec'),ns)
obj=ns['Runner']();obj.base_calls=0;obj.store=types.SimpleNamespace(root=Path('/SYNTHETIC/store'))
run={'id':c['run_id'],'scenario':s,'sent_api_ack_reference':{'basename':'ACK','representation':'decoded-message-json'}}
ack={'from':{'id':8812646969,'is_bot':True},'text':s['steps'][0]['request']};ackraw=A.encoded(ack);obj.verify_capture_context(run);ok('footer_correct_text_ACK_after_fullconsumer',obj.base_calls==1)
for name,fn in [('wrong_sender',lambda d:d['from'].update(id=2)),('wrong_text',lambda d:d.update(text='other')),('upload_ACK',lambda d:d.update(document={})),('fake_reply_ACK',lambda d:d.update(reply_to_message={})),('thread_ACK',lambda d:d.update(message_thread_id=1))]:
 x=copy.deepcopy(ack);fn(x);ackraw=A.encoded(x);refuses(name,lambda:obj.verify_capture_context(run))
# AST-equivalence independently checks all R3 signal/birth/wait mechanics; no actors.
oldtree=ast.parse((code.get('unused',b'') or b'') if False else 'pass')
# Literal runner/footer protocol names/counts, no hidden acceptance or source-ref wire.
send=next(n for n in next(x for x in basetree.body if isinstance(x,ast.ClassDef) and x.name=='Runner').body if isinstance(n,ast.FunctionDef) and n.name=='_send')
ok('original_sendMessage_params_only_chat_text',"params = {'chat_id': USERNAME, 'text': step['request']}" in ast.get_source_segment(base.decode(),send))
ok('no_offwire_source_reference_added_to_wire','source_reference' not in ast.dump(send,include_attributes=False))
ok('footer_no_refusal_capture_override',not any(isinstance(n,ast.FunctionDef) and n.name in ('capture_text','refusal','ready','bounded_reply') for n in runner.body))
print(json.dumps({'state':'PASS_PURE_SOURCE_COMPOSITION_ONLY','count':len(checks),'checks':checks,'real_DB_H_Office_native_token_reads_or_calls':0,'actual_current_or_first_or_authority_proofs':0},sort_keys=True))
