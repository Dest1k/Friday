"""Evaluate the saved R4 replies for the two-stage D07 TXT paraphrase."""

from datetime import datetime
import json
import math
import re

from ordinary_d03_reply import digest, original_ack, pinned_bytes, pinned_record, retained_text
from ordinary_s11_reply import direct_attachment_count, direct_reply_update_ids


PHASES = {
    "D-07-01": ("6a515948631c75aee8a459e8255a7e44fdd7463892ecaef298333ff46d75e406",
                "23c9df7fe3c1646729ec796e1673c3759fad763175d4b0f853a9f73cf4ba3fde", 934),
    "D-07-02": ("47281ab30864393e64cf0aeec569492c399d821944fbd21f25b43893ed154f01",
                "29dadb4c0b17a12c7bd07a7ad4544b19bead6f7b027224936ce7f40544e3c5bf", 891),
}
ORACLE_SHA256 = "cf30906dfa3817efa44788c35c445661a120d90560ca1b287749307d93e22954"
REVIEW_SCHEMA = "frw.root.d07-staged-reply-review.v1"
SCOPE_SCHEMA = "frw.root.d07-staged-reply-scope.v1"
AUTHORITY_SCHEMA = "frw.Root.ordinary-independent-history-admission.v1"
LINEAGE = {"principal", "peer", "chat", "topic", "native_session", "workspace"}


def finite_time(value):
    return type(value) in (int, float) and math.isfinite(value)


def read_closed_phase(observer, runner, cursor, phase, run_id, run_ref):
    if type(run_id) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D07 run ID required")
    path = runner.store.run_path(run_id)
    run = pinned_record(observer, run_ref, expected_path=path)
    scenario_sha, source_sha, source_size = PHASES[phase]
    if (run.get("id") != run_id or run.get("scenario_sha256") != scenario_sha
            or digest(observer.encoded(run["scenario"])) != scenario_sha
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or type(run.get("sent_message_id")) is not int or run["sent_message_id"] <= 0
            or run.get("sent_ids") != [run["sent_message_id"]] or run.get("send_state") != "sent"
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D07 phase and one original send required")
    created = datetime.fromisoformat(run["created_at"])
    intent, dispatch, sent, until, deadline = (run[name] for name in (
        "send_intent_at", "send_dispatch_at", "sent_at", "capture_until", "deadline"))
    if (created.utcoffset() is None or not all(map(finite_time, (intent, dispatch, sent, until, deadline)))
            or abs(deadline - created.timestamp() - 300) > 1
            or not created.timestamp() - 1 <= intent <= dispatch <= sent < until < deadline
            or until != sent + 180):
        raise ValueError("Exact D07 original 300/180-second clocks required")

    upload = run["scenario"]["steps"][0]["input"]
    request = run["request_metadata"]
    if request.get("input_sha256") != source_sha or request.get("input_bytes") != source_size:
        raise ValueError("D07 source identity differs from the original upload")
    source = observer.read_document_input(upload, lambda: None)
    if len(source) != source_size or digest(source) != source_sha:
        raise ValueError("Exact D07 original source bytes required")

    if runner.send_ack_budget(run) != 10 or run.get("send_timeout_seconds") != 10:
        raise ValueError("D07 original tester ACK deadline differs from 10 seconds")
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    if not observer.valid_input_ack(ack, upload, require_document_size=True):
        raise ValueError("D07 original ACK upload size differs or is unobserved")
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    terminal = drain.get("complete")
    if terminal is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D07 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome or len(observations) > 1:
        raise ValueError("D07 requires one whole direct text reply or a complete empty window")
    if direct_attachment_count(observer, runner, run, captures, ack):
        raise ValueError("D07 direct attachment conflicts with the text-only reply contract")
    text_ids = direct_reply_update_ids(observer, runner, run, captures, ack,
                                       contains=lambda message: "text" in message)
    if text_ids != [observation["update_id"] for observation in observations]:
        raise ValueError("D07 raw direct text inventory differs from the retained reply")

    answer, receipt = None, None
    if observations:
        body, receipt = retained_text(observer, runner, run, observations[0], captures, ack)
        answer = body.decode("utf-8")
        if not answer.strip() or receipt["tester_reply_message_id"] == ack["message_id"]:
            raise ValueError("D07 direct reply is empty or reuses its ACK message identity")
    capture = {
        "phase": phase, "run_id": run_id, "run": run_ref, "scenario_sha256": scenario_sha,
        "source_sha256": source_sha, "source_bytes": source_size,
        "sender_ack_id": ack["message_id"], "file_unique_id": ack["document"]["file_unique_id"],
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"], "send_intent_at": intent,
        "send_dispatch_at": dispatch, "sent_at": sent, "capture_until": until,
        "original_deadline": deadline, "terminal_completed_at": terminal["completed_at"],
        "receive_head": run["receive_head"], "reply_outcome": outcome,
        "reply": receipt, "answer_sha256": receipt["text_sha256"] if receipt is not None else None,
    }
    return capture, answer


def read_scope(observer, reference, capture, capture_sha):
    scope = pinned_record(observer, reference)
    if (set(scope) != {"schema", "operator", "capture_sha256", "lineage", "native_input", "context"}
            or scope["schema"] != SCOPE_SCHEMA or scope["operator"] != "Root"
            or scope["capture_sha256"] != capture_sha):
        raise ValueError("D07 scope receipt must name this exact closed capture")
    lineage = scope["lineage"]
    if (type(lineage) is not dict or set(lineage) != LINEAGE
            or any(type(lineage[key]) is not str or not lineage[key].strip() for key in LINEAGE - {"topic"})
            or (lineage["topic"] is not None
                and (type(lineage["topic"]) is not str or not lineage["topic"].strip()))):
        raise ValueError("D07 scope receipt requires the complete native lineage")
    native = scope["native_input"]
    source_fields = {"sender_ack_id", "file_unique_id", "source_sha256", "source_bytes"}
    if (type(native) is not dict or set(native) != source_fields | {"receiver_native_id", "evidence"}
            or any(type(native[key]) is not type(capture[key]) or native[key] != capture[key]
                   for key in source_fields)
            or type(native["receiver_native_id"]) is not str or not native["receiver_native_id"].strip()):
        raise ValueError("D07 native input receipt differs from the sender ACK or source")
    pinned_bytes(observer, native["evidence"])
    context = scope["context"]
    if type(context) is not dict:
        raise ValueError("Exact D07 context receipt required")
    return scope


def validate_context(observer, current, scope, previous):
    context = scope["context"]
    if previous is None:
        if (set(context) != {"initial_v1_absent", "initial_v2_absent", "evidence"}
                or context["initial_v1_absent"] is not True or context["initial_v2_absent"] is not True):
            raise ValueError("D07 phase 1 requires a clean comparison context")
    else:
        previous_item, previous_scope = previous
        prior = previous_item["capture"]
        if (set(context) != {"retained_v1", "ordered_authority", "evidence"}
                or scope["lineage"] != previous_scope["lineage"]
                or context["retained_v1"] != previous_scope["native_input"]
                or scope["native_input"]["receiver_native_id"] == context["retained_v1"]["receiver_native_id"]):
            raise ValueError("D07 phase 2 requires the exact retained v1 in the same native lineage")
        authority = pinned_record(observer, context["ordered_authority"])
        review = previous_item["review"]
        binding = {
            "run_id": prior["run_id"], "scenario_sha256": prior["scenario_sha256"],
            "run_record_sha256": prior["run"]["sha256"], "initially_absent": False,
            "review_schema": REVIEW_SCHEMA,
            "review": {key: review[key] for key in ("path", "sha256")},
        }
        created, expires = authority.get("created_at"), authority.get("expires_at")
        if (authority.get("schema") != AUTHORITY_SCHEMA or authority.get("operator") != "Root"
                or authority.get("accepted") is not True
                or authority.get("run_scenarios") != {current["run_id"]: current["scenario_sha256"]}
                or authority.get("ordered_predecessors") != {current["run_id"]: binding}
                or not finite_time(created) or not finite_time(expires)
                or not prior["original_deadline"] <= created <= current["send_intent_at"]
                or not current["send_dispatch_at"] < expires):
            raise ValueError("D07 phase 2 requires its original ordered authority and exact predecessor review")
    pinned_bytes(observer, context["evidence"])


def independent_verdict(observer, reference, item):
    if item["scope"] is None or item["capture"]["reply"] is None:
        raise ValueError("D07 independent review requires the exact reply and clean scope receipts")
    review = pinned_record(observer, reference)
    capture = item["capture"]
    expected = {
        "schema": REVIEW_SCHEMA, "run_id": capture["run_id"], "scenario_sha256": capture["scenario_sha256"],
        "capture_sha256": item["capture_sha256"], "answer_sha256": capture["answer_sha256"],
        "scope_sha256": item["scope"]["sha256"], "oracle_sha256": ORACLE_SHA256,
        "criteria_sha256": item["criteria_sha256"],
        "custody_evidence": {"run_record_sha256": capture["run"]["sha256"]},
    }
    if (set(review) != set(expected) | {"semantic", "custody", "independent_evidence"}
            or any(review[key] != value for key, value in expected.items())
            or review["semantic"] not in ("PASS", "FAIL") or review["custody"] not in ("PASS", "FAIL")):
        raise ValueError("D07 independent review differs from the exact reply, scope or oracle")
    pinned_bytes(observer, review["independent_evidence"])
    return review["semantic"], review["custody"]


def evaluate_saved_series(observer, store, *, stages, cursor_ref, oracle_ref):
    """Use the pinned R4 observer and Root-selected protected evidence references.

    Each prefix item names phase, run_id, run_ref, scope_ref and review_ref.
    The caller authenticates the underlying native and independent witnesses.
    The Root scope witness must join the ordered authority to the original
    phase-2 invocation. This reader checks the pinned authority's fields.
    The returned text is private evidence for semantic review of the pinned oracle.
    """
    if type(stages) not in (tuple, list) or not 1 <= len(stages) <= len(PHASES):
        raise ValueError("Exact D07 stage prefix required")
    raw = pinned_bytes(observer, oracle_ref)
    if digest(raw) != ORACLE_SHA256:
        raise ValueError("Exact D07 staged text oracle required")
    oracle = json.loads(raw, object_pairs_hook=observer.unique_object)
    cursor_path = store.root / "cursor.json"
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    runner = observer.Runner(store, None)
    items = []
    prior_scope = None
    seen_ids = set()
    for index, (phase, stage) in enumerate(zip(PHASES, stages), 1):
        if (type(stage) is not dict or set(stage) != {"phase", "run_id", "run_ref", "scope_ref", "review_ref"}
                or stage["phase"] != phase):
            raise ValueError("D07 stage prefix is out of order")
        capture, answer = read_closed_phase(observer, runner, cursor, phase, stage["run_id"], stage["run_ref"])
        ids = {capture["sender_ack_id"]}
        if capture["reply"] is not None:
            ids.add(capture["reply"]["tester_reply_message_id"])
        if seen_ids.intersection(ids):
            raise ValueError("D07 tester message identity was reused across phases")
        seen_ids.update(ids)
        previous = None
        if items:
            prior = items[-1]
            if prior["semantic"] != "PASS" or prior["custody"] != "PASS":
                raise ValueError("D07 phase 2 requires independent phase-1 semantic and custody PASS")
            if capture["send_intent_at"] < prior["capture"]["original_deadline"]:
                raise ValueError("D07 phase 2 began before the original phase-1 deadline")
            if stage["scope_ref"] is None:
                raise ValueError("D07 phase 2 requires protected evidence of the same native lineage")
            previous = prior, prior_scope
        capture_sha = digest(observer.encoded(capture))
        item = {
            "capture": capture, "capture_sha256": capture_sha, "answer": answer,
            "scope": stage["scope_ref"], "review": stage["review_ref"],
            "criteria_sha256": digest(observer.encoded(oracle[f"op{index:03d}"])),
            "semantic": "OPEN", "custody": "OPEN",
        }
        if stage["scope_ref"] is not None:
            prior_scope = read_scope(observer, stage["scope_ref"], capture, capture_sha)
            validate_context(observer, capture, prior_scope, previous)
        if stage["review_ref"] is not None:
            item["semantic"], item["custody"] = independent_verdict(observer, stage["review_ref"], item)
        items.append(item)

    for item in items:
        capture = item["capture"]
        pinned_record(observer, capture["run"], expected_path=store.run_path(capture["run_id"]))
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {"stages": items, "cursor": cursor_ref, "oracle_sha256": ORACLE_SHA256,
            "actual_native_reads": "OPEN", "formal_acceptance": "OPEN"}
