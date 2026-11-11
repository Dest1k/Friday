"""Pure synthetic parser checks; no actual Office/ciphertext/credential inputs."""
import ast
import base64
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
new=load('candidate_odf',ROOT/'candidate/tools/scoped_odf_password.py')
old=load('baseline_odf',ROOT/'baseline/tools/scoped_odf_password.py')
M=new.M;L=new.LOEXT;q=new.q
b64=lambda n:base64.b64encode(bytes(range(n))).decode()
checks=[]
def check(name,fn,expected=None):
 try:
  actual=fn()
 except new.ODFPasswordError as exc: actual=str(exc)
 except Exception as exc:
  checks.append({'name':name,'pass':False,'unexpected_exception_class':type(exc).__name__});return
 checks.append({'name':name,'pass':actual==expected,'actual':actual,'expected':expected})

def modern():
 entry=ET.Element(q(M,'file-entry'),{q(M,'full-path'):'encrypted-package',q(M,'media-type'):new.MIMES['odt'],q(M,'size'):'256'})
 enc=ET.SubElement(entry,q(M,'encryption-data'))
 ET.SubElement(enc,q(M,'algorithm'),{q(M,'algorithm-name'):new.AES_GCM,q(M,'initialisation-vector'):b64(12)})
 ET.SubElement(enc,q(M,'start-key-generation'),{q(M,'start-key-generation-name'):'http://www.w3.org/2001/04/xmlenc#sha256',q(M,'key-size'):'32'})
 ET.SubElement(enc,q(M,'key-derivation'),{q(M,'key-derivation-name'):new.ARGON2ID_LO,q(M,'key-size'):'32',q(M,'salt'):b64(16),q(L,'argon2-iterations'):'3',q(L,'argon2-memory'):'65536',q(L,'argon2-lanes'):'4'})
 return entry

def manifest(entry=None):
 root=ET.Element(q(M,'manifest'),{q(M,'version'):'1.4'});root.append(entry if entry is not None else modern());return root

def package(root=None,extras=(),payload=bytes(range(32)),method=zipfile.ZIP_STORED,fmt='odt'):
 root=manifest()if root is None else root
 stream=io.BytesIO()
 with zipfile.ZipFile(stream,'w')as archive:
  archive.writestr('mimetype',new.MIMES[fmt])
  archive.writestr('encrypted-package',payload,compress_type=method)
  archive.writestr('META-INF/manifest.xml',ET.tostring(root,encoding='utf-8'))
  for name,data in extras:archive.writestr(name,data)
 return stream.getvalue()

def code(mod,fn):
 try:fn();return None
 except mod.ODFPasswordError as exc:return str(exc)

def change(section,attr,value=None,delete=False,ns=M):
 entry=modern();node=entry if section=='entry'else entry[0]if section=='enc'else entry[0].find(q(M,section))
 if delete:node.attrib.pop(q(ns,attr))
 else:node.set(q(ns,attr),value)
 return entry

def diagnose(entry):return new._package(package(manifest(entry)),'odt',None)

sample=package()
check('known_modern_descriptor_is_bounded_unsupported',lambda:code(new,lambda:new._package(sample,'odt',None)),'odf_encryption_algorithm_unsupported')
check('baseline_exact_descriptor_reproduces_invalid_parameters',lambda:code(old,lambda:old._package(sample,'odt',None)),'odf_encryption_parameters_invalid')
for label,password in [('missing',None),('synthetic','PARSER-SYNTHETIC-NONSECRET')]:
 check('prepare_read_'+label,lambda password=password:code(new,lambda:new.prepare_read(sample,'odt',password)),'odf_encryption_algorithm_unsupported')
 check('encrypted_edit_'+label,lambda password=password:code(new,lambda:new.encrypted_edit(sample,'odt',password,{})),'odf_encryption_algorithm_unsupported')
# Explicitly prohibit reaching cryptographic execution or an edit operation.
new._key=lambda *a,**k:(_ for _ in()).throw(AssertionError('key execution forbidden'))
new._cipher=lambda *a,**k:(_ for _ in()).throw(AssertionError('cipher execution forbidden'))
check('unsupported_never_calls_key_or_cipher',lambda:code(new,lambda:new.prepare_read(sample,'odt','PARSER-SYNTHETIC-NONSECRET')),'odf_encryption_algorithm_unsupported')

for section,attrs in [('entry',['full-path','media-type','size']),('algorithm',['algorithm-name','initialisation-vector']),('start-key-generation',['start-key-generation-name','key-size']),('key-derivation',['key-derivation-name','key-size','salt'])]:
 for attr in attrs:
  # Removing the path is a manifest target failure; all other missing attrs are descriptor failures.
  reason='odf_manifest_duplicate'if section=='entry'and attr=='full-path'else'odf_encryption_parameters_invalid'
  check('modern_missing_'+section+'_'+attr,lambda s=section,a=attr:code(new,lambda:diagnose(change(s,a,delete=True))),reason)
for attr in ['argon2-iterations','argon2-memory','argon2-lanes']:
 check('modern_missing_'+attr,lambda a=attr:code(new,lambda:diagnose(change('key-derivation',a,delete=True,ns=L))),'odf_encryption_parameters_invalid')
for section in ['entry','enc','algorithm','key-derivation','start-key-generation']:
 check('modern_unknown_attr_'+section,lambda s=section:code(new,lambda:diagnose(change(s,'unknown','1'))),'odf_encryption_parameters_invalid')
 check('modern_unknown_namespace_attr_'+section,lambda s=section:code(new,lambda:diagnose(change(s,'salt','1',ns='urn:synthetic:other'))),'odf_encryption_parameters_invalid')
for section,attr,value,ns in [('enc','checksum','AAAA',M),('enc','checksum-type',M+'#sha256-1k',M),('key-derivation','iteration-count','100000',M),('key-derivation','key-size','16',M),('start-key-generation','key-size','20',M),('start-key-generation','start-key-generation-name','SHA1',M),('algorithm','algorithm-name',next(iter(new.AES_NAMES)),M),('key-derivation','key-derivation-name','PBKDF2',M),('algorithm','initialisation-vector','!',M),('algorithm','initialisation-vector',b64(16),M),('key-derivation','salt','!',M),('key-derivation','salt',b64(8),M),('key-derivation','argon2-memory','16',L)]:
 check('modern_invalid_'+section+'_'+attr+'_'+str(len(value)),lambda s=section,a=attr,v=value,n=ns:code(new,lambda:diagnose(change(s,a,v,ns=n))),'odf_encryption_parameters_invalid')
for attr,value in [('argon2-iterations','4'),('argon2-memory','65537'),('argon2-lanes','5'),('argon2-iterations','0'),('argon2-memory','0'),('argon2-lanes','0')]:
 check('modern_resource_'+attr+'_'+value,lambda a=attr,v=value:code(new,lambda:diagnose(change('key-derivation',a,v,ns=L))),'odf_encryption_resource_limit')
for value in ['-1','1.0','NaN','999999999','1e6',' ']:
 check('modern_invalid_number_'+value,lambda v=value:code(new,lambda:diagnose(change('key-derivation','argon2-memory',v,ns=L))),'odf_encryption_parameters_invalid')
check('modern_declared_size_limit',lambda:code(new,lambda:diagnose(change('entry','size',str(new.MAX_MEMBER+1)))),'odf_encryption_resource_limit')
for kind in ['algorithm','key-derivation','start-key-generation']:
 e=modern();e[0].append(copy.deepcopy(e[0].find(q(M,kind))))
 check('modern_duplicate_'+kind,lambda e=e:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')
for kind in ['algorithm','key-derivation','start-key-generation']:
 e=modern();e[0].remove(e[0].find(q(M,kind)))
 check('modern_missing_node_'+kind,lambda e=e:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')
e=modern();ET.SubElement(e[0],q(M,'unknown'))
check('modern_unknown_node',lambda:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')
e=modern();ET.SubElement(e[0][0],q(M,'nested'))
check('modern_nested_node',lambda:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')
for where in ['entry','enc','algorithm','kd','start']:
 e=modern();node={'entry':e,'enc':e[0],'algorithm':e[0][0],'start':e[0][1],'kd':e[0][2]}[where];node.text='SYNTHETIC-TEXT'
 check('modern_text_'+where,lambda e=e:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')

r=manifest();r.append(copy.deepcopy(r[0]))
check('later_manifest_duplicate_is_not_unsupported',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_manifest_duplicate')
r=manifest();ET.SubElement(r,q(M,'file-entry'),{q(M,'full-path'):'missing.bin'})
check('later_missing_target_is_not_unsupported',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_manifest_target_invalid')
r=manifest();ET.SubElement(r,q(M,'file-entry'),{q(M,'full-path'):'content.xml'})
check('mixed_plain_outer_is_not_unsupported',lambda:code(new,lambda:new._package(package(r,extras=[('content.xml',b'<x/>')]),'odt',None)),'odf_encryption_parameters_invalid')
r=manifest();ET.SubElement(r,q(M,'file-entry'),{q(M,'full-path'):'/',q(M,'media-type'):new.MIMES['odt']})
check('unexpected_root_is_not_unsupported',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_encryption_parameters_invalid')
r=manifest();r.set(q(M,'unknown'),'1')
check('modern_root_unknown_attr',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_encryption_parameters_invalid')
r=manifest();r.set(q(M,'version'),'bogus')
check('modern_root_invalid_version',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_encryption_parameters_invalid')
r=manifest();r.attrib.clear()
check('modern_root_missing_version',lambda:code(new,lambda:new._package(package(r),'odt',None)),'odf_encryption_parameters_invalid')
check('modern_mimetype_format_mismatch',lambda:code(new,lambda:new._package(sample,'ods',None)),'odf_mimetype_mismatch')
check('modern_manifest_media_type_mismatch',lambda:code(new,lambda:diagnose(change('entry','media-type',new.MIMES['ods']))),'odf_encryption_parameters_invalid')
check('modern_short_payload',lambda:code(new,lambda:new._package(package(payload=b'1'),'odt',None)),'odf_ciphertext_invalid')
check('modern_encrypted_member_not_stored',lambda:code(new,lambda:new._package(package(method=zipfile.ZIP_DEFLATED),'odt',None)),'odf_encrypted_member_not_stored')
check('modern_unmanifested_extra_member',lambda:code(new,lambda:new._package(package(extras=[('extra.bin',b'x')]),'odt',None)),'odf_encryption_parameters_invalid')
check('modern_unmanifested_directory',lambda:code(new,lambda:new._package(package(extras=[('extra/',b'')]),'odt',None)),'odf_encryption_parameters_invalid')
check('modern_active_outer_member',lambda:code(new,lambda:new._package(package(extras=[('Basic/x.xml',b'x')]),'odt',None)),'odf_active_or_signed_package_unsupported')
check('modern_path_escape',lambda:code(new,lambda:new._package(package(extras=[('../x',b'x')]),'odt',None)),'odf_member_path_invalid')
check('package_input_limit',lambda:code(new,lambda:new._package(b'x'*(new.MAX_BYTES+1),'odt',None)),'odf_input_limit')
bad_crc=bytearray(sample)
with zipfile.ZipFile(io.BytesIO(sample))as a:
 info=a.getinfo('encrypted-package');offset=info.header_offset
 offset+=30+int.from_bytes(sample[offset+26:offset+28],'little')+int.from_bytes(sample[offset+28:offset+30],'little')
bad_crc[offset]^=1
check('modern_corrupt_zip_payload_crc',lambda:code(new,lambda:new._package(bytes(bad_crc),'odt',None)),'odf_malformed_package')
s=io.BytesIO()
with zipfile.ZipFile(s,'w')as a:
 a.writestr('mimetype',new.MIMES['odt']);a.writestr('encrypted-package',bytes(range(32)))
 a.writestr('META-INF/manifest.xml',b'<!DOCTYPE x [<!ENTITY secret "synthetic">]><manifest/>')
check('modern_manifest_DTD',lambda:code(new,lambda:new._package(s.getvalue(),'odt',None)),'odf_manifest_invalid')
e=modern();e[0].append(ET.Element(q(M,'algorithm')))
check('modern_duplicated_missing_name_node',lambda:code(new,lambda:diagnose(e)),'odf_encryption_parameters_invalid')
# Compare all supported descriptors and a complete package to their exact baseline plans.
def legacy(name,key_size,start_name,start_size,checksum,kdf='PBKDF2',rounds='100000'):
 e=ET.Element(q(M,'file-entry'),{q(M,'full-path'):'content.xml',q(M,'media-type'):'text/xml',q(M,'size'):'32'})
 enc=ET.SubElement(e,q(M,'encryption-data'),{q(M,'checksum-type'):checksum,q(M,'checksum'):b64(hashlib.new(new.CHECKSUM_NAMES[checksum]).digest_size)})
 ET.SubElement(enc,q(M,'algorithm'),{q(M,'algorithm-name'):name,q(M,'initialisation-vector'):b64(16 if name in new.AES_NAMES else 8)})
 ET.SubElement(enc,q(M,'key-derivation'),{q(M,'key-derivation-name'):kdf,q(M,'key-size'):str(key_size),q(M,'iteration-count'):rounds,q(M,'salt'):b64(16)})
 if start_name is not None:ET.SubElement(enc,q(M,'start-key-generation'),{q(M,'start-key-generation-name'):start_name,q(M,'key-size'):str(start_size)})
 return e

def normalized(plan):return {k:v for k,v in plan.items()if k not in ('entry','enc','algorithm','kd')}
for i,(name,size)in enumerate(list(new.AES_NAMES.items())+[(x,16)for x in sorted(new.BLOWFISH)]):
 for start,startsize,cs in [(None,None,'SHA1/1K'),('http://www.w3.org/2001/04/xmlenc#sha256',32,M+'#sha256-1k')]:
  for kdf in ['PBKDF2',M+'#pbkdf2']:
   e=legacy(name,size,start,startsize,cs,kdf)
   check('supported_plan_equivalence_'+str(i)+'_'+str(startsize)+'_'+kdf,lambda e=e:normalized(new._plan(copy.deepcopy(e)))==normalized(old._plan(copy.deepcopy(e))),True)
e=legacy('http://www.w3.org/2001/04/xmlenc#aes256-cbc',32,'http://www.w3.org/2001/04/xmlenc#sha256',32,M+'#sha256-1k')
r=ET.Element(q(M,'manifest'));ET.SubElement(r,q(M,'file-entry'),{q(M,'full-path'):'/',q(M,'media-type'):new.MIMES['odt']});r.append(e)
s=io.BytesIO()
with zipfile.ZipFile(s,'w')as a:
 a.writestr('mimetype',new.MIMES['odt']);a.writestr('content.xml',bytes(range(32)));a.writestr('META-INF/manifest.xml',ET.tostring(r))
check('supported_CBC100000_package_equivalence',lambda:normalized(new._package(s.getvalue(),'odt',None)[3]['content.xml'])==normalized(old._package(s.getvalue(),'odt',None)[3]['content.xml']),True)
for attr,val,reason in [('iteration-count','100001','odf_encryption_resource_limit'),('salt','!','odf_encryption_parameters_invalid'),('key-size','16','odf_encryption_parameters_invalid')]:
 e=legacy('http://www.w3.org/2001/04/xmlenc#aes256-cbc',32,None,None,'SHA1/1K');e[0].find(q(M,'key-derivation')).set(q(M,attr),val)
 check('legacy_negative_preserved_'+attr,lambda e=e:code(new,lambda:new._plan(e))==code(old,lambda:old._plan(e))==reason,True)
e=legacy('http://www.w3.org/2001/04/xmlenc#aes256-cbc',32,None,None,'SHA1/1K');e[0].attrib.clear();ET.SubElement(e[0],q(M,'unknown'))
check('legacy_preexisting_validation_order_preserved',lambda:code(new,lambda:new._plan(e))==code(old,lambda:old._plan(e))=='odf_encryption_parameters_invalid',True)

# Evaluate the exact existing classifier in isolation, without loading harness/runtime.
harness=pathlib.Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112/candidate/harness.py')
tree=ast.parse(harness.read_text());names={'MODERN_ODF_UNSUPPORTED','returned_refusal','modern_unsupported'}
selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.Assign))and(getattr(n,'name',None)in names or any(isinstance(t,ast.Name)and t.id in names for t in getattr(n,'targets',[])))]
ns={};exec(compile(ast.Module(body=selected,type_ignores=[]),str(harness),'exec'),ns)
receipt={'success':False,'error':'document_extraction_failed','format':'odt','reason':'odf_encryption_algorithm_unsupported'}
check('unchanged_classifier_recognizes_unsupported_negative',lambda:ns['modern_unsupported'](receipt,'odt','current_latest'),True)
check('unsupported_receipt_is_never_successful_format_read',lambda:receipt.get('success')is True,False)
invalid=dict(receipt,reason='odf_encryption_parameters_invalid')
check('unchanged_classifier_rejects_invalid_parameters',lambda:ns['modern_unsupported'](invalid,'odt','current_latest'),False)
passed=all(x['pass']for x in checks)
out={'scope':'pure synthetic XML/package parser; no actual retained7/ciphertext/body/Office/native/live/model calls','count':len(checks),'all_pass':passed,'checks':checks}
p=ROOT/'CHECKS.json';p.write_text(json.dumps(out,indent=2)+'\n');p.chmod(0o600)
print(json.dumps({'count':len(checks),'all_pass':passed,'failed':[x for x in checks if not x['pass']]}))
sys.exit(0 if passed else 1)
