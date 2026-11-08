#!/usr/bin/env python3
"""Run the PRODUCT's archive engine for one profile's stale worker setup.

Calls worker_archive.archive() with the request document assembled from the product's
own recorded facts, under the product's own native guard. The engine renames the
profile's workers/ tree into worker-setup-archive/transactions/<tree_key>/workers and
publishes a permanent CONSUMED_NO_RETRY claim; it grants no runtime authority.

The native guard requires the gateway to be stopped and its host lock unclaimed, so
the caller must stop the gateway for the duration of this transaction.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
PROFILE = "dest_telegram"
USER_ID = "467035772"
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


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    wa = importlib.import_module("friday_rework.worker_archive")
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id
    from hermes_cli.plugins_state import PluginState
    access_mod = importlib.import_module("friday_rework.access")
    ProductAccess = access_mod.ProductAccess

    home = HOME / "profiles" / PROFILE
    request_path = HOME / "preparation/user-area-archive-evidence-owner-20261108/request.json"
    request = json.loads(request_path.read_text())

    policy = scope.policy(HOME)
    binding = next(b for b in policy["bindings"]
                   if b["runtime_profile"] == PROFILE and b["user_id"] == USER_ID)
    key = principal_id(binding["platform"], binding["transport_profile"],
                       binding["account_id"], binding["user_id"])

    state = PluginState("friday_rework")
    access = ProductAccess(state)
    row = access._document()["users"].get(key)
    if row is None:
        raise SystemExit("no product access row for this principal")

    budget_mod = importlib.import_module("friday_rework.runtime_containment")
    budget = budget_mod.Budget(180, started=time.monotonic())

    def verify():
        budget.check()
        with scope.authority(HOME):
            current = scope.policy(HOME)
            rows = ProductAccess(state)._document()["users"]
            if key not in rows or rows[key].get("generation") != request["generation"]:
                raise PermissionError("worker_archive_authority_changed")
            if current is None:
                raise PermissionError("worker_archive_policy_missing")
        return True

    try:
        result = wa.archive(home, binding, request["generation"], request,
                            verify=verify, budget=budget)
        say(stage="archived", result=result)
    except Exception as exc:
        say(stage="refused", error_type=type(exc).__name__, error=str(exc)[:300])
        raise
    clean()


if __name__ == "__main__":
    main()
