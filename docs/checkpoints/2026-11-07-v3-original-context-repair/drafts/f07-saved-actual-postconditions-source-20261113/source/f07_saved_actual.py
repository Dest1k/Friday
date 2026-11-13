"""Inert saved-F07 observation helpers. Explicit future Root calls only.

No CLI, scheduler, Store/API/new/send/model invocation at import. Functions return
objects; Root alone writes evidence and makes semantic/privacy/custody/host-close
judgments. Unsupported source_ref/tool-context evidence stays NOT_ESTABLISHED.
"""
from __future__ import annotations
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time
import types

DEFAULT_LIMIT = 1024**2
EXACT_LIMIT = 24*1024**2
MAX_NEW_ROWS = 64
MAX_FILES = 5000
MAX_RANGE = 8*1024**2
MAX_RANGE_TOTAL = 32*1024**2
SITES = ('agent/turn_context.py', 'gateway/run_turn.py')
BODY_FIELDS = ('content', 'api_content', 'tool_calls', 'tool_call_id')
ID_FIELDS = ('id', 'session_id', 'role', 'timestamp', 'platform_message_id', 'active', 'compacted')
SESSION_FIELDS = ('id', 'source', 'user_id', 'chat_id', 'chat_type', 'session_key', 'profile_name', 'transport_profile')

class Refused(ValueError): pass
def need(ok, code):
    if not ok: raise Refused(code)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)+'\n').encode()
def clone(value): return parse(encoded(value))
def unique(pairs):
    out={}
    for k,v in pairs:
        need(k not in out, 'SAVED_DUPLICATE_JSON_KEY'); out[k]=v
    return out
def parse(raw): return json.loads(raw, object_pairs_hook=unique)
def sha(v): return type(v) is str and re.fullmatch('[a-f0-9]{64}', v) is not None
def canonical(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and str(Path(value))==value and all(x not in ('','.','..') for x in value.split('/')[1:])
         and all(ord(c)>=32 and not 127<=ord(c)<=159 for c in value), 'SAVED_CANONICAL_PATH_REQUIRED')
    return Path(value)
def identity(s):
    return [getattr(s,k) for k in ('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')]
def safe_path(path, *, directory=False, private=False):
    p=canonical(str(path)); need(not any(q.is_symlink() for q in (p,*p.parents)), 'SAVED_SYMLINK_REFUSED')
    s=p.stat(); need((stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
        and s.st_uid==os.getuid() and (directory or s.st_nlink==1)
        and not stat.S_IMODE(s.st_mode)&0o002
        and (not private or stat.S_IMODE(s.st_mode)==(0o700 if directory else 0o600)), 'SAVED_UNSAFE_PATH')
    return p,s
def reference_shape(ref):
    return type(ref) is dict and set(ref)=={'path','bytes','sha256'} and sha(ref['sha256']) \
        and type(ref['bytes']) is int and 0<ref['bytes']<=EXACT_LIMIT and bool(canonical(ref['path']))
def read_reference(ref, *, private=True):
    need(reference_shape(ref), 'SAVED_EXACT_3REF_REQUIRED')
    p,s=safe_path(ref['path'],private=private)
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        before=os.fstat(f.fileno()); raw=f.read(ref['bytes']+1); after=os.fstat(f.fileno())
    need(identity(s)==identity(before)==identity(after)==identity(p.stat())
        and len(raw)==ref['bytes'] and digest(raw)==ref['sha256'], 'SAVED_REFERENCE_CHANGED')
    return raw
def doc(ref, **kw): return parse(read_reference(ref,**kw))
def ref_of(path, limit=DEFAULT_LIMIT, *, private=True):
    need(type(limit) is int and 0<limit<=EXACT_LIMIT,'SAVED_FIXED_READ_BOUND_REQUIRED')
    p,s=safe_path(str(path),private=private)
    need(0<s.st_size<=limit,'SAVED_FIXED_READ_BOUND_EXCEEDED')
    r=dict(path=str(p),bytes=s.st_size,sha256='0'*64)
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        before=os.fstat(f.fileno()); raw=f.read(limit+1); after=os.fstat(f.fileno())
    need(identity(s)==identity(before)==identity(after)==identity(p.stat()) and len(raw)==s.st_size,'SAVED_REFERENCE_CAS_CHANGED')
    r['sha256']=digest(raw); return r

def strict_saved_run(run, *, effect, canonical_ref, state_root):
    """No missing-run substitution. Exact actual canonical path and raw outcome."""
    need(reference_shape(canonical_ref) and canonical_ref['path']==str(canonical(state_root)/'runs'/(effect['run_id']+'.json')),
         'SAVED_CANONICAL_RUN_PATH_REQUIRED')
    need(type(run) is dict and run.get('id')==effect['run_id']
        and run.get('scenario_sha256')==effect['phase']['scenario_sha256']
        and run.get('scenario')==effect['phase']['scenario'] and type(run.get('step')) is int and run['step']==0
        and digest(encoded(run['scenario']))==run['scenario_sha256'], 'SAVED_RUN_EFFECT_CHANGED')
    need(run.get('send_state')=='sent' and type(run.get('send_attempts')) is int and run['send_attempts']==1
        and type(run.get('sent_message_id')) is int and run['sent_message_id']>0,
        'SAVED_CONFIRMED_SINGLE_SEND_REQUIRED_USE_UNCONFIRMED_CLOSURE_OTHERWISE')
    need(type(run.get('observations')) is list and len(run['observations'])<=32
        and type(run.get('seen')) is list and len(run['seen'])<=64,
        'SAVED_CAPTURE_FINITE_BOUND_EXCEEDED')
    return dict(raw_status=run.get('status'),raw_send_state=run.get('send_state'),
        raw_consumer_acceptance=run.get('acceptance','NOT_ESTABLISHED'),
        raw_reply_semantic_status=run.get('reply_text_acceptance','NOT_ESTABLISHED'),
        capture_window_complete=run.get('capture_window_complete'),
        full180=run.get('capture_window_complete') is True and run.get('capture_until')==run.get('sent_at',-1000)+180,
        status_is_evidence_ready=run.get('status')=='EVIDENCE_READY')

def capture_references(run, *, state_root):
    """Exact current run commitments only; no history/default-read enlargement.
    Custody verifier remains authoritative; this inventories its saved evidence.
    All references returned as sized 3refs, including raw update and receipt chain.
    """
    root=canonical(state_root); result={}; required=(('ACK','sent_api_ack_reference'),('window','sent_window_reference'),('task','sent_task_reference'))
    for label,key in required:
        r=run.get(key); need(type(r) is dict and set(r) in ({'basename','bytes','sha256'},{'basename','bytes','sha256','representation'}), 'SAVED_COMMITMENT_REFERENCE_REQUIRED')
        expected={'ACK':'send-ack-','window':'send-window-','task':'send-task-'}[label]+run['id']+'-'+str(run['step'])+'-'+str(run['send_attempts'])+'.json'
        need(r.get('basename')==expected and type(r.get('bytes')) is int and 0<r['bytes']<=DEFAULT_LIMIT and sha(r.get('sha256')),'SAVED_EXACT_COMMITMENT_NAME_REQUIRED')
        exact=dict(path=str(root/expected),bytes=r['bytes'],sha256=r['sha256']); read_reference(exact); result[label]=exact
    sequence=run.get('receive_sequence'); need(type(sequence) is int and 0<=sequence<=3*(64+1),'SAVED_RECEIPT_SEQUENCE_BOUND')
    key=run['id']+'-'+str(run['step'])+'-'+str(run['send_attempts']); head=run.get('receive_head'); chain=[]
    for index in range(sequence,-1,-1):
        need(type(head) is dict and set(head)=={'basename','bytes','sha256'} and head.get('basename')=='receive-'+key+'-'+str(index)+'.json','SAVED_CAPTURE_CHAIN_HEAD_MISMATCH')
        exact=dict(path=str(root/head['basename']),bytes=head['bytes'],sha256=head['sha256']); value=doc(exact)
        chain.append(exact); head=value.get('previous')
    need(head is None,'SAVED_CAPTURE_CHAIN_UNEXPECTED_PREDECESSOR')
    updates=[]
    for uid in run['seen']:
        need(type(uid) is int and uid>=0,'SAVED_EXACT_RAW_UPDATE_ID_REQUIRED')
        updates.extend([ref_of(root/'updates'/(str(uid)+'.json')),ref_of(root/'updates'/(str(uid)+'.arrival.json'))])
    receipts=[]; artifacts=[]
    for item in run['observations']:
        need(type(item) is dict and item.get('kind') in ('reply_text','document'),'SAVED_OBSERVATION_KIND_UNSUPPORTED')
        p=canonical(item.get('receipt_path')); need(p.parent==root/'downloads','SAVED_RECEIPT_OUTSIDE_DOWNLOADS')
        receipts.append(ref_of(p))
        if item['kind']=='document':
            target=canonical(item.get('path')); need(target.parent==root/'downloads','SAVED_ARTIFACT_OUTSIDE_DOWNLOADS')
            need(type(item.get('bytes')) is int and 0<item['bytes']<=EXACT_LIMIT and sha(item.get('sha256')),'SAVED_EXACT_ARTIFACT_BYTES_REQUIRED')
            exact=dict(path=str(target),bytes=item['bytes'],sha256=item['sha256']); read_reference(exact); artifacts.append(exact)
            overflow=target.with_suffix('.overflow.json')
            if overflow.exists(): artifacts.append(ref_of(overflow))
    terminal=root/('terminal-response-'+key+'.json')
    return dict(schema='frw.Root.F07.exact-saved-capture-inventory.v1',commitments=result,receive_chain=chain,
        raw_updates_and_arrivals=updates,observation_receipts=receipts,artifacts=artifacts,
        terminal_response=ref_of(terminal) if terminal.exists() else None,
        capture_window_complete=run.get('capture_window_complete'),
        full180=run.get('capture_window_complete') is True and run.get('capture_until')==run.get('sent_at',-1000)+180,
        bodies_not_copied=True,semantic_verdict='NOT_ESTABLISHED')

def verify_genuine_saved_custody(checker, *, effect, canonical_ref, candidate_ref, state_root, lock_owners):
    """FUTURE ROOT ONLY, held shared_slot/consumer/credential locks.

    Uses exact actual composed candidate and NORMAL existing Store constructor.
    Pre-existing 0700 directories are checked before constructor's exist_ok mkdir.
    api=None. Never calls new/send/run/observe. Genuine refusal is propagated.
    Candidate source provenance/composition must already have Root review.
    Its genuine global cursor verifier may traverse saved tester owner/history
    JSON chains; this helper does not replace or truncate that genuine behavior.
    Native SQL body collection below is separately restricted to exact NEW ids.
    """
    root=canonical(state_root)
    need(root==checker.STATE and set(lock_owners)=={'shared_slot','consumer','credential'}, 'SAVED_ROOT_AND_LOCK_BINDING_REQUIRED')
    for label,path in dict(shared_slot=checker.SLOT,consumer=root/'consumer.lock',credential=root/'tester-token').items():
        checker.lock_held(path,lock_owners[label])
    dirs=[root,root/'runs',root/'updates',root/'downloads']
    before={str(p):identity(safe_path(str(p),directory=True,private=True)[1]) for p in dirs}
    raw=read_reference(candidate_ref); run_raw=read_reference(canonical_ref); run=parse(run_raw)
    need(run_raw==encoded(run),'SAVED_CANONICAL_ENCODING_CHANGED')
    facts=strict_saved_run(run,effect=effect,canonical_ref=canonical_ref,state_root=state_root)
    # No substitute Store, Runner, method body, custody result or global cursor.
    module=types.ModuleType('_f07_actual_candidate_'+candidate_ref['sha256'][:12]); module.__file__=candidate_ref['path']
    exec(compile(raw,module.__file__,'exec'),module.__dict__)
    runner=module.Runner(module.Store(root),None)
    need(runner.api is None and type(runner.store) is module.Store,'SAVED_GENUINE_EXISTING_STORE_REQUIRED')
    runner.verify_reply_custody(run)
    need(before=={str(p):identity(safe_path(str(p),directory=True,private=True)[1]) for p in dirs}, 'SAVED_STORE_DIRECTORY_CHANGED')
    need(read_reference(candidate_ref)==raw and read_reference(canonical_ref)==run_raw,'SAVED_CUSTODY_SOURCE_OR_RUN_CHANGED')
    for label,path in dict(shared_slot=checker.SLOT,consumer=root/'consumer.lock',credential=root/'tester-token').items():
        checker.lock_held(path,lock_owners[label])
    capture=capture_references(run,state_root=state_root)
    return dict(schema='frw.Root.F07.saved-genuine-custody-observation.v1',canonical_run=clone(canonical_ref),
        candidate_source=clone(candidate_ref),method='Runner.verify_reply_custody',normal_existing_Store=True,
        api=None,new_called=False,send_called=False,raw=facts,capture=capture,custody_method_returned_without_refusal=True,
        semantic_verdict='NOT_ESTABLISHED',privacy_verdict='NOT_ESTABLISHED')

def selected_new_rows(checker, *, baseline, selected_ids):
    """FUTURE ROOT ONLY. Three readonly DBs; bodies ONLY explicitly selected NEW ids.

    No existing body sweep. Newly appearing row metadata is bounded and inventoried
    so selection omissions remain visible. Caller supplies actual ids, never ACK+N.
    """
    need(set(selected_ids)==set(checker.DATABASES)==set(baseline), 'SAVED_ALL3_DB_SELECTION_REQUIRED')
    result={}; deadline=time.monotonic()+15
    for label,path in checker.DATABASES.items():
        p,s=safe_path(str(path)); stable=identity(s)[:6]; floor=baseline[label]['max_message_id']
        ids=selected_ids[label]
        need(type(floor) is int and type(ids) is list and ids==sorted(set(ids)) and len(ids)<=MAX_NEW_ROWS
            and all(type(x) is int and x>floor for x in ids), 'SAVED_ONLY_EXACT_NEW_ROW_IDS_ALLOWED')
        need(stable==baseline[label]['identity'],'SAVED_DB_IDENTITY_CHANGED')
        with contextlib.closing(sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            columns={r[1] for r in db.execute('PRAGMA table_info(messages)')}
            need(set(ID_FIELDS)<=columns,'SAVED_UNSUPPORTED_NATIVE_MESSAGE_SCHEMA')
            metadata=db.execute('SELECT '+','.join(ID_FIELDS)+' FROM messages WHERE id>? ORDER BY id LIMIT ?',
                                (floor,MAX_NEW_ROWS+1)).fetchall()
            need(len(metadata)<=MAX_NEW_ROWS,'SAVED_NEW_ROW_BOUND_EXCEEDED')
            need(set(ids)<={r[0] for r in metadata},'SAVED_SELECTED_NEW_ROW_ABSENT')
            fields=(*ID_FIELDS,*(k for k in BODY_FIELDS if k in columns)); rows=[]
            for rid in ids:
                row=dict(zip(fields,db.execute('SELECT '+','.join(fields)+' FROM messages WHERE id=?',(rid,)).fetchone()))
                need(all(v is None or type(v) in (str,int,float) for v in row.values()),'SAVED_UNSUPPORTED_NATIVE_FIELD_TYPE')
                need(sum(len(v.encode()) for v in row.values() if type(v) is str)<=DEFAULT_LIMIT,'SAVED_NATIVE_ROW_BYTES_EXCEEDED')
                rows.append(row)
            principal=[dict(zip(SESSION_FIELDS,r)) for r in db.execute('SELECT '+','.join(SESSION_FIELDS)+' FROM sessions WHERE id=?',(checker.SID,))] if label=='tester' else []
            db.rollback()
        need(identity(p.stat())[:6]==stable,'SAVED_DB_IDENTITY_CAS_CHANGED')
        if label=='tester': need(principal==[checker.PRINCIPAL],'SAVED_NATIVE_PRINCIPAL_CHANGED')
        result[label]=dict(baseline_max_id=floor,new_metadata=[dict(zip(ID_FIELDS,r)) for r in metadata],
            selected_rows=rows,unselected_new_ids=[r[0] for r in metadata if r[0] not in ids],principal=principal)
    return dict(schema='frw.Root.F07.exact-new-native-rows.private.v1',profiles=result,
        old_message_bodies_read=False,grade='NOT_ESTABLISHED')

def select(value, path):
    """Explicit finite JSON selector, no recursive search, coercion or guessed key."""
    need(type(path) is list and 1<=len(path)<=16 and all(type(k) in (str,int) for k in path),'SAVED_EXACT_FIELD_SELECTOR_REQUIRED')
    for key in path:
        if type(value) is dict:
            need(type(key) is str and key in value,'SAVED_SELECTED_FIELD_ABSENT'); value=value[key]
        elif type(value) is list:
            need(type(key) is int and 0<=key<len(value),'SAVED_SELECTED_INDEX_ABSENT'); value=value[key]
        else: raise Refused('SAVED_SELECTED_FIELD_UNSUPPORTED')
    return value

def ingress_evidence(*, effect, principal, ack, new_rows, ingress_row_id, native_record_ref, selectors):
    """OPTIONAL product-object path, only if that actual product format EXISTS.

    The supported normal path is ingress_evidence_join below. This optional helper
    never requires new product instrumentation or invents an existing source_ref.
    """
    fields={'source_ref','source_path','source_sha256','source_bytes','filename','native_platform_message_id','session_id','session_key'}
    need(type(selectors) is dict and set(selectors)==fields,'SAVED_NATIVE_RECORD_FIELD_MAP_REQUIRED')
    record=doc(native_record_ref); values={k:select(record,p) for k,p in selectors.items()}
    rows=new_rows['profiles']['tester']['selected_rows']; found=[r for r in rows if r['id']==ingress_row_id]
    need(len(found)==1 and found[0]['role']=='user' and found[0]['session_id']==principal['id'],'SAVED_EXACT_NEW_USER_INGRESS_REQUIRED')
    row=found[0]; platform=values['native_platform_message_id']
    need(type(platform) in (int,str) and not isinstance(platform,bool) and re.fullmatch('[1-9][0-9]*',str(platform)) is not None
        and type(row['platform_message_id']) in (int,str) and str(row['platform_message_id'])==str(platform), 'SAVED_NATIVE_PLATFORM_ID_MISMATCH')
    source=effect['phase']['scenario']['steps'][0]['input']
    need(type(values['source_ref']) is str and bool(values['source_ref']) and len(values['source_ref'])<=4096
        and values['source_sha256']==source['sha256'] and type(values['source_bytes']) is int
        and values['source_bytes']==source['stat']['size_bytes'] and values['filename']==source['filename']
        and values['session_id']==principal['id'] and values['session_key']==principal['session_key'], 'SAVED_NATIVE_SOURCE_DOMAIN_MISMATCH')
    source_path=canonical(values['source_path']); actual_source=ref_of(source_path,DEFAULT_LIMIT,private=False)
    need(actual_source['sha256']==values['source_sha256'] and actual_source['bytes']==values['source_bytes'],'SAVED_ACTUAL_NATIVE_SOURCE_BYTES_CHANGED')
    need(type(ack.get('message_id')) is int and ack['message_id']>0,'SAVED_ACK_ID_REQUIRED')
    return dict(schema='frw.Root.F07.actual-source-reference-observation.v1',run_id=effect['run_id'],
        tester_ACK_message_id=ack['message_id'],native_message_row_id=ingress_row_id,native_platform_message_id=platform,
        native_principal=clone(principal),source_sha256=values['source_sha256'],source_bytes=values['source_bytes'],
        filename=values['filename'],source_ref=values['source_ref'],actual_native_source=actual_source,
        native_product_record=clone(native_record_ref),field_selectors=clone(selectors),
        selected_ingress_content_sha256=digest((row.get('content') or '').encode()),
        actual_product_record_producer_review='NOT_ESTABLISHED',ordinary_tool_context='NOT_ESTABLISHED',
        actual_source_ref_custody_checked=False,grade='NOT_ESTABLISHED')

def ingress_evidence_join(*, effect, principal, canonical_ref, run, ack_ref, ack, upload_task_ref,
                          new_rows, ingress_row_id, source_join_ref):
    """Root-normalized correlation of genuine existing evidence planes.

    No single product object/source_ref field is required. Root's saved join must
    name exact actual ACK/upload metadata, NEW native row, attachment-producer
    locator, received-file bytes+stat, and scoped actual native trace. It records
    actual sources; it is never described as product-produced provenance. Root
    still judges that locator/trace came from this turn and ordinary context.
    """
    join=doc(source_join_ref)
    need(join.get('schema')=='frw.Root.F07.actual-native-source-custody-join.v1'
        and join.get('operator')=='Root' and join.get('status')=='ROOT_NORMALIZED_ACTUAL_EVIDENCE_ONLY'
        and join.get('run_id')==effect['run_id'] and join.get('whole_effect_sha256')==digest(encoded(effect))
        and join.get('canonical_run')==canonical_ref and join.get('ACK')==ack_ref
        and join.get('upload_task')==upload_task_ref,'SAVED_ROOT_ACTUAL_MULTISOURCE_JOIN_REQUIRED')
    need(doc(canonical_ref)==run and doc(upload_task_ref)==run.get('request_metadata'),'SAVED_ACTUAL_UPLOAD_TASK_METADATA_CHANGED')
    kept_ack=doc(ack_ref)
    if kept_ack.get('ok') is True and type(kept_ack.get('result')) is dict: kept_ack=kept_ack['result']
    need(kept_ack==ack and ack.get('message_id')==run.get('sent_message_id'),'SAVED_ACTUAL_KEPT_ACK_CHANGED')
    rows=new_rows['profiles']['tester']['selected_rows']; found=[r for r in rows if r['id']==ingress_row_id]
    need(len(found)==1 and found[0]['role']=='user' and found[0]['session_id']==principal['id'],'SAVED_EXACT_NEW_USER_INGRESS_REQUIRED')
    row=found[0]; platform=join.get('native_platform_message_id')
    need(type(platform) in (int,str) and re.fullmatch('[1-9][0-9]*',str(platform)) is not None
        and type(row['platform_message_id']) in (int,str) and str(row['platform_message_id'])==str(platform)
        and join.get('native_message_row_id')==ingress_row_id and type(join['native_message_row_id']) is int
        and join.get('native_principal')==principal, 'SAVED_NATIVE_PLATFORM_ID_MISMATCH')
    native_row_ref=join.get('native_row_evidence'); native_saved=doc(native_row_ref)
    native_user_row=select(native_saved,join.get('native_user_row_selector'))
    projected={k:row.get(k) for k in ID_FIELDS}
    projected.update(content_sha256=digest((row.get('content') or '').encode()),
        api_content_sha256=digest((row.get('api_content') or '').encode()))
    need(native_user_row==projected,'SAVED_ROOT_NEW_ROW_EVIDENCE_MISMATCH')
    source=effect['phase']['scenario']['steps'][0]['input']; received=join.get('received_source')
    need(reference_shape(received) and received['sha256']==source['sha256']
        and received['bytes']==source['stat']['size_bytes'] and join.get('filename')==source['filename'],
        'SAVED_NATIVE_SOURCE_DOMAIN_MISMATCH')
    read_reference(received,private=False); _,s=safe_path(received['path'])
    need(join.get('received_source_identity')==identity(s),'SAVED_RECEIVED_SOURCE_IDENTITY_CHANGED')
    # Locator and tooltrace remain separate actual saved planes. Their semantic
    # correlation is a named Root judgment, never a guessed product field/API.
    planes={k:join.get(k) for k in ('producer_locator_evidence','ordinary_tool_trace_evidence')}
    need(all(reference_shape(r) for r in planes.values()),'SAVED_ACTUAL_LOCATOR_AND_SCOPED_TRACE_REQUIRED')
    for exact in planes.values(): read_reference(exact)
    need(type(ack.get('message_id')) is int and ack['message_id']>0,'SAVED_ACK_ID_REQUIRED')
    return dict(schema='frw.Root.F07.actual-source-reference-observation.v1',run_id=effect['run_id'],
        representation='ROOT_DERIVED_MULTI_SOURCE_CUSTODY_JOIN_NOT_PRODUCT_RECORD',
        tester_ACK_message_id=ack['message_id'],native_message_row_id=ingress_row_id,native_platform_message_id=platform,
        native_principal=clone(principal),source_sha256=received['sha256'],source_bytes=received['bytes'],filename=source['filename'],
        source_ref=None,actual_native_source=clone(received),received_source_identity=identity(s),
        source_join=clone(source_join_ref),native_row_evidence=clone(native_row_ref),
        source_planes=dict(ACK=clone(ack_ref),upload_task=clone(upload_task_ref),**clone(planes)),
        selected_ingress_content_sha256=projected['content_sha256'],
        actual_source_planes_provenance_review='NOT_ESTABLISHED',ordinary_tool_context='NOT_ESTABLISHED',
        actual_source_ref_custody_checked=False,grade='NOT_ESTABLISHED')

def logging_metadata(raw, *, origin, offset, principal):
    """Distinct source format recognizers only. Same producer copied twice = one."""
    out={s:[] for s in SITES}; pos=offset
    turn=re.compile(r'conversation turn: session='+re.escape(principal['id'])+r' model=\S+ provider=\S+ platform=telegram history=[0-9]+ input_type=\S+ content_parts=[0-9]+ msg_chars=[0-9]+(?: origin=\S+)?$')
    gateway=re.compile(r'inbound message: platform=telegram user=\S+ chat='+re.escape(principal['chat_id'])+r' kind=\S+ attachments=[0-9]+ msg_chars=[0-9]+ reply_to_id=\S+ reply_to_chars=[0-9]+$')
    for line in raw.splitlines(keepends=True):
        need(len(line)<=65536,'SAVED_LOG_LINE_BOUND_EXCEEDED')
        text=line.decode('utf-8',errors='replace').rstrip('\r\n')
        for site,pattern in ((SITES[0],turn),(SITES[1],gateway)):
            match=pattern.search(text)
            if match:
                out[site].append(dict(origin=origin,offset=pos,bytes=len(line),line_sha256=digest(line),
                    metadata_format=True,source_site=site,correlation_scope='same-new-range-and-session-or-chat; Root reviews exact turn',
                    raw_msg_preview_field=False))
        pos+=len(line)
    return out

def carrier_ranges(*, baseline, private_markers, principal):
    """FUTURE ROOT ONLY. Inventory ten EXACT baseline roots; read NEW files or
    suffixes beyond baseline size only. No old DB/log bodies. Rotation, deletion,
    equal-size rewrites, truncation and absent prefix proof remain unassessed.
    """
    need(type(baseline.get('roots')) is list and len(baseline['roots'])==10
        and len(set(baseline['roots']))==10 and type(baseline.get('files')) is list
        and len(baseline['files'])<=MAX_FILES,'SAVED_EXACT_TEN_ROOT_BASELINE_REQUIRED')
    roots=[canonical(p) for p in baseline['roots']]
    need(type(private_markers) is list and 1<=len(private_markers)<=64
        and all(type(p) is str and 4<=len(p)<=4096 for p in private_markers),'SAVED_EXPLICIT_PRIVATE_MARKERS_REQUIRED')
    markers={digest(p.encode()):p.encode() for p in private_markers}
    old={r['path']:r for r in baseline['files']}; need(len(old)==len(baseline['files']),'SAVED_DUPLICATE_BASELINE_PATH')
    need(all(any(canonical(p).is_relative_to(r) for r in roots) for p in old),'SAVED_BASELINE_OUTSIDE_ROOTS')
    current={}; unassessed=[]; entries=0
    for root in roots:
        safe_path(str(root),directory=True)
        for parent,dirs,files in os.walk(root,followlinks=False):
            entries+=len(dirs)+len(files); need(entries<=MAX_FILES,'SAVED_CARRIER_ENTRY_BOUND_EXCEEDED')
            for name in dirs: safe_path(str(Path(parent)/name),directory=True)
            for name in files:
                p=Path(parent)/name
                try:
                    _,s=safe_path(str(p)); current[str(p)]=dict(path=str(p),device=s.st_dev,inode=s.st_ino,uid=s.st_uid,gid=s.st_gid,
                        mode=stat.S_IMODE(s.st_mode),nlink=s.st_nlink,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
                except (Refused,OSError): unassessed.append(dict(path=str(p),reason='UNSAFE_OR_UNREADABLE_CARRIER'))
    ranges=[]; total=0; sites={s:[] for s in SITES}; changed=[]
    for path,row in sorted(current.items()):
        prior=old.get(path)
        if prior==row: continue
        changed.append(path)
        if prior is None: start=0; kind='NEW_FILE'
        elif all(prior.get(k)==row[k] for k in ('device','inode','uid','gid','mode','nlink')) and row['bytes']>prior['bytes']:
            start=prior['bytes']; kind='SUFFIX_ONLY_PREFIX_NOT_ASSESSED'
            unassessed.append(dict(path=path,reason='PREEXISTING_PREFIX_INTEGRITY_NOT_PROVED_BY_METADATA_BASELINE'))
        else:
            unassessed.append(dict(path=path,reason='PREEXISTING_REWRITE_ROTATION_OR_TRUNCATION_NO_OLD_BODY_SWEEP')); continue
        size=row['bytes']-start
        if size>MAX_RANGE or total+size>MAX_RANGE_TOTAL:
            unassessed.append(dict(path=path,reason='FIXED_RANGE_BOUND_EXCEEDED')); continue
        p,s=safe_path(path)
        fresh=dict(path=path,device=s.st_dev,inode=s.st_ino,uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),
                   nlink=s.st_nlink,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
        need(fresh==row,'SAVED_CARRIER_INVENTORY_TO_RANGE_CAS_CHANGED')
        with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
            before=os.fstat(f.fileno()); f.seek(start); raw=f.read(size+1); after=os.fstat(f.fileno())
        need(identity(s)==identity(before)==identity(after)==identity(p.stat()) and len(raw)==size,'SAVED_CARRIER_RANGE_CAS_CHANGED')
        total+=size; ranges.append(dict(path=path,offset=start,bytes=size,kind=kind,range_sha256=digest(raw),
            private_marker_matches={k:raw.count(v) for k,v in markers.items()},body_not_copied=True))
        if path.endswith(('/agent.log','/gateway.log')):
            observations=logging_metadata(raw,origin=path,offset=start,principal=principal)
            for site,rows in observations.items(): sites[site].extend(rows)
    for path in sorted(set(old)-set(current)): unassessed.append(dict(path=path,reason='DELETED_CARRIER_NO_CONTENT_AVAILABLE'))
    distinct={site:len({r['line_sha256'] for r in rows}) for site,rows in sites.items()}
    return dict(schema='frw.Root.F07.new-technical-carriers-safe.v1',roots=baseline['roots'],post_metadata=list(current.values()),
        new_paths=sorted(set(current)-set(old)),deleted_paths=sorted(set(old)-set(current)),changed_paths=changed,
        inspected_ranges=ranges,range_bytes_read=total,per_site_observations=sites,distinct_producer_records=distinct,
        two_distinct_source_formats_in_new_ranges=all(distinct.values()),unassessed=unassessed,
        actual_producer_execution='NOT_ESTABLISHED: Root reviews logger/source provenance and exact actual turn correlation',
        journal='NOT_COLLECTED: Root supplies exact saved after-cursor bounded journal separately',
        original_current_user_request_retention='SEPARATE_ROOT_ASSESSMENT_REQUIRED',
        raw_body_persisted=False,old_bodies_swept=False,privacy_verdict='NOT_ESTABLISHED')

def observe_saved_once(checker, *, effect, observed, canonical_ref, candidate_ref, baseline_ref,
                       native_host_close_ref, lock_owners, selected_ids, ingress_row_id,
                       source_join_ref, private_markers):
    """One finite FUTURE ROOT invocation AFTER the actual operation is closed.

    This is observation only, not an admission/clock/acceptance. No writes. Root
    supplies exact actual saved refs, refreshes baseline before the future phase,
    and holds all three locks throughout. The original refused/no-run phase is
    ineligible: canonical confirmed-send data is mandatory. Exceptions propagate
    with their concrete code; caller retains raw failure/partial/unknown outcome.
    Returned private new_rows/source observations must be protected by Root.
    """
    need(effect.get('checker') is not None and tuple(checker.LOGGING_SITES)==SITES,'SAVED_EXACT_CURRENT_CHECKER_REQUIRED')
    need(effect['checker']['path']==checker.__file__
        and digest(read_reference(effect['checker']))==effect['checker']['sha256'],'SAVED_CHECKER_REFERENCE_CHANGED')
    baseline=doc(baseline_ref); host=doc(native_host_close_ref)
    need(baseline.get('schema')=='friday.Root.F07.technical-carrier-baseline.v1'
        and baseline.get('operation_started') is False and baseline.get('db_metadata')==observed['databases']
        and baseline.get('two_logging_cursors')==observed['technical_log_cursor'], 'SAVED_EXACT_ACTUAL_PREPHASE_BASELINE_REQUIRED')
    need(type(host) is dict and type(host.get('schema')) is str,'SAVED_NATIVE_HOST_CLOSE_ARTIFACT_REQUIRED')
    def locked():
        need(set(lock_owners)=={'shared_slot','consumer','credential'},'SAVED_ALL_ROOT_LOCKS_REQUIRED')
        for label,path in dict(shared_slot=checker.SLOT,consumer=checker.STATE/'consumer.lock',credential=checker.STATE/'tester-token').items():
            checker.lock_held(path,lock_owners[label])
    def native_source_refs():
        refs={}
        need(set(observed['installed']['runtime_hashes'])==set(checker.RELEVANT),'SAVED_EXACT_RELEVANT_SOURCE_SET_REQUIRED')
        for name,want in observed['installed']['runtime_hashes'].items():
            need(type(name) is str and not name.startswith('/') and '..' not in name.split('/'),'SAVED_NATIVE_SOURCE_PATH_REQUIRED')
            r=ref_of(checker.H/'hermes-agent'/name,DEFAULT_LIMIT,private=False)
            need(r['sha256']==want,'SAVED_INSTALLED_SOURCE_CHANGED'); refs[name]=r
        return refs
    locked(); sources=native_source_refs()
    custody=verify_genuine_saved_custody(checker,effect=effect,canonical_ref=canonical_ref,candidate_ref=candidate_ref,
        state_root=str(checker.STATE),lock_owners=lock_owners)
    run=doc(canonical_ref); ack=doc(custody['capture']['commitments']['ACK'])
    if run['sent_api_ack_reference'].get('representation')=='botapi-wire-envelope-json':
        need(ack.get('ok') is True and type(ack.get('result')) is dict,'SAVED_ACK_WIRE_REQUIRED'); ack=ack['result']
    else: need(run['sent_api_ack_reference'].get('representation')=='decoded-message-json','SAVED_ACK_REPRESENTATION_REQUIRED')
    need(ack.get('message_id')==run['sent_message_id'] and ack.get('chat',{}).get('id')==8751854128
        and ack.get('from',{}).get('id')==8812646969 and ack.get('from',{}).get('is_bot') is True,'SAVED_TESTER_ACK_PRINCIPAL_REQUIRED')
    rows=selected_new_rows(checker,baseline=observed['databases'],selected_ids=selected_ids)
    source=ingress_evidence_join(effect=effect,principal=checker.PRINCIPAL,canonical_ref=canonical_ref,run=run,
        ack_ref=custody['capture']['commitments']['ACK'],ack=ack,upload_task_ref=custody['capture']['commitments']['task'],
        new_rows=rows,ingress_row_id=ingress_row_id,source_join_ref=source_join_ref)
    carriers=carrier_ranges(baseline=baseline,private_markers=private_markers,principal=checker.PRINCIPAL)
    need(native_source_refs()==sources,'SAVED_NATIVE_SOURCE_CAS_CHANGED')
    for exact in (canonical_ref,candidate_ref,baseline_ref,native_host_close_ref,effect['checker'],source_join_ref,source['native_row_evidence'],*source['source_planes'].values()): read_reference(exact)
    read_reference(source['actual_native_source'],private=False)
    need(identity(safe_path(source['actual_native_source']['path'])[1])==source['received_source_identity'],'SAVED_RECEIVED_SOURCE_FINAL_IDENTITY_CHANGED'); locked()
    return dict(schema='frw.Root.F07.saved-actual-observation-package.private.v1',status='OBSERVED_NOT_ROOT_ASSESSED',
        run_id=effect['run_id'],whole_effect_sha256=digest(encoded(effect)),canonical_run=clone(canonical_ref),candidate_source=clone(candidate_ref),
        baseline=clone(baseline_ref),native_host_close=clone(native_host_close_ref),unchanged_installed_source=sources,
        custody=custody,capture=custody['capture'],new_rows=rows,source_reference_observation=source,technical_carriers=carriers,
        assessment_template=unbound_assessment(checker,effect=effect,observed=observed),
        no_extra_event_or_replay_performed=True,Root_semantic_privacy_custody_host_close='NOT_ESTABLISHED')

def unbound_assessment(checker, *, effect, observed):
    return dict(schema='frw.Root.F07.actual-postcondition-assessment.v1',operator='Root',status='UNBOUND',
        plan=checker.postcondition_plan(effect,observed),evidence={k:None for k in ('canonical_run','ACK','capture','native_ingress','technical_carriers','native_host_close')},
        raw_status=None,raw_send_state=None,raw_consumer_acceptance='NOT_ESTABLISHED',extra_event_or_replay_performed=False,
        verdicts={k:'NOT_ESTABLISHED' for k in ('semantic','privacy','custody','native_host_close')},
        per_logging_site={s:dict(execution='NOT_OBSERVED',verdict='NOT_ESTABLISHED',evidence=[]) for s in SITES})

def assess_root_bound(checker, *, effect, observed, assessment, custody_ref, source_observation_ref,
                      candidate_ref, root_judgment_ref):
    """Pure saved-data validation. Root EXPLICIT judgments, never text auto-grader.
    Returns actual current209 ABI after source/custody/capture/record review.
    Root judgment is exact private saved input, tied to these bytes and dimensions.
    """
    need(assessment.get('status')=='ROOT_ASSESSED_SAVED_ACTUAL_ONLY','SAVED_UNBOUND_NOT_ASSESSMENT')
    custody=doc(custody_ref); source=doc(source_observation_ref); root=doc(root_judgment_ref)
    run_ref=assessment.get('evidence',{}).get('canonical_run'); run=doc(run_ref)
    need(custody.get('schema')=='frw.Root.F07.saved-genuine-custody-observation.v1'
        and custody.get('canonical_run')==run_ref and custody.get('candidate_source')==candidate_ref
        and custody.get('custody_method_returned_without_refusal') is True,'SAVED_GENUINE_CUSTODY_BINDING_REQUIRED')
    need(doc(assessment['evidence']['capture'])==custody.get('capture'), 'SAVED_EXACT_CUSTODY_CAPTURE_INVENTORY_REQUIRED')
    need(source.get('schema')=='frw.Root.F07.actual-source-reference-observation.v1','SAVED_SOURCE_OBSERVATION_SCHEMA_REQUIRED')
    if source.get('representation')=='ROOT_DERIVED_MULTI_SOURCE_CUSTODY_JOIN_NOT_PRODUCT_RECORD':
        for exact in (source['source_join'],source['native_row_evidence'],*source['source_planes'].values()): read_reference(exact)
    else: read_reference(source['native_product_record'])
    actual_source=source['actual_native_source']
    need(read_reference(actual_source,private=False) is not None
        and actual_source['sha256']==effect['phase']['scenario']['steps'][0]['input']['sha256']
        and actual_source['bytes']==effect['phase']['scenario']['steps'][0]['input']['stat']['size_bytes'], 'SAVED_NATIVE_SOURCE_FINAL_CAS_REQUIRED')
    if 'received_source_identity' in source:
        need(identity(safe_path(actual_source['path'])[1])==source['received_source_identity'],'SAVED_RECEIVED_SOURCE_FINAL_IDENTITY_CHANGED')
    need(root.get('schema')=='frw.Root.F07.explicit-saved-actual-judgments.v1' and root.get('operator')=='Root'
        and root.get('run_id')==effect['run_id'] and root.get('whole_effect_sha256')==digest(encoded(effect))
        and root.get('canonical_run')==run_ref and root.get('custody_observation')==custody_ref
        and root.get('native_source_observation')==source_observation_ref and root.get('candidate_source')==candidate_ref
        and root.get('evidence')==assessment['evidence'] and root.get('verdicts')==assessment['verdicts']
        and root.get('per_logging_site')==assessment['per_logging_site']
        and type(root.get('reasons')) is dict and set(root['reasons'])==set(assessment['verdicts'])
        and all(type(v) is str and bool(v) for v in root['reasons'].values()),'SAVED_EXPLICIT_ROOT_JUDGMENTS_REQUIRED')
    ingress=doc(assessment['evidence']['native_ingress'])
    need(source.get('run_id')==effect['run_id'] and source.get('native_principal')==checker.PRINCIPAL
        and ingress.get('actual_source_ref_evidence')==source_observation_ref
        and all(ingress.get(k)==source.get(k) for k in ('native_message_row_id','native_platform_message_id','source_sha256','filename','tester_ACK_message_id')),
        'SAVED_ACTUAL_INGRESS_OBSERVATION_JOIN_REQUIRED')
    read_reference(candidate_ref)
    if assessment['verdicts']['custody']=='PASS':
        need(root.get('actual_source_planes_provenance_reviewed') is True
            and root.get('actual_ordinary_tool_context_reviewed') is True
            and root.get('actual_source_custody_reviewed') is True
            and ingress.get('actual_source_ref_custody_checked') is True,'SAVED_ROOT_SOURCE_AND_ORDINARY_CONTEXT_REVIEW_REQUIRED')
    if assessment['verdicts']['semantic']=='PASS':
        need(custody['raw'].get('full180') is True and custody['raw'].get('status_is_evidence_ready') is True
            and not any(o.get('kind')=='document' for o in run.get('observations',[])), 'SAVED_FULL180_TEXT_ONLY_REQUIRED')
    if assessment['verdicts']['privacy']=='PASS':
        need(root.get('exact_new_carriers_and_two_distinct_producers_reviewed') is True
            and root.get('original_current_request_retention_separately_reviewed') is True
            and root.get('unassessed_privacy_planes')==[], 'SAVED_WHOLE_PRIVACY_NOT_AUTOMATIC')
    return checker.assess_saved_actual(assessment,effect=effect,observed=observed)
