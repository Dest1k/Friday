#!/usr/bin/env python3
"""Exercise the genuine R4 prepare consumer on a disjoint synthetic store."""

import datetime as dt
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
        sandbox = tempfile.TemporaryDirectory(prefix="frw-ordinary-admission-control-")
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

    def test_genuine_prepare_uses_exact_authority(self):
        _, runner = self.candidate()
        retained = self.history.read_bytes()
        run = runner.new(RUN_ID, self.scenario)
        self.assertEqual(run["status"], "PREPARED")
        self.assertEqual(run["send_attempts"], 0)
        self.assertEqual(run["scenario_sha256"], self.scenario_sha)
        self.assertEqual(self.history.read_bytes(), retained)
        self.assertEqual(len(list(self.store.runs.iterdir())), 2)

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
