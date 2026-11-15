"""Independent AST/source mocks only: never import/run a fixture actor."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat

BASE = Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-ENV-DELTA-SOURCE-20261115')
REVIEW = BASE / 'review'
PATHS = ['host/ownc_root_controller.py', 'host/ownc_namespace_supervisor.py', 'driver/ownc_gdb.py']
sources = {name: (BASE / name).read_bytes() for name in PATHS}
trees = {name: ast.parse(raw, filename=name) for name, raw in sources.items()}
results = []


def record(name, operation):
    try:
        detail = operation()
        results.append(dict(name=name, outcome='PASS', detail=detail))
    except Exception as exc:
        results.append(dict(name=name, outcome='FAIL', exception_class=type(exc).__name__, detail=str(exc)))


def demand(condition, message):
    if not condition:
        raise AssertionError(message)


def subset(name, names, extras=None):
    selected = [node for node in trees[name].body if isinstance(node, ast.FunctionDef) and node.name in names]
    demand({node.name for node in selected} == set(names), 'source function selection')
    scope = dict(ast=ast, hashlib=hashlib, json=json, re=re, Path=Path)
    if extras:
        scope.update(extras)
    exec(compile(ast.Module(body=selected, type_ignores=[]), name, 'exec'), scope)
    return scope


def refused(call, message):
    try:
        call()
    except RuntimeError as exc:
        demand(str(exc) == message, 'refusal changed: ' + str(exc))
        return
    raise AssertionError('required refusal absent')


root = subset(PATHS[0], ['need', 'namespace_argv'])
driver = subset(PATHS[2], ['declared_environment', 'construct_inferior_environment',
                         'environment_diagnostic', 'validate_inferior_environment'],
                {'require': root['need']})
supervisor = subset(PATHS[1], ['require', 'environment_diagnostic', 'validate_supervisor_environment'],
                    {'WORK': Path('/mock-only/not-opened')})
plan_path = BASE / 'inputs/worker_cached/STATIC-PLAN.json'
real_plan_raw = plan_path.read_bytes()
real_environment = json.loads(real_plan_raw)['target_environment']


class Builder:
    def __init__(self, extra=None):
        self.extra = extra or {}
    def build_namespace(self, **kwargs):
        self.command = kwargs['command']
        env = dict(real_environment)
        env.pop('DEBUGINFOD_URLS')
        env.update(self.extra)
        return ['/mock/bwrap', '--unshare-all', *[item for k, v in env.items()
                for item in ['--setenv', k, v]], '--', *self.command]


class Debugger:
    def __init__(self):
        self.commands = []
    def execute(self, command, to_string=False):
        demand(to_string is True, 'noncaptured debugger command')
        self.commands.append(command)
        return ''


def namespace_construction():
    builder = Builder()
    plan = dict(target_environment=real_environment, readonly_roots=['/mock/readonly'],
                binding_root='/mock/bind', source_refs={'supervisor': {'path': '/mock/supervisor.py'}})
    argv = root['namespace_argv'](plan, builder, work='/mock/work', job_ref={'path': '/mock/job', 'sha256': '0'*64})
    launcher = ast.parse(builder.command[-1])
    last = launcher.body[-1].value
    demand(isinstance(last, ast.Call) and isinstance(last.func, ast.Attribute)
           and isinstance(last.func.value, ast.Name) and last.func.value.id == 'os'
           and last.func.attr == 'execve', 'execve is not launcher terminal operation')
    executable, supervisor_argv, env = [ast.literal_eval(node) for node in last.args]
    demand(executable == '/usr/bin/python3' and supervisor_argv[-2] == '--job-ref-json', 'exec target/argv')
    demand(env == real_environment, 'execve environment differs from real declaration')
    demand(argv[argv.index('--')-3:argv.index('--')] == ['--setenv', 'DEBUGINFOD_URLS', ''], 'namespace explicit debug URL')
    refused(lambda: root['namespace_argv'](plan, Builder({'EXTRA_UNKNOWN': 'private-value'}),
            work='/mock/work', job_ref={}), 'ownc_builder_complete_environment_mismatch')
    return {'real_environment_count': len(env), 'execve_full_dictionary': True,
            'unexpected_builder_key_refused': True}


def debugger_construction():
    debugger = Debugger()
    before = dict(os.environ)
    driver['construct_inferior_environment'](debugger, real_environment)
    demand(dict(os.environ) == before, 'debugger Python environ mutated')
    expected_commands = ['set confirm off', 'unset environment'] + [
        'set environment ' + k + '=' + v for k, v in sorted(real_environment.items())]
    demand(debugger.commands == expected_commands, 'construction command order/full contents')
    for k, v in [('A\nshow version', 'x'), ('A\rshow version', 'x'), ('A\x00B', 'x'),
                 ('A=B', 'x'), ('A;show_version', 'x'), ('', 'x'), ('9BAD', 'x'),
                 ('GOOD', 'x\nshow version'), ('GOOD', 'x\rshow version'), ('GOOD', 'x\x00y'),
                 ('GOOD', ' padded '), ('FRW_NATIVE_X', 'x'), ('FRW_HELD_FIXTURE_CONFIG', 'x')]:
        bad = Debugger()
        try:
            driver['construct_inferior_environment'](bad, {k: v})
        except RuntimeError:
            demand(bad.commands == [], 'unsafe declaration executed a debugger command')
        else:
            raise AssertionError('unsafe declaration accepted')
    return {'commands': len(debugger.commands), 'all_validation_precedes_commands': True,
            'python_environment_unchanged': True}


def diagnostic_bounds():
    for scope in (driver, supervisor):
        actual = {'A'+str(i): 'secret-value-'+str(i) for i in range(80)}
        actual['K'*200] = 'private'
        payload = scope['environment_diagnostic'](actual, {'EXPECTED': 'other-private'}, phase='PHASE',
                                                nonce='0'*32, exception_class='RuntimeError')
        serialized = json.dumps(payload)
        demand('secret-value' not in serialized and 'other-private' not in serialized, 'private values leaked')
        demand(payload['extra_count'] == 81 and len(payload['extra_keys']) == 32, 'diagnostic count/list bound')
        demand(all(len(k) <= 128 for k in payload['extra_keys']), 'diagnostic key bound')
        long_name = 'K'*200+'\udc80'
        long_payload = scope['environment_diagnostic']({long_name: 'private-value'}, {}, phase='PHASE',
                                                      nonce='0'*32, exception_class='RuntimeError')
        demand(long_payload['extra_keys'] == ['sha256:'+hashlib.sha256(
            long_name.encode('utf-8', 'surrogatepass')).hexdigest()], 'long surrogate key hash')
    return {'both_diagnostics': True, 'list_maximum': 32, 'no_plaintext_values': True}


def strict_driver_compare():
    expected = {'A': 'secret-one', 'B': ''}
    good = 'A=secret-one\nB=\n'
    demand(driver['validate_inferior_environment'](good, expected) == expected, 'positive full compare')
    for text, code in [('A=secret-one\n', 'fixture_complete_startup_environment_mismatch'),
                       (good+'EXTRA=secret-two\n', 'fixture_complete_startup_environment_mismatch'),
                       ('A=changed\nB=\n', 'fixture_complete_startup_environment_mismatch'),
                       (good+'A=secret-one\n', 'fixture_inferior_environment_duplicate'),
                       ('A=secret-one\nmalformed\n', 'fixture_inferior_environment_encoding')]:
        refused(lambda: driver['validate_inferior_environment'](text, expected), code)
    def broken_publish(value):
        raise OSError('mock diagnostic publication denied')
    refused(lambda: driver['validate_inferior_environment']('A=changed\nB=\n', expected,
            publish=broken_publish, nonce='0'*32), 'fixture_complete_startup_environment_mismatch')
    return {'full_comparison': True, 'missing_extra_changed_duplicate_malformed_refused': True,
            'publish_OSError_preserves_first_refusal': True}


def strict_supervisor_compare():
    payloads = []
    supervisor['new_json'] = lambda path, value: payloads.append(value)
    supervisor['validate_supervisor_environment']({'A': 'x'}, {'A': 'x'}, '0'*32)
    demand(payloads[-1]['exception_class'] is None, 'successful comparison diagnostic class')
    for actual in ({}, {'A': 'y'}, {'A': 'x', 'EXTRA': 'private'}):
        refused(lambda: supervisor['validate_supervisor_environment'](actual, {'A': 'x'}, '0'*32),
                'fixture_supervisor_complete_environment')
    def broken_write(*args):
        raise OSError('mock diagnostic file denied')
    supervisor['new_json'] = broken_write
    refused(lambda: supervisor['validate_supervisor_environment']({'A': 'y'}, {'A': 'x'}, '0'*32),
            'fixture_supervisor_complete_environment')
    return {'missing_extra_changed_refused': True, 'write_OSError_preserves_first_refusal': True}


def native_finally_and_prestart_order():
    run = next(n for n in trees[PATHS[2]].body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    protected = next(n for n in run.body if isinstance(n, ast.Try))
    nested = protected.finalbody[-1]
    demand(isinstance(nested, ast.Try) and nested.finalbody, 'missing nested finally')
    demand('exec(compile(final,' in ast.unparse(nested.finalbody[0]), 'native finally no longer unconditional')
    construct = next(i for i, n in enumerate(protected.body) if 'construct_inferior_environment(' in ast.unparse(n))
    compare = next(i for i, n in enumerate(protected.body) if 'validate_inferior_environment(' in ast.unparse(n))
    starti = next(i for i, n in enumerate(protected.body) if "gdb.execute('starti'" in ast.unparse(n))
    demand(construct < compare < starti, 'inferior ENV setup/compare/starti order')
    setting_loop = protected.body[compare+1]
    demand('set startup-with-shell off' in ast.unparse(setting_loop), 'startup shell setting absent before starti')
    return {'construction_then_complete_compare_then_starti': True,
            'startup_shell_disabled_before_starti': True, 'native_finally_nested_guarantee': True}


def diagnostic_encoding_first_refusal():
    # Python's Unix environment supports surrogateescaped bytes. No actor/process
    # or environment mutation is needed to expose this diagnostic-only encoding edge.
    expected = {'A': 'expected'}
    text = 'A=changed\nUNEXPECTED=\udc80\n'
    refused(lambda: driver['validate_inferior_environment'](text, expected, publish=lambda value: None,
                                                          nonce='0'*32),
            'fixture_complete_startup_environment_mismatch')
    return {'diagnostic_encoding_preserves_first_refusal': True}


def diagnostic_constructor_OSError():
    def denied(*args, **kwargs):
        raise OSError('mock diagnostic constructor denied')
    expected = {'A': 'expected'}
    for scope, action, code in [
            (driver, lambda: driver['validate_inferior_environment']('A=changed\n', expected,
                      publish=lambda value: None, nonce='0'*32),
                      'fixture_complete_startup_environment_mismatch'),
            (supervisor, lambda: supervisor['validate_supervisor_environment']({'A':'changed'}, expected, '0'*32),
                      'fixture_supervisor_complete_environment')]:
        original = scope['environment_diagnostic']
        scope['environment_diagnostic'] = denied
        try:
            refused(action, code)
        finally:
            scope['environment_diagnostic'] = original
    return {'both_constructor_OSError_preserve_first_refusal': True}


def reconstructed_prior_edge():
    # Reconstruct just the guarded diagnostic block from the exact initial draft
    # source read. This is a source-mock regression control, not an executed old
    # artifact nor a runtime observation. The final source remains untouched.
    node = ast.parse(ast.unparse(next(n for n in trees[PATHS[2]].body
                     if isinstance(n, ast.FunctionDef) and n.name == 'validate_inferior_environment'))).body[0]
    publish_if = next(n for n in node.body if isinstance(n, ast.If)
                      and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
                      and n.test.left.id == 'publish')
    guarded = publish_if.body[0]
    demand(isinstance(guarded, ast.Try) and len(guarded.body) == 3, 'final diagnostic guard shape')
    summary, observed_hash, publish = guarded.body
    observed_hash.value.func.value.args[0] = ast.Call(func=ast.Attribute(value=ast.Name(id='text', ctx=ast.Load()),
                                      attr='encode', ctx=ast.Load()), args=[], keywords=[])
    guarded.body = [publish]
    publish_if.body = [summary, observed_hash, guarded]
    prior = dict(driver)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'reconstructed-initial-draft-function', 'exec'), prior)
    try:
        prior['validate_inferior_environment']('A=changed\nUNEXPECTED=\udc80\n', {'A':'expected'},
            publish=lambda value: None, nonce='0'*32)
    except UnicodeEncodeError:
        return {'reconstructed_initial_draft_masks_refusal_with': 'UnicodeEncodeError',
                'original_draft_not_executed': True, 'final_source_unmodified': True}
    raise AssertionError('reconstructed initial draft did not expose diagnostic edge')


record('namespace_explicit_execve_and_full_builder_compare', namespace_construction)
record('inferior_full_construction_and_injection_refusals', debugger_construction)
record('bounded_metadata_no_values', diagnostic_bounds)
record('driver_full_compare_and_publish_OSError', strict_driver_compare)
record('supervisor_full_compare_and_write_OSError', strict_supervisor_compare)
record('native_finally_and_prestart_order', native_finally_and_prestart_order)
record('driver_diagnostic_encoding_first_refusal', diagnostic_encoding_first_refusal)
record('diagnostic_constructor_OSError_first_refusal', diagnostic_constructor_OSError)
record('reconstructed_initial_draft_encoding_edge', reconstructed_prior_edge)

payload = dict(schema='frw.ownc.environment-delta-independent-source-controls.v1',
               source_refs=[dict(path=str(BASE/name), sha256=hashlib.sha256(raw).hexdigest())
                            for name, raw in sources.items()],
               real_plan_ref=dict(path=str(plan_path), sha256=hashlib.sha256(real_plan_raw).hexdigest()),
               checks=results, effects=dict(runtime=False, debugger=False, inferior=False, namespace=False,
                                           network=False, services=False, git=False, profile_changes=False),
               limitation='Pure AST/source mocks; no actual GDB or namespace compatibility qualification.')
raw = (json.dumps(payload, sort_keys=True, indent=2)+'\n').encode()
destination = REVIEW / 'CONTROLS-FINAL.json'
fd = os.open(destination, os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'wb') as stream:
    stream.write(raw)
print(json.dumps(dict(path=str(destination), sha256=hashlib.sha256(raw).hexdigest(), checks=results),
                 sort_keys=True))
