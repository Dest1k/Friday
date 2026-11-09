#!/usr/bin/env python3
"""Merge the preserved user data of one profile into its prepared home.

Source of truth: the untouched old home (.runtime/friday-normal-both-workers-frw032).
Target: the prepared profile home in the installed home.

Only user data is copied (session store, workspace, memories, skills, cron). The
profile's own native configuration, onboarding receipt, credentials and scope marker
are never touched: they belong to the product's own writers.

Rules that this version enforces, each of them a defect of the previous version:

* The session store is copied through the SQLite backup API, not by copying the file.
  A copy of ``state.db`` alone loses whatever the write-ahead log still holds.
* The source's own ``-wal`` and ``-shm`` sidecars are read together with the database
  through one connection, so the copy reflects every committed transaction. They are
  never removed: the source is the truth and stays untouched.
* The target's sidecars are never deleted before the target database is read. A read
  error is a refusal, not a reason to empty the target.
* A merge is refused when the target already holds a different session store. The
  previous version read the target with ``immutable=1``, which ignores the WAL and
  cannot show the current data.
* The file trees are merged with an explicit conflict rule: a target file that differs
  from the source is kept, and the difference is reported. The previous version used
  ``copytree(dirs_exist_ok=True)``, which silently replaced newer target data with the
  older copy.
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
TABLES = ("sessions", "messages", "session_turn_leases")


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def db_counts(path):
    """The row counts of a database, read in ordinary mode.

    The database is opened read-only with the write-ahead log included, so the counts
    reflect every committed transaction. A read error is raised, never swallowed.
    """
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in con.execute(
            "select name from sqlite_master where type='table'")}
        counts = {}
        for name in TABLES:
            if name in tables:
                counts[name] = con.execute(f"select count(*) from {name}").fetchone()[0]
        return counts
    finally:
        con.close()


def consistent_copy(source, target):
    """Copy a live SQLite database through the backup API.

    The source is opened in ordinary mode, so its write-ahead log is applied; the copy
    is written with the backup API, so the result is one consistent database.
    """
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(str(target))
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()
    os.chmod(target, 0o600)
    return {"copied": True, "bytes": target.stat().st_size, "sha256": sha(target),
            "rows": db_counts(target)}


def merge_tree(source, target):
    """Merge a file tree without replacing newer target data.

    A target file that is byte-identical to the source is left alone. A target file
    that differs is KEPT and reported: the merge never destroys target data. A source
    file that the target lacks is copied.
    """
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    added, kept, identical = [], [], []
    for path in sorted(source.rglob("*")):
        if path.is_dir() or path.is_symlink():
            continue
        relative = path.relative_to(source)
        destination = target / relative
        if destination.exists():
            if sha(path) == sha(destination):
                identical.append(str(relative))
            else:
                kept.append(str(relative))
            continue
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        os.chmod(destination, 0o600)
        added.append(str(relative))
    return {"tree": source.name, "added": len(added), "kept_target_differing": len(kept),
            "identical": len(identical),
            "kept_examples": kept[:10], "added_examples": added[:10]}


def main():
    profiles = sys.argv[1:] or ["telegram-bot-8812646969", "dest_telegram"]
    for profile in profiles:
        source = OLD / profile
        target = NEW / profile
        if not source.is_dir() or not target.is_dir():
            say(stage="skip", profile=profile, reason="source or target missing")
            continue
        say(stage="begin", profile=profile)
        result = {"stage": "merge", "profile": profile}
        src_db = source / "state.db"
        dst_db = target / "state.db"
        if src_db.is_file():
            if dst_db.is_file() and dst_db.stat().st_size > 0:
                # The target's own sidecars stay in place: the target database is read in
                # ordinary mode, so its write-ahead log is part of what it holds.
                existing = db_counts(dst_db)
                if existing.get("sessions", 0) > 0:
                    result["state_db"] = {"skipped": "target already holds sessions",
                                          "target_rows": existing}
                else:
                    result["state_db"] = consistent_copy(src_db, dst_db)
            else:
                result["state_db"] = consistent_copy(src_db, dst_db)
        else:
            result["state_db"] = {"absent_in_source": True}
        result["trees"] = [merge_tree(source / name, target / name)
                           for name in TREES if (source / name).is_dir()]
        result["source_state_db_sha256"] = sha(src_db) if src_db.is_file() else None
        result["source_sidecars"] = {
            suffix: ((source / ("state.db" + suffix)).stat().st_size
                     if (source / ("state.db" + suffix)).exists() else None)
            for suffix in ("-wal", "-shm")}
        say(**result)


if __name__ == "__main__":
    main()
