"""Finite Source assembly from exact reviewed legacy pins; no H reads/effects."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import difflib
import os

OUT=Path(__file__).resolve().parent
OLD=Path('/home/jericho/.cache/FRW-SOL-V3-HTML-V01-PARAMETRIC-ROOT-CONSTRUCTOR-CORE-20261117')
N=Path('/home/jericho/.cache/FRW-ASTRA-CORE229-DOCUMENT-AND-ANCHOR-ROOT-20261117/candidate-r1')
ROOT='/home/jericho/.cache/FRW-ASTRA-HTML-V01-EDIT229-ROOT-20261117'
os.umask(0o077)
def read(p,want):
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==want,(str(p),'pin');return raw
old=read(OLD/'constructor_r1.py','d9291cc90a72cb0ddb53606e35d8becde1faac452004ee1a72e12341ad98b97d')
tree=ast.parse(old)
f=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='FROZEN'for a in n.targets)))
core=read(OLD/'builder_core_r1.py','ce4ab86ea7ea8ee980b9af3ce6bd6ebcf9c66c247b9e7135e015f4faae40e072').decode()
metadata=read(Path(f['static_dependencies']['fixed228_metadata']['path']),f['static_dependencies']['fixed228_metadata']['sha256'])
candidate=json.loads(read(N/'ROOT-COMBINED-NATIVE-SOURCE-R1.json','d17794878c8b2cce295f8e0314b7f5612503776cca74baa5d9244955976b1a94'))
native7={r['path']:dict(path=f['baseline_source18']['tools/file_tools.py']['path'].removesuffix('tools/file_tools.py')+r['path'],bytes=r['after']['bytes'],sha256=r['after']['sha256'])for r in candidate['changes']}
def assignments(raw,values):
 lines=raw.decode().splitlines(keepends=True)
 nodes={n.targets[0].id:n for n in ast.parse(raw).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
 for name,value in sorted(values.items(),key=lambda x:nodes[x[0]].lineno,reverse=True):
  n=nodes[name];lines[n.lineno-1:n.end_lineno]=[name+' = '+repr(value)+'\n']
 return ''.join(lines).encode()
def one(s,a,b):
 assert s.count(a)==1,('seam',a,s.count(a));return s.replace(a,b)
def version(raw):
 # Explicit identifiers/labels only; never rewrite digest substrings or history.
 for a,b in [('EDIT228','EDIT229'),('Edit228','Edit229'),('edit228','edit229'),('HTML228','HTML229'),('RootHTML228','RootHTML229'),('INSTALLED228','INSTALLED229'),('installed228','installed229'),('fixed228','fixed229'),('FIXED228','FIXED229'),('EXACT228','EXACT229'),('ROOT228','ROOT229'),('Root228','Root229'),('actual228','actual229'),('CLOSED228','CLOSED229'),('DOCX228','DOCX229'),('NATIVE228','NATIVE229'),('DELIVERY228','DELIVERY229')]:raw=raw.replace(a.encode(),b.encode())
 return raw

f['legacy_constructor']=dict(path=str(OLD/'constructor_r1.py'),bytes=len(old),sha256=hashlib.sha256(old).hexdigest())
f['candidate229']=candidate
input_path=N.parent/'root-inputs-source/INPUT-CORE229.private.SOURCE-ONLY.json'
input_raw=read(input_path,'8cbcf0ee9c580386875d13ee6072eb53c1af0c3ead7b1926de0f00568f4ff501')
input_doc=json.loads(input_raw);assert len(input_doc['project_files'])==539
f['candidate_input229']=dict(path=str(input_path),bytes=len(input_raw),sha256=hashlib.sha256(input_raw).hexdigest())
f['native7']=native7
f['baseline_source23']={**f.pop('baseline_source18'),**native7}
f['text_roles']={**f['text_roles'],**{k:native7[k]for k in ('tools/file_tools.py','hermes_cli/friday_user_scope.py','hermes_cli/friday_workspace_text.py')}}
assert len(f['baseline_source23'])==23 and len(f['text_roles'])==8
old_preparation=f['templates']['preparation']
profile=ast.literal_eval(next(n.value for n in ast.parse(old_preparation).body if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='PROFILE'for a in n.targets)))
profile['source']['path']=ROOT+'/fixtures/mayak-html-v01.html'
for k in f['templates']:f['templates'][k]=version(f['templates'][k])
f['templates']['preparation']=assignments(f['templates']['preparation'],dict(PROFILE=profile,ROOT_BINDING=dict(state='ROOT_UNBOUND',installed_target=229,current_admission=False,execution_grant=False)))
f['templates']['current']=assignments(f['templates']['current'],dict(EXPECTED_PRODUCT_SOURCE_COMMIT=None,EXPECTED_NATIVE_RECEIPT_SHA=None,CHECKER=None,HTML229_ROLES={k:[r['sha256'],r['bytes']]for k,r in f['text_roles'].items()},DECISIONS=tuple('exact_installed229_539_text_roles_actual_receipt_and_fresh_native_process_assessed'if x.startswith('exact_installed229_')else x for x in ast.literal_eval(next(n.value for n in ast.parse(f['templates']['current']).body if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='DECISIONS'for a in n.targets))))))
for a,b in [('layers=228,project=537,native=17895','layers=229,project=539,native=17896'),('(228,537,17895,52,17730)','(229,539,17896,52,17730)')]:
 f['templates']['current']=one(f['templates']['current'],a.encode(),b.encode())
f['templates']['data_renderer']=assignments(f['templates']['data_renderer'],dict(ROOT_DIRECTORY=ROOT,SOURCE_COMMIT=None,NATIVE_RECEIPT_SHA256=None,TEXT_ROLE_PINS=tuple((k,r['sha256'],r['bytes'])for k,r in f['text_roles'].items())))
f['templates']['data_renderer']=one(f['templates']['data_renderer'],b'installed=228, project=537, native=17895',b'installed=229, project=539, native=17896')
# data validation uses the derived pins; counts/wording are exact current229.
f['templates']['data_renderer']=f['templates']['data_renderer'].replace(b'len(text_roles) == 7',b'len(text_roles) == 8').replace(b"spec['source_roles'] == 18",b"spec['source_roles'] == 23").replace(b'EXACT_INSTALLED229_TEXT7',b'EXACT_INSTALLED229_TEXT8').replace(b'seven text roles',b'eight text roles').replace(b'baseline18/DELIVERY7',b'baseline23/all7native+DELIVERY7')
issuer=ast.literal_eval(next(n.value for n in ast.parse(f['templates']['issuer_renderer']).body if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='TEMPLATE'for a in n.targets)))
issuer=one(issuer,b"spec.get('source_roles')==18",b"spec.get('source_roles')==23")
issuer=one(issuer,b"len(bundle['required_delivery_roles'])==7",b"len(bundle['required_delivery_roles'])==23")
issuer=one(issuer,b"need(type(roles)is dict and len(roles)==14 and type(base.get('source'))is dict and len(base['source'])==18",b"need(type(roles)is dict and len(roles)==23 and type(base.get('source'))is dict and len(base['source'])==23")
issuer=one(issuer,b"need(d['metadata_basis']==dict(path='/home/jericho/.cache/FRW-ASTRA-FIXED229-METADATA-SIBLING-SOURCE-20261117/ROOT-ACTUAL228-INSTALLATION-METADATA-SOURCE.json',bytes=4001,sha256='85e57d286100228d0e8059ffdb68c762526013c4f75fafa99268bcaeee4fa42a'),'Exact fixed229 dated metadata basis required')",b"need(d['metadata_basis']==current.METADATA_BASIS_REF,'Exact fixed229 dated metadata basis required')")
f['templates']['issuer_renderer']=assignments(f['templates']['issuer_renderer'],dict(ROOT_DIRECTORY=ROOT,TEMPLATE=issuer))
# The dated metadata sibling keeps every unrelated permission/CAS/current function.
m=version(metadata)
m=one(m,b'dict(modified=2,added=0,CAS=8,retained=17893)',b'dict(modified=6,added=1,CAS=13,retained=17889)')
m=one(m,b'==(228,17895,17730,52,537)',b'==(229,17896,17730,52,539)')
m=m.replace(b'NATIVE_TWO',b'NATIVE_SEVEN').replace(b"'native_two'",b"'native_seven'").replace(b'native_two=',b'native_seven=')
m=m.replace(b'retained_dependency_four=',b'retained_dependency_three=').replace(b'retained_dependency_four_scope=',b'retained_dependency_three_scope=').replace(b'NOT_228_INSTALL_TARGETS',b'NOT_229_INSTALL_TARGETS')
ma={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(metadata).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in ('LEAF_PINS','RETAINED226_DEPENDENCIES')}
leaf={**ma['LEAF_PINS'],**{k:r['sha256']for k,r in native7.items()}}
retained=ma['RETAINED226_DEPENDENCIES'];del retained['tools/file_tools.py']
m=assignments(m,dict(NATIVE_PYTHON=None,SOURCE_BOUND=False,CLOSURE=None,ACCEPTANCE=None,COUNTS=dict(layers=229,project=539,native=17896,plugins=52,base=17730),SOURCE_COMMIT=None,EXECUTION_COMMIT=None,RECEIPT_SHA=None,INPUT_SHA=None,CANONICAL_REFS=None,CANONICAL_PINS=None,NATIVE_SEVEN=native7,LEAF_PINS=leaf,METADATA_BASIS=None,RETAINED226_DEPENDENCIES=retained))
f['templates']['metadata']=m
f['template_pins']={k:dict(path=str(OUT/'templates'/('UNBOUND_'+k+'229.py')),bytes=len(v),sha256=hashlib.sha256(v).hexdigest())for k,v in f['templates'].items()}
# Historical 228 dependencies stay provenance; generated metadata/prep replace only these roles.
f['static_dependencies']['fixed229_metadata']=f['static_dependencies'].pop('fixed228_metadata')
f['static_dependencies']['fixed229_metadata']=None
f['static_dependencies']['metadata_basis']=None
f['static_dependencies']['preparation']=None
core=version(core.encode()).decode()
core=one(core,"source_roles']==18","source_roles']==23")
core=core.replace("baseline_source18","baseline_source23").replace("len(source)==18","len(source)==23").replace("source==FROZEN['baseline_source23']","encoded(source)==encoded(FROZEN['baseline_source23'])").replace('EIGHTEEN_SOURCE_ROLES','TWENTYTHREE_SOURCE_ROLES').replace('EIGHTEEN_TEXT_DELIVERY','TWENTYTHREE_TEXT_DELIVERY')
core=core.replace("EXPECTED_SOURCE_ROLE_COUNT = 18","EXPECTED_SOURCE_ROLE_COUNT = 23")
core=core.replace("source_roles=18","source_roles=23")
core=one(core,"set(spec)=={'document','document_ref','document_bytes','baseline_source'}","set(spec)=={'document','document_ref','document_bytes','baseline_source','installation_ref','installation_bytes'}")
core=one(core,"    return True\n\n\ndef _assignments", "    _installation(spec)\n    return True\n\n\ndef _assignments")
core=one(core,"def _current(raw,document,data_refs,scenario):","def _current(raw,document,data_refs,scenario,metadata_ref,basis):")
core=one(core,"INSTALLED229=repr(data_refs['ROOT-INSTALLED229-HTML-ROLE-ASSESSMENT.Source-only.json'])","INSTALLED229=repr(data_refs['ROOT-INSTALLED229-HTML-ROLE-ASSESSMENT.Source-only.json']),CHECKER=repr(metadata_ref),EXPECTED_PRODUCT_SOURCE_COMMIT=repr(basis['product_source_commit']),EXPECTED_NATIVE_RECEIPT_SHA=repr(basis['canonical']['receipt']['sha256'])")
# Require all new code plus retained delivery; exact baseline23 remains mandatory.
core=one(core,"    delivery={role:[r['sha256'],r['bytes']]for role,r in FROZEN['required_delivery_roles'].items()}","    delivery={role:[r['sha256'],r['bytes']]for role,r in FROZEN['baseline_source23'].items()}")
anchor="    raw=raw.replace(anchor,('EXPECTED_SOURCE_ROLE_COUNT = 23\\nDELIVERY229_ROLES = '+repr(delivery)+'\\n').encode()+anchor)"
replacement="    raw=raw.replace(anchor,('EXPECTED_SOURCE_ROLE_COUNT = 23\\nMETADATA_BASIS_REF = '+repr(data_refs['metadata_basis'])+'\\nDELIVERY229_ROLES = '+repr(delivery)+'\\n').encode()+anchor)"
core=one(core,anchor,replacement)
core=one(core,"    data=_DATA_MODULE.render_data(copy.deepcopy(document),copy.deepcopy(FROZEN['text_roles']))", "    basis=_installation(spec)\n    data_module=_frozen_module(FROZEN['templates']['data_renderer'],'Parametric229DataRenderer')\n    data_module.SOURCE_COMMIT=basis['product_source_commit'];data_module.NATIVE_RECEIPT_SHA256=basis['canonical']['receipt']['sha256']\n    data=data_module.render_data(copy.deepcopy(document),copy.deepcopy(FROZEN['text_roles']))\n    metadata=_metadata_source(spec,basis)\n    metadata_ref=reference(root+'/fixed229_metadata_source.py',metadata)")
core=one(core,"    current=_current(FROZEN['templates']['current'],document,refs,scenario)","    refs['metadata_basis']=spec['installation_ref']\n    current=_current(FROZEN['templates']['current'],document,refs,scenario,metadata_ref,basis)")
core=one(core,"files={**data,'root_html_v01_edit229_once.py':actor,'root_html_v01_edit229_current.py':current,'issue_reviewed_html_v01_edit229.py':issuer}","files={**data,'root_html_v01_edit229_once.py':actor,'root_html_v01_edit229_current.py':current,'issue_reviewed_html_v01_edit229.py':issuer,'html_v01_edit229_source.py':FROZEN['templates']['preparation'],'fixed229_metadata_source.py':metadata}")
core=one(core,"    deps=copy.deepcopy(FROZEN['static_dependencies'])","    deps=copy.deepcopy(FROZEN['static_dependencies'])\n    deps.update(fixed229_metadata=refs['fixed229_metadata_source.py'],metadata_basis=copy.deepcopy(spec['installation_ref']),preparation=refs['html_v01_edit229_source.py'])")
core=one(core,"required_delivery_roles=copy.deepcopy(FROZEN['required_delivery_roles'])","required_delivery_roles=copy.deepcopy(FROZEN['baseline_source23'])")
core=one(core,"def read_build_input(input_spec_ref,*,reader=None):","def read_build_input(input_spec_ref,installation_basis_ref,*,reader=None):")
core=one(core,"    result=dict(document=document,document_ref=copy.deepcopy(input_spec_ref),document_bytes=raw,baseline_source=copy.deepcopy(baseline['source']))","    need(reference_shape(installation_basis_ref),'HTML229_ACTUAL_INSTALLATION_UNBOUND')\n    installation_raw=reader(installation_basis_ref)\n    result=dict(document=document,document_ref=copy.deepcopy(input_spec_ref),document_bytes=raw,baseline_source=copy.deepcopy(baseline['source']),installation_ref=copy.deepcopy(installation_basis_ref),installation_bytes=installation_raw)")
core=core.replace('eight byte strings','ten byte strings').replace('eight exact bytes','ten exact bytes').replace('new protected0600 Source files','new protected0600 Source files').replace('actual native228','actual native229')
core=core.replace('including actor/current/issuer/scenario/eligibility/roleassessment/reconciliation/bundle','including actor/current/issuer/scenario/eligibility/roleassessment/reconciliation/bundle/preparation/metadata')
# New binding validator and finite metadata renderer, immediately before build().
extra=(OUT/'binding229_core.py').read_text()
core=one(core,'def build(spec):',extra+'\n\ndef build(spec):')
for role,raw in f['templates'].items():
 compile(raw,'<Source '+role+'>','exec')
 p=OUT/'templates'/('UNBOUND_'+role+'229.py');p.parent.mkdir(exist_ok=True,mode=0o700);p.write_bytes(raw)
(OUT/'builder_core229.py').write_text(core)
output=core+'\n# Frozen exact permitted Source; no import/read/current effects.\nFROZEN = '+repr(f)+'\n_initialize_frozen()\n'
compile(output,'constructor229.py','exec')
(OUT/'constructor229.py').write_text(output)
(OUT/'CORE228-to-229.patch').write_text(''.join(difflib.unified_diff((OLD/'builder_core_r1.py').read_text().splitlines(keepends=True),core.splitlines(keepends=True),fromfile='builder_core_r1.py',tofile='builder_core229.py')))
(OUT/'SOURCE-PINS.json').write_text(json.dumps(dict(legacy_constructor=f['legacy_constructor'],candidate229=dict(path=str(N/'ROOT-COMBINED-NATIVE-SOURCE-R1.json'),bytes=5056,sha256='d17794878c8b2cce295f8e0314b7f5612503776cca74baa5d9244955976b1a94'),native7=native7,baseline23=f['baseline_source23'],text8=f['text_roles'],templates=f['template_pins']),indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(assembled=True,bytes=len(output.encode()),sha256=hashlib.sha256(output.encode()).hexdigest())))
