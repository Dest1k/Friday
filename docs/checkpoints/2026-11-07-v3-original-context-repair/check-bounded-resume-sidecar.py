#!/usr/bin/env python3
"""Offline reproduction of the bounded-context guard defect found on 2026-11-09.

The defect: when the gateway resumes a turn, the recovery note acts as a persist OVERRIDE
for the current user turn. The transcript row then carries the override as its ``content``
while the bytes actually sent are kept in the ``api_content`` sidecar. The bounded-context
guard builds the current group through ``build_api_messages``, which substitutes the sidecar
into the wire copy, so the guard compares the SENT bytes of the current turn against the
TRANSCRIPT bytes of the same row. For a resumed turn those two always differ and the guard
refuses with "formatter removed or rewrote protected authority/user/tool rows", although no
formatter changed anything.

The check uses the product's own modules, without a model and without a network. It asserts
the CURRENT behaviour (the defect is present) and it also asserts that the guard still
refuses a genuinely rewritten protected row - that part must not regress.

The serving composition is NOT modified: the check imports modules and calls them
in-process and writes nothing into the home.

Run it with the interpreter of the installed environment:
  /home/jericho/.hermes/installs/<id>/environments/<id>/venv/bin/python check-bounded-resume-sidecar.py
"""
import copy
import json
import logging
import os
import sys
import unittest
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME") or
            "/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
os.environ["HERMES_HOME"] = str(HOME)
# NEVER write byte-code into the installed composition: the plugin inventory is checked
# against the install marker, and a __pycache__ directory would break that check.
sys.dont_write_bytecode = True
sys.pycache_prefix = "/home/jericho/.dsh/tmp/frw-pycache"
sys.path.insert(0, str(HOME / "hermes-agent"))

# The product's admission inspects the process arguments: a plain python script is not an
# admitted native role. The operator role 'gateway status' is an admitted one, so the check
# presents itself as that role for the duration of the import. No service is contacted.
_REAL_ARGV = list(sys.argv)
sys.argv = [str(HOME / "hermes-agent" / ".hermes" / "bin" / "hermes"), "gateway", "status"]

# When a compact bench carries a MODIFIED agent/bounded_context.py and the bench itself is
# too partial to import the full product (its run_agent needs the owned state that only a
# complete home has), BOUNDED_CONTEXT_OVERRIDE names that file. The agent package and every
# other module still come from HERMES_HOME, and only agent.bounded_context is replaced by
# the bench's copy. This exercises the real module bytes that the bench would publish.
import importlib.util as _importlib_util
_OVERRIDE = os.environ.get("BOUNDED_CONTEXT_OVERRIDE")
if _OVERRIDE:
    import agent as _agent_pkg  # noqa: F401  (the real package, from HERMES_HOME)
    _spec = _importlib_util.spec_from_file_location("agent.bounded_context", _OVERRIDE)
    _mod = _importlib_util.module_from_spec(_spec)
    sys.modules["agent.bounded_context"] = _mod
    _spec.loader.exec_module(_mod)
    _agent_pkg.bounded_context = _mod

try:
    from agent.bounded_context import (  # noqa: E402
        BoundedContextPolicy, guard_main_request, remember_bounded_protected_rows,
    )
    from agent.context_compressor import ContextCompressor  # noqa: E402
    from agent.turn_request_assembly import assemble_api_request  # noqa: E402

    # The user-scope projection is a privacy boundary of the serving product: it needs an
    # authenticated, routed user principal. It is NOT part of the bounded-context guard, so
    # the check replaces it with the identity it would apply - the rows are returned
    # unchanged - in order to exercise the guard itself.
    import hermes_cli.friday_user_scope as _scope
    _scope.public_identity_request_view = lambda agent, api_messages: api_messages
finally:
    # the admitted operator role stays in place: the product reads the process arguments
    # again when the real agent class is imported
    pass

# --- module provenance: every verdict must name the module it was produced against ----
# The guard under test is agent.bounded_context. The file it was actually imported from
# and its SHA256 are recorded so a verdict cannot be read as applying to a different
# tree. The import path is the one that is first on sys.path, which is HERMES_HOME's
# hermes-agent directory; the venv interpreter is separate and only supplies the
# dependencies.
import hashlib as _hashlib
_MODULE_PATH = Path(sys.modules['agent.bounded_context'].__file__).resolve()
_MODULE_SHA256 = _hashlib.sha256(_MODULE_PATH.read_bytes()).hexdigest()
sys.stderr.write("MODULE_PROVENANCE " + json.dumps({
    "module": "agent.bounded_context",
    "loaded_from": str(_MODULE_PATH),
    "sha256": _MODULE_SHA256,
    "hermes_home": str(HOME),
}, ensure_ascii=False) + "\n")

RESUME_NOTE = (
    "[System note: The previous turn was interrupted by a gateway interruption; the gateway "
    "is now back online. Any restart/shutdown command in the history has already run - do "
    "NOT re-execute or verify it. Address the user's NEW message below FIRST and focus on "
    "what the user is asking now. Do NOT re-execute old tool calls - skip any unfinished work "
    "from the conversation history.]"
)
REQUEST_TEXT = (
    "[The user sent a document: 'orders_complex_features.xlsx'. It is saved at: "
    "received/telegram_cf39a6e960edaa6b5526aff7840075f3ef59f67bcc313682f341475c4074b962_"
    "orders_complex_features.xlsx. Its text is not inlined here (it's a binary format such as "
    "PDF or DOCX). To read it, extract the document's text yourself - for example with the "
    "terminal tool or the ocr-and-documents skill - before answering, instead of asking the "
    "user to paste the contents.]\n\nСделай сводку по всем исходным строкам Orders."
)
# A DIFFERENT protected user message: an earlier completed exchange that is also inside
# the protected tail. Two different protected user rows are what the current-ask
# identification has to tell apart.
PREVIOUS_ASK = (
    "[The user sent a document: 'report_v1.docx'. It is saved at: "
    "received/telegram_1111111111111111111111111111111111111111111111111111111111111111_"
    "report_v1.docx. Its text is not inlined here (it's a binary format such as "
    "PDF or DOCX). To read it, extract the document's text yourself - for example with the "
    "terminal tool or the ocr-and-documents skill - before answering, instead of asking the "
    "user to paste the contents.]\n\nСделай сводку по версии 1."
)


def build_agent(compressor):
    """The agent surface the bounded guard reads.

    The real class is used with its constructor skipped, exactly as the product's own
    source-only tests do it, so the guard sees the production methods instead of stubs.
    """
    from run_agent import AIAgent
    agent = AIAgent.__new__(AIAgent)
    agent.__dict__.update(
        model='dispatcher', provider='custom',
        requested_provider='custom:friday-local', api_mode='chat_completions',
        max_tokens=4096, context_compressor=compressor,
        _bounded_context_policy=compressor.bounded_context_policy,
        tools=[], _current_turn_timestamp=1791973748.9341815,
        ephemeral_system_prompt=None, _reasoning_echo_flag=False,
        request_overrides={}, prefill_messages=None, _use_prompt_caching=False,
        _usage_anchor=None, client=None, session_id='resume-sidecar')
    agent.base_url = 'http://192.168.1.78:8001/v1'
    return agent


class ResumeSidecarReproduction(unittest.TestCase):
    def setUp(self):
        p = BoundedContextPolicy('custom:friday-local', 'dispatcher',
            'http://192.168.1.78:8001/v1', 40960, 40954, 4096, 4096, 1024, 2048, 4096)
        c = ContextCompressor('dispatcher', config_context_length=40960,
            provider='custom', base_url=p.base_url, api_mode='chat_completions',
            max_tokens=4096, quiet_mode=True)
        c.bounded_context_policy = p
        self.agent = build_agent(c)
        self.compressor = c
        self._contract_carries_sent_bytes = False
        self._contract_keeps_the_sidecar = False

    def rows(self, *, sidecar_differs, mutate_protected=False):
        """The rows of a resumed turn.

        With ``sidecar_differs`` the current user row carries the transcript projection in
        ``content`` and the sent bytes in ``api_content`` - exactly what the resume path
        produces when the recovery note is the persist override.
        """
        # The PROTECTED row in the history: its content is the transcript projection and it
        # carries NO sidecar - that is what the resume path leaves behind.
        protected_current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        # The INCOMING row of the same turn. In the live run the incoming row carried the
        # transcript text in its content and the SENT bytes in its api_content sidecar; the
        # wire projection substitutes the sidecar, so the request carries the sent bytes.
        current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        if sidecar_differs:
            # the LIVE row: the sent bytes are in content and in the sidecar
            current['content'] = RESUME_NOTE + "\n\n" + REQUEST_TEXT + "\n\n[live bytes]"
            current['api_content'] = RESUME_NOTE + "\n\n" + REQUEST_TEXT + "\n\n[live bytes]"
        # The layout mirrors the live run of 2026-11-09: the system authority, then the
        # compressed middle, then the protected tail that holds the current ask, its
        # assistant turn and its tool result.
        rows = [
            {'role': 'system', 'content': 'Original authority.'},
            {'role': 'assistant', 'content': 'Compressed middle summary.'},
            # the PROTECTED row keeps the transcript text; the sent bytes live in its sidecar
            protected_current if not sidecar_differs else dict(protected_current, **(
                {'api_content': current['api_content']} if current.get('api_content') else {})),
            {'role': 'assistant', 'content': '', 'reasoning_content': 'Exact reasoning.',
             'tool_calls': [{'id': 'write', 'type': 'function', 'function': {
                 'name': 'write_file', 'arguments': json.dumps(
                     {'path': '/existing', 'content': 'Резюме'}, ensure_ascii=False)}}]},
            {'role': 'tool', 'tool_call_id': 'write', 'content': 'Exact completed result.'},
        ]
        if mutate_protected:
            # a real tampering of a protected row: the tool result in the WIRE is rewritten,
            # while the protected contract keeps the original bytes
            rows[4]['content'] = 'Exact completed result, rewritten by the formatter.'
            self._mutated_tool = True
        return rows

    def arm_contract(self, rows, original_tool=None):
        """The protected contract holds the ORIGINAL bytes of the protected rows.

        In the live run the contract rows are the LIVE rows: they carry the transcript text
        in content and the SENT bytes in the api_content sidecar, and the anchors keep the
        sidecar. This is what the compressor stores.

        ``original_tool`` maps tool_call_id -> original content. It is used when the setup
        carries more than one tool row and only the one that a negative control mutates
        must be restored; the other rows keep their own bytes.
        """
        from agent.bounded_context import remember_bounded_protected_rows
        contract_rows = copy.deepcopy(rows)
        for row in contract_rows:
            if row.get('role') == 'tool':
                if original_tool is not None:
                    row['content'] = original_tool.get(row.get('tool_call_id'),
                                                      row.get('content'))
                else:
                    row['content'] = 'Exact completed result.'
        if self._contract_carries_sent_bytes:
            for row in contract_rows:
                if row.get('role') == 'user' and row.get('api_content'):
                    row['content'] = row['api_content']
        remember_bounded_protected_rows(self.compressor, contract_rows, 1, 2)

    def arm_context(self, rows, incoming, current_idx=2):
        """Record the request context the guard reads, exactly as the compressor does."""
        from agent.bounded_context import remember_bounded_compaction_context
        remember_bounded_compaction_context(self.agent, copy.deepcopy(rows),
                                            current_idx, '', '', None, copy.deepcopy(rows))
        # the guard reads the incoming row from here; it is the LIVE row of the current turn
        self.agent._bounded_compaction_request_context['incoming'] = copy.deepcopy(incoming)
        print(json.dumps({"arm_context": {"passed_len": len(incoming.get('content') or ''),
                                          "rows2_len": len(rows[current_idx].get('content') or ''),
                                          "stored_len": len(self.agent._bounded_compaction_request_context['incoming'].get('content') or '')}},
                         ensure_ascii=False))

    def diagnose(self):
        """Why is the current anchor not found?"""
        import agent.bounded_context as bc
        from agent.conversation_compression import _strip_marker_for_comparison
        c = self.compressor
        head, tail = c._bounded_protected_rows
        anchors = bc._bounded_protected_wire_anchors(c, head, tail)
        ctx = getattr(self.agent, '_bounded_compaction_request_context', None)
        incoming = ctx.get('incoming') if isinstance(ctx, dict) else None
        def ident(row):
            row = dict(row)
            for k in ("api_content", "_row_id", "_submit_row_session_id"):
                row.pop(k, None)
            return _strip_marker_for_comparison([row])
        print(json.dumps({"anchors_roles": [r.get('role') for r in anchors],
                          "anchor_user_keys": sorted(next((r for r in anchors if r.get('role') == 'user'), {}).keys()),
                          "incoming_keys": sorted((incoming or {}).keys()),
                          "identity_equal": bool(ident(next((r for r in anchors if r.get('role') == 'user'), {})) == ident(incoming or {})),
                          "anchor_user_len": len((next((r for r in anchors if r.get('role') == 'user'), {}).get('content') or '')),
                          "incoming_len": len(((incoming or {}).get('content') or '')),
                          "contract_tail_user_len": len((c._bounded_protected_rows[1][0].get('content') or '')) if c._bounded_protected_rows and c._bounded_protected_rows[1] else None,
                          "contract_tail_user_has_sidecar": ('api_content' in c._bounded_protected_rows[1][0]) if c._bounded_protected_rows and c._bounded_protected_rows[1] else None,
                          "anchor_head": (next((r for r in anchors if r.get('role') == 'user'), {}).get('content') or '')[:70],
                          "incoming_head": ((incoming or {}).get('content') or '')[:70]},
                         ensure_ascii=False))

    def compare_group(self, request=None):
        """Compare the current_group against the wire the way the guard does."""
        import agent.bounded_context as bc
        from agent.turn_context import build_api_messages, normalize_api_message_text
        ctx = getattr(self.agent, '_bounded_compaction_request_context', None)
        incoming = ctx.get('incoming') if isinstance(ctx, dict) else None
        current_view, _ = build_api_messages(self.agent, [incoming], current_turn_user_idx=0,
            ext_prefetch_cache='', plugin_user_context='', moa_config=None,
            active_system_prompt='')
        group = [row for row in current_view if row.get('role') == 'user']
        normalize_api_message_text(group)
        actual_user = [r for r in (request['messages'] or []) if r.get('role') == 'user']
        au = actual_user[0] if actual_user else {}
        print(json.dumps({"group_vs_actual": {
            "group_content_eq": group[0].get('content') == au.get('content'),
            "group_content_len": len(group[0].get('content') or ''),
            "actual_content_len": len(au.get('content') or ''),
            "group_keys": sorted(group[0].keys()),
            "actual_keys": sorted(au.keys()),
            "group_role": group[0].get('role'), "actual_role": au.get('role'),
            "group_tcid": group[0].get('tool_call_id'), "actual_tcid": au.get('tool_call_id'),
            "group_reasoning": group[0].get('reasoning_content'), "actual_reasoning": au.get('reasoning_content'),
            "group_tc": group[0].get('tool_calls'), "actual_tc": au.get('tool_calls')}},
                         ensure_ascii=False))
        print(json.dumps({"group_user_len": len(group[0].get('content') or ''),
                          "group_keys": sorted(group[0].keys()),
                          "group_row_keys": sorted((group[0] or {}).keys()),
                          "group_extra": {k: (type(v).__name__, len(v) if isinstance(v, (str, list, dict)) else v)
                                          for k, v in (group[0] or {}).items() if k not in ('role', 'content')},
                          "group_role": group[0].get('role'),
                          "group_reasoning": group[0].get('reasoning_content'),
                          "group_tool_calls": group[0].get('tool_calls'),
                          "group_tool_call_id": group[0].get('tool_call_id')},
                         ensure_ascii=False))

    def request(self, rows, wire_rows=None, current_idx=2):
        """The wire request.

        In the live run the wire carries the current row WITH its sidecar, because the turn
        start stamped the sent bytes onto the live dict before the request was assembled. The
        protected contract, in contrast, keeps the transcript projection of that row.
        """
        rows = copy.deepcopy(wire_rows if wire_rows is not None else rows)
        return assemble_api_request(self.agent, messages=rows,
            current_turn_user_idx=current_idx, _ext_prefetch_cache='',
            _plugin_user_context='', moa_config=None, active_system_prompt='',
            original_user_message=rows[current_idx].get('api_content') or rows[current_idx]['content'],
            pending_moa_prepared_request=None,
            request_logger=logging.getLogger('RESUME-SIDECAR')).api_messages

    def test_resumed_turn_with_a_sidecar_is_accepted(self):
        """A resumed turn whose sent bytes differ from its transcript text is ACCEPTED.

        Before the layer 'bounded-resume-sidecar-guard' this was refused with
        'formatter removed or rewrote protected authority/user/tool rows', although no
        formatter had changed anything: the guard compared the SENT bytes of the current
        ask with the TRANSCRIPT bytes of the same row. The refused case is proved on the
        pre-layer tree, and the accepted case here proves the fix.
        """
        rows = self.rows(sidecar_differs=True)
        self.arm_contract(rows)
        incoming_row = copy.deepcopy(rows[2])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        # the request assembly re-records the context with the rows it assembled, so the
        # incoming row is the WIRE row: its content is the sent bytes
        self.arm_context(wire_rows, wire_rows[2])
        guard_main_request(self.agent, request)
        print(json.dumps({"case": "resumed turn with a differing sidecar", "refused": False},
                         ensure_ascii=False))

    def test_the_contract_with_the_sent_bytes_is_accepted(self):
        """The experiment: the contract carries the SENT bytes of the current row."""
        self._contract_carries_sent_bytes = True
        rows = self.rows(sidecar_differs=True)
        self.arm_contract(rows)
        incoming_row = copy.deepcopy(rows[2])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        # the request assembly re-records the context with the rows it assembled, so the
        # incoming row is the WIRE row: its content is the sent bytes
        self.arm_context(wire_rows, wire_rows[2])
        guard_main_request(self.agent, request)
        print(json.dumps({"case": "the contract carries the sent bytes", "refused": False},
                         ensure_ascii=False))

    def test_the_same_turn_without_a_sidecar_is_accepted(self):
        """The control: with no sidecar the two representations agree and the guard passes."""
        rows = self.rows(sidecar_differs=False)
        self.arm_contract(rows)
        incoming_row = copy.deepcopy(rows[2])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        # the request assembly re-records the context with the rows it assembled, so the
        # incoming row is the WIRE row: its content is the sent bytes
        self.arm_context(wire_rows, wire_rows[2])
        self.diagnose()
        guard_main_request(self.agent, request)
        print(json.dumps({"case": "the same turn without a sidecar", "refused": False},
                         ensure_ascii=False))

    def test_a_rewritten_protected_row_is_still_refused(self):
        """The guard must keep refusing a formatter that really rewrites a protected row."""
        rows = self.rows(sidecar_differs=False, mutate_protected=True)
        self.arm_contract(rows)
        incoming_row = copy.deepcopy(rows[2])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        # the request assembly re-records the context with the rows it assembled, so the
        # incoming row is the WIRE row: its content is the sent bytes
        self.arm_context(wire_rows, wire_rows[2])
        self.diagnose()
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "a genuinely rewritten protected row", "refused": True,
                          "detail": detail[:220]}, ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    # ------------------------------------------------- the differing-sidecar negatives
    #
    # The negative control above runs with sidecar_differs=False, so it does NOT prove that
    # the protection survives in the CHANGED branch of the guard. The fix changed the way
    # the current ask is identified: the identity is now also accepted when the SENT
    # projection of a row matches. A changed branch that accepts too much would be a real
    # regression, so the negatives below run with sidecar_differs=True: the same branch
    # that accepts a correct resume must still refuse a changed request.
    #
    # Two independent substitutions are made, one per negative:
    #   * the SENT current request is changed  -> the sent bytes no longer match;
    #   * the PROTECTED result of the tool is changed -> the protected contract no longer
    #     matches the wire.
    # The correct resume with a differing sidecar must keep passing.

    def _resume_with_sidecar(self):
        """Arm the accepted resume with a differing sidecar and return (rows, request)."""
        rows = self.rows(sidecar_differs=True)
        self.arm_contract(rows)
        incoming_row = copy.deepcopy(rows[2])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        # the request assembly re-records the context with the rows it assembled, so the
        # incoming row is the WIRE row: its content is the sent bytes
        self.arm_context(wire_rows, wire_rows[2])
        return rows, wire_rows, request

    def test_a_changed_sent_request_with_a_sidecar_is_refused(self):
        """The SENT current request is changed while the sidecar differs -> REFUSED.

        This is the negative control for the CHANGED branch: the fix lets the current ask
        be identified through the representation the request sends it in. If the sent
        bytes are altered, that identification must fail and the guard must refuse.

        The substitution is made in the SIDE-CAR of the current user row, because that is
        the representation the request actually sends: the wire projection substitutes
        the sidecar into ``content``, so a change of ``content`` alone would be erased
        by the assembly and would not be a change of the sent request at all.
        """
        rows, wire_rows, request = self._resume_with_sidecar()
        # the SENT bytes of the current ask are changed: the sidecar now carries
        # different bytes, and they differ from the transcript text of the contract
        wire_rows[2]['api_content'] = (wire_rows[2].get('api_content') or '') \
            + "\n\n[rewritten by the formatter]"
        request['messages'] = self.request(rows, wire_rows)
        self.arm_context(wire_rows, wire_rows[2])
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "a changed sent request with a differing sidecar",
                          "refused": True, "detail": detail[:220]}, ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    def test_a_changed_protected_result_with_a_sidecar_is_refused(self):
        """The PROTECTED tool result is changed while the sidecar differs -> REFUSED.

        The protected result of the tool is part of the contract. Changing it in the wire
        must be refused even though the current ask itself is still identified correctly
        through the sent projection.
        """
        rows, wire_rows, request = self._resume_with_sidecar()
        wire_rows[4]['content'] = 'Exact completed result, rewritten by the formatter.'
        request['messages'] = self.request(rows, wire_rows)
        self.arm_context(wire_rows, wire_rows[2])
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "a changed protected result with a differing sidecar",
                          "refused": True, "detail": detail[:220]}, ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    def test_the_correct_resume_with_a_sidecar_still_passes(self):
        """The control of the two negatives above: the correct resume keeps passing."""
        rows, wire_rows, request = self._resume_with_sidecar()
        guard_main_request(self.agent, request)
        print(json.dumps({"case": "the correct resume with a differing sidecar",
                          "refused": False}, ensure_ascii=False))

    # -------------------------- two different protected user messages in the tail ------
    #
    # The protected tail is the part of the conversation after the compressed middle
    # (remember_bounded_protected_rows stores original[compress_end:]). When more than one
    # turn was completed after the compaction, the tail holds MORE THAN ONE user row, so
    # the guard sees two (or more) user anchors. The current-turn identification must then
    # pick the RIGHT anchor: it must not make two different protected user rows look like
    # the same ask, and it must not become ambiguous.
    #
    # This is a real layout: the compaction is called once per session and the tail keeps
    # every exchange after compress_end, including completed earlier turns.

    def rows_two_users(self, *, sidecar_differs=True):
        """A protected tail with TWO different protected user messages.

        Index 2 is a COMPLETED earlier exchange (its own ask, its own assistant turn, its
        own tool result). Index 5 is the CURRENT ask. Both are in the protected tail, so
        the guard sees two user anchors and must identify the current one.
        """
        prev_user = {'role': 'user', 'content': PREVIOUS_ASK}
        prev_assistant = {'role': 'assistant', 'content': '',
                          'reasoning_content': 'Previous reasoning.',
                          'tool_calls': [{'id': 'prev', 'type': 'function', 'function': {
                              'name': 'read_file', 'arguments': json.dumps(
                                  {'path': '/report_v1.docx'}, ensure_ascii=False)}}]}
        prev_tool = {'role': 'tool', 'tool_call_id': 'prev',
                     'content': 'Previous completed result.'}
        protected_current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        if sidecar_differs:
            current['content'] = RESUME_NOTE + "\n\n" + REQUEST_TEXT + "\n\n[live bytes]"
            current['api_content'] = RESUME_NOTE + "\n\n" + REQUEST_TEXT + "\n\n[live bytes]"
        current_anchor = (protected_current if not sidecar_differs else dict(
            protected_current, **({'api_content': current['api_content']}
                                  if current.get('api_content') else {})))
        rows = [
            # 0 head
            {'role': 'system', 'content': 'Original authority.'},
            # 1 compressed middle (not in the protected contract)
            {'role': 'assistant', 'content': 'Compressed middle summary.'},
            # 2 tail: previous completed ask
            prev_user,
            # 3 tail: previous assistant turn
            prev_assistant,
            # 4 tail: previous tool result
            prev_tool,
            # 5 tail: CURRENT ask
            current_anchor,
            # 6 tail: current assistant turn
            {'role': 'assistant', 'content': '', 'reasoning_content': 'Exact reasoning.',
             'tool_calls': [{'id': 'write', 'type': 'function', 'function': {
                 'name': 'write_file', 'arguments': json.dumps(
                     {'path': '/existing', 'content': 'Резюме'}, ensure_ascii=False)}}]},
            # 7 tail: current tool result
            {'role': 'tool', 'tool_call_id': 'write', 'content': 'Exact completed result.'},
        ]
        return rows

    def test_two_protected_users_resume_with_sidecar_is_accepted(self):
        """A correct resume with a differing sidecar and TWO protected user messages.

        The protected tail holds a completed earlier exchange AND the current ask, so the
        guard sees two user anchors. The correct resume must identify the CURRENT ask as
        the current anchor and must NOT be refused as ambiguous. This is the product test
        of the current-ask identification: the module under test is agent.bounded_context,
        loaded from the path recorded below.

        The tail is original[compress_end:] (see remember_bounded_protected_rows), so a
        conversation with more than one completed exchange after the compaction really does
        carry more than one protected user row in the guard's anchors.
        """
        rows = self.rows_two_users(sidecar_differs=True)
        self.arm_contract(rows, original_tool={'prev': 'Previous completed result.',
                                              'write': 'Exact completed result.'})
        incoming_row = copy.deepcopy(rows[5])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row, current_idx=5)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[5].get('api_content'):
            wire_rows[5]['content'] = wire_rows[5]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows, current_idx=5)}
        self.arm_context(wire_rows, wire_rows[5], current_idx=5)
        guard_main_request(self.agent, request)
        print(json.dumps({
            "case": "correct resume with differing sidecar and two protected user messages",
            "refused": False,
            "module": {"loaded_from": str(_MODULE_PATH), "sha256": _MODULE_SHA256},
        }, ensure_ascii=False))

    def test_two_protected_users_changed_previous_ask_is_refused(self):
        """A changed PREVIOUS protected user message must still be refused.

        With two protected user rows the current-ask identification must not weaken the
        protection of the OTHER protected user row: rewriting the previous ask in the wire
        must be refused even though the current ask is identified correctly.
        """
        rows = self.rows_two_users(sidecar_differs=True)
        self.arm_contract(rows, original_tool={'prev': 'Previous completed result.',
                                              'write': 'Exact completed result.'})
        incoming_row = copy.deepcopy(rows[5])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row, current_idx=5)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[5].get('api_content'):
            wire_rows[5]['content'] = wire_rows[5]['api_content']
        # the PREVIOUS protected user message is rewritten in the wire
        wire_rows[2]['content'] = PREVIOUS_ASK + "\n\n[rewritten by the formatter]"
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows, current_idx=5)}
        self.arm_context(wire_rows, wire_rows[5], current_idx=5)
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "two users: a changed previous protected user message",
                          "refused": True, "detail": detail[:220],
                          "module": {"loaded_from": str(_MODULE_PATH), "sha256": _MODULE_SHA256}},
                         ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    def test_two_protected_users_changed_sent_request_is_refused(self):
        """A changed SENT current request must still be refused with two protected users.

        The identification must not accept a current ask whose sent bytes were altered,
        even when another protected user row is present.
        """
        rows = self.rows_two_users(sidecar_differs=True)
        self.arm_contract(rows, original_tool={'prev': 'Previous completed result.',
                                              'write': 'Exact completed result.'})
        incoming_row = copy.deepcopy(rows[5])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row, current_idx=5)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[5].get('api_content'):
            wire_rows[5]['content'] = wire_rows[5]['api_content']
        # the SENT bytes of the current ask are changed (in the sidecar: that is the
        # representation the request actually sends)
        wire_rows[5]['api_content'] = (wire_rows[5].get('api_content') or '') \
            + "\n\n[rewritten by the formatter]"
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows, current_idx=5)}
        self.arm_context(wire_rows, wire_rows[5], current_idx=5)
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "two users: a changed sent current request",
                          "refused": True, "detail": detail[:220],
                          "module": {"loaded_from": str(_MODULE_PATH), "sha256": _MODULE_SHA256}},
                         ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    def test_two_protected_users_changed_tool_result_is_refused(self):
        """A changed PROTECTED tool result must still be refused with two protected users."""
        rows = self.rows_two_users(sidecar_differs=True)
        self.arm_contract(rows, original_tool={'prev': 'Previous completed result.',
                                              'write': 'Exact completed result.'})
        incoming_row = copy.deepcopy(rows[5])
        if incoming_row.get('api_content'):
            incoming_row['content'] = incoming_row['api_content']
        self.arm_context(rows, incoming_row, current_idx=5)
        wire_rows = copy.deepcopy(rows)
        if wire_rows[5].get('api_content'):
            wire_rows[5]['content'] = wire_rows[5]['api_content']
        # the protected result of the CURRENT tool is rewritten in the wire
        wire_rows[7]['content'] = 'Exact completed result, rewritten by the formatter.'
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows, current_idx=5)}
        self.arm_context(wire_rows, wire_rows[5], current_idx=5)
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "two users: a changed protected tool result",
                          "refused": True, "detail": detail[:220],
                          "module": {"loaded_from": str(_MODULE_PATH), "sha256": _MODULE_SHA256}},
                         ensure_ascii=False))
        self.assertIn("bounded_context", detail)


if __name__ == "__main__":
    # unittest parses sys.argv; the operator role is restored after the run
    _TEST_ARGV = list(sys.argv)
    unittest.main(verbosity=2, argv=_TEST_ARGV[:1])
