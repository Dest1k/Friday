"""Finite source-layer reader/preimage/forward-reverse checks, never an installer.

Real saved209 receipt/input metadata and product read_layers/check_preimages are
used. Only own single-file apply stand is mutated. Success does not qualify a
successor request or the complete normal builder/current/live admission path.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import time

os.umask(0o077)
START = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
signal.alarm(90)
B = Path(__file__).resolve().parent.parent
REPO = Path('/home/jericho/jericho/Friday_rework')
H = REPO / '.runtime/friday-normal-both-workers-frw032'
LAYER = 'f07-malformed-docx-error-provenance-after-source209'
PATCH = 'patches/hermes/' + LAYER + '.patch'
MANIFEST = 'patches/hermes/' + LAYER + '-manifest.json'
TARGET = 'hermes_cli/friday_user_scope.py'
INPUT = Path('/home/jericho/.cache/FRW-SOL-V3-F07-NATIVE209-AFTER208-CORE-20261113/INPUT-SOURCE209.PROSPECTIVE.NOT_INSTALLED.json')
CONSUMER = REPO / 'docs/checkpoints/2026-11-07-v3-original-context-repair/friday_v3_layer_publication.py'
BUILDER = CONSUMER.with_name('build-layer-publication-request.py')
PINS = json.loads((B / 'SOURCE-PINS.json').read_bytes())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(p):
    r = p.read_bytes()
    return {'path': str(p), 'bytes': len(r), 'sha256': digest(r)}


def selected(path, names, namespace):
    tree = ast.parse(path.read_bytes(), filename=str(path))
    nodes = [n for n in tree.body if getattr(n, 'name', None) in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)


checks = []


def passed(name, **facts):
    checks.append({'name': name, 'status': 'PASS', **facts})


before = (B / 'before' / TARGET).read_bytes()
after = (B / 'candidate' / TARGET).read_bytes()
receipt_raw = (H / 'hermes-agent.source.json').read_bytes()
assert digest(receipt_raw) == 'bf60335ab23269c2581118ba45a5485651aacb2a7aa1c7709a852faf9fff5564'
receipt = json.loads(receipt_raw)
input_raw = INPUT.read_bytes()
assert digest(input_raw) == '2805a670402e6265f988501326bf0d8fe26d6209e061b095dd652ef94786367d'
original_input = json.loads(input_raw)
assert len(receipt['layers']) == 209 and len(original_input['project_files']) == 499
assert receipt['files'][TARGET]['sha256'] == digest(before) == '3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474'
assert (H / 'hermes-agent' / TARGET).read_bytes() == before
passed('real_pinned209_receipt_input_and_selected_native_preimage')
manifest = json.loads((B / MANIFEST).read_bytes())
assert manifest['base_commit'] == receipt['commit']
assert manifest['patch'] == PATCH and manifest['patch_sha256'] == digest((B / PATCH).read_bytes())
assert manifest['files'] == [{'path': TARGET, 'before_sha256': digest(before), 'sha256': digest(after),
                             'bytes': len(after), 'mode': '100644', 'new_file': False}]
passed('native_single_file_manifest_matches_actual_before_and_candidate_after')
assert len(manifest['prerequisites']) == 209
assert all(original_input['project_files'].get(k) == v for k, v in manifest['prerequisites'].items())
receipt_patch_pins = {}
for row in receipt['layers']:
    # Existing legacy manifest.json and web-exact-limit.manifest.json do not
    # share the newer filename convention. Join their real pinned patch digest
    # uniquely, never invent a filename or normalize saved historical bytes.
    assert original_input['project_files'][row['manifest']] == row['manifest_sha256']
    matches = [name for name, value in manifest['prerequisites'].items()
               if value == row['patch_sha256']]
    assert len(matches) == 1 and matches[0] not in receipt_patch_pins
    receipt_patch_pins[matches[0]] = row['patch_sha256']
assert receipt_patch_pins == manifest['prerequisites']
passed('all209_real_prefix_patch_prerequisites_exact_no_fixture_chain')

# Execute only these unmodified source-reader/preimage methods, never the
# publisher's module main, current observer, install or service code.
assert pin(CONSUMER) == PINS['unchanged_publication_consumer']
ns = {'Path': Path, 'json': json, 'os': os, 'stat': stat, 'hashlib': hashlib}
selected(CONSUMER, {'Refused', 'require', 'digest', 'read_bytes', 'owned_file',
                    'read_layers', 'check_preimages'}, ns)
files = dict(original_input['project_files'])
files.update({PATCH: digest((B / PATCH).read_bytes()), MANIFEST: digest((B / MANIFEST).read_bytes())})
layers = ns['read_layers'](B, receipt, H, files, [LAYER])
assert ns['check_preimages'](layers, B / 'before', receipt['files']) == {TARGET: digest(after)}
passed('real_product_read_layers_and_check_preimages_on_actual_metadata')


def refused(name, action):
    try:
        action()
    except ns['Refused'] as error:
        passed(name, fixed_refusal=str(error))
    else:
        raise AssertionError(name + '_accepted')


wrong = copy.deepcopy(receipt['files'])
wrong[TARGET]['sha256'] = 'fb45b65f899a7c1561156b53fa167f309e48445b9ea00a14f8ed90d002b07dad'
refused('old208_preimage_refused', lambda: ns['check_preimages'](layers, B / 'before', wrong))
wrong = copy.deepcopy(receipt['files'])
wrong[TARGET]['sha256'] = digest(after)
refused('already_changed_or_third_image_not_adopted_as_preimage', lambda: ns['check_preimages'](layers, B / 'before', wrong))
wrong = copy.deepcopy(files)
wrong[MANIFEST] = '0' * 64
refused('manifest_project_pin_drift_refused', lambda: ns['read_layers'](B, receipt, H, wrong, [LAYER]))
wrong = copy.deepcopy(files)
wrong[PATCH] = '0' * 64
refused('patch_project_pin_drift_refused', lambda: ns['read_layers'](B, receipt, H, wrong, [LAYER]))
wrong = copy.deepcopy(receipt)
wrong['commit'] = '0' * 40
refused('wrong_donor_commit_refused', lambda: ns['read_layers'](B, wrong, H, files, [LAYER]))

stand = B / 'checks' / 'apply-stand'
assert not stand.exists()
(stand / 'hermes_cli').mkdir(parents=True, mode=0o700)
p = stand / TARGET
p.write_bytes(before)


def git_apply(*args):
    result = subprocess.run(['/usr/bin/git', '--no-optional-locks', 'apply', *args, str(B / PATCH)],
                            cwd=stand, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=10,
                            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_OPTIONAL_LOCKS': '0',
                                 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'})
    return result.returncode


assert git_apply('--check') == 0 and git_apply() == 0
assert p.read_bytes() == after
compile(after, str(p), 'exec')
passed('git_forward_apply_exact_candidate_and_compile')
assert git_apply('--reverse', '--check') == 0 and git_apply('--reverse') == 0
assert p.read_bytes() == before
passed('git_reverse_apply_exact209_beforeimage')
p.write_bytes(before.replace(b"'format': document_format, 'reason': exc.code})",
                             b"'format': 'drift', 'reason': exc.code})"))
assert p.read_bytes() != before and git_apply('--check') != 0
passed('touched_patch_context_drift_refused')
shutil.rmtree(stand)

old_tree = ast.parse(before)
new_tree = ast.parse(after)
def definitions(tree):
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
old_defs, new_defs = definitions(old_tree), definitions(new_tree)
assert old_defs.keys() == new_defs.keys()
assert [key for key in old_defs if old_defs[key] != new_defs[key]] == ['scoped_file']
passed('all_other_top_level_scope_definitions_unchanged', unchanged=len(old_defs) - 1)

# Replacing exactly the new catch with the old one makes the complete module
# AST identical: no control-flow, success, password or authority edits hide
# elsewhere in the large scoped_file body.
def target_handler(tree):
    matches = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and node.body and isinstance(node.body[0], ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == 'extraction_data' for t in node.body[0].targets):
                matches.append(node)
    assert len(matches) == 1 and len(matches[0].handlers) == 1
    return matches[0].handlers[0]
old_handler, new_handler = target_handler(old_tree), target_handler(new_tree)
assert ast.dump(old_handler.body[0], include_attributes=False) == ast.dump(new_handler.body[0], include_attributes=False)
assert isinstance(new_handler.body[2], ast.If)
assert ast.unparse(new_handler.body[2].test) == "document_format == 'docx' and exc.code == 'malformed_package'"
new_handler.body = old_handler.body
assert ast.dump(new_tree, include_attributes=False) == ast.dump(old_tree, include_attributes=False)
passed('only_exact_DOCX_malformed_error_catch_changed_existing_checkpoint_first')

builder_tree = ast.parse(BUILDER.read_bytes())
defaults = next(ast.literal_eval(n.value) for n in builder_tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'LAYER_NAMES' for t in n.targets))
assert len(defaults) == 4 and LAYER not in defaults
assert LAYER not in CONSUMER.read_text()
passed('default4_unchanged_new_layer_not_admitted_by_current_successor_builder')
assert pin(CONSUMER) == PINS['unchanged_publication_consumer']
assert pin(BUILDER) == PINS['unchanged_default_builder']
for rel, expected in PINS['source209_before'].items():
    assert pin(H / 'hermes-agent' / rel) == expected
assert digest((H / 'hermes-agent.source.json').read_bytes()) == digest(receipt_raw)
passed('selected_installed_sources_receipt_and_builder_unchanged_after_checks')

prefix = {'schema': 'frw.Sol.T39.real209-prefix-source-delta.v1',
          'state': 'SOURCE_ONLY_AFTER209_OPTIONAL_LAYER_NOT_ADMITTED_NOT_INSTALLED210',
          'input': pin(INPUT), 'receipt': pin(H / 'hermes-agent.source.json'),
          'ordered_installed209_layers': receipt['layers'],
          'optional_new_layer': {'name': LAYER, 'patch': pin(B / PATCH), 'manifest': pin(B / MANIFEST)},
          'candidate_native_modifications': 1, 'candidate_native_additions': 0,
          'hypothetical_project_pair_only_count': 501,
          'count_limit': '499+2 pair bytes only. No successor helper/CAS/current-input/builder admission supplied; no installed/project501 claim.'}
(B / 'PREFIX209-AND-SOURCE-DELTA.json').write_text(json.dumps(prefix, indent=2) + '\n')
signal.alarm(0)
usage = resource.getrusage(resource.RUSAGE_SELF)
out = {'schema': 'frw.Sol.T39.patch-consumer-checks.v1', 'state': 'PASS_SOURCE_SUBSET_ONLY',
       'checks': checks, 'passed': len(checks), 'failed': 0,
       'full_builder_or_install_or_runtime_pass': False,
       'limits': {'CPU_seconds': 60, 'AS_bytes': 512 * 1024**2, 'wall_seconds': 90,
                  'FSIZE_bytes': 16 * 1024**2, 'total_disk_budget_bytes': 100 * 1024**2},
       'resources': {'wall_seconds': time.monotonic() - START,
                     'CPU_seconds': usage.ru_utime + usage.ru_stime, 'maxrss_kib': usage.ru_maxrss},
       'cleanup': {'single_file_apply_stand_removed': not stand.exists()},
       'sources': {'consumer': pin(CONSUMER), 'builder': pin(BUILDER)},
       'scope': 'No module main/current observer/publisher/install/API invoked. Actual pinned receipt/input and actual product read_layers/check_preimages; source-only patch subset, not successor admission.'}
(B / 'checks' / 'PATCH-CONSUMER-CHECKS.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'passed': len(checks), 'wall_seconds': out['resources']['wall_seconds']}))
