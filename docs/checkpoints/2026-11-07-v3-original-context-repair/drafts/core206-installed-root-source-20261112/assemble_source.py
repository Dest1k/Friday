"""Reproduce prospective206 Root source from exact immutable source inputs. No runtime execution."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,os,re
B=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112')
S=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
CROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
PREV=Path('/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
REC=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
OLDF=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-FUTURE-FRAME-R2-20261112')
P204=Path('/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111')
LAYER='f06-protected-office-profiles-after-source205'
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def raw(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(n,v):
 p=B/n;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 p.write_bytes(v if isinstance(v,bytes)else v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
def move_scope(text):
 paths={str(OLD):'ZZOWNZZ',str(OLDF):'ZZPREVFRAMEZZ',str(PREV):'ZZNEWSOURCEZZ',str(P204):'ZZPREVSOURCEZZ'}
 for p,q in paths.items():text=text.replace(p,q)
 hashes=[]
 def keep(m):hashes.append(m.group());return 'ZZHASH'+chr(65+len(hashes)//26)+chr(65+len(hashes)%26)+'ZZ'
 text=re.sub(r'[0-9a-f]{32,64}',keep,text)
 text=text.replace('205','ZZNUMBERZZ').replace('204','205').replace('ZZNUMBERZZ','206')
 text=text.replace('491','ZZCOUNTZZ').replace('489','491').replace('ZZCOUNTZZ','493').replace('17887','17880')
 text=text.replace('core-user-result-contracts-after-source205',LAYER)
 for i,h in enumerate(hashes,1):text=text.replace('ZZHASH'+chr(65+i//26)+chr(65+i%26)+'ZZ',h)
 text=text.replace('ZZOWNZZ',str(B)).replace('ZZPREVFRAMEZZ',str(OLD)).replace('ZZNEWSOURCEZZ',str(CROOT)).replace('ZZPREVSOURCEZZ',str(PREV))
 return text
closure=load(REC/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')
assert sha(REC/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')=='b26122f9b99ae6c906da802f34420c9d6205ca1319e9f74e5ffe46a246f2b910'
cp=closure['canonical_CP205'];tx=Path(cp['path']).parent
before=load(tx/'hermes-agent.source.json');spec=load(S/'FINAL-NATIVE-SPEC.json')
current=load(CROOT/'INPUT-SOURCE206.json');previous=load(PREV/'INPUT-SOURCE205.json')
assert {k:v for k,v in current.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'}
projected=copy.deepcopy(before);projected['layers'].append(dict(manifest=spec['manifest_rel'],manifest_sha256=spec['manifest']['sha256'],patch_sha256=spec['patch']['sha256']))
lock=current['sources_lock'];projected['sources_lock_sha256']=lock['sha256']if isinstance(lock,dict)else sha(lock)
for row in spec['native_files']:
 projected['files'][row['path']].update(sha256=row['sha256'],bytes=row['bytes'],mode='100644')
expected=hashlib.sha256(raw(projected)).hexdigest()
assert projected==load(S/'NATIVE206-PROSPECTIVE-COMPOSITION.json')['expected_inventory']
put('PROSPECTIVE206-PROJECTION.json',dict(schema='frw.root206.projection-not-installed.v1',state='EXPECTED_FROM_ACTUAL205_IMMUTABLE_STAGE_SOURCE_ONLY_NOT_CURRENT206',actual205=ref(REC/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json'),before_receipt=ref(tx/'hermes-agent.source.json'),input=ref(CROOT/'INPUT-SOURCE206.json'),native_spec=ref(S/'FINAL-NATIVE-SPEC.json'),expected_receipt_sha256=expected,ordered205_prefix_sha256=hashlib.sha256(raw(before['layers'])).hexdigest(),counts=dict(before_layers=205,after_layers=206,native=17891,project=493,plugins=52,base=17730,native_targets=11,selected_CAS=17,untouched_native_rows=17880),no_actual206_request_admission_UUID_receipt=True))
# All historical receipts are stage snapshots, not reads of mutable live H bytes.
chain=[];r=cp
while True:
 q=load(r['path']);d=Path(r['path']).parent;n=q['installed_layers']+1
 chain.append(dict(layers=n,request=r,committed=ref(d/'committed.json'),source_receipt=ref(d/'hermes-agent.source.json'),layer_names=q['layer_names'],successor_schema=q['current_source_successor']['schema']))
 if 'previous_native_update'not in q['current_source_successor']:break
 r=q['current_source_successor']['previous_native_update']
assert [x['layers']for x in chain]==list(range(205,198,-1))
historical=dict(schema='frw.root.actual205-immutable-history.v1',state='ACTUAL205_COMPLETED_HISTORICAL_NOT_FRESH_ANCHOR',references=dict(complete_closure=ref(REC/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json'),request=cp,committed=closure['committed'],root_journal=closure['operation'],root_return=closure['root_return']),stage_refs=[ref(tx/n)for n in ['hermes-agent.source.json','FRIDAY-INSTALL.json','install-stamp.json']],intent=ref(tx/'intent.json'),chain199_205=chain,ordered205_layers=before['layers'],historical_process_identities_not_future_authority=closure['current_services'],stage_state='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED historical; separate Root closure completes205')
put('ACTUAL205-HISTORICAL-METADATA.json',historical)
result=load(S/'RESULT.json')
reuse=dict(schema='frw.root206.unchanged-source-evidence.v1',state='REUSE_ACCEPTED_TASK23_FOUR_SYNTHETIC_GATES_NO_NEW_RUNTIME_CREDIT',final_source_result=ref(S/'RESULT.json'),source_freeze=ref(S/'SOURCE-FREEZE.json'),root_acceptance=ref(REC/'SOL-TASK23-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json'),independent_review=ref(S/'execution-review/RESULT.json'),four_gate_evidence=[dict(label=x['kind'],evidence={k:x['report'][k]for k in ['path','sha256']})for x in result['actual_gate_runs']],retained_limits=result['support_limits'])
put('REUSED-206-FINAL-SOURCE-EVIDENCE.json',reuse)
# Preserve unchanged old profile proof as historical evidence;206 changes neither profile file.
profile_names=['hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py']
profile={name:before['files'][name]['sha256']for name in profile_names}
assert not set(profile)&{x['path']for x in spec['native_files']}
join=dict(schema='frw.root206.unchanged-bank-profile-source-join.v1',state='SOURCE_ONLY_EXACT205_PROFILE_UNCHANGED_IN206_NO_NEW_APP_CREDIT',before_profile_source_digests=profile,after_profile_source_digests=profile,changed_profile_definitions=[],new_Office_effects=0,saved_app_evidence_reused=True,evidence=[ref(OLD/'ROOT-205-MINIMUM-BANK-PROFILE-QUALIFICATION.json'),ref(OLD/'PROFILE-SOURCE-JOIN.json'),ref(REC/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json'),ref(S/'FINAL-NATIVE-SPEC.json')],limits='Exact205 PDF/presentation source bytes remain unchanged by206. Fresh bank metadata/topology/linktargets/rootCAS and four critical hashes still required. No new App/layout/formal/user/runtime credit.')
put('PROFILE-SOURCE-JOIN.json',join)
# Retain raw object verification helpers; no inherited205 current5 hardpins are used as206 proof.
origin_old=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE204-ROOT-MAINTENANCE-FRAME-20261111')
oldpolicy=load(origin_old/'ROOT-204-PUBLIC-ORIGIN-POLICY.json')
public5=load(REC/'F06-PUBLIC5-ACTUAL205-SOURCE-INTEGRATION-20261112/RESULT.json')['public5']
policy=dict(schema='frw.root206.raw-git-full-counterpart-origin-policy.v1',scope='Full493 current206public rawGit+workingbytes and currentprivate28, exact old48public489 plus completed205public491 ancestry; no runtimeauthority',execution_grant=False,published_ancestor48_policy=ref(origin_old/'ROOT-204-PUBLIC-ORIGIN-POLICY.json'),completed205_source_commit='b86eb1693cdb51f9d3a1a8bd0f7b6f8f06b497cb',completed205_public_input=ref(PREV/'INPUT-SOURCE205-PUBLIC-ACTUAL-INVENTORY.json'),current_public_input=ref(S/'INPUT-SOURCE206.PUBLIC.PROSPECTIVE.NOT_INSTALLED.json'),current_private_input=ref(CROOT/'INPUT-SOURCE206.json'),current_private_project=str(CROOT/'project493'),counterparts=ref(S/'COUNTERPART-INVARIANTS.json'),reviewed_current_files={k:v['sha256']for k,v in public5.items()},reviewed_current_modes={k:'100755'if k.endswith('/friday_v3_layer_publication.py')else'100644'for k in public5},expected206_receipt_sha256=expected,public_helper_sha256='40a404292832b258e48c4f5af7bac3fdf263ce30a4077bde0af0ab8eaed0a174',private_helper_sha256='489f6a23a4015bbb1daad9c405028b83e55b10725cd4f5e8b56ce678ee6e1eb9')
put('ROOT-206-PUBLIC-ORIGIN-POLICY.json',policy)
# Simple complete scope translations; substantive functions are replaced below.
for oldname,newname in [('boundary_contract.py','boundary_contract.py'),('start_core205_once.py','start_core206_once.py'),('core205-first-actual-root.py','f06-206-first-actual-root.py'),('root205_metadata.py','root206_metadata.py'),('run_native205_once.py','run_native206_once.py'),('resume_native205_services.py','resume_native206_services.py'),('prepare_source.py','prepare_source.py')]:put(newname,move_scope((OLD/oldname).read_text()))
for name in ['native_scope.py','admission-retained/observe-current-retained-units.py']:put(name,(OLD/name).read_bytes())
for name in ['build-layer-publication-request.py','friday_v3_layer_publication.py']:put('publication/'+name,(S/'publication'/name).read_bytes())
for p in OLD.glob('*-TEMPLATE.json'):
 name=move_scope(p.name);v=json.loads(move_scope(p.read_text()))
 put(name,v)
commands=json.loads(move_scope((OLD/'ROOT-FUTURE-COMMANDS.json').read_text()))
commands['commands']['builder'][commands['commands']['builder'].index('--current-source-native-predecessor')+1]='UNBOUND_GENUINE_CANONICAL_COMMITTED_CP205_REQUEST_PATH'
commands['order']='SOURCE ONLY. Root authentic actual205 predecessor + unchanged acceptedTask23 fourgates + new206sourceacceptance + freshallprofileanchor + finitefuture206authority. Explicit one-shotcaller; builder explicit --layer; fullinventory/CAS; freshreadback/binder/unchangedprofile/admission; onceactor. No consumed effect replay.'
put('ROOT-FUTURE-COMMANDS.json',commands)
# Mutable during assembly only, before sourcefreeze.
def edit(n,fn):
 p=B/n;p.write_text(fn(p.read_text()));p.chmod(0o600)
# Concrete references for metadata, carried to Root source acceptance template.
fixed=dict(prepared_composition=ref(S/'M2-RESULT-IMMUTABLE.json'),native_spec=ref(S/'FINAL-NATIVE-SPEC.json'),source_freeze=ref(S/'SOURCE-FREEZE.json'),prepared_root_recipe=ref(S/'ROOT-INTEGRATION-RECIPE-FINAL.json'),pm_environment_basis=ref(P204/'READONLY-PM-ENVIRONMENT-BASIS.json'),counterparts=ref(S/'COUNTERPART-INVARIANTS.json'),architecture_review=ref(S/'review/RESULT.json'),actual205_source_integration=ref(REC/'F06-PUBLIC5-ACTUAL205-SOURCE-INTEGRATION-20261112/RESULT.json'),prospective_composition=ref(S/'NATIVE206-PROSPECTIVE-COMPOSITION.json'))
m=(B/'root206_metadata.py').read_text()
a=m.index('FIXED=');b=m.index('\nFINAL_GATE_LABELS=',a);m=m[:a]+'FIXED='+repr(fixed)+m[b:]
m=m.replace("S=Path('"+str(CROOT)+"')","S=Path('"+str(CROOT)+"')\nTASK23=Path('"+str(S)+"')")
m=m.replace("BEFORE_RECEIPT='94aea3888c0c89b99022cda3259b7e947d063d91d8525ddbff5bd4df3ac98d6a'","BEFORE_RECEIPT='aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb'")
m=m.replace("PREVIOUS_INPUT='cb35f5a9cdac806d95e51c70038944a29f4d1abf28ee74caaf2e9593d79d6677'","PREVIOUS_INPUT='2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9'")
a=m.index('ROOT205_ORIGIN_METADATA=');b=m.index('\ndef validate_snapshot_origin(',a)
helpers=(origin_old/'root204_metadata.py').read_text();helpers=helpers[helpers.index('def origin_git('):helpers.index('def source_origin(')]
origin='''ORIGIN_POLICY=POLICY_REF_LITERAL
ORIGINAL205_INPUT={'path':str(S205/'INPUT-SOURCE205.json'),'sha256':PREVIOUS_INPUT}
def source_origin(expected_head, fresh_origin, *, repository=None, provenance_mode='published-remote'):
 repository=Path(repository) if repository is not None else Path('/home/jericho/jericho/Friday_rework')
 policy=readref(ORIGIN_POLICY);old=readref(policy['published_ancestor48_policy'])
 require(policy['schema']=='frw.root206.raw-git-full-counterpart-origin-policy.v1','origin_policy_schema')
 require(type(expected_head)is str and len(expected_head)==40 and all(c in '0123456789abcdef'for c in expected_head),'bound_current_head_required')
 head=origin_git(repository,'rev-parse','HEAD').decode().strip()
 require(head==expected_head and provenance_mode in ('published-remote','local-committed-main'),'bound_current_head_mode_required')
 if provenance_mode=='published-remote':require(head==fresh_origin,'fresh_current_head_origin_required')
 else:
  require(fresh_origin is None,'local_mode_has_no_remote_observation')
  require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main' and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_committed_main_required')
 require(not origin_git(repository,'for-each-ref','--format=%(refname)','refs/replace/').strip(),'replacement_objects_refused')
 require(origin_git(repository,'rev-parse','--is-shallow-repository').strip()==b'false','full_local_ancestry_required')
 graft=Path(origin_git(repository,'rev-parse','--path-format=absolute','--git-path','info/grafts').decode().strip())
 require(not os.path.lexists(graft),'grafted_ancestry_refused')
 for commit in [head,old['published_snapshot'],policy['completed205_source_commit']]:
  require(git_oid('commit',origin_git(repository,'cat-file','commit',commit))==commit,'raw_commit_identity_changed')
  origin_git(repository,'merge-base','--is-ancestor',commit,head)
 ancestor_public=readref(old['public_input'])['project_files'];require(len(ancestor_public)==489,'exact48public489_required')
 oldtree=origin_tree(repository,old['published_snapshot']);origin_blobs(repository,oldtree,ancestor_public)
 origin_blobs(repository,oldtree,old['snapshot_guards'],old['snapshot_guard_modes'])
 for name,row in old['retained_executed_sources'].items():
  require(reference(row['path'])=={k:row[k]for k in ('path','sha256')} and row['sha256']==old['snapshot_guards'][name],'old48_executed_source_join_changed')
 predecessor_public=readref(policy['completed205_public_input'])['project_files'];require(len(predecessor_public)==491,'exact205public491_required')
 origin_blobs(repository,origin_tree(repository,policy['completed205_source_commit']),predecessor_public)
 public=readref(policy['current_public_input'])['project_files'];private=readref(policy['current_private_input'])['project_files'];counterpart=readref(policy['counterparts'])
 require(set(public)==set(private) and len(public)==493,'exact206public_private493_required')
 differences=sorted(name for name in public if public[name]!=private[name])
 require(differences==counterpart['private_difference_names'] and len(differences)==counterpart['private_difference_count']==28,'exact28_private_public_differences_required')
 require(public['scripts/friday_ordinary_install.py']==policy['public_helper_sha256'] and private['scripts/friday_ordinary_install.py']==policy['private_helper_sha256'],'distinct_private_public_helpers_required')
 newtree=origin_tree(repository,head);origin_blobs(repository,newtree,public)
 origin_blobs(repository,newtree,policy['reviewed_current_files'],policy['reviewed_current_modes'])
 for name,digest in public.items():require(sha(owned(repository/name))==digest,'current_public493_working_drift:'+name)
 for name,digest in private.items():require(sha(owned(Path(policy['current_private_project'])/name))==digest,'current_private493_source_drift:'+name)
 require(origin_git(repository,'rev-parse','HEAD').decode().strip()==head,'current_head_changed_during_origin_check')
 if provenance_mode=='local-committed-main':require(origin_git(repository,'symbolic-ref','-q','HEAD').strip()==b'refs/heads/main' and origin_git(repository,'rev-parse','refs/heads/main').decode().strip()==head,'local_main_changed_during_origin_check')
 return dict(schema='frw.root206.raw-git-full-counterpart-origin-proof.v1',policy=dict(ORIGIN_POLICY),published_snapshot=old['published_snapshot'],completed205_source_commit=policy['completed205_source_commit'],current_head=head,fresh_origin_main=fresh_origin,provenance_mode=provenance_mode,remote_publication='DEFERRED_NOT_VERIFIED'if provenance_mode=='local-committed-main'else'FRESH_REMOTE_MAIN_VERIFIED',ancestor_public_files=489,predecessor_public_files=491,public_project_files=493,private_difference_count=28,reviewed_current_file_count=5,target_input_sha256=policy['current_private_input']['sha256'],expected_NOT_INSTALLED_receipt_sha256=policy['expected206_receipt_sha256'])
'''.replace('POLICY_REF_LITERAL',repr(ref(B/'ROOT-206-PUBLIC-ORIGIN-POLICY.json')))
m=m[:a]+origin.split('def source_origin(')[0]+helpers+'def source_origin('+origin.split('def source_origin(',1)[1]+m[b:]
a=m.index('def actual_predecessor():');b=m.index('\ndef project_source_pins(',a)
predecessor='''def actual_predecessor():
 record=readref(reference(B/'ROOT-ACTUAL205-PREDECESSOR.json'))
 require(record['schema']=='frw.root.actual205-predecessor.v1' and record['state']=='ROOT_RECONCILED_GENUINE_INSTALLED205_NOT_EXPECTATION' and record['template_only_no_execution_grant']is False,'genuine_actual205_record_required')
 historical=readref(reference(B/'ACTUAL205-HISTORICAL-METADATA.json'))
 require(all(record[k]==v for k,v in historical['references'].items()),'exact_completed205_refs_required')
 for stage in historical['stage_refs']:readref(stage)
 readref(historical['intent'])
 closure=readref(record['complete_closure'])
 require(closure['state']=='INSTALLED205_PROJECT491_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED' and closure['operation']==record['root_journal'] and closure['canonical_CP205']==record['request'] and closure['actors_and_boundary_closed']is True,'actual205_completed_closure_required')
 stage_receipt=readref(next(r for r in historical['stage_refs']if r['path'].endswith('/hermes-agent.source.json')))
 require(len(stage_receipt['layers'])==205 and len(stage_receipt['files'])==17891 and stage_receipt['source_file_count']==17730 and stage_receipt['layers']==historical['ordered205_layers'],'exact_completed205_ordered_prefix_required')
 chain=historical['chain199_205'];require([row['layers']for row in chain]==list(range(205,198,-1)) and chain[0]['request']==record['request'],'exact199_to205_chain_required')
 for index,row in enumerate(chain):
  req=readref(row['request']);committed=readref(row['committed']);stage=readref(row['source_receipt']);n=row['layers']
  tx=H/'preparation'/('ordinary-source-update-v45-'+row['request']['sha256'][:16])
  require(row['request']['path']==str(tx/'request.json') and row['committed']['path']==str(tx/'committed.json') and row['source_receipt']['path']==str(tx/'hermes-agent.source.json'),'canonical_chain_paths_required')
  require(req['home']==str(H) and req['schema']=='friday.ordinary-telegram-source-update.v46' and req['installed_layers']==n-1 and req['layer_names']==row['layer_names'] and len(row['layer_names'])==1,'exact_historical_edge_required')
  successor=req['current_source_successor'];require(successor['schema']==row['successor_schema']=='friday.current-source-native-successor.v'+str(n-198) and successor['root_project_update']==ROOT198,'exact_historical_version_root198_required')
  require(successor.get('previous_native_update')==(chain[index+1]['request']if index+1<len(chain)else None),'exact_ordered_previous_native_chain_required')
  require(committed['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED' and committed['request_reference']==row['request'] and committed['request_sha256']==row['request']['sha256'] and committed['source_receipt_sha256']==row['source_receipt']['sha256'] and committed['current_input']==req['current_input'] and committed['current_source_successor']==successor and committed['gateway_started']is False and committed['workers_enabled']is False,'genuine_committed_chain_stage_required')
  require(stage['layers']==stage_receipt['layers'][:n],'complete_stage_prefix_required')
  require(not os.path.lexists(tx/'rolled-back.json') and (tx/'intent.json').is_file(),'committed_stage_not_rollback_required')
 request=readref(record['request']);committed=readref(record['committed'])
 require(request['current_input']==ORIGINAL205_INPUT and committed['source_receipt_sha256']==BEFORE_RECEIPT and closure['installed']['canonical4']['current_input']==ORIGINAL205_INPUT,'actual205_input_receipt_join_required')
 journal=readref(record['root_journal']);require(journal['state']=='NATIVE205_PROJECT491_FRESH_PERMANENT_SERVICES_RUNNING' and journal['expected_receipt_sha256']==BEFORE_RECEIPT and journal['native_before_after']==[204,205],'actual205_Root_journal_required')
 require(journal['request']['sha256']==record['request']['sha256'] and readref(journal['request'])==request,'actual205_Root_canonical_request_join_required')
 require(journal['full_selected_native_files_readback'] and journal['fresh_default_spec_inspect'] and journal['user_db_wal_shm_verified_before_starts'] and journal['publisher_closed_before_parent_custody_release'],'actual205_fresh_consumer_and_closure_required')
 ret=readref(record['root_return']);require(ret['returncode']==0 and ret['boundary_pid_absent']is True,'actual205_boundary_closed_required')
 readref(ROOT198)
 return record['request']
'''
m=m[:a]+predecessor+m[b:]
m=m.replace("'2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9'},'exact_final206_input_required'","'e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39'},'exact_final206_input_required'")
m=m.replace("'schema':'friday.current-source-native-successor.v7'","'schema':'friday.current-source-native-successor.v8'")
m=m.replace("spec['manifest_sha256']","spec['manifest']['sha256']").replace("spec['patch_sha256']","spec['patch']['sha256']")
m=m.replace("require(len(spec['native_files'])==4", "require(len(spec['native_files'])==11")
m=m.replace("require({row['path'] for row in spec['native_files']}=={'gateway/run_attachment_presentation.py','hermes_cli/friday_prompt_scope.py','hermes_cli/friday_workspace_presentation.py','tools/session_search_tool.py'},'exact_four_native_paths_required')","require({row['path']for row in spec['native_files']}=="+repr({row['path']for row in spec['native_files']})+",'exact_eleven_native_paths_required')")
m=m.replace("Path(spec['native_source_directory'])","TASK23/'native-after'")
a=m.index(" proposed=spec['private_proposed_receipt']");b=m.index(" require(projected['layers'][:-1]",a)
m=m[:a]+" expected=readref(FIXED['prospective_composition'])\n require(projected==expected['expected_inventory'] and hashlib.sha256(encoded(projected)).hexdigest()=='"+expected+"','exact206_projection_required')\n"+m[b:]
m=m.replace("require(len(targets)==10,'exact_ten_targets_required')","require(len(targets)==17,'exact_seventeen_targets_required')").replace("'selected_target_count':10","'selected_target_count':17")
# source helper-only inventory delta, fixed pair absent, exact nonproject unchanged.
m=m.replace(" expected={str(C/'scripts/friday_ordinary_install.py'):current['project_files']['scripts/friday_ordinary_install.py']}"," require({k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in current.items()if k!='project_files'},'actual205_nonproject_fields_unchanged_required')\n added=set(current['project_files'])-set(previous['project_files']);changed={n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'].get(n)}\n require(added=={\"patches/hermes/"+LAYER+"-manifest.json\",\"patches/hermes/"+LAYER+".patch\"} and changed=={'scripts/friday_ordinary_install.py'} and not set(previous['project_files'])-set(current['project_files']),'exact_helper_pair_delta_required')")
a=m.index('def validate_profile_join(');b=m.index('\ndef load_actor_binding(',a)
profile_func='''def validate_profile_join(qualification,before,spec):
 require(qualification['schema']=='frw.root.native206-minimum-installed-bank-profile-qualification.v1','profile206_schema_required')
 join=readref(qualification['profile_equivalence_join'])
 require(qualification['profile_equivalence_join']==PROFILE_JOIN_REF,'exact_reviewed_unchanged_profile_join_required')
 old={name:before['files'][name]['sha256']for name in ('hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py')}
 require(not set(old)&{row['path']for row in spec['native_files']},'F06_must_not_change_bank_profile_files')
 require(join['state']=='SOURCE_ONLY_EXACT205_PROFILE_UNCHANGED_IN206_NO_NEW_APP_CREDIT' and join['before_profile_source_digests']==join['after_profile_source_digests']==old and qualification['before_profile_source_digests']==qualification['minimum_profile_source_digests']==old,'exact205_unchanged206_profile_required')
 require(join['changed_profile_definitions']==[] and join['new_Office_effects']==0 and join['saved_app_evidence_reused']is True,'no_new_Office_credit')
 for source in join['evidence']:readref(source)
 require(qualification['format_layout_ready']is False and qualification['formal_test_credit']is False,'no_new_layout_formal_credit')
 return old
'''.replace('PROFILE_JOIN_REF',repr(ref(B/'PROFILE-SOURCE-JOIN.json')))
m=m[:a]+profile_func+m[b:]
(B/'root206_metadata.py').write_text(m)
# Correct literal source pins and source-request inventory expectations in actor/boundary.
for n in ['run_native206_once.py','f06-206-first-actual-root.py','boundary_contract.py']:
 def fix(t):
  t=t.replace('94aea3888c0c89b99022cda3259b7e947d063d91d8525ddbff5bd4df3ac98d6a','aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb')
  t=t.replace('cb35f5a9cdac806d95e51c70038944a29f4d1abf28ee74caaf2e9593d79d6677','2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9')
  return t
 edit(n,fix)
edit('f06-206-first-actual-root.py',lambda t:t.replace("AFTER = 'aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb'","AFTER = '"+expected+"'").replace("projection['selected_target_count'] == 10","projection['selected_target_count'] == 17").replace('core206-first-actual-root.py','f06-206-first-actual-root.py').replace("m.validate_profile_join(qualification,load(H/'hermes-agent.source.json'),load(S/'FINAL-NATIVE-SPEC.json'))","m.validate_profile_join(qualification,load(H/'hermes-agent.source.json'),load(Path(m.FIXED['native_spec']['path'])))").replace("ref(F205/'ROOT-205-MINIMUM-BANK-PROFILE-QUALIFICATION.json')","ref(F205/'ROOT-205-MINIMUM-BANK-PROFILE-QUALIFICATION.json')").replace("actual_scope_and_limits='Current bank allmetadata/topology/linktargets/rootCAS+4criticalhash; savedunchangedapp data joined with exact old2f641773/new0526 presentation AST metadata-only/caller proof. Old native203 runtime rows not reused as205. No Office/newbank/layout/user/formal credit; old failures/unknowns retained.'","actual_scope_and_limits='Fresh bank metadata/topology/linktargets/rootCAS+4criticalhash; exact actual205 PDF/presentation source unchanged in206, saved accepted205 minimumprofile reused by pinned source join. Old runtime rows not reused ascurrent205. No Office/newbank/layout/user/formal credit; old failures/unknowns retained.'").replace("all_profile_owned_work_quiescent=latest['global_work']","all_profile_owned_work_quiescent=anchor['checks']['current_all_profile_owned_work_quiescent'] and latest['global_work']").replace("rows[label] = row","row['observed_monotonic']=time.monotonic(); rows[label] = row"))
edit('start_core206_once.py',lambda t:t.replace('core206-first-actual-root.py','f06-206-first-actual-root.py'))
edit('boundary_contract.py',lambda t:t.replace("value['Task23_future206_not_integrated']is True","value['Task23_accepted_source_only_not_runtime_qualified']is True").replace('original_future206_budgets','new_future206_budgets').replace(" row=value[name]", " row=value[name]").replace("def compare_service(","def compare_service("))
# Explicit perDB freshness and acknowledged scope basis; Root owns authenticity.
edit('boundary_contract.py',lambda t:t.replace(" require(set(value['services'])", " basis=value['quiescence_basis'];require(basis['global_native']=='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY' and basis['all_three_sql']=='ALL3_PROFILE_LEASES_AND_ALL_ORIGIN_ASYNC_DELEGATIONS' and basis['scoped_tester_queue']=='SCOPED_TESTER_ONLY_NOT_ALL_PROFILE_PENDING_PROOF','explicit_quiescence_scope_basis_required')\n require(basis['root_current_all_profile_pending_approval_cancel_maintenance_evidence'],'fresh_broad_scope_Root_evidence_required')\n for ref in basis['root_current_all_profile_pending_approval_cancel_maintenance_evidence']:reference(ref);require(ref in value['evidence'],'broad_scope_ref_must_be_actual_anchor_evidence')\n require(type(basis['limits'])is list and 'SCOPED_TESTER_QUEUE_FIELDS_DO_NOT_PROVE_ALL_PROFILE_PENDING_OR_APPROVALS'in basis['limits'],'scoped_queue_limits_must_be_preserved')\n require(set(value['services'])").replace("def compare_service(actual", " for row in dbs.values():\n  observed=row['observed_monotonic'];require(type(observed)in(int,float)and math.isfinite(observed)and 0<=current_monotonic-observed<=15,'fresh_each_profile_SQL_observation_required')\ndef compare_service(actual"))
# Actor must use Task23 spec, actual installed205 private helper for lock consumers.
edit('run_native206_once.py',lambda t:t.replace("SPEC = Path('"+str(CROOT/ 'FINAL-NATIVE-SPEC.json')+"')","SPEC = Path('"+str(S/'FINAL-NATIVE-SPEC.json')+"')").replace('fd34937bb9bb31a3455d383f13755a2e9cf7d33daf18173d67fa87981aa0b22b','90b12d3a915e9c841f15360588094119ffe9fe40e1e3813a2cb630ec6a1e9e56').replace('234dc8be5adb507a3bcd2460cd8bb3042a02460ffe5ea645a499ff90cd9dd3fc','7e8e886adaf738296ded1fda09740df5b242d6ad3b98d4bcdb29d8ada672da9c').replace('9d87119679afd5e128f27cbcbb2b4c445140ac53d5a5ba371b3c0b35e07a19c9','f570120371c28eeeb9f708ffbd32d451056c39fc57f7a49ed60eb9db0eb26cb5').replace("assert len(targets) == 4","assert len(targets) == 11").replace("bound['selected_target_count'] == 10","bound['selected_target_count'] == 17").replace("'friday.current-source-native-successor.v7'","'friday.current-source-native-successor.v8'"))
# Source-only UNBOUND templates; no genuine206 mutable record is made here.
for name in [p.name for p in B.glob('*-TEMPLATE.json')]:
 v=load(B/name)
 if name=='ROOT-ACTUAL205-PREDECESSOR-TEMPLATE.json':
  v.update(historical['references'])
  v['actual_scope_and_limits']='ROOT independently verifies immutable completed205 refs; historicalPID observations are not fresh future authority.'
 if name=='ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json':
  v['before_profile_source_digests']=profile;v['minimum_profile_source_digests']=profile;v['profile_equivalence_join']=ref(B/'PROFILE-SOURCE-JOIN.json');v['native_spec']=fixed['native_spec'];v['operational_input']=ref(CROOT/'INPUT-SOURCE206.json');v['declared_minimum_scope']=join['limits']
 if name=='ROOT-206-SOURCE-ACCEPTANCE-TEMPLATE.json':
  v['known_limits']='Final206four source/synthetic gates reused unchanged; current installed205 is historical predecessor basis. New206 runtimeauthority/currentanchor/onceadmission UNBOUND; no actual206installation/runtime/user acceptance, no Office/model/user replay, no powerlossatomicity.'
  v['source_pins']=fixed;v['final_source_result']=reuse['final_source_result'];v['four_gate_evidence']=reuse['four_gate_evidence'];v['independent_review_evidence']=[reuse['independent_review']];v['newapp_review_evidence']=[ref(OLD/'PROFILE-SOURCE-JOIN.json'),ref(B/'PROFILE-SOURCE-JOIN.json')];v['frame_review_evidence']=[dict(path='UNBOUND_FINAL_INDEPENDENT206_REVIEW',sha256='UNBOUND')]
 if name=='ROOT-206-CURRENT-SERVICE-ANCHOR-TEMPLATE.json':
  v['historical_refs']='ROOT_COPY_EXACT_SOURCE_PINS_historical_refs';v['installed']=dict(layers=205,project=491,nativefiles=17891,plugins=52,base_source_file_count=17730,receipt_sha256=closure['installed']['canonical4']['source_receipt']['sha256'],input_sha256=previous and sha(PREV/'INPUT-SOURCE205.json'))
  v['quiescence_basis']=dict(global_native='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',all_three_sql='ALL3_PROFILE_LEASES_AND_ALL_ORIGIN_ASYNC_DELEGATIONS',scoped_tester_queue='SCOPED_TESTER_ONLY_NOT_ALL_PROFILE_PENDING_PROOF',root_current_all_profile_pending_approval_cancel_maintenance_evidence=[dict(path='UNBOUND_ROOT_GENUINE_FRESH_BROAD_SCOPE_OBSERVATION',sha256='UNBOUND')],limits=['SCOPED_TESTER_QUEUE_FIELDS_DO_NOT_PROVE_ALL_PROFILE_PENDING_OR_APPROVALS'])
 if name=='ROOT-206-RUNTIME-AUTHORITY-TEMPLATE.json':
  v['new_future206_budgets']=v.pop('original_future206_budgets');v['Task23_accepted_source_only_not_runtime_qualified']=v.pop('Task23_future206_not_integrated');v['caller']=dict(path=str(B/'start_core206_once.py'),sha256='ROOT_EXACT_SOURCE_SHA256');v['boundary']=dict(path=str(B/'f06-206-first-actual-root.py'),sha256='ROOT_EXACT_SOURCE_SHA256')
 if name=='ROOT-206-FRESH-READBACK-TEMPLATE.json':
  v['installed_receipt_sha256']=closure['installed']['canonical4']['source_receipt']['sha256'];v['installed_input_sha256']=sha(PREV/'INPUT-SOURCE205.json')
 if name=='ROOT-206-FRESH-ADMISSION-TEMPLATE.json':v['native_spec']=fixed['native_spec']
 (B/name).write_bytes(raw(v))
# Leaf hashes, then frame actor pin, form an acyclic dependency chain.
edit('run_native206_once.py',lambda t:t.replace('2d2b87fc5676c3b7e4c859605034a6ca60749e35d2755b0d94830cbc2c11c30d',sha(B/'root206_metadata.py')).replace('462a468b183ab25c6c3347eb89ff11fa81735346068d5e8f5779946bfac241da',sha(B/'resume_native206_services.py')))
for p in B.rglob('*'):
 if p.is_file():p.chmod(0o600)
 elif p.is_dir():p.chmod(0o700)
print(json.dumps(dict(state='ASSEMBLED_SOURCE_ONLY_NOT_FROZEN',expected206_receipt_sha256=expected,own_bytes=sum(p.stat().st_size for p in B.rglob('*')if p.is_file()))))
