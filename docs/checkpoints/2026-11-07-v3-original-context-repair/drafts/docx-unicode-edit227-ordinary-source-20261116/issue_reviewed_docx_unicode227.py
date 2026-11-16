"""Root issuance after exact bound Source review; no API, ONCE or clock."""
from pathlib import Path
import hashlib,json,os,stat,time,types,sys
if not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode or not sys.flags.no_site:
 raise SystemExit('Root issuer requires nonoptimized isolated -I -B -S; no authority issued')
os.umask(0o077)
N=Path(__file__).parent
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
def need(ok,why):
 if not ok:raise ValueError(why)
def ref(p):
 raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(p,v):
 raw=(json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return ref(p)
def module(r,name):
 p=Path(r['path']);need(ref(p)==r,'Exact Source required');m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 need(len(sys.argv)==4,'Explicit bundle SHA, review path and review SHA required')
 bp=N/'ROOT-DOCX227-EXACT-SOURCE-BINDINGS.json';rp=Path(sys.argv[2])
 need(ref(bp)['sha256']==sys.argv[1]and ref(rp)['sha256']==sys.argv[3],'Exact accepted bundle/review required')
 bundle=json.loads(bp.read_bytes());s=bundle['sources'];run=bundle['run_id'];B=N/'bindings';W=N/'operation'
 need(run=='f03-docx-unicode-first-responsible-copy-edit-01-20261116','Original missing operation required')
 for r in s.values():need(ref(Path(r['path']))==r,'Bound source drift')
 review=json.loads(rp.read_bytes());need(review['decision']=='PASS_SOURCE_READY_ROOT_BINDINGS_REQUIRED'and review['open_critical_defects']==[],'Independent review required')
 for k in ('actor','current_checker','preparation','scenario'):need(s[k]in review['reviewed_sources'],'Exact source missing from review')
 need(ref(Path(__file__))in review['reviewed_sources'],'Issuer delta must be reviewed')
 base=json.loads(Path(s['baseline']['path']).read_bytes());scenario=json.loads(Path(s['scenario']['path']).read_bytes())
 history={r['id']:dict(sha256=r['sha256'],status=r['status'],send_state=r['send_state'],deadline=r['deadline'],new_effect_replay_authorized=False,unknown_retained=r['send_state']=='unknown')for r in base['history']}
 need(len(history)==532 and sum(r['unknown_retained']for r in history.values())==3,'Original history and unknowns required')
 need({p.stem for p in(STATE/'runs').glob('*.json')}==set(history),'Current history delta requires assessment')
 for k,row in history.items():need(ref(STATE/'runs'/(k+'.json'))['sha256']==row['sha256'],'Historical row changed')
 need(not(STATE/'runs'/(run+'.json')).exists(),'Missing operation already has a run')
 prep=module(s['preparation'],'RootActualDOCXUnicode227Prep');prep.validate_scenario_data(scenario)
 current=module(s['current_checker'],'RootActualDOCXUnicode227Current')
 current.validate_eligibility(json.loads(Path(s['eligibility']['path']).read_bytes()))
 current.validate_installed227_assessment(json.loads(Path(s['installed227']['path']).read_bytes()))
 now=time.time();gw=base['native']['identity']
 authority=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,authority_id='docx-original-F03-Unicode-edit227-20261116',run_scenarios={run:s['scenario']['sha256']},created_at=now,expires_at=now+600,boot_id=gw['boot_id'],gateway=dict(state_path=str(Path(base['canonical']['marker']['path']).parent/'gateway_state.json'),pid=gw['pid'],start_time=gw['start_time'],maximum_staleness_seconds=120),history=history,unknown_effects_resolved=False,old_rows_modified=False,new_trial_for_historical_task=False,product_or_B00_acceptance=False,no_old_task_replay=True,new_independent_inputs_only=True,ordered_predecessors={},docx_unicode227_original_case=prep.ORIGINAL_CASE,docx_unicode227_upload_input=current.UPLOAD_INPUT,docx_unicode227_effect_eligibility=s['eligibility'],docx_unicode227_installed227_assessment=s['installed227'],docx_unicode227_future_postconditions=prep.FUTURE_POSTCONDITIONS)
 authref=write(B/'ROOT-AUTHORITY.json',authority)
 prep.validate_authority_shape(authority,authref,run_id=run,scenario=scenario)
 oldp=Path('/home/jericho/.cache/FRW-ASTRA-EML-FIRST-READ-PREPARATION-20261116/bindings/ROOT-BOUND-DESCRIPTOR.json')
 need(ref(oldp)==dict(path=str(oldp),bytes=4843,sha256='38c82bea890516368f34fc9fd2d5037d31c78452a181dd070cce7178fb10b664'),'Retained descriptor and disk scope Source drift')
 old=json.loads(oldp.read_bytes())
 for k in ('selected_tester','history_helper','readonly_history'):need(ref(Path(old[k]['path']))==old[k],'Retained consumer Source drift')
 disk=json.loads(json.dumps(old['disk_scope']));disk['directory_roots'][0]=str(W)
 slot=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock');st=slot.lstat()
 need(stat.S_ISREG(st.st_mode)and st.st_uid==os.getuid()and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and not any(q.is_symlink()for q in(slot,*slot.parents)),'Existing protected slot required')
 W.mkdir(mode=0o700);need(not list(W.iterdir()),'Empty owned operation directory required')
 v=dict(schema='frw.Root.DOCX-Unicode227.once-driver-binding.v1',operator='Root',run_id=run,native_python=bundle['native_python'],actor=s['actor'],current_checker=s['current_checker'],preparation=s['preparation'],selected_tester=old['selected_tester'],history_helper=old['history_helper'],readonly_history=old['readonly_history'],review=ref(rp),authority=authref,scenario=s['scenario'],scenario_sha256=s['scenario']['sha256'],workdir=str(W),binding_dir=str(B),resources=bundle['resources'],slot_identity=dict(device=st.st_dev,inode=st.st_ino,uid=st.st_uid,mode=stat.S_IMODE(st.st_mode),nlink=st.st_nlink),disk_scope=disk,private_roots=[str(N),str(Path(s['preparation']['path']).parent),str(rp.parent)])
 r=write(B/'ROOT-BOUND-DESCRIPTOR.json',v)
 actor=module(s['actor'],'RootActualDOCXUnicode227Actor');actor.sources(v,actor.helper())
 print(json.dumps(dict(state='ACTUAL_REVIEWED_ROOT_BINDINGS_NO_API_NO_ONCE_NO_CLOCK',descriptor=r,authority_expires_at=now+600,history=532,unknowns=3,resources=v['resources'])))
if __name__=='__main__':main()
