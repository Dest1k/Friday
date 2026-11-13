"""Independent pure Task39 delta checks; no installed module execution or full-suite replay."""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import signal
import sys
import time
import types

os.umask(0o077)
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
B = OUT.parent
START = time.monotonic()
DISK = 100 * 1024**2
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (DISK, DISK))
signal.alarm(300)
effects = {'network_attempts': 0, 'subprocess_attempts': 0, 'outside_write_attempts': 0}
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn', 'os.exec')):
        key = 'network_attempts' if event.startswith('socket.') else 'subprocess_attempts'
        effects[key] += 1
        raise RuntimeError('UNDECLARED_EFFECT')
    if event == 'open':
        path, mode, flags = args
        write = ((isinstance(mode, str) and any(c in mode for c in 'wax+')) or
                 (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        if write and isinstance(path, (str, bytes)) and not Path(os.fsdecode(path)).is_relative_to(OUT):
            effects['outside_write_attempts'] += 1
            raise RuntimeError('OUTSIDE_WRITE')
sys.addaudithook(audit)

def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
expected = {
    'before/hermes_cli/friday_user_scope.py': '3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474',
    'candidate/hermes_cli/friday_user_scope.py': 'dc8ea5271f0937915fbf8cd0e39f74bd240e8f7d289d4a15e4f4062a7bf50d4a',
    'patches/hermes/f07-malformed-docx-error-provenance-after-source209.patch': '8d4ef6bc9506e790e1d203682e591495a6d9cb2d03830de6c71885380390bc88',
    'patches/hermes/f07-malformed-docx-error-provenance-after-source209-manifest.json': 'deb27efa37c5ea61e5df0f886c6cade19f78642ac07291be123372e29b8ceaa4',
    'ROOT-NEXT-RECIPE.json': '6f283caebd30d7f4dcfa299ba6ab0b808f9abd87aa22eb42fcdab8efa6005508',
    'SOURCE-PINS.json': '9489479798760aec1cb70d251b19fe81a9f417ebed0cce0a7db2c5d16156d2b2',
    'CHECKS.json': '67723934d6dc78ec4ed71523d9e17ecb497b8161459c615beb5cfb506daa53f3',
    'SOURCE-CAS.json': '3ac62c754e1db1769466cbf8c88fcf25fe211c05cab91075b4c065698dec1896',
    'checks/PATCH-CONSUMER-CHECKS.json': 'ce664e2d0ee316fa3475b4f28aebacd53d09f2de76a2d1829ef87e34e2d195d5',
    'connected-controls/RESULT.json': '8b046ce0ac9efa10dc1579f68945e7f2bdf77ede14c43489837ea40f1297ebf9',
    'connected-controls/check_connected.py': 'a1e030a9d2a0407d82af7781130e878dc8dd3c640cf8383532a7fc9d5d04868d',
    'connected-controls/checks.json': '0b7881cfe5e0721321571215cd4894cb65cae1016fe3c4fab907c2dc20d03e16',
    'connected-controls/sourcepins.json': '814798689396df86421727b9f4a0123dfc8df135add098ab19652b6228f4da0c',
    'connected-controls/resources.json': '4ec4d8c2e10a133da159915d42842cd20fbe0293330ef6ff13b85bb050e53ac7',
    'connected-controls/cleanup.json': 'f20107bc516476d2181f7a5dc7b1082e2217e2ab5ed5b44d1b16047e753b4b71',
    'producer-assessment/RESULT.json': '9cc214db33128b15944203b0ef8cb7d02d68e655348637263fae4773f4d51da0',
    'checks/VALIDATOR-ERRATA.json': '3f09ce784ddb0f4264a0e4c375bfd0ed71d91b0090ba784fa1d933b4cb395eed',
}
# Exact resource pin is authenticated by the connected result below; avoid manual transcription.
connected_result = json.loads((B/'connected-controls/RESULT.json').read_bytes())
expected['connected-controls/resources.json'] = connected_result['artifacts']['resources.json']['sha256']
inputs_before = {rel: pin(B/rel) for rel in expected}
for rel, sha in expected.items():
    assert inputs_before[rel]['sha256'] == sha, rel
for rel in ('checks/check_patch_consumer.py', 'PREFIX209-AND-SOURCE-DELTA.json'):
    inputs_before[rel] = pin(B/rel)

checks = []
def passed(name, **facts):
    checks.append({'name': name, 'status': 'PASS', **facts})
before = (B/'before/hermes_cli/friday_user_scope.py').read_bytes()
after = (B/'candidate/hermes_cli/friday_user_scope.py').read_bytes()
patch = (B/'patches/hermes/f07-malformed-docx-error-provenance-after-source209.patch').read_text().splitlines(keepends=True)
src = before.decode().splitlines(keepends=True)
result = []; cursor = 0; i = 3; hunks = 0
while i < len(patch):
    m = re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n', patch[i])
    assert m is not None
    start, old_count, new_start, new_count = map(int, m.groups())
    result.extend(src[cursor:start-1]); cursor = start-1; i += 1
    old_seen = new_seen = 0
    while i < len(patch) and not patch[i].startswith('@@ '):
        kind, text = patch[i][0], patch[i][1:]
        assert kind in ' +-'
        if kind in ' -':
            assert src[cursor] == text
            cursor += 1; old_seen += 1
        if kind in ' +':
            result.append(text); new_seen += 1
        i += 1
    assert (old_seen, new_seen) == (old_count, new_count)
    hunks += 1
result.extend(src[cursor:])
assert ''.join(result).encode() == after and hunks == 1
passed('one_hunk_in_memory_patch_yields_exact_final_candidate', hunks=hunks)

old_tree = ast.parse(before); new_tree = ast.parse(after)
def enclosing_try(tree):
    matches = [n for n in ast.walk(tree) if isinstance(n, ast.Try) and n.body
        and isinstance(n.body[0], ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'extraction_data' for t in n.body[0].targets)]
    assert len(matches) == 1 and len(matches[0].handlers) == 1
    return matches[0]
old_try, new_try = enclosing_try(old_tree), enclosing_try(new_tree)
restored = copy.deepcopy(new_tree)
enclosing_try(restored).handlers[0].body = copy.deepcopy(old_try.handlers[0].body)
assert ast.dump(old_tree, include_attributes=False) == ast.dump(restored, include_attributes=False)
assert ast.dump(old_try.handlers[0].body[0], include_attributes=False) == ast.dump(new_try.handlers[0].body[0], include_attributes=False)
passed('whole_module_AST_exact_after_restoring_only_final_catch_body', retained_checkpoint_first=True)

selection = [n for n in ast.walk(new_tree) if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'document_format' for t in n.targets)
    and isinstance(n.value, ast.IfExp)]
assert len(selection) == 1
def wrapper(tree):
    fn = ast.FunctionDef(name='run_selected_extraction',
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[copy.deepcopy(selection[0]), copy.deepcopy(enclosing_try(tree)),
              ast.Return(value=ast.Tuple(elts=[ast.Name(id='text', ctx=ast.Load()),
                  ast.Name(id='extraction_metadata', ctx=ast.Load()),
                  ast.Name(id='encryption_metadata', ctx=ast.Load())],ctx=ast.Load()))],
        decorator_list=[])
    return compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])), '<candidate-exact-selection-and-try>', 'exec')
old_code,new_code = wrapper(old_tree),wrapper(new_tree)
class ExtractionFailure(Exception):
    def __init__(self, code): self.code = code
class PasswordFailure(Exception):
    def __init__(self, code): self.code = code
class Cancel(Exception): pass
tools = types.ModuleType('tools'); tools.__path__ = []
ooxml = types.ModuleType('tools.scoped_ooxml_password')
ooxml.OOXMLPasswordError = PasswordFailure
sys.modules['tools'] = tools
sys.modules['tools.scoped_ooxml_password'] = ooxml
def run(code, filename, reason='malformed_package', seam='native_pass_through', cancel=False, success=False):
    calls = {'prepare':0, 'parser':0, 'document_check':0, 'revision_check':0}
    source = b'synthetic-original-input'; clear = b'synthetic-decrypted-malformed-input'
    metadata = {'encrypted':True, 'password_verified':True, 'decrypted_output_published':False}
    class Revision:
        def check(self, cap):
            calls['revision_check'] += 1
            if cancel: raise Cancel()
    def document_check(): calls['document_check'] += 1
    def prepare(data, fmt, password=None, checkpoint=None):
        calls['prepare'] += 1
        assert data is source and fmt == PurePosixPath(filename).suffix.lower().lstrip('.')
        if seam == 'password_exception_same_code': raise PasswordFailure('malformed_package')
        if seam == 'decrypt_success_nonempty_metadata': return clear, metadata
        assert seam == 'native_pass_through'
        return data, None
    class Text(str): extraction_metadata = {'native_container':True}
    text = Text('synthetic trusted success sentinel')
    def extract(data, fmt, checkpoint=None):
        calls['parser'] += 1
        assert data is (clear if seam == 'decrypt_success_nonempty_metadata' else source)
        assert fmt == PurePosixPath(filename).suffix.lower().lstrip('.')
        if success: return text
        raise ExtractionFailure(reason)
    ooxml.prepare_read = prepare
    ns = {'path':PurePosixPath(filename), 'data':source, 'args':{'password':'synthetic'},
        'OOXML_PASSWORD_FORMATS':{'docx','dotx','docm','dotm'}, 'revision':Revision(), 'cap':object(),
        'check_document':document_check, 'extract_scoped_document_bytes':extract,
        'ScopedExtractionError':ExtractionFailure, 'json':json, 'encryption_metadata':None}
    exec(code,ns)
    try:
        value = ns['run_selected_extraction']()
    except Cancel:
        return 'CANCEL',calls
    if isinstance(value,str): return json.loads(value),calls
    assert success and value[0] is text and value[1] is text.extraction_metadata
    assert value[2] is (metadata if seam == 'decrypt_success_nonempty_metadata' else None)
    return 'SUCCESS_SENTINELS_PRESERVED',calls
for filename,reason,seam,cancel,success,changed in (
    ('file.DOCX','malformed_package','native_pass_through',False,False,True),
    ('file.docx','malformed_package','decrypt_success_nonempty_metadata',False,False,True),
    ('file.dotx','malformed_package','native_pass_through',False,False,False),
    ('file.docx','profile_content_type_mismatch','native_pass_through',False,False,False),
    ('file.docx','malformed_package','password_exception_same_code',False,False,False),
    ('file.docx','malformed_package','decrypt_success_nonempty_metadata',True,False,False),
    ('file.docx',None,'decrypt_success_nonempty_metadata',False,True,False),
):
    old,oc = run(old_code,filename,reason,seam,cancel,success)
    new,nc = run(new_code,filename,reason,seam,cancel,success)
    assert oc == nc and oc['prepare'] == 1
    if changed:
        fv = new['format_validation']
        assert {k:v for k,v in new.items() if k!='format_validation'} == old
        assert old == {'success':False,'error':'document_extraction_failed','format':'docx','reason':'malformed_package'}
        assert fv['claimed_format']=='docx' and fv['actual_format']=='UNDETERMINED'
        assert fv['filename_extension']=='.docx' and fv['format_selection']=='filename_extension'
        assert fv['structure_validation']=='DOCX_PROFILE_NOT_VALIDATED'
        assert set(fv)=={'claimed_format','actual_format','filename_extension','format_selection','structure_validation','notice'}
        assert oc['parser']==1 and oc['revision_check']==1
    else:
        assert new==old
    if seam=='password_exception_same_code': assert oc['parser']==0
    if cancel: assert new=='CANCEL'
    passed('exact_AST_seam_'+seam+'_'+filename+'_'+str(reason)+'_'+str(cancel)+'_'+str(success),
        source_selection='exact candidate suffix assignment',changed=changed,counters=nc,
        substitution='parser and prepare boundary sentinels; no crypto/installed/parser execution')

manifest = json.loads((B/'patches/hermes/f07-malformed-docx-error-provenance-after-source209-manifest.json').read_bytes())
assert manifest['files']==[{'path':'hermes_cli/friday_user_scope.py','before_sha256':hashlib.sha256(before).hexdigest(),
    'sha256':hashlib.sha256(after).hexdigest(),'bytes':len(after),'mode':'100644','new_file':False}]
predecessor = Path('/home/jericho/.cache/FRW-SOL-V3-F07-NATIVE209-AFTER208-CORE-20261113/INPUT-SOURCE209.PROSPECTIVE.NOT_INSTALLED.json')
assert pin(predecessor)['sha256']=='2805a670402e6265f988501326bf0d8fe26d6209e061b095dd652ef94786367d'
input209=json.loads(predecessor.read_bytes())
assert len(input209['project_files'])==499 and len(manifest['prerequisites'])==209
assert all(input209['project_files'][k]==v for k,v in manifest['prerequisites'].items())
prefix=json.loads((B/'PREFIX209-AND-SOURCE-DELTA.json').read_bytes())
layers=prefix['ordered_installed209_layers']; assert len(layers)==209
assert {r['patch_sha256'] for r in layers}==set(manifest['prerequisites'].values())
passed('manifest_single_target_and_all209_real_saved_prefix_prerequisites',
    historical_input_pin=pin(predecessor),fresh_runtime_admission=False)

rows=json.loads((B/'connected-controls/checks.json').read_bytes())
assert len(rows)==20 and sum(r['changed_branch'] for r in rows)==5
for row in rows:
    assert row['status']=='PASS'
    if row['changed_branch']:
        assert {k:v for k,v in row['candidate'].items() if k!='format_validation'}==row['baseline']
    else: assert row['candidate']==row['baseline']
    assert row['baseline_observation']['counts']==row['candidate_observation']['counts']
passed('reviewed_saved20pair_evidence_consistent_and_seams_explicit',suite_replayed=False)

assert inputs_before=={rel:pin(B/rel) for rel in inputs_before}
assert effects=={'network_attempts':0,'subprocess_attempts':0,'outside_write_attempts':0}
signal.alarm(0)
usage=resource.getrusage(resource.RUSAGE_SELF)
out={'schema':'frw.Task39.independent-final-delta-probe.v1','status':'PASS',
    'checks':checks,'passed':len(checks),'inputs':inputs_before,'effect_counters':effects,
    'limits':{'CPU_seconds':list(resource.getrlimit(resource.RLIMIT_CPU)),
        'AS_bytes':list(resource.getrlimit(resource.RLIMIT_AS)),'wall_alarm_seconds':300,
        'FSIZE_bytes':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'total_disk_budget_bytes':DISK},
    'resources':{'wall_seconds':time.monotonic()-START,'CPU_seconds':usage.ru_utime+usage.ru_stime,
        'maxrss_kib':usage.ru_maxrss},
    'limits_of_credit':['pure candidate-AST seam checks; fake parser/prepare/authority',
        'no H module source executed or imported','no actual encryption/decryption',
        'no live or whole builder/install/runtime/semantic/formal qualification'],
    'cleanup':{'no_fixture_files_or_copies_created':True,'no_descendants_started':True,
        'pycache_paths':[str(p) for p in OUT.rglob('__pycache__')]}}
raw=(json.dumps(out,indent=2,ensure_ascii=False)+'\n').encode()
assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())+len(raw)<=DISK
p=OUT/'probe-evidence.json'; p.write_bytes(raw); p.chmod(0o600)
print(json.dumps({'status':'PASS','checks':len(checks),'evidence':pin(p)}))
