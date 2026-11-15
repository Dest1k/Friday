"""Root-only namespace ownC driver; no effect on import/default invocation.

Calls the exact pinned LocalServices acquire/release and proof/pair consumers.
The view is an explicit fixture-only known-environment placeholder. This does
not exercise canonical font CAS, metric ranges, Office, UNO or restoration.
Only Root's pre-admitted unit/namespace runner may invoke --job once.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import stat
import time

WORK = Path('/tmp/friday-metric-work')


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def read_ref(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'fixture_ref_schema')
    path = Path(ref['path'])
    require(path.is_absolute() and str(path.resolve()) == str(path), 'fixture_ref_alias')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022
                and before.st_size <= 262144, 'fixture_ref_rights_bound')
        raw = os.read(fd, 262145)
        stamp = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        require(stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat()), 'fixture_ref_changed')
    finally:
        os.close(fd)
    require(len(raw) <= 262144 and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'fixture_ref_pin')
    return raw


def new_json(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def wait_boundary(ns, child, boundary, deadline):
    while True:
        require(time.monotonic() < deadline and child.poll() is None, 'fixture_boundary_deadline_or_exit')
        path = WORK / 'native-trace.json'
        if path.exists():
            trace = json.loads(ns.runtime_read(path, deadline=deadline))
            require(trace['error'] is None, 'fixture_observer_refused_before_hold')
            if trace.get('fixture_boundary') == boundary:
                require(trace['record_semantics'] == 'FIXTURE_MARKER_ONLY'
                        and len(trace['records']) == (0 if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 10),
                        'fixture_boundary_marker_count')
                return trace['process']
        time.sleep(min(.005, max(0, deadline - time.monotonic())))


def run(config_ref):
    os.umask(0o077)
    require(Path.cwd() == WORK, 'fixture_supervisor_work')
    cfg = json.loads(read_ref(config_ref))
    require(type(cfg) is dict and set(cfg) == {'schema', 'prepared_ref', 'operation_id', 'nonce',
            'deadline_monotonic', 'bundle_ref'} and cfg['schema'] == 'frw.own-held-font-fixture-job.v1',
            'fixture_job_schema')
    prepared = json.loads(read_ref(cfg['prepared_ref']))
    for key in ('source_ref', 'target_ref', 'manifest_ref', 'adapter_ref', 'policy_ref',
                'native_observer_ref', 'namespace_ref', 'gdb_driver_ref', 'supervisor_ref'):
        read_ref(prepared[key])
    require(prepared['preparation_only'] is True and prepared['runtime_executed'] is False
            and prepared['kind'] == 'OWN_POPEN_FIXTURE_ONLY', 'fixture_preparation_scope')
    require(str(Path(__file__).resolve()) == prepared['supervisor_ref']['path'], 'fixture_supervisor_pin')
    deadline = cfg['deadline_monotonic']
    require(type(deadline) in (int, float) and math.isfinite(deadline) and time.monotonic() < deadline,
            'fixture_original_deadline')
    bundle = json.loads(read_ref(cfg['bundle_ref']))
    require(bundle['runtime']['operation_id'] == cfg['operation_id']
            and bundle['runtime']['nonce'] == cfg['nonce']
            and bundle['runtime']['operation_deadline_monotonic'] == deadline
            and bundle['manifest_ref'] == prepared['manifest_ref']
            and bundle['adapter_ref'] == prepared['adapter_ref']
            and bundle['policy_ref'] == prepared['policy_ref'], 'fixture_original_bundle_binding')
    require(cfg['bundle_ref']['path'] == str(WORK / 'helper-runtime.json'), 'fixture_bundle_work_path')
    # Importing this exact module does not call its guarded production main.
    spec = importlib.util.spec_from_file_location('frw_exact_namespace_for_own_fixture', prepared['namespace_ref']['path'])
    ns = importlib.util.module_from_spec(spec)
    exec(compile(read_ref(prepared['namespace_ref']), prepared['namespace_ref']['path'], 'exec'), ns.__dict__)
    require(ns.WORK == WORK, 'fixture_namespace_work')
    services = ns.LocalServices()
    environment = {key: os.environ.get(key) for key in ns.FONT_ENV_KEYS}
    require(environment['FC_LANG'] not in ('FRW_OWN_HELD_AFTER_LOAD', 'FRW_OWN_HELD_AFTER_CLOSE'),
            'fixture_mutation_must_change_known_initial_value')
    baseline_ref = new_json(WORK / 'own-fixture-known-initial-env.json', dict(
        schema='frw.own-fixture.known-startup-environment.v1', view=dict(environment=environment),
        semantics='KNOWN_STARTUP_ENV_ONLY_NOT_CANONICAL_FONT_VIEW'))
    digest = hashlib.sha256(json.dumps(environment, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    plan = dict(operation_id=cfg['operation_id'], nonce=cfg['nonce'], observer=dict(
        load_dependency=dict(manifest=prepared['manifest_ref'], adapter=prepared['adapter_ref']),
        config=dict(target_sha256=prepared['target_ref']['sha256'])), font_view=dict(
        baseline=baseline_ref, expected_view_sha256=digest, base_view_sha256=digest))
    driver_cfg = dict(kind='OWN_POPEN_FIXTURE_ONLY', nonce=cfg['nonce'],
        phase_path=str(WORK / 'phase.json'), trace_path=str(WORK / 'native-trace.json'),
        target_path=prepared['target_ref']['path'], target_sha256=prepared['target_ref']['sha256'],
        native_observer_ref=prepared['native_observer_ref'], marker_offsets=prepared['marker_offsets'])
    driver_cfg_ref = new_json(WORK / 'held-fixture-gdb-config.json', driver_cfg)
    child_env = dict(os.environ, FRW_HELD_FIXTURE_CONFIG=driver_cfg_ref['path'],
                     FRW_NATIVE_LOAD_DEPENDENCY_REF=json.dumps(cfg['bundle_ref']), DEBUGINFOD_URLS='')
    argv = ['/usr/bin/gdb', '-nx', '-nh', '-q', '-batch', '-iex', 'maintenance set worker-threads 1',
            '-iex', 'set auto-load off', '-iex', 'set debuginfod enabled off',
            '-x', prepared['gdb_driver_ref']['path'], '--args', prepared['target_ref']['path'], repr(deadline)]
    new_json(WORK / 'own-fixture-supervisor-started.json', dict(operation_id=cfg['operation_id'],
        nonce=cfg['nonce'], variant=prepared['variant'], deadline_monotonic=deadline,
        scope='ROOT_PRE_ADMITTED_OWN_C_ONLY', actual_M=None))
    child = None
    child_identity = None
    observations = []
    result = dict(schema='frw.own-held-font-fixture-supervisor-result.v1', variant=prepared['variant'],
        operation_id=cfg['operation_id'], nonce=cfg['nonce'], deadline_monotonic=deadline,
        actual_M=None, runtime_attested=False, Office_UNO=False,
        view_semantics='FIXTURE_ONLY_KNOWN_ENV_PROJECTION_PLACEHOLDER_NO_ACTUAL_FONT_CAS',
        marker_semantics='TEN_OBSERVED_INERT_OWN_C_MARKERS_NO_NATIVE_RANGE_OR_RESTORATION',
        observations=observations, status='UNRELEASED', refusal_code=None)
    try:
        with (WORK / 'gdb.log').open('xb') as log:
            os.chmod(log.name, 0o600)
            child = services.spawn(argv, env=child_env, stdout=log)
            child_identity = services.process(child.pid)
            native = None
            for boundary in ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'):
                current = wait_boundary(ns, child, boundary, deadline)
                require(native is None or native == current, 'fixture_boundary_same_pid_birth')
                native = current
                try:
                    held = services.acquire_font_runtime(plan, native, boundary=boundary, deadline=deadline, child=child)
                except ns.Refused as exc:
                    # The real consumer refuses the same actual proof. Never
                    # manufacture a release following failed baseline validation.
                    code = str(exc)
                    expected = prepared['expected_refusal']
                    if expected is None or boundary != expected['boundary'] or code != expected['code']:
                        raise
                    paths = ns.font_runtime_paths(boundary)
                    request_raw = ns.font_runtime_read(paths['request'])
                    proof_raw = ns.font_runtime_read(paths['proof'])
                    request, proof = json.loads(request_raw), json.loads(proof_raw)
                    changed = dict(environment)
                    changed['FC_LANG'] = ('FRW_OWN_HELD_AFTER_LOAD' if boundary == 'AFTER_LOAD_BEFORE_QUERY'
                                          else 'FRW_OWN_HELD_AFTER_CLOSE')
                    # Diagnostic control only: the actual proof must contain
                    # exactly the intentional mutation. This grants no release.
                    ns.validate_font_runtime_proof(proof, request, plan=plan, native=native, environment=changed)
                    require(not paths['release'].exists() and not paths['accepted'].exists(),
                            'fixture_refusal_must_not_release')
                    result.update(status='EXPECTED_PROJECTION_REFUSAL_REQUIRES_ROOT_CGROUP_CLEANUP', refusal_code=code,
                                  refusal_boundary=boundary, intentional_FC_LANG_mutation_observed=True,
                                  refused_request_ref=dict(path=str(paths['request']), sha256=ns.sha(request_raw)),
                                  refused_proof_ref=dict(path=str(paths['proof']), sha256=ns.sha(proof_raw)),
                                  refusal_diagnostic='EXPECTED_MUTATION_ONLY_PROOF_VALID_NO_RELEASE_NO_BASELINE_ACCEPTANCE')
                    return result
                ns.validate_font_runtime_proof(held['proof'], held['request'], plan=plan,
                                               native=native, environment=environment)
                view_path = WORK / ('font-view-after-load.json' if boundary == 'AFTER_LOAD_BEFORE_QUERY'
                                    else 'font-view-after-close.json')
                view_ref = new_json(view_path, dict(schema='frw.own-fixture.font-view-placeholder.v1',
                    phase=boundary, view_sha256=digest, base_static_view_sha256=digest,
                    office_process=held['office_process'], office_font_environment=environment,
                    office_font_environment_proof=held['proof_ref'], actual_M=None,
                    semantics='FIXTURE_ONLY_KNOWN_ENV_PROJECTION_NO_ACTUAL_CANONICAL_OR_EFFECTIVE_FONT_CAS'))
                services.release_font_runtime(plan, held, view_ref=view_ref, deadline=deadline)
                paths = ns.font_runtime_paths(boundary)
                ns.validate_font_runtime_pair(*(ns.font_runtime_read(paths[key]) for key in
                    ('request', 'proof', 'release', 'accepted')), ns.font_runtime_read(view_path),
                    plan=plan, native=native, environment=environment, boundary=boundary,
                    deadline=deadline, supervisor=held['request']['supervisor'])
                observations.append(dict(boundary=boundary, proof_ref=held['proof_ref'], view_ref=view_ref,
                    exact_namespace_consumer_pair_pass=True, canonical_font_CAS_exercised=False))
                # Advance only after exact release acceptance and pair validation.
                new_json(WORK / ('own-fixture-loaded-go' if boundary == 'AFTER_LOAD_BEFORE_QUERY'
                                 else 'own-fixture-closed-go'), dict(nonce=cfg['nonce'], boundary=boundary))
            while child.poll() is None:
                require(time.monotonic() < deadline, 'fixture_original_completion_deadline')
                time.sleep(.005)
            trace = json.loads(ns.runtime_read(WORK / 'native-trace.json', deadline=deadline))
            require(prepared['expected_refusal'] is None and child.returncode == 0
                    and trace['status'] == 'COMPLETE_HELD_ENV_FIXTURE_ONLY' and trace['error'] is None
                    and trace['own_inferior_absent'] is True and len(observations) == 2,
                    'fixture_terminal_contract')
            result.update(status='COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY', gdb_exit_code=child.returncode)
            return result
    except Exception as exc:
        result.update(status='REFUSED_REQUIRES_ROOT_CGROUP_CLEANUP', exception_class=type(exc).__name__,
                      refusal_code=str(exc) if type(exc) in (RuntimeError, ns.Refused) else None)
        return result
    finally:
        # Root must retire the actual whole unit/cgroup, including every helper.
        # This birth-bound direct-GDB SIGTERM only accelerates that cleanup.
        if child is not None and child.poll() is None:
            try:
                fd = os.pidfd_open(child.pid, 0)
                try:
                    require(services.process(child.pid) == child_identity, 'fixture_cleanup_gdb_birth')
                    signal.pidfd_send_signal(fd, signal.SIGTERM, None, 0)
                finally:
                    os.close(fd)
                result['owned_GDB_SIGTERM_sent'] = True
            except Exception as exc:
                result['owned_GDB_SIGTERM_error_class'] = type(exc).__name__
        result['Root_whole_cgroup_cleanup_required'] = True
        result['Root_own_PID_absence_acceptance_required'] = True
        new_json(WORK / 'held-fixture-supervisor-result.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-ref-json')
    args = parser.parse_args()
    if args.job_ref_json:
        outcome = run(json.loads(args.job_ref_json))
        print(json.dumps(outcome, sort_keys=True))
        raise SystemExit(0 if outcome['status'] in ('COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY',
            'EXPECTED_PROJECTION_REFUSAL_REQUIRES_ROOT_CGROUP_CLEANUP') else 2)
    print(json.dumps(dict(status='SOURCE_ONLY_NO_EXECUTION')))
