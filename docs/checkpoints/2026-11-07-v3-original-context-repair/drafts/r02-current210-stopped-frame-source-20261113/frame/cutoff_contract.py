"""Pure firstcandidate cut-off. Root observations authenticate data/scope, never this module."""
CATEGORIES={'active_turn','resume_flags','once','cancel'}
def require(value,why):
 if not value:raise ValueError(why)
def scope_checked(scope):
 require(type(scope)is dict and scope.get('root_qualified_complete_scope')is True and scope.get('other_relevant_writers_admission_sealed')is True,'Root_complete_stopped_recovery_data_scope_required')
 require(set(scope.get('covered_categories',[]))==CATEGORIES and scope.get('evidence'),'Root_recovery_state_category_evidence_required')
 paths=scope.get('related_recovery_state_paths')
 require(type(paths)is list and paths==sorted(set(paths)) and paths and all(type(x)is str and x.startswith('/')and 'UNBOUND'not in x for x in paths),'Root_exact_related_recovery_paths_required')
 return paths

def before_old_start(j,*,observed,settled,all_writers_sealed):
 require(j.get('candidate_startup_cutoff')=={'state':'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'},'old210_forbidden_after_candidate_start_or_UNKNOWN')
 require(j.get('candidate_start_attempt_intent')is None and all_writers_sealed is True and observed==settled,'old210_requires_exact_stopped_all_data_and_sealed_writers')
 require(j['restore_verified_inputs']['publisher_code']==2,'old210_only_after_publisher_refusal_or_verified_rollback')
 return True

def cross_before_candidate_start(j,*,request,observed,settled,all_writers_sealed,persist):
 require(j.get('candidate_startup_cutoff')=={'state':'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'}and j.get('candidate_start_attempt_intent')is None,'candidate_start_cutoff_already_consumed_no_retry')
 require(observed==settled and all_writers_sealed is True,'candidate_start_requires_exact_stopped_data_and_sealed_writers')
 require(j['restore_verified_inputs']['publisher_code']==0 and j['selected_project']==j['candidate_project'],'candidate211_committed_required')
 intent={'state':'CROSSED_BEFORE_FIRST_CANDIDATE_START_UNKNOWN_COUNTS_AS_CROSSED','request':request,'original_origin_monotonic':j['origin_monotonic'],'original_absolute_deadline_monotonic':j['absolute_deadline_monotonic'],'preserve_current_data_no_old210_delivery_or_resume':True}
 j['candidate_startup_cutoff']=dict(intent);j['candidate_start_attempt_intent']=dict(intent)
 # Caller must not issue start until durable journal save including fsync returns.
 persist()
 return intent

def saved_recovery_checked(j):
 gate=j['restore_verified_inputs'];cut=j.get('candidate_startup_cutoff');intent=j.get('candidate_start_attempt_intent')
 require(type(cut)is dict,'missing_cutoff_requires_Root_reconciliation_no_old_start')
 if gate['publisher_code']==2:
  require(cut=={'state':'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'}and intent is None,'old210_forbidden_after_candidate_start_or_UNKNOWN')
  return 'OLD210_ONLY_IF_CURRENT_EXACT_STOPPED_DATA_REVERIFIED'
 require(gate['publisher_code']==0 and j['selected_project']==j['candidate_project'],'forward211_only_current_settled_candidate')
 if intent is not None:
  require(cut==intent and cut.get('request')==j['request']and cut.get('preserve_current_data_no_old210_delivery_or_resume')is True,'candidate_cutoff_identity_changed')
  require(cut['original_origin_monotonic']==j['origin_monotonic']and cut['original_absolute_deadline_monotonic']==j['absolute_deadline_monotonic'],'original_clock_must_not_change')
  return 'FORWARD211_SAME_SAVED_PHASES_ONLY_NO_PUBLISHER_OR_NEW_CLOCK'
 require(cut=={'state':'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'}and not j['service_phases'],'unknown_candidate_phase_requires_Root_reconciliation')
 return 'CANDIDATE211_NOT_STARTED_REQUIRE_CUTOFF_BEFORE_START'
