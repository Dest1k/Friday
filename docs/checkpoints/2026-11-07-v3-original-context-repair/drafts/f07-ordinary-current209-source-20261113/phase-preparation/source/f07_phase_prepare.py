"""Finite CASE168 F07 source preparation; importing this module is inert.

The explicit preflight reads pinned SOURCE/metadata only. No H/current/socket/API,
model, sender, Store, capability or ContextVar is created. No function issues
Root authority. compose_source returns a local candidate in memory, retaining the
entire selected consumer and its capture/current/once/custody/stop behavior.
"""
from __future__ import annotations
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SELECTED_TESTER = '/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py'
SELECTED_SHA = 'cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b'
COMPLETE_SHA = '67d1aff2f27c8fbbb20303b0e2bcc1645ec4aa031cee2b26922726fd2acc6499'
TRUNCATED_SHA = '03bc974e86c81845b6d4d47bdb90eec7b21f66d750aa3319bc327149859a5a75'
DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
SOURCE_BASE = '/home/jericho/.cache/FRW-SOL-V3-F07-CURRENT-INGRESS-MISMATCH-CORE-20261112/fixtures'
ORIGINAL_PLAN = {'path':'/home/jericho/.jericho/runtime/astra-new-20261030-R1/postboot-20261102T1645MSK/B00-source151-F07-no-extension-1/PLAN.json','bytes':3907,'sha256':'3c99d7c311a2e906801bdba46fe93bad2cce3cd15c63d085c4e762bd9e1947a4'}
MANIFEST = {'path':'/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-F07-QUALIFICATION-PREP-20261113/INPUT-MANIFEST.json','bytes':8045,'sha256':'95d2f6813f20f5fb381224a3ec9466bb5d0b3b5bec43c4cd21031b499547f1b6'}
CLOSURE = {'path':'/home/jericho/.cache/FRW-ASTRA-V3-CORE209-ROOT-20261113/ACTUAL209-INSTALLED-CLOSED.json','bytes':None,'sha256':'202c51d2d9b0a7214016dcd5e085bd8425506d0316999805c14c82909f295f1c'}
PHASES = (
 ('NO_EXTENSION','source_without_extension','text/plain',1233,COMPLETE_SHA),
 ('FALSE_EXTENSION','false_extension.pdf','application/pdf',1233,COMPLETE_SHA),
 ('TRUNCATED_CONTAINER','truncated.docx',DOCX,64,TRUNCATED_SHA),
 ('HEALTHY_AFTER_FAILURE','healthy.docx',DOCX,1233,COMPLETE_SHA),
)
REQUESTS = (
 'Проверь настоящий формат этого файла без расширения и кратко опиши его предмет. Если прочитать его нельзя, объясни конкретное ограничение; оригинал не меняй.',
 'Прочитай этот файл. Проверь фактический формат по содержимому и сообщи, если расширение PDF или заявленный тип ему не соответствуют. Кратко перескажи текст и укажи ограничения чтения. Не изменяй исходный файл и не создавай новые файлы.',
 'Прочитай этот файл. Если структура повреждена или прочитана только часть, прямо скажи об этом и укажи, что удалось проверить. Не исправляй исходный файл молча, не изменяй его и не создавай новые файлы.',
 'Теперь прочитай этот исправный файл в этой же беседе. Кратко перескажи текст и укажи ограничения чтения. Не изменяй исходный файл и не создавай новые файлы.',
)
OBSERVE = {'mode':'bounded_reply_capture','window_seconds':180,'max_messages':32,'max_text_chars':8000,'max_documents':0,'document_max_bytes':8388608}
TIMING = {'operation_seconds':300,'reply_window_seconds':180,'ack_seconds':30,'reserve_seconds':5,'outer_seconds':600}
PREDECESSOR_FIELDS = {'run_id','scenario_sha256','run_record_sha256','review','review_schema','initially_absent'}
STAT_FIELDS = ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
MAX_REF = 24*1024*1024


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clone(value):
    return json.loads(encoded(value))


def unique(pairs):
    out = {}
    for key,value in pairs:
        need(key not in out,'F07_DUPLICATE_JSON_KEY')
        out[key] = value
    return out


def sha(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}',value) is not None


def canonical_path(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value)
         and str(Path(value))==value and all(p not in ('','.','..') for p in value.split('/')[1:]),
         'F07_CANONICAL_ABSOLUTE_PATH_REQUIRED')
    value.encode('utf-8')
    return Path(value)


def reference_shape(value):
    return (type(value) is dict and set(value)=={'path','bytes','sha256'}
            and canonical_path(value['path']).is_absolute() and type(value['bytes']) is int
            and 0<value['bytes']<=MAX_REF and sha(value['sha256']))


def read_source(path, *, limit=1024*1024, private=True):
    """Explicit readonly pinned-source helper; no import/current consumer access."""
    p = canonical_path(path)
    need(type(limit) is int and 0<limit<=MAX_REF,'F07_READ_BOUND_REQUIRED')
    need(not any(q.is_symlink() for q in (p,*p.parents)),'F07_NO_LINKS_REQUIRED')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid()
             and before.st_nlink==1 and not stat.S_IMODE(before.st_mode)&0o002
             and (not private or stat.S_IMODE(before.st_mode)==0o600), 'F07_SOURCE_CUSTODY_REFUSED')
        raw = stream.read(limit+1)
        after = os.fstat(stream.fileno())
    named = p.stat()
    ident = lambda s: tuple(getattr(s,k) for k in STAT_FIELDS)
    need(len(raw)<=limit and len(raw)==before.st_size and ident(before)==ident(after)==ident(named),
         'F07_SOURCE_CHANGED_OR_OVERSIZE')
    return raw,dict(zip(STAT_FIELDS,ident(before)))


def read_reference(reference, *, private=True):
    need(reference_shape(reference),'F07_EXACT_REFERENCE_REQUIRED')
    raw,_ = read_source(reference['path'],limit=reference['bytes'],private=private)
    need(len(raw)==reference['bytes'] and digest(raw)==reference['sha256'],'F07_REFERENCE_CHANGED')
    return raw


def document(reference):
    return json.loads(read_reference(reference),object_pairs_hook=unique)


def source_input(case, source_stat):
    """Pure pinned SOURCE shape; not a workspace/native/platform identity."""
    ordinal = next((i for i,p in enumerate(PHASES) if p[1]==Path(case.get('source_path','')).name),None)
    need(ordinal is not None,'F07_EXACT_PROSPECTIVE_SOURCE_REQUIRED')
    phase,filename,mime,size,want = PHASES[ordinal]
    need(case.get('sha256')==want and case.get('bytes')==size
         and source_stat.get('st_size')==size and source_stat.get('st_uid')==os.getuid(),
         'F07_PROSPECTIVE_PIN_MISMATCH')
    return {'kind':'document','path':str(canonical_path(case['source_path'])),'sha256':want,
            'stat':{out:source_stat[key] for out,key in (
                ('device','st_dev'),('inode','st_ino'),('size_bytes','st_size'),
                ('uid','st_uid'),('mtime_ns','st_mtime_ns'),('ctime_ns','st_ctime_ns'))},
            'filename':filename,'mime_type':mime,'caption':REQUESTS[ordinal]}


def construct_scenario(ordinal, upload):
    """Exact selected seven-key/single-document ordinary shape; grants nothing."""
    need(type(ordinal) is int and 1<=ordinal<=4,'F07_PHASE_ORDINAL_REQUIRED')
    _,name,mime,size,want = PHASES[ordinal-1]
    need(type(upload) is dict and set(upload)=={'kind','path','sha256','stat','filename','mime_type','caption'}
         and upload['kind']=='document' and upload['path']==str(Path(SOURCE_BASE)/name) and upload['filename']==name
         and upload['mime_type']==mime and upload['sha256']==want
         and type(upload['stat']) is dict
         and set(upload['stat'])=={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
         and all(type(v) is int and v>=0 for v in upload['stat'].values())
         and upload['stat']['inode']>0 and upload['stat']['uid']==os.getuid()
         and upload['stat'].get('size_bytes')==size and upload['caption']==REQUESTS[ordinal-1],
         'F07_EXACT_ORDERED_INPUT_REQUIRED')
    return {'tester_id':8812646969,'peer_id':8751854128,'peer_username':'@jerichodevbot',
            'deadline_seconds':300,'max_updates':64,'pace_seconds':1,
            'steps':[{'input':clone(upload),'observe':clone(OBSERVE)}]}


def phase_preparation(ordinal,upload):
    scenario = construct_scenario(ordinal,upload)
    return {'schema':'frw.F07.original-ordered-phase-preparation.v1',
            'state':'SOURCE_ONLY_UNBOUND_NOT_GRANTED','ordinal':ordinal,'phase':PHASES[ordinal-1][0],
            'original_CASE168_semantic_contract':True,'original_missing_artifacts_recreated':False,
            'scenario_request_provenance':('SAVED_ORIGINAL_PHASE1_CAPTION_WITH_EXPLICIT_NEW_PROSPECTIVE_INPUT' if ordinal==1 else 'NEW_PROSPECTIVE_REQUEST_ORIGINAL_SEALED_SCENARIO_NOT_RECREATED'),
            'prospective_fixture_only':True,'scenario':scenario,'scenario_sha256':digest(encoded(scenario)),
            'same_chat_session_no_reset':True,'requires_actual_closed_predecessor':ordinal>1,
            'previous_ordinal':ordinal-1 if ordinal>1 else None,'timing':clone(TIMING),
            'expected_semantics':('truthful_safe_malformed_rejection' if ordinal==3 else
                'healthy_followup_same_chat' if ordinal==4 else 'truthful_supported_DOCX_mismatch_limited_coverage'),
            'ordinary_output_contract':'text_only_zero_documents',
            'preop_missing_future_output_required':False,'runtime_acceptance':'NOT_RUN',
            'Root_phase_eligibility':None,'Root_run_id':None,'Root_current_source_permission_effect_proofs':None,
            'Root_authority':None,'actual_ACK':None,'native_ingress_source_reference':None,
            'actual_closed_predecessor':None}


def predecessor_binding(run, review_ref, *, review_schema, run_raw):
    """Consume Root-reviewed ACTUAL source facts; no acceptance/closure is invented.

    The ordinary-independent bounded capture already retains a truthful product
    refusal as RECEIVED_UNGRADED and can observe full180. A STOPPED/PARTIAL caused
    by transport/capture/timeout/unknown is not converted here or replayed.
    """
    need(type(run) is dict and encoded(run)==run_raw and sha(run.get('scenario_sha256'))
         and run.get('status')=='EVIDENCE_READY' and run.get('send_state')=='sent'
         and type(run.get('send_attempts')) is int and run['send_attempts']==1
         and run.get('capture_window_complete') is True,'F07_ACTUAL_COMPLETE_CAPTURE_REQUIRED')
    need(reference_shape(review_ref) and type(review_schema) is str and bool(review_schema),
         'F07_ROOT_ACTUAL_REVIEW_REFERENCE_REQUIRED')
    return {'run_id':run['id'],'scenario_sha256':run['scenario_sha256'],
            'run_record_sha256':digest(run_raw),
            'review':{'path':review_ref['path'],'sha256':review_ref['sha256']},
            'review_schema':review_schema,'initially_absent':False}


def compose_source(base_raw, phase, *, run_id, authority_ref, authority, previous_phase=None):
    """Existing F06 ordinary pin composition, adapted to exact cc36 seams ONLY.

    Root supplies a separately ISSUED original-case authority and genuine current
    proof at the future boundary. Returning bytes is source preparation, never
    issuance, read-only current qualification, or permission to execute them.
    No predecessor/capture/refusal/freshness/current/once logic is replaced.
    ACK30 is bound at the existing send_ack_budget method for this exact run and
    scenario only; historical and unrelated ordinary runs retain their original10.
    """
    need(type(base_raw) is bytes and digest(base_raw)==SELECTED_SHA,'F07_SELECTED_TESTER_CHANGED')
    need(type(phase) is dict and phase.get('state')=='SOURCE_ONLY_UNBOUND_NOT_GRANTED'
         and phase.get('scenario_sha256')==digest(encoded(phase.get('scenario'))), 'F07_PHASE_SOURCE_REQUIRED')
    ordinal = phase['ordinal']
    need(phase==phase_preparation(ordinal,phase['scenario']['steps'][0]['input']),
         'F07_EXACT_CURRENT_PHASE_METADATA_REQUIRED')
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',run_id)
         and run_id!='UNBOUND','F07_ROOT_SELECTED_NEW_RUN_REQUIRED')
    need(reference_shape(authority_ref) and authority_ref['bytes']==len(encoded(authority))
         and authority_ref['sha256']==digest(encoded(authority)), 'F07_EXACT_FUTURE_AUTHORITY_REFERENCE_REQUIRED')
    need(type(authority) is dict and authority.get('schema')=='frw.Root.ordinary-independent-history-admission.v1'
         and authority.get('operator')=='Root' and authority.get('accepted') is True
         and type(authority.get('authority_id')) is str and authority['authority_id']
         and authority.get('run_scenarios')=={run_id:phase['scenario_sha256']}
         and type(authority.get('history')) is dict and bool(authority['history'])
         and authority.get('unknown_effects_resolved') is False
         and authority.get('old_rows_modified') is False
         and authority.get('new_trial_for_historical_task') is False
         and authority.get('product_or_B00_acceptance') is False,
         'F07_ROOT_ORIGINAL_CASE_AUTHORITY_REQUIRED')
    need(authority.get('f07_original_case')=={
        'case_id':'F-07','case_index':168,'phase':PHASES[ordinal-1][0],'ordinal':ordinal,
        'controlled_fault_sequence_not_replay':True,'prospective_fixture_not_original':True},
        'F07_EXPLICIT_ROOT_ORIGINAL_CASE_DECISION_REQUIRED')
    predecessors = authority.get('ordered_predecessors',{})
    need(type(predecessors) is dict and set(predecessors)==({run_id} if ordinal>1 else set()),
         'F07_EXACT_IMMEDIATE_PREDECESSOR_REQUIRED')
    if ordinal>1:
        need(type(previous_phase) is dict and previous_phase.get('ordinal')==ordinal-1
             and previous_phase.get('phase')==PHASES[ordinal-2][0]
             and previous_phase.get('scenario_sha256')==digest(encoded(previous_phase.get('scenario'))),
             'F07_EXACT_PREVIOUS_PHASE_SCENARIO_REQUIRED')
        need(previous_phase==phase_preparation(ordinal-1,previous_phase['scenario']['steps'][0]['input']),
             'F07_EXACT_PREVIOUS_PHASE_METADATA_REQUIRED')
        pred=predecessors[run_id]
        need(type(pred) is dict and set(pred)==PREDECESSOR_FIELDS
             and pred['run_id']!=run_id and pred['scenario_sha256']==previous_phase['scenario_sha256']
             and sha(pred['run_record_sha256']) and pred['initially_absent'] is False
             and type(pred['review']) is dict and set(pred['review'])=={'path','sha256'}
             and sha(pred['review']['sha256']), 'F07_ACTUAL_REVIEWED_PREDECESSOR_REQUIRED')
    text=base_raw.decode('utf-8');tree=ast.parse(text);lines=text.splitlines(keepends=True)
    runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner')
    changes=[]
    for name,value in [('ORDINARY_INDEPENDENT_SCENARIOS',{run_id:phase['scenario_sha256']}),
                       ('ORDINARY_INDEPENDENT_AUTHORITY',authority_ref)]:
        nodes=[n for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
        need(len(nodes)==1,'F07_EXACT_ASSIGNMENT_SEAM_REQUIRED')
        node=nodes[0];changes.append((node.lineno,node.end_lineno,'    '+name+' = '+repr(value)+'\n'))
    method=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='ordinary_independent_admission')
    # Use positions, not a global string replace that could alter unrelated history.
    ids=[n for n in ast.walk(method) if isinstance(n,ast.Constant) and n.value=='ordinary-independent-jarvis-activate-20261108-r44']
    need(len(ids)==1,'F07_EXACT_AUTHORITY_SEAM_REQUIRED')
    node=ids[0];changes.append((node.lineno,node.end_lineno,lines[node.lineno-1][:node.col_offset]+repr(authority['authority_id'])+lines[node.lineno-1][node.end_col_offset:]))
    compares=[n for n in ast.walk(method) if isinstance(n,ast.Compare)
              and ast.unparse(n)=='len(document[\'history\']) != 40']
    need(len(compares)==1,'F07_EXACT_HISTORY_COUNT_SEAM_REQUIRED')
    node=compares[0].comparators[0]
    changes.append((node.lineno,node.end_lineno,lines[node.lineno-1][:node.col_offset]+str(len(authority['history']))+lines[node.lineno-1][node.end_col_offset:]))
    ack=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='send_ack_budget')
    returns=[n for n in ast.walk(ack) if isinstance(n,ast.Return)
             and isinstance(n.value,ast.Name) and n.value.id=='REPLY_ACK_RESERVE']
    need(len(returns)==1,'F07_EXACT_ORDINARY_ACK_SEAM_REQUIRED')
    node=returns[0]
    replacement=('    ' * 3 + "return (30 if run.get('id') == "+repr(run_id)
        +" and run.get('scenario_sha256') == "+repr(phase['scenario_sha256'])
        +" and 'continuation_reference' not in run else REPLY_ACK_RESERVE)\n")
    changes.append((node.lineno,node.end_lineno,replacement))
    # Two same-line token changes are not expected in the exact saved selected source.
    need(len({lo for lo,_,_ in changes})==len(changes),'F07_OVERLAPPING_SOURCE_SEAMS')
    for lo,hi,new in sorted(changes,reverse=True):lines[lo-1:hi]=[new]
    result=''.join(lines).encode();ast.parse(result)
    return result


def qualify_legacy_current(runner, exact_root_plan, *, consumer_fd=None, credential_fd=None):
    """FUTURE ROOT CALL ONLY: exact B226 check_current=True, never send.

    No native/source/capability or plan is fabricated here. Root must create and
    admit a separate read-only operation over genuine existing protected history
    and selected current runner. Exception/refusal propagates unchanged.
    This legacy continuation check does not qualify ordinary-independent instead.
    """
    need(type(exact_root_plan) is dict,'F07_GENUINE_LEGACY_PLAN_UNBOUND')
    return runner.continuation_material(exact_root_plan,check_current=True,
                                       consumer_fd=consumer_fd,credential_fd=credential_fd)


def preflight():
    """Explicit SOURCE ONLY reads of exact saved shapes and justclosed209 proof."""
    manifest=document(MANIFEST)
    original=document(ORIGINAL_PLAN)
    original_scenario=original['new_scenario']
    need(original_scenario['max_updates']==64
         and original_scenario['steps'][0]['observe']==OBSERVE
         and original_scenario['steps'][0]['input']['caption']==REQUESTS[0]
         and original['ack_timeout_seconds']==TIMING['ack_seconds'],
         'F07_ORIGINAL_PRESERVED_BOUNDS_OR_CAPTION_DRIFT')
    closure_raw,_=read_source(CLOSURE['path'])
    need(digest(closure_raw)==CLOSURE['sha256'],'F07_ACTUAL209_CLOSURE_CHANGED')
    closure=json.loads(closure_raw,object_pairs_hook=unique)
    need(closure.get('schema')=='friday.Root.actual209-installed-closed.v1'
         and closure.get('installed')=={'layers':209,'project':499,'native':17891,'plugins':52,'base':17730}
         and closure.get('F07_runtime_semantic_formal_accepted') is False,
         'F07_ACTUAL209_HISTORICAL_PROOF_MISMATCH')
    base_raw,_=read_source(SELECTED_TESTER,limit=2*1024*1024,private=False)
    need(digest(base_raw)==SELECTED_SHA,'F07_SELECTED_TESTER_CHANGED')
    preparations=[]; source_refs=[]
    for ordinal,case in enumerate(manifest['cases'][:4],1):
        raw,source_stat=read_source(case['source_path'],limit=case['bytes'])
        need(digest(raw)==case['sha256'],'F07_PROSPECTIVE_BYTES_CHANGED')
        upload=source_input(case,source_stat)
        preparations.append(phase_preparation(ordinal,upload))
        source_refs.append({'path':case['source_path'],'bytes':len(raw),'sha256':digest(raw),'identity':source_stat})
    return {'schema':'frw.F07.connected-source-preflight.v1','state':'SOURCE_PREFLIGHT_ONLY_NOT_CURRENT_NOT_ADMITTED',
            'phases':preparations,'source_inputs':source_refs,
            'actual209_closure_reused':dict(CLOSURE,bytes=len(closure_raw)),
            'selected_tester':{'path':SELECTED_TESTER,'bytes':len(base_raw),'sha256':SELECTED_SHA},
            'genuine_normal_context_tool':'NOT_RUN_BOOTSTRAP_UNBOUND',
            'B226_actual_check_current_true':'NOT_RUN_GENUINE_ROOT_RUNNER_PLAN_UNBOUND',
            'ordinary_current_authority':'NOT_RUN_ROOT_BINDINGS_UNBOUND',
            'future_output_preop_requirement':False,'new_execution_credit':0}


if __name__=='__main__':
    raise SystemExit('SOURCE ONLY: import inert helpers; Root must explicitly bind any future operation')
