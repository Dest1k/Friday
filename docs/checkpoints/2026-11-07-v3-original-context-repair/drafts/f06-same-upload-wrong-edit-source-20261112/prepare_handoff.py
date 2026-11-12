from pathlib import Path
import ast,json,types,hashlib
B=Path(__file__).resolve().parent;C=B/'candidate';D=B/'templates'
def mod(p):
 m=types.ModuleType('inert_own_source');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
A=mod(C/'f06_source.py');V=mod(C/'first_ingress.py');M=mod(C/'current_root.py')
def save(name,v):(D/name).write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
save('CONTRACT.UNBOUND.json',A.unbound())
save('ROOT-BINDING-INPUTS.UNBOUND.json',{'schema':'frw.Root.F06.same-upload-wrongedit-driver.v1','status':'UNBOUND_NOT_GRANTED','contract':A.unbound(),'source_freeze':None,'independent_review':None,'workdir':None,'slot_identity':None,'expected_binding_sha256':None})
save('CURRENT-ROOT-PROOF.UNBOUND.json',M.unbound_proof())
save('PRIVATE-CHANGE.UNBOUND.json',{'kind':'literal_replace','old':None,'new':None,'expected_occurrences':1})
save('PRIVATE-SCENARIO-CONSTRUCTOR.UNBOUND.json',{'state':'UNBOUND_NOT_GRANTED','call':'f06_source.construct_scenario(supplied_password=<Root-private deliberatewrong string>,change_spec=<Root actual authorized PRIVATE-CHANGE>,first_dependency=<actual closedfirst>,correct_dependency=<actual acceptedcorrect>)','supplied_password':None,'actual_first_dependency':None,'actual_correct_dependency':None,'change_spec':None,'plaintext_old_new_values':'NOT_READ_OR_INVENTED','one_text_message':True,'no_wire_source_reference_or_reply_or_path':True,'no_second_upload':True,'max_documents':0,'actual_reply_grading':'NOT_ESTABLISHED'})
save('ROOT-CLOCK.UNBOUND.json',{'schema':'frw.Root.F06.original-finite-clock.v1','started_at':None,'deadline_at':None,'started_monotonic':None,'deadline_monotonic':None,'boot_id':None})
prior=Path('/home/jericho/.cache/FRW-SOL-V3-F06-CANONICAL-BINDING-LAUNCH-PROTOCOL-CORE-20261112/templates/correct')
for name in ['FIRST-INGRESS.UNBOUND.json','ORIGINAL-CONSUMER-CUSTODY.UNBOUND.json','INSTALLATION.UNBOUND.json']:(D/name).write_bytes((prior/name).read_bytes())
fields={'schema':'frw.Root.F06.closed-correct-read.v1','operator':'Root','status':'UNBOUND_NOT_GRANTED','source':dict(A.SOURCE),'source_reference':None,'B':None,'canonical_run':None,'correct_binding':None,'ack':None,'task':None,'window':None,'closure':None,'assessment':None,'root_reconciliation':None,'private_custody':None,'native_ingress':None};save('CORRECT-READ.UNBOUND.json',fields)
common={'operator':'Root','status':'UNBOUND_NOT_GRANTED','source':dict(A.SOURCE),'source_reference':None,'B':None}
records={}
records['correct_closed']=dict(common,schema='frw.Root.F06.correct-read-closed.v1',canonical_run=None,correct_binding=None,actor_tree_closed=None,slot_released=None,no_pending_effect=None,original_clock_preserved=None,raw_outcome_preserved=None,original_consumer_custody=None,completed_at=None,clock=None)
records['correct_custody']=dict(common,schema='frw.Root.F06.correct-original-consumer-custody.v1',canonical_run=None,correct_binding=None,bound_source=None,base_consumer_sha256=A.BASE_SHA,assessed_methods=['verify_capture_context','verify_window','verify_reply_custody','receive_inventory'],capture_window_complete=None,terminal_complete=None,all_existing_raw_and_receipts_verified=None,late_arrivals_raw_only=None,original_clock_and_window_preserved=None,ack=None,task=None,window=None,terminal_receive=None,retained_basis=None)
records['correct_assessment']=dict(common,schema='frw.Root.F06.correct-read-semantic-assessment.v1',canonical_run=None,correct_binding=None,original_consumer_custody=None,outcome=None,correct_secret_verified_for_same_source=None,actual_first_paragraph_and_structure_match=None,toy_placeholder_oracle=None,new_reply_and_technical_secret_delta_privately_assessed=None,no_secret_echo_or_unrequested_new_secret_persistence=None,original_private_request_exemption_only=None,no_new_artifact_or_source_change=None,full180_required_and_verified=None,unknown_assumed_absent=None,retained_basis=None)
records['correct_reconciliation']=dict(common,schema='frw.Root.F06.correct-read-effect-reconciliation.v1',canonical_run=None,correct_binding=None,ack=None,task=None,window=None,closure=None,assessment=None,private_custody=None,native_ingress=None,effect_disposition=None,unknown_assumed_absent=None,no_reupload=None,raw_failures_and_UNKNOWN_preserved=None,next_operation=None,next_scenario_sha256=None,change_spec=None)
records['correct_private_custody']=dict(common,schema='frw.Root.F06.correct-read-private-custody.v1',canonical_run=None,original_source_identity=None,retained_source_sha256=None,downloaded_source_sha256=None,before_after_full_CAS_verified=None,no_new_document_or_output=None)
records['correct_native_ingress']=dict(common,schema='frw.Root.F06.correct-read-native-ingress.v1',canonical_run=None,platform_message_id=None,native_message_ids=None,actual_same_source_reference_observed=None)
keys=('legitimate_exact_change_authorized','actual_fixture_old_literal_and_unique_occurrence_privately_verified','deliberately_wrong_secret_verified_for_same_source','wrong_secret_distinct_from_previous_correct_secret','latest_supplied_wrong_password_only','previous_correct_password_or_history_use_prohibited','no_brute_force_or_password_search','expected_no_source_change_plaintext_output_or_delivery','new_reply_tool_arguments_files_and_secret_delta_review_required','original_private_request_exemption_only','actual_before_after_source_and_artifact_CAS_required')
records['wrong_edit_private_oracle']=dict(common,schema='frw.Root.F06.wrong-edit-private-oracle.v1',correct_read=None,phase=A.PHASE,scenario_sha256=None,change_spec=None,**{k:None for k in keys},future_reply_acceptance='NOT_ESTABLISHED',correct_edit_authorized=None,automatic_followup_authorized=None,max_outbound_documents=None,retained_basis=None)
# Prior unbound first-history/lineage/privacy recipes retain their null truth fields.
old=json.loads((prior/'ROOT-REVIEW-TEMPLATES.UNBOUND.json').read_bytes())
for k in ('correct_read_private_oracle',):old.pop(k,None)
for k,v in old.items():
 if type(v) is dict:
  if v.get('phase')=='DOCX-CORRECT-READ-SAME-UPLOAD':v['phase']=A.PHASE
  if v.get('schema')=='frw.Root.F06.same-upload-correctread-installed-runtime-privacy-review.v1':v['schema']='frw.Root.F06.same-upload-wrongedit-installed-runtime-privacy-review.v1'
  if k in ('history_semantic_review','runtime_privacy_review','retained_g6_source_lineage','source_ingress_lineage'):
   v.update(correct_read=None,change_spec=None,actual_correct_read_closed_semantically_accepted=None)
old.update(records);old['schema']='frw.Root.F06.same-upload-wrongedit-review-templates.v1'
old['runtime_privacy_review'].update(phase=A.PHASE,source_reference=None,latest_supplied_wrong_password_only=None,previous_correct_password_or_history_must_not_be_used=None)
old['history_semantic_review'].update(latest_supplied_wrong_password_only_authorized=None,unknown_assumed_absent=None)
save('ROOT-REVIEW-TEMPLATES.UNBOUND.json',old)
save('POST-OP-ASSESSMENT.UNBOUND.json',{'schema':'frw.Root.F06.wrong-edit-postoperation-criteria.v1','operator':'Root','status':'UNBOUND_NOT_GRANTED','phase':A.PHASE,'canonical_run':None,'actual_binding':None,'actual_source_reference':None,'source_before_after_full_CAS':None,'original_uploaded_cipher_identity_and_downloaded_cipher_sha':None,'baseline_and_after_output_artifact_inventory':None,'actual_new_reply_custody_and_full180':None,'actual_used_codec_password_equals_supplied_wrong_only':None,'prior_correct_password_reuse_or_guessing':None,'no_source_edit_no_plaintext_no_new_output_or_delivery':None,'new_reply_tools_technical_rows_logs_memory_privately_checked':None,'intentional_original_private_request_exemption_only':None,'known_or_unknown_effects_and_rawfailures_preserved':None,'acceptance':'NOT_ESTABLISHED','no_automatic_retry_followup_or_correctedit':True})
print(json.dumps({'templates':len(list(D.iterdir())),'actual_operational_values_bound':False}))
