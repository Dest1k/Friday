"""Pinned embedded Python bootstrap; isolated by bwrap, clearenv and fixed paths.
Do not use -I: it ignores PYTHONHOME deliberately supplied by the pinned wrapper.
"""
import os,sys,time,runpy,json,stat
from pathlib import Path
P='/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
CORE=P+'/python-core-3.12.13'
sys.dont_write_bytecode=True
sys.path[:]=[P,CORE+'/lib',CORE+'/lib/lib-dynload',CORE+'/lib/site-packages','/recipe']
if not (sys.flags.no_site and sys.flags.no_user_site and sys.dont_write_bytecode):raise RuntimeError('EMBEDDED_FLAGS')
if os.environ.get('PYTHONHOME')!=CORE or os.environ.get('URE_BOOTSTRAP')!='vnd.sun.star.pathname:'+P+'/fundamentalrc':raise RuntimeError('EMBEDDED_FIXED_ENV')
if sys.version_info[:3]!=(3,12,13):raise RuntimeError('EMBEDDED_VERSION')
import uno,unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
from com.sun.star.task import XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest
if uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE')!=0:raise RuntimeError('MACRO_NEVER_VALUE')
if uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE')!=0:raise RuntimeError('UPDATE_NEVER_VALUE')
mode=os.environ['FRW_F06_MODE']
if mode=='preflight':
 from f06_contract import save
 save(Path('/work/UNO-PREFLIGHT.json'),dict(state='ISOLATED_EMBEDDED_UNO_TYPES_IMPORT_PASS_NO_OFFICE',python=list(sys.version_info[:3]),path=sys.path,macro_NEVER_EXECUTE=0,update_NO_UPDATE=0,pid=os.getpid(),starttime=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],executable_identity=__import__('f06_contract').identity(Path('/proc/self/exe').stat()),Office_starts=0,document_loads=0,secret_reads=0,types=['PropertyValue','XInteractionHandler','DocumentPasswordRequest','DocumentMSPasswordRequest']))
 raise SystemExit(0)
# Wait only for the one already started owned Office. Never start/restart Office.
pipe=os.environ['FRW_F06_PIPE'];attempt=Path(os.environ['FRW_F06_ATTEMPT']);deadline=float(os.environ['FRW_F06_UNIT_START'])+300-20
if attempt.parent!=Path('/work') or attempt.name not in ('attempt-1','attempt-2','attempt-3') or pipe!='f06_'+os.environ['FRW_F06_NONCE']+'_a'+attempt.name[-1]:raise RuntimeError('ATTEMPT_PIPE_SCOPE')
ctx=uno.getComponentContext();resolver=ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',ctx)
while True:
 if time.monotonic()>=deadline:raise TimeoutError('OWN_PIPE_CONNECT_DEADLINE')
 try:remote=resolver.resolve('uno:pipe,name='+pipe+';urp;StarOffice.ComponentContext');break
 except NoConnectException:
  # Only the typed not-listening startup condition permits another connect.
  time.sleep(.05)
# Parent inside verifies actual socket owner, fd, process birth and argv before
# this client is permitted to load any document or read a credential.
desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
components=desktop.getComponents().createEnumeration();component_count=0
while components.hasMoreElements():
 components.nextElement();component_count+=1
 if component_count>0:raise RuntimeError('STARTUP_COMPONENTS_NOT_EMPTY')
ready=attempt/'CLIENT-READY.json'
from f06_contract import save
save(ready,dict(pipe=pipe,pid=os.getpid(),starttime=Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19],state='CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET',component_count=component_count))
while not (attempt/'PIPE-OWNERSHIP-ACCEPTED.json').exists():
 if time.monotonic()>=deadline:raise TimeoutError('PIPE_OWNERSHIP_DEADLINE')
 time.sleep(.02)
save(attempt/'PRODUCER-ENTERED.json',dict(state='ONE_PRODUCER_ENTERED_AFTER_EMPTY_COMPONENTS_AND_PARENT_ACCEPT',pipe=pipe,pid=os.getpid(),credential_read_yet=False,document_loads_yet=0))
sys.argv=['/recipe/office_fixture_driver.py','--root','/work','--input-root','/inputs','--credential-ref','/inputs/credential.private.json','--uno-pipe',pipe,'--mode','produce' if mode=='generate' else 'verify-inputs','--input-manifest-sha256',os.environ['FRW_F06_INPUT_SHA']]
# pyuno stores its interpreter Runtime in the existing __main__ module.
# A temporary runpy __main__ hides that initialized Runtime. Keep __main__
# intact and call the unchanged producer main from a separate library namespace.
producer_phase='producer_library_load'
try:
 producer=runpy.run_path('/recipe/office_fixture_driver.py',run_name='f06_producer_library')
 producer_phase='producer_main'
 raise SystemExit(producer['main']())
except Exception as exc:
 # Frames only: never format the exception, traceback, source text or locals.
 frames=[];tb=exc.__traceback__;seen=0
 while tb is not None and seen<64:
  seen+=1;code=tb.tb_frame.f_code
  if code.co_filename in ('/recipe/office_fixture_driver.py','/recipe/embedded_entry.py'):
   name=code.co_name
   frames.append(dict(file=code.co_filename,line=tb.tb_lineno,function=name if len(name)<=128 and (name.isidentifier() or name=='<module>') else 'REDACTED'))
  tb=tb.tb_next
 kind=type(exc).__name__
 error=dict(status='ERROR',exception_class=kind if len(kind)<=128 and all(part.isidentifier() for part in kind.split('.')) else 'REDACTED',phase=producer_phase,source_frames=frames,traceback_truncated=tb is not None,exception_messages_or_locals_saved=False)
 error['location_file_save_failed']=False
 try:save(attempt/'PRODUCER-ERROR-LOCATION.json',error)
 except Exception:error['location_file_save_failed']=True
 # An observer/stdout failure must not print the original exception context.
 try:print(json.dumps(error))
 except Exception:pass
 raise SystemExit(2)
