"""New finite readonly assessment of the saved Standard3.2 g6 bytes on installed207.

No producer, edit, model, send, Office, native app role, marker, overlay or user DB.
The historical nativeg6 cfb_header FAIL/editnone and all consumed native R3 remain unchanged.
"""
from pathlib import Path
import datetime
import hashlib
import importlib
import json
import os
import resource
import sys
import time
import uuid

B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
N=H/'hermes-agent'
O=B/'F06-INSTALLED207-RETAINED-G6-DOCX-READONLY-20261112'
SOURCE=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6/work/encrypted-inputs/f06-new-encrypted.docx')
CREDENTIAL=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6/inputs/credential.private.json')
EXPECTED='22b0dcb3fed3d979b37ff701af42b00d3756d76a863e8f8c736405acc9c33fd5'
os.umask(0o077)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def identity(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def main():
 assert sys.flags.isolated and sys.dont_write_bytecode and __debug__
 start=time.monotonic();deadline=start+60
 def tick():
  if time.monotonic()>=deadline:raise TimeoutError('OWN_READONLY_QUALIFICATION_DEADLINE')
 os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[-2:])
 resource.setrlimit(resource.RLIMIT_CPU,(45,45));resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 p=B/'CORE207-ACTUAL-INSTALLED-CLOSED-20261112.json'
 assert sha(p)=='996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'
 installed=json.loads(p.read_bytes())
 for pin in installed['installed']['canonical4'].values():assert ref(pin['path'])==pin
 assert SOURCE.resolve()==SOURCE and CREDENTIAL.resolve()==CREDENTIAL
 before=SOURCE.stat();credential_before=CREDENTIAL.stat();credential_sha=sha(CREDENTIAL)
 assert before.st_uid==credential_before.st_uid==os.getuid() and before.st_nlink==credential_before.st_nlink==1
 assert before.st_size==23040 and sha(SOURCE)==EXPECTED
 receipt=json.loads((H/'hermes-agent.source.json').read_bytes())
 codec=N/'tools/scoped_ooxml_password.py'
 assert sha(codec)==receipt['files']['tools/scoped_ooxml_password.py']['sha256']=='59c65471582a30baf61ed8367925b477d00af70d6d1211e6044ecb2a3d35029c'
 # Only these own synthetic credential/cipher bodies are read, inside this
 # admitted bounded readonly helper operation. No values become metadata/logs.
 secret=json.loads(CREDENTIAL.read_bytes())
 password=secret['password']
 assert type(password)is str and password
 wrong='frw-future-readonly-wrong-'+uuid.uuid4().hex
 assert wrong!=password
 data=SOURCE.read_bytes()
 def audit(event,args):
  if event in ('socket.connect','socket.connect_ex','socket.bind','subprocess.Popen','os.system','os.fork','os.posix_spawn','os.exec'):
   raise PermissionError('NO_NETWORK_OR_PROCESS_IN_READONLY_CODEC_ASSESSMENT')
  if event=='open':
   path,mode,flags=args
   writable=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if writable:
    physical=Path(os.fsdecode(path)) if isinstance(path,(str,bytes,os.PathLike)) else None
    if physical is None or not physical.is_relative_to(O):raise PermissionError('NO_EXTERNAL_WRITE_OR_PLAINTEXT_FILE')
  if event in ('os.mkdir','os.remove','os.rename','os.rmdir','os.chmod','os.chown','os.symlink','os.link','os.truncate','os.utime'):
   raise PermissionError('NO_FILESYSTEM_MUTATION_IN_READONLY_CODEC_ASSESSMENT')
 sys.addaudithook(audit)
 sys.path.insert(0,str(N))
 state='NOT_RUN';stage='actual_installed_codec_import';facts={};error_class=None;safe_code=None
 try:
  m=importlib.import_module('tools.scoped_ooxml_password')
  assert Path(m.__file__).resolve()==codec and 'run_agent' not in sys.modules
  stage='correct_read_same_saved_ciphertext'
  clear,metadata=m.prepare_read(data,'docx',password,checkpoint=tick)
  assert metadata['encryption_profile']=='standard3.2-aes128-sha1' and metadata['data_integrity_verified'] is False and metadata['password_verified'] is True and metadata['package_structure_verified'] is True
  assert type(clear)is bytes and len(clear)<=8*1024**2
  facts['correct_read']={'passed':True,'metadata':metadata,'clear_package_bytes':len(clear),'clear_package_sha256':hashlib.sha256(clear).hexdigest(),'plaintext_written_or_logged':False}
  # No extra payload is written. Wrong password exercises tag rejection on the
  # exact same retained encrypted bytes before any returned clear package.
  stage='wrong_read_same_saved_ciphertext'
  rejected=False
  try:m.prepare_read(data,'docx',wrong,checkpoint=tick)
  except m.OOXMLPasswordError as error:
   rejected=str(error)=='ooxml_password_incorrect' and error.__context__ is None
  facts['wrong_password_read']={'passed':rejected,'fixed_code':'ooxml_password_incorrect' if rejected else None,'raw_error_or_secret_logged':False}
  assert rejected
  assert sha(SOURCE)==EXPECTED and identity(SOURCE.stat())==identity(before) and sha(CREDENTIAL)==credential_sha and identity(CREDENTIAL.stat())==identity(credential_before)
  for pin in installed['installed']['canonical4'].values():assert ref(pin['path'])==pin
  state='PASS_INSTALLED207_SAME_G6_STANDARD32_NATIVE_CODEC_READ_ONLY'
 except BaseException as error:
  error_class=type(error).__module__+'.'+type(error).__qualname__
  value=str(error)
  if value in {'odf_crypto_unavailable','odf_password_required','odf_password_invalid','ooxml_password_incorrect','odf_encryption_parameters_invalid','odf_encryption_resource_limit'}:safe_code=value
  state='FAIL_OR_PARTIAL_INSTALLED207_SAME_G6_STANDARD32_READ_ONLY'
 result=dict(schema='friday.root.installed207.retained-g6-standard32-readonly.v1',state=state,stage=stage,
  at_moscow=datetime.datetime.now().astimezone().isoformat(),installation=ref(p),codec=ref(codec),
  original_ciphertext=ref(SOURCE),bytes=before.st_size,credential_values_logged=False,
  original_sha_after=sha(SOURCE),credential_sha_unchanged=sha(CREDENTIAL)==credential_sha,
  facts=facts,exception_class=error_class,fixed_code=safe_code,elapsed_seconds=time.monotonic()-start,
  old_native_g6_cfb_header_FAIL_and_editnone_preserved=True,old_native_R3_replayed=False,
  new_effect='Two memory-only readonly calls on installed actual codec and retained23040B: correct read and meaningful wrong-password tag rejection. No actual oldactor/request/UUID reuse.',
  no_producer_edit_model_Office_send_Store_or_DB=True,plaintext_written_or_logged=False,
  support_limits='Nativecodec Standard3.2 password verification/ZIP read only, NOT authenticatedMAC/data_integrity_verified=false. No ordinaryuserpath/delivery/editor/realOffice/fidelity/formalF06/full170/120/B00 PASS; original ciphertext unchanged.',
  actual_H_source_admission_not_overridden=True,own_budget={'wall':60,'CPU':45,'AS':2*1024**3,'CPUs':2})
 (O/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps(dict(state=state,stage=stage,ref=ref(O/'RESULT.json'),safe_code=safe_code,checks=list(facts))))
 return 0 if state.startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
