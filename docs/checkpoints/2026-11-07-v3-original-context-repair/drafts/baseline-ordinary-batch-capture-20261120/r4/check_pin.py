#!/usr/bin/env python3
"""Check independent active-poll custody and the last pre-dispatch guard."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def load_checks(path):
    spec = importlib.util.spec_from_file_location("friday_poll_intent_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior_checks = load_checks(Path(__file__).resolve().parents[1] / "r3" / "check_intent.py")
fixture = prior_checks.fixture


class PollPin(prior_checks.PollIntent):
    def start_reply(self):
        run = self.prepare_batch()
        self.api.terminal = self.api.batch
        return run

    def stop_before_batch_write(self, run):
        write = self.store.write

        def interrupt(path, data):
            if path.name.endswith(".wire"):
                raise KeyboardInterrupt
            return write(path, data)

        with patch.object(self.store, "write", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)

    def reopen_r3(self, run):
        resumed = older_r3.Runner(self.store, self.api, self.clock, self.clock.advance)
        return resumed, resumed.load(run["id"])

    def test_r3_reproduces_completion_after_deleting_pending(self):
        self.runner = older_r3.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = self.start_reply()
        self.stop_before_batch_write(run)
        self.runner.poll_intent_path(run).unlink()
        self.clock.advance(2)
        resumed, row = self.reopen_r3(run)
        resumed.observe(row)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertTrue(row["capture_window_complete"])
        self.assertEqual(row["observations"], [])

    def test_missing_pinned_pending_blocks_restart_before_network(self):
        run = self.start_reply()
        self.stop_before_batch_write(run)
        saved_pin = self.runner.load(run["id"])["poll_intent_pin"]
        self.runner.poll_intent_path(run).unlink()
        self.clock.advance(2)
        calls = list(self.api.calls)
        resumed, row = self.reopen(run)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "Pinned ordinary poll intent is missing"):
            resumed.observe(row)
        self.assertEqual(row["status"], "STOPPED")
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("capture_window_complete", row)
        self.assertEqual(row["poll_intent_pin"], saved_pin)
        self.assertEqual(self.api.calls, calls)

    def rollback_pending_to_previous_empty(self):
        run = self.start_reply()
        settle = self.runner.settle_poll_intent
        original_result = self.api.result
        previous = []

        def remember_empty(row, intent, outcome):
            settle(row, intent, outcome)
            if outcome == "EMPTY":
                previous.append(self.runner.poll_intent_path(row).read_bytes())

        def empty_then_reply(method, params):
            if method == "getUpdates" and params["timeout"] == 1:
                self.api.reply_poll_count += 1
                if self.api.reply_poll_count == 1:
                    return []
                self.clock.advance(1)
                return self.api.batch
            return original_result(method, params)

        self.api.result = empty_then_reply
        with patch.object(self.runner, "settle_poll_intent", side_effect=remember_empty):
            self.stop_before_batch_write(run)
        path = self.runner.poll_intent_path(run)
        pending = json.loads(path.read_bytes())
        older = json.loads(previous[0])
        self.assertEqual((pending["head"], pending["offset"]), (older["head"], older["offset"]))
        self.assertEqual((pending["outcome"], older["outcome"]), ("PENDING", "EMPTY"))
        self.store.write(path, previous[0])
        self.clock.advance(2)
        return run, pending, older

    def test_r3_reproduces_completion_after_replacing_pending_with_empty(self):
        self.runner = older_r3.Runner(self.store, self.api, self.clock, self.clock.advance)
        run, _, _ = self.rollback_pending_to_previous_empty()
        resumed, row = self.reopen_r3(run)
        resumed.observe(row)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertEqual(row["observations"], [])

    def test_stale_empty_at_same_head_and_offset_cannot_settle_new_poll(self):
        run, pending, older = self.rollback_pending_to_previous_empty()
        self.assertEqual(pending["generation"], older["generation"] + 1)
        calls = list(self.api.calls)
        resumed, row = self.reopen(run)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "pinned generation or outcome"):
            resumed.observe(row)
        self.assertEqual(row["status"], "STOPPED")
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("capture_window_complete", row)
        self.assertEqual(self.api.calls, calls)

    def stop_just_after_intent(self, run, tester):
        open_intent = self.runner.open_poll_intent

        def post_stop(row, cursor):
            intent = open_intent(row, cursor)
            self.store.put(self.store.root / "observer-stop.json", {"synthetic_stop": True})
            return intent

        with patch.object(self.runner, "open_poll_intent", side_effect=post_stop):
            with self.assertRaisesRegex(tester.Refused, "Observer stopped"):
                self.runner.observe(run)

    def test_r3_reproduces_poll_after_stop_recorded_during_intent_write(self):
        self.runner = older_r3.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = self.start_reply()
        self.stop_just_after_intent(run, older_r3)
        self.assertEqual(self.api.calls.count("getUpdates"), 1)

    def test_stop_after_intent_is_settled_without_receive(self):
        run = self.start_reply()
        self.stop_just_after_intent(run, fixture.tester)
        row = self.runner.load(run["id"])
        intent = self.runner.read_poll_intent(row)
        self.assertEqual(row["status"], "STOPPED")
        self.assertEqual(row["stop_phase"], "poll_intent")
        self.assertEqual(intent["outcome"], "NOT_DISPATCHED")
        self.assertEqual(row["poll_intent_pin"]["generation"], intent["generation"])
        self.assertNotIn("receive_poll_outcome_unknown", row)
        self.assertNotIn("capture_window_complete", row)
        self.assertNotIn("getUpdates", self.api.calls)

    def test_successive_empty_polls_at_same_offset_have_distinct_generations(self):
        self.scenario["steps"][0]["observe"]["window_seconds"] = 5
        run = self.new()
        self.runner.send(run)
        settle = self.runner.settle_poll_intent
        retained = []

        def read_back_empty(row, intent, outcome):
            settle(row, intent, outcome)
            reopened = self.runner.load(row["id"])
            retained.append((self.runner.read_poll_intent(reopened), reopened["poll_intent_pin"]))

        with patch.object(self.runner, "settle_poll_intent", side_effect=read_back_empty):
            self.runner.observe(run)
        self.assertEqual([intent["generation"] for intent, _ in retained], [1, 2, 3])
        self.assertTrue(all(intent["offset"] == 0 and intent["outcome"] == "EMPTY" for intent, _ in retained))
        self.assertEqual(len({pin["sha256"] for _, pin in retained}), 3)
        self.assertEqual(run["status"], "EVIDENCE_READY")

    def test_restart_after_known_empty_still_uses_normal_terminal_read(self):
        run = self.new()
        self.runner.send(run)
        with patch.object(self.runner, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        resumed, row = self.reopen(run)
        self.assertEqual(resumed.read_poll_intent(row)["outcome"], "EMPTY")
        self.clock.advance(2)
        resumed.observe(row)
        self.assertEqual(self.api.reply_poll_count, 1)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertTrue(row["capture_window_complete"])

    def test_interruption_between_active_and_run_pin_stops_before_dispatch(self):
        run = self.start_reply()
        save = self.runner.save

        def interrupt_new_pin(row):
            if "poll_intent_pin" in row:
                raise KeyboardInterrupt
            return save(row)

        with patch.object(self.runner, "save", side_effect=interrupt_new_pin):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        calls = list(self.api.calls)
        resumed, row = self.reopen(run)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "no coherent run pin"):
            resumed.observe(row)
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("getUpdates", calls)
        self.assertEqual(self.api.calls, calls)

    def test_interrupted_settlement_between_active_and_run_pin_stops(self):
        run = self.start_reply()
        save = self.runner.save

        def interrupt_settlement_pin(row):
            if self.store.get(self.runner.poll_intent_path(row), {}).get("outcome") == "BATCH":
                raise KeyboardInterrupt
            return save(row)

        with patch.object(self.runner, "save", side_effect=interrupt_settlement_pin):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        witness = self.witness(run)
        calls = list(self.api.calls)
        resumed, row = self.reopen(run)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "pinned generation or outcome"):
            resumed.observe(row)
        self.assertTrue(witness.exists())
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertEqual(self.api.calls, calls)

    def test_cursor_drift_after_intent_settles_without_receive(self):
        run = self.start_reply()
        open_intent = self.runner.open_poll_intent

        def change_cursor(row, cursor):
            intent = open_intent(row, cursor)
            self.store.put(self.store.root / "cursor.json", dict(cursor, offset=1))
            return intent

        with patch.object(self.runner, "open_poll_intent", side_effect=change_cursor):
            with self.assertRaisesRegex(fixture.tester.Refused, "cursor changed before dispatch"):
                self.runner.observe(run)
        self.assertEqual(self.runner.read_poll_intent(run)["outcome"], "NOT_DISPATCHED")
        self.assertNotIn("getUpdates", self.api.calls)

    def test_original_monotonic_budget_subtracts_staging_even_if_new_guard_is_larger(self):
        run = self.start_reply()
        self.api.terminal = []
        guarded = []
        call_timeouts = []
        monotonic = fixture.Clock()
        open_intent = self.runner.open_poll_intent
        guard = self.runner.guard
        call = self.api.call

        def advance_staging(row, cursor):
            intent = open_intent(row, cursor)
            monotonic.advance(2)
            return intent

        def set_limits(row, *, http_cap=10):
            if http_cap == fixture.tester.RECEIVE_POLL_HTTP_CAP:
                guarded.append(monotonic())
                return 3 if len(guarded) == 1 else 9
            return guard(row, http_cap=http_cap)

        def inspect_timeout(method, params=None, *, timeout):
            if method == "getUpdates" and params["timeout"] == 1:
                call_timeouts.append(timeout)
            return call(method, params, timeout=timeout)

        self.api.call = inspect_timeout
        with (patch.object(fixture.tester.time, "monotonic", monotonic),
              patch.object(self.runner, "open_poll_intent", side_effect=advance_staging),
              patch.object(self.runner, "guard", side_effect=set_limits)):
            self.runner.observe(run)
        self.assertEqual(guarded, [1000, 1002])
        self.assertEqual(call_timeouts, [1])
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["deadline"], 1300)

    def test_linked_batch_cannot_settle_a_different_intent(self):
        run = self.prepare_batch()
        with patch.object(self.runner, "settle_poll_intent", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        intent = self.runner.read_poll_intent(run)
        self.store.put(self.runner.poll_intent_path(run), dict(intent, offset=1))
        resumed, row = self.reopen(run)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(fixture.tester.Uncertain, "pinned generation or outcome"):
            resumed.observe(row)
        self.assertEqual(self.api.calls, calls)
        self.assertEqual(row["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("capture_window_complete", row)


if __name__ == "__main__":
    fixture.tester = fixture.load_tester(sys.argv.pop(1))
    older_r3 = fixture.load_tester(sys.argv.pop(1))
    prior_checks.older_r2 = fixture.load_tester(sys.argv.pop(1))
    prior_checks.prior_checks.prior = fixture.load_tester(sys.argv.pop(1))
    unittest.main()
