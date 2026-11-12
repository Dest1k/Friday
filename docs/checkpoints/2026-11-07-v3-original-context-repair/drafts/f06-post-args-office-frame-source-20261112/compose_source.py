"""Finite source composition only. No admission, UNO, Office or input reads."""
import ast, datetime, difflib, hashlib, json, os
from pathlib import Path
os.umask(0o077)
B=Path(__file__).resolve().parent; C=B/'candidate';C.mkdir(mode=0o700)
T25=Path('/home/jericho/.cache/FRW-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112')
T27=Path('/home/jericho/.cache/FRW-SOL-V3-F06-OBSERVED-ERRORCODE-ARGS-COMPAT-CORE-20261112')
A=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
ASSIGN='ASTRA-NATIVE-F06-POST-ARGS-COMPAT-OFFICE-FRAME-SOURCE-20261112#1'
F25='dc7eaf4385616ec5d4a6bd6b13e97a5795e34ccfbdc254943a1621b694db14b1'
F27='305d16593f582bcce419f13efb9bd97c2524c2c4c893aaf4437bca5e0dbb3e28'
CLASS1='176f65237a6416f0950bd18a5f366a5e3cc1262842058f18e5b2cbc7b3614f9b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=True,indent=2)+'\n');p.chmod(0o600)
assert sha(T25/'SOURCE-FREEZE-FINAL.json')==F25
assert sha(T27/'SOURCE-FREEZE-FINAL.json')==F27
f25=json.loads((T25/'SOURCE-FREEZE-FINAL.json').read_bytes())
f27=json.loads((T27/'SOURCE-FREEZE-FINAL.json').read_bytes())
old={Path(r['path']).name:r for r in f25['files'] if Path(r['path']).parent==T25/'candidate'}
new={Path(r['path']).name:r for r in f27['files'] if Path(r['path']).parent==T27/'revision2/candidate'}
provenance=[]
for name,row in old.items():
 if not name.endswith('.py'):continue
 source=Path((new.get(name)or row)['path']);assert sha(source)==(new.get(name)or row)['sha256']
 assert sha(Path(row['path']))==row['sha256']
 (C/name).write_bytes(source.read_bytes());(C/name).chmod(0o600)
 provenance.append(dict(name=name,task25_origin=row,composition_origin=pin(source)))
assert len(provenance)==11
# The accepted five-library graph is carried byte-exact, including two changed libraries.
libs={n:new[n]['sha256']for n in sorted(new)}
p=C/'f06_contract.py';s=p.read_text()
s=s.replace("ASSIGNMENT='ASTRA-SOL-V3-F06-ONE-TEMPLATE-DIAGNOSTIC-FRAME-20261112#1'",'ASSIGNMENT='+repr(ASSIGN))
s=s.replace("TASK24_FREEZE_SHA='d68090a8d60879e948ffb2cf105f80f520ff1a1a07f30d29f988346bea671971'", "TASK24_FREEZE_SHA='d68090a8d60879e948ffb2cf105f80f520ff1a1a07f30d29f988346bea671971'\nTASK25_FREEZE_SHA="+repr(F25)+"\nTASK27_FREEZE_SHA="+repr(F27)+"\nPREVIOUS_CLASS1_SUMMARY_SHA="+repr(CLASS1)+"\nOPERATION_KEY='one-template-post-args-compat1'\nPOSTCHANGE_PURPOSE='ONE_MISSING_POST_ARGS_NORMAL_PAYLOAD_AND_READONLY_LOAD'\nLIBRARY_SHA256="+repr(libs))
s=s.replace("type(key)is str and re.fullmatch('one-template-diag-[a-z0-9]{1,24}',key)is not None", "type(key)is str and key==OPERATION_KEY")
s=s.replace("'friday.f06.one-template-diagnostic-source.v1'", "'friday.f06.one-template-post-args-compat-source.v1'")
s=s.replace("and obj.get('state')=='SOURCE_ONLY_DORMANT','SOURCE_SCHEMA'", "and obj.get('state')=='SOURCE_ONLY_DORMANT' and obj.get('assignment')==ASSIGNMENT and obj.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA,'SOURCE_SCHEMA'")
s=s.replace("need({p.name for p in B.glob('*.py')}", "need({row['name']:row['sha256'] for row in rows if row.get('name') in LIBRARY_SHA256}==LIBRARY_SHA256,'EXACT_TASK27_LIBRARY_PAIR_AND_CARRIES')\n need({p.name for p in B.glob('*.py')}")
s=s.replace("row['bytes']<=1000000", "row['bytes']==4624")
s=s.replace("review.get('state')=='ROOT_ACCEPTED_ONE_TEMPLATE_DIAGNOSTIC_SOURCE'", "review.get('state')=='ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE'")
s=s.replace("and review.get('findings_remaining')==[],'ROOT_SOURCE_REVIEW'", "and review.get('task25_sourcefreeze_sha256')==TASK25_FREEZE_SHA and review.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA and review.get('previous_class1_summary_sha256')==PREVIOUS_CLASS1_SUMMARY_SHA and review.get('postchange_purpose')==POSTCHANGE_PURPOSE and review.get('findings_remaining')==[],'ROOT_SOURCE_REVIEW'")
s=s.replace("authority.get('state')=='ROOT_GRANTED_ONE_MISSING_CONVERSION_OBSERVATION'", "authority.get('state')=='ROOT_GRANTED_ONE_POST_ARGS_COMPAT_QUALIFICATION' and authority.get('assignment')==ASSIGNMENT and authority.get('task27_sourcefreeze_sha256')==TASK27_FREEZE_SHA and authority.get('previous_class1_summary_sha256')==PREVIOUS_CLASS1_SUMMARY_SHA and authority.get('postchange_purpose')==POSTCHANGE_PURPOSE")
s=s.replace("authority.get('original18_replayed')is False", "authority.get('original18_replayed')is False and authority.get('previous_class1_replayed')is False and authority.get('actual_normal_payload_type_before')=='UNKNOWN'")
p.write_text(s)
# Only entry/Root proof namespaces change; runtime ownership/budgets/custody stay exact.
for name in ('root_entry.py','root_frame.py'):
 p=C/name;s=p.read_text().replace('friday.f06.one-template-root-bindings.v1','friday.f06.one-template-post-args-root-bindings.v1').replace('friday.f06.one-template-admission.v1','friday.f06.one-template-post-args-admission.v1').replace('friday.f06.one-template-diagnostic-source.v1','friday.f06.one-template-post-args-compat-source.v1').replace('ROOT_FRESH_ONE_TEMPLATE_KERNEL_CUSTODY','ROOT_FRESH_POST_ARGS_COMPAT_ONE_TEMPLATE_KERNEL_CUSTODY')
 p.write_text(s)
# Unbound templates are shapes, never observations/grants.
binding=json.loads((T25/'candidate/ROOT-BINDINGS.TEMPLATE.json').read_bytes());binding.update(schema='friday.f06.one-template-post-args-root-bindings.v1',assignment=ASSIGN)
save(C/'ROOT-BINDINGS.TEMPLATE.json',binding)
proof=json.loads((T25/'candidate/ROOT-PROOFS.TEMPLATE.json').read_bytes());proof['schema']='post-args.inert.Root-proof-shapes.v1'
proof['source_review'].update(required_state='ROOT_ACCEPTED_POST_ARGS_COMPAT_ONE_TEMPLATE_SOURCE',task25_sourcefreeze_sha256=F25,task27_sourcefreeze_sha256=F27,previous_class1_summary_sha256=CLASS1,postchange_purpose='ONE_MISSING_POST_ARGS_NORMAL_PAYLOAD_AND_READONLY_LOAD')
proof['runtime_authority'].update(required_state='ROOT_GRANTED_ONE_POST_ARGS_COMPAT_QUALIFICATION',assignment=ASSIGN,task27_sourcefreeze_sha256=F27,previous_class1_summary_sha256=CLASS1,postchange_purpose='ONE_MISSING_POST_ARGS_NORMAL_PAYLOAD_AND_READONLY_LOAD',previous_class1_replayed=False,actual_normal_payload_type_before='UNKNOWN')
proof['fresh_boundary']['required_state']='ROOT_FRESH_POST_ARGS_COMPAT_ONE_TEMPLATE_KERNEL_CUSTODY'
proof['selected_manifest']['assignment']=ASSIGN
save(C/'ROOT-PROOFS.TEMPLATE.json',proof)
refs=[T25/'SOURCE-FREEZE-FINAL.json',T27/'SOURCE-FREEZE-FINAL.json',T27/'RESULT.json',A/'SOL-TASK25-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json',A/'SOL-TASK27-FINAL-ROOT-SOURCE-ACCEPTANCE-20261112.json',A/'F06-ONE-TEMPLATE-MISSING-CLASS-OBSERVED-PARTIAL-CLOSED-20261112.json']
assert sha(refs[-1])==CLASS1
D=B/'reference-metadata';D.mkdir(mode=0o700)
metadata_copy=D/refs[-1].name;metadata_copy.write_bytes(refs[-1].read_bytes());metadata_copy.chmod(0o600);refs[-1]=metadata_copy
save(C/'REFERENCES.json',dict(schema='post-args.exact.nonsecret.readonly.references.v1',files=[pin(p)for p in refs],runtime_authority=False))
rows=[]
for p in sorted(C.iterdir()):rows.append(dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)))
save(C/'SOURCE-PINS.json',dict(schema='friday.f06.one-template-post-args-compat-source.v1',state='SOURCE_ONLY_DORMANT',assignment=ASSIGN,task27_sourcefreeze_sha256=F27,source_set=[r['name']for r in rows],files=rows,execution_authority=False))
for row in provenance:
 p=C/row['name'];row['after']=pin(p);row['changed_from_task25']=sha(p)!=row['task25_origin']['sha256'];row['exact_task27_library']=row['name']in libs and sha(p)==libs[row['name']]
 ast.parse(p.read_text(),filename=str(p),feature_version=(3,12))
save(B/'COMPOSITION-MAP.json',dict(schema='post-args.source-composition.v1',state='SOURCE_ONLY_NO_RUNTIME_AUTHORITY',assignment=ASSIGN,files=provenance,exact_task27_libraries=libs,source_py_count=len(provenance),changed_from_task25=sum(r['changed_from_task25']for r in provenance),separate_operation='one-template-post-args-compat1',all_grants_bindings_clock_currentproof='UNBOUND'))
patch=[]
for row in provenance:
 if row['changed_from_task25']:
  patch.extend(difflib.unified_diff(Path(row['task25_origin']['path']).read_text().splitlines(True),(C/row['name']).read_text().splitlines(True),fromfile='a/'+row['name'],tofile='b/'+row['name']))
(B/'POST-ARGS-COMPOSITION.patch').write_text(''.join(patch))
save(B/'START.json',dict(started_moscow='2026-11-12T07:28:23+03:00',composed_at_moscow=datetime.datetime.now().astimezone().isoformat(),assignment=ASSIGN,state='SOURCE_ONLY_COMPOSED_UNBOUND',no_actual_inputs_read=True,no_live_effects=True))
print(json.dumps(dict(candidate=str(C),source_pin=pin(C/'SOURCE-PINS.json'),changed_from_T25=sum(r['changed_from_task25']for r in provenance),exact_T27_libraries=len(libs))))
