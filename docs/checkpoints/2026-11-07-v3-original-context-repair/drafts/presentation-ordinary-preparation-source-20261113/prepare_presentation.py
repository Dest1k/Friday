"""Inert, private, single-case scenario preparation; no executor/admission/Store.
Inputs are exact already reviewed draft bytes. Output is NOT a runnable plan.
Root must bind current209 source custody, once, authority and preintent separately.
"""
import hashlib
import json

DRAFT_SHA = "0d278aabe29a3d699644b992225fe2317fcc5a364ab3f6a26c82702ab229a18e"
SOURCE_SHA = "64556440f31c88320569f795020e486f56b9792ceb5fb4908a66797ef0fd780a"
ODP_MIME = "application/vnd.oasis.opendocument.presentation"
OBSERVE = {"mode": "bounded_reply_capture", "window_seconds": 180,
           "max_messages": 64, "max_text_chars": 8000, "max_documents": 1,
           "document_max_bytes": 8 * 1024 * 1024}

def prepare(draft_raw):
    """Pure bytes→private candidate. No file reads/writes, clock or runtime calls."""
    if type(draft_raw) is not bytes or hashlib.sha256(draft_raw).hexdigest() != DRAFT_SHA:
        raise ValueError("EXACT_REVIEWED_PRIVATE_DRAFT_REQUIRED")
    draft = json.loads(draft_raw)
    source = draft["source"]
    if (source["sha256"] != SOURCE_SHA or type(source["bytes"]) is not int
            or source["bytes"] != 48100 or draft["scenario_count"] != 1
            or any(draft[k] is not False for k in ("admitted", "executed", "sent", "formal_accepted"))):
        raise ValueError("EXACT_ORIGINAL_SOURCE_AND_UNEXECUTED_DRAFT_REQUIRED")
    request = draft["request_text_ru"]
    if type(request) is not str or not 1 <= len(request) <= 2000 or not request.strip():
        raise ValueError("BOUNDED_ORIGINAL_NATURAL_REQUEST_REQUIRED")
    scenario = {"tester_id": 8812646969, "peer_id": 8751854128,
                "peer_username": "@jerichodevbot", "deadline_seconds": 300,
                "max_updates": 65, "pace_seconds": 1,
                "steps": [{"request": request, "observe": dict(OBSERVE)}]}
    return {"schema": "frw.private.presentation-forward-preparation.v1",
            "state": "PREPARATION_ONLY_NOT_ADMITTED",
            "scenario": scenario,
            "task_template": {"kind": "ordinary-document-task", "nonce": None,
                              "request": request, "source_reference": None,
                              "output": {"filename": None, "mime_type": ODP_MIME}},
            "source": dict(source),
            "source_product_alias": draft["source_product_alias"],
            "unbound": ["Root exact current209 retained-source adapter",
                        "task_template.nonce", "task_template.source_reference",
                        "current history delta and first-forward once disposition",
                        "actual protected authority and preintent/current proofs",
                        "source alias/principal/CAS and output ownership/absence",
                        "actual operation budget/stop/cleanup ownership"],
            "qualification": "Scenario schema compatibility only. task_template is intentionally invalid for dispatch: null nonce and null retained-source reference are not grants. No future ACK/reply/output needed for preparation; no original effect repeated."}
