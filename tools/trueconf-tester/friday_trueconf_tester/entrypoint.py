"""Explicit configuration and lifetime for the separate TrueConf Tester."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import re
import ssl
import stat
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from .observer import (
    DirectRoute,
    resume_observation,
    run_once,
    stock,
    valid_id,
    validate_plan,
)
from .trueconf.trueconf_client import TrueConfClient, TrueConfError
from .trueconf.trueconf_files import FileTransferError, file_origin

_CONFIG_SCHEMA = "friday.trueconf-tester.entry.v1"
_CREDENTIAL_SCHEMA = "friday.trueconf-tester.credentials.v1"
_CONFIG_FIELDS = {
    "schema", "enabled", "origin", "tester_user_id", "product_user_id", "chat_id",
    "credentials_file", "ca_file", "state_dir", "plan_file", "observation_seconds",
}
_CREDENTIAL_FIELDS = {"schema", "origin", "tester_user_id", "username", "password"}
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class EntryRefused(Exception):
    """A sanitized startup refusal."""


@dataclass(frozen=True, slots=True)
class Setup:
    enabled: bool
    route: DirectRoute
    root: Path
    config_file: Path
    credentials_file: Path
    ca_file: Path | None
    state_dir: Path
    plan_file: Path
    windows: tuple[float, float]


@dataclass(frozen=True, slots=True)
class Credentials:
    username: str = field(repr=False)
    password: str = field(repr=False)


def _directory(path: Path) -> Path:
    path = stock.no_symlinks(path)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise EntryRefused("tester_directory_unprotected")
    return path


def _file(path: Path) -> Path:
    path = stock.no_symlinks(path)
    info = path.stat()
    if (
        not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
        or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise EntryRefused("tester_file_unprotected")
    return path


def _json(path: Path, cap: int) -> dict:
    try:
        obj = json.loads(stock.safe_read(path, cap), object_pairs_hook=stock.unique_object)
    except (OSError, ValueError, RecursionError, stock.Refused):
        raise EntryRefused("tester_json_unavailable") from None
    if not isinstance(obj, dict):
        raise EntryRefused("tester_json_shape")
    return obj


def _leaf(root: Path, value: object) -> Path:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise EntryRefused("tester_relative_leaf_required")
    return root / value


def _principal(identity: object) -> str:
    if not isinstance(identity, str) or not valid_id(identity):
        raise EntryRefused("invalid_trueconf_identity")
    base = identity.split("/", 1)[0]
    local, sep, realm = base.partition("@")
    if not sep or not local or not realm or "@" in realm:
        raise EntryRefused("invalid_trueconf_identity")
    return base.casefold()


def load_config(config_path: str | os.PathLike[str]) -> Setup:
    """Read the explicit local configuration without opening credentials or a socket."""
    config = Path(config_path).absolute()
    if config != Path(os.path.abspath(config)):
        raise EntryRefused("tester_config_path_not_normalized")
    try:
        root = _directory(config.parent)
        config = _file(root / config.name)
    except (OSError, ValueError, stock.Refused):
        raise EntryRefused("tester_config_unavailable") from None
    data = _json(config, 32 * 1024)
    if set(data) != _CONFIG_FIELDS or data["schema"] != _CONFIG_SCHEMA or type(data["enabled"]) is not bool:
        raise EntryRefused("tester_config_shape")
    try:
        origin, (scheme, _, _) = file_origin(data["origin"])
    except FileTransferError:
        raise EntryRefused("tester_origin_invalid") from None
    if scheme != "https" or origin != data["origin"]:
        raise EntryRefused("canonical_https_origin_required")
    tester_id, product_id, chat_id = data["tester_user_id"], data["product_user_id"], data["chat_id"]
    if _principal(tester_id) == _principal(product_id):
        raise EntryRefused("separate_tester_account_required")
    if not valid_id(chat_id):
        raise EntryRefused("tester_chat_id_invalid")
    windows = data["observation_seconds"]
    if (
        not isinstance(windows, list) or len(windows) != 2
        or any(type(t) not in (int, float) or not 0 < t <= 600 or not math.isfinite(t) for t in windows)
    ):
        raise EntryRefused("tester_windows_invalid")
    credential = _leaf(root, data["credentials_file"])
    ca = None if data["ca_file"] is None else _leaf(root, data["ca_file"])
    state = _leaf(root, data["state_dir"])
    plan = _leaf(root, data["plan_file"])
    paths = [config, credential, state, plan]
    if ca is not None:
        paths.append(ca)
    if len(paths) != len(set(paths)):
        raise EntryRefused("tester_paths_overlap")
    return Setup(data["enabled"], DirectRoute(origin, tester_id, product_id, chat_id), root, config,
                 credential, ca, state, plan, (windows[0], windows[1]))


def _local_inputs(setup: Setup, *, input_required: bool) -> tuple[dict, ssl.SSLContext]:
    plan = _json(setup.plan_file, stock.MAX_JSON)
    try:
        validate_plan(plan, setup.route, setup.route, setup.windows)
        source = Path(plan["steps"][0]["input"]["path"])
        if not source.is_absolute() or source != Path(os.path.abspath(source)):
            raise EntryRefused("tester_document_absolute_path_required")
        source.relative_to(setup.root)
        reserved = {setup.config_file, setup.credentials_file, setup.ca_file, setup.plan_file}
        if source in reserved or source == setup.state_dir or setup.state_dir in source.parents:
            raise EntryRefused("tester_document_scope_invalid")
        if input_required:
            _file(source)
            cutoff = time.monotonic() + 15

            def guard():
                if time.monotonic() >= cutoff:
                    raise EntryRefused("tester_document_preflight_expired")

            stock.read_document_input(plan["steps"][0]["input"], guard)
        if setup.ca_file is None:
            context = ssl.create_default_context()
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            pem = stock.safe_read(setup.ca_file, 1024 * 1024).decode("ascii")
            context.load_verify_locations(cadata=pem)
        if os.path.lexists(setup.state_dir):
            _directory(setup.state_dir)
        _file(setup.credentials_file)
    except (OSError, ValueError, KeyError, TypeError, stock.Refused):
        raise EntryRefused("tester_local_setup_invalid") from None
    return plan, context


def _credentials(setup: Setup) -> Credentials:
    data = _json(setup.credentials_file, 16 * 1024)
    if (
        set(data) != _CREDENTIAL_FIELDS or data["schema"] != _CREDENTIAL_SCHEMA
        or data["origin"] != setup.route.server or data["tester_user_id"] != setup.route.tester_user_id
    ):
        raise EntryRefused("tester_credential_binding_invalid")
    username, password = data["username"], data["password"]
    if (
        not isinstance(username, str) or not 0 < len(username) <= 1024
        or not isinstance(password, str) or not 0 < len(password) <= 4096
        or "\0" in username or "\0" in password
    ):
        raise EntryRefused("tester_credential_shape_invalid")
    return Credentials(username, password)


def _operation_boundary(setup: Setup, mode: str) -> None:
    path = setup.state_dir / "runs" / "trueconf-direct-document.json"
    try:
        stock.no_symlinks(path)
    except stock.Refused:
        raise EntryRefused("tester_journal_scope_invalid") from None
    if mode == "fresh" and (os.path.lexists(path) or os.path.lexists(path.with_name(path.name + ".new"))):
        raise EntryRefused("tester_fresh_run_already_recorded")
    if mode == "resume":
        try:
            _directory(path.parent)
            _file(path)
        except (OSError, ValueError, stock.Refused):
            raise EntryRefused("tester_resume_receipt_missing") from None


async def execute(mode: str, config_path: str | os.PathLike[str]) -> dict:
    """Run one explicit Tester operation with local setup and closed session ownership."""
    if mode not in ("check", "fresh", "resume"):
        raise EntryRefused("explicit_tester_operation_required")
    setup = load_config(config_path)
    if not setup.enabled:
        if mode == "check":
            return {"state": "DISABLED", "core_credit": 0}
        raise EntryRefused("tester_disabled")
    plan, tls = _local_inputs(setup, input_required=mode != "resume")
    if mode == "check":
        return {"state": "READY", "core_credit": 0}
    _operation_boundary(setup, mode)
    credentials = _credentials(setup)
    store = stock.Store(setup.state_dir)
    route = setup.route
    client = TrueConfClient(
        route.server,
        username=credentials.username,
        password=credentials.password,
        expected_user_id=route.tester_user_id,
        durable_ingress=True,
        ssl_context=tls,
    )
    try:
        if mode == "resume":
            return await resume_observation(client, store, route, route, plan, setup.windows)
        async with asyncio.timeout(15):
            await client.connect()
        return await run_once(client, store, route, route, plan, setup.windows)
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explicit operation for the separate TrueConf Tester")
    parser.add_argument("mode", choices=("check", "fresh", "resume"))
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(execute(args.mode, args.config))
    except KeyboardInterrupt:
        return 130
    except EntryRefused as exc:
        print(json.dumps({"state": "REFUSED", "reason": str(exc)}), file=sys.stderr)
        return 2
    except stock.Refused:
        print(json.dumps({"state": "REFUSED", "reason": "tester_observer_refused"}), file=sys.stderr)
        return 2
    except (TrueConfError, TimeoutError, OSError, ValueError):
        print(json.dumps({"state": "HELD", "reason": "tester_operation_unavailable"}), file=sys.stderr)
        return 3
    state = result["state"]
    print(json.dumps({"state": state, "core_credit": result.get("core_credit", 0)}))
    if state in ("DISABLED", "READY", "MATCHED_LOCAL_OBSERVATION"):
        return 0
    return 4 if state == "UNKNOWN" else 3
