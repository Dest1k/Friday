#!/usr/bin/env python3
"""Session Search Tool - long-term conversation recall over the SQLite session DB.

Single-shape tool; the mode is inferred from the args: DISCOVERY (``query``;
FTS5 deduped by lineage, adaptive detail hydrates only the top result),
SCROLL (``session_id`` + ``around_message_id``; ±window around the anchor),
READ (``session_id`` alone; whole session or head/tail), BROWSE (no args).
No LLM calls — every shape returns actual DB messages.
"""

import json
import logging
import re
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from hermes_state_common import _BOUNDARY_END_REASONS
from hermes_state_errors import SessionSearchIndexStatusError
from hermes_time import safe_strftime

# Hidden from browsing/searching — integrations (HERMES_SESSION_SOURCE=tool), delegate
# subagent runs, kanban workers are not the user's history.
_HIDDEN_SESSION_SOURCES = ("kanban", "subagent", "tool")
# Searchable but DEMOTED below interactive sessions: cron vocabulary dominates bare
# BM25 and starves out the user's own sessions ("recall blindness").
# Automation sources that are kept searchable but DEMOTED below interactive sessions in discover ranking.
# Cron jobs run on a schedule and accumulate large volumes of repetitive vocabulary (recurring project
# names, dates, "session", summaries); under bare BM25 they dominate the top-N FTS rows and starve out the
# user's own interactive sessions, producing "recall blindness" where only cron sessions surface (#19434).
# Demoting — not excluding — keeps cron content reachable when it's the only match, while interactive
# sessions always win when both match.
_DEMOTED_SESSION_SOURCES = ("cron",)

# Read-shape per-message content cap. #69334 capped discovery bookends (1200) and
# scroll windows (4000) but left ``_read_session`` returning whole messages, so a
# single archived tool result stored as a message could come back verbatim - one
# read returned 74K chars and took a request from ~50K to ~89K tokens in a step.
# Bounding message COUNT (head/tail) is not enough when content per message is
# unbounded; the agent can scroll around a message for detail (#114344).
_READ_MAX_CONTENT = 2000
# Field pages bound UTF-8 text bytes; the response bound includes JSON escaping.
# Neither is a model-token estimate.
_FIELD_MAX_BYTES = 6000
_RESPONSE_MAX_BYTES = 131072
# FTS rows scanned before dedup-by-lineage — well above the distinct sessions a query
# returns, so interactive matches buried under cron hits survive the demotion pass.
_DISCOVER_SCAN_LIMIT = 300
# exclude_session_ids: ids already inspected this task; capped so a runaway list can't fan out lineage walks.
_EXCLUDE_SESSION_IDS_CAP = 20
# Relative time bounds: "7d" / "24h" / "2w" = now minus N hours/days/weeks.
_RELATIVE_BOUND_RE = re.compile(r"^(\d+)\s*(h|d|w)$", re.IGNORECASE)
_RELATIVE_UNIT_SECONDS = {"h": 3600, "d": 86400, "w": 604800}
# Raw FTS rows are only a plan input; the response hydrates its own window/bookends.
_DISCOVER_SEARCH_FIELDS = ("id", "session_id", "role", "snippet", "source", "model", "session_started")
# Compaction handoff summaries (agent/context_compressor.py); excluded from bookends.
_COMPACTION_PREFIXES = ("[CONTEXT COMPACTION", "[CONTEXT SUMMARY]:")
# /new, /reset, idle/daily expiry and CLI /new ("new_session") end the predecessor WITHOUT
# carrying its transcript forward — unlike compression continuations and live delegation
# children. The store's boundary set, so the two cannot drift.
_FRESH_RESET_END_REASONS = _BOUNDARY_END_REASONS
_DISCOVERY_FAILURE = ContextVar('session_search_discovery_failure', default=None)


def _note_discovery_fault():
    budget = _DISCOVERY_FAILURE.get()
    if budget is not None:
        budget.failed = budget.failed or 'discovery_data_failed'


def _quiet(fn, default, msg, *log_args, with_exc: bool = False):
    """``fn()``, or *default* after debug-logging *msg* (+ the exception when *with_exc*)."""
    try:
        return fn()
    except Exception as e:
        _note_discovery_fault()
        logging.debug(msg, *(log_args + (e,) if with_exc else log_args), exc_info=True)
        return default


def _loud(fn, log_msg, error_prefix, *log_args):
    """``(fn(), None)``, or ``(None, tool_error_json)`` after an error-level log — for DB
    calls whose failure the model must see."""
    try:
        return fn(), None
    except SessionSearchIndexStatusError:
        # search_messages also reads rebuild status (including its gap fallback).
        # Preserve the typed failure when it occurs before response assembly.
        logging.warning("session_search index status read failed")
        return None, _index_status_error()
    except Exception as e:
        logging.error(log_msg, *log_args, e, exc_info=True)
        return None, tool_error(f"{error_prefix}: {e}", success=False)


def _format_timestamp(ts: Union[int, float, str, None]) -> str:
    """Unix timestamp -> readable date; ISO strings pass through; "unknown" for None."""
    if ts is None:
        return "unknown"
    if isinstance(ts, str) and not ts.replace(".", "").replace("-", "").isdigit():
        return ts
    return _quiet(lambda: safe_strftime(datetime.fromtimestamp(float(ts)), "%B %d, %Y at %I:%M %p"), str(ts),
                  "Failed to format timestamp %s: %s", ts, with_exc=True)


def _get_session_meta(db, session_id: str) -> dict:
    """``db.get_session`` that degrades to ``{}`` on error."""
    return _quiet(lambda: db.get_session(session_id), None,
                  "get_session failed for %s: %s", session_id, with_exc=True) or {}


def _session_meta_block(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {"when": _format_timestamp(meta.get("started_at")), "source": meta.get("source"),
            "model": meta.get("model"), "title": meta.get("title")}


def _utf8_prefix(text: str, limit: int) -> str:
    return text.encode('utf-8')[:limit].decode('utf-8', errors='ignore')


def _json_field_page(value, offset: int, limit: int):
    """A bounded page of canonical JSON, with character offsets for exact recovery."""
    result, consumed, used, more = [], 0, 0, False
    for chunk in json.JSONEncoder(ensure_ascii=False, separators=(',', ':')).iterencode(value):
        end = consumed + len(chunk)
        if end <= offset:
            consumed = end
            continue
        remaining = chunk[max(0, offset - consumed):]
        piece = _utf8_prefix(remaining, limit - used)
        result.append(piece)
        used += len(piece.encode('utf-8'))
        consumed = end
        if len(piece) < len(remaining):
            more = True
            break
    text = ''.join(result)
    if offset and not text:
        raise ValueError('field_offset must point inside the requested field')
    return text, more


def _message_pages(value):
    if isinstance(value, dict):
        if 'id' in value and 'role' in value and 'content' in value:
            yield value
        else:
            for child in value.values():
                yield from _message_pages(child)
    elif isinstance(value, list):
        for child in value:
            yield from _message_pages(child)


def _ok(**payload) -> str:
    result = {'success': True, **payload}
    encode = lambda: json.dumps(result, ensure_ascii=False)
    text = encode()
    if len(text.encode('utf-8')) <= _RESPONSE_MAX_BYTES:
        return text
    # Keep every message/session anchor. Detailed text can be recovered through
    # scroll, including tool-call JSON. Never spill another user's data to disk.
    # Keep a positive page so following next_*_offset always makes progress.
    # Metadata that cannot fit even with small pages receives the typed refusal.
    for limit in (512, 128, 32):
        for message in _message_pages(result):
            content = message.get('content')
            if isinstance(content, str) and len(content.encode('utf-8')) > limit:
                prefix = _utf8_prefix(content, limit)
                message['content'] = prefix
                message['content_truncated'] = True
                message['next_content_offset'] = message.get('content_offset', 0) + len(prefix)
            if 'tool_calls' in message:
                page, more = _json_field_page(message.pop('tool_calls'), 0, limit)
                message.update(tool_calls_page=page, tool_calls_offset=0,
                               tool_calls_truncated=more, tool_calls_encoding='json',
                               tool_calls_offset_unit='unicode_characters')
                if more:
                    message['next_tool_calls_offset'] = len(page)
            elif len(message.get('tool_calls_page', '').encode('utf-8')) > limit:
                page = _utf8_prefix(message['tool_calls_page'], limit)
                message.update(tool_calls_page=page, tool_calls_truncated=True,
                               next_tool_calls_offset=message.get('tool_calls_offset', 0) + len(page))
        result['response_truncated'] = True
        result['response_byte_limit'] = _RESPONSE_MAX_BYTES
        text = encode()
        if len(text.encode('utf-8')) <= _RESPONSE_MAX_BYTES:
            return text
    return json.dumps({'success': False, 'error': 'session_search_response_too_large',
                       'response_byte_limit': _RESPONSE_MAX_BYTES})


def _is_compaction_summary(content: str) -> bool:
    return bool(content) and content.lstrip().startswith(_COMPACTION_PREFIXES)


def _resolve_to_parent(db, session_id: str) -> tuple[str, bool]:
    """Walk parent_session_id to the root -> ``(root_id, has_compression_hop)``; the flag
    separates a compression-split lineage (parent summarised away) from a delegation
    lineage (child still visible to the parent)."""
    visited: set[str] = set()
    cur, has_compression = session_id, False
    while cur and cur not in visited:
        visited.add(cur)
        s = _get_session_meta(db, cur)
        has_compression = has_compression or s.get("end_reason") == "compression"
        if not s.get("parent_session_id"):
            break
        cur = s["parent_session_id"]
    return cur, has_compression


def _resolve_lineage(db, session_id: str) -> str:
    return _resolve_to_parent(db, session_id)[0]


def _parse_iso_bound(value: Optional[str]) -> Optional[int]:
    """Parse an ISO date/datetime OR a relative duration into a UTC unix timestamp.

    ISO: a date-only value (``YYYY-MM-DD``) is midnight UTC on that day (the SQL
    ``before`` predicate is exclusive, so ``before=2026-07-01`` keeps June and drops
    July 1 00:00). Relative: ``"7d"``, ``"24h"``, ``"2w"`` = now minus N
    hours/days/weeks, so ``after="7d"`` is the last week and ``before="7d"`` is
    everything older than a week.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if rel := _RELATIVE_BOUND_RE.match(text):
        return int(time.time()) - int(rel.group(1)) * _RELATIVE_UNIT_SECONDS[rel.group(2).lower()]
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"invalid time bound: {value!r} (expected ISO date/datetime like "
                         "2026-07-01, or a relative duration like 7d, 24h, 2w)") from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _coerce_started_ts(value: Any) -> Optional[int]:
    """``sessions.started_at`` as an int unix timestamp (numeric or ISO text); None if unusable."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    try:
        return int(float(text))
    except (TypeError, ValueError):
        pass
    try:
        return _parse_iso_bound(text)
    except ValueError:
        return None


def _in_time_window(started_ts: Optional[int], after_ts: Optional[int], before_ts: Optional[int]) -> bool:
    """``after_ts <= started_ts < before_ts``; an unknown start fails any bound."""
    if after_ts is None and before_ts is None:
        return True
    if started_ts is None:
        return False
    return (after_ts is None or started_ts >= after_ts) and (before_ts is None or started_ts < before_ts)


def _normalize_exclude_session_ids(raw: Any) -> List[str]:
    """Deduped, stripped session ids from a str or list, capped at ``_EXCLUDE_SESSION_IDS_CAP``."""
    items = [raw] if isinstance(raw, str) else list(raw) if isinstance(raw, (list, tuple)) else []
    out: List[str] = []
    for item in items:
        sid = item.strip() if isinstance(item, str) else ""
        if sid and sid not in out:
            out.append(sid)
        if len(out) >= _EXCLUDE_SESSION_IDS_CAP:
            break
    return out


def _excluded_lineage_roots(db, exclude_session_ids: List[str]) -> set[str]:
    """The excluded ids plus their lineage roots, so a child id also hides its parent chain."""
    roots: set[str] = set()
    for sid in exclude_session_ids:
        roots.add(sid)
        roots.add(_resolve_lineage(db, sid) or sid)
    return roots


def _same_lineage(db, a: str, b: str) -> bool:
    a_root = _resolve_lineage(db, a)
    return bool(a_root and a_root == _resolve_lineage(db, b))


def _session_left_live_context(db, session_id: str) -> bool:
    """True when the transcript left everyone's live context: ``compression``
    (summarised into the child) or a fresh reset (child starts empty). Live delegation
    children (``end_reason is None``) and ``branched`` parents (copied verbatim into
    the branch) ARE the current context, so they stay excluded from recall."""
    end_reason = (session_id and _get_session_meta(db, session_id).get("end_reason")) or None
    return end_reason == "compression" or end_reason in _FRESH_RESET_END_REASONS


def _get_message_storage_state(db, message_id) -> Optional[Dict[str, Any]]:
    """Owning session and visibility flags for *message_id* (None if missing/error)."""
    def _lookup():
        with db._lock:
            return db._conn.execute(
                "SELECT session_id, active, compacted FROM messages WHERE id = ?", (message_id,)).fetchone()
    row = message_id and _quiet(_lookup, None, "message storage-state lookup failed for %s", message_id)
    return dict(row) if row else None


def _is_compacted_state(state: Optional[Dict[str, Any]]) -> bool:
    """Compaction archives are ``active=0, compacted=1``; rewind/undo rows are
    ``active=0, compacted=0`` and must stay hidden."""
    return state is not None and state["active"] == 0 and state["compacted"] == 1


def _is_compacted_message(db, message_id) -> bool:
    """True for a compaction-archived row: no longer in live context, so discoverable
    even on the current session. False on any error."""
    return _is_compacted_state(_get_message_storage_state(db, message_id))


def _shape_message(m: Dict[str, Any], anchor_id: Optional[int] = None,
                   max_content_len: Optional[int] = None, content_offset: int = 0,
                   message_field: str = 'content') -> Dict[str, Any]:
    """Slim a message row; keeps ``content`` even when empty (tool-call-only turns)."""
    content = m.get("content")
    if isinstance(content, str) and "\x1b" in content:  # archived terminal output carries ANSI
        from tools.ansi_strip import strip_ansi
        content = strip_ansi(content)
    entry = {"id": m.get("id"), "role": m.get("role"), "content": content, "timestamp": m.get("timestamp")}
    entry.update({k: m.get(k) for k in ('tool_name', 'tool_call_id') if m.get(k)})
    if m.get('tool_calls'):
        offset = content_offset if message_field == 'tool_calls' else 0
        page, more = _json_field_page(m['tool_calls'], offset, _FIELD_MAX_BYTES)
        if not offset and not more and message_field == 'content':
            entry['tool_calls'] = m['tool_calls']
        else:
            entry.update(tool_calls_page=page, tool_calls_offset=offset,
                         tool_calls_truncated=more, tool_calls_encoding='json',
                         tool_calls_offset_unit='unicode_characters')
            if more:
                entry['next_tool_calls_offset'] = offset + len(page)
    elif message_field == 'tool_calls':
        raise ValueError('anchor has no tool_calls field')
    if anchor_id is not None and m.get("id") == anchor_id:
        entry["anchor"] = True
    content_offset = content_offset if message_field == 'content' else 0
    if content_offset and (not isinstance(content, str) or content_offset >= len(content)):
        raise ValueError("content_offset must point inside the anchor message text")
    if isinstance(content, str) and (content_offset or (max_content_len and len(content) > max_content_len)
                                    or len(content.encode('utf-8')) > _FIELD_MAX_BYTES):
        max_content_len = max_content_len or len(content)
        end = min(len(content), content_offset + max_content_len)
        piece = _utf8_prefix(content[content_offset:end], _FIELD_MAX_BYTES)
        end = content_offset + len(piece)
        entry.update(content=piece + ("…" if end < len(content) else ""),
                     content_truncated=True, original_content_chars=len(content),
                     content_offset=content_offset)
        if end < len(content):
            entry["next_content_offset"] = end
    return {k: v for k, v in entry.items() if v is not None or k == "content"}


def _session_link(session_id: str, profile: str = None) -> str:
    """The reference the agent writes for a session — same value the desktop composer
    emits, so it renders as a titled link. The profile segment is omitted when it
    can't be named confidently (a bare id still resolves, just not across profiles)."""
    from hermes_cli.friday_user_scope import ordinary_presentation
    if ordinary_presentation():
        return f"@session:{session_id}"
    def _active():
        from hermes_cli.profiles import get_active_profile_name
        resolved = get_active_profile_name()
        return "" if resolved == "custom" else resolved
    name = (profile or "").strip() or _quiet(_active, "", "get_active_profile_name failed for session link")
    return f"@session:{name}/{session_id}" if name else f"@session:{session_id}"


def _discovery_entry(lineage_root: Optional[str], **fields) -> Dict[str, Any]:
    """Canonical key order; ``parent_session_id`` set when the hit lives in a child."""
    entry = {k: fields[k] for k in (
        "session_id", "when", "source", "model", "title", "matched_role", "match_message_id", "snippet",
        "bookend_start", "messages", "bookend_end", "messages_before", "messages_after", "detail",
        "match_provenance")}
    if lineage_root and lineage_root != entry["session_id"]:
        entry["parent_session_id"] = lineage_root
    return entry


def _match_provenance(db, session_id: str, message_id, view: dict,
                      current_session_id: Optional[str]) -> dict:
    """Separate the raw hit's dates/context from the logical lineage metadata."""
    anchor = next((m for m in view.get("window", []) if m.get("id") == message_id), {})
    storage_state = _get_message_storage_state(db, message_id)
    return {
        "result_when_scope": "lineage_root_session_start",
        "session_when": _format_timestamp(_get_session_meta(db, session_id).get("started_at")),
        "message_when": _format_timestamp(anchor.get("timestamp")),
        "is_current_session": session_id == current_session_id if current_session_id else None,
        "compaction_archived": None if storage_state is None else _is_compacted_state(storage_state),
    }


def _title_match_result(db, query: str, current_lineage_root: Optional[str],
                        current_session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Discovery-shaped result when the query matches a session title, else None."""
    title_query = query.strip().strip("`'\"")  # models often quote a remembered title
    session_id = title_query and _quiet(lambda: db.resolve_session_by_title(title_query), None,
                                        "resolve_session_by_title failed for %r", title_query)
    if not session_id:
        return None
    lineage_root = _resolve_lineage(db, session_id)
    # Same-lineage title hits are in-context only while the session is live;
    # /new-reset and compression-ended parents are not.
    if current_lineage_root and lineage_root == current_lineage_root and not _session_left_live_context(db, session_id):
        return None
    session_meta = _quiet(lambda: db.get_session(lineage_root) or db.get_session(session_id), None,
                          "get_session failed for title match %s", session_id) or {}
    if session_meta.get("source") in _HIDDEN_SESSION_SOURCES:
        return None
    page = _quiet(lambda: db.get_session_recall_page(session_id, head=5, tail=3), {},
                  'get_session_recall_page failed for title match %s', session_id)
    messages = page.get('messages', [])
    anchor_id = messages[0].get("id") if messages else None
    view = {} if anchor_id is None else _quiet(
        lambda: db.get_anchored_view(session_id, anchor_id, window=5, bookend=3), {},
        "get_anchored_view failed for title match %s/%s", session_id, anchor_id)
    title = session_meta.get("title") or title_query
    # Same caps as FTS hits (_bookend / _hydrate_hit): a title match is a discovery entry too.
    def shape(key, fallback, anchor=None, max_content_len=1200):
        return [_shape_message(m, anchor_id=anchor, max_content_len=max_content_len)
                for m in (view.get(key) or fallback)]
    return {**_discovery_entry(
        lineage_root, session_id=session_id, when=_format_timestamp(session_meta.get("started_at")),
        source=session_meta.get("source", "unknown"), model=session_meta.get("model") or "unknown",
        title=title, matched_role="session_title", match_message_id=anchor_id,
        snippet=f"Session title matched: {title}",
        bookend_start=shape("bookend_start", messages[:3]),
        messages=shape("window", messages[:5], anchor_id, max_content_len=4000),
        bookend_end=shape("bookend_end", messages[-3:]), messages_before=view.get("messages_before", 0),
        messages_after=view.get("messages_after", max(page.get('message_count', len(messages)) - 5, 0)), detail="full",
        match_provenance=_match_provenance(db, session_id, anchor_id, view, current_session_id)),
        "_lineage_root": lineage_root}


def _index_status_observation(read_ok: bool, state: str) -> dict:
    """A rebuild-marker observation, explicitly not a content or query-snapshot proof."""
    return {"read_ok": read_ok, "state": state, "scope": "base_rebuild_markers",
            "observation_phase": "after_discovery_reads" if read_ok else "not_completed",
            "query_snapshot_binding": "NOT_ESTABLISHED", "completeness": "NOT_ESTABLISHED"}


def _index_status_error() -> str:
    return tool_error("session_search_index_status_failed", success=False,
                      index_status=_index_status_observation(False, "unknown"))


def _discover_payload(db, query: str, detail: str, results: list, **extra) -> str:
    """Discovery response; notes FTS backfill progress so the agent can explain thin
    results instead of treating them as ground truth."""
    try:
        status = db.fts_rebuild_status()
        if status is not None:
            if (not isinstance(status, dict) or status.get("pending") is not True
                    or any(type(status.get(k)) is not int for k in ("total", "indexed", "percent"))
                    or status["total"] <= 0 or not 0 <= status["indexed"] <= status["total"] <= (1 << 63) - 1
                    or status["percent"] != 100 * status["indexed"] // status["total"]):
                raise ValueError("invalid base rebuild status")
    except Exception:  # health: allow BLE001 -- Unknown marker-read faults must yield a typed refusal without disclosing private traceback data.
        logging.warning("session_search index status read failed")
        return _index_status_error()
    observation = _index_status_observation(True, "pending" if status is not None else "no_pending")
    rebuild = {} if status is None else {"index_rebuild": {"percent": status["percent"], "note": (
        f"The search index is rebuilding in the background ({status['percent']}% done, "
        f"{status['indexed']:,} of {status['total']:,} messages). Results from older messages "
        f"may be incomplete until it finishes.")}}
    return _ok(mode="discover", query=query, detail=detail, results=results, count=len(results),
               index_status=observation, **extra, **rebuild)


def _bookend(view: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    return [_shape_message(m, max_content_len=1200) for m in (view.get(key) or [])
            if not _is_compaction_summary(m.get("content", ""))]


def _hydrate_hit(db, lineage_root: str, match_info: Dict[str, Any], result_detail: str,
                 current_session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Discovery result from a surviving FTS row; None (dropped) if the view can't load."""
    hit_sid, msg_id = match_info.get("session_id") or lineage_root, match_info.get("id")
    try:
        view = db.get_anchored_view(hit_sid, msg_id, window=5, bookend=3)
    except Exception as e:
        _note_discovery_fault()
        logging.warning("get_anchored_view failed for %s/%s: %s", hit_sid, msg_id, e, exc_info=True)
        return None
    session_meta, full = _get_session_meta(db, lineage_root), result_detail == "full"
    return _discovery_entry(
        lineage_root, session_id=hit_sid,
        when=_format_timestamp(session_meta.get("started_at") or match_info.get("session_started")),
        source=session_meta.get("source") or match_info.get("source", "unknown"),
        model=session_meta.get("model") or match_info.get("model") or "unknown",
        title=session_meta.get("title") or None, matched_role=match_info.get("role"),
        match_message_id=msg_id, snippet=match_info.get("snippet") or "",
        bookend_start=_bookend(view, "bookend_start") if full else [],
        messages=[_shape_message(m, anchor_id=msg_id, max_content_len=4000)
                  for m in (view.get("window") or []) if full or m.get("id") == msg_id],
        bookend_end=_bookend(view, "bookend_end") if full else [],
        messages_before=view.get("messages_before", 0), messages_after=view.get("messages_after", 0),
        detail=result_detail, match_provenance=_match_provenance(
            db, hit_sid, msg_id, view, current_session_id))


def _discover_impl(db, query: str, role_filter: Optional[List[str]], limit: int, sort: Optional[str],
              detail: str, current_session_id: str = None, link_profile: str = None,
              after_ts: Optional[int] = None, before_ts: Optional[int] = None,
              exclude_session_ids: Optional[List[str]] = None) -> str:
    """Discovery shape: FTS5 plus adaptive or full result hydration."""
    current_lineage_root = _resolve_lineage(db, current_session_id) if current_session_id else None
    excluded_roots = _excluded_lineage_roots(db, exclude_session_ids or [])
    title_result = _title_match_result(db, query, current_lineage_root, current_session_id)
    # FTS rows are time-bounded in SQL (_search_filter_clauses); the title match bypasses that
    # query, so it is the one place the window is re-checked in Python.
    if title_result:
        title_sid, title_root = title_result["session_id"], title_result.get("_lineage_root") or title_result["session_id"]
        title_started = _coerce_started_ts((_get_session_meta(db, title_root) or _get_session_meta(db, title_sid)).get("started_at"))
        if {title_sid, title_root} & excluded_roots or not _in_time_window(title_started, after_ts, before_ts):
            title_result = None
    raw_results, err = _loud(lambda: db.search_messages(
        query=query, role_filter=role_filter or ["user", "assistant"],
        exclude_sources=list(_HIDDEN_SESSION_SOURCES), limit=_DISCOVER_SCAN_LIMIT, offset=0, sort=sort,
        fields=_DISCOVER_SEARCH_FIELDS, after_ts=after_ts, before_ts=before_ts), "FTS5 search failed: %s", "Search failed")
    if err:
        return err
    # Demote cron rows below interactive ones BEFORE dedup so a high-volume cron corpus
    # can't starve the user's own sessions out of the top `limit`; stable sort keeps BM25
    # order within each class.
    raw_results = sorted(raw_results, key=lambda r: (r.get("source") or "") in _DEMOTED_SESSION_SOURCES)
    # See #19434.
    if not raw_results and not title_result:
        return _discover_payload(db, query, detail, [], message=(
            "No matching sessions returned; index completeness is not established. "
            "FTS5 ANDs all terms by default — "
            "broaden with OR (`alpha OR beta`), exact-match with quoted "
            "phrases, exclude with NOT, or prefix-match with `deploy*`."))
    seen_sessions: Dict[str, Dict[str, Any]] = {}
    results = [title_result] if title_result else []
    if title_result and (title_lineage := title_result.pop("_lineage_root", None)):
        seen_sessions[title_lineage] = {"_title_only": True}
    # Dedupe by lineage (lineage_root -> first surviving FTS row) up to `limit`. The raw
    # owning session_id stays on the row — only it pairs validly with the FTS match id.
    # Current-lineage hits are skipped UNLESS the transcript left live context
    # (compression-ended, /new-reset predecessor, or an in-place compacted row on the
    # SAME session); a live delegation child (end_reason=None) stays excluded.
    for r in raw_results:
        if len(seen_sessions) >= limit:
            break
        raw_sid, resolved_sid = r["session_id"], _resolve_lineage(db, r["session_id"])
        if raw_sid in excluded_roots or resolved_sid in excluded_roots:
            continue
        # Skip the current session lineage — UNLESS the hit's transcript has left live context. Three
        # sub-cases: Legacy compression rotation: the FTS hit lives in a session that itself ended with
        # end_reason='compression'. That session's content has been replaced by a summary in the
        # continuation child, so it must stay discoverable. /new-reset (and idle/daily/CLI new_session): the
        # predecessor was ended without carrying any transcript into the child. Same lineage root, but the
        # prior conversation is NOT in the active context — hiding it made gateway recall go blind after
        # every /new (#85756). A live delegation child has end_reason=None, so it stays excluded. In-place
        # compaction: the FTS hit lives on the SAME session_id as the current session, but the matched
        # message row is an archived (active=0, compacted=1) row. The live-context load filters active=1, so
        # that content is no longer in context — let it through.
        is_compacted_hit = _is_compacted_message(db, r.get("id"))
        if current_lineage_root and resolved_sid == current_lineage_root and not (
                _session_left_live_context(db, raw_sid) or is_compacted_hit):
            continue
        if current_session_id and raw_sid == current_session_id and not is_compacted_hit:
            continue
        seen_sessions.setdefault(resolved_sid, {**r, "_lineage_root": resolved_sid})
    for lineage_root, match_info in seen_sessions.items():
        if match_info.get("_title_only"):
            continue
        # Adaptive: only the top-ranked result is fully hydrated.
        entry = _hydrate_hit(db, lineage_root, match_info, "full" if detail == "full" or not results else "compact",
                             current_session_id)
        if entry is not None:
            results.append(entry)
    for entry in results:
        entry["link"] = _session_link(entry["session_id"], link_profile)
    return _discover_payload(db, query, detail, results, sessions_searched=len(seen_sessions), link_hint=(
        "When referring the user to a session, write its `link` value "
        "verbatim inline mid-sentence (it renders as a titled link) — never "
        "as markdown, in backticks, on its own line, or next to the "
        "title/id/date. To read more around a compact result, scroll: "
        "session_search(session_id=..., around_message_id=match_message_id)."))



def _discover(db, *args, **kwargs) -> str:
    from hermes_cli.friday_user_scope import current
    cap = current()
    if cap is None:
        return _discover_impl(db, *args, **kwargs)
    from hermes_state_search_snapshot import run_discovery_snapshot
    def guarded(snapshot):
        token = _DISCOVERY_FAILURE.set(snapshot._budget)
        try:
            return _discover_impl(snapshot, *args, **kwargs)
        finally:
            _DISCOVERY_FAILURE.reset(token)
    return run_discovery_snapshot(db, cap, guarded)

def _resolve_profile_db(profile: str):
    """Another profile's ``state.db`` opened read-only (safe on a live DB); None = current."""
    if profile is None or not str(profile).strip():
        return None
    from hermes_cli import profiles as profiles_mod
    from hermes_state import SessionDB
    canon = profiles_mod.normalize_profile_name(profile)
    profiles_mod.validate_profile_name(canon)
    if not profiles_mod.profile_exists(canon):
        raise ValueError(f"profile '{canon}' does not exist")
    return SessionDB(db_path=profiles_mod.get_profile_dir(canon) / "state.db", read_only=True)


def _read_session(db, session_id: str, head: int = 20, tail: int = 10, link_profile: str = None) -> str:
    """Read shape: whole session, or ``head`` + ``tail`` messages with a scroll pointer."""
    meta = _get_session_meta(db, session_id)
    if not meta:
        return tool_error(f"session_id not found: {session_id}", success=False)
    page, err = _loud(lambda: db.get_session_recall_page(session_id, head=head, tail=tail), "get_messages failed for %s: %s", "failed to load session",
                      session_id)
    if err:
        return err
    shaped = [_shape_message(m, max_content_len=_READ_MAX_CONTENT) for m in page['messages']]
    total, truncated = page['message_count'], page['truncated']
    return _ok(mode="read", session_id=session_id, link=_session_link(session_id, link_profile),
               session_meta=_session_meta_block(meta), message_count=total, truncated=truncated,
               messages=shaped,
               **({"message": (f"Session has {total} messages; showing first {head} + last {tail}. "
                               "Pass around_message_id (any id above) to scroll the middle.")} if truncated else {}))


def _read_scoped(db, sid: str, profile: Optional[str]) -> str:
    """Read shape scoped to ONE store: the caller's profile, or the profile it named.

    A miss is a miss. Profiles are isolated islands, so a bare id never falls through to
    a scan of every other profile's ``state.db`` — that returned another profile's full
    transcript to any caller holding the id (#106761). The hint tells the model how to
    ask properly: ``@session:<profile>/<id>`` or ``profile=``.
    """
    result = _read_session(db, sid, link_profile=profile)
    if json.loads(result).get("success") is not False or profile:
        return result
    return tool_error(f"session_id not found in this profile: {sid}. If it belongs to another "
                      "profile, pass profile=<name> (or the @session:<profile>/<id> link).", success=False)


def _list_recent_sessions(db, limit: int, current_session_id: str = None, link_profile: str = None) -> str:
    """Browse shape: metadata for the most recent sessions (no LLM, no FTS5)."""
    def _browse():
        # Never use list_sessions_rich(order_by_last_active=True) here: it walks every
        # compression chain and derives activity/previews before LIMIT, which can
        # monopolise a gateway callback for minutes on a multi-GB state.db. The
        # bounded browse query preselects an indexed candidate set and carries a
        # cooperative SQLite VM cancellation deadline. Fail closed rather than
        # silently falling back to the whole-database query shape.
        bounded_list = getattr(db, "list_recent_sessions_bounded", None)
        if bounded_list is None:
            raise RuntimeError("session database does not support bounded recent-session browse")
        sessions = bounded_list(
            limit=limit + 15,  # extra so we can skip current / compression roots
            exclude_sources=list(_HIDDEN_SESSION_SOURCES), timeout_seconds=3.0)
        current_root, has_compression_hop = (
            _resolve_to_parent(db, current_session_id) if current_session_id else (None, False))
        # Compression continuation: the root was summarised into the live child, so hide
        # it. /new-reset children carry no transcript — keep that root browsable.
        hidden = {current_session_id, current_root if has_compression_hop and current_root else None}
        results = [{
            "session_id": s.get("id", ""), "link": _session_link(s.get("id", ""), link_profile),
            "title": s.get("title") or None, **{k: s.get(k, "") for k in ("source", "started_at", "last_active")},
            "message_count": s.get("message_count", 0), "preview": s.get("preview", "")}
            for s in [x for x in sessions if x.get("id", "") not in hidden][:limit]]
        return _ok(mode="browse", results=results, count=len(results), message=(
            f"Showing {len(results)} most recent sessions. Pass a query= to search, "
            "or session_id+around_message_id to scroll."))

    out, err = _loud(_browse, "Error listing recent sessions: %s", "Failed to list recent sessions")
    return err or out


def _clamp_int(value, default: int, lo: int, hi: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(lo, min(value, hi))


def _anchor_in_live_context(db, anchor_state, anchor_sid: str, current_session_id: str) -> bool:
    """True when the scroll anchor is still in the caller's active context (reject).
    Same-lineage history that LEFT live context (compacted rows, compression-ended
    parents, /new-reset predecessors) passes, so scroll never rejects a discovery result.
    Rewind/undo rows (active=0, compacted!=1) never count as out-of-context history."""
    if not _same_lineage(db, anchor_sid, current_session_id) or _is_compacted_state(anchor_state):
        return False
    return (anchor_state is not None and anchor_state["active"] == 0) or not _session_left_live_context(db, anchor_sid)


def _scroll(db, session_id: str, around_message_id: int, window: int = 5,
            current_session_id: str = None, content_offset: int = 0,
            message_field: str = 'content') -> str:
    """Scroll shape: a window centered on an anchor (no FTS5, no bookends)."""
    try:
        around_message_id = int(around_message_id)
    except (TypeError, ValueError):
        return tool_error("scroll requires integer around_message_id", success=False)
    window = _clamp_int(window, 5, 1, 20)
    # Locate the anchor BEFORE the current-lineage guard (see _anchor_in_live_context).
    anchor_state = _get_message_storage_state(db, around_message_id)
    owning = (anchor_state or {}).get("session_id")
    if current_session_id and _anchor_in_live_context(db, anchor_state, owning or session_id, current_session_id):
        return tool_error("scroll rejected: anchor lives in the current session lineage (already in your active context)", success=False)
    session_meta = _get_session_meta(db, session_id)
    if not session_meta:
        return tool_error(f"session_id not found: {session_id}", success=False)
    view, err = _loud(lambda: db.get_messages_around(session_id, around_message_id, window=window),
                      "get_messages_around failed: %s", "failed to load messages")
    if err:
        return err
    messages = view.get("window") or []
    extra = {}
    if not messages and owning and owning != session_id:
        # Lineage rebind: the caller paired a parent session_id with a message id
        # living in a descendant — serve the owner's window transparently.
        rebind_view = _same_lineage(db, session_id, owning) and _quiet(
            lambda: db.get_messages_around(owning, around_message_id, window=window),
            None, "rebind get_messages_around failed: %s", with_exc=True)
        if rebind_view and rebind_view.get("window"):
            extra["warning"] = (f"around_message_id {around_message_id} lives in {owning} "
                                f"(child of {session_id}); rebound transparently")
            view, messages, session_id = rebind_view, rebind_view["window"], owning
            session_meta = _get_session_meta(db, owning) or session_meta
    if not messages:
        return tool_error(f"around_message_id {around_message_id} not in session_id {session_id}", success=False)
    try:
        shaped = [_shape_message(m, anchor_id=around_message_id, max_content_len=4000,
                                 content_offset=content_offset if m.get("id") == around_message_id else 0,
                                 message_field=message_field if m.get('id') == around_message_id else 'content')
                  for m in messages]
    except ValueError as exc:
        return tool_error(str(exc), success=False)
    return _ok(
        mode="scroll", session_id=session_id, around_message_id=around_message_id,
        session_meta=_session_meta_block(session_meta), window=window,
        messages=shaped,
        messages_before=view.get("messages_before", 0), messages_after=view.get("messages_after", 0),
        hint=("To continue a truncated message, re-call with its id as around_message_id "
              "and its next_content_offset as content_offset. For tool_calls_page, set message_field=tool_calls "
              "and use next_tool_calls_offset as content_offset; concatenate tool_calls_page chunks then parse JSON. "
              "Offsets count Unicode characters, not tokens or UTF-8 bytes. "
              "Scroll forward: re-call with around_message_id = the LAST message's "
              "id; backward: the FIRST message's id (the boundary message repeats "
              "as an orientation marker). messages_before/messages_after < window "
              "means you've hit that end of the session."), **extra)


def _dispatch(query, role_filter, limit, db, current_session_id, session_id,
              around_message_id, window, sort, profile, detail, owned_dbs,
              after=None, before=None, exclude_session_ids=None, content_offset=0,
              message_field='content') -> str:
    """Mode dispatch (see module docstring); scroll wins when an anchor is set.
    Profile DBs opened here are appended to *owned_dbs* for the caller to close."""
    # A raw `@session:<profile>/<id>` link as session_id: ids never contain "/", so
    # split on it and adopt the embedded profile only when none was passed.
    if isinstance(session_id, str) and "/" in session_id:
        emb_profile, _, emb_id = session_id.partition("/")
        if emb_id:
            session_id = emb_id
            if emb_profile and (profile is None or not str(profile).strip()):
                profile = emb_profile
    # Cross-profile: swap in the named profile's DB (read-only) for every shape;
    # current-lineage guards key off ids that won't collide, so they stay inert.
    try:
        from hermes_cli.friday_user_scope import current
        profile_db = None if current() is not None else _resolve_profile_db(profile)
    except Exception as e:
        return tool_error(f"profile '{profile}': {e}", success=False)
    if profile_db is not None:
        db, current_session_id = profile_db, None
        owned_dbs.append(profile_db)
    if isinstance(session_id, str) and session_id.strip():
        if around_message_id is not None:
            return _scroll(db, session_id.strip(), around_message_id, window, current_session_id, content_offset, message_field)
        return _read_scoped(db, session_id.strip(), profile)
    limit = _clamp_int(limit, 3, 1, 10)
    if not query or not isinstance(query, str) or not query.strip():
        return _list_recent_sessions(db, limit, current_session_id, link_profile=profile)
    sort_norm = sort.strip().lower() if isinstance(sort, str) else None
    try:
        after_ts, before_ts = _parse_iso_bound(after), _parse_iso_bound(before)
    except ValueError as e:
        return tool_error(str(e), success=False)
    return _discover(
        db=db, query=query.strip(), limit=limit, sort=sort_norm if sort_norm in ("newest", "oldest") else None,
        role_filter=([r.strip() for r in role_filter.split(",") if r.strip()] or None) if isinstance(role_filter, str) else None,
        detail="full" if isinstance(detail, str) and detail.strip().lower() == "full" else "adaptive",
        current_session_id=current_session_id, link_profile=profile, after_ts=after_ts, before_ts=before_ts,
        exclude_session_ids=_normalize_exclude_session_ids(exclude_session_ids))


def session_search(query: str = "", role_filter: str = None, limit: int = 3, db=None,
                   current_session_id: str = None, session_id: str = None, around_message_id: int = None,
                   window: int = 5, sort: str = None, profile: str = None, detail: str = "adaptive",
                   after: str = None, before: str = None, exclude_session_ids: Optional[List[str]] = None,
                   content_offset: int = 0, message_field: str = 'content') -> str:
    """Run session search, closing DBs opened here. Positional order is frozen for old callers;
    new parameters are appended after ``detail``."""
    from hermes_cli.friday_user_scope import check_search, ScopeDenied, ordinary_tool_error_json
    if isinstance(session_id, str) and session_id.strip().startswith("@session:"):
        session_id = session_id.strip()[len("@session:"):]
        parts = session_id.split("/")
        if (len(parts) > 2 or any(not part or part in {".", ".."} or "@session:" in part for part in parts)
                or (len(parts) == 2 and profile not in (None, "", parts[0]))):
            return tool_error("Invalid or conflicting session link", success=False)
    content_offset = 0 if content_offset is None else content_offset
    if message_field not in ('content', 'tool_calls'):
        return tool_error('message_field must be content or tool_calls', success=False)
    if message_field != 'content' and (not isinstance(session_id, str) or not session_id.strip() or around_message_id is None):
        return tool_error('message_field requires session_id and around_message_id', success=False)
    if type(content_offset) is not int or content_offset < 0:
        return tool_error("content_offset must be a non-negative integer", success=False)
    if content_offset and (not isinstance(session_id, str) or not session_id.strip() or around_message_id is None):
        return tool_error("content_offset requires session_id and around_message_id", success=False)
    try:
        check_search(profile, session_id, db)
    except ScopeDenied:
        return ordinary_tool_error_json("product_user_scope_refused") or tool_error("product_user_scope_refused", success=False)
    if (isinstance(query, str) and query.strip()
            and isinstance(session_id, str) and session_id.strip()
            and around_message_id is None):
        return tool_error("session_search_ambiguous_query_session", success=False, hint=(
            "query + session_id without around_message_id is unsupported. For discovery, "
            "omit session_id and use query with role_filter; then scroll a relevant result "
            "with its returned session_id and match_message_id as around_message_id. "
            "To read a session, omit query. role_filter filters discovery matches only; "
            "returned context may include other roles."))
    from hermes_state import format_session_db_unavailable
    from hermes_state_registry import acquire, release_or_close
    owned_dbs: List[Any] = []
    if db is None:
        db = _quiet(acquire, None, "SessionDB unavailable for session_search")
        if db is None:
            return tool_error(format_session_db_unavailable(), success=False)
        owned_dbs.append(db)
    try:
        return _dispatch(query, role_filter, limit, db, current_session_id, session_id,
                         around_message_id, window, sort, profile, detail, owned_dbs,
                         after=after, before=before, exclude_session_ids=exclude_session_ids,
                         content_offset=content_offset, message_field=message_field)
    except (UnicodeError, RecursionError):
        return tool_error('session_search_invalid_data', success=False)
    finally:
        for owned_db in reversed(owned_dbs):
            _quiet(lambda: release_or_close(owned_db), None, "Failed to close session_search SessionDB")


def check_session_search_requirements() -> bool:
    """Requires the SQLite state database."""
    try:
        from hermes_state import _default_db_path
        return _default_db_path().parent.exists()
    except ImportError:
        return False


SESSION_SEARCH_SCHEMA = {
    "name": "session_search",
    "description": (
        "Recall past conversations: search or read old Hermes sessions (FTS5), or "
        "scroll inside one. Four shapes, picked by args: `query` = discovery "
        "(top-N matching sessions, top result fully hydrated); `session_id` + "
        "`around_message_id` = scroll (window of messages around an anchor); "
        "`session_id` alone = read a whole session — how you resolve an "
        "`@session:<profile>/<id>` link (split on '/' into profile + id); no "
        "args = browse recent sessions. A nonempty query + session_id without "
        "around_message_id is rejected: omit session_id for discovery, then scroll "
        "a returned hit with its session_id and match_message_id. "
        "Discovery groups hits by logical lineage: `when` is that lineage's start, "
        "while match_provenance gives the matched raw session/message dates and "
        "whether it is an archive of the current session. Such an archive is not "
        "a previous session. For an original/earliest source use sort='oldest'; "
        "for a previous-session source use before with the current session's start "
        "when known, then verify the returned raw session and document path. "
        "Results are actual DB messages, no LLM. "
        "Searches conversation history ONLY — when the user gave a direct "
        "source (URL, file, contact, live system), inspect that first; never "
        "conclude 'not found' from history alone. Use for questions about past "
        "conversations: 'what did we do about X', 'where did we leave Y'. When "
        "referring the user to a session, write its `link` value verbatim "
        "inline (it renders as a titled link)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search query (discovery shape). Keywords, phrases, or boolean "
                    "expressions to find in past sessions. Omit to browse recent "
                    "sessions. Do not combine with session_id unless around_message_id "
                    "is set; that ambiguous combination is rejected. Ignored when "
                    "session_id + around_message_id are set "
                    "(scroll shape)."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Discovery shape only. Max sessions to return (default 3, max 10). "
                    "Bump to 5–10 when the topic likely spans several sessions and you "
                    "want to pick the right one to scroll into."
                ),
                "default": 3,
            },
            "sort": {
                "type": "string",
                "enum": ["newest", "oldest"],
                "description": (
                    "Discovery shape only. Temporal bias on top of FTS5 ranking: omit "
                    "for relevance-only (exploratory recall), 'newest' for "
                    "\"where did we leave X\", 'oldest' for \"how did X start\" or "
                    "the original/earliest source. One hit per logical lineage is returned."
                ),
            },
            "detail": {
                "type": "string",
                "enum": ["adaptive", "full"],
                "description": (
                    "Discovery shape only. 'adaptive' (default) fully hydrates the "
                    "top-ranked result and returns only the exact anchor message for "
                    "lower-ranked results. 'full' returns bookends and the complete "
                    "anchored window for every result."
                ),
                "default": "adaptive",
            },
            "after": {
                "type": "string",
                "description": (
                    "Discovery shape only. Inclusive lower bound on session start "
                    "time. ISO date/datetime (e.g. 2026-06-01) or relative duration "
                    "(7d, 24h, 2w = within the last N). Use only when the user names "
                    "a time frame. sort is a ranking bias, not a bound."
                ),
            },
            "before": {
                "type": "string",
                "description": (
                    "Discovery shape only. Exclusive upper bound on session start "
                    "time. ISO date/datetime (a date-only value is midnight UTC that "
                    "day) or relative duration (7d = older than a week). Use only "
                    "when the user names a time frame or asks for a previous session. "
                    "FTS message matches use the matched raw session's start; "
                    "title-only matches use the logical-lineage start. Verify "
                    "match_provenance before treating a hit as a previous session."
                ),
            },
            "exclude_session_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Discovery shape only. Session ids already inspected this task. "
                    "Those sessions and their lineage are omitted so a later query "
                    "explores instead of repeating the same hit. Cap 20."
                ),
            },
            "session_id": {
                "type": "string",
                "description": (
                    "Session to read, or a returned @session: link. Used alone for read; "
                    "pair with around_message_id to scroll inside the session. It is "
                    "not a discovery query filter; omit it when searching with query."
                ),
            },
            "content_offset": {
                "type": "integer",
                "minimum": 0,
                "description": (
                    "Scroll only. Character offset inside the anchor message's displayed text. "
                    "To continue a truncated message, use its id as around_message_id and "
                    "its next_content_offset here. Defaults to 0; does not alter saved history."
                ),
            },
            "message_field": {
                "type": "string", "enum": ["content", "tool_calls"], "default": "content",
                "description": "Scroll anchor field. For a truncated tool_calls_page, select tool_calls and use next_tool_calls_offset as content_offset. Concatenate JSON text pages before parsing; offsets are Unicode characters. Original archived rows remain unchanged.",
            },
            "around_message_id": {
                "type": "integer",
                "description": (
                    "Scroll shape. Message id to center the window on — use "
                    "match_message_id from a discovery result, or any id from a "
                    "prior window."
                ),
            },
            "window": {
                "type": "integer",
                "description": (
                    "Scroll shape only. Messages to return on each side of the anchor "
                    "(anchor itself always included). Clamped to [1, 20]. Default 5."
                ),
                "default": 5,
            },
            "role_filter": {
                "type": "string",
                "description": (
                    "Discovery only. Comma-separated roles of matching messages; "
                    "returned context may include other roles. Ignored for read/scroll. "
                    "Discovery defaults to "
                    "'user,assistant' (tool output is usually noise). Pass "
                    "'user,assistant,tool' to include tool output (debugging tool "
                    "behaviour) or 'tool' to search tool output only."
                ),
            },
            "profile": {
                "type": "string",
                "description": (
                    "Optional. Read sessions from another Hermes profile's database "
                    "(read-only). Use when resolving an `@session:<profile>/<id>` link: "
                    "pass the profile segment here with session_id as the id segment. "
                    "Omit to use the current profile."
                ),
            },
        },
        "required": [],
    },
}


from tools.registry import registry, tool_error  # noqa: E402  (registration at import time)

registry.register(
    name="session_search",
    toolset="session_search",
    schema=SESSION_SEARCH_SCHEMA,
    handler=lambda args, **kw: session_search(
        query=args.get("query") or "", limit=args.get("limit", 3), window=args.get("window", 5),
        content_offset=args.get("content_offset", 0), message_field=args.get('message_field', 'content'),
        detail=args.get("detail", "adaptive"), db=kw.get("db"), current_session_id=kw.get("current_session_id"),
        **{k: args.get(k) for k in ("role_filter", "session_id", "around_message_id", "sort", "profile",
                                    "after", "before", "exclude_session_ids")}),
    check_fn=check_session_search_requirements,
    emoji="🔍")
