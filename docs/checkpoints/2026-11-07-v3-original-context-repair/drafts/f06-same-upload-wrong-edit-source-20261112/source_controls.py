import ast,copy,hashlib,json,os,sys,types
from pathlib import Path
B=Path(__file__).resolve().parent;C=B/'candidate';rows=[]
def check(name,ok):
 if not ok:raise AssertionError(name)
 rows.append({'name':name,'outcome':'PASS'})
def reject(name,f):
 try:f()
 except (ValueError,TypeError,KeyError,UnicodeError):check(name,True)
 else:raise AssertionError(name)
def module(p):
 m=types.ModuleType('task30_pure');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=module(C/'f06_source.py');V=module(C/'first_ingress.py')
spec={'kind':'literal_replace','old':'SYNTHETIC «старый» 𝄞','new':'SYNTHETIC новый \\ "quoted"','expected_occurrences':1};pw='SYNTHETIC_WRONG_ONLY_𝄞'
first={'schema':'frw.Root.F06.closed-first-upload.v1','status':'ROOT_BOUND_CLOSED_RECONCILED','source':A.SOURCE,'source_reference':{'run_id':'SYNTHETIC_FIRST','run_sha256':'1'*64,'input_sha256':A.SOURCE['sha256']}}
correct={'schema':'frw.Root.F06.closed-correct-read.v1','status':'ROOT_BOUND_CORRECT_READ_ACCEPTED','source':A.SOURCE,'source_reference':first['source_reference']}
s=A.construct_scenario(supplied_password=pw,change_spec=spec,first_dependency=first,correct_dependency=correct)
check('natural_wrongedit_one_text_full180_zero_documents',A.scenario_shape(s))
check('private_literal_roundtrip_and_latestwrongonly',A.request_parts(s['steps'][0]['request'])==(pw,spec))
check('offwire_source_reference_no_upload_reply_or_path',set(s['steps'][0])=={'request','observe'} and '/home/' not in s['steps'][0]['request'] and 'source_reference' not in s['steps'][0]['request'])
check('no_implicit_correctedit_or_previous_credential_permission','Не используй прежний правильный пароль из истории' in s['steps'][0]['request'] and 'ничего не меняй' in s['steps'][0]['request'])
for name,mut in [('extra_step',lambda v:v['steps'].append(v['steps'][0])),('extra_upload',lambda v:v['steps'][0].update(input={'kind':'document'})),('fake_reply',lambda v:v['steps'][0].update(reply_to_message_id=1)),('output_permission',lambda v:v['steps'][0]['observe'].update(max_documents=1)),('shortwindow',lambda v:v['steps'][0]['observe'].update(window_seconds=179)),('wrong_chat',lambda v:v.update(peer_id=1)),('bool_tester',lambda v:v.update(tester_id=True)),('permit_history',lambda v:v['steps'][0].update(request=v['steps'][0]['request'].replace('Не используй прежний правильный пароль из истории','Используй прежний пароль'))),('extra_followup',lambda v:v['steps'][0].update(request=v['steps'][0]['request']+' Затем повтори с правильным паролем.'))]:
 v=copy.deepcopy(s);mut(v);reject(name,lambda v=v:A.scenario_shape(v))
for key,value in [('old',''),('new',spec['old']),('expected_occurrences',True),('expected_occurrences',2),('kind','arbitrary_code'),('old','x\nOTHER'),('old','UNBOUND')]:
 v=dict(spec);v[key]=value;reject('bad_change_'+key+'_'+str(len(rows)),lambda v=v:A.change_shape(v))
for password in ('','UNBOUND','x\nECHO','\ud800','𝄞'*128):reject('password_bound_'+str(len(rows)),lambda password=password:A.request_for(password,spec))
check('255_UTF16_units_not_codepoints',A.request_parts(A.request_for('𝄞'*127+'x',spec))[0]=='𝄞'*127+'x')
for key in ('schema','status','source_reference'):
 v=copy.deepcopy(correct);v[key]='SYNTHETIC_INVALID';reject('no_fake_correct_'+key,lambda v=v:A.construct_scenario(supplied_password=pw,change_spec=spec,first_dependency=first,correct_dependency=v))
# The exact private change must match the wire request at the real caller seam.
raw=A.encoded(spec);r={'path':'/SYNTHETIC/change.json','bytes':len(raw),'sha256':A.digest(raw)};c={'change_spec':r}
check('change_binding_real_method',A.change_binding(c,s,lambda p:raw))
v=copy.deepcopy(s);v['steps'][0]['request']=A.request_for(pw,dict(spec,new='SYNTHETIC OTHER'))
reject('different_change_request_refused',lambda:A.change_binding(c,v,lambda p:raw))
reject('noncanonical_change_bytes_refused',lambda:A.change_binding(c,s,lambda p:raw+b' '))
# Whole canonicalization retained exact; fresh nested refs added after initial JSON.
c=A.unbound();c.update(run_id='SYNTHETIC_WRONG_EDIT',scenario_sha256='2'*64)
c=json.loads(A.encoded(c));c['root_current_proof']={'path':'/SYNTHETIC/свежий.json','bytes':17,'sha256':'3'*64}
base=A.BASE.read_bytes();footer=(C/'f06_footer.py.txt').read_bytes();source=A.successor(base,c,footer);roundtrip=A.successor(base,json.loads(A.encoded(c)),footer)
check('fresh_nested_ref_actual_footer_exact_source_roundtrip',source==roundtrip)
t=ast.parse(source);check('full_generated_source_compiles',bool(compile(t,'SYNTHETIC_GENERATED_NOT_EXECUTED','exec')))
original=ast.parse(base);oldrunner=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='Runner');runner=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
oldmethods={n.name:ast.dump(n,include_attributes=False) for n in oldrunner.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};methods={n.name:ast.dump(n,include_attributes=False) for n in runner.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
check('191_methods_190_unchanged',len(oldmethods)==191 and sum(methods[k]==v for k,v in oldmethods.items())==190)
# Underlying permission-safe edit already exists; no product implementation here.
check('five_source_only_targets',len(list(C.glob('*.py')))==4 and (C/'f06_footer.py.txt').exists())
caller=(C/'root_bind_dispatch_once.py').read_text();before=(B/'before/root_bind_dispatch_once.py').read_text()
a='        actor=None;stops=[];forwarded_stops=0;wait_attempted=False;forwarding_stops=False';z="        ended={'schema':"
check('R3_birth_signal_drain_cleanup_block_byteexact',caller[caller.index(a):caller.index(z)]==before[before.index(a):before.index(z)])
check('source_freeze_before_first_load',caller.index('F06_REVIEWED_SOURCE_DRIFT')<caller.index('a=load('))
check('change_binding_before_once_issuer_and_birth',caller.index('a.change_binding(c,s,read)')<caller.index("new(work/'ROOT-ONCE-INVOCATION.json'")<caller.index('issuer=load(')<caller.index('actor=subprocess.Popen('))
check('exact_reconstruction_guard_retained',"json.loads(read(work/'ROOT-ACTUAL-BINDING.json'))['contract'],footer)==read(bound),'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE'" in caller)
check('canonical_whole_contract_before_repr',A.successor.__code__.co_names.index('canonical_contract')<A.successor.__code__.co_names.index('repr'))
for name in ('canonical_contract','canonical_path','current_gate'):
 old=next(n for n in ast.parse((B/'before/f06_source.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name);new=next(n for n in ast.parse((C/'f06_source.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
 check('unchanged_'+name,ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False))
check('original_first_ingress_contract_and_custody_unchanged', all(ast.dump(next(n for n in ast.parse((B/'before/first_ingress.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)==ast.dump(next(n for n in ast.parse((C/'first_ingress.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False) for name in ('validate','original_custody')))
# Persist only codes/hashes; no request/password/old-new strings in reports.
print(json.dumps({'schema':'frw.Sol.Task30.pure-source-controls.v1','synthetic_only':True,'actual_user_NOT_RUN':True,'count':len(rows),'checks':rows,'source_sha256':A.digest(source),'candidate':{p.name:A.digest(p.read_bytes()) for p in sorted(C.iterdir()) if p.is_file()},'generated_consumer_executed':False,'no_actual_credential_doc_H_STATE_reads':True},sort_keys=True))
