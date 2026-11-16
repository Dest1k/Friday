"""Narrow SOURCE-ONLY recipe resolver for stock LibreOffice 26.2.5.2.

Importing this file imports no UNO binding and performs no service/config/model
operation. Root may call it only inside its separately admitted finite lifecycle,
after verifying the real loaded Calc model, process/component/source identity,
and fresh standalone/no-LOK/exclusive unchanged settings and config conditions.

The application script below is derived from the pinned native startup path; it
is NOT a direct observation of Application::GetSettings().GetLanguageTag(). The
public APIs used here expose the locale config and Calc's TextWysiwyg flag, not
the native AllSettings object. Empty locale requires an externally bound exact
process-start LC_ALL branch; unsupported branches refuse. This module never
issues runtime or historical acceptance.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
import re

SOURCE_COMMIT = "cd7284b4cbbfeb507e630c1aac019f4157393acb"
VERSION = "26.2.5.2"
C_UTF8_STOCK_LOCALE_LIFECYCLE = "DESKTOP_PREPARE_LOCALE_COMPLETED_NO_LATER_LANGUAGE_MUTATION"
DEFAULT_PROVIDER = "/singletons/com.sun.star.configuration.theDefaultProvider"
CONFIG_SERVICE = "com.sun.star.configuration.ConfigurationAccess"
SETUP_NODE = "/org.openoffice.Setup/L10N"
SUBSTITUTION_NODE = "/org.openoffice.VCL/FontSubstitutions"
GLOBAL_SETTINGS_SERVICE = "com.sun.star.sheet.GlobalSheetSettings"
EXTERNAL_STARTUP_CONDITIONS = (
    "exact_pinned_stock_process_components_and_source",
    "fresh_standalone_non_LOK_non_fuzzing_application",
    "exclusive_process_no_AllSettings_or_locale_mutation_since_startup",
    "same_configuration_view_unchanged_since_process_startup",
)
PROPERTY_TYPES = {
    "CharFontName": "string", "CharHeight": "float",
    "CharFontFamily": "short", "CharFontCharSet": "short",
    "CharWeight": "float", "CharPosture": "com.sun.star.awt.FontSlant",
}
# Complete named-encoding profile derived from the pinned native tables:
# UNO sal_Int16 -> rtl_TextEncoding uint16 -> best Windows byte -> RTL import.
# Only named native encodings with build-independent canonical export RTL 0/1
# are admitted. Missing conversion tables use the native Windows 1 fallback;
# this does not claim those encodings support a text converter. Reserved/gap/
# user-range values and valid encodings exporting another RTL charset refuse.
# The observed API short stays unchanged in source_nominal_font/observations.
CHARSET_ROUNDTRIPS = {
    -2: (1, 0),
    -1: (1, 0),
    0: (1, 0),
    1: (0, 1),
    3: (0, 1),
    4: (0, 1),
    5: (0, 1),
    6: (0, 1),
    7: (0, 1),
    8: (0, 1),
    11: (0, 1),
    12: (0, 1),
    14: (0, 1),
    21: (0, 1),
    22: (0, 1),
    41: (1, 0),
    45: (1, 0),
    46: (1, 0),
    48: (1, 0),
    49: (1, 0),
    50: (1, 0),
    51: (0, 1),
    53: (1, 0),
    75: (0, 1),
    76: (0, 1),
    89: (1, 0),
    90: (0, 1),
    91: (0, 1),
    92: (0, 1),
    94: (0, 1),
    95: (0, 1),
    96: (0, 1),
}
_SAFE_NAME = re.compile(r"[A-Za-z0-9 ._()+-]{1,128}\Z")
# These canonical forms cannot alias bare English except exact 'en'. This narrow
# check avoids pretending to reimplement native LanguageTag canonicalization for
# arbitrary configuration set names. Unsupported locale names explicitly refuse.
_CONFIG_LOCALE = re.compile(r"[a-z]{2}(?:-[A-Z]{2})?\Z")


class FontResolutionRefused(ValueError):
    """A stable reason code; exception messages never contain user/config text."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise FontResolutionRefused(code)


def observation_digest(observations):
    """Digest exact JSON observations only: not config identity or authority."""
    data = json.dumps(observations, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _checked_property(obj, name, typename):
    info = obj.getPropertySetInfo()
    _require(info is not None, "property_metadata_missing")
    prop = info.getPropertyByName(name)
    _require(prop.Type.typeName == typename, "property_schema_mismatch")
    return obj.getPropertyValue(name)


def _config_access(provider, nodepath, factory):
    argument = factory("nodepath", nodepath)
    _require(argument.Name == "nodepath" and argument.Value == nodepath,
             "property_value_factory_changed_nodepath")
    node = provider.createInstanceWithArguments(CONFIG_SERVICE, (argument,))
    _require(node is not None, "readonly_configuration_access_missing")
    return node


def _names(node):
    names = tuple(node.getElementNames())
    _require(len(names) <= 20000 and all(type(x) is str for x in names),
             "configuration_name_sequence_unsupported")
    _require(len(set(names)) == len(names), "duplicate_configuration_names")
    return names


def _utf16_key(value):
    return value.encode("utf-16-be", "surrogatepass")


def _resolve_ms_name(source_name, substitutions):
    locale_names = _names(substitutions)
    _require(all(_CONFIG_LOCALE.fullmatch(x) for x in locale_names),
             "configuration_locale_canonicalization_unsupported")
    font_names = ()
    matched_key = None
    raw_ms = None
    candidate = None
    # fontcfg.cxx's FontSubstConfiguration starts at LanguageTag('en'); native
    # getFallbackStrings(true) for this language-only tag returns only ['en'].
    if "en" in locale_names:
        english = substitutions.getByName("en")
        font_names = _names(english)
        ordered = sorted(font_names, key=_utf16_key)
        pos = bisect.bisect_left([_utf16_key(x) for x in ordered], _utf16_key("calibri"))
        if pos < len(ordered):
            found = ordered[pos]
            # Exact native lower_bound + prefix test; not a longest-prefix lookup.
            if len(found.encode("utf-16-le", "surrogatepass")) <= 14 and "calibri".startswith(found):
                matched_key = found
                raw_ms = english.getByName(found).getByName("SubstFontsMS")
                _require(raw_ms is None or (type(raw_ms) is str and len(raw_ms) <= 65536),
                         "MS_substitution_property_schema_unsupported")
                # Native fillSubstVector ignores a void Any: no MS candidates.
                # Preserve that observed None below; do not turn it into a
                # fabricated configuration string or use the general SubstFonts.
                ms_tokens = "" if raw_ms is None else raw_ms
                # Native fillSubstVector splits only semicolon, ignores empty
                # tokens and does not trim. Source name is exactly 'Calibri'.
                for token in ms_tokens.split(";"):
                    if token and token != source_name:
                        candidate = token
                        break
    resolved = candidate if candidate is not None else source_name
    _require(_SAFE_NAME.fullmatch(resolved) is not None and resolved == resolved.strip(),
             "resolved_export_font_name_unsupported")
    return resolved, {
        "nodepath": SUBSTITUTION_NODE,
        "observed_locale_names": sorted(locale_names, key=_utf16_key),
        "native_lookup_locale": "en",
        "observed_english_font_keys": sorted(font_names, key=_utf16_key),
        "source_search_key": "calibri", "native_matched_key": matched_key,
        "observed_SubstFontsMS": raw_ms, "resolved_export_name": resolved,
        "algorithm": "native_fixed_en_UTF16_lower_bound_then_prefix_first_nonempty_nonidentical_MS_token",
    }


def resolve_font_recipe(model, component_context, *, property_value_factory,
                        startup_locale_environment=None, stock_startup_locale_lifecycle=None):
    """Read actual APIs/config and return the five-field clean-font recipe.

    property_value_factory(name, value) must create a real UNO beans.PropertyValue
    in future Root execution. Pure tests supply an explicitly inert stand-in.
    Does not import UNO, connect/load/store/export/render, modify config, select
    fonts, measure text, close the model, or authenticate external Root facts.

    Current supported source profile: builtin Default/Standard Calibri 11pt,
    Swiss, normal, no posture; exact UNO charset short in the pinned named
    encoding table whose build-independent native roundtrip exports RTL 0 or 1;
    explicit en-US locale config,
    or empty locale with Root-supplied exact LC_ALL en_US.UTF-8 or C.UTF-8
    actual startup environment binding. C.UTF-8 additionally requires the exact
    Root stock_startup_locale_lifecycle token: successful stock Desktop locale
    initialization and no subsequent native language mutation, not a config ref. That external input is neither API-observed nor an
    assertion that the host's libc has this locale installed: the pinned Linux
    native source parses the string directly. Unknown/additional keys refuse.
    Export font name is resolved from the observed MS substitution configuration.
    Caller adds the pinned clean-default fields expected by observer leaf R2.
    """
    _require(callable(property_value_factory), "property_value_factory_missing")
    _require(model.supportsService("com.sun.star.sheet.SpreadsheetDocument") is True,
             "not_real_calc_model_service")
    styles = model.getStyleFamilies().getByName("CellStyles")
    style = styles.getByName("Default")
    _require(style.getName() == "Default" and style.isUserDefined() is False
             and style.getParentStyle() == "", "builtin_Default_style_binding_failed")
    values = {name: _checked_property(style, name, typename)
              for name, typename in PROPERTY_TYPES.items()}
    _require(type(values["CharFontName"]) is str and values["CharFontName"] == "Calibri",
             "source_font_name_outside_supported_profile")
    for name, expected in (("CharHeight", 11.0), ("CharWeight", 100.0)):
        value = values[name]
        _require(type(value) in (int, float) and value == expected and math.isfinite(value),
                 "source_font_scalar_outside_supported_profile")
    _require(type(values["CharFontFamily"]) is int and values["CharFontFamily"] == 5,
             "source_font_family_outside_supported_profile")
    charset = values["CharFontCharSet"]
    _require(type(charset) is int and charset in CHARSET_ROUNDTRIPS,
             "source_charset_roundtrip_unsupported")
    posture = values["CharPosture"]
    _require(getattr(posture, "typeName", None) == "com.sun.star.awt.FontSlant"
             and getattr(posture, "value", None) == "NONE", "source_posture_not_NONE")
    provider = component_context.getValueByName(DEFAULT_PROVIDER)
    _require(provider is not None, "default_configuration_provider_missing")
    setup = _config_access(provider, SETUP_NODE, property_value_factory)
    locale = setup.getByName("ooSetupSystemLocale")
    _require(type(locale) is str, "system_locale_property_schema_mismatch")
    # No inference from source text language, UI ooLocale, or available fonts.
    external_binding = None
    startup_conditions = list(EXTERNAL_STARTUP_CONDITIONS)
    selected_lc_all = None
    if startup_locale_environment is not None:
        _require(type(startup_locale_environment) is dict
                 and set(startup_locale_environment) == {"LC_ALL"},
                 "startup_locale_environment_schema_unsupported")
        selected_lc_all = startup_locale_environment["LC_ALL"]
        _require(type(selected_lc_all) is str
                 and selected_lc_all in ("en_US.UTF-8", "C.UTF-8"),
                 "startup_LC_ALL_outside_supported_en_US_or_C_UTF8_branch")
    if selected_lc_all == "C.UTF-8":
        _require(stock_startup_locale_lifecycle == C_UTF8_STOCK_LOCALE_LIFECYCLE,
                 "C_UTF8_stock_startup_language_lifecycle_UNBOUND")
    else:
        _require(stock_startup_locale_lifecycle is None,
                 "stock_startup_language_lifecycle_without_C_UTF8_branch")
    if locale == "":
        _require(selected_lc_all is not None,
                 "empty_system_locale_requires_unexposed_host_fallback")
        # Linux inunx uses LC_ALL first; isolang splits C.UTF-8 at '.',
        # lowercases C and maps the exact 'c' other-name to ENGLISH_US.
        # This is not SAL's osl_getProcessLocale/rtl_Locale parser.
        external_binding = {
            "kind": "EXTERNAL_ROOT_INPUT_NOT_API_OBSERVED",
            "process_start_environment": {"LC_ALL": selected_lc_all},
            "usage": "USED_EMPTY_CONFIGURATION_HOST_FALLBACK",
            "source_derived_effective_language_tag": "en-US",
            "scope": "native_Linux_environment_string_parse_not_libc_locale_availability",
        }
        startup_conditions.append(
            "actual_Root_bound_process_start_LC_ALL_unchanged_and_no_native_configured_system_language_override")
    else:
        _require(locale == "en-US", "application_script_locale_outside_supported_en_US_branch")
        if selected_lc_all is not None:
            external_binding = {
                "kind": "EXTERNAL_ROOT_INPUT_NOT_API_OBSERVED",
                "process_start_environment": {"LC_ALL": selected_lc_all},
                "usage": "UNUSED_EXPLICIT_CONFIGURATION_PRECEDENCE",
            }
    if selected_lc_all == "C.UTF-8":
        # The token is an externally bound Root lifecycle fact, not API proof
        # or a conclusion from ooSetupSystemLocale. Pinned stock prepareLocale
        # selects the configured system language from this same config/env.
        external_binding["stock_startup_locale_lifecycle"] = stock_startup_locale_lifecycle
        startup_conditions.append(
            "Root_observed_successful_stock_Desktop_prepareLocale_and_no_later_native_language_mutation")
    substitutions = _config_access(provider, SUBSTITUTION_NODE, property_value_factory)
    export_name, ms_observation = _resolve_ms_name(values["CharFontName"], substitutions)
    settings = component_context.getServiceManager().createInstanceWithContext(
        GLOBAL_SETTINGS_SERVICE, component_context)
    _require(settings is not None, "GlobalSheetSettings_unavailable")
    printer_metrics = _checked_property(settings, "UsePrinterMetrics", "boolean")
    _require(type(printer_metrics) is bool, "UsePrinterMetrics_schema_mismatch")
    _require(printer_metrics is False, "TextWysiwyg_printer_reference_path_unsupported")
    windows_charset, export_charset = CHARSET_ROUNDTRIPS[charset]
    nominal = {"Name": values["CharFontName"], "HeightPt": float(values["CharHeight"]),
               "Family": values["CharFontFamily"], "CharSet": charset,
               "Weight": float(values["CharWeight"]), "Posture": "NONE"}
    observations = {
        "style": {"family": "CellStyles", "programmatic_name": "Default",
                  "builtin": True, "parent": "", "font": nominal},
        "application_locale_config": {"nodepath": SETUP_NODE,
            "property": "ooSetupSystemLocale", "value": locale},
        "application_locale_external_binding": external_binding,
        "ms_name_transform": ms_observation,
        "charset_roundtrip": {"observed_source_UNO_short": charset,
            "source_derived_RTL_encoding": charset % 65536,
            "source_derived_Windows_charset_byte": windows_charset,
            "source_derived_export_RTL_encoding": export_charset},
        "global_sheet_settings": {"service": GLOBAL_SETTINGS_SERVICE,
            "property": "UsePrinterMetrics", "value": printer_metrics},
    }
    return {
        "schema": "frw.calc.runtime-font-recipe.observation.v1",
        "source_commit": SOURCE_COMMIT, "version": VERSION,
        "source_nominal_font": nominal,
        "recipe": {"Name": export_name, "Height": 220, "Family": 5,
                   "CharSet": export_charset, "Weight": 100.0},
        "default_script": {"value": "LATIN",
            "kind": "SOURCE_DERIVED_STARTUP_APPLICATION_STATE",
            "observed_ooSetupSystemLocale": locale,
            "external_startup_binding": external_binding,
            "requires_external_Root_conditions": startup_conditions},
        "use_printer_metrics": printer_metrics,
        "observations": observations,
        "observation_sha256": observation_digest(observations),
        "authority": "OBSERVATIONS_AND_CONDITIONAL_SOURCE_DERIVATION_ONLY",
    }
