"""Native Chat Completions SSE and SQLite regression using a synthetic HTTP transport."""
from contextlib import closing
from functools import wraps
import json
import socket
import sqlite3
from unittest.mock import patch

import httpx
import pytest

from tests.agent.test_bounded_local_context import BASE, MODEL, PROVIDER, profile


class EventStream(httpx.SyncByteStream):
    def __init__(self, frames):
        self.frames = frames

    def __iter__(self):
        yield from self.frames


def test_incomplete_sse_tool_call_does_not_survive_sqlite_reopen(tmp_path, monkeypatch):
    def deny_network(*args, **kwargs):
        pytest.fail("Offline SSE fixture attempted network access")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    from hermes_cli import _early_recovery, friday_credential_admission, venv_sync
    from pm import environments

    monkeypatch.setattr(friday_credential_admission, "SOURCE", tmp_path / "hermes-agent")
    with (
        patch.object(venv_sync, "prepare_launch", return_value=None),
        patch.object(environments, "activate_dependencies"),
        patch.object(_early_recovery, "recover_if_needed"),
        patch.object(_early_recovery, "restore_interrupted_pull", return_value=False),
    ):
        from run_agent import AIAgent

    from agent import friday_baseline_bridge, relay_runtime
    from hermes_cli.config import atomic_config_write
    from hermes_state import SessionDB
    from tools.file_tools import registry

    config = profile()
    # The full file-tool schema needs the main route's production-sized input budget.
    config["model"]["context_length"] = 262144
    config["auxiliary"]["compression"]["context_length"] = 262144
    route = config["providers"]["friday-local"]["models"][MODEL]
    route["context_length"] = 262144
    route["bounded_context"]["server_max_input_tokens"] = 262138
    config["tools"] = {"tool_search": {"enabled": "off"}}
    atomic_config_write(tmp_path / "config.yaml", config)
    monkeypatch.setattr(friday_baseline_bridge, "_load", lambda: None)
    monkeypatch.setattr(
        relay_runtime.HOST_REGISTRY, "for_profile",
        lambda *_args, **_kwargs: relay_runtime.NoopRelayRuntime(profile_key="offline", reason="isolated fixture"),
    )

    fact = "A unique value from the reopened session's fixture."
    (tmp_path / "fresh.txt").write_text(fact, encoding="utf-8")
    (tmp_path / "abandoned.txt").write_text("This call must never execute.", encoding="utf-8")
    dropped_id, fresh_id = "call_abandoned_eof", "call_fresh_after_reopen"
    broken_parts = ('{"path":', '"abandoned.txt","offset":1')
    with pytest.raises(json.JSONDecodeError):
        json.loads("".join(broken_parts))

    recovering = False
    requests = {False: [], True: []}

    def chunk(delta=None, finish=None):
        frame = {
            "id": "fixture", "object": "chat.completion.chunk", "created": 1, "model": MODEL,
            "choices": [{"index": 0, "delta": delta or {}, "finish_reason": finish}],
        }
        return ("data: " + json.dumps(frame) + "\n\n").encode()

    def tool_delta(call_id, arguments):
        return {"tool_calls": [{"index": 0, "id": call_id, "type": "function",
                               "function": {"name": "read_file", "arguments": arguments}}]}

    def respond(_transport, request):
        if request.method == "GET" and request.url.host == httpx.URL(BASE).host:
            return httpx.Response(404, json={"error": "Synthetic provider metadata"})
        assert request.method == "POST" and str(request.url) == BASE + "/chat/completions"
        body = json.loads(request.content)
        assert body["stream"] is True
        assert "read_file" in [tool["function"]["name"] for tool in body["tools"]]
        requests[recovering].append(body["messages"])
        number = len(requests[recovering])
        if not recovering:
            assert number <= 4
            frames = [chunk(tool_delta(dropped_id, broken_parts[0])),
                      chunk({"tool_calls": [{"index": 0, "function": {"arguments": broken_parts[1]}}]})]
            # EOF follows the last delta, with no finish_reason, usage, or [DONE].
        elif number == 1:
            frames = [chunk(tool_delta(fresh_id, '{"path":"fresh.txt"}')),
                      chunk(finish="tool_calls"), b"data: [DONE]\n\n"]
        else:
            assert number == 2
            frames = [chunk({"content": "Read completed."}, "stop"), b"data: [DONE]\n\n"]
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=EventStream(frames))

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    db_path = tmp_path / "state.db"
    session_id = "sse-eof-fixture"

    def new_agent(db):
        return AIAgent(
            model=MODEL, provider="custom", requested_provider=PROVIDER, base_url=BASE,
            api_key="fixture-only", api_mode="chat_completions", quiet_mode=True,
            skip_context_files=True, skip_memory=True, skip_background_review=True,
            enabled_toolsets=["file"], max_iterations=4, session_db=db, session_id=session_id,
            cwd=str(tmp_path), save_trajectories=False,
        )

    reads = []
    entry = registry.get_entry("read_file")
    read_file = entry.handler

    @wraps(read_file)
    def record_read(args, **kwargs):
        reads.append(args.get("path"))
        return read_file(args, **kwargs)

    monkeypatch.setattr(entry, "handler", record_read)

    def snapshot():
        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            return conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id", (session_id,)
            ).fetchall()

    def assert_abandoned_call_absent(rows):
        text = repr(rows)
        assert dropped_id not in text
        assert "abandoned.txt" not in text

    with closing(SessionDB(db_path)) as db:
        db.create_session(session_id, source="cli", model=MODEL)
        db.append_message(session_id, role="user", content="Retain the original question.")
        db.append_message(session_id, role="assistant", content="Retained prior answer.")
        original_rows = snapshot()
        assert len(original_rows) == 2
        history = db.get_messages_as_conversation(session_id)
        with closing(new_agent(db)) as agent:
            broken = agent.run_conversation("Open the earlier fixture.", conversation_history=history)
        assert broken["completed"] is False
        assert broken["partial"] and broken["failure_reason"] == "truncated" and broken["error"]
        assert len(requests[False]) == broken["api_calls"] == 4
        assert reads == []
        assert_abandoned_call_absent(broken["messages"])
        assert_abandoned_call_absent(requests[False])

    recovering = True
    with closing(SessionDB(db_path)) as reopened:
        retained = snapshot()
        assert retained[:len(original_rows)] == original_rows
        assert_abandoned_call_absent(retained)
        history = reopened.get_messages_as_conversation(session_id)
        with closing(new_agent(reopened)) as agent:
            result = agent.run_conversation("Read the fresh fixture.", conversation_history=history)
        assert result["completed"] is True
        assert result["final_response"] == "Read completed."
        transcript = reopened.get_messages_as_conversation(session_id)
        assert transcript[-2]["tool_call_id"] == fresh_id
        assert fact in transcript[-2]["content"]

    assert reads == ["fresh.txt"]
    assert len(requests[True]) == 2
    tool_result = requests[True][1][-1]
    assert tool_result["role"] == "tool" and tool_result["tool_call_id"] == fresh_id
    assert fact in tool_result["content"]
    assert_abandoned_call_absent(requests[True])
    final_rows = snapshot()
    assert final_rows[:len(original_rows)] == original_rows
    assert_abandoned_call_absent(final_rows)
