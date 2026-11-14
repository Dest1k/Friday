"""Review frozen source only. All runtime/current/process leaves stay inert.

Author control output is redirected to this review directory; sibling files are
read only. Native projection/run modules are never imported or executed.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest

BASE = Path('/home/jericho/.cache/FRW-SOL-V3-F04-ROOT-ORDINARY-CALLER-CORE-20261115')
REVIEW = BASE / 'review'


def require(ok, code):
    if not ok:
        raise AssertionError(code)


def raw_ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


manifest_path = Path(sys.argv[1])
manifest_sha = sys.argv[2]
manifest_raw = manifest_path.read_bytes()
require(hashlib.sha256(manifest_raw).hexdigest() == manifest_sha, 'FINAL_MANIFEST_DRIFT')
manifest = json.loads(manifest_raw)
refs = manifest['files']
if isinstance(refs, dict):
    refs = list(refs.values())
for ref in refs:
    require(raw_ref(ref['path']) == {k: ref[k] for k in ('path', 'bytes', 'sha256')}, 'FROZEN_LEAF_DRIFT')

# Run the inspected actual author controls with their single output path moved
# into our write scope. __file__ remains their location for exact source reads.
path = BASE / 'caller/check_source.py'
raw = path.read_text()
old = "target = HERE / 'SOURCE-CHECKS.json'"
require(raw.count(old) == 1, 'CONTROL_OUTPUT_SEAM_CHANGED')
edited = raw.replace(old, "target = Path(" + repr(str(REVIEW / 'CALLER-CONTROLS-REVIEW.json')) + ")")
namespace = {'__file__': str(path), '__name__': '_t90_independent_caller_controls'}
log = io.StringIO()
with contextlib.redirect_stdout(log):
    try:
        exec(compile(edited, str(path), 'exec'), namespace)
    except SystemExit as exc:
        require(exc.code in (None, 0), 'CALLER_CONTROLS_FAILED')
caller = json.loads((REVIEW / 'CALLER-CONTROLS-REVIEW.json').read_bytes())
require(caller['failed'] == 0 and caller['all_lifecycle_current_process_effect_leaves_inert'], 'CALLER_CONTROL_REPORT_FAILED')

path = BASE / 'current_stop/test_current_stop.py'
module = types.ModuleType('_t90_independent_current_controls')
module.__file__ = str(path)
exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
result = runner.run(suite)
require(result.wasSuccessful(), 'CURRENT_CONTROLS_FAILED')

path = BASE / 'current_stop/check_static.py'
static_out = io.StringIO()
with contextlib.redirect_stdout(static_out):
    exec(compile(path.read_bytes(), str(path), 'exec'), {'__file__': str(path), '__name__': '_t90_static_controls'})
static = json.loads(static_out.getvalue())
require(static['failed'] == 0, 'CURRENT_STATIC_CONTROLS_FAILED')

# Finish on exactly the same bytes as at control entry.
require(manifest_path.read_bytes() == manifest_raw, 'FINAL_MANIFEST_CHANGED_DURING_REVIEW')
for ref in refs:
    require(raw_ref(ref['path']) == {k: ref[k] for k in ('path', 'bytes', 'sha256')}, 'FROZEN_LEAF_CHANGED_DURING_REVIEW')
report = {
    'schema': 'frw.T90.final-frozen-source-controls.v1', 'source_only': True,
    'manifest': raw_ref(manifest_path),
    'caller': {'passed': caller['passed'], 'failed': caller['failed'], 'report': raw_ref(REVIEW / 'CALLER-CONTROLS-REVIEW.json')},
    'current_stop': {'passed': result.testsRun, 'failed': len(result.failures) + len(result.errors)},
    'current_stop_static': static,
    'source_refs': refs,
    'effects': {'actual_current_or_native_or_product_queries': False,
                'model_or_Office_or_Telegram_or_Git_or_service_effect': False,
                'actual_clock_once_slot_grant_run_scenario_created': False,
                'full_tester_or_native_gateway_import': False,
                'sibling_files_modified': False},
}
target = REVIEW / 'FROZEN-CONTROLS.json'
target.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
target.chmod(0o600)
print(json.dumps({'caller_passed': caller['passed'], 'current_passed': result.testsRun,
                  'static_passed': static['passed'], 'failed': 0,
                  'report': raw_ref(target)}, sort_keys=True))
