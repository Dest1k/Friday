"""Project the protected D12 sender ACK and its exact original upload."""

from datetime import datetime
import math
import re

from ordinary_d12_reply import SCENARIO_SHA256, SOURCE_SHA256, digest, read_record


def read_upload_ack(observer, store, *, run_id, run_ref):
    """Read outbound evidence independently of the eventual recipient outcome."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D12 tester run ID required")
    path = store.run_path(run_id)
    run = read_record(observer, run_ref, path)
    scenario = run["scenario"]
    if (run.get("id") != run_id or run.get("scenario_sha256") != SCENARIO_SHA256
            or digest(observer.encoded(scenario)) != SCENARIO_SHA256
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("sent_ids") != [run.get("sent_message_id")] or run.get("send_state") != "sent"):
        raise ValueError("Exact D12 scenario and one confirmed tester send required")
    upload = scenario["steps"][0]["input"]
    metadata = run["request_metadata"]
    if upload["sha256"] != SOURCE_SHA256 or metadata.get("input_sha256") != SOURCE_SHA256:
        raise ValueError("Exact D12 tester input bytes required")
    created = datetime.fromisoformat(run["created_at"])
    deadline = run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 900) > 1):
        raise ValueError("D12 original tester deadline does not match 900 seconds")

    runner = observer.Runner(store, None)
    runner.verify_capture_context(run)
    runner.verify_window(run)
    ref = run["sent_api_ack_reference"]
    ack = runner.read_reference({key: ref[key] for key in ("basename", "bytes", "sha256")},
                                f"send-ack-{run_id}-0-1.json")
    if ref["representation"] == "botapi-wire-envelope-json" and ack.get("ok") is True:
        ack = ack["result"]
    elif ref["representation"] != "decoded-message-json":
        raise ValueError("D12 tester ACK representation changed")
    sender, chat, document = ack.get("from", {}), ack.get("chat", {}), ack.get("document", {})
    if (type(sender.get("id")) is not int or sender["id"] != scenario["tester_id"]
            or sender.get("is_bot") is not True
            or type(chat.get("id")) is not int or chat["id"] != scenario["peer_id"]
            or chat.get("type") != "private" or ack.get("message_thread_id") is not None
            or ack.get("is_topic_message") is True or ack.get("reply_to_message") is not None
            or ack.get("caption") != upload["caption"]):
        raise ValueError("D12 protected ACK sender, route or original caption differs")
    if (not observer.valid_input_ack(ack, upload, require_document_size=True)
            or document.get("file_name") != upload["filename"] or document.get("mime_type") != upload["mime_type"]):
        raise ValueError("D12 protected ACK document name, MIME, size or file identifiers differ")
    read_record(observer, run_ref, path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "tester_sent_message_id": run["sent_message_id"], "telegram_date": ack["date"],
        "tester_id": scenario["tester_id"], "receiver_bot_id": scenario["peer_id"],
        "request_body_sha256": metadata["body_sha256"], "source_sha256": SOURCE_SHA256,
        "source_bytes": upload["stat"]["size_bytes"], "name": document["file_name"], "mime_type": document["mime_type"],
        "caption_sha256": digest(ack["caption"].encode("utf-8")),
        "file_unique_id_sha256": digest(document["file_unique_id"].encode("utf-8")),
        "ack": ref, "task": run["sent_task_reference"], "original_window": run["sent_window_reference"],
        "native_ingress_join": "OPEN",
    }
