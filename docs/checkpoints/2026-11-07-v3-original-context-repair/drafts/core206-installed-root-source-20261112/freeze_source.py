"""Freeze exact acyclic source and immutable history; creates no runtime request or grant."""
from pathlib import Path
import ast,hashlib,json,os,stat
B=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112')
TASK=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
os.umask(0o077)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def refs(v):
 if isinstance(v,dict):
  if set(v)>={'path','sha256'}and isinstance(v['path'],str)and v['path'].startswith('/')and isinstance(v['sha256'],str)and len(v['sha256'])==64:yield {k:v[k]for k in ('path','sha256')}
  for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
def add(out,p,d=None):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1 and not any(a.is_symlink()for a in(p,*p.parents)),str(p)
 digest=sha(p);assert d is None or d==digest,'pin_drift:'+str(p)
 if str(p)in out:assert out[str(p)]==digest
 out[str(p)]=digest
for n in ['SOURCE-PINS.json','ROOT-FRESH-REQUEST.json','ROOT-206-RUNTIME-AUTHORITY.json','ROOT-206-SOURCE-ACCEPTANCE.json','ROOT-ACTUAL205-PREDECESSOR.json','ROOT-NATIVE206-LIVE-OPERATION.json','FUTURE-EXECUTION']:assert not os.path.lexists(B/n),'bound_or_frozen_domain_refuses_regeneration:'+n
source={};history={}
# Exact accepted sourcefreeze transitive rows; these carry no current205 runtime authority.
add(source,TASK/'SOURCE-FREEZE.json','f1be05ce4e5b6a047d9ef90b465eec38b884ed08e9febe8234a797b4924872e0')
for row in load(TASK/'SOURCE-FREEZE.json')['rows']:add(source,row['path'],row['sha256'])
# Reuse retained bank/profile/R2 evidence without copying or invoking their collectors.
for p,d in load(OLD/'SOURCE-PINS.json')['source_refs'].items():
 if any(part in p for part in ['/FRW-ASTRA-V3-F04-','/FRW-ASTRA-V3-ODP-','/FRW-ASTRA-V3-V03-RECEIVED-PPTX-','/FRW-ASTRA-V3-CORE-F01-']):add(source,p,d)
# Explicit source refs from inert metadata constants.
tree=ast.parse((B/'root206_metadata.py').read_bytes())
for name in ['FIXED','ORIGIN_POLICY','ROOT198']:
 v=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
 for row in refs(v):add(source,row['path'],row['sha256'])
policy=load(B/'ROOT-206-PUBLIC-ORIGIN-POLICY.json')
for row in refs(policy):add(source,row['path'],row['sha256'])
oldpolicy=load(policy['published_ancestor48_policy']['path'])
for row in refs(oldpolicy):add(source,row['path'],row['sha256'])
# Full physical selected source projects, never assume all project paths are installed underH.
for root,inputref in [(Path(policy['current_private_project']),policy['current_private_input']),(Path('/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/project491'),dict(path='/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/INPUT-SOURCE205.json',sha256='2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9'))]:
 add(source,inputref['path'],inputref['sha256'])
 for n,d in load(inputref['path'])['project_files'].items():add(source,root/n,d)
join=load(B/'PROFILE-SOURCE-JOIN.json')
for row in refs(join):add(source,row['path'],row['sha256'])
# The retained205 profilejoin contains exact transitive evidence, preserved as such.
for row in refs(load(OLD/'PROFILE-SOURCE-JOIN.json')):add(source,row['path'],row['sha256'])
for row in refs(load(B/'ACTUAL205-HISTORICAL-METADATA.json')):add(history,row['path'],row['sha256'])
for row in refs(load(B/'REUSED-206-FINAL-SOURCE-EVIDENCE.json')):add(history,row['path'],row['sha256'])
for p in ['/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112/RESULT.json','/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112/ROOT-HANDOFF.json']:add(history,p)
for p in B.rglob('*'):
 if not p.is_file()or'review'in p.relative_to(B).parts or p.name in ['SOURCE-PINS.json','SOURCE-CONTROLS.json','RESULT.json','DIFF-MANIFEST.json','ROOT-NEXT-RECIPE.json']:continue
 if p.suffix in ['.py','.json']:add(source,p)
assert sum(p.stat().st_size for p in B.rglob('*')if p.is_file())<=64*1024**2,'own_source_cap'
counts=dict(before_layers=205,after_layers=206,before_project=491,after_project=493,native=17891,native_additions=0,native_targets=11,pair_absent=2,plugins=52,base=17730,selected_CAS=17,untouched_native_rows=17880)
v=dict(schema='frw.root206.coherent-after-actual205-source-pins.v1',state='FROZEN_SOURCE_ONLY_GENUINE205_PREDECESSOR_FUTURE206_NOT_INSTALLED',frame=str(B),publisher_unit='frw-astra-native206-install-after205-20261112.service',runtime_grant=False,execution_provenance_mode='UNBOUND_EXPLICIT_ROOT_MODE',execution_commit='UNBOUND_ROOT_CURRENT_COMMITTED_MAIN',public_main_sha=None,source_refs=source,historical_refs=history,public_changed_files=policy['reviewed_current_files'],counts=counts,freeze='Acyclic exact external source digest supplied byRootargv; excludes itself, laterpurecontrols/review/RESULT and allfutureRootbindings/requests/operation.',retained_limits=dict(native_canonical_unknown=3,structural_unresolved=45,R104_semantic_fail=True,default_workers_ready_accepted=False,DSH_A0_deferred=True,App_F06_template_PARTIAL=True,journaled_rollback_not_powerloss_atomicity=True,Standard32_data_integrity_verified=False,Agile_strict=True,modernODF_boundedunsupported_only=True,runtime_privacy_helper_WARN_genuineconsumer_NOT_RUN=True))
raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();fd=os.open(B/'SOURCE-PINS.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(state='SOURCE_FROZEN_NO_RUNTIME_GRANT',sha256=hashlib.sha256(raw).hexdigest(),source_refs=len(source),historical_refs=len(history))))
