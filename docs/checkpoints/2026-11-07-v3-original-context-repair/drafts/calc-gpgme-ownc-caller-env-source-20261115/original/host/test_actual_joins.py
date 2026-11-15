"""Actual generated metadata joins; no target, debugger, unit or namespace run."""
from pathlib import Path
import copy
import importlib.util
import json
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ownc_root_source_join_consumer', BASE / 'host/ownc_root_controller.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class ActualMetadataJoins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((BASE / 'inputs/worker_cached/STATIC-PLAN.json').read_bytes())
        cls.prepared = host.json_load(host.read_ref(cls.plan['prepared_ref']))
        cls.namespace = host.load_module(cls.plan['source_refs']['namespace'], 'ownc_reviewed_namespace_join_test')

    def build(self, prepared):
        return host.build_bundles(self.plan, prepared, self.namespace,
            operation_id='source-test-unbound', nonce='0' * 32, deadline=1.0, validation_only=True)

    def test_actual_four_source_plans(self):
        for variant in ('worker_cached', 'extra_fork', 'forbidden_gpg_home', 'wrong_gpgconf_name'):
            with self.subTest(variant=variant):
                plan = json.loads((BASE / 'inputs' / variant / 'STATIC-PLAN.json').read_bytes())
                host.inspect_plan(plan)

    def test_full_environment_omission_refused(self):
        plan = copy.deepcopy(self.plan)
        del plan['target_environment']['LANG']
        with self.assertRaisesRegex(RuntimeError, '^ownc_complete_collector_startup_env_join$'):
            host.inspect_plan(plan)

    def test_stale_office_paper_pin_refused_by_actual_fixture_validator(self):
        prepared = copy.deepcopy(self.prepared)
        prepared['gpgme_runtime_template']['paper_manifest_ref']['sha256'] = (
            '92b94f4100609c820f25891e09ec15267802833fb4665c393ff746c4565691d0')
        with self.assertRaisesRegex(ValueError, '^gpgme_exact_paper_window_and_outputs$'):
            self.build(prepared)

    def test_different_paper_gpgme_source_refused(self):
        prepared = copy.deepcopy(self.prepared)
        prepared['gpgme_runtime_template']['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '^gpgme_same_paper_load_window$'):
            self.build(prepared)

    def test_prebound_operation_clock_refused(self):
        prepared = copy.deepcopy(self.prepared)
        prepared['runtime_template']['operation_deadline_monotonic'] = 2.0
        with self.assertRaisesRegex(RuntimeError, '^ownc_template_clock_bound$'):
            self.build(prepared)


if __name__ == '__main__':
    unittest.main()
