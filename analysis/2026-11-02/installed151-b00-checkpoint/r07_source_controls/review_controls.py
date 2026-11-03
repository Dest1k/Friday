"""Own fake controls only; no product/renderer/authority imports or effects."""
import errno
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import r07_observed_stop as observed_module
from r07_observed_stop import ObservationRefused
from r07_observed_stop_controls import Harness, ObservedStopControls

ROOT = Path(__file__).resolve().parent


class LateStageHarness(Harness):
    """Same lifecycle as _create_bytes: enter observer, then create stage."""
    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)
        os.unlink(self.stage, dir_fd=self.fd)

    def worker(self):
        target = Path(self.root, self.stage)
        with target.open('xb') as stream:
            stream.write(b'%PDF-offline-observer-fake\n')
        target.chmod(0o600)
        super().worker()


class ReviewControls(unittest.TestCase):
    def make(self, harness_class=Harness, **kwargs):
        temporary = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(temporary.cleanup)
        harness = harness_class(temporary.name, **kwargs)
        self.addCleanup(harness.close)
        return harness

    def drive(self, harness):
        with harness.adapter:
            thread = threading.Thread(target=harness.worker)
            thread.start()
            try:
                observed = harness.adapter.wait_observed()
                receipt = harness.adapter.stop_and_resume()
            finally:
                thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertIsNone(harness.worker_error)
            report = harness.adapter.finalize()
        return observed, receipt, report

    def test_stage_created_after_enter_is_observable(self):
        harness = self.make(LateStageHarness)
        observed, receipt, report = self.drive(harness)
        self.assertTrue(observed['final_absent_before_stop'])
        self.assertEqual(harness.call.stop_calls, 1)
        self.assertEqual(harness.move_calls, 1)
        self.assertEqual(report['status'], 'ISOLATED_OBSERVATION_COMPLETE_NOT_CASE_PASS')
        self.assertEqual(report['unknown'], [])
        self.assertFalse(report['whole_case_credit'])

    def test_late_stage_actual_fake_publication_is_preserved_as_failure(self):
        harness = self.make(LateStageHarness, publish=True)
        _, _, report = self.drive(harness)
        self.assertEqual(harness.move_calls, 1)
        self.assertEqual(report['status'], 'FAIL_PUBLICATION_AFTER_OWNED_STOP')
        self.assertTrue(report['move']['final_after_move']['same_inode'])
        self.assertEqual(report['failures'], ['final_present_after_owned_stop'])

    def test_parent_permission_drift_still_refused(self):
        harness = self.make()
        with harness.adapter:
            os.chmod(harness.root, 0o750)
            thread = threading.Thread(target=harness.worker)
            thread.start()
            try:
                with self.assertRaisesRegex(ObservationRefused, '^parent_inode_mismatch$'):
                    harness.adapter.wait_observed()
                thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertEqual(harness.call.stop_calls, 0)
                self.assertEqual(harness.move_calls, 0)
                self.assertIsInstance(harness.worker_error, ObservationRefused)
            finally:
                os.chmod(harness.root, 0o700)
                thread.join(3)

    def test_post_move_stat_error_remains_unknown_after_later_absence(self):
        harness = self.make()
        original_record = harness.adapter._record_final_after_move
        def unreadable_once(fd, leaf):
            with patch.object(observed_module.os, 'stat', side_effect=PermissionError(errno.EACCES, 'offline-fake-denied')):
                original_record(fd, leaf)
        harness.adapter._record_final_after_move = unreadable_once
        _, _, report = self.drive(harness)
        self.assertEqual(report['move']['final_after_move'], {'present': None, 'error': 'PermissionError'})
        self.assertFalse(report['cleanup']['final_present'])
        self.assertEqual(report['status'], 'UNKNOWN_STOP_OR_CLEANUP')
        self.assertIn('post_move_final_presence_unobserved', report['unknown'])
