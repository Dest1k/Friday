"""Ordinary Hermes product admission/control; native transports are offline.

These checks exercise the actual plugin/state/DSH preparation and retained
filesystem bytes. They do not certify native worker, inference or live handoff.
"""
from dataclasses import asdict
import importlib
import json
from pathlib import Path
import subprocess

import pytest

from test_host_native import setup, isolated, native, offline_boundary, ingress, invoke, settle, control, CALL, ARGS
from test_result_delivery import completed


async def retained(setup, monkeypatch, paths=('answer.txt',)):
    module, row, workspace = await completed(setup, monkeypatch)
    if paths != ('answer.txt',):
        for path in paths:
            p = workspace / path
            p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            p.write_bytes(b'verified source bytes\n')
    row = module.collect_outputs(setup.host.store, row, list(paths))
    return module, row, workspace


def source_args(row, paths=None, **changes):
    return {**ARGS, 'goal_check': row['host']['binding']['brief']['goal_check'],
            'from_result': {'reference': row['existing_task_id'], 'paths': paths or row['result']['source_paths']}, **changes}


def second_native(setup, monkeypatch):
    """One unique synthetic native session/invocation per separate execution unit."""
    old_run = subprocess.run
    sup = importlib.import_module(setup.module.__package__ + '.supervision')
    class Supervisor:
        description = staticmethod(sup.NativeSupervisor.description)
        def observe(self, row):
            u = setup.boundary.units.get(row['supervisor']['unit'])
            active = bool(u and u['running'])
            invocation = (u or {}).get('inv', 'a'*32 if u else '')
            if row['native'] and invocation and row['native']['invocation_id'] != invocation:
                raise RuntimeError('foreign invocation')
            return sup.UnitObservation(row['supervisor']['unit'], invocation,
                'active' if active else 'inactive', 'running' if active else 'dead', 'success',
                42 if active else 0, '/offline/unit' if active else '', active, u is None)
        def stop(self, row):
            self.observe(row)
            setup.boundary.stops.append(row['supervisor']['unit'])
            if row['supervisor']['unit'] in setup.boundary.units:
                setup.boundary.units[row['supervisor']['unit']]['running'] = False
            return self.observe(row)
    def launch(argv, **kw):
        r = old_run(argv, **kw)
        unit = next(x.split('=', 1)[1] for x in argv if x.startswith('--unit='))
        row = next(v for v in setup.host.store.snapshot().values() if v['supervisor']['unit'] == unit)
        inv = row['existing_task_id'][7:39]
        setup.boundary.units[unit]['inv'] = inv
        control = Path(row['workspace_reference']) / '.dsh-adapter'
        events = [json.loads(x) for x in (control/'events.ndjson').read_text().splitlines()]
        events[0]['sessionId'] = 'session-' + inv[:8] + '-' + inv[8:12] + '-' + inv[12:16] + '-' + inv[16:20] + '-' + inv[20:32]
        (control/'events.ndjson').write_text(''.join(json.dumps(x)+'\n' for x in events))
        if (control/'terminal.json').exists():
            t=json.loads((control/'terminal.json').read_text());t['INVOCATION_ID']=inv
            (control/'terminal.json').write_text(json.dumps(t))
        return subprocess.CompletedProcess(argv, r.returncode, r.stdout, ('invocation ID: '+inv+'\n').encode())
    monkeypatch.setattr(subprocess, 'run', launch)
    monkeypatch.setattr(setup.module, 'NativeSupervisor', Supervisor)
    monkeypatch.setattr(sup, 'NativeSupervisor', Supervisor)
    hr = importlib.import_module(setup.module.__package__+'.host_runtime')
    monkeypatch.setattr(hr, 'NativeSupervisor', Supervisor)


@pytest.mark.asyncio
async def test_ordinary_continuation_inherits_original_grant_and_materializes_cold_tree(setup, monkeypatch):
    module, parent, workspace = await retained(setup, monkeypatch, ('src/main.py','README.md'))
    original = {k: parent[k] for k in ('created_at_unix','budget_seconds','deadline_unix')}
    setup.host.store.clock = lambda: parent['created_at_unix'] + 20
    second_native(setup, monkeypatch)
    call = {**CALL, 'tool_call_id': 'continuation-1'}
    accepted = invoke(setup, parent['host']['binding']['ingress'], call=call, args=source_args(parent))
    assert accepted['accepted'], accepted
    child = setup.host.store.snapshot()[accepted['reference']]
    assert all(child[k] == v for k,v in original.items())
    assert child['host']['acceptance'] == parent['host']['acceptance']
    assert child['host']['continuation']['mode'] == 'cold_retained_artifacts'
    assert child['workspace_reference'] != parent['workspace_reference']
    assert len(child['host']['inputs']) == 2
    assert all('#result:' in v['receipt_reference'] for v in child['host']['inputs'])
    # A duplicate before start grants no second schedule, copy or budget.
    assert invoke(setup,parent['host']['binding']['ingress'],call=call,args=source_args(parent))['reference'] == child['existing_task_id']
    await settle(setup)
    child = setup.host.store.get(child['existing_task_id'],child['owner'])
    assert child['host']['quiescence'] is not None, child
    root = Path(child['workspace_reference'])/'workspace'
    assert (root/'src/main.py').read_bytes() == b'verified source bytes\n'
    assert (root/'README.md').read_bytes() == b'verified source bytes\n'
    assert not (root/'.git').exists()
    assert child['native']['worker_reference'] != parent['native']['worker_reference']
    assert len(setup.boundary.launches) == 2
    assert setup.host.store.current_stage(parent['existing_task_id'],parent['owner'])['existing_task_id'] == child['existing_task_id']
    assert all((workspace / p).read_bytes() == b'verified source bytes\n' for p in ('src/main.py','README.md'))
    assert not invoke(setup,parent['host']['binding']['ingress'],call={**call,'tool_call_id':'branch'},args=source_args(parent))['accepted']


@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['cancel','pause','expired','elapsed','legacy_clock','unknown_source','changed_goal','unquiet','pending_unknown'])
async def test_no_continuation_from_stopped_unknown_unquiet_or_renewed_grant(setup, monkeypatch, kind):
    module, row, _ = await retained(setup, monkeypatch)
    args = source_args(row)
    if kind in ('cancel','pause'):
        setup.host.store.request_stop(row['existing_task_id'],row['owner'],kind)
    elif kind == 'expired': setup.host.store.clock=lambda:row['deadline_unix']
    elif kind == 'elapsed':
        setup.host.store.observe(row['existing_task_id'],row['owner'],native=row['native'],evidence_reference=row['execution_observation'],elapsed_seconds=row['budget_seconds'])
    elif kind == 'legacy_clock':
        with setup.host.store._locked() as data:
            data['jobs'][row['existing_task_id']]['host'].pop('acceptance')
            setup.host.store._save(data)
    elif kind == 'unknown_source': args['from_result']['paths']=['not-retained.py']
    elif kind == 'changed_goal': args['goal_check']='new broad goal'
    elif kind in ('unquiet','pending_unknown'):
        # Safe current pending row of another ingress reserves capacity; it
        # cannot be mistaken for the quiet retained predecessor.
        with setup.host.store._locked() as data:
            p=data['jobs'][row['existing_task_id']]
            p.pop('result');p['goal_verification']=p['delivery']='NOT_RUN'
            p['host']['quiescence']=p['host']['terminal']=None
            if kind == 'pending_unknown':
                p['native']=None;p['execution_observation']=None;p['elapsed_seconds']=0;p['submission_observation']='UNKNOWN'
            setup.host.store._save(data)
    before = len(setup.host.store.snapshot())
    result=invoke(setup,row['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=args)
    assert not result['accepted'], result
    assert len(setup.boundary.launches)==1 and len(setup.host.store.snapshot())==before


@pytest.mark.asyncio
@pytest.mark.parametrize('path',['../owner/file','/home/owner/repo','src/.env','.git/hooks/post-checkout','auth.json','credentials.json','a/../b','a//b','a\\b'])
async def test_model_cannot_nominate_host_paths_credentials_or_hooks(setup, monkeypatch,path):
    _,row,_=await retained(setup,monkeypatch)
    result=invoke(setup,row['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(row,[path]))
    assert not result['accepted'] and len(setup.host.store.snapshot())==1


@pytest.mark.asyncio
async def test_changed_retained_bytes_reserve_no_replayable_execution(setup, monkeypatch):
    module,row,_=await retained(setup,monkeypatch)
    artifact=row['result']['artifacts'][0]
    p=module.output_root(row)/artifact['reference'];p.chmod(0o600);p.write_bytes(b'changed retained bytes');p.chmod(0o400)
    call={**CALL,'tool_call_id':'continuation'};args=source_args(row)
    result=invoke(setup,row['host']['binding']['ingress'],call=call,args=args)
    assert not result['accepted'] and len(setup.boundary.launches)==1
    rows=setup.host.store.snapshot(); child=rows[result['reference']]
    assert child['host']['inputs'] is None and child['submission_observation']=='NOT_SUBMITTED'
    again=invoke(setup,row['host']['binding']['ingress'],call=call,args=args)
    assert again['reference']==child['existing_task_id'] and len(setup.boundary.launches)==1
    assert not invoke(setup,row['host']['binding']['ingress'],call={**call,'tool_call_id':'branch'},args=args)['accepted']


@pytest.mark.asyncio
async def test_root_stop_reaches_current_writer_and_propagates_terminal_intent(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch)
    second_native(setup,monkeypatch);setup.boundary.completed=False;setup.started.clear()
    r=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    assert r['accepted']
    import asyncio
    assert await asyncio.to_thread(setup.started.wait, 2)
    child=setup.host.store.snapshot()[r['reference']]
    assert child['host']['quiescence'] is None
    response = await control(setup, 'stop', parent['existing_task_id'])
    assert response['accepted'] and response['quiescent'], response
    rows=setup.host.store.snapshot()
    assert rows[parent['existing_task_id']]['stop_intent']==rows[child['existing_task_id']]['stop_intent']=='cancel'
    assert child['supervisor']['unit'] in setup.boundary.stops
    assert len(setup.boundary.launches)==2
    await settle(setup)


@pytest.mark.asyncio
@pytest.mark.parametrize('field',['user_id','chat_id','thread_id','session_key','session_id','bot_id','profile'])
async def test_retained_chain_rejects_foreign_owner_at_atomic_claim(setup,monkeypatch,field):
    _,parent,_=await retained(setup,monkeypatch)
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    briefmod=importlib.import_module(setup.module.__package__+'.boundary')
    brief=briefmod.parse_brief(source_args(parent));owner={**parent['owner'],field:'foreign'}
    with setup.host.store._locked() as data:
        with pytest.raises(RuntimeError):
            mod.admit(data['jobs'],parent['existing_task_id'],owner,brief,parent['host']['binding'],setup.host.store.clock())
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
@pytest.mark.parametrize('worker_map',[False,True])
async def test_dsh_to_a0_to_dsh_cold_handoff_uses_actual_native_input_and_cwd_interfaces(setup, monkeypatch, tmp_path,worker_map):
    import test_a0_host as a0_fixture
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    module,parent,_=await retained(setup,monkeypatch,('src/main.py','README.md'))
    call={**CALL,'tool_call_id':'a0-continuation'}
    # Configure actual A0 route. Only its Docker/systemd/API boundaries are fake.
    monkeypatch.setattr(a0_fixture,'CALL',call)
    state=a0_fixture.configure_a0(setup,parent['host']['binding']['ingress'],tmp_path,monkeypatch,separate_roots=worker_map)
    if worker_map:
        configured={'enabled':True,'workers':{'dsh':setup.runtime,'a0':state.runtime}}
        setup.configure(configured)
    args=source_args(parent,worker='a0')
    result=invoke(setup,parent['host']['binding']['ingress'],call=call,args=args)
    assert result['accepted'],result
    row=setup.host.store.snapshot()[result['reference']]
    assert row['created_at_unix']==parent['created_at_unix'] and row['deadline_unix']==parent['deadline_unix']
    assert row['host']['a0']['acceptance']==parent['host']['acceptance']
    (setup.home/'.env').write_text('OFFLINE_DSH_KEY=offline-profile-value\nFRIDAY_LLM_API_KEY=offline-fixture-key-one\nFRIDAY_EMBEDDINGS_API_KEY=offline-fixture-key-two\n')
    from agent.secret_scope import set_secret_scope, reset_secret_scope
    secret_token=set_secret_scope({'FRIDAY_LLM_API_KEY':'offline-fixture-key-one','FRIDAY_EMBEDDINGS_API_KEY':'offline-fixture-key-two'},profile_home=str(setup.home))
    token=set_hermes_home_override(setup.home)
    try:
        setup.host.attach_a0_capability(row['existing_task_id'],row['owner'],state.produce(row))
        await settle(setup)
    finally:
        reset_hermes_home_override(token);reset_secret_scope(secret_token)
    row=setup.host.store.snapshot()[row['existing_task_id']]
    assert row['host']['terminal']['state']=='completed' and row['host']['quiescence']['kind']=='a0'
    cont=importlib.import_module(setup.module.__package__+'.continuation')
    root=state.session.boundary.config.state_dir.parent/cont.a0_seed_root(row).removeprefix('/a0/')
    assert (root/'src/main.py').read_bytes()==b'verified source bytes\n'
    assert (root/'README.md').read_bytes()==b'verified source bytes\n'
    assert len(state.posts)==2 and cont.a0_seed_root(row) in state.posts[-1]['message']
    assert not state.running and row['host']['a0']['key_cleanup']=='REMOVED'
    row=module.collect_outputs(setup.host.store,row,['report.txt','diagnosis.txt'])
    # In the joined profile, selection changes without replacing configuration.
    if not worker_map:setup.configure(setup.runtime)
    second_native(setup,monkeypatch)
    # Restore the synthetic DSH launch seam from the first route (a0 fixture
    # uses its explicit command callback instead of subprocess.run).
    returned=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'dsh-return'},args=source_args(row))
    assert returned['accepted'],returned
    await settle(setup)
    final=setup.host.store.snapshot()[returned['reference']]
    assert final['host']['quiescence'] is not None
    assert final['created_at_unix']==parent['created_at_unix'] and final['deadline_unix']==parent['deadline_unix']
    assert final['host']['continuation']['root']==parent['existing_task_id']
    assert (Path(final['workspace_reference'])/'workspace/report.txt').read_bytes()==b'actual retained fixture bytes\n'
    assert len(setup.host.store.snapshot())==3
    assert len(setup.boundary.launches)==2
    if worker_map:
        assert setup.ctx.get_config('runtime')==configured
        assert final['host']['binding']['runtime']==setup.runtime
        assert row['host']['binding']['runtime']==state.runtime
    state.capture()


@pytest.mark.asyncio
async def test_historical_quiet_flag_cannot_hide_a_reappearing_native_writer(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch)
    setup.boundary.units[parent['supervisor']['unit']]['running']=True
    result=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    assert not result['accepted'] and len(setup.host.store.snapshot())==1
    assert len(setup.boundary.launches)==1
    setup.boundary.units[parent['supervisor']['unit']]['running']=False


@pytest.mark.asyncio
async def test_original_monotonic_budget_survives_wall_clock_rollback(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch)
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    import time
    now=parent['created_at_unix']+1
    monkeypatch.setattr(time,'monotonic_ns',lambda:parent['host']['acceptance']['accepted_monotonic_ns']+61_000_000_000)
    assert mod.remaining(parent,now)<=0


@pytest.mark.asyncio
@pytest.mark.parametrize('field',['acceptance','source_sha256','original_ingress','paths','root','predecessor','input_sha256','input_origin'])
async def test_corrupt_chain_or_input_provenance_refuses_every_read_and_submission(setup,monkeypatch,field):
    _,parent,_=await retained(setup,monkeypatch)
    setup.native.runner._draining=True
    result=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    assert not result['accepted'] and result.get('reference') # schedule refused after durable reservation
    child=setup.host.store.snapshot()[result['reference']]
    from copy import deepcopy
    key=importlib.import_module(setup.module.__package__+'.associations').KEY
    data=setup.ctx.state.get(key);broken=deepcopy(data);r=broken['jobs'][child['existing_task_id']]
    if field=='acceptance':r['host']['acceptance']['accepted_monotonic_ns']+=1
    elif field=='original_ingress':r['host']['continuation'][field]['message']['message_id']='other-message'
    elif field=='paths':r['host']['continuation'][field]=['different.py']
    elif field=='input_sha256':r['host']['inputs'][0]['sha256']='f'*64
    elif field=='input_origin':r['host']['inputs'][0]['receipt_reference']=r['host']['inputs'][0]['receipt_reference'].split('#result:')[0]+'#result:'+'f'*32+'.txt'
    else:r['host']['continuation'][field]='native-'+'f'*64 if field in ('root','predecessor') else 'f'*64
    setup.ctx.state.set(key,broken)
    try:
        with pytest.raises(RuntimeError):setup.host.store.snapshot()
        with pytest.raises(RuntimeError):setup.host.store.begin_submission(child['existing_task_id'],child['owner'])
    finally:setup.ctx.state.set(key,data)
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
async def test_changed_workspace_seed_refuses_before_native_launch(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch)
    setup.native.runner._draining=True
    result=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    child=setup.host.store.snapshot()[result['reference']]
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    from dataclasses import asdict
    contract=importlib.import_module(setup.module.__package__+'.adapters.contract')
    briefmod=importlib.import_module(setup.module.__package__+'.boundary')
    inputs=tuple(contract.VerifiedInput(**v) for v in child['host']['inputs'])
    mod.seed_workspace(child,inputs)
    (Path(child['workspace_reference'])/'workspace/answer.txt').write_bytes(b'foreign changed bytes')
    with pytest.raises(RuntimeError):setup.host._controller(child).prepare(child['existing_task_id'],child['owner'],briefmod.parse_brief(child['host']['binding']['brief']),inputs)
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
async def test_stop_of_root_after_store_damage_uses_checked_current_writer(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch)
    second_native(setup,monkeypatch);setup.boundary.completed=False;setup.started.clear()
    result=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    import asyncio
    assert await asyncio.to_thread(setup.started.wait,2)
    child=setup.host.store.snapshot()[result['reference']]
    # Corrupt durable reads while retaining exact cached ownership; no ACK or
    # writer release is claimed while the association store is damaged.
    state_get=setup.host.store.state_get
    monkeypatch.setattr(setup.host.store,'state_get',lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('offline damaged store')))
    response=await control(setup,'stop',parent['existing_task_id'])
    assert not response['accepted']
    assert child['supervisor']['unit'] in setup.boundary.stops
    monkeypatch.setattr(setup.host.store,'state_get',state_get)
    setup.host._stop(child,'cancel')
    await settle(setup)
    assert len(setup.boundary.launches)==2


@pytest.mark.asyncio
@pytest.mark.parametrize('extra',['.git/hooks/post-checkout','unexpected.py','src/link'])
async def test_seed_tree_extras_or_links_refuse_before_native_submission(setup,monkeypatch,extra):
    _,parent,_=await retained(setup,monkeypatch,('src/main.py',))
    setup.native.runner._draining=True
    r=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    child=setup.host.store.snapshot()[r['reference']]
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    contract=importlib.import_module(setup.module.__package__+'.adapters.contract')
    inputs=tuple(contract.VerifiedInput(**v) for v in child['host']['inputs'])
    mod.seed_workspace(child,inputs)
    root=Path(child['workspace_reference'])/'workspace';path=root/extra
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if extra.endswith('link'):path.symlink_to(root/'src/main.py')
    else:path.write_bytes(b'ungranted data')
    with pytest.raises(RuntimeError):mod.verify_seed(root,child,inputs)
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
async def test_symlink_injected_during_materialization_cannot_write_outside_seed(setup,monkeypatch):
    _,parent,_=await retained(setup,monkeypatch,('src/main.py',))
    setup.native.runner._draining=True
    r=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'continuation'},args=source_args(parent))
    child=setup.host.store.snapshot()[r['reference']]
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    contract=importlib.import_module(setup.module.__package__+'.adapters.contract')
    inputs=tuple(contract.VerifiedInput(**v) for v in child['host']['inputs'])
    root=Path(child['workspace_reference'])/'workspace'
    import os
    original=os.mkdir
    def inject(path,*a,**kw):
        value=original(path,*a,**kw)
        if path=='workspace' and kw.get('dir_fd') is not None:
            (root/'src').symlink_to(setup.cache,target_is_directory=True)
        return value
    monkeypatch.setattr(os,'mkdir',inject)
    with pytest.raises((RuntimeError,OSError)):mod.seed_workspace(child,inputs)
    assert not (setup.cache/'main.py').exists()
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
@pytest.mark.parametrize('intent',['pause','cancel'])
async def test_admin_stop_after_completion_retains_intent_and_denies_continuation(setup,monkeypatch,intent):
    from hermes_constants import set_hermes_home_override,reset_hermes_home_override
    _,parent,_=await retained(setup,monkeypatch)
    token=set_hermes_home_override(setup.home)
    try:
        before=setup.host.admin_control('default',parent['existing_task_id'],'status',lambda:None)
        assert before['stop_intent'] is None
        stopped=setup.host.admin_control('default',parent['existing_task_id'],intent,lambda:None)
        assert stopped['accepted'] and stopped['quiescent'] and stopped['stop_intent']==intent
        if intent=='cancel':
            assert setup.host.admin_control('default',parent['existing_task_id'],'pause',lambda:None)['stop_intent']=='cancel'
    finally:reset_hermes_home_override(token)
    row=setup.host.store.get(parent['existing_task_id'],parent['owner'])
    assert row['host']['terminal']==parent['host']['terminal'] and row['result']==parent['result']
    refused=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'after-stop'},args=source_args(parent))
    assert not refused['accepted'] and len(setup.host.store.snapshot())==1
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
@pytest.mark.parametrize('worker',['dsh','a0'])
async def test_runtime_receipt_requires_exact_continuation_helper(setup,monkeypatch,tmp_path,worker):
    from hermes_constants import set_hermes_home_override,reset_hermes_home_override
    runtime=setup.runtime
    if worker=='a0':
        from test_a0_host import configure_a0
        proof=await ingress(setup)
        runtime=configure_a0(setup,proof,tmp_path,monkeypatch).runtime
    hr=importlib.import_module(setup.module.__package__+'.host_runtime')
    token=set_hermes_home_override(setup.home)
    try:
        assert hr.check_runtime(runtime,setup.host.store)==runtime
        source=Path(hr.__file__).with_name('continuation.py')
        source.write_bytes(source.read_bytes()+b'\n# synthetic source drift\n')
        with pytest.raises(RuntimeError):hr.check_runtime(runtime,setup.host.store)
    finally:reset_hermes_home_override(token)
    assert not setup.boundary.launches


@pytest.mark.asyncio
async def test_seed_creation_stays_on_open_parent_when_path_is_replaced(setup,monkeypatch):
    import os
    _,parent,_=await retained(setup,monkeypatch,('src/main.py',))
    setup.native.runner._draining=True
    accepted=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'bound-directory'},args=source_args(parent))
    row=setup.host.store.snapshot()[accepted['reference']]
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    contract=importlib.import_module(setup.module.__package__+'.adapters.contract')
    inputs=tuple(contract.VerifiedInput(**v) for v in row['host']['inputs'])
    root=Path(row['workspace_reference'])/'workspace'
    parked=root.parent.with_name(root.parent.name+'-retained')
    original=os.mkdir
    changed=[]
    def replace_parent(name,*args,**kwargs):
        if name=='workspace' and kwargs.get('dir_fd') is not None and not changed:
            root.parent.rename(parked);root.parent.symlink_to(setup.cache,target_is_directory=True);changed.append(True)
        return original(name,*args,**kwargs)
    monkeypatch.setattr(os,'mkdir',replace_parent)
    mod.seed_workspace(row,inputs)
    assert changed and not (setup.cache/'workspace').exists()
    assert (parked/'workspace/src/main.py').read_bytes()==b'verified source bytes\n'
    with pytest.raises((RuntimeError,OSError)):mod.verify_seed(root,row,inputs)
    root.parent.unlink();parked.rename(root.parent)
    assert len(setup.boundary.launches)==1


@pytest.mark.asyncio
@pytest.mark.parametrize('component',['workdir','job','seed'])
async def test_a0_seed_walk_refuses_linked_components_from_trusted_anchor(setup,monkeypatch,tmp_path,component):
    _,parent,_=await retained(setup,monkeypatch,('src/main.py',))
    setup.native.runner._draining=True
    accepted=invoke(setup,parent['host']['binding']['ingress'],call={**CALL,'tool_call_id':'anchored-seed'},args=source_args(parent))
    row=setup.host.store.snapshot()[accepted['reference']]
    mod=importlib.import_module(setup.module.__package__+'.continuation')
    contract=importlib.import_module(setup.module.__package__+'.adapters.contract')
    inputs=tuple(contract.VerifiedInput(**v) for v in row['host']['inputs'])
    anchor=tmp_path/'owned-state';anchor.mkdir(mode=0o700)
    parts=['workdir','job','seed'];target=anchor
    for name in parts:
        target=target/name
        if name==component:
            target.symlink_to(setup.cache,target_is_directory=True);break
        target.mkdir(mode=0o700)
    before=sorted(setup.cache.rglob('*'))
    with pytest.raises((RuntimeError,OSError)):
        mod.materialize(anchor/'workdir/job/seed',row,inputs,anchor=anchor)
    assert sorted(setup.cache.rglob('*'))==before
    assert len(setup.boundary.launches)==1
