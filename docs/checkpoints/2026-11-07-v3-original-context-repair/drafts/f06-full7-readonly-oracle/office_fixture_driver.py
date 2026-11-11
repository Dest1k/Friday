#!/usr/bin/env python3
"""DORMANT independent readonly retained-input Office oracle; Root owns separate Office admission.
No launcher. Dedicated externally isolated UNO pipe/profile, total deadline and
cleanup are Root-owned. Secrets flow private0600 JSON -> memory/UNO props only.
"""
import argparse,hashlib,json,os,stat,zipfile
import f06_contract as c
from pathlib import Path
from xml.etree import ElementTree as ET

# BEGIN EXACT request_args_compat_v2.py SHA256 f57c76e450b7aa024e7726b3fef7973e317120ab8eee317095f6b38d814ae779
"""DORMANT, process-local compatibility for exactly four password exceptions and source-identified ErrorCodeRequest2.

No UNO imports, Office connection, global helper changes or acceptance rule.
Root may call install_request_args_compat(uno) in an admitted fresh client after
pinning the installed UNO sources and this file. Every non-args assignment still
uses the original UNO setter; Message/Name/password data are never inspected.
"""

REQUEST_NAMES = (
    "com.sun.star.task.DocumentPasswordRequest",
    "com.sun.star.task.DocumentMSPasswordRequest",
    "com.sun.star.task.DocumentPasswordRequest2",
    "com.sun.star.task.DocumentMSPasswordRequest2",
    "com.sun.star.task.ErrorCodeRequest2",
)


def _args_setter(original):
    def set_request_attribute(self, name, value):
        if name == "args":
            if type(value) is not tuple:
                raise TypeError("password_request_args_tuple_required")
            return BaseException.__setattr__(self, name, value)
        return original(self, name, value)
    return set_request_attribute


def install_request_args_compat(uno):
    """Validate all five exact generated classes before changing any one.

    Returned tuple is an in-memory restore token, never a JSON artifact. A fresh
    client exits after the bounded probe. Repeated installation is rejected.
    """
    original = uno._uno_struct__setattr__
    classes = tuple(uno.getClass(name) for name in REQUEST_NAMES)
    if len(set(classes)) != len(REQUEST_NAMES):
        raise ValueError("password_request_class_identity")
    for name, cls in zip(REQUEST_NAMES, classes):
        if type(cls) is not type or not issubclass(cls, Exception):
            raise ValueError("password_request_exception_class_required")
        if cls.__dict__.get("__pyunostruct__") != name:
            raise ValueError("password_request_exact_type_required")
        if cls.__dict__.get("__setattr__") is not original:
            raise ValueError("password_request_original_setter_required")
    token = tuple((cls, original, _args_setter(original)) for cls in classes)
    changed = []
    try:
        for cls, old_setter, replacement in token:
            cls.__setattr__ = replacement
            changed.append((cls, old_setter))
    except Exception:
        for cls, old_setter in reversed(changed):
            cls.__setattr__ = old_setter
        raise
    return token


def restore_request_args_compat(token):
    """CAS the entire token before restoring; never overwrite a later mutation."""
    if type(token) is not tuple or len(token) != len(REQUEST_NAMES):
        raise ValueError("password_request_restore_token")
    for name, row in zip(REQUEST_NAMES, token):
        if type(row) is not tuple or len(row) != 3:
            raise ValueError("password_request_restore_row")
        cls, original, replacement = row
        if type(cls) is not type or cls.__dict__.get("__pyunostruct__") != name:
            raise ValueError("password_request_restore_class")
        if cls.__dict__.get("__setattr__") is not replacement:
            raise ValueError("password_request_restore_cas")
    for cls, original, replacement in token:
        cls.__setattr__ = original

# END EXACT request_args_compat_v2.py

# BEGIN EXACT callback_observer_v2.py SHA256 eb3765d73b7e64d970f2438e68728f24a65842e1d8be300016f99ac978065c5c
"""DORMANT source-only F06 callback instrumentation; imports no UNO and runs no Office.

Root injects already admitted UNO objects. Preserve original handler decisions and
re-raise callback faults. This observer NEVER promotes a load failure to a password
refusal. Do not serialize payload/request/continuation objects or exception values.
"""
import re

_QUALIFIED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,16}\Z")
_FRAME_FILES = frozenset(("callback_observer.py", "callback_observer_v2.py", "office_fixture_driver.py", "uno.py", "unohelper.py"))


def safe_type(value):
    """Class identity only; UNO generated __name__ can already be qualified."""
    cls = type(value)
    name = cls.__name__
    module = cls.__module__
    candidate = name if "." in name else module + "." + name
    return candidate if len(candidate) <= 240 and _QUALIFIED.fullmatch(candidate) else "REDACTED_TYPE"


def safe_exception(error):
    """No Message, str/repr, args, locals, payload fields or file paths."""
    frames = []
    tb = error.__traceback__
    while tb is not None and len(frames) < 12:
        code = tb.tb_frame.f_code
        filename = code.co_filename.rsplit("/", 1)[-1]
        filename = filename if filename in _FRAME_FILES else "OTHER_SOURCE"
        function = code.co_name
        if len(function) > 100 or not _QUALIFIED.fullmatch(function):
            function = "OTHER_FUNCTION"
        frames.append({"source": filename, "function": function, "line": tb.tb_lineno})
        tb = tb.tb_next
    return {"exception_class": safe_type(error), "source_frames": frames}


def make_abort_handler(uno, unohelper, XInteractionHandler, DocumentPasswordRequest, DocumentMSPasswordRequest, ErrorCodeRequest2=None):
    """Only the existing callback is instrumented; selection semantics unchanged."""
    class AbortInteractions(unohelper.Base, XInteractionHandler):
        def __init__(self):
            self.events = []

        def handle(self, request):
            # FIRST callback operation: make an event before any UNO/type operation.
            event = {"phase": "entered", "phases": ["entered"], "request_kind": "UNCLASSIFIED", "abort_selected": False}
            self.events.append(event)

            def phase(name):
                event["phase"] = name
                event["phases"].append(name)

            try:
                phase("request_type_before")
                event["request_class"] = safe_type(request)
                phase("get_request_before")
                payload = request.getRequest()
                phase("get_request_after")
                event["payload_class"] = safe_type(payload)
                phase("classify_before")
                is_standard = isinstance(payload, DocumentPasswordRequest)
                is_ms = False if is_standard else isinstance(payload, DocumentMSPasswordRequest)
                event["is_document_password"] = is_standard
                event["is_document_ms_password"] = is_ms
                event["request_kind"] = "DocumentPasswordRequest" if is_standard else "DocumentMSPasswordRequest" if is_ms else "OTHER"
                is_error_code = not is_standard and not is_ms and ErrorCodeRequest2 is not None and type(payload) is ErrorCodeRequest2
                event["is_error_code_request2"] = is_error_code
                if is_error_code:
                    event["request_kind"] = "ErrorCodeRequest2"
                    phase("error_code_before")
                    error_code = payload.ErrCode
                    if type(error_code) is not int or not -(2**31) <= error_code < 2**31:
                        raise ValueError("typed_error_code_contract")
                    event["error_code"] = error_code
                    phase("error_code_after")
                phase("classify_after")
                phase("get_continuations_before")
                continuations = request.getContinuations()
                phase("get_continuations_after")
                event["continuation_attempts"] = []
                for continuation in continuations:
                    attempt = {"phase": "query_abort_type_before"}
                    event["continuation_attempts"].append(attempt)
                    phase("query_abort_type_before")
                    abort_type = uno.getTypeByName("com.sun.star.task.XInteractionAbort")
                    phase("query_interface_before")
                    attempt["phase"] = "query_interface_before"
                    abort = continuation.queryInterface(abort_type)
                    attempt["abort_available"] = abort is not None
                    attempt["phase"] = "query_interface_after"
                    phase("query_interface_after")
                    if abort is not None:
                        attempt["phase"] = "select_before"
                        phase("select_before")
                        abort.select()
                        event["abort_selected"] = True
                        attempt["phase"] = "select_after"
                        phase("select_after")
                        return
                phase("no_abort_continuation")
            except Exception as error:
                event["callback_error_phase"] = event["phase"]
                try:
                    event["callback_error"] = safe_exception(error)
                except Exception:
                    event["callback_error"] = {"exception_class": "DIAGNOSTIC_FAILURE", "source_frames": []}
                phase("callback_exception_reraised")
                raise

    return AbortInteractions()


def observed_password_abort(events):
    """Necessary event evidence only; caller must ALSO prove unopened load.

    No generic None/exception/ErrorCode/ArgumentPosition is password evidence.
    Requiring completed selection rejects callback failures and all other kinds.
    """
    return bool(events) and all(
        e.get("request_kind") in ("DocumentPasswordRequest", "DocumentMSPasswordRequest")
        and e.get("abort_selected") is True
        and e.get("phase") == "select_after"
        and "callback_error" not in e
        and "callback_error_phase" not in e
        for e in events
    )


# include/comphelper/errcode.hxx: Io=0, Abort=1, ERRCODE_IO_ABORT code27;
# ERRCODE_ABORT aliases it. ErrorCodeRequest2.ErrCode is IDL signed long.
EXPECTED_IO_ABORT = 283


def observed_password_refusal_sequence(events, fmt):
    """Necessary exact event order ONLY; unopened+same-byte positive required.

    Primary26.2 ODF abort emits one password Abort then one ErrorCodeRequest2
    carrying ERRCODE_IO_ABORT. Divergent types/codes/order, extra callbacks,
    incomplete selections and callback faults reject. Source verifier can mask
    internal IO/corruption as WrongPassword: this is cancellation evidence,
    not a cryptographic cause proof; same-byte correct semantics remain required.
    """
    if not isinstance(events, list):
        return False
    if fmt in ("docx", "xlsx", "pptx"):
        return len(events) == 1 and events[0].get("request_kind") == "DocumentMSPasswordRequest" and observed_password_abort(events)
    if fmt not in ("odt", "ods", "odp") or len(events) != 2:
        return False
    password, cancellation = events
    return (
        password.get("request_kind") == "DocumentPasswordRequest"
        and observed_password_abort([password])
        and cancellation.get("request_kind") == "ErrorCodeRequest2"
        and cancellation.get("payload_class") == "com.sun.star.task.ErrorCodeRequest2"
        and cancellation.get("is_error_code_request2") is True
        and type(cancellation.get("error_code")) is int
        and cancellation["error_code"] == EXPECTED_IO_ABORT
        and cancellation.get("abort_selected") is True
        and cancellation.get("phase") == "select_after"
        and "callback_error" not in cancellation
        and "callback_error_phase" not in cancellation
    )

# END EXACT callback_observer_v2.py

FORMATS={'docx':'Office Open XML Text','xlsx':'Calc MS Excel 2007 XML','pptx':'Impress MS PowerPoint 2007 XML','odt':'writer8','ods':'calc8','odp':'impress8'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def private_root(raw):
 p=Path(raw)
 if not p.is_absolute() or '..' in p.parts or p!=p.resolve(strict=True):raise ValueError('root_not_canonical')
 s=p.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('private_root_required')
 return p

def private_file(raw,root):
 p=Path(raw)
 if '..' in p.parts or not p.is_absolute() or not p.is_relative_to(root) or p!=p.resolve(strict=True):raise ValueError('file_not_canonical_within_root')
 for parent in [p.parent,*p.parent.parents]:
  s=parent.lstat()
  if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('private_directory_required')
  if parent==root:break
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=0o600:raise ValueError('private_file_required')
 return p


JOBS=[(fmt,filt,True) for fmt,filt in FORMATS.items()]+[('odt',FORMATS['odt'],False)]
PROFILES=('compatible1.3_or_Agile',)*6+('current_default_latest_odt_negative',)
def target_name(fmt,compatible):
 return ('f06-new-encrypted.' if compatible else 'f06-new-default-latest.')+fmt

def reconciled_inputs(root,expected):
 manifest=private_file(root/'RECONCILED-INPUTS.json',root)
 if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or sha(manifest)!=expected:raise ValueError('reconciled_manifest_pin')
 obj=json.loads(manifest.read_text());rows=obj['fixtures']
 if obj.get('schema')!='friday.f06.reconciled-existing-inputs.v1' or obj.get('semantic')!='ALPHA17' or type(obj.get('known_prefix_count')) is not int or obj['known_prefix_count']!=len(rows) or len(rows)!=7:raise ValueError('reconciled_prefix_contract')
 custody=Path(obj['custody_root'])
 c.reconciled_contract(obj)
 if custody!=c.ORIGINAL_CUSTODY:raise ValueError('reconciled_custody_path')
 result=[]
 for i,(row,(fmt,filt,compatible)) in enumerate(zip(rows,JOBS)):
  name=target_name(fmt,compatible)
  if row.get('format')!=fmt or row.get('fixture_profile')!=PROFILES[i] or row.get('name')!=name or row.get('path')!=str(custody/name):raise ValueError('reconciled_family_name_profile_path')
  p=private_file(root/'encrypted-inputs'/name,root)
  if type(row.get('bytes')) is not int or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('reconciled_existing_bytes_pin')
  result.append((row,p,fmt,filt,compatible))
 if set(q.name for q in (root/'encrypted-inputs').iterdir())!={r[1].name for r in result}:raise ValueError('reconciled_exact_prefix_directory')
 return manifest,obj,result

def atomic_result(path,value):
 # Own result only, never any encrypted input. Preserve previous complete prefix.
 tmp=path.with_name(path.name+'.next')
 fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:
  json.dump(value,f,ensure_ascii=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 if os.path.lexists(path):private_file(path,path.parent)
 os.replace(tmp,path)
 d=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(d)
 finally:os.close(d)

def main():
 c.require_final_codec()
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--input-root',required=True);ap.add_argument('--credential-ref',required=True);ap.add_argument('--uno-pipe',required=True);ap.add_argument('--mode',choices=['verify-inputs'],required=True);ap.add_argument('--input-manifest-sha256',required=True);a=ap.parse_args()
 os.umask(0o077);root=private_root(a.root);input_root=private_root(a.input_root)
 c.operation(os.environ.get('FRW_F06_KEY'),os.environ.get('FRW_F06_MODE'))
 if root!=Path('/work') or input_root!=Path('/inputs'):raise ValueError('fixed_namespace_roots_required')
 if not a.uno_pipe.startswith('f06_') or not a.uno_pipe.replace('_','').isalnum():raise ValueError('dedicated_pipe_required')
 manifest,reconciled,existing=reconciled_inputs(input_root,a.input_manifest_sha256)
 cred=private_file(a.credential_ref,input_root);secret=json.loads(cred.read_text());password=secret['password'];wrong=secret['wrong_password']
 if not isinstance(password,str) or not isinstance(wrong,str) or not password or not wrong or password==wrong:raise ValueError('credential_contract')
 import uno,unohelper
 from com.sun.star.beans import PropertyValue
 from com.sun.star.task import XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest,ErrorCodeRequest2
 from com.sun.star.lang import IllegalArgumentException
 compat_token=install_request_args_compat(uno)
 handler=make_abort_handler(uno,unohelper,XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest,ErrorCodeRequest2)
 def prop(name,value):
  p=PropertyValue();p.Name=name;p.Value=value;return p
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
 remote=resolver.resolve('uno:pipe,name='+a.uno_pipe+';urp;StarOffice.ComponentContext')
 desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
 def envelope(path,fmt,compatible):
  if fmt in ('docx','xlsx','pptx'):
   if path.read_bytes()[:8]!=bytes.fromhex('d0cf11e0a1b11ae1'):raise ValueError('ooxml_not_compound_encrypted_container')
   return {'container':'CFB','independent_oracle':'Office missing/wrong/correct reopen; signature alone insufficient'}
  ns='{urn:oasis:names:tc:opendocument:xmlns:manifest:1.0}'
  with zipfile.ZipFile(path) as z:raw=z.read('META-INF/manifest.xml');names=set(z.namelist())
  if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('manifest_dtd')
  entries=[]
  for entry in ET.fromstring(raw):
   enc=entry.find(ns+'encryption-data')
   if enc is None:continue
   alg=enc.find(ns+'algorithm');kd=enc.find(ns+'key-derivation');start=enc.find(ns+'start-key-generation')
   if alg is None or kd is None:raise ValueError('odf_encryption_descriptor')
   params={'member':entry.get(ns+'full-path'),'algorithm':alg.get(ns+'algorithm-name'),'kdf':kd.get(ns+'key-derivation-name'),'rounds':kd.get(ns+'iteration-count'),'checksum':enc.get(ns+'checksum-type'),'algorithm_attributes':dict(alg.attrib),'kdf_attributes':dict(kd.attrib),'start_key_attributes':dict(start.attrib) if start is not None else None}
   if compatible and (params['algorithm']!='http://www.w3.org/2001/04/xmlenc#aes256-cbc' or params['kdf'] not in ('PBKDF2',ns[1:-1]+'#pbkdf2') or params['rounds']!='100000' or params['checksum']!=ns[1:-1]+'#sha256-1k'):raise ValueError('odf_profile_outside_compatible_fixture_bounds')
   entries.append(params)
  if not entries:raise ValueError('odf_no_encrypted_members')
  if compatible and (not any(e['member']=='content.xml' for e in entries) or 'encrypted-package' in names):raise ValueError('odf_member_profile_required')
  return {'container':'ODF','encrypted_members':entries,'profile_DefaultVersion':10 if compatible else 3,'encrypted_package_present':'encrypted-package' in names,'checksum_authenticity':'NOT_A_SIGNATURE','coverage':'bounded compatible1.3' if compatible else 'current default/latest qualification; actual native reason still required'}
 def load(path,supplied=None):
  props=[prop('Hidden',True),prop('ReadOnly',True),prop('MacroExecutionMode',0),prop('UpdateDocMode',0),prop('InteractionHandler',handler)]
  if supplied is not None:props.append(prop('Password',supplied))
  return desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(path)),'_blank',0,tuple(props))
 def close(doc):
  try:doc.close(True)
  except Exception:doc.dispose()
 def semantic(doc,fmt,edited=False):
  if fmt in ('xlsx','ods'):
   sheet=doc.getSheets().getByName('F06Data');return sheet.getCellRangeByName('A2').getString()=='keep-001' and sheet.getCellRangeByName('B2').getValue()==(23 if edited else 17)
  wanted='F06 SYNTHETIC '+('BRAVO' if edited else 'ALPHA')+' 11 NOV'
  if fmt in ('docx','odt'):return wanted in doc.getText().getString() and 'F06 synthetic invariant paragraph' in doc.getText().getString()
  page=doc.getDrawPages().getByIndex(0);texts=[]
  for i in range(page.getCount()):
   shape=page.getByIndex(i)
   if hasattr(shape,'getString'):texts.append(shape.getString())
  return any(wanted in t for t in texts) and any('F06 synthetic invariant body' in t for t in texts)
 def probe(path,fmt,supplied,edited):
  doc=None;events_start=len(handler.events);answer={'opened':False,'semantic_match':False,'expected_password_refusal':False}
  load_exception_allowed=False
  try:
   doc=load(path,supplied)
   if doc is not None:
    answer['opened']=True
    try:answer['semantic_match']=bool(semantic(doc,fmt,edited))
    except Exception as error:answer['semantic_exception_class']=safe_type(error)
  except Exception as error:
   answer['load_exception_class']=safe_type(error)
   if fmt in ('docx','xlsx','pptx') and type(error) is IllegalArgumentException and answer['load_exception_class']=='com.sun.star.lang.IllegalArgumentException':
    position=error.ArgumentPosition
    answer['load_argument_position']=position if type(position) is int else None
    load_exception_allowed=type(position) is int and position==1
  finally:
   events=handler.events[events_start:];answer['interaction_events']=events
   typed_sequence=observed_password_refusal_sequence(events,fmt)
   # Sequence alone is insufficient: the load must remain unopened, and a
   # thrown load exception must be this exact observed UNO class. Generic
   # IllegalArgumentException, None and callback failures are never evidence.
   answer['expected_password_refusal']=answer['opened'] is False and doc is None and typed_sequence and ('load_exception_class' not in answer or load_exception_allowed)
   if doc is not None:close(doc)
  return answer
 out=root/'existing-input-oracle';out.mkdir(mode=0o700,exist_ok=False)
 jobs=JOBS
 rows=[];custody=[]
 for index,(fmt,filt,compatible) in enumerate(jobs):
  edited=False;original=existing[index][0];src=existing[index][1];before=sha(src);target=src
  # Custody precedes optional envelope/oracle checking. Checker failure cannot
  # erase already created bytes or authorize producing them again.
  target_before=sha(target)
  custody.append({'name':target.name,'format':fmt,'fixture_profile':PROFILES[index],'path':str(target),'sha256':target_before,'bytes':target.stat().st_size})
  atomic_result(out/'CUSTODY.json',{'mode':a.mode,'known_prefix_count':len(custody),'planned_rows':len(jobs),'fixtures':custody,'oracle_status':'PENDING_OR_INCONCLUSIVE','never_regenerate_for_checker_failure':True})
  descriptor=None;envelope_error=None
  try:descriptor=envelope(target,fmt,compatible)
  except Exception as error:envelope_error=type(error).__name__
  tests={'missing':probe(target,fmt,None,edited),'wrong':probe(target,fmt,wrong,edited),'correct':probe(target,fmt,password,edited)}
  unchanged=sha(src)==before and sha(target)==target_before
  passed=unchanged and envelope_error is None and tests['missing']['expected_password_refusal'] and tests['wrong']['expected_password_refusal'] and tests['correct']['opened'] and tests['correct']['semantic_match'] and not tests['correct']['interaction_events']
  rows.append({'format':fmt,'fixture_profile':PROFILES[index],'filter':filt,'source_path':str(src),'source_sha256':before,'path':str(target),'sha256':target_before,'bytes':target.stat().st_size,'independent_office_password_and_semantics_pass':passed,'tests':tests,'envelope':descriptor,'envelope_exception_class':envelope_error,'same_input_bytes_preserved':unchanged,'credential_ref':str(cred),'new_bytes':False,'copy_is_original':False,'original_host_path':original['path'],'raw_original_namespace_path':original['raw_original_namespace_path'],'original_identity':original['identity'],'recovered_old_bytes':False,'native_protected_result':'NOT_TESTED; exact current consumer qualification required'})
  atomic_result(out/'RESULT.json',{'mode':a.mode,'stores':0,'password_probes_completed':3*len(rows),'original_g6_oracle':reconciled['original_oracle'],'original_g6_all_pass':False,'original_ciphertext_custody_root':reconciled['custody_root'],'staged_copies_readonly':True,'input_manifest':str(manifest),'input_manifest_sha256':a.input_manifest_sha256,'rows':rows,'planned_rows':len(jobs),'whole_seven_covered':len(jobs)==7 and len(rows)==7,'all_pass':len(rows)==len(jobs) and all(r['independent_office_password_and_semantics_pass'] for r in rows),'oracle':'independent existing LibreOffice through dedicated UNO pipe','visual_fidelity':'NOT_TESTED','F06_formal_or_delivery':'NOT_RUN'})
  if not unchanged:raise ValueError('source_or_target_changed_after_operation')
 print(json.dumps({'fixtures':len(rows),'passed':sum(r['independent_office_password_and_semantics_pass'] for r in rows)}))
 restore_request_args_compat(compat_token)
 return 0 if all(r['independent_office_password_and_semantics_pass'] for r in rows) else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:
  print(json.dumps({'status':'ERROR','exception_class':type(exc).__name__}));raise SystemExit(2)
