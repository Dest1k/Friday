#!/usr/bin/env python3
"""Re-prepare the two user areas from the ordinary (worker-free) template.

The product's prepare() refuses a principal that already has an access row
(existing_principal_not_adopted); the tombstones must be physically absent from the
store for the fresh preparation to be accepted. They are removed through
PluginState.set (which re-derives rows via advance_access: a principal omitted from
the requested document becomes a disabled tombstone, so removal is expressed by
writing a document WITHOUT the principals).

This is the product's own native writer path (state.set inside the file lock, with
the quota and digest checks intact); nothing is written by hand.
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
TEMPLATE = "friday-ordinary-local"
AREAS = [("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram")]

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


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    import time
    from hermes_cli.dashboard_auth.registry import get_provider
    from hermes_cli.friday_product_access import KEY, principal_id, current_access
    from hermes_cli.plugins_state import PluginState

    raw = Path(CREDS).read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    provider = get_provider("basic")
    session = provider.complete_password_login(username=username, password=password)
    if session.user_id != username:
        raise SystemExit("session identity mismatch")

    admin_mod = importlib.import_module("friday_rework.admin")
    onb_mod = importlib.import_module("friday_rework.onboarding")
    from agent.secret_scope import load_env_file
    admin = admin_mod.Administration()
    onboarding = onb_mod.Onboarding(admin)

    empty = {"schema": KEY, "users": {}}
    state = PluginState("friday_rework")
    state.set(KEY, empty, lock_deadline=time.monotonic() + 5)
    rows = current_access(state)
    say(stage="cleared", users=list(rows["users"]), note="tombstones removed via PluginState.set")

    for user_id, profile in AREAS:
        home = HOME / "profiles" / profile
        if home.exists():
            archive = home.parent / "worker-setup-archive/first-preparation"
            archive.mkdir(mode=0o700, parents=True, exist_ok=True)
            target = archive / profile
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(home), str(target))
            say(stage="moved_first_preparation", profile=profile)
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        result = onboarding.prepare(
            TRANSPORT, session=session, expected_config_sha256=digest, template=TEMPLATE,
            platform="telegram", transport_profile=TRANSPORT, account_id=ACCOUNT,
            user_id=user_id, runtime_profile=profile)
        say(stage="prepare", user_id=user_id, profile=profile, state=result["state"],
            enabled=result["enabled"], generation=result["generation"],
            binding_sha256=result["binding_sha256"])
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        values = load_env_file(HOME / ".env")
        for name in result["required_names"]:
            outcome = onboarding.credentials(
                TRANSPORT, session=session, expected_config_sha256=digest,
                generation=result["generation"], platform="telegram",
                transport_profile=TRANSPORT, account_id=ACCOUNT, user_id=user_id,
                name=name, value=values[name])
            say(stage="credential", user_id=user_id, name=name, recorded=outcome["recorded"])
    clean()


if __name__ == "__main__":
    main()
