"""Source-only synthetic authority. Actual whole selected helpers/functions execute.
Native role/credential authority is a declared no-effect seam, never native PASS.
"""
import contextlib,copy,hashlib,importlib.machinery,importlib.util,json,os,resource,shutil,signal,sys,tempfile,time,types
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent;started=time.monotonic();checks=[]
sys.path.insert(0,str(W))
import argparse,uuid
parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
parser.add_argument('--repo-root',type=Path,required=True,help='Repository root containing plugins/ and tools/')
parser.add_argument('--helpers-root',type=Path,help='Root containing scripts/friday_{ordinary_,}install.py; defaults to repo root')
parser.add_argument('--native-dir',type=Path,required=True,help='Declared native dependency source directory; never executed as a process')
parser.add_argument('--native-overlay',type=Path,help='Optional native receipt-pinned whole-module overlay with hermes_cli/')
parser.add_argument('--native-receipt',type=Path,required=True,help='Receipt authenticating native source files imported by this test')
parser.add_argument('--native-receipt-sha256',required=True,help='Caller-pinned SHA256 of native receipt')
parser.add_argument('--run-root',type=Path,default=W/'runs')
parser.add_argument('--second-layer-root',type=Path,help='Enable second edge with exact patch/manifest from this root')
parser.add_argument('--publisher',type=Path,help='Actual publication module; required for second edge')
parser.add_argument('--reuse-fourth-negatives',action='store_true',help='Reuse original unchanged fourth-edge tamper matrix; execute actual fourth positive setup')
parser.add_argument('--reuse-r1-negatives',action='store_true',help='Skip already-verified R1 tamper matrix while preserving writer positives')
parser.add_argument('--publisher-rollback',action='store_true',help='Inject final default inspect failure; verify actual publisher rollback')
parser.add_argument('--second-native-before',type=Path,required=True,help='Exact retained CP200 beforeimage directory; fixture data only')
parser.add_argument('--third-helpers-root',type=Path,required=True)
parser.add_argument('--third-layer-root',type=Path,required=True)
parser.add_argument('--third-native-after',type=Path,required=True)
parser.add_argument('--third-rollback',action='store_true')
parser.add_argument('--fourth-helpers-root',type=Path,required=True)
parser.add_argument('--fourth-layer-root',type=Path,required=True)
parser.add_argument('--fourth-native-before',type=Path,required=True)
parser.add_argument('--fourth-native-after',type=Path,required=True)
parser.add_argument('--fourth-native-spec',type=Path,required=True)
parser.add_argument('--fourth-rollback',action='store_true')
parser.add_argument('--fifth-helpers-root',type=Path,required=True)
parser.add_argument('--fifth-layer-root',type=Path,required=True)
parser.add_argument('--fifth-native-before',type=Path,required=True,help='Retained source202 beforeimages; both fifth-only old targets are seeded here')
parser.add_argument('--fifth-native-after',type=Path,required=True)
parser.add_argument('--fifth-native-spec',type=Path,required=True)
parser.add_argument('--fifth-rollback',action='store_true')
parser.add_argument('--sixth-helpers-root',type=Path,required=True)
parser.add_argument('--sixth-layer-root',type=Path,required=True)
parser.add_argument('--sixth-native-before',type=Path,required=True)
parser.add_argument('--sixth-native-after',type=Path,required=True)
parser.add_argument('--sixth-native-spec',type=Path,required=True)
parser.add_argument('--sixth-rollback',action='store_true')
parser.add_argument('--reuse-fifth-negatives',action='store_true')
parser.add_argument('--seventh-helpers-root',type=Path,required=True)
parser.add_argument('--seventh-layer-root',type=Path,required=True)
parser.add_argument('--seventh-native-before',type=Path,required=True)
parser.add_argument('--seventh-native-after',type=Path,required=True)
parser.add_argument('--seventh-native-spec',type=Path,required=True)
parser.add_argument('--seventh-rollback',action='store_true')
parser.add_argument('--reuse-sixth-negatives',action='store_true')
parser.add_argument('--reuse-seventh-negatives',action='store_true')
parser.add_argument('--eighth-helpers-root',type=Path,required=True)
parser.add_argument('--eighth-layer-root',type=Path,required=True)
parser.add_argument('--eighth-native-before',type=Path,required=True)
parser.add_argument('--eighth-native-after',type=Path,required=True)
parser.add_argument('--eighth-native-spec',type=Path,required=True)
parser.add_argument('--eighth-rollback',action='store_true')
parser.add_argument('--reuse-eighth-negatives',action='store_true')
parser.add_argument('--ninth-helpers-root',type=Path,required=True)
parser.add_argument('--ninth-layer-root',type=Path,required=True)
parser.add_argument('--ninth-native-before',type=Path,required=True)
parser.add_argument('--ninth-native-after',type=Path,required=True)
parser.add_argument('--ninth-native-spec',type=Path,required=True)
parser.add_argument('--ninth-rollback',action='store_true')
parser.add_argument('--reuse-ninth-negatives',action='store_true')
parser.add_argument('--tenth-helpers-root',type=Path,required=True)
parser.add_argument('--tenth-layer-root',type=Path,required=True)
parser.add_argument('--tenth-native-before',type=Path,required=True)
parser.add_argument('--tenth-native-after',type=Path,required=True)
parser.add_argument('--tenth-native-spec',type=Path,required=True)
parser.add_argument('--tenth-rollback',action='store_true')
parser.add_argument('--reuse-tenth-negatives',action='store_true')
parser.add_argument('--cpu-seconds',type=int,default=420)
parser.add_argument('--wall-seconds',type=int,default=600)
parser.add_argument('--second-native-after',type=Path,help='Exact two ODS native afterimage files; required with second layer')
parser.add_argument('--mode',choices=('current','pre-r1'),default='current')
args=parser.parse_args()
# Root's new finite source-check assignment authorizes this copied bounded harness.
# Historical consumed recipe/approval is not repurposed as fresh authority.
sys.path.insert(0,str(W.parent))
from gate_common import require,literal
if not 1<=args.cpu_seconds<=600:parser.error('--cpu-seconds must be 1..600')
if not 1<=args.wall_seconds<=900:parser.error('--wall-seconds must be 1..900')
resource.setrlimit(resource.RLIMIT_CPU,(args.cpu_seconds,args.cpu_seconds))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
def wall_limit(signum,frame):raise TimeoutError('synthetic_whole_gate_wall_budget_exhausted')
signal.signal(signal.SIGALRM,wall_limit)
remaining=min(args.wall_seconds,float(os.environ['FRW_F06_DEADLINE_MONOTONIC'])-time.monotonic())
require(remaining>0,'whole gate wall budget already exhausted')
signal.setitimer(signal.ITIMER_REAL,remaining)
if args.ninth_rollback or args.eighth_rollback or args.seventh_rollback or args.sixth_rollback or args.fifth_rollback or args.fourth_rollback or args.third_rollback or args.publisher_rollback:parser.error('eighth preparation requires successful ancestral edges; select --ninth-rollback')
if bool(args.second_layer_root)!=bool(args.second_native_after):parser.error('--second-native-after and --second-layer-root must be paired')
if args.second_layer_root and not args.publisher:parser.error('--publisher required for second edge')
if args.publisher_rollback and not args.second_layer_root:parser.error('--publisher-rollback requires second edge')
if args.second_layer_root and args.mode=='pre-r1':parser.error('pre-r1 mode covers first edge only')
REPO=args.repo_root.resolve(strict=True)
HELPERS=(args.helpers_root or REPO).resolve(strict=True)
MODE='baseline' if args.mode=='pre-r1' else 'current'
args.run_root.mkdir(mode=0o700,parents=True,exist_ok=True)
REPORT_DIR=args.run_root/('r1-'+args.mode+'-'+uuid.uuid4().hex)
REPORT_DIR.mkdir(mode=0o700,exist_ok=False)

from source_guard import install_guard
install_guard(W.parent, args.run_root.resolve())

def enc(d):return (json.dumps(d,sort_keys=True,indent=2)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,mode=0o700,exist_ok=True);p.write_bytes(b if type(b) is bytes else enc(b));p.chmod(0o600)
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def mod(n,path=None):
 m=types.ModuleType(n);sys.modules[n]=m
 if path is not None:m.__path__=[str(path)];m.__spec__=importlib.machinery.ModuleSpec(n,loader=None,is_package=True)
 return m
def check(n,result,detail=None):
 checks.append({'name':n,'pass':bool(result),**({'detail':detail} if detail else {})})
 if not result:raise AssertionError(n+': '+str(detail))
 print('PASS '+n,flush=True)
def failure_report(kind,error,tb):
 import traceback
 failure={'state':'FAIL','checks':checks,'exception_class':kind.__name__,'exception':str(error),
  'invocation':sys.argv,'python':sys.executable,'seconds':time.monotonic()-started}
 with (REPORT_DIR/'FAILURE.json').open('xb') as stream:stream.write(enc(failure))
 traceback.print_exception(kind,error,tb)
sys.excepthook=failure_report
def refused(n,fn):
 try:fn()
 except (ValueError,OSError,KeyError,TypeError) as e:check(n,True,type(e).__name__+':'+str(e));return
 check(n,False,'accepted')
with tempfile.TemporaryDirectory(prefix='synthetic-authority-',dir=REPORT_DIR) as td:
 T=Path(td);P=T/'project';H=T/'home';N=H/'hermes-agent'
 for name in ('friday_install.py','friday_ordinary_install.py'):
  data=(HELPERS/'scripts'/name).read_bytes()
  write(P/'scripts'/name,data)
  write(REPORT_DIR/'source-snapshot/scripts'/name,data)
 write(REPORT_DIR/'INPUTS.json',{'helpers':{name:ref(HELPERS/'scripts'/name) for name in ('friday_install.py','friday_ordinary_install.py')},
  'invocation':sys.argv,'python':sys.executable,'authority':'EXPLICIT_SYNTHETIC_SOURCE_ONLY'})
 primitive=REPO/'plugins/friday_rework/runtime_primitives.py'
 write(P/'plugins/friday_rework/runtime_primitives.py',primitive.read_bytes());write(P/'plugins/friday_rework/__init__.py',b'')
 mod('scripts',P/'scripts');F=load(P/'scripts/friday_install.py','scripts.friday_install');O=load(P/'scripts/friday_ordinary_install.py','scripts.friday_ordinary_install')
 if MODE=='baseline':
  # Exactly the old whole function, isolated in memory; source candidate stays
  # untouched. All collaborators and authority checks retain current bytes.
  baseline=W/'pre_r1_function.py'
  expected='8258f32765026ff7999b9954d68d6a27b9c62081007c734b54cb466af69bf3ac'
  assert sha(baseline.read_bytes())==expected
  exec(compile(baseline.read_bytes(),str(baseline),'exec'),O.__dict__)

 from native_fixture import NativeFixture
 native=NativeFixture(H,N,F,O,write,ref,repo=REPO,native=args.native_dir,overlay=args.native_overlay,receipt=args.native_receipt,receipt_sha256=args.native_receipt_sha256);gw=native.gw;scope=native.users;calls=[]
 F.native_packages=lambda source:None
 for n in O.PROJECT_DSH_CURRENT_REQUIRED|O.PROJECT_DSH_CURRENT_OPTIONAL|{O.PROJECT_DSH_CURRENT_ADDITION}:write(P/n,('new '+n+'\n').encode())
 plugin_names={str(p.relative_to(P)) for p in (P/'plugins/friday_rework').rglob('*') if p.is_file()}
 for i in range(52-len(plugin_names)):write(P/f'plugins/friday_rework/fixture{i}.py',b'# synthetic plugin\n')
 write(P/'scripts/friday_native.py',b'# selected dispatcher synthetic source\n')
 layers=[]
 for i in range(198):
  patch=f'patches/hermes/fixture-{i}.patch';manifest=f'patches/hermes/fixture-{i}-manifest.json'
  write(P/patch,b'# synthetic patch\n');write(P/manifest,{'patch':patch,'patch_sha256':ref(P/patch)['sha256']})
  layers.append({'manifest':manifest,'manifest_sha256':ref(P/manifest)['sha256'],'patch_sha256':ref(P/patch)['sha256']})
 inventory=lambda:{str(p.relative_to(P)):sha(p.read_bytes()) for p in P.rglob('*') if p.is_file()}
 for i in range(477-len(inventory())):write(P/f'fixtures/project-{i}.txt',b'fixture\n')
 current_files=inventory();check('synthetic_project_count',len(current_files)==477)
 basefiles=dict(current_files);basefiles.pop(O.PROJECT_DSH_CURRENT_ADDITION)
 oldbytes={}
 for n in O.PROJECT_DSH_CURRENT_REQUIRED|O.PROJECT_DSH_CURRENT_OPTIONAL|O.PROJECT_DSH_CURRENT_HELPERS:
  oldbytes[n]=('old '+n+'\n').encode();basefiles[n]=sha(oldbytes[n])
 # Root477 deliberately pins DIFFERENT historical helper bytes. The new leaf
 # delivers its actual new helpers; validating ancestral helper origins would fail.
 rootfiles=dict(current_files)
 for n in O.PROJECT_DSH_CURRENT_HELPERS:rootfiles[n]=sha(('historical root '+n).encode())
 nativefiles={}
 fourth_spec=json.loads(args.fourth_native_spec.read_bytes())
 fourth_old=sorted(r['path'] for r in fourth_spec['native_files'] if not r['new_file'])
 assert len(fourth_old)==8
 fifth_spec=json.loads(args.fifth_native_spec.read_bytes())
 fifth_rows=fifth_spec['native_files']
 fifth_only=sorted(r['path'] for r in fifth_rows if not r['new_file'] and r['path'] not in fourth_old)
 assert fifth_only==['agent/context_compressor.py','hermes_cli/friday_workspace_presentation_text.py'],fifth_only
 seventh_spec=json.loads(args.seventh_native_spec.read_bytes())
 seventh_rows=seventh_spec['native_files']
 sixth_spec=json.loads(args.sixth_native_spec.read_bytes())
 third_targets=literal(args.sixth_helpers_root/'scripts/friday_ordinary_install.py','CURRENT_SOURCE_THIRD_NATIVE')
 earlier_targets=set(r['path'] for r in fourth_spec['native_files'])|set(r['path'] for r in fifth_rows)|set(O.CURRENT_SOURCE_SECOND_NATIVE)|set(third_targets)|set(r['path'] for r in sixth_spec['native_files'])
 # Seed only declared seventh preimages genuinely absent from all previous deltas.
 seventh_only=sorted(r['path'] for r in seventh_rows if not r['new_file'] and r['path'] not in earlier_targets)
 eighth_spec=json.loads(args.eighth_native_spec.read_bytes())
 eighth_rows=eighth_spec['native_files']
 assert len(eighth_rows)==11 and all(r['new_file'] is False for r in eighth_rows)
 # Eighth-only preimages occupy a separate range; adding eighth targets must
 # never alter the previous selection or overwrite an ancestral preimage.
 eighth_only=sorted(r['path'] for r in eighth_rows if r['path'] not in earlier_targets|set(r['path'] for r in seventh_rows))
 assert len(seventh_only)+len(eighth_only)<=17876,'declared source set exceeds available fixture seed slots'
 assert not set(eighth_only)&set(seventh_only)

 for i in range(17888):
  n=f'fixture/{i}.txt';data=('native0\n').encode() if i==0 else b''
  if args.second_layer_root and i>=17886:
   n=sorted(O.CURRENT_SOURCE_SECOND_NATIVE)[i-17886]
   data=(args.second_native_before/n).read_bytes()
   assert sha(data)==O.CURRENT_SOURCE_SECOND_NATIVE[n][0],n
  if 17876-len(seventh_only)-len(eighth_only)<=i<17876-len(seventh_only):
   n=eighth_only[i-(17876-len(seventh_only)-len(eighth_only))];data=(args.eighth_native_before/n).read_bytes()
   assert sha(data)==next(r['before_sha256'] for r in eighth_rows if r['path']==n)
  if 17876-len(seventh_only)<=i<17876:
   n=seventh_only[i-(17876-len(seventh_only))];data=(args.seventh_native_before/n).read_bytes()
   assert sha(data)==next(r['before_sha256'] for r in seventh_rows if r['path']==n)
  if 17878-len(fifth_only)<=i<17878:
   n=fifth_only[i-(17878-len(fifth_only))];data=(args.fifth_native_before/n).read_bytes()
   assert sha(data)==next(r['before_sha256'] for r in fifth_rows if r['path']==n)
  if 17878<=i<17886:
   n=fourth_old[i-17878];data=(args.fourth_native_before/n).read_bytes()
   assert sha(data)==next(r['before_sha256'] for r in fourth_spec['native_files'] if r['path']==n)
  if i in (17840,17841):
   tenth_rows=json.loads(args.tenth_native_spec.read_bytes())['native_files']
   tenth_row=tenth_rows[i-17840];n=tenth_row['path'];data=(args.tenth_native_before/n).read_bytes()
   assert sha(data)==tenth_row['before_sha256']
  assert n not in nativefiles,('duplicate_native_seed',n)
  write(N/n,data);nativefiles[n]={'sha256':sha(data),'bytes':len(data),'mode':'100644'}
 donor={'id':'hermes','commit':'syntheticcommit','tree':'synthetictree'}
 if args.second_layer_root:
  sm=args.second_layer_root/('patches/hermes/'+O.CURRENT_SOURCE_SECOND_LAYER+'-manifest.json')
  if not sm.exists():sm=args.second_layer_root/sm.name
  donor['commit']=json.loads(sm.read_bytes())['base_commit']
 lock=T/'lock.json';write(lock,{'repositories':[donor,{'id':'dsh'},{'id':'a0'}]})
 receipt={'schema':'friday.hermes-source.v1','status':'SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED','commit':donor['commit'],'base_tree':donor['tree'],'source_file_count':17730,'sources_lock_sha256':ref(lock)['sha256'],'layers':layers,'files':nativefiles}
 write(H/'hermes-agent.source.json',receipt);O.PROJECT_DSH_CURRENT_RECEIPT=ref(H/'hermes-agent.source.json')['sha256']
 stamp={'commit':receipt['commit'],'dirty':True,'fridaySource':{'baseTree':receipt['base_tree'],'layers':layers}}
 write(N/'install-stamp.json',stamp);O.PROJECT_DSH_CURRENT_STAMP=ref(N/'install-stamp.json')['sha256']
 base={'home':str(H),'containment':{},'bootstrap_python':{'path':'synthetic-not-executed'},'product':{'runtime':{'enabled':False},'dashboard':{}},'sources_lock':ref(lock),'project_files':basefiles,'worker_install':{'missing-historical':True},'hermes_prepare':{'path':str(T/'absent-installer'),'sha256':'a'*64}}
 bp=T/'base476.json';write(bp,base);O.PROJECT_DSH_CURRENT_INPUT=ref(bp)['sha256'];O.PROJECT_DSH_CURRENT_INVENTORY=sha(enc(basefiles))
 rootvalue=copy.deepcopy(base);rootvalue['project_files']=rootfiles;rp=T/'root477.json';write(rp,rootvalue)
 native.files()
 beforebase={'schema':F.SCHEMA,'home':str(H),'source':str(N),'state':'INSTALLED_TEMPLATE_INCOMPLETE','completion_stage':'TELEGRAM_ORDINARY','runtime_ready':False,'worker_state':'BOTH_WORKERS_PREPARATION_PENDING','input_sha256':ref(bp)['sha256'],'source_receipt_sha256':O.PROJECT_DSH_CURRENT_RECEIPT,'plugin_files':{n:h for n,h in basefiles.items() if n.startswith('plugins/friday_rework/')},'ordinary_gateway':{'source_receipt_sha256':O.PROJECT_DSH_CURRENT_RECEIPT,'operator_entry':{'input':ref(bp),'script':{'path':str(P/'scripts/friday_native.py'),'sha256':basefiles['scripts/friday_native.py']}}},'profile_files':{n:ref(H/n)['sha256'] for n in ('config.yaml','SOUL.md','FRIDAY-PROFILE.json')}}
 native.marker(beforebase)
 oldoperator=T/'previous-project/scripts/friday_native.py';write(oldoperator,(P/'scripts/friday_native.py').read_bytes())
 rootmarker=copy.deepcopy(beforebase);rootmarker['input_sha256']=ref(rp)['sha256'];rootmarker['plugin_files']={n:h for n,h in rootfiles.items() if n.startswith('plugins/friday_rework/')};rootmarker['ordinary_gateway']['operator_entry']['input']=ref(rp);rootmarker['ordinary_gateway']['operator_entry']['script']['path']=str(oldoperator)
 write(H/F.MARKER,rootmarker)
 for name in rootmarker['plugin_files']:write(H/name,(P/name).read_bytes())
 write(H/'preparation/ordinary-gateway/committed.json',{'state':'SOURCE_ACTIVATED_NOT_RUNTIME_ACCEPTED'});(H/'preparation/ordinary-gateway-archive').mkdir(mode=0o700)
 hist=lambda roots:{str(p.relative_to(H)):sha(p.read_bytes()) for r in roots for p in (H/r).rglob('*') if p.is_file()}
 eng={'schema':'frw.root.engineering152-successor-request.v1','home':str(H),'previous_input':ref(bp),'current_input':ref(bp)}
 etmp=T/'eng.json';write(etmp,eng);er=ref(etmp);etx=H/'preparation'/('ordinary-source-update-successor-'+er['sha256']);write(etx/'request.json',eng);er=ref(etx/'request.json')
 beforebase['ordinary_source_update_request']=er;rootmarker['ordinary_source_update_request']=er;write(H/F.MARKER,rootmarker)
 write(etx/'committed.json',{'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED','previous_input':eng['previous_input'],'current_input':eng['current_input'],'source_receipt_sha256':'d'*64,'gateway_started':False,'workers_enabled':False})
 receipt197=copy.deepcopy(receipt);receipt197['layers']=layers[:-1];marker197={'input_sha256':ref(bp)['sha256'],'source_receipt_sha256':sha(enc(receipt197))};stamp197={'commit':receipt['commit'],'dirty':True,'fridaySource':{'baseTree':receipt['base_tree'],'layers':layers[:-1]}}
 old={'schema':'friday.ordinary-telegram-source-update.v46','candidate_project':str(P),'home':str(H),'previous_input':ref(bp),'current_input':ref(bp),'project_inventory_sha256':O.PROJECT_DSH_CURRENT_INVENTORY,'source_receipt':{'path':str(H/'hermes-agent.source.json'),'sha256':sha(enc(receipt197))},'marker':{'path':str(H/F.MARKER),'sha256':sha(enc(marker197))},'stamp':{'path':str(N/'install-stamp.json'),'sha256':sha(enc(stamp197))},'predecessor_request':er,'predecessor_current_input_sha256':eng['current_input']['sha256'],'predecessor_receipt_sha256':'d'*64,'transaction_history':hist((O.TRANSACTION,'preparation/ordinary-gateway-archive'))}
 op=T/'oldcp.json';write(op,old);orr=ref(op);otx=H/'preparation'/('ordinary-source-update-v45-'+orr['sha256'][:16])
 write(otx/'before/hermes-agent.source.json',receipt197);write(otx/'before/FRIDAY-INSTALL.json',marker197);write(otx/'before/hermes-agent/install-stamp.json',stamp197);write(otx/'hermes-agent.source.json',receipt);write(otx/'install-stamp.json',stamp)
 oi={'schema':'friday.ordinary-telegram-source-update-transaction.v1','state':'SOURCE_UPDATE_INTENT','request_sha256':orr['sha256'],'previous_input':old['previous_input'],'current_input':old['current_input'],'source_receipt':old['source_receipt'],'gateway_started':False,'workers_enabled':False};oc={**oi,'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED','source_receipt_sha256':O.PROJECT_DSH_CURRENT_RECEIPT};write(otx/'intent.json',oi);write(otx/'committed.json',oc)
 anc={'request':orr,'intent':ref(otx/'intent.json'),'committed':ref(otx/'committed.json')};O.PROJECT_DSH_CURRENT_ANCESTOR={n:r['sha256'] for n,r in anc.items()}
 delta={'schema':O.PROJECT_DSH_CURRENT_DELTA_SCHEMA,'previous_input_sha256':O.PROJECT_DSH_CURRENT_INPUT,'previous_project_files_sha256':O.PROJECT_DSH_CURRENT_INVENTORY,'source_receipt_sha256':O.PROJECT_DSH_CURRENT_RECEIPT,'native_layers':198,'native_files':17888,'project_file_updates':[{'path':n,'before_sha256':basefiles.get(n),'after_sha256':h} for n,h in sorted(rootfiles.items()) if basefiles.get(n)!=h]};dp=T/'delta.json';write(dp,delta)
 br=T/'base-marker.json';write(br,beforebase)
 reqroot={'schema':O.PROJECT_DSH_CURRENT_SCHEMA,'seconds':600,'home':str(H),'previous_input':ref(bp),'current_input':ref(rp),'marker':{'path':str(H/F.MARKER),'sha256':ref(br)['sha256']},'source_receipt':ref(H/'hermes-agent.source.json'),'stamp':ref(N/'install-stamp.json'),'credential_files':{'.env':None,'auth.json':None},'transaction_history':hist((O.TRANSACTION,'preparation/ordinary-gateway-archive',str(etx.relative_to(H)),str(otx.relative_to(H)))),'predecessor_update':orr,'publication_ancestor':anc,'reviewed_delta':ref(dp)}
 for k in ('configuration','profile','launcher','native_unit'):
  fp=H/{'configuration':'config.yaml','profile':'FRIDAY-PROFILE.json','launcher':'hermes-agent/.hermes/bin/hermes'}.get(k,'native-unit.txt');write(fp,fp.read_bytes() if fp.exists() else b'synthetic current pin\n');reqroot[k]=ref(fp)
 rreq=T/'v6.json';write(rreq,reqroot);rr=ref(rreq);rtx=H/'preparation'/('ordinary-source-update-'+O.PROJECT_DSH_CURRENT_INPUT)
 before={F.MARKER:{'sha256':ref(br)['sha256'],'mode':0o600}}
 write(rtx/'before'/F.MARKER,beforebase)
 for n in rootfiles:
  if n.startswith('plugins/friday_rework/') and rootfiles[n]!=basefiles.get(n):
   before[n]=None if n not in basefiles else {'sha256':basefiles[n],'mode':0o600}
   if n in basefiles:write(rtx/'before'/n,oldbytes[n])
 ri={'schema':'friday.ordinary-telegram-source-update-transaction.v1','state':'SOURCE_UPDATE_CONSUMED_NO_RETRY','project_only':True,'native_source_unchanged':True,'request_reference':rr,'request_sha256':rr['sha256'],'seconds':600,'previous_input':ref(bp),'current_input':ref(rp),'publication_ancestor':anc,'reviewed_delta':ref(dp),'gateway_started':False,'workers_enabled':False,'before':before}
 rc={'schema':ri['schema'],'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED','project_only':True,'native_source_unchanged':True,'request_reference':rr,'request_sha256':rr['sha256'],'previous_input':ref(bp),'current_input':ref(rp),'source_receipt_sha256':O.PROJECT_DSH_CURRENT_RECEIPT,'gateway_started':False,'workers_enabled':False};write(rtx/'intent.json',ri);write(rtx/'committed.json',rc)
 check('root_metadata_authenticates_without_ancestral_helper_origin',O._project_current_root_checked(H,rr)[1]==rootvalue)
 newname='genuine-synthetic-after-source198';patch='patches/hermes/'+newname+'.patch';mn='patches/hermes/'+newname+'-manifest.json';newdata=b'native successor changed\n'
 write(P/patch,b'synthetic actual patch bytes\n');manifest={'patch':patch,'patch_sha256':ref(P/patch)['sha256'],'base_commit':receipt['commit'],'files':[{'path':'fixture/0.txt','before_sha256':nativefiles['fixture/0.txt']['sha256'],'sha256':sha(newdata),'bytes':len(newdata),'mode':'100644','new_file':False}]};write(P/mn,manifest)
 leaf=copy.deepcopy(rootvalue);leaf['project_files']=inventory();lp=T/'leaf479.json';write(lp,leaf)
 q={'schema':'friday.ordinary-telegram-source-update.v46','seconds':600,'home':str(H),'previous_input':ref(rp),'current_input':ref(lp),'candidate_input':ref(lp),'candidate_project':str(P),'marker':ref(H/F.MARKER),'source_receipt':ref(H/'hermes-agent.source.json'),'target_receipt':ref(H/'hermes-agent.source.json'),'stamp':ref(N/'install-stamp.json'),'transaction_history':old['transaction_history'],'predecessor_request':er,'predecessor_current_input_sha256':old['predecessor_current_input_sha256'],'predecessor_receipt_sha256':old['predecessor_receipt_sha256'],'installed_layers':198,'installed_files':17888,'project_inventory':leaf['project_files'],'project_inventory_sha256':sha(enc(leaf['project_files'])),'layer_names':[newname],'layer_manifest_updates':[mn],'project_file_updates':sorted(O.PROJECT_DSH_CURRENT_HELPERS),'plugin_set':[],'plugin_additions':[],'staged_files':[],'current_source_successor':{'schema':O.CURRENT_SOURCE_SUCCESSOR_SCHEMA,'root_project_update':rr},**{k:reqroot[k] for k in ('configuration','profile','launcher','native_unit')}}
 check('request_fieldset',set(q)==O.CURRENT_SOURCE_CP_FIELDS)
 check('actual_spec_prepublication_prospective',F.spec_checked(leaf,cli_only=True,source_update=q)[0]==H)
 (P/mn).chmod(0o644);check('pinned_public_manifest_mode644_supported',F.spec_checked(leaf,cli_only=True,source_update=q)[0]==H);(P/mn).chmod(0o600)
 # Store original request with intentionally noncanonical whitespace. The RAW
 # SHA, not a re-encoded semantic SHA, determines the canonical transaction.
 raw=json.dumps(q,sort_keys=False,separators=(',',':')).encode()+b'\n';qs=sha(raw);tx=H/'preparation'/('ordinary-source-update-v45-'+qs[:16]);write(tx/'request.json',raw);qr=ref(tx/'request.json')
 qi={'schema':'friday.ordinary-telegram-source-update-transaction.v1','state':'SOURCE_UPDATE_INTENT','request_sha256':qs,'request_reference':qr,'current_source_successor':q['current_source_successor'],'home':str(H),'previous_input':q['previous_input'],'current_input':q['current_input'],'source_receipt':q['source_receipt'],'layers':[mn],'files':['fixture/0.txt'],'plugin_set':[],'plugin_additions':[],'project_file_updates':q['project_file_updates'],'metadata':['hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json'],'gateway_started':False,'workers_enabled':False}
 write(tx/'intent.json',qi)
 for name in ('hermes-agent.source.json',F.MARKER,'hermes-agent/install-stamp.json'):write(tx/'before'/name,(H/name).read_bytes())
 check('prepublication_existing_intent_raw_proof',F.spec_checked(leaf,cli_only=True,source_update=q)[0]==H)
 after=copy.deepcopy(receipt);after['layers'].append({'manifest':mn,'manifest_sha256':leaf['project_files'][mn],'patch_sha256':leaf['project_files'][patch]});after['files']['fixture/0.txt'].update(sha256=sha(newdata),bytes=len(newdata));write(N/'fixture/0.txt',newdata);write(H/'hermes-agent.source.json',after)
 aftersha=ref(H/'hermes-agent.source.json')['sha256'];am=copy.deepcopy(rootmarker);am['input_sha256']=ref(lp)['sha256'];am['source_receipt_sha256']=aftersha;am['ordinary_gateway']['source_receipt_sha256']=aftersha;am['ordinary_gateway']['operator_entry']={'input':ref(lp),'script':{'path':str(P/'scripts/friday_native.py'),'sha256':leaf['project_files']['scripts/friday_native.py']}};write(H/F.MARKER,am)
 astamp=copy.deepcopy(stamp);astamp['fridaySource']['layers']=after['layers'];write(N/'install-stamp.json',astamp)
 for src,dst in [('hermes-agent.source.json','hermes-agent.source.json'),(F.MARKER,F.MARKER),('hermes-agent/install-stamp.json','install-stamp.json')]:write(tx/dst,(H/src).read_bytes())
 check('actual_spec_postpublication_explicit_before_commit',F.spec_checked(leaf,cli_only=True,source_update=q)[0]==H)
 check('actual_inspect_postpublication_explicit_before_commit',F.inspect(leaf,ref(lp)['sha256'],source_update=q)['ready'] is False)
 refused('default_missing_commit',lambda:F.spec_checked(leaf,cli_only=True))
 qc={'schema':qi['schema'],'state':'SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED','request_sha256':qs,'request_reference':qr,'current_source_successor':q['current_source_successor'],'previous_input':q['previous_input'],'current_input':q['current_input'],'predecessor_request_sha256':er['sha256'],'predecessor_receipt_sha256':old['predecessor_receipt_sha256'],'source_receipt_sha256':aftersha,'layers':[mn],'files':['fixture/0.txt'],'gateway_started':False,'workers_enabled':False,'seconds':1.5};write(tx/'committed.json',qc)
 check('native_check_before_T1',native.check() is None)
 check('default_before_T1',F.spec_checked(leaf,cli_only=True)[0]==H)
 check('inspect_before_T1',F.inspect(leaf,ref(lp)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
 # Original CP request/intent/commit/before/staged files are frozen facts.
 cp_immutable={str(p.relative_to(tx)):sha(p.read_bytes()) for p in tx.rglob('*') if p.is_file()}
 cp_original_config=q['configuration'].copy()
 phase_seal=am['ordinary_gateway']['configuration_sha256']
 before_config=(H/'config.yaml').read_bytes()
 def publish(after):
  for name,state in after.items():write(H/name,state['data'])
  native.check()
 def assert_history(label):
  now={str(p.relative_to(tx)):sha(p.read_bytes()) for p in tx.rglob('*') if p.is_file()}
  check(label,now==cp_immutable and q['configuration']==cp_original_config)
 pending=native.runtime()
 stage1=T/'T1-stage'
 after1=native.afterimages(leaf,ref(lp),pending,stage1)
 check('T1_exact_five_writer_afterimages',len(after1)==5)
 check('T1_prepared_without_live_mutation',(H/'config.yaml').read_bytes()==before_config)
 publish(after1)
 check('T1_native_serializer_changes_root_raw',ref(H/'config.yaml')['sha256']!=q['configuration']['sha256'])
 check('T1_semantic_root_unchanged',native.effective(H/'config.yaml',fail_closed=True)==native.root_config)
 check('T1_original_phase_seal_retained',json.loads((H/F.MARKER).read_bytes())['ordinary_gateway']['configuration_sha256']==phase_seal)
 assert_history('T1_original_CP_immutable')
 if MODE=='baseline':
  try:F.spec_checked(leaf,cli_only=True)
  except (ValueError,OSError,KeyError,TypeError) as e:
   check('baseline_actual_default_reader_refusal',True,type(e).__name__+':'+str(e))
  else:check('baseline_actual_default_reader_refusal',False,'unexpected acceptance')
  try:F.inspect(leaf,ref(lp)['sha256'])
  except (ValueError,OSError,KeyError,TypeError) as e:
   check('baseline_actual_inspect_refusal',True,type(e).__name__+':'+str(e))
  else:check('baseline_actual_inspect_refusal',False,'unexpected acceptance')
  # Isolate the second independent historical-marker defect by restoring only
  # the LEGITIMATE current root config before raw bytes; no CP evidence mutates.
  saved=(H/'config.yaml').read_bytes();write(H/'config.yaml',before_config)
  try:refused('baseline_marker_afterimage_refusal_after_isolating_config_pin',lambda:F.spec_checked(leaf,cli_only=True))
  finally:write(H/'config.yaml',saved)
 else:
  check('T1_actual_default_spec',F.spec_checked(leaf,cli_only=True)[0]==H)
  check('T1_actual_default_inspect',F.inspect(leaf,ref(lp)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
  # P is represented solely by the proof-reference configuration leaf. These
  # synthetic proof bytes have NO observation/native acceptance credit. The
  # actual writer and native semantic/onboarding readers must handle T2.
  active=copy.deepcopy(pending)
  active['current_availability']['proof']=ref(H/'synthetic-runtime/proof')
  after2=native.afterimages(leaf,ref(lp),active,T/'T2-stage')
  check('T2_exact_five_writer_afterimages',len(after2)==5)
  publish(after2)
  check('T2_original_phase_seal_retained',json.loads((H/F.MARKER).read_bytes())['ordinary_gateway']['configuration_sha256']==phase_seal)
  assert_history('T2_original_CP_immutable')
  check('T2_actual_default_spec',F.spec_checked(leaf,cli_only=True)[0]==H)
  check('T2_actual_default_inspect',F.inspect(leaf,ref(lp)['sha256'])['runtime_acceptance']=='NOT_GRANTED')
  if not args.reuse_r1_negatives:
   def corrupt(name,path,mutate,fn=None):
    original=path.read_bytes();write(path,mutate(original))
    try:refused(name,fn or (lambda:F.spec_checked(leaf,cli_only=True)))
    finally:write(path,original)
   def change_json(raw,fn):
    d=json.loads(raw);fn(d);return enc(d)
   def config_change(raw,fn):
    from hermes_yaml import safe_load,safe_dump
    d=safe_load(raw);fn(d);return safe_dump(d).encode()
   corrupt('unapproved_root_configuration',H/'config.yaml',lambda b:config_change(b,lambda d:d['model'].update(default='foreign')))
   corrupt('unapproved_gateway_configuration',H/'config.yaml',lambda b:config_change(b,lambda d:d['gateway'].update(systemd_watchdog_seconds=31)))
   # Even a writer-shaped raw marker reseal cannot approve an unrelated root
   # config delta; the phase's original normalized seal remains authoritative.
   saved_config=(H/'config.yaml').read_bytes();saved_marker=(H/F.MARKER).read_bytes()
   write(H/'config.yaml',config_change(saved_config,lambda d:d['model'].update(default='foreign')))
   changed_marker=json.loads(saved_marker);changed_marker['profile_files']['config.yaml']=ref(H/'config.yaml')['sha256']
   write(H/F.MARKER,changed_marker)
   try:refused('unapproved_config_with_raw_marker_reseal',lambda:F.spec_checked(leaf,cli_only=True))
   finally:write(H/'config.yaml',saved_config);write(H/F.MARKER,saved_marker)
   corrupt('unapproved_marker_phase_seal',H/F.MARKER,lambda b:change_json(b,lambda d:d['ordinary_gateway'].update(configuration_sha256='f'*64)))
   corrupt('unapproved_marker_extra_metadata',H/F.MARKER,lambda b:change_json(b,lambda d:d.update(unapproved=True)))
   corrupt('unapproved_marker_profile_hash_type',H/F.MARKER,lambda b:change_json(b,lambda d:d['profile_files'].update({'config.yaml':True})))
   corrupt('unapproved_marker_profile_hash_format',H/F.MARKER,lambda b:change_json(b,lambda d:d['profile_files'].update({'config.yaml':'z'*64})))
   corrupt('unapproved_profile_config_onboarding',native.profile/'config.yaml',lambda b:b+b'\nforeign_config: true\n',native.check)
   corrupt('unapproved_onboarding_receipt',native.profile/native.users.ONBOARDING,lambda b:change_json(b,lambda d:d.update(config_sha256='f'*64)),native.check)
   corrupt('unapproved_user_marker',native.profile/native.users.MARKER,lambda b:change_json(b,lambda d:d.update(onboarding_sha256='f'*64)),native.check)
   corrupt('source_receipt_tamper',H/'hermes-agent.source.json',lambda b:b+b' ')
   corrupt('stamp_tamper',N/'install-stamp.json',lambda b:b+b' ')
   corrupt('operator_source_tamper',P/'scripts/friday_native.py',lambda b:b+b' ')
   corrupt('operator_marker_tamper',H/F.MARKER,lambda b:change_json(b,lambda d:d['ordinary_gateway']['operator_entry']['script'].update(path=str(T/'foreign.py'))))
   corrupt('input_tamper',lp,lambda b:b+b' ')
   corrupt('project_plugin_tamper',P/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
   corrupt('installed_plugin_tamper',H/'plugins/friday_rework/fixture0.py',lambda b:b+b' ')
   corrupt('native_bytes_tamper',N/'fixture/0.txt',lambda b:b+b' ')
   corrupt('CP_request_tamper',tx/'request.json',lambda b:b+b' ')
   corrupt('CP_intent_tamper',tx/'intent.json',lambda b:change_json(b,lambda d:d.update(gateway_started=True)))
   corrupt('CP_commit_tamper',tx/'committed.json',lambda b:change_json(b,lambda d:d.update(source_receipt_sha256='f'*64)))
   for n in ('before/FRIDAY-INSTALL.json','before/hermes-agent.source.json','before/hermes-agent/install-stamp.json','FRIDAY-INSTALL.json','hermes-agent.source.json','install-stamp.json'):
    corrupt('CP_immutable_'+n,tx/n,lambda b:b+b' ')
   write(tx/'rolled-back.json',{})
   try:refused('rolledback_leaf_after_T2',lambda:F.spec_checked(leaf,cli_only=True))
   finally:(tx/'rolled-back.json').unlink()
   assert_history('final_original_CP_immutable')
   check('final_actual_default_spec',F.spec_checked(leaf,cli_only=True)[0]==H)
 second_evidence=None
 if args.second_layer_root:
  from second_edge import run_second_edge
  second_evidence=run_second_edge(locals())
 result={'schema':'friday.mutable-native-leaf-regression.v1','state':'PASS','mode':args.mode,
  'checks':checks,'seconds':time.monotonic()-started,'invocation':sys.argv,'python':sys.executable,'second_edge':second_evidence,'helper_refs':{n:ref(HELPERS/'scripts'/n) for n in ('friday_install.py','friday_ordinary_install.py')},
  'ancestral_negative_matrices_reused':{'r1':args.reuse_r1_negatives,'third':True,'fourth':args.reuse_fourth_negatives,'fifth':args.reuse_fifth_negatives,'sixth':args.reuse_sixth_negatives,'seventh':args.reuse_seventh_negatives},'authority':'EXPLICIT_SYNTHETIC_AUTHORITY_NO_NATIVE_ACCEPTANCE','limits':{'cpu_seconds':args.cpu_seconds,'wall_seconds':args.wall_seconds,'address_space_bytes':2*1024**3},
  'facts':{'native_gateway_check':'ACTUAL_WHOLE_FUNCTION_ROLE_FALSE','onboarding':'ACTUAL_USER_SCOPE_CHECK_AND_REAL_NATIVE_RESEALER',
   'native_config_serializer':'ACTUAL_ATOMIC_CONFIG_WRITE','writer':'ACTUAL_WHOLE_PREPARE_AFTERIMAGES',
   'T1_T2':'EXACT_FIVEFILE_WRITER_AFTERIMAGES; SYNTHETIC_AUTHORITY_PLAN; NOT_ACTUAL_DECLARATION/P_OBSERVATION',
   'authority_seams':['Synthetic owner.SOURCE/current receipt resolver','Read-only in-memory pre-existing product access principal'],
   'CP_immutable':cp_immutable,'T1_five_afterimages':{n:sha(s['data']) for n,s in after1.items()},
   **({'T2_five_afterimages':{n:sha(s['data']) for n,s in after2.items()}} if MODE!='baseline' else {})},
  'provenance':{'loaded_sources':native.provenance(),'repo_root':str(REPO),
   'harness':{p.name:ref(p) for p in W.glob('*.py')}}}
report=REPORT_DIR/'RESULT.json'
with report.open('xb') as stream:stream.write(enc(result))
report.chmod(0o600)
print('RESULT '+str(report),flush=True)
print(json.dumps({'state':result['state'],'checks':len(checks),'seconds':result['seconds']}))
