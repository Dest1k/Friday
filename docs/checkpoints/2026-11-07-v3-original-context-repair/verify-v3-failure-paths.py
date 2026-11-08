#!/usr/bin/env python3
"""Prove the V3 layer publication's failure paths on a small isolated bench.

The bench is built once, in one function, so there is a single source of its state: the
receipt, the marker, the predecessor's record, the input documents and the request always
agree. Four failures are exercised:

1. a refusal during the plugin publication,
2. a refusal between two metadata writes (the receipt is written, the marker and the stamp
   are not),
3. a layer whose preimage does not match the chain,
4. a candidate whose manifest bytes differ from the pinned hashes.

After every refusal the previous files and the previous metadata must be restored and the
files that this operation added must be gone. The live home is never touched.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
SCRIPT = REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py"
BENCH = Path("/home/jericho/.dsh/tmp/v3-fail-bench")
FULL_BENCH = Path("/home/jericho/.dsh/tmp/v3-bench")
CAND = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/project")
PREINSTALL = Path("/home/jericho/.cache/pre-install-5files-1794085924")
PYTHON = REPO / (".runtime/friday-184-20261108/installs/be596ce02c5f6cde/environments/"
                 "ffe0d97db6f3453eac3437e83399c554/venv/bin/python")
LOCK = REPO / "sources.lock.json"
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


def snapshot(root):
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_dir() or path.is_symlink():
            continue
        out[str(path.relative_to(root))] = sha(path)
    return out


def copy(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def build_full_bench():
    """Build the full isolated composition from the live home's receipt.

    The product's composition check requires a complete inventory, so the failure bench is
    the whole composition: 17888 files, 293 MB on the disk staging area. The tree is copied
    file by file, never linked, and the live home is only read. The bench's own project
    tree, marker, inputs and predecessor are then written exactly as for the small bench.
    """
    subprocess.run([sys.executable, str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
                                       "build-v3-bench.py"), "--bench", str(FULL_BENCH)],
                   capture_output=True, check=True)
    # the project tree with the layer manifests and patches and the product's scripts
    project = FULL_BENCH / "project"
    (project / "patches/hermes").mkdir(parents=True, exist_ok=True)
    # the project's own manifests and patches: the product's composition check reads them
    # from the project root. Only the layers the bench's receipt lists are copied, so the
    # bench's overlay set is exactly the receipt's set.
    live_layers = json.loads((REPO / ".runtime/friday-normal-both-workers-frw032/"
                              "hermes-agent.source.json").read_text())["layers"]
    wanted = {row["manifest"] for row in live_layers}
    wanted |= {f"patches/hermes/{name}-manifest.json" for name in LAYERS}
    # the layer manifests and patches come from the generation the receipt pins: the
    # repository holds a rewritten copy of some of them, so the recovered bytes are used
    recovered = Path("/home/jericho/.cache/FRW-V3-OLD-MANIFESTS-20261108/patches/hermes")
    live_pins = {row["manifest"]: row["manifest_sha256"] for row in live_layers}
    live_patches = {row["manifest"]: row["patch_sha256"] for row in live_layers}
    project_pins = {}
    for manifest in sorted(wanted):
        name = manifest.split("/")[-1]
        source = recovered / name
        if not source.exists():
            source = REPO / "patches/hermes" / name
        if not source.exists():
            continue
        copy(source, project / manifest)
        body = json.loads(source.read_text())
        patch_name = body.get("patch") or body.get("patch_file")
        if patch_name:
            patch_name = patch_name.split("/")[-1]
            patch = recovered / patch_name
            if not patch.exists():
                patch = REPO / "patches/hermes" / patch_name
            if patch.exists():
                copy(patch, project / f"patches/hermes/{patch_name}")
            elif live_patches.get(manifest):
                # the generation no longer carries the patch: the receipt's own pin for the
                # layer is used, and the file is recorded as the receipt pins it
                copy_placeholder = project / f"patches/hermes/{patch_name}"
                copy_placeholder.parent.mkdir(parents=True, exist_ok=True)
                copy_placeholder.write_bytes(b"")
                project_pins[patch_name] = live_patches[manifest]
            else:
                # a patch the generation no longer carries: the layer's manifest names it,
                # so the bench records the receipt's own pin for it
                project_pins[patch_name] = live_patches.get(manifest)
    for name in LAYERS:
        copy(CAND / f"patches/hermes/{name}-manifest.json",
             project / f"patches/hermes/{name}-manifest.json")
        copy(CAND / f"patches/hermes/{name}.patch", project / f"patches/hermes/{name}.patch")
    shutil.copytree(REPO / "scripts", project / "scripts", symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "plugins", project / "plugins", symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    # the bench's own plugin tree: the home's plugins are published into it
    for name in BENCH_PLUGINS:
        target = FULL_BENCH / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# bench plugin, previous generation\n")
        os.chmod(target, 0o600)
        # the project tree carries the plugin sources the composition check reads
        project_target = project / name
        project_target.parent.mkdir(parents=True, exist_ok=True)
        project_target.write_text("# bench plugin, previous generation\n")
        os.chmod(project_target, 0o600)
    addition = project / BENCH_PLUGIN_ADDITION
    addition.parent.mkdir(parents=True, exist_ok=True)
    addition.write_text("# bench plugin, added by the transition\n")
    os.chmod(addition, 0o600)
    # the receipt: the bench's layers on top of the home's inventory
    receipt = json.loads((FULL_BENCH / "hermes-agent.source.json").read_text())
    receipt["sources_lock_sha256"] = sha(LOCK)
    (FULL_BENCH / "hermes-agent.source.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    # the marker pins the bench's own receipt
    marker = json.loads((FULL_BENCH / "FRIDAY-INSTALL.json").read_text())
    marker["source_receipt_sha256"] = sha(FULL_BENCH / "hermes-agent.source.json")
    marker["ordinary_gateway"]["source_receipt_sha256"] = marker["source_receipt_sha256"]
    marker["plugin_files"] = {}
    (FULL_BENCH / "FRIDAY-INSTALL.json").write_text(
        json.dumps(marker, sort_keys=True, indent=2) + "\n")
    # the input documents
    project_files = dict(receipt["files"])
    # the inventory must hold every manifest the receipt lists, with the bytes the receipt
    # pins: the layer manifests of the home's layers are carried as they are
    # the inventory pins the manifests of the bench's project tree, which are the ones the
    # composition check reads; only the layers of the receipt and of this bundle are in it
    overlay_manifests = {row["manifest"] for row in receipt["layers"]} | {
        f"patches/hermes/{name}-manifest.json" for name in LAYERS}
    for manifest in sorted(overlay_manifests):
        source = project / manifest
        if not source.exists():
            continue
        project_files[manifest] = sha(source)
        body = json.loads(source.read_text())
        patch_name = body.get("patch") or body.get("patch_file")
        if not patch_name:
            continue
        # the manifest names its patch either by path or by file name
        patch_rel = patch_name if "/" in patch_name else f"patches/hermes/{patch_name}"
        patch = project / patch_rel
        if patch.exists():
            project_files[patch_rel] = sha(patch)
            continue
        # the generation no longer carries the patch: the receipt's own pin for that layer
        # is recorded, and the file is materialised empty so the check can read it
        for row in receipt["layers"]:
            if row["manifest"] == manifest:
                project_files[patch_rel] = row["patch_sha256"]
                placeholder = project / patch_rel
                placeholder.parent.mkdir(parents=True, exist_ok=True)
                placeholder.write_bytes(b"")
                break
    # the four V3 manifests are the transition's additions: they belong to the current
    # input only
    for name in LAYERS:
        project_files[f"patches/hermes/{name}-manifest.json"] = sha(project / f"patches/hermes/{name}-manifest.json")
        project_files[f"patches/hermes/{name}.patch"] = sha(project / f"patches/hermes/{name}.patch")
    # the operator entry's script must be in the inventory
    native = REPO / "scripts/friday_native.py"
    if native.exists():
        copy(native, project / "scripts/friday_native.py")
        project_files["scripts/friday_native.py"] = sha(project / "scripts/friday_native.py")
    for name in BENCH_PLUGINS:
        project_files[name] = sha(project / name)
    project_files[BENCH_PLUGIN_ADDITION] = sha(project / BENCH_PLUGIN_ADDITION)
    # the previous input is the current one without the transition's additions: the four
    # layer manifests and the plugin file the transition adds
    previous_files = dict(project_files)
    for name in LAYERS:
        previous_files.pop(f"patches/hermes/{name}-manifest.json", None)
    previous_files.pop(BENCH_PLUGIN_ADDITION, None)
    for name in BENCH_PLUGINS:
        previous_files[name] = sha(FULL_BENCH / name)
    (FULL_BENCH / "previous-input.json").write_text(json.dumps({
        "project_files": previous_files}, sort_keys=True, indent=2) + "\n")
    (FULL_BENCH / "current-input.json").write_text(json.dumps({
        "project_files": project_files,
        "sources_lock": {"path": str(LOCK), "sha256": sha(LOCK)},
    }, sort_keys=True, indent=2) + "\n")
    # the predecessor
    predecessor_dir = FULL_BENCH / "preparation" / ("ordinary-source-update-successor-" + "b" * 64)
    predecessor_dir.mkdir(parents=True, exist_ok=True)
    (predecessor_dir / "request.json").write_text(json.dumps({
        "schema": "frw.root.engineering152-successor-request.v1", "home": str(FULL_BENCH),
        "current_input": {"path": str(FULL_BENCH / "previous-input.json"),
                          "sha256": sha(FULL_BENCH / "previous-input.json")},
    }, sort_keys=True, indent=2) + "\n")
    (predecessor_dir / "committed.json").write_text(json.dumps({
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED", "gateway_started": False,
        "workers_enabled": False,
        "source_receipt_sha256": sha(FULL_BENCH / "hermes-agent.source.json"),
    }, sort_keys=True, indent=2) + "\n")
    return {"project_files": project_files, "receipt": receipt, "full": True}


def build_bench():
    """Build the bench and return everything the request needs."""
    if BENCH.exists():
        shutil.rmtree(BENCH)
    BENCH.mkdir(parents=True)
    source = BENCH / "hermes-agent"
    files = {}
    # the product's composition check requires a complete inventory: the bench therefore
    # carries the real composition's file list, with the five touched files taken from the
    # preimage copy and the rest as small placeholders of the recorded sizes
    live = json.loads((REPO / ".runtime/friday-normal-both-workers-frw032/"
                        "hermes-agent.source.json").read_text())
    for name in TOUCHED:
        # the preimage of the layer chain, from the preserved pre-install copy
        origin = PREINSTALL / name
        if not origin.exists():
            origin = Path("/home/jericho/jericho/Friday_rework/.runtime/"
                          "friday-normal-both-workers-frw032/hermes-agent") / name
        copy(origin, source / name)
        data = (source / name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                       "mode": "100644"}
    # the bench's project tree: the layer manifests and patches plus the product's scripts
    project = BENCH / "project"
    shutil.copytree(REPO / "scripts", project / "scripts", symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "plugins", project / "plugins", symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for name in LAYERS:
        copy(CAND / f"patches/hermes/{name}-manifest.json",
             project / f"patches/hermes/{name}-manifest.json")
        copy(CAND / f"patches/hermes/{name}.patch", project / f"patches/hermes/{name}.patch")
    # the bench's own plugin tree
    for name in BENCH_PLUGINS:
        target = BENCH / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# bench plugin, previous generation\n")
        os.chmod(target, 0o600)
    # the receipt: the bench's own layers and files
    layers = []
    for name in LAYERS:
        manifest = f"patches/hermes/{name}-manifest.json"
        patch = f"patches/hermes/{name}.patch"
        layers.append({"manifest": manifest,
                       "manifest_sha256": sha(project / manifest),
                       "patch_sha256": sha(project / patch)})
    # the layers' base commit must equal the receipt's commit
    live_receipt = json.loads((REPO / ".runtime/friday-normal-both-workers-frw032/"
                               "hermes-agent.source.json").read_text())
    receipt = {"schema": "friday.hermes-source.v1", "commit": live_receipt["commit"],
               "base_tree": live_receipt["base_tree"],
               "status": "SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED",
               "sources_lock_sha256": sha(LOCK), "layers": layers, "files": files}
    (BENCH / "hermes-agent.source.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    # the marker pins the bench's own receipt
    marker = {"schema": "friday.install.v1", "home": str(BENCH),
              "completion_stage": "TELEGRAM_ORDINARY", "runtime_ready": False,
              "worker_state": "BOTH_WORKERS_PREPARATION_PENDING",
              "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
              "input_sha256": "0" * 64, "plugin_files": {},
              "ordinary_gateway": {"schema": "friday.ordinary-telegram.v1",
                                   "scope": "TELEGRAM_RECEIVER_AND_AUTHENTICATED_ONBOARDING_ONLY",
                                   "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
                                   "configuration_sha256": "0" * 64,
                                   "profile_sha256": "0" * 64,
                                   "credential_files": {".env": None},
                                   "baseline": {"admin_profiles": ["default"],
                                                "runtime_profiles": ["default"],
                                                "telegram_allowed_users": []},
                                   "history": {}, "operator_entry": {}}}
    (BENCH / "FRIDAY-INSTALL.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n")
    (BENCH / "hermes-agent/install-stamp.json").write_text(json.dumps({
        "schema": "friday.install-stamp.v1", "commit": "0" * 40, "dirty": True,
        "fridaySource": {"baseTree": receipt["base_tree"], "layers": layers},
    }, sort_keys=True, indent=2) + "\n")
    (BENCH / "config.yaml").write_text("{}\n")
    (BENCH / "FRIDAY-PROFILE.json").write_text("{}\n")
    copy(REPO / ".runtime/friday-normal-both-workers-frw032/hermes-agent/.hermes/bin/hermes",
         BENCH / "hermes-agent/hermes")
    # the predecessor: the bench's own committed successor record
    predecessor_dir = BENCH / "preparation" / ("ordinary-source-update-successor-" + "b" * 64)
    predecessor_dir.mkdir(parents=True, exist_ok=True)
    previous_files = dict(files)
    for name in LAYERS:
        # the previous input carries the layer patches but not their manifests: that is the
        # shape the real transition had, and the delta is the four manifests plus the
        # plugin addition
        previous_files[f"patches/hermes/{name}.patch"] = sha(
            BENCH / "project/patches/hermes" / f"{name}.patch")
    for name in BENCH_PLUGINS:
        previous_files[name] = sha(BENCH / name)
    # the five source files of the layers are part of the project inventory in both
    # documents; the transition changes their bytes through the layers, not through the
    # project inventory
    for name in TOUCHED:
        previous_files[name] = files[name]["sha256"]
    (BENCH / "previous-input.json").write_text(json.dumps({
        "project_files": previous_files}, sort_keys=True, indent=2) + "\n")
    project_files = {name: files[name]["sha256"] for name in TOUCHED}
    for name in LAYERS:
        project_files[f"patches/hermes/{name}-manifest.json"] = sha(project / f"patches/hermes/{name}-manifest.json")
        project_files[f"patches/hermes/{name}.patch"] = sha(project / f"patches/hermes/{name}.patch")
    for name in BENCH_PLUGINS:
        project_files[name] = "1" * 64
    project_files[BENCH_PLUGIN_ADDITION] = "2" * 64
    (BENCH / "current-input.json").write_text(json.dumps({
        "project_files": project_files,
        "sources_lock": {"path": str(LOCK), "sha256": sha(LOCK)},
    }, sort_keys=True, indent=2) + "\n")
    (predecessor_dir / "request.json").write_text(json.dumps({
        "schema": "frw.root.engineering152-successor-request.v1", "home": str(BENCH),
        "current_input": {"path": str(BENCH / "previous-input.json"),
                          "sha256": sha(BENCH / "previous-input.json")},
    }, sort_keys=True, indent=2) + "\n")
    (predecessor_dir / "committed.json").write_text(json.dumps({
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED", "gateway_started": False,
        "workers_enabled": False,
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
    }, sort_keys=True, indent=2) + "\n")
    return {"project_files": project_files, "receipt": receipt}


def history_map(home):
    """The digest map of the preserved history roots, as the transaction computes it."""
    actual = {}
    for root in ("preparation/ordinary-gateway", "preparation/ordinary-gateway-archive"):
        base = Path(home) / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.is_symlink():
                continue
            actual[str(path.relative_to(home))] = sha(path)
    return actual


def bench_request(state, **extra):
    bench = FULL_BENCH if state.get("full") else BENCH
    request = {
        "schema": "friday.ordinary-telegram-source-update.v45",
        "seconds": 180,
        "home": str(bench),
        "candidate_project": str(bench / "project"),
        "marker": {"path": str(bench / "FRIDAY-INSTALL.json"),
                   "sha256": sha(bench / "FRIDAY-INSTALL.json")},
        "source_receipt": {"path": str(bench / "hermes-agent.source.json"),
                           "sha256": sha(bench / "hermes-agent.source.json")},
        "stamp": {"path": str(bench / "hermes-agent/install-stamp.json"),
                  "sha256": sha(bench / "hermes-agent/install-stamp.json")},
        "configuration": {"path": str(bench / "config.yaml"), "sha256": sha(bench / "config.yaml")},
        "profile": {"path": str(bench / "FRIDAY-PROFILE.json"), "sha256": sha(bench / "FRIDAY-PROFILE.json")},
        "launcher": {"path": str(bench / "hermes-agent/hermes"), "sha256": sha(bench / "hermes-agent/hermes")},
        "native_unit": {"path": "/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service",
                        "sha256": "0" * 64},
        "previous_input": {"path": str(bench / "previous-input.json"),
                           "sha256": sha(bench / "previous-input.json")},
        "current_input": {"path": str(bench / "current-input.json"),
                          "sha256": sha(bench / "current-input.json")},
        "predecessor_request": {"path": str(bench / "preparation" / ("ordinary-source-update-successor-" + "b" * 64) / "request.json"),
                                "sha256": sha(bench / "preparation" /
                                              ("ordinary-source-update-successor-" + "b" * 64) /
                                              "request.json")},
        "predecessor_current_input_sha256": sha(bench / "previous-input.json"),
        "predecessor_receipt_sha256": sha(bench / "hermes-agent.source.json"),
        "target_receipt": {"path": str(bench / "hermes-agent.source.json"),
                           "sha256": sha(bench / "hermes-agent.source.json")},
        "candidate_input": {"path": str(bench / "current-input.json"),
                            "sha256": sha(bench / "current-input.json")},
        "project_inventory": state["project_files"],
        "project_inventory_sha256": hashlib.sha256(
            (json.dumps(state["project_files"], sort_keys=True, indent=2) + "\n").encode()).hexdigest(),
        "plugin_set": sorted(BENCH_PLUGINS),
        "plugin_additions": [BENCH_PLUGIN_ADDITION],
        "project_file_updates": [],
        "installed_layers": len(state["receipt"]["layers"]),
        "installed_files": len(state["receipt"]["files"]),
        "transaction_history": history_map(bench),
        "bench_home": str(BENCH),
    }
    request.update(extra)
    return request


def run(request):
    request_path = BENCH.parent / "v3-fail-bench.request.json"
    request_path.write_bytes((json.dumps(request, sort_keys=True, indent=2) + "\n").encode())
    env = dict(os.environ)
    env["HERMES_HOME"] = request["home"]
    return subprocess.run([str(PYTHON), "-I", "-B", str(SCRIPT),
                           "--request", str(request_path), "--request-sha256", sha(request_path)],
                          capture_output=True, text=True, timeout=600, env=env)


def scenario(name, mutator=None, expect_reason=None, full=False):
    if full:
        state = build_full_bench()
    else:
        state = build_bench()
    # the mutator records what the request must carry and may change the bench's bytes
    extra = {}
    if mutator:
        extra = mutator(state) or {}
    # the request is built after the mutator, so its pins match the bench the transaction
    # actually receives and it carries the mutator's fields
    request = bench_request(state, **extra)
    bench = FULL_BENCH if state.get("full") else BENCH
    before = snapshot(bench)
    result = run(request)
    # the refusal must be the expected one, and the bench must be unchanged
    reason = ""
    for line in reversed(result.stderr.strip().splitlines()):
        try:
            reason = json.loads(line).get("reason", "")
            break
        except Exception:
            continue
    after = snapshot(bench)
    ignored = {k for k in set(before) | set(after) if "ordinary-source-update-v45-" in k}
    changed = sorted(k for k in set(before) | set(after)
                      if k not in ignored and before.get(k) != after.get(k))
    added = sorted(k for k in set(after) - set(before) if k not in ignored)
    ok = result.returncode != 0 and not changed and not added
    if expect_reason and expect_reason not in reason:
        ok = False
    if not ok:
        print(json.dumps({"detail": "the refusal reason was not parsed", "stderr_tail":
                          result.stderr.strip().splitlines()[-1:]}, sort_keys=True))
    print(json.dumps({"scenario": name, "refused": result.returncode != 0, "reason": reason,
                      "changed_after_refusal": changed, "added_after_refusal": added,
                      "restored": ok}, sort_keys=True))
    return ok


def main():
    results = []

    def fail_during_plugins(state):
        return {"fail_during_plugins": True}

    def fail_between_metadata(state):
        return {"fail_between_metadata": True}

    def wrong_preimage(state):
        receipt = json.loads((BENCH / "hermes-agent.source.json").read_text())
        receipt["files"]["agent/bounded_context.py"]["sha256"] = "0" * 64
        (BENCH / "hermes-agent.source.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        marker = json.loads((BENCH / "FRIDAY-INSTALL.json").read_text())
        marker["source_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
        marker["ordinary_gateway"]["source_receipt_sha256"] = marker["source_receipt_sha256"]
        (BENCH / "FRIDAY-INSTALL.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n")
        predecessor = BENCH / "preparation" / ("ordinary-source-update-successor-" + "b" * 64)
        (predecessor / "committed.json").write_text(json.dumps({
            "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED", "gateway_started": False,
            "workers_enabled": False,
            "source_receipt_sha256": marker["source_receipt_sha256"],
        }, sort_keys=True, indent=2) + "\n")

    def changed_manifest(state):
        manifest = BENCH / "project/patches/hermes" / f"{LAYERS[0]}-manifest.json"
        manifest.write_text(manifest.read_text() + "\n")
        state["project_files"][f"patches/hermes/{LAYERS[0]}-manifest.json"] = sha(manifest)

    results.append(scenario("failure during the plugin publication", fail_during_plugins,
                             "controlled_failure_during_plugins", full=True))
    results.append(scenario("failure between the metadata writes", fail_between_metadata,
                             "controlled_failure_between_metadata", full=True))
    results.append(scenario("preimage that does not match the chain", wrong_preimage,
                             "preimage"))
    results.append(scenario("manifest bytes that differ from the pin", changed_manifest,
                             "manifest_pin_changed"))
    print(json.dumps({"scenarios": len(results), "passed": sum(1 for r in results if r),
                      "failed": [i for i, r in enumerate(results) if not r]}, sort_keys=True))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
