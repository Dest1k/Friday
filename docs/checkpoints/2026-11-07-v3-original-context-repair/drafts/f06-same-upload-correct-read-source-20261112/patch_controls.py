"""Final own-cache source patch forward/reverse; no product/Git mutation."""
import ast,difflib,hashlib,json,os,shutil,subprocess,tempfile,types
from pathlib import Path
os.umask(0o077);B=Path(__file__).resolve().parent;V=B/'revision3';C=V/'candidate'
origin={'f06_source.py':'f06_source.py','f06_footer.py.txt':'f06_footer.py.txt','current_root.py':'current207.py','root_bind_dispatch_once.py':'root_bind_dispatch_once.py'}
before={k:(B/'baseline'/v).read_bytes() for k,v in origin.items()};after={p.name:p.read_bytes() for p in sorted(C.iterdir())};patch=''
for n,raw in after.items():patch+=''.join(difflib.unified_diff(before.get(n,b'').decode().splitlines(True),raw.decode().splitlines(True),fromfile='a/'+n if n in before else '/dev/null',tofile='b/'+n))
(V/'SOURCE.patch').write_text(patch)
stand=Path(tempfile.mkdtemp(prefix='patch-own-',dir=V))
commands=[]
try:
 for n,raw in before.items():(stand/n).write_bytes(raw)
 def run(args):
  r=subprocess.run(['/usr/bin/patch','-p1','--batch',*args],cwd=stand,input=patch.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
  commands.append(dict(argv=['patch','-p1','--batch',*args],exit_code=r.returncode,stdout_sha256=hashlib.sha256(r.stdout).hexdigest(),stderr_sha256=hashlib.sha256(r.stderr).hexdigest()));return r.returncode
 assert run(['--forward'])==0
 assert all((stand/n).read_bytes()==raw for n,raw in after.items())
 assert run(['--reverse'])==0
 assert all((stand/n).read_bytes()==raw for n,raw in before.items())
 assert not (stand/'first_ingress.py').exists()
 # Known altered preimage: exact original source consumer must not be replaced.
 (stand/'f06_source.py').write_bytes(b'WRONG_PREIMAGE\n');assert run(['--dry-run','--forward'])!=0
 checks=['source_forward_afterimage_exact5','source_reverse_beforeimage_exact4','new_firstvalidator_removed_on_reverse','known_wrong_preimage_refused']
finally:shutil.rmtree(stand)
# Grammar only under source contract Python3.12 compatible syntax.
for n,raw in after.items():
 if n.endswith('.py'):ast.parse(raw,feature_version=(3,12))
p=C/'f06_source.py';a=types.ModuleType('pure_final_adapter');a.__file__=str(p);exec(compile(after['f06_source.py'],str(p),'exec'),a.__dict__)
full=a.successor(a.BASE.read_bytes(),a.unbound(),after['f06_footer.py.txt']);(V/'bot_tester.f06.UNBOUND.py').write_bytes(full)
print(json.dumps(dict(state='PASS_OWN_SOURCE_PATCH_ONLY',checks=checks,commands=commands,stand_removed=not stand.exists(),patch_bytes=len(patch.encode()),patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),full_unbound_bytes=len(full),full_unbound_sha256=hashlib.sha256(full).hexdigest(),nativefiles_or_Office_or_actualfirst_authority_effects=0),sort_keys=True))
