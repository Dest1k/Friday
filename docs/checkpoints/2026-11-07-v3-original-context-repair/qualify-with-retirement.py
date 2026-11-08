#!/usr/bin/env python3
"""Run one A0 qualification attempt and retire the container it leaves behind.

Order that the installed A0 runtime cannot do by itself:
  1. the product starts the rootless docker unit and creates/observes/stops the
     container (its own native path)
  2. the product's own retirement needs the daemon still alive, so it is performed
     right after the attempt, through the PINNED runtime and the recorded plan

If the attempt already recorded a retirement receipt, nothing is retired twice.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
PROFILE = os.environ.get("FRW_PROFILE", "dest_telegram")
USER_ID = os.environ.get("FRW_USER_ID", "467035772")
ACCOUNT = "8751854128"
TRANSPORT = "default"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def clean():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def daemon_up(timeout=45):
    subprocess.run(["systemctl", "--user", "start", "friday-rework-docker.service"], check=True)
    socket = Path("/run/user/1000/friday-rework-docker/docker.sock")
    end = time.time() + timeout
    while time.time() < end and not socket.exists():
        time.sleep(0.5)
    return socket.exists()


def retire_if_needed(home):
    """Retire the container of the recorded attempt, through the pinned runtime."""
    import importlib
    host_runtime = importlib.import_module("friday_rework.host_runtime")
    plan_path = home / "workers/a0/probe-plan.json"
    state_path = home / "workers/a0/bootstrap/state.json"
    if not plan_path.is_file() or not state_path.is_file():
        say(stage="retire", skipped="no recorded plan/bootstrap for this attempt")
        return None
    state = json.loads(state_path.read_text())
    created = state.get("created") or {}
    container = created.get("container_id")
    if not container:
        say(stage="retire", skipped="no container was created in this attempt")
        return None
    sol = Path("/home/jericho/jericho/Friday_rework/.runtime/a0-runtime-sol")
    identity = json.loads(plan_path.read_text())["identity"]
    receipt = sol / identity / "retirement.json"
    if receipt.is_file():
        say(stage="retire", skipped="retirement receipt already present",
            receipt=str(receipt))
        return json.loads(receipt.read_text())
    prep = json.loads((home / "workers/a0/runtime-input.json").read_text())
    if not daemon_up():
        say(stage="retire", error="rootless docker socket did not appear")
        return None
    m = host_runtime.a0_runtime_module(prep["runtime"])
    plan = json.loads(plan_path.read_text())
    rt = m.Runtime(plan, stopping=True)
    try:
        result = rt.retire_initial_probe()
    except Exception as exc:
        say(stage="retire", error_type=type(exc).__name__, error=str(exc)[:200])
        return None
    say(stage="retire", result=result)
    return result


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    import re
    from hermes_cli.dashboard_auth.registry import get_provider

    home = HOME / "profiles" / PROFILE
    raw = Path("/home/jericho/jericho/frw_admin.txt").read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    provider = get_provider("basic")
    session = provider.complete_password_login(username=username, password=password)

    admin_mod = importlib.import_module("friday_rework.admin")
    onb_mod = importlib.import_module("friday_rework.onboarding")
    admin = admin_mod.Administration()
    onboarding = onb_mod.Onboarding(admin)
    plan = onboarding.templates(TRANSPORT, session=session)
    say(stage="operator_session", user_id=session.user_id, provider=session.provider,
        config_sha256=plan["config_sha256"], profile=PROFILE)

    try:
        result = onboarding.qualify_workers(
            TRANSPORT, session=session, expected_config_sha256=plan["config_sha256"],
            generation=1, platform="telegram", transport_profile=TRANSPORT,
            account_id=ACCOUNT, user_id=USER_ID)
        say(stage="qualify", state=result.get("state"), enabled=result.get("enabled"),
            worker_execution=result.get("worker_execution"),
            can_activate=result.get("can_activate"),
            workers={k: v["state"] for k, v in (result.get("workers") or {}).items()})
    except Exception as exc:
        say(stage="qualify_refused", error_type=type(exc).__name__, error=str(exc)[:300])
    retire_if_needed(home)
    clean()


if __name__ == "__main__":
    main()
