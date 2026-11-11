#!/usr/bin/env python3
"""Finite F06 native consumer qualification; default is no encrypted execution."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import time
import zipfile

BASE = Path(__file__).resolve().parent
PARENT = BASE.parent.parent
SOURCE = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
PYTHON = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/installs/45eb40fd2d5351a9/environments/8e0c92ce48434ddbb9125ee001560ccb/venv/bin/python')
ASSIGNMENT = 'ASTRA-SOL-V3-F06-PROTECTED-OFFICE-CORE-20261111#1'
WALL, CPU, MEMORY = 300, 180, 2 * 1024**3
PARENT_CAP, OWN_CAP = 192 * 1024**2, 64 * 1024**2
HEX = re.compile('[0-9a-f]{64}')
DENIED = []
AUDIT_PHASE = {'fixture': 'none', 'phase': 'worker_setup'}


class Refused(Exception):
    """Only a fixed public code, never caller text or exception strings."""


def require(value, code):
    if not value:
        raise Refused(code)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def private(path, directory=False):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'noncanonical_path')
    s = path.lstat()
    require(s.st_uid == os.getuid() and stat.S_IMODE(s.st_mode) == (0o700 if directory else 0o600), 'private_custody')
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'private_type')
    return s


def size_tree(root):
    return sum(p.lstat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def budget():
    require(size_tree(PARENT) < PARENT_CAP and size_tree(BASE) < OWN_CAP, 'disk_cap')


def dump(path, obj, exclusive=False):
    budget()
    payload = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()
    require(len(payload) < 4 * 1024**2, 'report_limit')
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def ref_read(ref, max_bytes=2 * 1024**2):
    require(isinstance(ref, dict) and {'path', 'sha256', 'bytes'} <= set(ref), 'unbound_reference')
    require(isinstance(ref['sha256'], str) and HEX.fullmatch(ref['sha256']) and type(ref['bytes']) is int, 'invalid_reference')
    p = Path(ref['path'])
    before = private(p)
    require(0 <= before.st_size == ref['bytes'] <= max_bytes, 'reference_size')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(stream.fileno())
        raw = stream.read(max_bytes + 1)
        after = os.fstat(stream.fileno())
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode, s.st_nlink, s.st_uid)
    require(fields(before) == fields(held) == fields(after) == fields(p.lstat()), 'reference_cas')
    require(sha(raw) == ref['sha256'], 'reference_hash')
    for key, actual in [('uid', held.st_uid), ('mode', '0600'), ('dev', held.st_dev), ('ino', held.st_ino)]:
        if key in ref:
            require(ref[key] == actual, 'reference_identity')
    return raw


def pins_check():
    pinpath = BASE / 'SOURCE-PINS.json'
    pins = json.loads(pinpath.read_bytes())
    require(pins['source'] == str(SOURCE) and pins['actual'] == 'H203/project487/native17891/plugins52/base17730', 'source_origin')
    require(pins['receipt'] == '9d8d1d954a59d5f944cb0b33c11cba3bba845cbb5d71088f335d68077c2a83c2', 'source_receipt')
    for row in pins['files']:
        relative = Path(row['relative'])
        require(not relative.is_absolute() and '..' not in relative.parts
                and relative.suffix == '.py', 'source_pin_name')
        p = SOURCE / row['relative']
        require(p.resolve() == p and sha(p.read_bytes()) == row['sha256'], 'source_pin_drift')
    for row in pins.get('resources', []):
        relative = Path(row['relative'])
        require(not relative.is_absolute() and '..' not in relative.parts
                and (relative in (Path('hermes_cli/friday_plain_docx_template.b64'), Path('install-stamp.json'))
                     or len(relative.parts) == 4 and relative.parts[:2] == ('plugins', 'platforms')
                     and relative.name in ('plugin.yaml', 'plugin.yml')), 'resource_pin_name')
        p = SOURCE / relative
        require(p.resolve() == p and sha(p.read_bytes()) == row['sha256'], 'resource_pin_drift')
    require(sha(PYTHON.resolve().read_bytes()) == pins['python_executable_sha256'], 'python_pin_drift')
    return pins


def source_read_allowed(path, pins):
    """Exact pinned code/resources only; never SOURCE/.env/auth/config/state."""
    p = Path(path)
    try:
        relative = p.relative_to(SOURCE).as_posix()
    except ValueError:
        return False
    allowed = {r['relative'] for r in pins['files']} | {r['relative'] for r in pins.get('resources', [])}
    return relative in allowed and p.resolve() == p


def same_fixture_identity(bound, actual):
    profile = 'compatible1.3_or_Agile' if bound['profile'] == 'compatible' else 'current_default_latest_odt_negative'
    return (actual.get('format') == bound['format'] and actual.get('fixture_profile') == profile
            and all(actual.get(k) == bound['input'][k] for k in ('path', 'sha256', 'bytes')))


def binding_intent(m):
    # No grant ref/hash inside the manifest: the separate Root grant commits it.
    names = ('assignment', 'operation_id', 'root_generation_operation_id',
             'harness_sha256', 'native_source_pins_sha256', 'limits', 'effect_scope',
             'root_generation_result', 'independent_input_oracle', 'credential',
             'credential_keys', 'fixtures')
    return {name: m[name] for name in names}


def validate_root_evidence(m, grant, generation, oracle, manifest_sha256):
    require(grant.get('schema') == 'friday.f06.root-native-grant.v2'
            and grant.get('assignment') == ASSIGNMENT
            and grant.get('native_qualification_authorized') is True, 'root_grant_contract')
    require(grant.get('manifest_sha256') == manifest_sha256, 'root_grant_manifest')
    require(grant.get('intent') == binding_intent(m), 'root_grant_intent')
    rows = m['fixtures']
    require(generation.get('mode') == 'produce' and generation.get('planned_rows') == 7, 'generation_not_exact_produce')
    generated = generation.get('fixtures') if 'fixtures' in generation else generation.get('rows')
    require(isinstance(generated, list) and len(generated) == 7
            and all(same_fixture_identity(b, a) for b, a in zip(rows, generated)), 'generation_exact_bytes')
    if 'fixtures' in generation:
        require(generation.get('known_prefix_count') == 7, 'generation_prefix_incomplete')
    else:
        require(generation.get('whole_seven_covered') is True, 'generation_rows_incomplete')
    require(oracle.get('mode') in ('produce', 'verify-inputs')
            and oracle.get('oracle') == 'independent existing LibreOffice through dedicated UNO pipe'
            and oracle.get('planned_rows') == 7 and oracle.get('whole_seven_covered') is True
            and oracle.get('all_pass') is True, 'oracle_incomplete_or_unaccepted')
    proofs = oracle.get('rows')
    require(isinstance(proofs, list) and len(proofs) == 7, 'oracle_exact7')
    for bound, actual in zip(rows, proofs):
        require(same_fixture_identity(bound, actual)
                and actual.get('independent_office_password_and_semantics_pass') is True
                and actual.get('same_input_bytes_preserved') is True, 'oracle_exact_bytes')
        probes = actual.get('tests', {})
        require(probes.get('missing', {}).get('expected_password_refusal') is True
                and probes.get('wrong', {}).get('expected_password_refusal') is True
                and probes.get('correct', {}).get('opened') is True
                and probes.get('correct', {}).get('semantic_match') is True
                and probes.get('correct', {}).get('interaction_events') == [], 'oracle_password_semantics')


def binding_check(path, digest, grant_path, grant_digest):
    # Validate all grants, references and exact7 metadata BEFORE opening credentials.
    raw = ref_read({'path': str(path), 'sha256': digest, 'bytes': Path(path).stat().st_size})
    m = json.loads(raw)
    require(m.get('schema') == 'friday.f06.native-binding.v2' and m.get('assignment') == ASSIGNMENT, 'binding_identity')
    require('root_grant' not in m, 'circular_grant_ref_forbidden')
    require(m.get('root_authorized_native_run') is True, 'root_grant_absent')
    require(m.get('native_source_pins_sha256') == sha((BASE / 'SOURCE-PINS.json').read_bytes()), 'binding_source')
    require(m.get('harness_sha256') == sha(Path(__file__).read_bytes()), 'binding_harness')
    require(m.get('limits') == {'wall_seconds': WALL, 'cpu_seconds': CPU, 'address_space_bytes': MEMORY, 'parent_disk_bytes': PARENT_CAP, 'harness_disk_bytes': OWN_CAP}, 'binding_limits')
    require(m.get('credential_keys') == {'correct': 'password', 'wrong': 'wrong_password'}, 'credential_keys')
    require(m.get('effect_scope') == {'state': 'own_synthetic_only', 'network': False,
            'Office': False, 'model': False, 'input_writes': False,
            'output': 'retained_encrypted_derivatives_only'}, 'binding_effect_scope')
    for key in ('operation_id', 'root_generation_operation_id'):
        require(type(m.get(key)) is str and re.fullmatch('[A-Za-z0-9_.#:-]{1,128}', m[key]), 'operation_identity')
    rows = m.get('fixtures')
    require(isinstance(rows, list) and len(rows) == 7, 'exact7_required')
    require([(r.get('format'), r.get('profile')) for r in rows] == [(f, 'compatible') for f in ('docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp')] + [('odt', 'current_latest')], 'fixture_order_profiles')
    for n, row in enumerate(rows):
        require(row.get('id') == 'f06-' + str(n + 1), 'fixture_id')
        require(type(row.get('edit')) is dict and type(row.get('expected_before')) is list and type(row.get('expected_after')) is list, 'semantic_binding')
        require(row['expected_before'] and row['expected_after'] and all(type(s) is str and s for s in row['expected_before'] + row['expected_after']), 'semantic_tokens')
        require(row.get('changed_member_allowlist') and type(row['changed_member_allowlist']) is list, 'member_binding')
        require(Path(row['input']['path']).suffix.lower() == '.' + row['format'], 'input_suffix')
        ref_read(row['input'], 1000000)
    generation = json.loads(ref_read(m['root_generation_result']))
    oracle = json.loads(ref_read(m['independent_input_oracle']))
    grant = json.loads(ref_read({'path': str(grant_path), 'sha256': grant_digest,
                                'bytes': Path(grant_path).stat().st_size}))
    validate_root_evidence(m, grant, generation, oracle, digest)
    # Credential metadata/custody is validated now; bytes remain unopened until worker run.
    private(Path(m['credential']['path']))
    require(HEX.fullmatch(m['credential']['sha256']) is not None and 0 < m['credential']['bytes'] < 16384, 'credential_binding')
    return m


def install_boundary(work, manifest=None):
    os.umask(0o077)
    sys.dont_write_bytecode = True
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY, MEMORY))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    # No model/API secrets or ambient gateway authority survive in the worker.
    os.environ.clear()
    for name in ('os-home', 'cache', 'config', 'tmp', 'data'):
        (work / name).mkdir(mode=0o700)
    os.environ.update(PATH='/usr/bin:/bin', HOME=str(work / 'os-home'), HERMES_HOME=str(work / 'authority'), PYTHONDONTWRITEBYTECODE='1', GATEWAY_ALLOWED_USERS='901,902', XDG_CACHE_HOME=str(work / 'cache'), XDG_CONFIG_HOME=str(work / 'config'), XDG_DATA_HOME=str(work / 'data'), TMPDIR=str(work / 'tmp'))
    os.chdir(work)
    allowed = [BASE, Path(sys.prefix), Path(sys.base_prefix), Path('/usr/lib'), Path('/usr/local/lib'), Path('/usr/share/zoneinfo'), Path('/home/jericho/jericho/.venv')]
    code_pins = json.loads((BASE / 'SOURCE-PINS.json').read_bytes())
    # -B alone still permits old source bytecode reads. This empty owned prefix
    # makes native imports use reviewed .py source instead of SOURCE/__pycache__.
    sys.pycache_prefix = str(work / 'cache' / 'python')
    external = set()
    if manifest:
        external = {str(Path(manifest['credential']['path']))} | {r['input']['path'] for r in manifest['fixtures']}
    exact = {'/dev/null', '/dev/urandom', '/etc/localtime', '/etc/mime.types', '/etc/ssl/openssl.cnf', '/proc/1/cgroup', '/proc/self/cgroup', '/proc/self/mountinfo'} | external
    def absolute(raw, d=None):
        if isinstance(raw, int):
            return None
        p = Path(os.fsdecode(raw))
        if not p.is_absolute():
            p = (Path(os.readlink('/proc/self/fd/' + str(d))) if isinstance(d, int) and d >= 0 else Path.cwd()) / p
        return Path(os.path.abspath(p))
    def inside(p, roots):
        return any(p == r or p.is_relative_to(r) for r in roots)
    def deny(event, path=None, *, rule, flags=None):
        # Diagnostic metadata only: no raw path/args/locals/content/exception text.
        # Collection failure must never turn a denial into permission.
        row = {'event': event, 'boundary_rule': rule, **AUDIT_PHASE}
        try:
            if type(flags) is int:
                row['open_flags'] = flags
            if path is not None:
                if inside(path, [work]):
                    category = 'owned_work'
                elif inside(path, [SOURCE]):
                    category = 'native_source'
                elif str(path) in exact:
                    category = 'exact_external'
                elif inside(path, allowed):
                    category = 'dependency_root'
                else:
                    category = 'outside_bound_roots'
                row.update(path_class=category,
                           path_sha256=sha(os.fsencode(path)))
            locations = []
            frame = sys._getframe(1)
            # Retain source locations only; never inspect frame locals/values.
            for _ in range(12):
                if frame is None:
                    break
                filename = Path(frame.f_code.co_filename)
                if filename == Path(__file__):
                    locations.append({'kind': 'harness', 'line': frame.f_lineno})
                elif filename.is_relative_to(SOURCE):
                    relative = filename.relative_to(SOURCE).as_posix()
                    if relative in {r['relative'] for r in code_pins['files']}:
                        locations.append({'kind': 'pinned_native_source',
                                          'relative': relative, 'line': frame.f_lineno})
                frame = frame.f_back
            row['source_locations'] = locations
        except Exception:
            row['metadata_status'] = 'incomplete_fixed_no_exception_message'
        DENIED.append(row)
        raise Refused('python_audit_boundary')
    def audit(event, args):
        if event == 'open':
            p = absolute(args[0]); flags = args[2]
            if p is None:
                return
            writing = isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            if writing and not inside(p, [work]):
                deny(event, p, rule='open_write_outside_work', flags=flags)
            if not writing and inside(p, [SOURCE]):
                if not (isinstance(flags, int) and flags & os.O_DIRECTORY) and not source_read_allowed(p, code_pins):
                    deny(event, p, rule='source_read_not_pinned', flags=flags)
                return
            if not writing and not inside(p, allowed) and str(p) not in exact:
                # Native code opens known ancestor directories to pin descriptors.
                if not (isinstance(flags, int) and flags & os.O_DIRECTORY):
                    deny(event, p, rule='open_read_outside_exact_roots', flags=flags)
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.chown', 'os.utime', 'os.truncate'):
            d = args[2] if event == 'os.mkdir' and len(args) > 2 else args[-1] if event in ('os.remove', 'os.rmdir', 'os.chmod') else None
            p = absolute(args[0], d)
            if p is not None and not inside(p, [work]):
                deny(event, p, rule='mutation_outside_work')
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            for k in (0, 1):
                p = absolute(args[k], args[k + 2] if len(args) > k + 2 else None)
                if p is not None and not inside(p, [work]):
                    deny(event, p, rule='filesystem_pair_outside_work')
        elif event == 'sqlite3.connect':
            raw = os.fsdecode(args[0])
            raw = raw[5:].split('?', 1)[0] if raw.startswith('file:') else raw
            if raw != ':memory:' and not inside(absolute(raw), [work]):
                deny(event, absolute(raw), rule='sqlite_outside_work')
        elif event in ('socket.connect', 'socket.bind', 'socket.sendto', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.exec'):
            deny(event, rule='external_effect_refused')
        elif event in ('os.listdir', 'os.scandir'):
            p = absolute(args[0])
            if p is not None and not inside(p, allowed + [SOURCE, PARENT]):
                deny(event, p, rule='enumeration_outside_roots')
    sys.addaudithook(audit)
    sys.path.insert(0, str(SOURCE))


class Native:
    def __init__(self, work):
        from hermes_cli import friday_user_scope as scope
        from hermes_cli.plugins_state import PluginState
        from hermes_cli.friday_product_access import KEY, principal_id
        from gateway.authz_mixin import GatewayAuthorizationMixin
        from gateway.config import Platform
        from gateway.session import SessionSource
        from gateway.session_identity import RoutingIdentity
        from tools.file_tools import read_file_tool, write_file_tool
        self.scope, self.read, self.write = scope, read_file_tool, write_file_tool
        self.root, self.KEY, self.PluginState = work / 'authority', KEY, PluginState
        self.root.mkdir(mode=0o700)
        self.bindings = [dict(platform='telegram', transport_profile='default', account_id='F06-SYNTHETIC-BOT', user_id=u, runtime_profile='f06-' + tag, tools=['read_file', 'write_file'] if tag == 'a' else ['read_file']) for u, tag in [('901', 'a'), ('902', 'b')]]
        settings = {'product_access': {'enabled': True, 'accounts': [dict(platform='telegram', transport_profile='default', account_id='F06-SYNTHETIC-BOT', runtime_profiles=['f06-a', 'f06-b'])]}, 'user_isolation': {'enabled': True, 'bindings': self.bindings}}
        dump(self.root / 'config.yaml', {'plugins': {'enabled': ['friday_rework'], 'entries': {'friday_rework': {'settings': settings}}}})
        with scope.authority(self.root):
            self.state = PluginState('friday_rework')
            rows = {principal_id(*(b[k] for k in ('platform', 'transport_profile', 'account_id', 'user_id'))): {k: b[k] for k in ('platform', 'transport_profile', 'account_id', 'user_id')} | {'enabled': True, 'role': 'user'} for b in self.bindings}
            self.state.set(KEY, {'schema': KEY, 'users': rows})
            self.homes = [scope.provision_new_home(self.root, b, {'max_iterations': 8}) for b in self.bindings]
        self.gateway, self.Platform, self.SessionSource, self.RoutingIdentity = GatewayAuthorizationMixin(), Platform, SessionSource, RoutingIdentity
        self.sources = [self.admit(i) for i in range(2)]

    def admit(self, i):
        b = self.bindings[i]
        src = self.SessionSource(self.Platform.TELEGRAM, 'F06-SYNTHETIC-CHAT', user_id=b['user_id'], chat_type='group', thread_id='F06-SYNTHETIC-TOPIC', profile=b['runtime_profile'])
        src._identity = self.RoutingIdentity('default', b['runtime_profile'], self.root, self.homes[i], multiplexed=True, transport_inferred=False)
        with self.scope.authority(self.root):
            require(self.gateway._principal_authorized(src, allow_adapter_delegation=True) is True, 'native_admission')
        return src

    @contextmanager
    def enter(self, i=0):
        with self.scope.authority(self.homes[i]), self.scope.scoped_source(self.sources[i]) as cap:
            yield cap

    def enabled(self, enabled):
        from hermes_cli.friday_product_access import current_access
        with self.scope.authority(self.root):
            access = current_access()
            access['users'][self.sources[0]._friday_user_scope.key]['enabled'] = enabled
            self.state.set(self.KEY, access)


def observe(fn):
    try:
        raw = fn()
        value = json.loads(raw)
        return value
    except Exception as error:
        return {'success': False, 'exception_class': type(error).__name__}


def no_content(value):
    # Structural helper for the preserved R1 synthetic preparation seam only.
    # Qualification acceptance uses the phase-specific classifiers below.
    return value.get('success') is False and not value.get('content') and value.get('exception_class') in (None, 'ScopeDenied')


PASSWORD_CODES = {
    'ooxml': {'missing': 'ooxml_password_required', 'wrong': 'ooxml_password_incorrect'},
    'odf': {'missing': 'odf_password_required', 'wrong': 'odf_password_rejected_or_corrupt'},
}
MODERN_ODF_UNSUPPORTED = frozenset({
    'odf_encryption_algorithm_unsupported', 'odf_key_derivation_unsupported',
    'odf_start_key_unsupported', 'odf_checksum_unsupported',
    'odf_encryption_structure_unsupported', 'odf_root_encryption_unsupported',
    'odf_partial_encryption_unsupported', 'odf_directory_encryption_unsupported',
})


def returned_refusal(value):
    return (isinstance(value, dict) and value.get('success') is False
            and not value.get('content') and 'exception_class' not in value)


def password_refusal(value, fmt, kind, edit=False):
    family = 'ooxml' if fmt in ('docx', 'xlsx', 'pptx') else 'odf'
    return (returned_refusal(value) and value.get('reason') == PASSWORD_CODES[family][kind]
            and value.get('error') == ('protected_document_edit_refused' if edit else 'document_extraction_failed')
            and (value.get('effect_disposition') == 'none' if edit else value.get('format') == fmt))


def scope_refusal(value):
    # Called on real scoped_file directly, before the ordinary privacy projection.
    return value == {'success': False, 'exception_class': 'ScopeDenied'}


def hash_refusal(value):
    return (returned_refusal(value) and value.get('error') == 'protected_document_edit_refused'
            and value.get('reason') == 'source_hash_mismatch' and value.get('effect_disposition') == 'none')


def collision_refusal(value, fmt):
    if fmt in ('docx', 'xlsx', 'pptx'):
        return (returned_refusal(value) and value.get('error') == 'protected_document_edit_refused'
                and value.get('reason') == 'document_already_exists' and value.get('effect_disposition') == 'none')
    return returned_refusal(value) and value.get('error') == 'document_already_exists' and 'reason' not in value


def cas_refusal(value, mutation_applied, native_source_verifier_denied):
    return (returned_refusal(value) and value.get('error') == 'document_not_created'
            and value.get('effect_disposition') == 'none' and mutation_applied
            and native_source_verifier_denied)


def modern_unsupported(value, fmt, profile):
    return (fmt == 'odt' and profile == 'current_latest' and returned_refusal(value)
            and value.get('format') == 'odt' and value.get('error') == 'document_extraction_failed'
            and value.get('reason') in MODERN_ODF_UNSUPPORTED)


def safe_receipt(value, sensitive=()):
    # No raw tool result, document text, content JSON, password or exception message.
    keys = ('success', 'error', 'reason', 'exception_class', 'sha256', 'source_sha256', 'encrypted', 'same_password', 'password_preserved', 'plaintext_published', 'decrypted_output_published', 'effect_disposition', 'create_only', 'verified')
    return {k: value[k] for k in keys if k in value and (not isinstance(value[k], str) or re.fullmatch('[A-Za-z0-9_.:-]{1,160}', value[k]) and not any(secret in value[k] for secret in sensitive))}


def prepare(native):
    from hermes_cli.friday_prompt_scope import ordinary_file_schema
    from tools.file_tools import READ_FILE_SCHEMA, WRITE_FILE_SCHEMA
    with native.enter():
        written = observe(lambda: native.write('probe.txt', 'F06-NATIVE-NONSECRET-PROBE'))
        read = observe(lambda: native.read('probe.txt'))
        read_schema = ordinary_file_schema({'function': READ_FILE_SCHEMA})
        write_schema = ordinary_file_schema({'function': WRITE_FILE_SCHEMA})
        require('password' in read_schema['function']['parameters']['properties'], 'read_schema_password')
        formats = write_schema['function']['parameters']['properties']['format']['enum']
        require({'ooxml_password_edit', 'odf_password_edit'} <= set(formats), 'write_schema_password_profiles')
    with native.enter(1):
        foreign = observe(lambda: native.read(str(native.homes[0] / 'workspace/probe.txt')))
        ungranted = observe(lambda: native.write('refused.txt', 'NONSECRET'))
    require(written.get('success') is True and 'F06-NATIVE-NONSECRET-PROBE' in read.get('content', ''), 'native_text_setup')
    require(no_content(foreign) and no_content(ungranted), 'native_acl_setup')
    retained = native.sources[0]._friday_user_scope
    with native.enter():
        native.enabled(False)
        revoked = observe(lambda: native.scope.scoped_file('read_file', {'path': 'probe.txt'}))
    native.enabled(True)
    with native.scope.authority(native.homes[0]):
        sticky = observe(lambda: retained.check())
    require(revoked.get('exception_class') == sticky.get('exception_class') == 'ScopeDenied' and retained.revoked, 'native_revoke_setup')
    native.sources[0] = native.admit(0)
    with native.enter():
        fresh = observe(lambda: native.read('probe.txt'))
    require(fresh.get('success') is True, 'native_fresh_admission_setup')
    return {'native_allowlist_product_access_admission': True, 'real_provision_scope_file_tools': True, 'actual_prompt_scope_schema': True, 'own_text_write_read': True, 'foreign_path_refused': True, 'ungranted_write_refused': True, 'native_PluginState_revoke_retained_cap': True, 'reenable_does_not_revive_old_cap': True, 'fresh_generation_read': True, 'encrypted_qualification': 'NOT_RUN', 'credential_bytes_read': False}


def clear_package(raw, fmt, password):
    if fmt in ('docx', 'xlsx', 'pptx'):
        from tools.scoped_ooxml_password import prepare_read
    else:
        from tools.scoped_odf_password import prepare_read
    clear, metadata = prepare_read(raw, fmt, password)
    return clear, metadata


def audit_fixture_label(value):
    # Exact public fixture IDs remain truthful for a future reviewed subset.
    return value if type(value) is str and value in (
        'f06-1', 'f06-2', 'f06-3', 'f06-4', 'f06-5', 'f06-6', 'f06-7'
    ) else 'unclassified_fixture'


def qualify(native, m, work):
    AUDIT_PHASE.update(fixture='none', phase='credential_load')
    cred = json.loads(ref_read(m['credential'], 16384))
    password, wrong = cred['password'], cred['wrong_password']
    require(type(password) is str and type(wrong) is str and password and wrong and password != wrong, 'credential_contract')
    rows = []
    outputs = []
    from tools.read_extract import extract_scoped_document_bytes
    from hermes_cli import friday_workspace_docx as docx, friday_workspace_odf_password as odfw
    for item in m['fixtures']:
        AUDIT_PHASE.update(fixture=audit_fixture_label(item.get('id')), phase='source_setup')
        budget()
        fmt, ident = item['format'], item['id']
        data = ref_read(item['input'], 1000000)
        srcname = ident + '.' + fmt
        src = native.homes[0] / 'workspace' / srcname
        fd = os.open(src, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        output = ident + '-edited.' + fmt
        profile = 'ooxml_password_edit' if fmt in ('docx', 'xlsx', 'pptx') else 'odf_password_edit'
        spec = dict(source=srcname, source_sha256=sha(data), password=password, edit=item['edit'])
        def edit(target, changes=None):
            return observe(lambda: native.write(target, json.dumps(spec | (changes or {})), format=profile))
        def scoped_read(target):
            return observe(lambda: native.scope.scoped_file('read_file', {'path': target, 'password': password}))
        def scoped_edit(target):
            return observe(lambda: native.scope.scoped_file('write_file', {'path': target, 'content': json.dumps(spec), 'format': profile}))
        checks, receipts = {}, {}
        with native.enter():
            for label, secret in [('missing_read', None), ('wrong_read', wrong), ('correct_read', password)]:
                AUDIT_PHASE['phase'] = label
                val = observe(lambda secret=secret: native.read(srcname, password=secret))
                receipts[label] = safe_receipt(val, (password, wrong))
                checks[label] = (password_refusal(val, fmt, 'missing' if label == 'missing_read' else 'wrong') if label != 'correct_read' else val.get('success') is True and val.get('source_sha256') == sha(data) and not val.get('partial') and all(s in val.get('content', '') for s in item['expected_before']))
                if label == 'correct_read':
                    observed_modern_unsupported = modern_unsupported(val, fmt, item['profile'])
            AUDIT_PHASE['phase'] = 'wrong_edit'
            val = edit(ident + '-wrong.' + fmt, {'password': wrong})
            receipts['wrong_edit'] = safe_receipt(val, (password, wrong))
            checks['wrong_edit'] = password_refusal(val, fmt, 'wrong', edit=True) and not (src.parent / (ident + '-wrong.' + fmt)).exists()
            AUDIT_PHASE['phase'] = 'stale_hash_edit'
            val = edit(ident + '-stale.' + fmt, {'source_sha256': '0' * 64})
            receipts['stale_hash_edit'] = safe_receipt(val, (password, wrong))
            checks['stale_hash_edit'] = hash_refusal(val) and not (src.parent / (ident + '-stale.' + fmt)).exists()
            AUDIT_PHASE['phase'] = 'correct_edit'
            val = edit(output)
            receipts['correct_edit'] = safe_receipt(val, (password, wrong))
            checks['correct_edit'] = val.get('success') is True
            if checks['correct_edit']:
                dst = src.parent / output
                AUDIT_PHASE['phase'] = 'output_ciphertext_read'
                encrypted = dst.read_bytes()
                AUDIT_PHASE['phase'] = 'decrypt_before'
                clear_before, bm = clear_package(data, fmt, password)
                AUDIT_PHASE['phase'] = 'decrypt_after'
                clear_after, am = clear_package(encrypted, fmt, password)
                checks['encrypted_output'] = bool(am and am.get('encrypted', True)) and not encrypted.startswith(b'PK\x03\x04') if fmt in ('docx', 'xlsx', 'pptx') else bool(am and am.get('encrypted'))
                AUDIT_PHASE['phase'] = 'semantics_after'
                after_text = extract_scoped_document_bytes(clear_after, fmt)
                checks['native_semantics_after'] = all(s in after_text for s in item['expected_after'])
                AUDIT_PHASE['phase'] = 'member_comparison'
                with zipfile.ZipFile(io.BytesIO(clear_before)) as beforezip, zipfile.ZipFile(io.BytesIO(clear_after)) as afterzip:
                    beforeparts = {n: beforezip.read(n) for n in beforezip.namelist()}
                    afterparts = {n: afterzip.read(n) for n in afterzip.namelist()}
                changed = [n for n in beforeparts if beforeparts.get(n) != afterparts.get(n) and n != 'META-INF/manifest.xml']
                checks['unaffected_members'] = set(beforeparts) == set(afterparts) and bool(changed) and set(changed) <= set(item['changed_member_allowlist'])
                AUDIT_PHASE['phase'] = 'output_metadata'
                checks['output_mode0600'] = stat.S_IMODE(private(dst).st_mode) == 0o600
                AUDIT_PHASE['phase'] = 'output_wrong_password'
                wrong_out = observe(lambda: native.read(output, password=wrong))
                checks['output_wrong_password'] = password_refusal(wrong_out, fmt, 'wrong')
                AUDIT_PHASE['phase'] = 'output_correct_native_read'
                correct_out = observe(lambda: native.read(output, password=password))
                checks['output_correct_native_read'] = correct_out.get('success') is True and correct_out.get('source_sha256') == sha(encrypted) and not correct_out.get('partial') and all(s in correct_out.get('content', '') for s in item['expected_after'])
                # A second write cannot replace the same existing ciphertext.
                AUDIT_PHASE['phase'] = 'output_noreplace'
                prior = dst.read_bytes(); collision = edit(output)
                checks['noreplace'] = collision_refusal(collision, fmt) and dst.read_bytes() == prior
                outputs.append({'fixture_id': ident, 'format': fmt, 'path': str(dst), 'sha256': sha(encrypted), 'bytes': len(encrypted), 'independent_output_oracle': 'NOT_RUN_ROOT_SEPARATE_OPERATION_REQUIRED'})
            AUDIT_PHASE['phase'] = 'scope_and_cas_controls'
            # Fault timing only: native renderer/auth/CAS/publication remain real.
            # One representative per wrapper; do not waste crypto for every family.
            if fmt in ('docx', 'odt') and item['profile'] == 'compatible':
                os.chmod(src, 0o644)
                try:
                    checks['unsafe_source_mode_refused'] = scope_refusal(scoped_read(srcname))
                finally:
                    os.chmod(src, 0o600)
                alias = src.parent / (ident + '-link.' + fmt)
                alias.symlink_to(srcname)
                try:
                    checks['source_symlink_refused'] = scope_refusal(scoped_read(alias.name))
                finally:
                    alias.unlink()
                sentinel = src.parent / (ident + '-sentinel.txt')
                sentinel.write_bytes(b'F06-NONSECRET-NOREPLACE-SENTINEL')
                linkout = src.parent / (ident + '-output-link.' + fmt)
                linkout.symlink_to(sentinel.name)
                try:
                    val = edit(linkout.name)
                    checks['output_symlink_noreplace'] = collision_refusal(val, fmt) and linkout.is_symlink() and sentinel.read_bytes() == b'F06-NONSECRET-NOREPLACE-SENTINEL'
                finally:
                    linkout.unlink()
                original_docx, original_odf = docx._create_bytes, odfw._create_bytes
                injected = []
                source_verifier_denials = []
                def mutate_before_publish(*args, **kwargs):
                    injected.append(True)
                    with src.open('ab') as stream:
                        stream.write(b'X')
                    original_verify = kwargs.get('verify_source')
                    require(callable(original_verify), 'native_source_verifier_missing')
                    def traced_verify():
                        try:
                            return original_verify()
                        except native.scope.ScopeDenied:
                            source_verifier_denials.append(True)
                            raise
                    kwargs['verify_source'] = traced_verify
                    return original_docx(*args, **kwargs)
                try:
                    docx._create_bytes = odfw._create_bytes = mutate_before_publish
                    val = edit(ident + '-cas-race.' + fmt)
                    checks['source_identity_cas'] = cas_refusal(val, bool(injected), bool(source_verifier_denials)) and not (src.parent / (ident + '-cas-race.' + fmt)).exists()
                finally:
                    docx._create_bytes, odfw._create_bytes = original_docx, original_odf
                    src.write_bytes(data)
        AUDIT_PHASE['phase'] = 'foreign_scope_controls'
        with native.enter(1):
            checks['foreign_read_acl'] = scope_refusal(scoped_read(str(src)))
            checks['ungranted_edit_acl'] = scope_refusal(scoped_edit('ungranted-' + ident + '.' + fmt))
        AUDIT_PHASE['phase'] = 'revocation_controls'
        # Revocation occurs via real PluginState before create, old capability stays dead.
        if fmt in ('docx', 'odt') and item['profile'] == 'compatible':
            retained = native.sources[0]._friday_user_scope
            with native.enter():
                native.enabled(False)
                revoked = observe(lambda: native.scope.scoped_file('write_file', {'path': ident + '-revoked.' + fmt, 'format': profile, 'content': json.dumps(spec)}))
                checks['retained_revoke'] = scope_refusal(revoked) and not (src.parent / (ident + '-revoked.' + fmt)).exists()
            native.enabled(True)
            with native.scope.authority(native.homes[0]):
                sticky = observe(lambda: retained.check())
            checks['sticky_revocation'] = retained.revoked is True and sticky.get('exception_class') == 'ScopeDenied'
            native.sources[0] = native.admit(0)
        AUDIT_PHASE['phase'] = 'source_and_staging_preserved'
        checks['source_bytes_preserved'] = src.read_bytes() == data
        checks['no_staging_left'] = not any(p.name.startswith('.friday-docx-') for p in src.parent.iterdir())
        status = 'NATIVE_PASS_OUTPUT_ORACLE_PENDING' if all(checks.values()) else 'NATIVE_FAIL'
        if observed_modern_unsupported:
            status = 'CURRENT_LATEST_UNSUPPORTED_OBSERVED_NOT_PASS'
        rows.append({'id': ident, 'format': fmt, 'profile': item['profile'], 'status': status, 'checks': checks, 'receipts': receipts})
        AUDIT_PHASE['phase'] = 'row_observations_persist'
        dump(work / 'OBSERVATIONS.json', rows)
    AUDIT_PHASE.update(fixture='none', phase='owned_output_secret_control')
    # Local secret leak control; never persist values or matching content.
    secrets_present = any(secret.encode() in p.read_bytes() for p in work.rglob('*') if p.is_file() for secret in (password, wrong))
    require(not secrets_present, 'secret_in_owned_output')
    AUDIT_PHASE['phase'] = 'output_oracle_request_persist'
    dump(work / 'OUTPUT-ORACLE-REQUESTS.json', {'outputs': outputs, 'credential': m['credential'], 'stage': 'NOT_RUN', 'instruction': 'Root independently reopen these SAME encrypted bytes with missing/wrong/correct passwords and compare requested semantics; do not recreate/native-edit/send again.'})
    return {'fixtures': rows, 'output_oracle': 'PENDING_SEPARATE_ROOT', 'all_f06_accepted': False, 'secret_bytes_in_owned_outputs': False}


def worker(args):
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY, MEMORY))
    private(BASE, True)
    pins_check()
    m = binding_check(Path(args.manifest), args.manifest_sha256, Path(args.root_grant), args.root_grant_sha256) if args.mode == 'qualify' else None
    if m:
        dump(BASE / 'QUALIFICATION-ONCE.json', {'manifest_sha256': args.manifest_sha256, 'root_grant_sha256': args.root_grant_sha256, 'started': time.time(), 'effect': 'BOUND_NATIVE_QUALIFICATION', 'automatic_retry': False}, exclusive=True)
    name = 'qualification' if m else 'prepare-' + args.check_id
    work = BASE / name
    work.mkdir(mode=0o700)
    started = time.monotonic()
    install_boundary(work, m)
    if m:
        class DiscardNativeOutput:
            def write(self, value):
                return len(value)
            def flush(self):
                pass
        # Unexpected native debug/error output cannot persist supplied passwords.
        sys.stdout = sys.stderr = DiscardNativeOutput()
    status = {'status': 'INCOMPLETE', 'encrypted': bool(m)}
    try:
        AUDIT_PHASE.update(fixture='none', phase='native_setup')
        native = Native(work)
        status = qualify(native, m, work) if m else prepare(native)
        status['status'] = 'COMPLETED_BOUNDED_NATIVE' if m else 'PREPARATION_CHECK_PASS'
    except Exception as error:
        status.update(status='REFUSED_OR_FAILED', exception_class=type(error).__name__, code=str(error) if isinstance(error, Refused) else 'fixed_no_exception_message')
    AUDIT_PHASE.update(fixture='none', phase='imported_source_inventory')
    imports = []
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_relative_to(SOURCE) and Path(path).is_file():
            imports.append({'module': name, 'relative': str(Path(path).relative_to(SOURCE)), 'sha256': sha(Path(path).read_bytes())})
    dump(work / 'IMPORTED-SOURCE-PINS.json', imports)
    status.update(elapsed_seconds=time.monotonic() - started, cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime, maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, audit_denials=DENIED, current_data_read_absence='NOT_PROVEN_BY_PYTHON_AUDIT_ALONE', own_HOME_HERMES_HOME_XDG_TMP_before_native_imports=True, Office_model_network=False)
    dump(work / 'SUMMARY.json', status)
    return 0 if status['status'] in ('COMPLETED_BOUNDED_NATIVE', 'PREPARATION_CHECK_PASS') else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=('prepare-check', 'check-binding', 'qualify'))
    ap.add_argument('--check-id', default='1')
    ap.add_argument('--manifest')
    ap.add_argument('--manifest-sha256')
    ap.add_argument('--root-grant')
    ap.add_argument('--root-grant-sha256')
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()
    os.umask(0o077)
    require(re.fullmatch('[a-zA-Z0-9_-]{1,32}', args.check_id), 'check_id')
    if args.mode in ('check-binding', 'qualify'):
        require(args.manifest and args.manifest_sha256 and HEX.fullmatch(args.manifest_sha256), 'unbound_manifest')
        require(args.root_grant and args.root_grant_sha256 and HEX.fullmatch(args.root_grant_sha256), 'unbound_root_grant')
    if args.worker:
        return worker(args)
    private(BASE, True); pins_check(); budget()
    if args.mode == 'check-binding':
        binding_check(Path(args.manifest), args.manifest_sha256, Path(args.root_grant), args.root_grant_sha256)
        print('BOUND_METADATA_CHECK_PASS_NO_CREDENTIAL_BYTES_READ')
        return 0
    require(not (BASE / ('qualification' if args.mode == 'qualify' else 'prepare-' + args.check_id)).exists(), 'existing_operation_no_retry')
    # Single fresh process group; there are no child processes inside the worker.
    command = [str(PYTHON), '-I', '-B', str(Path(__file__)), args.mode, '--worker', '--check-id', args.check_id]
    if args.manifest:
        command += ['--manifest', args.manifest, '--manifest-sha256', args.manifest_sha256]
        command += ['--root-grant', args.root_grant, '--root-grant-sha256', args.root_grant_sha256]
    log = BASE / ('qualification-launch.log' if args.mode == 'qualify' else 'prepare-' + args.check_id + '-launch.log')
    with open(log, 'xb') as output:
        p = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=output, start_new_session=True, cwd=BASE, env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'HOME': str(BASE / 'unused-os-home')})
        try:
            code = p.wait(timeout=WALL)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            dump(BASE / 'TIMEOUT.json', {'status': 'TIMED_OUT_RECONCILE_NO_RETRY', 'mode': args.mode, 'group_reaped': True})
            return 124
    print('NATIVE_OPERATION_COMPLETE' if code == 0 else 'NATIVE_OPERATION_FAILED_RECONCILE_NO_RETRY')
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Credential values/exception messages never reach stdout/stderr, even setup errors.
        print('F06_HARNESS_REFUSED:' + type(error).__name__ + (':' + str(error) if isinstance(error, Refused) else ''), file=sys.stderr)
        raise SystemExit(2)
