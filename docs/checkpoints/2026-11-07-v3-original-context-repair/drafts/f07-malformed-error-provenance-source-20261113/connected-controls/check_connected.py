"""Task39 bounded SOURCE connected controls. No runtime/user acceptance credit.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -B check_connected.py
Synthetic authority is explicit; the selected descriptor/parser source is exact.
"""
from __future__ import annotations
import ast
from contextvars import ContextVar
import hashlib
import importlib
import io
import json
import logging
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import sys
import time
import types
import zipfile

os.umask(0o077)
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
B = OUT.parent
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
F = Path('/home/jericho/.cache/FRW-SOL-V3-F07-CURRENT-INGRESS-MISMATCH-CORE-20261112/fixtures')
START = time.monotonic()
START_UTC = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
DISK = 100 * 1024**2
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (DISK, DISK))
signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError('WALL_LIMIT_300S')))
signal.alarm(300)
AFFINITY = sorted(os.sched_getaffinity(0))[:2]
os.sched_setaffinity(0, AFFINITY)
logging.getLogger().addHandler(logging.NullHandler())

FIELDS = ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_uid', 'st_gid',
          'st_nlink', 'st_mtime_ns', 'st_ctime_ns')
def pin(path):
    path = Path(path)
    s = path.stat()
    return {'path': str(path), 'bytes': s.st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'stat': {key: getattr(s, key) for key in FIELDS}}

def disk_bytes():
    return sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())

def bounded_write(path, data):
    path = Path(path)
    assert path.is_relative_to(OUT)
    old = path.stat().st_size if path.exists() else 0
    assert disk_bytes() - old + len(data) <= DISK
    path.write_bytes(data)
    path.chmod(0o600)

def json_write(path, obj):
    bounded_write(path, (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode())

EXPECTED = {
    B/'before/hermes_cli/friday_user_scope.py': '3dff39b51c8da112339ad5e2f5065a332fe102877303bf442a57624f07404474',
    B/'candidate/hermes_cli/friday_user_scope.py': 'dc8ea5271f0937915fbf8cd0e39f74bd240e8f7d289d4a15e4f4062a7bf50d4a',
    H/'tools/file_tools.py': 'b834615c95438c2f1cb725247cc2ea0b6e1d5e1566cc3498fec2a069bc21a40f',
    H/'tools/read_extract.py': '8f3ad405263470eac948a9f14fa6c0af18144697cf5244c6c8c8a4f7d543b339',
    H/'tools/scoped_word_profiles.py': 'ef6767cdca7b761f6aa0da9ecfe81b44b66cc99b28af81de6f308b4180007e59',
    H/'tools/scoped_word_review.py': '050fafea426d2e5c5df584cbc1105549dfcaa55240552b80719db7f8bdeacb96',
    H/'tools/scoped_zip.py': 'fdb74316af13069b30acab144dd2d846a7643e7941acc157cfc6ba0b4ddfc127',
    H/'tools/scoped_ooxml_password.py': '59c65471582a30baf61ed8367925b477d00af70d6d1211e6044ecb2a3d35029c',
    H/'tools/binary_extensions.py': None,
    H/'hermes_cli/friday_workspace_revision.py': 'a84959c7ddc6fec3a028e5b67b4af64b7ee5d7f462776b9a59150a1891b10dc4',
    F/'truncated.docx': '03bc974e86c81845b6d4d47bdb90eec7b21f66d750aa3319bc327149859a5a75',
    F/'healthy.docx': '67d1aff2f27c8fbbb20303b0e2bcc1645ec4aa031cee2b26922726fd2acc6499',
}
sources_before = {str(p): pin(p) for p in EXPECTED}
for p, expected in EXPECTED.items():
    if expected is not None:
        assert sources_before[str(p)]['sha256'] == expected, str(p)
assert sources_before[str(F/'truncated.docx')]['bytes'] == 64
assert sources_before[str(F/'healthy.docx')]['bytes'] == 1233

DEPS = OUT/'deps'
TOOLS = DEPS/'tools'
TOOLS.mkdir(mode=0o700, parents=True, exist_ok=True)
dependency_copies = []
for name in ('read_extract.py', 'scoped_word_profiles.py', 'scoped_word_review.py',
             'scoped_zip.py', 'scoped_ooxml_password.py'):
    original = H/'tools'/name
    target = TOOLS/name
    bounded_write(target, original.read_bytes())
    assert pin(target)['sha256'] == sources_before[str(original)]['sha256']
    dependency_copies.append({'source': str(original), 'copy': pin(target)})

effects = {'subprocess_attempts': 0, 'network_attempts': 0, 'outside_write_attempts': 0}
def audit(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn', 'os.exec')):
        effects['network_attempts' if event.startswith('socket.') else 'subprocess_attempts'] += 1
        raise RuntimeError('UNDECLARED_EFFECT')
    if event == 'open':
        path, mode, flags = args
        write = ((isinstance(mode, str) and any(c in mode for c in 'wax+')) or
                 (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        if write and isinstance(path, (str, bytes)) and not Path(os.fsdecode(path)).is_relative_to(OUT):
            effects['outside_write_attempts'] += 1
            raise RuntimeError('OUTSIDE_WRITE')
sys.addaudithook(audit)

selected_rows = []
def selected(path, names, namespace):
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = []
    for node in tree.body:
        name = getattr(node, 'name', None)
        if isinstance(node, ast.Assign):
            name = getattr(node.targets[0], 'id', None)
        if name in names:
            nodes.append(node)
    assert len(nodes) == len(names), (path, names)
    selected_rows.append({'path': str(path), 'nodes': sorted(names),
        'ast_sha256': hashlib.sha256(ast.dump(ast.Module(body=nodes, type_ignores=[]), include_attributes=False).encode()).hexdigest()})
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)

def module(name, **values):
    mod = types.ModuleType(name)
    mod.__dict__.update(values)
    sys.modules[name] = mod
    return mod

module('tools', __path__=[str(TOOLS)])
module('agent', __path__=[])
module('hermes_cli', __path__=[])
context = ContextVar('task39_synthetic_call', default=None)
module('agent.web_call_context', _current=context)
module('agent.bounded_context', bounded_tool_result_budget=lambda: None,
       serialized_bytes=lambda value: len(value.encode()))
error_ns = {'json': json}
selected(B/'candidate/hermes_cli/friday_user_scope.py', {'ScopeDenied', 'ScopeArgumentError'}, error_ns)
ScopeDenied = error_ns['ScopeDenied']
ScopeArgumentError = error_ns['ScopeArgumentError']
module('hermes_cli.friday_credential_admission', ordinary_readonly_file=lambda *a: None,
       session_artifact_file=lambda *a: None, CredentialDenied=type('CredentialDenied', (Exception,), {}))
binary_ns = {}
selected(H/'tools/binary_extensions.py', {'UNSUPPORTED_CONTAINER_EXTENSIONS'}, binary_ns)
module('tools.binary_extensions', **binary_ns)
module('hermes_cli.friday_workspace_7z_parts', is_split_path=lambda p: False)
pdf_calls = []
def pdf_sentinel(*a, **kw):
    pdf_calls.append('prepare')
    raise AssertionError('PDF_PREPARATION_NOT_EXPECTED')
module('tools.scoped_pdf_password', prepare_read=pdf_sentinel,
       PDFReadError=type('PDFReadError', (Exception,), {}))

WORK = OUT/'synthetic_home'
assert not WORK.exists(), 'Previous synthetic fixture residue requires inspection'
WORK.mkdir(mode=0o700)
workspace = WORK/'workspace'
workspace.mkdir(mode=0o700)
class Capability:
    home = WORK
    directory_identity = (WORK.stat().st_dev, WORK.stat().st_ino)
    checks = 0
    fail_at = None
    def check(self):
        self.checks += 1
        if self.fail_at is not None and self.checks >= self.fail_at:
            raise ScopeDenied()
        return self
cap = Capability()
class Call:
    session_id = 'task39-synthetic-call'
    task_id = 'task39-connected'
    checks = 0
    fail_at = None
    def check(self):
        self.checks += 1
        if self.fail_at is not None and self.checks >= self.fail_at:
            raise ScopeDenied()
call = Call()
context.set(call)
revision_ns = {'os': os, 'stat': stat, 'hashlib': hashlib, 'ScopeDenied': ScopeDenied}
selected(H/'hermes_cli/friday_workspace_revision.py',
         {'snapshot', '_FIELDS', 'check', 'NonTextSnapshotError', 'note_read', '_key'}, revision_ns)
revision = module('hermes_cli.friday_workspace_revision', **revision_ns)
sys.modules['hermes_cli'].friday_workspace_revision = revision
counts = {'snapshot': 0, 'workspace_document': 0, 'note_read': 0, 'prepare': 0, 'parser': 0}
exact_snapshot = revision.snapshot
exact_note = revision.note_read
def snapshot_spy(*a, **kw):
    counts['snapshot'] += 1
    return exact_snapshot(*a, **kw)
def note_spy(*a, **kw):
    counts['note_read'] += 1
    return exact_note(*a, **kw)
revision.snapshot = snapshot_spy
revision.note_read = note_spy

scope_variants = {}
for version in ('before', 'candidate'):
    ns = {'__name__': 'task39_scoped_'+version, 'os': os, 'stat': stat, 'Path': Path,
          'json': json, 'hashlib': hashlib, 'ScopeDenied': ScopeDenied,
          'ScopeArgumentError': ScopeArgumentError, 'current': lambda required=False: cap,
          'guard_tool': lambda *a: None, 'ordinary_presentation': lambda: True}
    selected(B/version/'hermes_cli/friday_user_scope.py',
        {'scoped_file', 'workspace_document', '_workspace_directory', '_private', '_owner_uid',
         'ordinary_tool_error_json', 'PUBLIC_TOOL_REFUSAL_COPY'}, ns)
    exact_workspace = ns['workspace_document']
    def workspace_spy(*a, _exact=exact_workspace, **kw):
        counts['workspace_document'] += 1
        return _exact(*a, **kw)
    ns['workspace_document'] = workspace_spy
    scope_variants[version] = ns
tool_ns = {'json': json, 'DEFAULT_READ_LIMIT': 2000}
selected(H/'tools/file_tools.py', {'read_file_tool'}, tool_ns)
read_extract = importlib.import_module('tools.read_extract')
ooxml = importlib.import_module('tools.scoped_ooxml_password')
exact_extract = read_extract.extract_scoped_document_bytes
exact_prepare = ooxml.prepare_read
prepare_mode = 'exact'
parser_error = None
def prepare_spy(data, format, password=None, *, checkpoint=None):
    counts['prepare'] += 1
    if prepare_mode == 'error_wrong':
        raise ooxml.OOXMLPasswordError('ooxml_password_incorrect')
    if prepare_mode == 'error_malformed_code':
        raise ooxml.OOXMLPasswordError('malformed_package')
    if prepare_mode == 'malformed_bytes_success':
        if checkpoint is not None:
            checkpoint()
        return malformed, None
    return exact_prepare(data, format, password, checkpoint=checkpoint)
def extract_spy(data, format, *, checkpoint=None):
    counts['parser'] += 1
    if parser_error is not None:
        raise read_extract.ScopedExtractionError(parser_error)
    return exact_extract(data, format, checkpoint=checkpoint)
ooxml.prepare_read = prepare_spy
read_extract.extract_scoped_document_bytes = extract_spy
malformed = (F/'truncated.docx').read_bytes()
healthy = (F/'healthy.docx').read_bytes()
def private(name, payload):
    path = workspace/name
    bounded_write(path, payload)
    return path
def zip_bytes(parts, compression=zipfile.ZIP_STORED):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=compression) as archive:
        for name, value in parts.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 13, 0, 0, 0))
            info.compress_type = compression
            archive.writestr(info, value)
    return buf.getvalue()
def reset():
    cap.checks = call.checks = 0
    cap.fail_at = call.fail_at = None
    for key in counts:
        counts[key] = 0
    context.set(call)
    assert not hasattr(call, '_workspace_read')
def read(version, name, *, mode='exact', error=None, cap_fail_at=None, call_fail_at=None, **kw):
    global prepare_mode, parser_error
    reset()
    prepare_mode, parser_error = mode, error
    cap.fail_at, call.fail_at = cap_fail_at, call_fail_at
    ns = scope_variants[version]
    module('hermes_cli.friday_user_scope', scoped_file=ns['scoped_file'], ScopeDenied=ScopeDenied,
           ordinary_tool_error_json=ns['ordinary_tool_error_json'])
    raw = tool_ns['read_file_tool'](name, task_id=call.task_id, **kw)
    observed = json.loads(raw)
    return observed, {'counts': dict(counts), 'cap_checks': cap.checks, 'call_checks': call.checks,
                      'context_identity': id(context.get()), 'raw_sha256': hashlib.sha256(raw.encode()).hexdigest()}

checks = []
old4 = {'success': False, 'error': 'document_extraction_failed', 'format': 'docx', 'reason': 'malformed_package'}
fv = {'claimed_format': 'docx', 'actual_format': 'UNDETERMINED', 'filename_extension': '.docx',
      'format_selection': 'filename_extension', 'structure_validation': 'DOCX_PROFILE_NOT_VALIDATED',
      'notice': 'The filename extension selected the DOCX reader. The bounded native reader refused '
                'the malformed package; its actual format was not established. No document text was returned.'}
refusal = {'success': False, 'error': scope_variants['candidate']['PUBLIC_TOOL_REFUSAL_COPY']}
def no_failure_overclaims(observed):
    assert observed['success'] is False
    forbidden = {'content', 'text', 'source_sha256', 'source_unchanged', 'partial', 'next_offset',
                 'next_char_offset', 'encryption', 'signature_validation', 'repaired', 'repair'}
    def check(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value), value
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)
    check(observed)
    validation = observed.get('format_validation', {})
    assert not validation.get('actual_format') == 'docx'
    assert not validation.get('structure_validation') == 'SUPPORTED_DOCX_PROFILE_VALIDATED'

def paired(name, path, *, changed=False, expected=None, success=False, seam='none', **kwargs):
    before_file = pin(workspace/path)
    before_names = sorted(p.name for p in workspace.iterdir())
    baseline, bm = read('before', path, **kwargs)
    candidate, cm = read('candidate', path, **kwargs)
    if changed:
        assert baseline == old4, baseline
        assert candidate == {**old4, 'format_validation': fv}, candidate
        assert {k: v for k, v in candidate.items() if k != 'format_validation'} == baseline
    else:
        assert baseline == candidate, (name, baseline, candidate)
        assert bm['raw_sha256'] == cm['raw_sha256']
    if expected is not None:
        assert candidate == expected, (name, candidate)
    if success:
        assert candidate['success'] and candidate['format'] == 'docx'
        assert 'Healthy follow-up marker: 2718.' in candidate['content']
        assert bm['counts']['note_read'] == cm['counts']['note_read'] == 0
    else:
        no_failure_overclaims(candidate)
    assert pin(workspace/path) == before_file
    assert sorted(p.name for p in workspace.iterdir()) == before_names
    assert bm['context_identity'] == cm['context_identity'] == id(call)
    checks.append({'name': name, 'status': 'PASS', 'changed_branch': changed,
        'output_comparison': 'only additive format_validation' if changed else 'exact raw JSON equality',
        'baseline': baseline, 'candidate': candidate, 'baseline_observation': bm, 'candidate_observation': cm,
        'fixture_pin': before_file, 'declared_substitution': seam,
        'custody_unchanged': True, 'same_synthetic_call_context': True})
    return checks[-1]

error = None
try:
    # Exact historical bytes are copied only from the approved source fixtures.
    private('truncated.docx', malformed)
    private('truncated.DOCX', malformed)
    for name in ('healthy.docx', 'healthy.DOCX', 'healthy_no_extension', 'false_extension.pdf'):
        private(name, healthy)
    paired('exact_64B_03bc_malformed_docx', 'truncated.docx', changed=True)
    paired('uppercase_suffix_malformed_docx', 'truncated.DOCX', changed=True)
    paired('exact_1233B_67d1_healthy_after_failure', 'healthy.docx', success=True)
    paired('uppercase_suffix_healthy_docx', 'healthy.DOCX', success=True)
    for name in ('healthy_no_extension', 'false_extension.pdf'):
        row = paired('existing_valid_mismatch_'+name, name, success=True)
        validation = row['candidate']['extraction']['format_validation']
        assert validation['actual_format'] == 'docx'
        assert validation['structure_validation'] == 'SUPPORTED_DOCX_PROFILE_VALIDATED'
        assert validation['filename_mismatch'] is True
    for name, payload, reason in (
        ('non_docx_zip.docx', zip_bytes({'plain.txt': b'not an Office document'}), 'content_types_missing_or_namespace'),
        ('plain_named.docx', b'Plain UTF-8, not a document package\n', 'malformed_package'),
        ('random_named.docx', bytes(range(64)), 'malformed_package')):
        private(name, payload)
        paired('non_DOCX_cannot_establish_DOCX_'+name, name, changed=(reason == 'malformed_package'),
               expected=None if reason == 'malformed_package' else {**old4, 'reason': reason})
    # Real nearest parser errors different from malformed_package remain untouched.
    with zipfile.ZipFile(io.BytesIO(healthy)) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    parts['[Content_Types].xml'] = parts['[Content_Types].xml'].replace(
        b'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
        b'application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml')
    private('wrong_profile.docx', zip_bytes(parts))
    paired('actual_parser_profile_mismatch_undecorated', 'wrong_profile.docx',
           expected={**old4, 'reason': 'profile_content_type_mismatch'})
    private('expansion.docx', zip_bytes({'oversize.xml': b'x'*1000001}, zipfile.ZIP_DEFLATED))
    paired('actual_parser_expansion_refusal_undecorated', 'expansion.docx',
           expected={**old4, 'reason': 'package_expansion_limit'})
    # Malformed but non-DOCX selected format is outside the exact changed branch.
    private('truncated.dotx', malformed)
    paired('other_reader_malformed_not_relabelled', 'truncated.dotx',
           expected={**old4, 'format': 'dotx'})
    # Invalid password goes through actual prepare_read validation; no crypto invoked.
    row = paired('actual_password_invalid_retains_exact_code', 'healthy.docx', password=17,
                 expected={**old4, 'reason': 'ooxml_password_invalid'})
    assert row['candidate_observation']['counts']['prepare'] == 1
    assert row['candidate_observation']['counts']['parser'] == 0
    # Wrong-password/fixed-code exceptions are injected at the producer seam, with no encrypted file.
    for mode, reason in (('error_wrong', 'ooxml_password_incorrect'), ('error_malformed_code', 'malformed_package')):
        row = paired('password_producer_'+mode+'_no_retry', 'healthy.docx', mode=mode,
            expected={**old4, 'reason': reason},
            seam='prepare_read raises actual OOXMLPasswordError with fixed code; no actual password attempt/encrypted document')
        assert row['candidate_observation']['counts']['prepare'] == 1
        assert row['candidate_observation']['counts']['parser'] == 0
    row = paired('successful_prepare_malformed_bytes_actual_parser', 'healthy.docx', changed=True,
        mode='malformed_bytes_success', seam='prepare_read success is substituted with exact 64B malformed bytes + None metadata; actual read_extract/Word/ZIP parser runs; no decrypt/encrypted document')
    assert row['candidate_observation']['counts']['prepare'] == 1
    assert row['candidate_observation']['counts']['parser'] == 1
    # Error type is important: other extractor failures remain the legacy four fields.
    row = paired('other_extractor_code_not_relabelled', 'healthy.docx', error='no_extractable_text',
        expected={**old4, 'reason': 'no_extractable_text'},
        seam='extract_scoped_document_bytes raises actual ScopedExtractionError(no_extractable_text); explicit exception boundary probe')
    assert row['candidate_observation']['counts']['parser'] == 1
    # Cap failure occurs at the changed except checkpoint, after the actual parser refused.
    malform_count = checks[0]['candidate_observation']['cap_checks']
    row = paired('current_capability_refusal_before_new_metadata', 'truncated.docx',
                 cap_fail_at=malform_count, expected=refusal,
                 seam='synthetic Capability.check revokes on the final exception checkpoint after actual malformed parser')
    assert row['candidate_observation']['counts']['parser'] == 1
    # Exact revision.check tests a synthetic current Call cancellation on the same final checkpoint.
    malformed_call_checks = checks[0]['candidate_observation']['call_checks']
    row = paired('scoped_call_cancellation_before_new_metadata', 'truncated.docx',
                 call_fail_at=malformed_call_checks, expected=refusal,
                 seam='synthetic Call.check cancels on exact revision.check final exception checkpoint after actual malformed parser')
    assert row['candidate_observation']['counts']['parser'] == 1
    paired('healthy_after_all_failures_same_context', 'healthy.docx', success=True)
    assert not pdf_calls
    assert effects == {'subprocess_attempts': 0, 'network_attempts': 0, 'outside_write_attempts': 0}
    assert sources_before == {str(p): pin(p) for p in EXPECTED}
    for row in dependency_copies:
        assert row['copy'] == pin(row['copy']['path'])
except BaseException as exc:
    error = {'class': type(exc).__name__, 'detail': str(exc)}
finally:
    shutil.rmtree(WORK)
    signal.alarm(0)

resources = {'start_utc': START_UTC, 'finish_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'wall_s': time.monotonic()-START,
    'cpu_s': resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
    'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'pid': os.getpid(), 'affinity': AFFINITY,
    'consumer_limits': {'CPU_s': list(resource.getrlimit(resource.RLIMIT_CPU)),
        'AS_bytes': list(resource.getrlimit(resource.RLIMIT_AS)), 'single_file_bytes': list(resource.getrlimit(resource.RLIMIT_FSIZE)),
        'wall_alarm_s': 300, 'aggregate_disk_budget_bytes': DISK,
        'aggregate_disk_enforcement': 'every explicit fixture/dependency/evidence write prechecked by bounded_write; bytecode disabled'},
    'disk_bytes_after_fixture_cleanup': disk_bytes(), 'aggregate_cgroup_claim': False}
cleanup = {'synthetic_workspace_removed': not WORK.exists(), 'dependency_copies_retained_for_reproduction': True,
           'fixture_payloads_retained': False, 'pycache_paths': [str(p) for p in OUT.rglob('__pycache__')]}
json_write(OUT/'sourcepins.json', {'sources_before': sources_before, 'sources_after': {str(p): pin(p) for p in EXPECTED},
                                  'dependency_copies': dependency_copies, 'selected_ast': selected_rows})
json_write(OUT/'checks.json', checks)
json_write(OUT/'resources.json', resources)
json_write(OUT/'cleanup.json', cleanup)
result = {'schema': 'frw.Sol.Task39.connected-malformed-provenance.v1',
    'status': 'PASS' if error is None else 'FAIL', 'error': error,
    'source_only': True, 'runtime_pass': False, 'installed_runtime_qualified': False,
    'live_user_credit': False, 'formal_f07_credit': False,
    'candidate_sha256': EXPECTED[B/'candidate/hermes_cli/friday_user_scope.py'],
    'baseline_sha256': EXPECTED[B/'before/hermes_cli/friday_user_scope.py'],
    'checks_passed': len(checks), 'changed_branch_pairs': sum(r['changed_branch'] for r in checks),
    'unchanged_raw_json_pairs': sum(not r['changed_branch'] for r in checks),
    'same_synthetic_context': True, 'effect_counters': effects,
    'actual_qualified_path': 'exact read_file_tool AST -> exact full scoped_file AST -> exact workspace_document / revision snapshot/check AST -> selectively copied read_extract / Word profile/review / ZIP parser; exact unencrypted OOXML pass-through except declared seam probes',
    'synthetic_authority_and_substitutions': [
        'current() returns own synthetic Capability; guard_tool no-op; no real admission/user authority',
        'Capability home identity is own private synthetic fixture home; actual _workspace_directory/_private/_owner_uid checks run',
        'credential read routes return None; no credential admission execution',
        'actual ContextVar contains synthetic Call; exact revision.check checks synthetic cancellation',
        'synthetic tools/agent/hermes_cli module namespaces; parser modules load only private copied source',
        'bounded_tool_result_budget=None, actual UTF-8 serialized byte size; split archive predicate false',
        'PDF prepare sentinel must remain uncalled; no PDF native process',
        'spies count and forward exact snapshot/workspace_document/note_read/prepare/parser unless per-check seam explicitly declared',
        'explicit password exception/success and extractor exception seams are not encrypted-producer/decrypt qualification'],
    'not_qualified': ['installed runtime', 'Telegram/model/API', 'real admission/persistence', 'Office rendering',
                      'actual encryption or password attempt', 'other formats/full gate', 'historical effects'],
    'artifacts': {name: pin(OUT/name) for name in ('check_connected.py', 'sourcepins.json', 'checks.json', 'resources.json', 'cleanup.json')},
    'cleanup': cleanup}
json_write(OUT/'RESULT.json', result)
print(json.dumps({'status': result['status'], 'checks_passed': len(checks), 'error': error}))
if error is not None:
    raise SystemExit(1)
