import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from r07_observed_stop import ObservedStopAdapter, ObservationRefused


ROOT = Path(__file__).resolve().parent


class FakeCall:
    def __init__(self, receipt_status="QUIESCENT", task_id="task-R07"):
        self.user_authority = {"principal": "offline-fake"}
        self.task_id = task_id
        self.call_id = "call-R07"
        self.session_id = "session-R07"
        self.session = None
        self.registry = None
        self.stopped = threading.Event()
        self.turn = SimpleNamespace(calls=set())
        self.turn.calls.add(self)
        self.receipt_status = receipt_status
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1
        self.stopped.set()
        if self.receipt_status == "QUIESCENT":
            self.turn.calls.discard(self)
        return {"status": self.receipt_status}


class Harness:
    def __init__(self, root, *, publish=False, receipt_status="QUIESCENT",
                 foreign_task=False, final_preexists=False, custody_active=False):
        self.root = root
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.stage = ".friday-docx-" + "a" * 32
        self.leaf = "derivative.pdf"
        with open(os.path.join(root, self.stage), "xb") as stream:
            stream.write(b"%PDF-offline-observer-fake\n")
        os.chmod(os.path.join(root, self.stage), 0o600)
        if final_preexists:
            Path(root, self.leaf).write_bytes(b"preexisting")
        self.call = FakeCall(receipt_status, "foreign" if foreign_task else "task-R07")
        if custody_active:
            self.call.session = object()
            self.call.registry = object()
        self.move_calls = 0
        self.worker_error = None

        def original_move(source_fd, stage, destination_fd, leaf):
            self.move_calls += 1
            if publish:
                os.rename(stage, leaf, src_dir_fd=source_fd, dst_dir_fd=destination_fd)

        self.docx = SimpleNamespace(_move=original_move)
        self.context = SimpleNamespace(
            _current=SimpleNamespace(get=lambda: self.call),
            same_web_authority=lambda call: call is self.call,
        )
        self.adapter = ObservedStopAdapter(
            docx_module=self.docx,
            web_context=self.context,
            check_cap=lambda cap: None,
            cap=object(),
            call=self.call,
            parent_fd=self.fd,
            final_path=self.leaf,
            final_leaf=self.leaf,
            expected_principal=self.call.user_authority,
            expected_task_id="task-R07",
            expected_call_id="call-R07",
            expected_session_id="session-R07",
            hold_seconds=2,
        )

    def close(self):
        os.close(self.fd)

    def worker(self):
        try:
            self.docx._move(self.fd, self.stage, self.fd, self.leaf)
            if os.path.exists(os.path.join(self.root, self.stage)):
                os.unlink(self.stage, dir_fd=self.fd)
        except Exception as error:
            self.worker_error = error


class ObservedStopControls(unittest.TestCase):
    def make(self, **kwargs):
        temporary = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(temporary.cleanup)
        harness = Harness(temporary.name, **kwargs)
        self.addCleanup(harness.close)
        return harness

    def drive(self, harness):
        with harness.adapter:
            thread = threading.Thread(target=harness.worker)
            thread.start()
            observed = harness.adapter.wait_observed()
            receipt = harness.adapter.stop_and_resume()
            thread.join(3)
            self.assertFalse(thread.is_alive())
            if harness.worker_error is not None:
                raise harness.worker_error
            report = harness.adapter.finalize()
        return observed, receipt, report

    def test_held_stage_stop_resume_and_cleanup(self):
        harness = self.make()
        observed, receipt, report = self.drive(harness)
        self.assertEqual(observed["stage_sha256"], __import__("hashlib").sha256(b"%PDF-offline-observer-fake\n").hexdigest())
        self.assertTrue(observed["final_absent_before_stop"])
        self.assertEqual(receipt["status"], "QUIESCENT")
        self.assertEqual(harness.call.stop_calls, 1)
        self.assertEqual(harness.move_calls, 1)
        self.assertEqual(report["status"], "ISOLATED_OBSERVATION_COMPLETE_NOT_CASE_PASS")
        self.assertFalse(report["whole_case_credit"])

    def test_publication_after_accepted_stop_is_failure(self):
        harness = self.make(publish=True)
        _, receipt, report = self.drive(harness)
        self.assertEqual(receipt["status"], "QUIESCENT")
        self.assertEqual(report["status"], "FAIL_PUBLICATION_AFTER_OWNED_STOP")
        self.assertIn("final_present_after_owned_stop", report["failures"])
        self.assertTrue(report["move"]["final_after_move"]["same_inode"])

    def test_unconfirmed_stop_is_not_retried_or_hidden(self):
        harness = self.make(receipt_status="STOP_UNCONFIRMED")
        _, receipt, report = self.drive(harness)
        self.assertEqual(receipt["status"], "STOP_UNCONFIRMED")
        self.assertEqual(harness.call.stop_calls, 1)
        self.assertEqual(report["status"], "UNKNOWN_STOP_OR_CLEANUP")
        self.assertIn("owned_stop_not_confirmed", report["unknown"])

    def assert_refused_before_effects(self, harness, reason):
        with harness.adapter:
            thread = threading.Thread(target=harness.worker)
            thread.start()
            with self.assertRaises(ObservationRefused) as caught:
                harness.adapter.wait_observed()
            thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(str(caught.exception), reason)
            self.assertIsInstance(harness.worker_error, ObservationRefused)
            self.assertEqual(harness.call.stop_calls, 0)
            self.assertEqual(harness.move_calls, 0)

    def test_foreign_task_refused_before_stop_or_move(self):
        self.assert_refused_before_effects(self.make(foreign_task=True), "task_call_session_mismatch")

    def test_existing_final_refused_before_stop_or_move(self):
        self.assert_refused_before_effects(self.make(final_preexists=True), "final_already_present")

    def test_renderer_custody_must_be_settled_at_stage(self):
        self.assert_refused_before_effects(self.make(custody_active=True), "renderer_custody_still_bound")

    def test_pre_stopped_call_cannot_manufacture_observed_stop(self):
        harness = self.make()
        harness.call.stopped.set()
        self.assert_refused_before_effects(harness, "call_already_stopped")


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    outcome = {
        "schema": "frw.b00.r07.offline-observer-controls.v1",
        "execution": "OFFLINE_OWN_FAKES_ONLY_NO_PRODUCT_IMPORT_OR_RENDERER",
        "tests_run": result.result.testsRun,
        "failures": len(result.result.failures),
        "errors": len(result.result.errors),
        "passed": result.result.wasSuccessful(),
    }
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["passed"] else 1)
