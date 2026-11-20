"""Protected D02 receiver metadata on the existing gateway control socket."""

import asyncio
import concurrent.futures
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from .d02_receiver_state import check_receiver_state


SCHEMA = "frw.gateway.d02-owned-receiver-control.v1"
OPTIONS_SCHEMA = "frw.Root.D02.receiver-options.v1"
PHASES = {
    "088d47d6a8efbf63068bb8fff13c69af05478a20156960811ac1d170db46c4cf",
    "bab05e12b1465b984bf58acfd8b25507162b31c135dbb3623623951a06b10a05",
}
ARM_SECONDS = 24
SHORT_SECONDS = 1.2
_LOCAL_RIGHTS_SECONDS = 0.2
_CAPTURE = 180
_RESERVE = 5 + 20
_RUN_JSON_LIMIT = 1024 * 1024
_CLOCK_TIMING = {"outer_seconds": 600, "operation_seconds": 300, "ack_seconds": 10,
                 "reply_window_seconds": _CAPTURE, "reserve_seconds": 5}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def _now(value):
    return type(value) in (int, float) and math.isfinite(value)


def _hex(value, chars=64):
    return type(value) is str and re.fullmatch(r"[0-9a-f]+", value) is not None and len(value) == chars


def _unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "d02_control_duplicate_json")
        value[key] = item
    return value


def _encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def _private_bytes(path, read_owned, limit):
    before = path.lstat()
    directory = path.parent.lstat()
    require(stat.S_ISDIR(directory.st_mode) and directory.st_uid == os.getuid()
            and stat.S_IMODE(directory.st_mode) == 0o700 and stat.S_ISREG(before.st_mode)
            and before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600
            and before.st_nlink == 1 and 0 < before.st_size <= limit,
            "d02_control_private_custody")
    raw = read_owned(path, private=True)
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode", "st_uid", "st_nlink")
    after = path.lstat()
    require(len(raw) == before.st_size
            and all(getattr(after, key) == getattr(before, key) for key in fields),
            "d02_control_protected_bytes_changed")
    return raw


def _private_doc(reference, read_owned, *, name=None, sized=True):
    keys = {"path", "sha256", "bytes"} if sized else {"path", "sha256"}
    require(type(reference) is dict and set(reference) == keys and _hex(reference["sha256"]),
            "d02_control_protected_reference")
    path = Path(reference["path"])
    require(str(path) == reference["path"] and path.is_absolute() and path.resolve(strict=True) == path
            and ".." not in path.parts and (name is None or path.name == name), "d02_control_protected_path")
    raw = _private_bytes(path, read_owned, 65536)
    require((not sized or type(reference["bytes"]) is int and len(raw) == reference["bytes"])
            and sha256(raw).hexdigest() == reference["sha256"], "d02_control_protected_bytes_changed")
    result = json.loads(raw, object_pairs_hook=_unique)
    require(type(result) is dict and raw == _encode(result), "d02_control_canonical_document")
    return result, path


def _kernel(pid):
    require(type(pid) is int and pid > 0, "d02_control_process_identity")
    proc = Path("/proc") / str(pid)
    require(proc.stat().st_uid == os.getuid(), "d02_control_process_owner")
    fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "start_time": int(fields[19]),
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def _work_identity(info):
    mode = stat.S_IMODE(info.st_mode)
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and mode == 0o700,
            "d02_control_protected_workdir")
    return dict(device=info.st_dev, inode=info.st_ino, uid=info.st_uid, mode=mode)


def _held_slot(path, identity, owner):
    require(type(owner) is dict and set(owner) == {"pid", "start_time", "boot_id"}
            and _kernel(owner["pid"]) == owner and path.resolve(strict=True) == path,
            "d02_control_original_owner")
    info = path.lstat()
    current = dict(device=info.st_dev, inode=info.st_ino, uid=info.st_uid,
                   mode=stat.S_IMODE(info.st_mode), nlink=info.st_nlink)
    require(stat.S_ISREG(info.st_mode) and current["uid"] == os.getuid()
            and current["mode"] == 0o600 and current["nlink"] == 1 and current == identity,
            "d02_control_fixed_slot_identity")
    device = f"{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}"
    require(any(len(row) >= 6 and row[1] == "FLOCK" and row[3] == "WRITE"
                and row[4] == str(owner["pid"]) and row[5] == device
                for row in (line.split() for line in Path("/proc/locks").read_text().splitlines())),
            "d02_control_fixed_slot_not_held")


class ReceiverControl:
    def __init__(self, *, home, slot, store, read_owned, select_adapter, check_rights):
        self.home = Path(home)
        self.slot = Path(slot)
        self.store = Path(store)
        self.read_owned = read_owned
        self.select_adapter = select_adapter
        self.check_rights = check_rights

    def doc(self, reference, **options):
        return _private_doc(reference, self.read_owned, **options)

    def _rights_current(self, options, phase, transport_deadline):
        # Do not spend the long-poll transport budget holding a native loop turn.
        deadline = min(transport_deadline, time.monotonic() + _LOCAL_RIGHTS_SECONDS)
        self.check_rights(options, phase, deadline)
        require(time.monotonic() < deadline, "d02_control_rights_check_expired")

    def _request(self, reference):
        value, _ = self.doc(reference, sized=False)
        require(set(value) == {"schema", "operator", "action", "query_id", "boot_id", "gateway",
                               "created_monotonic", "expires_monotonic", "arm_intent",
                               "receiver_options", "proof"}
                and value["schema"] == SCHEMA and value["operator"] == "Root"
                and value["action"] in ("arm", "confirm", "cutoff") and _hex(value["query_id"], 32)
                and (value["proof"] is None) == (value["action"] == "arm"),
                "d02_control_exact_request")
        actual = _kernel(os.getpid())
        require(value["boot_id"] == actual.pop("boot_id") and value["gateway"] == actual,
                "d02_control_gateway_changed")
        start, end = value["created_monotonic"], value["expires_monotonic"]
        budget = 25 if value["action"] == "arm" else 1.5
        require(_now(start) and _now(end) and 0 <= start <= time.monotonic() < end <= start + budget,
                "d02_control_request_expired")
        return value

    def _owner(self, request):
        intent, intent_path = self.doc(request["arm_intent"], name="receiver-arm-intent.json")
        claim, claim_path = self.doc(intent["claim"], name="claim.json")
        driver, driver_path = self.doc(intent["binding"])
        options, _ = self.doc(request["receiver_options"])
        phase, _ = self.doc(driver["phase"])
        authority, _ = self.doc(driver["authority"])
        work = Path(driver["workdir"])
        run_id, scenario_sha = intent["run_id"], intent["scenario_sha256"]
        require(type(run_id) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", run_id)
                and scenario_sha in PHASES and phase["scenario_sha256"] == scenario_sha
                and sha256(_encode(phase["scenario"])).hexdigest() == scenario_sha,
                "d02_control_exact_d02_phase")
        require(set(intent) == {"run_id", "scenario_sha256", "claim", "parent", "binding", "no_retry"}
                and driver["schema"] == "frw.Root.D02.owned-ordinary-driver.v1"
                and driver["status"] == "ROOT_BOUND_ONE_FUTURE_OPERATION" and driver["operator"] == "Root"
                and work.parent == driver_path.parent and claim_path.parent == intent_path.parent == work
                and _work_identity(work.lstat()) == driver["work_identity"]
                and not work.is_relative_to(self.home) and not work.is_relative_to(self.store)
                and driver["run_id"] == claim["run_id"] == run_id and claim["scenario_sha256"] == scenario_sha
                and claim["parent"] == intent["parent"] and claim["binding"] == intent["binding"]
                and claim["no_retry"] is True and intent["no_retry"] is True
                and driver["receiver_options"] == request["receiver_options"], "d02_control_exact_once_claim")
        upload = phase["scenario"]["steps"][0].get("input")
        input_sha = None if upload is None else upload["sha256"]
        require(authority["schema"] == "frw.Root.ordinary-independent-history-admission.v1"
                and authority["operator"] == "Root" and authority["accepted"] is True
                and authority["qualification_only"] is False
                and authority["run_scenarios"] == {run_id: scenario_sha}
                and type(authority["history"]) is dict and bool(authority["history"])
                and run_id not in authority["history"]
                and authority["new_independent_inputs_only"] is True and authority["no_old_task_replay"] is True
                and all(authority[key] is False for key in ("new_trial_for_historical_task", "old_rows_modified",
                    "unknown_effects_resolved", "product_or_B00_acceptance"))
                and claim["readonly_qualification"]["state"] == "SELECTED_ORDINARY_READONLY_QUALIFIED_NOT_EFFECT_ADMISSION"
                and claim["readonly_qualification"]["run_id"] == run_id
                and claim["readonly_qualification"]["scenario_sha256"] == scenario_sha
                and claim["readonly_qualification"]["input_sha256"] == input_sha
                and claim["readonly_qualification"]["new_called"] is False
                and claim["readonly_qualification"]["send_called"] is False,
                "d02_control_exact_active_once_authority")
        require(set(options) == {"schema", "principal", "profile", "rights", "observer_expires_monotonic"}
                and options["schema"] == OPTIONS_SCHEMA and _now(options["observer_expires_monotonic"])
                and options["observer_expires_monotonic"] <= request["created_monotonic"] + 600
                and str(phase["scenario"]["peer_id"]) == options["principal"]["account_id"]
                and str(phase["scenario"]["tester_id"]) == options["principal"]["user_id"]
                and type(phase["scenario"]["max_updates"]) is int,
                "d02_control_exact_receiver_options")
        _held_slot(self.slot, driver["slot_identity"], intent["parent"])
        return intent, driver, options, phase["scenario"], work

    def _durable_reservation(self, work, intent, options_ref, identity):
        # This metadata belongs to Once's existing no-retry work directory.
        # It is committed before touching the adapter and never overwritten.
        raw = _encode({"claim": intent["claim"], "parent": intent["parent"], "options": options_ref, "no_retry": True})
        directory = os.open(work, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            require(_work_identity(os.fstat(directory)) == identity, "d02_control_workdir_changed")
            fd = os.open("receiver-gateway-reservation.json",
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(directory)
        finally:
            os.close(directory)

    def _reservation_current(self, intent, request, work):
        expected = _encode({"claim": intent["claim"], "parent": intent["parent"],
                            "options": request["receiver_options"], "no_retry": True})
        path = work / "receiver-gateway-reservation.json"
        require(_private_bytes(path, self.read_owned, 65536) == expected,
                "d02_control_reservation_changed")

    @staticmethod
    def _arm_from(adapter, claim_sha, expires):
        value = adapter._ordinary_dm_wire_arm_readback(claim_sha)
        require(type(value) is dict
                and set(value) == {"claim_sha256", "generation", "first_offset", "armed_monotonic", "expires_monotonic"}
                and value["claim_sha256"] == claim_sha
                and type(value["generation"]) is int and value["generation"] > 0
                and type(value["first_offset"]) is int and 0 <= value["first_offset"] < 2**63
                and _now(value["armed_monotonic"]) and _now(value["expires_monotonic"])
                and 0 <= value["armed_monotonic"] <= time.monotonic() < value["expires_monotonic"] == expires,
                "d02_control_arm_not_confirmed")
        return {"state": "ARMED", **value}

    def _arm_receipt(self, reference, intent, request, work, adapter, expires):
        self._reservation_current(intent, request, work)
        arm, path = self.doc(reference, name="receiver-arm.json")
        current = self._arm_from(adapter, intent["claim"]["sha256"], expires)
        require(path.parent == work and arm["no_retry"] is True
                and arm["claim"] == intent["claim"] and arm["parent"] == intent["parent"]
                and arm["intent"] == request["arm_intent"] and arm["run_id"] == intent["run_id"]
                and arm["scenario_sha256"] == intent["scenario_sha256"]
                and arm["receipt"] == current, "d02_control_arm_readback_changed")
        return arm, current

    async def _arm(self, request, intent, driver, options, scenario, work, adapter, deadline):
        require(not os.path.lexists(work / "clock.json"), "d02_control_clock_already_started")
        self._durable_reservation(work, intent, request["receiver_options"], driver["work_identity"])
        _held_slot(self.slot, driver["slot_identity"], intent["parent"])
        require(time.monotonic() < deadline, "d02_control_arm_intent_expired")
        ready = asyncio.Event()
        loop = asyncio.get_running_loop()
        submitted = False
        waiting = True
        claim_sha = intent["claim"]["sha256"]
        generation = adapter._polling_generation

        def owner_is_current():
            now = time.monotonic()
            if now >= options["observer_expires_monotonic"] or not ready.is_set() and (
                    not waiting or now >= deadline):
                return False
            _held_slot(self.slot, driver["slot_identity"], intent["parent"])
            if submitted and not ready.is_set():
                current, _, _, _, current_work = self._owner(request)
                require(current == intent and work == current_work
                        and self.select_adapter(options["profile"], options["principal"]) is adapter,
                        "d02_control_native_arm_owner_changed")
                self._reservation_current(intent, request, work)
                self._rights_current(options, "arm", deadline)
                require(time.monotonic() < deadline, "d02_control_native_arm_expired")
                loop.call_soon(ready.set)
            return True

        try:
            adapter._reserve_ordinary_dm_wire_window(claim_sha256=claim_sha,
                user_id=int(options["principal"]["user_id"]), generation=generation,
                expires_monotonic=options["observer_expires_monotonic"], max_updates=scenario["max_updates"],
                owner_is_current=owner_is_current)
            submitted = True
            await asyncio.wait_for(ready.wait(), timeout=max(0, deadline - time.monotonic()))
            _held_slot(self.slot, driver["slot_identity"], intent["parent"])
            require(time.monotonic() < deadline, "d02_control_arm_readback_expired")
            return self._arm_from(adapter, claim_sha, options["observer_expires_monotonic"])
        finally:
            waiting = False

    @staticmethod
    def _check_ack_window(run, ack, window, scenario):
        encoding = run["sent_api_ack_reference"]["representation"]
        if encoding == "botapi-wire-envelope-json":
            require(type(ack) is dict and ack.get("ok") is True, "d02_control_successful_ack_envelope")
            ack = ack["result"]
        else:
            require(encoding == "decoded-message-json", "d02_control_known_ack_representation")
        message = run["sent_message_id"]
        date = run["sent_date"]
        require(type(message) is int and message > 0 and type(date) is int and date >= 0
                and ack["message_id"] == message and ack["date"] == date
                and ack["from"]["id"] == scenario["tester_id"] and ack["from"]["is_bot"] is True
                and ack["chat"]["id"] == scenario["peer_id"] and ack["chat"]["type"] == "private",
                "d02_control_received_ack_route")
        expected = {key: run[key] for key in ("scenario_sha256", "step", "send_attempts", "sent_message_id",
                    "sent_at", "send_intent_at", "send_dispatch_at", "send_timeout_seconds", "capture_until", "deadline")}
        expected.update(run_id=run["id"], window_seconds=_CAPTURE, ack=run["sent_api_ack_reference"],
                        task=run["sent_task_reference"])
        if "continuation_reference" in run:
            expected["continuation"] = run["continuation_reference"]
        require(window == expected and all(_now(run[key]) for key in
                ("send_intent_at", "send_dispatch_at", "sent_at", "send_timeout_seconds", "deadline"))
                and run["send_intent_at"] <= run["send_dispatch_at"] <= run["sent_at"]
                    <= run["send_dispatch_at"] + run["send_timeout_seconds"]
                and run["send_timeout_seconds"] == _CLOCK_TIMING["ack_seconds"]
                and run["capture_until"] + _CLOCK_TIMING["reserve_seconds"] <= run["deadline"],
                "d02_control_retained_window_binding")

    def _ack_cutoff(self, request, intent, work, adapter, expires, scenario):
        proof, proof_path = self.doc(request["proof"], name="receiver-cutoff-intent.json")
        _, receipt = self._arm_receipt(proof["arm"], intent, request, work, adapter, expires)
        clock, clock_path = self.doc(proof["clock"], name="clock.json")
        run_id = intent["run_id"]
        path = self.store / "runs" / (run_id + ".json")
        raw = _private_bytes(path, self.read_owned, _RUN_JSON_LIMIT)
        run = json.loads(raw, object_pairs_hook=_unique)
        before, after = proof["ack_monotonic"]
        wall = proof["ack_wall"]
        cutoff = proof["receiver_monotonic_cutoff"]
        require(proof_path.parent == clock_path.parent == work and proof["no_retry"] is True
                and proof["run_id"] == clock["run_id"] == run["id"] == run_id
                and proof["scenario_sha256"] == clock["scenario_sha256"] == run["scenario_sha256"] == intent["scenario_sha256"]
                and clock["schema"] == "frw.Root.F07.finite-operation-clock.v1"
                and clock["status"] == "ROOT_BOUND_FUTURE_OPERATION" and clock["old_effects_clocks_preserved"] is True
                and clock["timing"] == _CLOCK_TIMING and clock["receiver_arm"] == proof["arm"]
                and run["status"] == "OBSERVING" and run["send_state"] == "sent" and run["send_attempts"] == 1
                and run["step"] == 0 and run["scenario"] == scenario
                and run["sent_at"] == wall and run["capture_until"] == proof["original_wall_cutoff"] == wall + _CAPTURE
                and all(_now(item) for item in (before, after, wall, cutoff))
                and receipt["armed_monotonic"] <= clock["started_monotonic"] <= before <= after <= time.monotonic()
                and clock["deadline_monotonic"] == clock["started_monotonic"] + 600
                and cutoff == after + _CAPTURE
                and cutoff + _RESERVE <= min(clock["deadline_monotonic"], receipt["expires_monotonic"]),
                "d02_control_original_ack_clock")
        retained = {}
        for field, label in (("ack", "ack"), ("send_window", "window")):
            ref = proof[field]
            require(ref == run["sent_api_ack_reference" if field == "ack" else "sent_window_reference"]
                    and ref["basename"] == f"send-{label}-{run_id}-0-1.json",
                    "d02_control_current_ack_custody")
            content = _private_bytes(self.store / ref["basename"], self.read_owned, _RUN_JSON_LIMIT)
            require(len(content) == ref["bytes"] and sha256(content).hexdigest() == ref["sha256"],
                    "d02_control_current_ack_bytes")
            retained[field] = json.loads(content, object_pairs_hook=_unique)
        self._check_ack_window(run, retained["ack"], retained["send_window"], scenario)
        # Native window identity is checked by the positive ARM readback above.
        return adapter._ordinary_dm_wire_window, cutoff

    async def dispatch(self, reference, transport_deadline):
        request = self._request(reference)
        deadline = min(transport_deadline, request["expires_monotonic"])
        intent, driver, options, scenario, work = self._owner(request)
        action = request["action"]
        adapter = self.select_adapter(options["profile"], options["principal"])
        phase = {"arm": "arm", "confirm": "dispatch", "cutoff": "post_dispatch"}[action]
        self._rights_current(options, phase, deadline)
        require(time.monotonic() < deadline, "d02_control_dispatch_expired")
        if action == "arm":
            receipt = await self._arm(request, intent, driver, options, scenario, work, adapter, deadline)
            return {"accepted": True, "query_id": request["query_id"], "action": action,
                    "state": "ARMED", "receipt": receipt}
        expires = options["observer_expires_monotonic"]
        if action == "confirm":
            _, receipt = self._arm_receipt(request["proof"], intent, request, work, adapter, expires)
            _held_slot(self.slot, driver["slot_identity"], intent["parent"])
            require(time.monotonic() < deadline, "d02_control_confirm_expired")
            return {"accepted": True, "query_id": request["query_id"], "action": action,
                    "state": "ARMED", "receipt": receipt}
        window, cutoff = self._ack_cutoff(request, intent, work, adapter, expires, scenario)
        _held_slot(self.slot, driver["slot_identity"], intent["parent"])
        require(time.monotonic() < deadline, "d02_control_cutoff_expired")
        window.bind_cutoff(cutoff)
        return {"accepted": True, "query_id": request["query_id"], "action": action,
                "state": "CUTOFF_BOUND"}

    def handle(self, params, loop):
        if type(params) is not dict or set(params) != {"root_request"}:
            return {"accepted": False, "error": "d02_control_exact_parameters", "no_retry": True}
        future = None
        try:
            request = self._request(params["root_request"])
            budget = ARM_SECONDS if request["action"] == "arm" else SHORT_SECONDS
            deadline = min(time.monotonic() + budget, request["expires_monotonic"])
            future = asyncio.run_coroutine_threadsafe(self.dispatch(params["root_request"], deadline), loop)
            return future.result(timeout=max(0, deadline - time.monotonic()))
        except concurrent.futures.TimeoutError:
            if future is not None:
                future.cancel()
            return {"accepted": False, "error": "d02_receiver_control_UNKNOWN", "no_retry": True}
        except Exception:
            return {"accepted": False, "error": "d02_receiver_control_refused", "no_retry": True}


def ordinary_d02_receiver_verb(runner, loop):
    """Bind only the installed process home and existing Telegram route."""
    from gateway.config import Platform
    from gateway.session import SessionSource
    from gateway.session_identity import resolve_identity
    from gateway import pairing
    from hermes_cli import friday_product_access as access, friday_user_scope as scope
    from hermes_cli.friday_dashboard_owner import read_owned
    from hermes_cli.friday_ordinary_gateway import receiving_pairing_store
    from hermes_cli.plugins_state import PluginState
    from hermes_constants import get_process_hermes_home

    home = Path(get_process_hermes_home())
    slot = Path.home() / ".jericho/runtime/locks/synthetic-live-acceptance.lock"
    store = Path.home() / ".local/share/friday-telegram-bot-test"

    def select(profile, principal):
        user = principal["user_id"]
        adapter = runner.adapters.get(Platform.TELEGRAM)
        require(adapter is not None and principal["transport_profile"] == "default"
                and str(adapter._bot.id) == principal["account_id"], "d02_control_receiving_bot")
        source = SessionSource(platform=Platform.TELEGRAM, chat_id=user, chat_type="dm", user_id=user, is_bot=True)
        identity = resolve_identity(source, runner=runner, adapter=adapter, transport_profile="default", primary_home=home)
        require(identity.adapter() is adapter and identity.multiplexed and not identity.transport_inferred
                and identity.authorization_home == home and identity.transport_profile == "default"
                and identity.runtime_profile == profile and identity.runtime_home == home / "profiles" / profile,
                "d02_control_live_route_changed")
        ordinary, pairings = receiving_pairing_store(runner, source)
        require(ordinary is True and pairings is not None, "d02_control_live_receiving_pairing")
        return adapter

    def rights(options, phase, deadline):
        check_receiver_state(home, profile=options["profile"], expected_principal=options["principal"],
            rights=options["rights"], state=PluginState("friday_rework"), access=access, scope=scope,
            pairing=pairing, phase=phase, deadline=deadline)

    controller = ReceiverControl(home=home, slot=slot, store=store, read_owned=read_owned,
                                 select_adapter=select, check_rights=rights)
    return lambda params: controller.handle(params, loop)
