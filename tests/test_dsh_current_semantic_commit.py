"""Source/native-consumer fixtures; no native admission, model or network.

Actual serializers, typed planner, native managed-profile seal and owned-inode
publication run in synthetic homes. Native release authority is explicitly a
stub and does not prove an installed T1 transaction.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest
from test_dsh_current_availability import candidate, env, make_proof, save, activate_proof
from test_dsh_current_writer import writer_case, publish
from friday_admin_controls import worker_declarations as dec
from friday_admin_controls import worker_declaration_writer as writer
from friday_admin_controls import dsh_current_availability as cur
from friday_admin_controls.stopped_operator import _encoded
from scripts import friday_ordinary_install as ordinary

REFUSED = (ValueError, RuntimeError, OSError, KeyError, TypeError)


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def intent(request, reference):
    return {'schema': writer.APPLY_SCHEMA, 'state': 'CONSUMED_NO_RETRY',
        'request_sha256': reference['sha256'], 'request_reference': reference,
        'request_semantic_sha256': hashlib.sha256(_encoded(request)).hexdigest(),
        'clock': cur.read_json(request['clock']), 'clock_reference': request['clock'],
        'previous_input': request['previous_input'], 'current_input': request['current_input'],
        'before': request['before'], 'ready': False, 'retry_authorized': False,
        'consumers_started': False, 'workers_enabled': False, 'runtime_acceptance': 'NOT_GRANTED'}


def request_for(s):
    return {'schema': dec.DSH_CURRENT_APPLY_SCHEMA, 'seconds': 180,
        'home': str(s.f.e.home), 'profile': s.f.h.name,
        'previous_input': s.view.request['current_input'],
        'current_input': s.view.request['current_input'],
        'native_unit': {'path': str(s.evidence/'not-run.service'), 'sha256': 'a'*64},
        'before': {name: {'path': str(s.f.e.home/name),
            'sha256': hashlib.sha256(state['data']).hexdigest()}
            for name, state in s.view.before.items()},
        'retained': {}, 'declaration_source': s.source,
        'launcher_source': s.view.request['launcher_source'],
        'clock': s.f.c['current_availability']['cycle'], 'native_pm': {}}


@pytest.fixture
def committed_case(writer_case):
    s = writer_case
    outputs = writer.prepare_afterimages(s.view, s.plan, s.stage)
    request = request_for(s)
    request_ref = save(s.evidence/'request.json', request)
    tx = s.f.e.home/'preparation'/dec.dsh_current_transaction_name(s.b)
    tx.parent.mkdir(mode=0o700, exist_ok=True); tx.mkdir(mode=0o700)
    s.stage.rename(tx/'stage')
    (tx/'before').mkdir(mode=0o700)
    for name, state in s.view.before.items():
        ordinary.private_parents(tx/'before', name)
        ordinary.write(tx/'before'/name, state['data'], state['mode'])
    ordinary.write(tx/'intent.json', _encoded(intent(request, request_ref)))
    owned, _ = publish(s, outputs)
    result = {'state': 'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED',
        'ready': False, 'workers_enabled': False, 'consumers_started': False,
        'database_changed': False, 'native_migration': 'IMPLEMENTED',
        'runtime_acceptance': 'NOT_GRANTED', 'automatic_prepare': False,
        'request_sha256': request_ref['sha256'], 'clock': request['clock'],
        'previous_input': request['previous_input'], 'current_input': request['current_input'],
        'semantic_changes': s.plan['semantic_changes'],
        'after': {name: hashlib.sha256(state['data']).hexdigest() for name,state in outputs.items()},
        'original_attempt_consumed': True,
        'dsh_current': {'stage': dec.DSH_CURRENT_DECLARATION_SCHEMA,
            **copy.deepcopy(s.f.c['current_availability']), 'runtime_sha256': s.f.d['runtime_sha256']}}
    committed_state = writer._new_journal(tx/'committed.json', ordinary.encoded(result))
    authority = SimpleNamespace(home=s.f.e.home, tx=tx, declaration_bundle=s.b,
        clock=cur.read_json(request['clock']), request=request,
        request_reference=request_ref, prove_released=lambda: None)
    # This is a fixture's release stub, explicitly not native release admission.
    writer._dsh_completed(authority, result, committed_state, owned)
    s.f._pending_transaction=pin(tx/'committed.json')
    return SimpleNamespace(s=s, tx=tx, result=result, request=request,
        reference=pin(tx/'committed.json'), authority=authority,
        state=committed_state, owned=owned)


def checked(c, **kw):
    f=c.s.f
    return writer.checked_dsh_current_commit(c.reference,
        f.c['current_availability']['declaration'], f.d['runtime_sha256'],
        f.c['current_availability']['cycle'], config=f.c, **kw)


def test_semantic_initial_edge_ignores_format_path_clock_and_D_changes(writer_case):
    s=writer_case; first=dec.dsh_current_transaction_name(s.b)
    changed=copy.deepcopy(s.b); ref=changed['runtime_after']['current_availability']['declaration']
    document=cur.read_json(ref); p=s.evidence/'reformatted.json'
    p.write_text(json.dumps(document, indent=4)+'\n');p.chmod(0o600)
    changed['runtime_after']['current_availability']['declaration']=pin(p)
    changed['runtime_after']['current_availability']['cycle']={'path':'/different-clock','sha256':'a'*64}
    assert first==dec.dsh_current_transaction_name(changed)
    document['policy_authority']['id']='different-D-same-initial-baseline'
    save(p,document)
    changed['runtime_after']['current_availability']['declaration']=pin(p)
    assert first==dec.dsh_current_transaction_name(changed)
    different=copy.deepcopy(s.own);different['max_iterations']=777
    changed['profile_before']=save(s.evidence/'different-profile.json',different)
    assert first!=dec.dsh_current_transaction_name(changed)


def test_initial_baseline_carrier_paths_and_JSON_YAML_format_cannot_reset_key(writer_case):
    s=writer_case; first=dec.dsh_current_transaction_name(s.b)
    changed=copy.deepcopy(s.b)
    for key,document in (('root_before',s.root),('profile_before',s.own)):
        p=s.evidence/(key+'-equivalent.json')
        p.write_text(json.dumps(document,indent=4,sort_keys=False)+'\n');p.chmod(0o600)
        changed[key]=pin(p)
        assert changed[key]['path']!=s.b[key]['path']
        assert changed[key]['sha256']!=s.b[key]['sha256']
        assert dec.dsh_current_transaction_name(changed)==first


@pytest.mark.parametrize('legacy',['empty-partial','consumed-intent','UNKNOWN-no-commit'])
def test_initial_semantic_once_preserves_legacy_raw_consumption(writer_case, legacy):
    s=writer_case; preparation=s.f.e.home/'preparation';preparation.mkdir(mode=0o700,exist_ok=True)
    raw=s.b['runtime_after']['current_availability']['declaration']['sha256']
    old=preparation/('ordinary-dsh-current-declaration-'+raw);old.mkdir(mode=0o700)
    if legacy!='empty-partial':
        request=request_for(s); ref=save(s.evidence/'legacy-request.json',request)
        ordinary.write(old/'intent.json',_encoded(intent(request,ref)))
    changed=copy.deepcopy(s.b)
    document=cur.read_json(changed['runtime_after']['current_availability']['declaration'])
    p=s.evidence/'other-D.json';p.write_text(json.dumps(document,indent=4)+'\n');p.chmod(0o600)
    changed['runtime_after']['current_availability']['declaration']=pin(p)
    with pytest.raises(REFUSED):dec.dsh_current_consumption_check(preparation,changed)
    assert old.exists() and (not (old/'completed.json').exists())


def test_valid_structural_native_commit_and_active_T2_join(committed_case):
    c=committed_case; f=c.s.f
    assert checked(c)==c.result
    p=make_proof(f);p['pending_transaction']=c.reference
    assert cur.validate_proof(f.c,f.d,p) is p
    activate_proof(f,p)
    assert cur.validate_current(f.c)['proof']==p


@pytest.mark.parametrize('damage',['missing-intent','missing-completed','foreign-sibling',
    'wrong-commit-request','wrong-afterimages','false-consumed','wrong-release-request',
    'wrong-release-clock','release-outside-original-clock','forged-staged-marker',
    'forged-staged-config','live-pending-drift','replaced-intent-inode-during-read'])
def test_commit_provenance_refusals(committed_case, damage, monkeypatch):
    c=committed_case
    if damage=='missing-intent':(c.tx/'intent.json').unlink()
    elif damage=='missing-completed':(c.tx/'completed.json').unlink()
    elif damage=='foreign-sibling':
        other=c.tx.with_name(c.tx.name+'-sibling');shutil.copytree(c.tx,other)
        c.reference=pin(other/'committed.json')
    elif damage in ('wrong-commit-request','wrong-afterimages','false-consumed'):
        v=cur.read_json(c.reference)
        if damage=='wrong-commit-request':v['request_sha256']='e'*64
        elif damage=='wrong-afterimages':v['after']['config.yaml']='e'*64
        else:v['original_attempt_consumed']=1
        c.reference=save(c.tx/'committed.json',v)
    elif damage in ('wrong-release-request','wrong-release-clock','release-outside-original-clock'):
        v=cur.read_json(pin(c.tx/'completed.json'))
        if damage=='wrong-release-request':v['request']['sha256']='e'*64
        elif damage=='wrong-release-clock':v['clock']['sha256']='e'*64
        else:v['completed_mono']=c.authority.clock['deadline_mono']+1
        save(c.tx/'completed.json',v)
    elif damage=='forged-staged-marker':
        p=c.tx/'stage'/str(c.s.f.h.relative_to(c.s.f.e.home))/'.friday-user-scope.json'
        v=json.loads(p.read_bytes());v['principal']='forged';save(p,v)
    elif damage=='forged-staged-config':
        p=c.tx/'stage'/'config.yaml';p.write_bytes(p.read_bytes()+b'forged: true\n')
    elif damage=='live-pending-drift':
        p=c.s.f.e.home/'config.yaml';p.write_bytes(p.read_bytes()+b'forged: true\n')
    else:
        original=writer._read_reference; changed=False
        def read(ref,**kw):
            nonlocal changed
            out=original(ref,**kw)
            if Path(ref['path'])==c.tx/'completed.json' and not changed:
                changed=True;p=c.tx/'intent.json';raw=p.read_bytes();p.unlink();p.write_bytes(raw);p.chmod(0o600)
            return out
        monkeypatch.setattr(writer,'_read_reference',read)
    with pytest.raises(REFUSED):checked(c)


def test_probe_clock_must_begin_after_successful_T1(committed_case):
    c=committed_case;v=cur.read_json(pin(c.tx/'completed.json'))
    with pytest.raises(REFUSED,match='precedes_t1_completion'):
        checked(c,observation_started_mono=v['completed_mono']-.001)


def test_failed_native_release_never_creates_completion(committed_case):
    c=committed_case;(c.tx/'completed.json').unlink()
    def refusal():raise RuntimeError('synthetic release refusal')
    c.authority.prove_released=refusal
    with pytest.raises(RuntimeError,match='release refusal'):
        writer._dsh_completed(c.authority,c.result,c.state,c.owned)
    assert (c.tx/'intent.json').exists() and (c.tx/'committed.json').exists()
    assert not (c.tx/'completed.json').exists()
    with pytest.raises(REFUSED):checked(c)


def test_bare_claim_never_admits_P(committed_case):
    c=committed_case;f=c.s.f;p=make_proof(f)
    p['pending_transaction']=save(f.root/'bare-claimed-commit.json',{
        'state':'WORKER_DECLARATIONS_REBOUND_CONSUMERS_STOPPED',
        'runtime_acceptance':'NOT_GRANTED','consumers_started':False,
        'dsh_current':copy.deepcopy(c.result['dsh_current'])})
    with pytest.raises(RuntimeError,match='pending_transaction_unverified'):
        cur.validate_proof(f.c,f.d,p)
