#!/usr/bin/env python3
"""Finite v25 source seam controls; synthetic envelopes are never admission evidence."""
import argparse
import ast
from contextlib import redirect_stderr
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'publication'
ORIGINAL = Path('/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair')
NEW = 'ordinary-f04-owned-ingress-stop-terminal-after-source222'
PREFIX = 'friday.current-source-native-successor.v'
rows = []
def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
def passed(name, **facts): rows.append({'control': name, 'state': 'PASS', **facts})
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def refused(name, reason, call):
    try: call()
    except pub.Refused as exc:
        assert str(exc) == reason, (name, str(exc), reason)
        passed(name, reason=reason)
    else: raise AssertionError(name+' unexpectedly accepted')

def assignments(tree, name):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]

original_pins = {
    'build-layer-publication-request.py': '0e418cf06e32b845a40067c3c2325942ac070845943c36e4b9851ea75d76fafa',
    'friday_v3_layer_publication.py': '76a754cc79319a8e0af2cdf0692c17f2ac5a4de86d3498f8cd03ce3687e6f89d',
}
for name, expected in original_pins.items():
    assert sha((ORIGINAL/name).read_bytes()) == expected
    compile((OUT/name).read_bytes(), str(OUT/name), 'exec')
passed('exact_original_hashes_and_in_memory_compile', original_sha256=original_pins)
pub = load('v25_source_publication', OUT/'friday_v3_layer_publication.py')
builder = load('v25_source_builder', OUT/'build-layer-publication-request.py')
builder._CONSUMER = pub
assert pub.CURRENT_SOURCE_TWENTY_FIFTH_LAYER == builder.CURRENT_SOURCE_TWENTY_FIFTH_LAYER == NEW
assert pub.CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST_SHA256 == pub.CURRENT_SOURCE_TWENTY_FIFTH_PATCH_SHA256 == 'UNBOUND'
original_pub = ast.parse((ORIGINAL/'friday_v3_layer_publication.py').read_text())
pub_ast = ast.parse((OUT/'friday_v3_layer_publication.py').read_text())
original_builder = ast.parse((ORIGINAL/'build-layer-publication-request.py').read_text())
builder_ast = ast.parse((OUT/'build-layer-publication-request.py').read_text())
for old in original_pub.body:
    if isinstance(old, (ast.FunctionDef, ast.ClassDef)) and old.name not in ('run', 'current_source_request_bytes'):
        new = next(n for n in pub_ast.body if isinstance(n, type(old)) and n.name == old.name)
        assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False), old.name
old_names = ast.literal_eval(assignments(original_pub, 'LAYER_NAMES')[0].value)
assert pub.LAYER_NAMES == old_names+(NEW,) and len(set(pub.LAYER_NAMES)) == len(pub.LAYER_NAMES)
passed('single_new_registration_and_unchanged_other_publication_functions_classes')

with tempfile.TemporaryDirectory(prefix='builder-publication-controls-', dir=ROOT) as temporary:
    tmp = Path(temporary)
    parse_paths = ['--home',str(tmp/'never-installed-home'),'--candidate-project',str(tmp/'candidate'),
                   '--native-unit',str(tmp/'native-unit')]
    args = builder.parse_args(parse_paths)
    assert args.layer is None and args.layer_names == pub.HISTORICAL_LAYER_NAMES and len(args.layer_names) == 4
    assert pub.resolve_layer_names({'schema':pub.SCHEMA}) == args.layer_names
    assert pub.require_twenty_fifth_source_binding(args.layer_names) is None
    passed('builder_and_legacy_default_remain_historical_four')
    for version in range(1,25):
        pub.require_twenty_fifth_source_binding((), {'schema':PREFIX+str(version)})
    passed('early_guard_preserves_all_previous_context_versions', versions=list(range(1,25)))
    args = builder.parse_args(parse_paths+['--layer',NEW])
    assert args.layer_names == (NEW,)
    passed('cli_accepts_exact_new_selected_identity_only_as_explicit_layer')
    for name, suffix in [('unknown_future_layer',['--layer','unregistered-after-source223']),
                         ('empty_layer',['--layer','']), ('repeated_layer',['--layer',NEW,'--layer',NEW])]:
        with redirect_stderr(io.StringIO()):
            try: builder.parse_args(parse_paths+suffix)
            except SystemExit as exc: assert exc.code == 2
            else: raise AssertionError(name+' unexpectedly accepted')
        passed('cli_refuses_'+name)
    for name, names, reason in [('empty', [],'transaction_layer_names_empty'),
                                ('malformed', NEW,'transaction_layer_names_malformed'),
                                ('malformed_member',[1],'transaction_layer_names_malformed'),
                                ('repeated',[NEW,NEW],'transaction_layer_names_repeated')]:
        refused('composition_'+name,reason,
                lambda names=names: pub.resolve_layer_names({'schema':pub.SCHEMA_EXPLICIT,'layer_names':names}))
    refused('composition_absent','transaction_layer_names_required',
            lambda: pub.resolve_layer_names({'schema':pub.SCHEMA_EXPLICIT}))
    refused('composition_foreign_registered_set','transaction_layer_names_unknown',
            lambda: pub.check_project_inventory({'schema':pub.SCHEMA_EXPLICIT,'layer_names':['foreign-layer']},{},{}))

    # Execute only the bounded mapping and its in-memory requirements, never build_request.
    build_function = next(n for n in builder_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'build_request')
    mapping_node = assignments(builder_ast, 'supported')[0]
    old_map = ast.literal_eval(assignments(original_builder,'supported')[0].value)
    mapping = ast.literal_eval(mapping_node.value)
    assert mapping == {**old_map, PREFIX+'24':PREFIX+'25'} and len(mapping) == 24
    calls = [n for n in ast.walk(build_function) if isinstance(n, ast.Expr)
             and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
             and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'consumer'
             and n.value.func.attr == 'require' and any(isinstance(x,ast.Name) and x.id == 'previous_schema' for x in ast.walk(n))]
    assert len(calls) == 24
    seam = compile(ast.fix_missing_locations(ast.Module(body=[mapping_node,*calls],type_ignores=[])), '<bounded-builder-seam>', 'exec')
    def bounded(schema, names):
        env = {'consumer':pub,'previous_schema':schema,'args':SimpleNamespace(layer_names=names),
               **{key:value for key,value in vars(builder).items() if key.startswith('CURRENT_SOURCE_')}}
        exec(seam,env)
        return env['supported'][schema]
    assert bounded(PREFIX+'24',(NEW,)) == PREFIX+'25'
    passed('bounded_v24_to_v25_mapping_seam_exact_singleton', actual_builder_positive=False)
    for name,schema,names,reason in [
        ('future',PREFIX+'25',(NEW,),'transaction_current_source_supported_predecessor_required'),
        ('malformed',None,(NEW,),'transaction_current_source_supported_predecessor_required'),
        ('malformed_list',[],(NEW,),'transaction_current_source_supported_predecessor_required'),
        ('malformed_dict',{},(NEW,),'transaction_current_source_supported_predecessor_required'),
        ('empty',PREFIX+'24',(),'transaction_current_source_exact_twenty_fifth_layer_required'),
        ('repeated',PREFIX+'24',(NEW,NEW),'transaction_current_source_exact_twenty_fifth_layer_required'),
        ('foreign',PREFIX+'24',(pub.HISTORICAL_LAYER_NAMES[0],),'transaction_current_source_exact_twenty_fifth_layer_required'),
        ('composed',PREFIX+'24',(NEW,pub.HISTORICAL_LAYER_NAMES[0]),'transaction_current_source_exact_twenty_fifth_layer_required')]:
        refused('bounded_mapping_refuses_'+name,reason,lambda s=schema,n=names:bounded(s,n))

    # Missing args.home proves the barrier precedes every installed-home read.
    refused('actual_builder_unbound_before_home_access','transaction_current_source_twenty_fifth_binding_unbound',
            lambda:builder.build_request(SimpleNamespace(layer_names=(NEW,))))
    saved_reader = pub.current_source_request_bytes
    def no_request_reader(*args,**kwargs): raise AssertionError('unbound crossed request reader')
    pub.current_source_request_bytes = no_request_reader
    try:
        for name,request in [('selected',{'layer_names':[NEW]}),
                             ('context_only',{'current_source_successor':{'schema':PREFIX+'25'}})]:
            refused('actual_run_unbound_before_request_and_home_'+name,'transaction_current_source_twenty_fifth_binding_unbound',
                    lambda r=request:pub.run(r,None,None))
    finally: pub.current_source_request_bytes = saved_reader

    # Structural raw-envelope tests only. The opaque references are never opened.
    context = {'schema':PREFIX+'25',
               'root_project_update':{'path':'OPAQUE-UNOPENED-ROOT','sha256':sha(b'inert root')},
               'previous_native_update':{'path':'OPAQUE-UNOPENED-PREVIOUS','sha256':sha(b'inert previous')}}
    request = {'schema':pub.SCHEMA_EXPLICIT,'layer_names':[NEW],'current_source_successor':context}
    path = tmp/'inert-envelope.json';raw=encoded(request);path.write_bytes(raw);path.chmod(0o600)
    assert pub.current_source_request_bytes(request,path,sha(raw)) == raw
    passed('v25_typed_raw_envelope_structural_admission_only', product_preflight=False, references_opened=False)
    for name,bad_context,reason in [
        ('future',{**context,'schema':PREFIX+'26'},'transaction_current_source_context_required'),
        ('malformed_schema',{**context,'schema':25},'transaction_current_source_context_required'),
        ('extra_field',{**context,'foreign':1},'transaction_current_source_context_required'),
        ('missing_predecessor',{k:v for k,v in context.items() if k!='previous_native_update'},'transaction_current_source_context_required'),
        ('malformed_reference',{**context,'previous_native_update':{'path':'opaque','sha256':'UNBOUND'}},'transaction_current_source_root_reference_required')]:
        refused('typed_raw_refuses_'+name,reason,
                lambda c=bad_context:pub.current_source_request_bytes({**request,'current_source_successor':c},None,None))
    refused('v25_raw_hash_substitution','transaction_current_source_raw_request_changed',
            lambda:pub.current_source_request_bytes(request,path,'0'*64))
    path.write_bytes(b'{"a":1,"a":2}');path.chmod(0o600)
    refused('v25_duplicate_json','transaction_current_source_duplicate_json_key',
            lambda:pub.current_source_request_bytes(request,path,sha(path.read_bytes())))

    guarded_node = assignments(pub_ast,'guarded_current')[0]
    guarded_expr = compile(ast.Expression(guarded_node.value), '<guarded-current-seam>', 'eval')
    for version in range(1,27):
        result=eval(guarded_expr,{'current_context':True,'request':{'current_source_successor':{'schema':PREFIX+str(version)}}})
        assert result == (5<=version<=25)
    assert eval(guarded_expr,{'current_context':False,'request':{}}) is False
    passed('v25_separate_guarded_current_dispatch_preserves_bounded_v5_through_v25')

    # Execute the actual selected-target dispatch block over disposable local files.
    run_node = next(n for n in pub_ast.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    guarded_block = [n for n in run_node.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='guarded_current']
    assert len(guarded_block)==1
    home=tmp/'local-cas';home.mkdir(mode=0o700)
    for name in ('hermes-agent','scripts','patches','patches/hermes'): (home/name).mkdir(mode=0o700)
    def put(name,raw):
        p=home/name;p.write_bytes(raw);p.chmod(0o600);return {'sha256':sha(raw),'bytes':len(raw)}
    existing=put('hermes-agent/existing.py',b'local native before')
    helper=put('scripts/friday_ordinary_install.py',b'local helper before')
    refs={}
    for key,name in [('source_receipt','hermes-agent.source.json'),('marker','FRIDAY-INSTALL.json'),('stamp','hermes-agent/install-stamp.json')]:
        refs[key]=put(name,('local '+key).encode())
    dispatch_request={**refs,'project_file_updates':['scripts/friday_ordinary_install.py'],
                      'layer_manifest_updates':['patches/hermes/'+NEW+'-manifest.json'],
                      'plugin_set':[],'plugin_additions':[],'staged_files':[]}
    env={**vars(pub),'guarded_current':True,'final_state':{'existing.py':'unread-after','added.py':'unread-after'},
         'receipt':{'files':{'existing.py':existing}},'source':home/'hermes-agent','home':home,
         'request':dispatch_request,'layer_names':(NEW,),
         'previous_input':{'project_files':{'scripts/friday_ordinary_install.py':helper['sha256']}},
         'current_transaction':tmp/'uncreated-transaction'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=guarded_block,type_ignores=[])),'<selected-cas-dispatch>','exec'),env)
    journal=env['guarded_journal']
    assert isinstance(journal,pub._CurrentSourceV5Journal)
    expected={str(home/name) for name in ['hermes-agent/existing.py','hermes-agent/added.py',
             'scripts/friday_ordinary_install.py','patches/hermes/'+NEW+'.patch',
             'patches/hermes/'+NEW+'-manifest.json','hermes-agent.source.json','FRIDAY-INSTALL.json','hermes-agent/install-stamp.json']}
    assert set(journal.before_pins)==expected and set(journal.before_states)==expected
    assert not (tmp/'uncreated-transaction').exists()
    passed('actual_guarded_dispatch_uses_cas_journal_selected_targets_only', target_count=len(expected), consuming_mkdir=False, fixture_admission=False)
    (home/'scripts/friday_ordinary_install.py').write_bytes(b'foreign changed helper')
    refused('guarded_dispatch_refuses_changed_selected_preimage',
            'transaction_v5_authenticated_preimage_changed:'+str(home/'scripts/friday_ordinary_install.py'),
            journal.preflight)

result={'schema':'frw.native223.builder-publication-v25.source-result.v1',
        'assignment':'NATIVE223-BUILDER-PUBLICATION-V25-SOURCE-20261115#1',
        'state':'PASS_FINITE_SOURCE_DRAFT_UNBOUND_NO_PRODUCT_PREFLIGHT',
        'accepted_at_moscow':'2026-11-15T01:18:47+03:00',
        'completed_at_moscow':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
        'elapsed_seconds':(datetime.now(ZoneInfo('Europe/Moscow'))-datetime.fromisoformat('2026-11-15T01:18:47+03:00')).total_seconds(),
        'files':[{'path':str(OUT/name),'sha256':sha((OUT/name).read_bytes()),'bytes':(OUT/name).stat().st_size} for name in original_pins],
        'original_sha256':original_pins,'checks':rows,'count':len(rows),
        'binding_constants':['CURRENT_SOURCE_TWENTY_FIFTH_MANIFEST_SHA256','CURRENT_SOURCE_TWENTY_FIFTH_PATCH_SHA256'],
        'binding_guard_interface':'require_twenty_fifth_source_binding(layer_names=(), context=None)',
        'limits':['Manifest/patch bytes and native tuples remain UNBOUND; no actual builder positive or default product consumer run.',
                  'Synthetic raw envelopes and extracted in-memory mapping/CAS seams establish only local parser/dispatch behavior, never predecessor or admission authority.',
                  'No canonical current/H path was followed; no locks, services, models, Git, installation or live effects.',
                  'Final bind must replace both publication source hash constants with exact frozen bytes together with helper pins; ordinary helper retains native tuple and genuine222 proof authority.'],
        'temporary_materials_cleaned':True}
(ROOT/'builder-publication-result.json').write_bytes(encoded(result));(ROOT/'builder-publication-result.json').chmod(0o600)
print(json.dumps({'state':result['state'],'checks':len(rows),'result':str(ROOT/'builder-publication-result.json')},sort_keys=True))
