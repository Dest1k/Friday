"""Verify an address-only Dashboard projection from a pinned installation."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path


MARKER = "FRIDAY-INSTALL.json"
PROFILE = "FRIDAY-PROFILE.json"
CONFIG = "config.yaml"
TLS_PATHS = {
    "cafile": "dashboard-tls/ca.pem",
    "certfile": "dashboard-tls/server.pem",
    "keyfile": "dashboard-tls/server.key",
}
DASHBOARD_FILES = (MARKER, PROFILE, CONFIG)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def exact_object(raw):
    def unique(pairs):
        value = {}
        for key, entry in pairs:
            require(key not in value, "Dashboard route JSON has duplicate keys")
            value[key] = entry
        return value

    result = json.loads(raw, object_pairs_hook=unique)
    require(type(result) is dict, "Dashboard route requires a JSON object")
    return result


def exact_replacement(raw, old, new, reason):
    require(raw.count(old) == 1 and old != new, reason)
    return raw.replace(old, new, 1)


def verify_route_projection(*, before_root, before_unit, after_root, after_unit,
                            previous_marker_sha256, previous_unit_sha256,
                            old_host, old_public_url, host, public_url, before_marker=None):
    """Check candidate bytes. The caller supplies independently anchored old pins and approved addresses."""
    from hermes_cli.config_effective import read_user_config_effective_readonly
    from hermes_cli.dashboard_auth.prefix import _normalise_public_url
    from hermes_cli.friday_dashboard_owner import read_owned
    from hermes_cli.friday_dashboard_tls import checked
    from hermes_cli.friday_ordinary_gateway import (
        configuration_contract,
        configuration_matches,
        normalized_configuration,
    )
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override

    require(type(public_url) is str and bool(public_url)
            and _normalise_public_url(public_url) == public_url,
            "Dashboard public URL must match its native canonical form")
    before_root, before_unit, after_root, after_unit = map(
        Path, (before_root, before_unit, after_root, after_unit))
    before_marker = before_root / MARKER if before_marker is None else Path(before_marker)
    require(all(path.is_absolute() and path.resolve(strict=True) == path
                for path in (before_root, before_unit, after_root, after_unit, before_marker))
            and before_root != after_root and before_unit != after_unit
            and before_marker != after_root / MARKER,
            "Separate canonical Dashboard route snapshots required")

    before_paths = {MARKER: before_marker, PROFILE: before_root / PROFILE, CONFIG: before_root / CONFIG}
    after_paths = {name: after_root / name for name in (*DASHBOARD_FILES, *TLS_PATHS.values())}
    before_paths["unit"] = before_unit
    after_paths["unit"] = after_unit
    before = {name: read_owned(path, private=True) for name, path in before_paths.items()}
    require(digest(before[MARKER]) == previous_marker_sha256
            and digest(before["unit"]) == previous_unit_sha256,
            "Historical Dashboard marker or unit pin changed")
    marker = exact_object(before[MARKER])
    profile = exact_object(before[PROFILE])
    require(marker.get("completion_stage") == "TELEGRAM_ORDINARY"
            and marker.get("state") == "INSTALLED_TEMPLATE_INCOMPLETE",
            "Expected ordinary Telegram installation for Dashboard route")
    phase = marker["ordinary_gateway"]
    require(set(marker["tls_files"]) == set(TLS_PATHS.values())
            and all(marker["profile_files"][name] == digest(before[name]) for name in (PROFILE, CONFIG))
            and phase["profile_sha256"] == digest(before[PROFILE])
            and phase["source_receipt_sha256"] == marker["source_receipt_sha256"],
            "Historical Dashboard profile, config, TLS or source provenance changed")
    dashboard = profile["native_dashboard"]
    require(dashboard["host"] == old_host and dashboard["public_url"] == old_public_url
            and dashboard["auth_required"] is True and dashboard["tls"] == TLS_PATHS
            and type(dashboard["port"]) is int,
            "Historical authenticated Dashboard identity changed")
    port = dashboard["port"]

    after = {name: read_owned(path, private=True) for name, path in after_paths.items()}
    require(after[CONFIG] == exact_replacement(before[CONFIG], old_public_url.encode(), public_url.encode(),
                                                "Original Dashboard URL must occur once in config"),
            "Dashboard route changes other config bytes")
    old_argv = f"dashboard --host {old_host} --port {port} --no-open".encode()
    new_argv = f"dashboard --host {host} --port {port} --no-open".encode()
    require(after["unit"] == exact_replacement(before["unit"], old_argv, new_argv,
                                                "Original Dashboard bind must occur once in unit"),
            "Dashboard route changes other unit bytes")
    expected_profile = deepcopy(profile)
    expected_profile["native_dashboard"].update(host=host, public_url=public_url)
    require(after[PROFILE] == encoded(expected_profile), "Dashboard route changes other profile fields")

    previous_cfg = read_user_config_effective_readonly(before_paths[CONFIG])
    candidate_cfg = read_user_config_effective_readonly(after_paths[CONFIG])
    require(configuration_matches(previous_cfg, phase["configuration_sha256"])
            and previous_cfg["dashboard"]["public_url"] == old_public_url
            and previous_cfg["dashboard"]["require_auth"] is True,
            "Historical Dashboard effective configuration changed")
    expected_cfg = deepcopy(previous_cfg)
    expected_cfg["dashboard"]["public_url"] = public_url
    require(candidate_cfg == expected_cfg, "Dashboard route changes other effective settings")
    token = set_hermes_home_override(str(after_root))
    try:
        native_profile = configuration_contract(candidate_cfg, phase["baseline"])
    finally:
        reset_hermes_home_override(token)
    require(native_profile == expected_profile, "Dashboard route fails the native profile contract")

    tls_pins = {name: digest(after[name]) for name in TLS_PATHS.values()}
    ca = TLS_PATHS["cafile"]
    require(tls_pins[ca] == marker["tls_files"][ca], "Dashboard native CA changed")
    tls, _context = checked(after_root, TLS_PATHS, host, port, public_url)
    require(tls["ca_sha256"] == tls_pins[ca]
            and tls["cert_sha256"] == tls_pins[TLS_PATHS["certfile"]],
            "Dashboard TLS bytes changed during verification")

    expected_marker = deepcopy(marker)
    expected_marker["profile_files"].update({name: digest(after[name]) for name in (PROFILE, CONFIG)})
    expected_marker["ordinary_gateway"]["profile_sha256"] = digest(after[PROFILE])
    expected_marker["ordinary_gateway"]["configuration_sha256"] = normalized_configuration(candidate_cfg)
    expected_marker["tls_files"] = tls_pins
    require(after[MARKER] == encoded(expected_marker), "Dashboard route changes unrelated marker fields")
    require(all(read_owned(path, private=True) == before[name] for name, path in before_paths.items())
            and all(read_owned(path, private=True) == after[name] for name, path in after_paths.items()),
            "Dashboard route snapshots changed during verification")
    return {
        "state": "DASHBOARD_ADDRESS_ONLY_PROJECTION_VERIFIED",
        "source_receipt_sha256": marker["source_receipt_sha256"],
        "previous": {name: digest(raw) for name, raw in before.items()},
        "current": {name: digest(raw) for name, raw in after.items()},
        "tls": tls,
        "native_configuration_sha256": expected_marker["ordinary_gateway"]["configuration_sha256"],
        "publication_authorized": False,
    }
