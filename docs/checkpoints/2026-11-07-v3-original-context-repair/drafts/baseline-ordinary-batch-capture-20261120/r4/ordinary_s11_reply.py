"""Assess the one retained text response to the separate S11 XLSX read."""

from datetime import datetime
from hashlib import sha256
import math
from pathlib import Path
import re

from ordinary_d03_reply import MEDIA, advertised_document_matches, original_ack, pinned_record, retained_text


SCENARIO_SHA256 = "0909a9722fad7e64f4d51099c1e504f0daf19166db30ad700d772bb91b7789ad"
SOURCE_SHA256 = "642238cb4543087bef5b55c379110a59e37c0ae10e28fb958d2b32bc53b1f21e"
ORACLE_SHA256 = "233480711f065742bf72b7322e016c4c5f2c0759edf73670282458a7ce638e35"
CONTRACT_SHA256 = "ebc42547b8de62080dc0d71d0719a6f8134b5905e36aca4f0f20790055995b78"


def digest(raw):
    return sha256(raw).hexdigest()


def load_pinned_checker(observer, path, pin, name):
    path = Path(path)
    raw = observer.safe_read(path, 65536)
    if digest(raw) != pin:
        raise ValueError(f"Exact pinned S11 {name} required")
    module = {"__name__": f"_s11_{name}", "__file__": str(path)}
    exec(compile(raw, str(path), "exec"), module)
    return module


def direct_attachment_count(observer, runner, run, captures, ack):
    """Check raw committed updates, including media the generic observer skips."""
    peer = run["scenario"]["peer_id"]
    upload = run["scenario"]["steps"][0]["input"]
    expected_document = {
        "file_name": upload["filename"], "mime_type": upload["mime_type"],
        "file_size": upload["stat"]["size_bytes"], "file_unique_id": ack["document"]["file_unique_id"],
    }
    count = 0
    for uid, arrival in captures.items():
        if not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]:
            continue
        update, committed_arrival = runner.committed_capture(run, uid)
        if committed_arrival != arrival:
            raise ValueError("S11 committed receive inventory changed")
        message = update.get("message")
        if not isinstance(message, dict) or not MEDIA.intersection(message):
            continue
        chat, sender, parent = (message.get(key) for key in ("chat", "from", "reply_to_message"))
        date = message.get("date")
        if (isinstance(chat, dict) and chat.get("id") == peer and chat.get("type") == "private"
                and isinstance(sender, dict) and sender.get("id") == peer and sender.get("is_bot") is True
                and isinstance(parent, dict) and parent.get("message_id") == ack["message_id"]
                and type(date) is int and run["sent_date"] <= date <= run["capture_until"]
                and all(row.get("message_thread_id") is None and row.get("is_topic_message") is not True
                        for row in (message, parent))):
            parent_sender, parent_chat = parent.get("from"), parent.get("chat")
            if ("date" in parent and parent["date"] != ack["date"]
                    or "from" in parent and (type(parent_sender) is not dict
                                              or parent_sender.get("id") != ack["from"]["id"]
                                              or parent_sender.get("is_bot") is not True)
                    or "chat" in parent and (type(parent_chat) is not dict or parent_chat.get("id") != peer
                                              or parent_chat.get("type") != "private")
                    or "caption" in parent and not observer.caption_ack_matches(parent["caption"], upload["caption"])
                    or "document" in parent and not advertised_document_matches(parent["document"], expected_document)):
                raise ValueError("Committed attachment parent conflicts with the original upload")
            count += 1
    return count


def assess_closed_text_reply(observer, store, *, run_id, run_ref, cursor_ref, label,
                             scenario_sha, source_sha, assess_content, require_ack_size=False):
    """Bind retained text to one closed ordinary document-upload operation."""
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
    upload = scenario["steps"][0]["input"]
    if upload["sha256"] != source_sha or run["request_metadata"].get("input_sha256") != source_sha:
        raise ValueError(f"Exact {label} source upload required")

    observations = run["observations"]
    for item in observations:
        message_id, text_sha = item.get("message_id"), item.get("text_sha256")
        if (item.get("kind") != "reply_text" or type(message_id) is not int or message_id <= 0
                or type(text_sha) is not str or not re.fullmatch("[0-9a-f]{64}", text_sha)):
            raise ValueError(f"{label} closed observations must be exact text receipts")
        receipt_path = store.downloads / f"{run_id}-{message_id}-{text_sha}.text-receipt.json"
        if item.get("receipt_path") != str(receipt_path):
            raise ValueError(f"{label} text receipt is outside its exact Store path")

    runner = observer.Runner(store, None)
    if runner.send_ack_budget(run) != 10:
        raise ValueError(f"{label} original tester ACK budget changed")
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    if require_ack_size and not observer.valid_input_ack(ack, upload, require_document_size=True):
        raise ValueError(f"{label} original upload size differs or is unobserved")
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError(f"{label} original receive window is unsettled")
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError(f"{label} saved outcome differs from the retained observations")
    texts, receipts = [], []
    for item in observations:
        raw, receipt = retained_text(observer, runner, run, item, captures, ack)
        texts.append(raw)
        receipts.append(receipt)
    attachment_count = direct_attachment_count(observer, runner, run, captures, ack)
    result = {"status": outcome}
    if observations or attachment_count:
        result = assess_content(upload, texts, attachment_count)
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": scenario_sha,
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"], "sent_message_id": run["sent_message_id"],
        "receive_head": run["receive_head"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"], "reply_records": receipts,
        "in_window_direct_attachment_count": attachment_count,
        "receiver_screen": result,
    }


def assess_saved_filter(observer, store, *, run_id, run_ref, cursor_ref, oracle_path, contract_path):
    """Grade the saved text against the exact uploaded XLSX under original custody."""
    def assess_content(upload, texts, attachment_count):
        workbook = observer.read_document_input(upload, lambda: None)
        if len(workbook) != 3030 or digest(workbook) != SOURCE_SHA256:
            raise ValueError("S11 original workbook bytes changed")
        oracle = load_pinned_checker(observer, oracle_path, ORACLE_SHA256, "oracle")
        contract = load_pinned_checker(observer, contract_path, CONTRACT_SHA256, "contract")
        expected = oracle["expected_reply"](workbook)
        try:
            contract["check_saved_response"](oracle, expected, direct_reply_bytes=texts,
                                               attachment_count=attachment_count)
        except ValueError as error:
            return {"status": "FAIL", "reason": str(error)}
        return {"status": "PASS", "source_sha256": SOURCE_SHA256}

    evidence = assess_closed_text_reply(
        observer, store, run_id=run_id, run_ref=run_ref, cursor_ref=cursor_ref, label="S11",
        scenario_sha=SCENARIO_SHA256, source_sha=SOURCE_SHA256, assess_content=assess_content,
    )
    return {**evidence, "native_source_read": "OPEN", "formal_acceptance": "OPEN"}
