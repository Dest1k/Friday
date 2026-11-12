"""Finite source-only finalization. No product code/import/service/network effect."""
from pathlib import Path
import datetime,difflib,hashlib,importlib.util,json,os,stat

def main():
 import sys
 if sys.argv[1:]!=['--finalize-source-only']:raise ValueError('explicit_finite_source_finalization_mode_required')
 B=Path(__file__).parent
 OLD=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/core207-installed-root-source-20261112')
 W=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-CORE208-LOGGING-PUBLICATION-PREP-20261112')
 raw=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def put(n,v):
  p=B/n;p.write_bytes(v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
 def ref(p):return {'path':str(p),'sha256':sha(p)}
 def load(p):return json.loads(Path(p).read_bytes())
 # All known source hashes bind source only. Current/runtime fields stay UNBOUND.
 a=(B/'run_native208_once.py').read_text().replace('ROOT208_METADATA_HASH_TO_FINALIZE',sha(B/'root208_metadata.py')).replace('ROOT208_RECOVERY_HASH_TO_FINALIZE',sha(B/'resume_native208_services.py'))
 put('run_native208_once.py',a)
 patches=[]
 for name,fields in {
 'ROOT-208-FRESH-ADMISSION-TEMPLATE.json':{'actor':B/'run_native208_once.py','recovery':B/'resume_native208_services.py'},
 'ROOT-208-RUNTIME-AUTHORITY-TEMPLATE.json':{'boundary':B/'core208-first-actual-root.py','caller':B/'start_core208_once.py'}
 }.items():
  v=load(B/name)
  for key,path in fields.items():patches.append({'template':name,'key':key,'before':v[key],'after':ref(path)});v[key]=ref(path)
  put(name,v)
 if not (B/'PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json').exists():put('PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json',{'state':'SOURCE_HASH_ONLY_ACTUAL_ROOT_BINDINGS_UNBOUND','rows':patches,'metadata_child_final':ref(B/'METADATA-DELTA.json')})
 spec=importlib.util.spec_from_file_location('source_only208_metadata',B/'root208_metadata.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 commands=load(W/'postpower-20261113/ROOT-NEXT-RECIPE.json')['builder_command_template_only']
 commands[commands.index('--output')+1]=str(B/'ROOT-FRESH-REQUEST.json');commands[3]=str(B/'publication/build-layer-publication-request.py')
 py=commands[0]
 future={'schema':'frw.root208.future-command-templates.v1','state':'SOURCE_ONLY_PREPARED_COMMANDS_NOT_EXECUTED','execution_grant':False,'final_source_acceptance':'UNBOUND','commands':{'builder':commands,'metadata_binder':[py,'-I','-B',str(B/'root208_metadata.py'),'--validate-and-bind'],'once_actor':[py,'-I','-B',str(B/'run_native208_once.py'),'--execute-once-root-accepted-208'],'conditional_saved_service_recovery_only':[py,'-I','-B',str(B/'resume_native208_services.py'),'--resume-saved-service-phases']},'environment':{'GIT_OPTIONAL_LOCKS':'0','PYTHONDONTWRITEBYTECODE':'1','HERMES_HOME':str(m.H)},'order':'Root authentic207/sourceorigin/private497 + independent actualbulk/frame acceptance + fresh currentall3SQL/globalnative/resource/slot/cancel/service authority; one fresh explicit208 v10 request. Source templates give no effects grant. Never execute old207 caller/clock/effect.'}
 put('ROOT-FUTURE-COMMANDS.json',future)
 source_refs={};history_refs={}
 def pin(p,target,expected=None):
  p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode)and s.st_uid==os.getuid()and s.st_nlink==1 and not any(x.is_symlink()for x in(p,*p.parents)),str(p)
  digest=sha(p);assert expected is None or digest==expected,(str(p),expected,digest);assert str(p)not in target or target[str(p)]==digest;target[str(p)]=digest
 # Exact actual source inputs and every nearest private/public consumer file. No source
 # claim is made from mutable current service/DB/native readiness observations.
 for key in ('project_origins','public_origins'):
  origins=load(m.FIXED[key]['path'])['rows']
  for row in origins.values():pin(row['path'],source_refs,row['sha256'])
 previous=load(m.ORIGINAL207_INPUT['path'])
 for name,digest in previous['project_files'].items():pin(m.P/name,source_refs,digest)
 for row in load(m.FIXED['native_spec']['path'])['native_files']:
  pin(W/'native-after'/row['path'],source_refs,row['sha256'])
  pin(W/'native-before'/row['path'],source_refs,row['before_sha256'])
 for path in [*B.glob('*.py'),*B.glob('*TEMPLATE.json'),*B.glob('publication/*.py'),*B.glob('admission-retained/*.py'),B/'ROOT-FUTURE-COMMANDS.json',B/'PROSPECTIVE208-PROJECTION.json',B/'METADATA-DELTA.json',B/'PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json']:
  if path.name!='finalize_frame.py':pin(path,source_refs)
 for r in [*m.FIXED.values(),*m.HISTORICAL207_REFS.values(),m.ORIGINAL207_INPUT,m.ORIGINAL207_ORIGIN_POLICY,m.PROFILE_SOURCE_JOIN,m.ROOT198]:pin(r['path'],history_refs,r['sha256'])
 # Exact read-only historical canonical chain, no current mutable H metadata included.
 history=load(m.FIXED['actual207_provenance']['path'])
 def historical_walk(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):
    p=v['path']
    if '/preparation/'in p or '/.cache/'in p:pin(p,history_refs,v['sha256'])
   for x in v.values():historical_walk(x)
  elif isinstance(v,list):
   for x in v:historical_walk(x)
 historical_walk(history['canonical_chain'])
 for p in [m.F207/'run_native207_once.py',m.F207/'resume_native207_services.py',m.F207/'review/final/RESULT.json',m.F207/'review/final/actor-recovery/RESULT.json',m.F207/'ROOT-207-MINIMUM-BANK-PROFILE-QUALIFICATION.json',Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-NEW-CREATOR-APP-RECIPE-20261111/app_contract.py'),Path('/home/jericho/.cache/FRW-ASTRA-V3-V03-RECEIVED-PPTX-MISSING-APP-20261111/ROOT-FRESH-RUNTIME-PROOF.json'),Path('/home/jericho/.cache/FRW-ASTRA-V3-ODP-APP-ROOT-FRAME-PREP-20261111/BANK-PHYSICAL-INTEGRITY.json')]:pin(p,history_refs)
 manifest={'schema':'frw.root208.coherent-after-actual207-source-pins.v1','state':'FROZEN_SOURCE_ONLY_GENUINE207_HISTORY_FUTURE208_NOT_INSTALLED','runtime_grant':False,'frame':str(B),'execution_commit':'UNBOUND_ROOT_CURRENT_COMMITTED_MAIN','execution_provenance_mode':'UNBOUND_EXPLICIT_ROOT_MODE','public_main_sha':None,'publisher_unit':'frw-astra-native208-install-after207-20261113.service','public_changed_files':m.PUBLIC5,'counts':{'before_layers':207,'after_layers':208,'before_project':495,'after_project':497,'native':17891,'base':17730,'plugins':52,'native_targets':2,'native_additions':0,'selected_CAS':8,'untouched_native_rows':17889,'pair_absent':2},'freeze':'Acyclic exact external argv digest. Excludes self, later reviews/results/recipe, actual future Root bindings/requests/readbacks/admission/onceclaims/operations. Root committed public497 provenance remains UNBOUND; observed historical207 immutable refs are not current readiness.','source_refs':source_refs,'historical_refs':history_refs,'retained_limits':{'unexposed_all_profile_pending_queues_approvals_not_proved':True,'allhistory_legacy8_probe_historical_not_new_increment_blocker':True,'source_only_not_install_runtime_or_user_acceptance':True,'journaled_rollback_not_powerloss_atomicity':True,'consumed207_clocks_effects_closed':True,'initial_F06_document_operation_not_replayed':True,'healthy_permanent_services_infinity':True,'broader_v3_and_wholeprivacy_not_accepted':True}}
 put('SOURCE-PINS.json',manifest)
 # Exact diff against historical source archive, never modified or executed.
 mapping={'boundary_contract.py':'boundary_contract.py','native_scope.py':'native_scope.py','core208-first-actual-root.py':'f06-207-first-actual-root.py','root208_metadata.py':'root207_metadata.py','start_core208_once.py':'start_core207_once.py','run_native208_once.py':'run_native207_once.py','resume_native208_services.py':'resume_native207_services.py','admission-retained/observe-current-retained-units.py':'admission-retained/observe-current-retained-units.py'}
 rows=[]
 for new,old in mapping.items():
  diff=''.join(difflib.unified_diff((OLD/old).read_text().splitlines(True),(B/new).read_text().splitlines(True),fromfile='historical207/'+old,tofile='future208/'+new));name=new.replace('/','__')+'.diff';put(name,diff);rows.append({'before':ref(OLD/old),'after':ref(B/new),'diff':ref(B/name)})
 put('DIFF-MANIFEST.json',{'state':'EXACT_SOURCE_DELTA_ONLY','rows':rows,'metadata_template_parent_delta':ref(B/'PARENT-SOURCE-TEMPLATE-BINDING-DELTA.json')})
 print(json.dumps({'state':'SOURCE_FROZEN_ROOT_BINDINGS_UNBOUND','manifest':ref(B/'SOURCE-PINS.json'),'source_refs':len(source_refs),'historical_refs':len(history_refs)}))

if __name__=="__main__":main()
