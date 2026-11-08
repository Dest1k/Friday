#!/usr/bin/env python3
"""Targeted correction of the 2026-11-08 Jarvis restore attempt.

The attempt created two profile homes with a legacy (receipt-less) marker and wrote
policy/access records by hand. That is a weaker activation contract than the product's
onboarding path, so the attempt is withdrawn — without deleting anything:

  * profile homes are MOVED to a quarantine directory with a manifest (data preserved)
  * config.yaml is restored from the verified pre-change backup
  * the product-access store returns to its pre-change state (file absent)
  * pairing grants are kept (legitimate native grants; the onboarding path requires one)

The preserved source of user data is the untouched old home:
  .runtime/friday-normal-both-workers-frw032/profiles/<profile>
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
BACKUP = HOME / "backups/pre-user-area-20261108T1145/config.yaml"
EXPECTED_BACKUP_SHA = "778991c246afc77261d457a69031f107042639e228f9b5a7382c7b2653041f1c"
QUARANTINE = HOME / "preparation/user-area-restore-attempt-20261108T1210"
STORE = HOME / "plugin-data/agent-plugin-friday_rework-877e6505"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    rows = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink():
            rows[str(path.relative_to(root))] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    return rows


def main():
    if sha(BACKUP) != EXPECTED_BACKUP_SHA:
        raise SystemExit("backup config hash changed; refusing to restore")
    live = HOME / "config.yaml"
    if sha(live) == EXPECTED_BACKUP_SHA:
        raise SystemExit("live config already equals the pre-change backup")
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "friday.withdrawn-restore-attempt.v1", "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "reason": "legacy marker without onboarding receipt is not the product activation contract",
                "profiles": {}, "config": {}, "product_access": {}, "pairing": "kept"}
    subprocess.run(["systemctl", "--user", "stop", "hermes-gateway-1e9db5b2.service"], check=True)
    for name in ("dest_telegram", "telegram-bot-8812646969"):
        src = HOME / "profiles" / name
        if src.exists():
            manifest["profiles"][name] = {"files": inventory(src), "moved_to": str(QUARANTINE / name)}
            shutil.move(str(src), str(QUARANTINE / name))
    manifest["config"]["restored_from"] = str(BACKUP)
    manifest["config"]["restored_sha256"] = EXPECTED_BACKUP_SHA
    manifest["config"]["previous_sha256"] = sha(live)
    shutil.copy2(BACKUP, live)
    os.chmod(live, 0o600)
    for name in ("state.json", "admission.lock"):
        path = STORE / name
        if path.exists():
            manifest["product_access"][name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
            target = QUARANTINE / ("product-access-" + name)
            shutil.move(str(path), str(target))
    (QUARANTINE / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"stage": "withdrawn", "quarantine": str(QUARANTINE),
                      "config_sha256": sha(live), "profiles_moved": sorted(manifest["profiles"]),
                      "store_files_moved": sorted(name for name in os.listdir(STORE))}))


if __name__ == "__main__":
    main()
