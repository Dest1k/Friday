"""Finalize only own unfrozen206 source. Source edits are separate from Root bindings."""
from pathlib import Path
import ast,hashlib,json,os,re
B=Path(__file__).parent
os.umask(0o077)
assert not(B/'SOURCE-PINS.json').exists(),'frozen_source_refuses_modification'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def edit(n,f):
 p=B/n;p.write_text(f(p.read_text()));p.chmod(0o600)
def load(n):return json.loads((B/n).read_bytes())
def write(n,v):(B/n).write_bytes(encoded(v))
m=(B/'root206_metadata.py').read_text()
m=m.replace('def actual_predecessor():\n record=readref(reference(B/\'ROOT-ACTUAL205-PREDECESSOR.json\'))','def validate_predecessor_record(record):')
m=m.replace('def project_source_pins(request):',"def actual_predecessor():\n return validate_predecessor_record(readref(reference(B/'ROOT-ACTUAL205-PREDECESSOR.json')))\n\ndef project_source_pins(request):")
a=m.index(" require({row['path']for row in spec['native_files']}==");b=m.index(",\'exact_eleven_native_paths_required\')",a)
names=sorted(row['path']for row in json.loads(Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112/FINAL-NATIVE-SPEC.json').read_bytes())['native_files'])
m=m[:a]+" require({row['path']for row in spec['native_files']}==set("+repr(names)+")"+m[b:]
m=m.replace("'four_paths_no_native_absent_required'","'eleven_existing_paths_no_native_absent_required'").replace("'one_explicit_seventh_layer_required'","'one_explicit_eighth_layer_required'")
m=m.replace("for name,digest in public.items():require(sha(owned(repository/name))==digest,'current_public493_working_drift:'+name)","for name,digest in policy['reviewed_current_files'].items():require(sha(owned(repository/name))==digest,'current_public5_working_drift:'+name)")
(B/'root206_metadata.py').write_text(m)
edit('f06-206-first-actual-root.py',lambda t:t.replace("'exact206_tenCAS_required'","'exact206_seventeenCAS_required'").replace("reference='99f10f54e5e2989a3ec9c88b002d1fb3cacf4e3a'","reference='b86eb1693cdb51f9d3a1a8bd0f7b6f8f06b497cb'"))
# Exact Root admission source pins are static and acyclic: leafs before actor before template.
a=B/'run_native206_once.py';text=a.read_text()
text=re.sub(r"assert sha\(B / 'root206_metadata.py'\) == '[0-9a-f]{64}'","assert sha(B / 'root206_metadata.py') == '"+sha(B/'root206_metadata.py')+"'",text)
text=re.sub(r"assert sha\(RESTORE\) == '[0-9a-f]{64}'","assert sha(RESTORE) == '"+sha(B/'resume_native206_services.py')+"'",text);a.write_text(text)
v=load('ROOT-206-FRESH-ADMISSION-TEMPLATE.json')
for key,name in [('actor','run_native206_once.py'),('recovery','resume_native206_services.py')]:v[key]=dict(path=str(B/name),sha256=sha(B/name))
write('ROOT-206-FRESH-ADMISSION-TEMPLATE.json',v)
for p in B.rglob('*.py'):ast.parse(p.read_bytes(),filename=str(p));compile(p.read_bytes(),str(p),'exec')
for p in B.rglob('*'):
 if p.is_file():p.chmod(0o600)
 elif p.is_dir():p.chmod(0o700)
print(json.dumps(dict(state='FINAL_SOURCE_EDITED_NOT_FROZEN',metadata_sha256=sha(B/'root206_metadata.py'),actor_sha256=sha(a))))
