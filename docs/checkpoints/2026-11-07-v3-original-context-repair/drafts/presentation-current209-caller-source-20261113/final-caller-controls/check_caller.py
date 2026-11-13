#!/usr/bin/env python3
"""Finite SOURCE controls; every runtime object and receipt below is synthetic.

Executes exact original Runner methods after exact pinned history composition.
The real retained source row, actual Store, runtime and user bodies are not read.
No network/client/model/service/install operation is constructed or invoked.
"""
from __future__ import annotations
import ast
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time
import types

BASE = Path(__file__).resolve().parent
PARENT = BASE.parent / 'presentation_prepare.py'
START = time.monotonic()
STARTED = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat()
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024**2, 100 * 1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))

def enc(v):
    return (json.dumps(v, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def reference(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw))

def load(raw, path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module

def write(path, value, *, raw=False):
    data = value if raw else enc(value)
    path.write_bytes(data)
    path.chmod(0o600)
    return dict(basename=path.name, bytes=len(data), sha256=sha(data))

def source_method(raw, name):
    text = raw.decode()
    tree = ast.parse(text)
    runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
    return next(n for n in runner.body if isinstance(n, ast.FunctionDef) and n.name == name)

def body_dump(raw, name):
    return ast.dump(source_method(raw, name), include_attributes=False)

class PrefixBoundary(Exception):
    pass

class SideEffect(Exception):
    pass

RESULTS = []
DEFECTS = []

def check(name, fn, *, refuses=False, contains=None):
    before = time.monotonic()
    try:
        value = fn()
        if value is False:
            raise AssertionError('Control returned False')
        if refuses:
            RESULTS.append(dict(name=name, status='FAIL_ACCEPTED', synthetic=True))
            return False
        RESULTS.append(dict(name=name, status='PASS', synthetic=True, detail=value,
                            elapsed_seconds=round(time.monotonic()-before, 6)))
        return True
    except (ValueError, Refused) as exc:
        if not refuses:
            RESULTS.append(dict(name=name, status='FAIL_REFUSED', synthetic=True,
                                exception_class=type(exc).__name__, reason=str(exc)))
            return False
        matched = contains is None or contains in str(exc)
        RESULTS.append(dict(name=name, status='PASS_REFUSED' if matched else 'FAIL_WRONG_REFUSAL',
                            synthetic=True, exception_class=type(exc).__name__, reason=str(exc)))
        return matched
    except Exception as exc:
        RESULTS.append(dict(name=name, status='ERROR', synthetic=True,
                            exception_class=type(exc).__name__, reason=str(exc)))
        return False

parent_raw = PARENT.read_bytes()
p = load(parent_raw, PARENT, '_presentation_parent_control')
base_path = Path(p.SELECTED_TESTER)
base_raw = base_path.read_bytes()
shared_path = Path(p.SHARED['path'])
shared_raw = shared_path.read_bytes()
candidate_path = Path(p.CANDIDATE['path'])
candidate_raw = candidate_path.read_bytes()
assert sha(base_raw) == p.SELECTED_SHA
assert len(shared_raw) == p.SHARED['bytes'] and sha(shared_raw) == p.SHARED['sha256']
assert len(candidate_raw) == p.CANDIDATE['bytes'] and sha(candidate_raw) == p.CANDIDATE['sha256']
shared = load(shared_raw, shared_path, '_exact_shared_control')
shared.__source_raw__ = shared_raw

# The following object satisfies only the SOURCE shape contract. Its reference
# values are explicit synthetic placeholders and NEVER prove a real upload.
def shape_unit():
    ref = lambda name: dict(path=str(BASE / ('synthetic-' + name + '.json')),
                            bytes=1, sha256='a'*64)
    original = {k: ref(k) for k in p.ORIGINAL_REFS}
    original.update(run=dict(path='/home/jericho/.local/share/friday-telegram-bot-test/runs/'
        + p.SOURCE_REF['run_id'] + '.json', bytes=1, sha256=p.SOURCE_REF['run_sha256']),
        source_native_ingress=3289, source_platform_message_id='4211', original_sent_id=2138)
    return dict(schema='frw.PRESENTATION.retained-original-upload.v1',
        source_reference=copy.deepcopy(p.SOURCE_REF), original_alias=p.ALIAS,
        original=original, principal=p.PRINCIPAL,
        conversation=dict(session_id=p.SID, session_key=p.KEY),
        current_source=dict(path=str(BASE / 'synthetic-source' / p.ALIAS), bytes=48100,
            sha256=p.SOURCE_SHA, stat=dict(device=1, inode=1, size_bytes=48100,
                uid=1000, mtime_ns=1, ctime_ns=1)), Root_binding=ref('root-binding'))

unit = shape_unit()
phase = p.preparation(candidate_raw, retained_unit=unit,
    runtime_basis=dict(path=str(BASE/'synthetic-runtime.json'), bytes=1, sha256='b'*64))
RUN_ID = 'synthetic-presentation-new-source-control'
NOW = 10000.0
fixture = BASE / 'synthetic-store'
if fixture.exists():
    shutil.rmtree(fixture)
fixture.mkdir(mode=0o700)
proc = fixture/'proc'
(proc/'sys/kernel/random').mkdir(mode=0o700, parents=True)
(proc/'987654').mkdir(mode=0o700)
write(proc/'sys/kernel/random/boot_id', b'SYNTHETIC-BOOT\n', raw=True)
write(proc/'987654/stat', (' '.join(['synthetic']*21+['123456'])+'\n').encode(), raw=True)
state_path = fixture/'synthetic-gateway-state.json'
gateway_state = dict(pid=987654, start_time='123456', gateway_state='running',
    active_agents=0, active_work=None, restart_requested=False,
    updated_at=dt.datetime.fromtimestamp(NOW, dt.timezone.utc).isoformat(),
    session_store=dict(status='ok'), platforms=dict(telegram=dict(state='connected',
        needs_attention=False, writer_pid=987654, writer_start_time='123456')))
write(state_path, gateway_state)

authority = dict(schema='frw.Root.ordinary-independent-history-admission.v1', operator='Root',
    authority_id='SYNTHETIC-PRESENTATION-SOURCE-CONTROL-ONLY', accepted=True,
    run_scenarios={RUN_ID:phase['scenario_sha256']}, history={'placeholder1':{},'placeholder2':{}},
    created_at=NOW-1, expires_at=NOW+1, boot_id='SYNTHETIC-BOOT',
    no_old_task_replay=True, new_independent_inputs_only=True, unknown_effects_resolved=False,
    old_rows_modified=False, new_trial_for_historical_task=False, product_or_B00_acceptance=False,
    ordered_predecessors={}, gateway=dict(state_path=str(state_path), pid=987654,
        start_time='123456', maximum_staleness_seconds=30),
    presentation_original_case=dict(case_id='F-04', case_index=165, direction='PPTX_TO_ODP',
        genuinely_missing_original_forward=True, no_converter_or_App_replay=True,
        source_reference=copy.deepcopy(p.SOURCE_REF), original_alias=p.ALIAS,
        principal=p.PRINCIPAL, conversation=copy.deepcopy(unit['conversation'])),
    presentation_task=dict(kind='ordinary-document-task', nonce='cccccccccccccccccccccccccccccccc',
        request=phase['scenario']['steps'][0]['request'], source_reference=copy.deepcopy(p.SOURCE_REF),
        output=dict(filename=None, mime_type=p.ODP)))
authority_path=fixture/'synthetic-authority.json'

def composed_for(auth, ph=phase):
    raw=enc(auth)
    return p.compose_source(base_raw, ph, run_id=RUN_ID,
        authority_ref=reference(authority_path,raw), authority=auth, shared_module=shared)

composed_raw=composed_for(authority)
m=load(composed_raw, BASE/'synthetic-composed-source.py', '_synthetic_composed_control')
Refused=m.Refused
real_path=Path
def fixture_path(value='.'):
    value=real_path(value)
    if value==real_path('/proc') or real_path('/proc') in value.parents:
        return proc / value.relative_to('/proc')
    return value
m.Path=fixture_path
store=m.Store(fixture)
EVENTS=[]
CLOCK_READS=[]
def clock():
    CLOCK_READS.append(NOW)
    return NOW
runner=m.Runner(store, None, clock=clock, sleep=lambda *_: (_ for _ in ()).throw(SideEffect('sleep')))
original_cursor=runner.cursor_offsets
original_receive=runner.receive_inventory
original_admission=runner.ordinary_independent_admission
def cursor(*args,**kw):
    EVENTS.append('cursor_offsets')
    return original_cursor(*args,**kw)
def receive(*args,**kw):
    EVENTS.append('receive_inventory')
    return original_receive(*args,**kw)
def admission(*args,**kw):
    EVENTS.append('ordinary_independent_admission')
    return original_admission(*args,**kw)
runner.cursor_offsets=cursor
runner.receive_inventory=receive
runner.ordinary_independent_admission=admission
runner.save=lambda *_: (_ for _ in ()).throw(SideEffect('save'))
runner.send=lambda *_: (_ for _ in ()).throw(SideEffect('send'))
runner.observe=lambda *_: (_ for _ in ()).throw(SideEffect('observe'))
m.stamp=lambda: (_ for _ in ()).throw(SideEffect('stamp'))

old_scenario=copy.deepcopy(phase['scenario'])
old_scenario['steps'][0]['request']='SYNTHETIC SOURCE CONTROL: no user request, no effect.'
body=enc(dict(chat_id=m.USERNAME, text=old_scenario['steps'][0]['request']))
metadata=dict(method='sendMessage',params=dict(chat_id=m.USERNAME,text=old_scenario['steps'][0]['request']),
    body_sha256=sha(body),body_bytes=len(body),scenario_sha256=sha(enc(old_scenario)))
old=dict(id='synthetic-sent-history',scenario=old_scenario,scenario_sha256=sha(enc(old_scenario)),
    deadline=9000.0,step=0,status='STOPPED',send_state='sent',send_attempts=1,
    sent_message_id=777,sent_ids=[777],sent_date=8000,sent_at=8000.0,
    send_intent_at=7999.0,send_dispatch_at=7999.0,send_timeout_seconds=10,
    capture_until=8180.0,capture_start_offset=100,
    seen=[],message_ids=[],observations=[],update_count=0,
    reply_capture_prior_tracking=None,request_metadata=metadata)
old['sent_api_ack_reference']=dict(write(fixture/'send-ack-synthetic-sent-history-0-1.json',
    dict(chat=dict(id=m.PEER,type='private'),message_id=777,date=8000)), representation='decoded-message-json')
old['sent_task_reference']=write(fixture/'send-task-synthetic-sent-history-0-1.json',metadata)
window=dict(run_id=old['id'],scenario_sha256=old['scenario_sha256'],step=0,send_attempts=1,
    sent_message_id=777,sent_at=8000.0,send_intent_at=7999.0,send_dispatch_at=7999.0,
    send_timeout_seconds=10,window_seconds=180,capture_until=8180.0,deadline=9000.0,
    ack=old['sent_api_ack_reference'],task=old['sent_task_reference'],continuation=None)
old['sent_window_reference']=write(fixture/'send-window-synthetic-sent-history-0-1.json',window)
context=runner.receive_context(old)
records=[dict(kind='seed',offset=100)]
wire=write(fixture/'terminal-response-synthetic-sent-history-0-1.json',dict(ok=True,result=[]))
records.extend([dict(kind='terminal_intent',offset=100,started_at=8181.0,timeout_seconds=10,
    update_count=0,limit=20),dict(kind='terminal_response',offset=100,received_at=8182.0,wire=wire),
    dict(kind='terminal_complete',offset=100,completed_at=8183.0)])
previous=None
for index,record in enumerate(records):
    record.update(context=context,sequence=index,previous=previous)
    previous=write(fixture/('receive-synthetic-sent-history-0-1-'+str(index)+'.json'),record)
old.update(receive_head=previous,receive_sequence=len(records)-1)
old_path=store.run_path(old['id'])
write(old_path,old)
unknown=dict(id='synthetic-unknown-history',scenario=old_scenario,
    scenario_sha256=sha(enc(old_scenario)),step=0,status='UNRESOLVED',send_state='unknown',deadline=9000.0)
unknown_path=store.run_path(unknown['id'])
write(unknown_path,unknown)
cursor_value=dict(offset=100,capture_receipts={runner.receive_key(old):old['receive_head']})
write(fixture/'cursor.json',cursor_value)

def refresh_authority():
    authority['history']={}
    for row,path in [(old,old_path),(unknown,unknown_path)]:
        authority['history'][row['id']]=dict(sha256=sha(path.read_bytes()),status=row['status'],
            send_state=row['send_state'],deadline=row['deadline'],new_effect_replay_authorized=False,
            unknown_retained=row['send_state']=='unknown')
    raw=enc(authority)
    write(authority_path,raw,raw=True)
    # Recompose only the exact authority pin/cardinality seams, preserving methods.
    raw2=composed_for(authority)
    fresh=load(raw2, BASE/'synthetic-composed-source.py', '_synthetic_seams_control')
    runner.ORDINARY_INDEPENDENT_AUTHORITY=fresh.Runner.ORDINARY_INDEPENDENT_AUTHORITY
    runner.ORDINARY_INDEPENDENT_SCENARIOS=fresh.Runner.ORDINARY_INDEPENDENT_SCENARIOS
    return raw2

composed_raw=refresh_authority()
def snapshot():
    return {str(x.relative_to(fixture)):sha(x.read_bytes()) for x in fixture.rglob('*') if x.is_file()}
def qualify():
    EVENTS.clear();CLOCK_READS.clear()
    before=snapshot()
    result=runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    assert result['state']=='WHOLE_ORIGINAL_NEW_PREFIX_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION'
    assert result['new_called'] is False and result['save_called'] is False
    assert result['run_constructed'] is False and result['operation_clock_created'] is False
    assert snapshot()==before
    assert EVENTS[0]=='cursor_offsets' and EVENTS[1]=='receive_inventory'
    assert EVENTS.index('receive_inventory')<EVENTS.index('ordinary_independent_admission')
    assert CLOCK_READS and set(CLOCK_READS)=={NOW}
    return dict(events=list(EVENTS),freshness_clock_reads=len(CLOCK_READS),
        operation_clock_created=False,stamp_called=False,save_called=False,api=None,
        all_fixture_bytes_unchanged=True,actual_original_methods=True)

check('actual-whole-original-readonly-prefix-positive-synthetic',qualify)
check('original-capture-context-synthetic-receipts',lambda:runner.verify_capture_context(old) is None)
check('original-window-ACK10-synthetic-receipts',lambda:runner.verify_window(old) is None)
check('original-reply-custody-full-empty-terminal-synthetic',lambda:runner.verify_reply_custody(old) is None)

def prefix_to_construction_boundary():
    EVENTS.clear();CLOCK_READS.clear();before=snapshot()
    def stop():
        raise PrefixBoundary()
    m.stamp=stop
    try:
        runner.new(RUN_ID,phase['scenario'])
        raise AssertionError('Original new did not reach construction boundary')
    except PrefixBoundary:
        pass
    finally:
        m.stamp=lambda: (_ for _ in ()).throw(SideEffect('stamp'))
    assert snapshot()==before
    assert EVENTS[0]=='cursor_offsets' and EVENTS[1]=='receive_inventory'
    assert 'ordinary_independent_admission' in EVENTS
    return dict(actual_original_new=True,stopped_at='first_stamp_call_before_run_construction',
        all_fixture_bytes_unchanged=True,operation_clock_created=False,save_called=False,
        freshness_clock_reads=len(CLOCK_READS))
check('actual-original-new-entire-prefix-up-to-first-construction',prefix_to_construction_boundary)

# Compare original AST statements through observer-stop with the exact helper.
def prefix_equivalent():
    original=source_method(base_raw,'new')
    qualifier=source_method(composed_raw,'_f07_qualify_new_prefix_readonly')
    original_prefix=[]
    for statement in original.body:
        if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='run' for t in statement.targets):
            break
        original_prefix.append(statement)
    # Qualifier adds api=None refusal and continuation=None then exact prefix.
    actual=qualifier.body[2:-1]
    assert [ast.dump(n,include_attributes=False) for n in original_prefix]==[ast.dump(n,include_attributes=False) for n in actual]
    return dict(exact_original_statements=len(actual),branch_subtrees_preserved=True)
check('shared-helper-whole-prefix-AST-equivalence',prefix_equivalent)

for method in ['new','send_ack_budget','valid_send_budget','verify_capture_context','verify_window',
               'cursor_offsets','receive_inventory','read_reference','ordinary_independent_history_row',
               'ordinary_independent_current_rows']:
    check('unchanged-original-method-'+method,lambda method=method: body_dump(base_raw,method)==body_dump(composed_raw,method) or (_ for _ in ()).throw(AssertionError('changed original method')))

def mutate_file(path,mutator,fn):
    original=path.read_bytes()
    value=json.loads(original);mutator(value);write(path,value)
    try:return fn()
    finally:write(path,original,raw=True)

check('cursor-invalid-type-before-receive-inventory',lambda:mutate_file(fixture/'cursor.json',
    lambda x:x.update(offset=True),lambda:runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])),refuses=True,contains='cursor invalid')
check('cursor-head-removal-refused-before-admission',lambda:mutate_file(fixture/'cursor.json',
    lambda x:x['capture_receipts'].clear(),lambda:runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])),refuses=True,contains='capture heads')
check('receive-inventory-seed-sequence-refused',lambda:mutate_file(fixture/'receive-synthetic-sent-history-0-1-0.json',
    lambda x:x.update(sequence=True),lambda:runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])),refuses=True,contains='bytes/hash changed')
check('receive-inventory-terminal-window-refused',lambda:mutate_file(fixture/'receive-synthetic-sent-history-0-1-1.json',
    lambda x:x.update(started_at=8000),lambda:runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])),refuses=True,contains='bytes/hash changed')

def rehashed_receipt(index, mutator):
    saved={x:x.read_bytes() for x in fixture.rglob('*') if x.is_file()}
    value=copy.deepcopy(records[index]);mutator(value)
    previous=write(fixture/('receive-synthetic-sent-history-0-1-'+str(index)+'.json'),value)
    for subsequent in range(index+1,len(records)):
        value=copy.deepcopy(records[subsequent]);value['previous']=previous
        previous=write(fixture/('receive-synthetic-sent-history-0-1-'+str(subsequent)+'.json'),value)
    altered=copy.deepcopy(old);altered['receive_head']=previous
    write(old_path,altered)
    altered_cursor=copy.deepcopy(cursor_value)
    altered_cursor['capture_receipts'][runner.receive_key(old)]=previous
    write(fixture/'cursor.json',altered_cursor)
    EVENTS.clear()
    try:
        return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:
        assert EVENTS[:2]==['cursor_offsets','receive_inventory']
        assert 'ordinary_independent_admission' not in EVENTS
        for path,raw in saved.items():write(path,raw,raw=True)
check('semantic-receipt-sequence-bool-rehashed',lambda:rehashed_receipt(0,
    lambda x:x.update(sequence=True)),refuses=True,contains='sequence')
check('semantic-terminal-intent-before-window-rehashed',lambda:rehashed_receipt(1,
    lambda x:x.update(started_at=8000.0)),refuses=True,contains='terminal drain intent')
check('semantic-terminal-response-after-timeout-rehashed',lambda:rehashed_receipt(2,
    lambda x:x.update(received_at=8200.0)),refuses=True,contains='terminal response boundary')
check('semantic-terminal-complete-after-deadline-rehashed',lambda:rehashed_receipt(3,
    lambda x:x.update(completed_at=9000.0)),refuses=True,contains='terminal drain cannot complete')

def unknown_drift():
    original=unknown_path.read_bytes()
    row=copy.deepcopy(unknown);row['deadline']=9001.0;write(unknown_path,row)
    try:return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:write(unknown_path,original,raw=True)
check('exact-unknown-history-drift-refused',unknown_drift,refuses=True,contains='history bytes changed')
def outside_history():
    path=store.run_path('synthetic-unadmitted-unknown')
    row=copy.deepcopy(unknown);row['id']='synthetic-unadmitted-unknown';write(path,row)
    try:return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:path.unlink()
check('unadmitted-unknown-current-row-refused',outside_history,refuses=True,contains='Unfinished prior run')
def used_id():
    path=store.run_path(RUN_ID);write(path,dict(id=RUN_ID,scenario=old_scenario,
        step=0,status='PREPARED',send_state='none'))
    try:return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:path.unlink()
check('used-run-ID-refused',used_id,refuses=True,contains='Run ID already used')
def stop_marked():
    path=fixture/'observer-stop.json';write(path,dict(synthetic=True))
    try:return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:path.unlink()
check('observer-stop-refused',stop_marked,refuses=True,contains='Observer stop marker')
def api_present():
    runner.api=object()
    try:return runner._f07_qualify_new_prefix_readonly(RUN_ID,phase['scenario'])
    finally:runner.api=None
check('readonly-api-presence-refused',api_present,refuses=True,contains='api=None')
check('historical-ACK-exact-original10',lambda:runner.send_ack_budget(old)==10)
override=copy.deepcopy(old);override['new_ack_timeout_seconds']=30
check('historical-ACK-cannot-copy-F07new30',lambda:runner.send_ack_budget(override),refuses=True,contains='original ACK bound')
check('window-30-cannot-replace-historical10',lambda:mutate_file(fixture/'send-window-synthetic-sent-history-0-1.json',
    lambda x:x.update(send_timeout_seconds=30),lambda:runner.verify_window(old)),refuses=True,contains='custody mismatch')

# Structural input negatives exercise parent consumer and actual selected tester.
def changed_phase(change,recompute=False):
    q=copy.deepcopy(phase);change(q)
    if recompute:q['scenario_sha256']=sha(enc(q['scenario']))
    return p.validate_preparation(q)
phase_negatives=[
 ('phase-direction',lambda q:q.update(phase='ODP_TO_PPTX'),False),
 ('phase-ordinal-bool',lambda q:q.update(ordinal=True),False),
 ('phase-state',lambda q:q.update(state='EFFECT_GRANTED'),False),
 ('phase-timing-ACK30',lambda q:q['timing'].update(ack_seconds=30),False),
 ('scenario-principal',lambda q:q['scenario'].update(tester_id=1),True),
 ('scenario-deadline-float',lambda q:q['scenario'].update(deadline_seconds=300.0),True),
 ('scenario-step-input-replay',lambda q:q['scenario']['steps'][0].update(input={}),True),
 ('scenario-window179',lambda q:q['scenario']['steps'][0]['observe'].update(window_seconds=179),True),
 ('scenario-hash-mismatch',lambda q:q['scenario']['steps'][0].update(request='SYNTHETIC CHANGED'),False),
 ('source-native-tester-ID-confusion',lambda q:q['retained_unit']['original'].update(source_native_ingress=2138),False),
 ('source-platform-ID-type',lambda q:q['retained_unit']['original'].update(source_platform_message_id=4211),False),
 ('source-original-sent-bool',lambda q:q['retained_unit']['original'].update(original_sent_id=True),False),
 ('source-alias',lambda q:q['retained_unit'].update(original_alias='received/synthetic-other.pptx'),False),
 ('source-stat-bool',lambda q:q['retained_unit']['current_source']['stat'].update(device=True),False),
 ('source-unit-extra-field',lambda q:q['retained_unit'].update(synthetic_extra=True),False),
 ('phase-extra-field',lambda q:q.update(synthetic_extra=True),False),
]
for name,change,recompute in phase_negatives:
    check('parent-negative-'+name,lambda change=change,recompute=recompute:changed_phase(change,recompute),refuses=True)

equality_probes=[
 ('observe-max-documents-bool',lambda q:q['scenario']['steps'][0]['observe'].update(max_documents=True),True),
 ('observe-window-float',lambda q:q['scenario']['steps'][0]['observe'].update(window_seconds=180.0),True),
 ('timing-ACK-float',lambda q:q['timing'].update(ack_seconds=10.0),False),
]
for name,change,recompute in equality_probes:
    ok=check('parent-type-equality-'+name,lambda change=change,recompute=recompute:changed_phase(change,recompute),refuses=True)
    if not ok:DEFECTS.append(dict(code='PARENT_TYPE_EQUALITY_ACCEPTANCE',field=name))

for name,mut in [('observe-bool',lambda s:s['steps'][0]['observe'].update(max_documents=True)),
                 ('observe-float',lambda s:s['steps'][0]['observe'].update(window_seconds=180.0))]:
    scenario=copy.deepcopy(phase['scenario']);mut(scenario)
    check('actual-selected-scenario-negative-'+name,lambda scenario=scenario:m.validate_scenario(scenario),refuses=True)

def bad_compose(mut):
    q=copy.deepcopy(authority);mut(q)
    return composed_for(q)
for name,mut in [
 ('sourceunit-conversation',lambda a:a['presentation_original_case']['conversation'].update(session_key='SYNTHETIC-OTHER')),
 ('sourceunit-direction',lambda a:a['presentation_original_case'].update(direction='ODP_TO_PPTX')),
 ('task-nonce-unbound',lambda a:a['presentation_task'].update(nonce='UNBOUND00')),
 ('task-output-MIME',lambda a:a['presentation_task']['output'].update(mime_type='application/pdf')),
 ('scenario-binding',lambda a:a['run_scenarios'].update({RUN_ID:'0'*64})),
 ('historical-replay',lambda a:a.update(no_old_task_replay=False)),
 ('history-empty',lambda a:a.update(history={})),
]:
    check('authority-negative-'+name,lambda mut=mut:bad_compose(mut),refuses=True)
for name,mut in [
 ('case-index-float',lambda a:a['presentation_original_case'].update(case_index=165.0)),
 ('original-forward-integer',lambda a:a['presentation_original_case'].update(genuinely_missing_original_forward=1)),
]:
    ok=check('authority-type-equality-'+name,lambda mut=mut:bad_compose(mut),refuses=True)
    if not ok:DEFECTS.append(dict(code='PARENT_AUTHORITY_TYPE_EQUALITY_ACCEPTANCE',field=name))

check('compose-selected-pin-changed',lambda:p.compose_source(base_raw+b'\n',phase,run_id=RUN_ID,
    authority_ref=reference(authority_path,enc(authority)),authority=authority,shared_module=shared),refuses=True)
check('compose-shared-source-substitution',lambda:p.compose_source(base_raw,phase,run_id=RUN_ID,
    authority_ref=reference(authority_path,enc(authority)),authority=authority,shared_module=types.ModuleType('untrusted')),refuses=True)
changed_unit=copy.deepcopy(unit);changed_unit['conversation']['session_key']='SYNTHETIC-OTHER'
check('compose-retained-unit-substitution',lambda:p.compose_source(base_raw,phase,run_id=RUN_ID,
    authority_ref=reference(authority_path,enc(authority)),authority=authority,retained_unit=changed_unit,
    shared_module=shared),refuses=True)

# No fake full retained-upload success: the actual wrapper must reject synthetic
# shape metadata instead of treating its fixed historical SHA as real authority.
runner._presentation_reference_bytes=lambda ref:b'SYNTHETIC-NOT-ORIGINAL'
check('full-parent-readonly-rejects-synthetic-original-reference',
    lambda:p.qualify_selected_ordinary_readonly(runner,run_id=RUN_ID,phase=phase),
    refuses=True,contains='ORIGINAL_REFERENCE_CHANGED')

# Exact retained-unit consumer and original custody methods with one explicit
# synthetic trust-anchor substitution. No real historical row is opened.
def original_unit_control(*,envelope=False,deception=None,ack_change=None,source_change=None):
    saved=snapshot()
    saved_raw={x:x.read_bytes() for x in fixture.rglob('*') if x.is_file()}
    ps=load(parent_raw,PARENT,'_synthetic_original_upload_exact_methods')
    src=copy.deepcopy(old)
    src.update(id=p.SOURCE_REF['run_id'],sent_message_id=2138,sent_ids=[2138],
        capture_window_complete=True)
    if source_change:source_change(src)
    inp=dict(kind='document',path='/synthetic/public/presentation_core.pptx',
        sha256=p.SOURCE_SHA,stat=copy.deepcopy(unit['current_source']['stat']),
        filename='presentation_core.pptx',mime_type=m.UPLOAD_TYPES['pptx'],
        caption='SYNTHETIC SOURCE CONTROL ONLY')
    src['scenario']=copy.deepcopy(old_scenario)
    src['scenario']['steps'][0]={'input':inp,'observe':copy.deepcopy(old_scenario['steps'][0]['observe'])}
    src['scenario_sha256']=sha(enc(src['scenario']))
    src['request_metadata']=dict(method='sendDocument',chat_id=m.USERNAME,input_sha256=p.SOURCE_SHA,
        input_bytes=48100,input_stat=inp['stat'],filename=inp['filename'],mime_type=inp['mime_type'],
        caption=inp['caption'],content_type='multipart/form-data; boundary=frw-'+'c'*64,
        body_sha256='d'*64,body_bytes=48200,scenario_sha256=src['scenario_sha256'])
    ack=dict(message_id=2138,date=8000,chat=dict(id=m.PEER,type='private'),
        **{'from':dict(id=m.TESTER,is_bot=True)},caption=inp['caption'],document=dict(
            file_id='SYNTHETIC-FILE',file_unique_id='SYNTHETIC-UNIQUE',
            file_name='presentation_core.pptx',mime_type=inp['mime_type'],file_size=48100))
    if ack_change:ack_change(ack)
    ack_name='send-ack-'+src['id']+'-0-1.json'
    ack_raw=enc(dict(ok=True,result=ack) if envelope else ack)
    src['sent_api_ack_reference']=dict(write(fixture/ack_name,ack_raw,raw=True),
        representation='botapi-wire-envelope-json' if envelope else 'decoded-message-json')
    src['sent_task_reference']=write(fixture/('send-task-'+src['id']+'-0-1.json'),src['request_metadata'])
    win=copy.deepcopy(window)
    win.update(run_id=src['id'],scenario_sha256=src['scenario_sha256'],sent_message_id=2138,
        ack=src['sent_api_ack_reference'],task=src['sent_task_reference'])
    src['sent_window_reference']=write(fixture/('send-window-'+src['id']+'-0-1.json'),win)
    r2=m.Runner(store,None,clock=clock)
    recs=copy.deepcopy(records)
    recs[2]['wire']=write(fixture/('terminal-response-'+src['id']+'-0-1.json'),dict(ok=True,result=[]))
    prev=None
    for i,rec in enumerate(recs):
        rec.update(context=r2.receive_context(src),sequence=i,previous=prev)
        prev=write(fixture/('receive-'+src['id']+'-0-1-'+str(i)+'.json'),rec)
    src.update(receive_head=prev,receive_sequence=len(recs)-1)
    src_raw=enc(src)
    write(store.run_path(src['id']),src_raw,raw=True)
    cv=copy.deepcopy(cursor_value);cv['capture_receipts'][r2.receive_key(src)]=prev
    write(fixture/'cursor.json',cv)
    # OWNER-APPROVED TEST-ONLY substitution, unchanged method bodies.
    ps.SOURCE_REF=dict(p.SOURCE_REF,run_sha256=sha(src_raw))
    u=copy.deepcopy(unit);u['source_reference']=copy.deepcopy(ps.SOURCE_REF)
    u['original']['run']=dict(path=unit['original']['run']['path'],bytes=len(src_raw),sha256=sha(src_raw))
    u['original']['source_upload_ack']=reference(fixture/ack_name,ack_raw)
    u['original']['window']=reference(fixture/src['sent_window_reference']['basename'],enc(win))
    by_path={u['original']['run']['path']:src_raw,
        u['original']['source_upload_ack']['path']:ack_raw,u['original']['window']['path']:enc(win)}
    for key in ('admission','custody','closed_operation'):
        raw=enc(dict(synthetic=True,receipt=key))
        u['original'][key]=reference(fixture/('synthetic-original-'+key+'.json'),raw)
        by_path[u['original'][key]['path']]=raw
    if deception:
        key='source_upload_ack' if deception=='ACK-alias' else 'window'
        original_ref=u['original'][key]
        fake_path=fixture/('synthetic-deceptive-'+key+'.json')
        u['original'][key]=dict(original_ref,path=str(fake_path))
        by_path[str(fake_path)]=by_path[original_ref['path']]
    metadata=dict(schema='frw.Root.PRESENTATION.original-upload-metadata.v1',operator='Root',
        status='ROOT_BOUND_ORIGINAL_UPLOAD',source_reference=ps.SOURCE_REF,original_alias=p.ALIAS,
        original=u['original'],principal=u['principal'],conversation=u['conversation'],
        current_source=u['current_source'],source_unchanged=True,original_upload_authority_verified=True,
        original_operation_closed=True,original_effect_not_replayed=True)
    raw=enc(metadata);u['Root_binding']=reference(fixture/'synthetic-original-root-binding.json',raw)
    by_path[u['Root_binding']['path']]=raw
    r2._presentation_reference_bytes=lambda ref:by_path[ref['path']]
    try:
        result=ps.validate_original_runner(r2,u)
        assert result['state']=='ORIGINAL_UPLOAD_UNIT_AUTHENTICATED_NOT_NEW_EFFECT_GRANT'
        assert r2.send_ack_budget(src)==10
        return dict(exact_parent_method_body=True,exact_original_capture_window_custody_methods=True,
            synthetic_expected_run_sha256_substitution=True,real_original_authentication=False,
            ack_representation=src['sent_api_ack_reference']['representation'],historical_ack_seconds=10)
    finally:
        for x in list(fixture.rglob('*')):
            if x.is_file() and x not in saved_raw:x.unlink()
        for path,raw in saved_raw.items():write(path,raw,raw=True)
        assert snapshot()==saved
check('controlled-original-unit-decoded-ACK-full-consumer',lambda:original_unit_control())
check('controlled-original-unit-wire-envelope-ACK-full-consumer',lambda:original_unit_control(envelope=True))
check('controlled-original-ACK-same-bytes-alias-deception',lambda:original_unit_control(deception='ACK-alias'),
    refuses=True,contains='ACK_WINDOW_REFERENCE_JOIN_REQUIRED')
check('controlled-original-window-same-bytes-alias-deception',lambda:original_unit_control(deception='window-alias'),
    refuses=True,contains='ACK_WINDOW_REFERENCE_JOIN_REQUIRED')
check('controlled-original-ACK-native-platform-ID-confusion',lambda:original_unit_control(
    ack_change=lambda a:a.update(message_id=4211)),refuses=True,contains='message/context mismatch')
check('controlled-original-ACK-file-size-bool',lambda:original_unit_control(
    ack_change=lambda a:a['document'].update(file_size=True)),refuses=True)
if not check('controlled-original-ACK-sender-type-float',lambda:original_unit_control(
    ack_change=lambda a:a['from'].update(id=8812646969.0)),refuses=True):
    DEFECTS.append(dict(code='PARENT_ORIGINAL_ACK_SENDER_FLOAT_ACCEPTED',field='from.id'))
check('controlled-original-wire-ACK-sender-type-float',lambda:original_unit_control(envelope=True,
    ack_change=lambda a:a['from'].update(id=8812646969.0)),refuses=True)
check('controlled-original-ACK-chat-type-float',lambda:original_unit_control(
    ack_change=lambda a:a['chat'].update(id=8751854128.0)),refuses=True)
check('controlled-original-sent-message-type-float',lambda:original_unit_control(
    source_change=lambda s:s.update(sent_message_id=2138.0)),refuses=True)

driver_path=BASE.parent/'root_presentation_once.py'
driver_raw=driver_path.read_bytes()
driver_tree=ast.parse(driver_raw)
def function_calls(name):
    n=next(n for n in driver_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return [(ast.unparse(c.func),c.lineno) for c in ast.walk(n) if isinstance(c,ast.Call)]
def call_line(calls,name):
    return min(line for func,line in calls if func==name)
def driver_ordering():
    calls=function_calls('execute')
    assert call_line(calls,'source_inputs')<call_line(calls,'qualify_before_clock')
    assert call_line(calls,'qualify_before_clock')<call_line(calls,'H.scan_scope')<call_line(calls,'H.new')
    assert call_line(calls,'H.new')<call_line(calls,'subprocess.Popen')<call_line(calls,'H.wait_owned')
    newcalls=[c for c in ast.walk(next(n for n in driver_tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute'))
              if isinstance(c,ast.Call) and ast.unparse(c.func)=='H.new']
    claim=next(c for c in newcalls if 'ROOT-ONCE-DRIVER-INVOCATION.json' in ast.unparse(c))
    clk=next(c for c in newcalls if 'ROOT-ORIGINAL-OUTER600-CLOCK.json' in ast.unparse(c))
    assert call_line(calls,'qualify_before_clock')<claim.lineno<clk.lineno<call_line(calls,'subprocess.Popen')
    child=function_calls('owned_consumer')
    assert call_line(child,'H.child_limits')<call_line(child,'source_inputs')
    assert call_line(child,'apply_store_write_budget')<call_line(child,'prep.qualify_selected_ordinary_readonly')
    assert call_line(child,'prep.qualify_selected_ordinary_readonly')<call_line(child,'checker.observe')
    assert call_line(child,'checker.fresh')<call_line(child,'checker.compose_preintent_source')<call_line(child,'module.BotAPI')
    assert call_line(child,'module.BotAPI')<call_line(child,'runner.new')<call_line(child,'runner.send')<call_line(child,'runner.observe')
    readonly=function_calls('qualify_before_clock')
    assert not any(f in ('H.new','stamp','time.monotonic','time.time','module.BotAPI','runner.new','runner.save') for f,_ in readonly)
    assert call_line(readonly,'prep.qualify_selected_ordinary_readonly')<call_line(readonly,'checker.observe_readonly')
    return dict(AST_source_only=True,actual_driver_invoked=False,qualifier_before_claim_clock_child=True,
        limits_before_child_source_inputs=True,current209_before_API_new_send=True)
check('driver-source-lifecycle-ordering',driver_ordering)

def driver_no_import_effect():
    d=load(driver_raw,driver_path,'_presentation_driver_inert_control')
    assert d.SHARED_DRIVER['sha256']=='e40343ca212f551d62e842879485f039fbfc6bfb0d9e6777b64776e9eb832ce0'
    return dict(import_inert=True,shared_finite_helper_pin_preserved=True)
check('driver-import-inert-and-shared-pin',driver_no_import_effect)

finished=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat()
disk_bytes=sum(x.stat().st_size for x in BASE.rglob('*') if x.is_file())
assert disk_bytes<100*1024**2
usage=resource.getrusage(resource.RUSAGE_SELF)
pins=dict(parent=reference(PARENT,parent_raw),selected=reference(base_path,base_raw),
    shared=reference(shared_path,shared_raw),candidate=reference(candidate_path,candidate_raw),
    driver=reference(driver_path,driver_raw),
    composed=dict(bytes=len(composed_raw),sha256=sha(composed_raw)))
report=dict(schema='frw.SOL.Task38.presentation-caller-SOURCE-controls.v1',
    scope='SOURCE_SYNTHETIC_ONLY_NOT_RUNTIME_PASS',started_at_moscow=STARTED,finished_at_moscow=finished,
    elapsed_seconds=round(time.monotonic()-START,6),source_pins=pins,
    repeat_because='Parent fixed actual original ACK sender numeric-type acceptance; re-evaluate retained receipt controls and whole-prefix/type dependents on final source. Original FAIL preserved separately.',
    limitations=['Real retained original upload metadata unavailable to this child; no real source authentication claimed.',
        'Synthetic /proc and gateway paths replace only environment inputs; actual original consumer methods execute.',
        'Readonly prefix reads freshness clock; creates no operation clock.',
        'No actual runtime/new/send/model/API/Telegram/Office/native/service/install execution.'],
    resource_limits=dict(cpu_seconds=120,wall_seconds=300,address_space_bytes=512*1024**2,
        per_file_bytes=100*1024**2,aggregate_output_budget_bytes=100*1024**2),
    actual_resources=dict(user_cpu_seconds=usage.ru_utime,system_cpu_seconds=usage.ru_stime,
        max_rss_kib=usage.ru_maxrss,files_bytes=disk_bytes),
    results=RESULTS,defects=DEFECTS,
    counts={k:sum(r['status']==k for r in RESULTS) for k in sorted({r['status'] for r in RESULTS})})
write(BASE/'CHECKS.json',report)
summary=dict(schema='frw.SOL.Task38.caller-controls.RESULT.v1',
    state='SOURCE_CONTROLS_DEFECTS_FOUND' if any(r['status'].startswith(('FAIL','ERROR')) for r in RESULTS) else 'SOURCE_CONTROLS_PASS_SYNTHETIC_ONLY',
    checks=reference(BASE/'CHECKS.json',(BASE/'CHECKS.json').read_bytes()),
    code=reference(Path(__file__),Path(__file__).read_bytes()),source_pins=pins,
    counts=report['counts'],defects=DEFECTS,started_at_moscow=STARTED,finished_at_moscow=finished,
    elapsed_seconds=report['elapsed_seconds'],actual_runtime_PASS=False,real_original_upload_authentication=False)
write(BASE/'RESULT.json',summary)
print(json.dumps(dict(state=summary['state'],counts=summary['counts'],defects=DEFECTS,
    checks=summary['checks'],result=reference(BASE/'RESULT.json',(BASE/'RESULT.json').read_bytes())),sort_keys=True))
sys.exit(1 if any(r['status'].startswith(('FAIL','ERROR')) for r in RESULTS) else 0)
