"""Pure Source checks with explicitly inert API facades; no real Office/UNO.

No import starts a process, connects to a service, reads a document, or measures.
Ordinary functions below are compiled from exact copied Source AST nodes.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
checks=[]
def check(name, value, **details):
    if not value: raise AssertionError(name)
    checks.append(dict(name=name,pass_source_only=True,**details))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path,name):
    module=types.ModuleType(name)
    exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
    return module
before=load(ROOT/'before/runtime_font_resolver.py','old_resolver')
after=load(ROOT/'candidate/qualifier/runtime_font_resolver.py','new_resolver')
leaf=load(ROOT/'candidate/qualifier/reference_metric_leaf_r2.py','new_leaf')
old_leaf=load(ROOT/'before/reference_metric_leaf_r2.py','old_leaf')
mapping=json.loads((ROOT/'native-table/MAP.json').read_text())
profile={int(k):tuple(v) for k,v in mapping['canonical_build_independent_profile'].items()}
check('reviewed_baselines_exact',sha(ROOT/'before/runtime_font_resolver.py')=='489c4c7fbecbc035a0e3dde8e95efee3f6bf4b716fe22743c6eaba4863b0d32e'
      and sha(ROOT/'before/reference_metric_leaf_r2.py')=='d0afe33b17f4da04268b01ed1b52af9b69961177e9367cd72a27f5eda221586c')
check('nearest_ordinary_consumers_exact',sha(ROOT/'before/ordinary/friday_workspace_calc_native_uno.py')=='ab298eeaa75c8c57f0bdaae819d41fdb58770bc116cbd357addfa5ee79b77637'
      and sha(ROOT/'before/ordinary/friday_workspace_calc_measured.py')=='94b131eae69fcf9098722cc9023013e29eb7742c9e842a95b923e9c571499707')
check('every_primary_hash_matches',all(sha(Path(r['path']))==r['sha256'] for r in mapping['source_records']),primary_files=len(mapping['source_records']))
check('complete_pinned_native_roster',len(mapping['entries'])==98 and mapping['checks']['table_entries']==97
      and mapping['checks']['aggregate_definitions']==88 and mapping['checks']['inverse_explicit_cases']==18)
check('candidate_exact_derived_canonical_profile',after.CHARSET_ROUNDTRIPS==profile and len(profile)==32)

# Revert only the intended executable charset changes, then compare full ASTs.
changed=ast.parse((ROOT/'candidate/qualifier/runtime_font_resolver.py').read_text())
old_ast=ast.parse((ROOT/'before/runtime_font_resolver.py').read_text())
old_function=next(x for x in old_ast.body if isinstance(x,ast.FunctionDef) and x.name=='resolve_font_recipe')
for node in changed.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHARSET_ROUNDTRIPS' for t in node.targets):
        node.value=ast.parse(repr(before.CHARSET_ROUNDTRIPS),mode='eval').body
    if isinstance(node,ast.FunctionDef) and node.name=='resolve_font_recipe':
        node.body[0].value=copy.deepcopy(old_function.body[0].value)
        for item in ast.walk(node):
            if isinstance(item,ast.Dict):
                for i,key in enumerate(item.keys):
                    if isinstance(key,ast.Constant) and key.value=='source_derived_RTL_encoding':
                        item.values[i]=ast.parse('65535 if charset == -1 else charset',mode='eval').body
check('resolver_all_other_AST_unchanged',ast.dump(changed,include_attributes=False)==ast.dump(old_ast,include_attributes=False))
new_leaf=(ROOT/'candidate/qualifier/reference_metric_leaf_r2.py').read_text()
reversed_leaf=new_leaf.replace("and nominal['CharSet'] in "+repr(tuple(sorted(profile)))+',',
    "and (nominal['CharSet'] == -1 or 0 <= nominal['CharSet'] < 65536),")
check('R2_only_charset_guard_AST_delta',ast.dump(ast.parse(reversed_leaf),include_attributes=False)==ast.dump(ast.parse((ROOT/'before/reference_metric_leaf_r2.py').read_text()),include_attributes=False))
check('R2_full_actual_equality_and_export_guard_preserved',"require(actual == bound['source_font'], 'source_Default_font_changed')" in new_leaf
      and "type(recipe['CharSet']) is int and 0 <= recipe['CharSet'] < 65536" in new_leaf)

class Names:
    def __init__(self,values): self.values=values
    def getElementNames(self): return tuple(self.values)
    def getByName(self,name):
        value=self.values[name]
        return Names(value) if type(value) is dict else value
class Style:
    def __init__(self,charset):
        self.values={'CharFontName':'Calibri','CharHeight':11.0,'CharFontFamily':5,
            'CharFontCharSet':charset,'CharWeight':100.0,
            'CharPosture':types.SimpleNamespace(typeName='com.sun.star.awt.FontSlant',value='NONE')}
        self.charset_schema='short'
    def getName(self): return 'Default'
    def isUserDefined(self): return False
    def getParentStyle(self): return ''
    def getPropertySetInfo(self):
        return types.SimpleNamespace(getPropertyByName=lambda name:types.SimpleNamespace(Type=types.SimpleNamespace(typeName=self.charset_schema if name=='CharFontCharSet' else after.PROPERTY_TYPES[name])))
    def getPropertyValue(self,name): return self.values[name]
class Settings:
    value=False
    def getPropertySetInfo(self):
        return types.SimpleNamespace(getPropertyByName=lambda name:types.SimpleNamespace(Type=types.SimpleNamespace(typeName='boolean')))
    def getPropertyValue(self,name):
        assert name=='UsePrinterMetrics'
        return self.value
class Provider:
    locale=''
    raw_ms=None
    def createInstanceWithArguments(self,service,args):
        assert service==after.CONFIG_SERVICE
        if args[0].Value==after.SETUP_NODE: return Names({'ooSetupSystemLocale':self.locale})
        assert args[0].Value==after.SUBSTITUTION_NODE
        return Names({'en':{'calibri':{'SubstFontsMS':self.raw_ms}}})
class Context:
    def __init__(self): self.provider=Provider();self.settings=Settings();self.provider_reads=0
    def getValueByName(self,name):
        assert name==after.DEFAULT_PROVIDER
        self.provider_reads+=1
        return self.provider
    def getServiceManager(self):
        return types.SimpleNamespace(createInstanceWithContext=lambda service,context:self.settings)
class Model:
    def __init__(self,style): self.style=style
    def supportsService(self,service): return service=='com.sun.star.sheet.SpreadsheetDocument'
    def getStyleFamilies(self): return types.SimpleNamespace(getByName=lambda name:types.SimpleNamespace(getByName=lambda name:self.style))
    def getURL(self): return 'file:///home/jericho/.cache/INERT-SOURCE-CHECK/source.ods'
    def isReadonly(self): return True
    def isModified(self): return False
    def getPropertyValue(self,name):
        assert name=='ReferenceDevice'
        return None # Deliberate refusal before font/device/digit operations.
kwargs=dict(property_value_factory=lambda name,value:types.SimpleNamespace(Name=name,Value=value),
    startup_locale_environment={'LC_ALL':'C.UTF-8'},stock_startup_locale_lifecycle=after.C_UTF8_STOCK_LOCALE_LIFECYCLE)
def resolve(module,charset,context=None):
    return module.resolve_font_recipe(Model(Style(charset)),context or Context(),**kwargs)
def refusal(module,call,code):
    try: call()
    except (module.FontResolutionRefused if hasattr(module,'FontResolutionRefused') else module.Unbound) as e:
        return (getattr(e,'code',None) or str(e))==code
    return False
def source_context(output):
    return dict(schema='frw.Root.calc-reference-metric-qualified-context.v2',
        source_sha256=leaf.SOURCE_SHA256,source_bytes=leaf.SOURCE_BYTES,
        working_copy_url=Model(Style(0)).getURL(),working_copy_sha256_before=leaf.SOURCE_SHA256,
        working_copy_bytes=leaf.SOURCE_BYTES,producer_version=leaf.VERSION,
        reviewed_source_commit=leaf.SOURCE_COMMIT,
        components={r:dict(expected_sha256='0'*64,observed_sha256='0'*64) for r in leaf.COMPONENT_ROLES},
        standalone_non_LOK=True,same_reference_state=True,no_concurrent_device_user=True,
        native_width_transport=dict(mode='RAW32_POSTQUERY_NATIVE_JOIN',native_min=None,native_max=None,proof_sha256=None),
        default_script='LATIN',source_style_name='Default',source_font=copy.deepcopy(output['source_nominal_font']),
        export_descriptor=dict(leaf.DEFAULTS,**output['recipe']),
        load_policy=dict(read_only=True,hidden=True,macros='NEVER_EXECUTE',links='NO_UPDATE',interaction='ABORT_ONLY',network='OS_NAMESPACE_DENY',profile='FRESH_PRIVATE_NO_RESTORE',store_render_draw_conversion=False),
        evidence={r:dict(basis='ROOT_EXTERNAL_RECORD',sha256='0'*64) for r in leaf.EVIDENCE_ROLES})
outputs={}
for raw,(win,export) in profile.items():
    out=resolve(after,raw);outputs[raw]=out
    check('named_source_exact_roundtrip_'+str(raw),out['observations']['charset_roundtrip']==dict(
        observed_source_UNO_short=raw,source_derived_RTL_encoding=raw%65536,
        source_derived_Windows_charset_byte=win,source_derived_export_RTL_encoding=export))
    check('raw_observation_and_digest_'+str(raw),out['source_nominal_font']['CharSet']==raw
        and out['observations']['style']['font']['CharSet']==raw
        and out['observation_sha256']==after.observation_digest(out['observations'])
        and out['authority']=='OBSERVATIONS_AND_CONDITIONAL_SOURCE_DERIVATION_ONLY')
    ctx=source_context(out)
    check('R2_synthetic_context_and_full_actual_reread_'+str(raw),leaf.validate_root_context(ctx,leaf.qualification_sha256(ctx)) is ctx
        and refusal(leaf,lambda:leaf.observe_reference_metric(Model(Style(raw)),ctx,leaf.qualification_sha256(ctx),before_digit=lambda *a:None,after_digit=lambda *a:None),'exact_reference_device_capability_required'))
    wrong=copy.deepcopy(ctx);wrong['source_font']['CharSet']=0 if raw!=0 else 1
    check('R2_changed_actual_charset_refuses_'+str(raw),refusal(leaf,lambda:leaf.observe_reference_metric(Model(Style(raw)),wrong,leaf.qualification_sha256(wrong),before_digit=lambda *a:None,after_digit=lambda *a:None),'source_Default_font_changed'))
for raw in [-1,0,1]:
    check('prior_supported_branch_byte_equivalent_'+str(raw),resolve(before,raw)==outputs[raw])
check('UTF8_is_native_direct_76_to_Windows0_to_RTL1',outputs[76]['recipe']['CharSet']==1)
check('previous_profile_rejects_UTF8_not_proof_native_unsupported',refusal(before,lambda:resolve(before,76),'source_charset_roundtrip_unsupported'))
rejected=0
for raw in range(-32768,32768):
    if raw in profile: continue
    context=Context()
    if not refusal(after,lambda:resolve(after,raw,context),'source_charset_roundtrip_unsupported') or context.provider_reads:
        raise AssertionError(('outside-profile int accepted/config-read',raw))
    rejected+=1
check('exhaustive_other_UNO_short_values_refuse_before_config',rejected==65536-len(profile),rejected_values=rejected)
check('every_noncanonical_defined_native_encoding_refuses',all(e['UNO_short'] not in profile for e in mapping['entries'] if not e['canonical_export_profile']))
class IntSubclass(int): pass
for index,raw in enumerate([True,False,-1.0,76.0,'76',b'76',None,[],{},IntSubclass(76),-32769,32768,65534,65535,65536]):
    context=Context()
    check('nonexact_short_type_or_range_'+str(index),refusal(after,lambda:resolve(after,raw,context),'source_charset_roundtrip_unsupported') and context.provider_reads==0)
style=Style(76);style.charset_schema='unsigned short'
check('wrong_API_charset_metadata_refuses',refusal(after,lambda:after.resolve_font_recipe(Model(style),Context(),**kwargs),'property_schema_mismatch'))
style=Style(76);del style.values['CharFontCharSet'];context=Context()
try: after.resolve_font_recipe(Model(style),context,**kwargs)
except KeyError: missing=True
else: missing=False
check('missing_API_charset_never_defaults_or_reads_config',missing and context.provider_reads==0)
for raw in [-32768,-3,9,97,32767,32768,65535,True,76.0,'76',None]:
    ctx=source_context(outputs[76]);ctx['source_font']['CharSet']=raw
    check('R2_source_guard_exact_named_profile_'+str(len(checks)),refusal(leaf,lambda:leaf.validate_root_context(ctx,leaf.qualification_sha256(ctx)),'qualified_source_Normal_font_required'))
for raw in [-2,-1,65536,True,1.0]:
    ctx=source_context(outputs[76]);ctx['export_descriptor']['CharSet']=raw
    check('R2_export_guard_preserved_'+str(len(checks)),refusal(leaf,lambda:leaf.validate_root_context(ctx,leaf.qualification_sha256(ctx)),'qualified_export_font_transform_UNBOUND'))

# Exercise the actual nearest ordinary _font and descriptor guard Source nodes.
def selected(path,names,environment):
    tree=ast.parse(path.read_text())
    picked=[n for n in tree.body if (isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names)
        or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets))]
    exec(compile(ast.Module(body=picked,type_ignores=[]),str(path),'exec'),environment)
ordinary={}
selected(ROOT/'before/ordinary/friday_workspace_calc_measured.py',{'_font'},ordinary)
native={'math':math,'re':re}
selected(ROOT/'before/ordinary/friday_workspace_calc_native_uno.py',{'UnoConstructionRefused','need','_DESCRIPTOR_TYPES','_descriptor_values'},native)
package=types.ModuleType('hermes_cli');package.__path__=[]
resolver_module=types.ModuleType('hermes_cli.friday_workspace_calc_font_resolver')
resolver_module.resolve_font_recipe=after.resolve_font_recipe
previous={name:sys.modules.get(name) for name in ('hermes_cli','hermes_cli.friday_workspace_calc_font_resolver')}
sys.modules['hermes_cli']=package;sys.modules[resolver_module.__name__]=resolver_module
try:
    for raw,out in outputs.items():
        result=ordinary['_font'](Model(Style(raw)),Context(),kwargs['property_value_factory'],
            dict(startup_locale_environment=kwargs['startup_locale_environment'],stock_startup_locale_lifecycle=kwargs['stock_startup_locale_lifecycle']))
        descriptor=dict(leaf.DEFAULTS,**result['recipe'])
        check('actual_ordinary_whole_result_and_clean_descriptor_'+str(raw),result==out and native['_descriptor_values'](descriptor) is descriptor)
    sentinel=object();calls=[]
    resolver_module.resolve_font_recipe=lambda *a,**k:(calls.append((a,k)) or sentinel)
    result=ordinary['_font']('doc','context','pv',dict(startup_locale_environment={'LC_ALL':'C.UTF-8'},stock_startup_locale_lifecycle='token'))
    check('actual_ordinary_font_preserves_whole_return_object',result is sentinel and calls==[(('doc','context'),dict(property_value_factory='pv',startup_locale_environment={'LC_ALL':'C.UTF-8'},stock_startup_locale_lifecycle='token'))])
finally:
    for name,value in previous.items():
        if value is None: sys.modules.pop(name,None)
        else: sys.modules[name]=value
for raw in [-2,-1,2,10,76,65535,True,1.0]:
    descriptor=dict(leaf.DEFAULTS,**outputs[76]['recipe']);descriptor['CharSet']=raw
    try: native['_descriptor_values'](descriptor)
    except native['UnoConstructionRefused']: rejected=True
    else: rejected=False
    check('actual_ordinary_export_stays_exact_int0or1_'+str(len(checks)),rejected)

result=dict(schema='frw.complete-charset-contract.Source-checks.v1',status='PASS_SOURCE_ONLY',
    test_count=len(checks),checks=checks,supported_named_source_shorts=sorted(profile),
    exhaustive_rejected_other_short_values=65536-len(profile),
    scope='Inert facades; exact nearest R2 and ordinary Source consumers. No synthetic runtime record, authority, digits, widths or M.',
    effects=dict(UNO=False,Office=False,namespace=False,admission=False,measurement=False,digits=False,network=False),
    actual_3ed5_charset='UNKNOWN_NOT_CAPTURED',actual_M=None,runtime_accepted=False)
p=ROOT/'CHECKS.json';p.write_text(json.dumps(result,indent=2)+'\n');p.chmod(0o600)
print(json.dumps(dict(status=result['status'],test_count=len(checks),checks_sha256=sha(p))))
