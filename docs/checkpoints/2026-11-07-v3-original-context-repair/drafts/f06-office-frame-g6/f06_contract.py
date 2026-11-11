"""F06 pure finite-operation contract. Import has no live effects."""
import datetime, hashlib, json, os, re, stat, time
from pathlib import Path
B=Path(__file__).resolve().parent
ASSIGNMENT='ASTRA-F06-ROOT-OFFICE-GENERATION-FRAME-20261111#1'
P=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ENCRYPTED-INPUTS-PREP-20261111')
BASE=Path('/home/jericho/.jericho/toolchains/libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111')
MANIFEST=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')
MANIFEST_SHA='cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'
PRIOR=Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-APP-ROOT-FRAME-PREP-20261111/BANK-PHYSICAL-INTEGRITY.json')
PRIOR_SHA='7135caf77a9c2ae4de2c12b37a8b327cab2065e76ed87e36f675b5d95528a35c'
PLAIN_SHA='b78a2a3e0004ec6a00fff293a18427427dde88ea47cda17d46e3233698310a8d'
PREFIX='/opt/friday-document-toolchain'
PROGRAM=PREFIX+'/root/usr/lib/libreoffice/program'
STAGE='/work'
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
IDENTITY_FIELDS=('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
DEADLINE=None
FORMATS=('docx','xlsx','pptx','odt','ods','odp')
PROFILES=('compatible1.3_or_Agile',)*6+('current_default_latest_odt_negative',)
NAMES=tuple('f06-new-encrypted.'+f for f in FORMATS)+('f06-new-default-latest.odt',)
LIMITS=dict(whole_wall_seconds=300,aggregate_CPU_seconds=180,memory_bytes=2147483648,swap_bytes=0,affinity_cpus=2,pids_max=128,namespace_tmpfs_bytes=16777216,own_cap_bytes=100663296,cleanup_reserve_seconds=15,per_process_AS_bytes=2147483648,per_process_FSIZE_bytes=8388608,max_Office_starts=3,max_stores=7,max_password_probes=21)
PREFLIGHT_LIMITS={**LIMITS,'whole_wall_seconds':30,'aggregate_CPU_seconds':20,'cleanup_reserve_seconds':6,'max_Office_starts':0,'max_stores':0,'max_password_probes':0}
MOSCOW=datetime.timezone(datetime.timedelta(hours=3))

def limits(mode):
 need(mode in ('preflight','generate','verify-inputs'),'MODE')
 return PREFLIGHT_LIMITS if mode=='preflight' else LIMITS

def utcmoscow():return datetime.datetime.now(MOSCOW).isoformat()

def operation(key,mode):
 need((mode=='preflight' and key=='preflight-g1') or (mode=='generate' and key=='generate-g6') or (mode=='verify-inputs' and re.fullmatch('verify-inputs-[a-z0-9]{1,32}',key) is not None),'OPERATION_KEY')
 return B/'operations'/key

def unit_name(key):
 need(re.fullmatch('[a-z0-9-]{1,48}',key),'UNIT_KEY')
 return 'frw-astra-f06-'+key+'-20261111.service'

def need(value, code):
    if not value:
        raise ValueError(code)

def within(reserve=0):
    need(DEADLINE is None or time.monotonic() < DEADLINE - reserve, 'WHOLE_WALL_DEADLINE')

def identity(info):
    return [getattr(info, key) for key in IDENTITY_FIELDS]

def stable(path, limit=8*1024**2, own=True):
    within()
    path = Path(path)
    need(path.is_absolute() and not any(q.is_symlink() for q in (path, *path.parents)), 'PATH_LINK')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= limit, 'FILE_BOUNDARY')
        need(before.st_uid == (os.getuid() if own else 0), 'FILE_OWNER')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(limit+1)
        need(identity(before) == identity(os.fstat(fd)) == identity(path.lstat()) and len(raw) == before.st_size, 'FILE_CHANGED')
    finally:
        os.close(fd)
    within()
    return raw, dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), identity=identity(before))

def save(path, value):
    raw = (json.dumps(value, ensure_ascii=True, indent=2)+'\n').encode()
    need(len(raw) <= 4*1024**2, 'REPORT_LIMIT')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    parent = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)

def safe_dir(path):
    path = Path(path)
    need(path.is_absolute() and not any(q.is_symlink() for q in (path, *path.parents)), 'DIRECTORY_LINK')
    info = path.lstat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'DIRECTORY_BOUNDARY')
    return path

def private(path,root):
 path=Path(path);root=safe_dir(root)
 need(path.is_relative_to(root),'PRIVATE_SCOPE')
 for q in path.parents:
  safe_dir(q)
  if q==root:break
 raw,pin=stable(path)
 need(stat.S_IMODE(pin['identity'][2])==0o600,'PRIVATE_MODE')
 return raw,pin

def recipe_check():
 raw,pin=stable(B/'SOURCE-PINS.json');obj=json.loads(raw);seen=set();actual=[]
 for row in obj['files']:
  name=row['name'];need(Path(name).name==name and name not in seen,'SOURCE_NAME');seen.add(name)
  _,actualpin=private(B/name,B);need(all(actualpin[k]==row[k] for k in ('bytes','sha256')),'SOURCE_DRIFT');actual.append(actualpin)
 need(seen=={'f06_contract.py','root_frame.py','run_once.py','inside_once.py','embedded_entry.py','office_fixture_driver.py','office_fixture_driver.original.py','REFERENCES.json','REQUEST.json','source_controls.py','source_check.py'},'SOURCE_SET')
 refs=json.loads(stable(B/'REFERENCES.json')[0])
 for row in refs['files']:
  _,p=stable(row['path'],limit=8*1024**2);need(all(p[k]==row[k] for k in ('bytes','sha256')),'FROZEN_REFERENCE_DRIFT')
 return pin,actual

def plain_inputs():
 raw,pin=private(P/'PLAIN-INPUTS.json',P);need(pin['sha256']==PLAIN_SHA,'PLAIN_MANIFEST_SHA')
 obj=json.loads(raw);need(tuple(r['format'] for r in obj['fixtures'])==FORMATS,'PLAIN_SIX_ORDER')
 rows=[]
 for row in obj['fixtures']:
  path=P/'plain-inputs'/('f06-new-plain.'+row['format']);need(row['path']==str(path),'PLAIN_EXACT_PATH')
  _,p=private(path,P);need(all(p[k]==row[k] for k in ('bytes','sha256')),'PLAIN_SOURCE_SHA');rows.append(p)
 refraw,refpin=private(P/'CREDENTIAL-REF.json',P);ref=json.loads(refraw)
 need(ref.get('owner_uid')==os.getuid() and ref.get('mode')=='0o600' and ref.get('synthetic') is True and ref.get('secret_stdout_or_argv') is False,'CREDENTIAL_REF_SCHEMA')
 secret=Path(ref['path']);need(secret.is_relative_to(P) and secret.is_absolute() and '..' not in secret.parts,'CREDENTIAL_REF_PATH')
 # Do not read the secret in source checks. Root reads exact private bytes only
 # after admission and records a hash/identity, never content.
 return obj,pin,rows,ref,refpin

def reconciled_inputs(raw,pin):
 obj=json.loads(raw);rows=obj.get('fixtures',[])
 need(obj.get('schema')=='friday.f06.reconciled-existing-inputs.v1' and obj.get('semantic')=='ALPHA17','RECONCILE_SCHEMA')
 need(type(obj.get('known_prefix_count')) is int and obj['known_prefix_count']==len(rows) and 1<=len(rows)<=7,'RECONCILE_PREFIX')
 custody=operation('generate-g6','generate')/'work'/'encrypted-inputs'
 need(obj.get('custody_root')==str(custody),'RECONCILE_ORIGINAL_CUSTODY')
 safe_dir(custody);actual=[]
 for i,row in enumerate(rows):
  fmt=FORMATS[i] if i<6 else 'odt';name=NAMES[i]
  need(row.get('format')==fmt and row.get('name')==name and row.get('fixture_profile')==PROFILES[i] and row.get('path')==str(custody/name),'RECONCILE_EXACT_FAMILY_PATH_PROFILE')
  _,p=private(custody/name,custody);need(all(p[k]==row[k] for k in ('bytes','sha256','identity')),'RECONCILE_EXISTING_BYTES_IDENTITY');actual.append(p)
 # Known partial prefixes may retain RESULT/CUSTODY/oracle files; no unlisted
 # encrypted fixture, link or extra attempted later document is silently ignored.
 for path in custody.iterdir():
  need(path.name in set(NAMES[:len(rows)])|{'RESULT.json','CUSTODY.json'},'RECONCILE_UNBOUND_OUTPUT')
 return obj,actual

def bank_snapshot():
 raw,mpin=stable(MANIFEST);need(mpin['sha256']==MANIFEST_SHA,'BANK_MANIFEST')
 manifest=json.loads(raw);oldraw,oldpin=stable(PRIOR,limit=8*1024**2);need(oldpin['sha256']==PRIOR_SHA,'BANK_PRIOR_SHA');old=json.loads(oldraw)
 need(old['state']=='ALL_5116_SHA_PLUS_427_DIRECTORIES_282_EXACT_LINKS_VERIFIED_READONLY' and old['bank_manifest_sha256']==MANIFEST_SHA and old['bank_root']==str(BASE),'BANK_PRIOR_SCOPE')
 need(len(manifest['files'])==5116 and manifest['regular_bytes']==779553147 and len(manifest['directories'])==427 and len(manifest['symlinks'])==282,'BANK_INVENTORY')
 expected=set();rows=[]
 for kind,key in (('file','files'),('symlink','symlinks'),('directory','directories')):
  for item in manifest[key]:
   within();path=BASE/item['relative'];need(path.is_relative_to(BASE) and '..' not in Path(item['relative']).parts,'BANK_PATH')
   info=path.lstat();need(info.st_uid==item['uid'],'BANK_OWNER')
   if kind=='file':need(stat.S_ISREG(info.st_mode) and info.st_nlink==item['nlink'] and info.st_size==item['bytes'] and stat.S_IMODE(info.st_mode)==int(item['mode'],8),'BANK_FILE_METADATA')
   elif kind=='directory':need(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==int(item['mode'],8),'BANK_DIRECTORY')
   else:need(stat.S_ISLNK(info.st_mode) and os.readlink(path)==item['target'],'BANK_LINK')
   rows.append(dict(relative=item['relative'],kind=kind,identity=identity(info)));expected.add(item['relative'])
 actual=set()
 for directory,dirs,files in os.walk(BASE,followlinks=False):
  within()
  for name in dirs+files:
   actual.add(str((Path(directory)/name).relative_to(BASE)));need(len(actual)<=len(expected),'BANK_EXTRA')
 need(actual==expected and rows==old['bank_physical_rows'] and identity(BASE.lstat())==old['bank_root_identity'],'BANK_PRIOR_FULL_SHA_METADATA_ROOT_CAS')
 critical=[]
 for name in ('soffice.bin','libcomphelper.so','python','python.bin'):
  item=next(r for r in manifest['files'] if r['relative']=='root/usr/lib/libreoffice/program/'+name)
  _,p=stable(BASE/item['relative'],limit=64*1024**2);need(p['sha256']==item['sha256'],'BANK_CRITICAL_SHA');critical.append(p)
 return dict(bank_root=str(BASE),manifest=mpin,prior_full_SHA=oldpin,bank_root_identity=identity(BASE.lstat()),bank_physical_rows=rows,critical_four=critical,reused_full_SHA=True)

def runtime_pin_check(row):
 # Root chooses observations from kernel/source evidence; no canonical DB/HOME
 # reads are hidden in default arguments or implied by source-only check.
 raw,p=stable(row['path'],limit=8*1024**2);need(all(p[k]==row[k] for k in ('bytes','sha256','identity')),'ROOT_PROOF_PIN');return json.loads(raw),p

def bwrap(work,inputs,mode,key,origin,nonce):
 for path in (B,work):safe_dir(path)
 cmd=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session','--as-pid-1','--cap-drop','ALL','--clearenv','--ro-bind','/usr','/usr']
 for name in ('bin','sbin','lib','lib64'):
  path=Path('/')/name
  if path.exists():
   resolved=path.resolve();need(resolved.is_relative_to('/usr'),'HOST_ALIAS');cmd+=['--symlink',str(resolved),str(path)]
 cmd+=['--proc','/proc','--dev','/dev','--size',str(limits(mode)['namespace_tmpfs_bytes']),'--tmpfs','/tmp','--dir','/opt','--ro-bind',str(BASE),PREFIX,'--ro-bind','/usr/share',PREFIX+'/.host-share','--ro-bind',str(BASE/'share-merged'),'/usr/share','--dir','/etc']
 for name in ('/etc/fonts','/etc/ld.so.cache','/var/cache/fontconfig'):
  if Path(name).exists():cmd+=['--ro-bind',name,name]
 cmd+=['--ro-bind',str(B),'/recipe','--bind',str(work),'/work']
 if mode!='preflight':safe_dir(inputs);cmd+=['--ro-bind',str(inputs),'/inputs']
 cmd+=['--chdir','/work','--remount-ro','/']
 env=dict(PATH='/usr/bin:/bin',HOME='/work/home',TMPDIR='/work/tmp',LANG='C.UTF-8',LC_ALL='C.UTF-8',SAL_USE_VCLPLUGIN='svp',XDG_CACHE_HOME='/work/cache',XDG_CONFIG_HOME='/work/config',XDG_RUNTIME_DIR='/work/runtime',FRW_F06_MODE=mode,FRW_F06_KEY=key,FRW_F06_NONCE=nonce,FRW_F06_UNIT_START=str(origin))
 for k,v in env.items():cmd+=['--setenv',k,v]
 return cmd+['--','/usr/bin/python3','-I','-B','-S','/recipe/inside_once.py']
