import copy
import json
import sqlite3
from types import SimpleNamespace

import pytest

from agent.session_persistence import SessionPersistenceMixin
from agent.turn_finalizer import finalize_turn
from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from hermes_state import SessionDB
from hermes_cli import friday_product_access as access
from hermes_cli import friday_user_scope as users


class FakeAgent(SessionPersistenceMixin):
    def __init__(self, db, cap):
        self.max_iterations = 90
        self.iteration_budget = SimpleNamespace(remaining=10, used=1, max_total=90)
        self.quiet_mode = True
        self.model = "test-model"
        self.provider = "test-provider"
        self.base_url = ""
        self.platform = "telegram"
        self.session_id = "scoped-recovery"
        self.context_compressor = SimpleNamespace(last_prompt_tokens=0)
        self.request_overrides = {}
        self.valid_tool_names = []
        self.skip_background_review = True
        self._tool_guardrail_halt_decision = None
        self._interrupt_message = None
        self._response_was_previewed = False
        self._skill_nudge_interval = 0
        self._iters_since_skill = 0
        self._session_db = db
        self._session_db_created = True
        self._session_persist_lock = None
        self._last_flushed_db_idx = 0
        self._flushed_db_message_ids = set()
        self._db_flush_scan_prefix = None
        self._persist_user_message_idx = None
        self._persist_user_message_override = None
        self._persist_user_message_timestamp = None
        self._persist_user_message_platform_id = None
        self._friday_user_scope = cap
        self._friday_private_stream = True
        self._friday_room_guard = None
        self._friday_delegation = None
        self._friday_reply_effect_messages = []
        self._friday_no_dispatch_tool_calls = []
        self._friday_reply_effect_unknown = False
        self._friday_buffered_reply_parts = []
        self._friday_reply_stream_published = True
        self._current_streamed_assistant_text = ""
        self._reused_response_text = None
        for key in (
            "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
            "reasoning_tokens", "prompt_tokens", "completion_tokens", "total_tokens",
        ):
            setattr(self, "session_" + key, 0)
        self.session_estimated_cost_usd = 0
        self.session_cost_status = "unknown"
        self.session_cost_source = "test"

    def _ensure_db_session(self):
        self._session_db_created = True

    def _persist_session(self, messages, conversation_history):
        return self._flush_messages_to_session_db(messages, conversation_history)

    def _drop_trailing_empty_response_scaffolding(self, messages):
        pass

    def _save_trajectory(self, *args, **kwargs):
        pass

    def _cleanup_task_resources(self, *args, **kwargs):
        pass

    def _file_mutation_verifier_enabled(self):
        return False

    def _turn_completion_explainer_enabled(self):
        return False

    def _drain_pending_steer(self):
        return None

    def clear_interrupt(self):
        pass

    def _sync_external_memory_for_turn(self, **kwargs):
        pass

    def _safe_print(self, *args, **kwargs):
        pass

    def _emit_status(self, *args, **kwargs):
        pass


@pytest.fixture
def scoped_home(tmp_path, monkeypatch):
    monkeypatch.setattr("hermes_cli.plugins.invoke_hook", lambda *args, **kwargs: [])
    authorization_home = tmp_path / "authorization"
    home = authorization_home / "profiles" / "ordinary"
    home.mkdir(parents=True, mode=0o700)
    (home / "memories").mkdir(mode=0o700)
    (home / "workspace").mkdir(mode=0o700)
    binding = {
        "platform": "telegram",
        "transport_profile": "transport",
        "account_id": "account",
        "user_id": "user",
        "runtime_profile": "ordinary",
        "tools": ["read_file", "write_file"],
    }
    principal = ("telegram", "transport", "account", "user")
    key = access.principal_id(*principal)
    marker = {
        "schema": "friday.user-home.v1",
        "principal": key,
        "profile": "ordinary",
        "binding_sha256": users._fingerprint(binding),
    }
    (home / users.MARKER).write_text(json.dumps(marker), encoding="utf-8")
    (home / users.MARKER).chmod(0o600)
    policy = {"enabled": True, "bindings": [binding]}
    account = {
        "platform": "telegram",
        "transport_profile": "transport",
        "account_id": "account",
        "runtime_profiles": ["ordinary"],
    }
    admitted = {
        "platform": "telegram",
        "transport_profile": "transport",
        "account_id": "account",
        "user_id": "user",
        "enabled": True,
        "role": "user",
        "generation": 1,
    }
    monkeypatch.setattr(users, "policy", lambda _home: policy)
    monkeypatch.setattr(access, "access_policy", lambda: {"enabled": True, "accounts": [account]})
    monkeypatch.setattr(access, "current_access", lambda: {"schema": access.KEY, "users": {key: admitted}})
    stat = home.stat()
    cap = users.UserScope(
        authorization_home, home, "ordinary", principal, binding,
        (stat.st_dev, stat.st_ino), 1,
    )
    db = SessionDB(db_path=home / "state.db")
    origin = {
        "friday_account_origin": {
            "schema": "friday.account_origin.v1",
            "platform": "telegram",
            "transport_profile": "transport",
            "account_id": "account",
        }
    }
    db.create_session(
        "scoped-recovery", "telegram", user_id="user", profile_name="ordinary",
        origin_json=json.dumps(origin),
    )
    scope_token = users._CURRENT.set(cap)
    home_token = set_hermes_home_override(str(home))
    try:
        yield cap, home, db
    finally:
        users._CURRENT.reset(scope_token)
        reset_hermes_home_override(home_token)
        db.close()


def finish(agent, messages):
    return finalize_turn(
        agent,
        final_response="",
        api_call_count=2,
        interrupted=False,
        failed=True,
        messages=messages,
        conversation_history=[],
        effective_task_id="task",
        turn_id="turn",
        user_message="do it",
        original_user_message="do it",
        _should_review_memory=False,
        _turn_exit_reason="session_persistence_failed",
    )


def unsafe_messages(home):
    return [
        {"role": "user", "content": "do it"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "denied-call",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": json.dumps({"path": str(home / "cache" / "spill.json")}),
                },
            }],
        },
    ]


def test_valid_scoped_file_workflow_and_path_negatives(scoped_home):
    cap, home, _db = scoped_home
    written = json.loads(users.scoped_file("write_file", {"path": "note.txt", "content": "hello"}))
    assert written["success"] is True
    read = json.loads(users.scoped_file("read_file", {"path": "note.txt"}))
    assert read["success"] is True and "hello" in read["content"]
    cap.check()
    for path in (".env", "../foreign/secret", str(home / "cache" / "spill.json")):
        with pytest.raises(users.ScopeDenied):
            users.scoped_file("read_file", {"path": path})
    assert (home / "workspace" / "note.txt").read_text() == "hello"


def test_typed_rejected_arguments_remain_safe_and_durable(scoped_home):
    cap, _home, db = scoped_home
    agent = FakeAgent(db, cap)
    error = users.ordinary_tool_error_json(
        "product_user_scope_refused", cause=users.ScopeArgumentError("tool_call")
    )
    messages = [
        {"role": "user", "content": "do it"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "bad-args",
                "type": "function",
                "function": {"name": "tool_call", "arguments": "{\"calls\":[]}"},
            }],
        },
        {
            "role": "tool",
            "name": "tool_call",
            "tool_call_id": "bad-args",
            "content": error,
            "effect_disposition": "none",
        },
        {"role": "assistant", "content": "Invalid arguments; no file was created."},
    ]
    assert agent._flush_messages_to_session_db(messages, []) is True
    rows = db.get_messages_as_conversation(agent.session_id)
    assert [row["role"] for row in rows] == ["user", "assistant", "tool", "assistant"]
    assert json.loads(rows[2]["content"])["error_type"] == "invalid_arguments"
    assert rows[-1]["content"] == "Invalid arguments; no file was created."
    agent._friday_reply_withheld = False
    agent._friday_reply_withheld_reason = None
    agent._friday_no_dispatch_tool_calls = []
    agent._friday_reply_effect_messages = []
    agent._friday_reply_effect_unknown = False
    messages.extend([
        {"role": "user", "content": "correct it"},
        {"role": "assistant", "content": "safe correction"},
    ])
    assert agent._flush_messages_to_session_db(messages, []) is True
    assert db.get_messages_as_conversation(agent.session_id)[-1]["content"] == "safe correction"


def test_rejected_private_call_persists_safe_close_and_next_turn(scoped_home):
    cap, home, db = scoped_home
    agent = FakeAgent(db, cap)
    messages = unsafe_messages(home)
    rejected = messages[1]
    before = copy.deepcopy(rejected)
    assert agent._flush_messages_to_session_db(messages, []) is False
    assert db.get_messages_as_conversation(agent.session_id) == []

    result = finish(agent, messages)

    assert result["turn_exit_reason"] == "private_reply_withheld"
    assert result["failure_reason"] == "private_reply_withheld"
    assert "session_persistence_failed" not in result.get("failure_reason", "")
    assert result["final_response"] == users.PRIVATE_REPLY_COPY
    assert result["no_dispatch_tool_calls"] == [["denied-call", "read_file"]] or result["no_dispatch_tool_calls"] == [("denied-call", "read_file")]
    assert rejected == before
    rows = db.get_messages_as_conversation(agent.session_id)
    assert [row["role"] for row in rows] == ["user", "assistant"]
    assert rows[-1]["content"] == users.PRIVATE_REPLY_COPY
    assert not rows[-1].get("tool_calls")
    assert str(home) not in json.dumps(rows)
    assert agent._friday_withheld_tool_call_close_pending is False

    agent._friday_reply_withheld = False
    agent._friday_reply_withheld_reason = None
    agent._friday_no_dispatch_tool_calls = []
    agent._friday_reply_effect_messages = []
    agent._friday_reply_effect_unknown = False
    messages.extend([
        {"role": "user", "content": "next"},
        {"role": "assistant", "content": "safe next answer"},
    ])
    assert agent._flush_messages_to_session_db(messages, []) is True
    rows = db.get_messages_as_conversation(agent.session_id)
    assert [row["role"] for row in rows] == ["user", "assistant", "user", "assistant"]
    assert rows[-1]["content"] == "safe next answer"


def test_real_database_failure_is_not_hidden_by_safe_close(scoped_home, monkeypatch):
    cap, home, db = scoped_home
    agent = FakeAgent(db, cap)
    messages = unsafe_messages(home)
    assert agent._flush_messages_to_session_db(messages, []) is False

    def fail_append(**kwargs):
        raise sqlite3.OperationalError("synthetic append failure")

    monkeypatch.setattr(db, "append_messages_batch", fail_append)
    result = finish(agent, messages)

    assert result["turn_exit_reason"] == "session_persistence_failed"
    assert result["failure_reason"].startswith("session_persistence_failed:")
    assert agent._friday_withheld_tool_call_close_pending is True
    assert db.get_messages_as_conversation(agent.session_id) == []


def _mixed_rejected_messages(private_name):
    from agent.conversation_loop import _invalid_tool_name_error_content
    return [
        {"role": "user", "content": "do it"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "safe-read", "type": "function", "function": {
                "name": "read_file", "arguments": '{"path":"note.txt"}'}},
            {"id": "invalid-name", "type": "function", "function": {
                "name": private_name, "arguments": "{}"}},
        ]},
        {"role": "tool", "name": private_name, "tool_call_id": "invalid-name",
         "content": _invalid_tool_name_error_content(private_name, ["read_file", "write_file"])},
    ]


@pytest.mark.parametrize("private_kind", ["profile", "path"])
def test_recovery_removes_private_staged_errors(scoped_home, private_kind):
    cap, home, db = scoped_home
    private_name = cap.profile if private_kind == "profile" else str(home / "cache" / "private-name")
    agent = FakeAgent(db, cap)
    messages = _mixed_rejected_messages(private_name)
    original = copy.deepcopy(messages)
    assert agent._flush_messages_to_session_db(messages, []) is False
    assert db.get_messages_as_conversation(agent.session_id) == []
    result = finish(agent, messages)
    assert result["turn_exit_reason"] == "private_reply_withheld"
    assert result["effect_unknown"] is True  # Native unproven error metadata remains conservative.
    for rows in (messages, db.get_messages_as_conversation(agent.session_id)):
        public = [users.ordinary_message_view(row) for row in rows]
        assert private_name not in json.dumps(public)
        assert not any(row.get("tool_call_id") for row in public)
    assert [row["role"] for row in messages] == ["user", "assistant"]
    assert [row["role"] for row in db.get_messages_as_conversation(agent.session_id)] == ["user", "assistant"]
    # The guarded original is preserved by reference for private effect accounting.
    assert agent._friday_reply_effect_messages[1]["tool_calls"] == original[1]["tool_calls"]


def test_recovery_preserves_prior_effects_and_unrelated_staged_rows(scoped_home):
    cap, _home, db = scoped_home
    agent = FakeAgent(db, cap)
    prior = [
        {"role": "user", "content": "do it"},
        {"role": "assistant", "content": "", "tool_calls": [{
            "id": "earlier-write", "type": "function", "function": {
                "name": "write_file", "arguments": '{"path":"note.txt","content":"x"}'}}]},
        {"role": "tool", "name": "write_file", "tool_call_id": "earlier-write",
         "content": "unknown earlier outcome", "effect_disposition": "unknown"},
    ]
    assert agent._flush_messages_to_session_db(prior, []) is True
    old = copy.deepcopy(prior)
    messages = prior + _mixed_rejected_messages(cap.profile)[1:]
    unrelated = {"role": "tool", "name": "other_tool", "tool_call_id": "unrelated",
                 "content": "independent observation", "effect_disposition": "unknown"}
    messages.append(unrelated)
    assert agent._flush_messages_to_session_db(messages, []) is False
    result = finish(agent, messages)
    assert result["effect_unknown"] is True and result["partial"] is True
    assert messages[:3] == old
    assert any(row is unrelated for row in messages)
    assert not any(row.get("tool_call_id") == "invalid-name" for row in messages)
    assert db.get_messages_as_conversation(agent.session_id)[2]["content"] == "unknown earlier outcome"
