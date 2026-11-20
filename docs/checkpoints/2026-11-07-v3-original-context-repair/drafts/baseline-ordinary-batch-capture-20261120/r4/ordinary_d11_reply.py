"""Read the exact D11 recipient DOCX and prepare its structure and content review."""

import builtins
from datetime import datetime
from hashlib import sha256
from lzma import LZMAError
import math
from pathlib import Path
import re
from types import ModuleType
from zlib import error as DeflateError

from ordinary_d01_reply import DOCX_MIME, MAX_DOCX_BYTES, MEDIA, read_exact
from ordinary_d03_reply import advertised_document_matches, original_ack, pinned_record, retained_text


SCENARIO_SHA256 = "b99effc9a4cab5b11ce17b23260564a42f5f269f1fba3d94c3a505e0a5266414"
SOURCE_SHA256 = "e75b69bbbb235468e305e6bcc61901a637c4583764fe3af5191187a410438be3"
CHECKER_SHA256 = "7471d70d63fdbdd7135499945ce0cc76fd18bb4151c50d9cdb50d8ea64fc2d80"
PREPARER_SHA256 = "47fdaa897be868198fb973a0fc1c665764d990d9a8f134a9e3291fd927545953"

# Roles in the exact Ruchey passport identified by SOURCE_SHA256.
_PASSPORT_DATES = {
    "submission_deadline": "17 декабря 2026 года",
    "sample_storage_deadline": "25 января 2027 года",
    "passport_date": "11 ноября 2026 года",
}
_DATE_SEPARATOR = r"(?:\s*[:–—-]\s*| )"
_DATE_ROLE_PHRASES = {
    "submission_deadline": (
        rf"(?:срок|дата) сдачи(?: проекта)?{_DATE_SEPARATOR}(?:до )?"
        r"|(?:проект )?(?:(?:нужно|необходимо|следует) )?сдать(?: проект)? до "
    ),
    "sample_storage_deadline": (
        rf"срок хранения контрольного образца{_DATE_SEPARATOR}(?:до )?"
        r"|хранить контрольный образец до "
        r"|контрольный образец (?:хранится|хранить|следует хранить|нужно хранить) до "
    ),
    "passport_date": (
        rf"дата паспорта(?: проекта)?{_DATE_SEPARATOR}"
        r"|паспорт(?: проекта(?: «ручей»)?)? (?:от|датирован) "
    ),
    "sample_date": (
        rf"дата контрольного образца{_DATE_SEPARATOR}"
        r"|контрольный образец (?:от|датирован|изготовлен|подготовлен) "
    ),
}
_DATE_CLAIM = re.compile(
    r"(?:^|(?<=[.!?;]))\s*(?:[•–—-] )?(?:"
    + "|".join(f"(?P<{role}>{phrase})" for role, phrase in _DATE_ROLE_PHRASES.items())
    + r")"
    r"(?P<date>[0-9]{1,2} (?:января|февраля|марта|апреля|мая|июня|июля|августа|"
    r"сентября|октября|ноября|декабря) [0-9]{4} года)(?=$|[.!;])"
)


def digest(raw):
    return sha256(raw).hexdigest()


def load_report_checker(observer, directory):
    source = observer.safe_read(directory / "prepare_d11.py", 65536)
    checker = observer.safe_read(directory / "check_report.py", 65536)
    if digest(source) != PREPARER_SHA256 or digest(checker) != CHECKER_SHA256:
        raise ValueError("Exact D11 report checker and its facts module required")
    preparer = ModuleType("prepare_d11")
    preparer.__file__ = str(directory / "prepare_d11.py")
    exec(compile(source, preparer.__file__, "exec"), vars(preparer))

    def checker_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "prepare_d11" and level == 0:
            return preparer
        return builtins.__import__(name, globals, locals, fromlist, level)

    oracle = ModuleType("_pinned_d11_report_checker")
    oracle.__file__ = str(directory / "check_report.py")
    oracle.__builtins__ = dict(vars(builtins), __import__=checker_import)
    exec(compile(checker, oracle.__file__, "exec"), vars(oracle))
    return oracle


def read_saved_docx(observer, runner, run, item, captures, ack):
    return read_saved_document(observer, runner, run, item, captures, ack,
                               max_bytes=MAX_DOCX_BYTES, label="D11 recipient DOCX")


def read_saved_document(observer, runner, run, item, captures, ack, *, max_bytes, label):
    """Read a direct retained document against its original upload and bounded receipt."""
    update, arrival = runner.committed_capture(run, item["update_id"])
    message = update["message"]
    parent = message.get("reply_to_message", {})
    peer = run["scenario"]["peer_id"]
    upload = run["scenario"]["steps"][0]["input"]
    expected_parent = {"file_name": upload["filename"], "mime_type": upload["mime_type"],
                       "file_size": upload["stat"]["size_bytes"],
                       "file_unique_id": ack["document"]["file_unique_id"]}
    if (arrival != captures.get(item["update_id"])
            or not run["sent_at"] <= arrival["arrived_at"] < run["capture_until"]
            or not run["sent_date"] <= message["date"] <= run["capture_until"]
            or message["chat"].get("type") != "private" or parent.get("message_id") != ack["message_id"]
            or any(m.get("message_thread_id") is not None or m.get("is_topic_message") is True
                   for m in (message, parent))
            or parent.get("date", ack["date"]) != ack["date"]
            or "chat" in parent and (parent["chat"].get("id") != peer or parent["chat"].get("type") != "private")
            or "from" in parent and (parent["from"].get("id") != ack["from"]["id"]
                                      or parent["from"].get("is_bot") is not True)
            or "caption" in parent and not observer.caption_ack_matches(parent["caption"], upload["caption"])
            or "document" in parent and not advertised_document_matches(parent["document"], expected_parent)
            or MEDIA.intersection(message) != {"document"} or "text" in message):
        raise ValueError(f"{label} does not bind the original private upload")
    document, info = message["document"], item["get_file"]
    if (item.get("complete_artifact") is not True or item.get("artifact_acceptance") != "RECEIVED_UNGRADED"
            or not all(document.get(key) and document[key] == info.get(key) for key in ("file_id", "file_unique_id"))
            or not item["bytes"] == document.get("file_size") == info.get("file_size")):
        raise ValueError(f"{label} custody is incomplete")
    path = runner.store.downloads / f"{run['id']}-{item['message_id']}-{item['sha256']}.bin"
    reference = {key: item[key] for key in ("path", "bytes", "sha256")}
    data = read_exact(observer, reference, path, max_bytes)
    return data, {
        "name": document.get("file_name"), "download": reference, "raw_update": arrival["raw_update"],
        "arrived_at": arrival["arrived_at"],
        "message_id": item["message_id"], "update_id": item["update_id"], "caption": item["caption"],
        "receipt": {key: item["receipt_" + key] for key in ("path", "bytes", "sha256")},
    }


def review_date_roles(paragraphs):
    """Screen explicit date claims in the exact Ruchey variant for manual review."""
    matches, conflicts = [], []
    for index, paragraph in enumerate(paragraphs):
        normalized = " ".join(paragraph.casefold().replace("ё", "е").split())
        for match in _DATE_CLAIM.finditer(normalized):
            role = next(role for role in _DATE_ROLE_PHRASES if match[role] is not None)
            claim = {"paragraph_index": index, "role": role, "date": match["date"]}
            expected = _PASSPORT_DATES.get(role)
            if claim["date"] == expected:
                matches.append(claim)
            else:
                conflicts.append(dict(claim, expected_date=expected))
    resolved = {claim["role"] for claim in matches} - {claim["role"] for claim in conflicts}
    unresolved = [role for role in _PASSPORT_DATES if role not in resolved]
    state = "MATCHED"
    if conflicts:
        state = "CONFLICT"
    elif unresolved:
        state = "REVIEW_REQUIRED"
    return {"state": state, "matches": matches, "conflicts": conflicts, "unresolved_roles": unresolved}


def report_review(oracle, source, report):
    try:
        structure = oracle.verify_report(report)
    except (oracle.Rejected, oracle.BadZipFile, oracle.ET.ParseError,
            NotImplementedError, DeflateError, LZMAError, OSError, EOFError) as error:
        return {"state": "OFFLINE_REPORT_REFUSED", "reason": str(error)}, None
    report_body, roles = oracle.required_roles(oracle.package_xml(report))
    source_body = oracle.package_xml(source)["word/document.xml"].find(oracle.W + "body")
    # Retain the order and paragraph boundaries so reviewers can judge relationships between facts.
    report_paragraphs = [oracle.text(p) for p in report_body.findall(oracle.W + "p")]
    return structure, {
        "state": "REVIEW_REQUIRED",
        "passport_paragraphs": [oracle.text(p) for p in source_body.findall(oracle.W + "p")],
        "report_paragraphs": report_paragraphs,
        "date_roles": review_date_roles(report_paragraphs),
        "cached_footer_text": [
            [oracle.text(p) for p in footer.findall(oracle.W + "p")] for footer in roles["footer"]
        ],
    }


def assess_saved_report(observer, store, *, run_id, run_ref, cursor_ref, checker_directory):
    """Evaluate receiver content after closure; leave native and Writer evidence separate."""
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D11 run ID required")
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
        raise ValueError("Exact closed D11 report run and one send required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D11 original tester deadline does not match 300 seconds")
    upload = scenario["steps"][0]["input"]
    if run["request_metadata"].get("input_sha256") != SOURCE_SHA256 or upload["sha256"] != SOURCE_SHA256:
        raise ValueError("Exact D11 passport upload required")

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    if drain.get("complete") is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D11 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D11 saved outcome differs from the retained observations")
    documents = [item for item in observations if item["kind"] == "document"]
    texts = []
    for item in observations:
        if item["kind"] == "reply_text":
            data, receipt = retained_text(observer, runner, run, item, captures, ack)
            texts.append(dict(receipt, text=data.decode("utf-8")))

    report_receipt = structure = semantic = None
    output = {"state": outcome}
    if observations:
        failures = observer.ordinary_document_output_failures({"filename": None, "mime_type": DOCX_MIME}, documents)
        if failures:
            output = {"state": "FAIL", "conditions": failures, "document_count": len(documents)}
        else:
            report, report_receipt = read_saved_docx(observer, runner, run, documents[0], captures, ack)
            name = report_receipt["name"]
            if type(name) is not str or Path(name).suffix.lower() != ".docx":
                output = {"state": "FAIL", "conditions": ["EXPECTED_DOCX_FILENAME"]}
            else:
                source = observer.read_document_input(upload, lambda: None)
                if len(source) != 13906 or digest(source) != SOURCE_SHA256:
                    raise ValueError("D11 passport bytes changed")
                oracle = load_report_checker(observer, Path(checker_directory))
                structure, semantic = report_review(oracle, source, report)
    pinned_record(observer, run_ref, expected_path=run_path)
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": SCENARIO_SHA256,
        "send_ack": run["sent_api_ack_reference"], "send_window": run["sent_window_reference"],
        "send_task": run["sent_task_reference"], "sent_message_id": run["sent_message_id"],
        "receive_head": run["receive_head"], "capture_until": run["capture_until"],
        "terminal_completed_at": drain["complete"]["completed_at"],
        "receiver_output": output, "recipient_docx": report_receipt, "direct_text_replies": texts,
        "structure": structure, "semantic_review": semantic, "native_delivery": "OPEN",
        "writer_review": "OPEN", "formal_acceptance": "OPEN",
    }
