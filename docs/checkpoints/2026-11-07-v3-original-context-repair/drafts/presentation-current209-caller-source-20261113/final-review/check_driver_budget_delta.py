"""Finite pure driver-delta controls; no Root input, Store or current calls."""
from pathlib import Path
import ast, contextlib, hashlib, io, json, os, resource, signal, time, types
os.umask(0o077)
for k,v in ((resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,100*1024**2)):
    resource.setrlimit(k,(v,v))
OUT=Path(__file__).parent;SOURCE=OUT.parent/'root_presentation_once.py'
raw=SOURCE.read_bytes();START=time.monotonic();checks=[]
assert hashlib.sha256(raw).hexdigest()=='d46105322d90f3150aad274a0861e94f2ef45bfba89c7921df3dc3826dbf57f0'
def record(name,condition):
    assert condition,name
    checks.append(dict(name=name,status='PASS'))
def load():
    d=types.ModuleType('_independent_driver_budget_delta');d.__file__=str(SOURCE)
    exec(compile(raw,str(SOURCE),'exec'),d.__dict__);return d
def enc(v): return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
old_main='''def main(argv=None):
    args=sys.argv[1:] if argv is None else argv;os.umask(0o077)
    need(len(args) in (3,12) and args[0] in ('--readonly-before-clock','--execute-once','--owned-consumer'),
         'PRESENTATION_EXPLICIT_ROOT_BOUND_COMMAND_REQUIRED')
    H=read_shared();v,ref=H.exact_file(args[1],args[2]);validate(v,H)
    if len(args)==3 and args[0]=='--readonly-before-clock':
        print(json.dumps(readonly(v,H),sort_keys=True));return 0
    if len(args)==3 and args[0]=='--execute-once':
        print(json.dumps(execute(v,H,binding_ref=ref),sort_keys=True));return 0
    if len(args)==12 and args[0]=='--owned-consumer' and args[7]=='--clock':
        clock,clock_ref=H.exact_file(args[8],args[9]);cleanup,cleanup_ref=H.exact_file(args[10],args[11])
        return owned_consumer(v,H,ref,clock_ref,cleanup_ref,int(args[3]),
            dict(pid=int(args[4]),start_time=int(args[5]),boot_id=args[6]))
    raise ValueError('PRESENTATION_EXACT_SINGLE_OPERATION_COMMAND_REQUIRED')'''
s=raw.decode();tree=ast.parse(s);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
lines=s.splitlines(keepends=True);lines[main.lineno-1:main.end_lineno]=[old_main+'\n']
prior=''.join(lines).replace('PREPARATION_WALL_SECONDS=300\n','').replace(
    '        # End the separate bounded no-effect preparation interval before any\n'
    '        # once claim or original operation clock. It never extends outer600.\n'
    '        signal.setitimer(signal.ITIMER_REAL,0)\n','').encode()
record('exact_prior_driver_reconstruction_only_budget_delta',sha(prior)=='812419809d33d12627dae7d23710ea9cd464109e417d78ca7a273ff574ce64a2')
old_functions={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(prior).body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
record('only_main_and_execute_changed',set(old_functions)==set(new_functions) and [n for n in old_functions if old_functions[n]!=new_functions[n]]==['execute','main'])

class FakeHelper:
    def __init__(self,events):self.events=events
    def exact_file(self,*args):self.events.append('protected_binding_read');return {'resources':{'SYNTHETIC':True}},{'SYNTHETIC_REF':True}
    def child_limits(self,resources):assert resources=={'SYNTHETIC':True};self.events.append('finite_limits')
def harness():
    d=load();events=[];helper=FakeHelper(events)
    d.read_shared=lambda:helper;d.validate=lambda *_:events.append('shape_validate')
    return d,events
old_handler=signal.getsignal(signal.SIGALRM)
record('own_real_signal_timer_initially_unset',signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0))
d,events=harness()
d.readonly=lambda *_:events.append('readonly') or {'SYNTHETIC':True}
with contextlib.redirect_stdout(io.StringIO()):result=d.main(['--readonly-before-clock','SYNTHETIC-NO-FILE','0'*64])
record('readonly_main_limits_precede_actual_qualifier_dispatch',result==0 and events==['protected_binding_read','shape_validate','finite_limits','readonly'])
record('readonly_success_disarms_real_timer_and_restores_handler',signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0) and signal.getsignal(signal.SIGALRM)==old_handler)

d,events=harness();d.PREPARATION_WALL_SECONDS=0.02
def bounded_readonly(*_):events.append('readonly_waiting_own_SIGALRM');signal.pause()
d.readonly=bounded_readonly
before=time.monotonic()
try:
    with contextlib.redirect_stdout(io.StringIO()):d.main(['--readonly-before-clock','SYNTHETIC-NO-FILE','0'*64])
except TimeoutError as exc:
    expired=str(exc)=='PRESENTATION_PRECLAIM_PREPARATION_WALL_EXPIRED'
else:expired=False
record('real_SIGALRM_preclaim_timeout_raises_without_effect',expired and time.monotonic()-before<2 and events[-1]=='readonly_waiting_own_SIGALRM')
record('readonly_timeout_disarms_real_timer_and_restores_handler',signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0) and signal.getsignal(signal.SIGALRM)==old_handler)

d,events=harness()
timer_events=[]
class NoTimerSignal:
    SIGALRM=signal.SIGALRM;ITIMER_REAL=signal.ITIMER_REAL
    def signal(self,*args):timer_events.append(('signal',args));return old_handler
    def setitimer(self,*args):timer_events.append(('timer',args));return (0.0,0.0)
d.signal=NoTimerSignal();d.owned_consumer=lambda *_:events.append('owned_consumer') or 17
result=d.main(['--owned-consumer','SYNTHETIC-NO-FILE','0'*64,'9','10','11','SYNTHETIC-BOOT','--clock','SYNTHETIC-CLOCK','1'*64,'SYNTHETIC-CLEANUP','2'*64])
record('owned_consumer_main_no_independent_timer_or_outer_reset',result==17 and timer_events==[] and events.index('finite_limits')<events.index('owned_consumer'))

d=load();events=[]
class VirtualPath:
    def __init__(self,text):self.text=text
    def iterdir(self):events.append('empty_workdir');return []
    def __truediv__(self,name):return VirtualPath(self.text+'/'+name)
class ReachedClaim(Exception):pass
class SignalFacade:
    SIGINT=signal.SIGINT;SIGTERM=signal.SIGTERM;ITIMER_REAL=signal.ITIMER_REAL
    def getsignal(self,*_):return 'SYNTHETIC-OLD-HANDLER'
    def signal(self,*_):events.append('signal_handler')
    def setitimer(self,which,value):assert value==0;events.append('disarm_preclaim_timer')
class Helper:
    class StopUnconfirmed(Exception):pass
    def safe_lock(self,*_):events.append('shared_slot');return 999999
    def scan_scope(self,*_,**__):events.append('bounded_disk_baseline');return {}
    def kernel(self,*_):return dict(pid=1,start_time=1,boot_id='SYNTHETIC')
    def new(self,*_):events.append('first_once_claim');raise ReachedClaim()
d.Path=VirtualPath;d.signal=SignalFacade();d.os=types.SimpleNamespace(getpid=lambda:1,close=lambda _:events.append('slot_closed'))
d.source_inputs=lambda *_:(None,None,None,{},None,None,None)
d.qualify_before_clock=lambda *_:events.append('whole_readonly_preclock') or {}
v=dict(workdir='SYNTHETIC-VIRTUAL-NOT-FILESYSTEM',slot_identity={},disk_scope={},run_id='SYNTHETIC',resources={})
try:d.execute(v,Helper(),binding_ref={})
except ReachedClaim:pass
record('exact_execute_disarms_only_after_full_qualifier_and_disk_before_claim',events.index('whole_readonly_preclock')<events.index('bounded_disk_baseline')<events.index('disarm_preclaim_timer')<events.index('first_once_claim'))
record('controlled_preclaim_stop_releases_only_virtual_slot',events[-1]=='slot_closed')
record('final_driver_source_still_same',SOURCE.read_bytes()==raw)
result=dict(schema='frw.SOL.Task38.independent-driver-budget-delta.v1',scope='SOURCE_ONLY_SYNTHETIC_REAL_OWN_SIGNAL_NO_ROOT_CALL',
 source={'path':str(SOURCE),'bytes':len(raw),'sha256':sha(raw)},prior_driver_sha256=sha(prior),checks=checks,
 count=len(checks),elapsed_seconds=time.monotonic()-START,limits=dict(cpu_seconds=120,address_space_bytes=512*1024**2,disk_bytes=100*1024**2,wall_seconds=300),
 real_own_process_SIGALRM_used=True,actual_Root_Store_API_current_DB_H_Telegram_Office_product_model_send_install_service_effects=0)
(OUT/'DRIVER-BUDGET-DELTA-CHECKS.json').write_bytes(enc(result));os.chmod(OUT/'DRIVER-BUDGET-DELTA-CHECKS.json',0o600)
print(json.dumps({'checks':len(checks),'elapsed_seconds':result['elapsed_seconds']}))
