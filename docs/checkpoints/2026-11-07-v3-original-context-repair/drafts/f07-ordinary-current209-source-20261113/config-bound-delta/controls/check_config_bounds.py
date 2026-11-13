"""Finite SOURCE/OFFLINE config-bound controls; all observed inputs are own fixtures.

Execute the genuine config reader, readonly/current collectors, decisions and check.
Unchanged service/native/SQL/effect-shape dependencies are explicit synthetic stands.
Never read actual H configs, import product, construct Store or call socket/API/model.
"""
import ast
import copy
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import sys
import tempfile
import time
import types

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-CURRENT209-PREINTENT-COMPOSITION-20261113')
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2))
signal.alarm(240)
raw=(ROOT/'source/current209.py').read_bytes()
old=(ORIGINAL/'source/current209.py').read_bytes()
assert hashlib.sha256(old).hexdigest()=='d6f981a23493f3234dd46595071b0e0f6bc0efb020aa05ca32604c28daca1491'
m=types.ModuleType('source_only_config_bound');m.__file__=str(ROOT/'source/current209.py')
exec(compile(raw,m.__file__,'exec'),m.__dict__)
rows=[]
def test(name,fn):
    try:fn()
    except BaseException as e:
        rows.append(dict(name=name,state='FAIL',error=type(e).__name__));raise
    else:rows.append(dict(name=name,state='PASS'))
def need(value):assert value
def reject(fn,code):
    try:fn()
    except ValueError as e:assert str(e)==code,(str(e),code)
    else:raise AssertionError('expected refusal '+code)
def function_map(value):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(value).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
oldfunc=function_map(old);newfunc=function_map(raw)
changed=[name for name in oldfunc if oldfunc[name]!=newfunc[name]]
test('only_existing_function_delta_is_shared_current_collector',lambda:need(changed==['_observe_current']))
test('only_added_function_is_scoped_config_refs',lambda:need(set(newfunc)-set(oldfunc)=={'profile_config_refs'}))
oldtree=ast.parse(old);newtree=ast.parse(raw)
oldcollector=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='_observe_current')
oldconfig=next(n.value for n in oldcollector.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='configs' for t in n.targets))
class RestoreConfigExpr(ast.NodeTransformer):
    count=0
    def visit_Call(self,node):
        if isinstance(node.func,ast.Name) and node.func.id=='profile_config_refs':
            assert not node.args and not node.keywords
            self.count+=1;return copy.deepcopy(oldconfig)
        return self.generic_visit(node)
newtree.body=[n for n in newtree.body if not (isinstance(n,ast.FunctionDef) and n.name=='profile_config_refs') and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROFILE_CONFIG_LIMITS' for t in n.targets))]
restore=RestoreConfigExpr();normalized=restore.visit(newtree)
test('whole_module_AST_only_scope_helper_and_two_collection_expressions',lambda:need(restore.count==2 and ast.dump(normalized,include_attributes=False)==ast.dump(oldtree,include_attributes=False)))
for name in ('_read_bounded','read','read_reference','ref','observe_readonly','observe','decisions','check','effect_shape','prepare_effect','compose_preintent_source'):
    test('unchanged_exact_AST_'+name,lambda name=name:need(oldfunc[name]==newfunc[name]))
test('root_caller_bytes_unchanged',lambda:need((ROOT/'source/root_caller.py').read_bytes()==(ORIGINAL/'source/root_caller.py').read_bytes()))
test('fixed_scope_and_explicit_finite_limits',lambda:need(m.PROFILE_CONFIG_LIMITS=={'default':4194304,'dest':1048576,'tester':4194304} and set(m.PROFILE_CONFIG_LIMITS)==set(m.DATABASES) and m.DEFAULT_LIMIT==1048576 and m.EXACT_LIMIT==25165824))

fixture=Path(tempfile.mkdtemp(prefix='synthetic-config-',dir=ROOT/'controls'));fixture.chmod(0o700)
saved={}
def patch(name,value):saved.setdefault(name,getattr(m,name));setattr(m,name,value)
def put(path,value):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    data=value if isinstance(value,bytes) else m.encoded(value)
    path.write_bytes(data);path.chmod(0o600)
    return dict(path=str(path),bytes=len(data),sha256=m.digest(data))
sizes={'default':3382001,'dest':20782,'tester':3176638}
try:
    replacements={'/proc/uptime':fixture/'uptime','/proc/meminfo':fixture/'meminfo'}
    class StandPath(type(Path())):
        def __init__(self,*parts):
            if len(parts)==1 and str(parts[0]) in replacements:parts=(str(replacements[str(parts[0])]),)
            super().__init__(*parts)
    patch('Path',StandPath)
    test('synthetic_proc_reads_route_only_to_owned_inputs',lambda:need(str(m.Path('/proc/uptime'))==str(fixture/'uptime') and str(m.Path('/proc/meminfo'))==str(fixture/'meminfo')))
    H=StandPath(str(fixture/'home'));STATE=StandPath(str(fixture/'state'));private=StandPath(str(fixture/'private'))
    for p in (H,STATE,private):p.mkdir(mode=0o700)
    patch('H',H);patch('STATE',STATE)
    paths={'default':H/'config.yaml','dest':H/'profiles/dest_telegram/config.yaml','tester':H/'profiles/tester/config.yaml'}
    patch('DATABASES',{label:path.parent/'state.db' for label,path in paths.items()})
    def reset_configs():
        for label,path in paths.items():put(path,bytes([65+list(paths).index(label)])*sizes[label])
    reset_configs()
    expected={label:dict(path=str(path),bytes=sizes[label],sha256=m.digest(bytes([65+list(paths).index(label)])*sizes[label])) for label,path in paths.items()}
    test('actual_sized_oversize_synthetic_configs_exact_refs',lambda:need(m.profile_config_refs()==expected))
    for name in ('read','ref'):
        test('default_'+name+'_still_refuses_default_oversize',lambda name=name:reject(lambda:getattr(m,name)(str(paths['default']),private=False),'F07_INPUT_CAS_OR_SIZE_CHANGED'))
    test('strict_exact_sized_reader_accepts_known_large_ref',lambda:need(len(m.read_reference(expected['default'],private=False))==3382001))
    reads=[];bounded=m._read_bounded
    def traced(path,limit,private):reads.append((str(path),limit,private));return bounded(path,limit,private)
    patch('_read_bounded',traced)
    test('fixed_three_read_scope_no_discovery_or_retry',lambda:need(m.profile_config_refs()==expected and reads==[(str(paths[label]),limit,False) for label,limit in m.PROFILE_CONFIG_LIMITS.items()]))
    m._read_bounded=bounded
    for label in paths:
        bound=m.PROFILE_CONFIG_LIMITS[label]
        put(paths[label],b'x'*bound)
        test(label+'_inclusive_exact_bound',lambda label=label,bound=bound:need(m.profile_config_refs()[label]['bytes']==bound))
        put(paths[label],b'x'*(bound+1))
        test(label+'_overbound_refused',lambda:reject(m.profile_config_refs,'F07_INPUT_CAS_OR_SIZE_CHANGED'))
        reset_configs()
    target=paths['tester'];backup=target.read_bytes();target.unlink();target.symlink_to(paths['default'])
    test('config_symlink_refused',lambda:reject(m.profile_config_refs,'F07_NO_SYMLINKS_REQUIRED'))
    target.unlink();put(target,backup)
    original_dbs=m.DATABASES;linked=H/'linked-profile';linked.symlink_to(target.parent,target_is_directory=True)
    m.DATABASES=dict(original_dbs,tester=linked/'state.db')
    test('config_parent_symlink_refused',lambda:reject(m.profile_config_refs,'F07_NO_SYMLINKS_REQUIRED'))
    m.DATABASES=original_dbs;linked.unlink()
    link=fixture/'hardlinked';os.link(target,link)
    test('config_hardlink_refused',lambda:reject(m.profile_config_refs,'F07_UNSAFE_INPUT'))
    link.unlink()
    target.chmod(0o602)
    test('config_world_writable_refused',lambda:reject(m.profile_config_refs,'F07_UNSAFE_INPUT'))
    target.chmod(0o600)
    getuid=os.getuid;uid=getuid()
    try:
        os.getuid=lambda:uid+1
        test('config_owner_mismatch_refused_real_stat',lambda:reject(m.profile_config_refs,'F07_UNSAFE_INPUT'))
    finally:os.getuid=getuid
    fstat=os.fstat;calls=[0]
    def mutate_fstat(fd):
        value=fstat(fd);calls[0]+=1
        if calls[0]==1:put(paths['default'],b'z'*sizes['default'])
        return value
    try:
        os.fstat=mutate_fstat
        test('same_size_mutation_during_read_refused',lambda:reject(m.profile_config_refs,'F07_INPUT_CAS_OR_SIZE_CHANGED'))
    finally:os.fstat=fstat;reset_configs()
    configs=m.profile_config_refs();put(paths['default'],b'z'*sizes['default'])
    test('same_size_mutation_after_snapshot_exact_ref_refused',lambda:reject(lambda:m.read_reference(configs['default'],private=False),'F07_EXACT_REFERENCE_CHANGED'))
    reset_configs()

    # Execute the unmodified public readonly/current/check functions and full
    # actual _observe_current body; only unrelated unchanged dependencies stand.
    put(fixture/'uptime',b'0 0\n');put(fixture/'meminfo',b'MemAvailable: 10000000 kB\n')
    put(H/'hermes-agent/synthetic.py',b'# own synthetic current fixture\n')
    patch('RELEVANT',('synthetic.py',))
    ident=dict(pid=os.getpid(),start_time=100000,boot_id='SYNTHETIC_BOOT')
    gateway=dict(gateway_state='running',active_agents=0,active_work=None,restart_requested=False,session_store=dict(status='ok'),served_profiles=['default','dest_telegram','telegram-bot-8812646969'],hermes_home=str(H),argv=[str(H/'hermes-agent/hermes_cli/main.py'),'gateway','run'],pid=ident['pid'],start_time=ident['start_time'],platforms=dict(telegram=dict(state='connected',needs_attention=False,writer_pid=ident['pid'],writer_start_time=ident['start_time'])))
    put(H/'gateway_state.json',gateway);put(STATE/'cursor.json',dict(offset=123))
    source_ref=put(private/'input.txt',b'own synthetic prospective source\n');s=Path(source_ref['path']).stat()
    source=dict(path=source_ref['path'],sha256=source_ref['sha256'],stat=dict(device=s.st_dev,inode=s.st_ino,size_bytes=s.st_size,uid=s.st_uid,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns))
    phase=dict(ordinal=1,phase='SYNTHETIC_PHASE',scenario=dict(steps=[dict(input=source)]),scenario_sha256='1'*64,expected_semantics='SYNTHETIC_NOT_PRODUCT')
    native=dict(identity=ident,quiescent=True,global_work=dict(global_active_session_keys=[]))
    prep=types.SimpleNamespace(phase_preparation=lambda ordinal,input:copy.deepcopy(phase))
    transport=types.SimpleNamespace(fresh_native=lambda state:copy.deepcopy(native))
    patch('module',lambda ref:prep if ref==m.PREP else transport)
    installed=dict(environment_basis=dict(synthetic=True),runtime_hashes={})
    service_rows=dict(gateway=dict(identity=ident));env=dict(synthetic=True)
    patch('installation',lambda effect:copy.deepcopy(installed))
    patch('services',lambda basis:(copy.deepcopy(service_rows),copy.deepcopy(env)))
    patch('kernel',lambda pid:copy.deepcopy(ident))
    patch('databases',lambda:dict(synthetic='SQL_NOT_EXECUTED'))
    patch('history',lambda effect,stage:dict(sha256='2'*64,synthetic=True))
    patch('custody',lambda:dict(sha256='3'*64,synthetic=True))
    patch('technical_log_cursor',lambda:dict(synthetic=True,contents_read=False))
    resources=dict(m.TIMING,cpu_seconds=120,max_rss_bytes=512*1024**2,disk_bytes=100*1024**2)
    for k in ('clock','owned_parent_wait_cleanup'):resources[k]=put(private/(k+'.json'),dict(synthetic=True))
    effect=dict(schema='frw.Root.F07.current209-effect.v1',run_id='SOURCE-STAND-ONLY',phase=phase,resources=resources)
    for k in ('authority','scenario','checker','source_preparation','installation_closure','source_acceptance'):effect[k]=put(private/(k+'.json'),dict(synthetic=True))
    closure=dict(m.CLOSURE,bytes=1);acceptance=dict(m.ACCEPTANCE,bytes=1)
    limits={k:resources[k] for k in ('max_rss_bytes','disk_bytes')}
    observed=m.observe_readonly(phase=phase,run_id=effect['run_id'],closure_ref=closure,acceptance_ref=acceptance,resource_limits=limits)
    test('genuine_observe_readonly_oversized_configs_no_operation_clock',lambda:need(observed['operation_clock_created'] is False and observed['authority_issued'] is False and observed['observed']['profile_configs']==expected))
    clock=dict(deadline_monotonic=time.monotonic()+600)
    patch('effect_shape',lambda value:({},clock))
    actual=m.observe(effect)
    test('genuine_observe_same_exact_config_refs',lambda:need(actual['profile_configs']==observed['observed']['profile_configs']))
    log_cursor=m.technical_log_cursor;first=[True]
    def mutate_between_config_snapshots():
        if first[0]:first[0]=False;put(paths['default'],b'z'*sizes['default'])
        return log_cursor()
    m.technical_log_cursor=mutate_between_config_snapshots
    test('genuine_collector_final_same_size_config_CAS_refused',lambda:reject(lambda:m.observe(effect),'F07_FINAL_SQL_HISTORY_ONCE_CURSOR_CONFIG_OR_LOG_CAS_CHANGED'))
    m.technical_log_cursor=log_cursor;reset_configs();actual=m.observe(effect)

    evidence=put(private/'source-evidence.json',dict(synthetic=True));proof_ref=dict(path=str(private/'proof.json'),bytes=1,sha256='a'*64)
    def make_proof(observed):
        whole=m.digest(m.encoded(effect));now=time.time();mono=time.monotonic()
        review=dict(schema='frw.Root.F07.current209-original-case-decision.v1',operator='Root',status='ROOT_BOUND',whole_effect_sha256=whole,history_sha256=observed['history']['sha256'],custody_sha256=observed['custody']['sha256'],native_SQL_boundary_sha256=m.digest(m.encoded(dict(native=observed['native'],databases=observed['databases']))),original_phase_effect_eligible=True,old_effects_UNKNOWN_clocks_preserved=True,all_profile_semantic_unlogged_equivalents_reconciled=True,equivalent_consumed_phase_effects=[],projection_limit=m.PROJECTION_LIMIT,root_current_pending_approval_cancel_maintenance_assessed=True,current_scope_evidence=[evidence])
        privacy=dict(schema='frw.Root.F07.current209-privacy-preflight.v1',operator='Root',status='ROOT_BOUND_PREFLIGHT_NOT_RUNTIME_VERDICT',whole_effect_sha256=whole,runtime_hashes=observed['installed']['runtime_hashes'],logging_sites=list(m.LOGGING_SITES),technical_log_cursor=observed['technical_log_cursor'],postcondition_plan=m.postcondition_plan(effect,observed),source_metadata_only_checked=True,genuine_current_event_observed=False,runtime_logging_verdict='NOT_ESTABLISHED',raw_user_retention_separately_scoped=True,source_evidence=[evidence],effective_product_roots=[str(H)],private_roots=[str(private)],effective_roots_profile_config_refs=observed['profile_configs'],effective_roots_source_basis=[evidence])
        invocation=dict(schema='frw.Root.F07.one-ordinary-consumer-invocation.v1',run_id=effect['run_id'],whole_effect_sha256=whole,clock=effect['resources']['clock'],no_retry=True,consumer=ident)
        return dict(schema='frw.Root.F07.current209-preintent.v1',status='ROOT_BOUND',operator='Root',effect=effect,whole_effect_sha256=whole,created_at=now-1,expires_at=now+90,created_monotonic=mono-1,expires_monotonic=mono+90,boot_id=ident['boot_id'],observed=observed,lock_owners={k:ident for k in ('shared_slot','consumer','credential')},invocation=put(private/'invocation.json',invocation),Root_decision=put(private/'decision.json',review),privacy_preflight=put(private/'privacy.json',privacy))
    patch('process_bytes',lambda pid,name:b'SYNTHETIC_PROCESS_NO_PRIVATE_MARKERS')
    proof=make_proof(actual)
    test('genuine_decisions_privacy_rereads_all_exact_oversize_config_refs',lambda:m.decisions(proof,actual,proof_ref))
    patch('read_kernel_boot',lambda:ident['boot_id']);patch('lock_held',lambda path,owner:None)
    # process_bytes stand is needed by decisions; call the complete strict checker.
    proof_ref=put(private/'proof.json',proof)
    for stage in ('NEW','CURSOR_AUTHORITY','PRE_INTENT_REVALIDATION'):
        result=m.check(proof_ref,run_id=effect['run_id'],scenario=phase['scenario'],stage=stage)
        test('genuine_strict_check_'+stage+'_same_config_ABI',lambda result=result,stage=stage:need(result['admission'] is False and result['stage']==stage))
    put(paths['default'],b'z'*sizes['default'])
    test('genuine_strict_check_changed_snapshot_refused',lambda:reject(lambda:m.check(proof_ref,run_id=effect['run_id'],scenario=phase['scenario'],stage='NEW'),'F07_MUTABLE_CURRENT_FACTS_CHANGED'))
    reset_configs()
    marker=str(private).encode();put(paths['default'],marker+b'A'*(sizes['default']-len(marker)))
    marked=m.observe(effect);marked_proof=make_proof(marked)
    test('genuine_privacy_marker_in_oversize_config_refused',lambda:reject(lambda:m.decisions(marked_proof,marked,proof_ref),'F07_PRIVATE_ROOT_IN_PRODUCT_CONFIG'))
    reset_configs()
finally:
    for name,value in saved.items():setattr(m,name,value)
    shutil.rmtree(fixture)

out=dict(schema='frw.F07.config-bound-source-controls.v1',state='PASS',source=dict(path=str(ROOT/'source/current209.py'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),checks=len(rows),passed=sum(r['state']=='PASS' for r in rows),rows=rows,invariant_controls_reused=dict(own=114,independent=33,basis=str(ORIGINAL/'RESULT.json'),reason='Exact AST/bytes unchanged except scoped helper/constants and two collection expressions; unchanged dependencies explicitly stood in focused nearest-consumer execution.'),scope='SOURCE/OFFLINE synthetic fixtures only',actual_config_contents_read=False,actual_collector_calls=0,actual_Store_API_native_model_user_operations=0,Root_actual_readonly='NOT_RUN')
output=ROOT/'controls/CONFIG-BOUND-CONTROLS.json';output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');output.chmod(0o600)
print(json.dumps(dict(state=out['state'],checks=out['checks'],passed=out['passed'],output=str(output)),sort_keys=True))
