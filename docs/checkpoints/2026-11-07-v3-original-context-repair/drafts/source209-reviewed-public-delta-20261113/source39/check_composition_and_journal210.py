"""Exact changed composition plus real seven-target journal mechanics, private stand only."""
import ast,copy,hashlib,importlib.util,json,os,resource,stat,subprocess,sys,tempfile,time
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
B=Path(__file__).resolve().parent;R=Path('/home/jericho/jericho/Friday_rework');H=R/'.runtime/friday-normal-both-workers-frw032';P=Path('/home/jericho/.cache/FRW-SOL-V3-F07-NATIVE209-AFTER208-CORE-20261113')
CP='docs/checkpoints/2026-11-07-v3-original-context-repair';checks=[];started=time.monotonic()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(n,v,**facts):checks.append(dict(name=n,pass_=bool(v),**facts));assert v,n
def write(p,b,mode=0o600):p.parent.mkdir(parents=True,mode=0o700,exist_ok=True);p.write_bytes(b);p.chmod(mode)
def load(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def apply(root,patch,reverse=False,checkonly=False):
 env=dict(os.environ,PATH='/usr/bin:/bin',GIT_CEILING_DIRECTORIES=str(root.parent),GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
 args=['git','--no-optional-locks','apply','--whitespace=nowarn']+(['-R'] if reverse else [])+(['--check'] if checkonly else [])+[str(patch)]
 p=subprocess.run(args,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);assert p.returncode==0,p.stderr.decode()
spec=json.loads((B/'FINAL-NATIVE-SPEC.json').read_bytes());receipt=json.loads((H/'hermes-agent.source.json').read_bytes());projection=json.loads((B/'NATIVE210-PROSPECTIVE-COMPOSITION.json').read_bytes())['expected_inventory']
check('actual209_receipt_pin',sha(H/'hermes-agent.source.json')=='bf60335ab23269c2581118ba45a5485651aacb2a7aa1c7709a852faf9fff5564')
check('full_ordered210_exact209_prefix',projection['layers'][:209]==receipt['layers'] and len(projection['layers'])==210)
check('exact_native17890_retained',len(projection['files'])==17891 and sum(v==projection['files'][n] for n,v in receipt['files'].items())==17890)
check('exact_no_base_or_source_identity_change',{k:v for k,v in projection.items() if k not in ('layers','files')}=={k:v for k,v in receipt.items() if k not in ('layers','files')})
with tempfile.TemporaryDirectory(prefix='patch-stand-',dir=B) as td:
 t=Path(td);row=spec['native_files'][0];before=(H/'hermes-agent'/row['path']).read_bytes();write(t/row['path'],before)
 apply(t,Path(spec['patch']['path']),checkonly=True);apply(t,Path(spec['patch']['path']))
 check('real_Source39_patch_exact_afterimage',sha(t/row['path'])==row['sha256'])
 native_after=(t/row['path']).read_bytes()
 apply(t,Path(spec['patch']['path']),reverse=True);check('real_Source39_patch_reverse_exact', (t/row['path']).read_bytes()==before)
with tempfile.TemporaryDirectory(prefix='integration-stand-',dir=B) as td:
 t=Path(td);names=['scripts/friday_ordinary_install.py',CP+'/friday_v3_layer_publication.py',CP+'/build-layer-publication-request.py']
 base={n:subprocess.run(['git','--no-optional-locks','show','4d49c747fd7239cdfee2638f2c36f2edd6232b0a:'+n],cwd=R,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True,check=True,timeout=20).stdout for n in names}
 for n,b in base.items():write(t/n,b)
 apply(t,B/'PUBLIC-INTEGRATION.patch',checkonly=True);apply(t,B/'PUBLIC-INTEGRATION.patch')
 check('public_integration_exact_three_afterimages',all(sha(t/n)==sha(B/'source'/n) for n in names))
 apply(t,B/'PUBLIC-INTEGRATION.patch',reverse=True);check('public_integration_reverse_exact',all((t/n).read_bytes()==b for n,b in base.items()))
pub=load(B/'source'/CP/'friday_v3_layer_publication.py','source210_journal_publisher');builder=load(B/'source'/CP/'build-layer-publication-request.py','source210_journal_builder')
check('publisher30_known_layers_exact_one_appended',len(pub.LAYER_NAMES)==30 and pub.LAYER_NAMES[-1]==spec['layer'])
check('historical_four_unchanged',len(builder.LAYER_NAMES)==4 and builder.parse_args([]).layer_names==pub.HISTORICAL_LAYER_NAMES and pub.resolve_layer_names({'schema':pub.SCHEMA})==pub.HISTORICAL_LAYER_NAMES)
for flavour,root,inputfile,prior in [('private',B/'project501','INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json','INPUT-SOURCE209.PROSPECTIVE.NOT_INSTALLED.json'),('public',B/'source','INPUT-SOURCE210.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json','INPUT-SOURCE209.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json')]:
 value=json.loads((B/inputfile).read_bytes());old=json.loads((P/prior).read_bytes())
 check(flavour+'_501_exact_inventory',len(value['project_files'])==501 and all(sha(root/n)==h for n,h in value['project_files'].items()))
 check(flavour+'_only_helper_changed',{n for n,h in old['project_files'].items() if value['project_files'].get(n)!=h}=={'scripts/friday_ordinary_install.py'})
 check(flavour+'_exact_pair_addition',set(value['project_files'])-set(old['project_files'])=={spec['manifest_rel'],spec['patch_rel']} and not set(old['project_files'])-set(value['project_files']))
 check(flavour+'_nonproject_preserved',{k:v for k,v in value.items() if k!='project_files'}=={k:v for k,v in old.items() if k!='project_files'})
private=json.loads((B/'INPUT-SOURCE210.PROSPECTIVE.NOT_INSTALLED.json').read_bytes());public=json.loads((B/'INPUT-SOURCE210.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json').read_bytes())
check('private28_counterparts_exact',{n for n,h in private['project_files'].items() if public['project_files'][n]!=h}==set(spec['private_difference_names']) and len(spec['private_difference_names'])==28)
layers=pub.read_layers(B/'project501',receipt,H,private['project_files'],[spec['layer']]);state=pub.check_preimages(layers,H/'hermes-agent',receipt['files'])
check('normal_publisher_real209_CAS',state=={r['path']:r['sha256'] for r in spec['native_files']})
for label,mutate in [('wrong_preimage',lambda l:l[0]['files'][0].update(before_sha256='0'*64)),('false_addition',lambda l:l[0]['files'][0].update(new_file=True))]:
 bad=copy.deepcopy(layers);mutate(bad)
 try:pub.check_preimages(bad,H/'hermes-agent',receipt['files'])
 except pub.Refused:check(label+'_refused',True)
 else:check(label+'_refused',False)
# Seven selected targets use genuine bytes; synthetic metadata afterimages are
# explicitly journal-only and supply no after-consumer or installation claim.
native_name='hermes-agent/'+spec['native_files'][0]['path'];helper='scripts/friday_ordinary_install.py';mn=spec['manifest_rel'];pt=spec['patch_rel']
beforedata={native_name:(H/native_name).read_bytes(),helper:(H/helper).read_bytes(),mn:None,pt:None,**{n:(H/n).read_bytes() for n in ('hermes-agent.source.json','FRIDAY-INSTALL.json','hermes-agent/install-stamp.json')}}
afterdata={native_name:native_after,helper:(B/'project501'/helper).read_bytes(),mn:(B/'project501'/mn).read_bytes(),pt:(B/'project501'/pt).read_bytes(),**{n:b'JOURNAL_ONLY_SYNTHETIC_AFTERIMAGE\n'+n.encode() for n in ('hermes-agent.source.json','FRIDAY-INSTALL.json','hermes-agent/install-stamp.json')}}
check('exact_seven_selected_targets',len(beforedata)==len(afterdata)==spec['selected_targets']==7)
def makestand(t):
 home=t/'home';home.mkdir(mode=0o700)
 for n,b in beforedata.items():
  (home/n).parent.mkdir(parents=True,mode=0o700,exist_ok=True)
  if b is not None:write(home/n,b,0o644 if n==native_name else 0o600)
 pins={str(home/n):(None if b is None else dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))) for n,b in beforedata.items()}
 j=pub._CurrentSourceV5Journal(t/'journal',home,pins);j.preflight();return home,j
def images(home):return {n:None if not os.path.lexists(home/n) else ((home/n).read_bytes(),stat.S_IMODE((home/n).stat().st_mode)) for n in beforedata}
for injection in beforedata:
 with tempfile.TemporaryDirectory(prefix='journal-stand-',dir=B) as td:
  t=Path(td);home,j=makestand(t);old=images(home);published=[];pub.INJECT_AFTER_RENAME=True;pub.INJECT_TARGET=str(home/injection)
  pub.INJECT_SNAPSHOT_HOME=home;pub.INJECT_SNAPSHOT_DIR=None
  try:
   for n,b in afterdata.items():
    target=home/n
    if beforedata[n] is None:j.record_absent(target)
    else:j.record_existing(target,pub.owned_file(target))
    published.append(str(target));callback=j.prepare_publication(target,b,0o644 if n==native_name else 0o600)
    pub.publish(target,b,0o644 if n==native_name else 0o600,_before_replace=callback)
  except OSError as exc:check('postrename_injection_reached_'+injection,exc.errno==__import__('errno').EIO)
  else:check('postrename_injection_reached_'+injection,False)
  finally:pub.INJECT_AFTER_RENAME=False;pub.INJECT_TARGET=None
  check('own_afterimage_on_disk_'+injection,(home/injection).read_bytes()==afterdata[injection])
  j.restore(published);check('rollback_exact_bytes_modes_absence_'+injection,images(home)==old)
with tempfile.TemporaryDirectory(prefix='cas-stand-',dir=B) as td:
 t=Path(td);home,j=makestand(t);target=home/helper;data=target.read_bytes();write(target,data+b'foreign')
 try:j.record_existing(target,target.read_bytes())
 except pub.Refused:check('prepublication_foreign_CAS_refused',True)
 else:check('prepublication_foreign_CAS_refused',False)
with tempfile.TemporaryDirectory(prefix='foreign-stand-',dir=B) as td:
 t=Path(td);home,j=makestand(t);target=home/helper;j.record_existing(target,target.read_bytes());callback=j.prepare_publication(target,afterdata[helper],0o600);pub.publish(target,afterdata[helper],0o600,_before_replace=callback);write(target,b'foreign-write')
 try:j.restore([str(target)])
 except pub.Refused:check('foreign_rollback_state_refused_preserved',target.read_bytes()==b'foreign-write')
 else:check('foreign_rollback_state_refused_preserved',False)
result=dict(state='PASS_CHANGED_COMPOSITION_AND_SEVEN_TARGET_JOURNAL',at_moscow=__import__('datetime').datetime.now().astimezone().isoformat(),checks=checks,count=len(checks),elapsed_seconds=time.monotonic()-started,source_only=True,full_v12_publisher_transaction=False,limits='Journal mechanics seven real target beforeimages and own synthetic metadata afterimages; no full transaction/current admission/runtime proof. Unchanged Source39 behavior and ancestral full-gate results reused.')
(B/'COMPOSITION-AND-JOURNAL-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('state','count','elapsed_seconds')}))
