"""Genuine installed documented pure leaf; synthetic read_file privacy only. Original runtime-wrapper WARN NOT_RUN unchanged."""
from pathlib import Path
import ast,datetime,fcntl,hashlib,io,json,logging,os,resource,stat,sys,time
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N=H/'hermes-agent'
O=B/'F06-INSTALLED206-READ-FILE-PRIVACY-LEAF-20261112'
os.umask(0o077)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return dict(path=str(path),sha256=sha(path))
def main():
 assert sys.flags.isolated and sys.dont_write_bytecode and __debug__
 assert O.is_dir() and not (O/'RESULT.json').exists()
 os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
 started=time.monotonic()
 assert sha(B/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json')=='20e1a9ca845f52eeb0b6a149acc47fd91c9bc70142140e18095acdf18476b900'
 proof=json.loads((B/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json').read_bytes())
 assert proof['state']=='INSTALLED206_PROJECT493_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
 for row in proof['installed']['canonical4'].values():assert ref(row['path'])==row
 receipt=json.loads((H/'hermes-agent.source.json').read_bytes())
 helpers=N/'agent/message_sanitization.py'
 assert sha(helpers)==receipt['files']['agent/message_sanitization.py']['sha256']
 assert os.environ.get('HERMES_HOME')==str(H)
 # This is the actual installed source path, not an own fixture or import replacement.
 sys.path.insert(0,str(N))
 pm_state=H/'installs/45eb40fd2d5351a9'
 pm_lock=pm_state/'.install.lock'
 leases=pm_state/'environments/8e0c92ce48434ddbb9125ee001560ccb/.leases'
 lock_info=pm_lock.lstat();lock_digest=sha(pm_lock)
 assert stat.S_ISREG(lock_info.st_mode) and lock_info.st_uid==os.getuid() and lock_info.st_nlink==1
 created_leases=set();denied_opens=[]
 def audit(event,args):
  if event in ('socket.connect','socket.connect_ex','socket.bind','subprocess.Popen','os.system','os.fork','os.posix_spawn','os.exec'):
   raise PermissionError('NO_NETWORK_PROCESS_EFFECTS_IN_RUNTIME_WARN_CONTROL')
  if event=='open':
   path,mode,flags=args
   writable=(isinstance(mode,str) and any(char in mode for char in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writable:
    physical=None
    if isinstance(path,int):
     try:physical=Path(os.readlink('/proc/self/fd/'+str(path)))
     except OSError:pass
    elif isinstance(path,(str,bytes,os.PathLike)):physical=Path(os.fsdecode(path))
    own=physical is not None and physical.is_relative_to(O)
    sink=physical==Path('/dev/null') and stat.S_ISCHR(os.stat('/dev/null').st_mode) and os.stat('/dev/null').st_rdev==os.makedev(1,3)
    lock_allowed=False
    if physical==pm_lock:
     info=pm_lock.lstat()
     lock_allowed=(info.st_dev,info.st_ino,info.st_uid,info.st_nlink,info.st_mode)==(lock_info.st_dev,lock_info.st_ino,lock_info.st_uid,lock_info.st_nlink,lock_info.st_mode) and sha(pm_lock)==lock_digest
    new_lease=(physical is not None and physical.parent==leases and len(physical.name)==32 and all(char in '0123456789abcdef' for char in physical.name) and isinstance(flags,int) and flags&os.O_CREAT and flags&os.O_EXCL and not os.path.lexists(physical))
    if new_lease:created_leases.add(physical)
    if not(own or sink or lock_allowed or new_lease):
     denied_opens.append(dict(path_kind=type(path).__name__,path=str(physical) if physical else None,mode=mode,flags=flags))
     raise PermissionError('NO_WRITE_OUTSIDE_OWN_WARN_EVIDENCE')
  if event=='os.mkdir':
   path=Path(os.fsdecode(args[0]))
   if path.is_dir() and not any(parent.is_symlink() for parent in (path,*path.parents)):return
   if path==leases and not path.exists() and path.parent.is_dir():return
   raise PermissionError('NO_FILESYSTEM_MUTATION_IN_RUNTIME_WARN_CONTROL')
  if event=='os.remove' and Path(os.fsdecode(args[0])) in created_leases:return
  if event in ('os.remove','os.rename','os.rmdir','os.chmod','os.chown','os.symlink','os.link','os.truncate','os.utime'):
   raise PermissionError('NO_FILESYSTEM_MUTATION_IN_RUNTIME_WARN_CONTROL')
 sys.addaudithook(audit)
 stream=io.StringIO();logger=logging.getLogger('root.installed206.synthetic.runtime.warn')
 logger.handlers[:]=[logging.StreamHandler(stream)];logger.setLevel(logging.WARNING);logger.propagate=False
 stage='genuine_installed_pure_leaf_import';checks=[];exception_class=None;state='NOT_RUN_OR_PARTIAL'
 try:
  from agent import message_sanitization as helper
  assert Path(helper.__file__).resolve()==helpers
  assert sha(helpers)==receipt['files']['agent/message_sanitization.py']['sha256']
  assert 'run_agent' not in sys.modules
  imported_native=[]
  for name,module in tuple(sys.modules.items()):
   origin=getattr(module,'__file__',None)
   if origin and Path(origin).is_relative_to(N) and Path(origin).suffix=='.py':
    relative=str(Path(origin).relative_to(N))
    assert sha(origin)==receipt['files'][relative]['sha256']
    imported_native.append(relative)
  source_logger=helper.logger
  old_handlers=list(source_logger.handlers);old_level=source_logger.level;old_propagate=source_logger.propagate
  handler=logging.StreamHandler(stream);source_logger.handlers[:]=[handler];source_logger.setLevel(logging.WARNING);source_logger.propagate=False
  stage='actual_installed_read_file_repair_and_persistence_leaf'
  marker='F06_OWN_SYNTHETIC_LEAF_ONLY_206_NOT_USER_SECRET'
  try:
   valid=json.dumps(dict(path='synthetic-not-opened.docx',password=marker),ensure_ascii=False)
   repaired=helper._repair_tool_call_arguments(valid,'read_file')
   checks.append(dict(name='valid_execution_password_retained_in_memory_no_warning',passed=json.loads(repaired)==json.loads(valid) and not stream.getvalue()))
   malformed='{"path":"synthetic-not-opened.docx","password":"'+marker+'",}'
   fixed=helper._repair_tool_call_arguments(malformed,'read_file');logs=stream.getvalue()
   checks.append(dict(name='actual_leaf_WARNING_repair_same_password_in_memory',passed=json.loads(fixed)['password']==marker and 'Repaired malformed tool_call arguments' in logs))
   checks.append(dict(name='actual_read_file_diagnostic_both_copies_redacted',passed=marker not in logs and logs.count('[redacted file-tool arguments]')==2))
   calls=[dict(id='f06-read-206',type='function',function=dict(name='read_file',arguments=valid))]
   original=json.loads(json.dumps(calls));durable=helper.redact_protected_file_tool_calls_for_persistence(calls)
   checks.append(dict(name='actual_persistence_copy_removes_password_only_preserves_id_path',passed=json.loads(durable[0]['function']['arguments'])==dict(path='synthetic-not-opened.docx',password='[redacted]') and durable[0]['id']=='f06-read-206'))
   checks.append(dict(name='live_arguments_not_mutated_or_redacted',passed=calls==original and marker in calls[0]['function']['arguments']))
   user=dict(role='user',content='intentional synthetic credential '+marker)
   checks.append(dict(name='intentional_user_chat_not_blanket_erased',passed=helper.redact_protected_file_message_for_persistence(user)==user))
   before=len(stream.getvalue());unrelated='{"ordinary":1,}'
   other=helper._repair_tool_call_arguments(unrelated,'calculator');otherlog=stream.getvalue()[before:]
   checks.append(dict(name='unrelated_valid_repair_not_blanket_masked',passed=json.loads(other)==dict(ordinary=1) and unrelated in otherlog and '[redacted file-tool arguments]' not in otherlog))
   checks.append(dict(name='genuine_native_import_no_run_agent_or_overlay',passed='run_agent' not in sys.modules and len(imported_native)>=4))
   assert all(row['passed'] for row in checks)
   state='PASS_GENUINE_INSTALLED_READ_FILE_PURE_LEAF_ONLY'
  finally:
   source_logger.handlers[:]=old_handlers;source_logger.setLevel(old_level);source_logger.propagate=old_propagate
 except BaseException as error:
  exception_class=type(error).__module__+'.'+type(error).__qualname__
  error_exit_code=error.code if isinstance(error,SystemExit) and type(error.code) is int else None
  frames=[];trace=error.__traceback__
  while trace is not None:
   frames.append(dict(file=Path(trace.tb_frame.f_code.co_filename).name,line=trace.tb_lineno,function=trace.tb_frame.f_code.co_name));trace=trace.tb_next
  state='NOT_RUN_GENUINE_IMPORT_REFUSED' if stage=='genuine_installed_pure_leaf_import' else 'FAIL_OR_PARTIAL_ACTUAL_RUNTIME_WARN_CONTROL'
 # Raw warnings are synthetic only and stay private; exception text/context never serialized.
 (O/'synthetic-runtime-warning.log').write_text(stream.getvalue())
 for row in proof['installed']['canonical4'].values():assert ref(row['path'])==row
 result=dict(schema='friday.root.installed206.read-file-pure-leaf-consumer.v1',state=state,stage=stage,exception_class=exception_class,
  planned_native_PM_lease_files=[str(path) for path in sorted(created_leases)],PM_lock_hash_unchanged=sha(pm_lock)==lock_digest,
  audit_denied_opens=denied_opens, exception_frames=locals().get('frames',[]), native_exit_code=locals().get('error_exit_code'),
  at_moscow=datetime.datetime.now().astimezone().isoformat(),installed=proof['installed'],runtime_helper=ref(helpers),checks=checks,
  genuine_source_admission_not_overridden=True,source_module_or_constants_not_replaced=True,
  synthetic_only_no_model_AIAgent_instance_Store_doc_read_edit_send=True,
  effects_enforced='Normal native PM existinginstalllock and own fresh UUID runtimeleases allowed; source reviewed runtime_lock/lease_generation, no persistent user write. Existing PMleases cannot be pruned by this audit. Other write/network/process effects blocked; no native/source/marker/principal bypass. R2 primaryNOTRUN retained.',
  old_wrong_fixture_NOT_RUN_unchanged=True,elapsed_seconds=time.monotonic()-started,
  limits=dict(CPU_seconds=60,address_space_bytes=1024**3,CPUs=2,parent_wall_seconds=90),
  imported_native_sources=locals().get('imported_native',[]), original_runtime_wrapper_WARN='NOT_RUN unchanged; actual leaf WARNING is distinct', privacy_scope='Actual installed documented pure read_file repair/diagnostic/persistence projection only; no run_agent bootstrap required or bypassed, no overlay, no AIAgent/model/DB/doc. No actual user reply, output artifact, memory-manager or whole F06 acceptance.')
 (O/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(dict(state=state,stage=stage,exception_class=exception_class,checks_passed=sum(row['passed'] for row in checks),checks=len(checks),proof=ref(O/'RESULT.json'))))
 return 0 if state.startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
