"""Inert existing native readonly protocol. Future Root call only; no collector at import."""
import hashlib,json,math,os,socket,stat,struct,time
from pathlib import Path
HOME=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
SID='UNBOUND_ROOT_TESTER_SESSION_ID';KEY='agent:telegram-bot-UNBOUND_ROOT_TESTER_ID:telegram:dm:UNBOUND_ROOT_TESTER_ID';NATIVE_SHA='3a6b003622bc17ff5265e5c5117e0eb1f4572676d967763cb368e80947fc79b4'
def require(ok,why):
 if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def unique(pairs):
 v={}
 for k,value in pairs:require(k not in v,'duplicate JSON key');v[k]=value
 return v
def read(path,limit=24*1024*1024):
 p=Path(path);require(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents)),'absolute no-link path required')
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb')as f:
  b=os.fstat(f.fileno());raw=f.read(limit+1);a=os.fstat(f.fileno())
 identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 require(stat.S_ISREG(b.st_mode)and b.st_uid==os.getuid()and b.st_nlink==1 and not b.st_mode&0o002 and len(raw)<=limit and identity(b)==identity(a)==identity(p.stat()),'unsafe/changed owned evidence')
 return raw

def js(path):return json.loads(read(path),object_pairs_hook=unique)
def pinned(path,sha):
 raw=read(path);require(digest(raw)==sha,'pinned evidence changed: '+Path(path).name);return json.loads(raw,object_pairs_hook=unique)
def kernel(pid):
 parts=(Path('/proc')/str(pid)/'stat').read_text().split();return {'pid':pid,'start_time':int(parts[21]),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def validate_native(snapshot,identity,before,after):
 require(type(before)in(int,float)and type(after)in(int,float)and 0<=after-before<=3,'fresh bounded native observation required')
 observed=snapshot.get('observed_monotonic');require(type(observed)in(int,float)and math.isfinite(observed)and before<=observed<=after,'stale/future native snapshot')
 require(snapshot.get('schema')=='frw.gateway.ordinary-turn-readonly.v1'and snapshot.get('read_only')is True and snapshot.get('answering_pid')==identity['pid']and snapshot.get('birth_ticks')==identity['start_time']and snapshot.get('boot_id')==identity['boot_id'],'native/kernel identity mismatch')
 require(snapshot.get('implementation_sha256')==NATIVE_SHA and snapshot.get('session_id')==SID and snapshot.get('session_key')==KEY and type(snapshot.get('generation'))is int and snapshot['generation']>=0,'exact ordinary principal/SID/implementation required')
 for k in ('active','active_session_keys','turn_tokens','event_message_id','ctx_inbound_message_id','ctx_generation','pending_messages','active_adapters','adapter_generations','queued_events','pending_command','approvals','detached_owned_work','live_owned_delegations','durable_pending_delegations'):
  require(k in snapshot and not snapshot[k],'native active/missing field: '+k)
 for k in ('web_custody','terminal_custody'):
  v=snapshot.get(k,{});require(v.get('status')=='QUIESCENT'and v.get('sessions')==[]and v.get('recovery_blocked')is False,'native custody not quiescent')
 v=snapshot.get('own_web_inflight',{});require(v.get('session_id')==SID and v.get('session_key')==KEY and v.get('generation')==snapshot['generation']and v.get('recovery_blocked')is False and v.get('sessions')==[]and v.get('unretained_calls')==[]and all(v.get(k)is None for k in('event_message_id','task_id','turn_id','user_authority')),'ordinary owned inflight mismatch')
 return {'schema':snapshot['schema'],'read_only':True,'session_id':SID,'session_key':KEY,'generation':snapshot['generation'],'quiescent':True,'identity':identity,'freshness':'BOUNDED3S_SOCKET_PEERCRED_MONOTONIC_KERNEL_STATE_CAS'}
def fresh_native(state):
 before=time.monotonic();identity=kernel(state['pid']);require(identity['start_time']==state['start_time'],'state/kernel mismatch')
 req={'protocol':1,'id':'core208-source-admission-readonly','verb':'ordinary-turn-readonly','params':{'session_key':KEY,'session_id':SID}}
 socketpath=HOME/'gateway.sock';info=socketpath.lstat();require(stat.S_ISSOCK(info.st_mode)and info.st_uid==os.getuid()and not stat.S_IMODE(info.st_mode)&0o077 and not any(p.is_symlink()for p in(socketpath,*socketpath.parents)),'unsafe native socket')
 with socket.socket(socket.AF_UNIX)as sock:
  sock.settimeout(2);sock.connect(str(socketpath));pid,uid,_=struct.unpack('3i',sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12));require(pid==identity['pid']and uid==os.getuid(),'native kernel peer mismatch');sock.sendall((json.dumps(req)+'\n').encode());raw=b''
  while b'\n'not in raw:
   part=sock.recv(65536);require(part and len(raw)+len(part)<=524288,'native response missing/oversized');raw+=part
 require(raw.endswith(b'\n')and raw.count(b'\n')==1,'single native frame required');doc=json.loads(raw,object_pairs_hook=unique);require(doc.get('id')==req['id']and doc.get('ok')is True and doc.get('result',{}).get('accepted')is True,'native request refused/mismatched')
 snapshot=doc['result']['snapshot'];result=validate_native(snapshot,identity,before,time.monotonic());require(kernel(state['pid'])==identity,'kernel identity changed across native read');result['global_work']=dict(scope='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',read_only=True,identity=identity,observed_monotonic=snapshot['observed_monotonic'],global_active_session_keys=snapshot['active_session_keys'],web_custody=snapshot['web_custody'],terminal_custody=snapshot['terminal_custody']);return result
