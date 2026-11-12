"""Bounded composition controls: actual own patch consumer and source inventories."""
import ast,copy,hashlib,json,os,resource,signal,subprocess,tempfile,time
from pathlib import Path
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);signal.alarm(90)
B=Path(__file__).resolve().parent;S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112');start=time.monotonic();checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def check(n,v):assert v,n;checks.append(n)
def write(p,v):p.parent.mkdir(mode=0o700,exist_ok=True,parents=True);p.write_bytes(v)
def patch(root,p,rev=False,just=False):
 a=['git','--no-optional-locks','apply','--whitespace=nowarn']+(['--reverse'] if rev else [])+(['--check'] if just else [])+[str(p)]
 r=subprocess.run(a,cwd=root,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},capture_output=True,timeout=20);return r
spec=load(B/'FINAL-NATIVE-SPEC.json');rows=spec['native_files'];mn=spec['manifest_rel'];pt=spec['patch_rel'];man=load(B/'pair'/mn)
check('one_native_existing_7CAS_495project',len(rows)==1 and rows[0]['new_file'] is False and spec['selected_targets']==7 and spec['before_expected']=={'project':493,'native':17891,'layers':206,'plugins':52,'base':17730} and spec['after_expected']=={'project':495,'native':17891,'layers':207,'plugins':52,'base':17730})
old=load(S/'NATIVE206-PROSPECTIVE-COMPOSITION.json')['expected_inventory'];new=load(B/'NATIVE207-PROSPECTIVE-COMPOSITION.json')['expected_inventory']
check('native17891_and_exact206prefix',len(old['files'])==len(new['files'])==17891 and new['layers'][:206]==old['layers'] and len(new['layers'])==207)
check('one_codec_delta_other17890_native_unchanged',{n for n,h in old['files'].items() if new['files'][n]!=h}=={'tools/scoped_odf_password.py'})
check('accepted206other10_afterimages_unchanged',all(new['files'][r['path']]['sha256']==r['sha256'] for r in load(S/'FINAL-NATIVE-SPEC.json')['native_files'] if r['path']!='tools/scoped_odf_password.py'))
origins={};inputs={}
for kind,name,inp in [('operational','PROJECT495-ORIGINS.json','INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'),('public','PUBLIC495-ORIGINS.json','INPUT-SOURCE207.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json')]:
 ori=load(B/name)['rows'];v=load(B/inp);origins[kind]=ori;inputs[kind]=v
 check(kind+'_495_all_exact_genuine_origin_refs',len(ori)==len(v['project_files'])==495 and all(sha(Path(r['path']))==r['sha256']==v['project_files'][n] for n,r in ori.items()))
 prior=load(S/('INPUT-SOURCE206.PROSPECTIVE.NOT_INSTALLED.json' if kind=='operational' else 'INPUT-SOURCE206.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json'))
 check(kind+'_493to495_pair2_and_helper_only',{n for n,h in prior['project_files'].items() if v['project_files'][n]!=h}=={'scripts/friday_ordinary_install.py'} and set(v['project_files'])-set(prior['project_files'])=={mn,pt})
 check(kind+'_all_nonproject_inputs_unchanged',{k:v for k,v in prior.items() if k!='project_files'}=={k:v for k,v in v.items() if k!='project_files'})
check('all28_legitimate_counterpart_differences_preserved',sorted(n for n,h in inputs['operational']['project_files'].items() if inputs['public']['project_files'][n]!=h)==load(B/'COUNTERPART-INVARIANTS.json')['private_difference_names'] and len(load(B/'COUNTERPART-INVARIANTS.json')['private_difference_names'])==28)
prereq={}
for r in old['layers']:
 d=load(Path(origins['operational'][r['manifest']]['path']));p=d.get('patch',d.get('patch_file'))
 if '/' not in p:p=str(Path(r['manifest']).parent/p)
 prereq[p]=r['patch_sha256']
check('exact_full206_descriptor_declared_prerequisites',len(prereq)==206 and man['prerequisites']==prereq)
with tempfile.TemporaryDirectory(prefix='patch-controls-',dir=B) as td:
 t=Path(td);n=rows[0]['path'];write(t/n,(B/'native-before'/n).read_bytes());before=(t/n).read_bytes()
 check('real_native_patch_check',patch(t,B/'pair'/pt,just=True).returncode==0)
 check('real_native_patch_forward',patch(t,B/'pair'/pt).returncode==0 and sha(t/n)==rows[0]['sha256'])
 check('real_native_patch_double_apply_rejected',patch(t,B/'pair'/pt,just=True).returncode!=0)
 check('real_native_patch_reverse',patch(t,B/'pair'/pt,rev=True).returncode==0 and (t/n).read_bytes()==before)
 write(t/n,b'foreign\n');check('real_native_foreign_preimage_rejected',patch(t,B/'pair'/pt,just=True).returncode!=0)
 # Public5 exact Git patch forward/reverse in own isolated files.
 cp='docs/checkpoints/2026-11-07-v3-original-context-repair';files=['scripts/friday_ordinary_install.py',cp+'/friday_v3_layer_publication.py',cp+'/build-layer-publication-request.py']
 for n in files:write(t/n,(S/'public/scripts/friday_ordinary_install.py' if n.startswith('scripts/') else S/'publication'/Path(n).name).read_bytes())
 before={n:(t/n).read_bytes() for n in files}
 check('real_public5_patch_forward',patch(t,B/'PUBLIC-INTEGRATION.patch').returncode==0)
 check('real_public5_exact_afterimages',sha(t/files[0])==sha(B/'public/scripts/friday_ordinary_install.py') and all(sha(t/n)==sha(B/'publication'/Path(n).name) for n in files[1:]) and all(sha(t/n)==sha(B/'pair'/n) for n in (mn,pt)))
 check('real_public5_patch_reverse',patch(t,B/'PUBLIC-INTEGRATION.patch',rev=True).returncode==0 and all((t/n).read_bytes()==v for n,v in before.items()) and not (t/mn).exists() and not (t/pt).exists())
for p in [*B.glob('publication/*.py'),*B.glob('project495/scripts/*.py'),*B.glob('gates/controls/*.py'),*B.glob('gates/*.py')]:ast.parse(p.read_bytes())
check('all_source_and_controls_parse',True)
# Validate publisher exact admitted schemas and unchanged default4 using actual module.
import importlib.util,sys
p=B/'publication/friday_v3_layer_publication.py';s=importlib.util.spec_from_file_location('newpub',p);mod=importlib.util.module_from_spec(s);sys.modules[s.name]=mod;s.loader.exec_module(mod)
src=p.read_text();check('publisher_exact_ninth_schema_and_no_tenth','"friday.current-source-native-successor.v9"' in src and 'friday.current-source-native-successor.v10' not in src)
check('publisher_exact_one_layer_appended',mod.LAYER_NAMES[-1]==spec['layer'] and len(mod.LAYER_NAMES)==27)
result={'state':'PASS_SOURCE_COMPOSITION_CONTROLS','checks':checks,'count':len(checks),'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time(),'limits':{'wall_seconds':90,'cpu_seconds':60,'address_space_bytes':512*1024**2,'affinity':sorted(os.sched_getaffinity(0))},'no_actual_install_or_genuine_doc':True}
(B/'COMPOSITION-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('state','count','wall_seconds')}))
