"""Inert import; explicit bounded frozen-source verification only. No runtime grant."""
from pathlib import Path
import hashlib,json,os,stat,sys
B=Path(__file__).parent

def verify(path,digest):
 p=Path(path);s=p.lstat()
 if not(stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1 and not any(x.is_symlink()for x in(p,*p.parents))):raise ValueError('unsafe_source_ref:'+str(p))
 if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('source_changed:'+str(p))

def main():
 if not(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv)==4 and sys.argv[1:3]==['--check-frozen-source','--source-pins-sha256']):raise ValueError('explicit_isolated_source_check_required')
 verify(B/'SOURCE-PINS.json',sys.argv[3]);v=json.loads((B/'SOURCE-PINS.json').read_bytes())
 if v['schema']!='frw.root211.coherent-after-actual210-source-pins.v1' or v['frame']!=str(B)or v['runtime_grant']is not False:raise ValueError('exact_inert211_frame_required')
 for p,d in {**v['source_refs'],**v['historical_refs']}.items():verify(p,d)
 print(json.dumps({'state':'PASS_FROZEN_SOURCE_ONLY_NO_EXECUTION_GRANT','source_refs':len(v['source_refs']),'historical_refs':len(v['historical_refs'])}))

if __name__=='__main__':main()
