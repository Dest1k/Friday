"""Independent SOURCE controls. No GDB/target/helper/process observation."""
import ast
import builtins
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import types

ROOT=Path('/home/jericho/.cache/FRW-ASTRA-GPGME-OWNC-CALLER-SOURCE-20261115')
OUT=ROOT/'driver-review'
DEPS=Path('/home/jericho/.cache/FRW-ASTRA-CALC-GPGME-M2-REVIEWED-ROOT-20261115/candidate/outer/deps')
checks=[]

def record(name,value=True):
    assert value,name
    checks.append({'name':name,'source_control':'PASS'})

def readref(r):
    p=Path(r['path']);raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==r['sha256'],str(p)
    return raw

def load(path,name,extra=None):
    path=Path(path);ns={'__name__':name,'__file__':str(path),**(extra or {})}
    real_import=builtins.__import__
    def guarded_import(name,*args,**kwargs):
        assert name not in ('gdb','subprocess','ctypes'),'effectful_import:'+name
        return real_import(name,*args,**kwargs)
    ns['__builtins__']=dict(vars(builtins),__import__=guarded_import)
    exec(compile(path.read_bytes(),str(path),'exec'),ns)
    return ns

def rejection(fn,code):
    try:fn()
    except (RuntimeError,ValueError) as exc:
        assert str(exc)==code,(str(exc),code)
    else:raise AssertionError('missing_refusal:'+code)

D=load(ROOT/'driver/ownc_gdb.py','ownc_inert_import')
N=load(ROOT/'inputs/ownc_inputs.py','ownc_metadata_import')
G=load(ROOT/'inputs/generate_inputs.py','ownc_generator_import')
record('three_imports_inert_without_gdb_or_target_execution')
raw=(DEPS/'native_return_observer.py').read_bytes();tree=ast.parse(raw)
defs,final=D['exact_native'](tree)
selected=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in D['NATIVE_NAMES']]
record('selected_native_function_bodies_preserved',ast.dump(defs)==ast.dump(ast.Module(body=selected,type_ignores=[])))
expected=[x.finalbody for x in tree.body if isinstance(x,ast.Try) and len(x.body)==1 and isinstance(x.body[0],ast.Expr) and isinstance(x.body[0].value,ast.Call) and isinstance(x.body[0].value.func,ast.Name) and x.body[0].value.func.id=='main'][0]
record('native_finally_preserved_exactly',ast.dump(final)==ast.dump(ast.Module(body=expected,type_ignores=[])))
record('unknownfork_diagnostic_dependencies_extracted',{'process_boundary_snapshot','boundary_symbol','boundary_proc_identity'}<=D['NATIVE_NAMES'])
short=ast.Module(body=[x for x in tree.body if not(isinstance(x,ast.FunctionDef) and x.name=='boundary_symbol')],type_ignores=[])
rejection(lambda:D['exact_native'](short),'fixture_native_definitions')
record('native_definition_omission_refuses')

# Complete declared startup ENV, with meaningful added/missing/changed/duplicate controls.
D['require']=lambda ok,reason:None if ok else (_ for _ in ()).throw(RuntimeError(reason))
env=dict(N['ENV']);text='\n'.join(k+'='+v for k,v in sorted(env.items()))
assert D['validate_inferior_environment'](text,env)==env
for broken in [text+'\nUNDECLARED=1','\n'.join(text.splitlines()[1:]),text.replace('LANG=C.UTF-8','LANG=other')]:
    rejection(lambda broken=broken:D['validate_inferior_environment'](broken,env),'fixture_complete_startup_environment_mismatch')
rejection(lambda:D['validate_inferior_environment'](text+'\nHOME='+env['HOME'],env),'fixture_inferior_environment_duplicate')
record('full_environment_positive_and_added_missing_changed_duplicate_negatives')
record('only_five_literal_debugger_controls_removed',D['CONTROLS']==('FRW_NATIVE_OBSERVER_CONFIG','FRW_NATIVE_LOAD_DEPENDENCY_REF','FRW_NATIVE_GPGME_ENGINE_INIT_REF','FRW_NATIVE_GPGME_ENGINE_INIT_EVIDENCE','FRW_HELD_FIXTURE_CONFIG'))

# Callback composition exercised without target state or IO. These fakes are
# call-order controls only, never runtime custody or execution evidence.
order=[]
class Custody:
    e={'state':'CLOSED'}
    def metric(self):order.append('paper.metric')
class Paper:
    c=Custody()
    def ensure(self):return self.c
class Engine:
    def paper_closed(self):order.append('gpg.paper_closed')
    def metric_ready(self):order.append('gpg.metric_ready')
class Union:
    paper=Paper();gpgme=Engine()
    def metric_ready(self):order.append('union.metric_ready')
D.update(helper=Union(),STATE={'records':[],'fixture_boundary':'LOAD_OPEN'},load_window=lambda state:order.append(state))
D['paper_done']();assert order==['paper.metric','gpg.paper_closed']
order.clear();D['after_load']();assert order==['paper.metric','gpg.metric_ready','LOAD_CLOSED','union.metric_ready']
record('single_load_window_callback_order_without_reopen_or_clock_reset')
run_ast=next(x for x in ast.parse((ROOT/'driver/ownc_gdb.py').read_bytes()).body if isinstance(x,ast.FunctionDef) and x.name=='run')
assignments=[ast.unparse(x.targets[0]) for x in ast.walk(run_ast) if isinstance(x,ast.Assign) and len(x.targets)==1]
record('catchpoint_assignment_to_both_owners_without_wrapper_shadow','helper.paper.catchpoints' in assignments and 'helper.gpgme.catchpoints' in assignments and 'helper.catchpoints' not in assignments)
record('gpg_drain_routed_to_engine_and_dead_union_cleanup_unused',"helper.gpgme.drain()" in ast.unparse(run_ast) and 'cleanup_inferiors' not in ast.unparse(run_ast))

# Real selected executable bytes are data only. RVA+0x400000 must reconstruct
# exact callable addresses and each direct call's PLT destination.
selected=json.loads((ROOT/'inputs/SELECTED-INPUTS.json').read_bytes())
prep=json.loads(readref({'path':str(N['PREP']/'RESULT.json'),'sha256':'b8cf5f5bd9f5d80ff7e34ef62cdc3995f48a79ce99fd9d9eb2971852d0004e6b'}))
cached=json.loads(readref({'path':str(N['PREP']/'cached-getter/RESULT.json'),'sha256':'9bd2705488024f725892902346064db0b35909d5b1862eec2a9e2bdee520f50f'}))
variant_results=[]
production=(DEPS/'gpgme_engine_bundle.py').read_text()
for variant,v in selected['variants'].items():
    prepared=json.loads(readref(v['prepared_ref']));plan=json.loads(readref(v['plan_ref']))
    historical=cached if variant=='worker_cached' else {'source':prep['source'],'target':prep['variants'][variant]['target']}
    assert prepared['source_ref']=={k:historical['source'][k] for k in ('path','sha256')}
    assert prepared['target_ref']=={k:historical['target'][k] for k in ('path','sha256')}
    elf=N['ELF'](prepared['target_ref']['path']);source=readref(prepared['source_ref'])
    assert elf.ref==prepared['target_ref'] and elf.etype==2 and elf.origin==0x400000
    manifest=json.loads(readref(prepared['manifest_ref']));policy=load(DEPS/'paper_helper_policy.py','paper_policy')
    policy['validate_manifest'](manifest,fixture=True)
    assert manifest==N['paper_manifest'](prepared['source_ref']['path'],prepared['target_ref']['path'])
    for name,rva in prepared['marker_offsets'].items():
        va,size,_=elf.symbols[name]
        assert rva+elf.origin==va
        assert elf.get(va,min(16,size)).hex()==prepared['marker_entry_bytes'][name]
    for name,site in manifest['caller']['sites'].items():
        va=site['offset']+elf.origin
        assert elf.get(va-5,5).hex()==site['before'] and elf.get(va,8).hex()==site['after']
        assert va+struct.unpack('<i',bytes.fromhex(site['before'])[1:])[0]==elf.plt()[name.removesuffix('_return')]
    validator_ref=prepared['gpgme_binding']['validator'];validator_raw=readref(validator_ref).decode()
    old="PAPER_MANIFEST_SHA256 = '92b94f4100609c820f25891e09ec15267802833fb4665c393ff746c4565691d0'"
    new="PAPER_MANIFEST_SHA256 = '"+prepared['manifest_ref']['sha256']+"'"
    assert production.count(old)==1 and validator_raw==production.replace(old,new)
    validator=load(validator_ref['path'],'fixture_validator')
    modules=validator['load_sources'](prepared['gpgme_binding'],readref)
    gm=json.loads(readref(prepared['gpgme_binding']['manifest']))
    validator['validate_manifest'](gm,modules['policy'],modules['collector'])
    assert gm['collector_pins']['environment']==prepared['target_environment']==plan['target_environment']==N['ENV']
    assert set(gm['helpers'])=={'gpg','gpgsm','gpgconf'} and 'g13_version' in modules['policy'].BRANCHES
    assert prepared['runtime_template']['operation_deadline_monotonic'] is None
    assert gm['collector_pins']['operation'] is gm['collector_pins']['original'] is gm['collector_pins']['reaper'] is None
    # Only schema/manifest validation; no future runtime identities or clock.
    wrong=copy.deepcopy(manifest);wrong['kind']='OFFICE_PAPER_LOAD_DEPENDENCY'
    rejection(lambda:policy['validate_manifest'](wrong,fixture=True),'helper_manifest_kind')
    bad=copy.deepcopy(gm);bad['collector_pins']['environment']['GNUPGHOME']='/forbidden'
    rejection(lambda:validator['validate_manifest'](bad,modules['policy'],modules['collector']),'gpgme_environment_isolation_or_override')
    for role,images in gm['collector_pins']['dependencies'].items():
        for image in images:
            readref({'path':image['path'],'sha256':image['sha256']})
            for needed in N['ELF'](image['path']).needed:
                for root in N['ENV']['LD_LIBRARY_PATH'].split(':'):
                    assert not (Path(root)/needed).is_file(),'declared_LD_LIBRARY_PATH_override:'+needed
    variant_results.append({'variant':variant,'target_ref':elf.ref,'origin':elf.origin,'expected_refusal':prepared['expected_refusal']})
record('exact_selected_source_and_target_join_historical_hash_bound_preparation_results')
record('all_four_real_ELF_RVAs_paper_call_sites_entry_bytes_and_manifest_pins')
record('all_four_fixture_validator_copies_exact_single_paper_pin_replacement')
record('real_generated_manifests_accepted_by_exact_policy_collector_and_validator')
record('full_target_environment_join_metadata_manifest_plan_driver')
record('wrong_paper_kind_and_forbidden_environment_controls_refuse')
record('system_helper_dependency_hashes_and_no_actual_LD_LIBRARY_PATH_override')
record('runtime_fields_unbound_and_no_future_outcome_asserted')
assert hashlib.sha256((DEPS/'gpgme_engine_bundle.py').read_bytes()).hexdigest()=='72f0126e4fffcdba7d43f76a92bf2c03555ad86f8738c315cf41f389052efa15'
record('production_office_validator_unchanged')

# Independent review repair: diagnostic publication must never skip cleanup.
wrapper_finally=next(x.finalbody for x in run_ast.body if isinstance(x,ast.Try))
ns={'STATE':{'error':'original_refusal'},'CFG':{'native_observer_ref':{'path':'pure-placeholder'}},'final':ast.parse('cleanup_reached=True')}
def broken_diagnostic():raise OSError('pure_synthetic_diagnostic_failure')
ns['capture_refusal_stop']=broken_diagnostic
exec(compile(ast.fix_missing_locations(ast.Module(body=wrapper_finally,type_ignores=[])),'pure-wrapper-finally','exec'),ns)
record('diagnostic_save_failure_cannot_skip_native_finally_and_first_error_preserved',ns.get('cleanup_reached') is True and ns['STATE']['error']=='original_refusal' and ns['STATE']['ownc_refusal_diagnostic_exception_class']=='OSError')

# Guard-stage observer reads only numeric event ownership and callable names.
class BreakpointEvent:
    def __init__(self,bp):self.breakpoints=[bp]
class BP:
    def __init__(self,number,kind):self.number,self.type=number,kind
class EventGDB:
    BP_CATCHPOINT=99
EventGDB.BreakpointEvent=BreakpointEvent
u=Union();u.gpgme.handlers={1:(None,lambda:None,False)}
u.gpgme.handlers[1]=(None,types.SimpleNamespace(__name__='dirs_entry'),False)
u.gpgme.catchpoints={2:'fork'};u.paper.catchpoints={}
D.update(gdb=EventGDB,helper=u,STATE={})
D['observe_stop_stage'](BreakpointEvent(BP(1,0)));assert D['STATE']['ownc_last_guard_stage']=='dirs_entry'
D['observe_stop_stage'](BreakpointEvent(BP(2,99)));assert D['STATE']['ownc_last_guard_stage']=='boundary:fork'
record('new_diagnostic_stage_reader_routes_exact_handler_and_catchpoint_without_effect')

files=[ROOT/'driver/ownc_gdb.py',ROOT/'inputs/ownc_inputs.py',ROOT/'inputs/generate_inputs.py']
files+=sorted((ROOT/'inputs').rglob('*.json'))+sorted((ROOT/'inputs').glob('*/gpgme_engine_bundle.py'))+sorted((ROOT/'inputs').glob('*/fixture-validator.patch'))
refs=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
report={'schema':'frw.ownc.driver-independent-pure-source-controls.v1','checks':checks,'reviewed_sources_and_inputs':refs,'variants':variant_results,'scope':'STATIC_PURE_INTERFACE_CONTROLS_ONLY_NO_RUNTIME_QUALIFICATION','effects':{'target':False,'GDB':False,'GPG':False,'namespace':False,'network':False,'services':False},'actual_M':None}
path=OUT/'controls.json';path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');path.chmod(0o600)
print(json.dumps({'check_families':len(checks),'report':{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}},sort_keys=True))
