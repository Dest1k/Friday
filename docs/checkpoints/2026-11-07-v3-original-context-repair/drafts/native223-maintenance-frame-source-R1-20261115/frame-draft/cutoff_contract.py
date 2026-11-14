'Pure firstcandidate223 cutoff; all retained old data/replay fences remain.\n\nPort of the exact220 cutoff. The only new fence is old222; every210..218 fence\nis retained. This is source policy, not permission to reopen any old operation.\n'
CATEGORIES = {'active_turn', 'resume_flags', 'once', 'cancel'}
REPLAY_FENCES = tuple('preserve_current_data_no_old%d_delivery_or_resume' % n for n in range(210, 223))


def require(value, why):
    if not value:
        raise ValueError(why)


def scope_checked(scope):
    require(type(scope) is dict and scope.get('root_qualified_complete_scope') is True
            and scope.get('other_relevant_writers_admission_sealed') is True, 'Root_complete_stopped_recovery_data_scope_required')
    require(set(scope.get('covered_categories', [])) == CATEGORIES and scope.get('evidence'), 'Root_recovery_state_category_evidence_required')
    paths = scope.get('related_recovery_state_paths')
    require(type(paths) is list and paths == sorted(set(paths)) and paths
            and all(type(x) is str and x.startswith('/') and 'UNBOUND' not in x for x in paths), 'Root_exact_related_recovery_paths_required')
    return paths


def _before223(j):
    require(j.get('candidate_startup_cutoff') == {'state': 'NOT_CROSSED_NO_CANDIDATE_PROCESS_OR_EFFECT'}
            and j.get('candidate_start_attempt_intent') is None, 'old222_forbidden_after_candidate_start_or_UNKNOWN')
    require(j.get('managed_phase_may_have_executed') is False, 'no_automatic_old_resume_or_DBrestore')
    return True


def before_old_start(j, *, observed, settled, all_writers_sealed):
    _before223(j)
    require(all_writers_sealed is True and observed == settled, 'old222_requires_exact_stopped_all_data_and_sealed_writers')
    require(j['restore_verified_inputs']['publisher_code'] == 2, 'old222_only_after_publisher_refusal_or_verified_rollback')
    return True


def cross_before_candidate_start(j, *, request, observed, settled, all_writers_sealed, persist):
    _before223(j)
    require(observed == settled and all_writers_sealed is True, 'candidate_start_requires_exact_stopped_data_and_sealed_writers')
    require(j['restore_verified_inputs']['publisher_code'] == 0 and j['selected_project'] == j['candidate_project'], 'candidate223_committed_required')
    intent = dict(state='CROSSED_BEFORE_FIRST_CANDIDATE_START_UNKNOWN_COUNTS_AS_CROSSED', request=request,
                  original_origin_monotonic=j['origin_monotonic'], original_absolute_deadline_monotonic=j['absolute_deadline_monotonic'],
                  no_automatic_model_delivery_resume=True, no_DB_restore=True, **{name: True for name in REPLAY_FENCES})
    j['candidate_startup_cutoff'] = dict(intent)
    j['candidate_start_attempt_intent'] = dict(intent)
    j['managed_phase_may_have_executed'] = True
    persist()  # Must finish durably before the first service phase may start.
    return intent


def saved_recovery_checked(j):
    gate = j['restore_verified_inputs']; cut = j.get('candidate_startup_cutoff'); intent = j.get('candidate_start_attempt_intent')
    require(type(cut) is dict, 'missing_cutoff_requires_Root_reconciliation_no_old_start')
    if gate['publisher_code'] == 2:
        _before223(j)
        return 'OLD222_ONLY_IF_CURRENT_EXACT_STOPPED_DATA_REVERIFIED'
    require(gate['publisher_code'] == 0 and j['selected_project'] == j['candidate_project'], 'forward223_only_current_settled_candidate')
    if intent is not None:
        require(cut == intent and cut.get('request') == j['request'] and j.get('managed_phase_may_have_executed') is True,
                'candidate_cutoff_identity_changed')
        require(all(cut.get(k) is True for k in REPLAY_FENCES + ('no_automatic_model_delivery_resume', 'no_DB_restore')), 'phase_rollback_fence_required')
        require(cut['original_origin_monotonic'] == j['origin_monotonic']
                and cut['original_absolute_deadline_monotonic'] == j['absolute_deadline_monotonic'], 'original_clock_must_not_change')
        return 'FORWARD223_SAME_SAVED_PHASES_ONLY_NO_PUBLISHER_OR_NEW_CLOCK'
    _before223(j)
    require(not j['service_phases'], 'unknown_candidate_phase_requires_Root_reconciliation')
    return 'CANDIDATE223_NOT_STARTED_REQUIRE_CUTOFF_BEFORE_START'


def before_unconsumed_candidate_service_start(j, *, request, observed, settled, all_writers_sealed, persist):
    require(not j['service_phases'] and request == j['request'], 'first_candidate_service_phase_not_consumed_required')
    require(observed == settled and all_writers_sealed is True, 'candidate_start_requires_exact_stopped_data_and_sealed_writers')
    if j.get('candidate_start_attempt_intent') is None:
        return cross_before_candidate_start(j, request=request, observed=observed, settled=settled,
                                            all_writers_sealed=all_writers_sealed, persist=persist)
    require(saved_recovery_checked(j) == 'FORWARD223_SAME_SAVED_PHASES_ONLY_NO_PUBLISHER_OR_NEW_CLOCK', 'exact_saved_forward_cutoff_required')
    return j['candidate_start_attempt_intent']
