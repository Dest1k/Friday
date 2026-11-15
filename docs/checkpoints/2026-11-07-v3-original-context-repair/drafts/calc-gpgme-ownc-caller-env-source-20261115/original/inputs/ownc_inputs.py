"""Own-C metadata construction only. No execution, subprocess or process discovery.

All ELF parsing below reads files as data; no loader, target or tool is invoked.
Runtime operation IDs, nonce, clocks and process identities remain unbound.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import struct

BASE = Path(__file__).resolve().parents[1]
REVIEWED = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115')
DEPS = REVIEWED / 'candidate/outer/deps'
PREP = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-REAL-OWNC-QUALIFICATION-PREP-20261115')
WORK = '/tmp/friday-metric-work'
MARKERS = ('fixture_ready', 'fixture_paper_done', 'fixture_after_load', 'fixture_query_marker',
           'fixture_restore_marker', 'fixture_close_marker', 'fixture_after_close')
ENV = {'HOME':WORK+'/tmp','TMPDIR':WORK+'/tmp','XDG_CACHE_HOME':WORK+'/cache',
       'XDG_CONFIG_HOME':WORK+'/config','XDG_RUNTIME_DIR':WORK+'/runtime',
       'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PATH':'/usr/bin:/bin','SAL_USE_VCLPLUGIN':'svp',
       'LD_LIBRARY_PATH':'/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115/python-uno-binding/root/usr/lib/libreoffice/program:/opt/friday-document-toolchain/root/usr/lib/libreoffice/program:/opt/friday-document-toolchain/root/usr/lib/x86_64-linux-gnu',
       'URE_BOOTSTRAP':'vnd.sun.star.pathname:/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/fundamentalrc',
       'PYTHONDONTWRITEBYTECODE':'1','DEBUGINFOD_URLS':''}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def ref(path):
    path=Path(path)
    need(path.is_absolute() and path.resolve()==path,'source_ref_alias')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_uid in (0,os.getuid())
             and not before.st_mode&0o022 and before.st_size<=32*1024*1024,'source_ref_rights')
        with os.fdopen(os.dup(fd),'rb') as stream: raw=stream.read(32*1024*1024+1)
        stamp=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_uid,s.st_mode,s.st_nlink)
        need(stamp(before)==stamp(os.fstat(fd))==stamp(path.lstat()),'source_ref_cas')
    finally: os.close(fd)
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}


def put(path,value):
    path=Path(path); raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f: f.write(raw); f.flush();os.fsync(f.fileno())
    return ref(path)


class ELF:
    """Bounded little-endian ELF64 x86-64 metadata reader, never dlopen."""
    def __init__(self,path):
        self.path=Path(path); self.ref=ref(self.path);self.raw=self.path.read_bytes()
        need(hashlib.sha256(self.raw).hexdigest()==self.ref['sha256'],'elf_read_cas')
        h=struct.unpack_from('<16sHHIQQQIHHHHHH',self.raw)
        need(h[0][:6]==b'\x7fELF\x02\x01' and h[1] in (2,3) and h[2]==62 and h[9]==56
             and h[11]==64 and 0<h[10]<256 and 0<h[12]<256,'elf_supported')
        self.entry=h[4];self.etype=h[1];self.ph=[struct.unpack_from('<IIQQQQQQ',self.raw,h[5]+i*h[9]) for i in range(h[10])]
        self.origin=min(p[3]-p[2] for p in self.ph if p[0]==1) if self.etype==2 else 0
        sections=[struct.unpack_from('<IIQQQQIIQQ',self.raw,h[6]+i*h[11]) for i in range(h[12])]
        names=sections[h[13]];strtab=self.raw[names[4]:names[4]+names[5]]
        self.sections={self.cstr(strtab,s[0]):s for s in sections};self.symbols={}
        for s in sections:
            if s[1] not in (2,11):continue
            need(s[9]==24 and s[5]%24==0,'elf_symbol_layout')
            strings=sections[s[6]]; strings=self.raw[strings[4]:strings[4]+strings[5]]
            for i in range(s[5]//24):
                name,info,other,ndx,value,size=struct.unpack_from('<IBBHQQ',self.raw,s[4]+i*24)
                name=self.cstr(strings,name)
                if name and ndx:self.symbols[name]=(value,size,info&15)
        self.build_id=None
        for s in sections:
            if s[1]!=7:continue
            raw=self.raw[s[4]:s[4]+s[5]];off=0
            while off+12<=len(raw):
                nl,dl,kind=struct.unpack_from('<III',raw,off);off+=12
                name=raw[off:off+nl];off+=(nl+3)&~3
                desc=raw[off:off+dl];off+=(dl+3)&~3
                if kind==3 and name==b'GNU\0':self.build_id=desc.hex()
        self.needed=[]
        for s in sections:
            if s[1]!=6:continue
            strings=sections[s[6]]; strings=self.raw[strings[4]:strings[4]+strings[5]]
            for i in range(s[5]//16):
                tag,value=struct.unpack_from('<qQ',self.raw,s[4]+i*16)
                if tag==1:self.needed.append(self.cstr(strings,value))
        self.interpreter=None
        for p in self.ph:
            if p[0]==3:self.interpreter=self.raw[p[2]:p[2]+p[5]].rstrip(b'\0').decode('ascii')

    @staticmethod
    def cstr(raw,offset):
        end=raw.find(b'\0',offset);need(0<=offset<=end<len(raw),'elf_string_bound')
        return raw[offset:end].decode('ascii')

    def get(self,va,count):
        offsets=[p[2]+va-p[3] for p in self.ph if p[0]==1 and p[3]<=va and va+count<=p[3]+p[5]]
        need(len(offsets)==1 and 0<count<=8192,'elf_load_range');o=offsets[0]
        return self.raw[o:o+count]

    def plt(self):
        out={}; sections=list(self.sections.values())
        rela=self.sections.get('.rela.plt'); plt=self.sections.get('.plt.sec') or self.sections.get('.plt')
        need(rela is not None and plt is not None and rela[9]==24,'elf_plt_layout')
        # Resolve symbol table by matching linked section index, rather than assumptions.
        header=struct.unpack_from('<16sHHIQQQIHHHHHH',self.raw)
        dyn=struct.unpack_from('<IIQQQQIIQQ',self.raw,header[6]+rela[6]*64)
        strings=struct.unpack_from('<IIQQQQIIQQ',self.raw,header[6]+dyn[6]*64)
        strings=self.raw[strings[4]:strings[4]+strings[5]]
        for i in range(rela[5]//24):
            _,info,_=struct.unpack_from('<QQq',self.raw,rela[4]+i*24)
            name=struct.unpack_from('<I',self.raw,dyn[4]+(info>>32)*24)[0]
            stride=plt[9] or 16;skip=0 if '.plt.sec' in self.sections else 1
            out[self.cstr(strings,name)]=plt[3]+(i+skip)*stride
        return out

    def paper_caller(self):
        value,size,_=self.symbols['paper_load_fixture'];need(0<size<8192,'ownc_paper_function_bound')
        raw=self.get(value,size);plt=self.plt();sites={}
        for name in ('popen','fgets','pclose'):
            matches=[value+i+5 for i,b in enumerate(raw[:-4]) if b==0xe8 and
                     value+i+5+struct.unpack_from('<i',raw,i+1)[0]==plt[name]]
            need(len(matches)==1,'ownc_exact_call_'+name);ret=matches[0]
            sites[name+'_return']={'offset':ret-self.origin,'before':self.get(ret-5,5).hex(),'after':self.get(ret,8).hex()}
        return dict(self.ref,function_offset=value-self.origin,function_size=size,sites=sites)


def host_stamp(path):
    s=Path(path).stat()
    return dict(dev_major=os.major(s.st_dev),dev_minor=os.minor(s.st_dev),ino=s.st_ino,size=s.st_size,
                mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=s.st_mode,uid=s.st_uid,nlink=s.st_nlink)


def image(path):
    elf=ELF(Path(path).resolve());need(elf.build_id is not None,'elf_build_id_required')
    return dict(elf.ref,build_id=elf.build_id,host_stamp=host_stamp(elf.path))


def dependency_closure(path):
    queue=[Path(path).resolve()]; images={}
    while queue:
        current=queue.pop(0)
        if str(current) in images:continue
        elf=ELF(current);images[str(current)]=image(current)
        if elf.interpreter:queue.append(Path(elf.interpreter).resolve())
        for soname in elf.needed:
            need('/' not in soname,'elf_dependency_soname')
            candidates={p.resolve() for root in ('/usr/lib/x86_64-linux-gnu','/lib/x86_64-linux-gnu')
                        if (p:=Path(root)/soname).is_file()}
            need(len(candidates)==1,'elf_dependency_exact_resolution:'+soname);queue.extend(candidates)
    return [images[p] for p in sorted(images)]


def paper_manifest(source,target):
    m=json.loads((DEPS/'PAPER-HELPER-OFFICE-MANIFEST.json').read_bytes())
    m.update(kind='OWN_POPEN_FIXTURE_ONLY',source_sha256=ref(source)['sha256'],caller=ELF(target).paper_caller())
    return m


def gpgme_manifest():
    policy={};exec(compile((DEPS/'gpgme_engine_policy.py').read_bytes(),str(DEPS/'gpgme_engine_policy.py'),'exec'),policy)
    profile=dict(schema=policy['SCHEMA'],stage=policy['STAGE'],library=dict(path=policy['LIBRARY_PATH'],
        sha256=policy['LIBRARY_SHA256'],build_id=policy['BUILD_ID']),source_manifest_ref=policy['SOURCE_MANIFEST'],
        conditional_join_ref=policy['CONDITIONAL_JOIN'],branches=[dict(branch=b,role=policy['ROLES'][b],option=policy['OPTIONS'][b])
        for b in policy['BRANCHES']],pseudo_protocols=list(policy['UNSUPPORTED']),budgets=dict(wall_seconds=240,
        cpu_seconds=120,memory_bytes=2147483648,deadline_rule='SAME_ORIGINAL_ABSOLUTE_OPERATION_DEADLINE_NO_RESET'),runtime_available=False)
    helpers={}; deps={'original':dependency_closure(policy['LIBRARY_PATH'])}
    # g13 is absent on this host: do not invent a helper image or future branch.
    for role in ('gpgconf','gpg','gpgsm','g13'):
        p=Path('/usr/bin')/role
        if not p.exists():continue
        r=ref(p);s=p.stat();helpers[role]=dict(r,dev=s.st_dev,ino=s.st_ino);deps[role]=dependency_closure(p)
    pins=dict(operation=None,original=None,reaper=None,library=image(policy['LIBRARY_PATH']),
        libc=image('/usr/lib/x86_64-linux-gnu/libc.so.6'),environment=dict(ENV),cwd=WORK,
        absent_paths=['/etc/gnupg',WORK+'/tmp/.gnupg',WORK+'/config/gnupg',WORK+'/config/gpg',
                      WORK+'/config/gpgme'],private_roots=None,cgroup=None,uid_projection=None,dependencies=deps)
    return dict(schema='frw.calc.gpgme-engine-init-manifest.v2',profile=profile,collector_pins=pins,helpers=helpers,source_mode='COLD_GPGCONF')
