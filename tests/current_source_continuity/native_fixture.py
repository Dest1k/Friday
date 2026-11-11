"""Explicit synthetic authority; genuine serializers and native semantic readers.

No installed home is a target. The sole authority seams are synthetic SOURCE
resolution/receipt identity and an in-memory already-enabled product principal.
All current configuration, marker, onboarding and directory checks remain real.
"""
import copy, contextlib, hashlib, importlib.machinery, importlib.util, json, os, sys, types
from pathlib import Path


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    return m

class NativeFixture:
    def __init__(self,H,N,F,O,write,ref,*,repo,native,overlay,receipt,receipt_sha256):
        self.H,self.N,self.F,self.O,self.write,self.ref=H,N,F,O,write,ref
        self.repo=repo.resolve(strict=True);self.native=native.resolve(strict=True)
        self.overlay=overlay.resolve(strict=True) if overlay else None
        self.receipt_path=receipt.resolve(strict=True)
        assert ref(self.receipt_path)['sha256']==receipt_sha256,'native receipt SHA mismatch'
        self.receipt=json.loads(self.receipt_path.read_bytes())
        self.source_roots=[r for r in (self.overlay,self.native) if r is not None]
        # Pin native imports before module code runs. Dependencies outside the
        # declared native directories are normal Python packages, not authority.
        fixture=self
        class ReceiptPinnedImports:
            def find_spec(self,fullname,path=None,target=None):
                spec=importlib.machinery.PathFinder.find_spec(fullname,path,target)
                origin=getattr(spec,'origin',None)
                if not origin or not Path(origin).is_file():return None
                source_path=Path(origin).resolve()
                root=next((r for r in fixture.source_roots if source_path.is_relative_to(r)),None)
                if root is not None:
                    rel=str(source_path.relative_to(root))
                    assert ref(source_path)['sha256']==fixture.receipt['files'][rel]['sha256'],(fullname,rel)
                return None
        sys.meta_path.insert(0,ReceiptPinnedImports())
        os.environ['HERMES_HOME']=str(H)
        sys.path.insert(0,str(self.native))
        # Whole genuine Source199 modules. Their only differences from 198
        # are the separately reviewed Dashboard status additions; this test
        # still loads the exact final bytes instead of inferring equivalence.
        import hermes_cli
        for name in ('friday_dashboard_owner','friday_ordinary_gateway'):
            rel=Path('hermes_cli')/(name+'.py')
            path=next((root/rel for root in self.source_roots if (root/rel).is_file()),None)
            assert path is not None,rel
            assert ref(path)['sha256']==self.receipt['files'][str(rel)]['sha256'],rel
            loaded=module('hermes_cli.'+name,path)
            setattr(hermes_cli,name,loaded)
        from hermes_cli import friday_user_scope as users, friday_ordinary_gateway as gw
        from hermes_cli import friday_dashboard_owner as owner
        from hermes_cli import friday_product_access as access, plugins_state
        from hermes_cli.config import atomic_config_write
        from hermes_cli.config_effective import load_user_config_effective
        self.users,self.gw,self.owner,self.access=users,gw,owner,access
        self.atomic_config_write,self.effective=atomic_config_write,load_user_config_effective
        # Explicit fixture authority resolution. Genuine composition_checked in
        # the common reader still authenticates every native file and receipt.
        owner.SOURCE=N
        owner.source_identity=lambda home,source=None:{'receipt':ref(H/'hermes-agent.source.json')['sha256']}
        for name,path in [('plugins',self.repo/'plugins'),('plugins.friday_rework',self.repo/'plugins/friday_rework'),
                          ('frw_fixture_tools',self.repo/'tools')]:
            p=types.ModuleType(name);p.__path__=[str(path)];sys.modules[name]=p
        from frw_fixture_tools.configure_local_test import build_config
        config=build_config(base_url='http://127.0.0.1:9000/v1',model='synthetic-observed-local',
            key_env='LOCAL_KEY',context=32768,max_input=24576,main_output=4096,
            summary_output=2048,margin=1024,template_overhead=512,web_profile='exa-paid')
        config['model']['key_env']='LOCAL_KEY';config['auth']={'adopt_external_logins':False}
        config['delegation'].update(base_url='http://127.0.0.1:9000/v1',key_env='LOCAL_KEY')
        config['memory'].update(memory_enabled=True,user_profile_enabled=True)
        config['plugins']['enabled'].append('friday_rework')
        config['plugins']['entries']={'friday_rework':{'allow_gateway_work':True,'allow_gateway_control':True,
            'settings':{'runtime':{'enabled':False},'results':{'enabled':True}}}}
        config['toolsets']=['web','memory','file','session_search','friday_rework']
        config['platform_toolsets']={'cli':config['toolsets'],'telegram':config['toolsets']}
        config.pop('mcp_servers',None);config.pop('mcp',None)
        self.template={'config':copy.deepcopy(config),'tools':sorted(users.SAFE),
            'required_secrets':['LOCAL_KEY','EXA_API_KEY']}
        self.profile=H/'profiles/synthetic-user';self.profile.mkdir(mode=0o700,parents=True)
        self.binding=dict(platform='telegram',transport_profile='default',account_id='synthetic-bot',
            user_id='synthetic-user',runtime_profile=self.profile.name,tools=sorted(users.SAFE))
        self.key=access.principal_id(*(self.binding[k] for k in ('platform','transport_profile','account_id','user_id')))
        self.row={k:self.binding[k] for k in ('platform','transport_profile','account_id','user_id')}
        self.row.update(enabled=True,role='user',generation=1)
        self.document={'schema':access.KEY,'users':{self.key:self.row}}
        fixture=self
        class SyntheticReadOnlyState:
            """Only synthetic pre-existing admission; no native grant is minted."""
            def __init__(self,*args,**kwargs):pass
            def get_storage_readonly(self,key,default=None,**kwargs):
                if key!=access.KEY:raise AssertionError('unexpected synthetic state key')
                return copy.deepcopy(fixture.document)
        plugins_state.PluginState=SyntheticReadOnlyState
        self.own_config=config
        self.root_config=copy.deepcopy(config)
        settings=self.root_config['plugins']['entries']['friday_rework']['settings']
        settings.update(product_access={'enabled':True,'accounts':[dict(platform='telegram',
            transport_profile='default',account_id='synthetic-bot',runtime_profiles=['default',self.profile.name])]},
            admin={'enabled':True,'operators':[{'provider':'basic','user_id':'synthetic-owner','org_id':''}],
                'profiles':['default',self.profile.name]},
            user_isolation={'enabled':True,'bindings':[self.binding]},
            onboarding={'templates':{'synthetic-local':self.template}})
        self.root_config['gateway']={'multiplex_profiles':True,'systemd_watchdog_seconds':30,
            'profile_routes':[dict(name='friday-'+self.key,platform='telegram',bot_profile='default',
                user_id=self.binding['user_id'],profile=self.profile.name,enabled=True)]}
        self.root_config['platforms']={'telegram':{'enabled':True,'extra':{
            'drop_pending_on_cold_boot':False,'unauthorized_dm_behavior':'pair'}}}
        self.root_config['dashboard']={'basic_auth':{'username':'synthetic-owner'}}
        self.contract={'schema':'friday.product-profile.v1','kind':'normal_product','profile':'default',
            'native_dashboard':{'operator':{'provider':'basic','user_id':'synthetic-owner','org_id':''}},
            'required_scoped_names':{'channels':{'telegram':['TELEGRAM_BOT_TOKEN']},
                'inference_web':['LOCAL_KEY','EXA_API_KEY'],'dashboard':[]}}
        from plugins.friday_rework import onboarding,worker_declaration_writer as writer
        self.onboarding,self.writer=onboarding,writer
        self.native_check=gw.check

    def files(self):
        H=self.H;write=self.write
        # Historical CP input is legal JSON/YAML, intentionally not the native
        # serializer's YAML afterimage. T1 must produce a distinct raw hash.
        write(H/'config.yaml',self.root_config)
        write(H/'FRIDAY-PROFILE.json',self.contract);write(H/'SOUL.md',b'synthetic root soul\n')
        write(H/'preparation/ordinary-gateway/before/FRIDAY-INSTALL.json',{
            'completion_stage':'CLI_HOST_ONLY','original_attempt':{'synthetic-history':True},
            'cli_segment':{'synthetic-closed-clock':True}})
        p=self.profile
        write(p/'config.yaml',self.own_config);write(p/'SOUL.md',b'synthetic profile soul\n')
        write(p/'.env',b'LOCAL_KEY=synthetic-only-local\nEXA_API_KEY=synthetic-only-exa\n')
        for name in ('memories','workspace'):(p/name).mkdir(mode=0o700)
        st=p.stat()
        self.proof={'schema':'friday.onboarding.v1','binding_sha256':self.users._fingerprint(self.binding),
            'config_sha256':self.ref(p/'config.yaml')['sha256'],'soul_sha256':self.ref(p/'SOUL.md')['sha256'],
            'required_secrets':['LOCAL_KEY','EXA_API_KEY'],'directory_identity':[st.st_dev,st.st_ino],
            'template':'synthetic-local','authorization_home':str(H)}
        write(p/self.users.ONBOARDING,self.proof)
        write(p/self.users.MARKER,{'schema':'friday.user-home.v1','principal':self.key,'profile':p.name,
            'binding_sha256':self.users._fingerprint(self.binding),
            'onboarding_sha256':self.ref(p/self.users.ONBOARDING)['sha256']})

    def marker(self,m):
        m.update(original_attempt={'synthetic-history':True},cli_segment={'synthetic-closed-clock':True})
        phase=m['ordinary_gateway']
        phase.update(schema=self.gw.SCHEMA,scope='TELEGRAM_RECEIVER_AND_AUTHENTICATED_ONBOARDING_ONLY',
            configuration_sha256=self.gw.normalized_configuration(self.root_config),
            credential_files={'.env':self.gw.sha(b'{}'),'auth.json':None},
            profile_sha256=self.ref(self.H/'FRIDAY-PROFILE.json')['sha256'],
            baseline={'runtime_profiles':['default'],'admin_profiles':['default'],'telegram_allowed_users':[]},
            history={'preparation/ordinary-gateway/before/FRIDAY-INSTALL.json':
                self.ref(self.H/'preparation/ordinary-gateway/before/FRIDAY-INSTALL.json')['sha256']})

    def check(self):
        with self.users.authority(self.H):self.native_check(self.H,role=False)
        with self.users.authority(self.profile):
            self.users.UserScope(self.H,self.profile,self.profile.name,
                tuple(self.binding[k] for k in ('platform','transport_profile','account_id','user_id')),
                self.binding,tuple(self.proof['directory_identity']),1).check()

    def afterimages(self,current,reference,runtime,stage):
        O=self.O;U=self.users;p=self.profile;prefix=str(p.relative_to(self.H))+'/'
        from plugins.friday_rework.worker_declarations import DSH_CURRENT_DECLARATION_SCHEMA,DSH_CURRENT_PROOF_SCHEMA
        own=self.effective(p/'config.yaml',fail_closed=True)
        own['plugins']['entries']['friday_rework']['settings']['runtime']=copy.deepcopy(runtime)
        root=self.effective(self.H/'config.yaml',fail_closed=True)
        plan={'root_config':root,'profile_config':own,'dsh_current_stage':
            DSH_CURRENT_PROOF_SCHEMA if runtime['current_availability']['proof'] else DSH_CURRENT_DECLARATION_SCHEMA}
        names=['config.yaml',prefix+'config.yaml',prefix+U.ONBOARDING,prefix+U.MARKER,self.F.MARKER]
        authority=types.SimpleNamespace(home=self.H,profile_home=p,previous=current,current=current,
            marker=json.loads((self.H/self.F.MARKER).read_bytes()),request={'current_input':reference},
            before={n:O.update_file_state(self.H/n) for n in names})
        stage.mkdir(mode=0o700)
        after=self.writer.prepare_afterimages(authority,plan,stage)
        assert set(after)==set(names)
        return after

    def runtime(self,proof=None):
        # Real HostRuntime configuration validation executes on these shapes;
        # paths describe synthetic files only and are never executed.
        p=self.profile;root=self.H/'synthetic-runtime';root.mkdir(mode=0o700,exist_ok=True)
        for name in ('node','cli','patch','native','receipt','declaration','cycle','proof'):
            self.write(root/name,{'synthetic':name})
        d={'enabled':True,'runtime_profile':p.name,'runtime_home':str(p),
            'workspace_root':str(root/'workspace'),'staging_root':str(root/'stage'),
            'cache_roots':[str(root/'cache')],'budget_seconds':60,'max_file_bytes':1024,'max_total_bytes':4096,
            'dsh':{'payload_root':str(root/'payload'),'toolchain_root':str(root/'toolchain'),
                **{k:self.ref(root/k) for k in ('node','cli','patch')},
                'native_files':[self.ref(root/'native')],'key_name':'LOCAL_KEY','profile':'headless',
                'memory_bytes':1024**2,'cpu_percent':10,'tasks':1,'shutdown_seconds':1,'tmp_bytes':1024**2},
            'runtime_receipt':self.ref(root/'receipt'),
            'current_availability':{'declaration':self.ref(root/'declaration'),
                'cycle':self.ref(root/'cycle'),'proof':self.ref(root/'proof') if proof else None}}
        return d

    def provenance(self):
        keys=('hermes_cli.friday_ordinary_gateway','hermes_cli.friday_dashboard_owner',
            'hermes_cli.friday_user_scope','hermes_cli.friday_credential_admission',
            'hermes_cli.config','hermes_cli.config_effective','hermes_cli.config_section_guard',
            'hermes_yaml','utils','plugins.friday_rework.worker_declaration_writer',
            'plugins.friday_rework.worker_declarations','plugins.friday_rework.onboarding',
            'plugins.friday_rework.host_runtime','plugins.friday_rework.user_worker_join',
            'frw_fixture_tools.configure_local_test','frw_fixture_tools.web_profile')
        rows={name:self.ref(Path(sys.modules[name].__file__)) for name in keys}
        # Validate every native Python module loaded, including transitive
        # dependencies, against the explicitly pinned fixture receipt. Third
        # party packages are reported separately and confer no native credit.
        native_modules={}
        for name,loaded in tuple(sys.modules.items()):
            file=getattr(loaded,'__file__',None)
            if not file:continue
            path=Path(file).resolve()
            root=next((r for r in self.source_roots if path.is_relative_to(r)),None)
            if root is None:continue
            rel=str(path.relative_to(root))
            row=self.ref(path)
            assert row['sha256']==self.receipt['files'][rel]['sha256'],(name,rel)
            native_modules[name]=row
        return {'modules':rows,'all_loaded_native_modules':native_modules,
            'native_receipt':self.ref(self.receipt_path)}
