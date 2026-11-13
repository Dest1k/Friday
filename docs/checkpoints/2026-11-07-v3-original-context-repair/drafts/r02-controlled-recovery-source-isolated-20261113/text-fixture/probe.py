"""Connected source-only R02 text delivery fixture. No installed module import.

The transport, configuration, current event, resume store, turn-marker release,
clock stop and startup lifecycle are explicit synthetic seams. Real full ledger,
SQLite opener/transactions/WAL gate and complete selected ordinary caller and
startup functions run on own durable files in separately reaped processes.
"""
from __future__ import annotations
import asyncio, ast, contextlib, hashlib, importlib.util, json, logging, os
from pathlib import Path
import resource, shutil, subprocess, sys, time, types
from types import SimpleNamespace as NS

B=Path(__file__).resolve().parent
SOURCE=B/'source'
LIMIT=100*1024*1024
os.umask(0o077)
logging.disable(logging.CRITICAL)

def dump(p,v):
    p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o600)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def install(home):
    # Import namespace and home/config are stand-local, never process env/H defaults.
    for name in ['gateway','gateway.platforms','hermes_cli']:
        m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
    cfg=types.ModuleType('hermes_cli.config')
    cfg.load_config=lambda:{'gateway':{'delivery_ledger':True},'database':{}}
    cfg.load_config_readonly=cfg.load_config
    cfg.cfg_get=lambda v,*ks,default=None: default
    sys.modules[cfg.__name__]=cfg
    hc=types.ModuleType('hermes_constants');hc.get_process_hermes_home=lambda:home;sys.modules[hc.__name__]=hc
    dead=types.ModuleType('gateway.dead_targets')
    dead.classify_dead_error=lambda e:'forbidden' if e=='Forbidden: bot was blocked by the user' else None
    sys.modules[dead.__name__]=dead
    module('hermes_cli.sqlite_runtime',SOURCE/'hermes_cli/sqlite_runtime.py')
    module('hermes_state_errors',SOURCE/'hermes_state_errors.py')
    module('hermes_state_wal',SOURCE/'hermes_state_wal.py')
    module('hermes_cli.sqlite_util',SOURCE/'hermes_cli/sqlite_util.py')
    status=module('gateway.status',SOURCE/'status_selected.py')
    ledger=module('gateway.delivery_ledger',SOURCE/'gateway/delivery_ledger.py')
    base=module('stand_base',SOURCE/'base_selected.py');base.stop_reply_clock=lambda *a:None
    startup=module('stand_startup',SOURCE/'startup_selected.py')
    startup._log_suppressed=lambda *a,**k:contextlib.suppress(Exception)
    return ledger,base,startup,status

def append(path,row):
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

class Transport:
    name='isolated-transport';_owner_profile='owned-test'
    def __init__(self,home,cut='none'):self.home,self.cut=home,cut
    async def _send_with_retry(self,**kwargs):return await self.send(**kwargs)
    async def send(self,**kwargs):
        if self.cut=='before_transport':os._exit(91)
        append(self.home/'fake-remote.jsonl',{'synthetic_remote_accepted':True,'content':kwargs['content'],'chat_id':kwargs['chat_id']})
        if self.cut=='after_remote_acceptance':os._exit(92)
        return NS(success=True,message_id=str(len(lines(self.home/'fake-remote.jsonl'))),error=None)

def rows(L):
    with L._transaction() as c:
        return [dict(zip(['id','state','attempts','owner_pid','owner_start','profile'],r)) for r in c.execute('SELECT obligation_id,state,attempts,owner_pid,owner_started_at,adapter_profile FROM delivery_obligations ORDER BY obligation_id')]

def child(home,action,cut):
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(LIMIT,LIMIT));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    home.mkdir(mode=0o700,parents=True,exist_ok=True)
    def audit(event,args):
        def inside(path):
            if isinstance(path,int):return True
            return Path(os.fsdecode(path)).resolve().is_relative_to(B)
        denied=False
        if event=='open':
            path,mode,flags=args
            writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            denied=writing and not inside(path)
        elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate'}:
            denied=not inside(args[0])
        elif event in {'os.rename','os.link','os.symlink'}:
            denied=not inside(args[0]) or not inside(args[1])
        elif event in {'socket.connect','socket.bind','socket.getaddrinfo','subprocess.Popen'}:
            denied=True
        if denied:
            # Hard refusal cannot be swallowed by product best-effort try/except.
            os._exit(94)
    sys.addaudithook(audit)
    L,base,startup,status=install(home)
    adapter=Transport(home,cut)
    event=NS(text='Synthetic R02 own text request',message_id='70001',source=NS(platform=NS(value='telegram'),chat_id='90001',thread_id=None))
    key='stand:owned:thread-1';content='R02 nonsensitive source fixture final text'
    class Caller(base.BasePlatformAdapter):
        typed_command_prefix='!'
        gateway_runner=None
        def _final_delivery_adapter(self,source):return adapter
        async def _release_turn_marker(self,event):append(home/'turn-marker-release.jsonl',{'released':True})
    class Store:
        async def clear_resume_pending(self,key):append(home/'resume-clears.jsonl',{'session':key})
    class Startup(startup.GatewayStartupMixin):
        adapters={'telegram':adapter};_profile_adapters={'owned-test':{'telegram':adapter}}
        async_session_store=Store()
        def _startup_should_abort(self):return False
        async def _obligation_adapter(self,row):
            assert row['profile']=='owned-test' and row['platform']=='telegram';return adapter
        async def _release_unsent_boot_claims(self,claimed):assert claimed==[]
        async def _arm_flood_timers_for_waiting_rows(self):assert L.pending_retries()==[]
    async def run():
        if action=='initial':
            if cut=='after_pending_write':
                L.mark_attempting=lambda oid:os._exit(90)
            elif cut=='after_ack_before_finalize':
                L.mark_delivered=lambda oid:os._exit(93)
            result,_=await Caller().send_final_ledgered(event,key,content,{},reply_to=None)
            assert result.success
        elif action=='recover':
            c=Startup();claimed=await c._claim_pending_obligations();n=await c._redeliver_claimed_obligations(claimed)
            dump(home/'recovery.json',{'claimed':[{k:v for k,v in r.items() if k!='content'} for r in claimed],'sent':n,'rows':rows(L)})
        else:raise AssertionError(action)
    asyncio.run(run())
    dump(home/(action+'-closed.json'),{'pid':os.getpid(),'birth':status.get_process_start_time(os.getpid()),'rows':rows(L),'remote_count':len(lines(home/'fake-remote.jsonl'))})

def run_child(home,action,cut='none'):
    start=time.monotonic()
    p=subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--child',str(home),action,cut],capture_output=True,text=True,timeout=35,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1','LANG':'C.UTF-8'})
    assert not p.stdout,p.stdout
    if p.returncode not in [0,90,91,92,93]:raise AssertionError({'returncode':p.returncode,'stderr':p.stderr[-3000:]})
    return {'exit':p.returncode,'wall_s':time.monotonic()-start,'stderr_bytes':len(p.stderr.encode())}

def main():
    start=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(LIMIT,LIMIT));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    temp=B/'own-data';assert not temp.exists();temp.mkdir(mode=0o700)
    checks=[]
    def ck(name,value,evidence=None):
        checks.append({'name':name,'passed':bool(value),'evidence':evidence});assert value,name
    try:
        pins=json.loads((B/'SOURCE-PINS.json').read_text())
        for p in pins:
            raw=Path(p['source']).read_bytes();ck('exact current source pin '+p['source'],len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'])
        for p,out,cl in [(pins[5],'base_selected.py','BasePlatformAdapter'),(pins[6],'startup_selected.py','GatewayStartupMixin')]:
            orig=next(x for x in ast.parse(Path(p['source']).read_bytes()).body if isinstance(x,ast.ClassDef) and x.name==cl)
            selected=next(x for x in ast.parse((SOURCE/out).read_bytes()).body if isinstance(x,ast.ClassDef))
            for f in selected.body:
                source=next(x for x in orig.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==f.name)
                ck('complete actual caller AST '+f.name,ast.dump(f,include_attributes=False)==ast.dump(source,include_attributes=False))
        results=[]
        for cut,initial_count,final_count,marker in [('after_pending_write',0,1,False),('before_transport',0,1,True),('after_remote_acceptance',1,2,True),('after_ack_before_finalize',1,2,True),('none',1,1,None)]:
            home=temp/cut
            a=run_child(home,'initial',cut);initial=lines(home/'fake-remote.jsonl')
            ck(cut+' initial fake remote count',len(initial)==initial_count)
            import sqlite3
            with sqlite3.connect('file:'+str(home/'state.db')+'?mode=ro',uri=True) as con:
                before_rows=con.execute('SELECT state,attempts,owner_pid,owner_started_at,adapter_profile FROM delivery_obligations').fetchall()
            expected_state='pending' if cut=='after_pending_write' else ('delivered' if cut=='none' else 'attempting')
            ck(cut+' persisted pre-restart state',len(before_rows)==1 and before_rows[0][0]==expected_state and before_rows[0][1]==0 and before_rows[0][4]=='owned-test',before_rows)
            original=(home/'original.bin');original.write_bytes(b'OWN ORIGINAL: unchanged')
            previous=hashlib.sha256(original.read_bytes()).hexdigest()
            b=run_child(home,'recover');after=lines(home/'fake-remote.jsonl');r=json.loads((home/'recovery.json').read_text())
            ck(cut+' observed remote count',len(after)==final_count)
            ck(cut+' final ledger delivered',all(x['state']=='delivered' for x in r['rows']))
            if marker is not None:ck(cut+' recovered marker iff uncertain',after[-1]['content'].startswith('♻️') is marker)
            ck(cut+' original preserved',hashlib.sha256(original.read_bytes()).hexdigest()==previous)
            # A second fresh boot must not deliver terminal rows again.
            c=run_child(home,'recover');ck(cut+' terminal next boot no duplicate',len(lines(home/'fake-remote.jsonl'))==final_count)
            results.append({'cut':cut,'initial':a,'persisted_before_restart':before_rows,'restart':b,'second_restart':c,'fake_remote_before':initial_count,'fake_remote_after':final_count,'recovery':r})
        # Real ledger guards with own-process stamp and own DB; explicit synthetic dead owner
        # only for race/target/staleness tests, never installed/native/real historical rows.
        home=temp/'guards';home.mkdir();L,base,startup,status=install(home)
        ck('owner actual current process fingerprint',L._owner_alive(os.getpid(),status.get_process_start_time(os.getpid())))
        ck('pid reuse mismatch rejected',not L._owner_alive(os.getpid(),status.get_process_start_time(os.getpid())+10000))
        def record(oid,profile='owned-test'):
            L.record_obligation(obligation_id=oid,session_key='own-key',platform='telegram',chat_id='90001',thread_id=None,content='own guard text',adapter_profile=profile)
        def dead(oid,**kw):
            with L._transaction() as c:
                c.execute('UPDATE delivery_obligations SET owner_pid=NULL,owner_started_at=NULL WHERE obligation_id=?',(oid,))
                for k,v in kw.items():
                    assert k in {'attempts','created_at','state','last_error','updated_at'}
                    c.execute('UPDATE delivery_obligations SET '+k+'=? WHERE obligation_id=?',(v,oid))
        record('live');ck('live owner not claimed',L.sweep_recoverable()==[])
        record('wrong-profile','other-test');dead('wrong-profile')
        ck('wrong profile never claimed',L.sweep_recoverable(deliverable_targets={('telegram','owned-test')})==[])
        record('disconnected');dead('disconnected')
        ck('disconnected platform never claimed',L.sweep_recoverable(deliverable_platforms={'other'})==[])
        record('stale');dead('stale',created_at=time.time()-L.STALE_AFTER_SECONDS-1)
        record('exhausted');dead('exhausted',attempts=L.MAX_ATTEMPTS)
        L.sweep_recoverable(deliverable_platforms=set())
        state={x['id']:x for x in rows(L)}
        ck('stale and exhausted abandoned without send',state['stale']['state']==state['exhausted']['state']=='abandoned')
        record('claim');dead('claim')
        claimed=L.sweep_recoverable(deliverable_targets={('telegram','owned-test')})
        ck('fresh dead-owner claim one per row',len([r for r in claimed if r['obligation_id']=='claim'])==1)
        ck('second sweep cannot reclaim live claimed rows',L.sweep_recoverable(deliverable_targets={('telegram','owned-test')})==[])
        record('failed-flood');L.mark_failed('failed-flood','flood_control:60')
        ck('runtime flood not retried before deadline',L.sweep_failed_for_runtime('telegram',profile='owned-test')==[])
        record('runtime');L.mark_failed('runtime','send_path_degraded')
        claim=L.sweep_failed_for_runtime('telegram',profile='owned-test');ck('runtime exact owner claimed',len(claim)==1 and claim[0]['obligation_id']=='runtime')
        ck('runtime double claim blocked',L.sweep_failed_for_runtime('telegram',profile='owned-test')==[])
        ck('release unsent runtime claim exact owner',L.release_runtime_claim('runtime','send_path_degraded'))
        ck('release failed state cannot decrement twice',not L.release_runtime_claim('runtime','send_path_degraded'))
        ck('stable obligation identity same turn',L.compute_obligation_id('key','1','body')==L.compute_obligation_id('key','1','body'))
        ck('distinct ingress or session identity distinct',len({L.compute_obligation_id('key','1','body'),L.compute_obligation_id('key','2','body'),L.compute_obligation_id('key2','1','body')})==3)
        modes=[]
        for db in temp.rglob('state.db'):
            import sqlite3
            with sqlite3.connect(db) as c:modes.append({'scope':db.parent.name,'journal_mode':c.execute('PRAGMA journal_mode').fetchone()[0],'integrity':c.execute('PRAGMA integrity_check').fetchone()[0]})
        ck('all own databases integral',all(x['integrity']=='ok' for x in modes))
        usage=sum(p.stat().st_size for p in temp.rglob('*') if p.is_file());ck('aggregate disk below finite budget',usage<LIMIT,usage)
        dump(B/'CHECKS.json',{'checks':checks,'cases':results,'db_modes':modes,'scope':'ISOLATED_REAL_CURRENT_TEXT_CONSUMER_FAKE_TRANSPORT_NOT_LIVE','observed_defect':'Ambiguous attempting row is resent automatically with visible marker; accepted fake remote can receive same content twice. This is honest at-least-once current policy, not original R02 reconcile-before-resend compliance.','product_patch':None,'child_audit':'Every cut/recovery child hard-refuses writes outside own text fixture, socket connect/bind/DNS and nested process spawn; expected exitcodes exclude audit refusal94.'})
    finally:
        shutil.rmtree(temp)
    ru=resource.getrusage(resource.RUSAGE_SELF);rc=resource.getrusage(resource.RUSAGE_CHILDREN)
    dump(B/'RESOURCES.json',{'wall_s':time.monotonic()-start,'cpu_self_s':ru.ru_utime+ru.ru_stime,'cpu_children_s':rc.ru_utime+rc.ru_stime,'maxrss_self_kib':ru.ru_maxrss,'maxrss_child_kib':rc.ru_maxrss,'limits_each_process':{'CPU_s':120,'AS_bytes':536870912,'FSIZE_bytes':LIMIT,'CORE':0},'child_wall_timeout_s':35,'whole_command_wall_timeout_s':300,'disk_aggregate_enforced_by_bounded_fixture_and_measured':True,'no_aggregate_cgroup_claim':True})
    dump(B/'CLOSURE.json',{'own_data_removed':not temp.exists(),'children_subprocess_run_waited':True,'no_detached_processes':True,'no_product_effects':True})
    print(json.dumps({'passed':len(checks),'wall_s':time.monotonic()-start,'stand_closed':not temp.exists()}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),sys.argv[3],sys.argv[4])
    else:main()
