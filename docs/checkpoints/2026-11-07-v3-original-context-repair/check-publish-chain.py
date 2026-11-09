#!/usr/bin/env python3
"""Exercise the whole late-failure chain of the publication on a small fixture.

The chain is: publish() renames the file, the snapshot of the named files is written, the
injected failure is raised, and Journal.restore() puts the previous bytes and modes back.

The earlier boundary fixture called the snapshot helper directly, so it could not see a
failure inside publish() itself. This check goes through publish() and therefore proves
that the injection point is reached with the expected target, that the expected file set is
read, that the bytes really changed at the failure point and that the rollback restores the
previous bytes AND the previous modes.

A foreign exception (a NameError, for example) is NOT counted as the expected injection.

The fixture is tiny and lives in /home/jericho/.dsh/tmp. The serving home is never
published and never rolled back.
"""
import importlib.util
import json
import os
import shutil
import stat
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
SCRIPT = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py"
ROOT = Path("/home/jericho/.dsh/tmp/publish-chain-fixture")
sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("frw_publication_chain", SCRIPT)
pub = importlib.util.module_from_spec(_spec)
sys.modules["frw_publication_chain"] = pub
_spec.loader.exec_module(pub)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def modes(root):
    return {str(p.relative_to(root)): stat.S_IMODE(p.lstat().st_mode)
            for p in sorted(Path(root).rglob("*")) if p.is_file() and not p.is_symlink()}


def digest(path):
    return pub.digest(Path(path).read_bytes())


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    home = ROOT / "home"
    result = ROOT / "snapshot"
    (home / "plugins").mkdir(parents=True, exist_ok=True)
    watched = ["plugins/a.txt", "b.txt"]
    (home / "plugins" / "a.txt").write_bytes(b"alpha-original\n")
    (home / "b.txt").write_bytes(b"beta-original\n")
    os.chmod(home / "b.txt", 0o640)
    before_modes = modes(home)
    before_bytes = {name: digest(home / name) for name in watched}

    # the injection is armed for the named target and the named file set
    pub.INJECT_AFTER_RENAME = True
    pub.INJECT_TARGET = str(home / "b.txt")
    pub.INJECT_SNAPSHOT_DIR = str(result)
    pub.INJECT_SNAPSHOT_FILES = tuple(watched)
    pub.INJECT_SNAPSHOT_HOME = home

    journal = pub.Journal(ROOT / "journal", home)
    journal.record_existing(home / "b.txt", (home / "b.txt").read_bytes())
    journal.record_existing(home / "plugins" / "a.txt", (home / "plugins" / "a.txt").read_bytes())
    published = []
    outcome = None
    try:
        data = b"beta-published-by-the-chain\n"
        # the same call the transaction makes: the path is registered BEFORE the write
        published.append(home / "b.txt")
        pub.publish(home / "b.txt", data, 0o600)
    except BaseException as exc:  # the injected failure is expected
        outcome = (type(exc).__name__, str(exc))
    else:
        outcome = ("NO_FAILURE", "")

    # the snapshot must exist and describe the state AT the failure point
    snapshot_file = result / "STATE-AT-INJECTION.json"
    snapshot = json.loads(snapshot_file.read_text()) if snapshot_file.exists() else None
    at_point = {}
    if snapshot:
        for name in watched:
            entry = snapshot["files"].get(str(home / name))
            at_point[name] = entry

    # the file really changed before the rollback
    changed_at_point = {name: (at_point[name]["sha256"] != before_bytes[name])
                        for name in watched if at_point.get(name)}
    injection_flag_after_failure = pub.INJECT_AFTER_RENAME

    # and the rollback restores the previous bytes and modes
    try:
        journal.restore(published)
        restore_outcome = "RESTORED"
    except BaseException as exc:
        restore_outcome = type(exc).__name__ + ": " + str(exc)[:120]
    restored_bytes = {name: digest(home / name) for name in watched}
    after_modes = modes(home)

    expected_failure = (outcome[0] == "OSError" and "injected failure after the rename" in outcome[1])
    results = [
        {"check": "publish() raised the injected failure itself",
         "outcome": outcome[0], "detail": outcome[1][:120], "ok": expected_failure},
        {"check": "the snapshot was written at the failure point",
         "snapshot": str(snapshot_file) if snapshot else None,
         "at_target": snapshot.get("at_target") if snapshot else None,
         "target_is_the_named_one": bool(snapshot) and snapshot.get("at_target") == str(home / "b.txt"),
         "file_set": sorted(Path(p).relative_to(home).as_posix() for p in (snapshot or {}).get("read_paths", [])),
         "ok": bool(snapshot) and snapshot.get("at_target") == str(home / "b.txt")
               and sorted(Path(p).relative_to(home).as_posix() for p in snapshot.get("read_paths", [])) == sorted(watched)},
        {"check": "the published file really differed at the failure point",
         "changed": changed_at_point,
         "the_published_file_changed": changed_at_point.get("b.txt") is True,
         "the_untouched_files_kept_their_bytes": all(
             changed_at_point.get(name) is False for name in watched if name != "b.txt"),
         "ok": changed_at_point.get("b.txt") is True and all(
             changed_at_point.get(name) is False for name in watched if name != "b.txt")},
        {"check": "the injection was one-shot",
         "flag_after_the_failure": injection_flag_after_failure,
         "ok": injection_flag_after_failure is False},
        {"check": "the rollback restored the previous bytes",
         "before": before_bytes, "after": restored_bytes, "restore_outcome": restore_outcome,
         "ok": restored_bytes == before_bytes},
        {"check": "the rollback restored the previous modes",
         "before": before_modes, "after": after_modes,
         "ok": after_modes == before_modes},
    ]
    for result in results:
        say(**result)
    say(summary={"checks": len(results),
                 "passed": sum(1 for r in results if r["ok"]),
                 "ok": all(r["ok"] for r in results),
                 "note": ("the chain publish -> snapshot -> injected failure -> Journal.restore was "
                          "exercised through publish() itself; a foreign exception is not "
                          "counted as the expected injection.")})
    shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
