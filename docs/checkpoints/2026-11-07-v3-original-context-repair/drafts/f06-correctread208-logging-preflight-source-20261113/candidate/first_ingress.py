"""Pure, closed-first-upload dependency validation. No I/O except injected read.

All real references are UNBOUND in the source packet. Root supplies actual saved
ACK/ingress/custody/reconciliation after the first operation closes. This module
does not accept a preparation, absent-send inference, or source-only verdict.
Returned object contains metadata/references only, never the private scenario.
"""
import hashlib
import json
import math
import re
from pathlib import Path

BASE_SHA='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
SOURCE_SHA='22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5'
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
PEER=8751854128
TESTER=8812646969
MIME='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
FIELDS={'schema','operator','status','source_reference','source','B','source_identity',
        'canonical_run','first_binding','ack','task','window','closure',
        'root_reconciliation','private_custody','native_ingress'}

# Exact already completed first effect. These are immutable lineage expectations;
# none grants a new operation, freshness, clock, admission or credential.
EXPECTED_SOURCE_REFERENCE={'run_id': 'f06-first-docx-wrong-read-20261112-r1', 'run_sha256': '49b5d5fbc1bed36ef054dd478b8dfe8167baa0fe5cef4ced49bc4020f1b1b74e', 'input_sha256': '22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5'}
EXPECTED_ACTUAL_SOURCE={'path': 'received/telegram_4011b532062a0c382734e94e57e6e8560e0ee0c652a466db7d4ceec3adedc656_f06-new-encrypted.docx', 'platform_message_id': '4862', 'presentation_scope': {'binding_sha256': 'cbf7f45a811951c5198620e98817f36c525211a961237123989a477133c8b5f1', 'principal': 'b21d67fc1b4ccce97241421bf86e3bc7416064133f7afd0822e6734ac6d5eef5', 'profile': 'telegram-bot-8812646969'}, 'profile': 'telegram-bot-8812646969', 'session_id': '20261030_093055_43bba39f', 'sha256': '22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5', 'size_bytes': 23040, 'user_row_id': 5511}
ROOT_ACCEPTANCE={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-API-AFTER-Y-ROOT-20261112/ROOT-SCOPED-FIRST-WRONGREAD-ACCEPTANCE.json', 'bytes': 3154, 'sha256': 'ab76a402723bed5077bb05da0c1a769b6851c18b545c9e2cd1da35860130bb9f'}
INDEPENDENT_ACTUAL_REVIEW={'bytes': 16736, 'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F06-ACTUAL-FIRST-WRONGREAD-ASSESSMENT-20261112/REVIEW.json', 'sha256': '16d395d2e337b56998794ff9d564136c8b54e96b5983c780fa87fe464d3f8e95'}
EXPECTED_B={'profile':'telegram-bot-8812646969','session_id':'20261030_093055_43bba39f','session_key':'agent:telegram-bot-8812646969:telegram:dm:8812646969'}
RECEIVED_BASE=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/profiles/telegram-bot-8812646969/workspace')
RECEIVED_SOURCE={'path':str(RECEIVED_BASE/EXPECTED_ACTUAL_SOURCE['path']),'bytes':23040,'sha256':SOURCE_SHA}


def validate_native_join(c,first,ingress,ack,document,read):
    """Bind different bot ID planes through retained actual accepted evidence.

    Tester ACK2756 and native platform4862 are intentionally different IDs. A
    future Root judgement must join each with the original canonical receipt,
    native5511 presentation and exact received path. No body or secret is returned.
    """
    need(first['source_reference']==c['source_reference']==EXPECTED_SOURCE_REFERENCE
          and first['B']==EXPECTED_B, 'F06_FIRST_FIXED_SAME_UPLOAD_REFERENCE_REQUIRED')
    need(ingress.get('root_scoped_acceptance')==ROOT_ACCEPTANCE
          and ingress.get('saved_actual_review')==INDEPENDENT_ACTUAL_REVIEW,
          'F06_FIRST_ACTUAL_ACCEPTANCE_AND_REVIEW_REQUIRED')
    accepted=doc(ROOT_ACCEPTANCE,read);review=doc(INDEPENDENT_ACTUAL_REVIEW,read)
    need(accepted.get('schema')=='friday.Root.F06.actual-first-wrongread-scoped-acceptance.v1'
          and accepted.get('operator')=='Root' and accepted.get('actual_source_basis')==EXPECTED_ACTUAL_SOURCE
          and accepted.get('canonical_run')==first['canonical_run']
          and accepted.get('independent_review')==INDEPENDENT_ACTUAL_REVIEW
          and review.get('next_action_basis_only',{}).get('actual_source_reference')==EXPECTED_ACTUAL_SOURCE
          and review.get('effect_and_custody',{}).get('canonical_run')==first['canonical_run'],
          'F06_FIRST_RETAINED_ACTUAL_JOIN_CHANGED')
    need(ack.get('message_id')==2756 and ingress.get('tester_sent_message_id')==ack['message_id']
          and ingress.get('platform_message_id')=='4862'
          and ingress.get('native_user_row_id')==5511
          and ingress.get('native_message_ids')==[5511,5512,5513,5514]
          and ingress.get('actual_source_reference')==EXPECTED_ACTUAL_SOURCE
          and ingress.get('received_source')==RECEIVED_SOURCE
          and ingress.get('cross_bot_id_planes_separately_preserved') is True
          and ingress.get('file_id')==document['file_id']
          and ingress.get('file_unique_id')==document['file_unique_id']
          and ingress.get('source_reference_observed') is True,
          'F06_FIRST_EXACT_NATIVE_RECEIVED_SOURCE_JOIN_REQUIRED')
    identity=ingress.get('received_identity')
    need(type(identity) is dict and set(identity)=={'device','inode','uid','gid','mode','nlink','bytes','mtime_ns','ctime_ns'}
          and all(type(v) is int and v>=0 for v in identity.values())
          and identity['bytes']==23040 and identity['nlink']==1
          and identity['uid']==1000 and not identity['mode']&0o002,
          'F06_FIRST_ROOT_RECEIVED_IDENTITY_UNBOUND')
    return {'source_reference':EXPECTED_ACTUAL_SOURCE,'ciphertext':RECEIVED_SOURCE,'identity':identity}

def need(v,code):
    if not v:raise ValueError(code)
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(v):return hashlib.sha256(v).hexdigest()
def sha(v):return type(v) is str and re.fullmatch('[a-f0-9]{64}',v) is not None
def unique(pairs):
    d={}
    for k,v in pairs:
        need(k not in d,'F06_FIRST_DUPLICATE_JSON_KEY');d[k]=v
    return d
def path(v):
    need(type(v) is str and v.startswith('/') and not v.startswith('//')
         and not any(ord(c)<32 or 127<=ord(c)<=159 for c in v)
         and not any(p in ('','.','..') for p in v.split('/')[1:])
         and str(Path(v))==v,'F06_FIRST_LEXICAL_PATH_REFUSED')
    try:v.encode('utf8')
    except UnicodeError:raise ValueError('F06_FIRST_UTF8_PATH_REQUIRED') from None
    return Path(v)
def reference(r):
    return (type(r) is dict and set(r)=={'path','bytes','sha256'}
            and path(r['path']).is_absolute() and type(r['bytes']) is int
            and 0<r['bytes']<=24*1024**2 and sha(r['sha256']))
def readref(r,read):
    need(reference(r),'F06_FIRST_EXACT_REF_REQUIRED')
    missing=object();bounded=getattr(read,'f06_read_reference',missing)
    need(bounded is missing or callable(bounded),'F06_FIRST_BOUNDED_REFERENCE_CALLBACK_REQUIRED')
    raw=read(path(r['path'])) if bounded is missing else bounded(r)
    need(type(raw) is bytes and len(raw)==r['bytes'] and digest(raw)==r['sha256'],
         'F06_FIRST_REF_CHANGED')
    return raw
def doc(r,read):return json.loads(readref(r,read),object_pairs_hook=unique)
def source_reference(v):
    return (type(v) is dict and set(v)=={'run_id','run_sha256','input_sha256'}
            and type(v['run_id']) is str
            and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v['run_id']) is not None
            and v['run_id']!='UNBOUND' and sha(v['run_sha256'])
            and v['input_sha256']==SOURCE_SHA)
def stored_ref(r,recorded):
    return (reference(r) and type(recorded) is dict
            and set(recorded) in ({'basename','bytes','sha256'},
                                  {'basename','bytes','sha256','representation'})
            and type(recorded['basename']) is str
            and '/' not in recorded['basename'] and recorded['basename'] not in ('','.','..')
            and path(r['path'])==STATE/recorded['basename']
            and r['bytes']==recorded['bytes'] and r['sha256']==recorded['sha256'])
def judgement(r,read,schema,first):
    d=doc(r,read)
    need(type(d) is dict and d.get('schema')==schema and d.get('operator')=='Root'
         and d.get('status')=='ROOT_BOUND' and d.get('source_reference')==first['source_reference']
         and d.get('B')==first['B'] and d.get('source')==first['source'],
         'F06_FIRST_ROOT_JUDGEMENT_UNBOUND')
    return d
def validate(c,read):
    first=doc(c['first_ingress'],read)
    need(type(first) is dict and set(first)==FIELDS
         and first['schema']=='frw.Root.F06.closed-first-upload.v1'
         and first['operator']=='Root' and first['status']=='ROOT_BOUND_CLOSED_RECONCILED',
         'F06_FIRST_ACTUAL_CLOSED_INGRESS_REQUIRED')
    sr=first['source_reference']
    need(source_reference(sr) and sr==c['source_reference'] and sr['run_id']!=c['run_id']
         and first['source']==c['source'] and first['source']['sha256']==SOURCE_SHA,
         'F06_FIRST_EXACT_SOURCE_REFERENCE_REQUIRED')
    b=first['B'];want={k:c['boundary']['B'][k] for k in ('profile','session_id','session_key')}
    need(type(b) is dict and set(b)==set(want) and b==want
         and b['profile']=='telegram-bot-8812646969', 'F06_FIRST_SAME_B_REQUIRED')
    r=first['canonical_run']
    need(reference(r) and path(r['path'])==STATE/'runs'/(sr['run_id']+'.json')
         and r['sha256']==sr['run_sha256'],'F06_FIRST_CANONICAL_SOURCE_REQUIRED')
    raw=readref(r,read);run=json.loads(raw,object_pairs_hook=unique)
    need(raw==encoded(run) and run.get('id')==sr['run_id']
         and run.get('status') in ('EVIDENCE_READY','STOPPED','FAILED')
         and run.get('send_state')=='sent' and type(run.get('send_attempts')) is int
         and run['send_attempts']==1 and 'continuation_reference' not in run
         and type(run.get('step')) is int and run['step']==0
         and type(run.get('sent_message_id')) is int and run['sent_message_id']>0
         and run.get('sent_ids')==[run['sent_message_id']]
         and all(type(run.get(k)) in (int,float) and math.isfinite(run[k])
                 for k in ('sent_at','send_intent_at','send_dispatch_at','deadline'))
         and run['send_intent_at']<=run['send_dispatch_at']<=run['sent_at']
         and run['send_dispatch_at']<=run['sent_at']<=run['send_dispatch_at']+10
         and type(run.get('send_timeout_seconds')) is int and run['send_timeout_seconds']==10
         and 'new_ack_timeout_seconds' not in run
         and run['send_dispatch_at']+10+180+5<=run['deadline'],
         'F06_FIRST_UNCLOSED_OR_UNKNOWN_SEND_REFUSED')
    scenario=run.get('scenario',{});steps=scenario.get('steps',[])
    need(scenario.get('tester_id')==TESTER and scenario.get('peer_id')==PEER
         and scenario.get('peer_username')=='@jerichodevbot'
         and set(scenario)=={'tester_id','peer_id','peer_username','deadline_seconds','max_updates','pace_seconds','steps'}
         and all(type(scenario.get(k)) is int and scenario[k]==v for k,v in
                 {'tester_id':TESTER,'peer_id':PEER,'deadline_seconds':300,'max_updates':65,'pace_seconds':1}.items())
         and type(steps) is list and len(steps)==1 and set(steps[0])=={'input','observe'}
         and run.get('scenario_sha256')==digest(encoded(scenario)),
         'F06_FIRST_EXACT_UPLOADED_SCENARIO_REQUIRED')
    need(steps[0]['observe']=={'mode':'bounded_reply_capture','window_seconds':180,
          'max_messages':64,'max_text_chars':8000,'max_documents':0,'document_max_bytes':8*1024**2}
          and all(type(steps[0]['observe'][k]) is int for k in steps[0]['observe'] if k!='mode'),
          'F06_FIRST_ORIGINAL_CAPTURE_BOUNDS_REQUIRED')
    upload=steps[0]['input']
    need(type(upload) is dict and upload.get('kind')=='document'
         and upload.get('sha256')==SOURCE_SHA and upload.get('filename')=='f06-new-encrypted.docx'
         and upload.get('mime_type')==MIME and upload.get('path')==first['source']['path']
         and upload.get('stat')==first['source_identity']
         and set(upload)=={'kind','path','sha256','stat','filename','mime_type','caption'}
         and type(upload.get('caption')) is str and bool(upload['caption'])
         and type(upload.get('stat')) is dict
         and set(upload['stat'])=={'device','inode','size_bytes','uid','mtime_ns','ctime_ns'}
         and all(type(v) is int and v>=0 for v in upload['stat'].values())
         and upload['stat']['size_bytes']==23040,
         'F06_FIRST_DOCUMENT_IDENTITY_REQUIRED')
    binding=doc(first['first_binding'],read);old=binding.get('contract',{})
    need(binding.get('schema')=='frw.Root.F06.exact-first-wrongread-binding.v1'
          and reference(binding.get('source')) and sha(binding.get('whole_effect_sha256'))
          and old.get('schema')=='frw.F06.original-docx-ordinary-first-wrongread.v2'
         and old.get('phase')=='DOCX-WRONG-READ-INGRESS'
         and old.get('status')=='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD'
         and old.get('run_id')==sr['run_id'] and old.get('scenario_sha256')==run['scenario_sha256']
         and old.get('source')==first['source'] and reference(old.get('authority')),
         'F06_FIRST_ACTUAL_WRONGREAD_BINDING_REQUIRED')
    need({k:old.get('boundary',{}).get('B',{}).get(k) for k in b}==b,
         'F06_FIRST_ORIGINAL_B_BINDING_CHANGED')
    # Original exact ACK/task/window hashes are read, never reconstructed from IDs.
    for k,recorded in [('ack','sent_api_ack_reference'),('task','sent_task_reference'),
                       ('window','sent_window_reference')]:
        name='send-'+k+'-'+run['id']+'-0-1.json'
        need(stored_ref(first[k],run.get(recorded))
             and run[recorded]['basename']==name, 'F06_FIRST_ARTIFACT_CUSTODY_REQUIRED')
    ack=doc(first['ack'],read);ar=run['sent_api_ack_reference']
    if ar.get('representation')=='botapi-wire-envelope-json':
        need(ack.get('ok') is True,'F06_FIRST_ACK_OK_REQUIRED');ack=ack.get('result')
    else:need(ar.get('representation')=='decoded-message-json','F06_FIRST_ACK_REPRESENTATION_REQUIRED')
    need(type(ack) is dict and type(ack.get('message_id')) is int
         and ack['message_id']==run.get('sent_message_id') and ack['message_id']>0
         and ack.get('date')==run.get('sent_date') and type(ack.get('date')) is int
         and type(ack.get('chat',{}).get('id')) is int and ack['chat']['id']==PEER and ack['chat'].get('type')=='private'
         and type(ack.get('from',{}).get('id')) is int and ack['from']['id']==TESTER and ack['from'].get('is_bot') is True
         and ack.get('message_thread_id') is None and ack.get('caption')==upload.get('caption'),
         'F06_FIRST_REAL_ACK_CONTEXT_REQUIRED')
    d=ack.get('document',{})
    need(type(d) is dict and type(d.get('file_id')) is str and bool(d['file_id'])
         and type(d.get('file_unique_id')) is str and bool(d['file_unique_id'])
         and d.get('file_size')==23040 and d.get('file_name')=='f06-new-encrypted.docx'
         and d.get('mime_type')==MIME,'F06_FIRST_DOCUMENT_ACK_REQUIRED')
    task=doc(first['task'],read)
    need(set(task)=={'method','chat_id','input_sha256','input_bytes','input_stat','filename',
          'mime_type','caption','content_type','body_sha256','body_bytes','scenario_sha256'}
          and task==run.get('request_metadata') and task.get('method')=='sendDocument'
         and task.get('chat_id')=='@jerichodevbot' and task.get('input_sha256')==SOURCE_SHA
         and task.get('input_bytes')==23040 and task.get('input_stat')==upload['stat']
         and task.get('filename')==upload['filename'] and task.get('mime_type')==upload['mime_type']
         and type(task.get('body_bytes')) is int and 23040<=task['body_bytes']<=23040+8192
         and sha(task.get('body_sha256')) and type(task.get('content_type')) is str
         and re.fullmatch(r'multipart/form-data; boundary=frw-[a-f0-9]{64}',task['content_type']) is not None
         and task.get('caption')==upload.get('caption')
         and task.get('scenario_sha256')==run['scenario_sha256'],
         'F06_FIRST_UPLOAD_TASK_BINDING_REQUIRED')
    w=doc(first['window'],read)
    need(w.get('run_id')==run['id'] and w.get('scenario_sha256')==run['scenario_sha256']
         and type(w.get('step')) is int and w['step']==run['step']
         and type(w.get('send_attempts')) is int and w['send_attempts']==run['send_attempts']
         and w.get('send_intent_at')==run['send_intent_at']
         and w.get('send_dispatch_at')==run['send_dispatch_at']
         and w.get('send_timeout_seconds')==10 and type(w.get('send_timeout_seconds')) is int
         and w.get('deadline')==run['deadline'] and w.get('continuation') is None
         and w.get('sent_at')==run['sent_at']
         and w.get('sent_message_id')==ack['message_id'] and w.get('ack')==ar
         and w.get('task')==run['sent_task_reference'] and w.get('window_seconds')==180
         and w.get('capture_until')==run.get('capture_until')
         and type(w.get('sent_at')) in (int,float)
         and w.get('capture_until')==w['sent_at']+180,
         'F06_FIRST_ORIGINAL_WINDOW_REQUIRED')
    close=judgement(first['closure'],read,'frw.Root.F06.first-operation-closed.v1',first)
    need(close.get('actor_tree_closed') is True and close.get('slot_released') is True
         and close.get('no_pending_first_ingress') is True
         and close.get('original_clock_preserved') is True
         and close.get('raw_outcome_preserved') is True,
         'F06_FIRST_CLOSURE_NOT_ESTABLISHED')
    original_custody(close,first,run,binding,read)
    rec=judgement(first['root_reconciliation'],read,'frw.Root.F06.first-effect-reconciliation.v1',first)
    need(c['root_proofs']['first_upload_reconciliation']==first['root_reconciliation'],
         'F06_FIRST_ROOT_PROOF_REF_MISMATCH')
    need(rec.get('canonical_run')==r and rec.get('first_binding')==first['first_binding']
         and rec.get('ack')==first['ack'] and rec.get('task')==first['task']
         and rec.get('window')==first['window'] and rec.get('closure')==first['closure']
         and rec.get('effect_disposition')=='SENT_CONFIRMED_SAME_SOURCE_INGRESSED'
         and rec.get('unknown_assumed_absent') is False
         and rec.get('no_reupload') is True and rec.get('raw_failures_and_UNKNOWN_preserved') is True
         and rec.get('next_operation')=='ONE_SEPARATE_CORRECT_READ_NO_UPLOAD',
         'F06_FIRST_EFFECT_NOT_RECONCILED')
    cust=judgement(first['private_custody'],read,'frw.Root.F06.first-upload-private-custody.v1',first)
    need(cust.get('ack')==first['ack'] and cust.get('original_identity')==first['source_identity']
         and cust.get('retained_source_sha256')==SOURCE_SHA
         and cust.get('downloaded_source_sha256')==SOURCE_SHA
         and cust.get('original_and_retained_CAS_verified') is True,
         'F06_FIRST_PRIVATE_SOURCE_CUSTODY_REQUIRED')
    ingress=judgement(first['native_ingress'],read,'frw.Root.F06.same-B-source-ingress.v1',first)
    validate_native_join(c,first,ingress,ack,d,read)
    # This validates Root-bound evidence/joins, not new eligibility or credentials.
    # Root alone makes the actual semantic/privacy and next-operation decisions.
    return first

def original_custody(close,first,run,binding,read):
    """Root verifies the original consumer's custody; do not execute old admission.

    The original runtime records may be complete or genuinely partial. Their raw
    status and missing fields remain explicit and cannot become full180 or PASS.
    Root assesses the listed original read-only custody methods on the saved run.
    Existing heads require their original custody verification. A missing-head
    failure stays explicitly failed, never replayed/sent/processed or graded.
    """
    d=judgement(close.get('original_consumer_custody'),read,
                'frw.Root.F06.first-original-consumer-custody.v1',first)
    need(all(d.get(k)==first[k] for k in ('canonical_run','first_binding','ack','task','window'))
          and d.get('bound_source')==binding['source']
          and d.get('base_consumer_sha256')==BASE_SHA
          and d.get('assessed_methods')==['verify_capture_context','verify_window','verify_reply_custody','receive_inventory']
          and d.get('first_status')==run['status']
          and d.get('capture_window_complete_present')==('capture_window_complete' in run)
          and type(d.get('capture_window_complete_present')) is bool
          and d.get('capture_window_complete')==run.get('capture_window_complete')
          and (type(run.get('capture_window_complete')) is bool or run.get('capture_window_complete') is None)
          and (run['status']!='EVIDENCE_READY' or run.get('capture_window_complete') is True)
          and d.get('original_clock_and_window_preserved') is True
          and d.get('all_existing_raw_and_receipts_verified') is True
          and d.get('known_partial_not_upgraded') is True
          and d.get('late_arrivals_raw_only') is True
          and d.get('first_semantic_PASS_required') is False
          and d.get('acceptance')=='NOT_ESTABLISHED',
          'F06_FIRST_ORIGINAL_CONSUMER_CUSTODY_REQUIRED')
    readref(binding['source'],read)
    head=run.get('receive_head');sequence=run.get('receive_sequence')
    need(d.get('receive_head')==head and d.get('receive_sequence')==sequence,
          'F06_FIRST_RAW_RECEIVE_STATE_CHANGED')
    if head is None:
        need(sequence is None and run['status'] in ('STOPPED','FAILED')
              and run.get('capture_window_complete') is not True
              and run.get('seen')==run.get('message_ids')==run.get('observations')==[]
              and d.get('receive_custody')=='MISSING_ORIGINAL_RECEIVE_HEAD_FAILURE_PRESERVED'
              and d.get('method_assessment')=='ORIGINAL_MISSING_HEAD_FAILURE_PRESERVED'
              and type(d.get('missing_receive_failure_code')) is str
              and re.fullmatch('[A-Z0-9_]{1,96}',d['missing_receive_failure_code']) is not None,
              'F06_FIRST_MISSING_ORIGINAL_RECEIVE_CUSTODY_REFUSED')
    else:
        need(type(sequence) is int and 0<=sequence<=3*(65+1)
              and d.get('receive_custody')=='VERIFIED_EXISTING_FULL_OR_PARTIAL'
              and d.get('method_assessment')=='VERIFIED_ORIGINAL_EXISTING_CUSTODY'
              and stored_ref(d.get('terminal_receive'),head)
              and head['basename']=='receive-'+run['id']+'-0-1-'+str(sequence)+'.json',
              'F06_FIRST_ORIGINAL_RECEIVE_HEAD_REQUIRED')
        terminal=doc(d['terminal_receive'],read)
        need(terminal.get('sequence')==sequence and terminal.get('context',{}).get('run_id')==run['id']
              and terminal['context'].get('scenario_sha256')==run['scenario_sha256']
              and terminal['context'].get('window')==run['sent_window_reference']
              and terminal['context'].get('sent_message_id')==run['sent_message_id']
              and terminal['context'].get('deadline')==run['deadline']
              and (run.get('capture_window_complete') is not True or terminal.get('kind')=='terminal_complete'),
              'F06_FIRST_ORIGINAL_TERMINAL_RECEIVE_BINDING_REQUIRED')
    basis=d.get('retained_basis')
    need(type(basis) is list and bool(basis),'F06_FIRST_ORIGINAL_CUSTODY_BASIS_REQUIRED')
    for r in basis:readref(r,read)
    return d

def postcondition_plan(c,d):
    """An obligation for THIS future effect, never an actual privacy verdict."""
    p=d.get('logging_privacy_postcondition_plan')
    need(type(p) is dict and p.get('schema')=='frw.Root.F06.same-upload-correctread-postcondition-plan.v1'
         and p.get('status')=='REQUIRED_AFTER_ONE_FUTURE_OPERATION_NOT_ASSESSED'
         and p.get('run_id')==c['run_id'] and p.get('phase')==c['phase']
         and p.get('scenario_sha256')==c['scenario_sha256']
         and p.get('source_reference')==c['source_reference']
         and p.get('installation_closure')==c['installation']['closure']
         and p.get('runtime_hashes')==c['installation']['runtime_hashes']
         and p.get('gateway')==c['boundary']['gateway']
         and p.get('B')=={k:c['boundary']['B'][k] for k in ('profile','session_id','session_key')}
         and type(p.get('technical_log_cursor')) is dict
         and reference(p.get('technical_carrier_baseline'))
         and p.get('actual_full180_reply_capture_required') is True
         and p.get('new_technical_carrier_assessment_required') is True
         and p.get('original_private_request_exemption_only') is True
         and p.get('per_site_execution_and_verdict_separate') is True
         and p.get('missing_site_verdict')=='NOT_OBSERVED'
         and p.get('missing_actual_carriers_acceptance')=='NOT_ESTABLISHED'
         and p.get('no_extra_event_or_replay_for_qualification') is True
         and p.get('raw_statuses_not_upgraded') is True
         and p.get('assessment_schema')=='frw.Root.F06.same-upload-correctread-postcondition-assessment.v1',
         'F06_CORRECTREAD_POSTCONDITION_PLAN_REQUIRED')
    return p


def private_oracle(c,read):
    """Require a genuine Root private criterion judgment, never inspect plaintext.

    A hash/True is not a semantic acceptance by this source validator. Root must
    independently derive these facts from the actual retained plaintext oracle
    and correct synthetic credential, then evaluate the NEW ordinary reply later.
    """
    d=doc(c['root_proofs']['correct_read_private_oracle'],read)
    need(type(d) is dict and d.get('schema')=='frw.Root.F06.correct-read-private-oracle.v1'
         and d.get('operator')=='Root' and d.get('status')=='ROOT_BOUND'
         and d.get('source')==c['source'] and d.get('source_reference')==c['source_reference']
         and d.get('phase')==c['phase'] and d.get('scenario_sha256')==c['scenario_sha256']
         and d.get('correct_secret_verified_for_same_source') is True
         and d.get('actual_retained_first_paragraph_oracle') is True
         and d.get('toy_placeholder_oracle') is False
         and d.get('no_new_document_or_derivative') is True
         and d.get('technical_secret_delta_review_required_after_reply') is True
         and d.get('original_private_request_exemption_only') is True
         and d.get('future_reply_acceptance')=='NOT_ESTABLISHED',
         'F06_CORRECTREAD_PRIVATE_ORACLE_UNBOUND')
    basis=d.get('retained_basis')
    need(type(basis) is list and bool(basis),'F06_CORRECTREAD_ORACLE_BASIS_REQUIRED')
    for r in basis:readref(r,read)
    p=postcondition_plan(c,d)
    readref(p['technical_carrier_baseline'],read)
    return d
