"""Apply the existing D02 oracle to replies retained by the owned R4 caller."""

from hashlib import sha256
import json
from pathlib import Path
import re


PHASES = {
    "235a73f3411685f526bebd971c788f092dfebce0c745fb39cdd220821554e416": "D-02-01",
    "5a67f5517e2133a7314be051500d4527523f88e67d3039f4a47fa514405d34f6": "D-02-02",
}
SOURCE_SHA256 = "e1e22d351c4ff088428975c9870ee4f21174c52ed84e0a32cb964a1e7c9a2cd5"
ORACLE_SHA256 = "cd9c4f800a73a5adcbef5c412354dd73eb4eabf622c7aa1d89b56030f3a23147"
MEDIA = {
    "animation", "audio", "contact", "dice", "document", "game", "invoice", "location",
    "paid_media", "passport_data", "photo", "poll", "sticker", "story", "successful_payment",
    "venue", "video", "video_note", "voice",
}


def pinned_record(observer, reference, path):
    if (type(reference) is not dict or set(reference) != {"path", "bytes", "sha256"}
            or reference["path"] != str(path) or not path.is_absolute()
            or type(reference["bytes"]) is not int or not 0 < reference["bytes"] <= 2 * 1024**2):
        raise ValueError("Exact protected D02 run or cursor reference required")
    raw = observer.safe_read(path, reference["bytes"])
    if len(raw) != reference["bytes"] or sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("Protected D02 run or cursor changed")
    value = json.loads(raw, object_pairs_hook=observer.unique_object)
    if type(value) is not dict or observer.encoded(value) != raw:
        raise ValueError("Canonical D02 run or cursor required")
    return value


def original_ack(runner, run):
    ref = run["sent_api_ack_reference"]
    representation = ref["representation"]
    expected_name = f"send-ack-{run['id']}-0-1.json"
    ack = runner.read_reference({key: ref[key] for key in ("basename", "bytes", "sha256")}, expected_name)
    if representation == "botapi-wire-envelope-json" and ack.get("ok") is True:
        ack = ack["result"]
    elif representation != "decoded-message-json":
        raise ValueError("D02 acknowledgement representation changed")
    scenario = run["scenario"]
    if (ack.get("text") != scenario["steps"][0]["request"]
            or ack.get("from", {}).get("id") != scenario["tester_id"]
            or ack.get("from", {}).get("is_bot") is not True
            or ack.get("message_thread_id") is not None or ack.get("is_topic_message") is True):
        raise ValueError("D02 acknowledgement does not echo the exact private request")
    return ack


def reply_text(runner, run, observation, captures, ack):
    uid = observation["update_id"]
    update, arrival = runner.committed_capture(run, uid)
    message = update["message"]
    parent = message.get("reply_to_message")
    peer = run["scenario"]["peer_id"]
    if (observation["kind"] != "reply_text" or captures.get(uid) != arrival
            or observation["raw_update"] != arrival["raw_update"]
            or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
            or update["update_id"] != uid or message["message_id"] != observation["message_id"]
            or message["chat"]["id"] != peer or message["chat"]["type"] != "private"
            or message["from"]["id"] != peer or message["from"]["is_bot"] is not True
            or not isinstance(parent, dict) or any(parent.get(key) != ack[key] for key in ("message_id", "date", "text"))
            or parent.get("from", {}).get("id") != ack["from"]["id"] or parent["from"].get("is_bot") is not True
            or parent.get("chat", {}).get("id") != peer or parent["chat"].get("type") != "private"
            or message.get("message_thread_id") is not None or parent.get("message_thread_id") is not None
            or message.get("is_topic_message") is True or parent.get("is_topic_message") is True
            or not run["sent_date"] <= message["date"] <= run["capture_until"]
            or MEDIA.intersection(message) or type(message.get("text")) is not str):
        raise ValueError("D02 reply must be direct private text within the original ACK window")
    text = message["text"]
    text_sha256 = sha256(text.encode("utf-8")).hexdigest()
    if text_sha256 != observation["text_sha256"]:
        raise ValueError("D02 original reply text differs from the retained receipt")
    return text, {"reply_id": message["message_id"], "arrival_update": uid, "text_sha256": text_sha256}


def assess_saved_reply(observer, store, *, run_id, run_ref, cursor_ref, oracle_path):
    """Check saved receiver content for one phase. Native source evidence is separate."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D02 run ID required")
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, run_path)
    cursor = pinned_record(observer, cursor_ref, cursor_path)
    phase = PHASES.get(run.get("scenario_sha256"))
    if (phase is None or run.get("id") != run_id or run.get("step") != 0
            or run.get("send_attempts") != 1 or run.get("send_state") != "sent"
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D02 phase required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D02 receive journal did not complete its original window")
    if not run["observations"]:
        raise ValueError("D02 has no retained text reply")
    parts, replies = [], []
    for observation in run["observations"]:
        text, reference = reply_text(runner, run, observation, captures, ack)
        parts.append(text)
        replies.append(reference)

    oracle_raw = observer.safe_read(Path(oracle_path), 65536)
    if sha256(oracle_raw).hexdigest() != ORACLE_SHA256:
        raise ValueError("Exact existing D02 oracle required")
    oracle = {"__file__": str(oracle_path), "__name__": "_d02_oracle"}
    exec(compile(oracle_raw, str(oracle_path), "exec"), oracle)
    source = oracle["paragraphs"]()
    whole_reply = "\n".join(parts)
    if len(whole_reply) <= 8000:
        checks = oracle["content_checks"](phase, whole_reply, source)
        matches = oracle["content_matches"](phase, checks)
    else:
        checks, matches = None, None
    pinned_record(observer, run_ref, run_path)
    pinned_record(observer, cursor_ref, cursor_path)
    return {
        "phase": phase, "run_id": run_id, "run_sha256": run_ref["sha256"],
        "requested_source_sha256": SOURCE_SHA256, "sent_message_id": run["sent_message_id"],
        "reply_records": replies, "receiver_checks": checks, "receiver_content_matches": matches,
        "native_source_and_phase_predecessor": "OPEN", "formal_acceptance": "OPEN",
    }
