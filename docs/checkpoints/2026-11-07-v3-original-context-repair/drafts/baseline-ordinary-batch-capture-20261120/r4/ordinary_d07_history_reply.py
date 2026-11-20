"""Check the exact saved D07 retained-history table on the existing R4 records."""

from datetime import datetime
from hashlib import sha256
import math
from pathlib import Path
import re

from ordinary_d03_reply import original_ack, pinned_bytes, pinned_record, retained_text


SCENARIO_SHA256 = "d22418c5f25e4847c5fef9a0b7a0d0a1849334de33ae657c4a6d2268bd0044cf"
V1_SHA256 = "23c9df7fe3c1646729ec796e1673c3759fad763175d4b0f853a9f73cf4ba3fde"
V2_SHA256 = "4bc3ad96c79a1bca33e9a05900d0ac436c9b6b7156c9bbafc07364cfe9b86075"
ORACLE_SHA256 = "48506fa25fac1bbae3767ba6b6f777a305cb1735ef2aa85991659cfaee086d36"


def digest(data):
    return sha256(data).hexdigest()


def screen_table(oracle, source, revised, answer):
    old = oracle["_decode"](source, "V1")
    new = oracle["_decode"](revised, "V2")
    oracle["_check_source_delta"](old, new)
    if len(answer) > oracle["MAX_ANSWER_BYTES"]:
        return {"status": "UNVERIFIED", "category": "ANSWER_SIZE"}
    try:
        oracle["_check_table"](oracle["_decode"](answer, "ANSWER", "utf-8-sig"))
    except oracle["Refused"] as exc:
        return {"status": "FAIL", "category": exc.category}
    return {"status": "PASS", "verified_rows": len(oracle["EXPECTED_ROWS"])}


def assess_saved_comparison(observer, store, *, run_id, run_ref, cursor_ref, v1_ref, oracle_path):
    """Assess receiver content. The actual native reads and formal grade stay separate."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D07 retained run ID required")
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
        raise ValueError("Exact closed D07 retained-history comparison required")
    created = datetime.fromisoformat(run["created_at"])
    deadline = run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D07 original tester deadline does not match 300 seconds")
    upload = scenario["steps"][0]["input"]
    if upload["sha256"] != V2_SHA256 or run["request_metadata"].get("input_sha256") != V2_SHA256:
        raise ValueError("Exact D07 received v2 source identity required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D07 original receive window is unsettled")
    observations = run["observations"]
    expected_outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != expected_outcome:
        raise ValueError("D07 terminal reply outcome differs from the retained observations")
    update_ids = [obs["update_id"] for obs in observations]
    if update_ids != sorted(set(update_ids)):
        raise ValueError("Exact ordered D07 receiver observations required")
    parts, receipts = [], []
    for observation in observations:
        body, receipt = retained_text(observer, runner, run, observation, captures, ack)
        parts.append(body)
        receipts.append(receipt)
    answer = b"\n".join(parts)

    source = pinned_bytes(observer, v1_ref)
    revised = observer.read_document_input(upload, lambda: None)
    if len(source) != 934 or digest(source) != V1_SHA256 or len(revised) != 974 or digest(revised) != V2_SHA256:
        raise ValueError("D07 comparison requires the two exact TXT source versions")
    oracle_raw = observer.safe_read(Path(oracle_path), 65536)
    if digest(oracle_raw) != ORACLE_SHA256:
        raise ValueError("Exact existing D07 retained-history oracle required")
    oracle = {"__file__": str(oracle_path), "__name__": "_d07_retained_history_oracle"}
    exec(compile(oracle_raw, str(oracle_path), "exec"), oracle)
    table = screen_table(oracle, source, revised, answer) if observations else {"status": expected_outcome}
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "sent_message_id": run["sent_message_id"], "answer_sha256": digest(answer),
        "answer_bytes": len(answer), "reply_records": receipts, "receiver_table": table,
        "actual_native_reads": "OPEN", "formal_acceptance": "OPEN",
    }
