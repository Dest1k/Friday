#!/usr/bin/env python3
"""Check the composition semantics of the layer publication request.

Two properties are checked on small isolated data, without touching the serving home:

1. The generator and the validator understand the composition of ONE operation the same
   way. The generator writes the field `layer_names` and the explicit-composition schema
   v46; the validator reads exactly that field.

2. A set that is empty, malformed, repeated or unknown is REFUSED. It never becomes "all
   known layers". The historical four-layer request keeps its exact meaning: a legacy v45
   request without the field means exactly the four historical layers, not the six the
   validator happens to know today.

The validator is loaded as a module and only its pure functions are called: no home, no
candidate, no publication, no receiver.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "friday_v3_layer_publication.py"
GENERATOR = HERE / "build-layer-publication-request.py"

HISTORICAL_FOUR = (
    "source157-original-context-deterministic-overhead-after-source156",
    "source157-bounded-schema-hints-after-source156",
    "source157-tool-budget-fit-after-source156",
    "write-file-format-guard",
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    validator = load(VALIDATOR, "friday_v3_layer_publication")
    generator = load(GENERATOR, "build_layer_publication_request")
    failures = []

    def check(name, condition, detail=""):
        if condition:
            print("PASS " + name)
        else:
            failures.append(name + (": " + detail if detail else ""))
            print("FAIL " + name + (": " + detail if detail else ""))

    def refused(name, request, reason_fragment):
        try:
            got = validator.resolve_layer_names(request)
        except validator.Refused as exc:
            check(name, reason_fragment in str(exc), "reason=" + str(exc))
            return
        failures.append(name + ": not refused, got " + repr(got))
        print("FAIL " + name + ": not refused, got " + repr(got))

    # --- 1. the generator declares the composition explicitly -----------------------
    check("generator_declares_four_layers", len(generator.LAYER_NAMES) == 4,
          "got " + repr(generator.LAYER_NAMES))
    check("generator_uses_explicit_schema",
          "friday.ordinary-telegram-source-update.v46" in GENERATOR.read_text())
    check("generator_writes_layer_names",
          '"layer_names": list(LAYER_NAMES)' in GENERATOR.read_text())

    # --- 2. the explicit schema carries the declared composition --------------------
    explicit = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": list(HISTORICAL_FOUR)}
    check("explicit_four_layers_resolve",
          validator.resolve_layer_names(explicit) == HISTORICAL_FOUR)

    # --- 3. one-layer variants resolve to exactly that one layer --------------------
    for single in ("bounded-resume-sidecar-guard", "bounded-7z-codec-activation"):
        request = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [single]}
        check("single_layer_resolves:" + single,
              validator.resolve_layer_names(request) == (single,))
        # a one-layer request must not widen to the known set
        check("single_layer_not_widened:" + single,
              validator.resolve_layer_names(request) != validator.LAYER_NAMES)

    # --- 4. the historical four-layer request keeps its exact meaning --------------
    legacy = {"schema": validator.SCHEMA}
    check("legacy_four_layers_mean_four",
          validator.resolve_layer_names(legacy) == HISTORICAL_FOUR)
    check("legacy_does_not_mean_all_known",
          validator.resolve_layer_names(legacy) != validator.LAYER_NAMES)
    # an explicit field on a legacy schema wins over the legacy default
    legacy_explicit = {"schema": validator.SCHEMA, "layer_names": ["bounded-7z-codec-activation"]}
    check("legacy_explicit_field_wins",
          validator.resolve_layer_names(legacy_explicit) == ("bounded-7z-codec-activation",))

    # --- 5. a bad set is refused, never widened -------------------------------------
    refused("absent_field_v46", {"schema": validator.SCHEMA_EXPLICIT},
            "transaction_layer_names_required")
    refused("absent_field_unknown_schema", {"schema": "friday.whatever"},
            "transaction_layer_names_required")
    refused("empty_set", {"schema": validator.SCHEMA_EXPLICIT, "layer_names": []},
            "transaction_layer_names_empty")
    refused("empty_set_legacy", {"schema": validator.SCHEMA, "layer_names": []},
            "transaction_layer_names_empty")
    refused("repeated_name",
            {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [HISTORICAL_FOUR[0],
                                                                  HISTORICAL_FOUR[0]]},
            "transaction_layer_names_repeated")
    refused("not_a_list", {"schema": validator.SCHEMA_EXPLICIT, "layer_names": "all"},
            "transaction_layer_names_malformed")
    refused("non_string_element",
            {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [HISTORICAL_FOUR[0], 7]},
            "transaction_layer_names_malformed")
    refused("empty_string_element",
            {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [""]},
            "transaction_layer_names_malformed")

    # --- 6. an unknown name is refused by the known-set check -----------------------
    unknown = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": ["no-such-layer"]}
    try:
        names = validator.resolve_layer_names(unknown)
        known = set(names) <= set(validator.LAYER_NAMES)
        check("unknown_name_refused", not known, "resolved " + repr(names))
    except validator.Refused as exc:
        check("unknown_name_refused", True)

    # --- 7. the published request documents are read with the same semantics --------
    candidate = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108")
    observed = []
    for name in sorted(p.name for p in candidate.glob("REQUEST-*.json")):
        request = json.loads((candidate / name).read_text())
        if "layer_names" not in request:
            continue
        try:
            names = validator.resolve_layer_names(request)
        except validator.Refused as exc:
            observed.append(name + "=REFUSED(" + str(exc) + ")")
            continue
        observed.append(name + "=" + (",".join(names) if len(names) <= 1
                                      else str(len(names)) + " layers"))
    print("OBSERVED " + "; ".join(observed))

    print(json.dumps({"checks_failed": failures, "result": "PASS" if not failures else "FAIL"},
                     sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
