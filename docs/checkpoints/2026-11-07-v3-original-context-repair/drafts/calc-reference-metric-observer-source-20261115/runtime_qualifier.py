"""Source-only caller for Root's separately admitted, already-loaded Calc model.

No UNO import, process/clock/network/file IO, load/store/render/close or admission.
Root supplies two independently trusted by-value records and their SHA256 digests.
A digest binds supplied bytes; it does not create runtime facts or authority.
"""
import hashlib
import json
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

SOURCE_SHA256 = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
SOURCE_BYTES = 16538
VERSION = '26.2.5.2'
COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
C_UTF8_STOCK_LOCALE_LIFECYCLE = 'DESKTOP_PREPARE_LOCALE_COMPLETED_NO_LATER_LANGUAGE_MUTATION'
ROLES = {'calc_document','calc_xlsx_filter','vcl','toolkit','sal','font_config_view'}
LOAD_POLICY = dict(read_only=True, hidden=True, macros='NEVER_EXECUTE', links='NO_UPDATE',
                   interaction='ABORT_ONLY', network='OS_NAMESPACE_DENY',
                   profile='FRESH_PRIVATE_NO_RESTORE', store_render_draw_conversion=False)
LOAD_ARGS = dict(Hidden=True, ReadOnly=True, MacroExecutionMode=0, UpdateDocMode=0)

CLEAN_FONT_DEFAULTS = dict(StyleName='', Width=0, CharacterWidth=0.0, Pitch=0,
    Slant='NONE', Underline=0, Strikeout=0, Orientation=0.0, Kerning=True, WordLineMode=False, Type=0)

class Unsupported(ValueError):
    """Local refusal; Root still owns unconditional terminal process cleanup."""


def need(condition, reason):
    if not condition:
        raise Unsupported(reason)


def digest(s):
    return type(s) is str and len(s) == 64 and all(c in '0123456789abcdef' for c in s)


def canonical(v):
    return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha(v):
    return hashlib.sha256(canonical(v)).hexdigest()


def decode_root_record(raw, expected_file_sha256):
    """Bridge exact Root file bytes to the by-value canonical digest API.

    Returns (value, canonical_digest). Caller provides bytes without this module
    reading any path; exact on-disk pretty JSON hash is NOT the canonical digest.
    """
    need(type(raw) is bytes and len(raw)<=262144 and digest(expected_file_sha256)
         and hashlib.sha256(raw).hexdigest()==expected_file_sha256, 'Root_file_bytes_changed')
    def unique(pairs):
        out={}
        for k,v in pairs:
            need(k not in out, 'duplicate_Root_JSON_key')
            out[k]=v
        return out
    def invalid_constant(value):
        raise Unsupported('nonfinite_Root_JSON_number')
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=invalid_constant)
    need(type(value) is dict, 'Root_record_object_required')
    return value, sha(value)


def shape(v, keys, why):
    need(type(v) is dict and set(v) == set(keys), why)


def trusted(v, pin):
    need(digest(pin) and sha(v) == pin, 'externally_trusted_record_changed_or_UNBOUND')


def local_path(url):
    need(type(url) is str and len(url)<=4096 and '\x00' not in url, 'private_file_URL_UNBOUND')
    u=urlsplit(url); p=PurePosixPath(unquote(u.path))
    need(u.scheme == 'file' and not u.netloc and not u.query and not u.fragment
         and p.is_absolute() and '..' not in p.parts
         and '\x00' not in str(p) and '/.runtime/' not in str(p) and p.as_posix() == unquote(u.path), 'private_exact_cache_URL_required')
    return p


def cache_path(url):
    p=local_path(url)
    need(p.as_posix().startswith('/home/jericho/.cache/'), 'private_cache_working_source_required')
    return p


def ref(v):
    shape(v, ('path','sha256'), 'exact_external_proof_ref_required')
    need(type(v['path']) is str and v['path'].startswith('/home/jericho/.cache/')
         and '..' not in PurePosixPath(v['path']).parts and digest(v['sha256']), 'external_proof_UNBOUND')


def validate_preload_inputs(v, trusted_sha256):
    """Pure safe PRE-LOAD shape/identity check; does not assert a loaded process."""
    trusted(v,trusted_sha256)
    shape(v, ('schema','operation_id','source','working_copy','producer','expected_components',
              'load_policy','private_profile_url','mounted_work_directory_url'), 'exact_preload_schema_required')
    need(v['schema']=='frw.Root.calc-reference-observer-preload.v1', 'preload_schema_required')
    op=v['operation_id']
    need(type(op) is str and 1<=len(op)<=128 and all(c.isalnum() or c in '-_.' for c in op), 'operation_identity_UNBOUND')
    need(v['source']=={'sha256':SOURCE_SHA256,'bytes':SOURCE_BYTES}, 'exact_original_source_required')
    w=v['working_copy']; shape(w, ('url','sha256_before','bytes','uid','mode','nlink'), 'exact_working_copy_record_required')
    need(w['sha256_before']==SOURCE_SHA256 and w['bytes']==SOURCE_BYTES and type(w['uid']) is int
         and w['uid']==1000 and w['mode']=='0600' and type(w['nlink']) is int and w['nlink']==1,
         'protected_exact_private_copy_required')
    wp=cache_path(w['url']); mount=cache_path(v['mounted_work_directory_url']); profile=local_path(v['private_profile_url'])
    need(str(profile).startswith('/home/jericho/.cache/') or
         PurePosixPath('/tmp/friday-metric-work') in profile.parents, 'Root_private_namespace_profile_required')
    need(wp!=mount and mount in wp.parents and wp!=profile and profile not in wp.parents
         and mount not in profile.parents and profile not in mount.parents,
         'separate_private_profile_and_narrow_ro_work_mount_required')
    p=v['producer']; shape(p,('version','source_commit','publisher_binding_ref','publisher_acceptance_ref'), 'exact_source_basis_required')
    need(p['version']==VERSION and p['source_commit']==COMMIT, 'reviewed_stock_producer_required')
    ref(p['publisher_binding_ref']); ref(p['publisher_acceptance_ref'])
    need(p['publisher_binding_ref']['sha256']=='a685fd7ebcf6c3481cc452b9e5c9e323ce741969df805c5c22470e89308479a5'
         and p['publisher_acceptance_ref']['sha256']=='0b82767f6f31127ddc7ec3449dd023f2ac28eb4af6ad34fd2f21786c3e9ae1ae',
         'accepted_publisher_source_basis_changed')
    need(type(v['expected_components']) is dict and set(v['expected_components'])==ROLES
         and all(digest(h) for h in v['expected_components'].values()), 'all_expected_component_pins_required')
    need(v['load_policy']==LOAD_POLICY and all(type(v['load_policy'][k]) is type(x) for k,x in LOAD_POLICY.items()),
         'no_output_private_load_policy_required')
    return v


def validate_loaded_facts(v, pin, pre):
    """Root-only actual process/map/load/native-proof metadata, independently bound.

    This code cannot inspect /proc, native Font internals or launch policy. Root
    must construct this record from its owned runner observations, never a fixture.
    """
    trusted(v,pin)
    shape(v,('schema','operation_id','process','loaded_components','load_request','lifecycle','native_transport','evidence_ref','startup_locale_environment'),
          'exact_loaded_Root_facts_required')
    need(v['schema']=='frw.Root.calc-reference-observer-loaded.v1' and v['operation_id']==pre['operation_id'], 'same_owned_operation_required')
    p=v['process']; shape(p,('pid','start_ticks','executable_sha256','launch_api'), 'actual_process_identity_required')
    need(type(p['pid']) is int and p['pid']>0 and type(p['start_ticks']) is int and p['start_ticks']>0
         and digest(p['executable_sha256']) and p['launch_api']=='EXECVE_STANDALONE_SOFFICE_BIN',
         'owned_standalone_process_UNBOUND')
    need(type(v['loaded_components']) is dict and set(v['loaded_components'])==ROLES, 'actual_loaded_component_roles_required')
    for role, item in v['loaded_components'].items():
        shape(item,('path','sha256'), 'actual_loaded_component_identity_required')
        need(type(item['path']) is str and item['path'].startswith('/') and '..' not in PurePosixPath(item['path']).parts
             and item['sha256']==pre['expected_components'][role], 'loaded_component_changed:'+role)
    r=v['load_request']; shape(r,('url','scalar_arguments','interaction_handler','interaction_requests'), 'actual_load_request_required')
    need(r['url']==pre['working_copy']['url'] and r['scalar_arguments']==LOAD_ARGS
         and all(type(r['scalar_arguments'][k]) is type(x) for k,x in LOAD_ARGS.items())
         and type(r['interaction_requests']) is int and r['interaction_requests']==0, 'actual_safe_load_request_UNBOUND')
    h=r['interaction_handler']; shape(h,('argument_name','kind','instance_token','source_ref'), 'supplied_interaction_handler_required')
    need(h['argument_name']=='InteractionHandler' and h['kind']=='ABORT_ONLY'
         and type(h['instance_token']) is str and 1<=len(h['instance_token'])<=128, 'actual_abort_handler_instance_UNBOUND')
    ref(h['source_ref'])
    env=v['startup_locale_environment']
    need(env is None or (type(env) is dict and set(env)=={'LC_ALL'}
         and all(type(x) is str and len(x)<=256 for x in env.values())),
         'actual_startup_locale_environment_schema_required')
    c_utf8 = env == {'LC_ALL':'C.UTF-8'}
    lifecycle_keys=('exclusive_owner_operation_id','profile_origin','application_settings','reference_operations')
    if c_utf8:
        lifecycle_keys += ('stock_locale_initialization',)
    l=v['lifecycle']; shape(l,lifecycle_keys, 'actual_lifecycle_basis_required')
    if c_utf8:
        need(l['stock_locale_initialization']==C_UTF8_STOCK_LOCALE_LIFECYCLE,
             'C_UTF8_stock_startup_language_lifecycle_UNBOUND')
    need(l['exclusive_owner_operation_id']==pre['operation_id'] and l['profile_origin']=='CREATED_EMPTY_FOR_THIS_OPERATION'
         and l['application_settings']=='STARTUP_CONFIG_UNMODIFIED'
         and l['reference_operations']==['LOAD_CALC_WORKING_COPY'], 'fresh_exclusive_unmodified_lifecycle_UNBOUND')
    t=v['native_transport']
    shape(t,('mode','native_min','native_max','proof_ref','scope','proof_disposition','observer_plan_ref'), 'native_transport_mode_required')
    if t['mode']=='SIGNED32_PROVED':
        ref(t['proof_ref'])
        need(type(t['native_min']) is int and type(t['native_max']) is int
             and -(2**31)<=t['native_min']<=t['native_max']<2**31
             and t['scope']=='QUALIFIED_SINGLE_DIGIT_GETTEXTWIDTH_SIGNED32'
             and t['proof_disposition']=='SAME_STATE_SIGNED32_BOUND_PROVED'
             and t['proof_ref']['sha256']!='432c72c11d7b8c6bff7e1023dd5769c7aef07988576322009fc6fb75084904ae'
             and t['observer_plan_ref'] is None, 'native_signed32_exactness_UNBOUND')
    elif t['mode']=='RAW32_POSTQUERY_NATIVE_JOIN':
        need(t['native_min'] is None and t['native_max'] is None and t['proof_ref'] is None
             and t['scope']=='RAW32_ONLY_TEN_SINGLE_DIGITS'
             and t['proof_disposition']=='NO_PREQUERY_NATIVE_BOUND', 'raw_query_must_not_pretend_native_proof')
        ref(t['observer_plan_ref'])  # reviewed SOURCE plan, not future result/pre-PASS
    else:
        raise Unsupported('explicit_native_transport_mode_UNBOUND')
    ref(v['evidence_ref'])
    return v


def model_observations(doc, pre):
    need(doc is not None and doc.supportsService('com.sun.star.sheet.SpreadsheetDocument'), 'real_Calc_model_required')
    need(doc.getURL()==pre['working_copy']['url'] and doc.isReadonly() is True, 'wrong_or_writable_model')
    need(type(doc.isModified()) is bool and doc.isModified() is False, 'loaded_source_must_be_unmodified')
    # XModel.getArgs may omit load-only arguments. Absence is recorded, never
    # treated as a fresh load-policy proof; Root's independently bound request is
    # mandatory. If retained, relevant values must agree exactly (including type).
    args={}
    for p in doc.getArgs():
        if p.Name in LOAD_ARGS:
            need(p.Name not in args, 'duplicate_model_load_argument')
            args[p.Name]=p.Value
    for k,x in args.items():
        need(type(x) is type(LOAD_ARGS[k]) and x==LOAD_ARGS[k], 'model_load_argument_conflict:'+k)
    info=doc.getPropertySetInfo()
    need(info is not None and info.hasPropertyByName('ReferenceDevice'), 'ReferenceDevice_optional_property_unsupported')
    prop=info.getPropertyByName('ReferenceDevice')
    typename=getattr(prop.Type,'typeName',None)
    need(prop.Name=='ReferenceDevice' and type(prop.Attributes) is int and prop.Attributes & 16
         and typename=='com.sun.star.awt.XDevice', 'ReferenceDevice_type_or_readonly_contract_changed')
    device=doc.getPropertyValue('ReferenceDevice')
    need(device is not None and all(callable(getattr(device,n,None)) for n in ('createGraphics','getFont','getInfo')),
         'ReferenceDevice_XDevice_capability_missing')
    d=device.getInfo()
    # Descriptive observation only: never infer MapMode/physical twips or device
    # identity from pixel density. Same pointer is selected by exact Calc getter
    # source, standalone mode and TextWysiwyg=false, not equal-looking values.
    names=('Width','Height','PixelPerMeterX','PixelPerMeterY','BitsPerPixel')
    di={k:getattr(d,k) for k in names}
    need(all(type(di[k]) in (int,float) for k in names), 'DeviceInfo_contract_changed')
    canonical(di)  # rejects NaN/Inf; no metric range inferred
    return device, dict(model_url=doc.getURL(), readonly=True, modified=False,
                        retained_load_arguments=args, missing_load_arguments=sorted(set(LOAD_ARGS)-set(args)),
                        reference_property=dict(name=prop.Name,type_name=typename,attributes=prop.Attributes),
                        device_info=di, MapMode='NOT_PUBLICLY_OBSERVABLE_NO_UNIT_INFERENCE')


def qualify_and_observe(doc, component_context, pre, pre_sha256, loaded, loaded_sha256, *,
                        resolve_font_recipe, measurement_leaf, property_value_factory,
                        descriptor_factory=None, before_digit=None, after_digit=None):
    """Future Root call on real objects. SOURCE tests inject explicitly inert leaves.

    External records authenticate no other authority/clock. In-memory observation
    hashes bind real API results only; they are not invented external proof refs.
    Any exception is a refusal; outer Root finally closes/reaps without saving.
    """
    validate_preload_inputs(pre,pre_sha256)
    validate_loaded_facts(loaded,loaded_sha256,pre)
    paired_callbacks=callable(before_digit) and callable(after_digit)
    need(paired_callbacks or (before_digit is None and after_digit is None), 'trusted_phase_callback_pair_required')
    need(loaded['native_transport']['mode']!='RAW32_POSTQUERY_NATIVE_JOIN' or paired_callbacks,
         'raw32_query_requires_Root_phase_callbacks')
    device, model_obs=model_observations(doc,pre)
    resolver_inputs=dict(property_value_factory=property_value_factory,
                         startup_locale_environment=loaded['startup_locale_environment'])
    if loaded['startup_locale_environment'] == {'LC_ALL':'C.UTF-8'}:
        resolver_inputs['stock_startup_locale_lifecycle']=loaded['lifecycle']['stock_locale_initialization']
    font=resolve_font_recipe(doc,component_context,**resolver_inputs)
    need(type(font) is dict and {'recipe','source_nominal_font','observations'}<=set(font), 'real_font_resolver_contract_required')
    # Source derivation from live config plus Root's fresh unmodified startup
    # lifecycle is conditional, not a direct native Application settings getter.
    need(font['default_script']['value']=='LATIN', 'application_default_script_unsupported')
    need(font['use_printer_metrics'] is False, 'virtual_reference_profile_required')
    observations=dict(model=model_obs,font=font['observations'],source_font=font['source_nominal_font'],export_recipe=font['recipe'])
    obs_sha=sha(observations)
    e={k:dict(basis='LIVE_MODEL_CONFIG_OBSERVATIONS',sha256=obs_sha) for k in
       ('source_profile','default_script','ms_name_transform','charset_roundtrip','reference_state')}
    e.update({k:dict(basis='ROOT_EXTERNAL_RECORD',sha256=loaded_sha256) for k in
             ('producer_instance','private_load_policy','native_width_transport')})
    if loaded['startup_locale_environment'] == {'LC_ALL':'C.UTF-8'}:
        # Config observations alone do not establish native Application state.
        # C.UTF-8 additionally uses the independently bound stock-startup fact.
        e['default_script']=dict(basis='ROOT_EXTERNAL_RECORD',sha256=loaded_sha256)
    t=loaded['native_transport']
    ctx=dict(schema='frw.Root.calc-reference-metric-qualified-context.v2',
             source_sha256=SOURCE_SHA256,source_bytes=SOURCE_BYTES,
             working_copy_url=pre['working_copy']['url'],working_copy_sha256_before=SOURCE_SHA256,working_copy_bytes=SOURCE_BYTES,
             producer_version=VERSION,reviewed_source_commit=COMMIT,
             components={r:dict(expected_sha256=pre['expected_components'][r],observed_sha256=loaded['loaded_components'][r]['sha256']) for r in ROLES},
             standalone_non_LOK=True,same_reference_state=True,no_concurrent_device_user=True,
             native_width_transport=dict(mode=t['mode'],native_min=t['native_min'],native_max=t['native_max'],
                                         proof_sha256=t['proof_ref']['sha256'] if t['proof_ref'] else None),
             default_script='LATIN',source_style_name='Default',source_font=font['source_nominal_font'],
             export_descriptor=dict(CLEAN_FONT_DEFAULTS,**font['recipe']),load_policy=LOAD_POLICY.copy(),evidence=e)
    candidate=measurement_leaf(doc,ctx,sha(ctx),descriptor_factory=descriptor_factory,
                               before_digit=before_digit,after_digit=after_digit)
    need(candidate.get('runtime_attested') is False and candidate.get('actual_case_accepted') is False,
         'measurement_leaf_must_not_release_acceptance')
    # Repeat public model/config observations after leaf restoration. A changed
    # setting invalidates the candidate, even if a width looked plausible.
    _, after_model=model_observations(doc,pre)
    after_font=resolve_font_recipe(doc,component_context,**resolver_inputs)
    need(after_model==model_obs and after_font==font, 'model_or_config_changed_during_metric_no_release')
    return dict(schema='frw.calc.reference-qualifier.candidate.v1',status='ROOT_POSTCLOSE_ATTESTATION_REQUIRED',
                pre_record_sha256=pre_sha256,loaded_record_sha256=loaded_sha256,
                observations=observations,observations_sha256=obs_sha,leaf_context=ctx,leaf_context_sha256=sha(ctx),
                measurement=candidate,actual_M=None,runtime_attested=False,actual_case_accepted=False,
                historical_applicability='UNBOUND_SEPARATE_ROOT_ASSESSMENT',
                remaining=(['Root exact same-operation native64/raw32 postquery join; no trusted M before representability/scope validation']
                           if t['mode']=='RAW32_POSTQUERY_NATIVE_JOIN' else [])
                          + ['Root closes/disposes without save and reaps owned process','Root verifies original/working-copy hashes and terminal no-output/cleanup facts'],
                physical_fidelity='UNASSESSED')


if __name__=='__main__':
    print(json.dumps(dict(status='SOURCE_ONLY_NO_EXECUTION_ENTRYPOINT',actual_M=None,runtime_grant=False)))
