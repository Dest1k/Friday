"""Pure frame controls. No Office, secret/ciphertext reads or runtime inspection."""
import ast,copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B))
import f06_contract as c
import root_frame as root
import run_once as unit
import office_fixture_driver as driver

def run():
 rows=[]
 def check(name,action):
  action();rows.append(dict(name=name,passed=True))
 def yes(value):assert value
 def refused(action,code):
  try:action()
  except ValueError as exc:assert str(exc)==code,(str(exc),code)
  else:raise AssertionError('DID_NOT_REFUSE')
 check('exact_future_key',lambda:yes(c.operation(c.VERIFY_KEY,'verify-inputs')==B/'operations'/c.VERIFY_KEY))
 for mode,key in [('generate','generate-g6'),('generate','generate-g7'),('preflight','preflight-g1'),('verify-native-edits',c.VERIFY_KEY),('verify-inputs','verify-inputs-g6-oracle2'),('verify-inputs','verify-inputs-anything'),('verify-inputs','../generate-g6')]:
  check('reject_'+mode+'_'+key,lambda mode=mode,key=key:refused(lambda:c.operation(key,mode),'EXACT_VERIFY_INPUTS_ONLY_OPERATION'))
 for mode in ('generate','preflight','produce','verify-native-edits',''):
  check('limits_reject_'+mode,lambda mode=mode:refused(lambda:c.limits(mode),'VERIFY_INPUTS_ONLY_MODE'))
 lim=c.limits('verify-inputs')
 expected=dict(whole_wall_seconds=300,aggregate_CPU_seconds=180,memory_bytes=2147483648,swap_bytes=0,affinity_cpus=2,pids_max=128,namespace_tmpfs_bytes=16777216,own_cap_bytes=100663296,cleanup_reserve_seconds=15,per_process_AS_bytes=2147483648,per_process_FSIZE_bytes=8388608,max_Office_starts=3,max_stores=0,max_password_probes=21)
 check('unchanged_resource_limits_zero_stores_21_probes',lambda:yes(lim==expected))
 lim['max_stores']=7
 check('caller_cannot_mutate_shared_limits',lambda:yes(c.limits('verify-inputs')==expected))
 manifest=json.loads((B/'RECONCILED-INPUTS.json').read_text())
 check('full_seven_original_g6_metadata',lambda:yes(len(c.reconciled_contract(manifest))==7))
 cases={
 'partial6':lambda x:(x.update(known_prefix_count=6),x['fixtures'].pop()),
 'partial0':lambda x:x.update(known_prefix_count=0,fixtures=[]),
 'copy_as_original':lambda x:x.update(custody_root=str(B/'operations/generate-g6/work/encrypted-inputs')),
 'promoted_original_fail':lambda x:x.update(original_all_pass=True),
 'reset_original_clock':lambda x:x.update(original_clocks_reset=True),
 'replayed_original':lambda x:x.update(original_operation_replay=True),
 'wrong_oldsource':lambda x:x.update(original_source_pins_sha256='0'*64),
 'wrong_raw_result':lambda x:x['original_oracle'].update(sha256='0'*64),
 'wrong_raw_custody':lambda x:x['original_custody'].update(sha256='0'*64),
 'forged_closure':lambda x:x['original_closure'].update(path=str(B/'fake-closure.json')),
 'wrong_family_order':lambda x:x['fixtures'].reverse(),
 'wrong_profile':lambda x:x['fixtures'][6].update(fixture_profile='compatible1.3_or_Agile'),
 'hostpath_is_namespace':lambda x:x['fixtures'][0].update(path='/inputs/encrypted-inputs/'+c.NAMES[0]),
 'rawpath_is_host':lambda x:x['fixtures'][0].update(raw_original_namespace_path=x['fixtures'][0]['path']),
 'unbounded_file':lambda x:x['fixtures'][0].update(bytes=8388609),
 'bad_sha':lambda x:x['fixtures'][0].update(sha256='g'*64),
 'missing_identity':lambda x:x['fixtures'][0].pop('identity'),
 }
 for name,mutate in cases.items():
  x=copy.deepcopy(manifest);mutate(x)
  def action(x=x):
   try:c.reconciled_contract(x)
   except ValueError:return
   raise AssertionError('INVALID_RECONCILIATION_ACCEPTED')
  check('reject_'+name,action)
 saved_codec_state=c.ORACLE_CODEC_STATE;c.ORACLE_CODEC_STATE='PENDING_ROOT_FINAL_CODEC'
 check('pendingcodec_contract_guard',lambda:refused(c.require_final_codec,'FINAL_ORACLE_CODEC_PENDING_ROOT'))
 check('pendingcodec_root_before_admission_read',lambda:refused(lambda:root.validate_admission(Path('/must-not-read'),'0'*64),'FINAL_ORACLE_CODEC_PENDING_ROOT'))
 check('pendingcodec_unit_before_admission_read',lambda:refused(unit.main,'FINAL_ORACLE_CODEC_PENDING_ROOT'))
 check('pendingcodec_stage_before_mkdir_or_read',lambda:refused(lambda:unit.stage('verify-inputs',Path('/must-not-create'),{'operation_key':c.VERIFY_KEY}),'FINAL_ORACLE_CODEC_PENDING_ROOT'))
 check('invalidmode_stage_before_mkdir_or_read',lambda:refused(lambda:unit.stage('generate',Path('/must-not-create'),{'operation_key':'generate-g6'}),'EXACT_VERIFY_INPUTS_ONLY_OPERATION'))
 check('pendingcodec_driver_before_argparse_or_read',lambda:refused(driver.main,'FINAL_ORACLE_CODEC_PENDING_ROOT'))
 c.ORACLE_CODEC_STATE=saved_codec_state
 check('finalcodec_ready_source_only',lambda:yes(c.ORACLE_CODEC_STATE=='ROOT_FINAL_CODEC_INTEGRATED'))
 check('reject_unbound_codec_acceptance',lambda:refused(lambda:c.codec_acceptance(None),'CODEC_EXACT_ROOT_ACCEPTANCE'))
 driver_ast=ast.parse((B/'office_fixture_driver.py').read_text())
 forbidden={'storeAsURL','storeToURL','store','storeAs','createInstanceWithArguments','commitChanges','setPropertyValue'}
 check('driver_no_producer_store_config_call',lambda:yes(not {n.attr for n in ast.walk(driver_ast) if isinstance(n,ast.Attribute)}&forbidden))
 check('driver_exact_seven_order_profiles',lambda:yes(tuple(fmt for fmt,_,_ in driver.JOBS)==('docx','xlsx','pptx','odt','ods','odp','odt') and driver.PROFILES==c.PROFILES))
 # Exercise actual nested probe function with injected in-memory UNO boundary.
 probe_node=next(n for n in ast.walk(driver_ast) if isinstance(n,ast.FunctionDef) and n.name=='probe')
 mock_illegal=type('com.sun.star.lang.IllegalArgumentException',(Exception,),{})
 class Handler:
  def __init__(self):self.events=[]
 pw=lambda kind:dict(request_kind=kind,abort_selected=True,phase='select_after')
 ms=[pw('DocumentMSPasswordRequest')]
 odf=[pw('DocumentPasswordRequest'),dict(request_kind='ErrorCodeRequest2',payload_class='com.sun.star.task.ErrorCodeRequest2',is_error_code_request2=True,error_code=283,abort_selected=True,phase='select_after')]
 probe_module=compile(ast.fix_missing_locations(ast.Module(body=[probe_node],type_ignores=[])),'<actual_nested_probe>','exec')
 def probe_case(fmt,events,result=None,error=None,semantic=True):
  handler=Handler();closed=[]
  def load(path,supplied):
   handler.events.extend(copy.deepcopy(events))
   if error is not None:raise error
   return result
  env=dict(handler=handler,load=load,semantic=lambda *args:semantic,close=lambda obj:closed.append(obj),safe_type=driver.safe_type,observed_password_refusal_sequence=driver.observed_password_refusal_sequence,IllegalArgumentException=mock_illegal)
  exec(probe_module,env);answer=env['probe']('IN_MEMORY_PATH',fmt,None,False)
  yes((result is None or closed==[result]));return answer
 for fmt,events in [('docx',ms),('xlsx',ms),('pptx',ms),('odt',odf),('ods',odf),('odp',odf)]:
  check('typed_unopened_'+fmt,lambda fmt=fmt,events=events:yes(probe_case(fmt,events)['expected_password_refusal']))
 err=mock_illegal();err.ArgumentPosition=1
 check('typed_ooxml_exact_illegal_position1',lambda:yes(probe_case('docx',ms,error=err)['expected_password_refusal']))
 for pos in (0,2,True,'1',None):
  error=mock_illegal();error.ArgumentPosition=pos
  check('reject_illegal_position_'+str(pos),lambda error=error:yes(not probe_case('docx',ms,error=error)['expected_password_refusal']))
 check('reject_odf_illegal_even_typed_sequence',lambda:yes(not probe_case('odt',odf,error=err)['expected_password_refusal']))
 check('reject_untyped_None',lambda:yes(not probe_case('docx',[])['expected_password_refusal']))
 check('reject_untyped_qualified_illegal',lambda:yes(not probe_case('docx',[],error=err)['expected_password_refusal']))
 check('reject_unexpected_exception_after_sequence',lambda:yes(not probe_case('docx',ms,error=RuntimeError())['expected_password_refusal']))
 check('reject_callback_getRequest_fault',lambda:yes(not probe_case('docx',[dict(request_kind='DocumentMSPasswordRequest',abort_selected=False,phase='callback_exception_reraised',callback_error_phase='get_request_before',callback_error=dict(exception_class='builtins.SystemError'))])['expected_password_refusal']))
 bad=copy.deepcopy(odf);bad[1]['error_code']=282
 check('reject_wrong_secondary283_code',lambda:yes(not probe_case('odt',bad)['expected_password_refusal']))
 check('reject_reversed_secondary_order',lambda:yes(not probe_case('odt',list(reversed(odf)))['expected_password_refusal']))
 check('reject_opened_negative_despite_sequence',lambda:yes(not probe_case('docx',ms,result=object())['expected_password_refusal']))
 correct=probe_case('docx',[],result=object())
 check('correct_samebytes_semantics_noevents',lambda:yes(correct['opened'] and correct['semantic_match'] and not correct['interaction_events'] and not correct['expected_password_refusal']))
 correct_bad=probe_case('docx',[],result=object(),semantic=False)
 check('positive_bad_semantics_remains_fail',lambda:yes(correct_bad['opened'] and not correct_bad['semantic_match']))
 src=(B/'office_fixture_driver.py').read_text()
 for name,expected in [('request_args_compat_v2.py','f57c76e450b7aa024e7726b3fef7973e317120ab8eee317095f6b38d814ae779'),('callback_observer_v2.py','eb3765d73b7e64d970f2438e68728f24a65842e1d8be300016f99ac978065c5c')]:
  start=src.index('# BEGIN EXACT '+name+' SHA256 '+expected+'\n')+len('# BEGIN EXACT '+name+' SHA256 '+expected+'\n');end=src.index('\n# END EXACT '+name,start)
  check('verbatim_accepted_helper_'+name,lambda start=start,end=end,expected=expected:yes(hashlib.sha256(src[start:end].encode()).hexdigest()==expected))
 check('driver_readonly_macro_update_off',lambda:yes("prop('ReadOnly',True)" in src and "prop('MacroExecutionMode',0)" in src and "prop('UpdateDocMode',0)" in src))
 check('driver_original_fail_and_copy_provenance_explicit',lambda:yes("'original_g6_all_pass':False" in src and "'copy_is_original':False" in src and "'original_host_path':original['path']" in src and "'raw_original_namespace_path':original['raw_original_namespace_path']" in src))
 ins=(B/'inside_once.py').read_text();emb=(B/'embedded_entry.py').read_text();contract=(B/'f06_contract.py').read_text();uns=(B/'run_once.py').read_text();rs=(B/'root_frame.py').read_text()
 check('namespace_mount_guard_and_inputs_ro',lambda:yes("'--ro-bind',str(inputs),'/inputs'" in contract and "'MOUNT_READONLY'" in ins))
 check('empty_desktop_ownership_before_oracle',lambda:yes("'CONNECTED_ZERO_COMPONENTS_NO_DOCUMENT_OR_SECRET'" in ins and "save(attempt/'ORACLE-ENTERED.json'" in emb and "'--mode','verify-inputs'" in emb))
 check('copy_original_identity_and_aftercas',lambda:yes("'BEFORE_COPY_FULL_PIN'" in uns and "'ORIGINAL_AFTER_COPY_CAS'" in uns and "'STAGED_COPY_SHA_AND_DISTINCT_INODE'" in uns and 'original_host_pin=p,staged_host_pin=copypin' in uns))
 check('retained_original9_without_reexecution',lambda:yes(len(root.RETAINED_PREFLIGHT_FILES)==9 and "admission['assignment']==c.RETAINED_ASSIGNMENT" in rs and "admission['limits']==c.PREFLIGHT_LIMITS" in rs and "reuse['preflight_reexecuted'] is False" in rs))
 for name in ('verify-inputs.ADMISSION.TEMPLATE.json','SOURCE-DELTA-ACCEPTANCE.TEMPLATE.json','RETAINED-PREFLIGHT-ACCEPTANCE.TEMPLATE.json','RETAINED-INPUTS-ACCEPTANCE.TEMPLATE.json'):
  obj=json.loads((B/name).read_text());check('inert_'+name,lambda obj=obj:yes(obj['state'].startswith('UNBOUND_')))
 for name in [r['name'] for r in json.loads((B/'SOURCE-PINS.json').read_text())['files'] if r['name'].endswith('.py')]:
  check('compile_'+name,lambda name=name:compile((B/name).read_bytes(),str(B/name),'exec'))
 return dict(state='PURE_VERIFY_INPUTS_SOURCE_CONTROLS_PASS',count=len(rows),controls=rows,Office_starts=0,unit_starts=0,namespace_starts=0,credential_content_reads=0,ciphertext_content_reads=0,final_codec_review='ROOT_ACCEPTED_HELPERS_AND_REPRESENTATIVE_CONTRAST_FULL_FRAME_REVIEW_PENDING',runtime_or_application_PASS=False)
if __name__=='__main__':
 print(json.dumps(run(),indent=2))
