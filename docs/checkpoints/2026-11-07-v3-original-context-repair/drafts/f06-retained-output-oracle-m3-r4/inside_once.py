"""Dormant readonly native-edit oracle in the existing finite Root namespace.
Only actual document-free wait81 may continue bootstrap, on one original clock.
"""
import hashlib,json,math,os,re,resource,signal,stat,subprocess,sys,time
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
 # No retry after readiness, permission, entry or any result/document phase.
 # A cleanup-killed Office is not an observed bootstrap wait81.
 c.need(type(record.get('Office_exit')) is int and record['Office_exit']==81 and record.get('Office_exit_observed_by_wait') is True and record.get('Office_terminal_before_cleanup') is True,'BOOTSTRAP_NOT_ACTUAL_WAIT81')
 c.need(all(record.get(key) is False for key in ('client_ready','pipe_accepted','oracle_entered','oracle_result_exists','document_phase_exists')),'BOOTSTRAP_AFTER_READY_FORBIDDEN')
 c.need(record.get('owned_children_closed') is True and record.get('owned_pipe_closed') is True and record.get('matching_socket_files')==[],'BOOTSTRAP_CLOSURE_REQUIRED')
 c.need(type(number) is int and type(maximum) is int and 1<=number<maximum<=3,'BOOTSTRAP_START_CAP_EXHAUSTED')
 c.within()

def native_mode(mode):
 c.need(mode=='verify-native-edits','MODE')
 return mode

def decode(raw):
 def pairs(items):
  obj={}
  for key,value in items:
   c.need(key not in obj,'DUPLICATE_JSON_KEY');obj[key]=value
  return obj
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:c.need(False,'JSON_CONSTANT'))

def selection_contract(staged,manifest,digest,lim):
 # Pure checks of planned effects and selected metadata; no credential reads.
 c.need(type(staged) is dict and type(manifest) is dict,'STAGED_OBJECT')
 count=staged.get('selected_count');ids=staged.get('selected_fixture_ids');order=['f06-'+str(i) for i in range(1,8)]
 c.need(type(count) is int and 1<=count<=7 and type(ids) is list and len(ids)==count and ids==[ident for ident in order if ident in ids],'STAGED_SELECTION')
 c.need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None and staged.get('input_sha256')==digest,'STAGED_MANIFEST_DIGEST')
 c.need(type(staged.get('expected_stores')) is int and staged['expected_stores']==0 and type(staged.get('expected_probes')) is int and staged['expected_probes']==3*count and staged['expected_stores']<=lim['max_stores'] and staged['expected_probes']<=lim['max_password_probes'],'STAGED_EXPECTED_EFFECTS')
 c.need(manifest.get('schema')=='friday.f06.retained-native-edit-oracle.v1' and manifest.get('state')=='BOUND_RETAINED_BYTES_NOT_EXECUTION_AUTHORITY' and manifest.get('semantic')=='BRAVO23','STAGED_MANIFEST_SCHEMA')
 c.need(type(manifest.get('selected_count')) is int and manifest['selected_count']==count and manifest.get('selected_fixture_ids')==ids and type(manifest.get('fixtures')) is list and len(manifest['fixtures'])==count,'STAGED_MANIFEST_SELECTION')
 c.need(type(manifest.get('expected_Office_stores')) is int and manifest['expected_Office_stores']==0 and type(manifest.get('expected_Office_password_probes')) is int and manifest['expected_Office_password_probes']==3*count and manifest.get('whole_F06_accepted') is False,'STAGED_MANIFEST_EXPECTED_EFFECTS')
 pins=staged.get('source_pins');credential=staged.get('credential_source')
 declared_credential=manifest.get('credential')
 c.need(type(pins) is list and len(pins)==count and type(credential) is dict and type(declared_credential) is dict and all(credential.get(key)==declared_credential.get(key) for key in ('path','bytes','sha256')) and ('identity' not in declared_credential or credential.get('identity')==declared_credential['identity']),'STAGED_SOURCE_CREDENTIAL_METADATA')
 for ident,row,pin in zip(ids,manifest['fixtures'],pins):
  index=order.index(ident);fmt=('docx','xlsx','pptx','odt','ods','odp','odt')[index]
  profile='compatible1.3_or_Agile' if index<6 else 'current_default_latest_odt_negative'
  name='f06-native-edited.'+fmt if index<6 else 'f06-native-edited-default-latest.odt'
  c.need(type(row) is dict and type(pin) is dict and row.get('fixture_id')==ident and pin.get('fixture_id')==ident and row.get('format')==fmt and row.get('fixture_profile')==profile and row.get('staged_name')==name and row.get('semantic')=='BRAVO23','STAGED_TYPED_SELECTED_ROW')
  c.need(type(row.get('bytes')) is int and 0<row['bytes']<=1000000 and type(row.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None and all(pin.get(key)==row.get(key) for key in ('path','bytes','sha256')),'STAGED_ORIGINAL_SOURCE_PIN')
 return dict(selected_count=count,selected_fixture_ids=list(ids),expected_stores=0,expected_probes=3*count,input_sha256=digest)

def staged_inputs(lim):
 staged=decode(c.private('/inputs/STAGED.json','/inputs')[0])
 raw,pin=c.private('/inputs/NATIVE-OUTPUTS.json','/inputs');manifest=decode(raw)
 selected=selection_contract(staged,manifest,pin['sha256'],lim)
 # Exact copied-cipher directory, sizes and digests are checked before Office.
 directory=c.safe_dir('/inputs/native-outputs');expected=set()
 for row in manifest['fixtures']:
  expected.add(row['staged_name']);_,actual=c.private(directory/row['staged_name'],'/inputs')
  c.need(all(actual[key]==row[key] for key in ('bytes','sha256')),'STAGED_CIPHER_BYTES')
 c.need({p.name for p in directory.iterdir()}==expected,'STAGED_EXACT_SELECTED_DIRECTORY')
 return staged,manifest,selected

def office_argv(pipe,profile):
 return [c.PROGRAM+'/soffice.bin','-env:UserInstallation='+profile.as_uri(),'--headless','--nologo','--norestore','--nodefault','--nofirststartwizard','--accept=pipe,name='+pipe+';urp;StarOffice.ComponentContext']

def phase_observation(attempt,work):
 phase=work/'native-edit-oracle'
 return dict(client_ready=(attempt/'CLIENT-READY.json').exists(),pipe_accepted=(attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists(),oracle_entered=(attempt/'ORACLE-ENTERED.json').exists(),oracle_result_exists=(phase/'RESULT.json').exists(),document_phase_exists=phase.exists())

def failure_metadata(error,phase):
 # Do not inspect messages, source text, locals or arbitrary traceback paths.
 frames=[];tb=error.__traceback__;seen=0
 while tb is not None and seen<64:
  seen+=1;code=tb.tb_frame.f_code
  if code.co_filename in ('/recipe/inside_once.py','/recipe/embedded_entry.py','/recipe/office_fixture_driver.py','/recipe/f06_contract.py'):
   name=code.co_name;frames.append(dict(file=code.co_filename,line=tb.tb_lineno,function=name if len(name)<=128 and (name.isidentifier() or name=='<module>') else 'REDACTED'))
  tb=tb.tb_next
 kind=type(error).__name__
 return dict(exception_class=kind if len(kind)<=128 and kind.isidentifier() else 'REDACTED',phase=phase,source_frames=frames,traceback_truncated=tb is not None,exception_messages_or_locals_saved=False)

def result_exception(value):
 # Validate only the safe codec's class/frame projection, never exception data.
 qualified=r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}'
 c.need(type(value) is dict and set(value)=={'exception_class','source_frames'},'ORACLE_EXCEPTION_SHAPE')
 kind=value['exception_class'];frames=value['source_frames']
 c.need(type(kind) is str and len(kind)<=240 and re.fullmatch(qualified,kind) is not None and type(frames) is list and len(frames)<=12,'ORACLE_EXCEPTION_TYPES')
 for frame in frames:
  c.need(type(frame) is dict and set(frame)=={'source','function','line'},'ORACLE_EXCEPTION_FRAME_SHAPE')
  c.need(frame['source'] in ('callback_observer.py','callback_observer_v2.py','office_fixture_driver.py','uno.py','unohelper.py','OTHER_SOURCE') and type(frame['function']) is str and len(frame['function'])<=100 and re.fullmatch(qualified,frame['function']) is not None and type(frame['line']) is int and frame['line']>0,'ORACLE_EXCEPTION_FRAME_TYPES')

def result_events(events):
 # Early callback faults legitimately have only the initial fields. Later fields
 # remain conditional; every emitted value still has a bounded exact safe shape.
 phases={'entered','request_type_before','get_request_before','get_request_after','classify_before','error_code_before','error_code_after','classify_after','get_continuations_before','get_continuations_after','query_abort_type_before','query_interface_before','query_interface_after','select_before','select_after','no_abort_continuation','callback_exception_reraised'}
 required={'phase','phases','request_kind','abort_selected'}
 optional={'request_class','payload_class','is_document_password','is_document_ms_password','is_error_code_request2','error_code','continuation_attempts','callback_error_phase','callback_error'}
 c.need(type(events) is list and len(events)<=128,'ORACLE_EVENT_LIST')
 for event in events:
  c.need(type(event) is dict and required<=set(event)<=required|optional,'ORACLE_EVENT_SHAPE')
  sequence=event['phases']
  c.need(type(event['phase']) is str and event['phase'] in phases and type(sequence) is list and 1<=len(sequence)<=1024 and all(type(p) is str and p in phases for p in sequence) and sequence[0]=='entered' and sequence[-1]==event['phase'],'ORACLE_EVENT_PHASES')
  c.need(event['request_kind'] in ('UNCLASSIFIED','DocumentPasswordRequest','DocumentMSPasswordRequest','ErrorCodeRequest2','OTHER') and type(event['abort_selected']) is bool,'ORACLE_EVENT_KIND_ABORT')
  for key in ('request_class','payload_class'):
   if key in event:result_exception(dict(exception_class=event[key],source_frames=[]))
  for key in ('is_document_password','is_document_ms_password','is_error_code_request2'):
   if key in event:c.need(type(event[key]) is bool,'ORACLE_EVENT_BOOLEAN')
  if 'error_code' in event:c.need(type(event['error_code']) is int and -(2**31)<=event['error_code']<2**31,'ORACLE_EVENT_ERROR_CODE')
  if 'continuation_attempts' in event:
   attempts=event['continuation_attempts'];c.need(type(attempts) is list and len(attempts)<=128,'ORACLE_CONTINUATION_LIST')
   for attempt in attempts:
    c.need(type(attempt) is dict and {'phase'}<=set(attempt)<={'phase','abort_available'} and attempt['phase'] in ('query_abort_type_before','query_interface_before','query_interface_after','select_before','select_after') and ('abort_available' not in attempt or type(attempt['abort_available']) is bool),'ORACLE_CONTINUATION_SHAPE')
  if event['phase'] in ('select_after','no_abort_continuation'):
   c.need({'request_class','payload_class','is_document_password','is_document_ms_password','is_error_code_request2','continuation_attempts'}<=set(event),'ORACLE_COMPLETED_EVENT_FIELDS')
   if event['request_kind']=='ErrorCodeRequest2':c.need('error_code' in event,'ORACLE_COMPLETED_ERROR_CODE_FIELD')
   if event['phase']=='select_after':c.need(event['abort_selected'] is True and event['continuation_attempts'] and event['continuation_attempts'][-1]=={'phase':'select_after','abort_available':True},'ORACLE_COMPLETED_ABORT_FIELDS')
  c.need(('callback_error' in event)==('callback_error_phase' in event),'ORACLE_CALLBACK_ERROR_JOIN')
  if 'callback_error' in event:
   result_exception(event['callback_error']);c.need(event['callback_error_phase'] in phases and event['phase']=='callback_exception_reraised' and len(sequence)>=2 and sequence[-2]==event['callback_error_phase'],'ORACLE_CALLBACK_ERROR_PHASE')

def result_probe(probe,fmt):
 from callback_observer_v2 import observed_password_refusal_sequence
 required={'opened','semantic_match','expected_password_refusal','interaction_events'}
 optional={'load_exception','semantic_exception','load_argument_position'}
 c.need(type(probe) is dict and required<=set(probe)<=required|optional and all(type(probe[key]) is bool for key in ('opened','semantic_match','expected_password_refusal')),'ORACLE_RESULT_TYPED_PROBE')
 result_events(probe['interaction_events'])
 for key in ('load_exception','semantic_exception'):
  if key in probe:result_exception(probe[key])
 c.need(not probe['semantic_match'] or probe['opened'],'ORACLE_SEMANTIC_REQUIRES_OPEN')
 c.need('load_exception' not in probe or not probe['opened'],'ORACLE_LOAD_EXCEPTION_OPEN_JOIN')
 c.need('semantic_exception' not in probe or probe['opened'] and not probe['semantic_match'],'ORACLE_SEMANTIC_EXCEPTION_JOIN')
 if 'load_argument_position' in probe:
  position=probe['load_argument_position']
  c.need('load_exception' in probe and fmt in ('docx','xlsx','pptx') and probe['load_exception']['exception_class']=='com.sun.star.lang.IllegalArgumentException' and (position is None or type(position) is str and position=='UNOBSERVED' or type(position) is int and -32768<=position<32768),'ORACLE_LOAD_ARGUMENT_POSITION')
 allowed_exception='load_exception' not in probe or fmt in ('docx','xlsx','pptx') and probe['load_exception']['exception_class']=='com.sun.star.lang.IllegalArgumentException' and type(probe.get('load_argument_position')) is int and probe['load_argument_position']==1
 refusal=not probe['opened'] and observed_password_refusal_sequence(probe['interaction_events'],fmt) and allowed_exception
 c.need(probe['expected_password_refusal'] is refusal,'ORACLE_REFUSAL_OBSERVATIONS_JOIN')

def result_contract(result,manifest,selected,client_exit):
 # Complete saved observations can prove a count of observations, never an
 # instrumented runtime call count. A partial result cannot become complete.
 c.need(type(result) is dict and type(client_exit) is int and client_exit in (0,1),'ORACLE_COMPLETE_CLIENT_EXIT')
 c.need(set(result)<={'mode','input_manifest','input_manifest_sha256','rows','planned_rows','whole_seven_covered','all_pass','oracle','visual_fidelity','F06_formal_or_delivery','all_pass_scope','selected_fixture_ids','selected_count','full_six_covered','all_seven_pass','whole_F06_accepted'},'ORACLE_RESULT_FIELDS')
 count=selected['selected_count'];ids=selected['selected_fixture_ids'];rows=result.get('rows')
 c.need(result.get('mode')=='verify-native-edits' and result.get('input_manifest')=='/inputs/NATIVE-OUTPUTS.json' and result.get('input_manifest_sha256')==selected['input_sha256'],'ORACLE_RESULT_SOURCE')
 c.need(type(result.get('planned_rows')) is int and result['planned_rows']==count and type(result.get('selected_count')) is int and result['selected_count']==count and result.get('selected_fixture_ids')==ids and result.get('all_pass_scope')=='SELECTED_ONLY' and result.get('whole_F06_accepted') is False,'ORACLE_RESULT_SELECTED_SCOPE')
 c.need(type(rows) is list and len(rows)==count,'ORACLE_RESULT_NOT_COMPLETE')
 passed_ids=set()
 for ident,row,source in zip(ids,rows,manifest['fixtures']):
  c.need(type(row) is dict and row.get('fixture_id')==ident and row.get('format')==source['format'] and row.get('fixture_profile')==source['fixture_profile'],'ORACLE_RESULT_TYPED_ROW')
  c.need(set(row)<={'fixture_id','format','fixture_profile','filter','source_path','source_sha256','path','sha256','bytes','independent_office_password_and_semantics_pass','tests','envelope','envelope_exception_class','same_input_bytes_preserved','credential_ref','new_bytes','recovered_old_bytes','native_protected_result'},'ORACLE_RESULT_ROW_FIELDS')
  target='/inputs/native-outputs/'+source['staged_name']
  c.need(row.get('source_path')==target and row.get('path')==target and row.get('source_sha256')==source['sha256'] and row.get('sha256')==source['sha256'] and type(row.get('bytes')) is int and row['bytes']==source['bytes'] and row.get('new_bytes') is False and row.get('recovered_old_bytes') is False and row.get('credential_ref')=='/inputs/credential.private.json','ORACLE_RESULT_RETAINED_BYTES')
  tests=row.get('tests');c.need(type(tests) is dict and set(tests)=={'missing','wrong','correct'} and all(type(tests[key]) is dict for key in tests),'ORACLE_RESULT_PROBE_OBSERVATIONS')
  for probe in tests.values():result_probe(probe,source['format'])
  c.need(type(row.get('same_input_bytes_preserved')) is bool and type(row.get('independent_office_password_and_semantics_pass')) is bool,'ORACLE_RESULT_TYPED_VERDICT')
  c.need('envelope_exception_class' in row and (row['envelope_exception_class'] is None or type(row['envelope_exception_class']) is str and len(row['envelope_exception_class'])<=240 and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}',row['envelope_exception_class']) is not None),'ORACLE_ENVELOPE_EXCEPTION_CLASS')
  passed=row['same_input_bytes_preserved'] and row['envelope_exception_class'] is None and tests['missing']['expected_password_refusal'] and tests['wrong']['expected_password_refusal'] and tests['correct']['opened'] and tests['correct']['semantic_match'] and not tests['correct']['interaction_events']
  c.need(row['independent_office_password_and_semantics_pass'] is passed,'ORACLE_ROW_VERDICT_OBSERVATIONS_JOIN')
  if row['independent_office_password_and_semantics_pass']:passed_ids.add(ident)
 all_pass=len(passed_ids)==count
 c.need(type(result.get('all_pass')) is bool and result['all_pass']==all_pass and client_exit==(0 if all_pass else 1),'ORACLE_RESULT_CLIENT_VERDICT_JOIN')
 c.need(result.get('whole_seven_covered') is (count==7) and result.get('full_six_covered') is (set('f06-'+str(i) for i in range(1,7))<=passed_ids) and result.get('all_seven_pass') is (set('f06-'+str(i) for i in range(1,8))<=passed_ids),'ORACLE_RESULT_COVERAGE_FLAGS')
 return dict(state='COMPLETE_SELECTED_OBSERVATIONS_SEMANTIC_RESULT_SEPARATE',complete_selected_result=True,selected_count=count,selected_fixture_ids=list(ids),client_exit=client_exit,all_pass=all_pass,whole_F06_accepted=False,completed_probe_observations=3*len(rows),probe_count_basis='DERIVED_FROM_SAVED_COMPLETE_MISSING_WRONG_CORRECT_DICTS_NOT_INSTRUMENTED_CALLS',expected_stores=0,store_count_basis='PLANNED_STATIC_VERIFY_NATIVE_EDITS_BRANCH_AND_READONLY_INPUT_MOUNT_NOT_INSTRUMENTED_COUNT')

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
 native_mode(mode)
 for mount in ('/recipe',c.PREFIX,'/inputs'):
  hits=[r for r in rows if r[4]==mount];c.need(hits and 'ro' in hits[-1][5].split(','),'MOUNT_READONLY')
 # clear network namespace has only loopback and no non-loopback route.
 dev=Path('/proc/net/dev').read_text().splitlines()[2:];c.need(all(x.split(':',1)[0].strip()=='lo' for x in dev),'NETWORK_INTERFACE')
 c.need(len(os.sched_getaffinity(0))==2,'AFFINITY_TWO')

def ownership(p,ref,pipe,profile,observation_path):
 # Collect only this nonce's matching rows. Persist their bounded typed fields
 # before any acceptance/refusal, including malformed/excess/foreign rows.
 proc=Path('/proc',str(p.pid));rows=[]
 observation=dict(state='PIPE_OBSERVATION_NOT_ACCEPTANCE',pid=p.pid,starttime=ref['starttime'],pipe=pipe,profile=str(profile),rows=rows,Office_fd_snapshot=[],Office_fd_snapshot_bytes=0,max_Office_fd_snapshot_bytes=1048576,matching_rows_seen=0,kernel_rows_scanned=0,max_matching_rows=8,max_kernel_rows=4096,max_Office_fds=1024,scan_complete=False)
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
    row['observed_role']={('00010000','01'):'listener',('00000000','03'):'accepted'}.get((row['flags'],row['socket_state']),'UNEXPECTED')
    rows.append(row)
    if row['path_is_private_tmp']:
     row['path']=str(path)
     try:row['identity']=c.identity(path.lstat())
     except OSError as error:row['lstat_error_class']=type(error).__name__
  # Collect actual owned Office identity/argv/fds before a refused verdict.
  # Its fixed launch argv has no credentials; other processes are not scanned.
  before=(proc/'stat').read_text().rsplit(') ',1)[1].split();observation['observed_starttime']=before[19];observation['observed_uid']=proc.stat().st_uid
  exe=(proc/'exe').stat();want=Path(c.PROGRAM,'soffice.bin').stat();observation['executable_identity']=c.identity(exe);observation['executable_link']=os.readlink(proc/'exe')
  with (proc/'cmdline').open('rb') as stream:argvraw=stream.read(8193)
  c.need(len(argvraw)<=8192,'OFFICE_ARGV_BOUND')
  observation['argv_sha256']=hashlib.sha256(argvraw).hexdigest()
  observation['argv']=[arg.decode('utf-8','backslashreplace') for arg in argvraw.rstrip(b'\0').split(b'\0')]
  for number,fd in enumerate((proc/'fd').iterdir(),1):
   c.need(number<=1024,'OWN_PIPE_OFFICE_FDS_BOUND')
   try:link=os.readlink(fd)
   except FileNotFoundError:continue
   c.need(len(link)<=4096,'OFFICE_FD_LINK_BOUND');observation['Office_fd_snapshot_bytes']+=len(link)
   c.need(observation['Office_fd_snapshot_bytes']<=observation['max_Office_fd_snapshot_bytes'],'OFFICE_FD_SNAPSHOT_BOUND');observation['Office_fd_snapshot'].append(dict(fd=fd.name,link=link))
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
  observation['error_metadata']=failure_metadata(error,'owned_pipe_observation')
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
 return dict(state='OWNED_PIPE_PROCESS_PROFILE_OBSERVED',pid=p.pid,starttime=ref['starttime'],uid=os.getuid(),pipe=pipe,profile=str(profile),executable_identity=c.identity(exe),sockets=rows,listening_socket_inode=listeners[0]['socket_inode'],connected_socket_inodes=[r['socket_inode'] for r in connected],observation_path=str(observation_path),argv_sha256=observation['argv_sha256'],observed_accepted_socket_count=len(connected))

def main():
 # Fixed mode is rejected before directory/signal/process effects.
 mode=native_mode(os.environ.get('FRW_F06_MODE'));lim=c.limits(mode)
 origin=float(os.environ['FRW_F06_UNIT_START']);c.need(math.isfinite(origin) and 0<origin<=time.monotonic(),'ORIGINAL_ADMISSION_CLOCK')
 c.DEADLINE=origin+lim['whole_wall_seconds']-lim['cleanup_reserve_seconds'];c.within()
 os.umask(0o077);work=c.safe_dir('/work')
 report=dict(state='FAILED_OR_PARTIAL_PRESERVED',mode=mode,Office_launch_attempts=0,client_launch_attempts=0,Office_starts=0,client_starts=0,oracle_permissions=0,owned_children_closed=False,attempts=[],original_operation_start_monotonic=origin,absolute_work_deadline=c.DEADLINE,semantic_acceptance_is_separate=True)
 office=client=None;oref=cref=None;streams=[];record=None;pipe=None;attempt=None;phase='namespace_guard';selected=None
 def interrupted(signum,_):raise InterruptedError('OWNED_SIGNAL')
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
 try:
  mount_guard(mode);phase='staged_selected_contract'
  staged,manifest,selected=staged_inputs(lim);report['planned_selected_effects']=selected
  for name in ('home','tmp','cache','config','runtime','profile'):(work/name).mkdir(mode=0o700)
  env=dict(os.environ);env['LD_LIBRARY_PATH']=c.PROGRAM+':'+c.PREFIX+'/root/usr/lib/x86_64-linux-gnu';env['URE_BOOTSTRAP']='vnd.sun.star.pathname:'+c.PROGRAM+'/fundamentalrc';env['FRW_F06_INPUT_SHA']=selected['input_sha256']
  maximum=lim['max_Office_starts'];c.need(type(maximum) is int and maximum==3,'BOOTSTRAP_TOTAL_START_CAP')
  for number in range(1,maximum+1):
   c.within();office=client=None;oref=cref=None;record=None;phase='attempt_setup'
   attempt=work/('attempt-'+str(number));attempt.mkdir(mode=0o700)
   pipe='f06_'+env['FRW_F06_NONCE']+'_a'+str(number)
   env['FRW_F06_ATTEMPT']=str(attempt);env['FRW_F06_PIPE']=pipe
   record=dict(attempt=number,pipe=pipe,Office_exit=None,client_exit=None,Office_exit_observed_by_wait=False,client_exit_observed_by_wait=False,Office_terminal_before_cleanup=False,client_ready=False,pipe_accepted=False,oracle_entered=False,oracle_result_exists=False,document_phase_exists=False,owned_children_closed=False,owned_pipe_closed=False)
   report['attempts'].append(record)
   common=office_argv(pipe,work/'profile')
   streams += [(attempt/'Office.stdout.private').open('xb'),(attempt/'Office.stderr.private').open('xb')]
   report['Office_launch_attempts']+=1;record['Office_launch_attempted']=True;phase='owned_Office_launch'
   # Assign the direct Popen before pidfd/identity/proof work can fail.
   office=subprocess.Popen(common,stdin=subprocess.DEVNULL,stdout=streams[-2],stderr=streams[-1],env=env,close_fds=True)
   report['Office_starts']+=1;phase='owned_Office_birth'
   oref=birth(office);record['Office_birth']={k:v for k,v in oref.items() if k!='pidfd'}
   streams += [(attempt/'client.stdout.private').open('xb'),(attempt/'client.stderr.private').open('xb')]
   report['client_launch_attempts']+=1;record['client_launch_attempted']=True;phase='owned_client_launch'
   client=subprocess.Popen([c.PROGRAM+'/python','-B','-s','-S','/recipe/embedded_entry.py'],stdin=subprocess.DEVNULL,stdout=streams[-2],stderr=streams[-1],env=env,close_fds=True)
   report['client_starts']+=1;phase='owned_client_birth'
   cref=birth(client);record['client_birth']={k:v for k,v in cref.items() if k!='pidfd'}
   accepted=False;startup_exit=False;phase='owned_connection'
   while True:
    c.within()
    if office.poll() is not None:
     record['Office_exit']=office.wait();record['Office_exit_observed_by_wait']=True;record['Office_terminal_before_cleanup']=True;startup_exit=True;break
    if not accepted and (attempt/'CLIENT-READY.json').exists():
     ready=decode(c.stable(attempt/'CLIENT-READY.json')[0])
     c.need(ready['state']=='CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET' and type(ready['component_count']) is int and ready['component_count']==0 and ready['pipe']==pipe and ready['pid']==cref['pid'] and ready['starttime']==cref['starttime'],'CONNECTED_EMPTY_COMPONENTS_ACTUAL_CHILD')
     phase='owned_pipe_observation';proof=ownership(office,oref,pipe,work/'profile',attempt/'PIPE-OBSERVATION.json')
     proof['zero_components_client_witness']=ready
     c.need(report['oracle_permissions']==0,'ONE_READONLY_ORACLE_ONLY')
     c.save(attempt/'PIPE-OWNERSHIP-ACCEPTED.json',proof);accepted=True;report['oracle_permissions']+=1;phase='owned_oracle_wait'
    if client.poll() is not None:break
    time.sleep(.02)
   record.update(phase_observation(attempt,work))
   if startup_exit:
    phase='bootstrap_cleanup';close_attempt(office,client,oref,cref,record,pipe);oref=cref=None
    record.update(phase_observation(attempt,work))
    c.save(attempt/'ATTEMPT-RESULT.json',record)
    # Actual exits/closure are durable before the continuation verdict.
    phase='bootstrap_continuation';continuation(record,number,maximum)
    continue
   phase='owned_client_wait';record['client_exit']=client.wait();record['client_exit_observed_by_wait']=True
   phase='owned_final_cleanup';close_attempt(office,client,oref,cref,record,pipe);oref=cref=None
   record.update(phase_observation(attempt,work));c.save(attempt/'ATTEMPT-RESULT.json',record)
   # Every actual Office/client wait exit is saved before terminal verdicts.
   c.need(record['owned_children_closed'] and record['owned_pipe_closed'],'OWNED_FINAL_CLOSURE')
   c.need(accepted and record['oracle_entered'],'READONLY_ORACLE_NOT_ENTERED')
   phase='oracle_saved_result_contract'
   raw,resultpin=c.private(work/'native-edit-oracle'/'RESULT.json',work)
   summary=result_contract(decode(raw),manifest,selected,record['client_exit'])
   summary['original_result']=resultpin;summary['original_result_bytes_preserved']=True
   c.save(work/'ORACLE-RESULT-CONTRACT.json',summary);report['oracle_result_contract']=summary
   report['semantic_all_pass']=summary['all_pass'];report['oracle_client_exit']=record['client_exit']
   report['state']='READONLY_ORACLE_CLIENT_COMPLETED_SEPARATE_SEMANTIC_RESULT'
   break
 except BaseException as error:
  report['error_metadata']=failure_metadata(error,phase)
 finally:
  for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:None)
  if record is not None:
   record.update(phase_observation(attempt,work))
   if not record.get('cleanup_attempted') or not record.get('actual_children_terminal'):close_attempt(office,client,oref,cref,record,pipe)
   if not (attempt/'ATTEMPT-RESULT.json').exists():c.save(attempt/'ATTEMPT-RESULT.json',record)
   else:c.save(attempt/'ATTEMPT-FINAL-CLEANUP.json',record)
  for stream in streams:
   try:stream.close()
   except OSError:pass
  report['cleanup_errors']=[e for r in report['attempts'] for e in r.get('cleanup_errors',[])];report['owned_children_closed']=all(r['owned_children_closed'] for r in report['attempts']);report['owned_pipes_closed']=all(r['owned_pipe_closed'] for r in report['attempts'])
  usage=resource.getrusage(resource.RUSAGE_CHILDREN);report['children_CPU_seconds']=usage.ru_utime+usage.ru_stime;report['children_maxrss_kib']=usage.ru_maxrss;report['elapsed_whole_operation_seconds']=time.monotonic()-origin
  if not report['owned_children_closed'] or not report['owned_pipes_closed']:report['state']='STOP_UNCONFIRMED'
  report['completed_at_moscow']=c.utcmoscow();c.save(work/'INSIDE-RESULT.json',report)
 return 0 if report['state']=='READONLY_ORACLE_CLIENT_COMPLETED_SEPARATE_SEMANTIC_RESULT' else 1
if __name__=='__main__':raise SystemExit(main())
