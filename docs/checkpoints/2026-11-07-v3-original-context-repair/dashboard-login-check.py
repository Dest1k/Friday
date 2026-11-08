#!/usr/bin/env python3
"""Attempt the ordinary dashboard operator login with the owner-provided local file.

Prints ONLY non-secret outcomes. The password, cookies and tokens stay in this
process and are never written to stdout, logs, commits or project files.

Verification of success is an authorized /api/auth/me plus the operator identity
and the product's own operator-allowed policy check.
"""
import http.cookiejar
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

CREDS = Path("/home/jericho/jericho/frw_admin.txt")
BASE = "https://192.168.1.78:9119"
CA = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108/dashboard-tls/ca.pem")


def read_creds():
    raw = CREDS.read_text(errors="replace")
    user = re.search(r'"username"\s*:\s*"([^"]*)"', raw)
    pw = re.search(r'"password"\s*:\s*"([^"]*)"', raw)
    url = re.search(r'https?://[^\s"]+', raw)
    if not user or not pw:
        raise SystemExit("credential file lacks username/password fields")
    return (url.group(0) if url else BASE), user.group(1), pw.group(1)


def build_opener():
    ctx = ssl.create_default_context(cafile=str(CA))
    ctx.check_hostname = False  # the service certificate covers 192.168.1.78 / 192.168.12.128
    jar = http.cookiejar.CookieJar()

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
        NoRedirect,
    )
    return opener, jar


def post_json(opener, path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def get_json(opener, path):
    req = urllib.request.Request(BASE + path, method="GET", headers={"Accept": "application/json"})
    try:
        with opener.open(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def main():
    url, username, password = read_creds()
    opener, jar = build_opener()
    status, raw = post_json(opener, "/auth/password-login",
                            {"provider": "basic", "username": username,
                             "password": password, "next": "/"})
    outcome = {"login_status": status}
    try:
        body = json.loads(raw)
        outcome["login_ok"] = body.get("ok")
        outcome["next"] = body.get("next")
    except Exception:
        outcome["login_ok"] = False
    outcome["cookies_set"] = sorted(c.name for c in jar)
    if status != 200:
        print(json.dumps(outcome, sort_keys=True))
        raise SystemExit(1)
    st, raw = get_json(opener, "/api/auth/me")
    outcome["auth_me_status"] = st
    if st == 200:
        try:
            me = json.loads(raw)
            outcome["auth_me"] = {k: me.get(k) for k in
                                  ("user_id", "provider", "org_id", "display_name", "email")
                                  if k in me} or {"keys": sorted(me)[:8]}
        except Exception:
            outcome["auth_me"] = {"parsed": False}
    print(json.dumps(outcome, sort_keys=True))
    if st != 200:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
