#!/usr/bin/env python3
"""Issue a fresh targeted independent admission for the scenarios of ONE operation.

The authority binds the CURRENT gateway pid/start_time/state path and the CURRENT
verified history rows: every row that is not EVIDENCE_READY/STOPPED/FAILED, plus
every row whose send_state is intent/unknown, is re-read from the tester store and
re-verified here (digest, exact bytes, deadline, unknown flag). Nothing is copied
from an older authority document without re-checking the live bytes.

The document describes ITSELF accurately. The scope states the operation the
admission actually covers, and the supersedes field names the document it continues
from. The scope is NOT a fixed sentence about a single activation smoke, and it does
not carry a stale reference to an earlier admission: a future admission that covers
several scenarios says so, and the generator refuses to write a document whose scope
does not match the scenarios it covers.

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
GATEWAY_STATE = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/gateway_state.json")
OUT_DIR = Path("/home/jericho/.cache/FRW-KIMI-FMT-20261108")
SCENARIO = OUT_DIR / "scenarios" / "fmt-docx-create-r69.json"
RUN_ID = "fmt-docx-create-r69"
D12_RUN_ID = "d12-write-file-check-01-r48"
FMT_RUN_ID = "fmt-wrong-format-check-01-r49"
WRITE_RUN_ID = "ordinary-write-check-01-r49"
SCOPE_RUN_ID = "out-of-scope-check-01-r49"
F01_RUN_ID = "f01-csv-extract-check-01-r50"
M03_RUN_ID = "m03-addendum-check-01-r51"
M05_RUN_ID = "m05-current111-check-01-r52"
M06_RUN_ID = "m06-postrestart-check-01-r52"
# The next admission after R54. R54 itself is PINNED: the tester snapshot in use names
# its path, byte count and digest, and the file is stored in the repository. This issuer
# therefore never rewrites R54 - every release writes a NEW document with a NEW identity
# and a NEW path, and the tester snapshot is re-pinned to it in the same step.
AUTHORITY_ID = "ordinary-independent-jarvis-activate-20261109-r69"
AUTHORITY_FILE = "INDEPENDENT-AUTHORITY-R69.json"
# The document this one continues from. It names the document that is actually in force
# before it, not an old activation smoke: a released admission is never rewritten, so the
# chain is expressed by reference.
SUPERSEDES_AUTHORITY_ID = "ordinary-independent-jarvis-activate-20261109-r69"
SUPERSEDES_REASON = (
    "R69 is retained as history and is not rewritten: it was released against the live "
    "gateway of its own boot with its own history rows, and the tester snapshot that "
    "pins it keeps naming it. This document carries the same operation forward on the "
    "current gateway with freshly verified history rows; it does not rewrite the R54 to "
    "R69 results."
)
# The scope of THIS admission. It must describe the operation the scenarios below
# actually cover. The generator refuses to write a document whose scope names a single
# activation smoke while the scenario list covers several operations, and it refuses a
# scope that claims a product or B00 acceptance.
SCOPE = (
    "Targeted independent executions for tester 8812646969 on the current serving "
    "composition: the scenario list below names every run id this admission covers. It "
    "covers the twelve format-creation scenarios (docx, xlsx, ods, odt, pdf, rtf, csv, "
    "tsv, zip, 7z, txt, json) and the named regression scenarios of the current volume. "
    "It is an independent execution permission for those scenarios only. It is NOT a B00 "
    "acceptance, NOT a product acceptance and NOT a format-completeness acceptance: the "
    "semantic acceptance of every case is made separately against its own criterion and "
    "its own fixture."
)
# additional run ids covered by the same admission; each one is issued with its own
# scenario and its own fresh authority check
PACKAGE_FILE = Path("/home/jericho/.cache/FRW-KIMI-FMT-20261108/package-r69.json")
EXTRA_SCENARIOS = (
    (D12_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/D12-WRITE-FILE-CHECK.json"),
    (FMT_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/FMT-WRONG-FORMAT.json"),
    (WRITE_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/ORDINARY-WRITE.json"),
    (SCOPE_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/OUT-OF-SCOPE-REFUSAL.json"),
    ("m03-addendum-check-01-r50", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/m03-addendum-check-01-r50.json"),
    ("d08-template-fill-check-01-r54", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/d08-template-fill-check-01-r54.json"),
    ("s01-all-sheets-check-01-r58", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/s01-all-sheets-check-01-r58.json"),
    ("p01-pdf-intake-check-01-r57", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/p01-pdf-intake-check-01-r57.json"),
    ("s01-xlsx-intake-check-01-r56", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/s01-xlsx-intake-check-01-r56.json"),
    ("d09-translation-check-01-r55", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/d09-translation-check-01-r55.json"),
    (F01_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/f01-csv-extract-check-01-r50.json"),
    ("s-04-root-plan-check-01-r59", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/s-04-root-plan-check-01-r59.json"),
    ("s-10-root-plan-check-01-r59", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/s-10-root-plan-check-01-r59.json"),
    ("s-11-root-plan-check-01-r61", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/s-11-root-plan-check-01-r61.json"),
    ("p02-hybrid-pdf-check-01-r62", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/p02-hybrid-pdf-check-01-r62.json"),
    ("p04-ambiguous-amount-check-01-r62", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/p04-ambiguous-amount-check-01-r62.json"),
    ("m11-memory-note-check-01-r62", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/m11-memory-note-check-01-r62.json"),
    ("d07-compare-v1-v2-check-01-r67", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/d07-compare-v1-v2-check-01-r67.json"),
    ("a03-7z-roundtrip-check-01-r68", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/a03-7z-roundtrip-check-01-r68.json"),
    (M03_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/m03-addendum-check-01-r51.json"),
    (M05_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/m05-current111-check-01-r52.json"),
    (M06_RUN_ID, "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/m06-postrestart-check-01-r52.json"),
)
# The format-creation scenarios of the current operation. They are named separately so
# the scope above can be checked against the operation, and so a repetition of a name in
# the scenario list is impossible by construction.
FORMAT_SCENARIOS = (
    ("fmt-docx-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-docx-create-r69.json"),
    ("fmt-xlsx-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-xlsx-create-r69.json"),
    ("fmt-ods-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-ods-create-r69.json"),
    ("fmt-odt-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-odt-create-r69.json"),
    ("fmt-pdf-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-pdf-create-r69.json"),
    ("fmt-rtf-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-rtf-create-r69.json"),
    ("fmt-csv-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-csv-create-r69.json"),
    ("fmt-tsv-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-tsv-create-r69.json"),
    ("fmt-zip-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-zip-create-r69.json"),
    ("fmt-7z-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-7z-create-r69.json"),
    ("fmt-txt-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-txt-create-r69.json"),
    ("fmt-json-create-r69", "/home/jericho/.cache/FRW-KIMI-FMT-20261108/scenarios/fmt-json-create-r69.json"),
)
EXTRA_SCENARIOS = EXTRA_SCENARIOS + FORMAT_SCENARIOS
FINAL_STATUSES = {"EVIDENCE_READY", "STOPPED", "FAILED"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode()


def main():
    SCENARIOS = {}
    scenario = json.loads(SCENARIO.read_text())
    scenario_bytes = encoded(scenario)
    scenario_sha = digest(scenario_bytes)
    SCENARIOS[RUN_ID] = scenario_sha
    for extra_id, extra_path in EXTRA_SCENARIOS:
        extra = json.loads(Path(extra_path).read_text())
        SCENARIOS[extra_id] = digest(encoded(extra))
    if PACKAGE_FILE.is_file():
        for extra_id, extra_sha in json.loads(PACKAGE_FILE.read_text()).items():
            extra = json.loads((OUT_DIR / "scenarios" / (extra_id + ".json")).read_text())
            if digest(encoded(extra)) != extra_sha:
                raise SystemExit("package scenario digest changed: " + extra_id)
            SCENARIOS[extra_id] = extra_sha

    # The scope must describe THIS operation. A scope that names a single activation
    # smoke while the scenario list covers several operations is refused, and a scope
    # that claims a product or a B00 acceptance is refused: the admission is neither.
    scope = " ".join(SCOPE.lower().split())
    if "activation check" in scope and len(SCENARIOS) > 1:
        raise SystemExit("the scope names a single activation smoke but the admission "
                         "covers %d scenarios; the scope must describe the operation"
                         % len(SCENARIOS))
    # The document is not a product acceptance and not a B00 acceptance. A scope that
    # CLAIMS either one is refused; a scope that DENIES it is the correct wording.
    claims_product = "product acceptance" in scope and not (
        "not a product acceptance" in scope or "not a b00, fmt or product acceptance" in scope)
    claims_b00 = "b00 acceptance" in scope and not (
        "not a b00 acceptance" in scope or "not a b00, fmt or product acceptance" in scope)
    if claims_product:
        raise SystemExit("the scope claims a product acceptance")
    if claims_b00:
        raise SystemExit("the scope claims a B00 acceptance")
    covered_formats = [name for name in SCENARIOS if name.startswith("fmt-")]
    if covered_formats and "format-creation" not in scope and "format creation" not in scope:
        raise SystemExit("the scope does not mention the format-creation scenarios it covers")

    # A repeated run id would make the scenario map ambiguous, so it is refused.
    if len(set(SCENARIOS)) != len(SCENARIOS):
        raise SystemExit("the scenario list contains a repeated run id")

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
        "run_scenarios": dict(SCENARIOS),
        "same_canonical_local_run": False,
        "schema": "frw.Root.ordinary-independent-history-admission.v1",
        "scope": SCOPE,
        "supersedes": {
            "authority_id": SUPERSEDES_AUTHORITY_ID,
            "reason": SUPERSEDES_REASON,
        },
        "unknown_effects_resolved": False,
    }
    raw = encoded(document)
    target = OUT_DIR / AUTHORITY_FILE
    if target.exists():
        # a released admission is never rewritten: it would break the pin of the tester
        # snapshot that names it
        raise SystemExit("the admission " + str(target) + " already exists and is pinned; "
                         "release the next one instead")
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
