#!/usr/bin/env python3
"""Read-only probe: can the DSH worker of the prepared Jarvis profile be observed?

DSH needs no A0 container: dsh_observe() runs the installed adapter's own
foreground boundary (node + CLI smoke, web network probe) under a bounded systemd
scope. This script only inspects whether the DSH preconditions and pins are
present and current. It starts nothing and writes nothing.

The A0 half is separate and needs its own native container; this probe says
nothing about it.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
PROFILE = "telegram-bot-8812646969"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def main():
    from hermes_cli import friday_user_scope as scope
    import importlib
    host_runtime = importlib.import_module("friday_rework.host_runtime")

    home = HOME / "profiles" / PROFILE
    prepared = json.loads((home / "workers/dsh/runtime-input.json").read_text())
    runtime = prepared["runtime"]
    kind = "a0" if "a0" in runtime else "dsh"

    result = {"kind": kind, "profile": PROFILE}
    try:
        validated = host_runtime.validate_runtime(runtime)
        result["validate_runtime"] = "ok"
    except Exception as exc:
        result["validate_runtime"] = f"{type(exc).__name__}: {exc}"
        say(**result)
        return

    dsh = validated["dsh"]
    pins = {}
    for name in ("node", "cli", "patch"):
        path = Path(dsh[name]["path"])
        ok = path.is_file()
        pins[name] = {"path": str(path), "exists": ok,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if ok else None,
                      "expected": dsh[name].get("sha256")}
    for ref in dsh.get("native_files", []):
        path = Path(ref["path"])
        pins[f"native:{path.name}"] = {"path": str(path), "exists": path.is_file()}
    web = host_runtime._dsh_web(dsh)
    result["web_profile"] = web.profile if web else None
    result["web_pins"] = {
        "resolver": str(web.resolver.path), "trust_bundle": str(web.trust_bundle.path),
        "egress_evidence": str(web.egress_evidence.path),
        "research_policy": str(web.research_policy.path),
        "egress_sha256": web.egress_evidence.sha256,
    }
    result["pins"] = pins
    result["pin_mismatches"] = [n for n, row in pins.items()
                                if row.get("expected") and row.get("sha256")
                                and row["sha256"] != row["expected"]]
    result["workspace_root"] = validated["workspace_root"]
    result["staging_root"] = validated["staging_root"]
    result["cache_roots"] = validated["cache_roots"]
    result["runtime_receipt_present"] = Path(validated["runtime_receipt"]["path"]).is_file()
    result["workers_qualification_present"] = (home / "workers/qualification").exists()
    result["a0_bootstrap_present"] = (home / "workers/a0/bootstrap").exists()
    result["probe_plan_present"] = (home / "workers/a0/probe-plan.json").exists()
    result["scope_marker_present"] = (home / scope.MARKER).exists()
    result["conclusion"] = ("DSH observation preconditions are present and current; a fresh A0 "
                             "container is still required for the other half, and the product blocks "
                             "a repeated qualification while the previous attempt is on disk")
    say(**result)


if __name__ == "__main__":
    main()
