"""Exact actual SOURCE composition, AST only; never execute the old executor.

All operation/authority/current/once refs are explicitly synthetic placeholders.
No Store, Runner object, metadata observation or API client is constructed.
"""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import types

OUT=Path(__file__).parent
for kind,limit in ((resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,512*1024**2),
                   (resource.RLIMIT_FSIZE,100*1024**2)):
    resource.setrlimit(kind,(limit,limit))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(path,raw):return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def load(raw,path):
    module=types.ModuleType('_exact_inert_source');module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__);return module

pin=json.loads((OUT/'PARENT_PREP_PIN.json').read_bytes())
prepraw=Path(pin['path']).read_bytes()
assert ref(pin['path'],prepraw)==pin
p=load(prepraw,pin['path'])
adapterpath=OUT/'presentation_current209.py';adapterraw=adapterpath.read_bytes()
m=load(adapterraw,adapterpath)
assert m.PREP==pin
basepath=Path(p.SELECTED_TESTER);base=basepath.read_bytes();assert sha(base)==p.SELECTED_SHA
candidate=Path(p.CANDIDATE['path']).read_bytes()
synthetic=lambda name:dict(path=str(OUT/('SYNTHETIC-UNBOUND-'+name+'.json')),bytes=1,sha256='a'*64)
original={k:synthetic(k) for k in p.ORIGINAL_REFS}
original.update(run=dict(path='/home/jericho/.local/share/friday-telegram-bot-test/runs/'+p.SOURCE_REF['run_id']+'.json',
        bytes=1,sha256=p.SOURCE_REF['run_sha256']),source_native_ingress=3289,source_platform_message_id='4211',original_sent_id=2138)
unit=dict(schema='frw.PRESENTATION.retained-original-upload.v1',source_reference=p.clone(p.SOURCE_REF),
    original_alias=p.ALIAS,original=original,principal=p.PRINCIPAL,
    conversation=dict(session_id=p.SID,session_key=m.KEY),
    current_source=dict(path=str(OUT/'SYNTHETIC-workspace'/p.ALIAS),bytes=48100,sha256=p.SOURCE_SHA,
        stat=dict(device=1,inode=1,size_bytes=48100,uid=1000,mtime_ns=1,ctime_ns=1)),Root_binding=synthetic('Rootbinding'))
phase=p.preparation(candidate,retained_unit=unit,runtime_basis=synthetic('runtime'))
run_id='synthetic-presentation-exact-source-control'
authority=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,
    authority_id='synthetic-inert-source-authority',run_scenarios={run_id:phase['scenario_sha256']},
    history={'synthetic-shape-only':{'sha256':'a'*64}},ordered_predecessors={},
    unknown_effects_resolved=False,old_rows_modified=False,new_trial_for_historical_task=False,product_or_B00_acceptance=False,
    no_old_task_replay=True,new_independent_inputs_only=True,
    presentation_original_case=dict(case_id='F-04',case_index=165,direction='PPTX_TO_ODP',genuinely_missing_original_forward=True,
        no_converter_or_App_replay=True,source_reference=p.SOURCE_REF,original_alias=p.ALIAS,principal=p.PRINCIPAL,
        conversation=unit['conversation']),
    presentation_task=dict(kind='ordinary-document-task',nonce='cccccccccccccccccccccccccccccccc',
        request=phase['scenario']['steps'][0]['request'],source_reference=p.SOURCE_REF,output=dict(filename=None,mime_type=p.ODP)))
authority_ref=ref(OUT/'SYNTHETIC-UNBOUND-authority.json',p.encoded(authority))
ordinary=p.compose_source(base,phase,run_id=run_id,authority_ref=authority_ref,authority=authority,retained_unit=unit)
composed=m.compose_preintent_source(ordinary,phase=phase,run_id=run_id,authority_ref=authority_ref,authority=authority,
    proof_ref=synthetic('Rootproof'),checker_ref=ref(adapterpath,adapterraw),retained_unit=unit)

def methods(raw):
    runner=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Runner')
    return {n.name:n for n in runner.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

old=methods(ordinary);new=methods(composed)
assert set(old)==set(new)
unchanged=[]
for name in old:
    if name=='ordinary_independent_admission':continue
    assert ast.dump(old[name],include_attributes=False)==ast.dump(new[name],include_attributes=False),name
    unchanged.append(name)
assert ast.dump(ast.Module(body=old['ordinary_independent_admission'].body,type_ignores=[]),include_attributes=False)==\
    ast.dump(ast.Module(body=new['ordinary_independent_admission'].body[1:],type_ignores=[]),include_attributes=False)
first=new['ordinary_independent_admission'].body[0]
assert isinstance(first,ast.If) and first.test.comparators[0].value==run_id
calls=[n for n in ast.walk(first) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='check']
assert len(calls)==1
assert ast.dump(old['send_ack_budget'],include_attributes=False)==ast.dump(new['send_ack_budget'],include_attributes=False)
observations=dict(schema='frw.PRESENTATION.current209-exact-source-composition-checks.v1',
    state='SOURCE_AST_ONLY_NOT_RUNTIME_QUALIFICATION',completed_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),
    checks=[dict(name='final_pinned_actual_parent_preparation_source',status='PASS'),
            dict(name='actual_cc36_source_exactbyte_pinned_without_executor',status='PASS'),
            dict(name='actual_shared_history_compat_composition_only',status='PASS'),
            dict(name='every_original_composed_Runner_method_preserved_except_single_admission_prefix',status='PASS'),
            dict(name='exact_original_admission_body_preserved_after_new_check',status='PASS'),
            dict(name='exact_current_case_only_check_hook',status='PASS'),
            dict(name='original_ACK10_and_historical_row_budget_method_unchanged_by_checker',status='PASS')],
    count=7,failures=[],unchanged_method_count=len(unchanged),unchanged_methods=unchanged,
    source_refs=dict(preparation=pin,checker=ref(adapterpath,adapterraw),selected_tester=ref(basepath,base),shared_history_helper=p.SHARED),
    composed_ordinary_source=dict(bytes=len(ordinary),sha256=sha(ordinary)),
    combined_current_source=dict(bytes=len(composed),sha256=sha(composed)),
    observations='Synthetic shape-only refs; no authority/ref files written, no actual canonical/ACK/history bodies read.',
    old_executor_executions=0,Store_objects_created=0,actual_current_calls=0,actual_product_operations=0)
(OUT/'EXACT-COMPOSITION-CHECKS.json').write_text(json.dumps(observations,sort_keys=True,indent=2)+'\n')
(OUT/'EXACT-COMPOSITION-CHECKS.json').chmod(0o600)
print(json.dumps({'checks':7,'unchanged_Runner_methods':len(unchanged),'actual_runtime_calls':0}))
