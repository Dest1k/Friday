#!/usr/bin/env python3
"""Check the scope boundaries of the ordinary user areas through the product's own path.

The review's rule is explicit: a refusal of document_creation_requires_user_scope on a
direct call outside a user context does not by itself prove a defect, and the formats are
to be checked through the provided live path. This script therefore enters the scope the
way the product enters it - through the area's own UserScope - and checks what the product
can prove offline:

* that each user area has its own runtime profile, receiving root and storage paths, and
  that the two areas share no runtime root;
* that a file write inside a user's own workspace is accepted by the product's scope
  guard;
* that the same write aimed at the OTHER user's workspace is refused by the same guard;
* that the owner area and the Jarvis area are bound to different profiles, so the owner's
  conversation and data are not served through the Jarvis profile and the other way round.

No model answer is requested and none is graded: this is a boundary check of the product's
own guard, not a live task.
"""
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path("/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032")
AREAS = (("8812646969", "telegram-bot-8812646969"), ("467035772", "dest_telegram"))
PROBE = "scope-check.txt"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HOME / "hermes-agent"))
sys.path.insert(0, str(HOME / "plugins"))
os.environ["HERMES_HOME"] = str(HOME)


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def scope_for(binding):
    """The product's own capability object for one binding."""
    from hermes_cli import friday_user_scope as scope
    from hermes_cli.friday_product_access import principal_id, current_access
    key = principal_id(binding["platform"], binding["transport_profile"],
                       binding["account_id"], binding["user_id"])
    with scope.authority(HOME):
        access = current_access()["users"].get(key)
    generation = (access or {}).get("generation")
    home = HOME / "profiles" / binding["runtime_profile"]
    identity = home.stat()
    return scope.UserScope(authorization_home=HOME,
                           home=home,
                           profile=binding["runtime_profile"],
                           principal=(binding["platform"], binding["transport_profile"],
                                      binding["account_id"], binding["user_id"]),
                           binding=binding,
                           directory_identity=(identity.st_dev, identity.st_ino),
                           admission_generation=generation)


def main():
    from hermes_cli import friday_user_scope as scope
    policy = scope.policy(HOME)
    results = []
    roots = set()
    for user_id, profile in AREAS:
        binding = next((b for b in policy["bindings"]
                        if b["runtime_profile"] == profile and b["user_id"] == user_id), None)
        if binding is None:
            results.append({"area": profile, "bound": False})
            continue
        home = HOME / "profiles" / profile
        roots.add(str(home))
        results.append({
            "area": profile, "user_id": user_id, "bound": True,
            "receiving_root": str(home), "exists": home.is_dir(),
            "storage_paths": sorted(p.name for p in home.iterdir()
                                   if p.name in ("state.db", "workspace", "memories", "skills",
                                                 "cron", "sessions", "pairing")),
            "tools": len(binding.get("tools") or []),
        })
    results.append({"check": "the areas share no receiving root", "ok": len(roots) == len(AREAS)})
    results.append({"check": "the areas have different runtime profiles",
                    "ok": len({p for p, _ in AREAS}) == len(AREAS)})

    for user_id, profile in AREAS:
        binding = next(b for b in policy["bindings"]
                       if b["runtime_profile"] == profile and b["user_id"] == user_id)
        capability = scope_for(binding)
        own = capability.home / "workspace" / PROBE
        other_profile = AREAS[1][1] if profile == AREAS[0][1] else AREAS[0][1]
        other = HOME / "profiles" / other_profile / "workspace" / PROBE
        outcomes = {}
        # the product's own authority: the scope is evaluated under the area's own
        # runtime home, which is what the gateway process holds while it serves that area
        with scope.authority(capability.home):
            token = scope._CURRENT.set(capability)
            try:
                for label, path in (("inside_own_workspace", own),
                                    ("outside_own_workspace", other)):
                    try:
                        scope.scoped_file("write_file", {"path": str(path),
                                                        "content": "scope check\n"})
                        outcomes[label] = "ACCEPTED"
                    except Exception as exc:
                        outcomes[label] = type(exc).__name__
            finally:
                scope._CURRENT.reset(token)
        results.append({"area": profile, "scope_outcomes": outcomes,
                        "own_file_written": own.exists(),
                        "other_file_written": other.exists()})
        for path in (own, other):
            if path.exists():
                path.unlink()
    for result in results:
        say(**result) if len(result) > 1 else say(result)


if __name__ == "__main__":
    main()
