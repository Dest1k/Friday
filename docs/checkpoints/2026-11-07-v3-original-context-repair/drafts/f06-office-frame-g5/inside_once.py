"""One finite namespace; first-profile81 continuation before one producer only."""
import json,os,re,resource,signal,stat,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,'/recipe')
import f06_contract as c

def birth(p):
 # An unreaped child PID cannot be reused. Keep Popen as cleanup authority even
 # if pidfd acquisition, identity read or proof serialization fails.
 fd=os.pidfd_open(p.pid,0)
 try:
  raw=Path('/proc',str(p.pid),'stat').read_text();info=raw.rsplit(') ',1)[1].split()
  c.need(Path('/proc',str(p.pid)).stat().st_uid==os.getuid(),'CHILD_UID')
  return dict(pid=p.pid,starttime=info[19],pidfd=fd)
 except BaseException:os.close(fd);raise

def stop(p,ref):
 if p is None:return
 if p.returncode is None:
  try:
   if ref is not None:signal.pidfd_send_signal(ref['pidfd'],signal.SIGKILL,None,0)
   else:p.kill() # same unreaped direct child, before any wait/poll
  except ProcessLookupError:pass
  p.wait(timeout=3)
 c.need(p.returncode is not None,'CHILD_NOT_REAPED')

def pipe_closure(pipe):
 # No unlink or repair. A stale filesystem name after forced final cleanup is
 # retained; no kernel socket row means no open endpoint. Bootstrap additionally
 # requires absence of the name before any further Office is permitted.
 rows=[line for line in Path('/proc/net/unix').read_text().splitlines()[1:] if len(line.split())==8 and line.split()[7].endswith('_'+pipe)]
 files=[str(p) for p in Path('/tmp').iterdir() if p.name.endswith('_'+pipe)]
 return dict(owned_pipe_closed=not rows,matching_socket_rows=rows,matching_socket_files=files)

def continuation(record,number,maximum):
 # Only observed wait81 permits a further start; UNKNOWN and cleanup failures
 # are terminal. A successfully connected client irrevocably ends bootstrap.
 c.need(record.get('Office_exit')==81 and record.get('Office_exit_observed_by_wait') is True and record.get('Office_terminal_before_cleanup') is True,'BOOTSTRAP_NOT_ACTUAL_WAIT81')
 c.need(not record['client_ready'] and not record['pipe_accepted'] and not record['producer_entered'] and not record['document_phase_exists'],'BOOTSTRAP_AFTER_READY_FORBIDDEN')
 c.need(record['owned_children_closed'] and record['owned_pipe_closed'] and record['matching_socket_files']==[],'BOOTSTRAP_CLOSURE_REQUIRED')
 c.need(number<maximum,'BOOTSTRAP_START_CAP_EXHAUSTED')
 c.within()

def close_attempt(office,client,oref,cref,record,pipe):
 # Preserve the first cleanup failure even if a final bounded reap succeeds.
 errors=list(record.get('cleanup_errors',[]));record['cleanup_attempted']=True
 for p,ref,label in ((client,cref,'client'),(office,oref,'Office')):
  try:
   stop(p,ref)
   if p is not None:
    record[label+'_exit']=p.wait();record[label+'_exit_observed_by_wait']=True
  except BaseException as error:errors.append(label+':'+type(error).__name__)
  if ref is not None:
   try:os.close(ref['pidfd'])
   except OSError as error:errors.append(label+'_pidfd:'+type(error).__name__)
 record['cleanup_errors']=errors;record['actual_children_terminal']=all(p is None or p.returncode is not None for p in (client,office));record['owned_children_closed']=not errors and record['actual_children_terminal']
 try:record.update(pipe_closure(pipe) if pipe else dict(owned_pipe_closed=True,matching_socket_rows=[],matching_socket_files=[]))
 except BaseException as error:record['owned_pipe_closed']=False;record['pipe_closure_error_class']=type(error).__name__
 return record['owned_children_closed'] and record['owned_pipe_closed']

def mount_guard(mode):
 rows=[x.split() for x in Path('/proc/self/mountinfo').read_text().splitlines()]
 for mount in ('/recipe',c.PREFIX)+(() if mode=='preflight' else ('/inputs',)):
  hits=[r for r in rows if r[4]==mount];c.need(hits and 'ro' in hits[-1][5].split(','),'MOUNT_READONLY')
 # clear network namespace has only loopback and no non-loopback route.
 dev=Path('/proc/net/dev').read_text().splitlines()[2:];c.need(all(x.split(':',1)[0].strip()=='lo' for x in dev),'NETWORK_INTERFACE')
 c.need(len(os.sched_getaffinity(0))==2,'AFFINITY_TWO')

def ownership(p,ref,pipe,profile,observation_path):
 # Collect only this nonce's matching rows. Persist their bounded typed fields
 # before any acceptance/refusal, including malformed/excess/foreign rows.
 proc=Path('/proc',str(p.pid));rows=[]
 observation=dict(state='PIPE_OBSERVATION_NOT_ACCEPTANCE',pid=p.pid,starttime=ref['starttime'],pipe=pipe,profile=str(profile),rows=rows,matching_rows_seen=0,kernel_rows_scanned=0,max_matching_rows=8,max_kernel_rows=4096,max_Office_fds=1024,scan_complete=False)
 try:
  with Path('/proc/net/unix').open() as stream:
   header=stream.readline(4097);c.need(len(header)<=4096,'OWN_PIPE_KERNEL_LINE_BOUND')
   while True:
    line=stream.readline(4097)
    if not line:observation['scan_complete']=True;break
    observation['kernel_rows_scanned']+=1
    c.need(observation['kernel_rows_scanned']<=4096 and len(line)<=4096,'OWN_PIPE_KERNEL_SCAN_BOUND')
    fields=line.split(maxsplit=7)
    if not line.rstrip().endswith('_'+pipe):continue
    observation['matching_rows_seen']+=1
    c.need(len(rows)<8,'OWN_PIPE_MATCHING_ROWS_BOUND')
    if len(fields)!=8:
     rows.append(dict(malformed=True,field_count=len(fields),matches_nonce_suffix=True))
     c.need(False,'OWN_PIPE_MALFORMED_ROW')
    path=Path(fields[7].strip());row=dict(path_is_private_tmp=path.parent==Path('/tmp'),protocol=fields[2][:32],flags=fields[3][:32],type=fields[4][:32],socket_state=fields[5][:32],socket_inode=fields[6][:32],Office_fds=[])
    rows.append(row)
    if row['path_is_private_tmp']:
     row['path']=str(path)
     try:row['identity']=c.identity(path.lstat())
     except OSError as error:row['lstat_error_class']=type(error).__name__
  # Collect Office identity even for a refused cardinality/type, without saving
  # arbitrary cmdline contents or other processes' socket paths.
  before=(proc/'stat').read_text().rsplit(') ',1)[1].split();observation['observed_starttime']=before[19];observation['observed_uid']=proc.stat().st_uid
  exe=(proc/'exe').stat();want=Path(c.PROGRAM,'soffice.bin').stat();observation['executable_identity']=c.identity(exe)
  with (proc/'cmdline').open('rb') as stream:argvraw=stream.read(8193)
  c.need(len(argvraw)<=8192,'OFFICE_ARGV_BOUND')
  observation['argv_sha256']=__import__('hashlib').sha256(argvraw).hexdigest()
  for number,fd in enumerate((proc/'fd').iterdir(),1):
   c.need(number<=1024,'OWN_PIPE_OFFICE_FDS_BOUND')
   try:link=os.readlink(fd)
   except FileNotFoundError:continue
   for row in rows:
    if link=='socket:['+row['socket_inode']+']':row['Office_fds'].append(fd.name)
  for row in rows:
   if row.get('path'):
    try:row['identity_after']=c.identity(Path(row['path']).lstat())
    except OSError as error:row['lstat_after_error_class']=type(error).__name__
  after=(proc/'stat').read_text().rsplit(') ',1)[1].split()
  with (proc/'cmdline').open('rb') as stream:argvafter=stream.read(8193)
  c.need(len(argvafter)<=8192,'OFFICE_ARGV_BOUND')
  observation['identity_stable']=after[19]==before[19] and proc.stat().st_uid==observation['observed_uid'] and c.identity((proc/'exe').stat())==c.identity(exe) and argvafter==argvraw
 except BaseException as error:
  observation['observation_error_class']=type(error).__name__
  observation['observation_reason_code']=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z][A-Z0-9_]{0,100}',str(error)) else None
  c.save(observation_path,observation);raise
 c.save(observation_path,observation)
 c.need(re.fullmatch('f06_'+re.escape(os.environ['FRW_F06_NONCE'])+'_a[1-3]',pipe) is not None and re.fullmatch('[0-9a-f]{32}',os.environ['FRW_F06_NONCE']) is not None,'OWN_PIPE_EXACT_NONCE')
 c.need(observation['observed_starttime']==ref['starttime'] and observation['observed_uid']==os.getuid() and observation['identity_stable'],'OFFICE_BIRTH_UID')
 c.need((exe.st_dev,exe.st_ino)==(want.st_dev,want.st_ino),'OFFICE_EXACT_EXECUTABLE')
 argv=argvraw.split(b'\0')
 c.need(('-env:UserInstallation='+profile.as_uri()).encode() in argv and ('--accept=pipe,name='+pipe+';urp;StarOffice.ComponentContext').encode() in argv,'OFFICE_EXACT_PIPE_PROFILE_ARGV')
 c.need(observation['scan_complete'] and 1<=len(rows)<=8,'OWN_PIPE_ROW_CARDINALITY')
 paths=set();listeners=[];connected=[];inodes=set()
 for row in rows:
  c.need(row['path_is_private_tmp'],'OWN_PIPE_PRIVATE_TMP')
  ident=row.get('identity');c.need(ident and ident==row.get('identity_after') and stat.S_ISSOCK(ident[2]) and ident[3]==os.getuid(),'OWN_PIPE_SOCKET_UID_STABLE')
  paths.add((row['path'],tuple(ident)))
  c.need(row['protocol']=='00000000' and row['type']=='0001' and re.fullmatch('[1-9][0-9]*',row['socket_inode']) is not None,'OWN_PIPE_STREAM_PROTOCOL_INODE')
  c.need(row['socket_inode'] not in inodes,'OWN_PIPE_DISTINCT_INODES');inodes.add(row['socket_inode'])
  c.need(row['Office_fds'] and all(x.isdecimal() for x in row['Office_fds']),'OWN_PIPE_SOCKET_BELONGS_TO_EXACT_OFFICE')
  if (row['flags'],row['socket_state'])==('00010000','01'):listeners.append(row)
  elif (row['flags'],row['socket_state'])==('00000000','03'):connected.append(row)
  else:c.need(False,'OWN_PIPE_UNEXPECTED_FLAGS_STATE')
 c.need(len(paths)==1,'OWN_PIPE_ONE_STABLE_PATH')
 c.need(len(listeners)==1,'OWN_PIPE_EXACT_ONE_LISTENER')
 return dict(state='OWNED_PIPE_PROCESS_PROFILE_OBSERVED',pid=p.pid,starttime=ref['starttime'],uid=os.getuid(),pipe=pipe,profile=str(profile),executable_identity=c.identity(exe),sockets=rows,listening_socket_inode=listeners[0]['socket_inode'],connected_socket_inodes=[r['socket_inode'] for r in connected],observation_path=str(observation_path),argv_sha256=observation['argv_sha256'])

def main():
 os.umask(0o077);mode=os.environ['FRW_F06_MODE'];lim=c.limits(mode);origin=float(os.environ['FRW_F06_UNIT_START']);c.DEADLINE=origin+lim['whole_wall_seconds']-lim['cleanup_reserve_seconds']
 work=c.safe_dir('/work');report=dict(state='FAILED_OR_PARTIAL_PRESERVED',mode=mode,Office_launch_attempts=0,client_launch_attempts=0,Office_starts=0,client_starts=0,producer_permissions=0,owned_children_closed=False,attempts=[],original_unit_start_monotonic=origin,absolute_work_deadline=c.DEADLINE)
 office=client=None;oref=cref=None;streams=[];record=None;pipe=None;attempt=None
 def interrupted(signum,_):raise InterruptedError('OWNED_SIGNAL')
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
 try:
  mount_guard(mode)
  for name in ('home','tmp','cache','config','runtime','profile'):(work/name).mkdir(mode=0o700)
  env=dict(os.environ);env['LD_LIBRARY_PATH']=c.PROGRAM+':'+c.PREFIX+'/root/usr/lib/x86_64-linux-gnu';env['URE_BOOTSTRAP']='vnd.sun.star.pathname:'+c.PROGRAM+'/fundamentalrc'
  maximum=1 if mode=='preflight' else lim['max_Office_starts']
  if mode!='preflight':
   staged=json.loads(c.stable('/inputs/STAGED.json')[0]);env['FRW_F06_INPUT_SHA']=staged['input_sha256']
  for number in range(1,maximum+1):
   c.within();office=client=None;oref=cref=None;record=None
   attempt=work/('attempt-'+str(number));attempt.mkdir(mode=0o700)
   pipe=None if mode=='preflight' else 'f06_'+env['FRW_F06_NONCE']+'_a'+str(number)
   env['FRW_F06_ATTEMPT']=str(attempt);env['FRW_F06_PIPE']=pipe or ''
   record=dict(attempt=number,pipe=pipe,Office_exit=None,client_exit=None,Office_exit_observed_by_wait=False,client_exit_observed_by_wait=False,Office_terminal_before_cleanup=False,client_ready=False,pipe_accepted=False,producer_entered=False,document_phase_exists=False,owned_children_closed=False,owned_pipe_closed=False)
   report['attempts'].append(record)
   if mode!='preflight':
    common=[c.PROGRAM+'/soffice.bin','-env:UserInstallation='+(work/'profile').as_uri(),'--headless','--nologo','--norestore','--nodefault','--nofirststartwizard','--accept=pipe,name='+pipe+';urp;StarOffice.ComponentContext']
    streams += [(attempt/'Office.stdout.private').open('xb'),(attempt/'Office.stderr.private').open('xb')]
    report['Office_launch_attempts']+=1;record['Office_launch_attempted']=True
    office=subprocess.Popen(common,stdin=subprocess.DEVNULL,stdout=streams[-2],stderr=streams[-1],env=env,close_fds=True)
    report['Office_starts']+=1
    oref=birth(office);record['Office_birth']={k:v for k,v in oref.items() if k!='pidfd'}
   streams += [(attempt/'client.stdout.private').open('xb'),(attempt/'client.stderr.private').open('xb')]
   report['client_launch_attempts']+=1;record['client_launch_attempted']=True
   client=subprocess.Popen([c.PROGRAM+'/python','-B','-s','-S','/recipe/embedded_entry.py'],stdin=subprocess.DEVNULL,stdout=streams[-2],stderr=streams[-1],env=env,close_fds=True)
   report['client_starts']+=1
   cref=birth(client);record['client_birth']={k:v for k,v in cref.items() if k!='pidfd'}
   accepted=False;startup_exit=False
   while True:
    c.within()
    if office is not None and office.poll() is not None:
     record['Office_exit']=office.wait();record['Office_exit_observed_by_wait']=True;record['Office_terminal_before_cleanup']=True;startup_exit=True;break
    if not accepted and office is not None and (attempt/'CLIENT-READY.json').exists():
     ready=json.loads(c.stable(attempt/'CLIENT-READY.json')[0])
     c.need(ready['state']=='CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET' and type(ready['component_count']) is int and ready['component_count']==0 and ready['pipe']==pipe and ready['pid']==cref['pid'] and ready['starttime']==cref['starttime'],'CONNECTED_EMPTY_COMPONENTS_ACTUAL_CHILD')
     proof=ownership(office,oref,pipe,work/'profile',attempt/'PIPE-OBSERVATION.json')
     proof['zero_components_client_witness']=ready
     c.need(report['producer_permissions']==0,'ONE_PRODUCER_ONLY')
     c.save(attempt/'PIPE-OWNERSHIP-ACCEPTED.json',proof);accepted=True;report['producer_permissions']+=1
    if client.poll() is not None:break
    time.sleep(.02)
   record.update(client_ready=(attempt/'CLIENT-READY.json').exists(),pipe_accepted=(attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists(),producer_entered=(attempt/'PRODUCER-ENTERED.json').exists(),document_phase_exists=(work/'encrypted-inputs').exists())
   if startup_exit:
    close_attempt(office,client,oref,cref,record,pipe);oref=cref=None
    record.update(client_ready=(attempt/'CLIENT-READY.json').exists(),pipe_accepted=(attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists(),producer_entered=(attempt/'PRODUCER-ENTERED.json').exists(),document_phase_exists=(work/'encrypted-inputs').exists())
    c.save(attempt/'ATTEMPT-RESULT.json',record)
    continuation(record,number,maximum)
    continue
   record['client_exit']=client.wait();record['client_exit_observed_by_wait']=True;c.need(record['client_exit']==0,'CLIENT_TERMINAL_NONZERO')
   c.need(mode=='preflight' or accepted,'PIPE_NOT_ACCEPTED')
   break
  if mode=='preflight':
   typed=json.loads(c.stable(work/'UNO-PREFLIGHT.json')[0]);c.need(typed['pid']==cref['pid'] and typed['starttime']==cref['starttime'] and typed['executable_identity']==c.identity(Path(c.PROGRAM,'python.bin').stat()),'ACTUAL_EMBEDDED_PREFLIGHT_CHILD_JOIN')
  report['state']='ISOLATED_UNO_PREFLIGHT_NO_OFFICE_PASS' if mode=='preflight' else 'ORACLE_CLIENT_FINISHED_SEPARATE_FIXTURE_RESULT'
 except BaseException as error:
  report['error_class']=type(error).__name__
  report['reason_code']=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z][A-Z0-9_]{0,100}',str(error)) else None
 finally:
  # Defer additional signals across cleanup/save, but never ignore SIGKILL.
  for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:None)
  if record is not None:
   record.update(client_ready=(attempt/'CLIENT-READY.json').exists(),pipe_accepted=(attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists(),producer_entered=(attempt/'PRODUCER-ENTERED.json').exists(),document_phase_exists=(work/'encrypted-inputs').exists())
   if not record.get('cleanup_attempted') or not record.get('actual_children_terminal'):close_attempt(office,client,oref,cref,record,pipe)
   if not (attempt/'ATTEMPT-RESULT.json').exists():c.save(attempt/'ATTEMPT-RESULT.json',record)
   else:c.save(attempt/'ATTEMPT-FINAL-CLEANUP.json',record)
  for stream in streams:
   try:stream.close()
   except OSError:pass
  report['cleanup_errors']=[e for r in report['attempts'] for e in r.get('cleanup_errors',[])];report['owned_children_closed']=all(r['owned_children_closed'] for r in report['attempts']);report['owned_pipes_closed']=all(r['owned_pipe_closed'] for r in report['attempts'])
  usage=resource.getrusage(resource.RUSAGE_CHILDREN);report['children_CPU_seconds']=usage.ru_utime+usage.ru_stime;report['children_maxrss_kib']=usage.ru_maxrss;report['elapsed_whole_unit_seconds']=time.monotonic()-origin
  if not report['owned_children_closed'] or not report['owned_pipes_closed']:report['state']='STOP_UNCONFIRMED'
  report['completed_at_moscow']=c.utcmoscow();c.save(work/'INSIDE-RESULT.json',report)
 return 0 if report['state'] in ('ISOLATED_UNO_PREFLIGHT_NO_OFFICE_PASS','ORACLE_CLIENT_FINISHED_SEPARATE_FIXTURE_RESULT') else 1
if __name__=='__main__':raise SystemExit(main())
