#!/usr/bin/env python3
"""Exercise the genuine R4 prepare consumer on a disjoint synthetic store."""

import datetime as dt
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import ModuleType
import unittest


composer = runpy.run_path(str(Path(__file__).with_name("ordinary_admission_source.py")))
RUN_ID = "baseline-d10-local-control"
SOURCE = b""
SCENARIO = None


def load_observer(raw, name="private_observer_control"):
    module = ModuleType(name)
    module.__file__ = "<selected R4 observation source>"
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    return module


class OrdinaryAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_observer(SOURCE)
        cls.scenario = cls.base.validate_scenario(SCENARIO)
        cls.scenario_sha = cls.base.digest(cls.base.encoded(cls.scenario))

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="frw-ordinary-admission-stand-")
        self.addCleanup(sandbox.cleanup)
        self.work = Path(sandbox.name)
        self.store = self.base.Store(self.work / "state")
        self.now = dt.datetime.now(dt.timezone.utc)
        self.history = self.store.run_path("historical-unknown")
        old = dict(id="historical-unknown", status="UNKNOWN_SEND", send_state="unknown",
                   scenario={"steps": []}, deadline=self.now.timestamp() - 600)
        self.store.put(self.history, old)
        old_sha = self.base.digest(self.history.read_bytes())
        self.gateway_ref = self.work / "gateway.json"
        pid = os.getpid()
        start_time = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])
        self.gateway = dict(pid=pid, start_time=start_time, gateway_state="running",
                            active_agents=0, active_work=None, restart_requested=False,
                            session_store={"status": "ok"}, updated_at=self.now.isoformat(),
                            platforms={"telegram": {"state": "connected", "needs_attention": False,
                                                    "writer_pid": pid, "writer_start_time": start_time}})
        self.store.put(self.gateway_ref, self.gateway)
        self.authority = dict(
            schema=composer["AUTHORITY_SCHEMA"], authority_id="synthetic-control-only",
            operator="Root", accepted=True, run_scenarios={RUN_ID: self.scenario_sha},
            created_at=self.now.timestamp() - 1, expires_at=self.now.timestamp() + 180,
            boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            gateway=dict(state_path=str(self.gateway_ref), pid=pid, start_time=start_time,
                         maximum_staleness_seconds=180),
            new_independent_inputs_only=True, no_old_task_replay=True, old_rows_modified=False,
            unknown_effects_resolved=False, product_or_B00_acceptance=False,
            new_trial_for_historical_task=False,
            history={old["id"]: dict(sha256=old_sha, status=old["status"], send_state=old["send_state"],
                                     deadline=old["deadline"], new_effect_replay_authorized=False,
                                     unknown_retained=True)})
        self.checker = self.reference("checker.py", b"""from pathlib import Path
import hashlib

def check(proof_ref, *, contract_ref, prepare_ref, run_id, scenario, stage):
    for reference in (proof_ref, contract_ref, prepare_ref):
        raw = Path(reference['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference['sha256']:
            return False
    allowed = stage == 'NEW' or (stage == 'CURSOR_AUTHORITY'
                                and Path(proof_ref['path']).read_bytes() == b'synthetic cursor proof\\n')
    return run_id == 'baseline-d10-local-control' and bool(scenario['steps']) and allowed
""")
        self.proof = self.reference("proof.json", b"synthetic current proof\n")
        self.contract = self.reference("contract.json", b"synthetic exact owner decision\n")
        self.prepare = self.reference("prepare.json", b"synthetic exact scenario preparation\n")

    def reference(self, name, raw):
        path = self.work / name
        self.store.write(path, raw)
        return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def compose(self, **overrides):
        self.authority_ref = self.reference("authority.json", self.base.encoded(self.authority))
        inputs = dict(run_id=RUN_ID, scenario_sha256=self.scenario_sha, authority=self.authority,
                      authority_ref=self.authority_ref, checker_ref=self.checker, proof_ref=self.proof,
                      contract_ref=self.contract, prepare_ref=self.prepare)
        inputs.update(overrides)
        return composer["compose_observer"](SOURCE, **inputs)

    def candidate(self):
        module = load_observer(self.compose())
        return module, module.Runner(self.store, None, clock=lambda: self.now.timestamp())

    def assert_unprepared(self):
        self.assertFalse(self.store.run_path(RUN_ID).exists())
        self.assertFalse((self.store.root / "cursor.json").exists())

    def owned_caller(self, scenario):
        drafts = Path(__file__).resolve().parents[2]
        checker_path = ("f07-ordinary-current209-source-20261113/config-bound-delta/source/current209.py")
        actor_path = "ordinary-disk-monitor-next-source-20261116/root_f07_once.py"
        actor_raw = (drafts / actor_path).read_bytes()
        checker_raw = (drafts / checker_path).read_bytes()
        self.assertEqual(hashlib.sha256(actor_raw).hexdigest(),
                         "729efbd54ae5d12b61c0375964fdee817457c57544b08f79ca507215070ea5f5")
        self.assertEqual(hashlib.sha256(checker_raw).hexdigest(),
                         "24215d1fca8d59e4109e5934464cf4cfbcf6d2dd48d33b7d44c3fc54377de47f")
        actor = load_observer(actor_raw, "original_owned_f07_actor")
        checker = load_observer(checker_raw, "original_f07_lock_checker")
        actor.STATE = self.store.root
        actor.SLOT = Path(self.reference("acceptance.lock", b"")["path"])
        sink = self.store.root / "consumer.lock"
        credentials = self.store.root / "tester-token"
        self.store.write(sink, b"")
        self.store.write(credentials, b"inert lock-test bytes\n")
        scenario_sha = self.base.digest(self.base.encoded(scenario))
        self.authority["run_scenarios"] = {RUN_ID: scenario_sha}
        ordinary = self.compose(scenario_sha256=scenario_sha)
        caller = load_observer(ordinary)
        source = self.reference("bound-observer.py", ordinary)
        phase = {"scenario": scenario, "scenario_sha256": scenario_sha}
        descriptor = {"run_id": RUN_ID, "selected_tester": source}
        stack = self.enterContext(ExitStack())
        slot = actor.safe_lock(actor.SLOT)
        stack.callback(os.close, slot)
        return caller, sink, credentials, lambda: actor.qualify_before_clock(
            descriptor, caller, checker, ordinary, phase)

    def test_genuine_prepare_uses_exact_authority(self):
        _, runner = self.candidate()
        retained = self.history.read_bytes()
        run = runner.new(RUN_ID, self.scenario)
        self.assertEqual(run["status"], "PREPARED")
        self.assertEqual(run["send_attempts"], 0)
        self.assertEqual(run["scenario_sha256"], self.scenario_sha)
        self.assertEqual(self.history.read_bytes(), retained)
        self.assertEqual(len(list(self.store.runs.iterdir())), 2)

    def test_owned_readonly_prefix_leaves_store_unchanged(self):
        _, runner = self.candidate()
        original = self.history.read_bytes()
        before = sorted(self.store.root.iterdir())
        facts = runner._f07_qualify_new_prefix_readonly(RUN_ID, self.scenario)
        self.assertEqual(facts["state"], "WHOLE_ORIGINAL_NEW_PREFIX_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION")
        self.assertEqual(facts["scenario_sha256"], self.scenario_sha)
        self.assertEqual(facts["run_id"], RUN_ID)
        self.assertIsNone(facts["continuation"])
        self.assertTrue(all(facts[key] is False for key in ("new_called", "run_constructed", "save_called",
                                                             "send_called", "operation_clock_created")))
        self.assert_unprepared()
        self.assertEqual(self.history.read_bytes(), original)
        self.assertEqual(before, sorted(self.store.root.iterdir()))
        self.assertEqual(list(self.store.runs.iterdir()), [self.history])

    def test_owned_readonly_prefix_refuses_api_stop_and_prior_run(self):
        module, runner = self.candidate()
        runner.api = object()
        with self.assertRaisesRegex(module.Refused, "requires api=None"):
            runner._f07_qualify_new_prefix_readonly(RUN_ID, self.scenario)
        runner.api = None
        stop = self.store.root / "observer-stop.json"
        self.store.put(stop, {"product_cancelled": False})
        with self.assertRaisesRegex(module.Refused, "Observer stop marker set"):
            runner._f07_qualify_new_prefix_readonly(RUN_ID, self.scenario)
        self.assert_unprepared()
        stop.unlink()
        runner.new(RUN_ID, self.scenario)
        path = self.store.run_path(RUN_ID)
        retained = path.read_bytes()
        with self.assertRaisesRegex(module.Refused, "Run ID already used"):
            runner._f07_qualify_new_prefix_readonly(RUN_ID, self.scenario)
        self.assertEqual(path.read_bytes(), retained)

    def test_actual_owned_preclock_reads_exact_d10_without_writing(self):
        _, _, credentials, qualify = self.owned_caller(self.scenario)
        before = {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()}
        result = qualify()
        self.assertEqual(result["state"], "SELECTED_ORDINARY_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION")
        self.assertEqual(result["input_sha256"], self.scenario["steps"][0]["input"]["sha256"])
        self.assertFalse(result["readonly_prefix"]["operation_clock_created"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.store.root.rglob("*") if p.is_file()})
        self.assertEqual(credentials.read_bytes(), b"inert lock-test bytes\n")
        self.assert_unprepared()

    def test_actual_owned_preclock_refuses_busy_credential_and_releases_consumer(self):
        _, sink, credentials, qualify = self.owned_caller(self.scenario)
        with self.store.lock(credentials, create=False):
            with self.assertRaisesRegex(Exception, "Another tester consumer is active"):
                qualify()
            with self.store.lock(sink, create=False):
                self.assert_unprepared()
        self.assertFalse(qualify()["readonly_prefix"]["save_called"])

    def test_actual_owned_preclock_refuses_drifted_input(self):
        scenario = json.loads(self.base.encoded(self.scenario))
        upload = scenario["steps"][0]["input"]
        pinned = Path(upload["path"]).read_bytes()
        replacement = self.work / "local-d10.docx"
        self.store.write(replacement, pinned)
        upload["path"] = str(replacement)
        upload["stat"] = self.base.input_stat(replacement.stat())
        _, _, credentials, qualify = self.owned_caller(scenario)
        self.store.write(replacement, pinned + b"drift")
        with self.assertRaisesRegex(Exception, "Document source identity or metadata drift"):
            qualify()
        with self.store.lock(credentials, create=False):
            self.assert_unprepared()

    def test_actual_owned_preclock_stop_after_prefix_refuses_and_unlocks(self):
        caller, sink, credentials, qualify = self.owned_caller(self.scenario)
        document_reader = caller.read_document_input

        def interrupted_input(upload, guard):
            self.store.put(self.store.root / "observer-stop.json", {"product_cancelled": False})
            return document_reader(upload, guard)

        caller.read_document_input = interrupted_input
        with self.assertRaisesRegex(caller.Refused, "Observer stopped during read-only input qualification"):
            qualify()
        with self.store.lock(sink, create=False), self.store.lock(credentials, create=False):
            self.assert_unprepared()

    def test_unbound_candidate_still_refuses(self):
        runner = self.base.Runner(self.store, None)
        with self.assertRaisesRegex(self.base.Refused, "independent admission: absent"):
            runner.new(RUN_ID, self.scenario)
        self.assert_unprepared()

    def test_refuses_wrong_run_and_changed_scenario(self):
        module, runner = self.candidate()
        with self.assertRaisesRegex(module.Refused, "outside the exact ordinary admission"):
            runner.new("other-prospective-run", self.scenario)
        altered = dict(self.scenario, deadline_seconds=self.scenario["deadline_seconds"] - 1)
        with self.assertRaisesRegex(module.Refused, "Exact ordinary independent admission required"):
            runner.new(RUN_ID, altered)
        self.assert_unprepared()

    def test_refuses_history_drift_and_unbound_row(self):
        module, runner = self.candidate()
        old = self.store.get(self.history)
        self.store.put(self.history, dict(old, deadline=old["deadline"] - 1))
        with self.assertRaisesRegex(module.Refused, "history bytes changed"):
            runner.new(RUN_ID, self.scenario)
        self.store.put(self.history, old)
        self.store.put(self.store.run_path("foreign-row"), dict(old, id="foreign-row"))
        with self.assertRaisesRegex(module.Refused, "Unfinished prior run blocks new work"):
            runner.new(RUN_ID, self.scenario)
        self.assert_unprepared()

    def test_refuses_expired_authority_and_gateway_drift(self):
        module, runner = self.candidate()
        runner.clock = lambda: self.authority["expires_at"]
        with self.assertRaisesRegex(module.Refused, "Exact ordinary independent admission required"):
            runner.new(RUN_ID, self.scenario)
        runner.clock = lambda: self.now.timestamp()
        self.store.put(self.gateway_ref, dict(self.gateway, active_agents=1))
        with self.assertRaisesRegex(module.Refused, "Fresh quiescent gateway required"):
            runner.new(RUN_ID, self.scenario)
        self.assert_unprepared()

    def test_refuses_authority_or_checker_or_proof_drift(self):
        module, runner = self.candidate()
        for reference, refusal in ((self.authority_ref, "Exact ordinary independent admission required"),
                                   (self.checker, "Exact Root current checker bytes changed"),
                                   (self.proof, "Exact affirmative Root current qualification required")):
            with self.subTest(path=Path(reference["path"]).name):
                path = Path(reference["path"])
                prior = path.read_bytes()
                replacement = b"{}\n" if reference == self.authority_ref else b"changed\n"
                self.store.write(path, replacement)
                with self.assertRaisesRegex(module.Refused, refusal):
                    runner.new(RUN_ID, self.scenario)
                self.store.write(path, prior)
                self.assert_unprepared()

    def test_preserves_stop_and_pre_send_revalidation(self):
        module, runner = self.candidate()
        stop = self.store.root / "observer-stop.json"
        self.store.put(stop, {"product_cancelled": False})
        with self.assertRaisesRegex(module.Refused, "Observer stop marker set"):
            runner.new(RUN_ID, self.scenario)
        self.assert_unprepared()
        stop.unlink()
        run = runner.new(RUN_ID, self.scenario)
        with self.assertRaisesRegex(module.Refused, "Exact affirmative Root current qualification required"):
            runner.send(run)
        self.assertEqual(runner._send_phase, "CURSOR_AUTHORITY")
        self.assertEqual(run["send_attempts"], 0)
        self.assertEqual(run["send_state"], "none")

    def test_revalidates_before_intent_after_get_preflight(self):
        self.proof = self.reference("proof.json", b"synthetic cursor proof\n")
        module, runner = self.candidate()
        calls = []

        class GetOnlyTransport:
            def call(self, method, params=None, timeout=None):
                responses = {"getMe": {"is_bot": True, "id": module.TESTER},
                             "getWebhookInfo": {"url": ""},
                             "getChat": {"id": module.PEER, "type": "private"}}
                calls.append(method)
                return responses[method]

        run = runner.new(RUN_ID, self.scenario)
        runner.api = GetOnlyTransport()
        with self.assertRaisesRegex(module.Refused, "Exact affirmative Root current qualification required"):
            runner.send(run)
        self.assertEqual(calls, ["getMe", "getWebhookInfo", "getChat"])
        self.assertEqual(runner._send_phase, "PRE_INTENT_REVALIDATION")
        self.assertEqual(self.store.get(self.store.run_path(RUN_ID))["send_attempts"], 0)
        self.assertEqual(run["send_state"], "none")
        self.assertEqual(list(self.store.root.glob("send-task-*")), [])

    def test_scoped_observer_has_no_direct_cli(self):
        raw = self.compose()
        with self.assertRaisesRegex(SystemExit, "requires the reviewed owned caller"):
            load_observer(raw, "__main__")
        module = load_observer(raw)
        with self.assertRaisesRegex(SystemExit, "requires the reviewed owned caller"):
            module.main(["run"])


def refuse_network(event, args):
    if event.startswith(("socket.", "subprocess.")) or event in {"os.exec", "os.system", "os.spawn"}:
        raise AssertionError(f"Unexpected network or subprocess event {event}")


if __name__ == "__main__":
    source, scenario = map(Path, sys.argv[1:])
    SOURCE = source.read_bytes()
    SCENARIO = json.loads(scenario.read_bytes())
    os.umask(0o077)
    sys.addaudithook(refuse_network)
    unittest.main(argv=[sys.argv[0]])
