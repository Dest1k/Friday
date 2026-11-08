#!/usr/bin/env python3
"""Add the product's own ordinary (worker-free) onboarding template to the root set.

The product's installer creates `friday-ordinary-local` as an exact copy of
`friday-local` with `worker_inputs` removed (scripts/friday_ordinary_install.py:750).
A profile prepared from that template has no `worker_requirements`, so
`required_workers()` is False and `activate()` publishes the scope marker without
requiring DSH/A0 to be qualified - the shape the old WORKING composition uses.

This script performs that one root-configuration change through the product's own
config writers (digest check -> transaction -> atomic write), then verifies the
result with the product's own `validate_template`.

Nothing else in the root configuration is touched.
"""
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")

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
    from hermes_cli import config as native
    onboarding_mod = importlib.import_module("friday_rework.onboarding")

    path = HOME / "config.yaml"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = native.require_readable_config_before_write(path)
    config = copy.deepcopy(raw)
    settings = config["plugins"]["entries"]["friday_rework"]["settings"]
    plans = settings["onboarding"]["templates"]

    if "friday-ordinary-local" in plans:
        say(stage="already_present", templates=sorted(plans))
        return
    if "friday-local" not in plans:
        raise SystemExit("friday-local template is missing")

    ordinary = copy.deepcopy(plans["friday-local"])
    ordinary.pop("worker_inputs", None)
    onboarding_mod.validate_template(ordinary)
    plans["friday-ordinary-local"] = ordinary

    with native.config_write_transaction(path):
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise SystemExit("config changed underneath this writer; reload required")
        native.atomic_config_write(path, config)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    say(stage="ordinary_template_added", templates=sorted(plans),
        config_sha256_before=before, config_sha256_after=after)
    clean()


if __name__ == "__main__":
    main()
