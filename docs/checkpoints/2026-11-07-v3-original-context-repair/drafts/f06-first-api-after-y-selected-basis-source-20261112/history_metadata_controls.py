from pathlib import Path
import json,hashlib,types,copy
N=Path(__file__).parent
m=types.ModuleType('pure_current_admission_metadata');m.__file__=str(N/'source/root_bind_existing_consumer_once.py');exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
unknown=set(m.HISTORICAL_UNKNOWN_IDS)
h={k:dict(deadline=1.0,new_effect_replay_authorized=False,send_state='unknown' if k in unknown else 'none',sha256=hashlib.sha256(k.encode()).hexdigest(),status='STOPPED',unknown_retained=k in unknown) for k in [*m.HISTORICAL_UNKNOWN_IDS,*('SYNTHETIC-NONUSER-HISTORY-'+str(i) for i in range(42))]}
# Synthetic only known-hash substitution; exact production helper body runs.
m.HISTORICAL_HISTORY_SHA256=m.digest(m.encoded(h))
anchor=dict(gateway=dict(boot_id='00000000-0000-0000-0000-000000000001',pid=1000001,start_time=101))
v=dict(history=h,boot_id=anchor['gateway']['boot_id'],gateway=dict(pid=1000001,start_time=101,state_path=m.GATEWAY_STATE_PATH,maximum_staleness_seconds=600),canonical_encoding={'canonical_sha256':"json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(',', ':')) with no trailing newline",'tester_sha256':"bot_tester.encoded(scenario): json.dumps(scenario, ensure_ascii=True, sort_keys=True) + newline"},new_independent_inputs_only=True,no_old_task_replay=True,old_rows_modified=False,unknown_effects_resolved=False,product_or_B00_acceptance=False,new_trial_for_historical_task=False,same_canonical_local_run=False)
rows=[]
for case in ('positive','row_removed','row_added','history_hash','unknown_erased','replay_allowed','key_alias','boot','pid','birth','state_path','staleness','encoding','B00','new_trial','old_rows','unknowns_resolved','no_replay_false','ordered','memory'):
 c=copy.deepcopy(v)
 if case=='row_removed':c['history'].pop(next(iter(c['history'])))
 if case=='row_added':c['history']['SYNTHETIC-extra']={}
 if case=='history_hash':c['history'][next(iter(c['history']))]['sha256']='0'*64
 if case=='unknown_erased':c['history'][m.HISTORICAL_UNKNOWN_IDS[0]]['unknown_retained']=False
 if case=='replay_allowed':c['history'][m.HISTORICAL_UNKNOWN_IDS[0]]['new_effect_replay_authorized']=True
 if case=='key_alias':c['history']['../wrong-key']=c['history'].pop(next(iter(c['history'])))
 if case=='boot':c['boot_id']='00000000-0000-0000-0000-000000000002'
 if case=='pid':c['gateway']['pid']+=1
 if case=='birth':c['gateway']['start_time']+=1
 if case=='state_path':c['gateway']['state_path']+='.wrong'
 if case=='staleness':c['gateway']['maximum_staleness_seconds']=601
 if case=='encoding':c['canonical_encoding']['tester_sha256']='compact-no-newline'
 if case=='B00':c['product_or_B00_acceptance']=True
 if case=='new_trial':c['new_trial_for_historical_task']=True
 if case=='old_rows':c['old_rows_modified']=True
 if case=='unknowns_resolved':c['unknown_effects_resolved']=True
 if case=='no_replay_false':c['no_old_task_replay']=False
 if case=='ordered':c['ordered_predecessors']={}
 if case=='memory':c['memory_case']=None
 caught=None
 try:m.current_document_metadata(c,anchor)
 except ValueError as e:caught=e.args[0]
 assert (case=='positive')==(caught is None),(case,caught)
 rows.append(dict(case=case,passed=True,refusal=caught))
print(json.dumps(dict(controls=rows,count=len(rows),source_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),seam='HISTORICAL_HISTORY_SHA256 changed only in synthetic module; no actual R106/current authority/history body read; production code unchanged',actual_admission=False,provider_or_API=False)))
