#!/usr/bin/env python3
"""Issue a fresh targeted independent admission for one new run id.

The authority binds the CURRENT gateway pid/start_time/state path and the CURRENT
verified history rows: every row that is not EVIDENCE_READY/STOPPED/FAILED, plus
every row whose send_state is intent/unknown, is re-read from the tester store and
re-verified here (digest, exact bytes, deadline, unknown flag). Nothing is copied
from an older authority document without re-checking the live bytes.

Output is the authority document in the tester's encoded() form:
    json.dumps(value, ensure_ascii=True, sort_keys=True) + "\\n"
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

STATE = Path("/home/jericho/.local/share/friday-telegram-bot-test")
RUNS = STATE / "runs"
GATEWAY_STATE = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108/gateway_state.json")
OUT_DIR = Path("/home/jericho/.cache/FRW-KIMI-FMT-20261108")
SCENARIO = OUT_DIR / "scenarios" / "R44-JARVIS-ACTIVATE-CHECK.json"
RUN_ID = "jarvis-activate-check-01-r44"
AUTHORITY_ID = "ordinary-independent-jarvis-activate-20261108-r44"
FINAL_STATUSES = {"EVIDENCE_READY", "STOPPED", "FAILED"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode()


def main():
    scenario = json.loads(SCENARIO.read_text())
    scenario_bytes = encoded(scenario)
    scenario_sha = digest(scenario_bytes)

    now = time.time()
    history = {}
    needed = []
    for path in sorted(RUNS.glob("*.json")):
        raw = path.read_bytes()
        row = json.loads(raw)
        if row.get("status") in FINAL_STATUSES and row.get("send_state") not in ("intent", "unknown"):
            continue
        needed.append((path.name, row))

    for name, row in needed:
        raw = (RUNS / name).read_bytes()
        row = json.loads(raw)
        if digest(raw) != digest(encoded(row)) or encoded(row) != raw:
            raise SystemExit("history row bytes are not canonical: " + name)
        history[row["id"]] = {
            "deadline": row["deadline"],
            "new_effect_replay_authorized": False,
            "send_state": row["send_state"],
            "sha256": digest(raw),
            "status": row["status"],
            "unknown_retained": row["send_state"] == "unknown",
        }
        if now < row["deadline"]:
            raise SystemExit("history row still live (deadline in the future): " + row["id"])

    state = json.loads(GATEWAY_STATE.read_text())
    pid = int(state["pid"])
    start_time = int(state["start_time"])
    stat = Path("/proc") / str(pid) / "stat"
    if not stat.exists() or stat.read_text().split()[21] != str(start_time):
        raise SystemExit("gateway process identity does not match the state file")

    document = {
        "accepted": True,
        "authority_id": AUTHORITY_ID,
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "canonical_encoding": {
            "canonical_sha256": "json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(',', ':')) with no trailing newline",
            "tester_sha256": "bot_tester.encoded(scenario): json.dumps(scenario, ensure_ascii=True, sort_keys=True) + newline",
        },
        "created_at": now,
        "created_at_moscow": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
        "expires_at": now + 6 * 3600,
        "gateway": {
            "maximum_staleness_seconds": 600,
            "pid": pid,
            "start_time": start_time,
            "state_path": str(GATEWAY_STATE),
        },
        "history": history,
        "new_independent_inputs_only": True,
        "new_trial_for_historical_task": False,
        "no_old_task_replay": True,
        "old_rows_modified": False,
        "operator": "Root",
        "product_or_B00_acceptance": False,
        "run_scenarios": {RUN_ID: scenario_sha},
        "same_canonical_local_run": False,
        "schema": "frw.Root.ordinary-independent-history-admission.v1",
        "scope": ("One controlled Jarvis-area activation check from tester 8812646969 after the user "
                  "areas were restored through the product's onboarding path. Not a B00, FMT or "
                  "product acceptance."),
        "supersedes": {
            "authority_id": "ordinary-independent-jarvis-restore-20261108-r43",
            "reason": "the R43 binding names a gateway process that no longer exists; a fresh binding to the current gateway is required",
        },
        "unknown_effects_resolved": False,
    }
    raw = encoded(document)
    target = OUT_DIR / "INDEPENDENT-AUTHORITY-R44.json"
    target.write_bytes(raw)
    os.chmod(target, 0o600)
    print(json.dumps({
        "path": str(target), "bytes": len(raw), "sha256": digest(raw),
        "run_id": RUN_ID, "scenario_sha256": scenario_sha,
        "history_rows": len(history), "gateway_pid": pid, "gateway_start_time": start_time,
        "history_row_ids": sorted(history),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
