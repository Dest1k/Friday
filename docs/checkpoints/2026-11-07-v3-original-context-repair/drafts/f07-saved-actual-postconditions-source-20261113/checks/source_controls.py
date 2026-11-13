"""Synthetic local source controls. Never a user/runtime F07 execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import types

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('saved_f07',BASE/'source/f07_saved_actual.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
results=[]
def check(name, fn):
    fn(); results.append(dict(name=name,result='PASS_SOURCE_CONTROL'))
def refused(name, fn, code):
    try: fn()
    except Exception as e:
        assert code in str(e), (name,type(e).__name__,str(e)); results.append(dict(name=name,result='PASS_SOURCE_CONTROL',refusal=str(e))); return
    raise AssertionError(name+' failed to refuse')
def save(root,name,value):
    path=root/name; path.write_bytes(m.encoded(value)); path.chmod(0o600); return m.ref_of(path)

with tempfile.TemporaryDirectory(prefix='synthetic-',dir=BASE/'checks') as td:
    root=Path(td); root.chmod(0o700)
    for n in ('runs','updates','downloads'): (root/n).mkdir(mode=0o700)
    data=b'Harmless synthetic source bytes; no actual F07 or product state.\n'
    source=root/'controlled-source'; source.write_bytes(data); source.chmod(0o600)
    source_ref=m.ref_of(source)
    principal=dict(id='synthetic-session',session_key='synthetic:telegram:dm:100',chat_id='100')
    scenario=dict(steps=[dict(input=dict(sha256=m.digest(data),stat=dict(size_bytes=len(data)),filename='sample'))])
    effect=dict(run_id='synthetic-f07',phase=dict(scenario=scenario,scenario_sha256=m.digest(m.encoded(scenario))))
    run=dict(id=effect['run_id'],scenario=scenario,scenario_sha256=effect['phase']['scenario_sha256'],step=0,send_attempts=1,
        send_state='sent',sent_message_id=500,status='EVIDENCE_READY',sent_at=1000,capture_until=1180,capture_window_complete=True,
        observations=[],seen=[],receive_sequence=0)
    canonical=save(root/'runs','synthetic-f07.json',run)
    check('exact-canonical-effect-domain',lambda:m.strict_saved_run(run,effect=effect,canonical_ref=canonical,state_root=str(root)))
    wrong=copy.deepcopy(run); wrong['scenario_sha256']='0'*64
    refused('changed-scenario-rejected',lambda:m.strict_saved_run(wrong,effect=effect,canonical_ref=canonical,state_root=str(root)),'SAVED_RUN_EFFECT_CHANGED')
    wrong=copy.deepcopy(run); wrong['send_state']='unknown'
    refused('unknown-preserved-no-confirmed-path',lambda:m.strict_saved_run(wrong,effect=effect,canonical_ref=canonical,state_root=str(root)),'SAVED_CONFIRMED_SINGLE_SEND_REQUIRED')
    wrong=copy.deepcopy(run); wrong['send_attempts']=True
    refused('bool-send-count-not-integer',lambda:m.strict_saved_run(wrong,effect=effect,canonical_ref=canonical,state_root=str(root)),'SAVED_CONFIRMED_SINGLE_SEND_REQUIRED')
    wrong=copy.deepcopy(run); wrong['capture_window_complete']=False
    check('partial-capture-remains-partial',lambda: __import__('builtins').exec("assert m.strict_saved_run(wrong,effect=effect,canonical_ref=canonical,state_root=str(root))['full180'] is False",globals(),locals()))
    wrong=copy.deepcopy(run); wrong['capture_until']=1179
    check('short-capture-not-full180',lambda: __import__('builtins').exec("assert m.strict_saved_run(wrong,effect=effect,canonical_ref=canonical,state_root=str(root))['full180'] is False",globals(),locals()))
    wrongref=dict(canonical,bytes=canonical['bytes']+1)
    refused('3ref-size-cas',lambda:m.read_reference(wrongref),'SAVED_REFERENCE_CHANGED')
    refused('2ref-not-default-enlarged',lambda:m.read_reference(dict(path=canonical['path'],sha256=canonical['sha256'])),'SAVED_EXACT_3REF_REQUIRED')
    refused('path-domain-traversal',lambda:m.canonical(str(root)+'/../runs'),'SAVED_CANONICAL_PATH_REQUIRED')
    refused('missing-selector-not-guessed',lambda:m.select(dict(a=1),['source_ref']),'SAVED_SELECTED_FIELD_ABSENT')
    refused('bool-json-index-not-integer',lambda:m.select([1],[True]),'SAVED_EXACT_FIELD_SELECTOR_REQUIRED')
    native=dict(source_ref='opaque-native-ref',source_path=str(source),source_sha256=m.digest(data),source_bytes=len(data),
        filename='sample',native_platform_message_id='900',session_id=principal['id'],session_key=principal['session_key'])
    nr=save(root,'native-product-record.json',native); selectors={k:[k] for k in native}
    rows=dict(profiles=dict(tester=dict(selected_rows=[dict(id=41,role='user',session_id=principal['id'],platform_message_id='900',content='private synthetic request')])) )
    observation=m.ingress_evidence(effect=effect,principal=principal,ack=dict(message_id=500),new_rows=rows,
        ingress_row_id=41,native_record_ref=nr,selectors=selectors)
    check('ACK500-native900-SQL41-distinct-domains',lambda: __import__('builtins').exec("assert observation['tester_ACK_message_id']==500 and observation['native_platform_message_id']=='900' and observation['native_message_row_id']==41 and observation['grade']=='NOT_ESTABLISHED' and observation['actual_source_ref_custody_checked'] is False",globals(),locals()))
    wrongrows=copy.deepcopy(rows); wrongrows['profiles']['tester']['selected_rows'][0]['platform_message_id']='901'
    refused('native-id-not-guessed-offset',lambda:m.ingress_evidence(effect=effect,principal=principal,ack=dict(message_id=500),new_rows=wrongrows,ingress_row_id=41,native_record_ref=nr,selectors=selectors),'SAVED_NATIVE_PLATFORM_ID_MISMATCH')
    wrongnative=dict(native,source_sha256='0'*64); wn=save(root,'wrong-native-record.json',wrongnative)
    refused('native-source-byte-domain',lambda:m.ingress_evidence(effect=effect,principal=principal,ack=dict(message_id=500),new_rows=rows,ingress_row_id=41,native_record_ref=wn,selectors=selectors),'SAVED_NATIVE_SOURCE_DOMAIN_MISMATCH')
    # Normal supported contract: multiple genuine evidence planes, normalized by
    # Root. No product object contains source_ref/hash/size/sessionkey together.
    join_run=dict(run,request_metadata=dict(input_sha256=m.digest(data),input_bytes=len(data),filename='sample'))
    jc=save(root/'runs','synthetic-f07-join.json',join_run)
    ja=save(root,'synthetic-ACK.json',dict(message_id=500)); jt=save(root,'synthetic-upload-task.json',join_run['request_metadata'])
    row=rows['profiles']['tester']['selected_rows'][0]
    projected={k:row.get(k) for k in m.ID_FIELDS}; projected.update(content_sha256=m.digest(row['content'].encode()),api_content_sha256=m.digest(b''))
    jr=save(root,'synthetic-safe-new-row.json',dict(actual_new_user=projected))
    jl=save(root,'synthetic-attachment-producer-locator.json',dict(actual_received_file=str(source),native_platform_message_id='900'))
    jtr=save(root,'synthetic-new-tooltrace.json',dict(selected_new_ids=[41,42],genuine_context='NOT_ESTABLISHED'))
    join=dict(schema='frw.Root.F07.actual-native-source-custody-join.v1',operator='Root',status='ROOT_NORMALIZED_ACTUAL_EVIDENCE_ONLY',
        run_id=effect['run_id'],whole_effect_sha256=m.digest(m.encoded(effect)),canonical_run=jc,ACK=ja,upload_task=jt,
        native_message_row_id=41,native_platform_message_id='900',native_principal=principal,native_row_evidence=jr,
        native_user_row_selector=['actual_new_user'],received_source=source_ref,received_source_identity=m.identity(source.stat()),
        filename='sample',producer_locator_evidence=jl,ordinary_tool_trace_evidence=jtr)
    jref=save(root,'synthetic-Root-source-join.json',join)
    jo=m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=jref)
    check('Root-multisource-join-without-product-source-ref',lambda: __import__('builtins').exec("assert jo['source_ref'] is None and jo['representation']=='ROOT_DERIVED_MULTI_SOURCE_CUSTODY_JOIN_NOT_PRODUCT_RECORD' and jo['actual_source_ref_custody_checked'] is False and jo['ordinary_tool_context']=='NOT_ESTABLISHED' and jo['grade']=='NOT_ESTABLISHED'",globals(),locals()))
    bad_join=dict(join,native_platform_message_id='500'); bj=save(root,'bad-ACK-native-offset-join.json',bad_join)
    refused('Root-join-does-not-assume-ACK-native-equality',lambda:m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=bj),'SAVED_NATIVE_PLATFORM_ID_MISMATCH')
    bad_join=dict(join,received_source=dict(source_ref,sha256='0'*64)); bj=save(root,'bad-received-hash-join.json',bad_join)
    refused('Root-join-actual-source-byte-domain',lambda:m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=bj),'SAVED_NATIVE_SOURCE_DOMAIN_MISMATCH')
    bad_join=dict(join,received_source_identity=[0]*9); bj=save(root,'bad-received-stat-join.json',bad_join)
    refused('Root-join-received-stat-CAS',lambda:m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=bj),'SAVED_RECEIVED_SOURCE_IDENTITY_CHANGED')
    bad_projection=dict(projected,content_sha256='0'*64); br=save(root,'bad-native-row-projection.json',dict(actual_new_user=bad_projection)); bad_join=dict(join,native_row_evidence=br); bj=save(root,'bad-native-body-custody-join.json',bad_join)
    refused('Root-join-exact-new-native-row-evidence',lambda:m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=bj),'SAVED_ROOT_NEW_ROW_EVIDENCE_MISMATCH')
    bad_join=dict(join,ordinary_tool_trace_evidence=None); bj=save(root,'missing-new-native-tooltrace-join.json',bad_join)
    refused('Root-join-no-fabricated-ordinary-context',lambda:m.ingress_evidence_join(effect=effect,principal=principal,canonical_ref=jc,run=join_run,ack_ref=ja,ack=dict(message_id=500),upload_task_ref=jt,new_rows=rows,ingress_row_id=41,source_join_ref=bj),'SAVED_ACTUAL_LOCATOR_AND_SCOPED_TRACE_REQUIRED')
    # Synthetic chains test collection loss; no actual capture is claimed.
    for label,key,prefix in [('ACK','sent_api_ack_reference','send-ack-'),('window','sent_window_reference','send-window-'),('task','sent_task_reference','send-task-')]:
        r=save(root,prefix+'synthetic-f07-0-1.json',dict(synthetic=True)); run[key]=dict(basename=Path(r['path']).name,bytes=r['bytes'],sha256=r['sha256'])
    head=save(root,'receive-synthetic-f07-0-1-0.json',dict(previous=None)); run['receive_head']=dict(basename=Path(head['path']).name,bytes=head['bytes'],sha256=head['sha256'])
    inv=m.capture_references(run,state_root=str(root))
    check('exact-whole-capture-chain-inventory',lambda: __import__('builtins').exec("assert len(inv['receive_chain'])==1 and inv['full180'] is True and inv['semantic_verdict']=='NOT_ESTABLISHED'",globals(),locals()))
    (root/'receive-synthetic-f07-0-1-0.json').write_bytes(b'{}\n')
    refused('captured-chain-loss-rejected',lambda:m.capture_references(run,state_root=str(root)),'SAVED_REFERENCE_CHANGED')
    text1=b'INFO conversation turn: session=synthetic-session model=x provider=y platform=telegram history=1 input_type=str content_parts=1 msg_chars=9\n'
    text2=b'INFO inbound message: platform=telegram user=100 chat=100 kind=document attachments=1 msg_chars=9 reply_to_id=None reply_to_chars=0\n'
    log1=m.logging_metadata(text1,origin='synthetic-agent.log',offset=17,principal=principal)
    log2=m.logging_metadata(text2+text2,origin='synthetic-gateway.log',offset=29,principal=principal)
    check('distinct-producer-formats',lambda: __import__('builtins').exec("assert len(log1[m.SITES[0]])==1 and not log1[m.SITES[1]] and not log2[m.SITES[0]] and len({r['line_sha256'] for r in log2[m.SITES[1]]})==1",globals(),locals()))
    unsafe=text2.rstrip()+b' raw secret preview\n'
    check('raw-preview-format-not-credited',lambda: __import__('builtins').exec("assert not any(m.logging_metadata(unsafe,origin='synthetic',offset=0,principal=principal).values())",globals(),locals()))
    refused('log-line-fixed-bound',lambda:m.logging_metadata(b'x'*65537,origin='synthetic',offset=0,principal=principal),'SAVED_LOG_LINE_BOUND_EXCEEDED')
    fake=types.SimpleNamespace(postcondition_plan=lambda effect,observed:dict(synthetic=True))
    unbound=m.unbound_assessment(fake,effect=effect,observed={})
    check('UNBOUND-defaults-no-runtime-PASS',lambda: __import__('builtins').exec("assert unbound['status']=='UNBOUND' and set(unbound['verdicts'].values())=={'NOT_ESTABLISHED'} and all(r['execution']=='NOT_OBSERVED' for r in unbound['per_logging_site'].values())",globals(),locals()))
    refused('UNBOUND-cannot-final-assess',lambda:m.assess_root_bound(fake,effect=effect,observed={},assessment=unbound,custody_ref=None,source_observation_ref=None,candidate_ref=None,root_judgment_ref=None),'SAVED_UNBOUND_NOT_ASSESSMENT')
    refused('capture-update-count-finite-bound',lambda:m.strict_saved_run(dict(run,seen=list(range(65))),effect=effect,canonical_ref=canonical,state_root=str(root)),'SAVED_CAPTURE_FINITE_BOUND_EXCEEDED')
    refused('sized-ref-over24MiB-rejected',lambda:m.read_reference(dict(path=str(source),bytes=m.EXACT_LIMIT+1,sha256=m.digest(data))),'SAVED_EXACT_3REF_REQUIRED')
    # Three isolated synthetic DBs prove the old body is not returned/read by the
    # exact new-row projection. These are NOT the installed product databases.
    full_principal=dict(id='synthetic-session',source='telegram',user_id='100',chat_id='100',chat_type='dm',session_key='synthetic:telegram:dm:100',profile_name='synthetic',transport_profile='default')
    dbpaths={}; baseline={}
    for label in ('default','dest','tester'):
        p=root/(label+'.db'); db=sqlite3.connect(p)
        db.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY,session_id TEXT,role TEXT,timestamp REAL,platform_message_id TEXT,active INTEGER,compacted INTEGER,content TEXT,api_content TEXT,tool_calls TEXT,tool_call_id TEXT)')
        db.execute('CREATE TABLE sessions('+','.join(k+' TEXT' for k in m.SESSION_FIELDS)+')')
        db.execute('INSERT INTO sessions VALUES('+','.join('?' for _ in m.SESSION_FIELDS)+')',tuple(full_principal[k] for k in m.SESSION_FIELDS))
        db.execute("INSERT INTO messages(id,session_id,role,content) VALUES(1,'synthetic-session','user','OLD_BODY_MUST_NOT_BE_RETURNED')")
        db.execute("INSERT INTO messages(id,session_id,role,platform_message_id,content) VALUES(2,'synthetic-session','user','900','NEW_SELECTED_BODY')")
        db.commit(); db.close(); p.chmod(0o600); dbpaths[label]=p; baseline[label]=dict(max_message_id=1,identity=m.identity(p.stat())[:6])
    fake_db=types.SimpleNamespace(DATABASES=dbpaths,SID=full_principal['id'],PRINCIPAL=full_principal)
    selected=dict(default=[],dest=[],tester=[2]); projection=m.selected_new_rows(fake_db,baseline=baseline,selected_ids=selected)
    check('SQL-only-exact-selected-new-body',lambda: __import__('builtins').exec("assert 'OLD_BODY_MUST_NOT_BE_RETURNED' not in str(projection) and projection['profiles']['tester']['selected_rows'][0]['content']=='NEW_SELECTED_BODY' and projection['old_message_bodies_read'] is False",globals(),locals()))
    refused('SQL-old-selected-id-refused',lambda:m.selected_new_rows(fake_db,baseline=baseline,selected_ids=dict(default=[],dest=[],tester=[1])),'SAVED_ONLY_EXACT_NEW_ROW_IDS_ALLOWED')
    refused('SQL-more-than64-selected-id-refused',lambda:m.selected_new_rows(fake_db,baseline=baseline,selected_ids=dict(default=[],dest=[],tester=list(range(2,67)))),'SAVED_ONLY_EXACT_NEW_ROW_IDS_ALLOWED')
    # Range suffix only: old marker is absent from scan counts; old prefix is
    # explicitly unassessed and cannot become a wholeprivacy PASS.
    roots=[]
    for i in range(10):
        p=root/('carrier'+str(i)); p.mkdir(mode=0o700); roots.append(str(p))
    carrier=Path(roots[0])/'agent.log'; carrier.write_bytes(b'OLD_PRIVATE_MARKER\n'); carrier.chmod(0o600); s=carrier.stat()
    old=dict(path=str(carrier),device=s.st_dev,inode=s.st_ino,uid=s.st_uid,gid=s.st_gid,mode=0o600,nlink=1,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
    with carrier.open('ab') as f: f.write(text1)
    inventory=m.carrier_ranges(baseline=dict(roots=roots,files=[old]),private_markers=['OLD_PRIVATE_MARKER'],principal=principal)
    check('carrier-suffix-only-no-old-body-sweep',lambda: __import__('builtins').exec("assert inventory['range_bytes_read']==len(text1) and not any(sum(r['private_marker_matches'].values()) for r in inventory['inspected_ranges']) and any(r['reason']=='PREEXISTING_PREFIX_INTEGRITY_NOT_PROVED_BY_METADATA_BASELINE' for r in inventory['unassessed']) and inventory['privacy_verdict']=='NOT_ESTABLISHED'",globals(),locals()))
    refused('carrier-root-domain-exact-ten',lambda:m.carrier_ranges(baseline=dict(roots=roots[:9],files=[]),private_markers=['mark'],principal=principal),'SAVED_EXACT_TEN_ROOT_BASELINE_REQUIRED')
    # Execute only the genuine selected SOURCE's readonly custody method on
    # isolated synthetic existing Store. No actual Store/state/current/API.
    tester_ref=dict(path='/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py',bytes=1122813,sha256='cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b')
    mod=types.ModuleType('_synthetic_genuine_selected'); mod.__file__=tester_ref['path']
    exec(compile(m.read_reference(tester_ref,private=False),mod.__file__,'exec'),mod.__dict__)
    runner=mod.Runner(mod.Store(root),None)
    original_scenario=json.loads(Path('/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113/preparation/phase1-SCENARIO.PREPARED.NOT_ADMITTED.json').read_bytes())
    invalid=dict(run,scenario=original_scenario,scenario_sha256=m.digest(mod.encoded(original_scenario)),sent_ids=[500],sent_date=1,
        request_metadata=dict(scenario_sha256=m.digest(mod.encoded(original_scenario))))
    invalid['sent_api_ack_reference']=dict(basename='send-ack-synthetic-f07-0-1.json',bytes=1,sha256='0'*64,representation='decoded-message-json')
    refused('genuine-selected-custody-refuses-corrupt-ACK',lambda:runner.verify_reply_custody(invalid),'Capture outbound acknowledgement custody mismatch')
    assert runner.api is None
    # New history caller changes PREP only; validate unchanged public assessor ABI
    # against exact final checker source without calling observe/current/Store.
    checker_ref=dict(path='/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113/source/current209.py',bytes=51807,sha256='dede0e5e65a24f4b12d1f553467268f3c0d40a16bb59d22e587415385161c4e1')
    checker=types.ModuleType('_synthetic_exact_current209_checker'); checker.__file__=checker_ref['path']
    exec(compile(m.read_reference(checker_ref),checker.__file__,'exec'),checker.__dict__)
    e=dict(effect,installation_closure=dict(path='/synthetic/installation',bytes=1,sha256='1'*64),
        phase=dict(effect['phase'],phase='NO_EXTENSION',ordinal=1,expected_semantics='synthetic_only'))
    o=dict(gateway=dict(synthetic=True),databases=dict(synthetic=True),technical_log_cursor=dict(synthetic=True),installed=dict(runtime_hashes={}))
    actual_unbound=m.unbound_assessment(checker,effect=e,observed=o)
    check('exact-current209-plan-ABI',lambda: __import__('builtins').exec("assert actual_unbound['plan']['capture']==dict(full_seconds=180,max_updates=64,max_messages=32,max_documents=0,ack_seconds=30) and actual_unbound['plan']['future_output_required_preintent'] is False",globals(),locals()))
    refused('exact-current209-refuses-generated-UNBOUND',lambda:checker.assess_saved_actual(actual_unbound,effect=e,observed=o),'F07_ACTUAL_ASSESSMENT_UNBOUND')

out=dict(schema='frw.child.F07.saved-actual-source-controls.v1',all_synthetic=True,actual_F07_run=False,actual_H_SQL_STATE_API_model_send=False,
    count=len(results),controls=results,limits=dict(DEFAULT_LIMIT=m.DEFAULT_LIMIT,EXACT_LIMIT=m.EXACT_LIMIT,MAX_NEW_ROWS=m.MAX_NEW_ROWS,MAX_FILES=m.MAX_FILES,MAX_RANGE=m.MAX_RANGE,MAX_RANGE_TOTAL=m.MAX_RANGE_TOTAL))
target=BASE/'checks/SOURCE-CONTROLS.json'; target.write_bytes(m.encoded(out)); target.chmod(0o600)
print(json.dumps(dict(count=len(results),status='PASS_SOURCE_CONTROLS_ONLY')))
