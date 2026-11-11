"""Root-only actual203 readonly prerequisite for the exact original M14 query.

Import is inert. Preparation never calls observe/check. No authority is issued.
Only unchanged gate202 fresh_native/validate_native transport is reused; its
check() is NEVER called. Runtime reads are finite and scoped to this tester.
"""
import contextlib
import datetime as dt
import hashlib,json,math,os,sqlite3,stat,subprocess,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
DB=H/'profiles/telegram-bot-8812646969/state.db'
CONFIG=H/'profiles/telegram-bot-8812646969/config.yaml'
G=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-F01-BOUND-TESTER-PREP-20261111/gate202.py')
G_SHA='52c27671815632cf4fa884ee187a74fad2671e1fd53003a2d0512083bcef8c9a'
OP=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE203-ROOT-MAINTENANCE-FRAME-20261111/ROOT-NATIVE203-LIVE-OPERATION.json')
OP_SHA='e68e01832c63c08fb2b420466ee5abad0d73ebbe83ddd587964a06225e98d9d8'
LINEAGE=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/M14-CURRENT-READONLY-SOURCE-LINEAGE.json')
LINEAGE_SHA='ef7c2daa5bc7e41f1536e37f7a296898d1205deb8c87eb75429eaea2b4ecc6a5'
SID='20261030_093055_43bba39f'
KEY='agent:telegram-bot-8812646969:telegram:dm:8812646969'
RUN_ID='m14-original-postrestart-query-01'
RECEIPT='9d8d1d954a59d5f944cb0b33c11cba3bba845cbb5d71088f335d68077c2a83c2'
INPUT='31178b28f928c937118d5c58df5aa15bb9fe23f748979cbdd9cb2f1456f513ad'
EXPECTED={'source_layers':203,'project_files':487,'native_files':17891,'plugin_files':52,'base_source_files':17730,'source_receipt_sha256':RECEIPT,'input_sha256':INPUT}
PRIVATE_MARKERS=(b'FRW-ASTRA-V3-M14-EXACT-CONSUMER-PREP-20261111',b'FRW-ASTRA-V3-M14-POST203-FORWARD-PREP-20261111')
ADAPTER_SHA='0d0daeeb6a0e2b1c30580728c733533c5383f1cdfec43ca7dc2d5b96fe7eb336'
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
SESSION_FIELDS=('id','source','user_id','chat_id','chat_type','session_key','profile_name','transport_profile')
ROW_FIELDS=('id','session_id','role','content','timestamp','platform_message_id','active','compacted')

def require(ok,why):
 if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True)+'\n').encode()
def unique(pairs):
 out={}
 for k,v in pairs:require(k not in out,'duplicate JSON key');out[k]=v
 return out
def identity(s):
 return {'device':s.st_dev,'inode':s.st_ino,'uid':s.st_uid,'gid':s.st_gid,'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
def read(path,limit=24*1024*1024,private=False):
 p=Path(path);require(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'absolute no-symlink path required')
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb')as f:
  before=os.fstat(f.fileno());raw=f.read(limit+1);after=os.fstat(f.fileno())
 require(stat.S_ISREG(before.st_mode)and before.st_uid==os.getuid()and before.st_nlink==1 and not stat.S_IMODE(before.st_mode)&0o002 and len(raw)<=limit and identity(before)==identity(after)==identity(p.stat()),'unsafe or changed owned current file')
 require(not private or stat.S_IMODE(before.st_mode)==0o600,'Root facts must be0600')
 return raw
def doc(path,private=False):return json.loads(read(path,private=private),object_pairs_hook=unique)
def pinned(path,sha,private=False):
 raw=read(path,private=private);require(digest(raw)==sha,'pinned current evidence changed');return json.loads(raw,object_pairs_hook=unique)
def ref(path):
 raw=read(path);return {'path':str(Path(path)),'bytes':len(raw),'sha256':digest(raw)}
def readref(r,private=True):
 require(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact protected fact reference required');raw=read(r['path'],private=private);require(len(raw)==r['bytes']and digest(raw)==r['sha256'],'Root fact reference drift');return json.loads(raw,object_pairs_hook=unique)
def transport():
 raw=read(G);require(digest(raw)==G_SHA,'unchanged readonly transport source required');m=types.ModuleType('M14_unchanged_native_transport');m.__file__=str(G);exec(compile(raw,str(G),'exec'),m.__dict__);return m
def adapter():
 # Parent source/consumer pins this exact checker and adapter; require this local
 # adapter's actual frozen-v42 pin and all fixed original shape data as well.
 raw=read(HERE/'adapter.py');require(digest(raw)==ADAPTER_SHA,'exact reviewed adapter dependency changed');m=types.ModuleType('M14_current_adapter');m.__file__=str(HERE/'adapter.py');exec(compile(raw,m.__file__,'exec'),m.__dict__)
 require(m.BASE_SHA=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'and m.EXPECTED203==EXPECTED and m.RUN_ID==RUN_ID and m.SID==SID and m.KEY==KEY,'exact source binding mismatch');return m

def native203():
 """Selected native203 seam from Root source, with stable input reads/CAS."""
 op=pinned(OP,OP_SHA)
 require(op['state']=='NATIVE203_PROJECT487_FRESH_PERMANENT_SERVICES_RUNNING'and op['full_selected_native_files_readback']is True and op['selected_native_file_count']==17891 and op['user_db_wal_shm_verified_before_starts']is True and op['publisher_closed_before_parent_custody_release']is True,'actual203 accepted source/readback/restart proof required')
 for path,sha in op['restore_verified_inputs']['settled_files'].items():require(digest(read(path))==sha,'current203 settled input drift')
 receipt=pinned(H/'hermes-agent.source.json',RECEIPT);marker=doc(H/'FRIDAY-INSTALL.json');stamp=doc(H/'hermes-agent/install-stamp.json')
 require(marker['source_receipt_sha256']==RECEIPT and marker['input_sha256']==INPUT and(len(receipt['layers']),len(receipt['files']),len(marker['plugin_files']))==(203,17891,52)and stamp['fridaySource']['layers']==receipt['layers']and stamp['fridaySource']['baseTree']==receipt['base_tree'],'current203 receipt/marker/stamp tuple mismatch')
 for name,sha in marker['plugin_files'].items():require(digest(read(H/name))==sha,'current plugin drift')
 services={};g=transport()
 for unit,key in [('hermes-gateway-1b7e7667.service','gateway_after'),('hermes-dashboard.service','dashboard_after')]:
  r=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,UnitFileState,RuntimeMaxUSec,NRestarts'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5,check=True)
  require(len(r.stdout)<=65536 and len(r.stderr)<=65536,'bounded systemctl output required')
  properties={'LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','UnitFileState','RuntimeMaxUSec','NRestarts'};value={}
  for line in r.stdout.splitlines():
   require('='in line,'malformed permanent service property')
   name,field=line.split('=',1)
   require(name in properties and name not in value,'unexpected or duplicate permanent service property')
   value[name]=field
  require(set(value)==properties and all(value[n]==op[key]['unit'][n]for n in properties),'complete permanent service current custody required')
  pid=int(value['MainPID']);kernel=g.kernel(pid);require(kernel['start_time']==op[key]['start_time']and kernel['boot_id']==op['gateway_after']['boot_id'],'service kernel birth/boot drift');services[unit]=value
 state_raw=read(H/'gateway_state.json');state=json.loads(state_raw,object_pairs_hook=unique);tg=state.get('platforms',{}).get('telegram',{})
 require(state.get('pid')==174854 and state.get('start_time')==1454011 and state.get('gateway_state')=='running'and state.get('active_agents')==0 and state.get('active_work')is None and state.get('restart_requested')is False and state.get('session_store',{}).get('status')=='ok'and tg.get('state')=='connected'and tg.get('needs_attention')is False and tg.get('writer_pid')==174854 and tg.get('writer_start_time')==1454011,'actual current same writer not healthy/quiescent')
 for name in ('cmdline','environ'):
  raw=(Path('/proc')/str(state['pid'])/name).read_bytes();require(not any(v in raw for v in PRIVATE_MARKERS),'private preparation path in product process')
 native=g.fresh_native(state) # ONLY this unchanged native transport, never g.check().
 require(read(H/'gateway_state.json')==state_raw,'gateway state drift across current native read')
 return {'installed_product':dict(EXPECTED),'gateway':g.kernel(state['pid']),'native_readonly':native,'services':services}

def origin():
 value=pinned(LINEAGE,LINEAGE_SHA,private=True)
 require(value['state']=='ROOT_READONLY_CURRENT_M14_CANONICAL_SOURCES_AND_NATIVE_BOUNDARY_BOUND_NO_QUERY_AUTHORITY'and value['new_effects']==0 and value['database_path']==str(DB)and value['counts']=={'max_message_id':5504,'messages':5504}and value['exact_original_request_match_rows']==[],'exact Root scoped native/source lineage required')
 expected={'id':SID,'source':'telegram','user_id':'8812646969','chat_id':'8812646969','chat_type':'dm','session_key':KEY,'profile_name':'telegram-bot-8812646969','transport_profile':'default'}
 require(value['session']==expected,'original session/principal mismatch');a=adapter()
 require([r['id']for r in value['selected_native_user_rows']]==[3119,3124,4906],'exact original source row set required')
 for row in value['selected_native_user_rows']:
  src=row['actual_received_source'];rel=row['native_record_relative_source'];want=a.SOURCES[0 if row['id']in(3119,3124)else 1]
  require(row['session_id']==SID and row['role']=='user'and row['platform_message_id']==('4181'if row['id']in(3119,3124)else'4665')and not Path(rel).is_absolute()and rel.startswith('received/telegram_')and '..'not in Path(rel).parts and str(H/'profiles/telegram-bot-8812646969/workspace'/rel)==src['path']and rel in row['content']and src['bytes']==want['bytes']and src['sha256']==want['sha256'],'actual scoped relative native origin/source tuple mismatch')
  raw=read(src['path']);require(len(raw)==src['bytes']and digest(raw)==src['sha256']and identity(Path(src['path']).stat())==src['identity'],'current received original bytes/identity drift')
 return value

def database(lineage):
 # No checkpoint/reset/copy/WAL manipulation. Only existing read-only SQLite
 # transaction, selected immutable origin rows and this SID's bounded user rows.
 require(not any(p.is_symlink()for p in(DB,*DB.parents)),'native DB symlink refused')
 before=DB.stat();db_identity={k:identity(before)[k]for k in('device','inode','uid','gid','mode','nlink')}
 require(stat.S_ISREG(before.st_mode)and before.st_uid==os.getuid()and before.st_nlink==1 and not stat.S_IMODE(before.st_mode)&0o002,'unsafe actual native DB custody')
 with contextlib.closing(sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True,timeout=2))as con:
  con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
  count,maximum=con.execute('SELECT count(*),max(id) FROM messages').fetchone()
  require({'messages':count,'max_message_id':maximum}==lineage['counts'],'native aftermax/count drift; reconcile before any query')
  session=con.execute('SELECT '+','.join(SESSION_FIELDS)+' FROM sessions WHERE id=?',(SID,)).fetchone();require(session is not None and dict(zip(SESSION_FIELDS,session))==lineage['session'],'actual native authorization/session drift')
  rows=con.execute('SELECT '+','.join(ROW_FIELDS)+' FROM messages WHERE id IN (3119,3124,4906) ORDER BY id').fetchall()
  require(len(rows)==3,'native source rows missing')
  for row,old in zip(rows,lineage['selected_native_user_rows']):require(dict(zip(ROW_FIELDS,row))=={k:old[k]for k in ROW_FIELDS},'actual native source serialization drift')
  users=con.execute("SELECT id,platform_message_id,content FROM messages WHERE session_id=? AND role='user' ORDER BY id",(SID,)).fetchall();con.rollback()
 require(len(users)<=5504 and sum(len((r[2]or'').encode())for r in users)<=16*1024*1024,'bounded own-native user history exceeded')
 require({k:identity(DB.stat())[k]for k in db_identity}==db_identity,'native DB identity changed across readonly transaction')
 a=adapter();require(not any(r[2]==a.REQUEST for r in users),'original exact M14 query already present; no replay')
 require(not any(marker.decode()in(r[2]or'')for r in users for marker in PRIVATE_MARKERS),'private preparation/oracle package entered product user history')
 manifest=[[r[0],r[1],digest((r[2]or'').encode())]for r in users]
 return {'database_identity':db_identity,'counts':lineage['counts'],'session':lineage['session'],'selected_rows_sha256':digest(encoded(rows)),'user_history_manifest_sha256':digest(encoded(manifest)),'user_rows':len(users)}

def history():
 a=adapter();records=[];ids=[]
 paths=sorted((STATE/'runs').glob('*.json'));require(len(paths)<=1024,'bounded current run inventory exceeded')
 for path in paths:
  raw=read(path,limit=1024*1024,private=True);row=json.loads(raw,object_pairs_hook=unique);require(row.get('id')==path.stem and raw==encoded(row),'canonical history identity/encoding drift')
  if row['id']==RUN_ID:
   a.shape(RUN_ID,row.get('scenario'));created=dt.datetime.fromisoformat(row['created_at']).timestamp()
   require(row.get('status')=='PREPARED'and row.get('send_state')=='none'and row.get('send_attempts')==0 and row.get('step')==0 and row.get('scenario_sha256')==a.SCENARIO_SHA and 'continuation_reference'not in row and created<=time.time()<row['deadline']<=created+301 and not any(row.get(k)for k in('sent_ids','seen','message_ids','observations','update_count','repeat_count')),'own M14 row is not exact pristine unconsumed query')
   continue
  for step in row.get('scenario',{}).get('steps',[]):require(step.get('request',step.get('input',{}).get('caption'))!=a.REQUEST,'original exact M14 request already retained; no replay')
  records.append([path.name,digest(raw),len(raw)]);ids.append(row['id'])
 return {'records':records,'run_ids':ids,'manifest_sha256':digest(encoded(records))}

def observe():
 """Root may call this finite readonly collector before filling a proof. No grant."""
 current=native203();lineage=origin();native=database(lineage);hist=history();cursor=ref(STATE/'cursor.json');cursor['identity']=identity((STATE/'cursor.json').stat());config=ref(CONFIG);config['identity']=identity(CONFIG.stat())
 require(not(STATE/'observer-stop.json').exists(),'observer stop retained')
 cool=doc(STATE/'cooldown.json')if(STATE/'cooldown.json').exists()else{};require(time.time()>=cool.get('until',0),'cooldown retained')
 raw=read(CONFIG);require(not any(v in raw for v in PRIVATE_MARKERS),'private preparation path in product config')
 resources={'memory_available_bytes':int(next(x.split()[1]for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:')))*1024,'disk_available_bytes':os.statvfs(STATE).f_bavail*os.statvfs(STATE).f_frsize,'affinity_cpus':sorted(os.sched_getaffinity(0))}
 require(resources['memory_available_bytes']>=128*1024**2 and resources['disk_available_bytes']>=64*1024**2 and resources['affinity_cpus'],'minimum bounded text/optional-artifact observation resources unavailable')
 boundary={'history_manifest_sha256':hist['manifest_sha256'],'cursor_sha256':cursor['sha256'],'native_max_id':native['counts']['max_message_id'],'native_boundary_sha256':digest(encoded(native)),'source_origin_review_sha256':LINEAGE_SHA,'phase_unconsumed':'UNBOUND_SEMANTIC_REVIEW_REQUIRED','same_authorized_principal':True,'no_old_effect_replay':'UNBOUND_SEMANTIC_REVIEW_REQUIRED','uploads':0,'producer_calls':0,'restarts':0}
 return {'current':current,'native':native,'history':hist,'cursor':cursor,'profile_config':config,'mutable_boundary':boundary,'origin_review':ref(LINEAGE),'resource_availability':resources}

def shared_slot(owner):
 require(type(owner)is dict and set(owner)=={'pid','start_time','boot_id'},'actual Root shared-slot holder identity required')
 s=SLOT.stat();require(s.st_uid==os.getuid()and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and not any(p.is_symlink()for p in(SLOT,*SLOT.parents)),'shared slot custody changed')
 require(transport().kernel(owner['pid'])==owner,'Root shared-slot owner process changed')
 dev=f'{os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x}:{s.st_ino}';lines=Path('/proc/locks').read_text().splitlines()
 require(any(len(v:=line.split())>=6 and v[1]=='FLOCK'and v[3]=='WRITE'and v[4]==str(owner['pid'])and v[5]==dev for line in lines),'Root does not hold the existing exclusive shared slot')
 return True

def final_native(gateway):
 # Freshness is sampled after current custody/history reads, not only before them.
 with contextlib.closing(sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True,timeout=2))as con:
  con.execute('PRAGMA query_only=ON');con.execute('BEGIN');head=con.execute('SELECT count(*),max(id) FROM messages').fetchone();con.rollback()
 require(head==(5504,5504),'native aftermax at final boundary')
 raw=read(H/'gateway_state.json');state=json.loads(raw,object_pairs_hook=unique)
 require(state.get('pid')==gateway['pid']and state.get('start_time')==gateway['start_time'],'final gateway identity changed')
 native=transport().fresh_native(state)
 require(native.get('identity')==gateway and read(H/'gateway_state.json')==raw,'final native/state CAS changed')
 return native

def check(path,sha):
 proof=pinned(path,sha,private=True);a=adapter();now=time.time();started_monotonic=time.monotonic()
 require(proof.get('schema')=='frw.Root.m14-current203-prequery.v1'and proof.get('operator')=='Root'and proof.get('case')==a.CASE and proof.get('operation_id')==a.OPERATION and proof.get('phase')==a.PHASE and proof.get('scope')==a.SCOPE and proof.get('scenario_sha256')==a.SCENARIO_SHA and proof.get('installed_product')==EXPECTED,'exact M14/current203 Root proof shape required')
 require(type(proof.get('created_at'))in(int,float)and type(proof.get('expires_at'))in(int,float)and math.isfinite(proof['created_at'])and math.isfinite(proof['expires_at'])and proof['created_at']<=now<proof['expires_at']<=proof['created_at']+120,'stale/future Root prequery proof')
 require(type(proof.get('created_monotonic'))in(int,float)and type(proof.get('expires_monotonic'))in(int,float)and math.isfinite(proof['created_monotonic'])and math.isfinite(proof['expires_monotonic'])and 0<=proof['created_monotonic']<=started_monotonic<proof['expires_monotonic']<=proof['created_monotonic']+120,'stale/future Root monotonic prequery proof')
 monotonic_deadline=min(proof['expires_monotonic'],started_monotonic+(proof['expires_at']-now))
 def proof_fresh():
  wall=time.time();monotonic=time.monotonic()
  return proof['created_at']<=wall<proof['expires_at'] and proof['created_monotonic']<=monotonic<monotonic_deadline
 require(proof.get('origin_review')==ref(LINEAGE),'Root original source review pin mismatch');review=readref(proof['history_semantic_review'])
 actual=observe();saved=proof['observed']
 require(proof_fresh(),'Root proof expired during current observation')
 # Native idle generation may stay stable; every actual mutable custody byte,
 # original source, native row and current full inventory must still agree.
 for key in ('native','history','cursor','profile_config','mutable_boundary','origin_review'):require(actual[key]==saved[key],'actual current '+key+' changed since Root issue boundary')
 require(saved['current']['installed_product']==EXPECTED and actual['current']['gateway']==saved['current']['gateway']and actual['current']['services']==saved['current']['services'],'actual installed/service/process tuple changed')
 require(review.get('schema')=='frw.Root.m14-current-history-semantic-review.v1'and review.get('operator')=='Root'and review.get('case')==a.CASE and review.get('operation_id')==a.OPERATION and review.get('phase')==a.PHASE and review.get('history_manifest_sha256')==actual['history']['manifest_sha256']and review.get('native_boundary_sha256')==actual['mutable_boundary']['native_boundary_sha256']and review.get('classified_run_ids')==actual['history']['run_ids']and review.get('equivalent_original_phase_effects')==[]and review.get('compacted_unlogged_semantic_equivalents_reconciled')is True and review.get('old_effects_UNKNOWN_and_clocks_preserved')is True,'Root exact full-history/native semantic once review absent or consumed')
 refs=review.get('retained_basis');require(type(refs)is list and len(refs)>=2,'existing511/14 history basis refs required')
 for r in refs:readref(r)
 require(any(r['path']=='/home/jericho/.cache/FRW-ASTRA-V3-M14-POST203-FORWARD-PREP-20261111/SAVED-LINEAGE-ASSESSMENT.json'and r['sha256']=='d6dc8a1957753ae0cb75c00dbfbaa900d8ef42e9f74aa08026ec4229c201d2ad'for r in refs)and any(r['path']=='/home/jericho/.cache/FRW-ASTRA-V3-M14-POST203-FORWARD-PREP-20261111/ROOT-NEXT.json'and r['sha256']=='8aa436e7740c1a75ba244b96dca15f7b6873d9cd3db1009e1e6576e7e638d43d'for r in refs),'original511/14 scoped history and exact original criterion basis required')
 require(proof.get('private_oracle_excluded_from_product')is True and proof.get('same_ordinary_source_authorization_reviewed')is True,'Root privacy/authorization semantic review absent')
 shared_slot(proof['shared_slot_owner'])
 final=final_native(actual['current']['gateway']);require(final['generation']==actual['current']['native_readonly']['generation'],'native generation changed across current custody checks')
 require(proof_fresh(),'Root proof expired before final admission')
 boundary=dict(actual['mutable_boundary'],phase_unconsumed=True,no_old_effect_replay=True)
 return {'admission':False,'installed_product':dict(EXPECTED),'Root_proof_sha256':sha,'m14_mutable_boundary':boundary,'gateway':actual['current']['gateway'],'native_readonly':final}
