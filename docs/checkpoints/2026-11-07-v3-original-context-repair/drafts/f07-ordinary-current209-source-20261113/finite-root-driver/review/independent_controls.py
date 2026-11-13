"""Independent inert-driver controls; never imports product or executes its path."""
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import types

SOURCE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-FINITE-ROOT-ONCE-SOURCE-20261113/source/root_f07_once.py')
OWN = Path(__file__).absolute().parent
EXPECTED = 'f4798ee4c926b5e008747fd98d52e6d45111cfa380136a0ae79e50f0f65b7230'
raw = SOURCE.read_bytes()
assert len(raw) == 32361 and hashlib.sha256(raw).hexdigest() == EXPECTED
tree = ast.parse(raw)
d = types.ModuleType('_independent_inert_driver')
d.__file__ = str(SOURCE)
exec(compile(raw, str(SOURCE), 'exec'), d.__dict__)
facts = []

def check(name, fact):
    assert fact, name
    facts.append({'control': name, 'result': 'PASS'})

def refuses(fn, code):
    try:
        fn()
    except ValueError as exc:
        return str(exc) == code
    return False

# Import and UNBOUND gates may never consult path/IO/clock effects.
reads = []
original_readref = d.readref
d.readref = lambda *_a, **_k: reads.append('readref')
check('UNBOUND source_inputs refuses before reference/clock/effect',
      refuses(lambda: d.source_inputs({}), 'F07_DRIVER_UNBOUND_NO_EFFECT') and not reads)
d.readref = original_readref
check('empty main argv refuses', refuses(lambda: d.main([]), 'F07_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED'))
check('duplicate JSON keys refuse', refuses(lambda: d.parse('{"x":1,"x":2}'), 'F07_DUPLICATE_JSON_KEY'))

# Exercise only CLI parsing with every effect-bearing callee replaced by inert fakes.
saved = {k: getattr(d, k) for k in ('exact_file', 'validate', 'owned_consumer', 'execute')}
calls = []
d.exact_file = lambda path, sha: ({'fake': path}, {'path': path, 'sha256': sha, 'bytes': 1})
d.validate = lambda value: True
d.owned_consumer = lambda *args: calls.append(args) or 17
argv = ['--owned-consumer', '/fake/binding', 'a'*64, '47', '901', '902', 'boot',
        '--clock', '/fake/clock', 'b'*64, '/fake/cleanup', 'c'*64]
check('owned consumer argv exact12 positions', d.main(argv) == 17 and len(calls) == 1 and
      calls[0][2]['path'] == '/fake/clock' and calls[0][3]['path'] == '/fake/cleanup' and
      calls[0][4] == 47 and calls[0][5] == {'pid': 901, 'start_time': 902, 'boot_id': 'boot'})
calls.clear()
bad = list(argv); bad[7] = '--wrong'
check('owned consumer bad clock marker refuses before call',
      refuses(lambda: d.main(bad), 'F07_OWNED_CHILD_EXACT_ARGUMENTS_REQUIRED') and not calls)
d.execute = lambda *args, **kwargs: calls.append((args, kwargs)) or {'fake': True}
check('execute parser calls exactly once', d.main(['--execute-once', '/fake/binding', 'a'*64]) == 0 and len(calls) == 1)
for k, value in saved.items(): setattr(d, k, value)

defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
def call_lines(fn, attr):
    return sorted(n.lineno for n in ast.walk(defs[fn]) if isinstance(n, ast.Call) and
                  ((isinstance(n.func, ast.Name) and n.func.id == attr) or
                   (isinstance(n.func, ast.Attribute) and n.func.attr == attr)))
execute_text = ast.get_source_segment(raw.decode(), defs['execute'])
check('source/Root decisions precede original clock and birth',
      execute_text.index('source_inputs(v)') < execute_text.index('ROOT-ONCE-DRIVER-INVOCATION.json') <
      execute_text.index('start=time.monotonic()') < execute_text.index('subprocess.Popen('))
owned_text = ast.get_source_segment(raw.decode(), defs['owned_consumer'])
check('consumer three actual lock checks precede proof and runner effects',
      owned_text.index('checker.lock_held(SLOT,parent_identity)') < owned_text.index('with store.lock(') <
      owned_text.index('proof=caller.assemble_root_proof') and
      owned_text.index("checker.lock_held(STATE/'tester-token',me)") < owned_text.index('proof=caller.assemble_root_proof'))
check('privacy decisions and proof freshness precede token/API/new',
      owned_text.index('checker.decisions(proof,observed,proof_ref);checker.fresh(proof)') <
      owned_text.index('api=module.BotAPI(') < owned_text.index('run=runner.new('))
check('one genuine new/send/observe call in source',
      owned_text.count('runner.new(') == owned_text.count('runner.send(') == owned_text.count('runner.observe(') == 1)
check('same proof dual expiry120 and no future grade',
      'expires_at=wall+120' in owned_text and 'expires_monotonic=mono+120' in owned_text and
      'assess_saved_actual' not in owned_text and 'assess_unconfirmed_closure' not in owned_text)

original_resource = d.resource
limits = []
d.resource = types.SimpleNamespace(RLIMIT_CPU=1, RLIMIT_AS=2, RLIMIT_FSIZE=3,
                                   setrlimit=lambda label, value: limits.append((label, value)))
try:
    d.child_limits({'cpu_seconds': 31, 'max_rss_bytes': 32000000, 'disk_bytes': 1000000})
    check('finite CPU AS FSIZE hard/soft values reach child limiter',
          limits == [(1, (31,31)), (2, (32000000,32000000)), (3, (1000000,1000000))])
finally:
    d.resource = original_resource

class FakeTime:
    now = 100.0
    def monotonic(self): return self.now

class Actor:
    def __init__(self, time, exit_on=None, code=None):
        self.time = time; self.exit_on = exit_on; self.code = code; self.sent = []; self.waits = []
    def poll(self): return self.code
    def send_signal(self, sig):
        self.sent.append(int(sig))
        if sig == self.exit_on: self.code = -int(sig)
    def wait(self, timeout):
        self.waits.append(timeout)
        if self.code is not None: return self.code
        self.time.now += timeout
        raise subprocess.TimeoutExpired('fake-only', timeout)

saved_time, saved_scan = d.time, d.scan_scope
try:
    ft = FakeTime(); d.time = ft
    a = Actor(ft, exit_on=signal.SIGTERM); sent = []; life = {}
    code = d.stop_reap(a, {'deadline_monotonic': 105.0}, sent, life)
    check('stop escalation owns single child and original reserve',
          code == -int(signal.SIGTERM) and sent == [int(signal.SIGINT), int(signal.SIGTERM)] and
          sum(a.waits) <= 5.0 and life['cleanup_attempted'] and ft.now <= 105.0)
    ft = FakeTime(); d.time = ft; a = Actor(ft); sent = []; life = {}
    try:
        d.stop_reap(a, {'deadline_monotonic': 105.0}, sent, life)
        unconfirmed = False
    except d.StopUnconfirmed:
        unconfirmed = True
    check('nonreaped child honestly STOP_UNCONFIRMED without new clock',
          unconfirmed and sent == [int(signal.SIGINT), int(signal.SIGTERM), int(signal.SIGKILL)] and
          ft.now == 105.0 and abs(sum(a.waits)-5.0) < 1e-9)
    ft = FakeTime(); d.time = ft; a = Actor(ft, exit_on=signal.SIGINT)
    d.scan_scope = lambda *_a, **_k: {(1, 7): 12}
    result = d.wait_owned(a, {'deadline_monotonic': 700.0}, {'sample_seconds': .5}, {}, 10, [])
    check('observed aggregate bound stops and reaps fake owned child',
          result['stop_reason'] == 'OBSERVED_AGGREGATE_NEW_DISK_BOUND' and
          result['observed_new_bytes_highwater'] == 12 and result['hard_filesystem_quota'] is False and
          a.code is not None)
    ft = FakeTime(); d.time = ft; a = Actor(ft, exit_on=signal.SIGINT)
    d.scan_scope = lambda *_a, **_k: {}
    result = d.wait_owned(a, {'deadline_monotonic': 700.0}, {'sample_seconds': .5}, {}, 10, [int(signal.SIGTERM)])
    check('parent request stops fake child before monitoring loop', result['stop_reason'] == 'PARENT_STOP_REQUEST' and a.code is not None)
    ft = FakeTime(); d.time = ft; a = Actor(ft, code=0)
    d.scan_scope = lambda *_a, **_k: {(3, 8): 4}
    result = d.wait_owned(a, {'deadline_monotonic': 700.0}, {'sample_seconds': .5}, {}, 10, [])
    check('already exited fake child reaped and final carrier sample kept',
          result['exit_code'] == 0 and not a.sent and result['samples'] == 1 and result['observed_new_bytes_highwater'] == 4)
finally:
    d.time, d.scan_scope = saved_time, saved_scan

highwater = {}
check('aggregate growth deduplicates inode and keeps deleted highwater',
      d.charge_growth({(1,1): 10}, {(1,1): 17, (1,2): 4}, highwater) == 11 and
      d.charge_growth({(1,1): 10}, {(1,1): 11}, highwater) == 11)

scratch = OWN/'scratch'
scratch.mkdir(mode=0o700)
try:
    claim = scratch/'once.json'
    reference = d.new(claim, b'{"once":true}\n')
    try:
        d.new(claim, b'OVERWRITE-FORBIDDEN')
        duplicate_refused = False
    except FileExistsError:
        duplicate_refused = True
    check('durable O_EXCL once claim in own scratch only', duplicate_refused and claim.read_bytes() == b'{"once":true}\n' and
          reference['sha256'] == hashlib.sha256(claim.read_bytes()).hexdigest() and (claim.stat().st_mode & 0o777) == 0o600)
finally:
    for path in scratch.iterdir(): path.unlink()
    scratch.rmdir()

report = {'schema': 'frw.independent.inert-driver.controls.v1', 'source': {'path': str(SOURCE), 'bytes': len(raw),
          'sha256': hashlib.sha256(raw).hexdigest()}, 'facts': facts, 'passed': len(facts),
          'effects': {'product_imports': 0, 'product_IO': 0, 'actual_user_clocks': 0, 'actual_Popen': 0,
                      'actual_signals': 0, 'actual_Store': 0, 'user_API': 0},
          'limitations': ['fake wait/signal controls do not prove OS/live timing', 'source sequencing does not admit real inputs']}
out = OWN/'INDEPENDENT-CONTROLS.json'
with out.open('x') as stream: json.dump(report, stream, sort_keys=True, indent=2); stream.write('\n')
os.chmod(out, 0o600)
print(json.dumps({'passed': len(facts), 'report': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}))
