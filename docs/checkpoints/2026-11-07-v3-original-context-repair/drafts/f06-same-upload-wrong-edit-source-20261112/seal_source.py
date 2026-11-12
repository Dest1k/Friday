from pathlib import Path
import ast,difflib,hashlib,json
B=Path(__file__).resolve().parent;C=B/'candidate'
def enc(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
leaves=['f06_source.py','f06_footer.py.txt','first_ingress.py','current_root.py','root_bind_dispatch_once.py'];pins={};chunks=[]
for name in leaves:
 before=(B/'before'/name).read_bytes();after=(C/name).read_bytes()
 if name.endswith('.py'):ast.parse(after,feature_version=(3,12))
 pins[name]={'before':{'bytes':len(before),'sha256':sha(before)},'after':{'bytes':len(after),'sha256':sha(after)},'changed':before!=after,'origin':'Task29 canonical correct-read five-file branch; Task30 changed source only'}
 chunks.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
freeze={'schema':'frw.F06.ordinary-singleton.source-freeze.v1','files':{name:pins[name]['after'] for name in leaves}}
for path,raw in [(C/'SOURCE-FREEZE.json',enc(freeze)),(B/'SOURCE-PINS.json',enc({'assignment':'ASTRA-SOL-V3-F06-SAME-UPLOAD-WRONG-EDIT-SOURCE-20261112#1','source_only':True,'actual_user_NOT_RUN':True,'native_product_targets':0,'files':pins})),(B/'SOURCE.patch',''.join(chunks).encode())]:
 with path.open('xb') as f:f.write(raw)
 print(json.dumps({'path':str(path),'bytes':len(raw),'sha256':sha(raw)}))
