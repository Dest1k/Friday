#!/usr/bin/env python3
"""DORMANT independent Office producer/oracle; Root owns separate Office admission.
No launcher. Dedicated externally isolated UNO pipe/profile, total deadline and
cleanup are Root-owned. Secrets flow private0600 JSON -> memory/UNO props only.
"""
import argparse,hashlib,json,os,stat,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
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

def manifest_inputs(root,mode,expected):
 name='PLAIN-INPUTS.json' if mode=='produce' else 'NATIVE-OUTPUTS.json'
 manifest=private_file(root/name,root)
 if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or sha(manifest)!=expected:raise ValueError('input_manifest_pin')
 obj=json.loads(manifest.read_text());items=obj['fixtures']
 if len(items)!=6 or {r['format'] for r in items}!=set(FORMATS):raise ValueError('input_manifest_six_families')
 rows={r['format']:r for r in items};paths={}
 for fmt,row in rows.items():
  basename=('f06-new-plain.' if mode=='produce' else 'f06-native-edited.')+fmt
  # Manifest retains original host path; exact bytes are staged under /work.
  if Path(row['path']).name!=basename:raise ValueError('input_manifest_name')
  p=private_file(root/('plain-inputs' if mode=='produce' else 'native-outputs')/basename,root)
  if sha(p)!=row['sha256']:raise ValueError('input_source_pin')
  paths[fmt]=p
 return manifest,rows,paths

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--credential-ref',required=True);ap.add_argument('--uno-pipe',required=True);ap.add_argument('--mode',choices=['produce','verify-native-edits'],default='produce');ap.add_argument('--input-manifest-sha256',required=True);a=ap.parse_args()
 os.umask(0o077);root=private_root(a.root)
 if not a.uno_pipe.startswith('f06_') or not a.uno_pipe.replace('_','').isalnum():raise ValueError('dedicated_pipe_required')
 manifest,pinned,paths=manifest_inputs(root,a.mode,a.input_manifest_sha256)
 cred=private_file(a.credential_ref,root);secret=json.loads(cred.read_text());password=secret['password'];wrong=secret['wrong_password']
 if not isinstance(password,str) or not isinstance(wrong,str) or not password or not wrong or password==wrong:raise ValueError('credential_contract')
 import uno,unohelper
 from com.sun.star.beans import PropertyValue
 from com.sun.star.task import XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest
 class AbortInteractions(unohelper.Base,XInteractionHandler):
  def __init__(self):self.events=[]
  def handle(self,request):
   payload=request.getRequest()
   kind='DocumentPasswordRequest' if isinstance(payload,DocumentPasswordRequest) else 'DocumentMSPasswordRequest' if isinstance(payload,DocumentMSPasswordRequest) else 'OTHER'
   event={'request_kind':kind,'abort_selected':False};self.events.append(event)
   for continuation in request.getContinuations():
    abort=continuation.queryInterface(uno.getTypeByName('com.sun.star.task.XInteractionAbort'))
    if abort is not None:abort.select();event['abort_selected']=True;return
 handler=AbortInteractions()
 def prop(name,value):
  p=PropertyValue();p.Name=name;p.Value=value;return p
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
 remote=resolver.resolve('uno:pipe,name='+a.uno_pipe+';urp;StarOffice.ComponentContext')
 desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
 provider=remote.ServiceManager.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider',remote)
 config=provider.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess',(prop('nodepath','/org.openoffice.Office.Common/Save/ODF'),))
 def profile(version):
  config.setPropertyValue('DefaultVersion',uno.Any('short',version));config.commitChanges()
  if config.getPropertyValue('DefaultVersion')!=version:raise ValueError('odf_profile_readback')
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
  try:
   doc=load(path,supplied)
   if doc is not None:
    answer['opened']=True
    try:answer['semantic_match']=bool(semantic(doc,fmt,edited))
    except Exception as e:answer['semantic_exception_class']=type(e).__name__
   else:
    events=handler.events[events_start:]
    answer['expected_password_refusal']=bool(events) and all(e['request_kind'] in ('DocumentPasswordRequest','DocumentMSPasswordRequest') and e['abort_selected'] for e in events)
  except Exception as e:answer['load_exception_class']=type(e).__name__
  finally:
   answer['interaction_events']=handler.events[events_start:]
   if doc is not None:close(doc)
  return answer
 out=root/('encrypted-inputs' if a.mode=='produce' else 'native-edit-oracle');out.mkdir(mode=0o700,exist_ok=False)
 # Six compatible ordinary families plus one explicit current-default ODT.
 jobs=[(fmt,filt,True) for fmt,filt in FORMATS.items()]
 if a.mode=='produce':jobs.append(('odt',FORMATS['odt'],False))
 rows=[]
 for fmt,filt,compatible in jobs:
  edited=a.mode=='verify-native-edits';src=paths[fmt];before=sha(src)
  if before!=pinned[fmt]['sha256']:raise ValueError('source_changed_before_operation')
  if edited:target=src
  else:
   profile(10 if compatible else 3)
   target=out/(('f06-new-encrypted.' if compatible else 'f06-new-default-latest.')+fmt)
   if target.exists():raise ValueError('output_exists')
   doc=load(src)
   if doc is None:raise ValueError('plain_input_not_opened')
   try:
    if not semantic(doc,fmt):raise ValueError('plain_input_semantics')
    doc.storeAsURL(uno.systemPathToFileUrl(str(target)),tuple([prop('FilterName',filt),prop('Password',password),prop('Overwrite',False)]))
   finally:close(doc)
   private_file(target,root)
  if sha(src)!=before:raise ValueError('source_changed_after_operation')
  descriptor=envelope(target,fmt,compatible)
  tests={'missing':probe(target,fmt,None,edited),'wrong':probe(target,fmt,wrong,edited),'correct':probe(target,fmt,password,edited)}
  passed=tests['missing']['expected_password_refusal'] and tests['wrong']['expected_password_refusal'] and tests['correct']['opened'] and tests['correct']['semantic_match'] and not tests['correct']['interaction_events']
  rows.append({'format':fmt,'fixture_profile':'compatible1.3_or_Agile' if compatible else 'current_default_latest_odt_negative','filter':filt,'source_path':str(src),'source_sha256':before,'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'independent_office_password_and_semantics_pass':passed,'tests':tests,'envelope':descriptor,'credential_ref':str(cred),'new_bytes':not edited,'recovered_old_bytes':False,'native_protected_result':'NOT_TESTED; exact current consumer qualification required'})
  # Retain complete successful prefix; an external timeout must reconcile it.
  (out/'RESULT.json').write_text(json.dumps({'mode':a.mode,'input_manifest':str(manifest),'input_manifest_sha256':a.input_manifest_sha256,'rows':rows,'planned_rows':len(jobs),'all_pass':len(rows)==len(jobs) and all(r['independent_office_password_and_semantics_pass'] for r in rows),'oracle':'independent existing LibreOffice through dedicated UNO pipe','visual_fidelity':'NOT_TESTED','F06_formal_or_delivery':'NOT_RUN'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'fixtures':len(rows),'passed':sum(r['independent_office_password_and_semantics_pass'] for r in rows)}))
 return 0 if all(r['independent_office_password_and_semantics_pass'] for r in rows) else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:
  print(json.dumps({'status':'ERROR','exception_class':type(exc).__name__}));raise SystemExit(2)
