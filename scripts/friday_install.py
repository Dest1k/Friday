#!/usr/bin/env python3
"""Finite Friday composition over native preparers, PM and launchers.

Installation is an explicit effectful operator action. Planning and inspection
never install dependencies, read credentials or grant worker admission.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import ipaddress
import importlib.util
import importlib.machinery
import importlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'friday.native-install.v1'
MARKER = 'FRIDAY-INSTALL.json'
FAILURE = 'FRIDAY-INSTALL.failure.json'
HISTORY = {'claim': 'FRIDAY-INSTALL.original.json',
           'input': 'FRIDAY-INSTALL.original-input.json',
           'authorization': 'FRIDAY-INSTALL.continuation.json'}
REPAIR_FILES = {'scripts/friday_install.py', 'scripts/friday_native.py',
                'scripts/hermes_prepare.py', 'scripts/install_containment.py',
                'scripts/dsh_prepare.py'}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Friday entry refused: phase=arguments reason=invalid_cli_arguments\n')


class Refused(ValueError):
    """A reason supplied by this source, rather than arbitrary exception text."""
    def __init__(self, reason):
        self.reason = reason if re.fullmatch('[a-z][a-z0-9_]{0,127}', reason) else 'invalid_input'
        super().__init__(self.reason)


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def safe_diagnostic(exc, phase):
    from scripts.dsh_prepare import CommandFailed, StopUnconfirmed
    result = {'phase': phase, 'reason': 'native_operation_failed'}
    if isinstance(exc, StopUnconfirmed):
        result.update(reason='stop_unconfirmed', cessation='UNCONFIRMED')
        if hasattr(exc, 'observation'):
            result.update(exc.observation)
            result.update(reason='stop_unconfirmed', cessation='UNCONFIRMED')
    elif isinstance(exc, CommandFailed):
        result.update(exc.observation)
        result['cessation'] = 'REAPED' if exc.observation['reaped'] else 'UNCONFIRMED'
    elif isinstance(exc, Refused):
        result['reason'] = exc.reason
    elif isinstance(exc, OSError):
        result.update(reason='native_io_failed', errno=exc.errno)
    elif isinstance(exc, (KeyError, TypeError)):
        result['reason'] = 'invalid_input_shape'
    elif isinstance(exc, ValueError) and exc.args == ('original_install_budget_exhausted',):
        result['reason'] = 'original_install_budget_exhausted'
    return result


def diagnostic_text(value):
    parts = [f"phase={value['phase']}", f"reason={value['reason']}"]
    if 'returncode' in value:
        parts.extend([f"child_exit={value['returncode']}",
                      f"timeout={str(value['timeout']).lower()}",
                      f"reaped={str(value['reaped']).lower()}"])
    return ' '.join(parts)


def canonical(value):
    p = Path(value)
    require(p.is_absolute() and str(p) == value and '..' not in p.parts
            and p != Path('/') and p.resolve() == p, 'real_absolute_path_required')
    return p


def owned_file(path, *, private=False):
    p = canonical(str(path))
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and info.st_nlink == 1
                and (not private or not info.st_mode & 0o077), 'owned_regular_input_required')
        with os.fdopen(fd, 'rb', closefd=False) as f:
            data = f.read(64 * 1024**2 + 1)
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_uid', 'st_nlink')
        require(len(data) <= 64 * 1024**2 and all(getattr(info, k) == getattr(after, k) for k in fields),
                'input_changed_or_too_large')
        return data
    finally:
        os.close(fd)


def unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate_input_field')
        out[key] = value
    return out


def read_json(path):
    return json.loads(owned_file(path, private=True), object_pairs_hook=unique)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
            and isinstance(value['sha256'], str)
            and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'exact_input_pin_required')
    require(digest(owned_file(value['path'])) == value['sha256'], 'input_pin_changed')
    return canonical(value['path'])


def bootstrap_pin(value):
    """Hash the protected PM Python as a bounded executable, not JSON/source.

    The native standalone Python can exceed the 64 MiB document limit. Read
    this explicitly typed input in chunks; all other input limits stay intact.
    """
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
            and isinstance(value['sha256'], str)
            and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'exact_input_pin_required')
    path = canonical(value['path'])
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        limit = 256 * 1024**2
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1 and not before.st_mode & 0o022
                and bool(before.st_mode & 0o111) and 0 < before.st_size <= limit,
                'owned_protected_bootstrap_executable_required')
        hasher = hashlib.sha256(); total = 0
        while True:
            block = os.read(fd, min(1024**2, limit - total + 1))
            if not block:
                break
            total += len(block)
            require(total <= limit, 'bootstrap_executable_too_large')
            hasher.update(block)
        after, named = os.fstat(fd), path.lstat()
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_uid', 'st_nlink')
        require(total == before.st_size and all(
            getattr(before, k) == getattr(after, k) == getattr(named, k) for k in fields),
            'bootstrap_executable_changed')
        require(hasher.hexdigest() == value['sha256'], 'input_pin_changed')
    finally:
        os.close(fd)
    return path


def directory(path):
    p = canonical(str(path)); info = p.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700, 'owned_private_directory_required')
    return p


def spec_checked(value):
    fields = {'home', 'bootstrap_python', 'hermes_donor', 'hermes_prepare',
              'sources_lock', 'dsh_donor', 'a0_donor', 'product', 'project_files', 'seconds', 'containment'}
    require(isinstance(value, dict) and set(value) == fields | ({'dashboard_tls'} if 'dashboard_tls' in value else set()), 'explicit_install_fields_required')
    home = canonical(value['home']); directory(home.parent)
    require(home != Path.home() / '.hermes' and home != ROOT
            and not ROOT.is_relative_to(home), 'separate_product_home_required')
    require(type(value['seconds']) is int and 30 <= value['seconds'] <= 7200,
            'finite_install_budget_required')
    bootstrap_pin(value['bootstrap_python'])
    for key in ('hermes_prepare', 'sources_lock'):
        pin(value[key])
    for key in ('hermes_donor', 'dsh_donor', 'a0_donor'):
        canonical(value[key])
    require(canonical(value['dsh_donor']) == home / 'harness', 'owned_harness_destination_required')
    files = value['project_files']
    require(isinstance(files, dict) and files, 'reviewed_project_inventory_required')
    required = {'scripts/friday_install.py', 'scripts/friday_native.py',
                'scripts/dsh_prepare.py', 'plugins/friday_rework/adapters/dsh_keyless_web.mjs', 'scripts/a0_prepare.py', 'scripts/install_containment.py',
                'scripts/friday_start.py',
                'scripts/a0_runtime.py', 'scripts/rootless_docker_launch.py',
                'tools/configure_product.py', 'tools/configure_local_test.py',
                'tools/web_profile.py', 'config/SOUL.md', 'config/RESEARCH.md'}
    required.update(str(p.relative_to(ROOT)) for p in (ROOT / 'plugins/friday_rework').rglob('*')
                    if p.is_file())
    required.update(str(p.relative_to(ROOT)) for p in (ROOT / 'patches/hermes').rglob('*')
                    if p.is_file())
    require(required.issubset(files), 'complete_installer_plugin_inventory_required')
    for name, expected in files.items():
        require(isinstance(name, str) and not name.startswith('/')
                and '..' not in Path(name).parts and isinstance(expected, str)
                and re.fullmatch('[0-9a-f]{64}', expected), 'invalid_project_inventory')
        require(digest(owned_file(ROOT / name)) == expected, 'project_source_changed')
    product = value['product']
    require(isinstance(product, dict) and product.get('profile') == 'default',
            'native_default_receiving_home_required')
    require(isinstance(product.get('dashboard'), dict)
            and set(product['dashboard']) == {'host', 'port', 'public_url', 'operator'} | ({'tls'} if 'tls' in product['dashboard'] else set()),
            'explicit_dashboard_authority_required')
    # Reuse the existing pure local/capacity validator before any install
    # effects. Full native profile/provider/auth consumption happens later.
    # Load pure validators without claiming Hermes' native `tools` package.
    name = '_friday_install_validation'
    if name not in sys.modules:
        module = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(name, loader=None, is_package=True))
        module.__path__ = [str(ROOT / 'tools')]
        sys.modules[name] = module
    require(list(sys.modules[name].__path__) == [str(ROOT / 'tools')], 'foreign_validator_package')
    build_config = importlib.import_module(name + '.configure_local_test').build_config
    hermes_web_config = importlib.import_module(name + '.web_profile').hermes_web_config
    # Host-root ownership is checked at command admission, not by this pure
    # consumer inside an unprivileged namespace (where host UID 0 is unmapped).
    containment = value['containment']
    require(isinstance(containment, dict) and set(containment) == {'path', 'sha256'}
            and containment['path'] == '/usr/bin/bwrap'
            and isinstance(containment['sha256'], str)
            and re.fullmatch('[0-9a-f]{64}', containment['sha256']),
            'explicit_system_bubblewrap_pin_required')
    require(set(product) == {'profile', 'inference', 'web', 'dashboard', 'accounts', 'runtime'} | ({'a0_deployment'} if 'a0_deployment' in product else set()),
            'explicit_normal_product_required')
    if 'a0_deployment' in product:
        spec = importlib.util.spec_from_file_location('_friday_a0_profile_validator', ROOT / 'plugins/friday_rework/adapters/a0_profile.py')
        profile_validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profile_validator)
        deployment = profile_validator.checked_profile(product['a0_deployment'])
        selected = product['inference']
        chat = deployment['chat']
        require(chat['endpoint'] == selected['base_url'] and chat['model'] == selected['model']
                and chat['context_length'] == selected['context']
                and chat['max_output_tokens'] == selected['main_output']
                and selected['key_env'] == 'FRIDAY_LLM_API_KEY', 'a0_product_inference_profile_mismatch')
    build_config(**product['inference'])
    require(product['web'].get('profile') in ('exa-paid','exa-keyless')
            and set(product['web']) == {'profile', 'extract_char_limit', 'extract_timeout'}
            and all(product['web'][k] is not None for k in ('extract_char_limit', 'extract_timeout')),
            'mandatory_scoped_web_required')
    hermes_web_config(**product['web'])
    dash = product['dashboard']; ipaddress.ip_address(dash['host'])
    require(type(dash['port']) is int and 1 <= dash['port'] <= 65535, 'explicit_dashboard_port_required')
    public = urlsplit(dash['public_url'])
    local_http = (public.scheme == 'http' and public.hostname in ('localhost', '127.0.0.1', '::1')
                  and ipaddress.ip_address(dash['host']).is_loopback)
    require((public.scheme == 'https' or local_http) and public.hostname and public.username is None
            and public.password is None and public.port == dash['port']
            and public.path in ('', '/') and not public.query and not public.fragment,
            'protected_dashboard_public_authority_required')
    dashboard_tls_inputs(value, home)
    lock = json.loads(owned_file(pin(value['sources_lock'])))
    donors = {r['id']: r for r in lock['repositories']}
    require({'hermes', 'dsh', 'a0'}.issubset(donors), 'complete_donor_pins_required')
    return home, donors


def dashboard_tls_inputs(value, home):
    """Explicit protected deployment inputs; no issuer or trust-store writes."""
    dash = value['product']['dashboard']
    names = {'certfile': 'dashboard-tls/server.pem', 'keyfile': 'dashboard-tls/server.key',
             'cafile': 'dashboard-tls/ca.pem'}
    if 'tls' not in dash:
        require('dashboard_tls' not in value, 'undeclared_dashboard_tls_inputs')
        return {}
    require(dash['tls'] == names, 'explicit_owned_dashboard_tls_files_required')
    bind = ipaddress.ip_address(dash['host'])
    require(not bind.is_unspecified and not bind.is_multicast
            and urlsplit(dash['public_url']).scheme == 'https', 'explicit_dashboard_tls_authority_required')
    inputs = value.get('dashboard_tls')
    require(isinstance(inputs, dict) and set(inputs) == set(names), 'dashboard_tls_deployment_inputs_required')
    parents = set(); output = {}
    for key, row in inputs.items():
        path = pin(row); directory(path.parent); parents.add(path.parent)
        require(path.name == Path(names[key]).name and not path.is_relative_to(home),
                'separate_owned_dashboard_tls_input_required')
        raw = owned_file(path, private=True)
        require(digest(raw) == row['sha256'], 'dashboard_tls_input_changed')
        output[key] = raw
    require(len(parents) == 1, 'one_owned_dashboard_tls_input_scope_required')
    return output


def commands(value):
    """Generate native argv; no custom PM flags or replacement service backend."""
    home, _ = spec_checked(value); source = home / 'hermes-agent'
    from scripts.install_containment import checked_binary
    checked_binary(value['containment'])
    python = value['bootstrap_python']['path']; helper = str(ROOT / 'scripts/friday_native.py')
    launcher = str(source / '.hermes/bin/hermes')
    return {
        'compose': [python, '-B', value['hermes_prepare']['path'], '--repository', str(ROOT),
                    '--donor', value['hermes_donor'], '--destination', str(source),
                    '--seconds', str(min(120, value['seconds']))],
        'tools': [python, '-B', '-m', 'pm.cli', 'install', '--tools-only'],
        'dependencies': [python, '-B', '-m', 'pm.cli', 'install', '--extra', 'all',
                         '--extra', 'telegram', '--extra', 'web', '--extra', 'exa'],
        'native_completion': ['<native PM project_python>', '-B', helper, 'install'],
        'harness': [[python, '-B', str(ROOT / 'scripts/dsh_prepare.py'), phase,
                     '--donor', value['dsh_donor'], '--lock', value['sources_lock']['path'],
                     '--evidence', str(home / 'preparation/harness')]
                    for phase in ('source', 'toolchain', 'build', 'smoke')],
        'a0_inventory': [python, '-B', str(ROOT / 'scripts/a0_prepare.py'), 'prepare',
                         '--lock', value['sources_lock']['path'], '--checkout', value['a0_donor'],
                         '--output', str(home / 'preparation/a0.json')],
        'gateway_install': [launcher, '-p', 'default', 'gateway', 'install',
                            '--no-start-now', '--no-start-on-login'],
        'gateway_start': [launcher, '-p', 'default', 'gateway', 'start'],
        'dashboard': [launcher, '-p', 'default', 'dashboard', '--host',
                      value['product']['dashboard']['host'], '--port',
                      str(value['product']['dashboard']['port']), '--no-open'],
    }


def clean_environment(home):
    # Preserve the OS account HOME: native host rendezvous remains host-wide.
    # No ambient provider/token/auth/profile/runtime/PYTHONPATH influences PM.
    names = ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'TERM',
             'HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY', 'https_proxy', 'http_proxy', 'no_proxy')
    env = {k: os.environ[k] for k in names if k in os.environ}
    env.update(HERMES_HOME=str(home), PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0',
               GIT_TERMINAL_PROMPT='0', PYTHONNOUSERSITE='1')
    return env


def source_checked(source, receipt, donor):
    """Check every exported/overlaid byte; receipt status alone is insufficient."""
    require(receipt.get('schema') == 'friday.hermes-source.v1'
            and receipt.get('commit') == donor['commit']
            and receipt.get('base_tree') == donor['tree']
            and receipt.get('status') == 'SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED',
            'hermes_composition_identity_required')
    files = receipt.get('files')
    require(isinstance(files, dict) and len(files) > 1000, 'complete_hermes_inventory_required')
    for name, row in files.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,
                'unsafe_source_inventory_path')
        data = owned_file(source / name)
        require(digest(data) == row['sha256'] and len(data) == row['bytes']
                and bool((source / name).stat().st_mode & 0o111) == (row['mode'] == '100755'),
                'composed_source_changed')
    # Generated native products may coexist; never load a hidden source .env.
    require(not (source / '.env').exists() and not (source / '.env').is_symlink()
            and all(str(p.relative_to(source)) in files for p in source.glob('.env*')),
            'source_credential_file_refused')
    generated = ('.hermes/', 'node_modules/', 'hermes_cli/web_dist/', 'ui-tui/dist/',
                 'ui-tui/node_modules/', 'web/node_modules/', 'apps/shared/node_modules/')
    generated_files = {'install-stamp.json', '.hermes-bytecode-fingerprint'}
    for p in source.rglob('*'):
        name = str(p.relative_to(source))
        if p.is_symlink():
            require(name.startswith(generated), 'unexpected_source_link')
        if p.is_dir():
            continue
        require(name in files or name in generated_files or name.startswith(generated),
                'unexpected_composed_source_file')
    return files


def composition_checked(value, source, receipt, donor):
    require(receipt.get('sources_lock_sha256') == value['sources_lock']['sha256'],
            'composition_source_lock_changed')
    rows = receipt.get('layers')
    require(isinstance(rows, list), 'composition_overlay_inventory_missing')
    manifests = {n: h for n, h in value['project_files'].items()
                 if n.startswith('patches/hermes/') and n.endswith('.json')}
    require(len(rows) == len(manifests) and {r.get('manifest') for r in rows} == set(manifests),
            'composition_overlay_set_changed')
    for row in rows:
        name = row['manifest']; require(row.get('manifest_sha256') == manifests[name],
                                        'composition_overlay_manifest_changed')
        body = json.loads(owned_file(ROOT / name))
        patch = body.get('patch') or 'patches/hermes/' + body['patch_file']
        require(row.get('patch_sha256') == body['patch_sha256'] == value['project_files'][patch],
                'composition_overlay_patch_changed')
    return source_checked(source, receipt, donor)


def publish(path, value, *, budget=None):
    # Serialize before opening a file; long serialization cannot admit a write.
    payload = json.dumps(value, sort_keys=True, indent=2) + '\n'
    if budget: budget.check()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        if budget: budget.check()
        f.write(payload)
        if budget: budget.check()
        f.flush()
        if budget: budget.check()
        os.fsync(f.fileno())
        if budget: budget.check()
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        if budget: budget.check()
        os.fsync(fd)
        if budget: budget.check()
    finally:
        os.close(fd)


def partial_claim(input_hash, budget):
    return {'schema': SCHEMA, 'state': 'PARTIAL', 'input_sha256': input_hash,
            'deadline_mono': budget.deadline,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def reconcile(value, input_hash):
    """Read-only PARTIAL observation, with no replay or fresh execution grant.

    Legacy claims contain no durable child identity/cessation receipt. A clean
    directory, absent parent or lock availability cannot fill that evidence gap.
    Even a new failure receipt is historical evidence, not current quiescence.
    """
    require(isinstance(value, dict), 'explicit_install_fields_required')
    home = canonical(value['home']); directory(home)
    claim = read_json(home / MARKER)
    require(set(claim) == {'schema', 'state', 'input_sha256', 'deadline_mono', 'boot_id'}
            and claim['schema'] == SCHEMA and claim['state'] == 'PARTIAL'
            and claim['input_sha256'] == input_hash, 'exact_original_partial_claim_required')
    require(claim['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'original_install_boot_changed')
    deadline = claim['deadline_mono']
    require(type(deadline) in (int, float) and math.isfinite(deadline) and deadline > 0,
            'original_install_deadline_required')
    extra = False; count = 0
    with os.scandir(home) as entries:
        for item in entries:
            count += 1
            if item.name not in (MARKER, FAILURE): extra = True
            require(count <= 128, 'partial_observation_inventory_limit')
    failure = home / FAILURE
    has_failure = failure.exists() or failure.is_symlink()
    if has_failure:
        observation = read_json(failure)
        require(observation.get('schema') == 'friday.native-install-failure.v1'
                and observation.get('original_attempt') == claim
                and observation.get('resume_allowed') is False, 'failure_receipt_not_bound')
    remaining = max(0, deadline - time.monotonic())
    return {'state': 'PARTIAL_RETAINED_NO_REPLAY', 'effects': 'NONE', 'ready': False,
            'resume_allowed': False, 'original_attempt': claim,
            'original_remaining_seconds': remaining, 'original_budget_expired': remaining == 0,
            'contains_other_files': extra, 'historical_failure_receipt_bound': has_failure,
            'cessation': 'CURRENT_NATIVE_VERIFICATION_REQUIRED',
            'next': 'Independent lead review of original attempt, current cessation, repaired source pins and original clock; no replay admission'}


def immutable_bytes(path):
    raw = owned_file(path, private=True)
    require(stat.S_IMODE(Path(path).stat().st_mode) == 0o400,
            'immutable_continuation_evidence_required')
    return raw


def continuation_evidence(value, input_hash, authorization, authorization_hash,
                          original_raw, original_input_raw):
    """Operator-pinned independent reviews, never a self-reported ready flag.

    The out-of-band authorization digest is the operator trust anchor. File
    ownership alone does not establish that a review happened.
    """
    require(digest(authorization) == authorization_hash,
            'continuation_authorization_changed')
    auth = json.loads(authorization, object_pairs_hook=unique)
    require(isinstance(auth, dict) and set(auth) == {'schema', 'original_claim_sha256', 'original_input_sha256',
                         'current_input_sha256', 'cessation_review', 'repair_review'}
            and auth['schema'] == 'friday.pre-compose-continuation.v1'
            and auth['original_claim_sha256'] == digest(original_raw)
            and auth['original_input_sha256'] == digest(original_input_raw)
            and auth['current_input_sha256'] == input_hash,
            'exact_continuation_authority_required')
    original = json.loads(original_raw, object_pairs_hook=unique)
    old = json.loads(original_input_raw, object_pairs_hook=unique)
    require(isinstance(old, dict) and isinstance(original, dict) and set(original) ==
            {'schema', 'state', 'input_sha256', 'deadline_mono', 'boot_id'}
            and original['schema'] == SCHEMA and original['state'] == 'PARTIAL'
            and original['input_sha256'] == digest(original_input_raw),
            'exact_original_partial_claim_required')
    require(original['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'original_install_boot_changed')
    deadline = original['deadline_mono']
    require(type(deadline) in (int, float) and math.isfinite(deadline) and deadline > time.monotonic(),
            'original_install_budget_exhausted')
    # Immutable settings include destinations, donor lock, clocks, runtime,
    # worker map and credential *references*. No secret file is opened here.
    require(set(old) == set(value) and all(old[k] == value[k] for k in old
            if k not in ('project_files', 'hermes_prepare')),
            'continuation_settings_changed')
    previous, current = old['project_files'], value['project_files']
    require(isinstance(previous, dict) and isinstance(current, dict)
            and set(previous) == set(current), 'continuation_inventory_changed')
    changes = {k: {'before': previous[k], 'after': current[k]} for k in previous
               if previous[k] != current[k]}
    require(changes and set(changes).issubset(REPAIR_FILES), 'unreviewable_continuation_delta')
    require(set(old['hermes_prepare']) == set(value['hermes_prepare']) == {'path', 'sha256'}
            and value['hermes_prepare']['path'] == str(ROOT / 'scripts/hermes_prepare.py')
            and value['hermes_prepare']['sha256'] == current['scripts/hermes_prepare.py']
            and old['hermes_prepare']['sha256'] == previous['scripts/hermes_prepare.py'],
            'continuation_composer_changed')
    cessation_path = pin(auth['cessation_review'])
    cessation_raw = immutable_bytes(cessation_path)
    require(digest(cessation_raw) == auth['cessation_review']['sha256'], 'cessation_review_changed')
    cessation = json.loads(cessation_raw, object_pairs_hook=unique)
    require(isinstance(cessation, dict), 'independent_first_cessation_required')
    first = cessation.get('first_attempt', {})
    require(isinstance(first, dict), 'independent_first_cessation_required')
    require(cessation.get('assignment') == 'FRW032-INSTALL-CUSTODY-REVIEW'
            and cessation.get('generation') == 1
            and first.get('assignment') == 'FRW032-NORMAL-INSTALL-FIRST-ATTEMPT#1'
            and first.get('cessation_established') is True
            and first.get('claim_preserved') == original
            and first.get('original_installer_seconds') == old['seconds']
            and first.get('resume_granted') is False,
            'independent_first_cessation_required')
    refs = cessation.get('exact_refs', {})
    require(cessation.get('verdict') ==
            'FIRST_ATTEMPT_CESSATION_ESTABLISHED_RETROSPECTIVELY_AT_CENSUS; GENERAL_CONTAINMENT_COMPLETION_BARRIER_INSUFFICIENT'
            and refs.get('marker', {}).get('sha256') == digest(original_raw),
            'reviewed_first_census_required')
    census_path = pin(refs.get('census'))
    census_raw = immutable_bytes(census_path)
    require(digest(census_raw) == refs['census']['sha256'], 'cessation_census_changed')
    census = json.loads(census_raw, object_pairs_hook=unique)
    rows, interval = census.get('rows'), census.get('inclusive_candidate_starttime_ticks')
    require(census.get('schema') == 'friday.readonly-namespace-init-census.v1'
            and census.get('assignment') == 'FRW032-INSTALL-CUSTODY-REVIEW#1'
            and census.get('boot_id') == census.get('boot_id_after') == original['boot_id']
            and census.get('original_boot_matches') is True
            and census.get('completed_msk') == first.get('established_as_of_msk')
            and census.get('returned_sha256') == refs.get('returned', {}).get('sha256')
            and isinstance(rows, list) and rows
            and type(census.get('listed_count')) is int
            and census['listed_count'] == census.get('read_count') == len(rows)
            and census.get('read_errors') == census.get('vanished_during_read') == census.get('candidate_processes') == []
            and isinstance(interval, list) and len(interval) == 2
            and all(type(n) is int and n >= 0 for n in interval) and interval[0] <= interval[1]
            and all(isinstance(r, dict) and type(r.get('pid')) is int and r['pid'] > 0
                    and type(r.get('starttime_ticks')) is int
                    and not interval[0] <= r['starttime_ticks'] <= interval[1] for r in rows)
            and len({r['pid'] for r in rows}) == len(rows),
            'complete_reviewed_cessation_census_required')
    review_path = pin(auth['repair_review'])
    review_raw = immutable_bytes(review_path)
    require(digest(review_raw) == auth['repair_review']['sha256'], 'repair_review_changed')
    review = json.loads(review_raw, object_pairs_hook=unique)
    require(isinstance(review, dict) and set(review) == {'schema', 'reviewer', 'decision', 'stage',
                           'original_claim_sha256', 'original_input_sha256',
                           'current_input_sha256', 'cessation_review_sha256', 'source_changes'}
            and review['schema'] == 'friday.pre-compose-repair-review.v1'
            and review['reviewer'] == 'Astra'
            and review['decision'] == 'ALLOW_PRECOMPOSE_CONTINUATION'
            and review['stage'] == 'BEFORE_COMPOSE'
            and all(review[k] == auth[k] for k in
                    ('original_claim_sha256', 'original_input_sha256', 'current_input_sha256'))
            and review['cessation_review_sha256'] == auth['cessation_review']['sha256']
            and review['source_changes'] == changes,
            'independent_exact_repair_review_required')
    return original


def active_claim_checked(value, input_hash, budget):
    """Shared host/native consumer; continued claims retain the original clock."""
    home = Path(value['home']); claim = read_json(home / MARKER)
    expected = partial_claim(input_hash, budget)
    if claim == expected:
        return claim
    require(set(claim) == set(expected) | {'continuation'}
            and all(claim[k] == expected[k] for k in expected), 'fresh_install_claim_required')
    lineage = claim['continuation']
    require(isinstance(lineage, dict) and set(lineage) ==
            {'original_claim_sha256', 'original_input_sha256', 'authorization_sha256'},
            'continued_claim_lineage_required')
    raw = immutable_bytes(home / HISTORY['claim'])
    old_input = immutable_bytes(home / HISTORY['input'])
    auth = immutable_bytes(home / HISTORY['authorization'])
    require(digest(raw) == lineage['original_claim_sha256']
            and digest(old_input) == lineage['original_input_sha256'], 'continued_history_changed')
    original = continuation_evidence(value, input_hash, auth, lineage['authorization_sha256'], raw, old_input)
    require(original['deadline_mono'] == budget.deadline and original['boot_id'] == claim['boot_id'],
            'continued_original_clock_changed')
    return claim


def preserve_bytes(path, raw, budget):
    budget.check()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(fd, 'wb') as stream:
        budget.call(stream.write, raw); budget.call(stream.flush); budget.call(os.fsync, stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: budget.call(os.fsync, fd)
    finally: os.close(fd)


def continue_install(value, input_path, authorization_path, authorization_hash, original_input_path, *, started):
    """Only exact independently admitted, empty pre-compose FIRST continuation.

    No generic recovery: interrupted transition/history or any retained work or
    stop record requires independent reconciliation and cannot replay here.
    """
    from scripts.install_containment import Budget, Containment
    home = canonical(value['home']); directory(home)
    fd = os.open(home / MARKER, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise Refused('continuation_writer_busy') from None
        raw = owned_file(home / MARKER, private=True)
        claim = json.loads(raw, object_pairs_hook=unique)
        require(isinstance(claim, dict) and type(claim.get('deadline_mono')) in (int, float), 'original_install_deadline_required')
        budget = Budget(value.get('seconds'), started=started, deadline=claim['deadline_mono'])
        input_raw = budget.call(owned_file, input_path, private=True)
        require(json.loads(input_raw, object_pairs_hook=unique) == value, 'install_input_changed')
        auth = budget.call(immutable_bytes, authorization_path)
        old_input = budget.call(immutable_bytes, original_input_path)
        original = budget.call(continuation_evidence, value, digest(input_raw), auth,
                               authorization_hash, raw, old_input)
        require(list(sorted(p.name for p in home.iterdir())) == [MARKER],
                'precompose_home_not_pristine')
        home, donors = budget.call(spec_checked, value)
        argv = budget.call(commands, value)
        containment = Containment(value['containment'], budget, clean_environment(home))
        # Capability failure still leaves the original marker untouched.
        containment.probe(value['bootstrap_python']['path'], ROOT)
        require(os.fstat(fd).st_ino == (home / MARKER).stat().st_ino
                and owned_file(home / MARKER, private=True) == raw,
                'original_claim_changed_before_transition')
        budget.call(continuation_evidence, value, digest(input_raw), auth,
                    authorization_hash, raw, old_input)
        require(sorted(p.name for p in home.iterdir()) == [MARKER], 'precompose_home_not_pristine')
        require(budget.call(owned_file, input_path, private=True) == input_raw, 'install_input_changed')
        budget.call(spec_checked, value)
        for key, data in [('claim', raw), ('input', old_input), ('authorization', auth)]:
            preserve_bytes(home / HISTORY[key], data, budget)
        retained_names = sorted([MARKER, *HISTORY.values()])
        require(sorted(p.name for p in home.iterdir()) == retained_names,
                'precompose_home_changed_during_transition')
        continued = partial_claim(digest(input_raw), budget)
        continued['continuation'] = {'original_claim_sha256': digest(raw),
                                    'original_input_sha256': digest(old_input),
                                    'authorization_sha256': authorization_hash}
        pending = home / (MARKER + '.continued')
        publish(pending, continued, budget=budget)
        require(owned_file(home / MARKER, private=True) == raw, 'original_claim_changed_before_transition')
        require(sorted(p.name for p in home.iterdir()) == sorted([*retained_names, pending.name]),
                'precompose_home_changed_during_transition')
        budget.call(os.replace, pending, home / MARKER)
        sync = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
        try: budget.call(os.fsync, sync)
        finally: os.close(sync)
        budget.call(active_claim_checked, value, digest(input_raw), budget)
        require(sorted(p.name for p in home.iterdir()) == retained_names,
                'precompose_home_changed_during_transition')
        return _install_claimed(value, input_path, home, donors, argv, containment, budget, continued), budget
    finally:
        os.close(fd)


def install(value, input_path, *, budget=None):
    """One original clock includes intake, execution, IO and final admission."""
    from scripts.install_containment import Budget, Containment
    require(isinstance(value, dict), 'explicit_install_fields_required')
    budget = budget or Budget(value.get('seconds'))
    home, donors = budget.call(spec_checked, value)
    argv = budget.call(commands, value)
    raw = budget.call(owned_file, input_path, private=True)
    require(json.loads(raw, object_pairs_hook=unique) == value, 'install_input_changed')
    input_hash = digest(raw); budget.check()
    if home.exists():
        budget.call(directory, home)
        marker = budget.call(read_json, home / MARKER)
        require(marker.get('schema') == SCHEMA and marker.get('input_sha256') == input_hash,
                'foreign_existing_install_not_adopted')
        require(marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE',
                'partial_install_requires_reconciliation')
        return budget.call(inspect, value, input_hash)
    containment = Containment(value['containment'], budget, clean_environment(home))
    # Actual required namespace capability before claiming/writing any home.
    try:
        containment.probe(value['bootstrap_python']['path'], ROOT)
    except (OSError, ValueError, RuntimeError) as exc:
        exc.friday_diagnostic = safe_diagnostic(exc, 'namespace_probe')
        raise
    budget.call(home.mkdir, mode=0o700)
    claim = partial_claim(input_hash, budget)
    publish(home / MARKER, claim, budget=budget)
    return _install_claimed(value, input_path, home, donors, argv, containment, budget, claim)


def _install_claimed(value, input_path, home, donors, argv, containment, budget, claim):
    input_hash = claim['input_sha256']
    def execute(phase, command, cwd, timeout=1800):
        try:
            return containment.run(command, cwd, timeout=timeout)[0]
        except (OSError, ValueError, RuntimeError) as exc:
            diagnostic = safe_diagnostic(exc, phase)
            exc.friday_diagnostic = diagnostic
            exc.friday_attempt = claim
            # This receipt is evidence, never permission to replay the attempt.
            failure = {'schema': 'friday.native-install-failure.v1',
                       'original_attempt': claim, 'diagnostic': diagnostic,
                       'resume_allowed': False}
            try:
                require(read_json(home / MARKER) == claim, 'install_claim_changed')
                publish(home / FAILURE, failure, budget=budget)
            except (OSError, ValueError, RuntimeError):
                diagnostic['failure_receipt'] = 'NOT_PUBLISHED'
            raise
    execute('compose', argv['compose'], ROOT, 130)
    source = home / 'hermes-agent'; receipt_path = home / 'hermes-agent.source.json'
    receipt = budget.call(read_json, receipt_path)
    budget.call(composition_checked, value, source, receipt, donors['hermes'])
    for phase in ('tools', 'dependencies'):
        execute(phase, argv[phase], source)
    expression = 'from pm.environments import project_python; from pathlib import Path; print(project_python(Path.cwd()))'
    selected = execute('pm_python', [value['bootstrap_python']['path'], '-B', '-c', expression], source, 15)
    require(Path(selected).is_absolute() and Path(selected).is_file(), 'native_pm_python_missing')
    execute('native_completion', [selected, '-B', str(ROOT / 'scripts/friday_native.py'), 'install',
             '--input', str(input_path), '--deadline', str(budget.deadline)], source)
    for phase, command in zip(('source', 'toolchain', 'build', 'smoke'), argv['harness']):
        execute('harness_' + phase, command, ROOT)
    if value['product']['web']['profile'] == 'exa-keyless':
        budget.call(stage_keyless_provider, Path(value['dsh_donor']))
    execute('a0_inventory', argv['a0_inventory'], ROOT, 120)
    budget.call(composition_checked, value, source, receipt, donors['hermes'])
    marker = {'schema': SCHEMA, 'state': 'INSTALLED_TEMPLATE_INCOMPLETE',
              'input_sha256': input_hash, 'source_receipt_sha256': digest(budget.call(owned_file, receipt_path)),
              'home': str(home), 'source': str(source), 'runtime_ready': False,
              'gateway_installed': False, 'remaining': gaps(),
              'original_attempt': claim,
              'invocation_completion': 'NOT_PROVEN_BY_OUTPUT_RECEIPT'}
    if 'tls' in value['product']['dashboard']:
        marker['tls_files'] = {path: digest(budget.call(owned_file, home / path, private=True))
            for path in value['product']['dashboard']['tls'].values()}
        require(marker['tls_files'] == {path: value['dashboard_tls'][key]['sha256']
            for key, path in value['product']['dashboard']['tls'].items()}, 'installed_dashboard_tls_changed')
    marker['profile_files'] = {name: digest(budget.call(owned_file, home / name, private=True))
                               for name in ('config.yaml', 'SOUL.md', 'FRIDAY-PROFILE.json')}
    marker['plugin_files'] = {name: sha for name, sha in value['project_files'].items()
                              if name.startswith('plugins/friday_rework/')}
    pending = home / (MARKER + '.completed')
    publish(pending, marker, budget=budget)
    require(budget.call(read_json, home / MARKER) == claim, 'install_claim_changed')
    budget.call(os.replace, pending, home / MARKER)
    budget.check()
    fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
    try:
        budget.check()
        budget.call(os.fsync, fd)
    finally:
        os.close(fd)
    budget.check()
    return marker


def gaps():
    return ['A0 portable image/toolchain preparation is absent; fixed deployment needs separately admitted kernel/resources',
            'Both-worker configuration is available; A0 useful-web runtime admission and mixed live execution remain unverified',
            'Native Dashboard boundary requires independent source review and actual authenticated startup/attach acceptance',
            'Protected credential provisioning, actual account ownership, PM/build realization and all seven live journeys require independent acceptance']


def inspect(value, input_hash):
    home, donors = spec_checked(value); directory(home)
    marker = read_json(home / MARKER)
    require(marker.get('schema') == SCHEMA and marker.get('home') == str(home)
            and marker.get('input_sha256') == input_hash
            and marker.get('state') == 'INSTALLED_TEMPLATE_INCOMPLETE', 'foreign_or_partial_install')
    if 'tls' in value['product']['dashboard']:
        expected = {path: value['dashboard_tls'][key]['sha256']
            for key, path in value['product']['dashboard']['tls'].items()}
        require(marker.get('tls_files') == expected
                and all(digest(owned_file(home / path, private=True)) == pin for path, pin in expected.items()),
                'installed_dashboard_tls_changed')
    receipt_path = home / 'hermes-agent.source.json'
    require(digest(owned_file(receipt_path)) == marker.get('source_receipt_sha256'),
            'source_receipt_changed')
    composition_checked(value, home / 'hermes-agent', read_json(receipt_path), donors['hermes'])
    profile_files = marker.get('profile_files')
    require(isinstance(profile_files, dict)
            and set(profile_files) == {'config.yaml', 'SOUL.md', 'FRIDAY-PROFILE.json'},
            'installed_profile_inventory_missing')
    for name, sha in profile_files.items():
        require(digest(owned_file(home / name, private=True)) == sha, 'installed_profile_changed')
    expected_plugins = {name: sha for name, sha in value['project_files'].items()
                        if name.startswith('plugins/friday_rework/')}
    require(marker.get('plugin_files') == expected_plugins, 'installed_plugin_inventory_changed')
    for name, sha in expected_plugins.items():
        require(digest(owned_file(home / name, private=True)) == sha, 'installed_plugin_changed')
    return {'state': 'TEMPLATE_INCOMPLETE', 'ready': False, 'home': str(home),
            'effects': 'NONE', 'remaining': gaps(),
            'invocation_completion': 'NOT_PROVEN_BY_OUTPUT_RECEIPT'}


def start(value, input_hash, *, budget=None, input_path=None):
    from scripts.install_containment import Budget, Containment
    budget = budget or Budget(value.get('seconds'))
    budget.call(inspect, value, input_hash)
    # A source/rendered status cannot stand in for any configured runtime.
    require(value['product']['runtime'].get('enabled') is True,
            'mandatory_a0_web_kernel_and_final_native_dashboard_owner_not_admitted')
    require(input_path is not None, 'original_start_input_required')
    require(digest(budget.call(owned_file, input_path, private=True)) == input_hash,
            'original_start_input_changed')
    home = Path(value['home']); source = home / 'hermes-agent'
    custody = Containment(value['containment'], budget, clean_environment(home))
    expression = 'from pm.environments import project_python; from pathlib import Path; print(project_python(Path.cwd()))'
    selected = custody.run([value['bootstrap_python']['path'], '-B', '-c', expression], source, timeout=15)[0]
    require(Path(selected).is_absolute() and Path(selected).is_file(), 'native_pm_python_missing')
    # Re-exec the existing internal completion helper in the exact selected PM
    # generation. It revalidates all bytes and gates before any service effect.
    budget.call(inspect, value, input_hash)
    argv = [selected, '-B', str(ROOT / 'scripts/friday_native.py'), 'start',
            '--input', str(input_path), '--deadline', str(budget.deadline)]
    budget.check()
    os.execve(selected, argv, clean_environment(home))


def main():
    started = time.monotonic()  # before parser/input IO; never reset on dispatch
    parser = SafeParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('phase', choices=('plan', 'install', 'continue', 'check', 'dashboard-check', 'start', 'reconcile'))
    parser.add_argument('--input', required=True, type=Path, help='Private pinned JSON, no credential values')
    parser.add_argument('--continuation', type=Path, help='Immutable independently reviewed operator authorization')
    parser.add_argument('--continuation-sha256', help='Out-of-band operator pin for the exact authorization')
    parser.add_argument('--original-input', type=Path, help='Immutable exact original input bytes')
    args = parser.parse_args(); os.umask(0o077)
    sys.path.insert(0, str(ROOT))
    from scripts.dsh_prepare import StopUnconfirmed
    try:
        raw = owned_file(args.input, private=True)
        value = json.loads(raw, object_pairs_hook=unique); sha = digest(raw)
        from scripts.install_containment import Budget
        require(isinstance(value, dict), 'explicit_install_fields_required')
        require((args.phase == 'continue' and args.continuation is not None
                 and args.original_input is not None and args.continuation_sha256 is not None
                 and re.fullmatch('[0-9a-f]{64}', args.continuation_sha256))
                or (args.phase != 'continue' and args.continuation is None
                    and args.original_input is None and args.continuation_sha256 is None),
                'explicit_continuation_arguments_required')
        if args.phase == 'continue':
            result, budget = continue_install(value, args.input, args.continuation,
                                             args.continuation_sha256, args.original_input, started=started)
        else:
            budget = Budget(value.get('seconds'), started=started)
            budget.check()
        if args.phase == 'continue':
            pass
        elif args.phase == 'reconcile':
            result = reconcile(value, sha)
        elif args.phase == 'plan':
            result = {'state': 'PLANNED_NOT_EXECUTED', 'ready': False,
                      'commands': commands(value), 'remaining': gaps()}
        elif args.phase == 'install':
            result = install(value, args.input, budget=budget)
        elif args.phase == 'check':
            result = inspect(value, sha)
        elif args.phase == 'dashboard-check':
            inspect(value, sha)
            from scripts.friday_native import dashboard_source_check
            result = dashboard_source_check(Path(value['home']))
        else:
            result = start(value, sha, budget=budget, input_path=args.input)
        payload = json.dumps(result, sort_keys=True, indent=2)
        budget.check()
        print(payload, flush=True)
        budget.check()
    except StopUnconfirmed as exc:
        # Fixed text only: neither argv, stderr nor a chained error is safe to
        # print. Keep uncertain process custody distinct from a normal refusal.
        detail = diagnostic_text(getattr(exc, 'friday_diagnostic', safe_diagnostic(exc, args.phase)))
        if hasattr(exc, 'friday_attempt'): detail += ' attempt=' + exc.friday_attempt['input_sha256']
        parser.exit(3, 'STOP_UNCONFIRMED: ' + detail + '; owned command cessation is unconfirmed; '
                       'do not retry or release ownership before reconciliation\n')
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        # Native errors/inputs can contain credentials: print no exception body.
        detail = diagnostic_text(getattr(exc, 'friday_diagnostic', safe_diagnostic(exc, args.phase)))
        if hasattr(exc, 'friday_attempt'): detail += ' attempt=' + exc.friday_attempt['input_sha256']
        parser.exit(2, 'Friday entry refused: ' + detail + '\n')



def stage_keyless_provider(harness):
    """After intact donor build/smoke; exact extra product source, no ready grant."""
    raw = owned_file(ROOT / "plugins/friday_rework/adapters/dsh_keyless_web.mjs")
    target = harness / "friday-web-keyless.mjs"
    require(target.parent.resolve() == target.parent and not target.exists() and not target.is_symlink(), "existing_keyless_provider_not_replaced")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(fd, "wb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return {"path": str(target), "sha256": digest(raw), "runtime_ready": False}

if __name__ == '__main__':
    main()
