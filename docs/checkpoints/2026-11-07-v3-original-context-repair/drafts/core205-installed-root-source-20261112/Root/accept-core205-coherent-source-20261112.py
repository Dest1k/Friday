"""Root source decision only; no runtime authority or installation."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-CORE205-COHERENT-ROOT-SOURCE-AFTER204-20261112')
R=Path('/home/jericho/jericho/Friday_rework')
os.umask(0o077)
def load(p):return json.loads(Path(p).read_bytes())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def save(p,v):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w')as o:json.dump(v,o,indent=2,sort_keys=True);o.write('\n');o.flush();os.fsync(o.fileno())
def main():
 assert ref(F/'RESULT.json')['sha256']=='c43bc2a69f03874390852707735c932e0619dbe068b9f3f1c16d6ccc5cfbe99c'
 assert ref(F/'SOURCE-PINS.json')['sha256']=='8f6640b11f850ff7ed1ef30a23d09fc40496dca6f40ef5604882fc8e597b4a38'
 p=load(F/'SOURCE-PINS.json')
 for path,digest in {**p['source_refs'],**p['historical_refs']}.items():assert ref(path)['sha256']==digest
 review=load(F/'review/final/RESULT.json')
 assert review['state']=='APPROVE_SOURCE_ONLY_UNBOUND'
 assert ref(F/'review/final/RESULT.json')['sha256']=='72c6b0592ab70feee0d666b17019dd4e127fd89ac4e89366b877e7049fb8d02a'
 assert (F/'core205-first-actual-root.py').read_bytes()==(F/'review/final/core205-first-actual-root.proposed.py').read_bytes()
 retained=load(F/'REUSED-205-FINAL-SOURCE-EVIDENCE.json')
 for r in [retained['final_source_result'],retained['independent_review'],retained['root_acceptance']]+[x['evidence']for x in retained['four_gate_evidence']]:assert ref(r['path'])==r
 join=load(F/'PROFILE-SOURCE-JOIN.json')
 for r in join['evidence']:assert ref(r['path'])==r
 assert join['changed_definitions']==['_publish']and join['new_Office_effects']==0
 hist=load(F/'ACTUAL204-HISTORICAL-METADATA.json')
 for r in hist['references'].values():assert ref(r['path'])==r
 prev=load(F/'ROOT-ACTUAL204-PREDECESSOR-TEMPLATE.json')
 prev.update(hist['references'],state='ROOT_RECONCILED_GENUINE_INSTALLED204_NOT_EXPECTATION',template_only_no_execution_grant=False)
 save(F/'ROOT-ACTUAL204-PREDECESSOR.json',prev)
 head=subprocess.check_output(['git','-C',str(R),'--no-optional-locks','rev-parse','HEAD'],text=True).strip()
 assert head=='b86eb1693cdb51f9d3a1a8bd0f7b6f8f06b497cb'
 a=load(F/'ROOT-205-SOURCE-ACCEPTANCE-TEMPLATE.json');a.pop('required_state_after_actual_Root_review')
 a.update(accepted=True,all_four_current_source_gates_accepted=True,execution_grant=False,
   state='ROOT_ACCEPTED_EXACT205_SOURCE_OFFLINE_AND_RETAINED_RICH_REVIEW_NOT_RUNTIME',template_only_no_execution_grant=False,
   gate_retry_history_preserved=True,source_provenance=dict(mode='local-committed-main',commit=head),public_main_sha=None,
   frame_source_manifest=ref(F/'SOURCE-PINS.json'),frame_review_evidence=[ref(F/'review/final/RESULT.json'),ref(F/'FRESHNESS-DELTA-CHECK.json')],
   independent_review_evidence=[retained['independent_review']],newapp_review_evidence=[ref(F/'PROFILE-SOURCE-JOIN.json')])
 save(F/'ROOT-205-SOURCE-ACCEPTANCE.json',a)
 decision=dict(schema='frw.root205.coherent-source-acceptance.v1',state='ACCEPTED_SOURCE_ONLY_NOT_RUNTIME_ADMISSION',
   at_moscow=datetime.datetime.now().astimezone().isoformat(),source_result=ref(F/'RESULT.json'),manifest=ref(F/'SOURCE-PINS.json'),
   source_acceptance=ref(F/'ROOT-205-SOURCE-ACCEPTANCE.json'),actual204_predecessor=ref(F/'ROOT-ACTUAL204-PREDECESSOR.json'),
   independent_review=ref(F/'review/final/RESULT.json'),reviewer_delta_checked_by_other_participant=ref(F/'FRESHNESS-DELTA-CHECK.json'),
   root_delta_review='Final bytes equal reviewed proposal. Bank/resources precede native+SQL refresh; age guard repeats after binding immediately before actor.',
   unchanged_four_synthetic_gates_reused=True,new_gates=0,runtime_grant=False,old_effects_clocks_preserved=True,
   limits=['Actual205 not installed; fresh Root service/global anchor and finite authority required.',
           'App template PARTIAL/6 callback faults remain unchanged; no Office/model/send/replay credit.',
           'Journaled rollback does not prove power-loss atomicity.'])
 save(B/'CORE205-COHERENT-SOURCE-ROOT-ACCEPTANCE-20261112.json',decision)
 print(json.dumps(dict(state=decision['state'],source_acceptance=decision['source_acceptance'],predecessor=decision['actual204_predecessor'])))
if __name__=='__main__':main()
