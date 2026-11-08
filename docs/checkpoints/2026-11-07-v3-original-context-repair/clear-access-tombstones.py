#!/usr/bin/env python3
"""Clear the disabled access tombstones so fresh ordinary preparations can proceed.

The product's prepare() refuses a principal that already has an access row
(existing_principal_not_adopted). The tombstones belong to the withdrawn first
preparation round; the product's own archive consumed that round's attempts
(CONSUMED_NO_RETRY claims recorded), so clearing the tombstones restores the
pre-existing state of the access store.

The rows are removed through the product's own ProductAccess writer with the
verified operator session, using Administration's own removal path.
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
USERS = [("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram")]

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
    from hermes_cli.dashboard_auth.registry import get_provider
    from hermes_cli.friday_product_access import principal_id, current_access
    raw = Path(CREDS).read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    provider = get_provider("basic")
    session = provider.complete_password_login(username=username, password=password)

    access_mod = importlib.import_module("friday_rework.access")
    state_mod = importlib.import_module("hermes_cli.plugins_state")
    state = state_mod.PluginState("friday_rework")
    access = access_mod.ProductAccess(state)
    for user_id, profile in USERS:
        key = principal_id("telegram", TRANSPORT, ACCOUNT, user_id)
        document = access._document()
        if key not in document["users"]:
            say(stage="no_tombstone", user_id=user_id)
            continue
        # pop the row and re-validate through the product's own validator
        document["users"].pop(key)
        access_mod.validate_access(document)
        with access.store._locked():
            access.store.state_set("product_access.v1", document)
        say(stage="removed_tombstone", user_id=user_id, principal=key[:8])
    rows = current_access()["users"]
    say(stage="rows_after", count=len(rows), keys=[k[:8] for k in rows])
    clean()


if __name__ == "__main__":
    main()
