"""SOURCE-only independent controls; every filesystem fixture is private/synthetic.

No execute_once, run, namespace entry, unit, GDB, or model path is invoked.
The reviewed namespace is compiled into a separate in-memory purefixture module
with its initial WORK literal replaced in that AST only. Guarded reader bodies
remain exact. Small os syscall hooks arrange real file races; no reader is mocked.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import types

SCOPE = Path(__file__).resolve().parent.parent
OUT = SCOPE / 'review'
NAMESPACE = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115/candidate/outer/namespace_entry.py')
PIN = '398c3b883a4d0fcd31032709e71c8e15163cfeaeea4dc999262260047aa2e8bb'
RESULTS = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name, fixture_work=None):
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    if fixture_work is not None:
        changed = 0
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'WORK' for x in node.targets):
                node.value = ast.Call(func=ast.Name(id='Path', ctx=ast.Load()), args=[ast.Constant(str(fixture_work))], keywords=[])
                changed += 1
        assert changed == 1
        tree = ast.fix_missing_locations(tree)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(tree, str(path), 'exec'), module.__dict__)
    return module


def write(path, value, raw=False):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, value if raw else json.dumps(value).encode())
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def replacement(path, value):
    pending = path.with_name(path.name + '.purefixture-new')
    write(pending, value)
    os.replace(pending, path)


def check(name, call, expected=None):
    try:
        value = call()
    except Exception as exc:
        if expected is None or expected not in str(exc):
            raise AssertionError((name, type(exc).__name__, str(exc), expected)) from exc
        RESULTS.append({'name': name, 'result': 'PASS', 'observed': type(exc).__name__ + ':' + str(exc)})
    else:
        if expected is not None:
            raise AssertionError((name, 'unexpected acceptance', value))
        RESULTS.append({'name': name, 'result': 'PASS'})
        return value


def syscall_proxy(module, **overrides):
    original = module.os
    module.os = types.SimpleNamespace(**dict(vars(os), **overrides))
    return original


def main():
    os.umask(0o077)
    assert digest(NAMESPACE) == PIN
    root_path = SCOPE / 'host/ownc_root_controller.py'
    supervisor_path = SCOPE / 'host/ownc_namespace_supervisor.py'
    before_hashes = {str(p): digest(p) for p in (root_path, supervisor_path, NAMESPACE)}
    root = load(root_path, 'purefixture_root_reader_review')
    supervisor = load(supervisor_path, 'purefixture_supervisor_reader_review')
    fixture = Path(tempfile.mkdtemp(prefix='purefixture-', dir=OUT))
    os.chmod(fixture, 0o700)
    try:
        namespace_work = fixture / 'namespace-work'
        namespace_work.mkdir(mode=0o700)
        ns = load(NAMESPACE, 'purefixture_exact_namespace398c', namespace_work)
        host_parent = fixture / 'host-operation'
        host_parent.mkdir(mode=0o700)
        host_work = host_parent / 'work'
        host_work.mkdir(mode=0o700)
        scope = root.host_work_scope(host_work)
        deadline = lambda: time.monotonic() + 5
        for name in ('unit-release.json', 'office-release.json'):
            path = namespace_work / name
            write(path, {'nonce': 'fixture'})
            check('immutable namespace ' + name, lambda p=path: supervisor.wait_file(ns, p, deadline=deadline()))
            check('immutable existing expired ' + name, lambda p=path: supervisor.wait_file(ns, p, deadline=time.monotonic() - 1), 'fixture_existing_deadline_or_exit')
            check('immutable passed mutable mode ' + name, lambda p=path: ns.runtime_read(p, deadline=deadline()), 'runtime_publication_deadline_or_path')

        for name in ('native-trace.json', 'phase.json'):
            path = namespace_work / name
            write(path, {'nonce': 'fixture'})
            check('mutable namespace ' + name, lambda p=path: json.loads(ns.runtime_read(p, deadline=deadline())))
            check('mutable namespace expired ' + name, lambda p=path: ns.runtime_read(p, deadline=time.monotonic() - 1), 'runtime_publication_deadline')

        wrong = host_work / 'unit-release.json'
        write(wrong, {'nonce': 'fixture'})
        check('namespace refuses host pathscope', lambda: ns.runtime_read(wrong), 'exact_work_file_required')
        target = namespace_work / 'unit-release.json'
        for label, setup, expected in (
            ('group writable', lambda: os.chmod(target, 0o620), 'runtime_file_rights'),
            ('hardlink', lambda: os.link(target, namespace_work / 'extra-link'), 'runtime_file_rights'),
            ('symlink', lambda: (target.unlink(), target.symlink_to(namespace_work / 'phase.json')), 'exact_work_file_required'),
        ):
            if target.is_symlink():
                target.unlink()
            write(target, {'nonce': 'fixture'})
            setup()
            check('namespace ' + label, lambda: ns.runtime_read(target), expected)
            if target.is_symlink():
                target.unlink()
            if (namespace_work / 'extra-link').exists():
                (namespace_work / 'extra-link').unlink()
        write(target, b'{"nonce":"a","nonce":"b"}', raw=True)
        check('namespace duplicate JSON at actual wait consumer', lambda: supervisor.wait_file(ns, target, deadline=deadline()), 'fixture_duplicate_json_key')

        def ns_race(name, mutable):
            path = namespace_work / name
            write(path, {'version': 'before'})
            inode = path.stat().st_ino
            used = []
            def racing_fstat(fd):
                st = os.fstat(fd)
                if st.st_ino == inode and not used:
                    used.append(True)
                    replacement(path, {'version': 'after'})
                return st
            original = syscall_proxy(ns, fstat=racing_fstat)
            try:
                return ns.runtime_read(path, deadline=deadline()) if mutable else supervisor.wait_file(ns, path, deadline=deadline())
            finally:
                ns.os = original
        check('immutable namespace inode rewrite refuses', lambda: ns_race('unit-release.json', False), 'runtime_file_changed')
        assert check('mutable namespace retired inode reopens exact successor', lambda: json.loads(ns_race('native-trace.json', True))) == {'version': 'after'}

        ready_path = host_work / 'office-ready.json'
        write(ready_path, {'nonce': 'fixture'})
        check('host private real file', lambda: root.host_record(scope, ready_path.name, deadline=deadline()))
        check('host role path traversal refuses', lambda: root.host_record(scope, '../office-ready.json', deadline=deadline()), 'ownc_host_record_role')
        check('host already expired refuses', lambda: root.host_record(scope, ready_path.name, deadline=time.monotonic() - 1), 'ownc_host_original_deadline')
        for label, setup, expected in (
            ('group writable', lambda: os.chmod(ready_path, 0o620), 'ownc_host_record_rights_bound'),
            ('hardlink', lambda: os.link(ready_path, host_work / 'extra-link'), 'ownc_host_record_rights_bound'),
            ('symlink', lambda: (ready_path.unlink(), ready_path.symlink_to(host_work / 'unit-release.json')), 'Too many levels'),
        ):
            write(ready_path, {'nonce': 'fixture'})
            setup()
            check('host ' + label, lambda: root.host_record(scope, ready_path.name, deadline=deadline()), expected)
            if ready_path.is_symlink():
                ready_path.unlink()
            if (host_work / 'extra-link').exists():
                (host_work / 'extra-link').unlink()
        write(ready_path, b'{"nonce":"a","nonce":"b"}', raw=True)
        check('host duplicate JSON refuses', lambda: root.host_record(scope, ready_path.name, deadline=deadline()), 'ownc_duplicate_json_key')
        write(ready_path, b' ' * 1048577, raw=True)
        check('host 1MiB bound refuses', lambda: root.host_record(scope, ready_path.name, deadline=deadline()), 'ownc_host_record_rights_bound')

        write(ready_path, {'nonce': 'fixture'})
        inode = ready_path.stat().st_ino
        raced = []
        def root_fstat(fd):
            st = os.fstat(fd)
            if st.st_ino == inode and not raced:
                raced.append(True)
                replacement(ready_path, {'nonce': 'replacement'})
            return st
        original = syscall_proxy(root, fstat=root_fstat)
        try:
            check('host inode replacement refuses', lambda: root.host_record(scope, ready_path.name, deadline=deadline()), 'ownc_host_record_changed')
        finally:
            root.os = original

        def late_read(fd, size):
            time.sleep(.02)
            return os.read(fd, size)
        original = syscall_proxy(root, read=late_read)
        try:
            check('host deadline expires during real read', lambda: root.host_record(scope, ready_path.name, deadline=time.monotonic() + .01), 'ownc_host_original_deadline')
        finally:
            root.os = original
        write(target, {'nonce': 'fixture'})
        def late_fstat(fd):
            st = os.fstat(fd)
            time.sleep(.01)
            return st
        original = syscall_proxy(ns, fstat=late_fstat)
        try:
            check('immutable wrapper deadline expires during real read', lambda: supervisor.wait_file(ns, target, deadline=time.monotonic() + .005), 'fixture_existing_deadline_or_exit')
        finally:
            ns.os = original

        plan = {'operation_id': 'purefixture-operation', 'nonce': 'a' * 32,
                'observer': {'config': {'target_sha256': 'b' * 64}}}
        namespaces = {'pid': 'purefixture-ns'}
        native = {'pid': 4, 'start_ticks': 20, 'gdb_pid': 3, 'inferior': 1}
        inside = {'namespaces': namespaces, 'boot_id': 'purefixture-boot', 'ppid': 3, 'executable_sha256': 'b' * 64}
        gd = {'namespaces': namespaces, 'boot_id': 'purefixture-boot', 'start_ticks': 10}
        ready = {'schema': 'frw.calc.office-ready.v1', 'operation_id': plan['operation_id'], 'nonce': plan['nonce'],
                 'scope': 'OWN_C_FIXTURE_ONLY', 'native_symbols': None, 'native_process': native,
                 'office_identity': inside, 'gdb_identity': gd}
        office = {'pid': 104, 'ppid': 103, 'nspid': [104, 4], 'start_ticks': 20, 'namespaces': namespaces, 'boot_id': 'purefixture-boot'}
        gdb = {'pid': 103, 'nspid': [103, 3], 'start_ticks': 10, 'namespaces': namespaces, 'boot_id': 'purefixture-boot'}
        write(ready_path, ready)
        assert check('ready callback real reader and actual map_ready', lambda: root.read_ready(scope, plan, [office, gdb], deadline=deadline())) == (ready, office, gdb)
        write(ready_path, dict(ready, nonce='c' * 32))
        check('ready callback rejects wrong nonce', lambda: root.read_ready(scope, plan, [office, gdb], deadline=deadline()), 'ownc_ready_operation_or_fixture_scope')
        write(ready_path, ready)
        check('ready callback rejects PID birth mismatch', lambda: root.read_ready(scope, plan, [dict(office, start_ticks=21), gdb], deadline=deadline()), 'ownc_host_target_pid_birth_mapping')

        supervisor_result = {'schema': 'frw.own-held-font-fixture-supervisor-result.v1', 'operation_id': plan['operation_id'], 'nonce': plan['nonce']}
        trace = {'schema': 'frw.own-held-font-fixture-trace.v1', 'kind': 'OWN_POPEN_FIXTURE_ONLY', 'nonce': plan['nonce']}
        write(host_work / 'held-fixture-supervisor-result.json', supervisor_result)
        write(host_work / 'native-trace.json', trace)
        closure = ({}, {'populated': 0, 'pids': []})
        monitor = {'status': 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY', 'retirement_snapshot': closure, 'last_snapshot': None,
                   'invocation_id': 'purefixture-invocation', 'cgroup_path': '/purefixture-only'}
        assert check('terminal concrete shape after confirmed empty real readers', lambda: root.read_terminal(scope, plan, monitor, deadline=deadline())) == {'supervisor': supervisor_result, 'trace': trace}
        check('terminal UNKNOWN refuses before real readers', lambda: root.read_terminal(scope, plan, dict(monitor, status='OWNED_CLEANUP_UNKNOWN'), deadline=deadline()), 'ownc_terminal_cgroup_not_confirmed_empty')
        check('terminal populated refuses before real readers', lambda: root.read_terminal(scope, plan, dict(monitor, retirement_snapshot=({}, {'populated': 1, 'pids': [104]})), deadline=deadline()), 'ownc_terminal_cgroup_not_confirmed_empty')
        write(host_work / 'native-trace.json', dict(trace, nonce='c' * 32))
        check('terminal trace rejects nonce', lambda: root.read_terminal(scope, plan, monitor, deadline=deadline()), 'ownc_terminal_trace_operation_join')
        check('terminal postclose original hardend expired', lambda: root.read_terminal(scope, plan, monitor, deadline=time.monotonic() - 1), 'ownc_host_original_deadline')

        changed_work = host_parent / 'retired-work'
        host_work.rename(changed_work)
        host_work.mkdir(mode=0o700)
        write(host_work / 'office-ready.json', ready)
        check('host WORK inode replacement refuses', lambda: root.host_record(scope, ready_path.name, deadline=deadline()), 'ownc_host_work_changed')
    finally:
        shutil.rmtree(fixture)
    after_hashes = {str(p): digest(p) for p in (root_path, supervisor_path, NAMESPACE)}
    assert before_hashes == after_hashes
    report = {'schema': 'frw.ownc-reader-independent-review-controls.v1', 'source_only': True,
              'real_readers': True, 'fixture_namespace_work': 'separate in-memory AST purefixture only',
              'production_sources_unchanged': True, 'reviewed_sha256': before_hashes,
              'controls': RESULTS, 'passed': len(RESULTS), 'fixture_removed': not fixture.exists(),
              'live_effects': False}
    output = OUT / 'real-reader-controls.json'
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    os.chmod(output, 0o600)
    print(json.dumps({'passed': len(RESULTS), 'controls_ref': {'path': str(output), 'sha256': digest(output)}}))


if __name__ == '__main__':
    main()
