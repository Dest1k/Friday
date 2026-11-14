"""Pure F03 assembly seams. No reads, writes, time, observations or execution.

Pass modules loaded by Root from the accepted candidate source pins. All proof,
observation, authorization, facts and clock values are supplied by Root. Returned
bytes/references are projections; this module does not publish or admit them.
"""
import copy
import hashlib
import json
from pathlib import Path


def require(value, reason):
    if not value:
        raise ValueError('F03_ASSEMBLY_' + reason)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def record(path, value):
    """Serialize a caller-supplied document; never write it or create its time."""
    path = str(path)
    p = Path(path)
    require(p.is_absolute() and str(p) == path and '..' not in p.parts,
            'CANONICAL_DESTINATION_REQUIRED')
    raw = encoded(value)
    return raw, dict(path=path, bytes=len(raw), sha256=digest(raw))


def preclock_inputs(adapter, current, binder, phase, original_contract,
                    root_proofs, current_proof, private_workdir):
    """Replace source/proof refs in a draft; retain original case and old clock.

    Root supplies six final scoped review references and a fresh proof draft.
    This does not refresh the proof, observe current state or approve reviews.
    """
    adapter.contract_shape(original_contract)
    require(original_contract['resources']['clock'] == phase.OLD_CLOCK,
            'PRESERVED_OLD_CLOCK_REQUIRED')
    require(original_contract['scenario_sha256'] == phase.SCENARIO_SHA,
            'EXACT_ORIGINAL_SCENARIO_REQUIRED')
    c = copy.deepcopy(original_contract)
    c.update(status='UNBOUND_NOT_GRANTED', adapter=copy.deepcopy(binder.ADAPTER),
             current_gate=copy.deepcopy(binder.CURRENT), root_current_review=None,
             root_proofs=copy.deepcopy(root_proofs))
    adapter.contract_shape(c, bound=False)
    require(set(root_proofs) == adapter.PROOFS and
            all(adapter.reference(r) for r in root_proofs.values()),
            'SIX_EXACT_ROOT_PROOF_REFS_REQUIRED')
    p = copy.deepcopy(current_proof)
    p.update(contract_effect=adapter.effect(c), boundary_phase='CURSOR_AUTHORITY')
    # A draft must not accidentally carry a retained old observation as final.
    p.pop('observed', None)
    p.pop('whole_effect_sha256', None)
    current.proof_shape(p)
    return c, p, phase.preclock_projection(private_workdir)


def freeze_preclock(adapter, current, binder, phase, draft_contract,
                    proof_draft, observed, proof_path, consumer_path,
                    reviewed_template_bytes):
    """Freeze supplied actual preclock observation, then bind final consumer.

    Call only after Root has stabilized scoped review documents and checked
    semantics/lifetime. Returned proof/consumer bytes must precede any new clock.
    """
    require(draft_contract.get('status') == 'UNBOUND_NOT_GRANTED' and
            draft_contract.get('root_current_review') is None,
            'UNBOUND_DRAFT_REQUIRED')
    require(proof_draft['contract_effect'] == adapter.effect(draft_contract) and
            proof_draft['boundary_phase'] == 'CURSOR_AUTHORITY' and
            proof_draft.get('status') == 'ROOT_BOUND',
            'EXACT_PRECLOCK_INPUTS_REQUIRED')
    require(observed.get('admission') is False and
            observed.get('installed_product') == adapter.EXPECTED and
            observed.get('current_files') == proof_draft['current_files'] and
            type(observed.get('f03_mutable_boundary')) is dict and
            observed['f03_mutable_boundary'], 'ACTUAL_OBSERVATION_REQUIRED')
    c = copy.deepcopy(draft_contract)
    c['mutable_boundary'] = copy.deepcopy(observed['f03_mutable_boundary'])
    require(c['resources']['clock'] == phase.OLD_CLOCK,
            'OLD_CLOCK_MUST_NOT_CHANGE')
    p = copy.deepcopy(proof_draft)
    p.update(contract_effect=adapter.effect(c), observed=copy.deepcopy(observed))
    p['whole_effect_sha256'] = digest(encoded(p['contract_effect']))
    current.proof_shape(p)
    proof_bytes, proof_ref = record(proof_path, p)
    c.update(status='ROOT_BOUND_EXACT_F03', root_current_review=proof_ref)
    adapter.contract_shape(c)
    consumer_bytes = binder.bind_source(reviewed_template_bytes, c)
    consumer_ref = dict(path=str(consumer_path), bytes=len(consumer_bytes),
                        sha256=digest(consumer_bytes))
    require(adapter.reference(consumer_ref), 'CANONICAL_CONSUMER_PATH_REQUIRED')
    return dict(contract=c, proof=p, proof_bytes=proof_bytes,
                proof_ref=proof_ref, consumer_bytes=consumer_bytes,
                consumer_ref=consumer_ref)


def supplement_without_decision(phase, implementation_ref, consumer_ref,
                                clock_ref, reconciliation_ref):
    """No grant is created; Root supplies already fixed refs after its decision."""
    for r in (implementation_ref, consumer_ref, clock_ref, reconciliation_ref):
        require(phase.refshape(r), 'EXACT_SUPPLEMENT_REF_REQUIRED')
    c = phase.unbound()
    c.update(status='ROOT_BOUND_SEPARATE_MISSING_FIRST_SEND',
             implementation=copy.deepcopy(implementation_ref),
             consumer=copy.deepcopy(consumer_ref), clock=copy.deepcopy(clock_ref),
             reconciliation=copy.deepcopy(reconciliation_ref))
    return c


def decision_bindings(phase, supplement):
    """Values Root's own decision must bind; decision itself is excluded."""
    require(set(supplement) == set(phase.unbound()) and
            supplement['plan'] == phase.plan() and
            supplement['decision'] is None and
            supplement['status'] == 'ROOT_BOUND_SEPARATE_MISSING_FIRST_SEND',
            'UNSIGNED_EXACT_SUPPLEMENT_REQUIRED')
    return dict(plan_sha256=digest(encoded(supplement['plan'])),
                binding_sha256=digest(encoded({k: v for k, v in supplement.items()
                                               if k != 'decision'})),
                clock=copy.deepcopy(supplement['clock']),
                reconciliation=copy.deepcopy(supplement['reconciliation']))


def finish_supplement(phase, unsigned, root_decision, clock_document,
                      reconciliation_document, decision_path, supplement_path,
                      case_entry_ref, supervisor_ref):
    """Serialize an independently supplied Root decision; never decide for Root.

    This is composition checking only. Candidate contract()/boundary()/launch()
    still perform custody, pin, current-clock, reconciliation and live checks.
    """
    expected = decision_bindings(phase, unsigned)
    d = root_decision
    require(type(d) is dict and all(d.get(k) == v for k, v in expected.items()),
            'ROOT_DECISION_BINDING_MISMATCH')
    require(d.get('schema') == 'frw.Root.F03.separate-first-send-decision.v1' and
            d.get('operator') == 'Root' and
            d.get('status') == 'ROOT_ACCEPTED_SEPARATE_MISSING_FIRST_SEND' and
            d.get('execution_grant') is True and
            d.get('authorization_basis') in
            ('ROOT_STANDING_AUTHORIZATION_APPLIES', 'EXPLICIT_OWNER_APPROVAL') and
            d.get('old_clocks_not_extended') is True and
            d.get('R108_is_only_additional_bound_not_grant') is True and
            d.get('expires_at') == clock_document['first_send_deadline_wall'] and
            d.get('case_entry_source') == case_entry_ref and
            d.get('supervisor_source') == supervisor_ref,
            'INDEPENDENT_ROOT_DECISION_REQUIRED')
    # Authenticate exactly supplied bytes, never recreate clock/facts or age.
    for ref, document in ((unsigned['clock'], clock_document),
                          (unsigned['reconciliation'], reconciliation_document)):
        require(record(ref['path'], document)[1] == ref, 'DOCUMENT_REF_MISMATCH')
    decision_bytes, decision_ref = record(decision_path, d)
    c = copy.deepcopy(unsigned)
    c['decision'] = decision_ref
    supplement_bytes, supplement_ref = record(supplement_path, c)
    return dict(supplement=c, decision_bytes=decision_bytes,
                decision_ref=decision_ref, supplement_bytes=supplement_bytes,
                supplement_ref=supplement_ref)


def projected_metadata(phase, supplement_ref, original_pristine_raw):
    """Compute expected refs only. Child alone writes fixed ONCE and BEFORE."""
    require(phase.refshape(supplement_ref), 'EXACT_FINAL_SUPPLEMENT_REF_REQUIRED')
    require(type(original_pristine_raw) is bytes and
            len(original_pristine_raw) == phase.PRISTINE['bytes'] and
            digest(original_pristine_raw) == phase.PRISTINE['sha256'],
            'EXACT_RAW_PRISTINE_REQUIRED')
    before = phase.pin(phase.BEFORE, original_pristine_raw)
    marker = dict(schema='frw.Root.F03.separate-first-send-consumed.v1',
                  status='CONSUMED_ON_ENTRY_NO_RETRY', run_id=phase.RUN,
                  contract=copy.deepcopy(supplement_ref), before=before,
                  predecessors=copy.deepcopy(phase.MARKERS),
                  closure=copy.deepcopy(phase.CLOSURE))
    marker_bytes = phase.enc(marker)
    return dict(contract=copy.deepcopy(supplement_ref),
                once=phase.pin(phase.ONCE, marker_bytes), before=before)


def require_unchanged(frozen, active_observed, consumer_bytes, final_supplement):
    """After Root's final read-only observe: drift refuses, no rewrite/reset."""
    require(active_observed == frozen['proof']['observed'],
            'ACTIVE_OBSERVATION_DRIFT')
    require(type(consumer_bytes) is bytes and
            consumer_bytes == frozen['consumer_bytes'] and
            digest(consumer_bytes) == frozen['consumer_ref']['sha256'] and
            final_supplement['consumer'] == frozen['consumer_ref'],
            'FINAL_CONSUMER_DRIFT')
    return True
