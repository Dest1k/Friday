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

def copy_private(source,target,expected=None):
 raw,pin=c.stable(source)
 if expected is not None:c.need(all(pin[k]==expected[k] for k in ('bytes','sha256')),'BEFORE_COPY_SHA')
 fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return pin

def stage(mode,op,a):
 inputs=op/'inputs';inputs.mkdir(mode=0o700)
 _,_,_,ref,_=c.plain_inputs()
 secret=Path(ref['path']);_,sp=c.private(secret,c.P);c.need(sp['sha256']==ref['sha256'],'SECRET_EXACT_REF')
 # Credential is read/copied only here, inside an already admitted finite unit.
 copy_private(secret,inputs/'credential.private.json',sp)
 if mode=='generate':
  obj,mp,rows,_,_=c.plain_inputs();(inputs/'plain-inputs').mkdir(mode=0o700)
  copy_private(c.P/'PLAIN-INPUTS.json',inputs/'PLAIN-INPUTS.json',mp)
  for p in rows:copy_private(p['path'],inputs/'plain-inputs'/Path(p['path']).name,p)
  digest=mp['sha256'];pins=rows
 else:
  raw,mp=c.private(a['reconciled_manifest']['path'],c.B);c.need(all(mp[k]==a['reconciled_manifest'][k] for k in ('bytes','sha256','identity')),'RECONCILED_MANIFEST_PIN')
  obj,pins=c.reconciled_inputs(raw,mp);(inputs/'encrypted-inputs').mkdir(mode=0o700)
  copy_private(mp['path'],inputs/'RECONCILED-INPUTS.json',mp)
  for p in pins:copy_private(p['path'],inputs/'encrypted-inputs'/Path(p['path']).name,p)
  digest=mp['sha256']
 c.save(inputs/'STAGED.json',dict(input_sha256=digest,source_pins=pins,credential_source=sp))
 return inputs,pins

def root_parent(op,admission_sha,a,unit):
 raw,pin=c.private(op/'PARENT-BINDING.json',c.B);v=json.loads(raw)
 c.need(v['root_uid']==os.getuid() and v['boot_id']==a['boot_id'] and v['admission_sha256']==admission_sha and v['unit']==unit and v['nonce']==a['nonce'],'ROOT_PARENT_BINDING_SCOPE')
 proc=Path('/proc',str(v['root_pid']));c.need(proc.stat().st_uid==os.getuid(),'ROOT_PARENT_UID')
 now=(proc/'stat').read_text().rsplit(') ',1)[1].split()[19];c.need(now==v['root_starttime'],'ROOT_PARENT_BIRTH')
 fdpath=proc/'fd'/str(v['slot_fd']);s=fdpath.stat();c.need(c.identity(s)==v['slot_identity']==a['slot_identity'],'ROOT_PARENT_HELD_SLOT_IDENTITY')
 info=(proc/'fdinfo'/str(v['slot_fd'])).read_text();c.need(any('FLOCK  ADVISORY  WRITE' in line or 'FLOCK ADVISORY WRITE' in ' '.join(line.split()) for line in info.splitlines() if line.startswith('lock:')),'ROOT_PARENT_FLOCK_ACTUALLY_HELD')
 return v

def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('--admission',type=Path,required=True);p.add_argument('--admission-sha256',required=True);a=p.parse_args()
 raw,ap=c.private(a.admission,c.B);c.need(ap['sha256']==a.admission_sha256,'ADMISSION_SHA');ad=json.loads(raw)
 mode=ad['mode'];lim=c.limits(mode);key=ad['operation_key'];op=c.operation(key,mode);unit=c.unit_name(key)
 c.need(a.admission==c.B/(key+'.ADMISSION.json'),'ADMISSION_EXACT_PATH')
 recipepin,_=c.recipe_check();c.need(ad['state']=='ROOT_FRESH_ONCE_ADMITTED' and ad['assignment']==c.ASSIGNMENT and ad['source_pins_sha256']==recipepin['sha256'] and ad['limits']==lim,'UNIT_ROOT_ADMISSION_SCOPE')
 cg,origin,props=context(unit,lim);c.DEADLINE=origin+lim['whole_wall_seconds']
 c.need(ad['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'UNIT_BOOT')
 c.safe_dir(op);root_parent(op,a.admission_sha256,ad,unit);c.need(not os.path.lexists(op/'UNIT-INTENT.json') and not os.path.lexists(op/'work'),'UNIT_NO_REPLAY')
 report=dict(state='FAILED_OR_PARTIAL_PRESERVED_NO_REPLAY',unit=unit,mode=mode,operation_key=key,cgroup=str(cg),original_unit_start_monotonic=origin,namespace_closed=False)
 c.save(op/'UNIT-INTENT.json',report);process=None;pidfd=None;logs=[];before=None
 def interrupt(signum,_):raise InterruptedError('UNIT_SIGNAL')
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
 try:
  c.within(lim['cleanup_reserve_seconds']);before=c.bank_snapshot()
  inputs=None;pins=[]
  if mode!='preflight':inputs,pins=stage(mode,op,ad)
  work=op/'work';work.mkdir(mode=0o700)
  logs=[(op/'bwrap.stdout.private').open('xb'),(op/'bwrap.stderr.private').open('xb')]
  argv=c.bwrap(work,inputs,mode,key,origin,ad['nonce'])
  # try/finally owns the Popen object before pidfd/proof/save can raise.
  process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=logs[0],stderr=logs[1],env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},close_fds=True,preexec_fn=lambda:child_limits(lim))
  pidfd=os.pidfd_open(process.pid,0)
  report['namespace_pid']=process.pid;report['namespace_starttime']=Path('/proc',str(process.pid),'stat').read_text().rsplit(') ',1)[1].split()[19]
  while process.poll() is None:
   c.within(lim['cleanup_reserve_seconds']);root_parent(op,a.admission_sha256,ad,unit);c.need(cpu(cg)<lim['aggregate_CPU_seconds']-.25,'AGGREGATE_CGROUP_CPU')
   c.need(tree_bytes(c.B)+lim['namespace_tmpfs_bytes']<=lim['own_cap_bytes'],'OWN_DISK_DECLARED_CAP_MONITOR')
   time.sleep(.025)
  report['namespace_exit']=process.wait();c.need(report['namespace_exit']==0,'NAMESPACE_TERMINAL_NONZERO')
  c.need(c.bank_snapshot()==before,'BANK_AFTER_CAS')
  for pin in pins:
   _,now=c.stable(pin['path']);c.need(now==pin,'ORIGINAL_INPUT_AFTER_CAS')
  c.recipe_check();c.need(c.private(a.admission,c.B)[1]==ap,'ADMISSION_AFTER_CAS')
  report['state']='FINITE_UNIT_CONSUMER_FINISHED_ORACLE_RESULT_SEPARATE'
 except BaseException as error:
  report['error_class']=type(error).__name__;report['reason_code']=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z][A-Z0-9_]{0,100}',str(error)) else None
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
  report['whole_cgroup_CPU_seconds']=cpu(cg);report['elapsed_whole_unit_seconds']=time.monotonic()-origin
  report['CPU_monitor_is_aggregate_sampled_not_atomic']=True;report['disk_cap_is_declared_plus_sampled_not_atomic_quota']=True
  report['completed_at_moscow']=c.utcmoscow();c.save(op/'UNIT-RESULT.json',report)
 print(json.dumps({k:report[k] for k in ('state','namespace_closed','elapsed_whole_unit_seconds')}))
 return 0 if report['state']=='FINITE_UNIT_CONSUMER_FINISHED_ORACLE_RESULT_SEPARATE' else 1
if __name__=='__main__':raise SystemExit(main())
