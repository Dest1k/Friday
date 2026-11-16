"""Independent stdlib postconditions on actual bytes, never creates product EML.

Pure byte checks. Root separately authenticates received receipt/native/custody.
No future artifact is required or credited at Source/current preflight.
"""
import email.policy,hashlib,re
from email.parser import BytesParser
from email.utils import getaddresses
MAX_BYTES=1048576
CREATE_BODY='Коллеги, сверяем поставку за ноябрь.\nКоличество: 24 комплекта; сумма: 18 750,50 RUB.\nОтветственный: Анна Белова. Контрольная строка: склад № 7 — готово.'
CREATE_SUBJECT='Сверка поставки — ноябрь'
EDIT_SUBJECT='Уведомление — согласовано ✅'
def need(ok,why):
 if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
 need(type(raw)is bytes and 0<len(raw)<=MAX_BYTES,'BOUNDED_EML_BYTES_REQUIRED')
 m=BytesParser(policy=email.policy.default).parsebytes(raw)
 need(all(not p.defects for p in m.walk()),'INDEPENDENT_MIME_DEFECT')
 need(len(m.get_all('Subject',[]))==1,'ONE_TOP_LEVEL_SUBJECT_REQUIRED')
 return m

def verify_create(raw):
 m=parse(raw)
 need(str(m['Subject'])==CREATE_SUBJECT,'CREATE_EXACT_UNICODE_SUBJECT')
 need(getaddresses(m.get_all('From',[]))==[('', 'supply@example.org')],'CREATE_EXACT_FROM')
 need(getaddresses(m.get_all('To',[]))==[('', 'planning@example.org')],'CREATE_EXACT_TO')
 need(not m.is_multipart()and m.get_content_type()=='text/plain'and m.get_content_charset()=='utf-8','CREATE_NATIVE_PLAIN_UTF8')
 need(m.get_content().replace('\r\n','\n')==CREATE_BODY+'\n','CREATE_EXACT_THREE_LINES_PLUS_SERIALIZER_FINAL_NEWLINE')
 need(not list(m.iter_attachments())and all(not p.get_filename()and p.get_content_disposition()!='attachment' for p in m.walk()),'CREATE_NO_ATTACHMENTS')
 return dict(native_eml=True,independent_reopen=True,required_content_exact=True,attachments=0,bytes=len(raw),sha256=digest(raw),app_or_formal_acceptance=False)

def subject_cut(raw):
 # Preserve exact raw header ordering, folding, separators, MIME graph and payload.
 sep=re.search(br'\r\n\r\n|\n\n|\r\r',raw);need(sep is not None,'HEADER_BODY_BOUNDARY_REQUIRED')
 header=raw[:sep.start()];lines=header.splitlines(keepends=True)
 # Last header line has no terminator inside header. Folded continuation is same block.
 blocks=[];offset=0
 for line in lines:
  if line.startswith((b' ',b'\t')):
   need(bool(blocks),'BAD_HEADER_CONTINUATION');blocks[-1][2]+=len(line)
  else:
   name=line.split(b':',1)[0].lower();need(b':'in line,'MALFORMED_HEADER')
   blocks.append([name,offset,offset+len(line)])
  offset+=len(line)
 matches=[b for b in blocks if b[0]==b'subject'];need(len(matches)==1,'ONE_RAW_SUBJECT_REQUIRED')
 _,start,end=matches[0]
 return raw[:start]+raw[end:]

def payloads(m):
 return [(tuple(p.get_all('Content-Type',[])),tuple(p.get_all('Content-Disposition',[])),p.get_filename(),digest(p.get_payload(decode=True)or b''))for p in m.walk()if not p.is_multipart()]

def verify_edit(source,output,*,expected_source_sha256):
 need(digest(source)==expected_source_sha256,'IMMUTABLE_SOURCE_SHA_REQUIRED')
 a=parse(source);b=parse(output)
 need(str(b['Subject'])==EDIT_SUBJECT,'EDIT_EXACT_NEW_SUBJECT')
 need(str(a['Subject'])!=EDIT_SUBJECT,'EDIT_MUST_CHANGE_SUBJECT')
 need(subject_cut(source)==subject_cut(output),'ALL_NON_SUBJECT_RAW_BYTES_PRESERVED')
 need(payloads(a)==payloads(b),'ALL_BODY_AND_ATTACHMENT_DECODED_BYTES_PRESERVED')
 need(digest(source)!=digest(output),'DISTINCT_EDITED_BYTES_REQUIRED')
 return dict(native_eml=True,independent_reopen=True,subject_only=True,all_unselected_bytes_preserved=True,body_attachment_hashes_preserved=True,source_sha256=digest(source),bytes=len(output),sha256=digest(output),app_or_formal_acceptance=False)
