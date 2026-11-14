"""Prospective Root-controlled one-received-copy trusted-Basic Calc component. No run on import.

--check-only reads reviewed source/input metadata only. --execute additionally
requires a fresh Root grant, exact independent review, exclusive existing slot,
and an otherwise empty Root-created finite cgroup. It never creates a service.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
ASSIGNMENT = 'ASTRA-F04-RECEIVED-XLSX-APP-PREP-20261114#1'
UNIT = 'frw-astra-f04-received-xlsx-20261114-g1.service'
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
TOOLCHAIN = Path('/home/jericho/.jericho/toolchains/libreoffice-26.2.5.2-ubuntu26.04-amd64')
PREFIX = '/opt/friday-document-toolchain'
PROGRAM = PREFIX + '/root/usr/lib/libreoffice/program'
WORK = ROOT / 'operation'
SOURCE = Path('/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods')
SOURCE_SHA = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
SOURCE83_SHA = '87e2a8e37e6a28e63d09f148e997a55783875d528efa7a4e09e4409e626d336c'
DELTA = {'kind': 'additional_independent_numeric_plus_one', 'sheet_index': 1,
         'cell': 'C2', 'before': '2', 'after': '3', 'addend': '1'}
OLD_OUTPUTS = {'608bade9881fc66a6d0d16ee4ebb2d9899222fcf9eeb3b7ed297c7fe16e9cadf',
               'b0a686b3b15a58dc149861d01843df968ed8f247c3a8c284ff304ecc5157a5db'}
OLD_PREFIXES = ('/home/jericho/.cache/FRW-ASTRA-CALC-REAL-',
                '/home/jericho/.cache/FRW-ASTRA-NATIVE-CALC-REAL-APP-RECALC-',
                '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-RECEIVED-COPY-APP-ENTRY-PREP-')
BINDING_KEYS = {'schema', 'state', 'assignment', 'source', 'received',
                'ordinary_request', 'ordinary_request_sha256', 'delta',
                'conversion_assessment', 'custody', 'phase_authority', 'installed_current'}
PIN_KEYS = {'path', 'bytes', 'sha256', 'identity'}
IDENTITY_KEYS = {'dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns'}
EXPECTED_COUNTS = '1:2:1:2:1:1'



def need(ok, code):
    if not ok:
        raise ValueError(code)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum=1000000):
    p = Path(path)
    for ancestor in (p, *p.parents):
        need(not ancestor.is_symlink(), 'LINK')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        first = os.fstat(stream.fileno())
        need(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
             and first.st_nlink == 1 and first.st_size <= maximum, 'CUSTODY')
        raw = stream.read(maximum + 1)
        last = os.fstat(stream.fileno())
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid,
                     s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(key(first) == key(last) == key(p.lstat()) and len(raw) == first.st_size, 'CAS')
    return raw


def ref(path, maximum=1000000):
    raw = read(path, maximum)
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def save(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def identity(info):
    return dict(dev=info.st_dev, ino=info.st_ino, mode=info.st_mode, uid=info.st_uid,
                gid=info.st_gid, nlink=info.st_nlink, size=info.st_size,
                mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


def input_pin(path, maximum=2 * 1024**2):
    # Capture identity and bytes in one no-follow descriptor observation. Neither
    # hashing nor a path alone establishes Root's external received custody.
    p = Path(path)
    need(p.is_absolute() and '..' not in p.parts, 'ABSOLUTE_INPUT_PATH')
    for ancestor in (p, *p.parents):
        need(not ancestor.is_symlink(), 'LINK')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        first = os.fstat(stream.fileno())
        need(stat.S_ISREG(first.st_mode) and first.st_uid == os.getuid()
             and first.st_nlink == 1 and 0 < first.st_size <= maximum
             and not first.st_mode & 0o022, 'INPUT_CUSTODY')
        raw = stream.read(maximum + 1)
        last = os.fstat(stream.fileno())
    need(identity(first) == identity(last) == identity(p.lstat())
         and len(raw) == first.st_size, 'INPUT_CAS')
    return {'path': str(p), 'bytes': len(raw), 'sha256': sha(raw),
            'identity': identity(first)}, raw


def validate_pin(row):
    need(type(row) is dict and set(row) == PIN_KEYS, 'INPUT_PIN_SCHEMA')
    need(type(row['path']) is str and Path(row['path']).is_absolute()
         and '..' not in Path(row['path']).parts, 'INPUT_PIN_PATH')
    need(type(row['bytes']) is int and 0 < row['bytes'] <= 2 * 1024**2, 'INPUT_SIZE')
    need(type(row['sha256']) is str and len(row['sha256']) == 64
         and all(c in '0123456789abcdef' for c in row['sha256']), 'INPUT_DIGEST')
    x = row['identity']
    need(type(x) is dict and set(x) == IDENTITY_KEYS
         and all(type(v) is int and v >= 0 for v in x.values()), 'INPUT_IDENTITY')
    need(stat.S_ISREG(x['mode']) and not x['mode'] & 0o022
         and x['uid'] == os.getuid() and x['nlink'] == 1
         and x['size'] == row['bytes'], 'INPUT_IDENTITY_CUSTODY')


def validate_ref(row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'REF_SCHEMA')
    need(type(row['path']) is str and Path(row['path']).is_absolute()
         and '..' not in Path(row['path']).parts, 'REF_PATH')
    need(type(row['bytes']) is int and 0 < row['bytes'] <= 1000000, 'REF_SIZE')
    need(type(row['sha256']) is str and len(row['sha256']) == 64
         and all(c in '0123456789abcdef' for c in row['sha256']), 'REF_DIGEST')


def validate_binding(binding):
    # A deliberately incomplete template fails here before any file or slot read,
    # subprocess, work directory, intent, clock creation or Office admission.
    need(type(binding) is dict and binding.get('state') == 'ROOT_BOUND_FUTURE_RECEIVED_COPY_ONCE', 'UNBOUND')
    need(set(binding) == BINDING_KEYS
         and binding['schema'] == 'friday.Root.F04.received-xlsx-input.v1'
         and binding['assignment'] == ASSIGNMENT, 'BINDING_SCHEMA')
    for key in ('source', 'received'):
        validate_pin(binding[key])
    source, received = binding['source'], binding['received']
    need(source['path'] == str(SOURCE) and source['bytes'] == 16538
         and source['sha256'] == SOURCE_SHA, 'WRONG_SOURCE')
    need(received['sha256'] != SOURCE_SHA and received['sha256'] not in OLD_OUTPUTS
         and received['path'] != source['path']
         and not any(received['path'].startswith(p) for p in OLD_PREFIXES)
         and not Path(received['path']).is_relative_to(ROOT), 'NOT_FUTURE_RECEIVED')
    # Actual ordinary request bytes are an opaque Root-owned file pin. They are
    # distinct from Source83's canonical semantic request and the App delta.
    validate_ref(binding['ordinary_request'])
    need(binding['ordinary_request_sha256'] == binding['ordinary_request']['sha256'],
         'ORDINARY_REQUEST_PIN')
    need(type(binding['delta']) is dict and canonical(binding['delta']) == canonical(DELTA), 'DELTA')
    ordinary = binding['conversion_assessment']
    need(type(ordinary) is dict and set(ordinary) == {
         'receipt', 'state', 'assessor_sha256', 'source_sha256',
         'received_sha256', 'request_sha256'}
         and ordinary['state'] in ('SELECTED_REQUIRED_BYTES_MATCH_SOURCE_PROJECTION',
                                  'SELECTED_STRUCTURE_MATCH_WITH_CACHE_GAPS')
         and ordinary['assessor_sha256'] == SOURCE83_SHA
         and ordinary['source_sha256'] == SOURCE_SHA
         and ordinary['received_sha256'] == received['sha256']
         and type(ordinary['request_sha256']) is str
         and len(ordinary['request_sha256']) == 64
         and all(c in '0123456789abcdef' for c in ordinary['request_sha256']),
         'CONVERSION_QUALIFICATION')
    validate_ref(ordinary['receipt'])
    for key in ('custody', 'phase_authority', 'installed_current'):
        validate_ref(binding[key])
    return binding


def verify_current_inputs(binding):
    for key in ('source', 'received'):
        actual, _ = input_pin(binding[key]['path'])
        need(actual == binding[key], 'CURRENT_INPUT_' + key.upper())
    for row in [binding['ordinary_request'], binding['conversion_assessment']['receipt']] + [binding[k] for k in ('custody', 'phase_authority', 'installed_current')]:
        need(ref(Path(row['path']), row['bytes']) == row, 'ROOT_EVIDENCE_PIN')


def check_only(binding_path=None):
    binding_path = ROOT / 'ROOT-INPUT.json' if binding_path is None else Path(binding_path)
    need(binding_path == ROOT / 'ROOT-INPUT.json', 'FIXED_ROOT_INPUT')
    binding_raw = read(binding_path, 65536)
    binding = validate_binding(json.loads(binding_raw))
    raw = read(ROOT / 'PLAN.json', 65536)
    plan = json.loads(raw)
    need(plan['assignment'] == ASSIGNMENT and plan['execution_grant'] is False, 'PLAN')
    for row in plan['local_sources'] + plan['selected_toolchain_refs']:
        need(0 < row['bytes'] <= 32 * 1024**2, 'PIN_READ_BUDGET')
        need(ref(Path(row['path']), row['bytes']) == row, 'SOURCE_PIN')
    verify_current_inputs(binding)
    need(stat.S_IMODE(ROOT.stat().st_mode) == 0o700 and not ROOT.is_symlink(), 'ROOT_MODE')
    return plan, raw, binding, binding_raw


def validate_clock(start, now):
    need(type(start) in (int, float) and type(now) in (int, float)
         and 0 <= now - start < 15, 'FRESH_UNIT_START')
    return start + 270, start + 300


def validate_copy(staged, received):
    validate_pin(staged)
    need(staged['path'] == str(WORK / 'received-copy.xlsx')
         and staged['sha256'] == received['sha256']
         and staged['bytes'] == received['bytes']
         and (staged['identity']['dev'], staged['identity']['ino'])
             != (received['identity']['dev'], received['identity']['ino']), 'COPY_BYTES_IDENTITY')


def validate_saved(before, after):
    need(before is not None and before == after
         and before['path'] == str(WORK / 'controlledcopy-saved.xlsx'), 'SAVED_PRE_POST_REOPEN_CAS')


def publish_reopen_gate(budget, phase_deadline, observation_deadline, now=time.monotonic):
    """Complete durable content before atomic no-replace publication.

    observation_deadline is set once at the parent's first complete receipt
    observation, not claimed to be the actual Basic CloseCalc timestamp.
    All existing work/CPU/disk and phase checks are fresh at gate publication.
    """
    pending, final = WORK / 'reopen-ready.pending', WORK / 'reopen-ready.tsv'
    need(not os.path.lexists(final), 'REOPEN_GATE_ALREADY_EXISTS')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as gate:
        gate.write(b'REOPEN_AUTHORIZED_SAME_PINNED_NEW_OUTPUT\n')
        gate.flush()
        os.fsync(gate.fileno())
    budget()
    current = now()
    need(current < phase_deadline, 'PHASE_DEADLINE')
    need(current < observation_deadline, 'HANDOFF_OBSERVATION_DEADLINE')
    # Hardlink creation is atomic and refuses an existing destination. The
    # producer sees only the complete file, never the pending file's writes.
    os.link(pending, final, follow_symlinks=False)
    pending.unlink()
    return current


def validate_capture(journal, observations, complete):
    need(complete.splitlines() == [b'COMPLETE\t1:2:1:2:1:1'], 'MAIN_COMPLETE_RECEIPT')
    expected = [
        ('OPEN_INTENT', '/work/received-copy.xlsx'), ('OPENED', '/work/received-copy.xlsx'),
        ('CHANGE_INTENT', 'FIRST_SHEET:C2:2:PLUS_ONE:3'), ('CHANGED', 'FIRST_SHEET:C2:2:PLUS_ONE:3'),
        ('CALCULATE_ALL_INTENT', 'RECEIVED_COPY'), ('CALCULATED_ALL', 'RECEIVED_COPY'),
        ('SAVE_INTENT', 'controlledcopy-saved.xlsx'), ('SAVED', 'controlledcopy-saved.xlsx'),
        ('CLOSE_INTENT', 'controlledcopy-saved.xlsx'), ('CLOSED', 'controlledcopy-saved.xlsx'),
        ('OPEN_INTENT', '/work/controlledcopy-saved.xlsx'), ('OPENED', '/work/controlledcopy-saved.xlsx'),
        ('CLOSE_INTENT', 'controlledcopy-saved.xlsx'), ('CLOSED', 'controlledcopy-saved.xlsx'),
        ('COMPLETE', EXPECTED_COUNTS)]
    need(journal.splitlines() == [(k + '\t' + v).encode() for k, v in expected], 'JOURNAL_SEQUENCE_COUNTERS')
    rows = [line.decode('utf-8').split('\t') for line in observations.splitlines()]
    need(len(rows) <= 512 and all(len(row) == 2 for row in rows), 'OBSERVATION_ROWS')
    facts = dict(rows)
    need(len(facts) == len(rows), 'OBSERVATION_DUPLICATE')
    keys = {':BEGIN', 'CONTROLLED_COPY_READONLY_REOPENED:COUNTS', 'CONTROLLED_COPY_READONLY_REOPENED:COMPLETE'}
    widths = {}
    for prefix in ('RECEIVED_COPY_BASELINE', 'CONTROLLED_COPY_BEFORE_SAVE', 'CONTROLLED_COPY_READONLY_REOPENED'):
        keys.add(prefix + ':SHEET_COUNT')
        need(facts.get(prefix + ':SHEET_COUNT') == '3', 'OBSERVATION_SHEETS')
        keys.update(prefix + ':SHEET_NAME:' + str(s) for s in range(3))
        cells = [('0:A' + str(r), 2) for r in range(2, 6)]
        cells += [('0:' + c + str(r), 1) for r in range(2, 6) for c in ('C', 'D')]
        cells += [('0:G' + str(r), 3) for r in range(2, 6)] + [('1:B2', 3)]
        for cell, kind in cells:
            base = prefix + ':'
            keys.update(base + name + ':' + cell for name in ('CELL_TYPE', 'CELL_ERROR'))
            need(facts.get(base + 'CELL_TYPE:' + cell) == str(kind)
                 and facts.get(base + 'CELL_ERROR:' + cell) == '0', 'OBSERVATION_PRIMITIVE')
            keys.add(base + ('CELL_TEXT:' if kind == 2 else 'CELL_VALUE_CSTR:') + cell)
            if kind == 3:
                keys.add(base + 'CELL_FORMULA:' + cell)
        if prefix != 'CONTROLLED_COPY_BEFORE_SAVE':
            keys.add(prefix + ':READ_ONLY')
            need(facts.get(prefix + ':READ_ONLY') == ('False' if prefix == 'RECEIVED_COPY_BASELINE' else 'True'), 'OBSERVATION_READONLY')
            for s in range(3):
                for c in range(1, 8):
                    suffix = ':' + str(s) + ':' + str(c)
                    for prop in ('WIDTH', 'OPTIMAL_WIDTH', 'COLUMN_VISIBLE'):
                        key = prefix + ':' + prop + suffix
                        keys.add(key)
                        value = facts.get(key, '')
                        need(value.isdecimal() and int(value) > 0 if prop == 'WIDTH'
                             else value in ('True', 'False'), 'OBSERVATION_WIDTH_VALUE')
                    widths[(prefix, s, c)] = facts[prefix + ':WIDTH' + suffix]
    need(set(facts) == keys and facts[':BEGIN'] == 'RECEIVED_DISPOSABLE_COPY_NOT_ORDINARY_OR_USER_DELIVERY'
         and facts['CONTROLLED_COPY_READONLY_REOPENED:COUNTS'] == EXPECTED_COUNTS
         and facts['CONTROLLED_COPY_READONLY_REOPENED:COMPLETE'] == 'RECEIVED_COPY_SAVED_CLOSED_REOPENED', 'OBSERVATION_KEYS')
    return {'same_interpreter_all3_AtoG_widths_equal': all(
                widths[('RECEIVED_COPY_BASELINE', s, c)] == widths[('CONTROLLED_COPY_READONLY_REOPENED', s, c)]
                for s in range(3) for c in range(1, 8)), 'observation_rows': len(rows),
            'exact_counter_journal': True, 'semantic_or_F04_acceptance': False}


def validate_grant(grant, plan_raw, binding_raw, review, driver_sha, now):
    need(type(grant) is dict and set(grant) == {'state', 'assignment', 'purpose', 'plan_sha256',
         'input_sha256', 'unit', 'review_path', 'review_sha256', 'fresh_root_admission'}, 'GRANT_SCHEMA')
    need(grant['state'] == 'ROOT_GRANTED_ONCE' and grant['assignment'] == ASSIGNMENT
         and grant['purpose'] == 'FUTURE_F04_RECEIVED_XLSX_C2_2_TO_3_SAVE_REOPEN_ONLY'
         and grant['plan_sha256'] == sha(plan_raw) and grant['input_sha256'] == sha(binding_raw)
         and grant['unit'] == UNIT, 'ROOT_GRANT')
    fresh = grant['fresh_root_admission']
    keys = {'at_moscow', 'exclusive_shared_slot', 'same_selected_base_toolchain',
            'current_resources_and_custody', 'old_effects_closed_or_isolated', 'source_review_accepted',
            'genuine_received_and_source83_structure_qualified', 'original_phase_positive_not_begun',
            'additional_delta_allowed_by_original_authority_and_validation', 'current_installed_permissions_cancel_CAS'}
    need(type(fresh) is dict and set(fresh) == keys
         and all(fresh[k] is True for k in keys - {'at_moscow'}), 'FRESH_ADMISSION')
    when = datetime.fromisoformat(fresh['at_moscow'])
    need(when.utcoffset() == timedelta(hours=3) and 0 <= (now - when).total_seconds() <= 120, 'FRESH_ADMISSION_AGE')
    need(type(review) is dict and review.get('verdict') == 'PASS_SOURCE_PREPARATION_ONLY'
         and review.get('driver_sha256') == driver_sha
         and review.get('plan_sha256') == sha(plan_raw), 'REVIEW_BINDING')



def birth(pid):
    return int((Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])


def cgroup_setup():
    line = Path('/proc/self/cgroup').read_text().strip()
    need(line.startswith('0::/') and line.endswith('/' + UNIT), 'OWN_CGROUP_REQUIRED')
    path = line.split(':', 2)[2]
    group = Path('/sys/fs/cgroup') / path.lstrip('/')
    need((group / 'memory.max').read_text().strip() == str(2 * 1024**3), 'CG_MEMORY')
    need((group / 'memory.swap.max').read_text().strip() == '0', 'CG_SWAP')
    quota, period = map(int, (group / 'cpu.max').read_text().split())
    need(quota == 2 * period and int((group / 'pids.max').read_text()) <= 128, 'CG_CPU_PIDS')
    members = {int(p) for p in (group / 'cgroup.procs').read_text().split()}
    need(members == {os.getpid()}, 'CG_NOT_EXCLUSIVE')
    info = subprocess.run(['/usr/bin/systemctl', '--user', 'show', UNIT,
                           '--property=ExecMainStartTimestampMonotonic,RuntimeMaxUSec,KillMode'],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, check=True, timeout=3)
    props = dict(line.split('=', 1) for line in info.stdout.splitlines())
    need(props['KillMode'] == 'control-group' and props['RuntimeMaxUSec'] in ('5min', '5min 0s', '300s', '300000000us'), 'FINITE_UNIT')
    start = int(props['ExecMainStartTimestampMonotonic']) / 1000000
    validate_clock(start, time.monotonic())
    return line, group, start


def owned(cgroup_line, group):
    result = []
    for value in (group / 'cgroup.procs').read_text().split():
        pid = int(value)
        if pid == os.getpid():
            continue
        p = Path('/proc') / value
        try:
            if (p / 'cgroup').read_text().strip() != cgroup_line:
                raise ValueError('CG_CUSTODY_CHANGED')
            need(p.stat().st_uid == os.getuid(), 'PID_OWNER')
            result.append({'pid': pid, 'birth_ticks': birth(pid)})
        except (FileNotFoundError, ProcessLookupError):
            continue
    return result


def signal_owned(item, sig, cgroup_line):
    pid = item['pid']
    fd = None
    try:
        fd = os.pidfd_open(pid)
        p = Path('/proc') / str(pid)
        need(pid != os.getpid() and p.stat().st_uid == os.getuid()
             and (p / 'cgroup').read_text().strip() == cgroup_line
             and birth(pid) == item['birth_ticks'], 'SIGNAL_CUSTODY')
        signal.pidfd_send_signal(fd, sig)
    except (ProcessLookupError, FileNotFoundError):
        pass
    finally:
        if fd is not None:
            os.close(fd)


def close_owned(proc, teardown_deadline, list_owned, send_owned, now=time.monotonic, pause=time.sleep):
    """One shared absolute deadline; injectable inert failure controls use this path."""
    errors = []
    try:
        members = list_owned()
    except BaseException as exc:
        members = None
        errors.append('ENUM_' + type(exc).__name__)
    if members:
        for item in members:
            try:
                send_owned(item, signal.SIGTERM)
            except BaseException as exc:
                errors.append('TERM_' + type(exc).__name__)
        until = min(teardown_deadline, now() + 1)
        while now() < until:
            if proc is not None:
                try:
                    proc.poll()
                except BaseException as exc:
                    errors.append('POLL_' + type(exc).__name__)
            try:
                members = list_owned()
            except BaseException as exc:
                members = None
                errors.append('ENUM_' + type(exc).__name__)
                break
            if not members:
                break
            pause(min(.02, max(0, until - now())))
    if members:
        for item in members:
            try:
                send_owned(item, signal.SIGKILL)
            except BaseException as exc:
                errors.append('KILL_' + type(exc).__name__)
    if proc is not None:
        try:
            proc.wait(timeout=max(0, teardown_deadline - now()))
        except BaseException as exc:
            errors.append('REAP_' + type(exc).__name__)
    while now() < teardown_deadline:
        try:
            members = list_owned()
        except BaseException as exc:
            members = None
            errors.append('FINAL_ENUM_' + type(exc).__name__)
            break
        if not members:
            break
        pause(min(.02, max(0, teardown_deadline - now())))
    try:
        members = list_owned()
    except BaseException as exc:
        members = None
        errors.append('CLOSURE_ENUM_' + type(exc).__name__)
    reaped = proc is None or proc.returncode is not None
    return {'confirmed': members == [] and reaped, 'members_remaining': members,
            'handle_reaped': reaped, 'errors': errors, 'deadline': teardown_deadline}


def limits():
    cpus = sorted(os.sched_getaffinity(0))[:2]
    need(bool(cpus), 'CPU_AFFINITY')
    os.sched_setaffinity(0, cpus)
    for key, value in ((resource.RLIMIT_CPU, 60), (resource.RLIMIT_AS, 1536 * 1024**2),
                       (resource.RLIMIT_FSIZE, 16 * 1024**2), (resource.RLIMIT_CORE, 0),
                       (resource.RLIMIT_NOFILE, 256)):
        resource.setrlimit(key, (value, value))


def command(phase):
    need(phase in ('--terminate_after_init', 'macro:///Standard.Module1.InitOnly',
                   'macro:///Standard.Module1.Main'), 'FIXED_PHASE')
    args = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--as-pid-1', '--cap-drop', 'ALL', '--clearenv', '--ro-bind', '/usr', '/usr']
    for alias in ('bin', 'sbin', 'lib', 'lib64'):
        p = Path('/') / alias
        if p.exists():
            resolved = p.resolve()
            need(resolved.is_relative_to('/usr'), 'HOST_ALIAS')
            args += ['--symlink', str(resolved), str(p)]
    args += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/opt',
             '--ro-bind', str(TOOLCHAIN), PREFIX, '--ro-bind', '/usr/share', PREFIX + '/.host-share',
             '--ro-bind', str(TOOLCHAIN / 'share-merged'), '/usr/share', '--dir', '/etc']
    for p in ('/etc/fonts', '/etc/ld.so.cache', '/var/cache/fontconfig'):
        if Path(p).exists():
            args += ['--ro-bind', p, p]
    args += ['--bind', str(WORK), '/work']
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/work', 'TMPDIR': '/work/tmp',
           'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'SAL_USE_VCLPLUGIN': 'svp',
           'MAX_CONCURRENCY': '2', 'XDG_CACHE_HOME': '/work/cache',
           'XDG_CONFIG_HOME': '/work/config', 'XDG_RUNTIME_DIR': '/work/tmp',
           'LD_LIBRARY_PATH': PROGRAM + ':' + PREFIX + '/root/usr/lib/x86_64-linux-gnu',
           'URE_BOOTSTRAP': 'vnd.sun.star.pathname:' + PROGRAM + '/fundamentalrc'}
    for key, value in env.items():
        args += ['--setenv', key, value]
    args += ['--chdir', '/work', '--remount-ro', '/', '--', PROGRAM + '/soffice.bin',
             '-env:UserInstallation=file:///work/profile', '--headless', '--nologo',
             '--norestore', '--nodefault', '--nofirststartwizard', phase]
    return args


def registration():
    base = WORK / 'profile/user/basic'
    names = ('dialog.xlc', 'script.xlc', 'Standard/dialog.xlb', 'Standard/script.xlb', 'Standard/Module1.xba')
    found = sorted(str(p.relative_to(base)) for p in base.rglob('*') if p.suffix in ('.xba', '.xlb', '.xlc'))
    need(found == sorted(names), 'REGISTRATION_FILES')
    return {name: ref(base / name) for name in names}


def profile_ready(snapshot, helper):
    need(registration() == snapshot, 'REGISTRATION_DRIFT')
    raw = read(WORK / 'profile/user/registrymodifications.xcu')
    tree = helper.ET.fromstring(raw)
    need(helper.property_values(tree, '/org.openoffice.Setup/Office', 'ooSetupInstCompleted') == ['true'], 'CURRENT_SETUP_NOT_READY')
    need(helper.property_values(tree, '/org.openoffice.Office.Common/Security/Scripting', 'MacroSecurityLevel') == ['0'], 'CURRENT_TRUSTED_LIBRARY_SECURITY')
    restart = helper.property_values(tree, '/org.openoffice.Setup/Office', 'OfficeRestartInProgress')
    need(restart in ([], ['true'], ['false']), 'CURRENT_RESTART_FLAG')
    native_marker = read(WORK / 'profile/user/extensions/buildid', 1024).rstrip(b'\r\n')
    version = read(TOOLCHAIN / 'root/usr/lib/libreoffice/program/versionrc', 4096)
    expected = next(line.split(b'=', 1)[1] for line in version.splitlines() if line.startswith(b'buildid='))
    need(native_marker == expected, 'ACTUAL_NATIVE_BUILDID')
    return {'registry_sha256': sha(raw), 'native_buildid_sha256': sha(native_marker),
            'current_setup_true': True, 'current_trusted_library_MacroSecurityLevel': 0,
            'OfficeRestartInProgress_preserved': restart,
            'same_full_registration': True, 'read_only_guard': True}


def execute(grant_path, grant_sha):
    os.umask(0o077)
    plan, plan_raw, binding, binding_raw = check_only()
    need(Path(grant_path) == ROOT / 'ROOT-GRANT.json', 'FIXED_ROOT_GRANT')
    grant_raw = read(grant_path, 65536)
    need(sha(grant_raw) == grant_sha, 'GRANT_PIN')
    grant = json.loads(grant_raw)
    review_raw = read(grant['review_path'], 65536)
    need(sha(review_raw) == grant['review_sha256'], 'REVIEW_PIN')
    review = json.loads(review_raw)
    validate_grant(grant, plan_raw, binding_raw, review, sha(read(__file__)), datetime.now(timezone.utc))
    need(not os.path.lexists(WORK) and shutil.disk_usage(ROOT).free >= 256 * 1024**2, 'ONCE_OR_DISK')
    cgroup_line, group, start = cgroup_setup()
    actor_deadline, teardown_deadline = validate_clock(start, time.monotonic())
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    lock = os.open(SLOT, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    proc = None
    report = {'assignment': ASSIGNMENT, 'state': 'INTENT', 'unit': UNIT, 'cgroup': str(group),
              'boot_id': boot_id, 'actual_unit_start_monotonic': start,
              'actor_deadline': actor_deadline, 'teardown_deadline': teardown_deadline,
              'phases': [], 'Office_model_send_service_or_product_home_calls_in_preparation': 0,
              'component_only_not_ordinary_or_formal_acceptance': True, 'no_repeat_allowed': True,
              'input_sha256': sha(binding_raw), 'received_sha256': binding['received']['sha256'],
              'saved_before_reopen': None}
    lock_held = False
    staged_pin = None
    try:
        s = os.fstat(lock)
        need(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1, 'SLOT_CUSTODY')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_held = True
        WORK.mkdir(mode=0o700)
        def budget():
            need(time.monotonic() < actor_deadline, 'ACTOR_DEADLINE')
            usage = dict(line.split() for line in (group / 'cpu.stat').read_text().splitlines())
            need(int(usage['usage_usec']) <= 100000000, 'WHOLE_UNIT_CPU100')
            total = sum(p.stat().st_size for p in WORK.rglob('*') if p.is_file() and not p.is_symlink())
            need(total <= 128 * 1024**2, 'DISK128')
        def phase(name, tail, seconds, allowed=(0,)):
            nonlocal proc
            budget()
            need(not owned(cgroup_line, group), 'PRIOR_PHASE_CHILDREN_REMAIN')
            deadline = min(actor_deadline, time.monotonic() + seconds)
            record = {'name': name, 'start_monotonic': time.monotonic(), 'phase_deadline': deadline}
            report['phases'].append(record)
            with (WORK / (name + '.stdout')).open('xb') as stdout, (WORK / (name + '.stderr')).open('xb') as stderr:
                proc = subprocess.Popen(command(tail), stdin=subprocess.DEVNULL,
                                        stdout=stdout, stderr=stderr, start_new_session=True,
                                        env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}, preexec_fn=limits)
                record['handle'] = {'pid': proc.pid, 'birth_ticks': birth(proc.pid), 'boot_id': boot_id}
                save(WORK / (name + '.PROCESS.json'), record)
                while proc.poll() is None:
                    budget()
                    if name == 'main-received-copy-once' and (WORK / 'saved-closed.tsv').exists() and report['saved_before_reopen'] is None:
                        record['saved_closed_first_observed_monotonic'] = time.monotonic()
                        record['handoff_observation_deadline'] = min(deadline, actor_deadline,
                            record['saved_closed_first_observed_monotonic'] + 30)
                        need(read(WORK / 'saved-closed.tsv', 128).splitlines() == [b'SAVED_CLOSED\t1:1:1:1:1:1'], 'SAVED_CLOSED_RECEIPT')
                        need(staged_pin is not None and input_pin(WORK / 'received-copy.xlsx')[0] == staged_pin, 'STAGED_INPUT_CHANGED')
                        verify_current_inputs(binding)
                        output_pin, _ = input_pin(WORK / 'controlledcopy-saved.xlsx')
                        need(output_pin['sha256'] != binding['received']['sha256'], 'SAVED_UNCHANGED')
                        report['saved_before_reopen'] = output_pin
                        save(WORK / 'SAVED-BEFORE-REOPEN.json', output_pin)
                        record['reopen_gate_published_monotonic'] = publish_reopen_gate(
                            budget, deadline, record['handoff_observation_deadline'])
                    need(time.monotonic() < deadline, 'PHASE_DEADLINE')
                    time.sleep(min(.02, max(0, deadline - time.monotonic())))
                record['returncode'] = proc.wait(timeout=max(0, deadline - time.monotonic()))
                record['elapsed_seconds'] = time.monotonic() - record['start_monotonic']
                need(record['returncode'] in allowed, 'PHASE_EXIT')
                need(not owned(cgroup_line, group), 'PHASE_NAMESPACE_OR_CHILD_REMAINS')
            return record['returncode']
        try:
            save(WORK / 'INTENT.json', report)
            (WORK / 'tmp').mkdir(mode=0o700)
            phase('early-document-free-init', '--terminate_after_init', 15)
            helper = load_module('_owned_preserving_profile', ROOT / 'profile_helper.py')
            macro = read(ROOT / 'calc.bas', 65536).decode() + '\n\' Owner stage: ' + str(WORK) + '\n'
            helper.prepare(WORK, macro, ROOT)
            snapshot = registration()
            save(WORK / 'FULL-MODULE-REGISTRATION.json', snapshot)
            report['profile_guards'] = [profile_ready(snapshot, helper)]
            ready = False
            for index in (1, 2, 3):
                report['profile_guards'].append(profile_ready(snapshot, helper))
                need(not (WORK / 'received-copy.xlsx').exists() and not (WORK / 'controlledcopy-saved.xlsx').exists(), 'INIT_DOCUMENTS_PRESENT')
                need(not (WORK / 'init-entered.tsv').exists() and not (WORK / 'init-only.tsv').exists() and not (WORK / 'init-failed.tsv').exists()
                     and not (WORK / 'journal.tsv').exists(), 'INIT_ALREADY_ENTERED_OR_FAILED')
                code = phase('document-free-macro-init-' + str(index), 'macro:///Standard.Module1.InitOnly', 15, (0, 81))
                report['profile_guards'].append(profile_ready(snapshot, helper))
                if code == 0:
                    need(read(WORK / 'init-only.tsv', 128).splitlines() == [b'INIT_ONLY\tCOMPONENTS=0']
                         and read(WORK / 'init-entered.tsv', 128).splitlines() == [b'INIT_ONLY_ENTERED']
                         and not (WORK / 'init-failed.tsv').exists(), 'CLEAN0_COMPONENT_RECEIPT')
                    ready = True
                    break
                # Only a normal document-FREE restart exit81 with no entered
                # callback/receipt may advance; never repeat a document effect.
                need(not any((WORK / n).exists() for n in ('init-entered.tsv', 'init-only.tsv', 'init-failed.tsv', 'journal.tsv')), 'INIT81_PARTIAL_OR_UNKNOWN')
            need(ready, 'DOCUMENT_FREE_STARTUP_EXHAUSTED')
            verify_current_inputs(binding)
            received_pin, raw = input_pin(binding['received']['path'])
            need(received_pin == binding['received'], 'STAGE_RECEIVED_PIN')
            fd = os.open(WORK / 'received-copy.xlsx', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            staged_pin, _ = input_pin(WORK / 'received-copy.xlsx')
            validate_copy(staged_pin, binding['received'])
            save(WORK / 'STAGED-RECEIVED-PIN.json', staged_pin)
            (WORK / 'MAIN-LAUNCH-ONCE').mkdir(mode=0o700)
            report['profile_guards'].append(profile_ready(snapshot, helper))
            phase('main-received-copy-once', 'macro:///Standard.Module1.Main', 180)
            report['profile_guards'].append(profile_ready(snapshot, helper))
            report['capture'] = validate_capture(read(WORK / 'journal.tsv', 16384),
                read(WORK / 'observations.tsv', 131072), read(WORK / 'complete.tsv', 128))
            report['state'] = 'ACTOR_COMPLETED_PENDING_CLOSURE_AND_OFFLINE_ASSESSMENT'
        except BaseException as exc:
            report['state'] = 'PARTIAL_OR_UNKNOWN_PRESERVE_NO_REPEAT'
            report['failure_class'] = type(exc).__name__
        finally:
            closure = close_owned(proc, teardown_deadline,
                                  lambda: owned(cgroup_line, group),
                                  lambda item, sig: signal_owned(item, sig, cgroup_line))
            report['closure'] = closure
            report['elapsed_since_actual_unit_start'] = time.monotonic() - start
            report['outputs'] = []
            report['source_unchanged'] = False
            if not closure['confirmed']:
                report['state'] = 'STOP_UNCONFIRMED_PRESERVE_NO_REPEAT'
            else:
                try:
                    verify_current_inputs(binding)
                    need(staged_pin is not None and input_pin(WORK / 'received-copy.xlsx')[0] == staged_pin, 'STAGED_POSTPIN')
                    report['source_unchanged'] = True
                    output = WORK / 'controlledcopy-saved.xlsx'
                    if output.exists():
                        actual, _ = input_pin(output)
                        report['outputs'].append(actual)
                        validate_saved(report['saved_before_reopen'], actual)
                    if report['state'] == 'ACTOR_COMPLETED_PENDING_CLOSURE_AND_OFFLINE_ASSESSMENT':
                        need(len(report['outputs']) == 1, 'OUTPUT_COUNT')
                        report['state'] = 'CLOSED_COMPONENT_OUTPUTS_OFFLINE_SEMANTICS_UNASSESSED'
                except BaseException as exc:
                    report['state'] = 'POSTCONDITION_FAILED_PARTIAL_OR_UNKNOWN_PRESERVE_NO_REPEAT'
                    report['postcondition_failure_class'] = type(exc).__name__
            try:
                save(WORK / 'CLOSED.json', report)
            except BaseException as exc:
                report['closure_record_failure_class'] = type(exc).__name__
                report['state'] = 'CLOSURE_RECORD_FAILED_PRESERVE_NO_REPEAT'
            # Never inspect/remove a live actor's profile. Own generated profile
            # is reproducible; retain source/registration hashes and observations.
            if closure['confirmed']:
                cleanup_error = None
                try:
                    for name in ('profile', 'tmp', 'cache', 'config'):
                        p = WORK / name
                        if p.exists():
                            shutil.rmtree(p)
                except BaseException as exc:
                    cleanup_error = type(exc).__name__
                try:
                    save(WORK / 'PROFILE-CLEANUP.json', {'actor_closed': True, 'error_class': cleanup_error})
                except BaseException as exc:
                    report['profile_cleanup_record_failure_class'] = type(exc).__name__
        print(json.dumps({'state': report['state'], 'outputs_retained': len(report['outputs']),
                          'closure_confirmed': report['closure']['confirmed'], 'ordinary_or_formal_PASS': False}))
        return 0 if report['state'] == 'CLOSED_COMPONENT_OUTPUTS_OFFLINE_SEMANTICS_UNASSESSED' else 1
    finally:
        if lock_held:
            fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)


def main(argv=None):
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check-only', action='store_true')
    mode.add_argument('--execute', action='store_true')
    ap.add_argument('--grant')
    ap.add_argument('--grant-sha')
    args = ap.parse_args(argv)
    if args.check_only:
        _, raw, binding, _ = check_only()
        print(json.dumps({'state': 'SOURCE_PREFLIGHT_ONLY_NO_OFFICE_SLOT_OR_WRITES', 'plan_sha256': sha(raw),
                          'received_sha256': binding['received']['sha256'], 'execution_grant': False}))
        return 0
    need(args.grant and args.grant_sha, 'EXPLICIT_ROOT_GRANT_REQUIRED')
    return execute(args.grant, args.grant_sha)


if __name__ == '__main__':
    raise SystemExit(main())
