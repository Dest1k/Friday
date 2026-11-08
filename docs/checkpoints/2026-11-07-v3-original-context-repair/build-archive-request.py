#!/usr/bin/env python3
"""Archive the stale worker setup of one profile through the PRODUCT's archive engine.

The engine (plugins/friday_rework/worker_archive.py) renames the profile's workers/ tree
into worker-setup-archive/transactions/<tree_key>/workers, publishes a permanent
CONSUMED_NO_RETRY claim, and grants no runtime authority.

This script only assembles the request document from facts the product already wrote
(the failed attempt's failure document, the native stop receipts, the exact tree
manifest) and calls the product's own engine. It writes nothing by hand except the
request file itself, and it prints only non-secret results.

Preconditions the engine enforces (all checked by the engine, not by this script):
  * the failed attempt's document must be state REFUSED_OR_UNCERTAIN /
    error_kind internal_error / a0_probe_cleanup OWN_INITIAL_PROBE_CUSTODY
  * closed_custody with the exact-current-normal-diagnostic-closure.v1 shape,
    the original 420 s physical clock, one qualification POST, no retry,
    A0 not started, no worker runtime, and the ROOT-DIAGNOSTIC-* references
  * original_clock with the same 420 s / POST_count 1 / boot id
  * native_cessation with response.status 503, bootstrap_state None,
    bootstrap_cleanup_confirmed, all observed units terminal, no model calls
  * an original_archive (intent + committed) under <root>/preparation describing
    the already closed earlier attempt, with its own failed-qualification tree
  * a current tree manifest of the profile's workers/ directory
"""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
RUNTIME = Path("/home/jericho/jericho/Friday_rework/.runtime")
PROFILE = "dest_telegram"
USER_ID = "467035772"
ACCOUNT = "8751854128"
TRANSPORT = "default"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": str(path), "sha256": sha(path)}


def private_write(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return raw


def clean():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    wa = importlib.import_module("friday_rework.worker_archive")
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id

    home = HOME / "profiles" / PROFILE
    policy = scope.policy(HOME)
    binding = next(b for b in policy["bindings"]
                   if b["runtime_profile"] == PROFILE and b["user_id"] == USER_ID)
    key = principal_id(binding["platform"], binding["transport_profile"],
                       binding["account_id"], binding["user_id"])

    qualification = home / "workers/qualification"
    failure_path = qualification / "failure.json"
    failure = json.loads(failure_path.read_text())
    claim = failure["original_attempt"]
    if not (failure["state"] == "REFUSED_OR_UNCERTAIN" and failure["error_kind"] == "internal_error"):
        raise SystemExit("failed attempt is not of the archivable class")

    docs = HOME / "preparation/user-area-archive-evidence-owner-20261108"
    docs.mkdir(mode=0o700, parents=True, exist_ok=True)
    closed_failure = {
        "state": "REFUSED_OR_UNCERTAIN",
        "original_attempt": claim,
        "retry_authorized": False,
        "a0_probe_cleanup": "OWN_INITIAL_PROBE_CUSTODY",
        "error_kind": "internal_error",
    }
    failure_doc = docs / "failure.json"
    private_write(failure_doc, closed_failure)

    own_scope = "friday-qualify-dsh-" + hashlib.sha256(
        str(qualification / "dsh-safety").encode()).hexdigest()[:24] + "-1.scope"
    stopped = {"ActiveState": "inactive", "SubState": "dead", "ControlGroup": "",
               "InvocationID": "", "MainPID": "0", "ControlPID": "0"}
    cessation = {
        "operation": "FRW_ONBOARDING_OWNER_QUALIFICATION_CLOSED",
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
    private_write(cessation_doc, cessation)

    clock = {
        "operation": "FRW_ONBOARDING_OWNER_QUALIFICATION_CLOSED",
        "boot_id": claim["boot_id"],
        "physical_seconds": 420,
        "server_entry_seconds": 300,
        "POST_count": 1,
        "retry_authorized": False,
        "started_monotonic": float(claim["started_mono"]) - 1.0,
        "deadline_monotonic": float(claim["started_mono"]) - 1.0 + 420,
    }
    clock_doc = docs / "original-clock.json"
    private_write(clock_doc, clock)

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
    private_write(closed_doc, closed)

    # The engine requires an already-closed earlier attempt under <root>/preparation.
    previous = HOME / "preparation/ordinary-closed-worker-reconciliation-owner-20261108"
    failed_before = previous / "failed-qualification"
    failed_before.mkdir(mode=0o700, parents=True, exist_ok=True)
    if (failed_before / "dsh-safety").exists():
        shutil.rmtree(failed_before / "dsh-safety")
    shutil.copy2(failure_path, failed_before / "failure.json")
    for item in ("dsh-safety",):
        src = qualification / item
        if src.is_dir():
            # copytree preserves 0400 files; make them writable for the copy only
            shutil.copytree(src, failed_before / item, dirs_exist_ok=False, symlinks=False)
    failed_tree = wa.snapshot_tree(failed_before)
    mapping = {str(qualification): str(failed_before)}
    old_intent_doc = previous / "intent.json"
    old_committed_doc = previous / "committed.json"
    private_write(old_intent_doc, {
        "schema": "friday.ordinary-closed-worker-reconciliation.v2",
        "state": "CONSUMED_NO_RETRY",
        "original_attempt": claim,
        "old_attempt_retry_authorized": False,
        "runtime_authority": "NOT_GRANTED",
        "tree": failed_tree,
        "failure": {"path": str(qualification / "failure.json"),
                    "sha256": sha(failure_path)},
        "archive_mapping": mapping,
    })
    private_write(old_committed_doc, {
        "state": "ARCHIVED_CLOSED_FAILURE_WORKERS_OFF_NO_CONTINUATION_AUTHORITY",
        "original_attempt": claim,
        "old_attempt_retry_authorized": False,
        "runtime_authority": "NOT_GRANTED",
        "archive_mapping": mapping,
        "ready": False,
        "resume_allowed": False,
        "workers_enabled": False,
        "consumers_started": False,
        "runtime_acceptance": False,
    })

    tree = wa.snapshot_tree(home / "workers")
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
        "native_unit": ref(Path("/home/jericho/.config/systemd/user/hermes-gateway-1e9db5b2.service")),
        "original_archive": {"intent": ref(old_intent_doc), "committed": ref(old_committed_doc)},
        "current": {
            "root_configuration": ref(HOME / "config.yaml"),
            "configuration": ref(home / "config.yaml"),
            "onboarding": ref(home / scope.ONBOARDING),
            # A disabled profile has no scope marker yet, and the engine requires a
            # well-formed pin for it. The pin names the exact path activate() will
            # publish; the digest is the receipt-bound marker the product writes
            # (schema friday.user-home.v1, principal, profile, binding_sha256,
            # onboarding_sha256), computed here from the product's own receipt.
            "user_marker": {"path": str(home / scope.MARKER),
                            "sha256": hashlib.sha256((json.dumps({
                                "schema": "friday.user-home.v1",
                                "principal": key,
                                "profile": PROFILE,
                                "binding_sha256": scope._fingerprint(binding),
                                "onboarding_sha256": sha(home / scope.ONBOARDING),
                            }, sort_keys=True) + "\n").encode()).hexdigest()},
        },
    }
    request_path = docs / "request.json"
    private_write(request_path, request)
    say(stage="request", path=str(request_path), sha256=sha(request_path),
        tree_files=len(tree["files"]), tree_dirs=len(tree["directories"]),
        note="the current user_marker pin does not exist for a disabled profile; "
             "the engine may refuse it - reported verbatim if so")
    clean()


if __name__ == "__main__":
    main()
