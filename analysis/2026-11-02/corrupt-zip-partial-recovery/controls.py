from pathlib import Path
import hashlib,io,json,struct,types,zipfile
P=Path(__file__).resolve().parent
manifest=json.loads((P/'manifest.json').read_text());checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
for row in manifest['product_files']:
 raw=(P/row['published_source']).read_bytes();check('source_pin:'+row['path'],hashlib.sha256(raw).hexdigest()==row['sha256']and len(raw)==row['bytes']);compile(raw,row['path'],'exec')
check('four_sources_compile',len(manifest['product_files'])==4)
m=types.ModuleType('exact_bounded_zip');exec(compile((P/'source/tools/scoped_zip.py').read_bytes(),'scoped_zip.py','exec'),m.__dict__)
def fixture(method):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',compression=method)as z:
  z.writestr('healthy.txt',b'original healthy bytes\n');z.writestr('damaged.bin',b'neutral payload'*8)
 return b.getvalue()
def member(data,name,limit=4096):
 with zipfile.ZipFile(io.BytesIO(data))as z:return m.read_zip_member(z,data,z.getinfo(name),limit)
def payload_offset(data,name):
 with zipfile.ZipFile(io.BytesIO(data))as z:i=z.getinfo(name);off=i.header_offset;return off+30+sum(struct.unpack_from('<HH',data,off+26)),i.compress_size,off
def refuses(name,fn,kind,not_kind=None):
 try:fn()
 except kind as exc:check(name,not_kind is None or not isinstance(exc,not_kind))
 else:raise AssertionError(name)
for method in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):check('healthy_exact:'+str(method),member(fixture(method),'healthy.txt')==b'original healthy bytes\n')
data=fixture(zipfile.ZIP_STORED);at,size,off=payload_offset(data,'damaged.bin');bad=bytearray(data);bad[at]^=1
refuses('CRC_error_is_payload_only',lambda:member(bytes(bad),'damaged.bin'),m.ZipMemberDataError)
check('healthy_member_still_exact_after_other_damage',member(bytes(bad),'healthy.txt')==b'original healthy bytes\n')
refuses('bound_is_not_salvageable_payload',lambda:member(data,'healthy.txt',0),m.ZipMemberLimitError,m.ZipMemberDataError)
header=bytearray(data);header[off+14]^=1
refuses('header_CRC_mismatch_stays_structural',lambda:member(bytes(header),'damaged.bin'),zipfile.BadZipFile,m.ZipMemberDataError)
name=bytearray(data);name[off+30]^=1
refuses('local_name_mismatch_stays_structural',lambda:member(bytes(name),'damaged.bin'),zipfile.BadZipFile,m.ZipMemberDataError)
data=fixture(zipfile.ZIP_DEFLATED);at,size,off=payload_offset(data,'damaged.bin');bad=bytearray(data);bad[at:at+size]=b'\xff'*size
refuses('invalid_deflate_is_typed_payload',lambda:member(bytes(bad),'damaged.bin'),m.ZipMemberDataError)
print(json.dumps(dict(status='PASS',checks=checks,count=len(checks),source_only=True,whole_archive_authorization=False,installed_or_Telegram_acceptance=False),ensure_ascii=False,indent=2))
