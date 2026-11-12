"""Only explicit own synthetic crypto; no Office/runtime/network/user inputs."""
import os,resource,time
START=time.monotonic();CPU=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
import ast,base64,copy,hashlib,importlib.util,io,json,pathlib,sys,types,zipfile,zlib,traceback
from xml.etree import ElementTree as E
ROOT=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'candidate'))
from tools import scoped_odf_password as C
from tools.scoped_odt_create import create_odt
from tools.scoped_odt import extract_document
from tools.scoped_odf_profiles import render_edit
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Cryptodome.Cipher import AES
AES.new(bytes(32),AES.MODE_GCM,nonce=bytes(12))
spec=importlib.util.spec_from_file_location('baseline_codec',ROOT/'baseline/scoped_odf_password.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
M=C.M;L=C.LOEXT;q=C.q;checks=[];active=False;denials=[]
P='SYNTHETIC-ONLY-KEY-🔑';BAD='SYNTHETIC-ONLY-WRONG';clear=create_odt('Alpha original\nTail 783')
def check(name,fn,expected=True):
 try:
  actual=fn();ok=actual==expected
  checks.append({'name':name,'pass':ok,'actual':actual if isinstance(actual,(str,int,float,bool,type(None)))else type(actual).__name__,'expected':expected})
 except Exception as e:checks.append({'name':name,'pass':False,'unexpected_exception_class':type(e).__name__})
def refusal(fn):
 try:fn();return 'NO_REFUSAL'
 except C.ODFPasswordError as e:return str(e)
def raws(data):
 with zipfile.ZipFile(io.BytesIO(data))as z:return {i.filename:z.read(i)for i in z.infolist()}
def build(parts):
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w')as z:
  for n,v in parts.items():z.writestr(n,v,compress_type=zipfile.ZIP_STORED if n in ('mimetype','encrypted-package')else zipfile.ZIP_DEFLATED)
 return buf.getvalue()
def producer(inner=clear,*,password=P,memory=65536,iterations=3,lanes=4,compressed=None):
 # Independent producer uses direct standard KDF API and a different AES library.
 salt=bytes(range(16));iv=bytes(range(12));key=Argon2id(salt=salt,length=32,iterations=iterations,memory_cost=memory,lanes=lanes).derive(hashlib.sha256(password.encode()).digest())
 if compressed is None:
  co=zlib.compressobj(6,zlib.DEFLATED,-15);compressed=co.compress(inner)+co.flush()
 aes=AES.new(key,AES.MODE_GCM,nonce=iv,mac_len=16);body,tag=aes.encrypt_and_digest(compressed)
 root=E.Element(q(M,'manifest'),{q(M,'version'):'1.4'})
 en=E.SubElement(root,q(M,'file-entry'),{q(M,'full-path'):'encrypted-package',q(M,'media-type'):C.MIMES['odt'],q(M,'size'):str(len(inner))})
 enc=E.SubElement(en,q(M,'encryption-data'))
 E.SubElement(enc,q(M,'algorithm'),{q(M,'algorithm-name'):C.AES_GCM,q(M,'initialisation-vector'):base64.b64encode(iv).decode()})
 E.SubElement(enc,q(M,'start-key-generation'),{q(M,'start-key-generation-name'):'http://www.w3.org/2001/04/xmlenc#sha256',q(M,'key-size'):'32'})
 E.SubElement(enc,q(M,'key-derivation'),{q(M,'key-derivation-name'):C.ARGON2ID_LO,q(M,'key-size'):'32',q(M,'salt'):base64.b64encode(salt).decode(),q(L,'argon2-iterations'):str(iterations),q(L,'argon2-memory'):str(memory),q(L,'argon2-lanes'):str(lanes)})
 return build({'mimetype':C.MIMES['odt'].encode(),'encrypted-package':iv+body+tag,'META-INF/manifest.xml':E.tostring(root)})
def mutate(data,fn):
 parts=raws(data);root=E.fromstring(parts['META-INF/manifest.xml']);fn(root,parts);parts['META-INF/manifest.xml']=E.tostring(root);return build(parts)
fixture=producer()
# Imported helpers are exact code; all remaining codec calls are memory only.
def audit(event,args):
 if not active:return
 if event=='open':
  mode=args[1];flags=args[2]
  if isinstance(mode,str)and any(c in mode for c in 'wax+')or isinstance(flags,int)and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
   denials.append('write');raise AssertionError('filesystem write prohibited')
 if event.startswith(('socket.','subprocess.','os.exec','os.system','os.spawn')):
  denials.append(event);raise AssertionError('external effect prohibited')
sys.addaudithook(audit);active=True
check('rfc9106_argon2id_v19_external_vector',lambda:Argon2id(salt=b'\x02'*16,length=32,iterations=3,memory_cost=32,lanes=4,secret=b'\x03'*8,ad=b'\x04'*12).derive(b'\x01'*32).hex(),'0d640df58d78766c08c037a34a8b53c9d01ef0452d75b65eb52520e96b01e659')
check('independent_argon2_pycryptodome_producer_exact_clear',lambda:C.prepare_read(fixture,'odt',P)[0]==clear)
try:B.prepare_read(fixture,'odt',P);oldreason='NO_REFUSAL'
except B.ODFPasswordError as e:oldreason=str(e)
check('source206_boundedunsupported_same_own_fixture',lambda:oldreason,'odf_encryption_algorithm_unsupported')
check('authenticated_metadata_only',lambda:C.prepare_read(fixture,'odt',P)[1]=={'encrypted':True,'decrypted_for_read_only':True,'encrypted_members':1,'algorithms':[C.AES_GCM],'modern_profile':'LO_ARGON2ID19_AES256GCM','password_verification':'AEAD_TAG_MATCHED','data_integrity_verified':True,'encryption_authenticity':'AEAD_PAYLOAD_AUTHENTICATED_NOT_ORIGIN_IDENTITY'})
for n,pw,expected in [('missing',None,'odf_password_required'),('empty','','odf_password_invalid'),('wrong',BAD,'odf_password_rejected_or_corrupt'),('long','x'*1025,'odf_password_invalid'),('surrogate','\ud800','odf_password_invalid')]:
 check('password_'+n,lambda pw=pw:refusal(lambda:C.prepare_read(fixture,'odt',pw)),expected)
for label,offset in [('nonce',0),('ciphertext',13),('tag',-1)]:
 parts=raws(fixture);b=bytearray(parts['encrypted-package']);b[offset]^=1;parts['encrypted-package']=bytes(b);bad=build(parts)
 check('tamper_'+label,lambda bad=bad:refusal(lambda:C.prepare_read(bad,'odt',P)),'odf_ciphertext_invalid'if label=='nonce'else'odf_password_rejected_or_corrupt')
# Reject malformed/unbounded descriptors BEFORE the KDF, even with no password.
real_crypto=C._modern_crypto
C._modern_crypto=lambda *a:(_ for _ in()).throw(AssertionError('KDF reached'))
for attr,value,expected,ns in [('argon2-memory','65537','odf_encryption_resource_limit',L),('argon2-iterations','4','odf_encryption_resource_limit',L),('argon2-lanes','5','odf_encryption_resource_limit',L),('argon2-lanes','0','odf_encryption_resource_limit',L),('argon2-memory','8','odf_encryption_parameters_invalid',L),('argon2-memory','1e6','odf_encryption_parameters_invalid',L),('salt','!!!','odf_encryption_parameters_invalid',M),('key-size','16','odf_encryption_parameters_invalid',M)]:
 bad=mutate(fixture,lambda root,parts,attr=attr,value=value,ns=ns:root[0][0].find(q(M,'key-derivation')).set(q(ns,attr),value))
 check('before_kdf_'+attr+'_'+value,lambda bad=bad:refusal(lambda:C.prepare_read(bad,'odt',None)),expected)
for label,fn,expected in [
 ('inner_size',lambda r,p:r[0].set(q(M,'size'),str(C.MAX_BYTES+1)),'odf_encryption_resource_limit'),
 ('extra_outer',lambda r,p:p.update({'outside.xml':b'<x/>'}),'odf_encryption_parameters_invalid'),
 ('duplicate_manifest',lambda r,p:r.append(copy.deepcopy(r[0])),'odf_manifest_duplicate'),
 ('duplicate_algorithm',lambda r,p:r[0][0].append(copy.deepcopy(r[0][0][0])),'odf_encryption_parameters_invalid'),
 ('short_payload',lambda r,p:p.update({'encrypted-package':p['encrypted-package'][:28]}),'odf_ciphertext_invalid'),
 ('media_type',lambda r,p:r[0].set(q(M,'media-type'),C.MIMES['ods']),'odf_encryption_parameters_invalid'),
 ('unknown_argon_attr',lambda r,p:r[0][0][-1].set(q(L,'argon2-version'),'19'),'odf_encryption_parameters_invalid'),
]:
 bad=mutate(fixture,fn);check('before_kdf_'+label,lambda bad=bad:refusal(lambda:C.prepare_read(bad,'odt',P)),expected)
C._modern_crypto=real_crypto
# Authentication must precede decompression/inner parsing.
real_inflate=C._inflate;C._inflate=lambda *a:(_ for _ in()).throw(AssertionError('unauthenticated inflate'))
parts=raws(fixture);b=bytearray(parts['encrypted-package']);b[-1]^=1;parts['encrypted-package']=bytes(b)
check('tag_failure_no_plaintext_inflate',lambda:refusal(lambda:C.prepare_read(build(parts),'odt',P)),'odf_password_rejected_or_corrupt');C._inflate=real_inflate
# Authenticated but invalid inner data is still rejected by the unchanged guards.
for label,inner,expected in [
 ('wrong_inner_mime',build(dict(raws(clear),mimetype=C.MIMES['ods'].encode())),'odf_mimetype_mismatch'),
 ('zip_bomb',build(dict(raws(clear),**{'content.xml':b'a'*250000})),'odf_package_expansion_limit'),
 ('zip_path',build(dict(raws(clear),**{'../escape':b'x'})),'odf_member_path_invalid'),
 ('active_path',build(dict(raws(clear),**{'Basic/x.xml':b'<x/>'})),'odf_active_or_signed_package_unsupported'),
 ('active_xml',build(dict(raws(clear),**{'content.xml':b'<office:script xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"/>'})),'odf_active_or_signed_package_unsupported'),
 ('dtd_xml',build(dict(raws(clear),**{'content.xml':b'<!DOCTYPE x [<!ENTITY evil "boom">]><x>&evil;</x>'})),'odf_member_xml_invalid'),
 ('nested_encryption',fixture,'odf_nested_encryption_unsupported')]:
 bad=producer(inner,memory=32,iterations=1,lanes=1)
 check('authenticated_inner_'+label,lambda bad=bad:refusal(lambda:C.prepare_read(bad,'odt',P)),expected)
bad=producer(clear,memory=32,iterations=1,lanes=1,compressed=b'not a deflate stream')
check('authenticated_bad_deflate',lambda:refusal(lambda:C.prepare_read(bad,'odt',P)),'odf_password_rejected_or_corrupt')
class Cancelled(Exception):pass
def cancel():raise Cancelled()
def cancelled(fn):
 try:fn();return False
 except Cancelled:return True
check('cancel_before_kdf_propagates',lambda:cancelled(lambda:C.prepare_read(fixture,'odt',P,checkpoint=cancel)))
parts,infos,root,plans=C._package(fixture,'odt',None);n=[0]
def after_tag():
 n[0]+=1
 if n[0]==3:raise Cancelled()
check('cancel_after_tag_before_inflate_propagates',lambda:cancelled(lambda:C._modern_read(parts,plans['encrypted-package'],'odt',P,after_tag)))
# Invalid UTF8 password errors retain neither input in context nor exception text.
def malformed_password_private():
 try:C.password_bytes(P+'\ud800');return False
 except C.ODFPasswordError as e:return str(e)=='odf_password_invalid' and e.__context__ is None and P not in ''.join(traceback.format_exception(e))
check('malformed_password_error_no_input_context',malformed_password_private)
for pw,expected in [(None,'odf_password_required'),('', 'odf_password_invalid'),(False,'odf_password_invalid'),('x\x00y','odf_password_invalid'),('x'*1025,'odf_password_invalid'),('x'*1024,'ACCEPTED')]:
 check('password_boundary_'+str(type(pw).__name__)+'_'+str(len(pw)if isinstance(pw,str)else pw),lambda pw=pw:refusal(lambda:C.password_bytes(pw)).replace('NO_REFUSAL','ACCEPTED'),expected)

# Synthetic backend fault messages cannot survive in mapped exception context.
import cryptography.hazmat.primitives.kdf.argon2 as argon_module
from cryptography.exceptions import UnsupportedAlgorithm
real_argon=argon_module.Argon2id
for cls,expected in [(UnsupportedAlgorithm,'odf_crypto_unavailable'),(MemoryError,'odf_encryption_resource_limit'),(ValueError,'odf_encryption_parameters_invalid')]:
 def broken(*args,cls=cls,**kwargs):raise cls(P)
 argon_module.Argon2id=broken
 def private_error(expected=expected):
  try:C.prepare_read(fixture,'odt',P);return False
  except C.ODFPasswordError as e:return str(e)==expected and e.__context__ is None and P not in ''.join(traceback.format_exception(e))
 check('backend_error_message_context_discarded_'+cls.__name__,private_error)
argon_module.Argon2id=real_argon
# Authenticated outer DEFLATE expansion stops at the declared bounded size.
co=zlib.compressobj(6,zlib.DEFLATED,-15);bomb=co.compress(b'x'*(C.MAX_BYTES+1))+co.flush()
bad=producer(clear,memory=32,iterations=1,lanes=1,compressed=bomb)
check('authenticated_outer_deflate_bomb_capped',lambda:refusal(lambda:C.prepare_read(bad,'odt',P)),'odf_decrypted_size_mismatch')

# Actual pure editor, new encrypted envelope, independent AES readback.
original_hash=hashlib.sha256(fixture).hexdigest();out,meta=C.encrypted_edit(fixture,'odt',P,{'old_text':'Alpha original','new_text':'Beta changed'})
check('edit_preserves_original',lambda:hashlib.sha256(fixture).hexdigest()==original_hash)
check('edit_authentication_metadata',lambda:meta['data_integrity_verified']and meta['password_preserved']and meta['encryption_authenticity']=='AEAD_PAYLOAD_AUTHENTICATED_NOT_ORIGIN_IDENTITY')
op=raws(out);mp=E.fromstring(op['META-INF/manifest.xml']);kd=mp[0][0].find(q(M,'key-derivation'));alg=mp[0][0].find(q(M,'algorithm'))
salt=base64.b64decode(kd.get(q(M,'salt')));iv=base64.b64decode(alg.get(q(M,'initialisation-vector')))
check('edit_only_original_outer_inventory',lambda:set(op)=={'mimetype','encrypted-package','META-INF/manifest.xml'})
check('edit_fresh_salt_and_nonce',lambda:salt!=bytes(range(16))and iv!=bytes(range(12)))
key=Argon2id(salt=salt,length=32,iterations=3,memory_cost=65536,lanes=4).derive(hashlib.sha256(P.encode()).digest());aes=AES.new(key,AES.MODE_GCM,nonce=iv,mac_len=16);payload=op['encrypted-package'];inner=zlib.decompress(aes.decrypt_and_verify(payload[12:-16],payload[-16:]),-15)
check('independent_edit_readback_semantic_delta',lambda:'Beta changed'in extract_document(inner)and 'Alpha original'not in extract_document(inner))
check('edit_unchanged_other_inner_parts',lambda:all(raws(inner)[k]==v for k,v in raws(clear).items()if k!='content.xml'))
check('edit_exact_existing_editor_bytes',lambda:inner==render_edit(clear,'Alpha original','Beta changed','odt',None))
check('edited_ciphertext_rejects_wrong_password',lambda:refusal(lambda:C.prepare_read(out,'odt',BAD)),'odf_password_rejected_or_corrupt')
check('wrong_edit_refused',lambda:refusal(lambda:C.encrypted_edit(fixture,'odt',BAD,{'old_text':'Alpha original','new_text':'Beta changed'})),'odf_password_rejected_or_corrupt')
check('invalid_edit_schema_refused',lambda:refusal(lambda:C.encrypted_edit(fixture,'odt',P,{'replace':'x'})),'odf_edit_schema')
# Independent CBC fixture confirms the legacy path/metadata byte identity.
def legacy_cbc(inner):
 parts=raws(inner);root=E.fromstring(parts['META-INF/manifest.xml'])
 for en in root:
  name=en.get(q(M,'full-path'))
  if name not in parts or name in ('mimetype','META-INF/manifest.xml'):continue
  plain=parts[name];salt=bytes(range(16));iv=bytes(range(16));co=zlib.compressobj(6,zlib.DEFLATED,-15);compressed=co.compress(plain)+co.flush()
  digest=hashlib.sha256(compressed[:1024]).digest();pad=16-len(compressed)%16;compressed+=bytes(pad-1)+bytes([pad])
  key=hashlib.pbkdf2_hmac('sha1',hashlib.sha256(P.encode()).digest(),salt,1000,32)
  parts[name]=AES.new(key,AES.MODE_CBC,iv=iv).encrypt(compressed);en.set(q(M,'size'),str(len(plain)))
  enc=E.SubElement(en,q(M,'encryption-data'),{q(M,'checksum-type'):M+'#sha256-1k',q(M,'checksum'):base64.b64encode(digest).decode()})
  E.SubElement(enc,q(M,'algorithm'),{q(M,'algorithm-name'):'http://www.w3.org/2001/04/xmlenc#aes256-cbc',q(M,'initialisation-vector'):base64.b64encode(iv).decode()})
  E.SubElement(enc,q(M,'key-derivation'),{q(M,'key-derivation-name'):'PBKDF2',q(M,'key-size'):'32',q(M,'iteration-count'):'1000',q(M,'salt'):base64.b64encode(salt).decode()})
  E.SubElement(enc,q(M,'start-key-generation'),{q(M,'start-key-generation-name'):'http://www.w3.org/2001/04/xmlenc#sha256',q(M,'key-size'):'32'})
 parts['META-INF/manifest.xml']=E.tostring(root)
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w')as z:
  for n,v in parts.items():z.writestr(n,v,compress_type=zipfile.ZIP_STORED)
 return buf.getvalue()
legacy=legacy_cbc(clear)
check('legacy_cbc_exact_read_bytes_and_metadata_unchanged',lambda:C.prepare_read(legacy,'odt',P)==B.prepare_read(legacy,'odt',P))
check('legacy_cbc_wrong_password_unchanged',lambda:refusal(lambda:C.prepare_read(legacy,'odt',BAD)),'odf_password_rejected_or_corrupt')
legacy_out,legacy_meta=C.encrypted_edit(legacy,'odt',P,{'old_text':'Alpha original','new_text':'Beta changed'})
check('legacy_edit_readback_semantics',lambda:'Beta changed'in extract_document(C.prepare_read(legacy_out,'odt',P)[0]))
check('legacy_edit_authenticity_not_promoted',lambda:legacy_meta['encryption_authenticity']=='NOT_VERIFIED'and 'data_integrity_verified'not in legacy_meta and 'modern_profile'not in legacy_meta)
check('clear_package_behavior_byteidentity',lambda:C.prepare_read(clear,'odt')==B.prepare_read(clear,'odt'))
# Other modern families remain the accepted taxonomy-only capability.
for fmt in ('ott','ods','ots','odp','otp'):
 b=raws(fixture);b['mimetype']=C.MIMES[fmt].encode();r=E.fromstring(b['META-INF/manifest.xml']);r[0].set(q(M,'media-type'),C.MIMES[fmt]);b['META-INF/manifest.xml']=E.tostring(r);other=build(b)
 check('other_modern_family_still_unsupported_'+fmt,lambda other=other,fmt=fmt:refusal(lambda:C.prepare_read(other,fmt,P)),'odf_encryption_algorithm_unsupported')
 for label,change in [('larger_diagnostic_size',lambda r,p:r[0].set(q(M,'size'),str(C.MAX_BYTES+1))),('short_diagnostic_payload',lambda r,p:p.update({'encrypted-package':b'0'*16}))]:
  diagnostic=mutate(other,change)
  check('other_modern_taxonomy_'+fmt+'_'+label,lambda diagnostic=diagnostic,fmt=fmt:refusal(lambda:C.prepare_read(diagnostic,fmt,P)),'odf_encryption_algorithm_unsupported')


# Unchanged create-only permission/custody consumer under explicit synthetic seams.
class Denied(Exception):pass
state={'deny_parent':False,'identity':1,'publishes':0,'reads':0}
def parent(*args):
 if state['deny_parent']:raise Denied()
def document(*args,**kwargs):state['reads']+=1;return fixture,{},state['identity']
def create(*args,**kwargs):
 kwargs['verify_source']();state['publishes']+=1;return json.dumps({'success':True})
mods={'hermes_cli.friday_user_scope':{'ScopeDenied':Denied,'workspace_document':document},'hermes_cli.friday_workspace_docx':{'_check_parent':parent,'_create_bytes':create},'hermes_cli.friday_workspace_revision':{'check':lambda cap:None}}
for name,attrs in mods.items():
 mod=types.ModuleType(name);mod.__dict__.update(attrs);sys.modules[name]=mod
spec=importlib.util.spec_from_file_location('synthetic_consumer',ROOT/'candidate/hermes_cli/friday_workspace_odf_password.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
cap=types.SimpleNamespace(home=ROOT/'synthetic-home');request=json.dumps({'source':'own.odt','source_sha256':original_hash,'password':P,'edit':{'old_text':'Alpha original','new_text':'Beta changed'}})
def denied(fn):
 try:fn();return False
 except Denied:return True
state['deny_parent']=True
check('consumer_permission_denied_before_source_or_crypto',lambda:denied(lambda:W.create_edit(cap,1,'out.odt','out.odt',request))and state['reads']==0 and state['publishes']==0)
state['deny_parent']=False
check('consumer_source_hash_mismatch_no_publish',lambda:json.loads(W.create_edit(cap,1,'out.odt','out.odt',request.replace(original_hash,'0'*64)))['reason']=='source_hash_mismatch'and state['publishes']==0)
def changed_create(*args,**kwargs):state['identity']=2;kwargs['verify_source']();raise AssertionError('CAS failed')
W._create_bytes=changed_create
check('consumer_cas_identity_change_prevents_publish',lambda:denied(lambda:W.create_edit(cap,1,'out.odt','out.odt',request))and state['publishes']==0)
# Legacy crypto implementation and privacy modules remain byte/AST identical.
legacy_functions=('_cipher','_key','_inflate','_zip','_inert_xml','number','binary','_attrs')
oldtree=ast.parse((ROOT/'baseline/scoped_odf_password.py').read_text());newtree=ast.parse((ROOT/'candidate/tools/scoped_odf_password.py').read_text())
def node(tree,name):return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name),include_attributes=False)
check('legacy_crypto_guard_functions_ast_unchanged',lambda:all(node(oldtree,n)==node(newtree,n)for n in legacy_functions))
check('no_codec_writes_or_external_effects',lambda:denials==[])
check('public_metadata_has_no_password_key_salt_nonce_or_body',lambda:all(x not in json.dumps(meta)for x in (P,BAD,'Alpha original','Beta changed',salt.hex(),iv.hex(),key.hex())))
active=False
report={'scope':'PURE_SOURCE_OWN_SYNTHETIC_ONLY_NOT_PRODUCT_OR_INSTALL','count':len(checks),'passed':sum(x['pass']for x in checks),'failed':[x for x in checks if not x['pass']],'checks':checks,'limits':{'wall_seconds':90,'cpu_seconds':60,'address_space_bytes':512*1024*1024,'affinity':sorted(os.sched_getaffinity(0))},'actual':{'wall_seconds':time.monotonic()-START,'cpu_seconds':time.process_time()-CPU,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},'no_genuine_ciphertext':True,'no_office_model_network_send_install':True,'fixtures_retained':False}
(ROOT/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/'CHECKS.json').chmod(0o600)
print(json.dumps({k:report[k]for k in ('count','passed','failed','actual')}))
sys.exit(0 if report['count']==report['passed']else 1)
