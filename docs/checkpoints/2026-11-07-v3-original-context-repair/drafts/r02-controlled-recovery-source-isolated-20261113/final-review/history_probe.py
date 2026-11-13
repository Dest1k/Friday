"""Small independent native-history negative controls; no transport or sealed-harness call."""
import datetime
import hashlib
import importlib
import json
import os
import pathlib
import resource
import shutil
import sys
import time
import types

F = pathlib.Path(__file__).resolve().parent
B = F.parent
WORK = F / 'own-history-stand'
LIMIT = 100 * 1024 * 1024
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_FSIZE, (LIMIT, LIMIT))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.chdir(F)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def signature(path):
    info = path.stat()
    return dict(sha256=digest(path.read_bytes()), dev=info.st_dev, inode=info.st_ino,
                uid=info.st_uid, mode=oct(info.st_mode & 0o777), nlink=info.st_nlink,
                bytes=info.st_size, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)

def audit(event, args):
    def allowed(path):
        if isinstance(path, int):
            return True
        return pathlib.Path(os.fsdecode(path)).resolve().is_relative_to(F)
    denied = False
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        denied = writing and not allowed(path)
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate'}:
        denied = not allowed(args[0])
    elif event in {'os.rename', 'os.link', 'os.symlink'}:
        denied = not allowed(args[0]) or not allowed(args[1])
    elif event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork'}:
        denied = True
    if denied:
        os._exit(94)

sys.addaudithook(audit)
started = time.monotonic()
started_msk = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat()
assert not WORK.exists()
WORK.mkdir(mode=0o700)
source_before = {}
rows = []
peak_disk = 0
passed = False
try:
    exact = WORK / 'exact'
    pins = json.loads((B / 'file-fixture/sourcepins.json').read_text())['files']
    for entry in pins:
        original = pathlib.Path(entry['copy'])
        relative = original.relative_to(B / 'file-fixture/exact')
        dest = exact / relative
        dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        raw = original.read_bytes()
        assert digest(raw) == entry.get('copy_sha256', entry.get('sha256'))
        source_before[str(original)] = signature(original)
        dest.write_bytes(raw)
        dest.chmod(0o600)
    sys.path.insert(0, str(exact))
    current = {}
    def module(name, **attributes):
        obj = types.ModuleType(name)
        obj.__dict__.update(attributes)
        sys.modules[name] = obj
    def check_home(home):
        assert pathlib.Path(home) == current['home']
    module('hermes_constants', get_hermes_home=lambda: current['home'], assert_named_profile_home_live=check_home)
    module('gateway.config', Platform=object)
    module('gateway.session', SessionSource=object)
    module('gateway.session_identity', canonical_identity=None, restore_identity=None)
    delivery = importlib.import_module('gateway.run_plugin_delivery')
    native = importlib.import_module('hermes_cli.friday_native_state')
    from hermes_cli.plugins_state import PluginState
    route = dict(transport_profile='review', runtime_profile='review', bot_id='81001',
                 source=dict(platform='telegram', chat_id='81002', chat_type='dm', user_id='81003', thread_id=None, message_id='81004'))
    class Cap:
        key = 'independent-owned-history-probe'
        checks = 0
        def check(self):
            self.checks += 1
    for defect in ('journal_hash_name', 'journal_mode'):
        case = WORK / defect
        current['home'] = case / 'home'
        current['home'].mkdir(mode=0o700, parents=True)
        document = current['home'] / 'own-original.txt'
        document.write_bytes(b'Fresh independent nonsensitive original, never transported.\n')
        document.chmod(0o600)
        cap = Cap()
        state, selection, value = delivery._begin_ordinary_document(cap, 'own-original.txt', document.read_bytes(), route, document.name)
        directory = state.data_dir
        journals = list(directory.glob('friday-*.json'))
        assert len(journals) == 3
        retained = next(p for p in journals if json.loads(p.read_bytes()).get('relative_path') == 'own-original.txt')
        # Own synthetic namespace only: keep one original UNKNOWN journal so the
        # malformed entry is unambiguously the one inspected by the real reader.
        for path in journals:
            if path != retained:
                path.unlink()
        def read_error():
            try:
                delivery._ordinary_prior_attempt(state, cap, selection, 'own-original.txt', route)
            except native.NativeCommitUncertain as error:
                return dict(type=type(error).__name__, primary_type=type(error.primary).__name__,
                            primary=str(error.primary), stage=error.stage, replaced=error.replaced)
            raise AssertionError('real history consumer unexpectedly accepted')
        clean_error = read_error()
        assert clean_error['primary'] == 'delivery_requires_reconciliation'
        if defect == 'journal_hash_name':
            renamed = retained.with_name('friday-unknown-' + '0' * 64 + '.json')
            retained.rename(renamed)
            retained = renamed
            expected_primary = 'ordinary_document_history_invalid'
        else:
            retained.chmod(0o600)
            expected_primary = 'native_state_custody_not_private'
        before = dict(document=signature(document), current_state=signature(state.path), journal=signature(retained))
        error = read_error()
        after = dict(document=signature(document), current_state=signature(state.path), journal=signature(retained))
        assert error['primary'] == expected_primary
        assert error['replaced'] is False
        assert before == after
        assert all(signature(pathlib.Path(path)) == sig for path, sig in source_before.items())
        used = sum(p.stat().st_size for p in WORK.rglob('*') if p.is_file())
        peak_disk = max(peak_disk, used)
        assert used < LIMIT
        rows.append(dict(case=defect, real_clean_guard=clean_error, real_corrupt_guard=error,
                         before=before, after=after, original_and_state_and_corrupt_journal_unchanged=True,
                         sealed_source_bytes_and_identity_unchanged=True, cap_checks=cap.checks,
                         transport_invocations=0, disk_bytes=used))
    passed = True
finally:
    shutil.rmtree(WORK)
    own = resource.getrusage(resource.RUSAGE_SELF)
    result = dict(status='PASS' if passed else 'FAIL', started_msk=started_msk,
                  finished_msk=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),
                  wall_s=time.monotonic()-started, cpu_s=own.ru_utime+own.ru_stime,
                  max_rss_kib=own.ru_maxrss, peak_disk_bytes=peak_disk,
                  limits=dict(cpu_s=120, wall_external_s=300, AS_bytes=536870912, disk_bytes=LIMIT, core_bytes=0),
                  scope='Actual unchanged _begin_ordinary_document/_ordinary_prior_attempt, PluginState and native transaction on own tiny private files; synthetic capability and route; no send/restart/powerloss/live acceptance.',
                  caveat='Own malformed journal construction and redundant own journal removal are deliberate test setup; this does not recreate or repair any historical product effect.',
                  rows=rows, source_before=source_before,
                  cleanup=dict(own_stand_removed=not WORK.exists(), children_spawned=0, detached_processes=0,
                               foreign_writes=False, network_or_model_or_service_or_runtime_calls=False))
    out = F / 'HISTORY-PROBE.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], cases=len(rows), wall_s=result['wall_s'],
                          cleanup=result['cleanup'], sha256=digest(out.read_bytes()))))
