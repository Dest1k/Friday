"""Inert exact F07 source caller. Functions assemble caller-selected bindings only.
No Store/new/send/current/native/operationclock execution; Root retains all effects.
Use only after Root's independent original ordered-successor eligibility determination.
"""
from __future__ import annotations
import hashlib
import json
import types
from pathlib import Path


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
    """FUTURE ROOT locked call: original new prefix through every pre-row check.

    Exact composition contains AST-derived original Runner.new checks, truncated
    immediately before row construction. No new/save/stamp/deadline/API/send or
    operation clock is invoked. Historical expiry reads remain original checks.
    This qualifies no current209 proof, operation eligibility or user effect.
    """
    need(genuine_runner.api is None,'F07_READONLY_RUNNER_MUST_HAVE_NO_API')
    result=genuine_runner._f07_qualify_new_prefix_readonly(run_id,phase['scenario'])
    admission=genuine_runner.ordinary_independent_admission(run_id,phase['scenario'])
    need(admission is not None,'F07_EXACT_SELECTED_ORDINARY_ADMISSION_REQUIRED')
    genuine_runner.ordinary_independent_current_rows(admission,run_id)
    need(result['scenario_sha256']==phase['scenario_sha256'],'F07_EXACT_READONLY_PREFIX_SCENARIO_REQUIRED')
    return result


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


def select_ordered_successor(prep, saved, *, ordinal, scenario_raw):
    """Pure exact original array selection, successor-only; creates no grant."""
    need(type(ordinal) is int and 2<=ordinal<=4,'F07_EXPLICIT_SUCCESSOR_ORDINAL_REQUIRED')
    phases=saved.get('result',{}).get('phases') if type(saved) is dict else None
    need(type(phases) is list and len(phases)==4,'F07_ORIGINAL_FOUR_PHASE_ARRAY_REQUIRED')
    for index,phase in enumerate(phases,1):
        need(type(phase) is dict and phase.get('ordinal')==index
             and phase==prep.phase_preparation(index,phase['scenario']['steps'][0]['input']),
             'F07_EXACT_ORDERED_SAVED_PHASE_REQUIRED')
    phase=phases[ordinal-1];previous=phases[ordinal-2]
    need(type(scenario_raw) is bytes and scenario_raw==prep.encoded(phase['scenario']),
         'F07_EXACT_SELECTED_SUCCESSOR_SCENARIO_REQUIRED')
    return phase,previous


def accepted_successor_predecessor(checker, *, phase, previous_phase, original_phases, run_id, authority, bundle):
    """Root-only SAVED actual bridge, never accepts a caller-shaped future PASS.

    It reuses saved effect/observed/assessment and reconstructs the existing
    reviewed ABI. Historical proofs are not refreshed or used as current grants.
    The genuine ordinary prefix independently checks the immediate custody chain.
    """
    prep=checker.module(checker.PREP)
    selected,previous=select_ordered_successor(prep,dict(result=dict(phases=original_phases)),
        ordinal=phase.get('ordinal'),scenario_raw=prep.encoded(phase.get('scenario')))
    need(selected==phase and previous==previous_phase,'F07_ORIGINAL_SUCCESSOR_ARRAY_BINDING_REQUIRED')
    fields={'canonical_run','review','effect_and_consumer','proof','assessment'}
    need(type(bundle) is dict and set(bundle)==fields
         and all(checker.reference_shape(bundle[k]) for k in fields),'F07_ACTUAL_PREDECESSOR_BUNDLE_REQUIRED')
    descriptor=checker.doc(bundle['effect_and_consumer']);proof=checker.doc(bundle['proof'])
    effect=descriptor.get('effect');assessment=checker.doc(bundle['assessment']);review=checker.doc(bundle['review'])
    need(type(effect) is dict and descriptor.get('proof')==bundle['proof']
         and proof.get('schema')=='frw.Root.F07.current209-preintent.v1' and proof.get('operator')=='Root'
         and proof.get('status')=='ROOT_BOUND' and proof.get('effect')==effect
         and proof.get('whole_effect_sha256')==checker.digest(checker.encoded(effect))
         and type(proof.get('observed')) is dict and effect.get('phase')==previous_phase
         and previous_phase.get('ordinal')==phase.get('ordinal',0)-1,
         'F07_EXACT_SAVED_PREDECESSOR_EFFECT_REQUIRED')
    need(review.get('schema')=='frw.Root.F07.semantic-custody-review.v1'
         and assessment.get('evidence',{}).get('canonical_run')==bundle['canonical_run']
         and review.get('actual_postcondition_assessment')==bundle['assessment'],
         'F07_EXACT_SAVED_PREDECESSOR_ASSESSMENT_REQUIRED')
    expected=actual_predecessor_review(checker,effect=effect,observed=proof['observed'],
        assessment=assessment,assessment_ref=bundle['assessment'])
    need(review==expected and checker.read_reference(bundle['review'])==checker.encoded(expected),
         'F07_SAVED_ACTUAL_PREDECESSOR_REVIEW_CHANGED')
    raw=checker.read_reference(bundle['canonical_run']);run=checker.parse(raw)
    need(run.get('scenario')==previous_phase['scenario'] and run.get('id')==effect.get('run_id')
         and bundle['canonical_run']['path']==str(checker.STATE/'runs'/(run['id']+'.json')),
         'F07_CANONICAL_IMMEDIATE_PREDECESSOR_REQUIRED')
    binding=immediate_predecessor_binding(checker,canonical_run_ref=bundle['canonical_run'],review_ref=bundle['review'])
    need(authority.get('ordered_predecessors')=={run_id:binding},'F07_EXACT_AUTHORITY_ACTUAL_PREDECESSOR_JOIN_REQUIRED')
    if phase['ordinal']==2:
        need(bundle['canonical_run']==ORIGINAL_PHASE1_CANONICAL
             and bundle['review']==ORIGINAL_PHASE1_REVIEW,'F07_SAME_STARTED_ORIGINAL_SEQUENCE_ANCHOR_REQUIRED')
    else:
        # Previous accepted operation must itself have admitted the preceding
        # original phase. Its already-accepted effect is retained, not reissued.
        old_authority=checker.doc(effect['authority'])
        pred=old_authority.get('ordered_predecessors',{}).get(effect['run_id'],{})
        need(old_authority.get('f07_original_case')==dict(case_id='F-07',case_index=168,
                 phase=previous_phase['phase'],ordinal=previous_phase['ordinal'],
                 controlled_fault_sequence_not_replay=True,prospective_fixture_not_original=True)
             and type(pred) is dict and set(pred)==prep.PREDECESSOR_FIELDS
             and pred.get('initially_absent') is False and prep.sha(pred.get('run_record_sha256'))
             and pred.get('run_id')!=effect['run_id']
             and pred.get('scenario_sha256')==original_phases[phase['ordinal']-3]['scenario_sha256'],
             'F07_PREVIOUS_ACTUAL_ORDERED_SEQUENCE_REQUIRED')
        if phase['ordinal']==3:
            need(pred.get('run_id')==Path(ORIGINAL_PHASE1_CANONICAL['path']).stem
                 and pred.get('run_record_sha256')==ORIGINAL_PHASE1_CANONICAL['sha256']
                 and pred.get('review')=={k:ORIGINAL_PHASE1_REVIEW[k] for k in ('path','sha256')}
                 and pred.get('review_schema')=='frw.Root.F07.semantic-custody-review.v1',
                 'F07_SAME_STARTED_ORIGINAL_SEQUENCE_ANCHOR_REQUIRED')
    return previous_phase

ORIGINAL_PHASE1_CANONICAL = {'path': '/home/jericho/.local/share/friday-telegram-bot-test/runs/f07-ordered-noext-20261113-r1.json', 'bytes': 13561, 'sha256': '1ca07cc37f9be0ead7b5ddcae24d7f0b9f18fad38922bdc4743046b5ba0d961b'}
ORIGINAL_PHASE1_REVIEW = {'path': '/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113/ACTUAL-PHASE1/ROOT-ACTUAL-PHASE1-SEMANTIC-CUSTODY-PREDECESSOR-REVIEW.json', 'bytes': 945, 'sha256': 'b6b21c122204dcea22ff87905cb8e47e9773677b737ea2c33069d0d27edfff2b'}
