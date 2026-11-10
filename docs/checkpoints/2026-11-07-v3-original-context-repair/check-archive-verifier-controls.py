#!/usr/bin/env python3
"""Checker-only controls; no product qualification or external effects."""
from contextlib import nullcontext
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import types

CHECKER = Path(__file__).resolve().with_name('check-archive-containment.py')
spec = importlib.util.spec_from_file_location('archive_review_checker', CHECKER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
controls = []
original_open = os.open
scratch = Path(tempfile.mkdtemp(prefix='sol-v3-archive-review-20261110-controls-', dir='/home/jericho/.dsh/tmp'))
boundary = None
try:
    bench = scratch / 'bench'; bench.mkdir(mode=0o700)
    external = scratch / 'outside'; external.write_bytes(b'unchanged\n'); external.chmod(0o600)
    link = bench / 'escape'; link.symlink_to(external)
    boundary = m.Boundary(bench, CHECKER.parent)
    sys.addaudithook(boundary)
    os.open = boundary.descriptor_open
    before = m.tree(scratch)
    for label, effect in (
        ('chmod_final_symlink_denied', lambda: os.chmod(link, 0o644)),
        ('utime_final_symlink_denied', lambda: os.utime(link, ns=(1, 1))),
        ('chown_final_symlink_denied', lambda: os.chown(link, os.getuid(), os.getgid())),
        ('truncate_final_symlink_denied', lambda: os.truncate(link, 0)),
    ):
        try:
            effect(); denied = False
        except PermissionError:
            denied = True
        controls.append(dict(check=label, passed=denied))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for label, effect in (
            ('sendto_denied_before_send', lambda: sock.sendto(b'inert', ('127.0.0.1', 9))),
            ('bind_denied_before_bind', lambda: sock.bind(('127.0.0.1', 0))),
        ):
            try:
                effect(); denied = False
            except PermissionError:
                denied = True
            controls.append(dict(check=label, passed=denied))
    argv = [sys.executable, '-I', '-B', str(CHECKER.parent / 'hermes_cli/friday_workspace_7z_codec.py'), '--worker', str(os.getpid())]
    environment = {'LANG': 'C.UTF-8', 'PATH': '/usr/bin:/bin'}
    for label, executable, child_env in (
        ('subprocess_executable_mismatch_denied_audit_probe', '/bin/true', environment),
        ('subprocess_environment_mismatch_denied_audit_probe', sys.executable, dict(environment, HOME='/tmp')),
    ):
        try:
            boundary('subprocess.Popen', (executable, argv, '/', child_env)); denied = False
        except PermissionError:
            denied = True
        controls.append(dict(check=label, passed=denied))
    boundary('subprocess.Popen', (sys.executable, argv, '/', environment))
    controls.append(dict(check='expected_subprocess_shape_allowed_audit_probe', passed=len(boundary.children) == 1))
    controls.append(dict(check='external_tree_unchanged', passed=m.tree(scratch) == before))
    boundary.active = False
    os.open = original_open

    class WebTurn: pass
    class WebCall:
        def __init__(self, *args): pass
    context = types.ModuleType('agent.web_call_context')
    context.WebTurn = WebTurn; context.WebCall = WebCall
    context.bind_web_call = lambda call: nullcontext()
    sys.modules['agent.web_call_context'] = context
    m.admitted_scope = lambda scope, source: nullcontext()
    home = scratch / 'authorization' / 'profiles' / 'review'; workspace = home / 'workspace'
    workspace.mkdir(parents=True, mode=0o700)
    source = types.SimpleNamespace(_identity=types.SimpleNamespace(runtime_home=home, authorization_home=scratch / 'authorization'))
    for kind, expected_pass in (('regular', True), ('fifo', False), ('symlink', False), ('hardlink', False)):
        def write_file_tool(**args):
            output = workspace / args['path']; output.mkdir(mode=0o700)
            item = output / 'inside.txt'; item.write_bytes(b'expected\n'); item.chmod(0o600)
            if kind == 'fifo': os.mkfifo(output / 'extra.fifo', 0o600)
            if kind == 'symlink': (output / 'extra.link').symlink_to(item)
            if kind == 'hardlink': os.link(item, output / 'extra.link')
            return json.dumps(dict(success=True, verified=True))
        result = m.check_case('checker_' + kind, source, b'inert fixture', '.zip', 'zip_extract', {'inside.txt': b'expected\n'}, (None, types.SimpleNamespace(write_file_tool=write_file_tool)))
        controls.append(dict(check='output_' + kind, observed_passed=result['passed'], passed=result['passed'] is expected_pass))

    # Execute the actual isolated optional-fixture branch under fault injection;
    # this exercises checksum binding and custody aggregation without product I/O.
    module = ast.parse(CHECKER.read_text())
    main = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    try_body = next(n.body for n in main.body if isinstance(n, ast.Try))
    branch = next(n for n in try_body if isinstance(n, ast.If) and isinstance(n.test, ast.Attribute) and n.test.attr == 'seven_fixture')
    block = compile(ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])), str(CHECKER), 'exec')
    payload = b'fault-injection-fixture'
    for mode, wanted in (('changed_before_read', 'checker_seven_fixture_changed_before_consumption'), ('changed_after_read', False), ('unchanged', True)):
        known = '4ffbacf1b16a55a90ed4e92894e851e905fd090d82dbc48a8c773225697335e2'
        calls = [0]
        def fingerprint(path):
            calls[0] += 1
            return {'sha256': known if calls[0] == 1 or mode != 'changed_after_read' else 'changed'}
        globals_ = dict(m.__dict__, args=types.SimpleNamespace(seven_fixture=types.SimpleNamespace(read_bytes=lambda: payload)), fingerprint=fingerprint,
                        digest=lambda data: 'changed' if mode == 'changed_before_read' else known,
                        check_case=lambda *a: dict(passed=True, result={}), report=dict(py7zr_version='1.1.0', checks=[], remaining_gaps=[]), source=None, modules=None)
        try:
            exec(block, globals_)
            observed = globals_['report']['checks'][0]['passed']
        except RuntimeError as exc:
            observed = str(exc)
        controls.append(dict(check='fixture_custody_' + mode, observed=observed, passed=observed == wanted))
finally:
    if boundary is not None: boundary.active = False
    os.open = original_open
    shutil.rmtree(scratch)
report = dict(schema='friday.v3.archive-checker-review-controls.v1', checker_sha256=hashlib.sha256(CHECKER.read_bytes()).hexdigest(),
              controls=controls, passed=all(row['passed'] for row in controls),
              scratch_removed=not scratch.exists(), product_effects=False, note='Boundary controls use real denied APIs; subprocess and custody controls are explicitly checker-only fault injection, never product acceptance.')
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report['passed'] and report['scratch_removed'] else 1)
