#!/usr/bin/env python3
"""Build a small isolated bench for the V3 layer publication's failure paths.

The bench holds only what the transaction touches and reads:

* the five source files the four V3 layers touch,
* a reduced receipt that pins exactly those five files plus the layer manifests,
* the marker, the stamp, the configuration and the profile,
* the preparation roots the history map covers,
* the committed successor transaction,
* a small plugin tree with two plugins to publish and one to add.

The reduced receipt keeps the composition check meaningful: it pins every file the bench
tree holds, so the product's own check really runs over the bench.

The bench never touches the live home: its paths are separate and its receipt is its own.
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
LAYERS = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)
TOUCHED = (
    "agent/agent_init.py",
    "agent/bounded_context.py",
    "agent/context_compressor.py",
    "agent/conversation_compression.py",
    "tools/file_tools.py",
)
BENCH_PLUGINS = ("plugins/friday_rework/alpha.py", "plugins/friday_rework/beta.py")
BENCH_PLUGIN_ADDITION = "plugins/friday_rework/gamma.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def private_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def copy_file(source, target, mode=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if mode is not None:
        os.chmod(target, mode)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--bench", required=True, type=Path)
    args = parser.parse_args()
    bench = args.bench
    if bench.exists():
        shutil.rmtree(bench)
    bench.mkdir(parents=True)

    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    source = bench / "hermes-agent"
    # The bench starts from the composition BEFORE the V3 layers: the live home already
    # carries the published bytes, so the layers' preimages are taken from the predecessor
    # transaction's own beforeimage, which the product's journal keeps.
    before_receipt = None
    marker_live = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    successor = HOME / "preparation" / ("ordinary-source-update-successor-"
                                        + marker_live["ordinary_source_update_request"]["sha256"])
    candidate_before = successor / "before" / "hermes-agent.source.json"
    if candidate_before.exists():
        before_receipt = json.loads(candidate_before.read_text())
    # The bench starts from the composition BEFORE the V3 layers: the live home already
    # carries the published bytes, so the preimages come from the preserved pre-install
    # copy, whose files are pinned by the layers' own preimage hashes.
    before_root = None
    for candidate in sorted(Path("/home/jericho/.cache").glob("pre-install-5files-*")):
        if (candidate / "agent/agent_init.py").exists():
            before_root = candidate
    require_before = before_root is not None
    files = {}
    for name in TOUCHED:
        origin = HOME / "hermes-agent" / name
        if before_root is not None and (before_root / name).exists():
            origin = before_root / name
        copy_file(origin, source / name)
        data = (source / name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                       "mode": "100644"}
    # a reduced receipt that pins exactly the bench tree
    lock = Path("/home/jericho/jericho/Friday_rework/sources.lock.json")
    reduced = {"schema": receipt["schema"], "commit": receipt["commit"],
               "base_tree": receipt["base_tree"], "status": receipt["status"],
               "sources_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
               "layers": [row for row in receipt["layers"]
                          if row["manifest"] not in {f"patches/hermes/{n}-manifest.json"
                                                    for n in LAYERS}],
               "files": files}
    for name in TOUCHED:
        reduced["files"][name] = files[name]
    # the layer manifests and patches are part of the bench's own project tree, together
    # with the product's scripts package, so the product's own composition check can run
    project = bench / "project"
    shutil.copytree(Path("/home/jericho/jericho/Friday_rework/scripts"), project / "scripts",
                    symlinks=False, ignore=shutil.ignore_patterns("__pycache__"))
    # the product's validation package: the plugins the composition check imports
    shutil.copytree(Path("/home/jericho/jericho/Friday_rework/plugins"),
                    project / "plugins", symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for name in LAYERS:
        copy_file(CANDIDATE / f"patches/hermes/{name}-manifest.json",
                  project / f"patches/hermes/{name}-manifest.json")
        copy_file(CANDIDATE / f"patches/hermes/{name}.patch",
                  project / f"patches/hermes/{name}.patch")
    # the bench's own plugin tree: two plugins to publish and one to add
    for name in BENCH_PLUGINS:
        target = bench / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# bench plugin, previous generation\n")
        os.chmod(target, 0o600)
    # the launcher the request pins
    launcher = HOME / "hermes-agent/.hermes/bin/hermes"
    if launcher.exists():
        copy_file(launcher, bench / "hermes-agent/hermes")
    copy_file(HOME / "FRIDAY-INSTALL.json", bench / "FRIDAY-INSTALL.json")
    copy_file(HOME / "hermes-agent/install-stamp.json", bench / "hermes-agent/install-stamp.json")
    copy_file(HOME / "config.yaml", bench / "config.yaml")
    copy_file(HOME / "FRIDAY-PROFILE.json", bench / "FRIDAY-PROFILE.json")
    for root in ("preparation/ordinary-gateway", "preparation/ordinary-gateway-archive"):
        origin = HOME / root
        if origin.exists():
            shutil.copytree(origin, bench / root, symlinks=False)
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    successor = HOME / "preparation" / ("ordinary-source-update-successor-"
                                        + marker["ordinary_source_update_request"]["sha256"])
    if successor.exists():
        shutil.copytree(successor, bench / successor.relative_to(HOME), symlinks=False)
    # the bench's predecessor: its own committed successor record, so the transaction's
    # predecessor check has a record to read
    predecessor_dir = private_dir(bench / "preparation" /
                                  ("ordinary-source-update-successor-" + "b" * 64))
    predecessor_dir.mkdir(parents=True, exist_ok=True)
    (predecessor_dir / "request.json").write_text(json.dumps({
        "schema": "frw.root.engineering152-successor-request.v1", "home": str(bench),
        "current_input": {"path": str(bench / "previous-input.json"), "sha256": ""},
    }, sort_keys=True, indent=2) + "\n")
    (predecessor_dir / "committed.json").write_text(json.dumps({
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED", "gateway_started": False,
        "workers_enabled": False, "source_receipt_sha256": "",
    }, sort_keys=True, indent=2) + "\n")
    # The bench's own receipt
    (bench / "hermes-agent.source.json").write_text(
        json.dumps(reduced, sort_keys=True, indent=2) + "\n")
    os.chmod(bench / "hermes-agent.source.json", 0o600)
    # the bench's marker must pin the bench's own receipt
    bench_marker = json.loads((bench / "FRIDAY-INSTALL.json").read_text())
    bench_marker["source_receipt_sha256"] = hashlib.sha256(
        (bench / "hermes-agent.source.json").read_bytes()).hexdigest()
    bench_marker["ordinary_gateway"]["source_receipt_sha256"] = \
        bench_marker["source_receipt_sha256"]
    bench_marker["plugin_files"] = {}
    (bench / "FRIDAY-INSTALL.json").write_text(
        json.dumps(bench_marker, sort_keys=True, indent=2) + "\n")
    os.chmod(bench / "FRIDAY-INSTALL.json", 0o600)
    os.chmod(bench, 0o700)
    print(json.dumps({"bench": str(bench), "layers": len(LAYERS), "files": len(files),
                      "plugins": list(BENCH_PLUGINS),
                      "plugin_addition": BENCH_PLUGIN_ADDITION,
                      "size_kb": round(sum(p.stat().st_size for p in bench.rglob('*')
                                           if p.is_file()) / 1024, 1)}, sort_keys=True))


if __name__ == "__main__":
    main()
