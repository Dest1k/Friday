"""Authority and state custody for the local D02 receiver control.

The authenticated caller supplies the protected run/owner and immutable
rights pins. This module opens no receiver window and has no socket handler.
Use the returned buffer internally for receipt matching, never in RPC output.
"""

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
import time


PIN_FIELDS = {"root_config", "profile_config", "scope_marker", "source_receipt"}
ROUTE_FIELDS = {"platform", "transport_profile", "account_id", "user_id", "enabled", "role", "generation"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest_string(value):
    return type(value) is str and re.fullmatch("[a-f0-9]{64}", value) is not None


def _signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _file_pin(path, expected):
    _require(path.is_absolute() and path.resolve(strict=True) == path, "d02_current_path_changed")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC), "rb") as stream:
        first = os.fstat(stream.fileno())
        _require(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid() and first.st_nlink == 1
                 and not stat.S_IMODE(first.st_mode) & 0o022 and 0 < first.st_size <= 8_388_608,
                 "d02_current_file_custody")
        value = stream.read(first.st_size + 1)
        last = os.fstat(stream.fileno())
    _require(len(value) == first.st_size and _signature(first) == _signature(last)
             == _signature(path.lstat()) and sha256(value).hexdigest() == expected,
             "d02_current_file_changed")
    return _signature(last)


def _route_allowed(access, user, profile):
    policy = access.access_policy()
    if policy is None:
        return False
    accounts = [row for row in policy["accounts"] if
                row["platform"] == user["platform"] and row["transport_profile"] == user["transport_profile"]]
    return (len(accounts) == 1 and accounts[0]["account_id"] == user["account_id"]
            and profile in accounts[0]["runtime_profiles"])


def _read_bound_state(state, home, expected, *, pre_dispatch, deadline):
    directory = state.directory_storage_readonly
    _require(directory == home / "plugin-data" / "agent-plugin-friday_rework-877e6505"
             and directory.resolve(strict=True) == directory, "d02_private_state_scope_changed")
    path = directory / "state.json"
    before = _signature(path.lstat())
    data, observed = state._read_storage_readonly(lock_deadline=deadline, with_identity=True, strict_json=True)
    _require(tuple(observed["inode"]) == before[:2] and _signature(path.lstat()) == before,
             "d02_state_changed_during_authority_observation")
    _require(all(list(observed[key]) == expected[key] for key in ("directory", "lock_inode")),
             "d02_current_state_namespace_changed")
    if pre_dispatch:
        _require(list(observed["inode"]) == expected["inode"] and observed["sha256"] == expected["sha256"],
                 "d02_predispatch_state_cas_changed")
    return data, observed, path, before


def _namespace_current(state_path, observed):
    directory = state_path.parent
    lock = directory / ".state.json.lock"
    current, lock_stat = directory.lstat(), lock.lstat()
    return (directory.resolve(strict=True) == directory
            and stat.S_ISDIR(current.st_mode) and stat.S_IMODE(current.st_mode) == 0o700
            and current.st_uid == os.getuid() and (current.st_dev, current.st_ino) == tuple(observed["directory"])
            and stat.S_ISREG(lock_stat.st_mode) and stat.S_IMODE(lock_stat.st_mode) == 0o600
            and lock_stat.st_uid == os.getuid() and lock_stat.st_nlink == 1
            and (lock_stat.st_dev, lock_stat.st_ino) == tuple(observed["lock_inode"]))


def _state_pin(expected):
    _require(type(expected) is dict and set(expected) == {"directory", "lock_inode", "inode", "sha256"}
             and _digest_string(expected["sha256"]), "d02_exact_state_pin_required")
    for key in ("directory", "lock_inode", "inode"):
        identity = expected[key]
        _require(type(identity) is list and len(identity) == 2
                 and all(type(part) is int and part >= 0 for part in identity), "d02_exact_state_identity_required")


def check_receiver_state(home, *, profile, expected_principal, rights, state, access, scope, pairing, phase, deadline):
    """Validate current rights and return the locked routed receipt buffer.

    Arm and dispatch compare the original whole-file pins of both stores.
    After dispatch the original policy, pairing, exact selected access row
    and both namespaces still apply. The routed writer's new inode is allowed
    there. The caller owns boot, original claim, route and exact receipt proof.
    """
    _require(phase in ("arm", "dispatch", "post_dispatch"), "d02_exact_authority_phase_required")
    _require(type(deadline) in (int, float) and math.isfinite(deadline) and time.monotonic() < deadline,
             "d02_current_rights_observation_expired")
    _require(type(expected_principal) is dict and set(expected_principal) == ROUTE_FIELDS
             and expected_principal["platform"] == "telegram" and expected_principal["enabled"] is True
             and expected_principal["role"] == "user" and type(expected_principal["generation"]) is int
             and expected_principal["generation"] > 0
             and all(type(expected_principal[name]) is str and re.fullmatch("[1-9][0-9]{0,19}", expected_principal[name])
                     for name in ("account_id", "user_id"))
             and type(profile) is str and profile == "telegram-bot-" + expected_principal["user_id"],
             "d02_current_ordinary_principal_required")
    state_fields = {"authorization_state", "routed_state"}
    _require(type(rights) is dict and set(rights) == PIN_FIELDS | state_fields | {"isolation_binding_sha256", "active_pairing"}
             and all(_digest_string(rights[name]) for name in PIN_FIELDS | {"isolation_binding_sha256"})
             and rights["active_pairing"] in ("platforms/pairing/telegram-approved.json", "pairing/telegram-approved.json"),
             "d02_exact_current_rights_pins_required")
    for scope_name in state_fields:
        _state_pin(rights[scope_name])

    home = Path(home)
    selected_profile = home / "profiles" / profile
    paths = {"root_config": home / "config.yaml",
             "profile_config": selected_profile / "config.yaml",
             "scope_marker": selected_profile / ".friday-user-scope.json",
             "source_receipt": home / "hermes-agent.source.json"}
    static = {name: _file_pin(path, rights[name]) for name, path in paths.items()}
    principal_fields = ("platform", "transport_profile", "account_id", "user_id")
    principal = tuple(expected_principal[key] for key in principal_fields)
    pre_dispatch = phase != "post_dispatch"

    with scope.authority(home):
        _require(_route_allowed(access, expected_principal, profile), "d02_current_account_policy_changed")
        active = pairing.get_hermes_dir("platforms/pairing", "pairing", home=home) / "telegram-approved.json"
        _require(active == home / rights["active_pairing"], "d02_active_pairing_layout_changed")
        active_before = _signature(active.lstat())
        approvals = pairing._approved_json_storage_readonly(active, home)
        _require(bool(pairing._matching_ids("telegram", approvals, expected_principal["user_id"])),
                 "d02_current_receiving_pairing_required")
        check = scope.policy(home)
        bindings = [] if check is None else [row for row in check["bindings"]
                    if tuple(row[name] for name in principal_fields) == principal]
        _require(len(bindings) == 1 and bindings[0]["runtime_profile"] == profile
                 and "read_file" in bindings[0]["tools"]
                 and sha256((json.dumps(bindings[0], sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()).hexdigest()
                     == rights["isolation_binding_sha256"],
                 "d02_current_user_scope_changed")
        auth, auth_observed, auth_path, auth_before = _read_bound_state(state, home, rights["authorization_state"],
                                                 pre_dispatch=pre_dispatch, deadline=deadline)
        key = access.principal_id(*principal)
        _require(access.validate_access(auth[access.KEY])["users"].get(key) == expected_principal,
                 "d02_current_principal_rights_changed")

    with scope.authority(selected_profile):
        data, routed, routed_path, routed_before = _read_bound_state(state, selected_profile, rights["routed_state"],
                                         pre_dispatch=pre_dispatch, deadline=deadline)

    _require(auth_observed["directory"] != routed["directory"]
             and _namespace_current(auth_path, auth_observed) and _namespace_current(routed_path, routed)
             and pairing.get_hermes_dir("platforms/pairing", "pairing", home=home) / "telegram-approved.json" == active
             and _signature(active.lstat()) == active_before
             and _signature(auth_path.lstat()) == auth_before and _signature(routed_path.lstat()) == routed_before
             and all(path.resolve(strict=True) == path and _signature(path.lstat()) == static[name]
                     for name, path in paths.items()) and time.monotonic() < deadline,
             "d02_current_rights_observation_expired_or_changed")
    return data, {"authorization": auth_observed, "routed": routed}
