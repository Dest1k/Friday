"""Pure metadata join for a later Root boundary; no collector, product import or grant.
Only CLI --validate-and-bind writes an exclusive own-bundle metadata record. It cannot
produce request/admission/qualification/source acceptance or call any live consumer.
Root supplies authentic readbacks; validation is not a kernel/runtime proof.
"""
from pathlib import Path
import argparse,copy,datetime,hashlib,json,os,stat,time
B=Path(__file__).resolve().parent
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
S=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112')
MODERN207=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112')
S206=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
P=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112/project493')
C=S/'project495'
LAYER='f06-modern-odt-authenticated-profile-after-source206'
BEFORE_RECEIPT='253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21'
PREVIOUS_INPUT='e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39'
ROOT198={'path':'/home/jericho/.cache/FRW-ASTRA-V3-DSH-COHERENT-ROOT-COMPOSITION-20261111/final-v1/fresh-source-request/REQUEST.json','sha256':'886c6ab5bc76a810b24004f7042ef7c1b5add1b78f04781fac9c96335e3bd448'}
# Prepared source evidence only: none of these pins is a final gate/result grant.
FIXED={'prepared_composition': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/M1-PREPARED-RESULT.json', 'sha256': 'ed43902d011f23b6253c0da25092c36e6f70bf251328288c1f32777506ec8d41'}, 'native_spec': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/FINAL-NATIVE-SPEC.json', 'sha256': 'be6ae04a4a463e319fd050a2d9cb4bcaa9ea23e1a29b0d942c73f519850751cb'}, 'source_freeze': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/SOURCE-FREEZE.json', 'sha256': 'a1a34dcca440295256dae2ee0272643cdacc8459508bfae725873ca07e8503a6'}, 'prepared_root_recipe': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/ROOT-NEXT-RECIPE-FINAL.json', 'sha256': '3efb6db849fb7f9e0da3b0f694aacc90d1fc4b969a41695e0872247565cbb399'}, 'pm_environment_basis': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111/READONLY-PM-ENVIRONMENT-BASIS.json', 'sha256': '2ab5df26d6bd153ccc175e5813ad0fd769be377611b653fee486e3c3fab2062e'}, 'counterparts': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/COUNTERPART-INVARIANTS.json', 'sha256': 'b9d40876cc062e53c1ed7e3982016c2082a2920708faecd89dbe152dcdb69f74'}, 'architecture_review': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-SUCCESSOR-GATEPREP-INDEPENDENT-REVIEW-20261112/RESULT.json', 'sha256': '214d84a8ff6193c91da790ea0d68af1b6fbbf51251a3a0479b21987dd4f72750'}, 'actual206_closure': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json', 'sha256': '20e1a9ca845f52eeb0b6a149acc47fd91c9bc70142140e18095acdf18476b900'}, 'prospective_composition': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/NATIVE207-PROSPECTIVE-COMPOSITION.json', 'sha256': 'b220732fc706d089796a2cfe38c66078748dbef3326778d8e69da972fa915c94'}, 'project_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/PROJECT495-ORIGINS.json', 'sha256': '3b0de501303de8db10a406392228579d15e2a2b1e3478c50d6da6c9ec210a7c0'}, 'public_origins': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112/PUBLIC495-ORIGINS.json', 'sha256': '29da2ca9d1b940c792101bbf228499f637af107bac59909745fc4224db6a43ed'}}
FINAL_GATE_LABELS=('operational-success','operational-rollback','public-success','public-rollback')
SNAPSHOT_TRUE_FIELDS=(
 'source_authority_verified','public_source_pins_verified','operational_source_pins_verified',
 'profile_routing_verified','process_environment_verified','ordinary_readonly_quiescent',
 'all_three_user_db_zero_leases','stop_cooldown_clear','sole_heavy_slot_clear',
 'no_current_maintenance','cancellation_clear','resources_sufficient',
 'all_profile_owned_work_quiescent','current_request_unconsumed','old_effects_not_replayed',
 'native_pm_selected_python_verified','product_services_healthy_infinite_lifetime',
 'unchanged_bank_profile_evidence_reusable','known_limits_retained')
class InvalidBinding(ValueError):pass
def require(value,reason):
 if not value:raise InvalidBinding(reason)
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def owned(path):
 p=Path(path);v=p.lstat()
 require(stat.S_ISREG(v.st_mode) and not p.is_symlink() and v.st_uid==os.getuid() and v.st_nlink==1,'owned_regular_singlelink_required:'+str(p))
 # Historical0664 is accepted under protected home after identity/hash validation.
 for parent in p.parents:
  if parent==Path('/'):break
  w=parent.lstat();require(stat.S_ISDIR(w.st_mode) and not parent.is_symlink(),'real_parent_required')
 return p

def reference(path):return {'path':str(path),'sha256':sha(owned(path))}
def readref(ref):
 require(type(ref) is dict and set(ref)=={'path','sha256'},'exact_reference_fields_required')
 p=owned(ref['path']);require(sha(p)==ref['sha256'],'reference_hash_changed:'+str(p));return json.loads(p.read_bytes())
def fresh(value,now,reason):
 try:
  instant=datetime.datetime.fromisoformat(value);require(instant.utcoffset() is not None,'timezone_required')
  age=now-instant.timestamp();require(0<=age<=300,reason)
 except (ValueError,TypeError,OverflowError) as e:raise InvalidBinding(reason) from e


ORIGIN_POLICY={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/ROOT-207-PUBLIC-ORIGIN-POLICY.json', 'sha256': 'f8d29ef77b72a0de92010b8b013c88a662a5a6c9f3663312209d6382750bc548'}
PROJECT_SOURCE_PROOF={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112/ROOT-207-PROJECT-SOURCE.json', 'sha256': '1b83332bd3e0c44aebffd0114fe6bdc3d87ee8894dae4c90cdce1fd2584a8ba5'}
ORIGINAL206_INPUT={'path':str(S206/'INPUT-SOURCE206.json'),'sha256':PREVIOUS_INPUT}
def origin_git(repository, *args, input=None):
 import subprocess
 # Never use replacement objects, optional index writes or a network operation here.
 env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
 return subprocess.run(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
                        '-C',str(repository),*args], input=input,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       timeout=20,check=True,env=env).stdout

def git_oid(kind, raw):
 return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def origin_tree(repository, commit):
 raw=origin_git(repository,'ls-tree','-rz','--full-tree',commit)
 rows={}
 for record in raw.split(b'\0'):
  if not record:continue
  header,name=record.split(b'\t',1);mode,kind,oid=header.decode().split()
  name=name.decode('utf-8');require(name not in rows,'duplicate_git_path')
  rows[name]=(mode,kind,oid)
 return rows

def origin_blobs(repository, tree, expected, modes=None):
 names=sorted(expected)
 modes={name:'100644' for name in names} if modes is None else modes
 require(set(modes)==set(expected) and all(mode in ('100644','100755') for mode in modes.values()),'exact_regular_git_modes_required')
 require(all(name in tree and tree[name][:2]==(modes[name],'blob') for name in names),
         'exact_regular_published_blobs_required')
 oids=[tree[name][2] for name in names]
 raw=origin_git(repository,'cat-file','--batch',input=('\n'.join(oids)+'\n').encode())
 offset=0
 for name,oid in zip(names,oids):
  end=raw.index(b'\n',offset);header=raw[offset:end].decode().split();offset=end+1
  require(len(header)==3 and header[:2]==[oid,'blob'],'exact_git_blob_header_required')
  size=int(header[2]);body=raw[offset:offset+size];offset+=size
  require(raw[offset:offset+1]==b'\n' and len(body)==size,'complete_git_blob_required');offset+=1
  require(git_oid('blob',body)==oid,'git_blob_object_identity_changed')
  require(hashlib.sha256(body).hexdigest()==expected[name],'published_blob_changed:'+name)
 require(offset==len(raw),'unexpected_git_batch_tail')

def source_origin(expected_head, fresh_origin, *, repository=None, provenance_mode='published-remote'):
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

def validate_snapshot_origin(acceptance,snapshot):
 require(acceptance['source_provenance']=={'mode':snapshot['provenance_mode'],'commit':snapshot['head']},'accepted207_source_provenance_required')
 require(acceptance['public_main_sha']==snapshot['origin_main'],'accepted207_publication_observation_required')
 proof=source_origin(snapshot['head'],snapshot['origin_main'],provenance_mode=snapshot['provenance_mode'])
 require(snapshot['source_origin']==proof,'exact207_current_origin_proof_required')
 return proof

def validate_predecessor_record(record):
 require(record['schema']=='frw.root.actual206-predecessor.v1' and record['state']=='ROOT_RECONCILED_GENUINE_INSTALLED206_NOT_EXPECTATION' and record['template_only_no_execution_grant']is False,'genuine_actual206_record_required')
 historical=readref(reference(B/'ACTUAL206-HISTORICAL-METADATA.json'))
 require(all(record[k]==v for k,v in historical['references'].items()),'exact_completed206_refs_required')
 for stage in historical['stage_refs']:readref(stage)
 readref(historical['intent'])
 closure=readref(record['complete_closure'])
 require(closure['state']=='INSTALLED206_PROJECT493_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED' and closure['operation']==record['root_journal'] and closure['canonical_CP206']==record['request'] and closure['actors_and_boundary_closed']is True,'actual206_completed_closure_required')
 stage_receipt=readref(next(r for r in historical['stage_refs']if r['path'].endswith('/hermes-agent.source.json')))
 require(len(stage_receipt['layers'])==206 and len(stage_receipt['files'])==17891 and stage_receipt['source_file_count']==17730 and stage_receipt['layers']==historical['ordered206_layers'],'exact_completed206_ordered_prefix_required')
 chain=historical['chain199_206'];require([row['layers']for row in chain]==list(range(206,198,-1)) and chain[0]['request']==record['request'],'exact199_to206_chain_required')
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
 require(request['current_input']==ORIGINAL206_INPUT and committed['source_receipt_sha256']==BEFORE_RECEIPT and closure['installed']['canonical4']['current_input']==ORIGINAL206_INPUT,'actual206_input_receipt_join_required')
 journal=readref(record['root_journal']);require(journal['state']=='NATIVE206_PROJECT493_FRESH_PERMANENT_SERVICES_RUNNING' and journal['expected_receipt_sha256']==BEFORE_RECEIPT and journal['native_before_after']==[205,206],'actual206_Root_journal_required')
 require(journal['request']['sha256']==record['request']['sha256'] and readref(journal['request'])==request,'actual206_Root_canonical_request_join_required')
 require(journal['full_selected_native_files_readback'] and journal['fresh_default_spec_inspect'] and journal['user_db_wal_shm_verified_before_starts'] and journal['publisher_closed_before_parent_custody_release'],'actual206_fresh_consumer_and_closure_required')
 ret=readref(record['root_return']);require(ret['returncode']==0 and ret['boundary_pid_absent']is True,'actual206_boundary_closed_required')
 readref(ROOT198)
 return record['request']

def actual_predecessor():
 return validate_predecessor_record(readref(reference(B/'ROOT-ACTUAL206-PREDECESSOR.json')))

def validate_project_binding():
 # Root materialized this sourceproof, independently of future request/runtimeauthority.
 record=readref(PROJECT_SOURCE_PROOF)
 require(record['schema']=='friday.root.future207.project-source.v1'and record['state']=='ROOT_MATERIALIZED_PRIVATE495_PUBLIC5_CONNECTED_NOT_INSTALLED_NOT_GRANTED','exact_Root_materialized495_source_proof_required')
 require(record['runtime_grant']is False and record['actual_request_or_UUID_or_admission_created']is False and record['native207_installed']is False,'source_proof_not_runtime_grant')
 require(record['private_project']==str(C)and record['current_input']=={'path':str(S/'INPUT-SOURCE207.json'),'sha256':'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'}and record['previous_input']==ORIGINAL206_INPUT,'exact_actual_private495_domain_required')
 actual=readref(record['current_input']);previous=readref(record['previous_input']);policy=readref(ORIGIN_POLICY);prospective=readref(policy['prospective_private_input'])
 require(actual==prospective and {k:v for k,v in actual.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'},'actual207_must_derive_from_actual206_nonproject_fields')
 origins=readref(FIXED['project_origins'])['rows'];require(len(origins)==495 and {n:r['sha256']for n,r in origins.items()}==actual['project_files'],'full495_private_origins_required')
 for name,row in origins.items():require(reference(row['path'])=={k:row[k]for k in ('path','sha256')}and sha(owned(C/name))==row['sha256'],'actual_private495_source_drift:'+name)
 public=readref(policy['current_public_input']);counterpart=readref(FIXED['counterparts']);diff=sorted(n for n in actual['project_files']if actual['project_files'][n]!=public['project_files'][n])
 require(set(public['project_files'])==set(actual['project_files'])and len(diff)==counterpart['private_difference_count']==28 and diff==counterpart['private_difference_names']==record['private_public28'],'exact_private_public28_required')
 require(record['all495_origin_hashes_verified']is True and record['project_files']==495 and record['installed206_canonical4_unchanged']is True,'Root_materialization_checks_required')
 require({k:r['sha256']for k,r in record['public_source_changes'].items()}==policy['reviewed_current_files'],'Root_source_public5_exact_required')
 return record

def project_source_pins(request):
 validate_project_binding()
 previous=readref(request['previous_input']);current=readref(request['current_input'])
 require(request['previous_input']['sha256']==PREVIOUS_INPUT,'real_source206_input_required')
 require((len(previous['project_files']),len(current['project_files']))==(493,495),'project493_to495_required')
 for root,value in [(P,previous),(C,current)]:
  for name,digest in value['project_files'].items():require(sha(owned(root/name))==digest,'project_inventory_changed:'+name)
 require({k:v for k,v in previous.items()if k!='project_files'}=={k:v for k,v in current.items()if k!='project_files'},'actual206_nonproject_fields_unchanged_required')
 added=set(current['project_files'])-set(previous['project_files']);changed={n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'].get(n)}
 require(added=={'patches/hermes/f06-modern-odt-authenticated-profile-after-source206-manifest.json','patches/hermes/f06-modern-odt-authenticated-profile-after-source206.patch'} and changed=={'scripts/friday_ordinary_install.py'} and not set(previous['project_files'])-set(current['project_files']),'exact_helper_pair_delta_required')
 require(request['project_file_updates']==['scripts/friday_ordinary_install.py'],'exact_private_helper_update_required')
 require(request['plugin_set']==request['plugin_additions']==request['staged_files']==[],'no_plugin_or_worker_staging_required')
 require(request['project_inventory']==current['project_files'],'request_inventory_changed')
 require(request['project_inventory_sha256']==hashlib.sha256(encoded(current['project_files'])).hexdigest(),'inventory_digest_changed')
 require(request['current_input']==request['candidate_input'],'candidate_input_changed')
 return previous,current

def project_receipt(before,spec,current):
 result=copy.deepcopy(before)
 result['layers'].append({'manifest':spec['manifest_rel'],'manifest_sha256':spec['manifest']['sha256'],'patch_sha256':spec['patch']['sha256']})
 lock=current['sources_lock'];result['sources_lock_sha256']=lock['sha256'] if isinstance(lock,dict) else sha(lock)
 for row in spec['native_files']:
  value=dict(result['files'].get(row['path'],{}));value.update(sha256=row['sha256'],bytes=row['bytes'],mode='100644');result['files'][row['path']]=value
 return result

def validate_source_request(request):
 require(set(request)==set(('schema seconds home candidate_project layer_names marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request predecessor_current_input_sha256 predecessor_receipt_sha256 target_receipt candidate_input project_inventory project_inventory_sha256 plugin_set plugin_additions project_file_updates staged_files layer_manifest_updates installed_layers installed_files transaction_history current_source_successor').split()),'exact_builder_fields_no_test_injection_required')
 canonical={'marker':H/'FRIDAY-INSTALL.json','source_receipt':H/'hermes-agent.source.json','target_receipt':H/'hermes-agent.source.json','stamp':H/'hermes-agent/install-stamp.json','configuration':H/'config.yaml','profile':H/'FRIDAY-PROFILE.json','launcher':H/'hermes-agent/.hermes/bin/hermes','native_unit':Path('/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service'),'previous_input':S206/'INPUT-SOURCE206.json','current_input':S/'INPUT-SOURCE207.json','candidate_input':S/'INPUT-SOURCE207.json','predecessor_request':H/'preparation/ordinary-source-update-successor-afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00/request.json'}
 require(all(request[key]['path']==str(path) for key,path in canonical.items()),'canonical_request_paths_required')
 require(request['current_input']=={'path':str(S/'INPUT-SOURCE207.json'),'sha256':'c7a01f639606652f75db11418b5abd6e3a03b0babea09627570e39b0865ff838'},'exact_final207_input_required')
 require(request['previous_input']=={'path':str(S206/'INPUT-SOURCE206.json'),'sha256':PREVIOUS_INPUT},'exact_final207_input_required')
 require(request['target_receipt']==request['source_receipt'],'one_current_receipt_required')
 require(request['predecessor_request']['sha256']=='afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00' and request['predecessor_current_input_sha256']=='3948650d65fa78b48aa3bc838d4948815af2b75e4db5fffe29886c2707c7f93c' and request['predecessor_receipt_sha256']=='2c0eea5c2647172a0d059c2993c898b401c7d808bbcc85ee766d51aae7c0e51d','genuine_historical_root_predecessor_required')
 require(request['schema']=='friday.ordinary-telegram-source-update.v46','explicit_v46_required')
 require(request['home']==str(H) and request['candidate_project']==str(C),'exact_home_candidate_required')
 require(request['seconds']==600 and type(request['seconds']) is int,'forward600_required')
 require(request['layer_names']==[LAYER],'one_explicit_ninth_layer_required')
 require(request['installed_layers']==206 and request['installed_files']==17891,'true206_required')
 require(request['current_source_successor']=={'schema':'friday.current-source-native-successor.v9','root_project_update':ROOT198,'previous_native_update':actual_predecessor()},'genuine_root198_to206_chain_required')
 readref(ROOT198);readref(actual_predecessor())
 for key in ('marker','source_receipt','stamp','configuration','profile','launcher','native_unit','previous_input','current_input','predecessor_request','target_receipt','candidate_input'):
  # Some runtime pins (launcher/config/unit) are not JSON; only verify bytes/identity.
  ref=request[key];require(reference(ref['path'])==ref,'request_pin_changed:'+key)
 require(request['source_receipt']['sha256']==BEFORE_RECEIPT,'genuine_current206_receipt_required')
 previous,current=project_source_pins(request)
 spec=readref(FIXED['native_spec']);before=readref(request['source_receipt'])
 require((len(before['layers']),len(before['files']),before['source_file_count'])==(206,17891,17730),'real206_inventory_required')
 require(len(spec['native_files'])==1 and sum(row['new_file'] for row in spec['native_files'])==0,'one_existing_path_no_native_absent_required')
 require({row['path']for row in spec['native_files']}=={'tools/scoped_odf_password.py'},'exact_single_native_codec_path_required')
 require(request['layer_manifest_updates']==[spec['manifest_rel']],'only_new_pair_required')
 for row in spec['native_files']:
  path=H/'hermes-agent'/row['path']
  require(not os.path.lexists(path) if row['new_file'] else reference(path)['sha256']==row['before_sha256'],'native_preimage_changed:'+row['path'])
  require(sha(owned(MODERN207/'native-after'/row['path']))==row['sha256'],'native_afterimage_changed:'+row['path'])
 for role in ['manifest','patch']:require(reference(spec[role]['path'])=={k:spec[role][k] for k in ('path','sha256')},'pair_changed')
 projected=project_receipt(before,spec,current)
 require((len(projected['layers']),len(projected['files']))==(207,17891),'projection_count_wrong')
 expected=readref(FIXED['prospective_composition'])
 require(projected==expected['expected_inventory'] and hashlib.sha256(encoded(projected)).hexdigest()=='faf5d6ad698b7250b09545508352c120c0c8cdf653cecb9c37afeb2601c98a4b','exact207_projection_required')
 require(projected['layers'][:-1]==before['layers'],'exact206_prefix_required')
 native_paths={row['path'] for row in spec['native_files']}
 untouched={name:row for name,row in before['files'].items() if name not in native_paths}
 require(len(untouched)==17890 and {name:row for name,row in projected['files'].items() if name not in native_paths}==untouched,'all17890_untouched_native_rows_required')
 targets={str(H/'hermes-agent'/row['path']):{'before_sha256':row['before_sha256'],'after_sha256':row['sha256'],'native_new':row['new_file']} for row in spec['native_files']}
 for name in request['project_file_updates']+[spec['manifest_rel'],spec['patch_rel']]:
  path=H/name;targets[str(path)]={'before_sha256':previous['project_files'].get(name),'after_sha256':current['project_files'][name],'native_new':False}
 for key in ['marker','source_receipt','stamp']:targets[request[key]['path']]={'before_sha256':request[key]['sha256'],'metadata':True}
 require(len(targets)==7,'exact_seven_targets_required')
 for path,pin in targets.items():
  require(not os.path.lexists(path) if pin['before_sha256'] is None else reference(path)['sha256']==pin['before_sha256'],'selected_target_preimage_changed:'+path)
 return {'expected_receipt_sha256':hashlib.sha256(encoded(projected)).hexdigest(),'selected_target_count':7,'selected_targets':targets,'before_layers':206,'after_layers':207,'native_files_after':17891,'project_files_after':495,'current_input':request['current_input'],'previous_input':request['previous_input'],'native_spec':FIXED['native_spec']}

def validate_join(request,acceptance,snapshot,*,now,boot_id):
 for ref in FIXED.values():readref(ref)
 result=validate_source_request(request)
 reused=readref(reference(B/'REUSED-207-FINAL-SOURCE-EVIDENCE.json'))
 require(acceptance['final_source_result']==reused['final_source_result'] and acceptance['four_gate_evidence']==reused['four_gate_evidence'],'exact_unchanged_final207_four_gates_required')
 require(acceptance['modern_final_execution_review']in acceptance['independent_review_evidence'],'genuine_final_gate_independent_review_required')
 review=acceptance['modern_final_execution_review'];require(review==reused['final_execution_review'] and review!=reused['source_gateprep_review'] and review['path']=='/home/jericho/.cache/FRW-ASTRA-REVIEW-F06-MODERN207-ACTUAL-GATES-20261112/RESULT.json','separate_modern_final_execution_review_required');readref(review)
 readref(reused['root_final_execution_acceptance']);readref(reused['root_source_gate_authorization']);readref(reused['source_gateprep_review']);readref(reused['four_gate_summary'])
 require(acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json') and acceptance['frame_review_evidence'],'new_coherent_frame_review_required')
 for ref in acceptance['frame_review_evidence']:readref(ref)
 require(acceptance['schema']=='frw.root.native207-source-acceptance.v1' and acceptance['state']=='ROOT_ACCEPTED_EXACT207_SOURCE_OFFLINE_AND_RETAINED_RICH_REVIEW_NOT_RUNTIME','root_source_acceptance_required')
 require(acceptance['accepted'] is True and acceptance['execution_grant'] is False and acceptance['template_only_no_execution_grant'] is False,'source_acceptance_only')
 require(acceptance['source_pins']==FIXED,'exact_prepared_source_pins_required')
 require(acceptance['final_source_result']['sha256']!=FIXED['prepared_composition']['sha256'] and acceptance['final_source_result']!=FIXED['prepared_composition'],'prepared_M2_cannot_be_final_gate_result')
 require(len(acceptance['final_source_result']['sha256'])==64 and all(c in '0123456789abcdef' for c in acceptance['final_source_result']['sha256']),'bound_final_result_hash_required')
 readref(acceptance['final_source_result'])
 require(acceptance['all_four_current_source_gates_accepted'] is True and acceptance['gate_retry_history_preserved'] is True,'Root_final_four_gates_acceptance_required')
 require(tuple(row['label'] for row in acceptance['four_gate_evidence'])==FINAL_GATE_LABELS,'exact_four_gate_labels_required')
 for row in acceptance['four_gate_evidence']:readref(row['evidence'])
 for ref in acceptance['independent_review_evidence']+acceptance['newapp_review_evidence']:readref(ref)
 require(acceptance['independent_review_evidence'] and acceptance['newapp_review_evidence'],'actual_review_evidence_required')
 require(snapshot['schema']=='frw.root.native207-fresh-readback.v1' and snapshot['state']=='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT','fresh_root_readback_required')
 require(snapshot['template_only_no_execution_grant'] is False,'actual_readback_not_template_required')
 require(snapshot['boot_id']==boot_id,'current_boot_required');fresh(snapshot['observed_at_moscow'],now,'fresh_readback_required')
 require(all(snapshot['checks'][key] is True for key in SNAPSHOT_TRUE_FIELDS),'all_current_boundary_checks_required')
 origin_proof=validate_snapshot_origin(acceptance,snapshot)
 require(len(snapshot['head'])==40 and all(c in '0123456789abcdef' for c in snapshot['head']),'real_git_sha_required')
 require(snapshot['installed_receipt_sha256']==BEFORE_RECEIPT and snapshot['installed_input_sha256']==PREVIOUS_INPUT,'current_source206_pins_required')
 for service in ('gateway','dashboard'):
  identity=snapshot['services'][service];require(identity['boot_id']==boot_id and type(identity['pid']) is int and identity['pid']>0 and type(identity['birth_ticks']) is int and identity['birth_ticks']>0,'fresh_process_identity_required')
  require(len(identity['invocation_id'])==32 and identity['cgroup'].startswith('/user.slice/') and identity['enabled_active'] is True and identity['runtime_max']=='infinity','healthy_permanent_service_required')
 require(snapshot['evidence'],'fresh_actual_readback_evidence_required')
 for ref in snapshot['evidence']:readref(ref)
 require(snapshot['remaining_limits']=={'native_canonical_unknown':3,'structural_unresolved':45,'R104_semantic_fail':True,'default_workers_ready_accepted':False,'DSH_A0_deferred':True},'known_limits_must_remain')
 result.update(source_origin=origin_proof,genuine_actual206_predecessor=actual_predecessor(),fresh_root_services=copy.deepcopy(snapshot['services']),state='PURE_METADATA_BOUND_NOT_ADMISSION',source_acceptance={'path':str(B/'ROOT-207-SOURCE-ACCEPTANCE.json'),'sha256':hashlib.sha256(encoded(acceptance)).hexdigest()},snapshot_boot_id=boot_id,operation_seconds=1800,forward_seconds=600,external_rollback_seconds=180,publisher_terminal_cleanup_seconds=30,publisher_unit_seconds=810,publisher_client_seconds=840)
 return result

def validate_profile_join(qualification,before,spec):
 require(qualification['schema']=='frw.root.native207-minimum-installed-bank-profile-qualification.v1','profile207_schema_required')
 join=readref(qualification['profile_equivalence_join'])
 require(qualification['profile_equivalence_join']=={'path': '/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112/PROFILE-SOURCE-JOIN.json', 'sha256': '9d1c1e6fdaadc68f07eba2425007071cc14bae4c80af203f9b37d54587e53746'},'exact_reviewed_unchanged_profile_join_required')
 old={name:before['files'][name]['sha256']for name in ('hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py')}
 require(not set(old)&{row['path']for row in spec['native_files']},'F06_must_not_change_bank_profile_files')
 require(join['state']=='SOURCE_ONLY_EXACT206_PROFILE_UNCHANGED_IN207_NO_NEW_APP_CREDIT' and join['before_profile_source_digests']==join['after_profile_source_digests']==old and qualification['before_profile_source_digests']==qualification['minimum_profile_source_digests']==old,'exact206_unchanged207_profile_required')
 require(join['changed_profile_definitions']==[] and join['new_Office_effects']==0 and join['saved_app_evidence_reused']is True,'no_new_Office_credit')
 for source in join['evidence']:readref(source)
 require(qualification['format_layout_ready']is False and qualification['formal_test_credit']is False,'no_new_layout_formal_credit')
 return old

def load_actor_binding(bundle):
 require(Path(bundle).resolve()==B,'exact_bundle_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-207-SOURCE-ACCEPTANCE.json'))
 snapshot=readref(reference(B/'ROOT-207-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 saved=readref(reference(B/'ROOT-207-BOUND-INPUTS.json'))
 require(saved['binding']==value,'bound_input_join_changed')
 for key in ['request','source_acceptance','fresh_readback']:
  name={'request':'ROOT-FRESH-REQUEST.json','source_acceptance':'ROOT-207-SOURCE-ACCEPTANCE.json','fresh_readback':'ROOT-207-FRESH-READBACK.json'}[key]
  require(saved[key]==reference(B/name),'saved_input_ref_changed')
 return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--validate-and-bind',action='store_true',required=True);args=p.parse_args()
 require(__debug__ and sys_flags_safe(),'isolated_nonoptimized_no_bytecode_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-207-SOURCE-ACCEPTANCE.json'));snapshot=readref(reference(B/'ROOT-207-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 payload={'binding':value,**{key:reference(B/name) for key,name in [('request','ROOT-FRESH-REQUEST.json'),('source_acceptance','ROOT-207-SOURCE-ACCEPTANCE.json'),('fresh_readback','ROOT-207-FRESH-READBACK.json')]}}
 destination=B/'ROOT-207-BOUND-INPUTS.json';fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(encoded(payload));stream.flush();os.fsync(stream.fileno())
 print(json.dumps({'state':value['state'],'bound_inputs':reference(destination),'execution_grant':False}))
def sys_flags_safe():
 import sys
 return bool(sys.flags.isolated and sys.dont_write_bytecode)
if __name__=='__main__':main()
