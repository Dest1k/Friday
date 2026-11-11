#!/usr/bin/env python3
"""Finite synthetic OTT/OTS/OTP native qualification; no model/application route."""
from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import stat
import sys
import time

BASE=Path(__file__).resolve().parent
SOURCE=Path('/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032/hermes-agent')
ASSIGNMENT='ASTRA-CHILD-F06-ODF-TEMPLATE-NATIVE-PATHS-20261112#1'
START='2026-11-12T02:32:28+03:00'
WALL,CPU,MEMORY=90,60,2*1024**3
DENIED=[]
CODE_READS=set()
OPERATIONS=[]
PHASE='setup'


class Refused(Exception): pass
def require(ok,code):
    if not ok:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    require(len(raw)<4*1024**2,'report_size')
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw)
def identity(path):
    s=Path(path).lstat()
    return dict(dev=s.st_dev,ino=s.st_ino,mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,nlink=s.st_nlink,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)


def boundary():
    os.umask(0o077);sys.dont_write_bytecode=True
    require(BASE.resolve()==BASE and stat.S_IMODE(BASE.stat().st_mode)==0o700,'own_root_custody')
    require((BASE/'LAUNCH.json').exists() and (BASE/'RECONCILIATION.json').exists() and not (BASE/'CONTINUATION-LAUNCH.json').exists(),'continuation_admission')
    dump(BASE/'CONTINUATION-LAUNCH.json',dict(assignment=ASSIGNMENT,pid=os.getpid(),automatic_retry=False))
    pins=json.loads((BASE/'SOURCE-PINS.json').read_bytes())
    for row in pins['files']+pins['resources']:
        p=SOURCE/row['relative'];require(p.resolve()==p and sha(p.read_bytes())==row['sha256'],'source_pin_drift')
    require(sha(Path(sys.executable).resolve().read_bytes())==pins['python_executable_sha256'],'python_pin_drift')
    allowed_source={str(SOURCE/r['relative']) for r in pins['files']+pins['resources']}
    os.environ.clear()
    for n in ['os-home','cache','config','data','tmp']: (BASE/n).mkdir(mode=0o700,exist_ok=True)
    os.environ.update(PATH='/usr/bin:/bin',HOME=str(BASE/'os-home'),HERMES_HOME=str(BASE/'authority'),
        PYTHONDONTWRITEBYTECODE='1',GATEWAY_ALLOWED_USERS='901,902',XDG_CACHE_HOME=str(BASE/'cache'),
        XDG_CONFIG_HOME=str(BASE/'config'),XDG_DATA_HOME=str(BASE/'data'),TMPDIR=str(BASE/'tmp'))
    os.chdir(BASE);sys.pycache_prefix=str(BASE/'cache/python')
    available=sorted(os.sched_getaffinity(0));require(len(available)>=2,'two_cpus_unavailable')
    os.sched_setaffinity(0,set(available[:2]))
    resource.setrlimit(resource.RLIMIT_AS,(MEMORY,MEMORY))
    resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
    dependency_roots=[Path(sys.prefix),Path(sys.base_prefix),Path('/usr/lib'),Path('/usr/local/lib'),Path('/usr/share/zoneinfo')]
    exact={'/dev/null','/dev/urandom','/etc/localtime','/etc/mime.types','/etc/ssl/openssl.cnf','/proc/1/cgroup','/proc/self/cgroup','/proc/self/mountinfo'}
    def absolute(raw,d=None):
        if isinstance(raw,int):return None
        p=Path(os.fsdecode(raw))
        if not p.is_absolute():p=(Path(os.readlink('/proc/self/fd/'+str(d))) if isinstance(d,int) and d>=0 else Path.cwd())/p
        return Path(os.path.abspath(p))
    def inside(p,roots):return any(p==r or p.is_relative_to(r) for r in roots)
    def deny(event,p=None):
        DENIED.append(dict(event=event,phase=PHASE,**({'path':str(p)} if p else {})))
        raise Refused('python_audit_boundary')
    def audit(event,args):
        if event=='open':
            p=absolute(args[0]);flags=args[2]
            if p is None:return
            writing=isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
            if writing and not inside(p,[BASE]):deny(event,p)
            if not writing and inside(p,[SOURCE]):
                if isinstance(flags,int) and flags&os.O_DIRECTORY:return
                if str(p) not in allowed_source or p.resolve()!=p:deny(event,p)
                CODE_READS.add(str(p.relative_to(SOURCE)));return
            if not writing and not inside(p,[BASE]+dependency_roots) and str(p) not in exact:
                if not (isinstance(flags,int) and flags&os.O_DIRECTORY):deny(event,p)
        elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.chown','os.utime','os.truncate'):
            d=args[2] if event=='os.mkdir' and len(args)>2 else args[-1] if event in ('os.remove','os.rmdir','os.chmod') else None
            p=absolute(args[0],d)
            if p is not None and not inside(p,[BASE]):deny(event,p)
        elif event in ('os.rename','os.link','os.symlink'):
            for k in (0,1):
                p=absolute(args[k],args[k+2] if len(args)>k+2 else None)
                if p is not None and not inside(p,[BASE]):deny(event,p)
        elif event=='sqlite3.connect':
            raw=os.fsdecode(args[0]);raw=raw[5:].split('?',1)[0] if raw.startswith('file:') else raw
            if raw!=':memory:' and not inside(absolute(raw),[BASE]):deny(event)
        elif event in ('socket.connect','socket.bind','socket.sendto','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn','os.fork','os.exec'):deny(event)
        elif event in ('os.listdir','os.scandir'):
            p=absolute(args[0])
            if p is not None and not inside(p,[BASE,SOURCE]+dependency_roots):deny(event,p)
    sys.addaudithook(audit);sys.path.insert(0,str(SOURCE));sys.path.insert(0,str(BASE))
    return pins,available[:2]


@contextmanager
def operation(label):
    global PHASE
    PHASE=label;wall_start=time.monotonic();usage=resource.getrusage(resource.RUSAGE_SELF);before=usage.ru_utime+usage.ru_stime
    prior=signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Refused('operation_wall_limit')))
    priorcpu=signal.signal(signal.SIGXCPU,lambda *_:(_ for _ in ()).throw(Refused('operation_cpu_limit')))
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(before)+CPU,resource.RLIM_INFINITY))
    signal.setitimer(signal.ITIMER_REAL,WALL)
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior);signal.signal(signal.SIGXCPU,priorcpu)
        usage_after=resource.getrusage(resource.RUSAGE_SELF)
        OPERATIONS.append(dict(label=label,wall_seconds=time.monotonic()-wall_start,cpu_seconds=usage_after.ru_utime+usage_after.ru_stime-before))
        dump(BASE/'OPERATION-TIMES.json',OPERATIONS)


class Native:
    def __init__(self):
        from hermes_cli import friday_user_scope as scope
        from hermes_cli.plugins_state import PluginState
        from hermes_cli.friday_product_access import KEY,principal_id
        from gateway.authz_mixin import GatewayAuthorizationMixin
        from gateway.config import Platform
        from gateway.session import SessionSource
        from gateway.session_identity import RoutingIdentity
        from tools.file_tools import read_file_tool,write_file_tool
        self.scope,self.read,self.write=scope,read_file_tool,write_file_tool
        self.root=BASE/'authority';require(self.root.is_dir(),'retained_authority_absent')
        self.bindings=[dict(platform='telegram',transport_profile='default',account_id='OWN-ODF-TEMPLATE-BOT',user_id=u,runtime_profile='odf-template-'+tag,tools=['read_file','write_file'] if tag=='a' else ['read_file']) for u,tag in [('901','a'),('902','b')]]
        settings={'product_access':{'enabled':True,'accounts':[dict(platform='telegram',transport_profile='default',account_id='OWN-ODF-TEMPLATE-BOT',runtime_profiles=['odf-template-a','odf-template-b'])]},'user_isolation':{'enabled':True,'bindings':self.bindings}}
        self.homes=[self.root/'profiles'/b['runtime_profile'] for b in self.bindings]
        require(all(p.is_dir() for p in self.homes),'retained_synthetic_profiles_absent')
        self.sources=[]
        for i,b in enumerate(self.bindings):
            src=SessionSource(Platform.TELEGRAM,'OWN-SYNTHETIC-CHAT',user_id=b['user_id'],chat_type='group',thread_id='OWN-SYNTHETIC-TOPIC',profile=b['runtime_profile'])
            src._identity=RoutingIdentity('default',b['runtime_profile'],self.root,self.homes[i],multiplexed=True,transport_inferred=False)
            with scope.authority(self.root):require(GatewayAuthorizationMixin()._principal_authorized(src,allow_adapter_delegation=True) is True,'native_admission')
            self.sources.append(src)

    @contextmanager
    def enter(self,i=0):
        with self.scope.authority(self.homes[i]),self.scope.scoped_source(self.sources[i]) as cap:yield cap


def observe(fn):
    try:return json.loads(fn())
    except Exception as e:return {'success':False,'exception_class':type(e).__name__}
def receipt(v):
    keys=('success','error','reason','exception_class','source_sha256','sha256','encrypted','password_preserved','plaintext_published','create_only','effect_disposition','format')
    return {k:v[k] for k in keys if k in v and (not isinstance(v[k],str) or re.fullmatch('[A-Za-z0-9_.:-]{1,160}',v[k]))}
def refusal(v,fmt,which,edit=False):
    return v.get('success') is False and not v.get('content') and not v.get('exception_class') and v.get('reason')=={'missing':'odf_password_required','wrong':'odf_password_rejected_or_corrupt'}[which] and v.get('error')==('protected_document_edit_refused' if edit else 'document_extraction_failed') and (v.get('effect_disposition')=='none' if edit else v.get('format')==fmt)


def main():
    pins,cpus=boundary()
    with operation('independent_builder_import'):
        import spec_fixture as fixture
    credentials=json.loads((BASE/'SYNTHETIC-CREDENTIAL.json').read_bytes())
    password=credentials['password'];wrong=credentials['wrong_password']
    with operation('native_import_provision_admit'):native=Native()
    rows=[]
    for fmt in ('ott','ots','otp'):
        with operation(fmt+'_fixture_build'):
            src=native.homes[0]/'workspace'/('own-source.'+fmt)
            if fmt=='ott':
                saved=json.loads((BASE/'RECONCILIATION.json').read_bytes())['preserved'][0]
                raw=src.read_bytes();require(sha(raw)==saved['sha256'],'retained_fixture_hash')
                require(src.stat().st_ino==saved['ino'] and src.stat().st_dev==saved['dev'],'retained_fixture_identity')
            else:
                raw=fixture.build(fmt,password)
                with os.fdopen(os.open(src,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw)
            parts,structure=fixture.oracle(raw,fmt,password)
            require(fixture.semantics(parts,fmt,False),'independent_fixture_semantics')
            original_identity=identity(src)
        edit={'ott':dict(old_text='OTT-UNIQUE-BEFORE',new_text='OTT-UNIQUE-AFTER'),
              'ots':dict(sheet='TemplateSheet',cell='A1',expected='OTS-BEFORE',value='OTS-AFTER'),
              'otp':dict(slide=1,role='slide',old_text='OTP-UNIQUE-BEFORE',new_text='OTP-UNIQUE-AFTER')}[fmt]
        output='own-edited.'+fmt;out=src.parent/output
        spec=dict(source=src.name,source_sha256=sha(raw),password=password,edit=edit)
        row=dict(format=fmt,fixture={'path':str(src),'sha256':sha(raw),'identity':original_identity,'structure':structure},checks={'independent_fixture_spec_crypto_xml_semantics':True},receipts={})
        def record(label,val,ok):
            row['receipts'][label]=receipt(val);row['checks'][label]=bool(ok)
            dump(BASE/('OBSERVATIONS-INPROGRESS-'+fmt+'.json'),row)
        def write(name,changes=None):return observe(lambda:native.write(name,json.dumps(spec|(changes or {})),format='odf_password_edit'))
        with native.enter() as cap:
            row['capability']={k:getattr(cap,k,None) for k in ('key','profile','tools') if isinstance(getattr(cap,k,None),(str,int,list,tuple))}
            read_cases=[('correct',password)] if fmt=='ott' else [('missing',None),('wrong',wrong),('correct',password)]
            for which,secret in read_cases:
                with operation(fmt+'_'+which+'_read'):
                    val=observe(lambda:native.read(src.name,password=secret))
                    expected={'ott':'OTT-UNIQUE-BEFORE','ots':'OTS-BEFORE','otp':'OTP-UNIQUE-BEFORE'}[fmt]
                    record(which+'_read',val,refusal(val,fmt,which) if which!='correct' else val.get('success') is True and val.get('source_sha256')==sha(raw) and not val.get('partial') and expected in val.get('content','') and val.get('format')==fmt and val.get('encryption',{}).get('encrypted') is True)
            edit_cases=[] if fmt=='ott' else [('wrong_edit',{'password':wrong}),('missing_edit',{'password':None}),('stale_hash_edit',{'source_sha256':'0'*64})]
            for label,changes in edit_cases:
                with operation(fmt+'_'+label):
                    target='own-'+label+'.'+fmt;val=write(target,changes)
                    if label=='stale_hash_edit':ok=val.get('success') is False and val.get('reason')=='source_hash_mismatch' and val.get('effect_disposition')=='none' and not val.get('exception_class')
                    else:ok=refusal(val,fmt,'wrong' if label=='wrong_edit' else 'missing',True)
                    record(label,val,ok and not (src.parent/target).exists())
            if fmt=='ott':
                saved=json.loads((BASE/'RECONCILIATION.json').read_bytes())['preserved'][1]
                row['prior_completed_operations_not_replayed']=['missing_read','wrong_read','wrong_edit','missing_edit','stale_hash_edit','correct_edit','output_wrong_read','output_missing_read','noreplace','source_symlink_refused']
                row['prior_raw_receipts']='NOT_RETAINED_DUE_TO_ORIGINAL_HARNESS_FAILURE; no values reconstructed'
                row['retained_native_create_effect']={'previous_harness_sha256':json.loads((BASE/'RECONCILIATION.json').read_bytes())['original_harness_sha256'],'phase_after_effect':'representative_scope_controls','raw_tool_receipt':'NOT_RETAINED_DUE_TO_ORIGINAL_HARNESS_FAILURE','repeat_effect':False}
                row['checks']['retained_native_create_effect_reconciled']=out.exists() and sha(out.read_bytes())==saved['sha256'] and out.stat().st_ino==saved['ino']
            else:
                with operation(fmt+'_correct_edit'):
                    val=write(output);record('correct_edit',val,val.get('success') is True and val.get('source_sha256')==sha(raw) and val.get('password_preserved') is True and val.get('plaintext_published') is False)
            row['checks']['output_exists']=out.is_file()
            if out.exists():
                with operation(fmt+'_independent_output_oracle'):
                    encrypted=out.read_bytes();afterparts,afterstructure=fixture.oracle(encrypted,fmt,password)
                    row['output']={'path':str(out),'sha256':sha(encrypted),'identity':identity(out),'structure':afterstructure}
                    row['checks'].update(independent_output_password_crypto=True,independent_output_semantics=fixture.semantics(afterparts,fmt,True),
                        same_template_mime=structure['mime']==afterstructure['mime'],same_members=set(parts)==set(afterparts),
                        unrelated_members_preserved=all(parts[n]==afterparts[n] for n in parts if n not in ('content.xml','META-INF/manifest.xml')),
                        new_salts_ivs=all(structure[k][n]!=afterstructure[k][n] for k in ('salts_sha256','ivs_sha256') for n in structure[k]),output_private600=identity(out)['mode']=='0o600')
                output_read_cases=[('correct',password)] if fmt=='ott' else [('wrong',wrong),('missing',None),('correct',password)]
                for which,secret in output_read_cases:
                    with operation(fmt+'_output_'+which+'_read'):
                        val=observe(lambda:native.read(output,password=secret))
                        expected={'ott':'OTT-UNIQUE-AFTER','ots':'OTS-AFTER','otp':'OTP-UNIQUE-AFTER'}[fmt]
                        record('output_'+which+'_read',val,refusal(val,fmt,which) if which!='correct' else val.get('success') is True and val.get('source_sha256')==sha(encrypted) and expected in val.get('content','') and not val.get('partial'))
                if fmt!='ott':
                    with operation(fmt+'_noreplace'):
                        prior=out.read_bytes();prior_identity=identity(out);val=write(output)
                        record('noreplace',val,val.get('success') is False and val.get('error')=='document_already_exists' and not val.get('exception_class') and out.read_bytes()==prior and identity(out)==prior_identity)
            row['checks']['source_bytes_and_physical_identity_unchanged']=src.read_bytes()==raw and identity(src)==original_identity
        if fmt=='ott':
            with operation('representative_foreign_and_permission_controls'),native.enter(1):
                val=observe(lambda:native.scope.scoped_file('read_file',{'path':str(src),'password':password}))
                record('foreign_source_refused',val,val=={'success':False,'exception_class':'ScopeDenied'})
                val=observe(lambda:native.scope.scoped_file('write_file',{'path':'ungranted.ott','content':json.dumps(spec),'format':'odf_password_edit'}))
                record('ungranted_edit_refused',val,val=={'success':False,'exception_class':'ScopeDenied'} and not (native.homes[1]/'workspace/ungranted.ott').exists())
        row['all_checks_pass']=all(row['checks'].values());rows.append(row)
        dump(BASE/'OBSERVATIONS.json',rows)
    modules=[]
    for name,m in sorted(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if p and Path(p).is_relative_to(SOURCE):modules.append(dict(module=name,path=p,sha256=sha(Path(p).read_bytes())))
    size=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file() and not p.is_symlink())
    require(size<64*1024**2,'stand_disk_limit')
    result=dict(schema='friday.f06.odf-template-native-paths.v1',assignment=ASSIGNMENT,status='OTS_OTP_NATIVE_PASS_OTT_RETAINED_READ_ORACLE_PASS' if all(r['all_checks_pass'] for r in rows) and not DENIED else 'NATIVE_SYNTHETIC_FAIL',
        started_moscow=START,finished_moscow=time.strftime('%Y-%m-%dT%H:%M:%S',time.gmtime(time.time()+10800))+'+03:00',
        actual='H203/project487/native17891/plugins52/base17730',installed_source=str(SOURCE),source_receipt_sha256=pins['receipt'],
        python=str(Path(sys.executable)),python_target=str(Path(sys.executable).resolve()),python_sha256=pins['python_executable_sha256'],
        source_pins_sha256=sha((BASE/'SOURCE-PINS.json').read_bytes()),requirements_sha256=sha((BASE/'REQUIREMENTS.json').read_bytes()),
        entrypoints=['GatewayAuthorizationMixin._principal_authorized','friday_user_scope.provision_new_home','friday_user_scope.scoped_source','tools.file_tools.read_file_tool','tools.file_tools.write_file_tool','friday_user_scope.scoped_file','friday_workspace_odf_password.create_edit'],
        native_unmocked=True,fixture_builder='independent spec_fixture.py, cryptography AES; product uses Cryptodome AES',
        credential=dict(scope='fresh own synthetic only',path=str(BASE/'SYNTHETIC-CREDENTIAL.json'),custody=identity(BASE/'SYNTHETIC-CREDENTIAL.json'),values_logged=False,argv_or_env=False),
        limits=dict(per_operation_wall_seconds=WALL,per_operation_cpu_seconds=CPU,address_space_bytes=MEMORY,actual_cpu_affinity=cpus,stand_bytes=size,stand_max_bytes=64*1024**2,package_max_bytes=128*1024**2),
        first_attempt_reconciliation=json.loads((BASE/'RECONCILIATION.json').read_bytes()),rows=rows,loaded_native_modules=modules,source_open_inventory=sorted(CODE_READS),audit_denials=DENIED,operations=OPERATIONS,
        application_acceptance='NOT_RUN',bot_acceptance='NOT_RUN',formal_F06='NOT_CLAIMED',
        limits_of_evidence=['Synthetic fixtures independently checked for ZIP/XML/MIME/body/crypto/semantic invariants; no actual Office application validity or render acceptance.','Python audit observer restricts this interpreter; it is not OS confinement or proof of global absence.','Only declared compatible CBC/PBKDF2 template profile and bounded allowed edit contracts were exercised.','Flat FODT/FODS/FODP were not renamed or tested as encrypted templates; no NA judgement made.','No old actual F06 credentials/manifests/ciphertext or prior consumed qualification opened.'],
        next_root_stage='Independent review of own fixture/native evidence, then separately authorized application validity/output oracle and ordinary bot/formal coverage if required.')
    require(not DENIED,'audit_denial_precludes_pass')
    dump(BASE/'RESULT.json',result)
    print(json.dumps({'status':result['status'],'formats':[r['format'] for r in rows],'all_checks_pass':all(r['all_checks_pass'] for r in rows),'result_sha256':sha((BASE/'RESULT.json').read_bytes())}))


if __name__=='__main__':
    try:main()
    except Exception as e:
        # Never serialize native exception messages, tool inputs or content.
        code=str(e) if isinstance(e,Refused) and re.fullmatch('[a-z_]{1,100}',str(e)) else type(e).__name__
        dump(BASE/'CONTINUATION-FAILURE.json',dict(assignment=ASSIGNMENT,phase=PHASE,code=code,audit_denials=DENIED,automatic_retry=False))
        print(json.dumps({'status':'FAILED','phase':PHASE,'code':code}));sys.exit(1)
