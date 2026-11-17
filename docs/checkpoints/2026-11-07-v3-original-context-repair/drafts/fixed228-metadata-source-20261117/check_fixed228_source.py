"""Bounded pure Source checks; reads only named Code/basis/cached canonical inputs."""
import ast
import builtins
import contextlib
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import types

ROOT = Path('/home/jericho/.cache/FRW-ASTRA-FIXED228-METADATA-SIBLING-SOURCE-20261117')
SPEC_SHA = '8320f22d3a0777108fd451d56d12fd21076998cd4a93a0ca7c5beeb37c8f070b'
CODE_SHA = '17495f60426d492954e7f2a467b24cff462e9139a7c8d8758aabbe776e905ecd'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def load_ref(ref):
    raw=Path(ref['path']).read_bytes()
    assert len(raw)==ref['bytes'] and digest(raw)==ref['sha256'], 'INPUT_PIN_CHANGED'
    return raw

def write_json(name,value):
    target=ROOT/name
    target.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    target.chmod(0o600)

def copy(value):
    return json.loads(json.dumps(value))

spec_raw=(ROOT/'ROOT-AUTHORING-SPEC.json').read_bytes()
assert digest(spec_raw)==SPEC_SHA
spec=json.loads(spec_raw)
basis_raw=load_ref(spec['normalized_basis']);basis=json.loads(basis_raw)
old_raw=load_ref(spec['old_source']);old=old_raw.decode()
code_raw=(ROOT/'fixed228_metadata_source.py').read_bytes();assert digest(code_raw)==CODE_SHA
code=code_raw.decode();oldtree=ast.parse(old);newtree=ast.parse(code)
canonical_raw={k:load_ref(ref) for k,ref in spec['cached_canonical4'].items()}
canonical={k:json.loads(v) for k,v in canonical_raw.items()}
c=types.ModuleType('_fixed228_source');c.__file__=str(ROOT/'fixed228_metadata_source.py')
exec(compile(code,c.__file__,'exec'),c.__dict__)
# No reference/canonical/current access is available during either pure call.
@contextlib.contextmanager
def pure_only():
    def blocked(*args,**kwargs):
        raise AssertionError('PURE_CHECK_ATTEMPTED_IO')
    saved=(builtins.open,os.open,Path.open,Path.read_bytes,Path.read_text,c._read_bounded,c.read_reference,c.read_saved_reference)
    builtins.open=os.open=Path.open=Path.read_bytes=Path.read_text=c._read_bounded=c.read_reference=c.read_saved_reference=blocked
    try:
        yield
    finally:
        builtins.open,os.open,Path.open,Path.read_bytes,Path.read_text,c._read_bounded,c.read_reference,c.read_saved_reference=saved

observations=[]
with pure_only():
    metadata=c.installation_metadata(basis)
    shapes=c.installation_shapes(basis,canonical['receipt'],canonical['marker'],canonical['stamp'],canonical['input'])
assert shapes==metadata
assert metadata['counts']=={'layers':228,'project':537,'native':17895,'plugins':52,'base':17730}
assert metadata['native_two']==spec['current_native_two']
assert metadata['retained_dependency_four']==spec['retained226_dependency_four']
assert metadata['retained_dependency_two']==spec['previous227_two_retained_not_current_targets']
assert metadata['Source_eight_capture']==basis['Source_eight_capture']
assert 'NOT_CAPTURED' in metadata['Source_eight_capture']['state']
assert metadata['poststart_optional_Source_custody']['required_for_ordinary_install'] is False
assert metadata['current_admission'] is False and metadata['user_semantic_acceptance'] is False
assert metadata['canonical_values_assessed'] is False
observations.append({'case':'actual_cached_canonical4_pure_metadata_and_shapes','status':'PASS','io_blocked':True})

def expect_reject(name,callback,expected):
    with pure_only():
        try:
            callback()
        except ValueError as exc:
            assert str(exc)==expected, (name,str(exc),expected)
            observations.append({'case':name,'status':'REJECTED','code':str(exc)})
        else:
            raise AssertionError('NEGATIVE_ACCEPTED:'+name)

def metadata_negative(name,modify,expected):
    bad=copy(basis);modify(bad)
    expect_reject(name,lambda:c.installation_metadata(bad),expected)

def shape_negative(name,kind,modify,expected='DOCX228_CANONICAL_TUPLE_CHANGED'):
    values=dict(canonical);values[kind]=copy(values[kind]);modify(values[kind])
    expect_reject(name,lambda:c.installation_shapes(basis,values['receipt'],values['marker'],values['stamp'],values['input']),expected)

metadata_negative('normalized_count_layers',lambda x:x['counts'].__setitem__('layers',227),'DOCX228_ACTUAL_NORMALIZED_INSTALLATION_METADATA_REQUIRED')
metadata_negative('normalized_count_project',lambda x:x['counts'].__setitem__('project',535),'DOCX228_ACTUAL_NORMALIZED_INSTALLATION_METADATA_REQUIRED')
metadata_negative('canonical_hash',lambda x:x['canonical']['receipt'].__setitem__('sha256','0'*64),'DOCX228_CANONICAL_METADATA_TUPLE_CHANGED')
metadata_negative('canonical_size',lambda x:x['canonical']['stamp'].__setitem__('bytes',x['canonical']['stamp']['bytes']+1),'DOCX228_CANONICAL_METADATA_TUPLE_CHANGED')
metadata_negative('canonical_path',lambda x:x['canonical']['input'].__setitem__('path','/tmp/substitute228.json'),'DOCX228_CANONICAL_METADATA_TUPLE_CHANGED')
metadata_negative('authenticated_closure_hash',lambda x:x['Root_authenticated_closure'].__setitem__('sha256','0'*64),'DOCX228_EXACT_ROOT_NORMALIZED_BASIS_CHANGED')
metadata_negative('CAS8_downgrade',lambda x:x['native_delta'].__setitem__('CAS',7),'DOCX228_ACTUAL_NORMALIZED_INSTALLATION_METADATA_REQUIRED')
metadata_negative('native_two_old227_targets',lambda x:x.__setitem__('native_two',spec['previous227_two_retained_not_current_targets']),'DOCX228_NATIVE_TWO_METADATA_CHANGED')
metadata_negative('native_word_metadata_hash',lambda x:x['native_two']['tools/scoped_word_conversion.py'].__setitem__('sha256','0'*64),'DOCX228_NATIVE_TWO_METADATA_CHANGED')
metadata_negative('source_acceptance_hash',lambda x:x['source_acceptance'].__setitem__('sha256','0'*64),'DOCX228_INSTALLATION_SOURCE_ACCEPTANCE_METADATA_CHANGED')
metadata_negative('source_eight_old227_relabel',lambda x:x.__setitem__('Source_eight_capture',{'path':'/tmp/old227-capture.json','bytes':3877,'sha256':'a7bda60ca05c97a72e844ebc2bcfb71c26c583d39cb235a817e4b56dd51aee4f'}),'DOCX228_EXACT_ROOT_NORMALIZED_BASIS_CHANGED')
metadata_negative('optional_capture_promoted_prerequisite',lambda x:x['poststart_optional_Source_custody'].__setitem__('required_for_ordinary_install',True),'DOCX228_EXACT_ROOT_NORMALIZED_BASIS_CHANGED')
for key in ('current_admission','execution_grant','event_or_read_capability','future_user_semantics'):
    metadata_negative('authority_promotion_'+key,lambda x,key=key:x.__setitem__(key,True),'DOCX228_DATED_CLOSURE_NOT_CURRENT_AUTHORITY_REQUIRED')
oldbasis=next(ast.literal_eval(n.value) for n in oldtree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='METADATA_BASIS')
expect_reject('genuine_old227_basis',lambda:c.installation_metadata(oldbasis),'DOCX228_ACTUAL_NORMALIZED_INSTALLATION_METADATA_REQUIRED')
shape_negative('receipt_layers_count','receipt',lambda x:x['layers'].pop())
shape_negative('receipt_native_count','receipt',lambda x:x['files'].pop(next(iter(x['files']))))
shape_negative('receipt_base_count','receipt',lambda x:x.__setitem__('source_file_count',17729))
shape_negative('marker_plugins_count','marker',lambda x:x['plugin_files'].pop(next(iter(x['plugin_files']))))
shape_negative('input_project_count','input',lambda x:x['project_files'].pop(next(iter(x['project_files']))))
shape_negative('marker_receipt_hash','marker',lambda x:x.__setitem__('source_receipt_sha256','0'*64))
shape_negative('marker_input_hash','marker',lambda x:x.__setitem__('input_sha256','0'*64))
shape_negative('stamp_layers_mismatch','stamp',lambda x:x['fridaySource']['layers'].pop())
for name in spec['current_native_two']:
    shape_negative('native_word_leaf_'+name,'receipt',lambda x,name=name:x['files'][name].__setitem__('sha256','0'*64),'DOCX228_ACCEPTED_NATIVE_DEPENDENCY_CHANGED')
for name in spec['previous227_two_retained_not_current_targets']:
    shape_negative('retained227_leaf_'+name,'receipt',lambda x,name=name:x['files'][name].__setitem__('sha256','0'*64),'DOCX228_ACCEPTED_NATIVE_DEPENDENCY_CHANGED')
for name in spec['retained226_dependency_four']:
    shape_negative('retained226_leaf_'+name,'receipt',lambda x,name=name:x['files'][name].__setitem__('sha256','0'*64),'DOCX228_ACCEPTED_NATIVE_DEPENDENCY_CHANGED')
# Returned values cannot mutate pinned module or normalized input.
shapes['native_two'].clear();shapes['Source_eight_capture']['state']='CAPTURED'
with pure_only():
    assert c.installation_metadata(basis)==metadata
observations.append({'case':'returned_metadata_is_detached_clone','status':'PASS'})
# All ordinary admission/current entrypoints remain deliberate refusals.
expect_reject('check_refusal',lambda:c.check(None,run_id='test',scenario='test',stage='test'),'FIXED227_METADATA_ONLY_NO_ADMISSION_ENTRYPOINT')
expect_reject('installation_refusal',lambda:c.installation(None),'FIXED227_METADATA_ONLY_USE_EXPLICIT_CANONICAL_CHECKS')
expect_reject('observe_refusal',lambda:c.observe(None),'FIXED227_METADATA_ONLY_NO_CURRENT_OBSERVATION_ENTRYPOINT')
expect_reject('observe_readonly_refusal',lambda:c.observe_readonly(phase='test',run_id='test',closure_ref=None,acceptance_ref=None,resource_limits=None),'FIXED227_METADATA_ONLY_NO_CURRENT_OBSERVATION_ENTRYPOINT')

oldfunctions={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
newfunctions={n.name:n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert set(oldfunctions)==set(newfunctions)
changed=[];unchanged=[]
for name in oldfunctions:
    before=oldfunctions[name];after=newfunctions[name]
    assert ast.dump(before.args,include_attributes=False)==ast.dump(after.args,include_attributes=False), 'ABI_CHANGED:'+name
    oldsource=ast.get_source_segment(old,before);newsource=ast.get_source_segment(code,after)
    same_ast=ast.dump(before,include_attributes=False)==ast.dump(after,include_attributes=False)
    same_bytes=oldsource==newsource
    assert same_ast==same_bytes
    (unchanged if same_ast else changed).append({'name':name,'same_ast':same_ast,'same_bytes':same_bytes,'old_source_sha256':digest(oldsource.encode()),'new_source_sha256':digest(newsource.encode())})
assert {r['name'] for r in changed}=={'installation_metadata','installation_shapes'}
inventory={'schema':'frw.fixed228.metadata-source-api-inventory.v1','function_count':len(newfunctions),'abi_unchanged_all_functions':True,'changed_metadata_functions':changed,'unchanged_functions':unchanged,'unchanged_function_count':len(unchanged),'refusal_error_labels_retained':'Historical FIXED227 labels preserve exact refusal helper bodies; all refusal semantics unchanged.'}
def assignments(tree):
    return {n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
oldassignments=assignments(oldtree);newassignments=assignments(newtree)
changed_constants=[name for name in oldassignments if ast.dump(oldassignments[name],include_attributes=False)!=ast.dump(newassignments[name],include_attributes=False)]
added_constants=sorted(set(newassignments)-set(oldassignments))
assert set(changed_constants)=={'CLOSURE','ACCEPTANCE','COUNTS','SOURCE_COMMIT','EXECUTION_COMMIT','RECEIPT_SHA','INPUT_SHA','CANONICAL_REFS','CANONICAL_PINS','NATIVE_TWO','LEAF_PINS','METADATA_BASIS'}
assert added_constants==['RETAINED227_DEPENDENCIES'] and not set(oldassignments)-set(newassignments)
oldimports=[ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
newimports=[ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
assert oldimports==newimports
inventory.update(module_constant_changes=changed_constants,module_constant_additions=added_constants,
                 unchanged_module_assignments=[name for name in oldassignments if name not in changed_constants],
                 import_ast_unchanged=True,
                 module_changes_other_than_constants_and_two_metadata_functions=['library docstring version label','__main__ refusal version label (same refusal semantics)'])
write_json('API-AST-INVENTORY.json',inventory)
diff=''.join(difflib.unified_diff(old.splitlines(True),code.splitlines(True),fromfile=spec['old_source']['path'],tofile=str(ROOT/'fixed228_metadata_source.py')))
(ROOT/'fixed227-to-fixed228.diff').write_text(diff);(ROOT/'fixed227-to-fixed228.diff').chmod(0o600)
checks={'schema':'frw.fixed228.metadata-source-isolated-checks.v1','at_moscow':dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),'code':{'path':str(ROOT/'fixed228_metadata_source.py'),'bytes':len(code_raw),'sha256':digest(code_raw)},'normalized_basis':spec['normalized_basis'],'canonical_raw_authenticated':{k:{'bytes':len(v),'sha256':digest(v)} for k,v in canonical_raw.items()},'positive_count':sum(x['status']=='PASS' for x in observations),'negative_count':sum(x['status']=='REJECTED' for x in observations),'observations':observations,'bounds':'Only named Source files and four cached canonical JSONs loaded; metadata/shapes/refusal calls ran with file IO blocked. No H/current/live/model/API/Office/install/8capture/DB effects; no full MD suite.'}
write_json('ISOLATED-CHECKS.json',checks)
print(json.dumps({'state':'PASS','positive_count':checks['positive_count'],'negative_count':checks['negative_count'],'unchanged_functions':len(unchanged),'changed_functions':[r['name'] for r in changed],'code':checks['code']}))
