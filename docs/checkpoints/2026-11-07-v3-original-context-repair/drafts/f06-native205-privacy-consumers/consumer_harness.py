"""Finite isolated REAL native consumers; no gateway/model/client boot."""
import os, sys, pathlib, json, hashlib, importlib, importlib.abc, importlib.util
import resource, time, copy, io, logging, sqlite3, traceback, datetime, signal, contextlib, gc, shutil

ROOT = pathlib.Path(__file__).parent.resolve()
MODE = sys.argv[1]
assert MODE in ('candidate-writer', 'baseline-writer', 'candidate-surface', 'candidate-recovery','candidate-extra','candidate-finalcheck')
STAND = ROOT / 'stands' / (sys.argv[2] if len(sys.argv)>2 else ('candidate-writer' if MODE in ('candidate-recovery','candidate-finalcheck') else ('candidate-surface' if MODE=='candidate-extra' else MODE)))
STAND.mkdir(parents=True, exist_ok=MODE in ('candidate-recovery','candidate-extra','candidate-finalcheck'), mode=0o700)
os.umask(0o077)
for name in ('home','hermes','config','cache','data','tmp'):
    (STAND/name).mkdir(mode=0o700,exist_ok=MODE in ('candidate-recovery','candidate-extra','candidate-finalcheck'))
os.environ.clear()
os.environ.update(HOME=str(STAND/'home'),HERMES_HOME=str(STAND/'hermes'),
    XDG_CONFIG_HOME=str(STAND/'config'),XDG_CACHE_HOME=str(STAND/'cache'),
    XDG_DATA_HOME=str(STAND/'data'),TMPDIR=str(STAND/'tmp'),
    PATH='/usr/bin:/bin',PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',
    OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
os.chdir(STAND)
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
affinity_before=sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0,affinity_before[:2])
signal.alarm(90)
NATIVE=pathlib.Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
VENV=pathlib.Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv')
PM=pathlib.Path(sys.base_prefix).resolve()
five=['agent/agent_runtime_helpers.py','agent/message_sanitization.py','agent/session_persistence.py','hermes_state_messages.py','agent/display.py']
four=['gateway/run_attachment_presentation.py','hermes_cli/friday_prompt_scope.py','hermes_cli/friday_workspace_presentation.py','tools/session_search_tool.py']
variant='baseline' if MODE.startswith('baseline') else 'candidate'
overlays={x[:-3].replace('/','.'):ROOT/variant/x for x in five}
overlays.update({x[:-3].replace('/','.'):ROOT/'source205'/x for x in four})
class Overlay(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in overlays:
            return importlib.util.spec_from_file_location(fullname,overlays[fullname])
sys.meta_path.insert(0,Overlay())
sys.path.insert(0,str(NATIVE))
denials=[]; opened_native=set(); opened_own=set(); sqlite_paths=[]; prohibited=[]
def pathof(value):
    if isinstance(value,(str,bytes,os.PathLike)):
        return pathlib.Path(os.fsdecode(value)).absolute()
    return None
def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork'):
        prohibited.append(event); raise PermissionError('offline_no_process_or_network')
    if event=='sqlite3.connect':
        p=pathof(args[0]); sqlite_paths.append(str(p))
        if p is None or not p.is_relative_to(STAND):
            denials.append({'event':event,'path':str(p)}); raise PermissionError('own_db_only')
    if event!='open': return
    p=pathof(args[0])
    if p is None: return
    mode=args[1]; flags=args[2] if len(args)>2 else 0
    writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
    if writing:
        allowed=p.is_relative_to(STAND)
    else:
        allowed=(p.is_relative_to(ROOT) or p.is_relative_to(VENV) or p.is_relative_to(PM)
            or str(p).startswith(('/usr/','/lib/','/lib64/','/etc/','/proc/','/sys/','/dev/')))
        if p.is_relative_to(NATIVE):
            allowed=(p.suffix in ('.py','.pyc','.so') or p==NATIVE/'install-stamp.json' or
                (p.is_relative_to(NATIVE/'plugins'/'platforms') and p.name=='plugin.yaml'))
            if allowed: opened_native.add(str(p))
    if not allowed:
        denials.append({'event':event,'path':str(p),'writing':writing}); raise PermissionError('isolated_consumer_file_boundary')
    if p.is_relative_to(STAND):opened_own.add(str(p))
sys.addaudithook(audit)

checks=[]; started=time.monotonic(); report={'mode':MODE,'python':sys.version,'pid':os.getpid(),
    'home_env':{k:os.environ[k] for k in ('HOME','HERMES_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','TMPDIR')},
    'affinity_before':affinity_before,'affinity_actual':sorted(os.sched_getaffinity(0)),
    'limits':{'wall_seconds':90,'cpu_seconds':60,'as_bytes':2*1024**3,'fsize_bytes':64*1024**2},'checks':checks}
def check(name, ok, detail=None):
    checks.append({'name':name,'ok':bool(ok),'detail':detail})
    if not ok: raise AssertionError(name)
def fingerprint(path):
    p=pathlib.Path(path); return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def tool(cid,name,args):
    return {'id':cid,'type':'function','function':{'name':name,'arguments':args if isinstance(args,str) else json.dumps(args)}}

# Synthetic-only values, never read from original credential inputs or product user data.
READ='isolated-f06-read-6b21e4'; WRITE='isolated-f06-write-b85f02'; CHAT='allowed-private-original-9c143a'
DOC='ordinary-document-password-a001d7'; OTHER='ordinary-nonfile-password-c07152'
calls=[
 tool('read-call','read_file',{'path':'received/input.docx','password':READ,'offset':0,'limit':20}),
 tool('ooxml-call','write_file',{'path':'output/result.docx','format':'ooxml_password_edit','content':json.dumps({'source_path':'received/input.docx','password':WRITE,'edits':[{'find':'old','replace':'new'}]})}),
 tool('odf-call','write_file',{'path':'output/result.odt','format':'odf_password_edit','content':json.dumps({'source_path':'received/input.odt','Password':WRITE,'edits':[{'find':'old','replace':'new'}]})}),
 tool('ordinary-json','write_file',{'path':'output/data.json','format':'json','content':json.dumps({'password':DOC,'description':'ordinary document content'})}),
 tool('ordinary-tool','custom_tool',{'password':OTHER,'parameter':42}),
]
BASE_TIME=1730333333.125
messages=[{'role':'user','content':'Intentional original private input '+CHAT,'timestamp':BASE_TIME,'platform_message_id':'own-user-10'},
    {'role':'assistant','content':'Proceed with own fixture.','tool_calls':calls,'timestamp':BASE_TIME+1,'finish_reason':'tool_calls','token_count':37,'reasoning':'fixture reasoning retained'},
    *[{'role':'tool','name':c['function']['name'],'tool_call_id':c['id'],'content':'fixture result '+str(i),'timestamp':BASE_TIME+2+i} for i,c in enumerate(calls)],
    {'role':'assistant','content':'Complete.','timestamp':BASE_TIME+20,'token_count':3,'finish_reason':'stop'}]

def validate_calls(serialized, redacted, label):
    text=json.dumps(serialized)
    check(label+'.structured_credentials', (READ not in text and WRITE not in text) if redacted else (READ in text and WRITE in text))
    check(label+'.ordinary_document_retained',DOC in text)
    check(label+'.nonfile_retained',OTHER in text)
    data=json.loads(serialized) if isinstance(serialized,str) else serialized
    check(label+'.call_ids',[x['id'] for x in data]==[x['id'] for x in calls])
    check(label+'.read_other_fields', {k:v for k,v in json.loads(data[0]['function']['arguments']).items() if k!='password'}=={'path':'received/input.docx','offset':0,'limit':20})

try:
    # Import real modules with exact candidate/205 overlays, no sys.modules mock consumers.
    hs=importlib.import_module('hermes_state')
    persistence=importlib.import_module('agent.session_persistence')
    helpers=importlib.import_module('agent.agent_runtime_helpers')
    display=importlib.import_module('agent.display')
    sanitization=importlib.import_module('agent.message_sanitization')
    for name in overlays:importlib.import_module(name)
    for name,path in overlays.items():
        check('loaded_origin.'+name,pathlib.Path(sys.modules[name].__file__).resolve()==path.resolve())
    check('hermes_home_resolved',hs.get_hermes_home().resolve()==(STAND/'hermes').resolve())
    report['entrypoints']=[]
    if MODE=='candidate-finalcheck':
        # Independent missing fallback seam after native run_agent import refusal; no repeated import/admission attempt.
        agent=type('Agent',(),{})(); projected=persistence._db_flush_row(agent,copy.deepcopy(messages[1]),False)
        output=hs.divert_session_transcript_jsonl('own-divert',[projected])
        durable=json.loads(output.read_text());validate_calls(durable['tool_calls'],True,'divert')
        check('divert.other_fields',durable['timestamp']==messages[1]['timestamp'] and durable['content']==messages[1]['content'] and durable['reasoning']==messages[1]['reasoning'])
        db=hs.SessionDB(STAND/'hermes/state.db')
        try:
            db.create_session('malformed-projections','cli')
            malformed=[
                tool('badread','read_file','{"password":"'+READ+'",'),
                tool('duplicate','read_file','{"password":"'+READ+'","password":"'+WRITE+'"}'),
                tool('escaped','read_file','{"pass\\u0077ord":"'+READ+'","path":"received/own.docx"}'),
                tool('dict','write_file',{'format':'ooxml_password_edit','content':{'Password':WRITE,'edits':[]}}),
                tool('badcontent','write_file',{'format':'odf_password_edit','content':'{"password":"'+WRITE+'",'}),
                tool('nonobject','write_file',{'format':'ooxml_password_edit','content':['invalid',WRITE]}),
            ]
            original=copy.deepcopy(malformed)
            rowid=db.append_message('malformed-projections','assistant','fixture malformed envelope',tool_calls=malformed,timestamp=BASE_TIME+300)
            with contextlib.closing(sqlite3.connect(db.db_path)) as raw:
                raw.row_factory=sqlite3.Row; row=dict(raw.execute('SELECT * FROM messages WHERE id=?',(rowid,)).fetchone())
            check('malformed.actual_db_no_credential',READ not in row['tool_calls'] and WRITE not in row['tool_calls'])
            check('malformed.envelope_ids_and_timestamp',[x['id'] for x in json.loads(row['tool_calls'])]==[x['id'] for x in malformed] and row['timestamp']==BASE_TIME+300)
            check('malformed.execution_unchanged',malformed==original)
            # Native unaddressed CAS: stale loaded caller must adopt the concurrent winner.
            from agent.context_compressor import _DB_PERSISTED_MARKER
            from agent.message_metadata import DB_ROW_SNAPSHOT,MESSAGE_UID
            stale=db.get_messages_as_conversation('mixin-session',repair_alternation=True)
            stale_assistant=next(x for x in stale if x.get('tool_calls'))
            winner=copy.deepcopy(stale_assistant);winner.pop(_DB_PERSISTED_MARKER,None);winner['content']='Concurrent own winner.'
            db.append_messages_batch('mixin-session',[winner])
            stale_assistant.pop(_DB_PERSISTED_MARKER,None);stale_assistant['content']='Stale loser must not overwrite.'
            class Agent(persistence.SessionPersistenceMixin):pass
            a=Agent();a._session_db=db;a.session_id='mixin-session';a._session_db_created=True
            check('cas.stale_flush_safely_adopted',a._flush_messages_to_session_db(stale) is True)
            with contextlib.closing(sqlite3.connect(db.db_path)) as raw:
                raw.row_factory=sqlite3.Row
                row=dict(raw.execute("SELECT * FROM messages WHERE session_id='mixin-session' AND tool_calls IS NOT NULL").fetchone())
                n=raw.execute("SELECT count(*) FROM messages WHERE session_id='mixin-session'").fetchone()[0]
            check('cas.winner_not_overwritten_no_duplicate',row['content']=='Concurrent own winner.' and n==len(messages))
            check('cas.identity_fields_and_times_retained',row['id']==12 and row['timestamp']==BASE_TIME+1 and row['token_count']==37 and row['finish_reason']=='tool_calls' and row['reasoning']=='fixture reasoning retained')
            check('cas.stale_live_adopted_winner',stale_assistant['content']=='Concurrent own winner.')
            validate_calls(row['tool_calls'],True,'cas.winner')
            report['entrypoints']=['actual _db_flush_row -> hermes_state.divert_session_transcript_jsonl direct projected-row seam',
                'actual append_message malformed/duplicate/escaped/protected dict/nonobject -> own SQLite',
                'actual native loaded digest -> concurrent append_messages_batch row repair -> stale mixin CAS adoption']
        finally:db.close()
        report['divert_jsonl']=fingerprint(output)
    elif MODE=='candidate-extra':
        # The untouched native AIAgent class supplies the sanitizer's constants/id helper.
        # No AIAgent instance, GatewayRunner, model client or worker is constructed.
        import run_agent
        logstream=io.StringIO(); logger=logging.getLogger('isolated.runtime.repair');handler=logging.StreamHandler(logstream);logger.addHandler(handler)
        bad=[{'role':'assistant','tool_calls':[tool('corrupt-read','read_file','{"password":"'+READ+'",'),
            tool('corrupt-write','write_file','{"content":"'+WRITE+'",')]}]
        repaired=helpers.sanitize_tool_call_arguments(bad,logger=logger,session_id='own-corruption')
        logger.removeHandler(handler);logs=logstream.getvalue();(STAND/'runtime-repair.log').write_text(logs)
        check('runtime_repair.actual_warn_path',repaired==2 and 'Corrupted tool_call arguments repaired before request' in logs)
        check('runtime_repair.no_secret',READ not in logs and WRITE not in logs and '[redacted file-tool arguments]' in logs)
        check('runtime_repair.execution_json_repaired',all(x['function']['arguments']=='{}' for x in bad[0]['tool_calls']))
        # Same actual row projection consumed by real fallback JSONL writer. Not a forced corruption run.
        agent=type('Agent',(),{})(); projected=persistence._db_flush_row(agent,copy.deepcopy(messages[1]),False)
        output=hs.divert_session_transcript_jsonl('own-divert',[projected])
        durable=json.loads(output.read_text());validate_calls(durable['tool_calls'],True,'divert')
        check('divert.other_fields',durable['timestamp']==messages[1]['timestamp'] and durable['content']==messages[1]['content'] and durable['reasoning']==messages[1]['reasoning'])
        report['entrypoints']=['Actual agent.agent_runtime_helpers.sanitize_tool_call_arguments using real run_agent.AIAgent constants/static ID helper; no instance',
            'actual _db_flush_row -> hermes_state.divert_session_transcript_jsonl; no artificial currentDB corruption']
        report['divert_jsonl']=fingerprint(output);report['runtime_log']=fingerprint(STAND/'runtime-repair.log')
    elif MODE=='candidate-recovery':
        # Reassess the retained original own DB; do not repeat its completed writer effects.
        db=hs.SessionDB(STAND/'hermes'/'state.db')
        try:
            with contextlib.closing(sqlite3.connect(db.db_path)) as raw:
                raw.row_factory=sqlite3.Row
                oldrows=[dict(x) for x in raw.execute('SELECT * FROM messages ORDER BY id')]
            check('recovery.original_session_counts',len(oldrows)==18)
            for sid in ('append-single','batch-session','mixin-session'):
                rs=[x for x in oldrows if x['session_id']==sid]
                validate_calls(rs[1]['tool_calls'],True,'retained.'+sid)
                check('retained.timestamps.'+sid,[x['timestamp'] for x in rs]==[x['timestamp'] for x in (messages[:2] if sid=='append-single' else messages)])
                check('retained.original_user.'+sid,rs[0]['content']==messages[0]['content'])
            class Agent(persistence.SessionPersistenceMixin):pass
            a=Agent();a._session_db=db;a.session_id='mixin-session';a._session_db_created=True
            live=db.get_messages_as_conversation(a.session_id,repair_alternation=True)
            from agent.context_compressor import _DB_PERSISTED_MARKER
            from agent.message_metadata import DB_ROW_SNAPSHOT
            assistant=next(x for x in live if x.get('tool_calls'))
            rid=next(x['id'] for x in oldrows if x['session_id']==a.session_id and x['role']=='assistant' and x['tool_calls'])
            uid=assistant.get('message_uid'); snap=assistant[DB_ROW_SNAPSHOT]
            assistant['tool_calls']=copy.deepcopy(calls) # live execution uses raw args; persisted projection must match
            assistant.pop(_DB_PERSISTED_MARKER,None)
            assistant['content']='Changed nonsecret owned-row content.'
            check('reflush.addressed_success',a._flush_messages_to_session_db(live) is True)
            with contextlib.closing(sqlite3.connect(db.db_path)) as raw:
                raw.row_factory=sqlite3.Row; changed=dict(raw.execute('SELECT * FROM messages WHERE id=?',(rid,)).fetchone())
                count=raw.execute("SELECT count(*) FROM messages WHERE session_id='mixin-session'").fetchone()[0]
            check('reflush.same_row_no_duplicate',count==len(messages) and changed['content']==assistant['content'] and assistant['_row_id']==rid)
            check('reflush.snapshot_changes',assistant[DB_ROW_SNAPSHOT]!=snap)
            check('reflush.timestamp_preserved',changed['timestamp']==BASE_TIME+1)
            check('reflush.live_raw_args',assistant['tool_calls']==calls)
            validate_calls(changed['tool_calls'],True,'reflush')
            # Raw native203 baseline writer output -> candidate consumer, on a COPY of own fixture only.
            src=ROOT/'stands/baseline-writer/hermes/state.db'; dst=STAND/'hermes/legacy-own-copy.db'
            check('legacy.copy_source_exists',src.is_file() and not dst.exists())
            shutil.copyfile(src,dst)
            legacy=hs.SessionDB(dst)
            try:
                handoff=copy.deepcopy(messages)
                for msg in handoff:msg.pop('timestamp',None)
                legacy.publish_compression_child(parent_session_id='batch-session',child_session_id='carried-child',source='cli',messages=handoff,require_compression_lease=False)
                with contextlib.closing(sqlite3.connect(dst)) as raw:
                    raw.row_factory=sqlite3.Row
                    parent=[dict(x) for x in raw.execute("SELECT * FROM messages WHERE session_id='batch-session' ORDER BY id")]
                    child=[dict(x) for x in raw.execute("SELECT * FROM messages WHERE session_id='carried-child' ORDER BY id")]
                check('carry.raw_legacy_not_scrubbed',READ in parent[1]['tool_calls'] and WRITE in parent[1]['tool_calls'])
                validate_calls(child[1]['tool_calls'],True,'carry.child')
                check('carry.parent_timestamps',[x['timestamp'] for x in parent]==[x['timestamp'] for x in child])
                displayrows=legacy.get_messages('carried-child',include_ancestors=True,include_compacted=True)
                check('carry.real_display_deduped_normal_ids',len(displayrows)==len(messages),{'got':len(displayrows),'expected':len(messages)})
                report['legacy_copy']={'source':fingerprint(src),'new_db':str(dst),'parent_ids':[x['id'] for x in parent],'child_ids':[x['id'] for x in child]}
            finally:legacy.close()
            # Repeated donors, explicit timestamp and no-match: actual native carry method on own DB.
            db.create_session('timestamp-controls','cli')
            repeat={'role':'assistant','content':'repeat','tool_calls':copy.deepcopy(calls)}
            db.append_messages_batch('timestamp-controls',[dict(repeat,timestamp=BASE_TIME+100),dict(repeat,timestamp=BASE_TIME+101)])
            handoff=[copy.deepcopy(repeat),copy.deepcopy(repeat),dict(repeat,timestamp=BASE_TIME+200),dict(repeat,content='unmatched')]
            db.publish_compression_child(parent_session_id='timestamp-controls',child_session_id='timestamp-child',source='cli',messages=handoff,require_compression_lease=False)
            check('carry.distinct_repeated_donors',handoff[0]['timestamp']==BASE_TIME+100 and handoff[1]['timestamp']==BASE_TIME+101)
            check('carry.explicit_timestamp_preserved',handoff[2]['timestamp']==BASE_TIME+200)
            check('carry.no_match_uses_fresh_insert_time',handoff[3]['timestamp']>BASE_TIME+200)
            report['entrypoints']=['Retained own original candidate DB readback','SessionPersistenceMixin row-addressed reflush -> real CAS/transcript repair',
                'actual baseline203 ownDB copy -> candidate publish_compression_child -> _carry_parent_timestamps -> real get_messages(include_ancestors=True,include_compacted=True)']
        finally:db.close()
        report['db']=fingerprint(STAND/'hermes/state.db')
    elif MODE.endswith('writer'):
        db=hs.SessionDB(STAND/'hermes'/'state.db')
        try:
            db.create_session('append-single','cli')
            original=copy.deepcopy(calls)
            db.append_message('append-single','user',messages[0]['content'],timestamp=BASE_TIME,platform_message_id='own-user-10')
            rid=db.append_message('append-single','assistant',messages[1]['content'],tool_calls=calls,timestamp=BASE_TIME+1,
                finish_reason='tool_calls',token_count=37,reasoning='fixture reasoning retained')
            check('append.live_execution_args_unchanged',calls==original)
            with contextlib.closing(sqlite3.connect(STAND/'hermes'/'state.db')) as raw:
                raw.row_factory=sqlite3.Row
                row=dict(raw.execute('SELECT * FROM messages WHERE id=?',(rid,)).fetchone())
                user=dict(raw.execute("SELECT * FROM messages WHERE session_id='append-single' AND role='user'").fetchone())
            validate_calls(row['tool_calls'],variant=='candidate','append')
            check('append.timestamps_fields',row['timestamp']==BASE_TIME+1 and row['token_count']==37 and row['finish_reason']=='tool_calls' and row['reasoning']=='fixture reasoning retained')
            check('append.allowed_original_chat',user['content']==messages[0]['content'] and CHAT in user['content'] and user['timestamp']==BASE_TIME and user['platform_message_id']=='own-user-10')
            report['entrypoints'].append('SessionDB.append_message -> SessionMessagesMixin._message_row_params -> actual SQLite messages/tool_calls')
            db.create_session('batch-session','cli')
            batch=copy.deepcopy(messages); batch_original=copy.deepcopy(batch)
            inserted=db.append_messages_batch('batch-session',batch)
            check('batch.insert_count',inserted==len(messages))
            check('batch.live_execution_args_unchanged',batch[1]['tool_calls']==batch_original[1]['tool_calls'])
            with contextlib.closing(sqlite3.connect(STAND/'hermes'/'state.db')) as raw:
                raw.row_factory=sqlite3.Row
                rows=[dict(x) for x in raw.execute("SELECT * FROM messages WHERE session_id='batch-session' ORDER BY id")]
            validate_calls(rows[1]['tool_calls'],variant=='candidate','batch')
            check('batch.all_timestamps',[x['timestamp'] for x in rows]==[x['timestamp'] for x in messages])
            # Same raw live prefix must compare equal to its projected persisted form, not archive/reinsert.
            before=[(x['id'],x['message_uid'],x['timestamp'],x['tool_call_uid'],x['tool_call_uids']) for x in rows]
            db.replace_messages('batch-session',copy.deepcopy(messages),archive_dropped=True)
            with contextlib.closing(sqlite3.connect(STAND/'hermes'/'state.db')) as raw:
                raw.row_factory=sqlite3.Row
                after=[dict(x) for x in raw.execute("SELECT * FROM messages WHERE session_id='batch-session' ORDER BY id")]
            check('replace.projected_identity_prefix_kept',len(after)==len(rows) and all(x['active']==1 for x in after)
                and before==[(x['id'],x['message_uid'],x['timestamp'],x['tool_call_uid'],x['tool_call_uids']) for x in after])
            report['entrypoints'].append('SessionDB.append_messages_batch + replace_messages(archive_dropped=True): native transcript repair, projection, durable identity')
            # Direct real persistence mixin -> real guard and batch writer; no projection/DB consumer mocks.
            class Agent(persistence.SessionPersistenceMixin):pass
            a=Agent(); a._session_db=db; a.session_id='mixin-session'; a._session_db_created=True
            db.create_session(a.session_id,'cli')
            live=copy.deepcopy(messages)
            check('mixin.first_flush',a._flush_messages_to_session_db(live) is True)
            check('mixin.second_flush',a._flush_messages_to_session_db(live) is True)
            with contextlib.closing(sqlite3.connect(STAND/'hermes'/'state.db')) as raw:
                raw.row_factory=sqlite3.Row
                mixinrows=[dict(x) for x in raw.execute("SELECT * FROM messages WHERE session_id='mixin-session' ORDER BY id")]
            check('mixin.no_duplicate_rows',len(mixinrows)==len(messages))
            validate_calls(mixinrows[1]['tool_calls'],variant=='candidate','mixin')
            check('mixin.timestamps',[x['timestamp'] for x in mixinrows]==[x['timestamp'] for x in messages])
            check('mixin.live_args_unchanged',live[1]['tool_calls']==calls)
            report['entrypoints'].append('SessionPersistenceMixin._flush_messages_to_session_db -> _db_flush_collect/_db_flush_row -> guard_generated_rows -> append_messages_batch')
            report['sqlite_receipts']={'append_row':{k:v for k,v in row.items() if k not in ('tool_calls','content')},
                'batch_row_ids':[x['id'] for x in rows], 'mixin_row_ids':[x['id'] for x in mixinrows],
                'sessions':3,'messages':2+len(rows)+len(mixinrows)}
        finally:db.close()
        check('db.closed',db._conn is None)
        report['db']=fingerprint(STAND/'hermes'/'state.db')
    else:
        # Real converter and locked append-to-file writer; only tool schema context is synthetic empty.
        class Agent(persistence.SessionPersistenceMixin):
            def _format_tools_for_system_message(self):return ''
        a=Agent(); a.model='isolated-no-model-executed'; a.save_trajectories=True
        trajectory_live=copy.deepcopy(messages)
        a._save_trajectory(trajectory_live,messages[0]['content'],True)
        out=STAND/'trajectory_samples.jsonl'; data=json.loads(out.read_text())
        tool_text='\n'.join(x['value'] for x in data['conversations'] if x['from']=='gpt' and '<tool_call>' in x['value'])
        check('trajectory.structured_credentials_removed',READ not in tool_text and WRITE not in tool_text)
        check('trajectory.allowed_original_chat',any(CHAT in x['value'] for x in data['conversations'] if x['from']=='human'))
        check('trajectory.ordinary_document_nonfile_retained',DOC in tool_text and OTHER in tool_text)
        check('trajectory.execution_args_unchanged',trajectory_live==messages)
        check('trajectory.metadata_and_timestamp',data['model']==a.model and data['completed'] is True and isinstance(data['timestamp'],str))
        previews=[]
        for form in ('ooxml_password_edit','odf_password_edit'):
            for content in (json.dumps({'Password':WRITE,'edits':[]}),'{"pass\\u0077ord":"'+WRITE+'",',json.dumps({'Password':WRITE})[:-1],['invalid',WRITE]):
                args={'path':WRITE+'-echo.docx','format':' '+form.upper()+' ','content':content}
                original=copy.deepcopy(args)
                public=display.redact_tool_args_for_display('write_file',args)
                preview=display.prepare_tool_preview('write_file',args,fallback='own fixture',max_len=300)
                check('display.protected.'+str(len(previews)),WRITE not in json.dumps(public) and WRITE not in preview.text)
                check('display.execution_unchanged.'+str(len(previews)),args==original)
                previews.append({'public':public,'preview':preview.text})
        logstream=io.StringIO(); handler=logging.StreamHandler(logstream)
        logging.getLogger('agent.message_sanitization').addHandler(handler)
        malformed_cases=[('{"pass\\u0077ord":"'+READ+'",}', 'read_file'),('{"password":"'+WRITE+'",','write_file')]
        for value,name in malformed_cases:sanitization._repair_tool_call_arguments(value,name)
        logging.getLogger('agent.message_sanitization').removeHandler(handler)
        logs=logstream.getvalue(); (STAND/'repair.log').write_text(logs)
        check('repair.logs_exist',bool(logs))
        check('repair.no_raw_password_args',READ not in logs and WRITE not in logs and '[redacted file-tool arguments]' in logs)
        check('repair.nonfile_not_blanket_redacted',sanitization._repair_tool_call_arguments('{"other":"'+OTHER+'",}','custom_tool')=='{"other":"'+OTHER+'"}')
        report['entrypoints']+=['SessionPersistenceMixin._save_trajectory -> convert_to_trajectory_format -> agent.trajectory.save_trajectory (actual locked own JSONL append)',
            'agent.display.redact_tool_args_for_display + prepare_tool_preview','agent.message_sanitization._repair_tool_call_arguments actual WARNING capture']
        report['trajectory']=fingerprint(out); report['repair_log']=fingerprint(STAND/'repair.log'); report['previews']=previews
    check('audit.no_denied_or_prohibited_events',not denials and not prohibited,{'denials':denials,'prohibited':prohibited})
    gc.collect()
    report['state']='PASS_SCOPED_NATIVE_CONSUMERS' if variant=='candidate' else 'BASELINE_TECHNICAL_DUPLICATE_REPRODUCED'
except BaseException as e:
    report['state']='FAIL'; report['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
    report['elapsed_seconds']=time.monotonic()-started
    report['audit']={'denials':denials,'prohibited_events':prohibited,'sqlite_paths':sorted(set(sqlite_paths)),
        'opened_native_code':sorted(opened_native),'opened_own':sorted(opened_own),
        'limit':'Python audit observations only, not OS confinement or global read absence proof.'}
    report['loaded_overlay']={name:fingerprint(sys.modules[name].__file__) for name in overlays if name in sys.modules}
    report['loaded_native_python']={name:fingerprint(mod.__file__) for name,mod in tuple(sys.modules.items())
        if getattr(mod,'__file__',None) and pathlib.Path(mod.__file__).is_relative_to(NATIVE) and str(mod.__file__).endswith('.py')}
    report['stand_bytes']=sum(p.stat().st_size for p in STAND.rglob('*') if p.is_file())
    report['remaining_own_db_fds']=[os.readlink('/proc/self/fd/'+f) for f in os.listdir('/proc/self/fd')
        if os.path.exists('/proc/self/fd/'+f) and str(STAND/'hermes'/'state.db') in os.readlink('/proc/self/fd/'+f)]
    (STAND/('REPORT-extra.json' if MODE=='candidate-extra' else ('REPORT-finalcheck.json' if MODE=='candidate-finalcheck' else 'REPORT.json'))).write_text(json.dumps(report,indent=2,default=lambda x:{'bytes_hex':x.hex()} if isinstance(x,bytes) else str(x))+'\n')
    print(json.dumps({'mode':MODE,'state':report['state'],'checks':len(checks),'denials':len(denials),
        'error':report.get('error'),'elapsed_seconds':report['elapsed_seconds']}))
    signal.alarm(0)
sys.exit(0 if report['state']!='FAIL' else 2)
