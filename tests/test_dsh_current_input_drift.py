"""Every actual pinned leaf is re-read by the ordinary current consumer."""
from pathlib import Path
import pytest
from test_dsh_current_availability import candidate, env, make_proof, activate_proof
from friday_admin_controls import dsh_current_availability as cur
from friday_admin_controls import host_runtime as hr


@pytest.mark.parametrize('leaf',['node','cli','patch','native_0','web_resolver','web_trust_bundle','web_egress_evidence','web_research_policy'])
def test_actual_input_drift_denies_active_current_health(candidate,leaf):
    f=candidate;activate_proof(f,make_proof(f))
    assert hr.deployment_health(f.c)==f.c
    path=Path(f.d['inputs'][leaf]['path'])
    path.write_bytes(path.read_bytes()+b'\nDRIFT')
    with pytest.raises((RuntimeError,ValueError,OSError)):hr.deployment_health(f.c)


def test_unrelated_pending_receipt_refused_before_any_stage(candidate,monkeypatch):
    f=candidate
    import time
    from test_dsh_current_availability import save
    from friday_admin_controls import runtime_observers
    now=time.monotonic();folder=f.root/'unrelated-t1-observation'
    clock=save(f.root/'unrelated-t1-clock.json',{'schema':'friday.dsh-current-observation.clock.v1','boot_id':cur.identity()['boot_id'],'started_mono':now-1,'deadline_mono':now+179,'seconds':180,'stage_folder':str(folder)})
    pending=save(f.root/'unrelated-t1-transaction.json',{'state':'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED','runtime_acceptance':'NOT_GRANTED','consumers_started':False,'dsh_current':{'stage':'friday.dsh-current-declaration-stage.v1','declaration':{'path':'/foreign','sha256':'a'*64},'proof':None,'cycle':f.c['current_availability']['cycle'],'runtime_sha256':f.d['runtime_sha256']}})
    calls=[]
    monkeypatch.setattr(runtime_observers,'dsh_observe',lambda *a,**k:calls.append(True))
    with pytest.raises(hr.HostUnavailable,match='pending_transaction'):
        cur.observe_current(f.c,clock_reference=clock,pending_transaction=pending,folder=folder,verify=lambda:None)
    assert not calls and not folder.exists()


def test_one_clock_cannot_select_another_observation_folder(candidate,monkeypatch):
    f=candidate
    import time
    from test_dsh_current_availability import save
    # Folder refusal must be exercised after a genuine synthetic native T1,
    # rather than being masked by a fabricated pending stdout/status report.
    proof=make_proof(f)
    folder=f.root/'clock-original-folder'
    original_clock=cur.read_json(proof['clock'])
    clock=save(f.root/'clock-folder.json',dict(original_clock,stage_folder=str(folder)))
    pending=proof['pending_transaction']
    from friday_admin_controls import runtime_observers
    monkeypatch.setattr(runtime_observers,'dsh_observe',lambda *a,**k:pytest.fail('observation before folder admission'))
    with pytest.raises(hr.HostUnavailable,match='new_observation_folder'):
        cur.observe_current(f.c,clock_reference=clock,pending_transaction=pending,folder=f.root/'other-folder',verify=lambda:None)
    assert not folder.exists() and not (f.root/'other-folder').exists()
