"""One exact acyclic207 source freeze; no request/runtimegrant or missingbinding synthesis."""
from pathlib import Path
import ast,hashlib,json,os,stat
B=Path(__file__).parent;OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112');W=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112')
os.umask(0o077)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def refs(v):
 if isinstance(v,dict):
  if set(v)>={'path','sha256'}and isinstance(v['path'],str)and v['path'].startswith('/')and isinstance(v['sha256'],str)and len(v['sha256'])==64:yield {k:v[k]for k in ['path','sha256']}
  for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
def add(out,p,d=None):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1 and not any(a.is_symlink()for a in(p,*p.parents)),str(p)
 actual=sha(p);assert d is None or d==actual,'pin_drift:'+str(p)
 if str(p)in out:assert out[str(p)]==actual
 out[str(p)]=actual
for n in ['SOURCE-PINS.json','ROOT-FRESH-REQUEST.json','ROOT-207-PROJECT-SOURCE.json','ROOT-207-RUNTIME-AUTHORITY.json','ROOT-207-SOURCE-ACCEPTANCE.json','ROOT-ACTUAL206-PREDECESSOR.json','ROOT-NATIVE207-LIVE-OPERATION.json','FUTURE-EXECUTION']:assert not os.path.lexists(B/n),'bound_or_frozen_domain_refuses_regeneration:'+n
source={};history={}
# Accepted206 scope remains pinned and reused, never executing its consumed caller.
old=load(OLD/'SOURCE-PINS.json');assert sha(OLD/'SOURCE-PINS.json')=='c547cf3c65648a75f87693b23416a7fb2c287cdc8d6b3bb366bdca703e1253df';add(source,OLD/'SOURCE-PINS.json')
for p,d in old['source_refs'].items():add(source,p,d)
for p,d in old['historical_refs'].items():add(history,p,d)
add(source,W/'SOURCE-FREEZE.json','a1a34dcca440295256dae2ee0272643cdacc8459508bfae725873ca07e8503a6')
for row in load(W/'SOURCE-FREEZE.json')['rows']:add(source,row['path'],row['sha256'])
for origins in ['PROJECT495-ORIGINS.json','PUBLIC495-ORIGINS.json']:
 add(source,W/origins)
 for row in load(W/origins)['rows'].values():add(source,row['path'],row['sha256'])
# Exact metadata dependency values are literal refs, not runtime imports.
tree=ast.parse((B/'root207_metadata.py').read_bytes())
for name in ['FIXED','ORIGIN_POLICY','ROOT198','PROJECT_SOURCE_PROOF']:
 val=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets))
 for row in refs(val):add(source,row['path'],row['sha256'])
policy=load(B/'ROOT-207-PUBLIC-ORIGIN-POLICY.json')
for row in refs(policy):add(source,row['path'],row['sha256'])
# Root now supplied495, but current materialization proof is source-only, never authority.
add(source,policy['expected_actual_input_path'],policy['expected_actual_input_sha256'])
actual=load(policy['expected_actual_input_path']);root=Path(policy['current_private_project'])
for name,digest in actual['project_files'].items():add(source,root/name,digest)
for row in refs(load(B/'PROFILE-SOURCE-JOIN.json')):add(source,row['path'],row['sha256'])
for row in refs(load(B/'ACTUAL206-HISTORICAL-METADATA.json')):add(history,row['path'],row['sha256'])
for row in refs(load(B/'REUSED-207-FINAL-SOURCE-EVIDENCE.json')):add(history,row['path'],row['sha256'])
# No finaldigest in own frozen reports. Laterreview/result/recipe are outside this freeze.
for p in B.rglob('*'):
 if not p.is_file()or 'review'in p.relative_to(B).parts or p.name in ['SOURCE-PINS.json','RESULT.json','ROOT-NEXT-RECIPE.json']:continue
 if p.suffix in ['.py','.json','.diff']:add(source,p)
counts=load(B/'PROSPECTIVE207-PROJECTION.json')['counts']
v=dict(schema='frw.root207.coherent-after-actual206-source-pins.v1',state='FROZEN_SOURCE_ONLY_GENUINE206_PREDECESSOR_FUTURE207_NOT_INSTALLED',frame=str(B),publisher_unit='frw-astra-native207-install-after206-20261112.service',runtime_grant=False,execution_provenance_mode='UNBOUND_EXPLICIT_ROOT_MODE',execution_commit='UNBOUND_ROOT_CURRENT_COMMITTED_MAIN',public_main_sha=None,source_refs=source,historical_refs=history,public_changed_files=policy['reviewed_current_files'],counts=counts,freeze='Acyclic exact external argv digest; excludes itself, subsequent review/result/recipe, all future Rootbindings/requests/admission/once/operation. Root provided495proof is only source materialization, notruntimeauthority.',retained_limits=dict(native_canonical_unknown=3,structural_unresolved=45,R104_semantic_fail=True,default_workers_ready_accepted=False,DSH_A0_deferred=True,App_F06_template_PARTIAL=True,modern7_original_FAIL_editnone=True,journaled_rollback_not_powerloss_atomicity=True,Standard32_data_integrity_verified=False,Agile_strict=True,modern_ODT_crypto85_plus12_exact_reused=True,ordinary_F06_sourceR3_privacy_separate=True))
assert sum(p.stat().st_size for p in B.rglob('*')if p.is_file())<=64*1024**2
raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();fd=os.open(B/'SOURCE-PINS.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(state='FROZEN_SOURCE_ONLY_NO_EXECUTION_GRANT',sha256=hashlib.sha256(raw).hexdigest(),source_refs=len(source),historical_refs=len(history))))
