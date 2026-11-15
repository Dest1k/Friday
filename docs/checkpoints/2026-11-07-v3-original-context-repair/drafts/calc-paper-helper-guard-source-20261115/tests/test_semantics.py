"""Finite source tests; no GDB, helper, namespace, Office or UNO execution."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time
import types
import unittest
import tempfile
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
CANDIDATE = BASE / 'candidate'
DEPS = CANDIDATE / 'outer/deps'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


P = module('policy_under_test', DEPS / 'paper_helper_policy.py')
A = module('adapter_under_test', DEPS / 'paper_helper_gdb.py')
INNER = module('inner_under_test', CANDIDATE / 'inner/inner_client.py')
OUTER = module('outer_under_test', CANDIDATE / 'outer/outer_runner.py')
NAMESPACE = module('namespace_under_test', CANDIDATE / 'outer/namespace_entry.py')
CHECKER = module('checker_under_test', DEPS / 'check_native_trace.py')
MANIFEST = json.loads((DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json').read_text())
ORIGINAL = dict(pid=12, start_ticks=100, gdb_pid=2, inferior=1)
RUNTIME = dict(operation_id='OWN_SOURCE_TEST', nonce='0' * 32,
    source_sha256=MANIFEST['source_sha256'], manifest_ref=dict(path=str(DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json'),
        sha256=hashlib.sha256((DEPS / 'PAPER-HELPER-OFFICE-MANIFEST.json').read_bytes()).hexdigest()),
    marker_path='/tmp/friday-metric-work/load-dependency.json', operation_deadline_monotonic=200.0)
THREAD = [12, 12, 0]
PHASE = dict(nonce='0' * 32, phase='IDLE', index=None, digit=None)
MARKER = dict(schema=P.MARKER, state='LOAD_OPEN', **{k: RUNTIME[k] for k in
    ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'operation_deadline_monotonic')})
DASH = dict(pid=15, ppid=12, start_ticks=110)
PAPER = dict(pid=16, ppid=15, start_ticks=120)


def custody():
    return P.Custody(copy.deepcopy(MANIFEST), copy.deepcopy(RUNTIME), copy.deepcopy(ORIGINAL))


def window(c, **changes):
    args = dict(marker=copy.deepcopy(MARKER), phase=copy.deepcopy(PHASE), original=copy.deepcopy(ORIGINAL),
                now=150.0, records=[], active=None)
    args.update(changes)
    c.window(**args)


def arm(c, **changes):
    args = dict(exact_entry=True, exact_caller=True, command_equal=True, mode_equal=True)
    args.update(changes)
    c.arm(THREAD, **args)


def through(c, stop='closed'):
    window(c)
    arm(c)
    if stop == 'armed': return c
    c.birth({'pid': 12, 'start_ticks': 100}, DASH, route_ok=True)
    if stop == 'dash_born': return c
    c.exec('dash', dict(DASH, inferior=2), exact_image=True, exact_argv=True, custody_ok=True)
    if stop == 'dash_exec': return c
    c.entry('dash', dict(DASH, inferior=2), images_ok=True, custody_ok=True)
    if stop == 'dash_entry': return c
    c.birth({'pid': 15, 'start_ticks': 110}, PAPER, route_ok=True)
    if stop == 'paper_born': return c
    c.exec('paperconf', dict(PAPER, inferior=3), exact_image=True, exact_argv=True, custody_ok=True)
    c.entry('paperconf', dict(PAPER, inferior=3), images_ok=True, custody_ok=True)
    c.popen_return(THREAD, pipe_ok=True)
    if stop == 'paper_entry': return c
    c.exit(3, 3)
    c.exit(2, 3)
    c.eof(THREAD, empty_eof=True)
    if stop == 'reaped': return c
    c.close(THREAD, 768, 151.0, children_absent=True, original_ok=True)
    return c


def inner_config():
    fake = lambda name: dict(path='/OWN/INERT/' + name, sha256='1' * 64)
    c = dict(schema=INNER.SCHEMA, operation_id=RUNTIME['operation_id'], nonce=RUNTIME['nonce'],
        pipe_name='own_source_test_private_pipe', office_process=dict(namespace_pid=12, start_ticks=100,
        executable_sha256='2' * 64), modules={k: fake(k) for k in ('qualifier', 'resolver', 'leaf')},
        uno={'search_paths': ['/OWN/A', '/OWN/B', '/OWN/C'],
             'files': [fake(k) for k in ('uno.py', 'unohelper.py', 'pyuno.so', 'libpyuno.so')]},
        preload=fake('preload'), handler_source_ref=fake('inner.py'),
        paths=dict(work=INNER.WORK, phase=INNER.WORK + '/phase.json', trace=INNER.WORK + '/native-trace.json',
            checkpoint=INNER.WORK + '/inner-checkpoint.json', loaded_envelope=INNER.WORK + '/loaded-envelope.json',
            started=INNER.WORK + '/inner-started.json'), timeouts=dict(connect_seconds=1, loaded_seconds=1, ready_seconds=1))
    return c


class PolicyTests(unittest.TestCase):
    def test_actual_topology_semantics_and_separate_original(self):
        c = through(custody())
        P.validate_closed(c.snapshot(), RUNTIME, ORIGINAL)
        self.assertEqual(c.e['execs'], ['dash', 'paperconf'])
        self.assertEqual([x['exit_code'] for x in c.e['children']], [3, 3])
        self.assertEqual(c.e['original'], ORIGINAL)
        c.metric()

    def test_parent_return_and_EOF_scheduling_do_not_corrupt_helper_state(self):
        c = through(custody(), 'dash_exec')
        c.popen_return(THREAD, pipe_ok=True)  # Parent may resume after shell exec.
        c.entry('dash', dict(DASH, inferior=2), images_ok=True, custody_ok=True)
        c.birth({'pid': 15, 'start_ticks': 110}, PAPER, route_ok=True)
        c.exec('paperconf', dict(PAPER, inferior=3), exact_image=True, exact_argv=True, custody_ok=True)
        c.entry('paperconf', dict(PAPER, inferior=3), images_ok=True, custody_ok=True)
        c.eof(THREAD, empty_eof=True)  # EOF does not fabricate exit/reaping facts.
        with self.assertRaises(RuntimeError):
            c.close(THREAD, 768, 151.0, children_absent=True, original_ok=True)
        c.exit(3, 3); c.exit(2, 3)
        c.close(THREAD, 768, 151.0, children_absent=True, original_ok=True)
        c.metric()

    def test_marker_and_clock_negative_controls(self):
        for field, value in [('nonce', 'f' * 32), ('operation_id', 'OLD'), ('source_sha256', 'f' * 64),
                             ('manifest_ref', {'path': '/wrong', 'sha256': 'f' * 64}),
                             ('state', 'LOAD_CLOSED'), ('operation_deadline_monotonic', 999.0)]:
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                marker = copy.deepcopy(MARKER); marker[field] = value
                window(custody(), marker=marker)
        for value in (None, {}, {'phase': 'IDLE'}):
            with self.subTest(missing=value), self.assertRaises(RuntimeError):
                window(custody(), marker=value)
        for args in (dict(now=200.0), dict(now=201.0), dict(now=float('nan')),
                     dict(records=[{}]), dict(active={}), dict(phase=dict(PHASE, phase='METRIC')),
                     dict(original=dict(ORIGINAL, start_ticks=101)), dict(original=dict(ORIGINAL, pid=13))):
            with self.subTest(args=args), self.assertRaises(RuntimeError): window(custody(), **args)

    def test_exact_popen_negatives(self):
        for field in ('exact_entry', 'exact_caller', 'command_equal', 'mode_equal'):
            with self.subTest(field=field), self.assertRaises(RuntimeError): arm(custody(), **{field: False})
        c = through(custody(), 'armed')
        with self.assertRaises(RuntimeError): arm(c)
        with self.assertRaises(RuntimeError):
            custody().arm([13, 13, 0], exact_entry=True, exact_caller=True, command_equal=True, mode_equal=True)

    def test_birth_identity_route_and_extras(self):
        for parent, child, route in [({'pid': 13, 'start_ticks': 100}, DASH, True),
                ({'pid': 12, 'start_ticks': 101}, DASH, True),
                ({'pid': 12, 'start_ticks': 100}, dict(DASH, ppid=13), True),
                ({'pid': 12, 'start_ticks': 100}, DASH, False)]:
            with self.subTest(parent=parent, child=child, route=route), self.assertRaises(RuntimeError):
                through(custody(), 'armed').birth(parent, child, route_ok=route)
        with self.assertRaises(RuntimeError):
            custody().birth({'pid': 12, 'start_ticks': 100}, DASH, route_ok=True)
        with self.assertRaises(RuntimeError):
            through(custody(), 'paper_entry').birth({'pid': 16, 'start_ticks': 120},
                dict(pid=17, ppid=16, start_ticks=130), route_ok=True)

    def test_exec_image_argv_identity_and_extra_controls(self):
        for role, value, changes in [('dash', dict(DASH, inferior=2), {'exact_image': False}),
                ('dash', dict(DASH, inferior=2), {'exact_argv': False}),
                ('dash', dict(DASH, inferior=2), {'custody_ok': False}),
                ('dash', dict(DASH, inferior=2, start_ticks=999), {}),
                ('paperconf', dict(DASH, inferior=2), {})]:
            args = dict(exact_image=True, exact_argv=True, custody_ok=True); args.update(changes)
            with self.subTest(role=role, changes=changes), self.assertRaises(RuntimeError):
                through(custody(), 'dash_born').exec(role, value, **args)
        with self.assertRaises(RuntimeError):
            through(custody(), 'paper_entry').exec('paperconf', dict(PAPER, inferior=3),
                exact_image=True, exact_argv=True, custody_ok=True)

    def test_future_mapping_cannot_pass_entry(self):
        for key in ('images_ok', 'custody_ok'):
            args = dict(images_ok=True, custody_ok=True); args[key] = False
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                through(custody(), 'dash_exec').entry('dash', dict(DASH, inferior=2), **args)

    def test_exit_signal_unknown_and_pclose_controls(self):
        for inferior, code in [(2, 3), (3, None), (3, 0), (3, -9), (4, 3), (1, 0), (3, True)]:
            with self.subTest(inferior=inferior, code=code), self.assertRaises(RuntimeError):
                through(custody(), 'paper_entry').exit(inferior, code)
        for changes in (dict(children_absent=False), dict(original_ok=False), dict(now=200.0), dict(status=0), dict(thread=[12, 14, 0])):
            args = dict(thread=THREAD, status=768, now=151.0, children_absent=True, original_ok=True); args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(RuntimeError): through(custody(), 'reaped').close(**args)
        with self.assertRaises(RuntimeError): through(custody(), 'paper_entry').close(THREAD, 768, 151.0, children_absent=True, original_ok=True)
        with self.assertRaises(RuntimeError): through(custody(), 'paper_entry').eof(THREAD, empty_eof=False)
        with self.assertRaises(RuntimeError): through(custody(), 'paper_entry').metric()

    def test_independent_terminal_consumer_rejects_drift(self):
        evidence = through(custody()).snapshot()
        for key, value in [('state', 'ARMED'), ('execs', ['dash']), ('pclose_status', 0),
                           ('closure_observed_monotonic', 200.0), ('original', dict(ORIGINAL, pid=999))]:
            v = copy.deepcopy(evidence); v[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): P.validate_closed(v, RUNTIME, ORIGINAL)
        for key, value in [('start_ticks', 0), ('ppid', 12), ('exit_code', None), ('absent_at_close', False), ('entry_verified', False)]:
            v = copy.deepcopy(evidence); v['children'][1][key] = value
            with self.subTest(child_key=key), self.assertRaises(RuntimeError): P.validate_closed(v, RUNTIME, ORIGINAL)


class AdapterAndCallerTests(unittest.TestCase):
    def test_static_callsite_module_and_bytes(self):
        a = A.Adapter.__new__(A.Adapter); a.m = MANIFEST
        site = MANIFEST['caller']['sites']['popen_return']; frame = types.SimpleNamespace(pc=lambda: 500)
        a.offset = lambda f, image: site['offset']
        a.memory = lambda address, count: bytes.fromhex(site['before'] if address == 495 else site['after'])
        self.assertTrue(a.site('popen_return', frame))
        a.offset = lambda f, image: site['offset'] + 1
        with self.assertRaises(RuntimeError): a.site('popen_return', frame)
        a.offset = lambda f, image: site['offset']
        a.memory = lambda address, count: b'X' * count
        with self.assertRaises(RuntimeError): a.site('popen_return', frame)

    def test_executable_bytes_and_exact_argv_negative_controls(self):
        # Actual file hashing by the adapter; fixture metadata only, never exec.
        with tempfile.TemporaryDirectory(dir=BASE / 'tests') as directory:
            root = Path(directory); (root / '15').mkdir(); (root / '15/exe').write_bytes(b'OWN_INERT_IMAGE')
            a = A.Adapter.__new__(A.Adapter)
            image = dict(path='/OWN/EXACT/dash', sha256=hashlib.sha256(b'OWN_INERT_IMAGE').hexdigest())
            a.m = {'images': {'dash': image}}
            argv = b'sh\0-c\0--\0paperconf 2>/dev/null\0'
            a.bounded = lambda path, limit: argv
            real_path = Path
            def fake_path(value):
                return root if value == '/proc' else real_path(value)
            with patch.object(A, 'Path', fake_path), patch.object(A.os, 'readlink', lambda path: image['path']):
                self.assertTrue(a.image('dash', 15))
                argv = b'sh\0-c\0--\0paperconf -x\0'
                with self.assertRaises(RuntimeError): a.image('dash', 15)
                argv = b'sh\0-c\0--\0paperconf 2>/dev/null\0'
                (root / '15/exe').write_bytes(b'CHANGED_INERT_IMAGE')
                with self.assertRaises(RuntimeError): a.image('dash', 15)

    def test_environment_PATH_inheritance_and_paper_inputs(self):
        a = A.Adapter.__new__(A.Adapter); a.m = MANIFEST
        env = {k.encode(): v.encode() for k, v in MANIFEST['environment'].items()}
        a.bounded = lambda path, limit: b'\0'.join(k + b'=' + v for k, v in env.items()) + b'\0'
        with patch.object(A.os, 'readlink', lambda path: '/tmp/friday-metric-work'), \
                patch.object(A.os.path, 'lexists', lambda path: False):
            a.environment(12, initial=True)
            a.environment(15)
            env[b'PWD'] = b'/tmp/friday-metric-work'; a.environment(16)
            for key, value in [(b'PATH', b'/OWN/changed'), (b'PAPERSIZE', b'OWN'), (b'LD_PRELOAD', b'OWN')]:
                previous = env.get(key); env[key] = value
                with self.subTest(key=key), self.assertRaises(RuntimeError): a.environment(16)
                if previous is None: del env[key]
                else: env[key] = previous
        with patch.object(A.os, 'readlink', lambda path: '/tmp/friday-metric-work'), \
                patch.object(A.os.path, 'lexists', lambda path: path == '/etc/paperspecs'):
            with self.assertRaises(RuntimeError): a.environment(16)
    def test_exec_stop_does_not_assert_future_libs_entry_requires_them(self):
        a = A.Adapter.__new__(A.Adapter); a.m = MANIFEST; a.pin = lambda image: None
        paths = [MANIFEST['images'][r]['path'] for r in ('paperconf', 'loader')]
        a.maps = lambda pid: [(1, 2, 0, 'r-xp', path) for path in paths]
        self.assertTrue(a.loaded_images('paperconf', 16, entry=False))
        with self.assertRaises(RuntimeError): a.loaded_images('paperconf', 16, entry=True)
        paths.extend(MANIFEST['images'][r]['path'] for r in ('libc', 'libpaper'))
        self.assertTrue(a.loaded_images('paperconf', 16, entry=True))
        paths.append('/OWN/unknown.so')
        with self.assertRaises(RuntimeError): a.loaded_images('paperconf', 16, entry=True)

    def test_exact_FD_pipe_stderr_extra_controls(self):
        a = A.Adapter.__new__(A.Adapter)
        log = dict(dev=1, ino=8, type=stat.S_IFREG, rdev=0, access=os.O_WRONLY, cloexec=False)
        null = dict(dev=2, ino=9, type=stat.S_IFCHR, rdev=99, access=os.O_WRONLY, cloexec=False)
        pipe = dict(dev=3, ino=10, type=stat.S_IFIFO, rdev=0, access=os.O_WRONLY, cloexec=False)
        fds = {0: dict(null, access=os.O_RDONLY), 1: pipe, 2: log}
        a.original_stderr = log; a.original_stdin = fds[0]; a.pipe = None
        a.fd = lambda pid, n: fds[n]; a.null = lambda v: v['type'] == stat.S_IFCHR and v['rdev'] == 99
        class ProcPath:
            def __init__(self, *args): pass
            def __truediv__(self, value): return self
            def iterdir(self): return [types.SimpleNamespace(name=str(n)) for n in fds]
        with patch.object(A, 'Path', ProcPath):
            self.assertTrue(a.fds(15, 'dash'))
            with self.assertRaises(RuntimeError): a.fds(16, 'paperconf')
            fds[2] = null
            self.assertTrue(a.fds(16, 'paperconf'))
            fds[3] = dict(log, cloexec=True)
            with self.assertRaises(RuntimeError): a.fds(16, 'paperconf')
            self.assertTrue(a.fds(15, 'dash', redirection=True))
            fds[3] = dict(log, ino=999, cloexec=True)
            with self.assertRaises(RuntimeError): a.fds(15, 'dash', redirection=True)
            del fds[3]; fds[1] = dict(pipe, ino=11)
            with self.assertRaises(RuntimeError): a.fds(16, 'paperconf')

    def test_catchpoints_unknown_fork_and_exit_dispatch(self):
        a = A.Adapter.__new__(A.Adapter); a.g = types.SimpleNamespace(BP_CATCHPOINT=9)
        a.n = {'STATE': {'error': None}}
        a.catchpoints = {1: 'fork', 2: 'vfork', 3: 'exec'}; observed = []
        a.birth = lambda: observed.append('vfork'); a.exec = lambda: observed.append('exec'); a.publish = lambda: None
        for n in (2, 3): a.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=n)]))
        self.assertEqual(observed, ['vfork', 'exec'])
        for n in (1, 4):
            with self.assertRaises(RuntimeError): a.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=n)]))
        a.c = through(custody(), 'paper_entry'); a.ensure = lambda: a.c
        self.assertTrue(a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=3), exit_code=3)))
        self.assertTrue(a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=2), exit_code=3)))
        a.c.eof(THREAD, empty_eof=True); a.c.close(THREAD, 768, 151.0, children_absent=True, original_ok=True)
        self.assertFalse(a.exited(types.SimpleNamespace(inferior=types.SimpleNamespace(num=1), exit_code=0)))

    def test_hook_helper_exit_never_overwrites_original(self):
        tree = ast.parse((DEPS / 'native_return_observer.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'exited')
        state = dict(exit_code=None)
        helper = types.SimpleNamespace(exited=lambda event: event.inferior.num != 1)
        env = dict(STATE=state, helper=helper, fail=lambda reason: self.fail(reason))
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<exact-hook-exited>', 'exec'), env)
        env['exited'](types.SimpleNamespace(inferior=types.SimpleNamespace(num=3), exit_code=3))
        self.assertIsNone(state['exit_code'])
        env['exited'](types.SimpleNamespace(inferior=types.SimpleNamespace(num=1), exit_code=0))
        self.assertEqual(state['exit_code'], 0)

    def test_hook_signals_remain_refusal(self):
        tree = ast.parse((DEPS / 'native_return_observer.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'stopped')
        class SignalEvent: pass
        errors = []
        env = dict(gdb=types.SimpleNamespace(SignalEvent=SignalEvent), fail=errors.append)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<exact-hook-stopped>', 'exec'), env)
        env['stopped'](SignalEvent())
        self.assertEqual(errors, ['unexpected_signal'])

    def test_new_objfile_selected_helper_preserves_native_symbols(self):
        tree = ast.parse((DEPS / 'native_return_observer.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'install')
        state = dict(error=None, symbols=dict(outer=111, native=222, native_return=333))
        env = dict(installed=False, STATE=state, helper=types.SimpleNamespace(install=lambda: None),
            gdb=types.SimpleNamespace(selected_inferior=lambda: types.SimpleNamespace(num=3)),
            address=lambda _: self.fail('helper attempted native symbol resolution'))
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<exact-hook-install>', 'exec'), env)
        env['install']()
        self.assertEqual(state['symbols'], dict(outer=111, native=222, native_return=333))
        self.assertFalse(env['installed'])

    def test_selected_dead_helper_returns_original(self):
        a = A.Adapter.__new__(A.Adapter); commands = []
        a.g = types.SimpleNamespace(inferiors=lambda: [types.SimpleNamespace(num=1, pid=12),
            types.SimpleNamespace(num=2, pid=0), types.SimpleNamespace(num=3, pid=0)],
            execute=lambda cmd, **kwargs: commands.append(cmd))
        self.assertTrue(a.original_selected())
        self.assertEqual(commands, ['inferior 1'])

    def test_original_metric_guards_AST_unchanged(self):
        old = ast.parse((BASE / 'before/outer/deps/native_return_observer.py').read_text())
        new = ast.parse((DEPS / 'native_return_observer.py').read_text())
        unchanged = ['frame_ok', 'reg', 'memint', 'digit_at', 'OuterFinish', 'OuterEntry', 'NativeEntry', 'NativeReturn', 'address']
        for name in unchanged:
            a = next(n for n in old.body if getattr(n, 'name', None) == name)
            b = next(n for n in new.body if getattr(n, 'name', None) == name)
            self.assertEqual(ast.dump(a, include_attributes=False), ast.dump(b, include_attributes=False), name)
        for relative in ('qualifier/runtime_qualifier.py', 'qualifier/runtime_font_resolver.py',
                         'qualifier/reference_metric_leaf_r2.py', 'outer/font_view/font_view.py',
                         'outer/deps/metric_namespace.py', 'outer/deps/FUTURE-OFFICE-CONFIG-TEMPLATE.json'):
            self.assertEqual((BASE / 'before' / relative).read_bytes(), (CANDIDATE / relative).read_bytes(), relative)


class ConsumerTests(unittest.TestCase):
    def test_config_legacy_optional_and_absolute_deadline(self):
        c = inner_config(); INNER.validate_config(c)
        c['load_dependency'] = copy.deepcopy(RUNTIME); INNER.validate_config(c)
        for value in (None, float('inf'), float('nan'), 0, -1):
            c['load_dependency']['operation_deadline_monotonic'] = value
            with self.subTest(value=value), self.assertRaises(INNER.Refused): INNER.validate_config(c)
        c['office_process'] = None; c['load_dependency']['operation_deadline_monotonic'] = None
        INNER.validate_config(c, allow_unstarted=True)
        c['unreviewed'] = True
        with self.assertRaises(INNER.Refused): INNER.validate_config(c, allow_unstarted=True)

    def run_inner_load(self, raises):
        c = inner_config(); c['load_dependency'] = copy.deepcopy(RUNTIME)
        c['load_dependency']['operation_deadline_monotonic'] = time.monotonic() + 30
        writes = []; calls = []; handler = types.SimpleNamespace(requests=0, instance_token='OWN')
        class Doc:
            def close(self, value): calls.append(('close', value))
        class Desktop:
            def loadComponentFromURL(self, *args):
                calls.append(('load', args))
                self.assert_open = writes[-1][1]['state'] == 'LOAD_OPEN'
                if raises: raise ValueError('not_emitted')
                return Doc()
            def terminate(self): calls.append(('terminate',)); return True
        desktop = Desktop()
        runtime = dict(desktop=desktop, remote_context=None, handler=handler,
            property_value_factory=lambda k, v: (k, v), descriptor_factory=None, endpoint='own-inert')
        def supplier(*args):
            raise ValueError('stop_source_test_before_qualifier')
        q = dict(validate_preload_inputs=lambda *args: None)
        pre = dict(source={'sha256': MANIFEST['source_sha256']}, working_copy={'url': 'file:///OWN/INERT/never-opened.xlsx'})
        with patch.dict(os.environ, INNER.START_ENV):
            result = INNER.execute_inner(c, modules=dict(qualifier=q), preload=(pre, 'f' * 64),
                runtime_factory=lambda c: runtime, identity_observer=lambda c: {'own': True},
                loaded_supplier=supplier, readiness=lambda: None, write=lambda p, v: writes.append((p, copy.deepcopy(v))),
                phase_callbacks=object(), claim=lambda c: None)
        self.assertTrue(desktop.assert_open)
        markers = [v for p, v in writes if p == c['load_dependency']['marker_path']]
        self.assertEqual([v['state'] for v in markers], ['LOAD_OPEN', 'LOAD_CLOSED'])
        self.assertEqual(markers[0]['operation_deadline_monotonic'], markers[1]['operation_deadline_monotonic'])
        self.assertEqual(result['status'], 'REFUSED')
        self.assertIsNone(result['actual_M'])
        self.assertEqual(calls[0][1][:3], (pre['working_copy']['url'], '_blank', 0))
        return writes

    def test_marker_exact_load_call_and_finally_success(self):
        writes = self.run_inner_load(False)
        self.assertEqual([v.get('stage', v.get('state')) for _, v in writes], ['LOAD_OPEN', 'LOAD_CLOSED', 'MODEL_LOADED'])

    def test_marker_finally_on_load_exception(self):
        writes = self.run_inner_load(True)
        self.assertEqual([v.get('state') for _, v in writes], ['LOAD_OPEN', 'LOAD_CLOSED'])

    def test_outer_optional_binding_real_config_shapes(self):
        plan = dict(observer={}, inner_input={})
        self.assertIsNone(OUTER.inspect_load_dependency(plan, [BASE]))
        binding = {role: dict(path=str(DEPS / name), sha256=hashlib.sha256((DEPS / name).read_bytes()).hexdigest())
            for role, name in [('manifest', 'PAPER-HELPER-OFFICE-MANIFEST.json'), ('policy', 'paper_helper_policy.py'), ('adapter', 'paper_helper_gdb.py')]}
        plan.update(operation_id=RUNTIME['operation_id'], nonce=RUNTIME['nonce'])
        plan['observer'] = dict(load_dependency=binding, config={'symbol_file_path': MANIFEST['caller']['path'],
                                      'symbol_file_sha256': MANIFEST['caller']['sha256']})
        plan['inner_input'] = dict(load_dependency=dict(RUNTIME, operation_deadline_monotonic=None))
        self.assertEqual(OUTER.inspect_load_dependency(plan, [BASE]), MANIFEST)
        plan['inner_input']['load_dependency']['operation_deadline_monotonic'] = 999
        with self.assertRaises(OUTER.Refused): OUTER.inspect_load_dependency(plan, [BASE])

    def test_namespace_bundle_uses_original_clock_and_closure(self):
        binding = {role: dict(path=str(DEPS / name), sha256=hashlib.sha256((DEPS / name).read_bytes()).hexdigest())
            for role, name in [('manifest', 'PAPER-HELPER-OFFICE-MANIFEST.json'), ('policy', 'paper_helper_policy.py'), ('adapter', 'paper_helper_gdb.py')]}
        plan = dict(observer={'load_dependency': binding}, inner_input={'load_dependency': dict(RUNTIME,
            operation_deadline_monotonic=None)}, nonce=RUNTIME['nonce'], operation_id=RUNTIME['operation_id'])
        bundle, policy = NAMESPACE.load_dependency_bundle(plan, 200.0)
        self.assertEqual(bundle['runtime']['operation_deadline_monotonic'], 200.0)
        trace = dict(load_dependency=through(custody()).snapshot())
        marker = dict(MARKER, state='LOAD_CLOSED')
        class SyntheticAbsentProc:
            def __init__(self, *args): pass
            def __truediv__(self, value): return self
            def exists(self): return False
        with patch.object(NAMESPACE, 'runtime_read', lambda path: json.dumps(marker).encode()), \
                patch.object(NAMESPACE, 'Path', SyntheticAbsentProc):
            NAMESPACE.check_load_dependency_closed(trace, bundle['runtime'], policy, ORIGINAL)
            marker['state'] = 'LOAD_OPEN'
            with self.assertRaises(NAMESPACE.Refused):
                NAMESPACE.check_load_dependency_closed(trace, bundle['runtime'], policy, ORIGINAL)
        trace['load_dependency']['children'][1]['absent_at_close'] = False
        with self.assertRaises(RuntimeError): NAMESPACE.check_load_dependency_closed(trace, bundle['runtime'], policy, ORIGINAL)

    def test_native_trace_checker_legacy_and_optional_schema(self):
        # Genuine ten-call ABI shape with externally supplied original custody.
        symbols = dict(outer=1000, native=2000, native_return=1100)
        records = [dict(index=i, digit=str(i), thread=THREAD, font=20, device=30, string_address=40,
            raw_native=126, outer_int32=126, native_return_pc=1100, native_entry_sp=0x108, outer_entry_sp=0x208) for i in range(10)]
        trace = dict(schema='frw.native-return-trace.v1', kind='OFFICE_UNADMITTED', nonce=RUNTIME['nonce'],
            status='COMPLETE_UNATTESTED', records=records, error=None, exit_code=0, process=ORIGINAL,
            symbols=symbols, actual_M=None, runtime_attested=False, own_inferior_absent=True)
        def validate(**kwargs):
            raw = json.dumps(trace).encode()
            return CHECKER.validate_trace(raw, expected_sha256=hashlib.sha256(raw).hexdigest(), nonce=RUNTIME['nonce'],
                process=ORIGINAL, symbols=symbols, uno_widths=[126] * 10, root_custody_confirmed=True, **kwargs)
        validate()
        trace['load_dependency'] = through(custody()).snapshot()
        with self.assertRaises(CHECKER.Unbound): validate()
        with self.assertRaises(CHECKER.Unbound): validate(load_dependency=RUNTIME)
        validate(load_dependency=RUNTIME, validate_dependency=P.validate_closed)
        trace['records'][0]['raw_native'] = 4294967422
        with self.assertRaises(CHECKER.Unbound): validate(load_dependency=RUNTIME, validate_dependency=P.validate_closed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
