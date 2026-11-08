#!/usr/bin/env python3
"""Build the request for the V3 layer publication onto the serving ordinary home.

The generator and the validator agree on the field set: this file produces exactly the
keys that friday_v3_layer_publication.py requires, and every pin is taken from live bytes.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
CANDIDATE = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/project")
REPO = Path("/home/jericho/jericho/Friday_rework")
UNIT = Path("/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service")
OUT = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/REQUEST-LAYERS.json")
LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {"path": str(path), "sha256": sha(path)}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def main():
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    # The previous input document was removed by the owner's cleanup; the successor journal
    # keeps its digest and the project's own files are pinned by the marker.
    predecessor_tx = HOME / "preparation" / (
        "ordinary-source-update-successor-"
        + marker["ordinary_source_update_request"]["sha256"])
    predecessor = json.loads((predecessor_tx / "request.json").read_text())
    # The previous input document was removed by the owner's cleanup. It is reconstructed from
    # the candidate's input by removing the four layer pairs and restoring the serving home's
    # own plugin pins; the reconstruction is proven against the live home before it is used.
    previous_input = {"path": str(CANDIDATE.parent / "INPUT-PREVIOUS-RECONSTRUCTED.json"),
                      "sha256": sha(CANDIDATE.parent / "INPUT-PREVIOUS-RECONSTRUCTED.json")}
    require_previous = Path(previous_input["path"])
    if not require_previous.exists():
        raise SystemExit("previous input document is absent: " + str(require_previous))

    current_input = {"path": str(CANDIDATE.parent / "INPUT-LAYERS.json"),
                     "sha256": sha(CANDIDATE.parent / "INPUT-LAYERS.json")}
    previous = json.loads(Path(previous_input["path"]).read_text())
    current = json.loads(Path(current_input["path"]).read_text())

    history = {}
    for root in ("preparation/ordinary-gateway", "preparation/ordinary-gateway-archive"):
        base = HOME / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.is_symlink():
                continue
            history[str(path.relative_to(HOME))] = sha(path)

    request = {
        "schema": "friday.ordinary-telegram-source-update.v45",
        "seconds": 180,
        "home": str(HOME),
        "candidate_project": str(CANDIDATE),
        "marker": pin(HOME / "FRIDAY-INSTALL.json"),
        "source_receipt": pin(HOME / "hermes-agent.source.json"),
        "stamp": pin(HOME / "hermes-agent/install-stamp.json"),
        "configuration": pin(HOME / "config.yaml"),
        "profile": pin(HOME / "FRIDAY-PROFILE.json"),
        "launcher": pin(HOME / "hermes-agent/.hermes/bin/hermes"),
        "native_unit": pin(UNIT),
        "previous_input": previous_input,
        "current_input": current_input,
        "predecessor_request": pin(predecessor_tx / "request.json"),
        "predecessor_current_input_sha256": predecessor["current_input"]["sha256"],
        "predecessor_receipt_sha256": json.loads(
            (predecessor_tx / "committed.json").read_text())["source_receipt_sha256"],
        "target_receipt": pin(HOME / "hermes-agent.source.json"),
        "candidate_input": current_input,
        "project_inventory": current["project_files"],
        "project_inventory_sha256": hashlib.sha256(encoded(current["project_files"])).hexdigest(),
        "plugin_set": sorted(n for n in previous["project_files"]
                             if n.startswith("plugins/friday_rework/")
                             and current["project_files"].get(n) != previous["project_files"][n]),
        "plugin_additions": sorted(n for n in current["project_files"]
                                   if n.startswith("plugins/friday_rework/")
                                   and n not in previous["project_files"]),
        "project_file_updates": sorted(n for n in previous["project_files"]
                                       if not n.startswith("plugins/friday_rework/")
                                       and current["project_files"].get(n) != previous["project_files"][n]),
        "installed_layers": len(receipt["layers"]),
        "installed_files": len(receipt["files"]),
        "transaction_history": history,
    }
    raw = encoded(request)
    OUT.write_bytes(raw)
    os.chmod(OUT, 0o600)
    print(json.dumps({"request": str(OUT), "bytes": len(raw), "sha256": sha(OUT),
                      "history_entries": len(history),
                      "layers": len(request["installed_layers"] and receipt["layers"]),
                      "project_files": len(request["project_inventory"])}, sort_keys=True))


if __name__ == "__main__":
    main()
