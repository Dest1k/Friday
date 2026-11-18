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


CURRENT_SOURCE_TWENTY_FOURTH_LAYER = 'ods-xlsx-native-visibility-compare-after-source221'
# The selected v25 identity is fixed; its bytes remain UNBOUND in the consumer.
CURRENT_SOURCE_TWENTY_FIFTH_LAYER = 'ordinary-f04-owned-ingress-stop-terminal-after-source222'
CURRENT_SOURCE_TWENTY_SIXTH_LAYER = 'presentation-final-native-guidance-after-source223'
CURRENT_SOURCE_TWENTY_SEVENTH_LAYER = 'docx-located-mainstory-after-source224'
CURRENT_SOURCE_TWENTY_EIGHTH_LAYER = 'docx-required-stored-stories-after-source225'
CURRENT_SOURCE_TWENTY_NINTH_LAYER = 'core-communication-memory-after-source226'
CURRENT_SOURCE_THIRTIETH_LAYER = 'word-output-visibility-after-source227'
CURRENT_SOURCE_THIRTY_FIRST_LAYER = 'document-preserving-edit-current-anchor-after-source228'
CURRENT_SOURCE_THIRTY_SECOND_LAYER = 'communication-create-read-after-source229'
CURRENT_SOURCE_THIRTY_THIRD_LAYER = 'core-document-final-guidance-after-source230'
CURRENT_SOURCE_THIRTY_FOURTH_LAYER = 'delimited-explicit-locale-import-after-source231'
CURRENT_SOURCE_THIRTY_FIFTH_LAYER = 'keyed-merge-provenance-guidance-after-source232'
CURRENT_SOURCE_THIRTY_SIXTH_LAYER = 'zip-member-read-guidance-after-source233'
CURRENT_SOURCE_THIRTY_SEVENTH_LAYER = 'bounded-compaction-protected-rows-after-source234'
CURRENT_SOURCE_THIRTY_EIGHTH_LAYER = 'delimited-conversion-guidance-after-source235'
CURRENT_SOURCE_THIRTY_NINTH_LAYER = 'xlsx-recalc-truth-after-source236'
CURRENT_SOURCE_FORTIETH_LAYER = 'ordinary-document-reliability-after-source237'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path, raw=None):
    digest = sha(path) if raw is None else hashlib.sha256(raw).hexdigest()
    return {"path": str(path), "sha256": digest}


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
                        help="exact canonical committed CP199 through CP241 request for the bounded next edge")
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
    consumer = publication()
    forty_fourth_layer = consumer.CURRENT_SOURCE_FORTY_FOURTH_LAYER
    consumer.require_forty_fourth_source_binding(args.layer_names)
    forty_fourth = forty_fourth_layer in args.layer_names
    if forty_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_third_predecessor_required")
        predecessor_ref = consumer.forty_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_fourth_layer}-manifest.json",
                         f"patches/hermes/{forty_fourth_layer}.patch")
        }
        consumer.require_forty_fourth_source_binding(args.layer_names, source_pins)
    forty_third_layer = consumer.CURRENT_SOURCE_FORTY_THIRD_LAYER
    consumer.require_forty_third_source_binding(args.layer_names)
    forty_third = forty_third_layer in args.layer_names
    if forty_third:
        consumer.require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_second_predecessor_required")
        predecessor_ref = consumer.forty_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_third_layer}-manifest.json",
                         f"patches/hermes/{forty_third_layer}.patch")
        }
        consumer.require_forty_third_source_binding(args.layer_names, source_pins)
    forty_second_layer = consumer.CURRENT_SOURCE_FORTY_SECOND_LAYER
    consumer.require_forty_second_source_binding(args.layer_names)
    if forty_second_layer in args.layer_names:
        consumer.require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_first_predecessor_required")
        manifest = f"patches/hermes/{forty_second_layer}-manifest.json"
        patch = f"patches/hermes/{forty_second_layer}.patch"
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (manifest, patch)
        }
        consumer.require_forty_second_source_binding(args.layer_names, source_pins)
    forty_first_layer = consumer.CURRENT_SOURCE_FORTY_FIRST_LAYER
    consumer.require_forty_first_source_binding(args.layer_names)
    if forty_first_layer in args.layer_names:
        consumer.require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fortieth_predecessor_required")
    # The explicit after223 draft must also refuse before installed-home access.
    publication().require_fortieth_source_binding(args.layer_names)
    if CURRENT_SOURCE_FORTIETH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_ninth_predecessor_required")
    publication().require_thirty_ninth_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_NINTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_eighth_predecessor_required")
    publication().require_thirty_eighth_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_EIGHTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_seventh_predecessor_required")
    publication().require_thirty_seventh_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_SEVENTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_sixth_predecessor_required")
    publication().require_thirty_sixth_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_SIXTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_fifth_predecessor_required")
    publication().require_thirty_fifth_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_FIFTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_fourth_predecessor_required")
    publication().require_thirty_fourth_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_FOURTH_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_third_predecessor_required")
    publication().require_thirty_third_source_binding(args.layer_names)
    if CURRENT_SOURCE_THIRTY_THIRD_LAYER in args.layer_names:
        publication().require(
            getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_thirty_second_predecessor_required")
    publication().require_thirty_second_source_binding(args.layer_names)
    publication().require_thirty_first_source_binding(args.layer_names)
    publication().require_thirtieth_source_binding(args.layer_names)
    publication().require_twenty_ninth_source_binding(args.layer_names)
    publication().require_twenty_eighth_source_binding(args.layer_names)
    publication().require_twenty_seventh_source_binding(args.layer_names)
    publication().require_twenty_sixth_source_binding(args.layer_names)
    # Draft v25 bytes must be frozen before even reading the installed home.
    publication().require_twenty_fifth_source_binding(args.layer_names)
    home, candidate = args.home, args.candidate_project
    marker_path = home / "FRIDAY-INSTALL.json"
    bound_current = forty_third or forty_fourth
    if forty_fourth:
        receipt_path = home / "hermes-agent.source.json"
        receipt_raw = consumer.owned_file(receipt_path)
        receipt_ref = pin(receipt_path, receipt_raw)
        consumer.require(receipt_ref["sha256"] == consumer.CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_RECEIPT_SHA256,
                         "transaction_current_source_forty_fourth_previous_receipt_changed")
        receipt = json.loads(receipt_raw)
        marker_raw = consumer.owned_file(marker_path)
        marker_ref = pin(marker_path, marker_raw)
        consumer.require(marker_ref["sha256"] == consumer.CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_MARKER_SHA256,
                         "transaction_current_source_forty_fourth_previous_marker_changed")
        marker = json.loads(marker_raw)
        stamp_path = home / "hermes-agent/install-stamp.json"
        stamp_ref = pin(stamp_path, consumer.owned_file(stamp_path))
        consumer.require(stamp_ref["sha256"] == consumer.CURRENT_SOURCE_FORTY_FOURTH_PREVIOUS_STAMP_SHA256,
                         "transaction_current_source_forty_fourth_previous_stamp_changed")
    elif forty_third:
        receipt = consumer.read_forty_third_previous_receipt(home)
        receipt_ref = {"path": str(home / "hermes-agent.source.json"),
                       "sha256": consumer.CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_RECEIPT_SHA256}
        marker_raw = consumer.owned_file(marker_path)
        marker_ref = pin(marker_path, marker_raw)
        consumer.require(marker_ref["sha256"] == consumer.CURRENT_SOURCE_FORTY_THIRD_PREVIOUS_MARKER_SHA256,
                         "transaction_current_source_forty_third_previous_marker_changed")
        marker = json.loads(marker_raw)
    else:
        marker = json.loads(marker_path.read_text())
        receipt = json.loads((home / "hermes-agent.source.json").read_text())
    # The installed marker identifies the immutable committed successor journal. Later
    # layer publications link to it without rewriting its request or committed receipt.
    predecessor_tx = home / "preparation" / (
        "ordinary-source-update-successor-"
        + marker["ordinary_source_update_request"]["sha256"])
    predecessor = json.loads((predecessor_tx / "request.json").read_text())
    previous_raw = consumer.owned_file(args.previous_input) if bound_current else None
    current_raw = consumer.owned_file(args.current_input) if bound_current else None
    previous_input = pin(args.previous_input, previous_raw)
    current_input = pin(args.current_input, current_raw)
    previous = json.loads(previous_raw if bound_current else args.previous_input.read_text())
    current = json.loads(current_raw if bound_current else args.current_input.read_text())
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
        "marker": marker_ref if bound_current else pin(marker_path),
        "source_receipt": receipt_ref if bound_current else pin(home / "hermes-agent.source.json"),
        "stamp": stamp_ref if forty_fourth else pin(home / "hermes-agent/install-stamp.json"),
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
        "target_receipt": receipt_ref.copy() if bound_current else pin(home / "hermes-agent.source.json"),
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
            predecessor_raw = consumer.owned_file(args.current_source_native_predecessor)
            if forty_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_fourth_previous_request_changed")
            elif forty_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_third_previous_request_changed")
            predecessor_request = consumer.json.loads(predecessor_raw)
            consumer.require(type(predecessor_request) is dict,
                             "transaction_current_source_supported_predecessor_required")
            predecessor_context = predecessor_request.get("current_source_successor")
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
                "friday.current-source-native-successor.v13": "friday.current-source-native-successor.v14",
                "friday.current-source-native-successor.v14": "friday.current-source-native-successor.v15",
                "friday.current-source-native-successor.v15": "friday.current-source-native-successor.v16",
                "friday.current-source-native-successor.v16": "friday.current-source-native-successor.v17",
                "friday.current-source-native-successor.v17": "friday.current-source-native-successor.v18",
                "friday.current-source-native-successor.v18": "friday.current-source-native-successor.v19",
                "friday.current-source-native-successor.v19": "friday.current-source-native-successor.v20",
                "friday.current-source-native-successor.v20": "friday.current-source-native-successor.v21",
                "friday.current-source-native-successor.v21": "friday.current-source-native-successor.v22",
                "friday.current-source-native-successor.v22": "friday.current-source-native-successor.v23",
                "friday.current-source-native-successor.v23": "friday.current-source-native-successor.v24",
                "friday.current-source-native-successor.v24": "friday.current-source-native-successor.v25",
                "friday.current-source-native-successor.v25": "friday.current-source-native-successor.v26",
                "friday.current-source-native-successor.v26": "friday.current-source-native-successor.v27",
                "friday.current-source-native-successor.v27": "friday.current-source-native-successor.v28",
                "friday.current-source-native-successor.v28": "friday.current-source-native-successor.v29",
                "friday.current-source-native-successor.v29": "friday.current-source-native-successor.v30",
                "friday.current-source-native-successor.v30": "friday.current-source-native-successor.v31",
                "friday.current-source-native-successor.v31": "friday.current-source-native-successor.v32",
                "friday.current-source-native-successor.v32": "friday.current-source-native-successor.v33",
                "friday.current-source-native-successor.v33": "friday.current-source-native-successor.v34",
                "friday.current-source-native-successor.v34": "friday.current-source-native-successor.v35",
                "friday.current-source-native-successor.v35": "friday.current-source-native-successor.v36",
                "friday.current-source-native-successor.v36": "friday.current-source-native-successor.v37",
                "friday.current-source-native-successor.v37": "friday.current-source-native-successor.v38",
                "friday.current-source-native-successor.v38": "friday.current-source-native-successor.v39",
                "friday.current-source-native-successor.v39": "friday.current-source-native-successor.v40",
                "friday.current-source-native-successor.v40": consumer.CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA,
                "friday.current-source-native-successor.v41": consumer.CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA,
            }
            previous_schema = predecessor_context.get("schema") if type(predecessor_context) is dict else None
            consumer.require(type(previous_schema) is str and previous_schema in supported,
                             "transaction_current_source_supported_predecessor_required")
            consumer.require(forty_fourth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_fourth_edge_required")
            consumer.require(forty_third == (previous_schema == consumer.CURRENT_SOURCE_FORTY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_third_edge_required")
            consumer.require(forty_second_layer not in args.layer_names
                             or previous_schema == consumer.CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA,
                             "transaction_current_source_forty_first_predecessor_required")
            consumer.require(forty_first_layer not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v40",
                             "transaction_current_source_fortieth_predecessor_required")
            consumer.require(CURRENT_SOURCE_FORTIETH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v39",
                             "transaction_current_source_thirty_ninth_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_NINTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v38",
                             "transaction_current_source_thirty_eighth_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_EIGHTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v37",
                             "transaction_current_source_thirty_seventh_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_SEVENTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v36",
                             "transaction_current_source_thirty_sixth_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_SIXTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v35",
                             "transaction_current_source_thirty_fifth_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_FIFTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v34",
                             "transaction_current_source_thirty_fourth_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_FOURTH_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v33",
                             "transaction_current_source_thirty_third_predecessor_required")
            consumer.require(CURRENT_SOURCE_THIRTY_THIRD_LAYER not in args.layer_names
                             or previous_schema == "friday.current-source-native-successor.v32",
                             "transaction_current_source_thirty_second_predecessor_required")
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
            consumer.require(previous_schema != "friday.current-source-native-successor.v13"
                             or args.layer_names == ("r02-boot-sweep-observation-after-source211",),
                             "transaction_current_source_exact_fourteenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v14"
                             or args.layer_names == ("r02-managed-file-output-phase-after-source212",),
                             "transaction_current_source_exact_fifteenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v15"
                             or args.layer_names == ("m09-retained-projection-bridge-after-source213",),
                             "transaction_current_source_exact_sixteenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v16"
                             or args.layer_names == ("word-fidelity-and-docx-copy-after-source214",),
                             "transaction_current_source_exact_seventeenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v17"
                             or args.layer_names == ("m09-real-web-custody-receipt-after-source215",),
                             "transaction_current_source_exact_eighteenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v18"
                             or args.layer_names == ("ordinary-document-owner-through-attachments-after-source216",),
                             "transaction_current_source_exact_nineteenth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v19"
                             or args.layer_names == ("m09-genuine-summary-carrier-after-source217",),
                             "transaction_current_source_exact_twentieth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v20"
                             or args.layer_names == ("docx-inactive-story-interop-after-source218",),
                             "transaction_current_source_exact_twenty_first_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v21"
                             or args.layer_names == ("calc-required-formula-rich-profile-after-source219",),
                             "transaction_current_source_exact_twenty_second_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v22"
                             or args.layer_names == ("sameformat-rich-ods-after-source220",),
                             "transaction_current_source_exact_twenty_third_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v23"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_FOURTH_LAYER,),
                             "transaction_current_source_exact_twenty_fourth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v24"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_FIFTH_LAYER,),
                             "transaction_current_source_exact_twenty_fifth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v25"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_SIXTH_LAYER,),
                             "transaction_current_source_exact_twenty_sixth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v26"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_SEVENTH_LAYER,),
                             "transaction_current_source_exact_twenty_seventh_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v27"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_EIGHTH_LAYER,),
                             "transaction_current_source_exact_twenty_eighth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v28"
                             or args.layer_names == (CURRENT_SOURCE_TWENTY_NINTH_LAYER,),
                             "transaction_current_source_exact_twenty_ninth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v29"
                             or args.layer_names == (CURRENT_SOURCE_THIRTIETH_LAYER,),
                             "transaction_current_source_exact_thirtieth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v30"
                             or args.layer_names == (CURRENT_SOURCE_THIRTY_FIRST_LAYER,),
                             "transaction_current_source_exact_thirty_first_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v31"
                             or args.layer_names == (CURRENT_SOURCE_THIRTY_SECOND_LAYER,),
                             "transaction_current_source_exact_thirty_second_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v32"
                             or args.layer_names == (CURRENT_SOURCE_THIRTY_THIRD_LAYER,),
                             "transaction_current_source_exact_thirty_third_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v33"
                             or args.layer_names == (CURRENT_SOURCE_THIRTY_FOURTH_LAYER,),
                             "transaction_current_source_exact_thirty_fourth_layer_required")
            consumer.require(previous_schema != "friday.current-source-native-successor.v34"
                             or args.layer_names == (CURRENT_SOURCE_THIRTY_FIFTH_LAYER,),
                             "transaction_current_source_exact_thirty_fifth_layer_required")
            if previous_schema == "friday.current-source-native-successor.v35":
                consumer.require(args.layer_names == (CURRENT_SOURCE_THIRTY_SIXTH_LAYER,),
                                 "transaction_current_source_exact_thirty_sixth_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_THIRTY_FIFTH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_thirty_fifth_predecessor_lineage_changed")
            if previous_schema == "friday.current-source-native-successor.v36":
                consumer.require(args.layer_names == (CURRENT_SOURCE_THIRTY_SEVENTH_LAYER,),
                                 "transaction_current_source_exact_thirty_seventh_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_THIRTY_SIXTH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_thirty_sixth_predecessor_lineage_changed")
            if previous_schema == "friday.current-source-native-successor.v37":
                consumer.require(args.layer_names == (CURRENT_SOURCE_THIRTY_EIGHTH_LAYER,),
                                 "transaction_current_source_exact_thirty_eighth_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_THIRTY_SEVENTH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_thirty_seventh_predecessor_lineage_changed")
            if previous_schema == "friday.current-source-native-successor.v38":
                consumer.require(args.layer_names == (CURRENT_SOURCE_THIRTY_NINTH_LAYER,),
                                 "transaction_current_source_exact_thirty_ninth_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_THIRTY_EIGHTH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_thirty_eighth_predecessor_lineage_changed")
            if previous_schema == "friday.current-source-native-successor.v39":
                consumer.require(args.layer_names == (CURRENT_SOURCE_FORTIETH_LAYER,),
                                 "transaction_current_source_exact_fortieth_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_THIRTY_NINTH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_thirty_ninth_predecessor_lineage_changed")
            if previous_schema == "friday.current-source-native-successor.v40":
                consumer.require(args.layer_names == (forty_first_layer,),
                                 "transaction_current_source_exact_forty_first_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("home") == str(home)
                    and predecessor_request.get("layer_names") == [CURRENT_SOURCE_FORTIETH_LAYER]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_request.get("project_inventory") == previous["project_files"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_fortieth_predecessor_lineage_changed")
            if previous_schema == consumer.CURRENT_SOURCE_FORTY_FIRST_SUCCESSOR_SCHEMA:
                consumer.require(args.layer_names == (forty_second_layer,),
                                 "transaction_current_source_exact_forty_second_layer_required")
                consumer.require(
                    predecessor_request.get("schema") == consumer.SCHEMA_EXPLICIT
                    and predecessor_request.get("home") == str(home)
                    and predecessor_request.get("layer_names") == [forty_first_layer]
                    and predecessor_request.get("current_input") == request["previous_input"]
                    and predecessor_request.get("project_inventory") == previous["project_files"]
                    and predecessor_context.get("root_project_update")
                    == request["current_source_successor"]["root_project_update"],
                    "transaction_current_source_forty_first_predecessor_lineage_changed")
            request["current_source_successor"].update({
                "schema": supported[previous_schema],
                "previous_native_update": pin(args.current_source_native_predecessor,
                                              predecessor_raw if bound_current else None),
            })
    consumer.require_forty_fourth_source_binding(args.layer_names, request=request)
    if forty_fourth:
        consumer.require_forty_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_third_source_binding(args.layer_names, request=request)
    if forty_third:
        consumer.require_forty_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_first_source_binding(args.layer_names, request=request)
    consumer.require_forty_second_source_binding(args.layer_names, request=request)
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
