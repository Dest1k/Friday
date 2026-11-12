"""Bounded ODF password read and preserving encrypted edits, entirely in memory.

ODF 1.3 package encryption (part 2, 3.4 and 4.16): raw DEFLATE then
AES-CBC or legacy Blowfish-CFB8, PBKDF2-HMAC-SHA1, per-member checksum.
The checksum confirms a password; it is not a signature/authenticity claim.
The bounded LO wholesome profile additionally supports SHA256-start Argon2id
v19 and AES256-GCM, authenticating the complete compressed inner package.
No passwords, keys or unencrypted package bytes are written by this codec.
"""
import base64
import binascii
import copy
import hashlib
import hmac
import io
import re
import secrets
import stat
import zipfile
import zlib
from xml.etree import ElementTree as ET

from tools.scoped_presentation import xml_root, PresentationError, q
from tools.scoped_zip import read_zip_member, ZipMemberLimitError

M = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
MIMES = {n: 'application/vnd.oasis.opendocument.' + t for n,t in {
    'odt':'text', 'ott':'text-template', 'ods':'spreadsheet',
    'ots':'spreadsheet-template', 'odp':'presentation',
    'otp':'presentation-template'}.items()}
MAX_BYTES = 1_000_000
MAX_MEMBER = 2_000_000
MAX_TOTAL = 8_000_000
MAX_ROUNDS = 100_000
MAX_WORK = 2_000_000
AES_NAMES = {'http://www.w3.org/2001/04/xmlenc#aes128-cbc':16,
             'http://www.w3.org/2001/04/xmlenc#aes192-cbc':24,
             'http://www.w3.org/2001/04/xmlenc#aes256-cbc':32}
BLOWFISH = {'Blowfish CFB', M+'#blowfish'}
HASH_NAMES = {'SHA1':'sha1', 'http://www.w3.org/2000/09/xmldsig#sha1':'sha1',
              'http://www.w3.org/2000/09/xmldsig#sha256':'sha256',
              'http://www.w3.org/2001/04/xmlenc#sha256':'sha256'}
CHECKSUM_NAMES = {'SHA1/1K':'sha1', M+'#sha1-1k':'sha1', M+'#sha256-1k':'sha256'}
AES_GCM = 'http://www.w3.org/2009/xmlenc11#aes256-gcm'
ARGON2ID_LO = 'urn:org:documentfoundation:names:experimental:office:manifest:argon2id'
LOEXT = 'urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0'


class ODFPasswordError(ValueError):
    """Only fixed content-free codes leave this module."""


def fail(code):
    raise ODFPasswordError(code)


def tick(checkpoint):
    if checkpoint is not None:
        checkpoint()


def password_bytes(password):
    if password is None:
        fail('odf_password_required')
    if type(password) is not str or not password or '\x00' in password:
        fail('odf_password_invalid')
    try:
        value = password.encode('utf-8')
    except UnicodeError:
        value = None
    if value is None:
        fail('odf_password_invalid')
    if len(value) > 1024:
        fail('odf_password_invalid')
    return value


def number(value, maximum, minimum=0):
    if type(value) is not str or not re.fullmatch('[0-9]{1,8}', value):
        fail('odf_encryption_parameters_invalid')
    result = int(value)
    if not minimum <= result <= maximum:
        fail('odf_encryption_resource_limit')
    return result


def binary(value, minimum, maximum):
    if type(value) is not str or len(value)>4*maximum+8:
        fail('odf_encryption_parameters_invalid')
    try:
        data=base64.b64decode(value,validate=True)
    except (ValueError,binascii.Error):
        fail('odf_encryption_parameters_invalid')
    if not minimum<=len(data)<=maximum:
        fail('odf_encryption_parameters_invalid')
    return data


def _attrs(node, allowed, required=()):
    if (any(k not in {q(M,a) for a in allowed} for k in node.attrib)
            or any(q(M,a) not in node.attrib for a in required)
            or (node.text or '').strip() or (node.tail or '').strip()):
        fail('odf_encryption_parameters_invalid')


def _modern_plan(entry,enc,nodes):
    # Only the exact bounded LO descriptor; no alternate KDF or cipher fallback.
    # AEAD has no legacy /1K checksum and Argon2id has no PBKDF2 iteration-count.
    if set(nodes)!={q(M,'algorithm'),q(M,'key-derivation'),q(M,'start-key-generation')}:
        fail('odf_encryption_parameters_invalid')
    algorithm=nodes[q(M,'algorithm')];kd=nodes[q(M,'key-derivation')]
    start=nodes.get(q(M,'start-key-generation'))
    required={q(M,'key-derivation-name'),q(M,'key-size'),q(M,'salt'),
              q(LOEXT,'argon2-iterations'),q(LOEXT,'argon2-memory'),q(LOEXT,'argon2-lanes')}
    _attrs(entry,('full-path','media-type','size'),('full-path','media-type','size'))
    _attrs(enc,())
    _attrs(algorithm,('algorithm-name','initialisation-vector'),('algorithm-name','initialisation-vector'))
    if (set(kd.attrib)!=required or (kd.text or '').strip() or (kd.tail or '').strip()
            or start is None):fail('odf_encryption_parameters_invalid')
    _attrs(start,('start-key-generation-name','key-size'),('start-key-generation-name','key-size'))
    if (entry.get(q(M,'full-path'))!='encrypted-package'
            or algorithm.get(q(M,'algorithm-name'))!=AES_GCM
            or kd.get(q(M,'key-derivation-name'))!=ARGON2ID_LO
            or kd.get(q(M,'key-size'))!='32' or start.get(q(M,'key-size'))!='32'
            or start.get(q(M,'start-key-generation-name'))!='http://www.w3.org/2001/04/xmlenc#sha256'):
        fail('odf_encryption_parameters_invalid')
    iv=binary(algorithm.get(q(M,'initialisation-vector')),12,12)
    salt=binary(kd.get(q(M,'salt')),16,16)
    iterations=number(kd.get(q(LOEXT,'argon2-iterations')),3,1)
    memory=number(kd.get(q(LOEXT,'argon2-memory')),65536,8)
    lanes=number(kd.get(q(LOEXT,'argon2-lanes')),4,1)
    if memory<8*lanes:fail('odf_encryption_parameters_invalid')
    size=number(entry.get(q(M,'size')),MAX_MEMBER,1)
    return dict(modern=True,name=AES_GCM,rounds=0,key_size=32,entry=entry,
                enc=enc,algorithm=algorithm,kd=kd,iv=iv,salt=salt,size=size,
                iterations=iterations,memory=memory,lanes=lanes)


def _plan(entry):
    children=list(entry)
    if len(children)!=1 or children[0].tag!=q(M,'encryption-data'):
        fail('odf_encryption_structure_unsupported')
    enc=children[0]
    modern_candidate=any(
        child.tag==q(M,'algorithm')and child.get(q(M,'algorithm-name'))==AES_GCM
        or child.tag==q(M,'key-derivation')and child.get(q(M,'key-derivation-name'))==ARGON2ID_LO
        for child in enc)
    if not modern_candidate:
        _attrs(enc,('checksum','checksum-type'),('checksum','checksum-type'))
    nodes={}
    for child in enc:
        if child.tag in nodes or len(child):fail('odf_encryption_parameters_invalid')
        nodes[child.tag]=child
    if modern_candidate:
        return _modern_plan(entry,enc,nodes)
    if set(nodes) not in ({q(M,'algorithm'),q(M,'key-derivation')},
                         {q(M,'algorithm'),q(M,'key-derivation'),q(M,'start-key-generation')}):
        fail('odf_encryption_structure_unsupported')
    algorithm=nodes[q(M,'algorithm')];kd=nodes[q(M,'key-derivation')]
    _attrs(algorithm,('algorithm-name','initialisation-vector'),('algorithm-name','initialisation-vector'))
    _attrs(kd,('key-derivation-name','key-size','iteration-count','salt'),('key-derivation-name','iteration-count','salt'))
    name=algorithm.get(q(M,'algorithm-name'))
    if name not in AES_NAMES and name not in BLOWFISH:fail('odf_encryption_algorithm_unsupported')
    if kd.get(q(M,'key-derivation-name')) not in ('PBKDF2',M+'#pbkdf2'):fail('odf_key_derivation_unsupported')
    key_size=number(kd.get(q(M,'key-size'),'16'),32,1)
    if (name in AES_NAMES and key_size!=AES_NAMES[name]) or (name in BLOWFISH and key_size!=16):
        fail('odf_encryption_parameters_invalid')
    start=nodes.get(q(M,'start-key-generation'))
    start_name='SHA1';start_size=20
    if start is not None:
        _attrs(start,('start-key-generation-name','key-size'))
        start_name=start.get(q(M,'start-key-generation-name'),'SHA1')
        start_size=number(start.get(q(M,'key-size'),'20'),32,1)
    start_hash=HASH_NAMES.get(start_name)
    if start_hash is None:fail('odf_start_key_unsupported')
    if start_size!=hashlib.new(start_hash).digest_size:fail('odf_encryption_parameters_invalid')
    checksum_hash=CHECKSUM_NAMES.get(enc.get(q(M,'checksum-type')))
    if checksum_hash is None:fail('odf_checksum_unsupported')
    checksum=binary(enc.get(q(M,'checksum')),hashlib.new(checksum_hash).digest_size,hashlib.new(checksum_hash).digest_size)
    block=16 if name in AES_NAMES else 8
    return dict(name=name,key_size=key_size,rounds=number(kd.get(q(M,'iteration-count')),MAX_ROUNDS,1),
                salt=binary(kd.get(q(M,'salt')),8,64),iv=binary(algorithm.get(q(M,'initialisation-vector')),block,block),
                start_hash=start_hash,checksum_hash=checksum_hash,checksum=checksum,
                size=number(entry.get(q(M,'size')),MAX_MEMBER),entry=entry,enc=enc,algorithm=algorithm,kd=kd)


def _inert_xml(parts,checkpoint):
    # Package paths alone do not reveal inline scripts or event handlers.
    office='urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    text='urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    draw='urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
    script='urn:oasis:names:tc:opendocument:xmlns:script:1.0'
    form='urn:oasis:names:tc:opendocument:xmlns:form:1.0'
    table='urn:oasis:names:tc:opendocument:xmlns:table:1.0'
    for name,data in parts.items():
        if not name.lower().endswith('.xml') or name=='META-INF/manifest.xml':continue
        tick(checkpoint)
        try:root=xml_root(data)
        except (PresentationError,ET.ParseError,UnicodeError):fail('odf_member_xml_invalid')
        for node in root.iter():
            if (node.tag in (q(office,'script'),q(text,'script'),q(draw,'plugin'),
                             q(draw,'object-ole'),q(office,'dde-source'),q(text,'execute-macro'),
                             q(table,'table-source'),q(table,'cell-range-source'))
                    or (node.tag==q(office,'scripts') and (len(node)or(node.text or'').strip()))
                    or node.tag.startswith((q(script,''),q(form,''),q(text,'dde-'),
                                            q(text,'database-'),q(table,'database-'),q(table,'data-pilot-')))
                    or any(attr.startswith(q(script,''))for attr in node.attrib)):
                fail('odf_active_or_signed_package_unsupported')


def _package(data,format,checkpoint):
    if format not in MIMES:fail('odf_password_format_unsupported')
    if type(data)is not bytes or not 0<len(data)<=MAX_BYTES:fail('odf_input_limit')
    tick(checkpoint);parts={};infos={};total=0
    try:
        with zipfile.ZipFile(io.BytesIO(data))as archive:
            members=archive.infolist()
            if not 2<=len(members)<=512:fail('odf_member_limit')
            seen=set()
            for info in members:
                tick(checkpoint);name=info.filename;key=name.rstrip('/')
                if (name!=info.orig_filename or not key or name.startswith('/')
                        or any(c in name for c in '\\:%?#') or any(ord(c)<32 for c in name)
                        or any(p in ('','.','..')for p in key.split('/')) or key.casefold()in seen):
                    fail('odf_member_path_invalid')
                seen.add(key.casefold());mode=info.external_attr>>16
                if stat.S_IFMT(mode)not in(0,stat.S_IFREG,stat.S_IFDIR)or info.flag_bits&1:
                    fail('odf_zip_encryption_or_special_member')
                if info.compress_type not in(zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):fail('odf_compression_unsupported')
                if (key.lower().startswith(('basic/','scripts/')) or
                        key.lower().startswith('meta-inf/') and 'signature'in key.lower()):
                    fail('odf_active_or_signed_package_unsupported')
                total+=info.file_size
                if (info.file_size>MAX_MEMBER or total>MAX_TOTAL or
                        info.file_size>max(1,info.compress_size)*200):fail('odf_package_expansion_limit')
                if info.is_dir():
                    if info.file_size:fail('odf_nonempty_directory')
                    infos[name]=info
                    continue
                parts[name]=read_zip_member(archive,data,info,MAX_MEMBER);infos[name]=info
            if (members[0].filename!='mimetype' or members[0].compress_type!=zipfile.ZIP_STORED
                    or members[0].extra or parts.get('mimetype')!=MIMES[format].encode()):
                fail('odf_mimetype_mismatch')
    except (zipfile.BadZipFile,ZipMemberLimitError,ValueError,zlib.error,EOFError,NotImplementedError)as e:
        if isinstance(e,ODFPasswordError):raise
        fail('odf_malformed_package')
    manifest=parts.get('META-INF/manifest.xml')
    if manifest is None or len(manifest)>1_000_000:fail('odf_manifest_missing')
    try:root=xml_root(manifest)
    except (PresentationError,ET.ParseError,UnicodeError):fail('odf_manifest_invalid')
    if root.tag!=q(M,'manifest'):fail('odf_manifest_invalid')
    seen=set();plans={};work=0;roots=[]
    for entry in root:
        if entry.tag!=q(M,'file-entry'):fail('odf_manifest_structure_unsupported')
        name=entry.get(q(M,'full-path'))
        if not name or name.casefold()in seen:fail('odf_manifest_duplicate')
        seen.add(name.casefold())
        if name=='/':
            roots.append(entry)
            if len(entry):fail('odf_root_encryption_unsupported')
            continue
        key=name.rstrip('/')
        if (not key or name.startswith('/')or any(c in name for c in '\\:%?#')
                or any(ord(c)<32 for c in name)
                or any(p in('','.','..')for p in key.split('/'))):
            fail('odf_manifest_target_invalid')
        if (key.lower().startswith(('basic/','scripts/'))or key.lower()in('basic','scripts')
                or key.lower().startswith('meta-inf/')and'signature'in key.lower()):
            fail('odf_active_or_signed_package_unsupported')
        if name.endswith('/'):
            if len(entry):fail('odf_directory_encryption_unsupported')
            continue
        if name not in parts or name in('mimetype','META-INF/manifest.xml'):fail('odf_manifest_target_invalid')
        if len(entry):
            plan=_plan(entry);plans[name]=plan;work+=plan['rounds']*((plan['key_size']+19)//20)
            if infos[name].compress_type!=zipfile.ZIP_STORED:fail('odf_encrypted_member_not_stored')
    modern=any(p.get('modern')for p in plans.values())
    if modern:
        # A wholesome encrypted package omits the outer '/' and content.xml
        # entries. Validate its entire admitted outer inventory before crypto,
        # so a later duplicate/malformed entry cannot masquerade as this profile.
        _attrs(root,('version',),('version',))
        if (root.get(q(M,'version'))not in('1.3','1.4','1.5')
                or roots or set(plans)!={'encrypted-package'} or seen!={'encrypted-package'}
                or set(parts)!={'mimetype','META-INF/manifest.xml','encrypted-package'}
                or set(infos)!=set(parts)
                or plans['encrypted-package']['entry'].get(q(M,'media-type'))!=MIMES[format]):
            fail('odf_encryption_parameters_invalid')
        encrypted=parts['encrypted-package'];plan=plans['encrypted-package']
        if format!='odt':
            # Preserve the existing diagnostic envelope for other families.
            if len(encrypted)<16:fail('odf_ciphertext_invalid')
            fail('odf_encryption_algorithm_unsupported')
        number(plan['entry'].get(q(M,'size')),MAX_BYTES,1)
        # XMLENC GCM stores IV || ciphertext || 16-byte tag, without padding.
        if len(encrypted)<=28 or encrypted[:12]!=plan['iv']:fail('odf_ciphertext_invalid')
        return parts,infos,root,plans
    if len(roots)!=1 or roots[0].get(q(M,'media-type'))!=MIMES[format]or'content.xml'not in seen:
        fail('odf_manifest_type_mismatch')
    # ODF exempts mimetype and META-INF files from the manifest inventory.
    if any(name.casefold()not in seen for name in parts
           if name!='mimetype'and not name.startswith('META-INF/')):
        fail('odf_manifest_member_missing')
    if len(plans)>64 or work>MAX_WORK:fail('odf_encryption_resource_limit')
    if plans and 'content.xml'not in plans:fail('odf_partial_encryption_unsupported')
    return parts,infos,root,plans


def _cipher(plan,key,iv):
    try:
        from Cryptodome.Cipher import AES,Blowfish
    except ImportError:fail('odf_crypto_unavailable')
    if plan['name']in AES_NAMES:return AES.new(key,AES.MODE_CBC,iv=iv)
    return Blowfish.new(key,Blowfish.MODE_CFB,iv=iv,segment_size=8)


def _modern_crypto(plan,password,checkpoint):
    tick(checkpoint)
    error_code=None
    try:
        from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import UnsupportedAlgorithm
    except ImportError:error_code='odf_crypto_unavailable'
    if error_code:fail(error_code)
    try:
        key=Argon2id(salt=plan['salt'],length=32,iterations=plan['iterations'],
            memory_cost=plan['memory'],lanes=plan['lanes']).derive(hashlib.sha256(password).digest())
        cipher=AESGCM(key)
    except UnsupportedAlgorithm:error_code='odf_crypto_unavailable'
    except MemoryError:error_code='odf_encryption_resource_limit'
    except ValueError:error_code='odf_encryption_parameters_invalid'
    # Raise outside the backend exception handler: no backend message/context
    # can become a technical traceback containing key material or input data.
    if error_code:fail(error_code)
    tick(checkpoint)
    return cipher


def _modern_read(parts,plan,format,password,checkpoint):
    cipher=_modern_crypto(plan,password_bytes(password),checkpoint)
    error_code=None
    try:
        from cryptography.exceptions import InvalidTag
        compressed=cipher.decrypt(plan['iv'],parts['encrypted-package'][12:],None)
    except InvalidTag:error_code='odf_password_rejected_or_corrupt'
    except MemoryError:error_code='odf_encryption_resource_limit'
    except ValueError:error_code='odf_ciphertext_invalid'
    if error_code:fail(error_code)
    tick(checkpoint)
    # No inflate, XML parse, editor or plaintext result before the complete tag.
    clear=_inflate(compressed,plan)
    inner,_,_,inner_plans=_package(clear,format,checkpoint)
    if inner_plans or 'encrypted-package'in inner:fail('odf_nested_encryption_unsupported')
    _inert_xml(inner,checkpoint);tick(checkpoint)
    return clear,dict(encrypted=True,decrypted_for_read_only=True,encrypted_members=1,
        algorithms=[AES_GCM],modern_profile='LO_ARGON2ID19_AES256GCM',
        password_verification='AEAD_TAG_MATCHED',data_integrity_verified=True,
        encryption_authenticity='AEAD_PAYLOAD_AUTHENTICATED_NOT_ORIGIN_IDENTITY')


def _modern_encrypt(original,parts,infos,root,plan,clear,format,password,checkpoint):
    source_clear,_=prepare_read(original,format,password,checkpoint=checkpoint)
    source_parts,_,_,_=_package(source_clear,format,checkpoint)
    clear_parts,_,_,clear_plans=_package(clear,format,checkpoint)
    if clear_plans or set(source_parts)!=set(clear_parts):fail('odf_edit_member_set_changed')
    _inert_xml(clear_parts,checkpoint)
    # Same parameters and envelope; fresh salt and nonce for the new ciphertext.
    plan['salt']=secrets.token_bytes(16);plan['iv']=secrets.token_bytes(12)
    plan['entry'].set(q(M,'size'),str(len(clear)))
    plan['kd'].set(q(M,'salt'),base64.b64encode(plan['salt']).decode())
    plan['algorithm'].set(q(M,'initialisation-vector'),base64.b64encode(plan['iv']).decode())
    compressor=zlib.compressobj(6,zlib.DEFLATED,-15)
    compressed=compressor.compress(clear)+compressor.flush()
    cipher=_modern_crypto(plan,password_bytes(password),checkpoint)
    error_code=None
    try:
        encrypted=plan['iv']+cipher.encrypt(plan['iv'],compressed,None)
    except MemoryError:error_code='odf_encryption_resource_limit'
    except ValueError:error_code='odf_crypto_failed'
    if error_code:fail(error_code)
    tick(checkpoint)
    parts=dict(parts);parts['encrypted-package']=encrypted
    parts['META-INF/manifest.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w')as archive:
        for name in ['mimetype']+[n for n in infos if n!='mimetype']:
            info=copy.copy(infos[name]);info.extra=b'';info.comment=b''
            info.compress_type=zipfile.ZIP_DEFLATED if name=='META-INF/manifest.xml'else zipfile.ZIP_STORED
            archive.writestr(info,parts[name])
    result=buffer.getvalue()
    if len(result)>MAX_BYTES:fail('odf_output_limit')
    verified,_=prepare_read(result,format,password,checkpoint=checkpoint)
    if verified!=clear:fail('odf_encrypted_output_verification_failed')
    return result


def _key(plan,password):
    return hashlib.pbkdf2_hmac('sha1',hashlib.new(plan['start_hash'],password).digest(),
                               plan['salt'],plan['rounds'],plan['key_size'])


def _inflate(compressed,plan):
    try:
        inflater=zlib.decompressobj(-15);clear=inflater.decompress(compressed,plan['size']+1)
        if (len(clear)!=plan['size'] or not inflater.eof or inflater.unconsumed_tail
                or inflater.unused_data):fail('odf_decrypted_size_mismatch')
    except zlib.error:fail('odf_password_rejected_or_corrupt')
    return clear


def _zip(parts,infos,root):
    buffer=io.BytesIO();parts=dict(parts);parts['META-INF/manifest.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(buffer,'w')as archive:
        for name in ['mimetype']+[n for n in infos if n!='mimetype']:
            info=copy.copy(infos[name]);info.extra=b'';info.comment=b''
            info.compress_type=zipfile.ZIP_STORED if name=='mimetype'else zipfile.ZIP_DEFLATED
            archive.writestr(info,parts.get(name,b''))
    result=buffer.getvalue()
    if len(result)>MAX_BYTES:fail('odf_output_limit')
    return result


def prepare_read(data,format,password=None,*,checkpoint=None):
    parts,infos,root,plans=_package(data,format,checkpoint)
    if plans.get('encrypted-package',{}).get('modern'):
        return _modern_read(parts,plans['encrypted-package'],format,password,checkpoint)
    if not plans:
        if password is not None:password_bytes(password)
        return data,dict(encrypted=False)
    secret=password_bytes(password);total=sum(len(v)for k,v in parts.items()if k not in plans)
    for name,plan in plans.items():
        tick(checkpoint);encrypted=parts[name]
        if plan['name']in AES_NAMES and (not encrypted or len(encrypted)%16):fail('odf_ciphertext_invalid')
        compressed=_cipher(plan,_key(plan,secret),plan['iv']).decrypt(encrypted)
        if plan['name']in AES_NAMES:
            if not compressed or not 1<=compressed[-1]<=16:fail('odf_password_rejected_or_corrupt')
            compressed=compressed[:-compressed[-1]]
        checksum=hashlib.new(plan['checksum_hash'],compressed[:1024]).digest()
        if not hmac.compare_digest(checksum,plan['checksum']):fail('odf_password_rejected_or_corrupt')
        clear=_inflate(compressed,plan);total+=len(clear)
        if total>MAX_TOTAL:fail('odf_package_expansion_limit')
        parts[name]=clear;plan['entry'].remove(plan['enc']);plan['entry'].attrib.pop(q(M,'size'),None)
    tick(checkpoint);secret=None
    _inert_xml(parts,checkpoint)
    result=_zip(parts,infos,root)
    return result,dict(encrypted=True,decrypted_for_read_only=True,encrypted_members=len(plans),
        algorithms=sorted({p['name']for p in plans.values()}),password_checksum='MATCHED_NOT_AUTHENTICITY_PROOF')


def _encrypt_to_original(original,clear,format,password,checkpoint):
    original_parts,original_infos,root,plans=_package(original,format,checkpoint)
    if plans.get('encrypted-package',{}).get('modern'):
        return _modern_encrypt(original,original_parts,original_infos,root,
                               plans['encrypted-package'],clear,format,password,checkpoint)
    parts,infos,_,clear_plans=_package(clear,format,checkpoint)
    if clear_plans or not plans:fail('odf_encrypted_edit_contract')
    if set(parts)!=set(original_parts):fail('odf_edit_member_set_changed')
    # Editors operate on files; retain original harmless directory records too.
    infos={name:infos.get(name,info)for name,info in original_infos.items()}
    secret=password_bytes(password)
    for name,plan in plans.items():
        tick(checkpoint);plain=parts[name]
        if len(plain)>MAX_MEMBER:fail('odf_output_limit')
        compressor=zlib.compressobj(6,zlib.DEFLATED,-15);compressed=compressor.compress(plain)+compressor.flush()
        plan['salt']=secrets.token_bytes(len(plan['salt']));plan['iv']=secrets.token_bytes(len(plan['iv']))
        plan['entry'].set(q(M,'size'),str(len(plain)))
        plan['enc'].set(q(M,'checksum'),base64.b64encode(hashlib.new(plan['checksum_hash'],compressed[:1024]).digest()).decode())
        plan['kd'].set(q(M,'salt'),base64.b64encode(plan['salt']).decode())
        plan['algorithm'].set(q(M,'initialisation-vector'),base64.b64encode(plan['iv']).decode())
        if plan['name']in AES_NAMES:
            pad=16-len(compressed)%16;compressed+=secrets.token_bytes(pad-1)+bytes([pad])
        parts[name]=_cipher(plan,_key(plan,secret),plan['iv']).encrypt(compressed)
    # Encryption uses stored members per ODF 3.4; no ordinary ZIP crypto flag.
    parts['META-INF/manifest.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w')as archive:
        for name in ['mimetype']+[n for n in infos if n!='mimetype']:
            info=copy.copy(infos[name]);info.extra=b'';info.comment=b''
            info.compress_type=zipfile.ZIP_STORED if name=='mimetype'or name in plans else zipfile.ZIP_DEFLATED
            archive.writestr(info,parts.get(name,b''))
    result=buffer.getvalue();secret=None;tick(checkpoint)
    if len(result)>MAX_BYTES:fail('odf_output_limit')
    # Check final decryption against the exact editor output member payloads.
    verified,_=prepare_read(result,format,password,checkpoint=checkpoint)
    verified_parts,_,_,_=_package(verified,format,checkpoint)
    if any(verified_parts[k]!=parts_value for k,parts_value in _package(clear,format,checkpoint)[0].items()if k!='META-INF/manifest.xml'):
        fail('odf_encrypted_output_verification_failed')
    return result


def encrypted_edit(data,format,password,operation,*,checkpoint=None):
    clear,metadata=prepare_read(data,format,password,checkpoint=checkpoint)
    if not metadata['encrypted']:fail('odf_source_not_encrypted')
    if type(operation)is not dict:fail('odf_edit_schema')
    tick(checkpoint)
    try:
        if format in ('odt','ott'):
            from tools.scoped_odf_profiles import render_edit
            if set(operation)!={'old_text','new_text'}:fail('odf_edit_schema')
            edited=render_edit(clear,operation['old_text'],operation['new_text'],format,checkpoint)
        elif format in ('ods','ots'):
            from tools.scoped_ods import edit_spreadsheet
            edited=edit_spreadsheet(clear,operation,format=format,checkpoint=checkpoint)
        elif format in ('odp','otp'):
            from tools.scoped_presentation_text import edit_text
            edited=edit_text(clear,format,operation)
        else:fail('odf_password_format_unsupported')
    except (ValueError,TypeError,KeyError,OverflowError)as e:
        if isinstance(e,ODFPasswordError):raise
        # Public error text is a fixed code; never serialize operation/password.
        fail('odf_native_edit_refused')
    tick(checkpoint)
    result=_encrypt_to_original(data,edited,format,password,checkpoint)
    result_metadata=dict(
        encrypted=True,source_unchanged=True,password_preserved=True,
        new_member_salts_and_ivs=True,plaintext_published=False,
        encryption_authenticity='NOT_VERIFIED',native_edit_profile=format)
    if metadata.get('modern_profile'):
        result_metadata.update(modern_profile=metadata['modern_profile'],
            data_integrity_verified=True,password_verification='AEAD_TAG_MATCHED',
            encryption_authenticity=metadata['encryption_authenticity'])
    return result,result_metadata
