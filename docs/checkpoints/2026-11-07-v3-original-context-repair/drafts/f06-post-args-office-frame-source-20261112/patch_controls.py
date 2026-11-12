"""Real source patch forward/reverse, isolated own eleven-file stand only."""
import hashlib,json,pathlib,subprocess,tempfile
B=pathlib.Path(__file__).resolve().parent;C=B/'candidate';M=json.loads((B/'COMPOSITION-MAP.json').read_bytes());checks=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(dir=B,prefix='source-patch-stand-')as temp:
 D=pathlib.Path(temp)
 for row in M['files']:(D/row['name']).write_bytes(pathlib.Path(row['task25_origin']['path']).read_bytes())
 for reverse,label,target in ((False,'forward','after'),(True,'reverse','task25_origin')):
  args=['/usr/bin/patch','--batch','--fuzz=0','-p1','--input',str(B/'POST-ARGS-COMPOSITION.patch')]+(['--reverse']if reverse else[])
  p=subprocess.run(args,cwd=D,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
  assert p.returncode==0 and all(digest(D/r['name'])==r[target]['sha256']for r in M['files']);checks.append(dict(name='real_patch_'+label,passed=True))
 # Deliberately corrupt changed preimage: no implicit fuzzy acceptance.
 (D/'request_args_compat_v2.py').write_text('foreign source\n')
 p=subprocess.run(['/usr/bin/patch','--batch','--fuzz=0','-p1','--dry-run','--input',str(B/'POST-ARGS-COMPOSITION.patch')],cwd=D,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
 assert p.returncode!=0;checks.append(dict(name='foreign_preimage_refused',passed=True))
assert not pathlib.Path(temp).exists();checks.append(dict(name='owned_patch_stand_removed',passed=True))
print(json.dumps(dict(schema='post-args.patch-source-controls.v1',checks=checks,count=len(checks),all_pass=True,source_only=True,all_children_waited=True,temporary_stand_removed=True)))
