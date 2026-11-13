"""Exact checker AST + genuine synthetic files only; never read actual H/config.

Only selected reviewed functions are compiled. All synthetic files live in a
temporary directory below this script's review directory and are removed.
"""
import ast
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import types
from datetime import datetime, timezone, timedelta

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source/current209.py'
ORIGINAL = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT209-PREINTENT-COMPOSITION-20261113/source/current209.py')
EXPECTED_ORIGINAL = 'd6f981a23493f3234dd46595071b0e0f6bc0efb020aa05ca32604c28daca1491'
EXPECTED_SOURCE = '24215d1fca8d59e4109e5934464cf4cfbcf6d2dd48d33b7d44c3fc54377de47f'
started = datetime.now(timezone.utc)
raw = SOURCE.read_bytes()
base_raw = ORIGINAL.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED_SOURCE
assert hashlib.sha256(base_raw).hexdigest() == EXPECTED_ORIGINAL
tree = ast.parse(raw)
original_tree = ast.parse(base_raw)
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
base_functions = {n.name: n for n in original_tree.body if isinstance(n, ast.FunctionDef)}
results = []


def checked(name, operation):
    operation()
    results.append({'name': name, 'state': 'PASS'})


def eq(a, b):
    assert a == b, (a, b)


def refused(operation, code):
    try:
        operation()
    except ValueError as exc:
        eq(str(exc), code)
    else:
        raise AssertionError('Expected refusal ' + code)


# Restore only the two deliberately changed collection expressions and remove
# only the new literal-bound/helper nodes. Every remaining AST must be identical.
old_configs = next(n.value for n in ast.walk(base_functions['_observe_current'])
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'configs' for t in n.targets))


class RestoreCollection(ast.NodeTransformer):
    calls = 0

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'profile_config_refs':
            assert not node.args and not node.keywords
            self.calls += 1
            return copy.deepcopy(old_configs)
        return self.generic_visit(node)


restored = copy.deepcopy(tree)
restored.body = [n for n in restored.body
                 if not (isinstance(n, ast.FunctionDef) and n.name == 'profile_config_refs')
                 and not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PROFILE_CONFIG_LIMITS' for t in n.targets))]
normalizer = RestoreCollection()
restored = normalizer.visit(restored)
checked('only_literal_bound_helper_and_two_collection_expressions_changed',
        lambda: (eq(normalizer.calls, 2), eq(ast.dump(restored), ast.dump(original_tree))))
checked('readonly_strict_decisions_and_default_reader_functions_unchanged',
        lambda: [eq(ast.dump(functions[name]), ast.dump(base_functions[name]))
                 for name in ('observe', 'observe_readonly', 'check', 'decisions',
                              '_read_bounded', 'read', 'ref', 'read_reference',
                              'read_saved_reference', 'reference_shape', 'identity')])

# Compile exact selected source AST. No product module import, no source module
# execution, no actual collector/Store/native/API calls.
selected = ['need', 'digest', 'sha', 'canonical_path', 'identity', '_read_bounded',
            'read', 'reference_shape', 'read_reference', 'ref', 'profile_config_refs']
ns = dict(os=os, Path=Path, stat=stat, re=re, hashlib=hashlib,
          DEFAULT_LIMIT=1024**2, EXACT_LIMIT=24*1024**2)
const = next(n for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'PROFILE_CONFIG_LIMITS' for t in n.targets))
exec(compile(ast.Module(body=[copy.deepcopy(const), *[copy.deepcopy(functions[name]) for name in selected]], type_ignores=[]), str(SOURCE), 'exec'), ns)
checked('fixed_exact_label_limits', lambda: eq(ns['PROFILE_CONFIG_LIMITS'],
        {'default': 4*1024**2, 'dest': 1024**2, 'tester': 4*1024**2}))
checked('default_read_and_ref_no_limit_keyword', lambda: (
        eq(str(inspect.signature(ns['read'])), '(path, *, private=True)'),
        eq(str(inspect.signature(ns['ref'])), '(path, *, private=True)')))

with tempfile.TemporaryDirectory(prefix='synthetic-config-review-', dir=HERE) as temp:
    root = Path(temp)
    os.chmod(root, 0o700)
    paths = {label: root / label / 'config.yaml' for label in ns['PROFILE_CONFIG_LIMITS']}
    for p in paths.values():
        p.parent.mkdir(mode=0o700)
    ns['DATABASES'] = {label: p.parent / 'state.db' for label, p in paths.items()}

    def put(label, data, mode=0o600):
        paths[label].write_bytes(data)
        paths[label].chmod(mode)

    def seed_known_sizes():
        for label, size in {'default': 3382001, 'dest': 20782, 'tester': 3176638}.items():
            put(label, label[0].encode() * size)

    seed_known_sizes()
    refs = ns['profile_config_refs']()
    checked('known_actual_sizes_reproduced_with_synthetic_bytes_and_exact_refs', lambda: [
        eq(refs[label], {'path': str(paths[label]), 'bytes': len(paths[label].read_bytes()),
                        'sha256': hashlib.sha256(paths[label].read_bytes()).hexdigest()})
        for label in paths])
    checked('strict_sized_reread_accepts_large_synthetic_default_and_tester', lambda: [
        eq(ns['read_reference'](refs[label], private=False), paths[label].read_bytes())
        for label in paths])
    checked('generic_default_read_and_ref_still_refuse_above_1MiB', lambda: [
        refused(lambda f=f: f(paths['default'], private=False), 'F07_INPUT_CAS_OR_SIZE_CHANGED')
        for f in (ns['read'], ns['ref'])])

    # Genuine inclusive and overflow files, with the exact helper/guard.
    for label, limit in ns['PROFILE_CONFIG_LIMITS'].items():
        seed_known_sizes()
        put(label, b'x' * limit)
        checked(label + '_inclusive_bound_accepted', lambda label=label, limit=limit:
                eq(ns['profile_config_refs']()[label]['bytes'], limit))
        put(label, b'x' * (limit + 1))
        calls = []
        bounded = ns['_read_bounded']

        def traced(path, limit, private):
            calls.append((str(path), limit, private))
            return bounded(path, limit, private)

        ns['_read_bounded'] = traced
        checked(label + '_overflow_refused_without_discovery_or_fallback',
                lambda: refused(ns['profile_config_refs'], 'F07_INPUT_CAS_OR_SIZE_CHANGED'))
        checked(label + '_overflow_exact_once_and_fixed_bound', lambda label=label, limit=limit:
                eq([c for c in calls if c[0] == str(paths[label])], [(str(paths[label]), limit, False)]))
        ns['_read_bounded'] = bounded

    seed_known_sizes()
    put('default', b'a' * 1200000, 0o664)
    checked('private_false_retains_prior_0664_policy', lambda:
            eq(ns['profile_config_refs']()['default']['bytes'], 1200000))
    paths['default'].chmod(0o602)
    checked('world_writable_config_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_UNSAFE_INPUT'))
    paths['default'].chmod(0o600)

    class OsProxy:
        def __getattr__(self, name):
            return getattr(os, name)

        def getuid(self):
            return os.getuid() + 1

    ns['os'] = OsProxy()
    checked('nonowner_config_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_UNSAFE_INPUT'))
    ns['os'] = os
    hardlink = root / 'second-link'
    os.link(paths['default'], hardlink)
    checked('hardlinked_config_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_UNSAFE_INPUT'))
    hardlink.unlink()
    original = paths['default'].with_suffix('.original')
    paths['default'].rename(original)
    paths['default'].symlink_to(original)
    checked('leaf_symlink_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_NO_SYMLINKS_REQUIRED'))
    paths['default'].unlink()
    original.rename(paths['default'])
    alternate = root / 'linked-parent'
    alternate.symlink_to(paths['default'].parent, target_is_directory=True)
    ns['DATABASES']['default'] = alternate / 'state.db'
    checked('parent_symlink_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_NO_SYMLINKS_REQUIRED'))
    ns['DATABASES']['default'] = paths['default'].parent / 'state.db'
    alternate.unlink()

    # Mutate the genuine synthetic file between stream.read and after-fstat.
    class ReadMutation:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            return self.stream.fileno()

        def read(self, count):
            result = self.stream.read(count)
            with paths['default'].open('r+b') as writer:
                writer.write(b'M')
                writer.flush()
                os.fsync(writer.fileno())
            return result

    class MutationOs:
        def __getattr__(self, name):
            return getattr(os, name)

        def fdopen(self, *args, **kwargs):
            return ReadMutation(os.fdopen(*args, **kwargs))

    ns['os'] = MutationOs()
    checked('in_read_content_and_ctime_mutation_refused', lambda:
            refused(ns['profile_config_refs'], 'F07_INPUT_CAS_OR_SIZE_CHANGED'))
    ns['os'] = os
    seed_known_sizes()
    refs = ns['profile_config_refs']()

    # Exact unchanged final CAS statement, isolated from genuine runtime collector.
    cas = next(n for n in functions['_observe_current'].body
               if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
               and any(isinstance(a, ast.Constant) and a.value == 'F07_FINAL_SQL_HISTORY_ONCE_CURSOR_CONFIG_OR_LOG_CAS_CHANGED' for a in n.value.args))
    cas_code = compile(ast.Module(body=[copy.deepcopy(cas)], type_ignores=[]), str(SOURCE), 'exec')
    original_ref = ns['ref']
    ns.update(databases=lambda: 'db', dbs='db', history=lambda *_: 'history', hist='history',
              custody=lambda: 'owned', owned='owned', cursor='cursor',
              technical_log_cursor=lambda: 'logs', logs='logs',
              STATE=root, effect={}, stage='BASELINE', configs=refs)
    ns['ref'] = lambda p: 'cursor'
    checked('exact_final_CAS_accepts_unchanged_synthetic_configs', lambda: exec(cas_code, ns))
    put('tester', b'z' * refs['tester']['bytes'])
    checked('exact_final_CAS_rejects_same_length_config_change', lambda:
            refused(lambda: exec(cas_code, ns), 'F07_FINAL_SQL_HISTORY_ONCE_CURSOR_CONFIG_OR_LOG_CAS_CHANGED'))
    ns['ref'] = original_ref
    checked('strict_exact_sized_reread_rejects_same_length_hash_change', lambda:
            refused(lambda: ns['read_reference'](refs['tester'], private=False), 'F07_EXACT_REFERENCE_CHANGED'))
    seed_known_sizes()
    refs = ns['profile_config_refs']()
    wrong = dict(refs['default'], bytes=refs['default']['bytes'] - 1)
    checked('strict_exact_sized_reread_rejects_wrong_size', lambda:
            refused(lambda: ns['read_reference'](wrong, private=False), 'F07_INPUT_CAS_OR_SIZE_CHANGED'))

    # Exact existing privacy binding plus exact existing sized reread loop.
    decisions = functions['decisions']
    privacy_binding = next(n for n in decisions.body
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
        and any(isinstance(a, ast.Constant) and a.value == 'F07_CURRENT_CONFIG_ROOTS_BASIS_CHANGED' for a in n.value.args))
    markers = next(n for n in decisions.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'markers' for t in n.targets))
    config_loop = next(n for n in decisions.body if isinstance(n, ast.For)
                       and isinstance(n.iter, ast.Call)
                       and isinstance(n.iter.func, ast.Attribute)
                       and isinstance(n.iter.func.value, ast.Subscript)
                       and isinstance(n.iter.func.value.slice, ast.Constant)
                       and n.iter.func.value.slice.value == 'profile_configs')
    privacy_code = compile(ast.Module(body=copy.deepcopy([privacy_binding, markers, config_loop]), type_ignores=[]), str(SOURCE), 'exec')
    ns.update(privacy={'effective_roots_profile_config_refs': refs},
              actual={'profile_configs': refs}, protected=['/synthetic-private-marker-no-real-data'])
    checked('exact_privacy_nodes_accept_large_sized_config_refs', lambda: exec(privacy_code, ns))
    ns['privacy'] = {'effective_roots_profile_config_refs': {}}
    checked('exact_privacy_binding_refuses_config_ref_mismatch', lambda:
            refused(lambda: exec(privacy_code, ns), 'F07_CURRENT_CONFIG_ROOTS_BASIS_CHANGED'))
    marker = ns['protected'][0].encode()
    put('default', b'p' * (1200000 - len(marker)) + marker)
    refs = ns['profile_config_refs']()
    ns.update(privacy={'effective_roots_profile_config_refs': refs}, actual={'profile_configs': refs})
    checked('exact_privacy_sized_reread_rejects_private_marker_in_large_config', lambda:
            refused(lambda: exec(privacy_code, ns), 'F07_PRIVATE_ROOT_IN_PRODUCT_CONFIG'))

finished = datetime.now(timezone.utc)
eq(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), EXPECTED_SOURCE)
eq(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), EXPECTED_ORIGINAL)
report = dict(schema='frw.F07.config-bound-independent-synthetic-controls.v1',
              state='PASS_SOURCE_ONLY_SYNTHETIC', count=len(results), checks=results,
              original_sha256=EXPECTED_ORIGINAL, reviewed_source_sha256=EXPECTED_SOURCE,
              boundary=dict(actual_H_or_config_reads=0, actual_collector_calls=0,
                            product_native_Store_API_model_calls=0, runtime_admission=False,
                            exact_selected_AST=True, synthetic_file_IO_only=True,
                            exact_final_CAS_node_isolated=True, exact_privacy_nodes_isolated=True,
                            temporary_synthetic_files_removed=True),
              timing=dict(started_moscow=started.astimezone(timezone(timedelta(hours=3))).isoformat(),
                          completed_moscow=finished.astimezone(timezone(timedelta(hours=3))).isoformat(),
                          elapsed_seconds=(finished-started).total_seconds()))
(HERE/'INDEPENDENT-CONFIG-BOUND-CONTROLS.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({'state':report['state'], 'count':report['count'],
                  'source_sha256':EXPECTED_SOURCE, 'elapsed_seconds':report['timing']['elapsed_seconds']}))
