"""Pure Source checks; all API/context objects are explicit inert facades.

No UNO import, Office process, actual Root admission, digit query or metric value.
The context digests below bind synthetic test bytes and prove no authority.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
checks = []

def check(name, value):
    if not value:
        raise AssertionError(name)
    checks.append({'name': name, 'pass': True})

def load(path, name):
    module = types.ModuleType(name)
    exec(compile(path.read_text(), str(path), 'exec'), module.__dict__)
    return module

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

before = load(ROOT/'before/runtime_font_resolver.py', 'before_resolver')
after = load(ROOT/'candidate/qualifier/runtime_font_resolver.py', 'after_resolver')
old_leaf = load(ROOT/'before/reference_metric_leaf_r2.py', 'old_leaf')
leaf = load(ROOT/'candidate/qualifier/reference_metric_leaf_r2.py', 'leaf')
check('resolver506_pinned', digest(ROOT/'before/runtime_font_resolver.py') == '50605de9fdd064f7cf33ada71ba50c02ca385ec99ccd778d7df067c96046b553')
check('R2_parent_pinned', digest(ROOT/'before/reference_metric_leaf_r2.py') == 'b4b842ebb269c47e24190f3ed0139fcd91471d1b45241b86ccab8649757a6d7f')

# Reverse precisely the charset constant/docstring/metadata edits, then compare
# every executable AST node. Comments do not affect the AST.
changed_ast = ast.parse((ROOT/'candidate/qualifier/runtime_font_resolver.py').read_text())
for node in changed_ast.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CHARSET_ROUNDTRIPS' for t in node.targets):
        check('exact_charset_table', ast.literal_eval(node.value) == {-1:(1,0), 0:(1,0), 1:(0,1)})
        node.value = ast.parse('{0:(1,0), 1:(0,1)}', mode='eval').body
    if isinstance(node, ast.FunctionDef) and node.name == 'resolve_font_recipe':
        doc = node.body[0].value
        doc.value = doc.value.replace('Swiss, normal, no posture; UNO charset short -1 (RTL Unicode), 0 or 1;\n    explicit en-US locale config,', 'Swiss, normal, no posture; RTL charset 0 or 1; explicit en-US locale config,')
        for obj in ast.walk(node):
            if isinstance(obj, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == 'observed_source_UNO_short' for k in obj.keys):
                pairs = [(k,v) for k,v in zip(obj.keys,obj.values) if not (isinstance(k,ast.Constant) and k.value == 'source_derived_RTL_encoding')]
                obj.keys = [ast.Constant('observed_source_RTL_encoding') if isinstance(k,ast.Constant) and k.value == 'observed_source_UNO_short' else k for k,v in pairs]
                obj.values = [v for k,v in pairs]
check('resolver_all_other_AST_unchanged', ast.dump(changed_ast, include_attributes=False) == ast.dump(ast.parse((ROOT/'before/runtime_font_resolver.py').read_text()), include_attributes=False))
leaf_text = (ROOT/'candidate/qualifier/reference_metric_leaf_r2.py').read_text()
restored_leaf = leaf_text.replace("and type(nominal['CharSet']) is int\n            and (nominal['CharSet'] == -1 or 0 <= nominal['CharSet'] < 65536),", "and type(nominal['CharSet']) is int and 0 <= nominal['CharSet'] < 65536,")
check('R2_only_exact_minus1_validation_AST_change', ast.dump(ast.parse(restored_leaf), include_attributes=False) == ast.dump(ast.parse((ROOT/'before/reference_metric_leaf_r2.py').read_text()), include_attributes=False))
check('actual_reread_full_equality_unchanged', "require(actual == bound['source_font'], 'source_Default_font_changed')" in leaf_text)

class Names:
    def __init__(self, values): self.values = values
    def getElementNames(self): return tuple(self.values)
    def getByName(self, name):
        value = self.values[name]
        return Names(value) if type(value) is dict else value

class Style:
    def __init__(self, charset):
        self.values = {'CharFontName':'Calibri', 'CharHeight':11.0, 'CharFontFamily':5,
            'CharFontCharSet':charset, 'CharWeight':100.0,
            'CharPosture':types.SimpleNamespace(typeName='com.sun.star.awt.FontSlant', value='NONE')}
        self.charset_schema = 'short'
    def getName(self): return 'Default'
    def isUserDefined(self): return False
    def getParentStyle(self): return ''
    def getPropertySetInfo(self):
        return types.SimpleNamespace(getPropertyByName=lambda name: types.SimpleNamespace(Type=types.SimpleNamespace(typeName=self.charset_schema if name == 'CharFontCharSet' else after.PROPERTY_TYPES[name])))
    def getPropertyValue(self, name): return self.values[name]

class Settings:
    value = False
    def getPropertySetInfo(self):
        return types.SimpleNamespace(getPropertyByName=lambda name:types.SimpleNamespace(Type=types.SimpleNamespace(typeName='boolean')))
    def getPropertyValue(self, name):
        assert name == 'UsePrinterMetrics'
        return self.value

class Provider:
    locale = ''
    raw_ms = None
    def createInstanceWithArguments(self, service, args):
        assert service == after.CONFIG_SERVICE
        if args[0].Value == after.SETUP_NODE:
            return Names({'ooSetupSystemLocale':self.locale})
        assert args[0].Value == after.SUBSTITUTION_NODE
        return Names({'en':{'calibri':{'SubstFontsMS':self.raw_ms}}})

class Context:
    def __init__(self):
        self.provider = Provider(); self.settings = Settings(); self.provider_reads = 0
    def getValueByName(self, name):
        assert name == after.DEFAULT_PROVIDER
        self.provider_reads += 1
        return self.provider
    def getServiceManager(self):
        return types.SimpleNamespace(createInstanceWithContext=lambda service, context:self.settings)

class Model:
    def __init__(self, style): self.style = style
    def supportsService(self, service): return service == 'com.sun.star.sheet.SpreadsheetDocument'
    def getStyleFamilies(self): return types.SimpleNamespace(getByName=lambda name:types.SimpleNamespace(getByName=lambda name:self.style))
    def getURL(self): return 'file:///home/jericho/.cache/INERT-SOURCE-CHECK/source.ods'
    def isReadonly(self): return True
    def isModified(self): return False
    def getPropertyValue(self, name):
        assert name == 'ReferenceDevice'
        return None  # Deliberately no device, hence no digit path.

kwargs = dict(property_value_factory=lambda name,value:types.SimpleNamespace(Name=name,Value=value),
    startup_locale_environment={'LC_ALL':'C.UTF-8'}, stock_startup_locale_lifecycle=after.C_UTF8_STOCK_LOCALE_LIFECYCLE)

def refusal(module, fn, code):
    try: fn()
    except (module.FontResolutionRefused if hasattr(module,'FontResolutionRefused') else module.Unbound) as exc:
        return (getattr(exc,'code',None) or str(exc)) == code
    return False

def resolve(module, charset):
    return module.resolve_font_recipe(Model(Style(charset)), Context(), **kwargs)

check('prior_resolver_refuses_supported_API_minus1', refusal(before, lambda:resolve(before,-1), 'source_charset_roundtrip_unsupported'))
output = resolve(after,-1)
check('raw_API_minus1_kept_in_source_nominal', output['source_nominal_font']['CharSet'] == -1)
check('raw_API_minus1_kept_in_style_observation', output['observations']['style']['font']['CharSet'] == -1)
check('explicit_unsigned_reconstruction_separate_from_API_observation', output['observations']['charset_roundtrip'] == {'observed_source_UNO_short':-1,'source_derived_RTL_encoding':65535,'source_derived_Windows_charset_byte':1,'source_derived_export_RTL_encoding':0})
check('exact_reconstructed_export_recipe', output['recipe'] == {'Name':'Calibri','Height':220,'Family':5,'CharSet':0,'Weight':100.0})
check('accepted_nil_handling_preserved_in_inert_projection', output['observations']['ms_name_transform']['observed_SubstFontsMS'] is None)
check('observation_digest_binds_raw_and_derived_distinction', output['observation_sha256'] == after.observation_digest(output['observations']))
check('authority_remains_conditional_Source', output['authority'] == 'OBSERVATIONS_AND_CONDITIONAL_SOURCE_DERIVATION_ONLY')
for charset in [0,1]:
    old = resolve(before,charset); new = resolve(after,charset)
    converted = copy.deepcopy(new)
    rd = converted['observations']['charset_roundtrip']
    del rd['source_derived_RTL_encoding']
    rd['observed_source_RTL_encoding'] = rd.pop('observed_source_UNO_short')
    converted['observation_sha256'] = before.observation_digest(converted['observations'])
    check('prior_branch_all_fields_same_except_explicit_charset_metadata_'+str(charset), old == converted)

class IntSubclass(int): pass
invalid = [-32768,-2,2,76,32767,32768,65535,65536,True,False,-1.0,'-1',b'-1',None,[],{},IntSubclass(-1)]
for index,raw in enumerate(invalid):
    context = Context()
    check('unsupported_charset_type_or_value_'+str(index), refusal(after, lambda:after.resolve_font_recipe(Model(Style(raw)),context,**kwargs), 'source_charset_roundtrip_unsupported'))
    check('unsupported_charset_refuses_before_config_'+str(index), context.provider_reads == 0)
style = Style(-1); style.charset_schema = 'unsigned short'
check('wrong_charfontcharset_schema_still_refuses', refusal(after, lambda:after.resolve_font_recipe(Model(style),Context(),**kwargs), 'property_schema_mismatch'))

# Exact current nearest R2 consumer with synthetic bytes only. No fake runtime
# record is written and no measurement leaf can reach a font/digit API.
def source_context(result):
    return dict(schema='frw.Root.calc-reference-metric-qualified-context.v2',
        source_sha256=leaf.SOURCE_SHA256, source_bytes=leaf.SOURCE_BYTES,
        working_copy_url=Model(Style(-1)).getURL(), working_copy_sha256_before=leaf.SOURCE_SHA256,
        working_copy_bytes=leaf.SOURCE_BYTES, producer_version=leaf.VERSION,
        reviewed_source_commit=leaf.SOURCE_COMMIT,
        components={role:dict(expected_sha256='0'*64,observed_sha256='0'*64) for role in leaf.COMPONENT_ROLES},
        standalone_non_LOK=True,same_reference_state=True,no_concurrent_device_user=True,
        native_width_transport=dict(mode='RAW32_POSTQUERY_NATIVE_JOIN',native_min=None,native_max=None,proof_sha256=None),
        default_script='LATIN',source_style_name='Default',source_font=result['source_nominal_font'],
        export_descriptor=dict(leaf.DEFAULTS,**result['recipe']),
        load_policy=dict(read_only=True,hidden=True,macros='NEVER_EXECUTE',links='NO_UPDATE',interaction='ABORT_ONLY',network='OS_NAMESPACE_DENY',profile='FRESH_PRIVATE_NO_RESTORE',store_render_draw_conversion=False),
        evidence={role:dict(basis='ROOT_EXTERNAL_RECORD',sha256='0'*64) for role in leaf.EVIDENCE_ROLES})
ctx = source_context(output)
check('prior_R2_refuses_same_observed_minus1_context', refusal(old_leaf, lambda:old_leaf.validate_root_context(ctx,old_leaf.qualification_sha256(ctx)), 'qualified_source_Normal_font_required'))
check('new_R2_accepts_only_synthetic_schema_with_raw_minus1', leaf.validate_root_context(ctx,leaf.qualification_sha256(ctx)) is ctx)
callbacks = dict(before_digit=lambda *args:None,after_digit=lambda *args:None)
check('raw_minus1_full_style_reread_equality_passes_without_device_or_digits', refusal(leaf, lambda:leaf.observe_reference_metric(Model(Style(-1)),ctx,leaf.qualification_sha256(ctx),**callbacks), 'exact_reference_device_capability_required'))
wrong = copy.deepcopy(ctx); wrong['source_font']['CharSet'] = 65535
check('normalizing_observed_minus1_to_65535_is_rejected_by_unchanged_equality', refusal(leaf, lambda:leaf.observe_reference_metric(Model(Style(-1)),wrong,leaf.qualification_sha256(wrong),**callbacks), 'source_Default_font_changed'))
for raw in [-32768,-2,65536,True,False,-1.0,'-1',None]:
    bad = copy.deepcopy(ctx); bad['source_font']['CharSet'] = raw
    check('R2_other_negative_oversize_type_refusal_'+str(len(checks)), refusal(leaf, lambda:leaf.validate_root_context(bad,leaf.qualification_sha256(bad)), 'qualified_source_Normal_font_required'))
for raw in [-1,65536,True,-1.0]:
    bad = copy.deepcopy(ctx); bad['export_descriptor']['CharSet'] = raw
    check('R2_export_guard_unchanged_'+str(len(checks)), refusal(leaf, lambda:leaf.validate_root_context(bad,leaf.qualification_sha256(bad)), 'qualified_export_font_transform_UNBOUND'))

result = dict(schema='frw.charset-roundtrip.source-delta-pure-checks.v1',status='PASS_SOURCE_ONLY',test_count=len(checks),checks=checks,
    effects=dict(UNO=False,Office=False,namespace=False,network=False,admission=False,measurement=False,digits=False),
    facade_limit='All API/config/context objects are explicit inert Source facades; source_context zero hashes establish no external facts. No widths or M are created.',
    actual_M=None,actual_case_accepted=False,actual_Root0b33_charset='UNKNOWN_NOT_CAPTURED',
    code_refs=[dict(path=str(p),sha256=digest(p)) for p in [ROOT/'candidate/qualifier/runtime_font_resolver.py',ROOT/'candidate/qualifier/reference_metric_leaf_r2.py']])
p = ROOT/'CHECKS.json'; p.write_text(json.dumps(result,indent=2)+'\n'); p.chmod(0o600)
print(json.dumps(dict(status=result['status'],test_count=len(checks),checks_sha256=digest(p))))
