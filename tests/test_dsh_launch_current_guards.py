"""Source/native guards with explicit IO seams; no AA/network/worker execution.

Native UserScope/read-only generation validation is real against isolated homes.
Association loading, AppArmor attachment/label and subprocess transport are
synthetic seams; these tests cannot establish installed runtime acceptance.
"""
import copy
from dataclasses import replace
import importlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import test_dsh_adapter as fixture
import test_worker_web as web_fixture
from test_user_onboarding import env, prepare, secrets, grant, activate, home, row
from hermes_cli import friday_user_scope as scope

adapter_module = importlib.import_module('friday_dsh_adapter_test.adapters.dsh')
web_module = importlib.import_module('friday_dsh_adapter_test.worker_web')
LABEL = 'friday-dsh-native-v1 (enforce)'


@pytest.mark.parametrize('label', ['unconfined', 'friday-dsh-native-v1 (complain)',
    'unconfined//&friday-dsh-native-v1 (enforce)', None])
@pytest.mark.parametrize('keys', [(), ('LOCAL_TEST_KEY', 'EXA_API_KEY')])
def test_actual_bootstrap_refuses_before_key_read_or_exec(label, keys):
    reads=[];execs=[]
    class Secrets(dict):
        def __contains__(self,key): reads.append(key); return super().__contains__(key)
        def __getitem__(self,key): reads.append(key); return super().__getitem__(key)
    code=adapter_module._bootstrap(keys,web=True)
    with patch('sys.argv',['bootstrap','/tool','/node','cli']), \
         patch('os.environ',Secrets(LOCAL_TEST_KEY='SYNTHETIC',EXA_API_KEY='SYNTHETIC')), \
         patch('pathlib.Path.read_text',**({'return_value':label} if label is not None else {'side_effect':OSError('fixture unreadable label')})), \
         patch('os.execve',side_effect=lambda *a:execs.append(a)):
        with pytest.raises((RuntimeError,OSError)):exec(compile(code,'bootstrap.py','exec'),{})
    assert reads==[] and execs==[]


@pytest.mark.parametrize('keys', [(), ('LOCAL_TEST_KEY',)])
def test_actual_bootstrap_requires_exact_current_enforce_before_exec(keys):
    execs=[]
    with patch('sys.argv',['bootstrap','/tool','/node','cli']), \
         patch('os.environ',{'LOCAL_TEST_KEY':'SYNTHETIC','FOREIGN_KEY':'NOT_ADMITTED'}), \
         patch('pathlib.Path.read_text',return_value=LABEL+'\n'), \
         patch('os.execve',side_effect=lambda *a:execs.append(a)):
        exec(compile(adapter_module._bootstrap(keys,web=True),'bootstrap.py','exec'),{})
    assert len(execs)==1 and execs[0][0]=='/node'
    assert ('LOCAL_TEST_KEY' in execs[0][2]) == bool(keys)
    assert 'FOREIGN_KEY' not in execs[0][2]
    assert execs[0][2]['NODE_EXTRA_CA_CERTS']=='/job-input/web-ca.pem'


@pytest.fixture
def launch(env,monkeypatch):
    prepare(env);secrets(env);grant(env);assert activate(env)['enabled']
    h=home(env)
    binding=scope.policy(env.home)['bindings'][0]
    st=h.stat()
    cap=scope.UserScope(env.home,h,h.name,tuple(binding[k] for k in
        ('platform','transport_profile','account_id','user_id')),binding,(st.st_dev,st.st_ino),row(env)['generation'])
    w=web_fixture.WorkerWeb();w.setUp()
    f=w.f
    f.row['owner'].update(bot_id='bot-A',user_id='1',chat_id='fixture-chat',thread_id='',profile=h.name)
    p=f.prep()
    runtime={'runtime_home':str(h),'runtime_profile':h.name}
    ingress={'platform':'telegram','transport_profile':'default','runtime_profile':h.name,'source_profile':'',
        'message':{'bot_id':'bot-A','user_id':'1','chat_id':'fixture-chat','thread_id':''}}
    f.row['host']={'binding':{'runtime':copy.deepcopy(runtime),'ingress':ingress,
        'user_authority':{'principal_id':cap.key,'generation':cap.admission_generation}}}
    f.row['submission_observation']='UNKNOWN'
    # Real host_record structure is covered by existing native host tests. Here
    # only row retrieval is a seam, retaining real submit/prepare/native guards.
    f.adapter._row=lambda original:(copy.deepcopy(f.row),Path(f.row['workspace_reference']))
    checker=web_module.DshNetworkCheck(runtime,SimpleNamespace(clock=lambda:f.now),f.adapter)
    f.config=replace(f.config,verify_web_network=checker)
    f.adapter.config=f.config
    net=Path('/proc/self/ns/net').stat()
    policy={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'net_namespace':[net.st_dev,net.st_ino],'document_probes':['https://example.org/']}
    monkeypatch.setattr(web_module,'web_policy',lambda *a:copy.deepcopy(policy))
    fixture_state=SimpleNamespace(w=w,f=f,p=p,cap=cap,env=env,probes=0,models=0,key_reads=0,
        mutate=lambda:None,mutate_at=None,label=LABEL)
    old_environment=f.config.environment
    def environment():fixture_state.key_reads+=1;return old_environment()
    f.config=replace(f.config,environment=environment);f.adapter.config=f.config
    def transport(argv,**kw):
        if argv[0]==adapter_module._APPARMOR_ENTRY:
            fixture_state.probes+=1
            assert '--clearenv' in argv
            assert not {'LOCAL_TEST_KEY','EXA_API_KEY'} & set(kw['env'])
            code=(Path(f.row['workspace_reference'])/'inputs/bootstrap.py').read_bytes()
            captured=[]
            # Simulate the attachment result by executing the actual prepared
            # bootstrap, keeping CLI/Node and network transport fully stubbed.
            with patch('sys.argv',['bootstrap','/tool','/node','probe']), \
                 patch('os.environ',kw['env']), \
                 patch('pathlib.Path.read_text',return_value=fixture_state.label), \
                 patch('os.execve',side_effect=lambda *a:captured.append(a)):
                try:exec(compile(code,'bootstrap.py','exec'),{})
                except RuntimeError:return subprocess.CompletedProcess(argv,1,b'',b'fixture enforcement refusal')
            assert len(captured)==1 and not {'LOCAL_TEST_KEY','EXA_API_KEY'} & set(captured[0][2])
            urls=json.loads(argv[-1])
            result={'schema':'friday.dsh-web-observation.v1','rows':[dict(url=u,address='93.184.216.34',status=200,tls=True) for u in urls]}
            if fixture_state.mutate_at==fixture_state.probes:fixture_state.mutate()
            return subprocess.CompletedProcess(argv,0,json.dumps(result).encode(),b'')
        fixture_state.models+=1
        return f.launch(argv,**kw)
    monkeypatch.setattr(subprocess,'run',transport)
    with scope.authority(h):
        token=scope._CURRENT.set(cap)
        try:
            assert scope.check_retained_job(f.row) is None
            yield fixture_state
        finally:scope._CURRENT.reset(token);w.doCleanups()


def revoke_native(t):
    # Administrative actor has its own root context, just as the real API.
    # Do not accidentally revoke the retained cap merely by switching its home.
    token=scope._CURRENT.set(None)
    try:
        with scope.authority(t.env.home):
            t.env.admin.set_user('default',platform='telegram',transport_profile='default',
                account_id='bot-A',user_id='1',enabled=False,role='user')
    finally:scope._CURRENT.reset(token)


def submit(t):return t.f.adapter.submit(t.f.row,t.f.brief,(),t.p,lambda value:None)


def test_real_native_retained_guard_allows_same_owner_and_two_keyless_selectors(launch):
    t=launch;submit(t)
    assert (t.probes,t.models,t.key_reads)==(2,1,4)
    assert adapter_module._APPARMOR_ENTRY in t.f.argv


@pytest.mark.parametrize('field',['generation','principal','owner','ingress','runtime','native-revocation'])
@pytest.mark.parametrize('probe',[1,2])
def test_mutation_during_each_probe_prevents_model_launch(launch,field,probe):
    t=launch;t.mutate_at=probe
    def mutate():
        b=t.f.row['host']['binding']
        if field=='generation':b['user_authority']['generation']+=1
        elif field=='principal':b['user_authority']['principal_id']='f'*64
        elif field=='owner':t.f.row['owner']['user_id']='2'
        elif field=='ingress':b['ingress']['message']['user_id']='2'
        elif field=='runtime':b['runtime']['runtime_home']=str(t.env.home)
        else:revoke_native(t)
    t.mutate=mutate
    with pytest.raises((scope.ScopeDenied,web_module.WorkerWebError,adapter_module.AdapterError)):submit(t)
    assert t.probes==probe and t.models==0
    assert t.key_reads==(0 if probe==1 else 1)


@pytest.mark.parametrize('probe',[1,2])
@pytest.mark.parametrize('label',['unconfined','friday-dsh-native-v1 (complain)'])
def test_unloaded_or_complain_attachment_at_probe_refuses_before_model(launch,probe,label):
    t=launch
    if probe==1:t.label=label
    else:t.mutate_at=1;t.mutate=lambda:setattr(t,'label',label)
    with pytest.raises(web_module.WorkerWebError,match='native_dns_tls_refused'):submit(t)
    assert t.models==0 and t.probes==probe
    assert t.key_reads==(0 if probe==1 else 1)


def test_native_revocation_in_second_key_callback_refuses_at_final_rpc(launch):
    t=launch;old=t.f.config.environment
    def environment():
        result=old()
        if t.key_reads==2:revoke_native(t)
        return result
    t.f.adapter.config=replace(t.f.config,environment=environment)
    with pytest.raises(scope.ScopeDenied):submit(t)
    assert (t.probes,t.models,t.key_reads)==(2,0,2)


def test_owned_stop_after_readiness_and_native_authority_drift(launch,monkeypatch):
    t=launch;submit(t)
    revoke_native(t)
    with pytest.raises(scope.ScopeDenied):scope.check_retained_job(t.f.row)
    t.f.config.web.resolver.path.write_bytes(b'CHANGED CURRENT READINESS')
    t.f.row['stop_intent']='cancel'
    monkeypatch.setattr(t.f.adapter,'_launch_authority',lambda *a:pytest.fail('stop requires authority'))
    monkeypatch.setattr(t.f.adapter,'_pins',lambda:pytest.fail('stop requires readiness'))
    value=t.f.adapter.stop(t.f.row,t.p,'cancel')
    assert value.state=='stopped' and t.f.sup.stops==1 and not t.f.sup.running


@pytest.mark.parametrize('label',['unconfined','friday-dsh-native-v1 (complain)'])
def test_actual_prepared_cli_bootstrap_rechecks_enforcement_after_both_probes(launch,monkeypatch,label):
    t=launch;transport=subprocess.run;execs=[];reads=[]
    class SecretEnvironment(dict):
        def __contains__(self,key):reads.append(key);return super().__contains__(key)
        def __getitem__(self,key):reads.append(key);return super().__getitem__(key)
    def run(argv,**kw):
        if argv[0]==adapter_module._APPARMOR_ENTRY:return transport(argv,**kw)
        t.models+=1
        # Simulated kernel policy drift occurs after both successful probes.
        # Execute the exact prepared CLI bootstrap; never execute Node or CLI.
        code=(Path(t.f.row['workspace_reference'])/'inputs/bootstrap.py').read_bytes()
        with patch('sys.argv',['bootstrap','/tool','/node','cli']), \
             patch('os.environ',SecretEnvironment(kw['env'])), \
             patch('pathlib.Path.read_text',return_value=label), \
             patch('os.execve',side_effect=lambda *a:execs.append(a)):
            with pytest.raises(RuntimeError,match='enforcement_unconfirmed'):
                exec(compile(code,'bootstrap.py','exec'),{})
        return subprocess.CompletedProcess(argv,1,b'',b'fixture bootstrap enforcement refusal')
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(adapter_module.AdapterError):submit(t)
    assert (t.probes,t.models,t.key_reads)==(2,1,2)
    assert reads==[] and execs==[] and not t.f.sup.launched



def test_old_prepared_bootstrap_cannot_retain_launch_permission_by_its_old_hash():
    import hashlib
    f=fixture.AdapterTests();f.setUp()
    try:
        p=f.prep();root=Path(f.row['workspace_reference'])
        bootstrap=root/'inputs/bootstrap.py'
        legacy=b'import os,sys\nos.execve(sys.argv[2],sys.argv[2:],dict(os.environ))\n'
        bootstrap.write_bytes(legacy)
        receipt=Path(p.receipt_reference);value=json.loads(receipt.read_bytes())
        value['files'][str(bootstrap)]=hashlib.sha256(legacy).hexdigest()
        receipt.write_text(json.dumps(value))
        f.row['submission_observation']='UNKNOWN'
        with patch('subprocess.run') as run,pytest.raises(adapter_module.AdapterError,match='prepared_bootstrap_changed'):
            f.adapter.submit(f.row,f.brief,(),p,lambda value:None)
        run.assert_not_called()
    finally:f.doCleanups()
