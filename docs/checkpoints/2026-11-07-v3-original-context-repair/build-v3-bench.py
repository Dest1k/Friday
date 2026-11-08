#!/usr/bin/env python3
"""Build an isolated bench for the V3 layer publication.

The bench contains ONLY the bytes the transaction reads or writes:

* the five source files the four V3 layers touch (plus their live siblings),
* the receipt and the marker,
* the preparation roots the history map covers,
* the committed successor transaction.

The receipt's inventory stays the live one: the composition check proves the bench's tree
against it, so the bench must contain every file the receipt pins. To keep the bench
small the source tree is materialised as hard links to the live home's files - the
transaction only reads them, and it publishes into the bench's own copy of the five
touched files. Nothing in the live home is reachable through a link.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
CANDIDATE = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/project")
TOUCHED = (
    "agent/agent_init.py",
    "agent/bounded_context.py",
    "agent/context_compressor.py",
    "agent/conversation_compression.py",
    "tools/file_tools.py",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def link_or_copy(source, target):
    """Copy the file.

    The product's composition check requires st_nlink == 1 on every file it reads, so a hard
    link is not usable for the bench: the files are copied. The copy is bounded by the
    receipt's inventory (233 MB), not by the whole runtime tree (592 MB with the generated
    products) and never by the environments.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    shutil.copy2(source, target)


def copy_file(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--bench", required=True, type=Path)
    parser.add_argument("--materialise", action="store_true",
                        help="copy the source tree instead of linking it (needed for a real apply)")
    args = parser.parse_args()
    bench = args.bench
    if bench.exists():
        shutil.rmtree(bench)
    bench.mkdir(parents=True)

    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    # the bench's receipt pins the preimage bytes of the five files it publishes
    bench_receipt_files = {}
    source = bench / "hermes-agent"
    # the source tree: every file the receipt pins
    # The bench starts from the composition BEFORE the V3 layers: the five touched files
    # come from the preserved pre-install copy, whose bytes the layers' preimage hashes
    # pin; the rest of the composition is copied as it is.
    preinstall = None
    for candidate in sorted(Path("/home/jericho/.cache").glob("pre-install-5files-*")):
        if (candidate / "agent/agent_init.py").exists():
            preinstall = candidate
    if preinstall is None:
        raise SystemExit("the preserved pre-install copy of the five files is missing")
    for name, row in receipt["files"].items():
        origin = HOME / "hermes-agent" / name
        if not origin.exists():
            continue
        target = source / name
        if name in TOUCHED:
            copy_file(preinstall / name, target)
        else:
            copy_file(origin, target)
    # the generated artefacts that are not in the receipt are not needed for the check
    # the plugin tree of the home (the V3 plugin set is published into it)
    home_plugins = HOME / "plugins/friday_rework"
    if home_plugins.exists():
        shutil.copytree(home_plugins, bench / "plugins/friday_rework", symlinks=False)
    for name in TOUCHED:
        data = (source / name).read_bytes()
        bench_receipt_files[name] = {"sha256": hashlib.sha256(data).hexdigest(),
                                     "bytes": len(data), "mode": "100644"}
    bench_receipt = json.loads(json.dumps(receipt))
    bench_receipt["files"].update(bench_receipt_files)
    # the bench starts BEFORE the V3 layers: their manifest entries are removed from the
    # receipt, so the transition publishes them
    bench_receipt["layers"] = [row for row in bench_receipt["layers"]
                               if not any(name in row["manifest"] for name in (
                                   "source157-original-context-deterministic-overhead",
                                   "source157-bounded-schema-hints",
                                   "source157-tool-budget-fit", "write-file-format-guard"))]
    (bench / "hermes-agent.source.json").write_text(
        json.dumps(bench_receipt, sort_keys=True, indent=2) + "\n")
    os.chmod(bench / "hermes-agent.source.json", 0o600)
    copy_file(HOME / "FRIDAY-INSTALL.json", bench / "FRIDAY-INSTALL.json")
    copy_file(HOME / "hermes-agent/install-stamp.json", bench / "hermes-agent/install-stamp.json")
    copy_file(HOME / "config.yaml", bench / "config.yaml")
    copy_file(HOME / "FRIDAY-PROFILE.json", bench / "FRIDAY-PROFILE.json")
    launcher = HOME / "hermes-agent/.hermes/bin/hermes"
    if launcher.exists():
        copy_file(launcher, bench / "hermes-agent/.hermes/bin/hermes")
    # the history roots and the committed successor transaction
    for root in ("preparation/ordinary-gateway", "preparation/ordinary-gateway-archive"):
        origin = HOME / root
        if origin.exists():
            shutil.copytree(origin, bench / root, symlinks=False)
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    successor = HOME / "preparation" / ("ordinary-source-update-successor-"
                                       + marker["ordinary_source_update_request"]["sha256"])
    if successor.exists():
        shutil.copytree(successor, bench / successor.relative_to(HOME), symlinks=False)
    # the candidate project tree: read-only source of the four layer manifests and patches
    os.chmod(bench, 0o700)
    print(json.dumps({
        "bench": str(bench),
        "files": len(receipt["files"]),
        "touched": list(TOUCHED),
        "size_mb": round(sum(p.stat().st_size for p in bench.rglob('*') if p.is_file()) / 1e6, 1),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
