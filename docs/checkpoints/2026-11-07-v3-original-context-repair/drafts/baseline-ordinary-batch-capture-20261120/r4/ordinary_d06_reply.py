"""Assess the saved response to the exact separate D06 DOCX edit."""

from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from types import ModuleType

from ordinary_d03_reply import original_ack, pinned_bytes, pinned_record, retained_text
from ordinary_d11_reply import DOCX_MIME, read_saved_docx


SCENARIO_SHA256 = "037d89d7d315c017172d653ca59670c05b97130f4f8782154e67b854b40d7cb0"
SOURCE_SHA256 = "72d6eceb0a2c47b7737d1e93dca52c968df734e01ac6a10e08f036d4cedcfff0"
ORACLE_SHA256 = "aba44cfcb05cf8778776076b02205e351915868e3c6818ccf5c0fb5eb85fd564"
REFERENCE_SHA256 = "76d15cbaaebe7e0ed955f4bf5dbe36ce09101bb8679d2f7786b60b10647375c6"
WRITER_SHA256 = "2e718074e3309b519d391a9688d8735fdbd469bee8d267b7482309bb8d84c8fd"
OUTPUT = {"filename": "D06-Cedar-Delivery-Edited.docx", "mime_type": DOCX_MIME}


def digest(raw):
    return sha256(raw).hexdigest()


def review_docx(observer, upload, raw, oracle_path):
    original = observer.read_document_input(upload, lambda: None)
    if len(original) != 4606 or digest(original) != SOURCE_SHA256:
        raise ValueError("D06 original DOCX bytes changed")
    path = Path(oracle_path)
    source = observer.safe_read(path, 65536)
    if digest(source) != ORACLE_SHA256:
        raise ValueError("Exact D06 byte-delta checker required")
    oracle = ModuleType("_pinned_d06_byte_delta")
    oracle.__file__ = str(path)
    exec(compile(source, oracle.__file__, "exec"), vars(oracle))
    basis = oracle.canonical_source(original)
    try:
        result = oracle.verify(basis, raw)
    except oracle.Rejection as error:
        return {"status": "FAIL", "reason": str(error)}
    except (LookupError, ValueError):
        return {"status": "FAIL", "reason": "MALFORMED_DOCX_XML"}
    if (result["source_sha256"] != SOURCE_SHA256 or result["saved_sha256"] != digest(raw)
            or result["saved_bytes"] != len(raw)):
        raise ValueError("D06 checker assessed different bytes")
    return result


def writer_evidence(observer, download, reference):
    if reference is None or (download["bytes"], download["sha256"]) != (4611, REFERENCE_SHA256):
        return {"state": "OPEN"}
    raw = pinned_bytes(observer, reference)
    if digest(raw) != WRITER_SHA256:
        raise ValueError("Exact reusable D06 Writer observation required")
    proof = json.loads(raw, object_pairs_hook=observer.unique_object)
    if (proof["state"] != "ISOLATED_LOCAL_D06_WRITER_PAIR_PASS"
            or proof["inputs"]["original"]["sha256"] != SOURCE_SHA256
            or proof["inputs"]["reference"]["sha256"] != download["sha256"]
            or proof["docx_save_calls"] != 0 or proof["both_loaded_read_only"] is not True
            or proof["host_and_staged_inputs_unchanged"] is not True):
        raise ValueError("D06 Writer observation does not bind the unchanged exact pair")
    return {"state": "EXACT_BYTES_WRITER_OBSERVATION_REUSED",
            "observation_sha256": WRITER_SHA256, "pages": proof["visible_pages"]}


def assess_saved_edit(observer, store, *, run_id, run_ref, cursor_ref, oracle_path, writer_ref=None):
    """Check receiver bytes from the original closed window; keep native and formal evidence open."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D06 saved run ID required")
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, expected_path=run_path)
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    scenario = run["scenario"]
    if (run.get("id") != run_id or run.get("scenario_sha256") != SCENARIO_SHA256
            or digest(observer.encoded(scenario)) != SCENARIO_SHA256
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("send_state") != "sent" or run.get("sent_ids") != [run.get("sent_message_id")]
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D06 edit run and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - scenario["deadline_seconds"]) > 1):
        raise ValueError("D06 original tester deadline changed")
    step = scenario["steps"][0]
    upload = step["input"]
    if upload["sha256"] != SOURCE_SHA256 or run["request_metadata"].get("input_sha256") != SOURCE_SHA256:
        raise ValueError("Exact D06 source upload required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    if not observer.valid_input_ack(ack, upload, require_document_size=True):
        raise ValueError("D06 original ACK upload size differs or is unobserved")
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D06 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D06 saved outcome differs from the retained observations")
    texts = []
    for item in observations:
        if item["kind"] == "reply_text":
            body, receipt = retained_text(observer, runner, run, item, captures, ack)
            texts.append(dict(receipt, text=body.decode("utf-8")))
    documents = [item for item in observations if item["kind"] == "document"]
    document, content, writer = None, {"status": outcome}, {"state": "OPEN"}
    if observations:
        failures = observer.ordinary_document_output_failures(OUTPUT, documents)
        if len(documents) == 1:
            item = documents[0]
            size = item.get("bytes")
            if type(size) is not int or not 0 < size <= step["observe"]["document_max_bytes"]:
                failures.append("DOCUMENT_OUTSIDE_ORIGINAL_SIZE_BOUND")
            else:
                raw, document = read_saved_docx(observer, runner, run, item, captures, ack)
                if not failures:
                    content = review_docx(observer, upload, raw, oracle_path)
                    if content["status"] == "PASS":
                        writer = writer_evidence(observer, document["download"], writer_ref)
        if failures:
            content = {"status": "FAIL", "conditions": failures}
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "send_ack": run["sent_api_ack_reference"], "send_window": run["sent_window_reference"],
        "send_task": run["sent_task_reference"], "sent_message_id": run["sent_message_id"],
        "receive_head": run["receive_head"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"],
        "recipient_docx": document, "direct_text_replies": texts, "receiver_screen": content,
        "explicit_refusal_observed": run.get("refusal_observed") is True,
        "writer_observation": writer, "native_read_edit_delivery": "OPEN", "formal_acceptance": "OPEN",
    }
