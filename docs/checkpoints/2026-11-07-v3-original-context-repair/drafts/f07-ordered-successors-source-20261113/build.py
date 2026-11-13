"""Own source-only successor delta; no product imports or effects."""
import ast, datetime as dt, difflib, hashlib, json, os
from pathlib import Path
os.umask(0o077)
D=Path(__file__).parent
B=Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F07-HISTORY-CALLER-COMPAT-DELTA-20261113')
def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def ref(p):
 r=p.read_bytes();return dict(path=str(p),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def replace(s,old,new):
 assert s.count(old)==1,old[:100];return s.replace(old,new)
sources={p.name:p.read_text() for p in (B/'source').glob('*.py')}
s=sources['f07_phase_prepare.py']
s=replace(s,'import json\n','import json\nimport math\n')
s=replace(s,"and run.get('capture_window_complete') is True,'F07_ACTUAL_COMPLETE_CAPTURE_REQUIRED')", "and run.get('capture_window_complete') is True\n+         and type(run.get('sent_at')) in (int,float) and math.isfinite(run['sent_at'])\n+         and type(run.get('capture_until')) in (int,float) and math.isfinite(run['capture_until'])\n+         and run['capture_until']==run['sent_at']+180,'F07_ACTUAL_COMPLETE_CAPTURE_REQUIRED')".replace('\n+','\n'))
old='''    replacement=('    ' * 3 + "return (30 if run.get('id') == "+repr(run_id)
        +" and run.get('scenario_sha256') == "+repr(phase['scenario_sha256'])
        +" and 'continuation_reference' not in run else REPLY_ACK_RESERVE)\\n")'''
new='''    # This method is consumed by the ordinary whole-prefix predecessor custody
    # BEFORE the later current209 hook. Bind only this current/immediate pair.
    bindings={run_id:phase['scenario_sha256']}
    if ordinal>1:
        bindings[pred['run_id']]=pred['scenario_sha256']
    replacement=("            return (30 if "+repr(bindings)+".get(run.get('id')) == run.get('scenario_sha256')"
        +" and run.get('id') in "+repr(bindings)+" and 'continuation_reference' not in run else REPLY_ACK_RESERVE)\\n")'''
s=replace(s,old,new)
s=replace(s,'ACK30 is bound at the existing send_ack_budget method for this exact run and\n    scenario only; historical and unrelated ordinary runs retain their original10.',
 'ACK30 is bound at the earliest existing send_ack_budget method for this exact\n    current and genuine immediate-predecessor pair. Older/unrelated runs keep10.')
sources['f07_phase_prepare.py']=s
s=sources['root_caller.py'].replace('original first-phase eligibility determination.','original ordered-successor eligibility determination.')
s += '''

def select_ordered_successor(prep, saved, *, ordinal, scenario_raw):
    """Pure exact original array selection, successor-only; creates no grant."""
    need(type(ordinal) is int and 2<=ordinal<=4,'F07_EXPLICIT_SUCCESSOR_ORDINAL_REQUIRED')
    phases=saved.get('result',{}).get('phases') if type(saved) is dict else None
    need(type(phases) is list and len(phases)==4,'F07_ORIGINAL_FOUR_PHASE_ARRAY_REQUIRED')
    for index,phase in enumerate(phases,1):
        need(type(phase) is dict and phase.get('ordinal')==index
             and phase==prep.phase_preparation(index,phase['scenario']['steps'][0]['input']),
             'F07_EXACT_ORDERED_SAVED_PHASE_REQUIRED')
    phase=phases[ordinal-1];previous=phases[ordinal-2]
    need(type(scenario_raw) is bytes and scenario_raw==prep.encoded(phase['scenario']),
         'F07_EXACT_SELECTED_SUCCESSOR_SCENARIO_REQUIRED')
    return phase,previous


def accepted_successor_predecessor(checker, *, phase, previous_phase, original_phases, run_id, authority, bundle):
    """Root-only SAVED actual bridge, never accepts a caller-shaped future PASS.

    It reuses saved effect/observed/assessment and reconstructs the existing
    reviewed ABI. Historical proofs are not refreshed or used as current grants.
    The genuine ordinary prefix independently checks the immediate custody chain.
    """
    prep=checker.module(checker.PREP)
    selected,previous=select_ordered_successor(prep,dict(result=dict(phases=original_phases)),
        ordinal=phase.get('ordinal'),scenario_raw=prep.encoded(phase.get('scenario')))
    need(selected==phase and previous==previous_phase,'F07_ORIGINAL_SUCCESSOR_ARRAY_BINDING_REQUIRED')
    fields={'canonical_run','review','effect_and_consumer','proof','assessment'}
    need(type(bundle) is dict and set(bundle)==fields
         and all(checker.reference_shape(bundle[k]) for k in fields),'F07_ACTUAL_PREDECESSOR_BUNDLE_REQUIRED')
    descriptor=checker.doc(bundle['effect_and_consumer']);proof=checker.doc(bundle['proof'])
    effect=descriptor.get('effect');assessment=checker.doc(bundle['assessment']);review=checker.doc(bundle['review'])
    need(type(effect) is dict and descriptor.get('proof')==bundle['proof']
         and proof.get('schema')=='frw.Root.F07.current209-preintent.v1' and proof.get('operator')=='Root'
         and proof.get('status')=='ROOT_BOUND' and proof.get('effect')==effect
         and proof.get('whole_effect_sha256')==checker.digest(checker.encoded(effect))
         and type(proof.get('observed')) is dict and effect.get('phase')==previous_phase
         and previous_phase.get('ordinal')==phase.get('ordinal',0)-1,
         'F07_EXACT_SAVED_PREDECESSOR_EFFECT_REQUIRED')
    need(review.get('schema')=='frw.Root.F07.semantic-custody-review.v1'
         and assessment.get('evidence',{}).get('canonical_run')==bundle['canonical_run']
         and review.get('actual_postcondition_assessment')==bundle['assessment'],
         'F07_EXACT_SAVED_PREDECESSOR_ASSESSMENT_REQUIRED')
    expected=actual_predecessor_review(checker,effect=effect,observed=proof['observed'],
        assessment=assessment,assessment_ref=bundle['assessment'])
    need(review==expected and checker.read_reference(bundle['review'])==checker.encoded(expected),
         'F07_SAVED_ACTUAL_PREDECESSOR_REVIEW_CHANGED')
    raw=checker.read_reference(bundle['canonical_run']);run=checker.parse(raw)
    need(run.get('scenario')==previous_phase['scenario'] and run.get('id')==effect.get('run_id')
         and bundle['canonical_run']['path']==str(checker.STATE/'runs'/(run['id']+'.json')),
         'F07_CANONICAL_IMMEDIATE_PREDECESSOR_REQUIRED')
    binding=immediate_predecessor_binding(checker,canonical_run_ref=bundle['canonical_run'],review_ref=bundle['review'])
    need(authority.get('ordered_predecessors')=={run_id:binding},'F07_EXACT_AUTHORITY_ACTUAL_PREDECESSOR_JOIN_REQUIRED')
    if phase['ordinal']==2:
        need(bundle['canonical_run']==ORIGINAL_PHASE1_CANONICAL
             and bundle['review']==ORIGINAL_PHASE1_REVIEW,'F07_SAME_STARTED_ORIGINAL_SEQUENCE_ANCHOR_REQUIRED')
    else:
        # Previous accepted operation must itself have admitted the preceding
        # original phase. Its already-accepted effect is retained, not reissued.
        old_authority=checker.doc(effect['authority'])
        pred=old_authority.get('ordered_predecessors',{}).get(effect['run_id'],{})
        need(old_authority.get('f07_original_case')==dict(case_id='F-07',case_index=168,
                 phase=previous_phase['phase'],ordinal=previous_phase['ordinal'],
                 controlled_fault_sequence_not_replay=True,prospective_fixture_not_original=True)
             and pred.get('scenario_sha256')==prep.phase_preparation(phase['ordinal']-2,
                 checker.doc(dict(path=str(checker.STATE/'runs'/(pred.get('run_id','')+'.json')),
                     bytes=1,sha256='0'*64))['scenario']['steps'][0]['input'])['scenario_sha256'],
             'F07_PREVIOUS_ACTUAL_ORDERED_SEQUENCE_REQUIRED')
    return previous_phase
'''
# The earlier accepted effect already has exact prior scenario binding: compare
# original named scenario, without reading an older row or inventing a size pin.
s=replace(s,"and pred.get('scenario_sha256')==prep.phase_preparation(phase['ordinal']-2,\n                 checker.doc(dict(path=str(checker.STATE/'runs'/(pred.get('run_id','')+'.json')),\n                     bytes=1,sha256='0'*64))['scenario']['steps'][0]['input'])['scenario_sha256'],",
 "and type(pred) is dict and set(pred)==prep.PREDECESSOR_FIELDS\n+             and pred.get('initially_absent') is False and prep.sha(pred.get('run_record_sha256'))\n+             and pred.get('run_id')!=effect['run_id']\n+             and pred.get('scenario_sha256')==original_phases[phase['ordinal']-3]['scenario_sha256'],\n+             'F07_PREVIOUS_ACTUAL_ORDERED_SEQUENCE_REQUIRED')\n+        if phase['ordinal']==3:\n+            need(pred.get('run_id')==Path(ORIGINAL_PHASE1_CANONICAL['path']).stem\n+                 and pred.get('run_record_sha256')==ORIGINAL_PHASE1_CANONICAL['sha256']\n+                 and pred.get('review')=={k:ORIGINAL_PHASE1_REVIEW[k] for k in ('path','sha256')}\n+                 and pred.get('review_schema')=='frw.Root.F07.semantic-custody-review.v1',\n+                 'F07_SAME_STARTED_ORIGINAL_SEQUENCE_ANCHOR_REQUIRED')\n+        need(True,")
anchor=Path('/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113/ACTUAL-PHASE1/ROOT-ACTUAL-PHASE1-SEMANTIC-CUSTODY-PREDECESSOR-REVIEW.json')
# Metadata pins supplied in the TASK, no canonical body is read by this builder.
s += "\nORIGINAL_PHASE1_CANONICAL = "+repr(dict(path='/home/jericho/.local/share/friday-telegram-bot-test/runs/f07-ordered-noext-20261113-r1.json',bytes=13561,sha256='1ca07cc37f9be0ead7b5ddcae24d7f0b9f18fad38922bdc4743046b5ba0d961b'))+'\n'
s += "ORIGINAL_PHASE1_REVIEW = "+repr(dict(path=str(anchor),bytes=945,sha256='b6b21c122204dcea22ff87905cb8e47e9773677b737ea2c33069d0d27edfff2b'))+'\n'
sources['root_caller.py']=s
s=replace(sources['root_caller.py'],'import types\n','import types\nfrom pathlib import Path\n')
s=s.replace("        need(True,\n             'F07_PREVIOUS_ACTUAL_ORDERED_SEQUENCE_REQUIRED')\n",'')
sources['root_caller.py']=s
s=sources['root_f07_once.py']
s=s.replace('for the FIRST original F07 ordinary phase.','for one exact original F07 ordered successor (phases2..4).')
s=replace(s,"'Root_acceptance','resources','slot_identity','disk_scope'}", "'Root_acceptance','resources','slot_identity','disk_scope','phase_ordinal','accepted_predecessor'}")
s=replace(s,"'frw.Root.F07.first-phase-finite-driver.v1'", "'frw.Root.F07.ordered-successor-finite-driver.v1'")
s=replace(s,"    canonical_path(v['workdir'])", "    need(type(v['phase_ordinal']) is int and 2<=v['phase_ordinal']<=4,'F07_EXPLICIT_SUCCESSOR_ORDINAL_REQUIRED')\n    need(type(v['accepted_predecessor']) is dict\n         and set(v['accepted_predecessor'])=={'canonical_run','review','effect_and_consumer','proof','assessment'}\n         and all(reference_shape(r) for r in v['accepted_predecessor'].values()),'F07_ACTUAL_PREDECESSOR_BUNDLE_REQUIRED')\n    canonical_path(v['workdir'])")
old="""    saved=doc(v['saved_phase_preflight']);phase=saved['result']['phases'][0]
    need(phase['ordinal']==1 and phase['phase']=='NO_EXTENSION'
         and phase==checker.module(checker.PREP).phase_preparation(1,phase['scenario']['steps'][0]['input'])
         and readref(v['scenario'])==checker.encoded(phase['scenario']),'F07_EXACT_SAVED_FIRST_PHASE_REQUIRED')
    authority=doc(v['authority']);ordinary=checker.module(checker.PREP).compose_source(base,phase,run_id=v['run_id'],
        authority_ref=v['authority'],authority=authority,previous_phase=None)"""
new="""    saved=doc(v['saved_phase_preflight']);prep=checker.module(checker.PREP)
    phase,previous_phase=caller.select_ordered_successor(prep,saved,ordinal=v['phase_ordinal'],scenario_raw=readref(v['scenario']))
    authority=doc(v['authority'])
    caller.accepted_successor_predecessor(checker,phase=phase,previous_phase=previous_phase,run_id=v['run_id'],
        authority=authority,bundle=v['accepted_predecessor'],original_phases=saved['result']['phases'])
    ordinary=prep.compose_source(base,phase,run_id=v['run_id'],authority_ref=v['authority'],
        authority=authority,previous_phase=previous_phase)"""
s=replace(s,old,new)
s=replace(s,"    materials += [v['workdir'],phase['scenario']['steps'][0]['input']['path']]", "    materials += [v['workdir'],phase['scenario']['steps'][0]['input']['path']]\n    # Canonical predecessor is protected by its existing STATE contract; every\n    # Root review/proof/assessment source material remains in declared private roots.\n    materials += [r['path'] for k,r in v['accepted_predecessor'].items() if k!='canonical_run']")
s=replace(s,'    return caller,checker,base,phase,authority,ordinary,acceptance','    return caller,checker,base,phase,previous_phase,authority,ordinary,acceptance')
s=s.replace('caller,checker,base,phase,authority,ordinary,acceptance=source_inputs(v)','caller,checker,base,phase,previous_phase,authority,ordinary,acceptance=source_inputs(v)')
s=replace(s,'proof_ref=proof_ref,previous_phase=None)','proof_ref=proof_ref,previous_phase=previous_phase)')
sources['root_f07_once.py']=s
for name,text in sources.items():
 if name=='current209.py':continue
 text=text.replace('\n+','\n')
 ast.parse(text);(D/'source'/name).write_text(text)
s=sources['current209.py'];tree=ast.parse(s);n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='PREP' for t in n.targets));lines=s.splitlines(keepends=True);lines[n.lineno-1:n.end_lineno]=['PREP = '+repr(ref(D/'source/f07_phase_prepare.py'))+'\n'];s=''.join(lines);ast.parse(s);(D/'source/current209.py').write_text(s)
for name in sources:
 a=(B/'source'/name).read_text().splitlines(keepends=True);b=(D/'source'/name).read_text().splitlines(keepends=True)
 (D/(name+'.patch')).write_text(''.join(difflib.unified_diff(a,b,fromfile='accepted/'+name,tofile='successors/'+name)))
(D/'BASIS.json').write_bytes(encoded(dict(accepted_result=ref(B/'RESULT.json'),accepted_sources={p.name:ref(p) for p in (B/'source').glob('*.py')},source_start_moscow='2026-11-13T04:56:56+03:00',no_live_effects=True)))
print(json.dumps({p.name:ref(p) for p in (D/'source').glob('*.py')},sort_keys=True))
