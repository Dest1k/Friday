import datetime, hashlib, json, math, os, re, resource, sys, time, types
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent.parent;OUT=B/'review';CASE=B/'protocol-stand/cases/positive'
START=time.monotonic();CPU=time.process_time();ROWS=[];READS=[]
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
def audit(event,args):
 if event=='open' and not isinstance(args[0],int):
  p=Path(os.path.abspath(os.fsdecode(args[0])));flags=args[2];write=isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if not p.is_relative_to(B) or write and not p.is_relative_to(OUT):raise AssertionError('REVIEW_IO_BOUNDARY')
 elif event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn') or event.startswith('socket.'):raise AssertionError('REVIEW_RUNTIME_EFFECT')
sys.addaudithook(audit)
raw=(B/'candidate/first_ingress.py').read_bytes();F=types.ModuleType('independent_timing_review');F.__file__=str(B/'candidate/first_ingress.py');exec(compile(raw,F.__file__,'exec'),F.__dict__);F.STATE=CASE/'SYNTHETIC-STATE'
def enc(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def fixture(which):
 c=json.loads((CASE/'SYNTHETIC-root-inputs.json').read_bytes())['contract'];data={};reads=[]
 def read(p,**kw):
  s=str(p);reads.append(s)
  if s not in data:data[s]=Path(s).read_bytes()
  return data[s]
 def doc(r):return json.loads(read(r['path']))
 def put(r,v):
  raw=enc(v);data[r['path']]=raw;return dict(path=r['path'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 def synthetic_clock(name):
  raw=enc({'SYNTHETIC_ONLY_UNREAD_OLD_CLOCK':name});p=str(OUT/('SYNTHETIC-NOT-WRITTEN-'+name+'.json'));data[p]=raw
  return dict(path=p,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 oldfirst,oldcorrect=synthetic_clock('oldfirst'),synthetic_clock('oldcorrect')
 first=doc(c['first_ingress']);binding=doc(first['first_binding']);binding['contract']['resources']={'clock':oldfirst};first['first_binding']=put(first['first_binding'],binding)
 close=doc(first['closure']);cust=doc(close['original_consumer_custody']);cust['first_binding']=first['first_binding'];close['original_consumer_custody']=put(close['original_consumer_custody'],cust);first['closure']=put(first['closure'],close)
 rec=doc(first['root_reconciliation']);rec.update(first_binding=first['first_binding'],closure=first['closure']);first['root_reconciliation']=put(first['root_reconciliation'],rec);c['root_proofs']['first_upload_reconciliation']=first['root_reconciliation'];c['first_ingress']=put(c['first_ingress'],first)
 correct=doc(c['correct_read']);binding=doc(correct['correct_binding']);binding['contract'].update(first_ingress=c['first_ingress'],resources={'clock':oldcorrect});correct['correct_binding']=put(correct['correct_binding'],binding)
 close=doc(correct['closure']);cust=doc(close['original_consumer_custody']);cust['correct_binding']=correct['correct_binding'];close['original_consumer_custody']=put(close['original_consumer_custody'],cust);close.update(correct_binding=correct['correct_binding'],clock=oldcorrect)
 if which=='wrong_closure_clock':close['clock']=oldfirst
 correct['closure']=put(correct['closure'],close)
 assessment=doc(correct['assessment']);assessment.update(correct_binding=correct['correct_binding'],original_consumer_custody=close['original_consumer_custody']);correct['assessment']=put(correct['assessment'],assessment)
 rec=doc(correct['root_reconciliation']);rec.update(correct_binding=correct['correct_binding'],closure=correct['closure'],assessment=correct['assessment']);correct['root_reconciliation']=put(correct['root_reconciliation'],rec);c['root_proofs']['correct_read_reconciliation']=correct['root_reconciliation'];c['correct_read']=put(c['correct_read'],correct)
 clock=doc(c['resources']['clock']);clock['started_at']=close['completed_at']
 if which=='before_closed':clock['started_at']=close['completed_at']-0.0001
 elif which=='started_bool':clock['started_at']=True
 elif which=='started_missing':del clock['started_at']
 elif which=='after_closed':clock['started_at']=close['completed_at']+1
 c['resources']['clock']=put(c['resources']['clock'],clock)
 if which=='reuse_oldcorrect':c['resources']['clock']=oldcorrect
 elif which=='reuse_oldfirst':c['resources']['clock']=oldfirst
 first=F.validate(c,read)
 before=len(reads)
 try:
  value=F.correct_read(c,read,first);error=None
 except ValueError as exc:value=None;error=str(exc)
 timing_reads=reads[before:];oldpaths={oldfirst['path'],oldcorrect['path']}
 if any(p in oldpaths for p in timing_reads):raise AssertionError('old clock body read')
 expected={'reuse_oldcorrect':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','reuse_oldfirst':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','wrong_closure_clock':'F06_NEW_WRONGEDIT_CLOCK_DISTINCT_FROM_CLOSED_OPERATIONS','before_closed':'F06_NEW_CLOCK_MUST_START_AFTER_CORRECT_READ_CLOSURE','started_bool':'F06_NEW_CLOCK_MUST_START_AFTER_CORRECT_READ_CLOSURE','started_missing':'F06_NEW_CLOCK_MUST_START_AFTER_CORRECT_READ_CLOSURE'}.get(which)
 if expected is None:
  if error is not None or value!=correct:raise AssertionError((which,error))
 else:
  if error!=expected:raise AssertionError((which,error,expected))
 return {'name':which,'result':'PASS' if expected is None else 'REFUSED_AS_REQUIRED','code':error,'old_clock_bodies_opened':False,'real_first_validator_used':True,'real_correct_validator_used':True,'synthetic_ref_enrichment_only':True}
for case in ('exact_closure_boundary','after_closed','reuse_oldcorrect','reuse_oldfirst','wrong_closure_clock','before_closed','started_bool','started_missing'):ROWS.append(fixture(case))
result={'schema':'frw.Sol.Task30.independent-timing-controls.v1','first_ingress_sha256':hashlib.sha256(raw).hexdigest(),'checks':ROWS,'actual_effects':'NOT_RUN','source_only':True,'synthetic_fixtures':True,'fixture':'Retained original synthetic protocol positive; consistent injected reference metadata enrichment in memory, no file/body mutation','old_clock_bodies_read':False,'limits':{'wall_seconds':90,'CPU_seconds':60,'AS_bytes':512*1024**2,'cpus':2},'elapsed_wall_seconds':time.monotonic()-START,'elapsed_cpu_seconds':time.process_time()-CPU,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
encoded=enc(result);(OUT/'timing-controls.json').write_bytes(encoded);print(json.dumps({'checks':len(ROWS),'first_ingress_sha256':result['first_ingress_sha256'],'sha256':hashlib.sha256(encoded).hexdigest(),'wall_seconds':result['elapsed_wall_seconds']}))
