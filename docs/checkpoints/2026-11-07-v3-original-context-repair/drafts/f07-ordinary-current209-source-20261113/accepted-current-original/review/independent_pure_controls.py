"""Independent AST-extracted SOURCE ONLY controls. No candidate/runtime import.
All evidence predicates below are explicitly synthetic RAM; no current proof.
"""
import ast,copy,datetime as dt,hashlib,json,math,os,re,sys,time,types
from pathlib import Path
ROOT=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT209-PREINTENT-COMPOSITION-20261113')
REVIEW=ROOT/'review'
SOURCE=ROOT/'source/current209.py'
CALLER=ROOT/'source/root_caller.py'
FREEZE=ROOT/'SOURCE-FREEZE.json'
QUAL=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-F07-QUALIFICATION-PREP-20261113/qualify_current_scope.py')
allowed={str(SOURCE),str(CALLER),str(FREEZE),str(QUAL),str(ROOT/'controls/SOURCE-CONTROLS.json'),str(ROOT/'controls/check_source.py'),str(ROOT/'ROOT-USE.md')}
def audit(event,args):
 if event=='open':
  name=args[0]
  if isinstance(name,(str,bytes,os.PathLike)):
   p=os.fsdecode(name)
   if p not in allowed and not p.startswith(str(REVIEW)+'/'):
    raise RuntimeError('DENIED_NON_SOURCE_OR_REVIEW_OPEN')
 elif event in ('socket.__new__','socket.connect','subprocess.Popen','sqlite3.connect','os.system','os.exec','os.posix_spawn','os.fork'):
  raise RuntimeError('DENIED_LIVE_OR_PROCESS_EFFECT')
sys.addaudithook(audit)
raw=SOURCE.read_bytes();caller_raw=CALLER.read_bytes();freeze_raw=FREEZE.read_bytes();freeze=json.loads(freeze_raw)
assert hashlib.sha256(freeze_raw).hexdigest()=='dc5b1f2ab94362133c0f8cc62875b4a1c5f4682001216ebda1146c2c30ae154a'
for key,r in freeze['files'].items():
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
tree=ast.parse(raw);ctree=ast.parse(caller_raw);qual=ast.parse(QUAL.read_bytes())
names={'need','encoded','digest','clone','sha','unique','canonical_path','reference_shape','pristine','fresh','postcondition_plan','assess_saved_actual','assess_unconfirmed_closure'}
ns={'__builtins__':__builtins__,'json':json,'hashlib':hashlib,'re':re,'Path':Path,'dt':dt,'math':math,'time':types.SimpleNamespace(time=lambda:1000000.0,monotonic=lambda:1000.0),'EXACT_LIMIT':24*1024**2,'LOGGING_SITES':('agent/turn_context.py','gateway/run_turn.py'),'PRINCIPAL':{'SYNTHETIC':'principal'}}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(SOURCE)+':AST-pure-only','exec'),ns)
rows=[]
def test(name,fn):
 fn();rows.append({'name':name,'state':'PASS'})
def reject(fn,code=None):
 try:fn()
 except (ValueError,TypeError) as exc:
  if code is not None:assert str(exc)==code,(str(exc),code)
  return
 raise AssertionError('EXPECTED_REFUSAL')
phase={'phase':'TRUNCATED_CONTAINER','ordinal':3,'scenario':{'steps':[{'input':{'sha256':'a'*64,'filename':'truncated.docx'}}]},'scenario_sha256':'b'*64,'expected_semantics':'truthful_safe_malformed_rejection'}
effect={'run_id':'SYNTHETIC-INDEPENDENT-ONLY','phase':phase,'installation_closure':{'path':'/SYNTHETIC/closure','bytes':1,'sha256':'c'*64}}
now=1000000.0
row={'id':effect['run_id'],'scenario':copy.deepcopy(phase['scenario']),'scenario_sha256':phase['scenario_sha256'],'created_at':dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),'deadline':now+300,'step':0,'status':'PREPARED','send_state':'none','sent_ids':[],'seen':[],'message_ids':[],'observations':[],'update_count':0,'last_text':None,'repeat_count':0,'send_attempts':0,'capture_start_offset':0}
test('pristine_exact_fresh_original300',lambda:ns['pristine'](row,effect,now))
for key,value,code in [('send_attempts',1,None),('send_state','not_sent_rate_limited',None),('created_at',dt.datetime.fromtimestamp(now+1,dt.timezone.utc).isoformat(),'F07_OWN_PRISTINE_CREATION_CLOCK_CHANGED'),('deadline',now+214.999,None),('deadline',now+301,None),('scenario_sha256','d'*64,None),('extra_key',True,None)]:
 bad=copy.deepcopy(row);bad[key]=value
 test('pristine_reject_'+key+'_'+str(value)[:30],lambda bad=bad,code=code:reject(lambda:ns['pristine'](bad,effect,now),code))
proof={'created_at':now-1,'expires_at':now+30,'created_monotonic':999,'expires_monotonic':1030}
test('proof_dualclock_returns_min',lambda:ns['need'](ns['fresh'](proof,wall=now,mono=1000)==1030,'BAD_BOUND'))
for key,value in [('expires_at',now),('expires_monotonic',1000),('created_at',True),('created_monotonic',float('nan'))]:
 bad=copy.deepcopy(proof);bad[key]=value
 test('proof_reject_'+key,lambda bad=bad:reject(lambda:ns['fresh'](bad,wall=now,mono=1000)))
observed={'gateway':{'SYNTHETIC':'gateway'},'databases':{'tester':{'max_message_id':100}},'technical_log_cursor':{'SYNTHETIC':'cursor'},'installed':{'runtime_hashes':{'SYNTHETIC':'hash'}}}
plan=ns['postcondition_plan'](effect,observed)
test('preintent_plan_no_future_output_or_ID_equality',lambda:ns['need'](plan['future_output_required_preintent'] is False and plan['tester_ACK_message_id_is_native_platform_id'] is False and plan['raw_statuses_preserved'] is True and plan['no_extra_event_or_replay'] is True,'PLAN_REGRESSION'))
RAM={}
def put(name,value):
 raw=ns['encoded'](value);r={'path':'/SYNTHETIC_RAM/'+name,'bytes':len(raw),'sha256':ns['digest'](raw)};RAM[r['path']]=raw;return r
def readref(r,**kw):
 assert ns['reference_shape'](r);b=RAM[r['path']];assert len(b)==r['bytes'] and ns['digest'](b)==r['sha256'];return b
ns['read_reference']=readref;ns['doc']=lambda r,**kw:json.loads(readref(r))
ack={'message_id':200,'chat':{'id':8751854128},'from':{'id':8812646969,'is_bot':True}}
ackref=put('ACK.json',ack)
run={'id':effect['run_id'],'scenario_sha256':phase['scenario_sha256'],'status':'EVIDENCE_READY','send_state':'sent','send_attempts':1,'sent_message_id':200,'sent_api_ack_reference':dict(basename='ACK.json',bytes=ackref['bytes'],sha256=ackref['sha256'],representation='decoded-message-json'),'sent_at':now,'capture_until':now+180,'capture_window_complete':True,'acceptance':'NOT_ESTABLISHED'}
source_ref=put('source_ref.json',{'SYNTHETIC':'source_ref_not_actual'})
ingress={'schema':'frw.Root.F07.actual-native-ingress-correlation.v1','operator':'Root','run_id':effect['run_id'],'tester_ACK_message_id':200,'native_principal':ns['PRINCIPAL'],'native_platform_message_id':'777','native_message_row_id':101,'source_sha256':'a'*64,'filename':'truncated.docx','actual_source_ref_custody_checked':True,'actual_source_ref_evidence':source_ref}
refs={'canonical_run':put('run.json',run),'ACK':ackref,'native_ingress':put('ingress.json',ingress)}
for k in ('capture','technical_carriers','native_host_close'):refs[k]=put(k+'.json',{'SYNTHETIC':k+'_Root_assessed_only'})
assessment={'schema':'frw.Root.F07.actual-postcondition-assessment.v1','operator':'Root','status':'ROOT_ASSESSED_SAVED_ACTUAL_ONLY','plan':plan,'extra_event_or_replay_performed':False,'evidence':refs,'raw_status':'EVIDENCE_READY','raw_send_state':'sent','raw_consumer_acceptance':'NOT_ESTABLISHED','verdicts':dict(semantic='PASS',privacy='NOT_ESTABLISHED',custody='PASS',native_host_close='PASS'),'per_logging_site':{k:dict(execution='NOT_OBSERVED',verdict='NOT_ESTABLISHED',evidence=[]) for k in ns['LOGGING_SITES']}}
test('saved_actual_accepts_separate_decimal_native_ID_and_raw_ungraded',lambda:ns['need'](ns['assess_saved_actual'](assessment,effect=effect,observed=observed)['raw_consumer_acceptance']=='NOT_ESTABLISHED','REGRADING'))
for label,mutator in [('wrong_native_principal',lambda d:d.update(native_principal={'SYNTHETIC':'foreign'})),('old_native_row',lambda d:d.update(native_message_row_id=100)),('wrong_source_hash',lambda d:d.update(source_sha256='f'*64))]:
 bad=copy.deepcopy(assessment);x=copy.deepcopy(ingress);mutator(x);bad['evidence']['native_ingress']=put(label+'.json',x)
 test('saved_actual_reject_'+label,lambda bad=bad:reject(lambda:ns['assess_saved_actual'](bad,effect=effect,observed=observed),'F07_ACTUAL_NATIVE_SOURCE_REFERENCE_REQUIRED'))
bad=copy.deepcopy(assessment);bad['verdicts']['privacy']='PASS'
test('saved_actual_reject_privacy_PASS_without_logging',lambda:reject(lambda:ns['assess_saved_actual'](bad,effect=effect,observed=observed),'F07_PRIVACY_PASS_WITHOUT_ALL_OBSERVED_LOGGING_SITES'))
unknown=copy.deepcopy(run);unknown.update(status='UNKNOWN_SEND',send_state='unknown');uref=put('unknown.json',unknown)
closure={'schema':'frw.Root.F07.unconfirmed-technical-closure.v1','operator':'Root','run_id':effect['run_id'],'whole_effect_sha256':ns['digest'](ns['encoded'](effect)),'phase_successor_admitted':False,'raw_outcome_regraded':False,'extra_event_or_retry_performed':False,'semantic_verdict':'NOT_ESTABLISHED','canonical_run':uref,'raw_status':'UNKNOWN_SEND','raw_send_state':'unknown','closure_evidence':[source_ref]}
test('unknown_closure_no_ACK_or_native_ingress_required',lambda:ns['need'](ns['assess_unconfirmed_closure'](closure,effect=effect)['raw_send_state']=='unknown','UNKNOWN_RELABELED'))
for key,value in [('phase_successor_admitted',True),('raw_outcome_regraded',True),('extra_event_or_retry_performed',True),('semantic_verdict','PASS')]:
 bad=copy.deepcopy(closure);bad[key]=value
 test('unknown_reject_'+key,lambda bad=bad:reject(lambda:ns['assess_unconfirmed_closure'](bad,effect=effect),'F07_UNCONFIRMED_CLOSURE_UNBOUND'))
caller_ns={'__builtins__':__builtins__}
exec(compile(ast.Module(body=[n for n in ctree.body if isinstance(n,ast.FunctionDef) and n.name in {'need','qualify_selected_ordinary_readonly'}],type_ignores=[]),str(CALLER)+':AST-readonly-wrapper','exec'),caller_ns)
class SyntheticReadonlyStand:
 def __init__(self,api=None,admission=True):self.api=api;self.admission=admission;self.trace=[]
 def ordinary_independent_admission(self,name,scenario):self.trace.append(('admission',name,scenario));return {'SYNTHETIC':'admission'} if self.admission else None
 def ordinary_independent_current_rows(self,admission,name):self.trace.append(('current_rows',name));return True
 def new(self,*a,**k):raise AssertionError('DENIED_NEW')
 def send(self,*a,**k):raise AssertionError('DENIED_SEND')
stand=SyntheticReadonlyStand();ret=caller_ns['qualify_selected_ordinary_readonly'](stand,run_id=effect['run_id'],phase=phase)
test('readonly_wrapper_exact_two_calls_and_no_new_send',lambda:ns['need']([x[0] for x in stand.trace]==['admission','current_rows'] and ret['new_called'] is ret['send_called'] is False,'WRAPPER_SCOPE'))
test('readonly_wrapper_reject_API_object',lambda:reject(lambda:caller_ns['qualify_selected_ordinary_readonly'](SyntheticReadonlyStand(api=object()),run_id=effect['run_id'],phase=phase),'F07_READONLY_RUNNER_MUST_HAVE_NO_API'))
test('readonly_wrapper_reject_missing_admission',lambda:reject(lambda:caller_ns['qualify_selected_ordinary_readonly'](SyntheticReadonlyStand(admission=False),run_id=effect['run_id'],phase=phase),'F07_EXACT_SELECTED_ORDINARY_ADMISSION_REQUIRED'))
# Static relevant-pin equality is independent of parent runner fixtures.
getassign=lambda t,name:next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
cpins=ast.literal_eval(getassign(tree,'F07_PINS'));qpins=ast.literal_eval(getassign(qual,'REQUIRED_PINS'))
test('all_nine_relevant_pins_match_saved_qualification_source',lambda:ns['need'](cpins==qpins and len(cpins)==9,'DEPENDENCY_GAP'))
parent=json.loads((ROOT/'controls/SOURCE-CONTROLS.json').read_bytes())
test('parent112_controls_complete_and_source_only',lambda:ns['need'](parent['count']==len(parent['checks'])==112 and all(c['state']=='PASS' for c in parent['checks']) and parent['real_current_H_API_Store_new_send_tool_model_calls']==0,'PARENT_CONTROL_REPORT'))
report={'schema':'frw.F07.independent-pure-source-controls.v1','state':'PASS_SOURCE_ONLY_SYNTHETIC_NOT_ACTUAL_CURRENT','count':len(rows),'checks':rows,'source_sha256':hashlib.sha256(raw).hexdigest(),'freeze_sha256':hashlib.sha256(freeze_raw).hexdigest(),'guarded_non_source_open_or_live_effects':0,'scope':'AST-extracted pure functions with labelled synthetic RAM evidence; no candidate/runtime module import; no H/current/API/Store/new/send/tool/model calls','parent_controls_reused_not_rerun':True}
out=REVIEW/'INDEPENDENT-PURE-CONTROLS.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n');os.chmod(out,0o600)
print(json.dumps({'checks':len(rows),'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
