"""Inert exact F07 source caller. Functions assemble caller-selected bindings only.
No Store/new/send/current/native/operationclock execution; Root retains all effects.
Use only after Root's independent original first-phase eligibility determination.
"""
from __future__ import annotations
import hashlib
import json
import types


def need(ok,code):
    if not ok: raise ValueError(code)


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()


def load_checker(checker_ref,read_reference):
    """Explicit pinned SOURCE load using accepted direct/nested guarded reader."""
    raw=read_reference(checker_ref)
    need(len(raw)==checker_ref['bytes'] and hashlib.sha256(raw).hexdigest()==checker_ref['sha256'],'F07_EXACT_CHECKER_SOURCE_REQUIRED')
    value=types.ModuleType('_Root_F07_current209');value.__file__=checker_ref['path']
    exec(compile(raw,value.__file__,'exec'),value.__dict__);return value


def assemble_effect(checker,*,phase,run_id,authority_ref,scenario_ref,checker_ref,closure_ref,acceptance_ref,resources):
    """Pure; genuine authority/effect/current/source/provenance stay Root-bound."""
    return checker.prepare_effect(run_id=run_id,phase=phase,authority_ref=authority_ref,scenario_ref=scenario_ref,
        checker_ref=checker_ref,closure_ref=closure_ref,acceptance_ref=acceptance_ref,resources=resources)


def qualify_selected_ordinary_readonly(genuine_runner,*,run_id,phase):
    """FUTURE ROOT CALL on genuine selected Runner with api=None, never new/send.
    Root verifies existing protected Store dirs before its actual constructor;
    this helper neither constructs one nor substitutes a source stand as actual.
    Admission/current-row refusal propagates unchanged and grants no user effect.
    Use the authority-pinned ordinary source before attaching the operation-only
    preintent proof, then separately collect actual current metadata with
    checker.observe_readonly. No tool capability/normal context is fabricated.
    """
    need(genuine_runner.api is None,'F07_READONLY_RUNNER_MUST_HAVE_NO_API')
    admission=genuine_runner.ordinary_independent_admission(run_id,phase['scenario'])
    need(admission is not None,'F07_EXACT_SELECTED_ORDINARY_ADMISSION_REQUIRED')
    genuine_runner.ordinary_independent_current_rows(admission,run_id)
    return dict(state='SELECTED_ORDINARY_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION',run_id=run_id,
                scenario_sha256=phase['scenario_sha256'],new_called=False,send_called=False)


def assemble_root_proof(checker,*,effect,observed,created_at,expires_at,created_monotonic,expires_monotonic,
                        boot_id,lock_owners,invocation_ref,Root_decision_ref,privacy_preflight_ref):
    """Pure shape assembly, not issuance. Every factual/semantic input is Root's.
    Must be saved/protected only by Root after actual current collection/review.
    Invocation was O_EXCL-created by the existing finite Root caller once, with
    exact consumer kernel identity, held consumer+credential locks and same clock.
    """
    value=checker.unbound_proof()
    value.update(status='ROOT_BOUND',effect=checker.clone(effect),whole_effect_sha256=checker.digest(checker.encoded(effect)),
       observed=checker.clone(observed),created_at=created_at,expires_at=expires_at,created_monotonic=created_monotonic,
       expires_monotonic=expires_monotonic,boot_id=boot_id,lock_owners=checker.clone(lock_owners),invocation=checker.clone(invocation_ref),
       Root_decision=checker.clone(Root_decision_ref),privacy_preflight=checker.clone(privacy_preflight_ref))
    need(set(value)==checker.PROOF_FIELDS,'F07_EXACT_PROOF_ASSEMBLY_REQUIRED')
    return value


def compose_consumer(checker,base_raw,*,effect,authority,proof_ref,previous_phase=None):
    """Pure actual nearest caller. No candidate file/module/Store is created."""
    prep=checker.module(checker.PREP)
    phase=effect['phase'];run_id=effect['run_id']
    ordinary=prep.compose_source(base_raw,phase,run_id=run_id,authority_ref=effect['authority'],authority=authority,previous_phase=previous_phase)
    return checker.compose_preintent_source(ordinary,phase=phase,run_id=run_id,authority_ref=effect['authority'],
        authority=authority,proof_ref=proof_ref,checker_ref=effect['checker'],previous_phase=previous_phase)


def actual_predecessor_review(checker,*,effect,observed,assessment,assessment_ref):
    """Root-only pure bridge from independently assessed SAVED actual artifacts.
    Produces selected ordinary predecessor-review ABI; grants no new operation.
    """
    checker.need(checker.read_reference(assessment_ref)==checker.encoded(assessment),'F07_EXACT_ROOT_ACTUAL_ASSESSMENT_REQUIRED')
    checked=checker.assess_saved_actual(assessment,effect=effect,observed=observed)
    verdicts=checked['verdicts']
    need(verdicts['semantic']==verdicts['custody']=='PASS','F07_ACTUAL_PREDECESSOR_NOT_ACCEPTED')
    need(verdicts['privacy']!='FAIL' and verdicts['native_host_close']=='PASS',
         'F07_PREDECESSOR_PRIVACY_FAILURE_OR_HOST_NOT_CLOSED')
    run_ref=checked['evidence']['canonical_run'];run=checker.doc(run_ref)
    need(run['status']=='EVIDENCE_READY' and run['send_state']=='sent' and run['send_attempts']==1,
         'F07_ACTUAL_COMPLETE_SINGLE_SEND_PREDECESSOR_REQUIRED')
    return dict(schema='frw.Root.F07.semantic-custody-review.v1',run_id=effect['run_id'],scenario_sha256=effect['phase']['scenario_sha256'],
       semantic='PASS',custody='PASS',custody_evidence=dict(run_record_sha256=run_ref['sha256']),
       actual_postcondition_assessment=checker.clone(assessment_ref),whole_effect_sha256=checker.digest(checker.encoded(effect)),
       expected_semantics=effect['phase']['expected_semantics'],raw_reply_semantic_status=run.get('reply_text_acceptance'),
       privacy_verdict=verdicts['privacy'],native_host_close=verdicts['native_host_close'],
       original_phase_acceptance_is_not_global_formal_acceptance=True)


def immediate_predecessor_binding(checker,*,canonical_run_ref,review_ref):
    """Root writes/reviews exact review bytes first; no future or absent review."""
    prep=checker.module(checker.PREP);raw=checker.read_reference(canonical_run_ref);run=checker.parse(raw);review=checker.doc(review_ref)
    need(review.get('run_id')==run['id'] and review.get('scenario_sha256')==run['scenario_sha256']
         and review.get('semantic')==review.get('custody')=='PASS'
         and review.get('custody_evidence',{}).get('run_record_sha256')==canonical_run_ref['sha256'],'F07_EXACT_ACTUAL_REVIEW_JOIN_REQUIRED')
    return prep.predecessor_binding(run,review_ref,review_schema=review['schema'],run_raw=raw)
