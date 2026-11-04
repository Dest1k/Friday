"""Synthetic ordinary capabilities; real production admission/provisioning code."""
import copy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pathlib import Path
from contextlib import contextmanager
import contextvars
import weakref


@pytest.fixture
def env(tmp_path,monkeypatch,request):
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    from hermes_cli.friday_product_access import KEY,principal_id
    from hermes_cli.plugins_state import PluginState
    from gateway.config import Platform
    from gateway.session import SessionSource
    from gateway.session_identity import RoutingIdentity
    root=tmp_path/'home';root.mkdir(mode=0o700)
    monkeypatch.setenv('HERMES_HOME',str(root))
    import hermes_constants as hc
    monkeypatch.setattr(hc,'_PINNED_PROCESS_HERMES_HOME',str(root))
    monkeypatch.setattr(scope,'_CURRENT',contextvars.ContextVar('dialogue-test-current',default=None))
    monkeypatch.setattr(scope,'_SOURCE',contextvars.ContextVar('dialogue-test-source',default=None))
    monkeypatch.setattr(scope,'_ENGAGED',False)
    def write(p,v):p.write_text(json.dumps(v));p.chmod(0o600)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    native_tools=['memory','read_file','web_search','web_extract']
    bindings=[dict(platform='telegram',transport_profile='default',account_id='synthetic-account',user_id=str(i),runtime_profile='fixture-user-'+str(i),tools=native_tools) for i in (1,2)]
    cfg={'plugins':{'enabled':['friday_rework'],'entries':{'friday_rework':{'settings':{'product_access':{'enabled':True,'accounts':[dict(platform='telegram',transport_profile='default',account_id='synthetic-account',runtime_profiles=[b['runtime_profile'] for b in bindings])]},'user_isolation':{'enabled':True,'bindings':bindings}}}}},'gateway':{'multiplex_profiles':True,'profile_routes':[{'name':'friday-'+principal_id(*(b[k] for k in ('platform','transport_profile','account_id','user_id'))),'platform':b['platform'],'bot_profile':b['transport_profile'],'user_id':b['user_id'],'profile':b['runtime_profile'],'enabled':True} for b in bindings]}}
    write(root/'config.yaml',cfg)
    rows={principal_id(*(b[k] for k in ('platform','transport_profile','account_id','user_id'))):{k:b[k] for k in ('platform','transport_profile','account_id','user_id')}|dict(enabled=True,role='user') for b in bindings}
    with scope.authority(root):PluginState('friday_rework').set(KEY,dict(schema=KEY,users=rows))
    homes={};sources={};adapters=[]
    class Adapter:pass
    for b in bindings:
        h=scope.provision_new_home(root,b,{'max_iterations':8});homes[b['user_id']]=h
        if True:
            import hermes_yaml as yaml
            tool_cfg=yaml.safe_load((h/'config.yaml').read_text());tool_cfg['tools']={'tool_search':{'enabled':'on','defer':['web_search','web_extract']}};write(h/'config.yaml',tool_cfg)
        (h/'SOUL.md').write_text('Synthetic signed identity: Пятница. Preserve safety and tool authority.\n');(h/'SOUL.md').chmod(0o600)
        (h/'.env').write_text('SYNTHETIC_FIXTURE_KEY=offline-fixture\n');(h/'.env').chmod(0o600)
        st=h.stat();receipt=dict(schema='friday.onboarding.v1',binding_sha256=scope._fingerprint(b),config_sha256=sha(h/'config.yaml'),soul_sha256=sha(h/'SOUL.md'),required_secrets=['SYNTHETIC_FIXTURE_KEY'],directory_identity=[st.st_dev,st.st_ino],template='synthetic',authorization_home=str(root))
        write(h/scope.ONBOARDING,receipt)
        marker=json.loads((h/scope.MARKER).read_text());marker['onboarding_sha256']=sha(h/scope.ONBOARDING);write(h/scope.MARKER,marker)
        adapter=Adapter();adapters.append(adapter)
        s=SessionSource(Platform.TELEGRAM,'synthetic-chat',user_id=b['user_id'],chat_type='dm',profile=b['runtime_profile'])
        s._identity=RoutingIdentity('default',b['runtime_profile'],root,h,multiplexed=True,transport_inferred=False,transport=weakref.ref(adapter))
        with scope.authority(root):scope.admit_source(s)
        sources[b['user_id']]=s
    token=set_hermes_home_override(str(root))
    try:yield SimpleNamespace(root=root,homes=homes,sources=sources,adapters=adapters)
    finally:reset_hermes_home_override(token)


def home(env,uid='1'):return env.homes[uid]
def complete(env,uid='1'):return None


@contextmanager
def entered(env,uid='1'):
    with scope.authority(home(env,uid)),scope.scoped_source(env.sources[uid]) as cap:yield cap


from hermes_cli import friday_user_scope as scope

import socket

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Network is forbidden in this offline regression")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
