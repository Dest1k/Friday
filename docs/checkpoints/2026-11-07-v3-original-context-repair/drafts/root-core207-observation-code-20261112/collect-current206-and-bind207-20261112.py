"""Actual Root read-only current206 observations and separate future207 authority.
No maintenance/service/source transaction is started here.
"""
from pathlib import Path
import datetime, fcntl, hashlib, importlib.util, json, os, sqlite3, stat, subprocess, time
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
R=H.parent.parent
os.umask(0o077)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def load(p):return json.loads(Path(p).read_bytes())
def birth(pid):return int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
def run(argv):return subprocess.run(argv,capture_output=True,text=True,check=True,timeout=10).stdout
def show(unit,keys):return dict(x.split('=',1)for x in run(['/usr/bin/systemctl','--user','show',unit,'--property='+','.join(keys)]).splitlines()if'='in x)
def save(p,v):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w')as o:json.dump(v,o,indent=2,sort_keys=True);o.write('\n');o.flush();os.fsync(o.fileno())
def main():
 assert not (F/'ROOT-207-CURRENT-SERVICE-ANCHOR.json').exists()
 assert sha(F/'SOURCE-PINS.json')=='cdc06817972650d8a35778960b8ad28553b5600999a4ef078637499968e6bdb4'
 pins=load(F/'SOURCE-PINS.json')
 for path,digest in {**pins['source_refs'],**pins['historical_refs']}.items():assert sha(path)==digest
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 pred=load(F/'ROOT-ACTUAL206-PREDECESSOR.json');old=load(pred['root_journal']['path'])
 assert sha(pred['root_journal']['path'])==pred['root_journal']['sha256']and old['publisher_closed_before_parent_custody_release']
 oldprocesses={}
 for key in ['actor_identity','owned_local_process_identity','publisher_client_identity','publisher_process_identity']:
  row=old[key];pid=row['pid'];ticks=row['birth_ticks'];b=row.get('boot_id',old['actor_identity']['boot_id'])
  assert b!=boot or not Path('/proc',str(pid)).exists()or birth(pid)!=ticks
  oldprocesses[key]=dict(pid=pid,birth_ticks=ticks,boot_id=b,original_process_absent=True)
 assert sha(H/'hermes-agent.source.json')=='253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21'
 receipt=load(H/'hermes-agent.source.json');marker=load(H/'FRIDAY-INSTALL.json');stamp=load(H/'hermes-agent/install-stamp.json')
 current_input=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112/INPUT-SOURCE206.json')
 assert sha(current_input)==marker['input_sha256']and len(load(current_input)['project_files'])==493
 assert len(receipt['layers'])==206 and len(receipt['files'])==17891 and len(marker['plugin_files'])==52
 assert marker['input_sha256']=='e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39'
 assert stamp['fridaySource']['layers']==receipt['layers']and stamp['fridaySource']['baseTree']==receipt['base_tree']
 services={};envs={};keys=['LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','InvocationID','UnitFileState','RuntimeMaxUSec','NRestarts']
 for label,unit in [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]:
  s=show(unit,keys);pid=int(s['MainPID']);ticks=birth(pid)
  assert all(s[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items())
  assert '0::'+s['ControlGroup']in Path('/proc',str(pid),'cgroup').read_text().splitlines()
  selected={'HERMES_HOME','HERMES_GATEWAY_LOCK_DIR','HERMES_RUNTIME_DIR','HERMES_INSTALL_ROOT','HERMES_PROFILE'}
  env={k.decode():v.decode()for row in Path('/proc',str(pid),'environ').read_bytes().split(b'\0')for k,sep,v in [row.partition(b'=')]if sep and k.decode()in selected}
  assert env.get('HERMES_HOME')==str(H)and birth(pid)==ticks
  services[label]=dict(pid=pid,birth_ticks=ticks,boot_id=boot,invocation_id=s['InvocationID'],cgroup=s['ControlGroup'],enabled_active=True,runtime_max='infinity');envs[label]=env
 tester=Path('/home/jericho/.local/share/friday-telegram-bot-test')
 assert not os.path.lexists(tester/'observer-stop.json')
 cooldown=load(tester/'cooldown.json')if(tester/'cooldown.json').exists()else{}
 assert cooldown.get('until',0)<=time.time()
 locks={};slot=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
 for path in [slot,H/'.hermes-update-in-progress.lock']:
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  try:
   s=os.fstat(fd);assert stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[str(path)]=[s.st_dev,s.st_ino,s.st_uid,s.st_nlink,stat.S_IMODE(s.st_mode)]
  finally:os.close(fd)
 future=show('frw-astra-native207-install-after206-20261112.service',['LoadState','MainPID','ControlPID','ControlGroup'])
 assert future==dict(LoadState='not-found',MainPID='0',ControlPID='0',ControlGroup='')
 mem=int(next(x.split()[1]for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:')))
 fs=os.statvfs(F);cpus=sorted(os.sched_getaffinity(0));assert mem>8*1024**2 and fs.f_bavail*fs.f_frsize>16*1024**3 and len(cpus)>=2
 head=run(['git','-C',str(R),'--no-optional-locks','rev-parse','HEAD']).strip()
 acceptance=load(F/'ROOT-207-SOURCE-ACCEPTANCE.json')
 assert acceptance['source_provenance']==dict(mode='local-committed-main',commit=head)and acceptance['public_main_sha']is None
 origin=run(['git','-C',str(R),'--no-optional-locks','remote','get-url','origin']).strip();assert origin=='https://github.com/Dest1k/Friday.git'
 # Source/kernel/resource work is complete before current-work observation.
 raw=(H/'gateway_state.json').read_bytes();state=json.loads(raw);tg=state['platforms']['telegram']
 assert state['pid']==services['gateway']['pid']and state['start_time']==services['gateway']['birth_ticks']and state['gateway_state']=='running'
 assert state['served_profiles']==['default','dest_telegram','telegram-bot-8812646969']and state['active_agents']==0 and state['active_work']is None and state['restart_requested']is False
 assert tg['state']=='connected'and tg['needs_attention']is False and state['session_store']['status']=='ok'
 spec=importlib.util.spec_from_file_location('Root_actual_current206_native_readonly',F/'native_scope.py');transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
 native=transport.fresh_native(state);assert native['quiescent']and(H/'gateway_state.json').read_bytes()==raw
 databases={};spools={};deadline=time.monotonic()+15
 for label,rel in [('default','state.db'),('dest','profiles/dest_telegram/state.db'),('tester','profiles/telegram-bot-8812646969/state.db')]:
  path=H/rel
  with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=1)as db:
   db.set_progress_handler(lambda:int(time.monotonic()>=deadline),10000);db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
   row=dict(quick_check=db.execute('PRAGMA quick_check').fetchone()[0],leases=db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0],messages=db.execute('SELECT count(*) FROM messages').fetchone()[0],sessions=db.execute('SELECT count(*) FROM sessions').fetchone()[0],all_origin_pending_delegations=db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0])
   assert row['quick_check']=='ok'and row['leases']==row['all_origin_pending_delegations']==0
   databases[label]=row;db.rollback()
  spool=path.parent/'pending_messages';rows=list(spool.iterdir())if spool.is_dir()else[]
  assert not rows;spools[label]=dict(present=spool.exists(),pending_entries=0)
 assert(H/'gateway_state.json').read_bytes()==raw and time.monotonic()-native['global_work']['observed_monotonic']<=15
 at=datetime.datetime.now().astimezone().isoformat()
 obs=dict(schema='frw.root207.actual-current206-observation.v1',at_moscow=at,boot_id=boot,
  services=services,process_environment=envs,old206_processes=oldprocesses,native_readonly=native,databases=databases,pending_message_spools=spools,
  cooldown=cooldown,locks_free=locks,future_publisher_absent=future,memory_available_kib=mem,disk_available_bytes=fs.f_bavail*fs.f_frsize,cpus=cpus,
  all_profile_basis='Global gateway active-work aggregate0, native globalrunner activekeys empty, globalterminal/web QUIESCENT, all3stores leases0 and ALL-origin pending/live delegations0, all3 durable pending-message spools empty. Scoped tester queue/cancel/approvals fields are separately quiescent.',
  projection_limit='ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED. Other-profile in-memory pending queues/approvals are not individually exposed by installed ordinary-turn-readonly; no claim of observing those fields. Existing normal service shutdown owns preservation/drain of queues, not broad cancellation.',
  old_effects_clocks_preserved=True,head=head,origin_url=origin,provenance_mode='local-committed-main',remote_publication_claim=None)
 save(F/'ROOT-ACTUAL-CURRENT206-OBSERVATION.json',obs)
 anchor=load(F/'ROOT-207-CURRENT-SERVICE-ANCHOR-TEMPLATE.json');anchor.pop('required_state_after_actual_Root_readback')
 anchor.update(state='ROOT_ACTUAL_CURRENT206_BOUNDARY',template_only_no_execution_grant=False,boot_id=boot,observed_at_moscow=at,
  evidence=[ref(F/'ROOT-ACTUAL-CURRENT206-OBSERVATION.json')],historical_refs=pins['historical_refs'],services=services,process_environment=envs)
 anchor['quiescence_basis']['root_current_all_profile_pending_approval_cancel_maintenance_evidence']=[ref(F/'ROOT-ACTUAL-CURRENT206-OBSERVATION.json')]
 anchor['quiescence_basis']['limits'].append('ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED')
 anchor['checks']={k:True for k in anchor['checks']}
 save(F/'ROOT-207-CURRENT-SERVICE-ANCHOR.json',anchor)
 auth=load(F/'ROOT-207-RUNTIME-AUTHORITY-TEMPLATE.json')
 auth.update(state='ROOT_REVIEWED_EXACT207_FUTURE_EXECUTION',template_only_no_execution_grant=False,future_finite_operation_reviewed=True,
  old_effects_clocks_preserved=True,modern207_accepted_source_only_not_runtime_qualified=True,execution_commit=head,origin_url=origin,provenance_mode='local-committed-main',public_main_sha=None,
  source_pin_manifest=ref(F/'SOURCE-PINS.json'),source_acceptance=ref(F/'ROOT-207-SOURCE-ACCEPTANCE.json'),actual206_predecessor=ref(F/'ROOT-ACTUAL206-PREDECESSOR.json'),
  boundary=ref(F/'f06-207-first-actual-root.py'),caller=ref(F/'start_core207_once.py'),
  current_service_anchor=ref(F/'ROOT-207-CURRENT-SERVICE-ANCHOR.json'),shared_slot_identity=locks[str(slot)])
 save(F/'ROOT-207-RUNTIME-AUTHORITY.json',auth)
 print(json.dumps(dict(state='ACTUAL_CURRENT206_OBSERVED_FUTURE207_AUTHORITY_BOUND',at_moscow=at,anchor=ref(F/'ROOT-207-CURRENT-SERVICE-ANCHOR.json'),authority=ref(F/'ROOT-207-RUNTIME-AUTHORITY.json'),databases=databases)))
if __name__=='__main__':main()
