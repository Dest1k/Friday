"""Evaluate the saved replies for the exact two independent D08 captures."""

from datetime import datetime
from hashlib import sha256
from io import BytesIO
from lzma import LZMAError
import math
from pathlib import Path
import re
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile
from zlib import error as DeflateError

from ordinary_d03_reply import original_ack, pinned_record, retained_text
from ordinary_d08_ordered import FILL, TEMPLATE
from ordinary_d11_reply import DOCX_MIME, read_saved_docx


ORACLE_SHA256 = "9d71703d5bd1188bc12ec2c4149ee0c4fb2f7a3f2beb12e5a00fdd15397d9c02"
OFFICE_DOCUMENT_RELATIONSHIP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
MATH_NAMESPACE = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
PHASES = {
    TEMPLATE: ("D08-ALT-01", "348611c62ccdf8c0f2caae8fe7fa5a3aff0f129b439717d0d54f5d1ca0ed9131"),
    FILL: ("D08-ALT-02", "d67fdf5832f81485b976d8992a02bb684671882a61977f720a3cca1fbd8c0dd5"),
}


def digest(data):
    return sha256(data).hexdigest()


def load_bound_oracle(observer, path):
    code = observer.safe_read(path, 65536)
    if digest(code) != ORACLE_SHA256:
        raise ValueError("Exact existing D08 checker required")
    oracle = {"__file__": str(path), "__name__": "_d08_pinned_letter_oracle"}
    exec(compile(code, str(path), "exec"), oracle)
    fixtures = {}
    for ref in oracle["SOURCES"]["alternate"]:
        fixture_path, expected = ref
        raw = observer.safe_read(fixture_path, 65536)
        if digest(raw) != expected:
            raise ValueError("D08 checker source bytes changed")
        fixtures[ref] = raw
    # Validate both sources before screening replies. All subsequent reads use those same bytes.
    oracle["pinned"] = lambda path, expected: fixtures[path, expected]
    oracle["inputs"]("alternate")
    return oracle


def screen_filled_docx(oracle, raw):
    try:
        result = oracle["check_filled"](raw, "alternate")
        # The pinned checker already bounds archive sizes and rejects unsafe XML.
        with ZipFile(BytesIO(raw)) as package:
            relations = oracle["xml_part"](package.read("_rels/.rels"))
            body = oracle["xml_part"](package.read("word/document.xml"))
        primary = [
            item for item in relations
            if item.get("Target") in ("word/document.xml", "/word/document.xml")
            and (item.get("Type") or "").endswith("/officeDocument")
        ]
        if len(primary) != 1 or primary[0].get("Type") != OFFICE_DOCUMENT_RELATIONSHIP:
            return {"state": "FAIL", "condition": "EXPECTED_OFFICE_DOCUMENT_RELATIONSHIP"}
        if any(item.tag.startswith(MATH_NAMESPACE) for item in body.iter()):
            return {"state": "REVIEW_REQUIRED", "condition": "ADDITIONAL_MATH_CONTENT"}
    except (ValueError, KeyError, BadZipFile, ParseError, NotImplementedError,
            DeflateError, LZMAError, OSError, EOFError) as error:
        return {"state": "FAIL", "condition": str(error)}
    return result


def assess_saved_phase(observer, store, *, run_id, run_ref, cursor_ref, oracle_path):
    """Check receiver content only. Context, native execution and acceptance stay separate."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D08 phase run ID required")
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, expected_path=run_path)
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    scenario = run["scenario"]
    scenario_sha = run["scenario_sha256"]
    if (scenario_sha not in PHASES or digest(observer.encoded(scenario)) != scenario_sha
            or run.get("id") != run_id or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("send_state") != "sent" or run.get("sent_ids") != [run.get("sent_message_id")]
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D08 phase and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D08 original tester deadline does not match 300 seconds")
    phase, input_sha = PHASES[scenario_sha]
    upload = scenario["steps"][0]["input"]
    if run["request_metadata"].get("input_sha256") != input_sha or upload["sha256"] != input_sha:
        raise ValueError("Exact D08 source upload required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D08 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D08 saved outcome differs from the retained observations")
    update_ids = [item["update_id"] for item in observations]
    if update_ids != sorted(set(update_ids)):
        raise ValueError("Exact ordered D08 observations required")
    texts = []
    for item in observations:
        if item["kind"] == "reply_text":
            body, receipt = retained_text(observer, runner, run, item, captures, ack)
            texts.append(dict(receipt, text=body.decode("utf-8")))
    documents = [item for item in observations if item["kind"] == "document"]
    if len(documents) > scenario["steps"][0]["observe"]["max_documents"]:
        raise ValueError("D08 closed evidence exceeds its original artifact cap")
    output = {"state": outcome}
    document = None
    if observations:
        if digest(observer.read_document_input(upload, lambda: None)) != input_sha:
            raise ValueError("D08 input bytes changed")
        oracle = load_bound_oracle(observer, Path(oracle_path))
        if scenario_sha == TEMPLATE:
            text = "\n".join(item["text"] for item in texts)
            try:
                output = oracle["check_handover"](text, "alternate")
            except ValueError as error:
                output = {"state": "FAIL", "condition": str(error)}
        elif not documents:
            output = {"state": "FAIL", "condition": "EXPECTED_ONE_DOCUMENT"}
        else:
            raw, document = read_saved_docx(observer, runner, run, documents[0], captures, ack)
            name = document["name"]
            if documents[0]["advertised_document"].get("mime_type") != DOCX_MIME:
                output = {"state": "FAIL", "condition": "EXPECTED_DOCX_MIME"}
            elif type(name) is not str or Path(name).suffix.lower() != ".docx":
                output = {"state": "FAIL", "condition": "EXPECTED_DOCX_FILENAME"}
            else:
                output = screen_filled_docx(oracle, raw)
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "phase": phase, "scenario_sha256": scenario_sha,
        "send_ack": run["sent_api_ack_reference"], "send_window": run["sent_window_reference"],
        "send_task": run["sent_task_reference"], "receive_head": run["receive_head"],
        "sent_message_id": run["sent_message_id"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"], "receiver_content": output,
        "direct_text_replies": texts, "recipient_docx": document,
        "explicit_refusal_observed": run.get("refusal_observed") is True,
        "same_scope_and_native_lineage": "OPEN", "formal_acceptance": "OPEN",
    }
