"""Bounded 207 delta controls. Only own/frozen source and named Root closure read.
Installation metadata/filesystem/runtime-hash reads below are explicit memory seams.
No H/DB/process/native/Store/token/doc/API/issuer/clock/admission effect is invoked.
"""
import ast, copy, hashlib, json, os, resource, time, types
from pathlib import Path
os.umask(0o077)
started=time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
O=Path(__file__).resolve().parent
W=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY-SINGLETON-SOURCE-20261112')
events=[]
def load(path):
    m=types.ModuleType('_inert_'+path.name.replace('.','_'));m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m
def yes(name,fn):
    fn();events.append({'name':name,'outcome':'PASS'})
def no(name,fn):
    try:fn()
    except (ValueError,KeyError,TypeError):events.append({'name':name,'outcome':'EXPECTED_REFUSAL'});return
    raise AssertionError('Accepted '+name)
def check(value):assert value
a=load(O/'f06_source.py');old=load(W/'f06_source.py')
m=load(O/'current207.py');om=load(W/'current206.py')
d=load(O/'root_bind_dispatch_once.py')
yes('default_contract_UNBOUND',lambda:check(a.unbound()['status']=='UNBOUND_NOT_GRANTED'))
yes('default_current_proof_UNBOUND',lambda:check(m.unbound_proof()['status']=='UNBOUND_NOT_GRANTED'))
no('default_driver_rejected',lambda:d.validate_inputs(json.loads((O/'ROOT-BINDING-INPUTS.UNBOUND.json').read_bytes())))
no('default_bound_contract_rejected',lambda:a.contract_shape(a.unbound()))
yes('207_counts_exact',lambda:check(a.PRODUCT_COUNTS==dict(source_layers=207,project_files=495,native_files=17891,plugin_files=52,base_source_files=17730)))
yes('all_original_scope_source_crypto_timing_observation_proofs_fields_unchanged',lambda:check(all(getattr(a,k)==getattr(old,k) for k in ('SOURCE','CRYPTO','TIMING','OBSERVE','PROOFS','FIELDS','BOUNDARY','PHASE','BASE','BASE_SHA','INSTALLED_TESTER','INSTALLED_TESTER_SHA')) and a.scope()==old.scope()))
yes('exact_codec_key_changed_only',lambda:check(set(m.RUNTIME_HASHES)==set(om.RUNTIME_HASHES) and len(m.RUNTIME_HASHES)==12 and [k for k in m.RUNTIME_HASHES if m.RUNTIME_HASHES[k]!=om.RUNTIME_HASHES[k]]==['tools/scoped_odf_password.py'] and m.RUNTIME_HASHES['tools/scoped_odf_password.py']=='b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d'))
yes('all_11_other_runtime_hashes_unchanged',lambda:check(sum(m.RUNTIME_HASHES[k]==om.RUNTIME_HASHES[k] for k in m.RUNTIME_HASHES)==11))
yes('footer_byteexact_unchanged',lambda:check((O/'f06_footer.py.txt').read_bytes()==(W/'f06_footer.py.txt').read_bytes()))

mapping={
 om.CLOSURE_SHA:m.CLOSURE_SHA,om.RECEIPT:m.RECEIPT,om.INPUT:m.INPUT,
 om.RUNTIME_HASHES['tools/scoped_odf_password.py']:m.RUNTIME_HASHES['tools/scoped_odf_password.py']}
class VersionOnly(ast.NodeTransformer):
    def visit_Constant(self,node):
        value=node.value
        if type(value) is int and value in (206,493):node.value={206:207,493:495}[value]
        elif type(value) is str:
            node.value=mapping.get(value,value.replace('206','207').replace('493','495'))
        return node
def same_ast(before,after):
    return ast.dump(VersionOnly().visit(ast.parse(before)),include_attributes=False)==ast.dump(ast.parse(after),include_attributes=False)
for b,n in [('f06_source.py','f06_source.py'),('current206.py','current207.py'),('root_bind_dispatch_once.py','root_bind_dispatch_once.py')]:
    yes(n+'_AST_changes_are_exact_version_constants_only',lambda b=b,n=n:check(same_ast((W/b).read_bytes(),(O/n).read_bytes())))

base=a.BASE.read_bytes()
yes('frozen_fullv42_source_pin',lambda:check(a.digest(base)==a.BASE_SHA))
generated=a.successor(base,a.unbound(),(O/'f06_footer.py.txt').read_bytes())
old_unbound=(W/'bot_tester.f06.UNBOUND.py').read_text()
assert old_unbound.count("'source_layers': 206")==old_unbound.count("'project_files': 493")==1
old_unbound=old_unbound.replace("'source_layers': 206","'source_layers': 207").replace("'project_files': 493","'project_files': 495")
yes('fullconsumer_reconstructs_with_only207_contract_counts',lambda:check(old_unbound.encode()==generated))
oldtree=ast.parse(base);newtree=ast.parse(generated)
def firstdefs(tree):
    result={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name not in result:result[node.name]=node
    return result
defs0,defs1=firstdefs(oldtree),firstdefs(newtree)
for name,node in defs0.items():
    if name!='Runner':assert ast.dump(node,include_attributes=False)==ast.dump(defs1[name],include_attributes=False),name
methods0={n.name:n for n in defs0['Runner'].body if isinstance(n,ast.FunctionDef)}
methods1={n.name:n for n in defs1['Runner'].body if isinstance(n,ast.FunctionDef)}
for name,node in methods0.items():
    if name!='ordinary_independent_admission':assert ast.dump(node,include_attributes=False)==ast.dump(methods1[name],include_attributes=False),name
yes('original_fullconsumer_190_methods_AST_unchanged_except_admission_seam',lambda:check(len(methods0)-1==190))
p=O/'bot_tester.f06.UNBOUND.py';p.write_bytes(generated);p.chmod(0o600)

closure_raw=m.CLOSURE.read_bytes();closure=json.loads(closure_raw)
yes('Root_actual207_closure_exact_SHA_not_projection',lambda:check(m.digest(closure_raw)==m.CLOSURE_SHA=='996b43c584c8eb6d5c8dbbeb60f500958c873427cda0881ae74a7618d920f963'))
yes('Root_actual207_closure_receipt_input_tuple_join',lambda:check(closure['schema']=='friday.root.actual207.complete-closure.v1' and closure['installed']['canonical4']['source_receipt']['sha256']==m.RECEIPT and closure['installed']['canonical4']['current_input']['sha256']==m.INPUT and {k:closure['installed'][k] for k in ('layers','project','native','plugins','base')}==dict(layers=207,project=495,native=17891,plugins=52,base=17730)))

# From here all external reads/hashes are memory-only disclosed doubles. The
# actual installation() code executes unchanged to test each exact207 join.
receipt=dict(layers=list(range(207)),files={str(i):'x' for i in range(17891)},source_file_count=17730,base_tree='synthetic-base')
marker=dict(source_receipt_sha256=m.RECEIPT,input_sha256=m.INPUT,plugin_files={'synthetic-plugin-'+str(i):'synthetic-plugin-hash' for i in range(52)})
stamp=dict(fridaySource=dict(layers=receipt['layers'],baseTree=receipt['base_tree']))
inputs=dict(project_files={str(i):'x' for i in range(495)})
canonical=dict(source_receipt=receipt,marker=marker,stamp=stamp,current_input=inputs)
runtime=dict(m.RUNTIME_HASHES)
read_calls=[]
def fake_readref(ref,private=True):
    read_calls.append(('readref',ref['path']))
    if ref['path']==str(m.CLOSURE):return copy.deepcopy(closure)
    for key,known in closure['installed']['canonical4'].items():
        if ref['path']==known['path']:return copy.deepcopy(canonical[key])
    return {}
def fake_read(path,*args,**kwargs):
    read_calls.append(('read',str(path)))
    relative=str(path.relative_to(m.H))
    if relative.startswith('hermes-agent/'):return runtime[relative[len('hermes-agent/'):]].encode()
    return b'synthetic-plugin-hash'
m.readref=fake_readref;m.reference=lambda ref,private=True:b'synthetic-pinned-ref'
m.read=fake_read;m.digest=lambda raw:raw.decode()
proof=dict(installation_closure={'path':str(m.CLOSURE),'sha256':m.CLOSURE_SHA},installation_acceptance=closure['source_acceptance'])
yes('actual_installation_function207_join_with_disclosed_memory_IO_hash_seams',lambda:m.installation(proof))
q=copy.deepcopy(proof);q['installation_closure']={'path':str(om.CLOSURE),'sha256':om.CLOSURE_SHA}
no('old206_closure_pin_refused',lambda:m.installation(q))
q=copy.deepcopy(proof);q['installation_closure']['sha256']='0'*64
no('wrong207_closure_SHA_refused',lambda:m.installation(q))
orig=copy.deepcopy(closure)
closure['schema']='friday.root.actual206.complete-closure.v1'
no('old206_payload_at_newref_refused',lambda:m.installation(proof))
closure=copy.deepcopy(orig);closure['installed']['layers']=206
no('206_tuple_refused',lambda:m.installation(proof))
closure=copy.deepcopy(orig);closure['installed']['canonical4']['source_receipt']['sha256']=om.RECEIPT
no('old206_receipt_at207_refused',lambda:m.installation(proof))
closure=copy.deepcopy(orig);marker['input_sha256']='0'*64
no('wrong_input_join_refused',lambda:m.installation(proof))
marker['input_sha256']=m.INPUT
runtime['tools/scoped_odf_password.py']=om.RUNTIME_HASHES['tools/scoped_odf_password.py']
no('old206_codec_hash_at207_refused',lambda:m.installation(proof))
runtime['tools/scoped_odf_password.py']=m.RUNTIME_HASHES['tools/scoped_odf_password.py']
runtime['gateway/ordinary_turn_projection.py']='b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d'
no('positional_misassignment_to_projection_refused',lambda:m.installation(proof))
runtime['gateway/ordinary_turn_projection.py']=m.RUNTIME_HASHES['gateway/ordinary_turn_projection.py']
yes('207_join_restored_after_controls',lambda:m.installation(proof))
for label,change in [('old206_contract',lambda c:c['product'].update(source_layers=206,project_files=493)),('replay_or_sibling_phase',lambda c:c.update(phase='DOCX-CORRECT-READ'))]:
    q=a.unbound();change(q)
    no(label+'_refused_before_binding',lambda q=q:a.contract_shape(q,bound=False))
no('source_unbound_authority_cannot_dispatch_or_replay',lambda:d.validate_inputs({'status':'ROOT_BOUND_ONE_FUTURE_OPERATION'}))

result=dict(schema='frw.F06.ordinary207-delta-controls.v1',status='PASS_SOURCE_ONLY',checks=len(events),events=events,
    actual_installation_observed_by_child=False,actual_Root_closure_metadata_SHA_verified=True,
    core_original_runner_methods_unchanged=len(methods0)-1,
    current207_sha256=hashlib.sha256((O/'current207.py').read_bytes()).hexdigest(),
    adapter_sha256=hashlib.sha256((O/'f06_source.py').read_bytes()).hexdigest(),
    driver_sha256=hashlib.sha256((O/'root_bind_dispatch_once.py').read_bytes()).hexdigest(),
    unbound_fullconsumer_sha256=hashlib.sha256(generated).hexdigest(),
    seams=['installation external readref/reference/read/digest are disclosed memory doubles; no actual source hash read','no runtime/current boundary/DB/native/systemd/slot/token/document/API/issuer observation'],
    old_R3_stop_path_and_deadline_controls_reused_on_identical_AST=True,
    actual_model_Telegram_Office_admission_clock_effects=0,
    elapsed_seconds=time.monotonic()-started,cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(O/'VERSION-CONTROLS.json').write_bytes(a.encoded(result));(O/'VERSION-CONTROLS.json').chmod(0o600)
print(json.dumps({k:result[k] for k in ('status','checks','elapsed_seconds','max_RSS_KiB')}))
