"""Telegram inbound and provider-wire regression for native write crash recovery."""
import asyncio
from contextlib import closing
from functools import wraps
import json
import sys

import httpx
import pytest

from test_ordinary_sse_disconnect import (
    BASE, MODEL, CRASH_CONTENT, CRASH_FILENAME, CRASH_READ_ID, CRASH_READ_PROMPT,
    CRASH_WRITE_ID, CRASH_WRITE_PROMPT, DONE, EventStream, chunk, kill_at_crash_boundary,
    offline_chat, sqlite_snapshot, tool_delta,
)


@pytest.mark.skipif(sys.platform != "linux", reason="Reuses the Linux SIGKILL fixture")
@pytest.mark.parametrize("boundary", ["before-flush", "after-flush"])
def test_telegram_inbound_after_write_crash(tmp_path, monkeypatch, offline_chat, boundary, record_property):
    from gateway.config import GatewayConfig, Platform, PlatformConfig
    from gateway.platforms.event import MessageEvent
    from gateway.run import GatewayRunner
    from gateway.session import SessionStore
    from hermes_cli.config import atomic_config_write
    from tests.e2e.core.parity import _gateway_child as parity
    import yaml

    new_agent, SessionDB, registry = offline_chat
    user_id = 424242
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", str(user_id))
    monkeypatch.setenv("TERMINAL_CWD", str(tmp_path))
    pc = PlatformConfig(enabled=True, token="123456:offline-fixture", typing_indicator=False)
    config = GatewayConfig(platforms={Platform.TELEGRAM: pc}, multiplex_profiles=False,
                           sessions_dir=tmp_path / "sessions", write_sessions_json=False)
    db_path = tmp_path / "state.db"
    artifact = tmp_path / CRASH_FILENAME
    phase = "seed"
    requests = {"seed": [], "telegram": []}
    writes, reads, telegram_events = [], [], []
    expected_receipts = int(boundary == "after-flush")
    final_text = "The existing artifact was read."

    def respond(_transport, request):
        if request.method == "GET" and request.url.host == httpx.URL(BASE).host:
            return httpx.Response(404, json={"error": "Synthetic provider metadata"})
        assert request.method == "POST" and str(request.url) == BASE + "/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == MODEL
        requests[phase].append(body["messages"])
        n = len(requests[phase])
        call = None
        if phase == "seed":
            assert n == 1
            text, finish = "The prior Telegram conversation is retained.", "stop"
        elif n == 1:
            assert {"read_file", "write_file"} <= {row["function"]["name"] for row in body["tools"]}
            call = tool_delta("read_file", CRASH_READ_ID, json.dumps({"path": str(artifact)}))
            text, finish = "", "tool_calls"
        else:
            assert n == 2
            text, finish = final_text, "stop"
        if body.get("stream"):
            frames = [chunk(call or {"content": text}), chunk(finish=finish), DONE]
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=EventStream(frames))
        message = {"role": "assistant", "content": text}
        if call:
            message["tool_calls"] = [{key: value for key, value in call["tool_calls"][0].items() if key != "index"}]
        return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 1, "model": MODEL,
                                        "choices": [{"index": 0, "message": message, "finish_reason": finish}]})

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    adapter = parity.ParityTelegramAdapter(pc, Platform.TELEGRAM)
    source_fields = dict(chat_id=str(user_id), chat_type="dm", user_id=str(user_id),
                         chat_name="Offline", user_name="Offline")
    store = SessionStore(config.sessions_dir, config)
    try:
        entry = store.get_or_create_session(adapter.build_source(**source_fields))
        session_id = entry.session_id
        session_key = entry.session_key
    finally:
        store.close_all_db_handles()

    with closing(SessionDB(db_path)) as db, closing(new_agent(db, session_id)) as agent:
        prior = agent.run_conversation("Retain this earlier Telegram conversation.")
        assert prior["completed"] is True
        prior_rows = sqlite_snapshot(db_path, session_id)
        assert len(prior_rows) == 2

    def write_pair(messages):
        calls = [call for msg in messages for call in msg.get("tool_calls") or [] if call["id"] == CRASH_WRITE_ID]
        results = [msg for msg in messages if msg["role"] == "tool" and msg.get("tool_call_id") == CRASH_WRITE_ID]
        return calls, results

    def inspect_cut():
        assert artifact.read_bytes() == CRASH_CONTENT.encode("utf-8")
        with closing(SessionDB(db_path, read_only=True)) as db:
            calls, receipts = write_pair(db.get_messages_as_conversation(session_id))
            assert len(calls) == 1 and len(receipts) == expected_receipts
            assert calls[0]["function"]["name"] == "write_file"
            assert json.loads(calls[0]["function"]["arguments"]) == {"path": CRASH_FILENAME, "content": CRASH_CONTENT}
            assert db.session_lifecycle_statuses([session_id])[session_id] == "interrupted"
        rows = sqlite_snapshot(db_path, session_id)
        assert rows[:len(prior_rows)] == prior_rows
        return rows, calls[0], receipts

    child_entries, (cut_rows, original_call, receipts) = kill_at_crash_boundary(
        tmp_path, boundary, inspect_cut, session_id=session_id,
    )
    writes.extend(child_entries)
    assert inspect_cut() == (cut_rows, original_call, receipts)

    cfg_path = tmp_path / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["platform_toolsets"] = {"telegram": ["file"]}
    cfg["gateway"] = {"platforms": {"telegram": {"skip_context_files": True}}}
    atomic_config_write(cfg_path, cfg)

    write_entry = registry.get_entry("write_file")
    read_entry = registry.get_entry("read_file")
    write = write_entry.handler
    read = read_entry.handler

    @wraps(write)
    def count_write(args, **kwargs):
        writes.append("gateway")
        return write(args, **kwargs)

    @wraps(read)
    def count_read(args, **kwargs):
        reads.append(args.get("path"))
        return read(args, **kwargs)

    monkeypatch.setattr(write_entry, "handler", count_write)
    monkeypatch.setattr(read_entry, "handler", count_read)

    monkeypatch.setattr(parity, "emit", lambda kind, **event: telegram_events.append((kind, event)))

    async def run_inbound():
        runner = GatewayRunner(config=config)
        adapter.gateway_runner = runner
        runner.adapters[Platform.TELEGRAM] = adapter
        runner._wire_adapter_handlers(adapter)
        adapter._mark_connected()
        runner._gateway_loop = asyncio.get_running_loop()
        try:
            assert not runner._agent_cache and not requests["telegram"]
            source = adapter.build_source(**source_fields, message_id="42")
            incoming = MessageEvent(text=CRASH_READ_PROMPT, source=source, message_id="42", platform_update_id=142)
            await adapter.handle_message(incoming)
            assert incoming._gateway_accepted
            await asyncio.wait_for(adapter._session_tasks[session_key], timeout=30)
            assert runner.session_store.lookup_by_session_key(session_key).session_id == session_id
        finally:
            # This test owns the adapter and runner handles but never starts the service.
            await adapter.disconnect()
            assert runner._shutdown_executor(drain_timeout=3) == 0
            for cached in runner._agent_cache.values():
                cached[0].close()
            runner.session_store.close_all_db_handles()
            runner.close_all_session_db_handles()

    # Startup tool downloads are outside this inbound-only test.
    monkeypatch.setattr("tools.tirith_security.ensure_installed", lambda **_kwargs: None)
    phase = "telegram"
    asyncio.run(run_inbound())
    assert len(requests["telegram"]) == 2, telegram_events
    wire = requests["telegram"][0]
    calls, results = write_pair(wire)
    assert len(calls) == len(results) == 1
    function = calls[0]["function"]
    assert function["name"] == original_call["function"]["name"]
    assert json.loads(function["arguments"]) == json.loads(original_call["function"]["arguments"])
    recovered = results[0]["content"]
    if receipts:
        assert json.loads(recovered) == json.loads(receipts[0]["content"])
        assert json.loads(recovered)["verified"] is True
    else:
        notice = recovered.casefold()
        assert "may have executed" in notice and "inspect" in notice and "retry" in notice
        assert "bytes_written" not in notice and '"verified":true' not in notice.replace(" ", "")
    assert wire[-1]["role"] == "user"
    assert wire[-1]["content"].endswith(CRASH_READ_PROMPT)
    assert CRASH_WRITE_PROMPT not in wire[-1]["content"]
    assert sum(CRASH_WRITE_PROMPT in str(row["content"]) for row in wire if row["role"] == "user") == 1
    assert writes == child_entries and len(writes) == 1
    assert reads == [str(artifact)]
    gateway_read = requests["telegram"][1][-1]
    assert gateway_read["role"] == "tool" and gateway_read["tool_call_id"] == CRASH_READ_ID
    assert CRASH_CONTENT.strip() in gateway_read["content"]
    assert any(kind == "send" and event["chat_id"] == str(user_id) and event["content"] == final_text
               for kind, event in telegram_events)
    assert artifact.read_bytes() == CRASH_CONTENT.encode("utf-8")

    with closing(SessionDB(db_path, read_only=True)) as db:
        final = db.get_messages_as_conversation(session_id)
        assert len(write_pair(final)[1]) == expected_receipts
        assert CRASH_CONTENT.strip() in final[-2]["content"] and final[-2]["tool_call_id"] == CRASH_READ_ID
        assert final[-1]["content"] == final_text
        assert sum(row["role"] == "user" and row["content"] == CRASH_READ_PROMPT for row in final) == 1
    assert sqlite_snapshot(db_path, session_id)[:len(cut_rows)] == cut_rows

    record_property("crash_boundary", boundary)
    record_property("gateway_model_requests", len(requests["telegram"]))
    record_property("replayed_write_receipt", "verified" if receipts else "uncertain")
    record_property("write_entries_across_processes", len(writes))
    record_property("same_telegram_routing_entry", True)
