"""Exclusive acyclic source manifest creation; no request/runtime authority is created."""
from pathlib import Path
import hashlib,json,os
B=Path(__file__).resolve().parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-ROOT-FRAME-PREP-20261111')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 os.umask(0o077)
 forbidden=['ROOT-FRESH-REQUEST.json','ROOT-205-RUNTIME-AUTHORITY.json','ROOT-205-SOURCE-ACCEPTANCE.json','ROOT-ACTUAL204-PREDECESSOR.json','ROOT-NATIVE205-LIVE-OPERATION.json','FUTURE-EXECUTION','SOURCE-PINS.json']
 if any(os.path.lexists(B/n)for n in forbidden):raise ValueError('bound_or_frozen_domain_refuses_regeneration')
 previous=json.loads((OLD/'SOURCE-PINS.json').read_bytes());external={}
 # Preserve unchanged rich-source/profile/F04 evidence, excluding superseded frame mechanics.
 for path,digest in previous['source_refs'].items():
  if path.startswith(str(OLD))or '/CORE204-ROOT-BOUNDARY-SOURCE-PREP-'in path or path.endswith('/run_native204_once.py'):continue
  if sha(path)!=digest:raise ValueError('unchanged_source_ref_drift:'+path)
  external[path]=digest
 # Static pure module AST only: read explicit transitive source/metadata references.
 import ast
 module=ast.parse((B/'root205_metadata.py').read_bytes())
 fixed=next(ast.literal_eval(n.value)for n in module.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='FIXED'for t in n.targets))
 origin=next(ast.literal_eval(n.value)for n in module.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='ROOT204_ORIGIN_METADATA'for t in n.targets))
 for ref in [*fixed.values(),origin]:
  if sha(ref['path'])!=ref['sha256']:raise ValueError('source_hash_drift:'+ref['path'])
  external[ref['path']]=ref['sha256']
 policy=Path(origin['path']).parent/'ROOT-204-PUBLIC-ORIGIN-POLICY.json';external[str(policy)]=sha(policy)
 doc=json.loads(policy.read_bytes())
 for key in ('public_input','private_input','counterparts'):
  ref=doc[key]
  if sha(ref['path'])!=ref['sha256']:raise ValueError('origin_reference_drift:'+ref['path'])
  external[ref['path']]=ref['sha256']
 for ref in doc['retained_executed_sources'].values():
  if sha(ref['path'])!=ref['sha256']:raise ValueError('origin_retained_source_drift:'+ref['path'])
  external[ref['path']]=ref['sha256']
 historical={}
 h=json.loads((B/'ACTUAL204-HISTORICAL-METADATA.json').read_bytes())
 for ref in [*h['references'].values(),*h['stage_refs'],h['intent']]:historical[ref['path']]=ref['sha256']
 reuse=json.loads((B/'REUSED-205-FINAL-SOURCE-EVIDENCE.json').read_bytes())
 for ref in [reuse['final_source_result'],reuse['root_acceptance'],reuse['independent_review'],*[v['evidence']for v in reuse['four_gate_evidence']]]:historical[ref['path']]=ref['sha256']
 for p in ('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112/RESULT.json','/home/jericho/.cache/FRW-ASTRA-V3-CORE204-STARTUP-OBSERVER-R2-20261112/ROOT-HANDOFF.json'):
  historical[p]=sha(p)
 own=[p for p in B.rglob('*')if p.is_file()and p.suffix in ('.py','.json')and p.name not in ('SOURCE-CONTROLS.json','SOURCE-PINS.json','RESULT.json','DIFF-MANIFEST.json','ROOT-NEXT-RECIPE.json','FRESHNESS-DELTA-CHECK.json')and 'review'not in p.relative_to(B).parts]
 source={**external,**{str(p):sha(p)for p in own}}
 for path,digest in historical.items():
  if sha(path)!=digest:raise ValueError('historical_metadata_drift:'+path)
 total=sum(p.stat().st_size for p in B.rglob('*')if p.is_file())
 if total>64*1024**2:raise ValueError('own_source_disk_cap_exceeded')
 value=dict(schema='frw.root205.coherent-after-actual204-source-pins.v1',state='FROZEN_SOURCE_ONLY_GENUINE204_PREDECESSOR_FUTURE205_NOT_INSTALLED',frame=str(B),publisher_unit='frw-astra-native205-install-after204-20261112.service',runtime_grant=False,public_main_sha=None,execution_commit='UNBOUND_ROOT_CURRENT_COMMITTED_MAIN',source_refs=source,historical_refs=historical,public_changed_files=previous['public_changed_files'],counts=previous['counts'],freeze='Acyclic: exact manifest digest is supplied by Root argv. Manifest does not hash itself, actual Root inputs, later control/review outputs or RESULT.',retained_limits=dict(native_canonical_unknown=3,structural_unresolved=45,R104_semantic_fail=True,default_workers_ready_accepted=False,DSH_A0_deferred=True,App_F06_template_PARTIAL_is_local_not_global205_blocker=True,journaled_rollback_not_powerloss_atomicity=True))
 raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode();fd=os.open(B/'SOURCE-PINS.json',os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw)
 print(json.dumps(dict(state='SOURCE_FROZEN_NO_RUNTIME',sha256=hashlib.sha256(raw).hexdigest(),own_bytes=total,source_refs=len(source),historical_refs=len(historical))))
if __name__=='__main__':main()
