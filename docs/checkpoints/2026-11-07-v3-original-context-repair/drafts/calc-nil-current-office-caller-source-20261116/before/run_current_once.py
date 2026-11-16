"""Root-only one new readonly metric observation; original finite budget unchanged."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio,runpy,json,hashlib,os,time,subprocess,fcntl,stat,argparse
os.umask(0o077)
B=Path(__file__).resolve().parent
A=Path('/home/jericho/.cache/FRW-ASTRA-OWNC-POSTEXIT-ROOT-QUALIFICATION-20261116')
M=Path('/home/jericho/.cache/FRW-ASTRA-MAPPED-BOOTSTRAP-ROOT-QUALIFICATION-20261116')
P=Path('/home/jericho/.cache/FRW-ASTRA-CURRENT-OFFICE-M-ROOT-20261116')
E=Path('/home/jericho/.cache/FRW-ASTRA-EXTRA-FORK-WORKER-ROOT-QUALIFICATION-20261116')
Q=Path('/home/jericho/.cache/FRW-ASTRA-CALC-REFERENCE-OBSERVER-ROOT-20261115')
S=Path('/home/jericho/.cache/FRW-ASTRA-LOCALE-CONTRACT-FINAL-COMPOSITION-20261116')
F=Path('/home/jericho/.cache/FRW-ASTRA-MAPPED-BOOTSTRAP-OFFICE-M-ROOT-20261116')
L=Path('/home/jericho/.cache/FRW-ASTRA-OWNC-LOCALE-LANGUAGE-ACTUAL-20261116-887c410232d4')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':str(p),'sha256':sha(p)}
parser=argparse.ArgumentParser(description='Root-only exact locale Source acceptance and OwnC closure pins; no default approval')
parser.add_argument('--root-source-accepted',required=True)
parser.add_argument('--root-source-accepted-sha256',required=True)
parser.add_argument('--root-locale-closed',required=True)
parser.add_argument('--root-locale-closed-sha256',required=True)
args=parser.parse_args()
for pin in (args.root_source_accepted_sha256,args.root_locale_closed_sha256):assert len(pin)==64 and all(c in '0123456789abcdef' for c in pin)
source_accepted=Path(args.root_source_accepted);locale_closed=Path(args.root_locale_closed)
assert sha(source_accepted)==args.root_source_accepted_sha256
assert sha(locale_closed)==args.root_locale_closed_sha256
ident=json.loads((B/'PREPARED-ACTUAL-IDENTITY.json').read_text())
assert ref(source_accepted)==ident['locale_source_accepted_ref'] and ref(locale_closed)==ident['locale_qualified_closed_ref']
op=Path(ident['operation_dir']);planpath=Path(ident['plan_ref']['path']);plan_sha=ident['plan_ref']['sha256']
outer=Path(ident['outer_ref']['path'])
assert sha(planpath)==plan_sha and sha(outer)=='8f162630ab2922a75a93c79476730a7a34e34e869aa4b1eaa587b6c8d01933a1'
plan=json.loads(planpath.read_text());assert plan['operation_id']==ident['operation_id']
assert not(op/'consumed-once.json').exists() and not list((op/'work').iterdir())
def put(path,value):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:
  json.dump(value,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return ref(path)
def facts(p):
 s=p.lstat();return {'device':s.st_dev,'inode':s.st_ino,'uid':s.st_uid,'mode':format(stat.S_IMODE(s.st_mode),'04o'),'nlink':s.st_nlink,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
async def current_and_admit():
 C=runpy.run_path('/home/jericho/.jericho/runtime/sol-link-native-control.py')['NativeControl']
 async with C('astra') as c:
  g=(await c.call('thread/goal/get',{'threadId':c.thread}))['goal']
  queue=await c.call('thread/queue/list',{'threadId':c.thread,'limit':100})
  assert g['threadId']=='01a1c688-e36d-7021-8df4-9c5644a4d75b' and g['status']=='active' and g['createdAt']==1794332322
  assert not queue['data'] and queue.get('nextCursor') is None
 assert sha(E/'ROOT-MISSING-POSTINIT-EXTRA-FORK-EXPECTED-NEGATIVE-ACCEPTED.json')=='f6b82e49fd667b686d4718a5015b3dfc79951c37ea39f3f6fc3cc499c451a672'
 assert sha(M/'ROOT-PRODUCTION15-SOURCE-ACCEPTED.json')=='7e8b41e6e2ec48a9b6fa36268ef17849cef5de920c3cf0cedf1fd94a2927b23d'
 assert ref(M/'ROOT-PRODUCTION15-SOURCE-ACCEPTED.json')==ident['source_accepted_ref']
 qualified=M/'ROOT-MAPPED-POSTPAPER-OWNC-QUALIFIED-CLOSED.json'
 assert sha(qualified)=='c6bc47e38964d65cb92b2a9f2582a2c04fda88bf9ed8934753b536531c533fd7' and ref(qualified)==ident['changed_boundary_qualification_ref']
 prior_closed=P/'ROOT-CURRENT-OFFICE-LOAD-UNEXPECTED-FORK-50AA-CLOSED.json'
 assert sha(prior_closed)=='0a5b0529f998d66ebb5728e86bd7d92be5f5727c1f2282ec9631438569b11bff' and ref(prior_closed)==ident['prior_50aa_closed_ref']
 assert sha(S/'RESULT.json')=='5bd9bad045317246ce5d684795169a68dd6e4a5511938ceb67a8c92d23851e13'
 assert sha(S/'FINAL-FREEZE.json')=='4c8e9b3cc0edbd7c709b84f570085c5fe851c695ccc6e9a6be748df1bd082ff8'
 prior_f59e=F/'ROOT-CURRENT-OFFICE-F59E-ENV-PROFILE-REFUSAL-CLOSED.json'
 f59e_partial=F/'ROOT-F59E-PARTIAL-HELPER-EFFECT-CLARIFICATION.json'
 locale_actual=L/'ROOT-RESULT.json'
 assert sha(prior_f59e)=='57dcdd41503479a931a1dc4099cf81997695e1a609ac6e18ac9287891a265b29'
 assert sha(f59e_partial)=='7c168805fbb6f7c44d9cdd0e6069d0baa0f893e4a00df1546223dc70a1a21033'
 assert sha(locale_actual)=='5fe06a4b538a8c6a4ff7b333579c9e2e81606ed2bc38f23ccc4b2e9813d48187'
 assert ref(S/'RESULT.json')==ident['locale_source_result_ref'] and ref(S/'FINAL-FREEZE.json')==ident['locale_source_freeze_ref']
 assert ref(prior_f59e)==ident['prior_f59e_closed_ref'] and ref(f59e_partial)==ident['prior_f59e_partial_effect_ref'] and ref(locale_actual)==ident['locale_actual_ref']
 assert ref(source_accepted)==ident['locale_source_accepted_ref'] and ref(locale_closed)==ident['locale_qualified_closed_ref']
 services=[]
 for unit in ['hermes-gateway-1b7e7667.service','hermes-dashboard.service']:
  r=subprocess.run(['systemctl','--user','show',unit,'--property=Id,ActiveState,SubState,MainPID,InvocationID,RuntimeMaxUSec,NRestarts'],check=True,capture_output=True,text=True,timeout=10)
  v=dict(x.split('=',1) for x in r.stdout.splitlines());assert v['ActiveState']=='active' and v['SubState']=='running' and v['RuntimeMaxUSec']=='infinity'
  v['birth_ticks']=int(Path('/proc/'+v['MainPID']+'/stat').read_text().rsplit(')',1)[1].split()[19]);services.append(v)
 assert sha(H/'FRIDAY-INSTALL.json')=='1abce3b2307212c9c03d1494e09ed037ddc55903561ce5c66de06dceafb21f80'
 assert sha(H/'hermes-agent/install-stamp.json')=='6a40da2f2b5041a33dc998d7ce659a9c599a883b9eadf6c1b16eda7a319606be'
 lock=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
 fd=os.open(lock,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and not(s.st_mode&0o022)
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);lockfacts={'dev':s.st_dev,'ino':s.st_ino,'uid':s.st_uid,'nlink':s.st_nlink,'available_at_probe':True,'executor_reacquires':True};fcntl.flock(fd,fcntl.LOCK_UN)
 finally:os.close(fd)
 original=[]
 for item in plan['source_files']:
  p=Path(item['path']);before=facts(p);raw=p.read_bytes();assert facts(p)==before and hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==16538;original.append({'ref':item,'stamp':before})
 mem={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith(('MemAvailable:','SwapFree:'))}
 assert int(mem['MemAvailable'].split()[0])*1024>2*plan['budgets']['memory_bytes']
 assert os.statvfs(op).f_bavail*os.statvfs(op).f_frsize>1024**3
 passive=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-EXIT-PROFILE-ROOT-QUALIFICATION-20261115/ROOT-PASSIVE-STATIC-INPUTS-VERIFIED.json')
 assert sha(passive)=='9a11fed88576ca42d91b987b45e5ed0e8104c6f41ad54dba5437d6465d2e3b47'
 def stamp(s):return dict(dev_major=os.major(s.st_dev),dev_minor=os.minor(s.st_dev),ino=s.st_ino,uid=s.st_uid,mode=s.st_mode,size=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,nlink=s.st_nlink)
 backing=json.loads(passive.read_text())['profile']['files']
 for image in backing:assert stamp(Path(image['path']).lstat())==image['host_stamp']
 prior=json.loads(qualified.read_text())['unit_now']['Id']
 assert prior=='frw-helper-fixture-fbf7edf7db35cfb56a9b4f10b43fbca2.service'
 z=subprocess.run(['systemctl','--user','show',prior,'--property=LoadState,MainPID,ControlGroup'],check=True,capture_output=True,text=True,timeout=10)
 assert dict(x.split('=',1) for x in z.stdout.splitlines())=={'LoadState':'not-found','MainPID':'0','ControlGroup':''}
 retired_units={}
 for retired in (json.loads(prior_f59e.read_text())['after_exact_unit']['Id'],json.loads(locale_actual.read_text())['monitor']['unit']):
  assert retired in ('frw-calc-f59e9ed12df6adee84b3741224485096.service','frw-helper-fixture-887c410232d4c2aca3ee058ac1a30bec.service')
  retired_now=subprocess.run(['systemctl','--user','show',retired,'--property=LoadState,MainPID,ControlGroup'],check=True,capture_output=True,text=True,timeout=10)
  retired_units[retired]=dict(x.split('=',1) for x in retired_now.stdout.splitlines())
  assert retired_units[retired]=={'LoadState':'not-found','MainPID':'0','ControlGroup':''}
 assert set(retired_units)=={'frw-calc-f59e9ed12df6adee84b3741224485096.service','frw-helper-fixture-887c410232d4c2aca3ee058ac1a30bec.service'}
 snapshot={'schema':'frw.Root.calc-current-boundary-observations.v1','at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'goal':{k:g[k] for k in ['threadId','status','createdAt']},'Root_queue_empty':True,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'services':services,'installed224_unchanged':True,'DB_TG_refreshed':False,'source_current':original,'plan_ref':ref(planpath),'outer_ref':ref(outer),'work_empty':not list((op/'work').iterdir()),'ONCE_absent':not(op/'consumed-once.json').exists(),'exclusive_slot_probe':lockfacts,'resources':{'affinity':sorted(os.sched_getaffinity(0)),'meminfo':mem,'pressure':{k:Path('/proc/pressure',k).read_text().strip() for k in ['cpu','memory','io']}},'last_consumed_qualified_unit_ref':ref(qualified),'last_consumed_unit_current_absence':dict(x.split('=',1) for x in z.stdout.splitlines()),'prior_50aa_closed_ref':ref(prior_closed),'locale_source_accepted_ref':ref(source_accepted),'locale_qualified_closed_ref':ref(locale_closed),'locale_source_result_ref':ref(S/'RESULT.json'),'locale_source_freeze_ref':ref(S/'FINAL-FREEZE.json'),'prior_f59e_closed_ref':ref(prior_f59e),'prior_f59e_partial_effect_ref':ref(f59e_partial),'locale_actual_ref':ref(locale_actual),'f59e_and_locale_OwnC_units_current_absence':retired_units,'static14_backing_CAS_current':True,'byte_hash_proof_reused':ref(passive),'immutable_proofs_reused_no_rehash_repeat':True,'cancel':'Native goal active/no owner pause; executor repeats actual mutable guards under slot and owns finite operation/whole unit cleanup.','future_native64_raw32_M_fonts_restore_close_cleanup':None,'scope':'Only new private readonly load/font/reference/native10 observation; no render/store/draw/conversion/user/model/send/stop or product services/data mutation.','repeat_basis':ident['repeat_basis']}
 cr=put(op/'current-boundary-observations.json',snapshot)
 evidence=[ref(source_accepted),ref(locale_closed),ref(S/'RESULT.json'),ref(S/'FINAL-FREEZE.json'),ref(prior_f59e),ref(f59e_partial),ref(locale_actual),ref(M/'ROOT-PRODUCTION15-SOURCE-ACCEPTED.json'),ref(qualified),ref(prior_closed),ref(E/'ROOT-MISSING-POSTINIT-EXTRA-FORK-EXPECTED-NEGATIVE-ACCEPTED.json'),ref(A/'ROOT-FORBIDDEN-GPG-HOME-EXPECTED-NEGATIVE-ACCEPTED-CLOSED.json'),ref(A/'ROOT-WRONG-GPGCONF-SAME-BYTES-EXPECTED-NEGATIVE-ACCEPTED.json'),ref(Path('/home/jericho/.cache/FRW-ASTRA-OWNC-PUBLICATION-CUSTODY-ROOT-QUALIFICATION-20261116/ROOT-C400-SAME-ARTIFACT-DERIVED-POSITIVE-ACCEPTED.json')),ident['whole_preflight_ref'],ref(Q/'ROOT-SOURCE-LINK-ACCEPTED.json')]
 now=int(time.time());refs={}
 for kind,decision in [('current','CURRENT_EXACT_ROOT_PARAMETERS'),('readiness','SOURCE_REVIEWED_READY_FOR_SEPARATE_ADMISSION'),('admission','ADMIT_EXACT_OPERATION_ONCE')]:
  ers=[cr,ref(planpath)] if kind=='current' else evidence if kind=='readiness' else [refs['current'],refs['readiness'],cr]
  refs[kind]=put(op/(kind+'-Root-authority.json'),{'schema':'frw.calc.Root.'+kind+'.v1','operation_id':ident['operation_id'],'nonce':ident['nonce'],'plan_sha256':plan_sha,'issuer_scope':'Root','decision':decision,'effect':'ONE_PRIVATE_READONLY_CALC_LOAD_FONT_QUERY_NATIVE_TRACE','issued_unix':now,'expires_unix':now+300,'evidence_refs':ers})
 auth=put(op/'authority-refs.json',refs)
 put(op/'Root-admission-scope.json',{'at_moscow':snapshot['at_moscow'],'authority_origin':'Existing owner autonomous authorization plus Root actual source/helper reviews/current decision. Protected records describe this decision, not a new authentication mechanism.','repeat_basis':ident['repeat_basis'],'plan_ref':ref(planpath),'authority_refs':auth,'budget':plan['budgets'],'actual_future_results_not_prepassed':True,'Root_only_live_integrator':True,'no_other_actor_admitted':True})
 return auth
auth=asyncio.run(current_and_admit())
out=op/'actor.stdout.json';err=op/'actor.stderr.txt'
fo=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);fe=os.open(err,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try:
 p=subprocess.Popen(['/usr/bin/python3','-I','-B','-S',str(outer),'--execute-once','--input',str(planpath),'--input-sha256',plan_sha,'--authority-refs',auth['path'],'--authority-refs-sha256',auth['sha256']],stdin=subprocess.DEVNULL,stdout=fo,stderr=fe,start_new_session=True,close_fds=True)
finally:os.close(fo);os.close(fe)
birth=int(Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19])
ar=put(op/'Root-actor-start.json',{'at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'pid':p.pid,'birth_ticks':birth,'unit':'frw-calc-'+ident['nonce']+'.service','plan_ref':ref(planpath),'outer_ref':ref(outer),'authority_refs':auth,'finite_budget':plan['budgets'],'observation_timeout260_is_emergency_only_not_consumer_budget_extension':True})
print(json.dumps({'event':'ROOT_CURRENT_M_ACTOR_STARTED','pid':p.pid,'birth_ticks':birth,'operation_dir':str(op),'actor_ref':ar}),flush=True)
try:code=p.wait(timeout=260)
except subprocess.TimeoutExpired:
 p.terminate()
 try:code=p.wait(timeout=2)
 except subprocess.TimeoutExpired:p.kill();code=p.wait(timeout=2)
 put(op/'Root-wrapper-emergency-unknown.json',{'at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'status':'UNKNOWN_OUTER_OVERRAN_OBSERVATION_NO_M_RELEASE','actor_pid':p.pid,'actor_birth_ticks':birth,'actor_reaped':True,'owned_unit_reconciliation_required':True,'original_clock_not_extended':True})
 print(json.dumps({'event':'ROOT_ACTOR_TIMEOUT_UNKNOWN','code':code}),flush=True);raise SystemExit(3)
terminal={'at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'pid':p.pid,'birth_ticks':birth,'returncode':code,'actor_reaped':True,'actor_absent':not Path('/proc/'+str(p.pid)).exists(),'stdout_bytes':out.stat().st_size,'stderr_bytes':err.stat().st_size}
put(op/'Root-actor-terminal.json',terminal)
print(json.dumps({'event':'ROOT_CURRENT_M_ACTOR_TERMINAL',**terminal}),flush=True)
raise SystemExit(code)
