"""Task41 real selected caller/ledger/startup on own persistent SQLite, fake transport.
No installed product imports. Complete functions are compiled from own pinned copies.
"""
from __future__ import annotations
import ast,asyncio,contextlib,hashlib,importlib.util,json,logging,os,resource,shutil,sqlite3,subprocess,sys,threading,time,types
from pathlib import Path
from types import SimpleNamespace as NS
from dataclasses import dataclass
from typing import Any,Optional,Dict,Callable
B=Path(__file__).resolve().parents[1];OUT=B/'text-controls';LIMIT=100*1024*1024
os.umask(0o077);logging.disable(logging.CRITICAL)
BASE=['_record_delivery_obligation','_finalize_delivery_obligation','send_final_ledgered','_send_with_retry']
START=['_claim_pending_obligations','_clear_resume_pending_for_claimed_obligations','_redeliver_claimed_obligations','_release_unsent_boot_claims','_release_runtime_claim_quiet','_obligation_adapter','_startup_should_abort','_redeliver_failed_obligations_for_platform','_schedule_resume_pending_sessions']

def dump(p,v):p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o600)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m

def select(tree,rel,cls,names):
 s=(tree/rel).read_text();c=next(n for n in ast.parse(s).body if isinstance(n,ast.ClassDef) and n.name==cls)
 found=[n for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
 assert {n.name for n in found}==set(names)
 lines=s.splitlines(True)
 code='class '+cls+':\n'+''.join(''.join(lines[min([n.lineno]+[d.lineno for d in n.decorator_list])-1:n.end_lineno])+'\n' for n in found)
 return code,{n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in found}

def install(home,tree):
 for name in ['gateway','gateway.platforms','hermes_cli']:
  m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
 cfg=types.ModuleType('hermes_cli.config');cfg.load_config=lambda:{'gateway':{'delivery_ledger':True},'database':{}};cfg.load_config_readonly=cfg.load_config;cfg.cfg_get=lambda cfg,*ks,default=None:default;sys.modules[cfg.__name__]=cfg
 hc=types.ModuleType('hermes_constants');hc.get_process_hermes_home=lambda:home;sys.modules[hc.__name__]=hc
 dead=types.ModuleType('gateway.dead_targets');dead.classify_dead_error=lambda e:'forbidden' if e=='Forbidden: bot was blocked by the user' else None;sys.modules[dead.__name__]=dead
 for n,r in [('hermes_cli.sqlite_runtime','hermes_cli/sqlite_runtime.py'),('hermes_state_errors','hermes_state_errors.py'),('hermes_state_wal','hermes_state_wal.py'),('hermes_cli.sqlite_util','hermes_cli/sqlite_util.py')]:module(n,tree/r)
 status_src=(tree/'gateway/status.py').read_text();ts=ast.parse(status_src);names=['_get_process_start_time','get_process_start_time','start_time_fingerprints_match','_pid_exists'];parts=[]
 for n in ts.body:
  if isinstance(n,ast.FunctionDef) and n.name in names:parts.append(''.join(status_src.splitlines(True)[n.lineno-1:n.end_lineno]))
 status=types.ModuleType('gateway.status');status.__dict__.update({'os':os,'sys':sys,'Optional':Optional,'Any':Any,'time':time,'Path':Path,'START_TIME_DRIFT_TOLERANCE':200,'pid_exists_stdlib':lambda pid:False});sys.modules[status.__name__]=status;exec('\n\n'.join(parts),status.__dict__)
 L=module('gateway.delivery_ledger',tree/'gateway/delivery_ledger.py')
 src=(tree/'gateway/platforms/base.py').read_text();n=next(x for x in ast.parse(src).body if isinstance(x,ast.ClassDef) and x.name=='SendResult');code=''.join(src.splitlines(True)[n.lineno-2:n.end_lineno]);ns={'dataclass':dataclass,'Optional':Optional,'Any':Any,'__name__':__name__};exec(code,ns);SendResult=ns['SendResult']
 from enum import Enum
 class Platform(Enum):TELEGRAM='telegram';SLACK='slack'
 g={'asyncio':asyncio,'logging':logging,'time':time,'logger':logging.getLogger('own'),'Any':Any,'Dict':Dict,'Optional':Optional,'Callable':Callable,'MessageEvent':Any,'SendResult':SendResult,'stop_reply_clock':lambda *a:None,'records_delivery':lambda fn:fn,'Platform':Platform,'_log_suppressed':lambda *a,**k:contextlib.suppress(Exception)}
 basecode,basepin=select(tree,'gateway/platforms/base.py','BasePlatformAdapter',BASE);exec(basecode,g);Base=g['BasePlatformAdapter']
 names=START+(['_delivery_resume_generation'] if hasattr(L,'telegram_text_send_scope') else [])
 startcode,startpin=select(tree,'gateway/run_startup.py','GatewayStartupMixin',names);exec(startcode,g);Startup=g['GatewayStartupMixin']
 return L,Base,Startup,status,SendResult,Platform,{'base_AST':basepin,'startup_AST':startpin}

def append(p,v):
 with p.open('a') as f:f.write(json.dumps(v,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
def lines(p):return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
def rows(L):
 with L._transaction() as c:
  cols=['id','session','platform','chat','thread','content','state','attempts','owner_pid','owner_birth','profile','last_error']
  return [dict(zip(cols,r)) for r in c.execute('SELECT obligation_id,session_key,platform,chat_id,thread_id,content,state,attempts,owner_pid,owner_started_at,adapter_profile,last_error FROM delivery_obligations ORDER BY obligation_id')]
def limits():
 for k,v in [(resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,512*1024*1024),(resource.RLIMIT_FSIZE,LIMIT),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
def audit(event,args):
 def inside(p):return isinstance(p,int) or Path(os.fsdecode(p)).resolve().is_relative_to(B)
 denied=False
 if event=='open':
  p,m,fl=args;denied=((isinstance(m,str) and any(c in m for c in 'wax+')) or bool(fl & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))) and not inside(p)
 elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate'}:denied=not inside(args[0])
 elif event in {'os.rename','os.link','os.symlink'}:denied=not inside(args[0]) or not inside(args[1])
 elif event in {'socket.connect','socket.bind','socket.getaddrinfo','subprocess.Popen'}:denied=True
 if denied:os._exit(94)

def child(home,tree,action,cut):
 limits();sys.addaudithook(audit);L,Base,Start,status,Result,Platform,ap=install(home,tree)
 class Transport(Base):
  name='own-synthetic-transport';_owner_profile='owned-test';_send_path_degraded=False
  def _send_retry_is_final(self,r):return True
  async def send(self,**kw):
   if cut=='before_transport':os._exit(91)
   append(home/'remote.jsonl',{'synthetic_accepted':True,'content':kw['content'],'chat_id':kw['chat_id']})
   if cut=='after_remote_acceptance':os._exit(92)
   return Result(success=True,message_id=None if cut=='missing_ack' else '1')
 class Caller(Base):
  typed_command_prefix='!';gateway_runner=None
  def _final_delivery_adapter(self,s):return adapter
  async def _release_turn_marker(self,e):append(home/'released.jsonl',{'released':True})
 class Store:
  async def clear_resume_pending(self,k):append(home/'cleared.jsonl',{'session':k})
 class Startup(Start):
  _restart_requested=False;_draining=False;_shutdown_event=NS(is_set=lambda:False)
  adapters={Platform.TELEGRAM:None};_profile_adapters={'owned-test':{Platform.TELEGRAM:None}}
  async_session_store=Store()
  session_store=NS(_lock=threading.RLock(),_ensure_loaded_locked=lambda:None,_entries={})
  async def _authorization_adapter(self,*a):return adapter
  async def _run_owned_startup_cleanup(self,work,*a):return await work
  async def _arm_flood_timers_for_waiting_rows(self):pass
  def _authorization_adapter(self,platform,profile):
   assert platform==Platform.TELEGRAM and profile=='owned-test';return adapter
 adapter=Transport();event=NS(text='Own nonsensitive user request',message_id='70001',source=NS(platform=Platform.TELEGRAM,chat_id='90001',thread_id=None))
 key='own:telegram:session1';body='OWN R02 final body';Startup.adapters[Platform.TELEGRAM]=adapter;Startup._profile_adapters['owned-test'][Platform.TELEGRAM]=adapter
 async def run():
  if action=='initial':
   if cut=='after_pending_write':L.mark_attempting=lambda oid:os._exit(90)
   if cut=='after_ack_before_finalize':L.mark_delivered=lambda oid:os._exit(93)
   r,_=await Caller().send_final_ledgered(event,key,body,{},reply_to=None)
   dump(home/'initial-result.json',{'success':r.success,'error':r.error})
  elif action=='recover':
   s=Startup();claimed=await s._claim_pending_obligations();n=await s._redeliver_claimed_obligations(claimed)
   dump(home/'recovery.json',{'claimed':[{k:v for k,v in r.items() if k!='content'} for r in claimed],'sent':n,'rows':rows(L)})
  elif action=='reenter':
   r,_=await Caller().send_final_ledgered(event,key,body,{},reply_to=None);dump(home/'reenter-result.json',{'success':r.success,'error':r.error})
  else:raise AssertionError(action)
 asyncio.run(run());dump(home/(action+'-closed.json'),{'rows':rows(L),'pid':os.getpid(),'birth':status.get_process_start_time(os.getpid()),'ast':ap})

def run_child(home,tree,action,cut='none'):
 t=time.monotonic();p=subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--child',str(home),str(tree),action,cut],capture_output=True,text=True,timeout=35,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1','LANG':'C.UTF-8'})
 if p.returncode not in [0,90,91,92,93]:raise AssertionError({'exit':p.returncode,'stderr':p.stderr[-3000:]})
 assert not p.stdout
 return {'exit':p.returncode,'wall_s':time.monotonic()-t,'stderr_bytes':len(p.stderr)}
def snapshot(p):
 st=p.stat();return {'sha256':sha(p),'stat':[st.st_dev,st.st_ino,st.st_uid,st.st_gid,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_nlink]}

def main(stage):
 limits();start=time.monotonic();out=OUT/stage;assert not out.exists();out.mkdir(mode=0o700);temp=out/'own-data';temp.mkdir(mode=0o700);checks=[];cases=[]
 def ck(n,v,e=None):
  checks.append({'name':n,'passed':bool(v),'evidence':e})
  if not v:dump(out/'FAILED-CHECKS.json',{'checks':checks,'cases':cases})
  assert v,n
 try:
  # Freeze exact code BEFORE evidence is announced; future changes cannot overwrite this revision.
  for variant in ['baseline','candidate']:
   tree=out/variant;shutil.copytree(B/variant,tree)
   for cut in ['after_pending_write','before_transport','after_remote_acceptance','after_ack_before_finalize','none','missing_ack']:
    home=temp/(variant+'-'+cut);home.mkdir(mode=0o700);p=home/'original.bin';p.write_bytes(b'OWN ORIGINAL DOCUMENT unchanged');before=snapshot(p)
    a=run_child(home,tree,'initial',cut);remote_before=len(lines(home/'remote.jsonl'))
    with sqlite3.connect('file:'+str(home/'state.db')+'?mode=ro',uri=True) as c:
     prior=c.execute('select state,attempts,content,adapter_profile from delivery_obligations').fetchall();mode=c.execute('pragma journal_mode').fetchone()[0]
    ck(variant+'/'+cut+'/exact selected SQLite fresh WAL',mode=='wal',{'sqlite_version':sqlite3.sqlite_version,'journal_mode':mode})
    ck(variant+'/'+cut+'/original preserved across initial cut',snapshot(p)==before)
    b=run_child(home,tree,'recover');remote_after=len(lines(home/'remote.jsonl'));r=json.loads((home/'recovery.json').read_text());state=r['rows'][0]['state']
    expected_count=(1 if cut in ['none','missing_ack','after_pending_write'] else (0 if cut=='before_transport' else 1)) if variant=='candidate' else (1 if cut in ['none','missing_ack','after_pending_write','before_transport'] else 2)
    expected_state=('delivered' if cut in ['none','after_pending_write'] else 'uncertain') if variant=='candidate' else 'delivered'
    ck(variant+'/'+cut+'/remote effect count',remote_after==expected_count,remote_after)
    ck(variant+'/'+cut+'/durable outcome',state==expected_state,r['rows'])
    ck(variant+'/'+cut+'/payload profile original intact',prior[0][2]=='OWN R02 final body' and r['rows'][0]['content']==prior[0][2] and r['rows'][0]['profile']==prior[0][3]=='owned-test' and snapshot(p)==before)
    c=run_child(home,tree,'recover');ck(variant+'/'+cut+'/next boot no additional send',len(lines(home/'remote.jsonl'))==expected_count)
    reentry=None
    if variant=='candidate':
     reentry=run_child(home,tree,'reenter');v=json.loads((home/'reenter-result.json').read_text());ck(cut+'/same OID never resets fence',not v['success'] and v['error']=='delivery_not_admitted' and len(lines(home/'remote.jsonl'))==expected_count)
    cases.append({'variant':variant,'cut':cut,'initial':a,'recovery':b,'next_boot':c,'reentry':reentry,'before_state':prior,'before_remote_count':remote_before,'after_remote_count':remote_after,'state':state,'recovery_result':r,'original_snapshot':before,'original_after':snapshot(p)})
  # Additional precise ledger guards; all own rows, no historical state.
  if not stage.startswith('m1-'):
   home=temp/'guards';home.mkdir();L,Base,Start,status,Result,Platform,ap=install(home,out/'candidate')
   def record(oid,platform='telegram',profile='owned-test'):
    return L.record_obligation(obligation_id=oid,session_key='own-key',platform=platform,chat_id='90001',thread_id='11',content='Own preserved guard',adapter_profile=profile)
   def change(oid,**kw):
    with L._transaction() as c:
     for k,v in kw.items():
      assert k in {'owner_pid','owner_started_at','attempts','created_at','updated_at','state','last_error','adapter_profile'}
      c.execute('UPDATE delivery_obligations SET '+k+'=? WHERE obligation_id=?',(v,oid))
   def get(oid):return next(r for r in rows(L) if r['id']==oid)
   ck('actual live owner recognized',L._owner_alive(os.getpid(),status.get_process_start_time(os.getpid())))
   ck('PID reuse mismatch rejected',not L._owner_alive(os.getpid(),status.get_process_start_time(os.getpid())+10000))
   record('live');ck('boot does not steal live owner',L.sweep_recoverable()==[])
   record('wrong');change('wrong',owner_pid=None,owner_started_at=None,adapter_profile='other');ck('wrong route/profile not claimed',L.sweep_recoverable(deliverable_targets={('telegram','owned-test')})==[])
   for oid,err in [('legacy-network','NetworkError'),('legacy-flood','flood_control:1'),('legacy-timeout','timed out'),('legacy-spoof','send_path_degraded')]:
    record(oid);change(oid,state='failed',last_error=err,owner_pid=None,owner_started_at=None,attempts=0)
   claims=L.sweep_recoverable(deliverable_targets={('telegram','owned-test')});ck('legacy attempted failures adopted not resent',all(r.get('uncertain') and r.get('adopted') for r in claims) and len(claims)==4)
   for oid in ['legacy-network','legacy-flood','legacy-timeout','legacy-spoof']:
    ck(oid+' explicit uncertain retained',get(oid)['state']=='uncertain' and get(oid)['attempts']==0)
   record('runtime-ambiguous');L.mark_attempting('runtime-ambiguous');L.mark_failed('runtime-ambiguous','parse accepted response');ck('new ambiguous error explicit uncertain',get('runtime-ambiguous')['state']=='uncertain')
   record('spoof-local-error');L.mark_attempting('spoof-local-error');L.mark_failed('spoof-local-error','send_path_degraded');ck('ambiguous error literal is never zeroeffect proof',get('spoof-local-error')['state']=='uncertain')
   ck('uncertain not runtime claimed',L.sweep_failed_for_runtime('telegram',profile='owned-test')==[])
   record('local-degraded');L.mark_attempting('local-degraded');L.mark_failed('local-degraded','send_path_degraded',no_effect=True);cl=L.sweep_failed_for_runtime('telegram',profile='owned-test');ck('proven local no-effect runtime retry once',len(cl)==1 and cl[0]['obligation_id']=='local-degraded' and not cl[0]['needs_marker'])
   ck('no double runtime claim',L.sweep_failed_for_runtime('telegram',profile='owned-test')==[])
   ck('undispatched release exact owner',L.release_runtime_claim('local-degraded','send_path_degraded') and get('local-degraded')['state']=='failed_unsent')
   ck('release cannot decrement twice',not L.release_runtime_claim('local-degraded','send_path_degraded'))
   record('typed-flood');L.mark_attempting('typed-flood');L.mark_failed('typed-flood','flood_control:60',no_effect=True);ck('proved wholly unsent flood preserves wait',get('typed-flood')['state']=='failed_unsent' and any(x['not_before']>time.time() for x in L.pending_retries()))
   ck('flood not claimed before actual cooldown',not any(x['obligation_id']=='typed-flood' for x in L.sweep_failed_for_runtime('telegram',profile='owned-test')))
   record('dead-target');L.mark_attempting('dead-target');L.mark_failed('dead-target','Forbidden: bot was blocked by the user');change('dead-target',owner_pid=None,owner_started_at=None);ck('terminal dead target never boot retried',not any(r['obligation_id']=='dead-target' for r in L.sweep_recoverable()))
   record('late');L.mark_attempting('late');L.mark_delivered('late');L.mark_failed('late','late network error');ck('late failure cannot downgrade durable delivered',get('late')['state']=='delivered')
   record('foreign');change('foreign',state='attempting',owner_pid=99999999,owner_started_at=1);L.mark_delivered('foreign');ck('foreign-owner finalization refused',get('foreign')['state']=='attempting')
   for oid in ['stale','cap']:
    record(oid);change(oid,owner_pid=None,owner_started_at=None,**({'created_at':time.time()-L.STALE_AFTER_SECONDS-1} if oid=='stale' else {'attempts':L.MAX_ATTEMPTS,'state':'failed_unsent'}))
   L.sweep_recoverable(deliverable_platforms=set());ck('unsent stale/capped retain existing abandoned bounds',get('stale')['state']==get('cap')['state']=='abandoned')
   record('stale-uncertain');change('stale-uncertain',state='attempting',attempts=99,created_at=time.time()-L.STALE_AFTER_SECONDS-1,owner_pid=None,owner_started_at=None);L.sweep_recoverable();ck('uncertainty not silently abandoned at cap/staleness',get('stale-uncertain')['state']=='uncertain')
   # The retention cap counts only evictable rows; an uncertainty backlog never deletes new owed text.
   with L._transaction() as con:
    template=con.execute('select * from delivery_obligations where obligation_id=?',('legacy-network',)).fetchone()
    for i in range(510):
     v=list(template);v[0]='fence-'+str(i);con.execute('INSERT INTO delivery_obligations VALUES ('+','.join('?' for _ in v)+')',v)
   record('retained-new');ck('510 uncertainty rows neither erased nor evict pending',sum(1 for r in rows(L) if r['id'].startswith('fence-'))==510 and get('retained-new')['state']=='pending')
   # Real nearest startup cleanup and session-generation gate on actual-shaped own entries.
   async def startup_controls():
    entry=NS(session_key='answered',session_id='own-session',transport_profile='owned-test',last_resume_marked_at=100.0,updated_at=101.0,active_turn_token=None,active_turn_started_at=None,resume_pending=True)
    class FailStore:
     async def clear_resume_pending(self,k):raise OSError('own injected save failure')
    class Runner(Start):
     _restart_requested=False;_draining=False;_shutdown_event=NS(is_set=lambda:False)
     session_store=NS(_lock=threading.RLock(),_ensure_loaded_locked=lambda:None,_entries={'answered':entry})
     async_session_store=FailStore();tasks=[]
     def _resume_pending_candidates(self,p):return [entry]
     def _is_session_running(self,k):return False
     def _restored_source(self,e):return NS(platform=Platform.TELEGRAM)
     def _delivery_adapter_for(self,s):return object()
     def _resume_owner_authorized(self,*a):return True
     def _session_state(self,k):return NS(turn=NS(agent=None,started_ts=None))
     def _persist_active_agents(self):pass
     async def _run_startup_resume_event(self,*a):return None
     def _retain_background_task(self,t):self.tasks.append(t);return t
     async def _run_owned_startup_cleanup(self,work,*a):return await work
     def _authorization_adapter(self,p,pr):return None
     async def _arm_flood_timers_for_waiting_rows(self):pass
    runmod=types.ModuleType('gateway.run');runmod._AGENT_PENDING_SENTINEL=object();runmod._auto_continue_freshness_window=lambda:300;runmod._is_fresh_gateway_interruption=lambda *a,**k:True;sys.modules[runmod.__name__]=runmod
    Start._schedule_resume_pending_sessions.__globals__.update({'MessageEvent':lambda **kw:NS(**kw),'MessageType':NS(TEXT='text')})
    r=Runner();claim={'obligation_id':'ownveto','session_key':'answered','platform':'telegram','adopted':True,'uncertain':True}
    await r._clear_resume_pending_for_claimed_obligations([claim]);ck('failed sessionflag save cannot trigger answered-generation modelresume',r._schedule_resume_pending_sessions()==0)
    entry.updated_at=102.0;ck('future independent generation not permanently blocked',r._schedule_resume_pending_sessions()==1);await asyncio.gather(*r.tasks)
    record('abort-pending');change('abort-pending',owner_pid=None,owner_started_at=None)
    claim=next(x for x in L.sweep_recoverable(deliverable_targets={('telegram','owned-test')}) if x['obligation_id']=='abort-pending')
    r._draining=True;ck('shutdown before dispatch sends0',await r._redeliver_claimed_obligations([claim])==0)
    ck('pre-send cancellation releases genuineunsent claim without budgetloss',get('abort-pending')['state']=='failed_unsent' and get('abort-pending')['attempts']==0)
    record('missing-route');change('missing-route',owner_pid=None,owner_started_at=None)
    claim=next(x for x in L.sweep_recoverable(deliverable_targets={('telegram','owned-test')}) if x['obligation_id']=='missing-route');r._draining=False
    ck('exact adapter missing before dispatch sends0',await r._redeliver_claimed_obligations([claim])==0)
    ck('missing-route releasesunsent ownerclaim',get('missing-route')['state']=='failed_unsent' and get('missing-route')['attempts']==0)
   asyncio.run(startup_controls())
   # Preserve non-Telegram legacy marked retry behavior.
   record('other-channel',platform='slack');change('other-channel',state='attempting',owner_pid=None,owner_started_at=None);cl=L.sweep_recoverable(deliverable_platforms={'slack'});ck('unrelated channel existing marked recovery preserved',len(cl)==1 and cl[0]['needs_marker'])
   # A parsed success without an authoritative positive ID must stay UNKNOWN.
   for i,r in enumerate([Result(True),Result(True,message_id='0'),Result(True,message_id=True),Result(True,message_id='1',raw_response={'message_ids':['1','bad']}),Result(True,message_id='1',raw_response={'partial_overflow':True})]):ck('bad ACK proof '+str(i),not L.delivery_acknowledged('telegram',r))
   ck('positive SDK ACK accepted',L.delivery_acknowledged('telegram',Result(True,message_id='9',raw_response={'message_ids':['9','10']})))
  dbs=[]
  for p in temp.rglob('state.db'):
   with sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True) as c:dbs.append({'scope':p.parent.name,'journal_mode':c.execute('pragma journal_mode').fetchone()[0],'integrity':c.execute('pragma integrity_check').fetchone()[0]})
  ck('real own databases integral WAL',all(v['journal_mode']=='wal' and v['integrity']=='ok' for v in dbs))
  usage=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());ck('own bounded aggregate disk',usage<LIMIT,usage)
  pins=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p)} for v in ['baseline','candidate'] for p in sorted((out/v).rglob('*')) if p.is_file()]
  dump(out/'CHECKS.json',{'stage':stage,'checks':checks,'cases':cases,'source_pins':pins,'dbs':dbs,'engine':{'executable':sys.executable,'python':sys.version,'sqlite_version':sqlite3.sqlite_version,'sqlite_source_id':sqlite3.connect(':memory:').execute('select sqlite_source_id()').fetchone()[0]},'limits':'Source-only own-process exit after returned SQLcommit, not livecut/powerloss or remote reconciliation. Transport/event/sessionstore/config/deaderrorclassifier/replyclock are declared synthetic; actual complete selected caller/SQLite/startup execute.'})
 finally:shutil.rmtree(temp)
 ru=resource.getrusage(resource.RUSAGE_SELF);rc=resource.getrusage(resource.RUSAGE_CHILDREN)
 dump(out/'RESOURCES.json',{'wall_s':time.monotonic()-start,'cpu_self_s':ru.ru_utime+ru.ru_stime,'cpu_children_s':rc.ru_utime+rc.ru_stime,'rss_self_kib':ru.ru_maxrss,'rss_children_kib':rc.ru_maxrss,'limits_each':{'CPU_s':120,'AS_bytes':536870912,'FSIZE_bytes':LIMIT,'CORE':0},'outer_wall_s':300,'child_wall_s':35,'own_affinity':sorted(os.sched_getaffinity(0)),'disk_max_measured_bytes':usage})
 dump(out/'CLOSURE.json',{'own_data_removed':not temp.exists(),'all_spawned_subprocesses_run_waited':True,'no_detached_processes':True,'shared_effects':False})
 print(json.dumps({'stage':stage,'checks':len(checks),'wall_s':time.monotonic()-start,'closure':not temp.exists()}))
if __name__=='__main__':
 if sys.argv[1]=='--child':child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4],sys.argv[5])
 else:
  try:main(sys.argv[1])
  except BaseException:
   import traceback
   dump(OUT/sys.argv[1]/'ERROR.json',{'traceback':traceback.format_exc(),'credit':'HARNESS_FAILURE_NO_FINAL_PASS'})
   raise
