import json,os
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent
T25=Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112')
T27=Path('/home/jericho/.cache/FRW-SOL-V3-F06-OBSERVED-ERRORCODE-ARGS-COMPAT-CORE-20261112')
s=(T25/'pure_controls.py').read_text()
s=s.replace("source=pin('/synthetic/retained-source.ott',c.SELECTED_SHA)","source=pin('/synthetic/retained-source.ott',c.SELECTED_SHA,size=4624)")
s=s.replace('one-template-diag-synthetic','one-template-post-args-compat1')
s=s.replace('ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE','ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE')
s=s.replace('task24_freeze_sha256=c.TASK24_FREEZE_SHA,findings_remaining=[]',"task24_freeze_sha256=c.TASK24_FREEZE_SHA,task25_sourcefreeze_sha256=c.TASK25_FREEZE_SHA,task27_sourcefreeze_sha256=c.TASK27_FREEZE_SHA,previous_class1_summary_sha256=c.PREVIOUS_CLASS1_SUMMARY_SHA,postchange_purpose=c.POSTCHANGE_PURPOSE,findings_remaining=[]")
s=s.replace("authority=dict(state='ROOT_GRANTED_ONE_MISSING_CONVERSION_OBSERVATION',", "authority=dict(state='ROOT_GRANTED_ONE_POST_ARGS_COMPAT_QUALIFICATION',assignment=c.ASSIGNMENT,task27_sourcefreeze_sha256=c.TASK27_FREEZE_SHA,previous_class1_summary_sha256=c.PREVIOUS_CLASS1_SUMMARY_SHA,postchange_purpose=c.POSTCHANGE_PURPOSE,previous_class1_replayed=False,actual_normal_payload_type_before='UNKNOWN',")
marker="print(json.dumps({'schema':'task25.pure-controls.v1'"
extra='''
# Changed admission/source-pair namespaces: actual source consumer is called, no main.
check('new_operation_key_accepted',lambda:c.operation(c.OPERATION_KEY,c.MODE))
for oldkey in ('one-template-diag-class1','one-template-diag-synthetic','one-template-post-args-compat2'):
 check('old_or_renamed_operation_refused_'+oldkey,lambda oldkey=oldkey:refused(lambda:c.operation(oldkey,c.MODE)))
check('new_recipe_exact_current_sources',lambda:c.recipe_check())
def recipe_variant(mut):
 g=c.recipe_check.__globals__;original=g['private'];pins=json.loads((C/'SOURCE-PINS.json').read_bytes());mut(pins)
 def read(path,root):
  raw,pin=original(path,root)
  return (json.dumps(pins).encode(),pin) if pathlib.Path(path).name=='SOURCE-PINS.json' else (raw,pin)
 g['private']=read
 try:refused(c.recipe_check)
 finally:g['private']=original
for name,mut in (
 ('old_Task25_source_schema',lambda x:x.update(schema='friday.f06.one-template-diagnostic-source.v1')),
 ('old_Task25_assignment',lambda x:x.update(assignment='ASTRA-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112#1')),
 ('wrong_Task27_freeze',lambda x:x.update(task27_sourcefreeze_sha256='0'*64)),
 ('old_Task25_helper_pair',lambda x:next(r for r in x['files']if r['name']=='request_args_compat_v2.py').update(sha256='f57c76e450b7aa024e7726b3fef7973e317120ab8eee317095f6b38d814ae779')),
 ('old_Task25_probe_pair',lambda x:next(r for r in x['files']if r['name']=='conversion_probe.py').update(sha256='8a29758ea6dece9198d8a417619d2bad21c2dba44bd047d79c36d408e96f1a56')),
):check(name,lambda mut=mut:recipe_variant(mut))
for name,mut in (
 ('old_source_review_state',lambda a,r,u:r.update(state='ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE')),
 ('old_runtime_grant_state',lambda a,r,u:u.update(state='ROOT_GRANTED_ONE_MISSING_CONVERSION_OBSERVATION')),
 ('wrong_T27_review_freeze',lambda a,r,u:r.update(task27_sourcefreeze_sha256='0'*64)),
 ('wrong_T27_authority_freeze',lambda a,r,u:u.update(task27_sourcefreeze_sha256='0'*64)),
 ('wrong_T25_review_freeze',lambda a,r,u:r.update(task25_sourcefreeze_sha256='0'*64)),
 ('wrong_class1_summary_review',lambda a,r,u:r.update(previous_class1_summary_sha256='0'*64)),
 ('wrong_class1_summary_authority',lambda a,r,u:u.update(previous_class1_summary_sha256='0'*64)),
 ('old_assignment_authority',lambda a,r,u:u.update(assignment='OLD_TASK25')),
 ('wrong_postchange_purpose',lambda a,r,u:u.update(postchange_purpose='OLD_CLASS1_RETRY')),
 ('class1_replay_forbidden',lambda a,r,u:u.update(previous_class1_replayed=True)),
 ('normal_payload_not_invented',lambda a,r,u:u.update(actual_normal_payload_type_before='ErrorCodeRequest')),
):check(name,lambda mut=mut:refused(lambda:proof_case(mut)))
check('exact_selected_size_refused',lambda:refused(lambda:c.manifest_contract({**manifest,'fixtures':[{**row,'bytes':4623}]})))
check('wrong_owner_custody_refused',lambda:refused(lambda:c.full_pin_shape({**source,'identity':[1,2,stat.S_IFREG|0o600,os.getuid()+1,os.getgid(),1,4624,3,4]})))
check('hardlink_custody_refused',lambda:refused(lambda:c.full_pin_shape({**source,'identity':[1,2,stat.S_IFREG|0o600,os.getuid(),os.getgid(),2,4624,3,4]})))
check('world_readable_custody_refused',lambda:refused(lambda:c.full_pin_shape({**source,'identity':[1,2,stat.S_IFREG|0o644,os.getuid(),os.getgid(),1,4624,3,4]})))
'''
s=s.replace(marker,extra+marker.replace('task25.pure-controls.v1','post-args.parent-source-controls.v1'))
(B/'parent_controls.py').write_text(s)
s=(T25/'inside-child/pure_controls.py').read_text().replace('ROOT = Path(__file__).parent','ROOT = Path(__file__).parent / \'candidate\'').replace("error_code_request_type=CLASSES[compat.REQUEST_NAMES[-1]]","error_code_request_type=CLASSES[compat.REQUEST_NAMES[4]]")
s=s.replace('test_exact_task24_four_untouched','test_exact_task27_five_reviewed_libraries')
s=s.replace("'8a29758ea6dece9198d8a417619d2bad21c2dba44bd047d79c36d408e96f1a56'","'bb556abab6aecde55d61e8f7372fdba980303daabeaae322b40f7e152d3ab1f5'").replace("'f57c76e450b7aa024e7726b3fef7973e317120ab8eee317095f6b38d814ae779'","'23a2d996d7ee940b4a8a07140867e8e50e57b24859b18884872781ac40e1fc18'")
s=s.replace("'request_args_compat_v2.py': '23a2d996d7ee940b4a8a07140867e8e50e57b24859b18884872781ac40e1fc18'}", "'request_args_compat_v2.py': '23a2d996d7ee940b4a8a07140867e8e50e57b24859b18884872781ac40e1fc18', 'diagnostic_client.py':'5c8de29ece89b5f57435f3a40746223dea49c5582be50c9f3fcf8b376d218a9d'}")
s=s.replace("ASSIGNMENT='ASTRA-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112#1'", "ASSIGNMENT='ASTRA-NATIVE-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112#1'")
s=s.replace("dict(bytes=42, sha256=client.SELECTED_SHA)","dict(bytes=4624, sha256=client.SELECTED_SHA)")
s=s.replace("bytes=42, sha256=client.SELECTED_SHA", "bytes=4624, sha256=client.SELECTED_SHA").replace("1, 42, 3, 4", "1, 4624, 3, 4")
s=s.replace("own-source.ott', bytes=42,","own-source.ott', bytes=4624,")
(B/'inside_controls.py').write_text(s)
s=(T27/'final_protocol_controls.py').read_text().replace("R=B/'revision2/candidate'", "R=B/'candidate'").replace("(B/'baseline/uno.py')", "(__import__('pathlib').Path('/home/jericho/.cache/FRW-SOL-V3-F06-OBSERVED-ERRORCODE-ARGS-COMPAT-CORE-20261112/baseline/uno.py'))")
(B/'protocol_controls.py').write_text(s)
print('prepared parent/inside/protocol source controls')
