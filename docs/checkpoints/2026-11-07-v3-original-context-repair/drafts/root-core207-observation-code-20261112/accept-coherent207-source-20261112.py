"""Root source-only decision for exact207. No authority, admission or execution."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-COHERENT207-ROOT-SOURCE-AFTER206-20261112')
R=Path('/home/jericho/jericho/Friday_rework')
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def verify(row):assert ref(row['path'])=={k:row[k] for k in ('path','sha256')}
def save(p,v):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
 assert ref(F/'RESULT.json')['sha256']=='c952e6d76dfef2febe03f8e6b302e39a6804ece23fe50646004bfb7fdf20caea'
 assert ref(F/'SOURCE-PINS.json')['sha256']=='cdc06817972650d8a35778960b8ad28553b5600999a4ef078637499968e6bdb4'
 assert ref(F/'review/final/RESULT.json')['sha256']=='85505ff23660b6286e34768603bc91fa6bde38e8eb385e627b51471f4df52147'
 review=load(F/'review/final/RESULT.json')
 assert review['approved'] and review['state']=='APPROVED_SOURCE_ONLY_UNBOUND' and not review['blocking_findings']
 pins=load(F/'SOURCE-PINS.json')
 for path,digest in {**pins['source_refs'],**pins['historical_refs']}.items():assert ref(path)['sha256']==digest
 pred=load(F/'ROOT-ACTUAL206-PREDECESSOR-TEMPLATE.json')
 for name in ('request','committed','complete_closure','root_journal','root_return'):verify(pred[name])
 actual=load(pred['complete_closure']['path'])
 assert actual['state']=='INSTALLED206_PROJECT493_NATIVE17891_SERVICES_HEALTHY_OPERATION_CLOSED'
 assert actual['actors_and_boundary_closed'] and actual['publisher_client_code']==actual['fresh_DEFAULT_code']==0
 for row in actual['installed']['canonical4'].values():verify(row)
 assert not (Path(pred['request']['path']).parent/'rolled-back.json').exists()
 pred.update(state='ROOT_RECONCILED_GENUINE_INSTALLED206_NOT_EXPECTATION',template_only_no_execution_grant=False)
 save(F/'ROOT-ACTUAL206-PREDECESSOR.json',pred)
 head=subprocess.check_output(['git','-C',str(R),'--no-optional-locks','rev-parse','HEAD'],text=True).strip()
 assert head=='fddb0abc70ea9d1caed3dbd5186a0a0b52166e46'
 accepted=load(F/'ROOT-207-SOURCE-ACCEPTANCE-TEMPLATE.json')
 for row in [accepted['final_source_result']]+[x['evidence'] for x in accepted['four_gate_evidence']]+accepted['independent_review_evidence']+accepted['newapp_review_evidence']+list(accepted['source_pins'].values()):verify(row)
 assert load(accepted['modern_final_execution_review']['path'])['state']=='ACCEPTED_EXACT_SOURCE_AND_FOUR_ACTUAL_SYNTHETIC_SOURCE_GATES'
 accepted.pop('required_state_after_actual_Root_review')
 accepted.update(state='ROOT_ACCEPTED_EXACT207_SOURCE_OFFLINE_AND_RETAINED_RICH_REVIEW_NOT_RUNTIME',accepted=True,
  all_four_current_source_gates_accepted=True,execution_grant=False,gate_retry_history_preserved=True,
  template_only_no_execution_grant=False,frame_source_manifest=ref(F/'SOURCE-PINS.json'),
  frame_review_evidence=[ref(F/'review/final/RESULT.json')],source_provenance=dict(mode='local-committed-main',commit=head),public_main_sha=None,
  known_limits='Exactmodernsource/fouractualsyntheticgates b72/c73 and coherent207frame855 accepted. Current206 remainsinstalled; freshRootanchor/authority/once andactual207executionnotcreated. Modern7originalFAIL/editnone/templatePARTIAL/class1TERMINALSTOP/oldUNKNOWNunchanged. No powerlossatomicity.')
 save(F/'ROOT-207-SOURCE-ACCEPTANCE.json',accepted)
 result=dict(schema='frw.root207.coherent-source-acceptance.v1',state='ACCEPTED_SOURCE_ONLY_NOT_RUNTIME_ADMISSION',
  at_moscow=datetime.datetime.now().astimezone().isoformat(),source_result=ref(F/'RESULT.json'),source_manifest=ref(F/'SOURCE-PINS.json'),
  source_acceptance=ref(F/'ROOT-207-SOURCE-ACCEPTANCE.json'),actual206_predecessor=ref(F/'ROOT-ACTUAL206-PREDECESSOR.json'),
  independent_review=ref(F/'review/final/RESULT.json'),all_four_actual_synthetic_source_gates_accepted=True,new_gate_executions=0,
  runtime_grant=False,root_review='GenuineCP206/fullstage/198+199..206chain,495rawGit/public5/private28,7CAS/1existingnative/17890untouched; heldslot/R2observer/strictownedclosure andsaved-service-onlyrecovery; bankbeforenative/all3SQL andfinalageguard. Source86+independent23,2251pinsverified.',
  quiescence_scope='Globalnative/custody/gateway0 +all3SQLleases/all-origin/spools/cooldown/locks, explicit ALL_PROFILE_IN_MEMORY_PENDING_QUEUES_APPROVALS_NOT_EXPOSED, no invented API or everyqueue claim.',
  retained='ODTonly Argon2id19/GCM85+12 source scope; Standard3.2notMAC/AgileHMACstrict. App/ordinary/semantic/formal separate. Oldconsumed effects/clocks unchanged; rollbacknotpowerlossatomicity.')
 save(B/'F06-COHERENT207-ROOT-SOURCE-ACCEPTANCE-20261112.json',result)
 print(json.dumps(dict(state=result['state'],source_acceptance=result['source_acceptance'],predecessor=result['actual206_predecessor'])))
if __name__=='__main__':main()
