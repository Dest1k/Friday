"""Evaluate the exact D12 ZIP from the existing closed R4 capture."""

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata


SCENARIO_SHA256 = "3526cfe50aaf7318843a8a4b148b0df8ab0cc304328c6401fa20477fa62fc121"
SOURCE_SHA256 = "af87ff7f28e001976c7cd5edf40911c8bf11418953ca6c65183d6d5366103fe7"
ORACLE_SHA256 = "b416b25f69921a8b830d3c9b06ea9d50df5d081a428c0f07f1fd83d9e8ce75b3"
MAX_ZIP_BYTES = 2 * 1024 * 1024


def digest(raw):
    return sha256(raw).hexdigest()


def read_record(observer, reference, path):
    raw = observer.safe_read(path, observer.MAX_JSON)
    if reference != {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}:
        raise ValueError("Exact D12 retained run or cursor reference changed")
    record = json.loads(raw, object_pairs_hook=observer.unique_object)
    if type(record) is not dict or observer.encoded(record) != raw:
        raise ValueError("D12 protected record must be canonical")
    return record


def safe_zip_name(name):
    return (isinstance(name, str) and 5 <= len(name) <= 128
            and name.casefold().endswith(".zip") and name[0] != "."
            and name == name.strip() == unicodedata.normalize("NFC", name)
            and ".." not in name and not any(ch in name for ch in "/\\:")
            and all(not unicodedata.category(ch).startswith("C") for ch in name))


def assess_saved_zip(observer, store, *, run_id, run_ref, cursor_ref, oracle_path):
    """Correlate recipient custody, then pass the same retained bytes to the D12 oracle."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D12 retained run ID required")
    path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = read_record(observer, run_ref, path)
    cursor = read_record(observer, cursor_ref, cursor_path)
    if (run.get("id") != run_id or run.get("scenario_sha256") != SCENARIO_SHA256
            or digest(observer.encoded(run["scenario"])) != SCENARIO_SHA256
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or type(run.get("repeat_count")) is not int or run["repeat_count"] != 0
            or type(run.get("sent_message_id")) is not int or run["sent_message_id"] <= 0
            or run.get("sent_ids") != [run["sent_message_id"]] or run.get("send_state") != "sent"
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact D12 closed run and one acknowledged send required")
    upload = run["scenario"]["steps"][0]["input"]
    if upload["sha256"] != SOURCE_SHA256 or run["request_metadata"]["input_sha256"] != SOURCE_SHA256:
        raise ValueError("Exact D12 uploaded CSV hash required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    pending = runner.read_poll_intent(run)
    if drain.get("complete") is None or (pending and pending["outcome"] == "PENDING"):
        raise ValueError("D12 capture journal did not complete its original window")
    archives = [row for row in run["observations"] if row["kind"] == "document"]
    if len(archives) != 1 or run.get("reply_outcome") != "RECEIVED_UNGRADED":
        raise ValueError("D12 requires one retained archive inside the original response window")
    receipt, = archives
    uid = receipt["update_id"]
    update, arrival = runner.committed_capture(run, uid)
    message = update["message"]
    parent = message.get("reply_to_message", {})
    document, info = message["document"], receipt["get_file"]
    peer = run["scenario"]["peer_id"]
    name = document.get("file_name")
    if (arrival != captures.get(uid) or update["update_id"] != uid
            or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
            or not run["sent_date"] <= message["date"] <= run["capture_until"]
            or message["message_id"] != receipt["message_id"] or message["chat"]["type"] != "private"
            or message["chat"]["id"] != peer or message["from"]["id"] != peer
            or message["from"]["is_bot"] is not True or parent.get("message_id") != run["sent_message_id"]
            or any(msg.get("message_thread_id") is not None or msg.get("is_topic_message") is True
                   for msg in (message, parent))):
        raise ValueError("D12 ZIP must directly bind the original private ACK")
    if (receipt.get("complete_artifact") is not True or document.get("mime_type") != "application/zip"
            or not safe_zip_name(name) or document != receipt["advertised_document"]
            or not all(type(document.get(key)) is str and document[key] and info.get(key) == document[key]
                       for key in ("file_id", "file_unique_id"))
            or type(receipt["bytes"]) is not int or not 0 < receipt["bytes"] <= MAX_ZIP_BYTES
            or receipt["bytes"] != document["file_size"] or receipt["bytes"] != info["file_size"]):
        raise ValueError("D12 retained file identity, name, ZIP MIME or byte count differs")

    data = observer.safe_read(Path(receipt["path"]), MAX_ZIP_BYTES)
    if len(data) != receipt["bytes"] or digest(data) != receipt["sha256"]:
        raise ValueError("D12 ZIP changed after recipient custody verification")
    source = observer.read_document_input(upload, lambda: None)
    oracle_raw = observer.safe_read(oracle_path, 65536)
    if digest(oracle_raw) != ORACLE_SHA256:
        raise ValueError("Exact D12 ZIP oracle required")
    oracle = {"__file__": str(oracle_path), "__name__": "_d12_zip_oracle"}
    exec(compile(oracle_raw, str(oracle_path), "exec"), oracle)
    assessed = oracle["check"](source, data, SOURCE_SHA256, receipt["sha256"])
    read_record(observer, run_ref, path)
    read_record(observer, cursor_ref, cursor_path)
    return {
        "state": "D12_SAVED_RECIPIENT_ZIP_COMPONENT_ASSESSED",
        "run": run_ref, "cursor": cursor_ref, "run_id": run_id, "scenario_sha256": SCENARIO_SHA256,
        "peer_id": run["scenario"]["peer_id"], "tester_id": run["scenario"]["tester_id"],
        "request_body_sha256": run["request_metadata"]["body_sha256"],
        "sent_message_id": run["sent_message_id"], "send_ack": run["sent_api_ack_reference"],
        "send_task": run["sent_task_reference"], "send_window": run["sent_window_reference"],
        "receive_head": run["receive_head"], "raw_reply": arrival["raw_update"],
        "recipient_zip": {key: receipt[key] for key in ("path", "bytes", "sha256", "message_id", "update_id")},
        "filename": name, "assessment": assessed, "producer_to_recipient_join": "OPEN",
        "formal_acceptance": "OPEN",
    }


def join_native_zip(checked, *, ingress, attempt, reservation, candidate, delivery):
    """Join protected native evidence already read by the caller to the checked receiver archive.

    The caller must read the native ingress correlation and the final delivery row
    for the attempt selection. The candidate journal can precede final settlement.
    """
    if (checked.get("state") != "D12_SAVED_RECIPIENT_ZIP_COMPONENT_ASSESSED"
            or checked.get("scenario_sha256") != SCENARIO_SHA256):
        raise ValueError("Exact assessed D12 receiver archive required")
    route = attempt["route"]
    source = route["source"]
    expected_ingress = {
        "run_id": checked["run_id"], "scenario_sha256": SCENARIO_SHA256, "step": 0,
        "request_body_sha256": checked["request_body_sha256"], "source_sha256": SOURCE_SHA256,
        "tester_sent_message_id": checked["sent_message_id"], "native_ingress_message_id": source["message_id"],
        "receiver_bot_id": str(checked["peer_id"]), "native_chat_id": str(checked["tester_id"]),
        "native_thread_id": None,
    }
    if (set(ingress) != set(expected_ingress)
            or any(type(ingress[key]) is not type(value) or ingress[key] != value
                   for key, value in expected_ingress.items())
            or route["bot_id"] != expected_ingress["receiver_bot_id"]
            or source.get("platform") != "telegram" or source.get("chat_type") != "dm"
            or source.get("user_id") != str(checked["tester_id"])
            or source["chat_id"] != expected_ingress["native_chat_id"] or source["thread_id"] is not None
            or not isinstance(source["message_id"], str) or not re.fullmatch("[1-9][0-9]*", source["message_id"])):
        raise ValueError("D12 native ingress differs from the original acknowledged upload")
    relative = delivery.get("relative_path")
    path = PurePosixPath(relative) if isinstance(relative, str) else PurePosixPath()
    if (not path.parts or path.is_absolute() or path.as_posix() != relative
            or any(part.startswith(".") for part in path.parts)):
        raise ValueError("D12 native archive lacks its relative workspace selection")
    if (attempt.get("schema") != "friday.ordinary-document-attempt.v1"
            or not isinstance(attempt.get("selection"), str) or not re.fullmatch("[a-f0-9]{64}", attempt["selection"])
            or candidate.get("selection") != attempt["selection"] or delivery.get("route") != route
            or reservation.get("state") != "UNKNOWN" or reservation.get("receipt") is not None
            or any(reservation.get(key) != delivery.get(key)
                   for key in ("route", "relative_path", "sha256", "bytes", "file_name"))
            or delivery.get("state") != "DELIVERED" or delivery.get("receipt") != candidate.get("receipt")):
        raise ValueError("D12 native archive delivery is not durably settled for this attempt")
    artifact = checked["recipient_zip"]
    native = delivery["receipt"]
    wanted = {
        "state": "DELIVERED", "kind": "document", "sha256": artifact["sha256"], "bytes": artifact["bytes"],
        "file_name": checked["filename"], "bot_id": route["bot_id"], "chat_id": source["chat_id"],
        "thread_id": None, "reply_to": source["message_id"],
    }
    if (not isinstance(native, dict) or any(type(native.get(k)) is not type(v) or native[k] != v
                                           for k, v in wanted.items())
            or any(delivery.get(key) != wanted[key] for key in ("sha256", "bytes", "file_name"))
            or not isinstance(native.get("message_id"), str) or not re.fullmatch("[1-9][0-9]*", native["message_id"])):
        raise ValueError("D12 native archive differs from the complete recipient bytes or original reply")
    return {"state": "D12_NATIVE_AND_RECIPIENT_ARCHIVE_CUSTODY_MATCHED",
            "native_message_id": native["message_id"], "recipient_message_id": artifact["message_id"],
            "selection": attempt["selection"], "bytes": artifact["bytes"], "sha256": artifact["sha256"]}
