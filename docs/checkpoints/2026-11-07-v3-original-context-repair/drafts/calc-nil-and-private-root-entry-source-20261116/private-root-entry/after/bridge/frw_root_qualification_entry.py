"""Private administrative Root entry, never a model tool or public CLI.

This is the same trust boundary as the supplied Root runner: explicit owner
delegation and trusted Root execution authorize the administrative decision.
Live sole-writer/goal/current/source/slot/ONCE checks enforce its finite scope.
Neither a JSON record nor a constructor authenticates a third-party caller.
Run this only from the reviewed Root-owned runner, in a fresh native runtime.
"""
from pathlib import Path
import asyncio
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import secrets
import stat
import subprocess
import sys
import time
from types import MappingProxyType
from dataclasses import asdict, is_dataclass
from decimal import Decimal

BASE = Path(__file__).resolve().parent
ROOT_THREAD = '01a1c688-e36d-7021-8df4-9c5644a4d75b'
ROOT_GOAL_CREATED = 1794332322
CONTROL = Path('/home/jericho/.jericho/runtime/sol-link-native-control.py')
CONTROL_SHA = '7b616fe144e0641dc402f2051ef0226ff59fe132c36885474939623ba428da68'
H = Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
MARKER = '1abce3b2307212c9c03d1494e09ed037ddc55903561ce5c66de06dceafb21f80'
STAMP = '6a40da2f2b5041a33dc998d7ce659a9c599a883b9eadf6c1b16eda7a319606be'
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
_ISSUER = object()
_LIVE = {}
_RETAINED = {}  # exact failed owned operation; not a queue or retry controller


class RootEntryRefused(RuntimeError):
    """Finite local codes, without user bodies or arbitrary exception messages."""


def need(value, code):
    if not value:
        raise RootEntryRefused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def remaining(deadline):
    left = deadline - time.monotonic()
    need(math.isfinite(left) and left > 0, 'root_original_deadline')
    return left


def stamp(info):
    return tuple(getattr(info, name) for name in ('st_dev', 'st_ino', 'st_uid',
        'st_gid', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def private_bytes(path, *, expected=None, limit=1048576, modes=(0o400, 0o600)):
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path, 'root_exact_source_path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
             and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) in modes
             and 0 <= before.st_size <= limit, 'root_source_file_rights')
        chunks, size = [], 0
        while True:
            part = os.read(fd, min(65536, limit + 1 - size))
            if not part:
                break
            chunks.append(part); size += len(part)
            need(size <= limit, 'root_source_file_limit')
        raw = b''.join(chunks)
        need(stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat())
             and len(raw) == before.st_size and (expected is None or sha(raw) == expected),
             'root_source_file_CAS')
        return raw
    finally:
        os.close(fd)


def private_directory(path):
    s = path.lstat()
    need(path.is_absolute() and path.resolve() == path and stat.S_ISDIR(s.st_mode)
         and s.st_uid == os.getuid() and stat.S_IMODE(s.st_mode) == 0o700,
         'root_private_directory')


def put(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return sha(raw)


def _json_facts(value):
    if is_dataclass(value):
        return _json_facts(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_json_facts(item) for item in value]
    if type(value) is dict:
        return {key: _json_facts(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise RootEntryRefused('root_result_fact_shape')


def _retain_qualified_bytes(op, result, deadline):
    """Private durable artifacts inside original40; never a bearer proof/PASS.

    No result depends on a later caller copying transient bytes after work
    removal. Paths are fixed; no input/evidence-controlled path is accepted.
    """
    remaining(deadline)
    need(type(result) is dict and type(result.get('output')) is bytes
         and 0 < len(result['output']) <= 1000000 and type(result.get('evidence')) is dict,
         'root_qualifier_result_shape')
    evidence = ('ordinary-job.json', 'ordinary-result.json', 'ordinary-inner-result.json',
                'native-trace.json', 'native-terminal-base.json')
    need(set(result['evidence']) == set(evidence), 'root_result_evidence_names')
    refs = {}
    for name, raw in [('qualified-output.xlsx', result['output'])] + [
            (name, result['evidence'][name]) for name in evidence]:
        remaining(deadline)
        need(type(raw) is bytes and 0 < len(raw) <= 1048576, 'root_result_evidence_bound')
        fd = os.open(op / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        refs[name] = dict(path=str(op / name), sha256=sha(raw), bytes=len(raw))
    facts = {key: value for key, value in result.items() if key not in ('output', 'evidence')}
    put(op / 'Root-result.json', dict(status='PRIVATE_FINITE_QUALIFIER_CANDIDATE',
        artifact_refs=refs, facts=_json_facts(facts), production_enabled=False,
        admission_or_artifacts_are_bearer_authority=False))
    remaining(deadline)
    return refs


def _root_current(deadline, *, admission):
    """Real administrative client, bounded by the ORIGINAL remaining budget.

    Keep the supplied NativeControl constructor/route validation and call
    protocol. The client uses no appended 5/10/2 second timeout beyond Dp.
    It does not mutate either TUI/profile/goal/queue and never polls a model.
    """
    remaining(deadline)
    # Existing helper can be0644 under protected Root home; never chmod it.
    control_raw = private_bytes(CONTROL, expected=CONTROL_SHA,
                                modes=(0o400, 0o600, 0o644))
    control_globals = {'__name__': 'frw_verified_native_control',
                       '__file__': str(CONTROL), '__package__': None}
    exec(compile(control_raw, str(CONTROL), 'exec'), control_globals)
    C = control_globals['NativeControl']

    async def observe():
        from websockets.asyncio.client import unix_connect
        control = C('astra')  # actual sole visible writer/thread/profile check
        need(control.thread == ROOT_THREAD, 'root_native_thread')
        async with asyncio.timeout(remaining(deadline)):
            async with unix_connect(str(control.endpoint), uri='ws://localhost/',
                    compression=None, open_timeout=min(5, remaining(deadline)),
                    close_timeout=0, max_size=8_000_000) as ws:
                control.ws = ws
                result = await control.call('initialize', {
                    'clientInfo': {'name': 'friday_peer_control', 'version': '1'},
                    'capabilities': {'experimentalApi': True}})
                need(result.get('codexHome') == control.home, 'root_native_home')
                await ws.send(json.dumps({'method': 'initialized'}))
                goal = (await control.call('thread/goal/get', {'threadId': control.thread}))['goal']
                need(goal['threadId'] == ROOT_THREAD and goal['status'] == 'active'
                     and goal['createdAt'] == ROOT_GOAL_CREATED, 'root_owner_pause_or_epoch')
                if admission:
                    queue = await control.call('thread/queue/list',
                        {'threadId': control.thread, 'limit': 100})
                    need(not queue['data'] and queue.get('nextCursor') is None,
                         'root_admission_queue_not_empty')
        return dict(threadId=ROOT_THREAD, status='active', createdAt=ROOT_GOAL_CREATED)

    try:
        result = asyncio.run(observe())
        remaining(deadline)
        return result
    except BaseException:
        # No child diagnostics/private message is copied to public results.
        raise RootEntryRefused('root_live_authority_unavailable_or_stopped') from None


def _current_install_and_services(deadline):
    remaining(deadline)
    need(sha(private_bytes(H / 'FRIDAY-INSTALL.json', expected=MARKER,
                          modes=(0o400, 0o600, 0o644, 0o664))) == MARKER,
         'root_installed_marker')
    private_bytes(H / 'hermes-agent/install-stamp.json', expected=STAMP,
                  modes=(0o400, 0o600, 0o644, 0o664))
    services = []
    for unit in ('hermes-gateway-1b7e7667.service', 'hermes-dashboard.service'):
        result = subprocess.run(['systemctl', '--user', 'show', unit,
            '--property=Id,ActiveState,SubState,MainPID,InvocationID,RuntimeMaxUSec,NRestarts'],
            check=True, capture_output=True, text=True,
            timeout=min(10, remaining(deadline)))
        value = dict(row.split('=', 1) for row in result.stdout.splitlines())
        need(value.get('ActiveState') == 'active' and value.get('SubState') == 'running'
             and value.get('RuntimeMaxUSec') == 'infinity'
             and value.get('MainPID', '0').isdigit() and int(value['MainPID']) > 0,
             'root_services_not_healthy')
        services.append(value)
    remaining(deadline)
    return services


def _source_current(binding, deadline):
    remaining(deadline)
    raw = private_bytes(binding['manifest_path'], expected=binding['manifest_sha256'], limit=262144)
    manifest = json.loads(raw)
    need(manifest['kind'] == 'ROOT_FIRST_ORDINARY_CALC_QUALIFIER'
         and type(manifest['files']) is list and 1 <= len(manifest['files']) <= 128,
         'root_source_manifest_kind')
    names = set()
    for row in manifest['files']:
        remaining(deadline)
        path = Path(row['path'])
        need(path not in names and (path.is_relative_to(binding['closure_root'])
             or path.is_relative_to(binding['closure_root'].parent / 'native')),
             'root_fixed_source_closure_path')
        names.add(path)
        private_bytes(path, expected=row['sha256'], limit=160 * 1024 * 1024)
    callback = binding['closure_root'] / 'frw_root_first_qualifier.py'
    row = next((r for r in manifest['files'] if Path(r['path']) == callback), None)
    need(row is not None, 'root_fixed_callback_missing')
    return manifest


class RootAdmission:
    """Actual administrative decision retained by the native private issuer.

    No JSON loader or public constructor. Its issuer identity is bookkeeping
    AFTER the live trusted Root decision; check repeats actual authority and
    owns sticky revocation/stop, rather than trusting an admission-time record.
    """
    def __init__(self, *, _issuer, entered, deadline, operation_id, nonce, op,
                 slot_fd, slot_stamp, source_binding, goal, services, once_sha256):
        need(_issuer is _ISSUER, 'root_unissued_admission')
        self._issued_identity = object()
        self._binding = MappingProxyType(dict(entered=entered, deadline=deadline,
            operation_id=operation_id, nonce=nonce, op=op, once_sha256=once_sha256,
            source_binding=MappingProxyType(source_binding)))
        self._slot_fd, self._slot_stamp = slot_fd, slot_stamp
        self._pid, self._uid = os.getpid(), os.getuid()
        self._revoked, self._closed, self._native_agent = False, False, None
        self._goal, self._services = goal, services
        _LIVE[self._issued_identity] = self

    @property
    def entered_monotonic(self): return self._binding['entered']
    @property
    def deadline(self): return self._binding['deadline']
    @property
    def operation_id(self): return self._binding['operation_id']
    @property
    def nonce(self): return self._binding['nonce']
    @property
    def source_binding(self): return self._binding['source_binding']
    @property
    def work_parent(self): return self.source_binding['work_parent']

    def check(self, *, _deadline_ceiling=None):
        try:
            need(_LIVE.get(self._issued_identity) is self and not self._closed
                 and not self._revoked and os.getpid() == self._pid and os.getuid() == self._uid,
                 'root_stale_or_foreign_admission')
            effective = self.deadline
            if _deadline_ceiling is not None:
                need(type(_deadline_ceiling) in (float, int)
                     and math.isfinite(_deadline_ceiling)
                     and self.entered_monotonic < _deadline_ceiling <= self.deadline,
                     'root_guard_deadline_ceiling')
                effective = min(effective, _deadline_ceiling)
            remaining(effective)
            need(stamp(os.fstat(self._slot_fd)) == self._slot_stamp
                 and stamp(SLOT.lstat()) == self._slot_stamp, 'root_slot_CAS')
            once = self._binding['op'] / 'consumed-once.json'
            private_bytes(once, expected=self._binding['once_sha256'])
            _root_current(effective, admission=False)
            remaining(effective)
        except BaseException:
            self._revoked = True
            if self._native_agent is not None:
                self._native_agent.interrupt()
            raise

    def close(self):
        self._closed = True
        _LIVE.pop(self._issued_identity, None)


def run_root_first_qualification(prepared_path, prepared_sha256, *, _original_entered=None):
    """Root-owned library call from actual delegated administrative execution.

    Prepared JSON selects exact private SOURCE/configuration only; it is NOT
    authorization. It cannot replace the actual Root checks before issuance.
    There is no public CLI, boolean approval, supplied cap/agent/callback/argv.
    """
    observed = time.monotonic()
    entered = observed if _original_entered is None else _original_entered
    need(type(entered) is float and math.isfinite(entered) and entered <= observed,
         'root_original_entry_clock')
    # The trusted bootstrap passes its earlier stamp; this private metadata
    # cannot authorize an operation and never moves an existing stamp forward.
    deadline = entered + 40
    remaining(deadline)
    need(sys.dont_write_bytecode, 'root_private_source_requires_python_B')
    prepared_path = Path(prepared_path)
    private_directory(prepared_path.parent)
    config = json.loads(private_bytes(prepared_path, expected=prepared_sha256, limit=262144))
    need(set(config) == {'kind', 'closure_root', 'manifest_path', 'manifest_sha256',
                        'work_parent', 'operation_parent'}, 'root_prepared_schema')
    need(config['kind'] == 'ROOT_FIRST_ORDINARY_CALC_QUALIFIER', 'root_fixed_kind')
    binding = dict(closure_root=Path(config['closure_root']),
                   manifest_path=Path(config['manifest_path']),
                   manifest_sha256=config['manifest_sha256'], work_parent=Path(config['work_parent']))
    # This fixed kind is neither an arbitrary-source nor an arbitrary-path API.
    need(binding['closure_root'] == BASE and binding['manifest_path'] == BASE / 'ROOT-BRIDGE-PINS.json'
         and binding['work_parent'] == BASE.parent.parent / 'future-runtime-work'
         and Path(config['operation_parent']) == BASE.parent.parent / 'operations',
         'root_fixed_prepared_paths')
    # Current rights/CAS within the clock; fixed SOURCE inspector also validates
    # exact58/35/pin when the private callback begins, never before entry T0.
    for path in (binding['closure_root'], binding['work_parent'], Path(config['operation_parent'])):
        private_directory(path)
    manifest = _source_current(binding, deadline)
    binding['fixedcallback_sha256'] = next(row['sha256'] for row in manifest['files']
        if Path(row['path']) == BASE / 'frw_root_first_qualifier.py')
    goal = _root_current(deadline, admission=True)
    services = _current_install_and_services(deadline)
    fd = os.open(SLOT, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    admission = None
    result = None
    retain_slot = False
    callback_loaded = False
    callback_module = None
    completed = False
    try:
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1
             and not info.st_mode & 0o022, 'root_exclusive_slot_rights')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        need(stamp(SLOT.lstat()) == stamp(info), 'root_exclusive_slot_identity')
        need(not (Path(config['operation_parent']) / 'unresolved-root-owned-operation.json').exists(),
             'root_prior_owned_cleanup_unresolved')
        _root_current(deadline, admission=False)
        _source_current(binding, deadline)
        remaining(deadline)
        nonce = secrets.token_hex(16)  # only actual future Root admission, never Source checks
        operation_id = 'root-ordinary-first-qualifier-' + nonce
        op = Path(config['operation_parent']) / operation_id
        op.mkdir(mode=0o700)  # exclusive genuinely new Root-owned operation
        once_sha = put(op / 'consumed-once.json', dict(operation_id=operation_id, nonce=nonce,
            entered_monotonic=entered, deadline=deadline,
            scope='ONE_PRIVATE_ORDINARY_ODS_XLSX_QUALIFIER'))
        admission = RootAdmission(_issuer=_ISSUER, entered=entered, deadline=deadline,
            operation_id=operation_id, nonce=nonce, op=op, slot_fd=fd, slot_stamp=stamp(info),
            source_binding=binding, goal=goal, services=services, once_sha256=once_sha)
        admission.check()
        # Fixed code loader only; this does not create scope or permission.
        callback_path = BASE / 'frw_root_first_qualifier.py'
        need('frw_root_first_qualifier' not in sys.modules, 'root_callback_already_loaded')
        callback_raw = private_bytes(callback_path,
            expected=binding['fixedcallback_sha256'], limit=262144, modes=(0o400,))
        callback_spec = importlib.util.spec_from_file_location('frw_root_first_qualifier', callback_path)
        callback_module = importlib.util.module_from_spec(callback_spec)
        sys.modules['frw_root_first_qualifier'] = callback_module
        callback_loaded = True
        # Execute retained verified bytes; a path loader would reread mutable
        # code after CAS and could execute transient unpinned top-level code.
        exec(compile(callback_raw, str(callback_path), 'exec'), callback_module.__dict__)
        # Native module must be the exact pinned new private kind from this
        # prepared SOURCE closure, loaded into a fresh normal native runtime.
        from hermes_cli.friday_root_qualification import _dispatch_root_ordinary_first_qualification
        try:
            result = _dispatch_root_ordinary_first_qualification(admission)
            completed = True
        except BaseException as exc:
            from hermes_cli.friday_root_qualification import RootQualificationCleanupUnknown
            if isinstance(exc, RootQualificationCleanupUnknown):
                # Retain exact original state and slot until Root reconciles
                # these owned children. No new qualification may overwrite it.
                retain_slot = True
                _RETAINED[operation_id] = (admission, exc)
                put(Path(config['operation_parent']) / 'unresolved-root-owned-operation.json',
                    dict(operation_id=operation_id, nonce=nonce, deadline=deadline,
                         state='UNKNOWN_OWNED_CLEANUP_NO_RETRY', slot_held=True))
            raise
        admission.check()  # includes owner pause between production and release
        artifacts = _retain_qualified_bytes(op, result, deadline)
        admission.check()
        remaining(deadline)
        result = dict(result, artifact_refs=artifacts)
        return result
    finally:
        # Dispatcher owns same-call stop/context teardown; slot is held through
        # it and through callback work removal. A failed call is never retried.
        if admission is not None:
            admission.close()
        if callback_loaded and sys.modules.get('frw_root_first_qualifier') is callback_module:
            sys.modules.pop('frw_root_first_qualifier', None)
        if retain_slot:
            # The Root runner owns explicit reconciliation; closing this
            # descriptor here would falsely release a still-owned live slot.
            return_slot = False
        else:
            return_slot = True
        try:
            if return_slot:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            if return_slot:
                os.close(fd)
        if completed:
            remaining(deadline)  # total includes native teardown and slot release

