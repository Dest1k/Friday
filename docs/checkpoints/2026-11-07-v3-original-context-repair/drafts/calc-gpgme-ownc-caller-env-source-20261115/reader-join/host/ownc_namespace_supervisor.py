"""Root-only namespace ownC/GpgME supervisor SOURCE; no effect on import/default invocation.

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


def environment_diagnostic(actual, expected, *, phase, nonce, exception_class):
    """Bounded key names/counts/digests only; never emit an ENV value."""
    keys = lambda names: [name if len(name) <= 128 else 'sha256:' + hashlib.sha256(
        name.encode('utf-8', 'surrogatepass')).hexdigest() for name in sorted(names)[:32]]
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    changed = {key for key in set(actual) & set(expected) if actual[key] != expected[key]}
    digest = lambda env: hashlib.sha256(json.dumps(env, sort_keys=True,
        separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    return dict(schema='frw.ownc.environment-check-metadata.v1', phase=phase, nonce=nonce,
        exception_class=exception_class, actual_count=len(actual), expected_count=len(expected),
        actual_sha256=digest(actual), expected_sha256=digest(expected),
        missing_count=len(missing), extra_count=len(extra), changed_count=len(changed),
        missing_keys=keys(missing), extra_keys=keys(extra), changed_keys=keys(changed))


def validate_supervisor_environment(actual, expected, nonce):
    mismatch = actual != expected
    try:
        new_json(WORK / 'ownc-namespace-environment-check.json', environment_diagnostic(
            actual, expected, phase='NAMESPACE_SUPERVISOR_BEFORE_GDB', nonce=nonce,
            exception_class='RuntimeError' if mismatch else None))
    except Exception:
        # A diagnostic failure cannot replace the first ENV refusal. No child
        # exists at this boundary; Root still owns the original unit cleanup.
        if mismatch:
            raise RuntimeError('fixture_supervisor_complete_environment') from None
        raise
    require(not mismatch, 'fixture_supervisor_complete_environment')


def wait_boundary(ns, child, boundary, deadline):
    while True:
        require(time.monotonic() < deadline and child.poll() is None, 'fixture_boundary_deadline_or_exit')
        path = WORK / 'native-trace.json'
        if path.exists():
            trace = json_load(ns.runtime_read(path, deadline=deadline))
            require(trace['error'] is None, 'fixture_observer_refused_before_hold')
            if trace.get('fixture_boundary') == boundary:
                require(trace['record_semantics'] == 'FIXTURE_MARKER_ONLY'
                        and len(trace['records']) == (0 if boundary in ('BEFORE_LOAD_READY', 'AFTER_LOAD_BEFORE_QUERY') else 10),
                        'fixture_boundary_marker_count')
                return trace['process']
        time.sleep(min(.005, max(0, deadline - time.monotonic())))



def json_load(raw):
    def pairs(items):
        value = dict(items)
        require(len(value) == len(items), 'fixture_duplicate_json_key')
        return value
    return json.loads(raw, object_pairs_hook=pairs)


def read_immutable(ns, path, *, deadline, child=None, font=False):
    """Bracket strict immutable guarded reads with the same absolute clock."""
    def current():
        require(time.monotonic() < deadline and (child is None or child.poll() is None),
                'fixture_existing_deadline_or_exit:' + path.name)
    current()
    raw = ns.font_runtime_read(path) if font else ns.runtime_read(path)
    value = json_load(raw)
    current()
    return raw if font else value


def wait_file(ns, path, *, deadline, child=None):
    while not path.exists():
        require(time.monotonic() < deadline and (child is None or child.poll() is None),
                'fixture_existing_deadline_or_exit:' + path.name)
        time.sleep(min(.005, max(0, deadline - time.monotonic())))
    return read_immutable(ns, path, deadline=deadline, child=child)


def validate_release(release, unit, cfg, native, office, gdb_identity, deadline):
    require(release['operation_id'] == unit['operation_id'] == cfg['operation_id']
            and release['nonce'] == unit['nonce'] == cfg['nonce']
            and release['stage'] == 'ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND'
            and release['native_process'] == native and release['native_symbols'] is None,
            'fixture_host_release_operation_or_native_join')
    host = release['host_binding']
    require(host['unit'] == unit['unit'] and host['invocation_id'] == unit['invocation_id']
            and host['native_process'] == native and host['native_symbols'] is None
            and host['office']['nspid'][-1] == native['pid']
            and host['office']['start_ticks'] == native['start_ticks']
            and host['gdb']['nspid'][-1] == native['gdb_pid']
            and host['gdb']['start_ticks'] == gdb_identity['start_ticks']
            and host['office']['ppid'] == host['gdb']['pid']
            and host['office']['namespaces'] == host['gdb']['namespaces'] == office['namespaces']
            and host['office']['boot_id'] == host['gdb']['boot_id'] == office['boot_id']
            and host['office']['cgroup'] == host['gdb']['cgroup'] == '0::' + host['cgroup']['path']
            and host['cgroup']['path'] == unit['cgroup_path'], 'fixture_host_release_exact_current_process_join')
    reaper = host['namespace_reaper']
    require(reaper['nspid'][-1] == 1 and reaper['pid'] != unit['namespace_supervisor_host_identity']['pid']
            and reaper['namespaces'] == office['namespaces'] and reaper['boot_id'] == office['boot_id']
            and reaper['cgroup'] == host['office']['cgroup'], 'fixture_actual_namespace_pid1_reaper')
    witness = release['gpgme_collector_witness']
    require(type(witness) is dict and set(witness) == {'schema', 'operation_id', 'nonce',
        'deadline_monotonic', 'uid_projection', 'private_roots', 'cgroup'}
        and witness['schema'] == 'frw.calc.gpgme-collector-host-witness.v1'
        and witness['operation_id'] == cfg['operation_id'] and witness['nonce'] == cfg['nonce']
        and witness['deadline_monotonic'] == deadline and time.monotonic() < deadline,
        'fixture_original_host_witness_before_target_continue')


def native_refusal_trace(value, nonce):
    """Only a same-operation native first-error authorizes its finally wait."""
    return (type(value) is dict and value.get('kind') == 'OWN_POPEN_FIXTURE_ONLY'
            and value.get('nonce') == nonce and value.get('status') == 'REFUSED'
            and type(value.get('error')) is str and bool(value['error']))


def run(config_ref):
    os.umask(0o077)
    require(Path.cwd() == WORK, 'fixture_supervisor_work')
    cfg = json.loads(read_ref(config_ref))
    require(type(cfg) is dict and set(cfg) == {'schema', 'prepared_ref', 'operation_id', 'nonce',
            'deadline_monotonic', 'bundle_ref', 'gpgme_bundle_ref', 'target_environment', 'startup_deadline_monotonic'} and cfg['schema'] == 'frw.own-held-font-fixture-job.v1',
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
    validate_supervisor_environment(dict(os.environ), cfg['target_environment'], cfg['nonce'])
    gpgme_bundle = json.loads(read_ref(cfg['gpgme_bundle_ref']))
    modules = ns.gpgme_sources(prepared['gpgme_binding'])
    validator = modules['validator']
    gpgme_manifest = json.loads(read_ref(prepared['gpgme_binding']['manifest']))
    validator.validate_runtime(gpgme_bundle['runtime'], manifest_ref=prepared['gpgme_binding']['manifest'],
                               paper_runtime=bundle['runtime'])
    validator.validate_bundle(gpgme_bundle, gpgme_manifest, modules['policy'], modules['collector'])
    require(cfg['gpgme_bundle_ref']['path'] == str(WORK / 'output/observer-gpgme-engine-init-bundle.json')
            and gpgme_bundle['runtime']['operation_id'] == cfg['operation_id']
            and gpgme_bundle['runtime']['nonce'] == cfg['nonce']
            and gpgme_bundle['runtime']['operation_deadline_monotonic'] == deadline,
            'fixture_gpgme_original_operation_binding')
    paper_policy = {'__name__': 'frw_exact_fixture_paper_policy', '__file__': prepared['policy_ref']['path']}
    exec(compile(read_ref(prepared['policy_ref']), prepared['policy_ref']['path'], 'exec'), paper_policy)
    paper_manifest = json.loads(read_ref(prepared['manifest_ref']))
    paper_policy['validate_manifest'](paper_manifest, fixture=True)
    paper_policy['validate_runtime'](bundle['runtime'], paper_manifest)
    require(type(cfg['startup_deadline_monotonic']) in (int, float)
            and math.isfinite(cfg['startup_deadline_monotonic'])
            and time.monotonic() < cfg['startup_deadline_monotonic'] <= deadline, 'fixture_startup_budget')
    unit_release = wait_file(ns, WORK / 'unit-release.json', deadline=cfg['startup_deadline_monotonic'])
    require(unit_release['operation_id'] == cfg['operation_id'] and unit_release['nonce'] == cfg['nonce']
            and unit_release['stage'] == 'ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED', 'fixture_actual_unit_release')
    supervisor_now = services.process(os.getpid())
    host_supervisor = unit_release['namespace_supervisor_host_identity']
    require(host_supervisor['nspid'][-1] == os.getpid()
            and host_supervisor['start_ticks'] == supervisor_now['start_ticks']
            and host_supervisor['namespaces'] == supervisor_now['namespaces']
            and host_supervisor['boot_id'] == supervisor_now['boot_id'], 'fixture_actual_supervisor_host_binding')
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
        native_observer_ref=prepared['native_observer_ref'], marker_offsets=prepared['marker_offsets'], event_limit=8192,
        target_environment=cfg['target_environment'])
    driver_cfg_ref = new_json(WORK / 'held-fixture-gdb-config.json', driver_cfg)
    child_env = dict(cfg['target_environment'], FRW_HELD_FIXTURE_CONFIG=driver_cfg_ref['path'],
                     FRW_NATIVE_LOAD_DEPENDENCY_REF=json.dumps(cfg['bundle_ref']),
                     FRW_NATIVE_GPGME_ENGINE_INIT_REF=json.dumps(cfg['gpgme_bundle_ref']),
                     FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE=gpgme_bundle['evidence_path'])
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
            require(time.monotonic() < cfg['startup_deadline_monotonic'], 'fixture_original_startup_before_gdb')
            child = services.spawn(argv, env=child_env, stdout=log)
            child_identity = services.process(child.pid)
            ready_deadline = cfg['startup_deadline_monotonic']
            while True:
                require(time.monotonic() < ready_deadline and child.poll() is None,
                        'fixture_ready_deadline_or_gdb_exit')
                if (WORK / 'native-trace.json').exists():
                    ready_trace = json_load(ns.runtime_read(WORK / 'native-trace.json', deadline=ready_deadline))
                    require(ready_trace['nonce'] == cfg['nonce'] and ready_trace['error'] is None,
                            'fixture_ready_driver_refusal')
                    if ready_trace['status'] == 'READY_UNRELEASED':
                        break
                time.sleep(.005)
            original = ready_trace['process']
            require(ready_trace['symbols'] is None and ready_trace['fixture_boundary'] == 'BEFORE_LOAD_READY'
                    and original['gdb_pid'] == child.pid and original['inferior'] == 1,
                    'fixture_ready_inert_c_scope')
            office = services.process(original['pid'])
            require(office['namespace_pid'] == original['pid'] and office['start_ticks'] == original['start_ticks']
                    and office['ppid'] == child.pid
                    and office['executable_sha256'] == prepared['target_ref']['sha256'],
                    'fixture_ready_actual_owned_target')
            new_json(WORK / 'office-ready.json', dict(schema='frw.calc.office-ready.v1',
                operation_id=cfg['operation_id'], nonce=cfg['nonce'], native_process=original,
                native_symbols=None, office_identity=office, gdb_identity=child_identity,
                scope='OWN_C_FIXTURE_ONLY'))
            release = wait_file(ns, WORK / 'office-release.json', deadline=ready_deadline, child=child)
            validate_release(release, unit_release, cfg, original, office, child_identity, deadline)
            require(services.process(original['pid']) == office
                    and services.process(child.pid) == child_identity, 'fixture_ready_birth_changed_before_go')
            # The driver is stopped inside fixture_ready. This is the only
            # release marker, and LOAD_OPEN is still absent until this go.
            require(not (WORK / 'load-dependency.json').exists(), 'fixture_load_started_before_host_witness')
            require(time.monotonic() < ready_deadline and child.poll() is None,
                    'fixture_original_startup_before_ready_go')
            new_json(WORK / 'own-fixture-ready-go', dict(nonce=cfg['nonce'], boundary='BEFORE_LOAD_READY'))
            result['actual_host_release_validated'] = True
            native = None
            for boundary in ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'):
                current = wait_boundary(ns, child, boundary, deadline)
                require(native is None or native == current, 'fixture_boundary_same_pid_birth')
                native = current
                # The second point follows the selected worker-cached getter;
                # validate that changed trace at its own nearest consumer too.
                current_trace = json_load(ns.runtime_read(WORK / 'native-trace.json', deadline=deadline))
                require(time.monotonic() < deadline, 'fixture_original_closure_deadline')
                ns.check_load_dependency_closed(current_trace, bundle['runtime'], paper_policy, current)
                reaper_now = services.process(1)
                require(reaper_now['namespace_pid'] != os.getpid(), 'fixture_namespace_reaper_not_supervisor')
                ns.check_gpgme_engine_init_closed(current_trace, gpgme_bundle, validator, gpgme_manifest,
                                                  current, current_reaper=reaper_now)
                result.setdefault('actual_combined_load_closure_checked_at', []).append(boundary)
                require(time.monotonic() < deadline, 'fixture_original_closure_deadline')
                held = services.acquire_font_runtime(plan, native, boundary=boundary, deadline=deadline, child=child)
                require(time.monotonic() < deadline, 'fixture_original_proof_deadline')
                ns.validate_font_runtime_proof(held['proof'], held['request'], plan=plan,
                                               native=native, environment=environment)
                view_path = WORK / ('font-view-after-load.json' if boundary == 'AFTER_LOAD_BEFORE_QUERY'
                                    else 'font-view-after-close.json')
                view_ref = new_json(view_path, dict(schema='frw.own-fixture.font-view-placeholder.v1',
                    phase=boundary, view_sha256=digest, base_static_view_sha256=digest,
                    office_process=held['office_process'], office_font_environment=environment,
                    office_font_environment_proof=held['proof_ref'], actual_M=None,
                    semantics='FIXTURE_ONLY_KNOWN_ENV_PROJECTION_NO_ACTUAL_CANONICAL_OR_EFFECTIVE_FONT_CAS'))
                require(time.monotonic() < deadline, 'fixture_original_release_deadline')
                services.release_font_runtime(plan, held, view_ref=view_ref, deadline=deadline)
                require(time.monotonic() < deadline, 'fixture_original_release_deadline')
                paths = ns.font_runtime_paths(boundary)
                ns.validate_font_runtime_pair(*(read_immutable(ns, paths[key], deadline=deadline, child=child, font=True)
                    for key in ('request', 'proof', 'release', 'accepted')),
                    read_immutable(ns, view_path, deadline=deadline, child=child, font=True),
                    plan=plan, native=native, environment=environment, boundary=boundary,
                    deadline=deadline, supervisor=held['request']['supervisor'])
                require(time.monotonic() < deadline, 'fixture_original_pair_deadline')
                observations.append(dict(boundary=boundary, proof_ref=held['proof_ref'], view_ref=view_ref,
                    exact_namespace_consumer_pair_pass=True, canonical_font_CAS_exercised=False))
                # Advance only after exact release acceptance and pair validation.
                new_json(WORK / ('own-fixture-loaded-go' if boundary == 'AFTER_LOAD_BEFORE_QUERY'
                                 else 'own-fixture-closed-go'), dict(nonce=cfg['nonce'], boundary=boundary))
            while child.poll() is None:
                require(time.monotonic() < deadline, 'fixture_original_completion_deadline')
                time.sleep(.005)
            trace = json_load(ns.runtime_read(WORK / 'native-trace.json', deadline=deadline))
            require(prepared.get('expected_refusal') is None and child.returncode == 0
                    and trace['status'] == 'COMPLETE_HELD_ENV_FIXTURE_ONLY' and trace['error'] is None
                    and trace['own_inferior_absent'] is True and len(observations) == 2,
                    'fixture_terminal_contract')
            result.update(status='COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY', gdb_exit_code=child.returncode)
            return result
    except Exception as exc:
        result.update(status='REFUSED_REQUIRES_ROOT_CGROUP_CLEANUP', exception_class=type(exc).__name__,
                      refusal_code=str(exc) if type(exc) in (RuntimeError, ns.Refused) else None)
        # A confirmed native fail() publishes an early first-error trace while
        # stopped. Preserve its mandatory diagnostic/finally, on the same clock.
        # A supervisor-only fault grants no wait: retain immediate owned-GDB
        # SIGTERM below, with Root whole-cgroup cleanup still authoritative.
        native_refused = False
        try:
            refusal_trace = json_load(ns.runtime_read(WORK / 'native-trace.json', deadline=deadline))
            native_refused = native_refusal_trace(refusal_trace, cfg['nonce'])
        except Exception:
            pass  # Unknown/stale trace cannot authorize delaying owned cleanup.
        result['native_finally_wait_authorized'] = native_refused
        while native_refused and child is not None and child.poll() is None and time.monotonic() < deadline:
            time.sleep(min(.005, max(0, deadline - time.monotonic())))
        if child is not None:
            result['gdb_exit_code'] = child.poll()
        # Preserve exact native guard reason/stage and prior paper evidence for
        # Root's separate negative-control assessment. Arbitrary refusal is no PASS.
        if (WORK / 'native-trace.json').exists():
            try:
                failed_trace = json_load(ns.runtime_read(WORK / 'native-trace.json', deadline=deadline))
                require(failed_trace['kind'] == 'OWN_POPEN_FIXTURE_ONLY' and failed_trace['nonce'] == cfg['nonce'],
                        'fixture_refusal_trace_operation_join')
                result['observed_driver_error'] = failed_trace.get('error')
                result['observed_driver_status'] = failed_trace.get('status')
                result['observed_paper_evidence'] = failed_trace.get('load_dependency')
                result['observed_gpgme_evidence'] = failed_trace.get('gpgme_engine_init')
                result['observed_refusal_stop'] = failed_trace.get('ownc_refusal_stop')
                result['negative_control_acceptance'] = 'PENDING_ROOT_ACTUAL_STAGE_AND_CHILD_CUSTODY'
            except Exception as trace_error:
                result['trace_read_error_class'] = type(trace_error).__name__
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
        raise SystemExit(0 if outcome['status'] == 'COMPLETE_TWO_HELD_POINTS_FIXTURE_ONLY' else 2)
    print(json.dumps(dict(status='SOURCE_ONLY_NO_EXECUTION')))
