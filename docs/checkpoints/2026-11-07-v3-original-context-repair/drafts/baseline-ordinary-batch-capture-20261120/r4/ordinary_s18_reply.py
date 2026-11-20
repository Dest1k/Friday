"""Assess the saved workbook from the exact separate S18 edit."""

from datetime import datetime
from decimal import InvalidOperation
from hashlib import sha256
import math
from pathlib import Path
import re
from types import ModuleType
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError
from zlib import error as DeflateError

from ordinary_d03_reply import MEDIA, original_ack, pinned_record, retained_text
from ordinary_d11_reply import read_saved_document
from ordinary_s11_reply import direct_attachment_count, direct_reply_update_ids


SCENARIO_SHA256 = "b6bee941754be8f60f3d8b57ce3ad85e5044c760ffe397a418f4077f3ff19b9c"
SOURCE_SHA256 = "53de76c147a52a42594b74a2d36190dd712ee7a7fcbf58ab93e86a2f149d6251"
ORACLE_SHA256 = "bf42cfbc4911f6e33a2b1c4607970440dbc529d6d461ccc2f762e42e710e0c67"
OUTPUT_NAME = "S18-Cedar-Ledger-Edited.xlsx"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
NATIVE_MAX_BYTES = 1_000_000


def digest(raw):
    return sha256(raw).hexdigest()


def check_observation_paths(store, run_id, observations, label):
    for item in observations:
        kind = item.get("kind")
        if kind not in ("reply_text", "document"):
            raise ValueError(f"{label} unknown closed receiver observation")
        message_id = item.get("message_id")
        key = "sha256" if kind == "document" else "text_sha256"
        pin = item.get(key)
        if (type(message_id) is not int or message_id <= 0
                or type(pin) is not str or not re.fullmatch("[0-9a-f]{64}", pin)):
            raise ValueError(f"{label} exact receiver observation identity required")
        basename = store.downloads / f"{run_id}-{message_id}-{pin}"
        suffix = ".receipt.json" if kind == "document" else ".text-receipt.json"
        if (item.get("receipt_path") != str(basename) + suffix
                or (kind == "document" and item.get("path") != str(basename) + ".bin")):
            raise ValueError(f"{label} receiver file is outside its exact Store path")


def review_workbook(observer, upload, raw, oracle_path):
    original = observer.read_document_input(upload, lambda: None)
    if len(original) != 4010 or digest(original) != SOURCE_SHA256:
        raise ValueError("S18 original workbook bytes changed")
    path = Path(oracle_path)
    source = observer.safe_read(path, 65536)
    if digest(source) != ORACLE_SHA256:
        raise ValueError("Exact S18 workbook checker required")
    oracle = ModuleType("_pinned_s18_workbook_checker")
    oracle.__file__ = str(path)
    exec(compile(source, oracle.__file__, "exec"), vars(oracle))
    try:
        result = oracle.verify(original, raw, SOURCE_SHA256)
    except oracle.CheckError as error:
        return {"status": "FAIL", "reason": str(error)}
    except (OSError, ParseError, ExpatError, DeflateError, EOFError, InvalidOperation, LookupError, ValueError):
        return {"status": "FAIL", "reason": "MALFORMED_XLSX_PACKAGE"}
    if (result["saved_byte_check"] != "PASS" or result["source_sha256"] != SOURCE_SHA256
            or result["candidate_sha256"] != digest(raw)):
        raise ValueError("S18 checker assessed different bytes")
    return {"status": "PASS", **result}


def assess_closed_workbook_reply(observer, store, *, run_id, run_ref, cursor_ref, label,
                                 scenario_sha, source_sha, output_name, assess_content, allow_separate_text=False):
    """Join the exact upload and its bounded direct XLSX response before checking content."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError(f"Exact {label} run ID required")
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, expected_path=run_path)
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    scenario = run["scenario"]
    if (run.get("id") != run_id or run.get("scenario_sha256") != scenario_sha
            or digest(observer.encoded(scenario)) != scenario_sha
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("sent_ids") != [run.get("sent_message_id")] or run.get("send_state") != "sent"
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError(f"Exact closed {label} run and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - scenario["deadline_seconds"]) > 1):
        raise ValueError(f"{label} original tester deadline changed")
    step = scenario["steps"][0]
    upload = step["input"]
    if upload["sha256"] != source_sha or run["request_metadata"].get("input_sha256") != source_sha:
        raise ValueError(f"Exact {label} source upload required")
    observations = run["observations"]
    check_observation_paths(store, run_id, observations, label)

    runner = observer.Runner(store, None)
    if runner.send_ack_budget(run) != 10:
        raise ValueError(f"{label} original tester ACK budget changed")
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    if not observer.valid_input_ack(ack, upload, require_document_size=True):
        raise ValueError(f"{label} original ACK upload size differs or is unobserved")
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError(f"{label} original receive window is unsettled")
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError(f"{label} saved outcome differs from the retained observations")

    text_bodies, text_receipts, documents = [], [], []
    for item in observations:
        if item["kind"] == "reply_text":
            body, receipt = retained_text(observer, runner, run, item, captures, ack)
            text_bodies.append(body)
            text_receipts.append(receipt)
        else:
            documents.append(item)
    if allow_separate_text:
        raw_text_ids = direct_reply_update_ids(
            observer, runner, run, captures, ack,
            contains=lambda msg: type(msg.get("text")) is str and not MEDIA.intersection(msg),
        )
        if set(raw_text_ids) != {receipt["tester_update_id"] for receipt in text_receipts}:
            raise ValueError(f"{label} direct text is missing its exact closed receipt")
    attachments = direct_attachment_count(observer, runner, run, captures, ack)
    recipient, screen = None, {"status": outcome}
    text_limit = 1 if allow_separate_text else 0
    if observations or attachments:
        if len(documents) != 1 or attachments != 1 or len(text_receipts) > text_limit:
            screen = {"status": "FAIL", "reason": "EXPECTED_ONE_DIRECT_XLSX_REPLY"}
        else:
            item = documents[0]
            limit = min(step["observe"]["document_max_bytes"], NATIVE_MAX_BYTES)
            size = item.get("bytes")
            if type(size) is not int or not 0 < size <= limit:
                screen = {"status": "FAIL", "reason": "XLSX_OUTSIDE_NATIVE_DELIVERY_BOUND"}
            else:
                raw, recipient = read_saved_document(observer, runner, run, item, captures, ack,
                                                      max_bytes=limit, label=f"{label} recipient XLSX")
                if recipient["name"] != output_name or item["advertised_document"].get("mime_type") != XLSX_MIME:
                    screen = {"status": "FAIL", "reason": "EXPECTED_EXACT_XLSX_NAME_AND_MIME"}
                elif allow_separate_text:
                    screen = assess_content(upload, raw, recipient, text_bodies)
                else:
                    screen = assess_content(upload, raw, recipient)
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": scenario_sha,
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"], "sent_message_id": run["sent_message_id"],
        "receive_head": run["receive_head"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"], "recipient_xlsx": recipient,
        "direct_text_receipts": text_receipts, "receiver_screen": screen,
    }


def assess_saved_workbook_edit(observer, store, *, run_id, run_ref, cursor_ref, oracle_path):
    """Check the exact bounded receiver artifact. Calc and native verification stay separate."""
    evidence = assess_closed_workbook_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S18",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, output_name=OUTPUT_NAME,
        assess_content=lambda upload, raw, _ref: review_workbook(observer, upload, raw, oracle_path),
    )
    return {**evidence, "native_read_edit_delivery": "OPEN", "calc_same_received_bytes": "OPEN",
            "formal_acceptance": "OPEN"}
