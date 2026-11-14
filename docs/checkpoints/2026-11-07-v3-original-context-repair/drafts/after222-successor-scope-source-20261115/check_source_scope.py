#!/usr/bin/env python3
"""Finite SOURCE controls; genuine cached222 bytes, no canonical H dereference."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import os
import tempfile

OUT = Path(__file__).resolve().parent
REPO = Path('/home/jericho/jericho/Friday_rework')
PUBDIR = REPO/'docs/checkpoints/2026-11-07-v3-original-context-repair/drafts/native222-final-source-bind-20261114/publication'
PRIVATE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE222-ACTUAL-CALLER-GATE-20261114/project')
PUBLIC = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE222-ROOT-ACTUAL221-ORIGIN-CAPTURE-20261114/public-project525')
CAPTURE = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE223-ACTUAL222-PREDECESSOR-CAPTURE-20261115/ACTUAL222-ROOT-CANONICAL-CAPTURE.json')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def enc(value): return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

rows=[]
def passed(name,**facts): rows.append({'control':name,'state':'PASS',**facts})
def refused(name,reason,call):
    try: call()
    except pub.Refused as exc:
        assert str(exc)==reason,(name,str(exc),reason)
        passed(name,reason=reason)
    else: raise AssertionError(name+' unexpectedly accepted')

capture_raw=CAPTURE.read_bytes()
assert sha(capture_raw)=='32b80537a4e8c51246b21830b80b3fb48d8e3d6ffdc600006e660d9f7debca25'
capture=json.loads(capture_raw)
objects={}
for role,ref in capture['roles'].items():
    # cache_path is the only leaf opened. canonical_path remains opaque data.
    path=Path(ref['cache_path'])
    assert path.is_relative_to(CAPTURE.parent/'actual222')
    raw=path.read_bytes()
    assert sha(raw)==ref['sha256'] and len(raw)==ref['bytes']
    objects[role]=json.loads(raw)
passed('genuine_cached_exact8_hashes',roles=sorted(objects),canonical_paths_opened=0)
request=objects['request'];value=objects['input'];receipt=objects['receipt']
assert request['current_source_successor']['schema']=='friday.current-source-native-successor.v24'
assert len(value['project_files'])==525 and len(receipt['layers'])==222 and len(receipt['files'])==17893
assert request['current_input']['sha256']==capture['roles']['input']['sha256']
assert objects['marker']['input_sha256']==capture['roles']['input']['sha256']
assert objects['committed']['source_receipt_sha256']==capture['roles']['receipt']['sha256']
passed('genuine222_current_join',counts=capture['actual_installed_counts'])
canonical_ref={'path':capture['roles']['request']['canonical_path'],'sha256':capture['roles']['request']['sha256']}
assert Path(canonical_ref['path']).parent.name=='ordinary-source-update-v45-'+canonical_ref['sha256'][:16]
for name in ['intent','committed']:
    body=objects[name]
    assert body['request_reference']==canonical_ref and body['request_sha256']==canonical_ref['sha256']
    assert body['current_source_successor']==request['current_source_successor']
    assert body['current_input']==request['current_input'] and body['previous_input']==request['previous_input']
    assert body['gateway_started'] is False and body['workers_enabled'] is False
assert objects['intent']['state']=='SOURCE_UPDATE_INTENT'
assert objects['committed']['state']=='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED'
assert objects['stamp']['fridaySource']=={'baseTree':receipt['base_tree'],'layers':receipt['layers']}
assert objects['marker']['source_receipt_sha256']==capture['roles']['receipt']['sha256']
assert objects['marker']['ordinary_gateway']['source_receipt_sha256']==capture['roles']['receipt']['sha256']
assert objects['marker']['ordinary_gateway']['operator_entry']['input']==request['current_input']
passed('genuine222_retained_canonical_request_journal_marker_stamp_join',canonical_paths_opened=0)

pub=load_module('after222_scope_publication',PUBDIR/'friday_v3_layer_publication.py')
builder=load_module('after222_scope_builder',PUBDIR/'build-layer-publication-request.py')
builder._CONSUMER=pub
args=builder.parse_args([])
assert args.layer_names==pub.HISTORICAL_LAYER_NAMES and len(args.layer_names)==4
assert args.layer is None
passed('builder_default_remains_exact_four',layer_names=list(args.layer_names))
assert pub.resolve_layer_names({'schema':pub.SCHEMA})==pub.HISTORICAL_LAYER_NAMES
for name,names,reason in [
    ('explicit_absent',None,'transaction_layer_names_required'),
    ('explicit_empty',[],'transaction_layer_names_empty'),
    ('explicit_repeated',[pub.LAYER_NAMES[-1]]*2,'transaction_layer_names_repeated')]:
    probe={'schema':pub.SCHEMA_EXPLICIT}
    if names is not None:probe['layer_names']=names
    refused(name,reason,lambda p=probe:pub.resolve_layer_names(p))
raw=pub.current_source_request_bytes(request,capture['roles']['request']['cache_path'],capture['roles']['request']['sha256'])
assert sha(raw)==capture['roles']['request']['sha256']
passed('genuine222_raw_request_context_positive')
# Negative unsupported-schema probe in memory only; never a manufactured predecessor.
probe=dict(request);probe['current_source_successor']=dict(request['current_source_successor'])
probe['current_source_successor']['schema']='friday.current-source-native-successor.v25'
refused('future_v25_raw_context_closed','transaction_current_source_context_required',
    lambda:pub.current_source_request_bytes(probe,'UNBOUND-NO-FILE','UNBOUND'))

builder_ast=ast.parse((PUBDIR/'build-layer-publication-request.py').read_text())
supported=[n for n in ast.walk(builder_ast) if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='supported' for t in n.targets)]
assert len(supported)==1
mapping=ast.literal_eval(supported[0].value)
assert request['current_source_successor']['schema'] not in mapping
assert mapping['friday.current-source-native-successor.v23']=='friday.current-source-native-successor.v24'
passed('builder_genuine222_is_unsupported_next_predecessor',maximum_target='v24',next_required='v25')
publication_ast=ast.parse((PUBDIR/'friday_v3_layer_publication.py').read_text())
guarded=[n for n in ast.walk(publication_ast) if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='guarded_current' for t in n.targets)]
assert len(guarded)==1
guarded_schemas={n.value for n in ast.walk(guarded[0].value) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
assert 'friday.current-source-native-successor.v24' in guarded_schemas
assert 'friday.current-source-native-successor.v25' not in guarded_schemas
passed('future_v25_must_join_guarded_current_dispatch',existing_maximum='v24')

layers=pub.read_layers(PRIVATE,receipt,'OPAQUE-NOT-READ',value['project_files'],request['layer_names'])
assert len(layers)==1 and layers[0]['name']=='ods-xlsx-native-visibility-compare-after-source221'
passed('genuine222_manifest_patch_bytes',native_rows=len(layers[0]['files']))

helpers=[PRIVATE/'scripts/friday_ordinary_install.py',PUBLIC/'scripts/friday_ordinary_install.py']
parsed=[ast.parse(p.read_text()) for p in helpers]
methods=[{n.name:n for n in x.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))} for x in parsed]
region=[name for name,n in methods[0].items() if 2981<=n.lineno<=5787]
assert len(region)==56
assert all(ast.dump(methods[0][name],include_attributes=False)==ast.dump(methods[1][name],include_attributes=False) for name in region)
passed('private_public_current_chain_ast_equal',function_class_count=len(region),helper_sha256=[sha(p.read_bytes()) for p in helpers])
edge=methods[0]['_current_native_source_edge_checked']
historical_denial=any(isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not)
    and ast.unparse(n.operand)=='twenty_fourth and historical_marker is not None' for n in ast.walk(edge))
assert historical_denial
passed('twenty_fourth_historical_requires_new_sealed_join',existing_explicit_denial=True)

# Exercise the unchanged generic publication journal only in our disposable cache.
# These are local file-custody controls, not a predecessor, future request or admission.
with tempfile.TemporaryDirectory(prefix='journal-controls-',dir=OUT) as tmp:
    root=Path(tmp);home=root/'local-files';home.mkdir(mode=0o700)
    tx=root/'local-journal';tx.mkdir(mode=0o700)
    target=home/'existing';target.write_bytes(b'local-before');target.chmod(0o600)
    added=home/'absent'
    journal=pub._CurrentSourceV5Journal(tx,home,{str(target):{'sha256':sha(b'local-before')},str(added):None})
    journal.preflight();journal.record_existing(target,b'local-before');journal.record_absent(added)
    pub.publish(target,b'local-after',0o600,_before_replace=journal.prepare_publication(target,b'local-after',0o600))
    pub.publish(added,b'local-new',0o600,_before_replace=journal.prepare_publication(added,b'local-new',0o600))
    journal.restore([target,added])
    assert target.read_bytes()==b'local-before' and not added.exists()
    passed('generic_journal_exact_restore_existing_and_absent')
    refused('generic_journal_wrong_preimage','transaction_v5_authenticated_preimage_changed:'+str(target),
        lambda:pub._CurrentSourceV5Journal(tx,home,{str(target):{'sha256':'0'*64}}).preflight())
    second=pub._CurrentSourceV5Journal(tx,home,{str(target):{'sha256':sha(b'local-before')}})
    second.preflight();second.record_existing(target,b'local-before')
    pub.publish(target,b'local-own-after',0o600,_before_replace=second.prepare_publication(target,b'local-own-after',0o600))
    target.write_bytes(b'local-foreign-after')
    refused('generic_journal_foreign_afterimage','transaction_v5_restoration_foreign_state',lambda:second.restore([target]))
    assert target.read_bytes()==b'local-foreign-after'

result={'schema':'frw.after222.static-source-controls.v1','state':'PASS_SOURCE_ONLY_NO_FUTURE_ADMISSION',
    'controls':rows,'count':len(rows),'canonical_H_opened':False,'future_layer_bound':False,
    'services_models_Office_DB_locks_publication':False}
(OUT/'SOURCE-CONTROLS.json').write_bytes(enc(result))
os.chmod(OUT/'SOURCE-CONTROLS.json',0o600)
print(json.dumps({'state':result['state'],'controls':len(rows),'result':str(OUT/'SOURCE-CONTROLS.json'),'sha256':sha(enc(result))},sort_keys=True))
