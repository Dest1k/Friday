"""Source-only tiny-file controls; no Office/UNO/native actor or namespace use."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'candidate/inner/inner_client.py'
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-CALC-FONT-ENV-REVIEWED-ROOT-20261115/candidate/inner/inner_client.py')
spec = importlib.util.spec_from_file_location('controlled_inner', SOURCE)
inner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inner)


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


class ReaderControls(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='case-', dir=ROOT / 'inner-reader-tests'))
        self.old_work = inner.WORK
        inner.WORK = str(self.work)
        self.trace = self.work / 'native-trace.json'
        self.serial = 0
        self.publish(b'{"old":1}\n')

    def tearDown(self):
        inner.WORK = self.old_work
        shutil.rmtree(self.work)

    def publish(self, raw, mode=0o600):
        self.serial += 1
        pending = self.work / ('pending-' + str(self.serial))
        pending.write_bytes(raw)
        pending.chmod(mode)
        os.replace(pending, self.trace)

    def read(self, **kw):
        return inner.active_trace_bytes(str(self.trace), deadline=time.monotonic() + 1, **kw)

    def assert_refused(self, action, reason=None):
        with self.assertRaises(inner.Refused) as caught:
            action()
        if reason is not None:
            self.assertEqual(str(caught.exception), reason)

    def swap_on_open(self, replacement):
        original_open = os.open
        calls = []
        def opened(path, flags, *args, **kwargs):
            fd = original_open(path, flags, *args, **kwargs)
            if os.fspath(path) == str(self.trace):
                calls.append(fd)
                if len(calls) == 1:
                    replacement()
            return fd
        return patch.object(inner.os, 'open', opened), calls

    def change_on_read(self, change):
        original_read = os.read
        calls = []
        def read(fd, count):
            raw = original_read(fd, count)
            calls.append(raw)
            if len(calls) == 1:
                change()
            return raw
        return patch.object(inner.os, 'read', read), calls

    def test_private_0400_and_0600(self):
        for mode in (0o400, 0o600):
            with self.subTest(mode=oct(mode)):
                self.trace.chmod(mode)
                self.assertEqual(self.read(), b'{"old":1}\n')

    def test_replace_after_open_before_initial_fstat(self):
        control, calls = self.swap_on_open(lambda: self.publish(b'{"new":2}\n'))
        with control:
            self.assertEqual(self.read(), b'{"new":2}\n')
        self.assertEqual(len(calls), 2)

    def test_replace_during_tiny_read_discards_old_bytes(self):
        control, calls = self.change_on_read(lambda: self.publish(b'{"new":2}\n'))
        with control:
            self.assertEqual(self.read(), b'{"new":2}\n')
        self.assertIn(b'{"old":1}\n', calls)
        self.assertIn(b'{"new":2}\n', calls)

    def test_replace_between_final_fstat_and_path_check(self):
        original_stat = Path.stat
        checks = []
        def stat_path(path, *args, **kwargs):
            if path == self.trace:
                checks.append(path)
                if len(checks) == 2:
                    self.publish(b'{"new":2}\n')
            return original_stat(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat_path):
            self.assertEqual(self.read(), b'{"new":2}\n')
        self.assertEqual(len(checks), 4)

    def test_different_inode_with_old_fd_still_linked_refuses(self):
        def change():
            os.rename(self.trace, self.work / 'still-linked.json')
            self.publish(b'{"new":2}\n')
        control, _ = self.change_on_read(change)
        with control:
            self.assert_refused(self.read, 'file_changed_during_read')

    def test_missing_successor_does_not_retry(self):
        control, calls = self.change_on_read(self.trace.unlink)
        with control:
            self.assert_refused(self.read, 'native_trace_path_missing_during_read')
        self.assertEqual(len(calls), 2)

    def test_insecure_replacement_does_not_retry(self):
        control, calls = self.change_on_read(lambda: self.publish(b'{"new":2}\n', 0o644))
        with control:
            self.assert_refused(self.read, 'protected_file_required')
        self.assertEqual(len(calls), 2)

    def test_truncation_growth_and_same_size_mutation_refuse(self):
        for raw in (b'', b'{"much-longer":true}\n', b'{"new":2}\n'):
            with self.subTest(raw=raw):
                self.publish(b'{"old":1}\n')
                before = self.trace.stat()
                def mutate():
                    self.trace.write_bytes(raw)
                    os.utime(self.trace, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000))
                control, _ = self.change_on_read(mutate)
                with control:
                    self.assert_refused(self.read, 'file_changed_during_read')

    def test_mutation_then_atomic_replace_is_not_excused(self):
        before = self.trace.stat()
        def mutate_and_replace():
            self.trace.write_bytes(b'{"bad":0}\n')
            os.utime(self.trace, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000))
            self.publish(b'{"new":2}\n')
        control, _ = self.change_on_read(mutate_and_replace)
        with control:
            self.assert_refused(self.read, 'file_changed_during_read')

    def test_permissions_hardlink_size_uid_and_wrong_path_refuse(self):
        for mode in (0o640, 0o644, 0o666):
            self.trace.chmod(mode)
            self.assert_refused(self.read, 'protected_file_required')
        self.trace.chmod(0o600)
        os.link(self.trace, self.work / 'extra-link')
        self.assert_refused(self.read, 'protected_file_required')
        (self.work / 'extra-link').unlink()
        self.assert_refused(lambda: self.read(limit=1), 'protected_file_required')
        with patch.object(inner.os, 'getuid', return_value=os.getuid() + 1):
            self.assert_refused(self.read, 'protected_file_required')
        self.assert_refused(lambda: inner.active_trace_bytes(str(self.work / 'other.json'),
                            deadline=time.monotonic() + 1), 'active_native_trace_path_required')

    def test_symlink_and_directory_refuse(self):
        self.trace.unlink()
        self.trace.symlink_to(self.work / 'uncreated')
        with self.assertRaises(OSError):
            self.read()
        self.trace.unlink()
        self.trace.mkdir(mode=0o700)
        self.assert_refused(self.read, 'protected_file_required')

    def test_fifo_refuses_without_blocking(self):
        self.trace.unlink()
        os.mkfifo(self.trace, 0o600)
        script = ('import importlib.util,sys,time;sys.dont_write_bytecode=True;'
                  's=importlib.util.spec_from_file_location("inner",sys.argv[1]);'
                  'm=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.WORK=sys.argv[2];'
                  '\ntry:m.active_trace_bytes(m.WORK+"/native-trace.json",deadline=time.monotonic()+1)'
                  '\nexcept m.Refused as e:assert str(e)=="protected_file_required"'
                  '\nelse:raise AssertionError("FIFO accepted")')
        result = subprocess.run([sys.executable, '-I', '-B', '-S', '-c', script, str(SOURCE), str(self.work)],
                                capture_output=True, timeout=2)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_mode_and_link_mutation_during_read_refuse(self):
        for kind in ('mode', 'link'):
            with self.subTest(kind=kind):
                self.publish(b'{"old":1}\n')
                change = (lambda: self.trace.chmod(0o400)) if kind == 'mode' else (
                    lambda: os.link(self.trace, self.work / 'extra-link'))
                control, _ = self.change_on_read(change)
                with control:
                    self.assert_refused(self.read)
                if kind == 'link':
                    (self.work / 'extra-link').unlink()

    def test_io_error_is_not_a_retry(self):
        with patch.object(inner.os, 'read', side_effect=PermissionError('controlled')) as read:
            with self.assertRaises(PermissionError):
                self.read()
        self.assertEqual(read.call_count, 1)

    def test_max_eight_verified_replacements(self):
        original_open = os.open
        count = []
        def opened(path, flags, *args, **kwargs):
            fd = original_open(path, flags, *args, **kwargs)
            if os.fspath(path) == str(self.trace):
                count.append(fd)
                self.publish(b'{"new":2}\n')
            return fd
        with patch.object(inner.os, 'open', opened):
            self.assert_refused(self.read, 'native_trace_replacement_retry_limit')
        self.assertEqual(len(count), 8)

    def test_one_absolute_deadline_through_replacement_retries(self):
        clock = Clock()
        original_open = os.open
        count = []
        def opened(path, flags, *args, **kwargs):
            fd = original_open(path, flags, *args, **kwargs)
            if os.fspath(path) == str(self.trace):
                count.append(fd)
                clock.now += 0.4
                self.publish(b'{"new":2}\n')
            return fd
        with patch.object(inner.time, 'monotonic', clock.monotonic), patch.object(inner.os, 'open', opened):
            self.assert_refused(lambda: inner.active_trace_bytes(str(self.trace), deadline=101),
                                'bounded_metadata_wait_expired')
        self.assertEqual(len(count), 3)

    def test_expired_or_nonfinite_deadline_refuses_before_open(self):
        with patch.object(inner.os, 'open') as opened:
            for deadline in (0, -1, float('inf'), float('nan'), True):
                self.assert_refused(lambda: inner.active_trace_bytes(str(self.trace), deadline=deadline),
                                    'absolute_metadata_deadline_required')
            self.assert_refused(lambda: inner.active_trace_bytes(str(self.trace), deadline=time.monotonic() - 1),
                                'bounded_metadata_wait_expired')
        opened.assert_not_called()

    def ready(self):
        return dict(schema='frw.native-return-trace.v1', nonce='a' * 32,
                    kind='OFFICE_UNADMITTED', status='READY_UNRELEASED', error=None,
                    records=[], process=dict(pid=17, start_ticks=23))

    def config(self):
        ref = dict(path=str(self.work / 'inert.py'), sha256='1' * 64)
        return dict(schema=inner.SCHEMA, operation_id='inert-control', nonce='a' * 32,
            pipe_name='inert_private_pipe_123', office_process=dict(namespace_pid=17,
                start_ticks=23, executable_sha256='2' * 64),
            modules={k: copy.deepcopy(ref) for k in ('qualifier', 'resolver', 'leaf')},
            preload=copy.deepcopy(ref), handler_source_ref=copy.deepcopy(ref),
            uno=dict(search_paths=[str(self.work / x) for x in ('a', 'b', 'c')],
                files=[dict(path=str(self.work / x), sha256='3' * 64)
                       for x in ('uno.py', 'unohelper.py', 'pyuno.so', 'libpyuno.so')]),
            paths=dict(work=str(self.work), phase=str(self.work / 'phase.json'), trace=str(self.trace),
                checkpoint=str(self.work / 'checkpoint.json'), loaded_envelope=str(self.work / 'loaded.json'),
                started=str(self.work / 'started.json')),
            timeouts=dict(connect_seconds=1, loaded_seconds=1, ready_seconds=1))

    def test_wait_json_and_verify_ready_use_fresh_successor(self):
        ready = self.ready()
        self.publish(inner.canonical(dict(ready, status='STARTING')))
        control, _ = self.change_on_read(lambda: self.publish(inner.canonical(ready)))
        with control:
            value = inner.wait_json(str(self.trace), 1, lambda v: inner.verify_ready(v, self.config()),
                                    active_trace=True)
        self.assertEqual(value, ready)

    def test_readiness_identity_state_and_json_refusals_preserved(self):
        good = self.ready()
        for update in ({'nonce': 'b' * 32}, {'schema': 'wrong'}, {'kind': 'wrong'},
                       {'status': 'REFUSED'}, {'status': 'UNKNOWN'}, {'error': 'controlled'},
                       {'process': dict(pid=18, start_ticks=23)}, {'records': [{}]}):
            with self.subTest(update=update):
                self.publish(inner.canonical(dict(good, **update)))
                self.assert_refused(lambda: inner.wait_json(str(self.trace), 1,
                    lambda v: inner.verify_ready(v, self.config()), active_trace=True))
        for raw, error in ((b'{"x":1,"x":2}', inner.Refused),
                           (b'{"x":NaN}', inner.Refused), (b'{', json.JSONDecodeError)):
            self.publish(raw)
            with self.assertRaises(error):
                inner.wait_json(str(self.trace), 1, lambda v: True, active_trace=True)

    def test_replacement_does_not_excuse_readiness_refusals(self):
        good = self.ready()
        for update in ({'nonce': 'b' * 32}, {'schema': 'wrong'}, {'kind': 'wrong'},
                       {'status': 'REFUSED'}, {'status': 'UNKNOWN'}, {'error': 'controlled'},
                       {'process': dict(pid=18, start_ticks=23)}, {'records': [{}]}):
            with self.subTest(update=update):
                self.publish(inner.canonical(good))
                bad = dict(good, **update)
                control, calls = self.change_on_read(lambda: self.publish(inner.canonical(bad)))
                with control:
                    self.assert_refused(lambda: inner.wait_json(str(self.trace), 1,
                        lambda v: inner.verify_ready(v, self.config()), active_trace=True))
                self.assertIn(inner.canonical(bad), calls)

    def test_waits_share_absolute_deadline_instead_of_resetting(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                clock = Clock()
                if missing:
                    self.trace.unlink()
                else:
                    self.publish(inner.canonical(dict(self.ready(), status='STARTING')))
                with patch.object(inner.time, 'monotonic', clock.monotonic), patch.object(inner.time, 'sleep', clock.sleep):
                    self.assert_refused(lambda: inner.wait_json(str(self.trace), 1,
                        lambda v: inner.verify_ready(v, self.config()), active_trace=True, deadline=100.06),
                        'bounded_metadata_wait_expired')
                self.assertAlmostEqual(clock.now, 100.06)
                self.assertEqual(len(clock.sleeps), 3)

    def test_success_after_deadline_is_not_accepted(self):
        clock = Clock()
        self.publish(inner.canonical(self.ready()))
        def predicate(value):
            clock.now = 102
            return True
        with patch.object(inner.time, 'monotonic', clock.monotonic):
            self.assert_refused(lambda: inner.wait_json(str(self.trace), 1, predicate, active_trace=True),
                                'bounded_metadata_wait_expired')

    def test_deadline_expiring_during_final_path_check_refuses(self):
        clock = Clock()
        original_stat = Path.stat
        checks = []
        def stat_path(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if path == self.trace:
                checks.append(path)
                if len(checks) == 2:
                    clock.now = 102
            return result
        with patch.object(inner.time, 'monotonic', clock.monotonic), patch.object(Path, 'stat', stat_path):
            self.assert_refused(lambda: inner.active_trace_bytes(str(self.trace), deadline=101),
                                'bounded_metadata_wait_expired')

    def test_immutable_reader_is_unchanged_and_does_not_retry(self):
        def function_source(path, name):
            text = path.read_text()
            node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
            return ast.get_source_segment(text, node)
        self.assertEqual(function_source(SOURCE, 'protected_bytes'), function_source(ORIGINAL, 'protected_bytes'))
        raw = self.trace.read_bytes()
        pin = hashlib.sha256(raw).hexdigest()
        self.assertEqual(inner.protected_bytes(str(self.trace), pin), raw)
        self.assert_refused(lambda: inner.protected_bytes(str(self.trace), 'f' * 64), 'file_pin_changed')
        control, calls = self.swap_on_open(lambda: self.publish(b'{"new":2}\n'))
        with control:
            self.assert_refused(lambda: inner.protected_bytes(str(self.trace), pin), 'protected_file_required')
        self.assertEqual(len(calls), 1)
        self.publish(raw)
        control, _ = self.change_on_read(lambda: self.publish(b'{"new":2}\n'))
        with control:
            self.assert_refused(lambda: inner.protected_bytes(str(self.trace), pin), 'file_changed_during_read')
        # Generic loaded-envelope/accepted metadata keeps the strict reader.
        self.publish(b'{"old":1}\n')
        control, _ = self.change_on_read(lambda: self.publish(b'{"new":2}\n'))
        with control:
            self.assert_refused(lambda: inner.wait_json(str(self.trace), 1, lambda v: True),
                                'file_changed_during_read')

    def test_execute_inner_two_readiness_phases_each_cap_original_deadline(self):
        clock = Clock()
        c = self.config()
        c['load_dependency'] = dict(operation_id=c['operation_id'], nonce=c['nonce'], source_sha256='4' * 64,
            manifest_ref=dict(path=str(self.work / 'manifest.json'), sha256='5' * 64),
            marker_path=str(self.work / 'load-dependency.json'), operation_deadline_monotonic=105.5)
        pre = dict(source=dict(sha256='4' * 64), working_copy=dict(url='file:///inert-control.ods'))
        self.publish(inner.canonical(self.ready()))
        class Handler:
            requests = 0
            instance_token = 'inert-handler'
        class Doc:
            def close(self, ownership):
                return None
        class Desktop:
            def loadComponentFromURL(self, *args):
                clock.now = 105.0  # Legitimate load exceeds the first ready budget.
                return Doc()
            def terminate(self):
                return True
        handler = Handler()
        def loaded(config, preload, modules):
            return (dict(load_request=dict(url=pre['working_copy']['url'], scalar_arguments=inner.SCALARS.copy(),
                interaction_requests=0, interaction_handler=dict(argument_name='InteractionHandler', kind='ABORT_ONLY',
                    instance_token=handler.instance_token, source_ref=c['handler_source_ref'])),
                process=dict(pid=17, start_ticks=23, executable_sha256='2' * 64),
                startup_locale_environment=None, native_transport=dict(mode='RAW32_POSTQUERY_NATIVE_JOIN')), '6' * 64)
        def stop_before_query(*args, **kwargs):
            raise inner.Refused('inert_control_stop_before_query')
        modules = dict(qualifier=dict(validate_preload_inputs=lambda *args: None,
            qualify_and_observe=stop_before_query), resolver=dict(resolve_font_recipe=None),
            leaf=dict(observe_reference_metric=None))
        original_reader = inner.active_trace_bytes
        deadlines = []
        def read(path, *, deadline, **kw):
            deadlines.append(deadline)
            return original_reader(path, deadline=deadline, **kw)
        with patch.dict(os.environ, inner.START_ENV), patch.object(inner.time, 'monotonic', clock.monotonic), \
             patch.object(inner, 'active_trace_bytes', read):
            result = inner.execute_inner(c, modules=modules, preload=(pre, '7' * 64),
                runtime_factory=lambda config: dict(remote_context=object(), desktop=Desktop(), handler=handler,
                    property_value_factory=lambda k, v: (k, v), descriptor_factory=None, endpoint='inert'),
                identity_observer=lambda config: dict(config['office_process']), loaded_supplier=loaded,
                write=lambda *args: None, claim=lambda config: None)
        self.assertEqual(deadlines, [101.0, 105.5])
        self.assertEqual(result['stage'], 'QUALIFY_AND_QUERY')
        self.assertEqual(result['error']['reason'], 'inert_control_stop_before_query')
        self.assertTrue(result['readonly_close_confirmed'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReaderControls)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(scope='SOURCE_ONLY_TINY_FILES_NO_LIVE_ACTOR', tests=outcome.testsRun,
        failures=len(outcome.failures), errors=len(outcome.errors), successful=outcome.wasSuccessful(),
        source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        original=str(ORIGINAL), original_sha256=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
        limits=['No Office/UNO/GDB/native actor/namespace/service or live acceptance.',
                'Deterministic scheduling controls wrap real opens/reads/stats and os.replace of private tiny files.',
                'UID rejection uses a controlled getuid mismatch; no ownership changes.',
                'Two distinct readiness phases get separate ready_seconds, each capped by original operation deadline.'])
    (ROOT / 'inner-reader-tests/RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
