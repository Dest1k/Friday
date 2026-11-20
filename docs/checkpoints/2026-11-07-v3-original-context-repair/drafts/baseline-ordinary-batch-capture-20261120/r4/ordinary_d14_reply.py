"""Inspect the exact retained-pair D14 workbook from its closed receiver capture."""

from datetime import datetime
from hashlib import sha256
import json
from lzma import LZMAError
import math
import os
from pathlib import Path
import re
import stat
from types import ModuleType
from zipfile import BadZipFile
from zlib import error as DeflateError

from ordinary_d01_reply import MEDIA, read_exact
from ordinary_d02_reply import original_ack
from ordinary_d03_reply import pinned_record


SCENARIO_SHA256 = "5394ac076c92ba1c3cbb7c69361e7f4b2bb9944e312fc030d24b75f3f04933a3"
REQUEST_SHA256 = "0c2e78452e46915815c7553a7164817a20484ca64aedc338582c81bfd29d59f3"
INSPECTOR_SHA256 = "3c93120726098e6a2797f828ee8628a7c2bf5ea595df7cfabe653dbaff4fd147"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def digest(data):
    return sha256(data).hexdigest()


def private_reply(runner, run, item, captures, ack):
    uid = item["update_id"]
    update, arrival = runner.committed_capture(run, uid)
    message = update["message"]
    parent = message.get("reply_to_message")
    peer = run["scenario"]["peer_id"]
    if (arrival != captures.get(uid)
            or (item["kind"] == "reply_text" and arrival["raw_update"] != item["raw_update"])
            or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
            or not run["sent_date"] <= message["date"] <= run["capture_until"]
            or update["update_id"] != uid or message["message_id"] != item["message_id"]
            or message["chat"].get("id") != peer or message["chat"].get("type") != "private"
            or message["from"].get("id") != peer or message["from"].get("is_bot") is not True
            or type(parent) is not dict or parent.get("message_id") != ack["message_id"]
            or any(parent[key] != ack[key] for key in ("date", "text") if key in parent)
            or ("chat" in parent and (parent["chat"].get("id") != peer or parent["chat"].get("type") != "private"))
            or ("from" in parent and (parent["from"].get("id") != ack["from"]["id"]
                                      or parent["from"].get("is_bot") is not True))
            or MEDIA.intersection(parent)
            or any(row.get("message_thread_id") is not None or row.get("is_topic_message") is True
                   for row in (message, parent))):
        raise ValueError("D14 response does not bind the exact original private request")
    return message, {
        "message_id": item["message_id"], "update_id": uid, "raw_update": arrival["raw_update"],
        "arrived_at": arrival["arrived_at"],
        "receipt": {key: item["receipt_" + key] for key in ("path", "bytes", "sha256")},
    }


def worksheet_visibility(book, namespace):
    root = book.roots["xl/workbook.xml"]
    result = {}
    for node in root.findall(namespace + "sheets/" + namespace + "sheet"):
        name = node.attrib["name"]
        sheet = book.roots[book.sheets[name]]
        fmt = sheet.find(namespace + "sheetFormatPr")
        hidden_rows = []
        for row in sheet.findall(namespace + "sheetData/" + namespace + "row"):
            if row.get("hidden") in ("1", "true"):
                cell = row.find(namespace + "c")
                address = cell.get("r", "") if cell is not None else ""
                hidden_rows.append(row.get("r") or address.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") or None)
        result[name] = {
            "state": node.get("state", "visible"),
            "default_rows_hidden": fmt is not None and fmt.get("zeroHeight") in ("1", "true"),
            "hidden_rows": hidden_rows,
            "hidden_column_ranges": [
                [col.get("min"), col.get("max")] for col in sheet.findall(namespace + "cols/" + namespace + "col")
                if col.get("hidden") in ("1", "true")
            ],
        }
    return result


def inspect_saved_xlsx(observer, raw, artifact_sha, inspector_path):
    if digest(raw) != artifact_sha:
        raise ValueError("D14 workbook differs from correlated attachment receipt")
    def identity(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    info = inspector_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) not in (0o600, 0o700):
        raise ValueError("Private D14 workbook inspector required")
    source = observer.safe_read(inspector_path, 65536, private=False)
    if identity(info) != identity(inspector_path.lstat()) or digest(source) != INSPECTOR_SHA256:
        raise ValueError("Exact D14 workbook inspector required")
    inspector = ModuleType("_pinned_d14_workbook_inspector")
    inspector.__file__ = str(inspector_path)
    exec(compile(source, inspector.__file__, "exec"), vars(inspector))
    if len(raw) > inspector.MAX_BYTES:
        return {"state": "INSPECTION_UNAVAILABLE", "reason": "OUTSIDE_PINNED_READER_SIZE_LIMIT"}
    basis = observer.safe_read(inspector.BASIS, 65536)
    code = observer.safe_read(inspector.READER, 1_000_000, private=False)
    if digest(basis) != inspector.BASIS_SHA or digest(code) != inspector.READER_SHA:
        raise ValueError("Exact D14 grading facts and workbook reader required")
    facts = json.loads(basis, object_pairs_hook=observer.unique_object)
    reader = ModuleType("_pinned_d14_workbook_reader")
    reader.__file__ = str(inspector.READER)
    exec(compile(code, reader.__file__, "exec"), vars(reader))
    try:
        book = reader.Book(raw)
        rows = inspector.workbook_rows(book, reader.S)
        visibility = worksheet_visibility(book, reader.S)
        observations = inspector.cues(facts, rows)
    except (reader.RecalculationRefused, ArithmeticError, AttributeError, KeyError, TypeError, ValueError,
            BadZipFile, DeflateError, LZMAError, NotImplementedError, OSError, EOFError):
        return {"state": "INSPECTION_UNAVAILABLE", "reason": "PINNED_READER_COULD_NOT_INSPECT_PROFILE"}
    return {
        "state": "INSPECTED_NEEDS_INDEPENDENT_REVIEW", "workbook_sha256": artifact_sha,
        "grading_basis_sha256": inspector.BASIS_SHA, "native_reader_sha256": inspector.READER_SHA,
        "observation_count": len(observations), "observations": observations, "workbook_rows": rows,
        "sheet_visibility": visibility, "calculation_performed": False,
    }


def assess_saved_workbook(observer, store, *, run_id, run_ref, cursor_ref, inspector_path):
    """Read the actual recipient file and text using the same original window."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D14 saved run ID required")
    run_path, cursor_path = store.run_path(run_id), store.root / "cursor.json"
    run = pinned_record(observer, run_ref, expected_path=run_path)
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    scenario = run["scenario"]
    if (run.get("id") != run_id or run.get("scenario_sha256") != SCENARIO_SHA256
            or digest(observer.encoded(scenario)) != SCENARIO_SHA256
            or digest(scenario["steps"][0]["request"].encode()) != REQUEST_SHA256
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("send_state") != "sent" or run.get("sent_ids") != [run.get("sent_message_id")]
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D14 retained-pair run and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D14 original tester deadline does not match 300 seconds")
    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(runner, run)
    if (ack.get("message_id") != run["sent_message_id"] or ack.get("date") != run["sent_date"]
            or ack.get("chat", {}).get("id") != scenario["peer_id"] or ack["chat"].get("type") != "private"
            or MEDIA.intersection(ack)):
        raise ValueError("D14 original text ACK or private route differs")
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    terminal = drain.get("complete")
    if terminal is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D14 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D14 saved outcome differs from the retained observations")
    update_ids = [item["update_id"] for item in observations]
    if update_ids != sorted(set(update_ids)):
        raise ValueError("Exact ordered D14 observations required")

    texts, document, assessment = [], None, {"state": outcome}
    for item in observations:
        message, custody = private_reply(runner, run, item, captures, ack)
        if item["kind"] == "reply_text":
            text = message.get("text")
            if (type(text) is not str or MEDIA.intersection(message)
                    or digest(text.encode()) != item["text_sha256"] or text != item["text"]):
                raise ValueError("D14 text response differs from the exact saved receipt")
            texts.append(dict(custody, text=text, text_sha256=item["text_sha256"]))
            continue
        if item["kind"] != "document" or document is not None:
            raise ValueError("D14 capture exceeds the original workbook cap")
        advertised, info = message["document"], item["get_file"]
        if (item.get("complete_artifact") is not True or item.get("artifact_acceptance") != "RECEIVED_UNGRADED"
                or MEDIA.intersection(message) != {"document"} or "text" in message
                or not all(advertised.get(key) and advertised[key] == info.get(key) for key in ("file_id", "file_unique_id"))
                or not item["bytes"] == advertised.get("file_size") == info.get("file_size")):
            raise ValueError("D14 workbook identity or receipt is incomplete")
        path = store.downloads / f"{run_id}-{item['message_id']}-{item['sha256']}.bin"
        download = {key: item[key] for key in ("path", "bytes", "sha256")}
        raw = read_exact(observer, download, path, scenario["steps"][0]["observe"]["document_max_bytes"])
        name, mime = advertised.get("file_name"), advertised.get("mime_type")
        document = dict(custody, download=download, name=name, mime_type=mime, caption=item["caption"])
        if type(name) is not str or Path(name).suffix.lower() != ".xlsx" or mime != XLSX_MIME:
            assessment = {"state": "REVIEW_REQUIRED", "reason": "EXPECTED_XLSX_ATTACHMENT_METADATA"}
        else:
            assessment = inspect_saved_xlsx(observer, raw, download["sha256"], Path(inspector_path))
    if texts and document is None:
        assessment = {"state": "RECEIVED_TEXT_WITHOUT_XLSX"}
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "request_sha256": REQUEST_SHA256, "sent_message_id": run["sent_message_id"],
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"], "receive_head": run["receive_head"],
        "capture_until": run["capture_until"], "terminal_completed_at": terminal["completed_at"],
        "recipient_document": document, "direct_text_replies": texts, "inspection": assessment,
        "source_reads_and_producer_receipt": "OPEN", "semantic_review": "OPEN",
        "original_b00": "OPEN", "formal_acceptance": "OPEN",
    }
