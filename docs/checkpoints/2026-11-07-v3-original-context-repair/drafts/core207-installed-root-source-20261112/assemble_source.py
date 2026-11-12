"""Finite exact206→207 source assembly. Does not execute builder, actor or product code.
Namespaces are renamed separately from semantic deltas; no blanket numeric replacement.
"""
from pathlib import Path
import ast,copy,datetime,difflib,hashlib,json,os,re
B=Path(__file__).parent
OLD=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112')
W=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-MODERN-ODT-NORMAL-SUCCESSOR-SOURCE-20261112')
PREV=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE493-SOURCE-20261112')
CROOT=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ROOT-PRIVATE495-SOURCE-20261112')
P205=Path('/home/jericho/.cache/FRW-SOL-V3-CORE205-SEARCH-SHAPE-COMPOSITION-20261111/revision2')
F205=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112')
TASK23=Path('/home/jericho/.cache/FRW-SOL-V3-F06-NORMAL-SUCCESSOR-SOURCE-20261112')
REC=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
H=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032')
LAYER='f06-modern-odt-authenticated-profile-after-source206'
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def raw(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(n,v):
 p=B/n;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 p.write_bytes(v if isinstance(v,bytes)else v.encode()if isinstance(v,str)else raw(v));p.chmod(0o600)
def replace_many(s,m):
 return re.sub('|'.join(re.escape(x)for x in sorted(m,key=len,reverse=True)),lambda q:m[q.group()],s)
assert sha(OLD/'SOURCE-PINS.json')=='c547cf3c65648a75f87693b23416a7fb2c287cdc8d6b3bb366bdca703e1253df'
assert sha(W/'SOURCE-FREEZE.json')=='a1a34dcca440295256dae2ee0272643cdacc8459508bfae725873ca07e8503a6'
closure=load(REC/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json')
assert sha(REC/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json')=='20e1a9ca845f52eeb0b6a149acc47fd91c9bc70142140e18095acdf18476b900'
cp=closure['canonical_CP206'];tx=Path(cp['path']).parent
before=load(tx/'hermes-agent.source.json');spec=load(W/'FINAL-NATIVE-SPEC.json')
previous=load(PREV/'INPUT-SOURCE206.json');current=load(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json')
assert len(previous['project_files'])==493 and len(current['project_files'])==495
assert {k:v for k,v in current.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'}
projected=copy.deepcopy(before);projected['layers'].append(dict(manifest=spec['manifest_rel'],manifest_sha256=spec['manifest']['sha256'],patch_sha256=spec['patch']['sha256']))
lock=current['sources_lock'];projected['sources_lock_sha256']=lock['sha256']if isinstance(lock,dict)else sha(lock)
for row in spec['native_files']:projected['files'][row['path']].update(sha256=row['sha256'],bytes=row['bytes'],mode='100644')
expected=hashlib.sha256(raw(projected)).hexdigest()
assert projected==load(W/'NATIVE207-PROSPECTIVE-COMPOSITION.json')['expected_inventory']
counts=dict(before_layers=206,after_layers=207,before_project=493,after_project=495,native=17891,native_additions=0,native_targets=1,pair_absent=2,plugins=52,base=17730,selected_CAS=7,untouched_native_rows=17890)
put('PROSPECTIVE207-PROJECTION.json',dict(schema='frw.root207.projection-not-installed.v1',state='EXPECTED_FROM_ACTUAL206_IMMUTABLE_STAGE_SOURCE_ONLY_NOT_CURRENT207',actual206=ref(REC/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json'),before_receipt=ref(tx/'hermes-agent.source.json'),prospective_input=ref(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'),actual_input='UNBOUND_ROOT_MATERIALIZED_PRIVATE495',native_spec=ref(W/'FINAL-NATIVE-SPEC.json'),expected_receipt_sha256=expected,ordered206_prefix_sha256=hashlib.sha256(raw(before['layers'])).hexdigest(),counts=counts,no_actual207_request_admission_UUID_receipt=True))
chain=[];r=cp
while True:
 q=load(r['path']);d=Path(r['path']).parent;n=q['installed_layers']+1
 chain.append(dict(layers=n,request=r,committed=ref(d/'committed.json'),source_receipt=ref(d/'hermes-agent.source.json'),layer_names=q['layer_names'],successor_schema=q['current_source_successor']['schema']))
 if 'previous_native_update'not in q['current_source_successor']:break
 r=q['current_source_successor']['previous_native_update']
assert [x['layers']for x in chain]==list(range(206,198,-1))
history=dict(schema='frw.root.actual206-immutable-history.v1',state='ACTUAL206_COMPLETED_HISTORICAL_NOT_FRESH_ANCHOR',references=dict(complete_closure=ref(REC/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json'),request=cp,committed=closure['committed'],root_journal=closure['operation'],root_return=closure['root_return']),stage_refs=[ref(tx/n)for n in ['hermes-agent.source.json','FRIDAY-INSTALL.json','install-stamp.json']],intent=ref(tx/'intent.json'),chain199_206=chain,ordered206_layers=before['layers'],historical_process_identities_not_future_authority=closure['current_services'],stage_state='SOURCE_UPDATED_NOT_RUNTIME_ACCEPTED historical; separate Root closure completes206')
put('ACTUAL206-HISTORICAL-METADATA.json',history)
wresult=load(W/'RESULT.json')
reuse=dict(schema='frw.root207.final-modern-source-evidence.v1',state='FOUR_ACTUAL_SYNTHETIC_GATES_PASS_FINAL_ROOT_EXECUTION_REVIEW_DEPENDENCY_UNBOUND',final_source_result=ref(W/'RESULT.json'),source_freeze=ref(W/'SOURCE-FREEZE.json'),root_source_gate_authorization=wresult['independent_reviews']['Root_source_only_authorization'],source_gateprep_review=wresult['independent_reviews']['source_gateprep'],four_gate_summary=ref(W/'FOUR-GATES-ACTUAL-TERMINAL-SUMMARY.json'),four_gate_evidence=[dict(label=x['kind'],evidence={k:x['report'][k]for k in ['path','sha256']})for x in wresult['actual_gates']],final_execution_review='UNBOUND_ROOT_PINNED_ACCEPTED_REVIEW',accepted_crypto85_plus12='EXACT_B66D_UNCHANGED_REUSED_NOT_RERUN',retained_limits=wresult['limits_and_reuse'])
put('REUSED-207-FINAL-SOURCE-EVIDENCE.json',reuse)
profile={name:before['files'][name]['sha256']for name in ['hermes_cli/friday_workspace_pdf.py','hermes_cli/friday_workspace_presentation.py']}
assert not set(profile)&{x['path']for x in spec['native_files']}
join=dict(schema='frw.root207.unchanged-bank-profile-source-join.v1',state='SOURCE_ONLY_EXACT206_PROFILE_UNCHANGED_IN207_NO_NEW_APP_CREDIT',before_profile_source_digests=profile,after_profile_source_digests=profile,changed_profile_definitions=[],new_Office_effects=0,saved_app_evidence_reused=True,evidence=[ref(OLD/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION.json'),ref(OLD/'PROFILE-SOURCE-JOIN.json'),ref(REC/'CORE206-ACTUAL-INSTALLED-CLOSED-20261112.json'),ref(W/'FINAL-NATIVE-SPEC.json')],limits='Exact206 PDF/presentation source bytes unchanged207. Fresh bank metadata/topology/linktargets/rootCAS/fourcriticalhashes required; no new Office/App/layout/formal/user/runtime credit.')
put('PROFILE-SOURCE-JOIN.json',join)
# Explicit namespace identities and physical source domains, independent of semantic count/edge edits.
identity={str(OLD):str(B),str(F205):str(OLD),str(PREV):str(CROOT),str(P205):str(PREV),str(TASK23):str(W),'f06-protected-office-profiles-after-source205':LAYER}
for stem in ['root','native','Root','ROOT-','CORE','core','EXACT','NATIVE','OLD','CURRENT','INSTALLED','ACTUAL','actual','current','accepted','SOURCE','source','INPUT-SOURCE','PROJECT','project','after','BEFORE','before','EXPECTED','expected','genuine','canonical','profile','PROFILE','Task','future']:
 for n in [205,206]:identity[stem+str(n)]=stem+str(n+1)
for fragment in ['-205','-206','_205','_206','205to206','205_','206_','in206','unchanged206','unchanged205','205schema']:
 identity[fragment]=replace_many(fragment,{'205':'206','206':'207'})
identity.update({'PROJECT491':'PROJECT493','PROJECT493':'PROJECT495','project491':'project493','project493':'project495','public493':'public495','private493':'private495','project491_to493':'project493_to495'})
identity['Task23_accepted_source_only_not_runtime_qualified']='modern207_accepted_source_only_not_runtime_qualified'
identity.update({'aca0533b58ffe947e41c44f0dd65026fbac1593a90fa7b34efc373bc74e08fdb':'253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21','253f6586a4fb2b7f9004d47f0cf152a7671d92c774b892b95fa086324dc0bf21':expected,'2e8d10c24982c0164094a3565876106cd33f59351e052082c56b4f8f974bfef9':sha(PREV/'INPUT-SOURCE206.json'),'e6e480448509b336824b1aa13f27c359cc89eb4612c0317eb6a877cdb9586e39':sha(W/'INPUT-SOURCE207.PROSPECTIVE.NOT_INSTALLED.json'),'90b12d3a915e9c841f15360588094119ffe9fe40e1e3813a2cb630ec6a1e9e56':sha(W/'FINAL-NATIVE-SPEC.json'),'f570120371c28eeeb9f708ffbd32d451056c39fc57f7a49ed60eb9db0eb26cb5':'489f6a23a4015bbb1daad9c405028b83e55b10725cd4f5e8b56ce678ee6e1eb9','friday.current-source-native-successor.v8':'friday.current-source-native-successor.v9'})
semantic_numbers={205:206,206:207,491:493,493:495,17880:17890}
renamed=[]
def transform(text,name):
 lines=text.splitlines(keepends=True);offset=[0]
 for s in lines:offset.append(offset[-1]+len(s))
 edits=[]
 for node in ast.walk(ast.parse(text)):
  old=text[offset[node.lineno-1]+node.col_offset:offset[node.end_lineno-1]+node.end_col_offset]if hasattr(node,'lineno')else''
  new=None
  if isinstance(node,ast.Constant)and type(node.value)is str:
   val=replace_many(node.value,identity)
   # No string-count replace inside digests: reject accidental hash modifications.
   for h in re.findall(r'[0-9a-f]{64}',node.value):
    if h not in identity:assert h in val,('unexpected_hash_edit',name,h)
   if val!=node.value:new=repr(val)
  elif isinstance(node,ast.Constant)and type(node.value)is int and node.value in semantic_numbers:new=str(semantic_numbers[node.value])
  elif isinstance(node,ast.Name)and node.id in {'F205','S205','INPUT205','TASK23'}:new={'F205':'F206','S205':'S206','INPUT205':'INPUT206','TASK23':'MODERN207'}[node.id]
  if new is not None:
   edits.append((offset[node.lineno-1]+node.col_offset,offset[node.end_lineno-1]+node.end_col_offset,new));renamed.append(dict(file=name,line=node.lineno,before=old,after=new))
 for a,b,val in sorted(edits,reverse=True):text=text[:a]+val+text[b:]
 return text
names={'boundary_contract.py':'boundary_contract.py','start_core206_once.py':'start_core207_once.py','f06-206-first-actual-root.py':'f06-207-first-actual-root.py','root206_metadata.py':'root207_metadata.py','run_native206_once.py':'run_native207_once.py','resume_native206_services.py':'resume_native207_services.py','prepare_source.py':'prepare_source.py'}
for old,new in names.items():put(new,transform((OLD/old).read_text(),new))
for name in ['native_scope.py','admission-retained/observe-current-retained-units.py']:put(name,(OLD/name).read_bytes())
for name in ['build-layer-publication-request.py','friday_v3_layer_publication.py']:put('publication/'+name,(W/'publication'/name).read_bytes())
def json_transform(v):
 if isinstance(v,str):return replace_many(v,identity)
 if isinstance(v,int)and not isinstance(v,bool):return semantic_numbers.get(v,v)
 if isinstance(v,dict):return {replace_many(k,identity):json_transform(x)for k,x in v.items()}
 if isinstance(v,list):return [json_transform(x)for x in v]
 return v
for p in OLD.glob('*-TEMPLATE.json'):put(replace_many(p.name,identity),json_transform(load(p)))
commands=json_transform(load(OLD/'ROOT-FUTURE-COMMANDS.json'))
commands['commands']['builder'][commands['commands']['builder'].index('--current-source-native-predecessor')+1]=cp['path']
commands['order']='SOURCE ONLY. Root authentic actual206/full198+199..206 chain + modern207 finalexecutionreview and newframe review + fresh globalnative/all3SQL<=15s/currentCAS + Root private495 materialization + finitefuture207 authority. One --layer modern207 v8→v9; fullinventory/rawGit/modes/private28/7CAS. No consumed effect replay.'
put('ROOT-FUTURE-COMMANDS.json',commands)
put('NAMESPACE-TRANSFORMATION.json',dict(method='AST-literal/identifier explicit namespace identities; no global206→207 source replacement',source=ref(OLD/'SOURCE-PINS.json'),edits=renamed))
print(json.dumps(dict(state='ASSEMBLED_UNFINALIZED_UNBOUND',expected_receipt=expected,counts=counts,files=len(names))))
