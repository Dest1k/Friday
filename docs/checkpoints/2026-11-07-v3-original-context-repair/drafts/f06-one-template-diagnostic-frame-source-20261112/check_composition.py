import os,pathlib,json,hashlib,ast,resource,subprocess,tempfile,shutil,time
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
B=pathlib.Path(__file__).parent;C=B/'candidate';D=B/'baseline';start=time.monotonic();rows=[]
source=json.loads((C/'SOURCE-PINS.json').read_bytes());freeze=json.loads((B/'SOURCE-FREEZE-FINAL.json').read_bytes())
for row in freeze['files']:
 p=pathlib.Path(row['path']);raw=p.read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'];rows.append(row)
assert source['source_set']==sorted(source['source_set'])
assert {p.name for p in C.glob('*.py')}=={n for n in source['source_set']if n.endswith('.py')}
for row in source['files']:
 raw=(C/row['name']).read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
# Real patch program operates only on minimal own source fixture, never imports.
stand=pathlib.Path(tempfile.mkdtemp(prefix='patch-stand-',dir=B));checks={}
try:
 for p in D.glob('*.py'):(stand/p.name).write_bytes(p.read_bytes())
 for reverse in (False,True):
  args=['/usr/bin/patch','--batch','-p1','--reverse'if reverse else'--forward','-i',str(B/'TASK25-FRAME.patch')]
  p=subprocess.run(args,cwd=stand,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
  assert p.returncode==0
  expected=D if reverse else C
  names={p.name for p in stand.glob('*.py')};assert names=={p.name for p in expected.glob('*.py')}
  assert all((stand/n).read_bytes()==(expected/n).read_bytes()for n in names)
  checks['reverse'if reverse else'forward']=True
finally:shutil.rmtree(stand)
# Source recipe has correct original embedded3.12 + no cycle/stale placeholders
# in executable bindings; placeholders occur only in inert runtime proof shapes.
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p),feature_version=(3,12))
assert json.loads((C/'ROOT-BINDINGS.TEMPLATE.json').read_bytes())['runtime_authority']is None
assert json.loads((C/'ROOT-PROOFS.TEMPLATE.json').read_bytes())['state']=='ALL_UNBOUND_NO_AUTHORITY'
recipe=json.loads((B/'ROOT-FUTURE-RECIPE.json').read_bytes());assert recipe['source_pins']['sha256']==hashlib.sha256((C/'SOURCE-PINS.json').read_bytes()).hexdigest()
report=dict(schema='task25.source-composition-check.v1',all_pass=True,source_only=True,freeze_exact_refs=len(rows),candidate_source_rows=len(source['files']),python312_grammar=11,patch_forward_reverse=checks,minimal_stand_removed=True,no_source_import_or_Office_execution=True,actual_limits={'CPU':resource.getrlimit(resource.RLIMIT_CPU),'AS':resource.getrlimit(resource.RLIMIT_AS),'affinity':sorted(os.sched_getaffinity(0))},wall_seconds=time.monotonic()-start,CPU_seconds=time.process_time(),maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(B/'COMPOSITION-CHECKS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
