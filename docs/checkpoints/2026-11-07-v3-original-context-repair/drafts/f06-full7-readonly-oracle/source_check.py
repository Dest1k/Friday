"""Audit-fenced own-source plumbing checks; no live or fixture content reads."""
import json,os,resource,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_AS,(2147483648,2147483648))
refs=json.loads((B/'REFERENCES.json').read_text());allowed={r['path'] for r in refs['files']}
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
sys.path.insert(0,str(B))
import root_frame,source_controls,f06_contract as c
start=time.monotonic();cpu=time.process_time()
source=root_frame.offline_check();controls=source_controls.run()
result=dict(state='AUDIT_FENCED_VERIFY_INPUTS_SOURCE_CHECK_PASS',source=source,controls=controls,elapsed_seconds=time.monotonic()-start,CPU_seconds=time.process_time()-cpu,home_content_reads=sorted({p for p in reads if p.startswith('/home/jericho/')}),audit_denials=denials,actual_runtime_state_reads=0,credential_content_reads=0,ciphertext_content_reads=0,Office_starts=0,unit_starts=0,namespace_starts=0,runtime_or_application_PASS=False)
c.save(B/'AUDIT-SOURCE-CHECK.json',result)
print(json.dumps({k:result[k] for k in ('state','elapsed_seconds','credential_content_reads','ciphertext_content_reads','actual_runtime_state_reads')}))
