"""Independent final pure review probes. Never constructs a Store or runtime client."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, os, resource, time, types

os.umask(0o077)
for kind,bound in ((resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,100*1024**2)):
    resource.setrlimit(kind,(bound,bound))
START=time.monotonic()
OUT=Path(__file__).parent
ROOT=OUT.parent
checks=[]
def enc(v): return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def ref(path,raw): return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def load(path):
    raw=path.read_bytes();m=types.ModuleType('_independent_'+path.stem);m.__file__=str(path)
    exec(compile(raw,str(path),'exec'),m.__dict__);return m
def ok(name,condition,detail=None):
    assert condition,name
    checks.append(dict(name=name,status='PASS',detail=detail))
def reject(name,fn):
    try: fn()
    except (ValueError,TypeError,KeyError):
        checks.append(dict(name=name,status='PASS_REFUSED'));return
    raise AssertionError(name+' accepted')
def methods(raw):
    t=ast.parse(raw);c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
    return {n.name:n for n in c.body if isinstance(n,ast.FunctionDef)}
def dump(n): return ast.dump(n,include_attributes=False)
def fn(raw,name): return next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name)

paths=[ROOT/name for name in ('presentation_prepare.py','root_presentation_once.py','presentation_postconditions.py','presentation_current209.py')]
pins=[ref(path,path.read_bytes()) for path in paths]
p=load(paths[0]);d=load(paths[1]);c=load(paths[3])
ok('final_checker_exact_preparation_pin',c.PREP==pins[0])
old_adapter=ROOT/'current-adapter/presentation_current209.py'
old_tree=ast.parse(old_adapter.read_bytes());new_tree=ast.parse(paths[3].read_bytes())
changed=[(x,y) for x,y in zip(old_tree.body,new_tree.body) if dump(x)!=dump(y)]
ok('accepted_adapter_delta_only_PREP_pin',len(old_tree.body)==len(new_tree.body) and len(changed)==1
   and isinstance(changed[0][0],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PREP' for t in changed[0][0].targets))

synthetic=lambda name:dict(path=str(OUT/('SYNTHETIC-'+name)),bytes=1,sha256='a'*64)
original={key:synthetic(key) for key in p.ORIGINAL_REFS}
original.update(run=dict(path='/home/jericho/.local/share/friday-telegram-bot-test/runs/'+p.SOURCE_REF['run_id']+'.json',bytes=1,sha256=p.SOURCE_REF['run_sha256']),
                source_native_ingress=3289,source_platform_message_id='4211',original_sent_id=2138)
unit=dict(schema='frw.PRESENTATION.retained-original-upload.v1',source_reference=copy.deepcopy(p.SOURCE_REF),original_alias=p.ALIAS,
          original=original,principal=p.PRINCIPAL,conversation=dict(session_id=p.SID,session_key=p.KEY),
          current_source=dict(path=str(OUT/'SYNTHETIC-workspace'/p.ALIAS),bytes=48100,sha256=p.SOURCE_SHA,
                              stat=dict(device=1,inode=1,size_bytes=48100,uid=1000,mtime_ns=1,ctime_ns=1)),Root_binding=synthetic('Root'))
candidate=Path(p.CANDIDATE['path']).read_bytes()
phase=p.preparation(candidate,retained_unit=unit,runtime_basis=synthetic('runtime'))
ok('exact_candidate_shape_positive_source_only',p.validate_preparation(phase))
for name,change in [
    ('ordinal_bool',lambda x:x.update(ordinal=True)),
    ('reply_window175',lambda x:x['timing'].update(reply_window_seconds=175)),
    ('ACK30',lambda x:x['timing'].update(ack_seconds=30)),
    ('future_output_hash_preintent',lambda x:x.update(future_output_sha256='0'*64)),
    ('V01_alias_mixed_with_V03',lambda x:x['retained_unit'].update(original_alias='received/telegram_7343_presentation_core.pptx')),
    ('current_source_bytes_bool',lambda x:x['retained_unit']['current_source'].update(bytes=True)),
    ('source_ingress_float',lambda x:x['retained_unit']['original'].update(source_native_ingress=3289.0)),
    ('other_conversation',lambda x:x['retained_unit']['conversation'].update(session_key='OTHER'))]:
    x=copy.deepcopy(phase);change(x);reject('preparation_refuses_'+name,lambda x=x:p.validate_preparation(x))
run_id='synthetic-independent-final-source-review'
authority=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,
 authority_id='SYNTHETIC-SOURCE-REVIEW-NOT-AUTHORITY',run_scenarios={run_id:phase['scenario_sha256']},
 history={'SYNTHETIC-unresolved-history':{}},ordered_predecessors={},unknown_effects_resolved=False,old_rows_modified=False,
 new_trial_for_historical_task=False,product_or_B00_acceptance=False,no_old_task_replay=True,new_independent_inputs_only=True,
 presentation_original_case=dict(case_id='F-04',case_index=165,direction='PPTX_TO_ODP',genuinely_missing_original_forward=True,
 no_converter_or_App_replay=True,source_reference=p.SOURCE_REF,original_alias=p.ALIAS,principal=p.PRINCIPAL,conversation=unit['conversation']),
 presentation_task=dict(kind='ordinary-document-task',nonce='a'*32,request=phase['scenario']['steps'][0]['request'],
 source_reference=p.SOURCE_REF,output=dict(filename=None,mime_type=p.ODP)))
authref=ref(OUT/'SYNTHETIC-authority',enc(authority))
ok('authority_shape_positive_source_only',p.authority_shape(authority,authref,run_id=run_id,phase=phase))
for name,change in [
 ('nonce_31_hex',lambda a:a['presentation_task'].update(nonce='a'*31)),
 ('nonce_33_hex',lambda a:a['presentation_task'].update(nonce='a'*33)),
 ('nonce_32_uppercase',lambda a:a['presentation_task'].update(nonce='A'*32)),
 ('nonce_32_nonhex',lambda a:a['presentation_task'].update(nonce='g'*32)),
 ('nonce_old_loose_identifier',lambda a:a['presentation_task'].update(nonce='SYNTHETIC-only-final-source')),
 ('case_index_float',lambda a:a['presentation_original_case'].update(case_index=165.0)),
 ('forward_truth_integer',lambda a:a['presentation_original_case'].update(genuinely_missing_original_forward=1)),
 ('replay_flag',lambda a:a.update(no_old_task_replay=False)),
 ('future_output_hash_required',lambda a:a['presentation_task']['output'].update(sha256='0'*64))]:
 a=copy.deepcopy(authority);change(a)
 reject('authority_refuses_'+name,lambda a=a:p.authority_shape(a,ref(OUT/'SYNTHETIC-authority',enc(a)),run_id=run_id,phase=phase))

base=Path(p.SELECTED_TESTER).read_bytes();shared=load(Path(p.SHARED['path']));shared.__source_raw__=Path(p.SHARED['path']).read_bytes()
compatible=shared.apply_history_compat(base)
composed=p.compose_source(base,phase,run_id=run_id,authority_ref=authref,authority=authority,shared_module=shared)
before,after=methods(compatible),methods(composed)
ok('entire_shared_composition_method_set_preserved',set(before)==set(after),len(after))
modified=[name for name in before if dump(before[name])!=dump(after[name])]
ok('only_selected_ordinary_admission_changed',modified==['ordinary_independent_admission'],modified)
for name in ('new','send','send_ack_budget','valid_send_budget','verify_capture_context','verify_window','receive_inventory'):
 ok('genuine_'+name+'_AST_unchanged',dump(methods(base)[name])==dump(after[name]))
checker_ref=pins[3];proofref=synthetic('future-Root-proof')
final_source=c.compose_preintent_source(composed,phase=phase,run_id=run_id,authority_ref=authref,authority=authority,
 proof_ref=proofref,checker_ref=checker_ref)
final_methods=methods(final_source)
ok('preintent_inserts_only_one_selected_method',set(final_methods)==set(after) and
   [name for name in after if dump(after[name])!=dump(final_methods[name])]==['ordinary_independent_admission'])
admission=final_methods['ordinary_independent_admission'];first=admission.body[0]
ok('current209_hook_precedes_entire_original_admission',isinstance(first,ast.If) and dump(ast.Module(body=admission.body[1:],type_ignores=[]))==
   dump(ast.Module(body=after['ordinary_independent_admission'].body,type_ignores=[])))
literal_values=[n.value for n in ast.walk(first) if isinstance(n,ast.Constant)]
ok('preintent_hook_exact_named_checker_and_proof',checker_ref['sha256'] in literal_values and proofref['sha256'] in literal_values and run_id in literal_values)
reject('composed_base_byte_drift_refused',lambda:c.compose_preintent_source(composed+b'\n',phase=phase,run_id=run_id,authority_ref=authref,authority=authority,proof_ref=proofref,checker_ref=checker_ref))
ok('separate_native_render_limits_preserved',c.NATIVE_RENDER_LIMITS==dict(outer_wall_seconds=40,inner_wall_seconds=35,inner_cpu_seconds=35,inner_as_bytes=2*1024**3,inner_file_bytes=16*1024**2))
ok('exact_consumer_limits_and_outer_timing',d.TIMING==p.TIMING==c.TIMING==dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600)
 and d.LIMITS==dict(cpu_seconds=120,max_rss_bytes=512*1024**2,disk_bytes=100*1024**2))
driver_raw=paths[1].read_bytes();execute=fn(driver_raw,'execute');child=fn(driver_raw,'owned_consumer')
calls=lambda n:[(x.lineno,ast.unparse(x.func)) for x in ast.walk(n) if isinstance(x,ast.Call)]
exec_calls=calls(execute);child_calls=calls(child)
line=lambda cc,name:min(n for n,cname in cc if cname==name)
ok('preclock_qualifier_before_first_immutable_claim_clock_and_child',line(exec_calls,'qualify_before_clock')<line(exec_calls,'H.new')<line(exec_calls,'subprocess.Popen'))
ok('child_resources_before_source_loading',line(child_calls,'H.child_limits')<line(child_calls,'source_inputs'))
ok('child_full_readonly_and_current_before_API_and_new',line(child_calls,'prep.qualify_selected_ordinary_readonly')<line(child_calls,'checker.observe')<line(child_calls,'module.BotAPI')<line(child_calls,'runner.new')<line(child_calls,'runner.send'))
ok('driver_reuses_no_old_F07_executor',not any(name in ast.unparse(ast.parse(driver_raw)) for name in ('H.execute(', 'H.owned_consumer(', 'H.readonly(')))

for path,pin in zip(paths,pins):ok('final_source_still_same_'+path.name,ref(path,path.read_bytes())==pin)
usage=resource.getrusage(resource.RUSAGE_SELF)
result=dict(schema='frw.SOL.Task38.independent-final-pure-review-checks.v1',scope='SOURCE_ONLY_SYNTHETIC_NO_RUNTIME_PASS',
 reviewed_sources=pins,checks=checks,counts={status:sum(c['status']==status for c in checks) for status in ('PASS','PASS_REFUSED')},
 elapsed_seconds=time.monotonic()-START,cpu_seconds=usage.ru_utime+usage.ru_stime,max_rss_kib=usage.ru_maxrss,
 limits=dict(cpu_seconds=120,wall_seconds=300,address_space_bytes=512*1024**2,per_file_bytes=100*1024**2),
 actual_Store_or_current_API_DB_H_config_main_Telegram_Office_model_product_send_install_service_effects=0,
 original_upload_authentication=False,runtime_accepted=False,formal_PASS=False)
(OUT/'CHECKS.json').write_bytes(enc(result));os.chmod(OUT/'CHECKS.json',0o600)
print(json.dumps(dict(counts=result['counts'],elapsed_seconds=result['elapsed_seconds'],cpu_seconds=result['cpu_seconds'],max_rss_kib=result['max_rss_kib'],checks_file=str(OUT/'CHECKS.json'))))
