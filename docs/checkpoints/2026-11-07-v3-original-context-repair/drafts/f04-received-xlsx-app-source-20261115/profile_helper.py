"""Narrow source-only helper for a disposable initialized Office macro profile.

Call prepare(stage, macro_text, template_dir) AFTER --terminate_after_init and
BEFORE the single document macro. No Office invocation occurs in this module.
Keep the caller's existing deadline and process/resource containment unchanged.
"""
import hashlib, os, re, stat, tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

OOR='{http://openoffice.org/2001/registry}'
def need(v,m):
 if not v:raise ValueError(m)
def stable(p):
 p=Path(p);need(p.is_absolute() and not any(q.is_symlink() for q in (p,*p.parents)),'unsymlinked absolute file required')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==os.getuid() and a.st_nlink==1 and 0<a.st_size<1000000,'unsafe own profile/input file')
  with os.fdopen(fd,'rb',closefd=False) as f:raw=f.read(1000000)
  b=os.fstat(fd);z=p.lstat()
  key=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(key(a)==key(b)==key(z) and len(raw)==a.st_size,'file changed')
 finally:os.close(fd)
 return raw,key(a)
def property_values(root,path,name):
 return [v.text for item in root if item.get(OOR+'path')==path for prop in item if prop.get(OOR+'name')==name for v in prop.findall('value')]
def canonical(el):
 return (el.tag,tuple(sorted(el.attrib.items())),(el.text or '').strip(),tuple(canonical(x) for x in el))
def security_without_losing_setup(raw):
 root=ET.fromstring(raw);need(root.tag==OOR+'items','expected registry root')
 need(property_values(root,'/org.openoffice.Setup/Office','ooSetupInstCompleted')==['true'],'own initialization is not complete; do not document-launch')
 old_values=property_values(root,'/org.openoffice.Office.Common/Security/Scripting','MacroSecurityLevel')
 if not old_values:
  close=b'</oor:items>';need(raw.count(close)==1,'expected current-toolchain registry closure')
  addition=b'<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>0</value></prop></item>\n'
  out=raw.replace(close,addition+close)
  need(out.replace(addition,b'',1)==raw,'other registry bytes changed')
 elif len(old_values)==1:
  pattern=rb'(<item\s+oor:path="/org\.openoffice\.Office\.Common/Security/Scripting"[^>]*>)(.*?)(</item>)'
  matches=list(re.finditer(pattern,raw,re.S));need(len(matches)==1,'ambiguous existing security item')
  item=matches[0];content=item.group(2)
  prop=rb'(<prop\s+oor:name="MacroSecurityLevel"[^>]*>\s*<value>)[^<]*(</value>\s*</prop>)'
  updated,count=re.subn(prop,lambda m:m.group(1)+b'0'+m.group(2),content,flags=re.S);need(count==1,'ambiguous security property')
  out=raw[:item.start(2)]+updated+raw[item.end(2):]
 else:raise ValueError('duplicate security property')
 new=ET.fromstring(out);need(property_values(new,'/org.openoffice.Office.Common/Security/Scripting','MacroSecurityLevel')==['0'],'security merge failed')
 old_other=[canonical(x) for x in root if x.get(OOR+'path')!='/org.openoffice.Office.Common/Security/Scripting']
 new_other=[canonical(x) for x in new if x.get(OOR+'path')!='/org.openoffice.Office.Common/Security/Scripting']
 need(old_other==new_other and property_values(new,'/org.openoffice.Setup/Office','ooSetupInstCompleted')==['true'],'existing setup or other registry metadata lost')
 return out
def prepare(stage,macro_text,template_dir):
 stage=Path(stage);templates=Path(template_dir)
 need(stage == Path(__file__).parent/'operation' and not stage.is_symlink(),'own /tmp/friday-office-* stage required')
 s=stage.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'own stage0700 required')
 need(str(stage) in macro_text,'macro must bind this exact stage')
 standard=stage/'profile/user/basic/Standard';registry=stage/'profile/user/registrymodifications.xcu'
 reg_before,_=stable(registry);reg_after=security_without_losing_setup(reg_before)
 module=('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd"><script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">'+escape(macro_text)+'</script:module>').encode()
 payload=[(standard.parent/'script.xlc',stable(templates/'profile-proof-script.xlc')[0]),(standard/'script.xlb',stable(templates/'profile-proof-Standard-script.xlb')[0]),(standard/'Module1.xba',module),(registry,reg_after)]
 prepared=[];before=[]
 def guard(p):
  need(p.is_relative_to(stage),'outside own stage')
  for d in (p.parent,*p.parent.parents):
   if not d.is_relative_to(stage):break
   ds=d.lstat();need(stat.S_ISDIR(ds.st_mode) and ds.st_uid==os.getuid() and not ds.st_mode&0o022,'unsafe own profile parent')
 try:
  for dest,raw in payload:
   guard(dest);_,identity=stable(dest);ET.fromstring(raw)
   fd,temp=tempfile.mkstemp(prefix='.frw-trusted-',dir=dest.parent)
   with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   prepared.append((Path(temp),dest,raw,identity));before.append(dict(path=str(dest),identity=identity))
  for temp,dest,raw,identity in prepared:
   guard(dest);need(stable(dest)[1]==identity,'initialized profile file changed');os.replace(temp,dest)
  for _,dest,raw,_ in prepared:need(stable(dest)[0]==raw,'prepared profile payload changed')
 finally:
  for temp,_,_,_ in prepared:
   if temp.exists():temp.unlink()
 return dict(state='OWN_FOUR_FILE_PROFILE_PREPARED_PRESERVING_INITIALIZATION',before=before,registry_before_sha256=hashlib.sha256(reg_before).hexdigest(),registry_after_sha256=hashlib.sha256(reg_after).hexdigest(),ooSetupInstCompleted=True,MacroSecurityLevel=0,all_other_registry_metadata_preserved=True)
