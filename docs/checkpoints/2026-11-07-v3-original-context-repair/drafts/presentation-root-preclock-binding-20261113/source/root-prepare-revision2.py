"""Root-only finite metadata/input binding; no new/claim/API/send/Office.

Invoke only after Root accepts the two finite metadata preparations. The reviewed
full-caller CLI remains a separate mandatory pre-clock check, then live admission.
Revision2 reuses authenticated saved collection/phase/runtime/scenario metadata.
It refreshes canonical history only; saved facts are not current admission.
"""
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import secrets
import signal
import stat
import sys
import time
import traceback
import types

D=Path(__file__).parent
PARENT=Path('/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113')
SAVED_RUNTIME={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-SELECTED-RUNTIME-BASIS.json', 'bytes': 62348, 'sha256': 'cecfed8549d8885532aee1baa2bced44840452076812df98cf829a298616f8c0'}
SAVED_PHASE={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-PRESENTATION-PREPARATION.json', 'bytes': 5442, 'sha256': 'c59a845f70185afe9b5e0d1b39a7ddd90d4012610a672a10e067427cb6747161'}
SAVED_SCENARIO={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-SCENARIO.json', 'bytes': 1938, 'sha256': '00262cd02882795a8d8a96ecece6308e955e4d9b7a7944b901ff1dfa7efa560b'}
SAVED_CURRENT={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-CURRENT-FACTS-BEFORE-FULLCALLER.json', 'bytes': 1726395, 'sha256': 'b14887972183999e541f6ef4ab24885212d51b6d14755448d40928fa1c100874'}
RUNTIME_ADOPTION={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-FINITE-RUNTIME-BASIS-ADOPTED.json', 'bytes': 3726, 'sha256': '7c8257b41d22fbdf468feb2e3a7a511fb8d0060b64420198dcb854473d9f434a'}
DELTA_ADOPTION={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-FORWARD-EFFECT-DELTA-ACCEPTED.json', 'bytes': 6990, 'sha256': '74f6a2ddfccb228cf9b7af09e625936efbd2f5fbeb0273a0b844d4b06045b68c'}
POSTCONDITION_RECIPE={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-POSTCONDITION-RECIPE-ACCEPTED.json', 'bytes': 2797, 'sha256': '6f87f64e45c74ba773ec9f99e8f85319b3f6b498fc32ebd7d6019164cf89cad6'}
ORIGINAL_REFUSAL={'path': '/home/jericho/.cache/FRW-ASTRA-V3-PRESENTATION-ORDINARY209-ROOT-20261113/ROOT-INPUT-PREPARATION-REFUSED.json', 'bytes': 472, 'sha256': 'eaea5b3bf2779d9fc4d0bd5dc8ef4379bbd0ff527a0b165f2a105677d91f542f'}
S=Path('/home/jericho/.cache/FRW-SOL-V3-PRESENTATION-CURRENT209-CALLER-CORE-20261113')
A=Path('/home/jericho/.cache/FRW-ASTRA-SOL-T38-PRESENTATION-CURRENT209-CALLER-20261113')
F=Path('/home/jericho/.cache/FRW-ASTRA-V3-F07-ORDINARY209-ROOT-20261113')
RUN='f04-pptx-odp-first209-20261113-r1'

def encoded(v):return (json.dumps(v,ensure_ascii=True,sort_keys=True,allow_nan=False)+'\n').encode()
def ref(p):
    b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def new(name,value):
    p=D/name;raw=encoded(value)
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(p,want):
    assert not any(q.is_symlink() for q in (p,*p.parents))
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
        before=os.fstat(f.fileno())
        assert stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600
        raw=f.read(1024**2+1);after=os.fstat(f.fileno())
    ident=lambda s:tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    assert len(raw)<=1024**2 and len(raw)==before.st_size and ident(before)==ident(after)==ident(p.stat())
    assert hashlib.sha256(raw).hexdigest()==want
    m=types.ModuleType('_root_presentation_'+want[:12]);m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__);return m

def history_records(rows,sizes):
    """Pure canonical record projection, ordered by full filenames."""
    return sorted([[key+'.json',row['sha256'],sizes[key+'.json']] for key,row in rows.items()],key=lambda row:row[0])

def main():
    assert D==PARENT/'revision2'
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2))
    def expired(*_):raise TimeoutError('ROOT_PRESENTATION_INPUT_PREPARATION_WALL300')
    signal.signal(signal.SIGALRM,expired);signal.alarm(300)
    driver=load(S/'root_presentation_once.py','d46105322d90f3150aad274a0861e94f2ef45bfba89c7921df3dc3826dbf57f0')
    helper=driver.read_shared()
    checker_ref=dict(path=str(S/'presentation_current209.py'),bytes=54561,sha256='4b300ce8c7cd514254d5b35dd4b59916045e54e8a9e9d9908fb25ebef17a4d23')
    checker=helper.load_raw(helper.readref(checker_ref),checker_ref['path'],'_Root_presentation_current')
    prep=checker.module(checker.PREP)
    # Exact refs are supplied by Root after reading their completed evidence.
    runtime_ref=json.loads(sys.argv[1]);delta_ref=json.loads(sys.argv[2])
    runtime=helper.doc(runtime_ref);delta=helper.doc(delta_ref)
    assert runtime['operator']=='Root' and runtime['status']=='ROOT_BOUND_METADATA_ONLY_NOT_RUNTIME_VERDICT'
    adopted=helper.doc(RUNTIME_ADOPTION)
    assert adopted['Root_adopts_finite_named_categories'] is True and adopted['proposed_basis']==runtime_ref
    delta_adopted=helper.doc(DELTA_ADOPTION)
    assert delta_adopted['Root_accepts_bounded_first_forward_absence'] is True and delta_adopted['report']==delta_ref
    assert delta['state']=='COMPLETE_BOUNDED_DELTA_NO_NEW_ORDINARY_FORWARD_FOUND_ROOT_CURRENT_ADMISSION_SEPARATE'
    assert delta['semantic_effect_conclusion']['equivalent_ordinary_PPTX_to_ODP_found'] is False
    runtime_basis=SAVED_RUNTIME
    assert helper.doc(runtime_basis)==runtime
    unit=helper.doc(dict(path=str(A/'ROOT-V03-RETAINED-ORIGINAL-UNIT-BOUND.json'),bytes=2815,sha256='a186844cddf35fc54e63b63fc7c778c82a40988dca2cd06c54de82d53aa45525'))
    phase_ref=SAVED_PHASE;phase=helper.doc(phase_ref)
    prep.validate_preparation(phase)
    assert phase['retained_unit']==unit and phase['runtime_basis']==runtime_basis
    scenario_ref=SAVED_SCENARIO
    assert helper.readref(scenario_ref)==driver.encoded(phase['scenario'])
    history_helpers=load(F/'qualify_whole_new_prefix_readonly.py','13492267220a8f677321790a6d1dc31f4620262d56a5e20bc634818ba4e5e169')
    work=PARENT/'PPTX-ODP-ONCE'
    helper.protected_directory(work)
    assert not list(work.iterdir())
    fds=[]
    try:
        for p in (driver.SLOT,driver.STATE/'consumer.lock',driver.STATE/'tester-token'):
            fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW);fds.append(fd)
            s=os.fstat(fd)
            assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        rows,raws=history_helpers.history()
        assert len(rows)==518 and sum(r['unknown_retained'] for r in rows.values())==3
        assert not (driver.STATE/'runs'/(RUN+'.json')).exists()
        old=helper.doc(ref(F/'ROOT-PHASE4-BOUND-DRIVER-INPUT.json'))
        current_ref=SAVED_CURRENT;observed=helper.doc(current_ref)
        assert observed['state']=='READONLY_CURRENT_FACTS_NOT_OPERATION_ADMISSION'
        assert observed['operation_clock_created'] is False and observed['authority_issued'] is False
        assert helper.doc(ORIGINAL_REFUSAL)['no_new_API_send_model_claim_or_clock'] is True
        sizes={key+'.json':(driver.STATE/'runs'/(key+'.json')).stat().st_size for key in rows}
        assert observed['observed']['history']['records']==history_records(rows,sizes)
        manifest=[dict(name=n,bytes=size,sha256=sha) for n,sha,size in observed['observed']['history']['records']]
        assert hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()==delta['canonical_exact_diff']['current_manifest_sha256']==delta_adopted['canonical_manifest']
        for label in ('default','dest'):
            expected=delta['all_profile_scope']['reused_'+label+'_metadata']
            assert {k:observed['observed']['databases'][label][k] for k in expected}==expected
        assert observed['observed']['databases']['tester']['messages']==delta['native_actual_delta']['current_messages']==5543
        assert observed['observed']['databases']['tester']['max_message_id']==delta['native_actual_delta']['current_max_id']==5543
        state=observed['observed']['gateway'];now=time.time()
        authority=dict(schema='frw.Root.ordinary-independent-history-admission.v1',authority_id='Root-F04-original-first-forward-current209-20261113',operator='Root',accepted=True,created_at=now,expires_at=now+900,boot_id=state['boot_id'],run_scenarios={RUN:phase['scenario_sha256']},new_independent_inputs_only=True,no_old_task_replay=True,old_rows_modified=False,unknown_effects_resolved=False,product_or_B00_acceptance=False,new_trial_for_historical_task=False,history=rows,gateway=dict(state_path=str(checker.H/'gateway_state.json'),pid=state['pid'],start_time=state['start_time'],maximum_staleness_seconds=600),ordered_predecessors={},presentation_original_case=dict(case_id='F-04',case_index=165,direction='PPTX_TO_ODP',genuinely_missing_original_forward=True,no_converter_or_App_replay=True,source_reference=unit['source_reference'],original_alias=unit['original_alias'],principal=unit['principal'],conversation=unit['conversation']),presentation_task=dict(kind='ordinary-document-task',nonce=secrets.token_hex(16),request=phase['scenario']['steps'][0]['request'],source_reference=unit['source_reference'],output=dict(filename=None,mime_type='application/vnd.oasis.opendocument.presentation')),presentation_scenario=scenario_ref,scope='Exact missing original ordinary forward, separate Root fullcaller qualification and live admission required')
        auth_ref=new('ROOT-ORDINARY-FORWARD-HISTORY-AUTHORITY.json',authority)
        scope_ref=new('ROOT-PRESENTATION-WRITE-SCOPE.json',dict(schema='friday.Root.presentation.finite-write-scope.v1',at_moscow=dt.datetime.now().astimezone().isoformat(),source=old['disk_scope']['scope_evidence'],selected_presentation_source=ref(checker.H/'hermes-agent/hermes_cli/friday_workspace_presentation.py'),scope='Existing product persistence and tester roots plus own operation; native converter uses separately bounded temporary work/40wall35CPU2GiB16MiBperfile and removes its work in finally. Aggregate observed growth is not hard filesystem quota or full tmpfs measurement.',limitations=['Between-sample transient growth may be missed','Native temporary work is outside tester aggregate persistence monitor','No healthy service lifetime timer or global filesystem capability claim']))
        scope=dict(old['disk_scope']);scope['directory_roots']=sorted([str(work) if p==old['workdir'] else p for p in scope['directory_roots']]);scope['scope_evidence']=[scope_ref]
        v=dict(schema='frw.Root.PRESENTATION.single-forward-driver.v1',status='ROOT_BOUND_ONE_FUTURE_OPERATION',operator='Root',run_id=RUN,workdir=str(work),driver=ref(S/'root_presentation_once.py'),source_review=ref(S/'final-review/RESULT.json'),preparation=phase_ref,checker=checker_ref,selected_tester=old['selected_tester'],authority=auth_ref,installation_closure=old['installation_closure'],source_acceptance=old['source_acceptance'],resources=dict(driver.TIMING,**driver.LIMITS),slot_identity=helper.lock_identity(os.fstat(fds[0])),disk_scope=scope)
        privacy=helper.doc(old['Root_acceptance'])['privacy_preflight']
        original_refs=[unit['original'][k] for k in ('run','source_upload_ack','admission','window','custody','closed_operation')]
        privacy['private_roots']=sorted(set(privacy['private_roots']+[str(D),str(PARENT),str(S),str(A),str(Path(runtime_ref['path']).parent),str(Path(delta_ref['path']).parent)]+[str(Path(r['path']).parent) for r in original_refs]))
        for root in privacy['private_roots']:
            helper.protected_directory(root)
            assert all(not Path(root).is_relative_to(Path(p)) and not Path(p).is_relative_to(Path(root)) for p in privacy['effective_product_roots'])
        for r in original_refs:
            helper.readref(r)
            assert any(Path(r['path']).is_relative_to(Path(root)) for root in privacy['private_roots'])
        # Same material coverage and private-marker predicates as the later
        # checker.decisions, without fabricating future proof/clock/ACK fields.
        materials=[v[k]['path'] for k in ('driver','source_review','preparation','checker','authority','installation_closure','source_acceptance')]
        materials += [scenario_ref['path'],str(work),runtime_basis['path'],unit['Root_binding']['path']]+[r['path'] for r in original_refs]
        assert all(any(Path(p).is_relative_to(Path(root)) for root in privacy['private_roots']) for p in materials)
        markers=[p.encode() for p in privacy['private_roots']]
        for r in observed['observed']['profile_configs'].values():
            assert not any(marker in checker.read_reference(r,private=False) for marker in markers)
        for name in ('cmdline','environ'):
            assert not any(marker in checker.process_bytes(observed['observed']['gateway']['pid'],name) for marker in markers)
        privacy['scope']='Selected ordinary original PPTX→ODP; unchanged two metadata sites/source209. Future actual logging remains NOT_ESTABLISHED; effective roots source/config inference only. Private source/notes/raw retention separate; no all-profile filesystem capability claim.'
        a=dict(schema='frw.Root.PRESENTATION.explicit-preop-decisions.v1',status='ROOT_BOUND_ONE_FUTURE_FORWARD',operator='Root',run_id=RUN,scenario_sha256=phase['scenario_sha256'],Root_authorizes_observed_hash_binding_only=True,bindings={k:v[k] for k in ('driver','source_review','preparation','checker','selected_tester','authority','installation_closure','source_acceptance')},accepted_current_facts=driver.current_facts(checker,observed['observed']),original_forward_decision=dict(original_forward_effect_eligible=True,old_effects_UNKNOWN_clocks_preserved=True,all_profile_semantic_unlogged_equivalents_reconciled=True,root_current_pending_approval_cancel_maintenance_assessed=True,equivalent_consumed_forward_effects=[],projection_limit=driver.PROJECTION_LIMIT,current_scope_evidence=[delta_ref,current_ref,ref(A/'ROOT-V03-UNIT-SOURCE-VALIDATION-AND-NAMESPACE-ERRATUM.json')],reconciliation_scope='Root accepted exact506baseline plus saved518/new12 canonical and native5468–5543 delta. Revision2 refreshes canonical history only; authenticated saved all3SQL/globalquiescence/once/cancel/maintenance facts are reused, never labelled current-fresh admission. Mandatory genuine readonly-before-clock refreshes mutable facts before a separate live decision. Saved local producer/reverseV04/UNKNOWN effects remain closed; all-profile RAM limit retained.'),privacy_preflight=privacy,aggregate_disk_monitor_limitations_accepted=True,current_facts_basis=dict(reference=SAVED_CURRENT,freshness='SAVED_FINITE_COLLECTION_NOT_CURRENT_ADMISSION',nearest_preclock_current_refresh_required=True))
        v['Root_acceptance']=new('ROOT-EXPLICIT-DECISIONS.json',a)
        driver.source_inputs(v,helper)
        assert history_helpers.history()==(rows,raws)
        bound=new('ROOT-BOUND-DRIVER-INPUT.json',v)
        new('ROOT-BOUND-SOURCE-INPUTS-QUALIFIED.json',dict(state='ROOT_BOUND_INPUT_SOURCE_ONLY_SAVED_FACTS_NEAREST_PRECLOCK_CLI_STILL_REQUIRED',at_moscow=dt.datetime.now().astimezone().isoformat(),input=bound,postcondition_recipe=POSTCONDITION_RECIPE,current=current_ref,current_facts_freshness='SAVED_FINITE_COLLECTION_NOT_CURRENT_ADMISSION',parent_refusal=ORIGINAL_REFUSAL,canonical_count=518,unknown_retained=3,API_new_send_claim_clock=False))
        print(json.dumps(bound,sort_keys=True))
    finally:
        for fd in reversed(fds):os.close(fd)
        signal.alarm(0)

if __name__=='__main__':
    try:main()
    except BaseException as e:
        new('ROOT-INPUT-PREPARATION-REFUSED.json',dict(state='INPUT_PREPARATION_REFUSED_NO_NEW_USER_OPERATION',exception_class=type(e).__name__,fixed_code=str(e) if isinstance(e,ValueError) and str(e).startswith(('F07_','PRESENTATION_')) else None,trace_locations=[dict(file=x.filename,line=x.lineno,function=x.name) for x in traceback.extract_tb(e.__traceback__)],no_new_API_send_model_claim_or_clock=True))
        raise SystemExit(1)
