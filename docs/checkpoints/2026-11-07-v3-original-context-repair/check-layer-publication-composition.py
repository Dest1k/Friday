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
import tarfile
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
    layer_names = tuple(args.layer or ("bounded-current-ask-identity",))
    layer = layer_names[0]
    pair = tuple(name for selected in layer_names for name in (
        f"patches/hermes/{selected}-manifest.json", f"patches/hermes/{selected}.patch"))
    manifests = [json.loads((candidate / f"patches/hermes/{selected}-manifest.json").read_text())
                 for selected in layer_names]
    manifest = {"files": [row for body in manifests for row in body["files"]]}
    source_files = tuple(row["path"] for row in manifest["files"])
    check("bench_distinct_source_targets", len(source_files) == len(set(source_files)))
    if layer == "necessary-document-clarification-p04":
        check("bench_p04_exact_three_targets", set(source_files) == {
            "hermes_cli/friday_prompt_scope.py", "agent/prompt_builder.py", "tools/scoped_pdf_ocr.py"})
    if layer == "archive-conversion-failure-provenance-after188":
        check("bench_archive_provenance_exact_five_targets", set(source_files) == {
            "agent/turn_explainers.py", "agent/turn_finalizer.py", "agent/turn_context.py",
            "agent/tool_executor.py", "gateway/run_turn_runner.py"})
    if layer == "arj-unix-attribute-types-after-source189":
        check("bench_arj190_exact_one_codec_target", source_files == (
            "hermes_cli/friday_workspace_arj_codec.py",))
    if layer_names == ("ordinary-direct-plain-cancel-after-source192",):
        check("bench_c10_exact_one_base_target", source_files == ("gateway/platforms/base.py",))
        check("bench_c10_exact_192_prerequisites", len(manifests[0]["prerequisites"]) == 192)
        check("bench_c10_actual_preimage", hashlib.sha256((live / "hermes-agent" / source_files[0])
              .read_bytes()).hexdigest() == manifests[0]["files"][0]["before_sha256"])
    # Read every prerequisite through the same input consumed by publication. The
    # count need not equal the installed layer count; it is a dependency set.
    previous_input = json.loads(args.previous_input.read_text())
    current_input = json.loads(args.current_input.read_text())
    plugin_names = tuple(sorted(name for name, pin in previous_input["project_files"].items()
        if name.startswith("plugins/friday_rework/") and current_input["project_files"].get(name) != pin))
    if layer_names == ("ods-target-comments-after-source193",):
        check("bench_ods194_exact_one_target", source_files == ("tools/scoped_ods.py",))
        check("bench_ods194_exact_193_prerequisites", len(manifests[0]["prerequisites"]) == 193)
        check("bench_ods194_exact_one_plugin", plugin_names == ("plugins/friday_rework/host_record.py",))
        check("bench_ods194_current_installed193", len(before_receipt["layers"]) == 193)
    if layer_names == ("ods-comment-preservation-after-source194",):
        check("bench_ods195_exact_one_target", source_files == ("tools/scoped_ods.py",))
        check("bench_ods195_exact_194_prerequisites", len(manifests[0]["prerequisites"]) == 194)
        check("bench_ods195_no_plugin_delta", plugin_names == ())
        check("bench_ods195_current_installed194", len(before_receipt["layers"]) == 194)
        check("bench_ods195_actual_preimage", hashlib.sha256((live / "hermes-agent" / source_files[0])
              .read_bytes()).hexdigest() == manifests[0]["files"][0]["before_sha256"])
    if layer_names == ("odf-native-conversion-output-after-source195",):
        check("bench_odf196_exact_five_targets", set(source_files) == {
            "tools/scoped_word_conversion.py", "hermes_cli/friday_workspace_word_conversion.py",
            "hermes_cli/friday_workspace_spreadsheet_conversion.py",
            "tools/scoped_spreadsheet_conversion.py", "tools/scoped_spreadsheet_profiles.py"})
        check("bench_odf196_exact_195_prerequisites", len(manifests[0]["prerequisites"]) == 195)
        check("bench_odf196_no_plugin_delta", plugin_names == ())
        check("bench_odf196_current_installed195", len(before_receipt["layers"]) == 195)
        check("bench_odf196_actual_five_preimages", all(hashlib.sha256(
            (live / "hermes-agent" / row["path"]).read_bytes()).hexdigest()
            == row["before_sha256"] for row in manifests[0]["files"]))
    if layer_names == ("docx-odt-output-after-source196",):
        check("bench_word197_exact_one_target", source_files == ("tools/scoped_word_conversion.py",))
        check("bench_word197_exact_196_prerequisites", len(manifests[0]["prerequisites"]) == 196)
        check("bench_word197_no_plugin_delta", plugin_names == ())
        check("bench_word197_current_installed196", len(before_receipt["layers"]) == 196)
        check("bench_word197_actual_preimage", hashlib.sha256((live / "hermes-agent" / source_files[0])
              .read_bytes()).hexdigest() == manifests[0]["files"][0]["before_sha256"])
    if layer_names == ("odf-reverse-output-after-source197",):
        check("bench_reverse198_exact_two_targets", source_files == (
            "tools/scoped_word_conversion.py", "tools/scoped_spreadsheet_conversion.py"))
        check("bench_reverse198_exact_197_prerequisites", len(manifests[0]["prerequisites"]) == 197)
        prior_patches = {}
        for row in before_receipt["layers"]:
            prior = json.loads((candidate / row["manifest"]).read_text())
            patch = prior.get("patch", prior.get("patch_file"))
            patch = patch if "/" in patch else "patches/hermes/" + patch
            prior_patches[patch] = row["patch_sha256"]
        check("bench_reverse198_exact_receipt_prefix_dependencies",
              manifests[0]["prerequisites"] == prior_patches)
        check("bench_reverse198_base_commit_is_receipt_commit",
              manifests[0]["base_commit"] == before_receipt["commit"]
              == "781334eea4b9225a3e194faf0c241d9afe218634")
        check("bench_reverse198_no_plugin_delta", plugin_names == ())
        check("bench_reverse198_current_installed197", len(before_receipt["layers"]) == 197)
        check("bench_reverse198_exact_two_preimages", {
            row["path"]: row["before_sha256"] for row in manifests[0]["files"]} == {
            "tools/scoped_word_conversion.py": "2b5da5f3d0437ddad25e8729db556d4d2ee1eebdebc53b3214bdee385498bf15",
            "tools/scoped_spreadsheet_conversion.py": "e1a65a91bef106217a42bd58a102c751a5f66044e72df8f49b450bbfd43feebc"})
        check("bench_reverse198_actual_two_preimages", all(hashlib.sha256(
            (live / "hermes-agent" / row["path"]).read_bytes()).hexdigest()
            == row["before_sha256"] for row in manifests[0]["files"]))
        check("bench_reverse198_exact_two_postimages", {
            row["path"]: row["sha256"] for row in manifests[0]["files"]} == {
            "tools/scoped_word_conversion.py": "62c61f166b10a4ef2ff6b903ad7e00c95a0814adf84d68050221e4882b2ccf8b",
            "tools/scoped_spreadsheet_conversion.py": "2afbe63a166449e6b8acc0b907def046f01735b6c7690c9facbeba92958b9d03"})
        check("bench_reverse198_project474_prefix_preserved",
              len(previous_input["project_files"]) == 474 and len(current_input["project_files"]) == 476
              and all(current_input["project_files"].get(n) == pin
                      for n, pin in previous_input["project_files"].items()))
    check("bench_prerequisites_pinned", all(previous_input["project_files"].get(name) == pin
          for body in manifests for name, pin in body.get("prerequisites", {}).items()))
    if layer_names == ("read-file-reject-write-arguments-after-source189",
                       "archive-conversion-named-target-status-after-source190"):
        check("bench_two_fix_exact_two_source_targets", source_files == (
            "tools/file_tools.py", "agent/turn_explainers.py"))
        check("bench_independent_dependency_sets_preserved",
              [len(body["prerequisites"]) for body in manifests] == [189, 190])
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
        for name in plugin_names:
            target = home / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live / name, target)
            check("bench_plugin_preimage_pinned:" + name,
                  hashlib.sha256(target.read_bytes()).hexdigest() == previous_input["project_files"][name]
                  == before_marker["plugin_files"][name])
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
        command = [sys.executable, "-I", "-B", str(GENERATOR)] + [
                   flag for selected in layer_names for flag in ("--layer", selected)] + [
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
        check("bench_increment_only", request["layer_names"] == list(layer_names)
              and request["installed_layers"] == len(before_receipt["layers"])
              and not request["staged_files"] and not request["project_file_updates"]
              and request["plugin_set"] == list(plugin_names) and not request["plugin_additions"])
        # This is the consumer's existing isolated-bench switch. It suppresses service
        # inspection; all source, composition, journal and rollback code stays real.
        request["bench_home"] = str(home)

        event_number = 0

        def archive(value, outcome):
            nonlocal event_number
            if args.evidence_dir is None:
                return
            event_number += 1
            destination = args.evidence_dir.resolve()
            destination.mkdir(parents=True, exist_ok=True, mode=0o700)
            raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
            request_hash = hashlib.sha256(raw).hexdigest()
            stage = home / "preparation" / ("ordinary-source-update-v45-" + request_hash[:16])
            prefix = destination / (f"{event_number:02d}-" + request_hash[:16])
            prefix.with_suffix(".json").write_text(json.dumps({"request": value,
                "request_sha256": request_hash, "outcome": outcome,
                "stage_present": stage.exists()}, sort_keys=True, indent=2) + "\n")
            if stage.exists():
                with tarfile.open(str(prefix) + ".wal.tar.gz", "w:gz") as saved:
                    for path in sorted(stage.rglob("*")):
                        relative = path.relative_to(stage)
                        if path.is_file() and "staging" not in relative.parts:
                            saved.add(path, arcname=str(relative), recursive=False)
            snapshot = value.get("inject_snapshot_dir")
            if snapshot:
                for index, path in enumerate(sorted(Path(snapshot).glob("*.json"))):
                    shutil.copy2(path, str(prefix) + f".snapshot-{index}.json")

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
            archive(value, {"returncode": result.returncode, **outcome})
            return result.returncode, outcome

        watched = tuple("hermes-agent/" + name for name in source_files) + plugin_names + (
            "hermes-agent.source.json", "FRIDAY-INSTALL.json", "hermes-agent/install-stamp.json")
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

        if plugin_names:
            plugin_name = plugin_names[0]
            plugin_path = home / plugin_name
            stale_bytes = b"untracked stale actual plugin source\n"
            plugin_path.write_bytes(stale_bytes)
            stale_request = dict(request, fail_during_plugins=True)
            status, outcome = run(stale_request)
            check("bench_stale_actual_plugin_refused_before_intent", status == 2 and outcome.get("reason")
                  == "transaction_plugin_preimage_changed:" + plugin_name, str(outcome))
            stale_hash = hashlib.sha256((json.dumps(stale_request, sort_keys=True, indent=2) + "\n").encode()).hexdigest()
            stale_stage = home / "preparation" / ("ordinary-source-update-v45-" + stale_hash[:16])
            check("bench_stale_actual_plugin_no_intent", not (stale_stage / "intent.json").exists())
            check("bench_stale_actual_plugin_preserved", plugin_path.read_bytes() == stale_bytes)
            plugin_path.write_bytes(original[plugin_name][0])
            plugin_path.chmod(original[plugin_name][1])
            if stale_stage.exists():
                shutil.rmtree(stale_stage)
            omitted = dict(request, plugin_set=[])
            status, outcome = run(omitted)
            check("bench_undeclared_plugin_delta_refused", status == 2 and outcome.get("reason")
                  == "transaction_project_file_changed:" + plugin_names[0], str(outcome))
            bad_candidate = root / "wrong-plugin-bytes"
            # This negative reaches the actual product composition consumer before
            # plugin-byte validation, so retain its exact pinned project dependencies.
            # This is a project-only copy, with no runtime or user state.
            for name in current_input["project_files"]:
                dest = bad_candidate / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate / name, dest)
            (bad_candidate / plugin_names[0]).write_bytes(b"wrong plugin source\n")
            status, outcome = run(dict(request, candidate_project=str(bad_candidate)))
            check("bench_wrong_plugin_bytes_refused", status == 2 and outcome.get("reason")
                  == "transaction_candidate_bytes_changed:" + plugin_names[0], str(outcome))
            check("bench_wrong_plugin_bytes_rollback", all(
                ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode)) == item
                for name, item in original.items()) and all(not (home / name).exists() for name in pair))
            shutil.rmtree(bad_candidate)

        # Repin a deliberately wrong selected manifest in a separate tiny candidate.
        # The real entry point must reject each false postimage before publication.
        # In the second case, both patches have actually run in private staging.
        postimage_controls = [(index, selected, "sha256", 0)
                              for index, selected in enumerate(layer_names)]
        if layer_names == ("odf-reverse-output-after-source197",):
            postimage_controls += [(0, layer_names[0], "sha256", 1),
                                   (0, layer_names[0], "before_sha256", 0),
                                   (0, layer_names[0], "before_sha256", 1),
                                   (0, layer_names[0], "base_commit", 0)]
        for index, selected, field, file_index in postimage_controls:
            control_name = selected if (field, file_index) == ("sha256", 0) else (
                selected + ":" + field + ":" + str(file_index))
            bad_candidate = root / ("wrong-postimage-" + str(index))
            for name in pair:
                dest = bad_candidate / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate / name, dest)
            bad_manifest_name = f"patches/hermes/{selected}-manifest.json"
            bad_manifest_path = bad_candidate / bad_manifest_name
            bad_manifest = json.loads(bad_manifest_path.read_text())
            if field == "base_commit":
                bad_manifest[field] = before_receipt["base_tree"]
            else:
                bad_manifest["files"][file_index][field] = "0" * 64
            bad_manifest_path.write_text(json.dumps(bad_manifest, sort_keys=True, indent=2) + "\n")
            bad_current = json.loads(args.current_input.read_text())
            bad_current["project_files"][bad_manifest_name] = hashlib.sha256(
                bad_manifest_path.read_bytes()).hexdigest()
            bad_input = root / ("wrong-postimage-input-" + str(index) + ".json")
            bad_input.write_text(json.dumps(bad_current, sort_keys=True, indent=2) + "\n")
            bad_request = json.loads(json.dumps(request))
            bad_request["candidate_project"] = str(bad_candidate)
            bad_request["current_input"] = bad_request["candidate_input"] = {
                "path": str(bad_input), "sha256": hashlib.sha256(bad_input.read_bytes()).hexdigest()}
            bad_request["project_inventory"] = bad_current["project_files"]
            bad_request["project_inventory_sha256"] = hashlib.sha256(
                (json.dumps(bad_current["project_files"], sort_keys=True, indent=2) + "\n").encode()).hexdigest()
            status, outcome = run(bad_request)
            expected_reason = ("transaction_layer_base_commit_changed" if field == "base_commit"
                else "transaction_layer_preimage_changed:" + bad_manifest["files"][file_index]["path"]
                if field == "before_sha256" else "transaction_layer_output_changed:" + selected)
            check("bench_wrong_postimage_refused:" + control_name, status == 2
                  and outcome.get("reason") == expected_reason, str(outcome))
            restored = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                        for name in watched}
            check("bench_wrong_postimage_no_publication:" + control_name, restored == original
                  and all(not (home / name).exists() for name in pair))
            request_hash = hashlib.sha256((json.dumps(bad_request, sort_keys=True, indent=2) + "\n").encode()).hexdigest()
            bad_stage = home / "preparation" / ("ordinary-source-update-v45-" + request_hash[:16])
            check("bench_wrong_postimage_no_intent:" + control_name, not (bad_stage / "intent.json").exists())
            if field == "sha256":
                check("bench_wrong_postimage_real_staged_prefix:" + control_name, all(
                    hashlib.sha256((bad_stage / "staging" / row["path"]).read_bytes()).hexdigest()
                    == row["sha256"] for body in manifests[:index + 1] for row in body["files"]))
                shutil.rmtree(bad_stage)
            else:
                check("bench_wrong_preimage_or_commit_no_staging:" + control_name,
                      not bad_stage.exists())
            shutil.rmtree(bad_candidate)
            bad_input.unlink()

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
        archive(request, {"control": "deadline-before-staging", "reason": reason})
        check("bench_expired_before_staging_refused", reason == "transaction_deadline_expired", reason)
        request_hash = hashlib.sha256((json.dumps(request, sort_keys=True, indent=2) + "\n").encode()).hexdigest()
        check("bench_preflight_refusals_no_staging", not (
            home / "preparation" / ("ordinary-source-update-v45-" + request_hash[:16])).exists())
        before_source = {name: (source / name).read_bytes() for name in source_files}
        reason = deadline_refusal(lambda: 0.0 if all((source / name).read_bytes() == data
                                  for name, data in before_source.items()) else 181.0)
        archive(request, {"control": "deadline-after-source", "reason": reason})
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
        if plugin_names:
            status, outcome = run(dict(request, fail_during_plugins=True))
            check("bench_plugin_phase_failure", status == 2 and outcome.get("reason")
                  == "transaction_controlled_failure_during_plugins", str(outcome))
            check("bench_plugin_phase_restores_source_plugin_metadata_modes", all(
                ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode)) == item
                for name, item in original.items()) and all(not (home / name).exists() for name in pair))
            plugin_snapshot_dir = root / "plugin-rename-snapshot"
            status, outcome = run(dict(request, inject_after_rename=True,
                inject_target=str(home / plugin_names[-1]),
                inject_snapshot_dir=str(plugin_snapshot_dir),
                inject_snapshot_files=list(watched) + list(pair)))
            check("bench_plugin_rename_failure", status == 2 and outcome.get("exception") == "OSError", str(outcome))
            snapshots = list(plugin_snapshot_dir.glob("*.json"))
            check("bench_plugin_rename_snapshot_recorded", len(snapshots) == 1)
            if len(snapshots) == 1:
                snapshot = json.loads(snapshots[0].read_text())
                check("bench_plugin_postimage_reached", all(snapshot["files"][str(home / name)]
                    ["sha256"] == current_input["project_files"][name] for name in plugin_names))
            check("bench_plugin_rename_restores_all", all(
                ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode)) == item
                for name, item in original.items()) and all(not (home / name).exists() for name in pair))
        # A rename failure on the last source file proves that all selected source
        # bytes were on disk, and that rollback restores the entire multi-file layer.
        snapshot_dir = root / "rename-snapshot"
        injected = dict(request, inject_after_rename=True,
                        inject_target=str(source / source_files[-1]),
                        inject_snapshot_dir=str(snapshot_dir),
                        inject_snapshot_files=list(watched))
        status, outcome = run(injected)
        check("bench_last_source_rename_failure", status == 2 and outcome.get("exception")
              == "OSError", str(outcome))
        snapshots = list(snapshot_dir.glob("*.json"))
        check("bench_source_rename_snapshot_recorded", len(snapshots) == 1)
        if len(snapshots) == 1:
            snapshot = json.loads(snapshots[0].read_text())
            check("bench_all_source_postimages_reached", all(
                snapshot["files"][str(source / row["path"])]["sha256"] == row["sha256"]
                for row in manifest["files"]), str(snapshot))
        restored = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                    for name in watched}
        check("bench_last_source_rename_restores_all", restored == original
              and all(not (home / name).exists() for name in pair))
        # Fail after the final metadata rename: both source postimages, every new
        # pair and all three metadata files were published through the real journal.
        metadata_snapshot_dir = root / "metadata-rename-snapshot"
        injected = dict(request, inject_after_rename=True,
                        inject_target=str(home / "hermes-agent/install-stamp.json"),
                        inject_snapshot_dir=str(metadata_snapshot_dir),
                        inject_snapshot_files=list(watched) + list(pair))
        status, outcome = run(injected)
        check("bench_final_metadata_rename_failure", status == 2
              and outcome.get("exception") == "OSError", str(outcome))
        snapshots = list(metadata_snapshot_dir.glob("*.json"))
        check("bench_final_metadata_snapshot_recorded", len(snapshots) == 1)
        if len(snapshots) == 1:
            snapshot = json.loads(snapshots[0].read_text())
            check("bench_metadata_boundary_all_source_postimages", all(
                snapshot["files"][str(source / row["path"])]["sha256"] == row["sha256"]
                for row in manifest["files"]))
            check("bench_metadata_boundary_all_pair_postimages", all(
                snapshot["files"][str(home / name)]["sha256"]
                == hashlib.sha256((candidate / name).read_bytes()).hexdigest() for name in pair))
            check("bench_metadata_boundary_all_metadata_changed", all(
                snapshot["files"][str(home / name)]["sha256"]
                != hashlib.sha256(original[name][0]).hexdigest() for name in watched[-3:]))
            if plugin_names:
                check("bench_metadata_boundary_plugin_postimages", all(
                    snapshot["files"][str(home / name)]["sha256"] == current_input["project_files"][name]
                    for name in plugin_names))
        restored = {name: ((home / name).read_bytes(), stat.S_IMODE((home / name).stat().st_mode))
                    for name in watched}
        check("bench_final_metadata_rename_restores_all", restored == original
              and all(not (home / name).exists() for name in pair)
              and (predecessor / "committed.json").read_bytes() == predecessor_bytes)
        status, outcome = run(request)
        check("bench_real_consumer_commit", status == 0 and outcome.get("state")
              == "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED" and outcome.get("layers") == len(layer_names)
              and outcome.get("files") == len(source_files), str(outcome))
        if status:
            return
        after_receipt = json.loads((home / "hermes-agent.source.json").read_text())
        check("bench_previous_layers_preserved", after_receipt["layers"][:-len(layer_names)]
              == before_receipt["layers"] and [row["manifest"] for row in
              after_receipt["layers"][-len(layer_names):]] == list(pair[::2]))
        check("bench_only_target_inventory_changed",
              {k: v for k, v in after_receipt["files"].items() if k not in source_files}
              == {k: v for k, v in before_receipt["files"].items() if k not in source_files})
        check("bench_all_target_postimages_committed", all(after_receipt["files"][row["path"]]
              ["sha256"] == row["sha256"] and hashlib.sha256((source / row["path"])
              .read_bytes()).hexdigest() == row["sha256"] for row in manifest["files"]))
        check("bench_new_pair_published", all((home / name).read_bytes()
              == (candidate / name).read_bytes() for name in pair))
        stamp = json.loads((source / "install-stamp.json").read_text())
        marker = json.loads((home / "FRIDAY-INSTALL.json").read_text())
        check("bench_stamp_and_marker_follow_receipt", stamp["fridaySource"]["layers"]
              == after_receipt["layers"] and marker["input_sha256"]
              == request["current_input"]["sha256"]
              and marker["source_receipt_sha256"] == outcome["receipt_sha256"])
        if plugin_names:
            check("bench_plugin_postimages_committed", all((home / name).read_bytes()
                == (candidate / name).read_bytes() for name in plugin_names))
            check("bench_marker_plugin_pins_committed", all(marker["plugin_files"][name]
                == current_input["project_files"][name] for name in plugin_names))
            check("bench_marker_nontarget_plugin_pins_preserved", {k:v for k,v in marker["plugin_files"].items()
                if k not in plugin_names} == {k:v for k,v in before_marker["plugin_files"].items()
                if k not in plugin_names})
        if layer_names == ("odf-reverse-output-after-source197",):
            check("bench_reverse198_all51_plugin_pins_preserved",
                  len(marker["plugin_files"]) == 51
                  and marker["plugin_files"] == before_marker["plugin_files"])
            check("bench_reverse198_exact_target_rows", all(after_receipt["files"][row["path"]]
                  == {key: row[key] for key in ("bytes", "mode", "sha256")}
                  for row in manifests[0]["files"]))
        check("bench_commit_preserves_predecessor", (predecessor / "committed.json").read_bytes()
              == predecessor_bytes)
        summary = {"before_layers": len(before_receipt["layers"]),
                   "after_layers": len(after_receipt["layers"]),
                   "layer_names": list(layer_names),
                   "plugin_set": list(plugin_names),
                   "nontarget_source_inventory_preserved": len(before_receipt["files"]) - len(source_files),
                   "before_source": {name: before_receipt["files"][name]["sha256"]
                                     for name in source_files},
                   "after_source": {name: after_receipt["files"][name]["sha256"]
                                    for name in source_files},
                   "receipt_sha256": outcome["receipt_sha256"],
                   "previous_input_sha256": request["previous_input"]["sha256"],
                   "current_input_sha256": request["current_input"]["sha256"],
                   "temporary_bench_removed_on_exit": True}
        print("BENCH " + json.dumps(summary, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    for name in ("installed-home", "previous-input", "current-input", "candidate-project"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--layer", action="append")
    parser.add_argument("--evidence-dir", type=Path, help="retain own isolated requests, WAL and failure snapshots")
    args = parser.parse_args(argv)
    provided = [getattr(args, name) is not None for name in (
        "installed_home", "previous_input", "current_input", "candidate_project")]
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
    selected = generator.parse_args(["--layer", "necessary-document-clarification-p04"])
    check("generator_p04_cli_selects_only_increment",
          selected.layer_names == ("necessary-document-clarification-p04",))
    selected = generator.parse_args(["--layer", "archive-conversion-failure-provenance-after188"])
    check("generator_archive_provenance_cli_selects_only_increment",
          selected.layer_names == ("archive-conversion-failure-provenance-after188",))
    selected = generator.parse_args(["--layer", "arj-unix-attribute-types-after-source189"])
    check("generator_arj190_cli_selects_only_increment",
          selected.layer_names == ("arj-unix-attribute-types-after-source189",))
    two_fix = ("read-file-reject-write-arguments-after-source189",
               "archive-conversion-named-target-status-after-source190")
    selected = generator.parse_args([flag for name in two_fix for flag in ("--layer", name)])
    check("generator_two_fix_cli_exact_order", selected.layer_names == two_fix)
    check("consumer_two_fix_explicit_exact_order", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(two_fix)}) == two_fix)
    c10 = ("ordinary-direct-plain-cancel-after-source192",)
    selected = generator.parse_args(["--layer", c10[0]])
    check("generator_c10_cli_exact_only_increment", selected.layer_names == c10)
    check("consumer_c10_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(c10)}) == c10)
    ods194 = ("ods-target-comments-after-source193",)
    selected = generator.parse_args(["--layer", ods194[0]])
    check("generator_ods194_cli_exact_only_increment", selected.layer_names == ods194)
    check("consumer_ods194_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(ods194)}) == ods194)
    ods195 = ("ods-comment-preservation-after-source194",)
    selected = generator.parse_args(["--layer", ods195[0]])
    check("generator_ods195_cli_exact_only_increment", selected.layer_names == ods195)
    check("consumer_ods195_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(ods195)}) == ods195)
    odf196 = ("odf-native-conversion-output-after-source195",)
    selected = generator.parse_args(["--layer", odf196[0]])
    check("generator_odf196_cli_exact_only_increment", selected.layer_names == odf196)
    check("consumer_odf196_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(odf196)}) == odf196)
    word197 = ("docx-odt-output-after-source196",)
    selected = generator.parse_args(["--layer", word197[0]])
    check("generator_word197_cli_exact_only_increment", selected.layer_names == word197)
    check("consumer_word197_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(word197)}) == word197)
    reverse198 = ("odf-reverse-output-after-source197",)
    selected = generator.parse_args(["--layer", reverse198[0]])
    check("generator_reverse198_cli_exact_only_increment", selected.layer_names == reverse198)
    check("consumer_reverse198_explicit_exact_only_increment", validator.resolve_layer_names({
        "schema": validator.SCHEMA_EXPLICIT, "layer_names": list(reverse198)}) == reverse198)
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
                   "bounded-current-ask-identity", "necessary-document-clarification-p04",
                   "archive-conversion-failure-provenance-after188",
                   "arj-unix-attribute-types-after-source189",
                   "read-file-reject-write-arguments-after-source189",
                   "archive-conversion-named-target-status-after-source190"):
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

    def delta(previous, current, *, layer_name=layer, **extra):
        request = {"schema": validator.SCHEMA_EXPLICIT, "layer_names": [layer_name],
                   "project_inventory": current,
                   "project_inventory_sha256": validator.digest(validator.encoded(current)),
                   "plugin_set": [], "plugin_additions": [], "project_file_updates": []}
        request.update(extra)
        return request, {"project_files": previous}, {"project_files": current}

    check("new_exact_pair_delta_accepted", validator.check_project_inventory(
        *delta({}, {patch: "a" * 64, manifest: "b" * 64})) == (layer,))
    check("historical_pre_pinned_patch_delta_accepted", validator.check_project_inventory(
        *delta({patch: "a" * 64}, {patch: "a" * 64, manifest: "b" * 64})) == (layer,))
    p04 = "necessary-document-clarification-p04"
    p04_pair = {f"patches/hermes/{p04}.patch": "a" * 64,
                f"patches/hermes/{p04}-manifest.json": "b" * 64}
    check("p04_exact_pair_delta_accepted", validator.check_project_inventory(
        *delta({}, p04_pair, layer_name=p04)) == (p04,))
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
        ("p04_checker_addition_refused", delta({}, dict(p04_pair,
            **{"patches/hermes/check-necessary-document-clarification-p04.py": "c" * 64}),
            layer_name=p04), "transaction_project_delta_changed"),
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
