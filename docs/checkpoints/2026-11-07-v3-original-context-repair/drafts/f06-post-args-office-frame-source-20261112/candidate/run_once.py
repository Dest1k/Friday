"""Exact finite-unit consumer. No standalone execution or implicit admission."""
import argparse,json,os,re,resource,signal,stat,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
import f06_contract as c

def cpu(cg):return int(dict(x.split() for x in (cg/'cpu.stat').read_text().splitlines())['usage_usec'])/1e6

def tree_bytes(root):
 total=count=0
 def visit(fd):
  nonlocal total,count
  for name in os.listdir(fd):
   count+=1;c.need(count<50000,'OWN_ENTRIES_CAP')
   try:s=os.stat(name,dir_fd=fd,follow_symlinks=False)
   except FileNotFoundError:continue
   if stat.S_ISREG(s.st_mode):total+=s.st_size
   elif stat.S_ISDIR(s.st_mode):
    child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
    try:
     now=os.fstat(child);c.need((now.st_dev,now.st_ino)==(s.st_dev,s.st_ino),'OWN_TREE_DIRECTORY_CAS');visit(child)
    finally:os.close(child)
   elif stat.S_ISSOCK(s.st_mode):pass # own Office profile lock socket only; never traverse
   else:c.need(False,'OWN_TREE_LINK_OR_SPECIAL')
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:visit(fd)
 finally:os.close(fd)
 return total

def context(unit,lim):
 rows=Path('/proc/self/cgroup').read_text().strip().splitlines();c.need(len(rows)==1 and rows[0].startswith('0::/'),'UNIFIED_CGROUP')
 rel=rows[0].split(':',2)[2];c.need(rel.endswith('/'+unit),'EXACT_UNIT_CGROUP');cg=Path('/sys/fs/cgroup')/rel.lstrip('/')
 p=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'--property=ExecMainStartTimestampMonotonic,RuntimeMaxUSec,KillMode'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=3,check=True)
 props=dict(x.split('=',1) for x in p.stdout.splitlines());origin=int(props['ExecMainStartTimestampMonotonic'])/1e6
 c.need(props['KillMode']=='control-group' and props['RuntimeMaxUSec'] in (str(lim['whole_wall_seconds'])+'s',str(lim['whole_wall_seconds']*1000000)+'us','5min' if lim['whole_wall_seconds']==300 else '30s'),'UNIT_ORIGINAL_WALL')
 c.need(0<time.monotonic()-origin<lim['whole_wall_seconds'],'UNIT_ORIGINAL_CLOCK')
 c.need((cg/'memory.max').read_text().strip()==str(lim['memory_bytes']) and (cg/'memory.swap.max').read_text().strip()=='0','GROUP_MEMORY_SWAP')
 quota,period=map(int,(cg/'cpu.max').read_text().split());c.need(quota==period*2 and int((cg/'pids.max').read_text())<=128 and len(os.sched_getaffinity(0))==2,'GROUP_CPU_PIDS_AFFINITY')
 return cg,origin,props

def child_limits(lim):
 for key,value in ((resource.RLIMIT_CPU,lim['aggregate_CPU_seconds']),(resource.RLIMIT_AS,lim['per_process_AS_bytes']),(resource.RLIMIT_FSIZE,lim['per_process_FSIZE_bytes']),(resource.RLIMIT_CORE,0),(resource.RLIMIT_NOFILE,512)):
  resource.setrlimit(key,(value,value))

def matches(actual,expected):
 keys=('path','bytes','sha256','identity')
 c.need(all(actual[k]==expected[k] for k in keys if k in expected),'ORIGINAL_EXACT_PIN')

def copy_private(source,target,expected):
 raw,pin=c.stable(source);matches(pin,expected)
 fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:
  c.need(stream.write(raw)==len(raw),'PRIVATE_COPY_COMPLETE')
  stream.flush();os.fsync(stream.fileno())
 _,copied=c.stable(target)
 c.need(copied['bytes']==pin['bytes'] and copied['sha256']==pin['sha256'],'STAGED_SAME_BYTES')
 return pin,copied

def stage(mode,op,a,custody=None):
 # The caller owns progress before mkdir/copy/save; a failed tuple assignment
 # must not erase the known originals or a partially written target.
 if custody is None:custody={}
 inputs=op/'inputs';custody.update(inputs_path=str(inputs),inputs_created=False,original_expected_pins=[],original_inputs_before=[],copy_attempts=[],stage_completed=False)
 c.need(mode==c.MODE,'READONLY_ORACLE_MODE_ONLY')
 obj,mp,rows,ref=c.output_inputs(a)
 c.need(obj['selected_count']==len(rows)==a['selected_count'] and obj['selected_fixture_ids']==a['selected_fixture_ids'],'STAGE_SELECTED_SCOPE')
 def known(role,pin,fixture_id=None):
  item=dict(role=role,pin={k:pin[k] for k in ('path','bytes','sha256','identity') if k in pin},body_read_attempted=role!='credential_source')
  if fixture_id is not None:item['fixture_id']=fixture_id
  custody['original_expected_pins'].append(item)
 known('manifest',mp)
 for row in rows:
  known('retained_native_output',row,row['fixture_id']);known('native_source_ciphertext',row['native_source_ciphertext'],row['fixture_id'])
 credential_pin=dict(ref)
 known('credential_source',credential_pin)
 custody['original_inputs_before']=[item['pin'] for item in custody['original_expected_pins']]
 custody['selected_fixture_ids']=list(obj['selected_fixture_ids']);custody['selected_count']=len(rows)
 c.diagnostic_acceptance(a)
 inputs.mkdir(mode=0o700);custody['inputs_created']=True;(inputs/'native-outputs').mkdir(mode=0o700)
 pins=[];copies=[]
 def tracked_copy(role,source,target,expected,fixture_id=None):
  attempt=dict(role=role,original_host_pin={k:expected[k] for k in ('path','bytes','sha256','identity') if k in expected},staged_host_path=str(target),copy_is_original=False,copy_completed=False)
  if fixture_id is not None:attempt['fixture_id']=fixture_id
  custody['copy_attempts'].append(attempt)
  original,staged=copy_private(source,target,expected)
  attempt.update(original_host_pin=original,staged_host_pin=staged)
  c.need(original['identity'][:2]!=staged['identity'][:2],'STAGED_DISTINCT_INODE')
  attempt['copy_completed']=True
  copy=dict(role=role,original=original,staged=staged)
  if fixture_id is not None:copy['fixture_id']=fixture_id
  copies.append(copy)
  return original,staged
 original,staged=tracked_copy('manifest',mp['path'],inputs/'NATIVE-OUTPUTS.json',mp)
 pins.append(original)
 names=[]
 for row,pin in zip(obj['fixtures'],rows):
  c.need(row['fixture_id']==pin['fixture_id'],'STAGE_FIXTURE_ID')
  c.need(type(row['staged_name']) is str and Path(row['staged_name']).name==row['staged_name'] and row['staged_name'] not in ('.','..'),'STAGE_BASENAME_ONLY')
  original,staged=tracked_copy('retained_native_output',pin['path'],inputs/'native-outputs'/row['staged_name'],pin,row['fixture_id'])
  pins.extend((original,pin['native_source_ciphertext']))
  names.append(row['staged_name'])
 c.need(set(x.name for x in (inputs/'native-outputs').iterdir())==set(names) and len(names)==len(set(names)),'STAGE_EXACT_OUTPUT_DIRECTORY')
 # The only credential content read is inside this already admitted finite unit.
 # Before/after identity and the original upstream digest are mandatory; no
 # credential values are serialized, printed, or included in process arguments.
 _,identity=c.credential_metadata(ref)
 c.need(identity==a['credential_source_identity'],'CREDENTIAL_PRECOPY_IDENTITY')
 custody['original_expected_pins'][-1]['body_read_attempted']=True
 original,staged=tracked_copy('credential_private_copy',ref['path'],inputs/'credential.private.json',credential_pin)
 custody['original_expected_pins'][-1]['pin'].update(sha256=original['sha256'])
 custody['credential_digest_established_inside_admitted_unit_after_full_metadata_CAS']=True
 c.need(c.credential_metadata(ref)[1]==identity,'CREDENTIAL_POSTCOPY_IDENTITY')
 pins.append(original)
 custody['stage_metadata_attempt']=dict(path=str(inputs/'STAGED.json'),write_completed=False)
 c.save(inputs/'STAGED.json',dict(input_sha256=mp['sha256'],selected_count=len(rows),selected_fixture_ids=obj['selected_fixture_ids'],expected_stores=0,expected_probes=1,source_pins=rows,credential_source=original,copy_custody=copies,staged_ciphertext_inodes_are_new_copies=True,metadata_is_not_execution_authority=True))
 custody['stage_metadata_attempt']['pin']=c.private(inputs/'STAGED.json',inputs)[1]
 custody['stage_metadata_attempt']['write_completed']=True;custody['stage_completed']=True
 return inputs,pins

def readonly_after(a,custody,report):
 # Every observation owns its exception. An early failure must not hide later
 # originals/copies, and an uncompleted stage can never claim preservation.
 report['stage_progress']=custody;report['readonly_custody_after_cas']=False
 report['stage_completed']=bool(custody.get('stage_completed',False))
 namespace_closed=report.get('namespace_closed') is True
 report['custody_observation_scope']='after_owned_namespace_closed' if namespace_closed else 'momentary_namespace_stop_unconfirmed'
 errors=[];originals=[];original_observations=[];copies=[];copy_observations=[]
 report['original_inputs_before']=custody.get('original_inputs_before',[])
 metadata_ok=False
 try:
  obj,mp,rows,ref=c.output_inputs(a)
  c.need(obj['selected_fixture_ids']==custody.get('selected_fixture_ids') and len(rows)==custody.get('selected_count'),'AFTER_SELECTED_SCOPE')
  metadata_ok=True
 except BaseException as error:errors.append(dict(check='original_manifest_and_custody',error_class=type(error).__name__))
 for item in custody.get('original_expected_pins',[]):
  expected=item['pin'];row=dict(role=item['role'],path=expected['path'],cas_verified=False,content_preservation_verified=False)
  if 'fixture_id' in item:row['fixture_id']=item['fixture_id']
  original_observations.append(row)
  try:
   if item['role']=='credential_source' and not item['body_read_attempted']:
    _,identity=c.credential_metadata(a['credential_source']);c.need(identity==expected['identity'],'CREDENTIAL_AFTER_METADATA_CAS')
    row.update(observed_identity=identity,cas_scope='metadata_only',cas_verified=True)
   else:
    _,now=c.stable(expected['path']);row['observed_pin']=now;originals.append(now)
    matches(now,expected);row.update(cas_scope='body_and_full_identity' if namespace_closed else 'momentary_body_and_full_identity',cas_verified=True,content_preservation_verified=namespace_closed)
  except BaseException as error:row['error_class']=type(error).__name__
 inputs=Path(custody['inputs_path']) if 'inputs_path' in custody else None
 for attempt in custody.get('copy_attempts',[]):
  row=dict(role=attempt['role'],path=attempt['staged_host_path'],copy_completed=attempt['copy_completed'],cas_verified=False)
  if 'fixture_id' in attempt:row['fixture_id']=attempt['fixture_id']
  copy_observations.append(row)
  try:
   _,now=c.private(row['path'],inputs);row['observed_pin']=now;copies.append(now)
   c.need(attempt['copy_completed'] and now==attempt.get('staged_host_pin'),'STAGED_COPY_AFTER_CAS');row['cas_verified']=True
  except BaseException as error:row['error_class']=type(error).__name__
 stage_metadata_ok=False
 if 'stage_metadata_attempt' in custody:
  attempt=custody['stage_metadata_attempt'];row=dict(path=attempt['path'],write_completed=attempt['write_completed'],cas_verified=False);report['stage_metadata_after_observation']=row
  try:
   _,now=c.private(row['path'],inputs);row['observed_pin']=now
   c.need(attempt['write_completed'] and now==attempt.get('pin'),'STAGED_METADATA_AFTER_CAS');row['cas_verified']=True;stage_metadata_ok=True
  except BaseException as error:row['error_class']=type(error).__name__
 diagnostic_proof_ok=False
 try:c.diagnostic_acceptance(a);diagnostic_proof_ok=True
 except BaseException as error:errors.append(dict(check='diagnostic_acceptance',error_class=type(error).__name__))
 report['original_inputs_after']=originals;report['original_inputs_after_observations']=original_observations
 report['staged_copies_before']=[dict(role=r['role'],original=r['original_host_pin'],staged=r['staged_host_pin'],copy_is_original=False) for r in custody.get('copy_attempts',[]) if 'staged_host_pin' in r]
 report['staged_copies_after']=copies;report['staged_copies_after_observations']=copy_observations;report['custody_check_errors']=errors
 count=custody.get('selected_count',0)
 report['readonly_custody_after_cas']=bool(namespace_closed and custody.get('stage_completed') and metadata_ok and diagnostic_proof_ok and stage_metadata_ok and count==1 and len(original_observations)==2*count+2 and all(r['cas_verified'] and r['content_preservation_verified'] for r in original_observations) and len(copy_observations)==count+2 and all(r['cas_verified'] for r in copy_observations))
 if not report['readonly_custody_after_cas'] and report['state']!='STOP_UNCONFIRMED':report['state']='FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY'

def root_parent(op,admission_sha,a,unit):
 raw,pin=c.private(op/'PARENT-BINDING.json',c.B);v=json.loads(raw)
 c.need(v['root_uid']==os.getuid() and v['boot_id']==a['boot_id'] and v['admission_sha256']==admission_sha and v['unit']==unit and v['nonce']==a['nonce'],'ROOT_PARENT_BINDING_SCOPE')
 proc=Path('/proc',str(v['root_pid']));c.need(proc.stat().st_uid==os.getuid(),'ROOT_PARENT_UID')
 now=(proc/'stat').read_text().rsplit(') ',1)[1].split()[19];c.need(now==v['root_starttime'],'ROOT_PARENT_BIRTH')
 fdpath=proc/'fd'/str(v['slot_fd']);s=fdpath.stat();c.need(c.identity(s)==v['slot_identity']==a['slot_identity'],'ROOT_PARENT_HELD_SLOT_IDENTITY')
 info=(proc/'fdinfo'/str(v['slot_fd'])).read_text();c.need(any('FLOCK  ADVISORY  WRITE' in line or 'FLOCK ADVISORY WRITE' in ' '.join(line.split()) for line in info.splitlines() if line.startswith('lock:')),'ROOT_PARENT_FLOCK_ACTUALLY_HELD')
 return v

def main():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0));p=argparse.ArgumentParser();p.add_argument('--admission',required=True);p.add_argument('--admission-sha256',required=True);a=p.parse_args()
 a.admission=c.canonical(a.admission)
 raw,ap=c.private(a.admission,c.B);c.need(ap['sha256']==a.admission_sha256,'ADMISSION_SHA');ad=json.loads(raw)
 mode=ad['mode'];lim=c.limits(mode);key=ad['operation_key'];op=c.operation(key,mode);unit=c.unit_name(key)
 c.need(a.admission==c.B/(key+'.ADMISSION.json'),'ADMISSION_EXACT_PATH')
 recipepin,_=c.recipe_check();c.need(ad['state']=='ROOT_FRESH_ONCE_ADMITTED' and ad['assignment']==c.ASSIGNMENT and ad['source_pins_sha256']==recipepin['sha256'] and ad['limits']==lim,'UNIT_ROOT_ADMISSION_SCOPE')
 cg,unit_origin,props=context(unit,lim);origin=ad['original_operation_start_monotonic'];c.DEADLINE=origin+lim['whole_wall_seconds']
 c.need(type(origin) in (int,float) and 0<origin<=unit_origin<=time.monotonic()<c.DEADLINE,'ORIGINAL_ADMISSION_AND_UNIT_CLOCK')
 c.need(ad['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'UNIT_BOOT')
 c.safe_dir(op);root_parent(op,a.admission_sha256,ad,unit);c.need(not os.path.lexists(op/'UNIT-INTENT.json') and not os.path.lexists(op/'work'),'UNIT_NO_REPLAY')
 report=dict(state='FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY',unit=unit,mode=mode,operation_key=key,cgroup=str(cg),original_unit_start_monotonic=unit_origin,original_operation_start_monotonic=origin,namespace_closed=False)
 c.save(op/'UNIT-INTENT.json',report);process=None;pidfd=None;logs=[];before=None;inputs=None;pins=[];custody={}
 report['stage_progress']=custody
 def interrupt(signum,_):raise InterruptedError('UNIT_SIGNAL')
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
 try:
  c.within(lim['cleanup_reserve_seconds']);before=c.bank_snapshot()
  inputs,pins=stage(mode,op,ad,custody)
  work=op/'work';work.mkdir(mode=0o700)
  logs=[(op/'bwrap.stdout.private').open('xb'),(op/'bwrap.stderr.private').open('xb')]
  argv=c.bwrap(work,inputs,mode,key,origin,ad['nonce'])
  # try/finally owns the Popen object before pidfd/proof/save can raise.
  process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=logs[0],stderr=logs[1],env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},close_fds=True,preexec_fn=lambda:child_limits(lim))
  pidfd=os.pidfd_open(process.pid,0)
  report['namespace_pid']=process.pid;report['namespace_starttime']=Path('/proc',str(process.pid),'stat').read_text().rsplit(') ',1)[1].split()[19]
  while process.poll() is None:
   c.within(lim['cleanup_reserve_seconds']);root_parent(op,a.admission_sha256,ad,unit);c.need(cpu(cg)<lim['aggregate_CPU_seconds']-.25,'AGGREGATE_CGROUP_CPU')
   c.need(tree_bytes(op)+lim['namespace_tmpfs_bytes']<=lim['own_cap_bytes'],'OWN_OPERATION_DISK_DECLARED_CAP_MONITOR')
   c.need(tree_bytes(Path(ad['task_retention_root']))+lim['namespace_tmpfs_bytes']<=c.TASK_CAP,'WHOLE_TASK_DECLARED_CAP_MONITOR')
   time.sleep(.025)
  report['namespace_exit']=process.wait();c.need(report['namespace_exit']==0,'NAMESPACE_TERMINAL_NONZERO')
  c.need(c.bank_snapshot()==before,'BANK_AFTER_CAS')
  c.recipe_check();c.need(c.private(a.admission,c.B)[1]==ap,'ADMISSION_AFTER_CAS')
  report['state']='FINITE_UNIT_CONSUMER_FINISHED_ORACLE_RESULT_SEPARATE'
 except BaseException as error:
  report['error_class']=type(error).__name__;report['reason_code']=None
 finally:
  for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:None)
  try:
   if process is not None and process.returncode is None:
    try:
     if pidfd is not None:signal.pidfd_send_signal(pidfd,signal.SIGKILL,None,0)
     else:process.kill()
    except ProcessLookupError:pass
    process.wait(timeout=4)
   report['namespace_closed']=process is None or process.returncode is not None
  except BaseException as error:report['cleanup_error_class']=type(error).__name__;report['namespace_closed']=False
  finally:
   if pidfd is not None:os.close(pidfd)
   for stream in logs:stream.close()
  if not report['namespace_closed']:report['state']='STOP_UNCONFIRMED'
  try:readonly_after(ad,custody,report)
  except BaseException as error:
   report['custody_audit_error_class']=type(error).__name__;report['readonly_custody_after_cas']=False
   if report['state']!='STOP_UNCONFIRMED':report['state']='FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY'
  report['final_dependency_cas']={}
  for label,check in (('bank',lambda:c.need(before is not None and c.bank_snapshot()==before,'BANK_AFTER_CAS')),('source',c.recipe_check),('admission',lambda:c.need(c.private(a.admission,c.B)[1]==ap,'ADMISSION_AFTER_CAS'))):
   try:check();report['final_dependency_cas'][label]=True
   except BaseException as error:report['final_dependency_cas'][label]=False;report.setdefault('dependency_errors',[]).append(dict(check=label,error_class=type(error).__name__))
  if not all(report['final_dependency_cas'].values()) and report['state']!='STOP_UNCONFIRMED':report['state']='FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY'
  report['whole_cgroup_CPU_seconds']=cpu(cg);report['elapsed_whole_unit_seconds']=time.monotonic()-origin
  report['CPU_monitor_is_aggregate_sampled_not_atomic']=True;report['elapsed_from_actual_unit_start_seconds']=time.monotonic()-unit_origin;report['stores_planned']=0;report['expected_probes']=ad['expected_probes'];report['disk_cap_is_declared_plus_sampled_not_atomic_quota']=True
  report['completed_at_moscow']=c.utcmoscow();c.save(op/'UNIT-RESULT.json',report)
 print(json.dumps({k:report[k] for k in ('state','namespace_closed','elapsed_whole_unit_seconds')}))
 return 0 if report['state']=='FINITE_UNIT_CONSUMER_FINISHED_ORACLE_RESULT_SEPARATE' else 1
if __name__=='__main__':raise SystemExit(main())
