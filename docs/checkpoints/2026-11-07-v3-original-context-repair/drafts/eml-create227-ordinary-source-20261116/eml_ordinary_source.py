"""Pure independent ordinary EML CREATE and genuine-received EDIT binding for the actual cc36 ordinary consumer.

No import IO, issuer, current observation, actor, nonce, operation or API.
Root supplies real authority AND an independently accepted current checker/proof.
The final tester candidate keeps the existing sender/atomic/custody/stop paths.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import types

SELECTED_TESTER = '/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py'
SELECTED_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
HISTORY_HELPER_SHA = '6eb474ec654cb789be3a70ce783fa3abb40a4c6528a1b06b3afe376d721f6cb6'
READONLY_HISTORY_SHA = '0f1ff7f29b8f63a099b983756c21756fc8ec35b4e002e28979441ae67af3b9cf'


CREATE_REQUEST = 'Подготовь локальный файл supply-note.eml: отправитель supply@example.org, получатель planning@example.org, тема «Сверка поставки — ноябрь». Текст письма должен состоять ровно из трёх строк: «Коллеги, сверяем поставку за ноябрь.», «Количество: 24 комплекта; сумма: 18 750,50 RUB.» и «Ответственный: Анна Белова. Контрольная строка: склад № 7 — готово.». Сохрани письмо в формате EML без вложений и верни сам файл в этой беседе. Само письмо никому не отправляй.'
EDIT_REQUEST = 'В ранее присланном notice_saved.eml замени только тему письма на «Уведомление — согласовано ✅». Сохрани отдельную копию notice-approved.eml и верни её файлом в этой беседе. Исходный файл не меняй; отправителя, получателей, текст, вложение и остальные байты письма сохрани. Само письмо никому не отправляй.'
CREATE_SUBJECT='Сверка поставки — ноябрь'
EDIT_SUBJECT='Уведомление — согласовано ✅'
CREATE_BODY='Коллеги, сверяем поставку за ноябрь.\nКоличество: 24 комплекта; сумма: 18 750,50 RUB.\nОтветственный: Анна Белова. Контрольная строка: склад № 7 — готово.'
EXPECTED_FROM='supply@example.org'
EXPECTED_TO=['planning@example.org']
OUTPUTS={'create':{'filename':'supply-note.eml','mime_type':'message/rfc822'},'edit':{'filename':'notice-approved.eml','mime_type':'message/rfc822'}}
TIMING = dict(operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900)
OBSERVE = dict(mode='bounded_reply_capture',window_seconds=480,max_messages=32,max_text_chars=8000,max_documents=1,document_max_bytes=1048576)
ORIGINAL_CASE = {'case_ids':['F-01','F-02','F-03'],'case_indexes':[162,163,164],'format':'eml','format_index':108,'original_fixture_ref':'FX-FMT','scope':'independent ordinary plain-text CREATE and previously-received Subject-only copy EDIT; not full cases/format/B00','maximum_trials_per_operation':1}
ROOT_BINDING = {'state':'ROOT_UNBOUND','installed_target':227,'current_admission':False,'execution_grant':False,'live_effects':False}


def need(ok,code):
    if not ok: raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()
def clone(value): return json.loads(encoded(value))
def same(a,b): return encoded(a)==encoded(b)


def canonical_path(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and str(Path(value))==value and all(p not in ('','.','..') for p in value.split('/')[1:])
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value),'EMLCE_CANONICAL_PATH_REQUIRED')
    value.encode('utf-8'); return value


def reference_shape(value):
    if not (type(value) is dict and set(value)=={'path','bytes','sha256'}
            and type(value['bytes']) is int and 0<value['bytes']<=24*1024**2
            and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}',value['sha256'])): return False
    try: canonical_path(value['path']); return True
    except (ValueError,UnicodeError): return False


def operation_of(scenario):
    need(type(scenario)is dict and type(scenario.get('steps'))is list and len(scenario['steps'])==1,'EMLCE_EXACT_SINGLE_STEP_REQUIRED')
    req=scenario['steps'][0].get('request')
    need(req in (CREATE_REQUEST,EDIT_REQUEST),'EMLCE_EXACT_NATURAL_REQUEST_REQUIRED')
    return 'create' if req==CREATE_REQUEST else 'edit'


def received_source_shape(binding):
    need(type(binding)is dict and set(binding)=={'source_path','source_sha256','source_bytes','source_identity','received_artifact','receipt','native_ingress','native_original_read','source_unchanged','genuine_previously_received','original_first_read_preserved'},'EMLCE_REAL_PREVIOUSLY_RECEIVED_JOIN_REQUIRED')
    for k in ('received_artifact','receipt','native_ingress','native_original_read'):need(reference_shape(binding[k]),'EMLCE_RECEIVED_EXACT_REF_REQUIRED:'+k)
    need(binding['source_sha256']=='b308061ec10acc4d9b8f4bf45935da238b5ba851e1da9a5a64d4ec2a0e8b7928' and binding['source_bytes']==1579 and binding['source_sha256']==binding['received_artifact']['sha256'] and binding['source_bytes']==binding['received_artifact']['bytes'],'EMLCE_GENUINE_RECEIVED_B308_BYTES_REQUIRED')
    canonical_path(binding['source_path'])
    need(type(binding['source_identity'])is dict and set(binding['source_identity'])=={'device','inode','uid','size_bytes','mtime_ns','ctime_ns'} and all(type(v)is int and v>=0 for v in binding['source_identity'].values()),'EMLCE_NATIVE_SOURCE_IDENTITY_REQUIRED')
    need(binding['source_identity']['size_bytes']==binding['source_bytes'] and all(binding[k]is True for k in ('source_unchanged','genuine_previously_received','original_first_read_preserved')),'EMLCE_RECEIVED_SOURCE_INVARIANCE_REQUIRED')
    return True


def scenario_data(operation='create',*,received_source=None,tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot'):
    need(operation in ('create','edit'),'EMLCE_SUPPORTED_OPERATION_REQUIRED')
    need((tester_id,peer_id,peer_username)==(8812646969,8751854128,'@jerichodevbot') and type(tester_id)is type(peer_id)is int,'EMLCE_EXACT_TESTER_PEER_REQUIRED')
    if operation=='create':need(received_source is None,'EMLCE_CREATE_HAS_NO_SOURCE')
    else:received_source_shape(received_source)
    return dict(tester_id=tester_id,peer_id=peer_id,peer_username=peer_username,deadline_seconds=600,max_updates=64,pace_seconds=1,steps=[dict(request=CREATE_REQUEST if operation=='create'else EDIT_REQUEST,observe=clone(OBSERVE))])


def validate_scenario_data(scenario):
    operation=operation_of(scenario)
    expected=dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=600,max_updates=64,pace_seconds=1,steps=[dict(request=CREATE_REQUEST if operation=='create'else EDIT_REQUEST,observe=clone(OBSERVE))])
    need(same(scenario,expected),'EMLCE_EXACT_ONE_TEXT_REQUEST_NO_UPLOAD_RESET_OR_ORACLE_REQUIRED')
    return True


def preparation(scenario):
    validate_scenario_data(scenario);operation=operation_of(scenario)
    return dict(schema='frw.EML.create-edit.ordinary.source-preparation.v1',state='ROOT_UNBOUND',source_only=True,current_admission=False,execution_grant=False,original_case=clone(ORIGINAL_CASE),operation=operation,scenario=clone(scenario),scenario_sha256=digest(encoded(scenario)),timing=clone(TIMING),new_task_kind='ordinary-document-task',output=clone(OUTPUTS[operation]),source_reference=None,request_sha256=digest(scenario['steps'][0]['request'].encode()),actual_request_or_reply=False,future_native_write_returned_bytes_custody_semantics='POSTCONDITIONS_ONLY',requires_genuine_previously_received_join=operation=='edit',create_output_is_not_edit_source=True)


def _load_pure(raw,want,name):
    need(type(raw) is bytes and digest(raw)==want,'EMLCE_PINNED_STATIC_SOURCE_CHANGED')
    module=types.ModuleType(name);module.__file__='<pinned-static-source>'
    exec(compile(raw,module.__file__,'exec'),module.__dict__);return module


def _ordinary_source(base_raw,history_helper_raw,readonly_history_raw):
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'EMLCE_SELECTED_TESTER_CHANGED')
    helper=_load_pure(history_helper_raw,HISTORY_HELPER_SHA,'_emlce_retained_history_compat')
    readonly=_load_pure(readonly_history_raw,READONLY_HISTORY_SHA,'_emlce_exact_f03_readonly')
    # Only generic already-consumed history readers. Never F07 compose/phase.
    result=readonly.compose_source(helper.apply_history_compat(base_raw))
    tree=ast.parse(result);runners=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner']
    need(len(runners)==1,'EMLCE_EXACT_RUNNER_REQUIRED'); runner=runners[0]
    assignments={}
    for name in ('ORDINARY_INDEPENDENT_SCENARIOS','ORDINARY_INDEPENDENT_AUTHORITY'):
        nodes=[n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
        need(len(nodes)==1,'EMLCE_EXACT_ORDINARY_ASSIGNMENT_REQUIRED');assignments[name]=nodes[0]
    methods=[n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission']
    need(len(methods)==1,'EMLCE_EXACT_ADMISSION_REQUIRED');method=methods[0]
    authority=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261108-r44']
    counts=[n.comparators[0] for n in ast.walk(method) if isinstance(n,ast.Compare) and ast.unparse(n)=="len(document['history']) != 40"]
    need(len(authority)==len(counts)==1,'EMLCE_EXACT_AUTHORITY_HISTORY_SEAMS_REQUIRED')
    return result,assignments,authority[0],counts[0],method


def source_plan(base_raw,history_helper_raw,readonly_history_raw):
    compatible,assignments,authority,count,method=_ordinary_source(base_raw,history_helper_raw,readonly_history_raw)
    return dict(schema='frw.EML.create-edit.ordinary.static-plan.v1',state='SOURCE_ONLY_UNBOUND_NOT_GRANTED',
        original_case=clone(ORIGINAL_CASE),selected_tester_sha256=SELECTED_SHA,compatible_sha256=digest(compatible),
        seam_lines={**{k:n.lineno for k,n in assignments.items()},'authority_id':authority.lineno,
                    'history_count':count.lineno,'mandatory_Root_current_gate':method.body[-1].lineno},
        current_gate_abi='check(proof_ref, run_id=name, scenario=scenario, stage=getattr(self, _send_phase, NEW))',
        authority_issued=False,current_observed=False,grant=False,run_created=False,clock_created=False,
        future_native_write_returned_bytes_custody_reply='POSTCONDITIONS_ONLY')


def validate_authority_shape(authority,authority_ref,*,run_id,scenario):
    """Shape only. Original consumer and Root current authenticate real custody."""
    validate_scenario_data(scenario);operation=operation_of(scenario)
    need(type(run_id)is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id) and 'UNBOUND'not in run_id,'EMLCE_ROOT_UNUSED_RUN_REQUIRED')
    need(reference_shape(authority_ref) and type(authority)is dict and authority_ref['bytes']==len(encoded(authority)) and authority_ref['sha256']==digest(encoded(authority)),'EMLCE_EXACT_REAL_ROOT_AUTHORITY_REF_REQUIRED')
    need(authority.get('schema')=='frw.Root.ordinary-independent-history-admission.v1' and authority.get('operator')=='Root' and authority.get('accepted')is True and type(authority.get('authority_id'))is str and bool(authority['authority_id']) and 'UNBOUND'not in authority['authority_id'] and same(authority.get('run_scenarios'),{run_id:digest(encoded(scenario))}) and type(authority.get('history'))is dict and len(authority['history'])>=40 and same(authority.get('ordered_predecessors'),{}) and all(authority.get(k)is False for k in ('unknown_effects_resolved','old_rows_modified','new_trial_for_historical_task','product_or_B00_acceptance')) and authority.get('no_old_task_replay')is True and authority.get('new_independent_inputs_only')is True,'EMLCE_REAL_ROOT_ORDINARY_AUTHORITY_REQUIRED')
    need(same(authority.get('eml_original_case'),ORIGINAL_CASE) and authority.get('eml_operation')==operation and reference_shape(authority.get('eml_effect_eligibility_reconciliation')) and reference_shape(authority.get('eml_installed227_current_assessment')),'EMLCE_ROOT_ELIGIBILITY_AND_INSTALLED227_CURRENT_REQUIRED')
    if operation=='create':need(authority.get('eml_received_source')is None,'EMLCE_CREATE_HAS_NO_SOURCE')
    else:received_source_shape(authority.get('eml_received_source'))
    return True


def compose_source(base_raw,history_helper_raw,readonly_history_raw,*,scenario,run_id,
                   authority,authority_ref,current_checker_ref,current_proof_ref):
    """Pure future binding; returns Source, never current admission or execution.

    The inserted checker is mandatory before the existing ordinary admission
    returns, after its authority/current/history reads and before new/save/intent.
    Root MUST independently accept that checker for original EML create/edit scope, installed227 and effect eligibility,
    current mutable metadata, and genuine previously received source custody for EDIT.
    """
    validate_authority_shape(authority,authority_ref,run_id=run_id,scenario=scenario)
    need(reference_shape(current_checker_ref) and current_checker_ref['bytes']<=1024**2
         and reference_shape(current_proof_ref),'EMLCE_EXACT_ROOT_CURRENT_GATE_AND_PROOF_REQUIRED')
    need(current_checker_ref['path']!=authority_ref['path']
         and current_proof_ref['path'] not in (authority_ref['path'],current_checker_ref['path']),
         'EMLCE_SEPARATE_ROOT_CURRENT_BINDINGS_REQUIRED')
    compatible,assignments,authority_node,count_node,method=_ordinary_source(base_raw,history_helper_raw,readonly_history_raw)
    lines=compatible.decode().splitlines(keepends=True);changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{run_id:digest(encoded(scenario))}),('ORDINARY_INDEPENDENT_AUTHORITY',authority_ref)]:
        n=assignments[name];changes.append((n.lineno,n.end_lineno,'    '+name+' = '+repr(value)+'\n'))
    for n,value in [(authority_node,authority['authority_id']),(count_node,len(authority['history']))]:
        changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+repr(value)+lines[n.lineno-1][n.end_col_offset:]))
    gate=("        if name == "+repr(run_id)+":\n"
          "            _emlce_ref = "+repr(current_checker_ref)+"\n"
          "            _emlce_raw = safe_read(Path(_emlce_ref['path']))\n"
          "            if len(_emlce_raw) != _emlce_ref['bytes'] or digest(_emlce_raw) != _emlce_ref['sha256']:\n"
          "                raise Refused('EMLCE exact Root current checker changed')\n"
          "            import types as _emlce_types\n"
          "            _emlce_current = _emlce_types.ModuleType('_Root_EMLCE_historical_recall_current')\n"
          "            _emlce_current.__file__ = _emlce_ref['path']\n"
          "            exec(compile(_emlce_raw, _emlce_current.__file__, 'exec'), _emlce_current.__dict__)\n"
          "            _emlce_result = _emlce_current.check("+repr(current_proof_ref)+", run_id=name, scenario=scenario,\n"
          "                                             stage=getattr(self, '_send_phase', 'NEW'))\n"
          "            if _emlce_result is not True:\n"
          "                raise Refused('EMLCE Root current checker must explicitly return True')\n")
    need(isinstance(method.body[-1],ast.Return) and ast.unparse(method.body[-1].value)=='document',
         'EMLCE_EXACT_ADMISSION_RETURN_REQUIRED')
    changes.append((method.body[-1].lineno,method.body[-1].lineno-1,gate))
    need(len({lo for lo,_,_ in changes})==5,'EMLCE_OVERLAPPING_SOURCE_SEAMS_REFUSED')
    for lo,hi,replacement in sorted(changes,reverse=True):lines[lo-1:hi]=[replacement]
    result=''.join(lines).encode();ast.parse(result);return result


def qualify_selected_ordinary_readonly(runner,*,run_id,scenario):
    """Existing full pre-save prefix, without new/save/API/clock creation.

    ROOT ONLY on actual state. Isolated tests may use the real methods against
    their explicitly isolated reader. The real Root gate remains mandatory.
    """
    validate_scenario_data(scenario)
    need(runner.api is None,'EMLCE_READONLY_API_MUST_BE_NONE')
    qualified=runner._f07_qualify_new_prefix_readonly(run_id,scenario)
    admission=runner.ordinary_independent_admission(run_id,scenario)
    need(admission is not None,'EMLCE_EXACT_ORDINARY_ADMISSION_REQUIRED')
    runner.ordinary_independent_current_rows(admission,run_id)
    need(qualified['scenario_sha256']==digest(encoded(scenario)),
         'EMLCE_READONLY_SCENARIO_CHANGED')
    return dict(state='EMLCE_WHOLE_PRE_SAVE_READONLY_QUALIFIED_NOT_ADMISSION',
        original_new_prefix=qualified,original_case=clone(ORIGINAL_CASE),scenario_sha256=digest(encoded(scenario)),
        upload_planned=False,upload_executed=False,new_session_planned=False,
        future_native_write_returned_artifact_required_now=False,
        new_called=False,save_called=False,API_called=False,send_called=False,
        once_claim_created=False,operation_clock_created=False)


if __name__=='__main__':
    raise SystemExit('REFUSED: Source binding only; no actor, authority, current or execution')
