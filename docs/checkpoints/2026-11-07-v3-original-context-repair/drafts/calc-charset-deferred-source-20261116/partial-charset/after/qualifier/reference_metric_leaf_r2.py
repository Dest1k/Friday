"""Source-only R2 future Root leaf (copied from frozen99 R1); import does not import UNO or start Office.

Root must independently qualify the runtime/process/component/source/device
context before calling this on a real model. Hash equality here binds supplied
bytes, not authority. This module neither issues admission nor connects/loads,
exports, stores, renders, draws, closes or launches anything.
"""
import hashlib
import json
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

SOURCE_SHA256 = 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58'
SOURCE_BYTES = 16538
VERSION = '26.2.5.2'
SOURCE_COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
COMPONENT_ROLES = {'calc_document', 'calc_xlsx_filter', 'vcl', 'toolkit', 'sal', 'font_config_view'}
EVIDENCE_ROLES = {'source_profile', 'producer_instance', 'default_script',
                  'ms_name_transform', 'charset_roundtrip', 'reference_state',
                  'private_load_policy', 'native_width_transport'}
DEFAULTS = dict(StyleName='', Width=0, CharacterWidth=0.0, Pitch=0,
                Slant='NONE', Underline=0, Strikeout=0, Orientation=0.0,
                Kerning=True, WordLineMode=False, Type=0)


class Unbound(ValueError):
    pass


class RestorationUnconfirmed(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Unbound(reason)


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def qualification_sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_root_context(value, expected_qualification_sha256):
    """Validate an externally trusted Root context; do not authenticate it here."""
    require(type(value) is dict and digest(expected_qualification_sha256), 'Root_runtime_qualification_UNBOUND')
    require(qualification_sha256(value) == expected_qualification_sha256, 'Root_context_bytes_changed')
    required = {'schema', 'source_sha256', 'source_bytes', 'working_copy_url',
                'working_copy_sha256_before', 'working_copy_bytes', 'producer_version',
                'reviewed_source_commit', 'components', 'standalone_non_LOK',
                'same_reference_state', 'no_concurrent_device_user', 'native_width_transport', 'default_script',
                'source_style_name', 'source_font', 'export_descriptor', 'load_policy', 'evidence'}
    require(set(value) == required and value['schema'] == 'frw.Root.calc-reference-metric-qualified-context.v2',
            'exact_Root_runtime_context_required')
    require(value['source_sha256'] == value['working_copy_sha256_before'] == SOURCE_SHA256
            and value['source_bytes'] == value['working_copy_bytes'] == SOURCE_BYTES,
            'exact_source_and_private_copy_required')
    uri = urlsplit(value['working_copy_url'])
    path = PurePosixPath(unquote(uri.path))
    require(uri.scheme == 'file' and not uri.netloc and not uri.query and not uri.fragment
            and path.is_absolute() and '..' not in path.parts
            and str(path).startswith('/home/jericho/.cache/') and '/.runtime/' not in str(path),
            'private_cache_working_copy_URL_required')
    require(value['producer_version'] == VERSION and value['reviewed_source_commit'] == SOURCE_COMMIT,
            'exact_producer_component_version_required')
    require(type(value['components']) is dict and set(value['components']) == COMPONENT_ROLES,
            'exact_component_roles_required')
    for role, pair in value['components'].items():
        require(type(pair) is dict and set(pair) == {'expected_sha256', 'observed_sha256'}
                and digest(pair['expected_sha256']) and pair['expected_sha256'] == pair['observed_sha256'],
                'producer_component_UNBOUND_or_changed:'+role)
    require(value['standalone_non_LOK'] is True and value['same_reference_state'] is True
            and value['no_concurrent_device_user'] is True
            and value['default_script'] == 'LATIN',
            'same_standalone_export_reference_state_UNBOUND')
    transport = value['native_width_transport']
    require(type(transport) is dict and set(transport) == {'mode', 'native_min', 'native_max', 'proof_sha256'},
            'exact_native_transport_mode_required')
    require(transport['mode'] in ('SIGNED32_PROVED', 'RAW32_POSTQUERY_NATIVE_JOIN'),
            'explicit_native_transport_mode_UNBOUND')
    if transport['mode'] == 'SIGNED32_PROVED':
        require(digest(transport['proof_sha256'])
                and type(transport['native_min']) is int and type(transport['native_max']) is int
                and -(2**31) <= transport['native_min'] <= transport['native_max'] < 2**31,
                'independent_signed32_native_transport_proof_UNBOUND')
    else:
        require(transport['native_min'] is None and transport['native_max'] is None
                and transport['proof_sha256'] is None,
                'raw32_mode_must_not_fabricate_future_native_bound_or_proof')
    require(value['load_policy'] == dict(read_only=True, hidden=True,
            macros='NEVER_EXECUTE', links='NO_UPDATE', interaction='ABORT_ONLY',
            network='OS_NAMESPACE_DENY', profile='FRESH_PRIVATE_NO_RESTORE',
            store_render_draw_conversion=False), 'qualified_private_no_effect_load_policy_required')
    require(value['source_style_name'] == 'Default', 'recognized_Default_style_required')
    # Preserve the observed UNO short: -1 represents RTL Unicode 65535.
    # Native encoding reconstruction belongs to the resolver derivation; the
    # later actual style re-read must compare the same observed short value.
    nominal = value['source_font']
    require(type(nominal) is dict and set(nominal) == {'Name', 'HeightPt', 'Family', 'CharSet', 'Weight', 'Posture'}
            and nominal['Name'] == 'Calibri' and nominal['HeightPt'] == 11
            and nominal['Family'] == 5 and nominal['Weight'] == 100 and nominal['Posture'] == 'NONE'
            and type(nominal['CharSet']) is int
            and (nominal['CharSet'] == -1 or 0 <= nominal['CharSet'] < 65536),
            'qualified_source_Normal_font_required')
    recipe = value['export_descriptor']
    require(type(recipe) is dict and set(recipe) == set(DEFAULTS) | {'Name', 'Height', 'Family', 'CharSet', 'Weight'},
            'complete_clean_export_font_recipe_UNBOUND')
    require(type(recipe['Name']) is str and 0 < len(recipe['Name']) <= 128
            and not any(ord(c) < 32 or c in ';,\\' for c in recipe['Name']) and recipe['Height'] == 220 and recipe['Family'] == 5
            and recipe['Weight'] == 100 and type(recipe['CharSet']) is int and 0 <= recipe['CharSet'] < 65536,
            'qualified_export_font_transform_UNBOUND')
    require(all(type(recipe[k]) is type(v) and recipe[k] == v for k, v in DEFAULTS.items()),
            'clean_Font_defaults_must_match_pinned_implementation')
    require(type(value['evidence']) is dict and set(value['evidence']) == EVIDENCE_ROLES,
            'all_Root_qualification_evidence_required')
    for role, proof in value['evidence'].items():
        require(type(proof) is dict and set(proof) == {'basis', 'sha256'}
                and proof['basis'] in ('ROOT_EXTERNAL_RECORD', 'LIVE_MODEL_CONFIG_OBSERVATIONS')
                and digest(proof['sha256']), 'qualified_evidence_UNBOUND:'+role)
    return value


def _enum_name(value):
    return value if type(value) is str else getattr(value, 'value', None)


def make_pyuno_descriptor(recipe):
    """Future Root runtime only. Tests inject an inert factory instead."""
    import uno
    descriptor = uno.createUnoStruct('com.sun.star.awt.FontDescriptor')
    for key, value in recipe.items():
        setattr(descriptor, key, uno.Enum('com.sun.star.awt.FontSlant', value) if key == 'Slant' else value)
    return descriptor


def observe_reference_metric(doc, context, expected_qualification_sha256, *, descriptor_factory=None,
                             before_digit=None, after_digit=None):
    """Query ten raw widths on the exact reference device; no observation PASS.

    This is version-specific public-API composition, including temporary native
    Font/cache mutation. The caller owns load/policy/clock/process custody and
    post-close source hashes/cleanup. No result authenticates those conditions.
    The exported scalar has no independently proven physical twip/pixel unit.
    RAW32 mode requires trusted Root before/after callbacks. They own only their
    declared phase/response metadata; this module performs no file/debugger IO.
    before_digit(index,digit) must atomically publish exact nonce/METRIC/index/digit
    and hold it through the synchronous return. after_digit(index,digit,raw32)
    may record the response, but never writes CLOSED before full restore/docclose.
    Any callback error still passes through complete native Font finally restore.
    """
    bound = validate_root_context(context, expected_qualification_sha256)
    paired_callbacks = callable(before_digit) and callable(after_digit)
    require(paired_callbacks or (before_digit is None and after_digit is None),
            'trusted_Root_phase_callbacks_must_be_supplied_as_a_pair')
    require(bound['native_width_transport']['mode'] != 'RAW32_POSTQUERY_NATIVE_JOIN' or paired_callbacks,
            'raw32_native_trace_query_requires_trusted_Root_per_digit_phase_callbacks')
    require(doc is not None and doc.supportsService('com.sun.star.sheet.SpreadsheetDocument'),
            'exact_Calc_model_required')
    require(doc.getURL() == bound['working_copy_url'] and doc.isReadonly() is True,
            'bound_private_readonly_model_required')
    modified_before = doc.isModified()
    styles = doc.getStyleFamilies().getByName('CellStyles')
    style = styles.getByName(bound['source_style_name'])
    actual = {key: style.getPropertyValue(prop) for key, prop in
              [('Name','CharFontName'), ('HeightPt','CharHeight'), ('Family','CharFontFamily'),
               ('CharSet','CharFontCharSet'), ('Weight','CharWeight'), ('Posture','CharPosture')]}
    actual['Posture'] = _enum_name(actual['Posture'])
    require(actual == bound['source_font'], 'source_Default_font_changed')
    device = doc.getPropertyValue('ReferenceDevice')
    require(device is not None and all(callable(getattr(device, name, None))
            for name in ('createGraphics', 'getFont')), 'exact_reference_device_capability_required')
    descriptor = (descriptor_factory or make_pyuno_descriptor)(bound['export_descriptor'])
    require(all((_enum_name(getattr(descriptor,k)) if k == 'Slant' else getattr(descriptor,k)) == v
                for k,v in bound['export_descriptor'].items()), 'UNO_descriptor_factory_changed_recipe')
    restore = device.createGraphics()  # captures the complete original native Font
    require(restore is not None, 'complete_font_restore_capability_required')
    widths = []
    try:
        seed = device.createGraphics()
        require(seed is not None, 'clean_font_seed_capability_required')
        seed.selectFont(descriptor)  # pinned implementation starts from fresh vcl::Font()
        seed.getFontMetric()        # installs that Font; does not draw
        font = device.getFont(descriptor)
        require(font is not None, 'bound_reference_font_required')
        for index, digit in enumerate('0123456789'):
            if before_digit is not None:
                before_digit(index, digit)  # Root atomically publishes METRIC phase before synchronous call
            width = font.getStringWidth(digit)  # exact single-digit GetTextWidth call
            require(type(width) is int and -(2**31) <= width < 2**31,
                    'raw32_integral_UNO_transport_required')
            if after_digit is not None:
                after_digit(index, digit, width)  # only after successful synchronous return; no CLOSED here
            if bound['native_width_transport']['mode'] == 'SIGNED32_PROVED':
                require(0 < width < 65536, 'positive_integral_digit_metric_required_fallback_not_supported')
                require(bound['native_width_transport']['native_min'] <= width <= bound['native_width_transport']['native_max'],
                        'measured_width_conflicts_with_independent_native_bound')
            widths.append(width)
    finally:
        try:
            restore.getFontMetric()  # reinstalls complete old native Font, not descriptor approximation
        except Exception as exc:
            raise RestorationUnconfirmed('original_reference_Font_restore_UNCONFIRMED_no_metric_release') from exc
    require(doc.isModified() == modified_before, 'metric_observation_changed_model_modified_flag')
    raw_mode = bound['native_width_transport']['mode'] == 'RAW32_POSTQUERY_NATIVE_JOIN'
    return dict(schema='frw.calc.reference-device.raw-metric-candidate.v2',
                status='RAW32_UNTRUSTED_NATIVE_POSTJOIN_REQUIRED' if raw_mode else 'RAW_METRIC_CANDIDATE_REQUIRES_ROOT_RUNTIME_ATTESTATION',
                qualification_sha256=expected_qualification_sha256,
                digit_widths=widths, M_candidate=None if raw_mode else max(widths),
                native_transport_mode=bound['native_width_transport']['mode'],
                native64_postquery_join='UNBOUND_ROOT' if raw_mode else 'PREQUALIFIED_SIGNED32_BOUND',
                metric_unit='UNTRUSTED_RAW32_UNO_SIGNED_INTEGER' if raw_mode else 'RAW_CURRENT_REFERENCE_DEVICE_LOGICAL_SCALAR',
                consumer_interpretation='NO_CONSUMER_INTERPRETATION_UNTIL_EXACT_NATIVE64_RAW32_JOIN' if raw_mode else 'Exporter feeds this numeric scalar into convertTwipToMm100; physical twips are not proved.',
                phase_callbacks_used=paired_callbacks,
                native_font_restore_completed=True, exporter_fallback_used='UNASSESSED_UNTIL_NATIVE_JOIN' if raw_mode else False,
                native_transport_proof_sha256=bound['native_width_transport']['proof_sha256'],
                output_scope_guard='For trusted candidate: native64/raw32 exact, each 0<w<65536; raw32-only query imposes no semantic positivity/range claim',
                historical_applicability='UNBOUND_SEPARATE_ROOT_ASSESSMENT',
                source_modified_flag_changed=False, source_file_unchanged='UNBOUND_ROOT_POSTCLOSE_HASH',
                process_cleanup='UNBOUND_ROOT', runtime_attested=False,
                actual_case_accepted=False, physical_fidelity='UNASSESSED')


if __name__ == '__main__':
    print(json.dumps(dict(status='SOURCE_ONLY_NOT_EXECUTION_READY', actual_M=None,
                         reason='Root runtime qualification and real private Calc model are UNBOUND'), indent=2))
