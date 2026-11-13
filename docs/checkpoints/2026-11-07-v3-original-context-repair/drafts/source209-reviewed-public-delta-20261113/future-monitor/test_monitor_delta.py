"""Own-filesystem and injected controls; AST-load only selected inert functions."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time
import types
from unittest.mock import patch

D = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-PRESENTATION-DISK-MONITOR-ATTRIBUTION-20261113')
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113/source/root_f07_once.py')
SOURCE = D / 'source/root_f07_once.py'
FUNCTIONS = {'need', 'canonical_path', 'disk_monitor_failure', 'scan_scope', 'charge_growth', 'remaining', 'stop_reap', 'wait_owned'}
CONSTANTS = {'DISK_MONITOR_ENUMS', 'DISK_MONITOR_STAGES'}


def load_selected(raw, label):
    tree = ast.parse(raw)
    selected = [n for n in tree.body if
                isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS or
                isinstance(n, ast.ClassDef) and n.name == 'StopUnconfirmed' or
                isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in CONSTANTS for t in n.targets)]
    module = types.ModuleType(label)
    module.__dict__.update(Path=Path, time=time, os=os, stat=stat, signal=signal, subprocess=subprocess)
    exec(compile(ast.Module(body=selected, type_ignores=[]), label, 'exec'), module.__dict__)
    return module


def scope(path, maximum=50000):
    return dict(directory_roots=[str(path)], file_paths=[], max_entries=maximum, sample_seconds=0.02)


def scan_refusal(module, current_scope, expected, *, deadline=None):
    failure = {}
    try:
        module.scan_scope(current_scope, deadline=time.monotonic() + 2 if deadline is None else deadline, failure=failure)
    except Exception:
        pass
    else:
        raise AssertionError('expected refusal')
    assert failure['enum'] == expected, failure
    return failure


def child(code, *args):
    return subprocess.Popen([sys.executable, '-I', '-B', '-S', '-c', code, *map(str, args)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    raw, oldraw = SOURCE.read_bytes(), ORIGINAL.read_bytes()
    assert hashlib.sha256(oldraw).hexdigest() == 'e40343ca212f551d62e842879485f039fbfc6bfb0d9e6777b64776e9eb832ce0'
    h, old = load_selected(raw, 'future_monitor_delta'), load_selected(oldraw, 'pinned_original_monitor')
    original_ast, future_ast = ast.parse(oldraw), ast.parse(raw)
    old_nodes = {n.name: n for n in original_ast.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    new_nodes = {n.name: n for n in future_ast.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    unchanged = [name for name in old_nodes if name not in {'scan_scope', 'wait_owned'}]
    assert all(ast.dump(old_nodes[name], include_attributes=False) == ast.dump(new_nodes[name], include_attributes=False) for name in unchanged)
    assert len(future_ast.body) == len(original_ast.body) + 3
    work = D / 'control-fixtures'
    work.mkdir(mode=0o700)
    checks, actors = [], []
    started = time.monotonic()
    try:
        base = work / 'normal-files'
        base.mkdir(mode=0o700)
        (base / 'one').write_bytes(b'x' * 64)
        os.link(base / 'one', base / 'same-inode')
        current_scope = scope(base)
        new_rows = h.scan_scope(current_scope, deadline=time.monotonic() + 2)
        old_rows = old.scan_scope(current_scope, deadline=time.monotonic() + 2)
        assert old_rows == new_rows and len(new_rows) == 1 and sum(new_rows.values()) == 64
        checks.append('REAL_NORMAL_SCAN_AND_HARDLINK_DEDUP_MATCH_ORIGINAL')

        missing_scope = dict(current_scope, file_paths=[str(base / 'missing')])
        assert h.scan_scope(missing_scope, deadline=time.monotonic() + 2) == new_rows
        checks.append('INITIAL_MISSING_PATH_SKIP_UNCHANGED')

        linkbase = work / 'link-refusal'
        linkbase.mkdir(mode=0o700)
        target = work / 'target'
        target.write_bytes(b'own-fixture-only')
        link = linkbase / 'not-followed'
        link.symlink_to(target)
        failure = scan_refusal(h, scope(linkbase), 'F07_OPERATION_WRITE_SCOPE_LINK_RECONCILE_ONLY')
        assert failure['exception_class'] == 'ValueError' and failure['stage'] == 'SCAN_ENTRY_LINK_GUARD' and failure['path'] == str(link)
        checks.append('REAL_SYMLINK_GUARD_REFUSES_WITH_EXACT_PATH_NO_BYPASS')

        specialbase = work / 'special-refusal'
        specialbase.mkdir(mode=0o700)
        fifo = specialbase / 'own-fifo'
        os.mkfifo(fifo, 0o600)
        failure = scan_refusal(h, scope(specialbase), 'F07_WRITE_SCOPE_SPECIAL_FILE')
        assert failure['stage'] == 'SCAN_ENTRY_TYPE_GUARD' and failure['path'] == str(fifo)
        checks.append('REAL_FIFO_GUARD_REFUSES_WITHOUT_OPENING_BODY')

        deadline_failure = scan_refusal(h, current_scope, 'F07_DISK_SCAN_OUTER_DEADLINE', deadline=time.monotonic() - 1)
        assert deadline_failure['stage'] == 'SCAN_ENTRY_DEADLINE' and deadline_failure['entries'] == 0
        bound_failure = scan_refusal(h, scope(base, 1), 'F07_DISK_SCOPE_ENTRY_BOUND')
        assert bound_failure['entries'] == 2
        checks.append('DEADLINE_AND_ENTRY_CAP_GUARDS_UNCHANGED')

        lstat = Path.lstat
        def denied(path, *args, **kwargs):
            if path == base / 'one':
                raise PermissionError(13, 'INJECTED_MESSAGE_MUST_NEVER_BE_SERIALIZED', 'INJECTED_OTHER_FILENAME')
            return lstat(path, *args, **kwargs)
        with patch.object(Path, 'lstat', denied):
            failure = scan_refusal(h, current_scope, 'F07_DISK_MONITOR_OS_ERROR')
        assert failure['exception_class'] == 'PermissionError' and failure['errno'] == 13
        assert failure['path'] == str(base / 'one') and failure['stage'] == 'SCAN_ENTRY_LSTAT'
        assert 'INJECTED_' not in json.dumps(failure)
        checks.append('INJECTED_LSTAT_DENIAL_CLASS_ERRNO_PATH_RETAINED_MESSAGE_OMITTED')

        scandir = os.scandir
        def denied_open(path):
            if Path(path) == base:
                raise PermissionError(13, 'INJECTED_MESSAGE_MUST_NEVER_BE_SERIALIZED')
            return scandir(path)
        with patch.object(os, 'scandir', denied_open):
            failure = scan_refusal(h, current_scope, 'F07_DISK_MONITOR_OS_ERROR')
        assert failure['stage'] == 'SCAN_DIRECTORY_OPEN' and failure['path'] == str(base)
        checks.append('INJECTED_DIRECTORY_OPEN_DENIAL_LOCATION_RETAINED')

        class RefusingIterator:
            def __enter__(self):
                return iter(self)
            def __exit__(self, *unused):
                return False
            def __iter__(self):
                return self
            def __next__(self):
                raise OSError(5, 'INJECTED_MESSAGE_MUST_NEVER_BE_SERIALIZED')
        with patch.object(os, 'scandir', lambda path: RefusingIterator()):
            failure = scan_refusal(h, current_scope, 'F07_DISK_MONITOR_OS_ERROR')
        assert failure['stage'] == 'SCAN_DIRECTORY_NEXT' and failure['path'] == str(base)
        checks.append('INJECTED_DIRECTORY_ITERATION_REFUSAL_LOCATION_RETAINED')

        class PrivateExceptionName(Exception):
            pass
        failure = h.disk_monitor_failure(PrivateExceptionName('INJECTED_MESSAGE'), stage='INJECTED_STAGE', path='x' * 5000, entries=100002)
        assert failure == dict(exception_class='OTHER_EXCEPTION', enum='F07_DISK_MONITOR_UNCLASSIFIED_EXCEPTION', errno=None,
                              stage='MONITOR_BLOCK', path=None, path_status='OMITTED_OVER_BOUND', path_chars=5000, entries=None)
        assert 'INJECTED' not in json.dumps(failure) and 'PrivateExceptionName' not in json.dumps(failure)
        assert h.disk_monitor_failure(ValueError('INJECTED_MESSAGE'), stage='MONITOR_BLOCK')['enum'] == 'F07_DISK_MONITOR_UNCLASSIFIED_EXCEPTION'
        checks.append('ALLOWLISTED_ENUM_CLASS_STAGE_AND_PATH_BOUNDS_NO_ARBITRARY_TEXT')

        # Actual owned child: monitor refuses before sleeping; both refusal
        # samples survive and unchanged stop_reap must signal and reap it.
        actor = child('import time; time.sleep(20)')
        actors.append(actor)
        lifetime = dict(cleanup_attempted=False)
        clock = dict(deadline_monotonic=time.monotonic() + 12)
        result = h.wait_owned(actor, clock, scope(linkbase), {}, 4096, [], lifetime)
        assert result['stop_reason'] == 'AGGREGATE_DISK_MONITOR_REFUSED'
        assert result['monitor_failure']['path'] == str(link) and result['final_monitor_failure']['path'] == str(link)
        assert result['cleanup_signals'] == [int(signal.SIGINT)] and lifetime['cleanup_attempted']
        assert actor.poll() is not None and actor.wait(timeout=0) == result['exit_code']
        assert result['samples'] == 0 and result['observed_new_bytes_highwater'] == 0 and result['aggregate_cap_bytes'] == 4096
        checks.append('REAL_OWNED_CHILD_SCAN_REFUSAL_SIGINT_REAP_BOTH_FAILURES_RETAINED')

        # Real regular growth and natural owned exit, with no cleanup signal.
        growthbase = work / 'normal-owned-growth'
        growthbase.mkdir(mode=0o700)
        growthscope = scope(growthbase)
        baseline = h.scan_scope(growthscope, deadline=time.monotonic() + 2)
        actor = child('import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_bytes(b"x"*256); time.sleep(0.15)', growthbase / 'new-file')
        actors.append(actor)
        result = h.wait_owned(actor, dict(deadline_monotonic=time.monotonic() + 12), growthscope, baseline, 4096, [])
        assert result['exit_code'] == 0 and result['stop_reason'] is None and result['cleanup_signals'] == []
        assert result['monitor_failure'] is None and result['final_monitor_failure'] is None
        assert result['observed_new_bytes_highwater'] == 256 and result['samples'] >= 2
        assert result['hard_filesystem_quota'] is False
        checks.append('REAL_OWNED_NORMAL_GROWTH_SAMPLING_NATURAL_EXIT_CAP_ACCOUNTING_UNCHANGED')

        # Final-only failure after a separately created child's natural exit.
        actor = child('pass')
        actors.append(actor)
        actor.wait(timeout=2)
        with patch.object(os, 'scandir', denied_open):
            result = h.wait_owned(actor, dict(deadline_monotonic=time.monotonic() + 12), current_scope, {}, 4096, [])
        assert result['stop_reason'] == 'FINAL_DISK_SAMPLE_NOT_ESTABLISHED' and result['monitor_failure'] is None
        assert result['final_monitor_failure']['stage'] == 'SCAN_DIRECTORY_OPEN' and result['cleanup_signals'] == []
        checks.append('FINAL_ONLY_REFUSAL_SEPARATE_RECORD_NO_NEW_CLEANUP')

        # Accounting exceptions also retain a fixed location, without a fake
        # filesystem path; actual owned child cleanup remains required.
        actor = child('import time; time.sleep(20)')
        actors.append(actor)
        def bad_charge(*args):
            raise RuntimeError('INJECTED_MESSAGE_MUST_NEVER_BE_SERIALIZED')
        with patch.object(h, 'charge_growth', bad_charge):
            result = h.wait_owned(actor, dict(deadline_monotonic=time.monotonic() + 12), current_scope, {}, 4096, [])
        assert result['monitor_failure']['stage'] == 'CHARGE_GROWTH' and result['monitor_failure']['path'] is None
        assert result['final_monitor_failure']['stage'] == 'CHARGE_GROWTH'
        assert result['cleanup_signals'] == [int(signal.SIGINT)] and actor.poll() is not None
        assert 'INJECTED_' not in json.dumps(result)
        checks.append('INJECTED_ACCOUNTING_FAILURE_LOCATION_RETAINED_OWNED_CHILD_REAPED')

        assert ORIGINAL.read_bytes() == oldraw
        assert all(actor.poll() is not None for actor in actors)
        report = dict(status='PASS', schema='frw.Root.F04.future-monitor-diagnostic-controls.v1',
                      source_sha256=hashlib.sha256(raw).hexdigest(), original_sha256=hashlib.sha256(oldraw).hexdigest(),
                      checks=checks, checks_count=len(checks), elapsed_seconds=time.monotonic() - started,
                      unchanged_original_functions_and_classes=len(unchanged), original_unchanged=True,
                      own_children_created=len(actors), own_children_reaped=len(actors), own_fixtures_removed=True,
                      original_operation_replayed=False, product_effects=False, user_file_bodies_read=False)
    finally:
        for actor in actors:
            if actor.poll() is None:
                actor.kill()
                actor.wait(timeout=2)
        shutil.rmtree(work)
    raw_report = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    with os.fdopen(os.open(D / 'FUTURE-DELTA-CONTROLS.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as out:
        out.write(raw_report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
