"""Own small ODF-template fixtures; no product codec imported.

ODF 1.3 package layout, raw DEFLATE, SHA256 start/checksum, PBKDF2-SHA1,
AES256-CBC with W3C padding. Independent crypto implementation: cryptography.
This is a fixture/spec oracle, not an Office application validity oracle.
"""
import base64
import hashlib
import io
import zipfile
import zlib
from xml.etree import ElementTree as E
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

M = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
O = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
T = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
TB = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
D = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
S = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
F = 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
MIMES = {f:'application/vnd.oasis.opendocument.'+v for f,v in
         [('ott','text-template'),('ots','spreadsheet-template'),('otp','presentation-template')]}
AES = 'http://www.w3.org/2001/04/xmlenc#aes256-cbc'
SHA256 = 'http://www.w3.org/2000/09/xmldsig#sha256'
ROUNDS = 4096


def q(ns,n): return '{'+ns+'}'+n
def b64(b): return base64.b64encode(b).decode('ascii')
def xml(n): return E.tostring(n,encoding='utf-8',xml_declaration=True)
def sha(b): return hashlib.sha256(b).hexdigest()


def content(fmt,after=False):
    root=E.Element(q(O,'document-content'),{q(O,'version'):'1.3'})
    E.SubElement(root,q(O,'automatic-styles'))
    body=E.SubElement(root,q(O,'body'))
    if fmt=='ott':
        text=E.SubElement(body,q(O,'text'))
        E.SubElement(text,q(T,'p')).text='OTT-UNIQUE-AFTER' if after else 'OTT-UNIQUE-BEFORE'
        E.SubElement(text,q(T,'p')).text='RETAINED-TEXT-PARAGRAPH'
    elif fmt=='ots':
        book=E.SubElement(body,q(O,'spreadsheet'))
        table=E.SubElement(book,q(TB,'table'),{q(TB,'name'):'TemplateSheet'})
        row=E.SubElement(table,q(TB,'table-row'))
        cell=E.SubElement(row,q(TB,'table-cell'),{q(O,'value-type'):'string'})
        E.SubElement(cell,q(T,'p')).text='OTS-AFTER' if after else 'OTS-BEFORE'
        cell=E.SubElement(row,q(TB,'table-cell'),{q(O,'value-type'):'float',q(O,'value'):'17'})
        E.SubElement(cell,q(T,'p')).text='17'
    else:
        presentation=E.SubElement(body,q(O,'presentation'))
        for num,value in [(1,'OTP-UNIQUE-AFTER' if after else 'OTP-UNIQUE-BEFORE'),(2,'RETAINED-SECOND-SLIDE')]:
            page=E.SubElement(presentation,q(D,'page'),{q(D,'name'):'Slide'+str(num),q(D,'master-page-name'):'Default'})
            frame=E.SubElement(page,q(D,'frame'),{q(D,'name'):'Title'+str(num)})
            box=E.SubElement(frame,q(D,'text-box'))
            E.SubElement(box,q(T,'p')).text=value
    return xml(root)


def clear_parts(fmt):
    styles=E.Element(q(O,'document-styles'),{q(O,'version'):'1.3'})
    E.SubElement(styles,q(O,'styles'))
    auto=E.SubElement(styles,q(O,'automatic-styles'))
    layout=E.SubElement(auto,q(S,'page-layout'),{q(S,'name'):'pm1'})
    E.SubElement(layout,q(S,'page-layout-properties'),{q(F,'page-width'):'28cm',q(F,'page-height'):'21cm'})
    masters=E.SubElement(styles,q(O,'master-styles'))
    E.SubElement(masters,q(S,'master-page'),{q(S,'name'):'Default',q(S,'page-layout-name'):'pm1'})
    meta=E.Element(q(O,'document-meta'),{q(O,'version'):'1.3'})
    E.SubElement(meta,q(O,'meta'))
    settings=E.Element(q(O,'document-settings'),{q(O,'version'):'1.3'})
    E.SubElement(settings,q(O,'settings'))
    return {'mimetype':MIMES[fmt].encode(),'content.xml':content(fmt),'styles.xml':xml(styles),
            'meta.xml':xml(meta),'settings.xml':xml(settings),'Pictures/retained.bin':b'OWN-INERT-TEMPLATE-RESOURCE-20261112'}


def build(fmt,password):
    parts=clear_parts(fmt)
    manifest=E.Element(q(M,'manifest'),{q(M,'version'):'1.3'})
    E.SubElement(manifest,q(M,'file-entry'),{q(M,'full-path'):'/',q(M,'media-type'):MIMES[fmt],q(M,'version'):'1.3'})
    for name,raw in list(parts.items()):
        if name=='mimetype':continue
        entry=E.SubElement(manifest,q(M,'file-entry'),{q(M,'full-path'):name,q(M,'media-type'):'text/xml' if name.endswith('.xml') else 'application/octet-stream'})
        if not name.endswith('.xml'):continue
        compressor=zlib.compressobj(6,zlib.DEFLATED,-15)
        compressed=compressor.compress(raw)+compressor.flush()
        # Stable structure/salt/IV in these unique synthetic fixtures only.
        salt=hashlib.sha256(('own-salt:'+fmt+':'+name).encode()).digest()[:16]
        iv=hashlib.sha256(('own-iv:'+fmt+':'+name).encode()).digest()[:16]
        key=hashlib.pbkdf2_hmac('sha1',hashlib.sha256(password.encode()).digest(),salt,ROUNDS,32)
        pad=16-len(compressed)%16
        enc=Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor()
        parts[name]=enc.update(compressed+b'\0'*(pad-1)+bytes([pad]))+enc.finalize()
        entry.set(q(M,'size'),str(len(raw)))
        encryption=E.SubElement(entry,q(M,'encryption-data'),{q(M,'checksum-type'):M+'#sha256-1k',q(M,'checksum'):b64(hashlib.sha256(compressed[:1024]).digest())})
        E.SubElement(encryption,q(M,'algorithm'),{q(M,'algorithm-name'):AES,q(M,'initialisation-vector'):b64(iv)})
        E.SubElement(encryption,q(M,'key-derivation'),{q(M,'key-derivation-name'):'PBKDF2',q(M,'key-size'):'32',q(M,'iteration-count'):str(ROUNDS),q(M,'salt'):b64(salt)})
        E.SubElement(encryption,q(M,'start-key-generation'),{q(M,'start-key-generation-name'):SHA256,q(M,'key-size'):'32'})
    parts['META-INF/manifest.xml']=xml(manifest)
    return pack(parts)


def pack(parts):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        for name,value in parts.items():
            info=zipfile.ZipInfo(name,(2026,11,12,0,0,0))
            info.create_system=3;info.external_attr=(0o100600<<16)
            info.compress_type=zipfile.ZIP_STORED
            z.writestr(info,value)
    return buf.getvalue()


def oracle(raw,fmt,password):
    """Independent member decryption and ZIP/XML/profile verification."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist();parts={n:z.read(n) for n in z.namelist()}
        assert len(infos)==len(parts)==7
        assert infos[0].filename=='mimetype' and infos[0].compress_type==0 and not infos[0].extra
        assert parts['mimetype']==MIMES[fmt].encode()
        assert all(not i.flag_bits&1 and i.compress_type in (0,8) for i in infos)
        manifest=E.fromstring(parts['META-INF/manifest.xml'])
        paths=[n.get(q(M,'full-path')) for n in manifest]
        assert len(paths)==len(set(paths))
        roots=[n for n in manifest if n.get(q(M,'full-path'))=='/']
        assert len(roots)==1 and roots[0].get(q(M,'media-type'))==MIMES[fmt]
        encrypted=[];salts={};ivs={}
        for entry in manifest:
            e=entry.find(q(M,'encryption-data'))
            if e is None:continue
            name=entry.get(q(M,'full-path'));encrypted.append(name)
            assert z.getinfo(name).compress_type==zipfile.ZIP_STORED
            alg=e.find(q(M,'algorithm'));kd=e.find(q(M,'key-derivation'));start=e.find(q(M,'start-key-generation'))
            assert alg.get(q(M,'algorithm-name'))==AES and kd.get(q(M,'key-derivation-name'))=='PBKDF2'
            assert start.get(q(M,'start-key-generation-name'))==SHA256 and start.get(q(M,'key-size'))=='32'
            assert kd.get(q(M,'iteration-count'))==str(ROUNDS)
            assert e.get(q(M,'checksum-type'))==M+'#sha256-1k' and kd.get(q(M,'key-size'))=='32'
            salt=base64.b64decode(kd.get(q(M,'salt')),validate=True);iv=base64.b64decode(alg.get(q(M,'initialisation-vector')),validate=True)
            assert len(salt)==len(iv)==16
            key=hashlib.pbkdf2_hmac('sha1',hashlib.sha256(password.encode()).digest(),salt,int(kd.get(q(M,'iteration-count'))),32)
            decryptor=Cipher(algorithms.AES(key),modes.CBC(iv)).decryptor();compressed=decryptor.update(parts[name])+decryptor.finalize()
            assert 1<=compressed[-1]<=16
            compressed=compressed[:-compressed[-1]]
            assert hashlib.sha256(compressed[:1024]).digest()==base64.b64decode(e.get(q(M,'checksum')),validate=True)
            inflater=zlib.decompressobj(-15);plain=inflater.decompress(compressed)+inflater.flush()
            assert inflater.eof and not inflater.unused_data and len(plain)==int(entry.get(q(M,'size')))
            parts[name]=plain;salts[name]=sha(salt);ivs[name]=sha(iv)
        assert len(encrypted)==4 and set(encrypted)=={'content.xml','styles.xml','meta.xml','settings.xml'}
        root=E.fromstring(parts['content.xml']);body=root.find(q(O,'body'))
        expected={'ott':'text','ots':'spreadsheet','otp':'presentation'}[fmt]
        assert root.tag==q(O,'document-content') and len(body)==1 and body[0].tag==q(O,expected)
        for name,value in parts.items():
            if name.endswith('.xml'):E.fromstring(value)
        return parts,{'format':fmt,'mime':MIMES[fmt],'members':sorted(parts),'encrypted_members':sorted(encrypted),
                      'root_body':expected,'salts_sha256':salts,'ivs_sha256':ivs,'algorithm':AES,'rounds':ROUNDS}


def semantics(parts,fmt,after):
    root=E.fromstring(parts['content.xml'])
    texts=[p.text for p in root.iter(q(T,'p'))]
    if fmt=='ott':return texts==['OTT-UNIQUE-AFTER' if after else 'OTT-UNIQUE-BEFORE','RETAINED-TEXT-PARAGRAPH']
    if fmt=='ots':
        cells=list(root.iter(q(TB,'table-cell')))
        return len(cells)==2 and texts==['OTS-AFTER' if after else 'OTS-BEFORE','17'] and cells[0].get(q(O,'value-type'))=='string' and cells[1].get(q(O,'value'))=='17'
    pages=list(root.iter(q(D,'page')))
    return len(pages)==2 and texts==['OTP-UNIQUE-AFTER' if after else 'OTP-UNIQUE-BEFORE','RETAINED-SECOND-SLIDE'] and all(p.get(q(D,'master-page-name'))=='Default' for p in pages)
