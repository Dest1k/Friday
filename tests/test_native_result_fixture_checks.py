"""Real normal native dispatch/outer hook and terminal, offline isolated only."""
from contextvars import Context, ContextVar
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import pytest
from test_host_native import isolated,setup,native,offline_boundary,CALL
from test_result_delivery import completed
from test_result_tool import enable_results
from hermes_constants import set_hermes_home_override,reset_hermes_home_override
from tools.terminal_scope import build_profile_terminal_scope,set_terminal_scope,reset_terminal_scope
from tools.registry import registry
import model_tools

C=Path(__file__).resolve().parents[1]
REAL_RUN=subprocess.run


def normal(setup,row,args,*,call=None,suppress=False):
    call=call or {**CALL,'tool_call_id':'fixture-check'}
    def bound():
        proof=row['host']['binding']['ingress'];owner=row['owner']
        values=dict(PLATFORM='telegram',CHAT_ID=owner['chat_id'],CHAT_TYPE=proof['chat_type'],
                    THREAD_ID=owner['thread_id'],USER_ID=owner['user_id'],KEY=owner['session_key'],
                    ID=call['session_id'],MESSAGE_ID=owner['message_id'],PROFILE=proof['source_profile'])
        for k,v in values.items():ContextVar('HERMES_SESSION_'+k).set(v)
        token=set_hermes_home_override(setup.home)
        scope_token=set_terminal_scope(build_profile_terminal_scope(setup.home))
        try:
            if suppress:
                with model_tools.suppress_post_tool_call_hook():
                    return json.loads(model_tools.handle_function_call('friday_result',args,**call))
            return json.loads(model_tools.handle_function_call('friday_result',args,**call))
        finally:
            reset_terminal_scope(scope_token);reset_hermes_home_override(token)
    return Context().run(bound)


async def prepare(setup,monkeypatch,fixture='coding_add',good=True):
    module,row,workspace=await completed(setup,monkeypatch)
    enable_results(setup)
    if fixture=='coding_add':
        (workspace/'calculator.py').write_bytes(b'def add(a, b):\n    return a + b\n' if good else (C/'fixtures/host-repair/input/calculator.py').read_bytes())
        paths=['calculator.py']
    else:
        (workspace/'settings.json').write_bytes((C/'fixtures/engineering-repair/calibration/settings.json').read_bytes())
        (workspace/'report.json').write_bytes((C/'fixtures/engineering-repair/calibration/report.json').read_bytes() if good else b'{"readings":[],"meters":[],"totals":{}}')
        paths=['settings.json','report.json']
    row=module.collect_outputs(setup.host.store,row,paths)
    goals=importlib.import_module(setup.module.__package__+'.goal_checks')
    import hermes_yaml as yaml
    config=yaml.safe_load((setup.home/'config.yaml').read_text())
    config['terminal']={'backend':'local','cwd':str(workspace),'shell_init_files':[],'auto_source_bashrc':False}
    (setup.home/'config.yaml').write_text(yaml.safe_dump(config))
    scope=build_profile_terminal_scope(setup.home)
    folder,pins,_=goals.FIXTURES[fixture]
    admission=dict(enabled=True,fixture=fixture,reference=row['existing_task_id'],owner_sha256=goals.digest(row['owner']),
                   task_sha256=goals.digest(row['host']['binding']),artifacts=row['result']['artifacts'],
                   pins={f'fixtures/{folder}/{p}':hashlib.sha256((C/f'fixtures/{folder}/{p}').read_bytes()).hexdigest() for p in pins},
                   terminal_scope_sha256=goals.digest(scope),shell_init_reviewed=True,source_root=str(C))
    config['plugins']['entries']['friday_rework']['settings']['fixture_check']=admission
    (setup.home/'config.yaml').write_text(yaml.safe_dump(config))
    # Only the already finished worker boundary was mocked. Terminal/checker is real.
    monkeypatch.setattr(subprocess,'run',REAL_RUN)
    import tools.terminal_tool
    return goals,row,admission,config


@pytest.mark.asyncio
@pytest.mark.parametrize('fixture',['coding_add','engineering_report'])
@pytest.mark.parametrize('good',[True,False])
async def test_real_native_finite_owner_pass_and_fail(setup,monkeypatch,fixture,good):
    goals,row,_,_=await prepare(setup,monkeypatch,fixture,good)
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']})
    assert response.get('accepted'),response
    current=setup.host.store.get(row['existing_task_id'],row['owner'])
    observed=current['result']['observations'][response['observation_reference']]
    assert observed['state']==('PASS' if good else 'FAIL'),(response,observed)
    assert observed['native']['raw']==response['native']
    # Only the real outer hook records this. One pre-existing fake worker launch.
    assert len(setup.boundary.launches)==1
    assessed=normal(setup,row,{'action':'assess','reference':row['existing_task_id'],
        'verdict':observed['state'],'rationale':'Exact immutable fixture owner tests through native terminal.',
        'observations':[response['observation_reference']]},call={**CALL,'tool_call_id':'fixture-assess'})
    assert assessed.get('assessment',{}).get('method')=='owner_fixture_execution',assessed
    assert assessed['goal_verification']==observed['state']
    tool=registry.get_entry('friday_result',scope=setup.manager.scope_key).handler.__self__
    assert not tool.checks.pending
    assert not normal(setup,row,{'action':'check','reference':row['existing_task_id']},call={**CALL,'tool_call_id':'new-attempt'})['accepted']


@pytest.mark.asyncio
async def test_missing_outer_hook_stays_unknown_and_cannot_replay(setup,monkeypatch):
    goals,row,_,_=await prepare(setup,monkeypatch)
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']},suppress=True)
    assert response.get('accepted'),response
    ref=response['observation_reference']
    assert setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'][ref]['state']=='UNKNOWN'
    assert not normal(setup,row,{'action':'check','reference':row['existing_task_id']},call={**CALL,'tool_call_id':'replay'})['accepted']
    assessed=normal(setup,row,{'action':'assess','reference':row['existing_task_id'],'verdict':'PASS','rationale':'Lost hook','observations':[ref]},call={**CALL,'tool_call_id':'false-pass'})
    assert not assessed['accepted']


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation',['disabled','task','owner','artifact','pin','scope','shell','arg','call'])
async def test_preexec_substitution_refuses_without_terminal(setup,monkeypatch,mutation):
    goals,row,admission,config=await prepare(setup,monkeypatch)
    args={'action':'check','reference':row['existing_task_id']};call={**CALL,'tool_call_id':'fixture-check'}
    if mutation=='disabled':admission['enabled']=False
    if mutation=='task':admission['task_sha256']='0'*64
    if mutation=='owner':admission['owner_sha256']='0'*64
    if mutation=='artifact':admission['artifacts']=[]
    if mutation=='pin':admission['pins'][next(iter(admission['pins']))]='0'*64
    if mutation=='scope':admission['terminal_scope_sha256']='0'*64
    if mutation=='shell':config['terminal']['auto_source_bashrc']=True
    if mutation=='arg':args['command']='true'
    if mutation=='call':call['task_id']='foreign'
    import hermes_yaml as yaml
    config['plugins']['entries']['friday_rework']['settings']['fixture_check']=admission
    (setup.home/'config.yaml').write_text(yaml.safe_dump(config))
    monkeypatch.setattr(setup.ctx,'dispatch_tool',lambda *a,**kw:pytest.fail('not admitted terminal ran'))
    assert not normal(setup,row,args,call=call)['accepted']
    assert not setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations']


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation',['yield','background','timeout','truncation','accepted_only','redacted'])
async def test_incomplete_native_outcome_never_passes(setup,monkeypatch,mutation):
    goals,row,_,_=await prepare(setup,monkeypatch)
    bad={'output':'','exit_code':0,'error':None}
    if mutation=='yield':bad.update(status='yielded_to_background',exit_code=None)
    if mutation=='background':bad['session_id']='background'
    if mutation=='timeout':bad['exit_code']=124
    if mutation=='truncation':bad['truncation_note']='lost'
    if mutation=='accepted_only':bad['output']=json.dumps({'accepted':True})
    if mutation=='redacted':bad['output']='[REDACTED]'
    monkeypatch.setattr(setup.ctx,'dispatch_tool',lambda *a,**kw:json.dumps(bad))
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']})
    assert response['accepted']
    observed=setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'][response['observation_reference']]
    assert observed['state']=='UNKNOWN'


@pytest.mark.asyncio
@pytest.mark.parametrize('change',['stop','unload','artifact'])
async def test_change_during_native_call_leaves_unknown(setup,monkeypatch,change):
    goals,row,_,_=await prepare(setup,monkeypatch)
    actual=setup.ctx.dispatch_tool
    def changing(*a,**kw):
        raw=actual(*a,**kw)
        if change=='unload':setup.host._closed=True
        elif change=='stop':
            setup.host.store.request_stop(row['existing_task_id'],row['owner'],'cancel')
        else:
            artifact=row['result']['artifacts'][0]
            (goals.output_root(row)/artifact['reference']).write_text('changed')
        return raw
    monkeypatch.setattr(setup.ctx,'dispatch_tool',changing)
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']})
    assert not response['accepted']
    observed=next(iter(setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'].values()))
    assert observed['state']=='UNKNOWN' and observed['native'] is None


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation',['call','args','result','status'])
async def test_foreign_or_forged_outer_hook_cannot_consume_pending(setup,monkeypatch,mutation):
    goals,row,_,_=await prepare(setup,monkeypatch)
    args={'action':'check','reference':row['existing_task_id']}
    response=normal(setup,row,args,suppress=True)
    assert response['accepted']
    tool=registry.get_entry('friday_result',scope=setup.manager.scope_key).handler.__self__
    ref=response['observation_reference'];pending=tool.checks.pending[ref]
    call=pending['call'].copy();hookargs=args.copy();raw=pending['response'];status='ok'
    if mutation=='call':call['turn_id']='foreign'
    if mutation=='args':hookargs['reference']='another'
    if mutation=='result':raw=json.dumps({'accepted':True,'native':'forged'})
    if mutation=='status':status='error'
    tool.checks.post_tool_call(tool_name='friday_result',args=hookargs,result=raw,status=status,**call)
    assert ref in tool.checks.pending
    assert setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'][ref]['native'] is None


@pytest.mark.asyncio
async def test_hook_persistence_error_stays_durably_unknown_no_replay(setup,monkeypatch):
    goals,row,_,_=await prepare(setup,monkeypatch)
    save=setup.host.store._save
    # Document layout is the existing store, not a new fixture ledger.
    def guarded(data):
        def contains(v):
            if isinstance(v,dict):
                if v.get('kind')=='fixture_execution' and v.get('native') is not None:return True
                return any(contains(x) for x in v.values())
            if isinstance(v,list):return any(contains(x) for x in v)
            return False
        if contains(data):raise OSError('injected proof barrier loss')
        return save(data)
    monkeypatch.setattr(setup.host.store,'_save',guarded)
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']})
    observed=setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'][response['observation_reference']]
    assert observed['native'] is None and observed['state']=='UNKNOWN'
    assert not normal(setup,row,{'action':'check','reference':row['existing_task_id']},call={**CALL,'tool_call_id':'retry-after-loss'})['accepted']


@pytest.mark.asyncio
async def test_real_plugin_unload_retired_hook_never_revives_reservation(setup,monkeypatch):
    goals,row,_,_=await prepare(setup,monkeypatch)
    response=normal(setup,row,{'action':'check','reference':row['existing_task_id']},suppress=True)
    tool=registry.get_entry('friday_result',scope=setup.manager.scope_key).handler.__self__
    pending=tool.checks.pending[response['observation_reference']]
    setup.manager.unload()
    assert setup.host._closed
    tool.checks.post_tool_call(tool_name='friday_result',args=pending['args'],result=pending['response'],status='ok',**pending['call'])
    observed=setup.host.store.get(row['existing_task_id'],row['owner'])['result']['observations'][response['observation_reference']]
    assert observed['state']=='UNKNOWN' and observed['native'] is None


@pytest.mark.asyncio
async def test_admitted_fixture_cannot_substitute_file_review_for_owner_execution(setup,monkeypatch):
    goals,row,_,_=await prepare(setup,monkeypatch)
    inspected=normal(setup,row,{'action':'inspect','reference':row['existing_task_id']},call={**CALL,'tool_call_id':'fixture-file-read'})
    assert inspected['accepted']
    response=normal(setup,row,{'action':'assess','reference':row['existing_task_id'],'verdict':'PASS',
        'rationale':'File looks good but no owner execution.', 'observations':[inspected['observation_reference']]},
        call={**CALL,'tool_call_id':'file-fallback'})
    assert not response['accepted']
    assert setup.host.store.get(row['existing_task_id'],row['owner'])['goal_verification']=='NOT_RUN'
