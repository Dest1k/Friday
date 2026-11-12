import ast,difflib,hashlib,json,os,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;B=R.parent
T=Path('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112/candidate');W=Path('/home/jericho/.cache/FRW-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112/candidate')
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode()
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b))
def put(p,v):p.write_bytes(enc(v));p.chmod(0o600);return ref(p)
def astdefs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
checks=[];branches={};files={};patch=[];r1patch=[];shared=[];changed=[]
for branch in ('first','correct','wrong-edit'):
 before=T/branch if branch!='wrong-edit' else W;after=R/'candidate'/branch;branchfiles={}
 for p in sorted(after.iterdir()):
  if p.name=='SOURCE-FREEZE.json':continue
  key=branch+'/'+p.name;old=(before/p.name).read_bytes();new=p.read_bytes();r1=(B/'candidate'/branch/p.name).read_bytes();files[key]=ref(p);branchfiles[p.name]={k:files[key][k] for k in ('bytes','sha256')}
  if old!=new:
   assert p.name in ('f06_footer.py.txt','f06_source.py','first_ingress.py');changed.append(key)
   patch.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+key,tofile='b/'+key))
  else:checks.append(key+':byte_identical_original')
  if r1!=new:r1patch.extend(difflib.unified_diff(r1.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+key,tofile='b/'+key))
  if p.name in ('f06_source.py','first_ingress.py'):
   bd,ad=astdefs(old),astdefs(new);assert bd.keys()==ad.keys() and all(ad[k]==v for k,v in bd.items() if k!='readref')
   checks.append(key+':only_readref_AST_changed_all_other_functions_and_gates_exact')
   leaf=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='readref')
   assert not any(k.arg=='limit' for n in ast.walk(leaf) if isinstance(n,ast.Call) for k in n.keywords)
   checks.append(key+':Root_path_reader_never_requires_limit_keyword')
 footer=(after/'f06_footer.py.txt').read_text().replace('__CONTRACT__','{}');fd=astdefs(footer)
 shared.append((fd['_f06_reference_read'],fd['_f06_bounded_reference_read']))
 assert 'F06_CONTRACT' not in fd['_f06_reference_read'] and 'F06_CONTRACT' not in fd['_f06_bounded_reference_read']
 checks.append(branch+':no_contract_dictionary_search_or_recursive_ref_authority')
 assert '_f06_reference_read.f06_read_reference=_f06_bounded_reference_read' in (after/'f06_footer.py.txt').read_text()
 checks.append(branch+':bounded_callback_explicitly_exposed')
 adapter=(after/'f06_source.py').read_text();assert "0<v['bytes']<=24*1024**2" in adapter
 assert 'F06_FRESH_B_NATIVE_CESSATION_REQUIRED' in adapter and 'F06_ROOT_B_CURRENT_BOUNDARY_CHANGED' in adapter
 checks.append(branch+':original24MiB_ref_cap_native_current_gates_preserved')
 generated=ast.parse((R/'checks'/branch/'SYNTHETIC-full-consumer.py').read_bytes());base=ast.parse(BASE.read_bytes())
 def methods(tree):
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runner');return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
 bm,am=methods(base),methods(generated);assert len(bm)==len(am)==191 and all(am[k]==v for k,v in bm.items() if k!='ordinary_independent_admission')
 assert astdefs(BASE.read_bytes())['safe_read']==astdefs((R/'checks'/branch/'SYNTHETIC-full-consumer.py').read_bytes())['safe_read']
 checks.append(branch+':190_original_Runner_methods_and_original_safe_read_AST_exact')
 bf=json.loads((before/'SOURCE-FREEZE.json').read_bytes());bf['files']=branchfiles;branches[branch]=put(after/'SOURCE-FREEZE.json',bf)
assert len(set(shared))==1;checks.append('all3:both_shared_reader_functions_AST_identical');assert len(changed)==8
for name,data in [('SOURCE.patch',patch),('REVISION1-TO-REVISION2.patch',r1patch)]:p=R/name;p.write_text(''.join(data));p.chmod(0o600)
f=put(R/'SOURCE-FREEZE.json',dict(schema='frw.F06.bounded-root-proof-consumer-source.v2',revision=2,files=files,branch_freezes=branches,changed_files=changed,original_fullv42_sha256='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3',original_MAX_JSON=1048576,reference_cap_bytes=24*1024**2,root_reader_ABI='read(path, private=True), optional f06_read_reference(exactref) attribute; no required limit keyword',R1_result=ref(B/'RESULT.json'),R1_source_freeze=ref(B/'SOURCE-FREEZE.json'),execution_authority=False))
# Verify exact patch application in a disposable own filesystem stand.
stand=R/'patch-stand';stand.mkdir(mode=0o700);commands=[]
for branch in ('first','correct','wrong-edit'):
 before=T/branch if branch!='wrong-edit' else W;(stand/branch).mkdir(mode=0o700)
 for p in before.iterdir():
  if p.name!='SOURCE-FREEZE.json':shutil.copyfile(p,stand/branch/p.name)
def apply(*args):
 p=subprocess.run(['git','apply',*args,str(R/'SOURCE.patch')],cwd=stand,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True,text=True);assert p.returncode==0,p.stderr;commands.append(dict(args=args,returncode=p.returncode))
apply('--check');apply()
for branch in ('first','correct','wrong-edit'):
 for p in (stand/branch).iterdir():assert p.read_bytes()==(R/'candidate'/branch/p.name).read_bytes()
apply('--reverse','--check');apply('--reverse')
for branch in ('first','correct','wrong-edit'):
 before=T/branch if branch!='wrong-edit' else W
 for p in (stand/branch).iterdir():assert p.read_bytes()==(before/p.name).read_bytes()
shutil.rmtree(stand);pr=put(R/'PATCH-RESULT.json',dict(status='PASS',commands=commands,forward_all14_exact=True,reverse_all14_exact=True,own_stand_removed=True,actual_repository_mutated=False))
sr=put(R/'STRUCTURE-RESULT.json',dict(status='PASS',checks=checks,count=len(checks),source_files=14,changed_files=8,unchanged_files=6,shared_helpers_AST_identical=True,source_freeze=f,diff=ref(R/'SOURCE.patch'),R1_delta=ref(R/'REVISION1-TO-REVISION2.patch'),patch=pr))
print(json.dumps(dict(source_freeze=f,branch_freezes=branches,structure=sr,diff=ref(R/'SOURCE.patch'),R1_delta=ref(R/'REVISION1-TO-REVISION2.patch')),sort_keys=True))
