#!/usr/bin/env python3
"""Build the V3 publication request for the serving ordinary home.

Every pin is taken from the live home or from the frozen candidate; nothing is
copied from an older authority without re-reading the bytes.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
CAND = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108")
REPO = Path("/home/jericho/jericho/Friday_rework")
CKPT = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair"
PREV_INPUT = Path("/home/jericho/.cache/FRW-SOURCE156-FINALIZATION-REPAIR-20261104-R1/assembly-final-r2/FINAL-INPUT-SOURCE-CANDIDATE.json")
PREDECESSOR = HOME / "preparation/ordinary-source-update-successor-afb9863d58ee319d96e00e313a8cc495c6cb883f75430e7adcbb24c80ef5de00/request.json"
UNIT = Path("/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service")
OUT = CAND / "REQUEST-V3.json"


def pin(path):
    path = Path(path)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    current_input = CAND / "INPUT-V3.json"
    history = json.loads((CKPT / "serving-home-transaction-history.json").read_text())
    request = {
        "schema": "friday.ordinary-telegram-source-update.v45",
        "seconds": 180,
        "home": str(HOME),
        "previous_input": pin(PREV_INPUT),
        "current_input": pin(current_input),
        "marker": pin(HOME / "FRIDAY-INSTALL.json"),
        "source_receipt": pin(HOME / "hermes-agent.source.json"),
        "stamp": pin(HOME / "hermes-agent/install-stamp.json"),
        "configuration": pin(HOME / "config.yaml"),
        "profile": pin(HOME / "FRIDAY-PROFILE.json"),
        "launcher": pin(HOME / "hermes-agent/.hermes/bin/hermes"),
        "credential_files": {
            ".env": pin(HOME / ".env"),
            "auth.json": None if not (HOME / "auth.json").exists() else pin(HOME / "auth.json"),
        },
        "native_unit": pin(UNIT),
        "predecessor_update": pin(PREDECESSOR),
        "transaction_history": history,
        "target_frozen": pin(CAND / "FROZEN-V3.json"),
    }
    raw = (json.dumps(request, sort_keys=True, indent=2) + "\n").encode()
    OUT.write_bytes(raw)
    os.chmod(OUT, 0o600)
    print(json.dumps({
        "request": str(OUT),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "history_entries": len(history),
        "previous_input": request["previous_input"]["sha256"],
        "current_input": request["current_input"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
