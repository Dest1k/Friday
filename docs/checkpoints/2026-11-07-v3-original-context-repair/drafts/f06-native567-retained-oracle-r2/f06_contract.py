"""F06 pure finite-operation contract. Import has no live effects."""
import datetime, hashlib, json, os, re, stat, time, types
from pathlib import Path
B=Path(__file__).resolve().parent
ASSIGNMENT='ASTRA-CHILD-F06-NATIVE567-RETAINED-ORACLE-HANDOFF-20261112#1'
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
FORMATS=('docx','xlsx','pptx','odt','ods','odp')
PROFILES=('compatible1.3_or_Agile',)*6+('current_default_latest_odt_negative',)
NAMES=tuple('f06-new-encrypted.'+f for f in FORMATS)+('f06-new-default-latest.odt',)
LIMITS=dict(whole_wall_seconds=300,aggregate_CPU_seconds=180,memory_bytes=2147483648,swap_bytes=0,affinity_cpus=2,pids_max=128,namespace_tmpfs_bytes=16777216,own_cap_bytes=100663296,cleanup_reserve_seconds=15,per_process_AS_bytes=2147483648,per_process_FSIZE_bytes=8388608,max_Office_starts=3,max_stores=0,max_password_probes=6)
MOSCOW=datetime.timezone(datetime.timedelta(hours=3))


MODE='verify-native-edits'
TASK=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-NATIVE567-RETAINED-ORACLE-HANDOFF-20261112')
CACHE=Path('/home/jericho/.cache')
TASK_CAP=192*1024**2
HANDOFF_PATH=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-NATIVE567-RETAINED-ORACLE-HANDOFF-20261112/native567_handoff.py')
HANDOFF_SHA='e1e35eb9c90bbab75a16bae8519977f25a0c2d490c2e86358fbc795ea8527209'
CANONICAL_ACCEPTANCE_PATH=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-NATIVE567-RETAINED-ADAPTER-ROOT-ACCEPTANCE-20261112.json')
CANONICAL_ACCEPTANCE_SHA='a55c6dde29ad229d9bd085de5a1907741e6091e8a92b706b0faaa940091fa137' # Exact genuine Root source-only acceptance; no runtime admission.
CODEC_ACCEPTANCE_PATH=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/F06-PASSWORD-ORACLE-CODEC-FINAL-SNAPSHOT-ACCEPTANCE.json')
CODEC_ACCEPTANCE_SHA='84db6c10fcd5ae8d44ea9b4770cdbef5d918ab92790edf4bd5a56ab1474af457'
CODEC_OLD_ACCEPTANCE_PATH=CODEC_ACCEPTANCE_PATH.parent/'F06-PASSWORD-ORACLE-CODEC-ROOT-ACCEPTANCE.json'
CODEC_OLD_ACCEPTANCE_SHA='5b17faa03abbfb21ecca16b4b244de38bd0b497df3fced805fcf98d8130894ff'
CODEC_SNAPSHOT_ROOT=CODEC_ACCEPTANCE_PATH.parent/'F06-CODEC-FINAL-PRIVATE-SNAPSHOTS'
CODEC_REFUSAL_SHA='894c805582acc4e959f7315b20e0439818b4c404f6c3beec7bc87c91f10a7783'
MANDATORY_SOURCES={'f06_contract.py','root_frame.py','run_once.py','inside_once.py','embedded_entry.py','office_fixture_driver.py','SOURCE-REQUEST.json','REFERENCES.json','verify-native-edits.ADMISSION.TEMPLATE.json','request_args_compat_v2.py','callback_observer_v2.py'}
PRE_STAGE_CREDENTIAL_PATHS=set()
REF_KEYS={'path','sha256','bytes','identity','uid','gid','mode','dev','ino','nlink','mtime_ns','ctime_ns'}
FLAT_KEYS={'uid':'st_uid','gid':'st_gid','dev':'st_dev','ino':'st_ino','nlink':'st_nlink','mtime_ns':'st_mtime_ns','ctime_ns':'st_ctime_ns'}

def limits(mode):
 need(mode==MODE,'MODE');return dict(LIMITS)

def operation(key,mode):
 limits(mode)
 need(type(key)is str and re.fullmatch('verify-native-edits-[a-z0-9]{1,32}',key)is not None,'OPERATION_KEY')
 return B/'operations'/key

def unit_name(key):
 operation(key,MODE)
 return 'frw-astra-f06-'+key+'-20261111.service'

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
 # Deliberately metadata only. Never open/read/hash this path here.
 reference_shape(ref);need(ref['bytes']<16384,'CREDENTIAL_METADATA_SIZE')
 path=canonical(ref['path']);protected_parents(path);info=path.lstat()
 need(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1 and info.st_size==ref['bytes'],'CREDENTIAL_METADATA_CUSTODY')
 declared_metadata(ref,info)
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
 need(obj.get('schema')=='friday.f06.retained-output-root-source.v1' and obj.get('state')=='SOURCE_ONLY_DORMANT','SOURCE_SCHEMA')
 source_set=obj.get('source_set');need(type(source_set)is list and source_set==sorted(set(source_set)) and MANDATORY_SOURCES<=set(source_set),'SOURCE_SET')
 rows=obj.get('files');need(type(rows)is list and [r.get('name')for r in rows]==source_set,'SOURCE_ROWS')
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

def codec_pin_shape(ref):
 # Full stable pins are mandatory here, including all nine identity fields.
 reference_shape(ref)
 need(set(ref)=={'path','bytes','sha256','identity'},'CODEC_FULL_PIN_REQUIRED')
 ident=ref['identity']
 need(type(ident)is list and len(ident)==len(IDENTITY_FIELDS) and all(type(v)is int for v in ident),'CODEC_IDENTITY_SHAPE')
 need(stat.S_ISREG(ident[2]) and stat.S_IMODE(ident[2])==0o600 and ident[3]==os.getuid() and ident[5]==1 and ident[6]==ref['bytes'],'CODEC_PIN_CUSTODY')

def codec_proof_read(ref):
 codec_pin_shape(ref);raw,pin=reference_read(ref)
 need(exact_json(pin,ref),'CODEC_LINKED_PROOF_CAS')
 return raw,pin

def codec_acceptance(row):
 """Exact Root successor and immutable provenance; no original Q/cipher reads."""
 need(type(row)is dict and row.get('path')==str(CODEC_ACCEPTANCE_PATH) and row.get('sha256')==CODEC_ACCEPTANCE_SHA,'CODEC_EXACT_ROOT_ACCEPTANCE')
 raw,_=codec_proof_read(row);accepted=decode(raw)
 need(accepted.get('schema')=='friday.f06.Root-password-oracle-codec-acceptance.v1' and accepted.get('state')=='ROOT_ACCEPTED_TYPED_PASSWORD_ABORT_CODEC_SOURCE_AND_REPRESENTATIVE_CONTRAST','CODEC_ROOT_ACCEPTANCE_STATE')
 need(all(accepted.get(k)is False for k in ('all_seven_profiles_qualified','raw_G6_false_promoted','original_effects_replayed','native_grant_issued','stores_or_generation_authorized')),'CODEC_REPRESENTATIVE_SCOPE_ONLY')
 need(type(accepted.get('typed_negative_sequences_observed'))is int and accepted['typed_negative_sequences_observed']==4 and type(accepted.get('correct_samebyte_semantics_observed'))is int and accepted['correct_samebyte_semantics_observed']==2 and accepted.get('actual_representatives')==['docx','odt-compatible'],'CODEC_REPRESENTATIVE_OBSERVATIONS')
 helpers=accepted.get('helpers');need(type(helpers)is dict and set(helpers)=={'request_args_compat_v2.py','callback_observer_v2.py'},'CODEC_HELPER_SET')
 snapshots={**helpers,'independent_review':accepted['independent_review']}
 for name,ref in snapshots.items():
  filename='CANDIDATE-DELTA-REVIEW.json' if name=='independent_review' else name
  need(ref.get('path')==str(CODEC_SNAPSHOT_ROOT/filename),'CODEC_SNAPSHOT_EXACT_PATH')
  codec_proof_read(ref)
  if name in helpers:
   _,local=private(B/name,B)
   need(all(local[k]==ref[k]for k in ('bytes','sha256')),'CODEC_LOCAL_HELPER_BYTES')
 oldref=accepted['supersedes_old_acceptance']
 need(oldref.get('path')==str(CODEC_OLD_ACCEPTANCE_PATH) and oldref.get('sha256')==CODEC_OLD_ACCEPTANCE_SHA,'CODEC_OLD_ACCEPTANCE_LINEAGE')
 old=decode(codec_proof_read(oldref)[0])
 # Apart from time and the three stabilized proof refs, scope/policy/results
 # must be exactly the immutable old acceptance. No old Q file is opened.
 projection=dict(accepted)
 for key in ('supersedes_old_acceptance','preintent_refusal','proof_snapshot_origins'):projection.pop(key)
 for key in ('at_moscow','helpers','independent_review'):projection[key]=old[key]
 need(exact_json(projection,old),'CODEC_UNCHANGED_ACCEPTED_POLICY_AND_SCOPE')
 refusalref=accepted['preintent_refusal']
 need(refusalref.get('path')==str(CODEC_ACCEPTANCE_PATH.parent/'F06-FULL7-PREINTENT-CODEC-CAS-REFUSAL.json') and refusalref.get('sha256')==CODEC_REFUSAL_SHA,'CODEC_PREINTENT_REFUSAL_PIN')
 refusal=decode(codec_proof_read(refusalref)[0])
 need(refusal.get('schema')=='friday.f06.preintent-proof-cas-refusal.v1' and refusal.get('state')=='REFUSED_BEFORE_SLOT_UNIT_NAMESPACE_COPIES_DOCUMENTS' and refusal.get('reason')=='CODEC_LINKED_PROOF_CAS','CODEC_PREINTENT_REFUSAL_PRESERVED')
 originref=accepted['proof_snapshot_origins']
 need(originref.get('path')==str(CODEC_SNAPSHOT_ROOT/'ORIGIN-CUSTODY.json'),'CODEC_ORIGIN_EXACT_PATH')
 origin=decode(codec_proof_read(originref)[0])
 need(origin.get('schema')=='friday.f06.Root-final-codec-source-snapshot-origin.v1' and origin.get('state')=='EXACT_REVIEWED_NONSECRET_BYTES_ROOT_PRIVATE_SNAPSHOTS' and origin.get('native_GRANT')is False,'CODEC_ORIGIN_STATE')
 need(exact_json(origin.get('old_acceptance'),oldref) and exact_json(origin.get('failed_preintent'),refusalref),'CODEC_ORIGIN_ACCEPTANCE_REFUSAL_JOIN')
 sources=origin.get('sources');need(type(sources)is dict and set(sources)==set(snapshots),'CODEC_ORIGIN_SOURCE_SET')
 observations=refusal.get('linked_proof_observations');need(type(observations)is list,'CODEC_REFUSAL_OBSERVATIONS')
 oldsources={**old['helpers'],'independent_review':old['independent_review']}
 for name,ref in snapshots.items():
  item=sources[name];before=item['original_pin_at_acceptance'];now=item['original_pin_now']
  codec_pin_shape(before);codec_pin_shape(now)
  need(exact_json(before,oldsources[name]) and exact_json(item.get('snapshot'),ref),'CODEC_ORIGIN_SNAPSHOT_JOIN')
  need(all(now[k]==before[k]for k in ('path','bytes','sha256')) and now['identity'][:8]==before['identity'][:8] and now['identity'][8]!=before['identity'][8],'CODEC_ORIGIN_ONLY_CTIME_DELTA')
  need(all(ref[k]==before[k]for k in ('bytes','sha256')) and item.get('only_identity_metadata_changed')is True and item.get('source_bytes_changed')is False and item.get('original_chmod_or_write')is False,'CODEC_ORIGIN_UNCHANGED_BYTES')
  anchor=Path(old['source_root']);expected_parent_mode='0o775' if name=='independent_review' else '0o700'
  need(item.get('protected_original_anchor')==str(anchor) and Path(before['path']).is_relative_to(anchor) and item.get('original_parent_mode')==expected_parent_mode,'CODEC_ORIGIN_PROTECTED_HISTORY')
  matches=[o for o in observations if o.get('path')==before['path']]
  need(len(matches)==1 and matches[0].get('same_bytes_sha')is True and matches[0].get('same_identity')is False and exact_json(matches[0].get('old_identity'),before['identity']) and exact_json(matches[0].get('actual_pin'),now) and matches[0].get('parent_mode')==expected_parent_mode,'CODEC_ORIGIN_REFUSAL_OBSERVATION_JOIN')
 codec_proof_read(accepted['Root_source_delta_acceptance'])
 contrast=accepted.get('actual_contrast');need(type(contrast)is dict and set(contrast)=={'source','result','closure'},'CODEC_ACTUAL_CONTRAST_SET')
 actual={key:decode(codec_proof_read(ref)[0])for key,ref in contrast.items()}
 closure=actual['closure']
 need(closure.get('state')=='SECONDARY_ABORT_COMPAT_CONTRAST_KNOWN_CLOSED_OBSERVATIONS_ONLY' and closure.get('source_pins_sha256')==contrast['source']['sha256'] and exact_json(closure.get('diagnostic_ref'),contrast['result']) and closure.get('original_generation_replayed')is False and closure.get('stores')==0 and closure.get('child_reaped')is True and closure.get('owned_children_closed')is True and closure.get('owned_pipes_closed')is True and closure.get('slot_reacquired_and_released')is True,'CODEC_ACTUAL_CONTRAST_CLOSED_JOIN')
 return accepted

def output_inputs(a):
 """Distinct native567 exact metadata/cipher custody; no credential bytes."""
 need(a.get('mode')==MODE,'OUTPUT_INPUT_MODE')
 credential,credential_id=credential_metadata(a['credential_source']);forbidden={credential['path']};PRE_STAGE_CREDENTIAL_PATHS.update(forbidden)
 need(type(a.get('credential_source_identity'))is list and len(a['credential_source_identity'])==len(IDENTITY_FIELDS) and all(type(v)is int for v in a['credential_source_identity']) and a['credential_source_identity']==credential_id,'CREDENTIAL_ADMISSION_IDENTITY')
 adapter_ref=a['metadata_adapter_source']
 need(adapter_ref.get('path')==str(HANDOFF_PATH) and adapter_ref.get('sha256')==HANDOFF_SHA,'M2_ADAPTER_SOURCE')
 adapter_raw,_=reference_read(adapter_ref,forbidden)
 need(CANONICAL_ACCEPTANCE_SHA is not None,'NATIVE567_ROOT_ACCEPTANCE_UNBOUND')
 acceptance_ref=a['canonical_fix_acceptance']
 need(acceptance_ref.get('path')==str(CANONICAL_ACCEPTANCE_PATH) and acceptance_ref.get('sha256')==CANONICAL_ACCEPTANCE_SHA,'M2_CANONICAL_ACCEPTANCE')
 acceptance=decode(reference_read(acceptance_ref,forbidden)[0])
 need(acceptance.get('schema')=='friday.f06.Root-native567-retained-adapter-acceptance.v1' and acceptance.get('state')=='ROOT_INDEPENDENT_EXACT_DELTA_ACCEPTED_SOURCE_ONLY' and acceptance.get('source',{}).get('path')==str(HANDOFF_PATH) and acceptance.get('source',{}).get('sha256')==HANDOFF_SHA,'NATIVE567_ACCEPTED_SOURCE')
 need(acceptance.get('assignment')==ASSIGNMENT and acceptance.get('native_operation_id')=='ASTRA-F06-NATIVE203-UNSTARTED567-20261112#1' and acceptance.get('selected_fixture_ids')==['f06-5','f06-6'] and acceptance.get('findings_remaining')==[] and acceptance.get('execution_authorized')is False,'NATIVE567_ACCEPTANCE_SCOPE')
 request=decode(reference_read(a['metadata_request'],forbidden)[0])
 need(exact_json(request.get('credential'),credential),'M2_REQUEST_CREDENTIAL_JOIN')
 manifest_raw,manifest_pin=reference_read(a['output_manifest'],forbidden)
 manifest=decode(manifest_raw)
 # Reuse accepted pure metadata mapping, native grant/once/receipt and source
 # provenance joins instead of inventing another interpretation of handoff.
 module=types.ModuleType('f06_retained_metadata_reference');module.__file__=str(HANDOFF_PATH)
 exec(compile(adapter_raw,str(HANDOFF_PATH),'exec'),module.__dict__)
 expected=module.build(request)
 need(exact_json(expected,manifest),'M2_EXACT_MAPPED_MANIFEST')
 need(manifest.get('lineage_mode')=='distinct_native567_retained' and manifest.get('native_assignment')=='ASTRA-CHILD-F06-UNSTARTED-ODF-NATIVE-SCOPE-20261112#1' and manifest.get('native_operation_id')=='ASTRA-F06-NATIVE203-UNSTARTED567-20261112#1' and manifest.get('selected_fixture_ids')==['f06-5','f06-6'],'NATIVE567_MANIFEST_LINEAGE_SELECTION')
 ids=manifest.get('selected_fixture_ids');rows=manifest.get('fixtures');order=['f06-'+str(i)for i in range(1,8)]
 need(manifest.get('schema')=='friday.f06.retained-native-edit-oracle.v1' and manifest.get('state')=='BOUND_RETAINED_BYTES_NOT_EXECUTION_AUTHORITY' and manifest.get('assignment')==ASSIGNMENT and manifest.get('semantic')=='BRAVO23','OUTPUT_MANIFEST_SCHEMA')
 need(type(ids)is list and ids and ids==[i for i in order if i in ids] and type(rows)is list and len(rows)==len(ids) and type(manifest.get('selected_count'))is int and manifest['selected_count']==len(ids)<=7,'OUTPUT_SELECTION')
 need(a.get('selected_fixture_ids')==ids and type(a.get('selected_count'))is int and a['selected_count']==len(ids),'ADMISSION_SELECTION_JOIN')
 need(manifest.get('expected_Office_stores')==0 and type(manifest.get('expected_Office_stores'))is int and manifest.get('expected_Office_password_probes')==3*len(ids) and type(manifest.get('expected_Office_password_probes'))is int and manifest.get('whole_F06_accepted')is False,'OUTPUT_EXPECTED_EFFECTS')
 need(a.get('expected_stores')==0 and type(a.get('expected_stores'))is int and a.get('expected_probes')==3*len(ids) and type(a.get('expected_probes'))is int,'ADMISSION_EXPECTED_EFFECTS')
 need(exact_json(manifest.get('credential'),credential),'OUTPUT_CREDENTIAL_JOIN')
 evidence=a.get('native_evidence');need(type(evidence)is dict and set(evidence)==set(manifest.get('proofs',{})),'NATIVE_EVIDENCE_SET')
 for name,ref in evidence.items():
  need(exact_json(ref,manifest['proofs'][name]),'NATIVE_EVIDENCE_JOIN')
  reference_read(ref,forbidden)
 original=[]
 for ident,row in zip(ids,rows):
  index=order.index(ident);fmt=FORMATS[index]if index<6 else 'odt';name='f06-native-edited.'+fmt if index<6 else 'f06-native-edited-default-latest.odt'
  need(row.get('fixture_id')==ident and row.get('format')==fmt and row.get('fixture_profile')==PROFILES[index] and row.get('staged_name')==name and row.get('semantic')=='BRAVO23','OUTPUT_TYPED_ROW')
  source_ref=row['native_source_ciphertext'];output_ref=row['native_output_custody']
  _,source_pin=reference_read(source_ref,forbidden,1000000);_,output_pin=reference_read(output_ref,forbidden,1000000)
  need(all(row[k]==output_pin[k]for k in ('path','sha256','bytes')) and source_pin['path']!=output_pin['path'] and source_pin['sha256']!=output_pin['sha256'],'OUTPUT_SOURCE_CUSTODY_JOIN')
  original.append({**output_pin,'fixture_id':ident,'native_source_ciphertext':source_pin})
 # A credential replacement during proof/cipher validation must not pass.
 need(credential_metadata(credential)[1]==credential_id,'CREDENTIAL_METADATA_AFTER_CAS')
 return manifest,manifest_pin,original,credential

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
