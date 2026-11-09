#!/usr/bin/env python3
"""Prove the LATE rollback of the V3 publication on an isolated bench.

The earlier gap check proved that the rollback restores the state, but its injected
failure fired at the FIRST publication, before the marker and the stamp were touched,
and its success condition compared only the state before the operation with the state
after the restoration. That comparison does not prove that the metadata was changed and
restored.

This check proves the late point on the bytes:

  * the injection fires at a LATE target - the install stamp, which is published AFTER
    the marker - and the transaction records the home's state at that exact moment;
  * for every file whose restoration is claimed, the bytes at the injection point really
    DIFFER from the bytes before the operation;
  * reaching the failure point is proven by the recorded snapshot itself;
  * after the rollback every watched file has its previous bytes AND its previous mode,
    and a file that did not exist before the operation is gone;
  * the historical predecessor's record is unchanged.

A file that already matched the candidate before the operation is NOT counted as proof of
a restored change; the check reports it separately.

The serving home is never touched.
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
HOME = REPO / ".runtime/friday-normal-both-workers-frw032"
CAND = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108")
BENCH = Path("/home/jericho/.dsh/tmp/v3-late-bench")
SNAPSHOT = Path("/home/jericho/.dsh/tmp/v3-late-snapshot")
PRE = Path("/home/jericho/.cache/pre-install-5files-1794085924")
VENV = (REPO / ".runtime/friday-184-20261108/installs/be596ce02c5f6cde/environments/"
        "ffe0d97db6f3453eac3437e83399c554/venv/bin/python")
TOUCHED = ("agent/agent_init.py", "agent/bounded_context.py", "agent/context_compressor.py",
           "agent/conversation_compression.py", "tools/file_tools.py")
WATCHED = ("hermes-agent.source.json", "FRIDAY-INSTALL.json", "hermes-agent/install-stamp.json",
           "plugins/friday_rework/host_runtime.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state(path):
    path = Path(path)
    if not path.exists():
        return None
    info = path.lstat()
    return {"sha256": sha(path), "mode": stat.S_IMODE(info.st_mode), "bytes": info.st_size}


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def build_bench():
    subprocess.run([sys.executable, str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
                                       "build-v3-bench.py"), "--bench", str(BENCH)],
                   capture_output=True, check=True)
    for name in TOUCHED:
        shutil.copy2(PRE / name, BENCH / "hermes-agent" / name)
    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    for name in TOUCHED:
        data = (BENCH / "hermes-agent" / name).read_bytes()
        receipt["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(),
                                  "bytes": len(data), "mode": "100644"}
    (BENCH / "hermes-agent.source.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    marker["source_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    marker["ordinary_gateway"]["source_receipt_sha256"] = marker["source_receipt_sha256"]
    (BENCH / "FRIDAY-INSTALL.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n")
    for name in ("plugins/friday_rework/host_runtime.py", "plugins/friday_rework/a0_bootstrap.py",
                 "plugins/friday_rework/adapters/a0_web.py"):
        (BENCH / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HOME / name, BENCH / name)
    (BENCH / "preparation").mkdir(parents=True, exist_ok=True)
    (BENCH / "preparation/bench-unit.name").write_text("hermes-gateway-bench-nonexistent.service\n")
    predecessor = BENCH / "preparation" / "bench-predecessor"
    predecessor.mkdir(parents=True, exist_ok=True)
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    (predecessor / "request.json").write_text(json.dumps({
        "schema": "frw.root.engineering152-successor-request.v1",
        "home": str(BENCH),
        "current_input": request["current_input"],
    }, sort_keys=True, indent=2) + "\n")
    return predecessor


def main():
    if SNAPSHOT.exists():
        shutil.rmtree(SNAPSHOT)
    predecessor = build_bench()
    committed = (json.dumps({
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
        "gateway_started": False, "workers_enabled": False,
    }, sort_keys=True, indent=2) + "\n").encode()
    (predecessor / "committed.json").write_bytes(committed)

    before = {name: state(BENCH / name) for name in WATCHED}
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    raw = json.loads(json.dumps(request))
    raw["home"] = str(BENCH)
    raw["bench_home"] = str(BENCH)
    raw["project_file_updates"] = sorted(set(
        list(request.get("project_file_updates") or [])
        + ["plugins/friday_rework/host_runtime.py"]))
    raw["inject_after_rename"] = True
    raw["inject_target"] = str(BENCH / "hermes-agent/install-stamp.json")
    raw["inject_snapshot_dir"] = str(SNAPSHOT)
    # the files whose state is recorded at the injection point are named EXPLICITLY; the
    # scope of the read is not derived from the parents of the result directory
    raw["inject_snapshot_files"] = list(WATCHED)
    for key in ("marker", "source_receipt", "stamp", "configuration", "profile", "launcher"):
        path = Path(raw[key]["path"])
        relative = path.relative_to(HOME)
        raw[key] = {"path": str(BENCH / relative), "sha256": sha(BENCH / relative)}
    raw["target_receipt"] = {"path": str(BENCH / "hermes-agent.source.json"),
                             "sha256": sha(BENCH / "hermes-agent.source.json")}
    body = json.loads((predecessor / "request.json").read_text())
    body["current_input"] = {"path": raw["previous_input"]["path"],
                             "sha256": raw["previous_input"]["sha256"]}
    (predecessor / "request.json").write_text(json.dumps(body, sort_keys=True, indent=2) + "\n")
    raw["predecessor_request"] = {"path": str(predecessor / "request.json"),
                                  "sha256": sha(predecessor / "request.json")}
    raw["predecessor_current_input_sha256"] = raw["previous_input"]["sha256"]
    raw["predecessor_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    path = CAND / "REQUEST-LATE.json"
    path.write_bytes((json.dumps(raw, sort_keys=True, indent=2) + "\n").encode())
    os.chmod(path, 0o600)

    result = subprocess.run(
        [str(VENV), "-I", "-B", str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
             "friday_v3_layer_publication.py"), "--request", str(path),
         "--request-sha256", sha(path)],
        capture_output=True, text=True, timeout=900,
        env={**os.environ, "HERMES_HOME": str(BENCH)})
    outcome = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr[-300:]

    after = {name: state(BENCH / name) for name in WATCHED}
    snapshot_file = SNAPSHOT / "STATE-AT-INJECTION.json"
    reached = snapshot_file.exists()
    at_injection = {}
    if reached:
        at_injection = json.loads(snapshot_file.read_text())["files"]

    changed_at_the_point = {}
    unchanged_at_the_point = {}
    restored = {}
    for name in WATCHED:
        key = str(BENCH / name)
        point = at_injection.get(key)
        if point is None:
            continue
        before_entry = before[name]
        if before_entry is None:
            # the file did not exist before the operation: it must be gone after the rollback
            restored[name] = after[name] is None
            changed_at_the_point[name] = True
            continue
        differs = point["sha256"] != before_entry["sha256"]
        if differs:
            changed_at_the_point[name] = {"before_sha256": before_entry["sha256"][:12],
                                         "at_injection_sha256": point["sha256"][:12],
                                         "mode_at_injection": point["mode"]}
        else:
            unchanged_at_the_point[name] = "the file already matched the published bytes"
        restored[name] = (after[name] is not None
                          and after[name]["sha256"] == before_entry["sha256"]
                          and after[name]["mode"] == before_entry["mode"])
    predecessor_unchanged = (predecessor / "committed.json").read_bytes() == committed
    all_restored = all(restored.values()) if restored else False
    changed_count = len(changed_at_the_point)
    say(scenario="a one-shot failure at the LATE point: the install stamp, after the marker",
        outcome=outcome[:240],
        the_injection_point_was_reached=reached,
        files_proven_changed_at_the_point=changed_at_the_point,
        files_that_already_matched_the_candidate=unchanged_at_the_point,
        files_restored_with_bytes_and_mode=restored,
        every_claimed_restoration_holds=all_restored,
        predecessor_record_unchanged=predecessor_unchanged,
        ok=(reached and changed_count > 0 and all_restored and predecessor_unchanged))
    shutil.rmtree(BENCH, ignore_errors=True)
    shutil.rmtree(SNAPSHOT, ignore_errors=True)


if __name__ == "__main__":
    main()
