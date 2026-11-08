#!/usr/bin/env python3
"""Prepare the owner area's workers through the product's own writer.

The owner profile (dest_telegram) has a clean workers tree, so prepare_workers can
run for it. The shared A0 half may still fail later in qualify(), but preparation
itself is a product operation and is worth doing now: it records the DSH and A0
preparations with the current generation and binding.

Nothing is printed except non-secret results.
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
CREDS = Path("/home/jericho/jericho/frw_admin.txt")
PLATFORM = "telegram"
TRANSPORT = "default"
ACCOUNT = "8751854128"
OWNER_USER = "467035772"
OWNER_PROFILE = "dest_telegram"

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


def operator_session():
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    from hermes_cli.dashboard_auth.registry import get_provider
    provider = get_provider("basic")
    if provider is None:
        raise SystemExit("dashboard basic provider is not registered")
    raw = CREDS.read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    session = provider.complete_password_login(username=username, password=password)
    if provider.verify_session(access_token=session.access_token) is None:
        raise SystemExit("operator session failed provider verification")
    return session


def main():
    import importlib
    session = operator_session()
    admin_mod = importlib.import_module("friday_rework.admin")
    onb_mod = importlib.import_module("friday_rework.onboarding")
    admin = admin_mod.Administration()
    onboarding = onb_mod.Onboarding(admin)

    plan = onboarding.templates(TRANSPORT, session=session)
    digest = plan["config_sha256"]
    result = onboarding.prepare_workers(
        TRANSPORT, session=session, expected_config_sha256=digest, generation=1,
        platform=PLATFORM, transport_profile=TRANSPORT, account_id=ACCOUNT,
        user_id=OWNER_USER)
    say(stage="prepare_workers", state=result.get("state"), enabled=result.get("enabled"),
        required_workers=result.get("required_workers"),
        required_names=result.get("required_names"),
        can_prepare_workers=result.get("can_prepare_workers"),
        can_qualify_workers=result.get("can_qualify_workers"),
        can_activate=result.get("can_activate"),
        worker_execution=result.get("worker_execution"),
        workers={k: v["state"] for k, v in (result.get("workers") or {}).items()})
    clean()


if __name__ == "__main__":
    main()
