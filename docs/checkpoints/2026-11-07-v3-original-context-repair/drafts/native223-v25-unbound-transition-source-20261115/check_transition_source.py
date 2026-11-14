#!/usr/bin/env python3
"""Finite SOURCE delta controls. Explicit inert IO and AST precondition slices are not actual H/preflight."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import types

OUT=Path(__file__).resolve().parent
CAPTURE=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE223-ACTUAL222-PREDECESSOR-CAPTURE-20261115/ACTUAL222-ROOT-CANONICAL-CAPTURE.json')
ORIGINALS={'private':Path('/home/jericho/.cache/FRW-ASTRA-NATIVE222-ACTUAL-CALLER-GATE-20261114/project/scripts/friday_ordinary_install.py'),
    'public':Path('/home/jericho/.cache/FRW-ASTRA-NATIVE222-ROOT-ACTUAL221-ORIGIN-CAPTURE-20261114/public-project525/scripts/friday_ordinary_install.py')}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(a):return (json.dumps(a,sort_keys=True,indent=2)+'\n').encode()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Refused(Exception):pass
class StopAtRoot(Exception):pass
class F:
    MARKER='FRIDAY-INSTALL.json'
    def require(self,ok,reason):
        if not ok:raise Refused(reason)
    def canonical(self,path):return Path(path) # opaque strings only, never resolve/stat/open
    def directory(self,path):return Path(path) # inert IO leaf
    def digest(self,raw):return sha(raw)
    def unique(self,pairs):
        d={}
        for k,v in pairs:self.require(k not in d,'duplicate_key');d[k]=v
        return d
f=F();rows=[]
def passed(name,**facts):rows.append({'control':name,'state':'PASS',**facts})
def rejected(name,call,reason=None):
    try:call()
    except (Refused,ValueError) as e:
        if reason is not None:assert str(e)==reason,(name,str(e),reason)
        passed(name,reason=str(e))
    else:raise AssertionError(name+' unexpectedly accepted')
def restored(m,attrs,call):
    old={k:getattr(m,k) for k in attrs}
    for k,v in attrs.items():setattr(m,k,v)
    try:return call()
    finally:
        for k,v in old.items():setattr(m,k,v)

capraw=CAPTURE.read_bytes();assert sha(capraw)=='32b80537a4e8c51246b21830b80b3fb48d8e3d6ffdc600006e660d9f7debca25'
cap=json.loads(capraw);obj={};raws={}
for role,ref in cap['roles'].items():
    p=Path(ref['cache_path']);assert p.is_relative_to(CAPTURE.parent/'actual222')
    raw=p.read_bytes();assert len(raw)==ref['bytes'] and sha(raw)==ref['sha256'];obj[role]=json.loads(raw);raws[role]=raw
passed('genuine222_exact8_reused_cache_hashes',canonical_paths_opened=0)
modules={kind:load('source223_'+kind,OUT/kind/'scripts/friday_ordinary_install.py') for kind in ORIGINALS}
for m in modules.values():m.api=lambda:f
m=modules['private'];layer=m.CURRENT_SOURCE_TWENTY_FIFTH_LAYER
actual_ref={'path':cap['roles']['request']['canonical_path'],'sha256':cap['roles']['request']['sha256']}
for role in ('request','input','receipt','stamp','marker','intent','committed'):
    assert getattr(m,'CURRENT_SOURCE_TWENTY_FIFTH_PREVIOUS_'+role.upper())==cap['roles'][role]['sha256']
assert m.CURRENT_SOURCE_TWENTY_FIFTH_PREVIOUS_HELPER==obj['input']['project_files'][m.PROJECT_DSH_CURRENT_HELPER]
passed('genuine222_seven_origin_and_private_before_helper_pins')
# Independently transformed whole files retain their exact historical differences.
asts={k:ast.parse((OUT/k/'scripts/friday_ordinary_install.py').read_text()) for k in ORIGINALS}
methods={k:{n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))} for k,t in asts.items()}
region=[n for n in methods['private'] if n.startswith('_current_source_') or n.startswith('_CurrentSource') or n in ('current_native_source_successor_checked','_current_native_source_edge_checked')]
assert all(ast.dump(methods['private'][n],include_attributes=False)==ast.dump(methods['public'][n],include_attributes=False) for n in region)
for kind in ORIGINALS:
    orig={n.name:n for n in ast.parse(ORIGINALS[kind].read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    changed={n for n in orig if ast.dump(orig[n],include_attributes=False)!=ast.dump(methods[kind][n],include_attributes=False)}
    assert changed=={'_current_source_twenty_fourth_successor_checked','current_native_source_successor_checked','_current_native_source_edge_checked'},changed
    passed(kind+'_all_old_proofs_and_unrelated_functions_preserved',changed_functions=sorted(changed))
passed('new_current_chain_private_public_AST_matching',count=len(region),whole_files_identical=False)

for kind,x in modules.items():
    rejected(kind+'_unbound_source_delta',x._current_source_twenty_fifth_bindings_checked,'ordinary_current_successor_twenty_fifth_final_layer_binding_required')
    rejected(kind+'_unbound_before_any_home_IO',lambda x=x:x.current_native_source_successor_checked({'home':'OPAQUE-SOURCE-HOME'},cli_only=True,source_update={'current_source_successor':{'schema':x.CURRENT_SOURCE_TWENTY_FIFTH_SUCCESSOR_SCHEMA}}),'ordinary_current_successor_twenty_fifth_final_layer_binding_required')
    rejected(kind+'_unbound_direct_edge_before_any_home_IO',lambda x=x:x._current_native_source_edge_checked({'home':'OPAQUE-SOURCE-HOME'},cli_only=True,source_update={'current_source_successor':{'schema':x.CURRENT_SOURCE_TWENTY_FIFTH_SUCCESSOR_SCHEMA}}),'ordinary_current_successor_twenty_fifth_final_layer_binding_required')
    rejected(kind+'_external_history_constructor',lambda x=x:x._CurrentSourceTwentyFifthHistory({}, {}, {}, {}, {}, _seal=object()),'ordinary_current_successor_internal_twenty_fifth_history_required')

# Temporary in-memory tuples exercise source validation only; never stored as real bindings.
native_name='gateway/run_turn.py';before=obj['receipt']['files'][native_name]['sha256']
pure_native={native_name:(before,'1'*64,7,False),'source-only/new-file.py':(None,'2'*64,0,True)}
bound_memory={'CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST':'3'*64,'CURRENT_SOURCE_TWENTY_FIFTH_PATCH':'4'*64,'CURRENT_SOURCE_TWENTY_FIFTH_NATIVE':pure_native}
assert restored(m,bound_memory,m._current_source_twenty_fifth_bindings_checked) is True
passed('pure_source_tuple_types_replace_and_true_new_file',not_actual_binding=True)
for name,pins in [('empty',{}),('foreign_abs',{'/tmp/foreign':(None,'2'*64,1,True)}),('dot_alias',{'a/../b':(None,'2'*64,1,True)}),('slash_alias',{'a//b':(None,'2'*64,1,True)}),('bool_bytes',{'a':(None,'2'*64,True,True)}),('unbound_after',{'a':(None,'UNBOUND',1,True)}),('false_new_flag',{'a':(None,'2'*64,1,False)}),('integer_new_flag',{'a':(None,'2'*64,1,1)}),('unchanged',{'a':('2'*64,'2'*64,1,False)})]:
    a={**bound_memory,'CURRENT_SOURCE_TWENTY_FIFTH_NATIVE':pins}
    rejected('tuple_'+name,lambda a=a:restored(m,a,m._current_source_twenty_fifth_bindings_checked))
rejected('foreign_layer_binding',lambda:restored(m,{**bound_memory,'CURRENT_SOURCE_TWENTY_FIFTH_LAYER':'foreign'},m._current_source_twenty_fifth_bindings_checked))

# Full new authenticator with inert source leaves and retained222 request bytes.
# Historical24/edge entry observers stop before old chain/current authority.
selected=copy.deepcopy(obj['request']);selected['current_source_successor']={'schema':m.CURRENT_SOURCE_TWENTY_FIFTH_SUCCESSOR_SCHEMA,'root_project_update':copy.deepcopy(obj['request']['current_source_successor']['root_project_update']),'previous_native_update':actual_ref}
selected['previous_input']=copy.deepcopy(obj['request']['current_input']);selected['current_input']={'path':'/SOURCE-ONLY/UNBOUND-next-input.json','sha256':'a'*64}
tx=Path(actual_ref['path']).parent;calls=[]
f.owned_file=lambda path,**kw:raws[{'request.json':'request','intent.json':'intent','committed.json':'committed'}[Path(path).name]]
def source_json(path,**kw):
    path=Path(path)
    if path==Path(actual_ref['path']):return copy.deepcopy(obj['request'])
    if path==Path(obj['request']['current_input']['path']):return copy.deepcopy(obj['input'])
    if path.name=='FRIDAY-INSTALL.json':return copy.deepcopy(obj['marker'])
    raise AssertionError('unexpected source leaf:'+str(path))
def history_observer(value,request,**kw):
    h=kw['_twenty_fifth_history'];assert type(h) is m._CurrentSourceTwentyFifthHistory and h._seal is m._CURRENT_SOURCE_TWENTY_FIFTH_HISTORY_SEAL
    assert h.twenty_fourth_reference==m.encoded(actual_ref) and h.twenty_third_reference==m.encoded(obj['request']['current_source_successor']['previous_native_update'])
    assert kw['historical_marker']==obj['marker'];calls.append('sealed-history222');return {'request':request}
def edge_observer(value,**kw):assert kw['prior_edge']['request']==obj['request'];calls.append('selected-edge');return 'SOURCE-CALLPATH-ONLY'
attrs={**bound_memory,'_current_source_reference':lambda ref:Path(ref['path']),'_current_source_json':source_json,
    '_current_source_cp_transactions':lambda home,ref:tx,'_current_source_cp_proof':lambda *a,**kw:calls.append(('cp-proof',kw['committed'])),
    '_current_source_twenty_fourth_successor_checked':history_observer,'_current_native_source_edge_checked':edge_observer}
assert restored(m,attrs,lambda:m._current_source_twenty_fifth_successor_checked({'home':obj['input']['home']},selected,cli_only=True,source_update=selected))=='SOURCE-CALLPATH-ONLY'
assert calls==[('cp-proof',True),'sealed-history222','selected-edge'];passed('new_authenticator_sealed222_inert_callpath_only',actual_preflight=False)
for label,mutation in [
    ('old_schema',lambda r:r['current_source_successor'].__setitem__('schema',m.CURRENT_SOURCE_TWENTY_FOURTH_SUCCESSOR_SCHEMA)),
    ('future_schema',lambda r:r['current_source_successor'].__setitem__('schema','friday.current-source-native-successor.v26')),
    ('root_substitution',lambda r:r['current_source_successor']['root_project_update'].__setitem__('sha256','0'*64)),
    ('previous_input_substitution',lambda r:r['previous_input'].__setitem__('sha256','0'*64)),
    ('request_pin_substitution',lambda r:r['current_source_successor']['previous_native_update'].__setitem__('sha256','0'*64)),
    ('request_canonical_path_substitution',lambda r:r['current_source_successor']['previous_native_update'].__setitem__('path','/SOURCE-ONLY/foreign.json')),
    ('same_input',lambda r:r.__setitem__('current_input',copy.deepcopy(r['previous_input']))),
    ('same_input_path',lambda r:r['current_input'].__setitem__('path',r['previous_input']['path']))]:
    r=copy.deepcopy(selected);mutation(r)
    # The inert reader can return retained222 for a substituted ref; exact guards must still reject.
    a={**attrs,'_current_source_json':lambda p,**kw:copy.deepcopy(obj['request']) if str(p).endswith('request.json') or str(p).endswith('foreign.json') else source_json(p,**kw)}
    rejected('authenticator_'+label,lambda a=a,r=r:restored(m,a,lambda:m._current_source_twenty_fifth_successor_checked({'home':obj['input']['home']},r,cli_only=True,source_update=r)))
for role in ('intent','committed'):
    original=f.owned_file
    f.owned_file=lambda p,role=role,**kw:b'foreign' if Path(p).name==role+'.json' else original(p,**kw)
    rejected('authenticator_wrong_'+role+'_bytes',lambda:restored(m,attrs,lambda:m._current_source_twenty_fifth_successor_checked({'home':obj['input']['home']},selected,cli_only=True,source_update=selected)))
    f.owned_file=original

# Execute actual bounded-edge context and historical222 join until root observer.
edge=m._current_native_source_edge_checked
prior={'request':{'current_source_successor':{'schema':m.CURRENT_SOURCE_TWENTY_FOURTH_SUCCESSOR_SCHEMA}}}
rejected('terminal25_historical_refused',lambda:restored(m,bound_memory,lambda:edge({'home':obj['input']['home']},cli_only=True,source_update=selected,prior_edge=prior,historical_marker={})), 'ordinary_current_successor_context_required')
priorbad=copy.deepcopy(prior);priorbad['request']['current_source_successor']['schema']=m.CURRENT_SOURCE_TWENTY_THIRD_SUCCESSOR_SCHEMA
rejected('v25_wrong_prior_schema',lambda:restored(m,bound_memory,lambda:edge({'home':obj['input']['home']},cli_only=True,source_update=selected,prior_edge=priorbad)), 'ordinary_current_successor_context_required')
prior23={'request':{'current_source_successor':{'schema':m.CURRENT_SOURCE_TWENTY_THIRD_SUCCESSOR_SCHEMA},'current_input':obj['request']['previous_input']}}
rejected('historical222_missing_internal_seal',lambda:edge({'home':obj['input']['home']},cli_only=True,source_update=obj['request'],prior_edge=prior23,historical_marker={}), 'ordinary_current_successor_context_required')
proof=m._CurrentSourceTwentyFifthHistory(actual_ref,obj['request']['current_source_successor']['previous_native_update'],selected['current_source_successor']['root_project_update'],selected['previous_input'],selected['current_source_successor'],_seal=m._CURRENT_SOURCE_TWENTY_FIFTH_HISTORY_SEAL)
def stop_root(*a):raise StopAtRoot
histattrs={'_current_source_cp_transactions':lambda *a:tx,'_current_source_cp_proof':lambda *a,**kw:calls.append(('historical-cp-proof',kw['committed'])),'_project_current_root_checked':stop_root}
def joined():return restored(m,histattrs,lambda:edge({'home':obj['input']['home']},cli_only=True,source_update=obj['request'],prior_edge=prior23,historical_marker={},_twenty_fifth_history=proof))
try:joined()
except StopAtRoot:passed('historical222_exact_seal_reaches_root_observer_only',actual_chain_run=False)
else:raise AssertionError('root observer not reached')
for attr in ('twenty_fourth_reference','twenty_third_reference','root_reference','selected_previous','selected_context'):
    old=getattr(proof,attr);setattr(proof,attr,b'foreign')
    rejected('history222_substitute_'+attr,joined,'ordinary_current_successor_authenticated_twenty_fourth_history_required');setattr(proof,attr,old)

# Execute unchanged actual AST preconditions, no mirrored validator and no IO leaves.
edge_ast=methods['private']['_current_native_source_edge_checked']
def slice_code(start,end):
    text=(OUT/'private/scripts/friday_ordinary_install.py').read_text().splitlines()
    a=next(n.lineno for n in ast.walk(edge_ast) if isinstance(n,ast.Assign) and ast.get_source_segment('\n'.join(text),n).startswith(start))
    b=next(n.lineno for n in ast.walk(edge_ast) if isinstance(n,ast.For) and ast.get_source_segment('\n'.join(text),n).startswith(end))
    return compile(ast.Module(body=[n for n in edge_ast.body if a<=n.lineno<b],type_ignores=[]),'<REAL-SOURCE-ONLY-PRECONDITIONS>','exec')
projectcode=slice_code("names = request['layer_names']",'for name,expected in files.items()')
flags={n:False for n in ('second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth twenty_first twenty_second twenty_third twenty_fourth twenty_fifth').split()};flags['twenty_fifth']=True
manifest_name='patches/hermes/'+layer+'-manifest.json';patch_name='patches/hermes/'+layer+'.patch'
files=dict(obj['input']['project_files']);files.update({m.PROJECT_DSH_CURRENT_HELPER:'b'*64,manifest_name:'3'*64,patch_name:'4'*64})
req={'layer_names':[layer],'project_file_updates':[m.PROJECT_DSH_CURRENT_HELPER],'layer_manifest_updates':[manifest_name],'project_inventory':files,'project_inventory_sha256':sha(m.encoded(files))}
def project_env():return {**m.__dict__,**bound_memory,**flags,'f':f,'request':copy.deepcopy(req),'previous':copy.deepcopy(obj['input']),'current':{'project_files':copy.deepcopy(files)},'before_project_count':525}
def run_project(env):exec(projectcode,env);return env
run_project(project_env());passed('real_AST_project525_to527_helperonly_newpair_preconditions',actual_consumer=False)
for label,mutate in [
('empty_layers',lambda e:e['request'].__setitem__('layer_names',[])),('repeated_layers',lambda e:e['request'].__setitem__('layer_names',[layer,layer])),('foreign_layer',lambda e:e['request'].__setitem__('layer_names',['foreign'])),
('old_private_helper_substitution',lambda e:e['previous']['project_files'].__setitem__(m.PROJECT_DSH_CURRENT_HELPER,'7d7b221476a691fc6751f5d283f0e654eab810b7527b9e2841d152ea41964cb3')),
('changed_plugin',lambda e:e['current']['project_files'].__setitem__(next(n for n in files if n.startswith('plugins/friday_rework/')),'0'*64)),
('helper_unchanged',lambda e:e['current']['project_files'].__setitem__(m.PROJECT_DSH_CURRENT_HELPER,obj['input']['project_files'][m.PROJECT_DSH_CURRENT_HELPER])),
('foreign_project_target',lambda e:e['current']['project_files'].__setitem__('foreign.py','0'*64)),('missing_new_pair',lambda e:e['current']['project_files'].pop(patch_name)),
('unbound_manifest',lambda e:e.__setitem__('CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST','UNBOUND')),('inventory_pin_substitution',lambda e:e['request'].__setitem__('project_inventory_sha256','0'*64))]:
    e=project_env();mutate(e);rejected('project_'+label,lambda e=e:run_project(e))
assert len([n for n in files if n.startswith('plugins/friday_rework/')])==52
passed('real525_unchanged52plugin_inventory_reused')

# Exact AST native tuple/count statements, with a true new_file row included.
start=next(i for i,n in enumerate(edge_ast.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected_receipt')
end=next(i for i,n in enumerate(edge_ast.body[start:],start) if isinstance(n,ast.Expr) and ast.unparse(n.value).startswith("expected_receipt['layers'].append"))
nativecode=compile(ast.Module(body=edge_ast.body[start:end],type_ignores=[]),'<REAL-SOURCE-ONLY-NATIVE-PRECONDITIONS>','exec')
native_rows=[{'path':n,'before_sha256':pin[0],'sha256':pin[1],'bytes':pin[2],'new_file':pin[3],'mode':'100644'} for n,pin in pure_native.items()]
def native_env():return {**m.__dict__,**bound_memory,**flags,'f':f,'before_receipt':copy.deepcopy(obj['receipt']),'rows':copy.deepcopy(native_rows)}
e=native_env();exec(nativecode,e);assert len(e['expected_files'])==17894
passed('real_AST_exact_native_rows_and17893_plus_true_new_count',actual_consumer=False)
for label,mutation in [('before',lambda e:e['rows'][0].__setitem__('before_sha256','0'*64)),('after',lambda e:e['rows'][0].__setitem__('sha256','0'*64)),('bytes',lambda e:e['rows'][0].__setitem__('bytes',8)),('newfile',lambda e:e['rows'][0].__setitem__('new_file',True)),('foreign_scope',lambda e:e['rows'][0].__setitem__('path','foreign.py')),('missing_row',lambda e:e['rows'].pop()),('base_count',lambda e:e['before_receipt']['files'].pop(next(n for n in e['before_receipt']['files'] if n not in pure_native)))]:
    e=native_env();mutation(e);rejected('native_'+label,lambda e=e:exec(nativecode,e))

# Actual publication target construction for 1 and3 native rows proves no hard8.
pub=load('source223_pub_for_journal',OUT/'publication/friday_v3_layer_publication.py')
run_ast=next(n for n in ast.parse((OUT/'publication/friday_v3_layer_publication.py').read_text()).body if getattr(n,'name',None)=='run')
block=next(n for n in run_ast.body if isinstance(n,ast.If) and ast.unparse(n.test)=='guarded_current')
construction=compile(ast.Module(body=block.body[:-2],type_ignores=[]),'<REAL-SOURCE-JOURNAL-TARGETS>','exec')
for count in (1,3):
    request={**copy.deepcopy(req),'plugin_set':[],'plugin_additions':[],'staged_files':[]}
    for role in ('source_receipt','marker','stamp'):request[role]={'sha256':cap['roles'][{'source_receipt':'receipt'}.get(role,role)]['sha256']}
    receipt={'files':{n:{'sha256':'0'*64,'bytes':1} for n in ('n'+str(i) for i in range(count))}}
    scope={'final_state':receipt['files'],'receipt':receipt,'source':Path('/SOURCE-ONLY/home/hermes-agent'),'home':Path('/SOURCE-ONLY/home'),'request':request,'layer_names':(layer,),'previous_input':obj['input'],'require':pub.require}
    exec(construction,scope);assert len(scope['before_pins'])==count+6
    passed('real_publication_target_count_native_'+str(count)+'_plus6',target_count=len(scope['before_pins']),actual_H=False)

# New path dispatch uses unchanged journal; exercise alias + late known/foreign rollback
# only in finite disposable cache with nine actual selected local targets.
with tempfile.TemporaryDirectory(dir=OUT,prefix='selected-journal-controls-') as tmp:
    root=Path(tmp);home=root/'source-only-home';home.mkdir(mode=0o700);tx=root/'source-only-journal';tx.mkdir(mode=0o700)
    targets=[home/('target'+str(i)) for i in range(9)];beforepins={}
    for i,p in enumerate(targets):
        if i<6:p.write_bytes(('before'+str(i)).encode());p.chmod(0o600);beforepins[str(p)]={'sha256':sha(p.read_bytes())}
        else:beforepins[str(p)]=None
    j=pub._CurrentSourceV5Journal(tx,home,beforepins);j.preflight()
    for i,p in enumerate(targets):
        if i<6:j.record_existing(p,p.read_bytes())
        else:j.record_absent(p)
        after=('after'+str(i)).encode();pub.publish(p,after,0o600,_before_replace=j.prepare_publication(p,after,0o600))
    j.restore(targets)
    assert all(p.read_bytes()==('before'+str(i)).encode() for i,p in enumerate(targets[:6])) and all(not p.exists() for p in targets[6:])
    passed('selected9target_known_afterimages_and_absence_restore')
    alias=home/'alias';os.link(targets[0],alias)
    try:pub._CurrentSourceV5Journal(tx,home,{str(targets[0]):beforepins[str(targets[0])]}).preflight()
    except pub.Refused as exc:assert str(exc)=='transaction_v5_file_custody_changed';passed('journal_target_hardlink_alias_refused')
    else:raise AssertionError('journal hardlink accepted')
    alias.unlink()
    foreign=pub._CurrentSourceV5Journal(tx,home,{str(targets[0]):beforepins[str(targets[0])]});foreign.preflight();foreign.record_existing(targets[0],targets[0].read_bytes())
    pub.publish(targets[0],b'knownafter',0o600,_before_replace=foreign.prepare_publication(targets[0],b'knownafter',0o600));targets[0].write_bytes(b'foreignafter')
    try:foreign.restore([targets[0]])
    except pub.Refused as exc:assert str(exc)=='transaction_v5_restoration_foreign_state';passed('journal_foreign_afterimage_preserved_and_refused')
    else:raise AssertionError('journal foreign rollback accepted')
    assert targets[0].read_bytes()==b'foreignafter'

bind=load('source223_bind',OUT/'bind_frozen_source223.py')
# Only a disposable SOURCE stand; no canonical aliases, requests, installed metadata or binding output.
with tempfile.TemporaryDirectory(dir=OUT,prefix='source-bind-controls-') as tmp:
    tmp=Path(tmp);after_raw=b'changed source only\n';afterfile=tmp/'native-after';afterfile.write_bytes(after_raw)
    patch_raw=('diff --git a/'+native_name+' b/'+native_name+'\n--- a/'+native_name+'\n+++ b/'+native_name+'\n@@ -1 +1 @@\n-before\n+after\n').encode();patchfile=tmp/'layer.patch';patchfile.write_bytes(patch_raw)
    manifest={'base_commit':obj['receipt']['commit'],'patch':patch_name,'patch_sha256':sha(patch_raw),'prerequisites':{n:h for n,h in obj['input']['project_files'].items() if n.startswith('patches/hermes/') and n.endswith('.patch')},'files':[{'path':native_name,'before_sha256':before,'sha256':sha(after_raw),'bytes':len(after_raw),'mode':'100644','new_file':False}]}
    manifestfile=tmp/'manifest.json';manifestfile.write_bytes(enc(manifest))
    record={'schema':'friday.source223.frozen-bind.v1','layer_name':layer,'manifest':{'path':str(manifestfile),'sha256':sha(enc(manifest))},'patch':{'path':str(patchfile),'sha256':sha(patch_raw)},'afterimages':{native_name:{'path':str(afterfile),'sha256':sha(after_raw)}}}
    facts=bind.validate_record(record);assert facts['native'][native_name]==(before,sha(after_raw),len(after_raw),False)
    passed('bind_recipe_source_stand_validates_genuine222_before_and_exact_afterbytes',actual_binding_output_created=False)
    for label,mutate in [('foreign_layer',lambda r:r.__setitem__('layer_name','foreign')),('unbound_patch',lambda r:r['patch'].__setitem__('sha256','UNBOUND')),('missing_afterimage',lambda r:r.__setitem__('afterimages',{})),('foreign_afterimage',lambda r:r['afterimages'].__setitem__('foreign.py',r['afterimages'][native_name])),('afterbyte_pin',lambda r:r['afterimages'][native_name].__setitem__('sha256','0'*64))]:
        r=copy.deepcopy(record);mutate(r);rejected('bind_'+label,lambda r=r:bind.validate_record(r))
    for label,mutate in [('wrong_before',lambda a:a['files'][0].__setitem__('before_sha256','0'*64)),('wrong_newflag',lambda a:a['files'][0].__setitem__('new_file',True)),('wrong_bytes',lambda a:a['files'][0].__setitem__('bytes',1)),('repeated_path',lambda a:a['files'].append(copy.deepcopy(a['files'][0]))),('alias_path',lambda a:a['files'][0].__setitem__('path','a/../b')),('foreign_prerequisite',lambda a:a['prerequisites'].__setitem__('foreign.patch','0'*64))]:
        a=copy.deepcopy(manifest);mutate(a);manifestfile.write_bytes(enc(a));r=copy.deepcopy(record);r['manifest']['sha256']=sha(enc(a));rejected('bind_'+label,lambda r=r:bind.validate_record(r))
    manifestfile.write_bytes(enc(manifest))
    link=tmp/'source-link';link.symlink_to(afterfile)
    rejected('bind_source_symlink_refused',lambda:bind.source_bytes({'path':str(link),'sha256':sha(after_raw)}),'source_symlink_refused');link.unlink()
    realdir=tmp/'real-source-dir';realdir.mkdir();leaf=realdir/'leaf';leaf.write_bytes(b'cache only')
    linkdir=tmp/'source-dir-link';linkdir.symlink_to(realdir,target_is_directory=True)
    rejected('bind_ancestor_symlink_refused',lambda:bind.source_bytes({'path':str(linkdir/'leaf'),'sha256':sha(b'cache only')}),'source_symlink_refused');linkdir.unlink()
    for rel,pin in bind.TEMPLATE_PINS.items():
        b,_=bind.source_bytes({'path':str(OUT/rel),'sha256':pin});assert sha(b)==pin
    passed('bind_exact_four_draft_template_pins')
    for suffix,value,expected in [('MANIFEST','3'*64,'UNBOUND'),('PATCH','4'*64,'UNBOUND'),('NATIVE',pure_native,None)]:
        text=bind.replace_constant((OUT/'private/scripts/friday_ordinary_install.py').read_text(),'CURRENT_SOURCE_TWENTY_FIFTH_'+suffix,value,expected);compile(text,'<SOURCE-ONLY-BOUND-CONSTANT>','exec')
    passed('bind_finite_constant_substitution_compiles_without_execution')
    # A hardlinked afterimage must not be read as a second owned artifact.
    alias=tmp/'alias';os.link(afterfile,alias)
    rejected('bind_afterimage_hardlink_alias',lambda:bind.validate_record(record),'owned_regular_source_required');alias.unlink()

rejected('bind_dot_relative_path',lambda:bind.relative('.'),'unsafe_relative_path')

# Byte pins and AST equality make previous17 unchanged source controls reusable as stated.
oldcontrols=Path('/home/jericho/.cache/FRW-ASTRA-AFTER222-INSTALL-SUCCESSOR-SCOPE-20261115/SOURCE-CONTROLS.json')
assert sha(oldcontrols.read_bytes())=='3292b3f8c171d507467bfd8c7fda69ac6232860a4fc8465d69b0bb463f1e77eb'
passed('prior17_baseline_retained_unchanged222_bytes_and_journal_reused',sha256=sha(oldcontrols.read_bytes()),reason='Original222 exact8/layer bytes and unchanged generic journal evidence reused. Prior v25-ceiling/rawcontext/terminal24-denial controls describe old222 snapshot; changed v25/guarded dispatch and sealed historical222 are replaced by current draft controls, not carried over as new-candidate results.')
result={'schema':'frw.native223.v25.transition-source-controls.v1','state':'PASS_SOURCE_ONLY_UNBOUND_NO_ADMISSION','controls':rows,'count':len(rows),'all_IO_leaves':'explicitly inert except exact addressed protected cache source bytes and disposable source stand','canonical_H_opened':False,'actual_preflight':False,'native_delta_bound':False}
(OUT/'SOURCE-CONTROLS.json').write_bytes(enc(result));print(json.dumps({'state':result['state'],'count':len(rows),'sha256':sha(enc(result))},sort_keys=True))
