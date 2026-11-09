#!/usr/bin/env python3
"""Check the tester's reply-wording contract on isolated offline fixtures.

The contract is ONE deterministic rule for the model's own wording of a reply:
a non-empty string 'text' is the wording, otherwise a non-empty string 'caption' is, and
otherwise the reply has no wording at all. The writer functions and the reader share it.

The review named four fixtures that must pass through the COMMON reader, with no special
branch for any run:

  1. an ordinary text reply is recorded and the common custody check accepts it;
  2. a document reply with a caption and no text field takes the same full path;
  3. an OLD text receipt without the source marker keeps confirming message.text;
  4. a substituted caption, or a substituted source, is refused.

The fixtures are built in memory and the reader is exercised on them directly; the serving
home, the tester store and every run record are untouched.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
TESTER = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(TESTER.parent))
sys.path.insert(0, str(REPO / ".runtime/friday-normal-both-workers-frw032/hermes-agent"))

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("frw_tester_contract", TESTER)
bt = importlib.util.module_from_spec(_spec)
sys.modules["frw_tester_contract"] = bt
_spec.loader.exec_module(bt)

PEER = bt.PEER
TESTER_ID = bt.TESTER


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def message(text=None, caption=None, mid=4242, date=1794210000):
    value = {"message_id": mid, "date": date,
             "chat": {"id": PEER, "type": "private"},
             "from": {"id": PEER, "is_bot": True},
             "reply_to_message": {"message_id": 4241}}
    if text is not None:
        value["text"] = text
    if caption is not None:
        value["caption"] = caption
    return value


def run_row(update_id):
    """A minimal run row the writer and the reader agree on."""
    return {"id": "contract-fixture", "scenario_sha256": "0" * 64, "step": 0,
            "sent_message_id": 4241, "sent_ids": [4241], "sent_date": 1794209999,
            "capture_until": 1794210100, "capture_start_offset": 1794209990,
            "deadline": 1794211000, "observations": [], "message_ids": [],
            "request_metadata": {"body_sha256": "0" * 64, "scenario_sha256": "0" * 64},
            "sent_api_ack_reference": {},
            "scenario": {"peer_id": PEER, "tester_id": TESTER_ID,
                         "peer_username": "@jerichodevbot", "deadline_seconds": 300,
                         "max_updates": 8, "pace_seconds": 1,
                         "steps": [{"request": "проверка контракта текста",
                                    "observe": {"mode": "bounded_reply_capture",
                                                "document_max_bytes": 8388608,
                                                "max_documents": 0, "max_messages": 8,
                                                "max_text_chars": 8000, "window_seconds": 180}}]}}


def make_update(update_id, msg):
    return {"update_id": update_id, "message": msg,
            "arrived_at": 1794210005, "context": {}}


def writer_call(runner, run, msg, update):
    """Record the wording exactly as the product's tester does."""
    return runner.keep_text(run, msg, update)


def reader_check(runner, run, update, observation, raw):
    """The COMMON reader of one reply_text receipt.

    The reader is the one the product's tester uses for every reply: the raw update's
    bytes and hash, the retained wording, its digest, the date and the source field. No
    special branch and no per-run condition is involved.
    """
    message = update["message"]
    try:
        runner.check_reply_text_receipt(message, observation, raw)
        return "ACCEPTED", None
    except Exception as exc:
        return "REFUSED", str(exc)


def main():
    runner = bt.Runner(bt.Store(bt.CANONICAL_STATE), None)
    results = []

    # 1. an ordinary text reply
    run = run_row(1)
    msg = message(text="обычный ответ модели")
    update = make_update(1794209991, msg)
    observation = writer_call(runner, run, msg, update)
    outcome, detail = reader_check(runner, run, update, observation, bt.encoded(update))
    results.append({"fixture": "an ordinary text reply", "text_source": observation.get("text_source"),
                     "reader": outcome, "detail": detail,
                     "ok": outcome == "ACCEPTED" and observation.get("text_source") == "text"})

    # 2. a document reply with a caption and no text field
    run = run_row(2)
    msg = message(caption="Дополнение сохранено в новом DOCX")
    update = make_update(1794209992, msg)
    observation = writer_call(runner, run, msg, update)
    outcome, detail = reader_check(runner, run, update, observation, bt.encoded(update))
    results.append({"fixture": "a document reply with a caption and no text field",
                     "text_source": observation.get("text_source"),
                     "reader": outcome, "detail": detail,
                     "ok": outcome == "ACCEPTED" and observation.get("text_source") == "caption"
                          and observation.get("text_acceptance") == "RECEIVED_UNGRADED"
                          and observation.get("acceptance") == "NOT_ESTABLISHED"})

    # 3. an OLD receipt without the source marker keeps confirming message.text
    run = run_row(3)
    msg = message(text="старый ответ")
    update = make_update(1794209993, msg)
    legacy = writer_call(runner, run, msg, update)
    legacy.pop("text_source", None)
    legacy["text_sha256"] = bt.digest(legacy["text"].encode("utf-8"))
    outcome, detail = reader_check(runner, run, update, legacy, bt.encoded(update))
    results.append({"fixture": "an old receipt without the source marker",
                     "reader": outcome, "detail": detail, "ok": outcome == "ACCEPTED"})
    # and the same old receipt against a reply whose text field is gone is refused
    outcome2, detail2 = reader_check(runner, run, make_update(1794209993, message(caption="подмена")), legacy,
                                      bt.encoded(make_update(1794209993, message(caption="подмена"))))
    results.append({"fixture": "an old receipt against a reply without the text field",
                     "reader": outcome2, "detail": detail2, "ok": outcome2 == "REFUSED"})

    # 4. a substituted caption or a substituted source is refused
    run = run_row(4)
    msg = message(caption="оригинальная подпись")
    update = make_update(1794209994, msg)
    observation = writer_call(runner, run, msg, update)
    swapped = dict(observation)
    swapped["text"] = "подменённая подпись"
    outcome, detail = reader_check(runner, run, update, swapped, bt.encoded(update))
    results.append({"fixture": "a substituted caption", "reader": outcome, "detail": detail,
                     "ok": outcome == "REFUSED"})
    swapped_source = dict(observation)
    swapped_source["text_source"] = "text"
    outcome, detail = reader_check(runner, run, update, swapped_source, bt.encoded(update))
    results.append({"fixture": "a substituted text source", "reader": outcome, "detail": detail,
                     "ok": outcome == "REFUSED"})
    # the reader must not accept a source that is not a known field
    bogus_source = dict(observation)
    bogus_source["text_source"] = "body"
    outcome, detail = reader_check(runner, run, update, bogus_source, bt.encoded(update))
    results.append({"fixture": "an unknown text source", "reader": outcome, "detail": detail,
                     "ok": outcome == "REFUSED"})

    for result in results:
        say(**result)
    say(summary={"fixtures": len(results),
                 "passed": sum(1 for r in results if r["ok"]),
                 "ok": all(r["ok"] for r in results)})
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
