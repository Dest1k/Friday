"""Assess the retained D04 DOCX pair with the existing lexical and OOXML oracle."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory


SCENARIO_SHA256 = "9b6f6df645c3d07d0b695022349db4b7c81ea2d004c83a64847c63f7d408d78e"
SOURCE_SHA256 = "7f238f28c0a58e5c8a8c1e81b48970f8d470fb00e521a3107fa63070a7b01160"
ORACLE_SHA256 = "f59e787113cde236e77deeea4a657d5f3cbb387636283132584e549cbcc2ad82"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
FILENAMES = {"D04-Mayak-Brief.docx": "brief", "D04-Mayak-Appendix.docx": "appendix"}
DOCUMENT_MAX_BYTES = 8 * 1024 * 1024


def read_pair(runner, run, cursor, *, expected_run_id):
    """Return exact recipient artifact references and the completed-window record."""
    if (runner.api is not None or type(cursor) is not dict
            or run.get("id") != expected_run_id or run.get("scenario_sha256") != SCENARIO_SHA256
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("status") != "EVIDENCE_READY" or run.get("send_state") != "sent"
            or run.get("capture_window_complete") is not True
            or run.get("request_metadata", {}).get("input_sha256") != SOURCE_SHA256):
        raise ValueError("Exact closed D04 run and read-only observer required")

    runner.verify_reply_custody(run, cursor)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    terminal = drain.get("complete")
    poll = runner.read_poll_intent(run)
    if terminal is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D04 receive journal did not close the original window")

    artifacts = [row for row in run["observations"] if row["kind"] == "document"]
    if len(artifacts) != len(FILENAMES):
        raise ValueError("D04 requires both distinct DOCX replies in the original window")
    pair = {}
    peer = run["scenario"]["peer_id"]
    for receipt in artifacts:
        update_id = receipt["update_id"]
        update, arrival = runner.committed_capture(run, update_id)
        message = update["message"]
        parent = message.get("reply_to_message", {})
        document = message["document"]
        name = document.get("file_name")
        role = FILENAMES.get(name)
        if (role is None or role in pair or document.get("mime_type") != DOCX
                or receipt.get("complete_artifact") is not True or arrival != captures.get(update_id)
                or receipt["message_id"] != message["message_id"]
                or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
                or not run["sent_date"] <= message["date"] <= run["capture_until"]
                or message["chat"].get("type") != "private" or message["chat"].get("id") != peer
                or message["from"].get("id") != peer or message["from"].get("is_bot") is not True
                or parent.get("message_id") != run["sent_message_id"]
                or message.get("message_thread_id") is not None or message.get("is_topic_message") is True
                or parent.get("message_thread_id") is not None or parent.get("is_topic_message") is True):
            raise ValueError("D04 reply does not bind a distinct DOCX role and the original private ACK")
        pair[role] = {
            "name": name, "path": receipt["path"], "sha256": receipt["sha256"],
            "bytes": receipt["bytes"], "message_id": receipt["message_id"], "update_id": update_id,
            "receipt_path": receipt["receipt_path"], "receipt_sha256": receipt["receipt_sha256"],
            "arrived_at": arrival["arrived_at"], "raw_update": arrival["raw_update"],
        }
    return pair, terminal


def assess(r4, store, run, cursor, *, expected_run_id, oracle_path, scratch):
    """Grade the same retained bytes under their approved names in a private temporary directory."""
    pair, terminal = read_pair(r4.Runner(store, None), run, cursor, expected_run_id=expected_run_id)
    oracle_raw = r4.safe_read(oracle_path, 65536)
    if sha256(oracle_raw).hexdigest() != ORACLE_SHA256:
        raise ValueError("Exact D04 pair oracle required")
    oracle = {"__file__": str(oracle_path), "__name__": "_d04_pair_oracle"}
    exec(compile(oracle_raw, str(oracle_path), "exec"), oracle)
    upload = run["scenario"]["steps"][0]["input"]
    source_bytes = r4.read_document_input(upload, lambda: None)
    if sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("Exact D04 source changed during assessment")
    with TemporaryDirectory(prefix="d04-assessment-", dir=scratch) as directory:
        source = Path(directory) / upload["filename"]
        with source.open("xb") as stream:
            stream.write(source_bytes)
        copies = {}
        for role, item in pair.items():
            raw = r4.safe_read(item["path"], DOCUMENT_MAX_BYTES)
            if (len(raw), sha256(raw).hexdigest()) != (item["bytes"], item["sha256"]):
                raise ValueError("D04 recipient artifact changed after custody verification")
            copies[role] = Path(directory) / item["name"]
            with copies[role].open("xb") as stream:
                stream.write(raw)
        result = oracle["check_pair"](source, copies["brief"], copies["appendix"], source_sha256=SOURCE_SHA256)
    if any(result[role + "_sha256"] != evidence["sha256"] for role, evidence in pair.items()):
        raise ValueError("D04 oracle assessed different bytes")
    return {
        "state": "D04_RETAINED_PAIR_COMPONENT_ASSESSED",
        "scenario_sha256": SCENARIO_SHA256, "run_id": expected_run_id,
        "sent_message_id": run["sent_message_id"], "capture_until": run["capture_until"],
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"],
        "terminal_completed_at": terminal["completed_at"], "receive_head": run["receive_head"],
        "pair": pair, "component_assessment": result,
        "brief_rendered_pages": None, "formal_acceptance": "OPEN",
    }
