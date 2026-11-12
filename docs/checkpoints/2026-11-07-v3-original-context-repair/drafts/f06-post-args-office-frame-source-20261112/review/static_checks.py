"""Review-only stdlib AST/hash checks; never imports or executes candidate code."""
import ast
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat

PACKAGE = Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112')
CANDIDATE = PACKAGE / 'candidate'
T25 = Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112')
T27 = Path('/home/jericho/.cache/FRW-SOL-V3-F06-OBSERVED-ERRORCODE-ARGS-COMPAT-CORE-20261112')
REVIEW = PACKAGE / 'review'
EXPECTED_PINS_SHA = '89a003927b226f6d185af4954a34ead5c991bb74ccc88cccec6f6cbeed8d681f'
EXPECTED_CHANGED = ['conversion_probe.py', 'f06_contract.py', 'request_args_compat_v2.py', 'root_entry.py', 'root_frame.py']
LIBRARIES = ['callback_observer_v2.py', 'conversion_probe.py', 'diagnostic_client.py', 'readonly_diagnostic.py', 'request_args_compat_v2.py']
CHECKS = []

def check(name, value, evidence=None):
    CHECKS.append(dict(check=name, passed=bool(value), evidence=evidence))

def digest(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def functions(raw):
    tree = ast.parse(raw)
    return {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}

def constants(raw):
    tree = ast.parse(raw)
    return {target.id: ast.dump(node.value, include_attributes=False) for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}

pins = json.loads((CANDIDATE / 'SOURCE-PINS.json').read_bytes())
pin_ref = digest(CANDIDATE / 'SOURCE-PINS.json')
check('EXACT_REVIEW_KEY_SOURCE_PINS', pin_ref['sha256'] == EXPECTED_PINS_SHA, pin_ref)
check('NEW_SOURCE_SCHEMA_ASSIGNMENT_DORMANT', pins['schema'] == 'friday.f06.one-template-post-args-compat-source.v1' and pins['state'] == 'SOURCE_ONLY_DORMANT' and pins['assignment'] == 'ASTRA-NATIVE-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112#1' and pins['execution_authority'] is False)
check('SOURCE_SET_SORTED_EXACT', pins['source_set'] == sorted(set(pins['source_set'])) == [row['name'] for row in pins['files']])
rows = []
for row in pins['files']:
    path = CANDIDATE / row['name']
    actual = digest(path)
    metadata = path.lstat()
    actual['mode'] = format(stat.S_IMODE(metadata.st_mode), '04o')
    actual['uid'] = metadata.st_uid
    actual['nlink'] = metadata.st_nlink
    check('PIN_' + row['name'], actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'] and stat.S_ISREG(metadata.st_mode) and actual['mode'] == '0600' and actual['uid'] == os.getuid() and actual['nlink'] == 1, actual)
    rows.append(actual)
check('CANDIDATE_PRIVATE_DIRECTORY', stat.S_IMODE(CANDIDATE.stat().st_mode) == 0o700 and CANDIDATE.stat().st_uid == os.getuid() and not CANDIDATE.is_symlink())
check('SOURCE_ONLY_NO_OPERATIONS_OR_BOUND_PROOFS', {path.name for path in CANDIDATE.iterdir()} == set(pins['source_set']) | {'SOURCE-PINS.json'})
py_names = sorted(path.name for path in CANDIDATE.glob('*.py'))
check('EXACT_ELEVEN_PYTHON_FILES', len(py_names) == 11 and py_names == sorted(row['name'] for row in pins['files'] if row['name'].endswith('.py')))
freeze25_ref = digest(T25 / 'SOURCE-FREEZE-FINAL.json')
freeze27_ref = digest(T27 / 'SOURCE-FREEZE-FINAL.json')
check('EXACT_TASK25_FREEZE', freeze25_ref['sha256'] == 'dc7eaf4385616ec5d4a6bd6b13e97a5795e34ccfbdc254943a1621b694db14b1', freeze25_ref)
check('EXACT_TASK27_FREEZE', freeze27_ref['sha256'] == '305d16593f582bcce419f13efb9bd97c2524c2c4c893aaf4437bca5e0dbb3e28' == pins['task27_sourcefreeze_sha256'], freeze27_ref)
freeze25 = {row['path']:row for row in json.loads((T25 / 'SOURCE-FREEZE-FINAL.json').read_bytes())['files']}
freeze27 = {row['path']:row for row in json.loads((T27 / 'SOURCE-FREEZE-FINAL.json').read_bytes())['files']}
changed = []
patch = ''
function_deltas = {}
for name in py_names:
    before = (T25 / 'candidate' / name).read_bytes()
    after = (CANDIDATE / name).read_bytes()
    original = digest(T25 / 'candidate' / name)
    frozen = freeze25[str(T25 / 'candidate' / name)]
    check('TASK25_FROZEN_ORIGIN_' + name, all(original[key] == frozen[key] for key in ('bytes', 'sha256')))
    ast.parse(after, filename=name)
    if before != after:
        changed.append(name)
        patch += ''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True), fromfile='a/'+name, tofile='b/'+name))
    before_functions, after_functions = functions(before), functions(after)
    function_deltas[name] = sorted(key for key in before_functions.keys() | after_functions.keys() if before_functions.get(key) != after_functions.get(key))
check('ALL_ELEVEN_AST_PARSE_WITHOUT_EXECUTION', True)
check('EXACT_FIVE_CHANGED_SIX_CARRIED', changed == EXPECTED_CHANGED, dict(changed=changed, unchanged=[name for name in py_names if name not in changed]))
check('EXACT_REPORTED_PATCH', patch.encode() == (PACKAGE / 'POST-ARGS-COMPOSITION.patch').read_bytes(), digest(PACKAGE / 'POST-ARGS-COMPOSITION.patch'))
for name in LIBRARIES:
    path = T27 / 'revision2' / 'candidate' / name
    actual, copied, frozen = digest(path), digest(CANDIDATE / name), freeze27[str(path)]
    check('EXACT_ACCEPTED_TASK27_LIBRARY_' + name, all(actual[key] == copied[key] == frozen[key] for key in ('bytes', 'sha256')), copied)
check('CONTRACT_ONLY_EXPECTED_FUNCTIONS_CHANGED', function_deltas['f06_contract.py'] == ['diagnostic_acceptance', 'manifest_contract', 'operation', 'recipe_check'], function_deltas['f06_contract.py'])
check('ROOT_ENTRY_ONLY_EXPECTED_FUNCTIONS_CHANGED', function_deltas['root_entry.py'] == ['assemble', 'main'], function_deltas['root_entry.py'])
check('ROOT_FRAME_ONLY_ADMISSION_FRESH_STATE_CHANGED', function_deltas['root_frame.py'] == ['validate_fields'], function_deltas['root_frame.py'])
old_constants = constants((T25 / 'candidate' / 'f06_contract.py').read_bytes())
new_constants = constants((CANDIDATE / 'f06_contract.py').read_bytes())
check('ORIGINAL_LIMITS_EXACT_NO_EXTENSION', old_constants['LIMITS'] == new_constants['LIMITS'])
expected_changed_constants = ['ASSIGNMENT', 'LIBRARY_SHA256', 'OPERATION_KEY', 'POSTCHANGE_PURPOSE', 'PREVIOUS_CLASS1_SUMMARY_SHA', 'TASK25_FREEZE_SHA', 'TASK27_FREEZE_SHA']
changed_constants = sorted(key for key in old_constants.keys() | new_constants.keys() if old_constants.get(key) != new_constants.get(key))
check('ONLY_EXPECTED_CONTRACT_CONSTANTS_CHANGED', changed_constants == expected_changed_constants, changed_constants)
mapping = json.loads((PACKAGE / 'COMPOSITION-MAP.json').read_bytes())
check('COMPOSITION_MAP_RECOMPUTED', mapping['source_py_count'] == 11 and mapping['changed_from_task25'] == 5 and sorted(row['name'] for row in mapping['files']) == py_names and all(row['after']['sha256'] == digest(CANDIDATE / row['name'])['sha256'] and row['changed_from_task25'] == (row['name'] in changed) for row in mapping['files']))
references = json.loads((CANDIDATE / 'REFERENCES.json').read_bytes())
for row in references['files']:
    actual = digest(Path(row['path']))
    info = Path(row['path']).lstat()
    check('READONLY_REFERENCE_' + Path(row['path']).name, all(actual[key] == row[key] for key in ('bytes', 'sha256')) and stat.S_IMODE(info.st_mode) == 0o600 and stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1, actual)
safe_summary = references['files'][-1]
check('SAFE_CLASS1_SUMMARY_EXACT_METADATA_COPY', safe_summary['path'] == str(PACKAGE / 'reference-metadata' / 'F06-ONE-TEMPLATE-MISSING-CLASS-OBSERVED-PARTIAL-CLOSED-20261112.json') and safe_summary['sha256'] == '176f65237a6416f0950bd18a5f366a5e3cc1262842058f18e5b2cbc7b3614f9b' and safe_summary['bytes'] == 7362)
binding = json.loads((CANDIDATE / 'ROOT-BINDINGS.TEMPLATE.json').read_bytes())
proofs = json.loads((CANDIDATE / 'ROOT-PROOFS.TEMPLATE.json').read_bytes())
check('TEMPLATES_INERT_ALL_AUTHORITIES_UNBOUND', binding['state'] == 'UNBOUND_NOT_ADMITTED' and all(binding[name] is None for name in ('operation_key','source_pins_sha256','runtime_authority','source_review','fresh_boundary','output_manifest','credential_source')) and proofs['state'] == 'ALL_UNBOUND_NO_AUTHORITY' and proofs['source_review']['execution_authority'] is False and all(proofs[name]['state'].startswith('UNBOUND_') for name in ('source_review','runtime_authority','fresh_boundary','selected_manifest')))
check('REVIEW_FINAL_SOURCE_PINS_UNCHANGED', digest(CANDIDATE / 'SOURCE-PINS.json') == pin_ref)
result = dict(schema='friday.post-args.independent-static-review-evidence.v1', state='PASS_SOURCE_ONLY' if all(row['passed'] for row in CHECKS) else 'FAIL', at_moscow=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(), source_pins=pin_ref, checks=CHECKS, pass_count=sum(row['passed'] for row in CHECKS), total_count=len(CHECKS), source_files=rows, function_deltas=function_deltas, candidate_code_executed=False, candidate_modules_imported=False, actual_operations_read=False, credential_or_document_body_reads=False, live_effects=False)
destination = REVIEW / 'STATIC-EVIDENCE.json'
raw = (json.dumps(result, indent=2) + '\n').encode()
fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'wb') as stream:
    stream.write(raw)
print(json.dumps(dict(state=result['state'], pass_count=result['pass_count'], total_count=result['total_count'], failed=[row['check'] for row in CHECKS if not row['passed']], result=digest(destination))))
