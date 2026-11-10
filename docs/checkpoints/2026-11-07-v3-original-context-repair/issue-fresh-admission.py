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
# The next admission is derived from the ACTUAL released documents: the highest
# INDEPENDENT-AUTHORITY-R*.json in OUT_DIR is the predecessor, and the new identity is
# the next free number. A released admission is never rewritten, so the chain is
# expressed by reference and every release writes a NEW document with a NEW identity
# and a NEW path.
AUTHORITY_ID = None    # filled by derive_identity()
AUTHORITY_FILE = None  # filled by derive_identity()
SUPERSEDES_AUTHORITY_ID = None  # filled by derive_identity()
SUPERSEDES_REASON = (
    "The previous admission is retained as history and is not rewritten: it was "
    "released against the live gateway of its own boot with its own history rows, and "
    "the tester snapshot that pins it keeps naming it. This document carries the same "
    "operation forward on the current gateway with freshly verified history rows; it "
    "does not rewrite any earlier result."
)


def derive_identity(out_dir):
    """Derive the identity of the next admission from the actually released documents.

    Returns (authority_id, authority_file, supersedes_authority_id). The predecessor is
    the released document with the highest R number; the new identity is the next free
    number. Refuses to derive a self-superseding identity and refuses when no
    predecessor exists.
    """
    out = Path(out_dir)
    released = {}
    for path in out.glob("INDEPENDENT-AUTHORITY-R*.json"):
        stem = path.stem  # INDEPENDENT-AUTHORITY-R69
        if not stem.startswith("INDEPENDENT-AUTHORITY-R"):
            continue
        tail = stem[len("INDEPENDENT-AUTHORITY-R"):]
        if not tail.isdigit():
            continue
        released[int(tail)] = path
    if not released:
        raise SystemExit("no released admission found in " + str(out) + "; cannot derive the chain")
    prev_n = max(released)
    prev_doc = json.loads(released[prev_n].read_text())
    prev_id = prev_doc.get("authority_id")
    if not isinstance(prev_id, str) or not prev_id:
        raise SystemExit("the predecessor document has no authority_id: " + str(released[prev_n]))
    new_n = prev_n + 1
    # the new identity carries the CURRENT date and the next free number
    date = time.strftime("%Y%m%d", time.localtime())
    prefix = prev_id.rsplit("-r", 1)[0]  # e.g. ordinary-independent-jarvis-activate-20261109
    # replace the date part of the prefix with today's date
    parts = prefix.split("-")
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].isdigit() and len(parts[i]) == 8:
            parts[i] = date
            break
    new_id = "-".join(parts) + "-r" + str(new_n)
    new_file = "INDEPENDENT-AUTHORITY-R" + str(new_n) + ".json"
    if new_id == prev_id:
        raise SystemExit("derived identity equals the predecessor (self-supersedes): " + new_id)
    return new_id, new_file, prev_id


def validate_identity(authority_id, supersedes_id, out_dir):
    """Refuse a self-superseding identity and a missing predecessor."""
    if not isinstance(authority_id, str) or not authority_id:
        raise SystemExit("authority_id is required")
    if not isinstance(supersedes_id, str) or not supersedes_id:
        raise SystemExit("supersedes authority_id is required")
    if authority_id == supersedes_id:
        raise SystemExit("the admission supersedes itself: " + authority_id)
    out = Path(out_dir)
    pred = [p for p in out.glob("INDEPENDENT-AUTHORITY-R*.json")
            if json.loads(p.read_text()).get("authority_id") == supersedes_id]
    if not pred:
        raise SystemExit("the predecessor document is not in " + str(out) + ": " + supersedes_id)
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
# The format-creation scenarios of the current operation, EXCLUDING the primary (the
# primary run id is added separately as the primary entry and must not be repeated here;
# a repeated run id is refused). The twelve formats are covered by the primary plus
# these eleven.
FORMAT_SCENARIOS = (
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


def collect_scenarios(primary_id, primary_path, extra_scenarios, package_file):
    """Collect the scenario digests of one admission, refusing a repeated run id.

    Every entry keeps its ORIGIN (primary / extra / package). A run id that appears
    twice - in any combination of the three sources - is refused before the dict is
    built, so a collision can never silently replace one digest with another. A package
    entry whose declared digest does not match the file bytes is refused.

    Returns {run_id: sha256}. Raises SystemExit on any refusal.
    """
    entries = []          # (run_id, origin, sha256)
    seen = {}             # run_id -> origin

    def add(run_id, origin, sha):
        if not isinstance(run_id, str) or not run_id:
            raise SystemExit("scenario run id is empty or not a string")
        if run_id in seen:
            raise SystemExit(
                "the run id " + run_id + " is repeated: first as " + seen[run_id]
                + ", again as " + origin + "; a repeated run id is refused")
        seen[run_id] = origin
        entries.append((run_id, origin, sha))

    if not primary_id or not primary_path:
        raise SystemExit("the primary scenario id and path are required")
    primary = json.loads(Path(primary_path).read_text())
    add(primary_id, "primary", digest(encoded(primary)))

    for extra_id, extra_path in extra_scenarios:
        extra = json.loads(Path(extra_path).read_text())
        add(extra_id, "extra", digest(encoded(extra)))

    if package_file and Path(package_file).is_file():
        # The package is raw JSON: a repeated run id must be detected on the PAIRS of
        # the raw document, before any dict is built. json.loads() would silently keep
        # only the last value of a repeated key, so the duplicate would reach add()
        # only once and the refusal would never fire. The object_pairs_hook keeps every
        # pair in order, so a repeated key is fed to add() twice and is refused.
        raw_pairs = json.loads(Path(package_file).read_text(),
                               object_pairs_hook=lambda pairs: pairs)
        if not isinstance(raw_pairs, list):
            raise SystemExit("package must be a JSON object of run id -> sha256")
        # detect a repeated key BEFORE any digest check, so the refusal reason names
        # the repetition and cannot be masked by a digest mismatch on one of the pairs
        pkg_keys = {}
        for pkg_id, _pkg_sha in raw_pairs:
            if pkg_id in pkg_keys:
                raise SystemExit(
                    "the run id " + pkg_id + " is repeated INSIDE the package "
                    "(raw JSON object keys: " + str([k for k, _ in raw_pairs]) + "); "
                    "a repeated run id is refused")
            pkg_keys[pkg_id] = True
        for pkg_id, pkg_sha in raw_pairs:
            pkg_path = Path(primary_path).parent / (pkg_id + ".json")
            if not pkg_path.is_file():
                raise SystemExit("package scenario file is absent: " + str(pkg_path))
            pkg = json.loads(pkg_path.read_text())
            actual = digest(encoded(pkg))
            if actual != pkg_sha:
                raise SystemExit("package scenario digest changed: " + pkg_id)
            add(pkg_id, "package", actual)

    return {run_id: sha for run_id, _origin, sha in entries}


def validate_scope(scope, scenarios):
    """Refuse a scope that does not describe the operation the scenarios cover."""
    text = " ".join(str(scope).lower().split())
    if "activation check" in text and len(scenarios) > 1:
        raise SystemExit("the scope names a single activation smoke but the admission "
                         "covers %d scenarios; the scope must describe the operation"
                         % len(scenarios))
    claims_product = "product acceptance" in text and not (
        "not a product acceptance" in text or "not a b00, fmt or product acceptance" in text)
    claims_b00 = "b00 acceptance" in text and not (
        "not a b00 acceptance" in text or "not a b00, fmt or product acceptance" in text)
    if claims_product:
        raise SystemExit("the scope claims a product acceptance")
    if claims_b00:
        raise SystemExit("the scope claims a B00 acceptance")
    covered_formats = [name for name in scenarios if name.startswith("fmt-")]
    if covered_formats and "format-creation" not in text and "format creation" not in text:
        raise SystemExit("the scope does not mention the format-creation scenarios it covers")


def main():
    # The identity of THIS admission is derived from the actually released documents:
    # the predecessor is the highest released R number, and the new identity is the next
    # free one. A self-superseding identity is refused.
    auth_id, auth_file, supersedes_id = derive_identity(OUT_DIR)
    validate_identity(auth_id, supersedes_id, OUT_DIR)

    # Collect the scenarios with duplicate detection BEFORE the dict is built. The
    # primary is one of the entries; the collect step refuses a repeated run id, so a
    # collision between primary, extra and package can never silently replace one
    # digest with another. The primary run id is therefore NOT listed again among the
    # extra scenarios.
    scenarios = collect_scenarios(RUN_ID, SCENARIO, EXTRA_SCENARIOS, PACKAGE_FILE)
    scenario_sha = scenarios[RUN_ID]

    # The scope must describe THIS operation.
    validate_scope(SCOPE, scenarios)

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
        "authority_id": auth_id,
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
        "run_scenarios": dict(scenarios),
        "same_canonical_local_run": False,
        "schema": "frw.Root.ordinary-independent-history-admission.v1",
        "scope": SCOPE,
        "supersedes": {
            "authority_id": supersedes_id,
            "reason": SUPERSEDES_REASON,
        },
        "unknown_effects_resolved": False,
    }
    raw = encoded(document)
    target = OUT_DIR / auth_file
    # Publish the COMPLETE document atomically. The bytes are first written in full to
    # a uniquely named temporary file in the same directory, fsynced and closed, and
    # only then hard-linked to the final name. os.link() fails with FileExistsError if
    # the name is already taken, so two competing releases can never both publish the
    # same number and the second can never overwrite the first. The final pathname is
    # never visible to readers as a partially written JSON, because it only appears
    # after the bytes are complete. A plain exists() + write_bytes() pair has a race,
    # and a plain replace() would overwrite an already published admission - neither is
    # acceptable here.
    tmp = OUT_DIR / (auth_file + ".tmp-" + str(os.getpid()))
    fd = os.open(str(tmp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.link(str(tmp), str(target))
    except FileExistsError:
        tmp.unlink()
        # a released admission is never rewritten: it would break the pin of the tester
        # snapshot that names it
        raise SystemExit("the admission " + str(target) + " already exists and is pinned; "
                         "release the next one instead")
    except OSError:
        tmp.unlink()
        raise
    tmp.unlink()
    if oct(target.stat().st_mode & 0o777) != "0o600":
        os.chmod(target, 0o600)
    print(json.dumps({
        "path": str(target), "bytes": len(raw), "sha256": digest(raw),
        "authority_id": auth_id, "supersedes_authority_id": supersedes_id,
        "run_id": RUN_ID, "scenario_sha256": scenario_sha,
        "scenario_count": len(scenarios),
        "history_rows": len(history), "gateway_pid": pid, "gateway_start_time": start_time,
        "history_row_ids": sorted(history),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
