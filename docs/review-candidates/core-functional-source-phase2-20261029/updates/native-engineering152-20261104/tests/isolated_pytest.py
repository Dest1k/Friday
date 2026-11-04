#!/usr/bin/env python3
"""Run Source152 regressions without a model, network, child process or coordinator.

This is a test-only launcher. It preserves product decorators and
scope/persistence code; only unrelated baseline accounting is made inert.
Run in a fresh process. No installed or source file is modified.
"""
from __future__ import annotations

import argparse
import contextvars
import functools
import hashlib
import importlib
import json
import operator
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import Mock
from urllib.parse import parse_qs, unquote, urlsplit

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def verify_native(source):
    manifest_path = Path(__file__).resolve().parent.parent / 'NATIVE-FILES.json'
    manifest = json.loads(manifest_path.read_text())
    for item in manifest['files']:
        actual = digest(source / item['path'])
        if actual != item['sha256']:
            raise RuntimeError('Source152 native mismatch: ' + item['path'])
    return digest(manifest_path)


def install_guards(work):
    work = Path(work).resolve(strict=True)
    denied = []
    def fail(event, detail):
        denied.append({'event': event, 'kind': detail})
        raise PermissionError('isolated pytest denied: ' + event + ' (' + detail + ')')

    def descriptor_path(fd, event, *, directory=False):
        # Linux descriptor identity, never the caller's guess about its path.
        # Unlinked descriptors and non-files have no auditable work-tree path.
        try:
            value = os.readlink('/proc/self/fd/' + str(fd))
            if not value.startswith('/') or value.endswith(' (deleted)'):
                fail(event, 'descriptor has no stable private path')
            if directory and not stat.S_ISDIR(os.fstat(fd).st_mode):
                fail(event, 'dir_fd is not a directory')
            resolved = Path(value).resolve(strict=True)
            current = resolved.stat()
            opened = os.fstat(fd)
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                fail(event, 'descriptor path identity changed')
            return resolved
        except (OSError, ValueError):
            fail(event, 'descriptor cannot be resolved')

    def check_path(path, event, dir_fd=None):
        if isinstance(path, int):
            resolved = descriptor_path(path, event)
        else:
            value = os.fsdecode(path)
            target = Path(value)
            if not target.is_absolute() and dir_fd not in (None, -1):
                target = descriptor_path(dir_fd, event, directory=True) / target
            resolved = target.resolve()
        if not resolved.is_relative_to(work):
            fail(event, 'write outside private run directory')

    # CPython's open audit event omits dir_fd. Carry that one native call's
    # directory identity in a private, one-use context instead of changing the
    # path supplied to os.open or allowing arbitrary relative writes.
    native_open = os.open
    open_context = contextvars.ContextVar('isolated_native_open', default=None)
    authority = object()

    @functools.wraps(native_open)
    def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
        path = os.fspath(path)
        # CPython accepts path subclasses but their __eq__ must never execute
        # while authenticating an outstanding native call.
        path = str.__str__(path) if isinstance(path, str) else bytes.__bytes__(path)
        flags, mode = operator.index(flags), operator.index(mode)
        if dir_fd is not None:
            dir_fd = operator.index(dir_fd)
        call = [authority, threading.get_ident(), path, flags, dir_fd, False]
        token = open_context.set(call)
        try:
            return native_open(path, flags, mode, dir_fd=dir_fd)
        finally:
            open_context.reset(token)

    def audit(event, args):
        if event in {'socket.connect', 'socket.connect_ex', 'socket.bind',
                     'socket.sendto', 'socket.getaddrinfo', 'socket.gethostbyname',
                     'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork',
                     'os.forkpty', 'os.exec'}:
            fail(event, 'network or child process')
        if event == 'open':
            path, mode, flags = args
            writing = ((isinstance(mode, str) and any(x in mode for x in 'wax+')) or
                       isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                call = open_context.get()
                authenticated = (
                    call is not None and call[0] is authority
                    and call[1] == threading.get_ident() and not call[5]
                    and mode is None and type(path) is type(call[2])
                    and path == call[2]
                    and flags == (call[3] | os.O_CLOEXEC)
                )
                if authenticated:
                    call[5] = True
                    check_path(path, event, call[4])
                elif (mode is None and not isinstance(path, int)
                      and not Path(os.fsdecode(path)).is_absolute()):
                    fail(event, 'relative open lacks native dir_fd context')
                else:
                    check_path(path, event)
        elif event == 'sqlite3.connect':
            target = os.fsdecode(args[0])
            if target != ':memory:':
                if target.startswith('file:'):
                    uri = urlsplit(target)
                    query = parse_qs(uri.query, strict_parsing=True)
                    # Real SessionDB read pools use local mode=ro URIs.
                    if uri.netloc or uri.fragment or query != {'mode': ['ro']}:
                        fail(event, 'unreviewed SQLite URI options')
                    check_path(unquote(uri.path), event)
                else:
                    check_path(target, event)
        elif event in {'os.remove', 'os.rmdir'}:
            check_path(args[0], event, args[1])
        elif event in {'os.mkdir', 'os.chmod'}:
            check_path(args[0], event, args[2])
        elif event in {'os.chown', 'os.utime'}:
            check_path(args[0], event, args[3])
        elif event in {'os.truncate', 'os.setxattr', 'os.removexattr'}:
            check_path(args[0], event)
        elif event in {'os.rename', 'os.link'}:
            check_path(args[0], event, args[2])
            check_path(args[1], event, args[3])
        elif event == 'os.symlink':
            check_path(args[1], event, args[2])
    sys.addaudithook(audit)
    os.open = guarded_open
    return denied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('test_file')
    parser.add_argument('pytest_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    # Resolve caller-supplied test paths before changing into the native tree.
    args.test_file = str(Path(args.test_file).resolve())
    args.pytest_args = [str(Path(value).resolve()) if value.endswith('.py')
                        and not value.startswith('-') else value
                        for value in args.pytest_args]
    source, work = args.source.resolve(), args.work.resolve()
    if work == source or source in work.parents:
        raise RuntimeError('work must be outside the source tree')
    manifest_sha256 = verify_native(source)
    work.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name in ('home', 'tmp', 'hermes', 'locks', 'xdg-cache', 'xdg-state', 'xdg-config'):
        (work / name).mkdir(mode=0o700)
    # Imports after this point cannot inherit live installation settings/keys.
    for key in list(os.environ):
        if key.startswith(('HERMES_', 'FRIDAY_', 'PYTEST_', 'XDG_')) or any(
            marker in key for marker in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL')):
            os.environ.pop(key, None)
    os.environ.update({
        'HOME': str(work / 'home'), 'HERMES_HOME': str(work / 'hermes'),
        'HERMES_TEST_ISOLATION': str(work / 'hermes'),
        'HERMES_TEST_SANDBOX_HOME': str(work / 'hermes'),
        'HERMES_GATEWAY_LOCK_DIR': str(work / 'locks'),
        'HERMES_DISABLE_LAZY_INSTALLS': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        'FRIDAY_TEST_NATIVE_SOURCE': str(source),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0',
        'TZ': 'UTC', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
        'TMPDIR': str(work / 'tmp'), 'TMP': str(work / 'tmp'), 'TEMP': str(work / 'tmp'),
        'XDG_CACHE_HOME': str(work / 'xdg-cache'),
        'XDG_STATE_HOME': str(work / 'xdg-state'), 'XDG_CONFIG_HOME': str(work / 'xdg-config'),
    })
    sys.dont_write_bytecode = True
    tempfile.tempdir = str(work / 'tmp')
    time.tzset()
    os.chdir(source)
    sys.path.insert(0, str(source))
    started = time.time()
    denied = install_guards(work)
    calls = []
    outcomes = []
    counter = 0
    failure = None
    status = 1
    try:
        # Must happen before run_agent / TurnFacadeMixin is imported.
        bridge = importlib.import_module('agent.friday_baseline_bridge')
        if Path(bridge.__file__).resolve() != source / 'agent/friday_baseline_bridge.py':
            raise RuntimeError('bridge import did not come from selected source')

        def isolated_call(name, *positional, **kwargs):
            nonlocal counter
            counter += 1
            calls.append({'name': name, 'outcome_known': kwargs.get('outcome_known', True)})
            if name == 'begin':
                return 'private-test-token-' + str(counter)
            if name in {'end', 'observe_worker', 'start_worker', 'session_guard_change'}:
                return True
            raise AssertionError('unreviewed baseline bridge call: ' + str(name))

        def denied_load():
            raise AssertionError('real baseline adapter loading is forbidden in unit tests')

        def mocked_physical_create(client, request):
            create = client.chat.completions.create
            if not isinstance(create, Mock):
                calls.append({'name': 'physical_create_denied', 'outcome_known': True})
                raise AssertionError('unit test supplied an unmocked model client')
            calls.append({'name': 'physical_create_mock', 'outcome_known': True})
            return create(**request)

        bridge._call = isolated_call
        bridge._load = denied_load
        bridge.physical_create = mocked_physical_create
        import pytest
        class Reports:
            def pytest_runtest_logreport(self, report):
                if report.when == 'call' or report.failed:
                    outcomes.append({'nodeid': report.nodeid, 'stage': report.when,
                                     'outcome': report.outcome})
        extra = args.pytest_args
        if extra[:1] == ['--']:
            extra = extra[1:]
        status = int(pytest.main([
            args.test_file, '-q', '-p', 'no:cacheprovider',
            '--basetemp', str(work / 'pytest'),
            '--log-file', str(work / 'pytest.log'), *extra,
        ], plugins=[Reports()]))
    except BaseException as exc:
        failure = type(exc).__name__
        traceback.print_exc()
    finally:
        evidence = {
            'schema': 'frw.test-only-isolation.v1', 'source': str(source),
            'test_file': args.test_file, 'pytest_exit_code': status,
            'exception_class': failure, 'elapsed_seconds': time.time() - started,
            'bridge_sha256': digest(source / 'agent/friday_baseline_bridge.py'),
            'native_manifest_sha256': manifest_sha256,
            'native_19_hashes_verified': True,
            'live_coordinator_opened': False,
            'bridge_calls': calls, 'denied_attempts': denied,
            'test_outcomes': outcomes,
            'limits': ['No live effect acceptance; local Python audit fences only.',
                       'A blocked attempt is reported even if product code catches its error.',
                       'These are trusted local regressions, not a hostile-process sandbox.'],
        }
        (work / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
