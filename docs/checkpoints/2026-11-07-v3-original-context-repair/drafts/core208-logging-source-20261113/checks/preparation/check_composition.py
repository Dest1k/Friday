import ast,copy,hashlib,importlib.util,json,os,resource,subprocess,sys,tempfile,time
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True;resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
B=Path(__file__).resolve().parent;R=Path('/home/jericho/jericho/Friday_rework');CP='docs/checkpoints/2026-11-07-v3-original-context-repair';H=R/'.runtime/friday-normal-both-workers-frw032'
checks=[];start=time.monotonic()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(n,v):checks.append(dict(name=n,pass_=bool(v)));assert v,n
def load(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def write(p,b):p.parent.mkdir(mode=0o700,exist_ok=True,parents=True);p.write_bytes(b)
def apply(root,patch,reverse=False,checkonly=False):
 env=dict(PATH='/usr/bin:/bin',HOME=str(root.parent),GIT_CEILING_DIRECTORIES=str(root.parent),GIT_OPTIONAL_LOCKS='0')
 args=['git','--no-optional-locks','apply','--whitespace=nowarn']+(['-R'] if reverse else [])+(['--check'] if checkonly else [])+[str(patch)]
 p=subprocess.run(args,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);assert p.returncode==0,p.stderr.decode();return p
spec=json.loads((B/'FINAL-NATIVE-SPEC.json').read_bytes());receipt=json.loads((H/'hermes-agent.source.json').read_bytes());projection=json.loads((B/'NATIVE208-PROSPECTIVE-COMPOSITION.json').read_bytes())['expected_inventory']
check('real207_receipt_pin',sha(H/'hermes-agent.source.json')=='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b')
check('projected208_true207_prefix',projection['layers'][:207]==receipt['layers'] and len(projection['layers'])==208)
check('projected_native17889_untouched',sum(row==projection['files'][n] for n,row in receipt['files'].items())==17889 and len(projection['files'])==17891)
# This is an increment on authenticated installed207, not a fresh base rebuild.
# The normal publisher binds the selected pair plus every retained composition row.
# Keep the first failed all-history preparation probe as an explicit observation.
bank={};oldbank={};oldroot=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112/project495')
for row in receipt['layers']:
 m=B/'project497'/row['manifest'];d=json.loads(m.read_bytes());p=d.get('patch') or 'patches/hermes/'+d['patch_file']
 check('retained_manifest_patch_'+str(len(bank)+1),sha(m)==row['manifest_sha256'] and sha(B/'project497'/p)==row['patch_sha256']==d['patch_sha256'])
 bank[p]=row['patch_sha256'];oldbank[p]=json.loads((oldroot/row['manifest']).read_bytes())
manifest=json.loads((B/'pair'/spec['manifest_rel']).read_bytes())
check('selected208_prerequisites_exact_actual207_bank',manifest['prerequisites']==bank and len(bank)==207)
legacy=[]
for p,d in oldbank.items():
 deps=dict(d.get('prerequisites',{}))
 if d.get('prerequisite_patch'):deps[d['prerequisite_patch']]=d['prerequisite_patch_sha256']
 for n,h in deps.items():
  n=n if n.startswith('patches/hermes/') else 'patches/hermes/'+n
  if bank.get(n)!=h:legacy.append(dict(manifest=p,dependency=n,expected=h,actual=bank.get(n)))
observation=dict(state='PRESERVED_FAILED_OPTIONAL_ALL_HISTORY_FRESH_PREPARATION_PROBE',reason='overlay_prerequisite_mismatch',original_checker='check_composition.py before narrowed increment check',unchanged_legacy_mismatches=legacy,count=len(legacy),all_mismatching_rows_identical_to_canonical495=True,conclusion='No historical patch/manifest changed; actual normal builder/currentconsumer PASS separately. This package qualifies only the exact207_to208 increment; fresh full_from_base private graph remains unqualified.')
(B/'ALL-HISTORY-PROBE-OBSERVATION.json').write_text(json.dumps(observation,indent=2)+'\n')
check('legacy_allhistory_mismatches_unchanged_not_rewritten',len(legacy)==8 and all((B/'project497'/r['manifest']).read_bytes()==(oldroot/r['manifest']).read_bytes() for r in receipt['layers']))
with tempfile.TemporaryDirectory(prefix='twofile-stand-',dir=B) as td:
 t=Path(td)
 for row in spec['native_files']:write(t/row['path'],(B/'native-before'/row['path']).read_bytes())
 apply(t,B/'pair'/spec['patch_rel'],checkonly=True);apply(t,B/'pair'/spec['patch_rel'])
 check('real_native_patch_two_exact_afterimages',all(sha(t/r['path'])==r['sha256'] for r in spec['native_files']))
 apply(t,B/'pair'/spec['patch_rel'],reverse=True)
 check('real_native_patch_reverse_two_exact_preimages',all(sha(t/r['path'])==r['before_sha256'] for r in spec['native_files']))
with tempfile.TemporaryDirectory(prefix='public5-stand-',dir=B) as td:
 t=Path(td);names=['scripts/friday_ordinary_install.py',CP+'/friday_v3_layer_publication.py',CP+'/build-layer-publication-request.py'];before={n:(R/n).read_bytes() for n in names}
 for n,b in before.items():write(t/n,b)
 apply(t,B/'PUBLIC-INTEGRATION.patch',checkonly=True);apply(t,B/'PUBLIC-INTEGRATION.patch')
 check('public5_exact_afterimages',sha(t/names[0])==sha(B/'public/scripts/friday_ordinary_install.py') and all(sha(t/n)==sha(B/'publication'/Path(n).name) for n in names[1:]) and all(sha(t/n)==sha(B/'pair'/n) for n in (spec['manifest_rel'],spec['patch_rel'])))
 apply(t,B/'PUBLIC-INTEGRATION.patch',reverse=True)
 check('public5_reverse_exact_before_and_absence',all((t/n).read_bytes()==b for n,b in before.items()) and not (t/spec['manifest_rel']).exists() and not (t/spec['patch_rel']).exists())
pub=load(B/'publication/friday_v3_layer_publication.py','exact208_pub')
check('publisher_only_next_layer_appended',len(pub.LAYER_NAMES)==28 and pub.LAYER_NAMES[-1]==spec['layer'])
check('publisher_historical_four_unchanged',len(pub.HISTORICAL_LAYER_NAMES)==4 and pub.resolve_layer_names(dict(schema=pub.SCHEMA))==pub.HISTORICAL_LAYER_NAMES)
check('publisher_v10_only_no_future', 'friday.current-source-native-successor.v10' in (B/'publication/friday_v3_layer_publication.py').read_text() and 'friday.current-source-native-successor.v11' not in (B/'publication/friday_v3_layer_publication.py').read_text())
value=json.loads((B/'INPUT-SOURCE208.PROSPECTIVE.NOT_INSTALLED.json').read_bytes())
layer=pub.read_layers(B/'project497',receipt,H,value['project_files'],[spec['layer']]);state=pub.check_preimages(layer,H/'hermes-agent',receipt['files'])
check('actual207_twofile_preimage_chain',state=={r['path']:r['sha256'] for r in spec['native_files']})
for label,change in [('wrong_preimage',lambda x:x[0]['files'][0].update(before_sha256='0'*64)),('new_file_claim',lambda x:x[0]['files'][0].update(new_file=True))]:
 l=copy.deepcopy(layer);change(l)
 try:pub.check_preimages(l,H/'hermes-agent',receipt['files'])
 except pub.Refused:check(label+'_refused',True)
 else:check(label+'_refused',False)
for p in [B/'public/scripts/friday_ordinary_install.py',B/'project497/scripts/friday_ordinary_install.py',*B.glob('publication/*.py'),*B.glob('checks/controls/*.py')]:ast.parse(p.read_bytes())
check('changed_sources_parse',True)
result=dict(state='PASS_EXACT_INCREMENT_SOURCE_COMPOSITION',checks=checks,count=len(checks),wall_seconds=time.monotonic()-start,actual_preparation_allhistory='FAILED_UNCHANGED_LEGACY_GRAPH_PRESERVED_SEPARATELY',selected_increment_layers=1,exact_complete_layers=208,source_only=True,no_install_or_runtime_acceptance=True)
(B/'COMPOSITION-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(state=result['state'],count=len(checks),wall_seconds=result['wall_seconds'])))
