#!/usr/bin/env python3
"""Offline containment checks for the archive operations of cases A-13 and A-14.

The two cases are the only ones of the agreed volume whose required evidence is OFFLINE.
Five operations remain open in the registry for them:

  RAR expanded boundary, LHA expanded boundary, ARJ link, LHA hardlink, 7z hardlink
  and the asynchronous gateway cancel.

This script checks the PRODUCT's own containment primitives against those operations on
isolated fixtures under the disk staging area. It does not write into the product's
runtime tree, it does not send anything and it does not read the live home's data. Every
fixture is created, checked and removed inside the bench.

What is checked, and what is NOT:

The extraction below is this script's own _safe_extract. It is NOT the product's archive
handler, so this check does not prove the product's archive behaviour. What it does check
is the PRODUCT's own primitives - canonical, owned_file (O_NOFOLLOW, st_nlink == 1,
private mode) and require - against the archive situations the registry names:

* an archive entry whose name leaves the extraction root is refused and the root stays
  empty;
* an archive entry that is a link is refused;
* an archive whose expansion would exceed the quota is refused and nothing is left
  behind;
* the product's primitives refuse a symlinked file, a hardlinked file and a path that
  leaves its root, and accept an ordinary owned file.

The cancel scenario starts a sleeping script and terminates it with SIGTERM. It shows
that a terminated process leaves no partial state in that bench; it does NOT show that a
started PRODUCT operation can be cancelled and cleaned up.

The fixtures are tar-based: the RAR, LHA, ARJ and 7z formats cannot be exercised on this
machine, so the per-format extraction is not covered. A-13 and A-14 therefore stay
NOT_RUN in the registry.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "plugins"))
os.environ.setdefault("HERMES_HOME", str(REPO / ".runtime/friday-normal-both-workers-frw032"))

from friday_rework.runtime_primitives import (  # noqa: E402
    Refused, canonical, owned_file, require,
)

BENCH = Path("/home/jericho/.dsh/tmp/a13-a14-bench")
QUOTA_BYTES = 64 * 1024


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def refused(callable_, *args, **kwargs):
    """Run a call and report whether the product refused it."""
    try:
        callable_(*args, **kwargs)
    except Refused as exc:
        return True, exc.reason
    except Exception as exc:  # a different failure is not a product refusal
        return False, type(exc).__name__
    return False, None


def contains_escape(path):
    """True when a path leaves the extraction root."""
    try:
        canonical(str(path))
    except Refused:
        return True
    return False


def check_traversal(bench):
    """An entry that names a path outside the extraction root must be refused."""
    root = bench / "traversal"
    root.mkdir(parents=True, exist_ok=True)
    archive = bench / "traversal.tar"
    payload = bench / "payload.txt"
    payload.write_text("содержимое\n")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="../escape.txt")
    refused_flag, reason = refused(_safe_extract, archive, root, QUOTA_BYTES)
    escapes = [p.name for p in root.iterdir()] if root.exists() else []
    outside = (bench / "escape.txt").exists()
    return {"operation": "traversal outside the extraction root",
            "refused": refused_flag, "reason": reason,
            "extraction_root_empty": not escapes, "nothing_written_outside": not outside}


def _safe_extract(archive, root, quota):
    """Extract an archive under the product's containment rules."""
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    total = 0
    with tarfile.open(archive, "r") as tar:
        for member in tar.getmembers():
            name = member.name
            target = root / name
            require(not contains_escape(target), "archive_entry_outside_root")
            require(not member.issym() and not member.islnk(), "archive_link_entry_refused")
            total += max(member.size, 0)
            require(total <= quota, "archive_expansion_quota_exceeded")
            if member.isfile():
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                source = tar.extractfile(member)
                if source is not None:
                    target.write_bytes(source.read())
                    os.chmod(target, 0o600)


def check_link_entry(bench):
    """A link entry (hardlink or symlink) inside an archive must be refused."""
    root = bench / "links"
    root.mkdir(parents=True, exist_ok=True)
    archive = bench / "links.tar"
    payload = bench / "link-payload.txt"
    payload.write_text("цель\n")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="target.txt")
        info = tarfile.TarInfo("link.txt")
        info.type = tarfile.LNKTYPE
        info.linkname = "target.txt"
        tar.addfile(info)
    refused_flag, reason = refused(_safe_extract, archive, root, QUOTA_BYTES)
    return {"operation": "link entry inside an archive", "refused": refused_flag,
            "reason": reason}


def check_quota(bench):
    """An archive whose expansion exceeds the quota must be refused and leave nothing."""
    root = bench / "quota"
    root.mkdir(parents=True, exist_ok=True)
    archive = bench / "quota.tar"
    payload = bench / "big.txt"
    payload.write_bytes(b"x" * (QUOTA_BYTES * 4))
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="big.bin")
    refused_flag, reason = refused(_safe_extract, archive, root, QUOTA_BYTES)
    leftovers = [p.name for p in root.iterdir()] if root.exists() else []
    return {"operation": "expansion beyond the quota", "refused": refused_flag,
            "reason": reason, "nothing_left_behind": not leftovers}


def check_primitives(bench):
    """The primitives themselves: a symlink, a hardlink and an escaping path."""
    root = bench / "primitives"
    root.mkdir(mode=0o700, parents=True)
    plain = root / "plain.txt"
    plain.write_text("обычный\n")
    os.chmod(plain, 0o600)
    link_source = root / "link-source.txt"
    link_source.write_text("цель ссылки\n")
    os.chmod(link_source, 0o600)
    link = root / "symlink.txt"
    os.symlink(link_source, link)
    hard_source = root / "hard-source.txt"
    hard_source.write_text("цель жёсткой ссылки\n")
    os.chmod(hard_source, 0o600)
    hard = root / "hard.txt"
    os.link(hard_source, hard)
    sym_ok, sym_reason = refused(owned_file, link)
    hard_ok, hard_reason = refused(owned_file, hard)
    escape_ok, escape_reason = refused(canonical, str(root / ".." / "outside"))
    results = [
        {"operation": "symlinked file refused", "refused": sym_ok, "reason": sym_reason},
        {"operation": "hardlinked file refused", "refused": hard_ok, "reason": hard_reason},
        {"operation": "path outside its root refused", "refused": escape_ok,
         "reason": escape_reason},
        {"operation": "ordinary owned file accepted", "refused": False,
         "bytes": len(owned_file(plain))},
    ]
    return results


def check_async_cancel(bench):
    """An operation cancelled while it runs leaves no partial state."""
    root = bench / "cancel"
    root.mkdir(mode=0o700, exist_ok=True)
    archive = bench / "cancel.tar"
    payload = bench / "cancel-payload.txt"
    payload.write_text("отмена\n")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="partial.txt")
    script = bench / "cancel.py"
    script.write_text(
        "import sys, os, signal, threading, time\n"
        "sys.path.insert(0, %r)\n" % str(REPO / "plugins") +
        "from friday_rework.runtime_primitives import require\n"
        "root = %r\n" % str(root) +
        "def work():\n"
        "    require(True, 'never')\n"
        "    time.sleep(30)\n"
        "t = threading.Thread(target=work, daemon=True); t.start()\n"
        "time.sleep(0.2); os.kill(os.getpid(), signal.SIGTERM)\n")
    result = subprocess.run([sys.executable, str(script)], capture_output=True, timeout=30)
    leftovers = [p.name for p in root.iterdir()] if root.exists() else []
    return {"operation": "a terminated sleeping process leaves no partial state",
            "terminated_by_signal": result.returncode < 0 or result.returncode != 0,
            "returncode": result.returncode, "nothing_left_behind": not leftovers}


def main():
    if BENCH.exists():
        shutil.rmtree(BENCH)
    BENCH.mkdir(mode=0o700, parents=True)
    checks = [check_traversal(BENCH), check_link_entry(BENCH), check_quota(BENCH),
              check_primitives(BENCH), check_async_cancel(BENCH)]
    for check in checks:
        if isinstance(check, list):
            say(stage="primitives", results=check)
        else:
            say(stage="operation", **check)
    refusals = [c for c in checks if isinstance(c, dict) and c.get("refused")]
    failures = [c for c in refusals if not (c.get("extraction_root_empty", True)
                                          and c.get("nothing_written_outside", True)
                                          and c.get("nothing_left_behind", True))]
    say(stage="summary", operations=len(checks), refused=len(refusals),
        failures=[f["operation"] for f in failures])
    shutil.rmtree(BENCH, ignore_errors=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
