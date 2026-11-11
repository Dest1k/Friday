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

def manifest_inputs(root,mode,expected,manifest_name=None):
 name=manifest_name or ('PLAIN-INPUTS.json' if mode=='produce' else 'NATIVE-OUTPUTS.json')
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

JOBS=[(fmt,filt,True) for fmt,filt in FORMATS.items()]+[('odt',FORMATS['odt'],False)]
PROFILES=('compatible1.3_or_Agile',)*6+('current_default_latest_odt_negative',)
def target_name(fmt,compatible):
 return ('f06-new-encrypted.' if compatible else 'f06-new-default-latest.')+fmt

def reconciled_inputs(root,expected):
 manifest=private_file(root/'RECONCILED-INPUTS.json',root)
 if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or sha(manifest)!=expected:raise ValueError('reconciled_manifest_pin')
 obj=json.loads(manifest.read_text());rows=obj['fixtures']
 if obj.get('schema')!='friday.f06.reconciled-existing-inputs.v1' or obj.get('semantic')!='ALPHA17' or type(obj.get('known_prefix_count')) is not int or obj['known_prefix_count']!=len(rows) or not 1<=len(rows)<=7:raise ValueError('reconciled_prefix_contract')
 custody=Path(obj['custody_root'])
 if not custody.is_absolute() or '..' in custody.parts:raise ValueError('reconciled_custody_path')
 result=[]
 for i,(row,(fmt,filt,compatible)) in enumerate(zip(rows,JOBS)):
  name=target_name(fmt,compatible)
  if row.get('format')!=fmt or row.get('fixture_profile')!=PROFILES[i] or row.get('name')!=name or row.get('path')!=str(custody/name):raise ValueError('reconciled_family_name_profile_path')
  p=private_file(root/'encrypted-inputs'/name,root)
  if type(row.get('bytes')) is not int or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('reconciled_existing_bytes_pin')
  result.append((row,p,fmt,filt,compatible))
 if set(q.name for q in (root/'encrypted-inputs').iterdir())!={r[1].name for r in result}:raise ValueError('reconciled_exact_prefix_directory')
 return manifest,obj,result

def retained_native_inputs(root,expected):
 # A pinned manifest describes retained bytes; it never grants Office execution.
 manifest=private_file(root/'NATIVE-OUTPUTS.json',root)
 if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected) or sha(manifest)!=expected:raise ValueError('native_manifest_pin')
 obj=json.loads(manifest.read_text());rows=obj.get('fixtures');ids=obj.get('selected_fixture_ids')
 if obj.get('schema')!='friday.f06.retained-native-edit-oracle.v1' or obj.get('state')!='BOUND_RETAINED_BYTES_NOT_EXECUTION_AUTHORITY' or obj.get('semantic')!='BRAVO23':raise ValueError('native_manifest_unbound')
 if type(rows)is not list or type(ids)is not list or type(obj.get('selected_count'))is not int or not 1<=len(rows)<=7 or obj['selected_count']!=len(rows) or len(ids)!=len(rows):raise ValueError('native_selected_count')
 order=['f06-'+str(i) for i in range(1,8)]
 if ids!=[ident for ident in order if ident in ids]:raise ValueError('native_selected_order_unique')
 selected=[];names=[]
 for ident,row in zip(ids,rows):
  if type(row)is not dict or row.get('fixture_id')!=ident:raise ValueError('native_fixture_identity')
  index=order.index(ident);fmt,filt,compatible=JOBS[index]
  name='f06-native-edited.'+fmt if compatible else 'f06-native-edited-default-latest.odt'
  if row.get('format')!=fmt or row.get('fixture_profile')!=PROFILES[index] or row.get('semantic')!='BRAVO23' or row.get('staged_name')!=name:raise ValueError('native_family_profile_semantic')
  host=row.get('path');p=Path(host) if type(host)is str else Path('.')
  if not p.is_absolute() or '..'in p.parts or str(p)!=host or p.suffix!='.'+fmt:raise ValueError('native_original_path')
  p=private_file(root/'native-outputs'/name,root)
  digest=row.get('sha256');size=row.get('bytes')
  if type(digest)is not str or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest) or type(size)is not int or not 0<size<=1000000 or p.stat().st_size!=size or sha(p)!=digest:raise ValueError('native_existing_bytes_pin')
  selected.append((row,p,fmt,filt,compatible));names.append(name)
 if set(p.name for p in (root/'native-outputs').iterdir())!=set(names):raise ValueError('native_exact_selected_directory')
 return manifest,obj,selected

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
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--input-root',required=True);ap.add_argument('--credential-ref',required=True);ap.add_argument('--uno-pipe',required=True);ap.add_argument('--mode',choices=['produce','verify-native-edits','verify-inputs'],default='produce');ap.add_argument('--input-manifest-sha256',required=True);a=ap.parse_args()
 os.umask(0o077);root=private_root(a.root);input_root=private_root(a.input_root)
 if not a.uno_pipe.startswith('f06_') or not a.uno_pipe.replace('_','').isalnum():raise ValueError('dedicated_pipe_required')
 if a.mode=='verify-inputs':
  manifest,reconciled,existing=reconciled_inputs(input_root,a.input_manifest_sha256);pinned={};paths={}
 elif a.mode=='verify-native-edits':
  manifest,retained,existing_edits=retained_native_inputs(input_root,a.input_manifest_sha256);pinned={};paths={}
 else:manifest,pinned,paths=manifest_inputs(input_root,a.mode,a.input_manifest_sha256)
 cred=private_file(a.credential_ref,input_root);secret=json.loads(cred.read_text());password=secret['password'];wrong=secret['wrong_password']
 if not isinstance(password,str) or not isinstance(wrong,str) or not password or not wrong or password==wrong:raise ValueError('credential_contract')
 import uno,unohelper
 if a.mode=='verify-native-edits':
  from request_args_compat_v2 import install_request_args_compat
  from callback_observer_v2 import make_abort_handler,observed_password_refusal_sequence,safe_exception,safe_type
  request_args_compat_token=install_request_args_compat(uno)
  ErrorCodeRequest2=uno.getClass('com.sun.star.task.ErrorCodeRequest2')
  IllegalArgumentException=uno.getClass('com.sun.star.lang.IllegalArgumentException')
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
 handler=make_abort_handler(uno,unohelper,XInteractionHandler,DocumentPasswordRequest,DocumentMSPasswordRequest,ErrorCodeRequest2) if a.mode=='verify-native-edits' else AbortInteractions()
 def prop(name,value):
  p=PropertyValue();p.Name=name;p.Value=value;return p
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
 remote=resolver.resolve('uno:pipe,name='+a.uno_pipe+';urp;StarOffice.ComponentContext')
 desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
 config=None
 if a.mode=='produce':
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
  doc=None;events_start=len(handler.events);answer={'opened':False,'semantic_match':False,'expected_password_refusal':False};allowed_ooxml_exception=False
  try:
   doc=load(path,supplied)
   if doc is not None:
    answer['opened']=True
    try:answer['semantic_match']=bool(semantic(doc,fmt,edited))
    except Exception as e:
     if edited:answer['semantic_exception']=safe_exception(e)
     else:answer['semantic_exception_class']=type(e).__name__
   else:
    events=handler.events[events_start:]
    answer['expected_password_refusal']=bool(events) and all(e['request_kind'] in ('DocumentPasswordRequest','DocumentMSPasswordRequest') and e['abort_selected'] for e in events)
  except Exception as e:
   if edited:
    answer['load_exception']=safe_exception(e)
    if fmt in ('docx','xlsx','pptx') and type(e) is IllegalArgumentException and safe_type(e)=='com.sun.star.lang.IllegalArgumentException':
     try:
      position=e.ArgumentPosition
      allowed_ooxml_exception=type(position) is int and position==1
      answer['load_argument_position']=position if type(position) is int and -32768<=position<32768 else None
     except Exception:answer['load_argument_position']='UNOBSERVED'
   else:answer['load_exception_class']=type(e).__name__
  finally:
   answer['interaction_events']=handler.events[events_start:]
   if doc is not None:close(doc)
  if edited:
   answer['expected_password_refusal']=not answer['opened'] and observed_password_refusal_sequence(answer['interaction_events'],fmt) and ('load_exception' not in answer or allowed_ooxml_exception)
  return answer
 out=root/({'produce':'encrypted-inputs','verify-native-edits':'native-edit-oracle','verify-inputs':'existing-input-oracle'}[a.mode]);out.mkdir(mode=0o700,exist_ok=False)
 jobs=JOBS if a.mode=='produce' else (JOBS[:len(existing)] if a.mode=='verify-inputs' else [(fmt,filt,compatible) for _,_,fmt,filt,compatible in existing_edits])
 rows=[];custody=[]
 for index,(fmt,filt,compatible) in enumerate(jobs):
  edited=a.mode=='verify-native-edits'
  fixture_id=existing_edits[index][0]['fixture_id'] if edited else 'f06-'+str(index+1)
  fixture_profile=existing_edits[index][0]['fixture_profile'] if edited else PROFILES[index]
  if a.mode=='verify-inputs':src=existing[index][1];before=sha(src);target=src
  elif edited:
   src=private_file(existing_edits[index][1],input_root);before=sha(src);target=src
   if before!=existing_edits[index][0]['sha256'] or src.stat().st_size!=existing_edits[index][0]['bytes']:raise ValueError('native_source_changed_before_operation')
  else:
   src=paths[fmt];before=sha(src)
   if before!=pinned[fmt]['sha256']:raise ValueError('source_changed_before_operation')
   if edited:target=src
   else:
    profile(10 if compatible else 3)
    target=out/target_name(fmt,compatible)
    if os.path.lexists(target):raise ValueError('output_exists')
    doc=load(src)
    if doc is None:raise ValueError('plain_input_not_opened')
    try:
     if not semantic(doc,fmt):raise ValueError('plain_input_semantics')
     doc.storeAsURL(uno.systemPathToFileUrl(str(target)),tuple([prop('FilterName',filt),prop('Password',password),prop('Overwrite',False)]))
    finally:close(doc)
    private_file(target,root)
  # Custody precedes optional envelope/oracle checking. Checker failure cannot
  # erase already created bytes or authorize producing them again.
  target_before=sha(target)
  custody.append({'fixture_id':fixture_id,'name':target.name,'format':fmt,'fixture_profile':fixture_profile,'path':str(target),'sha256':target_before,'bytes':target.stat().st_size})
  atomic_result(out/'CUSTODY.json',{'mode':a.mode,'known_prefix_count':len(custody),'planned_rows':len(jobs),'fixtures':custody,'oracle_status':'PENDING_OR_INCONCLUSIVE','never_regenerate_for_checker_failure':True})
  descriptor=None;envelope_error=None
  try:descriptor=envelope(target,fmt,compatible)
  except Exception as error:envelope_error=type(error).__name__
  tests={'missing':probe(target,fmt,None,edited),'wrong':probe(target,fmt,wrong,edited),'correct':probe(target,fmt,password,edited)}
  unchanged=sha(src)==before and sha(target)==target_before
  passed=unchanged and envelope_error is None and tests['missing']['expected_password_refusal'] and tests['wrong']['expected_password_refusal'] and tests['correct']['opened'] and tests['correct']['semantic_match'] and not tests['correct']['interaction_events']
  rows.append({'fixture_id':fixture_id,'format':fmt,'fixture_profile':fixture_profile,'filter':filt,'source_path':str(src),'source_sha256':before,'path':str(target),'sha256':target_before,'bytes':target.stat().st_size,'independent_office_password_and_semantics_pass':passed,'tests':tests,'envelope':descriptor,'envelope_exception_class':envelope_error,'same_input_bytes_preserved':unchanged,'credential_ref':str(cred),'new_bytes':a.mode=='produce','recovered_old_bytes':False,'native_protected_result':'NOT_TESTED; exact current consumer qualification required'})
  result={'mode':a.mode,'input_manifest':str(manifest),'input_manifest_sha256':a.input_manifest_sha256,'rows':rows,'planned_rows':len(jobs),'whole_seven_covered':len(jobs)==7 and len(rows)==7,'all_pass':len(rows)==len(jobs) and all(r['independent_office_password_and_semantics_pass'] for r in rows),'oracle':'independent existing LibreOffice through dedicated UNO pipe','visual_fidelity':'NOT_TESTED','F06_formal_or_delivery':'NOT_RUN'}
  if edited:
   passed_ids={r['fixture_id'] for r in rows if r['independent_office_password_and_semantics_pass']}
   result.update(all_pass_scope='SELECTED_ONLY',selected_fixture_ids=retained['selected_fixture_ids'],selected_count=retained['selected_count'],full_six_covered=set('f06-'+str(i) for i in range(1,7))<=passed_ids,all_seven_pass=set('f06-'+str(i) for i in range(1,8))<=passed_ids,whole_F06_accepted=False)
  atomic_result(out/'RESULT.json',result)
  if not unchanged:raise ValueError('source_or_target_changed_after_operation')
 print(json.dumps({'fixtures':len(rows),'passed':sum(r['independent_office_password_and_semantics_pass'] for r in rows)}))
 return 0 if all(r['independent_office_password_and_semantics_pass'] for r in rows) else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:
  print(json.dumps({'status':'ERROR','exception_class':type(exc).__name__}));raise SystemExit(2)
