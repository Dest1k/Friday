"""Root factual normalization + one future exact reviewed driver; no retry path.

--prepare only freezes honest Root judgments from already observed, reviewed facts.
--execute-once starts the new original600 clock AFTER bulk preparation/review,
reobserves actual mutable state, binds immutable refs, then execs one reviewed driver.
Neither option changes product/source/config/services or old records.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import types

os.umask(0o077)
U=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-ORDINARY207-ROOT-BINDING-SOURCE-20261112')
B=Path('/home/jericho/.cache/FRW-ASTRA-V3-POSTPOWER-RECOVERY-20261111')
O=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-FIRST-ORDINARY-WRONGREAD-20261112')
C=Path('/home/jericho/.cache/FRW-ASTRA-F06-ORDINARY-CONSTRUCTOR-ROOTS-20261112')
K=Path('/home/jericho/.cache/FRW-ASTRA-F06-FIRST-WRONGREAD-PRIVACY-CRITERION-20261112')
G6=Path('/home/jericho/.cache/FRW-ASTRA-V3-F06-TYPED-SETTER-FIX-20261112/operations/generate-g6')
REVIEW=Path('/home/jericho/.cache/FRW-ASTRA-REVIEW-FIRST-ORDINARY-F06-ROOT-BINDING-20261112/RESULT.json')
PYTHON='/home/jericho/jericho/.venv/bin/python'
def raw(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    p=Path(p);s=p.lstat();assert p.is_file() and not any(q.is_symlink() for q in (p,*p.parents)) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b))
def get(p):return json.loads(Path(p).read_bytes())
def put(p,v):
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw(v));f.flush();os.fsync(f.fileno())
    return ref(p)
def load(p,name):
    m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def modules():return load(U/'f06_source.py','root_f06_source'),load(U/'current207.py','root_f06_current')
def baseline(c,check):
    proof=check.unbound_proof();closure=get(check.CLOSURE)
    proof.update(contract_effect=check.source(c).effect(c),whole_effect_sha256=sha(raw(check.source(c).effect(c))),installation_closure=ref(check.CLOSURE),installation_acceptance=closure['source_acceptance'])
    return proof,check.observe(proof)
def prepare():
    a,check=modules();c=get(O/'BULK-CONTRACT-UNBOUND.json');old=get(O/'OBSERVED-BULK-FACTS.json');facts=get(O/'HISTORY-LINEAGE-BULK-FACTS.json')
    _,now=baseline(c,check);assert now==old, 'Bulk observation basis drift; reconcile before any grant'
    # Root must first accept the separate source/config result in a pinned record.
    accepted=get(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json');assert accepted['decision']=='ROOT_ACCEPT_SCOPED_SOURCE_CONFIG_INFERENCE'
    cref=accepted['result'];assert cref==ref(C/'RESULT.json')
    roots=accepted['effective_product_roots'];assert roots==[str(check.H)]
    assert accepted['profile_configs']==now['profile_configs'] and accepted['external_manager_source_inference']=='CORE_NO_EXPLICIT_HANDOFF_NO_MANAGER_CONSTRUCTED'
    sourceproof=ref(U/'independent-review/RESULT.json');assert get(sourceproof['path'])['decision']=='SOURCE_ONLY_READY_UNBOUND'
    producer=ref(G6/'ROOT-G6-SEVEN-CIPHERTEXT-AND-CLOSURE.json')
    qualification=ref(B/'F06-INSTALLED207-RETAINED-G6-DOCX-READONLY-20261112/RESULT.json')
    assert get(qualification['path'])['state']=='PASS_INSTALLED207_SAME_G6_STANDARD32_NATIVE_CODEC_READ_ONLY'
    # All512 raw rows precede g6 creation, all3 native message tails precede it;
    # retained genuine creation/custody + exact source/native continuity establish
    # this selected missing ingress. Other historical/unknown effects stay closed.
    assert not facts['source_exact_or_selected_filename_matches'] and all(r['predates_source'] for r in facts['all_512'])
    assert all(v['last_before_g6'] for v in facts['all_three_database_metadata'].values())
    for run_id in now['history']['run_ids']:
        path=check.STATE/'runs'/(run_id+'.json')
        assert path.stat().st_mtime<facts['source_file_created_mtime_epoch']
    history=dict(schema='frw.Root.F06.history-semantic-once.v1',operator='Root',status='ROOT_BOUND',phase=a.PHASE,source=a.SOURCE,history_manifest_sha256=now['history']['manifest_sha256'],classified_run_ids=now['history']['run_ids'],native_boundary_sha256=now['f06_mutable_boundary']['native_boundary_sha256'],once_sha256=now['f06_mutable_boundary']['once_sha256'],ingress_lineage_sha256=now['f06_mutable_boundary']['ingress_lineage_sha256'],equivalent_original_phase_effects=[],all_profile_history_and_compacted_unlogged_equivalents_reconciled=True,old_effects_UNKNOWN_and_clocks_preserved=True,M14_partial_UNKNOWN_preserved_no_replay_or_regrade=True,all_profile_projection_limit=check.LIMIT,retained_basis=[ref(O/'HISTORY-LINEAGE-BULK-FACTS.json'),producer,ref(B/'F06-ORDINARY-DOCX-ROOT-PREPARATION-20261112/RESULT.json')],judgment_scope='Selected retained fresh g6 DOCX first ingress only. All512 raw run files and all3 native tails predate generation. No native ingress since creation; producer/closed readonly consumer effects did not send. Exact same source/name absent. Unrelated consumed/UNKNOWN not replayed, invisible in-memory global absence not claimed.')
    privacy=get(U/'ROOT-REVIEW-TEMPLATES.UNBOUND.json')['runtime_privacy_review']
    private=sorted({str(U),str(O),str(B),str(G6.parents[1]),str(K),str(C)})
    privacy.update(status='ROOT_BOUND',genuine_installed_runtime_consumer_observed=True,no_marker_or_import_bypass=True,raw_user_chat_retention_separately_reviewed=True,no_blanket_no_secret_persistence_claim=True,effective_product_roots=roots,effective_roots_profile_config_refs=now['profile_configs'],effective_roots_source_basis=[ref(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json'),cref],private_roots=private,runtime_evidence=[ref(B/'F06-INSTALLED206-READ-FILE-PRIVACY-LEAF-SAVED-ASSESSMENT-20261112.json'),ref(B/'F06-INSTALLED206-READ-FILE-PRIVACY-LEAF-20261112/RESULT.json'),ref(K/'RESULT.json'),ref(B/'F06-PRIVACY-NATIVE205-PERSISTENCE-ROOT-ACCEPTANCE-20261112.json')],scope='Actual installed206 pure consumer observed without overlay/guard bypass; its relevant installed207 DOCX/technical-copy bytes unchanged. This does not relabel invocation207 or fullwrapperWARN; original7/8FAIL/WARN_NOT_RUN retained. Raw intentional private user caption is permitted chat retention; reply/assistant/reasoning/tool/log/memory carriers must be assessed on actual new effect. No blanket secret persistence, global file confinement, MAC, ordinary or F06 acceptance.')
    assert privacy['runtime_hashes']==check.RUNTIME_HASHES
    check.disjoint(private,roots)
    lineage=get(U/'ROOT-REVIEW-TEMPLATES.UNBOUND.json')['source_ingress_lineage']
    lineage.update(status='ROOT_BOUND',source_identity=now['source_identity'],current_ingress_lineage_sha256=now['f06_mutable_boundary']['ingress_lineage_sha256'],original_producer_g6_retained=True,no_new_producer_or_native_repeat=True,first_ordinary_upload_not_previously_consumed=True,native_qualification=qualification,retained_producer_oracle_basis=[producer,ref(B/'F06-RETAINED-SEVEN-INPUT-ASSESSMENT/COMPOSITE-INPUT-ORACLE.json'),ref(O/'HISTORY-LINEAGE-BULK-FACTS.json')])
    proofs=dict(original_criterion=ref(K/'ORIGINAL-CRITERION.json'),independent_encrypted_producer=producer,actual_native_qualification=qualification,source_review=sourceproof)
    for key,value in [('all_profile_history_semantic_once',history),('private_password_handling',privacy),('source_ingress_lineage',lineage)]:proofs[key]=put(O/(key+'.json'),value)
    proofs['same_B_principal']=put(O/'SAME-B-PRINCIPAL.json',dict(operator='Root',status='ROOT_BOUND_SCOPED_PRINCIPAL',principal=now['databases']['tester']['principal'],gateway=now['gateway'],native_readonly=now['native_readonly'],observation=ref(O/'OBSERVED-BULK-FACTS.json'),one_private_sameB_only=True,no_other_profile_rights=True))
    # Final clock and its two proof refs are deliberately not created in preparation.
    c['root_proofs'].update(proofs);c['boundary']=now['f06_mutable_boundary']
    put(O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json',c)
    put(O/'ROOT-BULK-DECISION.json',dict(schema='friday.root.F06.bulk-decision.v1',decision='ROOT_FACTUAL_PREPARATION_ACCEPTED_NO_CLOCK_NO_AUTHORITY_NO_SEND',contract=ref(O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json'),freeze=ref(U/'SOURCE-FREEZE.json'),review=sourceproof,resources=ref(O/'PRE-CLOCK-RESOURCES-DEPENDENCIES.json'),current_prepared_observation=ref(O/'OBSERVED-BULK-FACTS.json'),first_ordinary_effect_started=False,required_before_once='Independent review of Root normalization/binder; fresh actual facts; final original600 clock/refs; reviewed single driver'))
    print(json.dumps(dict(state='ROOT_BULK_PREPARED_NO_CLOCK_NO_GRANT_NO_SEND',decision=ref(O/'ROOT-BULK-DECISION.json'))))
def execute_once():
    a,check=modules();c=get(O/'ROOT-PREPARED-CONTRACT-NO-CLOCK.json')
    review=get(REVIEW);assert review['decision']=='ACCEPT_ROOT_BINDING_PREPARATION_NO_LIVE_GRANT'
    assert review['root_binder_sha256']==sha(Path(__file__).read_bytes()) and review['root_bulk_decision_sha256']==ref(O/'ROOT-BULK-DECISION.json')['sha256'] and review['open_critical_defects']==[]
    assert not (O/'work/ROOT-ONCE-INVOCATION.json').exists() and not (O/'EXECUTION-CLOCK.json').exists() and not (check.STATE/'runs'/(c['run_id']+'.json')).exists()
    accepted=get(O/'CONSTRUCTOR-ROOTS-ROOT-ACCEPTANCE.json')
    assert accepted['result']==ref(C/'RESULT.json')
    basis=get(accepted['basis']['path'])
    assert accepted['basis']==ref(Path(accepted['basis']['path']))
    for row in basis['source_files'].values():check.reference(row['ref'],private=False)
    for row in accepted['proxy_scope_metadata']:check.reference(row['file'],private=True)
    _,now=baseline(c,check);assert now==get(O/'OBSERVED-BULK-FACTS.json'),'Mutable basis changed before new clock'
    # Inventory metadata only, for assessing new technical carriers after actual effect.
    files=[]
    dirs=[check.H/'logs',check.H/'sessions',check.H/'memories',check.H/'user-artifacts']
    profile=check.H/'profiles/telegram-bot-8812646969'
    dirs += [profile/name for name in ('logs','sessions','memories','workspace','cache','.curator_backups')]
    for root in dirs:
        if root.exists():
            for path in sorted(root.rglob('*')):
                assert not path.is_symlink() and len(files)<12000
                if path.is_file():
                    s=path.stat();files.append(dict(path=str(path),device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
    put(O/'PRE-EFFECT-TECHNICAL-CARRIER-METADATA.json',dict(roots=list(map(str,dirs)),files=files,db_metadata=now['databases'],at_moscow=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(),content_read=False))
    cursor=subprocess.run(['journalctl','--user','-u','hermes-gateway-1b7e7667.service','-n','0','--show-cursor','--no-pager'],check=True,capture_output=True,timeout=10).stdout.decode()
    put(O/'PRE-EFFECT-JOURNAL-CURSOR.json',dict(cursor=cursor,content_read=False))
    # THE NEW600 clock starts here; no peer wait/prep/gate is opened inside it.
    wall,mono=time.time(),time.monotonic()
    clock=dict(schema='frw.Root.F06.original-finite-clock.v1',started_at=wall,deadline_at=wall+600,started_monotonic=mono,deadline_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    clock_ref=put(O/'EXECUTION-CLOCK.json',clock);c['resources']['clock']=clock_ref
    wait=put(O/'OWNED-WAIT-AND-CLEANUP.json',dict(operator='Root',status='ROOT_BOUND_FINITE_SAME_CHILD',clock=clock_ref,driver=ref(U/'root_bind_dispatch_once.py'),same_child_nonreentrant_signal_drain=True,pending_birth_signal_handoff=True,reap_inside_original_deadline=True,no_appended_cleanup_time=True,stop_unconfirmed_retains_child_slot=True,permanent_gateway_dashboard_untouched=True))
    c['resources']['owned_parent_wait_cleanup']=wait
    c['root_proofs']['owned_actor_stop_resources']=wait
    c['root_proofs']['authoritative_budget_policy']=put(O/'AUTHORITATIVE-BUDGET-POLICY.json',dict(operator='Root',status='ROOT_AUTHORIZED_EXACT_ORIGINAL_FINITE_OPERATION',criterion=c['root_proofs']['original_criterion'],source_review=c['root_proofs']['source_review'],timing=a.TIMING,clock=clock_ref,cpu_seconds=c['resources']['cpu_seconds'],address_space_bytes=c['resources']['max_rss_bytes'],store_growth_and_temporary_copy_cap=c['resources']['disk_bytes'],new_previously_unstarted_operation=True,old_clocks_reset=False,one_initial_upload_only=True,followup_or_retry_authorized=False,scope=c['scope']))
    prepared,actual=baseline(c,check);assert actual==now,'Mutable basis changed during final binding'
    prepared.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION',observed=actual,runtime_privacy_review=c['root_proofs']['private_password_handling'],history_semantic_review=c['root_proofs']['all_profile_history_semantic_once'])
    # Run all non-live semantic/path checks before the single driver's durable claim.
    check.semantic(prepared,c,actual);check.private_material(prepared,c,actual,O/'ROOT-PREPARED-CURRENT-PROOF.json')
    c['root_current_proof']=put(O/'ROOT-PREPARED-CURRENT-PROOF.json',prepared)
    slot=check.SLOT.stat();slot_identity=dict(device=slot.st_dev,inode=slot.st_ino,uid=slot.st_uid,mode=stat.S_IMODE(slot.st_mode),nlink=slot.st_nlink)
    binding=dict(schema='frw.Root.F06.first-wrongread-driver.v1',status='ROOT_BOUND_ONE_FUTURE_OPERATION',contract=c,source_freeze=ref(U/'SOURCE-FREEZE.json'),independent_review=c['root_proofs']['source_review'],workdir=str(O/'work'),slot_identity=slot_identity,expected_binding_sha256=None)
    bref=put(O/'ROOT-BINDING-INPUTS.json',binding)
    assert min(clock['deadline_at']-time.time(),clock['deadline_monotonic']-time.monotonic())>=305
    os.execv(PYTHON,[PYTHON,'-I','-B','-S',str(U/'root_bind_dispatch_once.py'),'--execute-once',bref['path'],bref['sha256']])
if __name__=='__main__':
    assert sys.argv[1:] in (['--prepare'],['--execute-once'])
    prepare() if sys.argv[1]=='--prepare' else execute_once()
