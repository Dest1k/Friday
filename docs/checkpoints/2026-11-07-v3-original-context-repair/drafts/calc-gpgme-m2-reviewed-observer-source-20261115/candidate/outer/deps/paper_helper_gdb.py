"""Read-only GDB adapter for paper_helper_policy, shared by Office and fixture.

No inferior calls, stepping, writes, detach, output-pipe reads or return changes.
Callbacks only observe/queue; breakpoint creation occurs after execute returns.
The original supervisor's whole-cgroup deadline/cleanup remains authoritative.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time


# Exact installed ELF, relocation and instructions verified against the pinned
# glibc 2.43 iopopen source. Refuse interposition/copy relocations; never guess a
# GDB symbol owner or call getenv in the inferior. The call passes envp in r9.
ENV_SOURCE = dict(libc_sha256='9941dc28e68bc5fd788d9cd024c69e68c791d63799e7538a97b6040dd9f50fb6',
    load_offset=0x8e21b, load_bytes='488b058e3d1800', got_offset=0x211fb0,
    storage_offset=0x219de8, dereference_offset=0x8e238, dereference_bytes='4c8b08',
    call_offset=0x8e242, call_bytes='e879cc0800', zero_fill_start=0x214000, data_memory_end=0x220d90)
FONT_ENV_KEYS = (b'HOME', b'TMPDIR', b'XDG_CACHE_HOME', b'XDG_CONFIG_HOME', b'XDG_DATA_HOME',
    b'FONTCONFIG_FILE', b'FONTCONFIG_PATH', b'FONTCONFIG_SYSROOT', b'FC_LANG', b'LANG', b'LC_ALL',
    b'SAL_FONTPATH', b'SAL_USE_VCLPLUGIN', b'LD_LIBRARY_PATH', b'URE_BOOTSTRAP')


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def read_ref(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'helper_exact_ref')
    p = Path(ref['path'])
    require(p.is_absolute() and str(p.resolve()) == str(p), 'helper_ref_alias')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid in (0, os.getuid())
                and not s.st_mode & 0o022 and s.st_size <= 262144, 'helper_ref_rights_bound')
        raw = os.read(fd, 262145)
        a = os.fstat(fd)
        require((s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns) ==
                (a.st_dev, a.st_ino, a.st_size, a.st_mtime_ns, a.st_ctime_ns)
                and len(raw) <= 262144, 'helper_ref_changed')
    finally:
        os.close(fd)
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'helper_ref_hash')
    return raw


def create(gdb, native, bundle_ref):
    b = json.loads(read_ref(bundle_ref))
    require(type(b) is dict and set(b) == {'schema', 'runtime', 'manifest_ref', 'policy_ref', 'adapter_ref'}
            and b['schema'] == 'frw.calc.paper-helper-runtime-bundle.v1', 'helper_bundle_schema')
    require(str(Path(__file__).resolve()) == b['adapter_ref']['path'], 'helper_adapter_source')
    read_ref(b['adapter_ref'])
    policy = {'__name__': 'frw_pinned_paper_policy', '__file__': b['policy_ref']['path']}
    exec(compile(read_ref(b['policy_ref']), b['policy_ref']['path'], 'exec'), policy)
    m = json.loads(read_ref(b['manifest_ref']))
    require(b['runtime']['manifest_ref'] == b['manifest_ref'], 'helper_bundle_manifest_binding')
    return Adapter(gdb, native, b, m, policy)


class Adapter:
    def __init__(self, gdb, native, bundle, manifest, policy):
        self.g = gdb
        self.n = native
        self.b = bundle
        self.m = manifest
        self.p = policy
        self.fixture = native['CFG']['kind'] == 'OWN_POPEN_FIXTURE_ONLY'
        policy['validate_manifest'](manifest, fixture=self.fixture)
        policy['validate_runtime'](bundle['runtime'], manifest)
        require(bundle['runtime']['nonce'] == native['CFG']['nonce'], 'helper_native_nonce')
        require(self.fixture or native['CFG']['kind'] == 'OFFICE_UNADMITTED', 'helper_no_ABI_permission')
        self.c = None
        self.installed = False
        self.pending = None
        self.to_create = []
        self.breakpoints = []
        self.stop_handlers = {}
        self.retired_breakpoints = set()
        self.pending_stop = None
        self.stream = None
        self.pipe = None
        self.original_env = None
        self.spawn_env_verified = False
        self.environment_proof = []
        self.metadata_keys = list(FONT_ENV_KEYS)
        self.original_stderr = None
        self.original_stdin = None
        self.known = {}
        self.catchpoints = {}
        for image in [manifest['caller'], *manifest['images'].values()]:
            self.pin(image)
        link = manifest['shell_link']
        require(os.readlink(link['path']) == link['target'] and str(Path(link['path']).resolve()) ==
                link['canonical'] == manifest['images']['dash']['path'], 'helper_shell_link_changed')

    def pin(self, image):
        p = Path(image['path'])
        require(p.is_absolute() and str(p.resolve()) == str(p) and p.is_file(), 'helper_image_path')
        with p.open('rb') as f:
            require(hashlib.file_digest(f, 'sha256').hexdigest() == image['sha256'], 'helper_image_hash')

    def proc(self, pid):
        raw = self.bounded(Path('/proc') / str(pid) / 'stat', 4096).decode('ascii')
        v = raw.rsplit(')', 1)[1].split()
        return {'pid': pid, 'ppid': int(v[1]), 'start_ticks': int(v[19])}

    def bounded(self, path, limit):
        with Path(path).open('rb') as f:
            value = f.read(limit + 1)
        require(len(value) <= limit, 'helper_proc_bound')
        return value

    def ensure(self):
        original = self.n['STATE']['process']
        require(original is not None, 'helper_original_unbound')
        if self.c is None:
            self.c = self.p['Custody'](self.m, self.b['runtime'], original, fixture=self.fixture)
            self.known[original['pid']] = self.proc(original['pid'])
        self.original_check()
        return self.c

    def original_check(self):
        original = self.n['STATE']['process']
        require(original is not None, 'helper_original_unbound')
        p = self.proc(original['pid'])
        require(p['ppid'] == os.getpid() and p['start_ticks'] == original['start_ticks'], 'helper_original_birth_parent')
        root = Path('/proc') / str(p['pid'])
        require(os.readlink(root / 'cwd') == '/tmp/friday-metric-work', 'helper_working_directory_changed')
        require(os.readlink(root / 'exe') == self.n['CFG']['target_path'], 'helper_original_exec')
        with (root / 'exe').open('rb') as f:
            require(hashlib.file_digest(f, 'sha256').hexdigest() == self.n['CFG']['target_sha256'], 'helper_original_exe_hash')
        return p

    def maps(self, pid):
        result = []
        for line in self.bounded(Path('/proc') / str(pid) / 'maps', 512 * 1024).decode('ascii').splitlines():
            f = line.split(None, 5)
            if len(f) == 6 and f[5].startswith('/'):
                require(not f[5].endswith(' (deleted)'), 'helper_deleted_mapping')
                start, end = (int(v, 16) for v in f[0].split('-'))
                result.append((start, end, int(f[2], 16), f[1], f[5]))
        return result

    def base(self, pid, path):
        values = {start - offset for start, _end, offset, _perms, file in self.maps(pid) if file == path and offset == 0}
        require(len(values) == 1, 'helper_image_base')
        return values.pop()

    def offset(self, frame, image):
        pc = int(frame.pc())
        pid = self.g.selected_inferior().pid
        mapped = [v for v in self.maps(pid) if v[0] <= pc < v[1] and 'x' in v[3] and v[4] == image['path']]
        require(len(mapped) == 1, 'helper_PC_not_pinned_image')
        self.pin(image)
        return pc - self.base(pid, image['path'])

    def memory(self, address, count):
        require(type(address) is int and address > 0 and 0 < count <= 64, 'helper_memory_bound')
        return self.g.selected_inferior().read_memory(address, count).tobytes()

    def register(self, name):
        v = self.g.newest_frame().read_register(name)
        require(not v.is_unavailable and not v.is_optimized_out, 'helper_register_unavailable')
        return int(v) & ((1 << 64) - 1)

    def tid(self):
        t = self.g.selected_thread()
        require(t is not None and t.is_valid(), 'helper_thread_unknown')
        return list(t.ptid)

    def site(self, name, frame):
        site = self.m['caller']['sites'][name]
        require(self.offset(frame, self.m['caller']) == site['offset'], 'helper_exact_caller_site')
        pc = int(frame.pc())
        require(self.memory(pc - 5, 5).hex() == site['before'] and self.memory(pc, 8).hex() ==
                site['after'], 'helper_caller_site_bytes')
        return True

    def marker(self):
        # Atomic metadata only. Never infer LOAD from IDLE or a result-stage log.
        p = Path(self.b['runtime']['marker_path'])
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            s = os.fstat(fd)
            require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1
                    and not s.st_mode & 0o077 and s.st_size <= 4096, 'helper_marker_rights')
            raw = os.read(fd, 4097)
            require(len(raw) <= 4096, 'helper_marker_bound')
        finally:
            os.close(fd)
        return json.loads(raw)

    def window(self):
        c = self.ensure()
        c.window(self.marker(), self.n['phase'](), self.n['STATE']['process'], time.monotonic(),
                 self.n['STATE']['records'], self.n['get_active']())
        self.original_check()

    def parse_environment(self, raw):
        require(raw.endswith(b'\0') and len(raw) <= 128 * 1024, 'helper_environment_bound_or_termination')
        items = raw[:-1].split(b'\0') if raw != b'\0' else []
        require(len(items) <= 512 and all(b'=' in v and v.split(b'=', 1)[0] for v in items),
                'helper_environment_encoding')
        pairs = [v.split(b'=', 1) for v in items]
        env = dict(pairs)
        require(len(env) == len(pairs), 'helper_environment_duplicates')
        return env

    def current_environment(self, pid, *, expected_pointer=None):
        """Observe effective __environ from this stopped owned parent only.

        /proc/PID/environ retains the exec-time memory range, whereas setenv can
        replace both vector and strings. At the exact spawn call, also bind r9
        to this vector. No DWARF availability or symbol-name resolution assumed.
        """
        original = self.n['STATE']['process']
        inf = self.g.selected_inferior()
        require(original is not None and inf.num == 1 and inf.pid == pid == original['pid'],
                'helper_runtime_environment_original_only')
        before = self.original_check()
        require(all(t.is_valid() and t.is_stopped() for t in inf.threads()), 'helper_runtime_environment_all_stop')
        libc = self.m['images']['libc']
        require(libc['sha256'] == ENV_SOURCE['libc_sha256'], 'helper_runtime_environment_source_pin')
        self.pin(libc)
        base = self.base(pid, libc['path'])
        regions = []
        for line in self.bounded(Path('/proc') / str(pid) / 'maps', 512 * 1024).decode('ascii').splitlines():
            f = line.split(None, 5)
            start, end = (int(v, 16) for v in f[0].split('-'))
            regions.append((start, end, f[1], f[5] if len(f) == 6 else ''))

        def read(address, count, *, owner=None):
            require(type(address) is int and 0 < address < 1 << 47 and 0 < count <= 64,
                    'helper_runtime_environment_memory_bound')
            matches = [r for r in regions if r[0] <= address and address + count <= r[1] and 'r' in r[2]
                       and (owner is None or r[3] == owner)]
            require(len(matches) == 1, 'helper_runtime_environment_readable_mapping')
            return self.memory(address, count)

        for prefix in ('load', 'dereference', 'call'):
            data = bytes.fromhex(ENV_SOURCE[prefix + '_bytes'])
            require(read(base + ENV_SOURCE[prefix + '_offset'], len(data), owner=libc['path']) == data,
                    'helper_runtime_environment_instruction')
        storage = int.from_bytes(read(base + ENV_SOURCE['got_offset'], 8, owner=libc['path']), 'little')
        require(storage == base + ENV_SOURCE['storage_offset'], 'helper_runtime_environment_symbol_interposition')
        # __environ is in the anonymous zero-fill tail of this exact libc's
        # final PT_LOAD, not in a pathname-bearing /proc mapping.
        require(any(r[0] == base + ENV_SOURCE['zero_fill_start'] and r[0] <= storage and storage + 8 <= r[1]
                    and r[2] == 'rw-p' and r[3] == '' for r in regions)
                and any(r[1] == base + ENV_SOURCE['zero_fill_start'] and r[3] == libc['path'] for r in regions)
                and storage + 8 <= base + ENV_SOURCE['data_memory_end'],
                'helper_runtime_environment_libc_zero_fill')

        def snapshot():
            vector = int.from_bytes(read(storage, 8, owner=''), 'little')
            require(vector > 0 and vector % 8 == 0 and (expected_pointer is None or vector == expected_pointer),
                    'helper_runtime_environment_spawn_pointer')
            items = []
            total = 0
            for index in range(513):
                address = int.from_bytes(read(vector + index * 8, 8), 'little')
                if address == 0:
                    return vector, self.parse_environment(b'\0'.join(items) + b'\0')
                require(index < 512, 'helper_runtime_environment_vector_bound')
                item = bytearray()
                for _ in range(32769):
                    byte = read(address + len(item), 1)
                    total += 1
                    require(total <= 128 * 1024, 'helper_runtime_environment_total_bound')
                    if byte == b'\0':
                        break
                    item.extend(byte)
                    require(len(item) <= 32768, 'helper_runtime_environment_item_bound')
                else:
                    raise RuntimeError('helper_runtime_environment_item_bound')
                items.append(bytes(item))
            raise RuntimeError('helper_runtime_environment_vector_bound')

        pointer, env = snapshot()
        require((pointer, env) == snapshot() and self.original_check() == before
                and inf.pid == pid, 'helper_runtime_environment_snapshot_changed')
        return env

    def environment(self, pid, *, initial=False, expected_pointer=None):
        env = (self.current_environment(pid, expected_pointer=expected_pointer) if initial else
               self.parse_environment(self.bounded(Path('/proc') / str(pid) / 'environ', 128 * 1024)))
        self.audit_actual_env = env
        require(os.readlink(Path('/proc') / str(pid) / 'cwd') == '/tmp/friday-metric-work', 'helper_child_cwd_changed')
        expected = {k.encode(): v.encode() for k, v in self.m['environment'].items()} if initial else dict(self.original_env)
        if not initial and b'PWD' not in expected and b'PWD' in env:
            expected[b'PWD'] = b'/tmp/friday-metric-work'
        self.audit_expected_env = expected
        require(all(env.get(k.encode()) == v.encode() for k, v in self.m['environment'].items()), 'helper_environment_changed')
        require(not any(k in env for k in (b'PAPERSIZE', b'LC_PAPER', b'LD_PRELOAD', b'LD_AUDIT', b'ENV', b'BASH_ENV')),
                'helper_environment_override')
        require(all(not os.path.lexists(p) for p in self.m['absent_paths']), 'helper_paper_config_present')
        if initial:
            initial_env = self.parse_environment(self.bounded(Path('/proc') / str(pid) / 'environ', 128 * 1024))
            self.audit_font_initial = initial_env
            self.audit_initial_env = initial_env
            # Existing font CAS observes initial /proc. This proves equivalence
            # for its selected keys at THIS stopped boundary, not a later CAS.
            require(all(env.get(k) == initial_env.get(k) for k in FONT_ENV_KEYS),
                    'helper_font_runtime_environment_changed')
            self.original_env = env
        else:
            require(env == expected, 'helper_inherited_environment_changed')
        return True

    def boundary_metadata(self, pid, stage, role, *, refusal=None):
        """Bounded sanitized sidecar; never raw values, argv, mapped paths/data.

        It does not expand the native trace schema or confer runtime admission.
        A failed diagnostic write cannot replace the first underlying refusal.
        """
        allowed = ('popen', 'spawn', 'dash_exec', 'dash_entry', 'dash_birth', 'paperconf_exec', 'paperconf_entry', 'metric')
        require(stage in allowed and role in ('parent', 'dash', 'paperconf'), 'helper_diagnostic_stage')
        rows = []
        actual = getattr(self, 'audit_actual_env', None)
        expected = getattr(self, 'audit_expected_env', None)
        value_hash = lambda value: None if value is None else hashlib.sha256(value).hexdigest()
        keys = sorted(set(expected or {}) | set(actual or {}))
        retained = list(getattr(self, 'metadata_keys', FONT_ENV_KEYS))
        for key in keys:
            if key not in retained and len(retained) < 64:
                retained.append(key)
        self.metadata_keys = retained
        selected = [key for key in keys if key in retained]
        for key in selected:
            label = {'key': key.decode('ascii')} if re.fullmatch(rb'[A-Za-z_][A-Za-z0-9_]{0,63}', key) else {'key_sha256': value_hash(key)}
            rows.append(dict(label, expected_value_sha256=value_hash((expected or {}).get(key)),
                             actual_value_sha256=value_hash((actual or {}).get(key))))
        entry = dict(stage=stage, role=role, pid=pid, refusal=refusal, environment_key_count=len(keys),
                     environment_keys_truncated=len(selected) < len(keys))
        entry['environment_source_class'] = ('PINNED_LIBC_GOT_TO_ZERO_FILL_ENVIRON' if role == 'parent'
                                             else 'KERNEL_EXEC_ENVIRON')
        entry['inheritance_reference_class'] = ('EXACT_POSIX_SPAWN_R9' if stage == 'spawn'
                                                else 'PARENT_RUNTIME_SNAPSHOT')
        if refusal is not None:
            entry['environment'] = rows
        if actual is not None:
            entry['environment_sha256'] = hashlib.sha256(b'\0'.join(k + b'=' + actual[k] for k in sorted(actual)) + b'\0').hexdigest()
        initial = getattr(self, 'audit_font_initial', None)
        if initial is not None and actual is not None:
            entry['font_environment'] = [dict(key=k.decode('ascii'), initial_value_sha256=value_hash(initial.get(k)),
                runtime_value_sha256=value_hash(actual.get(k))) for k in FONT_ENV_KEYS]
            entry['font_runtime_equals_initial'] = all(initial.get(k) == actual.get(k) for k in FONT_ENV_KEYS)
            entry['font_scope'] = 'THIS_STOPPED_BOUNDARY_ONLY_NOT_FONT_CAS_POSTCONDITION'
            changed = sorted(k for k in set(initial) | set(actual) if initial.get(k) != actual.get(k))
            entry['exec_initial_to_runtime_changed_key_count'] = len(changed)
            entry['exec_initial_to_runtime_changed_keys'] = [
                dict({'key': k.decode('ascii')} if re.fullmatch(rb'[A-Za-z_][A-Za-z0-9_]{0,63}', k)
                     else {'key_sha256': value_hash(k)}, initial_value_sha256=value_hash(initial.get(k)),
                     runtime_value_sha256=value_hash(actual.get(k))) for k in changed if k in retained]
            entry['exec_initial_to_runtime_keys_truncated'] = any(k not in retained for k in changed)
        fds = []
        try:
            numbers = sorted(int(p.name) for p in (Path('/proc') / str(pid) / 'fd').iterdir())
            entry['fd_count'] = len(numbers)
            for number in numbers[:8]:
                try:
                    fds.append(dict(number=number, **self.fd(pid, number)))
                except Exception as exc:
                    fds.append(dict(number=number, observation_error_class=type(exc).__name__))
            entry['fds_truncated'] = len(numbers) > 8
        except Exception as exc:
            entry['fd_observation_error_class'] = type(exc).__name__
        entry['fds'] = fds
        for name, value in (('stdin', self.original_stdin), ('stderr', self.original_stderr), ('stdout_pipe', self.pipe)):
            entry['expected_' + name] = value
        prior = list(getattr(self, 'environment_proof', ()))
        require(len(prior) < 8, 'helper_diagnostic_stage_bound')
        prior.append(entry)
        value = dict(schema='frw.calc.paper-helper-boundary-metadata.v1',
            operation_id=self.b['runtime']['operation_id'], nonce=self.b['runtime']['nonce'],
            source_sha256=self.b['runtime']['source_sha256'], manifest_ref=self.b['runtime']['manifest_ref'],
            original=self.n['STATE']['process'], scope='HASHED_ENV_NUMERIC_FD_ONLY_NO_RUNTIME_ADMISSION', stages=prior)
        raw = (json.dumps(value, sort_keys=True) + '\n').encode()
        require(len(raw) <= 32768, 'helper_diagnostic_output_bound')
        path = Path('/tmp/friday-metric-work/paper-helper-boundary.json')
        tmp = path.with_suffix('.pending')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        self.environment_proof = prior

    def custody_boundary(self, pid, stage, role, *, initial=False, redirection=False, expected_pointer=None):
        self.audit_actual_env = self.audit_expected_env = self.audit_font_initial = self.audit_initial_env = None
        try:
            self.environment(pid, initial=initial, expected_pointer=expected_pointer)
            if role == 'parent':
                self.parent_fds(pid)
            else:
                self.fds(pid, role, redirection=redirection)
        except Exception as exc:
            try:
                self.boundary_metadata(pid, stage, role, refusal=str(exc) if type(exc) is RuntimeError else type(exc).__name__)
            except Exception:
                pass  # Preserve the original terminal refusal, never resume.
            raise
        # Keep successful runtime getter/font projection proofs for Root's join.
        if initial:
            self.boundary_metadata(pid, stage, role)
        return True

    def fd(self, pid, number):
        root = Path('/proc') / str(pid)
        p = root / 'fd' / str(number)
        s = p.stat()
        text = self.bounded(root / 'fdinfo' / str(number), 4096).decode('ascii')
        fields = dict(line.split(':', 1) for line in text.splitlines() if ':' in line)
        flags = int(fields['flags'].strip(), 8)
        return {'dev': s.st_dev, 'ino': s.st_ino, 'type': stat.S_IFMT(s.st_mode),
                'rdev': s.st_rdev, 'access': flags & os.O_ACCMODE,
                'cloexec': bool(flags & os.O_CLOEXEC)}

    def null(self, fd):
        s = Path('/dev/null').stat()
        return fd['type'] == stat.S_IFCHR and fd['rdev'] == s.st_rdev

    def same_fd(self, a, b):
        return all(a[k] == b[k] for k in ('dev', 'ino', 'type', 'rdev', 'access'))

    def fds(self, pid, role, *, redirection=False):
        numbers = [int(p.name) for p in (Path('/proc') / str(pid) / 'fd').iterdir()]
        require(len(numbers) <= (4 if redirection else 3) and {0, 1, 2}.issubset(numbers), 'helper_extra_FD')
        current = {n: self.fd(pid, n) for n in numbers}
        require(self.null(current[0]) and self.same_fd(current[0], self.original_stdin)
                and current[1]['type'] == stat.S_IFIFO and current[1]['access'] == os.O_WRONLY,
                'helper_stdin_stdout_FD')
        if self.pipe is None:
            self.pipe = current[1]
        require(self.same_fd(current[1], self.pipe), 'helper_stdout_pipe_changed')
        if role == 'dash' and not redirection:
            require(self.same_fd(current[2], self.original_stderr), 'helper_shell_initial_stderr')
        else:
            require(self.null(current[2]) and current[2]['access'] == os.O_WRONLY, 'helper_stderr_not_null')
        for number in set(numbers) - {0, 1, 2}:
            require(redirection and current[number]['cloexec'] and self.same_fd(current[number], self.original_stderr),
                    'helper_unapproved_inherited_FD')
        return True

    def child(self, role):
        c = self.c.e['children'][0 if role == 'dash' else 1]
        inf = self.g.selected_inferior()
        value = self.proc(inf.pid)
        require(all(value[k] == c[k] for k in ('pid', 'ppid', 'start_ticks')), 'helper_selected_child_identity')
        return dict(value, inferior=inf.num)

    def image(self, role, pid):
        image = self.m['images'][role]
        root = Path('/proc') / str(pid)
        require(os.readlink(root / 'exe') == image['path'], 'helper_exec_path')
        with (root / 'exe').open('rb') as f:
            require(hashlib.file_digest(f, 'sha256').hexdigest() == image['sha256'], 'helper_exec_hash')
        expected = ([b'sh', b'-c', b'--', b'paperconf 2>/dev/null'] if role == 'dash' else [b'paperconf'])
        require(self.bounded(root / 'cmdline', 256) == b'\0'.join(expected) + b'\0', 'helper_exec_argv')
        return True

    def loaded_images(self, role, pid, *, entry):
        allowed = {self.m['images'][k]['path']: self.m['images'][k] for k in
                   ([role, 'libc', 'loader'] + (['libpaper'] if role == 'paperconf' else []))}
        actual = {v[4] for v in self.maps(pid)}
        required = set(allowed) if entry else {self.m['images'][role]['path'], self.m['images']['loader']['path']}
        require(required.issubset(actual) and actual.issubset(set(allowed)), 'helper_mapped_image_set')
        for path in actual:
            self.pin(allowed[path])
        # At exec-stop libc/libpaper need not exist yet. At e_entry both must.
        return True

    def publish(self):
        if self.c is not None:
            self.n['STATE']['load_dependency'] = self.c.snapshot()
        self.n['save']()

    def breakpoint(self, address, fn, *, one_shot=True):
        class ObserverBreakpoint(self.g.Breakpoint):
            def stop(self):
                # GDB may evaluate this predicate more than once while deciding
                # an all-stop event. It must not advance the one-shot custody.
                # The actual BreakpointEvent is consumed once by dispatch().
                return True
        bp = ObserverBreakpoint('*' + hex(address), internal=True)
        # Installed GDB exposes this writable property (also statically present
        # in its exact binary). An absolute Office address must not be inserted
        # into a helper's different address space after exec.
        bp.inferior = self.g.selected_inferior().num
        require(bp.inferior == self.g.selected_inferior().num, 'helper_breakpoint_inferior_binding')
        self.breakpoints.append(bp)
        self.stop_handlers[bp.number] = (bp, fn, one_shot)
        return bp

    def queue_stop(self, event):
        """Queue only a real helper BreakpointEvent, never a stop predicate."""
        hits = [b for b in getattr(event, 'breakpoints', ())
                if b.number in self.stop_handlers or b.number in self.retired_breakpoints]
        if not hits:
            return False
        if self.n['STATE']['error'] is not None:
            return True  # First refusal is terminal; cleanup cannot advance custody.
        require(len(hits) == 1 and len(event.breakpoints) == 1 and self.pending_stop is None,
                'helper_ambiguous_or_duplicate_stop_event')
        inf = self.g.selected_inferior()
        number = hits[0].number
        require(number not in self.retired_breakpoints, 'helper_retired_breakpoint_event')
        bp, fn, one_shot = self.stop_handlers[number]
        require(bp.is_valid() and bp.enabled is True, 'helper_disabled_breakpoint_event')
        require(inf.num == bp.inferior and inf.pid > 0, 'helper_stop_event_inferior')
        self.pending_stop = (bp, fn, one_shot, inf.num, inf.pid, self.tid(), int(self.g.newest_frame().pc()))
        return True

    def install(self):
        if self.installed or not self.n['STATE']['process'] or self.g.selected_inferior().num != 1:
            return
        pid = self.n['STATE']['process']['pid']
        try:
            libc_base = self.base(pid, self.m['images']['libc']['path'])
            caller_base = self.base(pid, self.m['caller']['path'])
        except RuntimeError as e:
            if str(e) == 'helper_image_base':
                return
            raise
        self.ensure()
        # Keep the popen entry armed for the entire launch: any second invocation
        # or invocation outside this LOAD still reaches the unchanged refusal.
        self.breakpoint(libc_base + self.m['images']['libc']['entry'], self.popen, one_shot=False)
        self.breakpoint(libc_base + ENV_SOURCE['call_offset'], self.spawn_environment)
        for name, fn in (('popen_return', self.popen_return), ('fgets_return', self.eof), ('pclose_return', self.pclose_return)):
            self.breakpoint(caller_base + self.m['caller']['sites'][name]['offset'], fn)
        self.installed = True

    def popen(self):
        self.window()
        require(self.g.selected_inferior().num == 1, 'helper_popen_foreign_inferior')
        f = self.g.newest_frame()
        libc = self.m['images']['libc']
        entry = self.offset(f, libc) == libc['entry'] and self.memory(int(f.pc()), 16).hex() == libc['entry_bytes']
        caller = self.site('popen_return', f.older())
        # Exactly known bounded strings, including their NUL; unknown bytes never logged.
        command = self.memory(self.register('rdi'), len(b'paperconf 2>/dev/null\0')) == b'paperconf 2>/dev/null\0'
        mode = self.memory(self.register('rsi'), 2) == b'r\0'
        self.c.arm(self.tid(), exact_entry=entry, exact_caller=caller, command_equal=command, mode_equal=mode)
        self.custody_boundary(self.g.selected_inferior().pid, 'popen', 'parent', initial=True)

    def parent_fds(self, pid):
        current_stdin = self.fd(pid, 0)
        current_stderr = self.fd(pid, 2)
        require(self.original_stdin is None or self.same_fd(current_stdin, self.original_stdin),
                'helper_parent_stdin_changed')
        require(self.original_stderr is None or self.same_fd(current_stderr, self.original_stderr),
                'helper_parent_stderr_changed')
        self.original_stdin = current_stdin
        require(self.null(self.original_stdin) and self.original_stdin['access'] == os.O_RDONLY,
                'helper_parent_stdin_custody')
        self.original_stderr = current_stderr
        require(self.original_stderr['type'] == stat.S_IFREG and self.original_stderr['access'] == os.O_WRONLY,
                'helper_parent_stderr_custody')
        log = Path('/tmp/friday-metric-work/gdb.log')
        require(not log.is_symlink(), 'helper_log_symlink')
        s = log.stat()
        require(s.st_uid == os.getuid() and s.st_nlink == 1 and stat.S_IMODE(s.st_mode) == 0o600,
                'helper_log_custody')
        require((self.original_stderr['dev'], self.original_stderr['ino']) == (s.st_dev, s.st_ino),
                'helper_parent_stderr_not_owned_log')

    def spawn_environment(self):
        self.window()
        require(self.g.selected_inferior().num == 1 and self.tid() == self.c.thread
                and self.c.e['state'] == 'ARMED' and not self.spawn_env_verified,
                'helper_spawn_environment_order')
        libc = self.m['images']['libc']
        require(self.offset(self.g.newest_frame(), libc) == ENV_SOURCE['call_offset']
                and self.memory(int(self.g.newest_frame().pc()), 5).hex() == ENV_SOURCE['call_bytes'],
                'helper_spawn_environment_callsite')
        self.custody_boundary(self.g.selected_inferior().pid, 'spawn', 'parent', initial=True,
                              expected_pointer=self.register('r9'))
        self.spawn_env_verified = True

    def birth(self):
        self.window()
        inf = self.g.selected_inferior()
        p = self.proc(inf.pid)
        role = 'dash' if len(self.c.e['children']) == 0 else 'paperconf'
        if role == 'dash':
            require(inf.num == 1 and self.tid() == self.c.thread, 'helper_parent_thread')
            require(self.spawn_env_verified, 'helper_spawn_environment_unbound')
            frames = []
            f = self.g.newest_frame()
            for _ in range(16):
                if f is None or not f.is_valid():
                    break
                frames.append(f)
                f = f.older()
            libc = self.m['images']['libc']
            offsets = []
            for frame in frames:
                try:
                    offsets.append(self.offset(frame, libc))
                except RuntimeError:
                    pass
            require(all(v in offsets for v in self.m['libc_spawn_returns'])
                    and any(self.site_bool('popen_return', f) for f in frames), 'helper_libc_spawn_route')
        else:
            self.child('dash')
            require(self.c.e['children'][0]['entry_verified'], 'helper_shell_not_at_entry')
            f = self.g.newest_frame().older()
            require(self.offset(f, self.m['images']['dash']) == self.m['dash_vfork_return']
                    and self.memory(int(f.pc()) - 5, 5).hex() == 'e800a4ffff', 'helper_shell_vfork_callsite')
            self.custody_boundary(inf.pid, 'dash_birth', 'dash', redirection=True)
        tid = self.tid()
        text = self.bounded(Path('/proc') / str(inf.pid) / 'task' / str(tid[1]) / 'children', 256).decode('ascii')
        numbers = text.split()
        require(len(numbers) == 1 and numbers[0].isdecimal(), 'helper_exact_direct_child')
        child = self.proc(int(numbers[0]))
        self.c.birth({'pid': p['pid'], 'start_ticks': p['start_ticks']}, child, route_ok=True)
        self.known[child['pid']] = child

    def site_bool(self, name, frame):
        try:
            return self.site(name, frame)
        except RuntimeError:
            return False

    def exec(self):
        self.window()
        role = 'dash' if len(self.c.e['execs']) == 0 else 'paperconf'
        child = self.child(role)
        self.image(role, child['pid'])
        self.custody_boundary(child['pid'], role + '_exec', role)
        self.loaded_images(role, child['pid'], entry=False)
        self.c.exec(role, child, exact_image=True, exact_argv=True, custody_ok=True)
        address = self.base(child['pid'], self.m['images'][role]['path']) + self.m['images'][role]['entry']
        self.to_create.append((address, lambda: self.entry(role)))

    def entry(self, role):
        self.window()
        child = self.child(role)
        image = self.m['images'][role]
        require(self.offset(self.g.newest_frame(), image) == image['entry']
                and self.memory(int(self.g.newest_frame().pc()), 16).hex() == image['entry_bytes'], 'helper_image_entry_bytes')
        self.image(role, child['pid'])
        self.custody_boundary(child['pid'], role + '_entry', role)
        self.loaded_images(role, child['pid'], entry=True)
        self.c.entry(role, child, images_ok=True, custody_ok=True)

    def popen_return(self):
        self.window()
        self.site('popen_return', self.g.newest_frame())
        self.stream = self.register('rax')
        require(self.stream != 0, 'helper_popen_failed')
        fd = int.from_bytes(self.memory(self.stream + 112, 4), 'little', signed=True)
        require(2 < fd < 4096, 'helper_stream_FD')
        actual = self.fd(self.n['STATE']['process']['pid'], fd)
        # Opposite pipe access, same kernel pipe inode. Do not open/read its data.
        require(self.pipe is not None and actual['type'] == stat.S_IFIFO and actual['access'] == os.O_RDONLY
                and (actual['dev'], actual['ino']) == (self.pipe['dev'], self.pipe['ino']), 'helper_popen_pipe_binding')
        self.c.popen_return(self.tid(), pipe_ok=True)

    def eof(self):
        self.window()
        self.site('fgets_return', self.g.newest_frame())
        flags = int.from_bytes(self.memory(self.stream, 4), 'little')
        self.c.eof(self.tid(), empty_eof=self.register('rax') == 0 and bool(flags & 0x10) and not bool(flags & 0x20))

    def pclose_return(self):
        self.window()
        self.site('pclose_return', self.g.newest_frame())
        status = self.register('rax') & 0xffffffff
        absent = all(not (Path('/proc') / str(c['pid'])).exists() for c in self.c.e['children'])
        self.original_check()
        self.c.close(self.tid(), status, time.monotonic(), children_absent=absent, original_ok=True)

    def boundary(self, event):
        if self.n['STATE']['error'] is not None:
            return
        kinds = [self.catchpoints.get(b.number) for b in getattr(event, 'breakpoints', ()) if b.type == self.g.BP_CATCHPOINT]
        require(len(kinds) == 1 and kinds[0] in ('vfork', 'exec'), 'helper_unexpected_fork_or_catchpoint')
        if kinds[0] == 'vfork':
            self.birth()
        else:
            self.exec()
        self.pending = 'CONTINUE'
        self.publish()

    def exited(self, event):
        inf = getattr(event, 'inferior', None)
        require(inf is not None, 'helper_exit_inferior_unknown')
        if self.n['STATE']['error'] is not None:
            return inf.num != 1
        if inf.num == 1:
            if self.c is not None:
                self.c.metric()
            return False  # Caller alone owns original Office exit_code.
        self.ensure()
        self.c.exit(inf.num, getattr(event, 'exit_code', None))
        self.pending = 'CONTINUE'
        self.publish()
        return True

    def dispatch(self):
        if self.n['STATE']['error'] is not None:
            self.pending_stop = None
            self.to_create.clear()
            self.pending = None
            return None
        stopped, self.pending_stop = self.pending_stop, None
        if stopped is not None:
            bp, fn, one_shot, number, pid, thread, pc = stopped
            try:
                inf = self.g.selected_inferior()
                require(bp.number not in self.retired_breakpoints and bp.is_valid() and bp.enabled is True,
                        'helper_stop_breakpoint_changed')
                require((inf.num, inf.pid, self.tid(), int(self.g.newest_frame().pc())) ==
                        (number, pid, thread, pc), 'helper_stop_event_context_changed')
                fn()
                if one_shot:
                    # The fixed caller visits each return site once per popen;
                    # both helper entries are one-shot too. Retire only AFTER
                    # its exact value/context checks succeed, outside stop().
                    # All-stop helper exits can leave original at this same PC.
                    # A disabled inferior-specific breakpoint still participates
                    # in GDB's solib re-set. Its child inferior can disappear on
                    # exit, so destroy the consumed one-shot outside callbacks.
                    retired_number = bp.number
                    bp.delete()
                    require(not bp.is_valid(), 'helper_breakpoint_retirement_failed')
                    self.stop_handlers.pop(retired_number)
                    self.breakpoints.remove(bp)
                    self.retired_breakpoints.add(retired_number)
                self.pending = 'CONTINUE'
                self.publish()
            except Exception as e:
                self.n['fail'](str(e) if type(e) is RuntimeError else type(e).__name__)
                return None
        for address, fn in self.to_create:
            self.breakpoint(address, fn)
        self.to_create.clear()
        result, self.pending = self.pending, None
        return result

    def metric_ready(self):
        self.ensure().metric()
        marker = self.marker()
        expected = dict(schema=self.p['MARKER'], state='LOAD_CLOSED', **{k: self.b['runtime'][k] for k in
            ('operation_id', 'nonce', 'source_sha256', 'manifest_ref', 'operation_deadline_monotonic')})
        require(marker == expected, 'helper_LOAD_not_closed_before_metric')
        require(all(not (Path('/proc') / str(c['pid'])).exists() for c in self.c.e['children']), 'helper_child_present_before_metric')
        self.original_check()

    def original_selected(self):
        for inf in self.g.inferiors():
            if inf.num == 1 and inf.pid:
                self.g.execute('inferior 1', to_string=True)
                return True
        return False

    def identity_scope(self):
        """Extra terminal inferiors never replace the original numeric identity."""
        for inf in self.g.inferiors():
            if not inf.pid or inf.num == 1:
                continue
            require(self.c is not None and self.c.e['state'] != 'CLOSED' and inf.pid in self.known,
                    'helper_foreign_live_inferior')
            require(self.proc(inf.pid) == self.known[inf.pid], 'helper_live_inferior_birth')
        return True
