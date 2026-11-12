"""Root reconciles the already returned operation; never repeats installation."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,sqlite3,stat,subprocess
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def birth(pid):return int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
def main():
 j=load(F/'ROOT-NATIVE207-LIVE-OPERATION.json');ret=load(F/'FUTURE-EXECUTION/RETURN.json')
 assert j['state']=='NATIVE207_PROJECT495_FRESH_PERMANENT_SERVICES_RUNNING'and ret['returncode']==0 and ret['boundary_pid_absent']
 assert j['publisher_client_returncode']==0 and j['fresh_default_spec_inspect']and j['full_selected_native_files_readback']and j['selected_native_file_count']==17891
 assert j['publisher_closed_before_parent_custody_release']and j['user_db_wal_shm_verified_before_starts']
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();closed={}
 identities={k:v for k,v in j.items()if k in ['actor_identity','owned_local_process_identity','publisher_client_identity','publisher_process_identity']}
 intent=load(F/'FUTURE-EXECUTION/INTENT.json');identities['caller_identity']=dict(pid=intent['parent_pid'],birth_ticks=intent['parent_birth_ticks'])
 for k,v in identities.items():
  assert v.get('boot_id',j['actor_identity']['boot_id'])!=boot or not Path('/proc',str(v['pid'])).exists()or birth(v['pid'])!=v['birth_ticks']
  closed[k]=v
 assert not Path('/proc',str(ret['boundary_pid'])).exists()
 services={};keys='LoadState,ActiveState,SubState,MainPID,ControlPID,InvocationID,ControlGroup,UnitFileState,RuntimeMaxUSec,NRestarts'
 for label,unit in [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]:
  out=subprocess.check_output(['/usr/bin/systemctl','--user','show',unit,'--property='+keys],text=True)
  s=dict(line.split('=',1)for line in out.splitlines()if'='in line)
  assert all(s[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items())
  pid=int(s['MainPID']);ticks=birth(pid)
  expected=j['gateway_after']['unit']if label=='gateway'else j['dashboard_after']['unit']
  assert all(s[k]==expected[k]for k in ['MainPID','ControlPID','InvocationID','ControlGroup'])
  assert '0::'+s['ControlGroup']in Path('/proc',str(pid),'cgroup').read_text().splitlines()
  services[label]=dict(pid=pid,birth_ticks=ticks,boot_id=boot,unit=unit,invocation_id=s['InvocationID'],cgroup=s['ControlGroup'],state='active/running',runtime_max='infinity',restarts=0)
 state=load(H/'gateway_state.json');assert state['pid']==services['gateway']['pid']and state['start_time']==services['gateway']['birth_ticks']and state['gateway_state']=='running'
 assert state['served_profiles']==['default','dest_telegram','telegram-bot-8812646969']and state['platforms']['telegram']['state']=='connected'
 assert state['active_agents']==0 and state['active_work']is None and state['restart_requested']is False
 dbs={}
 for label,rel in [('default','state.db'),('dest','profiles/dest_telegram/state.db'),('tester','profiles/telegram-bot-8812646969/state.db')]:
  with sqlite3.connect((H/rel).as_uri()+'?mode=ro',uri=True,timeout=1)as db:
   db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
   row=dict(quick_check=db.execute('PRAGMA quick_check').fetchone()[0],leases=db.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0],messages=db.execute('SELECT count(*) FROM messages').fetchone()[0],sessions=db.execute('SELECT count(*) FROM sessions').fetchone()[0],all_origin_pending_delegations=db.execute("SELECT count(*) FROM async_delegations WHERE state IN ('running','stalling','finalizing') OR delivery_state IN ('pending','claimed','deferred')").fetchone()[0]);db.rollback()
  assert row['quick_check']=='ok'and row['leases']==row['all_origin_pending_delegations']==0
  assert all(row[k]==load(F/'ROOT-ACTUAL-CURRENT206-OBSERVATION.json')['databases'][label][k]for k in ['messages','sessions'])
  dbs[label]=row
 receipt=load(H/'hermes-agent.source.json');marker=load(H/'FRIDAY-INSTALL.json');stamp=load(H/'hermes-agent/install-stamp.json');q=load(F/'ROOT-FRESH-REQUEST.json')
 assert ref(H/'hermes-agent.source.json')['sha256']=='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b'
 assert len(receipt['layers'])==207 and len(receipt['files'])==17891 and receipt['source_file_count']==17730 and len(marker['plugin_files'])==52
 assert marker['input_sha256']==q['current_input']['sha256']and ref(q['current_input']['path'])==q['current_input']and len(load(q['current_input']['path'])['project_files'])==495
 assert marker['source_receipt_sha256']==ref(H/'hermes-agent.source.json')['sha256']and stamp['fridaySource']['layers']==receipt['layers']
 tx=H/'preparation'/('ordinary-source-update-v45-'+ref(F/'ROOT-FRESH-REQUEST.json')['sha256'][:16])
 assert (tx/'committed.json').is_file()and not(tx/'rolled-back.json').exists()and ref(tx/'request.json')['sha256']==ref(F/'ROOT-FRESH-REQUEST.json')['sha256']
 fd=os.open('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock',os.O_RDONLY|os.O_NOFOLLOW)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 finally:os.close(fd)
 result=dict(schema='friday.root.actual207.complete-closure.v1',state='INSTALLED207_PROJECT495_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED',
  at_moscow=datetime.datetime.now().astimezone().isoformat(),operation=ref(F/'ROOT-NATIVE207-LIVE-OPERATION.json'),root_return=ref(F/'FUTURE-EXECUTION/RETURN.json'),
  source_acceptance=ref(F/'ROOT-207-SOURCE-ACCEPTANCE.json'),root_source_decision=ref(B/'F06-COHERENT207-ROOT-SOURCE-ACCEPTANCE-20261112.json'),
  installed=dict(layers=207,project=495,native=17891,plugins=52,base=17730,canonical4=dict(marker=ref(H/'FRIDAY-INSTALL.json'),source_receipt=ref(H/'hermes-agent.source.json'),stamp=ref(H/'hermes-agent/install-stamp.json'),current_input=q['current_input'])),
  canonical_CP207=ref(tx/'request.json'),committed=ref(tx/'committed.json'),publisher_client_code=0,fresh_DEFAULT_code=0,complete_root_boundary_code=0,
  full_selected_native_files_readback=True,selected_native_file_count=17891,current_services=services,telegram='connected/3servedprofiles',databases=dbs,
  DB_WAL_SHM='Byteexact before starts verified by actor; after starts logical counts/quickcheck/leases. No blanket live-WAL byteexact claim.',
  slot_free=True,actors_and_boundary_closed=True,closed_actor_identities=closed,operation_elapsed_seconds=j['elapsed_seconds'],
  no_model_create_send_Office_or_worker_task=True,source_provenance=dict(mode='local-committed-main',commit='fddb0abc70ea9d1caed3dbd5186a0a0b52166e46',remote_publication_claim=None),
  retained_limits=['R104 semantic FAIL and M14 historical partial/UNKNOWN not regraded or replayed.','AppF06template18PARTIAL and newclass1TERMINALSTOP remain; four source gates synthetic only. Standard3.2 data_integrity_verified=false/notMAC; modernODTcode installed207 but samebytesnative/user qualification pending.','Journaled rollback does not prove power-loss atomicity.'],
  next='Assess installed207 modernODT on same savedbytes through justified separate finite operation; firstordinaryF06 source/admission/currentproof stillfuture and oldM14notreplayed. SourceTask26optionalcleanup, SolTask27observedErrorCodeRequest args compatibility. No producer/model/send replay.',complete_V3=False)
 path=B/'CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w')as o:json.dump(result,o,sort_keys=True,indent=2);o.write('\n');o.flush();os.fsync(o.fileno())
 print(json.dumps(dict(state=result['state'],proof=ref(path),canonical_CP207=result['canonical_CP207'],current_services=services,databases=dbs)))
if __name__=='__main__':main()
