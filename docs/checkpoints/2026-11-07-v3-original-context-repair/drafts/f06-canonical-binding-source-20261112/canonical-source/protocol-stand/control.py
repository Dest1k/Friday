"""Owned source-only whole-caller stand; never a product/tester execution role.

The exact caller main/execute and exact producer validations run. Host observation
is explicitly synthetic and dependency-injected only here, after pinned load.
"""
import ast, contextlib, datetime, fcntl, hashlib, io, json, locale, math, os
import pathlib, re, resource, signal, socket, sqlite3, stat, subprocess, sys, time, types
import encodings.unicode_escape, encodings.utf_8, encodings.ascii
from pathlib import Path

os.umask(0o077)
HERE=Path(__file__).resolve().parent
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
CASE=HERE/'cases'/sys.argv[1]
CASE.mkdir(mode=0o700,parents=True)
CONTROL=sys.argv[2]
SNAPSHOT=HERE/sys.argv[3]
AUDIT={'opens':[],'denied':[],'imports':[],'metadata':[],'real_subprocess':0,'network':0}
EVENTS=[]
def check(ok,why):
    if not ok:raise AssertionError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def audit(event,args):
    if event=='open':
        path=args[0]
        if isinstance(path,int):return
        text=os.fsdecode(path)
        absolute=os.path.abspath(text)
        if absolute==str(BASE):
            flags=args[2]
            if isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                AUDIT['denied'].append(['base_write',absolute]);raise RuntimeError('AUDIT_STATIC_BASE_WRITE_DENIED')
        elif not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
            AUDIT['denied'].append(['open',absolute]);raise RuntimeError('AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED')
        AUDIT['opens'].append(absolute)
    elif event=='import':
        AUDIT['imports'].append(args[0]);AUDIT['denied'].append(['import',args[0]])
        raise RuntimeError('AUDIT_POST_PREWARM_IMPORT_DENIED')
    elif event.startswith('socket.'):
        AUDIT['network']+=1;AUDIT['denied'].append([event]);raise RuntimeError('AUDIT_NETWORK_DENIED')
    elif event in ('subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.forkpty','pty.spawn') or event.startswith('os.exec'):
        AUDIT['real_subprocess']+=1;AUDIT['denied'].append([event]);raise RuntimeError('AUDIT_REAL_ACTOR_DENIED')
    elif event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.link','os.symlink','os.truncate'):
        for item in args[:2]:
            if isinstance(item,(str,bytes)):
                absolute=os.path.abspath(os.fsdecode(item))
                if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
                    AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_MUTATION_DENIED')
    elif event in ('os.listdir','os.scandir'):
        path=args[0]
        if not isinstance(path,int):
            absolute=os.path.abspath(os.fsdecode(path))
            if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/')):
                AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_DIRECTORY_READ_DENIED')
sys.addaudithook(audit)

# CPython audit does not expose stat/lstat/readlink. This test-only host seam
# confines those metadata operations as well; ancestors are metadata-only so the
# actual caller can establish no symlink in its canonical own input path.
metadata_ancestors={str(p) for p in (*HERE.parents,*BASE.parents)}
def confined_metadata(function,event):
    def call(path,*args,**kwargs):
        if not isinstance(path,int):
            absolute=os.path.abspath(os.fsdecode(path))
            if not (absolute==str(HERE) or absolute.startswith(str(HERE)+'/') or absolute==str(BASE) or absolute in metadata_ancestors):
                AUDIT['denied'].append([event,absolute]);raise RuntimeError('AUDIT_EXTERNAL_METADATA_DENIED')
            AUDIT['metadata'].append([event,absolute])
        return function(path,*args,**kwargs)
    return call
os.stat=confined_metadata(os.stat,'stat');os.lstat=confined_metadata(os.lstat,'lstat');os.readlink=confined_metadata(os.readlink,'readlink')

def put(path,value,raw=False):
    path=CASE/path if not isinstance(path,Path) or not path.is_absolute() else path
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    data=value if raw else encoded(value)
    path.write_bytes(data);path.chmod(0o600)
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}
def refresh(ref,value,raw=False):
    return put(Path(ref['path']),value,raw)
def module(path,name):
    m=types.ModuleType(name);m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m
def jsonread(ref):return json.loads(Path(ref['path']).read_bytes())
def sourcecopy():
    own=CASE/'source';own.mkdir(mode=0o700)
    pins={}
    for leaf in ('root_bind_existing_consumer_once.py','f06_source.py','current207.py','f06_footer.py.txt'):
        raw=(SNAPSHOT/leaf).read_bytes();put(own/leaf,raw,True)
        pins[leaf]={'bytes':len(raw),'sha256':sha(raw)}
    return own,pins

own,pins=sourcecopy()
M=module(own/'root_bind_existing_consumer_once.py','SYNTHETIC_REAL_FIRST_CALLER')
A=module(own/'f06_source.py','SYNTHETIC_REAL_FIRST_ADAPTER_FOR_FIXTURE')
fakeproc=CASE/'SYNTHETIC-proc';fakeproc.mkdir(mode=0o700)
put(fakeproc/'sys/kernel/random/boot_id',b'SYNTHETIC-BOOT-ID\n',True)
class SyntheticPathMeta(type):
    def __instancecheck__(cls,obj):return isinstance(obj,Path)
class SyntheticPath(type(Path()),metaclass=SyntheticPathMeta):
    def __init__(self,*args):
        if args and str(args[0]).startswith('/proc') and (str(args[0])=='/proc' or str(args[0]).startswith('/proc/')):
            args=(str(fakeproc)+str(args[0])[5:],*args[1:])
        super().__init__(*args)
M.Path=SyntheticPath
M.STATE=SyntheticPath(CASE/'SYNTHETIC-STATE')
(M.STATE/'runs').mkdir(parents=True,mode=0o700)
for leaf in ('consumer.lock','tester-token'):put(M.STATE/leaf,b'',True)
M.SLOT=SyntheticPath(CASE/'SYNTHETIC-shared-slot.lock');put(M.SLOT,b'',True)
M.ORIGINAL_DIR=SyntheticPath(CASE/'SYNTHETIC-O-CLOSED')
(M.ORIGINAL_DIR/'work').mkdir(parents=True,mode=0o700)
X=SyntheticPath(CASE/'SYNTHETIC-X-CLOSED');(X/'work').mkdir(parents=True,mode=0o700)
for name in ('BINDING_ORIGINAL_DIR','BINDING_DIR','PREVIOUS_CONSUMER_DIR','BINDING_FAILURE_DIR'):
    if hasattr(M,name):setattr(M,name,X)
M.ORIGINAL_RUN='SYNTHETIC-first-docx-wrong-read'
M.EXISTING_AUTHORITY_ID='SYNTHETIC-existing-R106-opaque'
M.EXISTING_CREATED=time.time()-60
M.EXISTING_EXPIRES=M.EXISTING_CREATED+6*3600
M.PYTHON='/SYNTHETIC/NEVER-EXECUTED-PYTHON'
fake_source={'path':str(CASE/'SYNTHETIC-retained-descriptor-NEVER-OPENED.docx'),'bytes':23040,'sha256':'1'*64}
A.SOURCE=fake_source
installed=put('SYNTHETIC-installed-static-placeholder.py',b'# SYNTHETIC static installed placeholder, never imported\n',True)
A.INSTALLED_TESTER=Path(installed['path']);A.INSTALLED_TESTER_SHA=installed['sha256']
pin={'path':fake_source['path'],'sha256':fake_source['sha256'],'stat':{'size_bytes':23040},'filename':'f06-new-encrypted.docx','mime_type':A.MIME,'kind':'document'}
scenario=A.construct_scenario(supplied_password='SYNTHETIC-DUMMY-NO-SECRET',input_pin=pin)
scenario_ref=put('SYNTHETIC-scenario.json',scenario)
M.ORIGINAL_SCENARIO_SHA=scenario_ref['sha256']
predecessor=put('SYNTHETIC-predecessor-issueddata.json',{'schema':'frw.Root.ordinary-independent-history-admission.v1','accepted':True,'authority_id':'SYNTHETIC-predecessor'})
authority_data={'schema':'frw.Root.ordinary-independent-history-admission.v1','operator':'Root','accepted':True,'authority_id':M.EXISTING_AUTHORITY_ID,'scope':A.scope(),'run_scenarios':{M.ORIGINAL_RUN:M.ORIGINAL_SCENARIO_SHA},'ordered_predecessors':{},'same_canonical_local_run':False,'created_at':M.EXISTING_CREATED,'expires_at':M.EXISTING_EXPIRES,'supersedes':{'authority_id':'SYNTHETIC-predecessor','reason':'SYNTHETIC stand explicit chain'}}
M.EXISTING_AUTHORITY=put('SYNTHETIC-issueddata-R106.json',authority_data)
oldonce=put(M.ORIGINAL_DIR/'work/ROOT-ONCE-INVOCATION.json',{'schema':'frw.Root.F06.one-driver-invocation.v1','run_id':M.ORIGINAL_RUN,'no_retry':True})
oldclockdata={'schema':'frw.Root.F06.original-finite-clock.v1','started_at':1.0,'deadline_at':601.0,'started_monotonic':1.0,'deadline_monotonic':601.0,'boot_id':'SYNTHETIC-CLOSED-BOOT'}
oldclock=put(M.ORIGINAL_DIR/'EXECUTION-CLOCK.json',oldclockdata)
O={'schema':'friday.root.F06.first-driver-prebirth-refusal-closure.v1','at_moscow':datetime.datetime.fromtimestamp(time.time()-120,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'state':'DRIVER_CLOSED_AFTER_ISSUANCE_BEFORE_BIND_OR_CONSUMER_BIRTH_NO_SEND','driver_exit_code':1,'actual_root_driver_pid':910001,'actual_root_driver_absent':True,'consumer_birth':False,'dispatch_invocation_absent':True,'canonical_run_absent':True,'actual_issued_authority':M.EXISTING_AUTHORITY,'actual_authority_id':M.EXISTING_AUTHORITY_ID,'authority_scope_scenario_correct':True,'no_API_client_created':True,'reissue_retry_resume_or_rename_authorized':False,'once_claim_preserved':oldonce,'original_clock':oldclock,'original_clock_endpoints_preserved':oldclockdata}
M.PREBIRTH_CLOSURE=put(M.ORIGINAL_DIR/'PREBIRTH-ISSUER-ONLY-CLOSURE.json',O)
xonce=put(X/'work/ROOT-FIRST-CONSUMER-ONCE.json',{'schema':'frw.Root.F06.first-consumer-invocation.v1','run_id':M.ORIGINAL_RUN,'no_retry':True,'issuer_invoked':False,'old_driver_resume':False,'existing_authority':M.EXISTING_AUTHORITY,'prebirth_closure':M.PREBIRTH_CLOSURE})
xclockdata=dict(oldclockdata,schema='frw.Root.F06.unstarted-consumer-finite-clock.v1')
xclock=put(X/'CONSUMER-CLOCK.json',xclockdata)
xsource=put(X/'work/bot_tester.f06.root-bound.py',b'# SYNTHETIC closed failed source, never imported\n',True)
xbinding=put(X/'work/ROOT-ACTUAL-BINDING.json',{'schema':'frw.Root.F06.exact-first-wrongread-binding.v1','source':xsource,'authority':M.EXISTING_AUTHORITY,'contract':{'run_id':M.ORIGINAL_RUN,'authority':M.EXISTING_AUTHORITY,'authority_id':M.EXISTING_AUTHORITY_ID,'scenario_sha256':M.ORIGINAL_SCENARIO_SHA,'scope':A.scope(),'resources':{'clock':xclock}}})
XC={'schema':'friday.root.F06.firstconsumer-binding-prebirth-refusal-closure.v1','at_moscow':datetime.datetime.fromtimestamp(time.time()-60,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'state':'FIRST_CONSUMER_BINDING_CREATED_RECONSTRUCTION_REFUSED_BEFORE_DISPATCH_NO_SEND','driver_exit_code':1,'actual_root_driver_pid':910002,'actual_root_driver_absent':True,'consumer_born':False,'dispatch_created':False,'canonical_run_created':False,'source_file':xsource,'actual_binding':xbinding,'whole_contract_values_equal_after_json':True,'all_non_contract_AST_equal':True,'source_reconstruction_guard_preserved':True,'failure':'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE','no_API_client_or_upload_or_model_based_on_actual_control_flow':True,'existing_R106_not_reissued':True,'consumer_stage_once_preserved':xonce,'original_consumer_clock_preserved':xclock,'old_issuer_only_once_clock_preserved':True,'no_old_driver_or_issuer_retry':True}
xclosure=put(X/'PREBIRTH-BINDING-RECONSTRUCTION-REFUSAL-CLOSURE.json',XC)
for name in ('BINDING_PREBIRTH_CLOSURE','PREBIRTH_BINDING_CLOSURE','BINDING_FAILURE_CLOSURE'):
    if hasattr(M,name):setattr(M,name,xclosure)

work=SyntheticPath(CASE/'work');work.mkdir(mode=0o700)
c=A.unbound();c.update(status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',run_id=M.ORIGINAL_RUN,scenario_ref=scenario_ref,scenario_sha256=M.ORIGINAL_SCENARIO_SHA,authority=M.EXISTING_AUTHORITY,authority_id=M.EXISTING_AUTHORITY_ID,authority_chain={'predecessor':predecessor,'predecessor_authority_id':'SYNTHETIC-predecessor','created_at':M.EXISTING_CREATED,'expires_at':M.EXISTING_EXPIRES})
def localref(leaf):
    raw=(own/leaf).read_bytes();return {'path':str(own/leaf),'bytes':len(raw),'sha256':sha(raw)}
c.update(adapter=localref('f06_source.py'),footer=localref('f06_footer.py.txt'),actual_root_B_checker=localref('current207.py'))
c['root_proofs']={k:put('proofs/SYNTHETIC-'+k+'.json',{'SYNTHETIC':k}) for k in A.PROOFS}
c['product']=dict(A.PRODUCT,source_receipt_sha256='2'*64,input_sha256='3'*64)
boundary={k:'4'*64 for k in A.BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}}
boundary.update(gateway={'SYNTHETIC':True,'pid':910003,'start_time':1},B={'profile':'telegram-bot-8812646969','session_id':'SYNTHETIC-SESSION','session_key':'SYNTHETIC-KEY','native_max_id':0},phase_unconsumed=True,uploads_this_operation=1,producer_calls=0,restarts=0)
c['boundary']=boundary
clockdata={'schema':'frw.Root.F06.unstarted-consumer-finite-clock.v1','started_at':time.time()-1,'deadline_at':time.time()+590,'started_monotonic':time.monotonic()-1,'deadline_monotonic':time.monotonic()+590,'boot_id':'SYNTHETIC-BOOT-ID'}
c['resources']=dict(A.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=64*1024**2,clock=put('SYNTHETIC-future-clock.json',clockdata),owned_parent_wait_cleanup=put('SYNTHETIC-cleanup-policy.json',{'SYNTHETIC':'owned stop policy descriptor'}))
c['source']=fake_source
freeze={'schema':'frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1' if 'canonical-existing-R106-first-consumer' in (own/'root_bind_existing_consumer_once.py').read_text() else 'frw.F06.existing-R106-first-consumer.source-freeze.v1','files':pins}
freeze_ref=put('SYNTHETIC-source-freeze.json',freeze)
review=put('SYNTHETIC-independent-review.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':freeze_ref['sha256'],'open_critical_defects':[]})
c['root_proofs']['source_review']=review
prepared={'status':'ROOT_PREPARED_ONE_FUTURE_OPERATION','contract_effect':A.effect(c),'whole_effect_sha256':sha(encoded(A.effect(c))),'observed':{'SYNTHETIC':True,'f06_mutable_boundary':boundary}}
c['root_current_proof']=put('SYNTHETIC-prepared-current-proof.json',prepared)
reconciliation={'schema':'frw.Root.F06.two-closed-prebirth-reconciliation.v1' if freeze['schema'].startswith('frw.F06.canonical') else 'frw.Root.F06.issuer-only-prebirth-reconciliation.v1','operator':'Root','status':'ROOT_BOUND_SEPARATELY_ADMITTED_UNSTARTED_CONSUMER','prebirth_closure':M.PREBIRTH_CLOSURE,'binding_prebirth_closure':xclosure,'original_run_id':M.ORIGINAL_RUN,'scenario_sha256':M.ORIGINAL_SCENARIO_SHA,'existing_authority':M.EXISTING_AUTHORITY,'old_once':oldonce,'old_clock':oldclock,'binding_old_once':xonce,'binding_old_clock':xclock,'binding_old_source':xsource,'binding_old_binding':xbinding,'created_at':time.time()-1,'expires_at':time.time()+110}
for key in ('first_consumer_stage_never_started','old_driver_closed_and_absent','old_once_and_clock_preserved','no_prior_bind_dispatch_canonicalrun_or_unknown','existing_issuance_scope_run_hash_chain_accepted','separate_missing_segment_authorized','no_old_driver_or_issuer_retry','binding_failure_closed_before_dispatch','binding_once_clock_source_preserved','no_unknown_consumer_effect'):reconciliation[key]=True
if freeze['schema'].startswith('frw.F06.canonical'):
    for old,new in (('first_consumer_stage_never_started','user_consumer_never_started'),('no_prior_bind_dispatch_canonicalrun_or_unknown','no_prior_user_dispatch_canonicalrun_or_unknown'),('separate_missing_segment_authorized','separate_missing_user_consumer_authorized')):reconciliation[new]=reconciliation.pop(old)
if freeze['schema'].startswith('frw.F06.existing'):
    for key in ('binding_prebirth_closure','binding_old_once','binding_old_clock','binding_old_source','binding_old_binding','binding_failure_closed_before_dispatch','binding_once_clock_source_preserved','no_unknown_consumer_effect'):reconciliation.pop(key,None)
reconciliation_ref=put('SYNTHETIC-reconciliation.json',reconciliation)
si=M.SLOT.stat();slot_identity={'device':si.st_dev,'inode':si.st_ino,'uid':si.st_uid,'mode':stat.S_IMODE(si.st_mode),'nlink':si.st_nlink}
v={'schema':'frw.Root.F06.canonical-existing-R106-first-consumer.v1' if freeze['schema'].startswith('frw.F06.canonical') else 'frw.Root.F06.existing-R106-first-consumer.v1','status':'ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER','contract':c,'source_freeze':freeze_ref,'independent_review':review,'workdir':str(work),'slot_identity':slot_identity,'expected_binding_sha256':None,'prebirth_closure':M.PREBIRTH_CLOSURE,'prebirth_reconciliation':reconciliation_ref}
if freeze['schema'].startswith('frw.F06.canonical'):v['binding_prebirth_closure']=xclosure

real_load=M.load
def load(ref,name,**kwargs):
    EVENTS.append(['load',Path(ref['path']).name])
    m=real_load(ref,name,**kwargs)
    if Path(ref['path']).name=='f06_source.py':
        m.SOURCE=fake_source;m.INSTALLED_TESTER=Path(installed['path']);m.INSTALLED_TESTER_SHA=installed['sha256']
        real_successor=m.successor
        def successor(base,contract,footer):
            EVENTS.append(['successor',list(contract['root_current_proof'])])
            raw=real_successor(base,contract,footer)
            if CONTROL=='reconstruction_guard' and sum(e[0]=='successor' for e in EVENTS)==2:return raw+b'# SYNTHETIC CORRUPTION\n'
            return raw
        m.successor=successor
    elif Path(ref['path']).name=='current207.py':
        def observe(proof):
            EVENTS.append(['SYNTHETIC-checker-observe'])
            value=json.loads(encoded(proof['observed']))
            if CONTROL=='current_changed':value['SYNTHETIC']='changed'
            return value
        def proofcheck(path,want):
            EVENTS.append(['SYNTHETIC-checker-check'])
            raw=M.read(path);check(sha(raw)==want,'stand checker pinned fresh proof')
            p=json.loads(raw);check(p['status']=='ROOT_BOUND','stand bound proof status')
            return {'whole_effect_sha256':p['whole_effect_sha256']}
        m.observe=observe;m.check=proofcheck
        m.transport=lambda:types.SimpleNamespace(kernel=lambda pid:{'SYNTHETIC':True,'pid':pid,'start_time':1})
    else:raise AssertionError('undeclared module load')
    return m
M.load=load
class PrebirthBoundary(BaseException):pass
POPPEN=[]
def fakepopen(argv,**kwargs):
    POPPEN.append({'argv':argv,'pass_fds':list(kwargs.get('pass_fds',())),'preexec_fn_present':callable(kwargs.get('preexec_fn'))})
    check(argv[0]=='/SYNTHETIC/NEVER-EXECUTED-PYTHON','synthetic interpreter')
    check(argv[4]==str(work/'bot_tester.f06.root-bound.py'),'bound source argv')
    check(len(POPPEN)==1,'sole boundary')
    raise PrebirthBoundary('SYNTHETIC_NO_CHILD_PREBIRTH_BOUNDARY')
M.subprocess=types.SimpleNamespace(Popen=fakepopen,DEVNULL=subprocess.DEVNULL,TimeoutExpired=subprocess.TimeoutExpired)
original_handlers={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
if CONTROL=='invalid_stop':
    def synthetic_registration(n,handler):
        previous=signal.signal(n,handler)
        if n==signal.SIGTERM and getattr(handler,'__name__',None)=='parent_stop':
            EVENTS.append(['SYNTHETIC-stop-after-registration-before-birth']);handler(n,None)
        return previous
    M.signal=types.SimpleNamespace(SIGINT=signal.SIGINT,SIGTERM=signal.SIGTERM,getsignal=signal.getsignal,signal=synthetic_registration)

if CONTROL=='source_drift_adapter':put(own/'f06_source.py',(own/'f06_source.py').read_bytes()+b'\n# DRIFT\n',True)
elif CONTROL=='source_drift_checker':put(own/'current207.py',(own/'current207.py').read_bytes()+b'\n# DRIFT\n',True)
elif CONTROL=='source_drift_footer':put(own/'f06_footer.py.txt',(own/'f06_footer.py.txt').read_bytes()+b'\n# DRIFT\n',True)
elif CONTROL=='source_drift_caller':put(own/'root_bind_existing_consumer_once.py',(own/'root_bind_existing_consumer_once.py').read_bytes()+b'\n# DRIFT\n',True)
elif CONTROL=='guard_disabled_source_drift':
    p=own/'root_bind_existing_consumer_once.py';raw=p.read_bytes();raw=raw.replace(b"'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE'",b"'SYNTHETIC_GUARD_DISABLED'");put(p,raw,True)
elif CONTROL=='authority_identity':authority_data['authority_id']='SYNTHETIC-WRONG';c['authority']=M.EXISTING_AUTHORITY=refresh(M.EXISTING_AUTHORITY,authority_data)
elif CONTROL=='authority_expired':M.EXISTING_CREATED=time.time()-21700;M.EXISTING_EXPIRES=M.EXISTING_CREATED+21600;c['authority_chain'].update(created_at=M.EXISTING_CREATED,expires_at=M.EXISTING_EXPIRES);authority_data.update(created_at=M.EXISTING_CREATED,expires_at=M.EXISTING_EXPIRES);c['authority']=M.EXISTING_AUTHORITY=refresh(M.EXISTING_AUTHORITY,authority_data)
elif CONTROL=='authority_scope':authority_data['scope']='SYNTHETIC WRONG SCOPE';c['authority']=M.EXISTING_AUTHORITY=refresh(M.EXISTING_AUTHORITY,authority_data)
elif CONTROL=='authority_run':authority_data['run_scenarios']={'SYNTHETIC-OTHER':'0'*64};c['authority']=M.EXISTING_AUTHORITY=refresh(M.EXISTING_AUTHORITY,authority_data)
elif CONTROL=='authority_predecessor':p=jsonread(predecessor);p['authority_id']='SYNTHETIC-WRONG';c['authority_chain']['predecessor']=refresh(predecessor,p)
elif CONTROL=='contract_run':c['run_id']='SYNTHETIC-OTHER'
elif CONTROL=='contract_scope':c['scope']='SYNTHETIC WRONG SCOPE'
elif CONTROL=='scenario_drift':put(Path(scenario_ref['path']),b'{}\n',True)
elif CONTROL in ('scenario_identity','scenario_observe_window'):
    if CONTROL=='scenario_identity':scenario['tester_id']=42
    else:scenario['steps'][0]['observe']['window_seconds']=179
    c['scenario_ref']=refresh(scenario_ref,scenario);c['scenario_sha256']=M.ORIGINAL_SCENARIO_SHA=c['scenario_ref']['sha256']
    authority_data['run_scenarios']={M.ORIGINAL_RUN:M.ORIGINAL_SCENARIO_SHA};c['authority']=M.EXISTING_AUTHORITY=refresh(M.EXISTING_AUTHORITY,authority_data)
elif CONTROL=='old_O_once_tamper':put(Path(oldonce['path']),b'{}\n',True)
elif CONTROL=='old_O_clock_tamper':put(Path(oldclock['path']),b'{}\n',True)
elif CONTROL=='old_X_once_tamper':put(Path(xonce['path']),b'{}\n',True)
elif CONTROL=='old_X_clock_tamper':put(Path(xclock['path']),b'{}\n',True)
elif CONTROL=='old_X_binding_tamper':put(Path(xbinding['path']),b'{}\n',True)
elif CONTROL=='old_X_source_tamper':put(Path(xsource['path']),b'# changed\n',True)
elif CONTROL=='old_O_once_rename':
    O['once_claim_preserved']=put(M.ORIGINAL_DIR/'work/SYNTHETIC-RENAMED-ONCE.json',jsonread(oldonce));M.PREBIRTH_CLOSURE=refresh(M.PREBIRTH_CLOSURE,O);v['prebirth_closure']=M.PREBIRTH_CLOSURE
elif CONTROL=='old_X_clock_rename':
    XC['original_consumer_clock_preserved']=put(X/'SYNTHETIC-RENAMED-CLOCK.json',xclockdata);xclosure=refresh(xclosure,XC);M.BINDING_PREBIRTH_CLOSURE=xclosure;v['binding_prebirth_closure']=xclosure
elif CONTROL=='old_O_dispatch':put(M.ORIGINAL_DIR/'work/ROOT-DISPATCH-INVOCATION.json',{},False)
elif CONTROL=='old_X_dispatch':put(X/'work/ROOT-DISPATCH-INVOCATION.json',{},False)
elif CONTROL=='old_X_unknown':put(X/'work/ROOT-STOP-UNCONFIRMED.json',{},False)
elif CONTROL=='old_X_actor':put(X/'work/ROOT-CONSUMER-ACTOR.json',{},False)
elif CONTROL=='old_driver_present':put(fakeproc/'910001/SYNTHETIC-presence',b'present',True)
elif CONTROL=='canonical_run':put(M.STATE/'runs'/(M.ORIGINAL_RUN+'.json'),{},False)
elif CONTROL=='reconciliation_stale':reconciliation['expires_at']=time.time()-5;v['prebirth_reconciliation']=refresh(reconciliation_ref,reconciliation)
elif CONTROL=='clock_expired':clockdata['deadline_at']=time.time()-1;c['resources']['clock']=refresh(c['resources']['clock'],clockdata)
elif CONTROL=='once_exists':put(work/'ROOT-FIRST-CONSUMER-ONCE.json',{'SYNTHETIC':'prior once'},False)
elif CONTROL=='invalid_cpu':c['resources']['cpu_seconds']=0
elif CONTROL=='invalid_memory':c['resources']['max_rss_bytes']=3*1024**3
elif CONTROL=='invalid_disk':c['resources']['disk_bytes']=65*1024**2
elif CONTROL=='invalid_reserve':c['resources']['reserve_seconds']=0
elif CONTROL=='invalid_cleanup':c['resources']['owned_parent_wait_cleanup']=None
elif CONTROL=='slot_identity':v['slot_identity']['inode']+=1
elif CONTROL=='review_mismatch':reviewdata=jsonread(review);reviewdata['source_freeze_sha256']='0'*64;v['independent_review']=refresh(review,reviewdata)
elif CONTROL=='work_custody':work.chmod(0o755)
elif CONTROL=='unknown_closure':XC['state']='UNKNOWN';v['binding_prebirth_closure']=M.BINDING_PREBIRTH_CLOSURE=refresh(xclosure,XC)
elif CONTROL=='bad_binding_ref':c['adapter']['sha256']='0'*64
elif CONTROL in ('positive','old_reconstruction','current_changed','reconstruction_guard','invalid_stop','audit_external_open','audit_external_write','audit_external_metadata','audit_network','audit_process','audit_import'):pass
else:raise AssertionError('unknown control '+CONTROL)

# Authority mutation controls keep the synthetic closed metadata/reconciliation
# reference coherent, so the genuine authority admission is the failing seam.
if (CONTROL.startswith('authority_') and CONTROL!='authority_predecessor') or CONTROL in ('scenario_identity','scenario_observe_window'):
    O['actual_issued_authority']=M.EXISTING_AUTHORITY
    M.PREBIRTH_CLOSURE=refresh(M.PREBIRTH_CLOSURE,O);v['prebirth_closure']=M.PREBIRTH_CLOSURE
    reconciliation['prebirth_closure']=M.PREBIRTH_CLOSURE;reconciliation['existing_authority']=M.EXISTING_AUTHORITY;reconciliation['scenario_sha256']=M.ORIGINAL_SCENARIO_SHA
    xo=jsonread(xonce);xo['existing_authority']=M.EXISTING_AUTHORITY;xo['prebirth_closure']=M.PREBIRTH_CLOSURE
    xonce=refresh(xonce,xo);XC['consumer_stage_once_preserved']=xonce
    xb=jsonread(xbinding);xb['contract']['authority']=M.EXISTING_AUTHORITY;xb['authority']=M.EXISTING_AUTHORITY;xb['contract']['scenario_sha256']=M.ORIGINAL_SCENARIO_SHA;xbinding=refresh(xbinding,xb);XC['actual_binding']=xbinding
    xclosure=refresh(xclosure,XC)
    for name in ('BINDING_PREBIRTH_CLOSURE','PREBIRTH_BINDING_CLOSURE','BINDING_FAILURE_CLOSURE'):
        if hasattr(M,name):setattr(M,name,xclosure)
    if 'binding_prebirth_closure' in v:v['binding_prebirth_closure']=xclosure
    reconciliation.update(binding_prebirth_closure=xclosure,binding_old_once=xonce,binding_old_binding=xbinding)
    v['prebirth_reconciliation']=refresh(reconciliation_ref,reconciliation)

binding=put('SYNTHETIC-root-inputs.json',v)
initial_custody={str(p):sha(p.read_bytes()) for root in (M.ORIGINAL_DIR,X) for p in root.rglob('*') if p.is_file()}
started=time.monotonic();failure=None;boundary=False;trace=None
try:
    if CONTROL=='audit_external_open':open('/SYNTHETIC-UNDECLARED-EXTERNAL-READ','rb')
    elif CONTROL=='audit_external_write':open('/SYNTHETIC-UNDECLARED-EXTERNAL-WRITE','wb')
    elif CONTROL=='audit_external_metadata':os.stat('/SYNTHETIC-UNDECLARED-EXTERNAL-METADATA')
    elif CONTROL=='audit_network':socket.socket()
    elif CONTROL=='audit_process':subprocess.Popen(['/SYNTHETIC-UNDECLARED-NEVER-EXECUTED'])
    elif CONTROL=='audit_import':__import__('SYNTHETIC_UNDECLARED_MODULE')
    else:M.main(['--execute-once',binding['path'],binding['sha256']])
except PrebirthBoundary as exc:failure=str(exc);boundary=True
except Exception as exc:
    failure=type(exc).__name__+':'+str(exc);trace=[];tb=exc.__traceback__
    while tb is not None:
        trace.append([tb.tb_frame.f_code.co_filename,tb.tb_lineno,tb.tb_frame.f_code.co_name]);tb=tb.tb_next
elapsed=time.monotonic()-started
handlers_restored=all(signal.getsignal(n)==handler for n,handler in original_handlers.items())
slot_pass_fd_closed=True
for call in POPPEN:
    for fd in call['pass_fds']:
        try:os.fstat(fd);slot_pass_fd_closed=False
        except OSError:pass
final_custody={path:sha(Path(path).read_bytes()) for path in initial_custody}
binding_path=work/'ROOT-ACTUAL-BINDING.json'
details={}
if binding_path.exists():
    br=json.loads(binding_path.read_bytes());details={'fresh_proof_ref_key_order_readback':list(br['contract']['root_current_proof']),'actual_binding':{'path':str(binding_path),'bytes':binding_path.stat().st_size,'sha256':sha(binding_path.read_bytes())},'bound_source':br['source'],'fresh_proof_sha256':br['contract']['root_current_proof']['sha256']}
result={'control':CONTROL,'snapshot':sys.argv[3],'source_pins':pins,'failure':failure,'trace':trace,'path_probe':str(M.Path('/proc/sys/kernel/random/boot_id')),'boundary':boundary,'fake_Popen_count':len(POPPEN),'fake_Popen':POPPEN,'events':EVENTS,'audit':AUDIT,'old_custody_preserved':initial_custody==final_custody,'elapsed_seconds':elapsed,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'resources':{'RLIMIT_CPU':list(resource.getrlimit(resource.RLIMIT_CPU)),'RLIMIT_AS':list(resource.getrlimit(resource.RLIMIT_AS)),'RLIMIT_FSIZE':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'affinity':sorted(os.sched_getaffinity(0))},'binding_details':details,'claims':'SOURCE-ONLY SYNTHETIC protocol qualification; never real authority, current observation, document, consumer, canonical state or acceptance'}
result.update(parent_signal_handlers_restored=handlers_restored,passed_shared_slot_fd_closed=slot_pass_fd_closed,harness_sha256=sha(Path(__file__).read_bytes()))
put(CASE/'RESULT.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='audit'},sort_keys=True))
