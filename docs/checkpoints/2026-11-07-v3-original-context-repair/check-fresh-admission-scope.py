#!/usr/bin/env python3
"""Check the admission generator against the REAL code it ships.

Production assertions call the generator's own functions (issue-fresh-admission.py
imported as a module) or its own main() with isolated inputs. An explicit legacy
publisher is retained as a negative control for the race detector. No production
condition is copied into a parallel implementation, and no refusal uses source grepping: a
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
    admission is never rewritten;
  * optional ordered predecessors: exact pinned canonical retained runs and protected
    Root PASS reviews are required before publication; empty input leaves the field
    absent, while malformed/changed/non-PASS input never publishes a final grant.

Run it with any python3:
    python3 check-fresh-admission-scope.py
"""
import contextlib
import hashlib
import importlib.util
import io
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


def competing_releases(publish, target):
    """Control both atomic linking and the legacy absent-check/write interleaving."""
    import threading

    link_barrier = threading.Barrier(2)
    absence_barrier = threading.Barrier(2)
    first_absence_done = threading.Event()
    arrival_lock = threading.Lock()
    real_link = os.link
    real_exists = Path.exists
    real_write_bytes = Path.write_bytes
    link_actors = []
    absent_actors = []
    writes = []
    results = [None, None]

    def sync_exists(path):
        exists = real_exists(path)
        if path == target and not exists:
            actor = threading.get_ident()
            with arrival_lock:
                absent_actors.append(actor)
                first = absent_actors[0] == actor
            absence_barrier.wait(timeout=10)
            if not first and not first_absence_done.wait(timeout=10):
                raise TimeoutError("first legacy actor did not finish")
        return exists

    def sync_link(src, dst):
        with arrival_lock:
            link_actors.append(threading.get_ident())
        link_barrier.wait(timeout=10)
        return real_link(src, dst)

    def observe_write(path, data):
        if path != target:
            return real_write_bytes(path, data)
        with arrival_lock:
            observed_absences = len(set(absent_actors))
        written = real_write_bytes(path, data)
        writes.append((threading.get_ident(), observed_absences, path.read_bytes()))
        return written

    def attempt(idx):
        try:
            publish(idx)
            results[idx] = ("ok", None)
        except SystemExit as exc:
            results[idx] = ("exit", str(exc))
        except Exception as exc:  # noqa: BLE001
            results[idx] = ("err", type(exc).__name__ + ": " + str(exc))
        finally:
            if absent_actors and absent_actors[0] == threading.get_ident():
                first_absence_done.set()

    os.link = sync_link
    Path.exists = sync_exists
    Path.write_bytes = observe_write
    try:
        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
    finally:
        os.link = real_link
        Path.exists = real_exists
        Path.write_bytes = real_write_bytes

    ok_count = sum(1 for result in results if result and result[0] == "ok")
    return {
        "results": results,
        "ok_count": ok_count,
        "exit_count": sum(1 for result in results if result and result[0] == "exit"),
        "err_count": sum(1 for result in results if result and result[0] == "err"),
        "exactly_one_succeeds": ok_count == 1,
        "absent_actors": absent_actors,
        "link_actors": link_actors,
        "writes": writes,
        "threads_finished": not any(thread.is_alive() for thread in threads),
    }


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

        # ---- main(): a partial os.write is completed, not published truncated ----
        # os.write() may write fewer bytes than requested. The generator must loop
        # until every byte is written and publish only complete bytes; the reported
        # size and hash must be those of the PUBLISHED file.
        part = tmp / "main-partial"
        part.mkdir()
        (part / "runs").mkdir()
        write_json(part / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(part / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        for name, value in [("OUT_DIR", part), ("RUNS", part / "runs"),
                            ("GATEWAY_STATE", part / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", tmp / "no-such-package.json"),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        gen.EXTRA_SCENARIOS = (("s2", str(scen / "s2.json")),)
        auth_id_p, auth_file_p, prev_id_p = gen.derive_identity(part)
        real_derive = gen.derive_identity
        real_write = os.write
        write_calls = [0]

        def short_write(fd, data):
            # first call writes only 7 bytes: a SHORT WRITE
            write_calls[0] += 1
            if write_calls[0] == 1:
                return real_write(fd, data[:7])
            return real_write(fd, data)

        gen.derive_identity = lambda _out: (auth_id_p, auth_file_p, prev_id_p)
        os.write = short_write
        try:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                gen.main()
            report = json.loads(stdout.getvalue())
            target_p = part / auth_file_p
            published = target_p.read_bytes()
            doc_p = json.loads(published)
            check("partial_write_publishes_complete_json",
                  doc_p.get("authority_id") == auth_id_p, str(doc_p.get("authority_id")))
            check("partial_write_retried_after_short_write",
                  len(published) > 7 and write_calls[0] >= 2,
                  "calls=%d published=%d" % (write_calls[0], len(published)))
            check("partial_write_reported_size_matches_published",
                  report.get("bytes") == len(published),
                  "reported=%r published=%d" % (report.get("bytes"), len(published)))
            check("partial_write_hash_matches_published",
                  report.get("sha256") == hashlib.sha256(published).hexdigest(),
                  "reported=%r published=%s"
                  % (report.get("sha256"), hashlib.sha256(published).hexdigest()))
            leftovers_p = [p.name for p in part.iterdir() if ".tmp-" in p.name]
            check("partial_write_no_temp_leftovers", not leftovers_p, str(leftovers_p))
        finally:
            os.write = real_write
            gen.derive_identity = real_derive

        # ---- main(): refusal after a partial write (RLIMIT_FSIZE) ---------------
        # An isolated subprocess limits the file size so the write fails partway.
        # The final file must NOT appear, the temp file must be removed, and a
        # previously published admission must be preserved. The limit is applied
        # only inside this isolated test.
        import subprocess as _sp
        rlim = tmp / "main-rlimit"
        rlim.mkdir()
        (rlim / "runs").mkdir()
        write_json(rlim / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(rlim / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        # seed a previously published admission that must survive
        write_json(rlim / "INDEPENDENT-AUTHORITY-R9.json", {"authority_id": "prov-r9",
                                                             "marker": "keep-me"})
        helper = tmp / "rlimit_helper.py"
        helper.write_text(
            "import os, resource, sys, signal\n"
            "signal.signal(signal.SIGXFSZ, signal.SIG_IGN)\n"
            "resource.setrlimit(resource.RLIMIT_FSIZE, (128, 128))\n"
            "sys.path.insert(0, %r)\n"
            "import importlib.util\n"
            "spec = importlib.util.spec_from_file_location('ifa', %r)\n"
            "gen = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(gen)\n"
            "for k, v in {'OUT_DIR': %r, 'RUNS': %r, 'GATEWAY_STATE': %r, "
            "'SCENARIO': %r, 'RUN_ID': 's1', 'PACKAGE_FILE': %r, 'SCOPE': gen.SCOPE}.items():\n"
            "    setattr(gen, k, __import__('pathlib').Path(v) if k in ('OUT_DIR','RUNS',"
            "'GATEWAY_STATE','SCENARIO','PACKAGE_FILE') else v)\n"
            "gen.EXTRA_SCENARIOS = (('s2', %r),)\n"
            "gen.derive_identity = lambda _o: (%r, %r, 'prov-r1')\n"
            "gen.main()\n"
            % (str(tmp), str(GENERATOR), str(rlim), str(rlim / "runs"),
               str(rlim / "gateway_state.json"), str(scen / "s1.json"),
               str(tmp / "no-such-package.json"), str(scen / "s2.json"),
               auth_id_p + "-rlimit", "INDEPENDENT-AUTHORITY-R2.json")
        )
        r = _sp.run([sys.executable, str(helper)], capture_output=True, text=True, timeout=30)
        check("rlimit_release_refuses", r.returncode != 0,
              "rc=%d out=%s err=%s" % (r.returncode, r.stdout[-120:], r.stderr[-120:]))
        final = rlim / "INDEPENDENT-AUTHORITY-R2.json"
        check("rlimit_no_final_file", not final.exists(), str(final))
        leftovers_r = [p.name for p in rlim.iterdir() if ".tmp-" in p.name]
        check("rlimit_no_temp_leftovers", not leftovers_r, str(leftovers_r))
        kept = rlim / "INDEPENDENT-AUTHORITY-R9.json"
        check("rlimit_previous_admission_preserved",
              kept.exists() and json.loads(kept.read_text()).get("marker") == "keep-me")

        # ---- race: two OVERLAPPING releases of the same number -----------------
        # Synchronize the real publication operation, and also the legacy target
        # exists() checks AFTER both have actually observed absence. The latter
        # control is essential: legacy exists()+write_bytes() never calls os.link.
        # Once both absence checks complete, finish the first actor before allowing
        # the second to use its stale False result. Both legacy actors then succeed
        # deterministically, without a concurrent truncate/read masking the defect.
        # On the os.link implementation exactly one publication succeeds.
        race2 = tmp / "main-race2"
        race2.mkdir()
        (race2 / "runs").mkdir()
        write_json(race2 / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(race2 / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        write_json(race2 / "INDEPENDENT-AUTHORITY-R2.json", {"authority_id": "prov-r2"})
        for name, value in [("OUT_DIR", race2), ("RUNS", race2 / "runs"),
                            ("GATEWAY_STATE", race2 / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", tmp / "no-such-package.json"),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        gen.EXTRA_SCENARIOS = (("s2", str(scen / "s2.json")),)
        auth_id_x, auth_file_x, prev_id_x = gen.derive_identity(race2)
        real_derive = gen.derive_identity
        gen.derive_identity = lambda _out: (auth_id_x, auth_file_x, prev_id_x)

        target_x = race2 / auth_file_x
        try:
            atomic = competing_releases(lambda _idx: gen.main(), target_x)
        finally:
            gen.derive_identity = real_derive

        check("race_both_actors_reached_controlled_point",
              len(set(atomic["absent_actors"])) == 2 or len(set(atomic["link_actors"])) == 2,
              "absence_checks=%d link_calls=%d"
              % (len(atomic["absent_actors"]), len(atomic["link_actors"])))
        check("race_threads_finished", atomic["threads_finished"])
        results = atomic["results"]
        ok_count, exit_count, err_count = (
            atomic["ok_count"], atomic["exit_count"], atomic["err_count"])
        check("race_exactly_one_succeeds", atomic["exactly_one_succeeds"],
              "ok=%d exit=%d err=%d results=%s" % (ok_count, exit_count, err_count, results))
        check("race_other_refuses", exit_count == 1,
              "ok=%d exit=%d err=%d results=%s" % (ok_count, exit_count, err_count, results))
        check("race_no_thread_error", err_count == 0,
              "results=%s" % (results,))
        check("race_winner_document_valid",
              target_x.is_file()
              and json.loads(target_x.read_text()).get("authority_id") == auth_id_x)
        check("race_winner_mode_0600",
              target_x.is_file() and oct(target_x.stat().st_mode & 0o777) == "0o600")
        leftovers_x = [p.name for p in race2.iterdir() if ".tmp-" in p.name]
        check("race_no_temp_leftovers", not leftovers_x, str(leftovers_x))

        # Retained negative control: this is the exact unsafe publication pattern,
        # using distinct documents so the first successful publication is visibly
        # overwritten. The same harness observes real absences before either write.
        legacy_target = tmp / "legacy-admission.json"

        def legacy_publish(idx):
            if legacy_target.exists():
                raise SystemExit("the admission already exists and is pinned")
            legacy_target.write_bytes(encoded({"actor": idx}))

        legacy = competing_releases(legacy_publish, legacy_target)
        legacy_writes = legacy["writes"]
        check("legacy_race_both_actors_observed_absence_before_writes",
              len(set(legacy["absent_actors"])) == 2 and len(legacy_writes) == 2
              and all(absences == 2 for _actor, absences, _raw in legacy_writes),
              "absence_checks=%d writes=%d"
              % (len(legacy["absent_actors"]), len(legacy_writes)))
        check("legacy_race_threads_finished", legacy["threads_finished"])
        check("legacy_race_two_successes",
              legacy["ok_count"] == 2 and legacy["exit_count"] == legacy["err_count"] == 0,
              str(legacy["results"]))
        check("legacy_race_first_publication_overwritten",
              len(legacy_writes) == 2 and legacy_writes[0][2] != legacy_writes[1][2]
              and legacy_target.read_bytes() == legacy_writes[1][2])
        check("legacy_race_detector_rejects_unsafe_publisher",
              not legacy["exactly_one_succeeds"])

        # ---- optional ordered predecessors: real issuer, isolated evidence ------
        ordered = tmp / "main-ordered"
        ordered.mkdir()
        (ordered / "runs").mkdir()
        write_json(ordered / "gateway_state.json", {"pid": os.getpid(), "start_time": int(_rs)})
        write_json(ordered / "INDEPENDENT-AUTHORITY-R1.json", {"authority_id": "prov-r1"})
        for name, value in [("OUT_DIR", ordered), ("RUNS", ordered / "runs"),
                            ("GATEWAY_STATE", ordered / "gateway_state.json"),
                            ("SCENARIO", scen / "s1.json"), ("RUN_ID", "s1"),
                            ("PACKAGE_FILE", None), ("EXTRA_SCENARIOS", ()),
                            ("SCOPE", gen.SCOPE)]:
            setattr(gen, name, value)
        previous_path = ordered / "runs" / "prior.json"
        review_path = ordered / "root-review.json"
        previous_scenario = {"retained": "actual synthetic prerequisite"}
        previous_sha = gen.digest(encoded(previous_scenario))
        previous = {"id": "prior", "scenario": previous_scenario,
                    "scenario_sha256": previous_sha, "status": "EVIDENCE_READY",
                    "send_state": "sent", "send_attempts": 1}

        def reset_ordered():
            for path in (previous_path, review_path):
                path.unlink(missing_ok=True)
            write_json(previous_path, previous)
            previous_path.chmod(0o600)
            review = {"schema": "friday.v3.root-synthetic-review.v1", "run_id": "prior",
                      "scenario_sha256": previous_sha, "semantic": "PASS", "custody": "PASS",
                      "custody_evidence": {"run_record_sha256": gen.digest(previous_path.read_bytes())}}
            # Review formatting is not a canonical-run requirement. Preserve an
            # existing 0664 review under the owned 0700 sandbox, without chmod PASS.
            review_path.write_text(json.dumps(review, indent=2) + "\n")
            review_path.chmod(0o664)
            binding = {"run_id": "prior", "scenario_sha256": previous_sha,
                       "run_record_sha256": gen.digest(previous_path.read_bytes()),
                       "review": {"path": str(review_path), "sha256": gen.digest(review_path.read_bytes())},
                       "review_schema": review["schema"], "initially_absent": False}
            gen.ORDERED_PREDECESSORS = {"s1": binding}
            return binding, review

        target_o = ordered / "INDEPENDENT-AUTHORITY-R2.json"

        def change_row(field, value):
            row = json.loads(previous_path.read_bytes())
            row[field] = value
            write_json(previous_path, row)
            # Repin the changed bytes and matching review so the specific retained
            # state/embedded-scenario check, rather than only the outer pin, is tested.
            binding = gen.ORDERED_PREDECESSORS["s1"]
            binding["run_record_sha256"] = gen.digest(previous_path.read_bytes())
            change_review("custody_evidence", {"run_record_sha256": binding["run_record_sha256"]})

        def change_review(field, value):
            review = json.loads(review_path.read_bytes())
            review[field] = value
            write_json(review_path, review)
            gen.ORDERED_PREDECESSORS["s1"]["review"]["sha256"] = gen.digest(review_path.read_bytes())

        def bad_input(name, mutate):
            binding, review = reset_ordered()
            mutate(binding, review)
            before = {p.name: p.read_bytes() for p in ordered.glob("INDEPENDENT-AUTHORITY-R*.json")}
            refuses("ordered_refuses_" + name, gen.main)
            after = {p.name: p.read_bytes() for p in ordered.glob("INDEPENDENT-AUTHORITY-R*.json")}
            check("ordered_no_publication_" + name,
                  after == before and not target_o.exists()
                  and not list(ordered.glob("*.tmp-*")))

        bad_input("non_map", lambda b, r: setattr(gen, "ORDERED_PREDECESSORS", None))
        bad_input("uncovered_successor", lambda b, r: setattr(gen, "ORDERED_PREDECESSORS", {"outside": b}))
        bad_input("self_predecessor", lambda b, r: b.update(run_id="s1"))
        bad_input("extra_binding_key", lambda b, r: b.update(extra=True))
        bad_input("missing_binding_key", lambda b, r: b.pop("initially_absent"))
        bad_input("unsafe_run_id", lambda b, r: b.update(run_id="../prior"))
        bad_input("unpinned_run", lambda b, r: b.update(run_record_sha256=None))
        bad_input("wrong_run_pin", lambda b, r: b.update(run_record_sha256="0" * 64))
        bad_input("malformed_scenario_pin", lambda b, r: b.update(scenario_sha256="not-a-sha"))
        bad_input("wrong_scenario_pin", lambda b, r: b.update(scenario_sha256="0" * 64))
        bad_input("extra_review_key", lambda b, r: b["review"].update(extra=True))
        bad_input("unpinned_review", lambda b, r: b["review"].update(sha256=None))
        bad_input("wrong_review_pin", lambda b, r: b["review"].update(sha256="0" * 64))
        bad_input("relative_review", lambda b, r: b["review"].update(path="root-review.json"))
        bad_input("nonboolean_initially_absent", lambda b, r: b.update(initially_absent=0))
        bad_input("missing_run", lambda b, r: previous_path.unlink())
        bad_input("changed_run_bytes", lambda b, r: previous_path.write_bytes(previous_path.read_bytes() + b" "))
        bad_input("noncanonical_run", lambda b, r: (
            previous_path.write_text(json.dumps(previous, indent=2) + "\n"),
            b.update(run_record_sha256=gen.digest(previous_path.read_bytes()))))
        bad_input("wrong_run_identity", lambda b, r: change_row("id", "other"))
        bad_input("embedded_scenario_changed", lambda b, r: change_row("scenario", {"retained": "different"}))
        bad_input("unfinished_run", lambda b, r: change_row("status", "PREPARED"))
        bad_input("unknown_send", lambda b, r: change_row("send_state", "unknown"))
        bad_input("repeat_send", lambda b, r: change_row("send_attempts", 2))
        bad_input("boolean_send_attempts", lambda b, r: change_row("send_attempts", True))
        bad_input("missing_review", lambda b, r: review_path.unlink())
        bad_input("changed_review_bytes", lambda b, r: review_path.write_bytes(review_path.read_bytes() + b" "))
        bad_input("malformed_review", lambda b, r: (
            review_path.write_text("{not-json}\n"),
            b["review"].update(sha256=gen.digest(review_path.read_bytes()))))
        bad_input("duplicate_review_json_keys", lambda b, r: (
            review_path.write_text('{"schema":"wrong",' + json.dumps(r)[1:] + "\n"),
            b["review"].update(sha256=gen.digest(review_path.read_bytes()))))
        bad_input("wrong_review_schema", lambda b, r: change_review("schema", "different"))
        bad_input("wrong_review_run", lambda b, r: change_review("run_id", "other"))
        bad_input("wrong_review_scenario", lambda b, r: change_review("scenario_sha256", "0" * 64))
        bad_input("semantic_fail", lambda b, r: change_review("semantic", "FAIL"))
        bad_input("custody_fail", lambda b, r: change_review("custody", "FAIL"))
        bad_input("wrong_review_custody_pin", lambda b, r:
                  change_review("custody_evidence", {"run_record_sha256": "0" * 64}))
        bad_input("unsafe_run_mode", lambda b, r: previous_path.chmod(0o664))
        bad_input("world_writable_review", lambda b, r: review_path.chmod(0o666))

        def symlink_review(binding, review):
            linked = ordered / "review-symlink.json"
            linked.symlink_to(review_path)
            binding["review"]["path"] = str(linked)

        bad_input("symlink_review", symlink_review)

        binding, _review = reset_ordered()
        expected = json.loads(encoded(gen.ORDERED_PREDECESSORS))
        # Keep unresolved and UNKNOWN rows exactly under the established history
        # mechanism. An ordered PASS predecessor cannot resolve or replace them.
        for run_id, state in [("unresolved", "sent"), ("unknown", "unknown")]:
            write_json(ordered / "runs" / (run_id + ".json"),
                       {"id": run_id, "deadline": 0, "status": "PREPARED", "send_state": state})
        review_before = (review_path.read_bytes(), review_path.stat().st_mode)
        with contextlib.redirect_stdout(io.StringIO()):
            gen.main()
        doc_o = json.loads(target_o.read_bytes())
        check("ordered_valid_exact_map_emitted", doc_o.get("ordered_predecessors") == expected)
        check("ordered_review_bytes_and_mode_preserved",
              review_before == (review_path.read_bytes(), review_path.stat().st_mode))
        check("ordered_history_and_unknowns_preserved",
              set(doc_o["history"]) == {"unresolved", "unknown"}
              and doc_o["history"]["unknown"]["unknown_retained"] is True
              and doc_o["history"]["unresolved"]["unknown_retained"] is False
              and all(row["new_effect_replay_authorized"] is False for row in doc_o["history"].values())
              and doc_o["unknown_effects_resolved"] is False)
        check("ordered_success_no_temp_leftovers", not list(ordered.glob("*.tmp-*")))
        gen.ORDERED_PREDECESSORS = {}
        with contextlib.redirect_stdout(io.StringIO()):
            gen.main()
        default_doc = json.loads((ordered / "INDEPENDENT-AUTHORITY-R3.json").read_bytes())
        check("ordered_default_empty_field_absent", "ordered_predecessors" not in default_doc)
        check("ordered_default_history_unchanged", default_doc["history"] == doc_o["history"])

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(json.dumps({"checks_failed": failures, "result": "PASS" if not failures else "FAIL"},
                     sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
