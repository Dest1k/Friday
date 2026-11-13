"""Root-only fresh metadata binding. No installation/admission/actor invocation."""
import pathlib,json,runpy,hashlib,os,time,datetime,subprocess,fcntl,stat,types
F=pathlib.Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE209-ROOT-FRAME-PREP-20261113-R2')
D=pathlib.Path(__file__).parent
H=pathlib.Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
R=H.parent.parent
EXPECTED='79faafa439202f0183bf5bda9ae45a96d47c18a92310ef69f8e27ed852b95c7f'
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def run(argv):return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=15).stdout
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
def main():
 os.umask(0o077)
 assert ref(F/'SOURCE-PINS.json')['sha256']==EXPECTED
 assert load(F/'ROOT-209-SOURCE-ACCEPTANCE.json')['accepted'] is True
 b=runpy.run_path(str(F/'core209-first-actual-root.py'))
 contract=types.SimpleNamespace(**runpy.run_path(str(F/'boundary_contract.py')))
 pins=load(F/'SOURCE-PINS.json');boot=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 a=load(F/'ROOT-209-CURRENT-SERVICE-ANCHOR-TEMPLATE.json');services={};envs={};rawunits={}
 for label,unit in [('gateway','hermes-gateway-1b7e7667.service'),('dashboard','hermes-dashboard.service')]:
  keys='LoadState,ActiveState,SubState,MainPID,ControlPID,ControlGroup,InvocationID,UnitFileState,RuntimeMaxUSec,NRestarts'
  t=dict(x.split('=',1)for x in run(['/usr/bin/systemctl','--user','show',unit,'--property='+keys]).splitlines()if '='in x)
  pid=int(t['MainPID']);proc=pathlib.Path('/proc')/str(pid)
  assert all(t[k]==v for k,v in dict(LoadState='loaded',ActiveState='active',SubState='running',ControlPID='0',UnitFileState='enabled',RuntimeMaxUSec='infinity',NRestarts='0').items())
  assert '0::'+t['ControlGroup'] in (proc/'cgroup').read_text().splitlines()
  selected={'HERMES_HOME','HERMES_GATEWAY_LOCK_DIR','HERMES_RUNTIME_DIR','HERMES_INSTALL_ROOT','HERMES_PROFILE'}
  env={k.decode():v.decode()for row in(proc/'environ').read_bytes().split(b'\0')for k,sep,v in[row.partition(b'=')]if sep and k.decode()in selected};assert env['HERMES_HOME']==str(H)
  services[label]=dict(pid=pid,birth_ticks=b['birth'](pid),boot_id=boot,invocation_id=t['InvocationID'],cgroup=t['ControlGroup'],enabled_active=True,runtime_max='infinity');envs[label]=env;rawunits[label]=t
 state_raw=(H/'gateway_state.json').read_bytes();s=json.loads(state_raw);tg=s['platforms']['telegram']
 assert s['pid']==services['gateway']['pid'] and s['start_time']==services['gateway']['birth_ticks'] and s['hermes_home']==str(H)
 assert s['served_profiles']==['default','dest_telegram','telegram-bot-8812646969'] and s['gateway_state']=='running' and s['active_agents']==0 and s['active_work']is None and s['restart_requested']is False and s['session_store']['status']=='ok' and tg['state']=='connected' and tg['needs_attention']is False
 native=runpy.run_path(str(F/'native_scope.py'))['fresh_native'](s)
 dbs=b['readonly_databases']();contract.validate_global_quiescence(native['global_work'],dbs,services['gateway'],current_monotonic=time.monotonic());assert(H/'gateway_state.json').read_bytes()==state_raw
 T=pathlib.Path('/home/jericho/.local/share/friday-telegram-bot-test');assert not os.path.lexists(T/'observer-stop.json')
 cool=load(T/'cooldown.json')if(T/'cooldown.json').exists()else{};assert cool.get('until',0)<=time.time()
 u=dict(x.split('=',1)for x in run(['/usr/bin/systemctl','--user','show',a['future_publisher_unit'],'--property=LoadState,MainPID,ControlPID,ControlGroup']).splitlines()if '='in x);assert u==dict(LoadState='not-found',MainPID='0',ControlPID='0',ControlGroup='')
 locks=[]
 for p in [pathlib.Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock'),T/'consumer.lock',T/'tester-token']:
  fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW)
  try:
   si=os.fstat(fd);assert si.st_uid==os.getuid() and si.st_nlink==1 and stat.S_ISREG(si.st_mode)
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append({'path':str(p),'available':True,'identity':[si.st_dev,si.st_ino,si.st_uid,si.st_nlink,stat.S_IMODE(si.st_mode)]})
  finally:os.close(fd)
 assert locks[0]['identity'][4]==0o600
 mem=int(next(x.split()[1]for x in pathlib.Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:')));fs=os.statvfs(F)
 assert mem>8*1024**2 and fs.f_bavail*fs.f_frsize>16*1024**3 and len(os.sched_getaffinity(0))>=2
 m=types.SimpleNamespace(**runpy.run_path(str(F/'root209_metadata.py')));m.actual_predecessor()
 assert ref(H/'hermes-agent.source.json')['sha256']==a['installed']['receipt_sha256']
 marker=load(H/'FRIDAY-INSTALL.json');receipt=load(H/'hermes-agent.source.json')
 assert marker['input_sha256']==a['installed']['input_sha256'] and(len(receipt['layers']),len(receipt['files']),receipt['source_file_count'],len(marker['plugin_files']))==(208,17891,17730,52)
 assert b['collect_services'](boot,{'services':services,'process_environment':envs},contract)==(services,envs)
 evidence=dict(schema='friday.Root.core209.fresh-anchor-observation.v1',at_moscow=now(),boot=boot,services=services,selected_environment=envs,raw_unit_metadata=rawunits,native=native,all3_databases=dbs,gateway_routing={k:s[k]for k in('served_profiles','active_agents','active_work','restart_requested')},telegram_connected=tg['state'],cooldown=cool,observer_stop_absent=True,future_publisher_absent=u,locks=locks,resources={'memory_available_kib':mem,'disk_available_bytes':fs.f_bavail*fs.f_frsize,'affinity':sorted(os.sched_getaffinity(0))},limitations=a['quiescence_basis']['limits'],no_product_model_user_write_or_new_clock=True)
 e=D/'ROOT209-R2-FRESH-ANCHOR-OBSERVATION.json';save(e,evidence)
 a.pop('required_state_after_actual_Root_readback');a.update(state='ROOT_ACTUAL_CURRENT208_BOUNDARY',template_only_no_execution_grant=False,observed_at_moscow=evidence['at_moscow'],boot_id=boot,services=services,process_environment=envs,historical_refs=pins['historical_refs'],evidence=[ref(e)],checks={k:True for k in a['checks']})
 a['quiescence_basis']['root_current_all_profile_pending_approval_cancel_maintenance_evidence']=[ref(e)]
 contract.validate_anchor(a,current_time=time.time(),boot=boot,historical=pins['historical_refs'],frame=str(F),publisher=a['future_publisher_unit'],home=str(H));save(F/'ROOT-209-CURRENT-SERVICE-ANCHOR.json',a)
 au=load(F/'ROOT-209-RUNTIME-AUTHORITY-TEMPLATE.json');au.update(state='ROOT_REVIEWED_EXACT209_FUTURE_EXECUTION',template_only_no_execution_grant=False,current_service_anchor=ref(F/'ROOT-209-CURRENT-SERVICE-ANCHOR.json'),actual208_predecessor=ref(F/'ROOT-ACTUAL208-PREDECESSOR.json'),source_pin_manifest=ref(F/'SOURCE-PINS.json'),source_acceptance=ref(F/'ROOT-209-SOURCE-ACCEPTANCE.json'),execution_commit='35c85be3a80999ee352a781d4990df3ba955e634',provenance_mode='local-committed-main',origin_url=run(['git','-C',str(R),'remote','get-url','origin']).strip(),public_main_sha=None,shared_slot_identity=locks[0]['identity'],future_finite_operation_reviewed=True,old_effects_clocks_preserved=True,f07_209_accepted_source_only_not_runtime_qualified=True)
 contract.validate_authority(au,manifest=ref(F/'SOURCE-PINS.json'),boundary=ref(F/'core209-first-actual-root.py'),caller=ref(F/'start_core209_once.py'),anchor=ref(F/'ROOT-209-CURRENT-SERVICE-ANCHOR.json'),source_acceptance=ref(F/'ROOT-209-SOURCE-ACCEPTANCE.json'),predecessor=ref(F/'ROOT-ACTUAL208-PREDECESSOR.json'),frame=str(F));save(F/'ROOT-209-RUNTIME-AUTHORITY.json',au)
 print(json.dumps({'state':'FRESH_ROOT_CURRENT208_ANCHOR_AND_EXACT_FUTURE209_AUTHORITY_BOUND','at_moscow':evidence['at_moscow'],'service_pids':{k:v['pid']for k,v in services.items()},'db_messages':{k:v['messages']for k,v in dbs.items()},'no_admission_or_maintenance_yet':True}))
if __name__=='__main__':main()
