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
    own=CASE/'Root/source';own.mkdir(mode=0o700,parents=True)
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
fake_source={'path':str(CASE/'private-input/SYNTHETIC-retained-descriptor-NEVER-OPENED.docx'),'bytes':23040,'sha256':'1'*64}
A.SOURCE=fake_source
installed=put('private-input/SYNTHETIC-installed-static-placeholder.py',b'# SYNTHETIC static installed placeholder, never imported\n',True)
A.INSTALLED_TESTER=Path(installed['path']);A.INSTALLED_TESTER_SHA=installed['sha256']
pin={'path':fake_source['path'],'sha256':fake_source['sha256'],'stat':{'size_bytes':23040},'filename':'f06-new-encrypted.docx','mime_type':A.MIME,'kind':'document'}
scenario=A.construct_scenario(supplied_password='SYNTHETIC-DUMMY-NO-SECRET',input_pin=pin)
scenario_ref=put('private-scenario/SYNTHETIC-scenario.json',scenario)
M.ORIGINAL_SCENARIO_SHA=scenario_ref['sha256']
predecessor=put('private-authority/INDEPENDENT-AUTHORITY-R105.json',{'schema':'frw.Root.ordinary-independent-history-admission.v1','accepted':True,'authority_id':'SYNTHETIC-predecessor'})
authority_data={'schema':'frw.Root.ordinary-independent-history-admission.v1','operator':'Root','accepted':True,'authority_id':M.EXISTING_AUTHORITY_ID,'scope':A.scope(),'run_scenarios':{M.ORIGINAL_RUN:M.ORIGINAL_SCENARIO_SHA},'ordered_predecessors':{},'same_canonical_local_run':False,'created_at':M.EXISTING_CREATED,'expires_at':M.EXISTING_EXPIRES,'supersedes':{'authority_id':'SYNTHETIC-predecessor','reason':'SYNTHETIC stand explicit chain'}}
M.EXISTING_AUTHORITY=put('private-authority/INDEPENDENT-AUTHORITY-R106.json',authority_data)
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

work=SyntheticPath(CASE/'unused-old-fixture-work');work.mkdir(mode=0o700)
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

# Root finalizer integration. All original modules below are inert source copies;
# synthetic observed host/current values are declared here, not product evidence.
F=module(HERE/'root_finalizer.snapshot.py','SYNTHETIC_ROOT_FINALIZER')
F.__file__=str(CASE/'Root/root_finalizer.py');put(Path(F.__file__),(HERE/'root_finalizer.snapshot.py').read_bytes(),True)
F.Path=SyntheticPath;F.B=CASE/'B';F.T=CASE/'T';F.O=M.ORIGINAL_DIR;F.X=X;F.Y=CASE/'Root';F.C=own;F.J=F.B/'SOL-TASK29-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json';F.PYTHON=M.PYTHON
# Keep module source byte-identical: only declared synthetic host globals change.
A.SOURCE=fake_source
FREF=lambda leaf:localref(leaf)
fr=put(own/'SOURCE-FREEZE.json',freeze);F.FIRST_FREEZE_SHA=fr['sha256']
leaf=put(F.T/'review/FIRST-SOURCE-REVIEW.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':fr['sha256'],'open_critical_defects':[]})
whole=put(F.T/'SOURCE-FREEZE.json',{'SYNTHETIC':'whole freeze'})
combined=put(F.T/'review/RESULT.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','open_critical_defects':[],'branch_reviews':{'first':leaf}})
parent=put(F.T/'PARENT-SOURCE-ACCEPTANCE.json',{'decision':'ACCEPT_FINITE_SOURCE_ONLY_RUNTIME_UNBOUND','source_freeze':whole,'child_refs':[combined]})
solresult=put(F.T/'RESULT.json',{'SYNTHETIC':'source-only result'})
F.REVIEW_PINS={leaf:str(sha((F.T/leaf).read_bytes())) for leaf in F.REVIEW_PINS}
put(F.T/'candidate/first/SOURCE-FREEZE.json',freeze)
rootaccept={'schema':'friday.root.SolTask29.source-acceptance.v1','state':'ROOT_ACCEPTED_CANONICAL_FIRST_AND_CORRECT_SOURCE_RUNTIME_UNBOUND','operator':'Root','branch_freezes':{'first':F.ref(F.T/'candidate/first/SOURCE-FREEZE.json')},'branch_reviews':{'first':leaf},'future_first_source_review_ref':leaf,'independent_review':combined,'parent_acceptance':parent,'source_result':solresult,'whole_source_freeze':whole,'execution_authority':False,'ordinary_first_consumer':'NOT_RUN','new_actual_currentproof_clock_admission':'UNBOUND','open_critical_defects':[]}
# Actual acceptance has a fixed byte count3928; declared synthetic padding keeps
# exact same expected size so packages' strict concrete acceptance gate runs.
rootaccept['SYNTHETIC-padding']='';rawbase=encoded(rootaccept);rootaccept['SYNTHETIC-padding']='p'*(3928-len(rawbase));rootacceptref=put(F.J,rootaccept);check(rootacceptref['bytes']==3928,'synthetic Root decision bytes')
F.ROOT_SOURCE_ACCEPTANCE_SHA=rootacceptref['sha256']
actual={'f06_mutable_boundary':boundary,'profile_configs':{},'databases':{'tester':{'principal':{'SYNTHETIC':True}}},'history':{'manifest_sha256':'5'*64,'run_ids':[]},'source_identity':{'SYNTHETIC':True},'gateway':{'pid':910003}}
H=CASE/'SYNTHETIC-H';(H/'logs').mkdir(parents=True,mode=0o700);put(H/'logs/metadata-only-carrier',b'SYNTHETIC-CONTENT-NOT-READ',True)
closure=put('proofs/installed-closure.json',{'source_acceptance':put('proofs/installed-acceptance.json',{'SYNTHETIC':True})})
privacy={'schema':'frw.Root.F06.installed207-runtime-privacy-review.v1','operator':'Root','status':'ROOT_BOUND','installed_product':c['product'],'runtime_hashes':module(own/'current207.py','SYNTHETIC_INTERFACE_CONSTANTS').RUNTIME_HASHES,'genuine_installed_runtime_consumer_observed':True,'no_marker_or_import_bypass':True,'raw_user_chat_retention_separately_reviewed':True,'no_blanket_no_secret_persistence_claim':True,'Standard3_2_data_integrity_verified':False,'runtime_evidence':[predecessor],'effective_product_roots':[str(H)],'effective_roots_profile_config_refs':{},'effective_roots_source_basis':[predecessor],'private_roots':sorted(str(CASE/n) for n in ('Root','SYNTHETIC-O-CLOSED','SYNTHETIC-X-CLOSED','proofs','private-input','private-authority','private-scenario','T','B')),'scope':'SYNTHETIC scoped old qualification'}
c['root_proofs']['private_password_handling']=put('proofs/private.json',privacy)
history={'schema':'frw.Root.F06.history-semantic-once.v1','operator':'Root','status':'ROOT_BOUND','phase':A.PHASE,'source':fake_source,'history_manifest_sha256':'5'*64,'classified_run_ids':[],'native_boundary_sha256':boundary['native_boundary_sha256'],'once_sha256':boundary['once_sha256'],'ingress_lineage_sha256':boundary['ingress_lineage_sha256'],'equivalent_original_phase_effects':[],'all_profile_history_and_compacted_unlogged_equivalents_reconciled':True,'old_effects_UNKNOWN_and_clocks_preserved':True,'M14_partial_UNKNOWN_preserved_no_replay_or_regrade':True,'all_profile_projection_limit':'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED','retained_basis':[predecessor,predecessor]}
c['root_proofs']['all_profile_history_semantic_once']=put('proofs/history.json',history)
lineage={'schema':'frw.Root.F06.retained-g6-source-lineage.v1','operator':'Root','status':'ROOT_BOUND','phase':A.PHASE,'source':fake_source,'source_identity':actual['source_identity'],'current_ingress_lineage_sha256':boundary['ingress_lineage_sha256'],'original_producer_g6_retained':True,'no_new_producer_or_native_repeat':True,'first_ordinary_upload_not_previously_consumed':True,'native_qualification':c['root_proofs']['actual_native_qualification'],'retained_producer_oracle_basis':[predecessor]}
c['root_proofs']['source_ingress_lineage']=put('proofs/lineage.json',lineage)
originalcontract=put(F.O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json',c);originalobservation=put(F.O/'OBSERVED-BULK-FACTS.json',actual)
basis=put('proofs/constructor-basis.json',{'source_files':{'SYNTHETIC':{'ref':predecessor}}})
constructorref=put(F.O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json',{'decision':'ROOT_ACCEPT_SCOPED_SOURCE_CONFIG_INFERENCE','effective_product_roots':[str(H)],'profile_configs':{},'external_manager_source_inference':'CORE_NO_EXPLICIT_HANDOFF_NO_MANAGER_CONSTRUCTED','result':predecessor,'basis':basis,'proxy_scope_metadata':[]})
judgment={'schema':'frw.Root.F06.two-closed-prebirth-judgment.v1','operator':'Root','status':'ROOT_ACTUAL_RECONCILED_FUTURE_MISSING_CONSUMER_ONLY','prebirth_closure':M.PREBIRTH_CLOSURE,'binding_prebirth_closure':M.BINDING_PREBIRTH_CLOSURE,'existing_authority':M.EXISTING_AUTHORITY,'original_run_id':M.ORIGINAL_RUN,'scenario_sha256':M.ORIGINAL_SCENARIO_SHA}
judgment.update({k:True for k in F.BOOLS});judgmentref=put('proofs/judgment.json',judgment)
plan={'schema':'frw.Root.F06.Task29.finalizer-plan.v1','operator':'Root','status':'ROOT_EXPLICIT_PREPARATION_NO_CLOCK_NO_GRANT','root_directory':str(F.Y),'source_directory':str(own),'root_source_acceptance':rootacceptref,'original_prepared_contract':originalcontract,'original_observation':originalobservation,'constructor_acceptance':constructorref,'prebirth_judgment':judgmentref}
planref=put('plan.json',plan)
LOADS=[];POPPEN=[];EXEC=[];JOURNAL=[]
real_load=F.load
class PrebirthBoundary(BaseException):pass

def synthetic_load(ref,name):
    LOADS.append(Path(ref['path']).name);m=real_load(ref,name)
    if Path(ref['path']).name=='f06_source.py':
        m.SOURCE=fake_source;m.INSTALLED_TESTER=Path(installed['path']);m.INSTALLED_TESTER_SHA=installed['sha256']
        if CONTROL=='authority_expired':
            real_admission=m.admission
            m.admission=lambda c,d,**kw:real_admission(c,d,now=M.EXISTING_EXPIRES+1,**kw)
    elif Path(ref['path']).name=='root_bind_existing_consumer_once.py':
        for k in ('Path','STATE','SLOT','ORIGINAL_DIR','PREBIRTH_CLOSURE','EXISTING_AUTHORITY','EXISTING_AUTHORITY_ID','EXISTING_CREATED','EXISTING_EXPIRES','ORIGINAL_RUN','ORIGINAL_SCENARIO_SHA','BINDING_DIR','BINDING_PREBIRTH_CLOSURE','PYTHON'):setattr(m,k,getattr(M,k))
        m.load=synthetic_load
    elif Path(ref['path']).name=='current207.py':
        # Preserve real typed effect, history, privacy, lineage and confinement
        # interfaces; only actual host observation/installed transport is synthetic.
        m.H=H;m.CLOSURE=Path(closure['path']);m.SLOT=M.SLOT;m.EXPECTED=c['product'];m.SID=boundary['B']['session_id'];m.KEY=boundary['B']['session_key'];m.source=lambda effect:(m.reference(effect['adapter']) and A)
        def observe(proof):
            EVENTS.append(['synthetic-host-observation']);m.validate_effect(proof)
            v=json.loads(encoded(actual))
            if CONTROL=='current_changed' and (F.Y/'ROOT-BULK-DECISION.json').exists():v['SYNTHETIC-drift']=True
            return v
        m.observe=observe;m.read_process=lambda pid,name:b''
        m.transport=lambda:types.SimpleNamespace(kernel=lambda pid:{'SYNTHETIC':True,'pid':pid,'start_time':1})
        def proofcheck(p,want):
            proof=json.loads(M.read(p));check(sha(M.read(p))==want and proof['status']=='ROOT_BOUND' and set(proof)==m.PROOF_FIELDS,'fresh real currentproof shape')
            m.validate_effect(proof);m.semantic(proof,dict(proof['contract_effect'],authority=M.EXISTING_AUTHORITY,authority_id=M.EXISTING_AUTHORITY_ID,status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',root_current_proof=F.ref(p)),actual)
            return {'whole_effect_sha256':proof['whole_effect_sha256']}
        m.check=proofcheck
    else:raise AssertionError('undeclared load')
    if CONTROL=='code_drift_after_load' and Path(ref['path']).name=='root_bind_existing_consumer_once.py' and not (F.Y/'CURRENT.NOT_GRANTED.json').exists():put(own/'f06_source.py',(own/'f06_source.py').read_bytes()+b'\n# SYNTHETIC CAS RACE\n',True)
    return m
F.load=synthetic_load

def fakejournal(argv,**kwargs):
    JOURNAL.append(argv);check(argv==['journalctl','--user','-u','hermes-gateway-1b7e7667.service','-n','0','--show-cursor','--no-pager'],'journal metadata-only command');return types.SimpleNamespace(stdout=b'SYNTHETIC-CURSOR\n')
F.subprocess.run=fakejournal

def fakepopen(argv,**kwargs):
    POPPEN.append(argv);check(callable(kwargs['preexec_fn']) and len(kwargs['pass_fds'])==1,'same slot and owned limit callable');raise PrebirthBoundary('SYNTHETIC-POPEN-BOUNDARY-NO-CHILD')
F.subprocess.Popen=fakepopen

def fakeexec(executable,argv):
    EXEC.append(argv);check(executable==M.PYTHON and argv[:5]==[M.PYTHON,'-I','-B','-S',str(own/'root_bind_existing_consumer_once.py')],'exact caller exec argv')
    caller=synthetic_load(F.ref(own/'root_bind_existing_consumer_once.py'),'SYNTHETIC_FINAL_HANDOFF_CALLER')
    prior=sys.argv;sys.argv=argv[4:]
    try:caller.main()
    finally:sys.argv=prior
F.os.execv=fakeexec

if CONTROL.startswith('source_drift_'):
    target=CONTROL.removeprefix('source_drift_');put(own/target,(own/target).read_bytes()+b'\n# SYNTHETIC DRIFT\n',True)
elif CONTROL=='freeze_parse_CAS':
    original_ref=F.ref
    def racing_ref(p):
        r=original_ref(p)
        if Path(p)==own/'SOURCE-FREEZE.json':put(Path(p),dict(freeze,SYNTHETIC='race-after-pin'))
        return r
    F.ref=racing_ref
elif CONTROL=='root_acceptance_drift':put(F.J,dict(rootaccept,execution_authority=True))
elif CONTROL=='first_review_wrong_freeze':put(F.T/'review/FIRST-SOURCE-REVIEW.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':'0'*64,'open_critical_defects':[]})
elif CONTROL=='root_plan_hash':planref['sha256']='0'*64
elif CONTROL=='O_once_changed':put(Path(oldonce['path']),dict(jsonread(oldonce),no_retry=False))
elif CONTROL=='X_binding_changed':put(Path(xbinding['path']),dict(jsonread(xbinding),authority={}))
elif CONTROL=='X_dispatch_present':put(X/'work/ROOT-DISPATCH-INVOCATION.json',{'SYNTHETIC':'dispatch'})
elif CONTROL=='judgment_unknown':judgment['no_unknown_consumer_effect']=False;plan['prebirth_judgment']=put(Path(judgmentref['path']),judgment);planref=put(Path(planref['path']),plan)
elif CONTROL=='carrier_symlink':(H/'logs/synthetic-link').symlink_to(H/'logs/metadata-only-carrier')
elif CONTROL=='authority_expired':pass # real adapter admission receives an expired declared synthetic wall time
elif CONTROL=='constructor_manager':v=jsonread(constructorref);v['external_manager_source_inference']='SYNTHETIC external manager';plan['constructor_acceptance']=put(Path(constructorref['path']),v);planref=put(Path(planref['path']),plan)
elif CONTROL=='private_root_intersection':privacy['effective_product_roots']=sorted([str(H),str(F.Y)]);c['root_proofs']['private_password_handling']=put(Path(c['root_proofs']['private_password_handling']['path']),privacy);plan['original_prepared_contract']=put(Path(originalcontract['path']),c);planref=put(Path(planref['path']),plan)

caught=None;prepared=False
try:
    F.main(['--prepare',planref['path'],planref['sha256']]);prepared=True
    check(not (F.Y/'CONSUMER-CLOCK.json').exists() and not any((F.Y/'work').iterdir()),'prepare no clock/once/currentgrant/consumer')
    finalreview={'schema':'frw.Root.F06.Task29.finalizer-review.v1','decision':'ACCEPT_ROOT_FINALIZER_NO_LIVE_GRANT','root_finalizer':F.ref(F.__file__),'root_bulk_decision':F.ref(F.Y/'ROOT-BULK-DECISION.json'),'root_source_acceptance':rootacceptref,'open_critical_defects':[]}
    rr=put('final-review.json',finalreview)
    if CONTROL=='final_review_code_hash':finalreview['root_finalizer']['sha256']='0'*64;rr=put(Path(rr['path']),finalreview)
    elif CONTROL=='bulk_contract_drift':put(F.Y/'CONTRACT.PREPARED-NO-CLOCK.json',{})
    elif CONTROL=='prior_work_once':put(F.Y/'work/ROOT-FIRST-CONSUMER-ONCE.json',{'SYNTHETIC':'closed'})
    elif CONTROL=='prior_new_clock':put(F.Y/'CONSUMER-CLOCK.json',{'SYNTHETIC':'closed'})
    F.main(['--execute-once',planref['path'],planref['sha256'],rr['path'],rr['sha256']])
except BaseException as e:caught=type(e).__name__+':'+str(e)
positive=CONTROL=='positive'
if positive:
    check(caught=='PrebirthBoundary:SYNTHETIC-POPEN-BOUNDARY-NO-CHILD','positive reaches real caller Popen boundary: '+str(caught))
    check(len(EXEC)==len(POPPEN)==1 and len(JOURNAL)==1,'exact one caller and fakePopen')
    inputs=jsonread(F.ref(F.Y/'ROOT-CONSUMER-INPUTS.json'));binding=jsonread(F.ref(F.Y/'work/ROOT-ACTUAL-BINDING.json'))
    check(A.successor(BASE.read_bytes(),binding['contract'],(own/'f06_footer.py.txt').read_bytes())==Path(binding['source']['path']).read_bytes(),'exact full source binding JSON reconstruction')
    check(inputs['contract']['run_id']==M.ORIGINAL_RUN and inputs['contract']['scenario_sha256']==M.ORIGINAL_SCENARIO_SHA,'original identity')
else:
    check(caught is not None and not POPPEN,'negative refuses before fakePopen')
    expected={'authority_expired':'F06_EXISTING_AUTHORITY_EXPIRED_OR_TIMES_CHANGED','private_root_intersection':'F06 private source/proof directory intersects effective product root','code_drift_after_load':'F06 pinned reference drift','freeze_parse_CAS':'ROOT_REFERENCE_CAS_CHANGED','current_changed':'ROOT_MUTABLE_BASIS_CHANGED_BEFORE_CLOCK'}
    if CONTROL in expected:check(expected[CONTROL] in caught,'specific intended negative reason: '+caught)
    if CONTROL.startswith('source_drift_') or CONTROL in ('root_acceptance_drift','first_review_wrong_freeze','root_plan_hash','freeze_parse_CAS'):check(not LOADS,'source/Root CAS refuses before executable dependency load')
    check(not EXEC,'negative before caller exec')
check(not AUDIT['denied'] and AUDIT['real_subprocess']==0 and AUDIT['network']==0,'owned audit confinement')
result={'control':CONTROL,'passed':True,'caught':caught,'prepared':prepared,'dependency_loads':LOADS,'exec_sentinels':len(EXEC),'Popen_sentinels':len(POPPEN),'journal_metadata_synthetic':len(JOURNAL),'audit_denied':AUDIT['denied'],'real_process_or_network':0,'declared_synthetic':'all host/current/authority/scenario/closure observations; exact Root helper copied source and full caller/adapter/current typed semantic/private methods; no actual current/private truth'}
put(CASE/'RESULT.json',result);print(json.dumps(result))
