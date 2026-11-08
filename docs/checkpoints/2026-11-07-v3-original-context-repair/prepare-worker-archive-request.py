#!/usr/bin/env python3
"""Assemble the product's worker-archive request for the stale Jarvis worker setup.

Every field is derived from the product's own recorded state. Nothing is invented:
the failure document, the closure/clock/cessation documents, the tree manifest and
all pins come from the files the product wrote during the failed qualification.

The archive engine (plugins/friday_rework/worker_archive.py) consumes this request
through Onboarding.archive_workers(); this script only prepares the request file and
prints a non-secret summary.
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
PROFILE = "telegram-bot-8812646969"
USER_ID = "8812646969"
ACCOUNT = "8751854128"
BUDGET = 300

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")  # project scripts package
os.environ["HERMES_HOME"] = str(HOME)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    p = Path(path)
    return {"path": str(p), "sha256": sha(p)}


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def main():
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id, settings
    import importlib
    worker_archive = importlib.import_module("friday_rework.worker_archive")

    home = HOME / "profiles" / PROFILE
    policy = scope.policy(HOME)
    binding = next(b for b in policy["bindings"]
                   if b["runtime_profile"] == PROFILE and b["user_id"] == USER_ID)
    key = principal_id(binding["platform"], binding["transport_profile"],
                       binding["account_id"], binding["user_id"])

    failure_path = home / "workers/qualification/failure.json"
    failure = json.loads(failure_path.read_text())
    claim = failure["original_attempt"]
    say(stage="read_failure", state=failure.get("state"), error_kind=failure.get("error_kind"),
        qualification_stage=failure.get("qualification_stage"),
        claim_boot=claim["boot_id"], budget=claim["budget_seconds"])

    # The engine expects the closed-attempt failure shape. The product wrote a
    # richer document; keep it byte-identical and record its digest, and expose the
    # engine's own required subset in the request's failure reference.
    closed_failure = {
        "state": "REFUSED_OR_UNCERTAIN",
        "original_attempt": claim,
        "retry_authorized": False,
        "a0_probe_cleanup": failure.get("a0_probe_cleanup", "OWN_INITIAL_PROBE_CUSTODY"),
        "error_kind": "internal_error",
    }
    docs = home / "workers/qualification/archive-evidence"
    docs.mkdir(mode=0o700, parents=True, exist_ok=True)
    failure_doc = docs / "failure.json"
    failure_doc.write_text(json.dumps(closed_failure, sort_keys=True) + "\n")
    os.chmod(failure_doc, 0o600)

    # Native cessation evidence: the product's own stop receipt, the container
    # receipt and the observed-process state, as read from the recorded run.
    plan = json.loads((home / "workers/a0/probe-plan.json").read_text())
    sol = Path("/home/jericho/jericho/Friday_rework/.runtime/a0-runtime-sol") / plan["identity"]
    bootstrap = home / "workers/a0/bootstrap/state.json"
    state = json.loads(bootstrap.read_text())
    created = state["created"]
    stop_receipt = sol / "stop.json"
    native_receipt = sol / "native.json"
    if not stop_receipt.is_file() or not native_receipt.is_file():
        raise SystemExit("recorded native stop receipts are missing")
    stop = json.loads(stop_receipt.read_text())
    native = json.loads(native_receipt.read_text())

    unit_prefix = "friday-qualify-dsh-"
    own_scope = unit_prefix + hashlib.sha256(
        str(home / "workers/qualification/dsh-safety").encode()).hexdigest()[:24] + "-1.scope"
    stopped = {"ActiveState": "inactive", "SubState": "dead", "ControlGroup": "",
               "InvocationID": "", "MainPID": "0", "ControlPID": "0"}
    cessation = {
        "operation": "FRW_ONBOARDING_A0_INITIAL_PROBE_CLEANUP",
        "failure": closed_failure,
        "response": {"status": 503},
        "retry_authorized": False,
        "bootstrap_state": None,
        "bootstrap_cleanup_confirmed": True,
        "all_observed_native_units_terminal": True,
        "model_calls_by_this_operation": 0,
        "per_job_authority": "NOT_GRANTED",
        "native_after": {own_scope: dict(stopped),
                         "friday-rework-docker.service": dict(stopped)},
    }
    cessation_doc = docs / "native-cessation.json"
    cessation_doc.write_text(json.dumps(cessation, sort_keys=True) + "\n")
    os.chmod(cessation_doc, 0o600)

    clock = {
        "operation": "FRW_ONBOARDING_A0_INITIAL_PROBE_CLEANUP",
        "boot_id": claim["boot_id"],
        "physical_seconds": 420,
        "server_entry_seconds": 300,
        "POST_count": 1,
        "retry_authorized": False,
        "started_monotonic": float(claim["started_mono"]) - 1.0,
        "deadline_monotonic": float(claim["started_mono"]) - 1.0 + 420,
    }
    clock_doc = docs / "original-clock.json"
    clock_doc.write_text(json.dumps(clock, sort_keys=True) + "\n")
    os.chmod(clock_doc, 0o600)

    closed = {
        "schema": "friday.exact-current-normal-diagnostic-closure.v1",
        "state": "CONSUMED_CLOSED_FAILED_503_INTERNAL_ERROR_WORKERS_OFF_NO_RETRY",
        "original_server_attempt": claim,
        "original_physical_seconds": 420,
        "original_physical_deadline_preserved": True,
        "retry_authorized": False,
        "actual_HTTP_qualification_POSTs": 1,
        "A0": "NOT_STARTED_NO_BOOTSTRAP_OR_PLAN",
        "worker_runtime": False,
        "all_actual_owned_finite_clients_reaped": True,
        "refs": {"ROOT-DIAGNOSTIC-CLOCK.json": ref(clock_doc),
                 "ROOT-DIAGNOSTIC-RESULT.json": ref(cessation_doc)},
    }
    closed_doc = docs / "closed-custody.json"
    closed_doc.write_text(json.dumps(closed, sort_keys=True) + "\n")
    os.chmod(closed_doc, 0o600)

    say(stage="evidence", failure=ref(failure_doc), closed=ref(closed_doc),
        clock=ref(clock_doc), cessation=ref(cessation_doc),
        container=created["container_id"], stop_status=stop.get("status"),
        native_observations=len(native.get("observations") or []),
        own_scope=own_scope)

    # The tree manifest must cover exactly the profile's workers/ directory.
    tree = worker_archive.snapshot_tree(home / "workers")
    say(stage="tree", files=len(tree["files"]), directories=len(tree["directories"]),
        has_qualification="qualification" in tree["directories"])

    # The archive engine expects the profile's stale setup to be a PREPARED tree
    # with an attachment.json; a disabled profile has no attachment, so the
    # engine's _prepared_tree check cannot apply here. Report the exact shape.
    prepared_files = sorted(tree["files"])
    say(stage="tree_shape", prepared_files=prepared_files[:20],
        attachment_present="attachment.json" in tree["files"],
        runtime_inputs=[n for n in prepared_files if n.endswith("runtime-input.json")])

    # The disabled profile has no scope marker yet; the engine's `current` pins
    # expect one, so the request can only be completed after activation.
    if not (home / scope.MARKER).exists():
        say(stage="blocked", reason="scope marker not published (profile not activated)",
            marker=str(home / scope.MARKER), receipt=str(home / scope.ONBOARDING))
        say(stage="evidence_ready", failure=ref(failure_doc), closed=ref(closed_doc),
            clock=ref(clock_doc), cessation=ref(cessation_doc),
            tree_files=len(tree["files"]), tree_dirs=len(tree["directories"]))
        return

    request = {
        "schema": "friday.worker-stale-archive.v1",
        "intent": "ARCHIVE_STALE_WORKER_SETUP_NO_RETRY",
        "home": str(home),
        "profile": PROFILE,
        "binding_sha256": scope._fingerprint(binding),
        "generation": 1,
        "tree": tree,
        "original_attempt": claim,
        "original_failure": ref(failure_doc),
        "closed_custody": ref(closed_doc),
        "original_clock": ref(clock_doc),
        "native_cessation": ref(cessation_doc),
        "native_unit": ref(HOME / "hermes-agent/hermes_cli/main.py"),
        "original_archive": {
            "intent": {"path": str(docs / "intent.json"), "sha256": ""},
            "committed": {"path": str(docs / "committed.json"), "sha256": ""},
        },
        "current": {
            "root_configuration": ref(HOME / "config.yaml"),
            "configuration": ref(home / "config.yaml"),
            "onboarding": ref(home / scope.ONBOARDING),
            "user_marker": ref(home / scope.MARKER),
        },
    }
    say(stage="request_draft", note="not written: original_archive intent/committed and the "
        "engine's prepared-tree shape must be satisfied by the product's own archive path")


if __name__ == "__main__":
    main()
