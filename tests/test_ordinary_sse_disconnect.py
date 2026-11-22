"""Native Chat Completions SSE and SQLite regression using a synthetic HTTP transport."""
from contextlib import closing
from functools import wraps
from time import monotonic_ns
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


def chunk(delta=None, finish=None):
    frame = {
        "id": "fixture", "object": "chat.completion.chunk", "created": 1, "model": MODEL,
        "choices": [{"index": 0, "delta": delta or {}, "finish_reason": finish}],
    }
    return ("data: " + json.dumps(frame) + "\n\n").encode()

def tool_delta(name, call_id, arguments):
    return {"tool_calls": [{"index": 0, "id": call_id, "type": "function",
                           "function": {"name": name, "arguments": arguments}}]}


def sqlite_snapshot(db_path, session_id):
    with closing(sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()


@pytest.fixture
def offline_chat(tmp_path, monkeypatch):
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

    def new_agent(db, session_id, *, max_iterations=4):
        return AIAgent(
            model=MODEL, provider="custom", requested_provider=PROVIDER, base_url=BASE,
            api_key="fixture-only", api_mode="chat_completions", quiet_mode=True,
            skip_context_files=True, skip_memory=True, skip_background_review=True,
            enabled_toolsets=["file"], max_iterations=max_iterations, session_db=db, session_id=session_id,
            cwd=str(tmp_path), save_trajectories=False,
        )

    return new_agent, SessionDB, registry


def test_incomplete_sse_tool_call_does_not_survive_sqlite_reopen(tmp_path, monkeypatch, offline_chat):
    new_agent, SessionDB, registry = offline_chat
    fact = "A unique value from the reopened session's fixture."
    (tmp_path / "fresh.txt").write_text(fact, encoding="utf-8")
    (tmp_path / "abandoned.txt").write_text("This call must never execute.", encoding="utf-8")
    dropped_id, fresh_id = "call_abandoned_eof", "call_fresh_after_reopen"
    broken_parts = ('{"path":', '"abandoned.txt","offset":1')
    with pytest.raises(json.JSONDecodeError):
        json.loads("".join(broken_parts))

    recovering = False
    requests = {False: [], True: []}

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
            frames = [chunk(tool_delta("read_file", dropped_id, broken_parts[0])),
                      chunk({"tool_calls": [{"index": 0, "function": {"arguments": broken_parts[1]}}]})]
            # EOF follows the last delta, with no finish_reason, usage, or [DONE].
        elif number == 1:
            frames = [chunk(tool_delta("read_file", fresh_id, '{"path":"fresh.txt"}')),
                      chunk(finish="tool_calls"), b"data: [DONE]\n\n"]
        else:
            assert number == 2
            frames = [chunk({"content": "Read completed."}, "stop"), b"data: [DONE]\n\n"]
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=EventStream(frames))

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    db_path = tmp_path / "state.db"
    session_id = "sse-eof-fixture"


    reads = []
    entry = registry.get_entry("read_file")
    read_file = entry.handler

    @wraps(read_file)
    def record_read(args, **kwargs):
        reads.append(args.get("path"))
        return read_file(args, **kwargs)

    monkeypatch.setattr(entry, "handler", record_read)

    def assert_abandoned_call_absent(rows):
        text = repr(rows)
        assert dropped_id not in text
        assert "abandoned.txt" not in text

    with closing(SessionDB(db_path)) as db:
        db.create_session(session_id, source="cli", model=MODEL)
        db.append_message(session_id, role="user", content="Retain the original question.")
        db.append_message(session_id, role="assistant", content="Retained prior answer.")
        original_rows = sqlite_snapshot(db_path, session_id)
        assert len(original_rows) == 2
        history = db.get_messages_as_conversation(session_id)
        with closing(new_agent(db, session_id)) as agent:
            broken = agent.run_conversation("Open the earlier fixture.", conversation_history=history)
        assert broken["completed"] is False
        assert broken["partial"] and broken["failure_reason"] == "truncated" and broken["error"]
        assert len(requests[False]) == broken["api_calls"] == 4
        assert reads == []
        assert_abandoned_call_absent(broken["messages"])
        assert_abandoned_call_absent(requests[False])

    recovering = True
    with closing(SessionDB(db_path)) as reopened:
        retained = sqlite_snapshot(db_path, session_id)
        assert retained[:len(original_rows)] == original_rows
        assert_abandoned_call_absent(retained)
        history = reopened.get_messages_as_conversation(session_id)
        with closing(new_agent(reopened, session_id)) as agent:
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
    final_rows = sqlite_snapshot(db_path, session_id)
    assert final_rows[:len(original_rows)] == original_rows
    assert_abandoned_call_absent(final_rows)


@pytest.mark.parametrize("exhaust_retries", [False, True], ids=["retry-succeeds", "retry-exhausted"])
def test_sse_eof_after_committed_write(tmp_path, monkeypatch, offline_chat, exhaust_retries, record_property):
    from agent import tool_executor

    new_agent, SessionDB, registry = offline_chat
    session_id = "sse-post-write"
    db_path = tmp_path / "state.db"
    artifact = tmp_path / "written.txt"
    fact = "A distinctive fixture created exactly once.\n"
    write_id = "call_original_write"
    read_id = "call_new_read"
    write_args = {"path": artifact.name, "content": fact}
    original_input = "Create the requested test artifact."
    new_input = "Read the already existing artifact and report its contents."
    final_answer = "The write was confirmed in this completed reply."
    fragments = [
        "The requested file was created. ",
        "The tool also reported the size. ",
        "The original contents remain available. ",
        "The user-facing response is still unfinished. ",
    ]
    requests = {"seed": [], "write": [], "read": []}
    phase = "seed"
    write_entries = []
    read_entries = []
    timeline = []
    committed_rows = []
    done = b"data: [DONE]\n\n"

    def pair(messages):
        calls = [(index, call) for index, msg in enumerate(messages) if msg["role"] == "assistant"
                 for call in msg.get("tool_calls") or [] if call["id"] == write_id]
        results = [(index, msg) for index, msg in enumerate(messages)
                   if msg["role"] == "tool" and msg.get("tool_call_id") == write_id]
        return calls, results

    def milestone(name):
        with closing(SessionDB(db_path, read_only=True)) as db:
            calls, results = pair(db.get_messages_as_conversation(session_id))
        timeline.append((name, monotonic_ns(), len(calls), len(results)))

    write_entry = registry.get_entry("write_file")
    write_handler = write_entry.handler

    @wraps(write_handler)
    def observe_write(args, **kwargs):
        write_entries.append(dict(args))
        milestone("write handler entry")
        outcome = write_handler(args, **kwargs)
        milestone("write handler returned")
        return outcome

    read_entry = registry.get_entry("read_file")
    read_handler = read_entry.handler

    @wraps(read_handler)
    def observe_read(args, **kwargs):
        read_entries.append(args.get("path"))
        return read_handler(args, **kwargs)

    flush = tool_executor._flush_session_db_after_tool_progress

    @wraps(flush)
    def observe_flush(agent, messages, *, stage):
        if stage == "tool result write_file":
            milestone("before native tool-result flush")
            result = flush(agent, messages, stage=stage)
            milestone("after native tool-result flush")
            committed_rows.extend(sqlite_snapshot(db_path, session_id))
            return result
        return flush(agent, messages, stage=stage)

    monkeypatch.setattr(write_entry, "handler", observe_write)
    monkeypatch.setattr(read_entry, "handler", observe_read)
    monkeypatch.setattr(tool_executor, "_flush_session_db_after_tool_progress", observe_flush)

    def respond(_transport, request):
        if request.method == "GET" and request.url.host == httpx.URL(BASE).host:
            return httpx.Response(404, json={"error": "Synthetic provider metadata"})
        assert request.method == "POST" and str(request.url) == BASE + "/chat/completions"
        body = json.loads(request.content)
        assert body["stream"] and {"write_file", "read_file"} <= {
            tool["function"]["name"] for tool in body["tools"]
        }
        requests[phase].append(body["messages"])
        number = len(requests[phase])
        if phase == "seed":
            assert number == 1
            frames = [chunk({"content": "The original conversation is retained."}, "stop"), done]
        elif phase == "write":
            if number == 1:
                frames = [chunk(tool_delta("write_file", write_id, json.dumps(write_args))),
                          chunk(finish="tool_calls"), done]
            else:
                if number == 2:
                    assert artifact.read_bytes() == fact.encode("utf-8")
                    milestone("first post-tool model request")
                if number == 3 and not exhaust_retries:
                    frames = [chunk({"content": final_answer}, "stop"), done]
                else:
                    assert 2 <= number <= 1 + len(fragments)
                    # Only a text delta, then EOF. No finish_reason, usage or [DONE].
                    frames = [chunk({"content": fragments[number - 2]})]
        elif number == 1:
            frames = [chunk(tool_delta("read_file", read_id, json.dumps({"path": artifact.name}))),
                      chunk(finish="tool_calls"), done]
        else:
            assert number == 2
            frames = [chunk({"content": "The existing artifact was read."}, "stop"), done]
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=EventStream(frames))

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)

    def assert_write_pair(messages):
        [(call_index, call)], [(result_index, message)] = pair(messages)
        assert call_index + 1 == result_index
        assert call["function"]["name"] == "write_file"
        assert json.loads(call["function"]["arguments"]) == write_args
        result = json.loads(message["content"])
        assert result["bytes_written"] == len(fact.encode("utf-8"))
        assert result["verified"] is True and result["resolved_path"] == str(artifact)
        return result

    # Keep the iteration budget above the write round and all four post-tool responses.
    with closing(SessionDB(db_path)) as db, closing(new_agent(db, session_id, max_iterations=8)) as agent:
        seed = agent.run_conversation("Save this unrelated conversation context.")
        assert seed["completed"] is True
        history = db.get_messages_as_conversation(session_id)
        original_rows = sqlite_snapshot(db_path, session_id)
        assert len(original_rows) == 2 and len(history) == 2
        assert not artifact.exists()

        phase = "write"
        turn = agent.run_conversation(original_input, conversation_history=history)
        assert artifact.read_text(encoding="utf-8") == fact
        assert write_entries == [write_args] and read_entries == []
        assert turn["completed"] is (not exhaust_retries)
        if exhaust_retries:
            assert turn["partial"] and turn["failure_reason"] == "truncated" and turn["error"]
            assert all(fragment.strip() in turn["final_response"] for fragment in fragments)
        else:
            assert final_answer in turn["final_response"]
        assert len(requests["write"]) == (5 if exhaust_retries else 3)
        for messages in requests["write"][1:]:
            assert_write_pair(messages)
        durable_pair = assert_write_pair(db.get_messages_as_conversation(session_id))

    milestones = [(name, calls, results) for name, _, calls, results in timeline]
    assert milestones == [
        ("write handler entry", 1, 0),
        ("write handler returned", 1, 0),
        ("before native tool-result flush", 1, 0),
        ("after native tool-result flush", 1, 1),
        ("first post-tool model request", 1, 1),
    ]
    start = timeline[0][1]
    record_property("sqlite_timeline", json.dumps([
        {"checkpoint": name, "elapsed_ms": (t - start) / 1e6, "calls": calls, "results": results}
        for name, t, calls, results in timeline
    ]))
    record_property("post_tool_sse_requests", len(requests["write"]) - 1)
    record_property("initial_turn_completed", turn["completed"])

    phase = "read"
    with closing(SessionDB(db_path)) as reopened:
        retained = sqlite_snapshot(db_path, session_id)
        assert committed_rows[:len(original_rows)] == original_rows
        assert len(committed_rows) == len(original_rows) + 3
        assert retained[:len(committed_rows)] == committed_rows
        history = reopened.get_messages_as_conversation(session_id)
        assert assert_write_pair(history) == durable_pair
        with closing(new_agent(reopened, session_id, max_iterations=8)) as fresh_agent:
            continued = fresh_agent.run_conversation(new_input, conversation_history=history)
        assert continued["completed"] is True
        assert continued["final_response"] == "The existing artifact was read."
        transcript = reopened.get_messages_as_conversation(session_id)
        assert assert_write_pair(transcript) == durable_pair
        assert transcript[-2]["tool_call_id"] == read_id and fact.strip() in transcript[-2]["content"]
        inputs = [msg["content"] for msg in transcript if msg["role"] == "user"]
        assert inputs.count(original_input) == inputs.count(new_input) == 1
    assert all(assert_write_pair(msgs) == durable_pair for msgs in requests["read"])
    assert len(requests["read"]) == 2
    assert requests["read"][0][-1]["role"] == "user" and requests["read"][0][-1]["content"] == new_input
    assert write_entries == [write_args] and read_entries == [artifact.name]
    assert artifact.read_text(encoding="utf-8") == fact
    assert sqlite_snapshot(db_path, session_id)[:len(committed_rows)] == committed_rows
    record_property("write_handler_entries_including_reopened_agent", len(write_entries))
