#!/usr/bin/env python3
"""Retire the retained A0 container through the PRODUCT's own pinned runtime.

Why this exists: the installed A0 runtime stops the rootless docker daemon BEFORE it
retires the container, so `retire_initial_probe()` loses its `docker rm` ACK and the
container record survives. A surviving record blocks every later route preparation
(`docker ps -aq` must be empty).

This script performs the product's own retirement, in the only order that can succeed:
  1. start the dedicated rootless docker unit (it is the product's own unit)
  2. load the PINNED A0 runtime module for the exact recorded plan
  3. call Runtime(plan, stopping=True).retire_initial_probe()
       -> the product verifies ownership, STOP_CONFIRMED, cessation of all observations,
          and then removes the container and writes its own retirement receipt
  4. verify the container table is empty and the receipt exists

Nothing is edited by hand: no docker state file is touched, no receipt is written by
this script. The daemon unit has RuntimeMaxSec=120s, so the steps run immediately.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
RUNTIME = Path("/home/jericho/jericho/Friday_rework/.runtime")
SOL = RUNTIME / "a0-runtime-sol"
PLAN = HOME / "profiles/telegram-bot-8812646969/workers/a0/probe-plan.json"
PREP = HOME / "profiles/telegram-bot-8812646969/workers/a0/runtime-input.json"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def clean():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        import shutil
        shutil.rmtree(cache, ignore_errors=True)


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    host_runtime = importlib.import_module("friday_rework.host_runtime")

    plan = json.loads(PLAN.read_text())
    prep = json.loads(PREP.read_text())
    identity = plan["identity"]
    sol = SOL / identity
    say(stage="inputs", identity=identity, sol=str(sol),
        receipt_files=sorted(p.name for p in sol.iterdir()) if sol.is_dir() else None,
        plan_assignment=plan["assignment"][:28])

    # 1. the product's own daemon unit
    subprocess.run(["systemctl", "--user", "start", "friday-rework-docker.service"], check=True)
    deadline = time.time() + 45
    socket = Path("/run/user/1000/friday-rework-docker/docker.sock")
    while time.time() < deadline and not socket.exists():
        time.sleep(0.5)
    if not socket.exists():
        raise SystemExit("rootless docker socket did not appear")
    say(stage="daemon", active=subprocess.run(
        ["systemctl", "--user", "is-active", "friday-rework-docker.service"],
        capture_output=True, text=True).stdout.strip())

    m = host_runtime.a0_runtime_module(prep["runtime"])
    rt = m.Runtime(plan, stopping=True)
    receipt = rt.receipt()
    say(stage="runtime", container_id=receipt["container_id"],
        invocation_id=receipt.get("invocation_id"),
        observations=len(receipt.get("observations") or []))

    # 2. the product's own retirement
    result = rt.retire_initial_probe()
    say(stage="retirement", result=result)

    # 3. verify
    listing = m.Runtime._command([str(m.DOCKER), "--host", m.SOCKET, "ps", "-aq"], 5).strip()
    say(stage="verify", container_table_empty=not listing, remaining=listing[:120],
        retirement_receipt=str(sol / "retirement.json"),
        retirement_receipt_present=(sol / "retirement.json").is_file())
    clean()


if __name__ == "__main__":
    main()
