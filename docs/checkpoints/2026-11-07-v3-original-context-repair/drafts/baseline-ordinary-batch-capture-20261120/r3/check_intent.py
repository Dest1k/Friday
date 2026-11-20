#!/usr/bin/env python3
"""Prove that an unproved ordinary receive cannot yield terminal evidence."""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def load_prior_checks(path):
    spec = importlib.util.spec_from_file_location("friday_poll_witness_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior_checks = load_prior_checks(Path(__file__).resolve().parents[1] / "r2" / "check_witness.py")
fixture = prior_checks.fixture


class PollIntent(prior_checks.PollWitness):
    def interrupt_before_witness(self, run):
        original_write = self.store.write

        def stop_before_witness(path, data):
            if path.name.endswith(".wire"):
                raise KeyboardInterrupt
            return original_write(path, data)

        with patch.object(self.store, "write", side_effect=stop_before_witness):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assertEqual(self.api.reply_poll_count, 1)
        self.assertEqual(list(self.store.root.glob("poll-response-*.wire")), [])

    def assert_stopped_unknown(self, run, message="was not durably retained"):
        resumed, row = self.reopen(run)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(fixture.tester.Uncertain, message):
            resumed.observe(row)
        row = resumed.load(row["id"])
        self.assertEqual(self.api.calls, calls)
        self.assertEqual(row["status"], "STOPPED")
        self.assertEqual(row["stop_phase"], "replay_poll_intent")
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertTrue(row["receive_poll_outcome_unknown"])
        self.assertFalse(row["product_cancelled"])
        self.assertNotIn("capture_window_complete", row)
        self.assertFalse(resumed.receive_inventory(row, terminal=True)[2])
        self.assertEqual(row["capture_until"], 1003)
        self.assertEqual(row["deadline"], 1300)
        self.assertEqual(self.api.calls.count("sendDocument"), 1)
        with self.assertRaisesRegex(fixture.tester.Refused, "Unresolved ordinary receive"):
            resumed.new("new-after-unknown-receive", self.scenario)
        self.assertEqual(self.api.calls, calls)

    def test_r2_reproduces_false_completion_after_predurable_loss(self):
        self.runner = older_r2.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = self.prepare_batch()
        self.api.terminal = self.api.batch
        self.interrupt_before_witness(run)
        self.clock.advance(2)
        resumed = older_r2.Runner(self.store, self.api, self.clock, self.clock.advance)
        row = resumed.load(run["id"])
        resumed.observe(row)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertTrue(row["capture_window_complete"])
        self.assertEqual(row["observations"], [])
        captures, _, _ = resumed.receive_inventory(row, terminal=True)
        self.assertEqual([captures[uid]["arrived_at"] for uid in (101, 102)], [1004, 1004])

    def test_resume_after_predurable_loss_cannot_stamp_timely_batch_late(self):
        run = self.prepare_batch()
        self.api.terminal = self.api.batch
        self.interrupt_before_witness(run)
        resumed, row = self.reopen(run)
        self.assertEqual(resumed.read_poll_intent(row)["outcome"], "PENDING")
        self.clock.advance(2)
        self.assert_stopped_unknown(run)
        self.assertEqual(list(self.store.captures.iterdir()), [])

    def test_interruption_after_intent_before_dispatch_is_conservatively_unknown(self):
        run = self.prepare_batch()
        with patch.object(self.runner, "poll_updates", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assertEqual(self.api.reply_poll_count, 0)
        self.clock.advance(1)
        self.assert_stopped_unknown(run)

    def test_committed_batch_settles_interrupted_poll_before_safe_resume(self):
        run = self.prepare_batch()
        settle = self.runner.settle_poll_intent

        def stop_before_settlement(row, intent, outcome):
            if outcome == "BATCH":
                raise KeyboardInterrupt
            return settle(row, intent, outcome)

        with patch.object(self.runner, "settle_poll_intent", side_effect=stop_before_settlement):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.witness(run)
        resumed, row = self.reopen(run)
        self.assertEqual(resumed.read_poll_intent(row)["outcome"], "PENDING")
        row = self.assert_recovered(run, [101, 102])
        self.assertEqual(resumed.read_poll_intent(row)["outcome"], "BATCH")
        self.assertEqual(self.api.reply_poll_count, 1)

    def test_authenticated_empty_poll_allows_complete_window(self):
        run = self.new()
        self.runner.send(run)
        self.runner.observe(run)
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "EMPTY")
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertTrue(run["capture_window_complete"])
        self.assertEqual(run["reply_outcome"], "NO_RESPONSE_UNVERIFIED")
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["deadline"], 1300)
        self.assertEqual(self.api.reply_poll_count, 1)

    def test_empty_poll_interrupted_before_settlement_remains_unknown(self):
        run = self.new()
        self.runner.send(run)
        settle = self.runner.settle_poll_intent

        def stop_before_empty(row, intent, outcome):
            if outcome == "EMPTY":
                raise KeyboardInterrupt
            return settle(row, intent, outcome)

        with patch.object(self.runner, "settle_poll_intent", side_effect=stop_before_empty):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.clock.advance(2)
        self.assert_stopped_unknown(run)

    def test_local_intent_write_cannot_dispatch_after_original_cutoff(self):
        run = self.prepare_batch()
        open_intent = self.runner.open_poll_intent

        def cross_cutoff(row, cursor):
            intent = open_intent(row, cursor)
            self.clock.advance(3)
            return intent

        with patch.object(self.runner, "open_poll_intent", side_effect=cross_cutoff):
            self.runner.observe(run)
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "NOT_DISPATCHED")
        self.assertEqual(self.api.reply_poll_count, 0)
        self.assertEqual(self.api.calls.count("getUpdates"), 1)
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["deadline"], 1300)

    def test_known_first_rate_limit_preserves_cooldown_and_resume(self):
        run = self.prepare_batch()
        result = self.api.result
        polls = []

        def limit_once(method, params):
            if method == "getUpdates" and params["timeout"] == 1:
                polls.append(params["offset"])
                if len(polls) == 1:
                    raise fixture.tester.RateLimited(1)
            return result(method, params)

        self.api.result = limit_once
        with self.assertRaises(fixture.tester.RateLimited):
            self.runner.observe(run)
        self.assertEqual(run["status"], "RATE_LIMITED_RECEIVE")
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "RATE_LIMITED")
        self.assertEqual(self.store.get(self.store.root / "cooldown.json")["until"], 1001)
        self.clock.advance(1)
        resumed, row = self.reopen(run)
        resumed.observe(row)
        self.assertEqual(polls, [0, 0])
        self.assertEqual(row["capture_until"], 1003)
        self.assertEqual(row["deadline"], 1300)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertEqual(self.api.calls.count("sendDocument"), 1)

    def test_rate_limited_retry_does_not_settle_original_unknown(self):
        run = self.prepare_batch()
        result = self.api.result
        polls = []

        def lose_then_limit(method, params):
            if method == "getUpdates" and params["timeout"] == 1:
                polls.append(params["offset"])
                if len(polls) == 1:
                    raise fixture.tester.Uncertain("synthetic response loss")
                raise fixture.tester.RateLimited(1)
            return result(method, params)

        self.api.result = lose_then_limit
        with self.assertRaisesRegex(fixture.tester.Uncertain, "remains unknown"):
            self.runner.observe(run)
        self.assertEqual(polls, [0, 0])
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(run["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertEqual(run["receive_http_retry"]["outcome"], "RESERVED")
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "PENDING")
        self.assert_stopped_unknown(run)

    def test_empty_value_without_exact_wire_refuses_before_terminal(self):
        run = self.new()
        self.runner.send(run)
        call = self.api.call

        def substitute_empty_wire(method, params=None, *, timeout):
            result = call(method, params, timeout=timeout)
            if method == "getUpdates":
                self.api._last_response = fixture.tester.encoded({"ok": False, "result": []})
            return result

        self.api.call = substitute_empty_wire
        with self.assertRaisesRegex(fixture.tester.Refused, "verified empty response"):
            self.runner.observe(run)
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "PENDING")
        self.assertNotIn("capture_window_complete", run)
        self.assertEqual(self.api.calls.count("getUpdates"), 1)

    def test_linked_batch_cannot_settle_a_different_intent(self):
        run = self.prepare_batch()
        with patch.object(self.runner, "settle_poll_intent", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        intent = self.runner.read_poll_intent(run)
        self.store.put(self.runner.poll_intent_path(run), dict(intent, offset=1))
        resumed, row = self.reopen(run)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "was not durably retained"):
            resumed.observe(row)
        self.assertEqual(self.api.calls, calls)
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("capture_window_complete", row)

    def test_r2_commitments_validate_without_an_intent_file_or_rewrite(self):
        self.runner = older_r2.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = self.prepare_batch()
        self.runner.observe(run)
        before = {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()}
        resumed, row = self.reopen(run)
        self.assertIsNone(resumed.read_poll_intent(row))
        resumed.verify_reply_custody(row)
        self.assertIn("complete", resumed.receive_inventory(row, terminal=True)[2])
        self.assertEqual(before, {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()})


if __name__ == "__main__":
    fixture.tester = fixture.load_tester(sys.argv.pop(1))
    older_r2 = fixture.load_tester(sys.argv.pop(1))
    prior_checks.prior = fixture.load_tester(sys.argv.pop(1))
    unittest.main()
