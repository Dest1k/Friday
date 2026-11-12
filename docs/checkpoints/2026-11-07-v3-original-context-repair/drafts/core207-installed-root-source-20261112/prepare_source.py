"""Inert source-freeze checker. Never builds requests, binds runtime or imports actors."""
from pathlib import Path
import argparse,hashlib,json,os,stat
B=Path(__file__).resolve().parent
def checked(path):
 p=Path(path);s=p.lstat()
 if not(stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1 and not any(x.is_symlink()for x in (p,*p.parents))):raise ValueError('owned_source_required')
 return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(expected):
 if checked(B/'SOURCE-PINS.json')!=expected:raise ValueError('external_source_digest_changed')
 v=json.loads((B/'SOURCE-PINS.json').read_bytes())
 if v['schema']!='frw.root207.coherent-after-actual206-source-pins.v1' or v['runtime_grant']is not False:raise ValueError('exact_source_domain_required')
 for p,d in {**v['source_refs'],**v['historical_refs']}.items():
  if checked(p)!=d:raise ValueError('source_changed:'+p)
 return dict(state='FROZEN_SOURCE_ONLY_VERIFIED_NO_RUNTIME_GRANT',references=len(v['source_refs'])+len(v['historical_refs']),runtime_grant=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check-frozen-source',action='store_true',required=True);p.add_argument('--source-pins-sha256',required=True);a=p.parse_args();print(json.dumps(validate(a.source_pins_sha256)))
if __name__=='__main__':main()
