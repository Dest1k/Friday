"""F06 pure finite-operation contract. Import has no live effects."""
import datetime, hashlib, json, os, re, stat, time, types
from pathlib import Path
B=Path(__file__).resolve().parent
ASSIGNMENT='ASTRA-NATIVE-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112#1'
BASE=Path('/home/jericho/.jericho/toolchains/libreofficedev-26.2.5.2-frw-b711-c459-direct-20261111')
MANIFEST=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json')
MANIFEST_SHA='cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776'
PRIOR=Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-APP-ROOT-FRAME-PREP-20261111/BANK-PHYSICAL-INTEGRITY.json')
PRIOR_SHA='7135caf77a9c2ae4de2c12b37a8b327cab2065e76ed87e36f675b5d95528a35c'
PREFIX='/opt/friday-document-toolchain'
PROGRAM=PREFIX+'/root/usr/lib/libreoffice/program'
STAGE='/work'
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
IDENTITY_FIELDS=('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
DEADLINE=None
CPU_GUARD=None
FORMATS=('ott',)
PROFILES=('own_synthetic_odf13_aes256cbc_pbkdf2sha1_4096',)
NAMES=('retained-source.ott',)
LIMITS=dict(whole_wall_seconds=300,aggregate_CPU_seconds=180,memory_bytes=2147483648,swap_bytes=0,affinity_cpus=2,pids_max=128,namespace_tmpfs_bytes=16777216,own_cap_bytes=100663296,cleanup_reserve_seconds=15,per_process_AS_bytes=2147483648,per_process_FSIZE_bytes=8388608,max_Office_starts=3,max_stores=0,max_password_probes=1,max_document_loads=1,max_getRequest_calls=1,max_metadata_bytes=32768)
MOSCOW=datetime.timezone(datetime.timedelta(hours=3))


MODE='one-template-diagnostic'
TASK=Path(__file__).resolve().parent.parent
CACHE=Path('/home/jericho/.cache')
TASK_CAP=128*1024**2
MANDATORY_SOURCES={'f06_contract.py','root_frame.py','run_once.py','inside_once.py','embedded_entry.py','diagnostic_client.py','root_entry.py','readonly_diagnostic.py','conversion_probe.py','request_args_compat_v2.py','callback_observer_v2.py','ROOT-BINDINGS.TEMPLATE.json'}
SELECTED_ID='template-ott-source'
SELECTED_SHA='61c72a4b14ce2a83677acce3b267fb00aeb773e7dc74ffd448a449bd5dfb4650'
ORIGINAL18_PATH=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-TEMPLATE-RETAINED-OFFICE-EXECUTION-20261112/ROOT-FINAL-PARTIAL-AND-CLOSURE.json')
ORIGINAL18_SHA='adfafd005b85e57b00d60f3fd9d82fea595b31cf8812cac3bbd9ba6d9e898f6e'
TASK24_FREEZE_SHA='d68090a8d60879e948ffb2cf105f80f520ff1a1a07f30d29f988346bea671971'
TASK25_FREEZE_SHA='dc7eaf4385616ec5d4a6bd6b13e97a5795e34ccfbdc254943a1621b694db14b1'
TASK27_FREEZE_SHA='305d16593f582bcce419f13efb9bd97c2524c2c4c893aaf4437bca5e0dbb3e28'
PREVIOUS_CLASS1_SUMMARY_SHA='176f65237a6416f0950bd18a5f366a5e3cc1262842058f18e5b2cbc7b3614f9b'
OPERATION_KEY='one-template-post-args-compat1'
POSTCHANGE_PURPOSE='ONE_MISSING_POST_ARGS_NORMAL_PAYLOAD_AND_READONLY_LOAD'
LIBRARY_SHA256={'callback_observer_v2.py': '746846c1ab7c8e19585ed9d51a303b88ebbd41ce31ebee98614e056efc34e967', 'conversion_probe.py': 'bb556abab6aecde55d61e8f7372fdba980303daabeaae322b40f7e152d3ab1f5', 'diagnostic_client.py': '5c8de29ece89b5f57435f3a40746223dea49c5582be50c9f3fcf8b376d218a9d', 'readonly_diagnostic.py': 'de112168cc22f635e08eb43b97a62b6b5d14add24a2e755f9a515010162656cf', 'request_args_compat_v2.py': '23a2d996d7ee940b4a8a07140867e8e50e57b24859b18884872781ac40e1fc18'}
PRE_STAGE_CREDENTIAL_PATHS=set()
REF_KEYS={'path','sha256','bytes','identity','uid','gid','mode','dev','ino','nlink','mtime_ns','ctime_ns'}
FLAT_KEYS={'uid':'st_uid','gid':'st_gid','dev':'st_dev','ino':'st_ino','nlink':'st_nlink','mtime_ns':'st_mtime_ns','ctime_ns':'st_ctime_ns'}

def limits(mode):
 need(mode==MODE,'MODE');return dict(LIMITS)

def operation(key,mode):
 limits(mode)
 need(type(key)is str and key==OPERATION_KEY,'OPERATION_KEY')
 return B/'operations'/key

def unit_name(key):
 operation(key,MODE)
 return 'frw-astra-f06-'+key+'-20261112.service'

def decode(raw):
 def pairs(items):
  out={}
  for key,value in items:need(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'JSON_CONSTANT'))

def exact_json(a,b):
 return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))

def canonical(path):
 need(type(path)is str,'PATH_TYPE');p=Path(path)
 need(p.is_absolute() and str(p)==path and '..' not in p.parts and p.resolve(strict=True)==p,'PATH_CANONICAL')
 return p

def protected_parents(path):
 for parent in (path.parent,*path.parent.parents):
  if parent==CACHE:return
  safe_dir(parent)
 need(False,'PRIVATE_CACHE_ANCHOR')

def reference_shape(ref):
 need(type(ref)is dict and {'path','bytes','sha256'}<=set(ref)<=REF_KEYS,'REFERENCE_SHAPE')
 need(type(ref['bytes'])is int and 0<ref['bytes']<=8*1024**2 and type(ref['sha256'])is str and re.fullmatch('[0-9a-f]{64}',ref['sha256'])is not None,'REFERENCE_DIGEST')

def declared_metadata(ref,info):
 if 'identity'in ref:need(type(ref['identity'])is list and len(ref['identity'])==len(IDENTITY_FIELDS) and all(type(v)is int for v in ref['identity']) and ref['identity']==identity(info),'REFERENCE_IDENTITY')
 for key,field in FLAT_KEYS.items():
  if key in ref:need(type(ref[key])is int and ref[key]==getattr(info,field),'REFERENCE_FLAT_IDENTITY')
 if 'mode'in ref:need(ref['mode']=='0600','REFERENCE_MODE')

def credential_metadata(ref):
 # Root supplies this frozen digest after independent protected custody. No
 # secret body read by preparation or entry; only admitted unit stages it.
 full_pin_shape(ref)
 need(0<ref['bytes']<=4096,'CREDENTIAL_METADATA_SIZE')
 path=canonical(ref['path']);protected_parents(path);info=path.lstat()
 need(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1,'CREDENTIAL_METADATA_CUSTODY')
 declared_metadata(ref,info);need(info.st_size==ref['bytes'],'CREDENTIAL_METADATA_BYTES')
 return dict(ref),identity(info)


def reference_read(ref,forbidden=(),limit=8*1024**2):
 reference_shape(ref);path=canonical(ref['path']);need(str(path)not in set(forbidden)|PRE_STAGE_CREDENTIAL_PATHS,'CREDENTIAL_CONTENT_READ_FORBIDDEN')
 protected_parents(path)
 raw,pin=private(path,path.parent)
 need(pin['bytes']<=limit and all(pin[k]==ref[k]for k in ('path','bytes','sha256')),'REFERENCE_PIN')
 declared_metadata(ref,path.lstat())
 need(pin['identity']==identity(path.lstat()),'REFERENCE_AFTER_METADATA_CAS')
 return raw,pin

def recipe_check():
 raw,pin=private(B/'SOURCE-PINS.json',B);obj=decode(raw)
 need(obj.get('schema')=='friday.f06.one-template-post-args-compat-source.v1' and obj.get('state')=='SOURCE_ONLY_DORMANT' and obj.get('assignment')==ASSIGNMENT and obj.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA,'SOURCE_SCHEMA')
 source_set=obj.get('source_set');need(type(source_set)is list and source_set==sorted(set(source_set)) and MANDATORY_SOURCES<=set(source_set),'SOURCE_SET')
 rows=obj.get('files');need(type(rows)is list and [r.get('name')for r in rows]==source_set,'SOURCE_ROWS')
 need({row['name']:row['sha256'] for row in rows if row.get('name') in LIBRARY_SHA256}==LIBRARY_SHA256,'EXACT_TASK27_LIBRARY_PAIR_AND_CARRIES')
 need({p.name for p in B.glob('*.py')}=={name for name in source_set if name.endswith('.py')},'SOURCE_PYTHON_INVENTORY')
 actual=[]
 for row in rows:
  name=row['name'];need(type(name)is str and Path(name).name==name and name!='SOURCE-PINS.json','SOURCE_NAME')
  _,p=private(B/name,B);need(all(p[k]==row[k]for k in ('bytes','sha256')),'SOURCE_DRIFT');actual.append(p)
 refs=decode(private(B/'REFERENCES.json',B)[0]);need(type(refs.get('files'))is list,'REFERENCE_SET')
 for row in refs['files']:reference_read(row)
 return pin,actual

def runtime_pin_check(row):
 raw,p=reference_read(row);return decode(raw),p

def full_pin_shape(ref):
 reference_shape(ref)
 need(set(ref)=={'path','bytes','sha256','identity'},'FULL_PIN_REQUIRED')
 ident=ref['identity']
 need(type(ident)is list and len(ident)==9 and all(type(v)is int for v in ident),'FULL_IDENTITY_SHAPE')
 need(stat.S_ISREG(ident[2]) and stat.S_IMODE(ident[2])==0o600 and ident[3]==os.getuid() and ident[5]==1 and ident[6]==ref['bytes'],'FULL_PIN_CUSTODY')


def manifest_contract(manifest):
 need(type(manifest)is dict and set(manifest)=={'schema','state','assignment','selected_count','selected_fixture_ids','expected_Office_stores','expected_Office_password_probes','whole_F06_accepted','as_template','credential','fixtures'},'SELECTED_MANIFEST_FIELDS')
 need(manifest['schema']=='friday.f06.one-template-selected.v1' and manifest['state']=='ROOT_BOUND_RETAINED_METADATA_NOT_EXECUTION_AUTHORITY' and manifest['assignment']==ASSIGNMENT,'SELECTED_MANIFEST_SCHEMA')
 need(type(manifest['selected_count'])is int and manifest['selected_count']==1 and manifest['selected_fixture_ids']==[SELECTED_ID],'SELECTED_SINGLE_ID')
 need(type(manifest['expected_Office_stores'])is int and manifest['expected_Office_stores']==0 and type(manifest['expected_Office_password_probes'])is int and manifest['expected_Office_password_probes']==1 and manifest['whole_F06_accepted']is False and manifest['as_template']is False,'SELECTED_EFFECT_SCOPE')
 full_pin_shape(manifest['credential'])
 rows=manifest['fixtures'];need(type(rows)is list and len(rows)==1 and type(rows[0])is dict,'SELECTED_ONE_ROW')
 row=rows[0]
 need(set(row)=={'path','bytes','sha256','identity','fixture_id','format','role','fixture_profile','semantic','mime','service','filter','staged_name','native_source_ciphertext'},'SELECTED_ROW_FIELDS')
 full_pin_shape({k:row[k]for k in ('path','bytes','sha256','identity')})
 need(row['fixture_id']==SELECTED_ID and row['format']=='ott' and row['role']=='source' and row['fixture_profile']==PROFILES[0] and row['semantic']=='BEFORE' and row['mime']=='application/vnd.oasis.opendocument.text-template' and row['service']=='com.sun.star.text.TextDocument' and row['filter']=='writer8_template' and row['staged_name']==NAMES[0],'SELECTED_TYPED_ROW')
 need(row['sha256']==SELECTED_SHA and row['bytes']==4624 and exact_json(row['native_source_ciphertext'],{k:row[k]for k in ('path','bytes','sha256','identity')}),'SELECTED_ORIGINAL_CIPHER_PIN')
 need(row['path']!=manifest['credential']['path'],'SECRET_CIPHER_PATH_ALIAS')
 return row


def diagnostic_acceptance(a):
 # Immutable original18 closure remains PARTIAL, source review is not authority.
 for name in ('original18_closure','source_review','runtime_authority','fresh_boundary'):full_pin_shape(a[name])
 original,pin=runtime_pin_check(a['original18_closure'])
 need(pin['path']==str(ORIGINAL18_PATH) and pin['sha256']==ORIGINAL18_SHA,'ORIGINAL18_EXACT_CLOSURE')
 review,_=runtime_pin_check(a['source_review'])
 need(review.get('state')=='ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE' and review.get('execution_authority')is False and review.get('source_pins_sha256')==a['source_pins_sha256'] and review.get('task24_freeze_sha256')==TASK24_FREEZE_SHA and review.get('task25_sourcefreeze_sha256')==TASK25_FREEZE_SHA and review.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA and review.get('previous_class1_summary_sha256')==PREVIOUS_CLASS1_SUMMARY_SHA and review.get('postchange_purpose')==POSTCHANGE_PURPOSE and review.get('findings_remaining')==[],'ROOT_SOURCE_REVIEW')
 authority,_=runtime_pin_check(a['runtime_authority'])
 need(authority.get('state')=='ROOT_GRANTED_ONE_POST_ARGS_COMPAT_QUALIFICATION' and authority.get('assignment')==ASSIGNMENT and authority.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA and authority.get('previous_class1_summary_sha256')==PREVIOUS_CLASS1_SUMMARY_SHA and authority.get('postchange_purpose')==POSTCHANGE_PURPOSE and authority.get('operation_key')==a['operation_key'] and authority.get('source_pins_sha256')==a['source_pins_sha256'] and authority.get('selected_manifest')==a['output_manifest'] and authority.get('source_review')==a['source_review'] and authority.get('original18_closure')==a['original18_closure'] and authority.get('fresh_boundary')==a['fresh_boundary'],'ROOT_RUNTIME_EXACT_JOINS')
 need(authority.get('original18_replayed')is False and authority.get('previous_class1_replayed')is False and authority.get('actual_normal_payload_type_before')=='UNKNOWN' and authority.get('original_strict_all_pass')is False and authority.get('whole_F06_accepted')is False and type(authority.get('max_document_loads'))is int and authority['max_document_loads']==1 and type(authority.get('max_getRequest_calls'))is int and authority['max_getRequest_calls']==1 and type(authority.get('stores'))is int and authority['stores']==0 and authority.get('correct_password_only')is True and authority.get('limits')==limits(MODE),'ROOT_SINGLE_OBSERVATION_AUTHORITY')
 need(authority.get('boot_id')==a['boot_id'] and authority.get('nonce')==a['nonce'] and authority.get('original_operation_start_monotonic')==a['original_operation_start_monotonic'],'ROOT_AUTHORITY_CURRENT_CLOCK_SCOPE')
 return review,authority


def output_inputs(a):
 need(a.get('mode')==MODE and a.get('selected_fixture_ids')==[SELECTED_ID] and type(a.get('selected_count'))is int and a['selected_count']==1 and type(a.get('expected_probes'))is int and a['expected_probes']==1 and type(a.get('expected_stores'))is int and a['expected_stores']==0,'SINGLE_DIAGNOSTIC_SELECTION')
 credential,credential_id=credential_metadata(a['credential_source']);PRE_STAGE_CREDENTIAL_PATHS.add(credential['path'])
 need(a['credential_source_identity']==credential_id,'CREDENTIAL_ADMISSION_IDENTITY')
 full_pin_shape(a['output_manifest'])
 raw,manifest_pin=reference_read(a['output_manifest'],{credential['path']});manifest=decode(raw)
 row=manifest_contract(manifest);need(manifest['credential']==credential,'SELECTED_CREDENTIAL_JOIN')
 pinref={k:row[k]for k in ('path','bytes','sha256','identity')}
 _,pin=reference_read(pinref,{credential['path']},1000000)
 need(credential_metadata(credential)[1]==credential_id,'CREDENTIAL_METADATA_AFTER_CAS')
 return manifest,manifest_pin,[{**pin,'fixture_id':SELECTED_ID,'native_source_ciphertext':dict(pin)}],credential


def retention_snapshot(root,operation_path=None):
 root=Path(root);need(root==TASK,'TASK_RETENTION_EXACT_ROOT');safe_dir(root)
 total=0;own=0;entries=0
 for parent,dirs,files in os.walk(root,followlinks=False):
  within();entries+=1+len(dirs)+len(files);need(entries<=65536,'RETENTION_ENTRY_BOUND')
  for name in dirs:
   p=Path(parent)/name;info=p.lstat();need(stat.S_ISDIR(info.st_mode) and not p.is_symlink(),'RETENTION_DIRECTORY')
  for name in files:
   p=Path(parent)/name;info=p.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid(),'RETENTION_FILE_CUSTODY');total+=info.st_size
   if operation_path is not None and p.is_relative_to(operation_path):own+=info.st_size
   need(total<=TASK_CAP and own<=LIMITS['own_cap_bytes'],'RETENTION_BYTES')
 return dict(task_root=str(root),task_bytes=total,task_cap_bytes=TASK_CAP,operation_bytes=own,operation_cap_bytes=LIMITS['own_cap_bytes'],claim='CURRENT_LOGICAL_BYTES_NOT_RESERVED_QUOTA')

def utcmoscow():return datetime.datetime.now(MOSCOW).isoformat()



def need(value, code):
    if not value:
        raise ValueError(code)

def within(reserve=0):
    if CPU_GUARD is not None:CPU_GUARD()
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


def bwrap(work,inputs,mode,key,origin,nonce):
 operation(key,mode)
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
 safe_dir(inputs);cmd+=['--ro-bind',str(inputs),'/inputs']
 cmd+=['--chdir','/work','--remount-ro','/']
 env=dict(PATH='/usr/bin:/bin',HOME='/work/home',TMPDIR='/work/tmp',LANG='C.UTF-8',LC_ALL='C.UTF-8',SAL_USE_VCLPLUGIN='svp',XDG_CACHE_HOME='/work/cache',XDG_CONFIG_HOME='/work/config',XDG_RUNTIME_DIR='/work/runtime',FRW_F06_MODE=mode,FRW_F06_KEY=key,FRW_F06_NONCE=nonce,FRW_F06_UNIT_START=str(origin))
 for k,v in env.items():cmd+=['--setenv',k,v]
 return cmd+['--','/usr/bin/python3','-I','-B','-S','/recipe/inside_once.py']
