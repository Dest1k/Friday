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
import stat
import subprocess
import time
import types
from urllib.parse import unquote, urlparse

WORK = Path('/tmp/friday-metric-work')
PROGRAM = '/opt/friday-document-toolchain/root/usr/lib/libreoffice/program'


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
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True, close_fds=True)

    def process(self, pid):
        return process_snapshot(pid)

    def font_view_observation(self, plan, *, phase, office_pid=None):
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
            items = (Path('/proc') / str(office_pid) / 'environ').read_bytes().split(b'\0')
            env = dict(item.split(b'=', 1) for item in items if b'=' in item)
            font_environment = {key: env[key.encode()].decode() if key.encode() in env else None
                                for key in baseline['view']['environment']}
            need(font_environment == baseline['view']['environment'], 'actual_Office_font_environment_changed')
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

    def loaded_observations(self, plan, native):
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
        font_view = self.font_view_observation(plan, phase='AFTER_LOAD_BEFORE_QUERY', office_pid=pid)
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


def output_inventory():
    allowed_files = {'namespace-job.json', 'unit-release.json', 'office-ready.json', 'office-release.json',
                     'observer-config.json', 'phase.json', 'native-trace.json', 'gdb.log', 'inner.log',
                     'inner-input.json', 'inner-result.json', 'inner-checkpoint.json', 'inner-started.json',
                     'loaded-envelope.json', 'loaded-record.json', 'loaded-observations.json',
                     'namespace-journal.json', 'namespace-result.json', 'font-CAS-phase.json',
                     'font-view-before-office.json', 'font-view-after-close.json', 'font-view-after-bootstrap.json', 'bootstrap.log', 'bootstrap-result.json'}
    allowed_dirs = {'profile', 'tmp', 'cache', 'config', 'runtime'}
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
            files.append({'path': str(relative), 'bytes': path.stat().st_size,
                          'scope': 'READONLY_DERIVED_FONTCONFIG_INPUT' if relative.parts[:2] == ('cache', 'fontconfig')
                                   else 'OWN_OPERATION_OUTPUT'})
    return files


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
            observations = services.loaded_observations(plan, native)
            need(services.now() < deadline, 'global_deadline_before_qualifier_query_release')
            evidence = atomic(WORK / 'loaded-observations.json', observations)
            record = build_loaded_record(plan, trace, checkpoint, observations, evidence)
            record_ref = atomic(WORK / 'loaded-record.json', record)
            need(not (WORK / 'loaded-envelope.json').exists(), 'future_or_duplicate_loaded_envelope')
            atomic(WORK / 'loaded-envelope.json', {'schema': 'frw.calc.inner.loaded-envelope.v1',
                'operation_id': plan['operation_id'], 'nonce': plan['nonce'], 'record': record_ref})
            emit('ACTUAL_LOADED_RECORD_RELEASED', process=record['process'], record_ref=record_ref)
            while client.poll() is None or gdb.poll() is None:
                need(services.now() < deadline, 'metric_close_global_deadline')
                need(client.poll() in (None, 0) and gdb.poll() in (None, 0), 'own_child_failed')
                services.sleep(0.02)
            need(client.returncode == 0 and gdb.returncode == 0, 'actual_child_exit_nonzero')
        inner = json.loads(runtime_read(WORK / 'inner-result.json'))
        trace = json.loads(runtime_read(WORK / 'native-trace.json'))
        phase = json.loads(runtime_read(WORK / 'phase.json'))
        need(phase == {'nonce': plan['nonce'], 'phase': 'CLOSED', 'index': None, 'digit': None}, 'actual_CLOSED_required')
        need(trace['status'] == 'COMPLETE_UNATTESTED' and trace['error'] is None
             and trace['exit_code'] == 0 and trace['own_inferior_absent'] is True, 'native_actual_exit_unconfirmed')
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
        after_view = services.font_view_observation(plan, phase='AFTER_READONLY_CLOSE')
        need(after_view['view_sha256'] == plan['font_view']['expected_view_sha256']
             == before_view['view_sha256'], 'postclose_font_CAS_drift')
        atomic(WORK / 'font-view-after-close.json', after_view)
        inventory = output_inventory()
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
