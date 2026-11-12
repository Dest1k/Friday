def fixture(mods=None):
 mods=mods or {};data=dict(code)
 def put(name,v,raw=False):
  p='/SYNTHETIC-T28-ONLY/'+name;raw=v if raw else A.encoded(v);data[p]=raw
  return dict(path=p,bytes=len(raw),sha256=A.digest(raw))
 def tweak(k,v):
  if k in mods:mods[k](v)
  return v
 source=dict(A.SOURCE);identity={'device':1,'inode':2,'size_bytes':23040,'uid':1,'mtime_ns':1,'ctime_ns':1}
 principal={'profile':'telegram-bot-8812646969','session_id':'SYNTHETIC-SESSION','session_key':'SYNTHETIC-KEY'}
 upload=dict(kind='document',path=source['path'],sha256=source['sha256'],stat=identity,filename='f06-new-encrypted.docx',mime_type=A.MIME,caption='SYNTHETIC-WRONG-REQUEST-NOT-A-CREDENTIAL')
 scenario=dict(tester_id=8812646969,peer_id=8751854128,peer_username='@jerichodevbot',deadline_seconds=300,max_updates=65,pace_seconds=1,steps=[{'input':upload,'observe':dict(A.OBSERVE)}])
 ack=tweak('ack',dict(message_id=11,date=1,chat={'id':8751854128,'type':'private'},**{'from':{'id':8812646969,'is_bot':True}},caption=upload['caption'],document=dict(file_id='SYNTHETIC-FILE-ID',file_unique_id='SYNTHETIC-UNIQUE-ID',file_size=23040,file_name='f06-new-encrypted.docx',mime_type=A.MIME)))
 # Canonical path strings are modeled only in this dict; no files are created there.
 def stored(name,v,rep=None):
  p=str(F.STATE/name);raw=A.encoded(v);data[p]=raw;r=dict(path=p,bytes=len(raw),sha256=A.digest(raw));recorded=dict(basename=name,bytes=len(raw),sha256=r['sha256'])
  if rep:recorded['representation']=rep
  return r,recorded
 ar,asr=stored('send-ack-SYNTHETIC-first-0-1.json',ack,'decoded-message-json')
 task=tweak('task',dict(filename='f06-new-encrypted.docx',mime_type=A.MIME,content_type='multipart/form-data; boundary=frw-'+'a'*64,body_sha256='b'*64,body_bytes=24000,method='sendDocument',chat_id='@jerichodevbot',input_sha256=source['sha256'],input_bytes=23040,input_stat=identity,caption=upload['caption'],scenario_sha256=A.digest(A.encoded(scenario))))
 tr,tsr=stored('send-task-SYNTHETIC-first-0-1.json',task)
 win=tweak('window',dict(step=0,send_attempts=1,send_intent_at=0,send_dispatch_at=0,send_timeout_seconds=10,deadline=300,run_id='SYNTHETIC-first',scenario_sha256=A.digest(A.encoded(scenario)),sent_message_id=11,sent_at=1,capture_until=181,window_seconds=180,ack=asr,task=tsr))
 wr,wsr=stored('send-window-SYNTHETIC-first-0-1.json',win)
 hr,hsr=stored('receive-SYNTHETIC-first-0-1-0.json',dict(kind='terminal_complete',sequence=0,context=dict(run_id='SYNTHETIC-first',scenario_sha256=A.digest(A.encoded(scenario)),window=wsr,sent_message_id=11,deadline=300)))
 run=tweak('run',dict(step=0,sent_ids=[11],sent_at=1,send_intent_at=0,send_dispatch_at=0,send_timeout_seconds=10,deadline=300,seen=[],message_ids=[],observations=[],receive_head=hsr,receive_sequence=0,capture_window_complete=True,id='SYNTHETIC-first',status='EVIDENCE_READY',send_state='sent',send_attempts=1,scenario=scenario,scenario_sha256=A.digest(A.encoded(scenario)),sent_message_id=11,sent_date=1,capture_until=181,sent_api_ack_reference=asr,sent_task_reference=tsr,sent_window_reference=wsr,request_metadata=task))
 rp=str(F.STATE/'runs'/'SYNTHETIC-first.json');raw=A.encoded(run);data[rp]=raw;rr=dict(path=rp,bytes=len(raw),sha256=A.digest(raw));sr={'run_id':'SYNTHETIC-first','run_sha256':rr['sha256'],'input_sha256':source['sha256']}
 dummy=put('dummy-proof.json',{'synthetic':True})
 old=dict(schema='frw.F06.original-docx-ordinary-first-wrongread.v2',phase='DOCX-WRONG-READ-INGRESS',status='ROOT_BOUND_EXACT_F06_FIRST_WRONGREAD',run_id=run['id'],scenario_sha256=run['scenario_sha256'],source=source,authority=dummy,boundary={'B':dict(principal,native_max_id=1)})
 binding=put('first-binding.json',dict(schema='frw.Root.F06.exact-first-wrongread-binding.v1',source=put('original-bound-source.py',b'#SYNTHETIC-NO-ACTUAL-CONSUMER',True),whole_effect_sha256='c'*64,contract=tweak('binding',old)))
 def judgement(k,schema,extra):
  d=dict(schema=schema,operator='Root',status='ROOT_BOUND',source_reference=sr,B=principal,source=source,**extra)
  return put(k+'.json',tweak(k,d))
 original=judgement('original_custody','frw.Root.F06.first-original-consumer-custody.v1',dict(canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,bound_source=json.loads(data[binding['path']])['source'],base_consumer_sha256=F.BASE_SHA,assessed_methods=['verify_capture_context','verify_window','verify_reply_custody','receive_inventory'],first_status=run['status'],capture_window_complete_present='capture_window_complete' in run,capture_window_complete=run.get('capture_window_complete'),original_clock_and_window_preserved=True,all_existing_raw_and_receipts_verified=True,known_partial_not_upgraded=True,late_arrivals_raw_only=True,first_semantic_PASS_required=False,acceptance='NOT_ESTABLISHED',receive_head=run.get('receive_head'),receive_sequence=run.get('receive_sequence'),method_assessment='VERIFIED_ORIGINAL_EXISTING_CUSTODY' if run.get('receive_head') else 'ORIGINAL_MISSING_HEAD_FAILURE_PRESERVED',receive_custody='VERIFIED_EXISTING_FULL_OR_PARTIAL' if run.get('receive_head') else 'MISSING_ORIGINAL_RECEIVE_HEAD_FAILURE_PRESERVED',missing_receive_failure_code='SYNTHETIC_ORIGINAL_FAILURE',terminal_receive=hr,retained_basis=[dummy]))
 closure=judgement('closure','frw.Root.F06.first-operation-closed.v1',dict(original_consumer_custody=original,actor_tree_closed=True,slot_released=True,no_pending_first_ingress=True,original_clock_preserved=True,raw_outcome_preserved=True))
 rec=judgement('reconciliation','frw.Root.F06.first-effect-reconciliation.v1',dict(canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,closure=closure,effect_disposition='SENT_CONFIRMED_SAME_SOURCE_INGRESSED',unknown_assumed_absent=False,no_reupload=True,raw_failures_and_UNKNOWN_preserved=True,next_operation='ONE_SEPARATE_CORRECT_READ_NO_UPLOAD'))
 cust=judgement('custody','frw.Root.F06.first-upload-private-custody.v1',dict(ack=ar,original_identity=identity,retained_source_sha256=source['sha256'],downloaded_source_sha256=source['sha256'],original_and_retained_CAS_verified=True))
 ingress=judgement('ingress','frw.Root.F06.same-B-source-ingress.v1',dict(platform_message_id=11,file_id=ack['document']['file_id'],file_unique_id=ack['document']['file_unique_id'],native_message_ids=[1,2],source_reference_observed=True))
 first=tweak('first',dict(schema='frw.Root.F06.closed-first-upload.v1',operator='Root',status='ROOT_BOUND_CLOSED_RECONCILED',source_reference=sr,source=source,B=principal,source_identity=identity,canonical_run=rr,first_binding=binding,ack=ar,task=tr,window=wr,closure=closure,root_reconciliation=rec,private_custody=cust,native_ingress=ingress))
 fr=put('closed-first.json',first)
 s=A.construct_scenario(supplied_password='SYNTHETIC-ONLY-NOT-A-REAL-SECRET',first_dependency=first)
 c=A.unbound();c.update(status='ROOT_BOUND_EXACT_F06_CORRECTREAD',run_id='SYNTHETIC-correct',authority=dummy,authority_id='ordinary-independent-SYNTHETIC',source_reference=sr,first_ingress=fr,first_validator=dict(path=str(C/'first_ingress.py'),bytes=len(code[str(C/'first_ingress.py')]),sha256=A.digest(code[str(C/'first_ingress.py')])))
 c.update(scenario_ref=put('correct-scenario.json',s),scenario_sha256=A.digest(A.encoded(s)),adapter=put('adapter-placeholder',b'x',True),footer=put('footer-placeholder',b'x',True),actual_root_B_checker=dummy,root_current_proof=dummy)
 c['product']=dict(source_layers=207,project_files=495,native_files=17891,plugin_files=52,base_source_files=17730,source_receipt_sha256='1'*64,input_sha256='2'*64)
 c['installation']=dict(closure=dummy,source_acceptance=dummy,product=c['product'],runtime_hashes={'SYNTHETIC-only.py':'3'*64})
 c['boundary']={k:'4'*64 for k in A.BOUNDARY};c['boundary'].update(gateway={'pid':1,'start_time':1},B=dict(principal,native_max_id=2),phase_unconsumed=True,uploads_this_operation=0,producer_calls=0,restarts=0)
 c['resources']=dict(A.TIMING,cpu_seconds=60,max_rss_bytes=512*1024**2,disk_bytes=32*1024**2,clock=dummy,owned_parent_wait_cleanup=dummy)
 c['root_proofs']={k:dummy for k in A.PROOFS};c['root_proofs']['first_upload_reconciliation']=rec
 oracle=dict(schema='frw.Root.F06.correct-read-private-oracle.v1',operator='Root',status='ROOT_BOUND',source=source,source_reference=sr,phase=A.PHASE,scenario_sha256=c['scenario_sha256'],correct_secret_verified_for_same_source=True,actual_retained_first_paragraph_oracle=True,toy_placeholder_oracle=False,no_new_document_or_derivative=True,technical_secret_delta_review_required_after_reply=True,original_private_request_exemption_only=True,future_reply_acceptance='NOT_ESTABLISHED',retained_basis=[dummy])
 c['root_proofs']['correct_read_private_oracle']=put('oracle.json',tweak('oracle',oracle))
 return c,s,first,lambda p,**kw:data[str(p)],data
