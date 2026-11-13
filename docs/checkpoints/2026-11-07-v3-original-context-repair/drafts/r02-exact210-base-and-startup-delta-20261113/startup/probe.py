"""Source-only connected startup-sweep failure probe on own SQLite and sessions.

The complete actual startup finish/claim/boot/scheduler/resume-dispatch and Base
ledger/send/finalize functions execute. Session persistence, model generation,
adapter acceptance, config, loop guard and peripheral service wiring are declared
synthetic seams; there are no installed imports or remote effects.
"""
from __future__ import annotations
import asyncio, contextlib, datetime, hashlib, importlib.util, json, logging, os
from pathlib import Path
import resource, shutil, signal, sqlite3, sys, threading, time, types
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent
os.umask(0o077)
for key, value in ((resource.RLIMIT_CPU, 90), (resource.RLIMIT_AS, 512*1024**2),
                   (resource.RLIMIT_FSIZE, 50*1024**2), (resource.RLIMIT_CORE, 0)):
    resource.setrlimit(key, (value, value))
signal.alarm(180)
logging.disable(logging.CRITICAL)

def audit(event, args):
    if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo',
                 'subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn'}:
        raise RuntimeError('forbidden external effect: '+event)
    if event == 'sqlite3.connect' and args[0] != ':memory:':
        if not Path(args[0]).resolve().is_relative_to(ROOT):
            raise RuntimeError('external SQLite forbidden')
    if event == 'open':
        name, mode, flags = args
        write = ((isinstance(mode,str) and any(c in mode for c in 'wax+'))
                 or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if write and not isinstance(name,int) and not Path(name).resolve().is_relative_to(ROOT):
            raise RuntimeError('external write forbidden')
sys.addaudithook(audit)

spec = importlib.util.spec_from_file_location('own_source_helpers', ROOT/'source_helpers.py')
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name]=p
spec.loader.exec_module(p)

EXTRA = ['_await_startup_boot_sends', '_start_finish_wiring', '_run_startup_resume_event',
         '_resume_pending_candidates']

async def scenario(variant, name):
    home=ROOT/'own-data'/(variant+'-'+name)
    home.mkdir(mode=0o700,parents=True)
    L, Base, Start, status, Result, Platform, pins = p.install(home, ROOT/variant)
    code, extra_pins=p.select(ROOT/variant,'gateway/run_startup.py','GatewayStartupMixin',EXTRA)
    ns=Start._claim_pending_obligations.__globals__
    exec(code,ns)
    Extra=ns['GatewayStartupMixin']
    for method in EXTRA: setattr(Start,method,getattr(Extra,method))
    ns.update({'MessageEvent':lambda **kw:NS(**kw), 'MessageType':NS(TEXT='text')})
    runmod=types.ModuleType('gateway.run')
    runmod._AGENT_PENDING_SENTINEL=object()
    runmod._auto_continue_freshness_window=lambda:300
    runmod._is_fresh_gateway_interruption=lambda marker,**kw:True
    runmod._startup_restore_drain_timeout_secs=lambda:0
    runmod._planned_restart_notification_pending=lambda:False
    runmod._restart_notification_pending=lambda:False
    sys.modules[runmod.__name__]=runmod
    guard=types.ModuleType('gateway.restart_loop_guard')
    guard.check_and_record=lambda *a,**kw:False
    sys.modules[guard.__name__]=guard
    sys.modules['gateway'].restart_loop_guard=guard

    effects=[]; generation=[]; clears=[]; tasks=[]; states={}
    key='own:telegram:answered'
    body='OWN already answered ordinary Telegram final'
    def entry(k, platform=Platform.TELEGRAM, resume=True):
        return NS(session_key=k,session_id='session-'+k,transport_profile='owned-test',
                  last_resume_marked_at=100.0,updated_at=101.0,active_turn_token=None,
                  active_turn_started_at=None,resume_pending=resume,suspended=False,
                  resume_reason='gateway_restart',origin=NS(platform=platform,chat_id='90001',thread_id=None,own_session_key=k))
    entries={key:entry(key)}
    class Store:
        async def clear_resume_pending(self,k):
            clears.append(k); entries[k].resume_pending=False
    class Transport(Base):
        name='own-synthetic-transport';_owner_profile='owned-test';_send_path_degraded=False
        _session_tasks={}; initial=True
        def _send_retry_is_final(self,r):return True
        async def send(self,**kw):
            effects.append({'platform':(kw.get('metadata') or {}).get('platform','telegram'),
                            'content':kw['content'],'chat_id':kw['chat_id']})
            return Result(success=True,message_id=None if self.initial else str(len(effects)))
        async def handle_message(self,event):
            generation.append({'platform':event.source.platform.value,'session':event.source.own_session_key})
            # Provider seam deterministically returns the SAME body. The real Base
            # caller derives a different OID for the synthetic resume event.
            result,_=await Caller().send_final_ledgered(event,event.source.own_session_key,body,
                       {'platform':event.source.platform.value},reply_to=None)
            assert result.success, result.error
    transport=Transport()
    class Caller(Base):
        gateway_runner=None;typed_command_prefix='!'
        def _final_delivery_adapter(self,s):return transport
        async def _release_turn_marker(self,event):return None
    class Runner(Start):
        _AUTO_RESUME_REASONS={'gateway_restart'}
        _restart_requested=False;_draining=False;_shutdown_event=NS(is_set=lambda:False)
        adapters={Platform.TELEGRAM:transport};_profile_adapters={'owned-test':{Platform.TELEGRAM:transport}}
        session_store=NS(_lock=threading.RLock(),_ensure_loaded_locked=lambda:None,_entries=entries)
        async_session_store=Store()
        def _restart_loop_guard_config(self):return 4,300,300
        def _is_session_running(self,k):return k in states and states[k].turn.agent is not None
        def _restored_source(self,e):return e.origin
        def _delivery_adapter_for(self,s):return transport
        def _resume_owner_authorized(self,*a):return True
        def _session_state(self,k):return states.setdefault(k,NS(turn=NS(agent=None,started_ts=None)))
        def _peek_session_state(self,k):return states.get(k)
        def _release_running_agent_state(self,k):states[k].turn.agent=None
        def _persist_active_agents(self):pass
        def _retain_background_task(self,t):tasks.append(t);return t
        def _track_task_in(self,bucket,t):bucket.add(t);return t
        def _late_failure_callback(self,message):return lambda task:None
        def _authorization_adapter(self,platform,profile):return transport
        async def _run_owned_startup_cleanup(self,work,*a):return await work
        async def _arm_flood_timers_for_waiting_rows(self):pass
        async def _send_restart_notification(self):pass
        async def _start_post_connect_services(self,count):pass
        async def _finish_startup_restore(self):
            await asyncio.gather(*tasks)
            self._draining=True  # finite seam after complete affected startup flow
    runner=Runner()
    initial_event=NS(text='Own nonsensitive ordinary request',message_id='70001',source=entries[key].origin)
    if name in {'pending', 'pending_open_failure', 'proved_unsent', 'unrelated_unanswered', 'ledger_disabled'}:
        if name in {'pending','pending_open_failure','proved_unsent'}:
            oid=L.compute_obligation_id(key,'70001',body)
            L.record_obligation(obligation_id=oid,session_key=key,platform='telegram',chat_id='90001',
                                thread_id=None,content=body,adapter_profile='owned-test')
            if name=='proved_unsent':
                assert L.mark_attempting(oid)
                L.mark_failed(oid,'send_path_degraded',no_effect=True)
    else:
        if name=='terminal':transport.initial=False
        first,_=await Caller().send_final_ledgered(initial_event,key,body,{},reply_to=None)
        assert first.success == (name=='terminal')
        assert len(effects)==1
    transport.initial=False
    with L._transaction() as connection:
        connection.execute('UPDATE delivery_obligations SET owner_pid=NULL,owner_started_at=NULL')
    before=p.rows(L)
    if name=='terminal':entries[key].resume_pending=False
    if name=='unrelated':
        entries['own:slack:unanswered']=entry('own:slack:unanswered',Platform.SLACK)
    fault_calls=[]
    if name in {'open_failure','open_failure_recovered','unrelated','pending_open_failure','explicit_off_after_fault'}:
        original=L._connect
        def one_shot_open_failure():
            fault_calls.append('connect')
            if len(fault_calls)==1:raise sqlite3.OperationalError('own injected startup open failure')
            return original()
        L._connect=one_shot_open_failure
    if name=='commit_failure':
        original=L._transaction
        @contextlib.contextmanager
        def one_shot_commit_failure():
            fault_calls.append('transaction')
            with original() as connection:
                yield connection
                if len(fault_calls)==1:
                    raise sqlite3.OperationalError('own injected startup transaction exit failure')
        L._transaction=one_shot_commit_failure
    if name=='ledger_disabled':
        sys.modules['hermes_cli.config'].load_config=lambda:{'gateway':{'delivery_ledger':False}}
    await runner._start_finish_wiring(0)
    after_start=p.rows(L)
    flags_after_start={k:e.resume_pending for k,e in entries.items()}
    initial_generations=list(generation)
    direct=None; recovered=None; explicit_off=None; reconnect_scheduled=None
    if variant=='after' and name in {'open_failure','commit_failure','pending_open_failure'}:
        reconnect_scheduled=runner._schedule_resume_pending_sessions(Platform.TELEGRAM)
        assert reconnect_scheduled==0
    if name=='unrelated':
        # An independent ordinary Telegram inbound final still works while only
        # automatic Telegram resume is withheld after the failed sweep.
        e=NS(text='Own new independent request',message_id='70002',source=entries[key].origin)
        r,_=await Caller().send_final_ledgered(e,'own:telegram:new','OWN independent new final',{},reply_to=None)
        direct=r.success
    if name=='open_failure_recovered':
        runner._draining=False
        rows=await runner._claim_pending_obligations()
        entries['own:telegram:independent']=entry('own:telegram:independent')
        resumed=runner._schedule_resume_pending_sessions()
        await asyncio.gather(*tasks)
        recovered={'claimed':len(rows),'scheduled':resumed,
                   'fence_failed':getattr(runner,'_delivery_resume_recovery_failed',False)}
    if name=='explicit_off_after_fault':
        sys.modules['hermes_cli.config'].load_config=lambda:{'gateway':{'delivery_ledger':False}}
        assert await runner._claim_pending_obligations()==[]
        explicit_off={'fence_failed':getattr(runner,'_delivery_resume_recovery_failed',False)}
        if variant=='after':
            explicit_off['scheduled']=runner._schedule_resume_pending_sessions(Platform.TELEGRAM)
    after=p.rows(L)
    with L._transaction() as connection:
        db={'journal_mode':connection.execute('pragma journal_mode').fetchone()[0],
            'integrity':connection.execute('pragma integrity_check').fetchone()[0]}
    result={'variant':variant,'scenario':name,'before':before,'after_start':after_start,'after':after,
            'effects':effects,'startup_generations':initial_generations,'all_generations':generation,
            'clears':clears,'fault_calls':len(fault_calls),'ordinary_new_final_success':direct,
            'recovery':recovered,'explicit_off_after_fault':explicit_off,
            'reconnect_scheduled':reconnect_scheduled,'session_flags_after_start':flags_after_start,
            'session_flags_final':{k:e.resume_pending for k,e in entries.items()},
            'fence_failed':getattr(runner,'_delivery_resume_recovery_failed',False),
            'db':db,'executed_ast':dict(pins['startup_AST'],**extra_pins),'base_ast':pins['base_AST']}
    shutil.rmtree(home)
    result['own_db_removed']=not home.exists()
    return result

def main():
    started=time.monotonic()
    variant=sys.argv[1]
    names=(['open_failure','commit_failure','healthy_uncertain','pending','pending_open_failure',
            'proved_unsent','terminal','unrelated_unanswered','ledger_disabled','unrelated',
            'open_failure_recovered','explicit_off_after_fault'])
    output=[]
    for name in names:
        output.append(asyncio.run(scenario(variant,name)))
    usage=resource.getrusage(resource.RUSAGE_SELF)
    result={'variant':variant,'scenarios':output,
            'wall_s':time.monotonic()-started,'cpu_s':usage.ru_utime+usage.ru_stime,
            'rss_kib':usage.ru_maxrss,'completed_moscow':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
            'source_sha256':hashlib.sha256((ROOT/variant/'gateway/run_startup.py').read_bytes()).hexdigest(),
            'scope':'Complete actual affected startup flow and normal Base ledgered send with own selected SQLite. Synthetic finite session/provider/transport/config/authorization/service seams; injected local open/transaction error. No runtime or remote credit.'}
    target=ROOT/('PROBES-'+variant+'.json');target.write_text(json.dumps(result,indent=2)+'\n');target.chmod(0o600)
    print(json.dumps({'variant':variant,'scenarios':len(output),
        'startup_generation_counts':{r['scenario']:len(r['startup_generations']) for r in output},
        'effect_counts':{r['scenario']:len(r['effects']) for r in output},'wall_s':result['wall_s']}))
if __name__=='__main__':main()
