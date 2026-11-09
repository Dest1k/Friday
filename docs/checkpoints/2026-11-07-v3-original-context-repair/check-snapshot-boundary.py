#!/usr/bin/env python3
"""Check the traversal boundary of the injection-point snapshot.

The snapshot of the injected failure used to derive its scope from the PARENTS of the
result directory. With the result directory inside the DSH staging area, that was the
whole of /home/jericho/.dsh: every session, every neighbouring bench and every cache, each
file read in full. This check proves the corrected boundary on a tiny fixture:

  * the named files of the bench are read;
  * a foreign file of a DSH session and a file of a neighbouring temporary directory are
    NOT read at all - the check proves it by making those files unreadable;
  * a missing named file is an explicit refusal, not a silent skip;
  * a symlink is an explicit refusal, not a silent skip;
  * the result never claims a general success over a partial set.

The fixture is tiny on purpose; no large file is created.
"""
import json
import os
import shutil
import stat
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
SCRIPT = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py"
ROOT = Path("/home/jericho/.dsh/tmp/snapshot-boundary-fixture")
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPT.parent))

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("frw_publication", SCRIPT)
pub = importlib.util.module_from_spec(_spec)
sys.modules["frw_publication"] = pub
_spec.loader.exec_module(pub)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def build():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    home = ROOT / "bench-home"
    result = ROOT / "result"
    (home / "plugins").mkdir(parents=True, exist_ok=True)
    (home / "plugins" / "a.txt").write_bytes(b"alpha\n")
    (home / "b.txt").write_bytes(b"beta\n")
    # foreign files that must never be read
    session = ROOT / "session"
    session.mkdir(parents=True, exist_ok=True)
    (session / "foreign-session.txt").write_bytes(b"session\n")
    neighbour = ROOT / "neighbour-bench"
    neighbour.mkdir(parents=True, exist_ok=True)
    (neighbour / "foreign-neighbour.bin").write_bytes(b"neighbour\n")
    # make the foreign files unreadable: a read would fail loudly
    for path in (session / "foreign-session.txt", neighbour / "foreign-neighbour.bin"):
        os.chmod(path, 0o000)
    return home, result


def main():
    home, result = build()
    named = ["b.txt", "plugins/a.txt"]
    pub._write_injection_snapshot(result, home / "b.txt", named, home)
    state = json.loads((result / "STATE-AT-INJECTION.json").read_text())
    read_paths = state["read_paths"]
    results = []

    results.append({
        "check": "the named files of the bench are read",
        "read": sorted(Path(p).relative_to(home).as_posix() for p in read_paths),
        "ok": sorted(Path(p).relative_to(home).as_posix() for p in read_paths) == sorted(named)})

    foreign = [ROOT / "session" / "foreign-session.txt", ROOT / "neighbour-bench" / "foreign-neighbour.bin"]
    touched = [str(p) for p in foreign if str(p) in read_paths]
    results.append({"check": "no foreign file is in the read set",
                    "foreign_files_read": touched, "ok": not touched})

    # a missing named file is an explicit refusal
    try:
        pub._write_injection_snapshot(result / "second", home / "b.txt", ["b.txt", "missing.txt"], home)
        refusal, reason = None, None
    except pub.Refused as exc:
        refusal, reason = "Refused", str(exc)
    results.append({"check": "a missing named file is an explicit refusal",
                    "outcome": refusal, "reason": reason,
                    "ok": refusal == "Refused" and "missing" in (reason or "")})

    # a symlink is an explicit refusal
    link = home / "link.txt"
    os.symlink(home / "b.txt", link)
    try:
        pub._write_injection_snapshot(result / "third", home / "b.txt", ["b.txt", "link.txt"], home)
        refusal, reason = None, None
    except pub.Refused as exc:
        refusal, reason = "Refused", str(exc)
    results.append({"check": "a symlink is an explicit refusal",
                    "outcome": refusal, "reason": reason,
                    "ok": refusal == "Refused" and "symlink" in (reason or "")})

    # a path that leaves the home is an explicit refusal
    try:
        pub._write_injection_snapshot(result / "fourth", home / "b.txt",
                                      ["b.txt", "../neighbour-bench/foreign-neighbour.bin"], home)
        refusal, reason = None, None
    except pub.Refused as exc:
        refusal, reason = "Refused", str(exc)
    results.append({"check": "a path outside the home is an explicit refusal",
                    "outcome": refusal, "reason": reason,
                    "ok": refusal == "Refused"})

    # an empty file set is an explicit refusal
    try:
        pub._write_injection_snapshot(result / "fifth", home / "b.txt", [], home)
        refusal, reason = None, None
    except pub.Refused as exc:
        refusal, reason = "Refused", str(exc)
    results.append({"check": "an empty file set is an explicit refusal",
                    "outcome": refusal, "reason": reason, "ok": refusal == "Refused"})

    for result in results:
        say(**result)
    say(summary={"checks": len(results),
                 "passed": sum(1 for r in results if r["ok"]),
                 "ok": all(r["ok"] for r in results)})
    # the fixture's unreadable files are made readable again before the removal
    for path in sorted(ROOT.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        try:
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
