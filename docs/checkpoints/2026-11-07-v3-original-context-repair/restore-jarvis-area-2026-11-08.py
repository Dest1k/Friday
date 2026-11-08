#!/usr/bin/env python3
"""Restore the user areas (Jarvis + owner) in the installed Friday home.

Standard product writers only; no hand-written store files.
Stage order: config -> homes -> data -> pairing -> access -> verify.

The onboarding transaction (plugins/friday_rework/onboarding.py) requires a verified
Dashboard operator Session; the only configured provider is `basic` and its password is
stored solely as a scrypt hash, so no Session can be minted here. This script therefore
uses the product's own primitives with the same runtime checks:
  * hermes_cli.friday_product_access / friday_user_scope.policy() for policy shape
  * friday_user_scope.provision_new_home() for the private home + capability marker
    (legacy contract: marker without a digest-bound onboarding receipt)
  * gateway.pairing.PairingStore for the native grant
  * plugins/friday_rework/admin.Administration.set_user() for product access
    (which enforces _require_complete_onboarding)

Run with HERMES_HOME set to the installed home. Prints non-secret JSON summaries only.
"""
import copy
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
OLD = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
os.environ["HERMES_HOME"] = str(HOME)
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME))
sys.path.insert(0, str(HOME / "plugins"))
sys.dont_write_bytecode = True

from hermes_cli import config as native  # noqa: E402
from hermes_cli import friday_user_scope as scope  # noqa: E402
from hermes_cli.friday_product_access import principal_id, settings  # noqa: E402

ACCOUNT = "8751854128"
TRANSPORT = "default"

OWNER = dict(
    platform="telegram", transport_profile=TRANSPORT, account_id=ACCOUNT,
    user_id="467035772", runtime_profile="dest_telegram",
    tools=["browser_back", "browser_click", "browser_navigate", "browser_press",
           "browser_scroll", "browser_snapshot", "browser_type", "delegate_task",
           "friday_result", "friday_work", "memory", "read_file", "session_search",
           "skill_manage", "skill_view", "skills_list", "web_extract", "web_search",
           "write_file"])
JARVIS = dict(
    platform="telegram", transport_profile=TRANSPORT, account_id=ACCOUNT,
    user_id="8812646969", runtime_profile="telegram-bot-8812646969",
    tools=["delegate_task", "friday_result", "friday_work", "memory", "read_file",
           "session_search", "skill_manage", "skill_view", "skills_list",
           "web_extract", "web_search", "write_file"])
BINDINGS = [OWNER, JARVIS]
TEMPLATE = "friday-local"
COPY_TREES = ["workspace", "memories", "skills", "cron"]


def log(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False))


def cfg_path():
    return HOME / "config.yaml"


def digest(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stage_config():
    path = cfg_path()
    before = digest(path)
    raw = native.require_readable_config_before_write(path)
    cfg = copy.deepcopy(raw)
    block = cfg["plugins"]["entries"]["friday_rework"]["settings"]
    block["user_isolation"] = {"enabled": True, "bindings": [copy.deepcopy(b) for b in BINDINGS]}
    account = block["product_access"]["accounts"][0]
    if (account["platform"], account["transport_profile"], account["account_id"]) != (
            "telegram", TRANSPORT, ACCOUNT):
        raise SystemExit("unexpected product account row")
    for binding in BINDINGS:
        if binding["runtime_profile"] not in account["runtime_profiles"]:
            account["runtime_profiles"].append(binding["runtime_profile"])
        if binding["runtime_profile"] not in block["admin"]["profiles"]:
            block["admin"]["profiles"].append(binding["runtime_profile"])
    gateway = cfg.setdefault("gateway", {})
    if gateway.get("multiplex_profiles") is not True:
        raise SystemExit("native_multiplex_installation_required")
    routes = gateway.setdefault("profile_routes", [])
    for binding in BINDINGS:
        key = principal_id(binding["platform"], binding["transport_profile"],
                           binding["account_id"], binding["user_id"])
        row = {"name": "friday-" + key, "platform": binding["platform"],
               "bot_profile": binding["transport_profile"], "user_id": binding["user_id"],
               "profile": binding["runtime_profile"], "enabled": True}
        if not [r for r in routes if r == row]:
            routes.append(row)
    with native.config_write_transaction(path):
        if digest(path) != before:
            raise SystemExit("config changed underneath this writer; reload required")
        native.atomic_config_write(path, cfg)
    policy = scope.policy(HOME)
    log(stage="config", sha256=digest(path), before_sha256=before,
        bindings=len(policy["bindings"]),
        profiles=[b["runtime_profile"] for b in policy["bindings"]],
        accounts=settings()["product_access"]["accounts"][0]["runtime_profiles"],
        admin_profiles=settings()["admin"]["profiles"],
        routes=len(settings_routes()))


def settings_routes():
    with scope.authority(HOME):
        return native.load_config_readonly().get("gateway", {}).get("profile_routes", [])


def stage_homes():
    template = settings()["onboarding"]["templates"][TEMPLATE]
    native_config = copy.deepcopy(template["config"])
    if native_config.get("plugins", {}).get("entries", {}).get("friday_rework", {}) \
            .get("settings", {}).get("runtime", {}).get("enabled") is True:
        raise SystemExit("template enables worker runtime; not a fresh-profile state")
    soul = (HOME / "plugins/friday_rework/SOUL.md").read_bytes()
    import hashlib
    soul_sha = hashlib.sha256(soul).hexdigest()
    for binding in BINDINGS:
        home = HOME / "profiles" / binding["runtime_profile"]
        if not (home / scope.MARKER).exists():
            home = scope.provision_new_home(HOME, binding, {}, publish=True)
        marker = json.loads((home / scope.MARKER).read_text())
        expected = {"schema": "friday.user-home.v1",
                    "principal": principal_id(binding["platform"], binding["transport_profile"],
                                              binding["account_id"], binding["user_id"]),
                    "profile": binding["runtime_profile"],
                    "binding_sha256": scope._fingerprint(binding)}
        if marker != expected:
            raise SystemExit("marker mismatch for " + binding["runtime_profile"])
        profile_config = copy.deepcopy(native_config)
        profile_config["terminal"] = {"cwd": str(home / "workspace")}
        if "worker_inputs" in template:
            profile_config["plugins"]["entries"]["friday_rework"]["settings"][
                "worker_requirements"] = ["dsh", "a0"]
        with scope.authority(home), native.config_write_transaction(home / "config.yaml"):
            native.atomic_config_write(home / "config.yaml", profile_config)
        (home / "SOUL.md").write_bytes(soul)
        write_secrets(home, binding["runtime_profile"], template["required_secrets"])
        st = home.stat()
        log(stage="home", profile=binding["runtime_profile"], marker=marker["schema"],
            binding_sha256=marker["binding_sha256"], soul_sha256=soul_sha,
            config_sha256=digest(home / "config.yaml"),
            directory_identity=[st.st_dev, st.st_ino],
            onboarding_receipt=(home / scope.ONBOARDING).exists())


def write_secrets(home, profile, names):
    target = home / ".env"
    if target.exists():
        return
    source = OLD / "profiles" / profile / ".env"
    values = {}
    for line in source.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    missing = [n for n in names if not values.get(n)]
    if missing:
        raise SystemExit("missing profile secrets in source .env")
    payload = "".join(f"{n}={values[n]}\n" for n in names)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def stage_data():
    for binding in BINDINGS:
        profile = binding["runtime_profile"]
        source = OLD / "profiles" / profile
        home = HOME / "profiles" / profile
        if not (home / scope.MARKER).exists():
            raise SystemExit("home missing for " + profile)
        copied = []
        db = source / "state.db"
        if db.is_file() and not (home / "state.db").exists():
            shutil.copy2(db, home / "state.db")
            copied.append("state.db")
        for name in COPY_TREES:
            src, dst = source / name, home / name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=False)
                copied.append(name)
        log(stage="data", profile=profile, copied=copied,
            state_db_bytes=(home / "state.db").stat().st_size if (home / "state.db").is_file() else 0,
            workspace_files=sum(1 for _ in (home / "workspace").rglob("*")) if (home / "workspace").is_dir() else 0)


def stage_pairing():
    from gateway.pairing import PairingStore
    store = PairingStore()
    result = {}
    for binding in BINDINGS:
        user_id = binding["user_id"]
        if not store.is_approved("telegram", user_id):
            code = store.generate_code("telegram", user_id,
                                       "Jarvis" if user_id == "8812646969" else "Rinat")
            if code is None:
                raise SystemExit("pairing code refused (rate limited or capacity)")
            pending = [p for p in store.list_pending("telegram") if p["user_id"] == user_id]
            if not pending:
                raise SystemExit("pairing request not published")
            approved = store.approve_request("telegram", pending[-1]["request_id"])
            if not approved:
                raise SystemExit("pairing request not approved")
        result[user_id] = PairingStore().is_approved("telegram", user_id)
    log(stage="pairing", approved=result, store_dir=str(store._dir))


def stage_access():
    import importlib
    admin_mod = importlib.import_module("friday_rework.admin")
    from hermes_cli.friday_product_access import current_access
    admin = admin_mod.Administration()
    out = {}
    for binding in BINDINGS:
        result = admin.set_user(TRANSPORT, platform=binding["platform"],
                                transport_profile=binding["transport_profile"],
                                account_id=binding["account_id"], user_id=binding["user_id"],
                                enabled=True, role="user")
        out[binding["user_id"]] = {"recorded": result["recorded"],
                                   "generation": result["user"].get("generation")}
    rows = current_access()["users"]
    log(stage="access", written=out, rows=len(rows),
        enabled={k.split(":")[0][:8]: v["enabled"] for k, v in rows.items()})


def stage_verify():
    from hermes_cli.friday_product_access import current_access, access_policy
    from gateway.pairing import PairingStore
    policy = scope.policy(HOME)
    access = current_access()["users"]
    store = PairingStore()
    report = {"policy_bindings": len(policy["bindings"]), "access_rows": len(access),
              "account_runtime_profiles": access_policy()["accounts"][0]["runtime_profiles"],
              "admin_profiles": settings()["admin"]["profiles"], "users": {}}
    for binding in BINDINGS:
        key = principal_id(binding["platform"], binding["transport_profile"],
                           binding["account_id"], binding["user_id"])
        home = HOME / "profiles" / binding["runtime_profile"]
        marker = json.loads((home / scope.MARKER).read_text())
        report["users"][binding["runtime_profile"]] = {
            "principal_matches": key == marker["principal"],
            "binding_matches": scope._fingerprint(binding) == marker["binding_sha256"],
            "receipt": (home / scope.ONBOARDING).exists(),
            "access_enabled": bool(access.get(key, {}).get("enabled")),
            "generation": access.get(key, {}).get("generation"),
            "pairing": store.is_approved(binding["platform"], binding["user_id"]),
            "home": str(home),
            "state_db": (home / "state.db").is_file(),
            "config": (home / "config.yaml").is_file(),
            "env": (home / ".env").is_file(),
            "workspace": (home / "workspace").is_dir(),
        }
    routes = {r["user_id"]: r["profile"] for r in settings_routes()}
    report["routes"] = routes
    log(stage="verify", **report)


STAGES = {"config": stage_config, "homes": stage_homes, "data": stage_data,
          "pairing": stage_pairing, "access": stage_access, "verify": stage_verify}

if __name__ == "__main__":
    for name in sys.argv[1:]:
        STAGES[name]()
