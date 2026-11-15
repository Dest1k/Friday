"""Finite Root-only caller SOURCE. Import/default/--inspect launch nothing.

The protected, externally hash-bound Root authority files are authorization
INPUTS, not self-authenticating facts. Only Root may construct/use them. Sol's
source rehearsal calls execute_once/namespace_entry.run ONLY with explicit inert
leaves; the real SystemdBackend/LocalServices effects are never used by Sol.
All subprocess argv are arrays; no shell, attach, generic kill, retry or services
outside the one freshly named operation unit are available here.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import re
import resource
import stat
import subprocess
import time
import types
from urllib.parse import unquote, urlparse

SCHEMA = 'frw.calc.outer-plan.v1'
WORK = '/tmp/friday-metric-work'
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
SLOT = '/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock'
CACHE = Path('/home/jericho/.cache')
EFFECT = 'ONE_PRIVATE_READONLY_CALC_LOAD_FONT_QUERY_NATIVE_TRACE'
SOURCE_ROLES = {'calc_document', 'calc_xlsx_filter', 'vcl', 'toolkit', 'sal', 'font_config_view'}
CONTROLLER_MEMORY_RESERVE_BYTES = 256 * 1024**2
SOURCE_SHA256 = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
SOURCE_BYTES = 16538


def unit_memory_limit(budget):
    return budget['memory_bytes'] - CONTROLLER_MEMORY_RESERVE_BYTES


class Refused(RuntimeError):
    pass


def need(value, code):
    if not value:
        raise Refused(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def exact_path(value):
    need(type(value) is str and value.startswith('/') and '\0' not in value,
         'absolute_path_required')
    path = Path(value)
    need('..' not in path.parts and str(path) == value, 'canonical_path_required')
    return path


def directory(path, *, private=False):
    path = exact_path(str(path))
    for item in [*reversed(path.parents), path]:
        st = item.lstat()
        need(stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode), 'directory_alias')
        need(st.st_uid in (0, os.getuid()) and not st.st_mode & 0o022,
             'directory_ownership_or_write_rights')
    if private:
        st = path.stat()
        need(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == 0o700,
             'private_0700_directory_required')
    return path


def read_pinned(ref, *, private=False, with_stat=False):
    need(type(ref) is dict and set(ref) == {'path', 'sha256'} and sha(ref['sha256']), 'file_ref')
    path = exact_path(ref['path'])
    directory(path.parent)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022,
             'protected_singlelink_file_required')
        if private:
            need(before.st_uid == os.getuid() and not before.st_mode & 0o077,
                 'owner_only_file_required')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read()
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
              before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size,
              after.st_mtime_ns, after.st_ctime_ns), 'file_changed_during_read')
        need(digest(raw) == ref['sha256'], 'file_pin_changed')
        return (raw, before) if with_stat else raw
    finally:
        os.close(fd)


def load_module(name, ref):
    raw = read_pinned(ref)
    module = types.ModuleType(name)
    module.__file__ = ref['path']
    exec(compile(raw, ref['path'], 'exec'), module.__dict__)
    return module


def atomic_json(path, value, *, exclusive=False):
    path = Path(path)
    raw = canonical(value)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    temp = path if exclusive else path.with_name(path.name + '.pending')
    fd = os.open(temp, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        if not exclusive:
            os.replace(temp, path)
    finally:
        if temp != path and temp.exists():
            temp.unlink()
    return {'path': str(path), 'sha256': digest(raw)}


def validate_budget(b):
    need(type(b) is dict and set(b) == {'wall_seconds', 'cpu_seconds', 'memory_bytes',
         'cleanup_seconds', 'startup_seconds', 'tasks_max'}, 'budget_schema')
    need(all(type(v) is int for v in b.values()), 'integer_budgets')
    need(30 <= b['wall_seconds'] <= 240 and b['cleanup_seconds'] + 2 < b['cpu_seconds'] <= 120
         and CONTROLLER_MEMORY_RESERVE_BYTES + 64 * 1024**2 <= b['memory_bytes'] <= 2 * 1024**3
         and 5 <= b['cleanup_seconds'] <= 20 and 1 <= b['startup_seconds'] <= 60
         and b['startup_seconds'] + b['cleanup_seconds'] < b['wall_seconds']
         and 8 <= b['tasks_max'] <= 128, 'finite_budget_bounds')
    return b


def observe_sources(plan, pre):
    """Authenticate both actual files, not just self-advertised fresh hashes."""
    need(pre['source'] == {'sha256': SOURCE_SHA256, 'bytes': SOURCE_BYTES}, 'exact_original_source_basis')
    refs = plan['source_files']
    need(type(refs) is list and len(refs) == 2 and len({r['path'] for r in refs}) == 2,
         'exact_two_distinct_original_and_working_source_refs')
    copy = pre['working_copy']
    u = urlparse(copy['url'])
    need(u.scheme == 'file' and not u.netloc and not u.query and not u.fragment,
         'exact_working_source_file_URL')
    working = str(exact_path(unquote(u.path)))
    need(sum(r['path'] == working for r in refs) == 1, 'working_URL_ref_mismatch')
    need(copy['sha256_before'] == SOURCE_SHA256 and type(copy['bytes']) is int
         and copy['bytes'] == SOURCE_BYTES and copy['mode'] in ('0400', '0600')
         and type(copy['uid']) is int and copy['uid'] == os.getuid()
         and type(copy['nlink']) is int and copy['nlink'] == 1, 'source_copy_claim_mismatch')
    observations = []
    for ref in refs:
        need(ref['sha256'] == SOURCE_SHA256, 'source_pin_not_canonical_original')
        raw, st = read_pinned(ref, private=True, with_stat=True)
        need(len(raw) == SOURCE_BYTES and st.st_size == SOURCE_BYTES and st.st_uid == os.getuid(),
             'actual_source_size_or_owner_mismatch')
        if ref['path'] == working:
            need(stat.S_IMODE(st.st_mode) == int(copy['mode'], 8) and st.st_uid == copy['uid']
                 and st.st_nlink == copy['nlink'], 'actual_working_source_rights_mismatch')
        observations.append({'path': ref['path'], 'sha256': digest(raw), 'bytes': len(raw),
            'device': st.st_dev, 'inode': st.st_ino, 'uid': st.st_uid,
            'mode': format(stat.S_IMODE(st.st_mode), '04o'), 'nlink': st.st_nlink,
            'mtime_ns': st.st_mtime_ns, 'ctime_ns': st.st_ctime_ns})
    need(len({(o['device'], o['inode']) for o in observations}) == 2, 'source_original_copy_inode_alias')
    return observations


def inspect_load_dependency(plan, readonly):
    observer, base = plan['observer'], plan['inner_input']
    binding = observer.get('load_dependency')
    if binding is None:
        need('load_dependency' not in base, 'helper_inner_without_outer_binding')
        return None
    need(type(binding) is dict and set(binding) == {'manifest', 'policy', 'adapter'}, 'helper_outer_binding_schema')
    for ref in binding.values():
        read_pinned(ref)
        need(any(Path(ref['path']).is_relative_to(p) for p in readonly), 'helper_source_not_readonly_mounted')
    need(binding['manifest']['sha256'] == '92b94f4100609c820f25891e09ec15267802833fb4665c393ff746c4565691d0',
         'exact_reviewed_Office_helper_manifest')
    manifest = json.loads(read_pinned(binding['manifest']))
    policy = load_module('frw_Root_static_helper_policy', binding['policy'])
    policy.validate_manifest(manifest)
    runtime = base.get('load_dependency')
    policy.validate_runtime(runtime, manifest, prelaunch=True)
    need(runtime['operation_deadline_monotonic'] is None and runtime['nonce'] == plan['nonce']
         and runtime['operation_id'] == plan['operation_id'] and runtime['manifest_ref'] == binding['manifest']
         and runtime['source_sha256'] == SOURCE_SHA256, 'helper_outer_runtime_binding')
    need(manifest['caller']['path'] == observer['config']['symbol_file_path']
         and manifest['caller']['sha256'] == observer['config']['symbol_file_sha256'], 'helper_same_LO_caller_image')
    return manifest


def inspect_plan(plan):
    """Read/verify prepared bytes/rights only. Never grants runtime authority."""
    need(type(plan) is dict and set(plan) == {'schema', 'operation_id', 'nonce', 'operation_dir',
         'work_dir', 'readonly_dirs', 'binding_root', 'namespace_builder', 'namespace_entry',
         'inner_client', 'inner_input', 'preload', 'component_paths', 'source_files', 'tools',
         'observer', 'budgets', 'startup_basis', 'font_view', 'bootstrap'}, 'outer_plan_schema')
    need(plan['schema'] == SCHEMA and type(plan['operation_id']) is str
         and re.fullmatch('[a-zA-Z0-9_.-]{1,128}', plan['operation_id'])
         and type(plan['nonce']) is str and re.fullmatch('[0-9a-f]{32}', plan['nonce']),
         'operation_identity_UNBOUND')
    b = validate_budget(plan['budgets'])
    opdir = directory(plan['operation_dir'], private=True)
    work = directory(plan['work_dir'], private=True)
    need(opdir.is_relative_to(CACHE) and work.parent == opdir and work.name == 'work',
         'separate_exact_private_operation_work')
    need(not list(work.iterdir()), 'work_must_be_prepared_empty')
    need(not (opdir / 'consumed-once.json').exists(), 'operation_already_consumed')
    directory(plan['binding_root'])
    readonly = [directory(p) for p in plan['readonly_dirs']]
    need(len(set(readonly)) == len(readonly), 'duplicate_readonly_mount')
    for name in ('namespace_builder', 'namespace_entry', 'inner_client', 'preload', 'startup_basis'):
        read_pinned(plan[name])
        if name != 'namespace_builder':
            need(any(Path(plan[name]['path']).is_relative_to(p) for p in readonly),
                 'code_or_metadata_not_readonly_mounted:' + name)
    need(type(plan['component_paths']) is dict and set(plan['component_paths']) == SOURCE_ROLES,
         'actual_component_role_paths')
    tools = plan['tools']
    expected = {'python': '/usr/bin/python3', 'gdb': '/usr/bin/gdb', 'bwrap': '/usr/bin/bwrap',
                'systemd_run': '/usr/bin/systemd-run', 'systemctl': '/usr/bin/systemctl'}
    need(type(tools) is dict and set(tools) == set(expected), 'exact_tool_roles')
    for name, target in expected.items():
        # Distribution symlinks (python3) are resolved explicitly in the ref;
        # actual argv must still name the standard selected invocation.
        need(Path(target).resolve() == Path(tools[name]['path']), 'selected_tool_path:' + name)
        read_pinned(tools[name])
    observer = plan['observer']
    need(type(observer) is dict and set(observer) in ({'hook', 'checker', 'contract', 'config'},
         {'hook', 'checker', 'contract', 'config', 'load_dependency'}),
         'observer_binding_schema')
    for role in ('hook', 'checker', 'contract'):
        read_pinned(observer[role])
        need(any(Path(observer[role]['path']).is_relative_to(p) for p in readonly),
             'observer_source_not_readonly_mounted')
    cfg = observer['config']
    template = json.loads(read_pinned({'path': str(Path(__file__).parent / 'deps' /
        'FUTURE-OFFICE-CONFIG-TEMPLATE.json'),
        'sha256': 'b23035aa4b4fa86c31e69dde78eab0f072ed9878e615b153bfc81d3aebdc7524'}))
    mutable_config = {'nonce', 'target_path', 'symbol_file_path', 'phase_path', 'trace_path'}
    need(set(cfg) == set(template) and all(cfg[k] == template[k] for k in set(template) - mutable_config),
         'exact_reviewed_native_observer_config_required')
    need(cfg['kind'] == 'OFFICE_UNADMITTED' and cfg['nonce'] == plan['nonce']
         and cfg['target_path'] == PROGRAM + '/soffice.bin'
         and cfg['symbol_file_path'] == PROGRAM + '/libmergedlo.so'
         and cfg['phase_path'] == WORK + '/phase.json'
         and cfg['trace_path'] == WORK + '/native-trace.json', 'namespace_observer_paths')
    need(sha(cfg['target_sha256']) and sha(cfg['symbol_file_sha256']), 'target_symbol_pins')
    pre = json.loads(read_pinned(plan['preload']))
    need(pre['operation_id'] == plan['operation_id'], 'same_preload_operation')
    source_observations = observe_sources(plan, pre)
    font = plan['font_view']
    need(type(font) is dict and set(font) == {'consumer', 'baseline', 'expected_view_sha256', 'provenance_ref', 'base_view_sha256', 'derived_cache'}
         and sha(font['expected_view_sha256']), 'Root_font_view_input_UNBOUND')
    baseline_raw = None
    for ref in (font['consumer'], font['baseline'], font['provenance_ref']):
        raw = read_pinned(ref, private=True)
        if ref == font['baseline']:
            baseline_raw = raw
        need(any(Path(ref['path']).is_relative_to(p) for p in readonly), 'font_CAS_input_not_readonly_mounted')
    need(len(baseline_raw) <= 4 * 1024**2, 'font_baseline_output_bound')
    baseline = json.loads(baseline_raw)
    consumer = load_module('frw_static_font_CAS_preparation_only', font['consumer'])
    try:
        consumer.checked_baseline(baseline, font['base_view_sha256'])
        derived = json.loads(read_pinned(font['derived_cache'], private=True))
        need(any(Path(font['derived_cache']['path']).is_relative_to(p) for p in readonly),
             'derived_cache_manifest_not_readonly_mounted')
        need(any(Path(derived['closed_origin']['path']).is_relative_to(p) for p in readonly),
             'derived_closed_origin_not_readonly_mounted')
        need(not Path(derived['source_directory']).is_relative_to(work)
             and not work.is_relative_to(derived['source_directory']), 'derived_cache_work_overlap')
        consumer.observe_derived_cache(derived, baseline)  # Only six actual input files, not a font inventory.
        need(consumer.digest(consumer.effective_expected_view(baseline, derived)) == font['expected_view_sha256'],
             'effective_font_view_UNBOUND')
    except Exception:
        raise Refused('Root_font_view_canonical_baseline_UNBOUND')
    provenance = json.loads(read_pinned(font['provenance_ref'], private=True))
    need(provenance['schema'] == 'frw.Astra.static-font-view-namespace-provenance.v1'
         and provenance['namespace_helper']['sha256'] == derived['base_namespace_helper_sha256']
         and derived['namespace_helper_sha256'] == plan['namespace_builder']['sha256'],
         'Root_font_view_namespace_source_provenance_mismatch')
    need(pre['expected_components']['font_config_view'] == font['expected_view_sha256']
         and plan['component_paths']['font_config_view'] == font['baseline']['path'],
         'font_role_requires_canonical_view_digest_and_real_baseline_descriptor_path')
    base = plan['inner_input']
    need(base['operation_id'] == plan['operation_id'] and base['nonce'] == plan['nonce']
         and base['preload'] == plan['preload'] and base['handler_source_ref'] == plan['inner_client'],
         'same_inner_operation_source')
    need(base['office_process'] is None, 'no_fabricated_prelaunch_process')
    need('load_dependency' in observer, 'current_font_runtime_getter_requires_pinned_helper_bundle')
    inspect_load_dependency(plan, readonly)
    need(base['paths'] == {'work': WORK, 'phase': WORK + '/phase.json', 'trace': WORK + '/native-trace.json',
         'checkpoint': WORK + '/inner-checkpoint.json', 'loaded_envelope': WORK + '/loaded-envelope.json',
         'started': WORK + '/inner-started.json'}, 'exact_same_phase_trace_barrier_paths')
    ro_mounts = readonly + [Path(plan['binding_root'])]
    working_path = unquote(urlparse(pre['working_copy']['url']).path)
    working_refs = [r for r in plan['source_files'] if r['path'] == working_path]
    need(len(working_refs) == 1, 'exact_working_source_pin_required')
    for ref in [*base['modules'].values(), *base['uno']['files'], *working_refs]:
        need(any(Path(ref['path']).is_relative_to(p) for p in ro_mounts),
             'exact_dependency_not_readonly_mounted')
    # Inner's real inspect routine prevalidates the supplied actual0400-compatible
    # qualifier. The only deliberately missing input here is future Office PID.
    client = load_module('frw_inner_source_inspect', plan['inner_client'])
    inspect = getattr(client, 'inspect_prelaunch', None)
    need(callable(inspect), 'inner_prelaunch_inspection_API_required')
    inspect(base)
    builder = load_module('frw_root_namespace_builder', plan['namespace_builder'])
    bootstrap = plan['bootstrap']
    need(type(bootstrap) is dict and set(bootstrap) == {'basis', 'versionrc'}, 'bootstrap_binding_schema')
    basis = json.loads(read_pinned(bootstrap['basis'], private=True))
    need(any(Path(bootstrap['basis']['path']).is_relative_to(p) for p in readonly), 'bootstrap_basis_not_readonly_mounted')
    need(basis['schema'] == 'frw.calc.fresh-profile-bootstrap-basis.v1'
         and basis['stock_commit'] == 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
         and basis['sequence'] == ['FRESH_ORDINARY_REQUIRE_81', 'SAME_PROFILE_TERMINATE_AFTER_INIT_REQUIRE_0']
         and basis['max_children'] == 2, 'exact_source_bootstrap_sequence_required')
    need(bootstrap['versionrc']['path'] == str(builder.TOOLCHAIN / 'root/usr/lib/libreoffice/program/versionrc'),
         'stock_versionrc_path_required')
    version_raw = read_pinned(bootstrap['versionrc'])
    need(len(version_raw) <= 65536, 'stock_versionrc_bound')
    argv = builder.build_namespace(writable=work, readonly=readonly, derived_cache=derived['source_directory'],
        binding_root=plan['binding_root'], command=['/usr/bin/python3', '-I', '-B', '-S',
        plan['namespace_entry']['path'], '--job', WORK + '/namespace-job.json'])
    need('--unshare-all' in argv and '--clearenv' in argv and '--die-with-parent' in argv
         and ['--setenv', 'LC_ALL', 'C.UTF-8'] == argv[argv.index('LC_ALL')-1:argv.index('LC_ALL')+2],
         'required_network_pid_mount_environment_boundary')
    return {'schema': 'frw.calc.outer-inspection.v1', 'operation_id': plan['operation_id'],
            'status': 'SOURCE_INPUTS_INSPECTED_NO_GRANT', 'namespace_argv': argv,
            'budgets': b, 'source_observations': source_observations,
            'actual_M': None, 'runtime_attested': False, 'runtime_grant': False}


def validate_authority(refs, plan_sha256, plan, *, now):
    """Fresh external Root observations/admission, independently hash-bound.

    No serialized boolean can create authority. These three records are the
    explicit Root call boundary; the caller must independently know their origin.
    Readiness describes reviewed source/prepared inputs, never future runtime PASS.
    """
    need(type(refs) is dict and set(refs) == {'current', 'readiness', 'admission'}, 'authority_refs')
    records = {}
    decisions = {'current': 'CURRENT_EXACT_ROOT_PARAMETERS',
                 'readiness': 'SOURCE_REVIEWED_READY_FOR_SEPARATE_ADMISSION',
                 'admission': 'ADMIT_EXACT_OPERATION_ONCE'}
    for kind in ('current', 'readiness', 'admission'):
        record = json.loads(read_pinned(refs[kind], private=True))
        need(set(record) == {'schema', 'operation_id', 'nonce', 'plan_sha256', 'issuer_scope',
             'decision', 'effect', 'issued_unix', 'expires_unix', 'evidence_refs'}, 'authority_schema')
        need(record['schema'] == 'frw.calc.Root.' + kind + '.v1'
             and record['operation_id'] == plan['operation_id'] and record['nonce'] == plan['nonce']
             and record['plan_sha256'] == plan_sha256 and record['issuer_scope'] == 'Root'
             and record['decision'] == decisions[kind] and record['effect'] == EFFECT,
             'authority_binding:' + kind)
        need(type(record['issued_unix']) is int and type(record['expires_unix']) is int
             and record['issued_unix'] <= now <= record['expires_unix']
             and 0 < record['expires_unix'] - record['issued_unix'] <= 300
             and now - record['issued_unix'] <= 120, 'stale_Root_authority:' + kind)
        need(type(record['evidence_refs']) is list and record['evidence_refs'], 'Root_evidence_refs_required')
        for ref in record['evidence_refs']:
            read_pinned(ref)
        records[kind] = record
    need(records['admission']['expires_unix'] > now + 1, 'admission_expiring')
    return records


def proc_identity(pid):
    """Current host/namespace PID birth and mapping, no process mutation."""
    need(type(pid) is int and pid > 0, 'positive_pid_required')
    root = Path('/proc') / str(pid)
    raw = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    status = (root / 'status').read_text().splitlines()
    nspids = next((list(map(int, s.split()[1:])) for s in status if s.startswith('NSpid:')), [])
    result = {'pid': pid, 'ppid': int(raw[1]), 'start_ticks': int(raw[19]),
              'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'nspid': nspids, 'executable': os.readlink(root / 'exe'),
              'namespaces': {n: os.readlink(root / 'ns' / n) for n in ('pid', 'mnt', 'net', 'user')},
              'cgroup': (root / 'cgroup').read_text().strip()}
    need(int((root / 'stat').read_text().rsplit(')', 1)[1].split()[19]) == result['start_ticks'],
         'PID_birth_changed')
    return result


def bind_symbols_from_maps(maps_text, config):
    """Pure join of externally read real mappings to pinned ELF offsets."""
    mappings = []
    for line in maps_text.splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) == 6 and parts[5] == config['symbol_file_path']:
            lo, hi = (int(x, 16) for x in parts[0].split('-'))
            mappings.append((lo, hi, parts[1], int(parts[2], 16)))
    bases = [lo for lo, _, _, offset in mappings if offset == 0]
    need(len(bases) == 1, 'actual_mapped_symbol_image_base_missing_or_ambiguous')
    base = bases[0]
    symbols = {'outer': base + config['outer_offset'], 'native': base + config['native_offset'],
               'native_return': base + config['outer_offset'] + config['return_delta']}
    need(all(any(lo <= address < hi and 'x' in perms for lo, hi, perms, _ in mappings)
             for address in symbols.values()), 'native_symbol_addresses_not_in_actual_executable_map')
    return {'symbols': symbols, 'mapped_image_base': base,
            'mapped_image_path': config['symbol_file_path'], 'maps_sha256': digest(maps_text.encode())}


def image_file_identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)

def stream_image_digest(path):
    """Hash one stable regular image through its FD with at most 1 MiB reads."""
    fd = None
    try:
        path_before = path.stat()
        need(stat.S_ISREG(path_before.st_mode), 'actual_host_image_not_regular')
        # NONBLOCK prevents a replacement FIFO from blocking before fstat.
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK)
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode), 'actual_host_image_not_regular')
        identity = image_file_identity(before)
        need(image_file_identity(path_before) == identity, 'actual_host_image_replaced')
        hasher = hashlib.sha256()
        remaining = before.st_size
        while remaining:
            block = os.read(fd, min(1024 * 1024, remaining))
            need(block, 'actual_host_image_changed_during_hash')
            hasher.update(block)
            remaining -= len(block)
        need(not os.read(fd, 1), 'actual_host_image_changed_during_hash')
        need(image_file_identity(os.fstat(fd)) == identity
             and image_file_identity(path.stat()) == identity,
             'actual_host_image_changed_during_hash')
        return hasher.hexdigest(), before
    except OSError as exc:
        raise Refused('actual_host_image_unreadable_or_replaced') from exc
    finally:
        if fd is not None:
            os.close(fd)

def mapped_image_records(maps_text, image_path):
    records = []
    for line in maps_text.splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) == 6 and parts[5] == image_path:
            records.append(parts[:5])
    return records

def observe_native_symbols(host_pid, plan):
    """Root independent early live mapping/hash observation, before client load."""
    before = proc_identity(host_pid)
    root = Path('/proc') / str(host_pid)
    config = plan['observer']['config']
    maps_before = (root / 'maps').read_text()
    binding = bind_symbols_from_maps(maps_before, config)
    target_hash, _ = stream_image_digest(root / 'exe')
    need(target_hash == config['target_sha256'], 'actual_host_target_pin_mismatch')
    image = root / 'root' / config['symbol_file_path'].lstrip('/')
    image_hash, image_stat = stream_image_digest(image)
    need(image_hash == config['symbol_file_sha256'], 'actual_host_mapped_library_pin_mismatch')
    mappings = mapped_image_records(maps_before, config['symbol_file_path'])
    need(all(tuple(int(part, 16) for part in row[3].split(':'))
             == (os.major(image_stat.st_dev), os.minor(image_stat.st_dev))
             and int(row[4]) == image_stat.st_ino for row in mappings),
         'actual_host_mapped_library_file_identity_mismatch')
    need(mapped_image_records((root / 'maps').read_text(), config['symbol_file_path']) == mappings,
         'actual_host_mapped_library_changed_during_symbol_binding')
    need(proc_identity(host_pid) == before, 'actual_host_process_changed_during_symbol_binding')
    return dict(binding, symbol_file_sha256=config['symbol_file_sha256'],
                target_sha256=config['target_sha256'], process_identity=before)


def observe_process_resources(host_pid):
    before = proc_identity(host_pid)
    root = Path('/proc') / str(host_pid)
    fields = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    memory = {}
    for line in (root / 'status').read_text().splitlines():
        if line.startswith(('VmRSS:', 'VmHWM:')):
            key, value, unit = line.split()
            need(unit == 'kB', 'font_CAS_process_RSS_unit_unknown')
            memory[key.rstrip(':')] = int(value) * 1024
    need(set(memory) == {'VmRSS', 'VmHWM'} and proc_identity(host_pid) == before,
         'font_CAS_process_birth_or_resource_scope_changed')
    return {'process_identity': before,
            'process_CPU_seconds': (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK'),
            'current_RSS_bytes': memory['VmRSS'], 'address_space_peak_RSS_bytes': memory['VmHWM']}


def validate_font_CAS_phase(marker, plan, processes, *, expected_process, resource_reader, now, operation_started):
    """Existing finite unit sampler's per-CAS guard, never a new watcher/unit."""
    need(marker['schema'] == 'frw.calc.font-CAS-phase.v1'
         and marker['operation_id'] == plan['operation_id'] and marker['nonce'] == plan['nonce']
         and marker['phase'] in ('BEFORE_OFFICE', 'AFTER_BOOTSTRAP_BEFORE_GDB', 'AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'),
         'font_CAS_phase_binding')
    need(marker['state'] in ('RUNNING', 'COMPLETE_UNRELEASED', 'REFUSED'), 'font_CAS_phase_state')
    need(marker['state'] != 'REFUSED', 'Root_font_CAS_refused_no_release')
    if marker['state'] != 'RUNNING':
        return None
    source = marker['process']
    matches = [p for p in processes if p.get('nspid') and p['nspid'][-1] == source['namespace_pid']
               and p.get('start_ticks') == source['start_ticks'] and p.get('namespaces') == source['namespaces']
               and p.get('boot_id') == source['boot_id'] and p.get('executable') == plan['tools']['python']['path']]
    need(len(matches) == 1 and source['executable_sha256'] == plan['tools']['python']['sha256'],
         'font_CAS_marker_not_bound_to_current_owned_host_process')
    process = matches[0]
    need(process == expected_process, 'font_CAS_marker_not_the_independently_bound_namespace_supervisor')
    current = resource_reader(process['pid'])
    need(current['process_identity'] == process, 'font_CAS_resource_PID_birth_custody_changed')
    started, cpu_start = marker['started_monotonic'], marker['started_process_CPU_seconds']
    need(type(started) in (int, float) and math.isfinite(started)
         and type(cpu_start) in (int, float) and math.isfinite(cpu_start)
         and operation_started <= started <= now and 0 <= cpu_start <= current['process_CPU_seconds'],
         'font_CAS_clock_or_CPU_origin_invalid')
    reserve = plan['budgets']['cleanup_seconds']
    need(now - started <= 60 - reserve, 'font_CAS_wall_cleanup_reserve_reached')
    need(current['process_CPU_seconds'] - cpu_start <= 30 - reserve - 1,
         'font_CAS_CPU_cleanup_reserve_reached')
    need(0 <= current['current_RSS_bytes'] <= current['address_space_peak_RSS_bytes'] <= 512 * 1024**2,
         'font_CAS_current_address_space_RSS_bound_exceeded')
    return {'phase': marker['phase'], 'started_monotonic': started, 'process': process, 'resources': current}


def validate_unit_identity(snapshot, *, unit, invocation=None, cgroup=None):
    need(snapshot.get('Id') == unit and re.fullmatch('[0-9a-f]{32}', snapshot.get('InvocationID', '')),
         'owned_transient_unit_identity_missing')
    if invocation is not None:
        need(snapshot['InvocationID'] == invocation, 'unit_invocation_changed')
    current = snapshot.get('ControlGroup', '')
    if current:
        prefix = '/user.slice/user-' + str(os.getuid()) + '.slice/user@' + str(os.getuid()) + '.service/'
        need(current.startswith(prefix) and current.endswith('/' + unit)
             and '..' not in Path(current).parts, 'unexpected_owned_cgroup_path')
        if cgroup is not None:
            need(current == cgroup, 'owned_cgroup_changed')
    exited_retained = (snapshot.get('ActiveState') == 'active' and snapshot.get('SubState') == 'exited'
                       and snapshot.get('MainPID') == '0' and snapshot.get('RemainAfterExit') == 'yes')
    need(current or snapshot.get('ActiveState') in ('inactive', 'failed') or exited_retained,
         'active_cgroup_missing')
    return snapshot


class SystemdBackend:
    """Actual future finite effects, never invoked by source-only tests."""
    def command(self, argv, *, timeout=10, check=True):
        cp = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
                            check=False, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8',
                            'LC_ALL': 'C.UTF-8', 'XDG_RUNTIME_DIR': '/run/user/' + str(os.getuid()),
                            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/' + str(os.getuid()) + '/bus'})
        need(not check or cp.returncode == 0, 'systemd_command_failed')
        return cp

    def absent(self, unit):
        cp = self.command(['/usr/bin/systemctl', '--user', 'show', unit, '--property=LoadState', '--value'], check=False)
        need(cp.returncode in (0, 1, 4) and cp.stdout.strip() == b'not-found',
             'user_systemd_unavailable_or_unit_presence_unknown')

    def launch(self, unit, namespace_argv, b):
        args = ['/usr/bin/systemd-run', '--user', '--unit=' + unit, '--quiet', '--service-type=exec']
        properties = {'RuntimeMaxSec': b['wall_seconds'] - b['cleanup_seconds'], 'MemoryMax': unit_memory_limit(b),
                      'MemorySwapMax': 0, 'TasksMax': b['tasks_max'], 'KillMode': 'control-group',
                      'SendSIGKILL': 'yes', 'TimeoutStopSec': b['cleanup_seconds'],
                      'OOMPolicy': 'kill', 'NoNewPrivileges': 'yes', 'CPUAccounting': 'yes',
                      'MemoryAccounting': 'yes', 'RemainAfterExit': 'yes', 'CPUQuota': '100%'}
        properties.update({'Restart': 'no', 'RestartForceExitStatus': ''})
        for key, value in properties.items():
            args += ['--property=' + key + '=' + str(value)]
        args += ['--', *namespace_argv]
        return self.command(args, timeout=10)

    def show(self, unit, *, timeout=10):
        props = ['Id', 'InvocationID', 'ControlGroup', 'MainPID', 'ActiveState', 'SubState',
                 'ExecMainCode', 'ExecMainStatus', 'Result', 'MemoryMax', 'MemorySwapMax',
                 'RuntimeMaxUSec', 'TasksMax', 'KillMode', 'TimeoutStopUSec', 'CPUUsageNSec',
                 'MemoryPeak', 'NoNewPrivileges', 'OOMPolicy', 'Transient', 'CPUQuotaPerSecUSec',
                 'RemainAfterExit', 'LoadState', 'Type', 'SendSIGKILL', 'Restart',
                 'RestartForceExitStatus', 'NRestarts']
        cp = self.command(['/usr/bin/systemctl', '--user', 'show', unit,
                           '--property=' + ','.join(props)], timeout=timeout, check=False)
        value = dict(line.split('=', 1) for line in cp.stdout.decode().splitlines() if '=' in line)
        need(cp.returncode == 0 or (cp.returncode in (1, 4) and value.get('LoadState') == 'not-found'),
             'systemd_unit_observation_unavailable')
        return value

    def snapshot_cgroup(self, path):
        need(path.startswith('/user.slice/') and '..' not in Path(path).parts, 'cgroup_path_invalid')
        root = Path('/sys/fs/cgroup' + path)
        if not root.exists():
            return {'path': path, 'exists': False, 'populated': 0, 'pids': [], 'cpu_usec': None, 'inode': None}
        need(root.resolve() == root, 'cgroup_alias')
        try:
            before = root.stat()
            for name in ('cgroup.events', 'cgroup.procs', 'cpu.stat', 'memory.current', 'memory.peak', 'memory.max'):
                need((root / name).is_file(), 'required_cgroup_v2_resource_interface_unavailable:' + name)
            events = dict(line.split() for line in (root / 'cgroup.events').read_text().splitlines())
            pids = set()
            for subtree in [root, *root.rglob('*')]:
                if subtree.is_dir():
                    pids.update(int(x) for x in (subtree / 'cgroup.procs').read_text().split())
            cpu = dict(line.split() for line in (root / 'cpu.stat').read_text().splitlines())
            value = {'path': path, 'exists': True, 'populated': int(events['populated']),
                    'pids': sorted(pids), 'cpu_usec': int(cpu['usage_usec']), 'inode': before.st_ino,
                    'memory_current': int((root / 'memory.current').read_text()),
                    'memory_peak': int((root / 'memory.peak').read_text()),
                    'memory_max': int((root / 'memory.max').read_text())}
            need(root.stat().st_ino == before.st_ino, 'cgroup_replaced')
            return value
        except (FileNotFoundError, Refused):
            if not root.exists():
                return {'path': path, 'exists': False, 'populated': 0, 'pids': [], 'cpu_usec': None, 'inode': None}
            raise

    def stop_owned(self, unit, invocation, cgroup, budget):
        # Recheck exact current invocation before the only whole-group stop.
        deadline = time.monotonic() + budget
        need(budget > 0, 'owned_cleanup_deadline_already_elapsed')
        validate_unit_identity(self.show(unit, timeout=budget), unit=unit, invocation=invocation, cgroup=cgroup)
        remaining = deadline - time.monotonic()
        need(remaining > 0, 'owned_cleanup_deadline_before_stop')
        self.command(['/usr/bin/systemctl', '--user', 'stop', unit], timeout=remaining)


def enforce_properties(s, b):
    need(s.get('Transient') == 'yes' and s.get('KillMode') == 'control-group'
         and s.get('NoNewPrivileges') == 'yes' and s.get('OOMPolicy') == 'kill'
         and s.get('MemoryMax') == str(unit_memory_limit(b)) and s.get('MemorySwapMax') == '0'
         and s.get('TasksMax') == str(b['tasks_max']) and s.get('RemainAfterExit') == 'yes',
         'actual_custody_properties_mismatch')
    need(s.get('Type') == 'exec' and s.get('SendSIGKILL') == 'yes' and s.get('Restart') == 'no'
         and s.get('RestartForceExitStatus') == '' and s.get('NRestarts') == '0',
         'execute_once_unit_type_kill_or_no_restart_invariant_mismatch')
    # systemctl serializes times as human-readable values. cgroup CPU accounting
    # and independent monotonic wall enforce the cumulative CPU/wall budgets;
    # RuntimeMaxSec is the service manager's backstop if this caller dies.
    need(0 < parse_duration(s.get('RuntimeMaxUSec')) <= b['wall_seconds'] - b['cleanup_seconds']
         and 0 < parse_duration(s.get('TimeoutStopUSec')) <= b['cleanup_seconds'],
         'finite_systemd_deadline_missing_or_expanded')
    need(parse_duration(s.get('CPUQuotaPerSecUSec')) == 1, 'whole_group_one_CPU_quota_required')


def parse_duration(text):
    need(type(text) is str and text not in ('', 'infinity'), 'finite_duration_required')
    units = {'us': 0.000001, 'ms': 0.001, 's': 1, 'min': 60, 'h': 3600}
    tokens = text.split()
    total = 0
    for token in tokens:
        m = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)(us|ms|s|min|h)', token)
        need(m is not None, 'unknown_systemd_duration')
        total += float(m.group(1)) * units[m.group(2)]
    return total


def active_budget(budget, cgroup, *, elapsed, outside_cpu):
    need(cgroup['exists'], 'active_owned_cgroup_missing')
    need(cgroup['cpu_usec'] is not None and cgroup['cpu_usec'] <=
         (budget['cpu_seconds'] - budget['cleanup_seconds'] - 1 - outside_cpu) * 1_000_000,
         'whole_cgroup_CPU_budget_exhausted')
    need(elapsed <= budget['wall_seconds'] - budget['cleanup_seconds'],
         'operation_wall_reserve_reached')


def monitor_owned(backend, *, unit, budget, emit, now=time.monotonic, sleep=time.sleep,
                  proc_reader=proc_identity, on_sample=None, operation_started=None,
                  outside_cpu=lambda: 0.0, outside_memory=lambda: 0):
    start = now() if operation_started is None else operation_started
    invocation = cgroup = inode = None
    last = None
    retirement = None
    outcome = 'UNKNOWN'
    reason = None
    try:
        while True:
            remaining = start + budget['wall_seconds'] - budget['cleanup_seconds'] - now()
            need(remaining > 0, 'operation_wall_reserve_reached')
            s = validate_unit_identity(backend.show(unit, timeout=min(10, remaining)), unit=unit,
                                       invocation=invocation, cgroup=cgroup)
            invocation = s['InvocationID']
            if s['ControlGroup']:
                cgroup = s['ControlGroup']
            enforce_properties(s, budget)
            need(cgroup is not None, 'no_owned_cgroup_observed')
            cg = backend.snapshot_cgroup(cgroup)
            if not cg['exists'] and s['ActiveState'] not in ('inactive', 'failed'):
                # Read-only exit reconciliation: the group can disappear between
                # systemd show and its kernel snapshot. Never re-run an effect.
                remaining = start + budget['wall_seconds'] - budget['cleanup_seconds'] - now()
                need(remaining > 0, 'operation_wall_reserve_reached')
                s = validate_unit_identity(backend.show(unit, timeout=min(10, remaining)),
                    unit=unit, invocation=invocation, cgroup=cgroup)
                enforce_properties(s, budget)
            if cg['exists']:
                need(inode in (None, cg['inode']), 'cgroup_inode_changed')
                inode = cg['inode']
                need(cg['memory_max'] == unit_memory_limit(budget)
                     and 0 <= cg['memory_current'] <= cg['memory_peak'] <= unit_memory_limit(budget),
                     'actual_whole_group_memory_limit_or_observation_mismatch')
            need(outside_memory() <= CONTROLLER_MEMORY_RESERVE_BYTES,
                 'outside_controller_memory_reserve_exceeded')
            retained_exit = (s['ActiveState'] == 'active' and s.get('SubState') == 'exited'
                             and s.get('MainPID') == '0')
            if s['ActiveState'] not in ('inactive', 'failed') and not retained_exit:
                # Never publish a new phase release from an already exhausted
                # snapshot; live budget checks precede the callback's effects.
                active_budget(budget, cg, elapsed=now() - start, outside_cpu=outside_cpu())
            processes = []
            for pid in cg['pids']:
                try:
                    identity = proc_reader(pid)
                    need(identity['pid'] == pid and type(identity['start_ticks']) is int
                         and identity['start_ticks'] > 0 and identity['cgroup'] == '0::' + cgroup,
                         'sampled_PID_not_current_owned_cgroup_member')
                    processes.append(identity)
                except FileNotFoundError:
                    # Exit racing a sampling read is an observation, not absence
                    # proof. Terminal proof below uses populated+pids+unit state.
                    processes.append({'pid': pid, 'state': 'EXIT_RACED_SAMPLE'})
            emit({'phase': 'CUSTODY_SAMPLE', 'unit': s, 'cgroup': cg, 'processes': processes})
            if on_sample is not None:
                on_sample(s, cg, processes)
            last = (s, cg)
            if s['ActiveState'] in ('inactive', 'failed') or retained_exit:
                need(now() - start <= budget['wall_seconds'] - budget['cleanup_seconds'],
                     'late_terminal_operation_wall')
                need(cg['populated'] == 0 and not cg['pids'], 'terminal_cgroup_not_empty')
                need(s['Result'] == 'success' and s['ExecMainCode'] == '1'
                     and s['ExecMainStatus'] == '0', 'actual_namespace_exit_not_success')
                need(s.get('CPUUsageNSec', '').isdigit()
                     and int(s['CPUUsageNSec']) / 1_000_000_000 + outside_cpu() <= budget['cpu_seconds'],
                     'terminal_CPU_usage_missing_or_exceeded')
                need(s.get('MemoryPeak', '').isdigit()
                     and int(s['MemoryPeak']) + outside_memory() <= budget['memory_bytes'],
                     'whole_operation_memory_peak_missing_or_exceeded')
                outcome = ('TERMINAL_CGROUP_EMPTY_NEEDS_UNIT_RETIREMENT' if retained_exit
                           else 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY')
                break
            # One-CPU aggregate quota plus cleanup/one-second sampling reserve:
            # stop before the declared cumulative120s ceiling, not at it. Actual
            # terminal counters are retained and independently checked as well.
            active_budget(budget, cg, elapsed=now() - start, outside_cpu=outside_cpu())
            sleep(0.1)
    except Exception as exc:
        reason = str(exc) if type(exc) is Refused else type(exc).__name__
        emit({'phase': 'REFUSED_NEEDS_OWNED_CLEANUP', 'reason': reason, 'actual_M': None})
    finally:
        if outcome != 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY' and invocation is not None and cgroup is not None:
            try:
                terminal_success = outcome == 'TERMINAL_CGROUP_EMPTY_NEEDS_UNIT_RETIREMENT'
                deadline = min(start + budget['wall_seconds'], now() + budget['cleanup_seconds'])
                remaining = deadline - now()
                need(remaining > 0, 'whole_owned_cleanup_deadline_already_elapsed')
                backend.stop_owned(unit, invocation, cgroup, remaining)
                while True:
                    remaining = deadline - now()
                    need(remaining > 0, 'whole_owned_cleanup_deadline')
                    s = backend.show(unit, timeout=min(10, remaining))
                    cg = backend.snapshot_cgroup(cgroup)
                    if s.get('LoadState') == 'not-found':
                        need(s.get('Id') == unit, 'retired_unit_name_mismatch')
                    else:
                        validate_unit_identity(s, unit=unit, invocation=invocation, cgroup=cgroup)
                    need(not cg['exists'] or inode in (None, cg['inode']), 'cleanup_cgroup_replaced')
                    emit({'phase': 'OWNED_CLEANUP', 'unit': s, 'cgroup': cg})
                    need(now() <= deadline, 'late_whole_owned_cleanup_observation')
                    retired = s.get('LoadState') == 'not-found' or s.get('ActiveState') in ('inactive', 'failed')
                    if retired and cg['populated'] == 0 and not cg['pids']:
                        retirement = (s, cg)
                        outcome = ('OWNED_UNIT_EXITED_AND_CGROUP_EMPTY' if terminal_success
                                   else 'REFUSED_OWNED_CGROUP_EMPTY')
                        if not terminal_success:
                            last = (s, cg)
                        break
                    need(now() < deadline, 'whole_owned_cleanup_deadline')
                    sleep(0.1)
            except Exception as exc:
                outcome = 'OWNED_CLEANUP_UNKNOWN'
                emit({'phase': outcome, 'reason': str(exc) if type(exc) is Refused else type(exc).__name__})
    return {'status': outcome, 'refusal': reason, 'unit': unit, 'invocation_id': invocation,
            'cgroup_path': cgroup, 'last_snapshot': last, 'retirement_snapshot': retirement,
            'actual_M': None, 'runtime_attested': False}


def acquire_existing_slot():
    path = Path(SLOT)
    directory(path.parent)
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)  # never creates/replaces slot
    try:
        st = os.fstat(fd)
        need(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1
             and not st.st_mode & 0o022, 'existing_slot_identity_or_rights')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as exc:
        os.close(fd)
        if type(exc) is Refused:
            raise
        raise Refused('exclusive_live_slot_taken')
    return fd


def execute_once(plan_ref, authority_refs, *, backend=None, proc_reader=proc_identity,
                 symbol_observer=observe_native_symbols, resource_reader=observe_process_resources,
                 now=time.monotonic, sleep=time.sleep):
    """Actual backend is ROOT ONLY; Sol tests may inject every inert effect leaf."""
    plan = json.loads(read_pinned(plan_ref, private=True))
    prepared = inspect_plan(plan)
    validate_authority(authority_refs, plan_ref['sha256'], plan, now=int(time.time()))
    slot = acquire_existing_slot()
    opdir = Path(plan['operation_dir'])
    events = []
    def emit(event):
        event = dict(event, monotonic_ns=time.monotonic_ns())
        events.append(event)
        atomic_json(opdir / 'outer-journal.json', {'schema': 'frw.calc.outer-journal.v1',
                    'operation_id': plan['operation_id'], 'events': events, 'actual_M': None})
    backend = backend or SystemdBackend()
    resource_start = [(resource.getrusage(w).ru_utime + resource.getrusage(w).ru_stime)
                      for w in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
    def outside_cpu():
        return sum(resource.getrusage(w).ru_utime + resource.getrusage(w).ru_stime - base
                   for w, base in zip((resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN), resource_start))
    def outside_memory():
        # CLI helpers are direct, synchronous and nonoverlapping. Sum of each
        # category's high-water RSS is a conservative overlap bound. The actual
        # namespace descendants live under the separate reduced MemoryMax.
        return 1024 * sum(resource.getrusage(w).ru_maxrss
                          for w in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN))
    result = {'status': 'REFUSED_BEFORE_INTENT', 'actual_M': None, 'runtime_attested': False}
    consumed = False
    try:
        # Repeat mutable current pins/rights/empty-work/authority under live slot.
        read_pinned(plan_ref, private=True)
        prepared = inspect_plan(plan)
        validate_authority(authority_refs, plan_ref['sha256'], plan, now=int(time.time()))
        need(outside_memory() <= CONTROLLER_MEMORY_RESERVE_BYTES,
             'outside_controller_memory_reserve_exceeded_before_intent')
        unit = 'frw-calc-' + plan['nonce'] + '.service'
        backend.absent(unit)
        for name in ('tmp', 'cache', 'config', 'runtime'):
            (Path(plan['work_dir']) / name).mkdir(mode=0o700)
        # Empty private mountpoint only, never copy/cache-delete/rebaseline.
        (Path(plan['work_dir']) / 'cache/fontconfig').mkdir(mode=0o700)
        operation_started = now()
        job = dict(plan=plan, plan_sha256=plan_ref['sha256'],
                   deadline_monotonic=operation_started + plan['budgets']['wall_seconds'] - plan['budgets']['cleanup_seconds'])
        atomic_json(Path(plan['work_dir']) / 'namespace-job.json', job, exclusive=True)
        atomic_json(opdir / 'consumed-once.json', {'schema': 'frw.calc.consumed-once.v1',
                    'operation_id': plan['operation_id'], 'nonce': plan['nonce'],
                    'plan_ref': plan_ref, 'authority_refs': authority_refs,
                    'intent': EFFECT, 'unit': unit, 'unix': int(time.time())}, exclusive=True)
        consumed = True
        emit({'phase': 'INTENT_CONSUMED_BEFORE_LAUNCH', 'unit': unit, 'actual_M': None})
        try:
            backend.launch(unit, prepared['namespace_argv'], plan['budgets'])
        except Exception as exc:
            # A command error/timeout can follow successful submission. Reconcile
            # exact unit once through monitor; never resubmit the launch.
            emit({'phase': 'LAUNCH_RESPONSE_UNKNOWN', 'exception_class': type(exc).__name__})
        host_binding = None
        supervisor_binding = None
        seen_font_phases = set()
        def release_verified_custody(s, cg, processes):
            nonlocal host_binding, supervisor_binding
            work = Path(plan['work_dir'])
            if s['ActiveState'] not in ('active', 'activating') or not cg['exists'] or not cg['pids']:
                return
            unit_release = work / 'unit-release.json'
            if not unit_release.exists():
                # Before this release the pinned namespace script waits and
                # launches no GDB/Office/client. Bind the unique actual Python
                # supervisor HERE, independently of any later CAS marker PID.
                candidates = [p for p in processes if p.get('executable') == plan['tools']['python']['path']]
                need(len(candidates) <= 1, 'unexpected_Python_children_before_unit_release')
                if not candidates:
                    return  # bwrap may still be execing the known supervisor.
                supervisor_binding = candidates[0]
                atomic_json(unit_release, {'operation_id': plan['operation_id'], 'nonce': plan['nonce'],
                    'stage': 'ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED', 'unit': unit,
                    'invocation_id': s['InvocationID'], 'cgroup_path': cg['path'],
                    'namespace_supervisor_host_identity': supervisor_binding}, exclusive=True)
                emit({'phase': 'NAMESPACE_SUPERVISOR_HOST_PID_BIRTH_BOUND', 'process': supervisor_binding})
            cas_phase = work / 'font-CAS-phase.json'
            if cas_phase.exists():
                marker = json.loads(cas_phase.read_bytes())
                bound = validate_font_CAS_phase(marker, plan, processes, expected_process=supervisor_binding,
                                               resource_reader=resource_reader,
                                               now=now(), operation_started=operation_started)
                if bound is not None:
                    key = (bound['phase'], bound['started_monotonic'])
                    if key not in seen_font_phases:
                        seen_font_phases.add(key)
                        emit({'phase': 'FONT_CAS_HOST_PID_BIRTH_CGROUP_BOUND', 'binding': bound})
            ready = work / 'office-ready.json'
            if ready.exists() and not (work / 'office-release.json').exists():
                value = json.loads(ready.read_bytes())
                need(value['operation_id'] == plan['operation_id'] and value['nonce'] == plan['nonce'],
                     'office_ready_other_operation')
                native, inside = value['native_process'], value['office_identity']
                matches = [p for p in processes if p.get('nspid') and p['nspid'][-1] == native['pid']
                           and p.get('start_ticks') == native['start_ticks']
                           and p.get('namespaces') == inside['namespaces']
                           and p.get('boot_id') == inside['boot_id']]
                need(len(matches) == 1, 'host_namespace_PID_birth_cgroup_mapping_missing')
                office = matches[0]
                gdb_inside = value['gdb_identity']
                parents = [p for p in processes if p.get('pid') == office['ppid']
                           and p.get('nspid') and p['nspid'][-1] == native['gdb_pid']
                           and p.get('namespaces') == inside['namespaces'] == gdb_inside['namespaces']
                           and p.get('start_ticks') == gdb_inside['start_ticks']
                           and p.get('boot_id') == gdb_inside['boot_id'] == inside['boot_id']]
                need(len(parents) == 1, 'host_GDB_direct_parent_mapping_missing')
                symbols = symbol_observer(office['pid'], plan)
                need(symbols['process_identity'] == office,
                     'host_PID_birth_or_custody_changed_during_independent_symbol_read')
                need(value['native_symbols'] == symbols['symbols'],
                     'early_GDB_symbols_differ_from_independent_host_mapping')
                fresh_group = backend.snapshot_cgroup(cg['path'])
                need(fresh_group['exists'] and fresh_group['inode'] == cg['inode']
                     and office['pid'] in fresh_group['pids'] and parents[0]['pid'] in fresh_group['pids'],
                     'owned_process_cgroup_changed_before_client_release')
                active_budget(plan['budgets'], fresh_group, elapsed=now() - operation_started,
                              outside_cpu=outside_cpu())
                need(outside_memory() <= CONTROLLER_MEMORY_RESERVE_BYTES,
                     'outside_memory_reserve_before_client_release')
                host_binding = {'office': office, 'gdb': parents[0], 'unit': unit,
                                'invocation_id': s['InvocationID'], 'cgroup': cg,
                                'native_process': native, 'native_symbols': symbols['symbols'],
                                'symbol_binding': symbols}
                atomic_json(work / 'office-release.json', {'operation_id': plan['operation_id'],
                    'nonce': plan['nonce'], 'stage': 'ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND',
                    'native_process': native, 'native_symbols': symbols['symbols'],
                    'host_binding': host_binding}, exclusive=True)
                emit({'phase': 'HOST_NAMESPACE_OFFICE_GDB_CGROUP_BOUND', 'binding': host_binding})
        result = monitor_owned(backend, unit=unit, budget=plan['budgets'], emit=emit,
            now=now, sleep=sleep, proc_reader=proc_reader, on_sample=release_verified_custody,
            operation_started=operation_started, outside_cpu=outside_cpu, outside_memory=outside_memory)
        if result['status'] == 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY':
            need(host_binding is not None, 'actual_host_namespace_process_binding_never_completed')
            pre = json.loads(read_pinned(plan['preload']))
            need(observe_sources(plan, pre) == prepared['source_observations'],
                 'actual_source_identity_rights_or_bytes_changed')
            raw = (Path(plan['work_dir']) / 'namespace-result.json').read_bytes()
            ns = json.loads(raw)
            need(ns['status'] == 'CLOSED_UNRELEASED' and ns['nonce'] == plan['nonce']
                 and ns['actual_M'] is None and ns['runtime_attested'] is False,
                 'namespace_closure_unconfirmed')
            loaded_observations = json.loads((Path(plan['work_dir']) / 'loaded-observations.json').read_bytes())
            cas_observations = [ns['font_view_before_office'], ns['font_view_after_bootstrap'], loaded_observations['font_view'],
                                ns['font_view_after_close']]
            for phase, view in zip(('BEFORE_OFFICE', 'AFTER_BOOTSTRAP_BEFORE_GDB', 'AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'), cas_observations):
                source = view['namespace_process']
                need(view['phase'] == phase and view['view_sha256'] == plan['font_view']['expected_view_sha256']
                     and view['consumer'] == plan['font_view']['consumer']
                     and view['baseline'] == plan['font_view']['baseline']
                     and view['provenance_ref'] == plan['font_view']['provenance_ref']
                     and view['base_static_view_sha256'] == plan['font_view']['base_view_sha256']
                     and view['derived_cache'] == plan['font_view']['derived_cache']
                     and source['namespace_pid'] == supervisor_binding['nspid'][-1]
                     and source['start_ticks'] == supervisor_binding['start_ticks']
                     and source['namespaces'] == supervisor_binding['namespaces']
                     and source['boot_id'] == supervisor_binding['boot_id']
                     and source['executable_sha256'] == plan['tools']['python']['sha256'],
                     'final_font_CAS_not_bound_to_same_actual_supervisor')
                need(all(type(view[k]) in (int, float) and math.isfinite(view[k]) and 0 <= view[k] <= limit
                     for k, limit in (('actual_wall_seconds', 60), ('actual_process_CPU_seconds', 30)))
                     and type(view['current_address_space_peak_RSS_bytes']) is int
                     and 0 <= view['current_address_space_peak_RSS_bytes'] <= 512 * 1024**2
                     and type(view['output_bytes']) is int and 0 <= view['output_bytes'] <= 4 * 1024**2
                     and view['observation']['status'] == 'metadata_cas_pass_with_critical_rehash',
                     'final_font_CAS_per_call_resource_or_actual_status_unbound')
            # Actual stopped current ENV is distinct from startup /proc bytes.
            # Join the exact two protocol transcripts to the canonical/effective
            # view and original Root-bound process after whole-cgroup closure.
            font_checker = load_module('frw_Root_current_font_runtime_checker', plan['namespace_entry'])
            font_environment = json.loads(read_pinned(plan['font_view']['baseline'], private=True))['view']['environment']
            font_deadline = operation_started + plan['budgets']['wall_seconds'] - plan['budgets']['cleanup_seconds']
            supervisor = {'pid': supervisor_binding['nspid'][-1], 'ppid': cas_observations[0]['namespace_process']['ppid'],
                          'start_ticks': supervisor_binding['start_ticks']}
            # Host and namespace PPID can differ; the pinned namespace CAS already
            # records its actual inside PPID. Bind it to that same supervisor.
            for boundary, view in zip(('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'), cas_observations[2:]):
                tag = 'loaded' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'closed'
                names = ['font-runtime-' + tag + '-' + kind + '.json' for kind in ('request', 'proof', 'release', 'accepted')]
                names.append('font-view-after-load.json' if tag == 'loaded' else 'font-view-after-close.json')
                transcripts = []
                for name in names:
                    path = Path(plan['work_dir']) / name
                    st = path.lstat()
                    need(stat.S_ISREG(st.st_mode) and st.st_size <= 32768, 'final_font_runtime_file_bound')
                    raw = read_pinned({'path': str(path), 'sha256': digest(path.read_bytes())}, private=True)
                    need(len(raw) <= 32768, 'final_font_runtime_read_bound')
                    transcripts.append(raw)
                proof_ref = font_checker.validate_font_runtime_pair(*transcripts, plan=plan,
                    native=host_binding['native_process'], environment=font_environment, boundary=boundary,
                    deadline=font_deadline, supervisor=supervisor)
                need(json.loads(transcripts[-1]) == view and view['office_font_environment_proof'] == proof_ref,
                     'final_font_runtime_view_transcript_differs')
            # Native checker is deliberately invoked ONLY here, after process,
            # cgroup, source, readonlyclose and no-output terminal confirmation.
            trace_raw = (Path(plan['work_dir']) / 'native-trace.json').read_bytes()
            trace = json.loads(trace_raw)
            need(trace['process'] == ns['native_process'] == host_binding['native_process']
                 and trace['symbols'] == ns['native_symbols'] == host_binding['native_symbols'],
                 'final_trace_differs_from_early_independent_Root_binding')
            checker = load_module('frw_Root_postclose_native_checker', plan['observer']['checker'])
            helper_kwargs = {}
            if 'load_dependency' in plan['observer']:
                policy = load_module('frw_Root_final_helper_policy', plan['observer']['load_dependency']['policy'])
                helper_runtime = dict(plan['inner_input']['load_dependency'])
                helper_runtime['operation_deadline_monotonic'] = (operation_started + plan['budgets']['wall_seconds']
                                                               - plan['budgets']['cleanup_seconds'])
                helper_kwargs = {'load_dependency': helper_runtime, 'validate_dependency': policy.validate_closed}
            evidence = checker.validate_trace(trace_raw, expected_sha256=digest(trace_raw),
                nonce=plan['nonce'], process=host_binding['native_process'], symbols=host_binding['native_symbols'],
                uno_widths=ns['uno_widths'], root_custody_confirmed=True, **helper_kwargs)
            terminal = result['last_snapshot'][0]
            need(now() - operation_started <= plan['budgets']['wall_seconds'], 'final_whole_operation_wall_exceeded')
            need(int(terminal['CPUUsageNSec']) / 1_000_000_000 + outside_cpu() <= plan['budgets']['cpu_seconds'],
                 'final_whole_operation_CPU_exceeded')
            need(outside_memory() <= CONTROLLER_MEMORY_RESERVE_BYTES
                 and int(terminal['MemoryPeak']) + outside_memory() <= plan['budgets']['memory_bytes'],
                 'final_whole_operation_memory_exceeded')
            result.update(status='CLOSED_NATIVE_BOUND_EVIDENCE_ONLY', native_evidence=evidence,
                          namespace_result_sha256=digest(raw), source_hashes_unchanged=True,
                          host_namespace_binding=host_binding)
    except Exception as exc:
        # The specific effect remains consumed/UNKNOWN. No repeat marker removal.
        result.update(status='REFUSED_OR_UNKNOWN', exception_class=type(exc).__name__,
                      reason=str(exc) if type(exc) is Refused else None, consumed_once=consumed)
        emit({'phase': result['status'], 'exception_class': type(exc).__name__, 'actual_M': None})
    finally:
        result['resource_scope'] = {'whole_unit_descendants': 'MemoryMax/CPUQuota/cpu.stat/systemd cumulativeCPU',
            'outside_unit_outer_and_reaped_control_children_CPU_seconds': outside_cpu(),
            'outside_unit_outer_peak_RSS_KiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'whole_operation_memory_budget_bytes': plan['budgets']['memory_bytes'],
            'whole_unit_memory_max_bytes': unit_memory_limit(plan['budgets']),
            'outside_controller_memory_reserve_bytes': CONTROLLER_MEMORY_RESERVE_BYTES,
            'outside_controller_and_sequential_helpers_RSS_upper_bound_bytes': outside_memory(),
            'memory_enforcement': 'Reduced hard unit MemoryMax plus observed/refusing reserved outer+helper RSS bound; no kernel hard RSS cap on Root caller',
            'CPU_budget_includes': 'Whole unit plus measured outside caller/control children since execution boundary',
            'RLIMIT_AS_used_as_RSS': False}
        if getattr(backend, 'source_only', False):
            result.update(source_rehearsal_only=True, runtime_grant=False,
                          evidence_scope='SYNTHETIC_PARSER_AND_ORCHESTRATION_ONLY')
        try:
            atomic_json(opdir / 'outer-result.json', result)
        finally:
            fcntl.flock(slot, fcntl.LOCK_UN)
            os.close(slot)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--execute-once', action='store_true')
    parser.add_argument('--input')
    parser.add_argument('--input-sha256')
    parser.add_argument('--authority-refs')
    parser.add_argument('--authority-refs-sha256')
    a = parser.parse_args(argv)
    need(not (a.inspect and a.execute_once), 'choose_inspect_or_execute')
    if not a.input:
        print(json.dumps({'status': 'SOURCE_ONLY_NO_OPERATION', 'actual_M': None, 'runtime_grant': False}))
        return 0
    ref = {'path': a.input, 'sha256': a.input_sha256}
    if a.execute_once:
        need(a.authority_refs and a.authority_refs_sha256, 'explicit_fresh_Root_authority_required')
        refs = json.loads(read_pinned({'path': a.authority_refs, 'sha256': a.authority_refs_sha256}, private=True))
        result = execute_once(ref, refs)
    else:
        result = inspect_plan(json.loads(read_pinned(ref, private=True)))
    print(json.dumps(result, sort_keys=True))
    return (0 if result['status'] in ('SOURCE_INPUTS_INSPECTED_NO_GRANT',
                                      'CLOSED_NATIVE_BOUND_EVIDENCE_ONLY') else 2)


def cli(argv=None):
    try:
        return main(argv)
    except (Refused, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'REFUSED_OR_UNBOUND_OR_UNKNOWN', 'actual_M': None,
            'runtime_grant': False, 'exception_class': type(exc).__name__,
            'reason': str(exc) if type(exc) is Refused else None}))
        return 2


if __name__ == '__main__':
    raise SystemExit(cli())
