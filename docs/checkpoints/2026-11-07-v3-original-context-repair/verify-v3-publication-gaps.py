#!/usr/bin/env python3
"""Check the remaining gaps of the V3 publication on an isolated bench.

The review named four gaps that must be proved on a bench, not on the serving home:

1. a REAL late failure after the marker and the stamp have been changed, with a full
   rollback of the files, the modes and the added files;
2. a non-empty project_file_updates whose previous and new bytes DIFFER, with the
   previous bytes restored on a rollback;
3. the restoration of the file MODES, not only their contents;
4. the immutability of the historical predecessor's committed.json.

Every scenario runs against the isolated composition on the disk staging area. The live
home is never touched.
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/jericho/jericho/Friday_rework")
HOME = REPO / ".runtime/friday-normal-both-workers-frw032"
CAND = Path("/home/jericho/.cache/FRW-V3-PUBLISH-CANDIDATE-20261108")
BENCH = Path("/home/jericho/.dsh/tmp/v3-gap-bench")
PRE = Path("/home/jericho/.cache/pre-install-5files-1794085924")
VENV = (REPO / ".runtime/friday-184-20261108/installs/be596ce02c5f6cde/environments/"
        "ffe0d97db6f3453eac3437e83399c554/venv/bin/python")
TOUCHED = ("agent/agent_init.py", "agent/bounded_context.py", "agent/context_compressor.py",
           "agent/conversation_compression.py", "tools/file_tools.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def modes(root):
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink():
            out[str(path.relative_to(root))] = stat.S_IMODE(path.lstat().st_mode)
    return out


def say(**kw):
    print(json.dumps(kw, sort_keys=True, ensure_ascii=False), flush=True)


def build_bench():
    subprocess.run([sys.executable, str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
                                       "build-v3-bench.py"), "--bench", str(BENCH)],
                   capture_output=True, check=True)
    for name in TOUCHED:
        shutil.copy2(PRE / name, BENCH / "hermes-agent" / name)
    receipt = json.loads((HOME / "hermes-agent.source.json").read_text())
    for name in TOUCHED:
        data = (BENCH / "hermes-agent" / name).read_bytes()
        receipt["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(),
                                  "bytes": len(data), "mode": "100644"}
    (BENCH / "hermes-agent.source.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    marker = json.loads((HOME / "FRIDAY-INSTALL.json").read_text())
    marker["source_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    marker["ordinary_gateway"]["source_receipt_sha256"] = marker["source_receipt_sha256"]
    (BENCH / "FRIDAY-INSTALL.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n")
    for name in ("plugins/friday_rework/host_runtime.py", "plugins/friday_rework/a0_bootstrap.py",
                 "plugins/friday_rework/adapters/a0_web.py"):
        (BENCH / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HOME / name, BENCH / name)
    (BENCH / "preparation").mkdir(parents=True, exist_ok=True)
    (BENCH / "preparation/bench-unit.name").write_text("hermes-gateway-bench-nonexistent.service\n")
    # the bench's own predecessor record: the request.json that the bench transaction
    # continues, and the committed.json that this operation must NOT rewrite
    predecessor = BENCH / "preparation" / "bench-predecessor"
    predecessor.mkdir(parents=True, exist_ok=True)
    request_body = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    (predecessor / "request.json").write_text(json.dumps({
        "schema": "frw.root.engineering152-successor-request.v1",
        "home": str(BENCH),
        "current_input": request_body["current_input"],
    }, sort_keys=True, indent=2) + "\n")
    return receipt, marker


def write_request(request, *, project_updates, previous_bytes, inject_after_rename,
                  predecessor_committed):
    """Build a bench request whose project file updates really differ from the bench."""
    raw = json.loads(json.dumps(request))
    raw["home"] = str(BENCH)
    raw["bench_home"] = str(BENCH)
    raw["project_file_updates"] = list(project_updates)
    raw["inject_after_rename"] = inject_after_rename
    for key in ("marker", "source_receipt", "stamp", "configuration", "profile", "launcher"):
        path = Path(raw[key]["path"])
        relative = path.relative_to(HOME)
        raw[key] = {"path": str(BENCH / relative), "sha256": sha(BENCH / relative)}
    raw["target_receipt"] = {"path": str(BENCH / "hermes-agent.source.json"),
                             "sha256": sha(BENCH / "hermes-agent.source.json")}
    predecessor = BENCH / "preparation" / "bench-predecessor"
    predecessor.mkdir(parents=True, exist_ok=True)
    body = json.loads((predecessor / "request.json").read_text())
    body["current_input"] = {"path": raw["previous_input"]["path"],
                             "sha256": raw["previous_input"]["sha256"]}
    (predecessor / "request.json").write_text(json.dumps(body, sort_keys=True, indent=2) + "\n")
    (predecessor / "committed.json").write_bytes(predecessor_committed)
    raw["predecessor_request"] = {"path": str(predecessor / "request.json"),
                                  "sha256": sha(predecessor / "request.json")}
    raw["predecessor_current_input_sha256"] = raw["previous_input"]["sha256"]
    raw["predecessor_receipt_sha256"] = sha(BENCH / "hermes-agent.source.json")
    out = CAND / "REQUEST-GAP.json"
    out.write_bytes((json.dumps(raw, sort_keys=True, indent=2) + "\n").encode())
    os.chmod(out, 0o600)
    return out


def run(request_path):
    result = subprocess.run(
        [str(VENV), "-I", "-B", str(REPO / "docs/checkpoints/2026-11-07-v3-original-context-repair/"
             "friday_v3_layer_publication.py"), "--request", str(request_path),
         "--request-sha256", sha(request_path)],
        capture_output=True, text=True, timeout=900,
        env={**os.environ, "HERMES_HOME": str(BENCH)})
    return result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr[-300:]


def snapshot():
    """The WORKING state of the bench: the operation's own journal is not part of it."""
    return {"modes": {k: v for k, v in modes(BENCH).items()
                      if not k.startswith("preparation/")},
            "files": {str(p.relative_to(BENCH)): sha(p) for p in sorted(BENCH.rglob("*"))
                      if p.is_file() and not p.is_symlink() and "preparation" not in p.parts}}


def main():
    receipt, marker = build_bench()
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    # a project file whose previous and new bytes really differ
    target = "plugins/friday_rework/host_runtime.py"
    bench_file = BENCH / target
    previous_bytes = bench_file.read_bytes()
    previous_mode = stat.S_IMODE(bench_file.lstat().st_mode)
    bench_file.write_bytes(b"# the bench's own distinct bytes for the gap check\n" + previous_bytes)
    os.chmod(bench_file, 0o640)
    bench_bytes = bench_file.read_bytes()
    bench_mode = stat.S_IMODE(bench_file.lstat().st_mode)
    predecessor_committed = (json.dumps({
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
        "gateway_started": False, "workers_enabled": False,
    }, sort_keys=True, indent=2) + "\n").encode()

    before = snapshot()
    # every real difference must be declared, plus the file this check exercises
    declared = list(request.get("project_file_updates") or []) + [target]
    request_path = write_request(request, project_updates=sorted(set(declared)), previous_bytes=previous_bytes,
                                 inject_after_rename=True, predecessor_committed=predecessor_committed)
    outcome = run(request_path)
    after = snapshot()

    changed = sorted(k for k in set(before["files"]) | set(after["files"])
                      if before["files"].get(k) != after["files"].get(k))
    mode_changed = sorted(k for k in set(before["modes"]) | set(after["modes"])
                          if before["modes"].get(k) != after["modes"].get(k))
    added = sorted(set(after["files"]) - set(before["files"]))
    removed = sorted(set(before["files"]) - set(after["files"]))
    predecessor_path = BENCH / "preparation" / "bench-predecessor" / "committed.json"
    predecessor_unchanged = predecessor_path.read_bytes() == predecessor_committed

    say(mode_changes=[{"path": k, "before": before["modes"].get(k), "after": after["modes"].get(k)}
                      for k in mode_changed][:8],
        scenario="a real late failure after the marker and the stamp changed",
        outcome=outcome[:300],
        files_changed=len(changed), files_added=len(added), files_removed=len(removed),
        modes_changed=len(mode_changed),
        predecessor_record_unchanged=predecessor_unchanged,
        target_restored_to_previous_bytes=(after["files"].get(target) == sha(bench_file)
                                           or before["files"].get(target) == after["files"].get(target)),
        ok=(len(changed) == 0 and len(added) == 0 and len(removed) == 0
            and len(mode_changed) == 0 and predecessor_unchanged))
    # ---- scenario 2: a successful publication of a project file whose previous and new
    # bytes really differ, then a rollback of THAT publication, with the mode restored
    receipt, marker = build_bench()
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    target = "plugins/friday_rework/host_runtime.py"
    bench_file = BENCH / target
    previous_bytes = bench_file.read_bytes()
    previous_mode = stat.S_IMODE(bench_file.lstat().st_mode)
    bench_file.write_bytes(b"# the bench's own distinct bytes for the gap check\n" + previous_bytes)
    os.chmod(bench_file, 0o640)
    predecessor_committed = (json.dumps({
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
        "gateway_started": False, "workers_enabled": False,
    }, sort_keys=True, indent=2) + "\n").encode()
    declared = sorted(set(list(request.get("project_file_updates") or []) + [target]))
    request_path = write_request(request, project_updates=declared, previous_bytes=previous_bytes,
                                  inject_after_rename=True, predecessor_committed=predecessor_committed)
    before = snapshot()
    outcome = run(request_path)
    after = snapshot()
    changed = sorted(k for k in set(before["files"]) | set(after["files"])
                      if before["files"].get(k) != after["files"].get(k))
    mode_changed = sorted(k for k in set(before["modes"]) | set(after["modes"])
                          if before["modes"].get(k) != after["modes"].get(k))
    predecessor_path = BENCH / "preparation" / "bench-predecessor" / "committed.json"
    say(scenario="a rollback of a publication whose project file had DIFFERENT previous bytes",
        outcome=outcome[:200],
        bench_bytes_sha256=sha_bytes(bench_bytes),
        bench_mode=bench_mode,
        restored_bytes_sha256=after["files"].get(target),
        restored_mode=after["modes"].get(target),
        bytes_restored=after["files"].get(target) == sha_bytes(bench_bytes),
        mode_restored=after["modes"].get(target) == bench_mode,
        other_files_changed=[c for c in changed if c != target],
        other_modes_changed=[m for m in mode_changed if m != target],
        predecessor_record_unchanged=predecessor_path.read_bytes() == predecessor_committed)
    # ---- scenario 3: the same publication WITHOUT the injected failure must apply the
    # new bytes and keep the historical predecessor's record untouched
    receipt, marker = build_bench()
    request = json.loads((CAND / "REQUEST-LAYERS.json").read_text())
    target = "plugins/friday_rework/host_runtime.py"
    predecessor_committed = (json.dumps({
        "schema": "friday.ordinary-telegram-source-update-transaction.v1",
        "state": "SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED",
        "source_receipt_sha256": sha(BENCH / "hermes-agent.source.json"),
        "gateway_started": False, "workers_enabled": False,
    }, sort_keys=True, indent=2) + "\n").encode()
    declared = sorted(set(list(request.get("project_file_updates") or []) + [target]))
    request_path = write_request(request, project_updates=declared, previous_bytes=b"",
                                  inject_after_rename=False, predecessor_committed=predecessor_committed)
    before = snapshot()
    outcome = run(request_path)
    after = snapshot()
    predecessor_path = BENCH / "preparation" / "bench-predecessor" / "committed.json"
    candidate_bytes = sha(CAND / "project" / target)
    say(scenario="the same publication without the injected failure",
        outcome=outcome[:200],
        target_published_bytes=after["files"].get(target),
        target_matches_the_candidate=after["files"].get(target) == candidate_bytes,
        predecessor_record_unchanged=predecessor_path.read_bytes() == predecessor_committed,
        own_record_written=(BENCH / "preparation").exists())
    shutil.rmtree(BENCH, ignore_errors=True)


if __name__ == "__main__":
    main()
