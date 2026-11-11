"""Root: one exact original M14 query through unchanged atomic issuer/full v42.

No effects on import. Preparation/review precedes this invocation. No retry,
clock extension, service timer, restart, upload, producer, or canonical regrade.
"""
import contextlib
import datetime as dt
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import types

W = Path(__file__).resolve().parent
B = Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
P = Path('/home/jericho/.cache/FRW-ASTRA-V3-M14-EXACT-CONSUMER-PREP-20261111')
CP = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair')
STATE = Path('/home/jericho/.local/share/friday-telegram-bot-test')
CHAIN = Path('/home/jericho/.cache/FRW-KIMI-FMT-20261108')
PYTHON = '/home/jericho/jericho/.venv/bin/python'
SLOT = Path('/home/jericho/.jericho/runtime/locks/synthetic-live-acceptance.lock')
PINS = {
 'adapter.py': '0d0daeeb6a0e2b1c30580728c733533c5383f1cdfec43ca7dc2d5b96fe7eb336',
 'current203.py': 'c454d3e4d2f0ab65fe7e4e90f466e8be97ffb594301c6ab5654edcaea8dbe965',
 'scenario.json': '8f62ea30909fb6d365716fff93205609b5adb74d7737d09b93ae35c4fefe4bec',
}
ISSUER_SHA = 'ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518'
SCOPE_REVIEW = Path('/home/jericho/.cache/FRW-ASTRA-V3-M14-ROOT-SCOPE-COMPAT-REVIEW-20261111/RESULT.json')
SCOPE_REVIEW_SHA = '5ed2a17ebf0c53a140d7e29769639cc2281590902bbf9b0385e773e176b86916'

def require(value, why):
    if not value:
        raise ValueError(why)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + '\n').encode()

def identity(value):
    return tuple(getattr(value, key) for key in ('st_dev', 'st_ino', 'st_uid', 'st_gid',
                 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))

def read(path):
    p = Path(path)
    require(p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents)), 'absolute non-symlink input required')
    with os.fdopen(os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        raw = stream.read(24 * 1024**2 + 1)
        after = os.fstat(stream.fileno())
    require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
            and before.st_nlink == 1 and not stat.S_IMODE(before.st_mode) & 0o002
            and len(raw) <= 24 * 1024**2 and identity(before) == identity(after) == identity(p.stat()), 'unsafe or changing input')
    return raw

def ref(path):
    raw = read(path)
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}

def new(path, raw):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())

def load(path, sha, name):
    raw = read(path)
    require(digest(raw) == sha, 'reviewed source/evidence drift: ' + str(path))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module

def privacy(checker):
    # Reuse source-derived effective roots only after current config/source pins.
    basis = json.loads(read(B / 'f01-privacy-roots.json'))
    extra = json.loads(read(B / 'f01-extra-mount-roots.json'))
    corrected = json.loads(read(B / 'f01-a0-source-derived-roots-correction.json'))
    for path, sha in basis['config_pins'].items():
        require(digest(read(path)) == sha, 'effective privacy config changed')
    for item in corrected['source_refs']:
        require(digest(read(item['path'])) == item['sha256'], 'effective extra-bind source changed')
    roots = list(basis['permitted_roots'].values()) + list(extra['extra_roots'].values())
    roots += [corrected['source_roots']['A0_RUNTIME_ROOT'], corrected['source_roots']['A0_MEMORY_SOURCE']]
    private = [W, B, P, Path('/home/jericho/.cache/FRW-ASTRA-V3-M14-POST203-FORWARD-PREP-20261111')]
    for own in private:
        require(own.is_dir() and stat.S_IMODE(own.stat().st_mode) == 0o700, 'private preparation directory custody')
        for allowed in map(Path, roots):
            require(not own.resolve().is_relative_to(allowed.resolve())
                    and not allowed.resolve().is_relative_to(own.resolve()), 'private preparation in effective product roots')
    markers = tuple(str(p).encode() for p in private)
    for item in basis['context']:
        raw = read(item['path'])
        require(not any(marker in raw for marker in markers), 'private preparation in product context')
    for leaf in ('cmdline', 'environ'):
        raw = (Path('/proc/174854') / leaf).read_bytes()
        require(not any(marker in raw for marker in markers), 'private preparation in product process')
    return {'config_pins': basis['config_pins'], 'effective_roots': roots,
            'new_private_roots_disjoint': [str(p) for p in private],
            'current_source_pins': corrected['source_refs'], 'worker_qualification': False}

def main():
    require(sys.argv[1:] == ['--execute-once'], 'explicit reviewed Root entry required')
    os.umask(0o077)
    require(digest(read(SCOPE_REVIEW)) == SCOPE_REVIEW_SHA, 'independent scope review drift')
    scope_review = json.loads(read(SCOPE_REVIEW))
    require(scope_review['decision'].startswith('PASS_SOURCE_OFFLINE'), 'scope review not accepted')
    for leaf, sha in PINS.items():
        require(digest(read(W / leaf)) == sha, 'exact accepted M14 source changed')
    a = load(W / 'adapter.py', PINS['adapter.py'], 'Root_M14_adapter')
    c = load(W / 'current203.py', PINS['current203.py'], 'Root_M14_checker')
    g = load(CP / 'issue-fresh-admission.py', ISSUER_SHA, 'Root_existing_atomic_issuer')
    require(digest(read(a.BASE)) == a.BASE_SHA and read(W / 'scenario.json') == a.encoded(a.scenario()), 'base/scenario drift')
    require(not (STATE / 'runs' / (a.RUN_ID + '.json')).exists(), 'canonical M14 run already exists; reconcile only')
    for path in CHAIN.glob('INDEPENDENT-AUTHORITY-R*.json'):
        require(a.RUN_ID not in json.loads(read(path)).get('run_scenarios', {}), 'M14 authority already exists; reconcile only')
    g.RUN_ID = a.RUN_ID
    g.SCENARIO = W / 'scenario.json'
    g.EXTRA_SCENARIOS = ()
    g.PACKAGE_FILE = None
    g.ORDERED_PREDECESSORS = {}
    g.SCOPE = a.SCOPE
    g.validate_scope(a.SCOPE, {a.RUN_ID: a.SCENARIO_SHA})
    fd = os.open(SLOT, os.O_RDWR | os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        require((s.st_dev, s.st_ino, s.st_uid, s.st_nlink, stat.S_IMODE(s.st_mode))
                == (2050, 9440373, os.getuid(), 1, 0o600), 'existing shared-slot custody changed')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for lock in (STATE / 'consumer.lock', STATE / 'tester-token'):
            q = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
            try:
                s = os.fstat(q)
                require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1
                        and stat.S_IMODE(s.st_mode) == 0o600, 'canonical receiver lock custody changed')
                fcntl.flock(q, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(q)
        private = privacy(c)
        new(W / 'ROOT-ONCE-INVOCATION.json', encoded({'state': 'ONE_ROOT_PREPARATION_ISSUE_BIND_AND_DISPATCH_INVOCATION_NO_RETRY',
            'created_at': time.time(), 'source': ref(Path(__file__)), 'scope_review': ref(SCOPE_REVIEW),
            'run_id': a.RUN_ID, 'scope': a.SCOPE, 'never_delete_rename_or_retry': True}))
        actual = c.observe()
        prior = json.loads(read(B / 'M14-FIRST-ACTUAL-READONLY-OBSERVATION.json'))
        # Root's saved511/14 +653 native-user semantic review remains applicable
        # only with this exact full inventory and native boundary, not zero text matches.
        prior = prior['snapshot']
        require(actual['history'] == prior['history'] and actual['native'] == prior['native'],
                'addressed all-history/native semantic basis changed; stop and reconcile')
        semantic = json.loads(read(P / 'CURRENT203-HISTORY-REVIEW.TEMPLATE.json'))
        semantic.update(classified_run_ids=actual['history']['run_ids'],
            history_manifest_sha256=actual['history']['manifest_sha256'],
            native_boundary_sha256=actual['mutable_boundary']['native_boundary_sha256'],
            equivalent_original_phase_effects=[], compacted_unlogged_semantic_equivalents_reconciled=True,
            old_effects_UNKNOWN_and_clocks_preserved=True)
        semantic['retained_basis'] += [ref(B / 'M14-NATIVE-CANDIDATE-ROOT-INTERPRETATION.json'),
            ref(B / 'M14-TARGETED-NATIVE-SEMANTIC-CANDIDATES.json'), ref(B / 'M14-SOURCE-R3-ROOT-ACCEPTANCE.json')]
        semantic['Root_judgment'] = ('Exact addressed511 canonical runs/14 related outcomes plus653 retained sameSID native user rows/66 candidates; '
            'M03/M04/M06/R50 and old plainTXT quotes are narrower consumed stages, not this combined originalM14 postrestart source/version/quote query. '
            'Null-platform recovery notes/inline uploads are retained data, not new instructions. No equivalent original phase established. '
            'Bounded retained evidence only, no absence claim outside unretained archives; all consumed/UNKNOWN effects/clocks unchanged.')
        new(W / 'ROOT-CURRENT-HISTORY-SEMANTIC-REVIEW.json', encoded(semantic))
        proof = json.loads(read(P / 'CURRENT203-PROOF.R3.TEMPLATE.json'))
        wall, mono = time.time(), time.monotonic()
        proof.update(scope=a.SCOPE, observed=actual, history_semantic_review=ref(W / 'ROOT-CURRENT-HISTORY-SEMANTIC-REVIEW.json'),
            created_at=wall, expires_at=wall+120, created_monotonic=mono, expires_monotonic=mono+120,
            shared_slot_owner=c.transport().kernel(os.getpid()), private_oracle_excluded_from_product=True,
            same_ordinary_source_authorization_reviewed=True, Root_current_privacy=private)
        proof_path = W / 'ROOT-CURRENT203-PREQUERY-PROOF.json'
        new(proof_path, encoded(proof))
        qualified = c.check(str(proof_path), ref(proof_path)['sha256'])
        new(W / 'ROOT-ACTUAL-CURRENT-CHECK.json', encoded(qualified))
        contract = dict(schema='frw.m14.exact-original.consumer-binding.v1', status='ROOT_BOUND_EXACT_M14',
            case=a.CASE, operation_id=a.OPERATION, phase=a.PHASE, run_id=a.RUN_ID, scope=a.SCOPE,
            scenario_sha256=a.SCENARIO_SHA, sources=a.SOURCES, expected_product=a.EXPECTED203,
            adapter=ref(W / 'adapter.py'), current_gate=ref(W / 'current203.py'),
            root_current_review=ref(proof_path), root_origin_review=ref(c.LINEAGE),
            mutable_boundary=qualified['m14_mutable_boundary'])
        contract = json.loads(a.encoded(contract))
        a.contract_shape(contract)
        g.SUPERSEDES_REASON = ('One genuinely missing original M14 phase after existing supported203 restart. Root current proof '
            + ref(proof_path)['sha256'] + '; preserved historical45 unresolved/3UNKNOWN and consumed stages/clocks; no old task replay.')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            g.main()  # Existing complete atomic issuer, unchanged and invoked ONCE.
        new(W / 'ISSUER.stdout', output.getvalue().encode())
        issued = json.loads(output.getvalue())
        authority = {'path': issued['path'], 'bytes': issued['bytes'], 'sha256': issued['sha256']}
        authority_raw = read(authority['path'])
        require(len(authority_raw) == authority['bytes'] and digest(authority_raw) == authority['sha256'], 'issued authority drift')
        source = a.successor(read(a.BASE).decode(), authority, issued['authority_id'], contract)
        bound = W / 'bot_tester.m14.root-bound.py'
        new(bound, source.encode())
        binding = dict(schema='frw.Root.m14.actual-bound-full-v42.v1', authority=authority,
            authority_id=issued['authority_id'], contract=contract, source=ref(bound),
            original_base=ref(a.BASE), scenario=ref(W / 'scenario.json'))
        new(W / 'ROOT-ACTUAL-BINDING.json', encoded(binding))
        roundtrip = json.loads(read(W / 'ROOT-ACTUAL-BINDING.json'))
        rr = roundtrip['authority']
        canonical_ref = {'path': rr['path'], 'bytes': rr['bytes'], 'sha256': rr['sha256']}
        require(a.successor(read(a.BASE).decode(), canonical_ref, roundtrip['authority_id'], roundtrip['contract']).encode()
                == read(bound), 'serialized full binding does not reconstruct exact executable bytes')
        full = load(bound, ref(bound)['sha256'], 'Root_actual_M14_full_receiver')
        class EvidenceView:
            root = STATE
            runs = STATE / 'runs'
            def run_path(self, name):
                return self.runs / (name + '.json')
            def get(self, path, default=None):
                return json.loads(read(path)) if Path(path).exists() else default
        def no_wait(_seconds):
            raise ValueError('Readonly actual admission preflight may not wait')
        runner = full.Runner(EvidenceView(), None, clock=time.time, sleep=no_wait)
        runner._m14_operation = 'NEW'
        admitted = runner.ordinary_independent_admission(a.RUN_ID, a.scenario())
        del runner._m14_operation
        require(admitted['authority_id'] == issued['authority_id'], 'actual full consumer did not accept issued singleton')
        new(W / 'ROOT-FULL-CONSUMER-READONLY-ADMISSION.json', encoded({'state': 'PASS_REAL_FULL_CONSUMER_NO_STORE_API_NEW_CLOCK',
            'at': time.time(), 'binding': ref(W / 'ROOT-ACTUAL-BINDING.json'), 'authority_id': admitted['authority_id'],
            'original_run_seconds': 300, 'original_full_capture_seconds': 180, 'original_reserve_seconds': 5}))
        argv = [PYTHON, '-I', '-B', '-S', str(bound), '--state-dir', str(STATE), 'run', '--run-id', a.RUN_ID,
                '--scenario', str(W / 'scenario.json')]
        new(W / 'ROOT-DISPATCH-INVOCATION.json', encoded({'state': 'ONE_ORIGINAL_FULL_CONSUMER_INVOCATION_NO_RETRY',
            'at': time.time(), 'argv': argv, 'authority': authority, 'binding': ref(W / 'ROOT-ACTUAL-BINDING.json'),
            'canonical_run_absent': not (STATE / 'runs' / (a.RUN_ID + '.json')).exists(), 'shared_slot_owner': proof['shared_slot_owner']}))
        with os.fdopen(os.open(W / 'CONSUMER.stdout', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as out, \
             os.fdopen(os.open(W / 'CONSUMER.stderr', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as err:
            # Parent stop requests cannot release shared custody while its exact
            # finite consumer is alive. Child exec receives its normal handlers;
            # this is parent-only deferral, never a change to child budgets/stop.
            deferred_stops = []
            def defer_parent_stop(number, _frame):
                deferred_stops.append({'signal': number, 'at': time.time()})
            prior_handlers = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
            actor = None
            try:
                for number in prior_handlers:
                    signal.signal(number, defer_parent_stop)
                require(not deferred_stops, 'Root stop received before consumer spawn; do not dispatch')
                started = time.monotonic()
                actor = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                         pass_fds=(fd,))  # SAME FLOCK description remains held by exact finite child too.
                try:
                    actor_identity = c.transport().kernel(actor.pid)
                    new(W / 'ROOT-CONSUMER-ACTOR.json', encoded({'at': time.time(), 'identity': actor_identity,
                        'original_run_seconds': 300, 'full_capture_seconds': 180, 'cleanup_reserve_seconds': 5,
                        'no_timer_on_permanent_services': True}))
                finally:
                    # Includes kernel/pin failure after successful Popen. Await
                    # SAME original finite CLI before any outer slot release.
                    code = actor.wait()
                    elapsed = time.monotonic() - started
            finally:
                for number, handler in prior_handlers.items():
                    signal.signal(number, handler)
        canonical = STATE / 'runs' / (a.RUN_ID + '.json')
        ended = {'state': 'ORIGINAL_FULL_CONSUMER_ENDED_RECONCILE_AND_GRADE_SAVED_ONLY',
            'at_moscow': dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),
            'exit_code': code, 'elapsed_seconds': elapsed, 'actor_identity': actor_identity,
            'deferred_parent_stop_requests': deferred_stops,
            'actor_absent': not (Path('/proc') / str(actor.pid)).exists(),
            'canonical_run': ref(canonical) if canonical.exists() else None,
            'shared_slot_released_only_after_consumer_return': True}
        new(W / 'ROOT-DISPATCH-ENDED.json', encoded(ended))
        print(json.dumps(ended, ensure_ascii=False))
    finally:
        os.close(fd)

if __name__ == '__main__':
    main()
