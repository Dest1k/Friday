"""Pinned source-only nine-edge recipe readers; no real publication authority."""
import ast,hashlib,json,math,sys
from pathlib import Path
KINDS=('operational-success','operational-rollback','public-success','public-rollback')
AUTHORITY='EXPLICIT_SYNTHETIC_SOURCE_ONLY_NO_NATIVE_OR_RUNTIME_GRANT'
LIMITS={'cpu_seconds':420,'wall_seconds':600,'maximum_cpus':2,'address_space_bytes':2*1024**3,'maximum_declared_own_total_bytes':512*1024**2}
LIMIT_SCOPE='RLIMIT_CPU and RLIMIT_AS are per process and inherited by subprocesses; affinity limits process tree to2 selected CPUs; wall deadline600. No aggregate cgroup memory or CPU-accounting claim.'
def require(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).resolve(strict=True)),'sha256':sha(p)}
def json_read(p):
 def pairs(rows):
  d={}
  for k,v in rows:require(k not in d,'duplicate JSON key');d[k]=v
  return d
 def nonfinite(v):raise ValueError('nonfinite JSON number')
 def finite(v):
  n=float(v);require(math.isfinite(n),'nonfinite JSON float');return n
 return json.loads(Path(p).read_bytes(),object_pairs_hook=pairs,parse_constant=nonfinite,parse_float=finite)
def literal(p,k):
 for n in ast.parse(Path(p).read_bytes()).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==k for t in n.targets):return ast.literal_eval(n.value)
 raise ValueError('missing literal '+k)
def verify_recipe(p,digest,own):
 require(__debug__,'optimized Python prohibited');p=Path(p).resolve(strict=True)
 require(p.is_relative_to(own) and sha(p)==digest,'recipe path/hash differs');v=json_read(p)
 require(v['schema']=='frw.modern-odt.ninth.synthetic-whole-gate-recipe.v1' and v['state']=='SOURCE_ONLY_REVIEWED_FINAL_RECIPE','unreviewed recipe')
 require(v['authority']==AUTHORITY and v['limits']==LIMITS and v['limit_scope']==LIMIT_SCOPE and v['run_order']==list(KINDS),'authority/budget/order differs')
 for name,h in v['pins'].items():require(sha(name)==h,'input drift '+name)
 r=json_read(v['independent_review']['path']);require(r['blocking_findings']==[] and r['source_freeze']['sha256']==v['source_freeze']['sha256'] and r['state']=='APPROVED_SOURCE_AND_GATE_PREPARATION','independent approval absent')
 require(v['actual206_context_only']['not_fresh_admission'] is True,'real206 context confused with grant')
 return v
def verify_python(v):
 require(sys.executable==v['python'] and sys.prefix==v['python_prefix'],'selected PM interpreter/prefix differs')
 import ruamel.yaml
 return {'python':sys.executable,'prefix':sys.prefix,'ruamel_yaml':str(Path(ruamel.yaml.__file__))}
