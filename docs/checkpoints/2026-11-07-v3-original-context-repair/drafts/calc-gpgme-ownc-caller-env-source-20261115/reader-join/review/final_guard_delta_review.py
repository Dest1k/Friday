"""Review only the final two added guards; preserve unchanged reader results."""
import ast
import hashlib
import json
import os
from pathlib import Path
import time
import types

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'host/ownc_namespace_supervisor.py'
PREVIOUS = '7684a8bbf9354f82a976a2fd0cfbbb427e7c5211d942ea01e31a665a695de50b'
FINAL = '7d3143f1bf85d18cada9fd5b692a4aada76ff0e53d4b47d13f7037dbc476eea5'


def main():
    source = SOURCE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == FINAL
    additions = [
        b"            require(time.monotonic() < cfg['startup_deadline_monotonic'], 'fixture_original_startup_before_gdb')\n",
        b"            require(time.monotonic() < ready_deadline and child.poll() is None,\n                    'fixture_original_startup_before_ready_go')\n",
    ]
    reconstructed = source
    for addition in additions:
        assert reconstructed.count(addition) == 1
        reconstructed = reconstructed.replace(addition, b'', 1)
    assert hashlib.sha256(reconstructed).hexdigest() == PREVIOUS
    guards = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            args = node.value.args
            if len(args) == 2 and isinstance(args[1], ast.Constant) and args[1].value in (
                    'fixture_original_startup_before_gdb', 'fixture_original_startup_before_ready_go'):
                guards[args[1].value] = compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec')
    assert len(guards) == 2
    results = []
    def require(ok, code):
        if not ok:
            raise RuntimeError(code)
    for key, guard in guards.items():
        for label, expired, exited in (('current alive', False, False), ('original startup expired', True, False)):
            env = {'time': time, 'require': require, 'cfg': {'startup_deadline_monotonic': time.monotonic() + (-1 if expired else 1)},
                   'ready_deadline': time.monotonic() + (-1 if expired else 1),
                   'child': types.SimpleNamespace(poll=lambda: 0 if exited else None)}
            try:
                exec(guard, env)
            except RuntimeError as exc:
                assert expired and str(exc) == key
            else:
                assert not expired
            results.append({'guard': key, 'control': label, 'result': 'PASS'})
    key = 'fixture_original_startup_before_ready_go'
    try:
        exec(guards[key], {'time': time, 'require': require, 'ready_deadline': time.monotonic() + 1,
                          'child': types.SimpleNamespace(poll=lambda: 0)})
    except RuntimeError as exc:
        assert str(exc) == key
    else:
        raise AssertionError('exited child accepted')
    results.append({'guard': key, 'control': 'child exited', 'result': 'PASS'})
    output = HERE / 'final-guard-controls.json'
    output.write_text(json.dumps({'previous_sha256': PREVIOUS, 'final_sha256': FINAL,
                      'exact_two_guard_delta_verified': True, 'unchanged_reader_controls_reused': True,
                      'controls': results, 'passed': len(results), 'live_effects': False}, sort_keys=True, indent=2) + '\n')
    os.chmod(output, 0o600)
    print(json.dumps({'passed': len(results), 'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
