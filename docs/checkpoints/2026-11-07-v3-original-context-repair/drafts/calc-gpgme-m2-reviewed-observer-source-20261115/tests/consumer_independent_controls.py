"""Independent inert extracted-source controls for the frozen M2 consumer joins.

No GDB module, inferior, helper, Office, namespace, ELF, or source-suite execution.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import types
import unittest
import re
from unittest.mock import patch

SOURCE = Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-COMPLETE-OBSERVER-SOURCE-20261115')
OUT = Path(__file__).parent
DEPS = SOURCE / 'candidate/outer/deps'
NATIVE = DEPS / 'native_return_observer.py'
REPAIR = OUT / 'repair-copy/native_return_observer.py'


def extracted(path, name, *, class_name=None):
    tree = ast.parse(path.read_bytes())
    scope = tree.body
    if class_name:
        scope = next(n for n in scope if isinstance(n, ast.ClassDef) and n.name == class_name).body
    return next(n for n in scope if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)


def need(ok, code):
    if not ok:
        raise RuntimeError(code)


def compile_nodes(nodes, namespace):
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<inert-reviewed-source>', 'exec'), namespace)


router_namespace = {'need': need}
compile_nodes([extracted(DEPS / 'gpgme_engine_gdb.py', 'MultiCustody')], router_namespace)
Router = router_namespace['MultiCustody']
paper_namespace = {'require': need}
compile_nodes([extracted(DEPS / 'paper_helper_gdb.py', 'boundary', class_name='Adapter')], paper_namespace)


def paper():
    result = types.SimpleNamespace(catchpoints={}, n={'STATE': {'error': None}},
        g=types.SimpleNamespace(BP_CATCHPOINT=9), calls=[], pending=None)
    result.birth = lambda: result.calls.append('birth')
    result.exec = lambda: result.calls.append('exec')
    result.publish = lambda: result.calls.append('publish')
    result.boundary = types.MethodType(paper_namespace['boundary'], result)
    return result


def gpgme():
    return types.SimpleNamespace(catchpoints={}, init_active=False, finished_initialization=False)


def wire(path, helper):
    main = extracted(path, 'main')
    block = next(n for n in main.body if isinstance(n, ast.If)
        and ast.unparse(n.test) == 'helper is not None'
        and 'catchpoints' in ast.unparse(n))
    # Execute only the authenticated routing assignments, not GDB settings.
    assignments = copy.deepcopy(block)
    assignments.body = [n for n in assignments.body if not isinstance(n, ast.Expr)]
    compile_nodes([assignments], {'helper': helper, 'catchpoints': {11: 'vfork', 12: 'exec', 13: 'fork'}})


class IndependentControls(unittest.TestCase):
    def test_frozen_composition_and_declared_results_exact(self):
        for filename, digest in {
            'RESULT.json': '26f6b728b3ef086a00b928fcd3a2c8e3c9601ad0a40f14d0a7fb99f42722d268',
            'SOURCE-FREEZE.json': '5ace27b5f9b33d4062ecd61c55a9ceae8ac5f3b9271793ef1d28cb9600b3aebd',
            'SOURCE-COMPOSITION.json': '3848c614ead5ec12a5dcd42f382fa0e1c9c3d03cd72dd10e165644d421e96d10',
        }.items():
            self.assertEqual(hashlib.sha256((SOURCE / filename).read_bytes()).hexdigest(), digest)
        freeze = json.loads((SOURCE / 'SOURCE-FREEZE.json').read_bytes())
        for ref in freeze['candidate_files']:
            self.assertEqual(hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest(), ref['sha256'])
        composition = json.loads((SOURCE / 'SOURCE-COMPOSITION.json').read_bytes())
        for record in composition['files']:
            for role in ('before', 'after'):
                ref = record[role]
                if ref is not None:
                    self.assertEqual(hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest(), ref['sha256'])

    def test_baseline_legacy_paper_catchpoint_delivery(self):
        p = paper()
        wire(NATIVE, p)
        p.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=11)]))
        self.assertEqual(p.calls, ['birth', 'publish'])

    def test_frozen_router_shadows_required_paper_map_and_refuses(self):
        p, g = paper(), gpgme()
        helper = Router(p, g)
        wire(NATIVE, helper)
        self.assertEqual(p.catchpoints, {})
        self.assertEqual(g.catchpoints, {11: 'vfork', 12: 'exec', 13: 'fork'})
        self.assertIn('catchpoints', vars(helper))
        with self.assertRaisesRegex(RuntimeError, '^helper_unexpected_fork_or_catchpoint$'):
            helper.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=11)]))
        self.assertEqual(p.calls, [])

    def test_repair_delivers_both_paper_routes_without_wrapper_shadow(self):
        p, g = paper(), gpgme()
        helper = Router(p, g)
        wire(REPAIR, helper)
        self.assertNotIn('catchpoints', vars(helper))
        self.assertEqual(p.catchpoints, g.catchpoints)
        for number in (11, 12):
            helper.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=number)]))
        self.assertEqual(p.calls, ['birth', 'publish', 'exec', 'publish'])

    def test_repair_keeps_legacy_route_and_rejects_unrecognized_boundary(self):
        p = paper()
        wire(REPAIR, p)
        p.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=12)]))
        self.assertEqual(p.calls, ['exec', 'publish'])
        for number in (13, 999):
            with self.assertRaisesRegex(RuntimeError, '^helper_unexpected_fork_or_catchpoint$'):
                p.boundary(types.SimpleNamespace(breakpoints=[types.SimpleNamespace(type=9, number=number)]))

    def test_repair_ast_changes_only_owned_catchpoints_and_control_environment(self):
        a, b = [ast.parse(p.read_bytes()) for p in (NATIVE, REPAIR)]
        for tree in (a, b):
            main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
            main.body = [n for n in main.body if not (isinstance(n, ast.If)
                and ((ast.unparse(n.test) == 'helper is not None' and 'catchpoints' in ast.unparse(n))
                     or (ast.unparse(n.test) == "helper is not None and hasattr(helper, 'gpgme')"
                         and 'unset environment' in ast.unparse(n))))]
        self.assertEqual(ast.dump(a), ast.dump(b))
        compile(REPAIR.read_bytes(), str(REPAIR), 'exec')

    def test_native_all_helper_mutations_have_explicit_owner(self):
        tree = ast.parse(REPAIR.read_bytes())
        writes = [(n.lineno, ast.unparse(n)) for n in ast.walk(tree)
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute)
                and ast.unparse(t).startswith('helper.') for t in n.targets)]
        self.assertEqual([text for _, text in writes], [
            'helper.pending = None', 'helper.pending_stop = None',
            'helper.paper.catchpoints = dict(catchpoints)',
            'helper.gpgme.catchpoints = dict(catchpoints)',
            'helper.catchpoints = dict(catchpoints)'])
        # The pending writes are the existing single-paper fallback only.
        fail = extracted(REPAIR, 'fail')
        fallback = next(n for n in fail.body if isinstance(n, ast.If)
            and ast.unparse(n.test) == 'helper is not None').body[0]
        self.assertEqual(ast.unparse(fallback.test), "hasattr(helper, 'clear_pending')")
        self.assertIn('helper.pending = None', ast.unparse(ast.Module(body=fallback.orelse, type_ignores=[])))

    def test_active_reader_and_immutable_paper_unchanged(self):
        legacy = Path('/home/jericho/.cache/FRW-ASTRA-CALC-ACTIVE-PUBLICATION-READER-DELTA-20261115/candidate')
        for relative, names in {
            'outer/namespace_entry.py': ('runtime_read', 'font_runtime_read', 'read_ref', 'load_dependency_bundle'),
            'inner/inner_client.py': ('active_trace_bytes', 'protected_bytes', 'wait_json'),
            'outer/outer_runner.py': ('read_pinned', 'inspect_load_dependency'),
        }.items():
            for name in names:
                self.assertEqual(ast.dump(extracted(legacy / relative, name)),
                    ast.dump(extracted(SOURCE / 'candidate' / relative, name)))
        for name, digest in {
            'paper_helper_gdb.py': '6c7f293cb7636b34f747143b797f9e6601d96d83ff5e49a752446bbfff334b10',
            'paper_helper_policy.py': 'd4cb74cd814fa78eeaeb249f9b2d6177f506dc881458f287cb372191b2a4ec61',
        }.items():
            self.assertEqual(hashlib.sha256((DEPS / name).read_bytes()).hexdigest(), digest)

    def test_repair_first_refusal_stays_first_and_both_pending_cleared(self):
        records = []
        helper = types.SimpleNamespace(clear_pending=lambda: records.append('both'))
        ns = {'helper': helper, 'STATE': {'error': 'first'}, 'pending_action': 'CONTINUE', 'save': lambda: None}
        compile_nodes([extracted(REPAIR, 'fail')], ns)
        ns['fail']('second')
        self.assertEqual(ns['STATE'], {'error': 'first', 'status': 'REFUSED'})
        self.assertEqual(records, ['both'])
        self.assertIsNone(ns['pending_action'])

    def test_real_union_clear_cancels_creation_retirement_and_continuation(self):
        p = types.SimpleNamespace(pending='CONTINUE', pending_stop='paper-stop', to_create=['paper-create'])
        g = types.SimpleNamespace(pending='GPG_DRAIN', pending_stop='gpg-stop', to_create=['gpg-create'], to_retire=[7])
        ns = {}
        compile_nodes([extracted(DEPS / 'gpgme_engine_gdb.py', 'clear_pending', class_name='Adapter')], ns)
        g.clear_pending = types.MethodType(ns['clear_pending'], g)
        helper = Router(p, g)
        ns = {'helper': helper, 'STATE': {'error': 'first'}, 'pending_action': 'CONTINUE', 'save': lambda: None}
        compile_nodes([extracted(REPAIR, 'fail')], ns)
        ns['fail']('second')
        self.assertEqual(ns['STATE']['error'], 'first')
        self.assertIsNone(ns['pending_action'])
        self.assertEqual((p.pending, p.pending_stop, p.to_create), (None, None, []))
        self.assertEqual((g.pending, g.pending_stop, g.to_create, g.to_retire), (None, None, [], []))

    def cleanup_namespace(self, *, stale_pid=False, change_birth=False):
        infs = [types.SimpleNamespace(num=n, pid=p) for n, p in ((1, 101), (2, 102), (4, 104), (9, 109))]
        live = {i.pid for i in infs}
        if stale_pid:
            live.add(999)
        identities = {pid: {'pid': pid, 'ppid': 77, 'start_ticks': pid + 1000} for pid in live}
        selected, calls, read_count = [None], [], {}

        def proc(pid):
            calls.append(('proc', pid))
            read_count[pid] = read_count.get(pid, 0) + 1
            value = dict(identities[pid])
            if change_birth and pid == 104 and read_count[pid] == 2:
                value['start_ticks'] += 1
            return value

        def execute(command, **kwargs):
            calls.append(('execute', command))
            if command.startswith('inferior '):
                selected[0] = next(i for i in infs if i.num == int(command.split()[1]))
            elif command == 'kill':
                live.discard(selected[0].pid)
                selected[0].pid = 0
            else:
                raise AssertionError(command)

        class InertPath:
            def __init__(self, path): self.pid = int(str(path).rsplit('/', 1)[1])
            def exists(self): return self.pid in live

        helper = types.SimpleNamespace(known={101: identities[101], 102: identities[102]},
            gpgme=types.SimpleNamespace(known={104: identities[104]}), proc=proc,
            clear_pending=lambda: calls.append(('clear_pending',)))
        if stale_pid:
            helper.gpgme.known[999] = identities[999]
        ns = {'helper': helper, 'STATE': {'error': 'first', 'status': 'REFUSED'}, 'Path': InertPath,
            'require': need, 'gdb': types.SimpleNamespace(inferiors=lambda: infs, execute=execute)}
        tree = ast.parse(REPAIR.read_bytes())
        final = next(n for n in tree.body if isinstance(n, ast.Try)).finalbody
        branch = next(n for n in final if isinstance(n, ast.If) and ast.unparse(n.test) == 'helper is None')
        compile_nodes([branch], ns)
        return ns['STATE'], calls

    def test_actual_native_cleanup_uses_entire_owned_inferior_union_with_birth_cas(self):
        state, calls = self.cleanup_namespace()
        self.assertTrue(state['own_inferior_absent'])
        self.assertEqual(state['error'], 'first')
        self.assertEqual([v for v in calls if v[0] == 'execute'], [
            ('execute', 'inferior 1'), ('execute', 'kill'), ('execute', 'inferior 2'), ('execute', 'kill'),
            ('execute', 'inferior 4'), ('execute', 'kill'), ('execute', 'inferior 9'), ('execute', 'kill')])
        self.assertEqual([v for v in calls if v[0] == 'proc'],
            [('proc', pid) for pid in (101, 101, 102, 102, 104, 104, 109, 109)])

    def test_cleanup_stale_known_pid_is_never_selected_or_killed(self):
        state, calls = self.cleanup_namespace(stale_pid=True)
        self.assertFalse(state['own_inferior_absent'])
        self.assertEqual(state['cleanup_error'], 'OWN_PROCESS_CLEANUP_UNCONFIRMED')
        self.assertEqual(state['error'], 'first')
        self.assertNotIn(('proc', 999), calls)
        self.assertEqual(len([v for v in calls if v == ('execute', 'kill')]), 4)

    def test_cleanup_birth_change_refuses_kill_and_preserves_first_error(self):
        state, calls = self.cleanup_namespace(change_birth=True)
        self.assertFalse(state['own_inferior_absent'])
        self.assertEqual(state['cleanup_error'], 'OWN_PROCESS_CLEANUP_UNCONFIRMED')
        self.assertEqual(state['error'], 'first')
        self.assertEqual(len([v for v in calls if v == ('execute', 'kill')]), 3)

    def test_root_environment_pin_is_exact_equality_with_explicit_extra_keys(self):
        tree = ast.parse((DEPS / 'gpgme_engine_policy.py').read_bytes())
        assignments = [n for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in ('ISOLATED', 'OPTIONAL_ISOLATED', 'FORBIDDEN') for t in n.targets)]
        ns = {'need': need, 're': re}
        compile_nodes(assignments + [extracted(DEPS / 'gpgme_engine_policy.py', 'validate_environment')], ns)
        expected = dict(ns['ISOLATED'], LD_LIBRARY_PATH='/own/pinned/readonly/library:path')
        ns['validate_environment'](dict(expected), expected)
        with self.assertRaisesRegex(RuntimeError, '^gpgme_exact_current_environment_changed$'):
            ns['validate_environment'](dict(expected, EXTRA_UNPINNED='value'), expected)
        # Pins are a trusted Root input, not an implicit extension-key allowlist.
        explicit = dict(expected, ROOT_SELECTED_EXTRA='explicit')
        ns['validate_environment'](dict(explicit), explicit)
        forbidden = dict(expected, LD_PRELOAD='/own/never-admitted.so')
        with self.assertRaisesRegex(RuntimeError, '^gpgme_environment_isolation_or_override$'):
            ns['validate_environment'](forbidden, forbidden)

    def drive_real_main_to_starti(self, helper):
        control = ('FRW_NATIVE_OBSERVER_CONFIG', 'FRW_NATIVE_LOAD_DEPENDENCY_REF',
            'FRW_NATIVE_GPGME_ENGINE_INIT_REF', 'FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE')
        debugger_environment = {key: 'private-debugger-control-' + str(i) for i, key in enumerate(control)}
        debugger_environment.update(HOME='/tmp/friday-metric-work/tmp', LANG='C.UTF-8',
            LD_LIBRARY_PATH='/own/pinned/readonly/libraries', ROOT_SELECTED_EXTRA='pinned-value')

        class StopAtStarti(Exception):
            pass

        class InertGDB:
            def __init__(self):
                self.inferior_environment = dict(debugger_environment)
                self.commands, self.bps = [], []
                self.events = types.SimpleNamespace(**{name: types.SimpleNamespace(connect=lambda cb: None)
                    for name in ('new_objfile', 'exited', 'stop')})
            def inferiors(self): return [types.SimpleNamespace(num=1, pid=0)]
            def selected_inferior(self): return self.inferiors()[0]
            def current_progspace(self): return types.SimpleNamespace(filename='/own/never-executed-target')
            def breakpoints(self): return self.bps
            def execute(self, command, **kwargs):
                self.commands.append(command)
                if command.startswith('unset environment '):
                    self.inferior_environment.pop(command.split(' ', 2)[2], None)
                if command.startswith('catch '):
                    self.bps.append(types.SimpleNamespace(number=len(self.bps) + 1))
                if command == 'starti':
                    raise StopAtStarti()

        class InertPath:
            def __init__(self, path): pass
            def read_bytes(self): return b'\x7fELF\x02\x01'

        fake = InertGDB()
        ns = {'require': need, 'gdb': fake, 'Path': InertPath, 'pin': lambda *args: None,
            'CFG': dict(kind='OFFICE_UNADMITTED', nonce='a' * 32, target_path='/own/never-executed-target',
                target_sha256='b' * 64, symbol_file_path='/own/never-executed-symbol', symbol_file_sha256='c' * 64),
            'load_helper': lambda: helper, 'catchpoints': {}, 'install': lambda: None,
            'exited': lambda: None, 'stopped': lambda: None, 'os': types.SimpleNamespace(environ=debugger_environment)}
        before = copy.deepcopy(debugger_environment)
        compile_nodes([extracted(REPAIR, 'main')], ns)
        with self.assertRaises(StopAtStarti):
            ns['main']()
        self.assertEqual(debugger_environment, before)
        return fake, before, control

    def test_real_main_optin_removes_only_debugger_control_keys_before_starti(self):
        p, g = paper(), gpgme()
        fake, original, control = self.drive_real_main_to_starti(Router(p, g))
        self.assertEqual(fake.inferior_environment, {k: v for k, v in original.items() if k not in control})
        self.assertEqual([command for command in fake.commands if command.startswith('unset environment ')],
            ['unset environment ' + key for key in control])
        self.assertEqual(fake.commands[-1], 'starti')
        self.assertEqual(p.catchpoints, {1: 'fork', 2: 'vfork', 3: 'exec'})
        self.assertEqual(p.catchpoints, g.catchpoints)

    def test_real_main_legacy_and_nohelper_leave_inferior_environment_unchanged(self):
        for helper in (None, paper()):
            fake, original, control = self.drive_real_main_to_starti(helper)
            self.assertEqual(fake.inferior_environment, original)
            self.assertFalse(any(command.startswith('unset environment ') for command in fake.commands))


if __name__ == '__main__':
    unittest.main(verbosity=2)
