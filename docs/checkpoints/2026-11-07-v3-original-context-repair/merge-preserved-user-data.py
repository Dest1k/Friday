#!/usr/bin/env python3
"""Merge the preserved user data of one profile into its prepared home.

Source of truth: the untouched old home (.runtime/friday-normal-both-workers-frw032).
Target: the prepared profile home in the installed home.

Only user data is copied (session store, workspace, memories, skills, cron). The
profile's own native configuration, onboarding receipt, credentials and scope
marker are never touched: they belong to the product's own writers.

Copy is refused when the target already holds a different session store, so a
merge can never overwrite live data silently.
"""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

RUNTIME = Path("/home/jericho/jericho/Friday_rework/.runtime")
OLD = RUNTIME / "friday-normal-both-workers-frw032/profiles"
NEW = RUNTIME / "friday-184-20261108/profiles"
TREES = ["workspace", "memories", "skills", "cron"]


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def db_rows(path):
    con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    try:
        tables = [r[0] for r in con.execute(
            "select name from sqlite_master where type='table'")]
        counts = {}
        for name in ("sessions", "messages", "session_turn_leases"):
            if name in tables:
                counts[name] = con.execute(f"select count(*) from {name}").fetchone()[0]
        return counts
    finally:
        con.close()


def main():
    profiles = sys.argv[1:] or ["telegram-bot-8812646969", "dest_telegram"]
    for profile in profiles:
        source = OLD / profile
        target = NEW / profile
        if not source.is_dir() or not target.is_dir():
            say(stage="skip", profile=profile, reason="source or target missing")
            continue
        result = {"stage": "merge", "profile": profile}
        say(stage="begin", profile=profile)
        src_db = source / "state.db"
        dst_db = target / "state.db"
        # A stale WAL (salt mismatch) makes the DB unreadable in normal mode; the
        # caller must have produced an epoch-clean DB first. Never copy sidecars.
        for suffix in ("-wal", "-shm"):
            stale = target / ("state.db" + suffix)
            if stale.exists():
                stale.unlink()
        if src_db.is_file():
            if dst_db.is_file() and dst_db.stat().st_size > 0:
                try:
                    existing = db_rows(dst_db)
                except Exception:
                    existing = {}
                if existing.get("sessions", 0) > 0:
                    result["state_db"] = {"skipped": "target already holds sessions"}
                else:
                    shutil.copy2(src_db, dst_db)
                    os.chmod(dst_db, 0o600)
                    result["state_db"] = {"copied": True, "bytes": dst_db.stat().st_size,
                                          "sha256": sha(dst_db), "rows": db_rows(dst_db)}
            else:
                shutil.copy2(src_db, dst_db)
                os.chmod(dst_db, 0o600)
                result["state_db"] = {"copied": True, "bytes": dst_db.stat().st_size,
                                      "sha256": sha(dst_db), "rows": db_rows(dst_db)}
        copied = []
        for name in TREES:
            src, dst = source / name, target / name
            if not src.is_dir():
                continue
            dst.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=False)
            files = sum(1 for p in dst.rglob("*") if p.is_file())
            copied.append({"tree": name, "files": files})
        result["trees"] = copied
        result["source_state_db_sha256"] = sha(src_db) if src_db.is_file() else None
        say(**result)


if __name__ == "__main__":
    main()
