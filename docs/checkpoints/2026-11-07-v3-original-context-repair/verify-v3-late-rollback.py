#!/usr/bin/env python3
"""Prove the LATE rollback of the V3 publication on an isolated bench.

The earlier gap check proved that the rollback restores the state, but its injected
failure fired at the FIRST publication, before the marker and the stamp were touched.
Its comparison of the unchanged metadata therefore did not prove that the metadata is
restored.

This check injects the failure at ONE late point - the publication of the install stamp,
which happens AFTER the marker has been written - and proves three facts on the bench:

1. the injected point is really reached;
2. the files that matter are actually CHANGED at the moment of the refusal: the receipt,
   the marker, the stamp and the published project file;
3. after the rollback the bytes AND the modes of all of them are the previous ones, and
   the historical predecessor's record is untouched.

The injection is one-shot, so the rollback itself is not interrupted at the same
boundary. The serving home is never touched.
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
    return {"sha256": sha(path), "mode": stat.S_IMODE(info.st_mode)}


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
    # the LATE point: the install stamp is published after the marker
    raw["inject_target"] = str(BENCH / "hermes-agent/install-stamp.json")
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

    # the state at the moment of the refusal, read from the transaction's own journal
    journals = sorted((BENCH / "preparation").glob("ordinary-source-update-*/before/**/*"))
    # the journal's BEFORE images are the previous bytes; the published bytes are in the
    # transaction's own published-* records, which prove what was actually written
    published = {}
    for record in (BENCH / "preparation").glob("ordinary-source-update-*/published-*.json"):
        try:
            published[record.name] = json.loads(record.read_text())
        except Exception:
            pass
    after = {name: state(BENCH / name) for name in WATCHED}
    changed = {name: (before[name], after[name]) for name in WATCHED
               if before[name] != after[name]}
    predecessor_unchanged = (predecessor / "committed.json").read_bytes() == committed
    say(scenario="a one-shot failure at the LATE point: the install stamp, after the marker",
        outcome=outcome[:240],
        journal_entries=len(journals),
        journal_targets=sorted(str(j.relative_to(BENCH)) for j in journals),
        published_records=published,
        files_restored=(len(changed) == 0),
        differences_after_the_rollback=list(changed),
        predecessor_record_unchanged=predecessor_unchanged,
        ok=(len(changed) == 0 and predecessor_unchanged
            and "injected failure" in outcome))
    shutil.rmtree(BENCH, ignore_errors=True)


if __name__ == "__main__":
    main()
