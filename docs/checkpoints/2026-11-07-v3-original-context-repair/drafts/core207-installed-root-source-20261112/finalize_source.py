"""Complete own source deltas before one acyclic freeze; never binds or executes runtime."""
from pathlib import Path
import ast,hashlib,json,os,re
B=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112')
W=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112')
PREV=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
CROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112')
os.umask(0o077)
assert not (B/'SOURCE-PINS.json').exists()
def load(p):return json.loads(Path(p).read_bytes())
def raw(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(n,v):
 p=B/n;p.write_bytes(v if isinstance(v,bytes)else v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
def edit(n,a,b,count=1):
 p=B/n;s=p.read_text();assert s.count(a)==count,(n,a,s.count(a));put(n,s.replace(a,b))
def function(s,name,new):
 tree=ast.parse(s);n=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name==name);lines=s.splitlines(keepends=True)
 return ''.join(lines[:n.lineno-1])+new.rstrip()+'\n'+''.join(lines[n.end_lineno:])
projection=load(B/'PROSPECTIVE207-PROJECTION.json');expected=projection['expected_receipt_sha256'];before=load(load(B/'ACTUAL206-HISTORICAL-METADATA.json')['stage_refs'][0]['path']);spec=load(W/'FINAL-NATIVE-SPEC.json');reuse=load(B/'REUSED-207-FINAL-SOURCE-EVIDENCE.json');oldpolicy=load(OLD/'ROOT-206-PUBLIC-ORIGIN-POLICY.json')
public=load(W/'INPUT-SOURCE207.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json');private=load(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json');origins=load(W/'PUBLIC495-ORIGINS.json');publicmap=origins['rows']
cpdir='docs/checkpoints/2026-11-07-v3-original-context-repair/'
files={cpdir+n:sha(W/'publication'/n)for n in ['friday_v3_layer_publication.py','build-layer-publication-request.py']}
files.update({n:public['project_files'][n]for n in ['scripts/friday_ordinary_install.py',spec['manifest_rel'],spec['patch_rel']]})
policy=dict(schema='frw.root207.raw-git-full-counterpart-origin-policy.v1',scope='Full495 current207 public rawGit+selected5 workingbytes and Rootactual private495/28; old48public489/completed205public491/completed206public493 ancestry. No authority.',execution_grant=False,published_ancestor48_policy=oldpolicy['published_ancestor48_policy'],completed205_source_commit=oldpolicy['completed205_source_commit'],completed205_public_input=oldpolicy['completed205_public_input'],completed206_source_commit='8d392e47c27e9d09d97645e50d2690c087b5c7f3',completed206_public_input=oldpolicy['current_public_input'],current_public_input=ref(W/'INPUT-SOURCE207.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json'),prospective_private_input=ref(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'),expected_actual_input_path=str(CROOT/'INPUT-SOURCE207.json'),expected_actual_input_sha256=sha(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'),current_private_project=str(CROOT/'project495'),counterparts=ref(W/'COUNTERPART-INVARIANTS.json'),private_origins=ref(W/'PROJECT495-ORIGINS.json'),public_origins=ref(W/'PUBLIC495-ORIGINS.json'),reviewed_current_files=files,reviewed_current_modes={n:'100755'if n.endswith('/friday_v3_layer_publication.py')else'100644'for n in files},expected207_receipt_sha256=expected,public_helper_sha256='1a0fdd1dac328c5424d5352d8c385a347b95e5f876d151dc88799c7a55c30007',private_helper_sha256='d6c68fb6350d2f97b94d8f2f07694858ac1e3e67bbd30f8ca646537495e66601')
put('ROOT-207-PUBLIC-ORIGIN-POLICY.json',policy)
fixed=dict(prepared_composition=ref(W/'M1-PREPARED-RESULT.json'),native_spec=ref(W/'FINAL-NATIVE-SPEC.json'),source_freeze=ref(W/'SOURCE-FREEZE.json'),prepared_root_recipe=ref(W/'ROOT-NEXT-RECIPE-FINAL.json'),pm_environment_basis=oldpolicy and load(OLD/'ROOT-206-SOURCE-ACCEPTANCE-TEMPLATE.json')['source_pins']['pm_environment_basis'],counterparts=ref(W/'COUNTERPART-INVARIANTS.json'),architecture_review=ref('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-SUCCESSOR-GATEPREP-INDEPENDENT-REVIEW-20261112/RESULT.json'),actual206_closure=projection['actual206'],prospective_composition=ref(W/'NATIVE207-PROSPECTIVE-COMPOSITION.json'),project_origins=ref(W/'PROJECT495-ORIGINS.json'),public_origins=ref(W/'PUBLIC495-ORIGINS.json'))
m=(B/'root207_metadata.py').read_text();tree=ast.parse(m)
for name,value in [('FIXED',fixed),('ORIGIN_POLICY',ref(B/'ROOT-207-PUBLIC-ORIGIN-POLICY.json'))]:
 n=next(n for n in ast.parse(m).body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets));lines=m.splitlines(keepends=True);m=''.join(lines[:n.lineno-1])+name+'='+repr(value)+'\n'+''.join(lines[n.end_lineno:])
# Exact private495 materialization is Root-only, separately acknowledged and verified at use.
project_binding='''def validate_project_binding():
 record=readref(reference(B/'ROOT-207-PROJECT-SOURCE.json'))
 require(record['schema']=='frw.root207.actual-private495-source.v1' and record['state']=='ROOT_MATERIALIZED_EXACT_PRIVATE495_FROM_ACTUAL206' and record['template_only_no_execution_grant']is False,'actual_private495_Root_binding_required')
 require(record['execution_grant']is False and record['actual_project']==str(C) and record['actual_input']=={'path':str(S/'INPUT-SOURCE207.json'),'sha256':'CURRENT_INPUT_SHA'} and record['previous_input']==ORIGINAL206_INPUT,'exact_actual_private495_domain_required')
 require(record['prospective_input']==FIXED_PROSPECTIVE and record['private_origins']==FIXED['project_origins'] and record['public_origins']==FIXED['public_origins'] and record['counterparts']==FIXED['counterparts'],'exact495_origin_binding_required')
 actual=readref(record['actual_input']);prospective=readref(record['prospective_input']);previous=readref(record['previous_input'])
 require(actual==prospective and {k:v for k,v in actual.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'},'actual207_must_derive_from_actual206_nonproject_fields')
 origins=readref(record['private_origins'])['rows'];require(len(origins)==495 and len(dict(origins))==495 and {n:r['sha256']for n,r in origins.items()}==actual['project_files'],'full495_private_origins_required')
 for name,row in origins.items():
  require(reference(row['path'])=={k:row[k]for k in ('path','sha256')} and sha(owned(C/name))==row['sha256'],'actual_private495_source_drift:'+name)
 public=readref(FIXED_PUBLIC);counterpart=readref(record['counterparts']);diff=sorted(n for n in actual['project_files']if actual['project_files'][n]!=public['project_files'][n])
 require(set(public['project_files'])==set(actual['project_files']) and len(diff)==counterpart['private_difference_count']==28 and diff==counterpart['private_difference_names'],'exact_private_public28_required')
 require(record['physical495_verified']is True and record['private_public28_verified']is True,'Root_materialization_checks_required')
 return record
'''.replace('CURRENT_INPUT_SHA',policy['expected_actual_input_sha256']).replace('FIXED_PROSPECTIVE',repr(policy['prospective_private_input'])).replace('FIXED_PUBLIC',repr(policy['current_public_input']))
m=m.replace('def project_source_pins(request):',project_binding+'\ndef project_source_pins(request):\n validate_project_binding()')
# Full historic rawGit beforeimages remain fixed; future current207 HEAD/mode remain runtime bindings.
origin='''def source_origin(expected_head, fresh_origin, *, repository=None, provenance_mode='published-remote'):
 repository=Path(repository)if repository is not None else Path('/home/jericho/jericho/Friday_rework')
 policy=readref(ORIGIN_POLICY);old=readref(policy['published_ancestor48_policy']);validate_project_binding()
 require(policy['schema']=='frw.root207.raw-git-full-counterpart-origin-policy.v1','origin_policy_schema')
 require(type(expected_head)is str and len(expected_head)==40 and all(c in '0123456789abcdef'for c in expected_head),'bound_current_head_required')
 head=origin_git(repository,'rev-parse','HEAD').decode().strip()
 require(head==expected_head and provenance_mode in ('published-remote','local-committed-main'),'bound_current_head_mode_required')
 if provenance_mode=='published-remote':require(head==fresh_origin,'fresh_current_head_origin_required')
 else:
  require(fresh_origin is None,'local_mode_has_no_remote_observation')
  require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main'and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_committed_main_required')
 require(not origin_git(repository,'for-each-ref','--format=%(refname)','refs/replace/').strip(),'replacement_objects_refused')
 require(origin_git(repository,'rev-parse','--is-shallow-repository').strip()==b'false','full_local_ancestry_required')
 graft=Path(origin_git(repository,'rev-parse','--path-format=absolute','--git-path','info/grafts').decode().strip());require(not os.path.lexists(graft),'grafted_ancestry_refused')
 for commit in [head,old['published_snapshot'],policy['completed205_source_commit'],policy['completed206_source_commit']]:
  require(git_oid('commit',origin_git(repository,'cat-file','commit',commit))==commit,'raw_commit_identity_changed');origin_git(repository,'merge-base','--is-ancestor',commit,head)
 ancestor=readref(old['public_input'])['project_files'];require(len(ancestor)==489,'exact48public489_required');oldtree=origin_tree(repository,old['published_snapshot']);origin_blobs(repository,oldtree,ancestor);origin_blobs(repository,oldtree,old['snapshot_guards'],old['snapshot_guard_modes'])
 for name,row in old['retained_executed_sources'].items():require(reference(row['path'])=={k:row[k]for k in ('path','sha256')}and row['sha256']==old['snapshot_guards'][name],'old48_executed_source_join_changed')
 for number,count in [(205,491),(206,493)]:
  prior=readref(policy['completed'+str(number)+'_public_input'])['project_files'];require(len(prior)==count,'exact_predecessor_public_inventory_required');origin_blobs(repository,origin_tree(repository,policy['completed'+str(number)+'_source_commit']),prior)
 public=readref(policy['current_public_input'])['project_files'];private=readref({'path':policy['expected_actual_input_path'],'sha256':policy['expected_actual_input_sha256']})['project_files'];counterpart=readref(policy['counterparts'])
 require(set(public)==set(private)and len(public)==495,'exact207public_private495_required');differences=sorted(name for name in public if public[name]!=private[name]);require(differences==counterpart['private_difference_names']and len(differences)==counterpart['private_difference_count']==28,'exact28_private_public_differences_required')
 require(public['scripts/friday_ordinary_install.py']==policy['public_helper_sha256']and private['scripts/friday_ordinary_install.py']==policy['private_helper_sha256'],'distinct_private_public_helpers_required')
 newtree=origin_tree(repository,head);origin_blobs(repository,newtree,public);origin_blobs(repository,newtree,policy['reviewed_current_files'],policy['reviewed_current_modes'])
 for name,digest in policy['reviewed_current_files'].items():require(sha(owned(repository/name))==digest,'current_public5_working_drift:'+name)
 for name,digest in private.items():require(sha(owned(Path(policy['current_private_project'])/name))==digest,'current_private495_source_drift:'+name)
 require(origin_git(repository,'rev-parse','HEAD').decode().strip()==head,'current_head_changed_during_origin_check')
 if provenance_mode=='local-committed-main':require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main'and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_main_changed_during_origin_check')
 return dict(schema='frw.root207.raw-git-full-counterpart-origin-proof.v1',policy=dict(ORIGIN_POLICY),published_snapshot=old['published_snapshot'],completed205_source_commit=policy['completed205_source_commit'],completed206_source_commit=policy['completed206_source_commit'],current_head=head,fresh_origin_main=fresh_origin,provenance_mode=provenance_mode,remote_publication='DEFERRED_NOT_VERIFIED'if provenance_mode=='local-committed-main'else'FRESH_REMOTE_MAIN_VERIFIED',ancestor_public_files=489,predecessor205_public_files=491,predecessor_public_files=493,public_project_files=495,private_difference_count=28,reviewed_current_file_count=5,target_input_sha256=policy['expected_actual_input_sha256'],expected_NOT_INSTALLED_receipt_sha256=policy['expected207_receipt_sha256'])
'''
m=function(m,'source_origin',origin)
# Targeted semantic deltas: 1 existing native path,7CAS,17890 untouched. Historical journal is205→206.
m=m.replace("journal['native_before_after']==[206,207]","journal['native_before_after']==[205,206]")
m=m.replace("len(spec['native_files'])==11","len(spec['native_files'])==1").replace("'eleven_existing_paths_no_native_absent_required'","'one_existing_path_no_native_absent_required'")
a=m.index(" require({row['path']for row in spec['native_files']}==");b=m.index('\n',a)
m=m[:a]+" require({row['path']for row in spec['native_files']}=={'tools/scoped_odf_password.py'},'exact_single_native_codec_path_required')"+m[b:]
m=m.replace('len(targets)==17','len(targets)==7').replace("'selected_target_count':17","'selected_target_count':7").replace('exact_seventeen_targets_required','exact_seven_targets_required').replace('all17880_untouched_native_rows_required','all17890_untouched_native_rows_required').replace('one_explicit_eighth_layer_required','one_explicit_ninth_layer_required')
# All genuine206 stage references, root198 and oldchain refs remain unmodified.
# Finalexecutionreview is distinct from earlier source/gateprep review and must be Root-pinned.
a=m.index(" require(reused['independent_review'] in acceptance['independent_review_evidence']");b=m.index(" require(acceptance['frame_source_manifest']",a)
m=m[:a]+""" require(acceptance['modern_final_execution_review']in acceptance['independent_review_evidence'],'genuine_final_gate_independent_review_required')
 review=acceptance['modern_final_execution_review'];require(review!=reused['source_gateprep_review'] and review['path']=='/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-MODERN207-ACTUAL-GATES-20261112/RESULT.json','separate_modern_final_execution_review_required');readref(review)
 readref(reused['root_source_gate_authorization']);readref(reused['source_gateprep_review']);readref(reused['four_gate_summary'])
"""+m[b:]
# Profilejoin bytes are rebuilt above and fixed by exact hash.
a=m.index(" require(qualification['profile_equivalence_join']==");b=m.index('\n',a)
m=m[:a]+" require(qualification['profile_equivalence_join']=="+repr(ref(B/'PROFILE-SOURCE-JOIN.json'))+",'exact_reviewed_unchanged_profile_join_required')"+m[b:]
put('root207_metadata.py',m)
# Actor/boundary/recovery keep accepted lifetime, freshness, slot and ownedclosure architecture.
edit('f06-207-first-actual-root.py',"reference='b86eb1693cdb51f9d3a1a8bd0f7b6f8f06b497cb'","reference='8d392e47c27e9d09d97645e50d2690c087b5c7f3'")
edit('f06-207-first-actual-root.py',"projection['selected_target_count'] == 17","projection['selected_target_count'] == 7")
edit('f06-207-first-actual-root.py','exact207_seventeenCAS_required','exact207_sevenCAS_required')
edit('run_native207_once.py','assert len(targets) == 11','assert len(targets) == 1')
edit('run_native207_once.py',"bound['selected_target_count'] == 17","bound['selected_target_count'] == 7")
# Meaningful template bindings. Never instantiate any actual Root binding.
history=load(B/'ACTUAL206-HISTORICAL-METADATA.json')
put('ROOT-ACTUAL206-PREDECESSOR-TEMPLATE.json',dict(schema='frw.root.actual206-predecessor.v1',state='TEMPLATE_EXPECTED206_NOT_ACTUAL',template_only_no_execution_grant=True,actual_scope_and_limits='Root reconciles exact genuine206 immutable stage/closure refs; historicalPID notcurrentauthority.',**history['references']))
put('ROOT-207-PROJECT-SOURCE-TEMPLATE.json',dict(schema='frw.root207.actual-private495-source.v1',state='TEMPLATE_NOT_MATERIALIZED',template_only_no_execution_grant=True,execution_grant=False,actual_project=str(CROOT/'project495'),actual_input=dict(path=str(CROOT/'INPUT-SOURCE207.json'),sha256=policy['expected_actual_input_sha256']),previous_input=ref(PREV/'INPUT-SOURCE206.json'),prospective_input=policy['prospective_private_input'],private_origins=fixed['project_origins'],public_origins=fixed['public_origins'],counterparts=fixed['counterparts'],physical495_verified=False,private_public28_verified=False))
accept=load(B/'ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json');accept.update(source_pins=fixed,final_source_result=reuse['final_source_result'],four_gate_evidence=reuse['four_gate_evidence'],modern_final_execution_review=dict(path='/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-MODERN207-ACTUAL-GATES-20261112/RESULT.json',sha256='UNBOUND_ROOT_ACCEPTED_FINAL_EXECUTION_REVIEW'),independent_review_evidence=[reuse['source_gateprep_review'],dict(path='/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-MODERN207-ACTUAL-GATES-20261112/RESULT.json',sha256='UNBOUND_ROOT_ACCEPTED_FINAL_EXECUTION_REVIEW')],newapp_review_evidence=[ref(OLD/'PROFILE-SOURCE-JOIN.json'),ref(B/'PROFILE-SOURCE-JOIN.json')],known_limits='Modern finalexecutionreview dependency UNBOUND until Root pins actual accepted independent finalreview. Actual207input/project/HEAD/mode/sourceacceptance/anchor/authority unbound. Modern7 originalFAIL/editnone, sourceR3privacy, App/full170/120/B00 andoldUNKNOWN/consumedclocks remain; no powerlossatomicity.')
put('ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json',accept)
for n in ['ROOT-207-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json','ROOT-207-FRESH-ADMISSION-TEMPLATE.json']:
 v=load(B/n);v['native_spec']=fixed['native_spec']
 if 'profile_equivalence_join'in v:v['profile_equivalence_join']=ref(B/'PROFILE-SOURCE-JOIN.json')
 put(n,v)
# Fix static dependency hashes leafs→metadata→actor→admission, without any source cycle.
s=(B/'run_native207_once.py').read_text()
for exp,digest in [("B / 'root207_metadata.py'",sha(B/'root207_metadata.py')),('CP',sha(B/'publication/friday_v3_layer_publication.py')),('RESTORE',sha(B/'resume_native207_services.py'))]:s,n=re.subn(r"assert sha\("+re.escape(exp)+r"\) == '[0-9a-f]{64}'","assert sha("+exp+") == '"+digest+"'",s);assert n==1,(exp,n)
put('run_native207_once.py',s)
admission=load(B/'ROOT-207-FRESH-ADMISSION-TEMPLATE.json');admission['actor']=ref(B/'run_native207_once.py');admission['recovery']=ref(B/'resume_native207_services.py');put('ROOT-207-FRESH-ADMISSION-TEMPLATE.json',admission)
# Actual206 observed metadata is not a current207 or newoperation grant.
for p in B.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
for p in B.rglob('*'):
 if p.is_file():p.chmod(0o600)
 elif p.is_dir():p.chmod(0o700)
print(json.dumps(dict(state='FINALIZED_SOURCE_UNBOUND_NOT_FROZEN',expected207_receipt=expected,metadata_sha256=sha(B/'root207_metadata.py'),actor_sha256=sha(B/'run_native207_once.py'))))
