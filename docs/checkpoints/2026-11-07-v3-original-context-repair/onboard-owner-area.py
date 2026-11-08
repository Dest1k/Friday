#!/usr/bin/env python3
"""Prepare the owner area (467035772 -> dest_telegram) through the product path.

Uses the same operator session and the same product writers as the Jarvis area:
Onboarding.prepare -> credentials. The worker step is deliberately NOT touched here:
the A0 half of the shared worker contract is blocked for the Jarvis profile and the
product's prepare/qualify gates are shared, so this script stops before workers.

Nothing is printed except non-secret results; secrets are read from the installed
home .env and written through Onboarding.credentials only.
"""
import hashlib
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
TEMPLATE = "friday-local"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def clean_cache():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def operator_session():
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean_cache()
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
    from hermes_cli.friday_product_access import admin_policy
    operator = admin_policy()["operators"][0]
    if (session.provider, session.user_id, session.org_id) != (
            operator["provider"], operator["user_id"], operator["org_id"]):
        raise SystemExit("session is not the configured product operator")
    return session


def main():
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id
    from friday_rework.admin import Administration
    from friday_rework.onboarding import Onboarding
    from agent.secret_scope import load_env_file

    session = operator_session()
    say(stage="operator_session", user_id=session.user_id, provider=session.provider)

    admin = Administration()
    onboarding = Onboarding(admin)
    plan = onboarding.templates(TRANSPORT, session=session)
    digest = plan["config_sha256"]

    key = principal_id(PLATFORM, TRANSPORT, ACCOUNT, OWNER_USER)
    home = HOME / "profiles" / OWNER_PROFILE
    say(stage="precheck", principal=key, config_sha256=digest,
        home_exists=home.exists(),
        policy_present=scope.policy(HOME) is not None,
        pending_profiles=[p["runtime_profile"] for p in plan["pending"]])

    if home.exists():
        say(stage="blocked", reason="profile home already exists; not adopting it",
            home=str(home))
        return

    result = onboarding.prepare(
        TRANSPORT, session=session, expected_config_sha256=digest, template=TEMPLATE,
        platform=PLATFORM, transport_profile=TRANSPORT, account_id=ACCOUNT,
        user_id=OWNER_USER, runtime_profile=OWNER_PROFILE)
    say(stage="prepare", state=result["state"], enabled=result["enabled"],
        generation=result["generation"], config_sha256=result["config_sha256"],
        target_config_sha256=result["target_config_sha256"],
        binding_sha256=result["binding_sha256"],
        required_names=result["required_names"], admission=result["admission"])

    plan = onboarding.templates(TRANSPORT, session=session)
    digest = plan["config_sha256"]
    values = load_env_file(HOME / ".env")
    missing = [n for n in result["required_names"] if not values.get(n)]
    if missing:
        raise SystemExit("installed home lacks required secrets: %d names" % len(missing))
    for name in result["required_names"]:
        outcome = onboarding.credentials(
            TRANSPORT, session=session, expected_config_sha256=digest,
            generation=result["generation"], platform=PLATFORM,
            transport_profile=TRANSPORT, account_id=ACCOUNT, user_id=OWNER_USER,
            name=name, value=values[name])
        say(stage="credential", name=name, state=outcome["state"], recorded=outcome["recorded"])

    plan = onboarding.templates(TRANSPORT, session=session)
    state = onboarding.workers_state(
        TRANSPORT, session=session, expected_config_sha256=plan["config_sha256"],
        generation=result["generation"], platform=PLATFORM, transport_profile=TRANSPORT,
        account_id=ACCOUNT, user_id=OWNER_USER)
    say(stage="workers_state", state=state["state"], enabled=state["enabled"],
        required_workers=state["required_workers"],
        can_prepare_workers=state["can_prepare_workers"],
        can_qualify_workers=state["can_qualify_workers"],
        can_activate=state["can_activate"],
        worker_execution=state["worker_execution"],
        workers={k: v["state"] for k, v in state["workers"].items()})


if __name__ == "__main__":
    main()
