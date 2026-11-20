#!/usr/bin/env python3
"""Inject interruptions into the ordinary batch's real Store and receive chain."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def load_fixture(path):
    spec = importlib.util.spec_from_file_location("friday_ordinary_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load_fixture(Path(__file__).resolve().parents[1] / "check_capture.py")


class PollWitness(fixture.OrdinaryCapture):
    def prepare_batch(self):
        # Wire order differs from the durable ascending update order.
        self.api.batch = [self.api.update(102, text="The row is done."), self.api.document(101)]
        call = self.api.call

        def keep_wire_layout(method, params=None, *, timeout):
            result = call(method, params, timeout=timeout)
            if method == "getUpdates" and result:
                self.api._last_response = b"  " + self.api._last_response + b"\n"
            return result

        self.api.call = keep_wire_layout
        run = self.new()
        self.runner.send(run)
        return run

    def witness(self, run):
        paths = list(self.store.root.glob("poll-response-*.wire"))
        self.assertEqual(len(paths), 1)
        data = fixture.tester.safe_read(paths[0])
        header, raw = data.split(b"\n", 1)
        commitment = json.loads(header)
        self.assertEqual(commitment["arrived_at"], 1002)
        self.assertEqual(commitment["offset"], 0)
        self.assertEqual(commitment["sequence"], 1)
        self.assertEqual(commitment["context_sha256"],
                         fixture.tester.digest(fixture.tester.encoded(self.runner.receive_context(run))))
        self.assertEqual(raw, self.api._last_response)
        self.assertEqual(json.loads(raw)["result"], self.api.batch)
        return paths[0]

    def reopen(self, run):
        resumed = fixture.tester.Runner(self.store, self.api, self.clock, self.clock.advance)
        return resumed, resumed.load(run["id"])

    def assert_recovered(self, run, remaining):
        self.clock.advance(2)
        resumed, row = self.reopen(run)
        pending, arrival = resumed.receive_inventory(row, pending_batch=True)
        self.assertEqual([update["update_id"] for update in pending], remaining)
        self.assertEqual(arrival, 1002)
        resumed.observe(row)
        resumed.verify_reply_custody(resumed.load(row["id"]))
        captured, _, terminal = resumed.receive_inventory(row, terminal=True)
        self.assertEqual([captured[uid]["arrived_at"] for uid in (101, 102)], [1002, 1002])
        self.assertEqual(row["capture_until"], 1003)
        self.assertEqual(row["deadline"], 1300)
        self.assertEqual(row["status"], "EVIDENCE_READY")
        self.assertIn("complete", terminal)
        self.assertEqual([item["kind"] for item in row["observations"]], ["document", "reply_text"])
        self.assertEqual(self.api.calls.count("sendDocument"), 1)
        self.assertEqual(self.api.calls.count("download"), 1)
        return row

    def assert_unrecoverable(self, run, reason):
        witness = self.witness(run)
        raw = witness.read_bytes()
        resumed, row = self.reopen(run)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(fixture.tester.Refused, reason):
            resumed.observe(row)
        self.assertEqual(self.api.calls, calls)
        self.assertEqual(witness.read_bytes(), raw)
        self.assertNotIn("capture_window_complete", row)
        self.assertEqual(row["observations"], [])

    def test_hard_loss_before_witness_write_has_no_arrival_evidence(self):
        run = self.prepare_batch()
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
        self.assertEqual(list(self.store.captures.iterdir()), [])
        resumed, row = self.reopen(run)
        self.assertEqual(resumed.receive_inventory(row, pending_batch=True), ([], None))
        self.assertNotIn("capture_window_complete", row)
        self.assertEqual(self.api.calls.count("sendDocument"), 1)

    def test_exact_clock_and_wire_remain_after_witness_before_chain(self):
        run = self.prepare_batch()
        commit = self.runner.commit_receive

        def stop_before_receipt(row, record):
            if record["kind"] == "poll_batch":
                raise KeyboardInterrupt
            return commit(row, record)

        with patch.object(self.runner, "commit_receive", side_effect=stop_before_receipt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assert_unrecoverable(run, "Unpaired ordinary poll response")

    def test_receipt_before_dual_head_commit_refuses_with_exact_witness(self):
        run = self.prepare_batch()
        original_write = self.store.write
        name = "receive-" + self.runner.receive_key(run) + "-1.json"

        def stop_after_receipt_file(path, data):
            original_write(path, data)
            if path.name == name:
                raise KeyboardInterrupt

        with patch.object(self.store, "write", side_effect=stop_after_receipt_file):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assertEqual(self.store.get(self.store.root / name)["kind"], "poll_batch")
        self.assert_unrecoverable(run, "Unpaired capture/process witness")

    def test_committed_witness_recovers_before_first_capture(self):
        run = self.prepare_batch()
        with patch.object(self.runner, "capture", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.witness(run)
        self.assert_recovered(run, [101, 102])
        self.assertEqual(self.api.reply_poll_count, 1)

    def test_committed_prefix_recovers_exact_suffix_without_repoll(self):
        run = self.prepare_batch()
        capture = self.runner.capture

        def stop_after_first_capture(update, **kwargs):
            capture(update, **kwargs)
            raise KeyboardInterrupt

        with patch.object(self.runner, "capture", side_effect=stop_after_first_capture):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.witness(run)
        self.assertEqual(sorted(p.name for p in self.store.captures.iterdir()), ["101.arrival.json", "101.json"])
        self.assert_recovered(run, [102])
        self.assertEqual(self.api.reply_poll_count, 1)

    def test_interrupted_second_capture_retains_full_witness_and_refuses(self):
        run = self.prepare_batch()
        original_write = self.store.write

        def stop_after_second_raw(path, data):
            original_write(path, data)
            if path == self.store.captures / "102.json":
                raise KeyboardInterrupt

        with patch.object(self.store, "write", side_effect=stop_after_second_raw):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assertFalse((self.store.captures / "102.arrival.json").exists())
        self.assert_unrecoverable(run, "Raw/arrival pairs differ")

    def test_split_second_capture_head_refuses_with_exact_witness(self):
        run = self.prepare_batch()
        original_write = self.store.write

        def stop_after_second_run_head(path, data):
            original_write(path, data)
            if path == self.store.run_path(run["id"]) and json.loads(data).get("receive_sequence") == 3:
                raise KeyboardInterrupt

        with patch.object(self.store, "write", side_effect=stop_after_second_run_head):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.assert_unrecoverable(run, "independent cursor/run capture commitment")

    def test_retry_return_marker_follows_durable_witness(self):
        run = self.prepare_batch()
        self.api.fail_first_poll = True
        save = self.runner.save

        def stop_before_retry_return_marker(row):
            if row.get("receive_http_retry", {}).get("outcome") == "RETURNED_UNVALIDATED":
                raise KeyboardInterrupt
            return save(row)

        with patch.object(self.runner, "save", side_effect=stop_before_retry_return_marker):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        witness = self.witness(run)
        self.assertEqual(self.store.get(self.store.run_path(run["id"]))["receive_http_retry"]["outcome"], "RESERVED")
        self.assert_recovered(run, [101, 102])
        self.assertTrue(witness.exists())
        self.assertEqual(self.api.reply_poll_count, 2)

    def test_altered_linked_witness_cannot_supply_resume(self):
        run = self.prepare_batch()
        with patch.object(self.runner, "capture", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        witness = self.witness(run)
        self.store.write(witness, witness.read_bytes() + b" ")
        resumed, row = self.reopen(run)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(fixture.tester.Refused, "witness differs from its committed bytes"):
            resumed.observe(row)
        self.assertEqual(self.api.calls, calls)

    def test_resumed_receive_after_rate_limit_stages_witness(self):
        run = self.prepare_batch()
        run["status"] = "RATE_LIMITED_RECEIVE"
        self.runner.save(run)
        self.runner.observe(run)
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual([item["kind"] for item in run["observations"]], ["document", "reply_text"])
        self.assertEqual(self.api.calls.count("sendDocument"), 1)

    def test_multiple_batches_keep_exact_committed_witnesses(self):
        self.scenario["steps"][0]["observe"]["window_seconds"] = 5
        run = self.prepare_batch()
        result = self.api.result

        def receive_twice(method, params):
            if method == "getUpdates" and params["timeout"] == 1 and params["offset"] == 103:
                self.api.reply_poll_count += 1
                return [self.api.update(103, text="A separate later reply.")]
            return result(method, params)

        self.api.result = receive_twice
        self.runner.observe(run)
        self.runner.verify_reply_custody(self.runner.load(run["id"]))
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual(len(list(self.store.root.glob("poll-response-*.wire"))), 2)
        captures, _ = self.runner.receive_inventory(run)
        self.assertEqual([captures[uid]["arrived_at"] for uid in (101, 102, 103)], [1002, 1002, 1003])

    def test_r1_receipts_validate_without_rewriting(self):
        self.api.batch = [self.api.document(101), self.api.update(102, text="The row is done.")]
        older = prior.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = older.new("synthetic-r1-history", self.scenario)
        older.send(run)
        older.observe(run)
        before = {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()}
        resumed, row = self.reopen(run)
        resumed.verify_reply_custody(row)
        self.assertIn("complete", resumed.receive_inventory(row, terminal=True)[2])
        self.assertEqual(before, {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()})


if __name__ == "__main__":
    fixture.tester = fixture.load_tester(sys.argv.pop(1))
    prior = fixture.load_tester(sys.argv.pop(1))
    unittest.main()
