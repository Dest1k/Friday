"""SOURCE/OFFLINE typed plans and real native reseal/publication consumers.

No StoppedOperator authority is faked. These exercise the construction and
owned-inode transaction seams; full native stopped apply remains a separate gate.
"""
import copy
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_dsh_current_availability import candidate, env, make_proof, reseal, save
from test_user_worker_provision import inputs
from test_user_onboarding import row
from test_product_profile import inputs as product_inputs
from friday_admin_controls import worker_declarations as dec
from friday_admin_controls import worker_declaration_writer as writer
from friday_admin_controls import dsh_current_availability as cur
from friday_admin_controls import onboarding
from friday_admin_controls.stopped_operator import StoppedOperator, selected_native_profile
from friday_admin_controls.adapters.a0_profile import legacy_profile, endpoint_urls
from hermes_cli import friday_user_scope as users
from hermes_cli.config import require_readable_config_before_write, atomic_config_write, atomic_config_replace, fast_safe_load
from hermes_cli.config_effective import _effective
from hermes_cli.friday_ordinary_gateway import normalized_configuration
from scripts import friday_install as native
from scripts import friday_ordinary_install as ordinary
from scripts.install_containment import Budget
from tools.configure_product import compose_product

REFUSED = (ValueError, RuntimeError, PermissionError, OSError, KeyError)


def pin(path):
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def get(value,path):
    for key in path:value=value[key]
    return value


def runtime(config):
    return get(config,dec.profile_dsh_path(config))


def replace_runtime_fixture(f,value):
    """Set up an explicit signed baseline; never a product apply shortcut."""
    cfg=require_readable_config_before_write(f.h/'config.yaml')
    cfg['plugins']['entries']['friday_rework']['settings']['runtime']=copy.deepcopy(value)
    prepared=onboarding.prepare_admin_config_edit(f.h,cfg)
    with users.authority(f.h):atomic_config_replace(f.h/'config.yaml',cfg)
    onboarding.finish_admin_config_edit(f.h,prepared)


def snapshot(home):
    return {str(p.relative_to(home)):p.read_bytes() for p in home.rglob('*') if p.is_file()
        and not p.name.endswith(('.lock','.backup'))}


def identity(f,root,own,evidence):
    binding=f.native['binding']
    value={'schema':'frw.current-dest-worker-identity.v1','binding':binding,
        'binding_sha256':dec.fingerprint(binding),'enabled':True,
        'generation':f.native['generation'],
        'principal':hashlib.sha256(json.dumps([binding[k] for k in dec.IDENTITY_FIELDS],
            ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
        'profile':str(f.h),'profile_template':json.loads((f.h/users.ONBOARDING).read_bytes())['template'],
        'worker_attach_template':'friday-local','authority':'STATIC_SOURCE_JOIN_ONLY',
        'source_refs':{'root_configuration':pin(f.e.home/'config.yaml'),
            'configuration':pin(f.h/'config.yaml'),'onboarding':pin(f.h/users.ONBOARDING),
            'user_marker':pin(f.h/users.MARKER),'access_state':pin(f.e.state.data_dir/'state.json'),
            'stale_attachment':{'path':str(f.h/'workers/attachment.json'),'sha256':'a'*64}}}
    return value,save(evidence/'identity.json',value)


def bundle(f,root,own,incoming,evidence,*,stage=dec.DSH_CURRENT_DECLARATION_SCHEMA,after=None):
    ident,ident_ref=identity(f,root,own,evidence)
    input_ref=save(evidence/'worker-inputs.json',incoming)
    value={'schema':stage,'state':'PROPOSED_NOT_APPLIED_NOT_AN_EXECUTABLE_MIGRATION_REQUEST',
        'root_before':ident['source_refs']['root_configuration'],
        'profile_before':ident['source_refs']['configuration'],'identity_reference':ident_ref,
        'changes':[{'document':'root_config','path':list(dec.TEMPLATE_INPUTS),
            'before_sha256':dec.fingerprint(get(root,dec.TEMPLATE_INPUTS)),
            'after_reference':input_ref}],
        'runtime_after':copy.deepcopy(f.c if after is None else after)}
    if stage == dec.DSH_CURRENT_DECLARATION_SCHEMA and 'current_availability' in runtime(own):
        value['refresh_context']=cur.identity()
    source={'bundle':save(evidence/'bundle.json',value),'worker_inputs':input_ref,'identity':ident_ref}
    return value,ident,source


def build_writer_case(f,tmp_path):
    before=copy.deepcopy(f.c);before.pop('current_availability')
    old,_=inputs(f.e)
    before['dsh']['web']['egress_evidence']=old['dsh']['web']['egress_evidence']
    baseline=require_readable_config_before_write(f.h/'config.yaml')
    baseline['plugins']['entries']['friday_rework']['settings']['runtime']=before
    prepared=onboarding.prepare_admin_config_edit(f.h,baseline)
    # Fixture setup deliberately restores a pre-T1 configuration. The real
    # writer itself only adds declaration/proof fields and never uses replace.
    with users.authority(f.h):atomic_config_replace(f.h/'config.yaml',baseline)
    onboarding.finish_admin_config_edit(f.h,prepared)
    own=require_readable_config_before_write(f.h/'config.yaml')
    root=require_readable_config_before_write(f.e.home/'config.yaml')
    spec=product_inputs();spec['inference'].update(model=own['model']['default'],key_env='LOCAL_KEY',max_input=24576)
    spec['dashboard']['operator']={'provider':'basic','user_id':'owner','org_id':''}
    product=compose_product(spec)
    for key,value in product['config'].items():
        if key not in ('plugins','gateway'):root[key]=copy.deepcopy(value)
    for key,value in product['config']['gateway'].items():root['gateway'].setdefault(key,copy.deepcopy(value))
    settings=get(root,dec.SETTINGS);settings['runtime']={'enabled':False}
    after_inputs={'required':['dsh','a0'],'workers':{},'source_scope':{'home':str(f.e.home),'profile':'default'}}
    for key in ('budget_seconds','max_file_bytes','max_total_bytes','dsh'):
        after_inputs['workers'].setdefault('dsh',{})[key]=copy.deepcopy(f.c[key])
    after_inputs['workers']['dsh']['dsh'].pop('patch')
    a,_=inputs(f.e,worker='a0');a['a0']['deployment']=legacy_profile()
    after_inputs['workers']['a0']={key:copy.deepcopy(a[key]) for key in ('budget_seconds','max_file_bytes','max_total_bytes','a0')}
    after_inputs['a0_network']={'name':'synthetic-stopped','endpoints':list(endpoint_urls(a['a0']['deployment'])),'policy':a['a0']['policy']}
    before_inputs=copy.deepcopy(after_inputs)
    before_inputs['workers']['dsh']['dsh']['web']['egress_evidence']=before['dsh']['web']['egress_evidence']
    # Global declarations stay scoped to their original source home/profile;
    # own-profile maintenance never replaces that policy with the private Q.
    after_inputs=copy.deepcopy(before_inputs)
    template=copy.deepcopy(f.e.template);template['worker_inputs']=before_inputs
    settings['onboarding']['templates']['friday-local']=template
    with users.authority(f.e.home):atomic_config_write(f.e.home/'config.yaml',root)
    root=fast_safe_load((f.e.home/'config.yaml').read_text())
    evidence=tmp_path/'evidence';evidence.mkdir(mode=0o700)
    b,i,source=bundle(f,root,own,after_inputs,evidence)
    plan=dec.plan_declaration_delta(root,own,after_inputs,i,b)
    input_ref=save(evidence/'same-install-input.json',{'home':str(f.e.home),'product':{'runtime':{'enabled':False}}})
    contract=product['contract'];contract['native_dashboard']['operator']={'provider':'basic','user_id':'owner','org_id':''}
    contract_ref=save(f.e.home/'FRIDAY-PROFILE.json',contract)
    marker={'schema':native.SCHEMA,'home':str(f.e.home),'input_sha256':input_ref['sha256'],
        'profile_files':{'config.yaml':pin(f.e.home/'config.yaml')['sha256'],'FRIDAY-PROFILE.json':contract_ref['sha256']},
        'ordinary_gateway':{'configuration_sha256':normalized_configuration(_effective(root)),
            'operator_entry':{'input':input_ref,'script':{'path':str(evidence/'not-executed.py'),'sha256':'a'*64}},
            'history':{'closed_original':'UNCHANGED'},'credential_files':{'unchanged':True}},
        'original_attempt':{'old_clock_preserved':True}}
    save(f.e.home/native.MARKER,marker)
    prefix=str(f.h.relative_to(f.e.home))+'/'
    names=['config.yaml',prefix+'config.yaml',prefix+users.ONBOARDING,prefix+users.MARKER,native.MARKER]
    view=SimpleNamespace(home=f.e.home,profile_home=f.h,previous=json.loads(Path(input_ref['path']).read_bytes()),
        current=json.loads(Path(input_ref['path']).read_bytes()),marker=marker,binding=f.native['binding'],
        row=copy.deepcopy(row(f.e)),proof=json.loads((f.h/users.ONBOARDING).read_bytes()),
        request={'schema':dec.DSH_CURRENT_APPLY_SCHEMA,'declaration_source':source,
            'current_input':input_ref,'launcher_source':a['a0']['launcher'],
            'clock':f.c['current_availability']['cycle']},
        before={n:ordinary.update_file_state(f.e.home/n) for n in names})
    stage=evidence/'stage';stage.mkdir(mode=0o700)
    result=SimpleNamespace(f=f,root=root,own=own,inputs=after_inputs,b=b,i=i,source=source,
        plan=plan,view=view,stage=stage,evidence=evidence,names=names,
        before=snapshot(f.e.home),generation=row(f.e)['generation'])
    f._writer_case=result
    return result


@pytest.fixture
def writer_case(candidate,tmp_path):
    return build_writer_case(candidate,tmp_path)


def publish(s,outputs,count=5):
    owned={}
    with ordinary.SourceUpdateDirectories(s.f.e.home,s.names,[]) as directories:
        for name in s.names[:count]:
            ordinary.publish_update_file(s.f.e.home/name,outputs[name]['data'],0o600,
                s.view.before[name],owned,name,parent_fd=directories.parent_fd(name))
        return owned,directories


def test_t1_actual_plan_native_resealer_and_current_scope_keep_generation(writer_case):
    s=writer_case
    assert writer._planned_delta(s.view)==s.plan
    outputs=writer.prepare_afterimages(s.view,s.plan,s.stage)
    assert snapshot(s.f.e.home)==s.before
    assert set(outputs)==set(s.names)
    publish(s,outputs)
    own=require_readable_config_before_write(s.f.h/'config.yaml')
    assert runtime(own)==s.f.c
    assert row(s.f.e)['generation']==s.generation
    with users.authority(s.f.e.home):users.check_onboarding_home(s.f.e.home,s.f.h,s.f.native['binding'])
    native_scope=s.f.native
    principal=tuple(native_scope['binding'][k] for k in dec.IDENTITY_FIELDS)
    with users.authority(s.f.h):
        users.UserScope(s.f.e.home,s.f.h,s.f.h.name,principal,native_scope['binding'],
            tuple(native_scope['directory_identity']),s.generation).check()
    assert cur.validate_current(runtime(own),allow_pending=True)['proof'] is None
    assert pin(Path(s.f.c['runtime_receipt']['path']))==s.f.c['runtime_receipt']
    now=snapshot(s.f.e.home)
    assert {n:v for n,v in now.items() if n not in s.names}=={n:v for n,v in s.before.items() if n not in s.names}


@pytest.mark.parametrize('damage',['budget','model-patch','receipt','root','other-worker','template-limit','policy-join','extra','binding','generation','t1-proof'])
def test_t1_narrow_plan_refuses_foreign_delta_without_mutation(writer_case,damage):
    s=writer_case;root=copy.deepcopy(s.root);own=copy.deepcopy(s.own);inc=copy.deepcopy(s.inputs);b=copy.deepcopy(s.b);i=copy.deepcopy(s.i)
    if damage=='budget':b['runtime_after']['budget_seconds']+=1
    elif damage=='model-patch':b['runtime_after']['dsh']['patch']['sha256']='a'*64
    elif damage=='receipt':b['runtime_after']['runtime_receipt']['sha256']='a'*64
    elif damage=='root':b['changes'][0]['before_sha256']='a'*64
    elif damage=='other-worker':inc['workers']['a0']['budget_seconds']+=1
    elif damage=='template-limit':inc['workers']['dsh']['budget_seconds']+=1
    elif damage=='policy-join':inc['workers']['dsh']['dsh']['web']['resolver']['sha256']='a'*64
    elif damage=='extra':b['unapproved']=True
    elif damage=='binding':i['binding']['user_id']='foreign'
    elif damage=='generation':i['generation']+=1
    elif damage=='t1-proof':b['runtime_after']['current_availability']['proof']={'path':'/unapproved','sha256':'a'*64}
    with pytest.raises(REFUSED):dec.plan_declaration_delta(root,own,inc,i,b)
    assert snapshot(s.f.e.home)==s.before


@pytest.mark.parametrize('count',range(1,6))
def test_each_partial_five_file_publication_rolls_back_owned_prefix(writer_case,count):
    s=writer_case;outputs=writer.prepare_afterimages(s.view,s.plan,s.stage);owned={}
    with ordinary.SourceUpdateDirectories(s.f.e.home,s.names,[]) as directories:
        for name in s.names[:count]:
            ordinary.publish_update_file(s.f.e.home/name,outputs[name]['data'],0o600,
                s.view.before[name],owned,name,parent_fd=directories.parent_fd(name))
        ordinary.restore_update_files(s.f.e.home,s.view.before,owned,directories=directories)
    assert snapshot(s.f.e.home)==s.before
    with users.authority(s.f.e.home):users.check_onboarding_home(s.f.e.home,s.f.h,s.f.native['binding'])
    assert row(s.f.e)['generation']==s.generation


def test_occupied_stage_and_current_cas_are_refused_without_adoption(writer_case):
    s=writer_case;(s.stage/'occupied').write_text('foreign')
    with pytest.raises(REFUSED):writer.prepare_afterimages(s.view,s.plan,s.stage)
    assert snapshot(s.f.e.home)==s.before
    (s.stage/'occupied').unlink();outputs=writer.prepare_afterimages(s.view,s.plan,s.stage)
    target=s.f.e.home/s.names[0];target.write_bytes(target.read_bytes()+b'\n')
    changed=target.read_bytes();owned={}
    with ordinary.SourceUpdateDirectories(s.f.e.home,s.names,[]) as directories:
        with pytest.raises(REFUSED):ordinary.publish_update_file(target,outputs[s.names[0]]['data'],0o600,
            s.view.before[s.names[0]],owned,s.names[0],parent_fd=directories.parent_fd(s.names[0]))
    assert target.read_bytes()==changed and owned=={}


def test_t2_exact_proof_plan_reseals_without_runtime_or_installation_change(writer_case):
    s=writer_case;outputs=writer.prepare_afterimages(s.view,s.plan,s.stage);publish(s,outputs)
    root=require_readable_config_before_write(s.f.e.home/'config.yaml');own=require_readable_config_before_write(s.f.h/'config.yaml')
    proof=make_proof(s.f);after=copy.deepcopy(s.f.c)
    after['current_availability']['proof']=save(s.evidence/'proof.json',proof)
    folder=s.evidence/'t2';folder.mkdir(mode=0o700)
    inc=get(root,dec.TEMPLATE_INPUTS);b,i,source=bundle(s.f,root,own,inc,folder,
        stage=dec.DSH_CURRENT_PROOF_SCHEMA,after=after)
    plan=dec.plan_declaration_delta(root,own,inc,i,b)
    assert plan['root_config']==root
    assert len(plan['semantic_changes'])==1
    writer.validate_installation_delta(s.view.previous,s.view.current,plan)
    broken=copy.deepcopy(b);broken['runtime_after']['max_file_bytes']+=1
    with pytest.raises(REFUSED):dec.plan_declaration_delta(root,own,inc,i,broken)
    wrong=copy.deepcopy(inc);wrong['workers']['a0']['budget_seconds']+=1
    with pytest.raises(REFUSED):dec.plan_declaration_delta(root,own,wrong,i,b)
    s.view.before={n:ordinary.update_file_state(s.f.e.home/n) for n in s.names}
    s.view.marker=json.loads((s.f.e.home/native.MARKER).read_bytes())
    s.view.proof=json.loads((s.f.h/users.ONBOARDING).read_bytes())
    stage=folder/'stage';stage.mkdir(mode=0o700)
    outputs=writer.prepare_afterimages(s.view,plan,stage);publish(s,outputs)
    assert cur.validate_current(runtime(require_readable_config_before_write(s.f.h/'config.yaml')))['proof']==proof
    assert row(s.f.e)['generation']==s.generation


def test_dsh_native_graph_stream_custody_rejects_drift_and_keeps_historical_modes(tmp_path):
    path=tmp_path/'protected-source';path.write_bytes(b'original');path.chmod(0o664)
    authority=StoppedOperator({},Budget(180));state=authority._dsh_reference_state(path)
    assert path.stat().st_mode&0o777==0o664
    assert authority._dsh_reference_state(path,previous=state)==state
    path.write_bytes(b'changed!')
    with pytest.raises(REFUSED):authority._dsh_reference_state(path,previous=state)


def test_native_dsh_profile_selection_uses_actual_target_and_exact_declared_scope():
    target='telegram-bot-8812646969';home=Path('/synthetic-authorization-home')
    request={'schema':dec.DSH_CURRENT_APPLY_SCHEMA,'profile':target}
    identity={'profile':str(home/'profiles'/target),'binding':{'runtime_profile':target}}
    assert selected_native_profile(request)==target
    assert selected_native_profile(request,root_home=home,identity=identity)==target
    foreign=dict(request,profile='foreign-valid-profile')
    with pytest.raises(REFUSED):selected_native_profile(foreign,root_home=home,identity=identity)
    with pytest.raises(REFUSED):selected_native_profile(request,root_home=Path('/foreign-home'),identity=identity)
    assert selected_native_profile({'schema':writer.APPLY_SCHEMA,'profile':'dest_telegram'})=='dest_telegram'
    with pytest.raises(REFUSED):selected_native_profile({'schema':writer.APPLY_SCHEMA,'profile':target})


@pytest.mark.parametrize('profile',['default','../foreign','x/y','',None,True,' leading','x'*65])
def test_native_dsh_profile_selection_refuses_default_unsafe_or_aliased_names(profile):
    with pytest.raises(REFUSED):selected_native_profile({'schema':dec.DSH_CURRENT_APPLY_SCHEMA,'profile':profile})


def test_dsh_installation_input_delta_cannot_change_any_other_worker(writer_case):
    s=writer_case;other=copy.deepcopy(s.view.current);other['unexpected_worker_change']=True
    with pytest.raises(REFUSED):writer.validate_installation_delta(s.view.previous,other,s.plan)


def test_partial_rollback_refuses_foreign_member_before_restoring_any_owned_path(writer_case):
    s=writer_case;outputs=writer.prepare_afterimages(s.view,s.plan,s.stage);owned={}
    with ordinary.SourceUpdateDirectories(s.f.e.home,s.names,[]) as directories:
        first=s.names[0]
        ordinary.publish_update_file(s.f.e.home/first,outputs[first]['data'],0o600,
            s.view.before[first],owned,first,parent_fd=directories.parent_fd(first))
        foreign=s.f.e.home/s.names[1]
        foreign.write_bytes(foreign.read_bytes()+b'\n# explicit foreign drift\n')
        before=snapshot(s.f.e.home)
        with pytest.raises(REFUSED):ordinary.restore_update_files(s.f.e.home,s.view.before,owned,directories=directories)
    assert snapshot(s.f.e.home)==before


@pytest.mark.parametrize('copied_clock',[False,True])
def test_t2_request_cannot_reuse_t1_clock_body_even_at_another_path(writer_case,copied_clock):
    s=writer_case;outputs=writer.prepare_afterimages(s.view,s.plan,s.stage);publish(s,outputs)
    proof=make_proof(s.f);after=copy.deepcopy(s.f.c)
    after['current_availability']['proof']=save(s.evidence/'proof-clock-test.json',proof)
    root=require_readable_config_before_write(s.f.e.home/'config.yaml')
    own=require_readable_config_before_write(s.f.h/'config.yaml');folder=s.evidence/'clock-test';folder.mkdir(mode=0o700)
    b,i,source=bundle(s.f,root,own,get(root,dec.TEMPLATE_INPUTS),folder,
        stage=dec.DSH_CURRENT_PROOF_SCHEMA,after=after)
    cycle=after['current_availability']['cycle']
    request_clock=save(folder/'copied-t1-clock.json',json.loads(Path(cycle['path']).read_bytes())) if copied_clock else cycle
    s.view.before={n:ordinary.update_file_state(s.f.e.home/n) for n in s.names}
    s.view.proof=json.loads((s.f.h/users.ONBOARDING).read_bytes())
    s.view.request.update(declaration_source=source,clock=request_clock)
    with pytest.raises(ValueError,match='t2_separate_original_clock'):
        writer._planned_delta(s.view)


def transition(s,after,folder,*,phase,request_clock=None):
    """Real typed parser, native resealer and five-file CAS publication."""
    root=require_readable_config_before_write(s.f.e.home/'config.yaml')
    own=require_readable_config_before_write(s.f.h/'config.yaml')
    folder.mkdir(mode=0o700)
    if phase == dec.DSH_CURRENT_PROOF_SCHEMA and request_clock is None:
        now=time.monotonic()
        request_clock=save(folder/'t2-native-clock.json',{'schema':'friday.worker-declarations.clock.v1',
            'boot_id':cur.identity()['boot_id'],'started_mono':now,'deadline_mono':now+180,'seconds':180})
    b,i,source=bundle(s.f,root,own,get(root,dec.TEMPLATE_INPUTS),folder,stage=phase,after=after)
    plan=dec.plan_declaration_delta(root,own,get(root,dec.TEMPLATE_INPUTS),i,b)
    s.view.before={n:ordinary.update_file_state(s.f.e.home/n) for n in s.names}
    s.view.marker=json.loads((s.f.e.home/native.MARKER).read_bytes())
    s.view.proof=json.loads((s.f.h/users.ONBOARDING).read_bytes())
    s.view.request.update(declaration_source=source,
        clock=request_clock or after['current_availability']['cycle'])
    assert writer._planned_delta(s.view)==plan
    stage=folder/'stage';stage.mkdir(mode=0o700)
    outputs=writer.prepare_afterimages(s.view,plan,stage);publish(s,outputs)
    s.f.c=copy.deepcopy(after)
    if phase == dec.DSH_CURRENT_DECLARATION_SCHEMA:
        # The new T1 has its own original beforeimage/source/clock. Retain it
        # before later T2 test setup mutates the reusable fixture view.
        view=SimpleNamespace(**vars(s.view))
        view.before=copy.deepcopy(s.view.before);view.request=copy.deepcopy(s.view.request)
        s.f._t1_journal_case=SimpleNamespace(f=s.f,b=b,i=i,source=source,plan=plan,
            view=view,stage=stage,evidence=folder,names=s.names)
    return b,i,plan


def establish_active(s):
    outputs=writer.prepare_afterimages(s.view,s.plan,s.stage);publish(s,outputs)
    proof=make_proof(s.f);after=copy.deepcopy(s.f.c)
    old_proof=save(s.evidence/'accepted-first-proof.json',proof)
    after['current_availability']['proof']=old_proof
    transition(s,after,s.evidence/'first-t2',phase=dec.DSH_CURRENT_PROOF_SCHEMA)
    assert cur.validate_current(after)['proof']==proof
    return proof


@pytest.mark.parametrize('newboot',[False,True])
def test_native_active_refresh_new_cycle_then_new_proof_without_old_reactivation(writer_case,monkeypatch,newboot):
    s=writer_case;oldproof=establish_active(s);old=copy.deepcopy(s.f.c)
    actual=cur.identity()
    if newboot:
        actual=dict(actual,boot_id='explicit-simulated-second-boot')
        monkeypatch.setattr(cur,'identity',lambda:copy.deepcopy(actual))
    now=time.monotonic();pending=copy.deepcopy(old)
    pending['current_availability']['proof']=None
    pending['current_availability']['cycle']=save(s.evidence/'refresh-clock.json',
        {'schema':'friday.worker-declarations.clock.v1','boot_id':actual['boot_id'],
         'started_mono':now,'deadline_mono':now+180,'seconds':180})
    b,i,plan=transition(s,pending,s.evidence/'refresh-t1',phase=dec.DSH_CURRENT_DECLARATION_SCHEMA)
    assert plan['root_config']==require_readable_config_before_write(s.f.e.home/'config.yaml')
    assert cur.validate_current(pending,allow_pending=True)['proof'] is None
    # Keep all old headers on the same D/R and update the simulated current
    # identity: cycle equality itself must still block this old observation.
    replay=copy.deepcopy(oldproof);replay['current']=actual
    with pytest.raises(RuntimeError,match='proof_changed'):
        cur.validate_proof(pending,s.f.d,replay)
    freshroot=s.f.root/'refresh-observation-source';freshroot.mkdir(mode=0o700)
    nextfixture=SimpleNamespace(**vars(s.f));nextfixture.root=freshroot
    fresh=make_proof(nextfixture)
    active=copy.deepcopy(pending);active['current_availability']['proof']=save(s.evidence/'refreshed-proof.json',fresh)
    t2now=time.monotonic()
    t2clock=save(s.evidence/'separate-t2-clock.json',
        {'schema':'friday.worker-declarations.clock.v1','boot_id':actual['boot_id'],
         'started_mono':t2now,'deadline_mono':t2now+180,'seconds':180})
    transition(s,active,s.evidence/'refresh-t2',phase=dec.DSH_CURRENT_PROOF_SCHEMA,request_clock=t2clock)
    assert cur.validate_current(active)['proof']==fresh
    assert row(s.f.e)['generation']==s.generation
    assert pin(Path(active['runtime_receipt']['path']))==old['runtime_receipt']
    with users.authority(s.f.e.home):users.check_onboarding_home(s.f.e.home,s.f.h,s.f.native['binding'])


def test_refresh_historical_source_headers_are_retained_without_requiring_current_sources(writer_case):
    s=writer_case;oldproof=establish_active(s);old=copy.deepcopy(s.f.c)
    old_declaration=copy.deepcopy(s.f.d)
    # Explicit historical source-successor fixture: immutable retired D/P
    # headers differ from current source inventory; the files remain exact.
    old_declaration['sources']['plugins/friday_rework/host_runtime.py']['sha256']='a'*64
    old['current_availability']['declaration']=save(s.evidence/'retired-declaration.json',old_declaration)
    oldproof=copy.deepcopy(oldproof);oldproof['declaration']=old['current_availability']['declaration']
    oldproof['sources']=copy.deepcopy(old_declaration['sources'])
    old['current_availability']['proof']=save(s.evidence/'retired-proof.json',oldproof)
    reseal(s.f.h,old)
    now=time.monotonic();pending=copy.deepcopy(s.f.c);pending['current_availability']['proof']=None
    pending['current_availability']['cycle']=save(s.evidence/'new-source-cycle.json',
        {'schema':'friday.worker-declarations.clock.v1','boot_id':cur.identity()['boot_id'],
         'started_mono':now,'deadline_mono':now+180,'seconds':180})
    assert dec.historical_dsh_current(old,s.f.native)==old['current_availability']
    transition(s,pending,s.evidence/'source-refresh-t1',phase=dec.DSH_CURRENT_DECLARATION_SCHEMA)
    assert cur.validate_current(pending,allow_pending=True)['proof'] is None


@pytest.mark.parametrize('damage',['pending-before','missing-context','foreign-context','old-proof-pin',
    'old-declaration-pin','old-cycle-pin','stale-generation','reuse-cycle','cloned-cycle','backdated-cycle','clock-join','expired-clock'])
def test_refresh_refusals_preserve_signed_beforeimage_and_old_effects(writer_case,damage):
    s=writer_case;establish_active(s);old=copy.deepcopy(s.f.c);now=time.monotonic()
    pending=copy.deepcopy(old);pending['current_availability']['proof']=None
    pending['current_availability']['cycle']=save(s.evidence/'future-clock.json',
        {'schema':'friday.worker-declarations.clock.v1','boot_id':cur.identity()['boot_id'],
         'started_mono':now,'deadline_mono':now+180,'seconds':180})
    if damage=='pending-before':
        before=copy.deepcopy(old);before['current_availability']['proof']=None;replace_runtime_fixture(s.f,before)
    if damage in ('old-proof-pin','old-declaration-pin','old-cycle-pin'):
        member={'old-proof-pin':'proof','old-declaration-pin':'declaration','old-cycle-pin':'cycle'}[damage]
        old['current_availability'][member]['sha256']='a'*64;reseal(s.f.h,old)
    root=require_readable_config_before_write(s.f.e.home/'config.yaml');own=require_readable_config_before_write(s.f.h/'config.yaml')
    folder=s.evidence/'refusal';folder.mkdir(mode=0o700)
    b,i,source=bundle(s.f,root,own,get(root,dec.TEMPLATE_INPUTS),folder,after=pending)
    if damage=='missing-context':b.pop('refresh_context')
    elif damage=='foreign-context':b['refresh_context']['boot_id']='foreign'
    elif damage=='stale-generation':i['generation']+=1
    elif damage=='reuse-cycle':b['runtime_after']['current_availability']['cycle']=old['current_availability']['cycle']
    elif damage=='cloned-cycle':b['runtime_after']['current_availability']['cycle']=save(folder/'cloned-cycle.json',
        json.loads(Path(old['current_availability']['cycle']['path']).read_bytes()))
    if damage=='backdated-cycle':
        oldproof=json.loads(Path(old['current_availability']['proof']['path']).read_bytes())
        start=oldproof['observed_mono']-.01
        b['runtime_after']['current_availability']['cycle']=save(folder/'backdated-clock.json',
            {'schema':'friday.worker-declarations.clock.v1','boot_id':cur.identity()['boot_id'],
             'started_mono':start,'deadline_mono':start+180,'seconds':180})
    before=snapshot(s.f.e.home)
    if damage=='clock-join':
        source['bundle']=save(folder/'bundle.json',b)
        s.view.before={n:ordinary.update_file_state(s.f.e.home/n) for n in s.names}
        s.view.proof=json.loads((s.f.h/users.ONBOARDING).read_bytes())
        s.view.request.update(declaration_source=source,clock=old['current_availability']['cycle'])
        with pytest.raises(REFUSED):writer._planned_delta(s.view)
    elif damage=='expired-clock':
        expired=save(folder/'expired-clock.json',{'schema':'friday.worker-declarations.clock.v1',
            'boot_id':cur.identity()['boot_id'],'started_mono':now-181,'deadline_mono':now-1,'seconds':180})
        with pytest.raises(REFUSED):writer.validated_clock(expired,180)
    else:
        with pytest.raises(REFUSED):dec.plan_declaration_delta(root,own,get(root,dec.TEMPLATE_INPUTS),i,b)
    assert snapshot(s.f.e.home)==before


def test_refresh_key_cannot_reset_consumption_with_new_clock_or_replayed_intent(writer_case):
    s=writer_case;establish_active(s);old=copy.deepcopy(s.f.c);now=time.monotonic()
    pending=copy.deepcopy(old);pending['current_availability']['proof']=None
    pending['current_availability']['cycle']=save(s.evidence/'new-clock.json',{'schema':'friday.worker-declarations.clock.v1',
        'boot_id':cur.identity()['boot_id'],'started_mono':now,'deadline_mono':now+180,'seconds':180})
    root=require_readable_config_before_write(s.f.e.home/'config.yaml');own=require_readable_config_before_write(s.f.h/'config.yaml')
    folder=s.evidence/'key';folder.mkdir(mode=0o700)
    b,i,source=bundle(s.f,root,own,get(root,dec.TEMPLATE_INPUTS),folder,after=pending)
    name=dec.dsh_current_transaction_name(b,old['current_availability'])
    expected=dec.fingerprint({'schema':'friday.dsh-current-refresh-key.v1','stage':dec.DSH_CURRENT_DECLARATION_SCHEMA,
        'previous':old['current_availability'],
        'declaration_semantic_sha256':dec.fingerprint(s.f.d),'current':cur.identity()})
    assert name=='ordinary-dsh-current-refresh-'+expected
    next_clock_start=time.monotonic()
    changed=copy.deepcopy(b);changed['runtime_after']['current_availability']['cycle']=save(folder/'other-clock.json',
        {'schema':'friday.worker-declarations.clock.v1','boot_id':cur.identity()['boot_id'],
         'started_mono':next_clock_start,'deadline_mono':next_clock_start+180,'seconds':180})
    assert changed['runtime_after']['current_availability']['cycle']['sha256'] != pending['current_availability']['cycle']['sha256']
    assert dec.dsh_current_transaction_name(changed,old['current_availability'])==name
    copied=copy.deepcopy(b)
    copied['runtime_after']['current_availability']['declaration']=save(folder/'copied-declaration.json',s.f.d)
    assert copied['runtime_after']['current_availability']['declaration']['path'] != pending['current_availability']['declaration']['path']
    assert dec.dsh_current_transaction_name(copied,old['current_availability'])==name
    reformatted=folder/'reformatted-declaration.json'
    reformatted.write_text(json.dumps(s.f.d,indent=4,sort_keys=False)+'\n');reformatted.chmod(0o600)
    reencoded=copy.deepcopy(b)
    reencoded['runtime_after']['current_availability']['declaration']=pin(reformatted)
    assert pin(reformatted)['sha256']!=pending['current_availability']['declaration']['sha256']
    assert dec.dsh_current_transaction_name(reencoded,old['current_availability'])==name
    assert dec.dsh_current_transaction_name(s.b,
        before_configurations=(s.root,s.own)).startswith('ordinary-dsh-current-initial-')
    # Exercise the actual read-only native preflight collision seam; this
    # structural object supplies no authority, guard replacement or claim.
    tx=s.f.e.home/'preparation'/name;tx.parent.mkdir(mode=0o700,exist_ok=True);tx.mkdir(mode=0o700)
    (tx/'intent.json').write_text('retained consumed original intent')
    authority=StoppedOperator({},Budget(180));authority.home=s.f.e.home
    authority.declaration_bundle=b;authority.dsh_previous=old['current_availability']
    with pytest.raises(REFUSED):authority._dsh_current_transaction()
    assert (tx/'intent.json').read_text()=='retained consumed original intent'
