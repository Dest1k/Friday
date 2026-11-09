#!/usr/bin/env python3
"""Inspect the access store's tombstones and generations. It no longer removes anything.

The previous version of this script popped the principal's row out of the access
document and wrote the document back, which destroyed the access history: the
generations the product's advance_access contract keeps, and the tombstones that record
which preparation was withdrawn. That removal is what let a fresh preparation be
accepted, and it cost the product its own history.

This version only reports:

* the principal's row, its generation and its enabled state,
* the tombstones and generations the store holds for it,
* the contract of the product's own advance_access, so the real way of preparing a
  principal again can be chosen from the facts.

Nothing is written. Removing a row is a product decision that belongs to the product's
own access transaction, not to an operator script.
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
    if session.user_id != username:
        raise SystemExit("session identity mismatch")

    access_mod = importlib.import_module("friday_rework.access")
    state_mod = importlib.import_module("hermes_cli.plugins_state")
    state = state_mod.PluginState("friday_rework")
    access = access_mod.ProductAccess(state)
    document = access._document()
    users = document.get("users", {})
    for user_id, profile in USERS:
        key = principal_id("telegram", TRANSPORT, ACCOUNT, user_id)
        row = users.get(key)
        if row is None:
            say(stage="no_row", user_id=user_id, principal=key[:8], profile=profile)
            continue
        say(stage="row", user_id=user_id, profile=profile, principal=key[:8],
            enabled=row.get("enabled"), generation=row.get("generation"),
            updated=row.get("updated"), fields=sorted(row))
    say(stage="store", schema=access_mod.KEY, users=len(users),
        tombstones=sorted(k[:8] for k, v in users.items() if v.get("enabled") is False),
        generations={k[:8]: v.get("generation") for k, v in sorted(users.items())})
    rows = current_access()["users"]
    say(stage="current_access", count=len(rows), keys=[k[:8] for k in rows])
    say(stage="note", text="nothing was written; the access history and the generations "
                           "are preserved")
    clean()


if __name__ == "__main__":
    main()
