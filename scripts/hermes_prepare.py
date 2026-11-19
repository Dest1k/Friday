#!/usr/bin/env python3
"""Export the complete pinned Hermes source and apply the selected overlays.

This is the source-preparation step of installation, not runtime admission.
It never imports a donor module, installs dependencies or starts a service.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time


class Refused(RuntimeError):
    pass


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'FRIDAY_SOURCE_REFUSED reason=invalid_cli_arguments\n')


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    require(isinstance(value, str) and value and "\\" not in value
            and all(ord(char) >= 32 and ord(char) != 127 for char in value), "invalid_relative_path")
    path = PurePosixPath(value)
    require(path.parts and not path.is_absolute() and str(path) == value
            and all(part not in {"..", ".git"} for part in path.parts), "invalid_relative_path")
    return value


def regular(path):
    require(path.parent.resolve() == path.parent, "symlinked_input_parent")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), "regular_input_required")
        data = stream.read()
        after = os.fstat(stream.fileno())
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
    require(all(getattr(before, key) == getattr(after, key) for key in fields), "input_changed")
    return data, stat.S_IMODE(before.st_mode)


def unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def read_json(path):
    data, _ = regular(path)
    return json.loads(data, object_pairs_hook=unique_object), sha(data)


@dataclass
class Budget:
    deadline: float

    def remaining(self):
        value = self.deadline - time.monotonic()
        require(value > 0, "source_preparation_deadline")
        return value


def git(directory, args, budget, *, data=None):
    env = {"PATH": os.defpath, "LANG": "C.UTF-8", "GIT_OPTIONAL_LOCKS": "0",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_TERMINAL_PROMPT": "0", "GIT_CEILING_DIRECTORIES": str(directory.parent)}
    result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                             "-c", "core.hooksPath=" + os.devnull, "-C", str(directory), *args],
                            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, timeout=budget.remaining(), check=False)
    require(result.returncode == 0, "git_source_operation_failed")
    return result.stdout


def source_identity(repository, donor, budget):
    lock, lock_sha = read_json(repository / "sources.lock.json")
    matches = [row for row in lock["repositories"] if row["id"] == "hermes"]
    require(len(matches) == 1, "hermes_pin_required")
    source = matches[0]
    require(source["clone_url"] == "https://github.com/NousResearch/hermes-agent.git",
            "unexpected_donor_origin")
    for name in ("commit", "tree"):
        require(re.fullmatch(r"[0-9a-f]{40}", source[name]), "invalid_source_pin")
    require(donor.resolve() == donor and donor.is_dir(), "canonical_donor_required")
    for expr, expected in (("HEAD", source["commit"]), ("HEAD^{tree}", source["tree"])):
        require(git(donor, ["rev-parse", expr], budget).decode().strip() == expected,
                "donor_identity_changed")
    require(git(donor, ["remote", "get-url", "origin"], budget).decode().strip()
            == source["clone_url"], "unexpected_donor_origin")
    entries = {}
    for record in git(donor, ["ls-tree", "-rz", source["commit"]], budget).split(b"\0"):
        if not record:
            continue
        header, name = record.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        require(kind == "blob" and mode in {"100644", "100755"}, "unsupported_source_entry")
        entries[relative(name.decode("utf-8"))] = (mode, oid)
    require(entries, "empty_donor")
    index = {}
    for record in git(donor, ["ls-files", "--stage", "-z"], budget).split(b"\0"):
        if not record:
            continue
        header, name = record.split(b"\t", 1)
        mode, oid, stage = header.decode("ascii").split()
        path = relative(name.decode("utf-8"))
        require(stage == "0" and path not in index, "dirty_donor_refused")
        index[path] = (mode, oid)
    require(index == entries, "dirty_donor_refused")
    # `git status` refreshes the index through repository-local clean filters.
    # Read only index metadata and verify the working bytes ourselves instead.
    for name, (mode, oid) in entries.items():
        source_bytes(donor, name, mode, oid, budget)
    return source, lock_sha, entries


def overlay_digest(value, reason):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), reason)
    return value


def overlay_files(body):
    files = body.get("files")
    if files is None:
        legacy = body.get("expected_patched_files")
        require(isinstance(legacy, dict), "invalid_overlay_files")
        files = []
        for path, value in legacy.items():
            require(isinstance(value, dict) and value.get("path", path) == path,
                    "invalid_overlay_file")
            files.append(dict(value, path=path))
    else:
        require("expected_patched_files" not in body, "conflicting_overlay_file_formats")
    require(isinstance(files, list) and files, "invalid_overlay_files")
    expected = {}
    for value in files:
        require(isinstance(value, dict), "invalid_overlay_file")
        row = dict(value)
        path = relative(row.get("path"))
        require(path not in expected, "duplicate_overlay_file")
        overlay_digest(row.get("sha256"), "invalid_overlay_file")
        require(type(row.get("bytes")) is int and row["bytes"] >= 0, "invalid_overlay_size")
        if "mode" in row:
            require(isinstance(row["mode"], str) and row["mode"] in {"100644", "100755"}, "invalid_overlay_mode")
        if "before_sha256" in row and row["before_sha256"] is not None:
            overlay_digest(row["before_sha256"], "invalid_overlay_preimage")
        if "before_bytes" in row:
            require(type(row["before_bytes"]) is int and row["before_bytes"] >= 0,
                    "invalid_overlay_preimage")
        if "before_mode" in row:
            require(isinstance(row["before_mode"], str) and row["before_mode"] in {"100644", "100755"}, "invalid_overlay_mode")
        if "new_file" in row:
            require(type(row["new_file"]) is bool, "invalid_overlay_new_file")
            if row["new_file"]:
                require(row.get("before_sha256") is None, "conflicting_overlay_preimage")
                row["before_sha256"] = None
            else:
                require("before_sha256" not in row or row["before_sha256"] is not None,
                        "conflicting_overlay_preimage")
        expected[path] = row
    base = body.get("expected_base_files", {})
    require(isinstance(base, dict), "invalid_overlay_preimages")
    for path, pin in base.items():
        require(relative(path) in expected, "unlisted_overlay_input")
        row = expected[path]
        if pin is None:
            fields = {"before_sha256": None}
        else:
            require(isinstance(pin, dict), "invalid_overlay_preimage")
            fields = {"before_sha256": overlay_digest(pin.get("sha256"), "invalid_overlay_preimage")}
            if "bytes" in pin:
                require(type(pin["bytes"]) is int and pin["bytes"] >= 0,
                        "invalid_overlay_preimage")
                fields["before_bytes"] = pin["bytes"]
            if "mode" in pin:
                require(isinstance(pin["mode"], str) and pin["mode"] in {"100644", "100755"}, "invalid_overlay_mode")
                fields["before_mode"] = pin["mode"]
        for key, value in fields.items():
            require(key not in row or row[key] == value, "conflicting_overlay_preimage")
            row[key] = value
    for path, row in expected.items():
        require(not any(str(parent) in expected for parent in PurePosixPath(path).parents),
                "overlay_path_ancestry_conflict")
        if row.get("new_file") is True:
            require(row.get("before_sha256") is None, "conflicting_overlay_preimage")
        if row.get("new_file") is False:
            require("before_sha256" not in row or row["before_sha256"] is not None,
                    "conflicting_overlay_preimage")
        if "before_bytes" in row or "before_mode" in row:
            require(isinstance(row.get("before_sha256"), str), "conflicting_overlay_preimage")
    return expected


def check_overlay_inputs(destination, files):
    for path, row in files.items():
        if "before_sha256" not in row:
            continue  # Older manifests rely on Git's exact patch preimage check.
        target = destination / path
        if row["before_sha256"] is None:
            require(target.parent.resolve() == target.parent, "symlinked_input_parent")
            try:
                target.lstat()  # Includes directories and dangling symlinks.
            except FileNotFoundError:
                continue
            raise Refused("overlay_input_already_exists")
        data, mode = regular(target)
        require(sha(data) == row["before_sha256"], "overlay_input_changed")
        if "before_bytes" in row:
            require(len(data) == row["before_bytes"], "overlay_input_changed")
        if "before_mode" in row:
            require(("100755" if mode & 0o111 else "100644") == row["before_mode"],
                    "overlay_input_mode_changed")


def overlay_file_pins(items):
    pins = {}
    for name, digest in items:
        relative(name)
        require(PurePosixPath(name).parent == PurePosixPath("patches/hermes")
                and Path(name).suffix in {".json", ".patch"}, "invalid_overlay_selection_path")
        require(name not in pins, "duplicate_overlay_selection")
        pins[name] = overlay_digest(digest, "invalid_overlay_selection_hash")
    require(pins, "empty_overlay_selection")
    return pins


def select_overlays(layers, pins):
    selected = {}
    matched = set()
    for name, layer in layers.items():
        manifest = layer["manifest"]
        if manifest not in pins and name not in pins:
            continue
        require(pins.get(manifest) == layer["manifest_sha256"]
                and pins.get(name) == layer["patch_sha256"], "overlay_selection_pair_changed")
        selected[name] = layer
        matched.update((manifest, name))
    require(matched == set(pins), "unknown_overlay_selection")
    require(all(layer["requires"].keys() <= selected.keys() for layer in selected.values()),
            "selected_overlay_dependency_missing")
    return selected


def overlay_layers(repository, commit, budget, *, overlay_pins=None):
    require(overlay_pins is None or type(overlay_pins) is dict, "invalid_overlay_selection")
    folder = repository / "patches/hermes"
    layers = {}
    manifest_owners = {}
    for manifest in sorted(folder.glob("*.json")):
        body, digest = read_json(manifest)
        require(isinstance(body, dict), "invalid_overlay_manifest")
        require(body.get("base_commit") == commit, "overlay_base_mismatch")
        patch_name = body.get("patch")
        if patch_name is None:
            require(isinstance(body.get("patch_file"), str), "invalid_overlay_path")
            patch_name = "patches/hermes/" + body["patch_file"]
        elif "patch_file" in body:
            require(isinstance(body["patch_file"], str)
                    and patch_name == "patches/hermes/" + body["patch_file"],
                    "conflicting_overlay_path")
        relative(patch_name)
        require(PurePosixPath(patch_name).parent == PurePosixPath("patches/hermes"),
                "overlay_path_outside_bundle")
        patch, _ = regular(repository / patch_name)
        require(sha(patch) == overlay_digest(body.get("patch_sha256"), "invalid_overlay_hash"),
                "overlay_hash_mismatch")
        require(patch_name not in layers, "duplicate_overlay")
        expected = overlay_files(body)
        requires = {}
        if "prerequisite_patch" in body:
            path = relative(body["prerequisite_patch"])
            require(path.endswith(".patch"), "overlay_prerequisite_mismatch")
            requires[path] = overlay_digest(body.get("prerequisite_patch_sha256"),
                                            "invalid_overlay_prerequisite")
        prerequisites = body.get("prerequisites", {})
        require(isinstance(prerequisites, dict), "invalid_overlay_prerequisites")
        for name, pin in prerequisites.items():
            relative(name)
            path = relative(name if name.startswith("patches/hermes/") else "patches/hermes/" + name)
            overlay_digest(pin, "invalid_overlay_prerequisite")
            require(path not in requires or requires[path] == pin, "conflicting_overlay_prerequisite")
            requires[path] = pin
        require(all(PurePosixPath(path).parent == PurePosixPath("patches/hermes") for path in requires),
                "overlay_path_outside_bundle")
        # Git parses its own patch format; refuse unsupported operations before
        # any application, including deletion and non-regular file creation.
        summary = git(repository, ["apply", "--summary", "-"], budget, data=patch)
        for record in summary.splitlines():
            require(re.fullmatch(rb" (?:create mode (?:100644|100755) .+|create (?!mode(?: |$)).+|mode change (?:100644|100755) => (?:100644|100755) .+)", record),
                    "unsupported_patch_operation")
        changed = set()
        for record in git(repository, ["apply", "--numstat", "-z", "-"], budget, data=patch).split(b"\0"):
            if record:
                added, removed, path = record.decode().split("\t", 2)
                require(added.isdigit() and removed.isdigit(), "unsupported_patch_operation")
                path = relative(path)
                require(path not in changed, "duplicate_patch_file")
                changed.add(path)
        require(changed == set(expected), "overlay_file_inventory_mismatch")
        manifest_name = str(manifest.relative_to(repository))
        manifest_owners[manifest_name] = patch_name
        layers[patch_name] = {"manifest": manifest_name, "manifest_sha256": digest,
                             "patch_sha256": sha(patch), "patch": patch, "files": expected,
                             "requires": requires}
    require(set(layers) == {str(p.relative_to(repository)) for p in folder.glob("*.patch")},
            "unmanifested_overlay")
    paths = {path for layer in layers.values() for path in layer["files"]}
    require(not any(str(parent) in paths for path in paths for parent in PurePosixPath(path).parents),
            "overlay_path_ancestry_conflict")
    for value in layers.values():
        requires = {}
        for reference, pin in value["requires"].items():
            # Historical maps may name a manifest while pinning its owning patch.
            dependency = manifest_owners.get(reference, reference)
            parent = layers.get(dependency)
            require(parent is not None and parent["patch_sha256"] == pin,
                    "overlay_prerequisite_mismatch")
            requires[dependency] = pin
        value["requires"] = requires
    ordered = []
    while len(ordered) < len(layers):
        ready = sorted(key for key, value in layers.items()
                       if key not in ordered and set(value["requires"]) <= set(ordered))
        require(ready, "overlay_dependency_cycle")
        ordered.extend(ready)
    selected = layers if overlay_pins is None else select_overlays(
        layers, overlay_file_pins(overlay_pins.items()))
    return [(key, selected[key]) for key in ordered if key in selected]


def source_bytes(donor, name, mode, oid, budget):
    budget.remaining()
    data, actual_mode = regular(donor / name)
    require(bool(actual_mode & 0o111) == (mode == "100755"), "donor_mode_changed")
    def blob(value):
        return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
    if blob(data) != oid:
        # Only a declared CRLF checkout with the exact canonical Git blob can
        # differ; never invoke arbitrary clean filters or accept changed bytes.
        attrs = git(donor, ["check-attr", "-z", "eol", "--", name], budget).split(b"\0")
        canonical = data.replace(b"\r\n", b"\n")
        require(attrs[:3] == [name.encode(), b"eol", b"crlf"]
                and b"\n" not in data.replace(b"\r\n", b"") and blob(canonical) == oid,
                "donor_blob_changed")
        data = canonical
    budget.remaining()
    return data


def export_source(donor, destination, entries, budget):
    expected = {}
    for name, (mode, oid) in entries.items():
        data = source_bytes(donor, name, mode, oid, budget)
        target = destination / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        budget.remaining()
        with target.open("xb") as stream:
            stream.write(data)
        target.chmod(0o755 if mode == "100755" else 0o644)
        expected[name] = {"sha256": sha(data), "bytes": len(data), "mode": mode}
    return expected


def preparation_budget(seconds):
    require(type(seconds) in (int, float) and 0 < seconds <= 1800, "invalid_preparation_budget")
    return Budget(time.monotonic() + seconds)


def compose(repository, donor, destination, *, seconds=120, overlay_pins=None):
    return _compose(repository, donor, destination, preparation_budget(seconds), overlay_pins=overlay_pins)


def _compose(repository, donor, destination, budget, *, overlay_pins=None):
    repository, donor, destination = map(Path, (repository, donor, destination))
    require(repository.is_absolute() and repository.resolve() == repository, "canonical_bundle_required")
    require(destination.is_absolute() and destination.parent.resolve() == destination.parent,
            "canonical_destination_required")
    require(not destination.is_relative_to(donor), "destination_inside_donor")
    parent = destination.parent.stat()
    require(parent.st_uid == os.getuid() and stat.S_IMODE(parent.st_mode) == 0o700,
            "private_destination_parent_required")
    require(not destination.exists() and not destination.is_symlink(), "fresh_destination_required")
    source, lock_sha, entries = source_identity(repository, donor, budget)
    layers = overlay_layers(repository, source["commit"], budget, overlay_pins=overlay_pins)
    budget.remaining()
    destination.mkdir(mode=0o700)  # exclusive; failures retain the partial tree
    expected = export_source(donor, destination, entries, budget)
    applied = []
    for name, layer in layers:
        check_overlay_inputs(destination, layer["files"])
        git(destination, ["apply", "--check", "--whitespace=nowarn", "-"], budget, data=layer["patch"])
        git(destination, ["apply", "--whitespace=nowarn", "-"], budget, data=layer["patch"])
        for path, row in layer["files"].items():
            data, mode = regular(destination / path)
            require(sha(data) == row["sha256"] and len(data) == row["bytes"], "overlay_output_mismatch")
            git_mode = "100755" if mode & 0o111 else "100644"
            require(row.get("mode", git_mode) == git_mode, "overlay_mode_mismatch")
            expected[path] = {"sha256": sha(data), "bytes": len(data), "mode": git_mode}
        applied.append({key: layer[key] for key in ("manifest", "manifest_sha256", "patch_sha256")})
    actual = {str(p.relative_to(destination)) for p in destination.rglob("*") if not p.is_dir()}
    require(actual == set(expected), "composed_inventory_mismatch")
    for name, pin in expected.items():
        budget.remaining()
        data, mode = regular(destination / name)
        require(sha(data) == pin["sha256"] and len(data) == pin["bytes"]
                and bool(mode & 0o111) == (pin["mode"] == "100755"), "composed_file_changed")
    budget.remaining()
    return {"schema": "friday.hermes-source.v1", "status": "SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED",
            "commit": source["commit"], "base_tree": source["tree"], "sources_lock_sha256": lock_sha,
            "source_file_count": len(entries), "layers": applied, "files": expected,
            "dependencies_installed": False, "services_started": False}


def main():
    parser = SafeParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--seconds", default=120, type=int)
    parser.add_argument("--overlay-file", nargs=2, action="append", metavar=("PATH", "SHA256"),
                        help="Pin each selected manifest and its owning patch. Default: all overlays.")
    args = parser.parse_args()
    os.umask(0o077)
    budget = preparation_budget(args.seconds)
    receipt = args.destination.with_name(args.destination.name + ".source.json")
    require(not receipt.exists() and not receipt.is_symlink(), "fresh_receipt_required")
    pins = overlay_file_pins(args.overlay_file) if args.overlay_file is not None else None
    result = _compose(args.repository, args.donor, args.destination, budget, overlay_pins=pins)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    budget.remaining()
    with receipt.open("x") as stream:
        stream.write(serialized)
        stream.flush()
        os.fsync(stream.fileno())
    success = json.dumps({"status": result["status"], "receipt": str(receipt),
                          "files": len(result["files"]), "overlays": len(result["layers"])})
    budget.remaining()
    print(success)


if __name__ == "__main__":
    try:
        main()
    except Refused as exc:
        # Reasons originate in this checked source; never print a Git exception,
        # argv, traceback, environment or path supplied by an operator.
        reason = str(exc)
        if not re.fullmatch('[a-z_]{1,100}', reason):
            reason = 'source_refused'
        print('FRIDAY_SOURCE_REFUSED reason=' + reason, file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print('FRIDAY_SOURCE_REFUSED reason=source_preparation_deadline', file=sys.stderr)
        sys.exit(2)
    except (OSError, ValueError, KeyError, TypeError):
        print('FRIDAY_SOURCE_REFUSED reason=source_input_or_io_failed', file=sys.stderr)
        sys.exit(2)
