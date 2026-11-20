"""Evaluate protected, already-closed D03 R4 captures in stage order."""

from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from types import ModuleType

PHASES = {
    "D-03-01": ("5f79d4fa5b2d268e74025329f19af05c02c29348cc9d44fa7f40c5baf232d9bd",
                "23c9df7fe3c1646729ec796e1673c3759fad763175d4b0f853a9f73cf4ba3fde", 934),
    "D-03-02": ("561071dc68cf0ee63a2b9893aec67c92ff3e32b0dd3718c848c0f78178f94131",
                "b8af75e9c7c5071f072c01c42a54618fd2deb7c20f46177175adc7845fe7de3d", 788),
    "D-03-03": ("d7871d061467b2a3067470f18de4e59a2373c0ff7cfed4d4facb08e89f78ab18",
                "9ea3f46573f194a4d92dadc01906f0adc75d27d6013478deff6710461b68ce9a", 456),
}
R4_SHA256 = "44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd"
ORACLE_SHA256 = "4cd84ffb072ac3981a5e4a289a5957cadba47a47891329ce53d8538f7cf73a2e"
REVIEW_SCHEMA = "frw.root.d03-staged-reply-review.v1"
MAX_JSON = 2 * 1024**2
MEDIA = {
    "animation", "audio", "contact", "dice", "document", "game", "invoice", "location",
    "paid_media", "passport_data", "photo", "poll", "sticker", "story", "successful_payment",
    "venue", "video", "video_note", "voice",
}


def digest(body):
    return sha256(body).hexdigest()


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def observer_from_source(source_bytes):
    """Load the exact R4 source without running its CLI or creating a Store."""
    if type(source_bytes) is not bytes or digest(source_bytes) != R4_SHA256:
        raise ValueError("Exact D03 R4 observer source required")
    module = ModuleType("_d03_owned_r4")
    exec(compile(source_bytes, "pinned-r4.py", "exec"), module.__dict__)
    return module


def pinned_bytes(observer, reference, *, expected_path=None):
    if (type(reference) is not dict or set(reference) != {"path", "bytes", "sha256"}
            or type(reference["path"]) is not str or type(reference["bytes"]) is not int
            or not 0 < reference["bytes"] <= MAX_JSON or not valid_sha(reference["sha256"])):
        raise ValueError("Exact sized D03 reference required")
    path = Path(reference["path"])
    if (not path.is_absolute() or ".." in path.parts or str(path) != reference["path"]
            or expected_path is not None and path != expected_path):
        raise ValueError("D03 reference path changed")
    raw = observer.safe_read(path, reference["bytes"])
    if len(raw) != reference["bytes"] or digest(raw) != reference["sha256"]:
        raise ValueError("D03 protected reference bytes changed")
    return raw


def pinned_record(observer, reference, *, expected_path=None):
    raw = pinned_bytes(observer, reference, expected_path=expected_path)
    record = json.loads(raw, object_pairs_hook=observer.unique_object)
    if type(record) is not dict or observer.encoded(record) != raw:
        raise ValueError("Canonical D03 record required")
    return record


def advertised_document_matches(document, expected):
    return type(document) is dict and all(
        type(document[key]) is type(value) and document[key] == value
        for key, value in expected.items() if key in document
    )


def original_ack(observer, runner, run):
    ref = run["sent_api_ack_reference"]
    read_ref = {key: ref[key] for key in ("basename", "bytes", "sha256")}
    ack = runner.read_reference(read_ref, f"send-ack-{run['id']}-0-1.json")
    representation = ref["representation"]
    if representation == "botapi-wire-envelope-json" and ack.get("ok") is True:
        ack = ack["result"]
    elif representation != "decoded-message-json":
        raise ValueError("Unknown D03 acknowledgement representation")
    scenario = run["scenario"]
    upload = scenario["steps"][0]["input"]
    if (ack.get("message_id") != run["sent_message_id"] or ack.get("date") != run["sent_date"]
            or ack.get("chat", {}).get("id") != scenario["peer_id"] or ack["chat"].get("type") != "private"
            or ack.get("from", {}).get("id") != scenario["tester_id"] or ack["from"].get("is_bot") is not True
            or ack.get("message_thread_id") is not None or ack.get("is_topic_message") is True
            or not observer.valid_input_ack(ack, upload)):
        raise ValueError("D03 original document ACK or tester route differs")
    if not advertised_document_matches(ack["document"], {
        "file_name": upload["filename"], "mime_type": upload["mime_type"],
    }):
        raise ValueError("D03 original ACK document name or MIME differs")
    return ack


def retained_text(observer, runner, run, observation, captures, ack):
    uid = observation["update_id"]
    update, arrival = runner.committed_capture(run, uid)
    message = update["message"]
    parent = message.get("reply_to_message")
    peer = run["scenario"]["peer_id"]
    if (observation.get("kind") != "reply_text" or observation.get("text_source") not in (None, "text")
            or captures.get(uid) != arrival or arrival["raw_update"] != observation["raw_update"]
            or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
            or update["update_id"] != uid or message["message_id"] != observation["message_id"]
            or message["chat"].get("id") != peer or message["chat"].get("type") != "private"
            or message["from"].get("id") != peer or message["from"].get("is_bot") is not True
            or type(parent) is not dict or parent.get("message_id") != ack["message_id"]
            or "date" in parent and parent["date"] != ack["date"]
            or "from" in parent and (parent["from"].get("id") != ack["from"]["id"]
                                     or parent["from"].get("is_bot") is not True)
            or "chat" in parent and (parent["chat"].get("id") != peer
                                     or parent["chat"].get("type") != "private")
            or any(msg.get("message_thread_id") is not None or msg.get("is_topic_message") is True
                   for msg in (message, parent))
            or not run["sent_date"] <= message["date"] <= run["capture_until"]
            or MEDIA.intersection(message) or type(message.get("text")) is not str):
        raise ValueError("D03 requires direct private text to the original ACK within its window")
    upload = run["scenario"]["steps"][0]["input"]
    expected_document = {
        "file_name": upload["filename"], "mime_type": upload["mime_type"],
        "file_size": upload["stat"]["size_bytes"], "file_unique_id": ack["document"]["file_unique_id"],
    }
    if (("caption" in parent and not observer.caption_ack_matches(parent["caption"], upload["caption"]))
            or ("document" in parent and not advertised_document_matches(parent["document"], expected_document))):
        raise ValueError("D03 reply parent conflicts with the original upload")
    body = message["text"].encode("utf-8")
    if digest(body) != observation["text_sha256"] or message["text"] != observation["text"]:
        raise ValueError("D03 reply text changed after receipt")
    return body, {
        "tester_reply_message_id": message["message_id"], "tester_update_id": uid,
        "text_sha256": observation["text_sha256"], "raw_update": observation["raw_update"],
        "text_receipt": {key: observation["receipt_" + key] for key in ("path", "bytes", "sha256")},
    }


def read_retained_stage(observer, store, *, phase, run_id, run_ref, cursor_ref):
    """Read only the addressed stage's committed recipient text and original clock."""
    if phase not in PHASES or type(run_id) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D03 phase and run ID required")
    scenario_sha, source_sha, source_bytes = PHASES[phase]
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, expected_path=run_path)
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    if (run.get("id") != run_id or run.get("scenario_sha256") != scenario_sha
            or digest(observer.encoded(run["scenario"])) != scenario_sha
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or type(run.get("sent_message_id")) is not int or run["sent_message_id"] <= 0
            or run.get("sent_ids") != [run["sent_message_id"]] or run.get("send_state") != "sent"
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True
            or run.get("reply_outcome") not in ("RECEIVED_UNGRADED", "NO_RESPONSE_UNVERIFIED")
            or run["request_metadata"].get("input_sha256") != source_sha
            or run["request_metadata"].get("input_bytes") != source_bytes):
        raise ValueError("Exact closed D03 phase and one acknowledged upload required")
    created = datetime.fromisoformat(run["created_at"])
    deadline = run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D03 original tester deadline does not match 300 seconds")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    terminal = drain.get("complete")
    if terminal is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D03 original receive window is unsettled")
    observations = run["observations"]
    if not observations or run["reply_outcome"] != "RECEIVED_UNGRADED":
        raise ValueError("D03 original window has no retained text reply")
    ids = [observation["update_id"] for observation in observations]
    if ids != sorted(set(ids)):
        raise ValueError("Exact ordered D03 text observations required")
    replies = [retained_text(observer, runner, run, observation, captures, ack) for observation in observations]
    for _, meta in replies:
        receipt = meta["text_receipt"]
        expected = store.downloads / f"{run_id}-{meta['tester_reply_message_id']}-{meta['text_sha256']}.text-receipt.json"
        pinned_record(observer, receipt, expected_path=expected)
    answer = b"\n".join(body for body, _ in replies)
    if not answer.decode("utf-8").strip():
        raise ValueError("No substantive saved D03 text")
    capture = {
        "phase": phase, "run_id": run_id, "scenario_sha256": scenario_sha, "run": run_ref,
        "tester_sent_message_id": run["sent_message_id"], "send_intent_at": run["send_intent_at"],
        "send_dispatch_at": run["send_dispatch_at"], "sent_at": run["sent_at"],
        "capture_until": run["capture_until"], "original_deadline": run["deadline"],
        "terminal_completed_at": terminal["completed_at"], "receive_head": run["receive_head"],
        "source_sha256": source_sha, "source_bytes": source_bytes,
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"],
        "response_sha256": digest(answer), "replies": [meta for _, meta in replies],
    }
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return capture, answer


def factual_signals(phase, answer):
    """Report literal signals for the independent reviewer, with no semantic verdict."""
    text = answer.decode("utf-8").casefold()

    def october(day):
        return (
            rf"(?<![\d./-])(?:2026-10-{day}|{day}(?:"
            rf"\s*(?:октябр\w*|oct(?:ober)?\b)(?:\s+2026\b|(?!\s+\d))"
            rf"|[./-]10(?:[./-]2026\b|(?![./-]\d))))(?!\d)"
        )

    facts = {
        "project_id": r"(?<!\w)mayak[-‑–]042(?!\w)",
        "original_budget": r"(?<!\d)95[ \u00a0\u202f,._]?000(?!\d)",
        "amended_budget": r"(?<!\d)104[ \u00a0\u202f,._]?500(?!\d)",
        "effective_date": october(16),
        "original_deadline": october(22),
        "amended_deadline": october(23),
        "addendum_term": r"\b(?:дополнени\w*|addendum|v2)\b",
        "earlier_note_term": r"\b(?:заметк\w*|черновик\w*|draft|note)\b",
    }
    early = {"D-03-01": ("amended_budget", "amended_deadline", "effective_date", "addendum_term", "earlier_note_term"),
             "D-03-02": ("earlier_note_term",)}
    selected = early.get(phase, tuple(facts))
    return {key: bool(re.search(facts[key], text)) for key in selected}


def review_stage(observer, oracle, capture, answer, reference, previous):
    capture_sha = digest(observer.encoded(capture))
    outcome = {"capture": capture, "capture_sha256": capture_sha,
               "literal_signals": factual_signals(capture["phase"], answer),
               "criteria": "UNVERIFIED_INDEPENDENT_EVIDENCE", "review": reference,
               "scope_sha256": None, "formal_acceptance": "OPEN"}
    if reference is None:
        return outcome

    review = pinned_record(observer, reference)
    if (set(review) != {"schema", "capture_sha256", "scope_sha256", "predecessor", "evidence", "criteria"}
            or review["schema"] != REVIEW_SCHEMA or review["capture_sha256"] != capture_sha
            or not valid_sha(review["scope_sha256"])
            or type(review["criteria"]) is not dict
            or review["criteria"].get("response_sha256") != capture["response_sha256"]):
        raise ValueError("Independent D03 review does not bind the exact response")
    predecessor = review["predecessor"]
    evidence = review["evidence"]
    required_refs = {"native_ingress", "staged_scope_and_absence", "independent_review"}
    if previous is not None:
        required_refs.add("ordered_release")
    if type(evidence) is not dict or set(evidence) != required_refs:
        raise ValueError("Exact D03 independent evidence references required")
    for record in evidence.values():
        pinned_bytes(observer, record)

    admitted = None
    if previous is None:
        if predecessor is not None:
            raise ValueError("D03 first phase has an unexpected predecessor")
    else:
        if (type(predecessor) is not dict
                or set(predecessor) != {"capture_sha256", "review_sha256", "verified_before_send"}
                or predecessor["capture_sha256"] != previous["capture_sha256"]
                or previous["review"] is None or predecessor["review_sha256"] != previous["review"]["sha256"]
                or type(predecessor["verified_before_send"]) is not bool):
            raise ValueError("D03 successor review does not bind the exact predecessor review")
        if previous["scope_sha256"] != review["scope_sha256"]:
            raise ValueError("D03 successor changed scope")
        admitted = {"phase": previous["capture"]["phase"], "criteria": previous["criteria"],
                    "same_dialog_predecessor_receipt_verified": predecessor["verified_before_send"]}
    outcome["scope_sha256"] = review["scope_sha256"]
    outcome["criteria"] = oracle["classify"](capture["phase"], answer, review["criteria"], admitted)
    return outcome


def evaluate_saved_series(observer, store, *, stages, cursor_ref, oracle_path):
    """Evaluate an ordered prefix using exact Root-selected protected review references.

    The reader validates proof bytes and joins. Root and the independent reviewer
    establish the meaning and authority of the native scope and semantic witnesses.
    This function returns evidence and never emits admission or a new send.
    """
    if type(stages) not in (tuple, list) or not 1 <= len(stages) <= len(PHASES):
        raise ValueError("Exact D03 stage prefix required")
    oracle_path = Path(oracle_path)
    if not oracle_path.is_absolute() or ".." in oracle_path.parts:
        raise ValueError("Exact D03 oracle path required")
    raw = observer.safe_read(oracle_path, 65536)
    if digest(raw) != ORACLE_SHA256:
        raise ValueError("Exact existing D03 oracle required")
    oracle = {"__name__": "_d03_oracle", "__file__": str(oracle_path)}
    exec(compile(raw, str(oracle_path), "exec"), oracle)
    if tuple(PHASES) != oracle["PHASES"]:
        raise ValueError("D03 oracle phase order changed")

    results = []
    seen_message_ids = set()
    for phase, stage in zip(PHASES, stages):
        if (type(stage) is not dict or set(stage) != {"phase", "run_id", "run_ref", "review_ref"}
                or stage["phase"] != phase):
            raise ValueError("D03 stage prefix is out of order")
        capture, answer = read_retained_stage(observer, store, phase=phase, run_id=stage["run_id"],
                                              run_ref=stage["run_ref"], cursor_ref=cursor_ref)
        ids = [capture["tester_sent_message_id"], *(row["tester_reply_message_id"] for row in capture["replies"])]
        if len(ids) != len(set(ids)) or seen_message_ids.intersection(ids):
            raise ValueError("D03 tester message identity was reused")
        seen_message_ids.update(ids)
        if results and min(capture["send_intent_at"], capture["send_dispatch_at"]) < results[-1]["capture"]["original_deadline"]:
            raise ValueError("D03 successor precedes original predecessor closure")
        results.append(review_stage(observer, oracle, capture, answer, stage["review_ref"],
                                    results[-1] if results else None))
    return {"stages": results, "cursor": cursor_ref,
            "reviewed_criteria_all_three": len(results) == len(PHASES) and all(
                item["criteria"] == "CRITERIA_SATISFIED" for item in results),
            "formal_acceptance": "OPEN"}
