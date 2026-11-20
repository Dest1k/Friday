"""Evaluate the saved, exact D09 translation without reissuing its request."""

from datetime import datetime
from hashlib import sha256
import json
from lzma import LZMAError
import math
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import ModuleType

from ordinary_d03_reply import original_ack, pinned_bytes, pinned_record, retained_text
from ordinary_d11_reply import DOCX_MIME, read_saved_docx


SCENARIO_SHA256 = "c8b18c77a422fba386b1f52dd68c7e66ab8761e02bf45135666a1e30e125c0e9"
SOURCE_SHA256 = "5193d619f07521188c5f73272f41c5ce616dbd0b0712964766a51888f63fdc56"
ORACLE_SHA256 = "0b43a40dc783a87a1556a4fca2da7fd48bc6e5002386a373b8e2463b68a45ec9"
COMPONENT_SHA256 = "12d08cec055ff01fa5d99eeb4949609aafb57c238d8072aef6bae4d5e8297d64"
WRITER_SHA256 = "4b4b732a77ff401e0240007ecc1c40c964d797e1df2b48a8e64d94f425356215"
OUTPUT_NAME = "D09-Orbit-English.docx"


def digest(data):
    return sha256(data).hexdigest()


def check_anchor_position(oracle, helper, roots):
    """Screen the physical target omitted by the checker's filtered body order."""
    body = roots[oracle.MAIN].find(oracle.W + "body")
    start_tag, end_tag = oracle.W + "bookmarkStart", oracle.W + "bookmarkEnd"
    named = [node for tree in roots.values() for node in tree.iter(start_tag)
             if node.get(oracle.W + "name") == oracle.BOOKMARK]
    if len(named) != 1:
        return {"status": "REVIEW_REQUIRED", "reason": "AMBIGUOUS_NAMED_BOOKMARK"}
    start = named[0]
    end = next(body.iter(end_tag))
    index = next(i for i, paragraph in enumerate(body) if start in paragraph)
    # The checked surrounding text roles are Schedule and shipment. Check their
    # physical adjacency and the empty range, including non-text Word elements.
    if (list(body[index]) != [start, end] or not 0 < index < len(body) - 1
            or not all(node.tag == oracle.W + "p" and helper.paragraph_text(node).strip()
                       for node in (body[index - 1], body[index + 1]))):
        return {"status": "REVIEW_REQUIRED", "reason": "BOOKMARK_POSITION_OR_LAYOUT_CHANGED"}
    return {"status": "PASS", "target": oracle.BOOKMARK, "directly_between_schedule_and_shipment": True}


def assess_docx(observer, source, report, oracle_path, scratch):
    raw = observer.safe_read(oracle_path, 65536)
    if digest(raw) != ORACLE_SHA256:
        raise ValueError("Exact D09 translation checker required")
    oracle = ModuleType("_pinned_d09_translation_checker")
    oracle.__file__ = str(oracle_path)
    exec(compile(raw, oracle.__file__, "exec"), vars(oracle))
    helper_path = oracle.D04_PATH
    helper_raw = observer.safe_read(helper_path, 65536)
    if digest(helper_raw) != oracle.D04_SHA256:
        raise ValueError("Exact D09 checker dependency required")
    helper = ModuleType("_pinned_d04_package_reader")
    helper.__file__ = str(helper_path)
    exec(compile(helper_raw, helper.__file__, "exec"), vars(helper))
    oracle.load_d04 = lambda: helper
    with TemporaryDirectory(prefix="d09-receiver-", dir=observer.secure_dir(Path(scratch))) as directory:
        original, translation = Path(directory) / "source.docx", Path(directory) / OUTPUT_NAME
        for path, data in ((original, source), (translation, report)):
            with path.open("xb") as stream:
                stream.write(data)
        try:
            result = oracle.check_translation(original, translation, source_sha256=SOURCE_SHA256)
            roots, _, _, anchor_docx_sha = oracle.read_package(translation, "translated", helper)
        except oracle.Refused as error:
            detail = str(error)
            if detail.startswith(("source", "verifier")):
                raise ValueError("D09 checker refused its pinned source or dependency") from error
            # The known English patterns do not decide every valid translation.
            state = "REVIEW_REQUIRED" if detail.startswith("translation ") else "FAIL"
            return {"status": state, "reason": detail}
        except (LZMAError, EOFError):
            return {"status": "FAIL", "reason": "Malformed DOCX archive"}
    if result["source_sha256"] != SOURCE_SHA256 or not result["candidate_sha256"] == anchor_docx_sha == digest(report):
        raise ValueError("D09 checker assessed different bytes")
    anchor = check_anchor_position(oracle, helper, roots)
    result["physical_bookmark_position"] = anchor
    if anchor["status"] != "PASS":
        result = {**result, **anchor}
    return result


def writer_evidence(observer, recipient, reference):
    if reference is None or (recipient["bytes"], recipient["sha256"]) != (7502, COMPONENT_SHA256):
        return {"state": "OPEN"}
    raw = pinned_bytes(observer, reference)
    if digest(raw) != WRITER_SHA256:
        raise ValueError("Exact reusable D09 Writer observation required")
    proof = json.loads(raw, object_pairs_hook=observer.unique_object)
    if proof["input_sha256"] != recipient["sha256"] or proof["native_save_calls"] != 0:
        raise ValueError("D09 Writer observation does not bind the unchanged recipient bytes")
    return {
        "state": "EXACT_BYTES_WRITER_OBSERVATION_REUSED",
        "observation_sha256": WRITER_SHA256,
        "pages": proof["page_count"],
        "rendered_internal_link": proof["rendered_internal_link"],
    }


def assess_saved_translation(observer, store, *, run_id, run_ref, cursor_ref, oracle_path, scratch, writer_ref=None):
    """Assess receiver content and reuse any Writer finding only on the same bytes."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D09 run ID required")
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
        raise ValueError("Exact closed D09 run and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D09 original tester deadline does not match 300 seconds")
    upload = scenario["steps"][0]["input"]
    if run["request_metadata"].get("input_sha256") != SOURCE_SHA256 or upload["sha256"] != SOURCE_SHA256:
        raise ValueError("Exact D09 source upload required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D09 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D09 saved outcome differs from the retained observations")
    texts = []
    for item in observations:
        if item["kind"] == "reply_text":
            body, receipt = retained_text(observer, runner, run, item, captures, ack)
            texts.append(dict(receipt, text=body.decode("utf-8")))
    documents = [item for item in observations if item["kind"] == "document"]
    if len(documents) > 1:
        raise ValueError("D09 closed evidence exceeds its original artifact cap")
    content, writer, document = {"status": outcome}, {"state": "OPEN"}, None
    if documents:
        raw, document = read_saved_docx(observer, runner, run, documents[0], captures, ack)
        if document["name"] != OUTPUT_NAME or documents[0]["advertised_document"].get("mime_type") != DOCX_MIME:
            content = {"status": "FAIL", "reason": "EXPECTED_EXACT_DOCX_NAME_AND_MIME"}
        else:
            source = observer.read_document_input(upload, lambda: None)
            if len(source) != 7834 or digest(source) != SOURCE_SHA256:
                raise ValueError("D09 source bytes changed")
            content = assess_docx(observer, source, raw, Path(oracle_path), scratch)
            writer = writer_evidence(observer, document["download"], writer_ref)
    elif observations:
        content = {"status": "FAIL", "reason": "EXPECTED_ONE_DOCX"}
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "send_ack": run["sent_api_ack_reference"], "send_window": run["sent_window_reference"],
        "send_task": run["sent_task_reference"], "sent_message_id": run["sent_message_id"],
        "receive_head": run["receive_head"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"],
        "recipient_docx": document, "direct_text_replies": texts,
        "explicit_refusal_observed": run.get("refusal_observed") is True,
        "receiver_screen": content, "writer_observation": writer,
        "native_delivery": "OPEN", "independent_translation_review": "OPEN", "formal_acceptance": "OPEN",
    }
