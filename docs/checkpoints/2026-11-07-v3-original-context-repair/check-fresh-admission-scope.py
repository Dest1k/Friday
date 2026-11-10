#!/usr/bin/env python3
"""Check the admission generator against the REAL code it ships.

Every assertion in this file calls the generator's own functions (issue-fresh-admission.py
imported as a module) or its own main() with isolated inputs. No condition is copied into
a parallel test implementation, and no refusal is checked by grepping the source: a
refusal is an actual SystemExit raised by the real code, and the "not published on
refusal" property is checked by looking for the output file after the call.

Covered:
  * derive_identity: the next identity and the predecessor are taken from the actually
    released documents, and a self-superseding identity is refused;
  * collect_scenarios: a repeated run id is refused before the dict is built - in every
    combination of primary / extra / package, with equal and with different bytes, so one
    digest can never silently replace another;
  * validate_scope: a scope that does not describe the operation is refused;
  * validate_identity: self-supersedes and a missing predecessor are refused;
  * main(): on any refusal the admission document is NOT written, and a released
    admission is never rewritten.

Run it with any python3:
    python3 check-fresh-admission-scope.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "issue-fresh-admission.py"


def load():
    spec = importlib.util.spec_from_file_location("issue_fresh_admission", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n")


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode()


def main():
    gen = load()
    failures = []

    def check(name, condition, detail=""):
        if condition:
            print("PASS " + name)
        else:
            failures.append(name + (": " + detail if detail else ""))
            print("FAIL " + name + (": " + detail if detail else ""))

    def refuses(name, fn, *args, fragment=None, **kwargs):
        """The real generator code must raise SystemExit; no source grepping."""
        try:
            fn(*args, **kwargs)
        except SystemExit as exc:
            msg = str(exc)
            ok = fragment is None or fragment in msg
            check(name, ok, "reason=" + msg if not ok else "")
            return
        except Exception as exc:  # noqa: BLE001
            check(name, False, "wrong exception " + type(exc).__name__ + ": " + str(exc))
            return
        check(name, False, "NOT REFUSED (returned normally)")

    tmp = Path(tempfile.mkdtemp(prefix="fresh-admission-check-"))
    try:
        # ---- a small isolated scenario set --------------------------------------
        scen = tmp / "scenarios"
        scen.mkdir()
        write_json(scen / "s1.json", {"a": 1})
        write_json(scen / "s2.json", {"b": 2})
        write_json(scen / "s3.json", {"c": 3})
        write_json(scen / "s1-dup.json", {"a": 1})        # SAME bytes as s1
        write_json(scen / "s1-diff.json", {"a": 999})      # DIFFERENT bytes

        # ---- derive_identity: the chain comes from the real releases -------------
        rel = tmp / "releases"
        rel.mkdir()
        write_json(rel / "INDEPENDENT-AUTHORITY-R5.json", {"authority_id": "prov-r5"})
        write_json(rel / "INDEPENDENT-AUTHORITY-R6.json", {"authority_id": "prov-r6"})
        new_id, new_file, prev_id = gen.derive_identity(rel)
        check("derive_next_identity_is_r7", new_id.endswith("-r7"), new_id)
        check("derive_next_file", new_file == "INDEPENDENT-AUTHORITY-R7.json", new_file)
        check("derive_predecessor_is_r6", prev_id == "prov-r6", prev_id)
        check("derive_not_self_supersedes", new_id != prev_id, new_id + " vs " + prev_id)

        # derive from an empty directory must refuse
        empty = tmp / "empty"
        empty.mkdir()
        refuses("derive_refuses_without_predecessor", gen.derive_identity, empty)

        # ---- validate_identity --------------------------------------------------
        gen.validate_identity("prov-r7", "prov-r6", rel)   # must NOT raise
        check("identity_valid_accepted", True)
        refuses("identity_refuses_self_supersedes", gen.validate_identity,
                "prov-r6", "prov-r6", rel, fragment="supersedes itself")
        refuses("identity_refuses_missing_predecessor", gen.validate_identity,
                "prov-r7", "prov-99", rel, fragment="predecessor document is not")

        # ---- collect_scenarios: positive ---------------------------------------
        got = gen.collect_scenarios("s1", scen / "s1.json",
                                    [("s2", scen / "s2.json"), ("s3", scen / "s3.json")],
                                    None)
        check("collect_positive_three", set(got) == {"s1", "s2", "s3"}, str(sorted(got)))
        check("collect_digest_matches_file",
              got["s1"] == gen.digest(gen.encoded({"a": 1})), got["s1"])

        # ---- collect_scenarios: repeated run id in every combination ------------
        refuses("collect_refuses_primary_extra_same_bytes",
                gen.collect_scenarios, "s1", scen / "s1.json",
                [("s1", scen / "s1-dup.json")], None, fragment="repeated")
        refuses("collect_refuses_primary_extra_different_bytes",
                gen.collect_scenarios, "s1", scen / "s1.json",
                [("s1", scen / "s1-diff.json")], None, fragment="repeated")
        refuses("collect_refuses_extra_extra_repeat",
                gen.collect_scenarios, "s1", scen / "s1.json",
                [("s2", scen / "s2.json"), ("s2", scen / "s2.json")], None,
                fragment="repeated")

        # package collision: the same run id as the primary, with the CORRECT digest
        # (so the digest check passes) - the duplicate check must still refuse it
        pkg = tmp / "package.json"
        s1_sha = gen.digest(gen.encoded({"a": 1}))
        write_json(pkg, {"s1": s1_sha})
        refuses("collect_refuses_primary_package_collision",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg,
                fragment="repeated")

        # wrong declared hash in the package: the file bytes do not match
        write_json(pkg, {"s9": "0" * 64})
        write_json(scen / "s9.json", {"z": 1})
        refuses("collect_refuses_wrong_package_digest",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg,
                fragment="digest changed")

        # a package entry whose scenario file is absent
        write_json(pkg, {"s-absent": "0" * 64})
        refuses("collect_refuses_missing_package_scenario",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg,
                fragment="absent")

        # the package is ignored when it does not exist (optional input)
        got2 = gen.collect_scenarios("s1", scen / "s1.json", [], tmp / "no-such-package.json")
        check("collect_without_package_ok", set(got2) == {"s1"})

        # ---- collect_scenarios: repeated run id INSIDE the package (raw JSON) ----
        # The fixture must be RAW JSON text: a Python dict would silently drop the
        # duplicate key and invalidate the check. json.loads() with a plain dict also
        # drops it, so the generator must parse the PAIRS of the raw document.
        s2_sha = gen.digest(gen.encoded({"b": 2}))

        pkg_raw_same = tmp / "package-raw-same.json"
        pkg_raw_same.write_text(
            '{"s2": "' + s2_sha + '", "s2": "' + s2_sha + '"}\n')
        refuses("collect_refuses_package_internal_repeat_same_hash",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg_raw_same,
                fragment="repeated")

        pkg_raw_diff = tmp / "package-raw-diff.json"
        pkg_raw_diff.write_text(
            '{"s2": "' + s2_sha + '", "s2": "' + "0" * 64 + '"}\n')
        refuses("collect_refuses_package_internal_repeat_different_hash",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg_raw_diff,
                fragment="repeated")

        # a package with an internal repeat whose LAST value is the correct digest
        # must still be refused (this is the exact shape that used to pass)
        pkg_raw_last_ok = tmp / "package-raw-last-ok.json"
        pkg_raw_last_ok.write_text(
            '{"s2": "' + "0" * 64 + '", "s2": "' + s2_sha + '"}\n')
        refuses("collect_refuses_package_internal_repeat_last_value_ok",
                gen.collect_scenarios, "s1", scen / "s1.json", [], pkg_raw_last_ok,
                fragment="repeated")

        # control: a package WITHOUT a repeat passes and yields the right digest
        pkg_ok = tmp / "package-ok.json"
        pkg_ok.write_text('{"s2": "' + s2_sha + '"}\n')
        got3 = gen.collect_scenarios("s1", scen / "s1.json", [], pkg_ok)
        check("collect_package_without_repeat_ok",
              set(got3) == {"s1", "s2"} and got3["s2"] == s2_sha, str(sorted(got3)))

        # ---- validate_scope ----------------------------------------------------
        many = {"fmt-docx-create-x": "h", "d12-write-file-check-01-r48": "h"}
        gen.validate_scope(gen.SCOPE, many)   # must NOT raise
        check("scope_corrected_accepted", True)
        refuses("scope_refuses_single_smoke_for_many",
                gen.validate_scope,
                "One controlled Jarvis-area activation check from tester 8812646969.",
                many, fragment="activation smoke")
        refuses("scope_refuses_claimed_product_acceptance",
                gen.validate_scope,
                "This admission is a product acceptance of the format coverage.",
                {"fmt-docx-create-x": "h"}, fragment="product acceptance")
        refuses("scope_refuses_claimed_b00_acceptance",
                gen.validate_scope,
                "This admission is a B00 acceptance of the volume.",
                {"fmt-docx-create-x": "h"}, fragment="B00 acceptance")
        refuses("scope_refuses_formats_not_mentioned",
                gen.validate_scope,
                "Independent execution of the regression scenarios.",
                {"fmt-docx-create-x": "h"}, fragment="format-creation")

        # ---- main(): no document is published on any refusal -------------------
        # The real main() is run with isolated paths. The duplicate run id makes
        # collect_scenarios raise BEFORE any file is written.
        sandbox = tmp / "main-sandbox"
        sandbox.mkdir()
        (sandbox / "runs").mkdir()
        # the gateway check reads /proc/<pid>/stat field 22 (index 21 after split);
        # use this very process so the identity matches
        _my_stat = Path("/proc") / str(os.getpid()) / "stat"
        _my_start = _my_stat.read_text().split()[21]
        write_json(sandbox / "gateway_state.json",
                   {"pid": os.getpid(), "start_time": int(_my_start)})
        # seed released predecessors so derive_identity can build the chain
        write_json(sandbox / "INDEPENDENT-AUTHORITY-R3.json", {"authority_id": "prov-r3"})
        write_json(sandbox / "INDEPENDENT-AUTHORITY-R4.json", {"authority_id": "prov-r4"})
        for name, value in [("OUT_DIR", sandbox), ("RUNS", sandbox / "runs"),
                            ("GATEWAY_STATE", sandbox / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", tmp / "no-such-package.json"),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        gen.EXTRA_SCENARIOS = (("s1", str(scen / "s1-dup.json")),)  # repeated run id

        before = set(sandbox.glob("INDEPENDENT-AUTHORITY-R*.json"))
        refuses("main_refuses_duplicate_and_publishes_nothing", gen.main,
                fragment="repeated")
        after = set(sandbox.glob("INDEPENDENT-AUTHORITY-R*.json"))
        check("main_published_nothing_on_refusal", after == before,
              "wrote: " + str(sorted(p.name for p in after - before)))

        # ---- main(): a released admission is never rewritten --------------------
        # The no-overwrite rule in main() is exercised by making the derived identity
        # collide with a file that is already in place. derive_identity() derives the
        # NEXT free number, so a direct collision cannot arise from the scan alone;
        # the rule is a second layer of protection, and it is tested here by fixing the
        # derived identity to the number that is already present.
        gen.EXTRA_SCENARIOS = (("s2", str(scen / "s2.json")),)
        auth_id, auth_file, prev_id = gen.derive_identity(sandbox)
        check("main_derived_predecessor_is_r4", prev_id == "prov-r4", prev_id)
        # seed the target file so the no-overwrite rule fires
        write_json(sandbox / auth_file, {"already": "released"})
        real_derive = gen.derive_identity
        gen.derive_identity = lambda _out: (auth_id, auth_file, prev_id)
        try:
            refuses("main_refuses_to_rewrite_released_admission", gen.main,
                    fragment="already exists and is pinned")
        finally:
            gen.derive_identity = real_derive
        # the seeded file must be untouched
        check("main_released_file_untouched",
              json.loads((sandbox / auth_file).read_text()) == {"already": "released"})

        # ---- main(): two competing releases of the same number ------------------
        # The real main() is run twice against the same isolated OUT_DIR with the same
        # derived identity. The first release must succeed; the second must refuse with
        # the pinned-file reason, and the PUBLISHED BYTES AND HASH OF THE FIRST must be
        # preserved untouched. This is the deterministic form of the race that
        # exists() + write_bytes() used to lose.
        race = tmp / "main-race"
        race.mkdir()
        (race / "runs").mkdir()
        _rs = (Path("/proc") / str(os.getpid()) / "stat").read_text().split()[21]
        write_json(race / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(race / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        write_json(race / "INDEPENDENT-AUTHORITY-R2.json", {"authority_id": "prov-r2"})
        for name, value in [("OUT_DIR", race), ("RUNS", race / "runs"),
                            ("GATEWAY_STATE", race / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", tmp / "no-such-package.json"),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        gen.EXTRA_SCENARIOS = (("s2", str(scen / "s2.json")),)

        auth_id_r, auth_file_r, prev_id_r = gen.derive_identity(race)
        check("race_derived_predecessor_is_r2", prev_id_r == "prov-r2", prev_id_r)
        real_derive = gen.derive_identity
        gen.derive_identity = lambda _out: (auth_id_r, auth_file_r, prev_id_r)
        try:
            # release 1: succeeds
            gen.main()
            target_r = race / auth_file_r
            check("race_first_release_wrote_file", target_r.is_file(), auth_file_r)
            first_bytes = target_r.read_bytes()
            first_hash = gen.digest(first_bytes)
            check("race_first_release_mode_0600",
                  oct(target_r.stat().st_mode & 0o777) == "0o600",
                  oct(target_r.stat().st_mode & 0o777))
            # release 2: must refuse and must NOT touch the published bytes
            refuses("race_second_release_refuses", gen.main,
                    fragment="already exists and is pinned")
            check("race_published_bytes_preserved",
                  target_r.read_bytes() == first_bytes,
                  "bytes changed after the refused second release")
            check("race_published_hash_preserved",
                  gen.digest(target_r.read_bytes()) == first_hash)
            # no leftover temp files from either release
            leftovers = [p.name for p in race.iterdir()
                         if p.name.endswith(".tmp-" + str(os.getpid()))]
            check("race_no_temp_leftovers", not leftovers, str(leftovers))
        finally:
            gen.derive_identity = real_derive

        # ---- main(): a normal successful release publishes complete JSON ---------
        norm = tmp / "main-norm"
        norm.mkdir()
        (norm / "runs").mkdir()
        write_json(norm / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(norm / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        for name, value in [("OUT_DIR", norm), ("RUNS", norm / "runs"),
                            ("GATEWAY_STATE", norm / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", tmp / "no-such-package.json"),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        gen.EXTRA_SCENARIOS = (("s2", str(scen / "s2.json")),)
        auth_id_n, auth_file_n, prev_id_n = gen.derive_identity(norm)
        real_derive = gen.derive_identity
        gen.derive_identity = lambda _out: (auth_id_n, auth_file_n, prev_id_n)
        try:
            gen.main()
            target_n = norm / auth_file_n
            doc = json.loads(target_n.read_text())
            check("normal_release_publishes_valid_json",
                  doc.get("authority_id") == auth_id_n, str(doc.get("authority_id")))
            check("normal_release_mode_0600",
                  oct(target_n.stat().st_mode & 0o777) == "0o600",
                  oct(target_n.stat().st_mode & 0o777))
            check("normal_release_predecessor_recorded",
                  doc.get("supersedes", {}).get("authority_id") == prev_id_n)
        finally:
            gen.derive_identity = real_derive

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(json.dumps({"checks_failed": failures, "result": "PASS" if not failures else "FAIL"},
                     sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
