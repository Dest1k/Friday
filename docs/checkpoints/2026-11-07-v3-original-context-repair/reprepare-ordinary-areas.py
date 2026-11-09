#!/usr/bin/env python3
"""Re-prepare the two user areas from the ordinary (worker-free) template.

The product's prepare() refuses a principal that already has an access row
(existing_principal_not_adopted) and a profile home that already exists
(existing_home_not_adopted). It is a path for a NEW principal, not a path for a repeated
preparation of an existing one.

This script therefore does NOT move the profile first and hope that prepare() accepts
it. The order is:

1. the PRECONDITIONS are checked while everything is still in place: the access row of
   the principal, the existence of the profile home, the archive target and the
   product's own admission checks. A failed precondition is a refusal BEFORE any data
   changes, so the working areas are never touched.
2. only then the profile home is moved into the archive of THIS transfer, and the
   product's prepare() runs.
3. if prepare() (or a later step of the preparation) refuses, the profile home is moved
   BACK to its previous place, so the area stays exactly as it was. The refusal is then
   reported with the restoration proven by the bytes.

The access store is never emptied, the user, the binding and the access history are
never deleted to get around the refusal, and an archive is never deleted: a second
transfer of the same profile gets its own directory, and a name collision is a refusal
before any data changes.

This script is NOT executed against the serving home by the current work: the areas are
already prepared and working, and a repeated preparation is not needed for it.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
CREDS = Path("/home/jericho/jericho/frw_admin.txt")
ACCOUNT = "8751854128"
TRANSPORT = "default"
TEMPLATE = "friday-ordinary-local"
AREAS = [("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram")]
TRANSFER = "transfer-01"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
sys.path.insert(0, "/home/jericho/jericho/Friday_rework")
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def clean():
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def access_rows(state):
    from hermes_cli.friday_product_access import current_access
    return current_access(state)["users"]


def tree_digest(root):
    """A digest of the bytes and the modes of a directory tree."""
    parts = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink():
            info = path.lstat()
            parts.append((str(path.relative_to(root)), oct(info.st_mode & 0o7777),
                          hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest(), len(parts)


def preconditions(user_id, profile, state):
    """Everything that must hold BEFORE the profile is moved anywhere.

    A failed precondition is a refusal while the working area is still in place.
    """
    from hermes_cli.friday_product_access import KEY, principal_id
    checks = {}
    rows = access_rows(state)
    key = principal_id("telegram", TRANSPORT, ACCOUNT, user_id)
    row = rows.get(key)
    checks["principal_has_an_access_row"] = row is not None
    checks["principal_generation"] = (row or {}).get("generation")
    home = HOME / "profiles" / profile
    checks["profile_home_exists"] = home.exists()
    archive_root = HOME / "worker-setup-archive"
    target = archive_root / TRANSFER / profile
    checks["archive_target_free"] = not target.exists()
    checks["archive_root"] = str(archive_root)
    checks["archive_target"] = str(target)
    # The product's prepare() refuses a principal that already has an access row and a
    # home that already exists. A repeated preparation is therefore NOT available through
    # prepare(): the product has no such path, and this script must not delete the access
    # row, the binding or the history to get past the refusal.
    checks["prepare_would_refuse_existing_principal"] = row is not None
    checks["prepare_would_refuse_existing_home"] = home.exists()
    checks["repeated_preparation_available_in_the_product"] = False
    return checks


def restore_profile(home, target):
    """Move the profile back to its previous place after a refusal.

    The refusal may have happened AFTER the product created a new home for the profile, so
    the new home is moved aside and the previous profile is put back. The new home is kept
    in the archive of this transfer, never destroyed, so nothing is lost.
    """
    if not target.exists():
        return False
    home.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if home.exists() or home.is_symlink():
        aside = target.with_name(target.name + ".replaced-by-preparation")
        if aside.exists():
            return False
        shutil.move(str(home), str(aside))
        say(stage="new_home_moved_aside", home=str(home), aside=str(aside))
    shutil.move(str(target), str(home))
    return True


def main():
    clean()
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    clean()
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    import importlib
    from hermes_cli.dashboard_auth.registry import get_provider
    from hermes_cli.friday_product_access import KEY, principal_id
    from hermes_cli.plugins_state import PluginState

    raw = Path(CREDS).read_text(errors="replace")
    username = re.search(r'"username"\s*:\s*"([^"]*)"', raw).group(1)
    password = re.search(r'"password"\s*:\s*"([^"]*)"', raw).group(1)
    provider = get_provider("basic")
    session = provider.complete_password_login(username=username, password=password)
    if session.user_id != username:
        raise SystemExit("session identity mismatch")

    admin_mod = importlib.import_module("friday_rework.admin")
    onb_mod = importlib.import_module("friday_rework.onboarding")
    from agent.secret_scope import load_env_file
    admin = admin_mod.Administration()
    onboarding = onb_mod.Onboarding(admin)

    state = PluginState("friday_rework")
    rows = access_rows(state)
    say(stage="access_before", users=sorted(rows),
        note="the access store keeps its tombstones and generations; it is not emptied")

    # ---- step 1: the preconditions, while every area is still in place
    blocked = []
    for user_id, profile in AREAS:
        checks = preconditions(user_id, profile, state)
        say(stage="preconditions", user_id=user_id, profile=profile, **checks)
        if not checks["profile_home_exists"]:
            blocked.append((user_id, profile, "the profile home does not exist"))
        if not checks["archive_target_free"]:
            blocked.append((user_id, profile, "the archive target of this transfer already exists"))
        if not checks["principal_has_an_access_row"]:
            blocked.append((user_id, profile, "the principal has no access row"))
        # The product's prepare() refuses an existing principal and an existing home, and
        # the product has no repeated-preparation path. Predicting that refusal HERE means
        # the profile is not moved at all, instead of being moved and then refused.
        if checks["prepare_would_refuse_existing_principal"] and checks["profile_home_exists"]:
            blocked.append((user_id, profile,
                            "the product's prepare() refuses an existing principal "
                            "(existing_principal_not_adopted) and an existing home "
                            "(existing_home_not_adopted); there is no repeated-preparation "
                            "path in the installed product, so the profile must not be moved"))
    if blocked:
        for user_id, profile, reason in blocked:
            say(stage="refused_before_any_change", user_id=user_id, profile=profile, reason=reason)
        raise SystemExit("preconditions failed; no profile was moved and no data changed")

    for user_id, profile in AREAS:
        home = HOME / "profiles" / profile
        archive_root = HOME / "worker-setup-archive"
        archive_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = archive_root / TRANSFER / profile
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        before_digest, before_count = tree_digest(home)
        shutil.move(str(home), str(target))
        say(stage="moved_to_archive", profile=profile, transfer=TRANSFER, target=str(target),
            files_before=before_count, digest_before=before_digest)
        try:
            plan = onboarding.templates(TRANSPORT, session=session)
            digest = plan["config_sha256"]
            result = onboarding.prepare(
                TRANSPORT, session=session, expected_config_sha256=digest, template=TEMPLATE,
                platform="telegram", transport_profile=TRANSPORT, account_id=ACCOUNT,
                user_id=user_id, runtime_profile=profile)
            say(stage="prepare", user_id=user_id, profile=profile, state=result["state"],
                enabled=result["enabled"], generation=result["generation"],
                binding_sha256=result["binding_sha256"])
            plan = onboarding.templates(TRANSPORT, session=session)
            digest = plan["config_sha256"]
            values = load_env_file(HOME / ".env")
            for name in result["required_names"]:
                outcome = onboarding.credentials(
                    TRANSPORT, session=session, expected_config_sha256=digest,
                    generation=result["generation"], platform="telegram",
                    transport_profile=TRANSPORT, account_id=ACCOUNT, user_id=user_id,
                    name=name, value=values[name])
                say(stage="credential", user_id=user_id, name=name, recorded=outcome["recorded"])
        except BaseException as exc:
            # the area is put back exactly where it was, before the refusal is reported
            restored = restore_profile(home, target)
            after_digest, after_count = tree_digest(home) if home.exists() else (None, 0)
            say(stage="refused_and_restored", user_id=user_id, profile=profile,
                error=type(exc).__name__, detail=str(exc)[:200], restored=restored,
                digest_before=before_digest, digest_after=after_digest,
                bytes_identical=(before_digest == after_digest) if restored else False,
                files_after=after_count)
            raise
    rows_after = access_rows(state)
    say(stage="access_after", users=sorted(rows_after),
        note="the access history is preserved across the preparation")
    clean()


if __name__ == "__main__":
    main()
