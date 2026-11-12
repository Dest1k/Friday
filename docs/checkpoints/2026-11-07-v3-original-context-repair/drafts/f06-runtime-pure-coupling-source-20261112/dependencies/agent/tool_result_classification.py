"""Shared helpers for classifying tool result payloads."""

from __future__ import annotations

import json
from typing import Any


FILE_MUTATING_TOOL_NAMES = frozenset({"write_file", "patch"})


# Tools whose interrupted/dangling execution is safe to discard because they
# cannot mutate either external state or Hermes session state. Unknown/plugin/
# MCP tools stay effect-capable by default.
NO_EFFECT_TOOL_NAMES = frozenset({
    "read_file", "search_files", "session_search", "skill_view", "skills_list",
    "web_extract", "web_search", "vision_analyze", "browser_snapshot",
    "browser_get_images", "browser_console", "read_terminal",
})


def tool_may_have_side_effect(tool_name: str) -> bool:
    return tool_name not in NO_EFFECT_TOOL_NAMES


def tool_call_identity(call: Any) -> tuple[str, str]:
    """Read pairing identity only; model arguments and disposition claims are data."""
    if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
        return "", ""
    call_id, name = call.get("id"), call["function"].get("name")
    return (call_id if isinstance(call_id, str) else "",
            name if isinstance(name, str) else "")


def tool_effects_unknown(rows, *, no_dispatch_tool_calls=(), pending_calls=True) -> bool:
    """Reduce native transcript metadata without reading model/tool payloads.

    ``none`` is an execution-owned top-level result column, never a claim from
    arguments/content or an assistant row. Only the native privacy pre-dispatch
    boundary supplies ``no_dispatch_tool_calls``; those exact identities are not
    transcript/model input. Missing, duplicate or inconsistent evidence is unsafe.
    ``pending_calls=False`` is only for progress before a batch has finished.
    """
    if not isinstance(no_dispatch_tool_calls, (list, tuple)):
        return True
    denied = {tuple(item) for item in no_dispatch_tool_calls
              if isinstance(item, (list, tuple)) and len(item) == 2
              and all(isinstance(value, str) and value for value in item)}
    calls, results = {}, set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("role") == "assistant" and row.get("tool_calls"):
            if not isinstance(row["tool_calls"], list):
                return True
            for call in row["tool_calls"]:
                call_id, name = tool_call_identity(call)
                if not call_id or not name or call_id in calls:
                    return True
                calls[call_id] = name
        elif row.get("role") == "tool":
            call_id = row.get("tool_call_id")
            if not isinstance(call_id, str) or call_id not in calls or call_id in results:
                return True
            results.add(call_id)
            name = calls[call_id]
            if any(row.get(key) and row[key] != name for key in ("name", "tool_name")):
                return True
            disposition = row.get("effect_disposition")
            if disposition == "none":
                continue
            # A readonly handler name does not certify opaque native middleware,
            # hooks or callbacks around it. Missing execution proof stays unknown.
            return True
    return bool(pending_calls and any(
        call_id not in results and (call_id, name) not in denied
        for call_id, name in calls.items()
    ))


# Set by a tool that REFUSED a call the harness judged redundant (repeated identical
# read/search). The body still carries ``"error"`` so the model reads it as a stop
# signal, but nothing failed: failure classifiers must not count it, or the cheap
# refusal feeds the streak that fires ``repeated_exact_failure_block``.
GUARDRAIL_REFUSAL_KEY = "guardrail_refusal"


def is_guardrail_refusal(result: Any) -> bool:
    """Return True when ``result`` (JSON string or parsed dict) is a harness refusal."""
    data = result
    if isinstance(result, str):
        try:
            data = json.loads(result.strip())
        except Exception:
            return False
    return isinstance(data, dict) and data.get(GUARDRAIL_REFUSAL_KEY) is True


def file_mutation_result_landed(tool_name: str, result: Any) -> bool:
    """Return True when a file mutation result proves the write landed."""
    if tool_name not in FILE_MUTATING_TOOL_NAMES or not isinstance(result, str):
        return False
    try:
        data = json.loads(result.strip())
    except Exception:
        return False
    if not isinstance(data, dict) or data.get("error"):
        return False
    if tool_name == "write_file":
        return "bytes_written" in data
    if tool_name == "patch":
        return data.get("success") is True
    return False
