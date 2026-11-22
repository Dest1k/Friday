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
                        help="exact canonical committed Core199 through Core296 request for the bounded next edge")
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
    consumer.require_d02_source_binding(args.layer_names)
    d02 = consumer.CURRENT_SOURCE_D02_LAYER in args.layer_names
    if d02:
        consumer.require(
            args.layer is not None
            and args.current_source_project_update is not None
            and args.current_source_native_predecessor is not None,
            "transaction_current_source_d02_previous_request_required")
        predecessor_ref = consumer.d02_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_d02_previous_request_pin_changed")
        layer = consumer.CURRENT_SOURCE_D02_LAYER
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{layer}-manifest.json", f"patches/hermes/{layer}.patch",
                         consumer.CURRENT_SOURCE_D02_HELPER, *consumer.CURRENT_SOURCE_D02_PLUGIN_AFTER)
        }
        consumer.require_d02_source_binding(args.layer_names, source_pins)
    ninety_sixth_layer = consumer.CURRENT_SOURCE_NINETY_SIXTH_LAYER
    consumer.require_ninety_sixth_source_binding(args.layer_names)
    ninety_sixth = ninety_sixth_layer in args.layer_names
    if ninety_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_fifth_predecessor_required")
        predecessor_ref = consumer.ninety_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_sixth_layer}-manifest.json",
                         f"patches/hermes/{ninety_sixth_layer}.patch")
        }
        consumer.require_ninety_sixth_source_binding(args.layer_names, source_pins)
    ninety_seventh_layer = consumer.CURRENT_SOURCE_NINETY_SEVENTH_LAYER
    consumer.require_ninety_seventh_source_binding(args.layer_names)
    ninety_seventh = ninety_seventh_layer in args.layer_names
    if ninety_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_sixth_predecessor_required")
        predecessor_ref = consumer.ninety_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_seventh_layer}-manifest.json",
                         f"patches/hermes/{ninety_seventh_layer}.patch")
        }
        consumer.require_ninety_seventh_source_binding(args.layer_names, source_pins)
    ninety_eighth_layer = consumer.CURRENT_SOURCE_NINETY_EIGHTH_LAYER
    consumer.require_ninety_eighth_source_binding(args.layer_names)
    ninety_eighth = ninety_eighth_layer in args.layer_names
    if ninety_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_seventh_predecessor_required")
        predecessor_ref = consumer.ninety_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_eighth_layer}-manifest.json",
                         f"patches/hermes/{ninety_eighth_layer}.patch")
        }
        consumer.require_ninety_eighth_source_binding(args.layer_names, source_pins)
    consumer.require_ninety_ninth_source_binding(args.layer_names)
    core296_schema = consumer.core296_successor_schema(args.layer_names)
    ninety_ninth = core296_schema is not None
    if ninety_ninth:
        ninety_ninth_layer = consumer.core296_successor_layer(core296_schema)
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_eighth_predecessor_required")
        predecessor_ref = consumer.ninety_ninth_predecessor_ref(args.home, core296_schema)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_ninth_layer}-manifest.json",
                         f"patches/hermes/{ninety_ninth_layer}.patch")
        }
        consumer.require_ninety_ninth_source_binding(args.layer_names, source_pins)
    ninety_fifth_layer = consumer.CURRENT_SOURCE_NINETY_FIFTH_LAYER
    consumer.require_ninety_fifth_source_binding(args.layer_names)
    ninety_fifth = ninety_fifth_layer in args.layer_names
    if ninety_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_fourth_predecessor_required")
        predecessor_ref = consumer.ninety_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_fifth_layer}-manifest.json",
                         f"patches/hermes/{ninety_fifth_layer}.patch")
        }
        consumer.require_ninety_fifth_source_binding(args.layer_names, source_pins)
    ninety_fourth_layer = consumer.CURRENT_SOURCE_NINETY_FOURTH_LAYER
    consumer.require_ninety_fourth_source_binding(args.layer_names)
    ninety_fourth = ninety_fourth_layer in args.layer_names
    if ninety_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_third_predecessor_required")
        predecessor_ref = consumer.ninety_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_fourth_layer}-manifest.json",
                         f"patches/hermes/{ninety_fourth_layer}.patch")
        }
        consumer.require_ninety_fourth_source_binding(args.layer_names, source_pins)
    ninety_third_layer = consumer.CURRENT_SOURCE_NINETY_THIRD_LAYER
    consumer.require_ninety_third_source_binding(args.layer_names)
    ninety_third = ninety_third_layer in args.layer_names
    if ninety_third:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_second_predecessor_required")
        predecessor_ref = consumer.ninety_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_third_layer}-manifest.json",
                         f"patches/hermes/{ninety_third_layer}.patch")
        }
        consumer.require_ninety_third_source_binding(args.layer_names, source_pins)
    ninety_second_layer = consumer.CURRENT_SOURCE_NINETY_SECOND_LAYER
    consumer.require_ninety_second_source_binding(args.layer_names)
    ninety_second = ninety_second_layer in args.layer_names
    if ninety_second:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninety_first_predecessor_required")
        predecessor_ref = consumer.ninety_second_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_second_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_second_layer}-manifest.json",
                         f"patches/hermes/{ninety_second_layer}.patch")
        }
        consumer.require_ninety_second_source_binding(args.layer_names, source_pins)
    ninety_first_layer = consumer.CURRENT_SOURCE_NINETY_FIRST_LAYER
    consumer.require_ninety_first_source_binding(args.layer_names)
    ninety_first = ninety_first_layer in args.layer_names
    if ninety_first:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_ninetieth_predecessor_required")
        predecessor_ref = consumer.ninety_first_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninety_first_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninety_first_layer}-manifest.json",
                         f"patches/hermes/{ninety_first_layer}.patch")
        }
        consumer.require_ninety_first_source_binding(args.layer_names, source_pins)
    ninetieth_layer = consumer.CURRENT_SOURCE_NINETIETH_LAYER
    consumer.require_ninetieth_source_binding(args.layer_names)
    ninetieth = ninetieth_layer in args.layer_names
    if ninetieth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_ninth_predecessor_required")
        predecessor_ref = consumer.ninetieth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_ninetieth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{ninetieth_layer}-manifest.json",
                         f"patches/hermes/{ninetieth_layer}.patch")
        }
        consumer.require_ninetieth_source_binding(args.layer_names, source_pins)
    eighty_ninth_layer = consumer.CURRENT_SOURCE_EIGHTY_NINTH_LAYER
    consumer.require_eighty_ninth_source_binding(args.layer_names)
    eighty_ninth = eighty_ninth_layer in args.layer_names
    if eighty_ninth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_eighth_predecessor_required")
        predecessor_ref = consumer.eighty_ninth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_ninth_layer}-manifest.json",
                         f"patches/hermes/{eighty_ninth_layer}.patch")
        }
        consumer.require_eighty_ninth_source_binding(args.layer_names, source_pins)
    eighty_eighth_layer = consumer.CURRENT_SOURCE_EIGHTY_EIGHTH_LAYER
    consumer.require_eighty_eighth_source_binding(args.layer_names)
    eighty_eighth = eighty_eighth_layer in args.layer_names
    if eighty_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_seventh_predecessor_required")
        predecessor_ref = consumer.eighty_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_eighth_layer}-manifest.json",
                         f"patches/hermes/{eighty_eighth_layer}.patch")
        }
        consumer.require_eighty_eighth_source_binding(args.layer_names, source_pins)
    eighty_seventh_layer = consumer.CURRENT_SOURCE_EIGHTY_SEVENTH_LAYER
    consumer.require_eighty_seventh_source_binding(args.layer_names)
    eighty_seventh = eighty_seventh_layer in args.layer_names
    if eighty_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_sixth_predecessor_required")
        predecessor_ref = consumer.eighty_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_seventh_layer}-manifest.json",
                         f"patches/hermes/{eighty_seventh_layer}.patch")
        }
        consumer.require_eighty_seventh_source_binding(args.layer_names, source_pins)
    eighty_sixth_layer = consumer.CURRENT_SOURCE_EIGHTY_SIXTH_LAYER
    consumer.require_eighty_sixth_source_binding(args.layer_names)
    eighty_sixth = eighty_sixth_layer in args.layer_names
    if eighty_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_fifth_predecessor_required")
        predecessor_ref = consumer.eighty_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_sixth_layer}-manifest.json",
                         f"patches/hermes/{eighty_sixth_layer}.patch")
        }
        consumer.require_eighty_sixth_source_binding(args.layer_names, source_pins)
    eighty_fifth_layer = consumer.CURRENT_SOURCE_EIGHTY_FIFTH_LAYER
    consumer.require_eighty_fifth_source_binding(args.layer_names)
    eighty_fifth = eighty_fifth_layer in args.layer_names
    if eighty_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_fourth_predecessor_required")
        predecessor_ref = consumer.eighty_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_fifth_layer}-manifest.json",
                         f"patches/hermes/{eighty_fifth_layer}.patch")
        }
        consumer.require_eighty_fifth_source_binding(args.layer_names, source_pins)
    eighty_fourth_layer = consumer.CURRENT_SOURCE_EIGHTY_FOURTH_LAYER
    consumer.require_eighty_fourth_source_binding(args.layer_names)
    eighty_fourth = eighty_fourth_layer in args.layer_names
    if eighty_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_third_predecessor_required")
        predecessor_ref = consumer.eighty_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_fourth_layer}-manifest.json",
                         f"patches/hermes/{eighty_fourth_layer}.patch")
        }
        consumer.require_eighty_fourth_source_binding(args.layer_names, source_pins)
    eighty_third_layer = consumer.CURRENT_SOURCE_EIGHTY_THIRD_LAYER
    consumer.require_eighty_third_source_binding(args.layer_names)
    eighty_third = eighty_third_layer in args.layer_names
    if eighty_third:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_second_predecessor_required")
        predecessor_ref = consumer.eighty_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_third_layer}-manifest.json",
                         f"patches/hermes/{eighty_third_layer}.patch")
        }
        consumer.require_eighty_third_source_binding(args.layer_names, source_pins)
    eighty_second_layer = consumer.CURRENT_SOURCE_EIGHTY_SECOND_LAYER
    consumer.require_eighty_second_source_binding(args.layer_names)
    eighty_second = eighty_second_layer in args.layer_names
    if eighty_second:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eighty_first_predecessor_required")
        predecessor_ref = consumer.eighty_second_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_second_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_second_layer}-manifest.json",
                         f"patches/hermes/{eighty_second_layer}.patch")
        }
        consumer.require_eighty_second_source_binding(args.layer_names, source_pins)
    eighty_first_layer = consumer.CURRENT_SOURCE_EIGHTY_FIRST_LAYER
    consumer.require_eighty_first_source_binding(args.layer_names)
    eighty_first = eighty_first_layer in args.layer_names
    if eighty_first:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_eightieth_predecessor_required")
        predecessor_ref = consumer.eighty_first_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eighty_first_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eighty_first_layer}-manifest.json",
                         f"patches/hermes/{eighty_first_layer}.patch")
        }
        consumer.require_eighty_first_source_binding(args.layer_names, source_pins)
    eightieth_layer = consumer.CURRENT_SOURCE_EIGHTIETH_LAYER
    consumer.require_eightieth_source_binding(args.layer_names)
    eightieth = eightieth_layer in args.layer_names
    if eightieth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_ninth_predecessor_required")
        predecessor_ref = consumer.eightieth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_eightieth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{eightieth_layer}-manifest.json",
                         f"patches/hermes/{eightieth_layer}.patch")
        }
        consumer.require_eightieth_source_binding(args.layer_names, source_pins)
    seventy_ninth_layer = consumer.CURRENT_SOURCE_SEVENTY_NINTH_LAYER
    consumer.require_seventy_ninth_source_binding(args.layer_names)
    seventy_ninth = seventy_ninth_layer in args.layer_names
    if seventy_ninth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_eighth_predecessor_required")
        predecessor_ref = consumer.seventy_ninth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_ninth_layer}-manifest.json",
                         f"patches/hermes/{seventy_ninth_layer}.patch")
        }
        consumer.require_seventy_ninth_source_binding(args.layer_names, source_pins)
    seventy_eighth_layer = consumer.CURRENT_SOURCE_SEVENTY_EIGHTH_LAYER
    consumer.require_seventy_eighth_source_binding(args.layer_names)
    seventy_eighth = seventy_eighth_layer in args.layer_names
    if seventy_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_seventh_predecessor_required")
        predecessor_ref = consumer.seventy_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_eighth_layer}-manifest.json",
                         f"patches/hermes/{seventy_eighth_layer}.patch")
        }
        consumer.require_seventy_eighth_source_binding(args.layer_names, source_pins)
    seventy_seventh_layer = consumer.CURRENT_SOURCE_SEVENTY_SEVENTH_LAYER
    consumer.require_seventy_seventh_source_binding(args.layer_names)
    seventy_seventh = seventy_seventh_layer in args.layer_names
    if seventy_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_sixth_predecessor_required")
        predecessor_ref = consumer.seventy_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_seventh_layer}-manifest.json",
                         f"patches/hermes/{seventy_seventh_layer}.patch")
        }
        consumer.require_seventy_seventh_source_binding(args.layer_names, source_pins)
    seventy_sixth_layer = consumer.CURRENT_SOURCE_SEVENTY_SIXTH_LAYER
    consumer.require_seventy_sixth_source_binding(args.layer_names)
    seventy_sixth = seventy_sixth_layer in args.layer_names
    if seventy_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_fifth_predecessor_required")
        predecessor_ref = consumer.seventy_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_sixth_layer}-manifest.json",
                         f"patches/hermes/{seventy_sixth_layer}.patch")
        }
        consumer.require_seventy_sixth_source_binding(args.layer_names, source_pins)
    seventy_fifth_layer = consumer.CURRENT_SOURCE_SEVENTY_FIFTH_LAYER
    consumer.require_seventy_fifth_source_binding(args.layer_names)
    seventy_fifth = seventy_fifth_layer in args.layer_names
    if seventy_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_fourth_predecessor_required")
        predecessor_ref = consumer.seventy_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_fifth_layer}-manifest.json",
                         f"patches/hermes/{seventy_fifth_layer}.patch")
        }
        consumer.require_seventy_fifth_source_binding(args.layer_names, source_pins)
    seventy_fourth_layer = consumer.CURRENT_SOURCE_SEVENTY_FOURTH_LAYER
    consumer.require_seventy_fourth_source_binding(args.layer_names)
    seventy_fourth = seventy_fourth_layer in args.layer_names
    if seventy_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_third_predecessor_required")
        predecessor_ref = consumer.seventy_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_fourth_layer}-manifest.json",
                         f"patches/hermes/{seventy_fourth_layer}.patch")
        }
        consumer.require_seventy_fourth_source_binding(args.layer_names, source_pins)
    seventy_third_layer = consumer.CURRENT_SOURCE_SEVENTY_THIRD_LAYER
    consumer.require_seventy_third_source_binding(args.layer_names)
    seventy_third = seventy_third_layer in args.layer_names
    if seventy_third:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_second_predecessor_required")
        predecessor_ref = consumer.seventy_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_third_layer}-manifest.json",
                         f"patches/hermes/{seventy_third_layer}.patch")
        }
        consumer.require_seventy_third_source_binding(args.layer_names, source_pins)
    seventy_second_layer = consumer.CURRENT_SOURCE_SEVENTY_SECOND_LAYER
    consumer.require_seventy_second_source_binding(args.layer_names)
    seventy_second = seventy_second_layer in args.layer_names
    if seventy_second:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventy_first_predecessor_required")
        predecessor_ref = consumer.seventy_second_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_second_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_second_layer}-manifest.json",
                         f"patches/hermes/{seventy_second_layer}.patch")
        }
        consumer.require_seventy_second_source_binding(args.layer_names, source_pins)
    seventy_first_layer = consumer.CURRENT_SOURCE_SEVENTY_FIRST_LAYER
    consumer.require_seventy_first_source_binding(args.layer_names)
    seventy_first = seventy_first_layer in args.layer_names
    if seventy_first:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_seventieth_predecessor_required")
        predecessor_ref = consumer.seventy_first_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventy_first_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventy_first_layer}-manifest.json",
                         f"patches/hermes/{seventy_first_layer}.patch")
        }
        consumer.require_seventy_first_source_binding(args.layer_names, source_pins)
    seventieth_layer = consumer.CURRENT_SOURCE_SEVENTIETH_LAYER
    consumer.require_seventieth_source_binding(args.layer_names)
    seventieth = seventieth_layer in args.layer_names
    if seventieth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_ninth_predecessor_required")
        predecessor_ref = consumer.seventieth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_seventieth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{seventieth_layer}-manifest.json",
                         f"patches/hermes/{seventieth_layer}.patch")
        }
        consumer.require_seventieth_source_binding(args.layer_names, source_pins)
    sixty_ninth_layer = consumer.CURRENT_SOURCE_SIXTY_NINTH_LAYER
    consumer.require_sixty_ninth_source_binding(args.layer_names)
    sixty_ninth = sixty_ninth_layer in args.layer_names
    if sixty_ninth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_eighth_predecessor_required")
        predecessor_ref = consumer.sixty_ninth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_ninth_layer}-manifest.json",
                         f"patches/hermes/{sixty_ninth_layer}.patch")
        }
        consumer.require_sixty_ninth_source_binding(args.layer_names, source_pins)
    sixty_eighth_layer = consumer.CURRENT_SOURCE_SIXTY_EIGHTH_LAYER
    consumer.require_sixty_eighth_source_binding(args.layer_names)
    sixty_eighth = sixty_eighth_layer in args.layer_names
    if sixty_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_seventh_predecessor_required")
        predecessor_ref = consumer.sixty_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_eighth_layer}-manifest.json",
                         f"patches/hermes/{sixty_eighth_layer}.patch")
        }
        consumer.require_sixty_eighth_source_binding(args.layer_names, source_pins)
    sixty_seventh_layer = consumer.CURRENT_SOURCE_SIXTY_SEVENTH_LAYER
    consumer.require_sixty_seventh_source_binding(args.layer_names)
    sixty_seventh = sixty_seventh_layer in args.layer_names
    if sixty_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_sixth_predecessor_required")
        predecessor_ref = consumer.sixty_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_seventh_layer}-manifest.json",
                         f"patches/hermes/{sixty_seventh_layer}.patch")
        }
        consumer.require_sixty_seventh_source_binding(args.layer_names, source_pins)
    sixty_sixth_layer = consumer.CURRENT_SOURCE_SIXTY_SIXTH_LAYER
    consumer.require_sixty_sixth_source_binding(args.layer_names)
    sixty_sixth = sixty_sixth_layer in args.layer_names
    if sixty_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_fifth_predecessor_required")
        predecessor_ref = consumer.sixty_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_sixth_layer}-manifest.json",
                         f"patches/hermes/{sixty_sixth_layer}.patch")
        }
        consumer.require_sixty_sixth_source_binding(args.layer_names, source_pins)
    sixty_fifth_layer = consumer.CURRENT_SOURCE_SIXTY_FIFTH_LAYER
    consumer.require_sixty_fifth_source_binding(args.layer_names)
    sixty_fifth = sixty_fifth_layer in args.layer_names
    if sixty_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_fourth_predecessor_required")
        predecessor_ref = consumer.sixty_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_fifth_layer}-manifest.json",
                         f"patches/hermes/{sixty_fifth_layer}.patch")
        }
        consumer.require_sixty_fifth_source_binding(args.layer_names, source_pins)
    sixty_fourth_layer = consumer.CURRENT_SOURCE_SIXTY_FOURTH_LAYER
    consumer.require_sixty_fourth_source_binding(args.layer_names)
    sixty_fourth = sixty_fourth_layer in args.layer_names
    if sixty_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_third_predecessor_required")
        predecessor_ref = consumer.sixty_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_fourth_layer}-manifest.json",
                         f"patches/hermes/{sixty_fourth_layer}.patch")
        }
        consumer.require_sixty_fourth_source_binding(args.layer_names, source_pins)
    sixty_third_layer = consumer.CURRENT_SOURCE_SIXTY_THIRD_LAYER
    consumer.require_sixty_third_source_binding(args.layer_names)
    sixty_third = sixty_third_layer in args.layer_names
    if sixty_third:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_second_predecessor_required")
        predecessor_ref = consumer.sixty_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_third_layer}-manifest.json",
                         f"patches/hermes/{sixty_third_layer}.patch")
        }
        consumer.require_sixty_third_source_binding(args.layer_names, source_pins)
    sixty_second_layer = consumer.CURRENT_SOURCE_SIXTY_SECOND_LAYER
    consumer.require_sixty_second_source_binding(args.layer_names)
    sixty_second = sixty_second_layer in args.layer_names
    if sixty_second:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixty_first_predecessor_required")
        predecessor_ref = consumer.sixty_second_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_second_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_second_layer}-manifest.json",
                         f"patches/hermes/{sixty_second_layer}.patch")
        }
        consumer.require_sixty_second_source_binding(args.layer_names, source_pins)
    sixty_first_layer = consumer.CURRENT_SOURCE_SIXTY_FIRST_LAYER
    consumer.require_sixty_first_source_binding(args.layer_names)
    sixty_first = sixty_first_layer in args.layer_names
    if sixty_first:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_sixtieth_predecessor_required")
        predecessor_ref = consumer.sixty_first_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixty_first_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixty_first_layer}-manifest.json",
                         f"patches/hermes/{sixty_first_layer}.patch")
        }
        consumer.require_sixty_first_source_binding(args.layer_names, source_pins)
    sixtieth_layer = consumer.CURRENT_SOURCE_SIXTIETH_LAYER
    consumer.require_sixtieth_source_binding(args.layer_names)
    sixtieth = sixtieth_layer in args.layer_names
    if sixtieth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_ninth_predecessor_required")
        predecessor_ref = consumer.sixtieth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_sixtieth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{sixtieth_layer}-manifest.json",
                         f"patches/hermes/{sixtieth_layer}.patch")
        }
        consumer.require_sixtieth_source_binding(args.layer_names, source_pins)
    fifty_ninth_layer = consumer.CURRENT_SOURCE_FIFTY_NINTH_LAYER
    consumer.require_fifty_ninth_source_binding(args.layer_names)
    fifty_ninth = fifty_ninth_layer in args.layer_names
    if fifty_ninth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_eighth_predecessor_required")
        predecessor_ref = consumer.fifty_ninth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_ninth_layer}-manifest.json",
                         f"patches/hermes/{fifty_ninth_layer}.patch")
        }
        consumer.require_fifty_ninth_source_binding(args.layer_names, source_pins)
    fifty_eighth_layer = consumer.CURRENT_SOURCE_FIFTY_EIGHTH_LAYER
    consumer.require_fifty_eighth_source_binding(args.layer_names)
    fifty_eighth = fifty_eighth_layer in args.layer_names
    if fifty_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_seventh_predecessor_required")
        predecessor_ref = consumer.fifty_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_eighth_layer}-manifest.json",
                         f"patches/hermes/{fifty_eighth_layer}.patch")
        }
        consumer.require_fifty_eighth_source_binding(args.layer_names, source_pins)
    fifty_seventh_layer = consumer.CURRENT_SOURCE_FIFTY_SEVENTH_LAYER
    consumer.require_fifty_seventh_source_binding(args.layer_names)
    fifty_seventh = fifty_seventh_layer in args.layer_names
    if fifty_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_sixth_predecessor_required")
        predecessor_ref = consumer.fifty_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_seventh_layer}-manifest.json",
                         f"patches/hermes/{fifty_seventh_layer}.patch")
        }
        consumer.require_fifty_seventh_source_binding(args.layer_names, source_pins)
    fifty_sixth_layer = consumer.CURRENT_SOURCE_FIFTY_SIXTH_LAYER
    consumer.require_fifty_sixth_source_binding(args.layer_names)
    fifty_sixth = fifty_sixth_layer in args.layer_names
    if fifty_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_fifth_predecessor_required")
        predecessor_ref = consumer.fifty_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_sixth_layer}-manifest.json",
                         f"patches/hermes/{fifty_sixth_layer}.patch")
        }
        consumer.require_fifty_sixth_source_binding(args.layer_names, source_pins)
    fifty_fifth_layer = consumer.CURRENT_SOURCE_FIFTY_FIFTH_LAYER
    consumer.require_fifty_fifth_source_binding(args.layer_names)
    fifty_fifth = fifty_fifth_layer in args.layer_names
    if fifty_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_fourth_predecessor_required")
        predecessor_ref = consumer.fifty_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_fifth_layer}-manifest.json",
                         f"patches/hermes/{fifty_fifth_layer}.patch")
        }
        consumer.require_fifty_fifth_source_binding(args.layer_names, source_pins)
    fifty_fourth_layer = consumer.CURRENT_SOURCE_FIFTY_FOURTH_LAYER
    consumer.require_fifty_fourth_source_binding(args.layer_names)
    fifty_fourth = fifty_fourth_layer in args.layer_names
    if fifty_fourth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_third_predecessor_required")
        predecessor_ref = consumer.fifty_fourth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_fourth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_fourth_layer}-manifest.json",
                         f"patches/hermes/{fifty_fourth_layer}.patch")
        }
        consumer.require_fifty_fourth_source_binding(args.layer_names, source_pins)
    fifty_third_layer = consumer.CURRENT_SOURCE_FIFTY_THIRD_LAYER
    consumer.require_fifty_third_source_binding(args.layer_names)
    fifty_third = fifty_third_layer in args.layer_names
    if fifty_third:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_second_predecessor_required")
        predecessor_ref = consumer.fifty_third_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_third_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_third_layer}-manifest.json",
                         f"patches/hermes/{fifty_third_layer}.patch")
        }
        consumer.require_fifty_third_source_binding(args.layer_names, source_pins)
    fifty_second_layer = consumer.CURRENT_SOURCE_FIFTY_SECOND_LAYER
    consumer.require_fifty_second_source_binding(args.layer_names)
    fifty_second = fifty_second_layer in args.layer_names
    if fifty_second:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fifty_first_predecessor_required")
        predecessor_ref = consumer.fifty_second_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_second_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_second_layer}-manifest.json",
                         f"patches/hermes/{fifty_second_layer}.patch")
        }
        consumer.require_fifty_second_source_binding(args.layer_names, source_pins)
    fifty_first_layer = consumer.CURRENT_SOURCE_FIFTY_FIRST_LAYER
    consumer.require_fifty_first_source_binding(args.layer_names)
    fifty_first = fifty_first_layer in args.layer_names
    if fifty_first:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_fiftieth_predecessor_required")
        predecessor_ref = consumer.fifty_first_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fifty_first_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fifty_first_layer}-manifest.json",
                         f"patches/hermes/{fifty_first_layer}.patch")
        }
        consumer.require_fifty_first_source_binding(args.layer_names, source_pins)
    fiftieth_layer = consumer.CURRENT_SOURCE_FIFTIETH_LAYER
    consumer.require_fiftieth_source_binding(args.layer_names)
    fiftieth = fiftieth_layer in args.layer_names
    if fiftieth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_ninth_predecessor_required")
        predecessor_ref = consumer.fiftieth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_fiftieth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{fiftieth_layer}-manifest.json",
                         f"patches/hermes/{fiftieth_layer}.patch")
        }
        consumer.require_fiftieth_source_binding(args.layer_names, source_pins)
    forty_ninth_layer = consumer.CURRENT_SOURCE_FORTY_NINTH_LAYER
    consumer.require_forty_ninth_source_binding(args.layer_names)
    forty_ninth = forty_ninth_layer in args.layer_names
    if forty_ninth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_eighth_predecessor_required")
        predecessor_ref = consumer.forty_ninth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_ninth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_ninth_layer}-manifest.json",
                         f"patches/hermes/{forty_ninth_layer}.patch")
        }
        consumer.require_forty_ninth_source_binding(args.layer_names, source_pins)
    forty_eighth_layer = consumer.CURRENT_SOURCE_FORTY_EIGHTH_LAYER
    consumer.require_forty_eighth_source_binding(args.layer_names)
    forty_eighth = forty_eighth_layer in args.layer_names
    if forty_eighth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_seventh_predecessor_required")
        predecessor_ref = consumer.forty_eighth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_eighth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_eighth_layer}-manifest.json",
                         f"patches/hermes/{forty_eighth_layer}.patch")
        }
        consumer.require_forty_eighth_source_binding(args.layer_names, source_pins)
    forty_seventh_layer = consumer.CURRENT_SOURCE_FORTY_SEVENTH_LAYER
    consumer.require_forty_seventh_source_binding(args.layer_names)
    forty_seventh = forty_seventh_layer in args.layer_names
    if forty_seventh:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_sixth_predecessor_required")
        predecessor_ref = consumer.forty_seventh_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_seventh_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_seventh_layer}-manifest.json",
                         f"patches/hermes/{forty_seventh_layer}.patch")
        }
        consumer.require_forty_seventh_source_binding(args.layer_names, source_pins)
    forty_sixth_layer = consumer.CURRENT_SOURCE_FORTY_SIXTH_LAYER
    consumer.require_forty_sixth_source_binding(args.layer_names)
    forty_sixth = forty_sixth_layer in args.layer_names
    if forty_sixth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_fifth_predecessor_required")
        predecessor_ref = consumer.forty_sixth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_sixth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_sixth_layer}-manifest.json",
                         f"patches/hermes/{forty_sixth_layer}.patch")
        }
        consumer.require_forty_sixth_source_binding(args.layer_names, source_pins)
    forty_fifth_layer = consumer.CURRENT_SOURCE_FORTY_FIFTH_LAYER
    consumer.require_forty_fifth_source_binding(args.layer_names)
    forty_fifth = forty_fifth_layer in args.layer_names
    if forty_fifth:
        consumer.require(
            args.layer is not None
            and getattr(args, "current_source_project_update", None) is not None
            and getattr(args, "current_source_native_predecessor", None) is not None,
            "transaction_current_source_forty_fourth_predecessor_required")
        predecessor_ref = consumer.forty_fifth_predecessor_ref(args.home)
        consumer.require(str(args.current_source_native_predecessor) == predecessor_ref["path"],
                         "transaction_current_source_forty_fifth_previous_request_pin_changed")
        source_pins = {
            path: consumer.digest(consumer.owned_file(args.candidate_project / path))
            for path in (f"patches/hermes/{forty_fifth_layer}-manifest.json",
                         f"patches/hermes/{forty_fifth_layer}.patch")
        }
        consumer.require_forty_fifth_source_binding(args.layer_names, source_pins)
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
    bound_current = forty_third or forty_fourth or forty_fifth or forty_sixth or forty_seventh or forty_eighth or forty_ninth or fiftieth or fifty_first or fifty_second or fifty_third or fifty_fourth or fifty_fifth or fifty_sixth or fifty_seventh or fifty_eighth or fifty_ninth or sixtieth or sixty_first or sixty_second or sixty_third or sixty_fourth or sixty_fifth or sixty_sixth or sixty_seventh or sixty_eighth or sixty_ninth or seventieth or seventy_first or seventy_second or seventy_third or seventy_fourth or seventy_fifth or seventy_sixth or seventy_seventh or seventy_eighth or seventy_ninth or eightieth or eighty_first or eighty_second or eighty_third or eighty_fourth or eighty_fifth or eighty_sixth or eighty_seventh or eighty_eighth or eighty_ninth or ninetieth or ninety_first or ninety_second or ninety_third or ninety_fourth or ninety_fifth or ninety_sixth or ninety_seventh or ninety_eighth or ninety_ninth or d02
    if ninety_ninth or d02:
        metadata_refs = consumer.d02_metadata_refs(home) if d02 else consumer.ninety_ninth_metadata_refs(home, core296_schema)
        edge = "d02" if d02 else "ninety_ninth"
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             f"transaction_current_source_{edge}_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_eighth:
        metadata_refs = consumer.ninety_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_seventh:
        metadata_refs = consumer.ninety_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_sixth:
        metadata_refs = consumer.ninety_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_fifth:
        metadata_refs = consumer.ninety_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_fourth:
        metadata_refs = consumer.ninety_fourth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_fourth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_third:
        metadata_refs = consumer.ninety_third_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_third_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_second:
        metadata_refs = consumer.ninety_second_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_second_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninety_first:
        metadata_refs = consumer.ninety_first_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninety_first_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif ninetieth:
        metadata_refs = consumer.ninetieth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_ninetieth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_ninth:
        metadata_refs = consumer.eighty_ninth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_ninth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_eighth:
        metadata_refs = consumer.eighty_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_seventh:
        metadata_refs = consumer.eighty_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_sixth:
        metadata_refs = consumer.eighty_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_fifth:
        metadata_refs = consumer.eighty_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_fourth:
        metadata_refs = consumer.eighty_fourth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_fourth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_third:
        metadata_refs = consumer.eighty_third_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_third_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_second:
        metadata_refs = consumer.eighty_second_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_second_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eighty_first:
        metadata_refs = consumer.eighty_first_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eighty_first_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif eightieth:
        metadata_refs = consumer.eightieth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_eightieth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_ninth:
        metadata_refs = consumer.seventy_ninth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_ninth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_eighth:
        metadata_refs = consumer.seventy_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_seventh:
        metadata_refs = consumer.seventy_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_sixth:
        metadata_refs = consumer.seventy_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_fifth:
        metadata_refs = consumer.seventy_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_fourth:
        metadata_refs = consumer.seventy_fourth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_fourth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_third:
        metadata_refs = consumer.seventy_third_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_third_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_second:
        metadata_refs = consumer.seventy_second_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_second_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventy_first:
        metadata_refs = consumer.seventy_first_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventy_first_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif seventieth:
        metadata_refs = consumer.seventieth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_seventieth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_ninth:
        metadata_refs = consumer.sixty_ninth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_ninth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_eighth:
        metadata_refs = consumer.sixty_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_seventh:
        metadata_refs = consumer.sixty_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_sixth:
        metadata_refs = consumer.sixty_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_fifth:
        metadata_refs = consumer.sixty_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_fourth:
        metadata_refs = consumer.sixty_fourth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_fourth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_third:
        metadata_refs = consumer.sixty_third_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_third_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_second:
        metadata_refs = consumer.sixty_second_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_second_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixty_first:
        metadata_refs = consumer.sixty_first_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixty_first_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif sixtieth:
        metadata_refs = consumer.sixtieth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_sixtieth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_ninth:
        metadata_refs = consumer.fifty_ninth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_ninth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_eighth:
        metadata_refs = consumer.fifty_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_seventh:
        metadata_refs = consumer.fifty_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_sixth:
        metadata_refs = consumer.fifty_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_fifth:
        metadata_refs = consumer.fifty_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_fourth:
        metadata_refs = consumer.fifty_fourth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_fourth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_third:
        metadata_refs = consumer.fifty_third_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_third_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_second:
        metadata_refs = consumer.fifty_second_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_second_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fifty_first:
        metadata_refs = consumer.fifty_first_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fifty_first_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif fiftieth:
        metadata_refs = consumer.fiftieth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_fiftieth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_ninth:
        metadata_refs = consumer.forty_ninth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_forty_ninth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_eighth:
        metadata_refs = consumer.forty_eighth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_forty_eighth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_seventh:
        metadata_refs = consumer.forty_seventh_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_forty_seventh_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_sixth:
        metadata_refs = consumer.forty_sixth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_forty_sixth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_fifth:
        metadata_refs = consumer.forty_fifth_metadata_refs(home)
        metadata_raw = {}
        for key in ("source_receipt", "marker", "stamp"):
            ref = metadata_refs[key]
            raw = consumer.owned_file(ref["path"])
            consumer.require(consumer.digest(raw) == ref["sha256"],
                             "transaction_current_source_forty_fifth_previous_metadata_pin_changed:" + key)
            metadata_raw[key] = raw
        receipt_ref, marker_ref, stamp_ref = (metadata_refs[key] for key in ("source_receipt", "marker", "stamp"))
        receipt = json.loads(metadata_raw["source_receipt"])
        marker = json.loads(metadata_raw["marker"])
    elif forty_fourth:
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
        "stamp": stamp_ref if (forty_fourth or forty_fifth or forty_sixth or forty_seventh or forty_eighth or forty_ninth or fiftieth or fifty_first or fifty_second or fifty_third or fifty_fourth or fifty_fifth or fifty_sixth or fifty_seventh or fifty_eighth or fifty_ninth or sixtieth or sixty_first or sixty_second or sixty_third or sixty_fourth or sixty_fifth or sixty_sixth or sixty_seventh or sixty_eighth or sixty_ninth or seventieth or seventy_first or seventy_second or seventy_third or seventy_fourth or seventy_fifth or seventy_sixth or seventy_seventh or seventy_eighth or seventy_ninth or eightieth or eighty_first or eighty_second or eighty_third or eighty_fourth or eighty_fifth or eighty_sixth or eighty_seventh or eighty_eighth or eighty_ninth or ninetieth or ninety_first or ninety_second or ninety_third or ninety_fourth or ninety_fifth or ninety_sixth or ninety_seventh or ninety_eighth or ninety_ninth or d02) else pin(home / "hermes-agent/install-stamp.json"),
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
            if d02:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_d02_previous_request_changed")
            elif ninety_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_ninth_previous_request_changed")
            elif ninety_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_eighth_previous_request_changed")
            elif ninety_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_seventh_previous_request_changed")
            elif ninety_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_sixth_previous_request_changed")
            elif ninety_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_fifth_previous_request_changed")
            elif ninety_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_fourth_previous_request_changed")
            elif ninety_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_third_previous_request_changed")
            elif ninety_second:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_second_previous_request_changed")
            elif ninety_first:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninety_first_previous_request_changed")
            elif ninetieth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_ninetieth_previous_request_changed")
            elif eighty_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_ninth_previous_request_changed")
            elif eighty_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_eighth_previous_request_changed")
            elif eighty_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_seventh_previous_request_changed")
            elif eighty_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_sixth_previous_request_changed")
            elif eighty_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_fifth_previous_request_changed")
            elif eighty_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_fourth_previous_request_changed")
            elif eighty_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_third_previous_request_changed")
            elif eighty_second:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_second_previous_request_changed")
            elif eighty_first:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eighty_first_previous_request_changed")
            elif eightieth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_eightieth_previous_request_changed")
            elif seventy_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_ninth_previous_request_changed")
            elif seventy_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_eighth_previous_request_changed")
            elif seventy_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_seventh_previous_request_changed")
            elif seventy_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_sixth_previous_request_changed")
            elif seventy_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_fifth_previous_request_changed")
            elif seventy_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_fourth_previous_request_changed")
            elif seventy_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_third_previous_request_changed")
            elif seventy_second:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_second_previous_request_changed")
            elif seventy_first:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventy_first_previous_request_changed")
            elif seventieth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_seventieth_previous_request_changed")
            elif sixty_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_ninth_previous_request_changed")
            elif sixty_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_eighth_previous_request_changed")
            elif sixty_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_seventh_previous_request_changed")
            elif sixty_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_sixth_previous_request_changed")
            elif sixty_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_fifth_previous_request_changed")
            elif sixty_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_fourth_previous_request_changed")
            elif sixty_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_third_previous_request_changed")
            elif sixty_second:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_second_previous_request_changed")
            elif sixty_first:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixty_first_previous_request_changed")
            elif sixtieth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_sixtieth_previous_request_changed")
            elif fifty_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_ninth_previous_request_changed")
            elif fifty_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_eighth_previous_request_changed")
            elif fifty_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_seventh_previous_request_changed")
            elif fifty_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_sixth_previous_request_changed")
            elif fifty_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_fifth_previous_request_changed")
            elif fifty_fourth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_fourth_previous_request_changed")
            elif fifty_third:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_third_previous_request_changed")
            elif fifty_second:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_second_previous_request_changed")
            elif fifty_first:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fifty_first_previous_request_changed")
            elif fiftieth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_fiftieth_previous_request_changed")
            elif forty_ninth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_ninth_previous_request_changed")
            elif forty_eighth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_eighth_previous_request_changed")
            elif forty_seventh:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_seventh_previous_request_changed")
            elif forty_sixth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_sixth_previous_request_changed")
            elif forty_fifth:
                consumer.require(consumer.digest(predecessor_raw) == predecessor_ref["sha256"],
                                 "transaction_current_source_forty_fifth_previous_request_changed")
            elif forty_fourth:
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
                consumer.CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_WRITE_RECOVERY_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_D02_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_D02_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_WORD_AFTER_D02_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_WORD_AFTER_D02_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_D02_RIGHTS_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_D02_RIGHTS_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_S08_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_FOURTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETY_FIRST_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_NINETIETH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETY_FIRST_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_NINTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_NINETIETH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_FOURTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTY_FIRST_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_EIGHTIETH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTY_FIRST_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_NINTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_EIGHTIETH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_FOURTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTY_FIRST_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTY_FIRST_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA,
                consumer.CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA: consumer.CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA,
            }
            previous_schema = predecessor_context.get("schema") if type(predecessor_context) is dict else None
            consumer.require(type(previous_schema) is str and previous_schema in supported,
                             "transaction_current_source_supported_predecessor_required")
            consumer.require(ninety_sixth == (previous_schema == consumer.CURRENT_SOURCE_NINETY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_sixth_edge_required")
            consumer.require(ninety_seventh == (previous_schema == consumer.CURRENT_SOURCE_NINETY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_seventh_edge_required")
            consumer.require(ninety_eighth == (previous_schema == consumer.CURRENT_SOURCE_NINETY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_eighth_edge_required")
            word_after_d02 = core296_schema == consumer.CURRENT_SOURCE_WORD_AFTER_D02_SUCCESSOR_SCHEMA
            d02_rights = core296_schema == consumer.CURRENT_SOURCE_D02_RIGHTS_SUCCESSOR_SCHEMA
            s08 = core296_schema == consumer.CURRENT_SOURCE_S08_SUCCESSOR_SCHEMA
            consumer.require(s08 == (previous_schema == consumer.CURRENT_SOURCE_D02_RIGHTS_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_s08_edge_required")
            consumer.require((ninety_ninth and not word_after_d02 and not d02_rights and not s08)
                             == (previous_schema == consumer.CURRENT_SOURCE_NINETY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_ninth_edge_required")
            consumer.require(word_after_d02 == (previous_schema == consumer.CURRENT_SOURCE_D02_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_word_after_d02_edge_required")
            consumer.require(d02_rights == (previous_schema == consumer.CURRENT_SOURCE_WORD_AFTER_D02_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_d02_rights_edge_required")
            consumer.require(d02 == (previous_schema == consumer.CURRENT_SOURCE_WRITE_RECOVERY_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_d02_edge_required")
            consumer.require(ninety_fifth == (previous_schema == consumer.CURRENT_SOURCE_NINETY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_fifth_edge_required")
            consumer.require(ninety_fourth == (previous_schema == consumer.CURRENT_SOURCE_NINETY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_fourth_edge_required")
            consumer.require(ninety_third == (previous_schema == consumer.CURRENT_SOURCE_NINETY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_third_edge_required")
            consumer.require(ninety_second == (previous_schema == consumer.CURRENT_SOURCE_NINETY_FIRST_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_second_edge_required")
            consumer.require(ninety_first == (previous_schema == consumer.CURRENT_SOURCE_NINETIETH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninety_first_edge_required")
            consumer.require(ninetieth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_NINTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_ninetieth_edge_required")
            consumer.require(eighty_ninth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_ninth_edge_required")
            consumer.require(eighty_eighth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_eighth_edge_required")
            consumer.require(eighty_seventh == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_seventh_edge_required")
            consumer.require(eighty_sixth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_sixth_edge_required")
            consumer.require(eighty_fifth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_fifth_edge_required")
            consumer.require(eighty_fourth == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_fourth_edge_required")
            consumer.require(eighty_third == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_third_edge_required")
            consumer.require(eighty_second == (previous_schema == consumer.CURRENT_SOURCE_EIGHTY_FIRST_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_second_edge_required")
            consumer.require(eighty_first == (previous_schema == consumer.CURRENT_SOURCE_EIGHTIETH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eighty_first_edge_required")
            consumer.require(eightieth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_NINTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_eightieth_edge_required")
            consumer.require(seventy_ninth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_ninth_edge_required")
            consumer.require(seventy_eighth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_eighth_edge_required")
            consumer.require(seventy_seventh == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_seventh_edge_required")
            consumer.require(seventy_sixth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_sixth_edge_required")
            consumer.require(seventy_fifth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_fifth_edge_required")
            consumer.require(seventy_fourth == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_fourth_edge_required")
            consumer.require(seventy_third == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_third_edge_required")
            consumer.require(seventy_second == (previous_schema == consumer.CURRENT_SOURCE_SEVENTY_FIRST_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_second_edge_required")
            consumer.require(seventy_first == (previous_schema == consumer.CURRENT_SOURCE_SEVENTIETH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventy_first_edge_required")
            consumer.require(seventieth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_NINTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_seventieth_edge_required")
            consumer.require(sixty_ninth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_ninth_edge_required")
            consumer.require(sixty_eighth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_eighth_edge_required")
            consumer.require(sixty_seventh == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_seventh_edge_required")
            consumer.require(sixty_sixth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_sixth_edge_required")
            consumer.require(sixty_fifth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_fifth_edge_required")
            consumer.require(sixty_fourth == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_fourth_edge_required")
            consumer.require(sixty_third == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_third_edge_required")
            consumer.require(sixty_second == (previous_schema == consumer.CURRENT_SOURCE_SIXTY_FIRST_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_second_edge_required")
            consumer.require(sixty_first == (previous_schema == consumer.CURRENT_SOURCE_SIXTIETH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixty_first_edge_required")
            consumer.require(sixtieth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_NINTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_sixtieth_edge_required")
            consumer.require(fifty_ninth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_ninth_edge_required")
            consumer.require(fifty_eighth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_eighth_edge_required")
            consumer.require(fifty_seventh == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_seventh_edge_required")
            consumer.require(fifty_sixth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_sixth_edge_required")
            consumer.require(fifty_fifth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_fifth_edge_required")
            consumer.require(fifty_fourth == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_THIRD_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_fourth_edge_required")
            consumer.require(fifty_third == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_SECOND_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_third_edge_required")
            consumer.require(fifty_second == (previous_schema == consumer.CURRENT_SOURCE_FIFTY_FIRST_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_second_edge_required")
            consumer.require(fifty_first == (previous_schema == consumer.CURRENT_SOURCE_FIFTIETH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fifty_first_edge_required")
            consumer.require(fiftieth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_NINTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_fiftieth_edge_required")
            consumer.require(forty_ninth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_EIGHTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_ninth_edge_required")
            consumer.require(forty_eighth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_SEVENTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_eighth_edge_required")
            consumer.require(forty_seventh == (previous_schema == consumer.CURRENT_SOURCE_FORTY_SIXTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_seventh_edge_required")
            consumer.require(forty_sixth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_FIFTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_sixth_edge_required")
            consumer.require(forty_fifth == (previous_schema == consumer.CURRENT_SOURCE_FORTY_FOURTH_SUCCESSOR_SCHEMA),
                             "transaction_current_source_exact_forty_fifth_edge_required")
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
                "schema": (consumer.CURRENT_SOURCE_D02_SUCCESSOR_SCHEMA if d02
                           else core296_schema if ninety_ninth else supported[previous_schema]),
                "previous_native_update": pin(args.current_source_native_predecessor,
                                              predecessor_raw if bound_current else None),
            })
    consumer.require_ninety_sixth_source_binding(args.layer_names, request=request)
    if ninety_sixth:
        consumer.require_ninety_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_seventh_source_binding(args.layer_names, request=request)
    if ninety_seventh:
        consumer.require_ninety_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_eighth_source_binding(args.layer_names, request=request)
    if ninety_eighth:
        consumer.require_ninety_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_d02_source_binding(args.layer_names, request=request)
    if d02:
        consumer.require_d02_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_ninth_source_binding(args.layer_names, request=request)
    if ninety_ninth:
        consumer.require_ninety_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_fifth_source_binding(args.layer_names, request=request)
    if ninety_fifth:
        consumer.require_ninety_fifth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_fourth_source_binding(args.layer_names, request=request)
    if ninety_fourth:
        consumer.require_ninety_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_third_source_binding(args.layer_names, request=request)
    if ninety_third:
        consumer.require_ninety_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_second_source_binding(args.layer_names, request=request)
    if ninety_second:
        consumer.require_ninety_second_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninety_first_source_binding(args.layer_names, request=request)
    if ninety_first:
        consumer.require_ninety_first_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_ninetieth_source_binding(args.layer_names, request=request)
    if ninetieth:
        consumer.require_ninetieth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_ninth_source_binding(args.layer_names, request=request)
    if eighty_ninth:
        consumer.require_eighty_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_eighth_source_binding(args.layer_names, request=request)
    if eighty_eighth:
        consumer.require_eighty_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_seventh_source_binding(args.layer_names, request=request)
    if eighty_seventh:
        consumer.require_eighty_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_sixth_source_binding(args.layer_names, request=request)
    if eighty_sixth:
        consumer.require_eighty_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_fifth_source_binding(args.layer_names, request=request)
    if eighty_fifth:
        consumer.require_eighty_fifth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_fourth_source_binding(args.layer_names, request=request)
    if eighty_fourth:
        consumer.require_eighty_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_third_source_binding(args.layer_names, request=request)
    if eighty_third:
        consumer.require_eighty_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_second_source_binding(args.layer_names, request=request)
    if eighty_second:
        consumer.require_eighty_second_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eighty_first_source_binding(args.layer_names, request=request)
    if eighty_first:
        consumer.require_eighty_first_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_eightieth_source_binding(args.layer_names, request=request)
    if eightieth:
        consumer.require_eightieth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_ninth_source_binding(args.layer_names, request=request)
    if seventy_ninth:
        consumer.require_seventy_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_eighth_source_binding(args.layer_names, request=request)
    if seventy_eighth:
        consumer.require_seventy_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_seventh_source_binding(args.layer_names, request=request)
    if seventy_seventh:
        consumer.require_seventy_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_sixth_source_binding(args.layer_names, request=request)
    if seventy_sixth:
        consumer.require_seventy_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_fifth_source_binding(args.layer_names, request=request)
    if seventy_fifth:
        consumer.require_seventy_fifth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_fourth_source_binding(args.layer_names, request=request)
    if seventy_fourth:
        consumer.require_seventy_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_third_source_binding(args.layer_names, request=request)
    if seventy_third:
        consumer.require_seventy_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_second_source_binding(args.layer_names, request=request)
    if seventy_second:
        consumer.require_seventy_second_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventy_first_source_binding(args.layer_names, request=request)
    if seventy_first:
        consumer.require_seventy_first_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_seventieth_source_binding(args.layer_names, request=request)
    if seventieth:
        consumer.require_seventieth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_ninth_source_binding(args.layer_names, request=request)
    if sixty_ninth:
        consumer.require_sixty_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_eighth_source_binding(args.layer_names, request=request)
    if sixty_eighth:
        consumer.require_sixty_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_seventh_source_binding(args.layer_names, request=request)
    if sixty_seventh:
        consumer.require_sixty_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_sixth_source_binding(args.layer_names, request=request)
    if sixty_sixth:
        consumer.require_sixty_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_fifth_source_binding(args.layer_names, request=request)
    if sixty_fifth:
        consumer.require_sixty_fifth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_fourth_source_binding(args.layer_names, request=request)
    if sixty_fourth:
        consumer.require_sixty_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_third_source_binding(args.layer_names, request=request)
    if sixty_third:
        consumer.require_sixty_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_second_source_binding(args.layer_names, request=request)
    if sixty_second:
        consumer.require_sixty_second_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixty_first_source_binding(args.layer_names, request=request)
    if sixty_first:
        consumer.require_sixty_first_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_sixtieth_source_binding(args.layer_names, request=request)
    if sixtieth:
        consumer.require_sixtieth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_ninth_source_binding(args.layer_names, request=request)
    if fifty_ninth:
        consumer.require_fifty_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_eighth_source_binding(args.layer_names, request=request)
    if fifty_eighth:
        consumer.require_fifty_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_seventh_source_binding(args.layer_names, request=request)
    if fifty_seventh:
        consumer.require_fifty_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_sixth_source_binding(args.layer_names, request=request)
    if fifty_sixth:
        consumer.require_fifty_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_fifth_source_binding(args.layer_names, request=request)
    if fifty_fifth:
        consumer.require_fifty_fifth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_fourth_source_binding(args.layer_names, request=request)
    if fifty_fourth:
        consumer.require_fifty_fourth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_third_source_binding(args.layer_names, request=request)
    if fifty_third:
        consumer.require_fifty_third_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_second_source_binding(args.layer_names, request=request)
    if fifty_second:
        consumer.require_fifty_second_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fifty_first_source_binding(args.layer_names, request=request)
    if fifty_first:
        consumer.require_fifty_first_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_fiftieth_source_binding(args.layer_names, request=request)
    if fiftieth:
        consumer.require_fiftieth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_ninth_source_binding(args.layer_names, request=request)
    if forty_ninth:
        consumer.require_forty_ninth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_eighth_source_binding(args.layer_names, request=request)
    if forty_eighth:
        consumer.require_forty_eighth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_seventh_source_binding(args.layer_names, request=request)
    if forty_seventh:
        consumer.require_forty_seventh_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_sixth_source_binding(args.layer_names, request=request)
    if forty_sixth:
        consumer.require_forty_sixth_predecessor(request, previous, raw=predecessor_raw)
    consumer.require_forty_fifth_source_binding(args.layer_names, request=request)
    if forty_fifth:
        consumer.require_forty_fifth_predecessor(request, previous, raw=predecessor_raw)
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
    if d02:
        consumer.check_plugin_preimages(request, previous, current, marker, home)
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
