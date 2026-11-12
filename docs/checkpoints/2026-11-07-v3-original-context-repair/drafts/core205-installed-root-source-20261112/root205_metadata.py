"""Pure metadata join for a later Root boundary; no collector, product import or grant.
Only CLI --validate-and-bind writes an exclusive own-bundle metadata record. It cannot
produce request/admission/qualification/source acceptance or call any live consumer.
Root supplies authentic readbacks; validation is not a kernel/runtime proof.
"""
from pathlib import Path
import argparse,copy,datetime,hashlib,json,os,stat,time
B=Path(__file__).resolve().parent
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
S=Path('/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2')
S204=Path('/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111')
P=Path('/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111/project489')
C=S/'project491'
LAYER='core-user-result-contracts-after-source204'
BEFORE_RECEIPT='94aea3888c0c89b99022cda3259b7e947d063d91d8525ddbff5bd4df3ac98d6a'
PREVIOUS_INPUT='cb35f5a9cdac806d95e51c70038944a29f4d1abf28ee74caaf2e9593d79d6677'
ROOT198={'path':'/home/jericho/.cache/FRW-ASTRA-V3-DSH-COHERENT-ROOT-COMPOSITION-20261111/final-v1/fresh-source-request/REQUEST.json','sha256':'886c6ab5bc76a810b24004f7042ef7c1b5add1b78f04781fac9c96335e3bd448'}
# Prepared source evidence only: none of these pins is a final gate/result grant.
FIXED={'prepared_composition': {'path': '/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111/sol-task17-M2-COHERENT-SOURCE-IMMUTABLE.json', 'sha256': 'e48894c7934efcc7059d23315a94225a661f647516b00ba3807dc6524db210f6'}, 'native_spec': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/FINAL-NATIVE-SPEC.json', 'sha256': 'fd34937bb9bb31a3455d383f13755a2e9cf7d33daf18173d67fa87981aa0b22b'}, 'source_freeze': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/SOURCE-FREEZE-FINAL.json', 'sha256': 'afde86079fae5f2e14e60ecc27aec4d20e2ae4f3d119427f88ab75080ed856c3'}, 'prepared_root_recipe': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/ROOT-INTEGRATION-RECIPE-PREPARED.json', 'sha256': '9d4b148fccf04c0079b969e6de97b811a70f15b24153395dca8cdfebff364a8d'}, 'pm_environment_basis': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE204-RTF-READER-COMPOSITION-20261111/READONLY-PM-ENVIRONMENT-BASIS.json', 'sha256': '2ab5df26d6bd153ccc175e5813ad0fd769be377611b653fee486e3c3fab2062e'}, 'counterparts': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2/COUNTERPART-INVARIANTS.json', 'sha256': 'dd6d2643352a263a183585b8a38f54cf430abef19eb67fa105d635b9e8250130'}, 'architecture_review': {'path': '/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/composition-review/final-coherent/RESULT.json', 'sha256': '12cb3900965fc758764fff243e5f95c3f7199ac17c5e0947d15dc4517822bd58'}}
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


ROOT204_ORIGIN_METADATA={'path':'/home/jericho/.cache/FRW-ASTRA-V3-CORE204-ROOT-MAINTENANCE-FRAME-20261111/root204_metadata.py','sha256':'c0c874096157de646cd50dea889dc8ae58616b35b5bcf6451b1c7fcc8bad9487'}
def source_origin(expected_head, fresh_origin, *, repository=None, provenance_mode='published-remote'):
 import importlib.util
 path=owned(ROOT204_ORIGIN_METADATA['path'])
 require(reference(path)==ROOT204_ORIGIN_METADATA,'exact204_origin_metadata_required')
 spec=importlib.util.spec_from_file_location('root204_origin_for205',path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module.source_origin(expected_head,fresh_origin,repository=repository,provenance_mode=provenance_mode)

def validate_snapshot_origin(acceptance,snapshot):
 require(acceptance['source_provenance']=={'mode':snapshot['provenance_mode'],'commit':snapshot['head']},'accepted205_source_provenance_required')
 require(acceptance['public_main_sha']==snapshot['origin_main'],'accepted205_publication_observation_required')
 proof=source_origin(snapshot['head'],snapshot['origin_main'],provenance_mode=snapshot['provenance_mode'])
 require(snapshot['source_origin']==proof,'exact205_current_origin_proof_required')
 return proof

def actual_predecessor():
 record=readref(reference(B/'ROOT-ACTUAL204-PREDECESSOR.json'))
 require(record['schema']=='frw.root.actual204-predecessor.v1' and record['state']=='ROOT_RECONCILED_GENUINE_INSTALLED204_NOT_EXPECTATION' and record['template_only_no_execution_grant'] is False,'genuine_actual204_record_required')
 historical=readref(reference(B/'ACTUAL204-HISTORICAL-METADATA.json'))
 for stage in historical['stage_refs']:readref(stage)
 readref(historical['intent'])
 stage_receipt=readref(next(r for r in historical['stage_refs'] if r['path'].endswith('/hermes-agent.source.json')))
 require(len(stage_receipt['layers'])==204 and len(stage_receipt['files'])==17891 and stage_receipt['source_file_count']==17730 and stage_receipt['layers'][-1]=={'manifest':'patches/hermes/rtf-optional-footnote-reader-after-source203-manifest.json','manifest_sha256':'0cef90c50fa23afe9c73ad880680f5b74956126b4b6f79affdaa6dee4234581d','patch_sha256':'8eeff0c650b66c5e32833ecca6c688616305d8add3feffbf00eb9f1d2f9e0027'},'complete_actual204_stage_prefix_required')
 expected=historical['references']
 require(all(record[k]==v for k,v in expected.items()),'exact_genuine_completed204_refs_required')
 closure=readref(record['complete_closure'])
 require(closure['state']=='INSTALLED204_PROJECT489_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED' and closure['operation']==record['root_journal'] and closure['canonical_CP204']==record['request'] and closure['actors_and_boundary_closed'] is True,'actual204_completed_closure_required')
 ref=record['request'];request=readref(ref)
 tx=H/'preparation'/('ordinary-source-update-v45-'+ref['sha256'][:16])
 require(ref['path']==str(tx/'request.json') and record['committed']['path']==str(tx/'committed.json'),'canonical_CP204_required')
 committed=readref(record['committed'])
 require(committed['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED' and committed['request_sha256']==ref['sha256'] and committed['source_receipt_sha256']==BEFORE_RECEIPT and committed['gateway_started'] is False and committed['workers_enabled'] is False,'genuine_committed_CP204_required')
 require(request['home']==str(H) and request['schema']=='friday.ordinary-telegram-source-update.v46' and request['installed_layers']==203 and request['layer_names']==['rtf-optional-footnote-reader-after-source203'],'exact_203_to204_CP_required')
 require(request['current_input']=={'path':str(S204/'INPUT-SOURCE204.json'),'sha256':PREVIOUS_INPUT} and committed['current_input']==request['current_input'],'genuine_CP204_input_required')
 require(committed['current_source_successor']==request['current_source_successor'] and committed['request_reference']==ref and committed['files']==['tools/scoped_rtf.py'] and committed['layers']==['patches/hermes/rtf-optional-footnote-reader-after-source203-manifest.json'],'exact_complete_CP204_committed_prefix_required')
 require(not os.path.lexists(tx/'rolled-back.json') and (tx/'intent.json').is_file(),'genuine_committed_stage_not_rollback_required')
 require(request['current_source_successor']['schema']=='friday.current-source-native-successor.v6' and request['current_source_successor']['root_project_update']==ROOT198,'CP204_ancestry_required')
 journal_ref=record['root_journal']
 require(journal_ref['path']=='/home/jericho/.cache/FRW-ASTRA-V3-CORE204-FUTURE-FRAME-R2-20261112/ROOT-NATIVE204-LIVE-OPERATION.json','actual204_Root_journal_path_required')
 journal=readref(journal_ref)
 require(journal['state']=='NATIVE204_PROJECT489_FRESH_PERMANENT_SERVICES_RUNNING' and journal['expected_receipt_sha256']==BEFORE_RECEIPT and journal['native_before_after']==[203,204],'actual204_Root_journal_required')
 require(journal['request']['path']=='/home/jericho/.cache/FRW-ASTRA-V3-CORE204-FUTURE-FRAME-R2-20261112/ROOT-FRESH-REQUEST.json' and journal['request']['sha256']==ref['sha256'],'actual204_Root_source_request_path_and_hash_required')
 require(readref(journal['request'])==request,'actual204_Root_and_canonical_request_bytes_required')
 require(journal['full_selected_native_files_readback'] and journal['fresh_default_spec_inspect'] and journal['user_db_wal_shm_verified_before_starts'] and journal['publisher_closed_before_parent_custody_release'],'actual204_fresh_consumer_and_closure_required')
 return ref

def project_source_pins(request):
 previous=readref(request['previous_input']);current=readref(request['current_input'])
 require(request['previous_input']['sha256']==PREVIOUS_INPUT,'real_source204_input_required')
 require((len(previous['project_files']),len(current['project_files']))==(489,491),'project489_to491_required')
 for root,value in [(P,previous),(C,current)]:
  for name,digest in value['project_files'].items():require(sha(owned(root/name))==digest,'project_inventory_changed:'+name)
 expected={str(C/'scripts/friday_ordinary_install.py'):current['project_files']['scripts/friday_ordinary_install.py']}
 require(request['project_file_updates']==['scripts/friday_ordinary_install.py'],'exact_private_helper_update_required')
 require(request['plugin_set']==request['plugin_additions']==request['staged_files']==[],'no_plugin_or_worker_staging_required')
 require(request['project_inventory']==current['project_files'],'request_inventory_changed')
 require(request['project_inventory_sha256']==hashlib.sha256(encoded(current['project_files'])).hexdigest(),'inventory_digest_changed')
 require(request['current_input']==request['candidate_input'],'candidate_input_changed')
 return previous,current

def project_receipt(before,spec,current):
 result=copy.deepcopy(before)
 result['layers'].append({'manifest':spec['manifest_rel'],'manifest_sha256':spec['manifest_sha256'],'patch_sha256':spec['patch_sha256']})
 lock=current['sources_lock'];result['sources_lock_sha256']=lock['sha256'] if isinstance(lock,dict) else sha(lock)
 for row in spec['native_files']:
  value=dict(result['files'].get(row['path'],{}));value.update(sha256=row['sha256'],bytes=row['bytes'],mode='100644');result['files'][row['path']]=value
 return result

def validate_source_request(request):
 require(set(request)==set(('schema seconds home candidate_project layer_names marker source_receipt stamp configuration profile launcher native_unit previous_input current_input predecessor_request predecessor_current_input_sha256 predecessor_receipt_sha256 target_receipt candidate_input project_inventory project_inventory_sha256 plugin_set plugin_additions project_file_updates staged_files layer_manifest_updates installed_layers installed_files transaction_history current_source_successor').split()),'exact_builder_fields_no_test_injection_required')
 canonical={'marker':H/'FRIDAY-INSTALL.json','source_receipt':H/'hermes-agent.source.json','target_receipt':H/'hermes-agent.source.json','stamp':H/'hermes-agent/install-stamp.json','configuration':H/'config.yaml','profile':H/'FRIDAY-PROFILE.json','launcher':H/'hermes-agent/.hermes/bin/hermes','native_unit':Path('/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service'),'previous_input':S204/'INPUT-SOURCE204.json','current_input':S/'INPUT-SOURCE205.json','candidate_input':S/'INPUT-SOURCE205.json','predecessor_request':H/'preparation/ordinary-source-update-successor-afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00/request.json'}
 require(all(request[key]['path']==str(path) for key,path in canonical.items()),'canonical_request_paths_required')
 require(request['current_input']=={'path':str(S/'INPUT-SOURCE205.json'),'sha256':'2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9'},'exact_final205_input_required')
 require(request['previous_input']=={'path':str(S204/'INPUT-SOURCE204.json'),'sha256':PREVIOUS_INPUT},'exact_final205_input_required')
 require(request['target_receipt']==request['source_receipt'],'one_current_receipt_required')
 require(request['predecessor_request']['sha256']=='afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00' and request['predecessor_current_input_sha256']=='3948650d65fa78b48aa3bc838d4948815af2b75e4db5fffe29886c2707c7f93c' and request['predecessor_receipt_sha256']=='2c0eea5c2647172a0d059c2993c898b401c7d808bbcc85ee766d51aae7c0e51d','genuine_historical_root_predecessor_required')
 require(request['schema']=='friday.ordinary-telegram-source-update.v46','explicit_v46_required')
 require(request['home']==str(H) and request['candidate_project']==str(C),'exact_home_candidate_required')
 require(request['seconds']==600 and type(request['seconds']) is int,'forward600_required')
 require(request['layer_names']==[LAYER],'one_explicit_seventh_layer_required')
 require(request['installed_layers']==204 and request['installed_files']==17891,'true204_required')
 require(request['current_source_successor']=={'schema':'friday.current-source-native-successor.v7','root_project_update':ROOT198,'previous_native_update':actual_predecessor()},'genuine_root198_to204_chain_required')
 readref(ROOT198);readref(actual_predecessor())
 for key in ('marker','source_receipt','stamp','configuration','profile','launcher','native_unit','previous_input','current_input','predecessor_request','target_receipt','candidate_input'):
  # Some runtime pins (launcher/config/unit) are not JSON; only verify bytes/identity.
  ref=request[key];require(reference(ref['path'])==ref,'request_pin_changed:'+key)
 require(request['source_receipt']['sha256']==BEFORE_RECEIPT,'genuine_current204_receipt_required')
 previous,current=project_source_pins(request)
 spec=readref(FIXED['native_spec']);before=readref(request['source_receipt'])
 require((len(before['layers']),len(before['files']),before['source_file_count'])==(204,17891,17730),'real204_inventory_required')
 require(len(spec['native_files'])==4 and sum(row['new_file'] for row in spec['native_files'])==0,'four_paths_no_native_absent_required')
 require({row['path'] for row in spec['native_files']}=={'gateway/run_attachment_presentation.py','hermes_cli/friday_prompt_scope.py','hermes_cli/friday_workspace_presentation.py','tools/session_search_tool.py'},'exact_four_native_paths_required')
 require(request['layer_manifest_updates']==[spec['manifest_rel']],'only_new_pair_required')
 for row in spec['native_files']:
  path=H/'hermes-agent'/row['path']
  require(not os.path.lexists(path) if row['new_file'] else reference(path)['sha256']==row['before_sha256'],'native_preimage_changed:'+row['path'])
  require(sha(owned(Path(spec['native_source_directory'])/row['path']))==row['sha256'],'native_afterimage_changed:'+row['path'])
 for role in ['manifest','patch']:require(reference(spec[role]['path'])=={k:spec[role][k] for k in ('path','sha256')},'pair_changed')
 projected=project_receipt(before,spec,current)
 require((len(projected['layers']),len(projected['files']))==(205,17891),'projection_count_wrong')
 proposed=spec['private_proposed_receipt'];require(sha(proposed['path'])==proposed['sha256'],'proposed_receipt_changed')
 require(hashlib.sha256(encoded(projected)).hexdigest()==proposed['sha256'],'exact205_projection_required')
 require(projected['layers'][:-1]==before['layers'],'exact204_prefix_required')
 native_paths={row['path'] for row in spec['native_files']}
 untouched={name:row for name,row in before['files'].items() if name not in native_paths}
 require(len(untouched)==17887 and {name:row for name,row in projected['files'].items() if name not in native_paths}==untouched,'all17887_untouched_native_rows_required')
 targets={str(H/'hermes-agent'/row['path']):{'before_sha256':row['before_sha256'],'after_sha256':row['sha256'],'native_new':row['new_file']} for row in spec['native_files']}
 for name in request['project_file_updates']+[spec['manifest_rel'],spec['patch_rel']]:
  path=H/name;targets[str(path)]={'before_sha256':previous['project_files'].get(name),'after_sha256':current['project_files'][name],'native_new':False}
 for key in ['marker','source_receipt','stamp']:targets[request[key]['path']]={'before_sha256':request[key]['sha256'],'metadata':True}
 require(len(targets)==10,'exact_ten_targets_required')
 for path,pin in targets.items():
  require(not os.path.lexists(path) if pin['before_sha256'] is None else reference(path)['sha256']==pin['before_sha256'],'selected_target_preimage_changed:'+path)
 return {'expected_receipt_sha256':hashlib.sha256(encoded(projected)).hexdigest(),'selected_target_count':10,'selected_targets':targets,'before_layers':204,'after_layers':205,'native_files_after':17891,'project_files_after':491,'current_input':request['current_input'],'previous_input':request['previous_input'],'native_spec':FIXED['native_spec']}

def validate_join(request,acceptance,snapshot,*,now,boot_id):
 for ref in FIXED.values():readref(ref)
 result=validate_source_request(request)
 reused=readref(reference(B/'REUSED-205-FINAL-SOURCE-EVIDENCE.json'))
 require(acceptance['final_source_result']==reused['final_source_result'] and acceptance['four_gate_evidence']==reused['four_gate_evidence'],'exact_unchanged_final205_four_gates_required')
 require(reused['independent_review'] in acceptance['independent_review_evidence'],'genuine_final_gate_independent_review_required')
 readref(reused['root_acceptance']);readref(reused['independent_review'])
 require(acceptance['frame_source_manifest']==reference(B/'SOURCE-PINS.json') and acceptance['frame_review_evidence'],'new_coherent_frame_review_required')
 for ref in acceptance['frame_review_evidence']:readref(ref)
 require(acceptance['schema']=='frw.root.native205-source-acceptance.v1' and acceptance['state']=='ROOT_ACCEPTED_EXACT205_SOURCE_OFFLINE_AND_RETAINED_RICH_REVIEW_NOT_RUNTIME','root_source_acceptance_required')
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
 require(snapshot['schema']=='frw.root.native205-fresh-readback.v1' and snapshot['state']=='ROOT_CURRENT_READBACK_NOT_EXECUTION_GRANT','fresh_root_readback_required')
 require(snapshot['template_only_no_execution_grant'] is False,'actual_readback_not_template_required')
 require(snapshot['boot_id']==boot_id,'current_boot_required');fresh(snapshot['observed_at_moscow'],now,'fresh_readback_required')
 require(all(snapshot['checks'][key] is True for key in SNAPSHOT_TRUE_FIELDS),'all_current_boundary_checks_required')
 origin_proof=validate_snapshot_origin(acceptance,snapshot)
 require(len(snapshot['head'])==40 and all(c in '0123456789abcdef' for c in snapshot['head']),'real_git_sha_required')
 require(snapshot['installed_receipt_sha256']==BEFORE_RECEIPT and snapshot['installed_input_sha256']==PREVIOUS_INPUT,'current_source204_pins_required')
 for service in ('gateway','dashboard'):
  identity=snapshot['services'][service];require(identity['boot_id']==boot_id and type(identity['pid']) is int and identity['pid']>0 and type(identity['birth_ticks']) is int and identity['birth_ticks']>0,'fresh_process_identity_required')
  require(len(identity['invocation_id'])==32 and identity['cgroup'].startswith('/user.slice/') and identity['enabled_active'] is True and identity['runtime_max']=='infinity','healthy_permanent_service_required')
 require(snapshot['evidence'],'fresh_actual_readback_evidence_required')
 for ref in snapshot['evidence']:readref(ref)
 require(snapshot['remaining_limits']=={'native_canonical_unknown':3,'structural_unresolved':45,'R104_semantic_fail':True,'default_workers_ready_accepted':False,'DSH_A0_deferred':True},'known_limits_must_remain')
 result.update(source_origin=origin_proof,genuine_actual204_predecessor=actual_predecessor(),fresh_root_services=copy.deepcopy(snapshot['services']),state='PURE_METADATA_BOUND_NOT_ADMISSION',source_acceptance={'path':str(B/'ROOT-205-SOURCE-ACCEPTANCE.json'),'sha256':hashlib.sha256(encoded(acceptance)).hexdigest()},snapshot_boot_id=boot_id,operation_seconds=1800,forward_seconds=600,external_rollback_seconds=180,publisher_terminal_cleanup_seconds=30,publisher_unit_seconds=810,publisher_client_seconds=840)
 return result

def validate_profile_join(qualification,before,spec):
 require(qualification['schema']=='frw.root.native205-minimum-installed-bank-profile-qualification.v1','profile205_schema_required')
 old={'hermes_cli/friday_workspace_pdf.py':before['files']['hermes_cli/friday_workspace_pdf.py']['sha256'],'hermes_cli/friday_workspace_presentation.py':before['files']['hermes_cli/friday_workspace_presentation.py']['sha256']}
 after=dict(old);after['hermes_cli/friday_workspace_presentation.py']=next(r['sha256'] for r in spec['native_files'] if r['path']=='hermes_cli/friday_workspace_presentation.py')
 require(qualification['before_profile_source_digests']==old and qualification['minimum_profile_source_digests']==after,'exact_old_new_profile_join_required')
 join=readref(qualification['profile_equivalence_join'])
 require(qualification['profile_equivalence_join']=={'path': '/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112/PROFILE-SOURCE-JOIN.json', 'sha256': '35326bc96e54aa1d0ca9f828d77c64c0a7ab06be2ca3393006216428cfb4adbd'},'exact_reviewed_profile_join_required')
 require(join['state']=='SOURCE_ONLY_METADATA_EQUIVALENCE_ACCEPTED_NO_NEW_APP_CREDIT' and join['old_presentation_sha256']==old['hermes_cli/friday_workspace_presentation.py'] and join['new_presentation_sha256']==after['hermes_cli/friday_workspace_presentation.py'],'profile_equivalence_required')
 require(join['changed_definitions']==['_publish'] and join['new_Office_effects']==0 and join['saved_app_evidence_reused'] is True,'metadata_only_saved_app_join_required')
 for source in join['evidence']:readref(source)
 require(qualification['format_layout_ready'] is False and qualification['formal_test_credit'] is False,'no_new_layout_formal_credit')
 return after

def load_actor_binding(bundle):
 require(Path(bundle).resolve()==B,'exact_bundle_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-205-SOURCE-ACCEPTANCE.json'))
 snapshot=readref(reference(B/'ROOT-205-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 saved=readref(reference(B/'ROOT-205-BOUND-INPUTS.json'))
 require(saved['binding']==value,'bound_input_join_changed')
 for key in ['request','source_acceptance','fresh_readback']:
  name={'request':'ROOT-FRESH-REQUEST.json','source_acceptance':'ROOT-205-SOURCE-ACCEPTANCE.json','fresh_readback':'ROOT-205-FRESH-READBACK.json'}[key]
  require(saved[key]==reference(B/name),'saved_input_ref_changed')
 return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--validate-and-bind',action='store_true',required=True);args=p.parse_args()
 require(__debug__ and sys_flags_safe(),'isolated_nonoptimized_no_bytecode_required')
 request=readref(reference(B/'ROOT-FRESH-REQUEST.json'));acceptance=readref(reference(B/'ROOT-205-SOURCE-ACCEPTANCE.json'));snapshot=readref(reference(B/'ROOT-205-FRESH-READBACK.json'))
 value=validate_join(request,acceptance,snapshot,now=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 payload={'binding':value,**{key:reference(B/name) for key,name in [('request','ROOT-FRESH-REQUEST.json'),('source_acceptance','ROOT-205-SOURCE-ACCEPTANCE.json'),('fresh_readback','ROOT-205-FRESH-READBACK.json')]}}
 destination=B/'ROOT-205-BOUND-INPUTS.json';fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(encoded(payload));stream.flush();os.fsync(stream.fileno())
 print(json.dumps({'state':value['state'],'bound_inputs':reference(destination),'execution_grant':False}))
def sys_flags_safe():
 import sys
 return bool(sys.flags.isolated and sys.dont_write_bytecode)
if __name__=='__main__':main()
