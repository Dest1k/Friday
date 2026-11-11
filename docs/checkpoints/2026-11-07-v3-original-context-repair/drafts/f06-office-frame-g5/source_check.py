"""Audit-fenced source-only check; exact existing proof/plain inputs only."""
import json,os,resource,runpy,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648))
refs=json.loads((B/'REFERENCES.json').read_text());allowed={r['path'] for r in refs['files']}
P=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ENCRYPTED-INPUTS-PREP-20261111')
allowed|={str(P/'plain-inputs'/('f06-new-plain.'+f)) for f in ('docx','xlsx','pptx','odt','ods','odp')}
reads=[];denials=[]
def audit(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.__new__'):
  denials.append(event);raise RuntimeError('SOURCE_ONLY_EXECUTION_DENIED')
 if event in ('open','os.listdir','os.scandir'):
  raw=args[0]
  if isinstance(raw,(str,bytes,os.PathLike)):
   p=os.fsdecode(raw)
   if p.startswith('/home/jericho/') and not (p==str(B) or p.startswith(str(B)+'/') or p in allowed):
    denials.append((event,p));raise RuntimeError('SOURCE_ONLY_HOME_READ_OUTSIDE_EXACT_ALLOWLIST')
   if event=='open':reads.append(p)
sys.addaudithook(audit)
start=time.monotonic();cpu=time.process_time();sys.argv=[str(B/'root_frame.py'),'--check'];rc=0
try:runpy.run_path(str(B/'root_frame.py'),run_name='__main__')
except SystemExit as exc:rc=exc.code
if rc!=0:raise RuntimeError('SOURCE_ONLY_CHECK_FAILED')
result=dict(state='AUDIT_FENCED_SOURCE_CHECK_PASS',exit=rc,elapsed_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu,home_content_reads=sorted({p for p in reads if p.startswith('/home/jericho/')}),audit_denials=denials,actual_runtime_state_reads=0,secret_reads=0,Office_starts=0,unit_starts=0,namespace_starts=0,all_read_FDs_closed=True)
(B/'AUDIT-SOURCE-CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('state','elapsed_seconds','secret_reads','actual_runtime_state_reads')}))
