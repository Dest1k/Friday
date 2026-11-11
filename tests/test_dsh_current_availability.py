"""Actual native profile authority and current consumers; native effects synthetic.

No service, worker, model or real network is run. Historical and current native
reports are explicit fixtures; they cannot establish installed availability.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

import pytest
from test_user_onboarding import env, prepare, secrets, grant, activate, home, row
from test_user_worker_provision import inputs
from friday_admin_controls import dsh_current_availability as cur
from friday_admin_controls import host_runtime as hr
from friday_admin_controls import onboarding
from hermes_cli import friday_user_scope as scope
from hermes_cli.config import require_readable_config_before_write, atomic_config_write


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.write_text(json.dumps(value,sort_keys=True)+'\n');path.chmod(0o600)
    return cur.pin(path)


def reseal(h,c):
    cfg=require_readable_config_before_write(h/'config.yaml')
    cfg['plugins']['entries']['friday_rework']['settings']['runtime']=copy.deepcopy(c)
    prepared=onboarding.prepare_admin_config_edit(h,cfg)
    with scope.authority(h):atomic_config_write(h/'config.yaml',cfg)
    onboarding.finish_admin_config_edit(h,prepared)


@pytest.fixture
def candidate(env):
    e=env;prepare(e);secrets(e);grant(e);assert activate(e)['enabled']
    h=home(e);cfg=require_readable_config_before_write(e.home/'config.yaml')
    binding=cfg['plugins']['entries']['friday_rework']['settings']['user_isolation']['bindings'][0]
    c,_=inputs(e);d=c['dsh'];root=h/'workers/dsh'
    cli=Path(d['payload_root'])/'apps/cli/lib/bin.js';cli.parent.mkdir(parents=True,mode=0o700)
    cli.write_bytes(b'NEVER EXECUTED SYNTHETIC CLI');cli.chmod(0o600);d['cli']=cur.pin(cli)
    for name in ('jobs','staging','cache','inputs'):(root/name).mkdir(parents=True,exist_ok=True,mode=0o700)
    from tools.render_dsh_local import build_patch
    own=require_readable_config_before_write(h/'config.yaml');provider=own['providers']['friday-local'];model=own['model'];capacity=provider['models'][model['default']];b=capacity['bounded_context']
    patch=build_patch(purpose='temporary-local-test',api='openai-completions',base_url=model['base_url'],model=model['default'],api_key_env='LOCAL_KEY',context_window=capacity['context_length'],max_tokens=b['main_max_output_tokens'],summary_max_tokens=b['compression_max_output_tokens'],headroom_tokens=b['safety_margin_tokens']+b['template_overhead_tokens'],web_profile='exa-paid')
    d['patch']=save(root/'inputs/dsh-local.json',patch)
    policy={'schema':cur.POLICY,'runtime_home':str(h),'runtime_profile':c['runtime_profile'],
        'authority_id':'synthetic-reviewed-operator','generation':1,'web_profile':'exa-paid',
        'allow_public_https':True,'document_probes':['https://docs.python.org/3/']}
    d['web']['egress_evidence']=save(root/'inputs/durable-policy.json',policy)
    st=h.stat();native={'authorization_home':str(e.home),'binding':binding,
        'generation':row(e)['generation'],'directory_identity':[st.st_dev,st.st_ino]}
    hist=h/'workers/qualification';hist.mkdir(mode=0o700)
    historical=copy.deepcopy(c)
    prep=save(hist/'retained-preparation.json',{'runtime':historical,'principal_binding_sha256':cur.fingerprint(binding),'generation':native['generation']})
    oldclock={'boot_id':'historical-boot','started_mono':10,'deadline_mono':610,'budget_seconds':600}
    orig=save(hist/'original.json',{'schema':'friday.user-worker-qualification.v1','home':str(h),'profile':c['runtime_profile'],'binding':binding,'binding_sha256':cur.fingerprint(binding),'generation':native['generation'],'original_attempt':oldclock,'preparations':{'dsh':prep}})
    fail=save(hist/'failure.json',{'state':'STOP_UNCONFIRMED','original_attempt':oldclock})
    retained={'original':orig,'local_failure':fail};dshrefs={'observation':save(hist/'dsh-stage.json',{'fixture':True})};safetyrefs={'observation':save(hist/'safety-stage.json',{'fixture':True})}
    comp=save(hist/'completion-original.json',{'schema':'friday.r481.post-a0-completion.v1','binding':binding,'binding_sha256':cur.fingerprint(binding),'generation':native['generation'],'old_attempt_reopened':False,'A0_start_repeated':False,'original_attempt':dict(oldclock,started_mono=800,deadline_mono=1100,budget_seconds=300),'preparations':{'dsh':prep},'retained':retained,'dsh_refs':dshrefs,'safety_refs':safetyrefs})
    smoke=[{'kind':kind,'observation':{'returncode':0,'reaped':True,'timeout':False}} for kind in ('version','help','headless-config','headless-help')]
    obs=save(hist/'observation.json',{'schema':'friday.worker-deployment-observation.v1','home':str(h),'profile':c['runtime_profile'],'effects':'OBSERVATION_ONLY','per_job_authority':'NOT_GRANTED','original':orig,'post_a0_completion':{'schema':'friday.r481.post-a0-completion.v1','original':comp,'retained':retained},'workers':{'dsh':{'smoke':smoke}}})
    c['runtime_receipt']=save(root/'runtime-receipt.json',{'schema':'friday-rework.dsh-runtime.v1','ready':True,'evidence':[obs]})
    graph={**{'retained.'+k:v for k,v in retained.items()},**{'dsh_refs.'+k:v for k,v in dshrefs.items()},**{'safety_refs.'+k:v for k,v in safetyrefs.items()}}
    cycle_now=time.monotonic()
    cycle=save(root/'t1-cycle-clock.json',{'schema':'friday.worker-declarations.clock.v1','boot_id':cur.identity()['boot_id'],'started_mono':cycle_now-1,'deadline_mono':cycle_now+179,'seconds':180})
    c['current_availability']={'declaration':{'path':str(root/'current-declaration.json'),'sha256':'0'*64},'proof':None,'cycle':cycle}
    dec={'schema':cur.DECLARATION,'runtime_home':str(h),'runtime_profile':c['runtime_profile'],'runtime_sha256':cur.runtime_semantic_digest(c),'policy':d['web']['egress_evidence'],'policy_authority':{'id':policy['authority_id'],'generation':policy['generation']},'native':native,'sources':cur.source_pins(),'inputs':cur.runtime_input_pins(c),'history':{'original':orig,'observation':obs,'failure':fail,'completion':comp,'preparation':prep,'receipt':c['runtime_receipt'],'retained':graph}}
    c['current_availability']['declaration']=save(root/'current-declaration.json',dec)
    reseal(h,c)
    return SimpleNamespace(e=e,h=h,c=c,d=dec,native=native,policy=policy,root=root)


def make_proof(f):
    from dsh_current_commit_fixture import commit_pending_fixture
    pending=commit_pending_fixture(f)
    from friday_admin_controls import runtime_observers as observers
    now=time.monotonic();ident=cur.identity();folder=f.root/'current-observation';folder.mkdir(mode=0o700)
    clock=save(folder/'clock.json',{'schema':'friday.dsh-current-observation.clock.v1','boot_id':ident['boot_id'],'started_mono':now,'deadline_mono':now+180,'seconds':180,'stage_folder':str(folder)})
    def execution(name,seconds):
        return {'returncode':0,'timeout':False,'reaped':True,'current_cap_seconds':seconds,'resource_envelope':{'unit':'friday-qualify-dsh-'+hashlib.sha256(str(folder/name).encode()).hexdigest()[:24]+'-1.scope',**{k:f.c['dsh'][k] for k in ('memory_bytes','cpu_percent','tasks')},'boot_id':ident['boot_id'],'deadline':now+seconds}}
    budget=SimpleNamespace(fixture_boot=ident['boot_id'],deadline=now+178)
    safety=safety_observation(f.c,f.h,folder/'dsh-safety',budget)
    safety['execution']=execution('dsh-safety',20)
    network={'network':observation(['https://api.exa.ai/',*f.policy['document_probes']]),'network_execution':execution('dsh-network',5),'policy_sha256':f.d['policy']['sha256']}
    return {'schema':cur.PROOF,'effects':'OBSERVATION_ONLY','per_job_authority':'NOT_GRANTED','declaration':f.c['current_availability']['declaration'],'cycle':f.c['current_availability']['cycle'],'runtime_sha256':f.d['runtime_sha256'],'policy':f.d['policy'],'native':f.native,'sources':f.d['sources'],'inputs':f.d['inputs'],'current':ident,'clock':clock,'observed_mono':now,'pending_transaction':pending,'folder':str(folder),'safety':safety,'network':network}


def activate_proof(f,p):
    f.c['current_availability']['proof']=save(f.root/'current-proof.json',p);reseal(f.h,f.c)


def test_pending_signed_native_config_refuses_ordinary_health(candidate):
    f=candidate
    assert cur.validate_current(f.c,allow_pending=True)['proof'] is None
    with pytest.raises(hr.HostUnavailable,match='pending'):hr.deployment_health(f.c)
    from friday_admin_controls import user_worker_join
    with pytest.raises(hr.HostUnavailable,match='pending'):user_worker_join.deployment_health(f.c)
    store=SimpleNamespace(state=SimpleNamespace(data_dir=f.h/'associations'))
    with scope.authority(f.h),pytest.raises(hr.HostUnavailable,match='pending'):hr.check_runtime(f.c,store)


def test_valid_active_proof_consumed_by_actual_health_and_factory(candidate,monkeypatch):
    f=candidate;p=make_proof(f);cur.validate_proof(f.c,f.d,p);activate_proof(f,p)
    assert hr.deployment_health(f.c)==f.c
    from friday_admin_controls import user_worker_join
    assert user_worker_join.deployment_health(f.c,binding=f.native['binding'],generation=f.native['generation'])==f.c
    store=SimpleNamespace(state=SimpleNamespace(data_dir=f.h/'associations'),clock=time.time,get=lambda *a:None)
    with scope.authority(f.h):assert hr.check_runtime(f.c,store)==f.c
    monkeypatch.setattr(hr,'NativeSupervisor',lambda:SimpleNamespace(stop=lambda *a:'STOP_USABLE'))
    binding=hr.dsh_binding(f.c,store)
    assert type(binding.adapter.config.verify_web_network).__name__=='DshNetworkCheck'
    # Factory/recovery and stop remain constructible after launch proof drift.
    Path(f.c['current_availability']['proof']['path']).write_text('proof drift')
    assert hr.dsh_binding(f.c,store).emergency_stop(None)=='STOP_USABLE'


@pytest.mark.parametrize('damage',['newboot','newnamespace','runtime','policy','source','inputs','pending','grant','clock','resources','stop','safety','network','original','failure','completion','static-smoke','duplicate','dangling','signed-config','generation'])
def test_current_refusals(candidate,damage):
    f=candidate;p=make_proof(f)
    if damage=='newboot':p['current']['boot_id']='foreign'
    elif damage=='newnamespace':p['current']['net_namespace']=[1,1]
    elif damage=='runtime':f.c['budget_seconds']+=1
    elif damage=='policy':p['policy']['sha256']='a'*64
    elif damage=='source':p['sources']['plugins/friday_rework/host_runtime.py']['sha256']='a'*64
    elif damage=='inputs':p['inputs']['node']['sha256']='a'*64
    elif damage=='pending':p['pending_transaction']['sha256']='a'*64
    elif damage=='grant':p['per_job_authority']='GRANTED'
    elif damage=='clock':p['clock']['sha256']='a'*64
    elif damage=='resources':p['network']['network_execution']['resource_envelope']['tasks']=1
    elif damage=='stop':p['safety']['execution']['reaped']=False
    elif damage=='safety':p['safety']['report']['outer']['label']='unconfined'
    elif damage=='network':p['network']['network']['rows'][0]['tls']=False
    elif damage in ('original','failure','completion'):
        Path(f.d['history'][damage]['path']).write_text('{}')
    elif damage=='static-smoke':f.c['dsh']['cli']['sha256']='a'*64
    elif damage=='duplicate':
        path=Path(f.c['current_availability']['declaration']['path']);path.write_text('{"schema":1,"schema":2}');f.c['current_availability']['declaration']=cur.pin(path)
    elif damage=='dangling':
        path=Path(f.c['current_availability']['declaration']['path']);path.unlink();path.symlink_to(f.root/'absent')
    elif damage=='signed-config':
        own=require_readable_config_before_write(f.h/'config.yaml');own['max_iterations']=own.get('max_iterations',30)+1
        with scope.authority(f.h):atomic_config_write(f.h/'config.yaml',own)
    elif damage=='generation':f.e.admin.set_user('default',platform='telegram',transport_profile='default',account_id='bot-A',user_id='1',enabled=False,role='user')
    with pytest.raises((RuntimeError,ValueError,OSError,PermissionError,KeyError)):
        if damage not in ('dangling','signed-config','generation'):activate_proof(f,p)
        cur.validate_current(f.c)


def test_semantic_digest_excludes_only_two_top_level_refs(candidate):
    f=candidate;a=cur.runtime_semantic_digest(f.c);c=copy.deepcopy(f.c)
    c['runtime_receipt']['sha256']='a'*64;c['current_availability']['proof']={'path':'/changed','sha256':'a'*64}
    assert cur.runtime_semantic_digest(c)==a
    c['dsh']['current_availability']={'model':'changed'}
    assert cur.runtime_semantic_digest(c)!=a


def observation(urls):
    return {"schema":"friday.dsh-web-observation.v1","rows":[dict(url=u,address="93.184.216.34",status=200,tls=True) for u in urls]}

def safety_observation(runtime, home, folder, budget):
    """Explicit synthetic native IO fixture; never deployment acceptance."""
    from friday_admin_controls import runtime_observers as observers
    status='NoNewPrivs: 1\nCapInh: 0000\nCapPrm: 0000\nCapEff: 0000\nCapAmb: 0000\nCapBnd: 000001ffffffffff'
    label='friday-dsh-command-v1//&friday-dsh-native-v1 (enforce)'
    report={'schema':'friday.dsh-native-safety.v1','status':'NATIVE_SAFETY_PASS',
        'runtime_home':str(home),'runtime_profile':runtime['runtime_profile'],
        'payload_root':runtime['dsh']['payload_root'],'node':runtime['dsh']['node']['path'],
        'controls':list(observers.DSH_SAFETY_CONTROLS),'shell_result':{'exitCode':0},'artifact_sha256':hashlib.sha256(b'R2-NATIVE-BASH-OK\n').hexdigest(),
        'outer':{'label':'friday-dsh-native-v1 (enforce)','status':status.splitlines(),
            'ns':{'user':'user:[2]','pid':'pid:[2]','mnt':'mnt:[2]'},'uid_map':'0 1000 1','gid_map':'0 1000 1'},
        'host':{'namespaces':{'user':'user:[1]','pid':'pid:[1]','mnt':'mnt:[1]'},'pid':12345},
        'nested':{'bash-label':label,'python-label':label,'node-label':label,'bash-status':status,
            'bash-pidns':'pid:[3]','bash-userns':'user:[3]','bash-mntns':'mnt:[3]',
            'bash-uid-map':'0 0 1','bash-gid-map':'0 0 1','bash-mountinfo':'1 2 0:1 / /proc ro - proc proc ro'},
        'wrap':{'argv':['/usr/bin/bwrap','--unshare-pid','--proc','/proc']}}
    d=runtime['dsh']
    envelope={'unit':'friday-qualify-dsh-'+hashlib.sha256(str(folder).encode()).hexdigest()[:24]+'-1.scope',
        **{k:d[k] for k in ('memory_bytes','cpu_percent','tasks')},
        'boot_id':'fixture-only','deadline':budget.deadline-1}
    # Match the existing synthetic fixture boot binding, never observe a host process.
    if hasattr(budget,'fixture_boot'): envelope['boot_id']=budget.fixture_boot
    return {'report':report,'execution':{'returncode':0,'reaped':True,'timeout':False,'resource_envelope':envelope},
        'specimen_sha256':hashlib.sha256(observers.DSH_NATIVE_SAFETY.encode()).hexdigest()}



def test_current_observer_runs_only_two_keyless_bounded_native_scopes(candidate,monkeypatch):
    f=candidate
    from dsh_current_commit_fixture import commit_pending_fixture
    pending=commit_pending_fixture(f)
    from friday_admin_controls import runtime_observers as observers
    from friday_admin_controls import runtime_process
    from friday_admin_controls.adapters import dsh as adapter
    calls=[];verifications=[];now=time.monotonic()
    clock=save(f.root/'observer-clock.json',{'schema':'friday.dsh-current-observation.clock.v1','boot_id':cur.identity()['boot_id'],'started_mono':now,'deadline_mono':now+180,'seconds':180,'stage_folder':str(f.root/'bounded-observation')})
    monkeypatch.setattr(adapter,'_apparmor_boundary',lambda cfg,argv:[adapter._APPARMOR_ENTRY,*argv[1:]])
    def run(argv,cwd,**kw):
        calls.append((argv,kw));assert argv[0]=='/usr/bin/systemd-run'
        assert '--scope' in argv and '--as-pid-1' in argv and adapter._APPARMOR_ENTRY in argv
        assert not {'LOCAL_KEY','EXA_API_KEY'} & set(kw['env'])
        assert kw['deadline']==pytest.approx(now+180)
        assert all(any(x.startswith('--property='+key+'=') for x in argv) for key in ('MemoryMax','MemorySwapMax','CPUQuota','TasksMax','RuntimeMaxSec'))
        os.write(int(argv[argv.index('--json-status-fd')+1]),b'{"child-pid":123456}\n{"exit-code":0}\n')
        if 'native-safety.mjs' in argv[-1]:
            assert kw['timeout']<=20
            out=safety_observation(f.c,f.h,Path(cwd),SimpleNamespace(deadline=kw['deadline']))['report']
        else:
            assert 'web-network.mjs' in argv[-2] and kw['timeout']<=5
            out=observation(json.loads(argv[-1]))
        return json.dumps(out),{'returncode':0,'reaped':True,'timeout':False}
    monkeypatch.setattr(runtime_process,'run',run)
    result=cur.observe_current(f.c,clock_reference=clock,pending_transaction=pending,
        folder=f.root/'bounded-observation',verify=lambda:verifications.append(True))
    assert len(calls)==2 and len(verifications)>=4
    value=cur.read_json(result);cur.validate_proof(f.c,f.d,value)
    assert value['per_job_authority']=='NOT_GRANTED'
    assert f.c['current_availability']['proof'] is None
    with pytest.raises(hr.HostUnavailable,match='pending'):cur.validate_current(f.c)
    with pytest.raises(hr.HostUnavailable,match='new_observation_folder'):
        cur.observe_current(f.c,clock_reference=clock,pending_transaction=pending,
            folder=f.root/'bounded-observation',verify=lambda:None)
    assert len(calls)==2


def test_expired_observer_clock_cannot_create_scope(candidate):
    f=candidate;now=time.monotonic()
    clock=save(f.root/'expired-clock.json',{'schema':'friday.dsh-current-observation.clock.v1','boot_id':cur.identity()['boot_id'],'started_mono':now-200,'deadline_mono':now-20,'seconds':180,'stage_folder':str(f.root/'never-created')})
    with pytest.raises(hr.HostUnavailable,match='expired'):
        cur.observe_current(f.c,clock_reference=clock,pending_transaction={'path':'/absent','sha256':'0'*64},folder=f.root/'never-created',verify=lambda:None)
    assert not (f.root/'never-created').exists()


def test_durable_policy_never_passes_legacy_finite_consumer(candidate):
    f=candidate
    from friday_admin_controls.worker_web import web_policy,WorkerWebError
    with pytest.raises(WorkerWebError):web_policy(hr._dsh_web(f.c['dsh']),str(f.h),f.c['runtime_profile'],time.time())


def test_large_input_hashing_is_streaming_and_exact(candidate):
    f=candidate;p=f.root/'large-native-input'
    with p.open('wb') as out:
        for i in range(33):out.write(bytes([i])*1024**2)
    p.chmod(0o600);ref={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    assert cur.verify_reference(ref)==ref
    with pytest.raises(hr.HostUnavailable):cur.read_json(ref)
    with p.open('r+b') as out:out.write(b'X')
    with pytest.raises(hr.HostUnavailable):cur.verify_reference(ref)


@pytest.mark.parametrize('damage',['expired','foreign-home','foreign-profile','foreign-boot','foreign-namespace'])
def test_legacy_finite_policy_stays_finite_and_scoped(candidate,damage):
    f=candidate;c=copy.deepcopy(f.c);c.pop('current_availability');ident=cur.identity()
    policy={'schema':'friday.worker-web.policy.v1','runtime_home':str(f.h),'runtime_profile':c['runtime_profile'],**ident,'expires_unix':time.time()+100,'allow_public_https':True,'document_probes':['https://docs.python.org/3/']}
    if damage=='expired':policy['expires_unix']=time.time()-1
    elif damage=='foreign-home':policy['runtime_home']='/foreign'
    elif damage=='foreign-profile':policy['runtime_profile']='foreign'
    elif damage=='foreign-boot':policy['boot_id']='foreign'
    elif damage=='foreign-namespace':policy['net_namespace']=[1,1]
    c['dsh']['web']['egress_evidence']=save(f.root/'legacy-policy.json',policy)
    from friday_admin_controls.worker_web import WorkerWebError
    with pytest.raises((WorkerWebError,hr.HostUnavailable)):hr.deployment_health(c)


def test_a0_schema_never_accepts_dsh_current_authority(candidate):
    a,_=inputs(candidate.e,worker='a0');assert hr.validate_runtime(a)==a
    a['current_availability']=copy.deepcopy(candidate.c['current_availability'])
    with pytest.raises(hr.HostUnavailable):hr.validate_runtime(a)


@pytest.mark.parametrize('target',['execution','cap','history-smoke'])
def test_boolean_or_float_aliases_do_not_forge_integer_native_success(candidate,target):
    f=candidate;p=make_proof(f)
    if target=='execution':p['network']['network_execution']['returncode']=False
    elif target=='cap':p['network']['network_execution']['current_cap_seconds']=5.0
    else:
        obs=cur.read_json(f.d['history']['observation']);obs['workers']['dsh']['smoke'][0]['observation']['returncode']=False
        save(f.d['history']['observation']['path'],obs)
    with pytest.raises((RuntimeError,ValueError)):
        if target=='history-smoke':cur.validate_declaration(f.c,f.d)
        else:cur.validate_proof(f.c,f.d,p)
