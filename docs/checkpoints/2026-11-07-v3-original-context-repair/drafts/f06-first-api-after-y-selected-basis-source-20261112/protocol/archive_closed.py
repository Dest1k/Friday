"""Losslessly compress closed own synthetic fixtures, preserving direct result/audit/resources."""
from pathlib import Path
import hashlib,json,tarfile,os,sys
os.umask(0o077)
P=Path(__file__).resolve().parent
KEEP={'RESULT.json','RESOURCES.json','AUDIT-SUMMARY.json','FIXTURE-ARCHIVE.json','FIXTURE.tar.gz'}
def archive(case):
 assert case.parent==P/'cases' and case.is_dir() and not case.is_symlink()
 files=[f for f in case.rglob('*') if f.is_file() and f.name not in KEEP]
 if not files:return None
 target=case/'FIXTURE.tar.gz';assert not target.exists()
 inventory={str(f.relative_to(case)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files}
 with tarfile.open(target,'w:gz',compresslevel=6) as t:
  for f in files:t.add(f,arcname=str(f.relative_to(case)),recursive=False)
 target.chmod(0o600)
 with tarfile.open(target,'r:gz') as t:
  assert set(t.getnames())==set(inventory)
  for name,row in inventory.items():
   data=t.extractfile(name).read();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 manifest={'state':'CLOSED_SYNTHETIC_FIXTURE_LOSSLESSLY_ARCHIVED','archive':{'path':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},'raw_member_pins':inventory,'no_effect_replayed':True}
 (case/'FIXTURE-ARCHIVE.json').write_text(json.dumps(manifest,sort_keys=True)+'\n');(case/'FIXTURE-ARCHIVE.json').chmod(0o600)
 for f in files:f.unlink()
 for d in sorted([d for d in case.rglob('*') if d.is_dir()],key=lambda d:len(d.parts),reverse=True):
  if not any(d.iterdir()):d.rmdir()
 return manifest['archive']
if __name__=='__main__':
 for name in sys.argv[1:]:print(json.dumps({'case':name,'archive':archive(P/'cases'/name)}))
