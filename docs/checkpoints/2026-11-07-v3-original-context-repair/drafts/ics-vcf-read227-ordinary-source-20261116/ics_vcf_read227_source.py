"""Pure initial ICS/VCF READ227 upload binding for the actual cc36 ordinary consumer.

No import IO, issuer, current observation, actor, nonce, operation or API.
Root supplies real authority AND an independently accepted current checker/proof.
The final tester candidate keeps the existing sender/atomic/custody/stop paths.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import types

SELECTED_TESTER = '/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py'
SELECTED_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
V42_SHA = 'f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
HISTORY_HELPER_SHA = '6eb474ec654cb789be3a70ce783fa3abb40a4c6528a1b06b3afe376d721f6cb6'
READONLY_HISTORY_SHA = '0f1ff7f29b8f63a099b983756c21756fc8ec35b4e002e28979441ae67af3b9cf'
TIMING = dict(operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900)
OBSERVE = dict(mode='bounded_reply_capture',window_seconds=480,max_messages=32,max_text_chars=8000,max_documents=0,document_max_bytes=1048576)
ORIGINAL_CASE = dict(case_id='F-01',case_index=162,formats={'ics':110,'vcf':111},original_fixture_ref='FX-FMT',operation='initial_genuine_local_ICS_or_VCF_upload_read',maximum_trials_per_operation=1,scope='READ_ONLY_NO_IMPORT_NO_SEND_NO_FULL_FORMAT_APP_FORMAL_CREDIT')
PROFILES = {'ics': {'source': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/native/fixtures/maple_schedule.ics', 'bytes': 2075, 'sha256': 'ae16ca56024a1f5949552c773764cf9d8d6ca9b8332a2c182220741d3331db46'}, 'input_filename': 'maple_schedule.ics', 'mime_type': 'text/calendar', 'request': 'Прочитай приложенный календарь maple_schedule.ics целиком. Перечисли все события с названиями, датами и временем так, как они записаны, местами и важными примечаниями. Если есть часовой пояс или повторение, объясни именно записанные условия, не вычисляя новые даты. В конце укажи последнюю содержательную заметку и где она находится в файле.', 'request_ref': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/ordinary/REQUEST-ICS-READ.txt', 'bytes': 610, 'sha256': 'b30e4c0707daa0d694b23f19e556881c38537eabcf352146f8f7ed63d1588cb2'}, 'format_index': 110}, 'vcf': {'source': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/native/fixtures/maple_contacts.vcf', 'bytes': 2194, 'sha256': '301538a40aa3c00b0eff445b6b15f7a9e7dd338b55b109782942a890de69ad41'}, 'input_filename': 'maple_contacts.vcf', 'mime_type': 'text/vcard', 'request': 'Прочитай приложенный файл контактов maple_contacts.vcf целиком. Перечисли все контакты с именами, организациями, должностями, адресами электронной почты, телефонами и примечаниями. Сохрани различия между рабочими и другими адресами. В конце укажи последнюю содержательную заметку и где она находится в файле.', 'request_ref': {'path': '/home/jericho/.cache/FRW-SOL-V3-ICS-VCF-ORDINARY-READ-SOURCE-CORE-20261116/ordinary/REQUEST-VCF-READ.txt', 'bytes': 554, 'sha256': '544cf0e3f0b40d74d185cc663526ec5ae764d01fa454a7dadfe3d3318a77c9f6'}, 'format_index': 111}}
ROOT_BINDING = dict(state='ROOT_UNBOUND',installed_target=227,current_admission=False,execution_grant=False)
STAT_FIELDS = {'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
INPUT_FIELDS = {'kind','path','sha256','stat','filename','mime_type','caption'}


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
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value),'ICSVCF227_CANONICAL_PATH_REQUIRED')
    value.encode('utf-8'); return value


def reference_shape(value):
    if not (type(value) is dict and set(value)=={'path','bytes','sha256'}
            and type(value['bytes']) is int and 0<value['bytes']<=24*1024**2
            and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}',value['sha256'])): return False
    try: canonical_path(value['path']); return True
    except (ValueError,UnicodeError): return False


def input_data(family,source_stat):
    need(family in PROFILES,'ICSVCF227_EXACT_FAMILY_REQUIRED');p=PROFILES[family]
    need(type(source_stat)is dict and set(source_stat)==STAT_FIELDS and all(type(v)is int and v>=0 for v in source_stat.values()) and source_stat['inode']>0 and source_stat['uid']==os.getuid() and source_stat['size_bytes']==p['source']['bytes'],'ICSVCF227_CURRENT_SOURCE_IDENTITY_REQUIRED')
    return dict(kind='document',path=p['source']['path'],sha256=p['source']['sha256'],stat=clone(source_stat),filename=p['input_filename'],mime_type=p['mime_type'],caption=p['request'])

def family_of(scenario):
    need(type(scenario)is dict and type(scenario.get('steps'))is list and len(scenario['steps'])==1 and type(scenario['steps'][0])is dict and set(scenario['steps'][0])=={'input','observe'},'ICSVCF227_SINGLE_READ_UPLOAD_REQUIRED')
    upload=scenario['steps'][0].get('input');need(type(upload)is dict,'ICSVCF227_INITIAL_DOCUMENT_REQUIRED')
    matches=[f for f,p in PROFILES.items()if upload.get('caption')==p['request']]
    need(len(matches)==1,'ICSVCF227_EXACT_NATURAL_REQUEST_REQUIRED');return matches[0]

def operation_of(scenario):family_of(scenario);return 'read'


def validate_input(upload):
    need(type(upload)is dict and set(upload)==INPUT_FIELDS,'ICSVCF227_EXACT_INPUT_FIELDS_REQUIRED')
    matches=[f for f,p in PROFILES.items()if upload.get('caption')==p['request']]
    need(len(matches)==1 and same(upload,input_data(matches[0],upload.get('stat'))),'ICSVCF227_EXACT_FIRST_UPLOAD_INPUT_REQUIRED');return True


def scenario_data(upload,*,tester_id,peer_id,peer_username):
    validate_input(upload)
    need(type(tester_id)is int and tester_id>0 and type(peer_id)is int and peer_id>0 and tester_id!=peer_id and type(peer_username)is str and re.fullmatch('@[A-Za-z][A-Za-z0-9_]{4,31}',peer_username),'ICSVCF227_ROOT_PRINCIPALS_REQUIRED')
    return dict(tester_id=tester_id,peer_id=peer_id,peer_username=peer_username,deadline_seconds=600,max_updates=64,pace_seconds=1,steps=[dict(input=clone(upload),observe=clone(OBSERVE))])


def validate_scenario_data(scenario):
    need(type(scenario) is dict and type(scenario.get('steps')) is list and len(scenario['steps'])==1
         and type(scenario['steps'][0]) is dict and set(scenario['steps'][0])=={'input','observe'},
         'ICSVCF227_ONE_FIRST_DOCUMENT_REQUIRED')
    expected=scenario_data(scenario['steps'][0]['input'],tester_id=scenario.get('tester_id'),
                           peer_id=scenario.get('peer_id'),peer_username=scenario.get('peer_username'))
    need(same(scenario,expected),'ICSVCF227_EXACT_SOURCE_SCENARIO_REQUIRED')
    return True


def preparation(scenario):
    validate_scenario_data(scenario);family=family_of(scenario);p=PROFILES[family]
    return dict(schema='frw.ICSVCF.READ227.ordinary.Source-preparation.v1',state='ROOT_UNBOUND',source_only=True,current_admission=False,execution_grant=False,original_case=clone(ORIGINAL_CASE),family=family,operation='read',scenario=clone(scenario),scenario_sha256=digest(encoded(scenario)),timing=clone(TIMING),new_task_kind='ordinary-document-task',output=None,source_reference=clone(p['source']),actual_request_or_reply=False,native_ingress_read_reply_custody='FUTURE_POSTCONDITIONS_ONLY',source_fixture_is_not_received_or_admission_authority=True)


def _load_pure(raw,want,name):
    need(type(raw) is bytes and digest(raw)==want,'ICSVCF227_PINNED_STATIC_SOURCE_CHANGED')
    module=types.ModuleType(name);module.__file__='<pinned-static-source>'
    exec(compile(raw,module.__file__,'exec'),module.__dict__);return module


def _ordinary_source(base_raw,history_helper_raw,readonly_history_raw):
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'ICSVCF227_SELECTED_TESTER_CHANGED')
    helper=_load_pure(history_helper_raw,HISTORY_HELPER_SHA,'_icsvcf227_retained_history_compat')
    readonly=_load_pure(readonly_history_raw,READONLY_HISTORY_SHA,'_icsvcf227_exact_f03_readonly')
    # Only generic already-consumed history readers. Never F07 compose/phase.
    result=readonly.compose_source(helper.apply_history_compat(base_raw))
    tree=ast.parse(result);runners=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner']
    need(len(runners)==1,'ICSVCF227_EXACT_RUNNER_REQUIRED'); runner=runners[0]
    assignments={}
    for name in ('ORDINARY_INDEPENDENT_SCENARIOS','ORDINARY_INDEPENDENT_AUTHORITY'):
        nodes=[n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
        need(len(nodes)==1,'ICSVCF227_EXACT_ORDINARY_ASSIGNMENT_REQUIRED');assignments[name]=nodes[0]
    methods=[n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission']
    need(len(methods)==1,'ICSVCF227_EXACT_ADMISSION_REQUIRED');method=methods[0]
    authority=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261108-r44']
    counts=[n.comparators[0] for n in ast.walk(method) if isinstance(n,ast.Compare) and ast.unparse(n)=="len(document['history']) != 40"]
    need(len(authority)==len(counts)==1,'ICSVCF227_EXACT_AUTHORITY_HISTORY_SEAMS_REQUIRED')
    return result,assignments,authority[0],counts[0],method


def source_plan(base_raw,history_helper_raw,readonly_history_raw):
    compatible,assignments,authority,count,method=_ordinary_source(base_raw,history_helper_raw,readonly_history_raw)
    return dict(schema='frw.ICSVCF227.F01-first-upload-ordinary-static-plan.v1',state='SOURCE_ONLY_UNBOUND_NOT_GRANTED',
        original_case=clone(ORIGINAL_CASE),selected_tester_sha256=SELECTED_SHA,compatible_sha256=digest(compatible),
        seam_lines={**{k:n.lineno for k,n in assignments.items()},'authority_id':authority.lineno,
                    'history_count':count.lineno,'mandatory_Root_current_gate':method.body[-1].lineno},
        current_gate_abi='check(proof_ref, run_id=name, scenario=scenario, stage=getattr(self, _send_phase, NEW))',
        authority_issued=False,current_observed=False,grant=False,run_created=False,clock_created=False,
        future_ingress_native_read_and_reply='POSTCONDITIONS_ONLY')


def validate_authority_shape(authority,authority_ref,*,run_id,scenario):
    """Shape only; runtime original reader and Root checker authenticate custody."""
    validate_scenario_data(scenario)
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)
         and 'UNBOUND' not in run_id,'ICSVCF227_ROOT_UNUSED_RUN_REQUIRED')
    need(reference_shape(authority_ref) and type(authority) is dict
         and authority_ref['bytes']==len(encoded(authority)) and authority_ref['sha256']==digest(encoded(authority)),
         'ICSVCF227_EXACT_REAL_ROOT_AUTHORITY_REF_REQUIRED')
    need(authority.get('schema')=='frw.Root.ordinary-independent-history-admission.v1'
         and authority.get('operator')=='Root' and authority.get('accepted') is True
         and type(authority.get('authority_id')) is str and bool(authority['authority_id'])
         and 'UNBOUND' not in authority['authority_id']
         and same(authority.get('run_scenarios'),{run_id:digest(encoded(scenario))})
         and type(authority.get('history')) is dict and len(authority['history'])>=40
         and same(authority.get('ordered_predecessors'),{})
         and all(authority.get(k) is False for k in ('unknown_effects_resolved','old_rows_modified',
             'new_trial_for_historical_task','product_or_B00_acceptance'))
         and authority.get('no_old_task_replay') is True and authority.get('new_independent_inputs_only') is True,
         'ICSVCF227_REAL_ROOT_ORDINARY_AUTHORITY_REQUIRED')
    need(same(authority.get('icsvcf_read227_original_case'),ORIGINAL_CASE) and authority.get('icsvcf_read227_family')==family_of(scenario) and authority.get('icsvcf_read227_operation')=='read' and same(authority.get('icsvcf_read227_upload_input'),scenario['steps'][0]['input']) and reference_shape(authority.get('icsvcf_read227_effect_eligibility')) and reference_shape(authority.get('icsvcf_read227_installed227_assessment')),'ICSVCF227_EXACT_ROOT_READ227_BINDINGS_REQUIRED')
    return True


def compose_source(base_raw,history_helper_raw,readonly_history_raw,*,scenario,run_id,
                   authority,authority_ref,current_checker_ref,current_proof_ref):
    """Pure future binding; returns Source, never current admission or execution.

    The inserted checker is mandatory before the existing ordinary admission
    returns, after its authority/current/history reads and before new/save/intent.
    Root MUST independently accept that checker for exact ICS/VCF READ227, actual original eligibility and current mutable state.
    A DOCX prior-read checker cannot satisfy that semantic requirement.
    """
    validate_authority_shape(authority,authority_ref,run_id=run_id,scenario=scenario)
    need(reference_shape(current_checker_ref) and current_checker_ref['bytes']<=1024**2
         and reference_shape(current_proof_ref),'ICSVCF227_EXACT_ROOT_CURRENT_GATE_AND_PROOF_REQUIRED')
    need(current_checker_ref['path']!=authority_ref['path']
         and current_proof_ref['path'] not in (authority_ref['path'],current_checker_ref['path']),
         'ICSVCF227_SEPARATE_ROOT_CURRENT_BINDINGS_REQUIRED')
    compatible,assignments,authority_node,count_node,method=_ordinary_source(base_raw,history_helper_raw,readonly_history_raw)
    lines=compatible.decode().splitlines(keepends=True);changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{run_id:digest(encoded(scenario))}),('ORDINARY_INDEPENDENT_AUTHORITY',authority_ref)]:
        n=assignments[name];changes.append((n.lineno,n.end_lineno,'    '+name+' = '+repr(value)+'\n'))
    for n,value in [(authority_node,authority['authority_id']),(count_node,len(authority['history']))]:
        changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+repr(value)+lines[n.lineno-1][n.end_col_offset:]))
    gate=("        if name == "+repr(run_id)+":\n"
          "            _icsvcf227_ref = "+repr(current_checker_ref)+"\n"
          "            _icsvcf227_raw = safe_read(Path(_icsvcf227_ref['path']))\n"
          "            if len(_icsvcf227_raw) != _icsvcf227_ref['bytes'] or digest(_icsvcf227_raw) != _icsvcf227_ref['sha256']:\n"
          "                raise Refused('ICSVCF227 exact Root current checker changed')\n"
          "            import types as _icsvcf227_types\n"
          "            _icsvcf227_current = _icsvcf227_types.ModuleType('_Root_ICSVCF227_first_upload_current')\n"
          "            _icsvcf227_current.__file__ = _icsvcf227_ref['path']\n"
          "            exec(compile(_icsvcf227_raw, _icsvcf227_current.__file__, 'exec'), _icsvcf227_current.__dict__)\n"
          "            _icsvcf227_result = _icsvcf227_current.check("+repr(current_proof_ref)+", run_id=name, scenario=scenario,\n"
          "                                             stage=getattr(self, '_send_phase', 'NEW'))\n"
          "            if _icsvcf227_result is not True:\n"
          "                raise Refused('ICSVCF227 Root current checker must explicitly return True')\n")
    need(isinstance(method.body[-1],ast.Return) and ast.unparse(method.body[-1].value)=='document',
         'ICSVCF227_EXACT_ADMISSION_RETURN_REQUIRED')
    changes.append((method.body[-1].lineno,method.body[-1].lineno-1,gate))
    need(len({lo for lo,_,_ in changes})==5,'ICSVCF227_OVERLAPPING_SOURCE_SEAMS_REFUSED')
    for lo,hi,replacement in sorted(changes,reverse=True):lines[lo-1:hi]=[replacement]
    result=''.join(lines).encode();ast.parse(result);return result


def qualify_selected_ordinary_readonly(runner,*,run_id,scenario):
    """Existing full pre-save prefix, without new/save/API/clock creation.

    ROOT ONLY on actual state. Isolated tests may use the real methods against
    their explicitly isolated reader. The real Root gate remains mandatory.
    """
    validate_scenario_data(scenario)
    need(runner.api is None,'ICSVCF227_READONLY_API_MUST_BE_NONE')
    qualified=runner._f07_qualify_new_prefix_readonly(run_id,scenario)
    admission=runner.ordinary_independent_admission(run_id,scenario)
    need(admission is not None,'ICSVCF227_EXACT_ORDINARY_ADMISSION_REQUIRED')
    runner.ordinary_independent_current_rows(admission,run_id)
    need(qualified['scenario_sha256']==digest(encoded(scenario)),
         'ICSVCF227_READONLY_SCENARIO_CHANGED')
    return dict(state='ICSVCF227_WHOLE_PRE_SAVE_READONLY_QUALIFIED_NOT_ADMISSION',
        original_new_prefix=qualified,original_case=clone(ORIGINAL_CASE),scenario_sha256=digest(encoded(scenario)),
        upload_planned=True,upload_executed=False,future_ingress_native_read_reply_required_now=False,
        new_called=False,save_called=False,API_called=False,send_called=False,
        once_claim_created=False,operation_clock_created=False)


if __name__=='__main__':
    raise SystemExit('REFUSED: Source binding only; no actor, authority, current or execution')
