"""Pure SOURCE controls. Only this package's private scratch files are written."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import signal
import subprocess
import time
from unittest.mock import patch

ROOT=Path(__file__).absolute().parents[1]
SOURCE=ROOT/'source/root_f07_once.py'
spec=importlib.util.spec_from_file_location('_finite_f07_source_controls',SOURCE)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def refused(name,call,code):
    try:call()
    except (ValueError,FileExistsError) as exc:
        check(name,code is None or str(exc)==code)
    else:raise AssertionError(name)

# Refusal is before every possible file/source/clock/lock/process operation.
with patch.object(d,'readref',side_effect=AssertionError('source IO before unbound refusal')):
    refused('UNBOUND execute refuses before source IO',lambda:d.execute({},binding_ref={}),
            'F07_DRIVER_UNBOUND_NO_EFFECT')
refused('default command refuses',lambda:d.main([]),'F07_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED')
refused('retry command absent',lambda:d.main(['--retry','x','y']),'F07_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED')
for path in ('relative','/a/../b','//home/a','/a//b','/a/./b','/a\n'):
    refused('canonical path refuses '+repr(path),lambda p=path:d.canonical_path(p),'F07_CANONICAL_ABSOLUTE_PATH_REQUIRED')
refused('duplicate JSON keys refuse',lambda:d.parse(b'{"a":1,"a":2}'),'F07_DUPLICATE_JSON_KEY')

# Atomic collision preserves first invocation and cannot issue a new claim.
scratch=ROOT/'controls/scratch';scratch.mkdir(mode=0o700,exist_ok=True)
claim=scratch/'synthetic-ONCE.json'
if claim.exists():claim.unlink()  # ONLY disposable control fixture, no operation material.
reference=d.new(claim,b'{"synthetic":true}\n')
refused('O_EXCL second claim fails',lambda:d.new(claim,b'replacement'),None)
check('O_EXCL preserves initial bytes',d.readref(reference)==b'{"synthetic":true}\n')
check('new file private',claim.stat().st_mode & 0o777==0o600)
refused('pin change refuses',lambda:d.readref(dict(reference,sha256='f'*64)),'F07_EXACT_PIN_CHANGED')

# Three real OS resource selectors are passed the exact Root-supplied numbers.
resources=dict(cpu_seconds=17,max_rss_bytes=256*1024**2,disk_bytes=32*1024**2)
with patch.object(resource,'setrlimit') as limits:d.child_limits(resources)
check('CPU AS FSIZE all applied exactly',limits.call_args_list==[
    ((resource.RLIMIT_CPU,(17,17)),),((resource.RLIMIT_AS,(256*1024**2,256*1024**2)),),
    ((resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2)),)])

# Per-inode positive growth remains charged after shrink/disappearance; replaced
# inode is conservatively charged in full. This is observed, never a hard quota.
base={(1,10):100};high={}
check('growth increase charged',d.charge_growth(base,{(1,10):150},high)==50)
check('growth shrink does not clear charge',d.charge_growth(base,{(1,10):110},high)==50)
check('growth disappearance does not clear charge',d.charge_growth(base,{},high)==50)
check('replacement charged independently',d.charge_growth(base,{(1,11):80},high)==130)

class FakeClock:
    now=0.0
    def monotonic(self):return self.now
class Actor:
    def __init__(self,clock,exit_on=None):
        self.clock=clock;self.exit_on=exit_on;self.code=None;self.signals=[];self.waits=[]
    def poll(self):return self.code
    def wait(self,timeout):
        self.waits.append(timeout)
        if self.code is not None:return self.code
        self.clock.now+=timeout
        raise subprocess.TimeoutExpired('synthetic',timeout)
    def send_signal(self,sig):
        self.signals.append(sig)
        if sig==self.exit_on:self.code=-int(sig)

clock=FakeClock();actor=Actor(clock,signal.SIGTERM);lifetime={}
with patch.object(d.time,'monotonic',clock.monotonic):
    check('owned cleanup TERM reaches same child',d.stop_reap(actor,{'deadline_monotonic':5},[],lifetime)==-signal.SIGTERM)
check('owned cleanup starts once',lifetime=={'cleanup_attempted':True})
check('cleanup uses INT then TERM only',actor.signals==[signal.SIGINT,signal.SIGTERM])
check('cleanup waits fit original reserve',sum(actor.waits)<=5 and clock.now<=5)
clock=FakeClock();actor=Actor(clock)
with patch.object(d.time,'monotonic',clock.monotonic):
    try:d.stop_reap(actor,{'deadline_monotonic':5},[])
    except d.StopUnconfirmed:check('unreaped child explicitly STOP_UNCONFIRMED',True)
    else:raise AssertionError('missing STOP_UNCONFIRMED')
check('unconfirmed cleanup has exact three signals',actor.signals==[signal.SIGINT,signal.SIGTERM,signal.SIGKILL])
check('unconfirmed cleanup cannot create more time',clock.now==5)

clock=FakeClock();actor=Actor(clock,signal.SIGINT)
scope=dict(sample_seconds=0.25)
with patch.object(d.time,'monotonic',clock.monotonic),patch.object(d,'scan_scope',return_value={(1,1):1001}):
    out=d.wait_owned(actor,{'deadline_monotonic':600},scope,{},1000,[])
check('aggregate growth stops owned consumer',out['stop_reason']=='OBSERVED_AGGREGATE_NEW_DISK_BOUND')
check('aggregate limit never called hard quota',out['hard_filesystem_quota'] is False)
check('no retry after aggregate stop',actor.signals==[signal.SIGINT])

# Independent Root assertions remain unknown. No helper fills semantic booleans.
phase=dict(scenario_sha256='a'*64)
v=dict(run_id='synthetic-only',**{k:None for k in ('driver','source_review','checker','root_caller','selected_tester',
    'saved_phase_preflight','scenario','authority','installation_closure','source_acceptance')})
a=dict(schema='frw.Root.F07.explicit-preop-decisions.v1',status='ROOT_BOUND_ONE_FUTURE_PHASE',operator='Root',
       run_id=v['run_id'],scenario_sha256=phase['scenario_sha256'],Root_authorizes_observed_hash_binding_only=True,
       bindings={k:v[k] for k in v if k!='run_id'},original_phase_decision={},privacy_preflight={},accepted_current_facts={})
refused('absent broad-scope Root assertion refuses',lambda:d.validate_acceptance(v,a,phase),
        'F07_ROOT_ORIGINAL_BROADSCOPE_JUDGMENT_REQUIRED')
a['original_phase_decision']=dict(**{k:True for k in d.ROOT_ASSERTIONS},equivalent_consumed_phase_effects=[],
    projection_limit=d.PROJECTION_LIMIT,current_scope_evidence=[{}])
refused('absent source privacy assertions refuse',lambda:d.validate_acceptance(v,a,phase),'F07_ROOT_SOURCE_PRIVACY_PREFLIGHT_REQUIRED')
a['privacy_preflight']=dict(source_metadata_only_checked=True,raw_user_retention_separately_scoped=True,
    genuine_current_event_observed=False,runtime_logging_verdict='NOT_ESTABLISHED',source_evidence=[{}],
    effective_roots_source_basis=[{}],effective_product_roots=['/synthetic-product'],private_roots=['/synthetic-private'])
refused('aggregate monitor limitation acknowledgment required',lambda:d.validate_acceptance(v,a,phase),
        'F07_OBSERVED_GROWTH_NOT_QUOTA_ACKNOWLEDGMENT_REQUIRED')
a['aggregate_disk_monitor_limitations_accepted']=True
check('explicit pure Root acceptance shape accepted',d.validate_acceptance(v,a,phase))
a['privacy_preflight']['genuine_current_event_observed']=True
refused('future runtime observation prohibited',lambda:d.validate_acceptance(v,a,phase),'F07_ROOT_SOURCE_PRIVACY_PREFLIGHT_REQUIRED')

tree=ast.parse(SOURCE.read_bytes());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
child=ast.unparse(functions['owned_consumer']);parent=ast.unparse(functions['execute'])
check('genuine runner sequence new send observe retained',child.index('runner.new(')<child.index('runner.send(')<child.index('runner.observe('))
check('new and send each exactly once',child.count('runner.new(')==child.count('runner.send(')==1)
check('privacy before token and new',child.index('checker.decisions(')<child.index('module.BotAPI(')<child.index('runner.new('))
check('fresh proof before composition',child.index('assemble_root_proof(')<child.index('compose_consumer('))
check('genuine readonly gate before observation',child.index('qualify_selected_ordinary_readonly(')<child.index('checker.observe('))
check('consumer token named locks both retained','store.lock(create=False)' in child and "store.lock(STATE / 'tester-token', create=False)" in child)
check('shared slot parent owns and passes descriptor','safe_lock(SLOT' in parent and 'pass_fds=(slot_fd,)' in parent)
check('one Popen birth site',parent.count('subprocess.Popen(')==1)
check('no resume retry send command in driver',not any(isinstance(n,ast.Attribute) and n.attr in {'resume_prepared','continue_unknown','advance'} for n in ast.walk(tree)))
check('parent child argv clock flag matches parser',"'--clock', clock_ref['path']" in parent and "args[7] == '--clock'" in ast.unparse(functions['main']))
check('consumer rlimits precede source loading',child.index('child_limits(')<child.index('source_inputs('))
check('proof exact dual 120 bound','expires_at=wall + 120' in child and 'expires_monotonic=mono + 120' in child)
check('original clock exactly600 and no reset',parent.count('deadline_monotonic=start + 600')==1)
check('no arbitrary group kills',not any(isinstance(n,ast.Attribute) and n.attr in {'killpg','system'} for n in ast.walk(tree)))
check('technical failures omit exception text','exception_class=type(exc).__name__' in child and 'str(exc)' not in child)
check('raw closure acceptance remains not established',"acceptance='NOT_ESTABLISHED', semantic='NOT_ESTABLISHED'" in child)

out=dict(schema='frw.F07.finite-driver.source-controls.v1',state='PURE_SOURCE_CONTROLS_ONLY',
    source=dict(path=str(SOURCE),bytes=SOURCE.stat().st_size,sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()),
    checks=checks,count=len(checks),failures=[],actual_H_Store_current_native_API_model_user_clock=False,
    actual_future_Root_effect='NOT_RUN')
(ROOT/'controls/SOURCE-CONTROLS.json').write_bytes(d.encoded(out))
print(json.dumps(dict(state=out['state'],count=len(checks),failures=[])))
