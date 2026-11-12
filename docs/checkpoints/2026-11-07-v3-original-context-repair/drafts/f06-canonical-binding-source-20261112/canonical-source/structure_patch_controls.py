import ast,difflib,hashlib,json,shutil,subprocess,types
from pathlib import Path
B=Path(__file__).resolve().parent;checks=[]
def check(name,v):
 assert v,name;checks.append(name)
def astfun(p,name):
 t=ast.parse(p.read_text());return ast.dump(next(n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name),include_attributes=False)
for branch,caller in [('first','root_bind_existing_consumer_once.py'),('correct','root_bind_dispatch_once.py')]:
 old=B/'before'/branch;new=B/'candidate'/branch
 for leaf in [p.name for p in old.iterdir()]:
  if leaf.endswith('.py'):ast.parse((new/leaf).read_text(),feature_version=(3,12))
  if leaf not in ('f06_source.py',caller):check(branch+':unchanged:'+leaf,(old/leaf).read_bytes()==(new/leaf).read_bytes())
 for fn in ('read','readref','new','load','clock_remaining','StopUnconfirmed','owned_remaining','wait_owned','canonical_path'):
  check(branch+':unchanged:'+fn,astfun(old/caller,fn)==astfun(new/caller,fn))
 text=(new/caller).read_text();check(branch+':exact_reconstruction_guard',"need(a.successor(read(a.BASE,private=False),json.loads(read(work/'ROOT-ACTUAL-BINDING.json'))['contract'],footer)==read(bound),'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE')" in text)
 oldbody=(old/caller).read_text();begin="        actor=None;stops=[];forwarded_stops=0;wait_attempted=False;forwarding_stops=False";check(branch+':same_R3_birth_stop_block',oldbody[oldbody.index(begin):]==text[text.index(begin):])
 tree=ast.parse(text);exe=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');calls=[(n.lineno,n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else '?') for n in ast.walk(exe) if isinstance(n,ast.Call)]
 firstload=min(l for l,fn in calls if fn=='load');check(branch+':source_gate_before_exec',text.index('F06_REVIEWED_SOURCE_DRIFT')<text.index("a=load("))
 check(branch+':strict_contract_copy', 'c=a.canonical_contract(' in text and 'c=json.loads(encoded(v[\'contract\'])' not in text)
# Whole nine-file exact forward/reverse patch. This is an own source stand, no shared Git.
parts=[]
for before in sorted((B/'before').glob('*/*')):
 after=B/'candidate'/before.relative_to(B/'before');rel=str(before.relative_to(B/'before'))
 if before.read_bytes()!=after.read_bytes():parts.extend(difflib.unified_diff(before.read_text().splitlines(keepends=True),after.read_text().splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel))
patch=B/'SOURCE.patch';patch.write_text(''.join(parts));stand=B/'patch-stand';shutil.copytree(B/'before',stand)
try:
 q=subprocess.run(['/usr/bin/git','--no-optional-locks','apply','--check',str(patch)],cwd=stand,capture_output=True,timeout=10);check('patch:forward_check',q.returncode==0)
 q=subprocess.run(['/usr/bin/git','--no-optional-locks','apply',str(patch)],cwd=stand,capture_output=True,timeout=10);check('patch:forward',q.returncode==0)
 check('patch:all_nine_after_exact',all((stand/p.relative_to(B/'candidate')).read_bytes()==p.read_bytes() for p in (B/'candidate').glob('*/*')))
 q=subprocess.run(['/usr/bin/git','--no-optional-locks','apply','-R',str(patch)],cwd=stand,capture_output=True,timeout=10);check('patch:reverse',q.returncode==0)
 check('patch:all_nine_before_exact',all((stand/p.relative_to(B/'before')).read_bytes()==p.read_bytes() for p in (B/'before').glob('*/*')))
 p=stand/'first/f06_source.py';p.write_text(p.read_text().replace("need(type(base_raw) is bytes", "need(type(DRIFT_RAW) is bytes"));q=subprocess.run(['/usr/bin/git','--no-optional-locks','apply','--check',str(patch)],cwd=stand,capture_output=True,timeout=10);check('patch:wrong_touched_hunk_refused',q.returncode!=0)
finally:shutil.rmtree(stand)
check('patch:own_stand_removed',not stand.exists())
first=(B/'candidate/first/root_bind_existing_consumer_once.py').read_text()
check('first:no_issuer_module_or_old_caller',all(s not in first for s in ('ISSUER=', 'issuer.main(', 'issue-fresh-admission.py', 'root_bind_dispatch_once.py')))
for n,h in [('O-CLOSED.json','d8f6c472ab34a1349e8dfb49ead0a95383aa479728c8d0fa818a4446b12a83f5'),('X-CLOSED.json','88d9d8ca60a732597935602af1af54d730b7c3887f41c3c11a701aa72afc5cc0')]:check(n+':exact_primary_metadata',hashlib.sha256((B/n).read_bytes()).hexdigest()==h)
print(json.dumps({'scope':'pure source/patch invariants; not runtime/user acceptance','checks':checks,'count':len(checks),'all_pass':True,'changed_files':[str(p.relative_to(B/'before')) for p in sorted((B/'before').glob('*/*')) if p.read_bytes()!=(B/'candidate'/p.relative_to(B/'before')).read_bytes()],'source_patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest()},sort_keys=True))
