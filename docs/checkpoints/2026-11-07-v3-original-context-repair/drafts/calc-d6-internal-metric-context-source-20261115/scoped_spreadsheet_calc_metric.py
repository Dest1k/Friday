"""Internal conditional Calc numeric relation; no observer or trust admission.

The trusted renderer/producer must construct this finite context only AFTER
independently verifying its facts and applicability to these exact byte inputs.
A dataclass, matching hashes, or serialized user claims authenticate nothing.
There is deliberately no JSON loader, runtime provider, metric default, fit, or
workbook hash allowlist. The default renderer supplies no context and refuses
unchanged. Actual producer/context admission is outside this source module.

Numeric rule reused from Source98 width_metric_proposal.py f0039fd8e0d3ac61,
with Source99 M1 7d47d578faf8f9cd terminology: M is the raw current-reference
logical scalar, NOT an established physical twip/pixel/point measurement.
"""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import re

PROFILE = 'calc-imported-native-rich-v1'
RULE = 'lo-26.2.5.2-explicit-column-forward-v1'
REVIEWED_COMMIT = 'cd7284b4cbbfeb507e630c1aac019f4157393acb'
COMPONENT_ROLES = ('calc_document','calc_xlsx_filter','sal','toolkit','vcl')


class MetricContextError(ValueError):
    pass


def _require(condition, code):
    if not condition:
        raise MetricContextError(code)


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


@dataclass(frozen=True)
class CalcReferenceMetricContext:
    """Already-verified INTERNAL facts, supplied by a trusted producer caller.

    Identity digests correlate a particular operation; they do not admit a
    workbook or prove any recorded fact. Evidence digests identify Root's finite
    producer/font/reference/applicability work, not a receipt authority system.
    The caller owns the real verification and any historical continuity proof.
    No public tool/user argument can create this object through this module.
    """
    source_sha256: str
    source_bytes: int
    destination_sha256: str
    destination_bytes: int
    producer_version: str
    reviewed_source_commit: str
    numeric_rule: str
    recipe_sha256: str
    component_sha256: tuple
    source_style_name: str
    source_font: tuple
    default_script: str
    export_name: str
    export_charset: int
    raw_font_height: int
    font_descriptor_sha256: str
    font_view_sha256: str
    reference_state_sha256: str
    applicability_sha256: str
    raw_m: int


def _context(context, source, destination):
    _require(type(context) is CalcReferenceMetricContext,'calc_metric_context_unbound')
    for name in ('source_sha256','destination_sha256','recipe_sha256',
                 'font_descriptor_sha256','font_view_sha256',
                 'reference_state_sha256','applicability_sha256'):
        _require(_sha(getattr(context,name)),'calc_metric_context_unbound')
    for name in ('source_bytes','destination_bytes'):
        _require(type(getattr(context,name)) is int and getattr(context,name)>0,
                 'calc_metric_context_unbound')
    for role,signature in (('source',source),('destination',destination)):
        _require((getattr(signature,'_package_sha256',None),
                  getattr(signature,'_package_bytes',None)) ==
                 (getattr(context,role+'_sha256'),getattr(context,role+'_bytes')),
                 'calc_metric_context_bytes_mismatch')
    _require(context.producer_version=='26.2.5.2'
             and context.reviewed_source_commit==REVIEWED_COMMIT
             and context.numeric_rule==RULE,'calc_metric_rule_unsupported')
    components=context.component_sha256
    _require(type(components) is tuple and len(components)==len(COMPONENT_ROLES)
             and all(type(row) is tuple and len(row)==2 for row in components)
             and tuple(row[0] for row in components)==COMPONENT_ROLES
             and all(_sha(row[1]) for row in components),
             'calc_metric_context_unbound')
    _require(context.source_style_name=='Default'
             and type(context.source_font) is tuple
             and context.source_font==('Calibri',Decimal(11))
             and type(context.source_font[1]) is Decimal
             and context.default_script=='LATIN'
             and type(context.export_name) is str
             and 0<len(context.export_name)<=255
             and not any(ord(c)<32 for c in context.export_name)
             and type(context.export_charset) is int and 0<=context.export_charset<=65535
             and type(context.raw_font_height) is int and context.raw_font_height==220,
             'calc_metric_font_profile_unsupported')
    _require(type(context.raw_m) is int and 0<context.raw_m<65536,
             'calc_reference_raw_metric_unbound')


def _half_up(value, stage, *, binary=False):
    _require(type(value) is Fraction and 0<value<=100000000,
             'calc_metric_length_unsupported')
    # The XML parser and SaveXml token expression use floating arithmetic.
    # The intervening integer convertTwipToMm100 conversion has exact half-up
    # rounding, so its half edges must not be incorrectly refused.
    _require(not binary or value.denominator!=2,'calc_'+stage+'_binary_half_boundary_unassessed')
    return (2*value.numerator+value.denominator)//(2*value.denominator)


def _xml_length_mm100(length_cm, original_length):
    """Refuse unproved XML rounding decisions, using the ORIGINAL lexeme.

    Pinned sax converter lcl_parseMeasure uses positive digit accumulation,
    decimal-divisor multiplication, division and addition, then unit conversion
    and +.5/truncation. For this positive bounded grammar there is no numerical
    cancellation. A conservative 8*n+64 binary64 rounding-operation budget
    covers the digit loops, denominators, unit conversion and final addition.
    Standard gamma_k=k*u/(1-k*u), u=2**-53, bounds their forward uncertainty.
    Once the decimal divisor overflows, every further addend is zero; the
    missing normalized tail is <1e-300 and is included separately below.
    This interval ONLY REFUSES ambiguous half decisions. It grants no tolerance
    to target-token equality and does not emulate arbitrary binary parser edges.
    """
    _require(type(original_length) is str,'calc_original_length_lexeme_required')
    match=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)(cm|mm|in|pt)',original_length)
    _require(match is not None,'calc_original_length_lexeme_required')
    factors={'cm':Fraction(1),'mm':Fraction(1,10),
             'in':Fraction(127,50),'pt':Fraction(127,3600)}
    exact=Fraction(Decimal(match[1]))*factors[match[2]]
    _require(exact==length_cm,'calc_original_length_geometry_mismatch')
    value=exact*1000
    steps=8*len(match[1])+64
    unit_roundoff=Fraction(1,2**53)
    _require(steps*unit_roundoff<Fraction(1,2),'calc_xml_rounding_scope_unsupported')
    gamma=steps*unit_roundoff/(1-steps*unit_roundoff)
    uncertainty=(value+1)*gamma+Fraction(1,10**300)
    floor=value.numerator//value.denominator
    half_distance=abs(value-Fraction(2*floor+1,2))
    _require(half_distance>uncertainty,'calc_xml_length_binary_rounding_unassessed')
    return _half_up(value,'xml_length',binary=True)


def lo_262_export_mm100(length_cm, *, original_length):
    """Exact rational source rule after a source-lexeme ambiguity refusal."""
    _require(type(length_cm) is Fraction and 0<length_cm<=1000,
             'calc_metric_length_unsupported')
    imported=_xml_length_mm100(length_cm,original_length)
    native=_half_up(Fraction(imported*72,127),'native_length')
    _require(0<native<65536,'calc_native_width_range_unsupported')
    return _half_up(Fraction(native*127,72),'export_length')


def lo_262_explicit_export_token(exported_mm100, *, raw_m):
    """Source98 exact SaveXml numeric model using raw reference scalar M."""
    _require(type(raw_m) is int and 0<raw_m<65536,
             'calc_reference_raw_metric_unbound')
    _require(type(exported_mm100) is int and 0<exported_mm100<=1000000,
             'calc_metric_length_unsupported')
    exact_cents=Fraction(exported_mm100*72*100,raw_m*127)
    cents=_half_up(exact_cents,'export_token',binary=True)
    token=Decimal((0,tuple(int(d) for d in str(cents)),-2))
    _require(1<=token<=255,'calc_metric_width_domain_unsupported')
    return token


def _columns(signature, source, names):
    result={}
    geometry=getattr(signature,'native_geometry',None)
    _require(type(geometry) is tuple,'calc_metric_raw_geometry_required')
    for row in geometry:
        _require(type(row) is tuple and len(row)>=2,'calc_metric_raw_geometry_required')
        if row[0]!='column_width':continue
        _require(len(row)==5,'calc_metric_raw_geometry_required')
        _,scope,first,last,value=row
        _require(scope in names and type(first) is int and type(last) is int
                 and 1<=first<=last<=64,'calc_metric_column_unsupported')
        if source:
            _require(type(value) is tuple and len(value)==2
                     and all(type(n) is int for n in value)
                     and value[0]>0 and value[1]>0,
                     'calc_metric_raw_geometry_required')
            value=Fraction(*value)
            _require(0<value<=1000,'calc_metric_length_unsupported')
        else:
            _require(type(value) is Decimal and value.is_finite() and 1<=value<=255,
                     'calc_metric_raw_token_required')
        for column in range(first,last+1):
            key=scope,column
            _require(key not in result,'calc_metric_column_overlap')
            result[key]=value
    return result


def _length_lexemes(signature,names):
    rows=getattr(signature,'_calc_column_lengths',None)
    _require(type(rows) is tuple,'calc_original_length_lexeme_required')
    values={}
    for row in rows:
        _require(type(row) is tuple and len(row)==4,'calc_original_length_lexeme_required')
        scope,first,last,raw=row
        _require(scope in names and type(first) is int and type(last) is int
                 and 1<=first<=last<=64 and type(raw) is str,
                 'calc_original_length_lexeme_required')
        for column in range(first,last+1):
            key=scope,column
            _require(key not in values,'calc_metric_column_overlap')
            values[key]=raw
    return values


def compare_explicit_tokens(source,destination,coverage,context):
    """Return separate exact expected/observed maps only after all checks.

    The existing rich comparator retains hidden-state, domains, coverage,
    graphs, styles, caches and every non-column comparison. This helper neither
    reconstructs a destination nor interprets physical geometry/fidelity.
    """
    _require(getattr(source,'source_kind','')=='ods'
             and getattr(source,'native_calc_profile',False) is True
             and getattr(source,'_destination_profile','')==PROFILE
             and getattr(destination,'source_kind','')=='xlsx'
             and getattr(destination,'native_calc_profile',False) is False
             and getattr(destination,'generated_profile','')==PROFILE,
             'calc_metric_profile_unsupported')
    _context(context,source,destination)
    names=getattr(source,'sheet_names',())
    _require(type(names) is tuple and names and len(names)==len(set(names))
             and getattr(destination,'sheet_names',())==names,
             'calc_metric_sheet_scope_unsupported')
    lengths=_columns(source,True,names);observed=_columns(destination,False,names)
    _require(lengths.keys()==observed.keys()==coverage and bool(lengths),
             'calc_metric_exact_column_coverage_required')
    lexemes=_length_lexemes(source,names)
    _require(lexemes.keys()==lengths.keys(),'calc_metric_exact_column_coverage_required')
    expected={key:lo_262_explicit_export_token(
                  lo_262_export_mm100(length,original_length=lexemes[key]),raw_m=context.raw_m)
              for key,length in lengths.items()}
    _require(expected==observed,'calc_exact_producer_token_mismatch')
    return expected,observed
