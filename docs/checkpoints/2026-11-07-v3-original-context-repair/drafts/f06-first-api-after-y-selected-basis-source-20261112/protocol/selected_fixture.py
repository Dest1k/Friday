"""Declared synthetic selected-boot metadata. No host collection or authority exists."""
OLD_BOOT='11111111-1111-4111-8111-111111111111'
BOOT_A='22222222-2222-4222-8222-222222222222'
BOOT_B='33333333-3333-4333-8333-333333333333'
POSITIVE={'positive_bootA_first','positive_bootB_repeat'}
BOOT=BOOT_A if CONTROL=='positive_bootA_first' else BOOT_B
VARIANT='first_postpower' if CONTROL=='positive_bootA_first' else 'repeat_postpower_Qwen_loading'

def runtime_fixture(observation, *, old=False):
    boot=OLD_BOOT if old else BOOT
    base=910010 if old else (920010 if boot==BOOT_A else 930010)
    gateway=dict(pid=base,start_time=400 if old else 600,boot_id=boot)
    dashboard=dict(pid=base+1,start_time=410 if old else 610,boot_id=boot)
    observation['gateway']=gateway
    observation['services']={}
    groups={'gateway':'/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-gateway-1b7e7667.service','dashboard':'/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-dashboard.service'}
    for name,ident in [('gateway',gateway),('dashboard',dashboard)]:
        observation['services'][name]={'identity':dict(ident),'unit':dict(ActiveState='active',ControlGroup=groups[name],ControlPID='0',InvocationID=('1' if old else ('2' if boot==BOOT_A else '3'))*31+('a' if name=='gateway' else 'b'),LoadState='loaded',MainPID=str(ident['pid']),NRestarts='0',RuntimeMaxUSec='infinity',SubState='running',UnitFileState='enabled')}
    b=observation['f06_mutable_boundary']['B']
    observation['native_readonly']=dict(schema='frw.gateway.ordinary-turn-readonly.v1',identity=dict(gateway),generation=10 if old else 11,quiescent=True,read_only=True,freshness='BOUNDED3S_SOCKET_PEERCRED_MONOTONIC_KERNEL_STATE_CAS',session_id=b['session_id'],session_key=b['session_key'])
    observation['f06_mutable_boundary']['gateway']=dict(gateway)
    refresh(observation)

def selected_documents():
    """Synthetic canonical Root documents; production functions authenticate them."""
    global SELECTED,SELECTION_REF,BASIS,ROOT_CURRENT,ROOT_SELECTION,RECOVERY,DELTA,READINESS,RECOVERED_AT
    if CONTROL=='persistent_database':actual['databases']['dest']['messages']+=1;refresh(actual)
    elif CONTROL=='persistent_source':actual['source']['sha256']='0'*64;refresh(actual)
    elif CONTROL=='persistent_config':actual['profile_configs']['SYNTHETIC-extra']={'path':'/SYNTHETIC/config','bytes':1,'sha256':'0'*64};refresh(actual)
    elif CONTROL=='persistent_history':
        actual['history']['records'][0][1]='0'*64;actual['history']['manifest_sha256']=obs_digest(actual['history']['records']);refresh(actual)
    elif CONTROL=='persistent_cursor':actual['cursor']['sha256']='0'*64;refresh(actual)
    elif CONTROL=='persistent_cipher':actual['source']['bytes']+=1;refresh(actual)
    elif CONTROL=='extra_STATE':actual['custody']['records'].append(['SYNTHETIC-extra-state.json',dict(actual['custody']['records'][0][1])]);actual['custody']['records'].sort(key=lambda r:tuple(r[0].split('/')));refresh(actual)
    elif CONTROL=='native_pid':actual['native_readonly']['identity']['pid']+=10
    elif CONTROL=='native_session':actual['native_readonly']['session_id']='SYNTHETIC-other'
    elif CONTROL=='native_quiescent':actual['native_readonly']['quiescent']=False
    elif CONTROL=='service_inactive':actual['services']['dashboard']['unit']['ActiveState']='inactive'
    elif CONTROL=='service_invocation_old':actual['services']['dashboard']['unit']['InvocationID']=old_actual['services']['dashboard']['unit']['InvocationID']
    pb=module(SNAPSHOT/'postboot_transition.py','SYNTHETIC_POSTBOOT_SCHEMA_CONSTANTS_ONLY')
    anchor=put('selected-basis/current-observation.json',actual)
    changed=sorted(k for k in old_actual if encoded(old_actual[k])!=encoded(actual[k]))
    changed_b=sorted(k for k in boundary if encoded(boundary[k])!=encoded(actual['f06_mutable_boundary'][k]))
    RECOVERED_AT=time.time()-90
    at=datetime.datetime.fromtimestamp(RECOVERED_AT,datetime.timezone(datetime.timedelta(hours=3))).isoformat()
    delta=dict(schema='friday.root.postpower.observed-delta.v1',at_moscow=at,scope='SYNTHETIC explicitly selected boot only',current_observation=anchor,persistent_fields_unchanged={k:True for k in pb._PERSISTENT},custody_delta={'added':[y.LEAF],'removed':[],'changed':[]},changed_top_level_keys=changed,mutable_boundary_changed_keys=changed_b,new_admission=False)
    initial=put('selected-basis/initial.json',{'SYNTHETIC':'metadata descriptor, not actual runtime'})
    recovery=dict(schema='friday.root.postpower.recovery-acceptance.v1',at_moscow=at,operator='Root',initial=initial)
    if VARIANT=='first_postpower':
        delta.update(old_proof_sha256=F.Y_PROOF['sha256'],before_gateway=old_actual['gateway'],after_gateway=actual['gateway'],old_R106_expires_at_preserved=M.EXISTING_EXPIRES,old_R106_expired_and_old_boot=True)
        recovery.update(state='ACCEPT_INSTALLED_SOURCE_DATA_READONLY_RUNTIME_AND_DEPENDENCY_RECOVERY_NOT_USER_TEST_ADMISSION',manifest_integrity=initial,native_routing=initial,providers=initial,native_PEER_channel=initial,old_Y_no_user_API_assessment=M.Y_SAVED_ASSESSMENT,installed207_preserved=True,source_native17891_plugins52_byteexact=True,DB_quickcheck_OK_messages=[30,196,5510],all3_full_DBmetadata_unchanged_from_Y=True,canonical512_first_F06_run_absent=True,current_gateway=actual['gateway'],dashboard_pid=actual['services']['dashboard']['identity']['pid'],permanent_services_infinity=True,model_inference_or_user_send_or_install_replayed=False,original_clocks_and_R106_expiry_preserved=True,R106_current_validity='EXPIRED_AND_DIFFERENT_BOOT_CANNOT_ADMIT',new_admission_or_clock=False)
    else:
        delta.update(current_gateway=actual['gateway'],previous_verified_boot=pb.HISTORICAL_PREVIOUS_BOOT,Qwen='OWNER_REPORT_LOADING_NO_INFERENCE_ADMISSION',current_runtime_source_plugin_hashes_verified=True,prior_full17891_integrity_reused=pb.HISTORICAL_FULL_MANIFEST['sha256']+'; no installed source writes since',full_native17891_rehashed_this_operation=False)
        recovery.update(state='ACCEPT_POSTBOOT_SOURCE_PERSISTENT_DATA_AND_READONLY_RUNTIME_BASIS_QWEN_LOADING_NOT_USER_TEST_ADMISSION',boot_id=BOOT,current_observation=anchor,prior_full_manifest_integrity=pb.HISTORICAL_FULL_MANIFEST,full17891_rerun=False,why_reuse_valid='No installed-source writes since full17891/plugin52 verification; canonical4 and current executing14/runtime+52plugin hashes rechecked through unchanged checker',Qwen='OWNER_REPORT_LOADING_NO_LIVE_INFERENCE_ADMISSION',all3DBquickcheck_and_fullmetadata='OK_30_196_5510_leasespending0',first_F06_user_API='NOT_RUN',previous_recovery=pb.HISTORICAL_PREVIOUS_RECOVERY,new_admission_clock_or_replay=False)
    DELTA=put('selected-basis/delta.json',delta)
    recovery['persistent_runtime_delta']=DELTA
    RECOVERY=put('selected-basis/recovery.json',recovery)
    BASIS=dict(recovery_acceptance=RECOVERY,persistent_runtime_delta=DELTA,postboot_observation=anchor)
    current_created=time.time()-120
    ROOT_CURRENT=dict(schema='frw.Root.ordinary-independent-history-admission.v1',operator='Root',accepted=True,authority_id='SYNTHETIC-Root-current-'+BOOT[-12:],scope=A.scope(),run_scenarios={M.ORIGINAL_RUN:M.ORIGINAL_SCENARIO_SHA},ordered_predecessors={},same_canonical_local_run=False,created_at=current_created,expires_at=current_created+3000,supersedes={'authority_id':M.EXISTING_AUTHORITY_ID,'reason':'SYNTHETIC missing first API only, explicit current admission; never actual Root authority'})
    if CONTROL=='current_expired':ROOT_CURRENT['expires_at']=time.time()-10
    elif CONTROL=='current_wrongscope':ROOT_CURRENT['scope']={'SYNTHETIC':'wrong'}
    elif CONTROL=='current_wrongrun':ROOT_CURRENT['run_scenarios']={'SYNTHETIC-wrong':'1'*64}
    elif CONTROL=='current_wrongparent':ROOT_CURRENT['supersedes']['authority_id']='SYNTHETIC-wrong'
    elif CONTROL=='current_wrongid':ROOT_CURRENT['authority_id']='UNBOUND'
    fake_unknown_ids=tuple('SYNTHETIC-unknown-'+str(i) for i in range(3))
    fake_history={('SYNTHETIC-unknown-'+str(i) if i<3 else 'SYNTHETIC-history-'+str(i)):dict(send_state='unknown' if i<3 else 'closed',unknown_retained=i<3,new_effect_replay_authorized=False) for i in range(45)}
    M.HISTORICAL_HISTORY_SHA256=sha(encoded(fake_history));M.HISTORICAL_UNKNOWN_IDS=fake_unknown_ids;M.GATEWAY_STATE_PATH=str(H/'gateway_state.json')
    ROOT_CURRENT.pop('ordered_predecessors',None)
    ROOT_CURRENT.update(history=fake_history,new_independent_inputs_only=True,no_old_task_replay=True,old_rows_modified=False,unknown_effects_resolved=False,product_or_B00_acceptance=False,new_trial_for_historical_task=False,canonical_encoding={'canonical_sha256':"json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(',', ':')) with no trailing newline",'tester_sha256':"bot_tester.encoded(scenario): json.dumps(scenario, ensure_ascii=True, sort_keys=True) + newline"},boot_id=BOOT,gateway=dict(pid=actual['gateway']['pid'],start_time=actual['gateway']['start_time'],state_path=M.GATEWAY_STATE_PATH,maximum_staleness_seconds=600))
    if CONTROL=='current_history_drift':ROOT_CURRENT['history']['SYNTHETIC-history-44']['send_state']='changed'
    elif CONTROL=='current_unknown_replay':ROOT_CURRENT['history']['SYNTHETIC-unknown-0']['new_effect_replay_authorized']=True;M.HISTORICAL_HISTORY_SHA256=sha(encoded(ROOT_CURRENT['history']))
    elif CONTROL=='current_policy_flag':ROOT_CURRENT['no_old_task_replay']=False
    elif CONTROL=='current_encoding':ROOT_CURRENT['canonical_encoding']['tester_sha256']='SYNTHETIC-wrong'
    elif CONTROL=='current_physical_tuple':ROOT_CURRENT['gateway']['pid']+=1
    SELECTED=put('private-current-admission/CURRENT-ROOT-DOCUMENT.json',ROOT_CURRENT)
    if CONTROL=='current_oldR106':SELECTED=M.EXISTING_AUTHORITY
    READINESS=put('selected-readiness/ROOT-READINESS.json',{'SYNTHETIC':True,'operator':'Root','current_operation_dependencies_ready':True,'basis':BASIS,'grants_actual_readiness':False})
    ROOT_SELECTION=dict(schema=M.SELECTION_SCHEMA,operator='Root',status=M.SELECTION_STATUS,historical_R106=M.EXISTING_AUTHORITY,selected_admission=SELECTED,selected_authority_id=ROOT_CURRENT['authority_id'],predecessor_authority_id=M.EXISTING_AUTHORITY_ID,original_run_id=M.ORIGINAL_RUN,scenario_sha256=M.ORIGINAL_SCENARIO_SHA,source=fake_source,scope=A.scope(),y_preintent_closure=M.Y_PREINTENT_CLOSURE,y_saved_assessment=M.Y_SAVED_ASSESSMENT,y_independent_review=M.Y_INDEPENDENT_REVIEW,**BASIS,boot_id=BOOT,current_operation_dependencies_ready=True,readiness_evidence=READINESS,created_at=time.time()-50,expires_at=time.time()+1000)
    ROOT_SELECTION.update({k:True for k in M.SELECTION_BOOLS})
    changes={'selection_wrongscope':('scope',{}),'selection_wrongrun':('original_run_id','SYNTHETIC-wrong'),'selection_wrongsource':('source',dict(fake_source,sha256='0'*64)),'selection_wrongparent':('predecessor_authority_id','SYNTHETIC-wrong'),'selection_wrongid':('selected_authority_id','SYNTHETIC-wrong'),'selection_wrongboot':('boot_id',OLD_BOOT),'selection_readiness_false':('current_operation_dependencies_ready',False),'selection_expired':('expires_at',time.time()-1)}
    if CONTROL in changes:
        key,value=changes[CONTROL];ROOT_SELECTION[key]=value
    if CONTROL=='selection_readiness_hash':ROOT_SELECTION['readiness_evidence']=dict(READINESS,sha256='0'*64)
    if CONTROL=='selection_mixedbasis':ROOT_SELECTION['persistent_runtime_delta']=RECOVERY
    SELECTION_REF=put('private-current-admission/SELECTION.json',ROOT_SELECTION)
