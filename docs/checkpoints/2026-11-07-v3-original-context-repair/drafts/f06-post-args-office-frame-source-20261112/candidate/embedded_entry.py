"""Dormant pinned embedded client for one metadata-only template diagnostic.
Import is inert. The script keeps the original initialized pyuno __main__ and
loads the reviewed driver in a separate library namespace before one main call.
"""
import json,math,os,re,runpy,sys,time
from pathlib import Path

P='/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
CORE=P+'/python-core-3.12.13'

def native_mode(mode):
 if mode!='one-template-diagnostic':raise ValueError('MODE')
 return mode

def driver_argv(pipe,digest):
 if type(pipe) is not str or re.fullmatch('f06_[0-9a-f]{32}_a[1-3]',pipe) is None:raise ValueError('EXACT_PIPE')
 if type(digest) is not str or re.fullmatch('[0-9a-f]{64}',digest) is None:raise ValueError('EXACT_INPUT_SHA')
 return ['/recipe/diagnostic_client.py','--input-manifest-sha256',digest]


def failure_metadata(error,phase):
 # Frames only. Never format the exception or read source text or locals.
 frames=[];tb=error.__traceback__;seen=0
 while tb is not None and seen<64:
  seen+=1;code=tb.tb_frame.f_code
  if code.co_filename in ('/recipe/diagnostic_client.py','/recipe/embedded_entry.py','/recipe/f06_contract.py'):
   name=code.co_name
   frames.append(dict(file=code.co_filename,line=tb.tb_lineno,function=name if len(name)<=128 and (name.isidentifier() or name=='<module>') else 'REDACTED'))
  tb=tb.tb_next
 kind=type(error).__name__
 return dict(status='ERROR',exception_class=kind if len(kind)<=128 and kind.isidentifier() else 'REDACTED',phase=phase,source_frames=frames,traceback_truncated=tb is not None,exception_messages_or_locals_saved=False)

def main():
 attempt=None;contract=None;phase='mode_guard'
 try:
  # No UNO imports, runtime mutations, connects or file reads before this guard.
  mode=native_mode(os.environ.get('FRW_F06_MODE'));phase='embedded_runtime_guard'
  sys.dont_write_bytecode=True
  sys.path[:]=[P,CORE+'/lib',CORE+'/lib/lib-dynload',CORE+'/lib/site-packages','/recipe']
  if not (sys.flags.no_site and sys.flags.no_user_site and sys.dont_write_bytecode):raise RuntimeError('EMBEDDED_FLAGS')
  if os.environ.get('PYTHONHOME')!=CORE or os.environ.get('URE_BOOTSTRAP')!='vnd.sun.star.pathname:'+P+'/fundamentalrc':raise RuntimeError('EMBEDDED_FIXED_ENV')
  if sys.version_info[:3]!=(3,12,13):raise RuntimeError('EMBEDDED_VERSION')
  import f06_contract as contract
  limits=contract.limits(mode);origin=float(os.environ['FRW_F06_UNIT_START'])
  contract.need(math.isfinite(origin) and 0<origin<=time.monotonic(),'ORIGINAL_ADMISSION_CLOCK')
  deadline=origin+limits['whole_wall_seconds']-limits['cleanup_reserve_seconds'];contract.DEADLINE=deadline;contract.within()
  phase='attempt_scope'
  pipe=os.environ['FRW_F06_PIPE'];raw_attempt=os.environ['FRW_F06_ATTEMPT'];candidate=Path(raw_attempt)
  contract.need(candidate.parent==Path('/work') and str(candidate)==raw_attempt and candidate.name in ('attempt-1','attempt-2','attempt-3') and pipe=='f06_'+os.environ['FRW_F06_NONCE']+'_a'+candidate.name[-1],'ATTEMPT_PIPE_SCOPE')
  argv=driver_argv(pipe,os.environ['FRW_F06_INPUT_SHA']);attempt=contract.safe_dir(candidate)
  phase='embedded_UNO_types'
  import uno,unohelper
  from com.sun.star.beans import PropertyValue
  from com.sun.star.connection import NoConnectException
  from com.sun.star.task import XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest
  if uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE')!=0:raise RuntimeError('MACRO_NEVER_VALUE')
  if uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE')!=0:raise RuntimeError('UPDATE_NEVER_VALUE')
  # Poll only typed NoConnect for the already-owned Office; no launch/restart.
  phase='owned_pipe_connect';ctx=uno.getComponentContext();resolver=ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',ctx)
  while True:
   if time.monotonic()>=deadline:raise TimeoutError('OWN_PIPE_CONNECT_DEADLINE')
   try:remote=resolver.resolve('uno:pipe,name='+pipe+';urp;StarOffice.ComponentContext');break
   except NoConnectException:time.sleep(.05)
  phase='same_Office_empty_Desktop_witness'
  desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
  components=desktop.getComponents().createEnumeration();component_count=0
  while components.hasMoreElements():
   components.nextElement();component_count+=1
   if component_count>0:raise RuntimeError('STARTUP_COMPONENTS_NOT_EMPTY')
  ready=dict(pipe=pipe,pid=os.getpid(),starttime=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],state='CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET',component_count=component_count)
  contract.save(attempt/'CLIENT-READY.json',ready)
  phase='owned_pipe_permission'
  while not (attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists():
   if time.monotonic()>=deadline:raise TimeoutError('PIPE_OWNERSHIP_DEADLINE')
   time.sleep(.02)
  # The parent has now checked actual owned listener/socket fds/PID/birth/argv.
  # Preserve this original __main__: pyuno stores its initialized Runtime here.
  contract.within();contract.save(attempt/'ORACLE-ENTERED.json',dict(state='ONE_METADATA_DIAGNOSTIC_ENTERED_AFTER_EMPTY_COMPONENTS_AND_PARENT_ACCEPT',mode=mode,pipe=pipe,pid=os.getpid(),credential_read_yet=False,document_loads_yet=0,types=['PropertyValue','XInteractionHandler','DocumentPasswordRequest','DocumentMSPasswordRequest'],macro_NEVER_EXECUTE=0,update_NO_UPDATE=0))
  sys.argv=argv;phase='oracle_library_load'
  oracle=runpy.run_path('/recipe/diagnostic_client.py',run_name='f06_diagnostic_library')
  phase='one_diagnostic_call';exitcode=oracle['run_once'](uno=uno,unohelper=unohelper,desktop=desktop,property_value=PropertyValue,interaction_handler_type=XInteractionHandler,password_request_type=DocumentPasswordRequest,ms_password_request_type=DocumentMSPasswordRequest,error_code_request_type=uno.getClass('com.sun.star.task.ErrorCodeRequest2'),input_manifest_sha256=os.environ['FRW_F06_INPUT_SHA'])
  contract.need(type(exitcode) is int and exitcode in (0,1),'ORACLE_MAIN_RETURN')
  return exitcode
 except BaseException as error:
  metadata=failure_metadata(error,phase);metadata['location_file_save_failed']=False
  # An invalid mode has no filesystem effects. After runtime/attempt validation,
  # only the private bounded class/phase/frame diagnostic is persisted.
  if contract is not None:
   try:contract.save((attempt/'ORACLE-ERROR-LOCATION.json') if attempt is not None else Path('/work/EMBEDDED-ERROR-LOCATION.json'),metadata)
   except BaseException:metadata['location_file_save_failed']=True
  try:print(json.dumps(metadata))
  except BaseException:pass
  return 2

if __name__=='__main__':raise SystemExit(main())
