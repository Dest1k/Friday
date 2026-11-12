"""Bounded pure207 delta controls. No actor/builder CLI/product/collector or runtime reads.
Canonical path maps below are in-memory fixtures over actual206 immutable stage metadata.
They are never persisted as actual requests, Rootbindings, authority or admission.
"""
from pathlib import Path
import argparse,ast,copy,datetime,hashlib,importlib.util,json,os,resource,time,types
B=Path(__file__).parent
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
START=time.monotonic();checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(dict(name=name,passed=True))
def negative(name,fn,reason=None):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError)as e:
  check(name,reason is None or reason in str(e));return
 raise AssertionError('negative_not_refused:'+name)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module(B/'root207_metadata.py','Pure207metadata');c=module(B/'boundary_contract.py','Pure207contract')
for p in B.rglob('*.py'):ast.parse(p.read_bytes(),filename=str(p));compile(p.read_bytes(),str(p),'exec')
check('all_python_source_compiles',True)
history=load(B/'ACTUAL206-HISTORICAL-METADATA.json');record=dict(schema='frw.root.actual206-predecessor.v1',state='ROOT_RECONCILED_GENUINE_INSTALLED206_NOT_EXPECTATION',template_only_no_execution_grant=False,**history['references'])
check('actual_CP206_original198_and_full199_206_chain_real_immutable_reads',m.validate_predecessor_record(record)==history['references']['request'])
for key in history['references']:
 bad=copy.deepcopy(record);bad[key]['sha256']='0'*64;negative('reject_wrong_actual206_'+key,lambda b=bad:m.validate_predecessor_record(b),'exact_completed206_refs_required')
bad=copy.deepcopy(record);bad['state']='EXPECTED206_FROM_PROJECTION';negative('reject_projection_as_actual206',lambda:m.validate_predecessor_record(bad),'genuine_actual206_record_required')
original_readref=m.readref;original_ref=m.reference;original_sha=m.sha;original_owned=m.owned;original_lexists=m.os.path.lexists
policy=load(B/'ROOT-207-PUBLIC-ORIGIN-POLICY.json');current=original_readref(policy['prospective_private_input']);previous=original_readref(m.ORIGINAL206_INPUT);public=original_readref(policy['current_public_input']);spec=original_readref(m.FIXED['native_spec']);before=original_readref(next(r for r in history['stage_refs']if r['path'].endswith('/hermes-agent.source.json')))
origins=original_readref(m.FIXED['project_origins'])['rows'];puborigins=original_readref(m.FIXED['public_origins'])['rows']
check('real_all495_private_and_public_source_origin_bytes',all(original_ref(r['path'])=={k:r[k]for k in ['path','sha256']}for r in [*origins.values(),*puborigins.values()]))
check('real_all493_predecessor_physical_source_bytes',all(sha(m.P/n)==d for n,d in previous['project_files'].items()))
check('only_helper_change_pair2_added_from493_to495',set(current['project_files'])-set(previous['project_files'])=={spec['manifest_rel'],spec['patch_rel']}and {n for n in previous['project_files']if previous['project_files'][n]!=current['project_files'].get(n)}=={'scripts/friday_ordinary_install.py'})
check('every_nonproject_field_equal_actual206', {k:v for k,v in current.items()if k!='project_files'}=={k:v for k,v in previous.items()if k!='project_files'})
projection=m.project_receipt(before,spec,current);expected=load(B/'PROSPECTIVE207-PROJECTION.json')['expected_receipt_sha256']
check('exact207_projection_from_genuine206',projection==original_readref(m.FIXED['prospective_composition'])['expected_inventory']and hashlib.sha256(m.encoded(projection)).hexdigest()==expected)
check('complete206_ordered_prefix',projection['layers'][:-1]==before['layers']==history['ordered206_layers'])
check('one_existing_codec_only_no_native_addition',len(spec['native_files'])==1 and spec['native_files'][0]['path']=='tools/scoped_odf_password.py'and spec['native_files'][0]['new_file']is False and spec['native_files'][0]['before_sha256']==before['files']['tools/scoped_odf_password.py']['sha256'])
check('all17890_native_untouched',len(set(before['files'])-{'tools/scoped_odf_password.py'})==17890 and {n:r for n,r in projection['files'].items()if n!='tools/scoped_odf_password.py'}=={n:r for n,r in before['files'].items()if n!='tools/scoped_odf_password.py'})
check('exact_afterimage_b66d',sha(m.MODERN207/'native-after/tools/scoped_odf_password.py')=='b66d95d1f2a4223ffcc9d54e28d13976b49e5e2f041e1c12456a8c7b85922d9d')
# Isolated virtual canonical207paths: all payloads stay only in memory.
binding=load(m.PROJECT_SOURCE_PROOF['path'])
virtual_json={m.PROJECT_SOURCE_PROOF['path']:binding,str(m.S/'INPUT-SOURCE207.json'):current,str(m.H/'hermes-agent.source.json'):before}
virtual_hash={str(m.C/n):d for n,d in current['project_files'].items()};virtual_hash.update({p:hashlib.sha256(m.encoded(v)).hexdigest()for p,v in virtual_json.items()})
virtual_hash[str(m.S/'INPUT-SOURCE207.json')]=policy['expected_actual_input_sha256'];virtual_hash[str(m.H/'hermes-agent.source.json')]=m.BEFORE_RECEIPT
for n,d in previous['project_files'].items():virtual_hash[str(m.H/n)]=d
for row in spec['native_files']:virtual_hash[str(m.H/'hermes-agent'/row['path'])]=row['before_sha256']
def vref(path):
 p=str(path)
 return dict(path=p,sha256=virtual_hash[p])if p in virtual_hash else original_ref(path)
def vread(ref):
 if ref['path']in virtual_json:
  m.require(vref(ref['path'])==ref or ref==m.PROJECT_SOURCE_PROOF,'virtual_reference_hash_changed');return copy.deepcopy(virtual_json[ref['path']])
 return original_readref(ref)
def vsha(path):return virtual_hash[str(path)]if str(path)in virtual_hash else original_sha(path)
try:
 m.reference=vref;m.readref=vread;m.sha=vsha;m.owned=lambda p:Path(p)
 m.os.path.lexists=lambda p:False if str(p)in {str(m.H/spec['manifest_rel']),str(m.H/spec['patch_rel'])}else original_lexists(p)
 check('Root_materialized_sourceproof_consumer_virtual495_positive',m.validate_project_binding()==binding)
 for name,mut in [('wrong_public_input',lambda r:r.update(current_input=policy['current_public_input'])),('wrong_project_domain',lambda r:r.update(private_project='/synthetic/wrong')),('physical_not_verified',lambda r:r.update(all495_origin_hashes_verified=False)),('counterpart_not_verified',lambda r:r.update(private_public28=[]))]:
  bad=copy.deepcopy(binding);mut(bad);virtual_json[m.PROJECT_SOURCE_PROOF['path']]=bad;virtual_hash[m.PROJECT_SOURCE_PROOF['path']]=hashlib.sha256(m.encoded(bad)).hexdigest();negative('reject_binding_'+name,m.validate_project_binding)
 virtual_json[m.PROJECT_SOURCE_PROOF['path']]=binding;virtual_hash[m.PROJECT_SOURCE_PROOF['path']]=hashlib.sha256(m.encoded(binding)).hexdigest()
 q=load(history['references']['request']['path']);q.update(previous_input=m.ORIGINAL206_INPUT,current_input=vref(m.S/'INPUT-SOURCE207.json'),candidate_input=vref(m.S/'INPUT-SOURCE207.json'),candidate_project=str(m.C),layer_names=[m.LAYER],installed_layers=206,installed_files=17891,project_file_updates=['scripts/friday_ordinary_install.py'],project_inventory=current['project_files'],project_inventory_sha256=hashlib.sha256(m.encoded(current['project_files'])).hexdigest(),layer_manifest_updates=[spec['manifest_rel']],current_source_successor=dict(schema='friday.current-source-native-successor.v9',root_project_update=m.ROOT198,previous_native_update=history['references']['request']))
 q['source_receipt']=q['target_receipt']=vref(m.H/'hermes-agent.source.json')
 closure=original_readref(history['references']['complete_closure'])
 for key in ['marker','stamp']:
  q[key]=closure['installed']['canonical4'][key];virtual_hash[q[key]['path']]=q[key]['sha256']
 # Other protected metadata hashes are existing historical input pins; virtual validation only.
 for key in ['configuration','profile','launcher','native_unit']:virtual_hash[q[key]['path']]=q[key]['sha256']
 oldactual=m.actual_predecessor;m.actual_predecessor=lambda:history['references']['request']
 result=m.validate_source_request(q);check('exact_request_reader_virtual_canonical206_to207_positive',result['selected_target_count']==7 and result['expected_receipt_sha256']==expected and result['after_layers']==207)
 check('exact_seven_CAS_target_paths',set(result['selected_targets'])=={str(m.H/'hermes-agent/tools/scoped_odf_password.py'),str(m.H/'scripts/friday_ordinary_install.py'),str(m.H/spec['manifest_rel']),str(m.H/spec['patch_rel']),str(m.H/'FRIDAY-INSTALL.json'),str(m.H/'hermes-agent.source.json'),str(m.H/'hermes-agent/install-stamp.json')})
 for name,mut in [('previous_layer205',lambda x:x.update(installed_layers=205)),('extra_layer',lambda x:x.update(layer_names=[m.LAYER,'unreviewed'])),('v8insteadv9',lambda x:x['current_source_successor'].update(schema='friday.current-source-native-successor.v8')),('futurev10',lambda x:x['current_source_successor'].update(schema='friday.current-source-native-successor.v10')),('fakeCP205',lambda x:x['current_source_successor'].update(previous_native_update=m.ROOT198)),('helper_omitted',lambda x:x.update(project_file_updates=[])),('plugins',lambda x:x.update(plugin_set=['p'])),('wrong_current_input',lambda x:x.update(current_input=policy['current_public_input'])),('inventory_hash',lambda x:x.update(project_inventory_sha256='0'*64)),('project_extra_field',lambda x:x.update(injection=True))]:
  bad=copy.deepcopy(q);mut(bad);negative('request_reject_'+name,lambda b=bad:m.validate_source_request(b))
 # Nativecount/scope/bytes: execute same exact source reader with individual mocked spec deltas.
 for name,mut in [('extra_native_path',lambda s:s['native_files'].append(copy.deepcopy(s['native_files'][0]))),('wrong_native_path',lambda s:s['native_files'][0].update(path='tools/other.py')),('new_native',lambda s:s['native_files'][0].update(new_file=True))]:
  bad=copy.deepcopy(spec);mut(bad);virtual_json[m.FIXED['native_spec']['path']]=bad;virtual_hash[m.FIXED['native_spec']['path']]=m.FIXED['native_spec']['sha256'];negative('request_reject_'+name,lambda:m.validate_source_request(q))
 del virtual_json[m.FIXED['native_spec']['path']];del virtual_hash[m.FIXED['native_spec']['path']]
 m.actual_predecessor=oldactual
finally:
 m.reference=original_ref;m.readref=original_readref;m.sha=original_sha;m.owned=original_owned;m.os.path.lexists=original_lexists
qual=load(B/'ROOT-207-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json');check('unchanged_bank_profile_consumer_positive',m.validate_profile_join(qual,before,spec)==qual['minimum_profile_source_digests'])
bad=copy.deepcopy(qual);bad['formal_test_credit']=True;negative('reject_App_formal_claim',lambda:m.validate_profile_join(bad,before,spec))
# Exact rawGit batch reader positive and meaningful object/mode/header/tail negative controls.
oldgit=m.origin_git;body=b'pure207\n';oid=m.git_oid('blob',body);tree={'p':('100644','blob',oid)};want={'p':hashlib.sha256(body).hexdigest()};batch=(oid+' blob '+str(len(body))+'\n').encode()+body+b'\n'
m.origin_git=lambda *a,**k:batch
m.origin_blobs(Path('/pure'),tree,want);check('rawGit_parser_exact_blob_mode_oid_SHA_positive',True)
negative('rawGit_reject_wrong_mode',lambda:m.origin_blobs(Path('/pure'),{'p':('120000','blob',oid)},want))
negative('rawGit_reject_wrong_SHA',lambda:m.origin_blobs(Path('/pure'),tree,{'p':'0'*64}))
m.origin_git=lambda *a,**k:batch+b'x';negative('rawGit_reject_trailing_bytes',lambda:m.origin_blobs(Path('/pure'),tree,want))
m.origin_git=lambda *a,**k:batch.replace(body,b'bad207!\n');negative('rawGit_reject_false_object_body',lambda:m.origin_blobs(Path('/pure'),tree,want));m.origin_git=oldgit
# Actual immutable completed206 rawGit493 evidence, no currentHEAD inference or network.
repo=Path('/home/jericho/jericho/Friday_rework');prior=original_readref(policy['completed206_public_input'])['project_files'];m.origin_blobs(repo,m.origin_tree(repo,policy['completed206_source_commit']),prior);check('real_completed206_rawGit_all493',True)
r=lambda n:dict(path='/synthetic/'+n,sha256='a'*64);refs={k:r(k)for k in ['manifest','boundary','caller','anchor','source_acceptance','predecessor']}
a=dict(schema='frw.root.native207-reviewed-future-boundary.v1',state='ROOT_REVIEWED_EXACT207_FUTURE_EXECUTION',template_only_no_execution_grant=False,frame='/synthetic/frame',execution_commit='b'*40,origin_url='https://github.com/Dest1k/Friday.git',provenance_mode='local-committed-main',public_main_sha=None,future_finite_operation_reviewed=True,new_future207_budgets=dict(actor=1800,source=600,publisher_unit=810,publisher_client=840,cold_each=180,postcheck=90,reserve=75),old_effects_clocks_preserved=True,modern207_accepted_source_only_not_runtime_qualified=True,shared_slot_identity=[1,2,1000,1,384],source_pin_manifest=refs['manifest'],boundary=refs['boundary'],caller=refs['caller'],current_service_anchor=refs['anchor'],source_acceptance=refs['source_acceptance'],actual206_predecessor=refs['predecessor'])
c.validate_authority(a,**refs,frame='/synthetic/frame');check('authority_localmode_remoteNone_positive',True)
for name,mut in [('remote_claim_in_local',lambda x:x.update(public_main_sha='b'*40)),('unbound_mode',lambda x:x.update(provenance_mode='UNBOUND')),('oldclock_reset',lambda x:x.update(old_effects_clocks_preserved=False)),('budget_shrink',lambda x:x['new_future207_budgets'].update(source=599)),('wrong_predecessor',lambda x:x.update(actual206_predecessor=r('wrong')))]:
 bad=copy.deepcopy(a);mut(bad);negative('authority_reject_'+name,lambda b=bad:c.validate_authority(b,**refs,frame='/synthetic/frame'))
a.update(provenance_mode='published-remote',public_main_sha=a['execution_commit']);c.validate_authority(a,**refs,frame='/synthetic/frame');check('publishedmode_explicit_separate_positive',True)

# Exact existing Rootsource proof + actual materialized495 reads only; no runtime reads/grants.
check('real_Root_materialized495_sourceproof_exact_pin_consumer',m.validate_project_binding()['project_files']==495)
anchor=load(B/'ROOT-207-CURRENT-SERVICE-ANCHOR-TEMPLATE.json');anchor.update(state='ROOT_ACTUAL_CURRENT206_BOUNDARY',template_only_no_execution_grant=False,observed_at_moscow=datetime.datetime.fromtimestamp(1100,datetime.timezone.utc).isoformat(),boot_id='b'*36,historical_refs={},frame='/synthetic/frame',future_publisher_unit='synthetic.service',home='/synthetic/home',evidence=[r('fresh')]);anchor['checks']={k:True for k in anchor['checks']};anchor['quiescence_basis']['root_current_all_profile_pending_approval_cancel_maintenance_evidence']=[r('fresh')]
anchor['services']={n:dict(pid=42,birth_ticks=50,boot_id='b'*36,invocation_id='a'*32,cgroup='/user.slice/synthetic',enabled_active=True,runtime_max='infinity')for n in ['gateway','dashboard']};anchor['process_environment']={n:dict(HERMES_HOME='/synthetic/home')for n in ['gateway','dashboard']}
anchor_args=dict(current_time=1110,boot='b'*36,historical={},frame='/synthetic/frame',publisher='synthetic.service',home='/synthetic/home')
c.validate_anchor(anchor,**anchor_args);check('anchor_truthful_unexposed_scope_positive',True)
bad=copy.deepcopy(anchor);bad['quiescence_basis']['limits'].remove('ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED');negative('anchor_reject_omitted_unexposed_limit',lambda:c.validate_anchor(bad,**anchor_args))
bad=copy.deepcopy(anchor);bad['quiescence_basis']['scoped_tester_queue']='ALL_PROFILE_PENDING';negative('anchor_reject_tester_as_allprofile_pending',lambda:c.validate_anchor(bad,**anchor_args))

gw=dict(pid=42,birth_ticks=50,boot_id='b'*36);g=dict(scope='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',read_only=True,identity=dict(pid=42,start_time=50,boot_id='b'*36),observed_monotonic=100,global_active_session_keys=[],terminal_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False),web_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False));dbs={n:dict(quick_check='ok',leases=0,all_origin_pending_delegations=0,observed_monotonic=100)for n in ['default','dest','tester']}
c.validate_global_quiescence(g,dbs,gw,current_monotonic=115);check('globalnative_all3SQL_age15_positive',True)
negative('globalnative_age15plus_refused',lambda:c.validate_global_quiescence(g,dbs,gw,current_monotonic=115.001))
for name in dbs:
 bad=copy.deepcopy(dbs);bad[name]['observed_monotonic']=99.99;negative('SQL_'+name+'_age15plus_refused',lambda b=bad:c.validate_global_quiescence(g,b,gw,current_monotonic=115))
 bad=copy.deepcopy(dbs);bad[name]['all_origin_pending_delegations']=1;negative('SQL_'+name+'_pending_refused',lambda b=bad:c.validate_global_quiescence(g,b,gw,current_monotonic=110))
# Exact publisher/builder bytes & builder argparse are source-only, no build_request/main invoked.
builder=module(B/'publication/build-layer-publication-request.py','Pure207BuilderArgs');args=builder.parse_args(['--home','/synthetic/home','--candidate-project','/synthetic/candidate','--previous-input','/synthetic/previous','--current-input','/synthetic/current','--current-source-project-update','/synthetic/root198','--current-source-native-predecessor',history['references']['request']['path'],'--layer',m.LAYER,'--seconds','600','--output','/synthetic/output'])
check('real_builder_argparser_one_explicit_ninth_layer',args.layer==[m.LAYER]and args.seconds==600)
check('default_four_exact_unchanged',builder.LAYER_NAMES==('source157-original-context-deterministic-overhead-after-source156','source157-bounded-schema-hints-after-source156','source157-tool-budget-fit-after-source156','write-file-format-guard'))
check('accepted_publication_source_bytes_exact',sha(B/'publication/build-layer-publication-request.py')==sha(m.MODERN207/'publication/build-layer-publication-request.py')and sha(B/'publication/friday_v3_layer_publication.py')==sha(m.MODERN207/'publication/friday_v3_layer_publication.py'))
def defs(p):return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(Path(p).read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
old=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112');actor=defs(B/'run_native207_once.py');older=defs(old/'run_native206_once.py')
for n in ['remaining','operation_remaining','command','service','data','file_metadata','directory_metadata','state_file_snapshot','selected_process_environment','closed','unchanged_user']:check('retained_actor_function_exact_'+n,actor[n]==older[n])
recovery=defs(B/'resume_native207_services.py');oldrecovery=defs(old/'resume_native206_services.py')
for n in ['publisher_cgroup_empty','publisher_process_closed','publisher_terminal_proven']:check('retained_strict_recovery_exact_'+n,recovery[n]==oldrecovery[n])
boundary=(B/'f06-207-first-actual-root.py').read_text();main=next(n for n in ast.parse(boundary).body if isinstance(n,ast.FunctionDef)and n.name=='main');maintext=ast.get_source_segment(boundary,main)
check('sharedslot_same_inherited_FD',"pass_fds=(slotfd,)"in boundary and 'fcntl.LOCK_UN'not in boundary and 'wait_same_child(child)'in boundary)
check('freshglobal_after_bank_resources',boundary.index('native = transport.fresh_native(state)')>boundary.index('resources = dict(')>boundary.index('if bank_check:'))
check('final_ageguard_after_binding_before_actor',maintext.rindex('contract.validate_global_quiescence(')>maintext.rindex('m.load_actor_binding(')and maintext.rindex('contract.validate_global_quiescence(')<maintext.rindex('result = launch_once('))
check('no_actual_future_artifacts',all(not(B/n).exists()for n in ['ROOT-FRESH-REQUEST.json','ROOT-207-PROJECT-SOURCE.json','ROOT-207-RUNTIME-AUTHORITY.json','ROOT-207-SOURCE-ACCEPTANCE.json','ROOT-NATIVE207-LIVE-OPERATION.json','FUTURE-EXECUTION']))
check('wall_guard90',time.monotonic()-START<=90)
value=dict(schema='frw.root207.pure-changed-source-controls.v1',state='PASS_PURE_SOURCE_ONLY_NO_REQUEST_NO_GRANT',checks=len(checks),rows=checks,wall_seconds=time.monotonic()-START,actual_runtime_observations=0,actual_effects=0,virtual_canonical_checks_not_actual_request=True,limits=['No genuine207builder request/authority/runtime/nonce generated; virtual dictionaries only.','W207 fourfullsyntheticgates andcrypto85+12 not rerun; inherited coverage stated separately.','Current207rawGit/actual495/fresh3SQL/globalnative/service/slot/CAS remain Root-bound.'])
p=B/'SOURCE-CONTROLS.json';fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb')as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(dict(state=value['state'],checks=len(checks),wall_seconds=value['wall_seconds'])))
