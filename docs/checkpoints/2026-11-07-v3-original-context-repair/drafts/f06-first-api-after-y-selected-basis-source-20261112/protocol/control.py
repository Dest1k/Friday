"""Owned source-only whole-caller stand; never a product/tester execution role.

The exact caller main/execute and exact producer validations run. Host observation
is explicitly synthetic and dependency-injected only here, after pinned load.
"""
import ast, copy, contextlib, datetime, fcntl, hashlib, io, json, locale, math, os
import pathlib, re, resource, signal, socket, sqlite3, stat, subprocess, sys, time, types
import uuid
import encodings.unicode_escape, encodings.utf_8, encodings.ascii
from pathlib import Path

ast.unparse(ast.parse('0'))  # Prewarm stdlib lazy unparser before deny-all import boundary.
os.umask(0o077)
HERE=Path(__file__).resolve().parent
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
CASE=HERE/'cases'/sys.argv[1]
CASE.mkdir(mode=0o700,parents=True)
CONTROL=sys.argv[2]
exec(compile((HERE/'selected_fixture.py').read_bytes(),str(HERE/'selected_fixture.py'),'exec'),globals())
SNAPSHOT=HERE/sys.argv[3]
AUDIT={'opens':[],'denied':[],'imports':[],'metadata':[],'real_subprocess':0,'network':0}
EVENTS=[];REAL_POPEN=subprocess.Popen;REAL_EXECV=os.execv;FAKE_WAITS=[]
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

# Exact source bytes and inert top-level statements verified before any source import.
PINSET=json.loads((HERE/'INPUT-PINS.json').read_bytes())['frozen_inputs']
INERT_VERIFIED=[]
for leaf in ('f06_source.py','current207.py','root_bind_existing_consumer_once.py','root_first_api_after_y.py','y_custody_delta.py','postboot_transition.py'):
    data=(SNAPSHOT/leaf).read_bytes();key=('source/'+leaf if 'source/'+leaf in PINSET else leaf)
    check(sha(data)==PINSET[key]['sha256'],'final production source pin before import')
    for node in ast.parse(data).body:
        check(isinstance(node,(ast.Expr,ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef,ast.ClassDef,ast.If)),'inert source top-level statement')
        if isinstance(node,ast.Expr):check(isinstance(node.value,ast.Constant) and isinstance(node.value.value,str),'only module docstring expressions')
        if isinstance(node,ast.Assign):
            check(all(ast.unparse(call.func) in ('Path','str','dict','tuple','sorted','Path(__file__).resolve','STRICT_MODULE_DESCRIPTOR.copy') for call in ast.walk(node) if isinstance(call,ast.Call)),'inert constant constructors only')
        if isinstance(node,ast.If):check(ast.unparse(node.test)=="__name__ == '__main__'",'only explicit main guard')
    INERT_VERIFIED.append(leaf)
own,pins=sourcecopy()
M=module(own/'root_bind_existing_consumer_once.py','SYNTHETIC_REAL_FIRST_CALLER')
PRODUCTION_AUTHORITY_TIMES={'created_at':M.EXISTING_CREATED,'expires_at':M.EXISTING_EXPIRES}
A=module(own/'f06_source.py','SYNTHETIC_REAL_FIRST_ADAPTER_FOR_FIXTURE')
fakeproc=CASE/'SYNTHETIC-proc';fakeproc.mkdir(mode=0o700)
put(fakeproc/'sys/kernel/random/boot_id',(BOOT+'\n').encode(),True)
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
M.EXISTING_CREATED=PRODUCTION_AUTHORITY_TIMES['created_at']
M.EXISTING_EXPIRES=PRODUCTION_AUTHORITY_TIMES['expires_at']
if CONTROL=='root_authority_expired':M.EXISTING_CREATED=PRODUCTION_AUTHORITY_TIMES['created_at'];M.EXISTING_EXPIRES=PRODUCTION_AUTHORITY_TIMES['expires_at']
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
O={'schema':'friday.root.F06.first-driver-prebirth-refusal-closure.v1','at_moscow':datetime.datetime.fromtimestamp(M.EXISTING_CREATED+60,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'state':'DRIVER_CLOSED_AFTER_ISSUANCE_BEFORE_BIND_OR_CONSUMER_BIRTH_NO_SEND','driver_exit_code':1,'actual_root_driver_pid':910001,'actual_root_driver_absent':True,'consumer_birth':False,'dispatch_invocation_absent':True,'canonical_run_absent':True,'actual_issued_authority':M.EXISTING_AUTHORITY,'actual_authority_id':M.EXISTING_AUTHORITY_ID,'authority_scope_scenario_correct':True,'no_API_client_created':True,'reissue_retry_resume_or_rename_authorized':False,'once_claim_preserved':oldonce,'original_clock':oldclock,'original_clock_endpoints_preserved':oldclockdata}
M.PREBIRTH_CLOSURE=put(M.ORIGINAL_DIR/'PREBIRTH-ISSUER-ONLY-CLOSURE.json',O)
xonce=put(X/'work/ROOT-FIRST-CONSUMER-ONCE.json',{'schema':'frw.Root.F06.first-consumer-invocation.v1','run_id':M.ORIGINAL_RUN,'no_retry':True,'issuer_invoked':False,'old_driver_resume':False,'existing_authority':M.EXISTING_AUTHORITY,'prebirth_closure':M.PREBIRTH_CLOSURE})
xclockdata=dict(oldclockdata,schema='frw.Root.F06.unstarted-consumer-finite-clock.v1')
xclock=put(X/'CONSUMER-CLOCK.json',xclockdata)
xsource=put(X/'work/bot_tester.f06.root-bound.py',b'# SYNTHETIC closed failed source, never imported\n',True)
xbinding=put(X/'work/ROOT-ACTUAL-BINDING.json',{'schema':'frw.Root.F06.exact-first-wrongread-binding.v1','source':xsource,'authority':M.EXISTING_AUTHORITY,'contract':{'run_id':M.ORIGINAL_RUN,'authority':M.EXISTING_AUTHORITY,'authority_id':M.EXISTING_AUTHORITY_ID,'scenario_sha256':M.ORIGINAL_SCENARIO_SHA,'scope':A.scope(),'resources':{'clock':xclock}}})
XC={'schema':'friday.root.F06.firstconsumer-binding-prebirth-refusal-closure.v1','at_moscow':datetime.datetime.fromtimestamp(M.EXISTING_CREATED+90,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'state':'FIRST_CONSUMER_BINDING_CREATED_RECONSTRUCTION_REFUSED_BEFORE_DISPATCH_NO_SEND','driver_exit_code':1,'actual_root_driver_pid':910002,'actual_root_driver_absent':True,'consumer_born':False,'dispatch_created':False,'canonical_run_created':False,'source_file':xsource,'actual_binding':xbinding,'whole_contract_values_equal_after_json':True,'all_non_contract_AST_equal':True,'source_reconstruction_guard_preserved':True,'failure':'F06_SERIALIZED_BINDING_NOT_RECONSTRUCTIBLE','no_API_client_or_upload_or_model_based_on_actual_control_flow':True,'existing_R106_not_reissued':True,'consumer_stage_once_preserved':xonce,'original_consumer_clock_preserved':xclock,'old_issuer_only_once_clock_preserved':True,'no_old_driver_or_issuer_retry':True}
xclosure=put(X/'PREBIRTH-BINDING-RECONSTRUCTION-REFUSAL-CLOSURE.json',XC)
for name in ('BINDING_PREBIRTH_CLOSURE','PREBIRTH_BINDING_CLOSURE','BINDING_FAILURE_CLOSURE'):
    if hasattr(M,name):setattr(M,name,xclosure)

work=SyntheticPath(CASE/'unused-old-fixture-work');work.mkdir(mode=0o700)
c=A.unbound();c.update(status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',run_id=M.ORIGINAL_RUN,scenario_ref=scenario_ref,scenario_sha256=M.ORIGINAL_SCENARIO_SHA,authority=M.EXISTING_AUTHORITY,authority_id=M.EXISTING_AUTHORITY_ID,authority_chain={'predecessor':predecessor,'predecessor_authority_id':'SYNTHETIC-predecessor','created_at':M.EXISTING_CREATED,'expires_at':M.EXISTING_EXPIRES})
def localref(leaf):
    raw=(own/leaf).read_bytes();return {'path':str(own/leaf),'bytes':len(raw),'sha256':sha(raw)}
c.update(adapter=localref('f06_source.py'),footer=localref('f06_footer.py.txt'),actual_root_B_checker=localref('current207.py'))
c['root_proofs']={k:put('proofs/SYNTHETIC-'+k+'.json',{'SYNTHETIC':k}) for k in A.PROOFS}
c['product']=dict(module(own/'current207.py','SYNTHETIC_EXPECTED_INSTALLED_METADATA_ONLY').EXPECTED)
boundary={k:'4'*64 for k in A.BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}}
boundary.update(gateway={'SYNTHETIC':True,'pid':910003,'start_time':1},B={'profile':'telegram-bot-8812646969','session_id':'SYNTHETIC-SESSION','session_key':'SYNTHETIC-KEY','native_max_id':0},phase_unconsumed=True,uploads_this_operation=1,producer_calls=0,restarts=0)
c['boundary']=boundary
clockdata={'schema':'frw.Root.F06.unstarted-consumer-finite-clock.v1','started_at':time.time()-1,'deadline_at':time.time()+590,'started_monotonic':time.monotonic()-1,'deadline_monotonic':time.monotonic()+590,'boot_id':'SYNTHETIC-BOOT-ID'}
c['resources']=dict(A.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=64*1024**2,clock=put('SYNTHETIC-future-clock.json',clockdata),owned_parent_wait_cleanup=put('SYNTHETIC-cleanup-policy.json',{'SYNTHETIC':'owned stop policy descriptor'}))
c['source']=fake_source
freeze=json.loads((SNAPSHOT/'SOURCE-FREEZE.json').read_bytes());check(freeze['files']==pins,'exact final four file freeze')
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
if CONTROL=='Y_historical_recon_false':reconciliation['old_driver_closed_and_absent']=False
reconciliation_ref=put('SYNTHETIC-reconciliation.json',reconciliation)
si=M.SLOT.stat();slot_identity={'device':si.st_dev,'inode':si.st_ino,'uid':si.st_uid,'mode':stat.S_IMODE(si.st_mode),'nlink':si.st_nlink}
v={'schema':'frw.Root.F06.canonical-existing-R106-first-consumer.v1' if freeze['schema'].startswith('frw.F06.canonical') else 'frw.Root.F06.existing-R106-first-consumer.v1','status':'ROOT_BOUND_SEPARATE_UNSTARTED_CONSUMER','contract':c,'source_freeze':freeze_ref,'independent_review':review,'workdir':str(work),'slot_identity':slot_identity,'expected_binding_sha256':None,'prebirth_closure':M.PREBIRTH_CLOSURE,'prebirth_reconciliation':reconciliation_ref}
if freeze['schema'].startswith('frw.F06.canonical'):v['binding_prebirth_closure']=xclosure

# Task31 Root frame integration. All concrete truths below are EXPLICIT SYNTHETIC.
# setup_y_fixture is inserted from the pinned sibling interface before execution.
F=module(SNAPSHOT/'root_first_api_after_y.py','SYNTHETIC_REAL_TASK31_ROOT_FRAME')
F.__file__=str(CASE/'Root/root_first_api_after_y.py')
put(Path(F.__file__),(SNAPSHOT/'root_first_api_after_y.py').read_bytes(),True)
F.Path=SyntheticPath;F.B=CASE/'B';F.T=CASE/'T';F.O=M.ORIGINAL_DIR;F.X=X;F.OLD_Y=CASE/'SYNTHETIC-Y-CLOSED';F.Y=CASE/'Root';F.C=own;F.J=F.B/'SYNTHETIC-TASK31-SOURCE-ACCEPTANCE.json';F.PYTHON=M.PYTHON
put(F.Y/'y_custody_delta.py',(SNAPSHOT/'y_custody_delta.py').read_bytes(),True)
F.FRAME_SUPPORT_SHA=sha((F.Y/'y_custody_delta.py').read_bytes())
put(F.Y/'postboot_transition.py',(SNAPSHOT/'postboot_transition.py').read_bytes(),True)
check(F.POSTBOOT_HELPER_SHA==sha((F.Y/'postboot_transition.py').read_bytes()),'exact frozen selected-basis helper')
fr=put(own/'SOURCE-FREEZE.json',(SNAPSHOT/'SOURCE-FREEZE.json').read_bytes(),True);check(F.FIRST_FREEZE_SHA==fr['sha256'],'unchanged final freeze pin')
review=put(F.T/'review/FIRST-SOURCE-REVIEW.json',{'decision':'SOURCE_ONLY_READY_UNBOUND','source_freeze_sha256':fr['sha256'],'open_critical_defects':[]})
reader=put(F.T/'review/BOUNDED-READER-ROOT-ACCEPTANCE.json',{'schema':'friday.root.F06.bounded-reader-R2-source-acceptance.v1','operator':'Root','state':'ROOT_ACCEPTED_F06_BOUNDED_READER_COMPONENTS_SOURCE_RUNTIME_INTEGRATION_UNBOUND','branch_freezes':{'first':{'sha256':'4925dcfb564c7cad0c29223bd5e58b29cd7a47dbec1b7d8aef5a38ae4a7941f6'}},'open_material_source_defects':[],'new_admission_or_clock_or_goal':False,'ordinary_semantic_or_F06_acceptance':False,'SYNTHETIC':'explicit ownfixture Root acceptance, not actual Root judgement'});F.BOUNDED_READER_ACCEPTANCE=reader
component={'schema':'frw.Root.F06.Task31.component-source-acceptance.v1','operator':'Root','decision':'ROOT_ACCEPTED_SOURCE_ONLY_MISSING_FIRST_API_UNBOUND','source_freeze':fr,'source_files':{leaf:localref(leaf) for leaf in F.LEAVES},'custody_delta_source':F.ref(F.Y/'y_custody_delta.py'),'first_source_review':review,'bounded_reader_root_acceptance':reader,'runtime_authority':False,'open_critical_defects':[]}
componentref=put(F.J,component)
frame={'schema':'frw.Root.F06.Task31.frame-source-acceptance.v1','operator':'Root','decision':'ROOT_ACCEPTED_FRAME_SOURCE_ONLY_UNBOUND','root_finalizer':F.ref(F.__file__),'custody_delta_source':F.ref(F.Y/'y_custody_delta.py'),'source_freeze':fr,'component_acceptance':componentref,'runtime_authority':False,'open_critical_defects':[]}
frameref=put(F.T/'review/FRAME-ACCEPTANCE.json',frame)
# The strict typed history/private/lineage inputs retain the proven T29 fixture.
actual={'f06_mutable_boundary':boundary,'profile_configs':{},'databases':{'tester':{'principal':{'SYNTHETIC':True}}},'history':{'manifest_sha256':'5'*64,'run_ids':[]},'source_identity':{'SYNTHETIC':True},'gateway':{'pid':910003}}
# Reuse the child's faithful, explicitly synthetic all-three-DB/custody fixture.
y=module(SNAPSHOT/'y_custody_delta.py','SYNTHETIC_FIXTURE_INTERFACE_ONLY')
exec(compile((HERE/'observation_fixture.py').read_bytes(),str(HERE/'observation_fixture.py'),'exec'),globals())
old_actual,actual=fixture_pair()
for observed in (old_actual,actual):
    observed['installed_product']=dict(c['product']);observed['profile_configs']={}
    observed['source']=dict(fake_source);observed['gateway']=dict(boundary['gateway'])
    observed['services']['gateway']['identity']=dict(boundary['gateway'])
    observed['native_readonly']['identity']=dict(boundary['gateway'])
    observed['f06_mutable_boundary']['gateway']=dict(boundary['gateway'])
    observed['f06_mutable_boundary']['B']=dict(boundary['B'])
    observed['source_identity']['size_bytes']=fake_source['bytes']
    observed['databases']['tester']['principal'].update(id=boundary['B']['session_id'],session_key=boundary['B']['session_key'],profile_name=boundary['B']['profile'])
    refresh(observed)
runtime_fixture(old_actual,old=True);runtime_fixture(actual)
SYNTHETIC_OLD_CUSTODY=old_actual['custody']['sha256'];SYNTHETIC_NEW_CUSTODY=actual['custody']['sha256']
boundary=old_actual['f06_mutable_boundary']
H=CASE/'SYNTHETIC-H';(H/'logs').mkdir(parents=True,mode=0o700);put(H/'logs/metadata-only-carrier',b'SYNTHETIC-CONTENT-NOT-READ',True)
closure=put('proofs/installed-closure.json',{'source_acceptance':put('proofs/installed-acceptance.json',{'SYNTHETIC':True})})
privacy={'schema':'frw.Root.F06.installed207-runtime-privacy-review.v1','operator':'Root','status':'ROOT_BOUND','installed_product':c['product'],'runtime_hashes':module(own/'current207.py','SYNTHETIC_INTERFACE_CONSTANTS').RUNTIME_HASHES,'genuine_installed_runtime_consumer_observed':True,'no_marker_or_import_bypass':True,'raw_user_chat_retention_separately_reviewed':True,'no_blanket_no_secret_persistence_claim':True,'Standard3_2_data_integrity_verified':False,'runtime_evidence':[predecessor],'effective_product_roots':[str(H)],'effective_roots_profile_config_refs':{},'effective_roots_source_basis':[predecessor],'private_roots':sorted(str(CASE/n) for n in ('Root','SYNTHETIC-O-CLOSED','SYNTHETIC-X-CLOSED','SYNTHETIC-Y-CLOSED','proofs','private-input','private-authority','private-scenario','T','B')),'scope':'SYNTHETIC scoped old qualification'}
c['root_proofs']['private_password_handling']=put('proofs/private.json',privacy)
history={'schema':'frw.Root.F06.history-semantic-once.v1','operator':'Root','status':'ROOT_BOUND','phase':A.PHASE,'source':fake_source,'history_manifest_sha256':old_actual['history']['manifest_sha256'],'classified_run_ids':old_actual['history']['run_ids'],'native_boundary_sha256':boundary['native_boundary_sha256'],'once_sha256':boundary['once_sha256'],'ingress_lineage_sha256':boundary['ingress_lineage_sha256'],'equivalent_original_phase_effects':[],'all_profile_history_and_compacted_unlogged_equivalents_reconciled':True,'old_effects_UNKNOWN_and_clocks_preserved':True,'M14_partial_UNKNOWN_preserved_no_replay_or_regrade':True,'all_profile_projection_limit':'ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED','retained_basis':[predecessor,predecessor]}
c['root_proofs']['all_profile_history_semantic_once']=put('proofs/history.json',history)
lineage={'schema':'frw.Root.F06.retained-g6-source-lineage.v1','operator':'Root','status':'ROOT_BOUND','phase':A.PHASE,'source':fake_source,'source_identity':actual['source_identity'],'current_ingress_lineage_sha256':boundary['ingress_lineage_sha256'],'original_producer_g6_retained':True,'no_new_producer_or_native_repeat':True,'first_ordinary_upload_not_previously_consumed':True,'native_qualification':c['root_proofs']['actual_native_qualification'],'retained_producer_oracle_basis':[predecessor]}
c['root_proofs']['source_ingress_lineage']=put('proofs/lineage.json',lineage)
basis=put('proofs/constructor-basis.json',{'source_files':{'SYNTHETIC':{'ref':predecessor}}})
constructorref=put(F.O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json',{'decision':'ROOT_ACCEPT_SCOPED_SOURCE_CONFIG_INFERENCE','effective_product_roots':[str(H)],'profile_configs':{},'external_manager_source_inference':'CORE_NO_EXPLICIT_HANDOFF_NO_MANAGER_CONSTRUCTED','result':predecessor,'basis':basis,'proxy_scope_metadata':[]})
# Explicit inert Y born/closed history; none of these source copies are imported.
M.Y_DIR=F.OLD_Y;(M.Y_DIR/'work').mkdir(parents=True,mode=0o700)
ywall=M.EXISTING_CREATED+180
ymono=1.0
yclockdata=dict(schema='frw.Root.F06.unstarted-consumer-finite-clock.v1',started_at=ywall,deadline_at=ywall+600,started_monotonic=ymono,deadline_monotonic=ymono+600,boot_id=OLD_BOOT)
yclock=put(M.Y_DIR/'CONSUMER-CLOCK.json',yclockdata)
y_source_pins={}
for oldleaf in F.LEAVES:
    y_source_pins[oldleaf]=put(M.Y_DIR/'source'/oldleaf,b'# SYNTHETIC historical inert source, never imported\n',True)
yfreeze=put(M.Y_DIR/'source/SOURCE-FREEZE.json',dict(schema='frw.F06.canonical-existing-R106-first-consumer.source-freeze.v1',files={k:{n:v[n] for n in ('bytes','sha256')} for k,v in y_source_pins.items()}))
F.Y_PROOF=put(M.Y_DIR/'work/ROOT-FRESH-CURRENT-PROOF.json',dict(observed=old_actual,SYNTHETIC='explicit retained original observation fixture'))
F.Y_DELTA=put(M.Y_DIR/'POST-REFUSAL-CUSTODY-DELTA.json',dict(SYNTHETIC='diagnostic-only custody observation fixture',old_sha256=old_actual['custody']['sha256'],new_sha256=actual['custody']['sha256']))
# Historical O/X reconciliation belongs to Y birth, not the new API clock.
reconciliation['created_at']=yclockdata['started_at']-20;reconciliation['expires_at']=yclockdata['started_at']+90
reconciliation_ref=put(Path(reconciliation_ref['path']),reconciliation)
c['resources']['clock']=yclock
old_input_c=copy.deepcopy(c)
oldinputs=dict(v,contract=old_input_c,source_freeze=yfreeze,prebirth_reconciliation=reconciliation_ref)
oldinputs.pop('y_reconciliation',None)
oldinputsref=put(M.Y_DIR/'ROOT-CONSUMER-INPUTS.json',oldinputs)
yonce=put(M.Y_DIR/'work/ROOT-FIRST-CONSUMER-ONCE.json',dict(schema='frw.Root.F06.canonical-first-consumer-invocation.v1',at=yclockdata['started_at']+5,run_id=M.ORIGINAL_RUN,existing_authority=M.EXISTING_AUTHORITY,prebirth_closure=M.PREBIRTH_CLOSURE,binding_prebirth_closure=M.BINDING_PREBIRTH_CLOSURE,old_driver_resume=False,issuer_invoked=False,no_retry=True,source_freeze=yfreeze,binding=oldinputsref))
ysource=put(M.Y_DIR/'work/bot_tester.f06.root-bound.py',b'# SYNTHETIC old Y bound source, never imported\n',True)
yboundc=copy.deepcopy(old_input_c);yboundc['root_current_proof']=F.Y_PROOF
yeffect='6'*64
ybinding=put(M.Y_DIR/'work/ROOT-ACTUAL-BINDING.json',dict(schema='frw.Root.F06.exact-first-wrongread-binding.v1',source=ysource,authority=M.EXISTING_AUTHORITY,contract=yboundc,whole_effect_sha256=yeffect))
yargv=[M.PYTHON,'-I','-B','-S',ysource['path'],'--state-dir',str(M.STATE),'run','--run-id',M.ORIGINAL_RUN,'--scenario',c['scenario_ref']['path']]
ydispatch=put(M.Y_DIR/'work/ROOT-DISPATCH-INVOCATION.json',dict(state='ONE_UNSTARTED_USER_CONSUMER_AFTER_TWO_CLOSED_PREBIRTH_FAILURES_NO_RETRY',argv=yargv,source=ysource,clock=yclock,whole_effect_sha256=yeffect))
yactor=put(M.Y_DIR/'work/ROOT-CONSUMER-ACTOR.json',dict(pid=910004,SYNTHETIC=True))
yended=put(M.Y_DIR/'work/ROOT-DISPATCH-ENDED.json',dict(schema='frw.Root.F06.original-consumer-ended.v1',exit_code=2,actor_absent=True,canonical_run=None,acceptance='NOT_ESTABLISHED'))
M.Y_HISTORY_PINS={str(Path(r['path']).relative_to(M.Y_DIR)):r for r in [yclock,yfreeze,*y_source_pins.values(),ybinding,yactor,yended,ydispatch,yonce,F.Y_PROOF,ysource]}
synthetic_hz=100
M.os.sysconf=lambda name:synthetic_hz
observed=dict(Y_consumer_did_start=True,raw_status_preserved='REFUSED_OR_UNKNOWN',actor_pid=910004,parent_pid=910005,actor_start_time=int((yclockdata['started_monotonic']+10)*synthetic_hz))
yreview={'schema':'frw.independent-review.F06-Y-preintent-no-send.v1','recommendation':'ACCEPT_ROOT_CLOSURE_CLASSIFICATION_WITH_EXPLICIT_SOURCE_DERIVED_INNER_CAUSE_LIMITATION','observed':observed,'reader_cause_assessment':{'original_nested_exception_observed':False},'exact_pins':M.Y_HISTORY_PINS}
M.Y_INDEPENDENT_REVIEW=put('proofs/SYNTHETIC-Y-independent-review.json',yreview)
yclosed={'schema':'friday.root.F06.first-consumer-preintent-guard-closure.v1','at_moscow':datetime.datetime.fromtimestamp(ywall+700,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'state':'ACTUAL_CONSUMER_BORN_CLOSED_REFUSED_IN_NEW_BEFORE_SAVE_OR_BOTAPI_REQUEST','consumer_exit_code':2,'consumer_actor_absent':True,'parent_slot_owner_absent':True,'slot_free':True,'canonical_run_absent':True,'BotAPI_client_constructed':True,'upload_model_reply_Office':False,'raw_status_preserved':'REFUSED_OR_UNKNOWN','actual_original_nested_exception_was_retained':False,'nested_cause_classification':'SOURCE_DERIVED_REPRODUCTION_NOT_ORIGINAL_RETAINED_EXCEPTION','retry_or_followup_authorized_by_this_record':False}
M.Y_PREINTENT_CLOSURE=put(M.Y_DIR/'PREINTENT-GUARD-REFUSAL-CLOSURE.json',yclosed)
yassessment={'schema':'friday.root.F06.Y.saved-preintent-assessment.v1','at_moscow':datetime.datetime.fromtimestamp(ywall+750,datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'operator':'Root','state':'ACCEPT_SOURCE_DERIVED_NO_USER_BOTAPI_BEFORE_CURRENT_GATE_REFUSAL_RAW_UNKNOWN_PRESERVED','original_closure':M.Y_PREINTENT_CLOSURE,'independent_review':M.Y_INDEPENDENT_REVIEW,'consumer_born_and_closed':True,'BotAPI_client_constructed':True,'raw_status':'REFUSED_OR_UNKNOWN','canonical_run_created':False,'first_user_upload_or_model_or_reply':'NOT_RUN','ordinary_semantic_or_F06_acceptance':False,'automatic_retry_or_followup_authorized':False}
M.Y_SAVED_ASSESSMENT=put('proofs/SYNTHETIC-Y-Root-assessment.json',yassessment)
selected_documents()
if CONTROL=='coherent_unselected_runtime':
    actual['gateway']['pid']+=100
    actual['services']['gateway']['identity']=dict(actual['gateway']);actual['services']['gateway']['unit']['MainPID']=str(actual['gateway']['pid'])
    actual['native_readonly']['identity']=dict(actual['gateway']);actual['f06_mutable_boundary']['gateway']=dict(actual['gateway'])
component.update(postboot_transition_source=F.ref(F.Y/'postboot_transition.py'),postboot_basis=BASIS)
componentref=put(F.J,component)
frame.update(postboot_transition_source=F.ref(F.Y/'postboot_transition.py'),postboot_basis=BASIS,component_acceptance=componentref)
frameref=put(Path(frameref['path']),frame)
historical_cas=[M.EXISTING_AUTHORITY,oldonce,oldclock,xonce,xclock,xsource,xbinding,M.PREBIRTH_CLOSURE,xclosure,*M.Y_HISTORY_PINS.values(),M.Y_PREINTENT_CLOSURE,M.Y_SAVED_ASSESSMENT,M.Y_INDEPENDENT_REVIEW,oldinputsref]

originalcontract=put(F.OLD_Y/'CONTRACT.PREPARED-NO-CLOCK.json',c)
judgment={'schema':'frw.Root.F06.Y-postboot-current-first-API-judgment.v1','operator':'Root','status':'ROOT_ACTUAL_RECONCILED_POSTBOOT_CURRENT_MISSING_FIRST_API_ONLY','prebirth_closure':M.PREBIRTH_CLOSURE,'binding_prebirth_closure':M.BINDING_PREBIRTH_CLOSURE,'y_preintent_closure':M.Y_PREINTENT_CLOSURE,'y_saved_assessment':M.Y_SAVED_ASSESSMENT,'y_independent_review':M.Y_INDEPENDENT_REVIEW,'existing_authority':M.EXISTING_AUTHORITY,'original_run_id':M.ORIGINAL_RUN,'scenario_sha256':M.ORIGINAL_SCENARIO_SHA,'y_fresh_proof':F.Y_PROOF,'custody_delta':F.Y_DELTA}
judgment.update(selected_admission=SELECTED,admission_selection=SELECTION_REF,postboot_basis=BASIS)
judgment.update({k:True for k in F.BOOLS});judgmentref=put('proofs/y-judgment.json',judgment)
plan={'schema':'frw.Root.F06.Task31.first-API-plan.v1','operator':'Root','status':'ROOT_EXPLICIT_PREPARATION_NO_CLOCK_NO_GRANT','root_directory':str(F.Y),'source_directory':str(own),'root_source_acceptance':componentref,'frame_acceptance':frameref,'original_prepared_contract':originalcontract,'y_fresh_proof':F.Y_PROOF,'constructor_acceptance':constructorref,'y_judgment':judgmentref,'selected_admission':SELECTED,'admission_selection':SELECTION_REF,'postboot_basis':BASIS}
planref=put('plan.json',plan)
LOADS=[];POPPEN=[];EXEC=[];JOURNAL=[];DELTA_CALLS=[];ADMISSION_CALLS=[];PIN_SEAMS=[]
real_load=F.load
class PrebirthBoundary(BaseException):pass

def synthetic_load(ref,name):
    LOADS.append(Path(ref['path']).name);m=real_load(ref,name)
    if Path(ref['path']).name=='f06_source.py':
        m.SOURCE=fake_source;m.INSTALLED_TESTER=Path(installed['path']);m.INSTALLED_TESTER_SHA=installed['sha256']
        real_admission=m.admission
        def record_admission(*args,**kwargs):
            ADMISSION_CALLS.append('UNCHANGED_ACTUAL_ADAPTER_ADMISSION');return real_admission(*args,**kwargs)
        m.admission=record_admission
    elif Path(ref['path']).name=='root_bind_existing_consumer_once.py':
        for k in ('Path','STATE','SLOT','ORIGINAL_DIR','PREBIRTH_CLOSURE','EXISTING_AUTHORITY','EXISTING_AUTHORITY_ID','EXISTING_CREATED','EXISTING_EXPIRES','ORIGINAL_RUN','ORIGINAL_SCENARIO_SHA','BINDING_DIR','BINDING_PREBIRTH_CLOSURE','PYTHON','Y_DIR','Y_PREINTENT_CLOSURE','Y_SAVED_ASSESSMENT','Y_INDEPENDENT_REVIEW','Y_HISTORY_PINS','HISTORICAL_HISTORY_SHA256','HISTORICAL_UNKNOWN_IDS','GATEWAY_STATE_PATH'):
            if hasattr(M,k):setattr(m,k,getattr(M,k))
        m.load=synthetic_load
    elif Path(ref['path']).name=='current207.py':
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
            m.validate_effect(proof);m.semantic(proof,dict(proof['contract_effect'],authority=SELECTED,authority_id=ROOT_CURRENT['authority_id'],status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',root_current_proof=F.ref(p)),actual)
            return {'whole_effect_sha256':proof['whole_effect_sha256']}
        m.check=proofcheck
    elif Path(ref['path']).name=='y_custody_delta.py':
        # Declared test-only immutable pin seam; real production validator unchanged.
        m.OLD_CUSTODY_SHA256=SYNTHETIC_OLD_CUSTODY;m.NEW_CUSTODY_SHA256=SYNTHETIC_NEW_CUSTODY
        real_expected=m.expected_evidence
        def fixture_expected():
            evidence=real_expected();evidence['saved_assessment']=M.Y_SAVED_ASSESSMENT;return evidence
        m.expected_evidence=fixture_expected
        PIN_SEAMS.append({'module':'y_custody_delta','globals':['OLD_CUSTODY_SHA256','NEW_CUSTODY_SHA256'],'expected_evidence_provider_changed_keys':['saved_assessment'],'production_validator_code_unchanged':True})
        original=m.validate_y_custody_delta
        def recorded_delta(*args,**kwargs):
            DELTA_CALLS.append('REAL_VALIDATOR_SYNTHETIC_HASH_PINS');return original(*args,**kwargs)
        m.validate_y_custody_delta=recorded_delta
    elif Path(ref['path']).name=='postboot_transition.py':
        strict=synthetic_load(F.ref(F.Y/'y_custody_delta.py'),'SYNTHETIC_STRICT_EVIDENCE_SCHEMA')
        m.OLD_CUSTODY_SHA256=SYNTHETIC_OLD_CUSTODY;m.NEW_CUSTODY_SHA256=SYNTHETIC_NEW_CUSTODY
        m.OLD_PROOF_SHA256=F.Y_PROOF['sha256'];m.STRICT_EVIDENCE_SHA256=sha(encoded(strict.expected_evidence()))
        PIN_SEAMS.append({'module':'postboot_transition','globals':['OLD_CUSTODY_SHA256','NEW_CUSTODY_SHA256','OLD_PROOF_SHA256','STRICT_EVIDENCE_SHA256'],'production_validator_code_unchanged':True})
        original=m.validate_postboot_y_transition
        def record_postboot(*args,**kwargs):
            DELTA_CALLS.append('REAL_POSTBOOT_VALIDATOR');return original(*args,**kwargs)
        m.validate_postboot_y_transition=record_postboot
    else:raise AssertionError('undeclared load '+Path(ref['path']).name)
    return m
F.load=synthetic_load

def fakejournal(argv,**kwargs):
    JOURNAL.append(argv);check(argv==['journalctl','--user','-u','hermes-gateway-1b7e7667.service','-n','0','--show-cursor','--no-pager'],'journal metadata-only command');return types.SimpleNamespace(stdout=b'SYNTHETIC-CURSOR\n')
F.subprocess.run=fakejournal

class FakeActor:
    pid=910006
    def poll(self):return 2
    def wait(self,timeout):FAKE_WAITS.append(timeout);return 2
    def send_signal(self,n):raise AssertionError('already-exited fake actor must not be signaled')
    def terminate(self):raise AssertionError('already-exited fake actor must not be terminated')
    def kill(self):raise AssertionError('already-exited fake actor must not be killed')
def fakepopen(argv,**kwargs):
    POPPEN.append(argv);check(callable(kwargs['preexec_fn']) and len(kwargs['pass_fds'])==1,'same slot and owned limit callable')
    check(argv[4]==str(F.Y/'work/bot_tester.f06.root-bound.py') and argv[7]=='run','exact fresh full consumer argv, never executed')
    return FakeActor()
F.subprocess.Popen=fakepopen

def fakeexec(executable,argv):
    EXEC.append(argv);check(executable==M.PYTHON and argv[:5]==[M.PYTHON,'-I','-B','-S',str(own/'root_bind_existing_consumer_once.py')],'exact caller exec argv')
    if CONTROL.startswith('caller_'):
        iv=jsonread(F.ref(argv[-2]));rc=jsonread(iv['y_reconciliation'])
        if CONTROL=='caller_lineage_missing' or CONTROL=='caller_lineage_readiness':
            lr=iv['contract']['root_proofs']['source_ingress_lineage'];lv=jsonread(lr)
            if CONTROL=='caller_lineage_missing':lv.pop('current_admission_selection')
            else:lv['readiness_evidence']=dict(READINESS,sha256='0'*64)
            iv['contract']['root_proofs']['source_ingress_lineage']=put(Path(lr['path']),lv)
        elif CONTROL=='caller_clock_wrongboot' or CONTROL=='caller_clock_before_recovery':
            cl=jsonread(iv['contract']['resources']['clock'])
            if CONTROL=='caller_clock_wrongboot':cl['boot_id']=OLD_BOOT
            else:
                cl['started_at']=RECOVERED_AT-1;cl['deadline_at']=cl['started_at']+600
            cr=put('SYNTHETIC-invalid-clock.json',cl);iv['contract']['resources']['clock']=cr;rc['future_clock']=cr
        elif CONTROL=='caller_recon_first_API_false':rc['first_user_API_never_started']=False
        elif CONTROL=='caller_recon_raw_changed':rc['raw_status']='PASS'
        elif CONTROL=='caller_old_clock_reuse':iv['contract']['resources']['clock']=yclock;rc['future_clock']=yclock
        elif CONTROL=='caller_new_clock_before_Y':
            w,m=time.time()-250,time.monotonic()-250
            early=dict(schema='frw.Root.F06.unstarted-consumer-finite-clock.v1',started_at=w,deadline_at=w+600,started_monotonic=m,deadline_monotonic=m+600,boot_id='SYNTHETIC-BOOT-ID')
            earlyref=put('SYNTHETIC-invalid-earlier-clock.json',early);iv['contract']['resources']['clock']=earlyref;rc['future_clock']=earlyref
        rc['current_contract_sha256']=sha(encoded(A.canonical_contract(iv['contract'])))
        iv['y_reconciliation']=put(Path(iv['y_reconciliation']['path']),rc)
        ivref=put(Path(argv[-2]),iv);argv[-1]=ivref['sha256']
    caller=synthetic_load(F.ref(own/'root_bind_existing_consumer_once.py'),'SYNTHETIC_FINAL_HANDOFF_CALLER')
    prior=sys.argv;sys.argv=argv[4:]
    try:caller.main()
    finally:sys.argv=prior
F.os.execv=fakeexec

def update_plan(key,ref):
    global planref
    plan[key]=ref;planref=put(Path(planref['path']),plan)
if CONTROL=='basis_unbound':plan['postboot_basis']='UNBOUND';planref=put(Path(planref['path']),plan)
elif CONTROL=='basis_missing':plan['postboot_basis']={k:v for k,v in BASIS.items() if k!='postboot_observation'};planref=put(Path(planref['path']),plan)
elif CONTROL=='basis_alias':
    basis_alias=dict(BASIS,postboot_observation=RECOVERY)
    component['postboot_basis']=basis_alias;componentref=put(F.J,component);plan['root_source_acceptance']=componentref
    frame.update(postboot_basis=basis_alias,component_acceptance=componentref);plan['frame_acceptance']=put(Path(frameref['path']),frame)
    plan['postboot_basis']=basis_alias;planref=put(Path(planref['path']),plan)
elif CONTROL=='current_unbound':plan['selected_admission']=None;planref=put(Path(planref['path']),plan)
elif CONTROL=='postboot_helper_source_drift':put(F.Y/'postboot_transition.py',(F.Y/'postboot_transition.py').read_bytes()+b'\n# drift\n',True)
elif CONTROL.startswith('source_drift_'):
    target=CONTROL.removeprefix('source_drift_');put(own/target,(own/target).read_bytes()+b'\n# SYNTHETIC DRIFT\n',True)
elif CONTROL=='helper_source_drift':put(F.Y/'y_custody_delta.py',(F.Y/'y_custody_delta.py').read_bytes()+b'\n# SYNTHETIC drift\n',True)
elif CONTROL=='frame_source_drift':put(Path(F.__file__),Path(F.__file__).read_bytes()+b'\n# SYNTHETIC drift\n',True)
elif CONTROL=='freeze_source_drift':put(own/'SOURCE-FREEZE.json',(own/'SOURCE-FREEZE.json').read_bytes()+b' ',True)
elif CONTROL=='bounded_reader_pin':
    component['bounded_reader_root_acceptance']=dict(reader,sha256='0'*64);update_plan('root_source_acceptance',put(F.J,component))
elif CONTROL=='bounded_reader_schema':
    rv=jsonread(reader);rv['ordinary_semantic_or_F06_acceptance']=True;reader=put(Path(reader['path']),rv);F.BOUNDED_READER_ACCEPTANCE=reader
    component['bounded_reader_root_acceptance']=reader;update_plan('root_source_acceptance',put(F.J,component))
elif CONTROL=='component_acceptance':
    component['runtime_authority']=True;update_plan('root_source_acceptance',put(F.J,component))
elif CONTROL=='frame_acceptance':
    frame['runtime_authority']=True;update_plan('frame_acceptance',put(Path(frameref['path']),frame))
elif CONTROL=='source_review':put(Path(review['path']),dict(jsonread(review),source_freeze_sha256='0'*64))
elif CONTROL=='root_plan_hash':planref['sha256']='0'*64
elif CONTROL=='Y_consumer_not_born':
    yclosed['BotAPI_client_constructed']=False;M.Y_PREINTENT_CLOSURE=put(Path(M.Y_PREINTENT_CLOSURE['path']),yclosed)
    judgment['y_preintent_closure']=M.Y_PREINTENT_CLOSURE;update_plan('y_judgment',put(Path(judgmentref['path']),judgment))
elif CONTROL=='Y_actual_API_recorded':
    yclosed['upload_model_reply_Office']=True;M.Y_PREINTENT_CLOSURE=put(Path(M.Y_PREINTENT_CLOSURE['path']),yclosed)
    judgment['y_preintent_closure']=M.Y_PREINTENT_CLOSURE;update_plan('y_judgment',put(Path(judgmentref['path']),judgment))
elif CONTROL=='Y_raw_UNKNOWN_changed':
    yassessment['raw_status']='PASS';M.Y_SAVED_ASSESSMENT=put(Path(M.Y_SAVED_ASSESSMENT['path']),yassessment)
    judgment['y_saved_assessment']=M.Y_SAVED_ASSESSMENT;update_plan('y_judgment',put(Path(judgmentref['path']),judgment))
elif CONTROL=='Y_source_hash_changed':put(Path(y_source_pins['f06_source.py']['path']),b'# SYNTHETIC changed old source\n',True)
elif CONTROL=='Y_undrained':put(M.Y_DIR/'work/ROOT-STOP-UNCONFIRMED.json',{'SYNTHETIC':'unreaped actor'})
elif CONTROL=='Y_unknown_api':
    judgment['no_unknown_API_effect_assumed_absent']=False;update_plan('y_judgment',put(Path(judgmentref['path']),judgment))
elif CONTROL=='Y_old_binding_changed':put(Path(ybinding['path']),dict(jsonread(ybinding),authority={}))
elif CONTROL=='custody_extra_record':
    actual['custody']['records'].append(['SYNTHETIC-extra.json',dict(actual['custody']['records'][0][1])]);actual['custody']['records'].sort(key=lambda r:tuple(r[0].split('/')));refresh(actual)
elif CONTROL=='custody_changed_record':actual['custody']['records'][0][1]['inode']+=1;refresh(actual)
elif CONTROL=='database_changed':actual['databases']['dest']['messages']+=1;refresh(actual)
elif CONTROL=='database_metadata_changed':actual['databases']['default']['message_metadata_sha256']='0'*64;refresh(actual)
elif CONTROL=='other_observation_changed':actual['services']['dashboard']['unit']['ActiveState']='inactive';refresh(actual)
elif CONTROL=='history_semantic_changed':
    history['native_boundary_sha256']='0'*64;c['root_proofs']['all_profile_history_semantic_once']=put(Path(c['root_proofs']['all_profile_history_semantic_once']['path']),history);update_plan('original_prepared_contract',put(Path(originalcontract['path']),c))
elif CONTROL=='private_root_intersection':
    privacy['effective_product_roots']=sorted([str(H),str(F.Y)]);c['root_proofs']['private_password_handling']=put(Path(c['root_proofs']['private_password_handling']['path']),privacy);update_plan('original_prepared_contract',put(Path(originalcontract['path']),c))
elif CONTROL=='lineage_changed':
    lineage['current_ingress_lineage_sha256']='0'*64;c['root_proofs']['source_ingress_lineage']=put(Path(c['root_proofs']['source_ingress_lineage']['path']),lineage);update_plan('original_prepared_contract',put(Path(originalcontract['path']),c))

EXPECTED={'current_history_drift': 'F06_CURRENT_ADMISSION_MUST_PRESERVE_EXACT_45_HISTORY_ROWS', 'current_unknown_replay': 'F06_CURRENT_ADMISSION_UNKNOWN_AND_NO_REPLAY_REQUIRED', 'current_policy_flag': 'F06_CURRENT_ADMISSION_HISTORICAL_POLICY_FLAGS_REQUIRED', 'current_encoding': 'F06_CURRENT_ADMISSION_ORIGINAL_ENCODING_REQUIRED', 'current_physical_tuple': 'F06_CURRENT_ADMISSION_SELECTED_PHYSICAL_TUPLE_REQUIRED', 'coherent_unselected_runtime': 'FRESH_OBSERVATION_NOT_EXACT_ROOT_ANCHOR', 'persistent_database': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'persistent_source': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'persistent_config': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'persistent_history': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'persistent_cursor': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'persistent_cipher': 'DELTA_EXACT_COMPUTED_CHANGE_SET', 'extra_STATE': 'RECORDED_CUSTODY_HASH_PAIR', 'native_pid': 'NATIVE_IDENTITY_BINDING', 'native_session': 'NATIVE_SESSION_BINDING', 'native_quiescent': 'NATIVE_READONLY_QUIESCENCE_GENERATION', 'service_inactive': 'SERVICE_RUNNING_PERMANENT_CONTROL', 'service_invocation_old': 'SERVICE_INVOCATION_NOT_NEW_BOOT', 'basis_unbound': 'ROOT_PLAN_UNBOUND', 'basis_missing': 'ROOT_PLAN_UNBOUND', 'basis_alias': 'F06_DISTINCT_POSTBOOT_BASIS_DOCUMENTS_REQUIRED', 'current_unbound': 'ROOT_EXACT_REFERENCE_REQUIRED', 'current_oldR106': 'F06_CURRENT_SELECTION_MUST_DIFFER_FROM_HISTORICAL_R106', 'current_expired': 'F06_EXISTING_AUTHORITY_EXPIRED_OR_TIMES_CHANGED', 'current_wrongscope': 'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT', 'current_wrongrun': 'F06_SINGLETON_ORDINARY_AUTHORITY_NO_MEMORY_GRANT', 'current_wrongparent': 'F06_ISSUED_SUPERSEDES_CHAIN_MISMATCH', 'current_wrongid': 'F06_CURRENT_SELECTED_AUTHORITY_ID_REQUIRED', 'selection_wrongscope': 'F06_CURRENT_SELECTION_ORIGINAL_SCOPE_AND_Y_REQUIRED', 'selection_wrongrun': 'F06_CURRENT_SELECTION_ORIGINAL_SCOPE_AND_Y_REQUIRED', 'selection_wrongsource': 'F06_CURRENT_SELECTION_ORIGINAL_SCOPE_AND_Y_REQUIRED', 'selection_wrongparent': 'F06_CURRENT_SELECTION_EXACT_AUTHORITY_CHAIN_REQUIRED', 'selection_wrongid': 'F06_CURRENT_SELECTION_EXACT_AUTHORITY_CHAIN_REQUIRED', 'selection_wrongboot': 'F06_CURRENT_SELECTION_BOOT_MISMATCH', 'selection_readiness_false': 'F06_CURRENT_OPERATION_DEPENDENCIES_NOT_ROOT_ACCEPTED', 'selection_readiness_hash': 'F06_PIN_CHANGED', 'selection_mixedbasis': 'F06_CURRENT_SELECTION_EXACT_POSTBOOT_RECOVERY_REQUIRED', 'selection_expired': 'F06_ROOT_CURRENT_SELECTION_STALE_OR_OUTSIDE_ADMISSION', 'caller_lineage_missing': 'F06_CURRENT_SELECTION_NOT_PINNED_IN_WHOLE_EFFECT_LINEAGE', 'caller_lineage_readiness': 'F06_CURRENT_SELECTION_NOT_PINNED_IN_WHOLE_EFFECT_LINEAGE', 'caller_clock_wrongboot': 'F06_CONSUMER_CLOCK_EXPIRED_OR_CHANGED', 'caller_clock_before_recovery': 'F06_FRESH_CLOCK_MUST_FOLLOW_ROOT_RECOVERY_AND_CURRENT_SELECTION', 'caller_recon_first_API_false': 'F06_ROOT_ACTUAL_Y_CLOSED_AND_FIRST_API_NEVER_STARTED_REQUIRED', 'caller_recon_raw_changed': 'F06_ROOT_MISSING_FIRST_API_RECONCILIATION_REQUIRED', 'source_drift_f06_source.py': 'ROOT_CODE_DRIFT', 'source_drift_root_bind_existing_consumer_once.py': 'ROOT_CODE_DRIFT', 'source_drift_current207.py': 'ROOT_CODE_DRIFT', 'source_drift_f06_footer.py.txt': 'ROOT_CODE_DRIFT', 'postboot_helper_source_drift': 'ROOT_POSTBOOT_DELTA_SOURCE_CHANGED', 'frame_source_drift': 'ROOT_FRAME_SOURCE_ACCEPTANCE_REQUIRED_BEFORE_IMPORT', 'component_acceptance': 'ROOT_ACTUAL_COMPONENT_SOURCE_ACCEPTANCE_REQUIRED', 'frame_acceptance': 'ROOT_FRAME_SOURCE_ACCEPTANCE_REQUIRED_BEFORE_IMPORT', 'final_bulk_review': 'ROOT_FINALIZER_AND_BULK_INDEPENDENT_REVIEW_REQUIRED', 'bulk_contract_drift': 'ROOT_BULK_CAS_CHANGED', 'current_changed': 'ROOT_MUTABLE_BASIS_CHANGED_BEFORE_CLOCK', 'old_clock_reuse': 'ROOT_STAGE_ALREADY_STARTED_OR_UNKNOWN_NO_RETRY', 'attempted_issuer_read': 'AUDIT_UNDECLARED_EXTERNAL_OPEN_DENIED', 'attempted_metadata': 'AUDIT_EXTERNAL_METADATA_DENIED', 'attempted_process': 'AUDIT_REAL_ACTOR_DENIED', 'attempted_network': 'AUDIT_NETWORK_DENIED', 'attempted_import': 'AUDIT_POST_PREWARM_IMPORT_DENIED'}
PREIMPORT={k for k in EXPECTED if k.startswith('source_drift_')}|{'helper_source_drift','frame_source_drift','freeze_source_drift','component_acceptance','frame_acceptance','source_review','root_plan_hash','bounded_reader_pin','bounded_reader_schema','postboot_helper_source_drift','basis_unbound','basis_missing'}
ATTACKS={k for k in EXPECTED if k.startswith('attempted_')}
caught=None;prepared=False;preexec_loads=None;before_signals={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}
try:
    if CONTROL in ATTACKS:
        if CONTROL=='attempted_issuer_read':os.open('/SYNTHETIC-UNDECLARED-ISSUER.json',os.O_RDONLY)
        elif CONTROL=='attempted_metadata':os.stat('/SYNTHETIC-UNDECLARED-METADATA')
        elif CONTROL=='attempted_process':REAL_POPEN(['/SYNTHETIC-NEVER-EXECUTED-PROCESS'])
        elif CONTROL=='attempted_network':socket.socket()
        elif CONTROL=='attempted_import':__import__('SYNTHETIC_UNDECLARED_IMPORT')
        elif CONTROL=='attempted_old_caller':fakeexec(M.PYTHON,[M.PYTHON,'-I','-B','-S',str(ysource['path'])])
    else:
        F.main(['--prepare',planref['path'],planref['sha256']]);prepared=True
        check(not (F.Y/'CONSUMER-CLOCK.json').exists() and not any((F.Y/'work').iterdir()),'prepare no clock/once/currentgrant/consumer')
        finalreview={'schema':'frw.Root.F06.Task31.finalizer-and-actual-bulk-review.v1','decision':'ACCEPT_ROOT_FINALIZER_NO_LIVE_GRANT','root_finalizer':F.ref(F.__file__),'root_bulk_decision':F.ref(F.Y/'ROOT-BULK-DECISION.json'),'root_source_acceptance':componentref,'open_critical_defects':[]}
        rr=put('final-review.json',finalreview)
        if CONTROL=='final_bulk_review':finalreview['root_finalizer']['sha256']='0'*64;rr=put(Path(rr['path']),finalreview)
        elif CONTROL=='bulk_contract_drift':put(F.Y/'CONTRACT.PREPARED-NO-CLOCK.json',{})
        elif CONTROL=='old_clock_reuse':put(F.Y/'CONSUMER-CLOCK.json',oldclockdata)
        preexec_loads=len(LOADS)
        F.main(['--execute-once',planref['path'],planref['sha256'],rr['path'],rr['sha256']])
except BaseException as e:caught=type(e).__name__+':'+str(e)
if CONTROL in POSITIVE:
    check(caught is None,'positive completes real frame/caller with returned FakeActor: '+str(caught))
    check(len(EXEC)==len(POPPEN)==len(FAKE_WAITS)==1 and len(JOURNAL)==1 and len(ADMISSION_CALLS)>0,'exact one caller/fakePopen/real wait_owned')
    inputs=jsonread(F.ref(F.Y/'ROOT-CONSUMER-INPUTS.json'));binding=jsonread(F.ref(F.Y/'work/ROOT-ACTUAL-BINDING.json'))
    check(A.successor(BASE.read_bytes(),binding['contract'],(own/'f06_footer.py.txt').read_bytes())==Path(binding['source']['path']).read_bytes(),'exact full source binding JSON reconstruction')
    check(A.canonical_contract(binding['contract'])==binding['contract'] and binding['contract']['root_current_proof']!=inputs['contract']['root_current_proof'],'canonical full contract and fresh nested reference reconstructed')
    check(inputs['contract']['run_id']==M.ORIGINAL_RUN and inputs['contract']['scenario_sha256']==M.ORIGINAL_SCENARIO_SHA,'original synthetic identity')
    newclock=jsonread(inputs['contract']['resources']['clock']);check(newclock['started_at']>max(jsonread(r)['deadline_at'] for r in (oldclock,xclock,yclock)),'genuinely new clock after all old finite clocks')
    check(all(F.ref(r['path'])==r for r in historical_cas),'all O/X/Y historical exact bytes preserved')
    derived=jsonread(F.ref(F.Y/'ROOT-Y-PROOF-DERIVATION.json'))
    check(set(k for k in derived['old_history'] if derived['old_history'][k]!=derived['new_history'][k])=={'once_sha256','ingress_lineage_sha256','retained_basis'},'history exact successor fields only')
    check(set(k for k in set(derived['old_lineage'])|set(derived['new_lineage']) if derived['old_lineage'].get(k)!=derived['new_lineage'].get(k))=={'current_ingress_lineage_sha256','retained_producer_oracle_basis','current_admission_selection','current_selected_admission','postboot_recovery_acceptance','postboot_basis','readiness_evidence'},'lineage exact successor fields only')
    check(binding['contract']['authority']==SELECTED and binding['contract']['authority_chain']['predecessor']==M.EXISTING_AUTHORITY,'new current Root admission exact historical parent')
    check(jsonread(SELECTED)['supersedes']['authority_id']==M.EXISTING_AUTHORITY_ID and jsonread(M.EXISTING_AUTHORITY)['expires_at']==PRODUCTION_AUTHORITY_TIMES['expires_at']<time.time(),'historical R106 expires immutable; separate current Root supersedes')
    check(newclock['boot_id']==BOOT and newclock['started_at']>=max(RECOVERED_AT,ROOT_SELECTION['created_at']),'new600 selected boot and after Root recovery+selection')
    ln=derived['new_lineage'];check(ln['postboot_basis']==BASIS and ln['readiness_evidence']==READINESS and ln['current_admission_selection']==SELECTION_REF,'exact selected basis/readiness retained in whole effect')
    ended=jsonread(F.ref(F.Y/'work/ROOT-DISPATCH-ENDED.json'))
    check(ended['actor_absent'] is True and ended['exit_code']==2 and ended['acceptance']=='NOT_ESTABLISHED' and ended['canonical_run'] is None,'real ended closure with fake PID only')
    q=os.open(M.SLOT,os.O_RDWR);fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB);os.close(q)
    check(all(signal.getsignal(n)==h for n,h in before_signals.items()),'signal handlers restored')
else:
    check(CONTROL in EXPECTED,'explicit finite known control')
    check(caught is not None and EXPECTED[CONTROL] in caught and not POPPEN,'negative exact refusal cause before fakePopen: '+str(caught))
    if CONTROL in PREIMPORT:check(not LOADS,'source/component/frame/review refuses PREIMPORT')
    if CONTROL=='final_bulk_review':check(len(LOADS)==preexec_loads,'actual bulk review refuses before execute imports')
    check(len(EXEC)==(1 if CONTROL.startswith('caller_') or CONTROL=='attempted_old_caller' else 0),'exact expected caller handoff count')
expected_denials=1 if CONTROL in ATTACKS-{'attempted_old_caller'} else 0
check(len(AUDIT['denied'])==expected_denials and AUDIT['real_subprocess']==(CONTROL=='attempted_process') and AUDIT['network']==(CONTROL=='attempted_network'),'owned audit exact expected confinement')
summary={'opens':len(AUDIT['opens']),'read_or_write_paths':sorted(set(AUDIT['opens'])),'metadata_operations':len(AUDIT['metadata']),'metadata_paths':sorted(set(p for _,p in AUDIT['metadata'])),'imports':AUDIT['imports'],'denied':AUDIT['denied'],'process_attempts_denied':AUDIT['real_subprocess'],'network_attempts_denied':AUDIT['network']}
put(CASE/'AUDIT-SUMMARY.json',summary)
usage=resource.getrusage(resource.RUSAGE_SELF)
put(CASE/'RESOURCES.json',dict(pid=os.getpid(),user_cpu_seconds=usage.ru_utime,system_cpu_seconds=usage.ru_stime,peak_rss_kib=usage.ru_maxrss,minor_page_faults=usage.ru_minflt,major_page_faults=usage.ru_majflt,affinity=sorted(os.sched_getaffinity(0)),cpu_limit=resource.getrlimit(resource.RLIMIT_CPU),as_limit=resource.getrlimit(resource.RLIMIT_AS),per_file_limit=resource.getrlimit(resource.RLIMIT_FSIZE),real_child_born=False,fake_actor_reaped_by_real_wait_owned=len(FAKE_WAITS)==1))
result={'control':CONTROL,'passed':True,'caught':caught,'expected_refusal':EXPECTED.get(CONTROL),'prepared':prepared,'dependency_loads':LOADS,'exec_sentinels':len(EXEC),'Popen_sentinels':len(POPPEN),'real_wait_owned_on_fake_actor':len(FAKE_WAITS),'journal_metadata_synthetic':len(JOURNAL),'real_delta_calls':len(DELTA_CALLS),'selected_boot':BOOT,'root_metadata_variant':VARIANT,'real_adapter_admission_calls':len(ADMISSION_CALLS),'synthetic_pin_seams':PIN_SEAMS,'whole_binding_JSON_successor_checked':CONTROL in POSITIVE,'O_X_Y_historical_CAS_checked':CONTROL in POSITIVE,'derived_semantic_lineage_exact_fields_checked':CONTROL in POSITIVE,'production_source_inert_AST_and_exact_pins_verified':INERT_VERIFIED,'audit_denied':AUDIT['denied'],'real_process_or_network':0,'production_R106_times_metadata_only':PRODUCTION_AUTHORITY_TIMES if CONTROL=='root_authority_expired' else None,'declared_synthetic':'all host/current/authority/scenario/closure/custody pins are ownfixture synthetic; unchanged Root frame and full caller/adapter/current semantic/private functions run; no actual current/private truth or live result'}
put(CASE/'RESULT.json',result);print(json.dumps(result))
