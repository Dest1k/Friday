'Pure source manifest assembly for this exact223 overlay, never admission.'
import copy
import hashlib
import json
from pathlib import PurePosixPath

SCHEMA = 'frw.root223.coherent-after-actual222-source-pins.v1'

def require(ok, why):
    if not ok:
        raise ValueError(why)


def validate_source_pins(value, *, source_bytes, frame):
    require(value['schema'] == SCHEMA and value['frame'] == frame,
            'exact223_source_frame_counts_required')
    require(value['runtime_grant'] is False and value['current_admission'] is False and
            value['root_source_accepted'] is False and value['review_required'] is True,
            'source_manifest_never_current_root_grant')
    require(set(source_bytes) == set(value['source_refs']) | set(value['historical_refs']),
            'complete_explicit_source_bytes_required')
    for path,digest in {**value['source_refs'],**value['historical_refs']}.items():
        p = PurePosixPath(path)
        require(p.is_absolute() and '..' not in p.parts and str(p) == path and
                path.startswith('/home/jericho/.cache/') and '/.runtime/' not in path and
                path != frame+'/SOURCE-PINS.json', 'cache_source_only_no_runtime_or_self_hash')
        require(hashlib.sha256(source_bytes[path]).hexdigest() == digest, 'source_pin_changed:'+path)
    ref = value['source_spec_ref']
    require(set(ref) == {'path','sha256'} and value['source_refs'].get(ref['path']) == ref['sha256'],
            'typed_selected_source_spec_role_required')
    spec = json.loads(source_bytes[ref['path']])
    require(spec['schema'] == 'frw.f04223.pair-spec.v1' and spec['source_only'] is True and
            spec['current_authority'] is False and spec['execution_grant'] is False and
            spec['installed223'] is False and spec['selected_targets'] == len(spec['native_files'])+6 and
            spec['successor_schema'] == 'friday.current-source-native-successor.v25',
            'exact_inert223_pair_spec_required')
    counts=spec['counts']; expected=dict(before_layers=222,after_layers=223,before_project=525,after_project=527,base=17730,native=counts['after_native'],plugins=52,native_targets=len(spec['native_files']),native_additions=counts['added'],selected_CAS=len(spec['native_files'])+6,untouched_native_rows=counts['retained'])
    require(value['counts']==expected,'derived_exact223_frame_counts_required')
    required = ['run_native223_once.py','resume_native223_services.py','root223_data.py','root223_metadata.py',
                'root223_projection.py','ROOT223-DATA-BINDINGS.json','bind_current_inputs223.py',
                'actor_static_inputs223.py','core223-first-actual-root.py','boundary_contract.py','cutoff_contract.py',
                'recovery_scope.py','frame_source.py','source_pins_producer.py','SOURCE-SPEC223.json',
                'publication/friday_v3_layer_publication.py','publication/build-layer-publication-request.py',
                'ACTUAL222-EIGHT-ROW-BINDING.json','ROOT-223-CONSUMED-HISTORY-TEMPLATE.json','ROOT-FUTURE-COMMANDS.json',
                'ROOT-223-FRESH-ADMISSION-TEMPLATE.json','ROOT-223-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json']
    require(all(frame+'/'+p in value['source_refs'] for p in required), 'complete223_frame_source_closure_required')
    require(value['source_refs'][frame+'/publication/friday_v3_layer_publication.py'] ==
            'UNBOUND_NATIVE223_CONSUMER_SHA', 'exact_accepted_real_consumer_required')
    require(value['source_refs'].get('/home/jericho/.cache/FRW-ASTRA-V3-CORE-FILE-INTEGRATION-20261111/presentation-bank-direct/EXPECTED-BANK-MANIFEST.json') ==
            'cf6db77f2448acfeb77f0a7fa7081e5cc26acd9cd08e7aee039d62b6ef1ac776', 'exact_prelaunch_bank_manifest_source_pin_required')
    return copy.deepcopy(value)


def assemble(*, frame, source_bytes, historical_bytes, source_spec_ref, product_source_commit):
    require(set(source_bytes).isdisjoint(historical_bytes), 'distinct_source_roles_required')
    pins = dict(schema=SCHEMA,frame=frame,counts=dict(before_layers=222,after_layers=223,before_project=525,after_project=527,base=17730,native=json.loads(source_bytes[source_spec_ref['path']])['counts']['after_native'],plugins=52,native_targets=len(json.loads(source_bytes[source_spec_ref['path']])['native_files']),native_additions=json.loads(source_bytes[source_spec_ref['path']])['counts']['added'],selected_CAS=len(json.loads(source_bytes[source_spec_ref['path']])['native_files'])+6,untouched_native_rows=json.loads(source_bytes[source_spec_ref['path']])['counts']['retained']),
                source_refs={p:hashlib.sha256(b).hexdigest()for p,b in source_bytes.items()},
                historical_refs={p:hashlib.sha256(b).hexdigest()for p,b in historical_bytes.items()},
                source_spec_ref=source_spec_ref,runtime_grant=False,current_admission=False,
                root_source_accepted=False,review_required=True,source_only=True,
                execution_commit=product_source_commit,execution_provenance_mode='published-remote',
                execution_public_main_sha=product_source_commit,public_main_sha=product_source_commit,
                product_source_commit=product_source_commit)
    return validate_source_pins(pins,source_bytes={**source_bytes,**historical_bytes},frame=frame)
