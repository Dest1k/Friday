#!/usr/bin/env python3
"""Generate only an inert Root228 Source sibling, never read current or install."""
import argparse,ast,hashlib,json,os,re,stat,types
from pathlib import Path
OWN=Path(__file__).parent
R1=OWN.parent/'source-frame228-unbound'
BASE=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE227-ROOT-SOURCE-INTEGRATION-20261116/bound-source-frame227-0f098a35-r5')
CORE=Path('/home/jericho/.cache/FRW-SOL-V3-COMMUNICATION228-SOURCE-INTEGRATION-CORE-20261116')
OLD='0f098a354033317fe4cf20dd7a225ad5b2442361'
PRODUCT='c1cb63f7ac7ed7c378d6638afeef7bb73c77080c'
PRODUCT='c1cb63f7ac7ed7c378d6638afeef7bb73c77080c'
KEYS={'product_source_commit','execution_commit','new_request','private_input','public_input','before_public_input','actual227_binding','closed227_authentication','durable227_cutoff'}

def require(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def checked(path,pin=None):
 p=Path(path);a=p.lstat();require(stat.S_ISREG(a.st_mode)and a.st_uid==os.getuid()and a.st_nlink==1 and not any(q.is_symlink()for q in(p,*p.parents)),'owned_exact_Source')
 raw=p.read_bytes();b=p.lstat();fields=('st_dev','st_ino','st_uid','st_gid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns');require(all(getattr(a,k)==getattr(b,k)for k in fields),'Source_identity_CAS');require(pin is None or sha(raw)==pin,'Source_sha');return raw
def write(p,raw):
 p.parent.mkdir(mode=0o700,parents=True,exist_ok=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(raw)
def replace_func(s,name,raw):
 t=ast.parse(s);n=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name==name);lines=s.splitlines(True);lines[n.lineno-1:n.end_lineno]=[raw.rstrip()+'\n'];return ''.join(lines)
def assign(s,name,v):
 t=ast.parse(s);n=next(n for n in t.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets));lines=s.splitlines(True);lines[n.lineno-1:n.end_lineno]=[name+' = '+repr(v)+'\n'];return ''.join(lines)
STRINGS={
 'core-communication-memory-after-source226':'communication-create-contract-after-source227',
 'CORE_COMMUNICATION_MEMORY':'COMMUNICATION_CREATE_CONTRACT',
 'ROOT-native226':'ROOT-native228',
 'ROOT-NATIVE226-CUSTODY-RELEASE':'ROOT-NATIVE228-CUSTODY-RELEASE',
 '35d5f4fe901dc4c11e43f52c65949e843c70de5c':OLD,
 '1644a836964162d5bdd9f86d5280988fc0e2112b3c1414d0214db6e2f493388f':'a7eff51998620b4af519c066e480af9895beb63451b188e7e26a2c9efb52edb0',
 'c0921fbd5674e934915d3c69cc362a61d8ac2481117f1566160c070aaf632e6c':'26e0a0c574d915360e109cfc78156a0435f22e4ffef4f44858706065a7ade95d',
 '04ce31a1c497084f93deea6cb2cee76a9f4c83a9df6851f2fe365d973272256e':'1644a836964162d5bdd9f86d5280988fc0e2112b3c1414d0214db6e2f493388f',
 '2fa298ac26325417a20ab9844ae5f709079e16db1c4fd300fd903646ee6fde0a':'c0921fbd5674e934915d3c69cc362a61d8ac2481117f1566160c070aaf632e6c',
 'f3206ed54fcdcea18dc2bff83e792c5b422ec8d86991b0748be70a3708be1969':'7376080ed7b4c49bf2af9dd26d89e000e194d31ca110be553e1c57c8613df07e',
 '3c0463144860c0ec25d30897c9e24757c7c2e0c8a7564129554ef36731124b2b':'36fff704a81cbce1098f81ce376eb5128264c8b35ea618accdab527acadb6a55',
 '9e038fa3c017466848632bb58542010334d8dc38177d30d4484166757a0ff39a':'22555dd018a59c7f4950195bb1c1ccf6ef54162b85a307aea5bc146eea339a46',
 '22555dd018a59c7f4950195bb1c1ccf6ef54162b85a307aea5bc146eea339a46':'4892163bc556e7d7dbf22b2d85a519eeae2a12c23252727f198dc3f0a45086f1',
 '9e65245f445b486fad4445b549360698066726f74006fe236db5afd26d79041e':'e47010a840e2eee2c6c47acb4a5bcd97362ea5575e2f25a5a33887b387890d84',
 '141c5177b42e73f8c0783f7c54760fa693ad0510e673257e1dc26f0399ae2371':'053bd77a42231610d56dc322ef5fe10c922f24d89add82bd11673005a9f373a0',
 'friday.current-source-native-successor.v29':'friday.current-source-native-successor.v30',
}
NUMBER={226:227,227:228,533:535,535:537,17893:17892}
NAMES={}
for prefix in ('native','Native','NATIVE','root','Root','ROOT-','PRODUCT','EXACT','NEW','FUTURE','SOURCE','INSTALLED','CURRENT','candidate','CANDIDATE','FORWARD','_before','source','Source'):
 NAMES[prefix+'227']=prefix+'228'
for prefix in ('native','Native','NATIVE','Root','actual','ACTUAL','OLD','old','CURRENT','source','Source','predecessor'):
 NAMES[prefix+'226']=prefix+'227'
NAMES.update({'PROJECT533':'PROJECT535','core227':'core228','v29_whole':'v30_whole','installed227':'installed228','durable226':'durable227','completed226':'completed227'})
def migrate_text(s):
 mapping={**STRINGS,**NAMES};pattern='|'.join(re.escape(k)for k in sorted(mapping,key=len,reverse=True))+r'|(?<![0-9a-f])(?:227|226|535|533|17893)(?![0-9a-f])'
 return re.sub(pattern,lambda m:mapping[m.group()]if m.group()in mapping else str(NUMBER[int(m.group())]),s)
class Migrate(ast.NodeTransformer):
 def visit_Global(self,n):n.names=[migrate_text(x)for x in n.names];return n
 def visit_Nonlocal(self,n):n.names=[migrate_text(x)for x in n.names];return n
 def visit_Name(self,n):n.id=migrate_text(n.id);return n
 def visit_FunctionDef(self,n):n.name=migrate_text(n.name);self.generic_visit(n);return n
 def visit_Attribute(self,n):n.attr=migrate_text(n.attr);self.generic_visit(n);return n
 def visit_keyword(self,n):
  if n.arg is not None:n.arg=migrate_text(n.arg)
  self.generic_visit(n);return n
 def visit_Constant(self,n):
  if type(n.value)is int and n.value in NUMBER:n.value=NUMBER[n.value]
  elif type(n.value)is str:n.value=migrate_text(n.value)
  return n

def migrate(s):return ast.unparse(ast.fix_missing_locations(Migrate().visit(ast.parse(s))))+'\n'
GATE='''ROOT_SOURCE_BINDINGS = %s
ROOT_BINDING_KEYS = set(%r)
def require_root_source_bindings():
    value=ROOT_SOURCE_BINDINGS
    if type(value)is not dict or set(value)!=ROOT_BINDING_KEYS:raise ValueError('Root228_Source_selectors_UNBOUND_before_runtime_IO')
    def digest(v,n=64):return type(v)is str and len(v)==n and all(c in '0123456789abcdef'for c in v)
    if not (digest(value['product_source_commit'],40)and value['product_source_commit']!='%s'and value['product_source_commit']=='c1cb63f7ac7ed7c378d6638afeef7bb73c77080c'and digest(value['execution_commit'],40)):raise ValueError('Root228_new_product_execution_UNBOUND_before_runtime_IO')
    for key in ROOT_BINDING_KEYS-{'product_source_commit','execution_commit'}:
        ref=value[key]
        if not(type(ref)is dict and set(ref)=={'path','sha256'}and type(ref['path'])is str and ref['path'].startswith('/home/jericho/.cache/')and 'UNBOUND'not in ref['path']and '..'not in ref['path'].split('/')and digest(ref['sha256'])):raise ValueError('Root228_exact_Source_ref_UNBOUND_before_runtime_IO:'+key)
    return value
'''
def gate(s,binding):
 s=s.replace('    if SOURCE_BOUND is not True:', '    require_root_source_bindings()\n    if SOURCE_BOUND is not True:',1)
 return GATE%(repr(binding),tuple(sorted(KEYS)),OLD)+'\n'+s

def main():
 p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,default=OWN/'operational-source228-unbound');p.add_argument('--root-bindings',type=Path);a=p.parse_args();require(a.destination.parent==OWN and not a.destination.exists(),'new_owned_Source_sibling_only')
 binding='UNBOUND_ROOT';extra={}
 if a.root_bindings:
  config=json.loads(checked(a.root_bindings));require(set(config)=={'selectors','source_refs'},'Root_ref_only_binding_ABI');binding=config['selectors'];extra=config['source_refs'];scope={};exec(GATE%(repr(binding),tuple(sorted(KEYS)),OLD),scope);scope['require_root_source_bindings']()
 spec=json.loads(checked(CORE/'SOURCE-SPEC228.json','b2c871e242d5d2f4f541f62d905d7e6c539020fb9041d1a657b8bb90ea20fee2'));rows=spec['native_files'];counts=spec['counts']
 oldnames=['run_native227_once.py','resume_native227_services.py','core227-first-actual-root.py','root227_metadata.py','root227_data.py','root227_projection.py','native227_binding.py','boundary_contract.py','cutoff_contract.py','recovery_scope.py','native_scope_preflight226.py','native_scope_post227.py','bind_current_inputs227.py','prepare_root227.py']
 names={n:migrate_text(n)for n in oldnames};base={n:checked(BASE/n).decode()for n in oldnames};source={names[n]:migrate(s)for n,s in base.items()}
 for n in ('actor_static_inputs228.py','root228_source_seam.py','read_static_source_inputs228.py'):source[n]=checked(R1/n).decode()
 for n,s in list(source.items()):
  assigns={t.id for node in ast.parse(s).body if isinstance(node,ast.Assign)for t in node.targets if isinstance(t,ast.Name)}
  if 'NATIVE_ROWS'in assigns:s=assign(s,'NATIVE_ROWS',rows)
  if 'COUNTS'in assigns:s=assign(s,'COUNTS',counts)
  source[n]=s
 actor=source['run_native228_once.py']
 actor=replace_func(actor,'read_static_source_inputs',"""def read_static_source_inputs(*,manifest,bound,request_path=None):
    require_source_bound()
    bind_source_data(manifest_sha256(manifest))
    seam=module_source(B/'root228_source_seam.py');spec_ref=manifest['source_spec_ref']
    return seam.read_static_source_inputs(manifest=manifest,bound=bound,route=dict(home=str(H),previous_project=str(P),candidate_project=str(C),native_spec=str(SPEC),request=str(REQ if request_path is None else request_path)),selection_aliases=dict(admission=dict(native_spec=spec_ref),qualification=dict(native_spec=spec_ref,operational_input=bound['current_input'])))
""")
 actor=replace_func(actor,'checked_native_settlement',"""def checked_native_settlement(before_receipt,receipt,targets,native_additions,*,publisher_code):
    return module_source(B/'root228_source_seam.py').checked_native_settlement(before_receipt,receipt,targets,native_additions,publisher_code=publisher_code)
""");source['run_native228_once.py']=actor
 nb=re.sub(r'== 2(?![0-9])','== 3',source['native228_binding.py']);nb=re.sub(r'== 8(?![0-9])','== 9',nb).replace('native_targets=2','native_targets=3').replace('selected_target_count=8','selected_target_count=9').replace('dict(touched=2, added=0, modified=2)','dict(touched=3, added=0, modified=3)')
 for key,value in dict(REQUEST_SHA=binding['new_request']['sha256']if type(binding)is dict else'UNBOUND_ROOT',INPUT_SHA=binding['private_input']['sha256']if type(binding)is dict else'UNBOUND_ROOT',CONSUMER='__FRAME__/publication/friday_v3_layer_publication.py',CONSUMER_SHA='8732011ea9d831d2eb84f1bf2c2c5e5196fe1a016fbf29ac7fa972a8604ce8d3',REQUEST='__FRAME__/ROOT-FRESH-REQUEST.json',STATIC_BINDING_SHA256='UNBOUND_ROOT',PREVIOUS_PROJECT='UNBOUND_ROOT',NATIVE_PREIMAGES={r['path']:dict(sha256=r['before_sha256'],bytes=len(checked(CORE/'native/before'/r['path'])),mode='100644')for r in rows}).items():nb=assign(nb,key,value)
 nb=nb.replace('dict(touched=2, added=0, modified=2)','dict(touched=3, added=0, modified=3)')
 source['native228_binding.py']=nb
 data=source['root228_data.py'].replace("len(value['native_after']) == 2","len(value['native_after']) == 3")
 data=data.replace("pinned(B / 'ROOT228-DATA-BINDINGS.json')","pinned(B / 'ROOT228-DATA-BINDINGS.json')")
 data=data.replace("source_module('native228_binding', descriptor['dependencies']['native228_binding'], raw_refs).bind_static(","bound_native_module(descriptor,raw_refs).bind_static(")
 data=re.sub(r"    require\(descriptor\['project_roots'\]\['previous'\] == '[^']*', 'exact_previous_private(?:533|535)_root_required'\)\n",'',data)
 data=data.replace("for role in ('manifest', 'patch'):\n        r = spec[role]","for role in ('manifest', 'patch'):\n        r = spec[role]\n        raw_refs[r['path']]=pinned(r['path'])")
 data=data.replace("fixed = descriptor['fixed']","fixed = descriptor['fixed']\n    for key in ('new_request','private_input','public_input','before_public_input','actual227_binding'):\n        fixedkey='request' if key=='new_request' else key\n        require(fixed[fixedkey]==ROOT_SOURCE_BINDINGS[key],'Root_selector_descriptor_alias_required:'+key)\n    for key,ref in ROOT_SOURCE_BINDINGS.items():\n        if type(ref)is dict:require(pins.get(ref['path'])==ref['sha256'],'Root_selector_external_pin_required:'+key)")
 data=replace_func(data,'prepare_planned_data',"def prepare_planned_data(**kwargs):\n    raise ValueError('R1_Source_projection_reused_actual_descriptor_requires_Root_binding')")
 data+='''\ndef bound_native_module(descriptor,raw_refs):
    m=source_module('native228_binding',descriptor['dependencies']['native228_binding'],raw_refs)
    m.PREVIOUS_PROJECT=descriptor['project_roots']['previous']
    return m
''';source['root228_data.py']=data
 meta=source['root228_metadata.py'];start=meta.index("    require(spec['schema']",meta.index('def validate_candidate'));end=meta.index("    require(source_readref(data['native_spec'])",start)
 meta=meta[:start]+"""    require(spec['schema']=='frw.sol.communication228.final-integration-Source-spec.v1'and spec['source_only']is True and spec['current_admission']is False and spec['execution_grant']is False and spec['install_ready']is False and spec['layer']==LAYER,'exact_Source228_spec')
    require(spec['counts']==dict(added=0,after_layers=228,after_project=537,base=17730,before_layers=227,before_project=535,modified=3,native=17895,plugins=52,retained=17892,selected_CAS=9),'exact_Source228_counts')
    require(spec['native_files']==binding['native_files']and binding['selected_target_count']==spec['counts']['selected_CAS']==len(spec['native_files'])+6 and data['fixed']['native_spec']==data['native_spec']and data['source_refs'][data['native_spec']['path']]==data['native_spec']['sha256'],'Source228_CAS9_join')
"""+meta[end:];source['root228_metadata.py']=meta
 proj=source['root228_projection.py'].replace('frw.core228.pair-spec.r2',spec['schema']).replace("spec['selected_targets'] == 8","spec['counts']['selected_CAS'] == 9").replace("('current_authority', 'execution_grant', 'installed228')","('current_admission', 'execution_grant', 'install_ready')").replace("static_binding['selected_target_count'] == 8","static_binding['selected_target_count'] == 9").replace("static_binding['native_targets'] == 2","static_binding['native_targets'] == 3").replace('native_targets=2','native_targets=3').replace('CAS_targets=8','CAS_targets=9');source['root228_projection.py']=proj
 source['recovery_scope.py']=source['recovery_scope.py'].replace("'ROOT-NATIVE228-LIVE-OPERATION.json'","'ROOT-NATIVE226-LIVE-OPERATION.json', '.ROOT-NATIVE226-LIVE-OPERATION.json.pending', 'ROOT-NATIVE228-LIVE-OPERATION.json'")
 source['predecessor227.py']=checked(OWN/'predecessor227_template.py').decode().replace('__METADATA_LITERAL__',repr(json.loads(checked(BASE.parent/'ROOT-ACTUAL227-EIGHT-IDENTITY-METADATA-SOURCE-ONLY.json','a91b59cc58ce66377471b9c3eed13614f8dc7d69e145d20ecb3ae9874db1feac'))))
 source['frame_source.py']=checked(OWN/'frame_source_template.py').decode()
 source['read_source_bound228.py']=checked(OWN/'read_source_bound228_template.py').decode()
 for n,s in list(source.items()):
  if n in ('root228_data.py','root228_metadata.py','root228_projection.py'):
   s=s.replace("spec[role]","spec['pair'][role]").replace("spec['manifest']","spec['pair']['manifest']").replace("spec['patch']","spec['pair']['patch']")
  if 'def require_source_bound():'in s or n in ('predecessor227.py',):s=gate(s,binding)
  source[n]=s.replace('__FRAME__',str(a.destination))
 a.destination.mkdir(mode=0o700)
 for n,s in source.items():compile(s,n,'exec');write(a.destination/n,s.encode())
 for n in ('build-layer-publication-request.py','friday_v3_layer_publication.py'):write(a.destination/'publication'/n,checked(CORE/'builder-publisher/publication'/n))
 write(a.destination/'SOURCE-SPEC228.json',checked(CORE/'SOURCE-SPEC228.json'))
 write(a.destination/'ROOT-SOURCE-BINDINGS-TEMPLATE.json',encoded(dict(selectors={k:'UNBOUND_ROOT'for k in sorted(KEYS)},source_refs={})))
 pins={str(p):sha(checked(p))for p in a.destination.rglob('*')if p.is_file()}
 for role in ('manifest','patch'):
  ref=spec['pair'][role];checked(ref['path'],ref['sha256']);pins[ref['path']]=ref['sha256']
 for path,pin in extra.items():checked(path,pin);pins[path]=pin
 manifest=dict(schema='frw.root228.coherent-after-actual227-source-pins.v1',source_only=True,runtime_grant=False,current_admission=False,source_refs=pins,historical_refs={},source_spec_ref=dict(path=str(a.destination/'SOURCE-SPEC228.json'),sha256=sha(checked(a.destination/'SOURCE-SPEC228.json'))),product_source_commit=binding['product_source_commit']if type(binding)is dict else PRODUCT,execution_commit=binding['execution_commit']if type(binding)is dict else'UNBOUND_ROOT',root_inputs_bound=type(binding)is dict,counts=counts)
 write(a.destination/'SOURCE-PINS.json',encoded(manifest))
 reused={};changed={}
 for old,s in base.items():
  def fs(t):return{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(t).body if isinstance(n,ast.FunctionDef)}
  expected=fs(migrate(s));actual=fs(source[names[old]])
  reused[names[old]]=[n for n in expected if expected[n]==actual.get(n)];changed[names[old]]=[n for n in expected if expected[n]!=actual.get(n)]
 write(a.destination/'AST-REUSE.json',encoded(dict(source_only=True,comparison='AST exact after explicitly enumerated version/count/hash/identity migration; changed function bodies listed separately',reused=reused,changed=changed)))
 print(json.dumps(dict(frame=str(a.destination),Source_pins_sha256=sha(encoded(manifest)),source_only=True,install_ready=False)))
if __name__=='__main__':main()
