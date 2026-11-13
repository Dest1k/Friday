"""Finite own constructor + exact extracted selected tester schema checks only."""
import copy
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024**2, 100 * 1024**2))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
B = Path(__file__).parent

def audit(event, args):
    if event.startswith(("socket.", "subprocess.", "os.system", "os.spawn", "os.exec", "os.fork")):
        raise RuntimeError("NO_PRODUCT_OR_EXTERNAL_PROCESS_OR_NETWORK")
    if event == "open":
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (1 | 2 | 64 | 512 | 1024)):
            if not isinstance(path, (str, bytes)) or Path(path).resolve().parent != B.resolve():
                raise RuntimeError("OWN_REPORT_WRITES_ONLY")
sys.addaudithook(audit)
started = time.monotonic()
ns = {"__file__": str(B / "prepare_presentation.py")}
exec(compile((B / "prepare_presentation.py").read_bytes(), ns["__file__"], "exec"), ns)
pure = {"__file__": str(B / "ordinary-consumer/selected_schema.py")}
exec(compile((B / "ordinary-consumer/selected_schema.py").read_bytes(), pure["__file__"], "exec"), pure)
draft_path = Path("/home/jericho/.cache/FRW-ASTRA-V3-PPTX-ODP-FIRST-SOURCE-ORACLE-20261111/FIRST-SCENARIO-DRAFT.private.json")
draft = draft_path.read_bytes()
candidate = ns["prepare"](draft)
checks = []
def ok(name, condition):
    if not condition: raise AssertionError(name)
    checks.append({"name": name, "status": "PASS"})
def refuses(name, fn):
    try: fn()
    except (ValueError, pure["Refused"]):
        checks.append({"name": name, "status": "REFUSED_AS_REQUIRED"})
    else: raise AssertionError(name)
ok("actual_pinned_draft_to_exact_frozen_candidate", candidate == json.loads((B / "CANDIDATE.private.json").read_bytes()))
ok("actual_selected_tester_scenario", pure["validate_scenario"](candidate["scenario"]) == candidate["scenario"])
ok("actual_selected_ODP_output_contract", pure["ordinary_document_outputs"](candidate["task_template"]["output"]) == [candidate["task_template"]["output"]])
ok("unbound_nonce_and_retained_source_no_grant", candidate["task_template"]["nonce"] is None and candidate["task_template"]["source_reference"] is None and candidate["state"] == "PREPARATION_ONLY_NOT_ADMITTED")
ok("no_upload_no_output_or_ack_inputs", set(candidate["scenario"]["steps"][0]) == {"request", "observe"} and "ACK" not in candidate)
refuses("modified_draft_refused_not_new_permission", lambda: ns["prepare"](draft + b" "))
refuses("python_bytearray_not_exact_bytes", lambda: ns["prepare"](bytearray(draft)))
refuses("wrong_draft_type", lambda: ns["prepare"](draft.decode()))
bad = copy.deepcopy(candidate["scenario"]); bad["steps"][0]["observe"]["future_sha256"] = "0" * 64
refuses("future_result_hash_not_preparation_requirement", lambda: pure["validate_scenario"](bad))
bad = copy.deepcopy(candidate["scenario"]); bad["deadline_seconds"] = 184
refuses("full180_plus_cleanup_reserve_enforced", lambda: pure["validate_scenario"](bad))
bad = copy.deepcopy(candidate["scenario"]); bad["steps"][0]["observe"]["max_documents"] = True
refuses("capture_count_bool_refused_by_actual_tester", lambda: pure["validate_scenario"](bad))
bad = copy.deepcopy(candidate["scenario"]); bad["steps"][0]["observe"]["max_messages"] = 66
refuses("capture_capacity_over_budget_refused", lambda: pure["validate_scenario"](bad))
refuses("wrong_native_output_MIME", lambda: pure["ordinary_document_outputs"]({"filename": None, "mime_type": "application/not-odp"}))
refuses("misleading_output_suffix", lambda: pure["ordinary_document_outputs"]({"filename": "result.pptx", "mime_type": ns["ODP_MIME"]}))
result = {"schema": "frw.presentation.finite-preparation-checks.v1", "status": "PASS_SOURCE_AND_SCHEMA_ONLY", "checks": checks, "count": len(checks), "elapsed_wall_seconds": time.monotonic() - started, "limits": {"CPU_seconds": 120, "AS_bytes": 512 * 1024**2, "FSIZE_bytes": 100 * 1024**2, "CORE": 0}, "execution": "Own pure constructor and exact extracted actual tester schema bodies only. Audit denies external processes/network/foreign writes; no full tester/product module import/Runner/Store/native current proof.", "not_proven": ["ordinary caller/admission/current209 retained-source adaptation", "actual receipt/custody/full180/semantic or formalPASS"], "pins": {}}
for path in [B / "prepare_presentation.py", B / "CANDIDATE.private.json", B / "ordinary-consumer/selected_schema.py", draft_path]:
    raw = path.read_bytes(); result["pins"][str(path)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
p = B / "PREPARATION-CHECKS.json"; p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n"); p.chmod(0o600)
print(json.dumps({"status": result["status"], "count": len(checks), "elapsed_wall_seconds": result["elapsed_wall_seconds"]}))
