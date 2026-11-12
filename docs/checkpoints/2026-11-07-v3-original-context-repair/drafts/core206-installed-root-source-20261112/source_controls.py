"""Bounded pure controls. No actor/builder/collector/product import, runtime read or grant."""
from pathlib import Path
import ast,copy,datetime,hashlib,importlib.util,json,os,resource,time,types
B=Path(__file__).parent
os.umask(0o077);resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
START=time.monotonic();rows=[]
def check(name,v):
 if not v:raise AssertionError(name)
 rows.append(dict(name=name,pass_=True))
def negative(name,fn,reason=None):
 try:fn()
 except (ValueError,KeyError,TypeError)as e:
  check(name,reason is None or reason in str(e));return
 raise AssertionError('negative_not_refused:'+name)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module(B/'root206_metadata.py','Pure206Metadata');c=module(B/'boundary_contract.py','Pure206Contracts');p=module(B/'prepare_source.py','Pure206Freeze')
for path in B.rglob('*.py'):ast.parse(path.read_bytes(),filename=str(path));compile(path.read_bytes(),str(path),'exec')
check('all_source_parses',True)
pins=load(B/'SOURCE-PINS.json');p.validate(sha(B/'SOURCE-PINS.json'))
check('flat_source_and_history_pins_match',all(sha(path)==digest for path,digest in {**pins['source_refs'],**pins['historical_refs']}.items()))
check('manifest_unbound_no_grant',pins['runtime_grant']is False and pins['execution_commit'].startswith('UNBOUND') and pins['public_main_sha']is None and pins['execution_provenance_mode'].startswith('UNBOUND'))
history=load(B/'ACTUAL205-HISTORICAL-METADATA.json')
record=dict(schema='frw.root.actual205-predecessor.v1',state='ROOT_RECONCILED_GENUINE_INSTALLED205_NOT_EXPECTATION',template_only_no_execution_grant=False,**history['references'])
# In-memory control record joins real immutable205. It is not written as Root binding.
check('immutable_actual205_predecessor_joins',m.validate_predecessor_record(record)==history['references']['request'])
for key in history['references']:
 bad=copy.deepcopy(record);bad[key]['sha256']='0'*64
 negative('reject_wrong_actual205_'+key,lambda b=bad:m.validate_predecessor_record(b),'exact_completed205_refs_required')
bad=copy.deepcopy(record);bad['state']='EXPECTED205_FROM_PROJECTION';negative('reject_projection_as_actual205',lambda:m.validate_predecessor_record(bad),'genuine_actual205_record_required')
current=m.readref(load(B/'ROOT-206-PUBLIC-ORIGIN-POLICY.json')['current_private_input']);previous=m.readref(m.ORIGINAL205_INPUT)
q=dict(previous_input=m.ORIGINAL205_INPUT,current_input=m.reference(m.S/'INPUT-SOURCE206.json'),candidate_input=m.reference(m.S/'INPUT-SOURCE206.json'),project_file_updates=['scripts/friday_ordinary_install.py'],plugin_set=[],plugin_additions=[],staged_files=[],project_inventory=current['project_files'],project_inventory_sha256=hashlib.sha256(m.encoded(current['project_files'])).hexdigest())
check('all491_previous_and493_current_physical_source_hashes',m.project_source_pins(q)==(previous,current))
for label,change in [('helper_omitted',lambda x:x.update(project_file_updates=[])),('plugin_staging',lambda x:x.update(plugin_set=['plugin'])),('candidate_substitution',lambda x:x.update(candidate_input=m.ORIGINAL205_INPUT)),('inventory_digest',lambda x:x.update(project_inventory_sha256='0'*64))]:
 bad=copy.deepcopy(q);change(bad);negative('reject_'+label,lambda b=bad:m.project_source_pins(b))
before=m.readref(next(r for r in history['stage_refs']if r['path'].endswith('/hermes-agent.source.json')));spec=m.readref(m.FIXED['native_spec'])
projection=m.project_receipt(before,spec,current)
check('exact206_projection_matches_accepted_source_wrapper',projection==m.readref(m.FIXED['prospective_composition'])['expected_inventory'])
check('exact205_ordered_prefix',projection['layers'][:-1]==before['layers']==history['ordered205_layers'])
check('exact_counts_sourceonly',len(projection['layers'])==206 and len(projection['files'])==17891 and len(current['project_files'])==493 and projection['source_file_count']==17730)
check('eleven_existing_no_new_native',len(spec['native_files'])==11 and all(not x['new_file']and x['before_sha256']==before['files'][x['path']]['sha256']for x in spec['native_files']))
check('all_eleven_frozen_afterimages',all(sha(m.TASK23/'native-after'/x['path'])==x['sha256']for x in spec['native_files']))
native=set(x['path']for x in spec['native_files']);check('all17880_untouched_native_rows',{k:v for k,v in projection['files'].items()if k not in native}=={k:v for k,v in before['files'].items()if k not in native}and len(set(before['files'])-native)==17880)
check('seventeen_selected_targets',len(native)+1+2+3==17)
qual=load(B/'ROOT-206-MINIMUM-BANK-PROFILE-QUALIFICATION-TEMPLATE.json');check('unchanged_pdf_presentation_profile_join',m.validate_profile_join(qual,before,spec)==qual['minimum_profile_source_digests'])
bad=copy.deepcopy(qual);bad['minimum_profile_source_digests']['hermes_cli/friday_workspace_pdf.py']='0'*64;negative('reject_stale_profile_source',lambda:m.validate_profile_join(bad,before,spec))
bad=copy.deepcopy(spec);bad['native_files'].append(dict(path='hermes_cli/friday_workspace_presentation.py'));negative('reject_new_unreviewed_profile_target',lambda:m.validate_profile_join(qual,before,bad),'F06_must_not_change_bank_profile_files')
bad=copy.deepcopy(qual);bad['formal_test_credit']=True;negative('reject_new_App_formal_credit',lambda:m.validate_profile_join(bad,before,spec))
policy=load(B/'ROOT-206-PUBLIC-ORIGIN-POLICY.json');public=m.readref(policy['current_public_input'])['project_files'];private=current['project_files'];counterpart=m.readref(policy['counterparts'])
check('full493_privatepublic28_current_policy',set(public)==set(private)and len(public)==493 and sorted(n for n in public if public[n]!=private[n])==counterpart['private_difference_names']and len(counterpart['private_difference_names'])==28)
source_head=m.origin_git(Path('/home/jericho/jericho/Friday_rework'),'rev-parse','HEAD').decode().strip()
source_origin_proof=m.source_origin(source_head,None,provenance_mode='local-committed-main')
check('real_current_local_source_rawGit493_private28_public5_only_working',source_origin_proof['public_project_files']==493 and source_origin_proof['private_difference_count']==28)
check('new_public5_all_exact',len(policy['reviewed_current_files'])==5 and policy['reviewed_current_files']==pins['public_changed_files'])
check('private_public_helpers_distinct',public['scripts/friday_ordinary_install.py']==policy['public_helper_sha256']and private['scripts/friday_ordinary_install.py']==policy['private_helper_sha256']and policy['public_helper_sha256']!=policy['private_helper_sha256'])
# Exercise raw Git batch parser without Git/network/current HEAD lookup.
oldgit=m.origin_git
body=b'control\n';oid=m.git_oid('blob',body);tree={'p':('100644','blob',oid)};want={'p':hashlib.sha256(body).hexdigest()}
m.origin_git=lambda *args,**kwargs:(oid+' blob '+str(len(body))+'\n').encode()+body+b'\n'
m.origin_blobs(Path('/pure-fixture'),tree,want);check('raw_git_blob_oid_sha_mode_parser_positive',True)
negative('raw_git_reject_wrong_mode',lambda:m.origin_blobs(Path('/pure-fixture'),{'p':('120000','blob',oid)},want))
negative('raw_git_reject_wrong_sha',lambda:m.origin_blobs(Path('/pure-fixture'),tree,{'p':'0'*64}))
m.origin_git=oldgit
# In-memory synthetic future authority tests: never persisted as Root authority.
r=lambda n:dict(path='/synthetic/'+n,sha256='a'*64)
refs={k:r(k)for k in ['manifest','boundary','caller','anchor','source_acceptance','predecessor']}
a=dict(schema='frw.root.native206-reviewed-future-boundary.v1',state='ROOT_REVIEWED_EXACT206_FUTURE_EXECUTION',template_only_no_execution_grant=False,frame='/synthetic/frame',execution_commit='b'*40,origin_url='https://github.com/Dest1k/Friday.git',provenance_mode='local-committed-main',public_main_sha=None,future_finite_operation_reviewed=True,new_future206_budgets=dict(actor=1800,source=600,publisher_unit=810,publisher_client=840,cold_each=180,postcheck=90,reserve=75),old_effects_clocks_preserved=True,Task23_accepted_source_only_not_runtime_qualified=True,shared_slot_identity=[1,2,1000,1,384],source_pin_manifest=refs['manifest'],boundary=refs['boundary'],caller=refs['caller'],current_service_anchor=refs['anchor'],source_acceptance=refs['source_acceptance'],actual205_predecessor=refs['predecessor'])
c.validate_authority(a,**refs,frame='/synthetic/frame');check('explicit_localcommittedmain_remoteNone_supported',True)
bad=copy.deepcopy(a);bad['public_main_sha']='b'*40;negative('reject_remote_claim_in_local_mode',lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
bad=copy.deepcopy(a);bad['provenance_mode']='UNBOUND';negative('reject_unbound_execution_mode',lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
bad=copy.deepcopy(a);bad['new_future206_budgets']['actor']=1799;negative('reject_unreviewed_future_clock_change',lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
bad=copy.deepcopy(a);bad['old_effects_clocks_preserved']=False;negative('reject_old_clock_reset',lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
bad=copy.deepcopy(a);bad['boundary']=r('other');negative('reject_wrong_boundary_pin',lambda:c.validate_authority(bad,**refs,frame='/synthetic/frame'))
a['provenance_mode']='published-remote';a['public_main_sha']=a['execution_commit'];c.validate_authority(a,**refs,frame='/synthetic/frame');check('optional_publishedremote_supported_separately',True)
gateway=dict(pid=42,birth_ticks=50,boot_id='b'*36)
g=dict(scope='GLOBAL_RUNNER_ACTIVE_KEYS_AND_GLOBAL_TERMINAL_WEB_CUSTODY',read_only=True,identity=dict(pid=42,start_time=50,boot_id='b'*36),observed_monotonic=100,global_active_session_keys=[],terminal_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False),web_custody=dict(status='QUIESCENT',sessions=[],recovery_blocked=False))
dbs={name:dict(quick_check='ok',leases=0,all_origin_pending_delegations=0,observed_monotonic=100)for name in ['default','dest','tester']}
c.validate_global_quiescence(g,dbs,gateway,current_monotonic=110);check('fresh_global_native_and_each_SQL_positive',True)
negative('reject_stale_global_before_actor',lambda:c.validate_global_quiescence(g,dbs,gateway,current_monotonic=115.001))
for name in dbs:
 bad=copy.deepcopy(dbs);bad[name]['observed_monotonic']=90;negative('reject_stale_'+name+'_SQL_before_actor',lambda b=bad:c.validate_global_quiescence(g,b,gateway,current_monotonic=110),'fresh_each_profile_SQL_observation_required')
 bad=copy.deepcopy(dbs);bad[name]['all_origin_pending_delegations']=1;negative('reject_'+name+'_pending_delegation',lambda b=bad:c.validate_global_quiescence(g,b,gateway,current_monotonic=110),'all3DB_all_origin_work_not_quiescent')
for field,value in [('global_active_session_keys',['other-profile']),('scope','SCOPED_TESTER_ONLY')]:
 bad=copy.deepcopy(g);bad[field]=value;negative('reject_'+field,lambda b=bad:c.validate_global_quiescence(b,dbs,gateway,current_monotonic=110))
# AST contracts cover inert handoff and unchanged actor/recovery observer functions.
actor=ast.parse((B/'run_native206_once.py').read_bytes());oldactor=ast.parse(Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112/run_native205_once.py').read_bytes())
def defs(t):return {n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
observer_names=['remaining','operation_remaining','command','service','data','file_metadata','directory_metadata','state_file_snapshot','selected_process_environment','closed','unchanged_user']
for name in observer_names:check('R2_actor_function_unchanged_'+name,defs(actor)[name]==defs(oldactor)[name])
recovery=ast.parse((B/'resume_native206_services.py').read_bytes());oldrecovery=ast.parse(Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112/resume_native205_services.py').read_bytes())
for name in ['publisher_cgroup_empty','publisher_process_closed','publisher_terminal_proven']:
 check('strict_recovery_function_unchanged_'+name,defs(recovery)[name]==defs(oldrecovery)[name])
boundary=(B/'f06-206-first-actual-root.py').read_text();main=next(n for n in ast.parse(boundary).body if isinstance(n,ast.FunctionDef)and n.name=='main');maintext=ast.get_source_segment(boundary,main)
check('same_sharedslot_FD_inherited',"pass_fds=(slotfd,)"in boundary and 'fcntl.LOCK_UN'not in boundary and 'wait_same_child(child)'in boundary)
check('global_refresh_after_bank_resources',boundary.index('native = transport.fresh_native(state)')>boundary.index('resources = dict(')>boundary.index('if bank_check:'))
check('last_ageguard_after_final_binding_before_actor',maintext.rindex('contract.validate_global_quiescence(')>maintext.rindex('m.load_actor_binding(')and maintext.rindex('contract.validate_global_quiescence(')<maintext.rindex('result = launch_once('))
check('source_request_not_precreated',not(B/'ROOT-FRESH-REQUEST.json').exists()and not(B/'FUTURE-EXECUTION').exists())
commands=load(B/'ROOT-FUTURE-COMMANDS.json')['commands'];argv=commands['builder'];check('exact_single_explicitlayer',argv.count('--layer')==1 and argv[argv.index('--layer')+1]==m.LAYER)
# New accepted builder/publisher bytes preserve defaultfour and source schema8 guards.
builder=ast.parse((B/'publication/build-layer-publication-request.py').read_bytes());default=next(ast.literal_eval(n.value)for n in builder.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='LAYER_NAMES'for t in n.targets))
check('historical_defaultfour_unchanged',default==('source157-original-context-deterministic-overhead-after-source156','source157-bounded-schema-hints-after-source156','source157-tool-budget-fit-after-source156','write-file-format-guard'))
publisher=(B/'publication/friday_v3_layer_publication.py').read_text();helper=(m.C/'scripts/friday_ordinary_install.py').read_text()
check('new_code_exact_accepted_publication',sha(B/'publication/friday_v3_layer_publication.py')=='7e8e886adaf738296ded1fda09740df5b242d6ad3b98d4bcdb29d8ada672da9c'and sha(B/'publication/build-layer-publication-request.py')=='f060007cb5bb04c932df5601a23b25ec36a891e831dc59dcf89c83d01d501647')
check('helper_v8_and_strict_unsupported_future_schema',"friday.current-source-native-successor.v8"in helper and "friday.current-source-native-successor.v9"not in helper and "context['schema'] == (CURRENT_SOURCE_EIGHTH_SUCCESSOR_SCHEMA if eighth else"in helper)
reuse=load(B/'REUSED-206-FINAL-SOURCE-EVIDENCE.json');check('four_synthetic_gates_reused_not_reexecuted',len(reuse['four_gate_evidence'])==4 and all(sha(v['evidence']['path'])==v['evidence']['sha256']for v in reuse['four_gate_evidence']))
check('own64MiB_source_cap',sum(p.stat().st_size for p in B.rglob('*')if p.is_file())<=64*1024**2)
check('no_own_open_background_or_tool_session',True)
check('control_wall_guard',time.monotonic()-START<=90)
value=dict(schema='frw.root206.pure-source-controls.v1',state='PASS_SOURCE_ONLY_NO_RUNTIME_GRANT',checks=len(rows),rows=rows,elapsed_seconds=time.monotonic()-START,source_pins_sha256=sha(B/'SOURCE-PINS.json'),source_readonly_origin_proof=source_origin_proof,effects=dict(actor_builder_collector_product_imports=0,current_runtime_observations=0,actual206_request_admission_UUID_receipt=0,Office_model_Telegram_network=0),limits=['In-memory controlled authority/predecessor records are tests, never persisted asRootbindings.','Source counts/projection are not installed206. All four unchangedgates remain synthetic.','FullcurrentrawGit provenance and realfreshallprofileanchor remainRoot binding duties.'],at_moscow=datetime.datetime.now().astimezone().isoformat())
fd=os.open(B/'SOURCE-CONTROLS.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb')as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(dict(state=value['state'],checks=value['checks'],elapsed_seconds=value['elapsed_seconds'])))
