"""Independent pure final-delta controls; no actors, proc reads or output outside review/."""
import sys
sys.dont_write_bytecode = True
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import types
import unittest

os.umask(0o077)
B = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-FORK-BIRTH-SOURCE-20261115')
R = B / 'review'
PREV = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-BOOTSTRAP-ENTRY-SOURCE-20261115')
snapshot_raw = (B / 'REVIEW-SNAPSHOT.json').read_bytes()
assert hashlib.sha256(snapshot_raw).hexdigest() == '657b756b1c5cfd6f353b319b654521c11da447308ae81b68838c1bbc76bf97a0'
snapshot = json.loads(snapshot_raw)
for ref in snapshot['refs']:
    assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest() == ref['sha256'], ref['path']

# Reuse only reviewed synthetic data fixtures; each assertion/scenario below is
# independent. Import-by-exec creates no pycache and the test main is not called.
fixtures_path = B / 'tests/fork_controls.py'
fixtures = {'__file__': str(fixtures_path), '__name__': 'independent_source_fixtures'}
exec(compile(fixtures_path.read_bytes(), str(fixtures_path), 'exec'), fixtures)
Kernel, Inf = fixtures['Kernel'], fixtures['Inf']
collector_module = fixtures['c']


class IndependentControls(unittest.TestCase):
    def test_context_and_explicit_birth_callsite_are_distinguished(self):
        direct = Kernel()
        self.assertEqual(direct.run(), 'gpgme_collector_unowned_or_unobserved_birth')
        self.assertEqual(direct.adapter.boundary_count, 1)
        direct_frames = direct.state['gpgme_collector_birth_refusal']['source_frames']
        self.assertTrue(any(v['source_role'] == 'adapter' for v in direct_frames))
        nested = Kernel(present=True)
        nested.infs.append(Inf(20, 9))
        self.assertEqual(nested.run(), 'gpgme_collector_unowned_or_unobserved_birth')
        self.assertEqual(nested.adapter.boundary_count, 0)
        d = nested.state['gpgme_collector_birth_refusal']
        self.assertEqual((d['requested_pid'], d['matching_valid_inferior_count'], d['known_parent_count']), (20, 2, 1))
        tree = ast.parse((B / 'candidate/outer/deps/gpgme_boundary_collector.py').read_bytes())
        allstop = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_all_stop')
        proc_line = next(n.lineno for n in ast.walk(allstop) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'proc')
        self.assertIn({'source_role': 'collector', 'line': proc_line}, d['source_frames'])
        self.assertFalse(nested.births)

    def test_later_registration_cannot_rearm_terminal_refusal(self):
        for stage in (0, 1):
            x = Kernel(stage)
            self.assertEqual(x.run(), 'gpgme_collector_unowned_or_unobserved_birth')
            first = copy.deepcopy(x.state['gpgme_collector_birth_refusal'])
            x.infs.append(Inf(20 + stage, 4 + stage))
            self.assertEqual(x.run(), 'gpgme_collector_unowned_or_unobserved_birth')
            self.assertEqual(x.state['gpgme_collector_birth_refusal'], first)
            self.assertNotIn(20 + stage, x.o.known)
            self.assertFalse(x.births)

    def test_parent_recheck_failure_keeps_guard_and_never_emits_birth_diagnostic(self):
        x = Kernel(present=True)
        original_stat = x.o._stat_process
        reads = []
        def stat(pid):
            reads.append(pid)
            value, detail = original_stat(pid)
            if pid == 13:
                value['start_ticks'] -= 1
            return value, detail
        x.o._stat_process = stat
        with self.assertRaisesRegex(RuntimeError, '^gpgme_collector_owned_birth_changed$'):
            x.o.proc(20)
        self.assertEqual(reads, [20, 13])
        self.assertNotIn('gpgme_collector_birth_refusal', x.state)
        self.assertNotIn(20, x.o.known)

    def test_diagnostic_failure_has_no_reobservation_and_preserves_reason(self):
        x = Kernel()
        reads = []
        stat = x.o._stat_process
        x.o._stat_process = lambda pid: (reads.append(pid) or stat(pid))
        def capture(*args):
            raise ValueError('SENTINEL_SECRET_EXCEPTION_TEXT')
        x.o._record_birth_refusal = capture
        with self.assertRaisesRegex(RuntimeError, '^gpgme_collector_unowned_or_unobserved_birth$'):
            x.o.proc(20)
        self.assertEqual(reads, [20])
        self.assertTrue(x.o._birth_refusal_attempted)
        self.assertNotIn('gpgme_collector_birth_refusal', x.state)
        self.assertNotIn('SENTINEL_SECRET', json.dumps(x.state))

    def test_unknown_caller_filename_and_private_fields_do_not_escape(self):
        x = Kernel()
        name = '/private/SENTINEL_SECRET_CALLSITE.py'
        ns = {'x': x}
        exec(compile('def caller():\n    x.o.proc(20)\n', name, 'exec'), ns)
        with self.assertRaisesRegex(RuntimeError, '^gpgme_collector_unowned_or_unobserved_birth$'):
            ns['caller']()
        d = x.state['gpgme_collector_birth_refusal']
        raw = json.dumps(d)
        self.assertNotIn('SENTINEL', raw)
        self.assertNotIn('/private/', raw)
        self.assertLess(len(raw), 4096)
        self.assertTrue(any(v['source_role'] == 'other' for v in d['source_frames']))

    def test_single_matching_valid_inferior_and_both_parent_conjuncts(self):
        cases = [(0, True), (1, False), (2, True)]
        for count, parent_known in cases:
            x = Kernel(present=False, wrongparent=not parent_known)
            x.infs += [Inf(20, 4+i) for i in range(count)]
            with self.subTest(count=count, parent_known=parent_known):
                with self.assertRaisesRegex(RuntimeError, '^gpgme_collector_unowned_or_unobserved_birth$'):
                    x.o.proc(20)
                d = x.state['gpgme_collector_birth_refusal']
                self.assertEqual(d['matching_valid_inferior_count'], count)
                self.assertEqual(d['known_parent_count'], int(parent_known))
                self.assertEqual(d['known_parent_identity'], x.original if parent_known else None)
                self.assertNotIn(20, x.o.known)

    def test_unmodified_runtime_sources_and_exact_final_graph(self):
        old = json.loads((PREV / 'SOURCE-COMPOSITION.json').read_bytes())
        new = json.loads((B / 'SOURCE-COMPOSITION.json').read_bytes())
        before = {v['relative_path']: v['selected'] for v in old['files']}
        after = {v['relative_path']: v['selected'] for v in new['files']}
        self.assertEqual(set(before), set(after))
        changed = {n for n in before if before[n] != after[n]}
        self.assertEqual(changed, {'outer/deps/gpgme_boundary_collector.py'})
        for ref in after.values():
            self.assertEqual(hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest(), ref['sha256'])
        uid = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-UID-WITNESS-SOURCE-20261115')
        hostpath = uid / 'host/ownc_root_controller.py'
        host = types.ModuleType('independent_exact_host')
        host.__file__ = str(hostpath)
        exec(compile(hostpath.read_bytes(), str(hostpath), 'exec'), host.__dict__)
        rows = []
        for variant in ('worker_cached', 'extra_fork', 'forbidden_gpg_home', 'wrong_gpgconf_name'):
            plan = json.loads((B / 'inputs' / variant / 'STATIC-PLAN.json').read_bytes())
            prepared = host.inspect_plan(plan)
            ns = host.load_module(plan['source_refs']['namespace'], 'independent_namespace_' + variant)
            _, bundle = host.build_bundles(plan, prepared, ns, operation_id='independent-source-no-actor', nonce='0'*32, deadline=1., validation_only=True)
            self.assertEqual(bundle['collector_ref'], prepared['gpgme_binding']['collector'])
            self.assertEqual(bundle['collector_ref']['sha256'], 'f2d8098dd9ea29e2ef9db75ecfaaab415aff303aaef9240fdc4641817c35d8fa')
            self.assertEqual(plan['budgets'], json.loads((PREV / 'inputs' / variant / 'STATIC-PLAN.json').read_bytes())['budgets'])
            rows.append({'variant': variant, 'collector_ref': bundle['collector_ref'], 'actual_consumers_passed': True, 'budgets_unchanged': True})
        (R / 'ACTUAL4-INDEPENDENT-CONSUMERS.json').write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls))
    text = stream.getvalue()
    (R / 'independent_controls.log').write_text(text)
    for ref in snapshot['refs']:
        assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest() == ref['sha256'], 'drift: ' + ref['path']
    print(text)
    raise SystemExit(0 if result.wasSuccessful() else 1)
