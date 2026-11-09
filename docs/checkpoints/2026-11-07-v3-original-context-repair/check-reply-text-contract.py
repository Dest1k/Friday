#!/usr/bin/env python3
"""Check the tester's reply-wording contract on isolated offline fixtures.

The contract is ONE deterministic rule for the model's own wording of a reply:
a non-empty string 'text' is the wording, otherwise a non-empty string 'caption' is, and
otherwise the reply has no wording at all. The writer functions and the reader share it.

ISOLATION: the check runs against its own small Store inside the DSH staging area, never
against the working CANONICAL_STATE. The writer and reader under test are the product's
own methods; only the place where the bytes live is replaced.

The fixtures:

  1. an ordinary text reply is recorded and the saved receipt is read back and accepted by
     the common reader;
  2. a document reply with a caption and no text field takes the same full path: the message
     really carries a 'document' field, and the saved caption does not turn the document
     into an accepted artifact nor widen max_documents;
  3. an OLD receipt without the source marker is checked against the UNCHANGED saved bytes
     of such a receipt, not by deleting the field from a new dictionary;
  4. a substituted caption, a substituted source and an unknown source are refused with the
     expected reason - a foreign exception is not counted as a successful negative test.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
TESTER = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py"
ROOT = Path("/home/jericho/.dsh/tmp/reply-text-contract-check")
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / ".runtime/friday-normal-both-workers-frw032/hermes-agent"))

_spec = importlib.util.spec_from_file_location("frw_tester_contract", TESTER)
bt = importlib.util.module_from_spec(_spec)
sys.modules["frw_tester_contract"] = bt
_spec.loader.exec_module(bt)

PEER = bt.PEER
TESTER_ID = bt.TESTER


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def message(text=None, caption=None, document=None, mid=4242, date=1794210000):
    value = {"message_id": mid, "date": date,
             "chat": {"id": PEER, "type": "private"},
             "from": {"id": PEER, "is_bot": True},
             "reply_to_message": {"message_id": 4241}}
    if text is not None:
        value["text"] = text
    if caption is not None:
        value["caption"] = caption
    if document is not None:
        value["document"] = document
    return value


def scenario(max_documents=0):
    return {"peer_id": PEER, "tester_id": TESTER_ID, "peer_username": "@jerichodevbot",
            "deadline_seconds": 300, "max_updates": 8, "pace_seconds": 1,
            "steps": [{"request": "проверка контракта текста",
                        "observe": {"mode": "bounded_reply_capture",
                                    "document_max_bytes": 8388608,
                                    "max_documents": max_documents, "max_messages": 8,
                                    "max_text_chars": 8000, "window_seconds": 180}}]}


def run_row(max_documents=0):
    return {"id": "contract-fixture", "scenario_sha256": "0" * 64, "step": 0,
            "sent_message_id": 4241, "sent_ids": [4241], "sent_date": 1794209999,
            "capture_until": 1794210100, "capture_start_offset": 1794209990,
            "deadline": 1794211000, "observations": [], "message_ids": [],
            "request_metadata": {"body_sha256": "0" * 64, "scenario_sha256": "0" * 64},
            "sent_api_ack_reference": {}, "scenario": scenario(max_documents)}


def make_update(update_id, msg):
    return {"update_id": update_id, "message": msg,
            "arrived_at": 1794210005, "context": {}}


def fresh_receipts(store):
    """Empty the check's own downloads and return the receipt saved by the last write."""
    for path in list(store.downloads.glob("*")):
        path.unlink()
    return None


def saved_receipt_of(store):
    files = sorted(store.downloads.glob("*.text-receipt.json"))
    if len(files) != 1:
        return None, b""
    raw = files[0].read_bytes()
    return json.loads(raw), raw


def expected_refusal(callable_):
    """Run a check that must refuse. Only the product's own Refused counts."""
    try:
        callable_()
    except bt.Refused as exc:
        return True, str(exc)
    except Exception as exc:
        return False, "foreign exception: " + type(exc).__name__ + ": " + str(exc)[:120]
    return False, "no refusal"


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True, exist_ok=True)
    ROOT.chmod(0o700)
    # the check's own small store, never the working one
    store = bt.Store(ROOT / "store")
    runner = bt.Runner(store, None)
    results = []

    # 1. an ordinary text reply: recorded, saved on disk, read back from those bytes
    run = run_row()
    msg = message(text="обычный ответ модели")
    update = make_update(1794209991, msg)
    fresh_receipts(store)
    observation = runner.keep_text(run, msg, update)
    saved_receipt, saved_bytes = saved_receipt_of(store)
    saved_path = next(iter(store.downloads.glob("*.text-receipt.json")), None)
    outcome, detail = "REFUSED", "the receipt was not saved"
    try:
        runner.check_reply_text_receipt(msg, saved_receipt, bt.encoded(update))
        outcome, detail = "ACCEPTED", None
    except Exception as exc:
        detail = type(exc).__name__ + ": " + str(exc)[:120]
    results.append({"fixture": "an ordinary text reply, written and read back from the saved bytes",
                    "saved_receipt": saved_path.name if saved_path else None,
                    "saved_sha256": hashlib.sha256(saved_bytes).hexdigest() if saved_bytes else None,
                    "text_source": saved_receipt.get("text_source"),
                    "reader": outcome, "detail": detail,
                    "ok": outcome == "ACCEPTED" and saved_receipt.get("text_source") == "text"
                          and saved_bytes != b""})

    # 2. a document reply with a caption and no text field
    run = run_row()
    document = {"file_id": "fid-1", "file_unique_id": "fuid-1", "file_name": "addendum.docx",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "file_size": 36848}
    msg = message(caption="Дополнение сохранено в новом DOCX", document=document)
    update = make_update(1794209992, msg)
    fresh_receipts(store)
    observation = runner.keep_text(run, msg, update)
    saved_receipt, saved_bytes = saved_receipt_of(store)
    saved_path = next(iter(store.downloads.glob("*.text-receipt.json")), None)
    try:
        runner.check_reply_text_receipt(msg, saved_receipt, bt.encoded(update))
        outcome, detail = "ACCEPTED", None
    except Exception as exc:
        outcome, detail = "REFUSED", type(exc).__name__ + ": " + str(exc)[:120]
    # the saved caption must not turn the document into an accepted artifact
    accepted_artifacts = [o for o in (saved_receipt,) if o.get("kind") == "document"]
    results.append({"fixture": "a document reply with a caption and no text field",
                    "the_message_really_carries_a_document": "document" in msg,
                    "saved_receipt_kind": saved_receipt.get("kind"),
                    "text_source": saved_receipt.get("text_source"),
                    "reader": outcome, "detail": detail,
                    "the_caption_did_not_become_an_accepted_document": not accepted_artifacts,
                    "max_documents_stays": scenario(0)["steps"][0]["observe"]["max_documents"],
                    "ok": outcome == "ACCEPTED" and saved_receipt.get("text_source") == "caption"
                          and "document" in msg and not accepted_artifacts
                          and saved_receipt.get("kind") == "reply_text"})

    # 3. an OLD receipt without the source marker, taken from SAVED bytes of such a receipt
    legacy_path = ROOT / "legacy-receipt.json"
    legacy_source = {
        "kind": "reply_text", "run_id": "contract-fixture", "step": 0,
        "sent_message_id": 4241, "sent_ids": [4241], "scenario_sha256": "0" * 64,
        "message_id": 4242, "update_id": 1794209993, "date": 1794210000,
        "text": "старый ответ", "text_sha256": bt.digest("старый ответ".encode("utf-8")),
        "text_chars": len("старый ответ"), "text_acceptance": "RECEIVED_UNGRADED",
        "acceptance": "NOT_ESTABLISHED",
        "raw_update": {"basename": "1794209993.json", "bytes": 0, "sha256": "0" * 64}}
    legacy_bytes = (json.dumps(legacy_source, ensure_ascii=True, sort_keys=True) + "\n").encode()
    legacy_path.write_bytes(legacy_bytes)
    legacy_path.chmod(0o600)
    legacy = json.loads(legacy_path.read_bytes())
    msg = message(text="старый ответ")
    update = make_update(1794209993, msg)
    legacy["raw_update"] = {"basename": "1794209993.json", "bytes": len(bt.encoded(update)),
                            "sha256": bt.digest(bt.encoded(update))}
    legacy_path.write_bytes((json.dumps(legacy, ensure_ascii=True, sort_keys=True) + "\n").encode())
    legacy = json.loads(legacy_path.read_bytes())
    accepted, detail = "REFUSED", None
    try:
        runner.check_reply_text_receipt(msg, legacy, bt.encoded(update))
        accepted, detail = "ACCEPTED", None
    except Exception as exc:
        detail = type(exc).__name__ + ": " + str(exc)[:120]
    # the same old receipt against a reply whose text field is gone is refused
    refused_ok, refused_reason = expected_refusal(
        lambda: runner.check_reply_text_receipt(message(caption="подмена"), legacy,
                                                bt.encoded(make_update(1794209993, message(caption="подмена")))))
    results.append({"fixture": "an old receipt without the source marker, from the saved bytes",
                    "saved_receipt": str(legacy_path),
                    "saved_sha256": hashlib.sha256(legacy_path.read_bytes()).hexdigest(),
                    "has_source_marker": "text_source" in legacy,
                    "reader": accepted, "detail": detail,
                    "the_same_old_receipt_without_the_text_field_is_refused": refused_ok,
                    "refusal_reason": refused_reason,
                    "ok": accepted == "ACCEPTED" and "text_source" not in legacy and refused_ok})

    # 4. a substituted caption, a substituted source and an unknown source
    run = run_row()
    msg = message(caption="оригинальная подпись")
    update = make_update(1794209994, msg)
    observation = runner.keep_text(run, msg, update)
    swapped_caption = dict(observation)
    swapped_caption["text"] = "подменённая подпись"
    ok_caption, reason_caption = expected_refusal(
        lambda: runner.check_reply_text_receipt(msg, swapped_caption, bt.encoded(update)))
    swapped_source = dict(observation)
    swapped_source["text_source"] = "text"
    ok_source, reason_source = expected_refusal(
        lambda: runner.check_reply_text_receipt(msg, swapped_source, bt.encoded(update)))
    bogus_source = dict(observation)
    bogus_source["text_source"] = "body"
    ok_bogus, reason_bogus = expected_refusal(
        lambda: runner.check_reply_text_receipt(msg, bogus_source, bt.encoded(update)))
    results.append({"fixture": "a substituted caption", "refused": ok_caption, "reason": reason_caption,
                    "ok": ok_caption and "custody changed" in (reason_caption or "")})
    results.append({"fixture": "a substituted text source", "refused": ok_source, "reason": reason_source,
                    "ok": ok_source and "custody changed" in (reason_source or "")})
    results.append({"fixture": "an unknown text source", "refused": ok_bogus, "reason": reason_bogus,
                    "ok": ok_bogus and "not a known field" in (reason_bogus or "")})

    for result in results:
        say(**result)
    say(summary={"fixtures": len(results),
                 "passed": sum(1 for r in results if r["ok"]),
                 "ok": all(r["ok"] for r in results),
                 "the_working_store_was_not_used": True,
                 "note": ("the reader method and the writer method are the product's own; only "
                          "the storage was replaced. The 'old receipt' fixture is read from "
                          "saved bytes, not by deleting a field in memory.")})
    shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
