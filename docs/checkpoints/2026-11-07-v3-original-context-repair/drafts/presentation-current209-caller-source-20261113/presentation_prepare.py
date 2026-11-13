"""Exact first original F04 PPTX→ODP SOURCE composition; import is inert.

No issuer, runtime discovery, natural-language credential parsing or executor.
Historical compatibility is the unchanged pinned shared helper, not a waiver.
Every effectful use requires Root's separately protected current bindings.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types

SELECTED_TESTER='/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py'
SELECTED_SHA='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
SHARED={'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113/source/f07_phase_prepare.py','bytes':92510,'sha256':'6eb474ec654cb789be3a70ce783fa3abb40a4c6528a1b06b3afe376d721f6cb6'}
CANDIDATE={'path':'/home/jericho/.cache/FRW-SOL-V3-PRESENTATION-ORDINARY-PREP-CORE-20261113/CANDIDATE.private.json','bytes':3039,'sha256':'c3bf7a7bd2745d1a7d2f05602d76217b16007e99d26bf93cb0604f0d229c1429'}
SOURCE_SHA='64556440f31c88320569f795020e486f56b9792ceb5fb4908a66797ef0fd780a'
SCENARIO_SHA='00262cd02882795a8d8a96ecece6308e955e4d9b7a7944b901ff1dfa7efa560b'
SOURCE_REF={'run_id':'root-b00-s151-v03-20261102-r1','run_sha256':'7834bf3e2af0b7c5ea1f25b87d48e4a0c9e4c222536c4eec095adb466d963f2a','input_sha256':SOURCE_SHA}
ALIAS='received/telegram_02f21001825f051033cd2b18639b87f231acfa84e28cc0edc5717eed82c35137_presentation_core.pptx'
PRINCIPAL='telegram-bot-8812646969'
SID='20261030_093055_43bba39f'
KEY='agent:telegram-bot-8812646969:telegram:dm:8812646969'
ODP='application/vnd.oasis.opendocument.presentation'
TIMING=dict(operation_seconds=300,reply_window_seconds=180,ack_seconds=10,reserve_seconds=5,outer_seconds=600)
PHASE_FIELDS={'schema','state','phase','ordinal','scenario','scenario_sha256','timing','retained_unit','runtime_basis','expected_semantics'}
UNIT_FIELDS={'schema','source_reference','original_alias','original','principal','conversation','current_source','Root_binding'}
ORIGINAL_FIELDS={'run','source_upload_ack','source_native_ingress','source_platform_message_id','original_sent_id','admission','window','custody','closed_operation'}
ORIGINAL_REFS={'run','source_upload_ack','admission','window','custody','closed_operation'}


def need(ok,code):
    if not ok:raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw):return hashlib.sha256(raw).hexdigest()


def clone(value):return json.loads(encoded(value))


def same(a,b):return encoded(a)==encoded(b)


def sha(value):return type(value) is str and re.fullmatch('[a-f0-9]{64}',value) is not None


def canonical_path(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and str(Path(value))==value and all(p not in ('','.','..') for p in value.split('/')[1:])
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value),'PRESENTATION_CANONICAL_PATH_REQUIRED')
    value.encode('utf-8');return Path(value)


def reference_shape(value):
    return type(value) is dict and set(value)=={'path','bytes','sha256'} and canonical_path(value['path']).is_absolute() and type(value['bytes']) is int and 0<value['bytes']<=24*1024**2 and sha(value['sha256'])


def load_pinned(reference,reader):
    need(reference_shape(reference),'PRESENTATION_PINNED_SOURCE_REQUIRED')
    raw=reader(reference)
    need(type(raw) is bytes and len(raw)==reference['bytes'] and digest(raw)==reference['sha256'],'PRESENTATION_SOURCE_CHANGED')
    m=types.ModuleType('_presentation_shared_exact_source');m.__file__=reference['path']
    exec(compile(raw,m.__file__,'exec'),m.__dict__);return m


def validate_retained_unit(unit,reader=None):
    """Pure shape, or exact saved metadata authentication when reader is explicit.

    Root supplies a metadata-only projection of original upload authority. The
    projection must pin complete canonical/ACK/admission/window/custody bytes.
    This does not issue that projection or infer ingress authority from SHA.
    Actual canonical joins are checked by validate_original_runner below.
    """
    need(type(unit) is dict and set(unit)==UNIT_FIELDS and unit['schema']=='frw.PRESENTATION.retained-original-upload.v1'
         and unit['source_reference']==SOURCE_REF and unit['original_alias']==ALIAS
         and unit['principal']==PRINCIPAL,'PRESENTATION_EXACT_V03_RETAINED_UNIT_REQUIRED')
    conversation=unit['conversation']
    need(type(conversation) is dict and set(conversation)=={'session_id','session_key'}
         and conversation['session_id']==SID and conversation['session_key']==KEY,
         'PRESENTATION_SAME_ORIGINAL_CONVERSATION_REQUIRED')
    original=unit['original']
    need(type(original) is dict and set(original)==ORIGINAL_FIELDS
         and all(reference_shape(original[k]) for k in ORIGINAL_REFS)
         and original['run']['sha256']==SOURCE_REF['run_sha256']
         and original['run']['path']=='/home/jericho/.local/share/friday-telegram-bot-test/runs/'+SOURCE_REF['run_id']+'.json'
         and type(original['source_native_ingress']) is int and original['source_native_ingress']==3289
         and original['source_platform_message_id']=='4211'
         and type(original['original_sent_id']) is int and original['original_sent_id']==2138,
         'PRESENTATION_ORIGINAL_UPLOAD_RECEIPT_UNIT_REQUIRED')
    source=unit['current_source']
    need(type(source) is dict and set(source)=={'path','bytes','sha256','stat'} and source['bytes']==48100
         and type(source['bytes']) is int and source['sha256']==SOURCE_SHA
         and canonical_path(source['path']).as_posix().endswith('/'+ALIAS),
         'PRESENTATION_ORIGINAL_ALIAS_AND_SOURCE_CAS_REQUIRED')
    s=source['stat']
    need(type(s) is dict and set(s)=={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
         and all(type(v) is int and v>=0 for v in s.values()) and s['inode']>0
         and s['size_bytes']==48100 and s['uid']==1000 and reference_shape(unit['Root_binding']),
         'PRESENTATION_FRESH_SOURCE_IDENTITY_REQUIRED')
    if reader is not None:
        raw=reader(unit['Root_binding']);need(len(raw)==unit['Root_binding']['bytes'] and digest(raw)==unit['Root_binding']['sha256'],
             'PRESENTATION_ROOT_UPLOAD_METADATA_CHANGED')
        data=json.loads(raw)
        need(same(data,dict(schema='frw.Root.PRESENTATION.original-upload-metadata.v1',operator='Root',
             status='ROOT_BOUND_ORIGINAL_UPLOAD',source_reference=SOURCE_REF,original_alias=ALIAS,
             original=original,principal=unit['principal'],conversation=conversation,
             current_source=source,source_unchanged=True,original_upload_authority_verified=True,
             original_operation_closed=True,original_effect_not_replayed=True)),
             'PRESENTATION_ROOT_ORIGINAL_UPLOAD_METADATA_REQUIRED')
        for key in ORIGINAL_REFS:
            raw=reader(original[key]);need(type(raw) is bytes and len(raw)==original[key]['bytes']
                and digest(raw)==original[key]['sha256'],'PRESENTATION_ORIGINAL_RECEIPT_CHANGED')
    return unit


def validate_preparation(phase):
    need(type(phase) is dict and set(phase)==PHASE_FIELDS
         and phase['schema']=='frw.PRESENTATION.original-forward-preparation.v1'
         and phase['state']=='SOURCE_ONLY_UNBOUND_NOT_GRANTED' and phase['phase']=='PPTX_TO_ODP'
         and type(phase['ordinal']) is int and phase['ordinal']==1 and same(phase['timing'],TIMING)
         and phase['expected_semantics']=='original_F04_forward_native_editable_ODP'
         and phase['scenario_sha256']==digest(encoded(phase['scenario']))
         and phase['scenario_sha256']==SCENARIO_SHA
         and reference_shape(phase['runtime_basis']),'PRESENTATION_EXACT_FIRST_FORWARD_PREPARATION_REQUIRED')
    validate_retained_unit(phase['retained_unit'])
    scenario=phase['scenario']
    need(type(scenario) is dict and set(scenario)=={'tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds','steps'}
         and {k:scenario[k] for k in ('tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds')}==
             dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=300,max_updates=65,pace_seconds=1)
         and all(type(scenario[k]) is int for k in ('tester_id','peer_id','deadline_seconds','max_updates','pace_seconds'))
         and type(scenario['steps']) is list and len(scenario['steps'])==1,'PRESENTATION_SINGLE_TEXT_ONLY_SCENARIO_REQUIRED')
    step=scenario['steps'][0]
    need(type(step) is dict and set(step)=={'request','observe'} and type(step['request']) is str
         and 1<=len(step['request'])<=2000
         and same(step['observe'],dict(mode='bounded_reply_capture',window_seconds=180,max_messages=64,
             max_text_chars=8000,max_documents=1,document_max_bytes=8388608)),
         'PRESENTATION_FULL180_ONE_ODP_CAPTURE_REQUIRED')
    return True


def preparation(candidate_raw,*,retained_unit,runtime_basis):
    """Exact accepted Task37 producer→concrete retained-input consumer shape."""
    need(type(candidate_raw) is bytes and len(candidate_raw)==CANDIDATE['bytes'] and digest(candidate_raw)==CANDIDATE['sha256'],
         'PRESENTATION_EXACT_TASK37_CANDIDATE_REQUIRED')
    candidate=json.loads(candidate_raw)
    phase=dict(schema='frw.PRESENTATION.original-forward-preparation.v1',state='SOURCE_ONLY_UNBOUND_NOT_GRANTED',
        phase='PPTX_TO_ODP',ordinal=1,scenario=clone(candidate['scenario']),
        scenario_sha256=digest(encoded(candidate['scenario'])),timing=clone(TIMING),
        retained_unit=clone(retained_unit),runtime_basis=clone(runtime_basis),
        expected_semantics='original_F04_forward_native_editable_ODP')
    validate_preparation(phase);return phase


def authority_shape(authority,reference,*,run_id,phase):
    validate_preparation(phase)
    need(reference_shape(reference) and reference['bytes']==len(encoded(authority)) and reference['sha256']==digest(encoded(authority)),
         'PRESENTATION_EXACT_ROOT_AUTHORITY_REFERENCE_REQUIRED')
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id) and run_id!='UNBOUND'
         and run_id!=SOURCE_REF['run_id'],'PRESENTATION_NEW_FORWARD_RUN_REQUIRED')
    need(type(authority) is dict and authority.get('schema')=='frw.Root.ordinary-independent-history-admission.v1'
         and authority.get('operator')=='Root' and authority.get('accepted') is True
         and type(authority.get('authority_id')) is str and bool(authority['authority_id']) and 'UNBOUND' not in authority['authority_id']
         and authority.get('run_scenarios')=={run_id:phase['scenario_sha256']}
         and type(authority.get('history')) is dict and bool(authority['history'])
         and authority.get('ordered_predecessors',{})=={}
         and all(authority.get(k) is False for k in ('unknown_effects_resolved','old_rows_modified','new_trial_for_historical_task','product_or_B00_acceptance'))
         and authority.get('no_old_task_replay') is True and authority.get('new_independent_inputs_only') is True,
         'PRESENTATION_ROOT_ORIGINAL_FORWARD_AUTHORITY_REQUIRED')
    expected=dict(case_id='F-04',case_index=165,direction='PPTX_TO_ODP',genuinely_missing_original_forward=True,
        no_converter_or_App_replay=True,source_reference=SOURCE_REF,original_alias=ALIAS,
        principal=PRINCIPAL,conversation=phase['retained_unit']['conversation'])
    need(same(authority.get('presentation_original_case'),expected),'PRESENTATION_EXPLICIT_ROOT_FORWARD_DECISION_REQUIRED')
    task=authority.get('presentation_task')
    need(type(task) is dict and set(task)=={'kind','nonce','request','source_reference','output'}
         and task['kind']=='ordinary-document-task' and task['request']==phase['scenario']['steps'][0]['request']
         and task['source_reference']==SOURCE_REF and task['output']==dict(filename=None,mime_type=ODP)
         and type(task['nonce']) is str and re.fullmatch('[a-f0-9]{32}',task['nonce'])
         and 'UNBOUND' not in task['nonce'],'PRESENTATION_ROOT_BOUND_SINGLE_ORDINARY_TASK_REQUIRED')
    return True


def validate_original_runner(runner,unit):
    """FUTURE ROOT only. Full existing source custody/window verification.

    Canonical/receipt bytes are authenticated; never emitted. Original sender ACK
    is validated by the original consumer (including its real historical bound),
    not by equating tester ACK2138 with native platform4211.
    """
    def reader(r):
        raw=runner._presentation_reference_bytes(r)
        need(type(raw) is bytes and len(raw)==r['bytes'] and digest(raw)==r['sha256'],'PRESENTATION_ORIGINAL_REFERENCE_CHANGED')
        return raw
    validate_retained_unit(unit,reader=reader)
    source=json.loads(reader(unit['original']['run']))
    need(source.get('id')==SOURCE_REF['run_id'] and source.get('send_state')=='sent'
         and source.get('send_attempts')==1 and type(source.get('send_attempts')) is int
         and type(source.get('sent_message_id')) is int and source.get('sent_message_id')==2138
         and source.get('capture_window_complete') is True
         and source.get('status') in ('EVIDENCE_READY','STOPPED'),
         'PRESENTATION_ORIGINAL_CLOSED_SINGLE_UPLOAD_REQUIRED')
    runner.verify_capture_context(source)
    runner.verify_window(source)
    runner.verify_reply_custody(source)
    _,_,drain=runner.receive_inventory(source,terminal=True)
    need(type(drain) is dict and set(drain)=={'intent','response','complete'}
         and all(type(v) is dict for v in drain.values())
         and drain['complete'].get('kind')=='terminal_complete',
         'PRESENTATION_ORIGINAL_AUTHENTICATED_TERMINAL_DRAIN_REQUIRED')
    for original_key,run_key in [('source_upload_ack','sent_api_ack_reference'),('window','sent_window_reference')]:
        r=source.get(run_key)
        need(type(r) is dict and type(r.get('basename')) is str and Path(r['basename']).name==r['basename']
             and same(unit['original'][original_key],dict(path=str(runner.store.root/r['basename']),bytes=r.get('bytes'),sha256=r.get('sha256'))),
             'PRESENTATION_ORIGINAL_ACK_WINDOW_REFERENCE_JOIN_REQUIRED')
    ackref=source['sent_api_ack_reference'];ack=json.loads(reader(unit['original']['source_upload_ack']))
    if ackref.get('representation')=='botapi-wire-envelope-json':ack=ack.get('result')
    need(type(ack) is dict and type(ack.get('message_id')) is int and ack['message_id']==2138
         and type(ack.get('from',{}).get('id')) is int and ack['from']['id']==8812646969
         and ack.get('from',{}).get('is_bot') is True
         and type(ack.get('chat',{}).get('id')) is int and ack['chat']['id']==8751854128
         and type(ack.get('document')) is dict and ack['document'].get('file_name')=='presentation_core.pptx'
         and type(ack['document'].get('file_size')) is int and ack['document']['file_size']==48100,
         'PRESENTATION_TRUE_ORIGINAL_SOURCE_DOCUMENT_ACK_REQUIRED')
    if 'continuation_reference' in source:
        need(source['continuation_reference']['sha256']==unit['original']['admission']['sha256'],
             'PRESENTATION_ORIGINAL_ADMISSION_PIN_REQUIRED')
    # Source input belongs to this actual original task, never another same-SHA alias.
    step=source.get('scenario',{}).get('steps',[{}])[0]
    upload=step.get('input')
    need(type(upload) is dict and upload.get('kind')=='document' and upload.get('sha256')==SOURCE_SHA
         and upload.get('filename')=='presentation_core.pptx' and upload.get('stat',{}).get('size_bytes')==48100,
         'PRESENTATION_CANONICAL_ORIGINAL_UPLOAD_INPUT_REQUIRED')
    return dict(state='ORIGINAL_UPLOAD_UNIT_AUTHENTICATED_NOT_NEW_EFFECT_GRANT',source_reference=clone(SOURCE_REF))


def compose_source(base_raw,phase,*,run_id,authority_ref,authority,retained_unit=None,shared_module=None):
    """Concrete original tester composition; no ACK override, no runtime effect.

    The genuine entire new prefix, send/intent/UNKNOWN/cursor/capture/stop paths
    are preserved. Runtime proof is inserted separately by current209 adapter.
    shared_module is allowed only for pure controlled source tests; its helper
    source is verified by its __source_raw__ pin, never arbitrary substitutions.
    """
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'PRESENTATION_SELECTED_TESTER_CHANGED')
    validate_preparation(phase);authority_shape(authority,authority_ref,run_id=run_id,phase=phase)
    need(retained_unit is None or retained_unit==phase['retained_unit'],'PRESENTATION_SOURCE_UNIT_CHANGED')
    if shared_module is None:
        # Explicit SOURCE read only. Pure callers may supply authenticated module.
        path=Path(SHARED['path'])
        need(not any(p.is_symlink() for p in (path,*path.parents)),'PRESENTATION_SHARED_HELPER_LINK')
        with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
            before=os.fstat(stream.fileno());raw=stream.read(SHARED['bytes']+1);after=os.fstat(stream.fileno())
        identity=lambda s:tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
             and stat.S_IMODE(before.st_mode)==0o600 and identity(before)==identity(after)==identity(path.stat()),
             'PRESENTATION_SHARED_HELPER_CUSTODY_CHANGED')
        need(len(raw)==SHARED['bytes'] and digest(raw)==SHARED['sha256'],'PRESENTATION_SHARED_HISTORY_HELPER_CHANGED')
        shared_module=types.ModuleType('_presentation_exact_history_helper');shared_module.__file__=SHARED['path']
        exec(compile(raw,shared_module.__file__,'exec'),shared_module.__dict__)
    else:
        raw=getattr(shared_module,'__source_raw__',None)
        need(type(raw) is bytes and len(raw)==SHARED['bytes'] and digest(raw)==SHARED['sha256'],'PRESENTATION_UNAUTHENTICATED_SHARED_HELPER')
    compatible=shared_module.apply_history_compat(base_raw)
    text=compatible.decode();tree=ast.parse(text);lines=text.splitlines(keepends=True)
    runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner');changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{run_id:phase['scenario_sha256']}),('ORDINARY_INDEPENDENT_AUTHORITY',authority_ref)]:
        ns=[n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
        need(len(ns)==1,'PRESENTATION_EXACT_ASSIGNMENT_SEAM_REQUIRED');n=ns[0]
        changes.append((n.lineno,n.end_lineno,'    '+name+' = '+repr(value)+'\n'))
    method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission')
    ids=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261108-r44']
    need(len(ids)==1,'PRESENTATION_EXACT_AUTHORITY_SEAM_REQUIRED');n=ids[0]
    changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+repr(authority['authority_id'])+lines[n.lineno-1][n.end_col_offset:]))
    compares=[n for n in ast.walk(method) if isinstance(n,ast.Compare) and ast.unparse(n)=="len(document['history']) != 40"]
    need(len(compares)==1,'PRESENTATION_EXACT_HISTORY_CARDINALITY_SEAM_REQUIRED');n=compares[0].comparators[0]
    changes.append((n.lineno,n.end_lineno,lines[n.lineno-1][:n.col_offset]+str(len(authority['history']))+lines[n.lineno-1][n.end_col_offset:]))
    need(len({lo for lo,_,_ in changes})==len(changes),'PRESENTATION_OVERLAPPING_SOURCE_SEAMS')
    for lo,hi,replacement in sorted(changes,reverse=True):lines[lo-1:hi]=[replacement]
    result=''.join(lines).encode();ast.parse(result);return result


def qualify_selected_ordinary_readonly(runner,*,run_id,phase):
    """FUTURE ROOT ONLY; no row/save/API/claim/clock, entire original prefix."""
    validate_preparation(phase)
    need(runner.api is None,'PRESENTATION_READONLY_API_MUST_BE_NONE')
    retained=validate_original_runner(runner,phase['retained_unit'])
    result=runner._f07_qualify_new_prefix_readonly(run_id,phase['scenario'])
    admission=runner.ordinary_independent_admission(run_id,phase['scenario'])
    need(admission is not None,'PRESENTATION_EXACT_ORDINARY_ADMISSION_REQUIRED')
    runner.ordinary_independent_current_rows(admission,run_id)
    need(result['scenario_sha256']==phase['scenario_sha256'],'PRESENTATION_READONLY_SCENARIO_CHANGED')
    return dict(state='WHOLE_PRESENTATION_PRE_SAVE_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION',
        original_new_prefix=result,retained=retained,new_called=False,save_called=False,API_called=False,
        send_called=False,once_claim_created=False,operation_clock_created=False)
