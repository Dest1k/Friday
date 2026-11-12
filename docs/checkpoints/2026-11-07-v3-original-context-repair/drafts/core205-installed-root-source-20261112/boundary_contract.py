"""Pure changed-scope205 contracts; cannot authenticate observations or grant runtime."""
import datetime,math
class InvalidBoundary(ValueError):pass
def require(value,reason):
 if not value:raise InvalidBoundary(reason)
def digest(value,length=64):return type(value)is str and len(value)==length and all(c in '0123456789abcdef' for c in value)
def fresh(value,current_time):
 try:
  stamp=datetime.datetime.fromisoformat(value);require(stamp.utcoffset()is not None,'anchor_timezone_required')
  require(0<=current_time-stamp.timestamp()<=300,'anchor_stale_or_future')
 except (TypeError,ValueError,OverflowError)as e:raise InvalidBoundary('anchor_stale_or_future')from e
def reference(value):
 require(type(value)is dict and set(value)=={'path','sha256'} and value['path'].startswith('/') and 'UNBOUND'not in value['path'] and not value['path'].endswith('-TEMPLATE.json') and digest(value['sha256']),'actual_exact_reference_required')
def validate_authority(value,*,manifest,boundary,caller,anchor,source_acceptance,predecessor,frame):
 require(value['schema']=='frw.root.native205-reviewed-future-boundary.v1' and value['state']=='ROOT_REVIEWED_EXACT205_FUTURE_EXECUTION' and value['template_only_no_execution_grant']is False,'authentic_Root205_authority_required')
 for key,ref in dict(source_pin_manifest=manifest,boundary=boundary,caller=caller,current_service_anchor=anchor,source_acceptance=source_acceptance,actual204_predecessor=predecessor).items():
  reference(ref);require(value[key]==ref,'exact_authority_ref_required:'+key)
 require(value['frame']==frame and digest(value['execution_commit'],40),'exact205_domain_current_commit_required')
 require(value['origin_url']in ('https://github.com/Dest1k/Friday','https://github.com/Dest1k/Friday.git'),'effective_origin_required')
 mode=value['provenance_mode'];require(mode in ('local-committed-main','published-remote'),'explicit_provenance_mode_required')
 require(value['public_main_sha']is None if mode=='local-committed-main' else value['public_main_sha']==value['execution_commit'],'explicit_publication_mode_required')
 require(value['future_finite_operation_reviewed']is True and value['original_future205_budgets']==dict(actor=1800,source=600,publisher_unit=810,publisher_client=840,cold_each=180,postcheck=90,reserve=75),'Root_exact_future_finite_budgets_required')
 require(value['old_effects_clocks_preserved']is True and value['Task23_future206_not_integrated']is True,'no_effect_replay_or_layer_skip_required')
 slot=value['shared_slot_identity'];require(type(slot)is list and len(slot)==5 and all(type(x)is int for x in slot)and slot[0]>0 and slot[1]>0 and slot[3:]==[1,384],'exact_shared_slot_identity_required')
def validate_anchor(value,*,current_time,boot,historical,frame,publisher,home):
 require(value['schema']=='frw.root205.current-service-anchor.v1'and value['state']=='ROOT_ACTUAL_CURRENT204_BOUNDARY'and value['template_only_no_execution_grant']is False,'authentic_current204_anchor_required')
 fresh(value['observed_at_moscow'],current_time)
 require(value['boot_id']==boot and type(boot)is str and len(boot)==36,'current_boot_required')
 require(value['historical_refs']==historical and value['frame']==frame and value['future_publisher_unit']==publisher and value['home']==home,'exact_anchor_domain_required')
 require(value['installed']==dict(layers=204,project=489,nativefiles=17891,plugins=52,base_source_file_count=17730,receipt_sha256='94aea3888c0c89b99022cda3259b7e947d063d91d8525ddbff5bd4df3ac98d6a',input_sha256='cb35f5a9cdac806d95e51c70038944a29f4d1abf28ee74caaf2e9593d79d6677'),'genuine_current204_required')
 expected=('current_all_profile_owned_work_quiescent','current_cancel_stop_cooldown_clear','current_no_maintenance','current_resources_sufficient','old_effects_clocks_preserved','actual204_operation_closed')
 require(set(value['checks'])==set(expected)and all(value['checks'][k]is True for k in expected),'all_current_anchor_checks_required')
 require(value['evidence'],'fresh_anchor_evidence_required')
 for ref in value['evidence']:
  reference(ref);require(ref['path']not in historical,'historical_ref_is_not_current_evidence')
 require(set(value['services'])==set(value['process_environment'])=={'gateway','dashboard'},'both_current_services_required')
 for name,row in value['services'].items():
  require(set(row)=={'pid','birth_ticks','boot_id','invocation_id','cgroup','enabled_active','runtime_max'},'exact_service_fields_required')
  require(type(row['pid'])is int and row['pid']>0 and type(row['birth_ticks'])is int and row['birth_ticks']>0 and row['boot_id']==boot and digest(row['invocation_id'],32)and row['cgroup'].startswith('/user.slice/')and row['enabled_active']is True and row['runtime_max']=='infinity','current_kernel_service_identity_required')
  require(value['process_environment'][name].get('HERMES_HOME')==home,'current_process_home_required')
def validate_global_quiescence(value,dbs,gateway,*,current_monotonic):
 require(value['scope']=='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY'and value['read_only']is True,'global_native_scope_required')
 require(value['identity']==dict(pid=gateway['pid'],start_time=gateway['birth_ticks'],boot_id=gateway['boot_id']),'global_native_kernel_identity_required')
 observed=value['observed_monotonic'];require(type(observed)in(int,float)and math.isfinite(observed)and 0<=current_monotonic-observed<=15,'fresh_global_native_observation_required')
 require(value['global_active_session_keys']==[],'global_runner_not_quiescent')
 for name in ('terminal_custody','web_custody'):
  row=value[name];require(row['status']=='QUIESCENT'and row['sessions']==[]and row['recovery_blocked']is False,'global_custody_not_quiescent')
 require(set(dbs)=={'default','dest','tester'}and all(row['quick_check']=='ok'and row['leases']==row['all_origin_pending_delegations']==0 for row in dbs.values()),'all3DB_all_origin_work_not_quiescent')
def compare_service(actual,expected,environment,expected_environment):
 require(actual==expected,'current_service_identity_changed');require(environment==expected_environment,'current_service_environment_changed')
def guard_absent(paths,lexists):
 for path in paths:require(not lexists(path),'consumed_output_or_transaction_exists:'+str(path))
