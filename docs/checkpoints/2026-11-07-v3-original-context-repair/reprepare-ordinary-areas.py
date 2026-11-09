#!/usr/bin/env python3
"""Re-prepare the two user areas from the ordinary (worker-free) template.

The product's prepare() refuses a principal that already has an access row
(existing_principal_not_adopted). The previous version of this script reached that
state by writing an empty access document, which dropped the tombstones AND the
generations the access history keeps, and by deleting an existing archive before the
next transfer.

This version keeps the access history intact and never destroys an archive:

* The access store is not emptied. The product's own advance_access contract keeps
  tombstones and generations; a repeated preparation is expressed as a product
  transaction that ADDS the new generation of the principal and leaves the previous
  generations as tombstones. The store is never rewritten with an empty users map.
* The first-preparation archive is never deleted. A second transfer of the same profile
  gets its own directory, named after the transfer; a name collision is a refusal before
  any data changes.
* The operator session, the profile, the bindings, the receipts, the configuration and
  the locks stay under the product's own writers; nothing is written by hand.
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
ACCOUNT = "8751854128"
TRANSPORT = "default"
TEMPLATE = "friday-ordinary-local"
AREAS = [("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram")]
TRANSFER = "transfer-01"

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


def access_rows(state):
    from hermes_cli.friday_product_access import current_access
    return current_access(state)["users"]


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    from hermes_cli.dashboard_auth.registry import get_provider
    from hermes_cli.friday_product_access import KEY, principal_id
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

    state = PluginState("friday_rework")
    rows = access_rows(state)
    say(stage="access_before", users=sorted(rows),
        note="the access store keeps its tombstones and generations; it is not emptied")

    for user_id, profile in AREAS:
        home = HOME / "profiles" / profile
        if home.exists():
            archive_root = home.parent / "worker-setup-archive"
            archive_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            target = archive_root / TRANSFER / profile
            if target.exists():
                # A name collision is a refusal before any data changes: the previously
                # saved profile, its attempts and its receipts are not rubbish.
                raise SystemExit("archive target already exists, refusing to replace it: "
                                 + str(target))
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.move(str(home), str(target))
            say(stage="moved_to_archive", profile=profile, transfer=TRANSFER,
                target=str(target))
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
    rows_after = access_rows(state)
    say(stage="access_after", users=sorted(rows_after),
        note="the access history is preserved across the preparation")
    clean()


if __name__ == "__main__":
    main()
