"""Normal startup over checked native ownership; no admission or process store.

All checks use installed native consumers. A worker receipt is reusable source
readiness only: this module never mints a per-job A0 capability or starts workers.
"""

from __future__ import annotations

import os
import re
import shlex
import stat
import sys
import time
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from pathlib import Path


_GATEWAY_STARTUP_TIMEOUT_DROPIN = b"[Service]\nTimeoutStartSec=180s\n"
_GATEWAY_START_COMMAND_SECONDS = 210
_GATEWAY_START_PROOF_SECONDS = 60
_GATEWAY_START_PROOF_RESERVE_SECONDS = 5
_GATEWAY_START_IDENTIFY_SECONDS = 20
_GATEWAY_START_IDENTIFY_MANIFEST = (
    "patches/hermes/ordinary-start-identify-cutoff-after-source341-manifest.json"
)


def prerequisites(value, budget):
    """No label in an installer/profile/health receipt grants launch authority."""
    from hermes_cli.friday_dashboard_owner import expected
    from hermes_cli.source_build import source_product_current
    from hermes_constants import get_hermes_home
    from pm.environments import owning_home_root, project_python
    from pm.paths import repo_root
    from scripts.friday_install import owned_file, require

    home = Path(value["home"])
    source = home / "hermes-agent"
    require(
        get_hermes_home() == home
        and repo_root() == source
        and Path(sys.executable) == project_python(source)
        and owning_home_root(source) in (None, home),
        "native_start_generation_mismatch",
    )
    if 'worker_install' in value:
        from hermes_cli.config_effective import read_user_config_effective_readonly
        configured = budget.call(read_user_config_effective_readonly,home / 'config.yaml')
        require(configured['plugins']['entries']['friday_rework']['settings']['runtime'] == value['product']['runtime'],
                'native_start_runtime_generation_changed')
    require(
        source_product_current(source, "tui", source / "ui-tui/dist")
        and source_product_current(source, "web", source / "hermes_cli/web_dist"),
        "native_frontend_freshness_not_verified",
    )
    pins = snapshot(home, budget)
    # This API is from the separately reviewed credential-admission overlay.
    # Its absence in the TLS-only base is a real dependency, not an invitation
    # to duplicate its key/pool/route/channel policy here.
    try:
        from hermes_cli.friday_credential_admission import bootstrap, channel_inputs, route_inputs, scoped
    except ModuleNotFoundError as exc:
        if exc.name != "hermes_cli.friday_credential_admission":
            raise
        raise ValueError("native_credential_admission_join_required") from None
    budget.call(bootstrap, home)
    identity = budget.call(expected)
    require(identity["home"] == str(home), "native_start_home_mismatch")
    with scoped(home):
        budget.call(route_inputs)
        contract, _values = budget.call(channel_inputs)
        require(
            contract["profile"] == "default" and bool(contract["required_scoped_names"]["channels"]),
            "native_receiving_channel_required",
        )
    from plugins.friday_rework.startup_health import worker_health

    report = budget.call(worker_health)
    rows = report["workers"]
    require(
        {r["worker"] for r in rows if r["deployment_verified"]} == {"dsh", "a0"}
        and all(r["deployment_verified"] for r in rows),
        "mandatory_a0_web_kernel_and_final_native_dashboard_owner_not_admitted",
    )
    # All imported code and native launchers belong to the same already checked
    # source generation. Snapshot comparison closes drift before service effects.
    from hermes_cli._launchers import _launcher_script, resolve_store_python

    python = resolve_store_python(source, publication=True)
    require(python is not None, "native_published_python_required")
    launcher = source / ".hermes/bin/hermes"
    command = [str(python), "-I", "-c", _launcher_script("hermes", source, None)]
    require(
        owned_file(launcher) == ("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n').encode()
        and os.access(launcher, os.X_OK)
        and not launcher.stat().st_mode & 0o022,
        "native_launcher_generation_changed",
    )
    unchanged(pins, budget)
    return identity, pins


def snapshot(home, budget):
    from scripts.friday_install import digest, owned_file, read_json

    source = home / "hermes-agent"
    launcher = source / ".hermes/bin/hermes"
    files = {
        str(home / p): True
        for p in ("config.yaml", "FRIDAY-PROFILE.json", "FRIDAY-INSTALL.json", "hermes-agent.source.json")
    }
    marker = read_json(home / "FRIDAY-INSTALL.json")
    files.update({str(source / p): False for p in read_json(home / "hermes-agent.source.json")["files"]})
    files.update({str(home / p): True for p in marker["plugin_files"]})
    files.update({str(home / p): True for p in marker.get("tls_files", {})})
    files[str(launcher)] = False
    for name in (".env", "auth.json"):
        if (home / name).exists() or (home / name).is_symlink():
            files[str(home / name)] = True
    pins = {
        path: {"private": private, "sha256": digest(owned_file(path, private=private))}
        for path, private in files.items()
    }
    for name in (".env", "auth.json"):
        if str(home / name) not in pins:
            pins[str(home / name)] = {"private": True, "sha256": None}
    return pins


def unchanged(pins, budget):
    from scripts.friday_install import digest, owned_file, require

    for path, row in pins.items():
        if row["sha256"] is None:
            require(not Path(path).exists() and not Path(path).is_symlink(), "native_start_input_changed")
            continue
        require(
            digest(budget.call(owned_file, path, private=row["private"])) == row["sha256"],
            "native_start_input_changed",
        )
    for path in pins:
        if Path(path).name == "hermes-agent.source.json":
            from hermes_cli.friday_dashboard_owner import source_identity

            budget.call(source_identity, Path(path).parent, source=Path(path).parent / "hermes-agent")


@contextmanager
def _gateway_timeout_dropin_custody(unit, fragment):
    from scripts.friday_install import require

    reason = "gateway_dropin_requires_reconciliation"
    require(unit.anchor == "/" and ".." not in unit.parts, reason)
    uid = os.getuid()
    directories = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    files = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    identity = ("st_dev", "st_ino", "st_mode", "st_uid", "st_ctime_ns")
    revision = identity + ("st_nlink", "st_size", "st_mtime_ns")
    with ExitStack() as opened:
        retained = []

        def retain(name, parent, flags, fields):
            fd = os.open(name, flags, dir_fd=parent)
            opened.callback(os.close, fd)
            before = os.fstat(fd)
            retained.append((fd, parent, name, fields, before))
            return fd, before

        parent = None
        parts = unit.parent.parts
        for index, part in enumerate(parts):
            fields = revision if index == len(parts) - 1 else identity
            parent, info = retain(part, parent, directories, fields)
            require(info.st_uid in (0, uid) and not info.st_mode & 0o022, reason)
        require(info.st_uid == uid, reason)
        dropins, info = retain(fragment.parent.name, parent, directories, revision)
        require(info.st_uid == uid and not info.st_mode & 0o022, reason)
        require(os.listdir(dropins) == [fragment.name], reason)

        def read(name, parent, limit):
            fd, before = retain(name, parent, files, revision)
            require(stat.S_ISREG(before.st_mode) and before.st_uid == uid
                    and before.st_nlink == 1 and not before.st_mode & 0o022
                    and 0 <= before.st_size <= limit, reason)
            with os.fdopen(fd, "rb", closefd=False) as stream:
                data = stream.read(before.st_size + 1)
            require(len(data) == before.st_size, reason)
            return data

        actual = read(unit.name, parent, 64 * 1024**2)
        require(read(fragment.name, dropins, len(_GATEWAY_STARTUP_TIMEOUT_DROPIN))
                == _GATEWAY_STARTUP_TIMEOUT_DROPIN, reason)

        def unchanged():
            for fd, parent_fd, name, fields, before in retained:
                current = os.fstat(fd)
                named = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                require(all(getattr(before, field) == getattr(current, field) == getattr(named, field)
                            for field in fields), reason)

        unchanged()
        yield actual.decode("utf-8-sig")
        unchanged()


def gateway_preflight(home, profile, budget, timeout_readback=None):
    """Native exact user unit only; never adopt, refresh, replace or reap foreign."""
    from gateway import host_rendezvous as hr
    from hermes_cli import gateway as gw
    from hermes_constants import get_hermes_home
    from scripts.friday_install import owned_file, require

    require(get_hermes_home() == home and profile == "default", "foreign_gateway_launch_home")
    require(gw.supports_systemd_services(), "native_user_systemd_required")
    require(
        not budget.call(gw.has_legacy_hermes_units) and not budget.call(gw.has_conflicting_systemd_units),
        "duplicate_native_gateway_service",
    )
    unit = gw.get_systemd_unit_path(system=False)
    require(not gw.get_systemd_unit_path(system=True).exists(), "system_gateway_unit_not_adopted")
    dropins = unit.parent / (unit.name + ".d")
    require(not dropins.is_symlink(), "gateway_dropin_requires_reconciliation")
    populated = dropins.exists() and any(dropins.iterdir())
    require(not populated or timeout_readback is not None, "gateway_dropin_requires_reconciliation")
    expected = budget.call(gw.generate_systemd_unit, system=False)
    normalize = gw._normalize_service_definition
    strip_optional = gw._strip_optional_systemd_directives
    if populated:
        fragment = dropins / "20-startup-timeout.conf"
        with _gateway_timeout_dropin_custody(unit, fragment) as actual:
            # The generated definition embeds the checked home. Compare the
            # bytes from the held FD without opening a second path for HOME.
            require(normalize(strip_optional(actual)) == normalize(strip_optional(expected)),
                    "foreign_or_changed_gateway_unit")
            expected_properties = {
                "Id": unit.name,
                "LoadState": "loaded",
                "FragmentPath": str(unit),
                "DropInPaths": str(fragment),
                "NeedDaemonReload": "no",
                "TimeoutStartUSec": "3min",
            }
            require(budget.call(timeout_readback, unit, tuple(expected_properties)) == expected_properties,
                    "gateway_timeout_dropin_effective_unproved")
        budget.check()
    elif unit.exists() or unit.is_symlink():
        require(not unit.stat().st_mode & 0o022, "writable_gateway_unit_refused")
        actual = budget.call(owned_file, unit).decode("utf-8-sig")
        require(
            gw._hermes_home_pinned_by_unit(unit) == str(home)
            and normalize(strip_optional(actual)) == normalize(strip_optional(expected)),
            "foreign_or_changed_gateway_unit",
        )
    # Existing live native owners must have proved exact home/profile/incarnation.
    record = budget.call(hr.read_record, hr.ROLE_GATEWAY, include_stale=True)
    if record is not None:
        from scripts.friday_native import host_owner

        budget.call(host_owner, record, home, profile)
        require(
            hr.liveness_is_proven(record) and hr.record_token_is_consistent(record),
            "gateway_incarnation_requires_reconciliation",
        )
    return unit, record


def gateway_observation(home, budget, read_properties=None, *, identify_with_cutoff=None):
    from gateway import host_rendezvous as hr
    from gateway.control_socket import CONTROL_PROTOCOL_VERSION, identify_gateway
    from gateway.status import normalize_updated_at, runtime_status_is_stale
    from hermes_cli import gateway as gw
    from hermes_cli.friday_gateway_owner import expected as expected_gateway
    from scripts.friday_install import read_json, require
    from scripts.friday_native import host_owner

    record = budget.call(hr.read_record, hr.ROLE_GATEWAY, include_stale=True)
    require(record is not None, "native_gateway_owner_not_observed")
    budget.call(host_owner, record, home, "default")
    require(
        hr.liveness_is_proven(record) and hr.record_token_is_consistent(record),
        "native_gateway_incarnation_unproved",
    )
    if read_properties is None:
        def read_properties(properties):
            return gw._read_systemd_unit_properties(system=False, properties=properties)
    properties = ("ActiveState", "SubState", "MainPID", "InvocationID")
    props = budget.call(read_properties, properties)
    state = budget.call(gw._read_gateway_runtime_status)
    source = budget.call(read_json, home / "hermes-agent.source.json")
    updated = normalize_updated_at(state.get("updated_at")) if isinstance(state, dict) else None
    require(
        props.get("ActiveState") == "active"
        and props.get("SubState") == "running"
        and props.get("MainPID") == str(record.pid)
        and re.fullmatch("[0-9a-f]{32}", props.get("InvocationID", "")) is not None
        and isinstance(state, dict)
        and type(state.get("pid")) is int
        and state.get("pid") == record.pid
        and state.get("gateway_state") == "running"
        and state.get("kind") == "hermes-gateway"
        and type(state.get("start_time")) is int
        and state.get("start_time") == record.start_time
        and state.get("hermes_home") == str(home)
        and isinstance(source.get("commit"), str)
        and re.fullmatch("[0-9a-f]{40}", source["commit"]) is not None
        and state.get("code_sha") == source["commit"]
        and not runtime_status_is_stale(state)
        and updated is not None
        and datetime.fromisoformat(updated) <= datetime.now(timezone.utc),
        "native_gateway_start_not_observed",
    )
    generation = budget.call(expected_gateway, home)
    diagnostic = {}
    if identify_with_cutoff is None:
        live = budget.call(identify_gateway, home, timeout=min(5.0, budget.check()), diagnostic=diagnostic)
    else:
        cutoff = min(budget.deadline, time.monotonic() + _GATEWAY_START_IDENTIFY_SECONDS)
        live = budget.call(identify_with_cutoff, home, cutoff=cutoff, diagnostic=diagnostic)
    identity = live if isinstance(live, dict) else {}
    fields = {
        "response": isinstance(live, dict),
        "protocol": identity.get("protocol") == CONTROL_PROTOCOL_VERSION,
        "kind": identity.get("kind") == "hermes-gateway",
        "pid": type(identity.get("pid")) is int and identity.get("pid") == record.pid,
        "start_time": type(identity.get("start_time")) is int and identity.get("start_time") == record.start_time,
        "hermes_home": identity.get("hermes_home") == str(home),
        "code_sha": identity.get("code_sha") == source["commit"],
        "friday_owner": identity.get("friday_owner") == generation,
    }
    if not all(fields.values()):
        from scripts.friday_install import Refused
        exc = Refused("native_gateway_generation_unproved")
        exc.friday_identity_observation = {**diagnostic,
            "mismatch": [name for name, matched in fields.items() if not matched]}
        raise exc
    # Generation validation and the native identify exchange can outlive an
    # incarnation. Reconcile the retained native owner after that exchange.
    observed = budget.call(hr.read_record, hr.ROLE_GATEWAY, include_stale=True)
    require(observed == record, "native_gateway_owner_changed_during_probe")
    current_props = budget.call(read_properties, properties)
    require(current_props == props, "native_gateway_unit_changed_during_probe")
    require(
        budget.call(hr.liveness_is_proven, record)
        and budget.call(hr.record_token_is_consistent, record),
        "native_gateway_incarnation_changed_during_probe",
    )
    budget.check()
    return record


def load_required_plugins(budget):
    from hermes_cli.plugins import discover_plugins, get_plugin_manager
    from hermes_cli.plugins_activation import activation_summaries
    from scripts.friday_install import require

    # Native normal dashboard CLI performs the same discovery. No POST or
    # localhost role-token escalation is needed for a trusted installed plugin.
    budget.call(discover_plugins)
    summaries = budget.call(activation_summaries, get_plugin_manager())
    names = {r["name"] for r in summaries}
    require({"friday_rework", "basic", "web-exa"} <= names, "mandatory_native_plugin_activation_failed")


def dashboard_admission(value, budget):
    from hermes_cli import web_server
    from hermes_cli.friday_dashboard_owner import expected

    dash = value["product"]["dashboard"]
    budget.call(web_server._configure_auth_gate, dash["host"], True, None, None)
    return budget.call(
        expected,
        registered=True,
        auth_required=web_server.app.state.auth_required,
        host=dash["host"],
        port=dash["port"],
    )


def launch(value, budget, *, pins):
    """Finite native service handoff, then the existing foreground Dashboard.

    The native gateway unit owns its receiver. A service-command ambiguity is
    STOP_UNCONFIRMED; no automatic stop/retry or invented receipt follows it.
    Dashboard bind/attachment keeps the donor's lock/auth/nonce lifecycle.
    """
    from gateway import host_rendezvous as hr
    from hermes_cli.friday_dashboard_owner import check_attachment
    from scripts.dsh_prepare import StopUnconfirmed
    from scripts.friday_install import clean_environment, commands, require
    from scripts.install_containment import Containment

    home = Path(value["home"])
    argv = budget.call(commands, value)
    unchanged(pins, budget)
    unit, old = gateway_preflight(home, "default", budget)
    serve = budget.call(hr.read_record, hr.ROLE_SERVE, include_stale=True)
    if serve is not None:
        budget.call(check_attachment, serve)  # Actual authenticated native probe.
    budget.call(load_required_plugins, budget)
    budget.call(dashboard_admission, value, budget)
    unchanged(pins, budget)
    custody = Containment(value["containment"], budget, clean_environment(home))
    custody.probe(value["bootstrap_python"]["path"], Path(value["home"]) / "hermes-agent")
    if old is None:
        # Preflight cannot prove absence from a missing rendezvous alone. Refuse
        # a live/unresolved native unit or process before any start request.
        from hermes_cli import gateway as gw

        props = budget.call(gw._read_systemd_unit_properties, system=False)
        require(
            props.get("ActiveState") in ("inactive", "failed", "")
            and str(props.get("MainPID", "0")) == "0"
            and not budget.call(gw.find_gateway_pids),
            "gateway_start_requires_reconciliation",
        )
        unchanged(pins, budget)
        unit, current = gateway_preflight(home, "default", budget)
        require(current is None, "gateway_owner_changed_before_handoff")
        try:
            if not unit.exists():
                custody.run(argv["gateway_install"], home / "hermes-agent", timeout=30)
            unchanged(pins, budget)
            _unit, current = gateway_preflight(home, "default", budget)
            require(current is None, "gateway_owner_changed_before_handoff")
            custody.run(argv["gateway_start"], home / "hermes-agent", timeout=30)
            gateway_observation(home, budget)
        except BaseException as exc:
            raise StopUnconfirmed("native gateway handoff requires reconciliation") from exc
    else:
        gateway_observation(home, budget)  # Reattach only; never restart/replay.
    try:
        unchanged(pins, budget)
        # Native foreground ownership transfers to the operator's terminal.
        # No child, nohup, daemon, launcher replacement or readiness claim.
        env = clean_environment(home)
        require((home / "hermes-agent/.hermes/bin/hermes").is_file(), "native_dashboard_launcher_missing")
        budget.check()
        os.execve(argv["dashboard"][0], argv["dashboard"], env)
        raise RuntimeError("native_foreground_transfer_not_observed")
    except BaseException as exc:
        # The checked gateway is now a native service owner. Never label a
        # failed Dashboard handoff as cessation or silently start it again.
        raise StopUnconfirmed(
            "native gateway remains owned; dashboard handoff requires reconciliation"
        ) from exc


def start(value, budget, *, raw=None):
    # The admission reads the installed product; the launch commands revalidate
    # the original unconfigured input the installer claimed.
    _identity, pins = prerequisites(value, budget)
    launch(value if raw is None else raw, budget, pins=pins)


def _ordinary_user_bus():
    from scripts.friday_install import directory, require

    runtime = directory(Path("/run/user") / str(os.getuid()))
    bus = runtime / "bus"
    info = bus.lstat()
    require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
            "ordinary_start_owned_user_bus_required")
    return runtime, bus, info


def _ordinary_systemctl(runtime, bus):
    return ["/usr/bin/env", "XDG_RUNTIME_DIR=" + str(runtime),
            "DBUS_SESSION_BUS_ADDRESS=unix:path=" + str(bus), "SYSTEMCTL_FORCE_BUS=1",
            "LC_ALL=C", "/usr/bin/systemctl", "--user"]


class _OrdinaryTimeoutManager:
    """Use one checked local manager for effective admission, Start and observation."""

    def __init__(self, unit, source):
        from hermes_cli import gateway as gw
        from scripts.friday_install import require

        require(unit.name == gw.get_service_name() + ".service", "ordinary_start_exact_native_unit_required")
        self.unit, self.source = unit, source
        self.runtime, self.bus, info = _ordinary_user_bus()
        self.identity = self._identity(self.runtime.lstat(), info)
        self.prefix = _ordinary_systemctl(self.runtime, self.bus)

    @staticmethod
    def _identity(runtime, bus):
        return tuple((s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_nlink) for s in (runtime, bus))

    def check_bus(self):
        from scripts.friday_install import require

        runtime, bus, info = _ordinary_user_bus()
        require(runtime == self.runtime and bus == self.bus
                and self._identity(runtime.lstat(), info) == self.identity,
                "ordinary_start_owned_user_bus_required")

    def command(self, action):
        self.check_bus()
        return [*self.prefix, action, self.unit.name]

    def properties(self, custody, properties):
        from scripts.friday_install import require

        command = self.command("show")
        output, _ = custody.run([*command, "--property=" + ",".join(properties)], self.source, timeout=15)
        self.check_bus()
        rows = [line.split("=", 1) for line in output.splitlines()]
        require(len(rows) == len(properties) and all(len(row) == 2 for row in rows),
                "gateway_timeout_dropin_effective_unproved")
        result = dict(rows)
        require(set(result) == set(properties), "gateway_timeout_dropin_effective_unproved")
        return result


def ordinary_start(value, budget):
    """Ordinary receiving service only; native operator Dashboard is separate.

    Full start above retains both workers and frontend qualification. This
    scope proves current installed native bytes, local credentials and exact
    user unit before one handoff; it never executes a worker or grants a user.
    """
    from gateway import host_rendezvous as hr
    from hermes_cli import gateway as gw
    from hermes_cli.friday_ordinary_gateway import check
    from hermes_cli.friday_credential_admission import bootstrap, scoped, route_inputs, channel_inputs
    from scripts.friday_install import clean_environment, require
    from scripts.install_containment import Budget, Containment
    from scripts.dsh_prepare import StopUnconfirmed
    from hermes_constants import get_hermes_home
    from pm.paths import repo_root
    from pm.environments import project_python

    home = Path(value['home']); source = home/'hermes-agent'
    require(get_hermes_home() == home and repo_root() == source
            and Path(sys.executable) == project_python(source), 'native_start_generation_mismatch')
    check(home)
    pins = snapshot(home,budget)
    budget.call(bootstrap,home)
    with scoped(home):
        budget.call(route_inputs)
        contract,_ = budget.call(channel_inputs)
        environment = clean_environment(home)
        custody = None
        manager = None

        def process_custody():
            nonlocal custody
            if custody is None:
                custody = Containment(value["containment"], budget, environment)
            return custody

        def preflight(*, initial=False):
            nonlocal manager
            previously_approved = manager is not None
            approved = False

            def readback(unit, properties):
                nonlocal approved, manager
                if manager is None:
                    manager = _OrdinaryTimeoutManager(unit, source)
                require(manager.unit == unit, "ordinary_start_exact_native_unit_required")
                approved = True
                return manager.properties(process_custody(), properties)

            result = gateway_preflight(home, "default", budget, readback)
            require(initial or approved == previously_approved,
                    "gateway_dropin_requires_reconciliation")
            return result

        unit,old = preflight(initial=True)
        require(budget.call(gw.get_systemd_linger_status)[0] is True, 'ordinary_existing_user_linger_required')
        unchanged(pins,budget)
        if old is not None:
            if manager is None:
                gateway_observation(home,budget)
            else:
                gateway_observation(home,budget,lambda keys: manager.properties(custody, keys))
            return {'state':'ORDINARY_NATIVE_GATEWAY_ALREADY_RUNNING','ready':False,'workers_enabled':False}
        identify_with_cutoff = None
        # The entry points already matched the pinned project overlay set and
        # exported source bytes to the receipt. A selected layer requires its
        # native client before a service effect can be admitted.
        if manager is not None and _GATEWAY_START_IDENTIFY_MANIFEST in value.get("project_files", {}):
            from inspect import Parameter, signature
            from gateway import control_socket

            client = getattr(control_socket, "identify_gateway", None)
            parameter = signature(client).parameters.get("cutoff") if callable(client) else None
            require(getattr(control_socket, "__file__", None) == str(source / "gateway/control_socket.py")
                    and getattr(control_socket, "_IS_WINDOWS", None) is False
                    and parameter is not None and parameter.kind is Parameter.KEYWORD_ONLY,
                    "ordinary_start_native_identify_cutoff_required")
            identify_with_cutoff = client
        if manager is None:
            props = budget.call(gw._read_systemd_unit_properties,system=False)
        else:
            props = budget.call(manager.properties, custody, ("ActiveState", "MainPID"))
        require(props.get('ActiveState') in ('inactive','failed','') and str(props.get('MainPID','0')) == '0'
                and not budget.call(gw.find_gateway_pids), 'gateway_start_requires_reconciliation')
        launcher = source/'.hermes/bin/hermes'
        from hermes_cli._launchers import _launcher_script,resolve_store_python
        from scripts.friday_install import owned_file
        python = resolve_store_python(source,publication=True)
        require(python is not None and owned_file(launcher) == ('#!/bin/sh\nexec '+
            shlex.join([str(python),'-I','-c',_launcher_script('hermes',source,None)])+' "$@"\n').encode()
            and os.access(launcher,os.X_OK) and not launcher.stat().st_mode & 0o022,
            'native_launcher_generation_changed')
        custody = process_custody()
        custody.probe(value['bootstrap_python']['path'],source)
        _unit,current = preflight()
        require(current is None,'gateway_owner_changed_before_handoff')
        stage = 'gateway_install'
        try:
            if not unit.exists():
                custody.run([str(launcher),'-p','default','gateway','install','--no-start-now','--no-start-on-login'],source,timeout=30)
            stage = 'input_snapshot'
            unchanged(pins,budget)
            stage = 'gateway_preflight'
            _unit,current = preflight()
            stage = 'gateway_owner'
            require(current is None,'gateway_owner_changed_before_handoff')
            stage = 'user_bus'
            if manager is None:
                runtime, bus, _ = _ordinary_user_bus()
                command = [*_ordinary_systemctl(runtime, bus), "start", unit.name]
            else:
                manager.check_bus()
            stage = 'native_unit_identity'
            require(unit == _unit and unit.name == gw.get_service_name()+'.service',
                    'ordinary_start_exact_native_unit_required')
            stage = 'native_unit_start'
            if manager is None:
                custody.run(command, source, timeout=90)
            else:
                # systemd owns the service's 180s. The client also allows time
                # for job delivery and leaves room for proof in a short outer budget.
                timeout = min(_GATEWAY_START_COMMAND_SECONDS,
                              budget.check(reserve=_GATEWAY_START_PROOF_RESERVE_SECONDS))
                custody.run(manager.command("start"), source, timeout=timeout)
            stage = 'gateway_observation'
            if manager is None:
                gateway_observation(home,budget)
            else:
                now = time.monotonic()
                proof_budget = Budget(_GATEWAY_START_PROOF_SECONDS, started=now,
                    deadline=min(budget.deadline, now + _GATEWAY_START_PROOF_SECONDS))
                proof_custody = Containment(value["containment"], proof_budget, environment)
                proof_budget.call(gateway_observation, home, proof_budget,
                    lambda keys: manager.properties(proof_custody, keys),
                    identify_with_cutoff=identify_with_cutoff)
        except BaseException as exc:
            # Keep the existing uncertainty boundary and original command owner.
            # Only source-defined stage/reason and existing safe observations
            # cross the internal CLI; never exception text, argv or raw output.
            from scripts.friday_install import safe_diagnostic, remember_secondary
            stopped = StopUnconfirmed('native ordinary gateway handoff requires reconciliation')
            stopped.friday_custody_primary = exc
            stopped.friday_custody_state = 'UNCONFIRMED'
            try:
                stopped.friday_diagnostic = safe_diagnostic(exc, 'ordinary_' + stage)
            except BaseException as diagnostic_failure:
                remember_secondary(stopped, diagnostic_failure)
            raise stopped from exc
        return {'state':'ORDINARY_NATIVE_GATEWAY_OBSERVED','ready':False,'workers_enabled':False,
                'runtime_acceptance':'GENUINE_TELEGRAM_INPUT_AND_CONTEXTUAL_FOLLOWUP_REQUIRED'}
