#!/usr/bin/env python3
"""Build the isolated bench for a plugin publication and its request, in one pass.

The bench mirrors the serving home except for the five source files the V3 layers touch,
which carry the preimage bytes, so that the layers can be applied again on it. The receipt,
the marker, the predecessor record and the request are written from the same state, so the
bench and its request never disagree.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
HOME = REPO / ".runtime/friday-normal-both-workers-frw032"
CAND = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108")
BENCH = Path("/home/jericho/.dsh/tmp/v3-bench")
PRE = Path("/home/jericho/.cache/pre-install-5files-1794085924")
TOUCHED = ("agent/agent_init.py", "agent/bounded_context.py", "agent/context_compressor.py",
           "agent/conversation_compression.py", "tools/file_tools.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    subprocess.run([sys.executable, str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
                                       "build-v3-bench.py"), "--bench", str(BENCH)],
                   capture_output=True, check=True)
    # the five files carry the preimage bytes, the rest of the tree is the home's
    for name in TOUCHED:
        shutil.copy2(PRE / name, BENCH / "hermes-agent" / name)
    # the bench's receipt and marker are the home's, with the preimage pins of the five files
    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    for name in TOUCHED:
        data = (BENCH / "hermes-agent" / name).read_bytes()
        receipt["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(),
                                  "bytes": len(data), "mode": "100644"}
    (BENCH / "hermes-agent.source.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    marker["source_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    marker["ordinary_gateway"]["source_receipt_sha256"] = marker["source_receipt_sha256"]
    (BENCH / "FRIDAY-INSTALL.json").write_text(
        json.dumps(marker, sort_keys=True, indent=2) + "\n")
    # the bench's plugin tree mirrors the home's
    for name in ("plugins/friday_rework/host_runtime.py", "plugins/friday_rework/a0_bootstrap.py"):
        (BENCH / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HOME / name, BENCH / name)
    # the bench's own unit name: a unit that does not exist, so the bench run is not
    # refused by the live gateway's activity
    (BENCH / "preparation").mkdir(parents=True, exist_ok=True)
    (BENCH / "preparation/bench-unit.name").write_text(
        "hermes-gateway-bench-nonexistent.service\n")
    # the request
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    request["home"] = str(BENCH)
    request["bench_home"] = str(BENCH)
    for key in ("marker", "source_receipt", "stamp", "configuration", "profile", "launcher"):
        path = Path(request[key]["path"])
        relative = path.relative_to(HOME)
        request[key] = {"path": str(BENCH / relative), "sha256": sha(BENCH / relative)}
    request["target_receipt"] = {"path": str(BENCH / "hermes-agent.source.json"),
                                 "sha256": sha(BENCH / "hermes-agent.source.json")}
    # the predecessor record of the bench names the bench's own previous input
    predecessor = HOME / "preparation" / (
        "ordinary-source-update-successor-" +
        json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
        ["ordinary_source_update_request"]["sha256"])
    bench_predecessor = BENCH / "preparation" / predecessor.name
    bench_predecessor.mkdir(parents=True, exist_ok=True)
    body = json.loads((predecessor / "request.json").read_text())
    body["home"] = str(BENCH)
    body["current_input"] = {"path": request["previous_input"]["path"],
                              "sha256": request["previous_input"]["sha256"]}
    (bench_predecessor / "request.json").write_text(
        json.dumps(body, sort_keys=True, indent=2) + "\n")
    (bench_predecessor / "committed.json").write_text(json.dumps({
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED", "gateway_started": False,
        "workers_enabled": False,
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
    }, sort_keys=True, indent=2) + "\n")
    request["predecessor_request"] = {"path": str(bench_predecessor / "request.json"),
                                      "sha256": sha(bench_predecessor / "request.json")}
    request["predecessor_current_input_sha256"] = request["previous_input"]["sha256"]
    request["predecessor_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    raw = (json.dumps(request, sort_keys=True, indent=2) + "\n").encode()
    out = CAND / "REQUEST-BENCH2.json"
    out.write_bytes(raw)
    os.chmod(out, 0o600)
    print(json.dumps({"bench": str(BENCH), "request": str(out),
                      "request_sha256": hashlib.sha256(raw).hexdigest(),
                      "plugin_set": request["plugin_set"]}, sort_keys=True))


if __name__ == "__main__":
    main()
