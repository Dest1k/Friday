"""Require exact D15 predecessor rows and reviews in the existing owned caller."""

from hashlib import sha256
import os
from pathlib import Path
import re
import stat


ALT_01 = "090f7276e1017c2ae2d3583f98db60702a2c0aa5baba1d069b80ac9b443c600b"
ALT_02 = "5c7ceffc7a22b17c67257f73efbb963d22ee85c7a78498700abc613fea821f3a"
ALT_03 = "a29e35c039f7f851fa2bcf220721859edfdf6f351bca41147509b714b0d24c68"
PHASES = (ALT_01, ALT_02, ALT_03)
COMPOSER_SHA256 = "57a21c19d5c2fde2ad06a9800502bdb7a5001ddf1be004c98c6ffe609bc139f6"
CURRENT_SHA256 = "2983e06dc5579adae0f0983d64d07b65c41f849b03dca0985f270d2547a9411b"


def reviewed_source(name, expected_sha256):
    path = Path(__file__).with_name(name)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOATIME
    with os.fdopen(os.open(path, flags), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 65536:
            raise ValueError("Bounded regular ordinary source required")
        raw = stream.read(65537)
    if len(raw) > 65536 or sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Exact reviewed ordinary source required")
    namespace = {"__file__": str(path)}
    exec(compile(raw, str(path), "exec"), namespace)
    return namespace


def check_predecessor_records(current, *, contract_ref, authority_ref, run_id,
                              scenario_sha256, history, prior_phases, immediate):
    # The existing current contract carries both evidence pairs. The authority
    # carries only the immediate pointer, and retains every row at its own hash.
    document = current["document"]
    contract = document(contract_ref)
    scope = contract.get("scope")
    if (contract.get("schema") != "frw.Root.ordinary-current-contract.v1"
            or contract.get("operator") != "Root" or contract.get("run_id") != run_id
            or contract.get("scenario_sha256") != scenario_sha256
            or contract.get("authority") != authority_ref or type(scope) is not dict):
        raise ValueError("D15 exact current contract required")
    rows, reviews = scope.get("rows", []), scope.get("reviews", [])
    if (type(rows) is not list or type(reviews) is not list
            or len(rows) != len(prior_phases) or len(reviews) != len(prior_phases)):
        raise ValueError("D15 exact ordered prior rows and reviews required")

    seen = {run_id}
    for expected, row_ref, review_ref in zip(prior_phases, rows, reviews, strict=True):
        row = document(row_ref)
        prior_id, scenario = row.get("id"), row.get("scenario")
        observations = row.get("observations")
        retained = history.get(prior_id) if type(prior_id) is str else None
        if (type(prior_id) is not str or prior_id in seen
                or type(retained) is not dict or retained.get("sha256") != row_ref["sha256"]
                or row.get("scenario_sha256") != expected or type(scenario) is not dict
                or current["digest"](current["encoded"](scenario)) != expected
                or row.get("status") != "EVIDENCE_READY" or retained.get("status") != "EVIDENCE_READY"
                or row.get("send_state") != "sent" or retained.get("send_state") != "sent"
                or type(row.get("send_attempts")) is not int or row["send_attempts"] != 1
                or type(row.get("deadline")) not in (int, float)
                or row["deadline"] != retained.get("deadline")
                or retained.get("new_effect_replay_authorized") is not False
                or retained.get("unknown_retained") is not False):
            raise ValueError("D15 exact retained predecessor row required")
        if (row.get("capture_window_complete") is not True
                or row.get("reply_outcome") != "RECEIVED_UNGRADED"
                or type(observations) is not list or not observations
                or any(type(item) is not dict or item.get("kind") != "reply_text"
                       or type(item.get("text")) is not str or not item["text"] for item in observations)):
            raise ValueError("D15 predecessor requires a complete text-only capture")
        seen.add(prior_id)

        review = document(review_ref)
        schema, custody = review.get("schema"), review.get("custody_evidence")
        if (type(schema) is not str or not schema or review.get("run_id") != prior_id
                or review.get("scenario_sha256") != expected
                or review.get("semantic") != "PASS" or review.get("custody") != "PASS"
                or type(custody) is not dict or custody.get("run_record_sha256") != row_ref["sha256"]):
            raise ValueError("D15 exact independent predecessor review required")
        if expected == prior_phases[-1] and immediate != {
                "run_id": prior_id, "scenario_sha256": expected, "initially_absent": False,
                "run_record_sha256": row_ref["sha256"], "review_schema": schema,
                "review": {"path": review_ref["path"], "sha256": review_ref["sha256"]}}:
            raise ValueError("D15 immediate predecessor differs from current row and review pins")


def compose_observer(source, *, run_id, scenario_sha256, authority, authority_ref,
                     checker_ref, proof_ref, contract_ref, prepare_ref):
    """Compose a singleton D15 phase. The current observer checks native scope."""
    if (type(run_id) is not str or re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id) is None
            or type(scenario_sha256) is not str or scenario_sha256 not in PHASES
            or type(authority) is not dict or type(authority.get("history")) is not dict):
        raise ValueError("Exact D15 phase and authority required")
    prior_phases = PHASES[:PHASES.index(scenario_sha256)]
    bindings = authority.get("ordered_predecessors", {})
    immediate = bindings.get(run_id) if type(bindings) is dict else None
    if not prior_phases:
        if type(bindings) is not dict or bindings:
            raise ValueError("D15 ALT-01 requires independent admission")
    elif (type(immediate) is not dict or set(bindings) != {run_id}
          or immediate.get("scenario_sha256") != prior_phases[-1]
          or immediate.get("initially_absent") is not False):
        raise ValueError("D15 requires the exact settled immediate predecessor")

    composer = reviewed_source("ordinary_admission_source.py", COMPOSER_SHA256)
    current = reviewed_source("ordinary_current.py", CURRENT_SHA256)
    composer["exact_reference"](contract_ref)
    check_predecessor_records(current, contract_ref=contract_ref, authority_ref=authority_ref,
                              run_id=run_id, scenario_sha256=scenario_sha256,
                              history=authority["history"], prior_phases=prior_phases, immediate=immediate)
    return composer["compose_observer"](
        source, run_id=run_id, scenario_sha256=scenario_sha256, authority=authority,
        authority_ref=authority_ref, checker_ref=checker_ref, proof_ref=proof_ref,
        contract_ref=contract_ref, prepare_ref=prepare_ref)
