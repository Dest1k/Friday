"""Pure producer qualification. Never execute the generated fullv42 consumer."""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import sys
import time
import types

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'producer-controls'
BASE=Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py')
INPUTS={BASE}|{ROOT/group/branch/'f06_source.py' for group in ('before','candidate') for branch in ('first','correct')}
READS=[]
DENIED=[]
START=time.time()
MONO=time.monotonic()
def audit(event,args):
    if event=='open':
        raw,mode,flags=args
        if isinstance(raw,int):raise PermissionError('CONTROL_FD_OPEN_DENIED')
        path=Path(os.path.abspath(os.fspath(raw)))
        write=bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if (write and path.parent!=OUT) or (not write and path not in INPUTS and path.parent!=OUT):
            DENIED.append(event);raise PermissionError('CONTROL_UNDECLARED_OPEN_DENIED')
        if not write:READS.append(str(path))
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.exec','os.posix_spawn','os.fork','pty.spawn'):
        DENIED.append(event);raise PermissionError('CONTROL_EXTERNAL_EFFECT_DENIED')
sys.addaudithook(audit)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def write(name,raw):
    path=OUT/name
    with path.open('xb') as stream:stream.write(raw)
    return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
def load(path,name):
    module=types.ModuleType(name);module.__file__=str(path)
    raw=path.read_bytes();exec(compile(raw,str(path),'exec'),module.__dict__)
    return module,raw
def fingerprint(v):
    t=type(v)
    if v is None:return ('null',)
    if t is bool:return ('bool',v)
    if t is int:return ('int',str(v))
    if t is float:return ('float',v.hex())
    if t is str:return ('str',v)
    if t is list:return ('list',tuple(fingerprint(x) for x in v))
    if t is dict:return ('dict',tuple((k,fingerprint(v[k])) for k in sorted(v)))
    raise AssertionError('unexpected fixture type')
def ref(label,raw=b'synthetic-data'):
    return {'path':'/synthetic/путь/'+label+'.json','bytes':len(raw),'sha256':sha(raw)}
FOOTER=b'F06_CONTRACT=__CONTRACT__\n'
def fixture(a,branch):
    c=a.unbound()
    c.update(status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD' if branch=='first' else 'ROOT_BOUND_EXACT_F06_CORRECTREAD',run_id='synthetic-f06-'+branch,scenario_sha256=sha(b'synthetic-scenario'),authority_id='synthetic-r106')
    for key in ('scenario_ref','authority','adapter','footer','actual_root_B_checker','root_current_proof'):
        c[key]=ref(key,FOOTER if key=='footer' else b'synthetic-data')
    c['root_proofs']={key:ref(key) for key in sorted(a.PROOFS)}
    c['product']={'source_layers':207,'project_files':495,'native_files':17891,'plugin_files':52,'base_source_files':17730,'source_receipt_sha256':sha(b'synthetic-source'),'input_sha256':sha(b'synthetic-input')}
    c['boundary']={key:sha(key.encode()) for key in a.BOUNDARY-{'gateway','B','phase_unconsumed','uploads_this_operation','producer_calls','restarts'}}
    c['boundary'].update(gateway={'pid':4242,'start_time':123.0,'diagnostics':{'é':'e\u0301\x00\n\t\u007f','\ue000':'private-use','\U00010000':'astral','number_types':[False,True,0,1,1.0,-0.0,0.0,None,2**100,[{'z':-1.25,'a':'中文/🙂'}]]}},B={'profile':'telegram-bot-8812646969','session_id':'synthetic-session','session_key':'synthetic-key','native_max_id':0},phase_unconsumed=True,uploads_this_operation=1 if branch=='first' else 0,producer_calls=0,restarts=0)
    c['resources']=dict(a.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=64*1024**2,clock=ref('clock'),owned_parent_wait_cleanup=ref('cleanup'))
    if branch=='first':
        c['authority_chain']={'predecessor':ref('predecessor'),'predecessor_authority_id':'synthetic-r105','created_at':10.0,'expires_at':100.0}
    else:
        c.update(first_validator=ref('first_validator'),first_ingress=ref('first_ingress'),source_reference={'run_id':'synthetic-first','run_sha256':sha(b'synthetic-first'),'input_sha256':a.SOURCE['sha256']},installation={'closure':ref('closure'),'source_acceptance':ref('source_acceptance'),'product':dict(c['product']),'runtime_hashes':{'synthetic':sha(b'synthetic-runtime')}})
    a.contract_shape(c)
    return c
def contract_node(raw):
    tree=ast.parse(raw)
    found=[node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='F06_CONTRACT' for x in node.targets)]
    assert len(found)==1
    return tree,found[0]
def inspect_source(raw,c):
    tree,node=contract_node(raw)
    assert fingerprint(ast.literal_eval(node.value))==fingerprint(c)
    runner=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Runner')
    values={target.id:ast.literal_eval(node.value) for node in runner.body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name) and target.id in ('ORDINARY_INDEPENDENT_AUTHORITY','ORDINARY_INDEPENDENT_SCENARIOS')}
    assert fingerprint(values['ORDINARY_INDEPENDENT_AUTHORITY'])==fingerprint(c['authority'])
    assert values['ORDINARY_INDEPENDENT_SCENARIOS']=={c['run_id']:c['scenario_sha256']}
    method=next(node for node in runner.body if isinstance(node,ast.FunctionDef) and node.name=='ordinary_independent_admission')
    assert sum(isinstance(node,ast.Constant) and node.value==c['authority_id'] for node in ast.walk(method))==1
    return tree,node
def without_contract(raw):
    tree,node=contract_node(raw);node.value=ast.Constant(value=None)
    return ast.dump(tree,include_attributes=False)
def reorder(value,mode,depth=0):
    if type(value) is dict:
        keys=list(value)
        if mode=='top' and depth==0 or mode=='nested' and depth>0 or mode=='all':keys.reverse()
        if mode=='rotate' and keys:keys=keys[1:]+keys[:1]
        return {key:reorder(value[key],mode,depth+1) for key in keys}
    if type(value) is list:return [reorder(item,mode,depth+1) for item in value]
    return value
def dict_count(v):
    if type(v) is dict:return 1+sum(dict_count(x) for x in v.values())
    if type(v) is list:return sum(dict_count(x) for x in v)
    return 0
CHECKS=[]
def check(name,fn):
    start=time.monotonic()
    try:
        data=fn();CHECKS.append({'name':name,'status':'PASS','wall_seconds':time.monotonic()-start,'details':data})
    except BaseException as exc:
        CHECKS.append({'name':name,'status':'FAIL','wall_seconds':time.monotonic()-start,'exception_class':type(exc).__name__,'exception':str(exc)[:512]})
def expect_value_error(fn):
    try:fn()
    except ValueError as exc:return str(exc)
    raise AssertionError('invalid data accepted')

base_raw=BASE.read_bytes()
assert sha(base_raw)=='f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3'
PINS={str(BASE):sha(base_raw)}
for branch in ('first','correct'):
    old,old_raw=load(ROOT/'before'/branch/'f06_source.py','_old_'+branch)
    fixed,fixed_raw=load(ROOT/'candidate'/branch/'f06_source.py','_fixed_'+branch)
    for group,raw in (('before',old_raw),('candidate',fixed_raw)):PINS[str(ROOT/group/branch/'f06_source.py')]=sha(raw)
    c=fixture(fixed,branch)
    # The real defect is mutation AFTER the caller initially normalizes JSON.
    c=json.loads(encoded(c));assert list(c['root_current_proof'])==['bytes','path','sha256']
    c['root_current_proof']=ref('fresh-root-proof',b'synthetic-fresh-proof')
    assert list(c['root_current_proof'])==['path','bytes','sha256']
    binding=write(branch+'-binding.json',encoded(c))
    readback=json.loads((OUT/(branch+'-binding.json')).read_bytes())
    def old_reproduction():
        initial=old.successor(base_raw,c,FOOTER);reconstructed=old.successor(base_raw,readback,FOOTER)
        assert initial!=reconstructed
        assert fingerprint(c)==fingerprint(readback)
        assert without_contract(initial)==without_contract(reconstructed)
        inspect_source(initial,c);inspect_source(reconstructed,readback)
        return {'expected_old_reconstruction':'REFUSED_BYTE_MISMATCH','only_difference':'F06_CONTRACT dict order after fresh proof mutation','initial':write(branch+'-old-source.py',initial),'reconstructed':write(branch+'-old-reconstructed.py',reconstructed),'binding':binding}
    check(branch+'/old-fresh-proof-mismatch',old_reproduction)
    canonical=fixed.canonical_contract(c)
    before_repr=repr(c)
    def helper_integrity():
        assert fingerprint(canonical)==fingerprint(c)
        assert repr(c)==before_repr
        assert repr(canonical)==repr(fixed.canonical_contract(readback))
        assert repr(canonical)==repr(fixed.canonical_contract(canonical))
        assert canonical is not c and canonical['boundary'] is not c['boundary']
        n=canonical['boundary']['gateway']['diagnostics']['number_types']
        assert [type(x) for x in n[:8]]==[bool,bool,int,int,float,float,float,type(None)]
        assert math.copysign(1,n[5])==-1 and math.copysign(1,n[6])==1
        return {'all_dictionary_nodes':dict_count(c),'typed_fingerprint_equal':True,'signed_zero_retained':True,'input_unmodified':True}
    check(branch+'/whole-contract-helper',helper_integrity)
    def scalar_roundtrip():
        values=[None,False,True,0,1,-1,1.0,0.0,-0.0,5e-324,1.7976931348623157e308,-2.2250738585072014e-308,'é e\u0301 中文/🙂 \x00\n\t\u007f',[],{}]
        for value in values:
            normalized=fixed.canonical_contract(value)
            assert fingerprint(normalized)==fingerprint(value)
            assert fingerprint(json.loads(encoded(normalized)))==fingerprint(value)
        return {'scalar_and_container_cases':len(values),'utf8_controls_and_float_extremes_retained':True}
    check(branch+'/scalar-json-roundtrip',scalar_roundtrip)
    stable=fixed.successor(base_raw,c,FOOTER)
    def fresh_fixed():
        again=fixed.successor(base_raw,readback,FOOTER)
        assert stable==again
        inspect_source(stable,c)
        return {'source':write(branch+'-fixed-source.py',stable),'reconstructed_sha256':sha(again),'exact_byte_equality':True,'authority_scenario_id_joins':True,'executed_generated_source':False}
    check(branch+'/fixed-fresh-proof-readback',fresh_fixed)
    for mode in ('top','nested','all','rotate'):
        def ordered_control(mode=mode):
            variant=reorder(c,mode)
            assert fingerprint(variant)==fingerprint(c)
            assert stable==fixed.successor(base_raw,variant,FOOTER)
            assert stable==fixed.successor(base_raw,json.loads(encoded(variant)),FOOTER)
            return {'mode':mode,'dictionary_nodes':dict_count(c),'exact_byte_equality':True}
        check(branch+'/ordering-'+mode,ordered_control)
    class Custom:pass
    class IntSubclass(int):pass
    class FloatSubclass(float):pass
    class StrSubclass(str):pass
    class DictSubclass(dict):pass
    class ListSubclass(list):pass
    cyclic_list=[];cyclic_list.append(cyclic_list)
    cyclic_dict={};cyclic_dict['self']=cyclic_dict
    mixed_cycle={'next':[]};mixed_cycle['next'].append(mixed_cycle)
    invalid={'tuple':(1,2),'set':{1},'frozenset':frozenset((1,)),'bytes':b'x','bytearray':bytearray(b'x'),'path':Path('/synthetic/path'),'custom':Custom(),'complex':1j,'range':range(2),'int-subclass':IntSubclass(1),'float-subclass':FloatSubclass(1),'str-subclass':StrSubclass('x'),'dict-subclass':DictSubclass(a=1),'list-subclass':ListSubclass((1,)),'int-key':{1:'a'},'bool-key':{False:'a'},'none-key':{None:'a'},'float-key':{1.5:'a'},'str-subclass-key':{StrSubclass('x'):1},'mixed-key':{'x':1,2:3},'nan':float('nan'),'positive-infinity':float('inf'),'negative-infinity':float('-inf'),'cyclic-list':cyclic_list,'cyclic-dict':cyclic_dict,'mixed-cycle':mixed_cycle}
    invalid.update({'high-surrogate':'\ud800','low-surrogate':'\udc00','surrogate-pair':'\ud800\udc00','surrogate-key':{'\ud800':1},'integer-serializer-limit':1 << (4*4301)})
    for label,value in invalid.items():
        def negative(value=value):
            direct=expect_value_error(lambda:fixed.canonical_contract(value))
            nested=json.loads(encoded(c));nested['boundary']['gateway']['invalid']=value
            through_successor=expect_value_error(lambda:fixed.successor(base_raw,nested,FOOTER))
            return {'direct_refusal':direct,'successor_refusal':through_successor}
        check(branch+'/reject-'+label,negative)
    mutations={'schema':lambda v:v.__setitem__('schema','wrong'),'phase':lambda v:v.__setitem__('phase','wrong'),'scope':lambda v:v.__setitem__('scope',v['scope']+'changed'),'source':lambda v:v['source'].__setitem__('sha256',sha(b'changed')),'crypto':lambda v:v['crypto'].__setitem__('data_integrity_verified',True),'product':lambda v:v['product'].__setitem__('source_layers',-1),'footer-hash':lambda v:v['footer'].__setitem__('sha256',sha(b'changed-footer'))}
    for label,mutate in mutations.items():
        def invalid_shape(mutate=mutate):
            value=json.loads(encoded(c));mutate(value)
            return {'refusal':expect_value_error(lambda:fixed.successor(base_raw,value,FOOTER))}
        check(branch+'/shape-'+label,invalid_shape)
    check(branch+'/wrong-base',lambda:{'refusal':expect_value_error(lambda:fixed.successor(base_raw+b'\n',c,FOOTER))})
    for label,footer in (('missing-contract',b'F06_CONTRACT={}\n'),('double-contract',b'A=__CONTRACT__\nB=__CONTRACT__\n')):
        def invalid_footer(footer=footer):
            value=json.loads(encoded(c));value['footer']=ref('synthetic-invalid-footer',footer)
            return {'refusal':expect_value_error(lambda:fixed.successor(base_raw,value,footer))}
        check(branch+'/'+label,invalid_footer)
    def list_order():
        value=json.loads(encoded(c));value['boundary']['gateway']['diagnostics']['number_types'].reverse()
        assert fixed.successor(base_raw,value,FOOTER)!=stable
        return {'list_order_is_preserved_not_sorted':True}
    check(branch+'/list-order-significant',list_order)
    def numeric_types():
        outputs=[]
        for value in (False,0,0.0,-0.0):
            variant=json.loads(encoded(c));variant['boundary']['gateway']['diagnostics']['number_types']=[value]
            outputs.append(sha(fixed.successor(base_raw,variant,FOOTER)))
        assert len(set(outputs))==4
        return {'bool_int_float_negative_zero_produce_distinct_bytes':True,'sha256':outputs}
    check(branch+'/numeric-types-significant',numeric_types)

def audit_negatives():
    for event in ('socket.connect','subprocess.Popen','os.system','os.fork'):
        try:sys.audit(event)
        except PermissionError:pass
        else:raise AssertionError('effect audit not enforced')
    try:Path('/synthetic-denied/body-never-read').read_bytes()
    except PermissionError:pass
    else:raise AssertionError('undeclared read not refused')
    try:Path('/synthetic-denied/output-never-written').write_bytes(b'x')
    except PermissionError:pass
    else:raise AssertionError('undeclared write not refused')
    return {'denied':list(DENIED),'socket_module_imported':'socket' in sys.modules,'subprocess_module_imported':'subprocess' in sys.modules}
check('audit-declared-access-and-effect-boundaries',audit_negatives)
usage=resource.getrusage(resource.RUSAGE_SELF)
summary={'schema':'frw.F06.canonical-producer-pure-controls.v1','status':'PASS' if all(x['status']=='PASS' for x in CHECKS) else 'FAIL','started_unix':START,'completed_unix':time.time(),'elapsed_seconds':time.monotonic()-MONO,'resources':{'cpu_seconds':usage.ru_utime+usage.ru_stime,'max_rss_kib':usage.ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'rlimit_cpu':resource.getrlimit(resource.RLIMIT_CPU),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE)},'input_sha256':PINS,'checks':CHECKS,'read_paths':sorted(set(READS)),'effect_limits':{'generated_consumer_executed':False,'network_or_model_or_native':False,'real_secret_document_authority_reads':False,'synthetic_footer':True,'canonical_reconstruction_guard_waiver':False}}
write('controls.json',encoded(summary))
print(json.dumps({'status':summary['status'],'checks':len(CHECKS),'failed':[x['name'] for x in CHECKS if x['status']!='PASS'],'elapsed_seconds':summary['elapsed_seconds'],'cpu_seconds':summary['resources']['cpu_seconds'],'max_rss_kib':usage.ru_maxrss},sort_keys=True))
raise SystemExit(0 if summary['status']=='PASS' else 1)
