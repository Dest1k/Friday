import ast, contextlib, datetime, fcntl, hashlib, io, json, math, os, re, resource, signal, sqlite3, stat, subprocess, sys, time, types
import encodings.utf_16_le
from pathlib import Path
os.umask(0o077)
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'review'
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
START=time.monotonic();CPU=time.process_time();RESULTS=[];ACCESSES=[]
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
def audit(event,args):
 if event=='open' and not isinstance(args[0],int):
  p=Path(os.path.abspath(os.fsdecode(args[0])));flags=args[2]
  allowed=p.is_relative_to(ROOT) or p==BASE
  write=isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if not allowed or write and not p.is_relative_to(OUT):raise AssertionError('REVIEW_EXTERNAL_IO_REFUSED')
  ACCESSES.append({'path':str(p),'write':bool(write)})
 elif event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn') or event.startswith('socket.'):
  raise AssertionError('REVIEW_RUNTIME_EFFECT_REFUSED')
sys.addaudithook(audit)
def check(name,condition):
 if not condition:raise AssertionError(name)
 RESULTS.append({'name':name,'result':'PASS'})
def negative(name,call,expected=None):
 try:call()
 except (ValueError,TypeError,KeyError) as exc:
  if expected and expected not in str(exc):raise
  RESULTS.append({'name':name,'result':'REFUSED_AS_REQUIRED','error_class':type(exc).__name__,'code':str(exc)});return
 raise AssertionError(name+' unexpectedly accepted')
def module(leaf):
 raw=(ROOT/'candidate'/leaf).read_bytes();m=types.ModuleType('independent_review_'+leaf);m.__file__=str(ROOT/'candidate'/leaf)
 exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
A=module('f06_source.py');F=module('first_ingress.py');C=module('current_root.py');D=module('root_bind_dispatch_once.py')
check('imports_only_declared_source_files',all(Path(x['path']).is_relative_to(ROOT) for x in ACCESSES))
freeze_raw=(ROOT/'candidate/SOURCE-FREEZE.json').read_bytes();freeze=json.loads(freeze_raw)
check('exact_five_file_freeze_schema',freeze['schema']=='frw.F06.ordinary-singleton.source-freeze.v1' and set(freeze['files'])=={'f06_source.py','f06_footer.py.txt','current_root.py','first_ingress.py','root_bind_dispatch_once.py'})
for leaf,pin in freeze['files'].items():
 raw=(ROOT/'candidate'/leaf).read_bytes();check('freeze_'+leaf,len(raw)==pin['bytes'] and A.digest(raw)==pin['sha256'])
check('source_and_current_templates_unbound',A.unbound()['status']=='UNBOUND_NOT_GRANTED' and C.unbound_proof()['status']=='UNBOUND_NOT_GRANTED')
negative('unbound_driver_before_source_or_runtime',lambda:D.validate_inputs({}),'F06_DRIVER_UNBOUND_NO_EFFECT')
negative('unbound_contract_before_dependency',lambda:A.contract_shape(A.unbound()))
negative('unbound_current_before_actual_observation',lambda:C.validate_proof(C.unbound_proof()),'F06 genuine Root proof unbound')
spec={'kind':'literal_replace','old':'SYNTHETIC ONLY OLD " QUOTED \\ '+A.REQUEST_PASSWORD,'new':'SYNTHETIC ONLY NEW','expected_occurrences':1}
password='SYNTHETIC-WRONG-ONLY'
request=A.request_for(password,spec)
check('request_exact_quoted_roundtrip_even_delimiters',A.request_parts(request)==(password,spec))
check('request_wrong_only_no_history_and_zero_output',all(s in request for s in ('ТОЛЬКО','Не используй прежний правильный пароль','не отправляй файл')))
for suffix in (' extra','\n',' '+A.REQUEST_SUFFIX):negative('request_extra_'+repr(suffix),lambda suffix=suffix:A.request_parts(request+suffix))
for field,value in [('expected_occurrences',True),('expected_occurrences',2),('kind','regex'),('new',spec['old']),('old',''),('old','UNBOUND'),('old','line\nbreak')]:
 changed=dict(spec);changed[field]=value;negative('change_'+field+'_'+repr(value),lambda changed=changed:A.change_shape(changed))
negative('wrong_password_control',lambda:A.request_for('invalid\npassword',spec))
negative('wrong_password_256_units',lambda:A.request_for('x'*256,spec))
negative('wrong_password_surrogate',lambda:A.request_for('\ud800',spec))
first={'schema':'frw.Root.F06.closed-first-upload.v1','status':'ROOT_BOUND_CLOSED_RECONCILED','source':A.SOURCE,'source_reference':{'synthetic':True}}
correct={'schema':'frw.Root.F06.closed-correct-read.v1','status':'ROOT_BOUND_CORRECT_READ_ACCEPTED','source':A.SOURCE,'source_reference':first['source_reference']}
scenario=A.construct_scenario(supplied_password=password,change_spec=spec,first_dependency=first,correct_dependency=correct)
check('pure_constructor_is_only_shape_no_actual_admission',A.scenario_shape(scenario) is True and scenario['steps'][0]['observe']['max_documents']==0 and len(scenario['steps'])==1)
for field,value in [('status','RECEIVED_UNGRADED'),('schema','source-only-pass'),('source_reference',{})]:
 changed=dict(correct);changed[field]=value;negative('constructor_correct_'+field,lambda changed=changed:A.construct_scenario(supplied_password=password,change_spec=spec,first_dependency=first,correct_dependency=changed))
def synthetic_ref(raw,name):return {'path':str(OUT/name),'bytes':len(raw),'sha256':A.digest(raw)}
change_raw=A.encoded(spec);c={'change_spec':synthetic_ref(change_raw,'synthetic-change-never-written.json')}
check('canonical_change_scenario_join',A.change_binding(c,scenario,lambda p:change_raw))
different=dict(spec,new='SYNTHETIC DIFFERENT ROOT CHANGE');raw=A.encoded(different);c2={'change_spec':synthetic_ref(raw,'different-never-written.json')}
negative('precise_authorized_change_mismatch',lambda:A.change_binding(c2,scenario,lambda p:raw),'F06_AUTHORIZED_CHANGE_SCENARIO_MISMATCH')
raw=json.dumps(spec).encode();c2={'change_spec':synthetic_ref(raw,'noncanonical-never-written.json')}
negative('noncanonical_change_input',lambda:A.change_binding(c2,scenario,lambda p:raw),'F06_AUTHORIZED_CHANGE_SCENARIO_MISMATCH')
base=BASE.read_bytes();footer=(ROOT/'candidate/f06_footer.py.txt').read_bytes();check('exact_nearest_full_v42_source',A.digest(base)==A.BASE_SHA)
unbound=A.unbound();left=A.successor(base,unbound,footer);reordered=dict(reversed(list(unbound.items())));right=A.successor(base,reordered,footer)
check('whole_tree_order_reconstruction',left==right==A.successor(base,json.loads(A.encoded(unbound)),footer))
check('successor_parse_only_no_effect',bool(ast.parse(left)))
def method_map(raw,class_name):
 node=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name==class_name)
 return {n.name:ast.dump(n,include_attributes=False) for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
bm=method_map(base,'Runner');sm=method_map(left,'Runner')
check('original_full_consumer_runner_except_explicit_authority_seam',all(bm[k]==sm[k] for k in bm if k!='ordinary_independent_admission'))
check('explicit_refusal_capture_custody_stop_unchanged',all(bm[k]==sm[k] for k in ('verify_capture_context','verify_window','verify_reply_custody','receive_inventory','process','_send')))
check('review_leaf_not_in_freeze_no_self_reference','SOURCE-REVIEW.json' not in freeze['files'] and 'RESULT.json' not in freeze['files'])
result={'schema':'frw.Sol.Task30.independent-source-controls.v1','source_freeze_sha256':A.digest(freeze_raw),'checks':RESULTS,'actual_effects':'NOT_RUN','source_only':True,'synthetic_fixtures':True,'elapsed_wall_seconds':time.monotonic()-START,'elapsed_cpu_seconds':time.process_time()-CPU,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'allowed_io':['own B source/evidence read','exact underrepo fullv42 source read','own B/review write'],'accesses':ACCESSES,'caps':{'CPU_seconds':60,'AS_bytes':512*1024**2,'wall_supervisor_seconds':90,'cpus':2}}
raw=A.encoded(result);(OUT/'independent-controls.json').write_bytes(raw)
print(json.dumps({'checks':len(RESULTS),'source_freeze_sha256':result['source_freeze_sha256'],'elapsed_seconds':result['elapsed_wall_seconds'],'sha256':A.digest(raw)}))
