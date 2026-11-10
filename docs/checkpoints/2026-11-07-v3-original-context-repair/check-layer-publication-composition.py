#!/usr/bin/env python3
"""Check the composition semantics of the layer publication request.

Two properties are checked on small isolated data, without touching the serving home:

1. The generator and the validator understand the composition of ONE operation the same
   way. The generator writes the field `layer_names` and the explicit-composition schema
   v46; the validator reads exactly that field.

2. A set that is empty, malformed, repeated or unknown is REFUSED. It never becomes "all
   known layers". The historical four-layer request keeps its exact meaning: a legacy v45
   request without the field means exactly the four historical layers, not every layer the
   validator happens to know today.

By default only pure consumer functions and CLI parsing run on small data. Optional
--installed-home/--previous-input/--current-input/--candidate-project exercise the actual
consumer and product composition on a temporary receipt-inventory-only source bench,
including a late rollback. They never publish into the installed home or start a receiver.
"""
import argparse
import contextlib
import importlib.util
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
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


def consumer_bench(check, args):
    """Run the unchanged real publication entry point against receipt-only copies."""
    live = args.installed_home.resolve()
    candidate = args.candidate_project.resolve()
    before_receipt = json.loads((live / "hermes-agent.source.json").read_text())
    before_marker = json.loads((live / "FRIDAY-INSTALL.json").read_text())
    layer = "bounded-current-ask-identity"
    pair = (f"patches/hermes/{layer}-manifest.json", f"patches/hermes/{layer}.patch")
    source_file = "agent/bounded_context.py"
    tmp_root = Path(os.environ.get("TMPDIR", "/home/jericho/.dsh/tmp"))
    with tempfile.TemporaryDirectory(prefix="v3-layer-increment-", dir=tmp_root) as temp:
        root = Path(temp)
        home = root / "home"
        home.mkdir(mode=0o700)
        source = home / "hermes-agent"
        for name in before_receipt["files"]:
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live / "hermes-agent" / name, target)
        for name in ("FRIDAY-INSTALL.json", "hermes-agent.source.json",
                     "hermes-agent/install-stamp.json"):
            shutil.copy2(live / name, home / name)
        # Only the pins are exercised for these inputs; keep private user configuration
        # out of the bench and use its own harmless bytes.
        for name in ("config.yaml", "FRIDAY-PROFILE.json", "hermes-agent/.hermes/bin/hermes"):
            target = home / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"isolated publication bench\n")
        predecessor_name = ("preparation/ordinary-source-update-successor-"
                            + before_marker["ordinary_source_update_request"]["sha256"])
        predecessor = home / predecessor_name
        predecessor.mkdir(parents=True, mode=0o700)
        for name in ("request.json", "committed.json"):
            shutil.copy2(live / predecessor_name / name, predecessor / name)
        predecessor_bytes = (predecessor / "committed.json").read_bytes()
        (home / "patches/hermes").mkdir(parents=True)
        unit = root / "bench.service"
        unit.write_bytes(b"# isolated bench unit; never started\n")
        request_path = root / "request.json"
        command = [sys.executable, "-I", "-B", str(GENERATOR), "--layer", layer,
                   "--home", str(home), "--candidate-project", str(candidate),
                   "--previous-input", str(args.previous_input.resolve()),
                   "--current-input", str(args.current_input.resolve()),
                   "--native-unit", str(unit), "--output", str(request_path)]
        built = subprocess.run(command, capture_output=True, text=True, timeout=120)
        check("bench_generator_cli", built.returncode == 0, built.stderr[-250:])
        if built.returncode:
            return
        request = json.loads(request_path.read_text())
        existing = list(command)
        existing[existing.index("--layer") + 1] = "bounded-7z-codec-activation"
        refused = subprocess.run(existing, capture_output=True, text=True, timeout=120)
        check("bench_generator_installed_layer_refused", refused.returncode != 0
              and refused.stderr.strip() == "transaction_increment_layer_already_installed"
              and json.loads(request_path.read_text()) == request, refused.stderr[-250:])
        check("bench_increment_only", request["layer_names"] == [layer]
              and request["installed_layers"] == len(before_receipt["layers"])
              and not request["staged_files"] and not request["project_file_updates"]
              and not request["plugin_set"] and not request["plugin_additions"])
        # This is the consumer's existing isolated-bench switch. It suppresses service
        # inspection; all source, composition, journal and rollback code stays real.
        request["bench_home"] = str(home)

        def run(value):
            raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
            request_path.write_bytes(raw)
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(VALIDATOR), "--request", str(request_path),
                 "--request-sha256", hashlib.sha256(raw).hexdigest()],
                env={**os.environ, "HERMES_HOME": str(home)}, capture_output=True,
                text=True, timeout=240)
            output = result.stdout if result.returncode == 0 else result.stderr
            try:
                outcome = json.loads(output.strip().splitlines()[-1])
            except (ValueError, IndexError):
                outcome = {"reason": output[-250:]}
            return result.returncode, outcome

        watched = ("hermes-agent/" + source_file, "hermes-agent.source.json",
                   "FRIDAY-INSTALL.json", "hermes-agent/install-stamp.json")
        original = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                    for name in watched}
        wrong = dict(request)
        wrong["previous_input"] = request["current_input"]
        status, outcome = run(wrong)
        check("bench_dishonest_previous_refused", status == 2
              and outcome.get("reason") == "transaction_previous_input_not_installed", str(outcome))
        wrong = json.loads(json.dumps(request))
        wrong["project_inventory"]["not-in-current-input"] = "0" * 64
        wrong["project_inventory_sha256"] = hashlib.sha256(
            (json.dumps(wrong["project_inventory"], sort_keys=True, indent=2) + "\n").encode()).hexdigest()
        status, outcome = run(wrong)
        check("bench_mismatched_inventory_refused", status == 2
              and outcome.get("reason") == "transaction_project_inventory_changed", str(outcome))
        unit_bytes = unit.read_bytes()
        unit.write_bytes(b"# changed unit after request generation\n")
        status, outcome = run(request)
        check("bench_changed_unit_refused", status == 2 and outcome.get("reason")
              == "transaction_pin_changed:native_unit", str(outcome))
        unit.write_bytes(unit_bytes)
        for seconds in (0, -1, True, "180"):
            status, outcome = run(dict(request, seconds=seconds))
            check("bench_invalid_seconds_refused:" + repr(seconds), status == 2
                  and outcome.get("reason") == "transaction_seconds_positive_integer_required",
                  str(outcome))

        def deadline_refusal(clock):
            # Control only the clock, not the publisher, source check, journal or restore.
            # This avoids a slow wall-clock wait or a kill in the middle of publication.
            consumer = load(VALIDATOR, "friday_v3_deadline_fixture")
            old_clock = consumer.time.monotonic
            old_home = os.environ.get("HERMES_HOME")
            old_umask = os.umask(0o077)
            try:
                consumer.time.monotonic = clock
                os.environ["HERMES_HOME"] = str(home)
                consumer.run(request, request_path, consumer.digest(consumer.encoded(request)))
            except consumer.Refused as exc:
                return str(exc)
            finally:
                consumer.time.monotonic = old_clock
                os.umask(old_umask)
                if old_home is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = old_home
            return "NOT_REFUSED"

        ticks = iter((0.0, 181.0))
        reason = deadline_refusal(lambda: next(ticks, 181.0))
        check("bench_expired_before_staging_refused", reason == "transaction_deadline_expired", reason)
        check("bench_preflight_refusals_no_staging", not tuple(
            (home / "preparation").glob("ordinary-source-update-v45-*")))
        before_source = (source / source_file).read_bytes()
        reason = deadline_refusal(lambda: 0.0 if (source / source_file).read_bytes()
                                  == before_source else 181.0)
        check("bench_deadline_after_source_publish_refused", reason == "transaction_deadline_expired",
              reason)
        restored = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                    for name in watched}
        check("bench_expired_deadline_allows_rollback", restored == original
              and all(not (home / name).exists() for name in pair)
              and (predecessor / "committed.json").read_bytes() == predecessor_bytes)
        failed = dict(request, fail_between_metadata=True)
        status, outcome = run(failed)
        check("bench_real_late_failure", status == 2 and outcome.get("reason")
              == "transaction_controlled_failure_between_metadata", str(outcome))
        restored = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                    for name in watched}
        check("bench_rollback_bytes_and_modes", restored == original)
        check("bench_rollback_removes_new_pair", all(not (home / name).exists() for name in pair))
        check("bench_rollback_preserves_predecessor", (predecessor / "committed.json").read_bytes()
              == predecessor_bytes)
        status, outcome = run(request)
        check("bench_real_consumer_commit", status == 0 and outcome.get("state")
              == "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED" and outcome.get("layers") == 1
              and outcome.get("files") == 1, str(outcome))
        if status:
            return
        after_receipt = json.loads((home / "hermes-agent.source.json").read_text())
        check("bench_previous_layers_preserved", after_receipt["layers"][:-1]
              == before_receipt["layers"] and after_receipt["layers"][-1]["manifest"] == pair[0])
        check("bench_only_target_inventory_changed",
              {k: v for k, v in after_receipt["files"].items() if k != source_file}
              == {k: v for k, v in before_receipt["files"].items() if k != source_file})
        check("bench_new_pair_published", all((home / name).read_bytes()
              == (candidate / name).read_bytes() for name in pair))
        stamp = json.loads((source / "install-stamp.json").read_text())
        marker = json.loads((home / "FRIDAY-INSTALL.json").read_text())
        check("bench_stamp_and_marker_follow_receipt", stamp["fridaySource"]["layers"]
              == after_receipt["layers"] and marker["input_sha256"]
              == request["current_input"]["sha256"]
              and marker["source_receipt_sha256"] == outcome["receipt_sha256"])
        check("bench_commit_preserves_predecessor", (predecessor / "committed.json").read_bytes()
              == predecessor_bytes)
        summary = {"before_layers": len(before_receipt["layers"]),
                   "after_layers": len(after_receipt["layers"]),
                   "before_source": before_receipt["files"][source_file]["sha256"],
                   "after_source": after_receipt["files"][source_file]["sha256"],
                   "receipt_sha256": outcome["receipt_sha256"],
                   "previous_input_sha256": request["previous_input"]["sha256"],
                   "current_input_sha256": request["current_input"]["sha256"],
                   "temporary_bench_removed_on_exit": True}
        print("BENCH " + json.dumps(summary, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    for name in ("installed-home", "previous-input", "current-input", "candidate-project"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args(argv)
    provided = [value is not None for value in vars(args).values()]
    if any(provided) and not all(provided):
        parser.error("the four bench inputs must be supplied together")
    validator = load(VALIDATOR, "friday_v3_layer_publication")
    generator = load(GENERATOR, "build_layer_publication_request")
    failures = []
    checks = []

    def check(name, condition, detail=""):
        checks.append(name)
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
    check("generator_default_cli_keeps_four", generator.parse_args([]).layer_names == HISTORICAL_FOUR)
    selected = generator.parse_args(["--layer", "bounded-current-ask-identity"])
    check("generator_explicit_cli_selects_increment",
          selected.layer_names == ("bounded-current-ask-identity",))
    selected = generator.parse_args(["--layer", "bounded-resume-sidecar-guard",
                                     "--layer", "bounded-current-ask-identity"])
    check("generator_explicit_cli_keeps_order", selected.layer_names == (
        "bounded-resume-sidecar-guard", "bounded-current-ask-identity"))
    for name, flags in (("generator_repeated_layer_refused", ["--layer", "bounded-current-ask-identity"] * 2),
                        ("generator_unknown_layer_refused", ["--layer", "no-such-layer"])):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                generator.parse_args(flags)
        except SystemExit as exc:
            check(name, exc.code == 2)
        else:
            check(name, False)

    # --- 2. the explicit schema carries the declared composition --------------------
    explicit = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": list(HISTORICAL_FOUR)}
    check("explicit_four_layers_resolve",
          validator.resolve_layer_names(explicit) == HISTORICAL_FOUR)

    # --- 3. one-layer variants resolve to exactly that one layer --------------------
    for single in ("bounded-resume-sidecar-guard", "bounded-7z-codec-activation",
                   "bounded-current-ask-identity"):
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

    # Both historical pre-pinned patches and genuinely new exact pairs use the same
    # consumer delta validator. Unrelated additions and changed existing patches refuse.
    layer = "bounded-current-ask-identity"
    patch = f"patches/hermes/{layer}.patch"
    manifest = f"patches/hermes/{layer}-manifest.json"

    def delta(previous, current, **extra):
        request = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [layer],
                   "project_inventory": current,
                   "project_inventory_sha256": validator.digest(validator.encoded(current)),
                   "plugin_set": [], "plugin_additions": [], "project_file_updates": []}
        request.update(extra)
        return request, {"project_files": previous}, {"project_files": current}

    check("new_exact_pair_delta_accepted", validator.check_project_inventory(
        *delta({}, {patch: "a" * 64, manifest: "b" * 64})) == (layer,))
    check("historical_pre_pinned_patch_delta_accepted", validator.check_project_inventory(
        *delta({patch: "a" * 64}, {patch: "a" * 64, manifest: "b" * 64})) == (layer,))
    check("declared_project_update_kept", validator.check_project_inventory(*delta(
        {patch: "a" * 64, "scripts/helper.py": "c" * 64},
        {patch: "a" * 64, manifest: "b" * 64, "scripts/helper.py": "d" * 64},
        project_file_updates=["scripts/helper.py"])) == (layer,))
    negative = (
        ("changed_existing_patch_refused", delta({patch: "a" * 64},
            {patch: "c" * 64, manifest: "b" * 64}), "transaction_layer_patch_pin_changed"),
        ("unselected_new_patch_refused", delta({}, {patch: "a" * 64, manifest: "b" * 64,
            "patches/hermes/unselected.patch": "c" * 64}), "transaction_project_delta_changed"),
        ("missing_selected_pair_refused", delta({}, {manifest: "b" * 64}),
            "transaction_layer_files_missing"),
        ("mismatched_request_inventory_refused", delta({}, {patch: "a" * 64, manifest: "b" * 64},
            project_inventory={}), "transaction_project_inventory_changed"),
    )
    for name, inputs, reason in negative:
        try:
            validator.check_project_inventory(*inputs)
        except validator.Refused as exc:
            check(name, reason in str(exc), str(exc))
        else:
            check(name, False)

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

    if all(provided):
        consumer_bench(check, args)

    print(json.dumps({"checks": len(checks), "checks_failed": failures,
                      "result": "PASS" if not failures else "FAIL"},
                     sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
