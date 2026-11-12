"""Exact Root source decision. No runtime authority or installation."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT206-ROOT-SOURCE-AFTER205-20261112')
R=Path('/home/jericho/jericho/Friday_rework')
os.umask(0o077)
def load(path):return json.loads(Path(path).read_bytes())
def ref(path):return dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
def verify(row):assert ref(row['path'])=={key:row[key] for key in ['path','sha256']}
def save(path,value):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as stream:
  json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
def main():
 assert ref(F/'RESULT.json')['sha256']=='d0a2dd3ff3d44187fb7c47f540a4152db431219feeeb51b88a7fa5a3f5379307'
 assert ref(F/'SOURCE-PINS.json')['sha256']=='c547cf3c65648a75f87693b23416a7fb2c287cdc8d6b3bb366bdca703e1253df'
 pins=load(F/'SOURCE-PINS.json')
 for path,digest in {**pins['source_refs'],**pins['historical_refs']}.items():assert ref(path)['sha256']==digest
 review=load(F/'review/final/RESULT.json')
 assert ref(F/'review/final/RESULT.json')['sha256']=='6593a166c2eb0390be9f4390911cc5956bd1f8b3c1faaba34a63ca85bf8c43b4'
 assert review['state']=='APPROVED_SOURCE_ONLY_UNBOUND' and review['approved'] and not review['blocking_findings']
 clarify=load(F/'review/ROOT-ANCHOR-SCOPE-CLARIFICATION.json')
 assert clarify['runtime_delta_required'] is False and clarify['additional_native_observability_API_required'] is False
 historical=load(F/'ACTUAL205-HISTORICAL-METADATA.json')
 for row in historical['references'].values():verify(row)
 for row in historical['stage_refs']:verify(row)
 verify(historical['intent'])
 actual=load(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')
 assert ref(B/'CORE205-ACTUAL-INSTALLED-CLOSED-20261112.json')['sha256']=='b26122f9b99ae6c906da802f34420c9d6205ca1319e9f74e5ffe46a246f2b910'
 assert actual['state']=='INSTALLED205_PROJECT491_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
 for row in actual['installed']['canonical4'].values():verify(row)
 predecessor=load(F/'ROOT-ACTUAL205-PREDECESSOR-TEMPLATE.json')
 predecessor.update(historical['references'],state='ROOT_RECONCILED_GENUINE_INSTALLED205_NOT_EXPECTATION',template_only_no_execution_grant=False)
 save(F/'ROOT-ACTUAL205-PREDECESSOR.json',predecessor)
 head=subprocess.check_output(['git','-C',str(R),'--no-optional-locks','rev-parse','HEAD'],text=True).strip()
 assert head=='8d392e47c27e9d09d97645e50d2690c087b5c7f3'
 accepted=load(F/'ROOT-206-SOURCE-ACCEPTANCE-TEMPLATE.json');accepted.pop('required_state_after_actual_Root_review')
 for row in [accepted['final_source_result']]+[x['evidence'] for x in accepted['four_gate_evidence']]+accepted['independent_review_evidence']+accepted['newapp_review_evidence']+list(accepted['source_pins'].values()):verify(row)
 accepted.update(accepted=True,all_four_current_source_gates_accepted=True,execution_grant=False,gate_retry_history_preserved=True,
  state='ROOT_ACCEPTED_EXACT206_SOURCE_OFFLINE_AND_RETAINED_RICH_REVIEW_NOT_RUNTIME',template_only_no_execution_grant=False,
  frame_source_manifest=ref(F/'SOURCE-PINS.json'),frame_review_evidence=[ref(F/'review/final/RESULT.json'),ref(F/'review/ROOT-ANCHOR-SCOPE-CLARIFICATION.json')],
  source_provenance=dict(mode='local-committed-main',commit=head),public_main_sha=None)
 save(F/'ROOT-206-SOURCE-ACCEPTANCE.json',accepted)
 decision=dict(schema='frw.root206.coherent-source-acceptance.v1',state='ACCEPTED_SOURCE_ONLY_NOT_RUNTIME_ADMISSION',at_moscow=datetime.datetime.now().astimezone().isoformat(),
  source_result=ref(F/'RESULT.json'),source_manifest=ref(F/'SOURCE-PINS.json'),source_acceptance=ref(F/'ROOT-206-SOURCE-ACCEPTANCE.json'),actual205_predecessor=ref(F/'ROOT-ACTUAL205-PREDECESSOR.json'),
  independent_review=ref(F/'review/final/RESULT.json'),actor_recovery_review=ref(F/'review/final/actor/RESULT.json'),scope_clarification=ref(F/'review/ROOT-ANCHOR-SCOPE-CLARIFICATION.json'),
  root_review='Exact genuineCP205/fullstage/chain199..205 and actual205 closure; rawGit493/private28/newpublic5 provenance;17CAS/11existingnative/493project/17891native/prefix205; heldslot/R2observer/explicitH recovery; bank before native+all3SQL and age beforeactor.',
  all_four_synthetic_source_gates_reused=True,new_gate_executions=0,runtime_grant=False,
  quiescence_scope='Fresh existing globalrunner/custody/gateway0/all3leases+alloriginSQL/spools/cooldown/locks with explicit ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED; no claim of observing every pending field or new native API.',
  retained='Standard3.2 not authenticatedMAC; modernODT unsupported in206; genuineprivacyWARN/ordinary/App/formal remain separate. OldFAIL/UNKNOWN/clocks unchanged; no powerlossatomicity.')
 save(B/'F06-COHERENT206-ROOT-SOURCE-ACCEPTANCE-20261112.json',decision)
 print(json.dumps(dict(state=decision['state'],source_acceptance=decision['source_acceptance'],predecessor=decision['actual205_predecessor'])))
if __name__=='__main__':main()
