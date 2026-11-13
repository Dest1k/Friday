#!/usr/bin/env python3
"""Build the request for the V3 layer publication onto the serving ordinary home.

The generator and the validator agree on the field set: this file produces exactly the
keys that friday_v3_layer_publication.py requires, and every pin is taken from live bytes.

The composition of THIS operation is carried EXPLICITLY in the request field
`layer_names`, and the request uses the explicit-composition schema v46. The validator
requires that field and refuses an absent, empty, malformed or repeated set instead of
widening the operation to every known layer. Without --layer the historical four-layer
composition is preserved. New operations use --layer NAME (repeat for a composed
increment), plus explicit candidate/input/output paths. Explicit increments refuse layers
already in the installed receipt and preflight against the actual publication consumer.

Example (request preparation only; the gateway need not be stopped):
    python3 -I -B SCRIPT --layer bounded-current-ask-identity \
        --candidate-project CANDIDATE --previous-input INSTALLED-INPUT.json \
        --current-input NEW-INPUT.json --output NEW-REQUEST.json
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
CANDIDATE = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/project")
REPO = Path("/home/jericho/jericho/Friday_rework")
UNIT = Path("/home/jericho/.config/systemd/user/hermes-gateway-1b7e7667.service")
OUT = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108/REQUEST-LAYERS.json")
# Backward-compatible default for the historical operation. New increments select
# their own exact composition with --layer; this tuple never grows with known layers.
LAYER_NAMES = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {"path": str(path), "sha256": sha(path)}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


_CONSUMER = None


def publication():
    global _CONSUMER
    if _CONSUMER is not None:
        return _CONSUMER
    path = Path(__file__).resolve().with_name("friday_v3_layer_publication.py")
    spec = importlib.util.spec_from_file_location("friday_v3_request_consumer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _CONSUMER = module
    return module


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--layer", action="append", choices=publication().LAYER_NAMES,
                        help="layer of this increment; repeat in application order")
    parser.add_argument("--home", type=Path, default=HOME)
    parser.add_argument("--candidate-project", type=Path, default=CANDIDATE)
    parser.add_argument("--native-unit", type=Path, default=UNIT)
    parser.add_argument("--previous-input", type=Path,
                        help="exact input pinned by the installed marker")
    parser.add_argument("--current-input", type=Path)
    parser.add_argument("--current-source-project-update", type=Path,
                        help="exact committed v6 root request for the bounded native continuation")
    parser.add_argument("--current-source-native-predecessor", type=Path,
                        help="exact canonical committed CP199, CP200, CP201, CP202, CP203, CP204 CP205, CP206, CP207, CP208, CP209 or CP210 request for the bounded next edge")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=int, default=180)
    args = parser.parse_args(argv)
    if args.layer is not None and len(set(args.layer)) != len(args.layer):
        parser.error("--layer names must not repeat")
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    if args.current_source_project_update is not None and args.layer is None:
        parser.error("--current-source-project-update requires an explicit --layer")
    if args.current_source_native_predecessor is not None and args.current_source_project_update is None:
        parser.error("--current-source-native-predecessor requires --current-source-project-update")
    args.layer_names = tuple(args.layer) if args.layer is not None else LAYER_NAMES
    args.home = args.home.resolve()
    args.candidate_project = args.candidate_project.resolve()
    args.native_unit = args.native_unit.resolve()
    base = args.candidate_project.parent
    args.previous_input = (args.previous_input or base / "INPUT-PREVIOUS-RECONSTRUCTED.json").resolve()
    args.current_input = (args.current_input or base / "INPUT-LAYERS.json").resolve()
    args.output = (args.output or base / "REQUEST-LAYERS.json").resolve()
    if args.current_source_project_update is not None:
        args.current_source_project_update = args.current_source_project_update.resolve()
    if args.current_source_native_predecessor is not None:
        args.current_source_native_predecessor = args.current_source_native_predecessor.resolve()
    return args


def build_request(args):
    home, candidate = args.home, args.candidate_project
    marker = json.loads((home / "FRIDAY-INSTALL.json").read_text())
    receipt = json.loads((home / "hermes-agent.source.json").read_text())
    # The installed marker identifies the immutable committed successor journal. Later
    # layer publications link to it without rewriting its request or committed receipt.
    predecessor_tx = home / "preparation" / (
        "ordinary-source-update-successor-"
        + marker["ordinary_source_update_request"]["sha256"])
    predecessor = json.loads((predecessor_tx / "request.json").read_text())
    previous_input = pin(args.previous_input)
    current_input = pin(args.current_input)
    previous = json.loads(args.previous_input.read_text())
    current = json.loads(args.current_input.read_text())
    consumer = publication()
    consumer.require(marker.get("input_sha256") == previous_input["sha256"],
                     "transaction_previous_input_not_installed")
    if args.layer is not None:
        installed = {row["manifest"] for row in receipt["layers"]}
        consumer.require(not any(f"patches/hermes/{name}-manifest.json" in installed
                                 for name in args.layer_names),
                         "transaction_increment_layer_already_installed")

    history = {}
    for root in ("preparation/ordinary-gateway", "preparation/ordinary-gateway-archive"):
        base = home / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.is_symlink():
                continue
            history[str(path.relative_to(home))] = sha(path)

    request = {
        # The explicit-composition schema: the composition of this operation is declared
        # in `layer_names` and never inferred.
        "schema": "friday.ordinary-telegram-source-update.v46",
        "seconds": args.seconds,
        "home": str(home),
        "candidate_project": str(candidate),
        # The composition of THIS operation, declared explicitly. The validator requires
        # this field and refuses an absent, empty, malformed or repeated set.
        "layer_names": list(args.layer_names),
        "marker": pin(home / "FRIDAY-INSTALL.json"),
        "source_receipt": pin(home / "hermes-agent.source.json"),
        "stamp": pin(home / "hermes-agent/install-stamp.json"),
        "configuration": pin(home / "config.yaml"),
        "profile": pin(home / "FRIDAY-PROFILE.json"),
        "launcher": pin(home / "hermes-agent/.hermes/bin/hermes"),
        "native_unit": pin(args.native_unit),
        "previous_input": previous_input,
        "current_input": current_input,
        "predecessor_request": pin(predecessor_tx / "request.json"),
        "predecessor_current_input_sha256": predecessor["current_input"]["sha256"],
        "predecessor_receipt_sha256": json.loads(
            (predecessor_tx / "committed.json").read_text())["source_receipt_sha256"],
        "target_receipt": pin(home / "hermes-agent.source.json"),
        "candidate_input": current_input,
        "project_inventory": current["project_files"],
        "project_inventory_sha256": hashlib.sha256(encoded(current["project_files"])).hexdigest(),
        "plugin_set": sorted(n for n in previous["project_files"]
                             if n.startswith("plugins/friday_rework/")
                             and current["project_files"].get(n) != previous["project_files"][n]),
        "plugin_additions": sorted(n for n in current["project_files"]
                                   if n.startswith("plugins/friday_rework/")
                                   and n not in previous["project_files"]),
        "project_file_updates": sorted(n for n in previous["project_files"]
                                       if not n.startswith("plugins/friday_rework/")
                                       and current["project_files"].get(n) != previous["project_files"][n]),
        "staged_files": [
            {"path": "worker-runtime-source/" + n, "source": n}
            for n in ("scripts/a0_runtime.py", "scripts/rootless_docker_launch.py",
                      "scripts/friday-rework-docker.service",
                      "plugins/friday_rework/adapters/a0_profile.py",
                      "plugins/friday_rework/adapters/a0_web.py")
            if n in current["project_files"]
            and (args.layer is None or current["project_files"][n]
                 != previous["project_files"].get(n))],
        "layer_manifest_updates": sorted(n for n in current["project_files"]
                                        if n.startswith("patches/hermes/")
                                        and n.endswith("-manifest.json")
                                        and n not in previous["project_files"]),
        "installed_layers": len(receipt["layers"]),
        "installed_files": len(receipt["files"]),
        "transaction_history": history,
    }
    if getattr(args, "current_source_project_update", None) is not None:
        request["current_source_successor"] = {
            "schema": "friday.current-source-native-successor.v1",
            "root_project_update": pin(args.current_source_project_update),
        }
        if getattr(args, "current_source_native_predecessor", None) is not None:
            predecessor_context = consumer.json.loads(
                consumer.owned_file(args.current_source_native_predecessor)).get("current_source_successor")
            supported = {
                "friday.current-source-native-successor.v1": "friday.current-source-native-successor.v2",
                "friday.current-source-native-successor.v2": "friday.current-source-native-successor.v3",
                "friday.current-source-native-successor.v3": "friday.current-source-native-successor.v4",
                "friday.current-source-native-successor.v4": "friday.current-source-native-successor.v5",
                "friday.current-source-native-successor.v5": "friday.current-source-native-successor.v6",
                "friday.current-source-native-successor.v6": "friday.current-source-native-successor.v7",
                "friday.current-source-native-successor.v7": "friday.current-source-native-successor.v8",
                "friday.current-source-native-successor.v8": "friday.current-source-native-successor.v9",
                "friday.current-source-native-successor.v9": "friday.current-source-native-successor.v10",
                "friday.current-source-native-successor.v10": "friday.current-source-native-successor.v11",
                "friday.current-source-native-successor.v11": "friday.current-source-native-successor.v12",
                "friday.current-source-native-successor.v12": "friday.current-source-native-successor.v13",
            }
            previous_schema = predecessor_context.get("schema") if type(predecessor_context) is dict else None
            consumer.require(previous_schema in supported,
                             "transaction_current_source_supported_predecessor_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v2"
                             or args.layer_names == ("retained-calc-xlsx-destination-after-source200",),
                             "transaction_current_source_exact_third_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v3"
                             or args.layer_names == ("rtf-rich-odp-followup-and-office-bank-after-source201",),
                             "transaction_current_source_exact_fourth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v4"
                             or args.layer_names == ("core-file-readability-and-context-provenance-after-source202",),
                             "transaction_current_source_exact_fifth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v5"
                             or args.layer_names == ("rtf-optional-footnote-reader-after-source203",),
                             "transaction_current_source_exact_sixth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v6"
                             or args.layer_names == ("core-user-result-contracts-after-source204",),
                             "transaction_current_source_exact_seventh_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v7"
                             or args.layer_names == ("f06-protected-office-profiles-after-source205",),
                             "transaction_current_source_exact_eighth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v8"
                             or args.layer_names == ("f06-modern-odt-authenticated-profile-after-source206",),
                             "transaction_current_source_exact_ninth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v9"
                             or args.layer_names == ("inbound-turn-log-metadata-after-source207",),
                             "transaction_current_source_exact_tenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v10"
                             or args.layer_names == ("f07-bounded-docx-structure-after-source208",),
                             "transaction_current_source_exact_eleventh_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v11"
                             or args.layer_names == ("f07-malformed-docx-error-provenance-after-source209",),
                             "transaction_current_source_exact_twelfth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v12"
                             or args.layer_names == ("r02-telegram-text-uncertain-recovery-after-source210",),
                             "transaction_current_source_exact_thirteenth_layer_required")
            request["current_source_successor"].update({
                "schema": supported[previous_schema],
                "previous_native_update": pin(args.current_source_native_predecessor),
            })
    consumer.require_current_source_context(home, request)
    # Run the actual consumer's source preflight before issuing a request. This does not
    # stage, publish, stop services, or change the installed home.
    names = consumer.check_project_inventory(request, previous, current)
    layers = consumer.read_layers(candidate, receipt, home, current["project_files"], names)
    if not consumer.bundle_already_applied(layers, home / "hermes-agent", receipt, request):
        consumer.check_preimages(layers, home / "hermes-agent", receipt["files"])
    if "current_source_successor" in request:
        consumer.current_source_consumer_checked(current, request, candidate)
    return request


def main(argv=None):
    args = parse_args(argv)
    request = build_request(args)
    raw = encoded(request)
    args.output.write_bytes(raw)
    os.chmod(args.output, 0o600)
    print(json.dumps({"request": str(args.output), "bytes": len(raw), "sha256": sha(args.output),
                      "history_entries": len(request["transaction_history"]),
                      "layers": request["installed_layers"],
                      "layer_names": request["layer_names"],
                      "project_files": len(request["project_inventory"])}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except publication().Refused as exc:
        raise SystemExit(str(exc)) from None
