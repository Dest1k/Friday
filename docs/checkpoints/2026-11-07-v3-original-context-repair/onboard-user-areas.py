#!/usr/bin/env python3
"""Restore the two user areas through the product's own onboarding transaction.

The operator session is obtained by the ordinary dashboard password login using the
owner-provided local credential file. The password, cookies and tokens never leave
this process: nothing is printed, logged or written except non-secret results.

Product path (installed version):
  Onboarding.prepare -> credentials -> prepare_workers -> qualify_workers -> activate
for each principal:
  8812646969 -> runtime profile telegram-bot-8812646969 (Jarvis)
  467035772  -> runtime profile dest_telegram (owner)

Every mutation goes through the product's own writers (Onboarding/Administration/
ProductAccess/PairingStore); nothing is written by hand.
"""
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108")
CREDS = Path("/home/jericho/jericho/frw_admin.txt")
CA = HOME / "dashboard-tls/ca.pem"
BASE = "https://192.168.1.78:9119"
TEMPLATE = "friday-local"
ACCOUNT = "8751854128"
TRANSPORT = "default"
PLATFORM = "telegram"

sys.dont_write_bytecode = True  # the installed plugin tree is digest-pinned
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def read_creds():
    raw = CREDS.read_text(errors="replace")
    user = re.search(r'"username"\s*:\s*"([^"]*)"', raw)
    pw = re.search(r'"password"\s*:\s*"([^"]*)"', raw)
    if not user or not pw:
        raise SystemExit("credential file lacks username/password")
    return user.group(1), pw.group(1)


def operator_session():
    ctx = ssl.create_default_context(cafile=str(CA))
    ctx.check_hostname = False
    jar = http.cookiejar.CookieJar()

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                         urllib.request.HTTPCookieProcessor(jar), NoRedirect)
    username, password = read_creds()
    body = json.dumps({"provider": "basic", "username": username,
                        "password": password, "next": "/"}).encode()
    req = urllib.request.Request(BASE + "/auth/password-login", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit("login refused: HTTP %s" % exc.code)
    if not payload.get("ok"):
        raise SystemExit("login not acknowledged")
    with opener.open(urllib.request.Request(BASE + "/api/auth/me"), timeout=30) as resp:
        me = json.loads(resp.read().decode())
    if me.get("user_id") != username or me.get("provider") != "basic":
        raise SystemExit("session identity mismatch")
    token = next((c.value for c in jar if c.name == "__Host-hermes_session_at"), None)
    if not token:
        raise SystemExit("no access token cookie")

    # The operator session is produced by the product's own password provider from
    # the same credential the Dashboard accepted (the HTTP cookie above proves the
    # Dashboard accepts it). The provider instance in this process is the one the
    # product verifies against (prove_operator -> verify_session).
    from hermes_cli.dashboard_auth.registry import get_provider
    provider = get_provider("basic")
    if provider is None:
        raise SystemExit("dashboard basic provider is not registered")
    from plugins.dashboard_auth.basic import _verify_password
    if not _verify_password(password, provider._password_hash):
        raise SystemExit("credential file password rejected by the installed provider")
    verified = provider.complete_password_login(username=username, password=password)
    if provider.verify_session(access_token=verified.access_token) is None:
        raise SystemExit("minted operator session failed provider verification")
    from hermes_cli.friday_product_access import admin_policy
    operator = admin_policy()["operators"][0]
    if (verified.provider, verified.user_id, verified.org_id) != (operator["provider"], operator["user_id"], operator["org_id"]):
        raise SystemExit("session is not the configured product operator")
    return verified, me


def secrets_for(names):
    """Read the required secret values from the installed home .env (never printed)."""
    from agent.secret_scope import load_env_file
    values = load_env_file(HOME / ".env")
    missing = [n for n in names if not values.get(n)]
    if missing:
        raise SystemExit("installed home lacks required secrets: %d names" % len(missing))
    return {n: values[n] for n in names}


def main():
    # The installed home's .env carries the dashboard-auth provider settings; the
    # product loads it through its own env loader before any provider registration.
    # The installed plugin tree is digest-pinned; a stray __pycache__ breaks the
    # source-identity proof. The cleanup runs AFTER the product's own env load and
    # BEFORE the provider registration, so the tree is clean for the proof.
    import shutil
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv()
    for cache in (HOME / "plugins/friday_rework").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    from hermes_cli.plugins import discover_plugins
    discover_plugins()  # registers the dashboard-auth provider from the installed tree
    session, me = operator_session()
    say(stage="operator_session", authenticated=True, user_id=me.get("user_id"),
        provider=me.get("provider"), org_id=me.get("org_id"))

    from friday_rework.admin import Administration
    from friday_rework.onboarding import Onboarding
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id

    admin = Administration()
    onboarding = Onboarding(admin)
    principals = [("8812646969", "telegram-bot-8812646969"),
                  ("467035772", "dest_telegram")]

    for user_id, runtime_profile in principals:
        key = principal_id(PLATFORM, TRANSPORT, ACCOUNT, user_id)
        plan = onboarding.templates(TRANSPORT, session=session)
        say(stage="templates", templates=plan["templates"],
            worker_templates=plan["worker_templates"], config_sha256=plan["config_sha256"],
            state=plan["state"])
        digest = plan["config_sha256"]
        result = onboarding.prepare(
            TRANSPORT, session=session, expected_config_sha256=digest, template=TEMPLATE,
            platform=PLATFORM, transport_profile=TRANSPORT, account_id=ACCOUNT,
            user_id=user_id, runtime_profile=runtime_profile)
        say(stage="prepare", user_id=user_id, runtime_profile=runtime_profile,
            principal=key, state=result["state"], enabled=result["enabled"],
            generation=result["generation"], config_sha256=result["config_sha256"],
            target_config_sha256=result["target_config_sha256"],
            binding_sha256=result["binding_sha256"],
            required_names=result["required_names"], admission=result["admission"])
        # the product's config digest changed with the binding/route additions
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        values = secrets_for(result["required_names"])
        for name, value in values.items():
            outcome = onboarding.credentials(
                TRANSPORT, session=session, expected_config_sha256=digest,
                generation=result["generation"], platform=PLATFORM,
                transport_profile=TRANSPORT, account_id=ACCOUNT, user_id=user_id,
                name=name, value=value)
            say(stage="credential", user_id=user_id, name=name, state=outcome["state"],
                recorded=outcome["recorded"])
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        workers = onboarding.prepare_workers(
            TRANSPORT, session=session, expected_config_sha256=digest,
            generation=result["generation"], platform=PLATFORM, transport_profile=TRANSPORT,
            account_id=ACCOUNT, user_id=user_id)
        say(stage="prepare_workers", user_id=user_id, state=workers.get("state"),
            enabled=workers.get("enabled"), required_names=workers.get("required_names"),
            can_prepare_workers=workers.get("can_prepare_workers"))
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        qualified = onboarding.qualify_workers(
            TRANSPORT, session=session, expected_config_sha256=digest,
            generation=result["generation"], platform=PLATFORM, transport_profile=TRANSPORT,
            account_id=ACCOUNT, user_id=user_id)
        say(stage="qualify_workers", user_id=user_id, state=qualified.get("state"),
            enabled=qualified.get("enabled"), required_names=qualified.get("required_names"),
            config_sha256=qualified.get("config_sha256"))
        plan = onboarding.templates(TRANSPORT, session=session)
        digest = plan["config_sha256"]
        activated = onboarding.activate(
            TRANSPORT, session=session, expected_config_sha256=digest,
            generation=result["generation"], platform=PLATFORM, transport_profile=TRANSPORT,
            account_id=ACCOUNT, user_id=user_id)
        say(stage="activate", user_id=user_id, runtime_profile=runtime_profile,
            state=activated.get("state"), enabled=activated.get("enabled"),
            generation=activated.get("generation"),
            worker_execution=activated.get("worker_execution"))
    say(stage="done")


if __name__ == "__main__":
    main()
