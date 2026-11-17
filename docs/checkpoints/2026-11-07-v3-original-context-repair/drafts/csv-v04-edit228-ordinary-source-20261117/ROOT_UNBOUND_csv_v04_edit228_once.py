"""One original CSVv04 upload/edit with qualified MD227 owned monitor unchanged; no execution permission from this Source."""
from pathlib import Path
import datetime,hashlib,json,os,signal,subprocess,sys,time,types
os.umask(0o077)
ROOT = Path('/home/jericho/.cache/FRW-SOL-V3-CSV-V04-EDIT228-ORDINARY-SOURCE-CORE-20261117/caller/r1')
CURRENT = Path('/home/jericho/.cache/FRW-SOL-V3-CSV-V04-EDIT228-ORDINARY-SOURCE-CORE-20261117/caller/r1/ROOT_UNBOUND_csv_v04_edit228_current.py')
PYTHON = 'ROOT_UNBOUND_NATIVE228_INTERPRETER'
STATE=Path('/home/jericho/.local/share/friday-telegram-bot-test')
SLOT=Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
RUN = 'ROOT_UNBOUND'
HELPER={'path':'/home/jericho/.cache/FRW-SOL-V3-DOCX-FIRST-SUMMARY-RECALL-SOURCE-CORE-20261116/dependencies/root_f07_once.py','bytes':40278,'sha256':'f172ccd6f9fd4e3eadbd47eb01582d8b83d2cb81415ac148bd1820488d3473dd'}
def need(ok,code):
 if not ok:raise ValueError(code)
def load(raw,path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def helper():
 raw=Path(HELPER['path']).read_bytes();need(len(raw)==HELPER['bytes']and hashlib.sha256(raw).hexdigest()==HELPER['sha256'],'CSV228_helper_changed');need(raw.count(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED')==1,'CSV228_exact_helper_diagnostic_seam_required');return load(raw.replace(b'F07_STOP_UNCONFIRMED_ORIGINAL_OUTER600_EXPIRED',b'CSV228_STOP_UNCONFIRMED_ORIGINAL_OUTER900_EXPIRED'),HELPER['path'],'RootCSV228OwnedHelpers')
def sources(v,h):
 need(v['run_id']==RUN and v['operator']=='Root'and v['resources']==dict(operation_seconds=600,reply_window_seconds=480,ack_seconds=10,reserve_seconds=5,outer_seconds=900,cpu_seconds=120,max_rss_bytes=536870912,disk_bytes=104857600),'CSV228_exact_first_effect_and_resources_required')
 need(v['current_checker']['path']==str(CURRENT) and v['actor']['path']==str(Path(__file__).absolute()),'CSV228_exact_Root_actor_gate')
 need(h.readref(v['actor'])==Path(__file__).read_bytes(),'CSV228_actor_Source_drift')
 review=h.doc(v['review']);need(review.get('decision')=='PASS_SOURCE_READY_ROOT_BINDINGS_REQUIRED'and review.get('open_critical_defects')==[],'CSV228_final_independent_review_required')
 for k in ('actor','current_checker','preparation'):
  need(v[k]in review['reviewed_sources'],'CSV228_review_exact_Source_missing')
 prep=load(h.readref(v['preparation']),v['preparation']['path'],'RootCSV228UploadPreparation')
 current=load(h.readref(v['current_checker']),v['current_checker']['path'],'RootCSV228Current')
 scenario=h.doc(v['scenario']);need(hashlib.sha256(h.encoded(scenario)).hexdigest()==v['scenario_sha256'],'CSV228_scenario_drift')
 need(current.ROOT_BOUND is True,'CSV228_ROOT_UNBOUND_FAILCLOSED')
 prep.validate_scenario_data(scenario);need(prep.operation_of(scenario)==current.OPERATION and prep.family_of(scenario)==current.FAMILY,'CSV228_EXACT_OPERATION_REQUIRED')
 authority=h.doc(v['authority']);prep.validate_authority_shape(authority,v['authority'],run_id=RUN,scenario=scenario)
 need(authority.get('csv_v04_edit228_effect_eligibility')==current.ELIGIBILITY and authority.get('csv_v04_edit228_installed228_assessment')==current.INSTALLED228,'CSV228_ACTOR_EXACT_ROOT_BINDINGS_REQUIRED')
 need(current.OPERATION=='edit'and current.FAMILY=='csv'and current.VARIANT=='v04'and authority.get('csv_v04_edit228_upload_input')==current.UPLOAD_INPUT and authority.get('csv_v04_edit228_original_case')==current.ORIGINAL_CASE and authority.get('csv_v04_edit228_future_postconditions')==current.FUTURE_POSTCONDITIONS,'CSVV04_ACTOR_EXACT_INITIAL_EDIT_REQUIRED')
 need(v.get('native_python')==PYTHON==sys.executable,'CSV228_EXACT_ROOT_NATIVE228_INTERPRETER_REQUIRED')
 for p in v['private_roots']:need(not Path(p).is_relative_to(current.H) and not current.H.is_relative_to(Path(p)),'CSV228_private_product_roots_overlap')
 need(all(any(Path(r['path']).is_relative_to(Path(root))for root in v['private_roots'])for r in(v['review'],v['current_checker'],v['preparation'],v['authority'],v['scenario'])),'CSV228_private_bindings_scope')
 return prep,current,scenario

def compose(v,h,prep,proof):
 authority=h.doc(v['authority'])
 raw=prep.compose_source(h.readref(v['selected_tester'],private=False),h.readref(v['history_helper']),h.readref(v['readonly_history']),scenario=h.doc(v['scenario']),run_id=RUN,authority=authority,authority_ref=v['authority'],current_checker_ref=v['current_checker'],current_proof_ref=proof)
 return raw

def proof(v,h,current,*,clock,parent):
 now,mono=time.time(),time.monotonic();me=h.kernel(os.getpid())
 p=dict(schema='frw.Root.CSV.V04.EDIT228.preintent-proof.v1',operator='Root',accepted=True,run_id=RUN,scenario_sha256=v['scenario_sha256'],baseline=current.BASE,family=current.FAMILY,operation=current.OPERATION,upload_input=current.UPLOAD_INPUT,effect_eligibility=current.ELIGIBILITY,installed228_assessment=current.INSTALLED228,received_source=None,variant=current.VARIANT,original_case=current.ORIGINAL_CASE,future_postconditions=current.FUTURE_POSTCONDITIONS,decisions={k:True for k in current.DECISIONS},future_ingress_read_answer_credit=False,created_at=now,expires_at=now+120,created_monotonic=mono,expires_monotonic=mono+120,clock=clock,lock_owners=dict(slot=parent,consumer=me,credential=me))
 return h.new(Path(v['binding_dir'])/('ROOT-PRECLOCK-PROOF.json'if clock is None else 'ROOT-PREINTENT-PROOF.json'),h.encoded(p))

def readonly(v,h,prep,current,scenario,parent):
 # Existing dirs/locks only; no token bytes/API/new run/send/capture/clock.
 store_paths=[STATE,STATE/'runs',STATE/'updates',STATE/'downloads'];before={str(p):h.protected_directory(p)for p in store_paths}
 # Compose requires an exact proof reference; create it while all named locks are held.
 base=load(h.readref(v['selected_tester'],private=False),v['selected_tester']['path'],'RootCSV228StaticTester');store=base.Store(STATE)
 need({str(p):h.protected_directory(p)for p in store_paths}==before,'CSV228_Store_constructor_changed_dirs')
 with store.lock(create=False),store.lock(STATE/'tester-token',create=False):
  pr=proof(v,h,current,clock=None,parent=parent);candidate=compose(v,h,prep,pr);module=load(candidate,v['selected_tester']['path'],'RootCSV228ReadonlyConsumer')
  runner=module.Runner(store,None)
  result=prep.qualify_selected_ordinary_readonly(runner,run_id=RUN,scenario=scenario)
  need(not store.run_path(RUN).exists(),'CSV228_readonly_created_run')
  return result

def child(v,h,binding,slot,parent,clockref):
 h.child_limits(v['resources']);need(h.kernel(os.getppid())==parent,'CSV228_owned_parent_changed');need(h.lock_identity(os.fstat(slot))==v['slot_identity'],'CSV228_inherited_slot_changed')
 prep,current,scenario=sources(v,h);clock=h.doc(clockref);need(h.remaining(clock)>605,'CSV228_original_clock_insufficient')
 store_base=load(h.readref(v['selected_tester'],private=False),v['selected_tester']['path'],'RootCSV228StoreBase');store=store_base.Store(STATE)
 # Retain the reviewed aggregate growth monitor, plus per-write temporary-copy cap.
 original_write=store.write;initial={};current_sizes={}
 def bounded(path,data):
  p=h.canonical_path(str(path));need(p.is_relative_to(store.root)and not any(q.is_symlink()for q in(p,*p.parents)),'CSV228_Store_write_outside_canonical_scope')
  if p not in initial:initial[p]=p.stat().st_size if p.exists()else 0;current_sizes[p]=initial[p]
  growth=sum(max(0,size-initial[name])for name,size in current_sizes.items())
  need(growth+len(data)<=v['resources']['disk_bytes'],'CSV228_aggregate_Store_write_and_temporary_copy_bound')
  original_write(p,data);current_sizes[p]=len(data)
 store.write=bounded
 with store.lock(create=False)as consumer_fd,store.lock(STATE/'tester-token',create=False)as credential_fd:
  pr=proof(v,h,current,clock=clockref,parent=parent);candidate=compose(v,h,prep,pr)
  candidate_ref=h.new(Path(v['workdir'])/'bot_tester.csv228.current228.py',candidate)
  module=load(candidate,candidate_ref['path'],'RootCSV228ActualConsumer');readonly_runner=module.Runner(store,None)
  prep.qualify_selected_ordinary_readonly(readonly_runner,run_id=RUN,scenario=scenario)
  # Token exists only in this owned child memory. cc36 authenticates real principals in GET preflight.
  api=module.BotAPI(module.safe_read(STATE/'tester-token',256).decode('ascii').strip());runner=module.Runner(store,api);run=None;stage='NEW'
  try:
   run=runner.new(RUN,scenario);stage='SEND';runner.send(run,consumer_fd=consumer_fd,credential_fd=credential_fd);stage='OBSERVE';runner.observe(run)
  except BaseException as exc:
   h.new(Path(v['workdir'])/'CONSUMER-RAW-FAILURE.json',h.encoded(dict(state='REFUSED_INTERRUPTED_OR_UNKNOWN',stage=stage,exception_class=type(exc).__name__,frames=h.enum_failure_frames(exc,stage),no_retry=True)));raise
  finally:
   p=store.run_path(RUN);h.new(Path(v['workdir'])/'CONSUMER-RAW-CLOSURE.json',h.encoded(dict(run_id=RUN,stage=stage,canonical_run=h.fileref(p)if p.exists()else None,status=run.get('status')if run else None,send_state=run.get('send_state')if run else None,capture_window_complete=run.get('capture_window_complete')if run else None,semantic='NOT_ESTABLISHED',privacy='NOT_ESTABLISHED',no_retry=True)))
 return 0

def execute(v,h,binding):
 prep,current,scenario=sources(v,h);work=Path(v['workdir']);need(not list(work.iterdir()),'CSV228_fresh_empty_operation_required');slot=h.safe_lock(SLOT,v['slot_identity']);parent=h.kernel(os.getpid());actor=None;clock=None;lifetime=dict(cleanup_attempted=False);stops=[]
 previous={s:signal.getsignal(s)for s in(signal.SIGINT,signal.SIGTERM)};previous_alarm=signal.getsignal(signal.SIGALRM)
 def stopped(sig,_):
  stops.append(int(sig))
  if actor is not None and actor.poll()is None:actor.send_signal(sig)
 try:
  for s in previous:signal.signal(s,stopped)
  def prep_timeout(*_):raise TimeoutError('CSV228_readonly_preparation_180_expired')
  signal.signal(signal.SIGALRM,prep_timeout);signal.setitimer(signal.ITIMER_REAL,180)
  prefix=readonly(v,h,prep,current,scenario,parent);baseline=h.scan_scope(v['disk_scope'],deadline=time.monotonic()+30)
  signal.setitimer(signal.ITIMER_REAL,0)
  need(not stops,'CSV228_owner_stop_before_clock');h.new(work/'ROOT-ONCE-DRIVER-INVOCATION.json',h.encoded(dict(run_id=RUN,binding=binding,parent=parent,prefix=prefix,no_retry=True)))
  start=time.monotonic();clock=dict(run_id=RUN,started_monotonic=start,deadline_monotonic=start+900,old_effects_clocks_preserved=True)
  clockref=h.new(work/'ROOT-ORIGINAL-OUTER900-CLOCK.json',h.encoded(clock))
  argv=[PYTHON,'-I','-B','-S',str(Path(__file__).absolute()),'--child',binding['path'],binding['sha256'],str(slot),str(parent['pid']),str(parent['start_time']),parent['boot_id'],clockref['path'],clockref['sha256']]
  with os.fdopen(os.open(work/'CONSUMER.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb')as out,os.fdopen(os.open(work/'CONSUMER.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb')as err:
   need(not stops,'CSV228_owner_stop_before_birth');actor=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(slot,));h.new(work/'ROOT-OWNED-ACTOR.json',h.encoded(dict(identity=h.kernel(actor.pid),parent=parent,clock=clockref)))
   result=h.wait_owned(actor,clock,v['disk_scope'],baseline,v['resources']['disk_bytes'],stops,lifetime,monitor_failure_path=work/'ROOT-DISK-MONITOR-FIRST-FAILURE.json')
  result.update(run_id=RUN,elapsed_seconds=time.monotonic()-start,owned_child_reaped=actor.poll()is not None,parent_stops=stops,original_clock=clockref,semantic='NOT_ESTABLISHED',no_retry=True)
  h.new(work/'ROOT-DISPATCH-ENDED.json',h.encoded(result));return result
 except h.StopUnconfirmed:
  h.new(work/'ROOT-STOP-UNCONFIRMED.json',h.encoded(dict(state='STOP_UNCONFIRMED',owned_actor_pid=actor.pid,no_retry=True)));raise
 finally:
  try:
   if actor is not None and actor.poll()is None and clock is not None and not lifetime['cleanup_attempted']:h.stop_reap(actor,clock,[],lifetime)
  finally:
   signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous_alarm)
   for s,handler in previous.items():signal.signal(s,handler)
   os.close(slot)

def main():
 need(RUN!='ROOT_UNBOUND'and PYTHON!='ROOT_UNBOUND_NATIVE228_INTERPRETER','CSV228_ROOT_UNBOUND_FAILCLOSED_BEFORE_IO')
 h=helper();args=sys.argv[1:];is_child=bool(args and args[0]=='--child');need(is_child or args[:1]==['--execute'],'CSV228_explicit_mode_required');p=Path(args[1]);raw=h.read(p,limit=1048576);need(hashlib.sha256(raw).hexdigest()==args[2],'CSV228_exact_binding_required');binding=dict(path=str(p),bytes=len(raw),sha256=args[2]);v=h.parse(raw)
 if is_child:
  parent=dict(pid=int(args[4]),start_time=int(args[5]),boot_id=args[6]);cp=Path(args[7]);cr=h.read(cp,limit=65536);need(hashlib.sha256(cr).hexdigest()==args[8],'CSV228_original_clock_changed');return child(v,h,binding,int(args[3]),parent,dict(path=str(cp),bytes=len(cr),sha256=args[8]))
 print(json.dumps(execute(v,h,binding)));return 0
if __name__=='__main__':raise SystemExit(main())
