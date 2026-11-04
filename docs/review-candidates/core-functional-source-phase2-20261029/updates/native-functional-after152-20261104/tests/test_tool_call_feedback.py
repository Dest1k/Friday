"""Offline real parser/ordinary guard/dispatcher tests. No provider is called."""

import copy
import json
from types import SimpleNamespace

import pytest

from conftest import entered, home
from hermes_cli import friday_user_scope as scope
from tools.tool_search import bridge_tool_schemas
from tools.tool_search_validation import normalize_tool_call_entries



def _native_call(args, ident="batch"):
    return SimpleNamespace(id=ident, type="function", function=SimpleNamespace(
        name="tool_call", arguments=json.dumps(args)))


def _dispatch(args):
    import model_tools
    return json.loads(model_tools.handle_function_call("tool_call", args))


@pytest.mark.parametrize("args,path,constraint,fragment", [
    ({}, "calls", "required", "non-empty JSON array"),
    ({"calls": []}, "calls", "minItems", "at least one"),
    ({"calls": 3}, "calls", "type", "JSON array"),
    ({"calls": '[{"arguments":{"query":"sample"}, {"name":"web_extract","arguments":{}}]'},
     "calls", "json_syntax", "not an escaped string"),
    ({"calls": [7]}, "calls[0]", "type", "must be an object"),
    ({"calls": [{"arguments": {"query": "sample"}}]}, "calls[0].name", "required", "Do not infer"),
    ({"calls": [{"name": "web_search", "arguments": '{"query":"sample"'}]},
     "calls[0].arguments", "json_syntax", "actual JSON object"),
    ({"calls": [{"name": "web_search", "arguments": []}]},
     "calls[0].arguments", "type", "JSON object"),
])
def test_argument_fault_reaches_real_ordinary_dispatch_without_leaf_execution(env, monkeypatch, args, path, constraint, fragment):
    import model_tools
    from agent.tool_call_batches import expand_local_tool_batches
    dispatched = []
    monkeypatch.setattr(model_tools.registry, "dispatch", lambda *a, **kw: dispatched.append(a))
    original = copy.deepcopy(args)
    with entered(env):
        call = _native_call(args)
        assert expand_local_tool_batches([call]) == [call]
        result = _dispatch(args)
    assert result["error_type"] == "invalid_arguments"
    assert result["path"] == path and result["constraint"] == constraint
    assert fragment in result["hint"] and "No tool was dispatched" in result["hint"]
    assert dispatched == [] and args == original


def test_feedback_does_not_echo_caller_payload_or_private_parser_exception(env):
    secret = "/home/private/AUTH_TOKEN-user-data"
    args = {"calls": [{"name": "web_search", "arguments": json.dumps(secret)}]}
    with entered(env):
        result = _dispatch(args)
    assert secret not in json.dumps(result)
    assert "Expecting" not in json.dumps(result)
    assert result["path"] == "calls[0].arguments"


@pytest.mark.parametrize("forbidden", ["terminal", "write_file", "tool_search"])
def test_forbidden_sibling_keeps_authority_refusal_not_argument_guidance(env, monkeypatch, forbidden):
    import model_tools
    dispatched = []
    monkeypatch.setattr(model_tools.registry, "dispatch", lambda *a, **kw: dispatched.append(a))
    args = {"calls": [{"name": "web_search", "arguments": {"query": "sample"}},
                      {"arguments": {}}, {"name": forbidden, "arguments": {}}]}
    with entered(env):
        result = _dispatch(args)
    assert "error_type" not in result and "path" not in result
    assert not dispatched


def test_foreign_registry_and_revoked_capability_still_refuse(env):
    args = {"calls": [{"name": "web_search", "arguments": {"query": "sample"}}]}
    with entered(env) as cap:
        with pytest.raises(scope.ScopeDenied):
            scope.guard_tool("tool_call", args, registry_scope=str(home(env, '2')))
        cap.revoked = True
        result = _dispatch({"calls": "["})
    assert "error_type" not in result


def test_rebuilt_local_batch_preserves_arguments_order_ids_and_dispatches_once(env, monkeypatch):
    import model_tools
    from agent.tool_call_batches import expand_local_tool_batches
    from tools.registry import registry
    from tools.web_tools import WEB_SEARCH_SCHEMA, WEB_EXTRACT_SCHEMA
    schemas = [copy.deepcopy(WEB_SEARCH_SCHEMA), copy.deepcopy(WEB_EXTRACT_SCHEMA)]
    defs = [{"type": "function", "function": s} for s in schemas]
    monkeypatch.setattr(model_tools, "get_tool_definitions", lambda **kw: copy.deepcopy(defs))
    observed = []
    # Keep production schemas and the real scoped dispatcher. Replace only the
    # external leaf with a recorder; no fake search results or network requests.
    def record(args, **kw):
        observed.append(copy.deepcopy(args))
        return json.dumps({"offline_leaf_reached": True})
    for schema in schemas:
        entry = registry.get_entry(schema['name'])
        monkeypatch.setattr(entry, "handler", record)
        monkeypatch.setattr(entry, "is_async", False)
    entries = [
        {"name": "web_search", "arguments": {"query": "site:example.test precise model 128GB", "limit": 8}},
        {"name": "web_extract", "arguments": {"urls": ["https://example.test/search?q=precise"], "char_limit": 6000}},
    ]
    with entered(env):
        for string_form in (False, True):
            args = {"calls": json.dumps(entries) if string_form else copy.deepcopy(entries)}
            call = _native_call(args)
            before = copy.deepcopy(call)
            expanded = expand_local_tool_batches([call])
            assert len(expanded) == 2 and call == before
            assert len({c.id for c in expanded}) == 2
            assert [c.id for c in expanded] == [c.id for c in expand_local_tool_batches([call])]
            for child in expanded:
                result = _dispatch(json.loads(child.function.arguments))
                assert result.get('offline_leaf_reached') is True, result
    assert observed == [entries[0]['arguments'], entries[1]['arguments']] * 2


def test_valid_legacy_and_json_string_forms_remain_compatible():
    entry = {"name": "web_search", "arguments": {"query": "precise", "limit": 8}}
    for args in (entry, {"calls": [entry]}, {"calls": entry}, {"calls": json.dumps([entry])},
                 {"calls": [{"name": entry['name'], "arguments": json.dumps(entry['arguments'])}]}):
        assert normalize_tool_call_entries(args) == ([entry], None)


def test_advertised_and_sanitized_schema_require_native_array_and_entry_name():
    from jsonschema import Draft202012Validator
    from tools.schema_sanitizer import sanitize_tool_schemas
    schema = next(x for x in bridge_tool_schemas(2) if x['function']['name'] == 'tool_call')
    for exposed in (schema, sanitize_tool_schemas([schema])[0]):
        validator = Draft202012Validator(exposed['function']['parameters'])
        assert validator.is_valid({'calls': [{'name': 'web_search', 'arguments': {'query': 'precise'}}]})
        assert not validator.is_valid({'calls': '[]'})
        assert not validator.is_valid({'calls': []})
        assert not validator.is_valid({'calls': [{'arguments': {'query': 'precise'}}]})
