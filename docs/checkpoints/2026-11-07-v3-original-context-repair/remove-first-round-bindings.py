#!/usr/bin/env python3
"""Remove the two user bindings and their routes from the root configuration.

The first preparation round created them from the friday-local template; the areas
are now re-prepared from friday-ordinary-local, and the product refuses to adopt an
existing binding (existing_binding_not_adopted). Only the bindings and the route
rows for these two runtime profiles are removed; every other root setting is kept.

Written through the product's own config writers (digest check -> transaction ->
atomic write).
"""
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
PROFILES = ["telegram-bot-8812646969", "dest_telegram"]

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def main():
    from hermes_cli import config as native
    path = HOME / "config.yaml"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = native.require_readable_config_before_write(path)
    config = copy.deepcopy(raw)
    settings = config["plugins"]["entries"]["friday_rework"]["settings"]

    isolation = settings.get("user_isolation") or {}
    bindings = isolation.get("bindings") or []
    kept = [b for b in bindings if b.get("runtime_profile") not in PROFILES]
    removed_bindings = [b for b in bindings if b.get("runtime_profile") in PROFILES]
    isolation["bindings"] = kept
    settings["user_isolation"] = isolation

    accounts = settings["product_access"]["accounts"]
    for account in accounts:
        account["runtime_profiles"] = [p for p in account["runtime_profiles"]
                                       if p not in PROFILES]
    admin_profiles = settings["admin"]["profiles"]
    settings["admin"]["profiles"] = [p for p in admin_profiles if p not in PROFILES]

    gateway = config.get("gateway") or {}
    routes = gateway.get("profile_routes") or []
    removed_routes = [r for r in routes if r.get("profile") in PROFILES]
    gateway["profile_routes"] = [r for r in routes if r.get("profile") not in PROFILES]
    config["gateway"] = gateway

    with native.config_write_transaction(path):
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise SystemExit("config changed underneath this writer; reload required")
        native.atomic_config_write(path, config)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    say(stage="bindings_removed", removed_bindings=[b["runtime_profile"] for b in removed_bindings],
        removed_routes=[r.get("profile") for r in removed_routes],
        remaining_bindings=[b["runtime_profile"] for b in kept],
        account_runtime_profiles=[a["runtime_profiles"] for a in accounts],
        admin_profiles=settings["admin"]["profiles"],
        config_sha256_before=before, config_sha256_after=after)


if __name__ == "__main__":
    main()
