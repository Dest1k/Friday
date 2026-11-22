"""Telegram provider-wire regression for native write crash recovery and compaction."""
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
@pytest.mark.parametrize("compress", [False, True], ids=["uncompressed", "compressed"])
def test_telegram_inbound_after_write_crash(tmp_path, monkeypatch, offline_chat, boundary, compress, record_property):
    from gateway.config import GatewayConfig, Platform, PlatformConfig
    from gateway.platforms.event import MessageEvent
    from gateway.run import GatewayRunner
    from gateway.session import SessionStore
    from hermes_cli.config import atomic_config_write
    from hermes_state_registry import close_all_under, live_shared_session_dbs
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
    requests = {"seed": [], "telegram": [], "reopen": []}
    compressor_requests, committed_at_dispatch = [], []
    summary = "The discussion compared several agenda options and collected questions for the next meeting."
    reopen_prompt = "Which agenda options were discussed earlier?"
    prior_count = 10 if compress else 1
    agenda_details = ("The team compared venue access, seating, and meal schedules. " *
                      (108 if compress else 1)).strip()
    prior_replies = [f"Agenda item {index}: {agenda_details}" for index in range(prior_count)]
    writes, reads, telegram_events = [], [], []
    expected_receipts = int(boundary == "after-flush")
    final_text = "The existing artifact was read."

    def respond(_transport, request):
        if request.method == "GET" and request.url.host == httpx.URL(BASE).host:
            return httpx.Response(404, json={"error": "Synthetic provider metadata"})
        assert request.method == "POST" and str(request.url) == BASE + "/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == MODEL
        auxiliary = body.get("response_format", {}).get("type") == "json_schema"
        call = None
        usage = None
        if auxiliary:
            assert compress and phase == "telegram" and not requests["telegram"]
            assert not body.get("tools")
            compressor_requests.append(body["messages"])
            text, finish = json.dumps({"summary": summary}), "stop"
            usage = {"prompt_tokens": 5000, "completion_tokens": 24, "total_tokens": 5024}
        else:
            requests[phase].append(body["messages"])
            n = len(requests[phase])
            if phase == "seed":
                text, finish = prior_replies[n - 1], "stop"
            elif phase == "reopen":
                assert n == 1
                text, finish = "The prior discussion covered meeting logistics.", "stop"
            elif n == 1:
                if compress:
                    committed_at_dispatch.append(committed_summary())
                assert {"read_file", "write_file"} <= {row["function"]["name"] for row in body["tools"]}
                call = tool_delta("read_file", CRASH_READ_ID, json.dumps({"path": str(artifact)}))
                text, finish = "", "tool_calls"
            else:
                assert n == 2
                text, finish = final_text, "stop"
        if body.get("stream"):
            frames = [chunk(call or {"content": text}), chunk(finish=finish)]
            if usage:
                frame = {"id": "fixture", "object": "chat.completion.chunk", "model": MODEL,
                         "created": 1, "choices": [], "usage": usage}
                frames.append(("data: " + json.dumps(frame) + "\n\n").encode())
            return httpx.Response(200, headers={"content-type": "text/event-stream"},
                                  stream=EventStream([*frames, DONE]))
        message = {"role": "assistant", "content": text}
        if call:
            message["tool_calls"] = [{key: value for key, value in call["tool_calls"][0].items() if key != "index"}]
        return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 1, "model": MODEL,
                                        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                                        **({"usage": usage} if usage else {})})

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
        for index in range(prior_count):
            prior = agent.run_conversation(f"Discuss agenda item {index}.",
                                           conversation_history=db.get_messages_as_conversation(session_id))
            assert prior["completed"] is True
        prior_rows = sqlite_snapshot(db_path, session_id)
        assert len(prior_rows) == prior_count * 2

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
    if compress:
        # The crash fixture uses 262144. A smaller resumed window crosses the
        # native pressure threshold while a compacted request can still fit.
        window = 131072
        cfg["model"]["context_length"] = window
        cfg["auxiliary"]["compression"]["context_length"] = window
        route = cfg["providers"]["friday-local"]["models"][MODEL]
        route["context_length"] = window
        route["bounded_context"]["server_max_input_tokens"] = window - 6
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

    async def run_inbound(message, message_id):
        adapter = parity.ParityTelegramAdapter(pc, Platform.TELEGRAM)
        runner = GatewayRunner(config=config)
        adapter.gateway_runner = runner
        runner.adapters[Platform.TELEGRAM] = adapter
        runner._wire_adapter_handlers(adapter)
        adapter._mark_connected()
        runner._gateway_loop = asyncio.get_running_loop()
        try:
            assert not runner._agent_cache and not requests[phase]
            source = adapter.build_source(**source_fields, message_id=message_id)
            incoming = MessageEvent(text=message, source=source, message_id=message_id,
                                    platform_update_id=int(message_id) + 100)
            await adapter.handle_message(incoming)
            assert incoming._gateway_accepted
            await asyncio.wait_for(adapter._session_tasks[session_key], timeout=30)
            return runner.session_store.lookup_by_session_key(session_key).session_id
        finally:
            # This test owns the adapter and runner handles but never starts the service.
            await adapter.disconnect()
            assert runner._shutdown_executor(drain_timeout=3) == 0
            for cached in runner._agent_cache.values():
                cached[0].close()
            runner.session_store.close_all_db_handles()
            runner.close_all_session_db_handles()
            # Gateway shutdown also sweeps process-wide handles held by tools.
            close_all_under(tmp_path)

    def committed_summary():
        with closing(SessionDB(db_path, read_only=True)) as db:
            active = db.get_messages(session_id)
            carriers = [row for row in active if row.get("_compressed_summary")]
            assert len(carriers) == 1 and summary in carriers[0]["content"]
            assert not any(row["content"] == prior_replies[2] for row in active)
            carrier = carriers[0]
            assert carrier["id"] > cut_rows[-1][0]
            archive = db.get_messages(session_id, include_compacted=True)
            assert any(row["compacted"] and row["content"] == prior_replies[2] for row in archive)
            return carrier["id"], carrier["content"]

    def assert_write_state(messages):
        calls, results = write_pair(messages)
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
        return results[0]

    # Startup tool downloads are outside this inbound-only test.
    monkeypatch.setattr("tools.tirith_security.ensure_installed", lambda **_kwargs: None)
    phase = "telegram"
    assert asyncio.run(run_inbound(CRASH_READ_PROMPT, "42")) == session_id
    if compress:
        assert len(compressor_requests) == 1
        assert committed_at_dispatch == [committed_summary()], telegram_events
        with closing(SessionDB(db_path, read_only=True)) as db:
            durable_result = assert_write_state(db.get_messages_as_conversation(session_id))
            assert (durable_result.get("effect_disposition") == "unknown") is (not receipts)
            history = db.get_messages(session_id, include_compacted=True)
            visible_originals = {(row["role"], row["content"]) for row in history
                                 if isinstance(row["content"], str)}
            for index, reply in enumerate(prior_replies):
                assert ("user", f"Discuss agenda item {index}.") in visible_originals
                assert ("assistant", reply) in visible_originals
            assert ("user", CRASH_WRITE_PROMPT) in visible_originals

        assert all(db.db_path != db_path for db in live_shared_session_dbs())
        phase = "reopen"
        assert asyncio.run(run_inbound(reopen_prompt, "43")) == session_id
        assert len(requests["reopen"]) == 1, telegram_events
        cold_wire = requests["reopen"][0]
        assert_write_state(cold_wire)
        assert cold_wire[-1]["role"] == "user" and cold_wire[-1]["content"] == reopen_prompt
        assert sum(row["role"] == "user" and row["content"] == CRASH_READ_PROMPT for row in cold_wire) == 1
        assert committed_summary() == committed_at_dispatch[0]
        record_property("native_compaction_commit_kind", "in_place")
        record_property("durable_summary_row_id", committed_at_dispatch[0][0])
        record_property("reopen_model_requests", len(requests["reopen"]))
    assert len(requests["telegram"]) == 2, telegram_events
    wire = requests["telegram"][0]
    assert_write_state(wire)
    if compress:
        for messages in (wire, cold_wire):
            assert any(summary in str(row.get("content")) for row in messages)
            assert not any(prior_replies[2] in str(row.get("content")) for row in messages)
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
        read_results = [row for row in final if row.get("tool_call_id") == CRASH_READ_ID]
        assert len(read_results) == 1 and CRASH_CONTENT.strip() in read_results[0]["content"]
        new_inputs = [row["content"] for row in final if row["role"] == "user"
                      and row["content"].endswith(CRASH_READ_PROMPT)]
        assert len(new_inputs) == 1 and CRASH_WRITE_PROMPT not in new_inputs[0]
        if not compress:
            assert len(write_pair(final)[1]) == expected_receipts
            assert final[-1]["content"] == final_text
            assert new_inputs == [CRASH_READ_PROMPT]
    if not compress:
        assert sqlite_snapshot(db_path, session_id)[:len(cut_rows)] == cut_rows

    record_property("crash_boundary", boundary)
    record_property("gateway_model_requests", len(requests["telegram"]))
    record_property("replayed_write_receipt", "verified" if receipts else "uncertain")
    record_property("write_entries_across_processes", len(writes))
    record_property("same_telegram_routing_entry", True)
