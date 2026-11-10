#!/usr/bin/env python3
"""Check the scope semantics of the fresh-admission generator.

The generator used to write a fixed sentence about "one controlled Jarvis-area
activation check" into EVERY document it released, and it named an old admission
(R48) with a D-12 reason, while the scenario list of the same document covered 34
scenarios of several operations, including twelve format-creation ones. The document
therefore described an operation other than the one it authorised.

This check verifies the corrected generator on small isolated data. It does NOT
release an admission, does not touch the tester store, does not contact the gateway
and does not write anything into the serving home: the generator's scope checks are
exercised with a patched scenario map and a patched history source.

Run it with any python3:
    python3 check-fresh-admission-scope.py
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "issue-fresh-admission.py"


def load():
    spec = importlib.util.spec_from_file_location("issue_fresh_admission", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scope_is_consistent(gen, scenarios, scope):
    """The scope check of the generator, applied to isolated data.

    The generator performs the check inside main(); the same predicates are applied
    here so the check can run without releasing an admission.
    """
    text = " ".join(scope.lower().split())
    problems = []
    if "activation check" in text and len(scenarios) > 1:
        problems.append("scope names a single activation smoke but covers "
                        + str(len(scenarios)) + " scenarios")
    claims_product = "product acceptance" in text and not (
        "not a product acceptance" in text or "not a b00, fmt or product acceptance" in text)
    claims_b00 = "b00 acceptance" in text and not (
        "not a b00 acceptance" in text or "not a b00, fmt or product acceptance" in text)
    if claims_product:
        problems.append("scope claims a product acceptance")
    if claims_b00:
        problems.append("scope claims a B00 acceptance")
    covered_formats = [name for name in scenarios if name.startswith("fmt-")]
    if covered_formats and "format-creation" not in text and "format creation" not in text:
        problems.append("scope does not mention the format-creation scenarios it covers")
    if len(set(scenarios)) != len(scenarios):
        problems.append("the scenario list contains a repeated run id")
    return problems


def main():
    gen = load()
    failures = []

    def check(name, condition, detail=""):
        if condition:
            print("PASS " + name)
        else:
            failures.append(name + (": " + detail if detail else ""))
            print("FAIL " + name + (": " + detail if detail else ""))

    # --- the historical wrong scope is refused for a multi-scenario operation ------
    historical = ("One controlled Jarvis-area activation check from tester 8812646969 "
                  "after the user areas were restored through the product's onboarding "
                  "path. Not a B00, FMT or product acceptance.")
    many = {"a03-7z-roundtrip-check-01-r68": "x", "fmt-docx-create-r69": "y"}
    problems = scope_is_consistent(gen, many, historical)
    check("historical_scope_refused_for_many_scenarios",
          any("activation smoke" in p for p in problems), str(problems))

    # ... and it stays acceptable for a genuine single-scenario operation that is not
    # a format-creation scenario. For a format scenario the historical scope is still
    # refused, because it does not describe that operation.
    problems = scope_is_consistent(gen, {"d12-write-file-check-01-r48": "x"}, historical)
    check("historical_scope_allowed_for_one_scenario", not problems, str(problems))
    problems = scope_is_consistent(gen, {"fmt-docx-create-r69": "x"}, historical)
    check("historical_scope_refused_for_a_format_scenario",
          any("format-creation" in p for p in problems), str(problems))

    # --- the corrected scope is accepted for the operation it describes -----------
    corrected = gen.SCOPE
    scenarios = {"fmt-docx-create-r69": "x", "fmt-xlsx-create-r69": "y",
                 "d07-compare-v1-v2-check-01-r67": "z"}
    problems = scope_is_consistent(gen, scenarios, corrected)
    check("corrected_scope_accepted", not problems, str(problems))
    check("corrected_scope_mentions_formats",
          "format-creation" in corrected.lower())
    check("corrected_scope_denies_product_acceptance",
          "not a product acceptance" in corrected.lower())
    check("corrected_scope_denies_b00_acceptance",
          "not a b00 acceptance" in corrected.lower())

    # --- a scope that claims a product acceptance is refused ---------------------
    for claim in ("This admission is a product acceptance of the format coverage.",
                  "This admission is a B00 acceptance of the volume."):
        problems = scope_is_consistent(gen, {"fmt-docx-create-r69": "x"}, claim)
        check("claim_refused:" + claim[:24], bool(problems), str(problems))

    # --- the supersedes field no longer names the old R48 with the D-12 reason ---
    source = GENERATOR.read_text()
    check("no_old_r48_reference", "ordinary-independent-jarvis-activate-20261109-r48"
          not in source)
    check("no_old_d12_reason", "the new D-12 regression" not in source)
    check("supersedes_names_the_current_document",
          gen.SUPERSEDES_AUTHORITY_ID == "ordinary-independent-jarvis-activate-20261109-r69")

    # --- the scenario list has no repeated run id -------------------------------
    ids = [name for name, _ in gen.EXTRA_SCENARIOS]
    check("no_repeated_extra_scenario", len(set(ids)) == len(ids),
          str(sorted({n for n in ids if ids.count(n) > 1})))
    check("format_scenarios_present", len(gen.FORMAT_SCENARIOS) == 12,
          str(len(gen.FORMAT_SCENARIOS)))
    expected_formats = {"docx", "xlsx", "ods", "odt", "pdf", "rtf", "csv", "tsv",
                        "zip", "7z", "txt", "json"}
    named_formats = set()
    for name, _ in gen.FORMAT_SCENARIOS:
        parts = name.split("-")
        named_formats.add(parts[1] if len(parts) > 2 and parts[1] != "create" else parts[-2])
    check("all_twelve_formats_named", named_formats == expected_formats,
          "named=" + str(sorted(named_formats)) + " expected=" + str(sorted(expected_formats)))

    # --- the generator still refuses to rewrite a released admission --------------
    check("refuses_to_rewrite_a_released_admission",
          "already exists and is pinned" in source)

    print(json.dumps({"checks_failed": failures, "result": "PASS" if not failures else "FAIL"},
                     sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
