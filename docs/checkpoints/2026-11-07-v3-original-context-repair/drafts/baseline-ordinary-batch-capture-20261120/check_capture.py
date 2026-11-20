#!/usr/bin/env python3
"""Exercise an ordinary tester with an in-memory transport and a private temporary Store."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_tester(path):
    spec = importlib.util.spec_from_file_location("friday_tester_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Clock:
    now = 1000

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class API:
    input_bytes = b"source row,10\n"
    result_bytes = b"result row,20\n"

    def __init__(self, tester, clock):
        self.tester = tester
        self.clock = clock
        self.calls = []
        self.batch = []
        self.terminal = []
        self.reply_poll_count = 0
        self.download_seconds = 0
        self.fail_ack = False
        self.fail_first_poll = False
        self.fail_terminal = False

    def ack(self):
        return {
            "message_id": 200,
            "date": int(self.clock()),
            "from": {"id": self.tester.TESTER, "is_bot": True},
            "chat": {"id": self.tester.PEER, "type": "private"},
        }

    def send_document(self, body, content_type, *, timeout):
        self.calls.append("sendDocument")
        assert self.input_bytes in body and content_type.startswith("multipart/form-data;")
        if self.fail_ack:
            raise self.tester.Uncertain("synthetic lost ACK")
        return dict(self.ack(), caption="Process the example.", document={
            "file_id": "input_file", "file_unique_id": "input_unique", "file_size": len(self.input_bytes),
        })

    def call(self, method, params=None, *, timeout):
        self.calls.append(method)
        assert timeout > 0
        result = self.result(method, params)
        self._last_response = self.tester.encoded({"ok": True, "result": result})
        return result

    def result(self, method, params):
        if method == "getMe":
            return {"id": self.tester.TESTER, "is_bot": True}
        if method == "getWebhookInfo":
            return {"url": ""}
        if method == "getChat":
            return {"id": self.tester.PEER, "type": "private"}
        if method == "getFile":
            assert params == {"file_id": "output_file"}
            return {
                "file_id": "output_file", "file_unique_id": "output_unique",
                "file_path": "documents/synthetic.csv", "file_size": len(self.result_bytes),
            }
        if method == "getUpdates":
            if params["timeout"] == 0:
                if self.fail_terminal:
                    raise self.tester.Uncertain("synthetic lost terminal response")
                return self.terminal
            self.reply_poll_count += 1
            if self.fail_first_poll:
                if self.reply_poll_count == 1:
                    self.clock.advance(1)
                    raise self.tester.Uncertain("synthetic lost poll response")
                if self.reply_poll_count == 2:
                    self.clock.advance(1)
                    return self.batch
            if self.reply_poll_count == 1:
                self.clock.advance(2)
                return self.batch
            return []
        raise AssertionError("Unexpected synthetic API call: " + method)

    def download(self, path, max_bytes, *, timeout):
        self.calls.append("download")
        assert path == "documents/synthetic.csv" and len(self.result_bytes) <= max_bytes
        assert timeout > 0
        self.clock.advance(self.download_seconds)
        return self.result_bytes

    def update(self, uid, **payload):
        return {"update_id": uid, "message": {
            "message_id": uid + 200, "date": 1001,
            "from": {"id": self.tester.PEER, "is_bot": True},
            "chat": {"id": self.tester.PEER, "type": "private"},
            "reply_to_message": {"message_id": 200},
            **payload,
        }}

    def document(self, uid):
        return self.update(uid, caption="Completed example.", document={
            "file_id": "output_file", "file_unique_id": "output_unique",
            "file_size": len(self.result_bytes), "file_name": "result.csv", "mime_type": "text/csv",
        })


class OrdinaryCapture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="frw-observation-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.clock = Clock()
        self.api = API(tester, self.clock)
        self.store = tester.Store(root / "store")
        self.runner = tester.Runner(self.store, self.api, self.clock, self.clock.advance)
        source = root / "example.csv"
        source.write_bytes(self.api.input_bytes)
        source.chmod(0o600)
        self.scenario = {
            "peer_id": tester.PEER, "tester_id": tester.TESTER, "peer_username": tester.USERNAME,
            "deadline_seconds": 300, "max_updates": 12, "pace_seconds": 1, "steps": [{
                "input": {
                    "kind": "document", "path": str(source), "sha256": tester.digest(source.read_bytes()),
                    "stat": tester.input_stat(source.stat()), "filename": "example.csv",
                    "mime_type": "text/csv", "caption": "Process the example.",
                },
                "observe": {
                    "mode": "bounded_reply_capture", "window_seconds": 3, "max_messages": 6,
                    "max_documents": 1, "max_text_chars": 400, "document_max_bytes": 1024,
                },
            }],
        }

    def new(self):
        return self.runner.new("synthetic-observation", self.scenario)

    def test_slow_download_preserves_sibling_timing_and_terminal_filters_late(self):
        self.api.batch = [self.api.document(101), self.api.update(102, text="The row is done.")]
        self.api.terminal = [self.api.document(103)]
        self.api.download_seconds = 2
        run = self.new()
        self.runner.send(run)
        self.runner.observe(run)
        run = self.runner.load(run["id"])
        self.runner.verify_reply_custody(run)
        captures, processed, terminal = self.runner.receive_inventory(run, terminal=True)
        self.assertEqual([captures[uid]["arrived_at"] for uid in (101, 102, 103)], [1002, 1002, 1004])
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["deadline"], 1300)
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertTrue(run["capture_window_complete"])
        self.assertEqual(run["reply_outcome"], "RECEIVED_UNGRADED")
        self.assertEqual(run["acceptance"], "NOT_ESTABLISHED")
        self.assertEqual([o["kind"] for o in run["observations"]], ["document", "reply_text"])
        artifact, reply = run["observations"]
        self.assertEqual(artifact["caption"], "Completed example.")
        self.assertEqual(artifact["sha256"], tester.digest(self.api.result_bytes))
        self.assertEqual(tester.safe_read(Path(artifact["path"])), self.api.result_bytes)
        self.assertEqual(reply["text"], "The row is done.")
        self.assertEqual(processed[103]["observations"], [])
        self.assertIn("complete", terminal)
        self.assertEqual(self.api.calls.count("sendDocument"), 1)
        self.assertEqual(self.api.calls.count("download"), 1)

    def test_verifier_refusal_preserves_returned_sibling_before_processing(self):
        self.scenario["steps"][0]["observe"]["max_documents"] = 0
        self.api.batch = [self.api.document(101), self.api.update(102, text="The row is done.")]
        run = self.new()
        self.runner.send(run)
        with self.assertRaisesRegex(tester.Refused, "Unexpected extra attachment"):
            self.runner.observe(run)
        run = self.runner.load(run["id"])
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(run["stop_phase"], "process_update")
        self.assertNotIn("capture_window_complete", run)
        self.assertEqual(run["observations"], [])
        sibling_path = self.store.captures / "102.json"
        self.assertTrue(sibling_path.is_file(), "A returned batch sibling was lost on the verifier refusal")
        self.assertEqual(self.store.get(sibling_path), self.api.batch[1])
        marker = self.runner.read_reference(run["receive_head"])
        self.assertEqual(marker["kind"], "processing")
        self.assertEqual(self.runner.read_reference(marker["previous"])["update_id"], 102)
        calls = list(self.api.calls)
        with self.assertRaisesRegex(tester.Refused, "Processing outcome uncertain"):
            self.runner.observe(run)
        self.assertEqual(self.api.calls, calls)
        self.assertNotIn("download", self.api.calls)

    def test_lost_terminal_receive_stays_partial_without_retry(self):
        self.api.batch = [self.api.update(101, text="The row is done.")]
        self.api.fail_terminal = True
        run = self.new()
        self.runner.send(run)
        with self.assertRaises(tester.Uncertain):
            self.runner.observe(run)
        run = self.runner.load(run["id"])
        self.runner.verify_reply_custody(run)
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(run["stop_phase"], "terminal_drain")
        self.assertEqual(run["stop_reason_code"], "TRANSPORT_OUTCOME_UNKNOWN")
        self.assertNotIn("capture_window_complete", run)
        self.assertEqual(run["observations"][0]["text"], "The row is done.")
        _, _, terminal = self.runner.receive_inventory(run, terminal=True)
        self.assertEqual(set(terminal), {"intent"})
        calls = list(self.api.calls)
        with self.assertRaisesRegex(tester.Refused, "Terminal drain already consumed"):
            self.runner.terminal_drain(run)
        self.assertEqual(self.api.calls, calls)

    def test_same_offset_retry_samples_arrival_before_local_journal_save(self):
        self.api.batch = [self.api.update(101, text="The row is done.")]
        self.api.fail_first_poll = True
        run = self.new()
        self.runner.send(run)
        save = self.runner.save

        def slow_retry_save(row):
            save(row)
            state = row.get("receive_http_retry", {})
            if state.get("outcome") == "RETURNED_UNVALIDATED" and self.clock() == 1002:
                self.clock.advance(2)

        with patch.object(self.runner, "save", side_effect=slow_retry_save):
            self.runner.observe(run)
        self.assertEqual(self.api.reply_poll_count, 2)
        self.assertEqual(run["receive_http_retry"]["offset"], 0)
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual([o["text"] for o in run["observations"]], ["The row is done."])
        self.assertEqual(self.runner.receive_inventory(run)[0][101]["arrived_at"], 1002)

    def test_restart_processes_committed_batch_against_original_arrival(self):
        self.api.batch = [self.api.document(101), self.api.update(102, text="The row is done.")]
        run = self.new()
        self.runner.send(run)
        with patch.object(self.runner, "process", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.observe(run)
        self.clock.advance(2)
        resumed = tester.Runner(self.store, self.api, self.clock, self.clock.advance)
        run = resumed.load(run["id"])
        resumed.observe(run)
        resumed.verify_reply_custody(resumed.load(run["id"]))
        self.assertEqual(run["capture_until"], 1003)
        self.assertEqual(run["deadline"], 1300)
        self.assertEqual(run["status"], "EVIDENCE_READY")
        self.assertEqual([o["kind"] for o in run["observations"]], ["document", "reply_text"])
        self.assertEqual(self.api.calls.count("sendDocument"), 1)
        self.assertEqual(self.api.calls.count("download"), 1)

    def test_overlarge_batch_is_refused_before_staging(self):
        self.scenario["max_updates"] = 2
        self.scenario["steps"][0]["observe"]["max_messages"] = 2
        self.api.batch = [self.api.update(uid, text="Another reply.") for uid in range(101, 105)]
        run = self.new()
        self.runner.send(run)
        with self.assertRaisesRegex(tester.Refused, "Invalid update batch"):
            self.runner.observe(run)
        run = self.runner.load(run["id"])
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(run["stop_phase"], "poll_batch")
        self.assertEqual(list(self.store.captures.iterdir()), [])

    def test_lost_send_ack_blocks_replay_and_new_work(self):
        self.api.fail_ack = True
        run = self.new()
        with self.assertRaisesRegex(tester.Refused, "Send outcome unknown"):
            self.runner.send(run)
        run = self.runner.load(run["id"])
        self.assertEqual(run["status"], "UNKNOWN_SEND")
        self.assertEqual(run["send_state"], "unknown")
        calls = list(self.api.calls)
        with self.assertRaisesRegex(tester.Refused, "never be reissued"):
            self.runner.send(run)
        with self.assertRaisesRegex(tester.Refused, "Unfinished prior run"):
            self.runner.new("new-synthetic-work", self.scenario)
        with self.assertRaisesRegex(tester.Refused, "confirmed send"):
            self.runner.observe(run)
        self.assertEqual(self.api.calls, calls)
        self.assertEqual(self.api.calls.count("sendDocument"), 1)


if __name__ == "__main__":
    tester = load_tester(sys.argv.pop(1))
    unittest.main()
