"""Exact source of final externally launched finite control batch.

Archived after the tool invocation for reproducibility. It was not present as a
file at invocation. Result limits describe this launch policy, not measured
aggregate cgroup/process-tree enforcement. No actual helper/consumer is launched.
Requires fresh case names; do not rerun consumed fixture directories.
"""
from pathlib import Path
import subprocess,json,concurrent.futures,time,resource,os,hashlib
P=Path('/home/jericho/.cache/FRW-ASTRA-PREPARE-T29-FIRST-CONSUMER-ROOT-FINALIZER-20261112/controls')
cases=['positive','source_drift_f06_source.py','source_drift_f06_footer.py.txt','source_drift_current207.py','source_drift_root_bind_existing_consumer_once.py','root_acceptance_drift','first_review_wrong_freeze','root_plan_hash','freeze_parse_CAS','code_drift_after_load','O_once_changed','X_binding_changed','X_dispatch_present','judgment_unknown','authority_expired','constructor_manager','private_root_intersection','final_review_code_hash','bulk_contract_drift','prior_work_once','prior_new_clock','current_changed','carrier_symlink']
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def run(case):
 r=subprocess.run(['python3','-I','-B','-S',str(P/'control.py'),'final-'+case,case,'first'],capture_output=True,text=True,timeout=30,preexec_fn=limits)
 for ext,data in [('stdout',r.stdout),('stderr',r.stderr)]:
  q=P/('final-'+case+'.'+ext);q.write_text(data);q.chmod(0o600)
 if r.returncode:return {'control':case,'exit':r.returncode,'stderr':r.stderr[-1200:]}
 return {'control':case,'exit':0,'result':ref(P/'cases'/('final-'+case)/'RESULT.json'),'observed':json.loads((P/'cases'/('final-'+case)/'RESULT.json').read_bytes())}
if __name__=='__main__':
 start=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(run,cases))
 assert all(r['exit']==0 for r in rs),rs
 print(json.dumps({'elapsed_seconds':time.monotonic()-start,'results':rs}))
