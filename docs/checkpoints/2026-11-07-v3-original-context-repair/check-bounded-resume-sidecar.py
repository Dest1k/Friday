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

    def rows(self, *, sidecar_differs, mutate_protected=False):
        """The rows of a resumed turn.

        With ``sidecar_differs`` the current user row carries the transcript projection in
        ``content`` and the sent bytes in ``api_content`` - exactly what the resume path
        produces when the recovery note is the persist override.
        """
        # The PROTECTED row in the history: its content is the transcript projection and it
        # carries NO sidecar - that is what the resume path leaves behind.
        protected_current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        # The INCOMING row of the same turn: the sent bytes are in its api_content sidecar,
        # so the wire projection differs from the transcript projection.
        current = {'role': 'user', 'content': RESUME_NOTE + "\n\n" + REQUEST_TEXT}
        if sidecar_differs:
            current['api_content'] = RESUME_NOTE + "\n\n" + REQUEST_TEXT + "\n\n[live bytes]"
        # The layout mirrors the live run of 2026-11-09: the system authority, then the
        # compressed middle, then the protected tail that holds the current ask, its
        # assistant turn and its tool result.
        rows = [
            {'role': 'system', 'content': 'Original authority.'},
            {'role': 'assistant', 'content': 'Compressed middle summary.'},
            current,
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

    def arm_contract(self, rows):
        """The protected contract holds the ORIGINAL bytes of the protected rows."""
        from agent.bounded_context import remember_bounded_protected_rows
        contract_rows = copy.deepcopy(rows)
        for row in contract_rows:
            row.pop('api_content', None)
        for row in contract_rows:
            if row.get('role') == 'tool':
                row['content'] = 'Exact completed result.'
        remember_bounded_protected_rows(self.compressor, contract_rows, 1, 2)

    def arm_context(self, rows, incoming):
        """Record the request context the guard reads, exactly as the compressor does."""
        from agent.bounded_context import remember_bounded_compaction_context
        remember_bounded_compaction_context(self.agent, copy.deepcopy(rows),
                                            2, '', '', None, copy.deepcopy(rows))
        self.agent._bounded_compaction_request_context['incoming'] = copy.deepcopy(incoming)

    def request(self, rows, wire_rows=None):
        """The wire request.

        In the live run the wire carries the current row WITH its sidecar, because the turn
        start stamped the sent bytes onto the live dict before the request was assembled. The
        protected contract, in contrast, keeps the transcript projection of that row.
        """
        rows = copy.deepcopy(wire_rows if wire_rows is not None else rows)
        return assemble_api_request(self.agent, messages=rows,
            current_turn_user_idx=2, _ext_prefetch_cache='',
            _plugin_user_context='', moa_config=None, active_system_prompt='',
            original_user_message=rows[2].get('api_content') or rows[2]['content'],
            pending_moa_prepared_request=None,
            request_logger=logging.getLogger('RESUME-SIDECAR')).api_messages

    def test_resumed_turn_with_a_sidecar_is_currently_refused(self):
        """The defect: a resumed turn whose sent bytes differ from its transcript text is refused."""
        rows = self.rows(sidecar_differs=True)
        self.arm_contract(rows)
        self.arm_context(rows, rows[2])
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "resumed turn with a differing sidecar",
                          "refused": True, "detail": detail[:220]}, ensure_ascii=False))
        self.assertIn("bounded_context", detail)

    def test_the_same_turn_without_a_sidecar_is_accepted(self):
        """The control: with no sidecar the two representations agree and the guard passes."""
        rows = self.rows(sidecar_differs=False)
        self.arm_contract(rows)
        self.arm_context(rows, rows[2])
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        guard_main_request(self.agent, request)
        print(json.dumps({"case": "the same turn without a sidecar", "refused": False},
                         ensure_ascii=False))

    def test_a_rewritten_protected_row_is_still_refused(self):
        """The guard must keep refusing a formatter that really rewrites a protected row."""
        rows = self.rows(sidecar_differs=False, mutate_protected=True)
        self.arm_contract(rows)
        self.arm_context(rows, rows[2])
        wire_rows = copy.deepcopy(rows)
        if wire_rows[2].get('api_content'):
            wire_rows[2]['content'] = wire_rows[2]['api_content']
        request = {'model': 'dispatcher', 'max_tokens': 4096,
                   'messages': self.request(rows, wire_rows)}
        with self.assertRaises(Exception) as caught:
            guard_main_request(self.agent, request)
        detail = str(caught.exception)
        print(json.dumps({"case": "a genuinely rewritten protected row", "refused": True,
                          "detail": detail[:220]}, ensure_ascii=False))
        self.assertIn("bounded_context", detail)


if __name__ == "__main__":
    # unittest parses sys.argv; the operator role is restored after the run
    _TEST_ARGV = list(sys.argv)
    unittest.main(verbosity=2, argv=_TEST_ARGV[:1])
