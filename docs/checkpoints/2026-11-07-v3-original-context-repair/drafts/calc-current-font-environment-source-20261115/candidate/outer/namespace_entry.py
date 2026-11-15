"""One finite namespace supervisor SOURCE. Import/default do not start children.

Only outer_runner's separately admitted transient unit may call --job. Injected
LocalServices replacements are Python test APIs, never JSON production options.
No attach, generic process signal, global service or standalone self-admission.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import resource
import re
import math
import signal
import stat
import subprocess
import time
import types
from urllib.parse import unquote, urlparse

WORK = Path('/tmp/friday-metric-work')
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'
FONT_ENV_KEYS = ('HOME', 'TMPDIR', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
    'FONTCONFIG_FILE', 'FONTCONFIG_PATH', 'FONTCONFIG_SYSROOT', 'FC_LANG', 'LANG', 'LC_ALL',
    'SAL_FONTPATH', 'SAL_USE_VCLPLUGIN', 'LD_LIBRARY_PATH', 'URE_BOOTSTRAP')


def font_runtime_paths(boundary):
    need(boundary in ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'), 'font_runtime_boundary')
    tag = 'loaded' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'closed'
    return {kind: WORK / ('font-runtime-' + tag + '-' + kind + '.json')
            for kind in ('request', 'proof', 'release', 'accepted')}


def font_runtime_read(path):
    path = Path(path)
    need(path.parent == WORK and not path.is_symlink(), 'font_runtime_exact_work_file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_nlink == 1
             and stat.S_IMODE(before.st_mode) == 0o600 and before.st_size <= 32768,
             'font_runtime_file_rights_bound')
        raw = os.read(fd, 32769)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        need(len(raw) <= 32768 and stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat()),
             'font_runtime_file_changed')
    finally:
        os.close(fd)
    return raw


def validate_font_projection(rows, environment, *, helper=False):
    need(type(environment) is dict and set(environment) == set(FONT_ENV_KEYS)
         and all(v is None or type(v) is str for v in environment.values()), 'font_runtime_baseline_exact15')
    need(type(rows) is list and len(rows) == 15 and [r.get('key') for r in rows if type(r) is dict]
         == list(FONT_ENV_KEYS), 'font_runtime_projection_exact15')
    for row in rows:
        expected = sha(environment[row['key']].encode()) if environment[row['key']] is not None else None
        fields = ('initial_value_sha256', 'runtime_value_sha256') if helper else ('value_sha256',)
        need(set(row) == {'key', *fields} and all(row[field] == expected for field in fields),
             'font_runtime_projection_changed')


def validate_font_runtime_proof(proof, request, *, plan, native, environment):
    need(type(request) is dict and set(request) == {'schema', 'operation_id', 'nonce', 'boundary', 'sequence',
         'process', 'supervisor', 'deadline_monotonic', 'requested_monotonic'}
         and request['schema'] == 'frw.calc.font-runtime-request.v1', 'font_runtime_request_schema')
    boundary = request['boundary']
    paths = font_runtime_paths(boundary)
    sequence = 0 if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 1
    need(type(request['sequence']) is int and request['sequence'] == sequence
         and type(request['supervisor']) is dict and set(request['supervisor']) == {'pid', 'ppid', 'start_ticks'}
         and all(type(v) is int for v in request['supervisor'].values())
         and request['supervisor']['pid'] > 0 and request['supervisor']['start_ticks'] > 0
         and request['supervisor']['ppid'] >= 0
         and all(type(request[k]) in (int, float) and math.isfinite(request[k])
                 for k in ('deadline_monotonic', 'requested_monotonic'))
         and 0 < request['requested_monotonic'] < request['deadline_monotonic'], 'font_runtime_request_values')
    need(type(proof) is dict and set(proof) == {'schema', 'operation_id', 'nonce', 'boundary', 'sequence',
         'process', 'supervisor', 'request_ref', 'phase', 'records_count', 'stopped_thread_count',
         'source_class', 'adapter_ref', 'libc_sha256', 'font_environment', 'scope', 'actual_M', 'runtime_attested'},
         'font_runtime_proof_schema')
    binding = plan['observer']['load_dependency']
    manifest = json.loads(read_ref(binding['manifest']))
    expected_phase = dict(nonce=plan['nonce'], phase='IDLE' if sequence == 0 else 'CLOSED', index=None, digit=None)
    need(proof['schema'] == 'frw.calc.current-font-environment.v1'
         and proof['operation_id'] == request['operation_id'] == plan['operation_id']
         and proof['nonce'] == request['nonce'] == plan['nonce']
         and proof['boundary'] == boundary and type(proof['sequence']) is int and proof['sequence'] == sequence
         and proof['process'] == request['process'] == native
         and proof['supervisor'] == request['supervisor'] and proof['phase'] == expected_phase
         and type(proof['records_count']) is int and proof['records_count'] == sequence * 10
         and type(proof['stopped_thread_count']) is int and 1 <= proof['stopped_thread_count'] <= 512
         and proof['source_class'] == 'PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON'
         and proof['adapter_ref'] == binding['adapter']
         and proof['libc_sha256'] == manifest['images']['libc']['sha256']
         and proof['scope'] == 'THIS_ALL_STOP_POINT_ONLY_NO_CONTINUOUS_ENVIRONMENT_CLAIM'
         and proof['actual_M'] is None and proof['runtime_attested'] is False, 'font_runtime_proof_binding')
    need(type(proof['request_ref']) is dict and set(proof['request_ref']) == {'path', 'sha256'}
         and proof['request_ref']['path'] == str(paths['request'])
         and type(proof['request_ref']['sha256']) is str
         and re.fullmatch('[0-9a-f]{64}', proof['request_ref']['sha256']), 'font_runtime_request_ref')
    validate_font_projection(proof['font_environment'], environment)
    return proof


def validate_font_runtime_pair(request_raw, proof_raw, release_raw, accepted_raw, view_raw, *, plan, native,
                               environment, boundary, deadline=None, supervisor=None):
    need(all(type(raw) is bytes and len(raw) <= 32768 for raw in
             (request_raw, proof_raw, release_raw, accepted_raw, view_raw)), 'font_runtime_pair_bound')
    request, proof, release, accepted, view = map(json.loads, (request_raw, proof_raw, release_raw, accepted_raw, view_raw))
    validate_font_runtime_proof(proof, request, plan=plan, native=native, environment=environment)
    paths = font_runtime_paths(boundary)
    proof_ref = {'path': str(paths['proof']), 'sha256': sha(proof_raw)}
    request_ref = {'path': str(paths['request']), 'sha256': sha(request_raw)}
    view_path = WORK / ('font-view-after-load.json' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'font-view-after-close.json')
    expected_release = dict(schema='frw.calc.font-runtime-release.v1',
        **{k: request[k] for k in ('operation_id', 'nonce', 'boundary', 'sequence', 'process')},
        request_ref=request_ref, proof_ref=proof_ref, font_view_ref={'path': str(view_path), 'sha256': sha(view_raw)})
    expected_accepted = dict(schema='frw.calc.font-runtime-accepted.v1',
        **{key: request[key] for key in ('operation_id', 'nonce', 'boundary', 'sequence', 'process')},
        release_ref={'path': str(paths['release']), 'sha256': sha(release_raw)},
        status='HELD_STOP_RELEASE_VALIDATED_NO_RESUME_CLAIM')
    office = view.get('office_process')
    need(request['boundary'] == boundary and proof['request_ref'] == request_ref and release == expected_release
         and accepted == expected_accepted
         and view['phase'] == boundary and view['view_sha256'] == plan['font_view']['expected_view_sha256']
         and view['base_static_view_sha256'] == plan['font_view']['base_view_sha256']
         and view['office_font_environment'] == environment and view['office_font_environment_proof'] == proof_ref
         and type(office) is dict and office['namespace_pid'] == native['pid']
         and office['start_ticks'] == native['start_ticks'] and office['ppid'] == native['gdb_pid']
         and (deadline is None or request['deadline_monotonic'] == deadline)
         and (supervisor is None or request['supervisor'] == supervisor), 'font_runtime_pair_CAS_binding')
    return proof_ref


class Refused(RuntimeError):
    pass


def need(value, code):
    if not value:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, value):
    path = Path(path)
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    tmp = path.with_name(path.name + '.pending')
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, path)
    return {'path': str(path), 'sha256': sha(raw)}


def runtime_read(path):
    path = Path(path)
    need(path.parent == WORK and path.name and not path.is_symlink(), 'exact_work_file_required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1
             and not st.st_mode & 0o077, 'runtime_file_rights')
        return f.read()


def read_ref(ref):
    path = Path(ref['path'])
    need(path.is_absolute() and '..' not in path.parts and str(path.resolve()) == str(path), 'source_path_alias')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid in (0, os.getuid())
             and not st.st_mode & 0o022, 'pinned_source_rights')
        raw = f.read()
    need(sha(raw) == ref['sha256'], 'pinned_source_changed')
    return raw


def process_snapshot(pid):
    root = Path('/proc') / str(pid)
    stat_fields = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    status = (root / 'status').read_text().splitlines()
    uid = next(line.split()[1:] for line in status if line.startswith('Uid:'))
    need(all(int(x) == os.getuid() for x in uid), 'foreign_process_uid')
    result = {'namespace_pid': pid, 'start_ticks': int(stat_fields[19]), 'ppid': int(stat_fields[1]),
              'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'executable_path': os.readlink(root / 'exe'),
              'executable_sha256': sha((root / 'exe').read_bytes()),
              'namespaces': {name: os.readlink(root / 'ns' / name) for name in ('pid', 'mnt', 'net', 'user')},
              'nspid': next((list(map(int, line.split()[1:])) for line in status if line.startswith('NSpid:')), []),
              'cgroup': (root / 'cgroup').read_text().strip()}
    need(int((root / 'stat').read_text().rsplit(')', 1)[1].split()[19]) == result['start_ticks'],
         'process_birth_changed')
    return result


def address_space_memory(pid):
    values = {}
    for line in (Path('/proc') / str(pid) / 'status').read_text().splitlines():
        if line.startswith(('VmRSS:', 'VmHWM:')):
            key, value, unit = line.split()
            need(unit == 'kB', 'current_address_space_RSS_unit_unknown')
            values[key.rstrip(':')] = int(value) * 1024
    need(set(values) == {'VmRSS', 'VmHWM'} and 0 <= values['VmRSS'] <= values['VmHWM'],
         'current_address_space_RSS_unknown')
    return values


class LocalServices:
    """Concrete OS implementation; source-only replay injects all effect methods."""
    source_only = False
    now = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)

    def spawn(self, argv, *, env, stdout):
        # DEVNULL opens O_RDWR in Python; the reviewed input contract is a
        # read-only null descriptor. Preserve argv/env/stdio/child ownership.
        with open(os.devnull, 'rb') as input_null:
            return subprocess.Popen(argv, stdin=input_null, stdout=stdout, stderr=subprocess.STDOUT,
                                    env=env, start_new_session=True, close_fds=True)

    def process(self, pid):
        return process_snapshot(pid)

    def acquire_font_runtime(self, plan, native, *, boundary, deadline, child):
        """Exact owned pidfd only; no fallback to kill(PID), attach or a later clock."""
        paths = font_runtime_paths(boundary)
        need(all(not os.path.lexists(path) for path in paths.values()), 'font_runtime_prefilled_or_duplicate')
        view_path = WORK / ('font-view-after-load.json' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'font-view-after-close.json')
        need(not os.path.lexists(view_path), 'font_runtime_prefilled_future_view')
        expected_phase = dict(nonce=plan['nonce'], phase='IDLE' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'CLOSED',
                              index=None, digit=None)
        need(json.loads(runtime_read(WORK / 'phase.json')) == expected_phase, 'font_runtime_request_phase')
        runtime = json.loads(runtime_read(WORK / 'helper-runtime.json'))['runtime']
        need(runtime['operation_id'] == plan['operation_id'] and runtime['nonce'] == plan['nonce']
             and runtime['operation_deadline_monotonic'] == deadline and self.now() < deadline,
             'font_runtime_request_original_deadline')
        before = self.process(native['pid'])
        need(before['namespace_pid'] == native['pid'] and before['start_ticks'] == native['start_ticks']
             and before['ppid'] == native['gdb_pid'] == child.pid
             and before['executable_sha256'] == plan['observer']['config']['target_sha256'],
             'font_runtime_request_owned_process')
        # pidfd prevents PID reuse between the fresh birth checks and signal.
        fd = os.pidfd_open(native['pid'], 0)
        try:
            need(self.process(native['pid']) == before and child.poll() is None, 'font_runtime_pidfd_birth_changed')
            fields = (Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split())
            supervisor = {'pid': os.getpid(), 'ppid': int(fields[1]), 'start_ticks': int(fields[19])}
            request = dict(schema='frw.calc.font-runtime-request.v1', operation_id=plan['operation_id'],
                nonce=plan['nonce'], boundary=boundary, sequence=0 if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 1,
                process=native, supervisor=supervisor, deadline_monotonic=deadline, requested_monotonic=self.now())
            request_ref = atomic(paths['request'], request)
            need(self.now() < deadline and self.process(native['pid']) == before,
                 'font_runtime_pre_signal_birth_or_deadline')
            signal.pidfd_send_signal(fd, signal.SIGSTOP, None, 0)
        finally:
            os.close(fd)
        while not paths['proof'].exists():
            need(self.now() < deadline and child.poll() is None, 'font_runtime_proof_deadline_or_GDB_exit')
            trace = json.loads(runtime_read(WORK / 'native-trace.json'))
            need(trace['error'] is None and trace['process'] == native, 'font_runtime_observer_refused')
            self.sleep(min(0.02, max(0, deadline - self.now())))
        raw = font_runtime_read(paths['proof'])
        need(sha(font_runtime_read(paths['request'])) == request_ref['sha256'],
             'font_runtime_proof_bound_or_request_changed')
        proof = json.loads(raw)
        baseline = json.loads(read_ref(plan['font_view']['baseline']))
        validate_font_runtime_proof(proof, request, plan=plan, native=native,
                                    environment=baseline['view']['environment'])
        need(proof['request_ref'] == request_ref and self.process(native['pid']) == before,
             'font_runtime_proof_request_or_birth_changed')
        return dict(request=request, request_ref=request_ref, proof=proof,
                    proof_ref={'path': str(paths['proof']), 'sha256': sha(raw)}, office_process=before)

    def release_font_runtime(self, plan, held, *, view_ref, deadline):
        request = held['request']
        paths = font_runtime_paths(request['boundary'])
        need(self.now() < deadline == request['deadline_monotonic']
             and self.process(request['process']['pid']) == held['office_process']
             and sha(font_runtime_read(paths['request'])) == held['request_ref']['sha256']
             and sha(font_runtime_read(paths['proof'])) == held['proof_ref']['sha256']
             and not os.path.lexists(paths['release']), 'font_runtime_release_CAS_or_deadline')
        release_ref = atomic(paths['release'], dict(schema='frw.calc.font-runtime-release.v1',
            **{key: request[key] for key in ('operation_id', 'nonce', 'boundary', 'sequence', 'process')},
            request_ref=held['request_ref'], proof_ref=held['proof_ref'], font_view_ref=view_ref))
        while not paths['accepted'].exists():
            need(self.now() < deadline, 'font_runtime_release_acceptance_original_deadline')
            trace = json.loads(runtime_read(WORK / 'native-trace.json'))
            need(trace['error'] is None and trace['process'] == request['process'], 'font_runtime_release_observer_refused')
            self.sleep(min(0.02, max(0, deadline - self.now())))
        accepted = json.loads(font_runtime_read(paths['accepted']))
        expected = dict(schema='frw.calc.font-runtime-accepted.v1',
            **{key: request[key] for key in ('operation_id', 'nonce', 'boundary', 'sequence', 'process')},
            release_ref=release_ref, status='HELD_STOP_RELEASE_VALIDATED_NO_RESUME_CLAIM')
        need(accepted == expected and self.now() < deadline, 'font_runtime_release_acceptance_binding')

    def font_view_observation(self, plan, *, phase, office_pid=None, font_runtime=None):
        """Pinned Root CAS in THIS namespace; no catalog rebuild or subprocess.

        Existing outer loop observes the explicit finite phase marker and owns
        cancellation/whole-cgroup cleanup. Local postchecks refuse overscope;
        neither these observed RSS checks nor RLIMIT_AS are called a hard RSS cap.
        """
        binding = plan['font_view']
        raw = read_ref(binding['consumer'])
        namespace = {'__name__': 'frw_pinned_Root_font_CAS', '__file__': binding['consumer']['path']}
        exec(compile(raw, binding['consumer']['path'], 'exec'), namespace)
        baseline_raw = read_ref(binding['baseline'])
        need(len(baseline_raw) <= 4 * 1024**2, 'Root_font_baseline_bound')
        baseline = json.loads(baseline_raw)
        read_ref(binding['provenance_ref'])
        me = self.process(os.getpid())
        font_environment = None
        office = None
        if office_pid is not None:
            office = self.process(office_pid)
            need(office['namespaces'] == me['namespaces'] and office['boot_id'] == me['boot_id'],
                 'font_CAS_must_share_actual_Office_namespace')
            need(font_runtime is not None and font_runtime['office_process'] == office
                 and font_runtime['request']['boundary'] == phase, 'actual_runtime_font_environment_required')
            validate_font_runtime_proof(font_runtime['proof'], font_runtime['request'], plan=plan,
                native=font_runtime['request']['process'], environment=baseline['view']['environment'])
            need(sha(font_runtime_read(font_runtime_paths(phase)['proof'])) == font_runtime['proof_ref']['sha256']
                 and not os.path.lexists(font_runtime_paths(phase)['release']), 'font_runtime_CAS_not_held')
            font_environment = baseline['view']['environment']
        before_wall = self.now()
        before_cpu = time.process_time()
        ticks = (Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split())
        before_proc_cpu = (int(ticks[11]) + int(ticks[12])) / os.sysconf('SC_CLK_TCK')
        marker = {'schema': 'frw.calc.font-CAS-phase.v1', 'operation_id': plan['operation_id'],
                  'nonce': plan['nonce'], 'state': 'RUNNING', 'phase': phase,
                  'process': me, 'started_monotonic': before_wall,
                  'started_process_CPU_seconds': before_proc_cpu,
                  'limits': {'wall_seconds': 60, 'cpu_seconds': 30, 'rss_bytes': 512 * 1024**2}}
        atomic(WORK / 'font-CAS-phase.json', marker)
        try:
            derived = json.loads(read_ref(binding['derived_cache']))
            current = namespace['validate_effective_font_config_view'](baseline,
                            expected_view_digest=binding['expected_view_sha256'], derived_cache=derived)
            encoded = json.dumps(current, sort_keys=True, separators=(',', ':')).encode()
            memory = address_space_memory(os.getpid())
            rss_peak = memory['VmHWM']
            elapsed = self.now() - before_wall
            used_cpu = time.process_time() - before_cpu
            need(elapsed <= 60 and used_cpu <= 30 and rss_peak <= 512 * 1024**2
                 and len(encoded) <= 4 * 1024**2, 'font_CAS_actual_per_call_resource_bound')
            need(current['view_sha256'] == binding['expected_view_sha256']
                 and current['observation']['status'] == 'metadata_cas_pass_with_critical_rehash',
                 'Root_font_CAS_current_canonical_view_mismatch')
            need(self.process(os.getpid()) == me and (office is None or self.process(office_pid) == office),
                 'font_CAS_process_namespace_or_birth_changed')
            result = {'schema': 'frw.calc.actual-font-view-CAS.v1', 'phase': phase,
                'view_sha256': current['view_sha256'], 'consumer': binding['consumer'],
                'baseline': binding['baseline'], 'provenance_ref': binding['provenance_ref'],
                'base_static_view_sha256': binding['base_view_sha256'], 'derived_cache': binding['derived_cache'],
                'digest_kind': 'ROOT_CANONICAL_NAMESPACE_VIEW_NOT_BASELINE_FILE_SHA',
                'namespace_process': me, 'office_process': office, 'office_font_environment': font_environment,
                'office_font_environment_proof': None if font_runtime is None else font_runtime['proof_ref'],
                'observation': current['observation'], 'actual_wall_seconds': elapsed,
                'actual_process_CPU_seconds': used_cpu, 'current_address_space_peak_RSS_bytes': rss_peak,
                'current_address_space_RSS_bytes': memory['VmRSS'],
                'peak_RSS_scope': 'Conservative current address-space VmHWM; no inherited/reaped-process rusage',
                'per_call_resource_scope': 'Pinned CAS callable plus manifest serialization; phase journal IO stays under active marker/global operation clock',
                'output_bytes': len(encoded), 'actual_M': None}
            marker.update(state='COMPLETE_UNRELEASED', actual_wall_seconds=elapsed,
                          actual_process_CPU_seconds=used_cpu, lifetime_peak_RSS_bytes=rss_peak)
            return result
        except Exception as exc:
            code = str(exc).split(':', 1)[0]
            marker.update(state='REFUSED', exception_class=type(exc).__name__,
                          refusal_code=code if code.replace('_', '').isalnum() else None)
            raise
        finally:
            atomic(WORK / 'font-CAS-phase.json', marker)

    def bootstrap_absent(self, pid):
        need(not (Path('/proc') / str(pid)).exists(), 'bootstrap_child_not_absent')
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                target = os.readlink(entry / 'exe')
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
            need(target != PROGRAM + '/soffice.bin', 'bootstrap_Office_process_still_present')

    def loaded_observations(self, plan, native, *, font_runtime=None):
        pid = native['pid']
        before = self.process(pid)
        root = Path('/proc') / str(pid)
        maps = (root / 'maps').read_text().splitlines()
        mapped = sorted({line.split(maxsplit=5)[5] for line in maps if len(line.split(maxsplit=5)) == 6
                         and line.split(maxsplit=5)[5].startswith('/')})
        need(not any(p.endswith(' (deleted)') for p in mapped), 'deleted_loaded_mapping')
        env_items = (root / 'environ').read_bytes().split(b'\0')
        env = dict(item.split(b'=', 1) for item in env_items if b'=' in item)
        hashes = {}
        for role, path in plan['component_paths'].items():
            if role == 'font_config_view':
                continue
            need(path.startswith('/') and '..' not in Path(path).parts, 'component_path_alias')
            target = root / 'root' / path.lstrip('/')
            st = target.stat()
            need(stat.S_ISREG(st.st_mode) and not st.st_mode & 0o022, 'component_rights')
            hashes[role] = {'path': path, 'sha256': sha(target.read_bytes()),
                            'observation': 'ACTUAL_MAPPED_COMPONENT',
                            'mapped': path in mapped}
        font_view = self.font_view_observation(plan, phase='AFTER_LOAD_BEFORE_QUERY', office_pid=pid,
                                               font_runtime=font_runtime)
        hashes['font_config_view'] = {'path': plan['font_view']['baseline']['path'],
            'sha256': font_view['view_sha256'], 'observation': 'ACTUAL_NAMESPACE_FONT_CONFIG_CAS',
            'mapped': False, 'digest_kind': 'ROOT_CANONICAL_NAMESPACE_VIEW_NOT_BASELINE_FILE_SHA'}
        after = self.process(pid)
        need(before == after, 'loaded_process_changed_during_observation')
        return {'schema': 'frw.calc.actual-loaded-observations.v1', 'process': before,
                'components': hashes, 'mapped_paths': mapped,
                'font_view': font_view, 'bootstrap': json.loads(runtime_read(WORK / 'bootstrap-result.json')),
                'startup_environment': {k: env.get(k.encode(), b'').decode() for k in ('LANG', 'LC_ALL')},
                'observed_after': 'MODEL_LOADED'}


def bootstrap_argv(plan, *, finalize=False):
    pre = json.loads(read_ref(plan['preload']))
    args = [PROGRAM + '/soffice.bin', '-env:UserInstallation=' + pre['private_profile_url'],
            '--headless', '--invisible', '--nologo', '--norestore', '--nodefault',
            '--nofirststartwizard', '--quickstart=no']
    return args + (['--terminate_after_init'] if finalize else [])


def bootstrap_profile(plan, *, services, deadline, emit):
    """Exactly two direct own children, with first81 then profile-finalizer0.

    The first ordinary fresh startup reaches extension synchronization; source's
    restart gate skips OpenClients/event loop on the required81 path. The second
    flag returns earlier at profile finalization and is NOT a claim that it
    reaches extension synchronization. No unknown status or third child retries.
    """
    basis = json.loads(read_ref(plan['bootstrap']['basis']))
    need(basis['schema'] == 'frw.calc.fresh-profile-bootstrap-basis.v1'
         and basis['sequence'] == ['FRESH_ORDINARY_REQUIRE_81', 'SAME_PROFILE_TERMINATE_AFTER_INIT_REQUIRE_0']
         and basis['max_children'] == 2, 'bootstrap_source_basis_UNBOUND')
    end = min(deadline, services.now() + plan['budgets']['startup_seconds'])
    pre = json.loads(read_ref(plan['preload']))
    need(pre['private_profile_url'] == (WORK / 'profile').as_uri(), 'bootstrap_exact_fresh_operation_profile')
    need(list((WORK / 'profile').iterdir()) == [], 'bootstrap_profile_must_start_empty')
    need(not (WORK / 'profile/user/extensions/buildid').exists(), 'bootstrap_buildid_must_start_absent')
    version_ref = {'path': PROGRAM + '/versionrc', 'sha256': plan['bootstrap']['versionrc']['sha256']}
    version = read_ref(version_ref)
    ids = re.findall(rb'^buildid=([^\r\n]+)', version, re.M)
    need(len(ids) == 1 and 0 < len(ids[0]) <= 256, 'bootstrap_stock_buildid_bound')
    steps = []
    with (WORK / 'bootstrap.log').open('xb') as log:
        os.chmod(WORK / 'bootstrap.log', 0o600)
        for index, expected in enumerate((81, 0)):
            need(services.now() < end, 'bootstrap_total_startup_deadline')
            emit('PROFILE_BOOTSTRAP_CHILD_STARTING', index=index, expected_exit=expected)
            child = services.spawn(bootstrap_argv(plan, finalize=index == 1), env=dict(os.environ), stdout=log)
            identity = services.process(child.pid)
            need(identity['namespace_pid'] == child.pid and identity['ppid'] == os.getpid()
                 and identity['executable_path'] == PROGRAM + '/soffice.bin'
                 and identity['executable_sha256'] == plan['observer']['config']['target_sha256'],
                 'bootstrap_actual_direct_child_identity')
            while child.poll() is None:
                need(services.now() < end, 'bootstrap_total_startup_deadline')
                services.sleep(0.02)
            need(child.returncode == expected, 'bootstrap_unknown_exit_or_wrong_stage')
            services.bootstrap_absent(child.pid)
            path = WORK / 'profile/user/extensions/buildid'
            need(str(path.resolve()) == str(path) and not path.is_symlink() and path.is_file(), 'bootstrap_stock_buildid_not_regular')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                st = os.fstat(stream.fileno())
                need(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1
                     and not st.st_mode & 0o077 and st.st_size <= 257, 'bootstrap_buildid_rights')
                raw = stream.read(258)
            need(raw == ids[0], 'bootstrap_buildid_mismatch')
            steps.append({'index': index, 'process': identity, 'exit_code': child.returncode,
                          'reaped_and_Office_absent': True, 'profile_buildid_sha256': sha(raw)})
            emit('PROFILE_BOOTSTRAP_CHILD_REAPED', **steps[-1])
    result = {'schema': 'frw.calc.own-fresh-profile-bootstrap.v1', 'operation_id': plan['operation_id'],
        'nonce': plan['nonce'], 'profile_origin': 'CREATED_EMPTY_FOR_THIS_OPERATION',
        'profile_url': pre['private_profile_url'], 'source_basis': plan['bootstrap']['basis'],
        'steps': steps, 'document_or_model_request': False, 'actual_M': None,
        'scope': 'ordinary81 extension-sync restart then early profile-finalizer0; final measured Office remains separate exact direct GDB child'}
    atomic(WORK / 'bootstrap-result.json', result)
    return result


def gdb_argv(plan):
    """Direct own soffice.bin child; shell/ASLR/autoload flags precede target."""
    base = plan['inner_input']
    pre = json.loads(read_ref(plan['preload']))
    return ['/usr/bin/gdb', '-nx', '-nh', '-batch',
            '-iex', 'maint set worker-threads 1', '-iex', 'set auto-load off',
            '-iex', 'set debuginfod enabled off', '-iex', 'set startup-with-shell off',
            '-iex', 'set disable-randomization off',
            '-x', plan['observer']['hook']['path'], '--args', PROGRAM + '/soffice.bin',
            '-env:UserInstallation=' + pre['private_profile_url'], '--headless', '--nologo',
            '--norestore', '--nodefault', '--nofirststartwizard',
            '--accept=pipe,name=' + base['pipe_name'] + ';urp;StarOffice.ComponentContext']


def build_loaded_record(plan, trace, checkpoint, observations, evidence_ref):
    """Actual-shaped pure join; callers cannot pass a future loaded template."""
    pre = json.loads(read_ref(plan['preload']))
    bootstrap = observations['bootstrap']
    need(bootstrap['operation_id'] == plan['operation_id'] and bootstrap['nonce'] == plan['nonce']
         and bootstrap['profile_origin'] == 'CREATED_EMPTY_FOR_THIS_OPERATION'
         and bootstrap['profile_url'] == pre['private_profile_url']
         and [s['exit_code'] for s in bootstrap['steps']] == [81, 0]
         and all(s['reaped_and_Office_absent'] is True for s in bootstrap['steps'])
         and bootstrap['source_basis'] == plan['bootstrap']['basis'], 'actual_same_operation_bootstrap_required')
    need(evidence_ref['path'] == str(WORK / 'loaded-observations.json'),
         'actual_namespace_observation_file_required')
    # Accepted100/R3 external evidence refs are honest cache refs. This is the
    # actual HOST backing file of the exact writable bind, not an invented cache
    # alias or a requirement that the inner client open masked host paths.
    host_evidence_ref = {'path': str(Path(plan['work_dir']) / 'loaded-observations.json'),
                         'sha256': evidence_ref['sha256']}
    need(checkpoint['schema'] == 'frw.calc.inner-checkpoint.v1'
         and checkpoint['operation_id'] == plan['operation_id'] and checkpoint['nonce'] == plan['nonce']
         and checkpoint['stage'] == 'MODEL_LOADED', 'same_actual_loaded_checkpoint')
    native = trace['process']
    p = observations['process']
    office = checkpoint['office_process']
    need(p['namespace_pid'] == native['pid'] == office['namespace_pid']
         and p['start_ticks'] == native['start_ticks'] == office['start_ticks']
         and p['ppid'] == native['gdb_pid']
         and p['executable_sha256'] == office['executable_sha256']
             == plan['observer']['config']['target_sha256']
         and p['executable_path'] == PROGRAM + '/soffice.bin', 'actual_office_process_binding')
    need(checkpoint['completed_operations'] == ['RESOLVE_OWN_REMOTE_CONTEXT', 'CREATE_REMOTE_DESKTOP',
         'LOAD_CALC_WORKING_COPY'] and type(checkpoint['later_language_mutations']) is int
         and checkpoint['later_language_mutations'] == 0, 'actual_remote_desktop_load_control_flow')
    need(observations['observed_after'] == 'MODEL_LOADED'
         and observations['startup_environment'] == {'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'},
         'actual_stock_C_UTF8_environment')
    need(checkpoint['remote_endpoint'] == 'uno:pipe,name=' + plan['inner_input']['pipe_name']
         + ';urp;StarOffice.ComponentContext', 'same_remote_endpoint')
    need(checkpoint['load_request']['url'] == pre['working_copy']['url']
         and checkpoint['load_request']['interaction_requests'] == 0, 'same_nointeraction_readonly_load')
    components = {}
    for role, item in observations['components'].items():
        need(item['path'] == plan['component_paths'][role]
             and item['sha256'] == pre['expected_components'][role], 'actual_component_mismatch:' + role)
        if role != 'font_config_view':
            need(item['mapped'] is True and item['observation'] == 'ACTUAL_MAPPED_COMPONENT'
                 and item['path'] in observations['mapped_paths'], 'required_component_not_mapped:' + role)
        else:
            f = observations['font_view']
            need(item['observation'] == 'ACTUAL_NAMESPACE_FONT_CONFIG_CAS'
                 and item['digest_kind'] == 'ROOT_CANONICAL_NAMESPACE_VIEW_NOT_BASELINE_FILE_SHA'
                 and f['view_sha256'] == plan['font_view']['expected_view_sha256'] == item['sha256']
                 and f['consumer'] == plan['font_view']['consumer']
                 and f['baseline'] == plan['font_view']['baseline']
                 and f['provenance_ref'] == plan['font_view']['provenance_ref']
                 and f['base_static_view_sha256'] == plan['font_view']['base_view_sha256']
                 and f['derived_cache'] == plan['font_view']['derived_cache']
                 and f['phase'] == 'AFTER_LOAD_BEFORE_QUERY'
                 and type(f.get('office_font_environment_proof')) is dict
                 and set(f['office_font_environment_proof']) == {'path', 'sha256'}
                 and f['office_font_environment_proof']['path'] == str(font_runtime_paths('AFTER_LOAD_BEFORE_QUERY')['proof'])
                 and type(f['office_font_environment_proof']['sha256']) is str
                 and re.fullmatch('[0-9a-f]{64}', f['office_font_environment_proof']['sha256'])
                 and f['office_process'] == p
                 and f['namespace_process']['namespaces'] == p['namespaces']
                 and f['namespace_process']['boot_id'] == p['boot_id'],
                 'fontconfig_requires_actual_same_Office_namespace_CAS')
        components[role] = {'path': item['path'], 'sha256': item['sha256']}
    need(set(components) == set(pre['expected_components']), 'all_component_roles_observed')
    # This is an actual pinned caller control-flow statement after successful
    # remote Desktop creation+load. It is NEVER inferred from locale config or
    # asserted before startup. Source100 remains frozen; Root's reviewed R3
    # same-API qualifier may accept this added lifecycle fact.
    lifecycle = {'exclusive_owner_operation_id': plan['operation_id'],
                 'profile_origin': 'CREATED_EMPTY_FOR_THIS_OPERATION',
                 'application_settings': 'STARTUP_CONFIG_UNMODIFIED',
                 'reference_operations': ['LOAD_CALC_WORKING_COPY'],
                 'stock_locale_initialization': 'DESKTOP_PREPARE_LOCALE_COMPLETED_NO_LATER_LANGUAGE_MUTATION'}
    read_ref(plan['startup_basis'])  # Root-reviewed exact source control-flow basis
    return {'schema': 'frw.Root.calc-reference-observer-loaded.v1', 'operation_id': plan['operation_id'],
            'process': {'pid': p['namespace_pid'], 'start_ticks': p['start_ticks'],
                        'executable_sha256': p['executable_sha256'], 'launch_api': 'EXECVE_STANDALONE_SOFFICE_BIN'},
            'loaded_components': components, 'load_request': checkpoint['load_request'],
            'lifecycle': lifecycle, 'native_transport': {'mode': 'RAW32_POSTQUERY_NATIVE_JOIN',
                 'native_min': None, 'native_max': None, 'proof_ref': None,
                 'scope': 'RAW32_ONLY_TEN_SINGLE_DIGITS', 'proof_disposition': 'NO_PREQUERY_NATIVE_BOUND',
                 'observer_plan_ref': plan['observer']['contract']},
            'evidence_ref': host_evidence_ref, 'startup_locale_environment': {'LC_ALL': 'C.UTF-8'}}


def validate_helper_boundary_metadata(raw, runtime, original):
    """Sanitized diagnostic sidecar, never a substitute for native/Root gates."""
    need(len(raw) <= 32768, 'helper_metadata_bound')
    value = json.loads(raw)
    need(type(value) is dict and set(value) == {'schema', 'operation_id', 'nonce', 'source_sha256',
         'manifest_ref', 'original', 'scope', 'stages'}
         and value['schema'] == 'frw.calc.paper-helper-boundary-metadata.v1'
         and value['scope'] == 'HASHED_ENV_NUMERIC_FD_ONLY_NO_RUNTIME_ADMISSION', 'helper_metadata_schema')
    need(all(value[k] == runtime[k] for k in ('operation_id', 'nonce', 'source_sha256', 'manifest_ref'))
         and value['original'] == original, 'helper_metadata_binding')
    is_hash = lambda v: type(v) is str and re.fullmatch('[0-9a-f]{64}', v) is not None
    is_count = lambda v: type(v) is int and v >= 0
    labels = set()
    def rows(items, hash_names):
        need(type(items) is list and len(items) <= 64, 'helper_metadata_key_bound')
        for row in items:
            need(type(row) is dict and (set(row) == {'key', *hash_names} or
                 set(row) == {'key_sha256', *hash_names}), 'helper_metadata_key_schema')
            if 'key' in row:
                need(type(row['key']) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}', row['key']),
                     'helper_metadata_key_name')
                labels.add(('name', row['key']))
            else:
                need(is_hash(row['key_sha256']), 'helper_metadata_key_hash')
                labels.add(('sha256', row['key_sha256']))
            need(all(row[k] is None or is_hash(row[k]) for k in hash_names), 'helper_metadata_value_hash')
    fd_keys = {'dev', 'ino', 'type', 'rdev', 'access', 'cloexec'}
    def fd(item):
        need(type(item) is dict and set(item) == fd_keys and type(item['cloexec']) is bool
             and all(is_count(item[k]) for k in fd_keys - {'cloexec'}), 'helper_metadata_fd_schema')
    stages = value['stages']
    need(type(stages) is list and 1 <= len(stages) <= 8, 'helper_metadata_stage_bound')
    required = {'stage', 'role', 'pid', 'refusal', 'environment_key_count', 'environment_keys_truncated',
                'environment_source_class', 'inheritance_reference_class', 'fds', 'expected_stdin',
                'expected_stderr', 'expected_stdout_pipe'}
    optional = {'environment', 'environment_sha256', 'font_environment', 'font_runtime_equals_initial',
                'font_scope', 'exec_initial_to_runtime_changed_key_count', 'exec_initial_to_runtime_changed_keys',
                'exec_initial_to_runtime_keys_truncated', 'fd_count', 'fds_truncated', 'fd_observation_error_class'}
    known_roles = {'popen': 'parent', 'spawn': 'parent', 'metric': 'parent', 'dash_birth': 'dash',
                   'dash_exec': 'dash', 'dash_entry': 'dash', 'paperconf_exec': 'paperconf', 'paperconf_entry': 'paperconf'}
    identifier = lambda v: type(v) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', v)
    for stage in stages:
        need(type(stage) is dict and required <= set(stage) <= required | optional
             and stage['stage'] in known_roles and stage['role'] == known_roles[stage['stage']]
             and type(stage['pid']) is int and stage['pid'] > 0
             and (stage['refusal'] is None or identifier(stage['refusal']))
             and is_count(stage['environment_key_count']) and type(stage['environment_keys_truncated']) is bool,
             'helper_metadata_stage_schema')
        need(stage['environment_source_class'] == ('PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON' if stage['role'] == 'parent' else 'KERNEL_EXEC_ENVIRON')
             and stage['inheritance_reference_class'] == ('EXACT_POSIX_SPAWN_R9' if stage['stage'] == 'spawn' else 'PARENT_RUNTIME_SNAPSHOT'),
             'helper_metadata_mapping_class')
        need(stage['role'] != 'parent' or stage['pid'] == original['pid'], 'helper_metadata_parent_identity')
        if 'environment' in stage:
            rows(stage['environment'], ('expected_value_sha256', 'actual_value_sha256'))
        if 'environment_sha256' in stage:
            need(is_hash(stage['environment_sha256']), 'helper_metadata_environment_hash')
        if 'font_environment' in stage:
            rows(stage['font_environment'], ('initial_value_sha256', 'runtime_value_sha256'))
            need(type(stage.get('font_runtime_equals_initial')) is bool
                 and stage.get('font_scope') == 'THIS_STOPPED_BOUNDARY_ONLY_NOT_FONT_CAS_POSTCONDITION', 'helper_metadata_font_scope')
        if 'exec_initial_to_runtime_changed_keys' in stage:
            rows(stage['exec_initial_to_runtime_changed_keys'], ('initial_value_sha256', 'runtime_value_sha256'))
            need(is_count(stage.get('exec_initial_to_runtime_changed_key_count'))
                 and type(stage.get('exec_initial_to_runtime_keys_truncated')) is bool, 'helper_metadata_changed_keys')
        for key in ('expected_stdin', 'expected_stderr', 'expected_stdout_pipe'):
            if stage[key] is not None:
                fd(stage[key])
        need(type(stage['fds']) is list and len(stage['fds']) <= 8, 'helper_metadata_fd_bound')
        for item in stage['fds']:
            need(type(item) is dict and is_count(item.get('number')), 'helper_metadata_fd_number')
            if 'observation_error_class' in item:
                need(set(item) == {'number', 'observation_error_class'} and identifier(item['observation_error_class']),
                     'helper_metadata_fd_error_class')
            else:
                fd({k: v for k, v in item.items() if k != 'number'})
        for key in ('fd_count',):
            if key in stage:
                need(is_count(stage[key]), 'helper_metadata_fd_count')
        if 'fds_truncated' in stage:
            need(type(stage['fds_truncated']) is bool, 'helper_metadata_fd_truncated')
        if 'fd_observation_error_class' in stage:
            need(identifier(stage['fd_observation_error_class']), 'helper_metadata_fd_error_class')
    need(len(labels) <= 64, 'helper_metadata_total_key_bound')
    return value


def output_inventory(*, helper_runtime=None, original=None, plan=None):
    allowed_files = {'namespace-job.json', 'unit-release.json', 'office-ready.json', 'office-release.json',
                     'observer-config.json', 'phase.json', 'native-trace.json', 'gdb.log', 'inner.log',
                     'helper-runtime.json', 'load-dependency.json',
                     'inner-input.json', 'inner-result.json', 'inner-checkpoint.json', 'inner-started.json',
                     'loaded-envelope.json', 'loaded-record.json', 'loaded-observations.json',
                     'namespace-journal.json', 'namespace-result.json', 'font-CAS-phase.json',
                     'font-view-before-office.json', 'font-view-after-close.json', 'font-view-after-bootstrap.json', 'bootstrap.log', 'bootstrap-result.json'}
    allowed_dirs = {'profile', 'tmp', 'cache', 'config', 'runtime'}
    if helper_runtime is not None:
        allowed_files.add('paper-helper-boundary.json')
        need((WORK / 'paper-helper-boundary.json').is_file(), 'helper_metadata_missing')
        need(plan is not None, 'font_runtime_inventory_requires_plan')
        baseline = json.loads(read_ref(plan['font_view']['baseline']))['view']['environment']
        allowed_files.add('font-view-after-load.json')
        for boundary in ('AFTER_LOAD_BEFORE_QUERY', 'AFTER_READONLY_CLOSE'):
            paths = font_runtime_paths(boundary)
            allowed_files.update(p.name for p in paths.values())
            view_path = WORK / ('font-view-after-load.json' if boundary == 'AFTER_LOAD_BEFORE_QUERY' else 'font-view-after-close.json')
            validate_font_runtime_pair(*(font_runtime_read(paths[k]) for k in ('request', 'proof', 'release', 'accepted')),
                font_runtime_read(view_path), plan=plan, native=original, environment=baseline,
                boundary=boundary, deadline=helper_runtime['operation_deadline_monotonic'])
    files = []
    for path in WORK.rglob('*'):
        relative = path.relative_to(WORK)
        need(not path.is_symlink(), 'unexpected_output_symlink')
        need(relative.parts[0] in allowed_dirs or (len(relative.parts) == 1 and path.name in allowed_files),
             'unexpected_writable_output')
        need(path.stat().st_uid == os.getuid() and not path.stat().st_mode & 0o077,
             'private_output_rights')
        if path.is_file():
            if relative.parts[0] in allowed_dirs:
                need(path.suffix.lower() not in ('.ods', '.xlsx', '.xls', '.csv', '.pdf', '.odt', '.docx'),
                     'unexpected_document_output')
            record = {'path': str(relative), 'bytes': path.stat().st_size,
                          'scope': 'READONLY_DERIVED_FONTCONFIG_INPUT' if relative.parts[:2] == ('cache', 'fontconfig')
                                   else 'OWN_OPERATION_OUTPUT'}
            if relative == Path('paper-helper-boundary.json'):
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
                with os.fdopen(fd, 'rb') as source:
                    before = os.fstat(source.fileno())
                    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_uid == os.getuid()
                         and stat.S_IMODE(before.st_mode) == 0o600 and before.st_size <= 32768,
                         'helper_metadata_rights_bound')
                    raw = source.read(32769)
                    after = os.fstat(source.fileno())
                identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
                need(identity(before) == identity(after) == identity(path.lstat()), 'helper_metadata_changed')
                metadata = validate_helper_boundary_metadata(raw, helper_runtime, original)
                need([s['stage'] for s in metadata['stages']] == ['popen', 'spawn']
                     and all(s['refusal'] is None and s.get('font_runtime_equals_initial') is True for s in metadata['stages']),
                     'helper_metadata_parent_boundaries_not_complete')
                for stage in metadata['stages']:
                    validate_font_projection(stage.get('font_environment'), baseline, helper=True)
                record.update(bytes=len(raw), sha256=sha(raw), scope='HASHED_ENV_NUMERIC_FD_ONLY_NO_RUNTIME_ADMISSION')
            elif len(relative.parts) == 1 and (path.name.startswith('font-runtime-') or path.name == 'font-view-after-load.json'):
                raw = font_runtime_read(path)
                record.update(bytes=len(raw), sha256=sha(raw), scope='BOUND_CURRENT_FONT_ENVIRONMENT_POINT_ONLY')
            files.append(record)
    return files


def load_dependency_bundle(plan, deadline):
    binding = plan['observer'].get('load_dependency')
    if binding is None:
        return None, None
    runtime = copy.deepcopy(plan['inner_input']['load_dependency'])
    # Exact pre-existing global operation clock, including elapsed bootstrap and
    # startup. loaded_seconds was only a postcall wait, never a LOAD clock.
    need(runtime['operation_deadline_monotonic'] is None, 'helper_prelaunch_clock_must_be_unbound')
    runtime['operation_deadline_monotonic'] = deadline
    manifest = json.loads(read_ref(binding['manifest']))
    policy = {'__name__': 'frw_pinned_namespace_paper_policy', '__file__': binding['policy']['path']}
    exec(compile(read_ref(binding['policy']), binding['policy']['path'], 'exec'), policy)
    policy['validate_manifest'](manifest)
    policy['validate_runtime'](runtime, manifest)
    need(runtime['manifest_ref'] == binding['manifest'] and runtime['nonce'] == plan['nonce']
         and runtime['operation_id'] == plan['operation_id'], 'helper_namespace_binding')
    bundle = {'schema': 'frw.calc.paper-helper-runtime-bundle.v1', 'runtime': runtime,
        'manifest_ref': binding['manifest'], 'policy_ref': binding['policy'], 'adapter_ref': binding['adapter']}
    read_ref(binding['adapter'])
    return bundle, policy


def check_load_dependency_closed(trace, runtime, policy, native):
    need(policy is not None and runtime is not None, 'helper_closure_policy_unbound')
    evidence = policy['validate_closed'](trace.get('load_dependency'), runtime, native)
    expected_marker = dict(schema=policy['MARKER'], state='LOAD_CLOSED', **{k: runtime[k] for k in
        ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'operation_deadline_monotonic')})
    need(json.loads(runtime_read(WORK / 'load-dependency.json')) == expected_marker, 'helper_LOAD_marker_not_closed')
    need(all(not (Path('/proc') / str(child['pid'])).exists() for child in evidence['children']),
         'helper_child_still_present_at_loaded_release')
    # Child exits alone are insufficient. The caller already performs the same
    # original Office birth/executable/font CAS before and after this check.
    return evidence


def run(job, *, services=None):
    """Real one-operation pipeline with optional in-process pure-test services."""
    services = services or LocalServices()
    plan = job['plan']
    need(Path.cwd() == WORK and WORK.is_dir() and stat.S_IMODE(WORK.stat().st_mode) == 0o700,
         'exact_namespace_work_required')
    deadline = job['deadline_monotonic']
    need(type(deadline) in (int, float) and services.now() < deadline, 'operation_deadline_expired')
    need(os.environ.get('LANG') == 'C.UTF-8' and os.environ.get('LC_ALL') == 'C.UTF-8',
         'preserve_actual_C_UTF8')
    events = []
    def emit(phase, **values):
        events.append(dict(phase=phase, monotonic=services.now(), **values))
        atomic(WORK / 'namespace-journal.json', {'schema': 'frw.calc.namespace-journal.v1',
            'operation_id': plan['operation_id'], 'nonce': plan['nonce'], 'events': events, 'actual_M': None})
    gdb = client = None
    after_view = None
    result = {'schema': 'frw.calc.namespace-result.v1', 'nonce': plan['nonce'],
              'status': 'REFUSED_NEEDS_OUTER_CGROUP_CLEANUP', 'actual_M': None, 'runtime_attested': False}
    def wait_file(path, *, limit, child=None):
        end = min(deadline, services.now() + limit)
        while not path.exists():
            need(services.now() < end, 'phase_deadline:' + path.name)
            need(child is None or child.poll() is None, 'child_exit_before:' + path.name)
            services.sleep(0.02)
        return json.loads(runtime_read(path))
    try:
        # The service manager's actual finite properties and cgroup must be
        # observed by outer before ANY Office/GDB child launch.
        release = wait_file(WORK / 'unit-release.json', limit=plan['budgets']['startup_seconds'])
        need(release['operation_id'] == plan['operation_id'] and release['nonce'] == plan['nonce']
             and release['stage'] == 'ACTUAL_OWN_UNIT_PROPERTIES_VERIFIED', 'unit_release_binding')
        before_view = services.font_view_observation(plan, phase='BEFORE_OFFICE')
        need(before_view['view_sha256'] == plan['font_view']['expected_view_sha256'],
             'before_Office_font_CAS_UNBOUND')
        atomic(WORK / 'font-view-before-office.json', before_view)
        emit('FONT_VIEW_BEFORE_OFFICE_CAS', view_sha256=before_view['view_sha256'])
        need(not (WORK / 'profile').exists(), 'profile_must_be_fresh_absent')
        (WORK / 'profile').mkdir(mode=0o700)
        bootstrap = bootstrap_profile(plan, services=services, deadline=deadline, emit=emit)
        # The same operation owns the newly initialized profile. Never import
        # the closed first operation's profile or describe this one as still empty.
        after_bootstrap_view = services.font_view_observation(plan, phase='AFTER_BOOTSTRAP_BEFORE_GDB')
        need(after_bootstrap_view['view_sha256'] == before_view['view_sha256'], 'bootstrap_font_view_drift')
        atomic(WORK / 'font-view-after-bootstrap.json', after_bootstrap_view)
        atomic(WORK / 'phase.json', {'nonce': plan['nonce'], 'phase': 'IDLE', 'index': None, 'digit': None})
        atomic(WORK / 'observer-config.json', plan['observer']['config'])
        env = dict(os.environ, FRW_NATIVE_OBSERVER_CONFIG=str(WORK / 'observer-config.json'))
        helper_bundle, helper_policy = load_dependency_bundle(plan, deadline)
        if helper_bundle is not None:
            bundle_ref = atomic(WORK / 'helper-runtime.json', helper_bundle)
            env['FRW_NATIVE_LOAD_DEPENDENCY_REF'] = json.dumps(bundle_ref, sort_keys=True)
        with (WORK / 'gdb.log').open('xb') as glog, (WORK / 'inner.log').open('xb') as ilog:
            os.chmod(WORK / 'gdb.log', 0o600)
            os.chmod(WORK / 'inner.log', 0o600)
            emit('GDB_DIRECT_CHILD_STARTING')
            gdb = services.spawn(gdb_argv(plan), env=env, stdout=glog)
            gdb_identity = services.process(gdb.pid)
            need(gdb_identity['namespace_pid'] == gdb.pid, 'actual_GDB_PID_identity')
            emit('GDB_STARTED', process=gdb_identity)
            end = min(deadline, services.now() + plan['budgets']['startup_seconds'])
            while True:
                need(services.now() < end and gdb.poll() is None, 'native_readiness_deadline_or_exit')
                if (WORK / 'native-trace.json').exists():
                    trace = json.loads(runtime_read(WORK / 'native-trace.json'))
                    need(trace['nonce'] == plan['nonce'] and trace['error'] is None, 'native_readiness_refused')
                    if trace['status'] == 'READY_UNRELEASED':
                        break
                services.sleep(0.02)
            native = trace['process']
            need(native['gdb_pid'] == gdb.pid and native['inferior'] == 1, 'own_direct_GDB_process')
            office = services.process(native['pid'])
            need(office['start_ticks'] == native['start_ticks'] and office['ppid'] == gdb.pid
                 and office['executable_sha256'] == plan['observer']['config']['target_sha256'],
                 'ready_actual_office_identity')
            atomic(WORK / 'office-ready.json', {'schema': 'frw.calc.office-ready.v1',
                'operation_id': plan['operation_id'], 'nonce': plan['nonce'],
                'native_process': native, 'native_symbols': trace['symbols'],
                'office_identity': office, 'gdb_identity': gdb_identity})
            initial_symbols = copy.deepcopy(trace['symbols'])
            emit('OFFICE_READY_WAITING_HOST_CUSTODY', native_process=native,
                 native_symbols=initial_symbols, office_identity=office)
            release = wait_file(WORK / 'office-release.json', limit=plan['budgets']['startup_seconds'], child=gdb)
            need(release['operation_id'] == plan['operation_id'] and release['nonce'] == plan['nonce']
                 and release['stage'] == 'ACTUAL_HOST_NAMESPACE_PID_BIRTH_CGROUP_BOUND'
                 and release['native_process'] == native and release['native_symbols'] == initial_symbols,
                 'host_process_symbol_custody_release')
            cfg = copy.deepcopy(plan['inner_input'])
            cfg['office_process'] = {'namespace_pid': native['pid'], 'start_ticks': native['start_ticks'],
                                     'executable_sha256': office['executable_sha256']}
            if helper_bundle is not None:
                cfg['load_dependency'] = copy.deepcopy(helper_bundle['runtime'])
            config_ref = atomic(WORK / 'inner-input.json', cfg)
            # Full inner inspect occurs after the actual READY process exists.
            read_ref(plan['inner_client'])
            client = services.spawn(['/usr/bin/python3', '-I', '-B', '-S', plan['inner_client']['path'],
                '--input', config_ref['path'], '--input-sha256', config_ref['sha256'],
                '--output', str(WORK / 'inner-result.json')], env=dict(os.environ), stdout=ilog)
            client_identity = services.process(client.pid)
            need(client_identity['namespace_pid'] == client.pid
                 and client_identity['namespaces'] == office['namespaces']
                 and client_identity['boot_id'] == office['boot_id'], 'actual_inner_same_namespace_identity')
            emit('INNER_CLIENT_STARTED', process=client_identity)
            checkpoint = wait_file(WORK / 'inner-checkpoint.json', limit=cfg['timeouts']['loaded_seconds'], child=client)
            # Refresh actual trace after LOAD; startup READY is not closure.
            trace = json.loads(runtime_read(WORK / 'native-trace.json'))
            need(trace['error'] is None and trace['process'] == native
                 and trace['symbols'] == initial_symbols and trace['records'] == [], 'loaded_trace_original_binding')
            helper_evidence = None
            if helper_bundle is not None:
                helper_evidence = check_load_dependency_closed(trace, helper_bundle['runtime'], helper_policy, native)
            else:
                need('load_dependency' not in trace, 'unexpected_helper_evidence')
            need(helper_bundle is not None, 'current_font_runtime_getter_requires_pinned_helper_bundle')
            loaded_held = services.acquire_font_runtime(plan, native, boundary='AFTER_LOAD_BEFORE_QUERY',
                                                        deadline=deadline, child=gdb)
            observations = services.loaded_observations(plan, native, font_runtime=loaded_held)
            need(observations['font_view']['office_font_environment_proof'] == loaded_held['proof_ref'],
                 'loaded_actual_font_runtime_proof_join')
            loaded_view_ref = atomic(WORK / 'font-view-after-load.json', observations['font_view'])
            if helper_evidence is not None:
                observations['load_dependency'] = helper_evidence
            need(services.now() < deadline, 'global_deadline_before_qualifier_query_release')
            evidence = atomic(WORK / 'loaded-observations.json', observations)
            record = build_loaded_record(plan, trace, checkpoint, observations, evidence)
            record_ref = atomic(WORK / 'loaded-record.json', record)
            need(not (WORK / 'loaded-envelope.json').exists(), 'future_or_duplicate_loaded_envelope')
            services.release_font_runtime(plan, loaded_held, view_ref=loaded_view_ref, deadline=deadline)
            atomic(WORK / 'loaded-envelope.json', {'schema': 'frw.calc.inner.loaded-envelope.v1',
                'operation_id': plan['operation_id'], 'nonce': plan['nonce'], 'record': record_ref})
            emit('ACTUAL_LOADED_RECORD_RELEASED', process=record['process'], record_ref=record_ref)
            while client.poll() is None or gdb.poll() is None:
                need(services.now() < deadline, 'metric_close_global_deadline')
                need(client.poll() in (None, 0) and gdb.poll() in (None, 0), 'own_child_failed')
                current_phase = json.loads(runtime_read(WORK / 'phase.json'))
                if current_phase == dict(nonce=plan['nonce'], phase='CLOSED', index=None, digit=None) and after_view is None:
                    need(client.poll() is None and gdb.poll() is None, 'postclose_boundary_before_termination_required')
                    closed_held = services.acquire_font_runtime(plan, native, boundary='AFTER_READONLY_CLOSE',
                                                                deadline=deadline, child=gdb)
                    after_view = services.font_view_observation(plan, phase='AFTER_READONLY_CLOSE',
                                                               office_pid=native['pid'], font_runtime=closed_held)
                    need(after_view['view_sha256'] == before_view['view_sha256'], 'postclose_font_CAS_drift')
                    after_ref = atomic(WORK / 'font-view-after-close.json', after_view)
                    services.release_font_runtime(plan, closed_held, view_ref=after_ref, deadline=deadline)
                services.sleep(0.02)
            need(client.returncode == 0 and gdb.returncode == 0, 'actual_child_exit_nonzero')
        inner = json.loads(runtime_read(WORK / 'inner-result.json'))
        trace = json.loads(runtime_read(WORK / 'native-trace.json'))
        phase = json.loads(runtime_read(WORK / 'phase.json'))
        need(phase == {'nonce': plan['nonce'], 'phase': 'CLOSED', 'index': None, 'digit': None}, 'actual_CLOSED_required')
        need(trace['status'] == 'COMPLETE_UNATTESTED' and trace['error'] is None
             and trace['exit_code'] == 0 and trace['own_inferior_absent'] is True, 'native_actual_exit_unconfirmed')
        if helper_bundle is not None:
            check_load_dependency_closed(trace, helper_bundle['runtime'], helper_policy, native)
        need(trace['process'] == native and trace['symbols'] == initial_symbols,
             'final_trace_changed_early_process_or_symbols')
        # The precise inner terminal contract is checked by the separate helper;
        # no M or postjoin is accepted within this still-live cgroup.
        need(inner['status'] == 'CANDIDATE_UNATTESTED_OUTER_POSTCONDITIONS_REQUIRED'
             and inner['stage'] == 'CLOSED' and inner['operation_id'] == plan['operation_id']
             and inner['nonce'] == plan['nonce'] and inner['actual_M'] is None
             and inner['runtime_attested'] is False, 'inner_readonlyclose_unconfirmed')
        need(inner['candidate']['measurement']['native_font_restore_completed'] is True
             and inner['readonly_close_confirmed'] is True and inner['desktop_terminate_requested'] is True
             and type(inner['handler_requests']) is int and inner['handler_requests'] == 0,
             'inner_full_closure_required')
        widths = inner['candidate']['measurement']['digit_widths']
        need(type(widths) is list and len(widths) == 10
             and widths == [r['raw32'] for r in inner['responses']]
             and all(type(v) is int for v in widths), 'inner_exact_raw32_responses')
        pre = json.loads(read_ref(plan['preload']))
        working_path = unquote(urlparse(pre['working_copy']['url']).path)
        working_refs = [r for r in plan['source_files'] if r['path'] == working_path]
        need(len(working_refs) == 1, 'exact_readonly_working_source_pin')
        read_ref(working_refs[0])
        need(after_view is not None and after_view['office_process'] == office
             and after_view['view_sha256'] == plan['font_view']['expected_view_sha256']
             == before_view['view_sha256'], 'postclose_font_CAS_drift')
        inventory = output_inventory(helper_runtime=helper_bundle['runtime'] if helper_bundle is not None else None,
                                     original=native if helper_bundle is not None else None, plan=plan)
        result.update(status='CLOSED_UNRELEASED', bootstrap=bootstrap, native_process=trace['process'], native_symbols=trace['symbols'],
                      uno_widths=widths, office_identity=office, output_inventory=inventory,
                      gdb_identity=gdb_identity, inner_client_identity=client_identity,
                      font_view_before_office=before_view, font_view_after_bootstrap=after_bootstrap_view, font_view_after_close=after_view,
                      readonly_close_confirmed=True, readonly_copy_hash_unchanged=True,
                      no_unexpected_writable_output=True, child_exit={'gdb': gdb.returncode, 'inner': client.returncode})
        emit('READONLY_CLOSE_CHILD_EXIT_SOURCE_NO_OUTPUT_CONFIRMED')
    except Exception as exc:
        result.update(exception_class=type(exc).__name__, reason=str(exc) if type(exc) is Refused else None)
        emit('REFUSED_NEEDS_OUTER_WHOLE_OWN_CGROUP_CLEANUP', exception_class=type(exc).__name__)
        # No partial child-only cleanup is presented as custody. On this finite
        # supervisor's exit, systemd KillMode=control-group plus outer stop/empty
        # verification handles even unknown forks or an externally killed GDB.
    finally:
        if services.source_only:
            result.update(source_rehearsal_only=True, evidence_scope='SYNTHETIC_PARSER_AND_ORCHESTRATION_ONLY')
        atomic(WORK / 'namespace-result.json', result)
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job')
    a = parser.parse_args()
    if not a.job:
        print(json.dumps({'status': 'SOURCE_ONLY_NO_OPERATION', 'actual_M': None, 'runtime_grant': False}))
        return
    need(a.job == str(WORK / 'namespace-job.json'), 'exact_outer_staged_job_required')
    result = run(json.loads(runtime_read(a.job)))
    raise SystemExit(0 if result['status'] == 'CLOSED_UNRELEASED' else 2)


if __name__ == '__main__':
    main()
