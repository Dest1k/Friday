#!/usr/bin/env python3
"""Small source controls. No installed marker, receipt, product home, or publication."""
import signal
signal.alarm(90)
import ast, contextlib, copy, hashlib, importlib.util, io, json, os, resource, shutil, stat, sys, tempfile, time
from pathlib import Path
START=time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
AFFINITY=sorted(os.sched_getaffinity(0))[:2]
os.sched_setaffinity(0,AFFINITY)
os.umask(0o077)
ROOT=Path(__file__).resolve().parent
BASE=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112/publication')
checks=[]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def checked(name,call):
 call(); checks.append({'name':name,'state':'PASS'})
def refused(call,code):
 try: call()
 except pub.Refused as exc: assert str(exc).startswith(code),(str(exc),code)
 else: raise AssertionError('not refused: '+code)
def assert_(value): assert value
pub=load(ROOT/'friday_v3_layer_publication.py','edge_pub')
builder=load(ROOT/'build-layer-publication-request.py','edge_builder')
basepub=load(BASE/'friday_v3_layer_publication.py','base_pub')
basebuilder=load(BASE/'build-layer-publication-request.py','base_builder')
NEW='f06-modern-odt-authenticated-profile-after-source206'
V='friday.current-source-native-successor.v'
checked('only_one_layer_added_and_historical_defaults_preserved',lambda:assert_(pub.LAYER_NAMES==basepub.LAYER_NAMES+(NEW,) and pub.HISTORICAL_LAYER_NAMES==basepub.HISTORICAL_LAYER_NAMES and builder.LAYER_NAMES==basebuilder.LAYER_NAMES and len(builder.LAYER_NAMES)==4))
checked('builder_dynamic_explicit_choice_accepts_new_layer',lambda:assert_(builder.parse_args(['--layer',NEW]).layer_names==(NEW,)))
checked('builder_no_layer_retains_four',lambda:assert_(builder.parse_args([]).layer_names==builder.LAYER_NAMES))
for opts in (['--layer','unrecognised-layer'],['--layer',NEW,'--layer',NEW]):
 def control(opts=opts):
  with contextlib.redirect_stderr(io.StringIO()):
   try: builder.parse_args(opts)
   except SystemExit as exc: assert exc.code==2
   else: raise AssertionError('parser accepted invalid layer')
 checked('parser_refuses_'+('_'.join(opts[1::2])),control)
# Execute the real builder's isolated context-construction AST block. No installed
# marker/receipt is fabricated, and build_request/product publication is never called.
tree=ast.parse((ROOT/'build-layer-publication-request.py').read_text())
build=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_request')
block=next(n for n in build.body if isinstance(n,ast.If) and 'current_source_project_update' in ast.unparse(n.test))
code=compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'actual-builder-context-block','exec')
from types import SimpleNamespace
with tempfile.TemporaryDirectory(prefix='context-controls-',dir=ROOT) as td:
 td=Path(td); root=td/'root-context-only.json'; pred=td/'predecessor-context-only.json'; root.write_bytes(b'{}\n')
 def context(previous_schema,layers):
  pred.write_bytes(pub.encoded({'current_source_successor':{'schema':previous_schema}}))
  args=SimpleNamespace(current_source_project_update=root,current_source_native_predecessor=pred,layer_names=layers)
  request={}; ns={'args':args,'request':request,'consumer':pub,'pin':builder.pin}
  exec(code,ns); return request['current_source_successor']
 old_layers={1:('ods-calc-retained-source-profile-after-source199',),2:('retained-calc-xlsx-destination-after-source200',),3:('rtf-rich-odp-followup-and-office-bank-after-source201',),4:('core-file-readability-and-context-provenance-after-source202',),5:('rtf-optional-footnote-reader-after-source203',),6:('core-user-result-contracts-after-source204',),7:('f06-protected-office-profiles-after-source205',),8:(NEW,)}
 for version,layers in old_layers.items():
  checked('builder_real_block_v%d_to_v%d'%(version,version+1),lambda version=version,layers=layers:assert_(context(V+str(version),layers)['schema']==V+str(version+1)))
 for layers in (old_layers[7],(NEW,'write-file-format-guard'),()):
  checked('v7_predecessor_refuses_inexact_eighth_layer_'+str(len(layers)),lambda layers=layers:refused(lambda:context(V+'8',layers),'transaction_current_source_exact_ninth_layer_required'))
 checked('v8_predecessor_is_not_a_ninth_edge',lambda:refused(lambda:context(V+'9',(NEW,)),'transaction_current_source_supported_predecessor_required'))
 request={'current_source_successor':{'schema':V+'9','root_project_update':builder.pin(root),'previous_native_update':builder.pin(pred)}}
 request_path=td/'new-context-only.json'
 def request_check(value,raw=None,expected_sha=None):
  raw=pub.encoded(value) if raw is None else raw; request_path.write_bytes(raw); request_path.chmod(0o600)
  return pub.current_source_request_bytes(value,request_path,expected_sha or pub.digest(raw))
 checked('v8_exact_owned_request_retained',lambda:assert_(request_check(request)==pub.encoded(request)))
 for version in range(1,9):
  value=copy.deepcopy(request); value['current_source_successor']['schema']=V+str(version)
  if version==1: del value['current_source_successor']['previous_native_update']
  checked('historical_request_v%d_keeps_acceptance'%version,lambda value=value:assert_(request_check(value)==pub.encoded(value)))
 for mutation,label in ((lambda c:c.pop('previous_native_update'),'missing_predecessor'),(lambda c:c.update(extra=True),'extra_field'),(lambda c:c.update(schema=V+'10'),'future_v9'),(lambda c:c['previous_native_update'].update(sha256='f'*63),'bad_reference_digest')):
  value=copy.deepcopy(request); mutation(value['current_source_successor'])
  expected='transaction_current_source_root_reference_required' if label=='bad_reference_digest' else 'transaction_current_source_context_required'
  checked('v8_refuses_'+label,lambda value=value,expected=expected:refused(lambda:request_check(value),expected))
 checked('v8_refuses_raw_request_sha_change',lambda:refused(lambda:request_check(request,expected_sha='0'*64),'transaction_current_source_raw_request_changed'))
 raw=pub.encoded(request)
 checked('v8_refuses_duplicate_json_keys',lambda:refused(lambda:request_check(request,raw=b'{"current_source_successor":null,"current_source_successor":null}\n'),'transaction_current_source_duplicate_json_key'))
# Inventory resolution is pure; these are project-inventory dictionaries, never receipts.
patch='patches/hermes/'+NEW+'.patch'; manifest='patches/hermes/'+NEW+'-manifest.json'
previous={'project_files':{'unchanged':'1'*64}}
current={'project_files':{**previous['project_files'],patch:'2'*64,manifest:'3'*64}}
req={'schema':pub.SCHEMA_EXPLICIT,'layer_names':[NEW],'project_inventory':current['project_files'],'project_inventory_sha256':pub.digest(pub.encoded(current['project_files'])),'plugin_additions':[],'plugin_set':[]}
checked('explicit_eighth_inventory_pair_accepted',lambda:assert_(pub.check_project_inventory(req,previous,current)==(NEW,)))
for names,code_refused in (([],'transaction_layer_names_empty'),([NEW,NEW],'transaction_layer_names_repeated'),(['unknown'],'transaction_layer_names_unknown')):
 bad=copy.deepcopy(req); bad['layer_names']=names
 checked('inventory_refuses_'+code_refused,lambda bad=bad,code_refused=code_refused:refused(lambda:pub.check_project_inventory(bad,previous,current),code_refused))
# Evaluate the actual guard expression: v8 enters the same CAS/rollback implementation.
ptree=ast.parse((ROOT/'friday_v3_layer_publication.py').read_text())
run=next(n for n in ptree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
guard=next(n.value for n in run.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='guarded_current' for t in n.targets))
guard_code=compile(ast.Expression(guard),'actual-guard-expression','eval')
for version in range(1,11):
 checked('guard_dispatch_v%d'%version,lambda version=version:assert_(eval(guard_code,{'current_context':True,'request':{'current_source_successor':{'schema':V+str(version)}}}) is (version in (5,6,7,8,9))))
# Real isolated filesystem controls on the unchanged journal selected by that guard.
# Generic targets only: no installed marker/receipt or product home is created.
with tempfile.TemporaryDirectory(prefix='cas-controls-',dir=ROOT) as td:
 td=Path(td); home=td/'owned'; home.mkdir(mode=0o700); existing=home/'existing'; absent=home/'absent'
 before=b'existing before\n'; after=b'owned after\n'; existing.write_bytes(before); existing.chmod(0o600)
 def journal(label):
  j=pub._CurrentSourceV5Journal(td/label,home,{str(existing):{'sha256':pub.digest(before),'bytes':len(before)},str(absent):None}); j.preflight(); return j
 j=journal('success')
 j.record_existing(existing,before); j.record_absent(absent)
 for target in (existing,absent): pub.publish(target,after,0o600,_before_replace=j.prepare_publication(target,after,0o600))
 assert existing.read_bytes()==after and absent.read_bytes()==after
 j.restore([existing,absent]); assert existing.read_bytes()==before and not absent.exists()
 checks.append({'name':'guarded_journal_real_publish_and_rollback_restores_bytes_and_absence','state':'PASS'})
 j=journal('late-failure'); j.record_existing(existing,before)
 pub.INJECT_AFTER_RENAME=True; pub.INJECT_TARGET=str(existing)
 try: pub.publish(existing,after,0o600,_before_replace=j.prepare_publication(existing,after,0o600))
 except OSError as exc: assert exc.errno == 5
 else: raise AssertionError('after-rename fault not injected')
 assert existing.read_bytes()==after
 j.restore([existing]); assert existing.read_bytes()==before
 checks.append({'name':'guarded_journal_real_failure_after_rename_rolls_back','state':'PASS'})
 j=journal('identity-change'); existing.unlink(); existing.write_bytes(before); existing.chmod(0o600)
 checked('CAS_refuses_same_bytes_different_inode',lambda:refused(lambda:j.record_existing(existing,before),'transaction_v5_recorded_preimage_changed'))
 existing.write_bytes(b'foreign bytes\n')
 checked('CAS_preflight_refuses_wrong_source_digest',lambda:refused(lambda:journal('bad-digest'),'transaction_v5_authenticated_preimage_changed'))
 existing.write_bytes(before); existing.chmod(0o664)
 checked('CAS_refuses_0664_target',lambda:refused(lambda:journal('bad-mode'),'transaction_v5_file_custody_changed'))
 existing.chmod(0o600); j=journal('foreign-rollback'); j.record_existing(existing,before)
 pub.publish(existing,after,0o600,_before_replace=j.prepare_publication(existing,after,0o600))
 existing.write_bytes(b'foreign bytes\n')
 checked('rollback_refuses_foreign_afterimage',lambda:refused(lambda:j.restore([existing]),'transaction_v5_restoration_foreign_state'))
 assert existing.read_bytes()==b'foreign bytes\n'
# Check base source remained byte-identical and save exact current source bindings.
expected={'friday_v3_layer_publication.py':'7e8e886adaf738296ded1fda09740df5b242d6ad3b98d4bcdb29d8ada672da9c','build-layer-publication-request.py':'f060007cb5bb04c932df5601a23b25ec36a891e831dc59dcf89c83d01d501647'}
for name,sha in expected.items(): assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==sha
result={'schema':'friday.f06.publication-edge.source-controls.v1','state':'PASS','checks':checks,'count':len(checks),'wall_seconds':round(time.monotonic()-START,6),'cpu_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'limits':{'wall_seconds':90,'cpu_seconds':60,'address_space_bytes':512*1024**2,'cpu_affinity':AFFINITY},'publication_called':False,'installed_receipt_fabricated':False,'artifacts':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (*expected,'PUBLICATION-EDGE.patch')}}
(ROOT/'CONTROLS.json').write_bytes(pub.encoded(result))
print(json.dumps({'state':result['state'],'count':len(checks),'seconds':result['wall_seconds'],'affinity':AFFINITY,'controls_sha256':hashlib.sha256((ROOT/'CONTROLS.json').read_bytes()).hexdigest()},sort_keys=True))
