"""Pure Source-copy check with the exact retained registry metadata.

The schema projection and API objects are inert test doubles, not live UNO.
No Office/model/render/network/namespace effect or acceptance is performed.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
BEFORE = Path('/home/jericho/.cache/FRW-ASTRA-CALC-ACTIVE-PUBLICATION-READER-DELTA-20261115/candidate/qualifier/runtime_font_resolver.py')
AFTER = ROOT / 'candidate/qualifier/runtime_font_resolver.py'
REGISTRY = Path('/home/jericho/.jericho/toolchains/libreoffice-26.2.5.2-ubuntu26.04-amd64/root/usr/lib/libreoffice/share/registry/main.xcd')
QUALIFIER = BEFORE.with_name('runtime_qualifier.py')
NS = '{http://openoffice.org/2001/registry}'
checks = []


def check(name, value):
    if not value:
        raise AssertionError(name)
    checks.append({'name': name, 'pass': True})


def load(path, name):
    m = types.ModuleType(name)
    exec(compile(path.read_text(), str(path), 'exec'), m.__dict__)
    return m


before = load(BEFORE, 'before_resolver')
after = load(AFTER, 'after_resolver')
qualifier = load(QUALIFIER, 'unchanged_qualifier')
check('before_pin', hashlib.sha256(BEFORE.read_bytes()).hexdigest() == 'dff61235323e51a3bd9e54f986411ca38fea57917bf1f9c016d3adb5b4898760')
check('registry_pin', hashlib.sha256(REGISTRY.read_bytes()).hexdigest() == '64d6e1a666eba60f99cc06499ef8acaba3935402f4086203fb2ba26872b2700e')
check('qualifier_pin', hashlib.sha256(QUALIFIER.read_bytes()).hexdigest() == 'efdf59843332ae97b71d58b4ba9694556e0d2a8c0647a31293f0e9dccde6fff7')

# Reverse only this small edit and compare the complete AST, proving that no
# style/locale/measurement/config/reference criterion was otherwise changed.
new_ast = ast.parse(AFTER.read_text())
old_ast = ast.parse(BEFORE.read_text())
fn = next(n for n in new_ast.body if isinstance(n, ast.FunctionDef) and n.name == '_resolve_ms_name')
changed_if = None
for n in ast.walk(fn):
    if isinstance(n, ast.If) and any(isinstance(q, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ms_tokens' for t in q.targets) for q in n.body):
        changed_if = n
check('exact_changed_branch_found', changed_if is not None)
changed_if.body = [n for n in changed_if.body if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ms_tokens' for t in n.targets))]
for n in ast.walk(changed_if):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == '_require' and any(isinstance(x, ast.Constant) and x.value == 'MS_substitution_property_schema_unsupported' for x in n.args):
        n.args[0] = ast.parse('type(raw_ms) is str and len(raw_ms) <= 65536', mode='eval').body
    if isinstance(n, ast.Name) and n.id == 'ms_tokens':
        n.id = 'raw_ms'
check('all_other_AST_unchanged', ast.dump(old_ast, include_attributes=False) == ast.dump(new_ast, include_attributes=False))

root = ET.parse(REGISTRY).getroot()
schemas = [n for n in root if n.tag.endswith('component-schema') and n.attrib.get(NS + 'name') == 'VCL' and n.attrib.get(NS + 'package') == 'org.openoffice']
data = [n for n in root if n.tag.endswith('component-data') and n.attrib.get(NS + 'name') == 'VCL' and n.attrib.get(NS + 'package') == 'org.openoffice']
check('one_real_VCL_schema', len(schemas) == 1)
template = next(n for n in schemas[0].iter() if n.tag == 'group' and n.attrib.get(NS + 'name') == 'LFonts')
props = [n for n in template if n.tag == 'prop']
ms_schema = next(n for n in props if n.attrib.get(NS + 'name') == 'SubstFontsMS')
check('real_MS_schema_is_string', ms_schema.attrib[NS + 'type'] == 'xs:string')
check('real_MS_schema_has_no_value', ms_schema.find('value') is None)
check('real_MS_schema_not_marked_nonnillable', ms_schema.attrib.get(NS + 'nillable') != 'false')
table = {}
for contribution in data:
    for subst in contribution:
        if subst.attrib.get(NS + 'name') != 'FontSubstitutions':
            continue
        for locale in subst:
            fonts = table.setdefault(locale.attrib[NS + 'name'], {})
            for font in locale:
                vals = {p.attrib[NS + 'name']: None for p in props}
                for p in font:
                    value = p.find('value')
                    vals[p.attrib[NS + 'name']] = (value.text or '') if value is not None else None
                fonts[font.attrib[NS + 'name']] = vals
check('real_locale_keys_exact_en', sorted(table) == ['en'])
check('real_calibri_MS_nil_projection', table['en']['calibri']['SubstFontsMS'] is None)
check('real_calibri_general_substitution_present', bool(table['en']['calibri']['SubstFonts']))


class Names:
    def __init__(self, values):
        self.values = values

    def getElementNames(self):
        return tuple(self.values)

    def getByName(self, name):
        value = self.values[name]
        return Names(value) if isinstance(value, dict) else value


def refusal(module, fn, code):
    try:
        fn()
    except module.FontResolutionRefused as e:
        return e.code == code
    return False


static_names = Names(table)
check('old_resolver_refuses_real_nil_projection', refusal(before, lambda: before._resolve_ms_name('Calibri', static_names), 'MS_substitution_property_schema_unsupported'))
name, observed = after._resolve_ms_name('Calibri', static_names)
check('candidate_real_nil_projection_keeps_Calibri', name == 'Calibri')
check('candidate_preserves_observed_nil', observed['native_matched_key'] == 'calibri' and observed['observed_SubstFontsMS'] is None)
check('general_substitutions_not_used_as_MS', name not in table['en']['calibri']['SubstFonts'].split(';'))
check('nullable_observation_remains_digestible_by_real_nearest_consumer', len(qualifier.sha(observed)) == 64)

for raw in ['', 'Arial', ';Calibri;;Arial;Verdana', 'Calibri', 'Carlito;Arial']:
    names = Names({'en': {'calibri': {'SubstFontsMS': raw}}})
    check('unchanged_populated_string_' + repr(raw), before._resolve_ms_name('Calibri', names) == after._resolve_ms_name('Calibri', names))
for raw in [False, True, 0, 1, 1.5, [], {}, b'', object(), 'x' * 65537]:
    # A dict is wrapped by Names and is still an unsupported test object.
    check('invalid_MS_type_or_bound_' + type(raw).__name__ + '_' + str(len(checks)), refusal(after, lambda raw=raw: after._resolve_ms_name('Calibri', Names({'en': {'calibri': {'SubstFontsMS': raw}}})), 'MS_substitution_property_schema_unsupported'))
for raw in [' Arial', 'Arial ', 'Arial,Calibri']:
    check('unsafe_nonempty_MS_still_refuses_' + repr(raw), refusal(after, lambda raw=raw: after._resolve_ms_name('Calibri', Names({'en': {'calibri': {'SubstFontsMS': raw}}})), 'resolved_export_font_name_unsupported'))
check('unsupported_locale_still_refuses', refusal(after, lambda: after._resolve_ms_name('Calibri', Names({'sr-Latn': {}})), 'configuration_locale_canonicalization_unsupported'))

# The next boundary is exercised only with inert objects. Values match the
# narrow nominal profile and exact real metadata types already required.
class Info:
    def getPropertyByName(self, name):
        return types.SimpleNamespace(Type=types.SimpleNamespace(typeName=after.PROPERTY_TYPES[name]))


class Style:
    values = {'CharFontName': 'Calibri', 'CharHeight': 11.0, 'CharFontFamily': 5,
              'CharFontCharSet': 1, 'CharWeight': 100.0,
              'CharPosture': types.SimpleNamespace(typeName='com.sun.star.awt.FontSlant', value='NONE')}

    def getName(self): return 'Default'
    def isUserDefined(self): return False
    def getParentStyle(self): return ''
    def getPropertySetInfo(self): return Info()
    def getPropertyValue(self, name): return self.values[name]


class Settings:
    value = False

    def getPropertySetInfo(self):
        return types.SimpleNamespace(getPropertyByName=lambda name: types.SimpleNamespace(Type=types.SimpleNamespace(typeName='boolean')))

    def getPropertyValue(self, name):
        assert name == 'UsePrinterMetrics'
        return self.value


class Provider:
    locale = ''

    def createInstanceWithArguments(self, service, args):
        assert service == after.CONFIG_SERVICE
        if args[0].Value == after.SETUP_NODE:
            return Names({'ooSetupSystemLocale': self.locale})
        assert args[0].Value == after.SUBSTITUTION_NODE
        return static_names


provider, settings = Provider(), Settings()
ctx = types.SimpleNamespace(getValueByName=lambda name: provider,
    getServiceManager=lambda: types.SimpleNamespace(createInstanceWithContext=lambda service, context: settings))
style = Style()
model = types.SimpleNamespace(supportsService=lambda service: True,
    getStyleFamilies=lambda: types.SimpleNamespace(getByName=lambda name: types.SimpleNamespace(getByName=lambda name: style)))
kwargs = dict(property_value_factory=lambda name, value: types.SimpleNamespace(Name=name, Value=value),
    startup_locale_environment={'LC_ALL': 'C.UTF-8'}, stock_startup_locale_lifecycle=after.C_UTF8_STOCK_LOCALE_LIFECYCLE)
recipe = after.resolve_font_recipe(model, ctx, **kwargs)
check('inert_full_recipe_remains_Calibri_11_Swiss_normal', recipe['recipe'] == {'Name': 'Calibri', 'Height': 220, 'Family': 5, 'CharSet': 1, 'Weight': 100.0})
check('inert_full_recipe_void_observation_preserved', recipe['observations']['ms_name_transform']['observed_SubstFontsMS'] is None)
check('inert_recipe_authority_unchanged', recipe['authority'] == 'OBSERVATIONS_AND_CONDITIONAL_SOURCE_DERIVATION_ONLY')
check('inert_recipe_digest_uses_observed_nil', recipe['observation_sha256'] == after.observation_digest(recipe['observations']))
settings.value = True
check('printer_reference_condition_unchanged', refusal(after, lambda: after.resolve_font_recipe(model, ctx, **kwargs), 'TextWysiwyg_printer_reference_path_unsupported'))
settings.value = False
provider.locale = 'ru-RU'
check('locale_condition_unchanged', refusal(after, lambda: after.resolve_font_recipe(model, ctx, **kwargs), 'application_script_locale_outside_supported_en_US_branch'))
provider.locale = ''
bad_kwargs = dict(kwargs, stock_startup_locale_lifecycle='UNBOUND')
check('external_lifecycle_condition_unchanged', refusal(after, lambda: after.resolve_font_recipe(model, ctx, **bad_kwargs), 'C_UTF8_stock_startup_language_lifecycle_UNBOUND'))

result = {'schema': 'frw.cfb4.resolver-nil-delta-pure-checks.v1', 'status': 'PASS_SOURCE_ONLY',
    'test_count': len(checks), 'checks': checks,
    'real_input': {'path': str(REGISTRY), 'sha256': hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), 'meaning': 'Exact static registry schema/data; no actual UNO values'},
    'projection_limit': 'None is an explicitly inert projection of optional nil schema metadata and supported UNO-void representation; actual CFB4 UNO Any/Python value was not captured.',
    'effects': {'office': False, 'UNO': False, 'namespace': False, 'network': False, 'runtime_qualification': False},
    'actual_M': None, 'actual_case_accepted': False}
p = ROOT / 'CHECKS.json'
p.write_text(json.dumps(result, indent=2) + '\n')
p.chmod(0o600)
print(json.dumps({'status': result['status'], 'test_count': len(checks), 'checks_sha256': hashlib.sha256(p.read_bytes()).hexdigest()}))
