#!/usr/bin/env python3
"""V3 layer publication onto the serving ordinary home (the reviewed layers).

Design constraints honoured by this script:

* No copy of the runtime. The composition is checked against the live tree with the
  product's own ``source_checked`` and a proven-cache list of the generated artefacts;
  the tree is never cloned.
* Independent source and target data. Every layer manifest is read from the candidate
  project tree, every expected byte from the live serving home, and the two are compared;
  no comparison reads the same file twice.
* Journal first, publish second. Every changed file is recorded with its beforeimage in
  the transaction directory before it is published, and a failed run restores the
  beforeimages.
* One receiver. The transaction refuses to start unless the gateway unit is stopped.

Usage:
    python -I -B SCRIPT --request PATH --request-sha256 SHA
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import shutil
import stat
import importlib.machinery
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "friday.ordinary-telegram-source-update.v45"
# The explicit-composition schema: the request MUST name the layers of THIS operation in
# the field `layer_names`, and the validator refuses an absent, empty, malformed or
# repeated set instead of widening the operation to every known layer.
SCHEMA_EXPLICIT = "friday.ordinary-telegram-source-update.v46"
LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
    "bounded-resume-sidecar-guard",
    "bounded-7z-codec-activation",
    "bounded-current-ask-identity",
    "necessary-document-clarification-p04",
    "archive-conversion-failure-provenance-after188",
    "arj-unix-attribute-types-after-source189",
    "read-file-reject-write-arguments-after-source189",
    "archive-conversion-named-target-status-after-source190",
    "ordinary-direct-plain-cancel-after-source192",
    "ods-target-comments-after-source193",
)
# The composition of the HISTORICAL four-layer request, named explicitly. A legacy v45
# request that carries no `layer_names` keeps exactly this meaning; it never widens to
# every layer this file happens to know today.
HISTORICAL_LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)
REQUIRED_HISTORY_ROOTS = (
    "preparation/ordinary-gateway",
    "preparation/ordinary-gateway-archive",
)


# A controlled failure at the rename/sync boundary of ONE named target. The injection is
# ONE-SHOT: it fires on the publication of that target and never during the rollback, so
# a rollback really restores the state instead of failing at the same place again.
INJECT_AFTER_RENAME = False
INJECT_TARGET = None
# When the injection fires, the transaction records what the home looks like AT THAT
# MOMENT: the bytes and modes of every file it has already published, and of every file it
# added. The record is written OUTSIDE the rollback journal, so the rollback cannot change
# it; it is the evidence that the late point was reached with changed files on disk.
INJECT_SNAPSHOT_DIR = None
# The files whose state is recorded at the injection point. They are named explicitly by
# the request; the scope of the read is never derived from a directory's parents.
INJECT_SNAPSHOT_FILES = ()
# The home the snapshot reads from. It is set from the VERIFIED home of the running
# transaction, never from the parents of the result directory, and it is passed to the
# snapshot explicitly.
INJECT_SNAPSHOT_HOME = None


class Refused(Exception):
    """The transaction refused; the home is unchanged."""


class StopUnconfirmed(Exception):
    """A consumer could not be confirmed stopped; the home is unchanged."""


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def read_bytes(path, limit=256 * 1024 ** 2):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode), "transaction_not_a_regular_file")
        require(info.st_size <= limit, "transaction_file_too_large")
        data = b""
        while len(data) <= limit:
            chunk = os.read(fd, min(1024 ** 2, limit + 1 - len(data)))
            if not chunk:
                break
            data += chunk
        require(len(data) <= limit, "transaction_file_too_large")
        named = path.lstat()
        for key in ("st_dev", "st_ino", "st_uid", "st_size", "st_mtime_ns", "st_ctime_ns"):
            require(getattr(info, key) == getattr(named, key), "transaction_file_identity_changed")
        return data
    finally:
        os.close(fd)


def read_json(path):
    return json.loads(read_bytes(path))


def owned_file(path):
    """Read a file the transaction owns; refuse links and foreign ownership."""
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode),
            "transaction_owned_regular_file_required")
    require(info.st_uid == os.getuid(), "transaction_owned_file_required")
    return read_bytes(path)


def private_directory(path, mode=0o700):
    path = Path(path)
    if path.exists():
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == mode, "transaction_private_directory_required")
        return path
    path.mkdir(parents=True, mode=mode)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == mode, "transaction_private_directory_required")
    return path


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    sync_directory(path.parent)


def publish(target, data, mode=0o600):
    """Publish bytes to the home through a private temporary file and one rename.

    A failure between the rename and the directory synchronisation leaves the file
    changed. The caller registers the path in the rollback list before the call, so such a
    file is restored as well.
    """
    global INJECT_AFTER_RENAME
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name("." + target.name + ".publish.tmp")
    if tmp.exists():
        tmp.unlink()
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    # the mode is set explicitly: the process umask would otherwise reduce it
    os.chmod(tmp, mode)
    os.replace(tmp, target)
    if INJECT_AFTER_RENAME and (INJECT_TARGET is None or str(target) == INJECT_TARGET):
        # The injection is one-shot: it fires on the publication of the named target and
        # never again, so the ROLLBACK of that same target restores it instead of failing
        # at the same boundary again.
        INJECT_AFTER_RENAME = False
        if INJECT_SNAPSHOT_DIR is not None:
            _write_injection_snapshot(INJECT_SNAPSHOT_DIR, target,
                                     INJECT_SNAPSHOT_FILES, INJECT_SNAPSHOT_HOME)
        # a controlled failure at the rename/sync boundary, used to prove that the rollback
        # covers a file that was already changed when the failure happened
        raise OSError(errno.EIO, "injected failure after the rename")
    sync_directory(target.parent)


def private_parents(root, relative):
    """Create the parent directories of a relative path inside the private root."""
    current = Path(root)
    for part in Path(relative).parent.parts:
        current = current / part
        if current.exists():
            info = current.lstat()
            require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
                    "transaction_directory_custody_refused")
            continue
        current.mkdir(mode=0o700)
        info = current.lstat()
        require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700,
                "transaction_directory_custody_refused")


# --------------------------------------------------------------------------- gateway


def gateway_running(unit_path, bench_home=None):
    """True when the gateway unit is active; the transaction refuses to run then.

    ``bench_home`` is only used on an isolated bench: there the unit of the bench's own
    runtime is inspected. The live home is never affected by a bench run.
    """
    unit = Path(unit_path)
    if bench_home is not None:
        # a bench run must not stop or inspect the live gateway; the bench's own gateway
        # is represented by a unit file inside the bench.
        bench_unit = Path(bench_home) / "preparation" / "bench-unit.name"
        if bench_unit.exists():
            unit = Path(bench_unit.read_text().strip())
        else:
            return False
    result = subprocess.run(["systemctl", "--user", "is-active", unit.name],
                            capture_output=True, text=True, timeout=30)
    return result.stdout.strip() == "active"


def _digest_file(path, limit=64 * 1024 * 1024, chunk=64 * 1024):
    """Stream a file through the digest with a bounded read and a bounded size."""
    import hashlib as _hashlib
    size = 0
    hasher = _hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            size += len(block)
            if size > limit:
                raise Refused("transaction_snapshot_file_too_large:" + str(path))
            hasher.update(block)
    return hasher.hexdigest(), size


def _write_injection_snapshot(directory, current_target, files, home):
    """Record the state of EXACTLY the named files at the moment of the injected failure.

    The set of files is passed in explicitly. The scope of the read is never derived from
    the parents of the result directory, so DSH sessions, neighbouring benches, caches and
    other temporary work are outside it by construction. Every named file must exist, must
    be a regular file inside the home and must not be a symlink; a missing file, an
    unreadable file or a size above the bound is an explicit refusal, never a silent skip.
    """
    import stat as _stat
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    home = Path(home).resolve()
    if not files:
        raise Refused("transaction_snapshot_file_set_empty")
    state = {}
    read_paths = []
    for relative in files:
        if not isinstance(relative, str) or not relative or relative.startswith("/"):
            raise Refused("transaction_snapshot_path_invalid:" + str(relative))
        target = (home / relative)
        # a symlink is refused by its own name, before any resolution
        if target.is_symlink():
            raise Refused("transaction_snapshot_path_is_symlink:" + relative)
        try:
            resolved = target.resolve()
        except OSError:
            raise Refused("transaction_snapshot_path_unresolvable:" + relative) from None
        if resolved != target or home not in resolved.parents:
            raise Refused("transaction_snapshot_path_outside_home:" + relative)
        if not target.is_file():
            raise Refused("transaction_snapshot_file_missing:" + relative)
        info = target.lstat()
        if not _stat.S_ISREG(info.st_mode):
            raise Refused("transaction_snapshot_file_not_regular:" + relative)
        sha256, size = _digest_file(target)
        state[str(target)] = {"sha256": sha256, "mode": _stat.S_IMODE(info.st_mode),
                              "bytes": size}
        read_paths.append(str(target))
    (directory / "STATE-AT-INJECTION.json").write_bytes(encoded(
        {"schema": "friday.v3.injection-point-state.v1",
         "at_target": str(current_target),
         "home": str(home),
         "files": state,
         "read_paths": read_paths}))


class Journal:
    """One beforeimage store for the whole operation.

    Every file the operation touches is recorded BEFORE it is written: the real previous
    bytes of the home and the attributes needed to restore them. A file that did not
    exist before is recorded as absent, so the rollback removes it. The receipt, the
    marker and the stamp are recorded the same way, so a refusal restores the metadata
    together with the content.
    """

    def __init__(self, root, home):
        self.root = Path(root)
        self.home = Path(home)
        self.entries = {}

    def entries_dict(self):
        return dict(self.entries)

    def _relative(self, path):
        """The path of a file relative to the home, so the journal stays inside its root."""
        path = Path(path)
        try:
            return path.relative_to(self.home)
        except ValueError:
            return Path(path.name)

    def _target(self, path):
        target = self.root / "before" / self._relative(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def record_existing(self, path, data):
        """Record the real previous bytes of an existing file.

        The first recording wins: a file that is written twice keeps the bytes it had
        before the operation started, not the bytes of the intermediate write.
        """
        path = Path(path)
        key = str(path)
        if key in self.entries:
            return self.entries[key]
        info = path.lstat()
        entry = {"state": "EXISTED", "sha256": digest(data), "bytes": len(data),
                 "mode": stat.S_IMODE(info.st_mode)}
        write_atomic(self._target(path), data, 0o600)
        self.entries[key] = entry
        return entry

    def record_absent(self, path):
        """Record that the file did not exist before this operation."""
        path = Path(path)
        key = str(path)
        if key in self.entries:
            return self.entries[key]
        entry = {"state": "ABSENT"}
        self.entries[key] = entry
        return entry

    def record(self, path, data):
        """Record the previous state of a file that is about to be written."""
        path = Path(path)
        if path.exists() and not path.is_symlink():
            return self.record_existing(path, data)
        return self.record_absent(path)

    def restore(self, paths):
        """Restore the recorded state of the given paths, newest first."""
        for path in reversed(list(paths)):
            key = str(path)
            entry = self.entries.get(key)
            if entry is None:
                continue
            target = Path(path)
            if entry["state"] == "ABSENT":
                if target.exists() or target.is_symlink():
                    target.unlink()
                    sync_directory(target.parent)
                continue
            saved = self._target(path)
            if not saved.exists():
                continue
            publish(target, owned_file(saved), entry.get("mode", 0o600))

    def write_intent(self, name, payload):
        write_atomic(self.root / name, encoded(payload), 0o600)


# ------------------------------------------------------------------ layer inventory


def resolve_layer_names(request):
    """Resolve the EXACT composition of this publication from the request.

    Two schemas are understood and both name the composition explicitly:

    * v46 (SCHEMA_EXPLICIT) REQUIRES the field `layer_names`. An absent field, a non-list,
      an empty list, a non-string element, a duplicate and an unknown name are each
      refused. A request never widens itself to every known layer.
    * v45 (SCHEMA) is the legacy schema of the historical four-layer request. When such a
      request carries no `layer_names` field, its composition is exactly
      HISTORICAL_LAYER_NAMES, named here as an explicit constant; it never widens to every
      layer known today. When it does carry the field, the field is validated exactly like
      in v46 and it wins over the legacy default.

    Returns the names in the order the request declares them.
    """
    if "layer_names" in request:
        names = request["layer_names"]
        if not isinstance(names, list):
            raise Refused("transaction_layer_names_malformed")
        if not names:
            raise Refused("transaction_layer_names_empty")
        for name in names:
            if not isinstance(name, str) or not name:
                raise Refused("transaction_layer_names_malformed")
        if len(set(names)) != len(names):
            raise Refused("transaction_layer_names_repeated")
        return tuple(names)
    if request.get("schema") == SCHEMA:
        return HISTORICAL_LAYER_NAMES
    raise Refused("transaction_layer_names_required")


def check_project_inventory(request, previous_input, current_input):
    """Validate the exact operation delta without staging or publishing any bytes."""
    layer_names = resolve_layer_names(request)
    require(set(layer_names) <= set(LAYER_NAMES), "transaction_layer_names_unknown")
    inventory = request["project_inventory"]
    require(inventory == current_input["project_files"],
            "transaction_project_inventory_changed")
    require(digest(encoded(inventory)) == request["project_inventory_sha256"],
            "transaction_project_inventory_changed")
    previous_files = previous_input["project_files"]
    current_files = current_input["project_files"]
    additions = {f"patches/hermes/{name}-manifest.json" for name in layer_names} | \
                {f"patches/hermes/{name}.patch" for name in layer_names}
    require(additions <= set(current_files), "transaction_layer_files_missing")
    require(set(previous_files) <= set(current_files),
            "transaction_project_file_removed")
    # Existing selected patches remain immutable. A genuinely new selected patch may
    # arrive with its manifest, so the exact installed input remains the predecessor;
    # no reconstructed baseline is needed merely to pretend the new patch was present.
    new_patches = {f"patches/hermes/{name}.patch" for name in layer_names
                   if f"patches/hermes/{name}.patch" not in previous_files}
    expected_additions = {f"patches/hermes/{name}-manifest.json" for name in layer_names} | \
                          new_patches | set(request["plugin_additions"])
    require(set(current_files) - set(previous_files) == expected_additions,
            "transaction_project_delta_changed")
    for name in layer_names:
        patch = f"patches/hermes/{name}.patch"
        require(patch in current_files
                and (patch not in previous_files
                     or current_files[patch] == previous_files[patch]),
                "transaction_layer_patch_pin_changed:" + patch)
    for name in previous_files:
        if name in request["plugin_set"]:
            # the plugin set is published as its own step and is checked there
            continue
        if name in request.get("project_file_updates", []):
            # a project file the transition deliberately updates; its bytes are proven
            # against the candidate and published in its own step
            continue
        require(current_files[name] == previous_files[name],
                "transaction_project_file_changed:" + name)

    return layer_names


def check_plugin_preimages(request, previous_input, current_input, marker, home,
                           already_published=False):
    """Bind the changed plugin set to its installed byte and marker before staging.

    An already-applied source bundle may still have pending old plugin bytes. It may
    also carry an already-published plugin, but only if its marker and bytes both pin
    the current image. An unexplained third image is never adopted as a beforeimage.
    """
    previous = previous_input["project_files"]
    current = current_input["project_files"]
    changed = {name for name, pin in previous.items()
               if name.startswith("plugins/friday_rework/") and current.get(name) != pin}
    names = request["plugin_set"]
    require(isinstance(names, list) and all(isinstance(name, str) for name in names)
            and len(names) == len(changed) and set(names) == changed,
            "transaction_plugin_set_changed")
    pins = marker.get("plugin_files", {})
    for name in sorted(changed):
        expected = previous[name]
        if already_published and pins.get(name) == current[name]:
            expected = current[name]
        require(pins.get(name) == expected, "transaction_plugin_marker_changed:" + name)
        require(digest(owned_file(Path(home) / name)) == expected,
                "transaction_plugin_preimage_changed:" + name)


def read_layers(candidate_root, receipt, home, project_files, layer_names):
    """Read the layer manifests of THIS operation from the candidate and bind them.

    The bytes that are actually read are tied to the hashes the current input pins: a
    manifest or patch whose bytes differ from the pinned hash is refused, so the layer
    that is applied is provably the reviewed one. The manifest body, the patch bytes and
    the file preimages are then compared with each other, never a file with itself.
    """
    layers = []
    for name in layer_names:
        manifest_rel = f"patches/hermes/{name}-manifest.json"
        patch_rel = f"patches/hermes/{name}.patch"
        require(manifest_rel in project_files and patch_rel in project_files,
                "transaction_layer_not_pinned")
        manifest_bytes = owned_file(Path(candidate_root) / manifest_rel)
        patch_bytes = owned_file(Path(candidate_root) / patch_rel)
        require(digest(manifest_bytes) == project_files[manifest_rel],
                "transaction_layer_manifest_pin_changed:" + manifest_rel)
        require(digest(patch_bytes) == project_files[patch_rel],
                "transaction_layer_patch_pin_changed:" + patch_rel)
        body = json.loads(manifest_bytes)
        require(body.get("patch") == patch_rel, "transaction_layer_patch_reference_changed")
        require(body.get("patch_sha256") == digest(patch_bytes)
                == project_files[patch_rel],
                "transaction_layer_patch_bytes_changed")
        require(body.get("base_commit") == receipt.get("commit"),
                "transaction_layer_base_commit_changed")
        files = body.get("files")
        require(isinstance(files, list) and files, "transaction_layer_files_required")
        layers.append({"name": name, "manifest": manifest_rel, "patch": patch_rel,
                       "manifest_bytes": manifest_bytes, "patch_bytes": patch_bytes,
                       "manifest_sha256": digest(manifest_bytes),
                       "patch_sha256": digest(patch_bytes),
                       "body": body, "files": files})
    return layers


def check_preimages(layers, source, receipt_files):
    """The strict preimage chain inside the bundle.

    For every file the chain is: the receipt's hash for the first layer that touches the
    file, then the result hash of the preceding layer that touches it. The expected value
    is never replaced by the layer's own declaration: a mismatch is a refusal. A bundle
    that is already published is recognised by a separate check of its final bytes and
    its receipt, not by weakening this chain.
    """
    state = {}
    for layer in layers:
        for row in layer["files"]:
            path = row["path"]
            expected = state.get(path)
            if expected is None:
                current = receipt_files.get(path)
                expected = None if current is None else current["sha256"]
            require(row.get("before_sha256") == expected,
                    "transaction_layer_preimage_changed:" + path)
            require(row.get("new_file") is (expected is None),
                    "transaction_layer_new_file_flag_changed:" + path)
            if expected is None:
                require(not os.path.lexists(Path(source) / path),
                        "transaction_new_source_exists:" + path)
            state[path] = row["sha256"]
    return state


def layer_already_applied(layer, source):
    """True when the layer's result bytes are already in the tree.

    A repeated run must recognise the published state instead of refusing it: the patch
    would no longer apply because its preimage is gone, while the wanted bytes are there.
    """
    for row in layer["files"]:
        path = Path(source) / row["path"]
        if not path.exists():
            return False
        data = owned_file(path)
        if digest(data) != row["sha256"] or len(data) != row["bytes"]:
            return False
    return True


def bundle_already_applied(layers, source, receipt, request=None):
    """True when the bundle is already published as a whole.

    This is a separate check, not a relaxation of the preimage chain: the tree must hold
    the final byte of every file the bundle touches, and the receipt must already list
    every layer of the bundle with the layer's own manifest and patch hashes. A bundle
    that is only partly published is not recognised here.
    """
    installed = {row["manifest"]: row for row in receipt.get("layers", [])}
    # a layer whose manifest this operation publishes anew may still carry the previous
    # bytes in the receipt; that difference is closed by the publication itself
    republished = set(request.get("layer_manifest_updates", []))
    final = {}
    for layer in layers:
        row = installed.get(layer["manifest"])
        if row is None:
            return False
        if row.get("manifest_sha256") != layer["manifest_sha256"]:
            if layer["manifest"] not in republished:
                return False
        if row.get("patch_sha256") != layer["patch_sha256"]:
            return False
        for file_row in layer["files"]:
            final[file_row["path"]] = file_row["sha256"]
    for path, sha in final.items():
        live = Path(source) / path
        if not live.exists():
            return False
        data = owned_file(live)
        if digest(data) != sha:
            return False
    return True


def row_bytes(layers, path):
    """The byte count the LAST layer that touches a path declares for it.

    For layers that touch the same file the final byte count is the one of the last
    layer, which is the state the published tree holds.
    """
    count = None
    for layer in layers:
        for row in layer["files"]:
            if row["path"] == path:
                count = row["bytes"]
    return count


def apply_layers(layers, source, staging):
    """Apply the selected layers in order onto a private staging tree.

    The staging tree holds only the files the layers touch, seeded with the live bytes.
    Each layer sees the previous layer's output. A layer whose result bytes are already in
    the tree is recognised as applied and skipped.
    """
    touched = []
    for layer in layers:
        for row in layer["files"]:
            path = row["path"]
            if path not in touched:
                touched.append(path)
    for path in touched:
        target = Path(staging) / path
        private_parents(staging, path)
        data = owned_file(Path(source) / path)
        write_atomic(target, data, 0o600)
    for layer in layers:
        if layer_already_applied(layer, staging):
            # this layer's result bytes are already there: keep them and move on
            for row in layer["files"]:
                data = owned_file(Path(staging) / row["path"])
                require(digest(data) == row["sha256"],
                        "transaction_layer_output_changed:" + layer["name"])
            continue
        patch = Path(staging).parent / (layer["name"] + ".patch")
        write_atomic(patch, layer["patch_bytes"], 0o600)
        for checking in (True, False):
            command = ["git", "--no-optional-locks", "apply", "--whitespace=nowarn"]
            if checking:
                command.append("--check")
            command.append(str(patch))
            result = subprocess.run(command, cwd=str(staging), capture_output=True,
                                    text=True, timeout=120,
                                    env={"GIT_CEILING_DIRECTORIES": str(Path(staging).parent),
                                         "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                         "HOME": str(Path(staging).parent)})
            require(result.returncode == 0,
                    "transaction_layer_patch_does_not_apply:" + layer["name"])
        for row in layer["files"]:
            path = row["path"]
            data = owned_file(Path(staging) / path)
            require(digest(data) == row["sha256"] and len(data) == row["bytes"],
                    "transaction_layer_output_changed:" + layer["name"])
    return touched


# --------------------------------------------------------------------- composition


def proven_cache(source, receipt_files):
    """The generated artefacts of the tree that are not part of the receipt inventory.

    The product's own composition check refuses unknown entries; the generated bytecode
    caches are proven instead of removed, so no tree copy is needed.
    """
    generated = ('.hermes/', 'node_modules/', 'hermes_cli/web_dist/', 'ui-tui/dist/',
                 'ui-tui/node_modules/', 'web/node_modules/', 'apps/shared/node_modules/')
    # The generated products that may coexist with the source tree. The product's own
    # check accepts them by prefix; nothing is proven by digest here, so the tree is not
    # read entry by entry and not copied.
    proven = {}
    source = Path(source)
    for path in source.rglob("*"):
        name = str(path.relative_to(source))
        if path.is_dir() or path.is_symlink():
            continue
        if name in receipt_files or name.startswith(generated):
            continue
        if name == ".web_ui_build.lock":
            continue
        if name.endswith(".pyc") and "__pycache__/" in name:
            # the product's proven_cache contract expects private files; the ordinary
            # bytecode cache is a generated product, proven by the prefix rule instead
            continue
    return proven


def composition_checked(value, source, receipt, donor, cache, project_root):
    """The product's own composition check with a proven-cache list.

    The product's helper is imported from the project's own scripts directory, so the check
    is the product's check and not a re-implementation. The whole composition_checked is
    used, not only its source_checked part: the source lock, the overlay set, the manifest
    digests and the patch digests are checked together with the source inventory.
    """
    project_root = Path(project_root)
    scripts_path = str(project_root / "scripts")
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    # the product's scripts package must resolve to the candidate's own scripts directory
    import importlib
    import importlib.util
    package = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True))
    package.__path__ = [scripts_path]
    sys.modules["scripts"] = package
    from scripts.friday_install import composition_checked as product_composition_checked
    return product_composition_checked(value, Path(source), receipt, donor,
                                       proven_cache=cache)


# ------------------------------------------------------------------------- history


def history_map(home):
    """Digest map of the preserved transaction history."""
    actual = {}
    home = Path(home)
    for root in REQUIRED_HISTORY_ROOTS:
        base = home / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise Refused("transaction_history_link_refused")
            if path.is_dir():
                continue
            actual[str(path.relative_to(home))] = digest(read_bytes(path))
    return actual


# --------------------------------------------------------------------------- main


def run(request, request_path, request_sha256):
    global INJECT_AFTER_RENAME, INJECT_TARGET, INJECT_SNAPSHOT_DIR, INJECT_SNAPSHOT_FILES
    global INJECT_SNAPSHOT_HOME
    started = time.monotonic()
    os.umask(0o077)
    INJECT_AFTER_RENAME = bool(request.get("inject_after_rename"))
    INJECT_TARGET = request.get("inject_target")
    INJECT_SNAPSHOT_DIR = request.get("inject_snapshot_dir")
    INJECT_SNAPSHOT_FILES = tuple(request.get("inject_snapshot_files") or ())
    require(request.get("schema") in (SCHEMA, SCHEMA_EXPLICIT),
            "transaction_only_v45_supported")
    home = Path(request["home"]).resolve()
    if INJECT_SNAPSHOT_DIR is not None:
        snapshot = Path(INJECT_SNAPSHOT_DIR)
        require(snapshot.is_absolute() and not str(snapshot).startswith(str(home) + "/"),
                "transaction_injection_snapshot_outside_home")
    require(home.is_dir(), "transaction_home_missing")
    require(os.environ.get("HERMES_HOME") == str(home), "transaction_environment_required")
    # the snapshot reads from the VERIFIED home of this transaction
    INJECT_SNAPSHOT_HOME = home
    candidate = Path(request["candidate_project"]).resolve()
    require(candidate.is_dir(), "transaction_candidate_missing")
    seconds = request.get("seconds", 180)
    require(type(seconds) is int and seconds > 0,
            "transaction_seconds_positive_integer_required")
    deadline = started + seconds

    def forward_budget():
        # Only forward work is budgeted. An expired operation must still restore every
        # published beforeimage; Journal.restore calls publish directly, never this guard.
        require(time.monotonic() < deadline, "transaction_deadline_expired")

    # 1. the gateway must be stopped: one receiver, never two.
    bench_home = request.get("bench_home")
    require(not gateway_running(request["native_unit"]["path"], bench_home),
            "transaction_gateway_running")

    # 2. pins: every referenced byte must still be the pinned byte.
    for key in ("marker", "source_receipt", "stamp", "configuration", "profile", "launcher",
                "native_unit", "current_input", "previous_input", "predecessor_request", "target_receipt",
                "candidate_input"):
        ref = request.get(key)
        require(isinstance(ref, dict) and "path" in ref and "sha256" in ref,
                "transaction_pin_required:" + key)
        require(digest(read_bytes(ref["path"])) == ref["sha256"],
                "transaction_pin_changed:" + key)
    for key in ():
        ref = request.get(key)
        require(isinstance(ref, dict) and "path" in ref and "sha256" in ref,
                "transaction_pin_required:" + key)
        require(digest(read_bytes(ref["path"])) == ref["sha256"],
                "transaction_pin_changed:" + key)

    marker = read_json(request["marker"]["path"])
    receipt = read_json(request["source_receipt"]["path"])
    previous_input = read_json(request["previous_input"]["path"])
    require(marker.get("input_sha256") == request["previous_input"]["sha256"],
            "transaction_previous_input_not_installed")
    current_input = read_json(request["current_input"]["path"])
    predecessor = read_json(request["predecessor_request"]["path"])

    # 3. the predecessor is the committed successor operation of this home.
    require(predecessor.get("schema") == "frw.root.engineering152-successor-request.v1",
            "transaction_predecessor_identity_changed")
    require(predecessor.get("home") == str(home)
            or request.get("bench_home") == str(home),
            "transaction_predecessor_home_changed")
    require(predecessor.get("current_input", {}).get("sha256")
            == request["predecessor_current_input_sha256"],
            "transaction_predecessor_input_changed")
    predecessor_tx = home / "preparation" / ("ordinary-source-update-successor-"
                                             + request["predecessor_request"]["sha256"])
    if not (predecessor_tx / "committed.json").exists():
        # a bench predecessor is supplied directly by the request
        predecessor_tx = Path(request["predecessor_request"]["path"]).parent
    predecessor_committed_path = predecessor_tx / "committed.json"
    predecessor_committed_bytes = (predecessor_committed_path.read_bytes()
                                    if predecessor_committed_path.exists() else b"")
    committed = read_json(predecessor_tx / "committed.json")
    require(committed.get("state") == "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED"
            and committed.get("gateway_started") is False
            and committed.get("workers_enabled") is False,
            "transaction_predecessor_not_committed")
    # The predecessor's record pins the receipt IT produced and stays immutable. This
    # operation writes its own record and only links to that predecessor, so the
    # predecessor's historical result is never rewritten.
    require(committed.get("source_receipt_sha256") == request["predecessor_receipt_sha256"],
            "transaction_predecessor_not_committed")

    # 4. the history is preserved byte for byte.
    actual_history = history_map(home)
    require(actual_history == request["transaction_history"],
            "transaction_history_changed")

    # 5. the receipt is the installed one and the marker agrees with it.
    require(marker.get("completion_stage") == "TELEGRAM_ORDINARY"
            and marker.get("runtime_ready") is False
            and marker.get("worker_state") == "BOTH_WORKERS_PREPARATION_PENDING",
            "transaction_home_state_changed")
    require(marker.get("source_receipt_sha256") == request["source_receipt"]["sha256"],
            "transaction_marker_receipt_changed")
    require(len(receipt.get("layers", [])) == int(request["installed_layers"]),
            "transaction_installed_layers_changed")
    require(len(receipt.get("files", {})) == int(request["installed_files"]),
            "transaction_installed_files_changed")

    # 6. the project inventory: the candidate adds exactly the layer pairs of THIS
    #    operation and changes nothing else that the home does not already carry.
    # The bundle of this operation is a subset of the known layers. A layer that is already
    # published is named so only when it is republished; a live publication of a new layer
    # names just that one, so the already published layers are never replayed.
    # The composition of THIS operation is explicit: the field is REQUIRED. An absent,
    # empty, malformed or repeated set is refused instead of silently widening the
    # operation to every known layer. The historical four-layer request keeps its exact
    # meaning because the generator names exactly those four layers.
    layer_names = check_project_inventory(request, previous_input, current_input)
    current_files = current_input["project_files"]

    # 7. the selected layers: manifest bytes, patch bytes and preimages. The layers are read
    #    from the candidate and tied to the hashes the current input pins; their preimage
    #    chain is checked against the receipt before anything is staged.
    layers = read_layers(candidate, receipt, home, current_files, layer_names)
    source = home / "hermes-agent"
    already_published = bundle_already_applied(layers, source, receipt, request)
    if not already_published:
        final_state = check_preimages(layers, source, receipt["files"])
    else:
        # the bundle is already published as a whole, with a consistent receipt; the final
        # bytes are the authoritative ones and no layer is replayed
        final_state = {}
        for layer in layers:
            for row in layer["files"]:
                final_state[row["path"]] = row["sha256"]

    # Existing plugin replacements share the source transaction, so their beforeimages
    # must be known before staging or intent, as well as before the journal records them.
    check_plugin_preimages(request, previous_input, current_input, marker, home,
                           already_published=already_published)

    # 8. apply the layers onto a private staging tree that holds only the touched files.
    #    A bundle that is already published is NOT applied again: for layers that touch the
    #    same file the old patch would be applied to the final bytes and would not apply.
    #    Its final bytes and its receipt are checked instead.
    forward_budget()
    staging_root = private_directory(home / "preparation" /
                                     ("ordinary-source-update-v45-" + request_sha256[:16]))
    staging = private_directory(staging_root / "staging")
    if already_published:
        touched = []
        for layer in layers:
            for row in layer["files"]:
                if row["path"] not in touched:
                    touched.append(row["path"])
        for path in touched:
            data = owned_file(Path(source) / path)
            expected = row_bytes(layers, path)
            require(digest(data) == final_state[path]
                    and (expected is None or len(data) == expected),
                    "transaction_published_bytes_changed:" + path)
            write_atomic(Path(staging) / path, data, 0o600)
    else:
        touched = apply_layers(layers, source, staging)

    # 9. the composition after the publication: the receipt's inventory plus the new bytes.
    projected = json.loads(json.dumps(receipt))
    # A layer that is already in the receipt must not be appended a second time. When the
    # operation publishes the layer's manifest anew, the projected receipt must carry the
    # published manifest bytes, so the composition check compares the tree with itself.
    installed_manifests = {row["manifest"] for row in projected["layers"]}
    published_manifests = set(request.get("project_file_updates", [])) | set(
        request.get("layer_manifest_updates", []))
    for layer in layers:
        if layer["manifest"] in installed_manifests:
            if layer["manifest"] in published_manifests:
                for row in projected["layers"]:
                    if row["manifest"] == layer["manifest"]:
                        row["manifest_sha256"] = layer["manifest_sha256"]
            continue
        projected["layers"].append({"manifest": layer["manifest"],
                                    "manifest_sha256": layer["manifest_sha256"],
                                    "patch_sha256": layer["patch_sha256"]})
    # the projected receipt must pin the same source lock as the current input
    lock = current_input["sources_lock"]
    lock_path = lock["path"] if isinstance(lock, dict) else lock
    projected["sources_lock_sha256"] = (lock["sha256"] if isinstance(lock, dict)
                                        else digest(read_bytes(lock_path)))
    for path, sha in final_state.items():
        row = dict(projected["files"][path]) if path in projected["files"] else {}
        data = owned_file(Path(staging) / path)
        row.update({"sha256": sha, "bytes": len(data), "mode": "100644"})
        projected["files"][path] = row
    cache = proven_cache(source, receipt["files"])
    lock = current_input["sources_lock"]
    lock_path = lock["path"] if isinstance(lock, dict) else lock
    donor = read_json(lock_path)
    donor = {r["id"]: r for r in donor["repositories"]}["hermes"]
    # The staged bytes are proven against the projected inventory before publication.
    for path in touched:
        staged = owned_file(Path(staging) / path)
        require(digest(staged) == final_state[path], "transaction_staged_bytes_changed:" + path)

    # 10. the journal: every file the operation touches is recorded before it is written.
    journal = Journal(staging_root, home)
    published = []

    def publish_with_journal(target, data, mode=0o600):
        """Publish a file and remember what it was before.

        The beforeimage is taken from the journal's first recording of that path, so a file
        that is written more than once is restored to its state before the operation.
        """
        target = Path(target)
        key = str(target)
        if key not in journal.entries:
            if target.exists() and not target.is_symlink():
                journal.record_existing(target, owned_file(target))
            else:
                journal.record_absent(target)
        forward_budget()
        # The path is registered BEFORE the write: a failure between the rename and the
        # directory synchronisation leaves the file changed, and the rollback must still
        # know about it.
        published.append(target)
        publish(target, data, mode)

    for path in touched:
        journal.record_existing(Path(source) / path, owned_file(Path(source) / path))
    for name in sorted(request.get("plugin_set", [])) + sorted(request.get("plugin_additions", [])):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    for name in sorted(request.get("project_file_updates", [])):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    for name in ("hermes-agent.source.json", "FRIDAY-INSTALL.json", "hermes-agent/install-stamp.json"):
        target = Path(home) / name
        if target.exists() and not target.is_symlink():
            journal.record_existing(target, owned_file(target))
        else:
            journal.record_absent(target)
    forward_budget()
    journal.write_intent("intent.json", {
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATE_INTENT",
        "request_sha256": request_sha256,
        "home": str(home),
        "previous_input": request["previous_input"],
        "current_input": request["current_input"],
        "source_receipt": request["source_receipt"],
        "layers": [layer["manifest"] for layer in layers],
        "files": touched,
        "plugin_set": sorted(request.get("plugin_set", [])),
        "plugin_additions": sorted(request.get("plugin_additions", [])),
        "project_file_updates": sorted(request.get("project_file_updates", [])),
        "metadata": ["hermes-agent.source.json", "FRIDAY-INSTALL.json",
                     "hermes-agent/install-stamp.json"],
        "gateway_started": False,
        "workers_enabled": False,
    })

    try:
        # 10a. the source files of the layers
        for path in touched:
            data = owned_file(Path(staging) / path)
            publish_with_journal(Path(source) / path, data, 0o600)
        write_atomic(staging_root / "published.json", encoded({"files": [str(p) for p in published]}), 0o600)
        if request.get("fail_after_publish"):
            # a controlled failure at a substantial point of the state change, used to prove
            # the rollback. It is only reachable through an explicit request field.
            raise Refused("transaction_controlled_failure_for_rollback_proof")
        # The product's own composition check runs over the published tree: the receipt's
        # inventory plus the new bytes. A refusal here restores the beforeimages.
        composition_checked(current_input, source, projected, donor, cache, candidate)

        # 10b. the project files the transition deliberately updates, then the V3 plugin set.
    #      Both are proven against the current input's pins before they are written.
        # New selected patches were not carried by the installed project. Publish them
        # with their manifests through the same journal so the next operation can prove
        # the installed project's complete pinned composition.
        new_patches = {f"patches/hermes/{name}.patch" for name in layer_names
                       if f"patches/hermes/{name}.patch" not in previous_input["project_files"]}
        project_updates = sorted(set(request.get("project_file_updates", []))
                                 | set(request.get("layer_manifest_updates", []))
                                 | new_patches)
        plugin_set = sorted(request["plugin_set"])
        plugin_additions = sorted(request["plugin_additions"])
        for name in project_updates + plugin_set + plugin_additions:
            candidate_bytes = owned_file(Path(candidate) / name)
            require(digest(candidate_bytes) == current_files[name],
                    "transaction_candidate_bytes_changed:" + name)
        # files the request places at an explicit path inside the home (the staged native
        # runtime source, for example): the path is relative to the home and never escapes it
        staged_files = request.get("staged_files") or []
        for entry in staged_files:
            target = Path(home) / entry["path"]
            require(not Path(entry["path"]).is_absolute()
                    and '..' not in Path(entry["path"]).parts,
                    "transaction_staged_path_refused")
            candidate_bytes = owned_file(Path(candidate) / entry["source"])
            require(digest(candidate_bytes) == current_files[entry["source"]],
                    "transaction_candidate_bytes_changed:" + entry["source"])
            private_parents(home, entry["path"])
            publish_with_journal(target, candidate_bytes, 0o600)
        if staged_files:
            write_atomic(staging_root / "published-staged.json",
                         encoded({"files": [e["path"] for e in staged_files]}), 0o600)
        journal.write_intent("intent-project-updates.json", {
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATE_PROJECT_FILE_INTENT",
            "request_sha256": request_sha256,
            "files": project_updates,
        })
        for name in project_updates:
            data = owned_file(Path(candidate) / name)
            publish_with_journal(Path(home) / name, data, 0o600)
        write_atomic(staging_root / "published-project-updates.json",
                     encoded({"files": project_updates}), 0o600)

        journal.write_intent("intent-plugins.json", {
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATE_PLUGIN_INTENT",
            "request_sha256": request_sha256,
            "files": plugin_set + plugin_additions,
        })
        for name in plugin_set:
            data = owned_file(Path(candidate) / name)
            publish_with_journal(Path(home) / name, data, 0o600)
        if request.get("fail_during_plugins"):
            # a controlled failure in the middle of the plugin publication, used to prove that
            # the rollback covers the plugin set as well
            raise Refused("transaction_controlled_failure_during_plugins")
        for name in plugin_additions:
            data = owned_file(Path(candidate) / name)
            target = Path(home) / name
            private_parents(home, name)
            publish_with_journal(target, data, 0o600)
        write_atomic(staging_root / "published-plugins.json",
                     encoded({"files": plugin_set + plugin_additions}), 0o600)
        plugin_published = plugin_set + plugin_additions

        # 11. the new receipt and marker, published through the same journal.
        new_receipt = projected
        new_receipt["files"] = projected["files"]
        write_atomic(staging_root / "hermes-agent.source.json", encoded(new_receipt), 0o600)
        publish_with_journal(home / "hermes-agent.source.json", encoded(new_receipt), 0o600)
        if request.get("fail_between_metadata"):
            # a controlled failure between two metadata writes, used to prove that the rollback
            # covers the receipt, the marker and the stamp together
            raise Refused("transaction_controlled_failure_between_metadata")

        new_marker = dict(marker)
        # the marker's plugin inventory must follow the published plugin set
        plugin_pins = dict(marker.get("plugin_files", {}))
        for name in plugin_published:
            plugin_pins[name] = digest(owned_file(Path(home) / name))
        new_marker["plugin_files"] = plugin_pins
        receipt_sha = digest(encoded(new_receipt))
        new_marker["source_receipt_sha256"] = receipt_sha
        # the ordinary gateway phase pins the receipt: it must follow the published one,
        # exactly as the product's own source update does.
        phase = dict(new_marker.get("ordinary_gateway", {}))
        phase["source_receipt_sha256"] = receipt_sha
        phase["operator_entry"] = {
            "input": {"path": str(request["current_input"]["path"]),
                      "sha256": request["current_input"]["sha256"]},
            "script": {"path": str(candidate / "scripts/friday_native.py"),
                       "sha256": current_files["scripts/friday_native.py"]},
        }
        new_marker["ordinary_gateway"] = phase
        # the install stamp pins the layer list of the receipt
        stamp = read_json(Path(home) / "hermes-agent/install-stamp.json")
        stamp["fridaySource"] = {"baseTree": new_receipt["base_tree"], "layers": new_receipt["layers"]}
        stamp_data = encoded(stamp)
        write_atomic(staging_root / "install-stamp.json", stamp_data, 0o600)
        new_marker["input_sha256"] = request["current_input"]["sha256"]
        write_atomic(staging_root / "FRIDAY-INSTALL.json", encoded(new_marker), 0o600)
        publish_with_journal(home / "FRIDAY-INSTALL.json", encoded(new_marker), 0o600)
        publish_with_journal(Path(home) / "hermes-agent/install-stamp.json", stamp_data, 0o600)

        forward_budget()
        # This operation's own record; the predecessor's record is left untouched and
        # that is proved on the bytes, not on a claim.
        require(predecessor_committed_path.read_bytes() == predecessor_committed_bytes,
                "transaction_predecessor_record_changed")
        write_atomic(staging_root / "committed.json", encoded({
            "schema": "friday.ordinary-telegram-source-update-transaction.v1",
            "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
            "request_sha256": request_sha256,
            "previous_input": request["previous_input"],
            "current_input": request["current_input"],
            "predecessor_request_sha256": request["predecessor_request"]["sha256"],
            "predecessor_receipt_sha256": request["predecessor_receipt_sha256"],
            "source_receipt_sha256": digest(encoded(new_receipt)),
            "layers": [layer["manifest"] for layer in layers],
            "files": touched,
            "gateway_started": False,
            "workers_enabled": False,
            "seconds": round(time.monotonic() - started, 3),
        }), 0o600)
    except Exception:
        # One rollback for the whole operation: the source files, the project files, the
        # plugin set, the receipt, the marker and the stamp. Files that this operation
        # added are removed again.
        journal.restore(published)
        write_atomic(staging_root / "rolled-back.json", encoded({
            "state": "ROLLED_BACK",
            "published": [str(p) for p in published],
            "entries": sorted(journal.entries),
        }), 0o600)
        raise

    # 12. clean up the staging tree; the journal keeps the evidence.
    shutil.rmtree(staging, ignore_errors=True)
    for layer in layers:
        (staging_root / (layer["name"] + ".patch")).unlink(missing_ok=True)

    return {"state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
            "layers": len(layers), "files": len(touched),
            "receipt_sha256": digest(encoded(new_receipt)),
            "transaction": str(staging_root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    require(__import__("re").fullmatch("[0-9a-f]{64}", args.request_sha256),
            "transaction_request_digest_required")
    raw = read_bytes(args.request)
    require(digest(raw) == args.request_sha256, "transaction_request_changed")
    request = json.loads(raw)
    try:
        result = run(request, args.request, args.request_sha256)
    except StopUnconfirmed as exc:
        print(json.dumps({"state": "STOP_UNCONFIRMED", "exception": type(exc).__name__},
                         sort_keys=True), file=sys.stderr)
        raise SystemExit(3) from None
    except Refused as exc:
        print(json.dumps({"state": "REFUSED_NOT_RUNTIME_ACCEPTED",
                          "exception": type(exc).__name__, "reason": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2) from None
    except Exception as exc:
        # an unexpected failure: the home is unchanged by the rollback, and the refusal is
        # reported in the same shape as a planned one
        print(json.dumps({"state": "REFUSED_NOT_RUNTIME_ACCEPTED",
                          "exception": type(exc).__name__, "reason": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
