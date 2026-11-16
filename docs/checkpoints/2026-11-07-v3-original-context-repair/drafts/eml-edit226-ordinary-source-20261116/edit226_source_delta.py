"""Pure fixed226 EDIT-only caller/current/actor Source delta. No IO/effects.

The original Source packet and future227 CREATE remain unchanged. No version or
operation selector admits another installed profile. Root binds real current.
"""
import ast,hashlib,types
from pathlib import Path
ADAPTER_SHA='60697c2c0290ed776560ccfd2c1ab3f06c73937a8044ce1caf767d8890d9c0c9'
GENERATOR_SHA='94706f69fe3c9a578f63e35b39b405eeee3fff0eb1a7e32ad73248d7c1379726'
EXPECTED226_TUPLE={'installed':226,'project':533,'native':17895,'plugins':52,'base':17730,'product_source_commit':'35d5f4fe901dc4c11e43f52c65949e843c70de5c'}
EDIT_NATIVE_REF={'path':'/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent/tools/scoped_communication.py','bytes':35499,'sha256':'bf4e515a71979562743607f6432a4370734d0a465d202a195e6ab3b74ee298db'}
CANONICAL226_SHA={'receipt':'9e65245f445b486fad4445b549360698066726f74006fe236db5afd26d79041e','marker':'f0a62d197decc50a891ab1a47a9fa53b4a56d8f8bda92901dd7afe0454fc457e','stamp':'7339e1228c9a5f558e88e6e1e00cc65472ce8982209f968980c71849f5b1fefb'}
def need(ok,code):
 if not ok:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(raw,sha,name):
 need(type(raw)is bytes and digest(raw)==sha,'EDIT226_EXACT_REVIEWED_PARENT_REQUIRED')
 m=types.ModuleType(name);m.__file__='<pinned-pure-parent>';exec(compile(raw,m.__file__,'exec'),m.__dict__);return m
def once(s,old,new):
 need(s.count(old)==1,'EDIT226_EXACT_LITERAL_SEAM');return s.replace(old,new)
def replace_nodes(source,changes):
 lines=source.splitlines(keepends=True);edits=[]
 for n in ast.parse(source).body:
  name=n.name if isinstance(n,ast.FunctionDef)else next((t.id for t in n.targets if isinstance(t,ast.Name)),'')if isinstance(n,ast.Assign)else ''
  if name in changes:edits.append((n.lineno,n.end_lineno,changes.pop(name)))
 need(not changes,'EDIT226_EXACT_NAMED_SEAMS_REQUIRED')
 for lo,hi,text in sorted(edits,reverse=True):lines[lo-1:hi]=[text]
 return ''.join(lines)

def adapter_source(parent_raw):
 load(parent_raw,ADAPTER_SHA,'_reviewed_EML_ordinary_parent')
 source=parent_raw.decode().replace('eml_installed227_current_assessment','eml_installed226_current_assessment').replace('EMLCE_ROOT_ELIGIBILITY_AND_INSTALLED227_CURRENT_REQUIRED','EDIT226_ROOT_ELIGIBILITY_AND_EXACT226_CURRENT_REQUIRED')
 source=replace_nodes(source,{
  'ORIGINAL_CASE':"ORIGINAL_CASE = {'case_id':'F-03','case_index':164,'format':'eml','format_index':108,'original_fixture_ref':'FX-FMT','scope':'Subject-only copy EDIT of genuine previously received notice_saved.eml on exact226; no CREATE admission','maximum_trials':1}\n",
  'operation_of':'''def operation_of(scenario):
    need(type(scenario)is dict and type(scenario.get('steps'))is list and len(scenario['steps'])==1 and scenario['steps'][0].get('request')==EDIT_REQUEST,'EDIT226_EXACT_GENUINE_RECEIVED_SUBJECT_EDIT_ONLY')
    return 'edit'
''',
  'scenario_data':'''def scenario_data(*,received_source=None,tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot'):
    need((tester_id,peer_id,peer_username)==(8812646969,8751854128,'@jerichodevbot')and type(tester_id)is type(peer_id)is int,'EDIT226_EXACT_TESTER_PEER_REQUIRED')
    received_source_shape(received_source)
    return dict(tester_id=tester_id,peer_id=peer_id,peer_username=peer_username,deadline_seconds=600,max_updates=64,pace_seconds=1,steps=[dict(request=EDIT_REQUEST,observe=clone(OBSERVE))])
''',
  'validate_scenario_data':'''def validate_scenario_data(scenario):
    operation_of(scenario)
    expected=dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=600,max_updates=64,pace_seconds=1,steps=[dict(request=EDIT_REQUEST,observe=clone(OBSERVE))])
    need(same(scenario,expected),'EDIT226_EXACT_SINGLE_NATURAL_EDIT_NO_UPLOAD_RESET_OR_ORACLE')
    return True
'''
 })
 source=once(source,'Pure independent ordinary EML CREATE and genuine-received EDIT binding','Pure exact226 genuine-received EML Subject-edit-only binding')
 source=once(source,"'installed_target':227","'installed_target':226")
 source=once(source,'original EML create/edit scope, installed227 and effect eligibility,','original F03 EML EDIT scope, exact installed226 and effect eligibility,')
 source=source.replace('frw.EML.create-edit.ordinary.source-preparation.v1','frw.EML.edit226.ordinary.source-preparation.v2').replace('frw.EML.create-edit.ordinary.static-plan.v1','frw.EML.edit226.ordinary.static-plan.v2')
 # Exact operation_of rejects CREATE before these retained, now unreachable parent branches.
 ast.parse(source);return source.encode()

def current_source(generator_raw,parent_current_raw,*,run_id='ROOT_UNBOUND',baseline_ref=None,eligibility_ref=None,installed226_ref=None,received_source_ref=None):
 parent=load(generator_raw,GENERATOR_SHA,'_reviewed_EML_Root_delta')
 source=parent.current_source(parent_current_raw,run_id=run_id,operation='edit',baseline_ref=baseline_ref,eligibility_ref=eligibility_ref,installed227_ref=installed226_ref,received_source_ref=received_source_ref).decode()
 source=source.replace('INSTALLED227','INSTALLED226').replace('installed227','installed226').replace('frw.Root.EML-create-edit.preintent-proof.v1','frw.Root.EML-edit226.preintent-proof.v2')
 source=once(source,"Root's bounded preintent gate for one original F01/EMLCE first upload.","Root's bounded preintent gate for one exact226 ordinary F03 EML copy edit.")
 source=once(source,"'exact_installed226_current_and_fresh_native_process_accepted'","'exact_installed226_current_existing_process_and_native_edit_profile_accepted'")
 source=once(source,"def need(ok,why):",'EXPECTED226_TUPLE = '+repr(EXPECTED226_TUPLE)+'\nEDIT_NATIVE_REF = '+repr(EDIT_NATIVE_REF)+'\nCANONICAL226_SHA = '+repr(CANONICAL226_SHA)+'\ndef need(ok,why):')
 old="need(assessment.get('operator')=='Root'and assessment.get('installed')==227 and assessment.get('current_accepted')is True and assessment.get('fresh_native_process_after_change')is True and assessment.get('baseline')==BASE,'EMLCE_REAL_INSTALLED226_CURRENT_REQUIRED')"
 new="need(assessment.get('operator')=='Root'and assessment.get('installed')==226 and assessment.get('current_accepted')is True and assessment.get('existing_native_process_accepted')is True and assessment.get('baseline')==BASE and assessment.get('current_tuple')==EXPECTED226_TUPLE and assessment.get('edit_native_ref')==EDIT_NATIVE_REF,'EDIT226_EXACT_CURRENT_PROFILE_REQUIRED')"
 source=once(source,old,new)
 source=once(source,"base=h.doc(BASE)","base=h.doc(BASE)\n need(all(base.get('canonical',{}).get(k,{}).get('sha256')==v for k,v in CANONICAL226_SHA.items()),'EDIT226_EXACT_CANONICAL3_REQUIRED')\n need(type(base.get('source'))is dict and list(base['source'].values()).count(EDIT_NATIVE_REF)==1,'EDIT226_EXACT_NATIVE_EDIT_SOURCE_NOT_SIBLING_REQUIRED')")
 ast.parse(source);return source.encode()

def actor_source(generator_raw,parent_actor_raw,*,run_id='ROOT_UNBOUND',source_root,current_path):
 parent=load(generator_raw,GENERATOR_SHA,'_reviewed_EML_Root_actor_delta')
 source=parent.actor_source(parent_actor_raw,run_id=run_id,source_root=source_root,current_path=current_path).decode().replace('INSTALLED227','INSTALLED226').replace('installed227','installed226').replace('frw.Root.EML-create-edit.preintent-proof.v1','frw.Root.EML-edit226.preintent-proof.v2')
 source=once(source,'One finite Root-owned original EMLCE ordinary upload; no background loop/retry.','One finite Root-owned exact226 ordinary F03 EML copy edit; no background loop/retry.')
 source=once(source,"need(current.ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')","need(current.ROOT_BOUND is True,'EMLCE_ROOT_UNBOUND_FAILCLOSED')\n need(current.OPERATION=='edit'and current.EXPECTED226_TUPLE=="+repr(EXPECTED226_TUPLE)+"and current.EDIT_NATIVE_REF=="+repr(EDIT_NATIVE_REF)+",'EDIT226_ACTOR_EXACT_FIXED_PROFILE_REQUIRED')")
 ast.parse(source);return source.encode()
if __name__=='__main__':raise SystemExit('REFUSED: fixed226 EDIT-only pure Source; Root binding required')
