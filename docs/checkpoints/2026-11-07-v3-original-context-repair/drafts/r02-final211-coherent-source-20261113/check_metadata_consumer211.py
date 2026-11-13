"""Execute the actual final v13 closest metadata edge with named, nonlive seams.

This is deliberately not the real whole builder/default consumer: prior history is
an exact saved210 memo; external config/profile/unit/launcher refs are metadata-only;
stop before installed plugin/native/credential/authority consumers. All file reads
after audit registration are restricted to this stand and the Python stdlib.
"""
import ast,copy,datetime,hashlib,importlib.util,json,os,resource,sys,time,traceback
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
B=Path(__file__).resolve().parent;CP='docs/checkpoints/2026-11-07-v3-original-context-repair'
started=time.monotonic();checks=[];read_paths=set();external_pin_metadata=[];seam_hits=[]
def enc(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def digest(x):return hashlib.sha256(x).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def check(n,v,**facts):checks.append(dict(name=n,pass_=bool(v),**facts));assert v,n
def read(p):return json.loads(Path(p).read_bytes())
def audit(event,args):
 if event=='open' and not isinstance(args[0],int):
  p=Path(os.fsdecode(args[0])).absolute();flags=args[2]
  if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC) and not p.is_relative_to(B):raise PermissionError('outside_own_write')
  if not p.is_relative_to(B) and not str(p).startswith(('/usr/lib/python','/usr/local/lib/python','/usr/share/locale')):raise PermissionError('external_read_denied:'+str(p))
  read_paths.add(str(p))
 if event in ('subprocess.Popen','socket.connect','socket.bind','os.system'):raise PermissionError('no_external_effect')
sys.addaudithook(audit)
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
m=load(B/'project503/scripts/friday_ordinary_install.py','final211_metadata_consumer')
q0=read(B/'before210/N211-REQUEST-METADATA.SOURCE-ONLY.json');value=read(B/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json')
old=read(B/'before210/INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json');receipt0=read(B/'before210/hermes-agent.source.json');marker0=read(B/'before210/FRIDAY-INSTALL.json');stamp0=read(B/'before210/hermes-agent/install-stamp.json')
spec=read(B/'FINAL-NATIVE-SPEC.json');projection=read(B/'NATIVE211-PROSPECTIVE-COMPOSITION.json')['expected_inventory']
home=Path(q0['home']);tx=home/'preparation/OFFLINE-SYNTHETIC211-METADATA-ONLY'
q=copy.deepcopy(q0);q['candidate_project']=str(B/'project503');q['current_input']=q['candidate_input']={'path':str(B/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json'),'sha256':sha(B/'INPUT-SOURCE211.PROSPECTIVE.NOT_INSTALLED.json')}
q['project_inventory']=value['project_files'];q['project_inventory_sha256']=digest(enc(value['project_files']))
raw0={home/n:(B/'before210'/n).read_bytes() for n in ['hermes-agent.source.json','FRIDAY-INSTALL.json','hermes-agent/install-stamp.json']}
pins={x['path']:x['sha256'] for x in q0.values() if isinstance(x,dict) and set(x)=={'path','sha256'}}
pins[q0['current_input']['path']]=q0['current_input']['sha256'];pins[q['current_input']['path']]=q['current_input']['sha256']
pins[q0['previous_input']['path']]=q0['previous_input']['sha256']
previous_script=marker0['ordinary_gateway']['operator_entry']['script'];pins[previous_script['path']]=previous_script['sha256']
rootref=q['current_source_successor']['root_project_update'];pins[rootref['path']]=rootref['sha256']
ancestor=Path('/OFFLINE-ANCESTOR-ANCHOR-METADATA.json')
root_request={'current_input':q['previous_input'],'publication_ancestor':{'request':{'path':str(ancestor),'sha256':digest(enc(q0))}},'native_unit':q['native_unit']}
pins[str(ancestor)]=digest(enc(q0))
prior={'request':{'current_input':q['previous_input'],'current_source_successor':{'schema':m.CURRENT_SOURCE_TWELFTH_SUCCESSOR_SCHEMA}},'value':old,'receipt':receipt0,'receipt_sha256':sha(B/'before210/hermes-agent.source.json'),'stamp':stamp0,'stamp_sha256':sha(B/'before210/hermes-agent/install-stamp.json'),'marker':marker0}
class Refused(Exception):pass
class ReachedBoundary(Exception):pass
mode='before';raw={};after_marker=None
class API:
 ROOT=B/'project503';MARKER='FRIDAY-INSTALL.json';SCHEMA=marker0['schema'];__file__=str(B/'project503/scripts/friday_install.py')
 def require(self,v,reason):
  if not v:raise Refused(reason)
 def canonical(self,p):return Path(p)
 def directory(self,p):return Path(p)
 def digest(self,b):return digest(b)
 def owned_file(self,p,private=False):
  p=Path(p)
  if p.is_relative_to(B):return p.read_bytes()
  if p in raw:return raw[p]
  if p==home/'config.yaml':
   seam_hits.append('config_leaf_bytes_not_read_metadata_only');return b'OFFLINE_METADATA_ONLY_NO_CONFIG_READ'
  raise Refused('unmapped_external_bytes:'+str(p))
api=API();m.api=lambda:api
def reference(ref):
 if type(ref)!=dict or set(ref)!={'path','sha256'}:raise Refused('offline_reference_shape')
 p=Path(ref['path'])
 if p.is_relative_to(B):
  if sha(p)!=ref['sha256']:raise Refused('offline_owned_reference_hash')
 else:
  if pins.get(str(p))!=ref['sha256']:raise Refused('offline_external_metadata_pin')
  if p in raw and digest(raw[p])!=ref['sha256']:raise Refused('offline_saved_source_pin')
  external_pin_metadata.append(str(p))
 return p
def json_read(p,private=True):
 p=Path(p)
 if p.is_relative_to(B):return read(p)
 if p in raw:return json.loads(raw[p])
 if p==ancestor:return copy.deepcopy(q0)
 raise Refused('unmapped_external_json:'+str(p))
def project_root(*args):seam_hits.append('prior_root198_to210_exact_saved_memo_not_reexecuted');return copy.deepcopy(root_request),copy.deepcopy(old)
def cp_tx(h,r):return tx if mode=='after' and r==q['current_input'] else None
def cp_proof(*args,**kw):
 seam_hits.append('synthetic_committed211_metadata_shape_not_transaction')
 fields={'layers':[spec['manifest_rel']],'files':[r['path'] for r in spec['native_files']]}
 return fields,dict(fields,source_receipt_sha256=digest(raw[home/'hermes-agent.source.json']))
def boundary(*args):raise ReachedBoundary('before_plugin_native_config_credential_authority_consumers')
m._current_source_reference=reference;m._current_source_json=json_read;m._project_current_root_checked=project_root
m._current_source_cp_transactions=cp_tx;m._current_source_cp_proof=cp_proof;m.checked_plugin_inventory=boundary
def setup(which):
 global mode,raw,after_marker
 mode=which;raw=dict(raw0)
 if mode=='after':
  receipt_raw=enc(projection);receipt_sha=digest(receipt_raw)
  stamp=copy.deepcopy(stamp0);stamp['fridaySource']={'baseTree':projection['base_tree'],'layers':projection['layers']}
  marker=copy.deepcopy(marker0);marker.update(input_sha256=q['current_input']['sha256'],source_receipt_sha256=receipt_sha)
  marker['ordinary_gateway']['source_receipt_sha256']=receipt_sha
  marker['ordinary_gateway']['operator_entry']={'input':q['current_input'],'script':{'path':str(B/'project503/scripts/friday_native.py'),'sha256':value['project_files']['scripts/friday_native.py']}}
  after_marker=marker;raw.update({home/'hermes-agent.source.json':receipt_raw,home/'hermes-agent/install-stamp.json':enc(stamp),home/'FRIDAY-INSTALL.json':enc(marker),tx/'before/hermes-agent.source.json':raw0[home/'hermes-agent.source.json'],tx/'before/FRIDAY-INSTALL.json':raw0[home/'FRIDAY-INSTALL.json'],tx/'before/hermes-agent/install-stamp.json':raw0[home/'hermes-agent/install-stamp.json'],tx/'FRIDAY-INSTALL.json':enc(marker),tx/'hermes-agent.source.json':receipt_raw,tx/'install-stamp.json':enc(stamp)})
def execute(request,current=value,history=prior):
 try:m._current_native_source_edge_checked(current,cli_only=True,source_update=request,prior_edge=history)
 except ReachedBoundary:return 'BOUNDARY'
 except Refused as e:return str(e)
 return 'UNEXPECTED_RETURN'
observations=[]
try:
 for which in ['before','after']:
  setup(which);result=execute(copy.deepcopy(q));check('actual_full_v13_metadata_edge_'+which,result=='BOUNDARY',reached=result)
  # All negatives start from the same coherent candidate and saved210 memo.
  for label,mutate in [
   ('wrong_before209',lambda x:x.update(installed_layers=209)),
   ('future14',lambda x:x['current_source_successor'].update(schema='friday.current-source-native-successor.v14')),
   ('wrong_previous210_hash',lambda x:x['previous_input'].update(sha256='f'*64)),
   ('wrong_receipt_CAS',lambda x:x['source_receipt'].update(sha256='f'*64)),
   ('wrong_stamp_CAS',lambda x:x['stamp'].update(sha256='f'*64)),
   ('wrong_marker_CAS',lambda x:x['marker'].update(sha256='f'*64)),
   ('wrong_final_inventory_hash',lambda x:x.update(project_inventory_sha256='f'*64)),
   ('installed_old_layer',lambda x:x.update(layer_names=['f07-malformed-docx-error-provenance-after-source209'])),
  ]:
   bad=copy.deepcopy(q);mutate(bad);r=execute(bad)
   if which=='after' and label=='wrong_marker_CAS':
    # Historical request before-marker hash is enforced during preflight and
    # canonical transaction proof. This seam does not replace that proof.
    check('after_before_marker_pin_shape_only_here_not_current_CAS',r=='BOUNDARY',reason=r)
   else:check(which+'_'+label+'_refused',r!='BOUNDARY' and r!='UNEXPECTED_RETURN',reason=r)
  if which=='after':
   for label,path,mutate in [
    ('current_marker',home/'FRIDAY-INSTALL.json',lambda x:x.update(source_receipt_sha256='f'*64)),
    ('current_stamp',home/'hermes-agent/install-stamp.json',lambda x:x['fridaySource'].update(layers=[])),
    ('current_receipt',home/'hermes-agent.source.json',lambda x:x['layers'].pop())]:
    original=raw[path];bad=json.loads(original);mutate(bad);raw[path]=enc(bad);r=execute(copy.deepcopy(q));raw[path]=original
    check('after_tampered_'+label+'_refused',r not in ('BOUNDARY','UNEXPECTED_RETURN'),reason=r)
  # Runtime-relevant changed manifest/preimage pins are executed from actual AST.
  tree=ast.parse((B/'project503/scripts/friday_ordinary_install.py').read_bytes())
  edge=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_current_native_source_edge_checked')
  for reason,variables in [
   ('ordinary_current_successor_exact_thirteenth_layer_images_required',dict(files=value['project_files'],manifest_name=spec['manifest_rel'],patch_name=spec['patch_rel'])),
   ('ordinary_current_successor_exact_thirteenth_native_images_required',dict(row=next(r for r in spec['native_files'] if r['path']=='gateway/run_startup.py'),name='gateway/run_startup.py')),
   ('ordinary_current_successor_native_preimage_changed',dict(row=next(r for r in spec['native_files'] if r['path']=='gateway/run_startup.py'),prior=receipt0['files']['gateway/run_startup.py']))]:
   calls=[n for n in ast.walk(edge) if isinstance(n,ast.Call) and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==reason]
   assert len(calls)==1;ns=dict(m.__dict__,thirteenth=True,**variables);expr=compile(ast.Expression(calls[0].args[0]),'<actual-changed-final-cohort-guard>','eval')
   check(which+'_actual_guard_positive_'+reason,eval(expr,ns))
   ns=copy.copy(ns)
   if 'files' in variables:ns['files']=dict(variables['files']);ns['files'][spec['manifest_rel']]='f'*64
   else:ns['row']=dict(variables['row']);ns['row']['sha256' if 'images' in reason else 'before_sha256']='f'*64
   check(which+'_actual_guard_negative_'+reason,eval(expr,ns) is False)
 check('own_reads_no_external_H_or_credentials',all(not p.startswith(str(home)) for p in read_paths) and not any(Path(p).name in ('.env','auth.json','pairing.json') for p in read_paths))
 check('final_startup_exact_accepted_hash',sha(B/'native-after/gateway/run_startup.py')=='d2c7047f77ba829ab416a985e12745dca9ea7d768741ca3316a5e1ad9a6b73a1')
 result=dict(schema='frw.r02.final211.closest-metadata-consumer.named-seams.v1',state='PASS_BEFORE_AFTER_SOURCE_METADATA_EDGE_WITH_NAMED_SEAMS_NOT_WHOLE_CONSUMER',checks=checks,count=len(checks),elapsed_seconds=time.monotonic()-started,at_moscow=datetime.datetime.now().astimezone().isoformat(),executed='Actual final private helper module _current_native_source_edge_checked in full through marker/receipt/stamp/private503/native4 guards. Stops at checked_plugin_inventory before plugin/native/config/credential/authority tail. Before210 actual saved bytes; after211 synthetic projected canonical shapes, not publication.',seams=sorted(set(seam_hits)),reference_metadata_only=sorted(set(external_pin_metadata)),reads=sorted(read_paths),no_real_H_builder_or_credential_identity=True,actual_transaction=False,admission=False,limits=['Root198..210 fixed-history consumer not rerun: saved authenticated210 memo supplied; immutable v13 guard35+15 reused by exact AST.','Config/profile/unit/launcher/external anchors are metadata-only pin seams, not current evidence. Own reads audit denied all external nonstdlib bytes.','After canonical metadata projection/synthetic intent+commit shape is source-only and never installed. Historical request before-marker SHA is shape-only in this after-leaf edge; full request/intent/commit proof is a named seam here, so this check has no after-CAS credit. Real whole defaultpostconsumer remains required after Root same admitted transaction.'])
except Exception as e:
 result=dict(state='HARNESS_FAILED_NOT_PRODUCT_RESULT',checks=checks,count=len(checks),exception=type(e).__name__,reason=str(e),locations=[dict(file=x.filename,line=x.lineno,name=x.name) for x in traceback.extract_tb(e.__traceback__)])
 (B/'METADATA-CONSUMER-HARNESS-FAILURES.json').write_bytes(enc(result));raise
(B/'METADATA-CONSUMER-CHECKS.json').write_bytes(enc(result));print(json.dumps({k:result[k] for k in ['state','count','elapsed_seconds']}))
