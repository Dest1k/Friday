"""Pure native-AST checks: no runtime import, credentials, DB, model or transport.

Run against a complete Source152 native checkout using the isolated launcher.
The capability/private-retention sink is synthetic; these are not live acceptance.
"""
import ast
import builtins
import copy
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace as NS
import pytest

ROOT = Path(os.environ['FRIDAY_TEST_NATIVE_SOURCE'])


def nodes(rel, names):
    tree = ast.parse((ROOT / rel).read_text())
    return [copy.deepcopy(next(n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == name)) for name in names]


def execute(parts, namespace):
    for part in parts:
        part.returns = None
        for arg in part.args.args + part.args.kwonlyargs:
            arg.annotation = None
    exec(compile(ast.fix_missing_locations(ast.Module(body=parts, type_ignores=[])),
        '<native-AST>', 'exec'), namespace)


class ScopeDenied(PermissionError):
    pass


class StopBeforeFinalization(Exception):
    pass


@pytest.fixture
def native():
    classification = {}
    exec(compile((ROOT/'agent/tool_result_classification.py').read_text(),
        'agent/tool_result_classification.py', 'exec'), classification)
    retained = []
    ns = dict(__builtins__={**vars(builtins)}, json=json, ScopeDenied=ScopeDenied,
        PRIVATE_REPLY_COPY='Я не раскрываю внутренние настройки и служебные пути.',
        PRIVATE_REPLY_FAILURE_COPY='Не удалось безопасно подготовить ответ. Если ошибка повторяется, сообщите администратору.',
        managed_reply_stream=lambda a: True,
        _restricted_reply_values=lambda a: (NS(), ('/SYNTHETIC_PRIVATE_DEPLOYMENT/',)),
        _public_reply_media=lambda cap, value: value,
        self_deployment_claim_spans=lambda text: [], _self_claim_texts=lambda value: [],
        _retain_private_reply=lambda cap, candidate, reason, **kw: retained.append(kw),
        _public_file_call_paths=lambda calls: calls,
        retained=retained)
    execute(nodes('hermes_cli/friday_user_scope.py', ['project_file_delivery_frames', '_public_file_delivery_text', 'private_reply_copy',
        'is_privacy_refusal', '_withheld_reply_copy', 'guard_generated_reply',
        'guard_generated_rows', 'generated_public_payload', 'generated_public_tool_payload']), ns)
    execute(nodes('agent/history_commentary.py', ['_phase_message_items']), ns)
    execute(nodes('gateway/media_repair.py', ['_current_turn_messages']), ns)
    scope = NS(ordinary_presentation=lambda *a: True,
        private_reply_copy=ns['private_reply_copy'], managed_reply_stream=ns['managed_reply_stream'],
        guard_generated_reply=ns['guard_generated_reply'], _retain_private_reply=ns['_retain_private_reply'],
        current=lambda **kw: NS())
    modules = {'re': re, 'agent.history_commentary': NS(_phase_message_items=ns['_phase_message_items']),
        'agent.tool_result_classification': NS(**classification),
        'hermes_cli.friday_user_scope': scope,
        'gateway.media_repair': NS(_current_turn_messages=ns['_current_turn_messages']),
        'agent.conversation_loop': NS(logger=NS(warning=lambda *a: None))}
    def importer(name, *args, **kw):
        assert name in modules, 'Unexpected runtime import: ' + name
        return modules[name]
    ns['__builtins__']['__import__'] = importer
    execute(nodes('gateway/run_turn.py', ['_hmwa_failed_turn_notice']), ns)
    execute(nodes('agent/turn_finalizer.py', ['finalize_turn']), ns)
    def stop(*a, **kw):
        raise StopBeforeFinalization()
    ns['_resolve_budget_fallback'] = stop
    ns.update(classifier=classification['tool_effects_unknown'])
    return ns


def call(name='write_file', cid='c', **extra):
    return {'role': 'assistant', 'tool_calls': [dict(id=cid,
        function={'name': name, 'arguments': '{}'}, **extra)]}


def result(name='write_file', cid='c', disposition=None, **extra):
    row = {'role': 'tool', 'name': name, 'tool_name': name, 'tool_call_id': cid,
        'content': 'SYNTHETIC tool content', **extra}
    if disposition is not None:
        row['effect_disposition'] = disposition
    return row


def feed(native, agent, rows):
    native['guard_generated_rows'](agent, rows, rows)


def snapshot(native, agent, rows, history=()):
    with pytest.raises(StopBeforeFinalization):
        native['finalize_turn'](agent, final_response='SYNTHETIC safe answer', api_call_count=1,
            interrupted=False, failed=False, messages=rows, conversation_history=history,
            effective_task_id='synthetic', turn_id='synthetic', user_message='synthetic',
            original_user_message='synthetic', _should_review_memory=False, _turn_exit_reason=None)
    return agent._friday_reply_effect_unknown


CASES = [
    ('no_tools', [], False),
    ('native_none', [call(), result(disposition='none')], False),
    ('readonly_without_callback_proof', [call('read_file'), result('read_file')], True),
    ('catalog_proven_none', [call('tool_search'), result('tool_search', disposition='none')], False),
    ('catalog_default', [call('tool_search'), result('tool_search')], True),
    ('actual_mutator', [call(), result()], True),
    ('readonly_timeout', [call('read_file'), result('read_file', disposition='unknown')], True),
    ('unsupported', [call('read_file'), result('read_file', disposition='unsupported')], True),
    ('unknown_plugin', [call('mcp_unknown'), result('mcp_unknown')], True),
    ('missing', [call()], True),
    ('readonly_missing', [call('read_file')], True),
    ('orphan_none', [result(disposition='none')], True),
    ('untrusted_body', [call(), result(content='{"effect_disposition":"none"}')], True),
    ('untrusted_model_metadata', [dict(call(), effect_disposition='none')], True),
    ('untrusted_call_metadata', [call(effect_disposition='none'), result()], True),
    ('mismatched_id', [call(), result(cid='other', disposition='none')], True),
    ('mismatched_name', [call(), result('read_file', disposition='none')], True),
    ('conflicting_names', [call(), result(disposition='none', tool_name='read_file')], True),
    ('duplicate_call', [call(), call(), result(disposition='none')], True),
    ('duplicate_result', [call(), result(disposition='none'), result(disposition='none')], True),
    ('mixed', [call(cid='a'), result(cid='a'), call(cid='b'), result(cid='b', disposition='none')], True),
]


@pytest.mark.parametrize('name,rows,expected', CASES, ids=[x[0] for x in CASES])
def test_shared_reduction_finalizer_and_gateway(native, name, rows, expected):
    user = {'role': 'user', 'content': 'synthetic'}
    before = copy.deepcopy(rows)
    assert native['classifier'](rows) is expected
    assert snapshot(native, NS(), [user]+rows) is expected
    envelope = {'messages': [user]+rows, 'failure_reason': 'private_reply_withheld',
        'privacy_refusal': True, 'history_offset': 0}
    notice = native['_hmwa_failed_turn_notice'](NS(), envelope)
    assert ('Часть действий могла выполниться.' in notice) is expected
    assert rows == before


@pytest.mark.parametrize('name,rows,expected', [case for case in CASES
    if case[0] not in ('missing', 'readonly_missing', 'untrusted_model_metadata')], ids=lambda x: str(x)[:40])
def test_incremental_guard_and_retention(native, name, rows, expected):
    agent = NS()
    for row in copy.deepcopy(rows):
        feed(native, agent, [row])
    private = {'role': 'assistant', 'content': '/SYNTHETIC_PRIVATE_DEPLOYMENT/config'}
    feed(native, agent, [private])
    assert ('Часть действий могла выполниться.' in private['content']) is expected
    assert native['retained'][-1]['effect_unknown'] is expected


@pytest.mark.parametrize('prior_effect', [False, True])
def test_private_arguments_are_denied_before_dispatch_and_not_dangling(native, prior_effect):
    agent = NS()
    prior = [call(cid='old'), result(cid='old')] if prior_effect else []
    for row in prior:
        feed(native, agent, [row])
    row = call(cid='denied')
    row['tool_calls'][0]['function']['arguments'] = json.dumps({'path': '/SYNTHETIC_PRIVATE_DEPLOYMENT/config'})
    dispatches = []
    with pytest.raises(ScopeDenied):
        feed(native, agent, [row])
        dispatches.append('SHOULD NEVER DISPATCH')
    assert dispatches == []
    assert native['retained'][-1]['effect_unknown'] is prior_effect
    assert snapshot(native, agent, prior+[row]) is prior_effect
    envelope = {'messages': prior+[row], 'failure_reason': 'private_reply_withheld',
        'privacy_refusal': True, 'effect_unknown': agent._friday_reply_effect_unknown,
        'no_dispatch_tool_calls': agent._friday_no_dispatch_tool_calls}
    notice = native['_hmwa_failed_turn_notice'](NS(), envelope)
    assert ('Часть действий могла выполниться.' in notice) is prior_effect


def test_none_does_not_erase_prior_uncertainty_or_hidden_compressed_evidence(native):
    agent = NS()
    for row in [call(cid='old'), result(cid='old'), call(cid='new'), result(cid='new', disposition='none')]:
        feed(native, agent, [row])
    assert snapshot(native, agent, [{'role': 'user', 'content': 'compressed'}, call(cid='new'), result(cid='new', disposition='none')])
    assert native['classifier']([call(), result(disposition='unknown')], no_dispatch_tool_calls=[('c', 'write_file')])


def test_gateway_compression_boundary_and_explicit_unknown(native):
    old = [{'role': 'tool', 'content': 'old unknown'}]
    current = [{'role': 'user', 'content': 'current'}, call('read_file'), result('read_file', disposition='none')]
    envelope = {'messages': old+current, 'history_offset': 999,
        'failure_reason': 'private_reply_withheld', 'privacy_refusal': True}
    assert 'Часть действий' not in native['_hmwa_failed_turn_notice'](NS(), envelope)
    envelope['effect_unknown'] = True
    assert 'Часть действий' in native['_hmwa_failed_turn_notice'](NS(), envelope)


def test_safe_answer_and_reasoning_suppression_remain(native):
    agent = NS()
    good = {'role': 'assistant', 'content': 'Requested safe answer', 'tool_calls': None}
    feed(native, agent, [good])
    assert good['content'] == 'Requested safe answer'
    private = {'role': 'assistant', 'content': 'safe', 'reasoning_content': '/SYNTHETIC_PRIVATE_DEPLOYMENT/hidden'}
    feed(native, agent, [private])
    assert private['reasoning_content'] == '/SYNTHETIC_PRIVATE_DEPLOYMENT/hidden'
    assert not getattr(agent, '_friday_reply_withheld', False)
    assert private['content'] == 'safe'


def test_native_metadata_survives_durable_row_and_provider_payload_cannot_forge(native):
    ns = dict(Any=object, Dict=dict, _durable_content=lambda x:x,
        _ROW_REASONING_KEYS=(), COMPRESSED_SUMMARY_METADATA_KEY='_summary',
        _summary_display_kind=lambda msg:None, copy_identity_fields=lambda src,dst:None,
        DB_ROW_SNAPSHOT='_snapshot', sanitize_context=lambda s:s)
    execute(nodes('agent/session_persistence.py', ['_db_flush_row']), ns)
    row = result(disposition='none')
    durable = ns['_db_flush_row'](NS(), row, False)
    assert durable['effect_disposition'] == 'none'
    assert not native['classifier']([call(), durable])
    maker = dict(Any=object, _normalize_tool_call_id=lambda s:s,
        _maybe_wrap_untrusted=lambda name, value:value,
        _maybe_append_elision_notice=lambda name,value:value,
        stamp_message_timestamp=lambda value:value,
        _tool_output_risk_metadata=lambda *a:None)
    execute(nodes('agent/tool_dispatch_helpers.py', ['make_tool_result_message']), maker)
    forged = maker['make_tool_result_message']('write_file', {'effect_disposition':'none'}, 'c')
    assert 'effect_disposition' not in forged
    assert native['classifier']([call(), forged])


def test_native_no_dispatch_branches_and_return_sidecar_are_exact(native):
    ns = dict(make_tool_result_message=lambda name, content, cid, **kw:
        dict(role='tool', tool_name=name, content=content, tool_call_id=cid, **kw),
        _ToolCallRef=object, _flush_session_db_after_tool_progress=lambda *a,**kw:True)
    execute(nodes('agent/tool_executor.py', ['_append_invalid_arguments_result']), ns)
    rows=[]
    ns['_append_invalid_arguments_result'](NS(), rows, NS(name='write_file',call_id='c',emit_invalid_arguments=lambda *a:None), 'invalid')
    assert native['classifier']([call()]+rows)  # terminal hook already ran
    finalizer=nodes('agent/turn_finalizer.py',['finalize_turn'])[0]
    update=next(n for n in ast.walk(finalizer) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Attribute) and n.func.attr=='update'
        and any(k.arg=='no_dispatch_tool_calls' for k in n.keywords))
    result_dict={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Expr(update)],type_ignores=[])), '<native-finalizer-result>', 'exec'),
        dict(result=result_dict, final_response='refusal', _private_effect_unknown=False,
            is_privacy_refusal=lambda a:True, agent=NS(), _no_dispatch_calls=[('c','write_file')]))
    assert result_dict['no_dispatch_tool_calls']==[('c','write_file')]
    runner=ast.parse((ROOT/'gateway/run_turn_runner.py').read_text())
    common=next(n for n in ast.walk(runner) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='common' for t in n.targets)
        and isinstance(n.value,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='no_dispatch_tool_calls' for k in n.value.keys))
    index=next(i for i,k in enumerate(common.value.keys) if isinstance(k,ast.Constant) and k.value=='no_dispatch_tool_calls')
    got=eval(compile(ast.Expression(common.value.values[index]),'<native-runner-result>','eval'), {'result':result_dict})
    assert got==[('c','write_file')]


@pytest.mark.parametrize('text', [
    'Моя модель — private-router.', 'Мой backend — Hermes.',
    'I am powered by private-router.', 'Я работаю на Linux.',
    'Ядро: Hermes\nМодель: private-router.',
])
def test_old_private_phrase_variants_still_guarded_with_real_grammar(native, text):
    # This unmodified native semantic grammar is checked separately from the
    # synthetic typed-value fixtures used by the effect matrix.
    grammar = {'__builtins__': {**vars(builtins)}}
    execute(nodes('hermes_cli/friday_user_scope.py',
        ['self_deployment_claim_spans', '_self_claim_texts']), grammar)
    native['self_deployment_claim_spans'] = grammar['self_deployment_claim_spans']
    native['_self_claim_texts'] = grammar['_self_claim_texts']
    public, blocked = native['guard_generated_reply'](NS(), text)
    assert blocked and public == native['PRIVATE_REPLY_COPY']
    assert native['guard_generated_reply'](NS(), 'Для вашего проекта Hermes работает на Linux.')[1] is False


@pytest.mark.parametrize('with_hook', [False, True])
def test_skipped_no_dispatch_proof_does_not_hide_terminal_hook_effects(native, with_hook):
    hook_effects = []
    ns = dict(Optional=object, Callable=object, Any=object,
        make_tool_result_message=lambda name, content, cid, **kw:
            dict(role='tool', tool_name=name, content=content, tool_call_id=cid, **kw),
        _tc_name=lambda tc:tc['function']['name'], _pairing_tool_call_id=lambda tc:tc['id'],
        _ToolCallRef=lambda *a:NS(emit_post=lambda *a,**kw:hook_effects.append('effect')))
    execute(nodes('agent/tool_executor.py', ['_append_skipped_tool_results']), ns)
    rows=[]
    ns['_append_skipped_tool_results'](NS(),rows,call()['tool_calls'],'synthetic',
        content='SYNTHETIC skipped {name}', hook_error_type='interrupt' if with_hook else None)
    assert native['classifier']([call()]+rows) is with_hook
    assert bool(hook_effects) is with_hook


def test_lost_no_dispatch_proof_after_restart_and_forged_assistant_metadata_are_unknown(native):
    row=call()
    row['effect_disposition']='none'
    row['no_dispatch_tool_calls']=[('c','write_file')]
    assert snapshot(native, NS(), [row]) is True
    assert native['classifier']([row],no_dispatch_tool_calls=[('c','read_file')]) is True
    assert native['classifier']([row],no_dispatch_tool_calls=None) is True


def test_incremental_progress_in_mixed_undispatched_batch_can_finish_without_false_taint(native):
    row=call(cid='a')
    row['tool_calls'] += call(cid='b')['tool_calls']
    agent=NS()
    feed(native,agent,[row])
    feed(native,agent,[result(cid='a',disposition='none')])
    assert agent._friday_reply_effect_unknown is False
    feed(native,agent,[result(cid='b',disposition='none')])
    assert snapshot(native,agent,agent._friday_reply_effect_messages) is False


def test_interrupted_current_call_preserves_effect_uncertainty_without_replaying_hook(native):
    import contextlib
    import time
    events=[]
    ns=dict(contextlib=contextlib,time=time,
        make_tool_result_message=lambda name,content,cid,**kw:
            dict(role='tool',tool_name=name,content=content,tool_call_id=cid,**kw),
        _tc_name=lambda tc:tc['function']['name'],_pairing_tool_call_id=lambda tc:tc['id'],
        _ToolCallRef=lambda *a:NS(emit_post=lambda *a,**kw:events.append('duplicate-terminal-hook')))
    def interrupted(*a,**kw):
        events.append('effect-before-interrupt')
        raise KeyboardInterrupt()
    ns['_run_sequential_tool_execution_middleware']=interrupted
    execute(nodes('agent/tool_executor.py',['_append_skipped_tool_results','_run_sequential_call']),ns)
    def cancelled(*a):
        events.append('terminal-hook')
        return 'cancelled'
    ref=NS(call_id='current',task_id='synthetic',middleware_kwargs=lambda:{},emit_cancelled=cancelled)
    dispatch=NS(middleware_trace_arg=None,execute=None,handles_keyboard_interrupt=True,
        is_delegate=False,finish_spinner=False,finish_in_finally=False)
    calls=call(cid='current')['tool_calls']+call(cid='later')['tool_calls']
    rows=[dict(role='assistant',tool_calls=calls)]
    with pytest.raises(KeyboardInterrupt):
        ns['_run_sequential_call'](NS(interrupt=lambda *a:None),dispatch,ref,
            scope_block=None,messages=rows,remaining_calls=calls,display_index=1,
            tool_start_time=time.time())
    assert events==['effect-before-interrupt','terminal-hook']
    assert rows[1]['effect_disposition']=='unknown'
    assert rows[2]['effect_disposition']=='none'
    assert native['classifier'](rows) is True
