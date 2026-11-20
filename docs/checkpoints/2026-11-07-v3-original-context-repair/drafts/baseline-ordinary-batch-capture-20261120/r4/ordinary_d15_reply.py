"""Read the closed D15 capture prefix and screen the exact final saved summary."""

from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import re

from ordinary_d03_reply import original_ack, pinned_record, retained_text
from ordinary_d15_ordered import DAMAGED_PHASES as DAMAGED_SCENARIO_HASHES


PHASES = (
    ("D15-ALT-01", "090f7276e1017c2ae2d3583f98db60702a2c0aa5baba1d069b80ac9b443c600b",
     "92ebf4d65763ae161a5e292ef758548a4ec801c516bf0260ea0c2c020f8d3a4b", 227),
    ("D15-ALT-02", "5c7ceffc7a22b17c67257f73efbb963d22ee85c7a78498700abc613fea821f3a",
     "981d9b0bf30acfe3d2201d584d49c7ea414adeec290a53233fa5ae1a06f597fc", 229),
    ("D15-ALT-03", "a29e35c039f7f851fa2bcf220721859edfdf6f351bca41147509b714b0d24c68",
     "374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb", 16),
)
ORACLE_SHA256 = "1c0e272b634ebab44543cba7b12b04c563cc70bab31f56302271ad0e0c9ffddf"
FACTS_SHA256 = "d7bc69a9d941fc49dabe6b889fbc3534c2105b480e81f2e79619674778453186"
DAMAGED_FACTS_SHA256 = "f76e1abc9604e60e5e02a014bdf3c752e8759ab84625725c021767579e5c38f5"
DAMAGED_PHASES = tuple(zip(
    ("D15-DAMAGED-01", "D15-DAMAGED-02", "D15-DAMAGED-03"),
    DAMAGED_SCENARIO_HASHES,
    ("39c2677207c53e4d274220543100c1b6d4dcd4964c790e4732f26c516416ef03",
     "2dfb6a9a483b27c4d9e8e035a72d67d901ac79bff71ff29efc9025271b65a6dd",
     "36e40b4b85b83c3a18d500594dae39e8eac3d08a9d5ca03116dd9b72a5e250be"),
    (245, 245, 1084),
    strict=True,
))
SERIES = {"unsupported": (PHASES, FACTS_SHA256), "damaged_docx": (DAMAGED_PHASES, DAMAGED_FACTS_SHA256)}


def digest(data):
    return sha256(data).hexdigest()


def _series(variant):
    if type(variant) is not str or variant not in SERIES:
        raise ValueError("Exact D15 saved series variant required")
    return SERIES[variant]


def read_closed_phase(observer, runner, cursor, position, run_id, run_ref, *, variant="unsupported"):
    if type(run_id) is not str or not re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id):
        raise ValueError("Exact D15 phase run ID required")
    phases, _ = _series(variant)
    run = pinned_record(observer, run_ref, expected_path=runner.store.run_path(run_id))
    name, scenario_sha, source_sha, source_size = phases[position]
    scenario = run["scenario"]
    if (run.get("id") != run_id or run.get("scenario_sha256") != scenario_sha
            or digest(observer.encoded(scenario)) != scenario_sha
            or type(run.get("step")) is not int or run["step"] != 0
            or type(run.get("send_attempts")) is not int or run["send_attempts"] != 1
            or run.get("send_state") != "sent" or run.get("sent_ids") != [run.get("sent_message_id")]
            or run.get("status") != "EVIDENCE_READY" or run.get("capture_window_complete") is not True):
        raise ValueError("Exact closed D15 prefix and one send per phase required")
    created, deadline = datetime.fromisoformat(run["created_at"]), run["deadline"]
    if (created.utcoffset() is None or type(deadline) not in (int, float) or not math.isfinite(deadline)
            or abs(deadline - created.timestamp() - 300) > 1):
        raise ValueError("D15 original tester deadline does not match 300 seconds")
    upload = scenario["steps"][0]["input"]
    if run["request_metadata"].get("input_sha256") != source_sha or upload["sha256"] != source_sha:
        raise ValueError("Exact D15 source upload required")
    raw = observer.read_document_input(upload, lambda: None)
    if len(raw) != source_size or digest(raw) != source_sha:
        raise ValueError("D15 source bytes changed")
    runner.verify_reply_custody(run, cursor)
    ack = original_ack(observer, runner, run)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    poll = runner.read_poll_intent(run)
    terminal = drain.get("complete")
    if terminal is None or (poll is not None and poll["outcome"] == "PENDING"):
        raise ValueError("D15 original receive window is unsettled")
    observations = run["observations"]
    outcome = "RECEIVED_UNGRADED" if observations else "NO_RESPONSE_UNVERIFIED"
    if run.get("reply_outcome") != outcome:
        raise ValueError("D15 saved outcome differs from the retained observations")
    update_ids = [item["update_id"] for item in observations]
    if update_ids != sorted(set(update_ids)):
        raise ValueError("Exact ordered D15 observations required")
    replies = []
    for item in observations:
        body, receipt = retained_text(observer, runner, run, item, captures, ack)
        replies.append(dict(receipt, text=body.decode("utf-8")))
    return {
        "phase": name, "run_id": run_id, "run_sha256": run_ref["sha256"], "scenario_sha256": scenario_sha,
        "source_name": upload["filename"], "source_sha256": source_sha, "source_bytes": source_size,
        "send_ack": run["sent_api_ack_reference"], "send_task": run["sent_task_reference"],
        "send_window": run["sent_window_reference"], "sent_message_id": run["sent_message_id"],
        "send_intent_at": run["send_intent_at"], "send_dispatch_at": run["send_dispatch_at"],
        "sent_at": run["sent_at"], "deadline": deadline, "capture_until": run["capture_until"],
        "receive_head": run["receive_head"], "terminal_completed_at": terminal["completed_at"],
        "outcome": outcome, "direct_text_replies": replies, "explicit_refusal_observed": run.get("refusal_observed") is True,
    }


def grade_summary(observer, phase, oracle_directory, *, variant="unsupported"):
    _, facts_sha256 = _series(variant)
    if phase["outcome"] == "NO_RESPONSE_UNVERIFIED":
        return {"state": phase["outcome"]}
    replies = phase["direct_text_replies"]
    if len(replies) != 1:
        return {"state": "REVIEW_REQUIRED", "screen": "EXPECTED_ONE_WHOLE_JSON_REPLY"}
    path = Path(oracle_directory) / "d15_oracle.py"
    source = observer.safe_read(path, 65536)
    facts = observer.safe_read(path.with_name("ORACLE.json"), 65536)
    if digest(source) != ORACLE_SHA256 or digest(facts) != facts_sha256:
        raise ValueError("Exact D15 checker and ten-fact basis required")
    oracle = {"__file__": str(path), "__name__": "_d15_pinned_summary_oracle"}
    exec(compile(source, str(path), "exec"), oracle)
    basis = json.loads(facts, object_pairs_hook=observer.unique_object)
    try:
        screen = oracle["grade"](replies[0]["text"], basis)
    except RecursionError:
        screen = "INVALID_SUMMARY_TEXT"
    state = "FACTS_MATCH_FOR_REVIEW" if screen == "TEXT_AND_FACTS_MATCH_FOR_REVIEW" else "REVIEW_REQUIRED"
    return {"state": state, "screen": screen, "reply_text_sha256": replies[0]["text_sha256"]}


def assess_saved_series(observer, store, *, stages, cursor_ref, oracle_directory, variant="unsupported"):
    """Assess a closed exact prefix using the existing receiver artifacts and checker."""
    phases, _ = _series(variant)
    if type(stages) not in (list, tuple) or not 1 <= len(stages) <= len(phases):
        raise ValueError("Exact D15 stage prefix required")
    cursor_path = store.root / "cursor.json"
    cursor = pinned_record(observer, cursor_ref, expected_path=cursor_path)
    runner = observer.Runner(store, None)
    series = []
    seen_message_ids = set()
    for position, stage in enumerate(stages):
        if type(stage) is not dict or set(stage) != {"run_id", "run_ref"}:
            raise ValueError("Exact D15 stage reference required")
        phase = read_closed_phase(observer, runner, cursor, position, stage["run_id"], stage["run_ref"], variant=variant)
        message_ids = [phase["sent_message_id"], *(row["tester_reply_message_id"] for row in phase["direct_text_replies"])]
        if len(set(message_ids)) != len(message_ids) or seen_message_ids.intersection(message_ids):
            raise ValueError("D15 stages reuse a tester-side message identity")
        seen_message_ids.update(message_ids)
        if series:
            prior = series[-1]
            if (prior["outcome"] != "RECEIVED_UNGRADED"
                    or min(phase["send_intent_at"], phase["send_dispatch_at"])
                    < max(prior["deadline"], prior["terminal_completed_at"])):
                raise ValueError("D15 successor preceded the prior settled original window or has no prior reply")
        series.append(phase)

    for phase in series[:2]:
        phase["handover_assessment"] = (
            "INDEPENDENT_REVIEW_REQUIRED" if phase["direct_text_replies"] else phase["outcome"]
        )
    summary = (grade_summary(observer, series[-1], oracle_directory, variant=variant)
               if len(series) == len(phases) else {"state": "OPEN"})
    for stage in stages:
        pinned_record(observer, stage["run_ref"], expected_path=store.run_path(stage["run_id"]))
    pinned_record(observer, cursor_ref, expected_path=cursor_path)
    return {
        "stages": series, "summary": summary, "independent_prior_and_same_native_lineage": "OPEN",
        "two_full_registered_text_reads_and_named_refusal": "OPEN", "formal_acceptance": "OPEN",
    }
