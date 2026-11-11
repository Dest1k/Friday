"""F06 pure finite-operation contract. Import has no live effects."""
import datetime, hashlib, json, os, re, stat, time
from pathlib import Path
B=Path(__file__).resolve().parent
ASSIGNMENT='ASTRA-F06-RETAINED-INPUT-ORACLE-FRAME-20261112#1'
RETAINED_ASSIGNMENT='ASTRA-F06-ROOT-OFFICE-GENERATION-FRAME-20261111#1'
VERIFY_KEY='verify-inputs-g6-oracle1'
ORACLE_CODEC_STATE='ROOT_FINAL_CODEC_INTEGRATED'
CODEC_ACCEPTANCE_PATH=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-PASSWORD-ORACLE-CODEC-FINAL-SNAPSHOT-ACCEPTANCE.json')
CODEC_ACCEPTANCE_SHA='84db6c10fcd5ae8d44ea9b4770cdbef5d918ab92790edf4bd5a56ab1474af457'
ORIGINAL_ROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112')
ORIGINAL_CUSTODY=ORIGINAL_ROOT/'operations/generate-g6/work/encrypted-inputs'
ORIGINAL_SOURCE_SHA='d2bab5030b69ee678d7a452ec8c654e2cb22a7a6219ffb053612e0e1dcf781ab'
ORIGINAL_RESULT_SHA='b7af6f75780a4911f928aeb52080b348f1982422f0d4a202730acfea6a64c97c'
ORIGINAL_CUSTODY_SHA='7c776feb8b094d1e384d8595a5daa61e12ccfdd9d64285fc80f3241bb261dade'
ORIGINAL_CLOSURE_SHA='60882e5e301d4299a42dc82389d48f5d9776459761343d9aef99f786bc20a2e1'
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
LIMITS=dict(whole_wall_seconds=300,aggregate_CPU_seconds=180,memory_bytes=2147483648,swap_bytes=0,affinity_cpus=2,pids_max=128,namespace_tmpfs_bytes=16777216,own_cap_bytes=100663296,cleanup_reserve_seconds=15,per_process_AS_bytes=2147483648,per_process_FSIZE_bytes=8388608,max_Office_starts=3,max_stores=0,max_password_probes=21)
PREFLIGHT_LIMITS={**LIMITS,'whole_wall_seconds':30,'aggregate_CPU_seconds':20,'cleanup_reserve_seconds':6,'max_Office_starts':0,'max_stores':0,'max_password_probes':0}
MOSCOW=datetime.timezone(datetime.timedelta(hours=3))

def limits(mode):
 need(mode=='verify-inputs','VERIFY_INPUTS_ONLY_MODE')
 return dict(LIMITS)

def require_final_codec():
 need(ORACLE_CODEC_STATE=='ROOT_FINAL_CODEC_INTEGRATED','FINAL_ORACLE_CODEC_PENDING_ROOT')

def utcmoscow():return datetime.datetime.now(MOSCOW).isoformat()

def operation(key,mode):
 need(mode=='verify-inputs' and key==VERIFY_KEY,'EXACT_VERIFY_INPUTS_ONLY_OPERATION')
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

def credential_reference():
 # Metadata only here. Actual secret bytes are read only by admitted unit stage.
 refraw,refpin=private(P/'CREDENTIAL-REF.json',P);ref=json.loads(refraw)
 need(ref.get('owner_uid')==os.getuid() and ref.get('mode')=='0o600' and ref.get('synthetic') is True and ref.get('secret_stdout_or_argv') is False,'CREDENTIAL_REF_SCHEMA')
 secret=Path(ref['path']);need(secret.is_relative_to(P) and secret.is_absolute() and '..' not in secret.parts,'CREDENTIAL_REF_PATH')
 return ref,refpin

def codec_acceptance(row):
 need(isinstance(row,dict) and row.get('path')==str(CODEC_ACCEPTANCE_PATH) and row.get('sha256')==CODEC_ACCEPTANCE_SHA,'CODEC_EXACT_ROOT_ACCEPTANCE')
 raw,pin=private(CODEC_ACCEPTANCE_PATH,CODEC_ACCEPTANCE_PATH.parent);need(pin==row,'CODEC_ROOT_ACCEPTANCE_CAS');accepted=json.loads(raw)
 need(accepted['schema']=='friday.f06.Root-password-oracle-codec-acceptance.v1' and accepted['state']=='ROOT_ACCEPTED_TYPED_PASSWORD_ABORT_CODEC_SOURCE_AND_REPRESENTATIVE_CONTRAST','CODEC_ROOT_ACCEPTANCE_STATE')
 need(accepted['all_seven_profiles_qualified'] is False and accepted['raw_G6_false_promoted'] is False and accepted['original_effects_replayed'] is False and accepted['native_grant_issued'] is False and accepted['stores_or_generation_authorized'] is False,'CODEC_REPRESENTATIVE_SCOPE_ONLY')
 need(accepted['typed_negative_sequences_observed']==4 and accepted['correct_samebyte_semantics_observed']==2,'CODEC_REPRESENTATIVE_OBSERVATIONS')
 rows=list(accepted['helpers'].values())+[accepted['independent_review'],accepted['Root_source_delta_acceptance']]+list(accepted['actual_contrast'].values())
 for expected in rows:
  _,observed=private(expected['path'],Path(expected['path']).parent);need(observed==expected,'CODEC_LINKED_PROOF_CAS')
 return accepted

def reconciled_contract(obj):
 rows=obj.get('fixtures',[])
 need(obj.get('schema')=='friday.f06.reconciled-existing-inputs.v1' and obj.get('semantic')=='ALPHA17','RECONCILE_SCHEMA')
 need(type(obj.get('known_prefix_count')) is int and obj['known_prefix_count']==len(rows)==7,'RECONCILE_EXACT_SEVEN')
 need(obj.get('custody_root')==str(ORIGINAL_CUSTODY),'RECONCILE_ORIGINAL_CUSTODY')
 need(obj.get('original_source_pins_sha256')==ORIGINAL_SOURCE_SHA and obj.get('original_all_pass') is False and obj.get('original_clocks_reset') is False and obj.get('original_operation_replay') is False,'RECONCILE_G6_FAILURE_PRESERVED')
 need(obj.get('original_closure',{}).get('path')==str(ORIGINAL_ROOT/'operations/generate-g6/ROOT-G6-SEVEN-CIPHERTEXT-AND-CLOSURE.json') and obj['original_closure'].get('sha256')==ORIGINAL_CLOSURE_SHA,'RECONCILE_EXACT_G6_CLOSURE')
 for field,name,sha in (('original_oracle','RESULT.json',ORIGINAL_RESULT_SHA),('original_custody','CUSTODY.json',ORIGINAL_CUSTODY_SHA)):
  pin=obj.get(field,{})
  need(pin.get('path')==str(ORIGINAL_CUSTODY/name) and pin.get('sha256')==sha,'RECONCILE_RAW_G6_PIN')
 for i,row in enumerate(rows):
  fmt=FORMATS[i] if i<6 else 'odt';name=NAMES[i]
  need(row.get('format')==fmt and row.get('name')==name and row.get('fixture_profile')==PROFILES[i] and row.get('path')==str(ORIGINAL_CUSTODY/name) and row.get('raw_original_namespace_path')=='/work/encrypted-inputs/'+name,'RECONCILE_EXACT_FAMILY_PATH_PROFILE')
  need(type(row.get('bytes')) is int and 0<row['bytes']<=LIMITS['per_process_FSIZE_bytes'] and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) is not None and isinstance(row.get('identity'),list) and len(row['identity'])==9,'RECONCILE_PIN_SHAPE')
 return rows

def reconciled_inputs(raw,pin):
 obj=json.loads(raw);rows=reconciled_contract(obj);safe_dir(ORIGINAL_CUSTODY)
 # Link the new result to unchanged raw G6 FAIL, never rewrite the old result.
 observed={}
 for field in ('original_oracle','original_custody','original_closure'):
  expected=obj[field];root=ORIGINAL_ROOT
  data,p=private(expected['path'],root);need(p==expected,'RECONCILE_G6_METADATA_CAS');observed[field]=json.loads(data)
 old=observed['original_oracle'];closure=observed['original_closure']
 need([{k:r[k] for k in ('path','bytes','sha256','identity')} for r in rows]==closure['encrypted_files'],'RECONCILE_ORIGINAL_IDENTITY_JOIN')
 need(old['mode']=='produce' and old['whole_seven_covered'] is True and old['all_pass'] is False and len(old['rows'])==7,'RECONCILE_RAW_G6_FAIL')
 need(closure['state']=='G6_SEVEN_CREATED_KNOWN_CLOSED_ORACLE_CLASSIFICATION_FAIL_PRESERVED' and closure['source_pins_sha256']==ORIGINAL_SOURCE_SHA and closure['actual_root_parent_absent'] is True and closure['actual_unit_actors']==[] and closure['actual_shared_slot_reacquired_and_released'] is True and closure['stores_consumed']==7 and closure['password_probes_consumed']==21 and closure['oracle_all_pass'] is False,'RECONCILE_G6_KNOWN_CLOSED')
 need(closure['evidence']['work/encrypted-inputs/RESULT.json']==obj['original_oracle'] and closure['evidence']['work/encrypted-inputs/CUSTODY.json']==obj['original_custody'],'RECONCILE_CLOSURE_RAW_JOIN')
 need(tuple((r['name'],r['format'],r['fixture_profile'],r['path'],r['bytes'],r['sha256']) for r in observed['original_custody']['fixtures'])==tuple((r['name'],r['format'],r['fixture_profile'],r['raw_original_namespace_path'],r['bytes'],r['sha256']) for r in rows),'RECONCILE_CUSTODY_PROJECTION')
 actual=[]
 for row in rows:
  _,p=private(row['path'],ORIGINAL_CUSTODY);need(all(p[k]==row[k] for k in ('bytes','sha256','identity')),'RECONCILE_EXISTING_BYTES_IDENTITY');actual.append(p)
 need(set(path.name for path in ORIGINAL_CUSTODY.iterdir())==set(NAMES)|{'RESULT.json','CUSTODY.json'},'RECONCILE_UNBOUND_OUTPUT')
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
 operation(key,mode);require_final_codec()
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
