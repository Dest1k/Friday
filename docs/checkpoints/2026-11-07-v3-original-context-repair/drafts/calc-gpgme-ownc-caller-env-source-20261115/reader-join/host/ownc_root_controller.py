"""Root own-C qualification SOURCE; import and --inspect perform no effects.

This finite caller reuses the reviewed outer monitor, resource guard, slot and
SystemdBackend.  It is not admission, an Office caller, or a qualification PASS.
Only an independently reviewed, externally hash-bound Root invocation may call
execute_once.  A consumed invocation is never replayed following UNKNOWN.
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
import re
import resource
import stat
import sys
import time
import types

WORK = '/tmp/friday-metric-work'
SCHEMA = 'frw.ownc.gpgme-static-plan.v1'
INVOCATION = 'frw.ownc.gpgme-root-invocation.v1'
SCOPE = 'ONE_HARMLESS_OWN_C_GPGME_QUALIFICATION_ONLY'
PINNED_OUTER_SHA = '756766d2a670d8c8b01c921a339fbd98ccf09928a1c4923dfe369d45c9027b57'
PINNED_NAMESPACE_SHA = '398c3b883a4d0fcd31032709e71c8e15163cfeaeea4dc999262260047aa2e8bb'
PINNED_BUILDER_SHA = '2223ffcee689611fa1ee8f19cb62e80a2a417f93affa7a28b4d3dc15acddea4b'
MAX_SOURCE_BYTES = 4 * 1024**2


def need(ok, code):
    if not ok:
        raise RuntimeError(code)


def stamp(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid,
            st.st_gid, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def read_ref(ref, *, private=False):
    need(type(ref) is dict and set(ref) == {'path', 'sha256'}
         and type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'ownc_ref_schema')
    path = Path(ref['path'])
    need(path.is_absolute() and str(path.resolve()) == str(path), 'ownc_ref_alias')
    for parent in [path.parent, *path.parent.parents]:
        st = parent.lstat()
        need(stat.S_ISDIR(st.st_mode) and st.st_uid in (0, os.getuid())
             and not st.st_mode & 0o022, 'ownc_ref_parent_rights')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022
             and before.st_size <= MAX_SOURCE_BYTES, 'ownc_ref_rights_or_bound')
        if private:
            need(before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600,
                 'ownc_private_ref_required')
        parts, count = [], 0
        while True:
            part = os.read(fd, min(65536, MAX_SOURCE_BYTES + 1 - count))
            if not part:
                break
            parts.append(part)
            count += len(part)
            need(count <= MAX_SOURCE_BYTES, 'ownc_ref_bound')
        raw = b''.join(parts)
        need(stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat()), 'ownc_ref_changed')
    finally:
        os.close(fd)
    need(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'ownc_ref_pin')
    return raw


def load_module(ref, name):
    module = types.ModuleType(name)
    module.__file__ = ref['path']
    exec(compile(read_ref(ref), ref['path'], 'exec'), module.__dict__)
    return module


def verify_image_ref(ref):
    """Stream executable pins so a large GDB image does not inflate RSS."""
    need(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'ownc_image_ref')
    path = Path(ref['path'])
    need(path.is_absolute() and path.resolve() == path, 'ownc_image_ref_alias')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022
             and 0 < before.st_size <= 128 * 1024**2, 'ownc_image_rights_or_bound')
        digest = hashlib.sha256()
        while True:
            part = os.read(fd, 1024**2)
            if not part:
                break
            digest.update(part)
        need(stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat())
             and digest.hexdigest() == ref['sha256'], 'ownc_image_pin_or_cas')
    finally:
        os.close(fd)


def json_load(raw):
    def pairs(items):
        value = dict(items)
        need(len(value) == len(items), 'ownc_duplicate_json_key')
        return value
    return json.loads(raw, object_pairs_hook=pairs)


def host_work_scope(work):
    """Bind the exact already-created private host work and its owned parent."""
    work = Path(work)
    need(work.is_absolute() and str(work.resolve()) == str(work), 'ownc_host_work_alias')
    for parent in work.parents:
        st = parent.lstat()
        need(stat.S_ISDIR(st.st_mode) and st.st_uid in (0, os.getuid())
             and not st.st_mode & 0o022, 'ownc_host_parent_rights')
    def directory(path):
        st = path.lstat()
        need(stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid()
             and stat.S_IMODE(st.st_mode) == 0o700, 'ownc_host_work_private_directory')
        return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid)
    return {'path': str(work), 'directory': directory(work), 'parent': directory(work.parent)}


def host_record(scope, name, *, deadline):
    """One bounded immutable same-FD/path host record; no namespace WORK alias.

    Ready is immutable. Terminal records are read only after Root confirms the
    whole cgroup empty. No replacement retry or fresh clock is permitted.
    """
    need(name in ('office-ready.json', 'held-fixture-supervisor-result.json', 'native-trace.json'),
         'ownc_host_record_role')
    need(type(deadline) in (int, float) and math.isfinite(deadline)
         and time.monotonic() < deadline, 'ownc_host_original_deadline')
    work = Path(scope['path'])
    need(host_work_scope(work) == scope, 'ownc_host_work_changed')
    directory = os.open(work, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        identity = lambda st: (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid)
        need(identity(os.fstat(directory)) == scope['directory'], 'ownc_host_work_changed')
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                     dir_fd=directory)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                 and stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1
                 and 0 <= before.st_size <= 1048576, 'ownc_host_record_rights_bound')
            need(stamp(before) == stamp(os.stat(name, dir_fd=directory, follow_symlinks=False)),
                 'ownc_host_record_changed')
            parts, count = [], 0
            while True:
                part = os.read(fd, min(65536, 1048577 - count))
                if not part:
                    break
                parts.append(part)
                count += len(part)
                need(count <= 1048576, 'ownc_host_record_bound')
            raw = b''.join(parts)
            need(len(raw) == before.st_size and stamp(before) == stamp(os.fstat(fd))
                 == stamp(os.stat(name, dir_fd=directory, follow_symlinks=False)),
                 'ownc_host_record_changed')
            need(identity(os.fstat(directory)) == scope['directory']
                 and host_work_scope(work) == scope, 'ownc_host_work_changed')
            value = json_load(raw)
            need(time.monotonic() < deadline, 'ownc_host_original_deadline')
            return value
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def read_ready(scope, plan, processes, *, deadline):
    ready = host_record(scope, 'office-ready.json', deadline=deadline)
    office, gdb = map_ready(plan, ready, processes)
    need(time.monotonic() < deadline, 'ownc_host_original_deadline')
    return ready, office, gdb


def read_terminal(scope, plan, monitored, *, deadline):
    """UNKNOWN cleanup cannot authorize treating a live publication as final."""
    need(monitored['status'] in ('OWNED_UNIT_EXITED_AND_CGROUP_EMPTY', 'REFUSED_OWNED_CGROUP_EMPTY'),
         'ownc_terminal_cgroup_not_confirmed_empty')
    closure = monitored.get('retirement_snapshot') or monitored.get('last_snapshot')
    need(closure is not None and closure[1]['populated'] == 0 and not closure[1]['pids']
         and monitored['invocation_id'] and monitored['cgroup_path'], 'ownc_terminal_cgroup_not_confirmed_empty')
    records = {}
    for name, key in (('held-fixture-supervisor-result.json', 'supervisor'), ('native-trace.json', 'trace')):
        need(time.monotonic() < deadline, 'ownc_host_original_deadline')
        if (Path(scope['path']) / name).exists():
            value = host_record(scope, name, deadline=deadline)
            if key == 'supervisor':
                need(value['schema'] == 'frw.own-held-font-fixture-supervisor-result.v1'
                     and value['operation_id'] == plan['operation_id'] and value['nonce'] == plan['nonce'],
                     'ownc_terminal_supervisor_operation_join')
            else:
                need(value['schema'] == 'frw.own-held-font-fixture-trace.v1'
                     and value['kind'] == 'OWN_POPEN_FIXTURE_ONLY' and value['nonce'] == plan['nonce'],
                     'ownc_terminal_trace_operation_join')
            records[key] = value
    need(time.monotonic() < deadline, 'ownc_host_original_deadline')
    return records


def put(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


def outside_memory():
    # Literal lifetime peaks. Never subtract/reset an inconvenient launch history.
    return sum(resource.getrusage(kind).ru_maxrss * 1024
               for kind in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN))


def outside_cpu():
    return sum(value.ru_utime + value.ru_stime for value in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def validate_budget(budget):
    need(type(budget) is dict and set(budget) == {'wall_seconds', 'cleanup_seconds', 'cpu_seconds',
        'memory_bytes', 'startup_seconds', 'tasks_max'}, 'ownc_budget_schema')
    need(all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in budget.values()),
         'ownc_finite_budget')
    need(0 < budget['cleanup_seconds'] < budget['startup_seconds'] <=
         budget['wall_seconds'] - budget['cleanup_seconds'] <= 230
         and budget['wall_seconds'] <= 240 and budget['cpu_seconds'] <= 120
         and budget['cpu_seconds'] > budget['cleanup_seconds'] + 1
         and 256 * 1024**2 < budget['memory_bytes'] <= 2 * 1024**3
         and type(budget['memory_bytes']) is int and type(budget['tasks_max']) is int
         and 8 <= budget['tasks_max'] <= 512, 'ownc_budget_outside_declared_caps')


def inspect_plan(plan):
    """Pure source/schema joins; imports pinned metadata, never a process leaf."""
    need(type(plan) is dict and set(plan) == {'schema', 'kind', 'variant', 'budgets', 'tools',
        'readonly_roots', 'binding_root', 'prepared_ref', 'source_refs', 'observer', 'target_environment'},
         'ownc_plan_schema')
    need(plan['schema'] == SCHEMA and plan['kind'] == 'OWN_POPEN_FIXTURE_ONLY', 'ownc_plan_scope')
    validate_budget(plan['budgets'])
    need(type(plan['source_refs']) is dict and set(plan['source_refs']) == {
        'outer_runner', 'metric_namespace', 'namespace', 'supervisor', 'gdb_driver'}, 'ownc_source_roles')
    refs = plan['source_refs']
    need(refs['outer_runner']['sha256'] == PINNED_OUTER_SHA
         and refs['metric_namespace']['sha256'] == PINNED_BUILDER_SHA
         and refs['namespace']['sha256'] == PINNED_NAMESPACE_SHA, 'ownc_reviewed_infra_pins')
    for ref in refs.values():
        read_ref(ref)
    need(type(plan['tools']) is dict and set(plan['tools']) == {'python', 'gdb', 'bwrap'}, 'ownc_tools_schema')
    for role, original in (('python', '/usr/bin/python3'), ('gdb', '/usr/bin/gdb'), ('bwrap', '/usr/bin/bwrap')):
        need(str(Path(original).resolve()) == plan['tools'][role]['path'], 'ownc_tool_realpath:' + role)
        verify_image_ref(plan['tools'][role])
    prepared = json_load(read_ref(plan['prepared_ref']))
    need(prepared['kind'] == plan['kind'] and prepared['variant'] == plan['variant']
         and prepared['preparation_only'] is True and prepared['runtime_executed'] is False,
         'ownc_preparation_scope')
    for key in ('source_ref', 'target_ref', 'manifest_ref', 'adapter_ref', 'policy_ref',
                'native_observer_ref', 'namespace_ref', 'gdb_driver_ref', 'supervisor_ref'):
        read_ref(prepared[key])
    need(prepared['namespace_ref'] == refs['namespace'] and prepared['supervisor_ref'] == refs['supervisor']
         and prepared['gdb_driver_ref'] == refs['gdb_driver'], 'ownc_prepared_source_join')
    need(type(plan['observer']) is dict and set(plan['observer']) == {
        'config', 'load_dependency', 'gpgme_engine_init'}, 'ownc_observer_roles')
    need(plan['observer']['config'] == {'target_sha256': prepared['target_ref']['sha256']},
         'ownc_target_observer_join')
    paper_binding = {'manifest': prepared['manifest_ref'], 'adapter': prepared['adapter_ref'],
                     'policy': prepared['policy_ref']}
    need(plan['observer']['load_dependency'] == paper_binding
         and plan['observer']['gpgme_engine_init'] == prepared['gpgme_binding'], 'ownc_helper_binding_join')
    env = plan['target_environment']
    need(type(env) is dict and all(type(k) is str and type(v) is str
         and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k)
         and not any(c in v for c in ('\0', '\n', '\r')) and v == v.strip()
         for k, v in env.items()) and env.get('DEBUGINFOD_URLS') == '',
         'ownc_exact_target_environment')
    need(not any(k.startswith('FRW_NATIVE_') or k == 'FRW_HELD_FIXTURE_CONFIG' for k in env),
         'ownc_no_debug_controls_in_target_environment')
    need(type(plan['readonly_roots']) is list and plan['readonly_roots']
         and all(type(p) is str and Path(p).is_absolute() for p in plan['readonly_roots'])
         and len(plan['readonly_roots']) == len(set(plan['readonly_roots'])), 'ownc_readonly_roots')
    for ref in [plan['prepared_ref'], *refs.values(), *paper_binding.values(),
                *prepared['gpgme_binding'].values(), prepared['source_ref'], prepared['target_ref']]:
        need(any(Path(ref['path']).is_relative_to(Path(root)) for root in plan['readonly_roots']),
             'ownc_readonly_source_not_mounted')
    manifest = json_load(read_ref(prepared['gpgme_binding']['manifest']))
    need(manifest['collector_pins']['environment'] == env, 'ownc_complete_collector_startup_env_join')
    need(manifest['collector_pins']['operation'] is None and manifest['collector_pins']['original'] is None
         and manifest['collector_pins']['reaper'] is None, 'ownc_no_future_process_facts')
    ns = load_module(refs['namespace'], 'frw_ownc_reviewed_namespace')
    # Use existing strict production-format consumers, with only the explicitly
    # isolated fixture validator's paper manifest pin changed by the preparer.
    build_bundles(plan, prepared, ns, operation_id='source-only-unbound', nonce='0' * 32,
                  deadline=1.0, validation_only=True)
    return prepared


def build_bundles(plan, prepared, ns, *, operation_id, nonce, deadline, validation_only=False):
    import copy
    paper = copy.deepcopy(prepared['runtime_template'])
    gpgme = copy.deepcopy(prepared['gpgme_runtime_template'])
    for runtime in (paper, gpgme):
        need(runtime['operation_deadline_monotonic'] is None, 'ownc_template_clock_bound')
        runtime.update(operation_id=operation_id, nonce=nonce, operation_deadline_monotonic=deadline)
    binding = plan['observer']['load_dependency']
    policy = load_module(binding['policy'], 'frw_ownc_paper_policy')
    manifest = json_load(read_ref(binding['manifest']))
    policy.validate_manifest(manifest, fixture=True)
    policy.validate_runtime(paper, manifest)
    need(paper['manifest_ref'] == binding['manifest'], 'ownc_paper_manifest_join')
    paper_bundle = {'schema': 'frw.calc.paper-helper-runtime-bundle.v1', 'runtime': paper,
        'manifest_ref': binding['manifest'], 'adapter_ref': binding['adapter'], 'policy_ref': binding['policy']}
    gb = plan['observer']['gpgme_engine_init']
    modules = ns.gpgme_sources(gb)
    modules['validator'].validate_runtime(gpgme, manifest_ref=gb['manifest'], paper_runtime=paper)
    gpgme_bundle = {'schema': 'frw.calc.gpgme-engine-init-bundle.v2', 'manifest_ref': gb['manifest'],
        **{role + '_ref': gb[role] for role in ('validator', 'collector', 'adapter', 'policy', 'mapper')},
        'runtime': gpgme, 'evidence_path': gpgme['evidence_path']}
    modules['validator'].validate_bundle(gpgme_bundle, json_load(read_ref(gb['manifest'])),
                                          modules['policy'], modules['collector'])
    return paper_bundle, gpgme_bundle


def namespace_argv(plan, builder, *, work, job_ref):
    """Reuse builder and compare its entire ENV, then add declared debug URL."""
    supervisor_argv = ['/usr/bin/python3', '-I', '-B', '-S', plan['source_refs']['supervisor']['path'],
                       '--job-ref-json', json.dumps(job_ref, sort_keys=True)]
    # Keep the old controller's read-only null stdin, private supervisor log and
    # zero core limit. This exec preserves the same namespace supervisor PID2;
    # the separate fresh-fork shell requirement applies to the Root controller.
    launcher = (
        "import os,resource\n"
        "from pathlib import Path\n"
        "w=Path('/tmp/friday-metric-work')\n"
        "f=os.open(w/'supervisor.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)\n"
        "z=os.open('/dev/null',os.O_RDONLY)\n"
        "os.dup2(z,0);os.dup2(f,1);os.dup2(f,2)\n"
        "if f>2:os.close(f)\n"
        "if z>2:os.close(z)\n"
        "resource.setrlimit(resource.RLIMIT_CORE,(0,0))\n"
        "os.execve('/usr/bin/python3'," + repr(supervisor_argv) + ","
        + repr(plan['target_environment']) + ")\n")
    command = ['/usr/bin/python3', '-I', '-B', '-S', '-c', launcher]
    argv = builder.build_namespace(writable=work, readonly=plan['readonly_roots'],
                                   binding_root=plan['binding_root'], command=command)
    delimiter = argv.index('--')
    actual = {}
    index = 0
    while index < delimiter:
        if argv[index] == '--setenv':
            need(argv[index + 1] not in actual, 'ownc_duplicate_builder_environment')
            actual[argv[index + 1]] = argv[index + 2]
            index += 3
        else:
            index += 1
    need('DEBUGINFOD_URLS' not in actual, 'ownc_builder_debug_url_unexpected')
    actual['DEBUGINFOD_URLS'] = ''
    need(actual == plan['target_environment'], 'ownc_builder_complete_environment_mismatch')
    return argv[:delimiter] + ['--setenv', 'DEBUGINFOD_URLS', ''] + argv[delimiter:]


def map_ready(plan, ready, processes):
    """Pure join; a supervisor PID2 cannot stand in for namespace reaper PID1."""
    need(ready['schema'] == 'frw.calc.office-ready.v1'
         and ready['operation_id'] == plan['operation_id'] and ready['nonce'] == plan['nonce']
         and ready['scope'] == 'OWN_C_FIXTURE_ONLY' and ready['native_symbols'] is None,
         'ownc_ready_operation_or_fixture_scope')
    native, inside = ready['native_process'], ready['office_identity']
    matches = [p for p in processes if p.get('nspid') and p['nspid'][-1] == native['pid']
        and p.get('start_ticks') == native['start_ticks'] and p.get('namespaces') == inside['namespaces']
        and p.get('boot_id') == inside['boot_id']]
    need(len(matches) == 1, 'ownc_host_target_pid_birth_mapping')
    office = matches[0]
    gd = ready['gdb_identity']
    parents = [p for p in processes if p.get('pid') == office['ppid'] and p.get('nspid')
        and p['nspid'][-1] == native['gdb_pid'] and p.get('namespaces') == inside['namespaces'] == gd['namespaces']
        and p.get('start_ticks') == gd['start_ticks'] and p.get('boot_id') == inside['boot_id'] == gd['boot_id']]
    need(len(parents) == 1 and inside['ppid'] == native['gdb_pid'] and native['inferior'] == 1,
         'ownc_host_gdb_direct_parent_mapping')
    need(inside['executable_sha256'] == plan['observer']['config']['target_sha256'], 'ownc_ready_target_hash')
    return office, parents[0]


def observe_stopped_target(base, office):
    """Read actual all-stop task states while GDB's ready callback is blocked."""
    root = Path('/proc') / str(office['pid']) / 'task'
    before = sorted(int(p.name) for p in root.iterdir())
    need(1 <= len(before) <= 64, 'ownc_ready_thread_bound')
    states = []
    for tid in before:
        lines = (root / str(tid) / 'status').read_text().splitlines()
        status = next((line.split()[1] for line in lines if line.startswith('State:')), None)
        need(status in ('t', 'T'), 'ownc_target_not_all_stopped_at_ready')
        states.append({'tid': tid, 'state': status})
    need(before == sorted(int(p.name) for p in root.iterdir())
         and base.proc_identity(office['pid']) == office, 'ownc_ready_threads_or_birth_changed')
    return {'semantics': 'ACTUAL_STOPPED_TIDS_WHILE_FIXTURE_READY_CALLBACK_BLOCKED',
            'tasks': states, 'observed_monotonic': time.monotonic()}


def check_invocation(invocation, plan_ref):
    need(type(invocation) is dict and set(invocation) == {'schema', 'scope', 'plan_ref', 'operation_id',
         'nonce', 'operation_dir', 'source_review_ref', 'expires_unix', 'root_admitted'}, 'ownc_invocation_schema')
    need(invocation['schema'] == INVOCATION and invocation['scope'] == SCOPE
         and invocation['root_admitted'] is True and invocation['plan_ref'] == plan_ref,
         'ownc_external_root_admission_required')
    need(type(invocation['expires_unix']) in (int, float) and math.isfinite(invocation['expires_unix'])
         and time.time() < invocation['expires_unix'] <= time.time() + 3600,
         'ownc_current_bounded_root_admission')
    need(type(invocation['operation_id']) is str and re.fullmatch('[A-Za-z0-9_.-]{1,128}', invocation['operation_id'])
         and type(invocation['nonce']) is str and re.fullmatch('[0-9a-f]{32}', invocation['nonce']),
         'ownc_invocation_identity')
    # This is a protected external review input, not a self-issued reviewer bit.
    review = json_load(read_ref(invocation['source_review_ref'], private=True))
    need(review.get('plan_ref') == plan_ref and review.get('source_accepted') is True
         and review.get('runtime_admitted') is False, 'ownc_independent_source_review_required')


def execute_once(plan_ref, invocation_ref):
    """ROOT ONLY future finite effect. No callers of this function in source tests."""
    os.umask(0o077)
    plan = json_load(read_ref(plan_ref, private=True))
    prepared = inspect_plan(plan)
    invocation = json_load(read_ref(invocation_ref, private=True))
    check_invocation(invocation, plan_ref)
    base = load_module(plan['source_refs']['outer_runner'], 'frw_ownc_existing_outer')
    builder = load_module(plan['source_refs']['metric_namespace'], 'frw_ownc_existing_builder')
    ns = load_module(plan['source_refs']['namespace'], 'frw_ownc_existing_namespace')
    need(outside_memory() <= 256 * 1024**2, 'ownc_pre_effect_literal_root_memory_reserve')
    op = Path(invocation['operation_dir'])
    need(op.is_absolute() and str(op.resolve()) == str(op) and op.is_relative_to(Path('/home/jericho/.cache')),
         'ownc_operation_directory_scope')
    need(not any(op.is_relative_to(Path(root)) or Path(root).is_relative_to(op)
                 for root in [*plan['readonly_roots'], plan['binding_root']]),
         'ownc_operation_directory_overlaps_readonly_source')
    base.directory(op, private=True)
    need(not any(op.iterdir()), 'ownc_operation_directory_not_fresh_no_replay')
    runtime_plan = dict(plan, **{key: invocation[key] for key in ('operation_id', 'nonce')})
    work = op / 'work'
    runtime_plan['work_dir'] = str(work)
    unit = 'frw-helper-fixture-' + invocation['nonce'] + '.service'
    backend = base.SystemdBackend()
    events, known = [], {}
    slot = base.acquire_existing_slot()
    consumed = False
    result = {'schema': 'frw.ownc.gpgme-root-observation.v1', 'status': 'REFUSED_BEFORE_INTENT',
              'actual_M': None, 'Office_UNO': False, 'runtime_attested': False,
              'qualification': 'PENDING_ROOT_SEMANTIC_REVIEW', 'plan_ref': plan_ref,
              'invocation_ref': invocation_ref}
    try:
        # Mutable rights, source pins and authority are checked under the one
        # existing slot before the first operation intent and clock.
        read_ref(plan_ref, private=True)
        read_ref(invocation_ref, private=True)
        inspect_plan(plan)
        check_invocation(invocation, plan_ref)
        backend.absent(unit)
        need(outside_memory() <= 256 * 1024**2, 'ownc_before_intent_literal_root_memory_reserve')
        work.mkdir(mode=0o700)
        for name in ('tmp', 'cache', 'config', 'runtime', 'output'):
            (work / name).mkdir(mode=0o700)
        work_scope = host_work_scope(work)
        start = time.monotonic()
        hardend = start + plan['budgets']['wall_seconds']
        deadline = start + plan['budgets']['wall_seconds'] - plan['budgets']['cleanup_seconds']
        paper, gpgme = build_bundles(plan, prepared, ns, operation_id=invocation['operation_id'],
                                    nonce=invocation['nonce'], deadline=deadline)
        paper_ref = put(work / 'helper-runtime.json', paper)
        gpgme_ref = put(work / 'output/observer-gpgme-engine-init-bundle.json', gpgme)
        job = {'schema': 'frw.own-held-font-fixture-job.v1', 'prepared_ref': plan['prepared_ref'],
            'operation_id': invocation['operation_id'], 'nonce': invocation['nonce'],
            'deadline_monotonic': deadline, 'bundle_ref': dict(paper_ref, path=WORK + '/helper-runtime.json'),
            'gpgme_bundle_ref': dict(gpgme_ref, path=gpgme['runtime']['bundle_path']),
            'target_environment': plan['target_environment'],
            'startup_deadline_monotonic': min(deadline, start + plan['budgets']['startup_seconds'])}
        job_ref = put(work / 'held-fixture-job.json', job)
        argv = namespace_argv(plan, builder, work=work,
                              job_ref=dict(job_ref, path=WORK + '/held-fixture-job.json'))
        put(op / 'Root-intent-before-once.json', {'plan_ref': plan_ref, 'invocation_ref': invocation_ref,
            'operation_id': invocation['operation_id'], 'nonce': invocation['nonce'], 'unit': unit,
            'scope': SCOPE, 'started_monotonic': start, 'deadline_monotonic': deadline,
            'pre_effect_SELF_plus_CHILDREN_lifetime_peak_bytes': outside_memory(), 'budgets': plan['budgets']})
        put(op / 'consumed-once.json', {'unit': unit, 'operation_id': invocation['operation_id'],
            'nonce': invocation['nonce'], 'intent': SCOPE, 'started_monotonic': start})
        consumed = True
        try:
            backend.launch(unit, argv, plan['budgets'])
        except Exception as exc:
            events.append({'phase': 'LAUNCH_RESPONSE_UNKNOWN_NO_RETRY', 'exception_class': type(exc).__name__})
        host_binding = None
        supervisor = None
        def emit(event):
            events.append(event)
            for proc in event.get('processes', []):
                if 'start_ticks' in proc:
                    known[str(proc['pid'])] = proc
        def release(s, cg, processes):
            nonlocal host_binding, supervisor
            if s['ActiveState'] not in ('active', 'activating') or not cg['exists'] or not cg['pids']:
                return
            unit_path = work / 'unit-release.json'
            if not unit_path.exists():
                candidates = [p for p in processes if p.get('executable') == plan['tools']['python']['path']]
                need(len(candidates) <= 1, 'ownc_multiple_python_before_unit_release')
                if not candidates:
                    return
                supervisor = candidates[0]
                need(supervisor['nspid'][-1] != 1, 'ownc_supervisor_must_not_claim_namespace_reaper')
                need(time.monotonic() < min(deadline, start + plan['budgets']['startup_seconds']),
                     'ownc_original_startup_deadline_before_unit_release')
                need(outside_memory() <= 256 * 1024**2, 'ownc_unit_release_literal_root_memory_reserve')
                put(unit_path, {'operation_id': invocation['operation_id'], 'nonce': invocation['nonce'],
                    'stage': 'ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED', 'unit': unit,
                    'invocation_id': s['InvocationID'], 'cgroup_path': cg['path'],
                    'namespace_supervisor_host_identity': supervisor})
            ready_path = work / 'office-ready.json'
            if not ready_path.exists() or (work / 'office-release.json').exists():
                return
            ready, office, gdb = read_ready(work_scope, runtime_plan, processes,
                deadline=min(deadline, start + plan['budgets']['startup_seconds']))
            need(base.proc_identity(office['pid']) == office and base.proc_identity(gdb['pid']) == gdb,
                 'ownc_process_changed_before_host_release')
            actual_sha, _ = base.stream_image_digest(Path('/proc') / str(office['pid']) / 'exe')
            need(actual_sha == prepared['target_ref']['sha256'], 'ownc_actual_host_target_image_pin')
            need(office['executable'] == prepared['target_ref']['path']
                 and gdb['executable'] == plan['tools']['gdb']['path'], 'ownc_actual_host_executables')
            fresh = backend.snapshot_cgroup(cg['path'])
            need(fresh['exists'] and fresh['inode'] == cg['inode']
                 and office['pid'] in fresh['pids'] and gdb['pid'] in fresh['pids'],
                 'ownc_cgroup_changed_before_host_release')
            base.active_budget(plan['budgets'], fresh, elapsed=time.monotonic() - start, outside_cpu=outside_cpu())
            need(outside_memory() <= 256 * 1024**2, 'ownc_office_release_literal_root_memory_reserve')
            reaper = base.observe_gpgme_namespace_reaper(runtime_plan, office, processes)
            need(reaper['pid'] != supervisor['pid'], 'ownc_reaper_is_not_python_supervisor')
            witness = base.observe_gpgme_collector_witness(runtime_plan, office, gdb, fresh, deadline)
            stopped = observe_stopped_target(base, office)
            need(time.monotonic() < min(deadline, start + plan['budgets']['startup_seconds'])
                 and outside_memory() <= 256 * 1024**2, 'ownc_budget_changed_before_custody_publication')
            base.active_budget(plan['budgets'], fresh, elapsed=time.monotonic() - start, outside_cpu=outside_cpu())
            host_binding = {'office': office, 'gdb': gdb, 'unit': unit, 'invocation_id': s['InvocationID'],
                'cgroup': fresh, 'native_process': ready['native_process'], 'native_symbols': None,
                'namespace_reaper': reaper, 'fixture_stop': stopped,
                'symbol_binding': {'semantics': 'EXPLICIT_INERT_OWN_C_SCOPE_NO_OFFICE_NATIVE_SYMBOLS',
                    'target_sha256': actual_sha, 'process_identity': office}}
            put(work / 'office-release.json', {'operation_id': invocation['operation_id'],
                'nonce': invocation['nonce'], 'stage': 'ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND',
                'native_process': ready['native_process'], 'native_symbols': None,
                'host_binding': host_binding, 'gpgme_collector_witness': witness})
            emit({'phase': 'ACTUAL_FIXTURE_HOST_CUSTODY_RELEASED', 'binding': host_binding})
        monitored = base.monitor_owned(backend, unit=unit, budget=plan['budgets'], emit=emit,
            on_sample=release, operation_started=start, outside_cpu=outside_cpu, outside_memory=outside_memory)
        result.update(status=monitored['status'], monitor=monitored, host_binding=host_binding,
                      elapsed_seconds=time.monotonic() - start)
        if monitored['status'] == 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY':
            need(host_binding is not None, 'ownc_target_custody_never_released')
        result.update(read_terminal(work_scope, runtime_plan, monitored, deadline=hardend))
        absent = {}
        for pid, identity in known.items():
            try:
                current = base.proc_identity(int(pid))
                absent[pid] = current['start_ticks'] != identity['start_ticks'] or current['boot_id'] != identity['boot_id']
            except FileNotFoundError:
                absent[pid] = True
        result['observed_owned_process_identities_absent'] = absent
        need(all(absent.values()), 'ownc_final_owned_pid_birth_still_present')
        # Reuse unchanged reviewed bytes, but recheck the source and current
        # rights at this operation's final boundary. No future fact is cached.
        inspect_plan(plan)
        last = monitored['last_snapshot']
        if last is not None:
            terminal = last[0]
            need(terminal.get('CPUUsageNSec', '').isdigit(), 'ownc_final_unit_cpu_unknown')
            need(int(terminal['CPUUsageNSec']) / 1_000_000_000 + outside_cpu()
                 <= plan['budgets']['cpu_seconds'], 'ownc_final_unit_plus_outside_cpu_budget')
            if monitored['status'] == 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY':
                need(terminal.get('MemoryPeak', '').isdigit()
                     and int(terminal['MemoryPeak']) + outside_memory() <= plan['budgets']['memory_bytes'],
                     'ownc_final_unit_peak_plus_literal_outside_peak_budget')
        need(time.monotonic() - start <= plan['budgets']['wall_seconds'], 'ownc_final_original_wall_budget')
        need(outside_memory() <= 256 * 1024**2, 'ownc_final_literal_root_memory_reserve')
        result['literal_SELF_plus_CHILDREN_lifetime_peak_bytes'] = outside_memory()
        result['events_ref'] = put(op / 'Root-events.json', events)
        put(op / 'ROOT-RESULT.json', result)
        return result
    except Exception as exc:
        result.update(status='UNKNOWN_RECONCILE_EXACT_OWNED_EFFECT' if consumed else 'REFUSED_BEFORE_INTENT',
                      exception_class=type(exc).__name__, consumed=consumed,
                      reason=str(exc) if type(exc) is RuntimeError else None)
        if not (op / 'ROOT-RESULT.json').exists():
            result['events_ref'] = put(op / 'Root-events.json', events)
            put(op / 'ROOT-RESULT.json', result)
        return result
    finally:
        fcntl.flock(slot, fcntl.LOCK_UN)
        os.close(slot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect-ref-json')
    parser.add_argument('--root-execute-plan-ref-json')
    parser.add_argument('--root-invocation-ref-json')
    args = parser.parse_args()
    if args.root_execute_plan_ref_json:
        need(args.root_invocation_ref_json is not None, 'ownc_no_implicit_root_admission')
        result = execute_once(json.loads(args.root_execute_plan_ref_json), json.loads(args.root_invocation_ref_json))
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] == 'OWNED_UNIT_EXITED_AND_CGROUP_EMPTY' else 2
    if args.inspect_ref_json:
        ref = json.loads(args.inspect_ref_json)
        inspect_plan(json_load(read_ref(ref, private=True)))
        print(json.dumps({'status': 'SOURCE_SCHEMA_JOINS_ONLY', 'runtime_admitted': False, 'actual_M': None}))
    else:
        print(json.dumps({'status': 'SOURCE_ONLY_NO_EXECUTION', 'runtime_admitted': False, 'actual_M': None}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
