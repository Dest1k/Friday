#!/usr/bin/env python3
"""Activate the two ordinary user areas through the product's own activation path.

Onboarding.activate() verifies the operator session, the prepared proof, the scoped
keys, the onboarding home and the native grant, then publishes the scope marker and
enables the access row. Nothing is written by hand.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
CREDS = Path("/home/jericho/jericho/frw_admin.txt")
ACCOUNT = "8751854128"
TRANSPORT = "default"
AREAS = [("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram")]

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def clean():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    from hermes_cli.dashboard_auth.registry import get_provider
    raw = Path(CREDS).read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    provider = get_provider("basic")
    session = provider.complete_password_login(username=username, password=password)

    admin_mod = importlib.import_module("friday_rework.admin")
    onb_mod = importlib.import_module("friday_rework.onboarding")
    admin = admin_mod.Administration()
    onboarding = onb_mod.Onboarding(admin)

    for user_id, profile in AREAS:
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        try:
            result = onboarding.activate(
                TRANSPORT, session=session, expected_config_sha256=digest, generation=1,
                platform="telegram", transport_profile=TRANSPORT, account_id=ACCOUNT,
                user_id=user_id)
            say(stage="activate", user_id=user_id, profile=profile,
                state=result.get("state"), enabled=result.get("enabled"),
                worker_execution=result.get("worker_execution"),
                can_activate=result.get("can_activate"))
        except Exception as exc:
            say(stage="activate_refused", user_id=user_id, profile=profile,
                error_type=type(exc).__name__, error=str(exc)[:300])
    clean()


if __name__ == "__main__":
    main()
